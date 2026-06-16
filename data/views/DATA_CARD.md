# Data card — `views.jsonl`

**Generated:** 2026-06-12 · **Generator:** `pca.gen_views` with `views_config.yaml` · deterministic (hash-seeded slice placement; no run-to-run variance)

## Source corpus
- **Dataset:** GovReport (`ccdv/govreport-summarization`, HF Hub, train split, streamed). U.S. GAO/CRS reports; public domain.
- **Why GovReport:** long single-narrative documents (median here ~11.9K tokens) so K=8 with 16–24× pass-1 compression is meaningful; clean body text; the standard public long-document corpus. (Brief offered GovReport / BookSum / QASPER / arXiv.)
- **Filter:** first 300 stream records with 8 192 ≤ tokens ≤ 24 000 (tiktoken cl100k_base). `data/corpus/corpus.jsonl` holds `{doc_id, n_tokens, text}`; `doc_id = govreport-{stream_index:05d}`.

## Views
- 300 docs × K=8 passes = **2 400 records**: `{doc_id, k, K, view_text, view_tokens, slice_tokens, slice_start_token, doc_tokens, compression_ratio, compressor}`.
- Schedule: constant view budget V=512 tokens; slice length geometric from whole doc (k=1) to 512 tokens verbatim (k=8); slice placement hash-seeded per (doc_id, k) — see `docs/DECISIONS.md` D1–D5.
- Median compression ratio by pass: 23.6, 15.2, 9.7, 6.2, 3.9, 2.5, 1.6, 1.0. Median view length ≈ 499 tokens at every pass (by construction).
- **Compressor: `extractive-sumbasic-v1` — a STAND-IN.** Production C is teacher-LLM summarization (parent §5). Everything trained on this file is **provisional** (`E0-provisional` in GATES.md).

## Contamination audit
The generator emits selected source sentences only — no headers, indices, or schedule annotations. Grep audit over the `view_text` field of all 2 400 records (patterns: `pass N of K`, `k=N`/`K=N`, `chunk N`, `govreport-\d+`, `sigma N`, `compression ratio/level/schedule`): **0 hits in every category**. (A naive grep of the raw JSONL shows 2 400 hits — those are the JSON metadata *keys* (`doc_id`, `compression_ratio`), not view content; classifiers only ever see `view_text`.) `experiments/e0_view_classifier/run.py` re-runs the same audit + strip defensively on every load and writes `audit.json`.

## Production views — `views_haiku_final.jsonl` (E0-FINAL, 2026-06-16)

The non-provisional E0 run replaces the extractive stand-in with the production
compressor **Claude Haiku 4.5** (D29). Same deterministic schedule (slices via
`pca.gen_slices`, identical D1–D5 placement); only the compression step is the LLM.
- 2 400 records, same fields **plus `gen_path`** recording the delivery path (D30):
  **`local`** 253 + **`remote`** 173 (`claude -p` under OAuth, the second over SSH to
  a second OAuth host) + **`kiro`** 1 974 (Kiro CLI headless, `claude-haiku-4.5`,
  credit-metered). Rebuild: `pca.gen_views_llm` per path → `pca.merge_paths`.
- Per-path view length is matched (median words 391 / 395 / 379); cross-path fidelity
  vs first-party `claude -p` validated in `experiments/e0_view_classifier/KIRO_FIDELITY.md`.
- Contamination audit: **0 / 2 400** (same patterns as below); all 2 400 view_texts distinct.
- **Not vendored** (gitignored), same as `views.jsonl` — regenerate from `slices.jsonl`
  via the commands above. Gate result: **signal-carrying, non-provisional** (GATES.md).

## Known limitations
- Extractive stand-in: views are subsets of source sentences, not abstractive summaries — stylistic signals of position (sentence-fragment density, topic jumps) may differ from the production LLM-summarization distribution in either direction.
- K fixed at 8 for all docs; exact-k is a clean 8-class problem but K-generalization is unmeasured.
- Encoding artifacts from the upstream dataset (e.g., `�` for curly quotes) are left as-is; they are position-independent.
