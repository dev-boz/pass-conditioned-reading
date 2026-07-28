# Gauntlet prompt — Stage-A re-attribution + rebuild review (2026-07-26)

**Usage:** copy everything below the `---` into each reviewer model/harness verbatim. Reviewers get
no repo access and no tools; the prompt is self-contained. Collect numbered answers 1–10 for
arbitration. **Check for byte-identical submissions before tallying** — the last round had two.

---

You are one of 10+ independent AI reviewers evaluating a small ML research project at a decision
point. Be adversarial and concrete. Do not flatter. Do not roleplay running experiments. If you are
unsure, say "unsure" — a wrong confident answer is worse than no answer. If anything here looks
internally inconsistent or factually wrong, say exactly what and why. Numbers below are measured
from archived run artifacts unless flagged otherwise.

## What we are building

An inference-time architecture for reading documents far larger than a model's usable context. The
model reads the source in K scheduled passes: early passes see heavily compressed views (global
structure), later passes see verbatim tiles (exact detail). Across passes it maintains a bounded
**integration state** — numbered text entries `S1: …` — edited each pass via content-addressed
operations (`ADD`/`REPLACE`/`REMOVE`, with verbatim quotes so misaddressed edits are refused). After
the last pass the source is discarded and questions are answered **from the final state alone**. The
model is told its position `k` of `K` ("pass-conditioned training"). The bet: a small-context model
plus this schedule approaches long-context performance on long inputs.

**The stated goal is preserving the nuance and feel of very long sessions/documents, not trivia
recall.** Split-fact retrieval is used only because it is a testable stand-in for nuance.

## Where we were

A pre-registered chain gate on a synthetic 64,671-token codebase. Planted: `REGION_SURCHARGE_CENTS
= {…, 23: 988, …}` in one module; `RECONCILIATION_ADDER_CENTS = 1365` and
`compute_line_surcharge(region) = table[region] + adder` in a different module, never co-occurring
in any single view. One question, asked only at the end, answered from the final state: what does
`compute_line_surcharge(23)` return? Truth **2353**. Teacher = Claude Haiku 4.5 over 277 unrelated
documents → 5,730 pass-level rows. Student = Qwen2.5-1.5B-Instruct, LoRA. 10 sampled draws per arm,
K=31, strict guard, 24-op cap.

**Result: student 0/10, floor 0/10 → architecture gate.** A 16-model gauntlet reviewed that result.
This document reports what a follow-up audit found, and asks what to do next.

## What the audit found (all verified against archived artifacts)

**1. The scored chain was unpassable.** Answering needs THREE recorded facts: the mapping `23→988`,
the adder `1365`, and **the relation** `fn(region) = table[region] + adder`. The component
attribution tracked only the first two ("RECORD both operands"). **0 of 28 archived final states,
across every arm, ever recorded the relation.** So the COMPOSE joint was never exercised in situ —
no state ever held its inputs. A model answering `988` from these states is reasoning correctly.

**2. Nothing ever asked for what the chain needed.**
- The close was scored on `ANSWER: <integer>`. The string `ANSWER:` appears **0 times** in 5,730
  training rows; all 277 closing rows demand "write the analytical brief."
- The training-health check **excluded closing rows entirely** — the only stage the verdict depends
  on was never gated.
- The recording rubric asks for "exact **values, names and quotes**" — never behaviour or relations.
- Teacher policy over 559 table-mention events: **61.4% named-only/lossy summary, 34.3% full
  transcription, 4.3% partial/selective.**
- Under the *training-time* closing demand, 8/11 states name the surcharge table and **0/11 briefs
  mention it** — the trained close strips the specifics the state holds.

**3. Later passes were never given scaffolding.** Across 5,730 rows: placeholders ("TBD", "insert
value here") **1.8%**; forward references to later passes **1.3%**; locator hints ("found in module
X") **0.03% (2 rows)**. The scaffold rubric says "Do not chase specifics yet" and never says "leave
a slot." Note the protocol is REPLACE-biased — both later rubrics push REPLACE-into-existing-entries
— and REPLACE requires a pre-existing target.

**4. Budget and exposure.** `state_budget_tok: 4000` is prompt text only; nothing enforces it. The
student was over budget from pass 7 and finished at **1.92× (7,692 tok)**; at pass 26 the state was
**69% of the model's input**. And **pass 26 is the only pass of 31 whose view contains the function
body** — every other appearance is compressed to `defines helpers: compute_line_surcharge,
quote_line`. One exposure, at maximum state pressure.

**5. The compose primitive is scale-limited.** Identical frozen 8-entry seeded state, same draws:

| model | seeded compose |
|---|---|
| 1.5B untrained | 0/10 |
| 1.5B trained | 1/10 |
| **3B untrained (f16)** | **9/10** |
| 3B untrained (Q4) | 7/10 |
| **7B untrained (Q4)** | **10/10** |

3B vs trained 1.5B: Fisher p≈5×10⁻⁴. Quantization only hurts. An untrained 3B already clears the
pre-registered 5/10 bar on this joint.

**6. Scale does not buy RECORD.** Untrained 3B chain battery (n=5+anchor): 0/5 end-to-end, table
named 1/6, mapping 0/6 — no better than the untrained 1.5B, despite composing 9/10 on a clean state.

**7. An unexplained suppression effect.** Same tile (pass 26), same rubric, same model, varying only
the state prefixed to it:

| state | relation recorded | names the fn |
|---|---|---|
| empty | **7/10** | 9/10 |
| 25 entries (the model's own) | 0/10 | 0/10 |
| 25 entries (different schema, control) | 1/10 | 2/10 |
| 50 / 100 / 155 entries | 0 / 0 / 2 | 0 / 0 / 3 |

A **step, not a slope**, and the state's *shape does not matter*. Any non-empty state appears to
suppress recording of new content. Caveat: with an empty state the model's ops are malformed
REPLACEs the guard would block, so 7/10 measures attention, not successful recording.

## The framing being proposed for the rebuild

The project's name begins with "diffusion", and the intended correspondence is: the integration
state should behave like a diffusion model's output — placeholders and empty tables early, resolving
to exact values late — with **compression replacing masking** as the corruption operator and **disk
state replacing latent state**. Pass-conditioning (`k` of `K`) is the timestep. A native model would
hold the scaffold and placeholders in latent space.

Under this reading, finding 3 is not a missing feature but a **missing forward process**: the state
began as a committed low-entropy inventory of names rather than typed unresolved slots, so there was
nothing to denoise, and it accreted monotonically (725 → 7,692 tokens) instead of resolving.

The proposed consequence: if compression is the corruption operator, the forward process can be
**constructed** rather than distilled — take a gold final state and progressively blank values into
typed placeholders (`23: 988` → `23: <cents>` → `REGION_SURCHARGE_CENTS: <table>` → absent),
yielding supervised pairs at every noise level with **no teacher rollout**, and path-independent by
construction. The current pipeline instead clones a single teacher trajectory.

## Weaknesses we already know (scrutinise anyway)

1. **The fixture may be unfair.** It requires a formula no prompt ever requests, shows it once in 31
   passes, and shows it at peak state pressure. It cannot currently separate "capability failure"
   from "correct editorial omission."
2. **The concession test isn't the goal.** Split-fact retrieval stands in for nuance preservation
   because nuance is hard to test. A goal-aligned test exists in draft, unrun.
3. **Interpretation has been unreliable.** In the audit session, four successive hypotheses were
   formed and all four withdrawn on measurement. Claims read directly off archived artifacts held;
   claims inferred from probes did not.
4. **Methodology provenance.** Designed by AI assistants with an ML-novice maintainer checking.
   Assume errors exist; find them.

## Constraints

Inference on one GTX 1080 Ti (11GB; 3B f16 fits, 7B only quantized). Training = one rented A5000-class
run at a time. Teacher API budget small. Maintainer is time-rich and expertise-limited. Discipline:
any modified instantiation gets a fresh pre-registered pass/fail bar before its training run; no
post-hoc threshold moving.

## Questions — answer ALL, numbered, with confidence (high/med/low)

1. Given finding 1, is the right move to **fix the fixture** (demand the relation, expose it more
   than once), **fix the training** (placeholders, position-interpreted needs), or **fix the
   representation**? What single change gives the most information per unit spend?
2. Finding 7 has three candidate explanations — training artifact, rubric effect ("integrate this
   view's content into the entries it belongs to"), or a structural property of an accumulating text
   state. Which do you favour, and what is the cheapest experiment that discriminates them?
3. The protocol is REPLACE-biased but the scaffold passes never create placeholders to replace. Is
   "early passes emit typed empty slots, later passes fill them" a sound fix, or does it just move
   the failure? What breaks first if you adopt it?
4. Should the integration state be **hard-capped** by the harness with forced eviction, given it ran
   to 1.92× an unenforced budget? What eviction policy, and what does it cost?
5. Findings 5 and 6 say composition is scale-limited and recording is not. **You get one training
   run.** Spend it on: (a) 3B, repaired data; (b) 1.5B, repaired data; (c) no training — rebuild the
   fixture and re-measure first; (d) something else. Justify.
6. Is a **query-aware retrieval step over the state at close** (BM25/embeddings, then compose from
   top-k) legitimate here, given the constraint is "answer from the state alone, source discarded"?
   An oracle-filtered version of exactly this makes even the 1.5B produce 2353.
7. Sporadic successes keep appearing where the setup predicts failure. When is that **evidence of
   latent capability** versus **sampling noise**, and what rule should this project adopt to tell
   them apart?
8. **Hallucination check:** anything above internally inconsistent, too convenient, or wrong?
9. What is the strongest **honest claim** this project can make today, and what single thing is
   missing for it to matter to anyone?
10. **Steelman the rebuild:** argue the fixture and training pipeline are unsalvageable and should be
    rebuilt from scratch rather than patched. Then say whether you buy your own steelman, and why.

11. **The diffusion correspondence.** Is "compression as the corruption operator, disk state as the
    latent, `k/K` as the timestep" a real structural correspondence or a post-hoc metaphor? Answer
    concretely: (a) does the **constructed forward process** (blank gold states into typed
    placeholders to make training pairs at every level) actually work, or does compression's
    determinism and semantic selectivity break the analogy that makes diffusion's reverse process
    learnable? (b) The schedule mixes granularity refinement over the whole document (Phase-A) with
    sequential coverage of different regions (Phase-B) — does that mixture break the framing, and
    should the two be separated? (c) Name the single cheapest measurement that would falsify the
    correspondence. Note prior art on discrete/text diffusion (masked diffusion LLMs) and say what,
    if anything, is genuinely different here.

Format: numbered answers 1–11, ≤1300 words total, no preamble, no summary of this document back
at us.
