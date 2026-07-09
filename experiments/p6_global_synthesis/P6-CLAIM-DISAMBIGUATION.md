# P6 — Claim disambiguation (STEP 1, analysis-only, $0) · 2026-06-18

**Which existence claim does P6 own?** Resolved from the 4 collected draws (1 deterministic
seed-42 temp-0 + 3 sampled seeds-1..3 temp-0.7) + the frozen `scaffold_haiku.json`. No new runs.

## Verdict

> **We own "coverage-beats-windowing." We do NOT own "scaffold-driven salience."**

- **Scaffold-driven salience — NOT owned.** The claim requires that the global scaffold causes a
  recording the cold local reader never produces. It doesn't: **`verbatim_only` (no scaffold)
  recorded a dull load-bearing test detail on its own** — D1 in the deterministic draw — and in
  that canonical greedy draw verbatim_only actually *beat* coupled_full (V got D1, C did not). So
  recording these specifics is an **arm-independent floor process**, and s2's coupled D1+D2 hit is
  a draw from that process, not evidence the scaffold caused it.
- **Coverage-beats-windowing — owned (cleanly, if modestly).** **dense (head+tail) recorded zero
  of the four mid-exclusive details across all four draws**, while the multi-pass state arms
  genuinely recorded D1, D2, and F7 (manual-verified). A multi-pass schedule surfaced and recorded
  mid-doc material a head+tail / RAG-on-endpoints reader **structurally cannot** reach. That proves
  the coverage mechanism — distinct from, and independent of, the scaffold mechanism.

## Evidence (the four questions)

**Q1 — did `verbatim_only` (no scaffold) EVER record a dull detail?** YES.
| detail | recorded by verbatim_only in |
|---|---|
| D1_timing (test) | **s42 (deterministic)** |
| C2_f7 (control) | s42 |
| D2_68pct (test) | never |
| C1_pkgcogs (control) | never |
→ verbatim surfaces dull details without the scaffold ⇒ **salience claim falls** (per the brief's
own decision rule: if verbatim also surfaces them, the coupled hit is arm-independent).

**Q2 — mid-doc details (all 4 are guard-b mid-exclusive) recorded by a state arm, dense cannot:**
| draw | arm | recorded |
|---|---|---|
| s42 | verbatim_only | D1, C2_f7 |
| s42 | coupled_full | C2_f7 |
| s2 | coupled_full | D1, D2 |
| (all) | **dense** | **nothing** |
→ multi-pass coverage recorded D1/D2/F7 that dense structurally cannot ⇒ **coverage claim holds.**

**Q3 — guard (c) re-verified vs the frozen scaffold s2 actually saw:** D1's and D2's
discriminating terms do **NOT** survive into `scaffold_haiku.json` (shared, frozen across all
draws). So s2's coupled recording is genuinely from the verbatim Phase-B tile, not from re-reading
the scaffold words. (This rules out the *coverage-masquerading-as-salience* artifact, but does not
revive salience — Q1 already disqualifies it because verbatim records arm-independently.)

**Q4 — control recording rate (the null baseline):** C1_pkgcogs = **0/4 across all arms** (floor);
C2_f7 = 2 recordings, both in s42 (verbatim_only + coupled_full), elsewhere floor.

## Honest bounds on the coverage claim
- It is partly *by construction*: the four details were selected guard-b mid-exclusive, so dense
  cannot have them — the non-trivial content is that the schedule **did genuinely record** them
  (sparse: a handful of instances across 4 draws), and dense recorded **zero**.
- It overlaps P4 but is cleaner: P4 compared recall on facts dense could partly reach (coupled ≤
  dense); P6 isolates **mid-doc-exclusive** material where dense gets zero and multi-pass gets a
  genuine (if sparse) non-zero. Modest, real, defensible.
- It is NOT the salience claim the salience-shaping design set out to test; that remains
  unanswerable on this floor and rides on E2′ ([[viability-vs-optimality]]).

## Consequence for phase-2/3 (per the brief's gating)
The brief's "What NOT to do": *don't start step 3 as written if we own coverage-but-not-salience —
the improvement gradient should target coverage recording, and step 3's framing is rewritten
first.* That applies: **step 3 must be reframed to a coverage gradient** (does the multi-pass
schedule's recording rate of mid-exclusive details improve with tweaks?), not a salience gradient.
Step 2 (lock the runner fixes + v1-vs-v2 recording-rate table) is unaffected and can proceed on
approval. **Surface this for maintainer review before step 2.**
