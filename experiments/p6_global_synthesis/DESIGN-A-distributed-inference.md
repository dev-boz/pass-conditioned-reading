# P6 (revised) — Distributed-inference probe · DESIGN DRAFT

> **STATUS 2026-06-16: the "deadline" and "Q2-unsupported" inferences below are BOTH DEAD.**
> Advisor + source-grep killed them:
> 1. Headline must be **coupled_full vs verbatim_only** (coverage held constant) — "coupled
>    beats dense by seeing a mid premise" is just coverage = P4 redux. Dense = coverage control.
> 2. The fixture **pre-empts its own inferences**: the "Q2 repeats the holiday supply failure"
>    conclusion is already stated verbatim in **seg8 turn 194** ("a full rollout in Q2... would
>    put us in the same supply bind one season later"); second-source-closed is in seg2 t29;
>    Q2-reliability-depends-on-panel-PO in seg15 t366. This story contains its own complete
>    analysis, so NO anti-RAG target can be built on *existing* latent implications.
> **PIVOT (pending advisor): plant a fully self-contained, ORTHOGONAL distributed inference** —
> new isolated factual asides in distant segments that the characters never combine (different
> threads, different reasons), with a conclusion I author and guarantee is stated nowhere and not
> single-window-derivable. Candidate: a staffing/ownership gap (e.g. the person who owns the
> numbered-packaging-line setup is on leave during the exact Sept–Oct setup window) — qualitative,
> no arithmetic, premises fully under my control. Headline metric = coupled_full vs verbatim_only.
> Everything below this line is the prior (dead) draft, kept for the record.
>
> **UPDATE — staffing-gap plant also DEAD (3rd design, same root cause).** Advisor: these
> characters audit execution risk obsessively (seg15 t365 "Is anything missing?"; seg13 t314
> frets about discovering packaging problems "in October") — a critical-path staffing conflict
> is exactly what they catch. A plausibly-buried needle reads as "implausibly-missed multi-hop
> retrieval," not understanding, and reintroduces the C2 critique this fixture defeats.
> **The criterion any Sandpiper plant must meet:** the unstated conclusion must be something
> these risk-hunting characters would *genuinely never compute* — i.e. **not a risk and not
> decision-relevant**. On a fixture whose back third is "what did we miss," that target is
> tiny; the *ease* with which each candidate dies (root cause→seg16 t388; cost aggregate→they
> compute margins; staffing gap→the audit catches it) is itself the finding.
>
> **FORK for the maintainer (their scientific call — comparability vs robustness):**
> - **(A) Purpose-built fixture or a deliberately-designed Sandpiper *extension*** where I
>   control the characters' knowledge-state so the conclusion is unavailable to them *by
>   construction* (premises in compartmentalized domains they never co-attend). Only robust
>   guarantee of an unstated-yet-true conclusion. Cost: a fresh fixture loses direct same-doc
>   comparability with P4/P5 recall; a designed extension preserves more of it. **Advisor leans
>   here; so do I.**
> - **(B) One more orthogonal-plant attempt on Sandpiper** meeting the criterion above. Cheaper
>   if it lands; we've now watched how readily it doesn't.
>
> **Honesty to weigh:** my own calibrated prior (P4 = misses were *salience*, not eviction;
> P5 = the lever is *query-conditioning*) predicts the coupled_full-vs-verbatim_only headline
> **likely NULLS** — if eviction isn't the bottleneck, a scaffold that prevents eviction won't
> move it. Building a new fixture for a predicted-null headline is a legitimate choice (probe #1
> of a battery; a documented null is informative), but the effort should be spent with eyes open.

---

# (DEAD) P6 (revised) — Distributed-inference probe · DESIGN DRAFT (pre-advisor, pre-implementation)

Supersedes the original P6 trace design, which was invalidated pre-run
(`PREFLIGHT-INVALIDATION.md`): the Sandpiper story explicitly restates its causal chain
throughout seg13–16, so a head+tail reader reaches any "trace/why" answer. The fix is an
**anti-RAG** target: a conclusion **stated nowhere** that must be *computed* from premises
**distributed** across the document, with at least one premise **mid-doc-exclusive**.

## The inference (a forced deadline)

Three premises, three regions; the conclusion is never written down:

- **P1 (head, seg2 — already in source):** the Inkstone e-ink panel has a **14-week lead time**,
  single-source, non-compressible.
- **P2 (MID — TO PLANT, ~seg8, mid-doc-exclusive):** after panels land at Halvorsen in Tallinn,
  the **sequenced Founders'-Edition run adds a further 6 weeks** before units can ship — assembly
  plus standing up the serial-numbering/packaging line. (Distinctive figure; lives in one mid
  segment only. Ties to the existing seg13 thread that numbering "needs to be designed into the
  packaging run," but the *duration* is new and mid-only.)
- **P3 (tail, seg12–13 — anchor a specific date):** the Founders' Edition must be **in customers'
  hands by the week of November 24** (pre-holiday ship).

**Conclusion C (stated NOWHERE):** total lead = 14 + 6 = **20 weeks**; to hit a Nov-24 ship, the
Inkstone panel order must be placed by **~early July (≈ July 7)**. Neither "20 weeks" nor
"early July"/the date appears anywhere in the doc.

## Why it is anti-RAG / discriminating

- **Head+tail reader** has P1 (head) + P3 (tail) but **not P2** (the 6-week assembly/numbering
  buffer, mid-only). It can at best subtract 14 weeks from Nov 24 (≈ mid-August) and **cannot
  surface the buffer or the 20-week combined lead** — structurally short of the answer.
- **coupled_full** (full coverage + scaffold) sees all three regions → integrates P2 → ~20 weeks
  / early July.
- **verbatim_only** (Phase-B tiles, NO scaffold): has all three premises in verbatim tiles but no
  coarse global structure → the ablation isolating whether the scaffold helps *assemble* a
  multi-region computation.

## Scoring (gold to be authored)

- **Headline (the anti-RAG bit):** does the answer **integrate P2** — the mid-doc 6-week
  assembly/numbering buffer, i.e. a combined lead of ~20 weeks (or a deadline on/before mid-July)?
  This is what a head+tail reader cannot have. Robust to weak-floor arithmetic: we score
  *premise-integration*, not an exact date.
- **Secondary:** exact conclusion (≈ July 7 / "20 weeks"); premise co-presence P1∧P2∧P3.
- **Guards (runner MUST assert, model-free):**
  (a) each premise string fires on the rebuilt source;
  (b) **substance-reachability:** P2's distinctive figure and the conclusion (20-week / July)
      do **NOT** appear in the dense head+tail context — verified by matcher **and** manual read;
  (c) the conclusion appears **nowhere** in the full source (grep the rebuilt doc).

## Pre-registered prediction

Confirmed iff: `coupled_full` integrates P2 (≈20-week lead / early-July deadline), `dense`
misses P2, and `coupled_full ≥ verbatim_only`. Nulls reported: if `verbatim_only` matches
`coupled_full`, coverage alone assembles it (scaffold isn't the lever); if `coupled_full` also
misses P2, the untrained floor can't do cross-doc inference at this scale (real negative → E2′).

## Implementation constraints

- **Do NOT touch the shared fixture.** Copy `Context diffusion/test_conversation/segments_v2`
  to a **P6-local** dir, plant P2 (and anchor P3's date) there, rebuild with `assemble.py` to a
  **P6-local data_dir**; point P6 config at it. P4/P5 keep using the original conversation.jsonl.
- Plant minimally and in-voice (two competent peers); P2 is a few sentences in one mid turn.
- Re-verify all three guards after rebuild before any model run.
- Honesty note for RESULTS: this is a *dated, additive* modification (planted premises), not a
  silent edit; include the diff; P6 runs on the augmented variant, P4/P5 on the original.
