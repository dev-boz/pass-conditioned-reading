# P7 — running the focused high-N matrix on the Threadripper 1920X / 128GB / 1080Ti

Goal: re-run the high-information P7 tests at **n=10** on the **7B** and on a **larger base model
(Qwen2.5-14B)**, to (a) estimate the stochastic record→retain→compose rates with real sample size,
and (b) test whether the bottlenecks (salience/recording, retention/clobber) are **capacity-limited**
(a bigger model fixes them → viability signal) or **architecture-limited** (persist regardless →
clobber-safe edit ops are necessary). The 1080Ti + a CUDA build cuts a CPU-overnight run to ~1–3 h.

## 1. What to copy

Unzip `p7_bundle.zip` (code + fixture + frozen scaffolds, ~MBs) preserving layout → `pca/src/…`,
`pca/experiments/p7_split_unit/…`, `pca/models/` (placeholders). Then place the two large items
(NOT in the zip):
- **7B model** `models/Qwen2.5-7B-Instruct-Q4_K_M.gguf` (~4.7 GB) — from the source machine.
- **14B model** `models/Qwen2.5-14B-Instruct-Q4_K_M.gguf` (~9 GB) — download from Hugging Face
  (e.g. `Qwen/Qwen2.5-14B-Instruct-GGUF`, the `Q4_K_M` file) into `models/`.
- **A CUDA llama.cpp build** in `models/llamacpp/` (see step 2).

## 2. CUDA llama.cpp build (the speedup)

The shipped `models/llamacpp/` is CPU-only. On the box: download the latest **Windows CUDA** llama.cpp
release (`llama-bXXXX-bin-win-cuda-x64.zip` from github.com/ggml-org/llama.cpp/releases; CUDA 12.x,
Pascal/1080Ti supported), unzip into `pca/models/llamacpp/` (keep `llama-server.exe` at that path so
`config.yaml` resolves). Needs a recent NVIDIA driver + CUDA 12 runtime. VRAM fit on the 11 GB card:
7B Q4 (~4.7 GB) and 14B Q4 (~9 GB) both fit fully with the 16K KV cache → `n_gpu_layers=99`.

## 3. Python env

```
python -m venv .venv && .venv\Scripts\activate
pip install tiktoken pyyaml requests
```

## 4. Verify the fixture is intact (deterministic — reproduces byte-for-byte)

```
cd pca
set PYTHONIOENCODING=utf-8
.venv\Scripts\python experiments\p7_split_unit\fixture\gen_fixture.py   # host_doc + spec (seed 70707)
.venv\Scripts\python experiments\p7_split_unit\gen_scaffold.py          # v2 scaffold; State-D guard PASS
.venv\Scripts\python experiments\p7_split_unit\gen_scaffold.py --compressor compress_code_v1 --out scaffold_v1.json
.venv\Scripts\python experiments\p7_split_unit\verify_fixture.py        # realized-view guards PASS
.venv\Scripts\python experiments\p7_split_unit\heterogeneity_check.py   # v2 heterogeneity profile
```

## 5. Run the matrix (unattended, resumable) — GPU

One model per invocation (run 7B first, then 14B). `--ngl 99 --threads 24` forces full GPU offload +
all threads (overriding the CPU-machine defaults in config.yaml):

```
.venv\Scripts\python experiments\p7_split_unit\run_matrix.py --model 7b  --n 10 --ngl 99 --threads 24
.venv\Scripts\python experiments\p7_split_unit\run_matrix.py --model 14b --n 10 --ngl 99 --threads 24
```
Each runs: **gates** (backfill + compose, n=10) · **neutral** survival (coupled Phase-A, n=10) ·
**specifics** end-to-end (dense + verbatim_only + coupled_full, FULL, fair-shot prompt, n=10). It
**skips** any draw whose result file already has the needed arms — safe to re-launch after an
interruption. Watch the first few `pass k/K … (Ns)` lines: ~5–20 s/pass = GPU engaged; ~100–400 s =
CPU fallback (check the CUDA build/driver). Rough GPU time: ~1–3 h per model for the full n=10 matrix.

## 6. What to read (bring back all `p7_results_*.json` + `*_result_*.json` + `matrix_*.log`)

- **Headline — specifics end-to-end** (`p7_results_<model>_spec_s*_t*.json`): per seed, does
  `coupled_full.closing.answer == 2353` and does `verbatim_only` fail? Plus per-pass
  `mapping.queried_mapping` (record), `queried_first_phase=="A"` (State-D), and whether it persists to
  the closing call (retention). **The money comparison = coupled vs verbatim on the closing ANSWER**,
  and the existence question = does ANY seed get 2353.
- **Neutral survival** (`<model>_mp6_neutral_*`): recording rate of the table un-prompted (expect ~0;
  test if the 14B changes it).
- **Gates** (`backfill_check_result_<model>.json`, `compose_gate_result_<model>.json`): unit still
  unguessable (0/n) and compose ceiling holds on the 14B.
- Per-model contrast 7B vs 14B on record/retain/compose rates = the capacity-vs-architecture read.

NOT in this matrix (by decision): deterministic temp-0 re-runs of saturated gates, and the
**relevance control** (it needs a positive-control redesign, not more N — `RELEVANCE-CONTROL.md`).
Nothing is published; surface results for review before any conclusion.
