# Commit map — identity rewrite of 2026-08-06

Before this branch's first publication, its 62 then-unpushed commits (everything after
`origin/main` = `cdaa1f6`) were rewritten to replace a private machine identity in the
author/committer fields with the public one (`dev-boz <byronwarnich@gmail.com>`). One committed
line was also rephrased in-history — the scrub-rule sentence in `docs/HANDOFF-2026-07-21.md`
quoted verbatim the two private strings it bans; it now names them descriptively. No other
content changed, and author/committer dates are preserved to the second.

Docs written before the rewrite cite the OLD short hashes (`HANDOFF-2026-07-21.md`,
`HANDOFF-2026-07-28.md`, `STAGEA-CHAIN-GATE-RESULTS.md`, and earlier commit messages on this
branch). This table decodes them.

| old | new | subject |
|---|---|---|
| 5391edb | 4ded693 | E2′ preparation: criterion doc, relevance-control v2 pre-reg, E2′ pre-reg, editops v3, P6/P7 record sync |
| 547f753 | 7208420 | Fixture v2 (relevance-control v2): positive control + category-matched pair, probe byte-identical |
| 7d2c527 | 8c65b6e | Guard v3 validated against archives: strict mode, stopword overlap, duplicate-exemption |
| d76dee6 | 45589f1 | E2′ teacher pipeline: ClaudePClient, teacher_gen driver, leakage gate, Stage-A config |
| 96e2082 | 0257572 | Maintainer input: pre-named third option, concession-test caveat, kiro-first teacher |
| bd60108 | 9bc608c | gitignore: p7 run dumps, e2prime data outputs |
| e59acd1 | 2ca7f44 | Relevance-control v2 scorer: mechanical pre-filter for the manual tier read |
| ab6f1c0 | 5fc63eb | Relevance-control v2 floor battery: PRE-REGISTERED BRANCH 3 (PC failed — fork unresolvable at floor altitude) |
| 470cb1d | d199071 | E2′ corpus tooling: 3-slice builder + fresh-seed synth generator; prose amendment |
| c73a334 | 11096d9 | teacher_config: point prose views at the frozen E0-final set (views_haiku_final.jsonl) |
| 74addf1 | b8a95f9 | Corpus built + leakage gate CLEAN (277 docs); scanner precision fix; stratified audit |
| a11ee9c | c6e95bb | Teacher gate attempt #1 FAILED (validity 0.773) → parser v3.1: multi-fragment quotes |
| 3afa194 | b647934 | Quote cap 400→2000: teacher quotes whole entries; attempt-2 doc reparses 1.000 |
| 84c9a6f | f5c336f | Parser v3.2: sed-style REPLACE pairs, sub-letter ids, colon-less/quoted ADD (gate #3 at 0.875) |
| 77049c6 | ad27d54 | Teacher-quality gate PASSED (attempt #4): validity 0.983, quote-rate 0.998 |
| da17cff | beea4ce | Mass-gen run #1 tail failure: 28 docs purged (772 empty passes), pipeline hardened |
| 1122f01 | 5eb3254 | P-C health-check script: held-out validity + dominant-op-type agreement (formulas stated) |
| b80a965 | 7567b0f | D33: Stage-A waits for full 277-doc corpus; 257-row snapshot recorded as contingency |
| b4f4e0c | 9406ae3 | teacher: claude_p_remote backend (D30 remote OAuth path over ssh, env-resolved host) |
| 750e47c | e513371 | E2' Stage-A corpus complete: 277/277 trajectories, 5,730 rows, zero empty passes |
| ff200e0 | 7f267af | trainer: step-cadence checkpointing (save_steps=25, keep 3) for pause/resume on the consumer box |
| f74f7c1 | c29c1e3 | gitignore: runs/ (training checkpoints, merged weights) |
| c78a30c | 9ef445e | trainer: eval batch 1 — HF default of 8 OOM'd the 11GB card at the epoch-1 eval |
| 78335f5 | 5b57296 | pc_check: Pascal Triton-deregister workaround (same as trainer) |
| 7bfce07 | de1b606 | pc_check: transformers 5.x apply_chat_template returns BatchEncoding — unpack for generate |
| c0888a0 | efa03d9 | pc_check: --server mode — check the served fp16 GGUF student (the gate-facing artifact) |
| e4c1669 | d0ad4c7 | D34 + STAGEA-TRAINING.md: run-1 P-C failure post-mortem (TRL keep_start truncation), run-2 length-gate protocol |
| 9b4b9cc | 9fd1fed | chunked causal SDPA (equivalence-gated) + run-2 feasibility probes: the 11GB wall, fork a/b/c |
| 31ad120 | b2e3468 | handoff 2026-07-14: session state, 3070 run-2 plan, hazard list; vram_probe into repo |
| 74d17e5 | 3ab6108 | Triton-deregister workaround: make conditional (ImportError-safe) — WSL-only, no-op where gcc exists |
| 144b754 | 4bfd764 | train_lora: bf16 + liger-kernel fused-CE support (run-2 cloud A5000 fix) |
| 32364b0 | 688b6e7 | D35 + STAGEA-TRAINING.md: run-2 cloud pivot (RunPod A5000), CE/logits memory wall, bf16+liger fix |
| 2840e2b | 92f785d | pc_check: implement the D34 envelope-scoring protocol (in-envelope bars, out-of-envelope appendix) |
| 4dd14d7 | ecd4e57 | Run-2 P-C: PASS (validity 0.970, agreement 0.761 on 213 in-envelope rows) |
| 54c59e8 | 0faad39 | Stage-A chain gate: pre-run addendum + strict-v3.2 evaluator (no draws yet) |
| 9807509 | 636c266 | Chain gate: split the closing decode budget from the recording budget (pre-run) |
| ba6da78 | 3de83d9 | Chain gate: post-battery analysis (criterion §3 verdict, §5 attribution) |
| 1208e80 | 52ec73a | Chain gate: fix a scoring false negative that would have faked an architecture gate |
| 2e005aa | 079fac6 | Stage-A: companion checks, closing-budget diagnostic, and closing probes |
| 6aa5853 | 3b6e7d5 | Chain gate: stop asserting a truncation cause the text cannot establish |
| 6c8cdd2 | 6b74cbb | Chain gate: measure Tier-1 lossy summary separately from not recording |
| c28b43a | d930df4 | Chain gate: report op-following so a zero stays interpretable |
| f0da40a | 5f0dc4c | Stage-A chain gate: results record + verdict (ARCHITECTURE GATE, 0/10 both arms) |
| 67b6823 | 0d2b369 | Chain gate: query-first closing probe — prefill order does not rescue compose |
| d12ad54 | cb6829f | Padded probe (length vs distraction dissociation) + exploration ledger |
| e813349 | c618306 | Gauntlet prompt + session handoff (post-gate, pre-arbitration) |
| 73ff76d | e637f41 | Cross-model probe plumbing: --model/--label arms + trained-demand closing variants |
| f2e9c1b | d2d58c4 | Gauntlet round 1 arbitration + round-2 prompt + session handoff (2026-07-26) |
| 016abbf | 2cd83b6 | Relation as a first-class joint: mechanize the 0/28 measurement |
| f28c771 | 180eb92 | Gauntlet round 2 (13 reviews) arbitration + revised lever board |
| 4b8b5e5 | 2cfa291 | P1 probe battery: suppression resolves to home-availability; k-channel inert |
| 210a4ae | bbaecec | M-NL shape: maintainer refinements R1/R2 + lived existence proof |
| 2bf891f | 9e510e2 | P1e explained-protocol probe + maintainer constraints on k/K and generalization |
| d3e6e85 | e608dc7 | P1e results: structure is promptable at 7B; training bought edit discipline |
| 4f283fb | 24eb3bb | Session handoff 2026-07-28 |
| 7116d97 | 27b0d72 | Home availability corrected to salience-under-competition (P1f + archive scan) |
| 6abd203 | c5a8179 | M-NL: type-A fixture draft + G4 capability ladder |
| d4b79b2 | 90b3714 | Schedule discrepancy: the implemented D25 two-level sweep is not the README's pyramid |
| 550ee46 | 32f091c | Pyramid infrastructure: schedule builders, six frozen compressor arms, per-arm validation |
| 5ed644b | ac26640 | Retain guard + pyramid chain-gate and probe instruments |
| 1d08eb7 | e12ed60 | Pre-registered confirm, seeds 11-20: predictions fixed 2026-08-02 before the run |
| 6ce0367 | 48c7e7a | Pyramid results: the pipeline completes end to end; recorder/reader split; confirm 4/4 |
