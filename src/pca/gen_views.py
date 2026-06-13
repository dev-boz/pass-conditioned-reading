"""Fetch corpus + generate the full view sequence per document.

Usage: uv run python -m pca.gen_views --config data/views/views_config.yaml
Idempotent: skips work if outputs exist and match the config doc count.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .compressor import get_compressor
from .schedule import generate_views
from .textutils import n_tokens


def fetch_corpus(cfg: dict, out_path: Path) -> list[dict]:
    from datasets import load_dataset

    c = cfg["corpus"]
    ds = load_dataset(c["dataset"], split=c["split"], streaming=True)
    docs = []
    for i, rec in enumerate(ds):
        if i >= c["scan_limit"] or len(docs) >= c["n_docs"]:
            break
        text = rec[c["text_field"]].strip()
        nt = n_tokens(text)
        if c["min_doc_tokens"] <= nt <= c["max_doc_tokens"]:
            docs.append({"doc_id": f"govreport-{i:05d}", "n_tokens": nt, "text": text})
    with out_path.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    return docs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    root = Path(args.config).resolve().parents[2]  # repo root (data/views/config -> root)

    corpus_path = root / cfg["outputs"]["corpus_path"]
    views_path = root / cfg["outputs"]["views_path"]
    n_docs = cfg["corpus"]["n_docs"]

    if corpus_path.exists():
        docs = [json.loads(l) for l in corpus_path.open(encoding="utf-8")]
        print(f"corpus exists: {len(docs)} docs")
    else:
        docs = fetch_corpus(cfg, corpus_path)
        print(f"fetched corpus: {len(docs)} docs -> {corpus_path}")
    if len(docs) < n_docs:
        print(f"WARNING: only {len(docs)} docs matched the filter (wanted {n_docs})")

    K, V = cfg["schedule"]["K"], cfg["schedule"]["V"]
    comp = get_compressor(cfg["compressor"])

    if views_path.exists():
        n_views = sum(1 for _ in views_path.open(encoding="utf-8"))
        if n_views == len(docs) * K:
            print(f"views exist and complete: {n_views} records — nothing to do")
            return
    with views_path.open("w", encoding="utf-8") as f:
        for j, d in enumerate(docs):
            for rec in generate_views(d["doc_id"], d["text"], K, V, comp):
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if (j + 1) % 25 == 0:
                print(f"  {j + 1}/{len(docs)} docs", flush=True)
    print(f"wrote views -> {views_path}")


if __name__ == "__main__":
    sys.exit(main())
