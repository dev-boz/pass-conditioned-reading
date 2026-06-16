"""Merge the per-delivery-path Haiku view files into one E0-final view set (D30).

Three first-class paths, each in its own file with provenance:
  local  -> data/views/views_haiku.jsonl         (claude -p, this box)
  remote -> data/views/views_haiku_remote.jsonl  (claude -p over SSH, a second OAuth host)
  kiro   -> data/views/views_haiku_kiro.jsonl    (Kiro CLI headless, credit-metered)

Stamps `gen_path` on records that lack it (the OAuth files predate the field),
dedups by (doc_id,k) preferring the more-authoritative first-party path
(local > remote > kiro), reports any overlap or missing (doc_id,k), and writes the
merged set. Expects 300 docs x K=8 = 2,400 when complete.

Usage:
  python -m pca.merge_paths --out data/views/views_haiku_final.jsonl
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

# authority order: earlier = preferred on (doc_id,k) collision
PATHS = [
    ("local", "data/views/views_haiku.jsonl"),
    ("remote", "data/views/views_haiku_remote.jsonl"),
    ("kiro", "data/views/views_haiku_kiro.jsonl"),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/views/views_haiku_final.jsonl")
    ap.add_argument("--expect-docs", type=int, default=300)
    ap.add_argument("--expect-k", type=int, default=8)
    args = ap.parse_args()

    merged: dict[tuple, dict] = {}
    overlaps = []
    per_path = Counter()
    for label, fp in PATHS:
        p = Path(fp)
        if not p.exists():
            print(f"  (skip {label}: {fp} absent)")
            continue
        n = 0
        for line in p.open(encoding="utf-8"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            r.setdefault("gen_path", label)
            key = (r["doc_id"], r["k"])
            if key in merged:
                overlaps.append((key, merged[key]["gen_path"], r["gen_path"]))
                continue  # keep the more-authoritative (earlier) path
            merged[key] = r
            per_path[r["gen_path"]] += 1
            n += 1
        print(f"  {label}: +{n} new (file {fp})")

    out = Path(args.out)
    with out.open("w", encoding="utf-8") as fh:
        for key in sorted(merged):
            fh.write(json.dumps(merged[key], ensure_ascii=False) + "\n")

    total = len(merged)
    expect = args.expect_docs * args.expect_k
    docs = {k[0] for k in merged}
    print(f"\nmerged total={total} (expect {expect}) docs={len(docs)} per_path={dict(per_path)}")
    if overlaps:
        print(f"WARNING: {len(overlaps)} (doc_id,k) overlaps across paths (kept authoritative): "
              f"{overlaps[:5]}")
    if total != expect:
        # report which (doc_id,k) are missing, grouped
        all_keys = {(d, k) for d in sorted(docs) for k in range(1, args.expect_k + 1)}
        missing = sorted(all_keys - set(merged))
        print(f"INCOMPLETE: {len(missing)} missing (doc_id,k); first 20: {missing[:20]}")
    else:
        print(f"COMPLETE: wrote {out}")


if __name__ == "__main__":
    main()
