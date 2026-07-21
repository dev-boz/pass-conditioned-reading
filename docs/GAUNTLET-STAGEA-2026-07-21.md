# Gauntlet prompt — Stage-A chain-gate result + roadmap review

**Usage:** copy everything below the `---` line into each reviewer model/harness verbatim. Reviewers get no repo access and no tools; the prompt is self-contained. Collect the numbered answers for arbitration (the gauntlet-arbitration.md pattern: verify every checkable claim before accepting it).

---

You are one of 10+ independent AI reviewers evaluating a small ML research project at a decision point. Be adversarial and concrete. Do not flatter. Do not roleplay running experiments. If you are unsure, say "unsure" — a wrong confident answer is worse than no answer. If anything in this document looks internally inconsistent or factually wrong, say exactly what and why.

## What we are trying to do

An inference-time architecture for reading documents much larger than a model's usable context. The model reads the source in K scheduled passes: early passes see heavily compressed views (global structure), later passes see verbatim tiles (exact details). Across passes it maintains a bounded **integration state** — numbered text entries `S1: ...`, `S2: ...` — which it edits each pass by emitting operations (`ADD`, `REPLACE`, `REMOVE`, content-addressed with verbatim quotes so misaddressed edits are refused). After the last pass, questions are answered **from the final state alone**; the source is gone. The bet: a small-context model plus this schedule can approach long-context performance on long inputs, and models can be **trained** to run this protocol well ("pass-conditioned training": the model is told its position k of K). The eventual goal is preserving the nuance of long sessions/documents, not trivia recall.

## The test we ran (Stage A chain gate, pre-registered)

- **Fixture:** a synthetic 64,671-token codebase. Planted in one module: `REGION_SURCHARGE_CENTS = {..., 23: 988, ...}` (24-entry integer table). Planted in a different module: `RECONCILIATION_ADDER_CENTS = 1365` and `compute_line_surcharge(region) = table[region] + adder`. The table and the call site never co-occur in any single view (verified mechanically). Decoys are planted too, including an arbitrary 12-entry `CARRIER_FUEL_BP` table. One question, asked only at the end, answered from final state: what does `compute_line_surcharge(23)` return? Truth: **2353**. The chain: **RECORD** (write `23:988` and `1365` into state during reading) → **RETAIN** (still there at close) → **COMPOSE** (988+1365 at close).
- **Anti-cheating rules:** no prompt anywhere may name the probe, the tables, values, or "record tables" (audited "forcing boundary"). Framing is need-class only: "operational questions about this codebase's pricing, order flow, configuration and cross-module behavior will be answered from your state alone." A backfill gate (GATE-1) confirms the answer is not guessable from the call-site fragment alone: PASS.
- **Training:** teacher = Claude Haiku 4.5 executing the same protocol over 277 unrelated documents → ~5,730 pass-level training rows (leakage-scanned against the fixture; zero hits). Student = Qwen2.5-1.5B-Instruct, LoRA r16/α32, trained on a rented A5000. Run 1 failed the pre-registered training-health gate because a truncation bug ate most code-row completions (caught, documented, rerun). Run 2 passed: held-out edit-op validity 0.970 (bar ≥0.95), op-type agreement with teacher 0.761 (bar ≥0.75).
- **Battery:** 10 sampled draws (seeds 1–10, temp 0.7) per arm + a temp-0 anchor reported separately. Arms: trained student vs the same base model untrained (floor). K=31 passes (6 compressed + 25 verbatim), strict content-addressed harness, 24-op cap per pass. Local GPU (GTX 1080 Ti), f16, 24K context.
- **Pre-committed verdict rule:** student ≥5/10 end-to-end = chain demonstrated; 2–4/10 = exactly one retry (more data or 1.5B→3B); ≤1/10 = "architecture gate" — stop spending training runs on this instantiation.

## Results

**End-to-end: student 0/10, floor 0/10 → architecture gate.** Zero mechanical candidate successes; hand review confirms no draw on either arm ends holding a linked `23→988` pair that a lenient scorer could count.

Component rates (student vs floor, over the 10 sampled draws):

| component | student | floor |
|---|---|---|
| edit ops applied per pass | 7.0 | 2.4 |
| final state size | ~7,700 tok (~116 entries) | ~725 tok |
| edit-op validity | 0.94–1.00 | 0.03–1.00 (bimodal) |
| surcharge table *named* at some pass | 7/10 | 2/10 |
| full mapping `23:988` recorded at some pass | 3/10 | 0/10 |
| both operands in state at close | 2/10 | 0/10 |
| operands lost after recording | 0/10 | 0/10 |
| close returns 2353 | 0/10 | 0/10 |

Failure anatomy (from archived raw outputs):

1. **RECORD is all-or-nothing per table.** Every table is either transcribed in full (24/24 pairs) or not at all (0/24) — never the one relevant row. When the student compresses instead, it writes range summaries with **fabricated statistics** ("70 entries, keys 10-98, values 161-988 cents" for the 24-entry table; a control-table summary borrows the other table's maximum).
2. **RETAIN is clean.** The content-addressed guard blocked ~150 suspicious writes across the student arm; nothing recorded was ever lost. The clobber failure mode that motivated the guard did not recur.
3. **CLOSE fails two dissociable ways** (probes below): the 2 student draws that reached close holding both operands still failed — one answered **86** by reasoning over the decoy fuel table ("the closest matching bp value to 23 within the range 17–86 is 86" — a confabulated rule), one reasoned `compute_line_surcharge(23)` returns **23** (argument/return confusion).
4. Format compliance is itself weak: 6/10 student closings never emitted the required `ANSWER: <integer>` line.

Diagnostics (non-verdict; some use oracle knowledge, declared as such):

- **GATE-3 seeded compose:** hand the model a clean 8-entry best-case state containing the full table, adder, and function definition → student **1/10**, floor **0/10**. Adding explicit permission to derive arithmetically changes nothing.
- **Distillation probe (oracle):** filter seed 2's own 155-entry final state to just the 2 entries holding the operands → it composes **2353 correctly**. It held the answer and could not find/use it at full length.
- **Padded probe (oracle, length-preserving):** keep those 2 operand entries at their original positions, replace all other entries with digit-free neutral filler (same length) → still 0/10 compose, **but wrong answers migrate onto the correct table** (86→988; another draw picks the right table wrong row; single-operand states return that operand). So: **distractor content misdirects retrieval; length itself kills two-operand composition at 1.5B.** The full chain fires only in a tiny state.
- **Prompt-level fixes do nothing:** a "quote the relevant entries before answering" instruction → 0/10. Moving the question before the state → 0/10 (the close already used data-first/question-last order).

## Weaknesses we already know (scrutinize anyway)

1. **Scale confound:** we cannot separate "architecture wrong" from "1.5B too small." Clean-state compose is ~1/10 at 1.5B.
2. **Teacher confound:** the student distills a schedule-executing teacher; results say what is learnable from that teacher, not what the architecture could do in principle.
3. **Concession test:** this chain gate is a concrete killable proxy, not the stated goal (nuance preservation). A goal-aligned test (M-NL) is drafted but unrun.
4. **Instrument fragility:** scoring was corrected 4× mid-run against archived text. Worst catch: the runner matched the mapping only as `23: 988` while the student wrote `23→988` — uncorrected, a measurement bug would have manufactured this exact negative verdict.
5. **Methodology provenance:** designed by AI assistants with an ML-novice maintainer double-checking. Assume errors exist; find them.

## Roadmap (lever board — reprioritize, kill, add)

Open levers: **(3) recording-pass prompt order** — current harness puts instructions before data; the data→instructions order (per a Google finding that data-before-prompt substantially helps) is untested; testable for $0 on the untrained floor, then a retrain by **re-rendering the existing 5,730 teacher rows in the new order (zero new teacher spend)**. **(4) selective reading** — early passes rate slice importance; only important verbatim slices are read → smaller, relevant state. **(5) guided reading** — early passes leave notes for later passes ("this detail matters"). **(8) composition-focused training mix.** **(9) scale 1.5B→3B.** **(10) native architecture** — replace the text state + edit ops with a latent slot-bank memory updated inside the model, pass-conditioning injected via AdaLN; dissolves the edit-sequence entirely (biggest build; design doc exists). **(12) M-NL** — test the actual goal (nuance→decision) with the existing student/floor pair, inference-only. Parked as efficiency-only (not implicated in any observed failure): confidence early-stopping, concurrent prefill, pass skipping, slice-overlap control. Closed by probe (negative): question-first close; retrieve-first instruction.

Constraints: inference on one GTX 1080 Ti (11GB; f16 1.5B fits, 3B probably, 7B only quantized); training = rented A5000-class, roughly one run at a time; teacher API budget small; maintainer is time-rich and expertise-limited; discipline = any modified instantiation gets a fresh pre-registered pass/fail bar before its training run (no post-hoc threshold moving; no same-instantiation retry after 0/10).

## Questions — answer ALL, numbered, with confidence (high/med/low) per answer

1. What is the most likely **fatal flaw** in the test design or training setup that we have NOT named above?
2. Given the retrieval-vs-length dissociation, rank your **top 3 levers** from the board (or new ones) with one-sentence reasoning each.
3. The all-or-nothing table recording: is it most likely a **data** problem (teacher demonstrations), an **objective** problem, an **op-grammar** problem, or an **architecture** problem? Name the cheapest test that discriminates.
4. You get **one training run**. Spend it on: (a) 3B same data, (b) 1.5B re-ordered/re-mixed data, (c) 1.5B + selective/guided-reading harness change, (d) no training — build M-NL or the native architecture instead. Pick one, justify.
5. Is ~1/10 clean-state compose at 1.5B evidence of a **hard capability floor**, or plausibly trainable? Cite what you know that bears on small-model multi-hop arithmetic-over-context.
6. What **prior art** are we reinventing or contradicting (memory-augmented reading, agentic long-context, map-reduce QA, RAG-over-own-notes, MemGPT-style state, recurrent memory transformers)? Name specific work and what it changes about what's worth testing.
7. What is the single cheapest **$0 inference-only probe** (frozen weights, 11GB GPU) you would run next that is not already listed?
8. **Hallucination check:** anything in our numbers look internally inconsistent or too convenient? Say what and why.
9. What is the strongest **honest claim** this project could make today, and what one thing is missing for that claim to matter to anyone?
10. **Steelman the kill:** argue this instantiation was never going to work and the gate was predictable a priori. Then say whether you buy your own steelman, and why.

Format: numbered answers 1–10, ≤1200 words total, no preamble, no summary of the document back at us.
