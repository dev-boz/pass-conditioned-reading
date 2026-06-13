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

## Known limitations
- Extractive stand-in: views are subsets of source sentences, not abstractive summaries — stylistic signals of position (sentence-fragment density, topic jumps) may differ from the production LLM-summarization distribution in either direction.
- K fixed at 8 for all docs; exact-k is a clean 8-class problem but K-generalization is unmeasured.
- Encoding artifacts from the upstream dataset (e.g., `�` for curly quotes) are left as-is; they are position-independent.
