# P7 cross-family — SESSION-4 RESULTS (full n=10, validity-gated, compose-verified)

Status: **PRELIMINARY / NOTHING PUBLISHED — surface for review.** This session: ran the validity gate
(skipped in S3), **completed all 6 cross-family rungs to n=10** after the user topped up OpenRouter
credit, re-gated, re-summarized, and hand-verified every headline compose + every verbatim-control
compose. Read alongside `HANDOFF.md` (§4 framing holds and is now better-powered).

Key interpretive frame (user, this session): **the models are blind to the architecture.** Nobody tells
them they are doing record→retain→compose; the final-pass agent does not know it is reading a thin slice.
So every compose is un-coached and zero-shot — which is why even rare composes, and the bare-`988`
lookups, are the meaningful signal. We are not engineering the compose; we are observing whether it
emerges blind.

---

## 1. Validity gate (§1b) — run at full n=10 this session

| family | n | provider (all seeds) | truncation | gate |
|---|---|---|---|---|
| Meta `llama70b` | 10 | **DeepInfra** | none | **PASSED** ✓ |
| Cohere `commandr` | 10 | **Cohere** | none | **PASSED** ✓ |
| Mistral `mistral24b` | 10 | **DeepInfra** | none | **PASSED** ✓ |
| Amazon `novalite` | 10 | **Amazon Bedrock** | none | FAIL = 2 *genuine* fragment-missing only (s3,s9) — see §3 |
| Anthropic `haiku45` | 10 | **Amazon Bedrock** | none | FAIL = 2 *genuine* fragment-missing only (s1,s3) |
| OpenAI `gpt4omini` | 10 | ⚠ **Azure + OpenAI (mixed)** | none | CAVEAT — unpinned provider fan-out (§4) |

No arm truncated anywhere → **no repeat of the 72B silent-corruption mode.** The novalite/haiku "FAILED"
banners are *only* the fragment-missing flags, which are not corruption (no truncation) — they are the
**retention** mode (records 988 but never carries 1365 into state), the *minority* failure mode, distinct
from the **recombination** majority where both operands are held and still not summed (§3).

## 2. Certified headline — full n=10 (regenerate: `summarize_p7.py`)

ops = mean coupled op-following; A-of-rec = of RECORDs, how many entered via the frozen Phase-A scaffold.

| family | n | ops | RECORD | RETAIN | A-of-rec | **COMPOSE** | verbatim | dense | neutral |
|---|---|---|---|---|---|---|---|---|---|
| Meta `llama70b` | 10 | 9.2 | **10/10** | 10/10 | **10/10** | **1/10** (s9) | 0/10 | 0/10 | 5/10 |
| OpenAI `gpt4omini` | 10 | 9.2 | 9/10 | 9/10 | 9/9 | **0/10** | 0/10 | 0/10 | 4/10 |
| Amazon `novalite` | 10 | 10.0 | 9/10 | 8/10 | 7/9 | **0/10** | 0/10 | 0/10 | 0/10 |
| Cohere `commandr` | 10 | 8.4 | **0/10** | 0/10 | 0/0 | 0/10 | 0/10 | 0/10 | 0/10 |
| Mistral `mistral24b` | 10 | 10.4 | 5/10 | 5/10 | 3/5 | **1/10** (s42) | 1/10 | 0/10 | 0/10 |
| Anthropic `haiku45` | 10 | **3.0** | 3/10 | 3/10 | 2/3 | 2/10 | **7/10** | 0/10 | 0/10 |
| *(ref)* Qwen `72b` | 10 | 7.1 | 4/10 | 4/10 | 3/4 | 2/10 (s2,s3) | 1/10 | 0/10 | 0/10 |

## 3. THE HEADLINE: compression strips the BINDING — the close answers from a binding-free state

Rests on the three **healthy strong-followers whose raw-tile control FAILS** (`verbatim 0/10`):
**`llama70b`, `gpt4omini`, `novalite`** (ops 9–10/pass). All three RECORD+RETAIN the planted fact
reliably via the Phase-A scaffold (9–10/10) — far better than the failing control — yet **COMPOSE ≤1/10.**

**Two distinct failure modes, separated by checking whether the final state actually holds BOTH operands
(`988` AND `1365`):**

| family | COMPOSE | **RECOMBINE-fail** (both operands in state, not summed) | RETENTION-fail (adder absent from state) | no-record |
|---|---|---|---|---|
| `llama70b` | 1 | **9** | 0 | 0 |
| `gpt4omini` | 0 | **6** | 3 | 1 |
| `novalite` | 0 | **6** | 2 | 2 |

**The dominant mode is RECOMBINATION failure: 22 seeds across the 3 families carried BOTH operands into
the scaffold-built state, and only 1 (llama s9) produced 2353** — the other 21 returned the bare lookup
`988` or declined (`None`/INSUFFICIENT). The cleanest case is **`llama70b`: GATE-confirmed both fragments
in state on all 10 seeds, composes 1.** Hand-read closings of the 9 llama failures (each holds 988 and
1365): seeds 1/2/3/7/8 **explicitly notice the `1365` adder and weigh combining**, then default to the
lookup — *"an addition operation might be involved … but without the exact formula … we cannot accurately
compute"* (s3 → INSUFFICIENT); *"assuming it directly relates to REGION_SURCHARGE_CENTS without additional
modifications"* (s8) → 988. The operands are present; what is missing is the **formula that binds them**.

**Mechanism — the close is NOT the dumb step; compression upstream of it is (the blind-agent frame).** The
record→retain op-DSL compression preserves the two *facts* (`23:988` and `1365`) but **strips the binding**
— that `compute_line_surcharge = REGION_SURCHARGE_CENTS[code] + RECONCILIATION_ADDER_CENTS`. The blind
close-agent, handed two separate recorded facts and no formula, conservatively returns the lookup. Two
observations pin the failure *upstream* of the close, not at it:
- the high-op followers compose **0/10 in BOTH the coupled AND the verbatim arms** — so it is their own
  aggressive op-DSL abstraction (not the scaffold specifically) that discards the formula; the failure
  tracks op-following/abstraction;
- when the binding *does* survive into state, the close composes fine — exactly what `haiku`'s verbatim
  arm shows (low-op faithful copy → the literal function body survives raw → **composes 7/10**, §5).

So the close-agent recombines when handed the binding; it returns `988` only when compression already
deleted the formula. Reproduced in **3 independent families (Meta/OpenAI/Amazon)**. The actionable thesis
answer is sharper than "target the close": **a custom model must target what survives compression — carry
the relational binding (`surcharge = table[code] + adder`), not just the atomic facts.**

A **secondary, minority mode is RETENTION failure** (5 seeds: gpt4omini s42/s3/s8, novalite s3/s9): the
`1365` adder never reaches final state, so the close *cannot* recombine. Different fix (carry both
fragments) — keep it distinct from the recombination majority. `llama70b` shows 0 of these.

**⚠ The designed money comparison is NULL on raw compose counts.** coupled-vs-verbatim composing 2353:
**llama 1v0, gpt 0v0, nova 0v0, mistral 1v1, haiku 2v7.** The scaffold does **not** out-compose the
raw-tile control by count. The positive result is specifically the **clean-Phase-A pathway** (record→retain
via the frozen scaffold → compose) that the verbatim control cannot access *by construction* (it has no
Phase-A), realized in llama s9 + mistral s42. State this plainly up front — a reviewer reads those two
columns first.

> **Stochastic-close caveat (from the gut-check follow-up, `GUTCHECK-RESULTS.md`):** each per-seed compose
> is a *single draw* from a stochastic close — re-sampling a fixed both-operands-held llama70b state
> composes only ~0–12% of the time. So small cross-family compose-count differences are within sampling
> noise; lean on the qualitative pattern (records reliably, composes rarely/unreliably), not exact counts.

`commandr` is a **different** failure — RECORD 0/10: it follows the op-DSL (ops 8.4) but never captures
the arbitrary table value at all. Keep it distinct (record-failure, not compose- or retention-failure).

## 4. Existence GENERALIZES — both composes hand-verified genuine

The clean Phase-A `record→retain→compose` chain (the bar only Qwen-72B-s2 had cleared) is cleared by
**two non-Qwen families**. Both verified as genuine reasoning (pull 988 + 1365 → 2353, cite source
modules/state IDs; `final_state` holds 988 & 1365 but NOT 2353 → the sum is composed only at the close):

- **`llama70b` seed 9** (temp 0.7, DeepInfra) — the **clean scale-match to Qwen-72B.** Llama RECORDS
  **10/10** and RETAINS **10/10**, **all via the Phase-A scaffold** (vs 72B's 4/10), yet COMPOSES 1/10
  (≈ 72B's 2/10). **Better recording buys no composition → the bottleneck is the close, not record/retain.**
  The single cleanest statement of the thesis in the whole study.
- **`mistral24b` seed 42** (temp **0.0**, DeepInfra) — the **only temp-0 deterministic-anchor compose in
  the entire study** (Qwen's anchor composed 0 at every scale). A healthy follower (ops 10.4 — NOT weak,
  retire the S3 "footnote" label). Its coupled 1/10 vs verbatim 1/10 is a *count* tie (different
  mechanisms: clean-Phase-A vs raw-tile), so mistral's contribution is the **existence proof**, not a
  scaffold-beats-control win.

Across the study, clean Phase-A composes now exist in **3 families: Qwen-72B (s2), Meta-Llama-70B (s9),
Mistral-24B (s42, temp-0).** Existence is no longer Qwen-specific.

### gpt4omini provider caveat (unchanged — user did not re-pin)
`gpt4omini` ran unpinned across **Azure + OpenAI**. Same `gpt-4o-mini` weights, so the records-but-no-
compose fingerprint is very likely robust, but it breaks the single-pinned-provider discipline. Optional
cleanup: re-pin to OpenAI in `config.yaml` and rerun n=10 (cheap). Treat the row as valid-with-caveat.

## 5. `haiku45` is CONFOUNDED — footnote only, NOT scaffold evidence

At full n=10, **verbatim control 7/10 ≫ coupled 2/10** — the control beats the scaffold. This is the
weak-follower confound the HANDOFF (§4) predicted, now confirmed:
- op-following **3.0** (below the healthy ~4–20 band). The coupled arm's state never builds well.
- All **7** verbatim composes are genuine (each pulls `23:988` + `1365` from raw tiles → 2353). So the
  task **leaks through raw tiles** for a faithful low-op copier, and **haiku IS capable** of the compose.
- Its 2 coupled composes are not clean (seed 4 = Phase-B raw tile; seed 7 = composed with **no record**).
  → **0 clean Phase-A composes.**

So haiku's low coupled compose is **protocol-transfer (weak op-following), NOT architecture.** It cannot
show a scaffold benefit because its control already solves the task. **Exclude from the headline**; the
headline rests on the three healthy followers whose control fails (§3).

## 6. kiro YOLO (confounded — footnote only)
Reproduced HANDOFF §6: single-shot chain fires for `haiku45_kiro` (1/1 clean State-D), `deepseek_kiro`
(1/1), `minimax_kiro` (1/1 but RECORD 0) — but the verbatim **control also composed** for
minimax/glm/deepseek. n=1 + agent harness + no temp control → "the chain CAN fire via kiro on a single
shot," nothing rate-comparable.

## 7. Status / what remains
- **All 6 cross-family rungs complete at n=10; gates clean (provider+truncation); composes verified.**
- The cross-family question the run was built for is **answered**: the bottleneck is general (3 families)
  — op-DSL compression strips the relational binding upstream of the close (dominant: 21/22 both-operands-held
  seeds fail to sum), with a minority retention mode — and existence generalizes (2 non-Qwen families).
- Optional only: re-pin `gpt4omini` to OpenAI to remove the §4 caveat. Nothing else blocked.
- **Nothing published.** Surface for the user's review before any external claim.
