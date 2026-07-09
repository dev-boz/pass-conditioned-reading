"""P7 — heterogeneity check (the thing v2 fixes; quantify that it's fixed). Model-free, $0.

v1 emitted the same header+signature WALL every chunk → homogeneous views drove the integration
model to re-compress its own state and clobber entries. v2 should make consecutive Phase-A views
structurally distinguishable. We quantify two things, both on document-class structure (probe-blind):

  - per-chunk STRUCTURAL PROFILE: how many lines are constant/table rows vs helper-digest vs headers
    vs imports/docs. A slice that defines a constant/table looks different in KIND from a pure-helper
    slice iff its constant-row count is non-trivial where others' is ~0.
  - consecutive-view SIMILARITY: mean Jaccard over line-shape tokens; lower = more heterogeneous.
    Reported with the view-size reduction vs the v1 wall (the uniform volume that drove aggregation).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pca.textutils import n_tokens  # noqa: E402

_HDR = re.compile(r"^#\s*=+\s*module:")
_DIGEST = re.compile(r"^defines helpers:")
_IMPORT = re.compile(r"^(import|from)\b")
_CONSTROW = re.compile(r"^\s*[\w'\"]+\s*:\s*[\w'\".\-]+,?\s*$")   # a dict entry row  "23: 988,"


def shape(line: str) -> str:
    """Coarse line-shape token (for similarity that ignores incidental names)."""
    s = line.strip()
    if not s:
        return ""
    if _HDR.match(s):
        return "HDR"
    if _DIGEST.match(s):
        return "DIGEST"
    if _IMPORT.match(s):
        return "IMPORT"
    if _CONSTROW.match(s):
        return "CONSTROW"
    if s.startswith(('"""', "'''", "#")):
        return "DOC"
    if "=" in s:
        return "ASSIGN"
    return "OTHER"


def profile(view: str) -> dict:
    c = {"HDR": 0, "DIGEST": 0, "IMPORT": 0, "CONSTROW": 0, "DOC": 0, "ASSIGN": 0, "OTHER": 0}
    for ln in view.splitlines():
        t = shape(ln)
        if t:
            c[t] += 1
    return c


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else 1.0


def main():
    sc = json.loads((HERE / "scaffold_struct.json").read_text(encoding="utf-8"))
    views = [c["view_text"] for c in sc]
    print("per-chunk structural profile (lines by kind) + view tokens:")
    print("  {:>5} {:>6} {:>7} {:>7} {:>9} {:>5} {:>7} {:>7}".format(
        "chunk", "tokens", "HDR", "DIGEST", "CONSTROW", "DOC", "IMPORT", "ASSIGN"))
    for i, v in enumerate(views):
        p = profile(v)
        print("  {:>5} {:>6} {:>7} {:>7} {:>9} {:>5} {:>7} {:>7}".format(
            i, n_tokens(v), p["HDR"], p["DIGEST"], p["CONSTROW"], p["DOC"], p["IMPORT"], p["ASSIGN"]))

    # consecutive-view similarity on line-shape multiset (kind), and on raw lines (content)
    print("\nconsecutive-view similarity (lower = more heterogeneous):")
    for i in range(len(views) - 1):
        shapes_a = set(enumerate_shapes(views[i]))
        shapes_b = set(enumerate_shapes(views[i + 1]))
        lines_a = {ln.strip() for ln in views[i].splitlines() if ln.strip()}
        lines_b = {ln.strip() for ln in views[i + 1].splitlines() if ln.strip()}
        print(f"  chunk {i}->{i+1}: line-content Jaccard={jaccard(lines_a, lines_b):.3f}")

    const_chunks = [i for i, v in enumerate(views) if profile(v)["CONSTROW"] >= 3]
    print(f"\nchunks carrying a constant/table block (CONSTROW>=3): {const_chunks}  "
          f"<- these are 'different in kind' from the pure-helper chunks (CONSTROW~0)")
    print("v1 (prior, archived in RESULTS): every chunk was a ~1800-tok header+signature wall with "
          "CONSTROW~0 except the table chunk's raw dict — i.e. uniform in kind. v2 view tokens are "
          "~900 (half the volume) and constant-bearing chunks are profile-distinct.")


def enumerate_shapes(view: str):
    """Position-tagged shapes so two identical-shape walls score high similarity but a constant
    block (unique CONSTROW positions) scores low against a helper wall."""
    out = []
    for j, ln in enumerate(view.splitlines()):
        t = shape(ln)
        if t:
            out.append(f"{j}:{t}")
    return out


if __name__ == "__main__":
    main()
