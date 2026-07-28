"""Stage-A companion checks — GATE-1 backfill and GATE-3 seeded compose, on the Stage-A arms.

E2PRIME-PREREG §6 requires both to re-run on the trained student. They are DIAGNOSTICS and
REFERENCE ROWS: per the addendum they are reported separately from the chain verdict and cannot
soften a chain-gate outcome.

Why not the frozen p7_split_unit scripts unchanged: they select a model from the P7 config
registry, which has no entry for the Stage-A student or its 1.5B floor, and they ask with the
LEGACY closing prompt ("do not invent numbers", no derivation permission). A GATE-3 run under the
legacy prompt says nothing about the closing frame the chain battery actually used. So both frames
are run here:

  legacy  — comparable to the archived P7 floor numbers
  chain   — the chain gate's own CLOSE_SYSTEM, comparable to this battery

The seeded state itself is imported from the frozen compose_gate.best_case_state, not re-written,
so GATE-3 keeps testing the same best-case state it always did.

GATE-1 asks the scoring question from fragment-2 alone (call site + adder, no table). It MUST fail:
a model that produces 2353 without the table is guessing, and a guessable fixture would make every
chain success uninterpretable.

  python experiments/e2prime/stagea_companion_checks.py --arm student --gate both
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P7 = ROOT / "experiments" / "p7_split_unit"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(P7))
sys.path.insert(0, str(HERE))

from pca.llm import LlamaServer                                       # noqa: E402
from compose_gate import CLOSING_SYSTEM as LEGACY_CLOSING             # noqa: E402
from compose_gate import best_case_state                              # noqa: E402
from stagea_chain_gate import ARMS, CLOSE_SYSTEM                      # noqa: E402

SPEC = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
TRUTH = SPEC["ground_truth_answer"]
TVAL = SPEC["table_value_for_queried"]
DRAWS = [(42, 0.0)] + [(s, 0.7) for s in range(1, 11)]

BACKFILL_SYSTEM = ("You are a precise Python code analyst. Answer using ONLY the code shown. "
                   "If the code shown is insufficient to determine the answer, say exactly: "
                   "INSUFFICIENT.")


def ask(server, system: str, user: str, seed: int, temp: float, max_tokens: int) -> dict:
    r = server.chat(system, user, max_tokens=max_tokens, temperature=temp, seed=seed)
    txt = r["text"]
    m = re.search(r"ANSWER:\s*(-?\d[\d,]*)", txt)
    ans = int(m.group(1).replace(",", "")) if m else None
    u = r.get("usage") or {}
    return {"seed": seed, "temp": temp, "answer": ans, "correct": ans == TRUTH,
            "completion_tokens": u.get("completion_tokens"),
            "declared_insufficient": "INSUFFICIENT" in txt,
            "emits_ground_truth": bool(re.search(rf"(?<!\d){TRUTH}(?!\d)", txt)),
            "emits_table_value": bool(re.search(rf"(?<!\d){TVAL}(?!\d)", txt)),
            "wall_s": r["wall_s"], "text": txt}


def gate3(server, max_tokens: int) -> dict:
    """Seeded-compose ceiling: hand the model a best-case state and ask. Isolates the closing step
    from recording and retention entirely — if this fails, COMPOSE is the blocked joint."""
    state = best_case_state(SPEC)
    user = (f"INTEGRATION STATE:\n{state}\n\nQuestion: {SPEC['scoring_question']}\n"
            "Reason briefly from the state, then end with: ANSWER: <integer>")
    out = {"gate": "GATE-3 seeded compose", "state_used": state, "frames": {}}
    for name, system in (("legacy", LEGACY_CLOSING), ("chain", CLOSE_SYSTEM)):
        rows = []
        for seed, temp in DRAWS:
            r = ask(server, system, user, seed, temp, max_tokens)
            rows.append(r)
            print(f"    [{name:6s}] seed={seed:>2} t={temp} -> ANSWER={r['answer']} "
                  f"correct={r['correct']} ({r['wall_s']}s)", flush=True)
        sampled = [r for r in rows if r["temp"] == 0.7]
        out["frames"][name] = {"draws": rows,
                               "sampled_correct": sum(r["correct"] for r in sampled),
                               "sampled_n": len(sampled),
                               "anchor_correct": next(r["correct"] for r in rows if r["temp"] == 0.0)}
        f = out["frames"][name]
        print(f"    [{name:6s}] sampled {f['sampled_correct']}/{f['sampled_n']}, "
              f"anchor correct={f['anchor_correct']} (anchor never pooled)", flush=True)
    return out


def gate1(server, max_tokens: int) -> dict:
    """Backfill defense: fragment-2 only (call site + adder, NO table). Any decode emitting the
    ground truth means the answer is guessable and every chain success becomes uninterpretable."""
    user = (f"Here is the only code available:\n\n{SPEC['fragment2_text']}\n\n"
            f"Question: {SPEC['scoring_question']}\nShow your reasoning briefly, then give the "
            f"final answer on its own line as: ANSWER: <integer or INSUFFICIENT>")
    rows = []
    for seed, temp in DRAWS:
        r = ask(server, BACKFILL_SYSTEM, user, seed, temp, max_tokens)
        rows.append(r)
        print(f"    seed={seed:>2} t={temp} -> ANSWER={r['answer']} gt={r['emits_ground_truth']} "
              f"tval={r['emits_table_value']} ({r['wall_s']}s)", flush=True)
    any_gt = any(r["emits_ground_truth"] for r in rows)
    verdict = "PASS (backfill-defended)" if not any_gt else "FAIL (guessable — chain uninterpretable)"
    print(f"    GATE-1 {verdict}: no decode emitted {TRUTH} == {not any_gt}", flush=True)
    return {"gate": "GATE-1 backfill", "draws": rows,
            "any_decode_emits_ground_truth": any_gt, "verdict": verdict}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["student", "floor", "both"], default="both")
    ap.add_argument("--gate", choices=["1", "3", "both"], default="both")
    # SCALE RUNG (2026-07-25): run the SAME frozen GATE-3 seeded state against a model that is not
    # a Stage-A arm, to turn "the scale confound is named, not resolved" into a measured curve.
    # Deliberately an override here rather than a new entry in stagea_chain_gate.ARMS: that dict
    # belongs to the verdict-bearing runner and must not be perturbed. Non-verdict either way.
    ap.add_argument("--model", default=None,
                    help="explicit GGUF path, overriding --arm (scale rungs; requires --label)")
    ap.add_argument("--label", default=None,
                    help="output name for --model runs, e.g. qwen7b_q4 -> companion_qwen7b_q4.json")
    ap.add_argument("--max-tokens", type=int, default=1200)
    ap.add_argument("--out", default="runs/stageA_chain_gate/_companion")
    ap.add_argument("--ctx", type=int, default=24576)
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--threads", type=int, default=24)
    ap.add_argument("--port", type=int, default=8099)
    args = ap.parse_args()

    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    exe = ROOT / "models" / "llamacpp" / "llama-server.exe"
    if args.model:
        if not args.label:
            raise SystemExit("--model requires --label (names the output file)")
        model_path = Path(args.model)
        if not model_path.is_absolute():
            model_path = ROOT / model_path
        if not model_path.exists():
            raise SystemExit(f"no such model: {model_path}")
        arms = [(args.label, model_path)]
    else:
        arms = [(a, ARMS[a]) for a in
                (["student", "floor"] if args.arm == "both" else [args.arm])]
    for arm, model in arms:
        print(f"\n{'=' * 78}\nCOMPANION CHECKS — arm: {arm}\n{'=' * 78}", flush=True)
        server = LlamaServer(str(exe), str(model), ctx=args.ctx, port=args.port,
                             threads=args.threads, n_gpu_layers=args.ngl)
        server.ensure_running()
        res = {"_meta": {"arm": arm, "model": str(model), "diagnostic": True,
                         "scale_rung": bool(args.model), "ctx": args.ctx,
                         "verdict_eligible": False,
                         "note": "E2PRIME-PREREG §6 companion checks — reported separately from "
                                 "the chain verdict; cannot soften a chain-gate outcome",
                         "max_tokens": args.max_tokens,
                         "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}}
        try:
            if args.gate in ("1", "both"):
                print("  GATE-1 backfill defense (fragment-2 only)", flush=True)
                res["gate1"] = gate1(server, args.max_tokens)
            if args.gate in ("3", "both"):
                print("  GATE-3 seeded compose (best-case state)", flush=True)
                res["gate3"] = gate3(server, args.max_tokens)
        finally:
            server.stop()
        (out_dir / f"companion_{arm}.json").write_text(
            json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  -> {out_dir / f'companion_{arm}.json'}", flush=True)


if __name__ == "__main__":
    main()
