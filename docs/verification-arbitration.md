# Verification Sweep Arbitration — Final Pre-Publication Pass

**Inputs:** five independent verification reports (01–03, DR-1, DR-2) against `verify-prompt-deep-research.md`, plus one ground-truth full-text fetch performed during arbitration (ST-MoE, arXiv 2202.08906, complete PDF).
**Date:** 2026-06-12.

## 1. Headline: the ST-MoE autopsy

The five reports returned **three mutually exclusive "verbatim" quotes** from the same paper about positional features in the router: two agents quoted it saying they *improve* performance (citing "Section 4.3: Router Design"), two quoted it saying they *did not* improve performance (citing "Section 4: Expert Routing"), and DR-2 claimed the experiment doesn't exist in Zoph et al. at all — an acronym collision with a 2026 AAAI "Spatiotemporal MoE" paper.

**Ground truth, from the full paper text:** neither cited section exists (Section 4 is "Fine-Tuning Performance of Sparse Models"), and no experiment adds sequence-positional features to the router. The only adjacent material is **Appendix J, Negative Results**: (a) *"Adding explicit expert positional information… through adding an embedding corresponding to what expert each token was sent… did not improve performance"* — expert-identity embeddings added to expert-layer **outputs**, not position-of-token features into the router; and (b) routed/dropped-history information fed to the router — *"made no difference."* Appendix C additionally found word-embedding router inputs eventually neutral.

**Verdicts:** the "helps" camp fabricated its quote outright (and reviewer 14's original gauntlet attestation — which my own arbitration propagated as "mildly pro-D1" — was equally fabricated; that propagation is on me, and it's the reason ✔R was never the same status as ✔A). The "doesn't help" camp fabricated its quote too but landed near the truth's direction by luck. DR-2's directional claim is the most accurate and its collision mechanism is the most plausible source of the phantom finding, though the fuller truth includes Appendix J's adjacent negatives.

**Corrected row (now in v0.3):** ST-MoE = router z-loss stability paper; encoder experts specialize (punctuation, verbs, proper nouns), decoder experts don't, multilingual experts don't specialize by language; Appendix J negatives as above; **no in-domain evidence on positional router features in either direction.** Consequence for D1: the v0.2 "OpenMoE/ST-MoE tension" framing is dead — replaced by something stronger: OpenMoE and ST-MoE both show language-MoE routing keys on token identity/content, and the position-features question is simply **unmeasured in language**. D1's view-swap probe targets a genuinely empty cell.

**The meta-lesson, now demonstrated twice at escalating severity:** Fresco showed real-paper-wrong-scope; ST-MoE shows that even verification-mode agents under URL mandates fabricate quotes *in both directions* and invent section names to anchor them. Quote-level claims only count when checked against the document itself. For anything load-bearing, the ledger now distinguishes ✔A (arbitration-verified against primary text) from ✔R (agent-attested with URL).

## 2. Other conflicts, adjudicated

**Residual Context Diffusion (4–1).** DR-1 escalated to NEW-THREAT by reading "residual update to the input context" as input-source staging. The shared abstract quote settles it the other way: *"converts these **discarded token representations** into contextual residuals… for the next denoising step"* — the residuals originate from the model's own intermediate states (remasked tokens during denoising, per DR-2's mechanistic detail) and modify the generation trajectory, not an external immutable source. The "input" of a denoising step is the evolving canvas: output-side in our taxonomy. **ADJACENT.** Row added (Hu et al., arXiv 2601.22954, ICML 2026 per DR-2's source list).

**DICE (4–1).** DR-1 verified a different paper entirely — DICE the image-edit coherence evaluator (2407.14274). The relevant DICE is the staleness-centric parallel diffusion-MoE inference paper (Luo et al., ICCV 2025, arXiv 2411.16786), as three agents and the v0.2 row's MoE context make unambiguous. DR-1's row discarded.

**LoopMoE (corrected, magnitude held open).** Four of five confirm v0.2's "no emergent-vs-conditioned ablation" was wrong: Loop Base (trajectory-only) vs +IterAdaLN **is** the ablation, and it exists. But the agents' magnitude quotes conflict — "a modest improvement in the commonsense dataset" (two agents, citing Table 3) versus "systematic drop… essential" (one agent) versus "significantly degrades" (DR-2). The corrected row is magnitude-neutral and flagged: quote numbers only after a direct read of Table 3. Full title: "LoopMoE: Unifying Iterative Computation with Mixture-of-Experts for Language Modeling" (Chen et al., arXiv 2606.04438). **Bonus for M2's framing:** in a loop, the token input is near-identical across iterations, so iteration index is *not inferable from the input* — LoopMoE sits at the zero-inferability end of the regime axis, where explicit conditioning helping is exactly what the regime story predicts. SCUD now anchors the same axis from the other side: masking diffusion succeeds *because* the schedule is inferable; structured diffusion needs the schedule injected. Two independent literatures now bracket E0's question.

**Remix-DiT authorship (1 correct, 2 rubber-stamped).** Agent 02's correction stands: Fang et al. (Gongfan Fang, Xinyin Ma, Xinchao Wang), not "Tan et al." — consistent with the NUS Torch-Pruning group. arXiv 2412.05628, NeurIPS 2024.

**ProMoE (5/5).** One paper, not two: "Routing Matters in MoE: Scaling Diffusion Transformers with Explicit Routing Guidance" (arXiv 2510.24711, ICLR 2026); ProMoE is the framework name. Rows merged.

**NaviEdit (weighting split).** Real (arXiv 2605.21190, 2026): image editing, decouples edit progress from scale traversal, and finds **decoupling wins** in that setting. Not a threat to M1 (output-canvas coordinates, no external source, no language) — but it's the right kind of caution: schedule-axis coupling is a live question whose answer is *setting-dependent*, which is precisely why M1 ships as a pre-registered interaction measurement with kill criteria rather than an assumed truth. Added as adjacent-conceptual.

## 3. Name collision flag (new, from DR-2's sweep)

**"Context Diffusion" already names a 2023 paper** — Najdenkoska et al., arXiv 2312.03584, "Context Diffusion: In-Context Aware Image Generation." Different domain, different mechanism, but identical headline term. Not fatal: keep **DiSCo** as the headline operator name and treat "Context Diffusion" as the descriptive layer, with a one-line disambiguation footnote in the README. Worth deciding before publishing, not after.

## 4. Consensus ledger (all clear)

Confirmed-as-characterized across all reporting agents, with URLs and quotes: **COMI** (Tang et al., ICLR 2026, 2602.01719 — input-side, single-pass decode), **SCUD** (Amin/Gruver/Wilson, NeurIPS 2025, 2506.08316 — "Why Masking Diffusion Works…", schedule-as-input, output-side), **DVLT/DéjàView** (2605.30215 — looped 3D reconstruction, step-conditioned, K as compute knob), **PonderLM** (Zeng et al., ICLR 2026, 2505.20674 — no step signal, no input staging; title corrected), **FraiLT** (2401.11626 — learnable iteration encodings, no explicit-vs-trajectory ablation), **Mode-Conditioning** (Wu/Goyal/Raghunathan, 2512.01127 — modes, not schedule position), **OpenMoE** (Xue et al., 2402.01739 — token-ID-dominated routing), **EC-DiT** (Xu et al., ICLR 2025, 2410.02098 — both observes and designs allocation shift), **Ganjdanesh et al.** (ECCV 2024, 2409.15557), **COCONUT** (COLM 2025, 2412.06769), **s1** (2501.19393, arXiv-only), **DiffusionGemma Sudoku early-stopping** (Google dev-blog quote pinned verbatim with URL).

## 5. Fresh-eyes sweeps on M1: five independent nulls

Roughly fifty logged queries across the five reports (arXiv cs.CL/cs.LG, OpenReview, HF daily papers, Semantic Scholar forward chains from RLM / Matryoshka / ReadTwice / SoT) returned **no paper running a coupled-vs-decoupled input/output staging ablation on a language task**. Benign near-hits, all catalogued: NaviEdit and ChainCoder (ICML 2023, outline→detail code generation, output-side — row added), Chain of Draft, Focus-dLLM, Chronicle, RaPD, DiffusionAnything, and the 2023 Context Diffusion image paper (the name-collision flag above).

## 6. Go/no-go

**GO — 5/5 agents, sustained after arbitration.** No blocker to publishing M1 as the primary claim. Three corrections were applied to our own documents in the process (ST-MoE row rewritten from ground truth, LoopMoE ablation acknowledged, Remix-DiT authorship), which is the sweep doing its job in both directions. The prior-art map carries no unverified load-bearing citation. Remaining pre-publish items are choices, not gates: the DiSCo/Context-Diffusion naming footnote, and whether to hold the push for E0's regime call.
