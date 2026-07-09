# Awareness gut-check — PRE-REGISTRATION (written before results; 2026-06-25)

**Status: GUT CHECK ONLY — confounded, never in the clean table.** kiro has no temp/seed/max_tokens
control and injects a residual base "AI coding agent" persona that a custom agent can't fully remove.
The clean confirmation (if a pulse) belongs on the OpenRouter pipeline.

## Question
Between blind models and a trained model there is a midpoint: inject minimal, **task-agnostic** awareness
via the prompt. Does it move the close-time outcome — and if so, is the lever **recorder-side** or
**closing-side**? This localizes what a custom model (or a cheap prompt feature) would target.

## Critical correction (from reading run.py — changes the design)
The recording model is **NOT blind** in the baseline. It already receives:
- `SYSTEM`: "You are the integration model inside a multi-pass reading architecture … partial views."
- `USER_TMPL` every pass: `position: {k, K}` (its pass index + total).
- `RUBRIC`: "integrate … the **relationships** among them" (already told to keep relationships).

It has architecture-awareness + position + a keep-relationships instruction **and still drops the
binding.** So the genuinely-blind component is the **CLOSING model**, whose prompt may *actively suppress*
recombination: *"Use only values present in the state; do not invent numbers … else INSUFFICIENT."* A
model holding 988 and 1365 but not 2353 can read "compute 988+1365" as inventing → returns bare 988 or
INSUFFICIENT. The llama70b failures used that exact language ("without the exact formula we cannot
compute"; one answered INSUFFICIENT).

## Setup (identical across arms)
kiro `claude-haiku-4.5`, agent `p7raw` (empty system prompt, no tools → strips kiro's agent layer; the
residual base persona is a CONSTANT across arms → cancels in the A/B), `--effort low` (non-thinking).
n=5, specifics, seeds 42/1/2/3/4 (kiro ignores seed → repeats sample any serving nondeterminism).

## Arms
1. **baseline** (`haiku_gc`): unmodified.
2. **closing-side** (`haiku_gc_close`, `permit_derive`): swap `CLOSING_SYSTEM` → `CLOSING_SYSTEM_DERIVE`:
   *"…Base your answer on values present in the state; you MAY compute and combine those values
   arithmetically to derive the answer. Do not introduce values that are absent…"* (task-agnostic: no
   surcharge/adder/addition mentioned).
3. **recorder-side** (`haiku_gc_rec`, `inject_pos`): prepend each pass:
   *"You are on reading pass {k} of {K}; this is one partial {phase}-view covering source turns
   {lo}–{hi} of {T} total, and {K−k} pass(es) remain."* (salient position + genuinely-new source-coverage;
   no task content).

## Pre-committed predictions
- **Primary readout:** per-seed classification of the COUPLED arm — compose(==2353) / recombine-fail
  (both 988 & 1365 in final_state, not summed) / retention-fail (a fragment absent) / no-record /
  INSUFFICIENT — plus the coupled compose rate and the INSUFFICIENT rate.
- **H1 (closing-side):** `haiku_gc_close` ≥ baseline on compose; specifically it converts
  recombine-fail/INSUFFICIENT seeds (state holds both operands) into composes. This is the lever.
- **H2 (recorder-side):** `haiku_gc_rec` ≈ baseline (near-null), since position/architecture/keep-
  relationships are already in the baseline; any movement comes only from the added source-coverage cue.
- **Localization:** close ≫ baseline AND rec ≈ baseline ⇒ the bottleneck is a **closing-side readout
  artifact**, not missing recorder awareness — and the cheap fix is the closing prompt, not the recorder.

## Caveats
n=5; no temp/seed control; kiro base-persona confound (constant across arms). Direction/localization only,
not magnitudes. A positive closing-side result → re-test cleanly on OpenRouter (`coupled` vs a
permit-derive `coupled` arm) with full temp/seed control before any claim.
