"""P6 — salience-shaping test (whole-document re-weighting). See PRE-REG.md + gold_chain.json.

v2 (2026-06-17): floor-degeneration fixes after the first run was confounded (RESULTS.md):
  - de-duplicate placeholder ADDs (no more 25x identical "# Supply Constraints..." headings)
  - prioritize REPLACE/REMOVE so the op cap never drops content edits for redundant ADDs
  - raise the apply cap; Phase-B tiles all read under the "verbatim" rubric (invite specifics,
    prefer REPLACE -> fills placeholders); removes D1's "scaffold"-stage confound
  - SAVE the generated ops each pass (so "never recorded" is always separable from "truncated")
  - --seed / --temp / --seeds for multi-draw replication (temp 0 is deterministic; >0 gives a rate)

Three arms, scored on what ends up RECORDED IN STATE (ever-recorded across passes), under one
GENERIC brief task (identical across arms; NOT query-conditioned toward the details):
  dense          — single-pass head+tail brief (coverage floor; lacks the mid-doc details)
  verbatim_only  — Phase-B verbatim tiles only, NO scaffold (cold local reader; the control)
  coupled_full   — Phase-A Haiku global scaffold (frozen cache) + Phase-B verbatim tiles (the claim)

Headline = load-bearing x arm INTERACTION: coupled_full records the load-bearing TEST details
preferentially over the prominence-matched CONTROLs, where verbatim_only shows no such preference.

  python experiments/p6_global_synthesis/run.py --seed 42 --temp 0.0          # deterministic ref
  python experiments/p6_global_synthesis/run.py --seed 7  --temp 0.7          # one sampled draw
  python experiments/p6_global_synthesis/run.py --arm coupled_full --max-passes 10  # smoke
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
from pca.planted import build_schedule, load_turns, normalize  # noqa: E402
from pca.textutils import n_tokens  # noqa: E402

SYSTEM = """You are the integration model inside a multi-pass reading architecture. Across K scheduled passes you build a single INTEGRATION STATE: a comprehensive analytical brief of a long conversation you only ever see through partial views.

Each pass you receive: the task, your schedule position, the current integration state (numbered entries S1, S2, ...), one view of the source, and an output demand for this pass.

Respond ONLY with edit operations, one per line, exactly:

ADD END: <text>
ADD S3: <text>
REPLACE S3: <text>
REMOVE S3
NO_CHANGE

Rules: refer to existing entry ids; single-line <text>; no commentary, no fences. Do NOT re-add an entry whose content is already present — REPLACE it to add detail instead."""

RUBRIC = {
    "scaffold": ("RUBRIC: early pass over a heavily compressed view. Build scaffold structure — "
                 "section headings and one-line placeholders via ADD. Do not chase specific figures yet."),
    "concrete": ("RUBRIC: middle pass. Integrate this view's substantive content into the existing "
                 "structure — prefer REPLACE of placeholders over new ADDs. Keep detail concise."),
    "verbatim": ("RUBRIC: near-verbatim pass. Integrate precise specifics — exact figures, names, "
                 "dates, prices, decisions, and the REASONS/causes behind them. Prefer REPLACE of an "
                 "existing placeholder/entry; ADD only a genuinely new fact; NO_CHANGE if already captured."),
}

USER_TMPL = """TASK: {task}

position: {{k: {k}, K: {K}}}

{rubric}

CURRENT INTEGRATION STATE:
{state}

VIEW OF THE SOURCE (this pass):
{view}

Respond with edit operations only."""


def load_scaffold(no_scaffold: bool):
    return None if no_scaffold else json.loads((HERE / "scaffold_haiku.json").read_text(encoding="utf-8"))


def build_passes(p4, turns, scaffold, no_scaffold: bool):
    """Phase-A views = FROZEN Haiku scaffold (coupled_full); Phase-B = verbatim tiles. Every
    Phase-B tile is forced to the 'verbatim' stage so both arms invite specifics identically
    (only the Phase-A scaffold differs). verbatim_only drops Phase A and renumbers."""
    sch = build_schedule(turns, p4["schedule"]["V"], p4["schedule"]["R"],
                         tuple(p4["schedule"]["stage_fracs"]))
    phaseA = [p for p in sch if p["phase"] == "A"]
    phaseB = [p for p in sch if p["phase"] == "B"]
    for p in phaseB:
        p["stage"] = "verbatim"                 # fine sweep: invite specifics, prefer REPLACE
    if no_scaffold:
        passes = [dict(p) for p in phaseB]
    else:
        assert len(scaffold) == len(phaseA), f"scaffold {len(scaffold)} != phaseA {len(phaseA)}"
        for c, p in zip(scaffold, phaseA):
            assert c["turn_lo"] == p["turn_lo"] and c["turn_hi"] == p["turn_hi"], "scaffold/chunk misalign"
            p["view_text"] = c["view_text"]
        passes = [dict(p) for p in phaseA] + [dict(p) for p in phaseB]
    K = len(passes)
    for i, p in enumerate(passes):
        p["k"], p["K"] = i + 1, K
    return passes


def prep_ops(ops, state, cap):
    """De-duplicate placeholder ADDs and prioritize REPLACE/REMOVE so the apply cap never drops
    a content edit in favour of a redundant heading ADD (the v1 floor-degeneration fix)."""
    seen = {normalize(e["text"]) for e in state.entries}
    repl = [o for o in ops if o["op"] in ("REPLACE", "REMOVE")]
    adds = []
    for o in ops:
        if o["op"] == "ADD":
            nt = normalize(o["text"])
            if nt and nt not in seen:
                seen.add(nt); adds.append(o)
    return (repl + adds)[:cap]            # REPLACE/REMOVE first (never truncated), then unique ADDs


def run_state_arm(server, m, task, passes, gold, temp, seed, op_cap, max_passes=None):
    if max_passes:
        passes = passes[:max_passes]
    state = IntegrationState()
    recs, snaps = [], []
    ever = {d["id"]: False for d in gold["details"]}
    first = {d["id"]: None for d in gold["details"]}
    for p in passes:
        user = USER_TMPL.format(task=task.strip(), k=p["k"], K=p["K"],
                                rubric=RUBRIC[p["stage"]], state=state.render(), view=p["view_text"])
        resp = server.chat(SYSTEM, user, max_tokens=m["max_tokens"], temperature=temp, seed=seed)
        parsed = parse_ops(resp["text"], state.ids(), state.next_id)
        ops = prep_ops(parsed.ops, state, op_cap)
        applied = state.apply(ops)
        rendered = state.render()
        now = score_details(rendered, gold)
        for did, v in now.items():
            if v and not ever[did]:
                ever[did], first[did] = True, p["k"]
        snaps.append(rendered)
        recs.append({"k": p["k"], "phase": p["phase"], "stage": p["stage"],
                     "view_tokens": n_tokens(p["view_text"]), "n_gen": len(parsed.ops),
                     "n_applied": applied, "state_tokens": n_tokens(rendered), "present_now": now,
                     "gen_ops": [{"op": o["op"], "text": o.get("text", "")[:200]} for o in parsed.ops]})
        print(f"  pass {p['k']}/{p['K']} ({p['phase']}/{p['stage']}) gen={len(parsed.ops)} "
              f"applied={applied} state={recs[-1]['state_tokens']}tok present={sum(now.values())} ({resp['wall_s']}s)", flush=True)
    final = state.render()
    return {"passes": recs, "final_state": final, "snapshots": snaps,
            "ever_present": ever, "first_pass": first, "final_present": score_details(final, gold)}


def run_dense_arm(server, p4, m, turns, task, temp, seed):
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
    user = (f"TASK: {task.strip()}\n\nHere is the conversation (a long middle section is omitted "
            f"for length):\n\n{text}\n\nWrite the comprehensive analytical brief now, including "
            f"specific figures, names, prices, dates, and the final decision and its reasons.")
    resp = server.chat("You are a careful analyst. Read the conversation excerpts and produce the brief.",
                       user, max_tokens=1500, temperature=temp, seed=seed)
    return {"head_turns": len(head), "tail_turns": len(tail), "omitted": omitted, "final_state": resp["text"]}


def score_details(text: str, gold: dict) -> dict:
    nt = normalize(text)
    return {d["id"]: any(normalize(v) in nt for v in d["any"]) for d in gold["details"]}


def interaction(present: dict, gold: dict) -> dict:
    role = {d["id"]: d["role"] for d in gold["details"]}
    tests = [i for i, r in role.items() if r == "test"]
    ctrls = [i for i, r in role.items() if r == "control"]
    return {"n_test": sum(present[i] for i in tests), "n_control": sum(present[i] for i in ctrls),
            "gap": sum(present[i] for i in tests) - sum(present[i] for i in ctrls)}


def run_guards(gold, turns, scaffold, p4):
    src = normalize("\n".join(t["text"] for t in turns))
    recap = normalize("\n".join(t["text"] for t in turns if t["seg"] in (15, 16)))
    d = p4["dense_baseline"]; fill, hf = d["fill_tokens"], d["head_frac"]; hb = int(fill * hf)
    head, ht, i = [], 0, 0
    while i < len(turns) and ht + turns[i]["tokens"] <= hb: head.append(i); ht += turns[i]["tokens"]; i += 1
    tail, tt, j = [], 0, len(turns) - 1
    while j > i and tt + turns[j]["tokens"] <= (fill - ht): tail.append(j); tt += turns[j]["tokens"]; j -= 1
    dense_ctx = normalize("\n".join(turns[k]["text"] for k in sorted(set(head) | set(tail))))
    sviews = normalize("\n".join(c["view_text"] for c in scaffold))
    for D in gold["details"]:
        assert any(normalize(v) in src for v in D["any"]), f"(a) {D['id']} not on source"
        assert not any(normalize(v) in dense_ctx for v in D["any"]), f"(b) {D['id']} in dense window"
        assert not any(normalize(v) in recap for v in D["any"]), f"(b) {D['id']} in seg15-16 recap"
        assert not any(normalize(v) in sviews for v in D["guard_terms"]), f"(c) {D['id']} in scaffold"
    print("guards (a) fires-on-source / (b) dense+recap floor / (c) salience-not-coverage: PASS", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["dense", "coupled_full", "verbatim_only", "all"], default="all")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--temp", type=float, default=0.0)
    ap.add_argument("--op-cap", type=int, default=24)
    ap.add_argument("--max-passes", type=int, default=None, help="smoke: limit state-building passes")
    args = ap.parse_args()
    cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
    p4 = yaml.safe_load((HERE / cfg["p4_config"]).read_text(encoding="utf-8"))
    gold = json.loads((HERE / cfg["gold_chain"]).read_text(encoding="utf-8"))
    task = gold["task"]
    turns = load_turns((HERE / cfg["p4_config"]).resolve().parent / Path(p4["data_dir"]) / "conversation.jsonl")
    scaffold = json.loads((HERE / "scaffold_haiku.json").read_text(encoding="utf-8"))
    run_guards(gold, turns, scaffold, p4)

    m = p4["model"]
    base = (HERE / cfg["p4_config"]).resolve().parent
    server = LlamaServer(str(base / m["server_exe"]), str(base / m["model_path"]),
                         ctx=m["ctx"], port=m["port"] + 4, threads=m["threads"])
    server.ensure_running()
    arms = ["dense", "verbatim_only", "coupled_full"] if args.arm == "all" else [args.arm]
    tag = "smoke" if args.max_passes else f"s{args.seed}_t{args.temp:g}"
    out = {"_meta": {"seed": args.seed, "temp": args.temp, "op_cap": args.op_cap}}
    for arm in arms:
        print(f"=== {arm} (seed={args.seed} temp={args.temp}) ===", flush=True)
        if arm == "dense":
            r = run_dense_arm(server, p4, m, turns, task, args.temp, args.seed)
            r["final_present"] = score_details(r["final_state"], gold)
            r["ever_present"] = dict(r["final_present"])
            r["first_pass"] = {d["id"]: (1 if r["final_present"][d["id"]] else None) for d in gold["details"]}
        else:
            passes = build_passes(p4, turns, load_scaffold(arm == "verbatim_only"),
                                  no_scaffold=(arm == "verbatim_only"))
            r = run_state_arm(server, m, task, passes, gold, args.temp, args.seed, args.op_cap,
                              max_passes=args.max_passes)
        r["present"] = r["ever_present"]
        r["interaction"] = interaction(r["present"], gold)
        out[arm] = r
        (HERE / f"p6_results_{tag}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  -> ever={r['present']} final={r['final_present']} "
              f"test/ctrl={r['interaction']['n_test']}/{r['interaction']['n_control']}", flush=True)
    server.stop()

    role = {d["id"]: d["role"] for d in gold["details"]}
    print(f"\nVERDICT seed={args.seed} temp={args.temp} — EVER-recorded (T=test,C=control; *=evicted by final):")
    print("  {:14}".format("detail") + "".join(f"{a:>14}" for a in arms))
    for D in gold["details"]:
        row = "  {:14}".format(f"{D['id']}[{role[D['id']][0].upper()}]")
        for a in arms:
            ev = out[a]["ever_present"][D["id"]]
            row += f"{(str(ev) + ('*' if ev and not out[a]['final_present'][D['id']] else '')):>14}"
        print(row)
    print("  " + "-" * (14 + 14 * len(arms)))
    print("  {:14}".format("test-ctrl gap") + "".join(f"{out[a]['interaction']['gap']:>14}" for a in arms))
    print("\nHeadline iff coupled_full gap > verbatim_only gap. Matcher is a PRE-FILTER (esp. D1); adjudicate by manual read.")


if __name__ == "__main__":
    main()
