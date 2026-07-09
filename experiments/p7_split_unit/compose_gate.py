"""P7 GATE 3 — positive control / ceiling check (the advisor's blocking gate; the F7-gate idea
applied to P7's ANSWER metric).

GATE 1 proved one fragment can't win (floor). GATE 2 proved coupled records the table where verbatim
doesn't (discriminator). Neither proves the untrained 7B can actually COMPOSE the answer even with
the full structure in state: recall 23->988 from a 24-entry table, recall the adder, connect
compute_line_surcharge to base+adder, and add. That is a multi-step chain P4/P6 never tested
(recall, not compose).

Seed the integration state with EVERYTHING coupled_full would have at its best (full table + adder +
function signature + realistic filler), then run the closing call and check for the exact answer.
  PASS -> a battery coupled-failure is a genuine retention/compose failure (run is interpretable).
  FAIL -> the battery is predicted floor-limited-null; carry to E2' WITHOUT burning ~26h.
Answer scored by the ANSWER: field (exact int), NOT substring (2353/988/1365 collide with filler).
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

CLOSING_SYSTEM = ("You are answering a question using ONLY the integration state below (an analytical "
                  "brief built from a codebase across many passes). Use only values present in the "
                  "state; do not invent numbers. Reason briefly, then end with a line 'ANSWER: "
                  "<integer>'.")


def best_case_state(spec: dict) -> str:
    """The state coupled_full would hold at its best: full table + adder + function, amid filler
    entries (realistic state noise, matching the GATE-2 coupled recordings)."""
    tbl = "{" + ", ".join(f"{k}: {v}" for k, v in spec["table"].items()) + "}"
    adder = spec["reconciliation_adder_cents"]
    entries = [
        "Module billing/digest19.py: helpers normalize_parcel, rank_slot, format_slot, validate_shard.",
        "Module carrier/cursor20.py: tokenize_record, hash_claim, compact_packet, sample_lane.",
        f"Module pricing/region_tables.py defines REGION_SURCHARGE_CENTS = {tbl} (cents per region code; arbitrary ops-review values).",
        "Module audit/node21.py: normalize_parcel, tokenize_record, merge_manifest, compact_packet.",
        "Module serialize/tariff22.py: flatten_parcel, resolve_token, trim_shard, batch_manifest.",
        f"Module fulfillment/line_quote.py defines RECONCILIATION_ADDER_CENTS = {adder}; compute_line_surcharge(region_code) returns REGION_SURCHARGE_CENTS[region_code] + RECONCILIATION_ADDER_CENTS.",
        "Module routing/digest33.py: dedupe_route, tokenize_digest, flatten_packet, expand_packet.",
        "Module metrics/window29.py: bucket_claim, clamp_claim, rank_manifest, scan_parcel.",
    ]
    return "\n".join(f"S{i+1}: {e}" for i, e in enumerate(entries))


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
    gt = spec["ground_truth_answer"]                 # 2353
    state = best_case_state(spec)
    q = spec["scoring_question"]
    user = f"INTEGRATION STATE:\n{state}\n\nQuestion: {q}\nReason briefly from the state, then end with: ANSWER: <integer>"

    server = LlamaServer(str(ROOT / m["server_exe"]), str(ROOT / m["model_path"]),
                         ctx=m["ctx"], port=m["port"] + 6,
                         threads=args.threads or m["threads"],
                         n_gpu_layers=args.ngl if args.ngl is not None else m.get("n_gpu_layers", 0))
    server.ensure_running()
    draws, n_correct = [], 0
    for seed, temp in DRAWS:
        resp = server.chat(CLOSING_SYSTEM, user, max_tokens=500, temperature=temp, seed=seed)
        txt = resp["text"]
        m = re.search(r"ANSWER:\s*(-?\d[\d,]*)", txt)
        ans = int(m.group(1).replace(",", "")) if m else None
        ok = ans == gt
        n_correct += ok
        draws.append({"seed": seed, "temp": temp, "answer": ans, "correct": ok,
                      "wall_s": resp["wall_s"], "text": txt})
        print(f"  seed={seed} t={temp} -> ANSWER={ans} correct={ok} ({resp['wall_s']}s)", flush=True)
    server.stop()

    verdict = ("PASS (floor CAN compose -> battery interpretable)" if n_correct
               else "FAIL (floor cannot compose -> battery predicted floor-limited-null; carry to E2')")
    out = {"gate": "compose_positive_control", "model": mkey, "ground_truth": gt,
           "n_correct": n_correct, "n_draws": len(DRAWS), "verdict": verdict,
           "state_used": state, "draws": draws}
    (HERE / f"compose_gate_result_{mkey}.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nGATE 3 {verdict}: {n_correct}/{len(DRAWS)} produced {gt}")


if __name__ == "__main__":
    main()
