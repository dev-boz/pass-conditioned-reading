# The use case, in the maintainer's own terms — and what it does to the cost story

**Status:** framing, recorded 2026-08-06 from the maintainer. Design intent and origin, not
results; nothing here is tested unless it cites a result doc. Companion to the README scope
section and `DISCO-NATIVE-ARCHITECTURE.md` §1.

## 1. Where the architecture actually came from

Weeks-long, single-topic conversations with frontier models (Sonnet/Opus class), returned to
every couple of days. Two observations, in tension:

- as the sessions grew, the model started **forgetting small details** — window limits and
  compaction doing what they do;
- the same bigness was what let it **notice things** — distributed patterns like the arXiv
  prior-art checking arc, integrated and named unprompted.

The architecture was imagined to get **both**: the fine detail and the noticing. The 08-05/08-06
results give that wish a precise technical shape. Noticing lives in the *reader* and survives
intact when the evidence is concentrated (G2 premise check: sonnet 10/10 on the distilled
carriers). The state is *exactly sufficient* (compose ladder: what it holds, any reader ≥3B
uses; what it lost, nothing recovers). So the job of everything upstream is: **a bounded state
that does not destroy the evidence patterns are made of.** The recorder does not need to
understand a pattern; it needs to not shred its carriers.

## 2. The cadence, and why the linear-cost caveat mostly dissolves here

The parent README's stated tradeoff — token use grows linearly with context — assumes the
reading happens in the user's face. This use case is **sporadic**: return once a week or every
couple of days. So the refresh runs **while the user is away** — asynchronous, batched,
recorder-priced tokens — and the expensive model the user actually talks to reads a bounded
state at normal per-message cost. You pay **per visit, not per turn**, in cheap tokens, with
no one waiting on it. For a user who would already pay extra to make a weekly return richer,
the trade was acceptable up front; amortized this way it is close to invisible.

## 3. Incremental recompression (maintainer, 2026-08-06 — design intent, untested)

A conversation only ever **appends at the end**. Every tile whose span is entirely in the past
is content-stable — cache it, never re-render it. A refresh therefore re-renders only:

- the **level-1 whole-session view** (always changes — it covers everything), and
- the **final tile at each level** (the only tile per level whose span includes new turns):
  pass 1, slice 2-of-2, slice 4-of-4, slice 8-of-8, and so on down the ladder.

On the current test shape (V=3000, six levels, 63 passes) that is **~7 re-rendered views
instead of 63 — roughly a tenth of a full re-read** — and only the passes whose views changed
re-run against the persistent state. Where the growing tail breaks tile alignment, alternate
tilings (strict 1-2-4-8, or 1-3-5-8, or whatever fits) so the old tiles stay frozen.

Two engineering notes to carry with the idea:

- the pyramid validator currently **enforces strict doubling (G1)**; incremental mode relaxes
  that deliberately. Make it an explicit mode with its own guard wording, not a silent drift —
  the schedule discrepancy was exactly a silent drift.
- the measured caveat (08-05): **every additional editing pass re-exposes what is already
  recorded** to the edit policy — doubling the pass count doubled the clobber exposure.
  Incremental updates keep the per-visit exposure small, and the `retain` guard is the standing
  mitigation; a full deep re-read stays an occasional event, not the default.

Further cost levers floated (pass-skipping, and others): all of them should surface as
**user-tunable sliders** — richness vs cost per refresh — not fixed policy.

## 4. Niche, said plainly

This is a niche use case and the maintainer is upfront about it: people who live in long,
sporadic, high-value sessions and would pay to make each return richer. That is the honest
market, and the honest scale of the claim.

## 5. The recorder/reader split — its actual status

**Not a design goal.** It fell out of testing (the close-only ladder), and it stands as a cost
*option* on one condition: **that it is not detrimental to output.** If recorder scale turns
out to improve output quality, the maintainer's call is to spend on the recorder — quality
outranks the cost win. The stack-search plan measures exactly this (recorder scale is an F1
axis), so the condition is checkable rather than aspirational.

## 6. The evolution path, if it earns one

Prompting → training → custom LLM. The floated end-state: a model that builds and maintains
the state **internally**, so the state-keeping becomes part of how it reasons rather than a
harness around it — the direction sketched in `DISCO-NATIVE-ARCHITECTURE.md` (slot-bank state,
schedule position injected structurally), with that doc's own quarantine kept in force: latent
*views* stay out, because they kill the audit-trail and recoverability properties that make
the on-disk design worth having. Recorded as a direction, not a plan; every step of it sits
behind the existing gates.
