# P6 — PREFLIGHT INVALIDATION (run BLOCKED before any model spend) · 2026-06-16

Source-only analysis (no arms run) found the P6 design is **not discriminating** on the
Sandpiper fixture. Recorded here before any compute so the decision is auditable. This is a
pre-run, source-inspection finding (not an outcome), so amending the design now is not a
pre-registration violation — but the redesign is the maintainer's scientific call.

## What the pre-reg claimed
> "a head+tail / RAG-on-endpoints reader has the cap (head) and the final direct decision
> (tail) but **cannot have L3** — the reason retail failed ('full fleet' / 'holiday density')
> lives in seg9 only (verified)."

The L3 *phrases* ("full fleet" / "holiday density") are indeed seg9-exclusive. But the test
scores **answers**, and the L3 *substance* (Meridian needed holiday volume far above the
8,000 cap → retail collapsed) is **recapped in the dense tail**.

## The two findings (model-free, from source)

1. **Numeric matcher leak (advisor catch).** `score_chain`'s discriminating path counts L3 if
   `("30000" or "40000") and ("meridian" or "retail")` co-occur. The dense head+tail context
   contains `30000` (tail) + `meridian` + `retail`, so a dense answer can score L3=True with no
   mid-doc access. The handoff's phrase-only guard would not have caught this.

2. **Fixture-level premise failure (decisive).** The dense tail (turn-idx 345–389) covers
   **seg15–16**, and **seg16 (turns 367–390) is an explicit "trace the full arc" synthesis
   recap** of the entire conversation. It states every link of the gold chain in prose,
   including the L3 hinge:
   - turn 370: 8,000-unit Halvorsen/Tallinn cap, Inkstone 14-week lead (L1)
   - turn 372: Meridian Outfitters, 120 stores, retail vision (L2)
   - **turn 373: "Meridian needed enough inventory to actually stock 120 stores for the
     holidays. Which isn't 8,000 units. It's closer to 30,000 or more." (L3 substance)**
   - turn 374: + 45–50% retail margin + 18-month exclusivity clause
   - turns 377–381: pivot to direct, Founders' Edition invite-only (L4)
   - turn 379/382: waitlist toward 25,000 (L5)

   A head+tail reader is therefore **handed the complete causal answer**, so coupled-vs-dense
   cannot measure whole-document synthesis here. Running it risks a **false-positive "win" by
   luck** (a 600-token dense answer that happens not to surface the buried recap) entering a
   *published* track record as a clean result — the outcome most to avoid.

## Why the obvious patches don't work
- Tightening / dropping the numeric matcher fixes finding 1 but **not** finding 2 (substance is
  in the tail regardless of phrasing).
- Gerrymandering the dense baseline to exclude seg16 is cheating: a real head+tail reader gets
  the closing recap.
- Redefining L3 as "the ordering/trace" to make it discriminate would be post-hoc
  goalpost-moving.

## Consequence for the battery on this fixture
seg16's whole-arc recap also leaks the other handoff battery ideas that have a *stated* answer:
(a) what-was-rejected-and-why (subscription kill + limited-store rollout are both in seg16),
(b) premise↔decision consistency (seg16 discusses values vs strategy explicitly), and
(d) strategy-evolution trace (seg16 *is* the evolution trace). Only idea **(c) distributed
inference — an UNSTATED conclusion** the reader must infer from scattered evidence — survives,
because a conclusion stated in no segment (incl. seg16) cannot be retrieved from head+tail.

## The light edit was tested and REJECTED (seg13 restates the hinge)
Simulated removing seg14–16 and rebuilt the dense head+tail selection: the new tail lands on
**seg12–13**, and **seg13 (the decision segment) restates the L3 causal hinge 5+ times**:
- turn 291: "We couldn't have stocked Meridian's 120 stores with 8,000 units"
- turns 296/297/308/317: "because Halvorsen Assembly can only make 8,000 units before the
  holidays, a wide retail launch was never supply-able for this window... We couldn't have met
  Meridian's volume requirement."

The reason retail failed is **inseparable from the decision**: seg13 exists to make and justify
the pivot, and the justification *is* the cap-vs-volume collision. Scrubbing it would gut seg13
and make the pivot incoherent. So removing the recap does **not** de-leak; this story explicitly
articulates and repeatedly restates its conclusions across seg13–16, so **any "trace/why"
question is reachable by a head+tail reader** on this fixture — edited or not (short of gutting
the decision segment).

## Recommendation (maintainer to decide) — two honest paths

**(A) Distributed-inference probe — recommended (handoff idea c, "cleanest anti-RAG").**
ADD scattered premises across the doc that *imply* a conclusion the characters **never state**;
ask for the conclusion. Immune to recaps by construction (a conclusion stated nowhere can't be
retrieved from head+tail). Reuses the story by *addition* — does not touch P4/P5 planted facts,
no incoherence risk. New guard: substance-reachability (head+tail cannot produce the conclusion),
verified by manual read, not just the matcher. More authoring, but the test that actually holds.

**(B) Reframe via the maintainer's "edit-the-compressed-slices" lever — narrower fallback.**
Drop the dense-head+tail-beating claim (unsalvageable here). Instead test scaffold-vs-no-scaffold
*assembly*: hand-trim the L3 hinge out of the coupled arm's Phase-A compressed views (legitimate —
compression quality isn't under test), deliver it only via the single verbatim Phase-B tile, and
ask whether `coupled_full` (scaffold helps attach it) integrates the hinge better than
`verbatim_only` (tile, no scaffold). No head+tail baseline; a weaker, different claim.

Recommendation: **(A)**. It is the probe the handoff itself names, the advisor endorses, and the
only one that survives this fixture's relentless self-restatement.
