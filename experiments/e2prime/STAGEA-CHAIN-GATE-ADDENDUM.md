# Stage A Chain Gate - Pre-run Addendum

**Status:** Maintainer-approved on 2026-07-20.

This addendum must be committed before any Stage-A chain-gate model draw. It changes no outcome threshold.

## Purpose

Run the Stage-A trained student and its same-base untrained floor on the frozen P7 split-unit chain fixture under the E2PRIME-PREREG and E2PRIME-CRITERION rules. This document fixes the implementation details needed to use the E2' v3.2 harness rather than the legacy P7 runner.

## Frozen setup

- Fixture: `experiments/p7_split_unit/fixture/fixture_spec.json`, version 2, seed 70707. `REGION_SURCHARGE_CENTS[23] = 988`, `RECONCILIATION_ADDER_CENTS = 1365`, and target answer 2353 are asserted before every run.
- Views and schedule: frozen P7 structure-preserving v2 scaffold and unchanged P7 schedule.
- Harness: `src/pca/editops.py` v3.2, `IntegrationState(guard="strict")`, and the frozen 24-op per-pass cap. Raw model output is parsed and applied without legacy P7 operation rewriting or deduplication.
- Recorder prompt: the E2' v3.2 grammar and per-pass scaffold/integrate/verbatim rubrics. The fixed need class is: "Downstream, operational questions about this codebase's pricing, order flow, configuration, and cross-module behavior will be answered from your state alone; the source will not be available." This names an information class, never a target structure, identifier, location, or value.
- Student: `runs/stageA_coupled_v2/stageA_v2-f16.gguf`.
- Floor: `models/Qwen2.5-1.5B-Instruct-f16.gguf`.
- Serving: local llama.cpp, one model at a time, 24,576-token context, full GPU offload.

## Draws and scoring

Each arm receives ten sampled draws (seeds 1-10, temperature 0.7) and one separately reported deterministic anchor (seed 42, temperature 0). The sampled ten are the verdict denominator; the anchor is never pooled.

End-to-end success requires all of:

1. final state visibly holds the 23-to-988 operand and 1365 adder;
2. state contains no pre-composed 2353 before closing;
3. close returns 2353; and
4. close visibly derives it from the recorded state.

The runner records mechanical candidate flags only. Every candidate success is hand-verified before a verdict. Raw prompts, outputs, parsed operations, guard outcomes, snapshots, hashes, and per-seed JSON records are retained.

## Required companion checks

The Stage-A record also includes the student relevance-control v2, GATE-1 backfill, GATE-3 seeded-compose, and the P3-rubric same-base reference. They are reported separately from the chain verdict and cannot soften a chain-gate outcome.

## Status clarification

`docs/E2PRIME-PREREG.md` and `docs/E2PRIME-CRITERION.md` were committed before teacher data generation. Their historical `DRAFT` wording is stale; by their own amendment rule, the committed protocol governs this run. This addendum records maintainer sign-off and implementation detail; it does not alter the pre-committed bars or permitted next moves.
