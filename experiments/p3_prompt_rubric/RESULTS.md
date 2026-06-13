# P3 — Prompt-rubric pilot · RESULTS

**Run:** 2026-06-13 · **Config hash:** `e0313a483d926888` · **Parser v2.1** (D22) · local Qwen2.5-7B-Instruct (llama.cpp CPU), temp 0, seed 42 · $0 spend
**Reproduce:** `make p3` (needs the P1 coupled-arm states, parser v2.1)

## Design

Three arms, identical items (P1 doc `govreport-00055`, coupled reference states
s_{k-1}, staged views v_k), K=6. Only the prompt manipulation varies:

- **(a) position_only** — structured `position: {k, K}` field, nothing else (= P2's with-position condition).
- **(b) position_rubric** — (a) + a 2–3-line per-pass behavioral rubric stating the expected behavior at that compression stage (scaffold / integrate-REPLACE / verbatim-REPLACE+REMOVE). Wording in `config.yaml`; stage boundaries D13.
- **(c) position_rubric_confidence** — (b) + a required final `confidence: 0.0–1.0` line.

Mean formulas (D24, echoed in `metrics.json`): **micro** = Σ valid / Σ candidate
lines; **macro** = mean of per-item rates. **Appropriateness** = fraction of
scored items passing D20 (early k=1,2: ADD-frac ≥ 0.5; late k=5,6: REPLACE+REMOVE
≥ 0.3; mid excluded; n=4 scored).

## Result

| arm | micro validity | macro validity | appropriateness (n=4) | confidence calibration |
|---|---|---|---|---|
| (a) position_only | 1.000 | 1.000 | 0.75 | — |
| (b) position_rubric | 1.000 | 1.000 | 1.00 | — |
| (c) position_rubric_confidence | 1.000 | 1.000 | 1.00 | r undefined (see below) |

**Validity is saturated at 1.000 across all three arms** under parser v2.1 — it
no longer discriminates anything at the prompt level. The signal is entirely in
the **op-type mix per pass**:

### Op-type fraction by pass (ADD / REPLACE; REMOVE≈0, NO_CHANGE≈0 throughout)

| pass (stage) | (a) position_only | (b) position_rubric | (c) +confidence |
|---|---|---|---|
| 1 (scaffold) | ADD .71 / REPL .29 | **ADD 1.0** | **ADD 1.0** |
| 2 (scaffold) | ADD .25 / REPL .50 | **ADD 1.0** | **ADD 1.0** |
| 3 (concrete) | ADD .20 / REPL .80 | **REPL 1.0** | **REPL 1.0** |
| 4 (concrete) | ADD .20 / REPL .80 | **REPL 1.0** | **REPL 1.0** |
| 5 (verbatim) | ADD .13 / REPL .88 | **REPL 1.0** | **REPL 1.0** |
| 6 (verbatim) | ADD .08 / REPL .83 | **REPL 1.0** | **REPL 1.0** |

**This is the finding.** The bare position field (a) does *not* produce staged
behavior: it mixes ADD and REPLACE at every pass and — tellingly — already goes
REPLACE-heavy by pass 2, i.e. it starts editing before it has finished
scaffolding. The **per-pass rubric (b) cleanly separates the stages**: pure ADD
(scaffold) at passes 1–2, pure REPLACE (integrate/verbatim) at passes 3–6 —
exactly the schedule-appropriate behavior Pass-Conditioned Training aims to
instil. That is a categorical difference in op-mix, more informative than the
appropriateness scalar (whose n=4 makes the 0.75→1.00 step itself weak; see P2
on its instability).

## Confidence arm (c)

Confidence was **emitted on only 4 of 6 passes** (k=5 and k=6 returned no
parseable `confidence:` line — the long late-pass outputs ran to the 700-token
cap before the trailing line). Values where present: k1 0.60, k2 0.60, k3 0.85,
k4 0.95 — **rising with pass index**, the face-valid direction (early
uncertainty → late confidence). **Calibration r is undefined**: validity is
constant at 1.0, so there is zero variance to correlate against. With op-mix
already identical to arm (b), **the confidence line added no measurable
behavioral signal here** and cost two missing emissions; if pursued, the
confidence line should go *first* (before ops) so the token cap can't truncate it.

## Take

At the prompt level, on one document and a 7B model: a bare position field does
not induce staged edit behavior, but a **per-pass behavioral rubric does**, and
cleanly. This is the strongest prompt-level result in the P-series and the
direct justification for **redefining E1′'s "prompt floor" arm as the rubric
version** (done in `docs/pca-outline-v0.3.md` §4 M2(b)). Caveats unchanged:
n=1 document, extractive-stand-in views, validity saturated so only op-mix
carries signal, appropriateness n=4. None of this is the trained comparison —
E1′ remains the arbiter, now with a stronger floor to beat.
