## Pass-Conditioned Reading / DiSCo: What the Experiments Actually Showed

**Verdict: not unfeasible. Possibly feasible with a trained model. That is the ceiling.**

Seven experiments (E0, P1–P7) on off-the-shelf instruction-tuned models — principally Qwen2.5-7B-Instruct, no fine-tuning — produced this result: the architecture did not fail in ways that close the gate, and showed enough to justify the next step. It did not validate the architecture.

> **About this work.** This is independent research by one person (GitHub: `dev-boz`), run on consumer hardware with no lab, funding, or formal research training. That constraint is real, and it bounded what follows — small sample sizes, local and hosted open models, and a single maintainer checking every number. The response to having few resources was to be *disciplined* rather than expansive: pre-register kill conditions before each run, publish the negatives, and never let the summary claim more than the data supports. Please read it in that spirit — a careful amateur's proof-of-mechanism and an honest request for help, not a finished result.

### The idea

A document too long for one context window is read in multiple passes. Each pass sees a differently compressed view — coarsest at pass 1, verbatim at pass K — and the model maintains a running structured state updated via edit operations (ADD, REPLACE, REMOVE). Early coarse passes are supposed to carry whole-document structure that a sequential single-window reader cannot acquire before it has already passed the section that establishes it. A `{k, K}` position signal conditions each pass so the model knows whether to scaffold, integrate, or surface verbatim detail. The specific claim the experiments tested: the full record→retain→compose chain on a fact split across non-adjacent passages whose linking formula does not survive any single compressed view.

### What individual components showed

Several pieces worked in isolation:

- The pass-position signal carries information not recoverable from view content alone (E0: 0.561 bucket accuracy vs 0.333 chance, n=360 test views, pre-registered gate call "signal-carrying"; K=8, GovReport corpus only).
- An off-the-shelf 7B can produce syntactically valid edit-ops at approximately 1.000 rate (P1–P3, n=1 document each). A per-pass behavioral rubric produces categorical op-type separation (pure ADD at scaffold passes, pure REPLACE later); a bare position field does not.
- In a cold proxy test, the coarse Phase-A pass preserved a full 24-entry lookup table that the verbatim-only arm missed, in 2 of 3 draws (P7 GATE 2, cold empty-state conditions). The warm go-signal run — designated the real arbiter per pre-registration — reversed this: the table was hosted in only a fraction of sampled warm draws and clobbered at pass 3 in every observed recording instance. Cold GATE 2 should not be read as a warm-conditions result; the warm arbiter is the operative finding.
- When the integration state was seeded with the correct structure, the closing model produced the correct answer in 4 of 4 draws (P7 GATE 3). This confirms the closing step is not the bottleneck; it isolates retention and salience as the open joints.

These are component-in-isolation results. They are not evidence the chain works.

### What the full chain did

**The full chain did not fire in the primary untrained 7B test (0 of 4 draws). Across model families, it was observed as isolated existence proofs — one confirmed draw per family across three families — not as a measured rate.**

Those three families (Qwen-72B, Meta-Llama-70B, Mistral-24B) each produced one hand-verified end-to-end chain completion. A separate, larger population shows the bottleneck: across the three strong-follower families whose verbatim control fails (Llama-70B, gpt-4o-mini, Nova-Lite), 22 seeds carried *both* numeric operands into final state, yet only 1 of those 22 — Llama-70B seed 9 — composed the correct answer. 21 of 22 failed to sum two figures the model already held. (Only Llama-70B seed 9 belongs to both groups; the Qwen-72B and Mistral-24B existence proofs sit outside the 22-seed population, which is why the recombination count is 1 of 22 and not 3.) The dominant open gap is recombination: the model holds the operands but not the relational binding that connects them, and loses the formula at close time.

Within those cross-family results, the coarse scaffold did not out-compose the verbatim-only arm: the tally across families was llama 1v0, gpt 0v0, nova 0v0, mistral 1v1, haiku 2v7 in favour of verbatim. On an untrained floor, the scaffold is not shown to add compose-rate advantage over simply reading verbatim tiles.

A small fraction (or none) was expected from an untrained floor. "Did not fail" is the honest characterization. It is not "works."

### The specific failure modes

The experiments did not produce a generic "floor is weak" verdict. Three distinct blocking joints were identified:

1. **Salience gap.** Under a neutral structural rubric, the floor omits structurally critical tables entirely — 0 of 6 draws recorded the target lookup table (both compressor versions, 3 draws each). Low-information names are recorded; high-information tables are dropped. Whether this represents a capability failure (to be corrected by training) or correct editorial behaviour (in which case training to record it would overfit to probe signals) is unresolved — this is the relevance-confound open question that must be settled before training data is constructed.
2. **Retention blocked by edit-op id-misaddressing.** Every time the table was recorded in Phase A, it was overwritten at pass 3 by a REPLACE operation targeting the wrong state slot (n=2 observations; replication required). This is a harness-fixable artifact, not a fundamental architecture failure.
3. **Recombination without relational binding.** Even with both operands confirmed in state, 21 of 22 seeds across families failed to compose the correct answer. Training must carry the linking formula, not just the atomic values.

### The negatives that bound the claim

- **P4 (recall, n=1 document):** the pre-registered kill condition failed. Coupled 32-pass schedule tied dense single-pass head+tail truncation at 5/8 facts each, at approximately 11x token cost and 9x wall-clock. No recall advantage over the cheapest baseline; no CIs computable.
- **P6 (salience-shaping):** the pre-registered interaction was uncomputable. The floor recorded test and control details in at most 1 of 4 draws, most draws zero. This is a floor-sensitivity limit, not a measured no-effect.
- **P2 (bare position field):** null. Validity 0.979 vs 0.983 across conditions. The earlier apparent effect (0.708 vs 0.375) was entirely a parser bug, not a real signal.
- **Prompt levers (gut-check):** both a recorder-side position injection and a closing-side permission-to-derive produced 0 correct compositions across 0 of 6 both-operands-held seeds tested. Prompt-injected awareness does not substitute for training.

### Why the methodology makes the modest claim credible

Kill conditions were pre-registered before runs. When P4's failed, it was recorded as a failure, not rationalized. A parser bug inflating apparent edit-op validity was diagnosed and the corrected rates replaced the inflated ones. A "v2 fixed the retention problem" claim was explicitly retracted when isolation tests showed the prompt, not the compressor, controlled the behavior. The forcing line — no prompt may instruct the model to do what only training should teach — is maintained throughout. The published negatives are not hedges. They are the mechanism by which the positive findings earn credibility.

### What the next step would measure, not guarantee

Training a small student model under a Pass-Conditioned Training objective (E2-prime) is warranted because the failure modes are specific and addressable — not because the floor was validated. A trained model has never been tested. Two open risks must be resolved before training data is constructed: (1) the relevance-confound question — if the model correctly declines to record an arbitrary lookup table under a neutral rubric, training it to do so would be overfitting to probe signals rather than learning structural importance; (2) a pre-committed criterion for what constitutes an architecture failure (as opposed to a trainable-further model failure) if E2-prime itself falls short on the P7 chain — this criterion does not yet exist and must be written down before E2-prime data generation begins.

*"This is a proposal, not a validated finding. Small-scale viability experiments are in progress."*

### What would help

This is a floor result that cannot take its own next step alone. The most useful help would be: a clean fine-tune (E2-prime) to actually test the trained-model hypothesis; a second pair of eyes on the data, the statistics, and the prior-art map; or input from anyone who knows the diffusion-LM / long-context literature well enough to confirm or kill the novelty claim. If the method is wrong, I would rather hear it from you now than discover it later. Open to collaboration, correction, and hard questions — `dev-boz` on GitHub.