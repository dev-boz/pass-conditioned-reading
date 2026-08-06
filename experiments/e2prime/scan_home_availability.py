"""Non-oracle home-availability scan — the archive version of P1b ($0, no GPU).

P1b measured recording against HAND-WRITTEN homes (declared oracle): with a semantically matching
entry in state the student records the adder 8-9/10 and the relation 4/10; with none, ~0. That
left the question the lever board actually needs answered:

    did the student's OWN scaffold ever build a matching home for a later tile,
    and does its recording rate track home availability?

This scans every archived chain draw (student + floor, 11 seeds each = 22 draws x 31 passes) and
measures three things, all mechanically, no model calls:

  1. TARGET-FACT LIFECYCLE — per draw, the pass at which each of the four chain-relevant tokens
     (adder value, adder name, fn name, 23->988 mapping) enters the state and whether it survives
     to the final state. Answers "who created the home, and did it hold?"
  2. MODULE-HOME AVAILABILITY — the frozen views are module-structured, so for every
     (pass, module-in-view) pair we can ask whether the state ALREADY held an entry mentioning
     that module (home_before) and whether one mentions it afterwards (present_after). The
     conditional rate P(present_after | home_before) vs P(present_after | no home) is the
     non-oracle form of the P1b contrast.
  3. OP DISPOSITION — every applied REPLACE is classified against the pre-state text of its
     target: did it land in an entry about a module the current view is showing (fill-a-home),
     or in an unrelated entry (the grind-what-exists bias P1a saw on padding)?

Probe/diagnostic, `gate_legal:false`. Nothing here is pooled with a gate; it re-reads committed
artifacts only.

    python experiments/e2prime/scan_home_availability.py
    python experiments/e2prime/scan_home_availability.py --json runs/.../scan.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P7 = ROOT / "experiments" / "p7_split_unit"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(P7))
sys.path.insert(0, str(HERE))

from verify_fixture import load_turns                                     # noqa: E402
from stagea_chain_gate import load_config, preflight, build_passes        # noqa: E402

RUNS = ROOT / "runs" / "stageA_chain_gate"
MODULE_RE = re.compile(r"^# ===== module: (\S+) =====$", re.M)
STATE_RE = re.compile(r"STATE:\n(.*?)\n\nVIEW \(pass ", re.S)
ENTRY_RE = re.compile(r"^(S\d+[a-z]?):\s(.*)$")

# The four chain-relevant tokens. `relation` is deliberately absent: it is a joint over two
# operands and gets its audited matcher in analyze_chain_gate._relation_flags(); string presence
# would over-count (the 07-28 S83 near-miss). Tracked here = what a home would have to HOLD.
TARGETS = {
    "adder_value": lambda s: "1365" in s,
    "adder_name": lambda s: "RECONCILIATION_ADDER_CENTS" in s,
    "fn_name": lambda s: "compute_line_surcharge" in s,
    "mapping_23_988": lambda s: bool(re.search(r"23\D{0,4}988", s)),
}

# Modules that carry the chain's facts, and the pass whose view first shows each.
TARGET_MODULES = {"fulfillment/line_quote.py", "pricing/region_tables.py"}


def module_key(path: str) -> str:
    """'fulfillment/line_quote.py' -> 'line_quote' — the distinctive stem a state entry would
    name. Views name modules by full path; states paraphrase, so match on the stem too."""
    return Path(path).stem


def parse_state_lines(text: str) -> list[tuple[str, str]]:
    out = []
    for ln in (text or "").splitlines():
        m = ENTRY_RE.match(ln.strip())
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def pre_state_from_user(user: str) -> list[tuple[str, str]]:
    """The state as the model was SHOWN it (authoritative), not re-derived from the prior pass."""
    m = STATE_RE.search(user or "")
    return parse_state_lines(m.group(1)) if m else []


def mentions(entries: list[tuple[str, str]], path: str) -> bool:
    key, low = module_key(path), path.lower()
    return any(low in t.lower() or key in t.lower() for _, t in entries)


def load_views() -> dict[int, dict]:
    cfg = load_config()
    spec = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    scaffold = json.loads((P7 / "scaffold_struct.json").read_text(encoding="utf-8"))
    turns = load_turns(P7 / "fixture" / "host_doc.jsonl")
    _, sch, _, _ = preflight(spec, turns, scaffold, cfg)
    views = {}
    for p in build_passes(sch, scaffold):
        views[p["k"]] = {"phase": p["phase"], "modules": MODULE_RE.findall(p["view_text"]),
                         "text": p["view_text"]}
    return views


def scan_draw(rec: dict, views: dict[int, dict]) -> dict:
    """One archived draw -> lifecycle, per-(pass, module) home rows, op dispositions."""
    life = {name: {"first_pass": None, "final": False} for name in TARGETS}
    rows, ops_by_phase, off_topic = [], defaultdict(Counter), []

    for p in rec["passes"]:
        k, phase = p["k"], p["phase"]
        pre = pre_state_from_user(p.get("user", ""))
        post = parse_state_lines(p.get("state_text", ""))
        post_text = p.get("state_text", "") or ""
        view = views.get(k, {"modules": []})

        for name, test in TARGETS.items():
            if life[name]["first_pass"] is None and test(post_text):
                life[name]["first_pass"] = k

        # (2) home availability, per module the view is showing this pass
        for mod in view["modules"]:
            rows.append({"k": k, "phase": phase, "module": mod,
                         "target_module": mod in TARGET_MODULES,
                         "home_before": mentions(pre, mod),
                         "present_after": mentions(post, mod)})

        # (3) op disposition — did applied REPLACEs land in an entry about a view module?
        blocked = {b.get("id") for b in p.get("apply_report", {}).get("blocked", [])
                   if isinstance(b, dict)}
        pre_by_id = dict(pre)
        for op in p.get("ops", []):
            kind = op.get("op")
            if kind != "REPLACE":
                ops_by_phase[phase][kind or "?"] += 1
                continue
            oid = op.get("id")
            if oid in blocked:
                ops_by_phase[phase]["REPLACE_blocked"] += 1
                continue
            tgt = pre_by_id.get(oid, "")
            new = op.get("text", "") or ""
            on_topic = any(module_key(m) in tgt.lower() or m.lower() in tgt.lower()
                           for m in view["modules"])
            new_on_topic = any(module_key(m) in new.lower() or m.lower() in new.lower()
                               for m in view["modules"])
            ops_by_phase[phase]["REPLACE_into_home" if on_topic
                                else "REPLACE_off_topic"] += 1
            # Two dispositions the hand-read surfaced, now counted rather than sampled:
            #   no-op   — the rewrite is byte-identical to what was already there (pure waste)
            #   clobber — an entry about a module the view is NOT showing is overwritten with
            #             content about one it IS: a new fact housed by destroying an old one.
            if new.strip() == tgt.strip():
                ops_by_phase[phase]["_of_which_noop"] += 1
            elif not on_topic and new_on_topic:
                ops_by_phase[phase]["_of_which_clobber"] += 1
            if not on_topic:
                off_topic.append({"k": k, "phase": phase, "id": oid, "target_pre": tgt,
                                  "new_text": new, "noop": new.strip() == tgt.strip(),
                                  "clobber": new_on_topic})

    final_text = rec.get("final_state", "") or ""
    for name, test in TARGETS.items():
        life[name]["final"] = bool(test(final_text))
    return {"lifecycle": life, "rows": rows, "off_topic": off_topic,
            "ops_by_phase": {ph: dict(c) for ph, c in ops_by_phase.items()}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None, help="write the full scan record here")
    ap.add_argument("--hand-read", type=int, default=0, metavar="N",
                    help="print N sampled Phase-B off-topic REPLACEs for reading")
    args = ap.parse_args()

    views = load_views()
    files = sorted(RUNS.glob("student_s*.json")) + sorted(RUNS.glob("floor_s*.json"))
    files = [f for f in files if not f.name.startswith("smoke_")]
    if not files:
        raise SystemExit(f"no archived draws under {RUNS}")

    scans, meta = {}, {}
    for f in files:
        rec = json.loads(f.read_text(encoding="utf-8"))
        arm = rec["_meta"]["arm"]
        scans[f.stem] = scan_draw(rec, views)
        meta[f.stem] = {"arm": arm, "seed": rec["_meta"]["seed"],
                        "n_passes": len(rec["passes"])}

    print(f"Non-oracle home-availability scan — {len(files)} archived draws, "
          f"{sum(m['n_passes'] for m in meta.values())} passes. Probe, gate_legal=false.\n")

    # ---- (1) target-fact lifecycle
    print("=" * 78)
    print("(1) TARGET-FACT LIFECYCLE — pass of first appearance / survives to final state")
    print("=" * 78)
    print(f"{'draw':<20} {'adder 1365':>12} {'ADDER name':>12} {'fn name':>12} {'23->988':>12}")
    for name, sc in scans.items():
        cells = []
        for t in ("adder_value", "adder_name", "fn_name", "mapping_23_988"):
            L = sc["lifecycle"][t]
            fp = L["first_pass"]
            cells.append("-" if fp is None else f"k{fp}{'' if L['final'] else ' LOST'}")
        print(f"{name:<20} " + "".join(f"{c:>12} " for c in cells))

    for arm in ("student", "floor"):
        sel = [s for n, s in scans.items() if meta[n]["arm"] == arm]
        if not sel:
            continue
        print(f"\n  {arm} (n={len(sel)}):")
        for t in ("adder_value", "adder_name", "fn_name", "mapping_23_988"):
            ever = sum(1 for s in sel if s["lifecycle"][t]["first_pass"] is not None)
            final = sum(1 for s in sel if s["lifecycle"][t]["final"])
            byA = sum(1 for s in sel
                      if (s["lifecycle"][t]["first_pass"] or 99) <= 6)
            print(f"    {t:<16} ever recorded {ever}/{len(sel)} | in final state "
                  f"{final}/{len(sel)} | first seen in Phase A (k<=6) {byA}/{len(sel)}")

    # ---- (2) module-home availability
    print("\n" + "=" * 78)
    print("(2) MODULE-HOME AVAILABILITY — P(entry mentions module after the pass | home before)")
    print("=" * 78)
    for arm in ("student", "floor"):
        rows = [r for n, s in scans.items() if meta[n]["arm"] == arm for r in s["rows"]]
        if not rows:
            continue
        print(f"\n  {arm}: {len(rows)} (pass, module) pairs")
        scopes = [("all modules", rows),
                  ("all modules, Phase B", [r for r in rows if r["phase"] == "B"]),
                  ("TARGET modules only", [r for r in rows if r["target_module"]])]
        for scope, sel in scopes:
            if not sel:
                continue
            hb = [r for r in sel if r["home_before"]]
            nb = [r for r in sel if not r["home_before"]]
            ph = sum(r["present_after"] for r in hb)
            pn = sum(r["present_after"] for r in nb)
            rate_h = f"{ph}/{len(hb)} = {ph / len(hb):.2f}" if hb else f"0/0 = -"
            rate_n = f"{pn}/{len(nb)} = {pn / len(nb):.2f}" if nb else f"0/0 = -"
            print(f"    {scope:<22} home_before {len(hb):>5}/{len(sel):<5}")
            print(f"    {'':<22}   present_after | home    : {rate_h}")
            print(f"    {'':<22}   present_after | NO home : {rate_n}")

    # ---- (3) op disposition
    print("\n" + "=" * 78)
    print("(3) OP DISPOSITION — where applied REPLACEs landed, by phase")
    print("=" * 78)
    for arm in ("student", "floor"):
        agg = Counter()
        for n, s in scans.items():
            if meta[n]["arm"] != arm:
                continue
            for ph, c in s["ops_by_phase"].items():
                for kind, v in c.items():
                    agg[f"{ph}:{kind}"] += v
        if not agg:
            continue
        print(f"\n  {arm}:")
        for phase in ("A", "B"):
            items = {k.split(":", 1)[1]: v for k, v in agg.items() if k.startswith(f"{phase}:")}
            subs = {k: items.pop(k, 0) for k in ("_of_which_noop", "_of_which_clobber")}
            tot = sum(items.values())
            if not tot:
                continue
            parts = ", ".join(f"{k}={v} ({v / tot:.0%})"
                              for k, v in sorted(items.items(), key=lambda x: -x[1]))
            print(f"    Phase {phase} ({tot} applied ops): {parts}")
            nrep = items.get("REPLACE_off_topic", 0) + items.get("REPLACE_into_home", 0)
            if nrep:
                print(f"      of the {nrep} REPLACEs: "
                      f"no-op (rewrote identical text) {subs['_of_which_noop']} "
                      f"({subs['_of_which_noop'] / nrep:.0%}), "
                      f"clobber (housed view content by overwriting an unrelated entry) "
                      f"{subs['_of_which_clobber']} ({subs['_of_which_clobber'] / nrep:.0%})")

    # ---- (5) the Phase-A capture contrast. Both operands are visible in Phase A: the full
    # REGION_SURCHARGE_CENTS table (23: 988 is one row of 24) at pass 2, and the standalone
    # RECONCILIATION_ADDER_CENTS = 1365 at pass 4. Same model, same scaffold rubric, two passes
    # apart, both at low state pressure — so this isolates extraction GRANULARITY from every
    # other candidate (phase, pressure, home availability, scale).
    print("\n" + "=" * 78)
    print("(5) PHASE-A CAPTURE — standalone scalar (k=4) vs one row of a 24-row table (k=2)")
    print("=" * 78)
    print(f"  {'draw':<18} | k2: table named / 988 present / 23->988 BOUND | k4: name / 1365")
    tally = Counter()
    for name in [n for n in scans if meta[n]["arm"] == "student"]:
        rec = json.loads((RUNS / f"{name}.json").read_text(encoding="utf-8"))
        st2 = next((p["state_text"] for p in rec["passes"] if p["k"] == 2), "")
        st4 = next((p["state_text"] for p in rec["passes"] if p["k"] == 4), "")
        v = {"tbl": "REGION_SURCHARGE_CENTS" in st2, "digits": "988" in st2,
             "bound": bool(re.search(r"23\D{0,4}988", st2)),
             "aname": "RECONCILIATION_ADDER_CENTS" in st4, "aval": "1365" in st4}
        for key, hit in v.items():
            tally[key] += hit
        tally["n"] += 1
        print(f"  {name:<18} |    {str(v['tbl']):<5}     {str(v['digits']):<5}     "
              f"{str(v['bound']):<12} |  {str(v['aname']):<5}  {v['aval']}")
    n = tally["n"]
    print(f"  {'TOTAL':<18} |    {tally['tbl']}/{n}      {tally['digits']}/{n}      "
          f"{tally['bound']}/{n}          |  {tally['aname']}/{n}    {tally['aval']}/{n}")
    print(f"\n  The digits 988 reach the state {tally['digits']}/{n} times but the 23->988 "
          f"BINDING only {tally['bound']}/{n}:\n  the table is summarized to its range "
          f"(\"24 surcharge rates (10-988 cents)\") and the key->value\n  pair is destroyed. "
          f"The standalone scalar survives {tally['aval']}/{n}.")

    # ---- (4) hand-read: what IS an "off-topic" REPLACE? The classifier keys on module names,
    # so an entry that holds the right content without naming its module (e.g. "Fixed
    # reconciliation adder ...") is scored off-topic. Read before believing the rate.
    if args.hand_read:
        print("\n" + "=" * 78)
        print(f"(4) HAND-READ — {args.hand_read} Phase-B off-topic REPLACEs, evenly sampled")
        print("=" * 78)
        pool = [(n, o) for n, s in scans.items() if meta[n]["arm"] == "student"
                for o in s["off_topic"] if o["phase"] == "B"]
        step = max(1, len(pool) // args.hand_read)
        for n, o in pool[::step][:args.hand_read]:
            print(f"\n  [{n} k={o['k']} {o['id']}] view modules this pass: "
                  f"{', '.join(module_key(m) for m in views[o['k']]['modules'][:6])} ...")
            print(f"    TARGET ENTRY (before): {o['target_pre'][:200]}")
            print(f"    REPLACED WITH        : {o['new_text'][:200]}")

    if args.json:
        out = Path(args.json)
        if not out.is_absolute():
            out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"_meta": {"probe": True, "gate_legal": False,
                                             "draws": meta}, "scans": scans},
                                  indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"\n-> {out}")

    print("\nProbe numbers. Hand-read the draws before believing any rate.")


if __name__ == "__main__":
    main()
