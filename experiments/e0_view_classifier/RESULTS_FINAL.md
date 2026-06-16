# E0-FINAL — position-from-view classifier · non-provisional · RESULTS

**Run:** 2026-06-16 · **Config hash:** `9afffbdd9285907b` (`config_final.yaml`, run as `config.yaml`) · CPU-only · seed 42
**Compressor:** Claude Haiku 4.5 (D29), delivered via three paths (D30) — `claude -p` local **253** + `claude -p` over SSH to a second OAuth host **173** + Kiro CLI headless **1,974** = **2,400** views, `gen_path`-stamped. Views: `data/views/views_haiku_final.jsonl`.
**Supersedes** the provisional run (`RESULTS.md`, extractive stand-in, 0.433).

## Headline — the pre-registered gate

| Probe | k-acc | ±1 | **bucket (test)** | norm-pos R² |
|---|---|---|---|---|
| Tier-A logreg (hand features) | 0.331 | 0.669 | **0.672** | 0.552 |
| Tier-B linear (MiniLM, chunk-pooled) | 0.231 | 0.550 | 0.544 | 0.190 |
| **Tier-B mlp (gate probe)** | 0.192 | 0.483 | **0.561** | 0.190 |

Chance: 0.333 (uniform) / 0.375 (majority). Splits: 1,680 train / 360 val / 360 test, by `doc_id`.

> **GATE (pre-registered, verbatim):** Tier-B bucket test acc ≥ 0.90 → time-agnostic; ≤ 0.70 → signal-carrying; between → mixed. Probe selected on validation (mlp: val 0.525 > linear 0.492).
> **Tier-B/mlp bucket test acc = 0.561 ≤ 0.70 → regime = SIGNAL-CARRYING (non-provisional).**

Contamination audit: **0 / 2,400** views modified (no positional metadata leaked into view text). All 2,400 view_texts distinct (no slice/view misalignment).

## Robustness — kiro-only gate (does the generator mix drive the call?)

The 2,400 views mix three delivery paths of the same model. To confirm the mix isn't responsible for the result, the gate was re-run on the **1,974 Kiro-only** views (247 docs) alone:

| | Tier-B/mlp bucket (test) | regime | config hash |
|---|---|---|---|
| mixed (2,400) | 0.561 | signal-carrying | `9afffbdd9285907b` |
| **kiro-only (1,974)** | **0.584** | signal-carrying | `5e07ce6679f42e0a` |

Within noise of each other ⇒ the mixed dataset is **not** carrying the call through generator heterogeneity; the production run **stands on its own**. This is what discharges the provisional label (GATES rule). (The OAuth-only half — 426 views, a contiguous low-doc-id block — is underpowered for its own gate and is not over-read; the Kiro half is the well-powered single-path check.) Cross-path fidelity is separately established in `KIRO_FIDELITY.md` (Kiro `claude-haiku-4.5` ≈ first-party `claude -p` Haiku on length, compression ratio, and number recall).

## Two read-it-right caveats

1. **Not delta-comparable to the provisional 0.433.** E0-final changed *two* things vs. the provisional run: the compressor (extractive stand-in → Haiku) **and** the Tier-B instrument (added `chunk_pool: true` so the probe pools over the whole view; provisional `config_provisional.yaml` has no chunk-pool). Either change can move the score. So the 0.433→0.561 rise **must not** be attributed to "abstractive Haiku leaks more position than extraction" — the instrument changed underneath it. The only quantity comparable across the two runs is the **regime call**, which is **signal-carrying** in both.

2. **Tier-A bucket = 0.672 is the excluded channel, not a leak the gate missed.** Hand features predict position at 0.672 (kiro-only 0.699), near the 0.70 line. This is expected and pre-declared (D7): Tier-A is dominated by **view length**, which is the text-side shadow of the compression ratio = *schedule metadata*, a near-deterministic function of k. Feeding it to the classifier would make E0 circular (the label leaks through the feature, not through the view's meaning). E0's question is "is *position* recoverable from the view's **semantics**?" — so the gate is on the frozen-encoder **Tier-B** probe. Tier-A is reported transparently as the surface-channel ceiling, never gated.

## Interpretation

The regime is **signal-carrying**: a frozen semantic encoder recovers coarse pass position from production Haiku views well above chance (0.561) but far below the time-agnostic floor (0.90). Per the M2/D1 pre-registration this means **M2's explicit conditioning channel is not predicted redundant** and **D1's probes remain interpretable** — both proceed as designed. The provisional → final transition did **not** flip the call; the one substantive risk flagged in the handoff (abstractive compression flipping the regime toward mixed/time-agnostic) did not materialize as a regime change.

## Reproduce

```
python -m pca.merge_paths --out data/views/views_haiku_final.jsonl   # 2,400 from the 3 path files
# gate (config_final.yaml is staged as config.yaml):
python experiments/e0_view_classifier/run.py                          # -> metrics.json, audit.json, figures/
# kiro-only robustness:
#   build subset (gen_path==kiro) -> data/views/views_kiro_only.jsonl; point config at it; run.py
```
Artifacts archived under `results_final/` (`metrics.json`, `audit.json`, `metrics_kiro_only.json`, `figures/`).
