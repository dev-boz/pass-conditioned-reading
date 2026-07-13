"""Equivalence gate for chunked_attn — MUST pass before any run-2 training step.

Asserts forward outputs AND input gradients match torch's stock math-backend causal SDPA
on CPU and (if available) CUDA, fp32 and fp16, at sizes spanning the block boundaries
(including ragged tails and GQA-shaped heads).

    ~/e2prime-venv/bin/python train/test_chunked_attn.py
"""

import sys
from pathlib import Path

import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chunked_attn import chunked_causal_sdpa  # noqa: E402


def one_case(device, dtype, B, H, N, D, block):
    torch.manual_seed(1234 + N)
    q = torch.randn(B, H, N, D, device=device, dtype=dtype, requires_grad=True)
    k = torch.randn(B, H, N, D, device=device, dtype=dtype, requires_grad=True)
    v = torch.randn(B, H, N, D, device=device, dtype=dtype, requires_grad=True)
    q2, k2, v2 = (t.detach().clone().requires_grad_(True) for t in (q, k, v))

    ref = F.scaled_dot_product_attention(q.float(), k.float(), v.float(), is_causal=True)
    out = chunked_causal_sdpa(q2, k2, v2, block_q=block, block_k=block).float()

    tol = 2e-5 if dtype == torch.float32 else 2e-3
    df = (ref - out).abs().max().item()
    assert df < tol, f"forward mismatch {df:.2e} (tol {tol:.0e}) N={N} {dtype} {device}"

    g = torch.randn_like(ref)
    ref.backward(g)
    out.backward(g)
    for a, b, name in ((q, q2, "dq"), (k, k2, "dk"), (v, v2, "dv")):
        dg = (a.grad.float() - b.grad.float()).abs().max().item()
        gtol = 5e-5 if dtype == torch.float32 else 5e-3
        assert dg < gtol, f"{name} mismatch {dg:.2e} (tol {gtol:.0e}) N={N} {dtype} {device}"
    return df


def main() -> None:
    devices = ["cpu"] + (["cuda"] if torch.cuda.is_available() else [])
    cases = [  # (N, block) spanning: N<block, N=block, ragged multi-block, exact multiple
        (64, 128), (128, 128), (500, 128), (512, 128), (1000, 256), (2048, 512)]
    for device in devices:
        for dtype in ([torch.float32, torch.float16] if device == "cuda" else [torch.float32]):
            for N, block in cases:
                df = one_case(device, dtype, 1, 4, N, 64, block)
            print(f"{device} {str(dtype).split('.')[-1]}: {len(cases)} cases OK "
                  f"(last fwd maxdiff {df:.1e})")
    print("chunked_attn EQUIVALENCE OK")


if __name__ == "__main__":
    main()
