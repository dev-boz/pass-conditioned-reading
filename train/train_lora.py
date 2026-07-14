"""E2′ student trainer — LoRA SFT on teacher trajectories (Stage A: coupled/explicit).

Run-1 (WSL2 venv ~/e2prime-venv, 1080 Ti, Pascal sm_61): fp32 default — consumer Pascal
fp16 math is ~1/64 rate and bf16/tf32 don't exist there. Failed its P-C check; root cause
was TRL's default truncation, not this trainer (see docs/HANDOFF-2026-07-14.md, D34).

Run-2 (rented Ampere/Ada cloud GPU, seq_len 10240): fp32/bf16-without-liger both OOM even
on 24GB at this window — HF's ForCausalLMLoss unconditionally does `logits.float()`, a
dtype-invariant ~vocab*seq*4-byte tensor (plus coexisting copies in the CE backward) that
persists regardless of model dtype. Validated fix: `--dtype bf16 --liger` (liger-kernel's
fused_linear_cross_entropy chunks the lm_head+CE so the full [seq,vocab] logits tensor is
never materialised) — measured peak 5.9GiB at seq 10240 on an A5000, vs 23.5GB+ OOM
without it. `--attn chunked` remains the Pascal fix (D34) and is not needed on Ampere+,
where stock SDPA already dispatches a real flash/efficient kernel.

Data: JSONL rows {"prompt": [chat messages], "completion": [assistant message]} rendered
by src/pca/teacher_gen.py (one row per pass; loss on completion tokens only — TRL
prompt-completion masking). The renderer, not this script, owns arm/channel formatting,
so one trainer serves every Stage A/B/C student.

    python train_lora.py --data data/e2prime/stageA_coupled.jsonl \
        --base Qwen/Qwen2.5-1.5B-Instruct --out runs/stageA_coupled_v2 \
        --seq-len 10240 --dtype bf16 --liger --merge

Hyperparameter defaults are the pre-registered engineering defaults
(docs/E2PRIME-PREREG.md §2); dtype/liger/attn are run-2 amendments, not defaults.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True, help="teacher-trajectory JSONL (prompt/completion rows)")
    p.add_argument("--base", default="Qwen/Qwen2.5-1.5B-Instruct")
    p.add_argument("--out", required=True, help="output dir (adapter, logs, optional merged model)")
    p.add_argument("--r", type=int, default=16)
    p.add_argument("--alpha", type=int, default=32)
    p.add_argument("--dropout", type=float, default=0.05)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--epochs", type=float, default=2.0)
    p.add_argument("--seq-len", type=int, default=4096)
    p.add_argument("--batch", type=int, default=1)
    p.add_argument("--accum", type=int, default=16)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--dtype", choices=["fp32", "fp16", "bf16"], default="fp32")
    p.add_argument("--liger", action="store_true",
                   help="apply_liger_kernel_to_qwen2(fused_linear_cross_entropy=True) — required "
                        "at seq_len>~6K on any GPU: HF's ForCausalLMLoss unconditionally does "
                        "logits.float(), a dtype-invariant ~vocab*seq*4-byte tensor (plus the CE "
                        "backward's coexisting copies) that no dtype change shrinks (D34 amendment, "
                        "run-2 cloud probes). Liger fuses the lm_head projection with a chunked CE "
                        "so the full [seq,vocab] logits tensor is never materialised.")
    p.add_argument("--eval-frac", type=float, default=0.05,
                   help="held-out fraction, split by DOC ID (never by row) for the P-C health check")
    p.add_argument("--merge", action="store_true", help="save merged weights after training")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--save-steps", type=int, default=25,
                   help="checkpoint every N optimizer steps (0 = per-epoch only). Pause/resume "
                        "granularity — cadence does not alter the optimization trajectory")
    p.add_argument("--attn", choices=["stock", "chunked"], default="stock",
                   help="'chunked' = flash-style O(n·block) causal SDPA (train/chunked_attn.py, "
                        "equivalence-gated) — required for seq >~6K on Pascal, where every stock "
                        "path materialises the fp32 n^2 score matrix (D34)")
    return p.parse_args()


def load_rows(path: Path) -> list[dict]:
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in rows:
        assert "prompt" in r and "completion" in r and "doc_id" in r, "renderer contract violated"
    return rows


def split_by_doc(rows: list[dict], eval_frac: float, seed: int) -> tuple[list[dict], list[dict]]:
    """Held-out split by document, not by row — passes of one doc never straddle the split."""
    import random
    docs = sorted({r["doc_id"] for r in rows})
    rng = random.Random(seed)
    rng.shuffle(docs)
    n_eval = max(1, int(len(docs) * eval_frac))
    eval_docs = set(docs[:n_eval])
    train = [r for r in rows if r["doc_id"] not in eval_docs]
    ev = [r for r in rows if r["doc_id"] in eval_docs]
    return train, ev


def main() -> None:
    args = parse_args()
    import torch
    # PyTorch 2.13 native Triton dispatches require a C compiler to JIT-compile
    # the Triton CUDA driver shim (CudaUtils).  On machines without gcc/clang this
    # raises RuntimeError at the first bmm call (Qwen2 RoPE outer-product path).
    # Deregister the Triton override so aten::bmm falls back to the regular CUDA
    # kernel. WSL-without-a-compiler-only; no-op (module absent) where gcc/clang
    # exists, e.g. the run-2 cloud pod (D34 amendment).
    try:
        from torch._native.registry import deregister_op_overrides
        deregister_op_overrides(disable_dsl_names=["triton"])
    except ImportError:
        pass
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows = load_rows(Path(args.data))

    # Length gate (run-1 post-mortem, D34): TRL's default keep_start truncation silently cut
    # the COMPLETION off every row longer than max_length — 74-81% of the code slices trained
    # with no signal. A row either fits the window whole or is excluded and logged; truncation
    # must never be the thing that touches a training row.
    attn_impl = "sdpa"
    if args.attn == "chunked":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from chunked_attn import register
        attn_impl = register()

    _DTYPES = {"fp32": torch.float32, "fp16": torch.float16, "bf16": torch.bfloat16}
    dtype = _DTYPES[args.dtype]
    if args.liger:
        from liger_kernel.transformers import apply_liger_kernel_to_qwen2
        apply_liger_kernel_to_qwen2(fused_linear_cross_entropy=True)
    tok = AutoTokenizer.from_pretrained(args.base)

    def full_len(r: dict) -> int:
        ids = tok.apply_chat_template(r["prompt"] + r["completion"], tokenize=True,
                                      return_dict=True)["input_ids"]
        return len(ids)

    from collections import Counter
    kept, dropped = [], Counter()
    for r in rows:
        if full_len(r) <= args.seq_len:
            kept.append(r)
        else:
            dropped[r["doc_id"].split("-")[0]] += 1
    print(f"length gate @ {args.seq_len}: kept {len(kept)}/{len(rows)} rows; "
          f"dropped per slice: {dict(dropped)}")
    rows = kept

    train_rows, eval_rows = split_by_doc(rows, args.eval_frac, args.seed)
    (out / "split.json").write_text(json.dumps({
        "n_train": len(train_rows), "n_eval": len(eval_rows),
        "seq_len": args.seq_len, "dropped_over_window": dict(dropped),
        "eval_docs": sorted({r["doc_id"] for r in eval_rows}),
    }, indent=1), encoding="utf-8")
    model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=dtype, device_map="cuda",
                                                 attn_implementation=attn_impl)
    model.config.use_cache = False

    # prompt/completion columns -> TRL applies the chat template and masks prompt tokens
    keep = ["prompt", "completion"]
    train_ds = Dataset.from_list([{k: r[k] for k in keep} for r in train_rows])
    eval_ds = Dataset.from_list([{k: r[k] for k in keep} for r in eval_rows]) if eval_rows else None

    peft_cfg = LoraConfig(
        r=args.r, lora_alpha=args.alpha, lora_dropout=args.dropout, bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    sft_cfg = SFTConfig(
        output_dir=str(out), seed=args.seed,
        num_train_epochs=args.epochs, learning_rate=args.lr, lr_scheduler_type="cosine",
        warmup_ratio=0.03, weight_decay=0.0,
        per_device_train_batch_size=args.batch, gradient_accumulation_steps=args.accum,
        # HF default eval batch is 8: eight seq-4096 rows forward at once ON TOP of the
        # train-resident weights+optimizer OOM'd the 11GB card at the epoch-1 boundary.
        per_device_eval_batch_size=1,
        gradient_checkpointing=True, max_length=args.seq_len,
        fp16=(args.dtype == "fp16"), bf16=(args.dtype == "bf16"),
        logging_steps=10,
        save_strategy=("steps" if args.save_steps else "epoch"),
        save_steps=(args.save_steps or 500), save_total_limit=3,
        eval_strategy="epoch" if eval_ds is not None else "no",
        report_to=[],
    )
    trainer = SFTTrainer(model=model, args=sft_cfg, train_dataset=train_ds,
                         eval_dataset=eval_ds, peft_config=peft_cfg)
    trainer.train(resume_from_checkpoint=args.resume)
    trainer.save_model(str(out / "adapter"))
    tok.save_pretrained(str(out / "adapter"))

    metrics = {"train": trainer.state.log_history[-3:]}
    (out / "final_metrics.json").write_text(json.dumps(metrics, indent=1), encoding="utf-8")

    if args.merge:
        merged = trainer.model.merge_and_unload()
        merged = merged.to(torch.float16)  # storage dtype for GGUF conversion
        merged.save_pretrained(str(out / "merged"))
        tok.save_pretrained(str(out / "merged"))
        print(f"merged fp16 model at {out/'merged'} — convert with llama.cpp convert_hf_to_gguf.py")

    print("training complete:", out)


if __name__ == "__main__":
    main()
