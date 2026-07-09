# P7 high-N matrix — SESSION-3 HANDOFF (cross-family generality + Haiku + kiro YOLO)

Read this top-to-bottom. Then skim `experiments/p7_split_unit/PRE-REG.md` (design) and
`FINDINGS-14B-OVERFLOW.md`. Memory files (auto-loaded) summarize the same state.
**NOTHING IS PUBLISHED — surface results for review before any conclusion.**

---

## 0. TL;DR — where we are

- **Qwen scale ladder DONE & certified**: 7B, 14B, 72B (all n=10). The 72B rung came back
  **INCONCLUSIVE** (compose not robustly rescued by scale; details in §3).
- **THIS SESSION launched a CROSS-FAMILY generality test** — does the record→retain→compose chain
  travel beyond Qwen, or is it Qwen-specific? Six **clean** non-Qwen families via OpenRouter:
  `llama70b` (Meta-70B), `gpt4omini` (OpenAI), `novalite` (Amazon), `commandr` (Cohere),
  `mistral24b` (Mistral), `haiku45` (Anthropic Haiku-4.5). All verified **non-thinking** + pass the
  compose-ceiling. Plus a **separate, quarantined KIRO YOLO** batch (§6).
- **CROSS-FAMILY RESULTS ARE IN (preliminary — §4).** Headline: the **close-time recombination
  bottleneck is GENERAL, not Qwen-specific.** Strong-follower families RECORD+RETAIN the table reliably
  (often *better* than Qwen) but COMPOSE near-zero: Llama-70B 9/9 record → **1/9 compose**, GPT-4o-mini
  9/10 → **0/10**, Nova-Lite 9/10 → **0/10**. The "records-but-won't-recombine" fingerprint reproduces
  cleanly across Meta / OpenAI / Amazon — strongly on-thesis for "a custom model must target the CLOSE."
- **⚠ COMPLETENESS + OPENROUTER CREDIT EXHAUSTED.** The headline is **solid on 4 well-powered clean
  families — `llama70b` (n=9), `gpt4omini` (10), `novalite` (10), `commandr` (9).** But **`mistral24b`
  and `haiku45` are STUCK at n=3**: the top-up RateLimitStopped because the **$10 OpenRouter credit is
  fully spent ($10.29 used).** To finish those two (or run anything else on OpenRouter) the **user must
  top up credit** — until then treat mistral/haiku as preliminary n=3 (and note haiku's lower
  op-following 3.5 means even at n=10 read its zeros cautiously). The validity gate (§1b) was **not**
  run this session — run it on the 4 complete families before final write-up. kiro models cost nothing
  (user's kiro tokens), so a kiro top-up needs no OpenRouter credit.

---

## 1. FIRST ACTIONS (do these, in order)

```powershell
$P = "D:\Context diffusion\p7 extra tests"
$PY = "$P\.venv\Scripts\python.exe"
cd "$P\experiments\p7_split_unit"

# (a) What finished? Count spec+neutral files per model (clean cross-family want 10 each; kiro want 1 spec).
foreach ($m in 'llama70b','gpt4omini','novalite','commandr','mistral24b','haiku45',
               'haiku45_kiro','minimax_kiro','glm_kiro','deepseek_kiro','qwen3coder_kiro') {
  $s = (Get-ChildItem -Filter "p7_results_${m}_spec_s*.json" -EA SilentlyContinue).Count
  $n = (Get-ChildItem -Filter "p7_results_${m}_mp6_neutral_s*.json" -EA SilentlyContinue).Count
  Write-Output ("{0,-16} spec={1} neutral={2}" -f $m,$s,$n)
}
# If any clean model is < 10/10: re-launch it (resumable, skips done seeds):
#   $env:OPENROUTER_API_KEY='<the key the user pasted this session — ask them>'; $env:PYTHONIOENCODING='utf-8'
#   & $PY run_matrix.py --model <model> --n 10 --tests neutral,specifics
```

```powershell
# (b) VALIDITY GATE each CLEAN model (must PASS before trusting any number). expect-provider per §4.
& $PY validate_72b.py --model llama70b  --n 10 --expect-provider DeepInfra
& $PY validate_72b.py --model gpt4omini --n 10 --expect-provider OpenAI
& $PY validate_72b.py --model novalite  --n 10 --expect-provider "Amazon Bedrock"
& $PY validate_72b.py --model commandr  --n 10 --expect-provider Cohere
& $PY validate_72b.py --model mistral24b --n 10 --expect-provider DeepInfra
& $PY validate_72b.py --model haiku45    --n 10 --expect-provider "Amazon Bedrock"
# (Do NOT validate *_kiro — n=1, no neutral files, provider="kiro:..." → it will "fail" trivially. §6.)
```

```powershell
# (c) SUMMARIZE the clean 6-family contrast beside the Qwen ladder (summarizer now prints OP-FOLLOWING):
& $PY summarize_p7.py --model 7b --model 14b --model 72b `
    --model llama70b --model gpt4omini --model novalite --model commandr --model mistral24b --model haiku45
# (d) kiro yolo, SEPARATELY (clearly labelled, never beside the clean rungs):
& $PY summarize_p7.py --model haiku45_kiro --model minimax_kiro --model glm_kiro --model deepseek_kiro --model qwen3coder_kiro
```

Then read the results through the lens in **§4** and surface to the user.

---

## 2. The experiment in one paragraph

P7 "split-unit" (code domain). A multi-pass reader builds an INTEGRATION STATE across K passes from
partial VIEWS of a codebase. **Money comparison = `coupled_full` vs `verbatim_only` on the closing
`ANSWER == 2353`** (GT: `compute_line_surcharge(23)` = REGION_SURCHARGE_CENTS[23] `988` +
RECONCILIATION_ADDER_CENTS `1365` = `2353`). Chain per seed (coupled): **RECORD** (the mapping `23:988`
ever enters state) → **RETAIN** (survives to final state) → **COMPOSE** (closing == 2353).
**State-D guard**: a *clean* coupled compose requires the mapping to first appear in a **Phase-A** pass
(`Dgd=A`, the frozen scaffold) — not a Phase-B raw tile (`Dgd=B`, which the verbatim control could also
do). `coupled_full` gets both fragments early via the frozen Phase-A scaffold; `verbatim_only` (raw
tiles, no scaffold) is the control. Draws per model: temp-0 seed 42 + (n-1) temp-0.7 seeds; reported
per-seed, never pooled.

---

## 3. Certified Qwen ladder results (the baseline; regenerate via §1c)

| metric | **7B** (Q4 local) | **14B** (Q4 local) | **72B** (DeepInfra fp8) |
|---|---|---|---|
| RECORD (coupled ever logs `23:988`) | 3/10 | **8/10** | 4/10 |
| RETAIN (both fragments in final state) | 3/10 | 8/10 | 4/10 |
| **COMPOSE** (closing ANSWER==2353) | **0/10** | **1/10** (seed4) | **2/10** (seeds 2,3) |
| — of which **clean Phase-A State-D** | 0/10 | 0/10 | **1/10** (seed2 only) |
| coupled vs verbatim on 2353 | 0 vs 0 | 1 vs 0 | 2 vs 1 |
| neutral (un-prompted record) | 0/10 | 0/9 | 0/10 |

**72B read = INCONCLUSIVE.** COMPOSE ≤2/10 at every scale; every compose is a temp-0.7 tail event; the
**temp-0 anchor (seed 42) composes 0 at all three scales**; cleanly scaffold-attributable compose is
0/0/1. So composition is **not robustly rescued by scale**. Two real secondaries: (1) **RECORD is
non-monotonic 3/8/4** — the 72B abstracts more and writes the verbatim table LESS than the 14B, so this
is not a clean capacity ladder; (2) the control (`verbatim_only`) composed once at 72B (first non-zero
control at any scale). ⚠ The 72B's FIRST run was silently corrupted (provider fan-out + client bugs;
RECORD came back 1/7); it was deleted and re-run clean on pinned DeepInfra. See memory
`p7-openrouter-api` → RUN INTEGRITY.

**User's actual bar (important):** the user is NOT chasing statistical conclusiveness. The target is a
**hard "maybe"** — *can the architecture EVER fire the full chain via the intended scaffold, even once,
so a custom-trained model "might" work (>0)?* That bar is **already cleared & verified**: 72B seed-2 is
a complete clean Phase-A scaffold record→retain→compose, and all compose events are genuine reasoning
from state (each pulls 988 + 1365 and sums to 2353), not coincidence. The cross-family run asks whether
that existence + the failure-fingerprint **generalize**.

---

## 4. THE CROSS-FAMILY TEST — RESULTS + framing (the key section)

**RESULTS (preliminary; regenerate via §1c; `mistral24b`/`haiku45` were topping up at session end).**
ops/pass = mean coupled op-following; "rec/ret/A/comp" = RECORD / RETAIN / clean-Phase-A-State-D / COMPOSE.

| family (key) | n | ops/pass | RECORD | RETAIN | State-D(A) | **COMPOSE** | verbatim | neutral |
|---|---|---|---|---|---|---|---|---|
| Meta `llama70b` | 9 | 9.3 | **9/9** | 9/9 | **9/9** | **1/9** | 0/9 | **5/9** |
| OpenAI `gpt4omini` | 10 | 9.2 | 9/10 | 9/10 | 9/9 | **0/10** | 0/10 | 4/10 |
| Amazon `novalite` | 10 | 10.0 | 9/10 | 8/10 | 7/9 | **0/10** | 0/10 | 0/10 |
| Cohere `commandr` | 9 | 8.7 | **0/9** | 0/9 | 0/9 | 0/9 | 0/9 | 0/10 |
| Mistral `mistral24b` | 3⚠ | 9.2 | 1/3 | 1/3 | 1/1 | 1/3 | 0/3 | 0/4 |
| Anthropic `haiku45` | 3⚠ | 3.5 | 1/3 | 1/3 | 1/1 | 0/3 | **2/3** | 0/4 |
| *(Qwen ref)* 72B | 10 | 4–20 | 4/10 | 4/10 | 1/10 | 2/10 | 1/10 | 0/10 |

**The read (preliminary):**
- **Recombination is the universal bottleneck.** The three best-n strong followers (Llama, 4o-mini,
  Nova) RECORD+RETAIN cleanly via the Phase-A scaffold — **better than Qwen ever did** (Llama 9/9 vs
  72B 4/10) — yet COMPOSE 1/9, 0/10, 0/10. So the scaffold's record→retain mechanism GENERALIZES well;
  the failure is specifically the **close-time recombination**, in 3 independent families. This is the
  architecture-limited fingerprint, reproduced — the cleanest evidence yet for "a custom-trained model
  would need to target the close step," and it answers the generality question the run was built for.
- **`commandr` is a different failure** (records 0/9 — follows the op-DSL but never captures the
  arbitrary table value; a RECORD failure, not a compose one). Keep it distinct in the writeup.
- **`mistral24b` is NOT a weak follower** after all (9.2 ops/pass over a full run; the upfront verify's
  "1 op/pass" was a single-pass fluke — drop the "footnote-only" label once it reaches n=10).
- **NEUTRAL is non-zero for Llama (5/9) and 4o-mini (4/10)** — those families record the table even
  un-prompted, unlike Qwen/Nova/Cohere (0). A real family difference in eagerness-to-record; note it.
- **`haiku45` (n=3, thin):** lower op-following (3.5), coupled composed 0/3 but verbatim 2/3 (control
  beat coupled) — too thin to read; **wait for the n=10 top-up.**
- **CAVEAT:** validity gate not yet run (§1b); and 2 models are n=3. Treat as preliminary; re-validate +
  re-summarize after the top-up before surfacing as final.

**The reframe (do not skip — it changes the writeup).** The compose-ceiling check already proved every
family CAN compose `2353` from a clean handed state. So the run does **NOT** test "does composition
generalize" — it tests whether the **scaffold + edit-op DSL implementation** carries the planted fact
through the multi-pass process to the close. That is **dominated by op-protocol following**, which is a
prompt-engineering artifact, NOT intelligence or architecture.

**Therefore: read every per-family number THROUGH op-following.** The summarizer now prints
`OP-FOLLOWING (coupled): mean N ops/pass`. A family near **~1 op/pass IGNORED the DSL** → its
state never builds → its 0 RECORD/COMPOSE is a **protocol-transfer failure, NOT architecture evidence**.
Pre-measured op-following (from the upfront verify) — interpret zeros only for healthy followers:

| family | model key | ops/pass (verify) | read its zeros? |
|---|---|---|---|
| Meta Llama-3.3-70B | `llama70b` | **21 (strong)** | YES — **the clean scale-matched comparison vs 72B** |
| OpenAI GPT-4o-mini | `gpt4omini` | **20 (strong)**, recorded 988 on pass 1 | YES |
| Amazon Nova-Lite | `novalite` | **12 (strong)**, recorded 988 on pass 1 | YES |
| Cohere Command-R | `commandr` | 4 (moderate) | with caution |
| Anthropic Haiku-4.5 | `haiku45` | TBD (kiro smoke showed ~4–5; read from results) | YES if healthy |
| Mistral-Small-24B | `mistral24b` | **~1 (WEAK)** | **NO — protocol-transfer; FOOTNOTE only** |

**What to look for, in priority order:**
1. **Llama-70B vs Qwen-72B** (the one clean comparison: same ~70B scale, different family, strong
   follower). Does Llama RECORD? RETAIN? COMPOSE? Clear **clean Phase-A State-D** (`Dgd=A`)?
2. **Does ANY strong-follower family clear clean Phase-A State-D compose** — the bar only Qwen-72B-seed2
   ever cleared (0/0/1 across the whole Qwen ladder)? If yes → existence generalizes. If no → the clean
   scaffold mechanism is essentially Qwen-specific-and-rare.
3. **Does the "fingerprint" reproduce** — records + retains but **won't recombine at the close**? If
   strong followers reproduce records-but-no-compose, that's the **same architecture-limited
   recombination signal in a 2nd/3rd family** — arguably MORE informative than scattered composes, and
   directly on-thesis for "a custom model would target the close-time recombination step."
4. **coupled vs verbatim** per family (does the scaffold beat the raw-tile control), and **neutral**
   (should be ~0 everywhere).
5. **Pre-commit before looking:** weak-follower (Mistral; maybe Command-R) zeros are protocol-transfer,
   **not** architecture — keep them out of the headline; Mistral is a cheap caveated footnote.

**Validity gate first (§1b).** At these models' large contexts nothing legitimately overflows, so the
gate's rule holds: **ANY truncation = corruption, not a finding**; fix/re-run before trusting numbers.

---

## 5. Haiku-4.5 (`haiku45`) — the 6th CLEAN family

Anthropic Claude Haiku 4.5 via OpenRouter → **Amazon Bedrock** (pinned). Verified **non-thinking**
(`reasoning_tokens: 0`) and clears the compose-ceiling. It is a real clean rung in the §4 comparison
(full temp/seed control, validated pipeline). Treat it like the other five strong-ish followers; read
its op-following from the results.

---

## 6. KIRO YOLO — quarantined; read SEPARATELY, never in the clean table

The user wanted to spend spare kiro-cli tokens on a "yolo" probe. Run via `kiro-cli chat
--no-interactive` (new `KiroClient` in `src/pca/llm.py`; `run.py` branches on `kiro: true`; prompt fed
on **stdin**; Kiro's ANSI/`> ` chrome stripped from stdout). Models (n=1, specifics only, seed 42):
`haiku45_kiro`, `minimax_kiro`, `glm_kiro`, `deepseek_kiro`, `qwen3coder_kiro`.

**Why it can NEVER join the clean comparison:** kiro wraps every call in **its own agent harness** (its
system prompt + tools) AND exposes **no temperature / seed / max_tokens** — so it can't reproduce the
temp-0/temp-0.7 draw design, can't do the temp-0 anchor, and isn't rate-comparable. It is an
**existence/fingerprint curiosity ONLY**. Read it through the same RECORD→RETAIN→COMPOSE + op-following
lens (the smoke showed Haiku-via-kiro DOES follow the op-DSL at ~4–5 ops/pass), but label it loudly as
"KIRO YOLO (confounded)" and keep it physically apart from the clean rungs. Some kiro models may be
thinking models (user explicitly OK'd including them as yolo) — their output may carry reasoning text;
parse tolerantly. Do NOT run `validate_72b.py` on `*_kiro` (n=1, no neutral, provider="kiro:..." →
trivial fail).

**KIRO YOLO results (n=1 each, CONFOUNDED — curiosity only, do NOT compare to the clean table):**
coupled COMPOSE on the single seed — `haiku45_kiro` 1/1 (clean State-D), `minimax_kiro` 1/1 (but
RECORD 0/1), `glm_kiro` 0/1, `deepseek_kiro` 1/1, `qwen3coder_kiro` 0/1; the verbatim *control* also
composed on minimax/glm/deepseek (1/1 each). n=1 + agent-harness + no-temp-control → unreadable as
rates; the only honest takeaway is "the chain CAN fire via kiro for several families on a single shot."
Tokens were the user's spare kiro credits. Leave as a labelled footnote.

---

## 7. Code / infra changed this session (so you understand repo state)

- **`src/pca/llm.py`**: `OpenRouterClient` HARDENED after the 72B corruption — only a GENUINE
  context-overflow 4xx (`"maximum context length"` / `"reduce the length"`) truncates; any other 4xx/5xx
  / network / **200-with-empty-choices** is transient → backoff+retry (≤10 attempts) → then
  `RateLimitStop` (clean). Added `provider_order`+`allow_fallbacks` (pin one upstream) and per-call
  `provider` in the return. **NEW `KiroClient`** (see §6).
- **`run.py`**: branches `kiro:` → `KiroClient`, else `api:` → `OpenRouterClient`, else `LlamaServer`.
  Saves `provider` per pass / closing / dense.
- **`config.yaml`**: clean cross-family entries (`llama70b` pin DeepInfra, `gpt4omini`, `novalite`,
  `commandr`, `mistral24b` pin DeepInfra, `haiku45` pin "Amazon Bedrock") + kiro entries (`*_kiro`,
  `kiro: true` + `kiro_model:`). Provider-pin entries use `api_provider_order: [X]` +
  `api_allow_fallbacks: false`.
- **`summarize_p7.py`**: now prints **OP-FOLLOWING** (mean ops/pass; flags ~1 as protocol-transfer).
- **`validate_72b.py`**: the validity gate (FAILs on missing arm / ANY truncation / closing overflow /
  wrong provider / RECORD-positive-but-fragment-missing). Args `--model`, `--n`, `--expect-provider`.
- **OpenRouter**: the user's key (PASTED in this session's chat — NOT stored in repo; ask the user or
  reuse from their notes; set `$env:OPENROUTER_API_KEY`). Credit at last check **≈ $3.7 remaining of
  $10**. Anthropic/Bedrock/DeepInfra/etc. pricing is cheap; clean Haiku ≈ $0.5–1.
- **kiro-cli**: `C:\Users\Boz\AppData\Local\Kiro-Cli\kiro-cli.exe` (user logged in; uses their tokens).
  Models via `kiro-cli chat --list-models -f json`. No code/key needed.
- Environment unchanged: `.venv` (py3.10), local Q4 7B/14B GGUFs, llama.cpp junction → `D:\llm\bin`.

---

## 8. Discipline reminders

- Only the COMPRESSOR/architecture is varied — never the prompt or "how the model thinks." **No thinking
  models in the clean set** (all 6 verified non-thinking; effort/reasoning OFF). Kiro yolo is exempt
  (explicitly confounded).
- **Validity gate before headline numbers.** Any truncation at these contexts = corruption.
- **Read per-family numbers through op-following.** A ~1-op/pass zero is protocol-transfer, not
  architecture.
- Report per-seed, never pooled. Nothing published — surface for review.
- Result files: `p7_results_<model>_spec_s*_t*.json` (specifics: dense/verbatim_only/coupled_full),
  `p7_results_<model>_mp6_neutral_s*` (neutral), `matrix_<model>.log` (per-model run log).
- Background-run cadence learned the hard way: latency estimates feel longer than wall-clock — check
  `(Get-Date)` vs the log's last-write before declaring a run "stuck."
