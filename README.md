# Pass-Conditioned Reading

Pre-registration and gated experiment scaffolding for **pass-conditioned reading** — a multi-pass architecture in which one schedule position jointly governs *what the model is shown* (input view resolution) and *what it must emit* (output detail level), over an external source that is never reconstructed.

This repository is the **public pre-registration and the running audit trail**, not a finished result. It exists so the design, the kill criteria, and the cheap gates are all on record *before* the load-bearing training run (E2′) is attempted. Builds on the parent proposal, [DiSCo / diffusive-semantic-compression](https://github.com/dev-boz/diffusive-semantic-compression).

> **Documentation under CC BY 4.0; code under Apache 2.0.** (`LICENSE-CC-BY-4.0.txt`, `LICENSE-Apache-2.0.txt`; split by artifact type — see *Licensing* below. GitHub's sidebar shows no license because it doesn't classify a dual-file split; both license files are present.)

## Start here

- **[`docs/pca-outline-v0.3.md`](docs/pca-outline-v0.3.md) — the centerpiece.** The pre-registration: M1's coupling claim with explicit *kill criteria*, the regime-gated experiment program (E0 → P-pilots → E1′/E2′), and a fully citation-verified prior-art map.
- **[`docs/gauntlet-arbitration.md`](docs/gauntlet-arbitration.md)** and **[`docs/verification-arbitration.md`](docs/verification-arbitration.md) — the method.** A 19-input adversarial review of the claims, plus a five-agent citation-verification sweep with arbitration that **caught fabricated citations in our own draft**. Published deliberately: the audit infrastructure is the point, and a documented self-correction is more informative than a polished claim.

## Status — a live program with its next gates named

| Stage | What | State |
|---|---|---|
| **E0** | Position-from-view classifier (the regime gate) | Done (provisional) — superseded by E0-final |
| **P1** | Prompt-level micro-pilot: coupled vs input-/output-staged | Done (parser v2.1) |
| **P2** | Position-token pilot (explicit position field vs none) | Done (parser v2.1) |
| **P3** | Prompt-rubric pilot (position / +rubric / +confidence) | Done |
| **P4** | **80K planted-facts run** — recall of deliberately planted facts across a long synthetic source under the coupled schedule | **Done — pre-registered kill condition FAILED** (see below) |
| **E0-final** | Non-provisional E0 on production (Haiku-summarized) views | **Done — regime = signal-carrying** (0.561; kiro-only robustness 0.584) |
| **P5** | **Verbatim-stage contamination** — does conditioning the read on prior state suppress recording of a task-relevant detail present in the view? (frozen upstream state; arms A0/A1/A2 isolate state-visibility) | **Done — no robust contamination**; P4's misses were task-vagueness, not prior-state suppression (see below) |
| **E1′ / E2′** | The trained conditioning-channel and coupling experiments | Gated behind the above; **not yet run** |

### E0 — now final: regime = signal-carrying

E0 asks whether pass position `(k, K)` is recoverable from the view `v_k` alone (near-ceiling → time-agnostic regime, the explicit channel is predicted redundant; low → signal-carrying, the program proceeds).

**E0-final (non-provisional):** run on 2 400 production views from the teacher compressor **Claude Haiku 4.5** (D29/D30). **Regime = signal-carrying** — Tier-B (semantic) bucket accuracy **0.561** vs the pre-registered 0.90 / 0.70 thresholds. A robustness gate on the single-path Kiro-only subset (1 974 views) lands at **0.584**, so the result is not an artifact of the multi-path generation; the production run stands on its own and the provisional label is dropped. Two read-it-right notes are in the report: **0.561 is *not* delta-comparable to the provisional 0.433** (E0-final changed both the compressor *and* the Tier-B instrument — it added chunk-and-pool), and the **Tier-A hand-feature 0.672 is the deliberately excluded length/schedule channel (D7)**, reported transparently, not gated. Details: [`experiments/e0_view_classifier/RESULTS_FINAL.md`](experiments/e0_view_classifier/RESULTS_FINAL.md), the cross-compressor fidelity check [`KIRO_FIDELITY.md`](experiments/e0_view_classifier/KIRO_FIDELITY.md), and [`docs/GATES.md`](docs/GATES.md). The original provisional run (extractive stand-in, 0.433, same signal-carrying call) is preserved in [`RESULTS.md`](experiments/e0_view_classifier/RESULTS.md).

### P4 — the pre-registered kill condition failed (reported, not buried)

P4 scored recall of deliberately planted facts in an 80K synthetic document, coupled schedule vs a single generous dense read. **Pre-registered kill rule: coupled must *exceed* dense, else evidence against M1's premise.** Outcome: **coupled 0.625 (5/8) ≤ dense 0.625** — at ~11× tokens and ~9× wall-clock, no recall advantage on this document. Diagnosis (not eviction): coverage worked and every fact reached a view; the untrained 7B floor simply declined to record three *task-orthogonal* asides, and the recall metric is partly measuring task-salience rather than coverage. Not an M1 refutation (n=1, untrained floor, task↔fact salience tension) but a real failure of the premise *as operationalized here* — carried, with diagnosis, into the E2′ design. Full account in [`experiments/p4_planted_facts/RESULTS.md`](experiments/p4_planted_facts/RESULTS.md).

### The P-pilots and the parser correction (proof-of-method)

The prompt-level pilots came with a methodological correction worth reading in full, because it is the reproducibility story:

- **P1's original "~50% malformed edit ops" number was a parser artifact.** The dominant 7B "malformation" was the model *naming* the entry it creates (`ADD S3: …`) rather than using `S3` as an insert-after anchor. Under a corrected parser, edit-op validity is ≈1.0 across all arms.
- **P2's apparent position effect evaporated.** The first run reported 0.708-vs-0.375 validity for position-field vs none; once the parser stopped penalizing the naming convention, it was **0.979 vs 0.983 — a null prompt-level effect.**
- **The keeper is P3's op-mix result.** A bare position field does *not* induce staged behavior; a **per-pass behavioral rubric does, cleanly** (pure ADD while scaffolding, pure REPLACE while integrating). This is the strongest prompt-level signal and the reason E1′'s "prompt floor" arm is now defined as the rubric version.

The full v1 → v2.0 → v2.1 parser progression — including the under-fix in between — is documented in [`docs/DECISIONS.md`](docs/DECISIONS.md) **D22**, with the obsolete numbers preserved under `*_parser-v1/` and `*_parser-v2.0/` directories. [`src/pca/editops.py`](src/pca/editops.py) and its tests are the corrected implementation.

## Reproducibility

- **[`docs/DECISIONS.md`](docs/DECISIONS.md)** lists all **30 invented parameters** traced to the spec line each derives from — which doubles as a spec-completeness audit of the parent proposal (it defines the schedule *shape* but almost no concrete values).
- `uv`-managed, pinned deps (`pyproject.toml`, `uv.lock`); fixed seeds throughout; every experiment re-runnable from its config alone. E0 (both runs) is CPU-only; the P-pilots use local CPU inference (Qwen2.5-7B-Instruct via llama.cpp), so those numbers cost $0 to reproduce. E0-final's views require the teacher compressor (Claude Haiku 4.5) — see the data card for the delivery paths and `gen_path` provenance.
- `make e0 | p1 | p2 | p3` (or the equivalent `uv run` lines in the `Makefile`). The corpus and view sets (`data/views/views*.jsonl`) and model weights are **not vendored** — `data/views/DATA_CARD.md` + `views_config.yaml` document regeneration; `src/pca/gen_views.py` rebuilds the provisional views, `pca.gen_views_llm` + `pca.merge_paths` the production (Haiku) views.

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

Dual-licensed by artifact type:

- **Documentation** — the outline, both arbitration documents, the prior-art map, `DECISIONS.md`, `GATES.md`, `RESULTS.md` files, and the data card — under **[CC BY 4.0](LICENSE-CC-BY-4.0.txt)**. Attribution required; redistribution and adaptation allowed.
- **Code** — `src/pca/`, the experiment runners, and configs — under **[Apache License 2.0](LICENSE-Apache-2.0.txt)**.

## Scope and honesty

M1 (the coupling interaction) is the paper; if its interaction term is null, this reduces to the parent's claims plus one-sided staging results that already exist. M2 is a distillation-efficiency measurement under a stated null. Nothing here is the trained comparison — E1′/E2′ remain the arbiters. E0-final did **not** kill M2/D1 (signal-carrying → the explicit channel is not predicted redundant, the probes stay interpretable), and P4 fired its kill condition against M1's premise *as operationalized by an untrained floor* — both outcomes are on the record above, unedited. P5 then probed one mechanism behind P4's result — whether prior state *contaminates* the read — and found **no robust effect**: under an explicit ask the untrained floor recovers the dropped facts in every arm, even at peak prior-saturation, so P4's miss was **task-vagueness, not contamination** (the lever is query/recall-conditioning the floor, a design choice). None of this settles viability, which rides on the trained student (E2′), not on getting an untrained floor over the line.
