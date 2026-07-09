# P7 — SESSION-4 CLOSEOUT & consolidation entry-point (2026-06-25)

**START HERE next session.** This supersedes `HANDOFF.md` §0 for *status* (HANDOFF's experiment
description/§2 still valid). Nothing published. Full consolidation to be done by the user next session.

## THE VERDICT (the question the whole test set out to answer)
Goal was binary-ish: prove the architecture is **unfeasible**, or that it's **possibly feasible with a
trained model** (a hard "maybe" / existence > 0). **Result: NOT unfeasible → possibly feasible with a
trained model.**
- **"Unfeasible" is ruled out.** The full record→retain→compose chain fires *genuinely* (hand-verified,
  not coincidence), *blind & untrained*, in **3 independent families**: Qwen-72B (s2), Meta-Llama-70B (s9),
  Mistral-24B (s42 — the only temp-0 deterministic-anchor compose in the study).
- **Reliability is the open gap, not capability.** Blind models RECORD reliably but COMPOSE rarely &
  stochastically (~0–12% from a held state). The cheap prompt-only fixes are NULL (gut check).
- **Training is the untested next step.** We varied prompts/architecture/scale/family — never weights. So
  "a trained model would work" is the motivated, untested hypothesis the existence result makes rational.
  Do NOT assert it as a result.

## DURABLE DOCS — read order for consolidation
1. `SESSION-4-RESULTS.md` — clean cross-family matrix, full n=10, validity-gated. Headline: close-time
   recombination is the general bottleneck (Meta/OpenAI/Amazon records-but-rarely-composes); existence
   generalizes (Llama s9, Mistral s42). Includes the recombination-vs-retention split and the
   money-comparison-null + stochastic-close caveats.
2. `GUTCHECK-PREREG.md` + `GUTCHECK-RESULTS.md` — the awareness "midpoint" probe (kiro + clean novalite).
   Verdict: BOTH prompt levers (recorder-position, closing-permission) NULL → prompt-injected awareness
   does NOT substitute for training. Mechanism ("needs the binding in state") NOT isolable (confounded).
   kiro is confounded throughout (same model 2/10 clean → 5/5 kiro).
3. `HANDOFF.md` — original design (§2) + Qwen ladder (§3) + cross-family framing (§4). Status parts stale.
4. `FINDINGS-14B-OVERFLOW.md`, `experiments/p7_split_unit/PRE-REG.md` — earlier design/integrity notes.

## CAUTIONS to carry into the writeup (advisor-checked)
- **Stochastic close:** every per-seed compose is one draw; re-sampling a fixed held state composes
  ~0–12%. Small cross-family compose-count diffs are noise — lean on the qualitative pattern.
- **Mechanism not isolated:** can't pin failure on "binding absent" — kiro-neutral had formula-in-state yet
  INSUFFICIENT; the one 5/5 cell is confounded on 3 axes (guidance × platform × formula).
- **kiro = confounded** (no temp/seed; base persona): existence/curiosity only, never a clean rung.
- **gpt4omini** clean-rung caveat: ran Azure+OpenAI (unpinned) — valid-with-caveat.

## HOUSEKEEPING / repo state
- OpenRouter credit ≈ **$2** left; **all API runs STOPPED**. kiro key the user pasted is **not needed →
  delete it**. The OpenRouter key lives only in env during runs (not in repo).
- Code added this session (kept, backward-compatible): `KiroClient` gains `--agent`/`--effort`;
  `run.py` gains `--inject-pos`/`--permit-derive` (config-toggled via `kiro_agent/kiro_effort/inject_pos/
  permit_derive`); custom kiro agent `~/.kiro/agents/p7raw.json` (empty prompt, no tools).
- Gut-check config entries: `haiku_gc`, `haiku_gc_close`, `haiku_gc_rec`, `novalite_pd`, `novalite_rec`.
- PARTIAL/throwaway result files from stopped arms (safe to delete during consolidation):
  `p7_results_novalite_pd_spec_*`, `p7_results_haiku_gc_close_spec_*`, `p7_results_haiku_gc_rec_spec_*`.
- Analysis scripts (scratchpad, may need re-creating): closing_lever_test.py, closing_multisample.py,
  classify_arms.py — all free local re-runs.

## NEXT-SESSION OPTIONS (user's call; no runs taken without go)
(a) the actual fine-tune / LoRA to test the training hypothesis cleanly (the real next experiment);
(b) free local cross-tab formula-in-state vs compose across all seeds (expect platform-confounded);
(c) just consolidate & write up — the feasibility question is already answered.
