# E2′ — Pre-registration: the trained-student experiments

**Status:** DRAFT for maintainer sign-off. Becomes binding when committed. No teacher data has been generated; no student has been trained.
**Date:** 2026-07-10
**Consumes:** E0-final (signal-carrying → the explicit channel and E1′ arms proceed); P3 (rubric = the prompt floor, outline §4 M2(b)); P4/P5 (query-conditioned framing, §6.7); P7 + cross-family (the chain gate target and its floor rates); docs/E2PRIME-CRITERION.md (verdict attribution — the §5(b) deliverable); experiments/p7_split_unit/RELEVANCE-CONTROL-V2.md (the P-B precondition).
**Kill criteria for M1/M2 are owned by pca-outline-v0.3 §4 and are not restated here.** This document specifies the runs.
**Amendment rule:** dated pre-run addenda only, committed before the affected run.

---

## 1. Shape: three gated stages

E2′ is not one experiment; it is a staged program with the cheapest kill first.

| Stage | What | Gated by | Kills available |
|---|---|---|---|
| **A — chain gate** | Train ONE student (coupled schedule, explicit channel). Re-pose the unchanged P7 split-unit battery. | E2PRIME-CRITERION §1 preconditions P-A/P-B/P-C | Architecture gate at ≤1/10 (criterion §3) — stops everything |
| **B — M1 factorial** | Train the remaining schedule arms; matched-compute comparison. | Stage A ≥ gray zone outcome | M1's own pre-registered kills (outline §4) |
| **C — E1′ / M2 channels** | Re-render identical tuples per conditioning channel; train channel arms. | Stage A pass; E0 regime call (already: signal-carrying) | M2's pre-registered kills (outline §4) |

Stage A answers the question this repo has been building toward: *does training move the record→retain→compose chain at all?* It is deliberately the smallest trained experiment that can receive the architecture-gate verdict. Stages B and C spend nothing until it survives.

---

## 2. Student

- **Base:** Qwen2.5-1.5B-Instruct. Same family as the floor experiments (comparability); small enough that the criterion's floor expectation (0/10 end-to-end untrained) is conservative. The criterion's single-retry escalation, if taken, is Qwen2.5-3B-Instruct.
- **Method:** LoRA (r=16, α=32, dropout 0.05, target = attention + MLP projections), fp16 storage / fp32 compute (Pascal has no usable fp16/bf16 math), gradient checkpointing, seq len 4,096, effective batch ≈ 16 via accumulation, lr 1e-4 cosine, 2–3 epochs. 4-bit NF4 quantization (QLoRA proper) is an engineering option if the 3B escalation is taken and memory demands it; it changes nothing scientific.
- **Hardware:** the local box (Threadripper 1920X, GTX 1080 Ti 11GB, 96GB RAM), training under WSL2. Expected wall-clock ~1–2 days per student at the §5 data scale. These are engineering defaults: tunable until data generation begins, frozen after (any later change = dated addendum).
- **What the student learns:** the training example is the rendered pass — system prompt (op grammar v3 + P3-style per-pass rubric + need-class framing) + position field + current state + view → target = the teacher's edit ops (pass 1: the bounded scaffold render, per outline Variant 2's hybrid mode). Loss on the target tokens only.

---

## 3. Teacher

- **Model & path:** Claude Haiku 4.5, delivered **kiro-cli first** (maintainer directive 2026-07-10: spare kiro quota; `p7raw` agent strips the kiro harness layer, effort=low keeps it non-thinking) with `claude -p` as fallback — the D30 precedent of mixed delivery paths of one model, with per-pass path provenance recorded in every trajectory and rendered row, under the standing KIRO_FIDELITY check. Neither path exposes temperature/seed (named limitation; acceptable for a teacher, impossible for a comparison arm). The compressor and the teacher are the same engine in different roles; this correlation is **named**: results are read under the outline's own framing — *what is learnable from a schedule-executing teacher per channel* (distillation efficiency), not a universal causal claim.
- **Teacher policy:** executes the coupled schedule on training documents. Prompted with: the v3 op grammar (content-addressed REPLACE/REMOVE), the per-pass behavioral rubric (P3 lineage), the need-class framing per E2PRIME-CRITERION §2, and a general structural objective (carry document structure; integrate; surface detail late; maintain the bounded state). **Forbidden in all teacher prompts:** any reference to evaluation probes, planted structures, specific tables, or "record X" imperatives — the §2 forcing boundary, audited (every prompt archived with the dataset).
- **Teacher-quality gate (before mass generation):** n = 20 trajectories hand-audited. Requirements: v3 syntactic validity ≥ 0.95; edit ops actually maintain a coherent state (spot-check applied states); zero forcing-boundary violations; content-address quotes present on ≥ 0.9 of REPLACE ops (the student must see the safe grammar to learn it). Failing gate → iterate on harness/format (permitted) and re-audit; cognition-scripting fixes are not available.

---

## 4. Corpus (training) and the leakage gate

Three slices, ~300 documents total, each 40–80K tokens:

| Slice | ~n | Purpose | Named risk |
|---|---|---|---|
| (a) GovReport-family long prose | 120 | The E0/P4 document class; views regenerable by the frozen pipeline | — |
| (b) Synthetic codebases from the fixture *generator family*, fresh seeds ≠ 70707 | 90 | Code-class structure: constants, tables, call sites, cross-module bindings | **Distribution overfit to the generator's style** — mitigated by (c) and by the eval fixture's exclusion; declared, not hidden |
| (c) Real-code pseudo-repos (permissively-licensed Python packages concatenated to length) | 90 | Distribution breadth for the code class | license/provenance recorded per doc |

**Leakage gate (mechanical, archived, zero-tolerance):** the eval fixture (seed 70707) and everything derived from it never enter training. Before training: scan the full training corpus for (i) any 12-gram overlap with the fixture's five planted texts, (ii) the probe identifiers and values (`REGION_SURCHARGE_CENTS`, `RECONCILIATION_ADDER_CENTS`, `compute_line_surcharge`, `STAGE_ORDER`, `EVENT_DISPATCH`, `DISPLAY_LABELS`, `CARRIER_FUEL_BP`, the integers 988/1365/2353 as table-adjacent tokens, and every key:value pair of every planted table). Scanner output committed alongside the data card. Any hit → the offending document is dropped and the drop logged.

**Scale estimate:** ~300 docs × K≈8–16 passes ≈ 3,000–4,500 examples ≈ 15–25M training tokens/epoch. Teacher generation ≈ 10–15M input + 1.5–2.5M output Haiku tokens ≈ **US$20–40 real-time (≈ half batched)** — the only API spend in Stage A.

---

## 5. Harness (frozen for all stages)

- **Edit ops:** parser/state **v3** — content-addressed REPLACE/REMOVE (optional verbatim quote of the target entry's current text between id and colon), quote-verified apply with redirect-by-content; quote-less REPLACE under **guard=strict** (misaddressed writes and unquoted slot-repurposing rewrites refused, logged; empirically 0 false blocks on 157 archived known-good ops). Grammar and guard semantics per D31 (+ same-day amendment); P-A obligations per E2PRIME-CRITERION §1 are satisfied as of D31/D32.
- **Compressor:** frozen per document class — Haiku 4.5 (D29) for prose; the frozen probe-blind v2 code compressor for code-class docs. Compressor code never edited mid-program; outputs re-derived deterministically per fixture/corpus version.
- **Schedule:** `src/pca/schedule.py` unchanged; state budget per the parent window invariant; pass-1 scaffold budget B_s per outline Variant 2.
- **Provenance:** every run archives config hash, prompts, seeds, per-pass state snapshots, and (new) per-op apply outcomes including guard blocks/redirects.

---

## 6. Stage A — the chain gate (full specification)

Everything here is fixed by E2PRIME-CRITERION §3; restated operationally:

1. **Arms:** trained student vs untrained same-base floor. Battery per arm: n=10 sampled (temp 0.7, seeds 1–10) + deterministic anchor (temp 0, seed 42; reported separately).
2. **Task framing:** query-conditioned (need-class) per criterion §2. A neutral-brief arm is additionally run **only if** RELEVANCE-CONTROL-V2 lands branch A (its outcome table governs).
3. **Fixture:** unchanged split-unit fixture; v2/v3 fixture version per RELEVANCE-CONTROL-V2 (probe bytes asserted identical); frozen scaffolds re-derived.
4. **Measures:** end-to-end compose (the verdict input); RECORD/RETAIN/COMPOSE component rates with warm per-pass tracking (the §5(d) retention measurement — retention is measured here for the first time under recording conditions, never assumed); guard-block/redirect counts (replicates or refutes the n=2 clobber mechanism); GATE-1 backfill re-run (unguessability holds for the student); GATE-3 seeded-compose re-run (closing competence); relevance-control v2 on the student (criterion §4.3); the P3-rubric prompt floor on the base model as a reference row (the bar any training claim must beat, §6.6).
5. **Verdicts:** criterion §3 table, applied mechanically (≥5/10 / 2–4/10 + single retry / ≤1/10). No other reading is available.

---

## 7. Stage B — M1 factorial (deferred details, binding scaffold)

Trained arms on condition-matched tuples (same documents, same teacher policy, schedule per arm): **coupled** (the Stage-A student) / **input-staged-only** / **output-staged-only** / **misaligned-coupled**; plus the **P3-rubric prompt floor** (untrained) and the **matched-compute single-pass dense baseline**. Budget = total tokens processed (prefill+decode), FLOPs and wall-clock reported. M1's interaction-term claim and kills per outline §4.

The eval battery for M1 (task set, blinded judge protocol, scoring rubric) is **deferred to a Stage-B addendum** that must be committed before any Stage-B training run — staged pre-registration, same discipline as the P6 battery. Stage B does not start unless Stage A ≥ gray zone.

## 8. Stage C — E1′ / M2 channels (deferred details, binding scaffold)

The Stage-A tuples re-rendered per channel: (a) explicit `(k,K)` field (= Stage-A student), (b) prompt-position + rubric, (c) no signal, (d) binary mode token. Four students on identical data; metrics and kills per outline §4 M2. Gated on Stage A; E0's regime call already satisfied. Stretch: schedule-blind-teacher control (unfunded, unchanged).

---

## 9. Not claimed / discipline

- Stage A passing ≠ architecture validated: M1's interaction term is the paper (outline §7). Stage A is an existence-and-reliability result on a trained student.
- **The chain gate is a concession test** (concrete outcome ≠ the stated goal of maintaining long-session nuance — maintainer's standing caveat, recorded in E2PRIME-CRITERION §3). The goal-aligned test is drafted (docs/NUANCE-EXPERIMENT-SHAPE.md) and deferred post-E2′; on a fail-or-inconclusive Stage A it runs as a trained-vs-untrained comparison. On a dual failure, the pre-named architecture answer is docs/DISCO-NATIVE-ARCHITECTURE.md (internal latent state — no edit sequence).
- All results are rates with denominators; the deterministic anchor is never pooled with sampled draws; per-seed tables are the primary record.
- Nothing is published until reviewed; drafts surface to the maintainer first (this document included).
- The teacher confound (distillation framing) and the generator-family risk (slice b) are carried in every write-up of Stage results.
