"""E2′ corpus builder (docs/E2PRIME-PREREG.md §4, incl. the 2026-07-10 prose amendment).

Slices:
  (a) prose  — the FROZEN E0 corpus + its frozen production views (views_haiku_final.jsonl,
      2,400 views = 300 docs x K=8, gen_path provenance). Docs used verbatim (~10-34K tok);
      no new compressor calls. First --n-prose doc_ids with complete K=8 view coverage.
  (b) synth  — fresh-seed generator-family codebases (gen_synth_code.py), disjoint pools,
      per-seed planted split structures. Declared distribution-overfit risk.
  (c) real   — permissively-licensed Python from the WSL venv site-packages, concatenated
      into pseudo-repos (one block per file, files >6K tok skipped to stay tile-compatible),
      license + version recorded per doc from dist-info METADATA.

Writes data/e2prime/corpus.jsonl and copies the frozen prose corpus + views into the repo's
data/ paths (gitignored) so teacher_gen runs self-contained. Run scan_leakage.py AFTER this.

  python experiments/e2prime/build_corpus.py --n-prose 120 --n-synth 90 --n-real 90
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
from gen_synth_code import synth_doc            # noqa: E402
from pca.textutils import n_tokens              # noqa: E402

D_CORPUS = Path(r"D:\Context diffusion\DiSCo\pca\data\corpus\corpus.jsonl")
D_VIEWS = Path(r"D:\Context diffusion\DiSCo\pca\data\views\views_haiku_final.jsonl")
SITE_PKGS = Path(r"\\wsl.localhost\Ubuntu\home\boz\e2prime-venv\lib\python3.12\site-packages")
REAL_PKGS = ["transformers", "datasets", "accelerate", "peft", "trl"]  # all Apache-2.0 family
MAX_BLOCK_TOK = 6000        # skip larger single files (keeps blocks Phase-B-tile compatible)
SYNTH_SEED0 = 20001


def pkg_license(pkg: str) -> str:
    for di in SITE_PKGS.glob(f"{pkg}-*.dist-info"):
        meta = di / "METADATA"
        if meta.exists():
            for line in meta.read_text(encoding="utf-8", errors="replace").splitlines():
                if line.startswith(("License-Expression:", "License:")) and len(line.split(":", 1)[1].strip()) > 1:
                    return f"{di.name.split('-')[1]}|{line.split(':', 1)[1].strip()[:60]}"
                if line.startswith("Classifier: License ::"):
                    return f"{di.name.split('-')[1]}|{line.split('::')[-1].strip()}"
    return "unknown"


def real_docs(n_docs: int, lo_tok: int = 40_000, hi_tok: int = 80_000) -> list[dict]:
    rng = random.Random(4242)
    out = []
    for pkg in REAL_PKGS:
        root = SITE_PKGS / pkg
        if not root.exists():
            print(f"  real: {pkg} not found, skipping")
            continue
        lic = pkg_license(pkg)
        files = sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)
        rng.shuffle(files)
        blocks, toks, part = [], 0, 0
        target = rng.randint(lo_tok, hi_tok)
        for p in files:
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            t = n_tokens(txt)
            if not (50 <= t <= MAX_BLOCK_TOK):
                continue
            rel = p.relative_to(SITE_PKGS).as_posix()
            blocks.append(f"# ===== module: {rel} =====\n{txt}")
            toks += t
            if toks >= target:
                out.append({"doc_id": f"realcode-{pkg}-{part:02d}", "kind": "code",
                            "blocks": blocks,
                            "provenance": {"source": "wsl-venv site-packages", "package": pkg,
                                           "license": lic, "total_tokens": toks}})
                blocks, toks, part = [], 0, part + 1
                target = rng.randint(lo_tok, hi_tok)
                if len(out) >= n_docs:
                    return out
        if blocks and toks >= lo_tok // 2:
            out.append({"doc_id": f"realcode-{pkg}-{part:02d}", "kind": "code",
                        "blocks": blocks,
                        "provenance": {"source": "wsl-venv site-packages", "package": pkg,
                                       "license": lic, "total_tokens": toks}})
        if len(out) >= n_docs:
            return out
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-prose", type=int, default=120)
    ap.add_argument("--n-synth", type=int, default=90)
    ap.add_argument("--n-real", type=int, default=90)
    ap.add_argument("--synth-lo", type=int, default=40_000)
    ap.add_argument("--synth-hi", type=int, default=80_000)
    args = ap.parse_args()

    out_path = ROOT / "data" / "e2prime" / "corpus.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ---- (a) prose: frozen E0 corpus + complete-coverage doc_ids -----------------------
    kcov = Counter()
    for line in D_VIEWS.open(encoding="utf-8"):
        kcov[json.loads(line)["doc_id"]] += 1
    complete = {d for d, c in kcov.items() if c == 8}
    prose = []
    for line in D_CORPUS.open(encoding="utf-8"):
        d = json.loads(line)
        if d["doc_id"] in complete:
            prose.append({"doc_id": d["doc_id"], "kind": "prose", "text": d["text"],
                          "provenance": {"source": "E0 frozen corpus (govreport)",
                                         "views": "views_haiku_final.jsonl (D29/D30 frozen)",
                                         "n_tokens": d.get("n_tokens")}})
        if len(prose) >= args.n_prose:
            break
    print(f"(a) prose: {len(prose)} docs (complete K=8 frozen-view coverage: {len(complete)}/300)")

    # copy the frozen artifacts into the repo's runtime paths (both gitignored)
    (ROOT / "data" / "views").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "corpus").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "views" / "views_haiku_final.jsonl").write_bytes(D_VIEWS.read_bytes())
    (ROOT / "data" / "corpus" / "corpus.jsonl").write_bytes(D_CORPUS.read_bytes())
    print("    frozen views + corpus copied into data/ (gitignored)")

    # ---- (b) synth: fresh seeds, sizes drawn per seed ----------------------------------
    synth = []
    for i in range(args.n_synth):
        seed = SYNTH_SEED0 + i
        target = random.Random(seed ^ 0xE2).randint(args.synth_lo, args.synth_hi)
        synth.append(synth_doc(seed, target))
        if (i + 1) % 15 == 0:
            print(f"(b) synth: {i + 1}/{args.n_synth}")
    print(f"(b) synth: {len(synth)} docs")

    # ---- (c) real ------------------------------------------------------------------------
    real = real_docs(args.n_real)
    lic_counts = Counter(d["provenance"]["license"] for d in real)
    print(f"(c) real: {len(real)} docs | licenses: {dict(lic_counts)}")

    docs = prose + synth + real
    with out_path.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    sizes = [d["provenance"].get("total_tokens") or d["provenance"].get("n_tokens") or 0
             for d in docs]
    print(f"\ncorpus: {len(docs)} docs -> {out_path}")
    print(f"tokens: total≈{sum(sizes):,} | prose {len(prose)} / synth {len(synth)} / real {len(real)}")
    print("NEXT: python experiments/e2prime/scan_leakage.py --corpus data/e2prime/corpus.jsonl")


if __name__ == "__main__":
    main()
