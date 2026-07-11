"""Rebuild the rendered training rows deterministically from the persisted trajectories.

Needed after purging bad trajectories (the row file is append-mode during generation, so
purges must rebuild it). Row content is fully derivable: each pass stores system/user/
raw_output, the closing stores its prompt + raw output.

  python experiments/e2prime/rebuild_rows.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from pca.teacher_gen import CLOSING_SYSTEM  # noqa: E402

TRAJ = ROOT / "data" / "e2prime" / "trajectories"
OUT = ROOT / "data" / "e2prime" / "stageA_coupled.jsonl"


def main() -> None:
    n_rows = 0
    with OUT.open("w", encoding="utf-8") as f:
        for tf in sorted(TRAJ.glob("*.json")):
            rec = json.loads(tf.read_text(encoding="utf-8"))
            K = rec["K"]
            for p in rec["passes"]:
                assert p["raw_output"].strip(), f"{tf.stem} k={p['k']}: empty pass survived purge"
                f.write(json.dumps({
                    "doc_id": rec["doc_id"], "k": p["k"], "K": K, "stage": p["stage"],
                    "gen_path": p.get("gen_path"),
                    "prompt": [{"role": "system", "content": p["system"]},
                               {"role": "user", "content": p["user"]}],
                    "completion": [{"role": "assistant", "content": p["raw_output"]}],
                }, ensure_ascii=False) + "\n")
                n_rows += 1
            c = rec["closing"]
            assert c["raw_output"].strip(), f"{tf.stem}: empty closing survived purge"
            f.write(json.dumps({
                "doc_id": rec["doc_id"], "k": K + 1, "K": K, "stage": "closing",
                "gen_path": c.get("gen_path"),
                "prompt": [{"role": "system", "content": CLOSING_SYSTEM},
                           {"role": "user", "content": c["user"]}],
                "completion": [{"role": "assistant", "content": c["raw_output"]}],
            }, ensure_ascii=False) + "\n")
            n_rows += 1
    print(f"rebuilt {n_rows} rows from {len(list(TRAJ.glob('*.json')))} trajectories -> {OUT}")


if __name__ == "__main__":
    main()
