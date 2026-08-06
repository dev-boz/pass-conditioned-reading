# The frozen-stack search — what makes it work, before anything else is trained

**Status:** plan, 2026-08-06. F1 is probe-class and runnable on the maintainer's word. F2's bar
and arms are DRAFT until the maintainer signs §6 — per the working mode, verdict wording is the
maintainer's. This plan refines the 07-28 sequence's Phase 2; it does not replace the Phase-3
decision rule.

**Maintainer's framing (2026-08-06, recorded):** find out what makes the architecture work
semi-reliably — which combination of prompting, compression strategy, structure, guards, scale —
*then* go into training knowing exactly what is most valuable to train.

**Why this is the right order now:** Stage-A training taught format, not the job (relation
demanded 0/28; placeholders 1.8% of rows; locator hints 0.03%; `ANSWER:` 0×) — the pipeline
distills faithfully, the curriculum was empty. Meanwhile the replicated end-to-end result used
the trained 1.5B as recorder, and **the assembled winning stack has never been run with an
untrained recorder.** If frozen weights + structure get most of the way, training's job shrinks
to a measured residual — and the residual is the curriculum.

---

## 1. What is already answered (do not re-run; references)

| axis | answer | where |
|---|---|---|
| reader scale | free at ≥3B; state is exactly sufficient; concordance perfect | PYRAMID-COMPRESSOR-RESULTS (compose ladder), confirm 4/4 |
| compression | role-aware LLM arm preserves the table + writes the relation; salience tracks recording monotonically | PYRAMID-COMPRESSOR-RESULTS findings 2-3 |
| guards | `retain` eliminated recorded-then-lost (0 losses, c1 0/10→3/10); `marked_hard` 10/10; both signalling variants dead | 08-05 handoff; retention probes |
| prompts on the trained 1.5B | 0 for 5 (anti-grind, noclobber ×2, selfmark, marked_soft) | ledger; PYRAMID-COMPRESSOR-RESULTS |
| scaffold structure, untrained | promptable at 7B with the TERSE rubric (10/10 homes); the long explaining prompt HURTS ≤3B | P1e |
| view density | the step is 10%→35% (1/20→7/20); >35% shallow; composition caps at ~half | SIGNAL-DENSITY-RESULTS (P1i) |
| slot syntax | not load-bearing (name-mention entries fill as well as [TBD:] slots) | P1b |
| scale alone | does not buy RECORD (3B chain 0/5, mapping 0/6) | 07-26 arbitration |
| k/K channel | inert twice; scoped: student never trained on a ladder | P1d, P1d_pyr |

The search below runs only the gaps.

## 2. The question, stated once

**What is the minimal frozen-weights stack — recorder scale × prompt × compression × guard ×
state policy — that makes record→retain→compose work semi-reliably? And which behaviors does NO
frozen stack produce?** The second list, ranked by how hard it blocks the chain, is what training
is for.

## 3. F1 — the joint battery sweep (single-pass cells, $0, current materials)

Five joint-level micro-tests, all existing constructions. Frozen weights. Probe conventions
throughout: `gate_legal=false`, dual scoring, seeds 1-10, temp 0.7, forcing-boundary asserts,
strict guard unless the guard IS the axis. Any cell that becomes a headline gets a fresh-seed
block before write-up (three-tier rule, as P1i did).

| joint | cell construction | metric (audited matchers) |
|---|---|---|
| J1 RECORD a binding | P1i `d30` view (35.5%, the rebuild's floor) + no-home s25, k=12 | applied `queried_mapping` |
| J2 FILL own scaffold | P1f pair: terse-rubric scaffold at k=4, then the pass-26 fill, paired by seed | ACQUIRED adder (post not pre) |
| J3 RETAIN under pressure | pinned window (graded s5 pass 56 state, k=57-63) | HELD through the known-fatal pass |
| J4 WRITE a relation | ctrl8 homes + pass-26 tile (declared oracle, comparison to the only cell relation has ever fired in) | applied relation |
| J5 CLOSE (anchor) | close_only on the three confirm c1 states, temp 0 | returns 2353 |

Sweep axes:

- **Models:** `qwen3b` (f16) and `qwen7b` (Q4 — the §6-07-26 quantization caveat stands: an
  op-format collapse at 7B-Q4 is inconclusive, not evidence; the clean-id cue from P1f §5.4 is
  the known mitigation). `qwen14b` (partial offload, ~8× slower) only as an escalation rung on
  joints where 7B fails. The trained 1.5B is the comparison column from ARCHIVED numbers — no
  re-runs.
- **Prompts (J1, J2-fill, J4):** `P_terse` (current rubrics) · `P_struct` (rubric + SALIENCE +
  ADD_LICENSE — the two splices that target measured mechanisms) · `P_expl` (EXPLAINED_ROLE).
  Scaffold half of J2 stays terse (P1e: terse wins for structure).
- **Guards (J3 only):** strict vs `retain`; `marked_hard` added only if losses appear under
  `retain`.
- J5 runs once per model, no prompt sweep — it is the known-free anchor.

Cost: ~300 single-pass draws + 4-6 retention windows (~70 passes each) + 30 close calls.
At 9-40 s/draw on the 1080 Ti: **one to two overnight batches, $0.** Harness deltas are small:
`--models` already exists; J1/J2/J4 prompt-variant cells exist for a subset of models; J3 needs
`--model` plumbing in `retention_probe.py`; plus a summarizer that assembles the capability map
(joint × model × prompt, archived-student column included) from the artifact JSONs.

**F1 output:** the capability map — which joints unlock with what, per scale, and which unlock
nowhere.

## 4. The fixture rebuild sits between F1 and F2

F1 is fair on current materials (densified views + pinned states test joints, not the document).
F2 is only meaningful on the rebuilt fixture — on the current one the best compressor hands over
the whole answer at pass 1 (the split-fact break). The rebuild spec is now fully numeric:
**total distinctive content > V** (08-05) **and ≥ ~35% distinctive share per decisive tile**
(P1i), checked with `author_pyramid_views.py --budget-audit` plus a per-tile audit before
authoring. Demand repairs 1-8 (ledger) ride along. F1's results say which stacks the rebuild is
worth building for.

## 5. F2 — assembled stacks, full chain, pre-registered (the Phase-2 battery, widened)

Pre-named construction rule (arms filled from F1, named before any chain runs):

- **S-A** best untrained (model × prompt) from F1 + role-aware compressor + `retain`
  (+`marked_hard` if J3 required it) + pyramid, stage by level.
- **S-B** same stack, `graded` compressor — the faithful arm; composition claims live here.
- **S-C** the trained 1.5B in the same harness — the incumbent.
- **S-D** (optional) the 3B stack if F1 shows 3B ≈ 7B — the cost lever.

Protocol: rebuilt fixture, 10 sampled seeds + t0 anchor per arm, faithful/assisted stamping per
arm, every c1 candidate hand-verified, close read by the ≥3B reader per the recorder/reader
design. Pre-registration written and PUSHED before the first draw (standing rule, 08-06).

## 6. The bar — DRAFT NUMBERS, maintainer signs before F2

"Semi-reliable," proposed: on the faithful arm, **c1 (both operands in the final state) ≥ 5/10**;
**the ≥3B reader composes on every c1 draw** (sufficiency, the replicated signature); **zero
recorded-then-lost**; recorder's own close reported, not gated. Falls short = the joint-level
attribution (ever-recorded / held / close), same as every chain battery before it.

*Maintainer: sign or edit these numbers; they freeze at F2 pre-registration.*

## 7. F3 — the residual is the curriculum

- **If S-A clears the bar:** the architecture works untrained; training becomes a cost lever
  (distill the 7B stack's behavior down to 1.5-3B), targeted at F1's measured deltas.
- **If arms fail:** the joints that no frozen stack produced — current prediction from the map:
  **binding-preserving fill** (untrained 7B fills homes but shreds name=value) and
  **relation-writing** (0/10 in every untrained cell ever) — become the training targets,
  ranked by F2 attribution.
- **Curriculum gate (new, mandatory before Phase 3):** the training set must mechanically show
  minimum demonstration rates for every scored behavior — placeholder rate, relation-
  demonstration rate, full-table-transcription rate, `ANSWER:` presence in closing rows, locator
  hints if lever 5a is adopted — all inside the health gate, all counted BEFORE training. The
  counters exist (07-26/28 audits); the change is running them pre-train. Never again train
  toward a behavior the data cannot be shown to contain.
- Data generation: constructed pairs (lever 15) preferred — placeholders and forward references
  exist BY CONSTRUCTION, no teacher-incentive problem; hand-curated gold (lever 16) as seed;
  teacher rollout only for behaviors the teacher demonstrably performs.
- Phase-3 decision rule (07-28) then applies unchanged: one A5000 run, one lever, 3B vehicle.

## 8. Out of scope, unchanged

M-NL G2 stays **held** for the maintainer's `claude -p` alternative. P1c (budget enforcement)
stays on the board — foldable into F2's harness if the maintainer wants it as the state-policy
axis. The wall test governs as always: if successive instantiations stop producing component
improvement, the project fails.
