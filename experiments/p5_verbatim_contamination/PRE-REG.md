# P5 — Verbatim-stage contamination · PRE-REGISTRATION

**Status:** pre-registered before running (this file is committed/pushed before any
arm is scored). Reuses the P4 fixture, schedule, untrained Qwen-7B floor, and
validated component matchers. Param sources: this file + `config.yaml`; D25–D30.

## Question (one mechanism)

When a pass's read is conditioned on the accumulated integration state, does that
prior state **suppress the recording of a task-relevant detail that is present in
the pass's own view**? P4 showed its three misses (F1/F3/F7) were *never recorded*
(`state_entry_pass: null`, `evicted: false`) — available in a view but not written.
The hypothesis under test is that the prior state's framing is part of the cause.

## Design — frozen-state, single-pass, three arms

Everything upstream is **frozen** to the recorded P4 coupled run, so the only thing
that varies is how the target read is conditioned:
- **Frozen prior state** = `coupled_run.json` `snapshots[p-2]` (state after pass p-1) — identical across arms.
- **Frozen view** = pass p's view from the deterministic schedule — identical across arms.
- **Task** = a **recall-framed** task (`config.yaml`), held constant. (P4's strategy-brief task made F7 task-orthogonal — correctly dropped; under a recall task F7 is task-relevant, which is the precondition for the test to detect anything.)

| arm | salience step | edit step | isolates |
|---|---|---|---|
| **A0** baseline | — | state + view + task → edit ops | (reference) |
| **A1** blind-salience | **view + task** → salient list | state + view + task + list → edit ops | — |
| **A2** state-visible (control) | **state + view + task** → salient list | state + view + task + list → edit ops | — |

- **A1 vs A2** isolates **state visibility at the salience step** = the contamination variable.
- **A2 vs A0** isolates the elicitation step itself (so a positive A1 isn't just "an extra planning step makes the model act more"). *A2 is mandatory; without it the result is uninterpretable.*

**Metric:** is the probe fact present in the resulting state (P4 normalized component matcher, full-credit)?

## Frozen probe-selection criterion (fixed before seeing any arm's output)

A (pass p, probe fact) pair qualifies iff: (a) the probe's P4 matcher **fires on pass p's view** (present to read); (b) the probe is **absent from the frozen pre-pass state** (a genuine not-yet-recorded detail); (c) it is **task-relevant under the recall task** (holds by construction for named entities/anecdotes). `run.py` asserts (a) and (b) before running. No planting, no post-hoc probe choice.

## Pre-registered predictions (falsifiable)

- **H1 (contamination real):** A1 records the probe; **A2 (and A0) drop it.** I.e., a read that does its salience judgment *without* the prior state captures the detail; the same read *with* the state visible suppresses it.
- **Elicitation-only (not contamination):** A1 *and* A2 record it, A0 drops → the gain is the planning step, not de-contamination. Reported as such.
- **Integration-stage, not salience-stage:** A1 records at the salience step but the edit step still fails to write it under all conditions → contamination acts at integration, not salience. Informative, pre-stated.
- **Null:** all three arms behave the same (all keep / all drop) → no detectable effect at this pass. A null at a low-saturation pass with a positive at a high-saturation pass would itself support the saturation hypothesis.

## Escalation (fastest-first; "test every option eventually")

1. **F7 @ pass 17** — real documented miss, no planting; most-saturated real probe (23 frozen entries). Run first.
2. **Saturation sweep** — same method at F3@6 (8 entries) and F1@3 (6 entries): does suppression grow with prior-state size? Directly tests the "final pass = most contaminated" intuition without planting.
3. **Final-pass-only with a planted probe** — only if 1–2 are inconclusive; the final tile (turn 390) is a rhetorical wrap-up with no task-relevant specific, so this requires planting a fact meeting criterion (c) above, declared before the run. Weakest on "don't force"; last resort.

## Scope / honesty

n is small — this is a **mechanism-existence probe at a fixed prompt floor**, like P4, not an effect-size estimate; replicate across probes/seeds before claiming generality. **A positive does not establish M1 viability** — it says the floor's salience miss is caused by state-conditioning and is addressable; viability rides on the trained student (E2′). A negative does not refute coupling. Same untrained Qwen-7B floor and $0 local inference as the P-series.
