"""P5 — verbatim-stage contamination: does conditioning the read on the
accumulated state suppress recording a task-relevant detail present in the view?

Frozen-state, single-pass, three arms (PRE-REG.md). For a target pass p and probe
fact, the prior state is FROZEN to the recorded P4 coupled run (snapshots[p-2]) and
the view is FROZEN to pass p's view — identical across arms. Only the conditioning
of the final read varies:

  A0  baseline      : state + view + task            -> edit ops              (1 call)
  A1  blind-salience: [view + task] -> salient list; [state + view + task + list] -> ops  (2 calls)
  A2  state-visible : [state + view + task] -> list; [state + view + task + list] -> ops  (2 calls)

A1 vs A2 isolates STATE VISIBILITY at the salience step (the contamination variable);
A2 vs A0 isolates the elicitation step. Metric: is the probe fact present in the
resulting state (P4 component matcher)? Same untrained Qwen-7B floor as P4.

  uv run python experiments/p5_verbatim_contamination/run.py            # first map entry (F7@17)
  uv run python experiments/p5_verbatim_contamination/run.py --pass 6 --probe F3
"""
from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pca.editops import IntegrationState, parse_ops  # noqa: E402
from pca.llm import LlamaServer  # noqa: E402
from pca.planted import build_schedule, fact_present, load_turns, match_components  # noqa: E402
from pca.textutils import n_tokens  # noqa: E402

EDIT_SYSTEM = """You are the integration model inside a multi-pass reading architecture. Across scheduled passes you build a single INTEGRATION STATE (numbered entries S1, S2, ...) from partial views of a long source.

Respond ONLY with edit operations, one per line, exactly:

ADD END: <text>
ADD S3: <text>
REPLACE S3: <text>
REMOVE S3
NO_CHANGE

Rules: refer to existing entry ids; single-line <text>; no commentary, no fences."""

SAL_SYSTEM = """You read ONE view of a long source and extract detail for a downstream recall task. List, as plain bullet points, every concrete task-relevant specific in THIS view: named people and their stated backgrounds, organizations, products, figures, dates, durations, prices, places, and personal anecdotes mentioned by name. One specific per line, starting with '- '. Output only the bullets."""

SAL_USER = """TASK: {task}
{state_block}VIEW (this pass):
{view}

List the concrete task-relevant specifics in THIS view."""

EDIT_USER = """TASK: {task}

position: {{k: {k}, K: {K}}}

OUTPUT DEMAND: near-verbatim pass — integrate precise specifics (exact figures, names, dates, prices, backgrounds, anecdotes). Prefer REPLACE/REMOVE; ADD what is missing; NO_CHANGE only if already captured.
{sal_block}
CURRENT INTEGRATION STATE:
{state}

VIEW OF THE SOURCE (this pass):
{view}

Respond with edit operations only."""


def state_from_entries(entries: list[dict]) -> IntegrationState:
    st = IntegrationState()
    st.entries = [dict(e) for e in entries]
    nums = [int(e["id"][1:]) for e in st.entries if e["id"][1:].isdigit()]
    st._next = (max(nums) + 1) if nums else 1
    return st


def run_arm(arm, server, cfg, m, task, k, K, frozen_entries, view, spec, max_ops):
    state = state_from_entries(frozen_entries)
    salience = None
    if arm in ("A1", "A2"):
        state_block = "" if arm == "A1" else f"CURRENT INTEGRATION STATE:\n{state.render()}\n\n"
        sresp = server.chat(SAL_SYSTEM, SAL_USER.format(task=task.strip(), state_block=state_block, view=view),
                            max_tokens=m["max_tokens"], temperature=m["temperature"], seed=cfg["seed"])
        salience = sresp["text"].strip()
        sal_block = f"\nSALIENT DETAILS YOU IDENTIFIED IN THIS VIEW:\n{salience}\n"
    else:
        sal_block = ""
    eresp = server.chat(EDIT_SYSTEM, EDIT_USER.format(task=task.strip(), k=k, K=K, sal_block=sal_block,
                                                      state=state.render(), view=view),
                        max_tokens=m["max_tokens"], temperature=m["temperature"], seed=cfg["seed"])
    parsed = parse_ops(eresp["text"], state.ids(), state.next_id)
    ops = parsed.ops[:max_ops]
    applied = state.apply(ops)
    present = fact_present(state.render(), spec)
    return {"arm": arm, "salience_text": salience, "edit_text": eresp["text"],
            "n_valid": parsed.valid, "n_candidate": parsed.candidate_lines, "n_applied": applied,
            "probe_present_after": present, "state_entries_after": len(state.entries),
            "wall_s": eresp["wall_s"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass", dest="pass_k", type=int, default=None)
    ap.add_argument("--probe", default=None)
    args = ap.parse_args()

    cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
    p4 = yaml.safe_load((HERE / cfg["p4_config"]).read_text(encoding="utf-8"))
    target = ({"pass": args.pass_k, "probe": args.probe} if args.pass_k else cfg["probes"][0])
    p, fid = target["pass"], target["probe"]
    spec = p4["facts_scoring"][fid]

    turns = load_turns((HERE / cfg["p4_config"]).resolve().parent / Path(p4["data_dir"]) / "conversation.jsonl")
    sch = build_schedule(turns, p4["schedule"]["V"], p4["schedule"]["R"], tuple(p4["schedule"]["stage_fracs"]))
    coupled = json.loads((HERE / cfg["coupled_run"]).read_text(encoding="utf-8"))
    snaps = coupled["snapshots"]

    view = sch[p - 1]["view_text"]
    frozen_entries = snaps[p - 2] if p >= 2 else []
    K = len(sch)

    # PRE-REG guards: matcher must fire on the view (present to read) and be ABSENT
    # from the frozen pre-pass state (a genuine not-yet-recorded detail).
    assert fact_present(view, spec), f"{fid} matcher does not fire on pass-{p} view — invalid probe"
    state0 = state_from_entries(frozen_entries)
    assert not fact_present(state0.render(), spec), \
        f"{fid} already present in frozen pre-pass state — invalid probe"
    print(f"P5 pass={p} probe={fid} | view={n_tokens(view)}tok frozen_state={len(frozen_entries)} entries "
          f"| probe in view=YES, in frozen state=NO (guards pass)", flush=True)

    m = p4["model"]
    server = LlamaServer(str((HERE / cfg["p4_config"]).resolve().parent / m["server_exe"]),
                         str((HERE / cfg["p4_config"]).resolve().parent / m["model_path"]),
                         ctx=m["ctx"], port=m["port"] + 2, threads=m["threads"])
    server.ensure_running()
    results = []
    for arm in cfg["arms"]:
        r = run_arm(arm, server, cfg, m, cfg["task"], p, K, frozen_entries, view, spec,
                    p4["budgets"]["max_ops_per_pass"])
        results.append(r)
        print(f"  {arm}: probe_present={r['probe_present_after']} "
              f"valid={r['n_valid']}/{r['n_candidate']} applied={r['n_applied']} "
              f"entries={r['state_entries_after']} ({r['wall_s']}s)", flush=True)
    server.stop()

    out = HERE / f"p5_pass{p}_{fid}.json"
    out.write_text(json.dumps({"pass": p, "probe": fid, "K": K, "task": cfg["task"].strip(),
                               "frozen_state_entries": len(frozen_entries), "view_tokens": n_tokens(view),
                               "arms": results}, indent=1, ensure_ascii=False), encoding="utf-8")
    verdict = {r["arm"]: r["probe_present_after"] for r in results}
    print(f"\nVERDICT pass={p} probe={fid}: {verdict}")
    print("  read: A1/A2 keep & A0 drop -> elicitation helps; A1 keep & A2 drop -> STATE-VISIBILITY "
          "(contamination) is the variable; all-same -> no effect at this pass.")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
