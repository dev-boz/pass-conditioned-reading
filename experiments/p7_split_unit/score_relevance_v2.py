"""Relevance-control v2 — mechanical pre-filter over the 5-draw battery results.

Scans each draw's per-pass state snapshots + final state for the PRE-REGISTERED decisive
attribution strings (RELEVANCE-CONTROL-V2.md): decl strings, exact module paths, shared
event keys, handler/label value words, and the v2 positive control (STAGE_ORDER /
queue/pipeline.py / run_pipeline / stage names). Output is the PRE-FILTER ONLY — tier
assignment (0/1/2) is by manual-confirmed read of the flagged states; generic category
mentions ("routing", "queue") never count for any table.

  python experiments/p7_split_unit/score_relevance_v2.py [--glob "p7_results_*7b*.json"]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))

RC = SPEC["relevance_control"]
PC = SPEC["positive_control"]

PROBES = {
    "PC/STAGE_ORDER": [PC["decl"], PC["module"], PC["consumer"]] + PC["stages"],
    "REL/EVENT_DISPATCH": ([RC["relevant_decl"], "routing/router.py", "dispatch("]
                           + list(RC["relevant_table"].keys())[:4]
                           + list(RC["relevant_table"].values())[:6]),
    "ARB/DISPLAY_LABELS": ([RC["arbitrary_decl"], "routing/labels.py", "label("]
                           + list(RC["arbitrary_table"].values())[:6]),
}
# verbatim-pair pre-filter (v1's relevant_kv/alias_kv analogue), full 24 pairs each
PAIRS = {
    "REL pairs": [f'"{k}": "{v}"' for k, v in RC["relevant_table"].items()],
    "ARB pairs": [f'"{k}": "{v}"' for k, v in RC["arbitrary_table"].items()],
    "PC order": [str(PC["stages"])],
}


def states_of(run: dict) -> list[str]:
    arm = run.get("coupled_full") or run
    snaps = arm.get("snapshots") or []
    out = [s if isinstance(s, str) else json.dumps(s) for s in snaps]
    for key in ("final_state", "final_state_render", "state_final"):
        if isinstance(arm.get(key), str):
            out.append(arm[key])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="p7_results_*7b*.json")
    args = ap.parse_args()
    files = sorted(HERE.glob(args.glob))
    if not files:
        print(f"no result files match {args.glob} in {HERE}")
        return
    print(f"fixture_version={SPEC.get('fixture_version', 1)} | {len(files)} result file(s)\n")
    for f in files:
        run = json.loads(f.read_text(encoding="utf-8"))
        texts = states_of(run)
        joined = "\n".join(texts)
        final = texts[-1] if texts else ""
        print(f"── {f.name}  (passes with state: {len(texts)})")
        for label, probes in PROBES.items():
            hits = [p for p in probes if p in joined]
            fin = [p for p in probes if p in final]
            print(f"   {label:22s} any-pass: {len(hits):2d} hit(s) {hits[:4]}"
                  f"{' …' if len(hits) > 4 else ''} | final-state: {len(fin)}")
        for label, probes in PAIRS.items():
            n_any = sum(1 for p in probes if p in joined)
            n_fin = sum(1 for p in probes if p in final)
            print(f"   {label:22s} verbatim pairs any-pass: {n_any}/{len(probes)} | final: {n_fin}")
        size = len(final.split())
        print(f"   final-state size ≈ {size} words\n")
    print("Pre-filter only. Tier calls (0/1/2, ≥4/5 rule) are manual-confirmed per "
          "RELEVANCE-CONTROL-V2.md; attribution requires the decisive strings above in a "
          "role-describing context — category-name mentions alone never count.")


if __name__ == "__main__":
    main()
