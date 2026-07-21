# Stage-A′ Exploration Ledger

**Status:** exploratory, post-gate. Nothing here is a verdict instrument.
**Date opened:** 2026-07-21, immediately after the Stage-A architecture gate (see STAGEA-CHAIN-GATE-RESULTS.md).

## The operating mode (maintainer, 2026-07-21)

This project is explicitly a **process, not a one-shot**: try levers, measure, adapt. Much of the methodology is AI-drafted and maintainer-checked; either can be wrong, so instruments are held with humility (the battery's scorer was corrected 4× mid-run — see the results doc). The rules that keep exploration scientific:

1. **Probes are cheap, labelled, non-verdict.** Oracle knowledge is allowed in a probe if declared. No probe number is ever pooled with a gate.
2. **A lever graduates only by fresh pre-registration.** A modified instantiation gets its own dated pre-reg with frozen bars *before* its training run. This is the criterion's own ≤1/10 next-move (architecture revision), iterated.
3. **Negative probes are recorded, not discarded.** (Two below already are.)
4. **The wall test (the stop rule, operationalized):** each instantiation's pre-reg names the **component rates** it expects to beat from the previous instantiation (not just end-to-end). The project fails when successive instantiations stop producing component improvement — measurable, not vibes. Stage-A run 2's rates (results doc §5 table) are the current baseline to beat.
5. One lever per instantiation where affordable; declare the confound where not.

## What the Stage-A evidence says the levers must attack

Two blocked joints (RETAIN is clean), plus one dissociation from the padded probe:

- **RECORD:** whole-entry, all-or-nothing (24/24 or 0/24, never the one relevant row); lossy Tier-1 summaries that *fabricate* statistics.
- **CLOSE/retrieval — content-sensitive:** distractor entries capture retrieval (seed 2 answered 86 off the decoy table; with distractors replaced by neutral filler it lands on the right table).
- **CLOSE/compose — length-sensitive:** even with neutral filler at full ~7.5K length, the 1.5B fetches ONE operand but never binds two and adds; the full chain fired only in a 2-line state. Small-model long-context degradation is real here (maintainer's hypothesis, confirmed 2026-07-21).
- Not promptable: neither a retrieve-first instruction nor question-first ordering at close moved anything.

## Lever board

| # | lever | joint it attacks | evidence so far | cheapest next probe | cost | status |
|---|---|---|---|---|---|---|
| 1 | Close prompt order (question-first) | close/retrieval | **probed 2026-07-21: 0/10, no help** (close was already data-first, the recommended order; flipping slightly hurt) | — | — | **CLOSED, negative** |
| 2 | Length-preserving distractor removal | close/retrieval vs compose | **probed 2026-07-21: dissociation** (retrieval redirects to operand lines; compose still 0/10 at full length; 2-line state composes) | — | — | **CLOSED as diagnostic — feeds levers 4/5/9** |
| 3 | **Recording-pass prompt order (data→instructions)** | RECORD | untested; Google finding (data>prompt substantially better) — current harness is instructions-first, the anti-pattern; "order may flip by stage" testable per-pass | inference-only on the untrained floor ($0, no train/eval mismatch); if signal → **reorder-and-rerender retrain from the archived 5,730 teacher rows (zero new teacher spend)** | $0 probe / 1 A5000 run | **OPEN — cheapest high-value** |
| 4 | **Selective reading** (early passes rate slices; only important verbatim slices read) | RECORD + state size (hits the length joint too: smaller, relevant state at close) | untested; directly targets all-or-nothing + 7.5K bloat | prototype inference-only on frozen weights (harness change only) | $0 | **OPEN — high value** |
| 5 | **Guided reading** (early passes leave notes for later passes) | RECORD relevance | untested; would let the verbatim pass record the *row*, not a fabricated range summary; forcing-boundary care: notes must be model-generated | prototype inference-only on frozen weights | $0 | **OPEN — high value** |
| 6 | Reverse reading (later pass requests re-read) | compose/binding | untested | defer until 4/5 probed (overlapping mechanism) | — | parked |
| 7 | Slice overlap control | RECORD completeness | untested; marginal against all-or-nothing | — | — | parked |
| 8 | Composition-focused training (closing-heavy data mix) | compose | GATE-3: clean-state compose 1/10 at 1.5B → training target is real but scale-capped | only inside a modified instantiation w/ fresh pre-reg; pair with 9 or 10 | retrain | OPEN |
| 9 | **Scale step 1.5B→3B** | compose ceiling (the length-sensitive joint) | GATE-3 + padded probe both point at a 1.5B compose ceiling | own pre-reg as a separable arm; 3B f16 should serve on the 1080 Ti (verify VRAM before committing) | 1 A5000 run | **OPEN** |
| 10 | Native architecture (latent slot bank, AdaLN pass-conditioning) | both joints at once | the criterion's pre-named ≤1/10 option; padded/distilled probes are direct evidence for addressable state | design doc exists (DISCO-NATIVE-ARCHITECTURE.md) | large build | OPEN — destination if text-state levers plateau |
| 11 | Confidence early-stop / concurrent prefill / pass skipping | efficiency only | not implicated in any blocked joint | — | — | parked (honest: speed levers, not fix levers) |
| 12 | M-NL nuance experiment (ask a different question) | test validity | chain gate is a declared concession test; "not asking the right question" is live | NUANCE-EXPERIMENT-SHAPE.md, runs trained-vs-untrained on the existing student/floor pair | inference-only | OPEN |

## Instrument debts (fix before ANY next battery)

- Port the paraphrase-robust pair matcher from `analyze_chain_gate.py` into the runner's live flags (colon-only matcher was kept mid-battery only for manifest-hash consistency).
- Archive `usage.completion_tokens` per call (makes decode-cap truncation decidable, not heuristic).
- Pre-commit a secondary "final number in prose" metric: 6/10 student draws produced no `ANSWER:` line; format compliance is itself a small-model failure and should be measured, not conflated with reasoning failure.

## Immediately runnable for $0 (say the word)

- **Lever 3 probe:** data-first recording prompts on the untrained floor, few seeds, component rates vs the floor baseline.
- **Lever 4/5 prototypes:** selective/guided reading harness variants on frozen student weights.
