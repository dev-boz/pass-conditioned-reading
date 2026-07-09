# E2′ Verdict Criteria — pre-committed before data generation

**Status:** DRAFT for maintainer sign-off. Becomes binding when committed. Per CONSOLIDATED-FINDINGS §5(b) this must be on the record **before any E2′ teacher data is generated**; no teacher data has been generated as of this draft.
**Date:** 2026-07-09
**Discharges:** CONSOLIDATED-FINDINGS §5(b) (named there as "a required deliverable — as of this draft, the criterion does not exist"). Consumes §5(a) (relevance fork), §5(d) (retention open), §6.5 (relevance-control fix), §6.7 (query-conditioned framing).
**Amendment rule:** once committed, these rules are frozen. Amendments only by dated addendum committed *before* the affected run — the P5-amendment discipline. A result file that motivates changing a rule does not change the rule for that result.

---

## 0. What this document is

The consolidated findings flagged that every negative in P1–P7 resolved to "→ E2′ will address this," and that without a pre-committed criterion the trained-model step becomes an unfalsifiable shield: any E2′ failure reinterpretable as "trainable further," any refusal to record reinterpretable as either failure or judgment, after the fact. This document fixes, in advance, how E2′ results will be read. It governs two forks:

- **Fork 1 — failure vs correct behavior.** If a model (floor or student) declines to record a structure, was that a capability failure or the editorially correct choice?
- **Fork 2 — model failure vs architecture failure.** If the trained student fails the P7 chain, is that trainable-further (more data/scale) or an architecture gate (the text-state edit-op instantiation is the problem)?

It does **not** govern M1/M2 themselves — their kill criteria are pre-registered in pca-outline-v0.3 §4 and stand unchanged. This document governs verdict *attribution* on the chain gate and the recording gates.

---

## 1. Preconditions — no capability verdict is interpretable until all three hold

**P-A. Harness fixes confirmed (clobber-safe edit ops).**
1. Content-addressed / clobber-safe edit ops implemented in `src/pca/editops.py` (a REPLACE must be validated against the content it claims to update, not only a parsable id).
2. **Regression replay:** the two recorded clobber instances (warm go-signal seed-2 t0.7 and fair-shot seed-42 t0 — the `REPLACE S3: FUNCTIONS=…` id-misaddressing events) are replayed against the new harness as fixtures and are **blocked**: the table entry survives, the misaddressed op is rejected or redirected per the new semantics.
3. **No false-block regression:** all archived valid P1–P7 transcripts reparse under the new harness at ≥ their parser-v2.1 validity. The harness change must not manufacture invalidity on known-good ops (the D22 lesson, run in reverse).

If P-A fails, fix the harness. Harness iteration is unlimited (it is architecture-side, always permitted under the forcing line).

**P-B. Relevance fork addressed (relevance-control v2).**
RELEVANCE-CONTROL-V2 (its own pre-registration) must run on the untrained floor with a **passing positive control** before E2′ training data is constructed. Its branch outcome selects the consequence mapping in §4. If its positive control fails on the floor — nothing crosses Tier 1 under neutral+v2 even non-diluted — the fork is unresolvable at floor altitude; then **query-conditioned framing becomes mandatory for every E2′ recording gate** (§6.7), and Fork 1 is evaluated on the trained student per §4.3.

**P-C. Training health (separates "training failed" from "trained model failed").**
On held-out teacher trajectories (documents never seen in training): student edit-op syntactic validity ≥ **0.95**, and per-pass op-type agreement with the teacher ≥ **0.75** (macro over passes). Below either bar, the run is a **training failure**: fix data/hyperparameters/schedule and retrain. Training-failure retries are unlimited and claim nothing — no capability fork may be invoked from a run that fails P-C, in either direction.

---

## 2. The task-framing rule (forcing-line boundary, fixed here)

P5 established that vague task framing, not coupling, suppressed recall, and §6.7 makes query-conditioned pass framing a design requirement. The boundary between legitimate conditioning and forcing is fixed as:

- **Legitimate:** naming an information **need-class** — e.g. "operational questions about this codebase's pricing and order flow will follow; the state must support answering them." A need-class quantifies over many possible structures; it does not name any.
- **Forcing (forbidden):** naming the target structure, its location, its identifiers, or its values — "record the surcharge table," "preserve tables," "do not overwrite S3." Anything that could only help the planted probe is forcing.

Audit rule: every prompt used in an E2′ gate is checked against this boundary and archived with the run. The same boundary applies to the **teacher**: teacher prompts may state the need-class and the general structural objective (carry structure, integrate, surface detail); they may never reference probe content. A student distilled from a probe-prompted teacher proves nothing (§5(c) of the consolidated findings).

---

## 3. Fork 2 — the P7 chain gate on the trained student

**Setup (frozen).** The unchanged 64,671-token split-unit fixture (seed 70707, subject to the fixture-version note in RELEVANCE-CONTROL-V2 — the chain probe itself, `REGION_SURCHARGE_CENTS` → `compute_line_surcharge(23) = 988 + 1365 = 2353`, is untouched in any fixture version); frozen v2 compressor; unchanged schedule; clobber-safe harness (P-A); **query-conditioned framing per §2** (plus the neutral arm too, if and only if the §4 branch permits reading it). Student = QLoRA-trained 1.5–3B per the E2′ pre-registration. Floor = **the same base model, untrained**, run in the same battery.

**Draws.** n = **10** sampled draws (temp 0.7, seeds 1–10) per arm, plus one deterministic anchor (temp 0, seed 42) reported separately and never pooled — the P6/P7 practice.

**End-to-end success** = the close produces **2353** with clean provenance under the SESSION-4 hand-verification rules: state holds both operands (988, 1365) before close, no 2353 present in state prior to close, the close visibly combines them (arithmetic or equivalent), not a lucky guess (GATE-1 backfill established 0/4 unguessability; the backfill check re-runs on the student to re-confirm).

**Floor check.** Expected floor rate 0/10 (the 7B floor was 0/4 end-to-end; the student bases are smaller). If the floor unexpectedly scores ≥2/10, the absolute thresholds below are void and the paired rule replaces them: **demonstrated** iff student − floor ≥ 5 successes; **architecture gate** iff student − floor ≤ 1; between → gray zone rule below.

**Verdict thresholds (primary, absolute, floor = 0–1/10):**

| Student end-to-end | Verdict | Pre-committed next move |
|---|---|---|
| **≥ 5/10** | **Chain demonstrated on a trained student** (vs 0/10 floor, Fisher exact p ≈ 0.03). Not "architecture validated" — that verdict belongs to M1's factorial, which this gate merely unlocks. | Proceed to the M1/M2 arms per the E2′ pre-registration. |
| **2–4/10** | **Trainable-further (gray zone), exactly one retry.** | One pre-committed iteration, chosen and stated *before* the retry run: double the teacher data (same objective, same distribution — no probe-targeting) **or** step the student 1.5B → 3B. Re-run the gate once. **≥5/10 → demonstrated; otherwise → reclassified ARCHITECTURE GATE.** No second retry. This single-retry rule is the shield-killer: the "→ train more" move is available exactly once. |
| **≤ 1/10** | **ARCHITECTURE GATE.** The text-state edit-op instantiation is gated — given P-A (clobber fixed), P-B (fork addressed), P-C (training healthy), and a legitimate need-class framing, training did not move the chain. | No further training spend on this instantiation. The program's next move is architecture revision (state representation / edit semantics / schedule redesign — e.g. the latent-state direction) or program stop. §5's component attribution names the blocked joint; it cannot soften the gate. |

**What ≤1/10 means and does not mean.** It gates *this instantiation* (bounded text state + ADD/REPLACE/REMOVE ops + this schedule + this compressor family), not the coupling claim in the abstract and not the parent proposal. It does mean: stop buying training runs for this instantiation.

---

## 4. Fork 1 — failure vs correct behavior (recording)

Instrument: the relevance-control v2 tiers (Tier 0 ignored / Tier 1 existence-or-purpose noted / Tier 2 mappings recorded), manual-confirmed, per-seed, with the v1 rule "recorded for relevance" = ≥ Tier 1 and the ≥4/5-seed decision bar. Requires v2's two structural fixes: an in-fixture **positive control (PC)** in a well-represented category, and the relevant/arbitrary pair **matched on category-representation** (no singletons).

### 4.1 On the untrained floor (runs before training data is constructed — P-B)

| Floor outcome (v2) | Reading | Consequence for E2′ (binding) |
|---|---|---|
| PC ≥ Tier 1 in ≥4/5 seeds; relevant ≥ Tier 1 in ≥4/5; arbitrary Tier 0 in ≥4/5 | **B — the floor discriminates; the earlier omission was editorial judgment** | Unconditioned-neutral recording of arbitrary structure is **not** a training target. The E2′ objective is need-conditioned recording + binding-carry. The chain gate (§3) runs **query-conditioned only**; a neutral-brief arm is not a gate. Under a *neutral* brief, a student that records the arbitrary table counts **against** the objective (overfit-to-probe indicator), not for it. (Under a need-class framing that covers it, recording it is correct — the against-rule applies to the neutral brief only.) |
| PC ≥ Tier 1 in ≥4/5; relevant Tier 0 (or <4/5 at ≥Tier 1) **with PC passing** | **A — genuine under-recording of brief-relevant structure despite instrument sensitivity** | "Record brief-relevant structure" is a **legitimate** training target, not probe-overfitting. The chain gate may run both neutral and query-conditioned arms (both pre-registered). |
| PC fails (< 4/5 at ≥Tier 1) | **Fork unresolvable at floor altitude** (the floor summarizes above table altitude everywhere — the v1 finding, reproduced) | Query-conditioned framing becomes **mandatory** for all E2′ recording gates. Fork 1 moves to the student (§4.3). |

### 4.2 Never do this

Reporting "A confirmed" from a null-on-both-arms without a passing PC — the exact laundering v1 refused. If v2 comes back degenerate again (PC fails), the fork is *carried as open*, framing goes mandatory-query-conditioned, and that is the whole conclusion.

### 4.3 On the trained student (always runs, whatever the floor branch)

Precondition: student PC ≥ Tier 1 in ≥4/5 seeds. If the student fails PC, training degraded basic brief competence — that is a **training failure** (P-C-class): fix training, do not read the fork.

| Student outcome | Verdict |
|---|---|
| Relevant ≥ Tier 1 in ≥4/5 **and** arbitrary Tier 0 in ≥4/5 | **Discriminating.** The §6.5 vindication branch: training taught relevance, not transcription. |
| Both ≥ Tier 1 in ≥4/5 | **Indiscriminate transcription.** Not a pass. Flags objective-overfit-to-form ("record all tables"). Audit the teacher data for transcription bias; **one** remediation retry (rebalance teacher data), then the verdict is final and reported as-is. |
| Relevant Tier 0 in ≥4/5 (PC passing) | **Recording gap persists under training.** Feeds §5 component attribution as a record-joint failure; contributes to Fork 2's verdict rather than owning its own. |

---

## 5. Component attribution (diagnostic — subordinate to §3)

When §3 lands gray or gate, attribute per component on the same n=10 battery, each reported as x/10 vs floor:

- **RECORD** — both operands (or the table + adder) hosted in state at any pass.
- **RETAIN** — operands present in state at close. Retention is reported as a **rate from warm per-pass tracking** (the §5(d) requirement: retention is open, never solved; the warm arbiter, not cold proxies, is the measurement — the GATE-2 lesson).
- **COMPOSE** — 2353 produced from held operands at close; plus a re-run of the seeded-state compose ceiling (GATE 3) to confirm the closing step still isn't the bottleneck.

Pre-named failure patterns: **record-blocked** (student, like the floor, never hosts the operands); **retain-blocked** (hosted then lost — if lost *despite* clobber-safe ops, the churn is representation-level, which is architecture-side evidence); **compose-blocked** (operands held at close, sum not produced — the 21/22 cross-family fingerprint; the binding-carry training target failed specifically).

Attribution names the joint for the architecture-revision decision. It does not convert a gate into a pass.

---

## 6. Terminal outcomes enumerated (the anti-shield table)

| Outcome | Verdict | Next allowed move |
|---|---|---|
| Student ≥5/10 on chain gate | Chain demonstrated at trained level | M1/M2 arms per pre-registration |
| Gray zone, retry taken, still <5/10 | Architecture gate | Architecture revision or stop — **no further training runs on this instantiation** |
| ≤1/10 first pass | Architecture gate | Same |
| Fork 1 student = indiscriminate transcription after its one remediation | Objective failure, reported as-is | Redesign the training objective before any further gate is attempted; the chain-gate result obtained with that student stands and is not re-rolled |
| M1 interaction null at trained level | The program reduces per pca-outline-v0.3 §7 (M1 is the paper) | Report; the chain-gate result, if positive, stands as a trained-level existence result and is published as such — it does not rescue M1 |
| Floor ≥2/10 on chain (surprise) | Absolute thresholds void | Paired rule in §3 governs |

No threshold in this document may be revised after E2′ data generation begins, except by dated pre-run amendment (header rule). "It would have passed under a reasonable alternative threshold" is not a reportable result under this program's discipline.

---

## 7. What this document does not govern

- M1/M2 kill criteria — owned by pca-outline-v0.3 §4.
- Teacher-data construction details, arm definitions, budgets — owned by the E2′ pre-registration (which must conform to §2's forcing boundary and cite this document).
- The relevance-control v2 design itself — owned by RELEVANCE-CONTROL-V2 (which this document consumes via §1 P-B and §4).
- Publication decisions — nothing here is published until reviewed; this document itself is surfaced for maintainer sign-off before it binds.
