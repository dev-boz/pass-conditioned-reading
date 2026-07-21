"""PROBE — where exactly does the close break? Design input, NOT a gate arm.

READ THIS BEFORE QUOTING ANY NUMBER FROM HERE. Several variants below feed the model a state that
was filtered USING ORACLE KNOWLEDGE of which entries matter. That is forcing under
E2PRIME-CRITERION §2 and it is deliberate: the point is to locate the blocked joint, not to give
the student a fair shot. No variant here is repeatable as a gate arm, none may be pooled with the
battery, and a number from here can never raise a chain-gate verdict. The frozen battery stands.

The question these answer: the battery's closing turn receives a ~7.5K-token state that the student
itself wrote, most of it "Group N: helpers ..." filler, and one draw held BOTH operands and still
answered 86. Two very different failure modes look identical from outside —

  compose-blocked   the model cannot combine two values it holds
  legibility-blocked the model cannot FIND its own operands inside its own state

They point at different redesigns. Compose-blocked argues the closing step needs work;
legibility-blocked argues the state representation does — which is the case
docs/DISCO-NATIVE-ARCHITECTURE.md makes for a retrieval-structured latent slot bank over a flat
text brief. Distinguishing them is worth more than another battery.

Variants (all replay ONLY the closing turn against archived final states):
  asis        the battery's own closing, re-asked — the control
  distilled   ORACLE: only state entries containing either operand survive
  modules     ORACLE-LITE: entries naming the pricing/fulfillment modules survive
  retrieve    unfiltered state, but told to locate and quote relevant entries before computing
  budget      unfiltered state, much larger decode budget (see also closing_budget_diag.py)

  python experiments/e2prime/probe_closing.py --arm student --variant all
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
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from pca.llm import LlamaServer                                   # noqa: E402
from stagea_chain_gate import ARMS, CLOSE_SYSTEM, P7              # noqa: E402

SPEC = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
TRUTH, TVAL, ADDER = (SPEC["ground_truth_answer"], SPEC["table_value_for_queried"],
                      SPEC["reconciliation_adder_cents"])
QCODE = SPEC["queried_code"]

RETRIEVE_SYSTEM = (
    CLOSE_SYSTEM + " Before answering, first quote the specific state entries that bear on the "
    "question, then reason from the quoted entries only.")


def distill(state: str) -> str:
    """ORACLE FILTER: keep only entries holding an operand. Forcing by construction."""
    keep = [ln for ln in state.splitlines()
            if re.search(rf"(?<!\d){TVAL}(?!\d)", ln) or re.search(rf"(?<!\d){ADDER}(?!\d)", ln)]
    return "\n".join(keep)


def modules(state: str) -> str:
    """ORACLE-LITE: keep entries naming the two modules the chain runs through. Still forcing —
    it names where to look — but it does not hand over the values themselves."""
    pats = ("region_tables", "REGION_SURCHARGE", "line_quote", "RECONCILIATION",
            "compute_line_surcharge", "pricing/", "fulfillment/")
    return "\n".join(ln for ln in state.splitlines() if any(p.lower() in ln.lower() for p in pats))


def build(variant: str, rec: dict) -> tuple[str, str, int]:
    state = rec["final_state"]
    system, budget = CLOSE_SYSTEM, 1200
    if variant == "distilled":
        state = distill(state)
    elif variant == "modules":
        state = modules(state)
    elif variant == "retrieve":
        system = RETRIEVE_SYSTEM
    elif variant == "budget":
        budget = 4096
    if variant == "queryfirst":
        # PREFILL ORDER, not oracle: the scoring question is legitimately available at close time;
        # this only moves it BEFORE the state so the model reads the ~7.7K-token brief already
        # knowing what it is looking for (query-conditioned retrieval). It is a train/eval mismatch
        # — the student was trained with the question AFTER the state — so it is a design probe, not
        # a verdict arm. Tests the maintainer's prefill-order hypothesis on the composition step.
        user = (f"Question: {SPEC['scoring_question']}\n\nFINAL STATE:\n{state}\n\n"
                "Using ONLY the state above, reason briefly, then end with: ANSWER: <integer>")
    else:
        user = (f"FINAL STATE:\n{state}\n\nQuestion: {SPEC['scoring_question']}\n"
                "Reason briefly from the state, then end with: ANSWER: <integer>")
    return system, user, budget


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["student", "floor"], default="student")
    ap.add_argument("--variant", default="all",
                    help="asis|distilled|modules|retrieve|budget|all (comma-separated)")
    ap.add_argument("--records", default="runs/stageA_chain_gate")
    ap.add_argument("--out", default="runs/stageA_chain_gate/_probe")
    ap.add_argument("--ctx", type=int, default=24576)
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--threads", type=int, default=24)
    ap.add_argument("--port", type=int, default=8100)
    args = ap.parse_args()

    all_variants = ["asis", "distilled", "modules", "retrieve", "budget"]
    variants = all_variants if args.variant == "all" else args.variant.split(",")
    rec_dir, out_dir = ROOT / args.records, ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for f in sorted(rec_dir.glob(f"{args.arm}_s*.json")):
        if f.name.startswith(("manifest", "smoke_", "_")):
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("complete"):
            records.append(r)
    if not records:
        raise SystemExit(f"no complete {args.arm} records in {rec_dir}")

    print(f"PROBE (design input, NOT a gate arm; distilled/modules use ORACLE filtering)")
    print(f"{len(records)} archived {args.arm} draw(s) x {len(variants)} variant(s)\n")
    server = LlamaServer(str(ROOT / "models" / "llamacpp" / "llama-server.exe"), str(ARMS[args.arm]),
                         ctx=args.ctx, port=args.port, threads=args.threads, n_gpu_layers=args.ngl)
    server.ensure_running()
    out = {"_meta": {"probe": True, "verdict_eligible": False, "gate_legal": False,
                     "note": "ORACLE-filtered variants are forcing under E2PRIME-CRITERION §2 and "
                             "exist to locate the blocked joint; never poolable with the battery",
                     "arm": args.arm, "model": str(ARMS[args.arm]),
                     "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
           "results": {}}
    try:
        for v in variants:
            rows = []
            for rec in records:
                seed, temp = rec["_meta"]["seed"], rec["_meta"]["temp"]
                system, user, budget = build(v, rec)
                r = server.chat(system, user, max_tokens=budget, temperature=temp, seed=seed)
                txt = r["text"]
                m = re.search(r"ANSWER:\s*(-?\d[\d,]*)", txt)
                ans = int(m.group(1).replace(",", "")) if m else None
                u = r.get("usage") or {}
                rows.append({"seed": seed, "temp": temp, "battery_answer": rec["closing"]["answer"],
                             "answer": ans, "correct": ans == TRUTH,
                             "state_lines_in": len(rec["final_state"].splitlines()),
                             "state_lines_used": len(user.split("FINAL STATE:\n")[1]
                                                     .split("\n\nQuestion:")[0].splitlines()),
                             "completion_tokens": u.get("completion_tokens"),
                             "wall_s": r["wall_s"], "text": txt})
                print(f"  [{v:>9}] seed={seed:>2} lines {rows[-1]['state_lines_in']:>4}->"
                      f"{rows[-1]['state_lines_used']:>3} ANSWER={str(ans):>6} "
                      f"correct={rows[-1]['correct']} ({r['wall_s']}s)", flush=True)
            sampled = [r for r in rows if r["temp"] == 0.7]
            out["results"][v] = {"draws": rows, "sampled_correct": sum(r["correct"] for r in sampled),
                                 "sampled_n": len(sampled)}
            print(f"  [{v:>9}] sampled {out['results'][v]['sampled_correct']}/"
                  f"{out['results'][v]['sampled_n']} correct\n", flush=True)
            (out_dir / f"probe_{args.arm}.json").write_text(
                json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    finally:
        server.stop()

    print("summary (sampled draws only):")
    for v, r in out["results"].items():
        print(f"  {v:>9}: {r['sampled_correct']}/{r['sampled_n']}")
    print("\nReading: 'asis' reproduces the battery. If 'distilled'/'modules' lift the rate while "
          "'asis' stays flat, the joint is state LEGIBILITY, not composition — the model holds the "
          "operands and cannot find them in its own brief, which is an argument about the state "
          "representation. If nothing lifts, composition itself is blocked. Neither reading may be "
          "carried into the chain verdict.")


if __name__ == "__main__":
    main()
