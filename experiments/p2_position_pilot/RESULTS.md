# P2 — Position-token pilot · RESULTS

**Run:** 2026-06-13 · **Config hash:** `d6e22cb7380df28d` · **Parser v2.1** (D22) · local Qwen2.5-7B-Instruct (llama.cpp CPU), temp 0, seed 42 · $0 spend
**Reproduce:** `make p2` (needs the P1 coupled-arm states, also parser v2.1)

## What this is — and is not

The prompt-level **proxy** for the explicit-position signal: identical items run
with a structured `position: {k, K}` field vs no position information. **The
trained explicit-field-vs-trajectory comparison is E1′; this does not measure
it.** Eval items are built from the P1 document (coupled-arm states s_{k-1} +
the staged views v_k) because the V1 PoC eval set was not locatable in Phase-0
(it does not exist in the public parent repo) — the brief's contingency.
6 items × 2 conditions = 12 generations.

## Result (parser v2.1)

| condition | n | mean edit-op validity¹ | position-appropriateness² (n=4 scored) |
|---|---|---|---|
| **with position field** | 6 | 0.979 | 0.75 |
| **no position info** | 6 | 0.983 | 1.00 |

¹ macro: mean over the 6 items of (valid ops / candidate op lines).
² heuristic D20: early (k=1,2) ADD-frac ≥ 0.5 = scaffold-like; late (k=5,6) REPLACE+REMOVE-frac ≥ 0.3 = edit-like; mid excluded.

## Headline: under a correct parser, the position field shows **no** prompt-level effect here

This **overturns the parser-v1 P2 result** (`parser-v1/`, which reported 0.708
vs 0.375 validity). That gap was almost entirely an artifact of parser v1
rejecting the model's id-naming convention (`ADD S3:` to *name* a new entry).
With parser v2.1:

- **Validity is saturated and near-identical** across conditions (0.979 vs
  0.983). Each condition has exactly one sub-1.0 item, both at k=5 and both the
  *same* cause: a final `REPLACE` line truncated by the 700-token generation
  cap (not a malformation, not the naming convention). The position field does
  not change whether a 7B model emits parseable ops — once the naming
  convention is accepted, it almost always does.
- **The appropriateness metric is noise at this n.** It *reversed* direction
  between the v2.0 and v2.1 reruns (v2.0: 0.75 vs 0.50 favoring position; v2.1:
  0.75 vs 1.00 favoring no-position) on the same 4 scored items. With n=4 and
  the only difference a few op-type coin-flips (e.g. the no-position k=1 emitted
  pure ADD = scaffold-like by luck; the with-position k=1 mixed in a REPLACE),
  no direction can be read from it.
- Op-mix detail (`metrics.json`): no condition uses REMOVE meaningfully except
  one with-position pass; both drift ADD→REPLACE as k rises, with or without
  the field.

## Take

**Weak/null go signal — and an honest negative is the result.** At the prompt
level, on one document and a 7B model, an explicit position field buys nothing
measurable once edit-op parsing is fixed; the model already shifts ADD→REPLACE
across passes from the trajectory and view content alone. This is *consistent
with* E0's provisional signal-carrying call only in the weak sense that neither
is a positive prompt-level position effect — and it raises the bar for E1′:
the trained comparison must show the explicit field earning its place, because
the prompt-level proxy does not. P3 tests whether a richer prompt manipulation
(per-pass rubric) moves behavior where the bare field did not. Raw outputs:
`items.jsonl`.
