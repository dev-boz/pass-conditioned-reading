"""CLOSE-ONLY probe — is the last link scale-limited? ($0, frozen weights, minutes not hours.)

The 2026-08-02 retain-guard run decomposed the chain completely. On `llm_roleaware` with
guard="retain", two draws finished with BOTH operands in the final state (c1=True, 2/10 — it had
been 0/10 on every pyramid arm without the guard), and both still failed to answer: one returned no
ANSWER line, the other returned 1365 — the adder alone, with `23: 988` sitting in the same state.

So the failure is no longer compression, coverage, recording or retention. It is COMPOSE, with the
operands present. GATE-3 already measured compose as scale-limited (1.5B student 1/10 vs untrained
7B 10/10) — but on a HAND-SEEDED state. This asks the same question of states the model built
itself, which is the version that matters and which has never been run.

Method: lift `final_state` verbatim from archived chain-gate draws, replay ONLY the closing turn
(the same CLOSE_SYSTEM and closing user prompt the gate uses, byte-identical), across models. The
recording passes are not re-run, so a full arm costs one call per draw.

  python experiments/e2prime/close_only_probe.py --run llm_roleaware_guard-retain --models student,qwen7b
  python experiments/e2prime/close_only_probe.py --run llm_roleaware_guard-retain --only-c1
  python experiments/e2prime/close_only_probe.py --summarize
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P7 = ROOT / "experiments" / "p7_split_unit"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(P7))
sys.path.insert(0, str(HERE))

from pca.llm import LlamaServer                                   # noqa: E402
from pca.textutils import n_tokens                                # noqa: E402
from stagea_chain_gate import CLOSE_SYSTEM, _int_present          # noqa: E402
from stagea_p1_probes import MODELS                               # noqa: E402

OUT_DIR = ROOT / "runs" / "stageA_chain_gate" / "_close_only"
PYR = ROOT / "runs" / "stageA_chain_gate_pyramid"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="llm_roleaware_guard-retain",
                    help="subdirectory of runs/stageA_chain_gate_pyramid (or 'd25')")
    ap.add_argument("--models", default="student,qwen7b",
                    help="local GGUF keys, and/or 'claude:<model>' for an API rung "
                         "(e.g. claude:haiku) — the closing turn is one call per draw, so an "
                         "off-box rung costs ten calls")
    ap.add_argument("--only-c1", action="store_true",
                    help="only draws whose final state holds BOTH operands — the cells where a "
                         "compose failure is unambiguously a compose failure")
    ap.add_argument("--temp", type=float, default=0.0,
                    help="0 = deterministic. The recording passes are already fixed; this isolates "
                         "the closing step, so sampling noise is not wanted by default.")
    ap.add_argument("--max-tokens", type=int, default=1200)
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--ctx", type=int, default=24576)
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--summarize", action="store_true")
    args = ap.parse_args()

    if args.summarize:
        summarize()
        return

    spec = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    truth = spec["ground_truth_answer"]
    tval, adder = spec["table_value_for_queried"], spec["reconciliation_adder_cents"]
    src = (ROOT / "runs" / "stageA_chain_gate") if args.run == "d25" else (PYR / args.run)
    if not src.exists():
        raise SystemExit(f"no such run dir: {src}")

    draws = []
    for f in sorted(src.glob("student_s*_t0.7.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        if not r.get("complete"):
            continue
        ff = r["final_flags"]
        if args.only_c1 and not (ff["queried_mapping"] and ff["adder_value_present"]):
            continue
        draws.append({"seed": r["_meta"]["seed"], "state": r["final_state"],
                      "state_tokens": r["final_state_tokens"],
                      "binding": ff["queried_mapping"], "adder": ff["adder_value_present"],
                      "c1": bool(ff["queried_mapping"] and ff["adder_value_present"]),
                      "orig_answer": r["closing"]["answer"]})
    if not draws:
        raise SystemExit(f"no draws matched in {src}"
                         + (" (--only-c1 with no c1 draws)" if args.only_c1 else ""))

    close_user = (lambda st: f"FINAL STATE:\n{st}\n\nQuestion: {spec['scoring_question']}\n"
                             "Reason briefly from the state, then end with: ANSWER: <integer>")
    print(f"run={args.run} draws={len(draws)} "
          f"(c1={sum(d['c1'] for d in draws)}, binding={sum(d['binding'] for d in draws)}, "
          f"adder={sum(d['adder'] for d in draws)}) models={args.models} temp={args.temp}")
    if args.dry_run:
        d = draws[0]
        print(f"\n--- CLOSING SYSTEM ---\n{CLOSE_SYSTEM}")
        print(f"\n--- CLOSING USER (seed {d['seed']}, state {d['state_tokens']} tok, elided) ---")
        print(close_user("<STATE>"))
        print("\nDry run OK. Nothing served, nothing written.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    exe = ROOT / "models" / "llamacpp" / "llama-server.exe"
    for mk in args.models.split(","):
        api = mk.startswith("claude:")
        model = None if api else MODELS[mk]
        if not api and not model.exists():
            print(f"[skip] {mk}: {model} not present")
            continue
        out = OUT_DIR / f"{args.run}__{mk.replace(':', '-')}_t{args.temp:g}.json"
        rec = {"_meta": {"probe": True, "gate_legal": False, "probe_id": "close_only",
                         "run": args.run, "model": mk, "temp": args.temp,
                         "only_c1": args.only_c1, "n_draws": len(draws),
                         "note": "closing turn ONLY, replayed on archived final states; recording "
                                 "passes not re-run",
                         "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")},
               "draws": [], "complete": False}
        print(f"\n=== {mk} ===", flush=True)
        server = None
        if not api:
            server = LlamaServer(str(exe), str(model), ctx=args.ctx, port=args.port,
                                 n_gpu_layers=args.ngl)
            server.ensure_running()
        t0 = time.time()
        try:
            for d in draws:
                if api:
                    # The API rung sends system+user as one prompt, since `claude -p` takes a
                    # single turn. Temperature is not exposed; the record stamps that.
                    import subprocess
                    from shutil import which
                    import os as _os
                    exe_c = (_os.environ.get("PCA_CLAUDE_EXE") or which("claude") or "claude")
                    t1 = time.time()
                    p = subprocess.run([exe_c, "-p", "--model", mk.split(":", 1)[1]],
                                       input=f"{CLOSE_SYSTEM}\n\n{close_user(d['state'])}",
                                       capture_output=True, text=True, encoding="utf-8",
                                       timeout=300)
                    if p.returncode != 0:
                        raise RuntimeError(f"claude -p exit {p.returncode}: {(p.stderr or '')[:200]}")
                    resp = {"text": (p.stdout or "").strip(), "wall_s": round(time.time() - t1, 1)}
                else:
                    resp = server.chat(CLOSE_SYSTEM, close_user(d["state"]),
                                       max_tokens=args.max_tokens, temperature=args.temp,
                                       seed=d["seed"])
                txt = resp["text"]
                m = re.search(r"ANSWER:\s*(-?\d[\d,]*)", txt)
                ans = int(m.group(1).replace(",", "")) if m else None
                shown = _int_present(txt, tval) and _int_present(txt, adder)
                rec["draws"].append({**{k: v for k, v in d.items() if k != "state"},
                                     "answer": ans, "correct": ans == truth,
                                     "derivation_visible": shown, "raw_output": txt,
                                     "wall_s": resp.get("wall_s")})
                print(f"  seed {d['seed']:>2} c1={d['c1']} state={d['state_tokens']}tok "
                      f"-> ANSWER={ans} correct={ans == truth} deriv={shown} "
                      f"(was {d['orig_answer']}) [{resp.get('wall_s')}s]", flush=True)
                out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        finally:
            if server is not None:
                server.stop()
                time.sleep(3)
        rec["complete"] = True
        rec["wall_s"] = round(time.time() - t0, 1)
        out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        n = len(rec["draws"])
        print(f"  -> correct {sum(x['correct'] for x in rec['draws'])}/{n} "
              f"| of the c1 draws {sum(x['correct'] for x in rec['draws'] if x['c1'])}/"
              f"{sum(x['c1'] for x in rec['draws'])}", flush=True)
    summarize()


def summarize() -> None:
    print(f"\n{'run':<34} {'model':<9} {'n':>3} {'correct':>8} {'correct|c1':>11} {'c1 draws':>9}")
    for f in sorted(OUT_DIR.glob("*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        d = r["draws"]
        if not d:
            continue
        m = r["_meta"]
        c1 = [x for x in d if x["c1"]]
        print(f"{m['run']:<34} {m['model']:<9} {len(d):>3} "
              f"{sum(x['correct'] for x in d):>6}/{len(d)} "
              f"{sum(x['correct'] for x in c1):>8}/{len(c1)} {len(c1):>9}")
    print("\ncorrect|c1 = composed 2353 GIVEN both operands were in the state. That denominator is "
          "the compose question; the rest is upstream. Probe numbers, gate_legal=false.")


if __name__ == "__main__":
    main()
