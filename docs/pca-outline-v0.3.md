# Pass-Conditioned Architectures for Context Diffusion (working title) — v0.3

**Status:** publish-ready. v0.1 survived a 19-input adversarial gauntlet (`gauntlet-arbitration.md`); v0.2 restructured the claims; v0.3 incorporates a five-agent pre-publication verification sweep with arbitration and one ground-truth full-text check (`verification-arbitration.md`). Every citation in §5 is verified; no ◯Q rows remain.
**Naming note:** "Context Diffusion" collides with Najdenkoska et al. 2023 (arXiv 2312.03584), an in-context *image generation* method. **DiSCo** is the headline operator name here; "Context Diffusion" is the descriptive layer, unrelated to that work.
**Parent proposal:** [DiSCo / diffusive-semantic-compression](https://github.com/dev-boz/diffusive-semantic-compression). Formalism carries over: at pass `k` of `K`, the model receives state `s_{k-1}`, view `v_k`, position `(k, K)`, task `q`, and emits edit operations.

## 1. Position

One primary empirical contribution, one regime-conditional measurement, one system description, one diagnostic:

- **M1 (primary): the coupling interaction.** Jointly staging input view resolution and output detail level under one schedule outperforms staging either side alone, at matched total compute. Five independent fresh-eyes sweeps (≈50 logged queries) found no prior coupled-vs-decoupled input/output staging ablation on a language task as of 2026-06-12.
- **M2 (measurement): conditioning-channel efficiency.** Among ways of delivering schedule position to a small student — explicit architectural field, prompt text, or not at all — which yields schedule-competent behavior cheapest at ≤8B? Regime-conditional; see §4.
- **S1 (system description): the coupled schedule itself.** One position signal governing both what the model is shown and what it must emit, over an external source. Not a mechanism claim; its value is established by M1 or not at all.
- **D1 (diagnostic, not a claim): routing analysis** of MoE students trained under this objective, reported as interpretability with disclosed limits.

**Dropped: hard-wired position routing (v0.1's C5).** Cause of death: Diff-MoE (Cheng et al., ICML 2025 — expert-specific timestep conditioning), Switch-DiT (2403.09176 — gating conditioned solely on timestep), MoDE (CoRL 2024 — noise-conditioned routing token), ProMoE (2510.24711), eDiff-I — a saturated design space. Hard-wiring position would also discard the content specialization D1 measures.

## 2. What changed and when

v0.1→v0.2: coupling claim promoted after unanimous top-two survival ranking; explicit-conditioning claim reframed around the regime question its split panel exposed; coupled-schedule claim demoted to system description; MoE prediction demoted to diagnostics; all experiments redesigned against consensus methodology attacks. v0.2→v0.3: every remaining citation verified by a five-agent sweep plus arbitration; three corrections applied to our own rows (ST-MoE rewritten from the actual paper, LoopMoE's conditioning ablation acknowledged, Remix-DiT authorship); RCD, NaviEdit, ChainCoder, LoopMoE added to the map; naming disambiguation added.

## 3. The variants (revised)

### Variant 1 — Generalist baseline (unchanged; not a contribution)

Prompt-only execution. ~50% malformed edit ops at 1.5B. Exists to be beaten.

### Variant 2 — Pass-conditioned multi-resolution training (the core)

Training tuples `(k, K, v_k, s_{k-1}, e_k)`, position as explicit input. Input side: views per the parent's compression schedule. Output side: state detail progresses in lockstep — scaffold, then concrete-abstractive, then verbatim integration — one schedule governing both.

**Mode resolution:** hybrid. Pass 1 renders the scaffold from scratch as a *bounded exception*: scaffold length capped at an explicit budget `B_s` (a schedule parameter), so pass-1 cost is `O(B_s)`, stated rather than implied. Subsequent passes emit edit operations; *output* cost per pass is bounded by the edit budget, while the *state* is bounded separately by the parent's window invariant — two different bounds, not conflated. Pure edit mode retained as an ablation arm. Render mode (full regeneration every pass) excluded: `O(|state|)` per pass.

**Known confound, stated as design fact:** the position signal may partly function as a mode switch (scaffold-pass vs edit-pass). E1′ includes a binary-mode-token arm to measure how much of the conditioning value is mode selection versus genuine schedule position.

**Training data:** teacher-generated, with the consequence stated plainly: results measure what is *learnable from a schedule-executing teacher per conditioning channel* — a distillation-efficiency result, the deployment-relevant question — not a universal causal claim. The schedule-blind-teacher control that would license the stronger claim is listed as a stretch experiment.

### Routing diagnostics (was Variant 3; no longer a variant)

D1 instruments E1′/E2′ MoE runs: routing-distribution divergence across passes against a twin-model null (same data, position fields ablated), plus a **cross-schedule view-swap probe** — feed a late-pass verbatim view at an early position and vice versa, and track which signal routing follows. The label-shuffle probe's asymmetry is disclosed: it can falsify position-tracking, never confirm it. Findings are reported as interpretability, with Diff-MoE / Race-DiT / EC-DiT cited as the reason this cannot be a novelty claim. **What makes the measurement worth taking:** in language MoE, routing is known to key on token identity and content (OpenMoE; ST-MoE's specialization analysis), and — per the verification sweep's ground-truth check — the effect of positional information on language-MoE routing is simply *unmeasured*: ST-MoE's only adjacent experiments (Appendix J: expert-identity embeddings on expert outputs; routed/dropped history into the router) were negative or neutral, and no one has fed schedule position to a reading-schedule-trained router and looked. D1 targets an empty cell, not a contested one.

## 4. Claims

**M1 — The coupling matters.** At matched total compute, the coupled schedule outperforms input-staged-only (forced-uniform detailed output every pass), output-staged-only (forced-uniform full-resolution input every pass), and a deliberately misaligned schedule (output staging lags input staging by one phase). Framed as a 2×2 factorial (input staged × output staged) plus the misalignment arm: the claim is a positive *interaction term* plus sensitivity to *synchronization*, not a main effect. *Dies if:* either single-sided arm matches coupled; or misaligned matches aligned; or the matched-compute single-pass dense baseline matches everything. *Budget definition:* total tokens processed (prefill + decode) across the full schedule, with FLOPs and wall-clock reported alongside; the full-resolution arms inherently sacrifice the bounded-per-pass property — reported, not hidden. *Context for expectations:* NaviEdit (2026) finds decoupling *wins* for image-editing schedule axes — coupling's value is setting-dependent, which is exactly why this ships as a pre-registered measurement with kill criteria rather than an assumption.

**M2 — Conditioning-channel efficiency (regime-conditional).** All arms train on *identical* teacher tuples; only the position-delivery channel varies: (a) explicit `(k, K)` field, (b) prompt-text position **plus per-pass behavioral rubric** (procedural floor; rubric per the P3 pilot — a 2–3-line stated expectation per schedule stage, replacing the bare prompt-text assertion of earlier drafts, updated 2026-06-12), (c) no signal (trajectory only), (d) binary mode token. Metrics: edit-op validity, position-appropriateness, end-task score. **Stated null hypothesis:** Zheng et al. (ICLR 2025) prove masked-diffusion training and sampling are time-agnostic because corruption level is inferable from the input. **The literature now brackets the axis:** SCUD (NeurIPS 2025) shows masking diffusion wins *because* its jump schedule is inferable, and injecting the schedule rescues structured diffusion where it isn't; LoopMoE (2026) shows that when iteration index is *not* inferable from a loop's near-identical inputs, explicit iteration conditioning (IterAdaLN) is needed. Whether Context Diffusion views leak position is exactly E0's question, answered before any training. *Dies if:* E0 shows position near-perfectly inferable and E1′ confirms no gain; or arm (c) matches arm (a); or gains reduce to arm (d)'s mode-switching.

**S1 — The coupled schedule (system description, conditional on M1).** One inference-time schedule governs both input view resolution and output detail, position as explicit model input, over an external source that is never reconstructed. Against the nearest families: cascaded/Matryoshka/Fresco-style multi-resolution diffusion stages the *generation canvas*; the views here are lossy observations of an external, immutable source, and the refined object is a bounded task-conditioned state. RCD recycles the model's own discarded denoising states — trajectory smoothing, not source staging. COMI compresses input coarse-to-fine but decodes once, single-pass. SUNDAE, the closest iterative text-refinement work, uses a shared operator with *no* explicit step input (verified), so the explicit-position element is less precedented than v0.1 assumed. If M1 fails, S1 reduces to an implementation note.

**D1 — Routing diagnostics (not a claim).** As specified in §3. Pre-registered readouts: routing-position divergence vs twin null; view-swap probe outcome (position-following / content-following / mixed); correlation of any specialization with task metrics. All three outcomes are reportable; none is claimed as novel — the phenomenon is documented in image-domain diffusion MoE (Race-DiT allocation evolution; Diff-MoE; EC-DiT). The fresh information is the language/reading-domain measurement of a cell the sweep confirmed empty.

## 5. Prior-art map v3 (fully verified)

Status key: ✔A = verified in arbitration against primary text/proceedings; ✔R = agent-verified with URL and verbatim line; ●M = multi-review CERTAIN, pre-cutoff, uncontested.

### A. Reading, staging, and refinement

| Work | What it does | Delta here | Status |
|---|---|---|---|
| RLM (Zhang et al. 2025) | LLM-driven recursion, external state | No schedule, no explicit position; parent | ✔R |
| LCM (2026) | Engine compaction, lossless pointers, no training | Parent | ✔R |
| ReadTwice (NAACL 2021); Retrospective Reader (AAAI 2021) | Two-pass reading: compressed/sketchy then detailed | K=2 fixed, no position signal, no staged output state | ●M |
| MemWalker (2023); FLARE (EMNLP 2023); Self-RAG (2023) | Navigated / retrieval-driven multi-pass input | Decision-driven access, no schedule, no output staging | ●M |
| Plan-and-Write (AAAI 2019); Fan et al. (ACL 2018); ProGen (Tan et al., NAACL 2021); Dong & Lapata (ACL 2018); Skeleton-of-Thought (2306.02228); ChainCoder (ICML 2023) | Output staged coarse→fine (stories, parsing, code) | Fixed full-resolution input; no explicit inference-time position signal | ✔R/●M |
| SUNDAE (ICLR 2022, 2112.06749); Mask-Predict; Levenshtein Transformer | Iterative text refinement / edit-op generation | No explicit step input (SUNDAE ✔); output-side; constant source | ✔R |
| COMI (Tang et al., ICLR 2026, 2602.01719) | Coarse-to-fine *input* context compression via marginal information gain (up to 32×) | Single-pass autoregressive decode; no multi-pass state, no position conditioning | ✔R |
| Funnel Transformer (2020); Perceiver (2021) | Architectural input compression | Architectural, not an inference-time schedule | ●M |
| Cascaded Diffusion (JMLR 2022); Matryoshka Diffusion (Gu et al., ICLR 2024, 2310.15111); Fresco (Zheng et al., CVPR 2026, 2601.07462) | Output-canvas resolution staging in images/video; Fresco is training-free variance-guided progressive upsampling | Generation-target staging, not external-source observation; no reading state | ✔A/✔R |
| Residual Context Diffusion (Hu et al., ICML 2026, 2601.22954) | Recycles discarded denoising-step token states as contextual residuals for the next step | Internal trajectory smoothing on the output path; prompt source never staged | ✔R |
| NaviEdit (2605.21190, 2026) | Decouples edit progress from scale traversal in image editing; finds decoupling wins there | Output-canvas coordinates, no external source, no language; evidence that coupling's value is setting-dependent | ✔R |
| HDLM (NeurIPS 2025); LLaDA (dense, 2502.09992); DiffusionGemma (2026, dev-blog cited directly incl. Sudoku early-stopping quote) | Same-length output diffusion LMs; DiffusionGemma = content-routed MoE instance | Parent distinctions | ✔R |
| Think Twice (2510.23596); PonderLM (Zeng et al., ICLR 2026, 2505.20674); COCONUT (COLM 2025, 2412.06769); s1 (2501.19393, arXiv-only) | Pass/iteration-flavored reasoning & test-time compute; PonderLM feeds no step signal | Own-output refinement; no external-source view schedule | ✔A/✔R |

### B. Position / step conditioning

| Work | What it does | Delta / relevance | Status |
|---|---|---|---|
| DDPM lineage; DiT (AdaLN) | Explicit timestep conditioning | Output-denoising step, not reading-schedule position | ●M |
| **Zheng et al., MDMs Secretly Time-Agnostic (ICLR 2025, 2409.02908)** | Time variable provably unnecessary in masked diffusion | **M2's null hypothesis**; regime selected by E0 | ✔A |
| MDLM (Sahoo et al., NeurIPS 2024) | Timestep-conditioning ablation, minimal impact | Empirical support for the null | ✔R |
| **SCUD (Amin, Gruver, Wilson; NeurIPS 2025, 2506.08316)** | "Why Masking Diffusion Works": conditions discrete diffusion on the jump schedule explicitly | Masking wins because its schedule is inferable; injecting the schedule rescues structured diffusion — brackets E0's axis from the non-inferable side | ✔R |
| **LoopMoE (Chen et al., 2606.04438, June 2026)** | Looped language MoE; IterAdaLN token-level iteration conditioning; **includes** Loop Base (trajectory-only) vs +IterAdaLN ablation | Recursion-depth conditioning where iteration is not inferable from near-identical loop inputs; gains reported (magnitude: quote only after direct read of Table 3); no reading schedule | ✔R |
| Universal Transformer (2019); ACT (2016) | Explicit step/depth in iterative shared-weight transformers | Depth recurrence, fixed input | ●M |
| FraiLT (2401.11626); DVLT/DéjàView (2605.30215, 2026) | Learnable iteration encodings (FraiLT, no explicit-vs-trajectory ablation); step-conditioned looped refinement with K as compute knob (3D vision) | Closest explicit-iteration mechanisms; no reading schedule | ✔R |
| SCoRe (ICLR 2025); PTR (ICLR 2025); Self-Refine; Reflexion | Implicit position via trajectory/attempt structure | The trajectory-only arm's lineage | ✔R |
| Mode-Conditioning (Wu, Goyal, Raghunathan; 2512.01127) | Explicit allocation across reasoning *modes* | Adjacent to the mode-token arm; not schedule position | ✔R |

### C. MoE routing (D1's context; C5's graveyard)

| Work | What it does | Relevance | Status |
|---|---|---|---|
| **Diff-MoE (Cheng et al., ICML 2025)** | Expert-specific timestep conditioning in diffusion MoE | Kills hard-wired-routing novelty; D1 context | ✔A |
| Switch-DiT (2403.09176) | Gating conditioned solely on timestep; explicit isolation > sharing | Second independent kill | ✔R |
| MoDE (CoRL 2024, 2412.12953) | Noise-conditioned routing token (explicit) | Pre-validates the dropped C5 direction | ✔R |
| Race-DiT (2503.16057) | Measures expert-allocation evolution across timesteps | The D1 phenomenon, documented in images | ✔A |
| EC-DiT (Xu et al., ICLR 2025, 2410.02098); Remix-DiT (Fang et al., NeurIPS 2024, 2412.05628); DICE (Luo et al., ICCV 2025, 2411.16786 — staleness-centric parallel diffusion-MoE inference); Ganjdanesh et al. (ECCV 2024, 2409.15557); Routing Matters in MoE / ProMoE (Wei et al., ICLR 2026, 2510.24711) | Timestep-aware allocation (observed *and* designed), basis-mixed timestep experts, staleness optimization, interval experts, explicit semantic routing guidance | Saturation of the space | ✔R |
| eDiff-I (2211.01324) | Noise-interval expert ensembles | The lineage's origin | ✔R |
| OpenMoE (Xue et al., 2402.01739) | Token-ID-dominated, context-independent routing | What language-MoE routing keys on absent intervention | ✔R |
| **ST-MoE (Zoph et al., 2202.08906)** | Router z-loss stability; encoder experts specialize (punctuation, verbs, proper nouns), decoder experts don't, multilingual experts not by language. Appendix J negatives: expert-identity embeddings on expert *outputs* and routed/dropped history into the router — no improvement. **No sequence-positional router features tested.** | Corrected from ground truth after a three-way agent quote conflict; positional-router-features question is *unmeasured* in language MoE — D1's cell is empty, not contested | ✔A |
| StableMoE (ACL 2022, 2204.08396); Hash Layers (2021); Expert Choice (2022) | Frozen/structured vs learned routing: regime-dependent | Why C5 was unanswerable as posed | ●M |

Removed in v0.2, stays removed: "From Amateur to Master (Yang et al., 2024)" — misattribution (actual: Neema et al. 2025, 2510.26336, unrelated).

## 6. Experimental program (gated)

**E0 — Position-from-view classifier. Run first; CPU-only; ~1 day.** Predict `(k, K)` from `v_k` alone on the teacher data. Near-ceiling → time-agnostic regime: explicit channel predicted redundant, D1 probes pre-declared uninterpretable. Low → the signal carries non-redundant information; M2/D1 proceed. The Zheng–SCUD–LoopMoE bracket makes this one classifier the regime selector for the whole program.

**P1 — Prompt-level micro-pilot. ~2 days, no training.** One long document, three hand-built schedules (coupled / input-only / output-only), off-the-shelf 7–8B model, transcripts for manual review.

**P2 — Position-token pilot. ~2 hours.** Explicit position field vs none on the V1 PoC; edit-op validity delta. Prompt-level proxy; the trained comparison is E1′.

**E2′ — M1 (load-bearing).** Separately trained 1.5–3B QLoRA students on condition-matched teacher data: coupled / input-staged-only (forced-uniform detailed output) / output-staged-only (forced-uniform full-resolution input) / misaligned-coupled / V1 prompt floor, plus the matched-compute single-pass dense baseline. Budget = total tokens processed; FLOPs and latency reported.

**E1′ — M2.** Four conditioning-channel arms on identical data (explicit / prompt floor / none / mode token), gated by E0's regime call. Stretch: schedule-blind-teacher control.

**D-suite — D1.** Twin null, cross-schedule view-swap probe, divergence-vs-metrics correlation on an inspectable open MoE (OLMoE-class — confirm best current option). Appendix material.

## 7. Honest scope

M1 is the paper; if its interaction term is null, this reduces to the parent's claims plus one-sided staging results that already exist — and NaviEdit is the standing reminder that decoupling can win. M2 is a distillation-efficiency measurement under a stated null, bracketed by Zheng (inferable → conditioning redundant) and SCUD/LoopMoE (non-inferable → conditioning needed); the teacher confound limits generality and the schedule-blind control is unfunded. S1 is a composition of published mechanisms whose value is entirely M1-conditional. D1 cannot confirm position-tracking, only falsify it; its target cell is empty in the language literature, verified against the primary text after agent quote-fabrication in both directions. E0 may kill M2 and D1 before any GPU is touched — that is a feature. Every row in §5 carries a verification status; nothing load-bearing rests on an unread paper.
