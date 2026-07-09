"""Emit deterministic schedule slices for Haiku-subagent compression (E0-final).

Python owns the schedule (slice lengths + hashed placement, D1-D5); Haiku
workers own only C() (summarize each slice to target_tokens). This writes
slices.jsonl; a worker reads its assigned doc_ids and writes view records;
merge_views.py reassembles views.jsonl.

Usage: uv run python -m pca.gen_slices --config data/views/views_config.yaml --n 5 --out data/views/slices_val.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from .schedule import generate_slices


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--n", type=int, default=None, help="number of docs (default: all in corpus)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    root = Path(args.config).resolve().parents[2]
    corpus = [json.loads(l) for l in (root / cfg["outputs"]["corpus_path"]).open(encoding="utf-8")]
    if args.n:
        corpus = corpus[: args.n]
    K, V = cfg["schedule"]["K"], cfg["schedule"]["V"]
    out = root / args.out if not Path(args.out).is_absolute() else Path(args.out)
    n_slices = 0
    with out.open("w", encoding="utf-8") as f:
        for d in corpus:
            for rec in generate_slices(d["doc_id"], d["text"], K, V):
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n_slices += 1
    print(f"wrote {n_slices} slices ({len(corpus)} docs x {K}) -> {out}")


if __name__ == "__main__":
    main()
