"""VALIDITY GATE for an API rung (default 72b). Robustness != validity: the first 72B run produced
plausible-looking numbers from CORRUPT data (arms silently truncated at state=6tok by spurious 400s,
seeds crashed and dropped). This gate refuses to certify a run that carries corruption, and is meant
to run BEFORE summarize_p7.py is trusted. Exit 1 on FAIL.

FAIL conditions:
  - any required result file missing, or any required arm key absent;
  - ANY truncation in any arm  -> at 32k ctx our peak prompt is ~24k Qwen-tok, so nothing legitimately
    overflows; a truncation == a spurious provider error mis-handled == corruption;
  - any closing answered None via context overflow (overflow_http set);
  - any recorded upstream provider != the pinned one (default DeepInfra) -> mixed weights/quant;
  - a RECORD-positive coupled seed whose final state is missing either fragment (988 table value or
    1365 adder) -> the same bar the 14B passed.

  python validate_72b.py --model 72b --n 10
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def seeds(n):
    return [(42, 0.0)] + [(s, 0.7) for s in range(1, n)]


def load(tag):
    f = HERE / f"p7_results_{tag}.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def providers_in(arm):
    provs = []
    for rec in arm.get("passes", []) or []:
        provs.append(rec.get("provider"))
    cl = arm.get("closing")
    if isinstance(cl, dict):
        provs.append(cl.get("provider"))
    if "final_state" in arm and "passes" not in arm:   # dense arm
        provs.append(arm.get("provider"))
    return [p for p in provs if p is not None]


def check_arm(label, arm, fails, expect_provider):
    if arm is None:
        fails.append(f"{label}: arm MISSING")
        return
    if arm.get("truncated"):
        fails.append(f"{label}: TRUNCATED at pass {arm.get('truncated_at_pass')} "
                     f"(n_passes_run={arm.get('n_passes_run')}, http={arm.get('truncated_http')}) "
                     f"= CORRUPTION — nothing legitimately overflows at 32k")
    cl = arm.get("closing") or {}
    if cl.get("overflow_http"):
        fails.append(f"{label}: closing OVERFLOW (http {cl.get('overflow_http')}) -> answer dropped")
    bad = sorted({p for p in providers_in(arm) if p != expect_provider})
    if bad:
        fails.append(f"{label}: upstream provider(s) {bad} != pinned {expect_provider}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="72b")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--expect-provider", default="DeepInfra")
    a = ap.parse_args()
    M, EP = a.model, a.expect_provider
    spec = json.loads((HERE / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    val, adder, gt = (str(spec["table_value_for_queried"]),
                      str(spec["reconciliation_adder_cents"]),
                      spec["ground_truth_answer"])

    fails, rows = [], []
    for seed, temp in seeds(a.n):
        lab = f"s{seed} t{temp:g}"
        d = load(f"{M}_spec_s{seed}_t{temp:g}")
        nd = load(f"{M}_mp6_neutral_s{seed}_t{temp:g}")
        if d is None:
            fails.append(f"{lab}: MISSING spec file")
            rows.append((seed, temp, "MISS", "-", "-", "-"))
            continue
        if nd is None:
            fails.append(f"{lab}: MISSING neutral file")
        for name in ("dense", "verbatim_only", "coupled_full"):
            check_arm(f"{lab} spec/{name}", d.get(name), fails, EP)
        if nd is not None:
            check_arm(f"{lab} neutral/coupled_full", nd.get("coupled_full"), fails, EP)

        cf = d.get("coupled_full") or {}
        recorded = bool((cf.get("final_mapping") or {}).get("queried_mapping"))
        fs = cf.get("final_state") or ""
        frag = "-"
        if recorded:
            hv, ha = val in fs, adder in fs
            frag = f"988={hv},1365={ha}"
            if not (hv and ha):
                fails.append(f"{lab}: RECORD-positive but coupled final state missing fragment(s) ({frag})")
        provs = sorted(set(providers_in(cf)))
        tr = ";".join(n for n in ("dense", "verbatim_only", "coupled_full")
                      if (d.get(n) or {}).get("truncated")) or "-"
        rows.append((seed, temp, "ok", ",".join(provs) or "none", "REC" if recorded else "-", tr))

    print("=" * 84)
    print(f"VALIDITY GATE — model={M}  n={a.n}  pinned-provider={EP}  GT={gt}")
    print("=" * 84)
    print(f"{'seed':>4} {'t':>4} | {'file':5} {'provider':16} {'rec':4} {'truncated-arms':22}")
    for seed, temp, fstat, pv, rec, tr in rows:
        print(f"{seed:>4} {temp:>4.1f} | {fstat:5} {pv:16} {rec:4} {tr:22}")
    print("-" * 84)
    if fails:
        print(f"\n*** GATE FAILED — {len(fails)} problem(s). DO NOT trust headline numbers. ***")
        for f in fails:
            print("  FAIL:", f)
        sys.exit(1)
    print("\nGATE PASSED — all files present, zero truncations, provider consistent, fragments intact.")
    print("Safe to run summarize_p7.py and surface the contrast.")


if __name__ == "__main__":
    main()
