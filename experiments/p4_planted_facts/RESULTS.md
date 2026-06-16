# P4 — Planted-facts recall (Sandpiper, 80K) · RESULTS

**Run:** 2026-06-14 · **Config hash:** `415fb49232e02ca3` · **Parser v2.1** · local Qwen2.5-7B-Instruct (llama.cpp CPU), temp 0, seed 42 · extractive **stand-in** compressor (provisional, as E0) · $0 spend
**Reproduce:** `make p4` then `score.py` (coupled + dense are separable; coupled is the ~4h pole). Means per D24.

## Headline — the pre-registered kill condition FAILED

| arm | fact recall (full-credit, 8 facts) | tokens processed | wall-clock |
|---|---|---|---|
| **coupled** (K=32 schedule) | **0.625 (5/8)** | 159,451 | 231.5 min |
| **dense** (single-pass head+tail, 14K of 73K) | **0.625 raw (5/8)** · 0.714 within-reach (5/7) | 13,883 | 24.5 min |

> **Kill rule (pre-registered):** coupled recall must *exceed* dense raw recall, else it is evidence against M1's premise. **Coupled (0.625) ≤ dense (0.625) → FAIL.** Reported, not buried. On this one document, the coupled schedule's ~11× token and ~9× wall-clock cost bought **no recall advantage** over a single generous head+tail read.

`headline_fact_recall = count(facts full-credit present in FINAL state) / 8`.

## What each arm kept and dropped — identical fact sets

Both arms got **F2 Cairn, F4 cap (8,000/Halvorsen/Inkstone/14-week), F5 $299, F6 Meridian, F8 Founders' Edition**; both missed **F1 Sandpiper (codename), F3 morning-walk-with-dog, F7 grandmother-typesetter**.

By tier (coupled): 2-distinctive 0.75 · 1-common 0.0 · tier3-setup 1.0 · single-turn-detail 0.0 · position-dependent 1.0.
By source position (coupled): early 0.67 · mid 0.0 · late 1.0.

## The diagnosis: coverage worked; integration *salience* was the bottleneck

This is **not** a coverage or eviction failure. The coverage-timing decomposition (slice-coverage / view-presence / state-entry passes) shows every one of the 8 facts **reached a view**, and the three misses each have `state_entry_pass = null` with `evicted = false` — they were **available but never written into the brief**:

| fact | view-presence pass | state-entry pass | at final |
|---|---|---|---|
| F7 grandmother (single-occurrence, mid) | **17** (its verbatim tile — exactly as pre-computed; compression dropped it from every earlier view) | never | absent |
| F1 Sandpiper (codename) | 3 | never | absent |
| F3 morning-walk-with-dog | 6 | never | absent |

So the schedule **did** deliver the hard single-occurrence F7 verbatim at the predicted pass; the rubric-floor 7B simply declined to record three low-salience **asides** — a launch codename, a "where I do my best thinking" aside, and a personal anecdote — into a *strategy* brief. **Dense missed the same two salience facts (F1, F3)** plus the one outside its window (F7, correctly excluded from its within-reach denominator). No alias-misplacement flags; no evictions anywhere.

## The Tier-3 payoff *succeeded* (co-presence + ordering)

The methodological crown jewel held: **F4 (early cap, entered the state at pass 3) and F8 (late decision, entered at pass 26) are both present in the final state** (`f4_f8_co_present_at_final = true`), with entry order matching the document order. The brief even states the causal link in prose (final state S1: *"Because Halvorsen Assembly can only make 8,000 units before the holidays, a wide retail launch was never supply-able… Turning the constraint into the strategy — that's what we're doing with the Founders' Edition. Scarcity reinforces the premium positioning…"*). Reported as **co-presence + ordering, not mechanically-verified causality** (D28) — though here the prose does carry the "because."

## Honest read — what this does and doesn't show (n=1 document)

- **It does** show the pre-registered kill condition failing: the untrained prompt floor does **not** convert the coverage advantage into higher faithful recall than a single generous single-pass read, at ~10× the cost, on this document. That is real evidence against M1's *premise as operationalized here* and must count.
- **It does not** refute M1 (the trained-student interaction). The bottleneck was integration **salience judgment by the untrained 7B floor**, not the coverage mechanism — which is precisely the gap E2′'s trained student is meant to close. This raises the bar E2′ must clear and is the informative part.
- **Metric/task tension (the key caveat for the real M1 design):** the task asks for a "comprehensive analytical brief," which arguably should *not* include a codename or a personal anecdote — yet the planted-fact metric penalizes those omissions. A coverage test wants a recall-framed task ("surface every named entity and personal detail"), or planted facts that are all strategy-relevant. F4/F5/F6/F8 (all strategy-relevant) were recalled 4/4; the three misses are all task-orthogonal asides. Fix the task↔fact alignment before reading P4-style recall as an M1 verdict.
- **Provisional compressor:** extractive stand-in (as E0). Production **Haiku** views (being generated for E0-final) shift view-presence timing and could change which low-salience facts survive compression into early views.

## Bottom line

Pre-registered verdict: **FAIL — coupled ≤ dense.** Mechanistically: coverage sound, Tier-3 co-presence achieved, but the untrained floor leaves the coverage advantage on the table and the recall metric is partly measuring task-salience rather than coverage. Carry both the verdict and the diagnosis into E2′'s design (recall-aligned task; trained student). Raw outputs: `coupled_run.json`, `dense_run.json`, `metrics.json`.
