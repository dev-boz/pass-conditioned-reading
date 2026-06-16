"""P4 pre-run validation (no model calls). Verifies: schedule covers all 390
turns verbatim; the F7 single-occurrence turn gets a sigma=0 read; every
normalized matcher fires on the source; and emits the predicted-recoverable-pass
table (slice-coverage and view-presence). Run before committing model time.

Usage: uv run python experiments/p4_planted_facts/dryrun.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pca.planted import (  # noqa: E402
    build_schedule, fact_turn_indices, load_manifest, load_turns,
    match_components, normalize,
)

cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
data = (HERE / cfg["data_dir"]).resolve()
turns = load_turns(data / "conversation.jsonl")
manifest = load_manifest(data / "planted_facts.json")
N = sum(t["tokens"] for t in turns)
print(f"turns={len(turns)}  total_tokens={N}")

passes = build_schedule(turns, cfg["schedule"]["V"], cfg["schedule"]["R"],
                        tuple(cfg["schedule"]["stage_fracs"]))
K = len(passes)
phaseA = [p for p in passes if p["phase"] == "A"]
phaseB = [p for p in passes if p["phase"] == "B"]
print(f"K={K}  (PhaseA={len(phaseA)} ramp, PhaseB={len(phaseB)} verbatim tiles)  V={cfg['schedule']['V']}")
print("PhaseA compression ratios:", [p["compression_ratio"] for p in phaseA])
print("PhaseB view_tokens range:", min(p["view_tokens"] for p in phaseB), "-",
      max(p["view_tokens"] for p in phaseB))

# coverage: every turn in some verbatim tile?
covered = set().union(*[p["turn_idx"] for p in phaseB])
print(f"verbatim coverage: {len(covered)}/{len(turns)} turns  ->", "COMPLETE" if len(covered) == len(turns) else "INCOMPLETE")

fidx = fact_turn_indices(manifest, turns)
f7_turn_idx = next(i for i, t in enumerate(turns) if t["turn"] == 153)
f7_tile = next(p["k"] for p in phaseB if f7_turn_idx in p["turn_idx"])
print(f"F7 (turn 153) first verbatim read at pass k={f7_tile} (stage {passes[f7_tile-1]['stage']})")

# matcher-fires-on-source assertion
src = "\n".join(t["text"] for t in turns)
print("\n-- matcher validation on source --")
for fid, spec in cfg["facts_scoring"].items():
    hits = match_components(src, spec["components"])
    miss = [c for c, h in hits.items() if not h]
    assert not miss, f"{fid} components do not fire on source: {miss}"
    print(f"  {fid}: all {len(hits)} components fire OK  required={spec['required']}")

# predicted-recoverable-pass table
print("\n-- predicted recoverable pass (slice-coverage / view-presence) --")
print(f"{'fact':4} {'tier':22} {'slice':>5} {'view':>5}  label")
for f in manifest["facts"]:
    fid = f["id"]
    sl = next((p["k"] for p in passes if p["turn_idx"] & fidx[fid]), None)
    req = cfg["facts_scoring"][fid]["components"]
    reqd = cfg["facts_scoring"][fid]["required"]
    vp = next((p["k"] for p in passes
               if all(match_components(p["view_text"], req)[n] for n in reqd)), None)
    print(f"{fid:4} {f['tier']:22} {str(sl):>5} {str(vp):>5}  {f['label']}")

print(f"\ntier3 link: F4 '8,000 units' first_turn 25, F8 \"Founders' Edition\" first_turn 292 "
      f"(sep {manifest['tier3_link']['separation_turns']} turns)")
print("dryrun OK")
