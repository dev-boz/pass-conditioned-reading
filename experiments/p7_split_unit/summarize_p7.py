"""Headline summary for a P7 matrix run (see TRANSFER.md sec 6). Read-only; draws no conclusions.

  python experiments/p7_split_unit/summarize_p7.py --model 7b
  python experiments/p7_split_unit/summarize_p7.py --model 7b --model 14b   # contrast

Money comparison = coupled_full vs verbatim_only on closing ANSWER == ground_truth (2353).
Chain per seed (coupled_full): record (queried_mapping ever seen) -> retain (in final state)
-> compose (closing answer == GT). State-D guard: first recording must be in a Phase-A pass.
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(pattern):
    out = {}
    for f in glob.glob(str(HERE / pattern)):
        try:
            out[f] = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  !! could not read {f}: {e}")
    return out


def arm_ans(d, arm):
    a = d.get(arm, {})
    c = a.get("closing", {}) or {}
    return c.get("answer"), bool(c.get("correct"))


def summarize_model(model):
    print(f"\n{'='*78}\nMODEL: {model}\n{'='*78}")

    # ---- gates ----
    bf = HERE / f"backfill_check_result_{model}.json"
    cg = HERE / f"compose_gate_result_{model}.json"
    if bf.exists():
        b = json.loads(bf.read_text(encoding="utf-8"))
        rows = b.get("results", b if isinstance(b, list) else b.get("draws", []))
        if isinstance(b, dict) and "results" in b:
            rows = b["results"]
        n = len(rows) if isinstance(rows, list) else b.get("n")
        correct = sum(1 for r in rows if r.get("correct") or r.get("gt")) if isinstance(rows, list) else b.get("n_correct")
        print(f"GATE backfill (unit unguessable): {correct}/{n if n else '?'} correct  (expect 0)")
    if cg.exists():
        c = json.loads(cg.read_text(encoding="utf-8"))
        print(f"GATE compose : keys={list(c.keys())[:8]}")

    # ---- specifics (headline) ----
    spec = load(f"p7_results_{model}_spec_s*.json")
    gt = None
    rows = []
    incomplete = 0
    for f, d in sorted(spec.items()):
        if not all(a in d for a in ("dense", "verbatim_only", "coupled_full")):
            incomplete += 1
            continue
        m = d.get("_meta", {})
        gt = m.get("ground_truth", gt)
        seed, temp = m.get("seed"), m.get("temp")
        d_ans, d_ok = arm_ans(d, "dense")
        v_ans, v_ok = arm_ans(d, "verbatim_only")
        c_ans, c_ok = arm_ans(d, "coupled_full")
        cf = d.get("coupled_full", {})
        rec = bool(cf.get("queried_ever"))
        phase = cf.get("queried_first_phase")
        retain = bool((cf.get("final_mapping") or {}).get("queried_mapping"))
        rows.append((seed, temp, d_ans, d_ok, v_ans, v_ok, c_ans, c_ok, rec, phase, retain))

    print(f"\nSPECIFICS end-to-end (ground truth = {gt}); n={len(rows)} complete seeds"
          + (f"  ({incomplete} incomplete/stale skipped)" if incomplete else ""))
    print(f"{'seed':>5} {'t':>4} | {'dense':>8} {'verb':>8} {'coupled':>8} || "
          f"{'rec':>3} {'Dgd':>3} {'ret':>3} {'2353?':>5}")
    print("-" * 72)
    for (seed, temp, d_ans, d_ok, v_ans, v_ok, c_ans, c_ok, rec, phase, retain) in rows:
        print(f"{seed:>5} {temp:>4} | {str(d_ans):>8} {str(v_ans):>8} {str(c_ans):>8} || "
              f"{'Y' if rec else '.':>3} {('A' if phase=='A' else (phase or '.')):>3} "
              f"{'Y' if retain else '.':>3} {'C' if c_ok else '.':>5}")

    n = len(rows) or 1
    coup_win = sum(1 for r in rows if r[7])
    verb_win = sum(1 for r in rows if r[5])
    dense_win = sum(1 for r in rows if r[3])
    rec_n = sum(1 for r in rows if r[8])
    dguard = sum(1 for r in rows if r[9] == "A")
    retain_n = sum(1 for r in rows if r[10])
    print("-" * 72)
    print(f"coupled_full ANSWER==2353 : {coup_win}/{n}")
    print(f"verbatim_only ANSWER==2353: {verb_win}/{n}   (expected to fail)")
    print(f"dense ANSWER==2353        : {dense_win}/{n}")
    print(f"RECORD (queried ever)     : {rec_n}/{n}")
    print(f"  of which State-D (A)    : {dguard}/{rec_n if rec_n else 1}")
    print(f"RETAIN (in final state)   : {retain_n}/{n}")
    print(f"COMPOSE (==2353)          : {coup_win}/{n}")

    # ---- op-protocol following (CROSS-FAMILY interpretation guard) ----
    # Mean edit-ops emitted per coupled pass. A value near 1 means the family largely IGNORED the
    # ADD/REPLACE edit-DSL, so the state never builds -> a 0 RECORD/COMPOSE is a PROTOCOL-TRANSFER
    # failure (prompt artifact), NOT evidence about the architecture or the model. Read zeros only
    # for families whose ops/pass is healthy (Qwen ran ~4-20).
    op_means, st_finals = [], []
    for f, d in spec.items():
        ps = (d.get("coupled_full") or {}).get("passes") or []
        if ps:
            op_means.append(sum(p.get("n_gen", 0) for p in ps) / len(ps))
            st_finals.append(ps[-1].get("state_tokens", 0))
    if op_means:
        mo = sum(op_means) / len(op_means)
        ms = int(sum(st_finals) / len(st_finals))
        flag = "  <== ~1 ops/pass: IGNORED op-DSL, zeros are protocol-transfer not architecture" if mo < 2 else ""
        print(f"OP-FOLLOWING (coupled)    : mean {mo:.1f} ops/pass (min {min(op_means):.1f}); "
              f"final state ~{ms}tok{flag}")

    # ---- neutral (un-prompted recording) ----
    neut = load(f"p7_results_{model}_mp6_neutral_s*.json")
    nrec = 0
    for f, d in neut.items():
        if (d.get("coupled_full") or {}).get("queried_ever"):
            nrec += 1
    print(f"\nNEUTRAL (un-prompted) coupled records table: {nrec}/{len(neut)}  (expect ~0)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", action="append", required=True)
    a = ap.parse_args()
    for m in a.model:
        summarize_model(m)


if __name__ == "__main__":
    main()
