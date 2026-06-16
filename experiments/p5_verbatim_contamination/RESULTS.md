# P5 — Verbatim-stage contamination · RESULTS

**Run:** 2026-06-16 · local Qwen2.5-7B-Instruct (llama.cpp CPU), temp 0, seed 42 · frozen
upstream state from the P4 coupled run · $0 spend · pre-registered (`PRE-REG.md`, pushed
before scoring; explicit-ask amendment pushed before the explicit runs).
Arms: **A0** baseline (state+view→ops) · **A1** blind-salience (view-only→list; then +state→ops) ·
**A2** state-visible salience (state+view→list; then →ops). A1-vs-A2 isolates state visibility;
A2-vs-A0 the elicitation step. Metric: probe fact present in the resulting state (P4 matcher).

## Headline

**No robust evidence of prior-state contamination. P4's misses were task-vagueness /
salience-misjudgment, not the prior state suppressing recall.** Naming the information
need (explicit ask) recovers the facts — genuinely, in *every* arm including the plain
baseline, even at peak prior-saturation.

## Results

| probe | pass | frozen state | **vague task** (A0/A1/A2) | **explicit ask** (A0/A1/A2) |
|---|---|---|---|---|
| F3 (walk+dog) | 6 | 8 entries | F / F / **T**  | **T / T / T** |
| F7 (grandmother typesetter, Garamond, 31y) | 17 | 23 (peak) | F / F / F | **T / T / T** |
| F1 (codename Sandpiper) | 3 | 6 entries | — | F / **T** / F |

### Read

1. **Vague task = coin toss (confirms the confound).** Under "capture *every* concrete
   specific", per-detail survival was inconsistent and direction-less: F3@6 kept only by
   the *state-visible* arm; F7@17 dropped by all three (though A1's blind salience step
   *did* list F7 — the edit step then dropped it: an integration-stage failure). No clean
   signal — the model was being asked to guess which asides mattered.

2. **Explicit ask recovers the facts, genuinely, across all arms (F3, F7).** Once the task
   names the need, A0/A1/A2 all record the fact with real multi-component entries — e.g.
   F7: *"The speaker's grandmother was a typesetter at Garamond Press for 31 years."*
   This holds at **peak saturation** (F7@17, 23 prior entries). ⇒ The P4 miss was the
   model (correctly) not rating a personal aside as belonging in a *strategy brief*; under
   a recall/lookup ask it surfaces it. **No contamination, no saturation effect.**

3. **The one arm-separation (F1@3: A0=F, A1=T, A2=F) is noise, not a mechanism.** F1's
   matcher is a single bare token (`sandpiper`); the decomposition shows **neither** salience
   step listed the codename, and A1's "present" is an *incidental* mention buried inside a
   Meridian/$299 entry it happened to add. Not a deliberate salience-driven recording, and
   it occurs at the **lowest** saturation (6 entries) — the **opposite** of the
   "more prior state ⇒ more contamination" hypothesis.

## Conclusion (and what it does/doesn't mean)

- **The contamination hypothesis is not supported on this evidence.** The binding failure
  in P4 was **task/query specification**, a design lever — not prior-state corruption of
  the read. Explicit/query-conditioned passes recover facts the vague task dropped.
- A secondary observation worth carrying: under the explicit ask the coupled floor recorded
  **F7, which lay entirely outside the dense baseline's window in P4** — i.e. coverage's
  advantage *is* convertible to recall once the ask is explicit. (Suggestive only; P5 did
  not re-run the full coupled-vs-dense comparison.)
- **Scope:** n=3 probes, 1 document, untrained Qwen-7B floor, temp 0 (single deterministic
  draw per arm — no seed/paraphrase replication). This is a **mechanism check**, not an
  effect-size estimate and **not** a viability verdict. Viability rides on the trained
  student (E2′). The actionable inference for E1′/E2′: **condition the prompt floor on the
  information need** (query/recall-framed), since vagueness — not coupling — was what
  suppressed recall here.

Raw per-arm outputs (salience text + edit ops + verdicts): `p5_pass*_vague.json`,
`p5_pass*_explicit.json` (not vendored; regenerate via `run.py [--explicit] --pass P --probe F`).
