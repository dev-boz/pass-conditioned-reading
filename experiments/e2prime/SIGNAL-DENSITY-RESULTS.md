# P1i — the signal-density ladder (2026-08-06)

**Status:** probe, exploratory, `gate_legal=false`, frozen weights, $0. Design and readings were
committed BEFORE the first draw (commit `58a59ee`); the fresh-seed replication was run before any
result was written up. Instrument: `stagea_p1_probes.py --probe p1i`. Artifacts:
`runs/stageA_chain_gate/_probe_p1/p1i_student_s01-10.json` (seeds 1-10) and
`.../p1i_student_s21-30.json` (seeds 21-30, never previously used by any arm), plus
`runs/p1i.log`, `runs/p1i_b2.log`. Every mapping hit reported below was hand-read untruncated.

## The question

HANDOFF-2026-08-05 next-step #1. The decisive tiles in the archived chains were 5.8-10.9% signal
and recording ran 1-3/10; HOME-AVAILABILITY §6 located the mechanism in edit-budget competition.
Is the **filler ratio** the binding constraint on RECORD — and if so, what signal share does the
Phase-2 fixture rebuild have to deliver?

## Construction

The queried-table section of the real pass-12 tile (263 tok, verbatim,
`pricing/region_tables.py` with `23: 988` as one row of 24) is **byte-identical in every cell**;
only the surrounding material changes. Filler is cut at top-level function boundaries. The pinned
state is `s25` in every cell (the p1a/p1d construction) — it holds **no entry for any module in
this tile**, so every recording is self-initiated (ADD, or REPLACE that repurposes an unrelated
entry). Verbatim rubric, honest position k=12/31, student only, temp 0.7, strict guard.

| cell | view tok | signal | what surrounds the table |
|---|---|---|---|
| `d10_base` | 2,623 | 10.0% | the real tile untouched — three boilerplate modules |
| `d30` | 741 | 35.5% | two boilerplate modules trimmed to a few functions |
| `d60` | 396 | 66.4% | one boilerplate module trimmed to one function |
| `d90` | 285 | 92.3% | a single module-header stub |
| `pad10_prose` | 2,694 | 9.8% | digit-free prose padding to the base length (docstring-only notes module) — the kind-of-filler control |

## The result

Applied `queried_mapping` (paraphrase-robust matcher, the audited one):

| cell | signal | seeds 1-10 | seeds 21-30 | **pooled /20** |
|---|---|---|---|---|
| `d10_base` | 10.0% | 1/10 | 0/10 | **1/20** |
| `d30` | 35.5% | 1/10 | 6/10 | **7/20** |
| `d60` | 66.4% | 2/10 | 6/10 | **8/20** |
| `d90` | 92.3% | 5/10 | 4/10 | **9/20** |
| `pad10_prose` | 9.8% | 1/10 | 3/10 | **4/20** |

- **Trend across the four rungs: permutation p = 0.0046** (one-sided, dose x success statistic,
  100k shuffles, pooled n=80).
- Endpoints, two-sided Fisher, pooled: d90 vs d10_base **p = 0.0084**; d60 vs d10 **p = 0.0197**;
  d30 vs d10 **p = 0.0436**.
- **The rungs above 35% do not separate from each other** (d90 vs d30 p = 0.75, d90 vs d60
  p = 1.00). The step is at the bottom of the ladder, not the top.
- Block variance is real: d30 ran 1/10 then 6/10. Temp 0.7, n=10 blocks — quote the pooled row,
  carry the spread.

**Reading `density_is_the_constraint`: FIRES.** Lifting the signal share from 10% to ~35% moves
recording from 1/20 to 7/20; further densification to 92% buys ~2 more draws in 20. And recording
never clears ~half: **composition fixes the bottom of the ladder, and something else owns the
ceiling** (below).

**The kind-of-filler discriminator did not resolve.** `pad10_prose` (4/20) sits between the poles
— not distinguishable from d10_base (p = 0.34) or from d90 (p = 0.18) at these n. The ordering
d10 (1) ≤ pad10 (4) << d30+ (7-9) is a directional hint that code-boilerplate filler suppresses
harder than inert prose at equal dilution, i.e. some of the effect is matchable-content
competition and not dilution alone. Direction only; neither pre-registered discriminator reading
is claimed.

## Where the edit budget went (pooled, 20 draws per cell)

| cell | applied ops | byte-identical no-op REPLACEs | blocked |
|---|---|---|---|
| `d10_base` | 139 | 93 (67%) | 19 |
| `d30` | 119 | 46 | 7 |
| `d60` | 64 | 30 | 11 |
| `d90` | 66 | 35 | 10 |
| `pad10_prose` | 240 | 128 (53%) | 18 |

Dilution does not merely hide the table — **it feeds the grinder**. The two long-view cells emit
2-4x the ops of the dense cells, and half to two-thirds are byte-identical rewrites. With no home
for anything in the view, misses put **zero** REPLACEs into entries about the view's modules
(0 of 36 at d10, 0 of 99 at pad10): the policy grinds the *state* when the view offers nothing to
match — filler kind changes what gets ground, not whether grinding happens.

## Mechanism notes (hand-read)

- **Recording route:** with no home available, hits arrive as fresh `ADD` entries (most) or by
  **repurposing** an unrelated helper-list entry (d60 seed 3/8, d90 seed 2/10 of block A) — the
  D31 slot-repurposing pathology, here working in the fact's favour.
- **Most hits transcribe the full 24-row table**; one truncated at 13 rows; one recorded it
  twice; one arrived in arrow form (`23→988`) — caught only because the matcher is
  paraphrase-robust (the 08-05 instrument fix earning its keep).
- **Misattribution rides along:** two hits gloss the table under the *stub's* module name
  (`GROUP 21 (audit/node21.py): surcharge_cents...`). The binding survives; the provenance is
  wrong. Same family as the archived `S2: 1365` misbinding.
- **d90 miss modes, all five hand-read (block A):** grinding loops (13-14 byte-identical
  REPLACEs of S1 — seeds 4, 6) and **name-or-range-without-rows** (seeds 5, 7, 8 record
  `REGION_SURCHARGE_CENTS` or `values 161-988 cents` with no rows). Even a 92%-signal view does
  not force row-level extraction.
- **Zero fabrication** across all 100 draws (no `1365`, no `compute_line_surcharge` anywhere);
  guard losses negligible (emitted ≈ applied in every cell).

## What this gives the fixture rebuild — the requirement, as numbers

1. **Distinctive-content share of a decisive view: at least ~one-third.** 10% → ~35% signal is
   where the recording step lives (1/20 → 7/20). Past ~35% the returns are shallow (7→8→9 of 20).
   Combined with the 08-05 constraint (distinctive content must exceed one view budget V so the
   pyramid's top level cannot answer everything), the Phase-2 fixture spec is now:
   **total distinctive content > V, and ≥ ~35% distinctive share within each decisive tile.**
   Run `author_pyramid_views.py --budget-audit` against both before authoring.
2. **Composition buys at most half.** At 92% signal, recording is 9/20; the misses are the
   policy's own modes — grinding and name-without-rows — which no fixture composition removes.
   That residue is the training/demand side (consistent with the prompt column running 0-for-5
   and only structural interventions moving anything).

## Caveats

One tile, one state (no homes — real mid-run states sometimes have them, which would open the
REPLACE-into-home route this probe deliberately lacks). The signal section is always the same 263
tokens, so signal *content* and signal *share* are not varied independently. The queried row sits
5th of 24 in the table; a tail row would test transcription truncation, observed once here.
Block-to-block spread at the 35% rung is the widest (1/10 vs 6/10). n=20 per cell, temp 0.7,
probe conventions throughout — nothing here pools with any gate.
