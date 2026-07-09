# 14B context overflow at the pre-registered ctx=16384 (finding "C")

**Status: surfaced for review, not a published conclusion.** Recorded 2026-06-21.

## Finding
At the pre-registered context window (`ctx=16384`), the **14B's integration state self-overflows
the context mid-run**, aborting the specifics state-arms before they finish. The 7B never hit this
(it stays terse). This is a capacity×architecture signal in its own right, independent of the
record/retain/compose scores.

## Evidence (first 14B matrix run, ngl=36, n=10)
- All **8/8 completed specifics seeds** produced result files containing **only the `dense` arm** —
  `verbatim_only` and `coupled_full` were missing.
- `verbatim_only` crashed at **pass ~18/25** with state ≈ **12,336 tokens**: the server returned
  **HTTP 400** (`/v1/chat/completions`) because prompt (state ~13k + a ≤3k source tile + system +
  900-token output budget) exceeded 16,384. The unhandled error killed `run.py` **before
  `coupled_full` ran** → no headline arm for any 14B seed.
- 8 identical tracebacks = the 8 seeds, all dying the same way. The **7B log had zero 400s**
  (its state stayed ~3k tokens; gen=1–5 ops/pass late vs the 14B's gen=22–26).
- Mechanism: the 14B is verbose — state grows ~**750 tokens/pass** — so the unbounded-state design
  crosses a fixed 16k budget around pass ~18.

## Interpretation (C, tentative)
A more capable model builds a **richer state that the unbounded-state architecture cannot hold**
within a fixed context budget. "Records more" does not imply "retains usefully" when the state
self-overflows. This is consistent with the **architecture-limited** reading (clobber-safe /
bounded-state edit ops are necessary), as distinct from a pure capacity ceiling.

## Remediation runs (both, to maximize data)
- **B — matched context.** Keep `ctx=16384` (parity with the 7B) and **truncate gracefully** at
  overflow: close on the state built so far. Measures *where it breaks + what it recorded by then*.
  Result tag `14b_*`.
- **A — more output room, same input limit.** Raise `n_ctx` so the accumulating **state (the model's
  output/working memory)** has room, while **keeping the source-input limited** (`V=3000`,
  `dense fill=14000`, `R`, `op_cap` unchanged) — so the experimental point (model sees the source
  only through partial views) is preserved. Result tag `14bx_*`.

## Harness change (infra only, not the experiment)
`run.py` `run_state_arm` / `closing_answer` now catch `requests.exceptions.HTTPError` and truncate
instead of crashing; results carry `truncated`, `truncated_at_pass`, `truncated_http`,
`n_passes_run`. Prompts, compressor, scaffold, `op_cap`, and draws are unchanged.
