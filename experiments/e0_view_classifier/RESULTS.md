# E0 — Position-from-view classifier · RESULTS

**Run:** 2026-06-12 · **Config hash:** `417694947c29e269` · **Status: `E0-provisional`** (stand-in compressor — see Validity) · CPU-only, $0 spend
**Reproduce:** `make e0` (regenerates from `config.yaml` + `data/views/views.jsonl` alone; fixed seed 42)

## Question

Can pass position `(k, K)` be predicted from the view `v_k` alone? This selects M2's regime under the Zheng (time-agnostic) ↔ SCUD/LoopMoE (conditioning-needed) bracket (v0.3 §4/§6) and decides D1's interpretability before any training spend.

## Pre-registered gate (written into config.yaml before the run, verbatim from the brief)

> Tier-B bucket accuracy ≥ 90% → regime = **time-agnostic**; ≤ 70% → regime = **signal-carrying**; between → **mixed**, proceed with caution flags. Probe selected on validation accuracy.

## Data

300 GovReport documents (8.2K–24K tokens) × K=8 passes = 2 400 views, constant V=512-token budget, geometric compression ladder 23.6× → 1.0× (median). Corpus justification and full schedule parameterization: `data/views/DATA_CARD.md`, `docs/DECISIONS.md` D1–D6. Split **by document**, 70/15/15 seeded (210/45/45 docs → 1 680/360/360 views) — all views of a doc share a split.

## Result

| Model | exact-k acc | macro-F1 | acc ±1 | bucket acc | k/K R² |
|---|---|---|---|---|---|
| chance | 0.125 | — | ~0.34 | 0.333 (majority 0.375) | 0.0 |
| **Tier A** hand features + logreg | 0.283 | 0.251 | 0.558 | **0.600** | 0.171 |
| **Tier B** MiniLM + linear probe | 0.158 | 0.155 | 0.414 | **0.433** | −0.220 |
| **Tier B** MiniLM + MLP(256) | 0.183 | 0.178 | 0.431 | 0.467 | −0.220¹ |

¹ The k/K regression is Ridge on the tier's features and does not vary by probe; one value per tier.

**Gate metric: Tier-B (linear probe, selected on val 0.436 > MLP 0.419) bucket test accuracy = 0.433 ≤ 0.70.**

## → Regime call: **signal-carrying** (`E0-provisional`)

Pass position is *not* near-perfectly inferable from these views. Under the pre-registered gate, the explicit position channel is predicted to carry non-redundant information: **M2 proceeds as designed and D1's probes remain interpretable** — provisionally (below).

### Reading the numbers

- **The signal that exists is shallow and lives at the endpoints.** Tier A (surface statistics) *beats* the MiniLM embeddings. Its confusion matrix (`figures/confusion_k_tier_a_logreg.png`) shows k=1 and k=8 recognized at 53%/78% row-accuracy while passes 2–6 are near-uniformly confused. Verbatim final slices read as contiguous prose; maximally compressed pass-1 views read as fragment-dense extracts; everything between blurs.
- **Representational leakage is weak**: bucket 0.43–0.47 vs 0.375 majority-chance; negative R² for embeddings (the regressor generalizes worse than predicting the mean). A student model would extract little position from view content alone.
- Behaviorally relevant headline per the brief: **bucket accuracy 0.433**.

## Validity requirements — status

1. **Production view distribution: NOT met → provisional.** Production C is teacher-LLM summarization (parent §5); no zero-cost inference path existed for 2 400 LLM compressions (Phase-0 inventory). Views use the deterministic extractive stand-in `extractive-sumbasic-v1`. **The regime call is therefore void as a final answer and labelled `E0-provisional` in GATES.md.** Direction of risk: abstractive summaries carry compressor *style* that may vary with ratio more than extraction does, so the production run could leak **more** position and flip the call toward mixed/time-agnostic; a provisional "signal-carrying" cannot be treated as safe. **What the real run needs:** the same pipeline with `compressor: llm` (backend stub in `src/pca/compressor.py`) — 2 400 compression calls ≈ 12M input + 1.2M output tokens; ≈ **US$8–15** with a small hosted model (e.g. Haiku-class) — requires spend approval, or a local GPU box to run a 7–8B summarizer overnight.
2. **Contamination strip: met.** Generator emits source sentences only. Grep-audit over all 2 400 `view_text` fields (patterns: `pass N of K`, `k=N`, `chunk N`, `doc_id` echo, `sigma`, `compression ratio/level/schedule`): **0 hits in every category**; `run.py` re-audits and defensively strips on every load (`audit.json`: 0/2400 views modified). Note: the stored JSONL *metadata* fields (`compression_ratio` etc.) never reach the classifier — and `compression_ratio` is deliberately **excluded** from Tier-A features as schedule metadata rather than view content (DECISIONS.md D7, a deviation from the brief's feature list, which names it).
3. **Split by document: met** (seeded shuffle of doc_ids; sizes above).

### Other caveats

- D5 slice placement is hash-decorrelated from pass index — the conservative choice; a left-to-right sweeping production schedule would add a source-position shortcut and raise these numbers (DECISIONS.md D5).
- MiniLM truncates to its 256-wordpiece max; Tier B sees roughly the first 40% of each view. Tier A sees all of it (and still only reaches 0.60 bucket).
- Single corpus, single K. K-generalization unmeasured.

## Figures

`figures/confusion_k_tier_a_logreg.png` · `figures/confusion_k_tier_b_linear.png` · `figures/confusion_k_tier_b_mlp.png` (row-normalized, test set)
