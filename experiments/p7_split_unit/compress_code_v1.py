"""P7 — v1 code compressor (RECONSTRUCTED for the isolation control only; NOT the architecture).

This is the ORIGINAL signature-keeping compressor: keep module-level statements (constants/literals,
imports, defs/classes, decorators, comments, docstrings) + nested def/class SIGNATURES; drop bodies.
It produced the homogeneous header+signature WALLS (~1800 tok/chunk) that the v2 work replaced.

Kept verbatim from the pre-v2 `compress_code.py` so the v1+neutral-prompt control reproduces the old
representation exactly. The architecture's compressor is v2 (`compress_code.py`); this file exists
only to attribute the churn-absence (compressor vs neutral-prompt) — see COMPRESSOR-V2.md.
"""
from __future__ import annotations

import re

_ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_\.\[\]]*\s*(?::[^=]+)?=")
_DEFCLS = re.compile(r"^(def|class|async\s+def)\b")
_IMPORT = re.compile(r"^(import|from)\b")
_DECOR = re.compile(r"^@")
_HEADER = re.compile(r"^#")


def _bracket_delta(s: str) -> int:
    s = re.sub(r"'[^']*'", "''", s)
    s = re.sub(r'"[^"]*"', '""', s)
    return (s.count("(") + s.count("[") + s.count("{")
            - s.count(")") - s.count("]") - s.count("}"))


def compress_code(text: str, target_tokens: int | None = None) -> str:
    out: list[str] = []
    depth = 0
    in_tripus = False
    triq = ""
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        strip = line.strip()
        if in_tripus:
            out.append(line)
            if triq in line:
                in_tripus = False
            continue
        if depth > 0:
            out.append(line)
            depth += _bracket_delta(line)
            continue
        indent = len(line) - len(line.lstrip())
        keep = False
        if not strip:
            keep = False
        elif indent == 0:
            if (_ASSIGN.match(strip) or _DEFCLS.match(strip) or _IMPORT.match(strip)
                    or _DECOR.match(strip) or _HEADER.match(strip)
                    or strip.startswith('"""') or strip.startswith("'''")):
                keep = True
        else:
            if _DEFCLS.match(strip) or _DECOR.match(strip):
                keep = True
        if not keep:
            continue
        out.append(line)
        for q in ('"""', "'''"):
            if strip.startswith(q) and not (len(strip) > 3 and strip.endswith(q)):
                in_tripus, triq = True, q
                break
        if not in_tripus:
            depth += _bracket_delta(line)
    return "\n".join(out).strip()
