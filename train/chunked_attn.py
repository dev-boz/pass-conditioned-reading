"""Chunked causal SDPA — O(n·block) attention memory for long-row training on Pascal.

Why this exists (D34 amendment): the 1080 Ti (sm_61) has no fused attention kernel in
torch 2.13 — flash/mem-efficient SDPA require sm_80/sm_70+ — so every dtype falls back to
the math backend, which materialises the full [h, n, n] score matrix in fp32 (~5 GB/layer
at n=10K, doubled by checkpoint recompute). That caps trainable sequence length at ~4-6K
on 11 GB regardless of model dtype. This module computes the SAME causal attention with a
flash-style online-softmax over KV blocks: peak extra memory is one [h, Bq, Bk] block of
scores, so 10K+ rows train in fp32.

Numerics: scores, running max/denominator, and the output accumulator are fp32 regardless
of input dtype; the result is cast back to the input dtype. Equivalence against the stock
math backend is asserted by train/test_chunked_attn.py (forward AND input-gradients).

Integration: registered as attention implementation "chunked_sdpa" via the transformers
AttentionInterface registry; select with attn_implementation="chunked_sdpa" at model load
(train_lora.py --attn chunked). HF applies repeat_kv before calling, so q/k/v arrive with
equal head counts. Inference-time KV-cache decode (q_len != kv_len) simply falls back to
stock SDPA — this path is for training/full-sequence forwards.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F


def _qblock(qb: torch.Tensor, k32: torch.Tensor, v32: torch.Tensor,
            qs: int, qe: int, block_k: int) -> torch.Tensor:
    """Online-softmax attention of one (already scaled) query block over KV[0:qe]. fp32 in/out."""
    B, H, bq, D = qb.shape
    m = torch.full((B, H, bq, 1), float("-inf"), device=qb.device, dtype=torch.float32)
    l = torch.zeros(B, H, bq, 1, device=qb.device, dtype=torch.float32)
    acc = torch.zeros(B, H, bq, D, device=qb.device, dtype=torch.float32)
    for ks in range(0, qe, block_k):                       # causal: KV blocks only up to qe
        ke = min(ks + block_k, qe)
        s = qb @ k32[:, :, ks:ke].transpose(-1, -2)        # [B,H,bq,bk]
        if ke > qs:                                        # block overlaps the diagonal → mask
            qi = torch.arange(qs, qe, device=qb.device).unsqueeze(-1)
            ki = torch.arange(ks, ke, device=qb.device).unsqueeze(0)
            s = s.masked_fill(ki > qi, float("-inf"))
        m_new = torch.maximum(m, s.amax(dim=-1, keepdim=True))
        # renormalise the running accumulator to the new max
        alpha = torch.exp(m - m_new)
        p = torch.exp(s - m_new)
        l = l * alpha + p.sum(dim=-1, keepdim=True)
        acc = acc * alpha + p @ v32[:, :, ks:ke]
        m = m_new
    return acc / l


def chunked_causal_sdpa(q: torch.Tensor, k: torch.Tensor, v: torch.Tensor,
                        block_q: int = 512, block_k: int = 512,
                        scale: float | None = None) -> torch.Tensor:
    """q, k, v: [B, H, N, D] (same H — repeat_kv already applied). Causal. Returns [B, H, N, D].

    Each query block is wrapped in torch.utils.checkpoint: without this, a backward pass
    (including the recompute inside HF layer-level gradient checkpointing) retains every
    KV-block's intermediates for the whole sequence — the O(n^2) memory returns as autograd
    graph. Nested non-reentrant checkpointing recomputes one q-block's inner loop at a time,
    bounding attention memory at one block's graph. Cost: one extra attention recompute."""
    B, H, N, D = q.shape
    scale = scale if scale is not None else D ** -0.5
    out_dtype = q.dtype
    q32, k32, v32 = q.float(), k.float(), v.float()

    grad_live = torch.is_grad_enabled() and (q.requires_grad or k.requires_grad or v.requires_grad)
    out = torch.zeros(B, H, N, D, device=q.device, dtype=torch.float32)
    for qs in range(0, N, block_q):
        qe = min(qs + block_q, N)
        qb = q32[:, :, qs:qe] * scale                      # [B,H,bq,D]
        if grad_live:
            blk = torch.utils.checkpoint.checkpoint(
                _qblock, qb, k32, v32, qs, qe, block_k, use_reentrant=False)
        else:
            blk = _qblock(qb, k32, v32, qs, qe, block_k)
        out[:, :, qs:qe] = blk
    return out.to(out_dtype)


def chunked_sdpa_forward(module, query, key, value, attention_mask=None,
                         dropout: float = 0.0, scaling: float | None = None,
                         **kwargs):
    """transformers AttentionInterface entry point (signature per sdpa_attention_forward)."""
    from transformers.integrations.sdpa_attention import repeat_kv, sdpa_attention_forward

    # Decode / cached path (q shorter than kv) or non-causal masks: stock SDPA is fine there —
    # the memory blowup only exists for long full-sequence training forwards.
    if query.shape[-2] != key.shape[-2] or query.shape[-2] <= 2048:
        return sdpa_attention_forward(module, query, key, value,
                                      attention_mask=attention_mask, dropout=dropout,
                                      scaling=scaling, **kwargs)
    if getattr(module, "num_key_value_groups", 1) != 1:
        key = repeat_kv(key, module.num_key_value_groups)
        value = repeat_kv(value, module.num_key_value_groups)
    attn_output = chunked_causal_sdpa(query, key, value, scale=scaling)
    return attn_output.transpose(1, 2).contiguous(), None


def register() -> str:
    """Register under 'chunked_sdpa' and return the name (idempotent)."""
    from transformers.modeling_utils import AttentionInterface
    if "chunked_sdpa" not in AttentionInterface._global_mapping:
        AttentionInterface.register("chunked_sdpa", chunked_sdpa_forward)
    return "chunked_sdpa"
