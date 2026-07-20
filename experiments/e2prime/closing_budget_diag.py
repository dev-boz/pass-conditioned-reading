"""DIAGNOSTIC — did the closing decode cap hide a compose, or is compose genuinely absent?

NOT A VERDICT INSTRUMENT. The frozen battery result stands whatever this says. Several battery
draws spent their entire 1,200-token closing budget without reaching an ANSWER line, while holding
the operands in state. "No answer" then has two very different readings — the student cannot
combine what it holds (a real COMPOSE failure, criterion §5) or it never got to the answer because
it was still reciting a ~7.5K-token state (an instrument limit). Those imply different
architecture-revision decisions, so the difference has to be measured rather than argued.

Method: replay ONLY the closing turn against each draw's ARCHIVED final state, with the identical
closing system/user prompt, the identical seed and temperature, and a much larger decode budget.
The recording passes are not re-run and no state is rebuilt, so nothing about the draw changes
except how much room the close had to finish. Each reply records the server's own
usage.completion_tokens, so cap-hits are decidable here rather than heuristic.

Read it as: if answers appear at a larger budget, the battery's COMPOSE rate is budget-limited and
must be reported as such; if they do not, the closing budget was never the binding constraint.

  python experiments/e2prime/closing_budget_diag.py --arm student --budget 4096
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from pca.llm import LlamaServer                                  # noqa: E402
from stagea_chain_gate import ARMS, CLOSE_SYSTEM, P7             # noqa: E402

SPEC = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
TRUTH = SPEC["ground_truth_answer"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["student", "floor"], default="student")
    ap.add_argument("--budget", type=int, default=4096, help="closing max_tokens for the replay")
    ap.add_argument("--records", default="runs/stageA_chain_gate")
    ap.add_argument("--out", default="runs/stageA_chain_gate/_closing_budget_diag")
    ap.add_argument("--ctx", type=int, default=24576)
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--threads", type=int, default=24)
    ap.add_argument("--port", type=int, default=8098)
    args = ap.parse_args()

    rec_dir, out_dir = ROOT / args.records, ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    files = [f for f in sorted(rec_dir.glob(f"{args.arm}_s*.json"))
             if not f.name.startswith(("manifest", "smoke_", "_"))]
    records = []
    for f in files:
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("complete"):
            records.append(r)
    if not records:
        raise SystemExit(f"no complete {args.arm} records in {rec_dir}")
    print(f"replaying the closing turn for {len(records)} {args.arm} draw(s) at "
          f"max_tokens={args.budget} (battery used {records[0]['_meta'].get('closing_max_tokens')})")

    model = ARMS[args.arm]
    server = LlamaServer(str(ROOT / "models" / "llamacpp" / "llama-server.exe"), str(model),
                         ctx=args.ctx, port=args.port, threads=args.threads, n_gpu_layers=args.ngl)
    server.ensure_running()
    out = {"_meta": {"diagnostic": True, "verdict_eligible": False,
                     "note": "closing-turn replay at a larger decode budget; the frozen battery "
                             "result is unchanged by anything here",
                     "arm": args.arm, "model": str(model), "replay_budget": args.budget,
                     "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
           "draws": []}
    try:
        for r in records:
            seed, temp = r["_meta"]["seed"], r["_meta"]["temp"]
            t0 = time.time()
            # byte-identical closing prompt: replayed from the archive, not rebuilt
            resp = server.chat(r["closing"]["system"], r["closing"]["user"],
                               max_tokens=args.budget, temperature=temp, seed=seed)
            txt = resp["text"]
            m = re.search(r"ANSWER:\s*(-?\d[\d,]*)", txt)
            ans = int(m.group(1).replace(",", "")) if m else None
            usage = resp.get("usage") or {}
            row = {"seed": seed, "temp": temp,
                   "battery_answer": r["closing"]["answer"], "replay_answer": ans,
                   "replay_correct": ans == TRUTH,
                   "completion_tokens": usage.get("completion_tokens"),
                   "hit_replay_cap": usage.get("completion_tokens") == args.budget,
                   "declared_insufficient": "INSUFFICIENT" in txt,
                   "final_state_tokens": r["final_state_tokens"],
                   "wall_s": round(time.time() - t0, 1), "raw_output": txt}
            out["draws"].append(row)
            print(f"  seed={seed:>2} battery={str(r['closing']['answer']):>6} -> "
                  f"replay={str(ans):>6} correct={row['replay_correct']} "
                  f"completion_tokens={row['completion_tokens']} cap_hit={row['hit_replay_cap']} "
                  f"({row['wall_s']}s)", flush=True)
            (out_dir / f"{args.arm}_budget{args.budget}.json").write_text(
                json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    finally:
        server.stop()

    d = out["draws"]
    n_new = sum(r["replay_correct"] and r["battery_answer"] != TRUTH for r in d)
    n_cap = sum(bool(r["hit_replay_cap"]) for r in d)
    print(f"\n{args.arm}: {sum(r['replay_correct'] for r in d)}/{len(d)} produce {TRUTH} at "
          f"budget {args.budget}; {n_cap}/{len(d)} still hit the cap.")
    if n_new:
        print(f"  !! {n_new} draw(s) produce the answer ONLY at the larger budget. The battery's "
              f"COMPOSE rate is budget-limited and must be reported as such — the frozen verdict "
              f"still stands, but it cannot be read as 'cannot compose'.")
    else:
        print("  No draw gains the answer from the larger budget: the closing decode budget was "
              "not the binding constraint, and the battery's COMPOSE reading is safe.")


if __name__ == "__main__":
    main()
