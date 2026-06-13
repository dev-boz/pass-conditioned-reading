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
| **E0** | Position-from-view classifier (the regime gate) | **Done, provisional** — see below |
| **P1** | Prompt-level micro-pilot: coupled vs input-/output-staged | Done (parser v2.1) |
| **P2** | Position-token pilot (explicit position field vs none) | Done (parser v2.1) |
| **P3** | Prompt-rubric pilot (position / +rubric / +confidence) | Done |
| **P4** | **80K planted-facts run** — recall of deliberately planted facts across a long synthetic source under the coupled schedule | **🔜 in progress** |
| **E0-final** | Non-provisional E0 on production (LLM-summarized) views | **🔜 in progress** — priced upgrade path documented in the E0 report |
| **E1′ / E2′** | The trained conditioning-channel and coupling experiments | Gated behind the above; **not yet run** |

### E0 — provisional, by design

E0 asks whether pass position `(k, K)` is recoverable from the view `v_k` alone (near-ceiling → time-agnostic regime, the explicit channel is predicted redundant; low → signal-carrying, the program proceeds). **Result: regime = signal-carrying** (Tier-B bucket accuracy 0.433 vs 0.90/0.70 pre-registered thresholds).

It is labelled **`E0-provisional`** and must not be read as final: the views were produced by a deterministic **extractive stand-in compressor**, not the production teacher-LLM summarizer (no zero-cost inference path was available). The stand-in caveat, the direction of risk, and the priced upgrade path (≈US$8–15 of LLM compression, or a local GPU summarizer) are all stated in [`experiments/e0_view_classifier/RESULTS.md`](experiments/e0_view_classifier/RESULTS.md) and [`docs/GATES.md`](docs/GATES.md). Honest negatives and provisional calls in public are a feature, not an omission.

### The P-pilots and the parser correction (proof-of-method)

The prompt-level pilots came with a methodological correction worth reading in full, because it is the reproducibility story:

- **P1's original "~50% malformed edit ops" number was a parser artifact.** The dominant 7B "malformation" was the model *naming* the entry it creates (`ADD S3: …`) rather than using `S3` as an insert-after anchor. Under a corrected parser, edit-op validity is ≈1.0 across all arms.
- **P2's apparent position effect evaporated.** The first run reported 0.708-vs-0.375 validity for position-field vs none; once the parser stopped penalizing the naming convention, it was **0.979 vs 0.983 — a null prompt-level effect.**
- **The keeper is P3's op-mix result.** A bare position field does *not* induce staged behavior; a **per-pass behavioral rubric does, cleanly** (pure ADD while scaffolding, pure REPLACE while integrating). This is the strongest prompt-level signal and the reason E1′'s "prompt floor" arm is now defined as the rubric version.

The full v1 → v2.0 → v2.1 parser progression — including the under-fix in between — is documented in [`docs/DECISIONS.md`](docs/DECISIONS.md) **D22**, with the obsolete numbers preserved under `*_parser-v1/` and `*_parser-v2.0/` directories. [`src/pca/editops.py`](src/pca/editops.py) and its tests are the corrected implementation.

## Reproducibility

- **[`docs/DECISIONS.md`](docs/DECISIONS.md)** lists all **24 invented parameters** traced to the spec line each derives from — which doubles as a spec-completeness audit of the parent proposal (it defines the schedule *shape* but almost no concrete values).
- `uv`-managed, pinned deps (`pyproject.toml`, `uv.lock`); fixed seeds throughout; every experiment re-runnable from its config alone. E0 is CPU-only; the P-pilots use local CPU inference (Qwen2.5-7B-Instruct via llama.cpp), so the published numbers cost $0 to reproduce.
- `make e0 | p1 | p2 | p3` (or the equivalent `uv run` lines in the `Makefile`). The corpus (`data/views/views.jsonl`) and model weights are **not vendored** — `data/views/DATA_CARD.md` + `views_config.yaml` document regeneration, and `src/pca/gen_views.py` rebuilds the views.

## Layout

```
docs/        pre-registration outline, both arbitration docs, DECISIONS.md, GATES.md
experiments/ e0_view_classifier/  p1_micro_pilot/  p2_position_pilot/  p3_prompt_rubric/
             (each: config, runner, RESULTS/transcripts, metrics.json; parser-v1/v2.0 archives)
src/pca/     view schedule, compressors, edit-op parser + tests, llama.cpp client, feature code
data/views/  DATA_CARD.md + views_config.yaml (the corpus itself is regenerated, not shipped)
```

## Licensing

Dual-licensed by artifact type:

- **Documentation** — the outline, both arbitration documents, the prior-art map, `DECISIONS.md`, `GATES.md`, `RESULTS.md` files, and the data card — under **[CC BY 4.0](LICENSE-CC-BY-4.0.txt)**. Attribution required; redistribution and adaptation allowed.
- **Code** — `src/pca/`, the experiment runners, and configs — under **[Apache License 2.0](LICENSE-Apache-2.0.txt)**.

## Scope and honesty

M1 (the coupling interaction) is the paper; if its interaction term is null, this reduces to the parent's claims plus one-sided staging results that already exist. M2 is a distillation-efficiency measurement under a stated null. Nothing here is the trained comparison — E1′/E2′ remain the arbiters. E0 may yet kill M2 and D1 before any GPU is touched once it is run on production views; that is the intended function of running it first.
