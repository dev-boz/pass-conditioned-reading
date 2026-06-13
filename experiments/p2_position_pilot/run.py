"""P2 — position-token pilot: identical eval items run with a structured
position field vs no position information; measures edit-op validity and a
position-appropriateness heuristic.

Usage: uv run python experiments/p2_position_pilot/run.py
Requires the P1 coupled arm to have run (provides s_{k-1} snapshots).
Outputs: metrics.json, items.jsonl (raw outputs per item x condition).
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

from pca.compressor import get_compressor  # noqa: E402
from pca.editops import IntegrationState, parse_ops  # noqa: E402
from pca.llm import LlamaServer  # noqa: E402
from pca.schedule import generate_views  # noqa: E402

SYSTEM = """You are the integration model inside a multi-pass reading architecture. You build a single INTEGRATION STATE that fulfils a task about a long source document seen through partial views.

You receive: the task, the current integration state (numbered entries S1, S2, ...), and one view of the source. Emit the edit operations that best advance the state toward fulfilling the task, appropriate to where this pass sits in the reading process.

Respond ONLY with edit operations, one per line, exactly:

ADD END: <text>
ADD S3: <text>
REPLACE S3: <text>
REMOVE S3
NO_CHANGE

Rules: max 12 operations; single-line <text>; refer only to existing entry ids; no commentary, no fences."""

USER_TMPL = """TASK: {task}
{position_line}
CURRENT INTEGRATION STATE:
{state}

VIEW OF THE SOURCE (this pass):
{view}

Respond with edit operations only."""


def op_fracs(ops: list[dict]) -> dict:
    n = max(len(ops), 1)
    return {
        "add": sum(o["op"] == "ADD" for o in ops) / n,
        "replace": sum(o["op"] == "REPLACE" for o in ops) / n,
        "remove": sum(o["op"] == "REMOVE" for o in ops) / n,
        "no_change": sum(o["op"] == "NO_CHANGE" for o in ops) / n,
        "n_ops": len(ops),
    }


def main() -> None:
    cfg_path = HERE / "config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg_hash = hashlib.sha256(cfg_path.read_bytes()).hexdigest()[:16]
    seed = cfg["seed"]

    states_path = (HERE / cfg["states_file"]).resolve()
    if not states_path.exists():
        sys.exit("P1 coupled arm has not run yet (coupled_states.json missing). Run make p1 first.")
    sdata = json.loads(states_path.read_text(encoding="utf-8"))
    K, doc_id = sdata["K"], sdata["doc_id"]

    p1cfg = yaml.safe_load((HERE / cfg["p1_dir"] / "schedules.yaml").read_text(encoding="utf-8"))
    task = p1cfg["task"].strip()
    doc = next(json.loads(l) for l in (ROOT / "data" / "corpus" / "corpus.jsonl").open(encoding="utf-8")
               if json.loads(l)["doc_id"] == doc_id)
    views = generate_views(doc_id, doc["text"], K, p1cfg["V"], get_compressor("extractive"))

    m = cfg["model"]
    server = LlamaServer(str((HERE / m["server_exe"]).resolve()), str((HERE / m["model_path"]).resolve()),
                         ctx=m["ctx"], port=m["port"], threads=m["threads"])
    server.ensure_running()

    items, per_cond = [], {"with_position": [], "no_position": []}
    for k in range(1, K + 1):
        state = IntegrationState.from_snapshot(sdata["snapshots"][k - 1])  # s_{k-1}
        view = views[k - 1]["view_text"]
        for cond in ("with_position", "no_position"):
            if not cfg["conditions"][cond]:
                continue
            pos = f"\nposition: {{k: {k}, K: {K}}}\n" if cond == "with_position" else "\n"
            user = USER_TMPL.format(task=task, position_line=pos, state=state.render(), view=view)
            print(f"k={k} [{cond}] prompting...", flush=True)
            resp = server.chat(SYSTEM, user, max_tokens=m["max_tokens"],
                               temperature=m["temperature"], seed=seed)
            parsed = parse_ops(resp["text"], state.ids(), state.next_id)
            rec = {"k": k, "K": K, "condition": cond,
                   "validity_rate": parsed.validity_rate,
                   "n_candidate_lines": parsed.candidate_lines, "n_valid": parsed.valid,
                   "op_fracs": op_fracs(parsed.ops),
                   "raw_output": resp["text"], "wall_s": resp["wall_s"]}
            items.append(rec)
            per_cond[cond].append(rec)
            print(f"    validity {parsed.valid}/{parsed.candidate_lines} "
                  f"fracs={ {a: round(b, 2) for a, b in rec['op_fracs'].items()} }", flush=True)

    # ---- aggregate
    ap = cfg["appropriateness"]

    def t_of(k: int) -> float:
        return (k - 1) / (K - 1)

    def appropriate(rec: dict) -> bool | None:
        t, f = t_of(rec["k"]), rec["op_fracs"]
        if t < ap["early_max_t"]:
            return f["add"] >= ap["early_add_frac_min"]
        if t >= ap["late_min_t"]:
            return (f["replace"] + f["remove"]) >= ap["late_edit_frac_min"]
        return None  # mid passes excluded from headline (D20)

    summary = {"config_hash": cfg_hash, "doc_id": doc_id, "K": K, "conditions": {}}
    for cond, recs in per_cond.items():
        if not recs:
            continue
        apps = [appropriate(r) for r in recs]
        scored = [a for a in apps if a is not None]
        summary["conditions"][cond] = {
            "n_items": len(recs),
            "mean_validity_rate": sum(r["validity_rate"] for r in recs) / len(recs),
            "appropriateness_rate": (sum(scored) / len(scored)) if scored else None,
            "n_appropriateness_scored": len(scored),
            "op_fracs_by_k": {r["k"]: {a: round(b, 3) for a, b in r["op_fracs"].items()} for r in recs},
        }
    (HERE / "items.jsonl").write_text(
        "\n".join(json.dumps(i, ensure_ascii=False) for i in items), encoding="utf-8")
    (HERE / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    for cond, s in summary["conditions"].items():
        print(f"{cond}: validity={s['mean_validity_rate']:.3f} "
              f"appropriateness={s['appropriateness_rate']}")
    print(f"config_hash = {cfg_hash}")


if __name__ == "__main__":
    main()
