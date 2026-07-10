"""E2′ leakage gate (docs/E2PRIME-PREREG.md §4) — mechanical, zero-tolerance, archived.

Scans the training corpus for any contamination from the evaluation fixture:
  (i)  12-gram overlap (whitespace-normalized, case-folded) with the five planted texts
       and the positive control,
  (ii) the probe identifiers and probe-adjacent values,
  (iii) every key:value pair of every planted table.
Any hit names the offending doc; exit code 1. The scan output is committed alongside the
data card before training begins.

  python experiments/e2prime/scan_leakage.py --corpus data/e2prime/corpus.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = HERE.parent / "p7_split_unit" / "fixture" / "fixture_spec.json"

IDENTIFIERS = ["REGION_SURCHARGE_CENTS", "RECONCILIATION_ADDER_CENTS", "compute_line_surcharge",
               "CARRIER_FUEL_BP", "EVENT_DISPATCH", "DISPLAY_LABELS", "STAGE_ORDER",
               "run_pipeline", "quote_line", "surcharge_cents", "fuel_bp"]


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def ngrams(s: str, n: int = 12) -> set[str]:
    w = norm(s).split(" ")
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", default=str(HERE / "leakage_scan.json"))
    args = ap.parse_args()

    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    planted = [spec[k] for k in ("fragment1_text", "control_text", "relevant_text",
                                 "aliases_text", "fragment2_text") if k in spec]
    if "pc_text" in spec:
        planted.append(spec["pc_text"])
    planted_grams: set[str] = set()
    for t in planted:
        planted_grams |= ngrams(t)

    # Precision fix (2026-07-10, first full-corpus run): bare integers ("1365") matched
    # incidental numbers in real code — over-broad vs the prereg's "as table-adjacent
    # tokens" wording. Any actual copy vector is covered by identifiers, pair strings,
    # and 12-grams; integers are probed only in their table/arithmetic-adjacent shapes.
    value_probes = [f"{spec['queried_code']}: {spec['table_value_for_queried']}",
                    f"= {spec['reconciliation_adder_cents']}",
                    f"+ {spec['reconciliation_adder_cents']}",
                    f"= {spec['ground_truth_answer']}",
                    f": {spec['ground_truth_answer']}"]
    pair_probes = [f'"{k}": "{v}"' for tbl in ("relevant_table", "arbitrary_table")
                   for k, v in spec["relevance_control"][tbl].items()]
    table_probes = [f"{k}: {v}" for k, v in spec["table"].items()]

    hits, n_docs = [], 0
    for line in Path(args.corpus).open(encoding="utf-8"):
        if not line.strip():
            continue
        doc = json.loads(line)
        n_docs += 1
        text = doc.get("text") or "\n".join(doc.get("blocks", []))
        tn = norm(text)
        for ident in IDENTIFIERS:
            if ident.lower() in tn:
                hits.append({"doc_id": doc["doc_id"], "type": "identifier", "probe": ident})
        for p in value_probes + table_probes + pair_probes:
            if norm(p) in tn:
                hits.append({"doc_id": doc["doc_id"], "type": "value", "probe": p})
        if ngrams(text) & planted_grams:
            sample = sorted(ngrams(text) & planted_grams)[:3]
            hits.append({"doc_id": doc["doc_id"], "type": "12gram", "probe": sample})

    report = {"corpus": args.corpus, "n_docs": n_docs, "n_hits": len(hits), "hits": hits,
              "fixture_version": spec.get("fixture_version", 1)}
    Path(args.out).write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    if hits:
        print(f"LEAKAGE: {len(hits)} hit(s) across {n_docs} docs — drop the offending docs "
              f"and log the drops. Report: {args.out}")
        sys.exit(1)
    print(f"leakage scan CLEAN: 0 hits across {n_docs} docs. Report: {args.out}")


if __name__ == "__main__":
    main()
