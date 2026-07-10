# E2′ corpus — build record (2026-07-10)

Built by `build_corpus.py`; final corpus `data/e2prime/corpus.jsonl` (gitignored, regenerable).

| Slice | n | Source | Notes |
|---|---|---|---|
| (a) prose | 120 | Frozen E0 corpus (govreport), complete K=8 frozen-view coverage (views_haiku_final.jsonl, D29/D30 gen_path provenance) | Zero new compressor calls (prereg §4 amendment) |
| (b) synth | 90 → **88** | gen_synth_code.py, seeds 20001–20090 | Two drops, below |
| (c) real | 69 | WSL venv site-packages: transformers 5.13.0, datasets 5.0.0, accelerate 1.14.0, peft 0.19.1, trl 1.8.0 — all Apache-2.0 family, license+version per doc | Eligible files exhausted at 69 pseudo-repos (target ~90; accepted) |
| **total** | **277** | ≈11.0M tokens | |

## Leakage gate (zero-tolerance, prereg §4)

First full-corpus run surfaced a **scanner precision fix**: bare integers ("1365") matched
incidental numbers in real code — over-broad vs the prereg's "integers … as table-adjacent
tokens" wording (13 false hits, all in transformers source or unrelated synth values). Fixed
to probe integers only in table/arithmetic-adjacent shapes (`= N`, `+ N`, `: N`); identifiers,
verbatim pair strings, and 12-grams cover every copy vector. Fix committed same day, pre-data-gen.

**Dropped docs (mechanical rule: any hit → drop + log):**
- `synthcode-20041` — its random table drew the pair `39: 279`, colliding with an actual
  eval-table pair. Random generation, not copied content; dropped per the rule as committed.
- `synthcode-20016` — its random adder constant drew exactly `= 1365` (the eval adder's
  arithmetic shape). Same class; dropped per the rule.

Final scan: **CLEAN — 0 hits across 277 docs** (`leakage_scan.json`, regenerable).

## Teacher-quality gate

`python -m pca.teacher_gen --config experiments/e2prime/teacher_config.yaml --audit 20` —
stratified across govreport / synthcode / realcode; gate bars: mean v3 validity ≥ 0.95,
quote rate on destructive ops ≥ 0.9; hand-audit of trajectories before mass generation.

**Attempt #1 (2026-07-10): FAILED on validity** — mean 0.773 (bar ≥0.95); quote-rate passed
(0.986). Diagnosis (2-pass replay on the worst doc): the teacher emits REPLACE quotes as
**multiple quoted fragments** ("label" "content") and fragments **longer than the 160-char
cap** — good content-addressing rejected by the v3 grammar (the D22 parser lesson, replayed
on quotes). Fix, harness-side per the pre-reg's permitted-iteration rule: parser **v3.1**
accepts 1+ fragments of 4–400 chars (ALL must match the target; redirect requires a unique
entry matching all); grammar prompt now asks for one 5–15-word exact fragment (tolerated if
not followed). Unit suite + archived-clobber replay + P1 false-block sweep all still clean.
Audit mode now persists trajectories to `trajectories_audit/` (hand-audit needs them).

**Attempt #2 (2026-07-10): superseded mid-run.** First doc improved 0.550 → 0.852 under
v3.1, but its persisted trajectory showed the residual invalids were whole-entry quotes of
444/483 chars — over the 400-char fragment cap. Cap raised to 2000 (longer quote = stricter
verification); attempt #2 stopped after doc 1 rather than spending the remaining ~430 kiro
calls on a parser known to under-score. Attempt #3 is the scoring run.
