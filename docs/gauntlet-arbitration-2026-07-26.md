# Gauntlet Arbitration — Stage-A chain gate (2026-07-26)

**Inputs:** `docs/GAUNTLET-STAGEA-2026-07-21.md` (the prompt) → `docs/gauntlet-25-7-26.md` (the answers).
**Method:** the `docs/gauntlet-arbitration.md` pattern — every checkable reviewer claim verified against
repo ground truth before it is allowed to move anything. A confident claim that contradicts archived
data loses to the data.
**Panel size:** 16 review blocks, but `ag-opus-4.6` and `deepseek-v4-pro-nim` are **byte-identical
submissions**, so the effective panel is **n=15** and their shared "native architecture first"
position is double-counted in any tally.

**Standing:** the Stage-A verdict (student 0/10, floor 0/10, ARCHITECTURE GATE) is **unchanged**.
What changed is the *attribution*, and two items in our own results doc are retracted below.

---

## 1. Verdict table

| # | claim | source | status |
|---|---|---|---|
| 1 | The close was never trained as QA; `ANSWER:` occurs 0× in 5,730 rows | composer-2.5-cursor, kimi-k3-qoder, mimo-2.5-pro-fb, mimo-2.5-oc | **CONFIRMED** |
| 2 | `pc_check.py` excludes closing rows from the training-health gate | composer-2.5-cursor | **CONFIRMED** (`train/pc_check.py:69`) |
| 3 | Teacher demonstrates all-or-nothing table recording | qwen-3.8-qoder, kimi-k3-qoder, deepseek-4-flash-oc, gemini-3.1-pro-agy, sonnet-4.5-kiro, devin-SWE-1.6-dc | **PARTLY CONFIRMED, mechanism corrected** (§3) |
| 4 | "Zero teacher rows show partial-table recording" | deepseek-4-flash-oc, qwen-3.8-qoder, gemini-3.1-pro-agy | **REFUTED** — 4.3% do |
| 5 | 24-op cap ≈ 24-entry table forces all-or-nothing | glm-5.2-nim (#1, high), gemini-3.1-pro-studio | **REFUTED** (§2) |
| 6 | Op grammar cannot express "record one row" | glm-5-kiro (high) | **REFUTED** (§2) |
| 7 | "3/10 recorded but 2/10 retained ⇒ 1 lost ⇒ RETAIN not clean" | deepseek-4-flash-oc, sonnet-4.5-kiro, ag-opus-4.6, qwen-3.8-qoder | **REFUTED** (§2) |
| 8 | Distilled 2-entry probe could not have held the function definition | gemini-3.1-pro-agy (high) | **REFUTED** (§2) |
| 9 | K=31 is out of distribution; training was K≤20 | agy-opus4.6, minimax-m3-fb, gemini-3.1-pro-studio | **REFUTED** (§2) |
| 10 | LoRA damaged the base model's reasoning | glm-5.2-nim (high) | **REFUTED** (§2) |
| 11 | "Compose fails at every scale, so it is representation-limited" | deepseek-4-flash-oc, ag-opus-4.6 ×2, mimo-2.5-oc | **REFUTED — decisively** (§4) |
| 12 | "~2/42 cross-family compose rate" | deepseek-4-flash-oc (high) | **FABRICATED** — no such denominator exists |
| 13 | "3/22 chain fires" | minimax-m3-fb | **MISSTATED** — but the substantive point stands (§4) |
| 14 | Training-state length OOD at close | agy-opus4.6, kimi-k3-qoder | **PARTLY CONFIRMED, quantified** (§3) |
| 15 | Temp-0 anchor "not shown" | ag-opus-4.6 ×2 | **REFUTED** — results doc lines 46/63; fair criticism of the *prompt*, not the record |

---

## 2. Adjudications — where the panel lost to archived data

- **Op granularity (5, 6).** Seed 2's `S26` holds **all 24 table pairs in one entry, 299 characters,
  one ADD op** (`runs/stageA_chain_gate/student_s2_t0.7.json`). `_ADD_RE` in `src/pca/editops.py:75`
  takes `(.+)` with `re.S` — arbitrary text. `ADD END: REGION_SURCHARGE_CENTS[23] = 988` is perfectly
  expressible. The 24-op cap never forced anything.
- **The "retention" contradiction (7).** Four reviewers conflated two different rows of the §5 table:
  *mapping* recorded is 3/10, *both operands* recorded is 2/10, retained 2/10, lost 0/10. The third
  draw recorded the mapping and never recorded the adder, so it never held both and nothing was lost.
  Internally consistent as written.
- **Distillation probe (8).** `S83` held `1365` **and** `compute_line_surcharge` together; the
  2-entry distilled state did contain the formula.
- **K distribution (9).** Bimodal: K=8 (prose) and K=21–38 (code). **217 rows survive the length gate
  at exactly K=31**, 3,204 at K≥21. The "~20.7 average" reviewers computed is an artifact of averaging
  a bimodal distribution.
- **LoRA damage (10).** Floor GATE-3 is 0/10 and the student is 1/10. Training improved it.

## 3. Adjudications — where the panel was right, with the mechanism corrected

**The close was never trained as the task it was scored on (1, 2).** All 277 closing rows carry
`closing_demand` = *"From your final state alone, write the analytical brief it supports…"*. The
string `ANSWER:` appears **0 times** in 5,730 rows. The eval close appends an `ANSWER: <integer>`
demand to the trained system prompt. And `train/pc_check.py:69` filters `stage != "closing"`, so the
only stage the verdict depends on was never inside the health gate. This is the panel's strongest
find and all three sub-claims verify exactly.

**Teacher recording policy, measured (3, 4).** Across 559 table-mention events in the teacher data:

| mode | share |
|---|---|
| named only / lossy summary (0 pairs recorded) | **61.4%** |
| full transcription (≥95% of pairs) | 34.3% |
| partial / selective | **4.3%** |

So partial recording is **rare, not absent** — the strong "zero examples" claim is refuted, and the
behaviour can be up-weighted rather than invented. The dominant teacher mode is *lossy summary*, not
exhaustive transcription, and that is precisely the student's dominant failure (table named 7/10,
mapping recorded 3/10). The student faithfully copies the teacher's **modal** policy.

**Length-gate damage — unnamed by the panel, and the largest new confound.** The `seq_len=10240`
gate dropped 1,446 of 5,730 rows, all code:

| stage | dropped |
|---|---|
| verbatim | **965 / 1,855 (52%)** |
| closing | 103 / 277 (37%) |
| integrate | 370 / 1,695 (22%) |
| scaffold | 8 / 1,903 (0.4%) |

The `verbatim` rubric is the *only* one that demands "exact values, names and quotes" — and half its
rows never trained. Surviving closing rows have median state 1,268 tok; only 22/174 (13%) reach the
eval's ~7,700-tok regime. So the state-length OOD claim (14) is real but overstated: the eval close
sits in a sparse upper tail, not outside the distribution.

## 4. The scale question — resolved, against the panel's consensus

Four reviewers argued compose fails at every scale, so the text state is at fault and the native
architecture is the only move. This conflates the **compose primitive** with the **end-to-end
conjunction**. The 21/22 and 1/10 figures they cite are chain composes from a model's own noisy
self-built state. On the *identical frozen 8-entry seeded state*
(`stagea_companion_checks.py:16` imports `compose_gate.best_case_state`, explicitly not rewritten):

| model | legacy frame | chain frame |
|---|---|---|
| Qwen2.5-1.5B floor (f16) | 0/10 | 0/10 |
| Qwen2.5-1.5B trained student (f16) | 1/10 | 1/10 |
| **Qwen2.5-3B untrained (f16)** | **7/10** | **9/10** |
| Qwen2.5-3B untrained (Q4_K_M) | 6/10 | 7/10 |
| **Qwen2.5-7B untrained (Q4_K_M)** | **10/10** | **10/10** |

3B vs the trained 1.5B: Fisher exact **p ≈ 5×10⁻⁴**. 7B vs the same: **p ≈ 6×10⁻⁵**.

**Compose from a clean flat-text state is scale-limited, not representation-limited.** The claim that
text-state edit ops "strip relational binding by construction" is wrong: a 7B binds
`table[23] + adder` out of prose 22/22 times. Quantization only *hurts* (3B f16 > 3B Q4 in both
frames), so the 7B Q4 number carries no precision caveat.

This also repairs the archived P7 GATE-3 number: it was reported 4/4, but pooled a temp-0 anchor with
3 sampled draws, which this project's own rules forbid. It is now 10/10 sampled with the anchor
separate, at n=11, on the current harness.

minimax-m3-fb's "3/22" is wrong as stated (`CONSOLIDATED-FINDINGS.md:335` explains the two trios are
different populations overlapping only at Llama-70B s9), but its substantive point — the chain fired
blind and untrained in three families and was never re-tested under the strict harness — was the most
decision-relevant thing any reviewer said.

---

## 4A. THE HEADLINE: the relation was never recorded, so the chain was unpassable

Answering `compute_line_surcharge(23)` needs **three** recorded facts: the mapping `23→988`, the
adder `1365`, and **the relation** `compute_line_surcharge(region) = REGION_SURCHARGE_CENTS[region]
+ RECONCILIATION_ADDER_CENTS`. The §5 attribution tracked only the first two and called that
"RECORD both operands."

Measured across every archived final state in every arm:

| arm | names `compute_line_surcharge` | records the relation |
|---|---|---|
| 1.5B trained student | 2/11 | **0/11** |
| 1.5B untrained floor | 0/11 | **0/11** |
| 3B untrained | 0/6 | **0/6** |

**0 of 28 states ever recorded the relation.** Seed 2's `S83` — the entry the results doc credits
with holding an operand — reads:

> `S83: GROUP 75 (fulfillment/line_quote.py): from pricing.region_tables import
> REGION_SURCHARGE_CENTS; RECONCILIATION_ADDER_CENTS=1365; compute_line_surcharge, quote_line`

The function is a bare name in a list. Contrast GATE-3's seeded equivalent, which states the
relation outright: *"compute_line_surcharge(region_code) **returns** REGION_SURCHARGE_CENTS[
region_code] **+** RECONCILIATION_ADDER_CENTS."* That single difference is the whole GATE-3 gap.

**Consequences.**

1. The 0/10 verdict is attributable to **RECORD**, not COMPOSE. The in-situ compose joint was never
   actually exercised: no state ever held its inputs.
2. When the 3B answers **988** from these states it is reasoning *correctly* — nothing in the state
   says anything must be added. The cross-model 0/2 result is not evidence about compose.
3. **Why no prompt would ever have produced it.** The `verbatim` rubric asks the model to "surface
   exact **values, names and quotes**" — values, names, quotes. Never behaviour, semantics, or
   relations. The teacher was never asked to record what a function *does*, so it never demonstrated
   it, so the student never learned it. Same defect class as §3 and §8.1: **every element the chain
   required was something no prompt ever asked for.**
4. This lands on the project's own flagged-unresolved **P7 relevance fork** (capability failure vs
   correct editorial omission). A model instructed to record values/names/quotes and then scored on
   a formula is being marked down for compliance. Until the recording demand names relations, this
   fixture cannot separate the two.
5. The `distilled` probe's lone success is now explicable: at 2 entries the 1.5B *inferred* the
   relation ("surcharge = base + adder" is a natural reading) rather than reading it. Inferable,
   never recorded. n=1.

**This does not un-gate the instantiation** — 0/10 is still 0/10, and a protocol that fails to
record the load-bearing relation is a real failure. But it is a **RECORD/demand failure with a
concrete fix**, not the architecture failure the verdict was read as.

## 4B. WHY the relation was never recorded — schema lock-in

**Pass 26 is the only pass in the 31-pass schedule whose VIEW contains `def compute_line_surcharge`
with its body.** Every other appearance — including Phase-A — is the compressed line `defines
helpers: compute_line_surcharge, quote_line`, body stripped by the compressor. The model gets
exactly one shot at the relation, at pass 26, under the `verbatim` rubric, with **155 entries
already in state**. Its five applied ops there were `REPLACE S102 "GROUP 92…"`, `REPLACE S103
"GROUP 93…"` — grinding its own inventory while the pricing code sat unread.

Graduated probe, identical tile + rubric + model, varying only the prefixed state (seed 2's own
pass-26 entries, unfiltered, in order):

| state entries | relation emitted | names the fn | adder |
|---|---|---|---|
| **0** | **7/10** | **9/10** | 5/10 |
| 25 | 0/10 | 0/10 | 0/10 |
| 50 | 0/10 | 0/10 | 0/10 |
| 100 | 0/10 | 0/10 | 2/10 |
| 155 | 2/10 | 3/10 | 2/10 |

A **step, not a slope** — collapse between 0 and 25, flat thereafter (2/10 vs 0/10 is Fisher
p≈0.47, noise). So "state size crowds out reading" is **wrong**. Hand-reading the outputs gives the
real mechanism:

- at 0 entries the model *describes what it sees*, relation included — but its ops are `REPLACE`
  against an empty state, malformed, and the strict guard would block all of them;
- at 25 entries it emits a well-formed `REPLACE S149 "GROUP 27 …"` folding the view's new functions
  into an existing group-listing entry.

**The state supplies a schema and the model assimilates new content into it.** With 155 entries of
`GROUP N: helper names`, the pass-26 tile is read as more helper names; `compute_line_surcharge`
becomes an item in a list and its computation is never recorded, because the established shape has
no slot for "what a function computes."

This subsumes three previously separate findings — all-or-nothing table recording, fabricated range
summaries, and the missing relation are one behaviour: **new content is coerced into the shape of
what the state already holds.** The teacher's modal policy (§3) is what set that shape.

Note the trap at both ends: at 0 entries the model notices the relation but cannot record it; at ≥25
it can record but no longer notices. Neither end gives both.

**Uncomfortable corollary.** "Training moved every component" (op-following 2.4→7.0, state
725→7,686 tok) reads as progress, but a larger, more uniform state is a *stronger* schema. The
improvement and the recording failure may be the same mechanism.

**CONTROL RUN — schema lock-in REFUTED.** Same tile, same rubric, 25-entry prefixes about the same
unrelated fixture modules, differing only in shape:

| 25-entry prefix | relation | names the fn |
|---|---|---|
| `GROUP N: helper names` (student's own) | 0/10 | 0/10 |
| computation-stating (`… defines fn(items, opt) which returns …`) | 1/10 | 2/10 |
| *(empty state, for reference)* | *7/10* | *9/10* |

1/10 vs 0/10 is Fisher p≈0.5. The shape of the state does **not** matter. **Any non-empty prefix
suppresses recording of new view content.** The schema reading above is withdrawn; what survives is
the bare effect: *empty state 7/10 → any 25-entry state ~0/10.*

**Three live explanations, not yet discriminated:**

1. **Training artifact.** The student was trained on rows that always have a state and whose teacher
   response is mostly REPLACE; the P-C bar rewarded op-type agreement. It may have learned
   "state present → maintain it" as a policy.
2. **Rubric effect.** Both operative rubrics instruct assimilation. `integrate`: *"integrate this
   view's content **into the entries it belongs to**; consolidate overlapping entries."* `verbatim`:
   *"REPLACE to surface exact values … **NO_CHANGE if this view adds nothing your state needs**."*
   Neither invites ADD for genuinely new material. The prompt may simply be telling the model to do
   what it does.
3. **Structural.** A flat accumulating text state suppresses ingestion in a small model regardless
   of training or prompt.

**Two cheap controls discriminate, both $0 on frozen weights:**
- same probe on the **untrained floor and untrained 3B** — if untrained models keep reading with a
  state present, (1) is implicated and it is fixable in training;
- same probe with a rubric that **explicitly licenses ADD for content with no home in the state** —
  if recording returns, (2) is implicated and it is fixable in the prompt.

Only if both come back negative is (3) — the architectural reading, and the first measured support
for lever 10 in this document — the surviving explanation.

## 5. RETRACTIONS from our own record

1. **`STAGEA-CHAIN-GATE-RESULTS.md` §5, finding 1 and §5.3 bullet 1** — *"whole-entry edit-op
   granularity: the task needs one row out of 24 and the instantiation can only offer all or none"*
   and *"A 3B would face the same granularity."* **Retracted.** The table rides in one op and one row
   is expressible (§2). The constraint is what the teacher demonstrated and what the length gate
   deleted. This removes one of the two pillars motivating lever 10; the flat-state retrieval pillar
   survives.
2. **`STAGEA-CHAIN-GATE-RESULTS.md` §5 attribution emphasis.** RECORD is over-blamed. Recording put
   the table into 8/11 states; the trained *close* then discarded it (§6).
3. **`docs/DISCO-NATIVE-ARCHITECTURE.md` §3 / §5** rest partly on "the op-DSL strips the relational
   binding." **Refined, not retracted** (see §4A). The *grammar* does not strip it — GATE-3's text
   entry carries the formula fine and a 7B composes from it 22/22. But the empirical claim survives
   in a sharper form: **this student, from this teacher, records structure (imports, constants,
   function-name lists) and never semantics (what a function computes) — 0/28 states.** That is a
   demand-and-data failure, not a property of the DSL, and it is fixable without changing the
   representation.

### Corrections made during this arbitration (in-session, disclosed)

Two claims were asserted and then withdrawn on further measurement. Both errors were the same shape
— treating a joint as *tested* when its inputs were absent:

- *"Compose is scale-limited, not representation-limited"* (from GATE-3 alone). Over-read: GATE-3
  uses a clean synthetic state and does not predict in-situ behaviour.
- *"In-situ compose fails and is scale-resistant"* (from the cross-model 3B close, 0/2). Withdrawn:
  the states lacked the relation, so the probe measured nothing about compose. **§4A supersedes.**

What survives from both: the GATE-3 ladder itself (1.5B 1/10 → 3B 9/10 → 7B 10/10) is sound, and
the compose primitive is genuinely scale-limited. In-situ compose remains **untested** — it cannot
be tested until a state exists that holds all three facts.

## 6. New results generated during arbitration (all $0, frozen weights, non-verdict)

- **`traindemand` probe** (literal trained close: bare `CLOSING_SYSTEM` + `closing_demand`, no
  question, no `ANSWER:` scaffold; 4096-token budget). **8/11 states name the surcharge table; 0/11
  briefs do.** 0/11 briefs contain `988`. The brief spends its budget enumerating ~99 numbered helper
  groups and never reaches the one entry that is not a numbered group. *Under the demand it was
  trained on, the close strips the specifics the state was holding.* First run at 1200 tokens was
  discarded — 11/11 truncated, uninformative.
- **`exactask` probe** (same question, exact-value demand, no `ANSWER:` scaffold). **0/10**, 9/11
  budget-clean. Seed 2 moved from 86 (decoy) to **1365** (a real operand), spontaneously quoted its
  own state, and never located `23→988`. A **third non-forcing** close negative alongside `retrieve`
  and `queryfirst` — it reaches the forcing probes' conclusion without oracle filtering.
- **Untrained 7B chain smoke (n=1):** applied 5.6 ops/pass, **18/31 passes applied nothing**,
  validity 0.61, final state **420 tok — smaller than the untrained 1.5B floor's 725**. Per P7's own
  reading rule, a weak op-follower's zero is protocol transfer, not architecture evidence.
  **CAVEAT, do not skip:** n=1 **and Q4_K_M**. The untrained **3B f16** chain battery run immediately
  afterwards is a *strong* op-follower (validity ≈1.00, hitting the 24-op cap, ~2.3K state by pass 8),
  so op-following is not monotone in scale and **quantization is a live suspect for the 7B's op-format
  collapse** — quantization already cost 2/10 on 3B compose. Any claim that "untrained 7B cannot run
  the protocol" needs a 7B f16 or 7B Q8 rerun before it is load-bearing. 7B f16 does not fit the
  1080 Ti at 24K ctx; Q8 (~7.5GB) probably does.

**The dissociation this exposes is the session's main finding:**

| | protocol-following | compose from clean state |
|---|---|---|
| 1.5B untrained | 2.4 ops/pass, 725 tok | 0/10 |
| 1.5B **trained** | **7.0 ops/pass, 7,686 tok** | 1/10 |
| 3B untrained (f16) | strong follower, validity ≈1.00 (battery running) | **9/10** |
| 7B untrained (Q4) | 5.6 ops/pass, 420 tok, validity 0.61 — quantization suspected | **10/10** |
| 3B/7B **trained** | **never tested** | **never tested** |

Training bought protocol-following; scale bought composition; **no run has ever had both**. The one
cell that would answer the architecture question is empty. No reviewer reasoned from this, because
the GATE-3 scale ladder was not in the prompt they were given.

## 7. Prior art — verified

Papers are real; the quantitative claims attached to them are frequently embellished, the same
pattern as the June arbitration.

- **MemWalker** — Chen, Pasunuru, Weston, Celikyilmaz, **2023** (arXiv 2310.05029), not 2024. The
  "tree-based pruning works at 7B" claim is unverified and inconsistent with its 70B-class setup.
- **HippoRAG** (Gutiérrez et al. 2024) real; the "small models + query-indexed memory beat
  long-context large models" comparison attached to it is unverified.
- **RAPTOR** is 2024 (Sarthi et al.), not 2020. **Unlimiformer** is 2023, not 2024.
- **Not named by any of the 15 reviewers, and closer to our goal than our own prior-art list:**
  - **BooookScore** (Chang et al., **ICLR 2024 oral**, arXiv 2310.00785) — compares hierarchical
    merging against incrementally updating a running summary, and finds incremental updating gives
    *lower coherence but higher detail*. Error taxonomy includes causal omissions and salience errors.
    Crucially, **neither workflow re-reads the source and neither goes coarse→fine**, so it is not
    this architecture; but it is a published, human-validated measurement of the exact
    coherence/detail tradeoff our schedule claims to beat, and it supplies the baseline pair the panel
    unanimously said we lack.
  - **LoCoMo-Plus** (arXiv 2602.10715) — beyond-factual conversational memory via implicit
    constraints, scored by constraint-consistency with an LLM judge; code at
    `github.com/xjtuleeyf/Locomo-Plus`; already evaluated Qwen2.5/3 at 3B–14B. Its finding that
    BLEU/ROUGE/F1 carry **systematic length bias** is a live hazard for us: the student's state is
    7,686 tok against the floor's 725, so any length-sensitive metric would manufacture a result in a
    trained-vs-untrained comparison. **Ban length-sensitive scoring from all arms.**

## 8. Methodology rulings adopted

1. **Ask for the exact form you will score.** A training demand of "write the analytical brief"
   cannot be scored with `ANSWER: <integer>` exact match. Before any battery, the training demand,
   eval demand, and scoring form must be the same shape. A train/eval demand mismatch is an
   instrument defect to repair, never a lever and never evidence about the architecture.
2. **Closing rows go inside the health gate.** Whatever stage the verdict reads must be gated.
3. **Report what the length gate drops, per stage.** A silent 52% deletion of the one rubric that
   demands exact values is not a detail.
4. **Hand-read before believing a flag.** Held again this session: the first `traindemand` run was
   worthless (11/11 truncated) and the new prose scorer had two bugs that would have hidden correct
   answers. Both were caught by reading raw output, not by the flags.

## 9. Verification queue (not yet arbitration-verified)

- MemWalker's actual backbone size — asserted 70B-class from recall; the search did not confirm it.
- LoCoMo-Plus licence (not stated in the paper; check the repo before building on it).
- Whether `traindemand` would *ever* reach the pricing entry given unlimited budget — the mechanism
  says no, but 11/11 capped at 4096, so a single 8192-token draw should settle it.
