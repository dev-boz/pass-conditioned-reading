# P7 — Split-Unit (code domain) · PRE-REGISTRATION

**Status:** pre-registered; gated. Fixture + structure-preserving compressor + pre-run gates are
surfaced here for maintainer review **before any battery run** ($0 / nothing published until
approved). Reframed from the brief's eviction framing with maintainer approval (2026-06-19); see
§1. Reuses `src/pca/` (schedule, edit-op state, llama server) + a **new** code-structure-preserving
compressor (`compress_code.py`) and a **new** code fixture (`fixture/`).

---

## 1. The reframe (why this is NOT the brief's eviction test)

The brief frames P7 as an **eviction** test: *"verbatim_only's bounded state has lost the first
fragment by the time the second arrives."* Our own prior data says that mechanism does not occur on
this floor:

- **P4:** all 8 facts `evicted: false` — recorded facts were kept; missed facts were *never
  recorded* (`state_entry_pass: null`). **Zero record-then-evict.**
- **P6:** across 4 draws, **one** record-then-evict event total (coupled lost a *control*); every
  other recorded detail persisted to the final state. (Scan: `ever_present ∧ ¬final_present`.)
- P6's own PRE-REG abandoned the eviction headline as **"predicted-null by our P4/P5 data."**

Betting P7 on eviction would re-run a predicted-null at ~26 h of compute — the P6-shaped waste this
program exists to avoid. **Reframe (approved):** P7 bets on **differential recording**, not
eviction. The split unit's fragment-1 is an **arbitrary lookup table** — bulk reference data that
is meaningless until queried. The claim:

> A **structure-preserving coarse pass** lets the model carry the table's skeleton (it records the
> table from the clean Phase-A view); a verbatim reader that meets the *same* table only as a raw
> int-wall embedded in a code tile, under a broad "build a brief" rubric, **discards it as noise and
> never records it.** When the late call site asks for a value from that table, `coupled_full` can
> reassemble the answer and `verbatim_only` cannot — not because it evicted the table, but because it
> never recorded it, while coupled did via the coarse structure-preserving pass.

This dodges all three prior nulls: P4's "no eviction" (we don't need eviction), P6's "recording is
arm-independent" (there, both arms read the dull clause under the *same* verbatim rubric in the
*same* Phase-B tile; here the asymmetry is the **compressor** — only coupled sees the table as
preserved structure), and the eviction predicted-null. The structure-preserving code compressor is,
per the brief, *"the code-specific lever and the reason code is the cleanest domain."*

## 2. The claim under test (precise)

A semantic code unit (a lookup whose value lives in an arbitrary table) is split across two
far-apart verbatim slices. `verbatim_only` accumulates state over the verbatim sweep but (per §1)
does not carry the arbitrary table to answer time. `coupled_full`, holding the structure-preserving
Phase-A view that preserves the table, does. **Money comparison = `coupled_full` vs `verbatim_only`**
(NOT vs dense). The mechanism must be visible: the table skeleton enters coupled's state in
**Phase-A** (the "State-D" guard), and verbatim_only lacks the table at answer time.

**Bar (per the brief):** a "might-work, not won't-work" probe on an untrained 7B floor + consumer
hardware. One clean signal (coupled answers where verbatim cannot, with the mechanism visible) is
sufficient; a floor-limited null is also informative (carry to E2′). Both publishable, neither a
tie — *iff* the fixture defeats backfill (it does; §5 GATE 1).

## 3. Fixture (`fixture/`, deterministic, seed 70707)

- **Host document:** a 100-block / **64,671-token** realistic Python codebase-as-document
  (shipping/billing service: validation, routing, billing, carrier, audit, … modules of varied
  templated functions). `host_doc.jsonl` = one block per "turn" (the schedule atom); generator
  `fixture/gen_fixture.py`; spec + computed ground truth `fixture/fixture_spec.json`.
- **The unguessable split unit** (arbitrary RNG lookup table — non-inferable from either fragment):
  - **fragment-1** (block 21, ~22% — mid-exclusive, locally mundane `pricing/region_tables.py`):
    `REGION_SURCHARGE_CENTS = { …, 23: 988, … }` — 24 entries, 3-digit RNG values, no pattern; the
    module docstring explicitly says the values are arbitrary ops-review settings, "not derived from
    distance or zone."
  - **fragment-2** (block 74, ~75% — mid-exclusive `fulfillment/line_quote.py`):
    `RECONCILIATION_ADDER_CENTS = 1365` + `def compute_line_surcharge(region_code): return
    REGION_SURCHARGE_CENTS[region_code] + RECONCILIATION_ADDER_CENTS`. Uses the table but restates
    no table value.
  - **Scoring question (asked ONLY at the end):** *"what integer does `compute_line_surcharge(23)`
    return?"* **Ground truth = 988 + 1365 = 2353** (computed; exact-int match, no LLM judge).
  - **Why neither fragment alone wins:** the table lacks the +adder and *which* code is asked; the
    call site lacks the table value. Both halves required → genuine reassembly; backfill-defended.

## 4. Method

- **Structure-preserving Phase-A compressor** (`compress_code.py`, deterministic, $0): keeps
  module-level constants / lookup-table literals / imports / docstrings / comment headers and
  def/class **signatures**; **drops function bodies**. Compresses ~7× (12.9K→1.8K tok/chunk, under
  V=3000) while keeping the table verbatim. Frozen to a JSON scaffold (P6 `gen_scaffold.py`
  pattern) so every draw reuses identical Phase-A views and the guards stay meaningful. Replaces the
  prose summarizers in `src/pca/compressor.py`, which force "plain prose, no bullet points" and would
  drop an int table (the maintainer's "customise compression to guarantee valid tests").
- **Schedule:** P4/P6 `build_schedule`, V=3000, R=5 → **6 Phase-A chunks + 25 Phase-B verbatim
  tiles.** Phase-A view_text overridden with the frozen structure-preserving scaffold (P6 pattern);
  every Phase-B tile read under the same "verbatim" rubric across arms (only the Phase-A pass
  differs).
- **Arms:**

  | arm | sees | role |
  |---|---|---|
  | dense | head+tail verbatim (~14K) | floor; both fragments are mid-exclusive → structurally misses (table stakes) |
  | **verbatim_only** | Phase-B verbatim tiles only, accumulating state, NO coarse pass | the baseline: meets the table only as raw embedded code |
  | **coupled_full** | structure-preserving Phase-A + Phase-B tiles | the claim: coarse pass preserves the table skeleton |

- **Query-leak resolution (the brief's make-or-break, lesson #2):** the standing task during
  state-building is **broad** ("build a comprehensive analytical brief of this codebase's structure
  and behaviour") and never names region 23 / surcharge. The scoring question is asked **only in a
  closing call, answered from the final integration state with NO source re-read.** So when
  verbatim_only reads the table early, nothing flags key 23 as must-retain.
- **Replication:** deterministic temp-0 (seed 42, canonical/P1–P5-comparable) + **≥3 sampled
  temp-0.7 seeds**, reported per-seed (never pooled across decode distributions). Recording &
  backfill are stochastic; repetition separates luck from mechanism.
- **Observability (lesson #4/#5):** save raw ops every pass; per-pass record whether the table
  (queried entry / value count) is present in `s_k`, first-appearance, and presence-at-answer-time,
  in BOTH state arms. Distinguishes "never recorded" from "recorded-then-evicted."

## 5. Pre-run gates (model-free guards + two empirical model gates — ALL before the battery)

- **Realized-view guards** (`verify_fixture.py`, **PASS**): (A) the queried entry `23: 988` + the
  adder fire on source; (B) neither fragment's discriminating values appear in the dense head+tail
  window (dense is a true floor); (C1) the table entry survives into the realized Phase-A view
  (coupled *can* record it from Phase-A — chunk 1) and the adder survives (chunk 3); (C2) no single
  Phase-B tile holds both fragments (fragment-1 in tile 5, fragment-2 in tile 18, gap 13 — split is
  real).
- **GATE 1 — backfill defense** (`backfill_check.py`, **PASS**): a fresh model given ONLY fragment-2
  + the question emitted the ground truth in **0/4** draws (temp-0 + 3×temp-0.7): it answered
  "INSUFFICIENT" (3/4) or gave no integer (1/4), never 2353 nor 988. The unit is genuinely
  unguessable. `backfill_check_result.json`.
- **GATE 2 — differential recording** (`recording_gate.py`, the discriminator), **PASS (differential
  ALIVE)**: cold single-pass recording of the table from (a) the raw Phase-B tile (verbatim_only's
  exposure) vs (b) the structure-preserving Phase-A view (coupled's exposure), under the identical
  broad task + verbatim rubric, temp-0 + 2×temp-0.7. Scored by the **usable mapping** (`23: 988`
  key→value adjacency) and confirmed by manual state read:
  - `verbatim_only` (raw tile) preserved the usable mapping in **0/3** draws — it abstracted the
    int-wall to "specific values for different region codes" (s42), "values like 314, 804, 883" (s2,
    first 3 only), or dumped keys and values as two **parallel lists** that lose the binding (s1).
    Even when given a rubric explicitly asking for "lookup-table contents," the floor discards the
    arbitrary table from raw embedded code.
  - `coupled_full` (structure-preserving Phase-A view) preserved the full table incl `23: 988` in
    **2/3** draws (incl. the canonical temp-0); it abstracted once under sampling (s1) — the
    floor-limited risk that motivates replication.
  - **Scoring correction (manual-read finding):** the `values_present`/`queried_present` bare-integer
    substring metrics are **unreliable** (3-digit values collide with filler constants; a
    parallel-list dump shows `988` without binding it to 23). The battery scores the **mapping**
    (`23: 988` adjacency) and ultimately the **closing-call answer == 2353** by the **`ANSWER:`
    field**, never bare value presence. `recording_gate_result.json`.
  - **GATE 2 is a go/no-go PROXY, not the measurement.** It used unequal K (coupled view at k=1/6 vs
    verbatim at k=1/25), empty accumulated state (least pressure → most favorable to recording, so
    verbatim's 0/3 is conservative), and tested only the recording half — never the answer, never
    table-survival through 25 Phase-B passes. The **real arbiter is the battery's per-pass
    verbatim-table-presence tracking**: if `verbatim_only` records the usable mapping in the full
    run, the money comparison collapses to **no-benefit** and is reported as such.
- **GATE 3 — compose positive control / ceiling** (`compose_gate.py`, the advisor's F7-gate applied
  to the answer metric), **PASS**: with the full structure seeded into state (table + adder +
  function signature + filler), the floor produced the exact answer **2353 in 4/4** draws (temp-0 +
  3×temp-0.7). So the floor **can** do the lookup-and-add chain; a battery coupled-failure is
  therefore a genuine retention/compose failure, **not** a "this floor can never compose" artifact —
  the run is interpretable. (Without this, a coupled-0/verbatim-0 battery would be uninterpretable.)
  `compose_gate_result.json`.

## 6. Pre-registered outcomes (stated before scoring)

- **Signal (might-work confirmed):** `coupled_full` answers 2353 at a meaningfully higher rate than
  `verbatim_only` across seeds, AND per-pass inspection shows coupled carried the table from Phase-A
  while verbatim_only never recorded it. Mechanism visible, not just the score.
- **Backfill caught:** `verbatim_only` answers correctly often → the unit is guessable or fragments
  too close (GATE 1 should pre-empt; report honestly, no unearned win).
- **Floor-limited null:** both arms fail (even coupled can't reassemble from the available
  structure) → the untrained 7B can't do this at this scale; real evidence the capability needs the
  trained student (E2′; [[viability-vs-optimality]]). Publishable, non-tie.
- **No-benefit:** coupled first acquires the table in Phase-B (not Phase-A — State-D guard fails at
  runtime), or both arms record/retain the table equally → the coarse pass gave no isolable benefit;
  report as such. **If GATE 2 shows verbatim_only also records the table, P7 is predicted-null and
  is carried to E2′ rather than run** (the reframe's own kill condition).

## 7. Scope / discipline

- Tests the **split-unit principle** (structure carried by the coarse pass enables reassembly), with
  slicing held identical across arms — NOT "code-aware slicing beats naive slicing." The isolated
  lever is the **coarse structure-preserving pass**, not the slice boundaries.
- **Honest scope of the reframe:** with eviction ~absent on this floor, P7 tests *"the coarse pass
  preserves a unit the verbatim reader discards as noise"* more than *"reassembly under eviction."*
  The split still earns its keep — by **query-leak isolation** (the table is encountered far from
  the query-relevant call, under a broad rubric, so verbatim has no cue to preserve it), not by
  eviction. We do not lean on the "reassembly under state loss" narrative the data no longer supports.
- Untrained Qwen-7B floor, n=1 fixture, 1 split unit, temp-0 + ≥3 sampled seeds. A mechanism probe,
  **not** an effect size and **not** a viability verdict (rides on E2′). Viability framing: remove
  confounds to give the floor a fair shot (structure-preserving compression, broad query); do not
  hand-hold it to the answer (no naming region 23 / surcharge in the task) — fair-shot, not forcing.
- Math/science split units (a proof step needing a lemma stated far earlier) are a noted follow-up;
  code first because units are explicit and compression is genuinely structure-preserving.
- **Do not publish until reviewed.** Surfaced for review: fixture + GATE 1 result + realized-view
  guards now; GATE 2 result on completion; the battery only on approval.
