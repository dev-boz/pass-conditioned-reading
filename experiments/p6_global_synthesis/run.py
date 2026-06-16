"""P6 — global (whole-document) synthesis test. *** UNTESTED — smoke-test first
(`--arm coupled_full --max-passes 6`) before a full run. ***

Three arms on the Sandpiper fixture, scored on a comparable closing ANSWER to the
synthesis question (gold_chain.json):
  dense          — single-pass head+tail (P4 run_dense), answers directly
  coupled_full   — Phase-A scaffold + Phase-B verbatim, builds state, then answers from it
  verbatim_only  — Phase-B tiles only (NO Phase-A scaffold), builds state, then answers

Headline metric: L3 (mid-doc hinge: "full fleet"/"holiday density") present in the answer
— the causal reason a head+tail reader structurally cannot have. See PRE-REG.md.

  uv run python experiments/p6_global_synthesis/run.py --arm all
  uv run python experiments/p6_global_synthesis/run.py --arm coupled_full --max-passes 6   # smoke
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
from pca.planted import build_schedule, load_turns, match_components, normalize  # noqa: E402
from pca.textutils import n_tokens  # noqa: E402

# State-building prompts: reuse P4's edit-op SYSTEM/RUBRIC/USER (keep identical to P4 so the
# only change vs P4 is the TASK = synthesis question). Copy from p4_planted_facts/run.py.
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
                 "dates, prices, decisions, and the REASONS/causes behind them. Prefer REPLACE/REMOVE; "
                 "ADD only what is missing; NO_CHANGE if already captured."),
}

USER_TMPL = """TASK: {task}

position: {{k: {k}, K: {K}}}

{rubric}

CURRENT INTEGRATION STATE:
{state}

VIEW OF THE SOURCE (this pass):
{view}

Respond with edit operations only."""

CLOSING = ("Using ONLY your integration state below, answer this question as a short causal "
           "narrative — state the reason(s), not just the outcome.\n\nQUESTION: {q}\n\n"
           "INTEGRATION STATE:\n{state}\n\nAnswer:")


def build_passes(cfg, p4, turns, no_scaffold: bool):
    sch = build_schedule(turns, p4["schedule"]["V"], p4["schedule"]["R"],
                         tuple(p4["schedule"]["stage_fracs"]))
    if no_scaffold:
        sch = [p for p in sch if p["phase"] == "B"]
        K = len(sch)
        for i, p in enumerate(sch):       # renumber so position field is coherent
            p["k"], p["K"] = i + 1, K
    return sch


def run_state_arm(server, cfg, p4, m, task, passes, question, max_passes=None):
    if max_passes:
        passes = passes[:max_passes]
    state = IntegrationState()
    recs = []
    for p in passes:
        user = USER_TMPL.format(task=task.strip(), k=p["k"], K=p["K"],
                                rubric=RUBRIC[p["stage"]], state=state.render(), view=p["view_text"])
        resp = server.chat(SYSTEM, user, max_tokens=m["max_tokens"], temperature=m["temperature"], seed=cfg["seed"])
        parsed = parse_ops(resp["text"], state.ids(), state.next_id)
        state.apply(parsed.ops[: p4["budgets"]["max_ops_per_pass"]])
        recs.append({"k": p["k"], "phase": p["phase"], "stage": p["stage"],
                     "n_valid": parsed.valid, "state_tokens": n_tokens(state.render())})
        print(f"  pass {p['k']}/{p['K']} ({p['phase']}/{p['stage']}) valid={parsed.valid} "
              f"state={recs[-1]['state_tokens']}tok", flush=True)
    ans = server.chat("You are a careful analyst.", CLOSING.format(q=question, state=state.render()),
                      max_tokens=600, temperature=m["temperature"], seed=cfg["seed"])
    return {"passes": recs, "final_state": state.render(), "answer": ans["text"]}


def run_dense_arm(server, cfg, p4, m, turns, question):
    d = p4["dense_baseline"]
    fill, hf = d["fill_tokens"], d["head_frac"]
    head_budget = int(fill * hf)
    head, ht, i = [], 0, 0
    while i < len(turns) and ht + turns[i]["tokens"] <= head_budget:
        head.append(i); ht += turns[i]["tokens"]; i += 1
    tail, tt, j = [], 0, len(turns) - 1
    while j > i and tt + turns[j]["tokens"] <= (fill - ht):
        tail.append(j); tt += turns[j]["tokens"]; j -= 1
    tail = sorted(tail)
    omitted = len(turns) - len(head) - len(tail)
    text = ("\n".join(turns[k]["text"] for k in head)
            + f"\n\n[... {omitted} turns omitted for length ...]\n\n"
            + "\n".join(turns[k]["text"] for k in tail))
    user = (f"Here is the conversation (a long middle section is omitted for length):\n\n{text}\n\n"
            f"Answer this as a short causal narrative — state the reason(s), not just the outcome.\n\n"
            f"QUESTION: {question}\n\nAnswer:")
    resp = server.chat("You are a careful analyst.", user, max_tokens=600,
                       temperature=m["temperature"], seed=cfg["seed"])
    return {"head_turns": len(head), "tail_turns": len(tail), "omitted": omitted, "answer": resp["text"]}


def score_chain(answer: str, gold: dict) -> dict:
    na = normalize(answer)
    links = {}
    for L in gold["links"]:
        hit = any(normalize(p) in na for p in L["any"])
        # numeric 30-40k counts for L3 only if co-occurring with meridian/retail
        if L.get("discriminating") and not hit:
            if ("30000" in na or "40000" in na) and ("meridian" in na or "retail" in na):
                hit = True
        links[L["id"]] = hit
    headline = next(L["id"] for L in gold["links"] if L.get("discriminating"))
    return {"links_present": links, "L3_mid_doc_hinge": links[headline],
            "chain_completeness": sum(links.values()), "n_links": len(links)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["dense", "coupled_full", "verbatim_only", "all"], default="all")
    ap.add_argument("--max-passes", type=int, default=None, help="smoke test: limit state-building passes")
    args = ap.parse_args()
    cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
    p4 = yaml.safe_load((HERE / cfg["p4_config"]).read_text(encoding="utf-8"))
    gold = json.loads((HERE / cfg["gold_chain"]).read_text(encoding="utf-8"))
    question = gold["question"]
    turns = load_turns((HERE / cfg["p4_config"]).resolve().parent / Path(p4["data_dir"]) / "conversation.jsonl")

    # PRE-REG guards: every link matcher fires on source; L3 hinge is mid-doc-exclusive
    src = "\n".join(t["text"] for t in turns)
    for L in gold["links"]:
        assert any(normalize(p) in normalize(src) for p in L["any"]), f"{L['id']} matcher absent from source"
    # (next session: also assert L3 terms do NOT fire on the dense head+tail context — see PRE-REG guards)

    m = p4["model"]
    base = (HERE / cfg["p4_config"]).resolve().parent
    server = LlamaServer(str(base / m["server_exe"]), str(base / m["model_path"]),
                         ctx=m["ctx"], port=m["port"] + 3, threads=m["threads"])
    server.ensure_running()
    arms = ["dense", "coupled_full", "verbatim_only"] if args.arm == "all" else [args.arm]
    out = {}
    for arm in arms:
        print(f"=== {arm} ===", flush=True)
        if arm == "dense":
            r = run_dense_arm(server, cfg, p4, m, turns, question)
        else:
            passes = build_passes(cfg, p4, turns, no_scaffold=(arm == "verbatim_only"))
            r = run_state_arm(server, cfg, p4, m, question, passes, question, max_passes=args.max_passes)
        r["score"] = score_chain(r["answer"], gold)
        out[arm] = r
        print(f"  -> L3_hinge={r['score']['L3_mid_doc_hinge']} "
              f"completeness={r['score']['chain_completeness']}/{r['score']['n_links']}", flush=True)
    server.stop()
    suffix = "_smoke" if args.max_passes else ""
    (HERE / f"p6_results{suffix}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\nVERDICT (L3 mid-doc hinge / chain completeness):")
    for arm in arms:
        s = out[arm]["score"]
        print(f"  {arm}: L3={s['L3_mid_doc_hinge']} chain={s['chain_completeness']}/{s['n_links']}")
    print("differentiator confirmed iff: coupled_full L3=True, dense L3=False, coupled_full>=verbatim_only.")


if __name__ == "__main__":
    main()
