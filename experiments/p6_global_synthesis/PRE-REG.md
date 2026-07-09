# P6 — Salience-shaping (whole-document re-weighting) · PRE-REGISTRATION (rewrite)

**Status:** pre-registered, awaiting maintainer approval before any gold authoring or model run.
Supersedes the original P6 *trace/synthesis* design, which was invalidated **pre-run** by
source inspection (`PREFLIGHT-INVALIDATION.md`, `DESIGN-A-distributed-inference.md`): the
Sandpiper conversation explicitly states and recaps its own conclusions, so neither a "trace the
decision" target nor any *unstated-conclusion* distributed-inference survives (3 designs died to
that one root cause). This rewrite changes the **headline question**, for a documented reason
(below), not the program's standards.

Reuses the existing P4/P5 Sandpiper fixture (390 turns / 16 segments), schedule, untrained
Qwen-7B floor, the P4 normalized matcher, and the P4 dense baseline — **no new fixture, no
fixture edit** (see `SANDPIPER-SALIENCE-AUDIT.md`). This file + the gold are committed before
any arm is scored.

## Why this headline (and why the old one was the wrong spend)

The original P6 headline — **coupled_full vs verbatim_only** measuring whether the scaffold keeps
a distributed fact from being **evicted** — is **predicted-null by our own prior results**, so it
could not discriminate the scaffold's value even if the scaffold works:

- **P4** located the bottleneck as **salience** (the untrained floor declined to *write down*
  available facts), **not eviction** (`state_entry_pass: null`, `evicted: false` — facts never
  fell out; they were never recorded).
- A scaffold's most-cited benefit is **preventing eviction**. If eviction was never the
  bottleneck, the scaffold has nothing to fix → coupled ≈ verbatim → predicted null.

A *predicted* null is weak signal (we already knew it). So P6 retargets the **live** bottleneck:

> **Does holding a coarse global map of the whole document make the model record a detail that is
> locally unremarkable but globally load-bearing — a detail a cold local reader would shrug past?**

This is a **salience-shaping** effect (re-weighting local salience via global context), aimed at
the bottleneck P4/P5 actually found, and we **genuinely do not know** its sign. That is what makes
it worth a run. This is **probe #1 of a battery**; one clean result is a signal, not proof.

## Mechanism under test

`verbatim_only` reads a segment **cold** and, following the verbatim rubric, records *some*
specifics but rates a dull-looking detail as not worth keeping. `coupled_full` reads the **same
verbatim tile** while holding the Phase-A scaffold ("this document is about a constrained launch
deferring wide retail to spring"), recognizes the dull detail as load-bearing, and records it.
The scaffold's job here is **organization/salience**, not retention.

## Arms (all query-conditioned — P5's lesson: never vague)

| arm | description | role |
|---|---|---|
| **dense** | single-pass head+tail (~14K of 73K), P4's `run_dense` | **coverage floor** — structurally lacks the mid-doc detail; expected to miss (table stakes, not the headline) |
| **verbatim_only** | Phase-B verbatim tiles only, **NO Phase-A scaffold** | cold local reader — the control the headline is measured against |
| **coupled_full** | Phase-A coarse scaffold + Phase-B verbatim tiles | the claim: global frame re-weights local salience |

**Headline contrast = coupled_full vs verbatim_only** (coverage held constant: both read the
detail verbatim in the same Phase-B tile; they differ only in the scaffold). All arms are
query-conditioned on the same explicit ask, and each state arm's final **integration state** is
scored (the salience effect is about what gets *recorded*, so we score the state, not only a
closing answer).

## The discriminating details — load-bearing × control pairs from existing Sandpiper (audit verified)

The audit (`SANDPIPER-SALIENCE-AUDIT.md`) established a real constraint: because these characters
discuss everything important, "load-bearing" correlates with "locally prominent," so **no single
detail is both maximally dull and maximally load-bearing**. A single-detail headline therefore
risks a **selection-artifact null** (if the detail is prominent, verbatim_only records it too).
The robust form is a **load-bearing × arm interaction with prominence-matched controls**:

| pair | load-bearing TEST (low airtime) | prominence-matched CONTROL (low airtime) |
|---|---|---|
| P-a | **D1 granular timing** — Halvorsen SMT expansion yields units only **Feb/March → April** (the *mechanism* the Q2-deferral rests on), seg2 t38, **1/24 turns** | packaging-COGS aside (seg7 t156), **1/24** — dull, NOT load-bearing |
| P-b | **D2 "68 percent margin penalty"** — the specific that kills the last retail salvage, seg9 t198, **1/24** | F7 grandmother/Garamond (seg7), **2/24** — low load-bearing flavor |

**Matchers MUST target the granular specific** ("February or March" / "April or later" / "68
percent margin penalty"), **never the focal topic** ("SMT" is 5/24 — prominent, would null by
artifact). See audit for the prominence measurements and guard evidence.

## Scoring (gold to be authored on approval)

- **Headline metric — the interaction:** within each pair, **coupled_full records the load-bearing
  TEST detail at a higher rate than the prominence-matched CONTROL, while verbatim_only shows no
  such preference** (and dense lacks both, being out-of-window). The claim is the *coupled
  load-bearing-vs-control gap exceeding the verbatim gap* — robust to absolute dullness and to
  one-detail thinness.
- **Per-arm recorded-in-state** for every test/control detail (the raw table behind the interaction).
- **Honesty on n:** two pairs, single draw, temp 0 — directional, not powered for significance;
  reported as a mechanism signal, not an effect size.
- Mechanical normalized match on the state text is the skeleton; a Kiro-Haiku judge may give a
  secondary read on whether the state *uses* the detail as load-bearing — caveated (judge
  confound), not the verdict.

## Guards the runner MUST assert (model-free, before any arm is trusted)

- **(a) fires-on-source:** each detail's matcher fires on its source segment.
- **(b) dense-floor real:** each detail's discriminating terms do **NOT** fire on the dense
  head+tail context — else dense isn't a true floor. (Matcher uses the mid-exclusive *mechanism*
  terms, e.g. `SMT`/`expanding their SMT`/`February or March` — **not** `April`/`scale`, which leak
  via the seg16 recap. This is the 30k-numeric-leak lesson carried forward.)
- **(c) salience-not-coverage [P6-specific trap]:** each detail's discriminating terms must **NOT**
  appear in the **Phase-A scaffold view** actually used — else coupled_full gets the detail by
  *reading the words* (coverage), not by scaffold-driven salience. Audit shows the existing
  compressor already drops D1's terms; the runner re-asserts it against the realized view, and if a
  term survives we hand-trim the compressed slice (legitimate — compression quality is not under
  test) or drop that detail.

## Pre-registered outcomes (all stated before scoring — no post-hoc reading)

- **Salience-shaping confirmed:** coupled_full records the load-bearing TEST details preferentially
  over the prominence-matched CONTROLs; verbatim_only shows no such preference (the interaction).
- **Null (reported, not buried):** verbatim_only shows the same test>control preference → the
  scaffold isn't doing salience-shaping; cold local reading already re-weights. Real signal → E2′.
- **Floor too weak:** coupled_full records neither test nor control (or no preference) → the
  untrained 7B can't use a global frame to re-weight local salience at this scale. Real negative → E2′.
- **Prominence-confound caught:** if coupled records test>control *but the controls turn out not
  prominence-matched* (verify post-hoc), the result reflects prominence, not load-bearing — report
  as inconclusive, not a win.
- **Dense surprise:** if dense records a TEST detail, re-audit matcher specificity (guard (b) should prevent).

## Discipline note (rigor, not goalpost-moving)

This is a **benchmark correction**, not a goalpost move: the eviction headline was **predicted-null
by our own P4/P5 data**, so it could not have discriminated the scaffold's value even on success.
The salience headline targets the bottleneck P4/P5 actually identified, and its sign is genuinely
unknown. **Once this salience version is pre-registered and run, we live with its result — no
further headline pivots after a valid test fires.**

## Scope / honesty

Untrained Qwen-7B floor, n=1 document, temp 0, single draw per arm; a **mechanism/architecture
probe**, not an effect-size estimate and **not a viability verdict** (that rides on the trained
student E2′). Probe #1 of a planned battery. One clean coupled_full > verbatim_only result is the
first qualitative evidence that a coarse global pass **re-weights what the reader finds worth
recording** — the point of the coarse-to-fine schedule — not proof of whole-document understanding.
