# Stage A Chain Gate — Results

**Date:** 2026-07-21.
**Status:** Battery complete and analyzed; companion checks and design probes appended below.
**Governing docs:** `docs/E2PRIME-CRITERION.md` §3 (verdict) / §5 (attribution), `docs/E2PRIME-PREREG.md` §6, and the pre-run `experiments/e2prime/STAGEA-CHAIN-GATE-ADDENDUM.md` (committed `54c59e8` before the first model draw).
**Artifacts:** `runs/stageA_chain_gate/` — per-seed JSON, per-arm manifests with content hashes, `ANALYSIS.txt`, `diagnostics.log`.

---

## Verdict

**ARCHITECTURE GATE.** Student **0/10**, floor **0/10** end-to-end on the sampled draws. The floor is inside its expected 0–1/10 band, so the §3 absolute thresholds hold and the ≤1/10 row applies.

Per E2PRIME-CRITERION §3: given P-A (clobber-safe harness), P-B (relevance fork addressed → query-conditioned framing), P-C (training health passed, run 2), and a legitimate need-class framing, training did not move the end-to-end record→retain→compose chain on this text-state edit-op instantiation. No further training spend is authorized on this instantiation. The pre-named third option is the native architecture (`docs/DISCO-NATIVE-ARCHITECTURE.md`).

This verdict was produced mechanically and survives hand review: both arms have **0 mechanical candidate successes**, so there is nothing to hand-verify upward, and a false-negative audit confirms **no draw on either arm holds a linked 23→988 pair at close** that a lenient reading could score as a hidden success.

### What the gate does and does not mean (from the criterion itself)

- It gates **this instantiation** — bounded text state + ADD/REPLACE/REMOVE ops + this schedule + this compressor family. Not the coupling claim in the abstract, not the parent proposal.
- It is a **concession test** (criterion §3 standing caveat): a concrete killable outcome, not a direct measure of the architecture's stated goal (maintaining long-session nuance). The goal-aligned follow-on is `docs/NUANCE-EXPERIMENT-SHAPE.md` (M-NL), pre-registered to run trained-vs-untrained on this exact student/floor pair on a fail-or-inconclusive Stage A.
- "Training did not move the chain" is the §3 headline; §5 attribution below refines it to the more accurate **training moved every component except the ones that carry the chain end-to-end**. The trained student beats its untrained base on op-following, recording, retention, and clean-state compose — see **Reading for the drawing board**. The gate is on the end-to-end *conjunction* at 1.5B, not a finding that training did nothing.
- The mechanical verdict is recorded as-is per the pre-registration's anti-shield rule; it is not softened. What it *licenses next* — a representation change, a scale step — is a drawing-board decision, not a re-roll of this frozen result.

---

## The battery (frozen, verdict-bearing)

Fixture v2 (seed 70707), frozen P7 v2 scaffold and schedule (K=31: 6 Phase-A + 25 Phase-B), `IntegrationState(guard="strict")`, 24-op cap, query-conditioned need class. Served locally on the GTX 1080 Ti, f16 GGUF, 24,576 ctx, full offload, one model at a time. 10 sampled draws (seeds 1–10, temp 0.7) are the verdict denominator; the seed-42 temp-0 anchor is reported separately and never pooled.

### Student — `runs/stageA_coupled_v2/stageA_v2-f16.gguf`

| seed | answer | RECORD both | RETAIN both | COMPOSE | applied/pass | state tok | validity |
|---|---|---|---|---|---|---|---|
| 1 | — (no ANSWER line) | · | · | · | 7.1 | 7579 | 0.942 |
| 2 | 86 | ✓ | ✓ | · | 8.3 | 7692 | 0.979 |
| 3 | — (no ANSWER line) | · | · | · | 3.7 | 7253 | 0.993 |
| 4 | — (no ANSWER line) | · | · | · | 7.0 | 8545 | 0.987 |
| 5 | — (no ANSWER line) | ✓ | ✓ | · | 7.0 | 7967 | 0.996 |
| 6 | 0 | · | · | · | 8.0 | 6473 | 0.952 |
| 7 | 1365 | · | · | · | 8.0 | 7373 | 0.985 |
| 8 | — (no ANSWER line) | · | · | · | 6.4 | 7432 | 0.987 |
| 9 | — (no ANSWER line) | · | · | · | 8.3 | 8305 | 0.985 |
| 10 | 98 | · | · | · | 6.2 | 8239 | 0.962 |
| **sampled** | **0/10** | **2/10** | **2/10** | **0/10** | 7.0 | 7686 | — |
| _42 (anchor)_ | _16_ | _·_ | _·_ | _·_ | _7.0_ | _7108_ | _0.888_ |

### Floor — `models/Qwen2.5-1.5B-Instruct-f16.gguf` (same base, untrained)

| seed | answer | RECORD both | applied/pass | state tok | validity |
|---|---|---|---|---|---|
| 1 | 522 | · | 0.0 | 6 | 0.750 |
| 2 | — (insufficient) | · | 3.5 | 875 | 0.804 |
| 3 | — (insufficient) | · | 2.1 | 830 | 0.985 |
| 4 | 523 | · | 0.1 | 21 | 0.148 |
| 5 | — (insufficient) | · | 1.7 | 1271 | 1.000 |
| 6 | — (insufficient) | · | 0.1 | 23 | 0.026 |
| 7 | 53 | · | 3.3 | 903 | 1.000 |
| 8 | 56 | · | 2.4 | 836 | 0.992 |
| 9 | 23 | · | 1.6 | 645 | 1.000 |
| 10 | 54 | · | 9.1 | 1841 | 1.000 |
| **sampled** | **0/10** | **0/10** | 2.4 | 725 | — |
| _42 (anchor)_ | _23_ | _·_ | _3.3_ | _1400_ | _0.996_ |

---

## §5 Component attribution

| joint | student | floor | reading |
|---|---|---|---|
| op-following (applied/pass) | **7.0** | 2.4 | training moved protocol-following ~3×; student builds a real ~7.7K-tok state, floor a thin ~0.7K-tok one |
| Tier-1 table named (any pass) | 7/10 | 2/10 | the student reads and catalogues the table far more often |
| Tier-2 mapping recorded (any pass) | 3/10 | 0/10 | but usually drops the mappings; the floor essentially never records them |
| RECORD both operands (any pass) | 2/10 | 0/10 | |
| RETAIN both at close | 2/10 | 0/10 | |
| **lost after recording** | **0/10** | **0/10** | **retention does not fail** — nothing recorded is ever lost, on either arm |
| COMPOSE (interpretable draws) | 0/2 | 0/0 | on the 2 draws that reached close holding both operands, the close still failed |
| end-to-end | 0/10 | 0/10 | |

**The chain breaks at two joints, and retention is not one of them.**

1. **RECORD — lossy summarization.** The student's dominant move on the surcharge table is to name it and report its entry count and value *range* — "24 surcharge rates (10–988 cents)", "70 entries, keys 10–98, values 161–988 cents" — while dropping every key→value mapping (Tier 1, not Tier 2). Recording is strictly all-or-nothing per table (24/24 or 0/24 across the arm; never the single relevant row), which is a property of whole-entry edit-op granularity: the task needs one row out of 24, and the instantiation can only offer all or none. Several summaries also **fabricate their statistics** (the real table is 24 entries over keys 10–98, not 70; one draw reports the control table's range as `BP 1-988`, borrowing the surcharge table's maximum).

2. **CLOSE — retrieval within the model's own state, not arithmetic.** On the two draws that reached close holding both operands, neither composed. Seed 2 held `23→988` (S26) and `1365`+`compute_line_surcharge` (S83) and answered **86** — by attending to the fixture's *decoy* control table (`CARRIER_FUEL_BP`) and confabulating a selection rule ("the closest matching bp value to 23 within the range 17–86 is 86"), never looking at the entries that held the answer. Seed 5 held both and reasoned that `compute_line_surcharge(23)` returns **23** — confusing the function's argument with its return value. These are binding/retrieval failures inside a ~7.7K-token self-generated brief, not failures of arithmetic.

**RETAIN is clean, which is a real result.** The strict guard fired hard on the student (144 quote-mismatch blocks, 93 content-redirects, 7 strict-repurpose blocks, 2 guard blocks across the arm) and **zero recorded operands were lost**. The D31 clobber mechanism that motivated the entire content-addressed harness rebuild is not what breaks the chain here — P-A did its job, and this closes off one architectural hypothesis cleanly.

### Floor interpretability

The floor is a weaker and more variable op-follower than the student (2.4 vs 7.0 applied/pass; validity bimodal, 0.026–1.000), but it is **not** a pure protocol-transfer zero: on the seven draws where it built a substantive state (645–1841 tok) it still recorded the mapping 0/10 and composed 0/10. Its confabulated answers (522, 523, 53, 56, 54) mostly come from the `CARRIER_FUEL_BP` decoy, the same table that captured the student's seed-2 close. So the floor's 0/10 is genuine incapability, not merely "can't follow ops," which makes the student comparison clean: both fail end-to-end, the student is by far the stronger op-follower and records the table more, and training still did not close the chain.

---

## Companion checks (E2PRIME-PREREG §6 — diagnostics; cannot soften the verdict)

_Filled from `runs/stageA_chain_gate/_companion/` and `_probe/` / `_closing_budget_diag/`._

### GATE-1 backfill defense
**PASS (backfill-defended)** on the student: no decode emitted 2353 from fragment-2 alone. The fixture is unguessable, so every chain failure above is genuine and any success would have been real.

### GATE-3 seeded compose (best-case state)
| frame | student | floor |
|---|---|---|
| legacy ("do not invent numbers") | **1/10** | 0/10 |
| chain (derive-permission) | **1/10** | 0/10 |

Handed a clean ~8-entry best-case state (full table + adder + function + realistic filler), the trained student composes 2353 only **1/10**, the untrained floor **0/10**. The derive-permission frame changes nothing. Reading: at 1.5B, the compose step is near the model's ceiling **even when the state is clean and legible** — so composition is a genuinely blocked joint, not only a downstream victim of bad recording. Training moved it 0→1/10; it did not clear it.

### Closing-budget diagnostic (student, 1200→4096 tokens)
Replaying every closing at 4096 tokens leaves every answer **unchanged** (seed 2 stays 86 at 247 tokens; the two `near_budget` draws never held both operands). **The battery's COMPOSE reading is not a decode-budget artifact.**

### Closing probes (student; oracle-filtered variants are forcing, design-input only)
| variant | sampled | what it isolates |
|---|---|---|
| asis (control) | 0/10 | reproduces the battery |
| **distilled** (state → only operand-bearing entries) | **1/10** | pure retrieval: can it compose once distractors are gone? |
| **modules** (state → entries naming the two modules) | **1/10** | same, coarser filter |
| retrieve (unfiltered + "quote relevant entries first") | 0/10 | can a *prompt-level* retrieval instruction fix it? |
| budget (unfiltered, 4096 tokens) | 0/10 | is it budget? |

The decisive draw is **seed 2**: in the battery it held `23→988` (S26) and `1365`+`compute_line_surcharge` (S83) among 155 entries and answered **86**, reasoning over the `CARRIER_FUEL_BP` decoy. Distill that identical state to the **2** entries that carry the operands and it composes **2353 correctly**. It held the answer and could not find it in its own 7.7K-token brief. Seed 5 (the other operand-holder) does **not** recover under distillation (98) — its failure is the argument/return confusion, a compose fault isolation cannot fix. And `retrieve` shows a *prompt* telling the model to quote relevant entries first does **not** help (0/10); only physically removing the distractors does. **The retrieval joint is real and it is structural, not promptable.**

---

## Reading for the drawing board

The mechanical verdict is a gate on **this instantiation**, and the point of the attribution above is to say *why*, precisely enough to choose the next move. Three findings matter more than the 0/10:

**1. Training moved every component — trained > untrained on all of them.** The end-to-end conjunction is the only place both arms read 0.

| signal | floor (untrained) | student (trained) |
|---|---|---|
| op-following (applied ops/pass) | 2.4 | **7.0** |
| final state built | 725 tok | **7686 tok** |
| Tier-1 table named | 2/10 | **7/10** |
| Tier-2 mapping recorded | 0/10 | **3/10** |
| both operands held at some pass | 0/10 | **2/10** |
| compose from a clean state (GATE-3) | 0/10 | **1/10** |
| end-to-end chain | 0/10 | 0/10 |

Training *matters* — the student is a categorically stronger reader/recorder than its base. The chain needs RECORD ∧ RETAIN ∧ COMPOSE to fire together in one draw; each marginal improved, and their product on a 1.5B still rounds to zero. "Improvement, not perfection" is the honest description, and the improvement is real and measured.

**2. Is a 1.5B simply incapable at this scale? — partly, and it is an open question the gate cannot close.** GATE-3 puts the compose ceiling at ~1/10 *even on a clean state*. If compose alone caps near 1/10 at 1.5B, no amount of better recording lifts the end-to-end product above the gate at this scale. Whether 3B/7B clears it is exactly the question the criterion's gray-zone retry (1.5B→3B) was built to answer — but that retry is only available at 2–4/10, and this run is 0/10, so the pre-registered rules do not license a scale retry off *this* result. The scale confound is named here, not resolved: this run cannot distinguish "the architecture is wrong" from "the model is too small," and it does not pretend to.

**3. The hard ADD/REPLACE/REMOVE constraint is the most implicated design choice, and it fails in two scale-independent ways.**
- **Whole-entry granularity → all-or-nothing recording.** The student records a table 24/24 or 0/24, never the single relevant row; where it compresses, it produces a *fabricated* Tier-1 summary. The task needs sub-entry, query-relevant recording and the op vocabulary cannot express it. A 3B would face the same granularity.
- **Flat-text state → un-addressable retrieval.** Seed 2 proves the operands can be present and unfindable, that the failure survives a prompt-level retrieve instruction, and that it dissolves the moment the state is given addressable structure (distillation). This is an argument about the *representation*, and it is precisely the case `docs/DISCO-NATIVE-ARCHITECTURE.md` makes: a retrieval-structured latent slot bank instead of a growing flat brief, with pass-conditioning by AdaLN rather than edit tokens.

**4. The instrument is a process, not an oracle.** The scorer was corrected four times mid-run — once for a paraphrase false-negative that *would have manufactured this exact verdict* from a bug. That is a standing caveat on any single number here: the measurement is delicate, and "we may not be asking the right question" is a live possibility, not a rhetorical hedge. The chain gate is a declared **concession test** — a concrete killable outcome, not the architecture's stated goal — and the pre-registered goal-aligned follow-on (`docs/NUANCE-EXPERIMENT-SHAPE.md`, M-NL) exists precisely because the right question may be a different one. This student/floor pair is the comparison M-NL needs.

**Net for the next session.** This is not "the coupling idea is falsified." It is: *this instantiation — flat text state + hard add/edit/delete + 1.5B — is gated, with a mechanistic account that points at two concrete, separable changes:* a state representation with addressable, sub-entry structure (native architecture), and a scale step to test the compose ceiling. Both are testable; neither is licensed as a retry off this frozen result, and both belong to the drawing-board decision, not to a re-roll of this gate.

---

## Instrument corrections made during the run (full disclosure)

The analysis instrument was corrected four times while the battery ran; each correction and its reasoning is a separate commit on `e2prime-prep`. The frozen battery data was never re-run — every correction is a re-scoring of archived state text, and the runner's own stored flags are observational (they feed no prompt and no state).

1. **Paraphrase false negative (would have faked the verdict).** The runner matches the queried mapping as `23: 988` (colon). The student paraphrases it as `23→988` (U+2192), so its recordings scored as non-recordings — the exact-match trap `pca/planted.py` warns about. Uncorrected this inflated the architecture-gate signal from a measurement bug. The analysis recomputes every flag from archived text with a paraphrase-robust, digit-boundary-safe matcher. Effect: student RECORD-mapping 0→3/10; seed 2 revealed as compose-blocked, not record-blocked.
2. **Truncation cause over-asserted.** An earlier classifier claimed decode-cap truncation from a reply's ending shape; it misfired in both directions ("weight>0." reads as finished, "...is 23." reads as truncated). Replaced with an evidence-only report (length vs budget) and deferred the cause to the budget diagnostic, which has the server's own `completion_tokens`.
3. **Tier-1 vs not-recording conflated.** Range-summary draws (988 as an endpoint) were pooled with genuine non-recording; they are now measured separately as the Tier-1/Tier-2 distinction the relevance taxonomy names.
4. **Op-following unreported.** Added per-arm op-following so a zero stays interpretable (P7 reading rule: a weak op-follower's zero is protocol transfer, not architecture evidence).

The runner keeps its colon-only matcher for this battery on purpose — editing it mid-run would desync the floor manifest hash from the student's. The paraphrase-robust matcher and `usage.completion_tokens` capture are queued for any future run (task).

---

## Stale DRAFT headers — additive status note

`docs/E2PRIME-PREREG.md` and `docs/E2PRIME-CRITERION.md` still carry `DRAFT for maintainer sign-off` wording describing a pre-training state. Per the handoff and the addendum, the historical wording is stale but binding by its own amendment rule, and it should be recorded additively rather than rewritten as if the draft-time statements were made post-training. This results document, the committed addendum, and the maintainer sign-off recorded therein are that additive dated record. The original documents are not edited.
