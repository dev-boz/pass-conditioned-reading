"""P3 — prompt-rubric pilot: (a) position field only / (b) + per-pass rubric /
(c) + confidence line. Identical items across arms (P1 doc, coupled reference
states, staged views); only the prompt manipulation varies.

Usage: uv run python experiments/p3_prompt_rubric/run.py
Outputs: metrics.json, items.jsonl. Means are reported BOTH ways (D24):
micro = sum(valid)/sum(candidate lines); macro = mean of per-item rates.
"""

from __future__ import annotations

import hashlib
import json
import re
import statistics
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

You receive: the task, your schedule position, the current integration state (numbered entries S1, S2, ...), and one view of the source. Emit the edit operations that best advance the state toward fulfilling the task, appropriate to where this pass sits in the reading process.

Respond ONLY with edit operations, one per line, exactly:

ADD END: <text>
ADD S3: <text>
REPLACE S3: <text>
REMOVE S3
NO_CHANGE

Rules: max 12 operations; single-line <text>; refer only to existing entry ids; no commentary, no fences."""

USER_TMPL = """TASK: {task}

position: {{k: {k}, K: {K}}}

CURRENT INTEGRATION STATE:
{state}

VIEW OF THE SOURCE (this pass):
{view}
{extras}
Respond with edit operations only."""

_CONF_RE = re.compile(r"(?im)^\s*confidence:\s*([01](?:\.\d+)?)\s*$")


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
        sys.exit("P1 coupled arm (parser v2) has not run yet. Run make p1 first.")
    sdata = json.loads(states_path.read_text(encoding="utf-8"))
    K, doc_id = sdata["K"], sdata["doc_id"]

    p1cfg = yaml.safe_load((HERE / cfg["p1_dir"] / "schedules.yaml").read_text(encoding="utf-8"))
    task = p1cfg["task"].strip()
    stages = p1cfg["stages_by_pass"]
    doc = next(json.loads(l) for l in (ROOT / "data" / "corpus" / "corpus.jsonl").open(encoding="utf-8")
               if json.loads(l)["doc_id"] == doc_id)
    views = generate_views(doc_id, doc["text"], K, p1cfg["V"], get_compressor("extractive"))

    m = cfg["model"]
    server = LlamaServer(str((HERE / m["server_exe"]).resolve()), str((HERE / m["model_path"]).resolve()),
                         ctx=m["ctx"], port=m["port"], threads=m["threads"])
    server.ensure_running()

    items: list[dict] = []
    for arm, spec in cfg["arms"].items():
        for k in range(1, K + 1):
            state = IntegrationState.from_snapshot(sdata["snapshots"][k - 1])  # s_{k-1}
            extras = ""
            if spec["rubric"]:
                extras += "\n" + cfg["rubrics"][stages[k - 1]].strip() + "\n"
            if spec["confidence"]:
                extras += "\n" + cfg["confidence_instruction"].strip() + "\n"
            user = USER_TMPL.format(task=task, k=k, K=K, state=state.render(),
                                    view=views[k - 1]["view_text"], extras=extras)
            print(f"[{arm}] k={k} prompting...", flush=True)
            resp = server.chat(SYSTEM, user, max_tokens=m["max_tokens"],
                               temperature=m["temperature"], seed=seed)
            parsed = parse_ops(resp["text"], state.ids(), state.next_id)
            conf = None
            if spec["confidence"]:
                cm = _CONF_RE.findall(resp["text"])
                conf = float(cm[-1]) if cm else None
            rec = {"arm": arm, "k": k, "K": K,
                   "n_valid": parsed.valid, "n_candidate_lines": parsed.candidate_lines,
                   "validity_rate": parsed.validity_rate,
                   "op_fracs": op_fracs(parsed.ops), "confidence": conf,
                   "raw_output": resp["text"], "wall_s": resp["wall_s"]}
            items.append(rec)
            print(f"    valid {parsed.valid}/{parsed.candidate_lines}"
                  + (f" conf={conf}" if conf is not None else ""), flush=True)

    # ---- aggregate
    ap = cfg["appropriateness"]

    def appropriate(rec: dict) -> bool | None:
        t, f = (rec["k"] - 1) / (K - 1), rec["op_fracs"]
        if t < ap["early_max_t"]:
            return f["add"] >= ap["early_add_frac_min"]
        if t >= ap["late_min_t"]:
            return (f["replace"] + f["remove"]) >= ap["late_edit_frac_min"]
        return None

    summary = {"config_hash": cfg_hash, "doc_id": doc_id, "K": K,
               "mean_formulas": {
                   "micro_validity": "sum(n_valid) / sum(n_candidate_lines) over the arm's 6 items",
                   "macro_validity": "mean over the arm's 6 items of (n_valid / n_candidate_lines), 0-candidate items counted as rate 0",
                   "appropriateness": "fraction of scored items passing D20 (early: ADD frac >= 0.5; late: REPLACE+REMOVE frac >= 0.3; mid excluded)"},
               "arms": {}}
    for arm in cfg["arms"]:
        recs = [r for r in items if r["arm"] == arm]
        scored = [a for a in (appropriate(r) for r in recs) if a is not None]
        out = {
            "n_items": len(recs),
            "micro_validity": sum(r["n_valid"] for r in recs) / max(sum(r["n_candidate_lines"] for r in recs), 1),
            "macro_validity": statistics.mean(r["validity_rate"] for r in recs),
            "appropriateness_rate": sum(scored) / len(scored) if scored else None,
            "n_appropriateness_scored": len(scored),
            "op_fracs_by_k": {r["k"]: {a: round(b, 3) for a, b in r["op_fracs"].items()} for r in recs},
            "validity_by_k": {r["k"]: f"{r['n_valid']}/{r['n_candidate_lines']}" for r in recs},
        }
        if cfg["arms"][arm]["confidence"]:
            pairs = [(r["confidence"], r["validity_rate"]) for r in recs if r["confidence"] is not None]
            out["confidence_by_k"] = {r["k"]: r["confidence"] for r in recs}
            out["n_confidence_emitted"] = len(pairs)
            try:
                out["confidence_validity_pearson_r"] = (
                    statistics.correlation([p[0] for p in pairs], [p[1] for p in pairs])
                    if len(pairs) >= 3 else None)
            except statistics.StatisticsError:
                out["confidence_validity_pearson_r"] = None  # constant input
        summary["arms"][arm] = out
        print(f"{arm}: micro={out['micro_validity']:.3f} macro={out['macro_validity']:.3f} "
              f"approp={out['appropriateness_rate']}")
    (HERE / "items.jsonl").write_text(
        "\n".join(json.dumps(i, ensure_ascii=False) for i in items), encoding="utf-8")
    (HERE / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"config_hash = {cfg_hash}")


if __name__ == "__main__":
    main()
