# Gauntlet Arbitration — Stage-A audit + rebuild framing (2026-07-28)

**Inputs:** `docs/GAUNTLET-STAGEA-2026-07-26.md` (the prompt) → `docs/gauntlet-28-7-26.md` (the answers).
**Panel:** 13 review blocks, all pairwise distinct (checked; no byte-identical submissions this round).
Two harnesses carry the same model family (`gemini-3.1-pro-agy` / `-studio`) — counted separately but
read as correlated. `gpt-5.6-terra-codex` double-rendered (items 1–2, then a full second pass 3–13);
read once, from the second pass.
**Method:** the `docs/gauntlet-arbitration.md` pattern — every checkable reviewer claim verified
against repo ground truth before it moves anything. A confident claim that contradicts archived data
loses to the data.

**Standing:** the Stage-A verdict (student 0/10, floor 0/10, ARCHITECTURE GATE) is unchanged. The
2026-07-26 arbitration's attribution (RECORD/demand failure, not architecture) is unchanged and was
**re-verified mechanically this session** (§5). What changed: six corrections to our own documents
(§2), a set of adopted controls and rules (§6), and a converged next-step sequence (§7).

---

## 1. Verdict table — reviewer claims, checked

| # | claim | source | status |
|---|---|---|---|
| 1 | Fisher p≈5×10⁻⁴ for 9/10 vs 1/10 is the **one-sided** value; two-sided ≈1.1×10⁻³ | gemini-agy, cantus, gpt-5.6 | **SUSTAINED** — recomputed by hand: one-sided 5.47×10⁻⁴, two-sided 1.09×10⁻³. Same applies to the 7B's 6×10⁻⁵. Conclusions unchanged at either sidedness. |
| 2 | "A 16-model gauntlet" is wrong — it was 16 review *blocks*, 15 effective after dedup | inkling | **SUSTAINED** — `GAUNTLET-STAGEA-2026-07-26.md:39` vs the 07-26 arbitration header. |
| 3 | Finding-7 table header "relation **recorded**" contradicts its own caveat (empty-state ops are guard-blocked emissions) | gemini-studio, qwen, cantus, gpt-5.6, opus, glm | **SUSTAINED** — artifacts score the ops-stream. Relabel "relation **emitted**"; adopt proposed-vs-applied dual scoring (§6.2). gemini-studio's "artificially props up your tables" is overheated — the caveat was disclosed in the same document — but the label was wrong. |
| 4 | "A model answering 988 is reasoning correctly" overclaims — the state **underdetermines** the answer; 988 is the best-supported guess, not correct reasoning | gpt-5.6 | **SUSTAINED** — reworded (§2.4). The operative consequence (cross-model 0/2 says nothing about compose) stands. |
| 5 | "Untrained 3B clears the pre-registered 5/10 bar" borrows gate language for a probe — the ≥5/10 bar is the criterion §3 **end-to-end** verdict bar; GATE-3 has no per-joint pre-registered bar | glm, gpt-5.6 | **SUSTAINED** — `E2PRIME-PREREG.md:75`, results doc §GATE-3. Restated (§2.5). |
| 6 | `analyze_chain_gate.rescore` has **no relation flag** — the 0/28 was never mechanized in the repo | deepseek, minimax | **SUSTAINED** — and now **paid**: relation flags added to `rescore()`/`components()`, re-run over all 28 archived final states: **0/28 confirmed** (strict, partial, and fn-free-addition patterns all zero), fn named 2/28 (student s2, s3) exactly as recorded (§5). |
| 7 | Findings 1↔6 are in tension: if 0/28 recorded the relation, the oracle-distilled 2353 means the chain was "passable-by-inference," so "unpassable as scored" is overstated | cantus, minimax | **SUSTAINED as wording, resolved** (§2.6). `distill()` is an oracle keep-operand-lines filter (`probe_closing.py:84`, honestly labelled); the distilled state held both operands + the bare fn name, never the formula. The 07-26 arbitration §2 item 8's phrase "did contain the formula" is **corrected** to "contained both operands and the bare function name." Finding 1 is restated: unpassable **by reading**; passable only via an inference the state never licensed, which fired once (n=1) in a 2-entry state and never at full length. |
| 8 | The crowding sweep's 50/100/155 cells are under-sampled (no denominators stated) | glm | **REFUTED by artifacts** — `_probe_crowding/crowding.json`: n=10 at every level, schema control n=10 both cells. The *gauntlet doc* omitted the denominators (fair reading); the data is fine. Denominators now inline in all tables (§6.4). |
| 9 | 7B untrained chain end-to-end "0/4" | glm (Q9) | **REFUTED** — the 7B chain run is an n=1 Q4 smoke with a declared quantization caveat (07-26 arbitration §6). No 0/4 exists. |
| 10 | "GATE 3: 4/4" cited as current | inkling (Q9) | **REVIEWER ERROR** — that is the retracted P7 pooled number (anchor + 3 draws); repaired to the scale ladder at n=11. Reviewers citing retracted numbers is a live aggregation hazard. |
| 11 | GATE-3's seed may "demonstrate relation-recording," making 3B's 9/10 imitation | sonnet-kiro (Q8b) | **ANSWERED BY DESIGN** — `compose_gate.best_case_state` documented: 8 entries; S3 full table, S6 adder + relation stated outright, six name-list fillers. GATE-3 measures compose-given-all-three-facts amid realistic noise; the seed is a static state, not an op demonstration. The relation being present is the point. |
| 12 | 61.4+34.3+4.3 = 100.0 — check rounding | kimi | **VERIFIED EXACT** — 343/192/24 of 559. |
| 13 | "28 states from 10 draws per arm" arithmetic unexplained | cantus | **RESOLVED** — 11 (student: 10 sampled + temp-0 anchor) + 11 (floor) + 6 (3B: 5 + anchor). |
| 14 | "69% of the model's input" needs its denominator; 7,692 is 31% of the 24,576 context | gpt-5.6 | **NUMBER VERIFIED, WORDING FIXED** — seed 2 pass 26: state 7,558 tok of a 10,920-tok prompt (state + view 2,981 + system) = **69.2% of the prompt**, ~31% of the context window. Both true; denominator now stated (§6.4). |
| 15 | 14B is in the model inventory but absent from the scale ladder | minimax | **EXPLAINED** — 7B hit 10/10; no headroom question left for 14B to answer. Recorded here so the gap isn't read as suppression. |
| 16 | `teacher_config.yaml` op_cap: 24, state_budget_tok: 4000 (prompt-rendered warn threshold); rubric strings as quoted | minimax, kimi | **VERIFIED** — yaml:24–25; `teacher_gen.py:102–108` verbatim; `need_class` constant at :123; budget prompt text at :124. Reviewer citations exact. |

Reviewer-error pattern for future gauntlets: retracted numbers re-cited (row 10), invented
denominators (row 9), and formatting-induced misreads (row 8). The prompt doc must carry
denominators inline and a "retracted numbers" box.

## 2. Corrections to our own record (all trace to §1)

1. **Sidedness.** All Fisher values reported with sidedness from now on: 3B vs trained 1.5B
   two-sided **p≈1.1×10⁻³**; 7B vs same two-sided ≈1.2×10⁻⁴. Nothing changes at α=0.05.
2. **"16-model gauntlet" → "16-review gauntlet (15 effective)."**
3. **Finding-7 label.** The crowding table's column is "relation **emitted (ops-stream)**"; the
   empty-state cell additionally carries "all ops would be guard-blocked." The 7-vs-0 contrast is
   attention-vs-recording, not recording-vs-recording — as the caveat said, now the table says it too.
4. **Underdetermination wording.** "Answering 988 from these states is the best-supported reading of
   a state that underdetermines the true value" replaces "is reasoning correctly."
5. **No gate language for probes.** "3B untrained composes 9/10 where the trained 1.5B manages 1/10"
   — full stop. The ≥5/10 criterion bar belongs to end-to-end verdicts only.
6. **07-26 arbitration §2 item 8 corrected.** The distilled 2-entry state contained both operands
   and the bare function name — **not** the formula. §4A.5's inference reading is the record.
   Headline finding 1 restated: *the chain was unpassable by reading (no state ever held the
   relation); it remained passable in principle by inferring addition — an inference that fired once
   in a 2-entry oracle state and never at full state size.* The verdict attribution (RECORD/demand)
   is unchanged; the absolute "unpassable" was too strong.

## 3. Question-by-question adjudication (dispositions, with credit)

**Q1 — first fix.** 11/13: demand/fixture first, on frozen weights, before any training. 2/13
(sonnet-kiro, glm) say representation first — but both operationalize it as a $0 hand-seeded
slot-fill probe, which is already the battery's P1b. **Converged, no real dissent: nothing is spent
on training until the repaired demand is shown to produce the behaviour on frozen weights.**

**Q2 — suppression effect.** Modal read: rubric effect first, structural last-man-standing. Adopted
discriminator: **kimi's 2×2** — {trained 1.5B, untrained 3B} × {current integrate rubric,
ADD-license rubric}, same pass-26 tile, same 25-entry state, n=10/cell — collapses both 07-26
controls into one design. Plus **gpt-5.6's length-matched inert-padding cell** (the 0-entry cell
varies prompt length, not just state presence) and **dual scoring** (proposed vs guard-applied,
cantus/gpt-5.6) so the empty-state cell stops comparing incompatible metrics. glm's caution stands:
the schema-control result already leans against a pure rubric story, so run it as a discriminator,
not a confirmation.

**Q3 — typed slots.** Unanimous "sound in principle, relocates the failure." The named failure
modes, each with an owner-condition attached to the lever: quote-matching on fill (opus — rigid
machine-parseable slot grammar, e.g. `[TBD:cents]`, or a FILL primitive with type-tag matching);
slot-selection foresight (glm's sharpest form: *deciding what slot to leave is deciding what to
record, one pass earlier*; gpt-5.6 — harness-supplied small slot vocabulary rather than free
invention); slot proliferation vs budget (qwen/mimo/cantus — slot cap, reserve ops for content);
suppression may fire on placeholder-heavy states too (deepseek/mimo — test after P1a); exposure
unfixed (kimi — slots fix addressability, not the single exposure; pairs with the fixture repair).
**Gate the lever on P1b (isolated slot-fill probe) before any training-side adoption.**

**Q4 — budget.** 13/13 enforce (gemini-studio's "no" is to *algorithmic* eviction, not to
enforcement). Split: harness-LRU (7) vs reject-and-reprompt-for-model-compaction (gemini-agy,
cantus, gpt-5.6, gemini-studio). Adopted: **probe simple first** (P1c: forced eviction at 4,000 tok
on frozen weights — if RECORD moves, size was load-bearing; minimax's stage-scaled op_cap as the $0
variant), **design honest later** (the trained instantiation gets model-driven compaction with
harness rejection — the architecture-honest version). kimi's additions adopted as instrument rules:
log eviction events; score "recorded-then-evicted" as a third outcome class; pin unresolved slots
if slots exist.

**Q5 — the training run.** 11/13 option (c): no training until the fixture is rebuilt and
re-measured. deepseek's (a) is impatience the sequence already prices in; minimax's (b) rests on
cross-family n=1 composes the project's own anomaly rule excludes, and on "the fixture is working,"
which finding 4 (single exposure at peak pressure) contradicts — discounted. **Adopted decision
rule (cantus/kimi):** repair fixture + demand → run untrained 3B → if it *passes*, the architecture
claim stands without training and the run is freed; if it *fails specifically on RECORD*, the
single A5000 run has a validated target: **3B, repaired data, RECORD-targeted** — compose is
already free at 3B; the empty cell (trained-3B: protocol ∧ compose) is the architecture question.

**Q6 — retrieval over the state at close.** Split 8 legitimate / 5 concedes-the-premise; both
halves agree on the synthesis, adopted: legitimate as a **declared companion arm only** — non-oracle
retriever (BM25 first), pre-registered top-k, compared against a **budget-matched
retrieval-over-flat-summary baseline** (kimi: else the comparison is rigged) — never a substitute
for fixing RECORD (a retriever cannot find a relation that was never written). Oracle-filtered
results remain ceilings/diagnostics, never results. **glm's warning goes on the ledger verbatim:**
if BM25-over-state is what closes the gap, the claim collapses to "pass-conditioned reading is an
expensive way to build a RAG store," and the P4 RAG-tie is waiting.

**Q7 — sporadic successes.** Adopted three-tier rule (gpt-5.6's labels, cantus's provenance test,
the maintainer's ablation rule as the middle tier): **(i) valid isolated success** — may generate
hypotheses, never upgrades a result; **(ii) replicated mechanism** — reproduces under named
ablation on fresh pre-registered draws, with artifact-visible provenance (the fact is *in* the
state via the op path, not inferred from generations); **(iii) demonstrated capability** —
pre-registered rate vs floor, exact test, n≥10. Existing rules retained: anchors never pool with
sampled draws; report the count *and* the exact p vs floor. gemini-studio's temp-0-only rule
noted, not adopted (conflicts with rate-based discipline; anchors already serve determinism).

**Q9 — honest claim.** Adopted (deepseek/glm's formulations, merged): *"On one synthetic 64.7K-token
codebase: pass-conditioned LoRA at 1.5B teaches near-perfect protocol execution (validity 0.94–1.00,
7.0 applied ops/pass, zero retention loss) whose ~7.7K-token state the model that built it cannot
use; the compose primitive is scale-limited (untrained 3B 9/10, 7B 10/10 vs trained 1.5B 1/10 on
the identical seeded state) while recording is not bought by scale (3B chain 0/5); any non-empty
state suppresses new-content emission as a step, not a slope; and the training pipeline never
demanded the three facts the scored chain required — the relation appears in 0/28 archived states.
Protocol-following and composition have never coexisted in one run."* Missing for it to matter:
**one end-to-end pass on a fair fixture, and one beat of a budget-matched external baseline**
(BooookScore's pair, RAG) — everything so far is internal to the harness (cantus/qwen).

**Q10 — rebuild vs patch.** Modal and adopted: **rebuild the fixture; regenerate the training
data; keep the harness and instrumentation** (guard, edit-op grammar, compressor, schedule, gates,
archived baselines — they are the regression suite). The 5,730 rows are not "poison" (gemini-agy)
— they are the archived control arm. Data-generation fork for Phase 3, maintainer's pick: (i) new
teacher generation under repaired rubrics; (ii) **constructed pairs** (gold states blanked to typed
slots — no teacher rollout), gated on Q11's falsifiers; (iii) **sonnet-kiro's hand-curated gold
trajectories** (~20 × augmented variants ≈ current row count) — cheap, teacher-free, coverage-poor;
viable as the few-shot seed for (i). Fixture repair requirements pooled from the panel: relation
exposed ≥3 passes at varied state pressure (split-fact never-co-occur constraint preserved — the fn
body names both operands, values still never co-occur); a **positive control** the current policy
provably records (inkling, gpt-5.6, mimo — this is the P7 relevance-fork fix); train demand = eval
demand = scoring form; closing rows inside the health gate.

**Q11 — diffusion.** Unanimous verdict, adopted: **as theory, dead** — compression is
deterministic and semantically selective; glm's kill is the crispest: *k is not a sufficient
statistic for the corruption*, so no diffusion learnability argument transfers. "Curriculum
learning with typed slots" (qwen) is the honest name. **As engineering, the constructed forward
process survives on its own merits** (path-independent supervised pairs at every level, zero
teacher spend) with a falsifier battery before any pipeline is built on it:
F1 (design-time, $0) — gpt-5.6's **ambiguity check**: does (blanked state + remaining views) ever
underdetermine the gold fill? Any nontrivial ambiguity on required slots kills deterministic
recovery. F2 ($0, frozen weights) — deepseek's **k-conditioning probe**: same tile+rubric at
k∈{5,15,26}; if placeholder-vs-exact behaviour doesn't move with k, the conditioning channel does
no timestep work. F3 (one short LoRA) — opus/glm's **constructed-pairs learnability test**:
train on (blanked, gold) pairs, measure held-out fill. F4 (post-rollout) — cantus's **separability
classifier**: real pass-k states vs constructed level-k states; near-perfect separability =
exposure bias, the constructed manifold is not the deployed manifold. cantus's exposure-bias point
is the standing risk and F4 is its measurement. **Phase-A/Phase-B separation is unanimous and
unconditional** (13/13): k/K indexes resolution only; region coverage gets its own counter; this
matches the Bayesian-filtering spine in `DISCO-NATIVE-ARCHITECTURE.md` and goes into any rebuild
regardless of the diffusion framing's fate. Non-monotone state specificity is no longer a
*prediction* to test on old runs (they are known-monotone; the process never operated) — it is a
**design requirement** on new data.

## 4. New levers surfaced, with credit

- **ADD-license recording demand** — classed a *demand repair*, not a lever (with relation-demanding
  rubric and close-format match): they make the task well-posed. (Whole panel; sharpest: deepseek,
  qwen.)
- **Typed-slot scaffold** with rigid grammar + slot cap + harness-supplied vocabulary + isolated
  fill-probe gate (opus, mimo, gpt-5.6, glm, sonnet-kiro).
- **Stage-scaled op_cap** as the $0 budget probe variant (minimax).
- **Eviction outcome class + event log** (kimi).
- **Retrieval-at-close companion arm** with budget-matched baseline (kimi's conditions, glm's
  collapse warning).
- **Constructed-pairs data generation + falsifier battery F1–F4** (maintainer's framing; falsifiers:
  gpt-5.6, deepseek, opus/glm, cantus).
- **Hand-curated gold trajectories** (sonnet-kiro).
- **Length-matched padding control** for any state-presence contrast (gpt-5.6).
- **Positive-control element in the fixture** (inkling, gpt-5.6, mimo).

## 5. Instrument work done this session

- **Relation is now a first-class joint.** `analyze_chain_gate.py`: `_relation_flags()` (line-scoped
  strict / partial / operands-linked patterns), surfaced in `rescore()` and `components()`
  (`RECORD_relation_ever`, `RETAIN_relation_at_close`, `RETAIN_ALL_THREE_at_close`, `fn_named*`).
  Validated: S83 near-miss (three names co-present, no link) does **not** match; GATE-3's seed
  sentence matches strict. Re-run over all 28 archived final states: **relation 0/28, fn named 2/28**
  — the 07-26 hand measurement reproduces mechanically.
- Crowding/schema-control denominators verified from artifacts (n=10 every cell).
- Pass-26 input composition verified from `student_s2_t0.7.json` (state 7,558 / prompt 10,920 tok).

## 6. Rulings adopted (added to standing methodology)

1. **Three-tier anomaly rule** (Q7) — isolated / replicated-mechanism / demonstrated-capability.
2. **Dual scoring in probe harnesses** — every op-level metric reports *proposed* (emitted) and
   *applied* (guard-passing) separately. No table may contrast one against the other.
3. **Probes never wear gate language.** Bars belong to pre-registered verdicts.
4. **Denominators inline, always** — every rate names its n in the same cell; every percentage of
   "input" names the denominator (prompt vs context window).
5. **P-values state sidedness.**
6. Reaffirmed: length-sensitive metrics banned from all arms; anchors never pooled; hand-read
   before believing a flag (this session: the flag was re-derived *from* the hand-read).

## 7. The sequence (converged; costs on the 1080 Ti unless noted)

- **Phase 0 — instrument debts** (hours): relation flags ✅ done; port paraphrase-robust matcher
  into the runner's live flags; archive `usage.completion_tokens` per call; dual proposed/applied
  scoring in the probe harnesses.
- **Phase 1 — $0 discrimination battery** (a weekend, frozen weights, all `gate_legal:false`):
  **P1a** kimi's 2×2 (+ padding cell, dual-scored) → names the suppression mechanism;
  **P1b** hand-seeded typed-slot fill probe (pass 26, both models) → is the slot mechanic live;
  **P1c** enforced-budget re-run (+ stage-scaled op_cap variant) → was size load-bearing;
  **P1d** k-conditioning probe (=F2) → does the timestep channel do anything.
- **Phase 2 — fixture + demand repair** (days of design, $0 compute): relation-demanding verbatim
  rubric; ADD license; `ANSWER:` in the closing demand; closing rows in the health gate;
  multi-exposure ≥3 at varied state pressure; positive control; component tracker already carries
  the relation. Then the **untrained-3B repaired-fixture battery** and the Q5 decision rule.
- **Phase 3 — the one training run** (A5000): only if Phase 2 fails on RECORD; 3B; data per the
  maintainer's fork (§3 Q10); one lever; defect repairs are not levers.
- **Parallel track, unblocked by all of the above:** M-NL (lever 12) — the panel's unanimous "what's
  missing" is external validity; BooookScore supplies the baseline pair, LoCoMo-Plus the
  length-bias hazard list.

## 8. Verification queue (not yet arbitration-verified)

- Reviewer-named prior art used only as reasoning colour this round (LLaDA 2502.09992, MDLM
  2406.07524, SEDD, D3PM, Diffusion-LM 2205.14217, SSD-LM, Plaid, Mask-Predict): no kills rest on
  them; verify only if cited in a paper draft. "DiffuLLM"/"HDLM" (minimax/mimo) are dubious names —
  do not cite.
- Carried from 07-26: MemWalker backbone size; LoCoMo-Plus licence; `traindemand` at 8192 tokens.
- minimax's request: hand-read distilled-probe transcripts to see whether 2353 cites state lines or
  priors — the inference reading (§2.6) predicts priors; settle when convenient.
