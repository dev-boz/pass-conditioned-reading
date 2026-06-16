# P6 — Global (whole-document) synthesis · PRE-REGISTRATION

**Status:** pre-registered; to be built and run in a fresh session (see `docs/HANDOFF-P6.md`).
Reuses the P4 fixture (Sandpiper, 390 turns / 16 segments), schedule, untrained Qwen-7B
floor, and the P4 normalized component matcher. Author the gold chain (`gold_chain.json`)
and this file are committed **before** any arm is scored.

## Why this test (the differentiator)

Fact **recall** is table stakes — RAG, long-context, even a head+tail read recover planted
facts (P4/P5). The PCA claim that must earn its keep is that the **coarse global passes
build a scaffold that yields whole-document *understanding*** — synthesis distributed
across the document that a local retriever cannot shortcut. P6 is the **first probe in a
battery** of such tests (more to come — aggregation, consistency, evolution, distributed
inference); the goal now is **viable**, not optimal. One clean win is a signal, not proof.

## The task (explicit — P5's lesson: never vague)

> "Why did the launch end up going direct-to-consumer instead of through a retail
> partnership? Trace the sequence of constraints and events that led to that decision."

The answer is a **causal chain distributed across the document** whose hinge is **mid-document**:
8,000-unit cap (seg2, head) → pursue Meridian retail (seg6) → **Meridian demands full-fleet /
holiday-density volume far above the cap → retail collapses (seg9, MID)** → no partner +
unchanged cap → pivot to direct (seg10) → waitlist + Founders' Edition (seg13, tail). See
`gold_chain.json` for the link matchers and the verified mid-doc-exclusive hinge.

**Why this defeats a local reader by construction:** a head+tail / RAG-on-endpoints reader
has the cap (head) and the final direct decision (tail) but **cannot have L3** — the reason
retail failed ("full fleet" / "holiday density") lives in seg9 only (verified). So a correct
*why* requires whole-document coverage + synthesis, not retrieval of the endpoints.

## Arms

| arm | description | role |
|---|---|---|
| **dense** | single-pass head+tail (~14K of 73K), P4's `run_dense` | predicted to MISS L3 (mid-doc) |
| **coupled_full** | Phase-A coarse scaffold (R chunks) + Phase-B verbatim tiles (P4's `run_coupled`) | the claim |
| **verbatim_only** | Phase-B verbatim tiles only, **no Phase-A scaffold** (`--no-scaffold`) | the KEY ablation — isolates whether the coarse global pass helps *assemble* the distributed chain |

All coupled/verbatim arms are query-conditioned on the task above (P5: explicit ask). After
state-building, each coupled/verbatim arm makes one **closing call** ("using your integration
state, answer: <question>") so all three arms are scored on a comparable **answer text**.

## Scoring (gold_chain.json)

- **Headline metric:** **L3 (mid-doc hinge) present in the answer** — "full fleet" / "holiday
  density" (or a 30–40k figure co-occurring with Meridian/retail). This is the bit a local
  reader cannot have.
- **Chain completeness:** count of L1–L5 present (co-presence).
- **Ordering** (coupled arms): L1→L3→L4→L5 in state-entry order (extend P4 Tier-3; reported, not headline).
- Mechanical component match is the skeleton; an LLM-judge (Kiro Haiku) may give a secondary
  read on whether the causal "because" is actually asserted — caveated, not the verdict.
- **Matcher guards (runner MUST assert):** (a) each link matcher fires on the source; (b) the
  L3 discriminating terms do **not** fire on the dense head+tail context (else the test isn't discriminating).

## Pre-registered predictions

- **Differentiator confirmed iff:** coupled_full produces the full chain **including L3**, dense
  **misses L3**, AND coupled_full ≥ verbatim_only on L3 / chain-completeness.
- **Null / negative (reported, not buried):** if verbatim_only matches coupled_full on L3, the
  coarse scaffold isn't what carries whole-doc synthesis (coverage alone suffices) — still
  informative for the architecture. If coupled_full *also* misses L3, the untrained floor can't
  synthesize across the document at this scale — a real negative to carry into E2′.
- **Dense surprise:** if dense somehow gets L3, re-audit matcher specificity (the guard should prevent this).

## Scope / honesty

Untrained Qwen-7B floor, n=1 document, temp 0, single draw per arm. A **mechanism/architecture
probe**, not an effect-size estimate and **not a viability verdict** (that rides on the trained
student E2′). But unlike recall, a clean coupled-beats-dense-and-verbatim-only result here is the
**first qualitative evidence that the architecture understands the whole document** — which is the
whole point of the coarse-to-fine schedule. This is probe #1 of a planned battery; one document
is not "whole-document understanding," it is one data point toward viability.
