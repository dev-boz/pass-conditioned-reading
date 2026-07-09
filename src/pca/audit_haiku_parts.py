"""Quality-gate the Haiku worker outputs before merge (E0-final).

Worker reliability is mixed (some misread the task, some rush). Line count is
not enough — flag any part that is missing, short, has duplicate/stub summaries,
or whose summaries are implausibly short. Prints PASS/FAIL per batch and the
list of batch numbers to re-run.

Usage: uv run python -m pca.audit_haiku_parts --dir data/views --n-batches 30
"""

from __future__ import annotations

import argparse
import glob as globmod
import json
import statistics as st
from pathlib import Path


def audit_file(fp: Path, args) -> bool:
    if not fp.exists():
        print(f"{fp.name}: MISSING")
        return False
    recs, ok = [], True
    for line in fp.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            ok = False
    if not recs:
        print(f"{fp.name}: EMPTY")
        return False
    words = [len(r.get("view_text", "").split()) for r in recs]
    distinct = len(set(r.get("view_text", "") for r in recs))
    medw = int(st.median(words)) if words else 0
    fields_ok = all({"doc_id", "k", "K", "view_text", "slice_tokens"} <= set(r) for r in recs)
    passed = (ok and fields_ok and len(recs) == args.expect_lines
              and distinct >= args.min_distinct
              and args.min_median_words <= medw <= args.max_median_words)
    print(f"{fp.name}: {'PASS' if passed else 'FAIL'}  lines={len(recs)} distinct={distinct} "
          f"med_words={medw} min_words={min(words)} json_ok={ok} fields_ok={fields_ok}")
    return passed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="data/views")
    ap.add_argument("--glob", default=None, help="audit files matching this glob instead of numbered batches")
    ap.add_argument("--n-batches", type=int, default=30)
    ap.add_argument("--expect-lines", type=int, default=80)
    ap.add_argument("--min-distinct", type=int, default=75)
    ap.add_argument("--min-median-words", type=int, default=150)
    ap.add_argument("--max-median-words", type=int, default=480)  # ~512-tok budget; flag oversized essays
    args = ap.parse_args()
    d = Path(args.dir)

    if args.glob:
        files = sorted(d.glob(args.glob))
        fails = [fp.name for fp in files if not audit_file(fp, args)]
        print(f"\nPASS {len(files) - len(fails)}/{len(files)}")
        print(("FAIL: " + " ".join(fails)) if fails else "ALL PASS")
        return

    rerun = []
    for b in range(args.n_batches):
        if not audit_file(d / f"views_haiku_part_{b:02d}.jsonl", args):
            rerun.append(b)
    print(f"\nPASS {args.n_batches - len(rerun)}/{args.n_batches}")
    print(("RE-RUN batches: " + " ".join(f"{b:02d}" for b in rerun)) if rerun else "ALL PASS — ready to merge")


if __name__ == "__main__":
    main()
