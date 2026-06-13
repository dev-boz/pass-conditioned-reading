"""Deterministic text utilities: tokenization, sentence splitting, hand features.

No randomness anywhere in this module. tiktoken cl100k_base is the single
token-counting convention for the whole repo (views, budgets, stats).
"""

from __future__ import annotations

import re
from functools import lru_cache

import tiktoken

# Minimal English stopword list (fixed, not NLTK-dependent, so the feature
# definition is frozen in-repo).
STOPWORDS = frozenset(
    """a about above after again all also am an and any are as at be because been
    before being below between both but by can did do does doing down during each
    few for from further had has have having he her here hers him his how i if in
    into is it its itself just me more most my no nor not now of off on once only
    or other our ours out over own same she should so some such than that the
    their theirs them then there these they this those through to too under until
    up very was we were what when where which while who whom why will with you
    your yours""".split()
)

_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])|\n{2,}")
_WORD_RE = re.compile(r"[A-Za-z']+")
_NUM_RE = re.compile(r"\d")
_PUNCT_RE = re.compile(r"[^\w\s]")
_CAP_RE = re.compile(r"\b[A-Z][a-z]+")


@lru_cache(maxsize=1)
def get_encoder():
    return tiktoken.get_encoding("cl100k_base")


def n_tokens(text: str) -> int:
    return len(get_encoder().encode(text, disallowed_special=()))


def encode(text: str) -> list[int]:
    return get_encoder().encode(text, disallowed_special=())


def decode(tokens: list[int]) -> str:
    return get_encoder().decode(tokens)


def split_sentences(text: str) -> list[str]:
    """Deterministic regex sentence splitter; collapses whitespace inside sentences."""
    parts = [re.sub(r"\s+", " ", p).strip() for p in _SENT_RE.split(text)]
    return [p for p in parts if p]


def hand_features(text: str) -> dict[str, float]:
    """Tier-A features. Every feature is computable from the view text alone —
    schedule metadata (true compression ratio, slice bounds) is deliberately
    excluded; see DECISIONS.md D7."""
    toks = encode(text)
    words = _WORD_RE.findall(text)
    words_l = [w.lower() for w in words]
    sents = split_sentences(text)
    n_t = max(len(toks), 1)
    n_w = max(len(words), 1)
    n_s = max(len(sents), 1)
    n_chars = max(len(text), 1)
    return {
        "len_tokens": float(len(toks)),
        "len_chars": float(len(text)),
        "type_token_ratio": len(set(words_l)) / n_w,
        "stopword_frac": sum(w in STOPWORDS for w in words_l) / n_w,
        "mean_sent_len_tokens": len(toks) / n_s,
        "n_sentences": float(n_s),
        "punct_density": len(_PUNCT_RE.findall(text)) / n_chars,
        "numeral_frac": len(_NUM_RE.findall(text)) / n_chars,
        "cap_word_frac": len(_CAP_RE.findall(text)) / n_w,
        "mean_word_len": sum(len(w) for w in words) / n_w,
    }


FEATURE_ORDER = [
    "len_tokens",
    "len_chars",
    "type_token_ratio",
    "stopword_frac",
    "mean_sent_len_tokens",
    "n_sentences",
    "punct_density",
    "numeral_frac",
    "cap_word_frac",
    "mean_word_len",
]
