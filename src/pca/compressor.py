"""Compression operator C(x, sigma) — pluggable backends.

The production pipeline (per parent README §5) is teacher-LLM summarization.
No inference path for that exists in this workspace at zero cost (Phase-0
inventory), so the default backend is a deterministic extractive compressor
and every result built on it is labelled provisional (GATES.md).

Swapping backends is a config change: `compressor: extractive` vs
`compressor: llm` in the views config.
"""

from __future__ import annotations

import math
from collections import Counter

from .textutils import STOPWORDS, _WORD_RE, n_tokens, split_sentences


class ExtractiveCompressor:
    """Deterministic salience-based extractive compression.

    Scoring: SumBasic-style content-word probability averaged over the
    sentence, idf-damped within the slice, with a mild lead prior.
    Selection: greedy by score until the token budget is met; output
    preserves original sentence order. No randomness, no metadata emitted.
    """

    name = "extractive-sumbasic-v1"

    def compress(self, text: str, target_tokens: int) -> str:
        if n_tokens(text) <= target_tokens:
            return text.strip()
        sents = split_sentences(text)
        if not sents:
            return text.strip()

        sent_words = [
            [w.lower() for w in _WORD_RE.findall(s) if w.lower() not in STOPWORDS]
            for s in sents
        ]
        tf = Counter(w for ws in sent_words for w in ws)
        df = Counter(w for ws in sent_words for w in set(ws))
        n_s = len(sents)
        total = max(sum(tf.values()), 1)

        def score(i: int) -> float:
            ws = sent_words[i]
            if not ws:
                return 0.0
            sal = sum((tf[w] / total) * math.log(1 + n_s / df[w]) for w in ws) / len(ws)
            lead = 1.0 + 0.15 * (1.0 - i / n_s)  # mild lead prior
            return sal * lead

        ranked = sorted(range(n_s), key=lambda i: (-score(i), i))
        chosen: list[int] = []
        budget = 0
        for i in ranked:
            cost = n_tokens(sents[i])
            if budget + cost > target_tokens and chosen:
                continue
            chosen.append(i)
            budget += cost
            if budget >= target_tokens * 0.95:
                break
        chosen.sort()
        return " ".join(sents[i] for i in chosen)


class LLMCompressor:
    """Teacher-LLM abstractive summarization backend (the production C).

    Not runnable in this workspace without an API key or a long CPU-generation
    budget; kept as the documented upgrade path for the non-provisional E0.
    """

    name = "llm-summarize-v0"

    def __init__(self, endpoint: str | None = None, model: str | None = None):
        self.endpoint = endpoint
        self.model = model

    def compress(self, text: str, target_tokens: int) -> str:
        raise NotImplementedError(
            "LLM compression backend requires an inference path. "
            "Estimated cost for 300 docs x 8 passes via a small hosted model: "
            "~US$8-15 (see E0 RESULTS.md). Configure endpoint/model and "
            "implement the call before use; do not run without spend approval."
        )


def get_compressor(name: str, **kwargs):
    if name == "extractive":
        return ExtractiveCompressor()
    if name == "llm":
        return LLMCompressor(**kwargs)
    raise ValueError(f"unknown compressor: {name}")
