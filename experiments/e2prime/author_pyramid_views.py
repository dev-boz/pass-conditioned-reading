"""Hand-authored pyramid view sets — emulating the compressor in its FINAL form ($0, no model).

The maintainer's framing: in its final form the compressor is part of the architecture, specialised
for the role, and hand-edited compressions are an attempt to emulate that before such a compressor
exists. Two arms are authored, per the 2026-07-30 call to build both:

  hand_blind   ONE uniform rule, stated below BEFORE it is applied, applied to every module
               identically, with no special-casing by name or content. Probe-blind: a skeptic who
               has never seen the fixture must accept the rule (the COMPRESSOR-V2.md standard).
  hand_oracle  The same rule, PLUS placement chosen knowing the probe. DECLARED ORACLE: design
               input only, never poolable with any verdict. It exists to show the ceiling — what
               the architecture does when compression is as good as it could possibly be for this
               chain.

--------------------------------------------------------------------------------------------
THE RULE (hand_blind), stated in advance:

  R1  A module that declares nothing at module level — no constants, no classes — is structurally
      indistinguishable from every other such module at a brief's resolution. Collapse the entire
      SET of them into one pattern block naming the shared body template, the count, and the
      membership by directory. Justification, probe-blind: a brief that lists a hundred
      near-identical helper inventories one by one has spent its budget proving they are
      near-identical. Naming the pattern once carries the same information.
  R2  Spend the whole freed budget on the modules that DO declare something, at the mildest
      severity that fits (pca.compress_graded's ladder, same sigma semantics).
  R3  No module is ever treated specially by name, path, or content. R1's test is structural and
      mechanical.

  This is the one thing the deterministic graded compressor cannot do: it works module-by-module
  and has no cross-module view, so it cannot notice that a hundred modules are the same module.
  That is the specific defect hand-editing is here to repair.

--------------------------------------------------------------------------------------------
MEASURED CONSEQUENCE, recorded because it matters more than the arm does: this fixture has 106
modules, of which SIX declare anything. Their declarations total well under one view budget. So a
compressor good enough to apply R1 puts the document's entire distinctive content into the level-1
view — and the split-fact guard cannot survive that. It is not a flaw in the compressor. It is a
statement about the fixture: a document whose distinctive content fits in a single view cannot test
composition across passes, no matter what schedule is wrapped around it.

  python experiments/e2prime/author_pyramid_views.py --arm hand_blind
  python experiments/e2prime/author_pyramid_views.py --arm hand_oracle
  python experiments/e2prime/author_pyramid_views.py --budget-audit
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P7 = ROOT / "experiments" / "p7_split_unit"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(P7))
sys.path.insert(0, str(HERE))

from pca.compress_graded import (SIGMA_MAX, SIGMA_NAMES, parse_modules,        # noqa: E402
                                 render_module)
from pca.textutils import n_tokens                                             # noqa: E402
from verify_fixture import load_turns                                          # noqa: E402
from stagea_chain_gate import load_config                                      # noqa: E402
from gen_pyramid_views import ARM_SPEC, OUT_DIR, plan_passes                   # noqa: E402


def declares(m: dict) -> bool:
    """R1's structural test: does this module declare anything at module level?"""
    return bool(m["consts"] or m["classes"])


def pattern_block(pure: list[dict]) -> str:
    """R1: the whole set of declaration-free modules as ONE block. Content-neutral — it reports
    the shared shape and the membership, and inspects nothing about what any module is for."""
    if not pure:
        return ""
    by_dir: dict[str, list[str]] = {}
    n_fns = 0
    for m in pure:
        path = m["path"] or "(unknown)"
        by_dir.setdefault(path.split("/")[0], []).append(path.split("/")[-1])
        n_fns += len(m["helpers"])
    lines = [
        f"# ===== {len(pure)} declaration-free helper modules (one shared pattern) =====",
        f"# These modules define no module-level constants or classes. They contain "
        f"{n_fns} free functions in total, all following one body template:",
        "#   def <verb>_<noun>(container, *params):",
        "#       acc = []",
        "#       for i, x in enumerate(container or []):",
        "#           if i % <modulus> == 0 and x is not None: acc.append((x, i * <multiplier>))",
        "#           elif x and getattr(x, 'weight', 0) > <threshold>: acc.append((x, i))",
        "#       return [t for t in acc if t[1] >= 0]",
        "# They declare nothing any other unit reads. Membership by package:",
    ]
    for d in sorted(by_dir):
        names = sorted(by_dir[d])
        lines.append(f"#   {d}/: {len(names)} modules — {', '.join(names)}")
    return "\n".join(lines)


def author_view(slice_text: str, V: int, oracle_paths: tuple[str, ...] = ()) -> tuple[str, dict]:
    """Author one view under R1-R3 (+ oracle placement when oracle_paths is given)."""
    mods = [m for m in parse_modules(slice_text)
            if (m["header"] or m["consts"] or m["classes"] or m["helpers"] or m["raw"])]
    pure = [m for m in mods if not declares(m)]
    decl = [m for m in mods if declares(m)]

    block = pattern_block(pure)
    budget = V - n_tokens(block) - 8 if block else V

    # R2: mildest severity that fits, allocated largest-first (same size-driven, content-neutral
    # rule the graded compressor uses — hand-editing changes WHAT is compressed, not how the
    # budget is shared out).
    idx = list(range(len(decl)))
    cost = {i: {s: n_tokens("\n".join(render_module(decl[i], s)) + "\n")
                for s in range(0, SIGMA_MAX + 1)} for i in idx}
    # oracle placement: named modules are pinned to sigma 1 (declarations verbatim, bodies dropped)
    # and never pushed further. This is the probe-aware step and the ONLY thing separating
    # hand_oracle from hand_blind.
    pinned = {i for i in idx if oracle_paths and (decl[i]["path"] or "") in oracle_paths}
    sig = {i: 1 for i in idx}
    total = sum(cost[i][sig[i]] for i in idx)
    while total > budget:
        cand = [i for i in idx if sig[i] < SIGMA_MAX and i not in pinned]
        if not cand:
            break
        i = max(cand, key=lambda j: (cost[j][sig[j]], -j))
        total -= cost[i][sig[i]]
        sig[i] += 1
        total += cost[i][sig[i]]
    # spend anything left over by RESTORING detail (sigma 1 -> 0) on the smallest modules first,
    # so the budget is used rather than banked
    while True:
        cand = [i for i in idx if sig[i] > 0 and
                total - cost[i][sig[i]] + cost[i][sig[i] - 1] <= budget]
        if not cand:
            break
        i = min(cand, key=lambda j: (cost[j][sig[j] - 1], j))
        total += cost[i][sig[i] - 1] - cost[i][sig[i]]
        sig[i] -= 1

    parts = [block] if block else []
    for i in idx:
        parts.append("\n".join(render_module(decl[i], sig[i])))
    view = "\n".join(p for p in parts if p).strip()
    report = {"n_modules": len(mods), "n_pure_collapsed": len(pure), "n_declaring": len(decl),
              "pattern_block_tokens": n_tokens(block) if block else 0,
              "declaring_sigma": {(decl[i]["path"] or f"mod{i}"): sig[i] for i in idx},
              "sigma_names": {str(s): SIGMA_NAMES[s] for s in sorted(set(sig.values()))},
              "pinned": sorted(decl[i]["path"] or f"mod{i}" for i in pinned),
              "view_tokens": n_tokens(view), "target_tokens": V}
    return view, report


def budget_audit(turns: list[dict], V: int) -> None:
    """How much of this document is actually distinctive? The number that decides whether the
    fixture can test composition at all."""
    mods = [m for m in parse_modules("\n".join(t["text"] for t in turns)) if m["header"]]
    decl = [m for m in mods if declares(m)]
    pure = [m for m in mods if not declares(m)]
    N = sum(t["tokens"] for t in turns)
    at1 = sum(n_tokens("\n".join(render_module(m, 1)) + "\n") for m in decl)
    at0 = sum(n_tokens("\n".join(render_module(m, 0)) + "\n") for m in decl)
    block = n_tokens(pattern_block(pure))
    print(f"document                         {N:>8,} tok  ({len(mods)} modules)")
    print(f"  declaration-free (R1 collapse) {len(pure):>8} modules -> one {block}-tok pattern block")
    print(f"  declaring modules              {len(decl):>8} modules")
    print(f"    their declarations (sigma 1) {at1:>8,} tok")
    print(f"    verbatim, bodies included    {at0:>8,} tok")
    print(f"\nview budget V                    {V:>8,} tok")
    print(f"distinctive content + block      {at1 + block:>8,} tok "
          f"= {(at1 + block) / V:.0%} of ONE view")
    if at1 + block <= V:
        print("\n  => A compressor that applies R1 fits the ENTIRE distinctive content of this\n"
              "     document into the level-1 view. The split-fact guard cannot survive such a\n"
              "     compressor, and no schedule wrapped around this document can test composition\n"
              "     across passes. This is a property of the FIXTURE, not of the compressor.")
    else:
        print(f"\n  => distinctive content exceeds one view by "
              f"{(at1 + block) / V:.1f}x — composition is testable.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["hand_blind", "hand_oracle"])
    ap.add_argument("--V", type=int, default=None)
    ap.add_argument("--branching", type=int, default=2)
    ap.add_argument("--budget-audit", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    V = args.V or cfg["schedule"]["code"]["V"]
    turns = load_turns(P7 / "fixture" / "host_doc.jsonl")
    passes, levels = plan_passes(turns, V, args.branching)
    N = sum(t["tokens"] for t in turns)

    if args.budget_audit or not args.arm:
        budget_audit(turns, V)
        return

    spec_fx = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    # DECLARED ORACLE: these paths are named because the probe is known. hand_blind never sees them.
    oracle_paths = (("pricing/region_tables.py", "fulfillment/line_quote.py")
                    if args.arm == "hand_oracle" else ())

    out_passes = []
    for p in passes:
        if p["verbatim"]:
            view, report = p["slice_text"], None
        else:
            view, report = author_view(p["slice_text"], V, oracle_paths)
        vt = n_tokens(view)
        out_passes.append({
            "level": p["level"], "tile": p["tile"], "n_tiles_at_level": p["n_tiles_at_level"],
            "turn_lo": p["turn_lo"], "turn_hi": p["turn_hi"],
            "idx_lo": p["idx_lo"], "idx_hi": p["idx_hi"],
            "slice_tokens": p["slice_tokens"], "view_tokens": vt,
            "compression_ratio": round(p["slice_tokens"] / max(vt, 1), 2),
            "verbatim": p["verbatim"],
            "view_source": "verbatim_tile" if p["verbatim"] else f"authored-{args.arm}",
            "compressor_report": report, "view_text": view})
        print(f"  L{p['level']}t{p['tile']:<2} {p['slice_tokens']:>7,} -> {vt:>5,} tok "
              f"({out_passes[-1]['compression_ratio']:>5.1f}x)"
              + (f"  collapsed {report['n_pure_collapsed']}, kept {report['n_declaring']}"
                 if report else "  verbatim"))

    rec = {"_meta": {
        "arm": args.arm, "compressor_key": None, "note": ARM_SPEC[args.arm]["note"],
        "probe_blind": ARM_SPEC[args.arm]["probe_blind"],
        "compressor_name": f"authored-{args.arm}",
        "authoring_rule": "R1 collapse declaration-free modules to one pattern block; "
                          "R2 spend the freed budget on declaring modules at the mildest "
                          "severity that fits; R3 no module treated specially",
        "oracle_paths": list(oracle_paths) or None,
        "oracle_note": ("DECLARED ORACLE — module paths pinned because the probe is known; "
                        "design input only, never poolable with a verdict"
                        if oracle_paths else None),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "V": V, "branching": args.branching, "levels": levels,
        "doc_tokens": N, "n_turns": len(turns), "K": len(passes),
        "host_doc_sha256": hashlib.sha256(
            (P7 / "fixture" / "host_doc.jsonl").read_bytes()).hexdigest(),
    }, "passes": out_passes, "complete": True}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{args.arm}.json"
    out_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    tot = sum(p["view_tokens"] for p in out_passes)
    print(f"\n{len(out_passes)} views | {tot:,} view tok = {tot / N:.2f}x source")
    print(f"-> {out_path.relative_to(ROOT)}")
    print(f"\nnext: python experiments/e2prime/verify_pyramid_schedule.py --views {args.arm}")


if __name__ == "__main__":
    main()
