"""Merge Haiku-worker partial view files into views.jsonl (E0-final).

Adds view_tokens + compression_ratio (computed in Python, not trusted from the
worker), sorts by (doc_id, k), validates completeness against slices.jsonl, and
runs the contamination audit (Haiku must not inject positional metadata).

Usage: uv run python -m pca.merge_views --slices data/views/slices_val.jsonl \
         --parts "data/views/views_haiku_val.jsonl" --out data/views/views_haiku.jsonl
"""

from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path

from .textutils import n_tokens

LEAK = [
    (re.compile(r"(?i)\bpass\s+\d+\s+of\s+\d+\b"), "pass-N-of-K"),
    (re.compile(r"(?i)\b[kK]\s*[:=]\s*\d+\b"), "k=N"),
    (re.compile(r"(?i)\bchunk\s*#?\d+\b"), "chunk-idx"),
    (re.compile(r"govreport-\d+"), "doc_id-echo"),
    (re.compile(r"(?i)\bcompression[ _-]?(ratio|level|schedule)\b"), "schedule-annotation"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slices", required=True, help="slices.jsonl used to generate the views (completeness check)")
    ap.add_argument("--parts", required=True, help="glob of worker output files")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    expected = {(json.loads(l)["doc_id"], json.loads(l)["k"]) for l in Path(args.slices).open(encoding="utf-8")}
    recs = []
    for fp in sorted(glob.glob(args.parts)):
        for l in Path(fp).open(encoding="utf-8"):
            recs.append(json.loads(l))

    seen, leaks, n_leak = {}, {}, 0
    for r in recs:
        vt = n_tokens(r["view_text"])
        r["view_tokens"] = vt
        r["compression_ratio"] = round(r["slice_tokens"] / max(vt, 1), 3)
        for pat, name in LEAK:
            if pat.search(r["view_text"]):
                leaks[name] = leaks.get(name, 0) + 1
                n_leak += 1
        seen[(r["doc_id"], r["k"])] = r

    missing = expected - set(seen)
    dupes = len(recs) - len(seen)
    recs = sorted(seen.values(), key=lambda r: (r["doc_id"], r["k"]))
    out = Path(args.out)
    with out.open("w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"merged {len(recs)} views -> {out}")
    print(f"  completeness: {len(seen)}/{len(expected)} (doc,k) pairs; missing={len(missing)} dupes={dupes}")
    print(f"  contamination (view_text): {leaks or 'none'} ({n_leak} hits)")
    if missing:
        print("  MISSING:", sorted(missing)[:10])


if __name__ == "__main__":
    main()
