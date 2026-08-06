# The schedule discrepancy — what ran vs what the README specifies

**Found:** 2026-07-30, by the maintainer, reading the measured per-pass cost back against the
architecture. **Status:** confirmed in code and in the archives. Nothing is committed.

## The README

> First pass is the whole session highly compressed, Second 2 passes are the conversation split
> in 2 with slightly less compression. The final passes are verbatim text.

A **tiling pyramid**: every level partitions the whole document; compression falls level by level;
the last level is verbatim. `k` indexes resolution — which is the thing pass-conditioning exists
to condition on, and the thing compression-as-noise needs in order to be a noise schedule.

## What is implemented

Two schedules exist. Neither is the pyramid.

| | `src/pca/schedule.py` (D5) | `src/pca/planted.py::build_schedule` (D25) |
|---|---|---|
| pass 1 | whole document → V ✅ | one 1/6 chunk ❌ |
| compression profile | geometric, → verbatim ✅ | two levels only ❌ |
| coverage per level | ONE randomly placed slice ❌ | complete ✅ |
| consumed by | E0 (`gen_views.py`, `gen_slices.py`) | **P4, P5, P6, P7, `teacher_gen.py`, the LoRA corpus, the E2′ chain gate** |

`build_schedule` is R=5–6 coarse chunks (each ~N/R compressed to V), then `ceil(N/V)` verbatim
tiles. Measured on the E2′ fixture: distinct compression ratios across all 31 passes are
**`[1, 4, 5]`**, and module coverage is a plain sweep — pass 1 covers modules 0–19, pass 2 covers
20–39, … pass 6 covers 104–105, then pass 7 restarts at 0–4 verbatim. **No pass ever sees the
whole document.**

## How deep it goes

`src/pca/teacher_gen.py:136` calls `build_schedule`. So the 277-document teacher corpus, the
5,730 training rows, and the LoRA that produced `runs/stageA_coupled_v2/stageA_v2-f16.gguf` were
all generated against the two-level schedule. The student was *pass-conditioned* on a schedule
with no resolution ladder.

**This explains P1d.** The k/K channel measured inert across k ∈ {5,15,26}, and falsifier F2 was
recorded negative. In the training data, position carried no information beyond "compressed sweep
or verbatim sweep", and the stage rubric already stated which. P1d is a finding about *that
schedule*, not about pass-conditioning. F2's negative verdict is withdrawn as a test of the
conditioning channel.

## When and why it happened

**D25, 2026-06-13**, introduced for P4 (planted facts). The recorded rationale is coverage:
*"Guarantees every turn read at full resolution by the end (so the single-occurrence F7 gets a
verbatim read)."* That is a sound requirement for planted-fact work. The defect is that the
two-phase schedule then became the default for everything downstream — including E2′ — and the
multi-level structure was never restored or re-argued. D5 had flagged the hazard:
*"The production schedule may eventually sweep systematically; if so, E0 must be re-run on that
schedule."*

## What this invalidates

- **The Stage-A "architecture gate" verdict, as a verdict on Context Diffusion.** It remains a
  valid verdict on the two-phase instantiation; it is not evidence about the README's design.
- **P1d / falsifier F2** (see above).
- The gauntlet's kill of the diffusion framing on "k is not a sufficient statistic" — argued
  against a schedule where k indexes almost nothing. Re-argue on the pyramid.
- P1f/P1g cells are scoped to the old schedule's pass-4/pass-26 views, though the *mechanisms*
  they found are within-pass and carry over.

## What survives

Everything that is about demand, edit policy, or within-pass behaviour — i.e. most of the
diagnostic work, all of which would have bitten on the correct schedule too:

- the relation was never demanded (**0/28** archived states record it); `ANSWER:` occurs **0×** in
  5,730 training rows; closing rows sat outside the health gate;
- the length gate silently dropped 52% of verbatim rows; the state budget is prompt text only;
- **table → range binding loss** (standalone scalar 8/11 vs table-row binding 1/11, p≈7.5×10⁻³);
- **salience**: the tile is 94% boilerplate and the policy records it faithfully;
- **grinding**: 26% of Phase-B REPLACEs are byte-identical no-ops, 10% clobber;
- compose is scale-limited (GATE-3 ladder used a frozen seeded state — schedule-independent).

And all infrastructure: edit-ops + strict guard, fixture v2 and its guards, the leakage scanner,
the teacher pipeline, the validated training/serving path, and the analysis and probe tooling.

## The replacement

`src/pca/planted.py::build_pyramid_schedule(turns, V, branching=2)` — added 2026-07-30, unused by
any gate until reviewed. Levels are derived by halving from the verbatim tile count
(`pyramid_levels`), each level tiles the document, each tile renders to V.

Measured on the E2′ fixture (N = 65,781 tok):

| V | passes | compression by level | view tokens | vs source |
|---|---|---|---|---|
| 3000 | 54 | 22.5× → 6.6× → 3.6× → 1.7× → 1.0× | 134,720 | **2.05×** |
| 1300 | 177 | 52.3× → 17.9× → 10.6× → 5.7× → 2.7× → 1.3× → 1.0× | 164,293 | **2.50×** |
| *(current D25)* | 31 | 5× → 4× → 1× | 81,340 | 1.24× |

The pyramid is roughly **2× the view cost** of the two-phase schedule, and the state is re-read at
every one of the extra passes — consistent with the README's own stated tradeoff ("token use and
time per output increases linearly"). State bounding therefore matters *more* under the correct
schedule, not less: state was already 65% of prefill at 31 passes.

**Known rough edge:** `_greedy_tile` packs turns greedily to a byte budget, so a level asking for
2 tiles can yield 4 (level 2 at V=3000 above). The compression ladder is monotone and correct, but
tile counts drift from the ideal 1, 2, 4, 8. A balanced partition (split by cumulative token mass
into exactly n parts) should replace the greedy call before this schedule is used for a gate.

## What has to be regenerated, and what it costs

Already on the plan before this was found — the 07-28 arbitration had ruled *no training until
demand and fixture are repaired and re-measured*, and the ledger notes that rubric-content changes
invalidate archived completions. So:

| item | status |
|---|---|
| teacher trajectories (277 docs, ~6,500 calls) | was **already** being regenerated for the demand repairs; schedule fix rides along |
| the LoRA run | was **already** blocked pending Phase 2 |
| source corpus, fixture, guards, tooling | unaffected |
| frozen-weight probe results | keep as diagnostics, re-scope claims to the old schedule |

The marginal cost of the schedule fix is close to the cost of the regeneration that was already
scheduled. The expensive outcome — a Phase-3 A5000 run on regenerated data against the wrong
schedule — is what finding this now avoids.
