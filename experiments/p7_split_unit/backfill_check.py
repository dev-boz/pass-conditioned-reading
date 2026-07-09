"""P7 GATE 1 — backfill defense (the brief's make-or-break, run BEFORE the battery).

Give the model ONLY fragment-2 (the call site + the reconciliation adder, NO table) and ask the
scoring question. It MUST fail: it cannot know REGION_SURCHARGE_CENTS[23], so it cannot produce
the ground-truth 2353 (nor the table value 988). Stochastic, so we test temp-0 + sampled seeds.

PASS (fixture is backfill-defended) iff NO decode emits the exact ground-truth integer.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pca.llm import LlamaServer  # noqa: E402


def draws_for(n):
    return [(42, 0.0)] + [(s, 0.7) for s in range(1, n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--n", type=int, default=4, help="draws: temp-0 + (n-1) sampled temp-0.7 seeds")
    ap.add_argument("--threads", type=int, default=None)
    ap.add_argument("--ngl", type=int, default=None)
    args = ap.parse_args()
    cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
    mkey = args.model or cfg.get("default_model", "7b")
    m = cfg["models"][mkey]
    DRAWS = draws_for(args.n)
    spec = json.loads((HERE / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    frag2 = spec["fragment2_text"]
    gt = str(spec["ground_truth_answer"])          # "2353"
    tval = str(spec["table_value_for_queried"])    # "988"
    q = spec["scoring_question"]

    system = ("You are a precise Python code analyst. Answer using ONLY the code shown. "
              "If the code shown is insufficient to determine the answer, say exactly: "
              "INSUFFICIENT.")
    user = (f"Here is the only code available:\n\n{frag2}\n\n"
            f"Question: {q}\nShow your reasoning briefly, then give the final answer on its own "
            f"line as: ANSWER: <integer or INSUFFICIENT>")

    server = LlamaServer(str(ROOT / m["server_exe"]), str(ROOT / m["model_path"]),
                         ctx=m["ctx"], port=m["port"] + 5,
                         threads=args.threads or m["threads"],
                         n_gpu_layers=args.ngl if args.ngl is not None else m.get("n_gpu_layers", 0))
    server.ensure_running()
    results, any_gt = [], False
    for seed, temp in DRAWS:
        resp = server.chat(system, user, max_tokens=400, temperature=temp, seed=seed)
        txt = resp["text"]
        ints = re.findall(r"-?\d+", txt.replace(",", ""))
        has_gt = gt in ints
        has_tval = tval in ints
        any_gt = any_gt or has_gt
        m = re.search(r"ANSWER:\s*([A-Za-z0-9\-]+)", txt)
        ans = m.group(1) if m else "(none)"
        results.append({"seed": seed, "temp": temp, "answer_field": ans,
                        "emits_ground_truth": has_gt, "emits_table_value": has_tval,
                        "wall_s": resp["wall_s"], "text": txt})
        print(f"  seed={seed} t={temp} -> ANSWER={ans!r} gt={has_gt} tval={has_tval} ({resp['wall_s']}s)",
              flush=True)
    server.stop()

    verdict = "PASS (backfill-defended)" if not any_gt else "FAIL (guessable — REDESIGN)"
    out = {"gate": "backfill_defense", "model": mkey, "n": args.n, "ground_truth": gt,
           "table_value": tval, "verdict": verdict, "any_decode_emits_ground_truth": any_gt,
           "draws": results}
    (HERE / f"backfill_check_result_{mkey}.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nGATE 1 {verdict}: no decode emitted {gt} == {not any_gt}")


if __name__ == "__main__":
    main()
