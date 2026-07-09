"""P7 — pre-run guard checks on the realized views (model-free, $0). Mirrors P6's guard discipline.

  (A) fires-on-source: the queried table entry + the adder are present in the host doc.
  (B) dense-floor: neither fragment's discriminating values are in the dense head+tail window.
  (C) State-D / structure-preserving: the table value + queried key + the adder SURVIVE into the
      realized Phase-A coarse views (so coupled CAN record them from Phase-A) AND no single Phase-B
      verbatim tile holds BOTH the table entry and the call site (so the split is real).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pca.planted import build_schedule          # noqa: E402
from pca.textutils import n_tokens              # noqa: E402
from compress_code import compress_code         # noqa: E402

V, R, STAGE_FRACS = 3000, 5, (0.34, 0.67)
DENSE_FILL, DENSE_HEAD_FRAC = 14000, 0.5


def load_turns(path: Path) -> list[dict]:
    turns = []
    for line in path.open(encoding="utf-8"):
        r = json.loads(line)
        turns.append({"turn": r["turn"], "seg": r["seg"], "text": r["content"],
                      "tokens": n_tokens(r["content"])})
    return turns


def dense_window_text(turns: list[dict]) -> str:
    head_budget = int(DENSE_FILL * DENSE_HEAD_FRAC)
    head, ht, i = [], 0, 0
    while i < len(turns) and ht + turns[i]["tokens"] <= head_budget:
        head.append(i); ht += turns[i]["tokens"]; i += 1
    tail, tt, j = [], 0, len(turns) - 1
    while j > i and tt + turns[j]["tokens"] <= (DENSE_FILL - ht):
        tail.append(j); tt += turns[j]["tokens"]; j -= 1
    return "\n".join(turns[k]["text"] for k in sorted(set(head) | set(tail)))


def main():
    spec = json.loads((HERE / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    turns = load_turns(HERE / "fixture" / "host_doc.jsonl")
    qcode = spec["queried_code"]
    tval = str(spec["table_value_for_queried"])           # "988"
    adder = str(spec["reconciliation_adder_cents"])       # "1365"
    entry = f"{qcode}: {tval}"                             # "23: 988" (the table line)
    call = "compute_line_surcharge"
    table_decl = "REGION_SURCHARGE_CENTS = {"

    sch = build_schedule(turns, V, R, STAGE_FRACS)
    phaseA = [p for p in sch if p["phase"] == "A"]
    phaseB = [p for p in sch if p["phase"] == "B"]
    print(f"schedule: {len(phaseA)} Phase-A chunks + {len(phaseB)} Phase-B tiles (V={V}, R={R})")

    # ---- (A) fires-on-source
    src = "\n".join(t["text"] for t in turns)
    assert entry in src and f"RECONCILIATION_ADDER_CENTS = {adder}" in src, "(A) fragment not on source"
    print(f"(A) fires-on-source: table entry '{entry}' and adder {adder} present in host doc  PASS")

    # ---- (B) dense-floor: discriminating values not in the head+tail window
    dense = dense_window_text(turns)
    assert entry not in dense and call not in dense, "(B) fragment leaks into dense window"
    print(f"(B) dense-floor: neither '{entry}' nor '{call}' in dense head+tail window  PASS")

    # ---- (C1) structure-preserving: table + adder survive realized Phase-A coarse views
    A_views = [compress_code(p["slice_text"], V) for p in phaseA]
    all_A = "\n".join(A_views)
    sizes = [(n_tokens(p["slice_text"]), n_tokens(v)) for p, v in zip(phaseA, A_views)]
    table_chunks = [i for i, v in enumerate(A_views) if table_decl in v]
    entry_chunks = [i for i, v in enumerate(A_views) if entry in v]
    adder_chunks = [i for i, v in enumerate(A_views) if f"RECONCILIATION_ADDER_CENTS = {adder}" in v]
    assert entry in all_A, "(C1) queried table entry did NOT survive into any Phase-A view"
    assert f"RECONCILIATION_ADDER_CENTS = {adder}" in all_A, "(C1) adder did NOT survive Phase-A"
    print(f"(C1) structure-preserving Phase-A: table decl in chunks {table_chunks}, "
          f"queried entry '{entry}' in chunks {entry_chunks}, adder in chunks {adder_chunks}  PASS")
    for i, (raw, comp) in enumerate(sizes):
        print(f"     chunk {i}: {raw}->{comp} tok ({round(raw/max(comp,1),1)}x)")

    # ---- (C2) split is real: no single Phase-B tile holds BOTH fragments
    f1_tiles = [i for i, p in enumerate(phaseB) if entry in p["view_text"] or table_decl in p["view_text"]]
    f2_tiles = [i for i, p in enumerate(phaseB) if call in p["view_text"]]
    overlap = set(f1_tiles) & set(f2_tiles)
    assert f1_tiles and f2_tiles, "(C2) a fragment is missing from all Phase-B tiles"
    assert not overlap, f"(C2) tile(s) {overlap} hold BOTH fragments — split not real"
    gap = min(f2_tiles) - max(f1_tiles)
    print(f"(C2) split real: fragment-1 in Phase-B tile(s) {f1_tiles}, fragment-2 in {f2_tiles}, "
          f"no overlap; tile gap = {gap}  PASS")

    print(f"\nALL GUARDS PASS. Ground truth: compute_line_surcharge({qcode}) = "
          f"{spec['table_value_for_queried']} + {adder} = {spec['ground_truth_answer']}")


if __name__ == "__main__":
    main()
