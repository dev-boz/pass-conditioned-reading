"""P4 — planted-facts recall. Runs the coupled schedule and/or the dense baseline.

Stages are separable so the multi-hour coupled run is never lost:
  uv run python experiments/p4_planted_facts/run.py --stage coupled
  uv run python experiments/p4_planted_facts/run.py --stage dense
Each writes <stage>_run.json (idempotent: skips if it exists). Scoring is a
separate, model-free step (score.py).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pca.editops import IntegrationState, parse_ops  # noqa: E402
from pca.llm import LlamaServer  # noqa: E402
from pca.planted import (  # noqa: E402
    build_schedule, load_manifest, load_turns, match_components,
)
from pca.textutils import n_tokens  # noqa: E402

SYSTEM = """You are the integration model inside a multi-pass reading architecture. Across K scheduled passes you build a single INTEGRATION STATE: a comprehensive analytical brief of a long conversation you only ever see through partial views.

Each pass you receive: the task, your schedule position, the current integration state (numbered entries S1, S2, ...), one view of the source, and an output demand for this pass.

Respond ONLY with edit operations, one per line, exactly:

ADD END: <text>
ADD S3: <text>
REPLACE S3: <text>
REMOVE S3
NO_CHANGE

Rules: refer to existing entry ids; single-line <text>; no commentary, no fences."""

RUBRIC = {
    "scaffold": ("RUBRIC: early pass over a heavily compressed view. Build scaffold structure — "
                 "section headings and one-line placeholders via ADD. Do not chase specific figures yet."),
    "concrete": ("RUBRIC: middle pass. Integrate this view's substantive content into the existing "
                 "structure — prefer REPLACE of placeholders over new ADDs. Keep detail concise."),
    "verbatim": ("RUBRIC: late, near-verbatim pass. Integrate precise specifics — exact figures, names, "
                 "dates, prices, decisions. Prefer REPLACE/REMOVE; ADD only what is missing; NO_CHANGE if already captured."),
}

USER_TMPL = """TASK: {task}

position: {{k: {k}, K: {K}}}

{rubric}

CURRENT INTEGRATION STATE:
{state}

VIEW OF THE SOURCE (this pass):
{view}

Respond with edit operations only."""


def run_coupled(cfg, turns, out_path, max_passes=None):
    sch = build_schedule(turns, cfg["schedule"]["V"], cfg["schedule"]["R"],
                         tuple(cfg["schedule"]["stage_fracs"]))
    if max_passes:
        sch = sch[:max_passes]
    m = cfg["model"]
    server = LlamaServer(str((HERE / m["server_exe"]).resolve()), str((HERE / m["model_path"]).resolve()),
                         ctx=m["ctx"], port=m["port"], threads=m["threads"])
    server.ensure_running()
    state = IntegrationState()
    recs, snaps = [], []
    for p in sch:
        user = USER_TMPL.format(task=cfg["task"].strip(), k=p["k"], K=p["K"],
                                rubric=RUBRIC[p["stage"]], state=state.render(), view=p["view_text"])
        ptok = n_tokens(user)
        print(f"[coupled] pass {p['k']}/{p['K']} ({p['phase']}/{p['stage']}) "
              f"view={p['view_tokens']}tok prompt={ptok}tok ...", flush=True)
        resp = server.chat(SYSTEM, user, max_tokens=m["max_tokens"], temperature=m["temperature"], seed=cfg["seed"])
        parsed = parse_ops(resp["text"], state.ids(), state.next_id)
        ops = parsed.ops[: cfg["budgets"]["max_ops_per_pass"]]
        applied = state.apply(ops)
        st_tok = n_tokens(state.render())
        recs.append({"k": p["k"], "phase": p["phase"], "stage": p["stage"],
                     "turn_lo": p["turn_lo"], "turn_hi": p["turn_hi"],
                     "view_tokens": p["view_tokens"], "compression_ratio": p["compression_ratio"],
                     "n_candidate": parsed.candidate_lines, "n_valid": parsed.valid,
                     "n_applied": applied, "aliased": parsed.aliased,
                     "state_tokens": st_tok, "prompt_tokens": ptok, "wall_s": resp["wall_s"]})
        snaps.append([dict(e) for e in state.entries])
        warn = " [OVER STATE BUDGET]" if st_tok > cfg["budgets"]["state_tokens"] else ""
        print(f"    valid {parsed.valid}/{parsed.candidate_lines} applied {applied} "
              f"aliased {parsed.aliased} state {st_tok}tok{warn} ({resp['wall_s']}s)", flush=True)
    server.stop()
    out_path.write_text(json.dumps({"arm": "coupled", "K": len(sch), "passes": recs,
                                    "snapshots": snaps, "final_state": state.render()}, indent=1), encoding="utf-8")
    print(f"[coupled] -> {out_path}")


def run_dense(cfg, turns, out_path):
    d = cfg["dense_baseline"]
    fill, hf = d["fill_tokens"], d["head_frac"]
    head_budget, tail_budget = int(fill * hf), fill - int(fill * hf)
    head, ht, i = [], 0, 0
    while i < len(turns) and ht + turns[i]["tokens"] <= head_budget:
        head.append(i); ht += turns[i]["tokens"]; i += 1
    tail, tt, j = [], 0, len(turns) - 1
    while j > i and tt + turns[j]["tokens"] <= tail_budget:
        tail.append(j); tt += turns[j]["tokens"]; j -= 1
    tail = sorted(tail)
    omitted = len(turns) - len(head) - len(tail)
    text = ("\n".join(turns[k]["text"] for k in head)
            + f"\n\n[... {omitted} turns omitted for length ...]\n\n"
            + "\n".join(turns[k]["text"] for k in tail))
    user = (f"TASK: {cfg['task'].strip()}\n\nHere is the conversation (a long middle section is "
            f"omitted for length):\n\n{text}\n\nWrite the comprehensive analytical brief now, "
            f"including specific figures, names, prices, and the final decision and its reason.")
    m = cfg["model"]
    server = LlamaServer(str((HERE / m["server_exe"]).resolve()), str((HERE / m["model_path"]).resolve()),
                         ctx=d["ctx"], port=m["port"] + 1, threads=m["threads"])
    server.ensure_running()
    ptok = n_tokens(user)
    print(f"[dense] head={len(head)} tail={len(tail)} omitted={omitted} prompt={ptok}tok ...", flush=True)
    resp = server.chat("You are a careful analyst. Read the conversation excerpts and produce the brief.",
                       user, max_tokens=1500, temperature=m["temperature"], seed=cfg["seed"])
    server.stop()
    out_path.write_text(json.dumps({"arm": "dense", "head_turn_idx": head, "tail_turn_idx": tail,
                                    "omitted_turns": omitted, "prompt_tokens": ptok,
                                    "wall_s": resp["wall_s"], "answer": resp["text"]}, indent=1), encoding="utf-8")
    print(f"[dense] -> {out_path} ({resp['wall_s']}s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["coupled", "dense", "all"], default="all")
    ap.add_argument("--max-passes", type=int, default=None, help="smoke test: limit coupled passes, write *_smoke.json")
    args = ap.parse_args()
    cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
    data = (HERE / cfg["data_dir"]).resolve()
    turns = load_turns(data / "conversation.jsonl")

    # matcher-fires-on-source guard (advisor): never trust a state 0 unless the matcher fires on source
    src = "\n".join(t["text"] for t in turns)
    for fid, spec in cfg["facts_scoring"].items():
        hits = match_components(src, spec["components"])
        miss = [c for c, h in hits.items() if not h]
        assert not miss, f"{fid} matcher does not fire on source: {miss}"

    if args.stage in ("coupled", "all"):
        if args.max_passes:
            run_coupled(cfg, turns, HERE / "coupled_smoke.json", max_passes=args.max_passes)
            return
        out = HERE / "coupled_run.json"
        if out.exists():
            print("coupled_run.json exists — skipping")
        else:
            run_coupled(cfg, turns, out)
    if args.stage in ("dense", "all"):
        out = HERE / "dense_run.json"
        if out.exists():
            print("dense_run.json exists — skipping")
        else:
            run_dense(cfg, turns, out)
    print("P4 run stage done.")


if __name__ == "__main__":
    main()
