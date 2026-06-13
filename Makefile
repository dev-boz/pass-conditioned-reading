# PCA experiments — each target idempotent and re-runnable from its config.
# Windows note: no system make is installed by default; either install one
# (e.g. `winget install GnuWin32.Make`) or run the underlying commands below
# directly — they are plain `uv run` invocations with no make-only logic.

UV ?= uv

.PHONY: setup views e0 p1 p2 p3 all

setup:            ## create venv + install pinned deps (uv.lock)
	$(UV) sync

views: setup      ## fetch corpus + generate data/views/views.jsonl (skips if complete)
	$(UV) run python -m pca.gen_views --config data/views/views_config.yaml

e0: views         ## run the E0 gate (CPU-only)
	$(UV) run python experiments/e0_view_classifier/run.py

p1: setup         ## run the 3-arm micro-pilot (local llama.cpp 7B; skips arms with transcripts)
	$(UV) run python experiments/p1_micro_pilot/run.py

p2: setup         ## run the position-token pilot (needs p1 coupled arm)
	$(UV) run python experiments/p2_position_pilot/run.py

p3: setup          ## run the prompt-rubric pilot (needs p1 coupled arm)
	$(UV) run python experiments/p3_prompt_rubric/run.py

all: e0 p1 p2 p3
