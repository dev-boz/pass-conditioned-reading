# P7 — Relevance control v2 (Reading A vs B) · PRE-REGISTRATION (before fixture change or run)

**Status:** DRAFT for maintainer sign-off; becomes binding when committed. No fixture-v2 code exists yet; no run has started.
**Date:** 2026-07-09
**Supersedes for interpretation:** RELEVANCE-CONTROL.md (v1), whose result was the pre-registered AMBIGUOUS branch — both tables Tier 0 in 5/5 seeds with **no positive control** and **singleton-module dilution**, so the null was uninterpretable. v1's build (matched axes, tiers, manual-confirmed scoring) is inherited unchanged; v2 exists to fix exactly the two defects v1 itself identified.
**Consumed by:** docs/E2PRIME-CRITERION.md §1 P-B and §4 (this control's branch outcome selects the E2′ consequence mapping; it must run on the untrained floor **before E2′ teacher data is constructed**).

## The question (unchanged)

The floor omits the arbitrary `REGION_SURCHARGE_CENTS` table under a neutral brief (0/6 draws). Reading A: recording-capability failure → E2′ justified. Reading B: correct editorial omission → training a model to record it is overfitting to the probe. v1 could not distinguish these because nothing in the fixture was *shown recordable* at table altitude (no instrument-sensitivity proof) and both planted tables sat in singleton categories that die at inventory level before content relevance can matter.

## The two fixes

### Fix 1 — In-fixture positive control (instrument sensitivity)

**PC = `STAGE_ORDER`**, a **small (5-entry)** behavior-governing structure in the **well-represented `queue/` category**: `queue/pipeline.py`, an ordered stage map consumed by `run_pipeline()`, which drives the codebase's end-to-end flow (intake → validate → transform → bill → report, as arbitrary-but-plausible stage keys). Probe-blind justification: the pipeline's stage order is the single most brief-worthy fact in a "what does this codebase do" brief — it is what the codebase *does*. No reference to, dependence on, or proximity to the surcharge probe.

Why a PC at this shape: v1 already established that **module/category inventory** is recordable on the floor (the briefs enumerate the ~15 categories and helper names — that altitude needs no new control). What was never shown recordable is a *specific named structure with a stated role*. PC is the cheapest such structure: small, central, behavior-governing, represented-category. If even PC fails Tier 1, the floor summarizes above structure altitude everywhere, and the fork is unresolvable at floor altitude (branch 3 below).

**Instrument sensitive ⇔ PC ≥ Tier 1 in ≥ 4/5 seeds.**

### Fix 2 — The matched pair, category-representation-matched (no singletons)

The v1 pair moves from singleton categories into the **same well-represented category** as sibling modules:

| | v1 (singleton) | v2 (represented, same category) |
|---|---|---|
| EVENT_DISPATCH (relevant) | `dispatch/router.py` | **`routing/router.py`** |
| DISPLAY_LABELS (arbitrary) | `ui/labels.py` | **`routing/labels.py`** (docstring: cosmetic labels shown next to each routed event in the activity feed) |

Same-category placement makes category representation *identical by construction* — the category's survival at inventory level is shared, so the contrast is carried by table content/role alone. All v1 matched axes inherited: same 24 real event-name keys, arbitrary non-derivable real-word two-token values, same size/surface form (str→str module-level dict + docstring + helper), same Phase-A chunk (state-pressure match), neither rule-compressible, neither OOD-hard. Only behavioral relevance differs, carried by context: `dispatch()` drives control flow; `label()` is cosmetic.

Named residual confounds (reported, accepted): (a) within-category competition — a brief line about the `routing/` category might mention one table and not the other for length reasons; mitigated because Tier 1 requires only a role mention, which is cheap for both. (b) PC-vs-pair size/centrality gap — PC is 5 entries and pipeline-central, the pair is 24 entries; a PC-pass therefore proves sensitivity at *structure* altitude, not "24-entry-table" altitude; this is why the outcome table below still contains an explicit judgment-flavored reading and why the arbitration is by pre-registered branch, not by narrative.

## Fixture v2 — generation discipline (probe preserved byte-identical)

The chain probe must be untouched (E2PRIME-CRITERION §3 requires the unchanged split unit). Rules for `gen_fixture.py` v2:

1. **Separate RNG stream for all new content:** every new draw (STAGE_ORDER keys/values, any new wording) comes from `random.Random(SEED + 1)`, consumed **after** the existing stream's draws, which are not reordered, added to, or removed. `REGION_SURCHARGE_CENTS`, `RECONCILIATION_ADDER_CENTS`, `CARRIER_FUEL_BP`, `EVENT_DISPATCH`/`DISPLAY_LABELS` contents, and all filler modules must be **byte-identical** to v1 (asserted, see guard 4).
2. **Placement:** the pair's module-path strings change (`dispatch/router.py` → `routing/router.py`, `ui/labels.py` → `routing/labels.py`) with contents otherwise identical; PC inserted as one new block at ≈ **0.35** (its own Phase-A chunk, distinct from the pair's chunk and from both fragments' chunks).
3. **Post-generation guards (asserted in the generator, printed to the run log):**
   - fragment-1, control, pair, fragment-2 block fractions within ±0.02 of v1 targets (0.22 / 0.45 / 0.62 / 0.68 / 0.75); mid-exclusivity (outside head/tail ~11%) maintained;
   - **pair still lands in the same seg/chunk** (the one-block insertion shifts indices; if a seg boundary splits the pair, the PC insertion index is nudged until the guard passes — the nudge rule is mechanical, not judgment);
   - `fixture_spec.json` v2 records: `ground_truth_answer` identical to v1 (**2353-equivalence assert**: table[23] and adder byte-equal), PC decl/table, new positions, and a `fixture_version: 2` field.
4. **Verification:** `verify_fixture.py` extended with the byte-equality asserts (probe fragments, control table, pair tables vs v1 spec values) and the guards above. The v2 scaffold is re-derived by the **frozen v2 compressor code** — the compressor is frozen as code + deterministic procedure; its outputs are re-derived per fixture version, never hand-edited (decision to be logged in DECISIONS.md on implementation).

## Protocol (frozen, v1-inherited)

- **Model:** the untrained floor, Qwen2.5-7B-Instruct Q4_K_M (llama.cpp), same build/config as v1.
- **Prompt:** the neutral brief, unchanged (P6-lineage; no append-only, no "record tables", no probe mention). Forcing-line audit per E2PRIME-CRITERION §2 applies.
- **Compressor:** frozen v2 code, scaffold re-derived on fixture v2 (above). Schedule unchanged; coupled Phase-A passes, warm.
- **Replication:** temp-0 (seed 42) + 4 sampled temp-0.7 seeds (1–4); per-seed, never pooled. State size reported per seed (v1 range was ~160–2,750 tok; the spread is part of the floor characterization).
- **Metric:** v1 tiers, manual-confirmed (auto verbatim-pair filter = pre-filter only). Tier 0 ignored / Tier 1 existence-or-purpose noted / Tier 2 ≥1 mapping recorded. "Recorded" = ≥ Tier 1.
- **Decisive attribution checks (manual):** decl strings (`STAGE_ORDER`, `EVENT_DISPATCH = {`, `DISPLAY_LABELS = {`), exact module paths (`queue/pipeline.py`, `routing/router.py`, `routing/labels.py`), shared key strings (`order.created`, …), handler/label value words, `run_pipeline`/`dispatch(`/`label(`. Generic mentions of the `routing/` or `queue/` *categories* do **not** count for any table (the v1 false-positive lesson, now sharper because the pair deliberately lives inside a filler category).

## Pre-registered outcomes (stated before any code or run)

| # | Floor result (per-seed, ≥4/5 bar) | Reading | Binding consequence (E2PRIME-CRITERION §4.1) |
|---|---|---|---|
| 1 | PC ≥T1 **and** relevant ≥T1 **and** arbitrary T0 | **B — the floor discriminates; the surcharge omission was editorial judgment** | Neutral-brief recording of arbitrary structure is NOT a training target; E2′ objective = need-conditioned recording + binding-carry; chain gate runs query-conditioned only; a student recording the arbitrary table under a *neutral* brief counts against the objective. |
| 2 | PC ≥T1 **and** relevant <4/5 at ≥T1 | **A — under-recording of brief-relevant structure despite proven sensitivity** | "Record brief-relevant structure" is a legitimate training target; chain gate may run neutral + query-conditioned arms. (If arbitrary ≥T1 while relevant <4/5 — an inverted result — treat as outcome 4.) |
| 3 | PC <4/5 at ≥T1 | **Fork unresolvable at floor altitude** (floor summarizes above structure altitude everywhere — v1's finding, now with the strongest legitimate candidate) | Query-conditioned framing becomes mandatory for all E2′ recording gates; Fork 1 moves to the trained student (E2PRIME-CRITERION §4.3). This is a complete, reportable conclusion — not a failure of the control. |
| 4 | Anything else (inverted, mixed, wide-spread) | **Ambiguous** | Report as-is; re-audit for residual confounds; do not force a read; fork carried open with branch-3 consequence (mandatory query-conditioning) as the conservative default. |

Note the asymmetry, inherited from v1: a null-on-both with a failing PC is branch 3, never "A confirmed." Reporting A requires the PC to have passed. This is the anti-laundering rule.

## Cost, scope, publication

Local llama.cpp on this box ($0 API; CUDA build cuts the 5-draw set to ~1–2 h). Does not run the battery, the chain gate, or any E2′ arm; does not touch the compressor code or the prompt; does not test retention. Nothing published; results surfaced for maintainer review with the raw transcripts and the per-seed tier table before any A/B/branch conclusion is recorded.

---

## RESULT (run 2026-07-10, fixture v2, 5 draws: temp-0 s42 + temp-0.7 s1–s4) — PRE-REGISTERED BRANCH 3: fork unresolvable at floor altitude (PC failed)

Battery: coupled Phase-A warm, neutral prompt, frozen v2 compressor on the v2 scaffold, Qwen2.5-7B-Instruct Q4_K_M (llama.cpp CUDA, full offload), 31 passes + closing per draw. Mechanical pre-filter: `score_relevance_v2.py`; tier calls manual-confirmed from the flagged state contexts. **Interpretation below is DRAFT pending maintainer confirmation.**

Recording tier per structure, per seed (0 ignored / 1 existence-or-purpose noted / 2 mappings):

| seed | PC STAGE_ORDER | REL EVENT_DISPATCH | ARB DISPLAY_LABELS | final-state size |
|---|---|---|---|---|
| 42 (t0) | 0 | 0 | 0 | ~1,108 w |
| 1 (t0.7) | 0 | 0 | 0 | ~380 w |
| 2 (t0.7) | 0 | 0 | **1** | ~885 w |
| 3 (t0.7) | 0 ⁽ᵃ⁾ | 0 ⁽ᵇ⁾ | 0 ⁽ᶜ⁾ | ~931 w |
| 4 (t0.7) | 0 ⁽ᵈ⁾ | 0 | 0 | ~1,105 w |

Borderlines (manual read, verbatim contexts archived in the result JSONs):
(a) s3 held the full inventory line "MODULE: queue/pipeline.py defines helpers: run_pipeline, stage_intake, …, stage_publish" in state through passes ~16–20, **then lost it before close** — a record-then-lost instance (the churn signature, again). (b) s3 final: "MODULE: routing/router.py defines helpers: dispatch." — inventory mention, no role. (c) s3 final: labels.py inventory line with unrelated filler helpers merged in. (d) s4 final holds run_pipeline + all five stage_* names **inside a flat many-helper inventory list** — names only, no structure, no role, no order stated. Even scoring every borderline generously as Tier 1, PC = 2/5 < 4/5.

**Verdict per the pre-registered outcome table: Outcome 3 — PC < 4/5 at ≥Tier 1 → the fork is unresolvable at floor altitude.** The floor summarizes above structure altitude even for the strongest legitimate candidate (small, pipeline-central, represented-category). Binding consequence (E2PRIME-CRITERION §4.1): **query-conditioned framing becomes mandatory for every E2′ recording gate; Fork 1 is evaluated on the trained student (§4.3).** This is a complete, reportable conclusion — not a failure of the control (the anti-laundering rule: this is NOT "Reading A confirmed").

**Report-only observations (no interpretive weight; per-seed, single draws):**
- The v2 fixes landed mechanically where v1's design could not: in v1 the singleton pair modules were *never mentioned at all* in any draw; in v2 the relocated pair reached at least inventory-level mention in 2/5 draws, and the PC's content reached state in 2/5 (once surviving to close as names-only). Category representation and small/central structure measurably raise what crosses the inventory threshold — just not to structure altitude.
- The single Tier-1 of the battery went to the **arbitrary** table (s2: "Routing display labels are defined in routing/labels.py, with labels for various events such as 'order.created', 'payment.updated'" — role noted, no mappings). Inverted vs both readings' predictions; n=1 single draw; noise under this program's standards ("do not force a read").
- s3's record-then-lost PC line is a fresh warm-retention observation consistent with the P7 churn story; it goes to §5(d) evidence, not to this control's question.
- Final-state size spread ~380–1,108 words across seeds (v1 range reproduced).
