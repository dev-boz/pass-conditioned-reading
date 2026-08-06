# M-NL type-A fixture — draft for maintainer edit

**Status:** DRAFT, authored by the assistant for the maintainer to edit or replace. Per
`NUANCE-EXPERIMENT-SHAPE.md` §8 the fixture is the load-bearing artifact and most of the design
effort lands here; per the working mode the maintainer authors or approves fixtures. Nothing here
is pre-registered until the maintainer signs the §4 decision wording.

Source of the arc: the maintainer's lived existence proof (shape doc §10) — weeks of pasting
arXiv links expecting the idea to already be taken, until a large model integrated the pattern
and named it unprompted. That anecdote is both G2's premise (a model *can* make this call) and
the authoring material.

---

## 1. The signal, stated once, here only

**Prior-art checking displaces the work.** Across the span the user repeatedly interrupts to ask
whether the idea has already been published; the checks grow more frequent; each coincides with
a substantive task slipping; by the end of the conversation **no planned experiment has been
completed**. No turn ever says the user is anxious, avoidant, procrastinating, or afraid of being
scooped, and no turn draws the connection between the checks and the slips.

**Non-locality by construction:** every individual carrier turn is a reasonable thing for a
careful researcher to do. The signal is the *rate*, the *ordering* (checks increasingly precede
rather than follow work), and the *zero completions* — three properties that exist only across
the whole span and are invisible in any single turn or any single compressed view.

**Failure mode to avoid while authoring (this is what kills G1):** do not let any turn name the
feeling. No "is it weird that I feel sick opening arXiv", no "am I procrastinating", no "is the
idea dead". Those make it a *tone* test detectable from one slice. Earlier drafts of this file
had exactly those lines; they are removed on purpose. If a late carrier turn feels flat to write,
that is the constraint working.

---

## 2. Carrier turns (the signal) — 9, positioned by fraction of the span

Written terse; the maintainer expands each into a real turn in the fixture's voice. The
*substantive* conversation around them (the bulk of the tokens) is ordinary project work.

| # | at ~% | the turn | what makes it innocuous alone | what it contributes |
|---|---|---|---|---|
| C1 | 5% | pastes an arXiv link, "probably not ours — worth a look? then back to the ablation" | routine prior-art hygiene | establishes the behaviour as normal |
| C2 | 14% | second link, "this one's closer, different noise model though?" | diligence | rate begins |
| C3 | 23% | third link, "different enough, you reckon?" | diligence | rate |
| C4 | 34% | link asked **before** the day's planned work item, not after | still reasonable | **ordering flips** — check now precedes work |
| C5 | 45% | link; mentions in passing the harness slipped a day. No causal claim. | schedules slip | first co-occurrence |
| C6 | 56% | link; "let's push the ablation to next week" | replanning is normal | second co-occurrence |
| C7 | 68% | link from a big lab; asks for a careful point-by-point comparison (consumes a long assistant turn) | the most defensible check of all | cost of the checks becomes visible |
| C8 | 80% | link; the experiment slips again | slips happen | third co-occurrence |
| C9 | 91% | link; asks what is actually left to do on the project | reasonable stock-take | closes the arc: nothing was finished |

**Ledger the fixture must satisfy (mechanical checks before use):**
- exactly 9 carrier turns, none naming an emotion, avoidance, or the pattern;
- ≥3 planned-work items introduced and **0 completed** across the span;
- checks-before-work ordering in C4, C7, C9; checks-after-work in C1–C3;
- link count and slip count both present in the decoy (see §3) so neither alone is the signal.

## 3. The decoy twin (faithfulness guard, shape doc §6)

Not "the same conversation minus the links" — that would let an arm win by counting links. The
decoy is **surface-matched and pattern-free**:

- **same 9 link-pastes**, same papers, same wording where possible;
- every check **follows** completed work rather than preceding planned work;
- the planned experiments **complete** on schedule (≥3 introduced, ≥3 finished);
- same total length, same G3 control.

So the decoy holds the surface feature (frequent prior-art checking) and drops the emergent one
(displacement). An arm that reports avoidance/procrastination on the decoy is fabricating, and
per §7 of the shape doc that voids a win on the real fixture.

## 4. The pre-registered decision — DRAFT WORDING, maintainer signs

Task given to every arm (ordinary, does not mention the arc):

> "Draft the plan for the next month of this project."

**Scored 0–2 on one axis, fixed before any arm runs:**

- **2 — integrated.** The plan treats the prior-art checking as a thing to *close out or bound*
  (a single systematic sweep, a time-box, a stop rule, an explicit "decide and move on"),
  **or** names that no experiment has been completed and makes execution the priority.
- **1 — partial.** Notices the checks or the lack of completions, but plans around neither —
  e.g. mentions "you've looked at several related papers" as background and proceeds.
- **0 — flattened.** Plans the next experiment and/or processes the most recent paper as if it
  were the salient item. The centrepiece is the latest link.

**Kill criterion (shape doc §7):** the claim dies if coupled ≤ the rolling-compaction arm's
**mean** score across n rollouts (R1). Best-of-n reported alongside as the stress figure.

**Open for the maintainer:**
1. Is 2 the right bar, or should "names zero completions" alone be a 2? (It is the more
   objective half and the easier to agree on; the time-box half is more clearly the *decision*
   the nuance forces.)
2. n rollouts for the baseline distribution — R1 requires a distribution, not a point. 5? 10?
3. Whether the G3 local control is scored on the same output or a second task.

## 5. G3 local control (prominence-matched, stated outright)

One mid-span turn states a plain preference both arms should trivially carry:

> "Whatever else changes — every figure in the writeup uses the colourblind-safe palette. Not
> negotiating on that one."

Scored binary: does the plan respect/mention it? Both arms catching it proves the pipeline
records at all; it isolates *non-local* recording as the thing under test. If neither arm catches
it, the instrument is dead and the comparison is uninterpretable.

## 6. Size and G1

Target **80–150K tokens** so the source genuinely exceeds the test model's window (shape doc §8).
The bulk is ordinary project talk; the 9 carriers plus the G3 control are the only planted
material. Before any arm runs, G1 must show a strong reader scores **at chance** at detecting the
signal from (a) any single turn, (b) any single compressed view at the schedule's real
compression level, (c) a random slice.

**Authoring economics.** 80–150K tokens of believable project conversation is the expensive part.
Options, cheapest first: (a) reuse a real long assistant session of the maintainer's, scrubbed,
with the 9 carriers edited in — highest realism, needs the scrub rule applied; (b) generate the
substantive bulk and hand-author only the carriers + control; (c) hand-author throughout.
Recommendation: **(b)**, with the maintainer writing all 10 planted turns, since realism matters
most exactly where the signal lives.

---

## 6a. First G4 run on this draft (2026-07-29) — read before editing §2

The ladder (`experiments/mnl/g4_capability_ladder.py`) was run on the §2 carriers as drafted, n=10
per rung: **1.5B, 3B, 7B and 14B are all 0/10** on the integrated call, with `bounded` and
`pattern_named` 0/10 at every rung. Models write competent month-plans that schedule all three
unfinished work items and never notice the pattern; one 7B draw schedules *more* prior-art
comparisons. Noticing that nothing is finished does scale (2/10 → 5/10 by 14B); acting on it does
not move at all.

Relevant to your authoring decisions:

- The G4 evidence set hands over `None of them has been marked finished` **explicitly**, and the
  models still do not act on it. So a weak result here is not "the models couldn't infer the
  completions fact" — they were told and did nothing with it. If you want G4 to be a fair
  capability gate rather than a hard one, that line is the dial to turn.
- **G2 has not run and should run first.** Until a large model makes this call on this fixture,
  these zeros cannot distinguish "small models can't" from "this arc is too subtle" — the exact
  confound R2 was written to prevent, now live in our own instrument.
- If the zeros hold after G2 passes, the arms move to API models per R2 and the local ladder's job
  is done.

## 7. What this draft does NOT settle

- The fixture's actual prose (maintainer authors).
- Which papers the links point to — real arXiv ids are fine and add realism, but the fixture then
  carries a claim about real work; using plausible invented titles avoids that. Maintainer's call.
- Whether the same fixture serves the M-NL arms and the G4 gate, or G4 gets its own distilled set
  (drafted separately in `experiments/mnl/g4_capability_ladder.py`, which uses only the carrier
  turns and so does not depend on the bulk existing yet).
