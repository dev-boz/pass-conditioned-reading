"""E2′ teacher-trajectory generation + training-row rendering (Stage A: coupled/explicit).

The teacher (Claude Haiku 4.5 via `claude -p`, D29/D30 lineage) executes the coupled
schedule over a corpus document, maintaining the integration state through the v3
edit-op harness (guard per config; E2′ = strict). Every pass becomes one training row
{doc_id, prompt: [system,user], completion: [assistant]} with the teacher's RAW text as
the completion (the student distills exactly what the teacher emitted, quotes included),
plus one closing row per document. Trajectories carry full provenance (config hash,
prompts, per-op apply outcomes) and generation is resumable per doc.

Forcing boundary (E2PRIME-CRITERION §2): prompts below state the op grammar, the per-pass
behavioral rubric (P3 lineage), a need-class, and a general structural objective. Nothing
may name a probe, a target structure, an identifier, or a value. Run scan_leakage.py over
the corpus BEFORE generation (P-B ordering: RELEVANCE-CONTROL-V2 must also have run).

  python -m pca.teacher_gen --config experiments/e2prime/teacher_config.yaml [--limit N]
  python -m pca.teacher_gen --config ... --audit 20     # teacher-quality gate, no rendering
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

from .editops import IntegrationState, parse_ops
from .llm import ClaudePClient, KiroClient
from .planted import build_schedule
from .textutils import n_tokens


class FallbackClient:
    """Ordered delivery paths of the SAME teacher model (D30 precedent): kiro-cli first
    (maintainer directive 2026-07-10 — spare kiro quota), `claude -p` fallback. A path
    'fails' on exception or empty text; provenance carries whichever path answered."""

    def __init__(self, clients: list):
        self.clients = clients

    def chat(self, system: str, user: str, max_tokens: int = 700, **kw) -> dict:
        errs = []
        for c in self.clients:
            try:
                r = c.chat(system, user, max_tokens=max_tokens, **kw)
            except Exception as e:  # path down → try the next one
                errs.append(f"{type(c).__name__}:{e}")
                continue
            if (r.get("text") or "").strip():
                return r
            errs.append(f"{type(c).__name__}:empty")
        # 2026-07-11 hardening (mass-gen run #1: 772 empty passes rendered silently when
        # kiro quota died and claude -p hit its window): ALL paths failing is a hard error.
        # An empty teacher output must never become a training row; resumability retries.
        raise RuntimeError("all teacher delivery paths failed: " + " | ".join(errs)[:300])


def make_teacher_client(cfg: dict):
    order = cfg["teacher"].get("backends", ["claude_p"])
    built = []
    for name in order:
        if name == "kiro":
            k = cfg["teacher"]["kiro"]
            built.append(KiroClient(kiro_model=k["model"], agent=k.get("agent"),
                                    effort=k.get("effort")))
        elif name == "claude_p":
            built.append(ClaudePClient(model=cfg["teacher"]["claude_p"]["model"],
                                       timeout=cfg["teacher"]["timeout_s"]))
        else:
            raise ValueError(f"unknown teacher backend: {name}")
    return built[0] if len(built) == 1 else FallbackClient(built)

GRAMMAR = """You maintain a bounded integration state via edit operations, one per line:

    ADD END: <text>                          append a new entry
    ADD <id>: <text>                         insert a new entry AFTER entry <id>
    REPLACE <id> "<quote>": <text>           replace entry <id>'s text
    REMOVE <id> "<quote>"                    delete entry <id>
    NO_CHANGE                                this pass contributes nothing

The <quote> is REQUIRED on REPLACE and REMOVE: ONE short fragment (roughly 5-15 words),
copied EXACTLY from the CURRENT text of the entry you are changing. It proves you are
editing the entry you think you are; an edit whose quote does not match its target is
refused by the harness. Do not paraphrase inside the quote."""

RUBRICS = {
    "scaffold": ("This is an early, heavily compressed pass. Expected ops: ADD new scaffold "
                 "entries naming the document's major units and how they relate. Do not chase "
                 "specifics yet."),
    "integrate": ("This is a mid-schedule pass. Expected ops: mostly REPLACE — integrate this "
                  "view's content into the entries it belongs to; consolidate overlapping "
                  "entries; keep the state within budget."),
    "verbatim": ("This is a late verbatim pass. Expected ops: REPLACE to surface exact values, "
                 "names and quotes into the entries they belong to; REMOVE only redundant "
                 "scaffolding. NO_CHANGE if this view adds nothing your state needs."),
}

CLOSING_SYSTEM = ("You are given only your final integration state from a multi-pass read. "
                  "The source document is not available.")


def _stage(k: int, K: int, fracs: tuple[float, float]) -> str:
    f = (k - 1) / max(K - 1, 1)
    return "scaffold" if f < fracs[0] else ("integrate" if f < fracs[1] else "verbatim")


def _system_prompt(cfg: dict, stage: str) -> str:
    t = cfg["task"]
    return (f"{GRAMMAR}\n\nObjective: {t['structural_objective']}\n\n"
            f"Context: {t['need_class']}\n\nThis pass: {RUBRICS[stage]}\n\n"
            f"State budget: stay under {cfg['harness']['state_budget_tok']} tokens; "
            f"consolidate rather than truncate. Output ONLY edit-op lines.")


def _user_prompt(k: int, K: int, state_text: str, view: str) -> str:
    return (f"position: {{k: {k}, K: {K}}}\n\nSTATE:\n{state_text}\n\n"
            f"VIEW (pass {k} of {K}):\n{view}")


def _code_passes(doc: dict, sc: dict) -> list[dict]:
    turns = [{"turn": i, "seg": i // 24 + 1, "text": b, "tokens": n_tokens(b)}
             for i, b in enumerate(doc["blocks"])]
    sch = build_schedule(turns, sc["V"], sc["R"], tuple(sc["stage_fracs"]))
    # Phase-A chunks get the frozen probe-blind code compressor; Phase-B tiles are verbatim.
    p7dir = Path(__file__).resolve().parents[2] / "experiments" / "p7_split_unit"
    sys.path.insert(0, str(p7dir))
    from compress_code import compress_code  # frozen v2 compressor (D32 freeze semantics)
    out = []
    for p in sch:
        view = compress_code(p["slice_text"], sc["V"]) if p["phase"] == "A" else p["slice_text"]
        out.append({"phase": p["phase"], "view": view})
    return out


def _prose_passes(doc: dict, sc: dict, repo_root: Path) -> list[dict]:
    views_path = repo_root / sc["views_jsonl"]
    if not views_path.exists():
        raise FileNotFoundError(
            f"prose views not pre-generated: {views_path} — run the D29 compressor pipeline "
            "(pca.gen_views_llm + pca.merge_paths) first; teacher_gen never compresses prose itself")
    views = {}
    for line in views_path.open(encoding="utf-8"):
        r = json.loads(line)
        if r["doc_id"] == doc["doc_id"]:
            views[r["k"]] = r["view_text"]
    K = sc["K"]
    missing = [k for k in range(1, K + 1) if k not in views]
    if missing:
        raise ValueError(f"{doc['doc_id']}: missing pre-generated views for k={missing}")
    return [{"phase": "-", "view": views[k]} for k in range(1, K + 1)]


def run_doc(doc: dict, cfg: dict, client, repo_root: Path) -> dict:
    kind = doc["kind"]
    sc = cfg["schedule"][kind]
    passes = _code_passes(doc, sc) if kind == "code" else _prose_passes(doc, sc, repo_root)
    K = len(passes)
    fracs = tuple(cfg["schedule"]["code"]["stage_fracs"]) if kind == "code" else (0.34, 0.67)
    st = IntegrationState(guard=cfg["harness"]["guard"])
    rows, record = [], {"doc_id": doc["doc_id"], "kind": kind, "K": K, "passes": [],
                        "provider": None}
    for i, p in enumerate(passes, start=1):
        stage = _stage(i, K, fracs)
        system = _system_prompt(cfg, stage)
        user = _user_prompt(i, K, st.render(), p["view"])
        resp = client.chat(system, user, max_tokens=900)
        record["provider"] = resp.get("provider")
        res = parse_ops(resp["text"], st.ids(), st.next_id)
        applied = st.apply(res.ops[: cfg["harness"]["op_cap"]])
        n_quoted = sum(1 for o in res.ops if o["op"] in ("REPLACE", "REMOVE") and "quote" in o)
        n_destr = sum(1 for o in res.ops if o["op"] in ("REPLACE", "REMOVE"))
        record["passes"].append({
            "k": i, "K": K, "phase": p["phase"], "stage": stage,
            "gen_path": resp.get("provider"),
            "raw_output": resp["text"], "system": system, "user": user,
            "valid": res.valid, "candidates": res.candidate_lines, "applied": applied,
            "quoted_destructive": n_quoted, "destructive": n_destr,
            "apply_report": st.last_report, "state_snapshot": st.snapshot(),
            "wall_s": resp.get("wall_s"),
        })
        rows.append({"doc_id": doc["doc_id"], "k": i, "K": K, "stage": stage,
                     "gen_path": resp.get("provider"),
                     "prompt": [{"role": "system", "content": system},
                                {"role": "user", "content": user}],
                     "completion": [{"role": "assistant", "content": resp["text"]}]})
    # closing row
    close_user = (f"FINAL STATE:\n{st.render()}\n\nTask: {cfg['task']['closing_demand']}")
    resp = client.chat(CLOSING_SYSTEM, close_user, max_tokens=1200)
    record["closing"] = {"raw_output": resp["text"], "user": close_user,
                         "gen_path": resp.get("provider")}
    rows.append({"doc_id": doc["doc_id"], "k": K + 1, "K": K, "stage": "closing",
                 "gen_path": resp.get("provider"),
                 "prompt": [{"role": "system", "content": CLOSING_SYSTEM},
                            {"role": "user", "content": close_user}],
                 "completion": [{"role": "assistant", "content": resp["text"]}]})
    return {"record": record, "rows": rows}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--limit", type=int, default=0, help="stop after N docs (0 = all)")
    ap.add_argument("--audit", type=int, default=0,
                    help="teacher-quality gate: run N docs, print the audit table, render nothing")
    ap.add_argument("--backends", default=None,
                    help="comma-separated delivery-path override (e.g. 'claude_p' when kiro "
                         "is quota-capped); same model either way, gen_path records the truth")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    if args.backends:
        cfg["teacher"]["backends"] = [b.strip() for b in args.backends.split(",")]
    cfg_hash = hashlib.sha256(cfg_path.read_bytes()).hexdigest()[:16]
    repo_root = Path(__file__).resolve().parents[2]
    corpus_path = repo_root / cfg["paths"]["corpus"]
    traj_dir = repo_root / cfg["paths"]["out_trajectories"]
    traj_dir.mkdir(parents=True, exist_ok=True)
    rendered_path = repo_root / cfg["paths"]["out_rendered"]

    client = make_teacher_client(cfg)
    docs = [json.loads(l) for l in corpus_path.open(encoding="utf-8") if l.strip()]
    if args.audit:
        # stratify the audit across document classes (doc_id prefix: govreport /
        # synthcode / realcode) — corpus order alone would audit only the first slice
        groups: dict[str, list[dict]] = {}
        for d in docs:
            groups.setdefault(d["doc_id"].split("-")[0], []).append(d)
        docs = [d for tup in zip(*groups.values()) for d in tup]
    n_cap = args.audit or args.limit or len(docs)

    audit_rows, done = [], 0
    for doc in docs:
        if done >= n_cap:
            break
        traj_file = traj_dir / f"{doc['doc_id']}.json"
        if traj_file.exists() and not args.audit:
            continue  # resumable
        try:
            out = run_doc(doc, cfg, client, repo_root)
        except RuntimeError as e:
            print(f"FAILED {doc['doc_id']}: {e}")
            continue  # no artifacts written; the resumable re-run picks it up
        out["record"]["config_hash"] = cfg_hash
        done += 1
        if args.audit:
            # persist audit trajectories separately — the prereg's hand-audit needs them
            audit_dir = traj_dir.parent / (traj_dir.name + "_audit")
            audit_dir.mkdir(parents=True, exist_ok=True)
            (audit_dir / f"{doc['doc_id']}.json").write_text(
                json.dumps(out["record"], indent=1, ensure_ascii=False), encoding="utf-8")
            ps = out["record"]["passes"]
            v = sum(p["valid"] for p in ps) / max(sum(p["candidates"] for p in ps), 1)
            q = sum(p["quoted_destructive"] for p in ps) / max(sum(p["destructive"] for p in ps), 1)
            blocked = sum(len(p["apply_report"]["blocked"]) for p in ps)
            audit_rows.append((doc["doc_id"], v, q, blocked))
            print(f"AUDIT {doc['doc_id']}: validity={v:.3f} quote_rate={q:.3f} blocked={blocked}")
            continue
        traj_file.write_text(json.dumps(out["record"], indent=1, ensure_ascii=False),
                             encoding="utf-8")
        with rendered_path.open("a", encoding="utf-8") as f:
            for row in out["rows"]:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"DONE {doc['doc_id']}: K={out['record']['K']} rows={len(out['rows'])}")

    if args.audit and audit_rows:
        mv = sum(r[1] for r in audit_rows) / len(audit_rows)
        mq = sum(r[2] for r in audit_rows) / len(audit_rows)
        print(f"\nTEACHER-QUALITY GATE over n={len(audit_rows)} docs: "
              f"mean validity={mv:.3f} (need >=0.95) mean quote_rate={mq:.3f} (need >=0.9); "
              f"hand-audit the trajectories before mass generation (prereg §3).")


if __name__ == "__main__":
    main()
