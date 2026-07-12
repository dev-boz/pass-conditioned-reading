"""E2′ student trainer — LoRA SFT on teacher trajectories (Stage A: coupled/explicit).

Runs in the WSL2 venv (~/e2prime-venv) on the 1080 Ti. Pascal (sm_61) note: consumer
Pascal fp16 math is ~1/64 rate and bf16/tf32 don't exist there, so the default is fp32
compute with fp16 available behind a flag for memory-bound configs (slower per-step).

Data: JSONL rows {"prompt": [chat messages], "completion": [assistant message]} rendered
by src/pca/teacher_gen.py (one row per pass; loss on completion tokens only — TRL
prompt-completion masking). The renderer, not this script, owns arm/channel formatting,
so one trainer serves every Stage A/B/C student.

    python train_lora.py --data data/e2prime/stageA_coupled.jsonl \
        --base Qwen/Qwen2.5-1.5B-Instruct --out runs/stageA_coupled \
        [--merge]   # also save merged fp16 weights for llama.cpp GGUF conversion

Hyperparameter defaults are the pre-registered engineering defaults
(docs/E2PRIME-PREREG.md §2); they freeze when data generation begins.
"""

from __future__ import annotations

import argparse
import json
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
    p.add_argument("--dtype", choices=["fp32", "fp16"], default="fp32")
    p.add_argument("--eval-frac", type=float, default=0.05,
                   help="held-out fraction, split by DOC ID (never by row) for the P-C health check")
    p.add_argument("--merge", action="store_true", help="save merged weights after training")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--save-steps", type=int, default=25,
                   help="checkpoint every N optimizer steps (0 = per-epoch only). Pause/resume "
                        "granularity — cadence does not alter the optimization trajectory")
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
    # kernel.  This is the minimal fix; no other behaviour changes.
    from torch._native.registry import deregister_op_overrides
    deregister_op_overrides(disable_dsl_names=["triton"])
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows = load_rows(Path(args.data))
    train_rows, eval_rows = split_by_doc(rows, args.eval_frac, args.seed)
    (out / "split.json").write_text(json.dumps({
        "n_train": len(train_rows), "n_eval": len(eval_rows),
        "eval_docs": sorted({r["doc_id"] for r in eval_rows}),
    }, indent=1), encoding="utf-8")

    dtype = torch.float32 if args.dtype == "fp32" else torch.float16
    tok = AutoTokenizer.from_pretrained(args.base)
    model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=dtype, device_map="cuda")
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
        gradient_checkpointing=True, max_length=args.seq_len,
        fp16=(args.dtype == "fp16"), bf16=False,  # no bf16/tf32 on Pascal
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
