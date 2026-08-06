"""The role-specialized compressor as a RESOLUTION OPERATOR — C(x, sigma), not C(x).

WHY THIS EXISTS. `experiments/p7_split_unit/compress_code.py` (v2) established the right frame —
"the compressor is architecture, not generic preprocessing" — and it is probe-blind and frozen. But
its `target_tokens` argument is *advisory*: selection is by structural role, so it emits one fixed
severity and therefore one fixed ratio. Measured on the E2' fixture across the six pyramid levels it
runs 11.8x at EVERY level (5,573 tok for the whole document, 347 tok for a sixteenth). A schedule
whose compressor has no sigma knob cannot be a resolution ladder: k would index nothing, which is
precisely the defect docs/SCHEDULE-DISCREPANCY-2026-07-30.md found in the D25 schedule. So the
pyramid needs the same compressor with a severity parameter.

THE LADDER. Each step is justified on the CODE DOCUMENT CLASS, blind to any probe — the
COMPRESSOR-V2.md standard: a skeptic who has never seen the fixture must accept every choice. The
ordering answers one question: as the budget tightens, what does a brief of a codebase give up first?

  sigma 0  verbatim            The module exactly as written, bodies included.
                               WHY IT EXISTS: without a verbatim rung the operator can only tighten,
                               so a tile whose sigma-1 rendering already fits the budget stops there
                               and spends nothing more. Measured: levels 2-5 pinned at a flat 11.8x
                               and level 5 emitted 347 tokens against a 3,000-token budget. A
                               resolution operator has to be able to spend the budget as well as
                               save it, so the ladder starts at "no compression at all".
  sigma 1  drop_bodies         Keep module header, docstrings/comments, imports, class headers, ALL
                               module-level constants verbatim, free functions as a name digest.
                               (Identical to compress_code v2 — this rung is the already-
                               pre-registered design.)
                               WHY FIRST: function bodies are the bulk and the lowest-information
                               part of a module; the declarations callers depend on are elsewhere.
  sigma 2  drop_prose          Also drop module docstrings and module-level comments.
                               WHY: prose *about* the code is commentary on declarations that are
                               still present; the declaration is the primary source. When something
                               must go, the gloss goes before the thing it glosses.
  sigma 3  drop_edges          Also drop imports and the helper name digest.
                               WHY: the dependency graph and the helper inventory describe how a
                               module is wired and what it can do; the constants say what callers
                               will actually read out of it. Forced to choose, a brief keeps the
                               values over the wiring.
  sigma 4  shape_collections   Collection literals above a small threshold collapse to their SHAPE
                               (entry count, key range, value range); scalar constants stay verbatim.
                               WHY: a scalar costs one line, so summarizing it saves nothing and is
                               never worth doing. A large collection is the only place where real
                               bytes remain, and its shape is the affordable description of it.
                               NOTE, stated in advance: this is the rung where key->value BINDING
                               dies while the collection's range survives. That is a prediction of
                               the design, not an accommodation of a result — it is the mechanism
                               behind the archived 8/11-vs-1/11 scalar-vs-table-row measurement.
  sigma 5  names_only          Declaration NAMES only; every value dropped; helpers as a count.
                               WHY: at this budget the only affordable claim is what a module
                               declares, not what the declarations equal.
  sigma 6  module_inventory    Module path only.
                               WHY: the floor. The document still tiles; nothing but structure left.

BUDGET ALLOCATION. sigma is chosen PER MODULE, not per slice. Every module starts at `sigma_min`;
while the rendered view exceeds the budget, sigma is raised on the LARGEST currently-rendered module
(ties broken by document order). Largest-first is a SIZE rule, not a content rule, so it stays
probe-blind: the compressor never asks what a module is about, only how many tokens it costs. The
realized sigma distribution is returned by `compress_graded_report`, because "at level 1 it ran
sigma 5 on 96 modules and sigma 4 on 10" is the interesting datum for designing the next compressor.

Deterministic, $0, no model. Line scanner (not an AST parse), so it is robust to tile boundaries
that cut mid-file — same robustness requirement as compress_code v2.
"""

from __future__ import annotations

import re

from .textutils import n_tokens

# --- line classification (same conventions as p7_split_unit/compress_code.py v2) -------------
_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_\.\[\]]*\s*(?::[^=]+)?=")   # NAME = ... / NAME: T = ...
_ASSIGN_NAME = re.compile(r"^([A-Za-z_][A-Za-z0-9_\.\[\]]*)\s*(?::[^=]+)?=\s*(.*)$")
_DEFCLS = re.compile(r"^(def|class|async\s+def)\b")
_DEFNAME = re.compile(r"^(?:async\s+def|def)\s+([A-Za-z_]\w*)")
_CLSNAME = re.compile(r"^class\s+([A-Za-z_]\w*)")
_IMPORT = re.compile(r"^(import|from)\b")
_MODHDR = re.compile(r"^#\s*=+\s*module:\s*(.*?)\s*=*\s*$")

# The schedule renders turns as "<role>: <content>", so the first line of every turn carries a role
# prefix that would hide a module header from the scanner. Stripped explicitly rather than left to
# fall through _ASSIGN by accident (which is what happens without this).
_ROLE_PREFIX = re.compile(r"^(?:code|user|assistant|system|tool)\s*:\s*(?=#|\"\"\"|'''|\w)")

# A dict entry "23: 988," / "'ab': 'cd'," — used only for SHAPE summaries at sigma 4.
_DICT_ITEM = re.compile(r"""^\s*(['"]?)([^'":,]+)\1\s*:\s*(['"]?)([^'",]*)\3\s*,?\s*$""")

SIGMA_NAMES = {0: "verbatim", 1: "drop_bodies", 2: "drop_prose", 3: "drop_edges",
               4: "shape_collections", 5: "names_only", 6: "module_inventory"}
SIGMA_MIN, SIGMA_MAX = 0, 6

# A collection literal is collapsed at sigma 4 only if it is big enough that collapsing it buys
# anything. Below this it is cheaper to keep it whole than to describe it.
_COLLAPSE_MIN_ITEMS = 4


def _bracket_delta(s: str) -> int:
    s = re.sub(r"'[^']*'", "''", s)
    s = re.sub(r'"[^"]*"', '""', s)
    return (s.count("(") + s.count("[") + s.count("{")
            - s.count(")") - s.count("]") - s.count("}"))


def _num(s: str):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- parse
def parse_modules(text: str) -> list[dict]:
    """Line-scan a slice into per-module IR. Mirrors compress_code v2's scanner exactly for the
    kinds it recognises; adds explicit role-prefix handling and a scalar/collection split (needed
    for sigma 4, which treats the two differently)."""
    mods: list[dict] = []

    def new_mod(header: str | None, path: str | None):
        m = {"header": header, "path": path, "prose": [], "imports": [],
             "consts": [], "classes": [], "helpers": [], "raw": ([header] if header else [])}
        mods.append(m)
        return m

    cur = new_mod(None, None)      # content before the first module header (tile cut mid-file)
    depth = 0
    in_doc, docq = False, ""

    for raw in text.splitlines():
        line = _ROLE_PREFIX.sub("", raw.rstrip("\n"))
        strip = line.strip()

        mh0 = _MODHDR.match(strip)
        if not mh0:                                 # sigma 0 keeps the module exactly as written
            cur["raw"].append(line)

        if in_doc:                                  # module docstring continuation
            cur["prose"].append(line)
            if docq in line:
                in_doc = False
            continue
        if depth > 0:                               # multi-line literal continuation (table rows)
            cur["consts"][-1]["lines"].append(line)
            depth += _bracket_delta(line)
            continue
        if not strip:
            continue

        mh = _MODHDR.match(strip)
        if mh:
            cur = new_mod(line, mh.group(1) or None)
            continue
        if len(line) - len(line.lstrip()) > 0:      # indented = function/method body -> drop
            continue

        if strip.startswith("#"):
            cur["prose"].append(line)
        elif _IMPORT.match(strip):
            cur["imports"].append(line)
        elif strip.startswith('"""') or strip.startswith("'''"):
            cur["prose"].append(line)
            q = strip[:3]
            if not (len(strip) > 3 and strip.endswith(q)):
                in_doc, docq = True, q
        elif _DEFCLS.match(strip):
            if strip.startswith("class"):
                m = _CLSNAME.match(strip)
                cur["classes"].append({"name": m.group(1) if m else "?", "line": line})
            else:
                m = _DEFNAME.match(strip)
                if m:
                    cur["helpers"].append(m.group(1))
        elif _ASSIGN.match(strip):
            m = _ASSIGN_NAME.match(strip)
            name, rhs = (m.group(1), m.group(2)) if m else ("?", "")
            d = _bracket_delta(strip)
            cur["consts"].append({"name": name, "lines": [line],
                                  "collection": d > 0 or bool(re.match(r"^[\[{(]", rhs))})
            depth += d
    return mods


def _shape(const: dict) -> str:
    """SHAPE line for a collection literal: entry count + key/value ranges. Content-neutral —
    it describes the literal's extent, never which entries matter."""
    items = [_DICT_ITEM.match(ln) for ln in const["lines"][1:]]
    pairs = [(m.group(2).strip(), m.group(4).strip()) for m in items if m]
    body = " ".join(const["lines"])
    if not pairs:                                   # list/tuple/set: count separators only
        n = max(body.count(",") - (1 if body.rstrip().rstrip(")]}").rstrip().endswith(",") else 0), 0)
        return f"{const['name']} = <collection collapsed: ~{n + 1} items>"
    ks = [_num(k) for k in (p[0] for p in pairs)]
    vs = [_num(v) for v in (p[1] for p in pairs)]
    def rng(vals, raw):
        nums = [v for v in vals if v is not None]
        if len(nums) == len(raw) and nums:
            lo, hi = min(nums), max(nums)
            fmt = (lambda x: f"{x:g}")
            return f"{fmt(lo)}..{fmt(hi)}"
        return f"{raw[0][0] if isinstance(raw[0], tuple) else raw[0]}.." \
               f"{raw[-1][0] if isinstance(raw[-1], tuple) else raw[-1]}"
    kr = rng(ks, [p[0] for p in pairs])
    vr = rng(vs, [p[1] for p in pairs])
    return (f"{const['name']} = <collection collapsed: {len(pairs)} entries, "
            f"keys {kr}, values {vr}>")


def render_module(m: dict, sigma: int) -> list[str]:
    """One module at one severity. Every branch is a pure function of sigma and the IR."""
    header = m["header"] if m["header"] else "# (module continued)"
    if sigma <= 0:
        return list(m["raw"]) if m["raw"] else [header]
    if sigma >= 6:
        return [header]
    if sigma >= 5:
        names = [c["name"] for c in m["consts"]] + [c["name"] for c in m["classes"]]
        out = [header]
        if names:
            out.append(f"declares: {', '.join(names)}")
        if m["helpers"]:
            out.append(f"helpers: {len(m['helpers'])}")
        return out

    out = [header]
    if sigma <= 1:
        out += m["prose"]
    if sigma <= 2:
        out += m["imports"]
    for c in m["classes"]:
        out.append(c["line"])
    for c in m["consts"]:
        if sigma >= 4 and c["collection"] and len(c["lines"]) - 1 >= _COLLAPSE_MIN_ITEMS:
            out.append(_shape(c))
        else:
            out += c["lines"]
    if sigma <= 2 and m["helpers"]:
        out.append(f"defines helpers: {', '.join(m['helpers'])}")
    return out


def _render(mods: list[dict], sigmas: list[int]) -> str:
    out: list[str] = []
    for m, s in zip(mods, sigmas):
        if not (m["header"] or m["prose"] or m["imports"] or m["consts"]
                or m["classes"] or m["helpers"] or m["raw"]):
            continue
        out += render_module(m, s)
    return "\n".join(out).strip()


def compress_graded_report(text: str, target_tokens: int, sigma_min: int = SIGMA_MIN,
                           sigma_max: int = SIGMA_MAX) -> tuple[str, dict]:
    """Compress to `target_tokens`, returning (view, report).

    Every module starts at sigma_min; while over budget, the LARGEST currently-rendered module is
    pushed one rung down the ladder. Size-driven and deterministic, so no content judgement enters
    the allocation. Costs are precomputed per (module, sigma) so the loop is arithmetic, not
    repeated rendering."""
    mods = parse_modules(text)
    live = [i for i, m in enumerate(mods)
            if (m["header"] or m["prose"] or m["imports"] or m["consts"]
                or m["classes"] or m["helpers"] or m["raw"])]
    if not live:
        return text.strip(), {"n_modules": 0, "sigma_hist": {}, "sigma_max_used": None}

    cost = {i: {s: n_tokens("\n".join(render_module(mods[i], s)) + "\n")
                for s in range(sigma_min, sigma_max + 1)} for i in live}
    sig = {i: sigma_min for i in live}
    total = sum(cost[i][sig[i]] for i in live)

    while total > target_tokens:
        cand = [i for i in live if sig[i] < sigma_max]
        if not cand:
            break
        # largest rendered module first; document order breaks ties
        i = max(cand, key=lambda j: (cost[j][sig[j]], -j))
        total -= cost[i][sig[i]]
        sig[i] += 1
        total += cost[i][sig[i]]

    sigmas = [sig.get(i, sigma_max) for i in range(len(mods))]
    view = _render(mods, sigmas)
    hist: dict[str, int] = {}
    for i in live:
        hist[str(sig[i])] = hist.get(str(sig[i]), 0) + 1
    report = {"n_modules": len(live), "sigma_hist": hist,
              "sigma_min_used": min(sig[i] for i in live),
              "sigma_max_used": max(sig[i] for i in live),
              "sigma_names": {k: SIGMA_NAMES[int(k)] for k in hist},
              "view_tokens": n_tokens(view), "target_tokens": target_tokens}
    return view, report


class GradedCodeCompressor:
    """Compressor-protocol wrapper (`.compress(text, target_tokens) -> str`, `.name`) so the graded
    compressor drops into build_pyramid_schedule wherever ExtractiveCompressor goes."""

    name = "graded-structural-v1"

    def __init__(self, sigma_min: int = SIGMA_MIN, sigma_max: int = SIGMA_MAX):
        self.sigma_min, self.sigma_max = sigma_min, sigma_max
        self.last_report: dict | None = None

    def compress(self, text: str, target_tokens: int) -> str:
        view, rep = compress_graded_report(text, target_tokens, self.sigma_min, self.sigma_max)
        self.last_report = rep
        return view


def compress_graded(text: str, target_tokens: int) -> str:
    return compress_graded_report(text, target_tokens)[0]
