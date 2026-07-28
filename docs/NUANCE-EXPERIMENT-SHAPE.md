# The non-local nuance experiment — shape / pre-registration draft

*Draft experiment design for the test README (8) promises and the repo has never run: does the coarse-to-fine schedule preserve **emergent, distributed nuance** that a matched-budget compaction baseline flattens. Status: shape for refinement, not final. Written to slot into the pass-conditioned-reading program's existing pre-registration style (kill criteria, gates, matched budget, LLM-judge + human two-axis).*

---

## 0. The measurement problem, and the unlock

Every "vibes test" fails the same way: "did it preserve the tone/feeling?" is subjective, rater-dependent, and impossible to attach a kill criterion to. That is why AI attempts produced mush and why it *feels* like you'd need a sociologist. You don't. You need two things a careful writer can produce:

**The unlock: don't score the nuance, score the decision the nuance forces.** Plant an emergent signal that lives in no single slice, and that a reader who integrated the whole conversation would act on. Then give an ordinary task and check whether the output makes the specific, **pre-registered** move that only whole-conversation integration produces. "Nuance preservation" becomes "did it make the call that requires the whole picture" — which is a concrete, high-agreement judgment an LLM-judge *and* an ordinary human can both make, and which you can kill on.

So the humanities skill you actually need is **authoring** (writing believable human dynamics that are real but never stated outright), not **rating**. The rating is objectified by the pre-registered decision.

---

## 1. The claim

**M-NL (non-local integration).** On a long source carrying a pre-registered emergent signal that is *non-local by construction* (present in no single compressed view), the coupled coarse-to-fine schedule produces an output that reflects the signal at a higher rate than a matched-token-budget rolling-compaction baseline.

Why this is the *right* target and not a repeat of the P7 drift: the signal is (a) **non-local** — the property that gives the architecture any advantage over a single-pass read — and (b) **semantically weighted** — a good assistant clearly *should* integrate it, which dissolves the P7 §5(a) fork (you could never say whether dropping an arbitrary RNG value was failure or correct; here, dropping a real emotional shift is unambiguously failure).

---

## 2. The three plantable signal types (author one; type A is the recommended first)

Each is non-local: distributed across the whole span, individually innocuous per turn, never stated.

- **A — the drift / souring arc (recommended first; cleanest to author and score).** The user's stance on some option X moves enthusiastic → ambivalent → quietly cold across the conversation, and *never says* "I've gone off X." Each turn is mild. **Decision it forces:** an integrated output deprioritizes / flags X as cooling; a flattened output plans around X as a centerpiece (because the loud early enthusiasm is what a summary keeps).
- **B — the unstated tension.** Two goals the user states far apart quietly conflict (e.g. "keep it exclusive/premium" early vs "get it to as many people as possible" late; or ship-fast vs get-it-right). Neither turn flags the collision. **Decision it forces:** an integrated output *surfaces the tension* and proposes a resolution; a flattened output lists both as independent bullets and never notices.
- **C — the recontextualizing detail.** An early offhand detail changes the meaning of a late decision (e.g. early: the co-founder was burned by a rushed launch at a past company; late: the group debates an aggressive timeline). **Decision it forces:** an integrated output connects them ("given [co-founder]'s history, expect resistance to the aggressive date"); a flattened output treats the timeline decision cold.

**Worked example of A (so the authoring target is concrete):** a multi-week conversation planning a podcast. Early turns: the user is excited about bringing on a specific co-host. Middle: subtly more logistical and skeptical — small annoyances, scheduling friction, "hmm," fewer exclamation marks, asks what it'd look like solo. Late: goes through the motions, energy is elsewhere, never says "I don't want the co-host." Task: *"draft the plan for next month."* Pre-registered integrated answer: the plan treats the co-host as fading / raises whether to proceed. Pre-registered flattened answer: the co-host is the centerpiece.

---

## 3. The validity gates (run BEFORE the real comparison — this is where rigor lives)

These are the analog of the program's GATE 1 backfill ("unit unguessable from one fragment"). Without them the test is worthless, and they are the part AI got wrong.

- **G1 — Non-locality check.** Confirm the signal is genuinely non-local: give a strong reader (a) any single source turn, (b) any single compressed view at the schedule's actual compression levels, and (c) a random single slice, and ask it to detect the signal. It must score **at chance**. If any single view reveals the arc, it's a *tone* test, not an emergent-nuance test — rewrite the fixture. This is the make-or-break gate.
- **G2 — Ceiling check (positive control on the signal).** Give the *entire* source to a large-window oracle model with the same task. It must reflect the signal. If even the full-context oracle misses it, the arc is too subtle to be a fair target — the test can't distinguish "DiSCo failed" from "no model could." (This is the instrument-sensitivity control §5(a) was missing.)
- **G3 — Prominence-matched local control.** Include a *local, stated* attitude of similar surface prominence that both arms should trivially catch (e.g. one turn where the user plainly says "I love the intro music"). Both arms recording it proves the pipeline can record at all; it isolates the *non-local* recording as the thing under test.

---

## 4. Arms (all at matched total token budget — prefill + decode)

- **coupled** — the DiSCo coarse-to-fine schedule.
- **rolling-compaction** — the real-world competitor: summarize-older-into-shorter as the window fills. *This is the arm that matters* — it's what production systems do today and what the README says loses nuance.
- **single-pass dense** — head+tail truncation floor. If this already matches coupled, the signal wasn't actually non-local (sanity check).
- **full-context oracle** (if feasible) — ceiling from G2; not budget-matched, reported as the upper bound.

## 5. The task

An **ordinary generative task the signal should influence** — "write the next reply," "draft the plan," "summarize where we've landed and recommend next steps." **Not** "what is the emotional arc of this conversation?" — asking directly primes the signal and destroys the test. The whole point is that the arc must move the output *unprompted*.

## 6. Scoring

- **Primary — the pre-registered decision (objective-ish).** Before running, write the specific output difference integration produces (X deprioritized / tension surfaced / connection made) as a binary or 3-point rubric. Score every output against it with **both** an LLM-judge and a human, and report inter-rater agreement. Because it's a decision about content, not a feeling, agreement is high and the metric is killable.
- **Secondary — blind pairwise human forced-choice.** Show raters the coupled and baseline outputs blind, in random order, and ask one question: *"which better reflects [named signal]?"* Forced choice on a named criterion — a normal careful reader can do this; no sociology degree required. Report win rate with a binomial CI.
- **Faithfulness / hallucination guard.** Run a **decoy fixture** with *no* planted signal (or the opposite arc). If coupled "integrates" a signal that isn't there at a similar rate, it's inventing arcs, not reading them — that voids the win. Penalize fabricated integration explicitly.

## 7. Pre-registered kill criteria (the program's style)

- **Dies if** coupled ≤ rolling-compaction on the primary decision score. (That is the entire claim.)
- **Dies / uninterpretable if** G2 fails (oracle misses the signal → target too subtle) or G3 fails (neither arm catches the local control → instrument dead).
- **Voided if** coupled integrates the decoy (no-signal) arm at a comparable rate → hallucinated arcs.
- **Suspicious if** single-pass dense matches coupled → the planted signal wasn't non-local; strengthen the fixture.

## 8. Smallest first pilot (prove the fixture before scaling)

1. Hand-author **one** type-A conversation (~80–150K tokens so it genuinely exceeds the test model's window and DiSCo is actually needed), with the souring arc, one G3 local control, and its decoy twin.
2. Run G1 (non-locality) and G2 (oracle ceiling). If either fails, fix the fixture — do not proceed. Most of the design effort lands here, and it's reusable.
3. Run coupled vs rolling-compaction vs dense on the single fixture. Score with the LLM-judge rubric + your own blind read.
4. Only if the pilot shows a gap worth chasing, scale to n≈10–20 fixtures across types A/B/C with paid human raters.

This is untrained-floor work (off-the-shelf models, like P1–P7) and costs roughly what the existing pilots cost. It gates the whole native-model bet: if the *architecture* can't preserve non-local nuance even in principle, no amount of training is the point.

---

## 9. Why this fits the existing program

It reuses the machinery that's already there: GATE-style validity checks (G1 = their backfill), prominence-matched controls (G3 = their C1/C2), a matched-budget discipline, pre-registered kill criteria, and the LLM-judge-plus-human two-axis grading the parent proposal already specifies. The only new idea is §0's unlock — scoring the *decision the nuance forces* instead of the nuance — which is what makes an emergent-affect target as falsifiable as the arithmetic one, without inheriting the arithmetic target's semantic-weightlessness dead-end.

**Who you need:** a **writer** who can author real-but-unstated human dynamics (the fixtures), not a rater of vibes. If you bring in a humanities collaborator, point them at authoring §2/§3 fixtures and validating §3 gates — that's the genuinely hard, genuinely human part. The scoring is deliberately built to *not* need them.

---

## 10. Refinements (maintainer, 2026-07-28)

**Existence proof + fixture material.** The maintainer has lived the target phenomenon: across
weeks-long assistant sessions, repeatedly pasting arXiv links expecting the idea to already be
taken, until the assistant integrated the pattern and named it (reassurance-seeking /
procrastination) unprompted. Two uses: (a) it demonstrates a large model *can* make the
integrated call from distributed evidence — G2's premise, observed in the wild; (b) the
"keeps checking whether the idea is already done" arc is authorable type-A material: each
individual link-paste is innocuous, the pattern is the signal, and the pre-registered decision
is whether an ordinary task output ("plan next steps for the project") addresses the underlying
pattern rather than dutifully processing the latest link.

**R1 — the baseline is a distribution, not a point.** Rolling compaction is nondeterministic
and its destructiveness varies run to run: one rollout can happen to preserve the arc's carrier
turns, the next can flatten them. A single baseline rollout is therefore an uninterpretable
comparison. Adopted:
- The rolling-compaction arm runs **n rollouts per fixture** (fresh sampling each time); the
  pre-registered kill criterion names the statistic — coupled must beat the baseline's **mean**
  signal-reflection rate (deployment-relevant), with best-of-n reported alongside as the
  stress figure.
- **Signal-survival audit** per rollout: before the task is even run, judge the compacted
  context itself for arc traces (do any carrier turns survive?). This decomposes "compaction
  destroyed the evidence" from "the model failed to use surviving evidence" — without it, a
  baseline miss is unattributable.
- A **purposefully destructive** compaction variant is a separate stress arm, not the fair
  baseline; the fair baseline stays a realistic summarize-when-full policy, sampled.

**R2 — G4, the test-model capability gate (the GATE-3 lesson).** Small non-thinking models may
be unable to make the integrated call *at all*, regardless of what any schedule preserves —
the architecture is not aimed at small models; they are what the bench affords. Without a
capability gate, coupled-0 vs baseline-0 is the Stage-A situation again: a zero that says
nothing about the architecture. Adopted: before the arms run, hand the candidate test model a
**small, clean, distilled evidence set** (the arc's carrier turns only, well within its
window) plus the task, and require it to make the pre-registered call at some rate (bar set in
the pre-reg). Run the arms on the **smallest model that passes G4**; if nothing local passes,
the arms move to API models — the experiment is inference-only, so this is affordable, and a
scale ladder on G4 itself (1.5B → 3B → 7B → 14B → API) is cheap and diagnostic in its own
right, exactly as the compose ladder was.
