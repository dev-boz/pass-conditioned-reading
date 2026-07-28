agy-opus4.6

  1. Most likely fatal flaw not named above. (Confidence: high)

  Training–inference distribution shift on state size. The pre-reg specifies  seq_len=10,240  for training, and the D34 length gate drops rows exceeding it. But teacher
  trajectories use K=8–20 passes over 10–34K-token documents — teacher states at close are small (a few hundred tokens). At inference the fixture runs K=31 passes, and the student
  accumulates ~7,700-token states (~116 entries). The model has never seen a training example where the state constitutes the majority of its context. The close phase — which is
  structurally a retrieval-then-compose task over a ~7.7K-token flat list — is a task the model was never actually trained on at that length. This isn't just "1.5B is small"; the
  training data systematically underrepresents the exact condition being tested. You named the scale confound and the teacher confound but not this state-length OOD confound,
  which could fully explain the close failure independent of model capacity.

  2. Top 3 levers. (Confidence: med)



  1. (3) Data-before-instructions prompt order + retrain with larger-state teacher rows — the Google "data-first" finding is real (Hsieh et al., 2024 positional bias in ICL), and
  you can simultaneously fix the state-length OOD problem by generating teacher trajectories with K≥25 and larger final states. One retrain addresses two failure modes. Zero new
  teacher spend only if you keep current K; you probably shouldn't.
  2. (9) Scale 1.5B→3B — the GATE-3 seeded-compose diagnostic at 1/10 on an 8-entry state is damning. This is a 2-operand lookup+add; 1.5B models empirically struggle with multi-
  hop arithmetic in context (cf. Dziri et al., "Faith and Fate" 2023 showing compositional reasoning degrades sharply below ~7B). 3B plausibly crosses the threshold.
  3. (12) Run M-NL now — it's inference-only, tests the actual goal, and if the student passes M-NL while failing the chain gate, it reframes the whole project. Cheapest
  information gain on whether you're testing the right thing.

  3. All-or-nothing table recording: data problem, objective, grammar, or architecture? (Confidence: med)

  Most likely a data problem. The teacher (Haiku 4.5) decides what to record; the student imitates the teacher. If the teacher, prompted with need-class framing (no hint to record
  tables), consistently either transcribes entire tables or summarizes them, the student learns that policy. The 24-op cap is just barely sufficient for a 24-entry table (one ADD
  per entry, zero other ops), making partial transcription mechanically impossible if any ops are spent elsewhere. Cheapest discriminating test: inspect the 277 teacher
  trajectories for any pass containing a table — does the teacher ever record a partial table (e.g., 5 of 24 rows)? If never, the problem is in the teacher demonstrations. If
  sometimes, it's an objective/grammar issue (the student failed to learn partial recording).

  4. One training run: pick one. (Confidence: med)

  (b) 1.5B re-ordered/re-mixed data, but with a crucial amendment: generate new teacher rows at K≥25 with code-class documents so the teacher builds ~5K+ token states, and render
  in data-first prompt order. This directly addresses the state-length OOD confound (question 1) and the prompt-order lever simultaneously. Option (a) 3B is tempting but doesn't
  fix the training data gap — 3B with the same small-state teacher rows may repeat the close failure. Option (d) is premature — the native architecture is a multi-week build with
  uncertain payoff.

  5. Is ~1/10 clean-state compose at 1.5B a hard floor or trainable? (Confidence: med)

  Plausibly trainable but not obviously so. The task is: scan 8 entries, find a table mapping, find an adder constant, add two 3-digit integers. At 1.5B this is at the edge.
  Qwen2.5-1.5B can do 3-digit addition in isolation (verified in many benchmarks), so the bottleneck is retrieval from 8 entries, not arithmetic. Fine-tuning on explicit "look up
  then compute" examples should lift this. However, "Faith and Fate" (Dziri et al. 2023) and "GSM-Symbolic" (Mirzadeh et al. 2024) show that compositional reasoning in
  transformers degrades with problem depth and model size in ways that resist fine-tuning on the surface task. I lean trainable with targeted data at 8-entry scale, but not at
  116-entry scale without retrieval scaffolding — and 116 entries is what this architecture produces.

  6. Prior art being reinvented or contradicted. (Confidence: high)

  • MemGPT (Packer et al. 2023): nearly identical design — LLM manages its own bounded working memory via explicit read/write operations across pages. Your content-addressed ops
  are a stricter version of their edit primitives. Key difference: MemGPT uses a large model (GPT-4-class) as the controller. Your result is consistent with MemGPT's implicit
  claim that the controller must be capable. This argues for scaling the model before re-engineering the memory.
  • ReadAgent (Lee et al. 2024): gist-then-retrieve multi-pass reading. They found gisting works at 70B+ but degrades at small scale — directly corroborating your finding.
  • Recurrent Memory Transformers (Bulatov et al. 2022, 2024): continuous memory bank across segments, the exact design your DISCO doc proposes. They show gains on long-range
  tasks but require pre-training-time integration, not post-hoc LoRA. This significantly raises the bar for your lever (10).
  • Your design contradicts the emerging consensus that retrieval-augmented approaches (RAPTOR, recursive summarization) outperform fixed-schedule sequential reading for factual
  QA — your protocol forces a fixed schedule with no demand-driven retrieval, which is why the table recording is all-or-nothing.

  7. Cheapest $0 inference-only probe not listed. (Confidence: high)

  State truncation at close. Take the 2 student draws (seeds 2, 5) that held both operands, and run close with the state truncated to the last N entries for decreasing N (116, 80,
  40, 20, 10, 5) — no oracle knowledge needed, just mechanical truncation of the state the model itself built. This isolates the exact state length at which composition breaks,
  for free, on existing weights. If composition works at N=20 but not N=40, the problem is pure retrieval-in-length. If it fails at N=5, the problem is the model itself.

  8. Hallucination check on numbers. (Confidence: med)

  The write-up says "operands lost after recording: 0/10" and "~150 suspicious writes blocked" — this is surprisingly clean and makes the content-addressed guard look perfect. But
  the write-up also says the guard "blocked ~150 suspicious writes across the student arm" while edit-op validity is 0.94–1.00. If 150 ops were blocked across 10 draws × 31 passes
  = 310 pass-invocations at ~7 ops each (~2,170 total ops), that's a ~7% block rate — consistent with 0.94 validity lower bound. The numbers are internally consistent. Nothing
  looks fabricated.

  One mild flag: the distillation probe reports "1/10" but the detailed diagnostics log says seed 2 composed 2353 correctly. The write-up says "it composes 2353 correctly"
  (singular), implying exactly 1 seed. Fine, but the framing "held the answer and could not find/use it" implies all 10 draws held both operands when only 2 did — slightly
  misleading rhetoric, not a data error.

  9. Strongest honest claim today, and what's missing. (Confidence: high)

  Honest claim: "A 1.5B model can be trained to reliably execute a structured multi-pass reading protocol (edit-op validity ~0.97) and build a large integration state over 64K
  tokens, but cannot compose over that state at this scale." What's missing for it to matter: a comparison against a trivial baseline (e.g., map-reduce with the same model, or
  simple RAG-and-merge). Without showing the protocol does something better than naive alternatives, the positive finding (protocol compliance) is an engineering result, not a
  scientific one.

  10. Steelman the kill. (Confidence: high)

  The kill was predictable because: (a) P7 cross-family results showed that even 70B-class models fail to compose at 21/22 rate when holding both operands — this is not a 1.5B
  problem, it's a protocol problem (flat text states defeat LLM retrieval at scale); (b) P4 showed the coupled schedule bought zero recall advantage over a single dense read at
  11× token cost; (c) GATE-3 seeded compose at 1/10 (1.5B) and 4/4 (7B) in P7 proves the compose step is model-scale-dependent, and the pre-registration locked the gate at 1.5B;
  (d) the training data never contains states remotely close to 7.7K tokens, guaranteeing OOD failure at close. The architecture gate was baked in the moment K=31 was chosen for a
  model trained on K≤20, with close-phase composition never stress-tested at the resulting state size.

  Do I buy it? Mostly. Points (a) and (d) are strongest. But point (a) cuts against the architecture and the kill rule — if 70B models also fail compose-over-flat-state, then the
  5/10 bar at 1.5B was never reachable, and the kill says more about the bar than the idea. The state-length OOD confound (d) means the experiment didn't test what it claimed to
  test: it tested a 1.5B model on an out-of-distribution close task, not whether pass-conditioned reading can learn to compose. The kill is procedurally correct but epistemically
  weak — you have not yet tested this architecture with matched training and inference conditions.
  
---

ag-opus-4.6

Fatal flaw not named: the teacher's pass-schedule demonstrations almost certainly show the teacher doing the intended protocol, but the student learns to imitate the output format without learning the underlying function. The teacher (Claude Haiku) is a strong model that likely resolves the task internally, then writes a post-hoc transcript that looks like it followed the protocol. The 1.5B student sees a sequence of tokens where "look at compressed view → write things in state" correlates with being a capable model, but the causal link is broken. The student learns to perform the ritual (emit ADD/REPLACE with plausible-looking content) without the cognition. This explains why the student is active (7.0 ops/pass, large state) yet functionally blind (all-or-nothing table copy, fabricated statistics). You're training a smaller model to mimic the surface behavior of a larger model's reasoning process, which is the classic failure mode of distillation into capacity-limited students for tasks requiring internal computation.

Top 3 levers, ranked:

(10) Native architecture (latent slot-bank): The padded probe proves the bottleneck is attention-based retrieval over a large key-value soup in a 1.5B model, not a protocol design flaw. A latent memory bypasses text-based self-attention entirely; this is the only lever that attacks the dissociation directly.
(9) Scale 1.5B→3B: The clean-state 1/10 and the 1.5B model's inability to compose two numbers in 116-entry state is a hard capability floor for multi-hop reasoning over distractors at this scale; 3B may cross the threshold where the architecture's theoretical merit can actually manifest.
(4/5) Selective/guided reading (combined): These are the only levers that shrink the integration state size before the composition step, which the padded probe shows is the critical variable; they attack the distraction problem at input time rather than hoping the model can ignore noise later.
All-or-nothing recording cause and cheapest discriminator test: Most likely an objective + data interaction. The teacher demonstrations likely always record full tables when a table is deemed relevant (a rational behavior for a capable model), so the student has zero examples of selective row extraction. The student then learns "table present → copy all" as the only valid action in the objective space. Cheapest discriminator test ($0, inference-only): Prompt the untrained base model with a single example of the RECORD pass containing exactly one row from a small table, and ask it to complete the next step. If the base model also tries to copy all rows when shown a full table but can copy one when shown one, the student's all-or-nothing behavior is purely a distillation artifact, not an architecture limit. If the base model itself refuses to do partial copies, it's a fundamental objective mis-specification.

Pick one training run: (a) 3B same data. The padded probe is dispositive: the model held both operands in 2/10 draws and failed to compose them. The 1.5B model fails the core primitive (two-number addition from a moderately long state) under any condition except the tiny cleaned state. That's a capability floor, not a data problem. Spending a run on 3B tests whether this architecture ever works for this base primitive. If 3B fails clean-state compose >5/10, the entire text-state paradigm is dead and we move to native architecture. If it succeeds, everything else becomes a refinement problem. Re-ordered data and selective reading are optimization levers for a system that already works; the system doesn't work.

Hard capability floor vs trainable: Hard capability floor for this class of model. Evidence: Qwen2.5-1.5B is an open-weights model with known weak multi-hop reasoning. Multi-hop arithmetic over context requires: (1) locating two fact-bearing entities among distractors, (2) binding them to a computational operation, and (3) executing that operation without confounding. Prior work (e.g., "Lost in the Middle" and multi-hop QA benchmarks on 1–3B models) shows that step (1) alone degrades sharply with distractor count at this scale. The padded probe confirms this: the model can do (3) when (1) is trivial (2-entity clean state), but collapses when 116 filler entries exist. This is the classic small-model retrieval head capacity limit: the model's attention cannot maintain distinct bindings for >O(10) key-value pairs simultaneously. This is not a training problem you can fix by showing more examples of retrieval success; the success doesn't exist in the capacity envelope.

Prior art we are reinventing or contradicting:

MemWalker (Chen et al., 2024): Tree-structured recurrent reading of long documents with a maintained memory. Direct precedent for "multi-pass with state." Contradiction: they show tree-based pruning works at 7B; this work tries a fixed linear schedule at 1.5B and discovers that without pruning (selective reading), the memory is too large for the model to use.
Recurrent Memory Transformers (Bulatov et al., 2022): Use learned memory tokens as a recurrent state across segments. This project reinvents this with text entries, and the padded probe shows why that's inferior: text entries compete for attention; memory tokens don't.
RAPTOR (Sarthi et al., 2024): Recursive abstraction of documents into a tree summary; QA uses top-down retrieval. The "compressed passes → verbatim" schedule is a flat version of this. What changes: RAPTOR uses a dedicated retrieval step; this project expects the model itself to handle retrieval implicitly via self-attention, which is what fails at 1.5B.
ReAct / Self-Ask (Yao et al., 2023): This project reinvents interleaved reasoning and retrieval but without letting the model ask questions during reading; it only lets it write state. The failure to compose suggests the model needs a retrieval query step to use its own state, which the protocol forbids (answer from state alone, no re-reading).
Key takeaway: The protocol is missing an explicit retrieval-from-state step before composition. All working systems decouple the "store" and "retrieve" operations; this protocol merges them into attention, which is capacity-limited.
Cheapest $0 probe (not listed): Run the student model with the same final state from the 2/10 "both operands" draws, but append the question at the top of the context instead of the bottom, with the state below it. The current protocol has question-after-state, which means the question is the last thing the model attends to, and all the garbage state entries are between the question and the answer (the model has to attend backwards over distractors). If flipping the order (question first) gets composition >0, the problem is not retrieval capacity but position bias in Qwen2.5's RoPE: the model loses query fidelity as distance from the state entries grows. This is a known positional failure in smaller models (attention fades at long distances from the target).

Hallucination check:

The all-or-nothing property ("every table is either transcribed in full (24/24 pairs) or not at all") across 10 draws is internally consistent but too extreme to be sampling noise (10 draws, random seed, temp 0.7). If the model had a 50% chance per row of copying a table, you'd expect partial copies. This implies a deterministic branching: the model decides "this is a table I am recording" (copies all 24) vs "this is not" (copies none). This is consistent with the teacher's behavior pattern but worth verifying: are the 3/10 draws where "full mapping recorded" the same seeds as the 2/10 "both operands in state at close"? If yes, those 2 successful state completions came from the 3 recordings, meaning 1 recording was lost (mapping recorded but not retained to close), which contradicts the clean RETAIN claim. Check if seeds 3 mapping-recording draws map onto the 2 operand-at-close draws.
"Close returns 2353" is 0/10 for student, but the temp-0 anchor is reported separately and not shown. This is a gap: if temp-0 anchor also fails, it confirms the model has no path to success; if it succeeds, the 0/10 at temp 0.7 is an exploration failure, not a capability failure. The anchor result should be shown.
Strongest honest claim and what's missing: Claim: "A 1.5B model can be trained to execute a multi-pass reading protocol with content-addressed memory operations, maintaining a state of ~116 entries with 0.94–1.00 edit-op validity across 31 scheduled passes, and no stored information is ever lost to clobbering (RETAIN is perfect)." What's missing: The model cannot use that state for any computational task. Perfect retention with zero utility is a sharp demonstration that text-state memory is a decoy proxy for a real cognitive architecture, but the project needs at least one end-to-end success on a non-trivial compose to make that claim interesting to anyone. Without that, the claim is "we built a very reliable write-only memory," which is a non-result for the target community.

Steelman the kill and my buy-in: A small (1.5B) dense model has no room to learn a full operating system protocol (compression, record, retain, compose) from a few thousand heterogeneous teacher traces distilled from a much larger teacher. The student sees a 31-step action sequence and must learn which parts of its state to write to, when to compress, and how to later compose. This is a sequence length of ~24k tokens of causal LM with sparse supervision (only the final answer is rewarded implicitly via teacher matching). The student's capacity is already saturated learning the surface grammar of passes and edit ops, leaving no representational capacity for the semantic content of what to record. The 1/10 clean-state compose confirms the base model can't even do the arithmetic primitive. The architecture was always going to fail: a 1.5B model is a brittle testbed for an architecture that fundamentally requires robust multi-hop reasoning over dense state. Do I buy this steelman? Mostly yes, but with one reservation. The steelman predicts the student cannot format-comply, which it mostly can't (6/10 no ANSWER line), and cannot compose, which it definitely cannot (1/10 clean, 0/10 full). But the 1/10 clean-state compose means the model has the arithmetic circuit; it's being suppressed by length. The steelman is right that 1.5B is too small, but wrong about why: the failure isn't learning the protocol, it's retrieving two specific numbers from a moderately long state, a parametric attention bottleneck, not a learning problem. The steelman would have the model produce garbage at all state sizes; it actually succeeds at tiny state. So the kill is valid (1.5B is too small), but the diagnosis (couldn't learn the protocol) is wrong; the problem is architectural deployment (text-state is too large for 1.5B's retrieval).

---

deepseek-4-flash-oc

1. Most likely fatal flaw not named — the teacher objective mismatch. The 5,730 training rows are behavioral clones of Claude Haiku 4.5 emitting edit ops under the same schedule at low effort (teacher config: effort: low). The student learns token-level output patterns, not schedule-conditioned strategy. This is why it fabricates statistics (it copies the shape of a summary the teacher wrote without understanding the content) and why RECORD is all-or-nothing (the teacher transcribes tables fully or skips them; the student copies that binary, never selecting one row). The P-C agreement bar (0.75) measures whether the student's op type matches the teacher's, not whether the student achieves the same outcome. The student could pass P-C while learning nothing about global strategy. Confidence: high.
 2. Top 3 levers: (9) scale 1.5B→3B — GATE-3 clean-state compose at 1.5B is 1/10; you cannot train your way around a model-capacity ceiling on the central operation. (3) recording-pass prompt order — data→instructions ordering (untested, $0 floor probe, then re-render existing teacher rows) directly targets the "fabricated summary" pattern because data-before-instructions gives the model concrete content before it decides what to record. (4) selective reading — smaller, relevant state at close attacks both the all-or-nothing record problem and the length-sensitive compose dissociation simultaneously, without retraining. Confidence: high.
 3. Objective problem (with data as the mechanism). The teacher's demonstrations are all-or-nothing per table because the teacher decides table-level importance, not row-level. The student inherits this as a binary behavior. Cheapest discriminator: grep the 5,730 teacher training rows for cases where the teacher recorded a single row of a multi-row table (a partial-table ADD). If zero such cases exist in teacher data, the student can't learn single-row recording regardless of architecture. This costs $0. Confidence: high.
 4. (a) 3B same data. The compose ceiling is the binding constraint across every result. GATE-3 (1/10 at 1.5B), the padded probe (0/10 at full length even with neutral distractors), and the cross-family result (21/22 both-operands-held → no compose at 70B) all converge: compose fails in text-state format regardless of scale, but at 1.5B it fails additionally because the model is too small to find and bind two numbers in ~7.7K tokens. Scaling first tests the separable hypothesis before you add confounds. If 3B lifts GATE-3 from 1/10 to, say, 3/10, you learn something. If it stays 1/10, the representation is the problem and you pivot to native architecture. Confidence: high.
 5. Hard floor, not trainable at 1.5B. Evidence: (a) Llama-70B with 10/10 RECORD and 10/10 RETAIN composes at 1/10 on the same chain; (b) Mistral-24B with 5/5 RETAIN composes at 1/10; (c) the cross-family combined rate across all models holding both operands is ~2/42. Multi-hop arithmetic over self-generated text in a flat format does not scale with training at 1.5B because the retrieval step (find 988 and 1365 among 7.7K tokens) is an in-context search problem that small models demonstrably fail — see "lost in the middle" (Liu et al. 2023), which shows middle-position recall degrades sharply at 1.5B scale even for direct (non-self-generated) text. Confidence: high.
 6. You are reinventing Recurrent Memory Transformers (RMT, Bulatov et al. 2022) with a text-based external memory instead of learned memory representations, which is strictly worse — the cross-family data proves it (70B can't compose from text state). You contradict the "lost in the middle" finding (Liu et al. 2023) by assuming the model can retrieve from its own ~7.7K output, which is harder than retrieval from source text. You are implicitly testing against Unlimiformer (Bertsch et al. 2024) and MemGPT (Packer et al. 2023) without citing them as baselines — both describe bounded-state approaches with explicit retrieval mechanisms. The relevant finding: the cross-family compose rate (~2/42) is essentially the same as the random-guess rate for a 4-digit number, which changes what is worth testing — you should compare against a trivial baseline (does the dense truncation arm, which can't even see both fragments, produce 2353 at the same rate?). Confidence: high.
 7. Double the op cap to 48 and rerun the student (same seeds, inference-only). The student hits 7.0 applied ops/pass against a 24-op cap. If the cap constrains the model's ability to emit fine-grained table rows (it records the table name at 7/10 but the mapping at only 3/10), a higher cap should raise RECORD without any training. If RECORD doesn't budge, the bottleneck is genuinely the model's behavior policy, not the budget. This tests a design parameter inherited from P6 that was never independently validated for the trained student. Confidence: medium (the mechanism is plausible but may be wrong — the issue could be op-type preference, not budget).
 8. The "lost after recording: 0/10" number is misleading. 3/10 student draws recorded the mapping at some pass; 2/10 retained it at close. That means 1 of 3 draws did lose a recorded mapping. The document frames this as "nothing recorded was ever lost" by using a binary "any draw lost anything" flag, but the 1/3 per-draw loss rate is non-trivial. Also: the scorer was corrected 4× mid-run, and the paraphrase fix (23: 988 → 23→988) would have manufactured a 0/10 verdict into a measurement bug that happens to still read 0/10 after correction. "The answer is 0/10 either way" is true but the mechanism changed from record-blocked to compose-blocked — the attribution was wrong mid-run, and the document treats this as "we caught it" rather than "our instrument was unreliable." Confidence: high.
 9. Strongest honest claim: "A content-addressed edit-op guard prevents clobber loss in a multi-pass reading protocol at 1.5B, but the text-state format imposes a retrieval ceiling invariant up to 70B parameters." Missing for it to matter: a same-framework positive result at any scale where compose works (7B+ with the same harness), showing the ceiling is rate-limiting rather than absolute. Without this, the claim is a negative result on an architecture the field hasn't asked for. One cross-family compose count at 7B Qwen (1/10 or better) on the same guard+format would establish the gate was a 1.5B artifact. Confidence: high.
10. Steelman: The cross-family data (21/22 compose failure at 70B, 1/10 at 24B, 0/10 at GPT-4-mini) was already collected before the Stage A run. This data shows that even at 70B with perfect RECORD/RETAIN (10/10), compose fires at ~5%. The task is not a model-capacity problem — it's a representation problem. The text serialization flattens 23→988 + 1365 + compute_line_surcharge(region) = table[region] + adder into prose that the model must re-parse, find two numbers among thousands of tokens, and add them — all while being told "answer from your state, the source is gone." A 1.5B was never going to solve a task where 70B models get 1/10. The gate was a foregone conclusion: the only unknown was whether RECORD would be the bottleneck (it wasn't — training moved it to 2/10) or COMPOSE (it was — the cross-family already showed this). Do I buy it? Yes, mostly. The cross-family compose rate (~2/42 across all models holding both operands) is the single most important number in the entire project record, and it was collected before the Stage A training run. A properly rigorous gate would have used the cross-family compose rate (not the 7B's P7 GATE-3 4/4) to set the student bar. Running a 1.5B training run against a task where 70B gets 1/10 was a predictable waste. The only charitable reading is that the cross-family compose rate measures full-chain (recorded in-schedule, not seeded), and the Stage A clean-state GATE-3 was meant to test the pure compose ceiling — but GATE-3 returned 1/10, consistent with the cross-family. Confidence: high.

---

minimax-m3-fb

1. Fatal flaw NOT named (confidence: high). Training corpus density on the probe's distribution. 5,730 rows from 277 docs is dominated by prose + generic code; teachers rarely transcribe multi-entry integer tables word-for-word because few training docs contain tables. The teacher signal on "record this whole table because it's the answer" is extrapolated, not distribution-grounded. Symptom: student 7/10 names the table (relevance learned) but only 3/10 transcribes it (table-record signal is a weak generalisation, not a learned target). This is the gap the meatspace 1/10 GATE-3 number points at.
2. Top 3 levers (confidence: med-high).
- (8) Composition-focused training mix. Re-render a small block of teacher rows that explicitly demonstrate close composition (state holds X and Y; emit SUM). ~200 added rows, $0 new teacher spend. Direct GATE-3 attacker; if compose rises, training is the lever; if not, model-size floor confirmed.
- (4) Selective reading. Directly attacks the padded-probe distractor finding (wrong-table rows get pulled at close). Bigger harness change; would need its own pre-reg under the program's discipline.
- (3) Re-ordered teacher rows (data-before-prompts). Cheapest test floor-first ($0); if it moves even the untrained floor compose rate, prompt order is materially implicated.
3. All-or-nothing table recording (confidence: high). Objective problem. GATE-3 with eight-entry clean state + explicit "derive arithmetically" permission returns 1/10 student, 0/10 floor — that rules out grammar and largely rules out the text-state surface. The training objective optimises imitating teacher edit ops; the teacher's close behaviour is "carry structure," not "stab a numeric answer." Zero compute gradient flows through composition. Cheapest discriminating test: freeze the student, give it a single context window holding only  988 ,  1365 , and the call site — no state, no schedule — and ask for  compute_line_surcharge(23) . >90% → training target. <90% → model-size floor. ~3 minutes, frozen weights.
4. One training run (confidence: high). (d) No training — build M-NL first, then native architecture. The criterion §3 names ≤1/10 as "no further training spend on this instantiation"; (a) and (b) retrain on this instantiation and violate single-retry discipline. (c) requires a fresh pre-reg for the harness change and doesn't address the model-size floor the GATE-3 clean-state probe already localised. (d) is the criterion's named fallback: build M-NL (inference-only, $0 API, tests the actual stated goal), then — if M-NL shows the goal is even reachable at small scale — move to the native architecture (latent relational state + AdaLN + content-aware slicing), which dissolves the edit-sequence entirely and is the criterion's pre-named §3 endgame.
5. Clean-state compose at 1.5B — hard floor or trainable (confidence: med). Hard floor for general multi-hop numeric composition over context at 1.5B; narrow trainable. Small LMs are documented at 20–50% on MMLU-style numeric context tasks; the padded probe is a smoking gun that length itself kills composition at 1.5B. Targeted numeric-composition fine-tuning has shown it's a learnable but narrow distribution in the FLAN/T5-era literature. The training mix has zero arithmetic-composition signal at close. Architecture is not at fault; capability is the rate-limiter; that capability is recoverable only with targeted data.
6. Prior art reinvented or contradicted (confidence: high).
- MemGPT (2023) — virtual context with text-state edit ops is the same design.
- Recurrent Memory Transformers (Bulatov 2022) — sub-1B recurrent segment memory pretraining.
- RAPTOR (2020) — coarse-to-fine hierarchical reading with explicit pass count is RAPTOR with a position channel.
- MemGPT/RMT papers' published failure rates at small scale match this 0/10 — both reported small-context backbones underperforming until end-to-end memory-aware fine-tune.
- Most damaging omission in your narrative: SESSION-4-CLOSEOUT reports the chain fires on Qwen-72B (s2), Meta-Llama-70B (s9), and Mistral-24B (s42) — 3/22 from your own cross-family battery. The program never re-tests any of those under the strict Stage-A harness. Re-running chain on Qwen-72B under strict guards is the experiment that arbitrates between "model-size floor" and "architecture gate." Until then, the 0/10 at 1.5B is consistent with both stories.
7. Cheapest $0 inference-only probe not listed (confidence: high). Verbatim-only probe — feed the trained student the full table + adder + call site in one context window, no surrounding codebase, no state, no schedule, no edit grammar; ask  compute_line_surcharge(23) . If it passes here but fails GATE-3 on the 8-entry clean state, the architecture's state/schedule overhead is hurting, and dense single-pass is better at 1.5B. If it also fails, the chain failure is the model, not the architecture, and the next move is (a). Frozen weights, 3 minutes, no API, no edits.
8. Hallucination / inconsistency check (confidence: med-high).
- 60% of trained student closings never emit the required  ANSWER:  line. That's instruction-following, not commerce. The 0/10 headline flatlines a failure mode at the protocol level that argues the student never fully learned the close-time procedure. The verdict's binary denominator hides it.
- Teacher's true chain record rate is unreported. "20 hand-audited teacher trajectories" is underpowered to characterise teacher's chain pass rate. If teacher itself only records at ~30–50% the student absorption rate of 3/10 may already be near teacher's ceiling — and no training run fixes it.
- K mismatch. Inference runs at K=31 (6 compressed + 25 verbatim); training was rendered at K≈8–16. The student never saw a pass-position near its close regime under training. This is a regime-distribution miss independent of the data-density issue in Q1.
9. Strongest honest claim today (confidence: high). "At 1.5B on ~5,730 teacher-rendered rows, LoRA fine-tuning teaches the student to execute the edit protocol — held-out syntactic validity 0.94–1.00, op-type agreement 0.76 — but multi-hop numeric composition over context remains below 1.5B's capability floor, independent of the pass-conditioned architecture. The training moves every component metric except end-to-end compose." Missing: one end-to-end success at any scale, under the strict Stage-A harness, ideally a re-test of one of the cross-family composers on the same chain fixture. Until the chain fires even once in the strict regime, the architecture is a hypothesis, not an empirical result.
10. Steelman the kill, then honest read (confidence: high). Steelman: 1.5B was always the wrong test substrate. The text-state + edit-op DSL asks the student to scribe a 24-entry integer table word-for-word and then perform multi-hop numeric binding — a 7B+ pretraining habit on a 1.5B that fails to follow close-time instructions in 60% of draws. The 5,730-row corpus has few table-bearing demonstrations, so the teacher's signal on table-record fidelity is weakly extrapolated. Any replica trained on this scale, this corpus, this objective would land identically. Buy? ~80%. The 20% I withhold: the untrained same-base floor is also 0/10, and SESSION-4-CLOSEOUT records 3/22 successful composes on Qwen-72B / Llama-70B / Mistral-24B using the same fixture family. The architecture did fire at scale; the Stage-A instantiation hit a model-size floor, not an architecture floor. The criterion's verdict is correct for "stop spending on this instantiation"; it is not established for "this approach cannot work at any scale." Don't let the discipline-true verdict drift into the stronger claim it doesn't license.

---

gemini-3.1-pro-agy

  1. High. The most likely fatal flaw is a fundamental misalignment between the training objective (general document compression) and the evaluation task (exact-match database
  lookup). You trained a summarizer via Haiku 4.5 on "unrelated documents", but are testing it on needle-in-a-haystack retrieval in a synthetic codebase. Because the teacher did
  not know the future probe question, it could not demonstrate the highly specific, anticipatory extraction of row 23. The student simply learned to take generic notes, making it
  useless for highly specific trivia probes.
  2. High.

  • (8) Composition-focused training mix: The 1.5B model fails to compose even in an 8-entry clean state; it mathematically cannot succeed at a 116-entry state without explicit
  training to ignore distractors during the CLOSE phase.
  • (4) Selective reading: Since state length alone kills composition (as proven by your padded probe), strictly bottlenecking state size is mandatory for a 1.5B model's limited
  attention capacity.
  • (3) Recording-pass prompt order: At a cost of $0 and zero new teacher spend, this is the cheapest immediate lever to test if instruction adherence can be improved before
  overhauling the architecture.

  3. High. It is a data problem. The teacher (Haiku 4.5) did not know the specific probe question during its reading passes. Without foresight, it had no reason to selectively
  extract the single 23: 988 mapping. It likely demonstrated either summarizing the entire table or block-copying it intact, which the student perfectly cloned.
  Cheapest test: Grep the 5,730 training rows for any instance of a partial dictionary or isolated key-value pair being selectively extracted. If none exist, the student simply
  learned the teacher's block-copy behavior.
  4. High. (b) 1.5B re-ordered/re-mixed data.
  Justification: The 8-entry clean state failing at 1/10 and the padded probe failing at 0/10 prove the model lacks the fundamental ability to reliably compose two facts in the
  presence of even minimal length or distractors. Scaling to 3B (a) or changing the architecture (d) avoids the root cause. You must fix the training mix to explicitly demonstrate
  2-hop retrieval and arithmetic within the CLOSE phase to establish a true baseline before abandoning the 1.5B scale.
  5. High. It is plausibly trainable, not a hard capability floor. Literature on small models (e.g., Phi-1.5, TinyStories) demonstrates that <2B models can perform multi-hop logic
  and arithmetic if trained on dense, high-quality synthetic data specific to the task. The 1/10 performance is an artifact of your LoRA tuning lacking explicit demonstrations of
  step-by-step routing through the generated state during the CLOSE phase, resulting in diffuse and misdirected attention.
  6. Medium. You are reinventing MemGPT (bounded context updated via edit ops) and Self-Notes / RAG-over-own-notes (iterative reading and writing). However, you are directly
  contradicting the Chain-of-Thought (CoT) literature. Your CLOSE phase demands the model implicitly locate two separate state entries and compose them in one forward pass. Prior
  art insists small models must externalize their retrieval (e.g., explicitly quoting source entries) before computing the answer. This dictates that you must test an explicitly
  forced CoT during the CLOSE phase.
  7. High. Run the CLOSE phase on the 8-entry clean state with a forced Chain-of-Thought prefix. Instead of letting the model freely generate its answer, pre-fill the assistant's
  response with: Thinking: To find the surcharge for region 23, I first need to look up the region table.... This tests whether the composition failure is due to a true lack of
  computational depth (which CoT fixes) or catastrophic forgetting of the context.
  8. High. The Distillation probe results are internally inconsistent. You claim that filtering the state to "just the 2 entries holding the operands" allowed it to correctly
  compose 2353. However, to know that the operands should be added, the model requires the function definition (compute_line_surcharge(region) = table[region] + adder). If the
  filtered state strictly contained only the two operand entries, the function definition was excluded, making it impossible for the model to know it should add 988 and 1365
  rather than multiply or subtract them. Either one of those two entries was a massive code block containing the function definition, or this probe result is a hallucination.
  9. High.
  Strongest honest claim: "A 1.5B model can be pass-conditioned to reliably execute a strict content-addressed edit grammar (0.94+ validity) to iteratively compress a 64k-token
  document into a bounded text state."
  What is missing: Functional utility. The resulting state is unreadable by the model itself during the final QA phase, making the entire compression exercise useless for actual
  reasoning or downstream tasks.
  10. High.
  Steelman: This instantiation was predictably doomed because it attempted to solve a semantic routing problem via behavioral cloning of syntactic operations. The student learned
  how to emit edit ops from a teacher that was blindly taking general notes, but never learned why to take them. A 1.5B model lacks the zero-shot reasoning to anticipate what a
  future probe might ask, and its attention mechanism is too weak to perform implicit multi-hop retrieval over a 116-entry state without end-to-end task optimization linking the
  final answer back to the reading passes.
  Do I buy it? Yes. Behavioral cloning of a generic reading protocol is fundamentally broken for small models. Small models require task-aware gradients (e.g., RL or QA-driven
  objectives) propagating from a final correct answer back to the intermediate reading passes to establish intent and focus.
  
---

laguna-m.1-kc

1. Fatal flaw (high confidence). The all-or-nothing recording behavior stems from a training objective mismatch. The teacher demonstrates full-table transcription as the response to "build a comprehensive analytical brief" — it has no incentive to extract only relevant rows. The student learns this all-or-nothing pattern, which works for the ~1K token prose views but fails catastrophically on 7K+ token code chunks where the op cap (24) truncates the table. The cheapest fix: check if teacher trajectories show similar truncation patterns (they won't be truncated in training since seq_len=10240), but if they do, the student is learning corrupted data. The real problem: the objective "integrate this view's content" doesn't distinguish "integrate what's relevant to the user's eventual questions" from "integrate everything you see."
2. Top 3 levers (medium confidence). 
- (9) Scale 1.5B→3B: The padded-probe shows length kills composition at 1.5B; scale is the cleanest lever if the hardware supports it.
- (3) Recording-pass prompt order: Data-before-prompt may reduce the all-or-nothing tendency by making the state more salient, testable at $0 with frozen weights.
- (10) Native architecture: The edit-sequence is fundamentally incompatible with the 1.5B's retrieval limitations; a latent slot bank with AdaLN injection would collapse the long-context retrieval problem into the model's internal attention.
3. All-or-nothing table recording (high confidence). Most likely an objective problem — the rubric "integrate this view's content; consolidate overlapping entries; keep the state within budget" doesn't encode selectivity. When the model sees a large table, it either transcribes all or abstracts it. The cheapest discriminator: run the teacher on the fixture and check if its raw output shows selective row extraction vs full transcription. If teacher transcribes fully, it's an objective flaw; if it extracts selectively, it's student overfitting.
4. Spend one training run on (d) — no training, build M-NL or native architecture. The chain gate is 0/10 on both arms with a clean retention mechanism. Throwing another training run at 1.5B when the PADDED PROBE shows 0/10 compose even with operands visible and in-position is irrational. The bottleneck is architectural (length-dependent retrieval), not training. M-NL would at least test the actual goal (nuance preservation) rather than this failed trivia proxy. If M-NL also fails, native architecture is the only coherent next step.
5. Clean-state compose at ~1/10 (medium confidence). This looks like a hard capability floor, not plausibly trainable. Small models (1-2B) consistently fail multi-hop arithmetic when operands are embedded in text (the padded-probe confirms this). The model can do arithmetic (GATE-3 shows 1/10 correct), but retrieval from ~7K tokens of state overwhelms it. Qwen 2.5 72B or a model with strong interpolation abilities would be needed to train through this, not 1.5B. The architecture should make operands FINDABLE (structured slots) rather than hoping scale fixes it.
6. Prior art contradicted. You're reinventing MemGPT-style state management (memory pressure forcing eviction) and recurrent memory transformers (the idea of iterative state refinement). But these works preserve recency or use write-protected memory slots. MemGPT's LRU eviction and hierarchical memory are more principled than your all-or-nothing compression. More critically, RAG over own notes approaches (like REACT agents) keep retrievable embeddings rather than relying on text-anchored attention. Your text-state approach loses to these because embeddings preserve similarity structure; your state is just more context for the model to attend over.
7. Cheapest $0 probe. Run the P7 fixture at temp=0 with the 1.5B GGUF but give it an ADDITIONAL pass after the final state: FINAL STATE + QUESTION + "Your answer must be a single integer." where the question is placed BEFORE the state (contradicting your data-first order) and the instruction explicitly constrains format. This tests whether the model can parse its own state under any conditions, without any training changes.
8. Hallucination check (medium confidence). The statement that "6/10 student closings never emitted ANSWER: <integer>" seems suspect. If the scoring requires this format and it's missing in 60% of cases, either (a) the model wasn't trained on closing-format examples, or (b) the 1.5B has fundamental format compliance issues. Also suspicious: the padded probe shows "wrong answers migrate onto the correct table (86→988)" — this suggests value matching is happening but on wrong rows, which means the 1.5B IS retrieving but with poor binding. This is more severe than the report implies.
9. Strongest honest claim (medium confidence). That edit-op syntax with content-addressing prevents id-misaddressing clobber (RETAIN works). But what's missing for this to matter: any demonstration that the model can actually USE recorded facts to answer questions. The chain gate measured retention correctly but never validated composition — the model just fails to sum two visible numbers in long contexts. A working chain needs both.
10. Steelman the kill (high confidence). This was never going to work because: (1) the 1.5B scale cannot retrieve two operands across ~7K token state (padded-probe proves this); (2) the all-or-nothing recording means the model can't selectively accumulate relevant facts; (3) the architecture forces the model to perform multi-hop arithmetic in attention rather than in external memory. These are fundamental limitations, not bugs. Do I buy this? Partially. I buy the scale argument (length-dependent retrieval failure) and the objective argument (training doesn't teach selectivity). But I don't buy that "coupled schedule is dead" — a native architecture with proper memory slots could salvage the core insight that coarse-to-fine reading is valuable. The current instantiation just can't execute it.

---

composer-2.5-cursor

  1. Closing was trained weakly and never gated. Train data has 277 closing rows, but pc_check.py explicitly drops stage != "closing" from the health check — so the only skill the
     verdict requires (compose/format from state) was never a pass bar. Co-fatal and unnamed: query-blind need-class recording makes “keep the one relevant row” underdetermined at
     READ time, so all-or-nothing / fabricated ranges are the rational policy under your own forcing boundary. (high)

  2. (4) selective reading — only lever that can shrink ~7.7k distractor states into the regime where distilled compose already works. (8) composition mix — attacks GATE-3’s ~1/10
     clean-state ceiling and the unvalidated closing objective. (9) 3B — needed if length-sensitive two-operand binding is a capacity wall, not just a data wall. (Kill or defer (3)
     until a floor probe shows signal; (10) only after text-state levers plateau.) (high)

  3. Mostly objective + data, secondarily op-grammar. Teacher demos + SFT reward whole-entry dumps and lossy summaries; the grammar cannot express “ADD row 23 only”; architecture
     (flat state) is what kills CLOSE, not RECORD. Cheapest discriminator: score teacher trajectories on how often tables are full-transcribed vs one-row vs range-summary; then
     force the student (frozen) on a single verbatim table tile and count the same three modes — if teacher never one-rows, it’s data; if teacher one-rows but student can’t emit
     it, grammar/objective; if both can but only dump 24/24 under need-class K-schedule, architecture/protocol. (high)

  4. (b). One run should fix the actual training hole (closing excluded from health; compose barely supervised) and can re-render order/mix from existing 5,730 rows at zero teacher
     cost. (a) confounds scale with the same broken objective. (c) is a harness change — prove it $0 on frozen weights before burning a run. (d) M-NL doesn’t fix the measured
     joints; native is too big for an expertise-limited one-run bet. (med)

  5. Plausibly trainable for short/clean state; hard floor for long flat state at 1.5B. Distilled 2-line → 2353 proves arithmetic+binding work; GATE-3 1/10 and padded 0/10 show
     failure is retrieval/binding under length, matching small-model collapse on multi-hop / “needle + reason” suites (RULER-style, lost-in-the-middle), not inability to add
     988+1365. (med)

  6. Closest priors: MemGPT / Letta (paged text OS memory + tools), ReadAgent (gist memories + lookup), AutoCompressors / summary-state agents, RAPTOR / map-reduce QA, RMT /
     Memorizing Transformers (learned recurrent memory). You reinvent MemGPT-style notes without a retrieval API over them, then ask a 1.5B to do the retrieve+join in-context. That
     shifts worth-testing toward: explicit retrieve-over-state, teacher ceiling on the fixture, and whether latent slots beat text notes — not more prompt-order microtweaks. (high)

  7. Teacher ceiling on the frozen fixture: run Haiku (same protocol, need-class, K=31) end-to-end and score RECORD/RETAIN/COMPOSE. If the teacher fails selective RECORD, the gate
     was never a student/scale question. (Runner already exists; API cost is small — if “$0” is strict: compose-vs-state-length curve on frozen student with synthetic states of
     size 2…128 burying the two operands.) (high)

  8. Inconsistencies: (i) Gauntlet says no draw “ends holding a linked 23→988 pair”; RESULTS/ANALYSIS say seeds 2 and 5 held both at close — the RESULTS wording is about no lenient
     success, the gauntlet misstates it. (ii) “~150” guard blocks vs archived 144+93+7+2=246 (only ~153 if redirects excluded — say so). (iii) Live runner flags still wrong on seed
     2 (queried_mapping: false) while analysis says true — instrument debt, not just historical. (iv) Distillation narrative (“seed 2 → 2353”) vs table 1/10 is fine only if you
     state seed 5 stays broken; easy to misread as “always works when distilled.” (high)

  9. Honest claim: pass-conditioned LoRA on 1.5B measurably improves protocol following and partial RECORD vs the same base (7.0 vs 2.4 ops/pass; 3/10 vs 0/10 mapping; RETAIN 0
     losses under strict guards), but does not produce end-to-end cross-tile compose on this concession fixture. Missing for anyone else to care: a capable-model (teacher) or
     larger-student ceiling on the same fixture, or a goal-aligned M-NL result — otherwise it’s “small model fails hard multi-hop over self-notes,” which is not news. (high)

  10. Steelman: With query-blind recording, whole-entry ops, flat growing notes, no closing health bar, and a 1.5B asked to bind two buried numbers amid decoys after 31 passes,
      0/10 was the prior. Distillation/GATE-3 make that prediction sharper a priori. Do I buy it? Mostly yes on this instantiation; not as a kill of “scheduled multi-pass reading”
      in general — training moved every component except the conjunction, and RETAIN worked. The gate correctly killed this text-op stack at 1.5B; it did not entitle a claim that
      the parent idea is dead. (high)
	  
---

mimo-2.5-oc

1. Most likely unnamed fatal flaw: The closing prompt at inference is distributionally shifted from training. The student was trained on simple closings (CLOSING_SYSTEM + "Task: {closing_demand}" — a general analytical brief demand) but at inference gets an extended CLOSE_SYSTEM (with explicit arithmetic-permission and ANSWER: <integer> format) plus a specific question. The student never saw this format in its ~5,730 training rows. Evidence: 6/10 student closings never emitted the required ANSWER line — direct signal that the format is out-of-distribution. The project names "format compliance" as weak but doesn't attribute it to this specific distribution shift between the teacher training rows and the inference close. (Confidence: med — the shifted prompt includes helpful instructions that should assist, not hurt, so the shift alone may not be fatal, but combined with 1.5B scale it likely matters.)
2. Top 3 levers, ranked:
(a) Latent relational state (native architecture, #10): The 21/22 recombination failure across 70B/24B/7B models is the single strongest signal in the data. Text-state edit ops strip relational binding by construction. A latent slot-bank with content-addressed writes and relational storage is the only lever that attacks the demonstrated bottleneck structurally rather than at the margins.
(b) Composition-focused training mix (#8): The current teacher trajectories almost certainly contain zero examples of arithmetic-over-state composition (the teacher wrote general briefs on unrelated documents). Synthetic training rows that demonstrate "find two values in state, combine them arithmetically at close" would teach the one skill the chain gate actually requires. This is cheap (generate ~200 targeted teacher rows) and directly addresses the composition gap.
(c) Scale 1.5B→3B (#9): GATE-3 seeded compose is 1/10 at 1.5B; the cross-family data shows 70B models compose at ~1/10 too, but with much better RECORD/RETAIN rates. Scale won't fix recombination alone but may lift the composition floor enough for training to gain traction.
3. All-or-nothing table recording: Most likely an op-grammar problem. The grammar provides ADD END: <text> (append raw text) — there is no op for "extract entry 23 from this table." The teacher either copies the full table verbatim (when the view makes it salient) or records a compressed summary (when it doesn't). The grammar lacks a selective-extraction primitive, so all-or-nothing is the only behavior the format supports. Cheapest discriminating test: prompt the untrained floor with "record ONLY entries relevant to cross-module arithmetic" — if selective recording appears, it's grammar/prompt, not architecture. If it doesn't, it's capability. (Confidence: med.)
4. One training run: (b) 1.5B re-ordered/re-mixed data. The prompt-order fix (data before instructions) is $0 to validate on the untrained floor first. If it helps, re-rendering the existing 5,730 teacher rows in the new order costs zero additional teacher API spend. If it doesn't help, you've burned no teacher budget and gained a clean null. This dominates (a) because 3B alone won't fix recombination (the cross-family data shows 70B models fail there too), and dominates (c) and (d) because it's the cheapest way to rule in/out a $0 prompt-order confound before committing to a more expensive change.
5. ~1/10 clean-state compose at 1.5B — hard floor or trainable? Plausibly trainable for the specific arithmetic case, but the cross-family data (21/22 both-operands-held seeds fail to sum across Llama-70B, GPT-4o-mini, Nova) suggests relational binding in text-state systems is genuinely hard, not just a 1.5B ceiling. The 1.5B rate (1/10) is actually higher than the cross-family average (~1/22 ≈ 4.5%), which is surprising and may be noise. Honest assessment: the text-state edit-op format likely has a low ceiling on recombination at any scale; the specific arithmetic case might be trainable to ~3-5/10 with targeted data, but the general relational binding problem probably requires the latent-state architecture to solve reliably. (Confidence: low on the specific number, med on the directional claim.)
6. Prior art being reinvented or contradicted:
- MemGPT (Packer et al. 2023): bounded state + edit operations for in-context learning. DiSCo's closest architectural cousin; the key difference is the coarse-to-fine schedule (MemGPT manages a flat memory tier, not compressed views).
- Titans (2024): surprise-gated memory writes — the relevance mechanism the project needs but doesn't have. The "surprise" signal could replace the salience gap the data shows.
- ICAE / AutoCompressor: learned compression vectors — what DiSCo's latent-state variant (§6) becomes. The project acknowledges this but quarantines it.
- RAPTOR: hierarchical summarization — what coarse passes approximate. DiSCo claims the schedule adds value over flat summarization; P4's tie with dense head+tail contradicts this for recall.
- Map-reduce QA: DiSCo improves on this by maintaining cross-chunk state, but the 21/22 recombination failure means the state doesn't carry binding — so it may not actually improve on map-reduce for the composition task.
- RMT / Recurrent Memory Transformers: persistent latent memory across steps — the native architecture's state bank. DiSCo's text-state version is a degraded instance.
7. Cheapest $0 inference-only probe not listed: Run the untrained floor with the training-time closing prompt (simple CLOSING_SYSTEM + "Task: {closing_demand}") instead of the inference-time closing. If the floor composes better with the prompt it was actually trained on, the closing distribution shift is a measured confound. This is a one-line config change, runs in minutes on existing hardware, and directly tests the hypothesis from Q1.
8. Hallucination check: The "21/22" recombination denominator is drawn from llama/gpt/nova families, while the existence proof cites Qwen-72B, Llama-70B, and Mistral-24B — different populations overlapping only at Llama-70B seed 9. The numbers are internally consistent (the doc notes this) but the denominator switch across sections is easy to misread as contradictory. The 12-entry CARRIER_FUEL_BP decoy table is mentioned as "planted" but never appears in any scoring — its presence in the fixture is asserted but unverified in the files I read. No other numeric inconsistency found; the arithmetic (988+1365=2353) is correct.
9. Strongest honest claim: "Pass-conditioned reading with text-state edit ops fails the chain gate at 1.5B (0/10); the composition step is the demonstrated bottleneck across model families (21/22); the architecture is not unfeasible (3-family existence proof at n=1 each) but this instantiation is gated." What's missing for this to matter: any test of the actual goal (nuance→decision, not arithmetic). Without M-NL or a similar goal-aligned test, the claim is about edit-op mechanics, not about whether coarse-to-fine reading preserves the kind of understanding the project sets out to preserve. The strongest claim the project could make today is about the recombination bottleneck — that's a genuine empirical finding across families — but it doesn't vindicate or kill the architecture's purpose.
10. Steelman the kill: (a) 1.5B can't compose from seeded state (GATE-3 1/10); (b) 70B models barely compose either (1/10 Llama, 1/10 Mistral, 0/10 GPT-4o-mini); (c) the training data never demonstrates the target skill; (d) the closing prompt is distributionally shifted from training; (e) text-state edit ops strip relational binding by construction, so the architecture can't carry the one thing the chain gate requires. I buy (a)-(c) and (e) strongly. I partially buy (d) — it's fixable, but at 1.5B it may not matter even if fixed. The steelman convincingly kills this instantiation (text-state edit ops at 1.5B on this training data). It does not kill the architecture in the abstract — the latent-state native design (§3) specifically addresses (e), and the cross-family existence proof shows the chain can fire. The steelman is strongest on the claim that spending another training run on this instantiation is wasted money, and weakest on the claim that the idea is dead.

---

glm-5-kiro

 1. Most likely fatal flaw NOT named: The training objective is misaligned with the chain requirement. The student imitates teacher edit operations (ε-prediction), not the state the
  operations produce (x̂₀-prediction). This means the model learns "how to emit ADD/REPLACE" without a gradient signal toward "what state enables downstream composition." The
  padded-probe finding — that operands exist but cannot be retrieved from a long state — directly reflects this: the teacher's edit sequence is followed, but no training signal
  enforces retrievability. The native architecture doc's §5 diagnosis is correct: "path-independent training toward s*" would require a continuous state, which text forecloses.
  Medium confidence.
  2. Top 3 levers:
    - (10) Native architecture — The padded/distilled dissociation proves retrieval in a flat 7.7K-token text state is structurally broken at 1.5B; latent content-addressed slots
  with relational bindings attack both the clobber problem (solved by the guard) and the recombination problem (unsolved).
    - (9) Scale 1.5B→3B — GATE-3 shows clean-state compose at ~1/10 at 1.5B; this is the cheapest way to discriminate "architecture wrong" from "model too small," and the results doc
  explicitly flags this as the gray-zone retry that 0/10 forecloses.
    - (3) Recording-pass prompt order — $0 to test on floor, re-render existing training rows for $0 teacher spend; directly attacks the all-or-nothing recording by changing what the
  model sees first.

  3. All-or-nothing table recording: an op-grammar problem masked as a data problem. The grammar forces whole-entry edits (ADD/REPLACE <id>: <text>); partial-row recording is
  syntactically impossible. A teacher cannot demonstrate recording a single 23:988 row from a 24-entry table without recording all 23 other rows first — the granularity is hardcoded.
  Cheapest discriminative test: give the untrained floor a hand-crafted single-row prompt ("Record only entry 23 from the table") and verify it cannot comply syntactically,
  confirming grammar limitation rather than training data. High confidence.
  4. One training run: (d) no training — build M-NL. The architecture gate says "stop spending training runs on this instantiation." The 0/10 means no retry is licensed under the
  pre-registered rules. M-NL tests the actual goal (nuance preservation) with frozen weights, costs $0, and either (a) validates the student is useful for the stated purpose despite
  failing the concession test, or (b) confirms the architecture gate extends to the goal. This is the only move that respects the discipline without burning the single allowed run on
  a gated instantiation. High confidence.
  5. ~1/10 clean-state compose at 1.5B: evidence of a hard floor, but not conclusive. Small models (<3B) struggle with multi-step reasoning over long context even when the steps are
  explicit — the "lost in the middle" phenomenon and attention sink work show this. However, Qwen2.5-1.5B can perform simple addition when both operands are in its training
  distribution and context is short. The 1/10 suggests: (a) the two-operand retrieval-plus-arithmetic combination is near ceiling, and (b) no amount of recording improvement lifts
  the product above 0 until compose improves. Whether it is trainable at 1.5B is unknown; the GATE-3 0→1 improvement suggests it responds to training but saturates fast. Medium
  confidence.
  6. Prior art:
    - MemGPT / stateful agents — Maintain explicit state updated via tool calls. DiSCo differs: scheduled passes rather than agentic autonomy, but shares the "state as integration
  medium" premise. The retrieval failure here suggests MemGPT-style text state hits the same limit at small scale.
    - Recurrent Memory Transformers (RMT) — Fixed-size memory slots passed across segments. DiSCo's state is analogous, but RMT trains the memory read/write end-to-end rather than
  through discrete edit ops. The all-or-nothing recording suggests RMT's continuous memory is better for partial extraction.
    - RAPTOR / hierarchical summarization — Builds a tree, queries it. DiSCo integrates into a flat state, losing the tree's addressability. The retrieval failure suggests
  hierarchical indexing matters.
    - Map-reduce QA — Parallel processing, merge results. DiSCo is sequential with state persistence, enabling cross-pass integration that map-reduce forecloses.

     What changes: the retrieval failure suggests text state without indexing is insufficient; hierarchical (RAPTOR) or latent (RMT) state should be tested.

  7. Cheapest $0 inference-only probe not listed: Run the floor model on a synthetic 2-table, 2-addend, 2-function fixture where the chain requires selecting one of each based on a
  shared key (e.g., compute_surcharge(23) uses table A, compute_fee(23) uses table B). This isolates whether the retrieval failure is (a) distractor-sensitive, (b) key-dependent, or
  (c) a general binding deficit. Same hardware, same frozen weights, just a new prompt/fixture. High confidence this is novel.
  8. Hallucination check: three concerns.
    - The 4× scoring corrections — The paraphrase-matcher bug would have manufactured the exact 0/10 verdict if uncorrected. This is disclosed and addressed, but raises the question:
  what other silent bugs remain? The runner's colon-only matcher is kept "on purpose" for hash consistency — this is defensible but fragile.
    - The 7.0 vs 2.4 ops-applied gap — The student emits more ops and has higher validity, yet achieves 0/10 on the end-to-end chain. This is internally consistent (ops ≠ chain
  success) but the magnitude of improvement without any end-to-end transfer is striking.
    - The "nothing recorded was ever lost" claim — The guard fired 246 times on the student (144 quote-mismatch + 93 redirect + 7 repurpose + 2 guard). If the guard is preventing
  data loss, this is working as intended. But the claim "zero recorded operands were lost" depends on the scoring logic being correct; the 4× corrections suggest scorer fragility.
  Medium confidence on consistency; low confidence on scorer correctness.

  9. Strongest honest claim: Training improves protocol-following, recording, and retention, but the text-state edit-op instantiation gates at 1.5B on end-to-end chain composition
  due to retrieval and granularity failures. What is missing: a demonstration that any alternative instantiation (native architecture, larger model, or different state
  representation) clears the chain gate. Without that, the claim is a negative result on one configuration, which matters only if it guides the next configuration to test. The M-NL
  goal-aligned test could provide that guidance.
  10. Steelman the kill: A 1.5B model with 24K context cannot reliably retrieve and compose two specific values from a 7.7K-token self-generated state when the question is provided
  after the state. This is predictable from known small-model limitations: (a) attention degradation over long sequences ("lost in the middle"), (b) no architectural mechanism for
  content-addressable retrieval in text, (c) the edit-op grammar forces whole-table or nothing recording. The padded/distilled probe confirms: length kills composition, distractors
  misdirect retrieval. No amount of training on edit-op imitation can overcome a retrieval architecture that does not exist. Do I buy it? Partially. The steelman is strong on the
  retrieval/granularity analysis but weak on the scale confound — 3B might clear it, and the experiment was not run. The architecture is gated at 1.5B, but the verdict says "this
  instantiation" and the steelman overgeneralizes to "all instantiations." The distinction matters for where to spend next. Medium confidence.
  
---

devin-SWE-1.6-dc

  1. Most likely fatal flaw NOT named: Training objective mismatch. You train to imitate teacher edit-ops (ε-style), but the native architecture doc argues x̂₀-style (train toward
  teacher's state, not its brushstrokes) is path-independent and denser. This brittleness could explain why the student learns protocol-following (7.0 vs 2.4 ops/pass) but fails the
  chain — it learned the wrong proxy objective. This is named in DISCO-NATIVE-ARCHITECTURE.md but not listed as a known weakness in your results doc. (confidence: high)
  2. Top 3 levers: (1) Scale 1.5B→3B — GATE-3 and padded probe both show a 1.5B compose ceiling; this directly tests the length-sensitive joint. (2) Native architecture — padded
  probe proves distractor content kills retrieval in flat text; latent slot bank with content-addressed writes is the designed fix. (3) Selective reading — attacks both RECORD all-
  or-nothing (by reducing what needs recording) and state-size bloat (hits the length joint). (confidence: med)
  3. All-or-nothing recording: DATA problem. The 24/24 or 0/24 pattern suggests teacher demonstrations show either full transcription or nothing; the student imitates this. Cheapest
  test: manually inspect teacher rows on the surcharge-table-bearing passes to see if any demonstrate partial recording. If teacher never shows it, student won't learn it.
  (confidence: high)
  4. One training run: (a) 3B same data. The compose ceiling is the best-diagnosed blocker (GATE-3: 1/10 clean-state; padded: 0/10 at full length). 3B is the cleanest test of whether
  this is scale-bounded. Native architecture (d) is the right endpoint but requires a build before any training. (confidence: med)
  5. ~1/10 clean-state compose: Evidence of a hard capability floor at 1.5B. Small models reliably fail multi-hop reasoning across context; the padded probe (0/10 compose at full
  length, only fires in 2-line state) shows length itself kills two-operand binding. Cite: Liu et al. 2024 "Lost in the Middle" — retrieval degrades with context even for single-hop;
  your probe shows the degradation is worse for binding. (confidence: high)
  6. Prior art: (1) Recurrent Memory Transformers (RMT) — segment-wise recurrence with a memory vector; you differ by coarse-to-fine schedule instead of uniform segmentation. (2)
  MemGPT — hierarchical memory with explicit management; you differ by pass-conditioned automation instead of OS-style scheduler. (3) Map-reduce QA — multi-pass summarization; you
  differ by stateful integration across passes instead of one-shot aggregation. What changes: none test coarse-to-fine scheduling as the primary lever. (confidence: med)
  7. Cheapest $0 inference-only probe: Test lever 3 (data→instructions order on recording passes) on the untrained floor. Run 3-5 seeds, compare RECORD rates vs current instructions-
  first baseline. If signal, it's zero-cost before any retraining. (confidence: high)
  8. Hallucination check: Your op-type agreement 0.761 (bar 0.75) is suspiciously convenient — a 0.011 margin on a 5,730-row training run. If the true agreement were 0.74, run 2
  would have failed P-C and you'd be in a different world. Also, padded probe says "wrong answers migrate onto the correct table" — but you report 0/10 compose overall. How many of
  those 0/10 are "right table wrong row" vs completely unrelated? This conflation masks whether retrieval is partially working. (confidence: med)
  9. Strongest honest claim: Training a 1.5B model to follow a multi-pass reading protocol improves state-building (7.0 vs 2.4 ops/pass, 7.7K vs 0.7K tokens) and recording (7/10 vs
  2/10 table-named), but end-to-end composition remains blocked at this scale. What's missing: a result where the chain actually fires — even once — at trained level. Without that,
  you've demonstrated protocol learning, not the architecture's core claim. (confidence: high)
  10. Steelman the kill: A 1.5B model with a flat text state and whole-entry edit ops was never going to bind two operands across 155 entries at close time. Small models fail
  retrieval in large contexts (known result); your padded probe confirms this structural limitation. The all-or-nothing recording is predicted by whole-entry granularity. The gate
  was predictable a priori. Do I buy it? Partially. The all-or-nothing and retrieval failures were predictable, but you correctly predicted that RETAIN would be clean (and it was).
  The unknown was whether training could overcome the retrieve/compose floor at 1.5B — your test answered that, and the answer is no. The gate was justified. (confidence: med)
  
  ---
  
  sonnet-4.5-kiro
  
   1. Most likely fatal flaw (high confidence): The student never sees examples of successful multi-hop composition during training. Your teacher is Haiku 4.5 executing the protocol
  over 277 documents, but you don't say those documents contained multi-hop retrieval problems that Haiku solved. If the teacher demonstrations are just "record facts, answer
  single-fact questions," the student learns recording and formatting but never the retrieve-compose pattern. The 5,730 rows were leakage-scanned against the fixture but not
  characterized for composition demand. A student can't learn what the teacher never demonstrated.
  2. Top 3 levers (high confidence):
    - (8) Composition-focused training mix: Generate synthetic training pairs where ground-truth requires composing 2-3 state entries, verify teacher solves them, train on those.
  Directly targets the observed failure mode.
    - (3) Data-before-instructions prompt order: Zero-cost floor test ($0), and if it lifts floor performance on any metric, the re-render is free. Google's finding is robust; your
  current order fights established priors.
    - (12) M-NL inference test: Costs nothing, tells you if record/retain already solves something goal-relevant. If the student can't compose but can preserve nuance for softer
  decisions, the killable-proxy test killed the wrong thing.

  3. All-or-nothing recording (medium confidence): Most likely data problem. The teacher saw 277 documents; how many contained 24-entry integer tables? If few/none, the teacher has
  no demonstration of "selectively excerpt one row from a dense table," only "transcribe small config blocks" vs "summarize large ones." The fabricated statistics smell like the
  teacher's own compression behavior being faithfully distilled. Cheapest discriminant: Hand-write 3 single-pass prompts showing a 20-entry table with instruction "record only the
  entry for key 23" → run teacher → if teacher transcribes all 20, it's teacher limitation; if it extracts the one row, it's training-mix underrepresentation.
  4. One training run (medium confidence): (b) 1.5B re-ordered/re-mixed data. Reasoning: You have infrastructure to generate training data (the teacher pipeline). Re-rendering
  existing rows in data-first order is free; generating 500 new composition-demanding rows costs minimal API budget. This tests two high-prior hypotheses (prompt order +
  composition-in-training) without the scale confound and without building unproven infrastructure (selective reading adds harness complexity; 3B might not fit f16; native
  architecture is a research bet). If this fails, the scale confound becomes your top suspect and 3B is next.
  5. ~1/10 clean-state compose (low confidence): probably hard floor at 1.5B, but testable. Negative evidence: 1.5B models typically fail multi-step arithmetic and two-premise
  logical deduction without finetuning on those exact tasks (see BIG-bench "multi_step_arithmetic" and "logical_deduction" benchmarks; <5% for 1.3B-1.6B models). Positive evidence:
  distillation can teach smaller models to mimic larger models' algorithms if training data shows the steps. Your student *can* emit valid edit ops (learned algorithm), suggesting
  trainability. But the padded-probe result (length-preserving but content-neutralized state still fails) suggests working-memory limits, not retrieval. Discriminant: generate 1000
  synthetic "state + question requiring 2-fact composition" examples, finetune 1.5B for 1 epoch, test. If that reaches >50%, it's trainable; if it stays <10%, it's floor.
  6. Prior art (high confidence):
    - Compressive Transformer (Rae et al. 2019): Compressed past activations into memory. Your schedule is their compression at inference time.
    - Memorizing Transformers (Wu et al. 2022): External kNN memory over past states. Your integration state is an editable text-based version.
    - Recurrent Memory Transformer (Bulatov et al. 2022): Recurrent token-based memory. Same motivation, yours uses symbolic ops.
    - MemGPT (Packer et al. 2023): Editable text-based "main context" managed by LLM-generated operations. Your architecture is almost literally MemGPT applied to document reading,
  not chat. This is the closest hit.
    - Lost in the Middle (Liu et al. 2023): Multi-document QA retrieval fails when relevant facts are "lost in the middle" of long context. Your padded probe reproduces this at 7,700
  tokens (much shorter than their 32k-128k tests), suggesting 1.5B makes the phenomenon worse.

     Implication: MemGPT-style state management is validated for chat; your negative result suggests the approach doesn't transfer to dense multi-hop reading at small scale, likely
  because MemGPT's tasks don't require composing facts into novel arithmetic.

  7. Cheapest $0 probe (high confidence): Test floor and student on the existing fixture but with the question injected at an early pass (say pass 15 of 31), not at close. State size
  will be smaller (~3k tok) when the question arrives. If compose rate rises above 0/10, it's a length-at-retrieval problem; if it stays 0/10, the problem is earlier (record or
  retain). Cost: re-run the harness with question timing changed, no new weights, no new data.
  8. Inconsistency check (high confidence):
  - "Operands lost after recording: 0/10" but "both operands in state at close: 2/10." If nothing recorded was ever lost, how did 1 of the 3 draws that recorded the mapping lose it
  by close? Either the "recorded at some pass" scan is overcounting (matching partial transcriptions), or "lost" is undercounting (REPLACE edits that semantically alter the entry),
  or the 3 and 2 are from overlapping-but-not-identical draw sets. Clarify the denominator and the definition of "recorded."
    - Edit-op validity 0.94–1.00 across student draws but "6/10 student closings never emitted the required ANSWER: <integer> line." Format compliance failure at close but not during
  passes suggests close has a different prompt template or the format instruction is pass-specific but not close-specific. Is close actually trained? If the teacher rows are
  pass-level (reading) but not close-level (answering), the student never learned the close format.

  9. Strongest honest claim (medium confidence): "A 1.5B model can be trained to maintain a 100+ entry structured state across 31 scheduled passes over a 64k-token document using
  content-addressed symbolic operations, achieving 94%+ edit validity and zero unforced memory clobbers." What's missing for it to matter: Evidence the state contains anything
  useful. Without a task the state solves (even partially), this is infrastructure without application. Run M-NL or a softer multi-fact QA battery to show the state beats baseline on
  something.
  10. Steelman the kill (high confidence): This was predictable. (1) Small models can't do multi-hop reasoning over context (established BIG-bench results). (2) The teacher (Haiku
  4.5) is weaker than the oracle models in long-context benchmarks; distillation can't exceed teacher capability. (3) The training data is teacher-generated over unrelated documents,
  so the student learns the teacher's behaviors (formatting, recording salient items) but not task-specific retrieval strategies for code or multi-hop composition (those weren't in
  the 277 documents). (4) The test is a worst-case retrieval problem: two facts separated by design, no co-occurrence, embedded in 7,700 tokens—harder than most real-world
  long-context QA. The gate was a capability test for something that wasn't trained or teachable at this scale. Do I buy it? Partially (medium confidence). The test is hard, but the
  padded-probe result (correct composition when given only 2 relevant entries + same-length filler) suggests the architecture could work if recording were selective. The
  all-or-nothing recording is the unforced error; if the teacher demonstrated selective extraction, or if the prompt order were fixed, 2-3/10 seems reachable, enough for a retry. So
  not "never going to work," but "underspecified training data made failure likely."
  
---

qwen-3.8-qoder

   ---

   1. Fatal flaw not named above. (Confidence: high)

   The teacher demonstrations themselves teach the all-or-nothing recording that kills the chain. I inspected stageA_coupled.jsonl: the teacher records full tables verbatim in
   mid-passes (e.g., NOTCH_OFFSETS_1: {14: 149, 15: 430, ...}) then compresses them to range summaries in closing passes (row 3159: {13: 905, 15: 374, ..., 94: 167}). The student is
   faithfully imitating a teacher that demonstrates "transcribe everything or summarize to a range." The training objective has no signal for "record the one row that will matter
   later" because the teacher — which doesn't know the future question — never does that either. This isn't a scale problem or an op-grammar problem; it's that the distillation
   target encodes the exact failure mode you're measuring. You named "teacher confound" generically, but the specific mechanism is: the teacher's closing-pass compression is the
   student's learned default, and no amount of scale fixes a training distribution that never contains the target behavior.

   2. Top 3 levers. (Confidence: med)

   1. New lever: re-train the teacher with question-conditioned recording (or at minimum, add synthetic training rows where the correct behavior is "record one row, not the table").
   The current teacher data is the proximate cause of all-or-nothing recording; no harness change fixes a behavior the student was never shown.
   2. (4) Selective reading — directly attacks state bloat (7.7K→smaller), which the padded probe proved is the compose-killer. Smaller state = closer to the 2-line distilled
   condition where compose fires.
   3. (9) Scale 1.5B→3B — GATE-3 shows compose at 1/10 even clean; this is plausibly a capacity ceiling, not a training gap. Cheapest way to test whether the architecture has any
   viable scale.

   3. All-or-nothing recording: data problem. (Confidence: high)

   It's a data problem. The teacher demonstrations (verified in the JSONL) show exactly two modes: full transcription or range-summary compression. There are zero training rows where
    the teacher records a single relevant row from a larger table. The student cannot learn a behavior absent from its training distribution. Cheapest discriminating test: hand-craft
    20–30 synthetic training rows where the correct completion is ADD END: REGION_SURCHARGE_CENTS[23] = 988 (single-row recording from a visible 24-entry table), fine-tune for 50
   steps, and check whether the student ever emits a single-row recording on the fixture. If it does, the behavior was learnable but undemonstrated. If it doesn't, escalate to
   op-grammar (can't express sub-entry) or architecture.

   4. One training run: (b) 1.5B re-ordered/re-mixed data — but with a critical modification. (Confidence: med)

   Not (b) as stated (just reordering prompts). Spend it on 1.5B with augmented training data that includes single-row recording demonstrations and compose-heavy closing rows.
   Rationale: (a) 3B same data just learns the same wrong behavior at larger scale; (c) harness changes don't fix a missing training signal; (d) M-NL on a model that can't compose is
    measuring nothing. The re-rendering idea is right (zero teacher spend) but you must filter and augment the 5,730 rows: drop closing-pass rows that demonstrate lossy compression,
   add synthetic rows demonstrating selective recording + arithmetic composition. The Google data-before-prompt finding is a secondary benefit, not the main lever.

   5. 1/10 clean-state compose: hard floor or trainable? (Confidence: med)

   Plausibly trainable, but barely. Evidence bearing on this: Qwen2.5-1.5B can do single-step arithmetic (988+1365) reliably in isolation — the failure is binding two operands
   retrieved from context plus executing the operation, a two-hop task. Small-model multi-hop QA literature (e.g., Tang et al. 2023 on multi-hop reasoning in <3B models) shows these
   models fail at entity binding across separated context positions, not at arithmetic per se. The distilled probe (2-line state → correct compose) confirms the arithmetic is intact;
    the binding is what breaks. This is trainable in principle (the model has the components) but the 1/10 rate suggests the binding circuit is barely present at 1.5B. A
   composition-focused training mix with many two-operand examples might push it to 4–5/10, but I'd estimate <30% probability of clearing a ≥5/10 bar at 1.5B. The padded probe (0/10
   at full length even with neutral filler) is the most damning evidence: length itself degrades binding, and that's architectural, not experiential.

   6. Prior art. (Confidence: med)

   - MemGPT (Packer et al. 2023): closest analogue — LLM manages its own context via function calls, paging memory in/out. Your content-addressed edit ops are a more constrained
   version. MemGPT's finding: the model's self-editing reliability is the bottleneck, not the memory structure. This predicts your RETAIN-clean/RECORD-broken split.
   - Map-reduce QA (e.g., LangChain's MapReduceDocumentsChain): your compressed-then-verbatim schedule is a learned version of map-reduce. The known failure: the reduce step (your
   compose) loses information that the map step (your recording) discarded. This is exactly your chain failure.
   - Recurrent Memory Transformer / MemoryLLM (Wang et al. 2024): latent slot-bank memory updated across segments. Your lever (10) native architecture is this. Their finding: latent
   memory outperforms text-state for multi-hop because retrieval is implicit (attention over slots) rather than explicit (scan a flat brief). This directly supports your padded-probe
    finding.
   - RAPTOR (Sarthi et al. 2024): recursive summarization tree for long-doc QA. Contradicts your flat-state design: hierarchical structure enables retrieval that flat lists cannot.
   Your state is a flat numbered list; RAPTOR suggests a tree would fix the retrieval failure.
   - What changes: the prior art says your retrieval failure (flat text, length-sensitive) is predicted and structural, not a training artifact. The native architecture (10) or a
   hierarchical state is the fix the literature points to, not prompt engineering.

   7. Cheapest $0 probe not listed. (Confidence: med)

   State-position randomization at close. Take seed 2's 155-entry state, keep all entries but randomly permute their order (put the operand entries at positions 1 and 2 instead of
   S26 and S83), and re-run the close. This tests whether the failure is positional (the model can't attend to middle-of-document entries — "lost in the middle," Liu et al. 2023) vs.
    content-based (distractor semantics capture retrieval). The padded probe showed distractors matter, but didn't isolate position. If moving the operands to the front fixes compose
    at full length, the fix is a state-ordering policy (most-recently-relevant first), which is a $0 harness change. If it doesn't, the failure is purely semantic distraction and
   only structural changes help.

   8. Hallucination check / internal inconsistency. (Confidence: med)

   Two things look off:

   "operands lost after recording: 0/10" is suspiciously clean. The guard blocked ~150 writes, yet zero recorded operands were ever lost. This is too convenient — it means the guard
   never once false-blocked an operand-bearing entry, despite firing 150 times. Either the guard is perfectly calibrated (unlikely at 1.5B output quality) or the operand entries were
    never targeted by destructive ops (plausible but should be verified: were any of the 150 blocked writes targeting S26 or S83 in seed 2?). If a blocked write would have replaced
   an operand entry with something else, the "0/10 lost" is an artifact of the guard, not a clean retention result.
   The training-health pass margins are razor-thin (validity +0.020, agreement +0.011 over bars). Agreement dipped below 0.75 as late as 200/213 rows. With n=213, the 95% CI on 0.761
    is roughly ±0.057 — meaning the true agreement could be 0.70, below the bar. The pass is statistically fragile. This doesn't invalidate the verdict (0/10 is 0/10 regardless) but
   it means the "training worked" claim is weaker than presented.

   9. Strongest honest claim today. (Confidence: high)

   "We demonstrate that pass-conditioned LoRA training on a 1.5B model produces a categorically stronger protocol-follower (3× op-following, 10× state construction, 3.5× table
   recording) than the untrained base, and that a content-addressed guard achieves perfect retention — but the end-to-end chain fails because (a) the training distribution teaches
   lossy compression, not selective recording, and (b) flat-text state at ~7.5K tokens defeats two-operand binding at 1.5B scale, a failure that is structural (survives prompt
   engineering) and dissociable from arithmetic capability."

   What's missing for it to matter: a single positive existence proof. You have zero draws where the full chain fires. Until you can show even 1/10 on any instantiation (even a 3B
   with augmented data, even a hand-crafted 5-entry state), the architecture is unfalsified-but-undemonstrated. One working example would change the narrative from "interesting
   negative result" to "promising architecture with a solvable bottleneck."

   10. Steelman the kill. (Confidence: high for the steelman, med for whether I buy it)

   The steelman: this instantiation was dead on arrival. A 1.5B model has ~24K context but effective attention over ~2–4K tokens (lost-in-the-middle is well-established at this
   scale). You asked it to maintain a 7.7K-token flat brief and then retrieve two specific entries from 116 to perform arithmetic. The padded probe proved this fails at 1.5B
   regardless of content. The recording failure was equally predictable: the teacher compresses tables (because it doesn't know the future question), so the student learns to
   compress. The op-grammar has no sub-entry operation, so "record one row" requires creating a new entry with just that row — a behavior never demonstrated. Every component failure
   was individually foreseeable from the literature; their conjunction at 0/10 is not surprising. The architecture gate was the predictable outcome of combining a small model, a flat
    state, a lossy teacher, and a granular op vocabulary.

   Do I buy it? Partially. The compose failure at 1.5B was predictable and I buy that fully — the padded probe is conclusive. But the recording failure was not inevitable: the
   teacher data shows full transcription is possible (the student does it 3/10), and the all-or-nothing pattern is a training-distribution artifact, not a capability limit. A teacher
    that demonstrated selective recording, or a training mix with compose-heavy closings, could have moved RECORD from 3/10 to 6–7/10. The gate was predictable for this exact
   configuration, but the configuration had a fixable data problem that a more experienced team would have caught before spending the training run. The architecture isn't proven
   wrong; the instantiation was under-engineered at the data level.
   
---

mimo-2.5-pro-fb

1. Most likely unnamed fatal flaw: the close turn has no training signal. The teacher data consists of  (prompt, edit_ops)  tuples at each pass. The close-turn behavior — "read a large state, retrieve the right entries, perform multi-hop arithmetic, emit  ANSWER: <int> " — is never demonstrated in the training corpus. The student learned the reading protocol (7.0 applied/pass, near teacher parity) but composition at close remained at the base model's baseline (~0–1/10). GATE-3 shows this ceiling is real: even handed a clean 8-entry state, the trained student composes 1/10, indistinguishable from the untrained floor. If the training objective never includes the close turn, the student cannot learn to close, regardless of how well it reads. Every other failure diagnosis assumes the close is trainable from the reading data; this one says it was never in the loss. Confidence: high. Cheapest test: add a small dedicated closing-training split (teacher closes from curated states) and re-run GATE-3.
2. Top 3 levers.
(a) #9 — Scale 1.5B→3B. GATE-3 (1/10 on a clean 8-entry state) identifies compose as the hardest blocked joint; if compose caps at ~10% regardless of state quality, the end-to-end conjunction rounds to zero at any sample size. Only a scale step tests whether this ceiling is parameter-limited or architecture-limited. (b) #4 — Selective reading. Directly attacks both blocked joints: sub-entry, query-guided recording avoids the all-or-nothing failure, and a smaller relevant state at close (~1–2K tok instead of ~7.7K) lives inside the region where the padded probe showed composition works. Can be prototyped inference-only on frozen weights. (c) #10 — Native architecture. The exploration ledger and the padded/distilled probes are the direct evidentiary basis for addressable latent state + AdaLN; this lever is what the gate was designed to license. It attacks both joints at their root rather than mitigating symptoms.
3. All-or-nothing recording is an op-grammar problem masquerading as a data problem. The ADD grammar accepts arbitrary text, so in principle the model could emit  ADD S_new: "23: 988" . But every teacher trajectory for tables either recorded the full table or summarized it — the teacher (Haiku, 200K ctx) had no reason to cherry-pick one row when it could transcribe the whole thing trivially. The student learned exactly what was demonstrated. The grammar permits selective recording; the data never demonstrates it; and the model cannot generalize the pattern from zero examples. Cheapest discriminative test: inject 20 synthetic teacher rows into the training data where the teacher records only the query-relevant row from a table (with a "record only what matters" rubric), retrain on the existing corpus + these rows (a few hours of compute), and measure whether the student's recording behavior shifts from 24/24-or-nothing to selective. If it shifts → data problem confirmed. If it doesn't → the op-grammar's whole-entry framing is load-bearing and the grammar needs sub-entry ops.
4. One training run: (a) 3B same data. The reasoning: the compose joint is the hardest blocked joint, GATE-3 puts its ceiling at ~1/10 even on a clean 8-entry state, and every lever that attacks RECORD (levers 3–5) is wasted if compose stays capped. Scaling to 3B is the only lever that tests whether compose is inherently capped at this architecture or just parameter-limited. If 3B hits 30–50% on GATE-3, the architecture is alive and the next move is recording-focused levers at 3B. If 3B stays at ~1/10, the architecture gate generalizes across scale and the native architecture (lever 10) is the only remaining move. Either answer is decisive. Options (b) and (c) attack the recording joint, which is moot if compose is fundamentally blocked. Option (d) tests a different question (nuance preservation) without resolving the mechanistic question the gate raised. One caveat: verify 3B f16 fits the 1080 Ti (≈6GB model weights + KV cache in 11GB; tight but probably feasible at 24K ctx with quantized KV or reduced ctx).
5. ~1/10 clean-state compose is a soft capability floor, not a hard one — but the gap to "trainable" is large. The padded probe is decisive evidence: at 2 lines (≈50 tokens), compose fires reliably; at 7.7K tokens with neutral filler, it fails completely; even with distractors removed but length preserved, it fails. This is the classic small-model long-context retrieval degradation pattern — consistent with findings from RULER, LongBench, and Needle-in-a-Haystack benchmarks showing 1–3B models degrade sharply past 3–4K tokens on multi-hop retrieval. The 1/10 rate on an 8-entry state (~200 tokens) suggests the model can compose in its comfort zone but the margin is razor-thin. Plausibly trainable to 20–30% with: (a) explicit chain-of-thought decomposition at close ("table[23] = ?; adder = ?; sum = ?"), which was not tested — the "retrieve" probe asked for entry quotation, not arithmetic decomposition; (b) composition-focused training data (lever 8). But 50%+ at 1.5B on a 7.7K-token state is unlikely without a structural change to the state representation. Confidence: medium.
6. Prior art — what's closest and what it changes.
- MemGPT (Packer et al., 2023): hierarchical memory with self-directed retrieval and tool calls. Closest deployment analog; DiSCo's difference is the coarse-to-fine schedule and content-addressed edit ops, not just memory management. MemGPT's failure modes (tool-calling errors, wrong retrieval) parallel DiSCo's close failures, suggesting the retrieval joint is a known hard problem across architectures, not specific to text-state edit ops.
- Recurrent Memory Transformers / RMT (Bulatov et al., 2022–2023): recurrence through special memory tokens across segments. DiSCo's integration state is a text-mode analog of RMT's memory tokens. RMT shows memory tokens degrade over many segments — the same long-horizon retention problem DiSCo's content-addressed guard was built to solve. The comparison matters: if RMT-style latent memory already demonstrated that discrete memory tokens fail at scale, DiSCo's text state is strictly worse.
- Titans (Google, 2025): surprise-gated test-time memory writes. The exploration ledger already cites this. The key insight: surprise-gating is the principled form of relevance-filtered recording. DiSCo's "record everything or nothing" failure is exactly what surprise-gating prevents.
- Map-reduce QA / RAPTOR (Sarthi et al., 2024): recursive tree summarization for RAG. RAPTOR builds a static hierarchy; DiSCo iteratively revises state. RAPTOR's success on multi-hop QA (without iterative revision) suggests that for factoid questions, static summarization may suffice — weakening the case for DiSCo's complexity on the chain-gate's specific task type.
- The critical gap: No prior work that I can identify tests "pass-conditioned training" (telling the model its schedule position) as a distinct mechanism. P2 and P3 in this project's own pilots showed it matters (rubric-conditioned staging). This is the one genuinely novel empirical contribution, and it is untested in the native form (AdaLN vs prompt tokens).
7. Cheapest unlisted $0 inference-only probe: explicit chain-of-thought decomposition at close. The "retrieve" probe asked the model to quote relevant entries before answering (still 0/10). But no probe tested arithmetic decomposition: "Step 1: Find the surcharge for region 23 in your state. Step 2: Find the reconciliation adder. Step 3: Add them." This is different from retrieval — it structures the reasoning, not just the search. On frozen student weights, 10 seeds, costs nothing. If this moves compose from 0/10 to 2–3/10, it means the close failure is a reasoning-structure problem, not a pure capability ceiling, and the next training run should include CoT-formatted closing examples. If still 0/10, compose is genuinely capability-limited at 1.5B.
8. Hallucination check — numbers are internally consistent. I verified: (a) student applied/pass = 7.0 is exact (7.1+8.3+3.7+7.0+7.0+8.0+8.0+6.4+8.3+6.2 = 70.0/10); (b) floor state average = 725 tok is exact (6+875+830+21+1271+23+903+836+645+1841 = 7250/10); (c) guard events (144+93+7+2 = 246 total, ~150 "blocks" excluding redirects — matches the "~150 suspicious writes" claim, with "suspicious" being slightly loose for "blocks + redirects"); (d) 277 docs × ~20.7 passes/doc ≈ 5,730 rows — plausible given the K=8 prose / K=31 code split; (e) dates are chronological. One item worth flagging: the training health bars were close-margin passes — agreement 0.7606 vs bar 0.75 (margin 0.011), validity 0.9699 vs bar 0.95 (margin 0.020). The results doc acknowledges this ("tracked as a close call"). Not inconsistent, but if either bar had been set 0.02 higher, Run 2 would have failed training health too, and the gate would have been "training failure," not "architecture gate." The pre-registered bars themselves are the unexamined assumption — why 0.75 and not 0.80? Confidence: high that the numbers are honest; medium that the bars are well-calibrated.
9. Strongest honest claim + what's missing. "Pass-conditioned training demonstrably moves every measurable component of a multi-pass reading protocol at 1.5B parameters — op-following 3×, table recording 3.5×, state richness 10× — with zero retention failures on content-addressed writes. The end-to-end conjunction fails at this scale because composition from a large self-generated state exceeds the model's retrieval and arithmetic capacity, not because the protocol is unlearnable." What's missing for this to matter: a demonstration that the protocol preserves information a single-pass read would lose on a real document (not a synthetic arithmetic proxy). The M-NL experiment is drafted precisely for this. Without it, the claim is about a protocol's learnability, not its value — and learnability of a protocol that doesn't yet work end-to-end is a finding for the architecture-search community, not for anyone with a document-reading problem.
10. Steelman the kill — this was predictable a priori. Five independent conditions must hold simultaneously for a success: (1) model records the relevant data row from among 24 during a verbatim pass; (2) records the adder from a different module in a different pass; (3) both survive 25 subsequent passes of state editing; (4) model retrieves both from a 7.7K-token self-generated state at close; (5) model performs 988+1365=2353 correctly. Pre-gate estimates for each: recording ≈ 0.2–0.3 (the model must notice one row among thousands of tokens during a verbatim tile), retention ≈ 0.9 (content-addressed guard should help), retrieval ≈ 0.3 (prior art on small-model long-context is discouraging), arithmetic ≈ 0.5 (1.5B models are ~50% on two-operand addition per GSM8K-style data). Joint probability: 0.25 × 0.9 × 0.3 × 0.5 ≈ 0.034. With n=10, P(≥1 success) ≈ 1-(1-0.034)^10 ≈ 29%. P(≥5/10) ≈ 0.0003%. The ≥5/10 threshold was unreachable at plausible per-component rates. A more informative threshold would have been ≥1/10 (any success at all), which had ~30% power under reasonable assumptions. Do I buy it? Mostly. The arithmetic is rough but the direction is right: the conjunction of 4–5 independent sub-50% events will reliably produce zeros in small samples, and the pre-registration set a threshold that required near-perfect component rates. The counter-argument: training moved components substantially (3× op-following, 3.5× recording), so the pre-gate component estimates might have been pessimistic. But GATE-3's 1/10 on compose — the one component training barely moved — anchors the weakest link and dominates the conjunction. The gate was likely to fail; the valuable finding is why it failed (the mechanistic decomposition into RECORD/RETAIN/COMPOSE), not that it failed.

---

deepseek-v4-pro-nim

Fatal flaw not named: the teacher's pass-schedule demonstrations almost certainly show the teacher doing the intended protocol, but the student learns to imitate the output format without learning the underlying function. The teacher (Claude Haiku) is a strong model that likely resolves the task internally, then writes a post-hoc transcript that looks like it followed the protocol. The 1.5B student sees a sequence of tokens where "look at compressed view → write things in state" correlates with being a capable model, but the causal link is broken. The student learns to perform the ritual (emit ADD/REPLACE with plausible-looking content) without the cognition. This explains why the student is active (7.0 ops/pass, large state) yet functionally blind (all-or-nothing table copy, fabricated statistics). You're training a smaller model to mimic the surface behavior of a larger model's reasoning process, which is the classic failure mode of distillation into capacity-limited students for tasks requiring internal computation.

Top 3 levers, ranked:

(10) Native architecture (latent slot-bank): The padded probe proves the bottleneck is attention-based retrieval over a large key-value soup in a 1.5B model, not a protocol design flaw. A latent memory bypasses text-based self-attention entirely; this is the only lever that attacks the dissociation directly.
(9) Scale 1.5B→3B: The clean-state 1/10 and the 1.5B model's inability to compose two numbers in 116-entry state is a hard capability floor for multi-hop reasoning over distractors at this scale; 3B may cross the threshold where the architecture's theoretical merit can actually manifest.
(4/5) Selective/guided reading (combined): These are the only levers that shrink the integration state size before the composition step, which the padded probe shows is the critical variable; they attack the distraction problem at input time rather than hoping the model can ignore noise later.
All-or-nothing recording cause and cheapest discriminator test: Most likely an objective + data interaction. The teacher demonstrations likely always record full tables when a table is deemed relevant (a rational behavior for a capable model), so the student has zero examples of selective row extraction. The student then learns "table present → copy all" as the only valid action in the objective space. Cheapest discriminator test ($0, inference-only): Prompt the untrained base model with a single example of the RECORD pass containing exactly one row from a small table, and ask it to complete the next step. If the base model also tries to copy all rows when shown a full table but can copy one when shown one, the student's all-or-nothing behavior is purely a distillation artifact, not an architecture limit. If the base model itself refuses to do partial copies, it's a fundamental objective mis-specification.

Pick one training run: (a) 3B same data. The padded probe is dispositive: the model held both operands in 2/10 draws and failed to compose them. The 1.5B model fails the core primitive (two-number addition from a moderately long state) under any condition except the tiny cleaned state. That's a capability floor, not a data problem. Spending a run on 3B tests whether this architecture ever works for this base primitive. If 3B fails clean-state compose >5/10, the entire text-state paradigm is dead and we move to native architecture. If it succeeds, everything else becomes a refinement problem. Re-ordered data and selective reading are optimization levers for a system that already works; the system doesn't work.

Hard capability floor vs trainable: Hard capability floor for this class of model. Evidence: Qwen2.5-1.5B is an open-weights model with known weak multi-hop reasoning. Multi-hop arithmetic over context requires: (1) locating two fact-bearing entities among distractors, (2) binding them to a computational operation, and (3) executing that operation without confounding. Prior work (e.g., "Lost in the Middle" and multi-hop QA benchmarks on 1–3B models) shows that step (1) alone degrades sharply with distractor count at this scale. The padded probe confirms this: the model can do (3) when (1) is trivial (2-entity clean state), but collapses when 116 filler entries exist. This is the classic small-model retrieval head capacity limit: the model's attention cannot maintain distinct bindings for >O(10) key-value pairs simultaneously. This is not a training problem you can fix by showing more examples of retrieval success; the success doesn't exist in the capacity envelope.

Prior art we are reinventing or contradicting:

MemWalker (Chen et al., 2024): Tree-structured recurrent reading of long documents with a maintained memory. Direct precedent for "multi-pass with state." Contradiction: they show tree-based pruning works at 7B; this work tries a fixed linear schedule at 1.5B and discovers that without pruning (selective reading), the memory is too large for the model to use.
Recurrent Memory Transformers (Bulatov et al., 2022): Use learned memory tokens as a recurrent state across segments. This project reinvents this with text entries, and the padded probe shows why that's inferior: text entries compete for attention; memory tokens don't.
RAPTOR (Sarthi et al., 2024): Recursive abstraction of documents into a tree summary; QA uses top-down retrieval. The "compressed passes → verbatim" schedule is a flat version of this. What changes: RAPTOR uses a dedicated retrieval step; this project expects the model itself to handle retrieval implicitly via self-attention, which is what fails at 1.5B.
ReAct / Self-Ask (Yao et al., 2023): This project reinvents interleaved reasoning and retrieval but without letting the model ask questions during reading; it only lets it write state. The failure to compose suggests the model needs a retrieval query step to use its own state, which the protocol forbids (answer from state alone, no re-reading).
Key takeaway: The protocol is missing an explicit retrieval-from-state step before composition. All working systems decouple the "store" and "retrieve" operations; this protocol merges them into attention, which is capacity-limited.
Cheapest $0 probe (not listed): Run the student model with the same final state from the 2/10 "both operands" draws, but append the question at the top of the context instead of the bottom, with the state below it. The current protocol has question-after-state, which means the question is the last thing the model attends to, and all the garbage state entries are between the question and the answer (the model has to attend backwards over distractors). If flipping the order (question first) gets composition >0, the problem is not retrieval capacity but position bias in Qwen2.5's RoPE: the model loses query fidelity as distance from the state entries grows. This is a known positional failure in smaller models (attention fades at long distances from the target).

Hallucination check:

The all-or-nothing property ("every table is either transcribed in full (24/24 pairs) or not at all") across 10 draws is internally consistent but too extreme to be sampling noise (10 draws, random seed, temp 0.7). If the model had a 50% chance per row of copying a table, you'd expect partial copies. This implies a deterministic branching: the model decides "this is a table I am recording" (copies all 24) vs "this is not" (copies none). This is consistent with the teacher's behavior pattern but worth verifying: are the 3/10 draws where "full mapping recorded" the same seeds as the 2/10 "both operands in state at close"? If yes, those 2 successful state completions came from the 3 recordings, meaning 1 recording was lost (mapping recorded but not retained to close), which contradicts the clean RETAIN claim. Check if seeds 3 mapping-recording draws map onto the 2 operand-at-close draws.
"Close returns 2353" is 0/10 for student, but the temp-0 anchor is reported separately and not shown. This is a gap: if temp-0 anchor also fails, it confirms the model has no path to success; if it succeeds, the 0/10 at temp 0.7 is an exploration failure, not a capability failure. The anchor result should be shown.
Strongest honest claim and what's missing: Claim: "A 1.5B model can be trained to execute a multi-pass reading protocol with content-addressed memory operations, maintaining a state of ~116 entries with 0.94–1.00 edit-op validity across 31 scheduled passes, and no stored information is ever lost to clobbering (RETAIN is perfect)." What's missing: The model cannot use that state for any computational task. Perfect retention with zero utility is a sharp demonstration that text-state memory is a decoy proxy for a real cognitive architecture, but the project needs at least one end-to-end success on a non-trivial compose to make that claim interesting to anyone. Without that, the claim is "we built a very reliable write-only memory," which is a non-result for the target community.

Steelman the kill and my buy-in: A small (1.5B) dense model has no room to learn a full operating system protocol (compression, record, retain, compose) from a few thousand heterogeneous teacher traces distilled from a much larger teacher. The student sees a 31-step action sequence and must learn which parts of its state to write to, when to compress, and how to later compose. This is a sequence length of ~24k tokens of causal LM with sparse supervision (only the final answer is rewarded implicitly via teacher matching). The student's capacity is already saturated learning the surface grammar of passes and edit ops, leaving no representational capacity for the semantic content of what to record. The 1/10 clean-state compose confirms the base model can't even do the arithmetic primitive. The architecture was always going to fail: a 1.5B model is a brittle testbed for an architecture that fundamentally requires robust multi-hop reasoning over dense state. Do I buy this steelman? Mostly yes, but with one reservation. The steelman predicts the student cannot format-comply, which it mostly can't (6/10 no ANSWER line), and cannot compose, which it definitely cannot (1/10 clean, 0/10 full). But the 1/10 clean-state compose means the model has the arithmetic circuit; it's being suppressed by length. The steelman is right that 1.5B is too small, but wrong about why: the failure isn't learning the protocol, it's retrieving two specific numbers from a moderately long state, a parametric attention bottleneck, not a learning problem. The steelman would have the model produce garbage at all state sizes; it actually succeeds at tiny state. So the kill is valid (1.5B is too small), but the diagnosis (couldn't learn the protocol) is wrong; the problem is architectural deployment (text-state is too large for 1.5B's retrieval).

---

glm-5.2-nim

Fatal flaw: The 24-op cap per pass directly forces the all-or-nothing table recording failure mode. A 24-entry table consumes exactly 24 ADD operations to transcribe verbatim. If the model decides to record the table, it must spend its entire pass budget on that single table, leaving zero capacity to record the adder or call site. This creates an artificial serialization bottleneck that makes selective recording mathematically impossible within a single pass. (High)

Top 3 levers:

(10) Native architecture: The text state and discrete edit-ops are introducing the exact attention interference and serialization bottlenecks killing the model; latent continuous memory bypasses this entirely.
(12) M-NL: The chain gate is a toy proxy; test the actual goal immediately on the untrained/trained floor to see if the architecture has any value for nuance preservation before spending more money.
(9) 1.5B→3B: The 1/10 clean-state compose and 0/10 padded probe strongly suggest a raw capability floor; if the base model cannot do 2-hop retrieval in a 200-token window, no harness orchestration will save it. (Medium)
All-or-nothing recording: It is an op-grammar / harness constraint problem. The 24-op cap fits the 24-row table exactly, forcing "transcribe whole table" to consume a full pass. Cheapest discriminative test: Remove the per-pass op cap entirely (or raise it to 100) on the untrained floor model and run the battery. If partial table recording occurs, the cap is the culprit. (High)

One run: (d) No training — build M-NL. The pre-registered gate verdict was "stop spending training runs on this instantiation." You have a scale confound, an architecture confound, and a toy-proxy confound. Before scaling or tweaking, you must verify if any instantiation of this state-keeping has value for the actual goal (nuance) using inference-only on the existing weights. (High)

1/10 clean-state compose: Plausibly trainable, but severely impaired by training format constraints. Qwen2.5-1.5B can natively perform 2-hop addition if allowed a scratchpad. Forcing the model to emit ANSWER: <integer> directly demands lookahead arithmetic, which 1.5B models fail at. If the training rows forced direct answers, the LoRA likely overwrote the model's native CoT ability. (Medium)

Prior art: Compressive Transformer / Block-Recurrent Transformers use continuous memory read/writes, avoiding the discrete ADD/REMOVE string-matching fragility you hit. MemGPT manages context via paging rather than verbatim transcription. This work contradicts the assumption that discrete text edit-ops are a stable target for distillation. Prior art heavily favors continuous latent state updates because LLMs are notoriously bad at precise string content-addressing without intermediate scratchpads. (High)

$0 probe: Run the GATE-3 clean-state (8-entry) close, but modify the prompt to allow a Chain-of-Thought scratchpad (e.g., "Extract the two operands, then compute the sum step-by-step before ANSWER:"). If 1/10 jumps to >8/10, the failure is formatting/objective, not capability floor. You haven't tested this because you forced direct answers. (High)

Hallucination / Inconsistency: The diagnostics claim "length itself kills two-operand composition at 1.5B" based on the padded probe, but GATE-3 uses a clean 8-entry state (tiny length) and still fails 1/10. A 1.5B model scoring 1/10 on an 8-entry retrieval-and-add task is wildly anomalous and points to a catastrophic format-compliance failure induced by your LoRA training, not a length or attention interference issue. 6/10 format failures on a tiny prompt means the model is broken, not the architecture. (High)

Honest claim: "A 1.5B model distilled to maintain a discrete text-state memory fails multi-hop cross-module composition, primarily due to training-induced format collapse and op-cap serialization bottlenecks." Missing for it to matter: A proof that any model (e.g., 3B or Claude) succeeds on this exact harness, isolating the architecture's viability from 1.5B's incapacity. (High)

Steelman the kill: Small LLMs have an effective context horizon of ~1k tokens. Forcing a 1.5B model to maintain a 7.7k token state divides attention across a space an order of magnitude beyond its native capacity. Distilling a 1.5B model to act as a symbolic database controller via discrete serial ops is fundamentally misaligned with how attention scales; it was guaranteed to fail by losing localization. I buy this steelman, but only partially. The native capability floor explains the 0/10, but the 1/10 on the 8-entry GATE-3 proves that the training method itself actively damaged the model's baseline reasoning. The kill was predictable. (High)

---

gemini-3.1-pro-studio

1. What is the most likely fatal flaw in the test design or training setup that we have NOT named above?
Confidence: High
The test design contains a fatal information bottleneck: the "need-class only" framing. You hid the specific target (23) until the final CLOSE phase. During passes 1–31, the model only knows it needs "operational questions about pricing." Mathematically, it cannot selectively extract 23: 988; it is forced to either transcribe the entire table or guess/summarize. You built a test that penalizes the model for failing to extract a specific row, but deliberately withheld the only piece of information that would allow it to identify that row as relevant.
2. Given the retrieval-vs-length dissociation, rank your top 3 levers from the board (or new ones) with one-sentence reasoning each.
Confidence: High
(8) Composition-focused training mix: Your clean-state compose is 1/10; if the model cannot do basic A+B arithmetic over 8 clean entries, optimizing state size or reading strategies is useless.
(4) Selective reading: Directly addresses the padded-probe finding (length kills composition) by violently culling the 7,700-token state bloat to only essential facts.
(New) CoT Scratchpad in CLOSE phase: 6/10 models failed format compliance and others hallucinated rules; forcing a reasoning scratchpad before the ANSWER: line offloads the computation from the model's severely limited internal weights.
3. The all-or-nothing table recording: is it most likely a data problem, an objective problem, an op-grammar problem, or an architecture problem? Name the cheapest test that discriminates.
Confidence: High
It is an objective problem. Because the target query is hidden until the end, the objective forces the model to either bulk-record everything that looks like a table or destructively summarize it. It cannot prioritize.
Cheapest test: Run the untrained floor model (or your current student) on 10 draws, but leak the exact final question (compute_line_surcharge(23)) into the prompt of every pass. If the model pivots to extracting only 23: 988, the objective/framing was the sole blocker.
4. You get one training run. Spend it on: (a), (b), (c), (d)? Pick one, justify.
Confidence: Medium
Spend it on (b) 1.5B re-ordered/re-mixed data (combining levers 3 and 8).
Justification: Your padded probe and GATE-3 show a hard failure at the terminal composition step (1/10 on clean state, 0/10 on padded). Upgrading to 3B (a) might just inherit the same formatting/composition mismatch if the teacher data didn't adequately demonstrate multi-hop arithmetic from state notes. You need to explicitly mix in multi-hop A+B composition tasks on small, clean states to fix the 1/10 floor, and re-order the prompt so data precedes instructions to maximize instruction adherence at 1.5B.
5. Is ~1/10 clean-state compose at 1.5B evidence of a hard capability floor, or plausibly trainable? Cite what you know that bears on small-model multi-hop arithmetic-over-context.
Confidence: High
It is plausibly trainable for format, but multi-hop arithmetic over context without a scratchpad is approaching a hard floor. We know from literature on small SLMs (like Qwen1.5/2.5-1.5B and Phi-2/3) that multi-hop retrieval and arithmetic degrade catastrophically when distractors are present, often requiring explicit Chain-of-Thought to resolve. The fact that 6/10 runs failed to even emit ANSWER: <integer> suggests catastrophic forgetting of instruction-following during the CLOSE phase, not an absolute limit of the weights. With CoT forced, 1.5B can do this.
6. What prior art are we reinventing or contradicting? Name specific work and what it changes about what's worth testing.
Confidence: High
Reinventing: MemGPT (maintains bounded state via OS-style ADD/REPLACE operations over infinite contexts) and Memoria / Walking Down Memory Maze (agentic memory banks updated incrementally).
Contradicting: The entire "Long-Context is All You Need" paradigm (e.g., Gemini 1.5 Pro, Claude 3.5 200k), which empirically proves that joint attention over raw, uncompressed text vastly outperforms lossy, bottlenecked memory architectures for complex QA.
What this changes: Testing recall/composition against an 64k context model is a losing battle. You must test tasks where joint attention fails entirely (e.g., extremely long temporal updates, contexts >10M tokens, or scenarios requiring dynamic state mutations over weeks), otherwise this architecture has no reason to exist.
7. What is the single cheapest $0 inference-only probe you would run next that is not already listed?
Confidence: High
Zero-shot Chain-of-Thought injection at CLOSE. Modify the final system prompt to append: "THINKING: Let's extract the variables from the state and compute the result step-by-step. \nANSWER:" right at the end. Your failures included argument/return confusion ("returns 23") and confabulated rules ("closest to 86"). These are classic symptoms of a model being forced to do multi-hop arithmetic entirely within its forward pass without token-generation space.
8. Hallucination check: anything in our numbers look internally inconsistent or too convenient? Say what and why.
Confidence: Medium
Two things look highly suspicious:
Pass Count Mismatch: You have 5,730 training rows from 277 documents. That averages ~20.6 passes per document. Yet your test battery runs K=31 passes. The student is extrapolating out-of-distribution on the pass conditioning for passes 22–31.
The 24-Op Cap vs. 24-Entry Table: You stated "Every table is transcribed in full (24/24 pairs)... 24-op cap per pass." If it writes one row per edit op, the table perfectly hits the 24-op ceiling. It's mathematically suspicious that it captured exactly 24 pairs. It likely wanted to write more (e.g., the rest of the file or the CARRIER_FUEL_BP decoy) but was arbitrarily hard-capped by your harness, artificially limiting the observation of its true failure mode.
9. What is the strongest honest claim this project could make today, and what one thing is missing for that claim to matter to anyone?
Confidence: High
Claim: "A 1.5B parameter model can reliably learn to execute a strict, content-addressed CRUD memory protocol over long documents (achieving >0.94 edit validity and avoiding state clobbering) via supervised distillation."
Missing: You have absolutely no evidence that this architecture yields better performance, lower latency, or cheaper inference than standard chunked RAG or native long-context models. Until it beats a naive baseline on a functional metric (like M-NL), it is just an elaborate logging mechanism.
10. Steelman the kill: argue this instantiation was never going to work and the gate was predictable a priori. Then say whether you buy your own steelman, and why.
Confidence: High
Steelman: This instantiation was doomed from inception. It demands query-blind, high-fidelity extraction of arbitrary numerical facts (a known weakness of LLMs), forces them into an unstructured integration state, fills that state with 7,700 tokens of distractors, and then demands zero-shot, multi-hop arithmetic over that noisy state using a 1.5B parameter model (another known weakness). You created a lossy information bottleneck, stripped the context needed for relevance scoring, and then tested it on an arithmetic task too hard for the base model's clean-state capacity.
Do I buy it? Yes, absolutely. You ran an end-to-end test where the component parts (1.5B multi-hop arithmetic, query-blind extraction) were individually guaranteed to fail. The architecture gate operated exactly as it should: it killed a setup that ignored the fundamental capacity limits of its own base model. Ensure the base model can do the terminal task first, then build the complex pipeline around it.

---

kimi-k3-qoder

 ▪ (high) The battery tested a terminal behavior that was never trained. Repo-verified: of 5,730 rows, 277 are "closing" rows but they teach analytical-brief writing (closing_demand,
    teacher_config.yaml:48); the string ANSWER: occurs 0 times in training data. The eval close demands state→question→ANSWER: <integer> — out-of-distribution in task, format, and
   length: the training window was justified with "state ≤4000 tok," yet eval states averaged 7,686 tok (max 8,545). The 6/10 missing ANSWER lines and the compose failures are
   exactly what triple-OOD predicts. Companion design flaw nobody named: state writes are question-blind, so row-level selectivity is information-theoretically unavailable — you can
   only learn class-level policies ("tables matter → copy tables"), which is what happened.
   (med) (i) (8) composition-focused mix — the close is the stage that scored 0 even with operands present, and it is precisely the stage absent from the training data. (ii) (4)
   selective reading — the only lever that shrinks close-time state back into both the regime where the chain provably fires (tiny states) and the ≤4K training distribution; the
   padded probe says excess state alone is fatal. (iii) (3) prompt-order re-render — $0 on the floor, zero teacher spend; weaker mechanism than (8)/(4) but dominates on cost and
   re-prices every training decision. (9) is strictly dominated until the close is trained: scaling an unsupervised terminal behavior is a lottery ticket.

   (high) Data problem. Verified: across all 277 teacher trajectories, only ~7% of 846 table-like entries show any omission marker; the teacher norm is exhaustive transcription (one
   entry holds ~153 records), and the grammar (_ADD_RE = (.+), unbounded) permits it. The student faithfully learned the demonstrated policy; the target behavior —
   padded probe says excess state alone is fatal. (iii) (3) prompt-order re-render — $0 on the floor, zero teacher spend; weaker mechanism than (8)/(4) but dominates on cost and
   re-prices every training decision. (9) is strictly dominated until the close is trained: scaling an unsupervised terminal behavior is a lottery ticket.
   (high) Data problem. Verified: across all 277 teacher trajectories, only ~7% of 846 table-like entries show any omission marker; the teacher norm is exhaustive transcription (one
   entry holds ~153 records), and the grammar (_ADD_RE = (.+), unbounded) permits it. The student faithfully learned the demonstrated policy; the target behavior —
   need-class-selective partial transcription — appears in ~0 demonstrations. Cheapest discriminating test (one hour, $0): count partial-table transcriptions in the 5,730 rows. If
   ~0, it's data by construction — no architecture emits behavior absent from its demonstrations, and objective/architecture hypotheses are moot until data is fixed.
   (med) (d) — build M-NL. Your pre-committed rule said ≤1/10 = stop spending training runs on this instantiation, and every training option now bets the scarcest resource on one
   unproven mechanism while the goal-aligned test sits unrun at zero training cost. M-NL with the existing student/floor pair is decisive either way: if the 116-entry student state
   loses to the 725-token floor state on nuance→decision, no lever on the board matters; if it wins, you have your real claim and a re-aimed objective. If a run must be spent: (b),
   re-mixed to add QA-format closing rows synthesized from existing states. (a) is last — same data preserves every identified flaw.
   (med) Plausibly trainable, not a hard floor. The task is one lookup plus 988+1365 — strictly easier than GSM8K multi-step problems, where Qwen2.5-1.5B-Instruct scores
   non-trivially with CoT. Goat (Liu & Low 2023) shows fine-tuned 7B beats GPT-4 on arithmetic — arithmetic is highly trainable. Dziri et al. 2023 ("Faith and Fate") shows
   compositionality collapses precisely without task-specific training — this student's exact condition (zero QA-from-state rows). The observed failures are distractor
   discrimination, argument/return grounding, and format — all supervision-shaped, none arithmetic. Caveat: two-operand retrieval under near-isomorphic distractors is a genuine
   small-model weak spot; trainable ≠ clears 5/10.
   (med-high) MemGPT (Packer et al. 2023): self-editing memory, but its evals evade compositional joins. ReadAgent (Lee et al. 2024): gist reading that re-fetches raw pages
   query-aware at answer time — the move your protocol forbids. HippoRAG (Gutiérrez et al. 2024) and A-MEM (Xu et al. 2025): small LLMs + query-indexed memory beat long-context large
    models on multi-hop QA — directly contradicting "1.5B too small" as a sufficient explanation. LongLLMLingua (Jiang et al. 2023): question-aware compression ≫ question-agnostic —
   predicts your RECORD selectivity failure. RMT/ARMT (Bulatov et al. 2022; Rodkin et al. 2024): memory tokens work but cross-segment associative recall requires explicit training.
   Memorizing Transformer (Wu et al. 2022), Compressive Transformer (Rae et al. 2019), AutoCompressor (Chevalier et al. 2023): substrate and cautionary recipes for lever (10).
   Map-reduce QA: known to fail exactly your cross-module join. Net: every successful memory system retrieves query-aware; add a query-aware upper-bound arm (re-fetch/retrieval over
   state) to price what the source-gone constraint costs.
   (high) Real-state size sweep: for the 2 student draws holding both operands at close, re-run the identical close after deleting 25/50/75% of non-operand entries (real adversarial
   distractors retained), plus one arm deleting only decoy-table entries. Your padded probe used digit-free filler, so it removed distractor content while claiming to isolate length;
    this maps compose-vs-state-size on real content and directly prices the state budget the harness must enforce. $0, frozen weights, fits the 1080 Ti.
   (high) Headline numbers check out against the repo (153 blocked, validity band, 116 entries/7,686 tok, temp-0 anchors exist and also fail). Flags: (a) no uncertainty
   quantification anywhere — GATE-3's 1/10-vs-0/10 is Fisher p≈0.5, and the load-bearing filtered-probe success is n=1; (b) "length itself kills composition" is confounded twice —
   training states were ≤4K tok while eval closes ran 6.5–8.5K (OOD, not length per se), and state-length vs within-entry length (24 pairs in one entry) is never separated — GATE-3
   fails at only 8 entries; (c) "RETAIN is clean" is partly by construction — the guard blocked 153 writes; the honest claim is "retention is guaranteed by the harness," not learned;
    (d) E2E pools format failure with reasoning failure — verdict robust, component attribution not.
   (high) Strongest claim: "A scheduled multi-pass protocol with content-addressed edit ops is distillable into a 1.5B model — ≥0.94 op validity over 31 passes, a self-organized
   ~7.7K-token state, zero guard-visible retention loss, transfer to an unseen domain." Missing for it to matter: one downstream task where the maintained state beats the floor's
   state (student-state > floor-state > no-state). A large valid state is a procedure, not a capability, until something reads it better. M-NL is that missing measurement.
   (med) Steelman: E2E = P(record)×P(retain)×P(compose)×P(format), and every factor was knowably weak pre-run: compose at 1.5B from an idealized state ~0.1 (a $0 GATE-3 on the base
   model would have revealed it — nobody ran the terminal capability check before fixing the 0.5 bar); format untrained (0 ANSWER rows); selectivity information-theoretically
   unavailable under question-blind writes, forcing full transcription, which breaches the ≤4K state assumption and pushes the close OOD. The product cannot reach 0.5; the gate was
   lost at pre-registration, not at evaluation. I buy the narrow version: this instantiation + this data + this bar was dead on arrival, and the calibration failure was avoidable. I
   reject the strong version: retention worked, selectivity and compose are trainable targets with known recipes, and query-aware memory-agent literature shows small models doing
   multi-hop. The steelman kills schedule-execution distillation as a recipe — not the bet.