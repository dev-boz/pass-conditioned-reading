"""Generate and FREEZE the pyramid view set for one compressor arm.

The compressor is architecture (COMPRESSOR-V2.md), so "which compressor" is an experimental arm,
not a config detail: it decides what every level of the pyramid can carry, and therefore what the
chain gate is even able to measure. This generates one frozen view set per arm so every draw, seed
and model reads byte-identical views, and so the expensive (LLM) arms are paid for once.

The TILING is identical across arms — `pyramid_levels` + `balanced_tile` depend only on the turns
and V — so arms differ in exactly one thing: what the compressor did to the same spans.

Arms:
  extractive     general, deterministic, budget-aware (SumBasic). The off-the-shelf baseline.
  graded         role-specialized, deterministic, sigma-parameterized (pca.compress_graded).
  llm_general    Claude Haiku 4.5 with the generic D29 summary prompt — a general LLM compressor.
  llm_roleaware  Claude Haiku 4.5 told its place in the architecture (pca.compressor
                 _role_aware_prompt) — "specialised for the role".
  hand_blind     hand-authored, one uniform rule applied to every module, probe-blind.
  hand_oracle    hand-authored knowing the probe — DECLARED ORACLE, diagnostic only.

  python experiments/e2prime/gen_pyramid_views.py --arm extractive
  python experiments/e2prime/gen_pyramid_views.py --arm graded
  python experiments/e2prime/gen_pyramid_views.py --arm llm_general --workers 2
  python experiments/e2prime/gen_pyramid_views.py --arm llm_roleaware --workers 2 --probe-one
  python experiments/e2prime/gen_pyramid_views.py --list
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P7 = ROOT / "experiments" / "p7_split_unit"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(P7))
sys.path.insert(0, str(HERE))

from pca.compressor import get_compressor                        # noqa: E402
from pca.planted import balanced_tile, pyramid_levels            # noqa: E402
from pca.textutils import n_tokens                               # noqa: E402
from verify_fixture import load_turns                            # noqa: E402
from stagea_chain_gate import load_config                        # noqa: E402

OUT_DIR = HERE / "pyramid_views"

# Arms whose views are authored by hand rather than generated (see AUTHORED-VIEWS.md). They are
# produced by author_pyramid_views.py and only validated here.
HAND_ARMS = {"hand_blind", "hand_oracle"}

ARM_SPEC = {
    "extractive":    {"compressor": "extractive",    "probe_blind": True,
                      "note": "general deterministic extractive (SumBasic), budget-aware"},
    "graded":        {"compressor": "graded",        "probe_blind": True,
                      "note": "role-specialized deterministic sigma-ladder (compress_graded)"},
    "llm_general":   {"compressor": "llm",           "probe_blind": True,
                      "note": "Haiku 4.5, generic D29 summary prompt (general compressor)"},
    "llm_roleaware": {"compressor": "llm_roleaware", "probe_blind": True,
                      "note": "Haiku 4.5, told its architectural role (specialised for the role)"},
    "hand_blind":    {"compressor": None,            "probe_blind": True,
                      "note": "hand-authored, one uniform rule over all modules, probe-blind"},
    "hand_oracle":   {"compressor": None,            "probe_blind": False,
                      "note": "hand-authored knowing the probe — DECLARED ORACLE, diagnostic only"},
}


def plan_passes(turns: list[dict], V: int, branching: int = 2) -> list[dict]:
    """The tiling, compressor-independent. Identical for every arm."""
    levels = pyramid_levels(turns, V, branching)
    out = []
    for level, n_tiles in enumerate(levels, start=1):
        for ti, (lo, hi) in enumerate(balanced_tile(turns, n_tiles)):
            slice_text = "\n".join(t["text"] for t in turns[lo:hi + 1])
            out.append({"level": level, "tile": ti, "n_tiles_at_level": n_tiles,
                        "turn_lo": turns[lo]["turn"], "turn_hi": turns[hi]["turn"],
                        "idx_lo": lo, "idx_hi": hi,
                        "slice_text": slice_text, "slice_tokens": n_tokens(slice_text),
                        "verbatim": n_tokens(slice_text) <= V})
    for i, p in enumerate(out):
        p["k"], p["K"] = i + 1, len(out)
    return out, levels


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=sorted(ARM_SPEC))
    ap.add_argument("--V", type=int, default=None, help="per-view budget (default: config)")
    ap.add_argument("--branching", type=int, default=2)
    ap.add_argument("--workers", type=int, default=2, help="LLM arms only")
    ap.add_argument("--timeout", type=int, default=600, help="LLM call timeout (s)")
    ap.add_argument("--probe-one", action="store_true",
                    help="LLM arms: generate ONE view (the coarsest) and stop, to check the "
                         "delivery path and the output before paying for the rest")
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    V = args.V or cfg["schedule"]["code"]["V"]
    turns = load_turns(P7 / "fixture" / "host_doc.jsonl")
    passes, levels = plan_passes(turns, V, args.branching)
    N = sum(t["tokens"] for t in turns)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.list or not args.arm:
        print(f"fixture: {N:,} tok, {len(turns)} turns | V={V} | levels {levels} | "
              f"{len(passes)} passes ({sum(not p['verbatim'] for p in passes)} compressed, "
              f"{sum(p['verbatim'] for p in passes)} verbatim)\n")
        print(f"{'arm':<15} {'status':<12} {'views':>6}  note")
        for a, s in ARM_SPEC.items():
            f = OUT_DIR / f"{a}.json"
            if f.exists():
                r = json.loads(f.read_text(encoding="utf-8"))
                st = "complete" if r.get("complete") else f"partial"
                nv = len(r.get("passes", []))
            else:
                st, nv = "missing", 0
            print(f"{a:<15} {st:<12} {nv:>6}  {s['note']}")
        return

    spec = ARM_SPEC[args.arm]
    out_path = OUT_DIR / f"{args.arm}.json"
    if args.arm in HAND_ARMS:
        raise SystemExit(f"'{args.arm}' is hand-authored — build it with "
                         f"experiments/e2prime/author_pyramid_views.py, then validate with "
                         f"verify_pyramid_schedule.py --views {args.arm}")

    rec = {"_meta": {}, "passes": [], "complete": False}
    if out_path.exists() and not args.redo:
        try:
            rec = json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            rec = {"_meta": {}, "passes": [], "complete": False}
    done = {(p["level"], p["tile"]): p for p in rec.get("passes", [])}

    rec["_meta"] = {
        "arm": args.arm, "compressor_key": spec["compressor"], "note": spec["note"],
        "probe_blind": spec["probe_blind"],
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "V": V, "branching": args.branching, "levels": levels,
        "doc_tokens": N, "n_turns": len(turns), "K": len(passes),
        "host_doc_sha256": hashlib.sha256(
            (P7 / "fixture" / "host_doc.jsonl").read_bytes()).hexdigest(),
    }

    is_llm = spec["compressor"] in ("llm", "llm_roleaware")
    kw = {"timeout": args.timeout} if is_llm else {}
    comp = get_compressor(spec["compressor"], **kw)
    rec["_meta"]["compressor_name"] = getattr(comp, "name", spec["compressor"])

    todo = [p for p in passes if not p["verbatim"] and (p["level"], p["tile"]) not in done]
    if args.probe_one:
        todo = todo[:1]
    print(f"arm={args.arm} compressor={rec['_meta']['compressor_name']} V={V}\n"
          f"{len(passes)} passes | {sum(p['verbatim'] for p in passes)} verbatim (free) | "
          f"{len(done)} cached | {len(todo)} to generate", flush=True)

    def build(p: dict) -> dict:
        t0 = time.time()
        if p["verbatim"]:
            view, report = p["slice_text"], None
        elif getattr(comp, "accepts_context", False):
            view = comp.compress(p["slice_text"], V, level=p["level"], n_levels=len(levels))
            report = None
        else:
            view = comp.compress(p["slice_text"], V)
            report = getattr(comp, "last_report", None)
        vt = n_tokens(view)
        return {"level": p["level"], "tile": p["tile"], "n_tiles_at_level": p["n_tiles_at_level"],
                "turn_lo": p["turn_lo"], "turn_hi": p["turn_hi"],
                "idx_lo": p["idx_lo"], "idx_hi": p["idx_hi"],
                "slice_tokens": p["slice_tokens"], "view_tokens": vt,
                "compression_ratio": round(p["slice_tokens"] / max(vt, 1), 2),
                "verbatim": p["verbatim"],
                "view_source": "verbatim_tile" if p["verbatim"] else rec["_meta"]["compressor_name"],
                "compressor_report": report, "gen_s": round(time.time() - t0, 1),
                "view_text": view}

    lock = threading.Lock()

    def save() -> None:
        rec["passes"] = sorted(done.values(), key=lambda r: (r["level"], r["tile"]))
        out_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")

    # verbatim passes are free and deterministic — always (re)filled
    for p in passes:
        if p["verbatim"]:
            done[(p["level"], p["tile"])] = build(p)

    n_fail = 0
    if is_llm and args.workers > 1:
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {ex.submit(build, p): p for p in todo}
            for fut in as_completed(futs):
                p = futs[fut]
                try:
                    r = fut.result()
                except Exception as e:
                    n_fail += 1
                    print(f"  FAIL L{p['level']}t{p['tile']}: {str(e)[:160]}", flush=True)
                    continue
                with lock:
                    done[(r["level"], r["tile"])] = r
                    save()
                    print(f"  L{r['level']}t{r['tile']:<2} {r['slice_tokens']:>7,} -> "
                          f"{r['view_tokens']:>5,} tok ({r['compression_ratio']:>5.1f}x) "
                          f"[{r['gen_s']}s]", flush=True)
    else:
        for p in todo:
            try:
                r = build(p)
            except Exception as e:
                n_fail += 1
                print(f"  FAIL L{p['level']}t{p['tile']}: {str(e)[:160]}", flush=True)
                continue
            done[(r["level"], r["tile"])] = r
            save()
            print(f"  L{r['level']}t{r['tile']:<2} {r['slice_tokens']:>7,} -> "
                  f"{r['view_tokens']:>5,} tok ({r['compression_ratio']:>5.1f}x) "
                  f"[{r['gen_s']}s]", flush=True)

    rec["complete"] = len(done) == len(passes) and not args.probe_one
    save()
    tot = sum(r["view_tokens"] for r in done.values())
    print(f"\n{len(done)}/{len(passes)} views | {tot:,} view tok = {tot / N:.2f}x source | "
          f"failures {n_fail} | complete={rec['complete']}")
    print(f"-> {out_path.relative_to(ROOT)}")
    if not rec["complete"] and not args.probe_one:
        print("re-run to resume (cached views are skipped)")
    print(f"\nnext: python experiments/e2prime/verify_pyramid_schedule.py --views {args.arm}")


if __name__ == "__main__":
    main()
