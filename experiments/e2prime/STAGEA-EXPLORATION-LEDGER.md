# Stage-A′ Exploration Ledger

**Status:** exploratory, post-gate. Nothing here is a verdict instrument.
**Date opened:** 2026-07-21, immediately after the Stage-A architecture gate (see STAGEA-CHAIN-GATE-RESULTS.md).
**Revised:** 2026-07-28, after the second gauntlet (13 reviews) and its arbitration (`docs/gauntlet-arbitration-2026-07-28.md`). Statuses, kills, and credits below reflect that arbitration; the 2026-07-26 arbitration remains the authoritative account of the audit findings themselves.

## The operating mode (maintainer, 2026-07-21 — unchanged)

This project is explicitly a **process, not a one-shot**: try levers, measure, adapt. Much of the methodology is AI-drafted and maintainer-checked; either can be wrong, so instruments are held with humility (the battery's scorer was corrected 4× mid-run; the 07-26 session withdrew four interpretations to measurement). The rules that keep exploration scientific:

1. **Probes are cheap, labelled, non-verdict.** Oracle knowledge is allowed in a probe if declared. No probe number is ever pooled with a gate. Probes never wear gate language (bar-clearing talk belongs to pre-registered verdicts only).
2. **A lever graduates only by fresh pre-registration.** A modified instantiation gets its own dated pre-reg with frozen bars *before* its training run.
3. **Negative probes are recorded, not discarded.**
4. **The wall test:** each instantiation's pre-reg names the **component rates** it expects to beat from the previous instantiation. The project fails when successive instantiations stop producing component improvement.
5. One lever per instantiation where affordable; declare the confound where not. **Defect repairs are not levers** and do not consume the budget.
6. **Anomaly rule (three tiers, adopted 07-28):** *isolated success* (hypothesis fuel only) → *replicated mechanism* (reproduces under named ablation, fresh pre-registered draws, artifact-visible provenance) → *demonstrated capability* (pre-registered rate vs floor, exact test, n≥10). Anchors never pool with sampled draws.
7. **Dual scoring:** every op-level metric reports *proposed* (emitted) and *applied* (guard-passing) separately. Denominators inline. P-values state sidedness. Length-sensitive metrics banned from all arms.

## What the evidence now says (post-audit, post-arbitration)

The chain needs **three** recorded facts — mapping `23→988`, adder `1365`, and the **relation** `fn(region) = table[region] + adder`. Mechanized 2026-07-28: **0/28 archived final states across all arms record the relation** (fn named 2/28). The chain was unpassable **by reading**; passable only via an inference that fired once (n=1) in a 2-entry oracle state.

- **RECORD is the blocked joint, and it is demand-shaped:** the verbatim rubric asks for "values, names and quotes," never behaviour; the teacher's modal policy is lossy summary (61.4% of 559 events); scaffolding was never trained (placeholders 1.8%, locator hints 0.03%); the close was never trained as QA (`ANSWER:` 0× in 5,730 rows) and closing rows sat outside the health gate; the length gate silently dropped 52% of verbatim rows; the state budget is prompt text only and ran to 1.92×.
- **COMPOSE from a clean state is scale-limited, not representation-limited:** identical seeded state, trained 1.5B 1/10 vs untrained 3B 9/10 (two-sided Fisher p≈1.1×10⁻³), 7B 10/10. Scale does not buy RECORD (3B chain battery 0/5, mapping 0/6).
- **The suppression step:** same tile/rubric/model, empty state → 7/10 relation *emitted* (ops malformed, would be guard-blocked); any 25+-entry state → ~0/10, shape-irrelevant, n=10 every cell. Three live explanations (training artifact / rubric effect / structural), discriminator = P1a below.
- **The dissociation:** training bought protocol-following (7.0 applied ops/pass), scale bought composition; **no run has ever had both.** The empty cell — trained 3B — is the architecture question.

**Current honest claim** (use this, nothing stronger): protocol execution trains cleanly at 1.5B and produces a state its own builder cannot use; compose is free at 3B untrained; recording under any non-empty state is the unsolved joint, and the first training run tested a fixture whose scored demand training never made. Missing for anyone else to care: one end-to-end pass on a fair fixture, and one beat of a budget-matched external baseline (BooookScore pair, RAG).

## Demand repairs (NOT levers — prerequisites for any next instantiation)

1. Recording rubric demands **relations/behaviour** ("record what each function computes"), not only values/names/quotes.
2. Recording rubric **licenses ADD** for content with no home in the state.
3. **Train demand = eval demand = scoring form** (`ANSWER: <integer>` present in training close rows).
4. **Closing rows inside the health gate** (`pc_check.py` stage filter).
5. **Fixture multi-exposure:** the relation visible in ≥3 passes at varied state pressure (split-fact constraint preserved — the fn body names both operands; the *values* still never co-occur).
6. **Positive control** planted: an element the current policy provably records, so capability-failure separates from correct-editorial-omission (the P7 relevance fork). (inkling, gpt-5.6, mimo)
7. **State budget enforced in the harness** (the enforcement is a repair; the *policy* is lever 13).
8. Report length-gate drops per stage before training on any regenerated data.

## Lever board

| # | lever | joint | evidence / conditions | cheapest next probe | status |
|---|---|---|---|---|---|
| 1 | Close prompt order (question-first) | close/retrieval | probed 07-21: 0/10 | — | **CLOSED, negative** |
| 2 | Length-preserving distractor removal | close | probed 07-21: dissociation (distractors steer retrieval; length blocks compose) | — | **CLOSED as diagnostic** |
| 3 | Recording-pass prompt order (data→instructions) | RECORD | untested; still the only training-side change that re-renders the archived 5,730 rows at zero teacher spend (prompt reorder keeps completions as valid targets; rubric *content* changes do not — they change what the completion should have been) | $0 floor probe, then re-render retrain | **OPEN** |
| 4 | Selective reading (rate slices, read only what matters) | RECORD + state size | untested; overlaps P1c budget probe — run that first | prototype on frozen weights | **OPEN** |
| 5 | **Typed-slot scaffold** (guided reading, concretized) | RECORD (gives REPLACE a target; the protocol's own mechanics require it) | conditions from gauntlet: rigid machine-parseable slot grammar (opus), slot cap + ops reserved for content (mimo/qwen/cantus), harness-supplied slot vocabulary (gpt-5.6), FILL/type-tag guard fallback (opus); known risk: slot selection is the salience decision one pass earlier (glm); suppression may fire on slot-heavy states too (deepseek) | **P1b** hand-seeded slot-fill probe, pass 26, both models, $0 | **OPEN — gated on P1b** |
| 6 | Reverse reading (later pass requests re-read) | compose/binding | untested | defer until 4/5 probed | parked |
| 7 | Slice overlap control | RECORD completeness | marginal | — | parked |
| 8 | Composition-focused training (closing-heavy mix) | compose | **KILLED 07-28** — GATE-3 ladder: compose is free at 3B untrained (9/10); training the compose joint at 1.5B fights a scale wall (1/10 seeded). Training targets RECORD now. | — | **CLOSED, superseded by 9** |
| 9 | **Scale step → 3B** | compose ceiling | resolved as probe: untrained 3B 9/10 seeded compose; scale does not buy RECORD (0/5 chain). 3B is the **vehicle** for any Phase-3 run, not a fix by itself | untrained-3B battery on the repaired fixture (Phase 2) | **OPEN — the designated training vehicle** |
| 10 | Native architecture (latent slot bank, AdaLN) | both joints | op-granularity pillar retracted 07-26; flat-state retrieval pillar stands; **first measured support arrives only if P1a returns "structural"**; BM25-at-close success would be adjacent evidence (glm: flat text needing external retrieval concedes the same point) | wait for P1a | OPEN — destination if text-state levers plateau |
| 11 | Early-stop / prefill / pass skipping | efficiency | speed, not fix | — | parked |
| 12 | **M-NL nuance experiment** | test validity | elevated by panel consensus: everything so far is internal to the harness; BooookScore supplies the external baseline pair, LoCoMo-Plus the length-bias hazards | NUANCE-EXPERIMENT-SHAPE.md on the existing student/floor pair, inference-only | **OPEN — runnable in parallel now** |
| 13 | **Budget policy** (who evicts: harness-LRU vs reject-and-reprompt model compaction; stage-scaled op_cap) | RECORD under pressure | enforcement itself is repair #7; the *policy* is a design choice; kimi: log evictions, score "recorded-then-evicted" as third outcome class, pin unresolved slots | **P1c** forced eviction at 4,000 tok + stage-scaled op_cap variant (minimax), $0 | **OPEN — gated on P1c** |
| 14 | **Retrieval-at-close companion arm** (BM25 over state) | close/retrieval | legitimate as *declared companion only*: non-oracle, pre-registered top-k, vs budget-matched retrieval-over-flat-summary baseline (kimi); cannot substitute for RECORD (nothing retrieves an unwritten relation); **glm's collapse warning:** if this is what closes the gap, the claim becomes "expensive RAG-store builder" and the P4 RAG-tie is waiting | add as companion arm to the Phase-2 battery | **OPEN — companion only** |
| 15 | **Constructed-pairs data generation** (gold state → typed-slot blanking; replaces teacher rollout) | RECORD training signal | diffusion *theory* framing killed by unanimous panel (compression deterministic + semantically selective; k not a sufficient statistic — glm); survives as engineering iff falsifiers pass: **F1** ambiguity check, design-time $0 (gpt-5.6) → **F2** k-conditioning probe = P1d (deepseek) → **F3** constructed-pairs LoRA, held-out fill (opus/glm) → **F4** separability classifier vs real rollout states = the exposure-bias measurement (cantus). Non-monotone state specificity is a design requirement of the new data, not a prediction | F1 on the repaired fixture's gold state | **OPEN — gated F1→F4** |
| 16 | **Hand-curated gold trajectories** (~20 × augmentation) | RECORD training signal | sonnet-kiro; teacher-free, coverage-poor; best use: few-shot seed for repaired teacher generation | cost it after Phase 2 | **OPEN — fallback / seed** |
| 17 | **Phase-A/Phase-B conditioning separation** (k/K = resolution only; region coverage gets its own counter) | conditioning coherence | unanimous 13/13; matches the filtering spine in DISCO-NATIVE-ARCHITECTURE.md; applies to ANY rebuild regardless of lever 15's fate | design-time, free | **ADOPTED for any rebuild** |

## The sequence (from the 07-28 arbitration §7)

**Phase 0** instrument debts → **Phase 1** $0 battery (P1a suppression 2×2 + padding cell, dual-scored; P1b slot fill; P1c budget; P1d k-conditioning) → **Phase 2** demand repairs + fixture rebuild → untrained-3B battery → **decision rule:** pass ⇒ architecture claim stands untrained, training freed; fail-on-RECORD ⇒ **Phase 3** one A5000 run, 3B, repaired data, one lever. **M-NL runs in parallel any time.**

## Instrument debts

- **PAID 07-26:** secondary prose-number metric (`score_prose`).
- **PAID 07-28:** relation as first-class joint — `_relation_flags()` in `analyze_chain_gate.py`, validated (S83 near-miss rejected, GATE-3 seed matched), 0/28 re-verified mechanically.
- **OUTSTANDING:** port paraphrase-robust matcher into the runner's live flags; archive `usage.completion_tokens` per call; dual proposed/applied scoring in probe harnesses (rule adopted, code not yet); port the 07-26 scratchpad probes (relation-demand A/B, crowding, schema control) into `experiments/e2prime/` before re-running them.

## Immediately runnable for $0 (say the word)

- **P1a** — kimi's 2×2: {trained 1.5B, untrained 3B} × {integrate rubric, ADD-license rubric}, same pass-26 tile, 25-entry state, n=10/cell, + length-matched padding cell, dual-scored. Discriminates training-artifact / rubric / structural in one weekend.
- **P1b** — typed-slot fill probe: seed `REGION_SURCHARGE_CENTS table (pricing/region_tables.py) — values TBD` (+ fn-contract slot), run pass 26 on both models.
- **P1c** — enforced 4,000-tok budget re-run (+ stage-scaled op_cap variant).
- **P1d** — k∈{5,15,26} conditioning probe on the trained student.
- Lever 3 floor probe; M-NL prep.
