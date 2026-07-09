"""P7 — focused high-N matrix driver (one model per invocation; unattended + RESUMABLE).

Runs, for the chosen model, the high-information set agreed for the Threadripper/1080Ti run
(skips deterministic re-runs, already-saturated re-runs, and the design-broken relevance control):

  gates       backfill (unit still unguessable) + compose ceiling           — n draws
  neutral     coupled_full Phase-A only (does the floor record un-prompted)  — n draws
  specifics   coupled_full + verbatim_only + dense, FULL end-to-end,         — n draws
              under the FAIR-SHOT specifics prompt (the headline: can it work
              at all + does coupled beat verbatim, on the closing ANSWER==2353)

Draws = temp-0 (seed 42) + (n-1) sampled temp-0.7 seeds; reported per-seed (never pooled).
Resumable: a draw whose result file already has the needed arms is skipped.

  # on the Threadripper, GPU (1080Ti, CUDA build): 7b then 14b
  python experiments/p7_split_unit/run_matrix.py --model 7b  --n 10 --ngl 99 --threads 24
  python experiments/p7_split_unit/run_matrix.py --model 14b --n 10 --ngl 99 --threads 24
  # subset / smaller N:
  python experiments/p7_split_unit/run_matrix.py --model 7b --n 4 --tests specifics
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable


def seeds(n):
    return [(42, 0.0)] + [(s, 0.7) for s in range(1, n)]


def done(tag, arms):
    f = HERE / f"p7_results_{tag}.json"
    if not f.exists():
        return False
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        return all(a in d for a in arms)
    except Exception:
        return False


def run(argv, log):
    line = " ".join(str(a) for a in argv)
    print(f"  >>> {line}", flush=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"\n##### {time.strftime('%H:%M:%S')}  {line}\n")
        f.flush()
        subprocess.run([PY] + argv, cwd=str(HERE), stdout=f, stderr=subprocess.STDOUT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="registry key (7b/14b)")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--ngl", type=int, default=None)
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--tests", default="gates,neutral,specifics")
    a = ap.parse_args()
    M, tests = a.model, a.tests.split(",")
    hw = (["--ngl", str(a.ngl)] if a.ngl is not None else []) + \
         (["--threads", str(a.threads)] if a.threads is not None else [])
    common = ["--model", M] + hw
    log = HERE / f"matrix_{M}.log"
    print(f"=== P7 matrix: model={M} n={a.n} tests={tests} ngl={a.ngl} threads={a.threads} ===", flush=True)

    if "gates" in tests:
        run(["backfill_check.py", "--model", M, "--n", str(a.n)] + hw, log)
        run(["compose_gate.py", "--model", M, "--n", str(a.n)] + hw, log)

    for seed, temp in seeds(a.n):
        sd = ["--seed", str(seed), "--temp", str(temp)]
        if "neutral" in tests:
            tag = f"{M}_mp6_neutral_s{seed}_t{temp:g}"
            if done(tag, ["coupled_full"]):
                print(f"  skip (done): {tag}", flush=True)
            else:
                run(["run.py", "--arm", "coupled_full", "--max-passes", "6"] + sd + common, log)
        if "specifics" in tests:
            tag = f"{M}_spec_s{seed}_t{temp:g}"
            if done(tag, ["coupled_full", "verbatim_only"]):
                print(f"  skip (done): {tag}", flush=True)
            else:
                run(["run.py", "--arm", "all"] + sd + common + ["--specifics"], log)

    print(f"=== matrix {M} complete; results p7_results_{M}_* + *_result_{M}.json ===", flush=True)


if __name__ == "__main__":
    main()
