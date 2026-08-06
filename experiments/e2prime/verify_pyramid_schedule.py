"""Validate the tiling-pyramid schedule, per compressor arm, before any gate is run on it ($0).

The 2026-07-30 discrepancy (docs/SCHEDULE-DISCREPANCY-2026-07-30.md) replaced the two-level D25
schedule with `build_pyramid_schedule`. This asserts the properties the README's design requires,
and — because the compressor is architecture, not preprocessing — it does so PER ARM: which
compressor ran decides what each level can carry, and therefore what the chain gate can measure.

    G1  strict doubling: level tile counts are 1, 2, 4, 8, ...
    G2  every level TILES the document: complete coverage, no overlap, no gaps
    G3  compression falls monotonically and the final level is verbatim (ratio 1.0)
    G4  k indexes resolution: compression is a function of level, not of position within a level
    C1  EARLY EXPOSURE (replaces the old frozen-scaffold assert): at which level does each operand
        first survive compression? The old C1 asserted the hand-built scaffold carried the operands
        into Phase A. On the pyramid that is not an assumption to assert but a property to MEASURE,
        and it differs per arm.
    G5  SPLIT-FACT GUARD — may any single view hold both operands? If one does, the chain is
        answerable from a single pass and the fixture stops being a cross-pass compose test.

RUN CLASS (maintainer's rule, 2026-07-30): every arm is stamped, never suppressed.

    faithful  — the split holds AND the views were authored blind to the probe. A chain result on
                this arm is a genuine test of composing across passes.
    assisted  — one or both fails. Still run, still reported, but scored separately: with the split
                broken the arm measures RETENTION (does what pass 1 gave it survive to the close?),
                which is a real question, just not the compose question.

    python experiments/e2prime/verify_pyramid_schedule.py --all            # the comparison table
    python experiments/e2prime/verify_pyramid_schedule.py --views graded   # one arm, full detail
    python experiments/e2prime/verify_pyramid_schedule.py                  # live extractive (no cache)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P7 = ROOT / "experiments" / "p7_split_unit"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(P7))
sys.path.insert(0, str(HERE))

from pca.planted import build_pyramid_schedule, build_schedule, pyramid_levels   # noqa: E402
from verify_fixture import load_turns                                            # noqa: E402
from stagea_chain_gate import load_config                                        # noqa: E402
from gen_pyramid_views import ARM_SPEC, OUT_DIR                                  # noqa: E402

REPORT_DIR = HERE / "pyramid_views"


# --------------------------------------------------------------------------- loading
def load_arm(arm: str, V: int, branching: int, turns: list[dict]) -> tuple[list[dict], dict]:
    """A frozen arm's views as a schedule-shaped list, or a live extractive build if arm is None."""
    if arm is None:
        sch = build_pyramid_schedule(turns, V, branching)
        for p in sch:
            p.setdefault("tile", 0)
        return sch, {"arm": "(live extractive)", "probe_blind": True,
                     "compressor_name": "extractive-sumbasic-v1"}
    path = OUT_DIR / f"{arm}.json"
    if not path.exists():
        raise SystemExit(f"no frozen views for arm '{arm}': {path}\n"
                         f"generate with: python experiments/e2prime/gen_pyramid_views.py "
                         f"--arm {arm}")
    rec = json.loads(path.read_text(encoding="utf-8"))
    sch = []
    for p in rec["passes"]:
        sch.append({**p, "turn_idx": set(range(p["idx_lo"], p["idx_hi"] + 1)),
                    "phase": "B" if p["verbatim"] else "A"})
    sch.sort(key=lambda p: (p["level"], p["tile"]))
    for i, p in enumerate(sch):
        p["k"], p["K"] = i + 1, len(sch)
    meta = dict(rec["_meta"])
    meta.setdefault("probe_blind", ARM_SPEC.get(arm, {}).get("probe_blind", True))
    if not rec.get("complete"):
        print(f"  !! WARNING: arm '{arm}' is marked incomplete ({len(sch)} views)")
    return sch, meta


def operand_markers(spec: dict) -> dict:
    qcode, tval = spec["queried_code"], spec["table_value_for_queried"]
    return {
        # fragment 1 — the queried key->value binding, and the table LITERAL it lives in.
        # The declaration marker keeps the original "= {" form on purpose: a bare mention of the
        # table's NAME is not its contents. `compute_line_surcharge` reads REGION_SURCHARGE_CENTS,
        # so every verbatim view of the function mentions the name while carrying none of the rows
        # — matching on the name alone marks that tile as holding both fragments and silently
        # destroys the split-fact guard.
        "entry": f"{qcode}: {tval}",
        "entry_compact": f"{qcode}:{tval}",
        "table_decl": "REGION_SURCHARGE_CENTS = {",
        "table_name": "REGION_SURCHARGE_CENTS",
        # fragment 2 — the adder and the routine that combines them
        "adder_decl": f"RECONCILIATION_ADDER_CENTS = {spec['reconciliation_adder_cents']}",
        "adder_name": "RECONCILIATION_ADDER_CENTS",
        "fn": "compute_line_surcharge",
    }


def view_tags(v: str, M: dict) -> dict:
    """Which fragments a single view actually carries. `entry` is the BINDING (23 bound to 988),
    which is the thing the chain needs — the archived pathology is a table surviving as its range,
    where the digits appear but the binding does not. `table_name`/`adder_name` are the weaker
    STRUCTURAL exposure: the view says such a thing exists without saying what it equals."""
    return {
        "entry": (M["entry"] in v) or (M["entry_compact"] in v),
        "table_decl": M["table_decl"] in v,
        "table_name": M["table_name"] in v,
        "adder_value": M["adder_decl"] in v or (M["adder_name"] in v and "1365" in v),
        "adder_name": M["adder_name"] in v,
        "fn": M["fn"] in v,
    }


def classify(sch: list[dict], meta: dict, spec: dict) -> dict:
    """G5 + C1 + the faithful/assisted stamp."""
    M = operand_markers(spec)
    per_view, both = [], []
    first = {"entry": None, "table_decl": None, "table_name": None,
             "adder_value": None, "adder_name": None, "fn": None}
    for p in sch:
        t = view_tags(p["view_text"], M)
        f1 = t["entry"] or t["table_decl"]
        f2 = t["adder_value"] or t["fn"]
        if f1 and f2:
            both.append(p)
        if any(t.values()):
            per_view.append((p, t))
        for key in first:
            if t.get(key) and first[key] is None:
                first[key] = p["level"]
    probe_blind = bool(meta.get("probe_blind", True))
    split_intact = not both
    reasons = []
    if not split_intact:
        reasons.append(f"single_pass_answerable (k={[p['k'] for p in both][:6]}, "
                       f"level {sorted({p['level'] for p in both})})")
    if not probe_blind:
        reasons.append("probe_aware_authoring")
    return {"run_class": "faithful" if (split_intact and probe_blind) else "assisted",
            "reasons": reasons, "split_intact": split_intact, "probe_blind": probe_blind,
            "both_operand_views": [{"k": p["k"], "level": p["level"]} for p in both],
            "first_level": first, "per_view": per_view}


# --------------------------------------------------------------------------- checks
def run_checks(sch: list[dict], meta: dict, spec: dict, turns: list[dict], levels: list[int],
               branching: int, verbose: bool) -> dict:
    fails, notes = [], []
    N = sum(t["tokens"] for t in turns)
    lv_list = sorted({p["level"] for p in sch})

    # G1 strict doubling
    want = [branching ** i for i in range(len(levels))]
    g1 = levels == want[:len(levels)]
    if not g1:
        fails.append(f"G1: levels {levels} != {want[:len(levels)]}")

    # G2 per-level coverage
    all_idx = set(range(len(turns)))
    g2 = True
    for lv in lv_list:
        ps = [p for p in sch if p["level"] == lv]
        union, overlap = set(), 0
        for p in ps:
            overlap += len(union & p["turn_idx"])
            union |= p["turn_idx"]
        want_tiles = min(levels[lv - 1], len(turns))
        if not (union == all_idx and overlap == 0 and len(ps) == want_tiles):
            g2 = False
            fails.append(f"G2: level {lv} tiles {len(ps)}!={want_tiles}, "
                         f"coverage {len(union)}/{len(turns)}, overlap {overlap}")

    # G3 monotone compression, verbatim floor
    ratios, rows = [], []
    for lv in lv_list:
        ps = [p for p in sch if p["level"] == lv]
        sl = sum(p["slice_tokens"] for p in ps) / len(ps)
        vw = sum(p["view_tokens"] for p in ps) / len(ps)
        r = sl / max(vw, 1)
        ratios.append(r)
        rows.append((lv, len(ps), sl, vw, r))
    mono = all(ratios[i] >= ratios[i + 1] - 1e-9 for i in range(len(ratios) - 1))
    verb = abs(ratios[-1] - 1.0) < 0.05
    if not mono:
        fails.append("G3: compression not monotone across levels")
    if not verb:
        fails.append(f"G3: final level ratio {ratios[-1]:.2f} != 1.0")

    # G4 resolution is a property of the level, not of position within it
    worst, spreads = 0.0, []
    for lv in lv_list:
        ps = [p for p in sch if p["level"] == lv]
        rs = [p["slice_tokens"] / max(p["view_tokens"], 1) for p in ps]
        spread = (max(rs) - min(rs)) / max(sum(rs) / len(rs), 1e-9)
        worst = max(worst, spread)
        spreads.append((lv, min(rs), max(rs)))
    g4 = worst < 0.75
    if not g4:
        notes.append(f"G4: within-level ratio spread {worst:.0%} — levels overlap in resolution, "
                     f"so k indexes resolution only loosely")

    # budget discipline — does the compressor actually SPEND its budget?
    comp = [p for p in sch if not p.get("verbatim", p["compression_ratio"] > 1.05)]
    fill = (sum(p["view_tokens"] for p in comp) / (len(comp) * meta.get("V", 3000))
            if comp else 1.0)

    cls = classify(sch, meta, spec)
    tot = sum(p["view_tokens"] for p in sch)

    if verbose:
        print(f"(G1) tile counts per level {levels} — strict doubling: {'PASS' if g1 else 'FAIL'}")
        print(f"(G2) per-level coverage: {'PASS' if g2 else 'FAIL'}")
        print(f"\n(G3) resolution ladder")
        print(f"     {'level':>5} {'tiles':>6} {'slice tok':>10} {'view tok':>9} {'compression':>12}")
        for lv, n, sl, vw, r in rows:
            print(f"     {lv:>5} {n:>6} {sl:>10,.0f} {vw:>9,.0f} {r:>11.1f}x")
        print(f"     monotone decreasing: {'PASS' if mono else 'FAIL'} | "
              f"final level verbatim: {'PASS' if verb else 'FAIL'}")
        print(f"\n(G4) within-level compression spread")
        for lv, lo, hi in spreads:
            print(f"     level {lv}: ratio {lo:.1f}..{hi:.1f}")
        print(f"     worst relative spread {worst:.0%} — {'PASS' if g4 else 'REVIEW'}")
        print(f"\n(BUDGET) compressed views fill {fill:.0%} of the {meta.get('V', 3000)}-tok budget "
              f"on average" + ("" if fill > 0.8 else "  <- under-spending: the ladder is coarser "
                               "than the schedule asks for"))
        print(f"\n(C1) EARLY EXPOSURE — first level at which each fragment survives:")
        for key, label in (("entry", "23->988 BINDING"), ("table_decl", "table literal"),
                           ("table_name", "table exists (name)"), ("adder_value", "adder value"),
                           ("adder_name", "adder exists (name)"), ("fn", "the fn")):
            lv = cls["first_level"].get(key)
            print(f"     {label:<21} {('level ' + str(lv)) if lv else 'never'}")
        print(f"\n(G5) SPLIT-FACT GUARD — may any single view hold both operands?")
        for p, t in cls["per_view"][:24]:
            tags = ",".join(k for k, v in t.items() if v)
            print(f"     k={p['k']:>3} (level {p['level']}, {p['compression_ratio']:>5.1f}x): {tags}")
        if len(cls["per_view"]) > 24:
            print(f"     ... and {len(cls['per_view']) - 24} more")
        print("     " + ("PASS — no single view holds both operands." if cls["split_intact"]
                         else f"FAIL — {len(cls['both_operand_views'])} view(s) hold BOTH: "
                              f"k={[b['k'] for b in cls['both_operand_views']][:8]}"))
        print(f"\ncost: {len(sch)} passes, {tot:,} view tok = {tot / N:.2f}x source")

    return {"arm": meta.get("arm"), "compressor": meta.get("compressor_name"),
            "n_passes": len(sch), "levels": levels, "ratios": [round(r, 1) for r in ratios],
            "G1": g1, "G2": g2, "G3_monotone": mono, "G3_verbatim_floor": verb, "G4": g4,
            "within_level_spread": round(worst, 3), "budget_fill": round(fill, 3),
            "view_tokens": tot, "cost_vs_source": round(tot / N, 2),
            "first_level": cls["first_level"], "split_intact": cls["split_intact"],
            "probe_blind": cls["probe_blind"], "run_class": cls["run_class"],
            "reasons": cls["reasons"],
            "both_operand_views": cls["both_operand_views"],
            "hard_failures": fails, "notes": notes}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--V", type=int, default=None, help="per-view budget (default: config)")
    ap.add_argument("--branching", type=int, default=2)
    ap.add_argument("--views", default=None, help=f"frozen arm: {', '.join(sorted(ARM_SPEC))}")
    ap.add_argument("--all", action="store_true", help="compare every generated arm")
    ap.add_argument("--json-out", default=None, help="write the report(s) to this path")
    args = ap.parse_args()

    cfg = load_config()
    V = args.V or cfg["schedule"]["code"]["V"]
    spec = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    turns = load_turns(P7 / "fixture" / "host_doc.jsonl")
    N = sum(t["tokens"] for t in turns)
    levels = pyramid_levels(turns, V, args.branching)

    arms = ([a for a in ARM_SPEC if (OUT_DIR / f"{a}.json").exists()] if args.all
            else [args.views])
    if args.all and not arms:
        raise SystemExit("no frozen arms found — run gen_pyramid_views.py first")

    reports = []
    for arm in arms:
        sch, meta = load_arm(arm, V, args.branching, turns)
        meta["V"] = V
        if not args.all:
            print(f"Pyramid schedule — arm={arm or '(live extractive)'} "
                  f"compressor={meta.get('compressor_name')}\n"
                  f"V={V}, branching={args.branching}, doc {N:,} tok, {len(turns)} turns\n"
                  f"{len(sch)} passes across {len(levels)} levels\n")
        rep = run_checks(sch, meta, spec, turns, levels, args.branching, verbose=not args.all)
        reports.append(rep)

    if args.all:
        print(f"Pyramid arms — V={V}, doc {N:,} tok, levels {levels}\n")
        print(f"{'arm':<15} {'class':<9} {'ladder (compression by level)':<38} {'fill':>5} "
              f"{'cost':>6} {'binding@':>9} {'adder@':>7}")
        for r in reports:
            lad = " ".join(f"{x:g}" for x in r["ratios"])
            fl = r["first_level"]
            print(f"{r['arm']:<15} {r['run_class']:<9} {lad:<38} {r['budget_fill']:>4.0%} "
                  f"{r['cost_vs_source']:>5.2f}x "
                  f"{('L' + str(fl['entry'])) if fl['entry'] else '--':>9} "
                  f"{('L' + str(fl['adder_value'])) if fl['adder_value'] else '--':>7}")
        print(f"\n{'arm':<15} {'G1':>4} {'G2':>4} {'G3mono':>7} {'G3verb':>7} {'G4':>4} "
              f"{'split':>7}  reasons / failures")
        for r in reports:
            def m(b):
                return "ok" if b else "FAIL"
            print(f"{r['arm']:<15} {m(r['G1']):>4} {m(r['G2']):>4} {m(r['G3_monotone']):>7} "
                  f"{m(r['G3_verbatim_floor']):>7} {m(r['G4']):>4} "
                  f"{('intact' if r['split_intact'] else 'BROKEN'):>7}  "
                  f"{'; '.join(r['reasons'] + r['hard_failures'])[:70]}")
        print("\nfaithful = split holds AND views authored probe-blind -> a genuine cross-pass "
              "compose test.\nassisted = otherwise; still run and reported, but it measures "
              "RETENTION, not composition.")
    else:
        r = reports[0]
        print(f"\nRUN CLASS: {r['run_class'].upper()}"
              + (f"  ({'; '.join(r['reasons'])})" if r["reasons"] else ""))
        print("\n" + ("ALL HARD CHECKS PASSED" if not r["hard_failures"] else
                      "FAILURES:\n  - " + "\n  - ".join(r["hard_failures"])))
        for n in r["notes"]:
            print(f"NOTE: {n}")

    out = Path(args.json_out) if args.json_out else REPORT_DIR / "_validation.json"
    out.write_text(json.dumps(reports, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nreport -> {out.relative_to(ROOT)}")
    sys.exit(1 if any(r["hard_failures"] for r in reports) and not args.all else 0)


if __name__ == "__main__":
    main()
