"""P4 scoring — model-free. Reads coupled_run.json + dense_run.json + manifest +
config, rebuilds the (deterministic) schedule for coverage-timing, and writes
metrics.json. Every mean states its formula (D24).

Usage: uv run python experiments/p4_planted_facts/score.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pca.planted import (  # noqa: E402
    build_schedule, fact_turn_indices, load_manifest, load_turns, match_components,
)

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
cfg_hash = hashlib.sha256((HERE / "config.yaml").read_bytes()).hexdigest()[:16]
data = (HERE / cfg["data_dir"]).resolve()
turns = load_turns(data / "conversation.jsonl")
manifest = load_manifest(data / "planted_facts.json")
fidx = fact_turn_indices(manifest, turns)
sch = build_schedule(turns, cfg["schedule"]["V"], cfg["schedule"]["R"], tuple(cfg["schedule"]["stage_fracs"]))
spec = cfg["facts_scoring"]
FACTS = [f["id"] for f in manifest["facts"]]
N_TURNS = len(turns)


def required_present(text, fid):
    hits = match_components(text, spec[fid]["components"])
    return all(hits[n] for n in spec[fid]["required"]), hits


def source_position(fid):
    first = min(fidx[fid])
    t = first / (N_TURNS - 1)
    return "early" if t < 1 / 3 else "mid" if t < 2 / 3 else "late"


def score_state(text):
    """Per-fact full-credit presence + component hits, for one final-state text."""
    out = {}
    for fid in FACTS:
        present, hits = required_present(text, fid)
        out[fid] = {"present": present, "components": hits}
    return out


coupled = json.loads((HERE / "coupled_run.json").read_text(encoding="utf-8"))
result = {"config_hash": cfg_hash, "source_tokens": sum(t["tokens"] for t in turns),
          "K": coupled["K"], "n_facts": len(FACTS),
          "mean_formulas": {
              "headline_fact_recall": "count(facts full-credit present in FINAL state) / 8",
              "by_tier": "same, partitioned by manifest tier",
              "by_source_position": "same, partitioned by tercile of the fact's first-occurrence turn"},
          "arms": {}}

# ---------- coupled: recall + coverage-timing + survival ----------
final = coupled["final_state"]
fs = score_state(final)
snaps = coupled["snapshots"]   # per-pass list of entries


def state_text_at(pass_i):
    return "\n".join(f"{e['id']}: {e['text']}" for e in snaps[pass_i])


timing = {}
for fid in FACTS:
    slice_pass = next((p["k"] for p in sch if p["turn_idx"] & fidx[fid]), None)
    view_pass = next((p["k"] for p in sch
                      if all(match_components(p["view_text"], spec[fid]["components"])[n]
                             for n in spec[fid]["required"])), None)
    entry_pass = next((i + 1 for i in range(len(snaps))
                       if required_present(state_text_at(i), fid)[0]), None)
    present_final = fs[fid]["present"]
    evicted = (entry_pass is not None) and (not present_final)
    timing[fid] = {"tier": next(f["tier"] for f in manifest["facts"] if f["id"] == fid),
                   "source_position": source_position(fid),
                   "slice_coverage_pass": slice_pass, "view_presence_pass": view_pass,
                   "state_entry_pass": entry_pass, "present_at_final": present_final, "evicted": evicted}

recall = sum(fs[f]["present"] for f in FACTS) / len(FACTS)
by_tier, by_pos = {}, {}
for f in manifest["facts"]:
    by_tier.setdefault(f["tier"], []).append(fs[f["id"]]["present"])
    by_pos.setdefault(source_position(f["id"]), []).append(fs[f["id"]]["present"])

# alias misplacement audit: passes with aliased ops, and whether any fact was evicted that pass
alias_passes = [p["k"] for p in coupled["passes"] if p["aliased"] > 0]
alias_flag = []
for fid in FACTS:
    ep = timing[fid]["state_entry_pass"]
    if timing[fid]["evicted"] and ep is not None:
        # find pass where it left
        left = next((i + 1 for i in range(ep, len(snaps)) if not required_present(state_text_at(i), fid)[0]), None)
        if left in alias_passes:
            alias_flag.append({"fact": fid, "evicted_at_pass": left, "aliased_ops_that_pass": True})

result["arms"]["coupled"] = {
    "headline_fact_recall": recall,
    "facts_present": {f: fs[f]["present"] for f in FACTS},
    "by_tier": {k: sum(v) / len(v) for k, v in by_tier.items()},
    "by_source_position": {k: sum(v) / len(v) for k, v in by_pos.items()},
    "coverage_timing": timing,
    "f4_f8_co_present_at_final": fs["F4"]["present"] and fs["F8"]["present"],
    "component_detail_F4": fs["F4"]["components"], "component_detail_F7": fs["F7"]["components"],
    "total_tokens_processed": sum(p["prompt_tokens"] for p in coupled["passes"]),
    "wall_clock_min": round(sum(p["wall_s"] for p in coupled["passes"]) / 60, 1),
    "alias_misplacement_flags": alias_flag or "none",
}

# ---------- dense: raw + within-reach recall ----------
dense_path = HERE / "dense_run.json"
if dense_path.exists():
    dense = json.loads(dense_path.read_text(encoding="utf-8"))
    ds = score_state(dense["answer"])
    reach = set(dense["head_turn_idx"]) | set(dense["tail_turn_idx"])
    within = {f: bool(fidx[f] & reach) for f in FACTS}
    raw = sum(ds[f]["present"] for f in FACTS) / len(FACTS)
    reachable = [f for f in FACTS if within[f]]
    wr = (sum(ds[f]["present"] for f in reachable) / len(reachable)) if reachable else None
    result["arms"]["dense"] = {
        "raw_fact_recall": raw,
        "within_reach_recall": wr, "n_within_reach": len(reachable),
        "facts_present": {f: ds[f]["present"] for f in FACTS},
        "facts_within_reach": within,
        "total_tokens_processed": dense["prompt_tokens"],
        "wall_clock_min": round(dense["wall_s"] / 60, 1),
    }
    # ---------- kill condition ----------
    verdict = ("COUPLED WINS" if recall > raw else
               "FAIL — coupled <= dense (evidence against M1 premise)")
    result["kill_condition"] = {"rule": cfg["gate"]["rule"].strip(),
                                "coupled_recall": recall, "dense_raw_recall": raw,
                                "verdict": verdict, "provisional": cfg["gate"]["provisional"]}

(HERE / "metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"coupled headline recall = {recall:.3f} ({sum(fs[f]['present'] for f in FACTS)}/8)")
print("by tier:", {k: round(v, 2) for k, v in result['arms']['coupled']['by_tier'].items()})
print("by position:", {k: round(v, 2) for k, v in result['arms']['coupled']['by_source_position'].items()})
if dense_path.exists():
    print(f"dense raw recall = {result['arms']['dense']['raw_fact_recall']:.3f} "
          f"within-reach = {result['arms']['dense']['within_reach_recall']}")
    print("KILL:", result["kill_condition"]["verdict"])
print(f"config_hash = {cfg_hash}  -> metrics.json")
