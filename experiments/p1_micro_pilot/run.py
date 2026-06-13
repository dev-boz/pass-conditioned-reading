"""P1 — prompt-level micro-pilot: coupled vs input-staged-only vs output-staged-only.

Usage: uv run python experiments/p1_micro_pilot/run.py [--arms coupled,...]
Re-runnable from schedules.yaml alone; idempotent per arm (skips arms whose
transcript already exists; delete a transcript to re-run that arm).
Outputs per arm: transcripts/<arm>.md, transcripts/<arm>_states.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pca.editops import IntegrationState, parse_ops  # noqa: E402
from pca.llm import LlamaServer  # noqa: E402
from pca.schedule import generate_views  # noqa: E402
from pca.textutils import n_tokens  # noqa: E402


def load_doc(doc_id: str) -> dict:
    for line in (ROOT / "data" / "corpus" / "corpus.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        if d["doc_id"] == doc_id:
            return d
    raise KeyError(doc_id)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", default=None, help="comma-separated subset of arms")
    args = ap.parse_args()

    cfg_path = HERE / "schedules.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg_hash = hashlib.sha256(cfg_path.read_bytes()).hexdigest()[:16]
    K, V, seed = cfg["K"], cfg["V"], cfg["seed"]
    doc = load_doc(cfg["doc_id"])

    # staged views from the SAME production pipeline as E0 (extractive stand-in)
    from pca.compressor import get_compressor

    staged_views = generate_views(doc["doc_id"], doc["text"], K, V, get_compressor("extractive"))

    prompts = {p.stem: p.read_text(encoding="utf-8") for p in (HERE / "prompts").glob("*.txt")}
    fmt = dict(scaffold_B_s=cfg["budgets"]["scaffold_B_s"], state_tokens=cfg["budgets"]["state_tokens"])

    m = cfg["model"]
    server = LlamaServer(str((HERE / m["server_exe"]).resolve()), str((HERE / m["model_path"]).resolve()),
                         ctx=m["ctx"], port=m["port"], threads=m["threads"])
    server.ensure_running()

    arms = list(cfg["arms"]) if not args.arms else args.arms.split(",")
    for arm in arms:
        spec = cfg["arms"][arm]
        out_md = HERE / "transcripts" / f"{arm}.md"
        if out_md.exists():
            print(f"[{arm}] transcript exists — skipping (delete to re-run)")
            continue
        state = IntegrationState()
        snapshots = [state.snapshot()]
        lines = [
            f"# P1 transcript — arm: **{arm}**",
            "",
            f"- doc: `{cfg['doc_id']}` ({doc['n_tokens']} tokens) · K={K} · V={V}",
            f"- model: Qwen2.5-7B-Instruct Q4_K_M via llama.cpp CPU · temp={m['temperature']} · seed={seed}",
            f"- views: {spec['views']} · demands: {spec['demands']} · config `{cfg_hash}` · {date.today()}",
            "",
        ]
        for k in range(1, K + 1):
            stage = cfg["stages_by_pass"][k - 1] if spec["demands"] == "staged" else "full_detail"
            demand = prompts[f"demand_{stage}"].format(**fmt).strip()
            if spec["views"] == "staged":
                vrec = staged_views[k - 1]
                view, vstat = vrec["view_text"], (
                    f"slice {vrec['slice_tokens']} tok → view {vrec['view_tokens']} tok "
                    f"(ratio {vrec['compression_ratio']}×)")
            else:
                view, vstat = doc["text"], f"full document verbatim ({doc['n_tokens']} tok, ratio 1×)"
            user = prompts["user_template"].format(
                task=cfg["task"].strip(), k=k, K=K, state=state.render(), view=view, demand=demand)
            print(f"[{arm}] pass {k}/{K} ({stage}) — prompting ({n_tokens(user)} tok)...", flush=True)
            resp = server.chat(prompts["system"], user, max_tokens=m["max_tokens"],
                               temperature=m["temperature"], seed=seed)
            parsed = parse_ops(resp["text"], state.ids(), state.next_id)
            ops = parsed.ops[: cfg["budgets"]["max_ops_per_pass"]]
            applied = state.apply(ops)
            st_tok = n_tokens(state.render())
            warn = " [over state budget]" if st_tok > cfg["budgets"]["state_tokens"] else ""
            print(f"    ops {parsed.valid}/{parsed.candidate_lines} valid, {applied} applied; "
                  f"state {st_tok} tok{warn} ({resp['wall_s']}s)", flush=True)
            lines += [
                f"## Pass {k}/{K} — demand: `{stage}`",
                "",
                f"**View:** {vstat} · **gen wall-clock:** {resp['wall_s']}s · "
                f"**usage:** {resp['usage'].get('prompt_tokens', '?')}+{resp['usage'].get('completion_tokens', '?')} tok",
                "",
                "<details><summary>Prompt (user message)</summary>",
                "", "```text", user, "```", "</details>", "",
                "### Raw model output", "", "```text", resp["text"].strip(), "```", "",
                f"### Parsed edit ops — {parsed.valid}/{parsed.candidate_lines} valid "
                f"(validity {parsed.validity_rate:.2f}), {applied} applied"
                + (f", {len(parsed.ops) - len(ops)} dropped over op budget" if len(parsed.ops) > len(ops) else ""),
                "",
                "```json", json.dumps(ops, indent=1), "```", "",
            ]
            if parsed.invalid:
                lines += ["**Invalid op lines:**", "", "```text", "\n".join(parsed.invalid), "```", ""]
            lines += [f"### State after pass ({st_tok} tok{warn})", "", "```text", state.render(), "```", ""]
            snapshots.append(state.snapshot())
        out_md.write_text("\n".join(lines), encoding="utf-8")
        (HERE / "transcripts" / f"{arm}_states.json").write_text(
            json.dumps({"doc_id": cfg["doc_id"], "K": K, "config_hash": cfg_hash,
                        "snapshots": snapshots}, indent=1), encoding="utf-8")
        print(f"[{arm}] transcript -> {out_md}")
    print("P1 done.")


if __name__ == "__main__":
    main()
