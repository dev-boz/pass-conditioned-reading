"""M-NL G4 — test-model capability gate, as a scale ladder ($0 local, inference only).

Shape doc §10, refinement R2 (the GATE-3 lesson): before any M-NL arm runs, the candidate test
model must prove it can make the pre-registered integrated call AT ALL, from a small clean
evidence set well inside its window. Without this gate, coupled-0 vs baseline-0 repeats the
Stage-A situation — a zero that says nothing about the architecture, only about the model.

    The arms run on the SMALLEST model that passes G4.
    If nothing local passes, the arms move to API models (the experiment is inference-only).
    The ladder is diagnostic in its own right, exactly as the compose ladder was.

What this probe hands the model is DELIBERATELY EASY: the nine carrier turns of the type-A
fixture (docs/MNL-TYPE-A-FIXTURE-DRAFT.md §2), back to back, stripped of the ~100K tokens of
ordinary project talk they are embedded in. That concentration is the point — G4 measures
capability, not preservation. A model that cannot make the call here cannot be the test model;
a model that can has said nothing yet about whether any schedule preserves the signal.

Scoring is a MECHANICAL PRE-FILTER over the pre-registered 0/1/2 rubric. It is not the score.
Every draw's raw output is archived and hand-read before any number is believed (working mode:
interpretation is the unreliable layer, the archive is not).

    python experiments/mnl/g4_capability_ladder.py --dry-run
    python experiments/mnl/g4_capability_ladder.py                     # local ladder
    python experiments/mnl/g4_capability_ladder.py --models qwen7b,qwen14b
    python experiments/mnl/g4_capability_ladder.py --models haiku_remote,sonnet_remote  # API rungs
    python experiments/mnl/g4_capability_ladder.py --summarize

API rungs (the R2 escalation, and the G2 PREMISE check on the distilled evidence set — full G2
on the authored 80-150K fixture is still owed): Claude via `claude -p` on a remote host's OAuth
pool, the D30 delivery path. Requires PCA_CLAUDE_SSH_HOST in the environment; the host never
enters this repo or the artifacts (ClaudePClient provenance records the path as
`claude-p-remote:<alias>`). Named limitation, inherited from the teacher lineage: `claude -p`
exposes no temperature/seed control, so API-rung draws are repeated sampling at CLI defaults and
the seed column is a draw label only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pca.llm import LlamaServer, ClaudePClient                           # noqa: E402

MODELS = {
    "qwen1_5b": ROOT / "models" / "Qwen2.5-1.5B-Instruct-f16.gguf",
    "qwen3b": ROOT / "models" / "Qwen2.5-3B-Instruct-f16.gguf",
    "qwen7b": ROOT / "models" / "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
    "qwen14b": ROOT / "models" / "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
}
# API rungs: model key -> `claude -p --model` alias. Ceiling first (sonnet), teacher-class
# (haiku) for continuity with the compressor lineage.
API_MODELS = {"haiku_remote": "haiku", "sonnet_remote": "sonnet"}
LADDER = ["qwen1_5b", "qwen3b", "qwen7b", "qwen14b"]
SEEDS = list(range(1, 11))
TEMP = 0.7
MAX_TOKENS = 700
OUT_DIR = ROOT / "runs" / "mnl_g4"

# --------------------------------------------------------------------------- the evidence set
# The nine carrier turns, condensed. Authored to the §2 ledger: no turn names an emotion,
# avoidance, or the pattern; the signal is rate + ordering + zero completions. Timestamps stand
# in for the span's elapsed weeks (the real fixture carries them implicitly through its bulk).
CARRIERS = [
    ("week 1, Tue", "Saw this on arXiv this morning - 'Hierarchical Memory for Long-Context "
                    "Agents'. Skimmed it, don't think it's ours, but can you check? Then let's "
                    "get back to the ablation."),
    ("week 1, Fri", "Another one - 'Recursive Summarisation with Learned Compression'. This "
                    "one's closer. Different noise model though, right?"),
    ("week 2, Wed", "'Multi-Pass Document Understanding' - different enough, you reckon?"),
    ("week 3, Mon", "Before we start on the eval harness today - quick look at this one? "
                    "'Scheduled Context Refinement', came out Friday."),
    ("week 3, Thu", "Here's another - 'Iterative State Editing for Long Documents'. Harness "
                    "slipped a day, by the way."),
    ("week 4, Tue", "'Coarse-to-Fine Retrieval over Long Context'. Let's push the ablation to "
                    "next week."),
    ("week 5, Mon", "This one's from a big lab - 'Progressive Compression for Agent Memory'. "
                    "Can you do a proper point-by-point against ours? Take your time on it."),
    ("week 6, Wed", "'Staged Reading for Document QA'. The experiment's going to slip again, "
                    "I think."),
    ("week 7, Tue", "'Bounded-State Iterative Reading'. What's actually left to do on this "
                    "project, at this point?"),
]

# Planned work introduced across the same span, none of it finished — the third leg of the
# signal. In the full fixture this is carried by the ordinary bulk; G4 states it as context.
PLANNED = ["the ablation (introduced week 1)", "the eval harness (introduced week 3)",
           "the scaling experiment (introduced week 4)"]

TASK = "Draft the plan for the next month of this project."

SYSTEM = ("You are a research assistant who has been working with this person on their project "
          "for several weeks. Answer their request directly and practically.")


def build_user() -> str:
    turns = "\n".join(f"[{when}] {text}" for when, text in CARRIERS)
    planned = "\n".join(f"- {p}" for p in PLANNED)
    return (f"Here is our conversation history over the past seven weeks:\n\n{turns}\n\n"
            f"Work items opened during this period:\n{planned}\n\n"
            f"None of them has been marked finished.\n\n{TASK}")


# --------------------------------------------------------------------------- scoring pre-filter
# Crude on purpose. These are PRE-FILTERS over the §4 rubric, not the rubric. Hand-read arbitrates
# every draw; a rate printed from these regexes is a reading aid, never a result.
_BOUNDED = re.compile(
    r"time[- ]?box|timebox|stop rule|one (?:systematic|thorough|final|proper) (?:sweep|review|"
    r"search|pass)|single (?:sweep|review|literature)|set (?:a )?(?:deadline|limit).{0,40}"
    r"(?:review|search|paper)|stop (?:checking|searching|looking)|cap (?:the )?(?:time|number)"
    r".{0,30}paper|decide (?:and|then) move on|moratorium|freeze the (?:search|review)", re.I)
_ZERO_DONE = re.compile(
    r"(?:nothing|none|no (?:experiment|work item|task|deliverable)s?)\b.{0,60}"
    r"(?:finish|complet|deliver|done|shipped)"
    r"|(?:not|never) (?:yet )?(?:been )?(?:finish|complet)"
    r"|zero (?:completed|finished)|hasn'?t been (?:finished|completed)"
    r"|all (?:three|3)\b.{0,30}(?:open|unfinished|incomplete|outstanding)"
    r"|(?:still|remain)\w* (?:open|unfinished|incomplete)|no progress on", re.I)
_PATTERN_NAMED = re.compile(
    r"prior[- ]art.{0,40}(?:displac|interrupt|instead of|rather than|crowd|dominat|consum)"
    r"|(?:displac|crowd|squeez)\w*.{0,40}(?:execution|experiment|implementation)"
    r"|(?:reviewing|checking|reading) (?:papers|arxiv|literature).{0,50}"
    r"(?:instead of|rather than|at the expense)|pattern of (?:checking|reviewing)", re.I)
_LATEST_CENTRED = re.compile(
    r"bounded[- ]?state iterative reading|the (?:most recent|latest) paper", re.I)
# Rubric level 1 ("notices, but plans around neither") — mere acknowledgement of the checking,
# with no bound proposed and no completions observation.
_NOTICES = re.compile(
    r"(?:you(?:'ve| have)|we(?:'ve| have)) (?:been )?(?:look\w*|review\w*|read\w*|check\w*)"
    r".{0,40}(?:papers|arxiv|literature|related work)"
    r"|several (?:related |similar )?papers|a number of (?:related )?papers", re.I)


def prefilter(text: str) -> dict:
    t = text or ""
    return {"bounded": bool(_BOUNDED.search(t)),
            "zero_completions": bool(_ZERO_DONE.search(t)),
            "pattern_named": bool(_PATTERN_NAMED.search(t)),
            "notices_checks": bool(_NOTICES.search(t)),
            "latest_centred": bool(_LATEST_CENTRED.search(t))}


def provisional_score(f: dict) -> int:
    """Provisional 0/1/2 per the DRAFT §4 rubric. Rewrite when the maintainer signs the wording;
    the components stay separable above so either reading of open question #1 can be scored after
    the fact without re-running anything."""
    if f["bounded"] or f["pattern_named"]:
        return 2
    if f["zero_completions"] or f["notices_checks"]:
        return 1
    return 0


# --------------------------------------------------------------------------- main
def summarize(out_dir: Path) -> None:
    for f in sorted(out_dir.glob("g4_*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        d = rec["draws"]
        n = len(d)
        agg = {k: sum(x["prefilter"].get(k, False) for x in d)
               for k in ("bounded", "zero_completions", "pattern_named", "notices_checks",
                         "latest_centred")}
        s2 = sum(1 for x in d if x["provisional_score"] == 2)
        print(f"{rec['_meta']['model_key']:<10} n={n:<3} "
              f"bounded {agg['bounded']}/{n}  zero-done {agg['zero_completions']}/{n}  "
              f"pattern-named {agg['pattern_named']}/{n}  "
              f"notices {agg['notices_checks']}/{n}  "
              f"latest-centred {agg['latest_centred']}/{n}  | provisional 2s: {s2}/{n}")
    print("\nPRE-FILTER counts, not scores. G4 is a gate on the pre-registered rubric, and the "
          "rubric wording is unsigned (docs/MNL-TYPE-A-FIXTURE-DRAFT.md §4). Hand-read.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=None, help=f"comma list from {list(MODELS)}")
    ap.add_argument("--seeds", default=None)
    ap.add_argument("--port", type=int, default=8098)
    ap.add_argument("--ctx", type=int, default=8192)
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--threads", type=int, default=24)
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--summarize", action="store_true")
    args = ap.parse_args()

    if args.summarize:
        summarize(OUT_DIR)
        return

    seeds = SEEDS
    if args.seeds:
        seeds = []
        for part in args.seeds.split(","):
            if "-" in part:
                a, b = part.split("-")
                seeds += list(range(int(a), int(b) + 1))
            else:
                seeds.append(int(part))

    user = build_user()
    keys = args.models.split(",") if args.models else LADDER

    if args.dry_run:
        print(f"DRY RUN — ladder {keys}, seeds {seeds}\n")
        print(f"--- SYSTEM ---\n{SYSTEM}\n\n--- USER ({len(user)} chars) ---\n{user}")
        print("\n--- pre-filter on a hand-written INTEGRATED answer (should flag) ---")
        print(prefilter("Before planning more experiments: three work items have been opened "
                        "and none finished, while prior-art review has displaced execution. "
                        "Propose one systematic sweep this week, time-boxed to two days, then "
                        "a decision and no further checks until the ablation ships."))
        print("--- pre-filter on a hand-written FLATTENED answer (should not) ---")
        print(prefilter("Next month: 1) finish reviewing Bounded-State Iterative Reading and "
                        "position our contribution against it, 2) run the ablation, 3) draft "
                        "the related-work section."))
        print("\nDry run OK. Nothing served, nothing written.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    exe = ROOT / "models" / "llamacpp" / "llama-server.exe"
    for mk in keys:
        is_api = mk in API_MODELS
        if is_api:
            assert os.environ.get("PCA_CLAUDE_SSH_HOST"), \
                "API rungs need PCA_CLAUDE_SSH_HOST in the environment (host never enters the repo)"
            model_desc = f"claude-p-remote:{API_MODELS[mk]}"
        else:
            model = MODELS[mk]
            assert model.exists(), model
            model_desc = str(model)
        out_path = OUT_DIR / f"g4_{mk}.json"
        if out_path.exists() and not args.redo:
            print(f"[skip] {out_path.name} exists")
            continue
        rec = {"_meta": {"probe": True, "gate_legal": False,
                         "gate": ("M-NL G4 ladder, API rung — doubles as the G2 PREMISE check "
                                  "on the distilled evidence set; full G2 on the authored "
                                  "fixture still owed" if is_api else "M-NL G4 (capability)"),
                         "model_key": mk, "model_path": model_desc,
                         "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                         "seeds": seeds, "temp": TEMP, "max_tokens": MAX_TOKENS,
                         **({"decoding": "claude -p CLI defaults — no temp/seed control; "
                                         "the seed column is a draw label only"} if is_api
                            else {}),
                         "rubric": "DRAFT, unsigned — MNL-TYPE-A-FIXTURE-DRAFT.md §4",
                         "evidence": "carrier turns only, concentrated (capability, not "
                                     "preservation)", "task": TASK},
               "system": SYSTEM, "user": user, "draws": []}
        print(f"\n{'=' * 66}\nG4 {mk} ({model_desc})\n{'=' * 66}", flush=True)
        if is_api:
            server = ClaudePClient(model=API_MODELS[mk],
                                   ssh_host=os.environ["PCA_CLAUDE_SSH_HOST"])
        else:
            server = LlamaServer(str(exe), str(model), ctx=args.ctx, port=args.port,
                                 threads=args.threads, n_gpu_layers=args.ngl)
            server.ensure_running()
        t0 = time.time()
        try:
            for seed in seeds:
                resp = server.chat(SYSTEM, user, max_tokens=MAX_TOKENS, temperature=TEMP,
                                   seed=seed)
                f = prefilter(resp["text"])
                rec["draws"].append({"seed": seed, "prefilter": f,
                                     "provisional_score": provisional_score(f),
                                     "raw_output": resp["text"], "wall_s": resp.get("wall_s")})
                print(f"  seed={seed} bounded={f['bounded']} zero_done={f['zero_completions']} "
                      f"pattern={f['pattern_named']} latest={f['latest_centred']} "
                      f"({resp.get('wall_s')}s)", flush=True)
                out_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False),
                                    encoding="utf-8")
        finally:
            server.stop()
            time.sleep(3)
        rec["wall_s"] = round(time.time() - t0, 1)
        out_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
