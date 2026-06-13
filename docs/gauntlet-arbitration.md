# Gauntlet Arbitration — pca-outline v0.1

**Inputs:** 16 distinct generalist reviews (note: `05.md` ≡ `deep-research-report-2.md`, byte-identical — counted once) + 1 sourced deep-research report with URLs (DR-1) + 3 independent verification searches run during arbitration (Diff-MoE, Fresco, Zheng time-agnosticism).
**Date:** 2026-06-12.

## 1. Verdict table

| Claim | Panel consensus | Median kill prob. | Disposition |
|---|---|---|---|
| C1 (coupled schedule) | ADJACENT-to-MAJOR; every component exists, the composition doesn't; novelty conditional on C3 | ~50% | **Demote to system description (S1), conditional on M1.** Not a standalone contribution. |
| C2 (explicit > implicit) | Genuinely contested — panel split between "established law" and "proven unnecessary" | ~40% | **Reframe as regime-conditional measurement (M2)** with redesigned protocol. The panel's own contradiction is the finding (see §3c). |
| C3 (coupling matters) | Ranked #1 survivor by 13 of 16 reviews; DR-1 ran auditable-absence searches and found nothing | ~32% | **Promote to primary contribution (M1).** Ablation redesigned (§4). |
| C4 (emergent routing) | Phenomenon pre-empted in diffusion MoE; probe asymmetric; "emergent" framing logically compromised | ~65% | **Dead as claim. Demote to diagnostics (D1)** with redesigned controls. |
| C5 (hard-wired routing) | Universal kill: Diff-MoE, MoDE, Switch-DiT, ProMoE, eDiff-I, plus internal contradiction with C4 | ~78% | **Drop.** Tombstone retained in v0.2. |

## 2. Killing citations, verified

These drove the drop decisions and were independently verified during arbitration (not taken on reviewer authority):

- **Diff-MoE** — Cheng et al., ICML 2025 (PMLR v267). VERIFIED. "Expert-specific timestep conditioning" in diffusion MoE. Kills C5's mechanism novelty outright.
- **Switch-DiT** — Zhang et al., arXiv 2403.09176. Sourced by DR-1 with quote: gating conditioned *solely* on timestep embeddings; explicit parameter isolation beats sharing across timesteps. Independent second kill on C5; pre-empts C4's phenomenon with explicit conditioning.
- **MoDE** — Reuss et al., CoRL 2024, arXiv 2412.12953. Sourced by DR-1 with quote: noise-conditioned routing token. Explicit, not emergent (see §3b).
- **Race-DiT** — arXiv 2503.16057, VERIFIED in arbitration search: documents expert-allocation evolution across denoising timesteps. The C4 phenomenon, measured, in images.
- **Zheng et al., "MDMs are Secretly Time-Agnostic"** — ICLR 2025, arXiv 2409.02908. VERIFIED. Training and sampling of masked diffusion are theoretically free of the time variable. This is M2's stated null hypothesis (§3c).
- **eDiff-I** — arXiv 2211.01324 (not 2202.12855 as DR-1 mis-cited). Real; 04's RECONSTRUCTED flag was over-cautious.

## 3. Adjudications — where the panel was wrong

**(a) "The router can't see shuffled labels, so the probe is physically meaningless" (3 reviews, incl. the duplicated DR-2).** Wrong. Position enters the *model* as input under V2; the router reads hidden states downstream of that input, so manipulating the label can move routing. The probe is coherent. The critique that *stands* is the asymmetric version (reviews 12/14): the probe can **falsify** position-tracking (routing follows content → content-driven) but cannot **confirm** it (routing following the label only proves label-detectability). v0.2's D1 adopts the asymmetric framing and discloses it.

**(b) MoDE characterization conflict.** One review claimed MoDE shows *emergent* specialization; DR-1's sourced quote settles it: MoDE's router *receives* the noise token — explicit conditioning. MoDE pre-validates C5's direction, not C4's emergence. The emergence-adjacent evidence is Race-DiT's allocation-evolution measurement and (per one search-enabled review) Diff-MoE's "entangled routing" analysis — verify that specific framing against the Diff-MoE paper body before citing it.

**(c) The C2 contradiction is a regime question, and it dissolves into experiment E0.** One camp: explicit step conditioning is established best practice (DDPM lineage, Diffusion-LM), C2 is "experimental hygiene" — 95% kill. Other camp: Zheng et al. *prove* the time variable is unnecessary in masked diffusion, and MDLM's ablation confirms minimal impact — the claim's direction may be wrong. Both are right in different regimes, and the regime is determined by one property: **whether schedule position is inferable from the input itself.** In MDMs it is (mask ratio is visible), so time conditioning is redundant. In DDPM-style continuous noise it is less so. Whether Context Diffusion views leak position is an empirical property of the teacher data — measurable by a CPU-only classifier (E0, from review 00, the single best methodological suggestion in the pile). E0 decides which regime M2 lives in *before any GPU training*, and simultaneously determines whether D1's probes are interpretable.

**(d) Fresco.** Real paper — "From Sketch to Fresco," Zheng et al., arXiv 2601.07462, CVPR 2026 — but the review citing it hallucinated the authors ("Carlson et al.") and inflated its scope. Verified: it is a *training-free acceleration* method for image/video DiTs (low-res drafting, variance-guided progressive upsampling of the output canvas). No training objective, no external source, no position conditioning, output-side. ADJACENT (cascaded/Matryoshka family), not the claimed 75%-kill MAJOR OVERLAP. Half-real citations — real paper, wrong authors, wrong scope — are the most dangerous failure mode this gauntlet surfaced; the verification layer caught two (Fresco, "From Amateur to Master").

**(e) "From Amateur to Master (Yang et al., 2024)".** Confirmed misattribution by three independent reviews: the real paper is Neema et al., 2025 (arXiv:2510.26336), automated curriculum learning for knowledge infusion — not hierarchical generation. Row removed in v0.2.

**(f) "(k, K) is an unbounded signal that breaks bounded-state invariants" (review 16).** Dismissed: two integers, O(log K) bits.

**(g) SUNDAE correction (review 14, live-verified).** SUNDAE applies a shared operator with *no explicit step index* — the closest text-domain iterative refinement work does **not** use explicit position conditioning. This *strengthens* the explicit-signal element of S1/M2 rather than threatening it.

## 4. Methodology rulings (consensus, adopted into v0.2)

1. **E2 redesign (M1).** The old three-arm design fails four ways: token-budget confound (full-resolution arms force truncation), coupled-by-learning leak (unconstrained arms may self-couple), ill-posedness (decoupled arms force inconsistent objectives), and one-model-vs-three-students ambiguity. v0.2 adopts: three separately trained students on condition-matched teacher data; decoupled arms with **forced-uniform** opposite sides; a **misaligned-schedule** arm (output lags input by one phase) to isolate synchronization; budget defined as *total tokens processed* with FLOPs and latency reported alongside; and a **matched-compute single-pass dense baseline** as the existence check — if coupled multi-pass can't beat one pass at equal total compute, nothing downstream matters.
2. **E1 redesign (M2).** All arms train on *identical* teacher tuples; only the position-delivery channel varies (explicit field / prompt text / absent). Prompt arm demoted to procedural floor (three reviews flagged it as a strawman). Added arm: binary mode token ({scaffold, edit}) vs full (k, K) — tests the mode-switch confound (review 12). Teacher confound honestly reframed: E1 measures *distillation efficiency per conditioning channel* — the deployment-relevant question — not a universal causal claim. Independent/uniform-teacher control listed as the stretch experiment that would license the stronger claim.
3. **D1 controls.** Twin-model null (same data, position fields ablated) retained with its limits stated; **cross-schedule view-swap probe** (reviews 08/16: feed pass-7's verbatim view at pass-1's position and vice versa, track which signal routing follows) replaces sole reliance on label-shuffling; asymmetry disclosed up front.
4. **Experiment ordering** (review 13's point made binding): E0 → prompt-level micro-pilot → 2-hour position-token pilot → E2′ → E1′ → D-suite. Gates between each.

## 5. Verification queue (run before publication; reviewer-search-attested but not arbitration-verified)

LoopMoE (June 2026, IterAdaLN — in-domain C5 neighbour, attested by one live-search review); DVLT/Déjà View (NVIDIA, May 2026); SCUD (NeurIPS 2025, schedule-conditioned discrete diffusion); COMI (ICLR 2026, coarse-to-fine context compression); FraiLT (arXiv 2401.11626, iteration encodings); Residual Context Diffusion (Jan 2026); EC-DIT; Remix-DiT (NeurIPS 2024); DICE (ICCV 2025); ProMoE — note arXiv 2510.24711's actual title appears to be "Routing Matters in MoE," reconcile; Ganjdanesh et al. ECCV 2024 (arXiv 2409.15557); Think Twice (2510.23596); Ponder in Continuous Space (2505.20674); COCONUT (COLM 2025); s1 (2501.19393); Mode-Conditioning (Wu et al. 2025); OpenMoE token-ID finding; ST-MoE positional-features nuance (review 14's live check says adding position features to the router *helps* — mildly pro-D1); DiffusionGemma Sudoku early-stopping phrasing (one review couldn't attest it; it is in the developer-blog text — cite the blog directly).

## 6. What survived, in one paragraph

The program is now: **one primary empirical contribution** (M1, the coupling interaction — the only claim every review ranked top-two and the sourced search cleared with an audit trail), **one regime-conditional measurement** (M2, gated by a free CPU experiment that resolves the panel's own contradiction), **one honest system description** (S1, valuable iff M1 holds), and **one interpretability appendix** (D1). C5 is dead and the diffusion-MoE literature that killed it is so saturated — Diff-MoE, Switch-DiT, Race-DiT, ProMoE, Remix-DiT, DICE, eDiff-I, MoDE — that its death is the safest conclusion in this document.
