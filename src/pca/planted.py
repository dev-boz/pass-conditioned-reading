"""P4 — planted-facts recall: turn-aware coverage schedule + mechanical scoring.

Source is the 390-turn Sandpiper conversation (turn-indexed), not a flat doc, so
the coverage-timing diagnostic is a clean turn-range intersection against the
ground-truth manifest. Distinct from E0/P1's token-offset schedule (and
deliberately NOT using E0's anti-leakage hash placement D5 — here the coverage
mechanism is the object of study). See DECISIONS.md D25–D27.

Two matchers, two jobs (advisor catch — exact-substring on the paraphrasing
state would repeat the parser exact-match trap):
- coverage-timing (fact ∩ a pass's *source* slice): exact strings are valid,
  the source is verbatim.
- final-state recall: NORMALIZED, component-level match (the integration model
  paraphrases: "his grandmother", "8000" vs "8,000 units", "299" vs "$299").
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .compressor import ExtractiveCompressor
from .textutils import n_tokens


# ----------------------------------------------------------------- loading
def load_turns(path: str | Path) -> list[dict]:
    turns = []
    for line in Path(path).open(encoding="utf-8"):
        t = json.loads(line)
        t["text"] = f"{t['role']}: {t['content']}"
        t["tokens"] = n_tokens(t["text"])
        turns.append(t)
    return turns


def load_manifest(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ----------------------------------------------------------------- normalization
def normalize(s: str) -> str:
    """Lowercase; unify apostrophes (drop them); strip $; remove digit-group commas;
    hyphens→space; collapse whitespace. So '8,000-unit'→'8000 unit', '$299'→'299',
    "Founders' Edition"→'founders edition', '14-week'→'14 week', '31 years'⊃'31 year'."""
    s = s.lower().replace("’", "'").replace("‘", "'").replace("'", "")
    s = s.replace("$", "")
    s = re.sub(r"(?<=\d),(?=\d)", "", s)        # 8,000 -> 8000
    s = s.replace("-", " ")
    s = re.sub(r"\s+", " ", s)
    return s


# ----------------------------------------------------------------- schedule
def _greedy_tile(turns: list[dict], budget: int) -> list[tuple[int, int]]:
    """Partition turn indices into contiguous tiles each <= budget tokens
    (a single oversized turn becomes its own tile). Returns [(lo,hi inclusive)]."""
    tiles, lo, cur = [], 0, 0
    for i, t in enumerate(turns):
        if cur + t["tokens"] > budget and i > lo:
            tiles.append((lo, i - 1))
            lo, cur = i, 0
        cur += t["tokens"]
    tiles.append((lo, len(turns) - 1))
    return tiles


def _render(turns: list[dict], lo: int, hi: int) -> str:
    return "\n".join(t["text"] for t in turns[lo : hi + 1])


def build_schedule(turns: list[dict], V: int, R: int, stage_fracs=(0.34, 0.67)) -> list[dict]:
    """Two-phase coverage-complete coupled schedule (DECISIONS D25):
      Phase A — global scaffold: R contiguous chunks (~N/R tokens each) each
        compressed to V. After R passes the whole conversation has been seen once,
        compressed (coarse coverage).
      Phase B — verbatim sweep: ceil(N/V) contiguous tiles, each <= V tokens, read
        verbatim (sigma=0). Guarantees every turn read at full resolution by the end
        (so the single-occurrence F7 gets a verbatim read).
    Output-demand stage ladder by pass fraction: scaffold / concrete / verbatim.
    """
    comp = ExtractiveCompressor()
    N = sum(t["tokens"] for t in turns)
    passes: list[dict] = []

    chunks = _greedy_tile(turns, max(N // R, V))      # ~R coarse chunks
    for (lo, hi) in chunks:
        slice_text = _render(turns, lo, hi)
        view = comp.compress(slice_text, V)
        passes.append({"phase": "A", "turn_lo": turns[lo]["turn"], "turn_hi": turns[hi]["turn"],
                       "turn_idx": set(range(lo, hi + 1)), "slice_text": slice_text,
                       "view_text": view, "slice_tokens": n_tokens(slice_text),
                       "view_tokens": n_tokens(view)})

    for (lo, hi) in _greedy_tile(turns, V):           # verbatim tiling
        slice_text = _render(turns, lo, hi)
        passes.append({"phase": "B", "turn_lo": turns[lo]["turn"], "turn_hi": turns[hi]["turn"],
                       "turn_idx": set(range(lo, hi + 1)), "slice_text": slice_text,
                       "view_text": slice_text, "slice_tokens": n_tokens(slice_text),
                       "view_tokens": n_tokens(slice_text)})

    K = len(passes)
    for i, p in enumerate(passes):
        p["k"] = i + 1
        p["K"] = K
        frac = i / max(K - 1, 1)
        p["stage"] = ("scaffold" if frac < stage_fracs[0]
                      else "concrete" if frac < stage_fracs[1] else "verbatim")
        p["compression_ratio"] = round(p["slice_tokens"] / max(p["view_tokens"], 1), 2)
    return passes


# ----------------------------------------------------------------- fact matching
def fact_turn_indices(manifest: dict, turns: list[dict]) -> dict[str, set[int]]:
    """0-based turn-list indices where each fact occurs (any of its strings)."""
    by_turn = {t["turn"]: i for i, t in enumerate(turns)}
    out = {}
    for f in manifest["facts"]:
        idx = set()
        for s, info in f["by_string"].items():
            for occ in info["occurrences"]:
                if occ["turn"] in by_turn:
                    idx.add(by_turn[occ["turn"]])
        out[f["id"]] = idx
    return out


def match_components(text: str, components: list[dict]) -> dict[str, bool]:
    """Each component: {name, any:[patterns]} — present if any normalized pattern
    is a substring of the normalized text."""
    nt = normalize(text)
    return {c["name"]: any(normalize(p) in nt for p in c["any"]) for c in components}


def fact_present(text: str, fact_spec: dict) -> bool:
    """Full-credit presence: all `required` components present."""
    hits = match_components(text, fact_spec["components"])
    return all(hits[name] for name in fact_spec["required"])
