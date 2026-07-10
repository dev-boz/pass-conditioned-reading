# A DiSCo-native LLM: ground-up design exploration (v2)

*Companion to the Context Diffusion / DiSCo / pass-conditioned-reading program. Status: **unvalidated design exploration.** Nothing here is tested. Several mappings to existing systems are borrowable machinery, not identities — flagged inline. Argue with it in the same honest-scope spirit as the proposal's own "why this isn't X" sections.*

**What changed from v1 (2026-07 revision, after reading the pass-conditioned-reading data):**
- The "~50% malformed edit ops" motivation for a latent state is **retracted** — it was a parser artifact (edit-op validity is ≈1.0 on an untrained 7B once the parser accepts the naming convention). §3 is re-motivated around the failures the data *actually* shows: the pass-3 **id-misaddressing clobber** (retention) and the **21/22 recombination** failure (relational binding).
- The **coupling (M1)** — one schedule position governing both input-view resolution and output detail — is now treated as the central claim, and AdaLN is argued as its natural home, with support from the P2/P3/E0 pilots.
- §1's economic framing is corrected: the win is **not "small window good,"** it's that window size becomes a cost/quality knob *decoupled from input length*. (Credit: Boz's pushback.)
- A new §1.5 states what the integration state is *for* — **non-local understanding** — and separates the two things called "nuance," only one of which the architecture can claim.
- The **"works on off-the-shelf models today" framing is dropped as a virtue.** A custom model was the target from the start; the untrained-floor runs are diagnostics, not a deployment path. So the native design isn't "trading away" deployability — §9 is re-cast from *tradeoff* to *real cost* (compute, expertise, architecture-risk).
- Added **§5.6 on the compressor** — it is the forward/noise process and the highest-leverage *end-product* lever (co-designed to the reader's relevance target, not co-trained), but explicitly **not a PoC concern**: the data shows coverage already works and the blocker is integration.
- Added the **soft-vs-hard-experts fork** (§2 — one AdaLN-modulated net vs a separate expert per pass; the latter is the eDiff-I/MoDE/D1 lineage, kept as a per-*phase* ablation that must earn its cost) and the **Global Workspace framing** of the shared state (§3 — the integration state as a bandwidth-limited workspace the pass-phases and towers coordinate through).
- Added the **ε-vs-x̂₀ training-parametrization arm** (§5, from DiffusionBlocks 2506.14202): imitate the teacher's edit ops vs train each pass toward the teacher's *state* — the latter is path-independent, requires the latent state (§3), and inherits diffusion's stage-wise-independent-training property.

---

## 0. The premise

The current DiSCo implementation is bolted onto a model built for something else. An off-the-shelf transformer is asked to read text views, hold a **text** integration state, emit **text** edit operations, and infer its schedule position from a prompt string. A ground-up model moves each of those into the weights: how it is **conditioned** (pass position), where the **state** lives (latent), how it **reads** (a reader/refiner split), how **compute is scheduled** (learned halting). None of these require the risky move of also making the *views* latent — that one is quarantined in §6.

The pilots point at three concrete failure joints for the untrained floor, and the native design should be read as attacking exactly these:
- **Recording** — under a vague task the floor omits non-obviously-relevant detail (P4; P5 showed this is task-vagueness, not prior-state contamination — a specification lever, partly).
- **Retention** — a recorded item is clobbered mid-schedule by an edit that mis-addresses its slot (P7's pass-3 `REPLACE S3: FUNCTIONS=…` overwriting the table). This is a harness/representation bug, and content-addressed writes are the fix.
- **Recombination** — with *both* operands held in the final state, 21 of 22 seeds still failed to combine them (P7 cross-family). The op-DSL carries atoms but strips the *binding* between them.

---

## 1. The economic framing (corrected): window size becomes a decoupled knob

The v1 headline ("build a deliberately small-context model") was too strong. The accurate claim: DiSCo makes the context window a **tunable cost/quality dial, decoupled from input length**, instead of a hard requirement set by your longest input. Three consequences, all of which Boz flagged and all of which are right:

- **A bigger window makes DiSCo *easier*, not redundant.** Larger `W` → each slice can be less compressed → less loss per pass → fewer passes → less coarse-to-fine compounding. A product tunes the window *up* toward the cost ceiling, not down to the floor. Small windows are a *testing* choice (and a way to prove the method, not the window, is doing the work).
- **Model capability is an orthogonal axis.** Window size and parameter/quality are independent. A stronger model compresses, integrates, and follows the schedule better. Use the best model you can afford; DiSCo lets *whatever* model you pick ingest inputs past its window. It is "and," not "instead of."
- **The per-turn output ceiling is real.** A bounded window bounds what a single pass can *emit*. This is the parent proposal's "faithful output must be bounded" caveat seen from the generation side: DiSCo targets huge-**input**, bounded-**output** tasks (a reply, a decision, a brief). Genuinely long-form *generation* would need the coarse-to-fine trick applied to the output too — out of scope for now, and worth stating as a scope line rather than hiding.

The still-sharp version of the payoff: at a *fixed* window and a *fixed* model, DiSCo handles inputs that neither could otherwise touch, at predictable cost, with an auditable recoverable process. That is the claim — not that small is better.

## 1.5. What the integration state is *for*: non-local understanding

This is the load-bearing reframe, and it is what the pass-conditioned-reading data quietly proves the program is really about.

The integration state exists to hold what is true of the **whole** source but present in **no single view** of it. Call it *non-local* structure. RAG retrieves parts; compaction summarizes parts; both are local operations. A coarse-to-fine schedule integrating into a persistent state is the only one of the three that can carry something that survives in no part.

There are two very different things people call "nuance," and only one is non-local:

- **Tone / register** ("this thread is melancholic," "he writes terse") is **local** — any single slice carries it. A single prompted pass recovers it. This does *not* discriminate the architecture from a one-slice read, and the program was right to drop it.
- **Emergent / distributed nuance** — a stance that quietly soured across three weeks, an unstated tension between two goals stated far apart, a detail that recontextualizes a later decision — is **non-local**. It exists only as an integration across the span. This is what the README means by "hidden if only given partial or fragmented information."

The split-unit arithmetic fact (P7's `988 + 1365 = 2353`) and emergent nuance are **not the same shape** — one is discrete, one is diffuse — but they share the one property that matters: **non-locality**. That shared property is what grants the architecture its discrimination power over a single-pass read. The diffuseness of nuance is only why it is *harder to score*, which is the honest reason a measurability-optimizing program drifted from it to the arithmetic target (see the separate nuance-experiment note). The native architecture's job description, stated once: **be a machine for non-local integration — of facts and of affect — toward a bounded state.**

This reframe also fixes the relevance-target problem (see §5): the state should distill toward "what a careful reader carries forward," which *includes* non-local affect, not toward the narrow literal query.

---

## 2. Pass-conditioning as AdaLN, and the coupling it serves *(build first)*

The single cleanest, best-supported native upgrade, and the home of the M1 coupling claim.

Diffusion transformers never put the timestep in the token stream. They Fourier-embed it, run a small MLP, and generate **per-block scale/shift (γ, β)** modulating every attention and FFN sub-layer (AdaLN; "AdaLN-Zero" zero-inits the gates so each block starts as identity and *learns* how hard to modulate). Feed `(k, K)` — and a state-budget signal `|s_{k-1}|/W` — in exactly that way.

The pilots predict this is the right mechanism, twice over:
- **P2**: a bare position *token* did nothing (validity 0.979 vs 0.983, null). A signal that only enters at the input and has to survive the stack is too weak.
- **P3**: a per-pass *behavioral rubric* cleanly induced staging (pure ADD while scaffolding, pure REPLACE while integrating). AdaLN is the in-weights version of "condition behavior on position" — the rubric baked into the normalization statistics of every layer rather than asserted in a prompt.
- **E0-final**: position is *not* recoverable from the view (0.561, "signal-carrying"), so an explicit conditioning channel is non-redundant — it is justified to build one at all.

**The coupling (M1) is the natural payload.** One position embedding drives *both* what input resolution the model expects *and* what output detail is appropriate — that is the coupling stated as a single conditioning vector. AdaLN makes "input-side expectation" and "output-side behavior" two heads off the same `(k,K)` embedding, which is the mechanically honest way to express "one knob governs both sides."

**First falsifying test:** train two identical small refiners on the same teacher trajectories, one AdaLN-conditioned, one with position as input tokens. If AdaLN doesn't beat the token version on position-appropriate behavior, the mechanism isn't earning its complexity. (This is E1′ with an AdaLN arm added.)

**Soft modulation vs hard per-pass experts (the alternative, and why it's an ablation not the default).** The obvious stronger version of pass-conditioning is a *separate expert per pass* rather than one modulated network — and the phases genuinely are different jobs (scaffold-from-a-blur / integrate-mid-detail / surface-verbatim-and-revise), the same "layout vs texture" case eDiff-I makes for images. It is well-precedented on the image side (eDiff-I noise-interval expert ensembles; MoDE noise-conditioned routing token; Diff-MoE expert-specific timestep conditioning; Switch-DiT timestep-only gating) — which is exactly why the pca-outline demoted hard-wired position routing (old C5) and kept only D1's routing diagnostic. Three reasons AdaLN stays the default and experts stay an ablation that must *earn* their cost: **continuity** (the state flows across passes; hard model-switches risk a seam where smooth modulation interpolates), **cost** (K dense experts = K× parameters, each trained on 1/K of the pass-diversity data — fragmenting already-scarce signal, wrong for small models on limited compute), and **variable K** (content-aware slicing, §5.5, makes the pass count document-dependent, so literal per-pass experts have no fixed slots). If experts are tried, reframe *per-pass* → *per-phase*: 3–4 experts (scaffold / integrate / surface) selected by schedule position, which survives variable K and is cheap enough to defend. This is literally D1's question — does routing specialize by pass? — so it belongs in the program as a measured ablation, not a headline.

---

## 3. The integration state as a latent memory bank *(re-motivated by the P7 data)*

v1 justified this with the malformed-edits number, which is retracted. The *real* justification is stronger and comes straight from P7's two blocking joints.

Move the state off the token stream into a fixed bank of latent slots, and edits become **learned, content-addressed** read/write/gate operations. Two payoffs, each mapped to a named failure:

- **Content-addressed writes kill the retention clobber.** P7's retention failure was `REPLACE S3: …` hitting the wrong stable id and overwriting the table; the program's own E2′ requirement #2 is "content-addressed edit operations… validate that a REPLACE targets the intended content, not just the named id." A latent write *is* content-addressed by construction — you write to the slot whose meaning matches, not to a string id that can be mis-typed. The native state delivers their identified fix for free.
- **Relational storage attacks the recombination failure.** 21/22 seeds held both operands and still didn't combine them, because the op-DSL "strips the relational binding." A state that stores *relations* (bindings between slots), not just atomic entries, carries `surcharge = table[code] + adder` as a first-class object. This is the harder and more important half — the atoms were never the problem.
- **A continuous state unlocks the better training objective.** The x̂₀-style loss (§5 — train each pass to move the state toward the target state, not to imitate the teacher's edit ops) only has a gradient over a continuous state. Text states foreclose it. A third independent reason to go latent, from the training side.

**The state as a bandwidth-limited shared workspace (Global Workspace).** The cleanest frame for what this bank *is*: a Global Workspace (Goyal, Bengio et al., ICLR 2022, *Coordination Among Neural Modules Through a Shared Global Workspace*) — a bounded shared latent space that specialist modules read from and write to via attention, where the *limited capacity* forces them to share only what matters. The mapping is almost exact: the integration state is the workspace, the pass-phase behaviours (§2) and the reader/refiner towers (§4) are the specialists, and the window budget is the bandwidth bottleneck that enforces the bounded-state invariant. This is the principled version of "modules talking in latent space," and it is why the coordination channel is the *state itself* rather than passed text — the workspace is where content-addressed writes (above) land and where cross-tower attention (§4) reaches. It also reframes the bounded-state assumption (§5) as a feature, not just a constraint: the bandwidth limit is what forces the specialists to distill.

Machinery to steal, honestly labeled:
- **Cartridges** (trained-KV-cache built by self-study distillation) — the integration state *is* a cartridge, but built online by the schedule instead of offline. "Self-study" ≈ the teacher-distillation data plan.
- **Titans** (test-time memory writes gated by *surprise*) — the honest form of ADD/REPLACE, and a *relevance* mechanism orthogonal to task-salience. Surprise-gating records a striking-but-off-task detail, which is exactly the P4 recording gap — *provided* the relevance target is set correctly (§5) and not overfit to probe answers (respecting the program's §5c forcing-line worry).
- **Mixture-of-Memories / RMT** — multiple slots + routing so a conclusion over one region isn't clobbered by detail from another (the interference the clobber is a crude instance of).

Revisability (the edge over RAPTOR / the Ehrlich-Blackman LCM) gets a native mechanism from self-correcting/remasking diffusion LMs (ReMDM, RemeDi, 2025): revising a slot is remasking-and-re-denoising it given new evidence.

**Bounded attention over pass-history (from Dreamer, 2601.21582).** A fixed-size state over ~30 passes hits the "constant hidden-size bottleneck that restricts many-step" processing that depth-recurrent models hit; Dreamer's fix is *depth attention* — attend back over earlier steps instead of carrying one evolving vector. The DiSCo analog: let the refiner at close time attend over a **bounded window (or a few compressed checkpoint states) of prior pass-states**, not just `s_{k-1}`. This attacks recombination directly — operands written at pass 3 and pass 26 can be bound at close time by attending to the passes that wrote them, instead of both needing to survive in one overwritten state. The cost is honest: full-history attention grows with `K` and erodes the bounded-per-pass property, so the design is a bounded window or checkpoint set — which is where this meets RMT.

**First falsifying test:** re-pose P7 on a small model whose state uses content-addressed relational writes. If the pass-3 clobber and the recombination failure don't both improve over the string-id op-DSL, the latent state isn't buying what the data says it should.

---

## 4. A reader / refiner two-tower split *(native Context Diffusion)*

NVIDIA's Nemotron TwoTower is the template: a large, possibly frozen *reader* encodes the current view (bidirectionally — a view is a bounded block), and a small trained, pass-conditioned *refiner* owns the state and cross-attends into the reader for detail. Capability concentrates in the frozen reader you never retrain; the cheap trained part is the refiner, which is exactly what needs pass-conditioning. It also matches the program's economics: the trained student stays small (1.5–3B), the reading strength is borrowed.

**First falsifying test:** frozen strong reader + tiny trained refiner vs one mid-size model doing the whole job at matched FLOPs. If the split doesn't win, it's adding coordination cost without paying for it.

---

## 5. The theory spine: DiSCo is amortized Bayesian filtering — with a corrected relevance target

The proposal's §6 asks whether the reverse process "admits a well-defined reverse-time process." It does, and naming it does formal work: **the integration state is a posterior belief; each view is an observation; each edit is a Bayesian update; the schedule is the observation sequence.** That is the "grounded, not generative" property made precise — a filter conditions on observations rather than imagining detail from a prior.

The state converging to `s*` (a task-conditioned distillation) rather than to `x` is the statement that the belief is a **minimal sufficient statistic** — the Information Bottleneck: maximize `I(state; Y | q)`, minimize `I(state; source)`.

**The ε-vs-x̂₀ parametrization choice exists for passes, and it should be an experiment arm.** Diffusion trains each step either to predict the increment (ε) or the clean target (x̂₀); the choice matters empirically. The teacher-tuple plan as written is pure increment-imitation — reproduce the teacher's edit ops `e_k`, i.e. clone the teacher's *brushstrokes* — brittle, because many edit paths reach the same good state and the teacher's particular path is arbitrary. The x̂₀-style alternative: score pass k's output against the teacher's **state** (at pass k, or final `s*`) with position-dependent weighting — path-independent, denser per-pass signal, and the mechanism that makes independent per-timestep training work in diffusion at all. DiffusionBlocks (Sakana AI, 2506.14202) demonstrates the same stage-wise-independence property on a second axis (network depth), across five transformer families — the empirical answer to "don't you need credit assignment through the whole schedule?" **Caveat: the x̂₀ objective requires the latent state (§3).** "Move toward `s*`" has a gradient only if the state is continuous; a text state forecloses the denoising-objective family entirely. (Speculative unification from the same paper, flagged as framing rather than validated design: blocks-within-a-pass and passes are the same kind of denoising step — one L×K-step trajectory over the state with observation injections at pass boundaries — collapsing the recurrent-depth axis and the pass axis into one object.)

**The correction the pilots force — the choice of relevance variable `Y` is the whole game, and P4 is what happens when you pick it wrong.** If `Y` is the narrow literal query, the state correctly drops task-orthogonal asides — which is exactly P4's "failure" (it dropped a codename, a personal anecdote, a morning-walk aside from a *strategy brief*, and the metric penalized it). That is not the premise failing; it is a mis-specified `Y`. Set `Y` to "what a careful reader carries forward" — including non-local affect — and the same architecture keeps those details and still stays bounded, because the target is broader but finite. Operationally: **condition on the narrow task at readout, not by throwing detail away each pass.** Keep a richer belief; collapse to the query only when answering.

*Flagged extension, not core:* particle filtering (several belief states, resampled) hedges against a wrong early commitment, but reintroduces stochasticity against the determinism-on-both-sides selling point. Optional variance-reduction mode, not default.

---

## 5.5 The tuning-features list (FEATURES.md), re-read for a trained model

The FEATURES.md knobs were conceived for a regular prompt-driven LLM, where each is a separate bolt-on trick. In a native model most of them **collapse into three learned primitives** — you don't implement seven features, you train three behaviors and the features fall out. This collapse is itself the result.

**Primitive 1 — a learned read policy (belief-uncertainty × predicted relevance).** In the filtering frame (§5), the belief state's uncertainty over unread regions *is* the signal for where to look next. One policy subsumes four list items:
- *Selective reading* = read where uncertainty × relevance is highest.
- *Pass skipping* = the same policy declining low-value regions — the sublinear schedule the parent already describes, now learned rather than fixed.
- *Reverse reading* = the policy pointed backward: the Bayesian *smoothing* pass (re-observe an earlier region) vs the forward *filtering* pass. This is the strongest form of "late passes revise early conclusions" — not just editing the state, but re-observing the source at finer resolution when a late detail contradicts an early belief.
- *Guided reading* (in part) — an "a launch date is referenced but unresolved" note is just a high-uncertainty belief slot that steers later reads.

**Primitive 2 — the state carries open questions, not only conclusions.** This is the rest of *guided reading*, and it has teeth: the integration state should explicitly hold *unresolved bindings and expectations*, not just settled facts. An open slot "surcharge = table[code] + adder; adder still unknown" that survives from pass 3 until pass 26 fills it is exactly the mechanism the recombination failure needs. Guided reading isn't a feature to add; it's what the state should be.

**Primitive 3 — learned halting (posterior convergence).** *Confidence-based early stoppage* = halt when the belief stops changing across passes, not when the model emits a self-reported confidence number. This fixes what the untrained floor couldn't: P3's confidence sub-arm was inconclusive (emitted on only 4/6 passes). A trained convergence signal is the native version.

Two items stay separate because they genuinely are:
- *Slice overlapping control* is a schedule knob — with the note that a boundary-aware learned compressor can carry cross-slice context *softly* (attention across chunk boundaries), reducing the need for literal token overlap. It's one mitigation for the coarse-to-fine loss you flagged in README (8); boundary-aware compression is the native one.
- *Concurrent prefill* is a systems optimization, not architecture — though the two-tower split makes it cleaner (batch the reader's view-encodes) and opens a *speculative-schedule* variant: a cheap draft refiner proposes edits for several upcoming slices in parallel, a stronger verifier accepts (speculative decoding, applied to passes).

**The new one — content-aware slice size/count — is the most load-bearing addition.** Letting a coherent unit (a code block, an embedded story, a table, a function) be its own slice even if the count rises is the text analog of content-aware segmentation vs a fixed grid. The deep point: **fixed-size slicing manufactures *false* non-locality by cutting naturally-coupled things in half.** Part of P7's split-unit difficulty is exactly that — an arbitrary boundary severed a binding that never had to be distributed. So the division of labor is clean enough to state as a principle:

> Content-aware slicing removes *false* non-locality (artifacts of arbitrary cutting). The integration state carries *true* non-locality (genuinely distributed structure and affect). Don't make the state work to rebind what the slicer never should have split.

This de-risks recombination directly: keep a function with its call site, or a table with its use, in one slice where the source allows, and the binding never needs cross-pass recovery. Prior art for doing it *learned* rather than by hard rules: Meta's Dynamic Large Concept Model (Dec 2025) learns semantic boundaries from latent representations instead of fixed ones — the native form of your feature is a learned segmenter, not a "code blocks are slices" heuristic. Two interactions to design around: variable slice size means the *coupling* (slice size ↔ compression level, M1) must be defined over semantic units, not token counts; and variable slice count means `K` is document-adaptive, which AdaLN handles (`K` is just an input) and which pairs naturally with learned halting.

**The tension to hold, and it's the real cost.** Every adaptive item here — selective reading, pass skipping, reverse reading, halting, adaptive `K` — trades away the *deterministic schedule*, which the parent proposal treats as a core virtue (determinism on both sides, unlike LCM). The resolution: keep a deterministic schedule as a **floor** (guaranteed eventual coverage = the recoverability guarantee), and let the learned policy *prioritize within budget* and choose *sublinear skips* above that floor. Determinism for the guarantee; learned policy for efficiency. In a regular LLM these were free bolt-ons; natively they interact with the one property you least want to lose, so they belong *above* a guaranteed floor, not instead of it.

---

## 5.6 The compressor: the forward process, and an end-product lever (not a PoC concern)

`C(x, σ)` is treated almost as a given elsewhere in this doc, which understates it. The compressor **is the forward (noise) process** — the length-reducing semantic compression that is DiSCo's one claimed-novel axis. In ordinary diffusion the forward process is fixed and information-preserving (Gaussian); here it is **lossy and semantic**, so what it discards at each σ sets what any pass can *ever* contribute from that view. That makes it the single component that can silently cap the system's ceiling.

**But it is not the PoC blocker, and the data says so.** In P4 the compressor did its job — every planted fact *reached a view*; the failures were downstream (integration, retention, recombination). So the compressor is the **ceiling-setter and the end-product optimization frontier, not the thing that is currently broken.** Sequence accordingly: **skip it for the PoC / native build**, and treat it as where you go for optimality once the refiner works. Polishing the input while the failure lives in the integration is misdirected effort.

**Separable as a module, not as an objective.** You can build, freeze, and swap the compressor — the repo's freeze-and-swap discipline is correct engineering. But "good compression" is only definable relative to the reader: it means *preserve what a careful reader carries forward at each level* — the same relevance variable `Y` as the integration state (§5). Encoder and decoder are separate modules with a *joint* optimum, so you **co-design the compressor to the reader's needs even if you do not co-train them.** A generic summarizer is suboptimal because its target isn't the reader's relevance class.

**The forcing-line boundary (§9).** Reader-*aware* compression is legitimate; probe-*aware* compression is cheating. The target is the relevance **class** — general structural and affective importance in this document class — not the answer to a specific probe. That is why an off-the-shelf summarizer leaves performance on the table *and* "tune the compressor to keep the test answer" is overfitting: the optimum sits between, which is what makes the probe-blind discipline right rather than merely cautious.

**Two quality axes, not one.** (1) *What survives to each level* — relevance. (2) *Consistency across levels* — the σ-high coarse view must be a **faithful abstraction** of the σ=0 verbatim, not a divergent one. If the coarse summary misleads, the reader builds a wrong scaffold early and may not repair it even when the verbatim arrives late (the P1 "scaffold collapse" smell). Content-aware slicing (§5.5) is part of the second axis — honest boundaries are what let a coarse view abstract a *unit* instead of a *fragment*.

**Its optimal limit is §6.** Pushed to the frontier, the best compressor is not a better text summarizer — it is a learned latent multi-resolution encoder (the ICAE / AutoCompressor / Dynamic-LCM family). But that *is* the latent-views move: **compression optimization and the latent-views quarantine are one axis viewed from two ends.** A text compressor keeps the flat-source-on-disk audit guarantee; a latent one is more optimal and less inspectable. So "how hard do I optimize the compressor" and "how much auditability will I spend" are the *same dial* — which caps compressor ambition at the recoverability line unless you have decided to trade it. For an end product that decision is live; for the PoC it does not arise, because you are not optimizing the compressor yet.

---

## 6. The move to quarantine: latent views

Making the **views** latent (soft tokens instead of natural-language summaries) is the one move that attacks the proposal's own foundations: it kills the audit trail, weakens the "ground truth is flat text on disk, re-read verbatim" recoverability guarantee, and walks into "isn't this just ICAE / AutoCompressor / Meta-LCM with a schedule?" Keep it an *optional efficiency variant* with a dual-rail mitigation (compute over latents, keep text as ground truth, decode back for the log). Do not claim a σ-conditioned variable-rate encoder as clearly novel.

## 7. Borrowable machinery, labeled honestly

- **Diffusion Forcing** — per-position variable noise *intensity at constant length*. DiSCo's distinguishing axis is *length reduction*. It gives the easy half of the mixed-resolution view, not the novel half. Cite for "variable per-slice conditioning is trainable," nothing more.
- **Mixture-of-Recursions / MoD / PonderNet** — halting/router machinery for learned adaptive scheduling (the confidence-based early exit). But MoR deepens compute on the *same* input; a DiSCo pass ingests a *new view*. Borrow the halting head, not the "passes = recursion depth" identity.
- **Recurrent-depth latent reasoning (Geiping), COCONUT** — evidence that iterating in latent space without emitting tokens works. Support for the latent state, not components to copy.
- **State Stream Transformer, Liger** — cheap conversion paths to give an existing model a latent state carrier without training from scratch.

## 8. Prior art new to the report

Threats to keep in the "why this isn't X" file (latent-view / compression neighbors): **ICAE**, **AutoCompressor** (recursive summary vectors — closest compression neighbor), **Meta Large Concept Model** (SONAR sentence-embedding reasoning — and the name collision: the report's "LCM" is Ehrlich & Blackman's engine, the field's "LCM" is Meta's concept model; disambiguate).

Corroborating / borrowable: **Cartridges** (+ at-Scale, Still), **Titans**, **RMT**, **Mixture-of-Recursions**, self-correcting/remasking diffusion LMs (**ReMDM/RemeDi/Corrective DLMs**), **BD3-LM / Fast-dLLM v2**, and **IB-for-LLMs / QUITO-X** for §5.

July-2026 additions (Boz's search; none touch the novel cell): **Dreamer** (2601.21582, depth-recurrent attention mixtures) — borrowable for §3's bounded pass-history attention; **Mural** (2606.29013, frozen LLM + diffusion via shared attention) — corroborates the §4 two-tower split, cross-domain; **SharpMoE** (2606.26938, saliency routing for diffusion MoE) — image-domain, belongs in the saturated D1/§5C routing bucket, no claim impact. And for content-aware slicing (§5.5): **Dynamic Large Concept Model** (Dec 2025) — learned semantic boundaries.

**DiffusionBlocks** (Shing et al., Sakana AI, 2506.14202) — reinterprets network *depth* as a denoising process (residual updates ≈ dynamical-system steps), so blocks train independently via score matching and match end-to-end training across five transformer families. Not prior art (training procedure, not reading), but the strongest available support for PCT's training economics: it demonstrates, on a second axis (depth, vs. our passes), the same stage-wise-independence property of denoising processes that lets pass tuples `(k, K, v_k, s_{k-1}, e_k)` be trained independently — the answer to the "don't you need credit assignment through the whole schedule?" objection. Borrow the principle, not the machinery (score matching on continuous activations does not transfer to discrete edit ops).

## 9. What this costs (honest scope)

A custom model was always the target here, so — contra some earlier framing — this does **not** "trade away" an off-the-shelf-deployability virtue. That was never on the ledger; it's an AI-introduced framing, not the author's goal. The untrained-floor runs (P1–P7, and the nuance test below) are **diagnostics that de-risk the build, not a product path.** The real costs sit elsewhere and are real: training compute, synthetic data generation, and expertise the program doesn't yet have; and — because everything now rides on the trained model, with no "at least it works today" fallback — the live risk that the **architecture**, not merely the untrained floor, is what fails. That makes the kill-criterion discipline for the trained model matter *more*, not less (it is the antidote to the "→ E2′ will fix it" shield the program already worries about). Beyond that: native latent state is less inspectable than a text buffer (mitigate by decoding slots for the audit log); the bounded-state assumption is unchanged; joint training risks cold-start drift (freeze the reader first); the IB objective needs a practical surrogate (context-distillation KL against the teacher's answer distribution); and the §5c forcing-line risk is real — a surprise/relevance write rule must target document-class-general importance, not probe answers.

## 10. Sequencing

1. **Validate the value, untrained, before building anything** — the non-local nuance experiment (separate note). This is the test the README promises and the repo never ran, and it needs no training.
2. **AdaLN pass-conditioning** on a small refiner over existing teacher trajectories (§2) — cheapest native win, attacks the P2/P3 gap directly.
3. **Latent content-addressed relational state** (§3) — re-pose P7; this is the sharpest test of whether "native" beats "bolted-on" on the retention and recombination joints the data actually found.
4. Two-tower split (§4), then latent views (§6) last and optional.

*Deferred to end-product, not PoC:* compressor optimization (§5.6). Coverage already works (P4: every fact reached a view); the blocker is integration, so a better compressor is optimality-later, not blocker-now. It becomes central only once the refiner is solid and the auditability trade in §6 is on the table.

The through-line: the native moves that are safest to build are also the ones that attack the exact failure joints the program's own experiments surfaced — retention (content-addressed writes), recombination (relational storage), and position-appropriate behavior (AdaLN).

---

*Prior-art claims are from a July 2026 sweep and are not guaranteed comprehensive. Re-check any "novel"/"closest" judgment before it enters a proposal.*
