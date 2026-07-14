"""P-C training-health check (E2PRIME-CRITERION §1 P-C) — run after train_lora.py.

On the held-out teacher trajectories (the split-by-doc eval docs recorded in split.json):
generate the student's completion for every held-out pass prompt (greedy), parse with the
production v3.2 harness, and report:

  - syntactic validity   = Σ valid / Σ candidate lines over all held-out passes  (bar ≥ 0.95)
  - op-type agreement    = macro over passes of [dominant op-type(student) ==
                           dominant op-type(teacher)], op-type ∈ {ADD, REPLACE, REMOVE,
                           NO_CHANGE}; ties broken by the order above (formula stated per
                           the D24 discipline)                                    (bar ≥ 0.75)

Below either bar the run is a TRAINING failure: fix data/hyperparameters and retrain —
no capability fork may be invoked (criterion §1 P-C).

**Envelope protocol (D34, run-2, pre-committed before any run-2 result existed):** the
trainer's length gate means held-out rows can still exceed the training window (excluded
from training, never from eval). Bars are scored ONLY on held rows whose full
prompt+completion length fits within `split.json`'s recorded `seq_len` — the envelope the
student actually trained on, which the pre-reg established covers the §3 gate altitude.
Over-window held rows are still generated and parsed but reported as a separate
out-of-envelope appendix, never counted toward the verdict.

  ~/e2prime-venv/bin/python train/pc_check.py --run runs/stageA_coupled \
      --data data/e2prime/stageA_coupled.jsonl [--base Qwen/Qwen2.5-1.5B-Instruct]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from pca.editops import IntegrationState, parse_ops  # noqa: E402

ORDER = ["ADD", "REPLACE", "REMOVE", "NO_CHANGE"]


def dominant(ops: list[dict]) -> str:
    if not ops:
        return "NONE"
    c = Counter(o["op"] for o in ops)
    return max(ORDER, key=lambda t: (c.get(t, 0), -ORDER.index(t)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="training output dir (adapter/ + split.json)")
    ap.add_argument("--data", required=True)
    ap.add_argument("--base", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--max-new", type=int, default=900)
    ap.add_argument("--limit", type=int, default=0, help="cap held-out rows (0 = all)")
    ap.add_argument("--server", default=None,
                    help="llama.cpp base URL (e.g. http://127.0.0.1:8093): check the SERVED fp16 "
                         "GGUF student — the artifact the §3 gates probe — instead of "
                         "transformers+adapter (which needs ~2× the VRAM of serving). "
                         "Greedy either way; the parse/metrics are identical.")
    args = ap.parse_args()

    run = Path(args.run)
    split = json.loads((run / "split.json").read_text(encoding="utf-8"))
    eval_docs = set(split["eval_docs"])
    seq_len = split.get("seq_len")  # absent = pre-D34 run (no length gate, no envelope split)
    rows = [json.loads(l) for l in open(args.data, encoding="utf-8") if l.strip()]
    held = [r for r in rows if r["doc_id"] in eval_docs and r["stage"] != "closing"]
    if args.limit:
        held = held[: args.limit]

    from transformers import AutoTokenizer
    len_tok = AutoTokenizer.from_pretrained(args.base)

    def full_len(r: dict) -> int:
        ids = len_tok.apply_chat_template(r["prompt"] + r["completion"], tokenize=True,
                                          return_dict=True)["input_ids"]
        return len(ids)

    if seq_len:
        in_env = [r for r in held if full_len(r) <= seq_len]
        out_env = [r for r in held if full_len(r) > seq_len]
    else:
        in_env, out_env = held, []
    print(f"held-out docs: {len(eval_docs)} | held-out pass rows: {len(held)} "
          f"| in-envelope (<= {seq_len}): {len(in_env)} | out-of-envelope: {len(out_env)}")

    if args.server:
        import requests

        def generate(msgs: list[dict]) -> str:
            r = requests.post(f"{args.server}/v1/chat/completions",
                              json={"messages": msgs, "max_tokens": args.max_new,
                                    "temperature": 0.0, "seed": 42}, timeout=1800)
            r.raise_for_status()
            return (r.json()["choices"][0]["message"].get("content") or "")
    else:
        import torch
        # Same Pascal workaround as train_lora.py: no C compiler in WSL for the Triton shim;
        # no-op (module absent) wherever gcc/clang exists.
        try:
            from torch._native.registry import deregister_op_overrides
            deregister_op_overrides(disable_dsl_names=["triton"])
        except ImportError:
            pass
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tok = AutoTokenizer.from_pretrained(str(run / "adapter"))
        model = AutoModelForCausalLM.from_pretrained(args.base, torch_dtype=torch.float32,
                                                     device_map="cuda")
        model = PeftModel.from_pretrained(model, str(run / "adapter"))
        model.eval()

        def generate(msgs: list[dict]) -> str:
            enc = tok.apply_chat_template(msgs, add_generation_prompt=True,
                                          return_tensors="pt", return_dict=True).to("cuda")
            with torch.no_grad():
                out = model.generate(**enc, max_new_tokens=args.max_new, do_sample=False,
                                     pad_token_id=tok.eos_token_id)
            return tok.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)

    import re

    def score(rows_subset: list[dict], label: str) -> dict:
        v_sum = c_sum = 0
        agree, per_doc = [], Counter()
        for i, r in enumerate(rows_subset):
            msgs = r["prompt"]
            text = generate(msgs)
            # parse both against a state reconstructed from the prompt is unnecessary for
            # these metrics: validity needs id-resolvability, so rebuild ids from the STATE
            # block of the prompt (S\d+ lines) — the same context the teacher saw.
            state_ids = set(re.findall(r"^(S\d+[A-Za-z]?):", msgs[1]["content"], re.M))
            next_id = max([int(re.sub(r"[A-Za-z]", "", s[1:])) for s in state_ids], default=0) + 1
            sres = parse_ops(text, state_ids, next_id)
            tres = parse_ops(r["completion"][0]["content"], state_ids, next_id)
            v_sum += sres.valid
            c_sum += sres.candidate_lines
            a = dominant(sres.ops) == dominant(tres.ops)
            agree.append(a)
            per_doc[r["doc_id"]] += (not a)
            if (i + 1) % 25 == 0:
                print(f"  [{label}] {i+1}/{len(rows_subset)} | running validity "
                      f"{v_sum/max(c_sum,1):.3f} | agreement {sum(agree)/len(agree):.3f}")
        validity = v_sum / max(c_sum, 1)
        agreement = sum(agree) / max(len(agree), 1)
        return {"validity": round(validity, 4), "agreement": round(agreement, 4),
                "n_rows": len(rows_subset), "worst_docs": per_doc.most_common(5)}

    in_result = score(in_env, "in-envelope")
    verdict = ("PASS" if (in_result["validity"] >= 0.95 and in_result["agreement"] >= 0.75)
               else "TRAINING FAILURE (P-C)")
    out_result = score(out_env, "out-of-envelope") if out_env else None

    report = {**in_result, "n_docs": len(eval_docs), "verdict": verdict,
              "bars": {"validity": 0.95, "agreement": 0.75}, "seq_len_envelope": seq_len,
              "mode": ("server-gguf" if args.server else "transformers-adapter"),
              "out_of_envelope_appendix": out_result}
    (run / "pc_check.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    # ASCII only: '>=' not the math glyph — a cp1252-redirected stdout on Windows dies on it
    # (run 1 wrote the report then crashed on this very line).
    print(f"\nP-C (in-envelope, n={in_result['n_rows']}): validity={in_result['validity']:.3f} "
          f"(>=0.95) agreement={in_result['agreement']:.3f} (>=0.75) -> {verdict}")
    if out_result:
        print(f"P-C out-of-envelope appendix (n={out_result['n_rows']}, NOT counted toward "
              f"verdict): validity={out_result['validity']:.3f} agreement={out_result['agreement']:.3f}")
    print(f"report: {run/'pc_check.json'}")


if __name__ == "__main__":
    main()
