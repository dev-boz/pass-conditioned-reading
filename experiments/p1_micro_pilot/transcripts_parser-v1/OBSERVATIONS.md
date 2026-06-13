# P1 — mechanical observations (facts only; the qualitative judgment is the maintainer's)

Doc `govreport-00055` (8 456 tok) · K=6 · Qwen2.5-7B-Instruct Q4_K_M, llama.cpp CPU, temp 0, seed 42 · run 2026-06-12

## Per-pass edit-op validity (valid/candidate lines)

| pass | coupled | input_staged_only | output_staged_only |
|---|---|---|---|
| 1 | 1/16 | 12/12 | 5/5 |
| 2 | 4/4 | 8/8 | 11/18 |
| 3 | 4/4 | 4/4 | 15/20 |
| 4 | 5/5 | 1/5 | 17/23 |
| 5 | 3/3 | 1/1 | 7/8 |
| 6 | 1/2 | 7/7 | 4/5 |
| **mean rate** | **0.65** | **0.83** | **0.75** |

Coupled pass 1 failure mode: model anchored ADDs to ids its own prior ADDs
would create (`ADD S2:` against an empty state) — V1-class malformation.
Output arm passes 2–4 exceeded the 12-op budget (18–23 candidate lines;
excess dropped per D18).

## Integration-state size after each pass (tokens; budget 1 800, D16)

| pass | coupled | input_staged_only | output_staged_only |
|---|---|---|---|
| 1 | 16 | 459 | 75 |
| 2 | 37 | 583 | 150 |
| 3 | 153 | 1 144 | 112 |
| 4 | 270 | 1 572 | 194 |
| 5 | 767 | 2 073 ⚠ | 278 |
| 6 | 1 218 | 2 020 ⚠ | 278 |

input_staged_only violated the state budget at passes 5–6. output_staged_only
— full document visible every pass, staged demands — ended with a state ~4–7×
smaller than the other arms.

## Cost (tokens processed and wall-clock; CPU)

| arm | prompt tok (Σ) | wall-clock | per pass |
|---|---|---|---|
| coupled | ~5.0K | ~9.1 min | 56–193 s |
| input_staged_only | ~9.6K | ~17.3 min | 80–265 s |
| output_staged_only | ~52.4K | ~61 min | 479–692 s |

P1 is deliberately **not** compute-matched (that is E2′'s budget definition);
the 10× prefill cost of the full-resolution arm is the parent's
bounded-per-pass property shown concretely.
