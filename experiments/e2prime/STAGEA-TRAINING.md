# Stage-A student training — run record

Student: Qwen2.5-1.5B-Instruct + LoRA (r=16 α=32 dropout=0.05, all attn+MLP projections),
lr 1e-4 cosine, warmup 0.03, epochs 2, batch 1 × accum 16, fp32 compute (Pascal sm_61),
split-by-doc eval 5% (seed 42). Data: `stageA_coupled.jsonl` (5,730 rows / 277 docs).
Hardware: GTX 1080 Ti 11GB, shared desktop card, WSL2 venv.

## Run 1 (2026-07-12 → 07-14): completed, P-C FAILED — root cause found, superseded

- `--seq-len 4096` (the pre-registered engineering default), `runs/stageA_coupled/`.
- Ops incidents, all recovered by step-checkpointing (`save_steps=25`, commit ff200e0):
  OOM at step 228 (full-card allocation failure; mitigated with
  `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`), OOM at step 338 = the epoch-1
  boundary eval (HF default eval batch 8 × seq-4096 rows; fixed to eval batch 1,
  commit c78a30c). Resumes lost ≤13 steps; final leg ran 11.3h unattended.
- Final: train_loss 0.2857, eval_loss 0.2016 (epoch 1: 0.2043).
- **P-C health check (served fp16 GGUF via llama.cpp, `pc_check --server`, 322 held rows):
  validity 0.9343 (bar ≥0.95), agreement 0.6025 (bar ≥0.75) → TRAINING FAILURE.**
  Worst-agreement docs: all synthcode.

### Post-mortem

TRL 1.8 `SFTTrainer` truncates prepared rows to `max_length` with default
`truncation_mode="keep_start"` — it keeps the FIRST 4,096 tokens. Our rows are
`[prompt][completion]` with the completion at the end; teacher prompts (state block +
view + grammar) run to 24K tokens on code docs. Exact per-slice damage (Qwen tokenizer,
full prompt+completion length):

| slice | rows | fit ≤4096 whole | completion PARTIALLY cut | completion FULLY cut (no signal) |
|---|---|---|---|---|
| govreport | 1,080 | 99.9% | 0.1% | 0.0% |
| realcode | 2,043 | 22.6% | 3.7% | **73.8%** |
| synthcode | 2,607 | 17.3% | 1.8% | **80.9%** |

The student trained on prose plus the short minority of code rows; mid/late-schedule code
behaviour was never in the loss. This exactly reproduces the P-C shape: validity 0.934
(op grammar generalises from prose), agreement collapsed to 0.60 concentrated in
synthcode. The clean-looking eval_loss (0.2016) averaged over the same surviving-row
subset and could not surface the problem. Corroboration: llama.cpp rejected held prompts
> 16K during the first serve attempt; token-length audit (this table) matches.

The failure is a HARNESS defect (data preparation), not a capability observation.
Per E2PRIME-CRITERION §1 P-C: fix data/hyperparameters and retrain; no capability fork.

## Run 2 protocol (pre-committed 2026-07-14, before launch — D34)

1. **Length gate replaces truncation** (train_lora.py): every row is tokenized up front;
   rows whose full prompt+completion exceed `--seq-len` are EXCLUDED and logged per slice
   in `split.json`. No kept row can be touched by truncation. Never train through silent
   truncation again.
2. **Window = 10,240** (fallback 8,192 only if the VRAM probe fails): covers the §3 gate
   altitude (fixture prompts ≈ ≤8.5K: state ≤4000 + V=3000 view + grammar/demand) with
   margin, and retains 74.8% of rows (govreport 100%, realcode 83.6%, synthcode 57.4%).
   Dropped rows are all long-tail late passes of the biggest code docs — outside anything
   the gates pose. Position-conditioning coverage note: high-k examples remain present
   via prose (K=8, all fit) and smaller code docs; monster-doc late passes are the loss.
3. All other hyperparameters unchanged from the pre-registered defaults.
4. **P-C re-run protocol, fixed now**: bars scored on held-out rows whose full length fits
   the training window (the trained envelope, which contains the gate altitude);
   over-window held rows reported separately as an out-of-envelope appendix, not counted
   toward the bars. Same bars (validity ≥0.95, agreement ≥0.75), same served-GGUF mode.
5. Output: `runs/stageA_coupled_v2/`.

Run-1 artifacts are retained (`runs/stageA_coupled/`, pc_check.json mode=server-gguf) as
the audit trail of the defect.

### Run-2 feasibility probes (2026-07-14, pre-launch — the 11 GB wall, measured)

Sequence-length probes on the idle card (fwd/bwd through the exact training config):

- **Stock SDPA**: fp32@8192, fp16@8192, fp16@10240 all OOM. Pascal (sm_61) has no fused
  attention; torch's math backend materialises the n² score matrix in fp32 for BOTH input
  dtypes (half inputs are upcast for softmax).
- **Chunked causal SDPA built** (`train/chunked_attn.py`, flash-style online softmax,
  q-block nested checkpointing; equivalence-gated fwd+grads vs stock at 2e-5/5e-5 fp32 —
  `train/test_chunked_attn.py`, all cases pass). Attention memory solved.
- **fp32@10240 with chunked attention still OOMs** — the next wall is dtype-fundamental:
  fp32 weights (6.2 GB) + 28-layer boundary activations at 10K (1.8 GB) + the LM-head
  logits path ([1, 10240, 151936] fp32 = 6.2 GB, plus the CE fp32 copy) exceed 11 GB.
  **Full-corpus-window fp32 training does not fit this card. Fork presented to the
  maintainer** (options a/b/c below); no run-2 launch until decided.

  (a) rent a 24-48 GB cloud GPU for the 1-2 day run — stock kernels, pre-registered fp32
      preserved, ~US$15-30;
  (b) local fp16 mixed precision + chunked attention + a chunked cross-entropy (transformers
      upcasts full logits to fp32 for CE — must be chunked too) — free, ~2-2.5 days, three
      deviation surfaces (dtype dynamics, custom attention [validated], custom loss);
  (c) local fp32 at a ~6144 window — free, stock-ish, but the gate altitude (~8.5K prompts)
      is then OUTSIDE the trained envelope and synthcode retention drops to ~25-30%: weak.
