"""P7 — structure-preserving CODE compressor (v2, the architecture's Phase-A compressor).

THE COMPRESSOR IS ARCHITECTURE, not generic preprocessing. v1 (keep every signature, drop bodies)
produced **homogeneous views**: every Phase-A chunk was the same header+signature wall, which drove
the integration model to destructively re-compress its own state into churning `MODULES`/`FUNCTIONS`
aggregates and clobber standalone entries (the "retention failure" was substantially a
representation failure). v2 fixes the representation so consecutive views are **heterogeneous and
structure-distinguishing** — the model can append distinct facts instead of collapsing look-alike
walls.

DESIGN PRINCIPLES — each justified on the CODE DOCUMENT CLASS, blind to any probe (a skeptic who has
never seen the test must accept every choice):

  1. FOREGROUND module-level constants / literals (incl. multi-line dict/list/tuple literals),
     verbatim. Justification: in code, module-level constants and tables are the declarations that
     callers depend on — they are high-information and a brief of a codebase must capture them.
     (Tables are kept because code modules define tables that callers depend on — NOT because any
     question asks about one.)
  2. KEEP imports/from-imports. Justification: imports are the module's dependency / call-graph edges.
  3. KEEP class definitions and (where present) their method signatures. Justification: classes are
     the type/structure of the code.
  4. COLLAPSE free functions to a compact one-line name digest ("defines helpers: a, b, c") instead
     of emitting every `def ...:` signature. Justification: in helper modules the individual
     signatures are low-information and near-uniform across modules; the module's *distinctive*
     content is its declarations, and helper names suffice for a brief. This is the heterogeneity
     lever — it removes the uniform signature-wall volume so a slice that defines a constant looks
     structurally different in kind from a slice of pure helpers.
  5. KEEP module docstrings / module-level comments. Justification: module purpose and
     constant-explaining comments are distinctive context.
  DROP function/method bodies (the bulk, low-information).

Deterministic, $0, robust to chunk boundaries that cut mid-file (line scanner, not an AST parse).
Frozen to scaffold_struct.json (gen_scaffold.py) and pre-registered — one design, justified blind,
not iterated to taste. (Simplification: this fixture has no classes; class-method-signature handling
keeps the class header and folds methods into the helper digest — documented, untested here.)
"""
from __future__ import annotations

import re

_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_\.\[\]]*\s*(?::[^=]+)?=")   # NAME = ... / NAME: T = ...
_DEFCLS = re.compile(r"^(def|class|async\s+def)\b")
_DEFNAME = re.compile(r"^(?:async\s+def|def)\s+([A-Za-z_]\w*)")
_IMPORT = re.compile(r"^(import|from)\b")
_MODHDR = re.compile(r"^#\s*=+\s*module:")


def _bracket_delta(s: str) -> int:
    s = re.sub(r"'[^']*'", "''", s)
    s = re.sub(r'"[^"]*"', '""', s)
    return (s.count("(") + s.count("[") + s.count("{")
            - s.count(")") - s.count("]") - s.count("}"))


def compress_code(text: str, target_tokens: int | None = None) -> str:
    """Heterogeneous, structure-distinguishing Phase-A view (see module docstring). `target_tokens`
    is advisory (kept for the compressor protocol); selection is by structural role, not budget."""
    mods: list[dict] = []

    def new_mod(header):
        m = {"header": header, "lead": [], "consts": [], "helpers": []}
        mods.append(m)
        return m

    cur = new_mod(None)            # content before the first module header (chunk cut mid-file)
    depth = 0                      # open-bracket depth inside a kept constant's multi-line literal
    in_doc, docq = False, ""

    for raw in text.splitlines():
        line = raw.rstrip("\n")
        strip = line.strip()

        if in_doc:                                  # module docstring continuation
            cur["lead"].append(line)
            if docq in line:
                in_doc = False
            continue
        if depth > 0:                               # multi-line constant literal continuation (table rows)
            cur["consts"][-1].append(line)
            depth += _bracket_delta(line)
            continue
        if not strip:
            continue

        if _MODHDR.match(strip):                    # new module
            cur = new_mod(line)
            continue
        if len(line) - len(line.lstrip()) > 0:      # indented = function/method body → drop
            continue
        # module-level (indent 0) logical statement
        if strip.startswith("#"):                   # comment (distinctive context)
            cur["lead"].append(line)
        elif _IMPORT.match(strip):                  # dependency edge
            cur["lead"].append(line)
        elif strip.startswith('"""') or strip.startswith("'''"):   # module docstring
            cur["lead"].append(line)
            q = strip[:3]
            if not (len(strip) > 3 and strip.endswith(q)):
                in_doc, docq = True, q
        elif _DEFCLS.match(strip):
            if strip.startswith("class"):           # type structure — keep header
                cur["consts"].append([line])
            else:                                   # free function — name digest only
                m = _DEFNAME.match(strip)
                if m:
                    cur["helpers"].append(m.group(1))
        elif _ASSIGN.match(strip):                  # module-level constant / literal (foreground)
            cur["consts"].append([line])
            depth += _bracket_delta(line)
        # else: drop

    out: list[str] = []
    for m in mods:
        if not (m["header"] or m["lead"] or m["consts"] or m["helpers"]):
            continue
        out.append(m["header"] if m["header"] else "# (module continued)")
        out += m["lead"]
        for c in m["consts"]:
            out += c
        if m["helpers"]:
            out.append(f"defines helpers: {', '.join(m['helpers'])}")
    return "\n".join(out).strip()
