# The pyramid schedule, and the compressor as architecture — 2026-07-30

**Status:** complete. Six view arms measured; four chain-gate arms (44 draws, none truncated); P1d
and P1h re-run on the pyramid. Nothing here is verdict-eligible: the addendum froze the D25
schedule, so every pyramid run is a new experiment and is stamped as one.

**If you read one thing:** the schedule was not the binding constraint. Fixing it changed nothing at
the close (1/10 → 0/10, p=1.00). The arm that hands the model the complete answer in pass 1 still
returns 0/10 on the composed answer. What the pyramid *did* buy is a clean separation of three
blockers that the two-level schedule had confounded — compression, salience, and retention — and the
evidence now points at the third. Sections in order: the six arms, then the four findings about
compressors, then the chain gate, P1d, P1h, and cost.

## The short version

The maintainer's instruction was that the compressor is part of the architecture in its final form,
specialised for the role, and that hand-edited compressions are an attempt to emulate that — but to
try a general compressor too. Six arms were built and measured on the same pyramid tiling. Four
things came out of it, and the fourth is the one that matters most.

1. **The existing specialized compressor is not a resolution operator.** `compress_code.py` (v2) is
   `C(x)`, not `C(x, sigma)`: its budget argument is advisory, so it emits a flat **11.8x at every
   level** — 5,573 tokens for the whole document (over a 3,000 budget) and 347 for a sixteenth
   (under it). On a pyramid that means `k` indexes nothing, which is the exact defect the pyramid
   was built to repair. A sigma-parameterized version (`src/pca/compress_graded.py`) fixes it.
2. **How good the compressor is at salience predicts whether the fixture still works.** Across the
   six arms the relationship is monotone: the better the compressor, the earlier the operands
   appear, and past a threshold a single view answers the whole chain.
3. **A general LLM compressor reproduces the archived table-to-range pathology by itself.** Given
   the whole document it writes *"surcharges spanning 161 to 988 cents"* — the range — while
   keeping the standalone scalar *"a fixed reconciliation adder of 1365 cents"* exactly. That is
   the 8/11-vs-1/11 scalar-vs-table-row asymmetry (p≈7.5×10⁻³), now observed at the **compressor**
   stage rather than the recorder stage.
4. **This fixture cannot test composition against a competent compressor, and the reason is
   arithmetic.** Of 106 modules, **six** declare anything. Their declarations total **1,129
   tokens**; with a pattern block covering the other 100 that is **1,806 tokens = 60% of ONE view
   budget**. Any compressor that notices the document is 94% one repeated module puts the entire
   distinctive content into the level-1 view. The split-fact guard survives only where the
   compressor is bad at salience.

## The six arms

Identical tiling in every arm (`pyramid_levels` + `balanced_tile` depend only on the turns and V),
so the arms differ in exactly one thing: what the compressor did to the same spans.
V = 3000, branching 2, doc 65,781 tok / 106 turns, levels 1-2-4-8-16-32, K = 63.

| arm | class | compression by level | budget fill | cost | binding@ | adder@ |
|---|---|---|---|---|---|---|
| `extractive` general, deterministic | **faithful** | 22.5 11.2 5.7 2.8 1.4 1.0 | 97% | 2.37x | L6 | L6 |
| `graded` role-specialized, deterministic | **faithful** | 22.0 11.2 5.8 3.0 1.5 1.0 | 91% | 2.29x | **L2** | **L1** |
| `llm_general` Haiku, generic D29 prompt | **faithful** | 55.7 18.3 10.8 3.8 2.3 1.0 | 62% | 1.87x | L6 | L4 |
| `llm_roleaware` Haiku, told its role | assisted | 46.8 24.9 13.4 4.4 3.3 1.0 | 47% | 1.67x | L1 | L1 |
| `hand_blind` authored, uniform rule | assisted | 30.5 27 22 16.7 12.7 1.0 | 18% | 1.25x | L1 | L1 |
| `hand_oracle` authored, probe-aware | assisted | 30.5 27 22 16.7 12.7 1.0 | 18% | 1.25x | L1 | L1 |

`binding@` / `adder@` = the coarsest level at which the queried key→value binding (`23: 988`) and
the adder's value survive compression. **faithful** = the split holds *and* the views were authored
blind to the probe, so a chain result is a genuine cross-pass compose test. **assisted** = one or
both fails; still run and reported, but it measures RETENTION, not composition.

Guard results per arm are in `pyramid_views/_validation.json`. G1 (strict doubling) and G2
(per-level tiling) pass everywhere — they are properties of the schedule, not the compressor. G3
(monotone, verbatim floor) passes everywhere. G4 and G5 separate the arms, below.

## Finding 1 — the specialized compressor had no sigma knob

`compress_code.py` selects by structural role and treats `target_tokens` as advisory. Measured
across the six levels it produces a flat 11.8x, overshooting V by 86% at level 1 and undershooting
it by 88% at level 5. Its output size tracks the *content* of the slice, not the *budget*.

`src/pca/compress_graded.py` re-expresses the same design as a severity ladder, each rung justified
on the code document class with no reference to any probe (the COMPRESSOR-V2.md standard):

| sigma | what it drops | why that, at that point |
|---|---|---|
| 0 verbatim | nothing | the operator must be able to *spend* budget, not only save it |
| 1 drop_bodies | function bodies | the bulk, and the lowest-information part of a module (= compress_code v2) |
| 2 drop_prose | docstrings, comments | the gloss goes before the thing it glosses |
| 3 drop_edges | imports, helper digest | wiring is cheaper to lose than the values callers read |
| 4 shape_collections | large literals → count + key/value range; scalars kept verbatim | a scalar costs one line, so summarizing it saves nothing |
| 5 names_only | all values | only the claim that a thing is declared remains affordable |
| 6 module_inventory | everything but the path | the floor |

sigma is chosen **per module**: all start at 0, and while over budget the *largest currently
rendered* module is pushed one rung (ties by document order). Largest-first is a size rule, not a
content rule, so the allocator never asks what a module is about.

The sigma 0 rung was added after measurement, not by design: without it the operator could only
tighten, so levels 2-5 pinned at a flat 11.8x and level 5 emitted 347 tokens against a 3,000-token
budget. That is recorded because it is the general lesson — **a compressor that can only remove
detail is not a resolution operator.**

Result: a genuine ladder (22.0 → 11.2 → 5.8 → 3.0 → 1.5 → 1.0), every view within 9% of budget, and
a sigma distribution that slides with level — at level 1 it runs sigma 2-5 across 106 modules; at
level 5, 73 of 106 modules are verbatim.

**Note, stated in advance and then observed:** sigma 4 is where key→value *binding* dies while the
collection's *range* survives. That was written into the ladder's justification before the arms were
run, and it is the mechanism behind the archived scalar-vs-table-row result. It is a prediction of
the design, not an accommodation of a result.

## Finding 2 — early exposure, and what the coarsest view actually says

The old C1 *asserted* that the hand-built scaffold carried both operands into Phase A. On the
pyramid that is not an assumption to assert but a property to measure, and it differs per arm. The
graded arm's level-1 view (whole document, 22x) contains exactly:

```
# ===== module: pricing/region_tables.py =====
declares: REGION_SURCHARGE_CENTS
# ===== module: fulfillment/line_quote.py =====
RECONCILIATION_ADDER_CENTS = 1365
```

The coarsest pass learns *that* a region-surcharge table exists — a home — and *what* the adder is —
a value. The specific row needs descending the pyramid; it arrives at level 2. That is
"record coarse, refine fine" with real early signal, **and the split-fact guard still holds.**

By contrast `extractive` gives no early exposure whatsoever: both operands appear for the first time
at the verbatim level, so the "record coarse, refine fine" story has no coarse signal to record.

## Finding 3 — the general LLM compressor loses the binding and keeps the scalar

Same model, same slice, same budget; the only difference is whether the compressor was told its role.

- **Generic D29 prompt** (`llm_general`), whole document at 55.8x: `REGION_SURCHARGE_CENTS`,
  `RECONCILIATION_ADDER_CENTS` and `compute_line_surcharge` are all **absent by name**. The value
  988 appears only as a range endpoint — *"region codes ranging from 10 to 98 and surcharges
  spanning 161 to 988 cents"* — while 1365 survives as a value — *"a fixed reconciliation adder of
  1365 cents per line"*. It spends its budget narrating the boilerplate template.
- **Role-aware prompt** (`llm_roleaware`), same slice at 46.8x: keeps the entire 24-entry table
  including `23:988`, the adder, and writes the relation out explicitly as
  `compute_line_surcharge(region_code) → REGION_SURCHARGE_CENTS[region_code] + 1365`.

Three of the four probe-blind compressors (extractive, graded at sigma 4-5, llm_general) show the
same asymmetry: **a standalone scalar survives compression; one row of a table does not.** Only the
role-aware arm breaks it, and it does so by refusing to compress the table at all.

## Finding 4 — the fixture is 97% padding, and that is what made the chain look hard

```
document                           65,781 tok  (106 modules)
  declaration-free (R1 collapse)      100 modules -> one 677-tok pattern block
  declaring modules                     6 modules
    their declarations (sigma 1)     1,129 tok
    verbatim, bodies included        1,482 tok
view budget V                        3,000 tok
distinctive content + block          1,806 tok = 60% of ONE view
```

Six modules declare anything: `pricing/region_tables.py`, `queue/pipeline.py`,
`carrier/fuel_tables.py`, `routing/router.py`, `routing/labels.py`, `fulfillment/line_quote.py`.
The other 100 are declaration-free helper modules following one body template — detectable
structurally, without naming anything.

So a compressor that applies the obvious probe-blind rule — *collapse a hundred indistinguishable
modules to one pattern block and spend the freed budget on the six that declare something* — fits
the document's entire distinctive content into the level-1 view. `hand_blind` does exactly that and
fills **18%** of its budget, because after the collapse there is nothing else to put in.

**This is a property of the fixture, not of the compressor.** It gives the Phase-2 fixture rebuild a
hard requirement it did not have before: *the document's distinctive content must exceed one view
budget*, or the pyramid's top level answers everything and no schedule wrapped around it can test
composition across passes.

It also explains, retrospectively, why the 94%-boilerplate salience finding was so sharp. The
filler was not scenery around the experiment; the filler *was* the difficulty.

## Finding 5 — budget discipline and salience pull against each other

G4 asks whether compression is a function of level rather than of position within a level — i.e.
whether `k` really indexes resolution. It passes for the three budget-driven arms and **fails** for
the three salience-driven ones.

The reason is structural. A salience-driven compressor's output size tracks how much distinctive
content a span happens to hold, so two tiles at the same level compress by wildly different amounts
(`hand_blind` level 4: the tile holding `line_quote.py` renders far larger than its eight siblings).
A budget-driven compressor always renders to V, so ratio is fixed by the slice size, which is fixed
by the level.

| | k indexes resolution (G4) | keeps what matters | split survives |
|---|---|---|---|
| extractive | yes | no | yes |
| graded | yes | yes | yes |
| llm_general | yes | partly (scalar only) | yes |
| llm_roleaware | **no** | yes | **no** |
| hand_blind / hand_oracle | **no** | yes | **no** |

`graded` is the only arm in the top-left and top-middle at once. Whether that survives a document
whose distinctive content actually exceeds one view is the open question, and it is the same
question as the fixture rebuild.

One more null worth recording: **`hand_oracle` and `hand_blind` produced byte-identical view sets.**
Pinning the two operand modules because the probe is known changed nothing, because the probe-blind
rule already keeps every declaration in the document. When the compressor is good, there is nothing
left for an oracle to add.

## What was built

| file | what |
|---|---|
| `src/pca/compress_graded.py` | the sigma-parameterized role-specialized compressor |
| `src/pca/compressor.py` | `RoleAwareLLMCompressor` + `_role_aware_prompt`; `get_compressor` gains `llm_roleaware`, `graded` |
| `src/pca/planted.py` | `build_pyramid_schedule` accepts an injected compressor and records which ran |
| `experiments/e2prime/gen_pyramid_views.py` | generate + freeze one view set per arm (resumable; `--probe-one` before paying for an LLM arm) |
| `experiments/e2prime/author_pyramid_views.py` | the two hand-authored arms + `--budget-audit` |
| `experiments/e2prime/verify_pyramid_schedule.py` | G1-G5 + C1 early exposure, per arm, with the faithful/assisted stamp |
| `experiments/e2prime/stagea_chain_gate.py` | `--schedule pyramid --views ARM --stage-map {level,fraction}` |
| `experiments/e2prime/stagea_p1_probes.py` | `--probe p1d_pyr` (resolution vs label) and `--probe p1h_pyr` (provisional marks) |

Two bugs were caught by the guards before any result depended on them: the split-fact marker was
loosened from `REGION_SURCHARGE_CENTS = {` to a bare name mention, which made every verbatim view of
`compute_line_surcharge` look like it held both operands (it reads the table, so it mentions the
name); and `pyramid_stage` emitted `concrete` where the prompt module's rubric key is `integrate`,
which killed the first draw at pass 4 and is now asserted against `RUBRICS` directly.

## Coupling on the pyramid

The output-demand stage is derived from the **level**, not the pass fraction (`--stage-map level`,
the default). M1's claim is that one schedule position sets both what the model sees and what it
must produce; on the D25 schedule those coincide because there are only two resolutions, but on the
pyramid level 6 begins at k=32 of 63, so a fraction-based ladder puts ten verbatim views under the
`integrate` rubric. Staging by level keeps the two halves of the coupling aligned.

The ladder is lopsided by construction — scaffold 3, integrate 12, verbatim 48 — because tile counts
double per level. That is what the pyramid implies, not a tuning choice; `--stage-map fraction`
exists for comparison.

## Chain gate on the pyramid — first draw, hand-read

`--schedule pyramid --views graded --arm student`, seed 1, temp 0.7. 63 passes, 1,278 s, **no
truncation** (state peaked at 13,489 tok against a 24,576 context, so the doubled pass count is
affordable on this fixture). Baseline to beat, from the archived D25 battery: student RECORD
(`23: 988` in the final state) **1/10**, close returns 2353 **0/10**; floor 0/10 on both.

Seed 1 on the pyramid: `ANSWER=None`, no candidate, `record_first_pass=None` — the binding never
reached the state. What makes the draw worth reading is the pass where it should have.

**Pass 38 is the one verbatim view carrying `23: 988`.** It emitted exactly one edit op, and the
strict guard blocked it:

- the tile is 2,402 tok across four modules; the surcharge section is **263 tok — 10.9%** of it.
  (Under D25 the equivalent tile was 5.8% signal. The pyramid nearly doubles the ratio and it is
  still a tenth.)
- the model's single op was a `REPLACE` into `metrics/digest14.py` — a **declaration-free
  boilerplate module** — not the table. It did not attempt the binding.
- that op was blocked `blocked_quote_mismatch`, because the generation had degenerated into a
  repetition loop (`normalize_manifest, normalize_tariff, normalize_lane,` repeated to the token
  limit) so the quoted old text no longer matched the entry.

So on the correct schedule, with the adder recorded from pass 7 onward and held to the end, the
model still spent the decisive pass on filler. **The salience blocker survives the schedule fix.**
That is the outcome the 07-29 findings predicted, and it is now measured against a schedule where
`k` genuinely indexes resolution rather than one where it indexed nothing.

Two secondary observations from the same draw: the adder reached the state at **pass 7 (level 3)**
and was still present at pass 63 — retention over 56 passes is not the problem; and the state ran
to 13,489 tok against a 4,000-tok advisory budget, replicating "budget advisory-only" at twice the
pass count.

### The full battery, and a clobber caught in the act

Ten sampled seeds + the anchor, none truncated.

| | RECORD (`23: 988` at close) | close returns 2353 | mechanical candidates |
|---|---|---|---|
| D25, student (archived, verdict-eligible) | **1/10** | 0/10 | 0/10 |
| **pyramid `graded`, student** | **0/10** | 0/10 | 0/10 |

The schedule fix does not move recording (1/10 → 0/10, Fisher p = 1.00 — no difference either way).
Two seeds answered `1365`: the model reaching for the one operand it did hold.

But **seed 5 recorded the binding at pass 38 — exactly the right pass — held it for nineteen
consecutive passes (38-56), and lost it at pass 57.** Hand-read:

- at pass 56, entry **S36** read
  `pricing/region_tables: REGION_SURCHARGE_CENTS dict (... {10:314, 14:804, 17:883, 19:808, 23:988, ...})`
- pass 57's view contains four modules, **all of them declaration-free boilerplate**
  (`transform/envelope76`, `validate/payload77`, `routing/manifest78`, `billing/tariff79`)
- the model emitted five REPLACEs, all applied. S36 became
  `routing/manifest78: normalize_parcel (i%84, weight>0.531), hash_envelope (i%56, weight>0.257), ...`

The entry holding the answer was overwritten with filler, by a pass whose view contained nothing
but filler. That is the archived 10%-clobber pathology, caught in the act, and it destroyed the one
draw in ten that would otherwise have recorded.

**This is the pyramid's own cost, and it is a new finding.** The same seed under D25 recorded at
pass 12 and the entry *survived* to the close. On the pyramid the fact is recorded later (pass 38
of 63) and then has to survive twenty-five further editing passes. Doubling the pass count doubles
the exposure of everything already recorded to being overwritten. Retention over many passes is not
free, and on this evidence the binding constraint is not whether a fact gets recorded but whether
an edit policy with a 26% no-op and 10% clobber rate can leave it alone afterwards.

## P1d on the pyramid — the conditioning channel, re-asked

`--probe p1d_pyr --views graded`, student, seeds 1-10, temp 0.7, identical 25-entry archived state
in every cell. The 07-30 discrepancy withdrew falsifier F2's negative on the grounds that k carried
no information in training. The pyramid gives k a real referent, so the question is askable — and it
splits into three that the old schedule could not separate.

**LAB — does the label alone do anything?** View, state and rubric pinned to the verbatim tile;
only `position: {k, K}` varies.

| k label | 1 | 8 | 32 | 63 |
|---|---|---|---|---|
| applied `23: 988` | 3/10 | 2/10 | 3/10 | 3/10 |

Flat across a 63x swing: **11/40 pooled, no trend.** The position channel is inert, now measured on
a schedule where it could have carried something.

**MIS — when label and content disagree, which wins?**

| cell | applied `23: 988` | ops emitted (mean) | no-op REPLACEs |
|---|---|---|---|
| `mis_fineview_earlyK` (verbatim view, labelled k=1) | 3/10 | 4.5 | 1 |
| `mis_coarseview_lateK` (22x view, labelled k=63) | 0/10 | 16.6 | 103 |

**Content wins — on the well-powered metric.** The recording contrast (3/10 vs 0/10) is
Fisher p=0.211 and does NOT support a claim on its own at n=10. The edit-behaviour contrast does:
4.5 vs 16.6 ops per draw and **1 vs 103 no-op REPLACEs** are per-op counts over ten draws, not
ten-draw proportions. On those, the verbatim view labelled k=1 behaves like the honest verbatim
condition and the coarse view labelled k=63 behaves like the honest coarse condition. The label does
not shift behaviour toward the stage it names; the view does.

**RES — does behaviour track the view's resolution?** Same source turn, its six nested covering
views, each labelled with its own true k and stage. Because every level renders to the same budget,
view LENGTH is near-constant (2,402-2,989 tok) across the ladder, so the length/content confound the
padded probe was built for is controlled by construction.

| level | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| compression | 22.0x | 11.4x | 6.3x | 2.7x | 1.6x | 1.0x |
| binding in view | no | yes | yes | yes | yes | yes |
| applied `23: 988` | 0/10 | 1/10 | 1/10 | 0/10 | 1/10 | 3/10 |
| ops emitted (mean) | 17.4 | 16.0 | 15.0 | 7.7 | 7.8 | 7.0 |

Recording trends upward but **not significantly at n=10** (L6 3/10 vs L2 1/10, Fisher p≈0.58) — read
it as suggestive only. What does move sharply is **edit volume: 17.4 ops at 22x down to 7.0 at
verbatim**, a clean monotone response. So the model *is* behaving differently at different
resolutions; that response is driven by what it sees, not by what k says.

Note also that the binding sits in the view at every level from 2 down and is recorded at most 3/10
even when fully verbatim. **View content is necessary and nowhere near sufficient** — consistent
with the chain gate, where the decisive tile was 10.9% signal and lost.

**Scope, stated honestly:** this student was trained on the D25 two-level schedule, so it was never
trained to use a resolution ladder. The result says a D25-trained student does not respond to k on a
pyramid. It does not establish what a pyramid-trained student would do — that is the E2' training
question, and it is exactly what the regeneration ordered by the 07-28 arbitration would answer.

## P1h on the pyramid — the provisional-mark mechanism

Held back in the 07-30 handoff because it tested a prompt fix against the old schedule. The
mechanism is the maintainer's: *record a value as soon as you see it, mark it `988*` as unconfirmed,
and settle it on the pass that shows it in full detail.*

It needs a compressor whose coarse views **degrade** the value rather than dropping it, and only one
arm supplies that. Measured across the arms for the queried value:

- `llm_general` — survives as a **range** at levels 1,2,3,5 and exactly at level 6. Four coarse
  passes where a provisional mark is the right move.
- `graded` — **absent** at level 1 (its module sits at sigma 5, declaring the table's name and no
  values), exact from level 2. Nothing to mark.
- `extractive` — absent until level 6. Nothing to mark.

So the probe runs on `llm_general` and **refuses** on the others rather than silently testing a
mechanism whose precondition is absent. That the *general* compressor is the one producing the
degraded form is not incidental: it is the archived table-to-range pathology, arising in the
compressor rather than the recorder.

Student, seeds 1-10, coarse view = level 1 (55.8x), fine view = level 6 (verbatim, binding exact).

| cell | applied `23: 988` | `988` anywhere in state | provisional marks emitted |
|---|---|---|---|
| `coarse_plain` | 0/10 | 7/10 | **0 in 0/10** |
| `coarse_provisional` | 0/10 | 8/10 | **0 in 0/10** |
| `fine_plain_after_plain` | 0/10 | 6/10 | 0 |
| `fine_confirm_after_prov` | 1/10 | 10/10 | 0 |
| `fine_confirm_after_plain` | 1/10 | 8/10 | 0 |

**The mechanism's precondition fails: the mark is never emitted.** Hand-read — the PROVISIONAL
sentence is present verbatim in the system prompt, worked example included (*"putting an asterisk
immediately after it (for example count: 47*)"*), and there are **zero asterisks of any kind** in
any post-state across ten draws. The 1.5B student does not execute the instruction.

So the pre-registered reading `mark_is_load_bearing` cannot fire, and indeed
`fine_confirm_after_prov` (1/10) equals `fine_confirm_after_plain` (1/10): whatever the CONFIRM
rubric buys, it is not bought by the mark, because there were no marks.

**Report this as UNTESTED-AS-DESIGNED, not as a refutation.** "The mechanism does not work" and
"this model cannot follow the instruction" are different claims, and only the second is supported.
The mechanism needs re-testing at a scale that emits the mark before anything is concluded about it.

One thing the cells do show cleanly: the states faithfully record the compressor's lossy form.
Seed 1's state reads *"Pricing module (surcharge tables, region codes 10-98, surcharges 161-988
cents)"* — the range, propagated intact from the level-1 view. **The binding was destroyed by the
compressor and the recorder preserved the destruction faithfully.** The two-stage pathology, end to
end: what the compressor throws away, no downstream demand can recover.

## All four chain-gate arms, and where the blocker actually is

Ten sampled seeds + anchor per arm, none truncated. All pyramid runs are `verdict_eligible=false`
by construction.

| arm | model | RECORD at close | RECORD+adder | close returns 2353 |
|---|---|---|---|---|
| D25 (archived, verdict-eligible) | student | 1/10 | 1/10 | 0/10 |
| pyramid `extractive` | student | 0/10 | 0/10 | 0/10 |
| pyramid `graded` | student | 0/10 | 0/10 | 0/10 |
| pyramid `graded` | **floor** | 0/10 | 0/10 | 0/10 |
| pyramid `llm_roleaware` | student | 1/10 | 0/10 | 0/10 |

**No arm composes. The student is not distinguishable from its untrained floor on this schedule.**

The end-state numbers hide the interesting part. Tracking whether the binding was *ever* in the
state, at any pass, and whether it survived:

| arm | ever recorded | still there at close | destroyed after being recorded | lost at pass |
|---|---|---|---|---|
| `extractive` (operands only at L6) | 0/10 | 0/10 | — | — |
| `graded` (adder L1, binding L2) | 1/10 | 0/10 | 1 of 1 | 57 (held 19 passes) |
| `llm_roleaware` (everything at L1) | **3/10** | 1/10 | **2 of 3** | 7, 17 |

Two things fall out, and they are different in strength.

**1. Compression quality tracks whether the fact is ever recorded — suggestive, underpowered.**
Ever-recorded runs 0 → 1 → 3 of 10 in exactly the order of the compressors' salience. It is
monotone and it is the direction the architecture predicts, but at n=10 no pair separates:
roleaware vs extractive Fisher **p=0.211**, roleaware vs graded **p=0.582**. Read it as a
direction to test at larger n, not as a result.

**2. Most of what gets recorded is then destroyed — descriptive, and hand-verified.**
Across arms, the binding entered the state in **4 draws** and was gone by the close in **3 of them**.
That is a count, not an inference, and both clobber events were read by hand with the destroying
edit identified:

- `graded` seed 5, pass 57: entry **S36** held the full table including `23:988`. The view at that
  pass contained four modules, **all declaration-free boilerplate**. The model emitted five
  REPLACEs; S36 became `routing/manifest78: normalize_parcel (i%84, weight>0.531), ...`
- `llm_roleaware` lost it at passes **7 and 17** — within 3 to 13 passes of recording it, and while
  the level-1 view had already supplied the whole answer.

**The decisive arm is `llm_roleaware`.** Its level-1 view hands the model, in 1,407 tokens:

```
REGION_SURCHARGE_CENTS = {10:314, ..., 23:988, ...}
RECONCILIATION_ADDER_CENTS = 1365
compute_line_surcharge(region_code) → REGION_SURCHARGE_CENTS[region_code] + 1365
```

— the table, the adder, and the relation written out as a formula, at pass 1 of 63. Sixty-two
passes later the state holds the binding in 1 draw of 10, holds binding *and* adder together in
**0**, and the close returns 2353 in **0**.

That relocates the blocker. It is not coverage (every operand was read). It is not the schedule
(the pyramid is the README's own design, validated on five guards). It is not compression in this
arm (the compressor delivered the complete answer, early, in one view). It is not the recording
demand at the decisive pass (there was no decisive pass — the answer arrived first). What remains is
**retention across passes under an edit policy that overwrites**: 26% of REPLACEs are byte-identical
no-ops and 10% clobber an unrelated entry, and on 63 passes those rates get 63 chances.

This is the pyramid's own cost, and it is a genuinely new finding: **the schedule that makes `k`
index resolution also doubles the number of opportunities to destroy what has already been
recorded.** Under D25 the same seed-5 draw recorded at pass 12 and the entry survived to the close.

## The exploration (2026-08-02) — where the blocker actually is

Exploratory throughout: `gate_legal=false`, arms chosen after seeing data, seeds 1-10. Seeds 11-20
are deliberately untouched so a pre-registered confirm is still available.

### An instrument correction first, because it moves earlier numbers

The chain gate's live `queried_mapping` flag required a literal colon (`23: 988`). The state that
finally held both operands wrote the binding as **`23→988`**, so the flag read False on a state that
held the fact, correctly bound. This is the "paraphrase-robust matcher into the chain runner's live
flags" debt the 07-29 handoff listed as outstanding, and the exact trap `pca.planted`'s own
docstring warns about.

Re-scoring the archive with the analysis-side matcher (`analyze_chain_gate.rescore`):

| arm | model | live flag | **rescored** | c1 (both operands) |
|---|---|---|---|---|
| D25 (verdict-eligible) | student | 1/10 | **3/10** | 2/10 |
| D25 | floor | 0/10 | 0/10 | 0/10 |
| pyramid `extractive` | student | 0/10 | 0/10 | 0/10 |
| pyramid `graded` | student | 0/10 | 0/10 | 0/10 |
| pyramid `graded` | floor | 0/10 | 0/10 | 0/10 |
| pyramid `llm_roleaware` | student | 1/10 | 2/10 | 1/10 |
| pyramid `llm_roleaware` + `retain` | student | 2/10 | **3/10** | **3/10** |

**The undercount reached a verdict-eligible run**: D25 student RECORD is 3/10, not 1/10. The live
matcher now uses the same separator class as the analysis path so the two cannot diverge again.

### The retain guard

`IntegrationState(guard="retain")` refuses a REPLACE that drops numeric literals the target entry
held. Motivation, measured across 3,941 REPLACEs in the pyramid draws: 37% dropped literals, and of
the 3,226 that PASSED the strict guard and were applied, **1,003 (31%) destroyed detail** — 435 of
them five or more literals at once.

On `llm_roleaware`, where retention had headroom:

| | ever recorded | at close | losses | **c1 (both)** |
|---|---|---|---|---|
| base | 3/10 | 1/10 | **2 of 3 destroyed** | 1/10 |
| `retain` | 2/10 | 2/10 | **0** | **3/10** |

391 destructive edits blocked; **every fact recorded survived to the close.** c1 had been 0/10 on
every other pyramid arm. Two caveats: 1/10→2/10 at close is p=1.00, and on the retention micro-probe
the guard's 10/10 is close to tautological (it is defined to preserve exactly what that metric
measures). The non-tautological part is that the model still emits ~68 detail-destroying REPLACEs
under the guard: it refuses bad edits, it does not teach better ones.

Also recorded: the guard on `graded` did nothing (0/10), because recording on that arm succeeds
1/10 — a retention fix behind a recording step that fails 90% of the time has no headroom. And the
prompt-side lever is now **0 for 3** (p1g ANTI_GRIND, plus `noclobber` twice, which both *lowered*
retention and *raised* detail-loss attempts). Both fixes that worked were structural.

### The compose ladder — the session's result

Replaying ONLY the closing turn on states the 1.5B student built itself
(`close_only_probe.py`, temp 0):

| reader | correct overall | **correct given the state holds both operands** |
|---|---|---|
| student (1.5B, fine-tuned) | 0/10 | **0/3** |
| Qwen2.5-3B (untrained) | 3/10 | **3/3** |
| Qwen2.5-7B (untrained) | 3/10 | **3/3** |
| Qwen2.5-14B (untrained) | 3/10 | **3/3** |
| Claude Haiku 4.5 | 3/10 | **3/3** |

**Every reader from 3B to a frontier model answered correctly on exactly seeds {1, 5, 10} — exactly
the set of states that truly hold both operands. Not one more, not one fewer.**

That perfect concordance across a >100x parameter range is the informative part, more than any
single denominator. It says:

1. **The state is exactly sufficient.** Where it holds the operands, every competent reader answers.
   Where it does not, nothing up to a frontier model recovers them — the information is genuinely
   gone, not merely hard to find.
2. **The compose boundary is between 1.5B and 3B**, not 1.5B and 7B as GATE-3's seeded-state result
   suggested. And every model that clears it is UNTRAINED — no fine-tuning, no rubric exposure.
3. **Scaling the reader buys nothing beyond 3B.** All remaining headroom is in the recorder.

So the pipeline runs end to end: a 1.5B, given a role-aware compressor and an edit guard, builds a
bounded state from a 65,781-token document that a 3B answers a cross-module question from. The
recorder and the reader can be different models, and the small one's job is *maintaining the state*,
not answering from it.

**What this is not.** n=3 on the decisive cell, one fixture whose distinctive content is 1,806
tokens, arms selected after seeing the data, and the reader did only the closing step. It does not
show a win over a dense read, and it does not vindicate pass-conditioning specifically — the k/K
channel measured inert twice (P1d, and again on the pyramid). What carries the result is coverage +
retention + a compressor that preserves bindings. That is most of DiSCo, but it is not the
`k`-conditioning claim.

## The confirming run — pre-registered, held-out seeds

`CONFIRM-PREREG-2026-08-02.md` was written and its predictions fixed BEFORE the run. Seeds 11-20
had never been used by any arm in this program. Stack unchanged from the exploration: pyramid /
`llm_roleaware` views (not regenerated) / `guard=retain` / 1.5B student, frozen.

| | predicted | observed | |
|---|---|---|---|
| **P1** c1 — both operands in the final state | >= 2/10 | **3/10** (seeds 11, 14, 15) | pass |
| **P2** Qwen2.5-3B composes 2353 on every c1 draw | all | **3/3** | pass |
| **P3** the 1.5B student composes on none | 0 | **0/3** | pass |
| **P4** recorded-then-lost | 0 | **0/10** | pass |

All four pass. c1 = 3/10 on held-out seeds against 3/10 in the exploration, and the 3B again
answered on **exactly** the c1 seeds and nothing else — the same perfect concordance seen on seeds
1-10, now on data the stack was not fitted to.

**So the central claim is replicated, not fitted:** a 1.5B student, given a role-aware compressor
and an edit guard, builds a bounded state from a 65,781-token document that an untrained 3B answers
a cross-module question from — in about 3 draws of 10 — and never destroys the fact once recorded.

Scope is unchanged and still narrow: one fixture, no dense-read comparison, and the k/K conditioning
channel is not part of the claim.

## Importance marks — the maintainer's notes-to-later-passes idea

The simplified confidence extra: let earlier passes tell later passes which entries are load-bearing
so later passes do not clobber them. Strictly more general than `retain`, which protects only
numbers and cannot tell a load-bearing constant from an incidental one.

Three variants separate *producing* an importance signal from *using* one — the same two skills that
came apart on compose. Instrument: the discriminating configuration (start state pinned to `graded`
seed 5 pass 56, 6,852 tok, 66 entries; window k=57-63 containing the known-fatal pass 57).

| condition | HELD | lost at | ops refused by mark | self-authored marks |
|---|---|---|---|---|
| `base` | 8/10 | 57, 57 | 0 | 0 |
| `selfmark` — model marks its own entries | 8/10 | 57, 57 | 0 | **0** |
| `marked_soft` — harness marks, rubric asks model to respect them | **8/10** | **57, 57** | 0 | 0 |
| `marked_hard` — same, plus ops on marked entries refused | **10/10** | — | 8 | 0 |

**Both signalling variants fail; only enforcement works.**

- **The model cannot PRODUCE a mark.** Zero self-authored marks in ten draws here, zero in an
  earlier run, and zero asterisks in P1h under an explicit worked example. Three independent
  designs, same result.
- **The model cannot USE a mark it is shown.** `marked_soft` is *identical* to base — same 8/10,
  the same two losses at the same pass 57, and 209 REPLACEs against base's 215. Not a small effect:
  no effect. Hand-verified that the test was live — the marking rule flagged exactly two of 66
  entries, and they were **S36** (the entry that gets clobbered, holding the table) and **S65** (the
  adder and the relation). The at-risk entry was visibly flagged, the rubric explained the flag and
  forbade overwriting it, and the model overwrote it anyway.
- **Mechanical enforcement works**, refusing 8 ops and eliminating the losses — but that is the
  harness doing it, in the same category as `retain`, not the model responding to a signal.

Note also what the first attempt at a marking rule showed: "contains a multi-digit literal or an
ALL-CAPS token" flagged **70 of 70** entries. In a code state every entry has a `digest14` or an
`i%84`. A crude importance heuristic saturates on this fixture exactly as compression and recording
did — the same 1,806-tokens-of-signal problem, one level up. The rule that works marks a *binding*
(`NAME = value`, or `key: value`), which flags 2-9 entries depending on the state.

**The prompt column is now 0 for 5** on this student: p1g ANTI_GRIND, `noclobber` twice, `selfmark`,
`marked_soft`. Every intervention that moved anything was structural — the role-aware compressor,
the `retain` guard, mark enforcement. That is the clearest practical finding of the exploration: at
this scale the recorder's edit policy has to be *enforced by the architecture*, not requested in a
rubric.

## Cost

The pyramid costs about **2x** the D25 schedule in view tokens (2.29-2.37x source vs 1.24x) and
**63 passes instead of 31**, with the state re-read at every one — consistent with the README's own
stated tradeoff. The salience-driven arms are *cheaper* than D25 (1.25-1.67x) because they throw
away the boilerplate, which is the same fact as Finding 4 seen from the cost side.
