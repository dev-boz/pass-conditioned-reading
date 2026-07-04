## Pass-Conditioned Reading / DiSCo: what the experiments actually showed

The verdict, up front: not unfeasible. Possibly feasible with a trained model. That's the ceiling of what I can claim.

Seven experiments (E0, P1 to P7) on off-the-shelf instruction-tuned models, mostly Qwen2.5-7B-Instruct with no fine-tuning, produced this result: the architecture didn't fail in ways that would close the gate, and it showed enough to justify the next step. It did not validate the architecture.

A note on who's behind this. It's independent research by one person (me, dev-boz on GitHub), run on consumer hardware with no lab, no funding and no formal research training. That constraint is real and it shaped everything here - small sample sizes, local and hosted open models, and one person checking every number. My answer to having few resources was to be disciplined instead of expansive: pre-register the kill conditions before each run, publish the negatives, and never let the summary claim more than the data supports. Please read it in that spirit. This is a careful amateur's proof-of-mechanism and an honest request for help, not a finished result.

### The idea

A document too long for one context window gets read in multiple passes. Each pass sees a differently compressed view - coarsest at pass 1, verbatim at pass K - and the model keeps a running structured state that it updates with edit operations (ADD, REPLACE, REMOVE). The early coarse passes are supposed to carry whole-document structure that a normal sequential reader can't have yet, because it hasn't reached the section that establishes it. A {k, K} position signal tells the model where it is in the process, so it knows whether to scaffold, integrate or surface verbatim detail.

The specific claim the experiments tested: the full record→retain→compose chain, on a fact split across non-adjacent passages where the linking formula doesn't survive any single compressed view.

### What worked in isolation

Several pieces worked on their own.

The pass-position signal carries information you can't recover from the view content alone. E0 measured 0.561 bucket accuracy against 0.333 chance (n=360 test views, K=8, GovReport corpus only), and the pre-registered gate call was "signal-carrying".

An off-the-shelf 7B can produce syntactically valid edit-ops at close to a 1.0 rate (P1 to P3, n=1 document each). A per-pass behavioural rubric produces clean op-type separation - pure ADD at scaffold passes, pure REPLACE later. A bare position field does nothing.

In a cold proxy test, the coarse Phase-A pass preserved a full 24-entry lookup table that the verbatim-only arm missed, in 2 of 3 draws (P7 GATE 2, cold empty-state conditions). But the warm go-signal run, which the pre-registration named as the real arbiter, reversed this: the table was only hosted in a fraction of sampled warm draws, and every time it did get recorded it was clobbered at pass 3. Don't read the cold result as a warm-conditions result. The warm arbiter is the operative finding.

When the integration state was seeded with the correct structure, the closing model got the right answer in 4 of 4 draws (P7 GATE 3). So the closing step isn't the bottleneck. Retention and salience are the open joints.

These are components in isolation. They're not evidence the chain works.

### What the full chain did

The full chain did not fire in the primary untrained 7B test, 0 of 4 draws. Across model families it showed up as isolated existence proofs - one confirmed hand-verified draw each from Qwen-72B, Meta-Llama-70B and Mistral-24B - not as a measured rate.

A separate, larger population shows where the bottleneck is. Across the three strong-follower families whose verbatim control fails (Llama-70B, gpt-4o-mini, Nova-Lite), 22 seeds carried both numeric operands into the final state. Only 1 of those 22, Llama-70B seed 9, composed the correct answer. The other 21 failed to sum two figures the model was already holding. (Seed 9 is the only overlap between the two groups - the Qwen-72B and Mistral-24B existence proofs sit outside the 22-seed population, which is why the count is 1 of 22 and not 3.) So the dominant open gap is recombination: the model holds the operands but loses the relational binding that connects them, and drops the formula at close time.

Within those cross-family runs, the coarse scaffold also didn't out-compose the verbatim-only arm. The tally across families was llama 1v0, gpt 0v0, nova 0v0, mistral 1v1, haiku 2v7 in favour of verbatim. On an untrained floor, the scaffold isn't shown to add any compose-rate advantage over just reading verbatim tiles.

A small fraction (or none) was what you'd expect from an untrained floor. "Did not fail" is the honest read. It's not "works".

### The specific failure modes

The experiments didn't produce a generic "the floor is weak" verdict. Three distinct joints are blocking the chain.

The first is a salience gap. Under a neutral structural rubric the floor skips structurally critical tables entirely - 0 of 6 draws recorded the target lookup table (both compressor versions, 3 draws each). It records low-information names and drops high-information tables. Whether that's a capability failure that training fixes, or correct editorial behaviour (in which case training the model to record it would just be overfitting to my probe signals), is unresolved. That's the relevance-confound question, and it has to be settled before any training data gets built.

The second is retention blocked by edit-op misaddressing. Every time the table did get recorded in Phase A, a REPLACE aimed at the wrong state slot overwrote it at pass 3 (n=2 observations, replication required). That one is a harness-fixable artifact, not a fundamental architecture failure.

The third is recombination without relational binding. Even with both operands confirmed in state, 21 of 22 seeds across families failed to compose the answer. Training has to carry the linking formula, not just the atomic values.

### The negatives that bound the claim

P4 (recall, n=1 document): the pre-registered kill condition failed. The coupled 32-pass schedule tied a dense single-pass head+tail truncation at 5/8 facts each, at roughly 11x the tokens and 9x the wall-clock. No recall advantage over the cheapest baseline, and no confidence intervals computable at n=1.

P6 (salience-shaping): the pre-registered interaction was uncomputable. The floor recorded test and control details in at most 1 of 4 draws, most draws zero. That's a floor-sensitivity limit, not a measured no-effect.

P2 (bare position field): null. Validity 0.979 vs 0.983 across conditions. The earlier apparent effect (0.708 vs 0.375) was entirely a parser bug, not a real signal.

And a gut-check on prompt levers: a recorder-side position injection and a closing-side permission-to-derive both produced 0 correct compositions across the 6 seeds tested that held both operands. Prompt-injected awareness doesn't substitute for training.

### Why I think the modest claim holds up

The kill conditions were pre-registered before the runs. When P4's fired, it went on the record as a failure, not a rationalisation. A parser bug that was inflating apparent edit-op validity got diagnosed, and the corrected rates replaced the inflated ones. I explicitly retracted a "v2 fixed the retention problem" claim when isolation tests showed the prompt, not the compressor, was controlling the behaviour. And one rule held the whole way through: no prompt may instruct the model to do what only training should teach. The published negatives aren't hedging. They're what makes the positive findings worth anything.

### What the next step would measure, not guarantee

Training a small student model under a pass-conditioned objective (E2-prime) is warranted because the failure modes are specific and addressable, not because the floor was validated. A trained model has never been tested.

Two open risks have to be resolved before any training data is constructed. One is the relevance-confound question above - if the model is correctly declining to record an arbitrary lookup table under a neutral rubric, then training it to record one is overfitting to probe signals rather than learning structural importance. The other is a pre-committed line for what counts as an architecture failure, as opposed to a model that just needs more training, if E2-prime itself falls short on the P7 chain. That criterion doesn't exist yet and it has to be written down before E2-prime data generation begins.

This is a proposal, not a validated finding. Small-scale viability experiments are in progress.

### What would help

This is a floor result that can't take its own next step alone. The most useful things right now would be a clean fine-tune (E2-prime) to actually test the trained-model hypothesis, a second pair of eyes on the data, the statistics and the prior-art map, or input from anyone who knows the diffusion-LM / long-context literature well enough to confirm or kill the novelty claim. If the method is wrong I'd rather hear it from you now than discover it later. Open to collaboration, correction and hard questions - dev-boz on GitHub.

