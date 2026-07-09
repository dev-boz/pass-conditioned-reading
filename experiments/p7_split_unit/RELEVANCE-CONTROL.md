# P7 — Relevance control (Reading A vs B) · PRE-REGISTRATION (before scoring)

## The question

P7's salience finding (`COMPRESSOR-V2.md`): under a probe-blind compressor + neutral prompt the floor
records module/helper names but omits the arbitrary `REGION_SURCHARGE_CENTS` table (0/6 neutral draws).
Filed as "salience / what-to-record gap → trainable → E2′." But that has an unresolved fork:

- **Reading A (failure):** the floor lacks the judgment to record a brief-worthy structure → trainable
  → **E2′ justified.**
- **Reading B (correct behavior):** omitting an arbitrary, meaningless-until-queried table *is* the
  correct editorial choice for a brief → the floor was right → this is the **P4 task-salience
  confound** in a new domain, and training E2′ to record the arbitrary table would teach it to be
  **wrong under the task** (overfitting to the probe — the forcing line relocated into training).

The two readings make opposite E2′ recommendations. This control distinguishes them.

## The test — a matched pair differing ONLY in behavioral relevance

Two tables added to the fixture (`fixture/gen_fixture.py`), both read in the **same Phase-A chunk 3 /
pass 4** (identical state pressure), both surviving the frozen v2 compressor into that view (24/24):

| | keys | values | size | consumed by | relevance |
|---|---|---|---|---|---|
| **EVENT_DISPATCH** (relevant) | 24 real event names (`order.created`, …) | arbitrary, non-derivable real-word handlers (`expire_shipment`, …) | 24 | `dispatch()` — runs the handler for each event (**control flow**) | a behavioural brief must capture which events route where |
| **DISPLAY_LABELS** (arbitrary) | **same** 24 event names | arbitrary, non-derivable real-word labels (`jade_ridge`, …) | 24 | a trivial `label()` (**cosmetic display**) | none — decorative |

**Matched axes** (the advisor's confounds, controlled): size, surface form (str→str module-level dict
literal + docstring + helper), position (same chunk/pass), **regularity** (both values
non-derivable from keys — neither rule-compressible), **token difficulty** (both real-word two-token
values — neither OOD-hard), and shared keys. **Only behavioral relevance differs,** carried by context
(routing-that-drives-control-flow vs cosmetic-display), not by decoration. Relevance justified
**probe-blind**: control-flow routing is what a "what does this codebase do" brief must capture — no
reference to the surcharge probe.

## Protocol (frozen)

- **Neutral prompt, unchanged** (P6-lineage broad brief; no append-only, no "record tables", no probe
  mention). v2 compressor **frozen**. Schedule unchanged. Coupled Phase-A passes, warm. Only the
  fixture gained the matched pair.
- **Replication:** temp-0 + **4 sampled temp-0.7 seeds**; per-seed, never pooled.
- **Metric — tiered, by manual-confirmed read** (auto `relevant_kv`/`alias_kv` = verbatim-pair
  pre-filter only):
  - **Tier 0 — ignored:** the table is not mentioned.
  - **Tier 1 — noted existence/purpose:** the brief mentions the table / its role (e.g. "a dispatcher
    routing events to handlers") **without** the mappings.
  - **Tier 2 — mappings recorded:** ≥1 event→value pair recorded (verbatim or prose).
  - "Recorded for relevance" = **≥ Tier 1.**

## Pre-registered outcomes (stated BEFORE scoring)

- **Reading B confirmed (arbitrary omission was CORRECT editorial judgment):** relevant ≥ Tier 1 in
  **≥4/5 seeds** AND arbitrary = Tier 0 in **≥4/5 seeds**. ⇒ the floor preferentially records the
  behaviour-governing table and correctly drops the cosmetic one; the earlier surcharge omission was
  *correct salience*, not a capability failure. **CONSEQUENCE: "train E2′ to record the arbitrary
  table" is overfitting to the probe — the E2′ target as framed is wrong; the architecture's recording
  step is working; the planted signal was the problem (P4 confound re-identified).**
- **Reading A confirmed (genuine recording failure):** relevant is Tier 0 (or only rarely ≥Tier 1) at
  a rate comparable to arbitrary — both essentially ignored. ⇒ the floor under-records brief-worthy
  structure regardless of relevance. **CONSEQUENCE: E2′ justified; its target — "record
  brief-relevant structure" — is legitimate, not overfitting.**
- **Ambiguous:** rates overlap / wide spread, or relevant and arbitrary both sometimes noted without
  ≥4/5 separation ⇒ more seeds, or re-audit the matched pair for residual confounds. Do not force a read.

## RESULT (manual-confirmed; 5 draws: temp-0 + 4× temp-0.7) — INCONCLUSIVE (manipulation didn't land; fork UNRESOLVED)

Recording tier per table, per seed (Tier 0 ignored / 1 noted-purpose / 2 mappings):

| seed | EVENT_DISPATCH (relevant) | DISPLAY_LABELS (arbitrary) | state size |
|---|---|---|---|
| 42 (t0) | **Tier 0** | **Tier 0** | ~2100 tok (recorded a lot) |
| 1 (t0.7) | Tier 0 | Tier 0 | ~620 |
| 2 (t0.7) | Tier 0 | Tier 0 | ~975 |
| 3 (t0.7) | Tier 0 | Tier 0 | ~160 |
| 4 (t0.7) | **Tier 0** | **Tier 0** | ~2750 tok (recorded a lot) |

**Both tables ignored in 5/5 seeds.** Decisive check (per seed): the dispatch module (`router.py`/
`EVENT_DISPATCH`/`dispatch(`), the shared event keys (`order.created`…), the relevant handler values,
the arbitrary label values, and `DISPLAY_LABELS`/`ui/labels` — **all absent in every seed.** The
verbatim-pair pre-filter is 0/0 for both, all passes. The "routing"/"dispatch" keyword hits were
**false positives** — the filler `routing` module, `*_route` helper names, and incidental prose — not
the dispatch table. What the floor DID record: the voluminous module/helper-name inventory.

**This is the pre-registered AMBIGUOUS / manipulation-didn't-land branch — NOT Reading A.** A
null-on-both-arms does not resolve the fork, for two reasons:

1. **No positive control → the instrument's sensitivity is unproven.** To conclude "the floor
   under-records *regardless of relevance*" (A) requires showing the setup *could* detect relevance
   mattering — i.e. that *some* brief-relevant structure clears Tier 1+ under neutral+v2. Nothing does
   (not the dispatch/ui modules, not CARRIER_FUEL in the represented `carrier` category, nothing). All
   arms reading zero measures "nothing crosses threshold here" — re-confirming the prior neutral+v2
   non-recording — not "relevance has no effect." (This is the GATE-3 / F7-gate / recordability-control
   discipline applied elsewhere this program and skipped here.)
2. **Singleton-module dilution confound.** Both inserted tables live in *unique* categories
   (`dispatch/router.py`, `ui/labels.py`) while the 100 filler modules cluster into ~15
   well-represented categories. The high-recording briefs (s42, s4) enumerate exactly those ~15
   categories and drop both singletons **at the inventory level** — table *contents* never became the
   deciding factor. "DISPATCH ignored" is explained by singleton-vs-represented before
   relevance-of-content can matter.

**Honest headline:** under the neutral brief the floor produces a **category-level summary and records
no specific data structure of any kind** (relevant or arbitrary, int or str, nor even the singleton
modules' existence) — it operates *above* table-transcription altitude. That is consistent with
**both** "can't record relevant structure" (A) **and** "reasonable altitude choice on an
altitude-ambiguous task" (B / the P4 task confound). **The fork is NOT resolved; carry it to E2′ as
open.** Reporting "A confirmed" would launder a degenerate null into a conclusion.

**What was nonetheless sound** (keep): the confound fixes (regularity, token-difficulty, shared keys,
same chunk) were necessary; tiers pre-registered before scoring; the manual read caught the
"routing"/"dispatch" false positives (which is what *exposed* the both-zero floor). The build is good;
only the inference from a degenerate null was wrong (corrected here).

**The discriminator that WOULD resolve it (maintainer's call — flagged, not run):** one run with
(a) an in-fixture **positive control** — a brief-relevant structure placed in a *well-represented*
category — confirmed to surface at Tier 1+ (proving instrument sensitivity), and (b) the
relevant/arbitrary pair **matched on category-representation too** (not singletons). If a
non-diluted relevant structure surfaces and the arbitrary one doesn't → B/judgment; if a non-diluted
relevant structure is *still* dropped → A. Without a positive instance, the comparison can't run.

$0 local CPU; nothing published. Does NOT run the battery or E2′; does NOT test retention (the
arbitrary table never recorded under neutral conditions — retention untested). Does NOT change the
compressor or prompt. **Surfaced for review before drawing the A-vs-B conclusion** (the recording-rate
contrast is reported; the interpretation is gated on maintainer approval).
