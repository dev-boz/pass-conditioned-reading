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


def balanced_tile(turns: list[dict], n: int) -> list[tuple[int, int]]:
    """Partition turn indices into EXACTLY n contiguous tiles of near-equal token mass.

    Unlike `_greedy_tile` (pack-to-a-byte-budget), this splits on proportional boundaries, so a
    level that asks for 2 tiles gets 2 — which is what the 1-2-4-8 pyramid requires. Turn-granular,
    so tiles snap to turn boundaries and masses are only approximately equal."""
    n = max(1, min(n, len(turns)))
    total = sum(t["tokens"] for t in turns)
    tiles: list[tuple[int, int]] = []
    lo, acc = 0, 0
    for i, t in enumerate(turns):
        acc += t["tokens"]
        remaining_tiles = n - len(tiles)
        if remaining_tiles <= 1 or i >= len(turns) - 1:
            continue
        # Split when the proportional boundary is reached, OR when we are about to run out of
        # turns to give the remaining tiles one each. Without the second clause, a level whose
        # tile count approaches the turn count misses its first boundary and can never recover
        # (it emitted a single tile) — caught by verify_pyramid_schedule at V=1300.
        turns_left_after_i = len(turns) - 1 - i
        if acc >= total * (len(tiles) + 1) / n or turns_left_after_i <= remaining_tiles - 1:
            tiles.append((lo, i))
            lo = i + 1
    tiles.append((lo, len(turns) - 1))
    return tiles


def pyramid_levels(turns: list[dict], V: int, branching: int = 2) -> list[int]:
    """Tile counts per level, coarsest first: 1, 2, 4, 8, ... doubling until every tile at that
    level fits in V (i.e. the level is verbatim). Strict doubling guarantees each level is a clean
    refinement of the one above; the final level may leave one short tile, which is fine.

    Stops early if tiles would outnumber turns (turn-granular floor) — if a single turn exceeds V
    it can never be rendered verbatim, and the caller compresses it."""
    levels, n = [], 1
    while True:
        levels.append(n)
        tiles = balanced_tile(turns, n)
        widest = max(sum(t["tokens"] for t in turns[lo:hi + 1]) for lo, hi in tiles)
        if widest <= V or n >= len(turns):
            return levels
        n *= branching


def build_pyramid_schedule(turns: list[dict], V: int, branching: int = 2,
                           stage_fracs=(0.34, 0.67), compressor=None) -> list[dict]:
    """The README's coarse-to-fine TILING PYRAMID — the schedule the project actually specifies.

        pass 1        : the whole document, compressed to V
        level 2       : 2 tiles, each half the document, each compressed to V
        ...
        final level   : ceil(N/V) tiles, each <= V tokens, VERBATIM

    Every level TILES the document (complete coverage, no overlap); compression falls
    geometrically from N/V at the top to 1.0 at the bottom, because each tile always renders to
    the same budget V while covering less source. `k` therefore indexes resolution, which is what
    pass-conditioning is supposed to condition on.

    Contrast with `build_schedule` (D25), which this replaces for architecture work: that one has
    exactly TWO levels (R coarse chunks, then a verbatim sweep), so k carries no resolution
    signal beyond "which of the two sweeps am I in" — see docs/SCHEDULE-DISCREPANCY-2026-07-30.md.

    `compressor` is any object with `.compress(text, target_tokens) -> str` (defaults to the
    general extractive backend). The compressor is ARCHITECTURE, not preprocessing — which of them
    is used changes what every level can carry, so it is injected and recorded, never assumed.
    A compressor exposing `accepts_context` is additionally told its (level, n_levels).
    """
    comp = compressor if compressor is not None else ExtractiveCompressor()
    levels = pyramid_levels(turns, V, branching)
    passes: list[dict] = []
    for level, n_tiles in enumerate(levels, start=1):
        tiles = balanced_tile(turns, n_tiles)
        for (lo, hi) in tiles:
            slice_text = _render(turns, lo, hi)
            verbatim = n_tokens(slice_text) <= V
            if verbatim:
                view = slice_text
            elif getattr(comp, "accepts_context", False):
                view = comp.compress(slice_text, V, level=level, n_levels=len(levels))
            else:
                view = comp.compress(slice_text, V)
            passes.append({"phase": "A" if not verbatim else "B", "level": level,
                           "n_tiles_at_level": len(tiles),
                           "compressor": getattr(comp, "name", type(comp).__name__),
                           "turn_lo": turns[lo]["turn"], "turn_hi": turns[hi]["turn"],
                           "turn_idx": set(range(lo, hi + 1)), "slice_text": slice_text,
                           "view_text": view, "slice_tokens": n_tokens(slice_text),
                           "view_tokens": n_tokens(view)})
    K = len(passes)
    for i, p in enumerate(passes):
        p["k"], p["K"] = i + 1, K
        frac = i / max(K - 1, 1)
        p["stage"] = ("scaffold" if frac < stage_fracs[0]
                      else "concrete" if frac < stage_fracs[1] else "verbatim")
        p["compression_ratio"] = round(p["slice_tokens"] / max(p["view_tokens"], 1), 2)
    return passes


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
