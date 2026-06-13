# P2 — Position-token pilot · RESULTS

**Run:** 2026-06-12 · **Config hash:** `d6e22cb7380df28d` · local Qwen2.5-7B-Instruct (llama.cpp CPU), temp 0, seed 42 · $0 spend
**Reproduce:** `make p2` (needs the P1 coupled-arm states)

## What this is — and is not

**This is the prompt-level proxy for the explicit-position signal.** Identical
eval items run twice — once with a structured `position: {k: n, K: 6}` field in
the prompt, once with no position information at all. **The trained
explicit-field-vs-trajectory comparison is E1′, and this experiment does not
measure it.** Nothing here licenses an M2 claim; this is the cheap go/no-go
signal the brief asked for.

**Eval-set provenance:** the V1 PoC eval set was not locatable in Phase-0
inventory (it does not exist in the public parent repo), so per the brief's
contingency the items are built from the P1 document: for each k ∈ 1..6, state
s_{k-1} comes from the P1 coupled-arm snapshots and the view is the same
staged view v_k. 6 items × 2 conditions = 12 generations.

## Result

| condition | n | mean edit-op validity | position-appropriateness (heuristic D20, n=4 scored) |
|---|---|---|---|
| **with position field** | 6 | **0.708** | 0.50 |
| **no position info** | 6 | **0.375** | 0.25 |

Direction favors the explicit position field on both measures. **Treat as a
weak go signal, not a finding**: one document, one model, six items per
condition, and the appropriateness heuristic scored on four items.

## What actually drove the gap

- The dominant malformation in *both* conditions is the **sequential-ADD-anchor
  error**: the model anchors `ADD S5:` to ids its own earlier ADD lines would
  create, which the parser correctly rejects (ids are assigned by the harness;
  D15). Every zero-valid-op item in the run is this failure, not refusal or prose.
- At k=1 (empty state) both conditions fail identically this way. The
  conditions separate at k=2–5, where the no-position outputs kept anchoring
  invalidly while the with-position outputs more often used existing ids.
- Op-mix detail (`metrics.json`): no REMOVE ops anywhere in the run;
  `NO_CHANGE` appeared only in the with-position condition (k=4) — the only
  observed instance of mid-schedule restraint.
- The late-pass appropriateness criterion (REPLACE/REMOVE ≥ 0.3 at k≥5) failed
  in the with-position condition at k=5 (its single op was an ADD) — the
  position field did not by itself induce edit-like late behavior.

## Relation to the program

Consistent with E0's provisional **signal-carrying** call (position is not
recoverable from these views, so supplying it ought to help) — but both
results share the stand-in-compressor caveat and P2's tiny n. E1′ remains the
arbiter. Raw outputs: `items.jsonl`.
