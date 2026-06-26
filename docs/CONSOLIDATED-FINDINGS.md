# Consolidated Findings: Pass-Conditioned Reading / DiSCo Architecture

**Status:** Internal research record, maintainer handoff  
**Date:** 2026-06-26  
**Honest headline:** NOT unfeasible — it did not fail and showed potential. "Possibly feasible with a trained model" is the ceiling of what the evidence supports. Do not read further than that.

---

## 1. Goal, Stated Plainly

**What pass-conditioned reading / DiSCo tries to do.** A document too long to fit in a single context window is read in multiple passes. Each pass sees a compressed *view* of the document — a budget-bounded summary at a compression ratio that falls geometrically across K passes, from coarsest (earliest) to verbatim (latest). Between passes the model maintains a running *integration state*: a structured set of named entries that it updates via edit operations (ADD, REPLACE, REMOVE). The claim is that the coarse early passes serve a different function than the verbatim late passes: the early passes carry whole-document *structure* — which semantic units exist, how they relate, what is absent — while the late passes expand specific units to their verbatim detail. A sequential bounded-state reader that processes the document left-to-right in fixed windows cannot acquire structure before it has read past the section that establishes it. The coarse pass can, because it sees the entire document at low fidelity.

The explicit pass-position signal — a structured `{k, K}` field conditioning each pass — tells the model where it is in the schedule so it can calibrate what kind of content to write: scaffold at k=1, integrate at mid-k, surface verbatim detail at k=K. This is the *pass-conditioned reading* claim.

**What it is not.** This is not a recall claim. The original document stays on disk; verbatim late passes read it directly. If a query can pre-name the information need, a standard retrieval-augmented pipeline (RAG) will retrieve the relevant passage and answer precisely. The architecture is not trying to beat RAG on named-query recall. The claim is narrower: *detecting and carrying global structure that a sequential bounded-state reader cannot acquire, on queries that cannot pre-name the pattern* — split semantic units whose operands appear in non-adjacent passages, coverage-shape gaps, relational bindings that survive no single view. Recall on individually named facts is RAG turf and the program concedes it.

**Why E2-prime is the intended optimum.** No model has been trained under the Pass-Conditioned Training objective. The experiments in P1–P7 run on off-the-shelf instruction-tuned models (principally Qwen2.5-7B-Instruct) with no fine-tuning. These are an *untrained 7B floor*: a proof-of-mechanism baseline. The project's own framing is direct: "An untrained model has no signal for when to scaffold versus refine versus surface verbatim detail beyond whatever the prompt asserts; in practice it over-contributes at every position and under-integrates the detail that late-pass verbatim reads surface." The target is a QLoRA-trained student (1.5–3B) that has learned the schedule from a teacher executing it — E2-prime. The floor experiments are designed to be small enough to die quickly if the architecture is broken, and to identify the blocking joints if it is not, so that E2-prime has a specific, motivated problem to solve rather than a generic "do better" objective.

The V1 generalist prompt-only floor is: ~50% malformed edit ops at 1.5B (Qwen 2.5 1.5B; n unspecified; described as existing to be beaten, not as a pass-conditioned result).

---

## 2. The Defensible Claim at Its Narrowed Final Form

**Starting claim (pre-experiments):** whole-corpus understanding via a coarse-to-fine reading schedule.

**Narrowed claim (post-P1–P7):** detecting and carrying global structure — split semantic units, coverage-shape, presence/absence of named entities — that a sequential bounded-state reader cannot acquire, *where the query cannot pre-name the pattern*.

**What was ruled out and why:**

- **Categorical abstraction = poolable.** If the information need is a category (topics, entities, themes), a pooling reader or hierarchical summarizer handles it without a schedule. No added value from pass-conditioning.
- **Vibes / style / tone = query-primable.** These can be elicited in a single prompted pass once the query names the register. Not a discriminating use case.
- **Recall = RAG-equivalent / ties.** P4 (n=1 document, 8 planted facts) confirmed the tie: coupled 5/8 = dense head+tail 5/8. The architecture did not improve on a cheap dense truncation for individually named facts. This is not a refutation of M1 at one document (the untrained floor, task-orthogonal planted facts, and extractive compressor are all confounds), but it correctly narrows the claim away from "recall is our turf."

The surviving claim is the one the program cannot rule out: carrying the *relational binding* of a semantic unit split across non-adjacent passages — specifically, record→retain→compose on a fact whose two operands appear in distant sections and whose linking formula does not survive in any single view's compression. P7 (split-unit fixture on a 64,671-token codebase) is the cleanest operationalization of this claim. P7's end-to-end rate on the untrained 7B is 0/4.

---

## 3. What Each Experiment Found, at True Strength

### E0 — Does the pass-position signal carry non-redundant information?

**What it tested.** Whether pass position (k, K) can be predicted from view content v_k alone, to select the temporal regime for M2 (explicit conditioning adds value vs. is redundant because position is inferable from view content). Tier-B probe: MiniLM semantic embeddings. Tier-A probe: hand-crafted surface features (excluded from the gate by design; see D7 below). Gate thresholds pre-registered: ≥0.90 → time-agnostic; ≤0.70 → signal-carrying; between → mixed.

**Final result (non-provisional, 2026-06-16, config hash 9afffbdd9285907b):**  
Tier-B MLP bucket test accuracy = **0.561**, n = 360 test views (45 docs × K=8), vs. chance 0.333 uniform / 0.375 majority. Gate call: **signal-carrying** (0.561 ≤ 0.70). Kiro-only robustness: 0.584 on 1,974 views (247 docs × 8 passes), single-path Haiku generator — within noise of mixed 0.561, confirming the generator mix is not driving the call.

**Provisional result (2026-06-12, config hash 417694947c29e269, superseded):**  
Tier-B linear bucket test accuracy = **0.433**, same 360-view test set, same gate call (signal-carrying). Non-comparable to final; see confounds below.

**Negatives.**
- Tier-B MiniLM embeddings are beaten by Tier-A surface hand features (bucket acc 0.433–0.467 Tier-B vs 0.600 Tier-A provisional; 0.561 vs 0.672 final). Shallow surface statistics carry more positional signal than semantic embeddings.
- Tier-B k/K regression: R² = −0.220 (both linear and MLP, provisional run). The embedding regressor generalizes *worse* than predicting the constant mean — not merely weak, actively mis-generalized.
- Positional signal is shallow and endpoint-concentrated: k=1 recognized at 53% row-accuracy, k=8 at 78%; passes 2–6 near-uniformly confused. Mid-sequence positions are unresolvable from view content.
- MiniLM truncates to 256-wordpiece max; Tier-B saw only ~40% of each view in the provisional run and still failed to surpass the surface-feature probe.
- Tier-A hand features approach (and in kiro-only reach 0.699) the 0.70 signal-carrying boundary — excluded because they are dominated by view length, which is the text-side shadow of compression ratio = schedule metadata, not view semantics (D7).
- K-generalization is unmeasured: single K=8, single corpus (GovReport). Whether the signal-carrying regime holds at other K values or corpus types is unknown.

**Confounds.**
- The provisional-to-final delta (0.433 → 0.561) is non-comparable and cannot be attributed to "Haiku leaks more position." Two things changed simultaneously: the compressor (extractive → Haiku) and the Tier-B instrument (chunk-and-pool added so probe sees whole view, not MiniLM-truncated ~40%). Both moves can raise the score. Only the regime call is cross-run comparable.
- D5 conservative choice: slice placement is hash-decorrelated from pass index rather than left-to-right. A left-to-right production schedule would add a source-position shortcut and raise Tier-A numbers; the regime call is therefore conservative.

**Self-corrections.**
- D7 exclusion: compression_ratio was in the brief's Tier-A feature list; E0 deliberately excluded it as schedule metadata that would make the gate circular.
- Provisional-to-final non-comparability explicitly self-flagged: "the delta (provisional→final) cannot be attributed to Haiku leaks more position." The program resisted the flattering interpretation.

**Contribution.** E0 established the signal-carrying regime for K=8 on GovReport, discharging the provisional caveat for that configuration. The explicit pass-position channel carries non-redundant information; M2's conditioning arms proceed and D1's probes remain interpretable. K-generalization and corpus generalization remain open. The gate methodology — contamination strip (0/2,400 hits), Tier-A exclusion, provisional status with direction-of-risk disclosure, split-by-document, pre-registered selection rule — serves as the honesty template for all subsequent gates.

---

### P1 — Micro-Pilot: Does scheduling collapse without per-pass view compression?

**What it tested.** Three prompt-level arms on a single 7B model (Qwen2.5-7B-Instruct Q4_K_M, llama.cpp CPU, temp=0.0, seed=42), one document (govreport-00055, 8,456 tokens), K=6 passes: (1) **coupled** — staged views (V=512 tok/pass) + staged output demands; (2) **input_staged_only** — staged views, full_detail demanded every pass; (3) **output_staged_only** — full document visible every pass, staged demands. LLM judge stubbed; gate function: if coupling shows nothing at the prompt level, E2-prime training is unlikely to rescue it.

**Results (parser v2.1, D22 rerun, n=1 document, n=1 seed, n=6 passes per arm):**

| Metric | coupled | input_staged_only | output_staged_only |
|---|---|---|---|
| Edit-op validity (micro) | 1.000 | 1.000 | 0.992 |
| Final state size (tok) | 992 | 2,060 ⚠ | 354 |
| Prompt tokens | 5,912 | 9,168 | 52,365 |
| Wall-clock | 12.2 min | 15.6 min | 67.4 min |

Validity = 1.000 is a *component-in-isolation* result (edit-op syntax), not a chain-quality result. No numeric quality comparison exists anywhere in the record.

**Negatives.**
- Every finding rests on n=1: one document, one seed, one temperature, one model. No claim survives replication because replication was not attempted.
- Coupled arm pass 6 shows anchor-drift: the model responded to a verbatim view containing an OFAC $299M figure by appending OFAC boilerplate to unrelated entries S2–S8, overwriting $12 billion total-fines content built across passes 1–5. Entry S6 conflates sub-figure with aggregate.
- Coupled arm final state retains structural redundancy (S13–S15, S19–S21 survive alongside S2–S12); the restructuring demand was not acted on.
- output_staged_only collapsed: state grew from 75 tok at pass 1 to 180 tok through passes 2–5, barely to 354 tok at pass 6 — covering an 8,456-token document with approximately five scaffold-level one-liners. The full-document arm's staging collapsed entirely.
- input_staged_only overran state budget at passes 5–6 (2,100 and 2,060 tok vs 1,800 tok warning threshold); at pass 3 the model pasted the full view verbatim as a single ADD op.
- No ROUGE, BERTScore, or reference-abstract comparison was produced. The gate question (does coupling produce a better analytical brief than the control arms?) was explicitly left as a qualitative manual review and has no recorded answer.
- Cost is not compute-matched: output_staged_only consumed 52,365 prompt tokens vs 5,912 for coupled (8.9×).

**Self-corrections — the parser artifact.**  
Parser-v1 showed coupled pass 1 at 1/16 valid (0.063) and overall coupled mean at 0.65. This was a parser bug: the model named new state entries with forward-referencing IDs (e.g., `ADD S2:` against an empty state); parser-v1 could not resolve these as valid. Parser-v2.0 fixed most cases but coupled pass 6 still showed 5/14 invalid. Parser-v2.1 achieved 1.000 for coupled and 0.992 for output_staged_only. The v1 and v2.0 rates (0.65/0.83/0.75 and 0.868 respectively) must not be carried forward as evidence of model discipline differences. The parser-v2.1 rerun (D22) is the canonical copy; v1 and v2.0 subdirectories are preserved as correction history.

**Contribution.** P1 established three concrete things and one open gate. (1) An off-the-shelf 7B can produce syntactically valid edit-ops at ≈1.000 rate once the naming convention is accepted (component-in-isolation, n=1). (2) The full-document arm collapsed to a trivially small state (354 tok); per-pass view compression is necessary to prevent staging collapse, not merely a cost reduction. (3) The full-detail arm overran the state budget and accumulated verbatim chunks rather than abstractions. (4) Open gate: whether the coupled arm's staged scaffold actually constrains content in the intended way is formally unanswered. The explicit gate question — "if coupling shows nothing here at the prompt level, training (E2-prime) is unlikely to rescue it" — cannot be checked off or failed; it remains open.

---

### P2 — Prompt-Level Position Field Effect

**What it tested.** Whether a bare structured `position: {k, K}` field changes edit-op validity or position-appropriateness of generated ops, compared to no position information. 6 items × 2 conditions = 12 generations. Items built from P1 coupled-arm states. Qwen2.5-7B-Instruct, llama.cpp CPU, temp 0, seed 42.

**Result:** Null / no measurable effect.

| Condition | n | Validity (mean) | Appropriateness (n=4 scored) |
|---|---|---|---|
| With position field | 6 | 0.979 | 0.75 |
| No position info | 6 | 0.983 | 1.00 |

Validity difference: 0.004 favouring *no-position*. No CI reported. Appropriateness direction reversed between parser v2.0 (0.75 vs 0.50, favouring position) and v2.1 (0.75 vs 1.00, favouring no-position) on the same 4 items — explicitly labelled noise in the file.

**Negatives.**
- Headline result is an honest negative: the position field buys nothing measurable at the prompt level on a 7B model once parsing is fixed.
- Validity is saturated and near-identical across conditions, leaving no room to detect a position-field effect.
- Position-appropriateness at n=4 is explicitly declared noise: direction reversed between parser versions.
- No positive prompt-level position effect was demonstrated. The bar for E1-prime is raised: the trained comparison must show the field earning its place.

**Self-correction — the parser artifact overturned.**  
Parser-v1 reported 0.708 vs 0.375 validity (with vs without position field). This gap was entirely a parser-v1 artifact (same naming-convention rejection that afflicted P1). Parser-v2.1 rerun: 0.979 vs 0.983 — null. The apparent effect was false; P2's contribution is clearing it.

**Contribution.** P2 establishes that the bare prompt-level position field produces no measurable effect on a 7B model; the earlier apparent effect was a parser artifact. This clears the false positive, raises the bar for the trained comparison (E1-prime), and motivates P3.

---

### P3 — Per-Pass Behavioral Rubric

**What it tested.** Whether a per-pass behavioral rubric — specifying expected op-type at each compression stage — induces staged edit behavior (ADD-heavy scaffold passes, REPLACE-heavy late passes) in an untrained 7B. Three arms, one document (govreport-00055), K=6: (a) **position_only** — bare `{k, K}` field; (b) **position_rubric** — position + per-pass behavioral rubric; (c) **position_rubric_confidence** — (b) plus required trailing confidence line. Qwen2.5-7B-Instruct, llama.cpp CPU, temp 0, seed 42, config hash e0313a483d926888.

**Result (parser v2.1, n=1 document, n=6 passes per arm):**

| Pass | (a) ADD / REPLACE | (b)/(c) ADD / REPLACE |
|---|---|---|
| 1 | 0.71 / 0.29 | 1.00 / 0.00 |
| 2 | 0.25 / 0.50 | 1.00 / 0.00 |
| 3 | 0.20 / 0.80 | 0.00 / 1.00 |
| 4 | 0.20 / 0.80 | 0.00 / 1.00 |
| 5 | 0.13 / 0.88 | 0.00 / 1.00 |
| 6 | 0.08 / 0.83 | 0.00 / 1.00 |

Validity: micro = 1.000 / macro = 1.000 across all three arms (validity is saturated; it no longer discriminates at the prompt level). Appropriateness (n=4 scored passes): arm (a) = 0.75 (3/4); arms (b) and (c) = 1.00 (4/4) — explicitly noted as weak given documented instability at n=4. Confidence values where emitted (arm c only, 4 of 6 passes): k1=0.60, k2=0.60, k3=0.85, k4=0.95; k5 and k6 not emitted (700-token generation cap truncated the trailing line). Calibration r is undefined: validity is constant at 1.0, leaving zero variance to correlate against.

**Negatives.**
- Validity saturated: it can no longer serve as a dependent variable.
- Appropriateness at n=4 inherently weak; the 0.75-to-1.00 step is explicitly deferred to the op-type mix as the primary finding.
- Confidence arm: emitted on only 4 of 6 passes; added no measurable behavioral signal.
- n=1 document; all findings rest on a single item.
- No CIs for any metric.

**Self-correction — "v2 fixed it" overcorrection side-effect.** Parser v2.1 resolving the parser artifact caused validity saturation — the fix introduced a new ceiling. This consequence is acknowledged explicitly: the fix is what foreclosed validity as a signal.

**Contribution.** Strongest prompt-level result in the P-series. A bare position field does not induce staged edit behavior in an untrained 7B (arm (a) was REPLACE-heavy by pass 2, before scaffolding was complete). A per-pass behavioral rubric produces categorical separation (pure ADD at scaffold passes, pure REPLACE at integrate/verbatim passes). This directly justified redefining E1-prime's prompt-floor arm as the rubric version (pca-outline-v0.3 §4 M2(b)). Confidence sub-arm is inconclusive; practical fix identified: move confidence line before ops so the token cap cannot truncate it (not yet tested).

---

### P4 — Planted-Facts Recall: The Tie

**What it tested.** Coupled K=32 multi-pass schedule vs. dense single-pass head+tail read (14K of 73K) on 8 planted facts in one 80K document ("Sandpiper"). Pre-registered kill condition: coupled recall must strictly exceed dense raw recall. Qwen2.5-7B-Instruct, llama.cpp CPU, temp 0, seed 42, Parser v2.1, extractive stand-in compressor (provisional, as E0), config hash 415fb49232e02ca3, run 2026-06-14.

**Result (n=1 document, single draw, no CIs computable):**

| Arm | Recall | Tokens | Wall-clock |
|---|---|---|---|
| Coupled | 5/8 = **0.625** | 159,451 | 231.5 min |
| Dense raw | 5/8 = **0.625** | 13,883 | 24.5 min |
| Dense within-reach | 5/7 = **0.714** | — | — |

**Kill condition: FAILED. Coupled (0.625) ≤ dense raw (0.625).**

~11× token and ~9× wall-clock cost bought zero recall advantage.

**Negatives.**
- Kill condition FAILED. Reported, not buried.
- Dense within-reach 0.714 (5/7, excluding F7 which was correctly outside the dense window) makes the negative *stronger*, not softer.
- Three facts missed by BOTH arms: F1 (Sandpiper codename), F3 (morning-walk-with-dog), F7 (grandmother-typesetter). Arms did not differ in what they missed.
- End-to-end chain recall advantage: did not materialize.
- Mid-document position recall in coupled: 0.0 (early 0.67, mid 0.0, late 1.0). Single-turn-detail tier: 0.0. Common tier: 0.0.

**Confounds (critical — do not read the failure as more than it is).**
- Provisional extractive compressor, not production Haiku.
- Task/metric tension: the task asked for a "comprehensive analytical brief" which arguably should not include a launch codename, a personal anecdote, or a "where I do my best thinking" aside. F4/F5/F6/F8 (strategy-relevant) were recalled 4/4; all three misses are task-orthogonal asides. The metric is partly measuring task-salience, not coverage.
- n=1 document; no CIs computable.

**Finding (component-in-isolation — DIAGNOSIS: coverage is not the bottleneck).** Every one of the 8 facts reached a view. The three misses have state_entry_pass=null with evicted=false — available but never written into the brief. This is not a coverage or eviction failure; it is a salience/integration failure. The schedule delivered F7 (grandmother-typesetter, single-occurrence, mid) at view-presence pass 17 — exactly the pre-computed tile — yet state_entry_pass=null. The schedule did its job; the untrained 7B declined to record it.

**Finding (component-in-isolation — RETAIN).** No evictions anywhere. F4 entered state at pass 3, F8 at pass 26; f4_f8_co_present_at_final=true. Tier-3 co-presence with correct document ordering held.

**Self-correction.** The file separates the kill condition verdict (FAIL) from the mechanistic diagnosis (salience, not coverage). The within-reach adjustment (5/7) is applied transparently and makes the negative stronger rather than softening it. The file explicitly flags task-to-fact misalignment as a caveat and calls for alignment fixes before E2-prime.

**Contribution.** Establishes that the untrained 7B floor does not convert the coverage advantage into a recall advantage over a cheap dense baseline (the tie is with dense head+tail truncation, not RAG). The kill condition failing here is informative rather than devastating — the untrained floor was not expected to pass it — but it must not be minimized or relabelled as success. Raises the specific bar E2-prime must clear and mechanistically points to salience/integration as the gap.

---

### P5 — Contamination Check

**What it tested.** Whether prior-state visibility at the salience step suppresses recording of task-relevant details that are present in the current view. Proposed explanation for P4's three documented misses (F1/F3/F7). Three arms on frozen P4 upstream state: A0 baseline (state+view→edit ops), A1 blind-salience (view+task→salience list, then +state→edit ops), A2 state-visible salience (state+view+task→list, then→edit ops). A1-vs-A2 isolates state visibility at the salience step. Run 2026-06-16, Qwen2.5-7B-Instruct, temp 0, seed 42, n=3 probes, 1 document.

**Result (n=3 probes, n=1 document, single deterministic draw per arm):**

| Probe | Vague task A0/A1/A2 | Explicit ask A0/A1/A2 | Frozen state entries |
|---|---|---|---|
| F3@pass6 | F / F / T | T / T / T | 8 |
| F7@pass17 | F / F / F | T / T / T | 23 (peak) |
| F1@pass3 | — | F / T / F | 6 |

H1 (contamination: A1 records, A2 and A0 drop) observed in **0/3** qualifying probes.

**Negatives.**
- H1 was not observed in any probe under either task condition.
- F7@pass17 at peak saturation (23 prior entries): all three arms dropped the fact under the vague task (F/F/F) — the null outcome.
- F3@pass6 under vague task: the state-visible arm (A2) was the *only* one to record — the inverse of the contamination prediction.
- Under explicit ask, all three arms recovered F3 and F7 with no arm separation — zero differential signal consistent with H1.
- F7@pass17 vague task: A1's blind salience step *did* list F7, but the edit step then dropped it — an integration-stage failure, not a salience-stage success; the chain did not complete.
- "The contamination hypothesis is not supported on this evidence."

**Finding (genuine).** Explicit/query-conditioned framing recovers facts across all arms, including the baseline (A0) and at peak saturation (F7@pass17, 23 prior entries). The P4 misses were task/query-specification failures — a design lever — not prior-state corruption of the read. A1's "present" at F1@pass3 is an incidental mention buried inside a Meridian/$299 entry, not deliberate salience-driven recording; the RESULTS file classifies it as noise. "It occurs at the lowest saturation (6 entries) — the opposite of the 'more prior state → more contamination' hypothesis."

**Self-correction.** P5 revises the implicit P4 interpretation. The pre-registration listed "Integration-stage, not salience-stage" as a possible outcome; the F7 vague-task result (A1's salience step listed F7 but the edit step dropped it) matches this pre-stated alternative and is not a clean H1 confirmation.

**Actionable inference for E1-prime/E2-prime.** Condition the prompt floor on the information need (query/recall-framed passes), since vagueness — not coupling — was what suppressed recall.

---

### P6 — Salience-Shaping: Floor-Limited and Inconclusive

**What it tested.** Whether holding a coarse global scaffold of the full document causes an untrained Qwen2.5-7B to record a locally unremarkable but globally load-bearing detail that a cold local reader would skip. Arms: **coupled_full** (Phase-A coarse scaffold + Phase-B verbatim tiles) vs. **verbatim_only** (Phase-B tiles alone). Fixture: Sandpiper conversation, 390 turns / 16 segments; 2 test details (D1_timing: Feb/Mar SMT granularity; D2_68pct: 68% margin penalty) paired with 2 prominence-matched controls (C1_pkgcogs; C2_f7). 1 deterministic draw (seed 42, temp 0) + 3 sampled draws (seeds 1–3, temp 0.7; NOT pooled with deterministic). Run 2026-06-18.

**IMPORTANT NODE-LABEL CORRECTION.** The node is labelled "global synthesis" in the orchestrator. The synthesis/trace/recompose design was invalidated PRE-RUN by source inspection (Sandpiper recaps its own conclusions; no unstated-conclusion distributed-inference target survives). "Three designs died to that one root cause." What ran and was floor-limited is *salience-shaping*, not synthesis recomposition. P6 must not be recorded as a tested-and-floor-limited synthesis-recompose chain — that chain was never tested.

**Result (v2 final, n=4 draws, n=1 document, n=2 test × 2 control details):**

| Detail | verbatim det/3smp | coupled det/3smp |
|---|---|---|
| D1_timing | ✓ / 0 | ✗ / 1 |
| D2_68pct | ✗ / 0 | ✗ / 1 |
| C1_pkgcogs | ✗ / 0 | ✗ / 0 |
| C2_f7 | ✓ / 0 | ✓ / 0 |

Note: coupled's 2 test-detail recordings (D1 and D2) are *both from the same single draw* (s2, seed 2, temp 0.7). NOT independent replications.

**The pre-registered headline interaction (coupled records TEST > CONTROL; verbatim shows no such preference) was UNCOMPUTABLE.** C1_pkgcogs was never recorded in any draw; C2_f7 was recorded only in the deterministic draw by both arms — no arm-discriminating baseline. "≤1/4 per detail, most draws zero."

**Negatives.**
- Pre-registered interaction uncomputable.
- 2 of 4 draws (s1, s3) recorded zero test or control details in either arm.
- No replicable coupled-vs-verbatim difference: s42 (det) favoured verbatim (V recorded D1, C did not); s2 (samp) favoured coupled; s1 and s3 recorded nothing. Directions disagree.
- The floor records test details too sporadically to detect any salience-shaping effect even if one exists. "Not a measured no-effect (we lacked the sensitivity to detect one)."
- "The floor-sparsity is the finding."

**V1 confound (superseded, not the pre-registered "floor too weak" verdict).**  
V1 run (2026-06-16–17) was confounded by placeholder spam (coupled_full ~25× duplicate unfilled headings; verbatim_only ~10× duplicate headings) and asymmetric op-cap truncation (coupled_full D1 tile: valid=31, applied=16, dropped=15; verbatim_only: 0 drops). "Applying it would have laundered a broken run into a result." V1 is superseded and kept as record only.

**Self-corrections.**
- Design invalidation pre-run: original P6 headline (eviction-prevention of a distributed fact) was predicted-null by P4/P5 results (bottleneck was non-recording, not eviction). Retargeted to salience-shaping before any run; this preserved discrimination power.
- "v2 fixed it" is NOT overclaimed: fixing the runner (v1→v2) did not make the salience question answerable. Recording remained too sparse to compute the interaction. The floor-sparsity limit is independent of the runner pathology.
- N=1 impression overturned by replication: s42 (det) suggested "scaffold blurs specifics / anti-salience." This impression flipped in s2. "The n=1 impression was a single-draw artifact — exactly why replication was required."

**Contribution.** Characterises the ceiling of the untrained Qwen2.5-7B for salience-shaping: too sporadic to evaluate the salience question at all. "The shoehorned generic floor cannot answer the salience question; it rides on the trained student E2-prime." The F7 gate (both arms recording C2_f7 in the deterministic draw) confirms the fixed runner can record specifics; v2 non-recordings are genuine floor behaviour. Produced concrete runner fixes (prioritise REPLACE over ADD, raise op cap to 24, save raw op text per pass).

---

### P7 — Split-Unit Fixture: The Primary End-to-End Test

**What it tested.** The full record→retain→compose chain on a 100-block / 64,671-token Python codebase fixture (seed 70707). A single semantic unit — compute_line_surcharge(23) = 988 + 1365 = 2353 — is split across two mid-exclusive fragments: fragment-1 is REGION_SURCHARGE_CENTS (24-entry arbitrary RNG lookup table, block 21 ~22%) and fragment-2 is the call site that uses it without restating any value (block 74 ~75%). Arms: dense (head+tail floor), verbatim_only (Phase-B tiles only), coupled_full (Phase-A structure-preserving + Phase-B tiles). V2 compressor: probe-blind, heterogeneous, frozen-once, ~7× compression, ~900 tok/view vs v1 ~1,800 tok/view. Also tested: salience gap (neutral rubric, both compressors) and relevance control (EVENT_DISPATCH: behaviourally relevant 24-entry routing table vs DISPLAY_LABELS: cosmetically arbitrary 24-entry label table, matched on size/surface/position/regularity/token difficulty/shared keys).

**Primary result — full chain end-to-end (fair-shot run, specifics-demanding prompt, temp-0 + 3×temp-0.7, 31 passes + closing):**

**0/4 produced 2353.**

Component gate results:

| Gate | Result | What it tests |
|---|---|---|
| GATE 1 — backfill (fragment-2 only) | 0/4 (3/4 "INSUFFICIENT", 1/4 no integer) | Unit unguessable from call site alone |
| GATE 2 — cold differential recording | coupled **2/3**; verbatim_only **0/3** | Coarse pass preserves full table (cold proxy only — see warm-arbiter reversal below) |
| GATE 3 — compose ceiling | **4/4** exact answer 2353 | Chain can compose when structure seeded |

**GATE 2 cold-vs-warm reversal.** The warm go-signal run — designated the real arbiter per pre-registration — directly contradicted the cold GATE 2 result: the table was hosted in only a fraction of sampled warm draws (~1/3) and clobbered at pass 3 in every observed recording instance. Cold GATE 2 (2/3 coupled; 0/3 verbatim-only) is a proxy result under empty-state conditions and must not be read as a warm-conditions result. The operative finding is the warm arbiter.

Additional rates:

| Condition | Rate |
|---|---|
| Table recorded in Phase-A | Achievable but rare — the source's own shorthand is "~1/4" (not a computed fraction). 2 recordings were directly observed (warm go-signal seed-2; fair-shot seed-42), each clobbered at pass 3; exact denominator not pinned, since the two recordings came from different run conditions (see residual flags). |
| Table retained past pass 3 | 0/observed instances |
| Neutral+warm recording | 0/6 (0/3 v2+neutral; 0/3 v1+neutral) |
| Relevance control — EVENT_DISPATCH | Tier 0 in 5/5 seeds |
| Relevance control — DISPLAY_LABELS | Tier 0 in 5/5 seeds |

**The chain is blocked at retention. "record ✓ (achievable, ~1/4) · retain ✗ (pass-3 clobber) · compose ✓" → "end-to-end blocked at retention, not recording."**

**Negatives.**
- Full chain 0/4. The primary headline.
- Table never recorded under neutral prompt in 0/6 draws (both compressors, 3 draws each). This is the salience gap — "told to record exact values, it records low-information names and drops the high-information table."
- Table clobbered at pass 3 in every observed recording event. Retention through the multi-pass sweep: 0 successful observations.
- Battery money comparison (coupled_full vs verbatim_only on closing answer across seeds) NOT run — predicted-null on unaided floor; table recorded ~1/4 then clobbered before pass 4, answer-time presence ≈0.
- Relevance control: both EVENT_DISPATCH (relevant) and DISPLAY_LABELS (arbitrary) ignored in 5/5 seeds each. **Both-zero does not resolve the capability-failure vs correct-editorial-omission fork.** UNRESOLVED.
- GATE 2 cold contradicted by warm go-signal: cold (empty state, k=1) showed coupled 2/3; warm (accumulated state) showed sparse hosting (~1/3 sampled draws) and immediate pass-3 clobber. The cold proxy was flagged in advance as a proxy; the warm run is the real arbiter.
- V2+specifics deliberately NOT run (forcing-blocked, Line 3 — only the compressor, not the instructions, may change). V2 compressor's independent contribution to retention is unidentified, not disproven.

**Clobber mechanism (n=2 observations — warm go-signal seed2 t0.7 + fair-shot seed-42 t0).** Edit-op id-misaddressing: `REPLACE S3: FUNCTIONS=...` — the model meant to update its functions entry but addressed S3, which held the table → the table is clobbered by an unrelated functions list. This is a trainable + partly harness-fixable artifact (clobber-safe/content-addressed edit ops), not a deliberate discard. n=2 is small; replication required.

**Relevance-control confound.** Singleton-module dilution: EVENT_DISPATCH and DISPLAY_LABELS placed in unique categories while 100 filler modules cluster into ~15 well-represented categories. High-recording briefs enumerate exactly the ~15 represented categories and drop both singletons at inventory level, before table-content relevance can matter. No positive-control instrument: no brief-relevant structure was confirmed to surface at Tier 1+ under neutral+v2. A null-on-both-arms cannot distinguish "relevance has no effect" from "nothing crosses threshold here." The relevance-control fork is unresolved; it must be carried to E2-prime as open.

**Self-corrections.**
- "v2 fixed the churn" overcorrection: RESULTS.md (2026-06-19 update) described the retention failure as "a REPRESENTATION artifact (now FIXED)" by v2. COMPRESSOR-V2.md explicitly corrects this: "claiming v2 fixed the churn would over-state the run." Isolation control (v1+neutral vs v1+specifics) shows toggling the *prompt* alone flips churn on/off with v1 views held constant. The views' independent role is open.
- GATE 2 cold-vs-warm reversal: warm go-signal directly contradicted cold GATE 2 (coupled 2/3). Pre-reg already flagged GATE 2 as "a go/no-go PROXY, not the measurement"; warm per-pass tracking is "the real arbiter." RESULTS.md formalises the reversal.
- Relevance control not laundered into Reading A: "Reporting A confirmed would launder a degenerate null into a conclusion."
- Framing corrected (2026-06-19): P7 initially framed around eviction; reframed to differential recording because P4 and P6 established eviction near-absent on this floor. The warm go-signal then observed pass-3 overwrite-eviction after all — but as a trainable edit-op failure mode, not the classical predicted-null.

**Contribution.** Identified the salience/recording step as the primary demonstrated gap under neutral conditions (0/6, robust across both compressors). Under fair-shot specifics conditions, isolated the retention failure as the chain-blocking joint: edit-op id-misaddressing clobber. The relevance-control fork (capability failure → E2-prime justified vs correct editorial omission → training would be overfitting) remains UNRESOLVED and is the most important open question entering E2-prime. Delivered: clean 64,671-token code fixture, probe-blind v2 compressor frozen to scaffold_struct.json, gates (GATE 1: 0/4; GATE 2 cold proxy: 2/3 — reversed by the pre-registered warm arbiter, which showed sparse hosting and pass-3 clobber in every observed recording; GATE 3: 4/4), and the full diagnostic ready to re-pose P7 on E2-prime unchanged.

---

### P7 Cross-Family — Existence Check Across Model Families

**What it tested.** Whether the full end-to-end chain (record→retain→compose → answer=2353) fires genuinely across model families beyond Qwen-72B, and the rate and nature of recombination failure once both operands are held in state. Validity-gated, n=10 per family, blind and untrained.

**End-to-end compose rate (n=10 per family):**

| Family | RECORD | RETAIN | COMPOSE |
|---|---|---|---|
| Meta-Llama-70B | 10/10 | 10/10 | **1/10** (seed 9) |
| Mistral-24B | 5/10 | 5/10 | **1/10** (seed 42, temp 0.0) |
| gpt4omini | 9/10 | 9/10 | **0/10** |
| novalite | 9/10 | 9/10 | **0/10** |
| commandr | 0/10 | — | **0/10** |
| haiku45 | — | — | **2/10** (confounded; 0 clean Phase-A) |
| Qwen-72B ref | 4/10 | 4/10 | **2/10** (seeds 2, 3) |

**Recombination bottleneck.** Of 22 seeds across llama/gpt/nova where both operands (988 AND 1365) were confirmed held in final state, only 1 (llama seed 9) composed to 2353. **21/22 failed to sum.** Stochastic-close rate from a fixed held-state: ~0–12% (gut-check follow-up; no CI stated; single-draw-per-seed caution applies).

**Three-family existence proof.** The full clean Phase-A record→retain→compose chain fires in 3 independent families: Qwen-72B (seed 2), Meta-Llama-70B (seed 9), Mistral-24B (seed 42, temp 0.0), all hand-verified (pull 988 + 1365 → 2353, cite source; final state holds 988 and 1365 but NOT 2353 prior to close). These are each n=1 draws. Small cross-family compose-count differences are within sampling noise. (Note: these two trios are different populations. The 21/22 recombination set above is llama/gpt/nova — the strong-followers whose verbatim control fails; this existence trio is Qwen-72B/Llama-70B/Mistral-24B. They overlap only at Llama-70B seed 9 — the lone compose inside the 1/22 — so "1 of 22" and "3-family existence" are consistent, not contradictory; Qwen-72B s2 and Mistral-24B s42 lie outside the 22-seed denominator.)

**Negatives.**
- Money-comparison null: scaffold does NOT out-compose raw-tile verbatim control by count. "coupled-vs-verbatim composing 2353: llama 1v0, gpt 0v0, nova 0v0, mistral 1v1, haiku 2v7." The scaffold is not shown to add compose-rate advantage over simply reading verbatim tiles on an untrained floor.
- 21/22 both-operands-held seeds fail to sum. Dominant failure mode is RECOMBINATION, not retention.
- gpt4omini: COMPOSE 0/10 despite RECORD 9/10 and RETAIN 9/10.
- commandr: RECORD 0/10 — a different failure mode (record-failure).
- haiku45: verbatim control 7/10 >> coupled 2/10; 0 clean Phase-A composes; excluded from headline.
- Prompt-only awareness levers null (gut-check): both recorder-position and closing-permission prompt injections null — prompt-injected awareness does NOT substitute for training.
- "DO NOT assert it as a result" (re: trained model working).

**Self-corrections.**
- Mistral-24B was labelled a "footnote" (weak model) in Session 3 due to low RECORD rate. Corrected in Session 4: ops 10.4 — NOT a weak follower; footnote label retired.
- Session 3 skipped the validity gate; Session 4 ran it at full n=10 for all families.
- haiku45's coupled composes previously risked being presented as scaffold evidence; Session 4 confirmed 0 clean Phase-A composes.
- Money comparison null was not stated plainly in earlier sessions; stated plainly up front in Session 4.

**Contribution.** Moves the binary feasibility question from foreclosed to open: NOT unfeasible → possibly feasible with a trained model. The recombination bottleneck (21/22 both-operands-held seeds fail to sum; op-DSL compression strips relational binding) is the actionable thesis: a custom model must carry the binding (surcharge = table[code] + adder), not just the atomic facts. The ~0–12% stochastic-close rate quantifies the reliability gap that training must close.

---

### P7-Gutcheck — Prompt Lever Null

**What it tested.** Whether minimal, task-agnostic prompt-injected awareness (recorder-side: inject-pos; closing-side: permit-derive) moves the close-time COMPOSE outcome. Gut-check only — explicitly labelled confounded, small-n, direction only.

**Result:** Both levers null.

- inject-pos (novalite, n=10): COMPOSE 0/10 → 0/10.
- permit-derive (novalite, n=6 both-held seeds): COMPOSE 0/6. Changed failure mode (INSUFFICIENT → bare lookups 988/1365), never 2353.
- permit-derive (llama70b, multi-sample, 2 fixed held states): s2 baseline 1/8 vs permit-derive 0/8; s7 baseline 0/8 vs permit-derive 0/8.

kiro confound: same model (claude-haiku-4.5) COMPOSE 2/10 on clean OpenRouter/Bedrock vs 5/5 via kiro. The kiro cell differs on three confounded axes simultaneously (guidance level, platform/harness, formula-in-state rate) and cannot join the clean table.

**Key negatives.** "Permission to compute ≠ knowing what to compute." Composition from an operands-only state is stochastic at ~0–12%; not suppressed by the closing prompt. kiro-NEUTRAL had formula in state yet answered INSUFFICIENT 0/5 — the one reliably-composing cell (kiro-haiku specifics 5/5) is confounded and does not isolate the mechanism. "Our own data blocks" the binding-in-state claim.

**Self-correction.** llama70b single-shot permit-derive "looked promising" (2 INSUFFICIENT seeds flipped to 2353) — multi-sampling (0/8 and 0/8) relabelled it stochastic luck.

**Contribution.** Definitively answers the awareness midpoint question: prompt-injected awareness does not substitute for training-level changes. "Do NOT edit SESSION-4 §3 numbers from this probe."

---

### Arbitrations and Self-Correction Record

**Gauntlet (19 inputs, 5 claims, 2026-06-12):**

| Claim | Median kill prob. | Verdict |
|---|---|---|
| C5 — hard-wired routing | ~78% | Killed: universal panel consensus (Diff-MoE, Switch-DiT, MoDE, ProMoE, eDiff-I) |
| C4 — emergent routing | ~65% | Killed: phenomenon pre-empted; probe asymmetric |
| C1 — coupled schedule | ~50% | Demoted: novelty conditional on C3 |
| C2 — conditioning channel | ~40% | Reframed: regime-conditional under E0's gate |
| C3 — split-unit/coverage structure | ~32% | Promoted: #1 survivor; 13/16 reviews ranked it #1 |

**Verification sweep — ST-MoE fabrication.** Ground-truth fetch (n=1 complete PDF, arXiv 2202.08906) found: 0 of 2 cited sections exist ("Section 4.3: Router Design," "Section 4: Expert Routing"); all 5 agent quotes were mutually exclusive fabrications; real content is Appendix J (Negative Results): expert-identity embeddings "did not improve performance"; routed/dropped-history "made no difference." Meta-lesson: "even verification-mode agents under URL mandates fabricate quotes in both directions and invent section names to anchor them." The gauntlet arbitration itself propagated reviewer 14's fabricated attestation ("mildly pro-D1"). "That propagation is on me."

**M1 fresh-eyes sweep (5 agents, ~50 logged queries):** Returned 0 prior-art papers running a coupled-vs-decoupled input/output staging ablation on a language task. GO verdict sustained after arbitration (5/5).

**Three corrections applied to project documents:** ST-MoE row rewritten from ground truth; LoopMoE ablation acknowledged (magnitude: "quote only after direct read of Table 3"); Remix-DiT authorship corrected (Fang et al., not Tan et al.). "Three corrections were applied to our own documents in the process, which is the sweep doing its job in both directions."

**Additional corrections:** "From Amateur to Master (Yang et al., 2024)" — confirmed misattribution; real paper is Neema et al. 2025. Fresco cited with fabricated authors ("Carlson et al." vs Zheng et al.) and inflated scope. eDiff-I arXiv number: 2202.12855 corrected to 2211.01324. LoopMoE ablation exists (Loop Base vs +IterAdaLN) but magnitude is unresolved and requires direct Table 3 read.

---

## 4. The Discipline as Load-Bearing Content

The methodological discipline of this program is not a footnote. It is the mechanism by which positive findings earn credibility, and without it the positive findings would be worthless.

**Pre-registration with kill conditions stated before runs.** E0's gate thresholds (≥0.90 time-agnostic / ≤0.70 signal-carrying) were registered in experiments/e0_view_classifier/config.yaml before any data was collected. P4's kill condition ("coupled recall must strictly exceed dense raw recall") was pre-registered; when it failed (0.625 = 0.625), the failure was recorded, not rationalized. P7's sequential gate structure (GATE 1 before GATE 2 before battery) was pre-committed; battery spend (~26 h CPU) was withheld pending gate results.

**The forcing line.** The program distinguishes two types of fixes: (1) fixing the architecture — compressor, harness, slicing, edit-op system — which is always permitted; (2) scripting what the model must learn via prompt — which is forbidden. The concrete illustration from P7 is that the retention failure (edit-op id-misaddressing clobber) was diagnosed as a harness artifact and the fix is clobber-safe/content-addressed edit ops — a harness change — not a prompt instruction telling the model what to preserve. The v2 compressor is permitted because it changes the views' information content, not the model's instructions about how to use them. Training a student to answer probe questions would be the same forcing move baked into weights.

**Probe-blind compressor design.** The v2 compressor was designed on document-class properties (foreground module constants/tables/imports/type-structure, collapse boilerplate helpers to name digest) before seeing the test question. E0's Tier-A exclusion (compression_ratio excluded from the gate despite being in the brief's feature list) is the same principle: including it would have made the gate circular — schedule metadata masquerading as view-semantics signal. D7 is the decision record.

**Frozen compressor (Haiku 4.5, D29, locked 2026-06-13).** The production compressor is frozen. All training data for E2-prime will be generated by the same compressor, ensuring cross-experiment comparability. Changing the compressor after seeing results is the compressor-design analogue of changing the probe after seeing results.

**Rate-not-instance reading with explicit mean formulas (D24).** Every reported result is a rate with its denominator. A CI touching zero is unmeasured, not partial success. An instance of the chain firing is not evidence the chain works; the rate at which it fires is the evidence. The first OBSERVATIONS.md quoted means that recomputed from neither the micro formula (sum-valid / sum-candidate-lines) nor the macro formula (unweighted mean of per-pass rates); the maintainer caught it; all tables are now machine-generated from run logs/JSON.

**Pre-committed kill thresholds (D10).** The gate thresholds are stated before the run; the run result is compared against the pre-committed threshold; the verdict is whichever the data produces. P4's kill condition firing is the concrete demonstration that the program is capable of receiving a failure verdict and recording it as such.

**The symmetric-overreach rule.** An error in the flattering direction and an error in the unflattering direction are equally wrong. This is demonstrated repeatedly: (a) "v2 fixed the churn" was an error in the flattering direction; it was corrected. (b) P7's GATE 2 cold result (coupled 2/3) was an error in the over-hopeful direction; the warm arbiter contradicted it, and the warm result was accepted. (c) The provisional-to-final E0 delta (0.433 → 0.561) was not attributed to "Haiku leaks more position" because the instrument also changed simultaneously; the flattering reading was explicitly rejected. (d) "Reporting A confirmed would launder a degenerate null into a conclusion." The negative findings — P4 tie, P6 floor-limited, P7 salience gap, gut-check nulls — are the spine of the credibility. The self-corrections (parser artifact, "v2 fixed it" overcorrection, relevance-control result) are evidence the findings are trustworthy, not hedges to minimise.

---

## 5. Overfitting Traps Going into E2-Prime

This is the most important forward-looking section. Every trap listed here is a live risk, not a theoretical concern.

### (a) The Relevance Confound

P7's salience gap — the floor omits the REGION_SURCHARGE_CENTS lookup table even when asked for "exact values" — has two readings:

- **Reading A (capability failure):** The untrained floor cannot evaluate global structural importance; a trained model would correctly record it. E2-prime is justified.
- **Reading B (correct editorial omission):** The table is an arbitrary RNG lookup with no semantic weight in the document's logical flow; the floor is making the editorially correct choice. Training to record it would be overfitting the model to respond to planted probe signals, not to genuine structural importance.

**The relevance control (EVENT_DISPATCH vs DISPLAY_LABELS) was designed to resolve this fork. It did not.** Both tables — the behaviourally relevant routing table and the cosmetically arbitrary label table — were ignored in 5/5 seeds each. The null-on-both result is uninterpretable for two reasons: (1) no positive control proving instrument sensitivity was included (no brief-relevant structure was confirmed to surface at Tier 1+); (2) singleton-module dilution means both singletons were dropped at inventory level before table-content relevance could matter.

**E2-prime must NOT be trained to record task-irrelevant planted signals.** The training objective must target document-class-general structural behaviour (carry the relational binding between semantically connected units) rather than "produce the probe's expected answers." The fork must be resolved before training data is constructed by adding (a) an in-fixture positive control confirmed to surface at Tier 1+ under neutral+v2, proving instrument sensitivity, and (b) a relevant/arbitrary pair matched on category-representation as well as all other confounds.

### (b) The "→ E2-prime" Streak as an Unfalsifiable Shield

Every experiment in P1–P7 that produced a negative or inconclusive result was followed by "→ E2-prime will address this." At some point this becomes an unfalsifiable shield: any negative is reinterpreted as "expected from an untrained floor" and any positive becomes "evidence E2-prime is needed." The program must keep two distinctions alive going into E2-prime:

- **Model failure vs architecture failure.** If E2-prime also fails on the P7 chain, the question is whether the failure is in the trained model (trainable further) or in the architecture (the edit-op system, the compressor, the slicing scheme). These require different fixes and must be diagnosed independently.
- **Failure vs correct behaviour.** If E2-prime declines to record the REGION_SURCHARGE_CENTS table under a neutral rubric, that may be correct behaviour, not a failure. The program needs a pre-committed criterion for distinguishing the two before seeing E2-prime's results.

**This criterion must be written down and committed to the record before E2-prime data generation begins. It is a required deliverable. As of this draft, the criterion does not exist, and §5(b) cannot be closed until it does. A sketch of the structure it must have: (i) a positive-control condition under which E2-prime's recording of structurally relevant content can be confirmed; (ii) a threshold below which E2-prime failure on the P7 chain — after harness fixes are confirmed and the relevance fork is resolved — constitutes an architecture gate rather than a trainable-further result. Without both, the E2-prime shield remains unfalsifiable.**

### (c) Forcing via the Training Objective

The forcing line applies equally to training. Training the student to produce the outputs that the prompt was forbidden to instruct is the same forcing move baked into weights. Concretely: if the training data consists of (view_k, state_{k-1}, probe_expected_answer) triples where the teacher was specifically prompted to record probe answers at each pass, the student will learn to respond to the probe rather than to structural importance. The training objective must be "carry what is structurally important in the document class," learned from a teacher executing a schedule with a general structural objective — not "record these specific values because the evaluator asks for them." The schedule-blind-teacher control (listed as a stretch experiment) is the one that would license the stronger causal claim.

### (d) Retention is Untested, Not Solved

The clobber mechanism was observed in n=2 instances (seed2 warm go-signal + seed-42 fair-shot). The v2 compressor's independent contribution to retention under recording conditions is unidentified (the discriminating v2+specifics cell was blocked by the forcing-line rule). Retention under a trained model has never been tested. It should be treated as an open question to MEASURE in E2-prime, not an assumption to carry as solved.

Both mitigations remain live requirements for E2-prime's harness:
1. **Heterogeneous v2 compressor** — halved view volume, heterogeneous profiles — plausibly reduces representation churn, but this is unconfirmed in the recording regime.
2. **Clobber-safe / content-addressed edit ops** — the id-misaddressing clobber is a fixable harness issue, not a deep model failure, but fixing it requires the harness to validate that a REPLACE targets the intended content, not just the named id. This is a harness requirement, not a prompt instruction.

### (e) N=1 Inferences Carried as Facts

Two findings from P7 rest on n=2 total observations and should not be treated as established:

- **Clobber mechanism** (REPLACE S3: FUNCTIONS=... overwrites table): observed in n=1 warm go-signal (seed2 t0.7) + n=1 fair-shot (seed-42 t0) = n=2 across two separate runs, consistent but small. The mechanism diagnosis is plausible and actionable but requires replication.
- **State-D-holds** (State-D at Phase-A pass 2, seed-42 t0, seed2 t0.7 warm go-signal): observed in n=2 specific instances. "f4_f8_co_present_at_final=true" and "control table 12/12 seed1" are similarly single-draw observations. None of these constitutes a measured rate.

---

## 6. Concrete Inputs for E2-Prime

The following inputs are directly specified by the P-series findings and should be treated as harness requirements, not design options.

**1. The v2 probe-blind heterogeneous code compressor.** Frozen to scaffold_struct.json. Foreground: module constants, tables, imports, type structure. Collapse: boilerplate helpers to name digest. Target: ~900 tok/view (~7× compression). The compressor was designed before seeing the test question; it must remain frozen throughout E2-prime data generation and evaluation.

**2. Clobber-safe / content-addressed edit operations.** The id-misaddressing clobber (REPLACE targeting wrong stable numeric id) is the identified retention-blocking failure mode. The harness must validate that a REPLACE's target id matches the content it is intended to update, not merely that the id parses. Content-addressed operations (where the op names the content it replaces, not just the id slot) are the principled fix.

**3. The split-unit fixture + backfill defence.** The 64,671-token codebase fixture (seed 70707) with REGION_SURCHARGE_CENTS as the split-unit target is ready to re-pose on E2-prime unchanged. GATE 1 (backfill from fragment-2 alone: 0/4 on the untrained floor, confirming the unit is unguessable without both fragments) establishes the fixture's validity as a discriminating test. GATE 3 (compose ceiling: 4/4 when structure seeded) confirms the closing step is not the bottleneck — the model can produce the correct answer when given correct state. This isolates retention and salience as the open joints, not composition. The trained-model end-to-end outcome remains to be measured by E2-prime.

**4. The gate methodology as the honesty template.** Every new gate in E2-prime should follow E0's methodology: pre-registered threshold, contamination audit, held-out test split by document, probe selected on validation with selection rule frozen, direction-of-risk disclosed if instrument changes, provisional status until production conditions confirmed.

**5. The relevance control as the model that distinguishes capability-failure from correct-omission.** The relevance control must be fixed before training data is constructed: (a) add a positive control in a well-represented category confirmed to surface at Tier 1+ under neutral+v2; (b) match the relevant/arbitrary pair on category-representation. If the fixed relevance control shows the trained model records the relevant table but not the arbitrary one, Reading A is supported and E2-prime training is vindicated. If the trained model records neither, the correct-omission reading must be taken seriously and the training objective reconsidered.

**6. The P3 rubric as the prompt floor for E1-prime.** The strongest prompt-level finding in the P-series is P3's categorical op-type separation (pure ADD at scaffold passes, pure REPLACE at integrate/verbatim passes) under the per-pass behavioral rubric. E1-prime's prompt-floor arm is the rubric version, per pca-outline-v0.3 §4 M2(b). Any trained model must beat this rubric floor to claim that training adds value over prompting alone.

**7. Query-conditioned pass framing (from P5).** The operative lesson from P5 is that vague task framing — not prior-state visibility — suppressed P4's recall. E2-prime's information-extraction passes should be conditioned on the information need (query/recall-framed), not on a generic "capture every concrete specific" rubric. This is a prompt-design requirement, not a training objective.

---

## Summary: What Was Shown, What Was Not, and Why E2-Prime is Justified

**What was shown (in isolation, at true strength):**

- E0: the explicit pass-position channel carries non-redundant information not recoverable from view content alone (Tier-B bucket accuracy 0.561, n=360 test views, pre-registered gate call "signal-carrying"; K=8, GovReport only). Component-in-isolation.
- P1–P3: an off-the-shelf 7B can produce syntactically valid edit-ops at ≈1.000 rate (parser v2.1, n=1 document each); a per-pass behavioral rubric produces categorical op-type separation (pure ADD at scaffold passes, pure REPLACE at integrate/verbatim passes); full-document visibility collapses staging entirely (output_staged_only final state 354 tok vs coupled 992 tok). Component-in-isolation.
- P4: coverage delivered every planted fact to a view; co-presence F4+F8 held in state; bottleneck is integration salience, not coverage (component-in-isolation diagnosis). Kill condition failed (tied 5/8 = 5/8).
- P5: prior-state contamination is not the cause of P4's misses; task/query specification is the operative lever. Mechanism check, n=3 probes.
- P7 GATE 2 (cold proxy only): coarse pass preserved full 24-entry lookup table in 2/3 draws; verbatim-only preserved the usable mapping in 0/3. Cold empty-state conditions. The pre-registered warm arbiter (accumulated state) reversed this: sparse hosting (~1/3 sampled draws) and immediate pass-3 clobber in every observed recording; cold GATE 2 is not a warm-conditions result.
- P7 GATE 3: compose ceiling 4/4 when full structure seeded — the closing step is not the bottleneck; the model can produce the correct answer when given correct state. This isolates retention and salience as the open joints. Component-in-isolation.
- P7 cross-family: the full chain fires in 3 independent model families (Qwen-72B s2, Meta-Llama-70B s9, Mistral-24B s42 temp-0), all blind and untrained. n=1 per family. Each a single draw.

**What was not shown:**

- The full chain (record AND retain AND compose) fired end-to-end in 0/4 draws in the primary P7 test (fair-shot, specifics-demanding prompt). The 3-family cross-family existence composes are each n=1 single draws; small count differences are within sampling noise.
- Retention through the multi-pass sweep: never successfully observed. Retention is open, not solved.
- Any salience-shaping effect of the coarse scaffold: P6 was floor-limited (≤1/4 per detail, most draws zero, pre-registered interaction uncomputable).
- The relevance-control fork: the capability-failure vs correct-editorial-omission distinction is unresolved.
- Recall advantage over a cheap dense baseline: tied at 5/8 (P4, n=1).
- Any positive prompt-level effect of the bare position field (P2: null, 0.979 vs 0.983).
- GATE 2 cold result replicated under warm/accumulated-state conditions: the pre-registered warm arbiter showed sparse hosting (~1/3 sampled draws) and pass-3 clobber in every observed recording instance, directly contradicting the cold 2/3 result.
- The coarse scaffold out-composing the verbatim-only arm on close-time answer rate: across model families the tally was llama 1v0, gpt 0v0, nova 0v0, mistral 1v1, haiku 2v7 in favour of verbatim. The scaffold added no demonstrated compose-rate advantage over simply reading verbatim tiles on an untrained floor.

**Why the trained-model step is justified despite the floor not being validated:**

The untrained 7B was not expected to pass the P4 kill condition or fire the P7 chain reliably. The floor result is informative because: (1) it did not fail in a way that closes the gate — the chain was not impossible (3-family existence at n=1 each); (2) the blocking joints are now identified (salience/recording under neutral rubric; retention via id-misaddressing clobber; recombination of operands without relational binding); (3) each blocking joint has a candidate fix (query-conditioned rubric; clobber-safe edit ops; trained student carrying the binding); (4) the three fixes correspond to three different training targets, each testable independently. The warrant for E2-prime is that the architecture is *not unfeasible* and the failure modes are *specific and addressable*, not that the floor was validated.

"This is a proposal, not a validated finding. Small scale viability experiments are in progress."

---

*This document is an internal research record. All rates, n-values, and open questions are stated as accurately as the primary-source extracts permit. Where the primary sources are ambiguous or a finding rests on n=1, this is stated explicitly. Every effort has been made to analyse the data scrupulously, but the dataset is large and reviewed by a single maintainer, so oversights may remain — corrections are welcome. The discipline and the negatives are not hedges — they are the contribution.*