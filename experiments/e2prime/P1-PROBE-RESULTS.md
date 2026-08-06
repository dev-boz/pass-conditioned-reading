# P1 probe battery — results (2026-07-28)

> **SUPERSEDED IN PART, 2026-07-29.** The synthesis below ("home availability is the recording
> variable") is too simple and is corrected in `HOME-AVAILABILITY-RESULTS.md` §6. The operative
> variable is home availability **with competing matchable content absent** — the `ctrl8` oracle
> state fills well because its other entries are inert, not because it has homes. When the model
> fills a scaffold it built itself, which necessarily covers every module, acquisition is **0/10**
> despite 8/10 dedicated homes. Also corrected there: the ctrl8 adder rate is ~5–9/10 across seed
> blocks, not 9/10 (fresh-seed confirm 5/10). The relation 4/10 result **replicated** at seeds
> 11–20 (3/10, p=1.00), discharging reading 4 below.

**Status:** probes, `gate_legal:false`, frozen weights, $0. Runner: `stagea_p1_probes.py`
(dual proposed/applied scoring; every op-level metric reports *emitted* — what the model wrote —
and *applied* — what the strict guard let into the state). Artifacts:
`runs/stageA_chain_gate/_probe_p1/`. Draws: seeds 1–10, temp 0.7, max_tokens 900, 24-op cap,
pass-26 tile (the only view holding `def compute_line_surcharge`), K=31 label unless varied.
All Fisher values two-sided. Hand-reads performed on every load-bearing cell before this
write-up; quoted verbatim below.

## P1a — suppression discriminator ({empty, 25-entry own-state prefix, token-matched padding} × {trained verbatim rubric, +ADD-license})

Student (trained 1.5B), n=10 per cell, relation/fn/adder:

| cell | emitted | applied |
|---|---|---|
| empty × current | **5/10** / 10/10 / 5/10 | 0/10 / 0/10 / 0/10 (all ops malformed REPLACEs) |
| empty × ADD-license | 6/10 / 10/10 / 5/10 | **1/10 / 1/10 / 1/10** |
| 25 own entries × current | 0/10 / 2/10 / 0/10 | 0/10 / 2/10 / 0/10 |
| 25 own entries × ADD-license | 0/10 / 1/10 / 1/10 | **0/10** / 0/10 / 0/10 |
| 25 padding × current | 0/10 / 0/10 / 1/10 | 0/10 / 0/10 / 1/10 |

Untrained 3B (same cells): applied ≈ 0 everywhere **including empty** — its draws are mostly a
single well-formed REPLACE aimed at a **nonexistent id** (hand-read, seed 5: `REPLACE S135 …`
against a 25-entry state; S135 exists only in the full 155-entry battery state). The 3B reads
the view (it names the tile's actual functions) but cannot drive the op format cold from a
pass-26 drop-in. **Per the P7 reading rule its zeros are protocol transfer, not suppression
evidence — the training-artifact leg is formally undiscriminated by this arm.**

Readings:

1. **ADD-license does NOT restore recording over a populated state** (0/10 emitted and applied
   at 25 entries, unchanged from baseline). The rubric-effect explanation, as a one-sentence
   prompt fix, is dead.
2. The license **does** unlock applied recording at empty state (1/10 full relation through the
   strict guard — hand-read, seed 3: `S2: compute_line_surcharge(region_code) = base
   (REGION_SURCHARGE_CENTS[region_code]) + RECONCILIATION_ADDER_CENTS`). Where REPLACE is
   impossible, the licensed ADD fires; where entries exist, the REPLACE policy outcompetes it.
3. **Padding suppresses like the real state** (0/10 relation) and the model grinds it — up to
   23 valid REPLACEs rewriting digit-free filler it has never seen. Suppression is not about
   the state's content, schema (07-26 control), or meaning.

## P1b — typed-slot fill probe + controls (student; oracle states, declared)

| cell (n=10) | applied relation | applied adder (1365 arrives) | fabricated mapping |
|---|---|---|---|
| 8 entries, typed `[TBD:]` slots | **4/10** | **8/10** | 0/10 |
| 8 entries, same mentions, **no slots** | **4/10** | **9/10** | 0/10 |
| 8 padding entries (size control) | 0/10 | 1/10 | 0/10 |

- ctrl8 adder 9/10 vs 25-own-entries 0/10: p≈1.2×10⁻⁴. vs size-matched padding 1/10:
  p≈1.1×10⁻³. Relation 4/10 vs 0/10: p≈0.09 (suggestive, not decisive at n=10).
- Hand-read (slots seed 2): the model still REPLACEs **all eight** entries — the
  grind-everything bias persists — but the rewrites *carry the view's values into the matching
  entries* (`S2: RECONCILIATION_ADDER_CENTS = 1365`). Zero table-value fabrication in 30
  slot/ctrl draws; the unfillable table slot stays `[TBD]`.
- **The slot syntax is not load-bearing — the semantic home is.** An entry that merely *names*
  the module/identifier receives the value as reliably as a typed empty slot.

## P1d — k-conditioning (student; k ∈ {5, 15, 26}, rubric/state/view fixed)

Behaviour is flat across k: relation 0/10 everywhere, fn 0–2/10, placeholders 0, op profiles
indistinguishable. **The position channel does no measurable conditioning work on the trained
student** — falsifier F2 for the constructed-pairs lever returns negative for the *current*
channel. What training conditioned on position was evidently the rubric text, not the
`position: {k, K}` line.

## The synthesis — the suppression effect has a mechanical form

Across all fourteen cells the applied-recording rates sort on exactly one variable: **whether
the state offers an entry that semantically matches the view content**.

| state offers | applied recording |
|---|---|
| nothing (empty) | 0 — ops illegal (REPLACE against nothing); ADD-license leaks 1/10 |
| entries, none matching (25 own prefix, padding at 8 or 25) | ~0 — the model grinds what exists |
| **matching entries** (8-entry oracle states, slot or no slot) | **adder 8–9/10, relation 4/10** |
| matching entry buried among 155 | 2/10 (the 07-26 crowding tail; S83 existed but lost to competition) |

The trained recording policy is **REPLACE-into-the-semantically-matching-entry** — precisely
what both operative rubrics say ("into the entries it belongs to / they belong to"). With a
matching target the values land through the strict guard at high rate, *relation included*;
without one, recording is zero regardless of state size, shape, or an explicit ADD license.
The 07-26 step (0→25) reframes: the 25-entry prefix happened to contain no entry about the
tile's modules; the 155-entry state contained a buried one and showed the 2/10 tail.

**Consequences for the lever board:**

- **Lever 10 (native architecture) loses its new pillar before gaining it.** The structural
  reading — "a flat text state suppresses ingestion per se" — is refuted: the flat state
  supports guard-clean relation recording at 4/10 when a home exists. What remains for lever 10
  is the close-side retrieval argument only.
- **Lever 5 reframes from "typed slots" to "home-building."** The scaffold's real job is to
  have created a value-shaped, module-keyed entry *before* the verbatim pass arrives. Typed
  slots are one way; a name-mention entry is enough. This is cheaper than a slot grammar and
  dodges the quote-matching-on-fill and slot-typing failure modes the gauntlet predicted.
- **The demand repairs stand** (relation-demanding rubric, multi-exposure) — a home for the
  *relation* still has to be induced, and one exposure under 20-module competition produced
  only the 2/10 tail even with a home present.
- **The non-oracle question is now precise:** can Phase-A scaffold passes be made to build
  matching homes for later tiles *without* oracle help? That is the guided-reading training
  target, and it is measurable on the existing archives (how often did the student's own
  scaffold create a home the later tile could land in?).
- **P1c (enforced budget) not yet run** — needs an `--enforce-budget` arm in the chain-gate
  runner; still worth running, but the home-availability mechanism predicts its effect will be
  indirect (smaller state ⇒ fewer competing non-homes).

## P1e — explained-protocol probe (maintainer hypothesis, run 2026-07-28)

Hypothesis: "the training almost just needs to be a prompt — if the model knew the architecture
and its position it could almost do it on its own, or at least a larger model should." Cells:
H1 home-leaving (Phase-A view k=2, empty state), H2 fill (pass-26 tile vs ctrl8 homes / empty);
trained terse rubric vs an architecture-explaining prompt; student / untrained 3B f16 /
untrained 7B Q4. n=10 per cell.

| model × cell | homes built (mean module-keyed entries) | applied adder fill | applied relation |
|---|---|---|---|
| 7B h1 trained-rubric | **20.0** (one per module — textbook; includes a pricing-table home) | — | — |
| 7B h1 explained | 19.5 | — | — |
| 3B h1 trained-rubric | 4.0 | — | — |
| 3B h1 explained | **0.0** (keyless fragments: "defines helpers: sample_ledger", no module) | — | — |
| student h1 trained / explained | 4.5 / 1.8 | — | — |
| 7B h2 homes, trained-rubric | — | **6/10 — but binding-destroying** | 0/10 |
| 7B h2 homes, explained | — | 2/10 | 0/10 |
| 3B h2 homes (either prompt) | (explained: ADDs ~4.5 new homes at pass 26 instead of filling) | 0/10 | 0/10 |
| student h2 homes, trained | — | 9/10, binding preserved | 4/10 |
| student h2 homes, explained | — | 5/10 | 5/10 |

Hand-reads (verbatim):

- 7B scaffold, seed 1: `S1: module: carrier/cursor20.py defines helpers: tokenize_record, …` —
  twenty such lines, one per module, from the compressed Phase-A view, under the ORDINARY
  trained scaffold rubric. The untrained 7B home-builds without any special explanation.
- 7B fill, seed 2: `REPLACE S2 "RECONCILIATION_ADDER_CENTS": 1365` sprayed at every entry
  (guard blocked the non-matching ones). The one that landed left **`S2: 1365`** — the value
  arrived and the *name was destroyed*. Fill-without-binding: the entry no longer says what
  1365 is. The trained student's fills read `RECONCILIATION_ADDER_CENTS = 1365`.
- 3B h1 explained, seed 1: eight valid ADDs, every one a keyless helper-name fragment. Not
  format collapse — content degeneration under the longer prompt.

**Readings:**

1. **Structure is prompt-elicitable and scale-graded; the explanation is not the unlock.** The
   terse trained rubric already elicits a full per-module scaffold from the untrained 7B; the
   long explanation helps nobody and actively hurts the 3B (4.0 → 0.0 homes) and the student
   (whose LoRA is specialized to its trained prompt shape).
2. **What training actually bought is edit discipline, not strategy.** Untrained 7B fills 6/10
   destructively; the trained 1.5B fills 9/10 preserving the name=value binding. And
   **relation-recording remains training-only**: 0/10 in every untrained cell at any scale here,
   vs the student's 4–5/10.
3. **The inverse of GATE-3.** The 7B composes a seeded relation 10/10 but never *writes* one;
   the student writes one 4/10 but composes 1/10. Reading and writing the relation dissociate
   across scale in opposite directions.
4. student × h2homes × trained-rubric uses the same seeds/prompt/state as P1b's ctrl8 cell, so
   its identical 4/10 & 9/10 is a **determinism check, not a replication** — the fresh-seed
   (11–20) confirming run is still owed under the three-tier rule.
5. The 7B drove the op format cleanly here (Q4 caveat did not bite in this regime).

**Next $0 cells this licenses:** (a) own-scaffold fill — feed the 7B's H1 state back as the H2
state: does it fill its *own* homes, untrained? (b) the archive scan (non-oracle home
availability across the 22 battery draws); (c) the fresh-seed confirming run for the student's
relation-fill.

## Caveats

- All P1b/ctrl states are **oracle** (hand-written homes naming fixture identifiers): legal,
  declared, design-input only, never poolable. The 3B/floor arms cannot drive the op format
  cold, so "trained policy vs innate" is still not fully discriminated — but the mechanism's
  shape (it matches the rubric wording; the model maintains even meaningless filler) points at
  the learned policy.
- Emitted-side fn/relation in P1b-style cells is partially seed-contaminated (the state itself
  names the fn); only *value arrivals* (1365, the composed relation line) and fabrication
  (mapping) are clean applied metrics there.
- n=10 per cell; the relation-fill 4/10 needs its confirming run under the three-tier anomaly
  rule before anything graduates.
