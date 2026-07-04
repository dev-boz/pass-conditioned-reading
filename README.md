# Pass-Conditioned Reading

This is the testing repo for pass-conditioned reading, one of the core pieces of the [DiSCo / Context Diffusion proposal](https://github.com/dev-boz/diffusive-semantic-compression). The idea under test: a single schedule position controls both what the model is shown (how compressed the view is) and what it has to produce (how detailed the output is), over a source that is never reconstructed. The model only ever sees views of it.

The main repo explains the idea and where it came from. This repo is where I try to break it cheaply before spending real money on training. Everything is set up as a pre-registration, meaning the design, the criteria that would kill it, and the cheap gate experiments are all on record before the expensive training run (E2′) is attempted. Partly because that's good practice, and partly so that when E2′ eventually happens nobody (including me) can quietly move the goalposts after seeing the results. So what you're looking at here is not a finished result, it's a running audit trail.

## Where to start

If you only read one thing, read the [public summary](docs/PUBLIC-SUMMARY.md). It's the short plain-language version, and the honest one-liner is: not unfeasible, possibly feasible with a trained model. It didn't fail, and it showed potential.

The full record is the [consolidated findings](docs/CONSOLIDATED-FINDINGS.md), covering everything from E0 through P7 plus a cross-family existence check. What was shown, what wasn't, the negatives and the open questions, and why I think the trained-model step (E2′) is still justified even though the untrained floor never got over the line. It supersedes the status table below for P7 and the cross-family work.

The pre-registration itself is the [outline, v0.3](docs/pca-outline-v0.3.md). That's the coupling claim (M1) with explicit kill criteria, the gated experiment program (E0 → P-pilots → E1′/E2′), and a prior-art map where every citation has been verified.

Then there are two review documents, the [gauntlet arbitration](docs/gauntlet-arbitration.md) and the [verification arbitration](docs/verification-arbitration.md). The first is a 19-input adversarial review of the claims. The second is a five-agent citation-verification sweep that caught fabricated citations in my own draft. I've published both as-is, because I think a documented self-correction says more about whether you can trust this repo than a polished claim would.

## Current status

A quick note first: since the table below was written, experiments through P7 (split-unit record→retain→compose) and a cross-family existence check have finished (26 June 2026). The consolidated findings doc linked above is the current record, the table is the running log through P6.

| Stage | What | Where it landed |
|---|---|---|
| E0 | Position-from-view classifier (the regime gate) | Done (provisional), superseded by E0-final |
| P1 | Prompt-level micro-pilot, coupled vs input-/output-staged | Done (parser v2.1) |
| P2 | Position-token pilot, explicit position field vs none | Done (parser v2.1) |
| P3 | Prompt-rubric pilot (position / +rubric / +confidence) | Done |
| P4 | 80K planted-facts run, recall of deliberately planted facts under the coupled schedule | Done, and the pre-registered kill condition failed (details below) |
| E0-final | Non-provisional E0 on production (Haiku-summarised) views | Done, regime is signal-carrying (0.561, Kiro-only robustness 0.584) |
| P5 | Verbatim-stage contamination, does prior state suppress recording of a detail present in the view? | Done, no robust contamination. P4's misses were task-vagueness, not prior-state suppression |
| P6 | Whole-document synthesis, a causal why whose hinge sits mid-document | Pre-registered ([pre-reg](experiments/p6_global_synthesis/PRE-REG.md), [gold chain](experiments/p6_global_synthesis/gold_chain.json)), first of a planned battery, run pending |
| E1′ / E2′ | The trained conditioning-channel and coupling experiments | Gated behind everything above, not yet run |

### E0: can you tell where you are just by looking?

E0 asks whether the pass position (k, K) is recoverable from the view v_k alone. If it is (near-ceiling accuracy) then telling the model its position would be redundant and the whole conditioning channel is on shaky ground. If it isn't, position carries real signal and the program continues.

The final run used 2,400 production views from the teacher compressor, Claude Haiku 4.5 (decisions D29/D30). The result is signal-carrying. Tier-B semantic bucket accuracy came in at 0.561 against the pre-registered 0.90 / 0.70 thresholds. A robustness gate on the single-path Kiro-only subset (1,974 views) landed at 0.584, so the result isn't an artifact of the multi-path generation. The production run stands on its own and the provisional label is dropped.

Two things to keep in mind when reading the numbers. First, the 0.561 is not comparable to the earlier provisional 0.433, because E0-final changed both the compressor and the Tier-B instrument (it added chunk-and-pool), so the two runs are measuring with different rulers. Second, the Tier-A hand-feature score of 0.672 is the length/schedule channel I deliberately excluded (D7). It's reported for transparency, not used for the gate. Details are in the [final results](experiments/e0_view_classifier/RESULTS_FINAL.md), the cross-compressor fidelity check is in [KIRO_FIDELITY](experiments/e0_view_classifier/KIRO_FIDELITY.md), and the gate definitions are in [GATES](docs/GATES.md). The original provisional run (extractive stand-in, 0.433, same signal-carrying call) is preserved in [RESULTS](experiments/e0_view_classifier/RESULTS.md).

### P1 to P3: mostly a lesson about my own parser

The prompt pilots ended up teaching me more about my testing method than about the model.

P1 originally reported around 50% malformed edit operations, which looked terrible. It turned out to be my parser, not the model. The dominant "malformation" was the 7B naming the entry it creates (ADD S3: ...) rather than using S3 as an insert-after anchor, and the parser was counting that as broken. With the parser corrected, edit-op validity is ≈1.0 across every arm.

P2's apparent position effect evaporated the same way. The first run showed 0.708 vs 0.375 validity for position-field vs none. Once the parser stopped penalising the naming convention it was 0.979 vs 0.983, a null prompt-level effect.

The result that survived is P3. A bare position field does not induce staged behaviour, but a per-pass behavioural rubric does, cleanly - pure ADD while scaffolding, pure REPLACE while integrating. That's the strongest prompt-level signal in the repo and it's why E1′'s "prompt floor" arm is now defined as the rubric version.

The full parser progression (v1 → v2.0 → v2.1, including an under-fix in the middle) is documented in [DECISIONS.md](docs/DECISIONS.md) under D22, and I've kept the obsolete numbers in the parser-v1 and parser-v2.0 directories rather than deleting them. The corrected implementation is [editops.py](src/pca/editops.py) and its tests.

### P4: the kill condition fired

P4 planted facts in an 80K synthetic document and scored recall under the coupled schedule against a single generous dense read. The pre-registered kill rule was blunt: coupled has to beat dense, or that counts as evidence against M1's premise.

It didn't beat it. Coupled scored 0.625 (5/8), dense scored 0.625, and the coupled schedule spent roughly 11× the tokens and 9× the wall-clock getting there. On this document, no recall advantage. That's a fail and I'm reporting it as one.

The diagnosis, which is not the same as excusing it: coverage actually worked, every planted fact reached a view. The untrained 7B simply declined to record three asides that were orthogonal to the task it was given, so the recall metric is partly measuring task-salience rather than coverage. It doesn't refute M1 (n=1, an untrained floor, and that task-vs-fact salience tension), but it is a real failure of the premise as operationalised here, and it goes into the E2′ design with the diagnosis attached. Full account in the [P4 results](experiments/p4_planted_facts/RESULTS.md).

### P5: was P4's miss contamination?

P5 chased one possible mechanism behind P4. Does conditioning the read on prior state suppress the recording of a task-relevant detail that's sitting right there in the view? Three arms (A0/A1/A2) isolated state-visibility against a frozen upstream state.

The answer is no robust contamination. Under an explicit ask, the untrained floor recovers the dropped facts in every arm, even at peak prior-saturation. P4's misses were task-vagueness, not prior-state suppression, which means the lever is a design choice (query- or recall-conditioning the floor) rather than a fundamental flaw.

### P6 and the trained runs

P6 asks whether the coarse-scaffold schedule can answer a causal why whose hinge sits mid-document, the kind of question that head+tail truncation and RAG structurally miss. Arms are dense, coupled, and verbatim-only with no scaffold. It's pre-registered and is the first of a planned battery.

E1′ and E2′, the trained conditioning-channel and coupling experiments, sit gated behind all of the above and have not been run. They're the actual arbiters.

## Reproducing the results

[DECISIONS.md](docs/DECISIONS.md) lists all 30 parameters I had to invent, each traced back to the spec line it derives from. That doubles as a spec-completeness audit of the parent proposal, which defines the schedule shape but almost no concrete values.

Everything is uv-managed with pinned deps (pyproject.toml, uv.lock) and fixed seeds, and every experiment re-runs from its config alone. E0 (both runs) is CPU-only and the P-pilots use local CPU inference (Qwen2.5-7B-Instruct via llama.cpp), so those numbers cost $0 to reproduce. E0-final's views need the teacher compressor (Claude Haiku 4.5) - see the data card for the delivery paths and gen_path provenance.

Run with `make e0 | p1 | p2 | p3`, or the equivalent `uv run` lines in the Makefile. The corpus, the view sets (data/views/views*.jsonl) and the model weights are not vendored. The [data card](data/views/DATA_CARD.md) and views_config.yaml document regeneration, src/pca/gen_views.py rebuilds the provisional views, and pca.gen_views_llm plus pca.merge_paths rebuild the production (Haiku) ones.

## Layout

```
docs/        pre-registration outline, both arbitration docs, DECISIONS.md, GATES.md
experiments/ e0_view_classifier/ (incl. RESULTS_FINAL.md, KIRO_FIDELITY.md, results_final/)
             p1_micro_pilot/  p2_position_pilot/  p3_prompt_rubric/  p4_planted_facts/
             (each: config, runner, RESULTS/transcripts, metrics.json; parser-v1/v2.0 archives)
src/pca/     view schedule, compressors (extractive + claude-p/Kiro Haiku), edit-op parser
             + tests, llama.cpp client, planted-facts scoring, view/merge drivers, feature code
data/views/  DATA_CARD.md + views_config.yaml (corpus + view sets are regenerated, not shipped)
```

## Licensing

Docs and code are licensed separately. The documentation (the outline, both arbitration docs, the prior-art map, DECISIONS.md, GATES.md, the RESULTS files and the data card) is [CC BY 4.0](LICENSE-CC-BY-4.0.txt). The code (src/pca/, the experiment runners and the configs) is [Apache 2.0](LICENSE-Apache-2.0.txt). GitHub's sidebar shows no license because it can't classify a two-file split, but both license files are in the repo.

## What's being claimed, and what isn't

M1, the coupling interaction, is the paper. If its interaction term comes back null, this whole thing reduces to the parent proposal plus some one-sided staging results that already exist elsewhere. M2 is a distillation-efficiency measurement under a stated null. Nothing in this repo is the trained comparison - E1′ and E2′ remain the arbiters.

Where the record stands so far: E0-final did not kill M2/D1 (signal-carrying means the explicit channel isn't predicted redundant, and the probes stay interpretable). P4 fired its kill condition against M1's premise as operationalised by an untrained floor, and P5 then showed the mechanism wasn't contamination - under an explicit ask the floor recovers the dropped facts in every arm, even at peak prior-saturation, so the miss was task-vagueness and the fix is a design choice. All of that is above, unedited. None of it settles viability. That rides on the trained student (E2′), not on getting an untrained floor over the line.
