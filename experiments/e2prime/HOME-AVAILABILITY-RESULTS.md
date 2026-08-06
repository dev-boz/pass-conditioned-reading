# Home availability without the oracle — archive scan + own-scaffold probe (2026-07-29)

**Status:** probes and archive measurements, `gate_legal:false`, frozen weights, $0. Nothing here
is pooled with a gate. Instruments: `scan_home_availability.py` (no GPU, re-reads committed
archives) and `stagea_p1_probes.py --probe p1f` (new cells, fresh seeds 11–20). Artifacts:
`runs/stageA_chain_gate/_probe_p1/home_availability_scan.json`, `.../p1f_{student,qwen7b}.json`,
`runs/stageA_chain_gate/p1f.log`.

## Plain-language summary

P1b showed that the student records well when we *hand it* an entry the new fact belongs in, and
records almost nothing when we don't. That was measured with hand-written states, so the obvious
objection was: fine, but the student never builds those entries for itself. This session checked
that against the real runs instead of hand-written states.

It does build them — more than expected. At the fourth pass of every run, the compressed view
happens to show a small module with a single line reading `RECONCILIATION_ADDER_CENTS = 1365`,
and in 8 of 11 runs the student wrote that number into its state right there, during a pass whose
instructions tell it *not* to chase specifics. So one of the two numbers the final question needs
was captured early, unprompted, in most runs, and it was still there at the end in 6 of 11.

The other number was not, and the reason is now specific. It is also visible in Phase A — pass 2
shows the whole surcharge table, with `23: 988` as one row among twenty-four. The student
summarized that table to its range ("24 surcharge rates (10–988 cents)") in most runs. The digits
988 reached the state 5 times out of 11; the fact that 988 is *the value for region 23* reached it
once. Same model, same rubric, two passes apart: a number sitting on its own line survives 8/11,
the same kind of number sitting in a table row survives 1/11.

So the blocked joint is narrower than "recording." The student records. It cannot pull one row out
of a table without dissolving the row into a summary — and a summary of a lookup table is exactly
the thing that cannot answer a lookup.

Then the probe. We had the model build its own scaffold and fill its own homes, to see whether
last session's result survives without hand-written states. It does not, and the failure is more
useful than a pass would have been. The student builds good homes at pass 4 — 8 of 10 fresh
seeds, one of them reading `RECONCILIATION_ADDER_CENTS = 1365` with the name attached. At pass 26
it then fills them **zero** times out of ten, while the hand-written state gets filled 5 times.
Reading the raw outputs shows where the work went: the pass-26 view is 94% auto-generated helper
boilerplate and 6% the module that matters, and the model spent every edit faithfully recording
the boilerplate.

That reverses the picture. The hand-written state worked last session not because it *had* homes
but because it had **nothing else to match** — its other entries all said "details deferred". A
real scaffold covers every module in the document, so it manufactures exactly the competitors that
soak up the edit budget. The model is not failing to record. It is recording the wrong 94%, and
the instructions it was trained on genuinely do not tell the two apart.

The second finding is about waste. Across the runs, half of the student's edits in the detailed
phase land on entries the current view says nothing about, and a quarter of all its rewrites
replace an entry with byte-identical text — 322 edits that changed nothing. Ten percent overwrite
an unrelated entry to house new content, which is how facts get destroyed. In one run the student
deleted an entry holding both the surcharge range and the adder, at the exact pass that was
showing the surcharge table.

---

## 1. Non-oracle target-fact lifecycle (22 archived draws × 31 passes)

Every archived chain draw, both arms, tracked per pass. Denominators inline; `LOST` = entered the
state and was gone by the final state.

| | student (n=11) | floor (n=11) |
|---|---|---|
| adder value `1365` ever recorded | **8/11** | 0/11 |
| …still in the final state | 6/11 | 0/11 |
| …first seen in Phase A (k≤6) | **8/11** | 0/11 |
| fn name `compute_line_surcharge` ever | 2/11 | 0/11 |
| mapping `23→988` ever | 3/11 | 0/11 |
| relation | 0/11 (audited matcher) | 0/11 |

Per-draw first-appearance: adder at **k=4 in every one of the 8** student draws that got it
(s8, s9 recorded it at k=4 and lost it later). Mapping: k=2 once (s3), k=12 twice (s2, s5).

**Instrument check.** This scan's flags are looser than the audited matcher, so every final-state
flag was cross-checked against `analyze_chain_gate.rescore()`. They agree exactly: mapping 3/11,
adder 6/11, relation 0/11. The 0/28 relation headline is unchanged.

**What it overturns.** Lever 5's premise as written — "Phase-A scaffold passes never create a
home for later tiles" — is too strong. For the adder they do, at 8/11, without oracle help and
against a rubric that says not to chase specifics. What Phase A fails to build is a home that
preserves a *binding* (§3).

## 2. Module-home availability, all (pass, module) pairs

For each pass, for each module the view shows, did the state already hold an entry naming it?

| arm | scope | home before | present after \| home | present after \| NO home |
|---|---|---|---|---|
| student | all pairs | 1023/2332 | 930/1023 = 0.91 | 1168/1309 = 0.89 |
| student | Phase B only | 1023/1166 | 930/1023 = **0.91** | 71/143 = **0.50** |
| student | target modules | 12/44 | 12/12 = 1.00 | 14/32 = 0.44 |
| floor | all pairs | 53/2332 | 53/53 = 1.00 | 98/2279 = 0.04 |

The all-pairs row is confounded and should not be quoted: Phase A adds an entry per module
(§4), so "present after" is near-ceiling regardless. **Phase B is the honest comparison** —
0.91 with a home vs 0.50 without. Home availability tracks persistence in the real runs, in the
same direction P1b found with oracle states, at about half the effect size.

## 3. The Phase-A capture contrast — the sharp result

Both operands are visible in Phase A, two passes apart, at comparably low state pressure:

- **pass 2** shows the full `REGION_SURCHARGE_CENTS` table; `23: 988` is one row of 24.
- **pass 4** shows `RECONCILIATION_ADDER_CENTS = 1365` on its own line in a small module.

| student, n=11 | captured at that pass |
|---|---|
| adder name at k=4 | 8/11 |
| adder **value** at k=4 | **8/11** |
| table named at k=2 | 3/11 |
| digits `988` present at k=2 | 5/11 |
| **`23→988` binding at k=2** | **1/11** |

Two-sided Fisher, scalar vs binding: **p ≈ 7.5×10⁻³**. (Adder 8/11 vs floor 0/11:
p ≈ 1.0×10⁻³. Digits-present 5/11 vs bound 1/11: p ≈ 0.15, n.s. — the digits/binding gap is
suggestive at this n, the scalar/table gap is not.)

The digits arrive without the binding because the table is compressed to its range: entries read
`24 surcharge rates (10-988 cents), NOT derived from distance/zone`. 988 is retained *as the
maximum*, not as region 23's value. This is the 07-26 "lossy Tier-1 summarization" attribution,
now with a within-model, within-phase, non-oracle contrast that rules out phase, state pressure,
home availability, and scale as the explanation.

**Consequence.** The demand repair the ledger already lists (relation-demanding rubric) does not
cover this. A rubric that says "record what each function computes" still permits
`24 surcharge rates (10-988 cents)`. The repair has to demand **key→value bindings survive
compression** — i.e. the queried row, or the whole table, never the range.

## 4. Op disposition — where the edit budget goes

| arm | phase | applied ops | breakdown |
|---|---|---|---|
| student | A | 1051 | ADD 1012 (96%), REPLACE off-topic 39 (4%) |
| student | B | 1510 | REPLACE off-topic 769 (51%), REPLACE into-home 483 (32%), ADD 258 (17%) |
| floor | A | 103 | ADD 93 (90%), NO_CHANGE 10 (10%) |
| floor | B | 2504 | ADD 2482 (99%), NO_CHANGE 22 (1%) |

Of the student's 1,252 Phase-B REPLACEs: **322 (26%) rewrote an entry to byte-identical text**,
and **121 (10%) were clobbers** — an entry about a module the view was *not* showing, overwritten
with content about one it was.

The floor never REPLACEs (99% ADD). The REPLACE bias is trained-in, confirmed without oracle.

**Hand-read** (working mode: totals are pre-filters). Eight sampled Phase-B off-topic REPLACEs:
four were byte-identical no-ops; one was a slot repurposing (an entry about
`routing/cursor18.py` overwritten with `schema/record42.py` content); and one is the find of the
scan —

> `student_s7`, pass 12, target entry `S24` before:
> `24 surcharge rates (10-988 cents), NOT derived from distance/zone; REGION_SURCHARGE_CENTS
> (fulfillment/line_quote.py): 1365 cents (fixed reconciliation adder ...); CARRIER_FU…`
> replaced with: `STAGE_ORDER_CONFIG (queue/pipeline.py): 6 stages …`

At the pass showing the surcharge table, the student destroyed the one entry holding both the
surcharge range and the adder. Note also that the destroyed entry was *already* mis-bound — it
attributes `REGION_SURCHARGE_CENTS` to `line_quote.py` and gives it the adder's value. The same
binding failure as §3, and the same family as P1e's `S2: 1365`.

## 5. P1f — own-scaffold fill (fresh seeds 11–20)

New cells in `stagea_p1_probes.py`. The model scaffolds a Phase-A view itself, then fills the
pass-26 tile into the state **it** built, paired seed-for-seed. No oracle in the contrast: `h1_p4`
sees the target module, `h1_p2` does not, so the p2 arm is a no-home control the model generated
for itself. `ctrl8_confirm` re-runs P1b's oracle cell at fresh seeds — the confirming run owed
under the three-tier rule.

### 5.1 The student builds good homes and then ignores them

| cell (student, n=10) | target home built | adder in state after | relation applied |
|---|---|---|---|
| `h1_p2` (scaffold pass 2) | 0/10 | 0/10 | 0/10 |
| `h1_p4` (scaffold pass 4) | **8/10 dedicated** (+1 list-mention) | 5/10 | 0/10 |

The pass-4 scaffold result replicates the archive (§1, 8/11) on fresh seeds and with a stricter
test. These are real homes, well bound — seed 19 wrote three of them, including
`S17: GROUP 87 (fulfillment/line_quote): RECONCILIATION_ADDER_CENTS = 1365 (Q3 compliance,
RFC-2231)`.

Then, filling the pass-26 tile into those same states:

| fill cell (student, n=10) | **acquired** 1365 | carried over | lost | relation |
|---|---|---|---|---|
| `h2own_p4` (own scaffold, home present) | **0/10** | 4 | 1 | 0/10 |
| `h2own_p2` (own scaffold, no home) | **3/10** | 0 | 0 | 0/10 |
| `ctrl8_confirm` (oracle homes) | **5/10** | 0 | 0 | 3/10 |

Scoring `applied.adder` alone would have read h2own_p4 as 4/10 — that is **carryover from the
scaffold pass, not fill**. Acquisition (in post, not in pre) is the honest metric and it is zero.

**The own-scaffold hypothesis fails, and the no-home arm beats the home arm.** That is the
opposite of the P1b prediction and it is not noise — it is mechanical, and the hand-reads show
why.

### 5.2 Why — the view's bulk outcompetes the home

The pass-26 tile is five module sections: `fulfillment/line_quote.py` is **172 of 2,981 tokens
(5.8%)**. The other **94% is auto-composed helper boilerplate** (`defines helpers: …` plus
`(i%40, weight>0.583)`-style bodies).

The trained policy is REPLACE-into-the-semantically-matching-entry. Given a state whose entries
are per-module helper lists, the matching entries for 94% of the view are the boilerplate entries
— so that is where the edit budget goes. Verbatim, seed 13, which had built a clean home at S7:

> state `S7: LINE_SURCHARGE/QUOTE: line_quote.py imports REGION_SURCHARGE_CENTS from
> pricing.region_tables — fixed reconciliation adder applied to every audited line`
> output at pass 26 (all 3 ops): `REPLACE S8 "validate_cursor, compact_ledger, …"
> "validate_cursor (i%40, weight>0.583), compact_ledger (i%39, weight>0.294), …"`

Seed 19, with three good homes and the value already in S17, spent all 7 ops rewriting the S1/S2
overview entries. Seed 17 spent its single op on S1.

The oracle `ctrl8` state gets filled precisely because it is a **clean field**: 8 short entries,
five of them inert (`details deferred`), three about the target identifiers. The view's 94%
boilerplate has nothing to match, so the only available matches are the target homes.

**This corrects last session's headline.** P1b's "home availability is the recording variable" is
too simple. The operative variable is home availability **with competing matchable content
removed** — and removing the competition is an artifact of the oracle state, not a property a
real Phase-A scaffold can have, because a real scaffold covers every module the document has.
The 07-28 reframe of the crowding step survives (the 155-entry state's home was buried), but the
burial is by *competition for the edit budget*, not by state size as such.

### 5.3 The confirming run passes (relation), with one caveat (adder)

| ctrl8 oracle cell | seeds 1–10 (P1b) | seeds 11–20 (P1f) | two-sided Fisher |
|---|---|---|---|
| applied relation | 4/10 | **3/10** | p = 1.00 |
| applied adder | 9/10 | **5/10** | p = 0.14 |

The relation-fill rate replicates on fresh seeds. Under the three-tier rule the student's
guard-clean relation recording into a matching home moves from *isolated success* to **replicated
mechanism** — it reproduced under a named ablation with fresh pre-registered draws and
artifact-visible provenance. It is still not a *demonstrated capability* (no pre-registered rate
vs floor).

The adder rate is the softer half: 9/10 → 5/10 is not significant at n=10 but it is a wide gap,
and it means P1b's 8–9/10 should be quoted as "high, ~5–9/10 across seed blocks", not as 9/10.
The determinism-duplicate note in `P1-PROBE-RESULTS.md` reading 4 is now discharged.

### 5.4 Untrained 7B — same failure, one arm inconclusive

| cell (qwen7b Q4, n=10) | target home | **acquired** 1365 | relation | op format (valid/candidate) |
|---|---|---|---|---|
| `h1_p2` | 0/10 | — | — | 200/200 |
| `h1_p4` | **10/10** | **0/10** | 0/10 | 111/252 |
| `h2own_p4` | 10/10 | 0/10 | 0/10 | **15/67 — collapsed** |
| `h2own_p2` | 1/10 | **0/10** | 0/10 | 44/46 |
| `ctrl8_confirm` | 9/10 | **6/10** | **0/10** | 48/60 |

Three clean readings and one that must be discarded:

1. **Structure is promptable, recording is not** — replicated at fresh seeds. The 7B builds a
   home for the target module in **10/10** scaffold draws but writes the adder value **0/10**,
   where the trained student writes it 5/10. P1e's split holds.
2. **Relation-writing stays training-only.** 7B relation 0/10 in every cell including the oracle
   one it fills 6/10. The inverse-GATE-3 dissociation replicates on fresh seeds.
3. **The 7B does not fill its own scaffold either** — `h2own_p2` acquires 0/10 with the op format
   intact (44/46 valid), so that zero is real.
4. **`h2own_p4` is inconclusive and is not evidence.** The format collapsed: the 7B emitted bare
   numeric ids (`REPLACE 15 "module: cache/digest68.py"`, `ADD 1:`) instead of `S`-prefixed ones,
   so 52 of 67 candidate lines were rejected before any content question arose. Per the 07-26
   arbitration §6 quantization caveat and the P7 protocol-transfer rule, this cell says nothing
   about home-filling. Notably the format held in exactly the cells whose state carried clean
   `S1…S8` ids and collapsed where the state was its own `S1: module: …` output — the id
   presentation appears to cue the format, which is a probe hazard worth remembering.

Hand-read of the 7B's oracle fill (seed 15) shows the P1e binding pathology again, in a milder
form — it wrote `RECONCILIATION_ADDER_CENTS = 1365` into **both** S2 and S3, overwriting the
`compute_line_surcharge` home with a duplicate of the adder, and stripped S1 to
`REGION_SURCHARGE_CENTS[region_code]`. Name=value binding preserved this time; entry identity
destroyed.

## 6. Synthesis — what the mechanism actually is

Last session's statement was "home availability is the recording variable." Three of this
session's measurements do not fit it, and the correction is specific.

| state at the pass-26 fill | matching home? | competing matchable entries? | acquired 1365 |
|---|---|---|---|
| `ctrl8` oracle, 8 entries | yes, 3 of 8 | **no** — 5 inert "details deferred" | 5–9/10 |
| own `h1_p4` scaffold, ~11 entries | **yes, 8/10 dedicated** | **yes** — per-module helper lists | **0/10** |
| own `h1_p2` scaffold, ~11 entries | no | partly (coarse/abstract) | 3/10 (via ADD) |
| 25-entry own prefix (P1a) | no | yes | 0/10 |
| 155-entry real state (07-26) | yes, buried | yes, heavily | 2/10 |

Home availability alone predicts row 2 should be the *best* cell. It is the worst. What separates
the rows is **competition for the edit budget**: the pass-26 tile is 94% auto-composed helper
boilerplate and 5.8% `fulfillment/line_quote.py`, so a state whose entries are per-module helper
lists offers a near-perfect semantic match for the 94% — and the REPLACE-into-the-matching-entry
policy dutifully spends every op there. The oracle `ctrl8` state works not because it has homes
but because it has **nothing else to match**.

Stated carefully:

> The trained recording policy matches view content to state entries and edits what matches. It
> is not failing to record — at pass 26 it records fluently and accurately. It records the
> **bulk** of the view (boilerplate helper signatures, annotated with their `i%40, weight>0.583`
> bodies) rather than its one load-bearing line. Nothing in the rubric distinguishes them: "record
> exact values, names and quotes" describes the helper weights perfectly.

This is the project's own P7 relevance fork, arriving at the RECORD joint with a mechanism
attached, and it lands on top of §3's finding that the one row the chain needs is precisely the
kind of content the policy compresses away.

**What it does to the lever board:**

- **Lever 5 (home-building) needs a second half or it will not work.** Building homes is already
  happening — 8/11 in the archives, 8/10 on fresh seeds, 10/10 untrained at 7B. Filling them does
  not follow, because a Phase-A scaffold that covers every module necessarily manufactures the
  competitors. Home-building without a salience mechanism is not sufficient; on this evidence it
  is not even the binding constraint.
- **Relevance/salience is promoted from a P7 loose end to the RECORD joint's live blocker.** The
  demand repairs list needs an item: the recording demand must distinguish load-bearing content
  from bulk, and the fixture must stop being 94% filler if we want to measure anything else.
- **§3 adds a separate demand repair:** key→value bindings must survive compression. A
  relation-demanding rubric does not imply it — `24 surcharge rates (10-988 cents)` satisfies
  "record what this module holds" and destroys the lookup.
- **Lever 10's record-side motivation stays dead** (a flat text state records fine, §5.3), and
  lever 13 (budget policy) gains support it did not have: 26% of Phase-B REPLACEs are byte-identical
  no-ops, so the budget is not merely tight, it is being spent on nothing.

## 7. Caveats

- §1–§4 re-read committed archives; no new sampling, so they inherit those runs' n=11 per arm and
  their temperature. They are observational, not a designed contrast — except §3, which is a
  within-draw comparison of two passes and is the closest thing here to a controlled test.
- §3's two passes differ in more than granularity (different modules, k=2 vs k=4, view length
  1093 vs 1502 tok). The granularity reading is the most parsimonious, not the only one; P1f's
  h1_p4 cell and a matched probe on a *scalar planted at pass 2* would settle it.
- The `home_before` / `present_after` test is string matching on module path and stem. An entry
  that holds a module's content without naming it (`Fixed reconciliation adder …`) scores as
  no-home and as off-topic. §4's off-topic rate is therefore an **upper** bound and §2's
  home-availability an **under**-count; the hand-read is what the reading rests on.
- Nothing here is a replication of P1b: different instrument, different (non-oracle) states.
  It is convergent evidence for the same mechanism, at a smaller effect size.
