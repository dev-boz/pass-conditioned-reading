# GATES.md — pre-registered gate outcomes

## E0 — position-from-view (gate for M2's regime and D1's interpretability)

### E0-FINAL (non-provisional) — 2026-06-16

| Field | Value |
|---|---|
| Date | 2026-06-16 |
| Status | **FINAL** — production compressor (Claude Haiku 4.5, D29) delivered via three paths (D30: `claude -p` local 253 + SSH/second-host 173 + Kiro CLI 1,974); provisional label dropped (justified by the kiro-only robustness gate below). |
| Gate metric | Tier-B bucket test accuracy (probe selected on validation: **mlp**, val 0.525 > linear 0.492; selection rule unchanged from provisional — same `run.py`) |
| Value | **0.561** (chance 0.333 uniform / 0.375 majority) |
| Thresholds | ≥ 0.90 → time-agnostic · ≤ 0.70 → signal-carrying · between → mixed |
| **Regime call** | **signal-carrying** (non-provisional) |
| Robustness (kiro-only) | **0.584** signal-carrying on the 1,974 single-path Kiro views (247 docs) — within noise of the mixed 0.561 ⇒ the generator mix is not driving the call; the production run **stands on its own**. `results_final/metrics_kiro_only.json`, config hash `5e07ce6679f42e0a`. |
| Surface channel (Tier-A) | Tier-A hand-feature bucket acc = **0.672** (kiro-only 0.699), near the 0.70 boundary. This is the **excluded** channel (D7): Tier-A is dominated by view length, the text-side shadow of the compression ratio = schedule metadata, not view semantics. The gate is on the **semantic** Tier-B probe by design; Tier-A is reported transparently, not gated. |
| vs provisional | Provisional was **0.433** (extractive stand-in, Tier-B **without** chunk-pool). The final 0.561 is **not delta-comparable**: E0-final changed *two* things at once — the compressor (extractive → Haiku) **and** the Tier-B instrument (added chunk-and-pool so the probe sees the whole view). Both moves can raise the score; the rise cannot be attributed to "Haiku leaks more position." Only the **regime call** (signal-carrying) is comparable across runs, and it is unchanged. |
| Config hash | `9afffbdd9285907b` (`experiments/e0_view_classifier/config_final.yaml`, run as `config.yaml`) |
| Artifacts | `experiments/e0_view_classifier/results_final/{metrics.json, audit.json, metrics_kiro_only.json, figures/}`; `RESULTS_FINAL.md`; `KIRO_FIDELITY.md` (Kiro≈`claude -p` paired check); views `data/views/views_haiku_final.jsonl` (gen_path-stamped) |
| Consequence | M2 (E1′ conditioning-channel arms) proceeds as designed; D1 probes remain interpretable. The provisional caveat is discharged. |

### E0-provisional — 2026-06-12 (superseded; kept for the record)

| Field | Value |
|---|---|
| Status | `E0-provisional` — stand-in extractive compressor, Tier-B without chunk-pool |
| Gate metric / Value | Tier-B bucket test acc (probe: linear) = **0.433** |
| Regime call | **signal-carrying** (provisional) |
| Config hash | `417694947c29e269` |
| Note | Raw `metrics.json`/figures were overwritten by the E0-final run; reproducible on demand from the preserved `experiments/e0_view_classifier/config_provisional.yaml` + `data/views/views.jsonl` (deterministic, seed 42). Numbers + diagnosis preserved in `RESULTS.md`. |

## Pending gates

- **E0 (final, non-provisional):** ✅ DONE 2026-06-16 — see the E0-FINAL table above (0.561, signal-carrying; kiro-only robustness 0.584).
- **P1 → E2′:** qualitative judgment on P1 transcripts is the maintainer's, by design (brief). All three transcripts ready in `experiments/p1_micro_pilot/transcripts/` (reran 2026-06-13 under **parser v2.1**; machine-generated stats in `OBSERVATIONS.md`: micro validity coupled 1.000 / input-staged 1.000 / output-staged 0.992).
- **P2 → E1′:** reran 2026-06-13, parser v2.1 (config `d6e22cb7380df28d`): validity 0.979 with position field vs 0.983 without — **null prompt-level effect** (the earlier 0.708/0.375 gap was a parser-v1 artifact). Honest negative; raises the bar for E1′.
- **P3 → E1′:** ran 2026-06-13 (config `e0313a483d926888`): validity saturated at 1.000 across arms; the **per-pass rubric** cleanly induces staged ADD→REPLACE op-mix that the bare position field does not; confidence line added nothing measurable. Basis for redefining E1′'s prompt-floor arm as the rubric version.
- **P4 → M1/E2′ (planted-facts recall, 80K Sandpiper):** ran 2026-06-14 (config `415fb49232e02ca3`). **Pre-registered kill condition FAILED: coupled 0.625 (5/8) ≤ dense 0.625 (5/8)** — at ~11× tokens / ~9× wall-clock the coupled schedule bought no recall advantage over a single head+tail read on this one document. Diagnosis (RESULTS.md): the **coverage mechanism worked** (every fact reached a view; the single-occurrence F7 delivered verbatim at the predicted pass 17) and the **Tier-3 co-presence succeeded** (F4 early + F8 late both in the final brief, with the causal link in prose) — the bottleneck was the **untrained 7B floor declining to integrate three task-orthogonal asides** (codename, dog-walk, grandmother), which dense missed too. Not an M1 refutation (n=1, prompt floor not trained, task↔planted-fact salience tension) but a real failure of M1's premise *as operationalized here*; carry the verdict + diagnosis into E2′. Provisional (extractive stand-in compressor).
- **Parser note:** all P1/P2/P3/P4 numbers are **parser v2.1** (D22). parser-v1 and parser-v2.0 outputs archived under `*_parser-v1/` and `*_parser-v2.0/`; their numbers are obsolete.
