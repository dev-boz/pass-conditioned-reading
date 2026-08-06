# Pre-registration — confirming run, 2026-08-02

Written and committed to BEFORE the run. Seeds 11-20 have never been used by any arm in this
program; every result so far is on seeds 1-10. This is the hardening pass on the stack that the
2026-08-02 exploration fitted.

## What is being confirmed

The fitted stack, unchanged:

- schedule: pyramid (V=3000, branching 2, 63 passes, stage by level)
- views: `llm_roleaware` (frozen, already generated — NOT regenerated for this run)
- guard: `retain` (REPLACE may not drop numeric literals the target entry held)
- model: the Stage-A student (1.5B), frozen weights
- reader for the closing turn: student (1.5B) and Qwen2.5-3B, temp 0

Exploratory result being tested (seeds 1-10): c1 = 3/10 states held both operands; readers >=3B
composed 2353 on 3/3 of those; the 1.5B on 0/3.

## Predictions, stated in advance

- **P1 (primary):** c1 >= 2/10 on seeds 11-20 — at least two final states hold both operands.
- **P2 (primary):** on the c1 draws, Qwen2.5-3B composes 2353 on **all** of them.
- **P3:** the 1.5B student composes 2353 on **none** of them.
- **P4:** zero losses — no draw records the binding and then loses it, as on seeds 1-10 (0 losses
  under `retain` vs 2 of 3 without it).

## What counts as a failure

- P1 fails if c1 <= 1/10. That would make the seeds 1-10 c1=3/10 look like a favourable draw.
- P2 fails if the 3B misses any c1 draw. That would break "the state is exactly sufficient".
- P4 fails if any draw loses a recorded binding. That would break the retain-guard mechanism claim.

P3 failing (the 1.5B succeeding) would be good news and would weaken the recorder/reader split
claim; it is recorded as a prediction so it cannot be reinterpreted afterwards.

## Scoring

`analyze_chain_gate.rescore` (paraphrase-robust) for all state flags, NOT the pre-2026-08-02
colon-only live matcher. Every candidate hand-verified before being reported, per the addendum.

## Standing caveats, unchanged by any outcome

One fixture, whose distinctive content is 1,806 tok (60% of one view budget). No dense-read
comparison. The k/K conditioning channel measured inert twice and is not part of this claim: what is
being confirmed is coverage + retention + binding-preserving compression, not pass-conditioning.
`gate_legal=false` — this is not the addendum's frozen D25 protocol and is never poolable with the
Stage-A verdict.

## Provenance addendum — 2026-08-06, added at commit time

"Committed to" in the header meant the predictions were fixed, not a git commit: this file was not
committed until 2026-08-06, four days after the run. The ordering evidence is therefore filesystem
timestamps, not git history: last write 2026-08-02 14:22 +1000; the confirm run directory
(`runs/stageA_chain_gate_pyramid/CONFIRM_roleaware_retain/`) created 16:51 and its log
(`runs/confirm_roleaware_retain.log`) last written 17:16 the same afternoon. Those timestamps
support the written-before-run claim, but they are weaker evidence than a pushed commit, and this
note exists so the gap is on the record rather than papered over. Standing rule from this date: a
pre-registration counts only once committed **and pushed** before the run it registers.
