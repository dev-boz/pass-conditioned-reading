"""P7 — freeze the Phase-A structure-preserving scaffold (deterministic, $0, no model).

Runs compress_code over build_schedule's Phase-A chunk boundaries and caches the views to
scaffold_struct.json (P6 gen_scaffold pattern), so every draw/seed reuses identical Phase-A views
and the guards stay meaningful. Re-asserts the State-D guard (queried table entry + adder survive).

  python experiments/p7_split_unit/gen_scaffold.py                                  # v2 (architecture)
  python experiments/p7_split_unit/gen_scaffold.py --compressor compress_code_v1 --out scaffold_v1.json
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
from pca.planted import build_schedule          # noqa: E402
from pca.textutils import n_tokens              # noqa: E402
from verify_fixture import load_turns           # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compressor", default="compress_code", help="module exposing compress_code()")
    ap.add_argument("--out", default="scaffold_struct.json")
    args = ap.parse_args()
    compress_code = importlib.import_module(args.compressor).compress_code
    cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
    spec = json.loads((HERE / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    turns = load_turns(HERE / "fixture" / "host_doc.jsonl")
    s = cfg["schedule"]
    sch = build_schedule(turns, s["V"], s["R"], tuple(s["stage_fracs"]))
    chunksA = [p for p in sch if p["phase"] == "A"]

    out = []
    for i, p in enumerate(chunksA):
        view = compress_code(p["slice_text"], s["V"])
        out.append({"chunk": i, "turn_lo": p["turn_lo"], "turn_hi": p["turn_hi"],
                    "slice_tokens": p["slice_tokens"], "view_tokens": n_tokens(view),
                    "compression_ratio": round(p["slice_tokens"] / max(n_tokens(view), 1), 2),
                    "compressor": "structure-preserving-code-v1", "view_text": view})
        print(f"  chunk {i} turns{p['turn_lo']}-{p['turn_hi']}: "
              f"{p['slice_tokens']}->{n_tokens(view)}tok ({out[-1]['compression_ratio']}x)")

    # State-D guard against the frozen views
    entry = f"{spec['queried_code']}: {spec['table_value_for_queried']}"
    adder = f"RECONCILIATION_ADDER_CENTS = {spec['reconciliation_adder_cents']}"
    all_views = "\n".join(c["view_text"] for c in out)
    assert entry in all_views, f"State-D guard FAIL: '{entry}' not in frozen scaffold"
    assert adder in all_views, f"State-D guard FAIL: adder not in frozen scaffold"
    (HERE / args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"DONE -> {args.out} ({len(out)} chunks); State-D guard PASS "
          f"(table entry '{entry}' + adder present)")


if __name__ == "__main__":
    main()
