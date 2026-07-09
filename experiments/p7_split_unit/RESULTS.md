# P7 — Split-Unit (code domain) · RESULTS

> ## UPDATE 2026-06-20 (FAIR-SHOT end-to-end, 7B) — record ✓ / retain ✗ / compose ✓ → 0/4 end-to-end; blocked at the pass-3 clobber
> Maintainer restated the bar as **"can it work AT ALL, even barely"** and accepted a **generic
> specifics-demanding prompt** (`--specifics`: "record exact values + the data structures the code
> defines", no probe reference) as fair-shot. Full `coupled_full` (31 passes + closing), 7B, temp-0 +
> 3 sampled: **0/4 produced 2353.** Decisive trajectory (seed-42 temp-0): the answer table is
> **RECORDED at Phase-A pass 2** (kv=22, State-D holds) — the recording the neutral prompt never
> elicited — then **EVICTED at pass 3** (the same edit-op id-misaddressing clobber, now deterministic),
> gone for the remaining 28 passes → `ANSWER=None`. The *smaller* 12-entry control table recorded in
> Phase-B **did** survive (ctrl=12), so retention isn't impossible — the 24-entry answer table is
> clobbered early (a consolidating REPLACE targets the large single-entry table). So under a fair shot
> the chain is **record ✓ (achievable, ~1/4) · retain ✗ (pass-3 clobber) · compose ✓** → end-to-end
> blocked at **retention**, not recording. This is now *demonstrated* end-to-end (vs earlier inferred).
> Next: the Threadripper matrix re-runs this at **n=10 on 7B + Qwen2.5-14B** to test whether a larger
> model avoids the clobber (capacity) or not (architecture → clobber-safe edit ops). `TRANSFER.md`,
> `run_matrix.py`. Files `p7_results_spec_s*.json`.

> ## UPDATE 2026-06-19 (v2 compressor, fair setup) — the "retention joint" was a REPRESENTATION
> artifact (now FIXED); the true residual gap is SALIENCE/RECORD → E2′. See `COMPRESSOR-V2.md`.
> Treating the Phase-A compressor as architecture, a **probe-blind, document-class** compressor
> (foreground module constants/tables/imports/type-structure; collapse boilerplate helpers to a name
> digest) made consecutive Phase-A views **heterogeneous** (constant-bearing chunks profile-distinct;
> view volume halved). Re-running coupled's Phase-A **warm under the UNCHANGED neutral prompt** (my
> earlier "record contents" prompt additions reverted — Line 3) over temp-0 + 2 sampled seeds:
> **the table is still not recorded** — and this is a clean SALIENCE result: the neutral rubric asks
> to "integrate precise specifics — exact values," the floor records plenty of specifics (every
> module's helper names) yet **omits the one high-information structure, the constant/lookup table**
> (the **P4/P5/P6 salience / what-to-record floor**, isolated in the code domain). No destructive
> churn occurred — BUT that is **confounded** (compressor AND prompt both changed; the neutral prompt
> elicits high-level summaries with no detailed aggregate to clobber), so it does **not** confirm
> "v2 fixed the churn." Chain status on the unaided 7B: carry ✓ (C1) · **record ✗ DEMONSTRATED
> (salience — the trainable gap → E2′)** · **retain — NOT TESTED** (table never entered state;
> churn-absence confounded with the prompt revert) · compose ✓ (GATE 3) · one-fragment-can't-win ✓
> (GATE 1). Table did not survive ⇒ **no forcing/circularity**. **ISOLATION CONTROL RUN (v1 + neutral
> prompt): the prompt is SUFFICIENT to cause/remove the churn** — v1+neutral shows no destructive
> churn (table still never recorded, 6/6 neutral draws); toggling the prompt with v1 fixed flips churn
> on/off (v1+specifics churned in attempts 1,3). The maintainer's churn diagnosis was **real**; the
> control relocates the *demonstrated* cause to the prompt and **leaves the views' independent role
> OPEN** (the disambiguating v2+specifics cell is forcing-blocked — so "views don't matter" would
> overreach, same error as "v2 fixed it"). v2 earns no retention credit here but stays a legitimate
> heterogeneity/efficiency improvement. Caveat: "no churn under neutral" is ≈n=1 (only the temp-0 draw
> accumulated state; the sampled seeds idled ~150 tok). **Net: single binding gap = SALIENCE/record
> (robust both compressors); churn is prompt-sufficient with the views' role unidentified; retention
> untested. For E2′ (which records substantially → the specifics regime where churn WAS seen and v2 is
> untested): keep BOTH the heterogeneous compressor AND clobber-safe edit ops — the churn risk is
> real, not insurance.** v2+specifics deliberately NOT run (forcing line). Text below = prior (v1 +
> non-neutral) analysis; superseded here.

> ## VERDICT 2026-06-19 (v1, superseded on the joint diagnosis) — VIABILITY-POSITIVE AT THE COMPONENT LEVEL; one trainable joint breaks the chain → E2′ (battery NOT run)
> The maintainer's bar is **"can it work AT ALL with a 7B, even barely"** (the custom model is the
> optimum; [[viability-vs-optimality]]). By that bar P7 is **positive**: every load-bearing step of
> the mechanism fired at least once on the untrained 7B —
> - the **coarse structure-preserving pass records the full arbitrary table** — cold (GATE 2) and
>   **warm with State-D holding** (seed2: `REGION_SURCHARGE_CENTS` incl `23: 988` entered in Phase-A
>   pass 2), and the neutral control table too (seed1, 12/12);
> - the **floor composes the exact answer 2353 from state** (GATE 3, 4/4);
> - a fragment-2-only reader **cannot** (GATE 1, 0/4) — the unit is genuinely unguessable.
>
> The integrated chain breaks at **exactly one joint: retention through the warm rewrite.** The
> diagnostic (seed2 pass 3) shows the break is **not** a deliberate discard of reference data and
> **not** a deep retention inability — it is an **edit-op id-misaddressing slip**: the model emitted
> `REPLACE S3: FUNCTIONS=…` to update its functions entry but S3 held the table, **clobbering it by
> hitting the wrong stable id.** That is a harness-interaction + **trainable** failure — exactly the
> kind a custom-trained student fixes. So the honest call is **"it can work; the unaided 7B just
> can't hold it together across the edit-op sweep" → carry to E2′**, with retention-through-the-sweep
> as the explicit thing the trained student must demonstrate. Reached via pre-run gates + a warm
> go-signal **before** the ~26 h battery (the battery is predicted-null on the *unaided* floor and was
> not run).

## What was tested (the reframe)

Eviction looked ~absent on this floor (P4 0/8, P6 1/~16), so P7 was reframed (maintainer-approved)
from the brief's eviction test to **differential recording**: an arbitrary lookup table
(`REGION_SURCHARGE_CENTS`, `23: 988`) preserved by a structure-preserving Phase-A coarse pass that
`coupled_full` records and `verbatim_only` (raw int-wall in a Phase-B tile) discards. Money
comparison = coupled_full vs verbatim_only on the closing answer `compute_line_surcharge(23) ==
2353`. See `PRE-REG.md`. (Note: the warm go-signal then surfaced overwrite-eviction after all — see
the finding below.)

## Pre-run gates (all passed)

- **Realized-view guards** (`verify_fixture.py`): (A) on-source, (B) both fragments mid-exclusive →
  dense a true floor, (C1) table+adder survive Phase-A (~7× structure-preserving compression),
  (C2) split real (fragment-1 tile 5, fragment-2 tile 18, gap 13).
- **GATE 1 — backfill** (`backfill_check.py`): fragment-2-only model emits the answer **0/4** (says
  INSUFFICIENT). Unit unguessable.
- **GATE 2 — differential recording, COLD** (`recording_gate.py`): with an *empty* state at k=1,
  `coupled_full` records the full table incl `23: 988` in **2/3** draws; `verbatim_only` (raw tile)
  preserves the usable mapping **0/3**. Passed *as a cold proxy* — flagged in the pre-reg as a proxy,
  with the warm run as the real arbiter.
- **GATE 3 — compose ceiling** (`compose_gate.py`): with the full structure seeded into state, the
  floor produces `2353` in **4/4**. The lookup-and-add capability is present.

## The gate that decided it: the WARM go-signal (the real arbiter, per the pre-reg)

The pre-reg said GATE 2 is a cold proxy and "the real arbiter is the per-pass warm tracking." The
warm look (`coupled_full` reading Phase-A chunks with accumulated state — battery conditions)
**contradicted the cold proxy.** A **recordability control** — a second unrelated arbitrary table
(`CARRIER_FUEL_BP`), not the answer, not query-relevant — was added to separate "runner artifact"
from "floor limit" (the handoff's F7-gate idea). Coupled, 4 Phase-A passes, answer table at pass 2 /
control at pass 3:

| draw | answer table (queried `23:988`) | control table | note |
|---|---|---|---|
| temp-0, prompt #1 (P6-lineage) | not recorded | not recorded | terse name-inventory mega-entries; destructive REPLACE (state 382→141) |
| temp-0, prompt #2 ("distinct entries") | not recorded | not recorded | enumerates every header/signature as one op (gen 40–59) → op cap → dicts skipped |
| temp-0, prompt #3 ("inline single entry") | **truncated** to first 3 of 24 (`23:988` dropped) | not recorded | fixates on a `MODULES={dir:[files]}` map, duplicated across passes |
| **t0.7 seed1**, prompt #3 | not recorded | **FULL (12/12)** at pass 3 | floor *can* host a full arbitrary table warm |
| **t0.7 seed2**, prompt #3 | **FULL (24/24) incl `23:988` at pass 2, State-D HOLDS** | partial (3) | …then **dropped by pass 3** (overwritten during restructuring) |

**Two reads, both decisive against an *unaided-floor* battery (not against viability):**

1. **Apples-to-apples (prompt held constant): GATE-2-cold vs prompt-#1-warm** isolates cold-vs-warm —
   cold (empty state) it records the full table; warm (accumulated state) it does not. The break is
   the warm dynamic, not the prompt. (Prompts #2–#3 were bounded rescue attempts; each produced a
   different avoidance, confirming no reasonable uniform prompt rescues it — diagnosis fixed at #1.)
2. **The flip at temp-0.7 (lesson #3):** the temp-0-only picture ("floor can't host tables") was
   wrong. The control records fully (seed1) and the answer table records fully with State-D holding
   (seed2) — so the floor **can** host a full table warm. But it is **sparse** (full answer-table
   entry in ~1/3 draws) and, the one time it entered, it was **overwritten the next pass** (pass 2→3)
   — ~28 passes upstream of the closing call that needs it.

**Why no battery:** coupled's only structural edge is recording the table early in **Phase-A
(pass 2)**; the closing call reads the **final** state at **pass 31+**. The quantity that matters is
"table present at answer time," and the one entry we observed did not survive to even pass 4. A
battery would measure ≈0 at answer time however often the table enters Phase-A — the P6 low-base-rate
sunk-cost trap (memory: "base rates this low won't be rescued by more N"). This is a verdict against
spending the run on the *unaided* floor — **not** against viability: the mechanism's components all
fired (see verdict), and the one break is the trainable joint diagnosed below.

## The actual new finding + the pass-3 diagnostic (the payoff for E2′)

P7 began from "eviction is dead on this floor." Under the warm temp-0.7 **code/table** dynamic we
watched a recorded table get **overwritten the next pass** — so the bottleneck has shifted from
*recording* (P4/P6) to **retention through the warm rewrite**.

**Mechanism of the loss (seed2, snapshots + ops):**
- pass 2: `ADD REGION_SURCHARGE_CENTS = {…23: 988…}` → entry **S3** = the full table (kv=24,
  State-D holds).
- pass 3: `ADD MODULES=…` (→ new S4) + **`REPLACE S3: FUNCTIONS=…`** — the model meant to update its
  *functions* entry but addressed **S3**, which held the **table** → the table is **clobbered** by an
  unrelated functions list (after pass 3, S3 = FUNCTIONS; the table is gone, state still grew).

So the loss is an **edit-op id-misaddressing slip**, not a decision to drop reference data: the
untrained floor cannot reliably track which stable numeric id holds what across passes, and a
mis-targeted REPLACE silently overwrites unrelated content. This is **(a) trainable** (a custom
student tracks ids / doesn't clobber) and **(b) partly a harness artifact** of the stable-numeric-id
edit-op scheme — *not* evidence the floor fundamentally can't retain. Precise input for E2′:
**evaluate the trained student on retention-through-the-sweep, and consider content-addressed /
clobber-safe edit ops** so a recording slip can't erase coarse-pass structure. (Strength: the clobber
is observed n=1 (seed2 pass 2→3) atop pervasive destructive churn across all attempts — enough to
name the joint that breaks, not to assert a law.)

## Why this is viability-positive, not an architecture win-or-null

- The coarse-pass mechanism records the table **cold** (GATE 2) and composition works (GATE 3) — the
  architecture's two load-bearing steps each succeed in isolation.
- The break is the **untrained 7B's warm multi-pass state-building**: sparse table-hosting + a
  destructive rewrite that overwrites recorded structure. A property of the floor and its
  integration dynamic, not of the coarse-to-fine schedule. The capability is present; it needs the
  trained student **in the same dynamic** (E2′).

## Value delivered

- A clean code split-unit fixture + a deterministic structure-preserving code compressor + a warm
  recordability-control diagnostic + three passing gates — **ready to re-pose P7 on E2′ unchanged**,
  now with retention (not just recording) as the explicit thing to measure.
- The verdict was reached at the **gate stage (~hours of CPU)**, **saving the ~26 h battery** — the
  pre-run gating discipline paying off.
- **Floor finding for E1′/E2′:** warm integration on the untrained 7B records arbitrary tables only
  sparsely and **does not retain them through restructuring** (recorded-then-overwritten); a trained
  student or a retention-targeted prompt-floor is required to carry reference data across passes.

## Options for the maintainer (both their call; I recommend neither be required)

1. **Answer-blind full run, no prompt change** (~1.7 h on the 1080Ti): seed2 (and a few t0.7 seeds),
   full 31 passes + real closing, to convert the n=1 clobber inference into a measured datum. **Flagged
   near-certain-null** — seed2 lost the table within one pass, 28 upstream of the closing call; this
   mostly re-confirms the diagnostic. Not required: the component-level viability + the named joint
   already make the E2′ case.
2. **A persistence intervention is a FORCING-LINE call and is yours, not mine.** Either a uniform
   "don't overwrite recorded data structures" prompt **or** a clobber-safe / content-addressed edit-op
   harness would likely produce an end-to-end success — but P7's claim *is* that the coarse pass holds
   the skeleton through the sweep, so a success obtained by patching retention partly assumes the
   conclusion. The prompt version is closer to forcing; the harness clobber-safety fix is closer to a
   legitimate infrastructure confound-removal (cf. the P6 op-cap fix) since the loss is a mis-addressed
   REPLACE, not a retention decision. I am **not** doing either unprompted; surfaced for your decision.

## Scope / honesty

Untrained Qwen-7B floor, n=1 fixture, 1 split unit + 1 control table; warm go-signal = temp-0 (3
prompts) + 2 sampled temp-0.7 seeds, coupled-only, 4 Phase-A passes. The overwrite-eviction is
observed n=1; the sparse-hosting rate is ~1/3 of sampled draws. A floor characterization + a
not-yet-testable architecture claim — **not** an effect size, **not** a viability verdict. Battery
NOT run; nothing published. Closing-answer correctness from the go-signal is NOT cited (those
closings ran on 4-pass truncated state, not a real final state — not a fair test). Artifacts:
`{PRE-REG.md, fixture/, compress_code.py, verify_fixture.py, backfill_check.py, recording_gate.py,
compose_gate.py, run.py, scaffold_struct.json, gosignal_coupled*.log, *_result.json}`.
