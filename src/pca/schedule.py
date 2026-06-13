"""View schedule: v_k = C(slice(x, r_k), sigma_k) per parent README §4.

Concrete parameterization (all invented values logged in docs/DECISIONS.md):

- Per-view token budget V is constant across passes (window invariant
  |s_{k-1}| + |v_k| + overhead <= W, parent §4 "Bounding the integration state").
- Slice length shrinks geometrically from the whole source (pass 1) to V
  tokens (pass K): slice_len_k = N * (V/N)^((k-1)/(K-1)).
- Compression ratio sigma proxy = slice_len_k / V: maximal at pass 1,
  1.0 (verbatim) at pass K — "narrow slice = light compression; whole
  source = heavy compression" (parent §3 step 1).
- Slice placement for k >= 2 is deterministic per (doc_id, k) via a hashed
  RNG, so source position is NOT systematically correlated with pass index
  (a left-to-right sweep would hand E0 a source-position shortcut that is a
  schedule-design artifact, not a compression-level signal). See DECISIONS.md D5.
- Slices snap to sentence boundaries.
"""

from __future__ import annotations

import hashlib
import random

from .textutils import encode, n_tokens, split_sentences


def _slice_lengths(n_doc_tokens: int, K: int, V: int) -> list[int]:
    if n_doc_tokens <= V:
        return [n_doc_tokens] * K
    out = []
    for k in range(1, K + 1):
        f = (V / n_doc_tokens) ** ((k - 1) / (K - 1))
        out.append(max(V, round(n_doc_tokens * f)))
    return out


def _sentence_offsets(sents: list[str]) -> list[int]:
    """Cumulative token offsets of sentence starts."""
    offs, acc = [], 0
    for s in sents:
        offs.append(acc)
        acc += n_tokens(s) + 1
    offs.append(acc)
    return offs


def slice_at(sents: list[str], offs: list[int], start_tok: int, length_tok: int) -> str:
    """Contiguous run of whole sentences covering [start_tok, start_tok+length_tok)."""
    lo = max(i for i in range(len(sents)) if offs[i] <= start_tok)
    hi = lo
    while hi < len(sents) and offs[hi + 1] - offs[lo] < length_tok:
        hi += 1
    return " ".join(sents[lo : hi + 1])


def generate_views(doc_id: str, text: str, K: int, V: int, compressor) -> list[dict]:
    """Full view sequence for one document. Deterministic in (doc_id, text, K, V)."""
    sents = split_sentences(text)
    offs = _sentence_offsets(sents)
    N = offs[-1]
    lengths = _slice_lengths(N, K, V)
    records = []
    for k in range(1, K + 1):
        slice_len = lengths[k - 1]
        if slice_len >= N:
            start = 0
            slice_text = " ".join(sents)
        else:
            rng = random.Random(
                int.from_bytes(hashlib.sha256(f"{doc_id}|{k}".encode()).digest()[:8], "big")
            )
            start = rng.randrange(0, N - slice_len + 1)
            slice_text = slice_at(sents, offs, start, slice_len)
        slice_tokens = n_tokens(slice_text)
        view = compressor.compress(slice_text, V)
        records.append(
            {
                "doc_id": doc_id,
                "k": k,
                "K": K,
                "view_text": view,
                "view_tokens": n_tokens(view),
                "slice_tokens": slice_tokens,
                "slice_start_token": start,
                "doc_tokens": N,
                "compression_ratio": round(slice_tokens / max(n_tokens(view), 1), 3),
                "compressor": compressor.name,
            }
        )
    return records


def doc_token_count(text: str) -> int:
    return len(encode(text))
