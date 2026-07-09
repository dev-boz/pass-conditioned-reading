"""P7 — split-unit (code domain) battery runner. See PRE-REG.md.

Differential-recording reframe (eviction ~absent on this floor): the arbitrary table is preserved
by the structure-preserving Phase-A coarse pass (coupled_full records it) but discarded as raw
int-wall noise by the verbatim reader (verbatim_only). Money comparison = coupled_full vs
verbatim_only. Closing question asked ONLY at the end, answered from the final state (no source
re-read); exact-int ANSWER==2353 scoring. Per-pass queried-mapping tracking distinguishes
never-recorded from recorded-then-evicted.

Adapted from p6_global_synthesis/run.py (v2 fixes kept): dedup placeholder ADDs + prioritize
REPLACE/REMOVE so the op cap never drops content for redundant ADDs; save gen_ops every pass; one
"specifics" rubric across all passes (GATE 2 validated the differential comes from the VIEW, not the
rubric). Portable: model paths relative to pca/ root; --threads / --ngl for the target machine.

  python experiments/p7_split_unit/run.py --draws            # full battery (4 draws x 3 arms)
  python experiments/p7_split_unit/run.py --seed 42 --temp 0 # one draw
  python experiments/p7_split_unit/run.py --arm coupled_full --max-passes 8   # smoke
  python experiments/p7_split_unit/run.py --draws --threads 24 --ngl 99       # Threadripper+1080Ti
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import requests
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))

from pca.editops import IntegrationState, parse_ops  # noqa: E402
from pca.llm import LlamaServer, OpenRouterClient, KiroClient  # noqa: E402
from pca.planted import build_schedule, normalize     # noqa: E402
from pca.textutils import n_tokens                     # noqa: E402
from compress_code import compress_code               # noqa: E402
from verify_fixture import load_turns                  # noqa: E402

# Integration prompt = NEUTRAL broad brief (P6-lineage), UNCHANGED. Per the standing discipline,
# only the COMPRESSOR (what the architecture shows the model) is modified for P7 — never the
# instructions (how the model is told to think). No append-only / anti-rewrite / data-structure
# directives here; that would hand-install the cognition E2′ must learn.
TASK = ("You are building a single comprehensive analytical brief of a large codebase that you "
        "only ever see through partial views: what the system does, how its modules are organized, "
        "what the important components do, and how the parts fit together.")

SYSTEM = """You are the integration model inside a multi-pass reading architecture. Across K scheduled passes you build a single INTEGRATION STATE: a comprehensive analytical brief of a large codebase you only ever see through partial views.

Each pass you receive: the task, your schedule position, the current integration state (numbered entries S1, S2, ...), one view of the source, and an output demand for this pass.

Respond ONLY with edit operations, one per line, exactly:

ADD END: <text>
ADD S3: <text>
REPLACE S3: <text>
REMOVE S3
NO_CHANGE

Rules: refer to existing entry ids; single-line <text>; no commentary, no fences. Do NOT re-add an entry whose content is already present — REPLACE it to add detail instead."""

RUBRIC = ("RUBRIC: integrate this view's precise specifics into the brief — exact values, names, "
          "definitions, and the relationships among them. Prefer REPLACE of an existing entry to add "
          "detail; ADD a genuinely new fact; NO_CHANGE if already captured.")

# FAIR-SHOT specifics-demanding prompt (--specifics): a GENERIC instruction to build a thorough
# technical brief that includes constants and the data structures the code defines — with NO mention
# of the probe, the surcharge table, region 23, or "the table you'll be asked about". This is the
# analogue of P6's verbatim rubric ("integrate precise specifics — exact figures, names, dates").
# It is fair-shot (tells the model what KIND of brief to build), NOT forcing (does not point at the
# answer). Used to test "can it work AT ALL" under a fair shot, vs the un-prompted neutral bar.
SPECIFICS_TASK = (
    "You are building a single comprehensive TECHNICAL brief of a large codebase that you only ever "
    "see through partial views. Capture both what the system does and the concrete details an "
    "engineer would need to reason about its behaviour: the exact values of constants and "
    "configuration, the data structures the code defines together with their contents, the key "
    "functions, and how the parts fit together.")
SPECIFICS_RUBRIC = (
    "RUBRIC: integrate this view's precise specifics into the brief — exact constant values, the "
    "contents of any data structure the code defines (its keys and values), function signatures, and "
    "the relationships among them. Prefer REPLACE of an existing entry to add detail; ADD a genuinely "
    "new fact; NO_CHANGE if already captured.")

USER_TMPL = """TASK: {task}

position: {{k: {k}, K: {K}}}

{rubric}

CURRENT INTEGRATION STATE:
{state}

VIEW OF THE SOURCE (this pass):
{view}

Respond with edit operations only."""

CLOSING_SYSTEM = ("You are answering a question using ONLY the integration state below (an analytical "
                  "brief built from a codebase across many passes). Use only values present in the "
                  "state; do not invent numbers. Reason briefly, then end with a line 'ANSWER: "
                  "<integer>'. If the state lacks the needed value, end with 'ANSWER: INSUFFICIENT'.")
# AWARENESS A/B (closing-side, --permit-derive): relaxes the "do not invent numbers" suppressor so the
# closing model may COMBINE values it already holds, while still barring absent values. Task-agnostic:
# no mention of the surcharge/adder/addition — only a generic permission to derive arithmetically.
CLOSING_SYSTEM_DERIVE = ("You are answering a question using ONLY the integration state below (an "
                  "analytical brief built from a codebase across many passes). Base your answer on values "
                  "present in the state; you MAY compute and combine those values arithmetically to derive "
                  "the answer. Do not introduce values that are absent from the state. Reason briefly, then "
                  "end with a line 'ANSWER: <integer>'. If the state lacks the values needed, end with "
                  "'ANSWER: INSUFFICIENT'.")


def prep_ops(ops, state, cap):
    """Dedup placeholder ADDs; REPLACE/REMOVE first so the cap never drops a content edit (P6 v2)."""
    seen = {normalize(e["text"]) for e in state.entries}
    repl = [o for o in ops if o["op"] in ("REPLACE", "REMOVE")]
    adds = []
    for o in ops:
        if o["op"] == "ADD":
            nt = normalize(o["text"])
            if nt and nt not in seen:
                seen.add(nt); adds.append(o)
    return (repl + adds)[:cap]


def _kv(nt, table):
    return sum(1 for k, val in table.items()
              if normalize(f"{k}: {val}") in nt or normalize(f"{k}:{val}") in nt)


def _kv_str(nt, table):
    """Verbatim str->str pair recorded (pre-filter; PRE-REG scoring note — adjudicate by manual read)."""
    return sum(1 for k, val in table.items() if normalize(f'"{k}": "{val}"') in nt)


def mapping_present(text: str, spec: dict) -> dict:
    """Recording pre-filters (manual read adjudicates). queried_mapping/kv_count = answer table;
    control_kv = arbitrary int control; relevant_kv / alias_kv = the RELEVANCE-CONTROL pair
    (EVENT_DISPATCH vs TOKEN_ALIASES — matched str->str tables, same chunk/pass, only relevance differs)."""
    nt = normalize(text)
    q, v = spec["queried_code"], spec["table_value_for_queried"]
    queried = (normalize(f"{q}: {v}") in nt or normalize(f"{q}:{v}") in nt)
    rc = spec.get("relevance_control", {})
    return {"queried_mapping": queried, "kv_count": _kv(nt, spec["table"]),
            "control_kv": _kv(nt, spec["control_table"]),
            "relevant_kv": _kv_str(nt, rc.get("relevant_table", {})),
            "alias_kv": _kv_str(nt, rc.get("arbitrary_table", {}))}


def closing_answer(server, m, state_text, spec, temp, seed, permit_derive=False):
    sys_prompt = CLOSING_SYSTEM_DERIVE if permit_derive else CLOSING_SYSTEM
    user = (f"INTEGRATION STATE:\n{state_text}\n\nQuestion: {spec['scoring_question']}\n"
            "Reason briefly from the state, then end with: ANSWER: <integer>")
    try:
        resp = server.chat(sys_prompt, user, max_tokens=500, temperature=temp, seed=seed)
    except requests.exceptions.HTTPError as e:
        code = getattr(getattr(e, "response", None), "status_code", None)
        print(f"  !! closing HTTP {code} (state too large for context) -> answer=None", flush=True)
        return {"answer": None, "correct": False, "wall_s": None,
                "text": f"<closing failed: HTTP {code}>", "overflow_http": code}
    txt = resp["text"]
    mm = re.search(r"ANSWER:\s*(-?\d[\d,]*)", txt)
    ans = int(mm.group(1).replace(",", "")) if mm else None
    return {"answer": ans, "correct": ans == spec["ground_truth_answer"],
            "wall_s": resp["wall_s"], "text": txt, "provider": resp.get("provider")}


def build_passes(turns, cfg, scaffold, no_scaffold: bool):
    s = cfg["schedule"]
    sch = build_schedule(turns, s["V"], s["R"], tuple(s["stage_fracs"]))
    phaseA = [p for p in sch if p["phase"] == "A"]
    phaseB = [p for p in sch if p["phase"] == "B"]
    if no_scaffold:
        passes = [dict(p) for p in phaseB]
    else:
        assert len(scaffold) == len(phaseA), f"scaffold {len(scaffold)} != phaseA {len(phaseA)}"
        for c, p in zip(scaffold, phaseA):
            assert c["turn_lo"] == p["turn_lo"] and c["turn_hi"] == p["turn_hi"], "scaffold misalign"
            p["view_text"] = c["view_text"]
        passes = [dict(p) for p in phaseA] + [dict(p) for p in phaseB]
    for i, p in enumerate(passes):
        p["k"], p["K"] = i + 1, len(passes)
    return passes


def run_state_arm(server, m, passes, spec, temp, seed, op_cap, max_passes=None, inject_pos=False):
    if max_passes:
        passes = passes[:max_passes]
    state = IntegrationState()
    recs, snaps = [], []
    ever_queried, first_queried, first_phase = False, None, None
    truncated, trunc_pass, trunc_http = False, None, None
    T = max((p.get("turn_hi", 0) for p in passes), default=0)
    for p in passes:
        user = USER_TMPL.format(task=TASK.strip(), k=p["k"], K=p["K"], rubric=RUBRIC,
                                state=state.render(), view=p["view_text"])
        if inject_pos:
            user = (f"You are on reading pass {p['k']} of {p['K']}; this is one partial "
                    f"{p['phase']}-view covering source turns {p['turn_lo']}–{p['turn_hi']} of {T} "
                    f"total, and {p['K'] - p['k']} pass(es) remain.\n\n" + user)
        try:
            resp = server.chat(SYSTEM, user, max_tokens=m["max_tokens"], temperature=temp, seed=seed)
        except requests.exceptions.HTTPError as e:
            trunc_http = getattr(getattr(e, "response", None), "status_code", None)
            truncated, trunc_pass = True, p["k"]
            print(f"  !! pass {p['k']}/{p['K']} ({p['phase']}) HTTP {trunc_http} "
                  f"(input context exhausted) -> TRUNCATING arm at state={n_tokens(state.render())}tok; "
                  f"closing on state so far", flush=True)
            break
        parsed = parse_ops(resp["text"], state.ids(), state.next_id)
        ops = prep_ops(parsed.ops, state, op_cap)
        applied = state.apply(ops)
        rendered = state.render()
        mp = mapping_present(rendered, spec)
        if mp["queried_mapping"] and not ever_queried:
            ever_queried, first_queried, first_phase = True, p["k"], p["phase"]
        snaps.append(rendered)
        recs.append({"k": p["k"], "phase": p["phase"], "view_tokens": n_tokens(p["view_text"]),
                     "n_gen": len(parsed.ops), "n_applied": applied,
                     "state_tokens": n_tokens(rendered), "mapping": mp, "provider": resp.get("provider"),
                     "gen_ops": [{"op": o["op"], "text": o.get("text", "")[:200]} for o in parsed.ops]})
        print(f"  pass {p['k']}/{p['K']} ({p['phase']}) gen={len(parsed.ops)} applied={applied} "
              f"state={recs[-1]['state_tokens']}tok q_map={mp['queried_mapping']} kv={mp['kv_count']} "
              f"ctrl={mp['control_kv']} REL={mp['relevant_kv']} ALIAS={mp['alias_kv']} ({resp['wall_s']}s)",
              flush=True)
    final = state.render()
    return {"passes": recs, "final_state": final, "snapshots": snaps,
            "final_mapping": mapping_present(final, spec),
            "queried_ever": ever_queried, "queried_first_pass": first_queried,
            "queried_first_phase": first_phase,
            "truncated": truncated, "truncated_at_pass": trunc_pass, "truncated_http": trunc_http,
            "n_passes_run": len(recs)}


def run_dense_arm(server, cfg, m, turns, temp, seed):
    d = cfg["dense_baseline"]
    fill, hf = d["fill_tokens"], d["head_frac"]
    head, ht, i = [], 0, 0
    while i < len(turns) and ht + turns[i]["tokens"] <= int(fill * hf):
        head.append(i); ht += turns[i]["tokens"]; i += 1
    tail, tt, j = [], 0, len(turns) - 1
    while j > i and tt + turns[j]["tokens"] <= (fill - ht):
        tail.append(j); tt += turns[j]["tokens"]; j -= 1
    tail = sorted(tail)
    omitted = len(turns) - len(head) - len(tail)
    text = ("\n".join(turns[k]["text"] for k in head)
            + f"\n\n[... {omitted} blocks omitted for length ...]\n\n"
            + "\n".join(turns[k]["text"] for k in tail))
    user = (f"TASK: {TASK.strip()}\n\nHere is the codebase (a long middle section is omitted for "
            f"length):\n\n{text}\n\nWrite the comprehensive analytical brief now.")
    resp = server.chat("You are a careful code analyst. Read the excerpts and produce the brief.",
                       user, max_tokens=1500, temperature=temp, seed=seed)
    return {"head_turns": len(head), "tail_turns": len(tail), "omitted": omitted,
            "final_state": resp["text"], "provider": resp.get("provider")}


def run_guards(spec, turns, scaffold, cfg):
    entry = f"{spec['queried_code']}: {spec['table_value_for_queried']}"
    adder = f"RECONCILIATION_ADDER_CENTS = {spec['reconciliation_adder_cents']}"
    call = "compute_line_surcharge"
    src = "\n".join(t["text"] for t in turns)
    assert entry in src and adder in src, "(A) fragment not on source"
    d = cfg["dense_baseline"]; fill, hf = d["fill_tokens"], d["head_frac"]
    head, ht, i = [], 0, 0
    while i < len(turns) and ht + turns[i]["tokens"] <= int(fill * hf): head.append(i); ht += turns[i]["tokens"]; i += 1
    tail, tt, j = [], 0, len(turns) - 1
    while j > i and tt + turns[j]["tokens"] <= (fill - ht): tail.append(j); tt += turns[j]["tokens"]; j -= 1
    dense_ctx = "\n".join(turns[k]["text"] for k in sorted(set(head) | set(tail)))
    assert entry not in dense_ctx and call not in dense_ctx, "(B) fragment in dense window"
    all_views = "\n".join(c["view_text"] for c in scaffold)
    assert entry in all_views and adder in all_views, "(C1) table/adder not in frozen scaffold"
    s = cfg["schedule"]
    phaseB = [p for p in build_schedule(turns, s["V"], s["R"], tuple(s["stage_fracs"])) if p["phase"] == "B"]
    f1 = [i for i, p in enumerate(phaseB) if entry in p["view_text"]]
    f2 = [i for i, p in enumerate(phaseB) if call in p["view_text"]]
    assert f1 and f2 and not (set(f1) & set(f2)), "(C2) split not real (fragment overlap)"
    print(f"guards PASS: (A) on-source (B) dense-floor (C1) scaffold-carries-table "
          f"(C2) split real (f1 tiles {f1}, f2 tiles {f2})", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["dense", "coupled_full", "verbatim_only", "all"], default="all")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--temp", type=float, default=0.0)
    ap.add_argument("--draws", action="store_true", help="run the full pre-registered draw set")
    ap.add_argument("--op-cap", type=int, default=None)
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--ngl", type=int, default=None, help="n_gpu_layers (99 = full offload on CUDA build)")
    ap.add_argument("--max-passes", type=int, default=None, help="smoke: limit state-building passes")
    ap.add_argument("--scaffold", default="scaffold_struct.json",
                    help="frozen Phase-A scaffold (default v2; use scaffold_v1.json for the control)")
    ap.add_argument("--specifics", action="store_true",
                    help="FAIR-SHOT generic specifics-demanding prompt (record exact values + data "
                         "structures the code defines; no probe reference) instead of the neutral brief")
    ap.add_argument("--model", default=None, help="model registry key (7b/14b); default from config")
    ap.add_argument("--inject-pos", action="store_true",
                    help="AWARENESS A/B (recorder-side): prepend a salient natural-language position/"
                         "coverage line to each recording pass (pass k/K, source span, passes remaining)")
    ap.add_argument("--permit-derive", action="store_true",
                    help="AWARENESS A/B (closing-side): let the closing model compute/combine values "
                         "present in the state (relaxes 'do not invent numbers'); task-agnostic")
    args = ap.parse_args()
    if args.specifics:
        global TASK, RUBRIC
        TASK, RUBRIC = SPECIFICS_TASK, SPECIFICS_RUBRIC

    cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
    spec = json.loads((HERE / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    scaffold = json.loads((HERE / args.scaffold).read_text(encoding="utf-8"))
    print(f"scaffold: {args.scaffold}", flush=True)
    turns = load_turns(HERE / "fixture" / "host_doc.jsonl")
    run_guards(spec, turns, scaffold, cfg)

    mkey = args.model or cfg.get("default_model", "7b")
    m = cfg["models"][mkey]
    inject_pos = bool(m.get("inject_pos")) or args.inject_pos
    permit_derive = bool(m.get("permit_derive")) or args.permit_derive
    print(f"model: {mkey} ({m.get('model_path') or m.get('api_model') or m.get('kiro_model')})"
          f"{'  [+inject-pos]' if inject_pos else ''}{'  [+permit-derive]' if permit_derive else ''}", flush=True)
    op_cap = args.op_cap if args.op_cap is not None else cfg["op_cap"]
    threads = args.threads if args.threads is not None else m.get("threads", 8)
    ngl = args.ngl if args.ngl is not None else m.get("n_gpu_layers", 0)
    if m.get("kiro"):
        server = KiroClient(m["kiro_model"], ctx=m.get("ctx", 200000), max_tokens=m["max_tokens"],
                            agent=m.get("kiro_agent"), effort=m.get("kiro_effort"))
        print(f"  KIRO (CONFOUNDED; agent={m.get('kiro_agent') or 'default'} effort={m.get('kiro_effort') or 'default'}; "
              f"no temp/seed/max_tokens): {m['kiro_model']}", flush=True)
    elif m.get("api"):
        server = OpenRouterClient(m["api_model"], ctx=m["ctx"], max_tokens=m["max_tokens"],
                                  base_url=m.get("api_base"),
                                  api_key_env=m.get("api_key_env", "OPENROUTER_API_KEY"),
                                  provider_order=m.get("api_provider_order"),
                                  allow_fallbacks=m.get("api_allow_fallbacks", True))
        prov = m.get("api_provider_order")
        print(f"  API: {m['api']} / {m['api_model']}"
              + (f" | pinned provider={prov} fallbacks={m.get('api_allow_fallbacks', True)}" if prov else ""),
              flush=True)
    else:
        server = LlamaServer(str(ROOT / m["server_exe"]), str(ROOT / m["model_path"]),
                             ctx=m["ctx"], port=m["port"] + 7, threads=threads, n_gpu_layers=ngl)
    server.ensure_running()

    draws = [tuple(d) for d in cfg["draws"]] if args.draws else [(args.seed, args.temp)]
    arms = ["dense", "verbatim_only", "coupled_full"] if args.arm == "all" else [args.arm]
    for seed, temp in draws:
        pm = "spec" if args.specifics else "neutral"
        mp = f"mp{args.max_passes}_" if args.max_passes else ""
        tag = f"{mkey}_{mp}{pm}_s{seed}_t{temp:g}"
        out = {"_meta": {"model": mkey, "seed": seed, "temp": temp, "op_cap": op_cap,
                         "threads": threads, "n_gpu_layers": ngl, "prompt": pm,
                         "inject_pos": inject_pos, "permit_derive": permit_derive,
                         "ground_truth": spec["ground_truth_answer"]}}
        for arm in arms:
            print(f"=== {arm} (seed={seed} temp={temp}) ===", flush=True)
            if arm == "dense":
                r = run_dense_arm(server, cfg, m, turns, temp, seed)
                r["final_mapping"] = mapping_present(r["final_state"], spec)
                r["queried_ever"] = r["final_mapping"]["queried_mapping"]
            else:
                passes = build_passes(turns, cfg, scaffold, no_scaffold=(arm == "verbatim_only"))
                r = run_state_arm(server, m, passes, spec, temp, seed, op_cap,
                                  max_passes=args.max_passes, inject_pos=inject_pos)
            r["closing"] = closing_answer(server, m, r["final_state"], spec, temp, seed,
                                          permit_derive=permit_derive)
            out[arm] = r
            (HERE / f"p7_results_{tag}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                                         encoding="utf-8")
            print(f"  -> closing ANSWER={r['closing']['answer']} correct={r['closing']['correct']} "
                  f"| final q_map={r['final_mapping']['queried_mapping']} kv={r['final_mapping']['kv_count']} "
                  f"ctrl_kv={r['final_mapping']['control_kv']} "
                  f"first_pass={r.get('queried_first_pass')} phase={r.get('queried_first_phase')}", flush=True)
    server.stop()

    print(f"\nMONEY COMPARISON = coupled_full vs verbatim_only on closing ANSWER=={spec['ground_truth_answer']}; "
          "State-D guard = coupled's queried mapping must first appear in a Phase-A pass (phase 'A').")


if __name__ == "__main__":
    main()
