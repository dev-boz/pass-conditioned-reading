# GATES.md — pre-registered gate outcomes

## E0 — position-from-view (gate for M2's regime and D1's interpretability)

| Field | Value |
|---|---|
| Date | 2026-06-12 |
| Status | **`E0-provisional`** — run on stand-in extractive compressor, not the production teacher-LLM summarizer; see E0 RESULTS.md "Validity" for what the real run needs (~US$8–15 of LLM compression or a local GPU summarizer) |
| Gate metric | Tier-B bucket test accuracy (probe selected on validation: linear) |
| Value | **0.433** (chance 0.333 uniform / 0.375 majority) |
| Thresholds | ≥ 0.90 → time-agnostic · ≤ 0.70 → signal-carrying · between → mixed |
| **Regime call** | **signal-carrying** (provisional) |
| Consequence | M2 (E1′ conditioning-channel arms) proceeds as designed; D1 probes remain interpretable. NOT final until re-run on production views — abstractive compression could plausibly leak more position than extraction and flip this call. |
| Config hash | `417694947c29e269` (`experiments/e0_view_classifier/config.yaml`) |
| Artifacts | `experiments/e0_view_classifier/{metrics.json, RESULTS.md, audit.json, figures/}` |

## Pending gates

- **E0 (final, non-provisional):** same config with `compressor: llm` once an inference path is approved.
- **P1 → E2′:** qualitative judgment on P1 transcripts is the maintainer's, by design (brief). All three transcripts ready in `experiments/p1_micro_pilot/transcripts/` (reran 2026-06-13 under **parser v2.1**; machine-generated stats in `OBSERVATIONS.md`: micro validity coupled 1.000 / input-staged 1.000 / output-staged 0.992).
- **P2 → E1′:** reran 2026-06-13, parser v2.1 (config `d6e22cb7380df28d`): validity 0.979 with position field vs 0.983 without — **null prompt-level effect** (the earlier 0.708/0.375 gap was a parser-v1 artifact). Honest negative; raises the bar for E1′.
- **P3 → E1′:** ran 2026-06-13 (config `e0313a483d926888`): validity saturated at 1.000 across arms; the **per-pass rubric** cleanly induces staged ADD→REPLACE op-mix that the bare position field does not; confidence line added nothing measurable. Basis for redefining E1′'s prompt-floor arm as the rubric version.
- **Parser note:** all P1/P2/P3 numbers are **parser v2.1** (D22). parser-v1 and parser-v2.0 outputs archived under `*_parser-v1/` and `*_parser-v2.0/`; their numbers are obsolete.
