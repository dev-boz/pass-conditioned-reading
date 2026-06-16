"""Paired fidelity check: does Kiro's claude-haiku-4.5 behave like the
first-party `claude -p` Haiku used for the 426 OAuth views?

Takes N (doc_id,k) pairs already compressed via the OAuth path, re-compresses
the SAME slice through the Kiro backend, and compares paired: word count,
compression ratio, summary-to-summary content overlap, and source-number recall.
If Kiro tracks claude -p, the mixed-generator E0-final dataset is clean and the
gate can be declared non-provisional. ~N*0.05 credits.

Run from the pca dir with KIRO_API_KEY set:
  python experiments/e0_view_classifier/kiro_fidelity_check.py --n 8
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "src"))

from pca.compressor import KiroCompressor  # noqa: E402
from pca.textutils import n_tokens  # noqa: E402

_WORD = re.compile(r"[A-Za-z']+")
_NUM = re.compile(r"\d[\d,.]*")


def content_words(s: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(s) if len(w) > 3}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / max(len(a | b), 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--oauth", default="data/views/views_haiku.jsonl")
    ap.add_argument("--slices", default="data/views/slices.jsonl")
    args = ap.parse_args()

    oauth = {(r["doc_id"], r["k"]): r for r in
             (json.loads(l) for l in Path(args.oauth).open(encoding="utf-8"))}
    slices = {(r["doc_id"], r["k"]): r for r in
              (json.loads(l) for l in Path(args.slices).open(encoding="utf-8"))}

    keys = sorted(oauth)
    # spread across the file (positions + docs), deterministic
    step = max(len(keys) // args.n, 1)
    picked = keys[::step][: args.n]

    comp = KiroCompressor()

    def do(key):
        sl = slices[key]
        kv = comp.compress(sl["slice_text"], 512)
        return key, kv

    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        for key, kv in ex.map(do, picked):
            ov = oauth[key]["view_text"]
            wo, wk = len(ov.split()), len(kv.split())
            cro = oauth[key]["compression_ratio"]
            crk = round(slices[key]["slice_tokens"] / max(n_tokens(kv), 1), 3)
            jac = jaccard(content_words(ov), content_words(kv))
            src_nums = set(_NUM.findall(slices[key]["slice_text"]))
            rec_o = len(src_nums & set(_NUM.findall(ov))) / max(len(src_nums), 1)
            rec_k = len(src_nums & set(_NUM.findall(kv))) / max(len(src_nums), 1)
            results.append((key, wo, wk, cro, crk, jac, rec_o, rec_k))
            print(f"{key[0]} k{key[1]}: words oauth={wo} kiro={wk} | "
                  f"cr oauth={cro} kiro~={crk} | jaccard={jac:.2f} | "
                  f"num-recall oauth={rec_o:.2f} kiro={rec_k:.2f}", flush=True)

    n = len(results)
    mean = lambda i: sum(r[i] for r in results) / n
    print("\n=== MEANS (n=%d) ===" % n)
    print(f"words: oauth={mean(1):.0f} kiro={mean(2):.0f}")
    print(f"compression_ratio: oauth={mean(3):.1f} kiro~={mean(4):.1f}")
    print(f"summary-summary jaccard (content words): {mean(5):.2f}")
    print(f"source-number recall: oauth={mean(6):.2f} kiro={mean(7):.2f}")


if __name__ == "__main__":
    main()
