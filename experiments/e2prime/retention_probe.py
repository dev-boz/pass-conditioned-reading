"""RETENTION probe — the fast exploration instrument ($0, frozen weights).

WHY THIS EXISTS. A full pyramid chain-gate draw is 63 passes and ~21 minutes, so a ten-seed arm
costs ~3.5 h. That is far too slow to explore with. The 2026-08-01 measurements located the failure
precisely enough that it can be tested directly and cheaply instead:

  across 3,941 REPLACEs in the pyramid student draws
    33% byte-identical no-ops
    26% target an entry with <20% lexical overlap with the current view
    37% DROP numeric literals the entry already held
  and of the 3,226 REPLACEs that PASSED the strict guard and were applied,
    1,003 (31%) destroyed numeric detail — 435 of them five or more literals at once.

The chain gate showed the consequence: across arms the queried binding entered the state in 4 draws
and was gone by the close in 3. `llm_roleaware` hands the model the complete answer in pass 1 and
still closes 0/10, so the blocker is not delivery, coverage, compression or the recording demand —
it is whether an already-recorded fact SURVIVES the passes that follow.

So this probe starts from a state that ALREADY HOLDS the fact and runs the subsequent views, asking
one question: what keeps it there? Twelve passes instead of sixty-three, and a small start state,
makes a condition cost minutes rather than hours.

START STATE — declared. It is the student's OWN state, lifted from the `llm_roleaware` chain-gate
run at the earliest pass where that run recorded the binding, and held FIXED across seeds so every
draw begins with the fact present. Self-generated, not hand-written: no oracle. Holding it fixed is
what makes this a retention measurement rather than another recording measurement.

CONDITIONS
  base      strict guard, trained verbatim rubric — the status quo
  retain    guard="retain": a REPLACE may not drop numeric literals the entry held (editops)
  noclobber strict guard + an anti-clobber sentence spliced into the rubric
  both      retain guard + the sentence
  nobudget  strict guard, the state-budget sentence REMOVED from the system prompt

`nobudget` is its own hypothesis: the prompt tells the model to stay under 4,000 tokens and
"consolidate rather than truncate", the state runs to 13,489, and consolidation is exactly the
destructive REPLACE being measured. The instruction may be causing the pathology it is blamed for.

  python experiments/e2prime/retention_probe.py --dry-run
  python experiments/e2prime/retention_probe.py --conditions base,retain --seeds 1-5
  python experiments/e2prime/retention_probe.py --summarize
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P7 = ROOT / "experiments" / "p7_split_unit"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(P7))
sys.path.insert(0, str(HERE))

from pca.editops import IntegrationState, parse_ops, _lost_literals   # noqa: E402
from pca.llm import LlamaServer                                       # noqa: E402
from pca.teacher_gen import _system_prompt, _user_prompt              # noqa: E402
from pca.textutils import n_tokens                                    # noqa: E402
from verify_fixture import load_turns                                 # noqa: E402
from stagea_chain_gate import load_config, pyramid_stage              # noqa: E402
from verify_pyramid_schedule import load_arm                          # noqa: E402
from stagea_p1_probes import MODELS, PROBE_TOKENS, state_from_lines   # noqa: E402

OUT_DIR = ROOT / "runs" / "stageA_chain_gate" / "_retention"
TEMP = 0.7
MAX_TOKENS = 900
OP_CAP = 24

# Anti-clobber splice. Generic — names no probe token; the forcing-boundary assert covers it.
# Targets the two measured pathologies directly (detail loss, and editing entries this view does
# not cover), in the maintainer's own framing: don't change unless you're sure, don't lose detail.
NOCLOBBER = (" Before you REPLACE an entry, check that this view is actually about that entry: if "
             "the view says nothing about what an entry records, leave it alone. Never rewrite an "
             "entry in a way that drops exact values, names or quotes it already holds — if you "
             "are adding detail, carry the existing detail through unchanged. When in doubt, ADD a "
             "new entry rather than overwrite an existing one.")

BUDGET_RE = re.compile(r"State budget: stay under \d+ tokens; consolidate rather than truncate\.\s*")

# ---------------------------------------------------------------- importance marks (2026-08-02)
# The maintainer's idea, and the simplified form of the proposal's confidence extra: let earlier
# passes tell later passes which entries are load-bearing, so later passes do not clobber them.
#
# Strictly more general than guard="retain", which protects only NUMBERS and cannot tell a
# load-bearing constant from an incidental one. A per-entry mark protects whatever is marked.
#
# Design constraint from evidence: P1h showed this student CANNOT emit a mark — asked to write
# "988*" for unconfirmed values, with a worked example in the prompt, it produced zero asterisks
# across ten draws. So a model-AUTHORED mark probably fails here for reasons unrelated to whether
# the mechanism works. Hence three variants, separating "can the model USE an importance signal"
# from "can the model PRODUCE one" — the same two skills that came apart on compose:
#
#   selfmark     the model marks its own entries (the idea as stated; expected to hit the P1h ceiling)
#   marked_soft  the HARNESS marks entries and renders the mark; the rubric asks the model to
#                respect it; nothing is enforced. THE INTERESTING CELL.
#   marked_hard  same, plus ops targeting a marked entry are refused outright.
#
# The marking rule is probe-blind and content-class based: an entry is load-bearing if it carries a
# multi-digit literal or a declared ALL-CAPS identifier — i.e. something a later reader could not
# reconstruct. It never inspects what the entry is about.
# SELECTIVITY MATTERS, and the first rule failed on it. "Contains a multi-digit literal or an
# ALL-CAPS token" flagged 70 of 70 entries — in a code state, every entry has a `digest14`, an
# `i%84` or a `weight>0.531`. A mark that applies to everything carries no information; that is the
# salience problem one level up. The rule below marks a BINDING — a named constant or a key given a
# value — which is what "a later reader could not reconstruct" actually means.
_MARK_BIND = re.compile(
    r"[A-Z][A-Z0-9]{2,}(?:_[A-Z0-9]+)+\s*[:=]\s*\d"     # NAMED_CONSTANT = 1365
    r"|(?<!\d)\d{1,4}\s*(?::|=|->|→|=>)\s*\d{2,}(?!\d)"  # 23: 988 / 23→988 (a table row)
)
MARK = "[!]"


def is_load_bearing(text: str) -> bool:
    return bool(_MARK_BIND.search(text or ""))


def render_marked(st) -> tuple[str, set[str]]:
    """State rendering with `[!]` on load-bearing entries. Does not mutate the entries — the mark
    is a VIEW of the state, so nothing downstream inherits a marker the model did not write."""
    lines, marked = [], set()
    for e in st.entries:
        if is_load_bearing(e["text"]):
            marked.add(e["id"])
            lines.append(f"{e['id']} {MARK}: {e['text']}")
        else:
            lines.append(f"{e['id']}: {e['text']}")
    return ("\n".join(lines) if lines else "(empty — no entries yet)"), marked


MARKS_RUBRIC = (
    f" Entries flagged {MARK} in the state hold exact values, names or identifiers that an earlier "
    f"pass judged load-bearing and that a later reader could not reconstruct. Do not REPLACE or "
    f"REMOVE a {MARK} entry unless this view gives you a more complete version of the same "
    f"content — and then carry every value it already holds through into the new text. Prefer "
    f"adding a new entry over rewriting a flagged one.")

SELFMARK_RUBRIC = (
    f" When an entry you write holds an exact value, name or identifier that a later reader could "
    f"not reconstruct on its own, begin that entry's text with {MARK} to flag it as load-bearing. "
    f"Leave {MARK} off entries that only describe structure. Treat any {MARK} entry already in the "
    f"state as one you should not overwrite.")


def build_system(cfg: dict, stage: str, noclobber: bool, nobudget: bool,
                 marks: str | None = None) -> str:
    sysp = _system_prompt(cfg, stage)
    if marks:
        marker = "\n\nState budget:"
        assert marker in sysp, "system prompt shape changed; marks splice has no anchor"
        splice = MARKS_RUBRIC if marks == "shown" else SELFMARK_RUBRIC
        sysp = sysp.replace(marker, splice + marker, 1)
    if noclobber:
        # Anchor on the section boundary, not on a rubric sentence: this probe spans scaffold,
        # integrate AND verbatim passes, and the three rubrics share no sentence. Splicing before
        # "State budget:" appends to whichever "This pass:" rubric is in force. Must run BEFORE
        # the nobudget strip, which removes that anchor.
        marker = "\n\nState budget:"
        assert marker in sysp, "system prompt shape changed; NOCLOBBER splice has no anchor"
        sysp = sysp.replace(marker, NOCLOBBER + marker, 1)
    if nobudget:
        sysp2 = BUDGET_RE.sub("", sysp)
        assert sysp2 != sysp, "budget sentence not found; --nobudget would be a no-op"
        sysp = sysp2
    leaks = [t for t in PROBE_TOKENS if t.lower() in sysp.lower()]
    assert not leaks, f"forcing-boundary violation: {leaks}"
    return sysp


CONDITIONS = {
    "base":      {"guard": "strict", "noclobber": False, "nobudget": False},
    "retain":    {"guard": "retain", "noclobber": False, "nobudget": False},
    "noclobber": {"guard": "strict", "noclobber": True,  "nobudget": False},
    "both":      {"guard": "retain", "noclobber": True,  "nobudget": False},
    "nobudget":  {"guard": "strict", "noclobber": False, "nobudget": True},
    # importance marks — see the MARK block above
    "marked_soft": {"guard": "strict", "noclobber": False, "nobudget": False,
                    "marks": "shown", "enforce_marks": False},
    "marked_hard": {"guard": "strict", "noclobber": False, "nobudget": False,
                    "marks": "shown", "enforce_marks": True},
    "selfmark":    {"guard": "strict", "noclobber": False, "nobudget": False,
                    "marks": "self", "enforce_marks": False},
}


def find_start_state(spec: dict, pick: str = "largest", pin_run: str | None = None,
                     pin_pass: int | None = None) -> tuple[list[str], dict]:
    """The student's OWN state, lifted from a pyramid chain-gate draw at a pass where it held the
    binding. Declared, self-generated, fixed across seeds.

    `pick`:
      largest   the biggest such state in the archive (default). THIS MATTERS. The first run of
                this probe used the earliest such state — 1,115 tok, 29 entries — and every
                condition INCLUDING the baseline held 10/10: a ceiling, no headroom, nothing to
                measure. That is the same error that invalidated p1g, whose anti-grind arm was
                tested against ~11-entry states while the 26% pathology lives in the real
                7.7K-token state. Clobber is a large-state phenomenon, so the start state has to be
                large or the instrument cannot see it.
      earliest  the first such state; reproduces the ceiling above. Kept for the record.
    """
    qcode, tval = spec["queried_code"], spec["table_value_for_queried"]
    pat = re.compile(rf"(?<!\d){qcode}\s*:\s*{tval}(?!\d)")
    cands = []
    for f in sorted((ROOT / "runs" / "stageA_chain_gate_pyramid").glob("*/student_s*_t0.7.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        for p in r["passes"]:
            if p["flags"]["queried_mapping"]:
                cands.append({"k": p["k"], "arm": f.parent.name, "src": f.name,
                              "tok": p["state_tokens"], "snap": p["state_snapshot"]})
    if not cands:
        raise SystemExit("no pyramid draw ever held the binding — no start state exists.")
    if pin_run:
        arm, _, name = pin_run.replace("\\", "/").rpartition("/")
        sel = [c for c in cands if c["src"] == name and (not arm or c["arm"] == arm)
               and (pin_pass is None or c["k"] == pin_pass)]
        if not sel:
            raise SystemExit(f"pinned start state not found: {pin_run} pass={pin_pass}")
        best = max(sel, key=lambda c: c["k"]) if pin_pass is None else sel[0]
    else:
        best = (max(cands, key=lambda c: c["tok"]) if pick == "largest"
                else min(cands, key=lambda c: c["k"]))
    lines = [f"{e['id']}: {e['text']}" for e in best["snap"]["entries"]]
    holder = [e["id"] for e in best["snap"]["entries"] if pat.search(e["text"])]
    return lines, {"from_arm": best["arm"], "from_run": best["src"], "at_pass": best["k"],
                   "state_tokens": best["tok"], "n_entries": len(lines), "pick": pick,
                   "holder_entry": holder, "self_generated": True,
                   "n_candidate_states": len(cands),
                   "note": "student's own state from a pyramid chain-gate draw; fixed across seeds "
                           "so every draw starts with the fact present"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--conditions", default="base,retain,noclobber,both,nobudget")
    ap.add_argument("--views", default="llm_roleaware")
    ap.add_argument("--model", default="student", choices=sorted(MODELS))
    ap.add_argument("--seeds", default="1-10")
    ap.add_argument("--passes", type=int, default=12, help="views to run after the start state")
    ap.add_argument("--start-pick", choices=["largest", "earliest"], default="largest",
                    help="which archived binding-holding state to start from. 'earliest' is a "
                         "1.1K-tok state and produces a 10/10 ceiling in every condition")
    # AUTO-SELECTION IS NOT REPRODUCIBLE. `largest` re-scans the archive, so adding a run silently
    # moves the start state: the marks probe picked pass 60 instead of pass 56, leaving a 3-view
    # window, and every condition returned 10/10 for want of anything to measure. Pin the state
    # explicitly for any comparison that has to mean something.
    ap.add_argument("--start-run", default=None,
                    help="pin the start state, e.g. 'graded/student_s5_t0.7.json'")
    ap.add_argument("--start-pass", type=int, default=None, help="pin the pass within --start-run")
    ap.add_argument("--window", choices=["next", "verbatim"], default="next",
                    help="next = the views immediately following the start state (where the "
                         "llm_roleaware run lost the binding, passes 7 and 17); verbatim = the "
                         "level-6 sweep (where the graded run lost it, pass 57)")
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--ctx", type=int, default=24576)
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--threads", type=int, default=24)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--summarize", action="store_true")
    ap.add_argument("--redo", action="store_true")
    args = ap.parse_args()

    if args.summarize:
        summarize()
        return

    seeds: list[int] = []
    for part in args.seeds.split(","):
        if "-" in part:
            a, b = part.split("-")
            seeds += list(range(int(a), int(b) + 1))
        else:
            seeds.append(int(part))

    cfg = load_config()
    spec = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    turns = load_turns(P7 / "fixture" / "host_doc.jsonl")
    views, vmeta = load_arm(args.views, cfg["schedule"]["code"]["V"], 2, turns)
    n_levels = len({v["level"] for v in views})
    fracs = tuple(cfg["schedule"]["code"]["stage_fracs"])

    lines, start_meta = find_start_state(spec, args.start_pick, args.start_run, args.start_pass)
    maxlv = max(v["level"] for v in views)
    if args.window == "verbatim":
        todo = [v for v in views if v["level"] == maxlv][:args.passes]
    else:
        todo = [v for v in views if v["k"] > start_meta["at_pass"]][:args.passes]
    qcode, tval = spec["queried_code"], spec["table_value_for_queried"]
    pat = re.compile(rf"(?<!\d){qcode}\s*:\s*{tval}(?!\d)")

    print(f"start state: {start_meta['n_entries']} entries, {n_tokens(chr(10).join(lines))} tok, "
          f"from {start_meta['from_run']} pass {start_meta['at_pass']} "
          f"(holder {start_meta['holder_entry']})")
    print(f"then {len(todo)} views: k={[v['k'] for v in todo]}")
    print(f"conditions: {args.conditions} | seeds {seeds} | model {args.model}")

    if args.dry_run:
        for c in args.conditions.split(","):
            cd = CONDITIONS[c]
            sysp = build_system(cfg, pyramid_stage(todo[0]["level"], n_levels, fracs),
                                cd["noclobber"], cd["nobudget"], cd.get("marks"))
            print(f"\n--- {c}: guard={cd['guard']} marks={cd.get('marks')} "
                  f"enforce={cd.get('enforce_marks')} ({len(sysp)} chars) ---\n{sysp[-520:]}")
        st0 = state_from_lines(lines)
        mtxt, mids = render_marked(st0)
        print(f"\n--- marked rendering: {len(mids)}/{len(st0.entries)} entries flagged {MARK} ---")
        print("\n".join(l for l in mtxt.splitlines() if MARK in l)[:600])
        print("\nDry run OK. Nothing served, nothing written.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    exe = ROOT / "models" / "llamacpp" / "llama-server.exe"
    model = MODELS[args.model]
    server = LlamaServer(str(exe), str(model), ctx=args.ctx, port=args.port,
                         threads=args.threads, n_gpu_layers=args.ngl)
    server.ensure_running()
    print(f"served {model.name}", flush=True)
    try:
        for cname in args.conditions.split(","):
            cd = CONDITIONS[cname]
            out = (OUT_DIR /
                   f"{cname}_{args.model}_{args.views}_{args.start_pick}_{args.window}.json")
            if out.exists() and not args.redo:
                if json.loads(out.read_text(encoding="utf-8")).get("complete"):
                    print(f"[skip] {out.name} complete", flush=True)
                    continue
            rec = {"_meta": {"probe": True, "gate_legal": False, "probe_id": "retention",
                             "condition": cname, **cd, "model": args.model,
                             "views_arm": args.views, "compressor": vmeta.get("compressor_name"),
                             "seeds": seeds, "n_passes": len(todo), "temp": TEMP,
                             "op_cap": OP_CAP, "start_state": start_meta,
                             "noclobber_text": NOCLOBBER if cd["noclobber"] else None,
                             "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                   "draws": [], "complete": False}
            print(f"\n=== {cname} (guard={cd['guard']}, noclobber={cd['noclobber']}, "
                  f"nobudget={cd['nobudget']}) ===", flush=True)
            t0 = time.time()
            for seed in seeds:
                st = state_from_lines(lines)
                assert pat.search(st.render()), "start state lost the binding"
                trace, nlost, nblocked_detail, ops_ct = [], 0, 0, Counter()
                nmark_blocked, nselfmarks = 0, 0
                for v in todo:
                    stage = pyramid_stage(v["level"], n_levels, fracs)
                    sysp = build_system(cfg, stage, cd["noclobber"], cd["nobudget"],
                                        cd.get("marks"))
                    pre = {e["id"]: e["text"] for e in st.entries}
                    st.guard = cd["guard"]
                    # `shown` marks are a RENDERING of the state, not part of any entry's text, so
                    # the model sees importance without having to have written it.
                    if cd.get("marks") == "shown":
                        state_text, marked_ids = render_marked(st)
                    else:
                        state_text, marked_ids = st.render(), set()
                    resp = server.chat(sysp, _user_prompt(v["k"], len(views), state_text,
                                                          v["view_text"]),
                                       max_tokens=MAX_TOKENS, temperature=TEMP, seed=seed)
                    res = parse_ops(resp["text"], st.ids(), st.next_id)
                    ops = res.ops[:OP_CAP]
                    if cd.get("enforce_marks"):
                        keep = [o for o in ops
                                if not (o["op"] in ("REPLACE", "REMOVE")
                                        and o.get("id") in marked_ids)]
                        nmark_blocked += len(ops) - len(keep)
                        ops = keep
                    st.apply(ops)
                    nselfmarks += sum(1 for e in st.entries if (e["text"] or "").startswith(MARK))
                    ops_ct.update(o["op"] for o in res.ops)
                    for o in res.ops:
                        if o["op"] == "REPLACE" and o.get("id") in pre:
                            if _lost_literals(pre[o["id"]], o.get("text") or ""):
                                nlost += 1
                    nblocked_detail += sum(1 for b in st.last_report["blocked"]
                                           if b["reason"] == "blocked_detail_loss")
                    trace.append({"k": v["k"], "level": v["level"], "held": bool(pat.search(st.render())),
                                  "state_tokens": n_tokens(st.render())})
                held = bool(pat.search(st.render()))
                lost_at = next((t["k"] for t in trace if not t["held"]), None)
                rec["draws"].append({"seed": seed, "held_to_end": held, "lost_at_pass": lost_at,
                                     "trace": trace, "n_replace_detail_loss_emitted": nlost,
                                     "n_blocked_detail_loss": nblocked_detail,
                                     "n_ops_blocked_by_mark": nmark_blocked,
                                     "n_selfmarked_entries": nselfmarks,
                                     "op_types": dict(ops_ct), "final_state": st.render()})
                print(f"  seed {seed}: held={held} lost_at={lost_at} "
                      f"detail-loss REPLACEs emitted={nlost} blocked={nblocked_detail} "
                      f"mark-blocked={nmark_blocked} selfmarks={nselfmarks} "
                      f"ops={dict(ops_ct)}", flush=True)
                out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
            rec["complete"] = True
            rec["wall_s"] = round(time.time() - t0, 1)
            out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
            n = len(rec["draws"])
            print(f"  -> HELD {sum(d['held_to_end'] for d in rec['draws'])}/{n} "
                  f"[{rec['wall_s']}s]", flush=True)
    finally:
        server.stop()
        time.sleep(3)
    summarize()


def summarize() -> None:
    print(f"\n{'condition':<12} {'guard':<7} {'n':>3} {'HELD':>6} {'lost at (passes)':<22} "
          f"{'detail-loss REPLACEs':>21} {'blocked':>8}")
    for f in sorted(OUT_DIR.glob("*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        d = r["draws"]
        if not d:
            continue
        m = r["_meta"]
        held = sum(x["held_to_end"] for x in d)
        lost = [x["lost_at_pass"] for x in d if x["lost_at_pass"]]
        emit = sum(x["n_replace_detail_loss_emitted"] for x in d)
        blk = sum(x["n_blocked_detail_loss"] for x in d)
        print(f"{m['condition']:<12} {m['guard']:<7} {len(d):>3} {held:>4}/{len(d)} "
              f"{str(sorted(lost))[:22]:<22} {emit:>21} {blk:>8}")
    print("\nHELD = the queried binding was still in the state after all passes. Probe numbers, "
          "gate_legal=false; hand-read before any claim.")


if __name__ == "__main__":
    main()
