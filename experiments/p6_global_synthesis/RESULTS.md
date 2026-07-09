# P6 — Salience-shaping test · RESULTS

> ## FINAL VERDICT 2026-06-18 — INCONCLUSIVE / FLOOR-LIMITED (underpowered on the generic floor)
> The untrained generic floor records distributed load-bearing specifics **too sporadically**
> (≤1/4 per detail, most draws zero, both controls at floor) to evaluate salience-shaping at all.
> This is a clean, valid, replicated *characterization of the floor's ceiling* — NOT a measured
> "no effect" (we lacked the sensitivity to detect one) and NOT a runner failure (v1's confound is
> fixed; see below).
>
> Fixed runner (dedup placeholder ADDs, prioritize REPLACE, op cap 24, Phase-B all "verbatim"
> stage, save gen-ops). Draws: **1 deterministic** (seed 42, temp 0 — the canonical, P1–P5-comparable
> greedy decode) + **3 sampled** (seeds 1–3, temp 0.7; op-validity calibrated). NOT pooled into one
> rate — different decode distributions. Guards (a/b/c) PASS every run; **F7 gate PASSED** (both
> arms recorded the F7 control in the deterministic draw → the runner *can* record specifics, so a
> non-recording is real, not a floor artifact). All recordings below are **manual-verified genuine**.
>
> **EVER-recorded, by draw (V = verbatim_only, C = coupled_full):**
>
> | detail | role | s42 det (t0) | s1 (t0.7) | s2 (t0.7) | s3 (t0.7) | V: det / 3-smp | C: det / 3-smp |
> |---|---|---|---|---|---|---|---|
> | D1_timing (Feb/Mar SMT) | test | **V** | – | **C** | – | ✓ / 0 | ✗ / 1 |
> | D2_68pct (68% penalty) | test | – | – | **C** | – | ✗ / 0 | ✗ / 1 |
> | C1_pkgcogs | control | – | – | – | – | ✗ / 0 | ✗ / 0 |
> | C2_f7 | control | V, C | – | – | – | ✓ / 0 | ✓ / 0 |
>
> **The pre-registered headline metric could not be evaluated.** P6's headline was the load-bearing
> × arm *interaction* (coupled records TEST > CONTROL where verbatim does not). With **both controls
> at floor** (C1 never recorded; C2 only in the deterministic draw, by both arms), the interaction
> is **uncomputable** — there is no control baseline to compare against. The table above is the
> fallback raw-count read, and it shows **no replicable coupled-vs-verbatim difference**: 2 of 4
> draws (s1, s3) record *nothing*; the 2 that record disagree in direction — s42 favors **verbatim**
> (V got D1), s2 favors **coupled** (C got both D1 and D2). The floor-sparsity *is* the finding.
>
> **The single-draw temp-0 reading did NOT replicate.** s42 alone looked like "scaffold blurs
> specifics → anti-salience"; with replication that flips (s2 has coupled recording both
> specifics verbatim, e.g. "...units don't start coming off the line until February or March... ",
> "...a 68 percent margin penalty..."). The n=1 impression was a single-draw artifact — exactly
> why replication was required.
>
> **Interpretation (viability framing [[viability-vs-optimality]]).** On the untrained generic
> Qwen-7B floor, the coarse global scaffold confers **no reliable advantage** in recording
> distributed load-bearing specifics — and the base rate of recording them at all is very low
> (most draws capture none), so the floor is too sparse/noisy to *express* a salience-shaping
> effect even if one exists. This is **not** an architecture negative: it is "the shoehorned
> generic floor cannot answer the salience question; it rides on the trained student E2′."
> Genuinely useful as a calibration of the floor and of the test's power.
>
> **Scope:** 4 draws, 1 document, 2 test × 2 control details, single fixture, untrained 7B floor.
> Mechanism/power probe — not an effect size, not a viability verdict (E2′). The low detail-recording
> base rate means low statistical power: a real effect could be present yet undetectable here.
>
> Raw: `p6_results_s42_t0.json`, `p6_results_s{1,2,3}_t0.7.json`. Runner: `run.py` (v2, fixed).
> The placeholder-degeneration that broke v1 (below) is resolved (dup-entry instances 25→~2;
> REPLACE-driven content states). Not published (maintainer reviews before any push).
>
> ---
> ### (below: v1 run — INCONCLUSIVE runner pathology, kept as record; superseded by the above)

**Verdict (v1, superseded): INCONCLUSIVE — the salience question was not validly posed.** The run degenerated
upstream of the question: on the untrained Qwen-7B floor the coarse-scaffold + "scaffold"-stage
rubric produced **unfilled-placeholder spam**, and the 16-op apply cap then **truncated heavily
and asymmetrically at exactly the two test-detail tiles** in the scaffolded arm. So "coupled_full
recorded neither test detail" cannot be read as a salience signal. The *real, useful* empirical
finding here is about the **prompt-floor/schedule**, not salience-shaping — see below. This does
**not** publish as a clean negative; it is the maintainer's "if the test is inconclusive we can
build a different one" case.

Run 2026-06-16→17; $0 beyond 6 Kiro-Haiku scaffold compressions; local Qwen2.5-7B floor, temp 0,
single draw. Design + pre-reg: `PRE-REG.md`, `gold_chain.json`, `SANDPIPER-SALIENCE-AUDIT.md`.
Pre-run invalidation of the earlier trace design: `PREFLIGHT-INVALIDATION.md`. Raw:
`p6_results.json`, `p6_run.log`. Guards (a/b/c) asserted PASS at runtime.

## The empirical finding (lead with this — it's real and informs E1′/E2′)

**The coarse-to-fine schedule + edit-op floor degenerates on the untrained 7B**, two coupled
pathologies:

1. **Placeholder spam, never filled.** Both state arms ended ~40 entries dominated by duplicate,
   *unfilled* section headings — coupled_full ~25× "# Supply Constraints and Go-to-Market
   Strategy"; verbatim_only ~10× "# Key Constraints and Figures". The "scaffold"-stage rubric
   ("build section headings and one-line placeholders via ADD") does exactly what it says, and the
   floor **never REPLACE-s the placeholders with content** in later stages. coupled_full (more
   scaffold-stage passes) was worse: leaner, more abstract, fewer concrete entries.
2. **Op-cap truncation at the floor's over-generation.** When the floor over-emits ops, `apply(
   parsed.ops[:16])` silently drops the overflow, order-dependent:

   | arm | D1 tile (pass, stage) | D2 tile (pass, stage) |
   |---|---|---|
   | coupled_full | pass10 scaffold: valid=31 **applied=16 → 15 dropped** | pass20 concrete: valid=22 **applied=16 → 6 dropped** |
   | verbatim_only | pass4 scaffold: valid=6 applied=6 (0 dropped) | pass14 concrete: valid=6 applied=6 (0 dropped) |

   The scaffolded arm was truncated at **both** test tiles; the no-scaffold arm at neither. Raw op
   text was **not saved**, so for coupled_full "detail never recorded" cannot be distinguished from
   "the recording op was among the 15/6 dropped." This asymmetry biases against the scaffolded arm
   precisely where the test lives → the coupled-vs-verbatim contrast is **confounded, not clean.**

These two are prompt-floor/runner findings, directly useful for E1′/E2′ design (below). Neither
is evidence about whether a global frame re-weights local salience.

## What the arms actually recorded (matcher + manual read)

| detail | role | dense | verbatim_only | coupled_full |
|---|---|---|---|---|
| D1_timing | test | – | – | – (D1 tile truncated −15) |
| D2_68pct | test | – | – | – (D2 tile truncated −6) |
| C1_pkgcogs | control | – | – | – |
| C2_f7 | control | – | **recorded** | – |

- **Manual read confirms the matcher is not the issue** (esp. needed for D1, which paraphrases):
  no test specific appears in any phrasing in either state; coupled's "20 store" hit is an
  unrelated Meridian gross-margin line, not the 68%/300-unit scenario.
- **Per-pass eviction-aware tracking:** the tests were never recorded at any pass (not
  recorded-then-evicted) — so where the run *is* clean, it's a recording floor, not eviction.
- **The one truncation-free, clean sub-result:** verbatim_only read **both** test tiles with no
  op truncation and still recorded neither (D1 under the figure-suppressing "scaffold" rubric;
  D2 under "concrete"). That is a clean datum that the *cold* floor didn't surface D1/D2 — but it
  says nothing about the scaffold, since coupled's matching reads were truncated.

## Why not "floor too weak" (a pre-registered bucket)
The pre-reg's "floor too weak" meant *the model read the specific and didn't rate it worth
keeping* — a genuine salience signal. That is **not** what happened: a placeholder-spam +
op-truncation pathology prevented the question from being posed. Reporting the pathology as the
pre-registered negative would launder a broken run into a result — the exact trap the pre-flight
discipline exists to avoid. Hence: **inconclusive.**

## Scope / honesty
n = 2 test × 2 control, single binary each, one document, temp 0, untrained Qwen-7B floor —
directional at best, and here not even that (confounded). Not an effect size, not a viability
verdict (E2′). D1 was additionally fragile pre-run (figure-suppressing "scaffold"-stage tile +
paraphrase-sensitive matcher); D2 was the clean test and was truncated in coupled / unrecorded in
verbatim.

## Carry-forward (the value of this run)
1. **Prompt-floor / schedule fixes for E1′/E2′** (directly motivated): cap ADDs harder and/or
   **prioritize REPLACE over ADD** in late stages so placeholders get filled; **shorten or drop
   the "scaffold" stage** on a weak floor; raise/abolish the 16-op apply cap or apply ops by a
   salience order rather than first-16; **save raw op text** every pass (so truncation vs
   non-generation is always separable).
2. **Re-pose the salience question only after the floor stops degenerating** — best on the trained
   student (E2′), or on the 7B *after* the runner fix, where the state actually hosts specifics.
3. **Decision for the maintainer:** (a) accept this as an inconclusive prompt-floor finding and
   carry the salience question to E2′, or (b) apply the cheap runner fix (#1) and rerun (~3h CPU)
   to get a clean coupled-vs-verbatim read on the 7B. **Do not publish until decided.**
