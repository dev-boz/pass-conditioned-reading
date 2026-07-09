# Awareness gut-check — RESULTS (2026-06-25). GUT CHECK ONLY / confounded / nothing published.

Companion to `GUTCHECK-PREREG.md`. kiro = confounded (no temp/seed; residual base persona).

## Baseline (`haiku_gc`: kiro claude-haiku-4.5, p7raw agent, effort low; n=5, specifics)
| metric | value |
|---|---|
| coupled COMPOSE (==2353) | **5/5** |
| both operands in final state | 5/5 |
| INSUFFICIENT | 0/5 |
| verbatim_only compose | 3/5 (one 2004, one None) |
| coupled op-following | 3.1 ops/pass |

## Two findings (both significant)

**1. Huge harness confound — no headroom.** The SAME model (Claude Haiku 4.5) composes **2/10 on the clean
OpenRouter/Bedrock path** but **5/5 via kiro** (p7raw base persona + effort low + kiro serving). Coupled even
beats verbatim here (5 vs 3), the reverse of the clean path (2 vs 7). So kiro-haiku has no failure for the
awareness levers to fix — the two lever arms (`haiku_gc_close`, `haiku_gc_rec`) were ceiling-bound and were
**stopped**. It also vividly demonstrates *why* kiro can never join the clean table.

**2. Composition tracks BINDING-survival in state (confirms §3 from the success side).** The kiro-haiku
closing that composed cited **S72 — the formula itself**: *"compute_line_surcharge(region_code) → base +
1365"* — then did `988 + 1365 = 2353`. The clean-path failures (llama70b etc.) hold 988 and 1365 but **not
the formula**, and return bare 988. So the discriminator between compose and fail is precisely whether the
**relational binding** (`surcharge = table[code] + adder`) survives compression into the state — exactly the
§3 claim, now shown from a positive case, not just inferred from failures.

## Implication for the levers
- **permit-derive (closing-side)** and **inject-pos (recorder-side)** must be tested on a model that
  **fails at baseline** with the both-operands-held-but-no-formula pattern. That is the clean OpenRouter
  set, NOT kiro-haiku. Best target: **`llama70b`** (9/10 both-held-not-summed, formula dropped, verbatim
  0/10 — cleanest headroom); cheap alternatives **`novalite`/`gpt4omini`** (6/10 headroom).
- Sharpened prediction for permit-derive: it helps only if the model *suspects* the relationship but is
  suppressed by "do not invent." If the formula is genuinely absent from state, permission to compute won't
  supply the missing relationship → permit-derive may be near-null, which would re-point the fix to
  **recorder-side formula-preservation** (what kiro's harness accidentally achieved, and what training would
  target). Either outcome is clean and informative.

## Lever A/B verdict (clean OpenRouter, isolated tests) — BOTH LEVERS NULL

**Recorder-side `inject-pos` (novalite n=10 vs baseline): NULL.** COMPOSE 0/10 → 0/10; both-held 6 → 4
(noise); no improvement. Salient position/coverage does nothing — expected, since the baseline already
gives position + architecture + a keep-relationships rubric.

**Closing-side `permit-derive`: NULL (no reliable compose gain).** Tested cleanly by holding the recorded
state FIXED and re-running only the closing:
- llama70b single-shot looked promising (2 INSUFFICIENT seeds → 2353) — but **multi-sampling refutes it**:
  on fixed held state s2, baseline `{INSUFF:4,988:3,2353:1}` = 1/8 compose vs permit-derive 0/8; s7
  baseline 0/8 vs permit-derive 0/8. The "flips" were stochastic luck.
- novalite (6 both-held, 5 INSUFFICIENT): permit-derive flipped INSUFFICIENT → **988/1365 (bare lookups),
  not 2353** — COMPOSE 0/6, zero flips. It changes the *failure mode*, not the outcome.
- So relaxing "do not invent" does NOT supply the missing relationship; permission to compute ≠ knowing
  what to compute.

**The close is stochastic with a LOW compose rate from an operands-only state (~0–12%).** Composition
isn't *suppressed* by the prompt (permit-derive doesn't unlock it); the model just rarely infers that the
two held values should be summed — because the **binding/formula isn't in state.**

## Synthesis (bounded — what the data can and cannot support)

**Clean, well-supported — the answer to the midpoint question:** both injected levers are NULL. Minimal
prompt-injected "awareness" did not move the outcome. Lead evidence: closing-side permit-derive on
**novalite = 0/6** (clean Bedrock; it turned INSUFFICIENT into a bare lookup 988/1365, never 2353);
recorder-side inject-pos on **novalite = 0/10**. (The llama70b single-shot "2 INSUFFICIENT → 2353" looked
positive but multi-sampling two held states showed permit-derive 0/8 and 1/8→0/8 — the flips were
stochastic; note multi-sample did not re-test those exact seeds, so treat it as non-support, not a hard
refutation.)

**Direction (supported):** recorder/guidance-side matters; closing-side does not. kiro-haiku composes
**5/5 under the specifics prompt but 0/5 under the neutral (lower-guidance) prompt** — a guidance effect on
the recorder — while both *injection* levers (recorder-position, closing-permission) are null.

**Mechanism (NOT isolable — do NOT over-claim "binding").** Tempting to say "composition needs the binding
in state," but our own data blocks it:
- kiro-NEUTRAL had the formula in state (crude detector) on s1/s2/s4 yet answered INSUFFICIENT 0/5 — so
  binding-in-state did NOT yield composition within that model.
- the one reliably-composing cell (kiro-haiku specifics 5/5) differs from the failing cells on THREE
  confounded axes at once — guidance, platform/harness (kiro vs clean), formula-in-state — so 5/5 cannot
  be attributed to binding alone.
- the formula detector is a crude substring check that does NOT cleanly track compose across our seeds, so
  it cannot carry a mechanism claim.
What we CAN say: **composition is unreliable from an operands-only state (~0–12% per held state, stochastic),
and no prompt-level lever fixed it.**

**On training:** we varied PROMPTS, not WEIGHTS. So "a trained model would carry the binding" remains the
untested next step — prompt-injected awareness is not a substitute, but whether training helps is not
something this probe measured. State it as the open question, not a result.

## Status: gut check COMPLETE. Nothing published. Confounded (kiro) / small-n / 2-state multi-sample —
direction only. Do NOT edit SESSION-4 §3 numbers from this probe (one stochastic-close caveat line only).
