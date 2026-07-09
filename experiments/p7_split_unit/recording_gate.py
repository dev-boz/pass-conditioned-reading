"""P7 GATE 2 — the differential-recording discriminator (the advisor's pre-run gate; the reframe
hinges on it). Eviction is ~absent on this floor (P4 0/8; P6 1/~16), so P7 does NOT bet on
record-then-evict. It bets on DIFFERENTIAL RECORDING:

  coupled_full meets the arbitrary table as a clean structural artifact in the structure-preserving
  Phase-A view (and records it); verbatim_only meets the SAME table only as a raw int-wall embedded
  in a Phase-B code tile under a broad 'build a brief' rubric (and discards it as noise).

Cheap proxy (cold single pass, no accumulated state — the EASIEST case for recording, so a
non-recording here is conservative): run one integration pass on
  (a) the raw Phase-B tile that contains the table  (verbatim_only's exposure), and
  (b) the structure-preserving Phase-A view that contains the table  (coupled's exposure),
under the identical broad task + 'verbatim' rubric, and measure how much of the table lands in
state. Differential is ALIVE iff (b) records the table and (a) does not (or records far less).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
from pca.editops import IntegrationState, parse_ops  # noqa: E402
from pca.llm import LlamaServer                       # noqa: E402
from pca.planted import build_schedule, normalize     # noqa: E402
from pca.textutils import n_tokens                     # noqa: E402
from compress_code import compress_code               # noqa: E402

sys.path.insert(0, str(HERE))
from verify_fixture import load_turns, V, R, STAGE_FRACS  # noqa: E402

DRAWS = [(42, 0.0), (1, 0.7), (2, 0.7)]

TASK = ("You are building a single comprehensive analytical brief of a large codebase that you "
        "only ever see through partial views. Capture its structure and behaviour: the modules, "
        "the key data structures and constants, what the important functions compute, and any "
        "business rules the code encodes.")

SYSTEM = """You are the integration model inside a multi-pass reading architecture. Across K scheduled passes you build a single INTEGRATION STATE: a comprehensive analytical brief of a large codebase you only ever see through partial views.

Each pass you receive: the task, your schedule position, the current integration state (numbered entries S1, S2, ...), one view of the source, and an output demand for this pass.

Respond ONLY with edit operations, one per line, exactly:

ADD END: <text>
ADD S3: <text>
REPLACE S3: <text>
REMOVE S3
NO_CHANGE

Rules: refer to existing entry ids; single-line <text>; no commentary, no fences. Do NOT re-add an entry whose content is already present — REPLACE it to add detail instead."""

RUBRIC = ("RUBRIC: near-verbatim pass. Integrate precise specifics — exact constant values, "
          "lookup-table contents, function signatures, names, and the rules they encode. Prefer "
          "REPLACE of an existing entry; ADD only a genuinely new fact; NO_CHANGE if already captured.")

USER_TMPL = """TASK: {task}

position: {{k: {k}, K: {K}}}

{rubric}

CURRENT INTEGRATION STATE:
{state}

VIEW OF THE SOURCE (this pass):
{view}

Respond with edit operations only."""


def run_one(server, view, task, k, K, temp, seed):
    state = IntegrationState()
    user = USER_TMPL.format(task=task.strip(), k=k, K=K, rubric=RUBRIC,
                            state=state.render(), view=view)
    resp = server.chat(SYSTEM, user, max_tokens=900, temperature=temp, seed=seed)
    parsed = parse_ops(resp["text"], state.ids(), state.next_id)
    state.apply(parsed.ops)
    return state.render(), len(parsed.ops), resp["wall_s"]


def table_recorded(state_text: str, table: dict) -> dict:
    nt = normalize(state_text)
    hits = [k for k, v in table.items() if normalize(f"{k}: {v}") in nt or normalize(f"{k}:{v}") in nt]
    vals = [k for k, v in table.items() if normalize(str(v)) in nt]
    return {"entries_kv": len(hits), "values_present": len(vals), "queried_present":
            normalize(str(table["23"])) in nt}


def main():
    spec = json.loads((HERE / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    table = spec["table"]
    turns = load_turns(HERE / "fixture" / "host_doc.jsonl")
    sch = build_schedule(turns, V, R, STAGE_FRACS)
    phaseA = [p for p in sch if p["phase"] == "A"]
    phaseB = [p for p in sch if p["phase"] == "B"]
    decl = "REGION_SURCHARGE_CENTS = {"
    tileB = next(p for p in phaseB if decl in p["view_text"])
    viewA = next(compress_code(p["slice_text"], V) for p in phaseA if decl in compress_code(p["slice_text"], V))
    print(f"raw Phase-B tile: {n_tokens(tileB['view_text'])} tok | "
          f"structure-preserving Phase-A view: {n_tokens(viewA)} tok", flush=True)

    server = LlamaServer(str(ROOT / "models" / "llamacpp" / "llama-server.exe"),
                         str(ROOT / "models" / "Qwen2.5-7B-Instruct-Q4_K_M.gguf"),
                         ctx=16384, port=8093, threads=8)
    server.ensure_running()
    out = {"gate": "differential_recording", "draws": []}
    for seed, temp in DRAWS:
        sa, na, wa = run_one(server, viewA, TASK, 1, 6, temp, seed)       # coupled Phase-A exposure
        sb, nb, wb = run_one(server, tileB["view_text"], TASK, 1, 25, temp, seed)  # verbatim raw tile
        ra, rb = table_recorded(sa, table), table_recorded(sb, table)
        rec = {"seed": seed, "temp": temp,
               "phaseA_coupled": {**ra, "n_ops": na, "wall_s": wa, "state": sa},
               "phaseB_verbatim": {**rb, "n_ops": nb, "wall_s": wb, "state": sb}}
        out["draws"].append(rec)
        print(f"  seed={seed} t={temp}: PhaseA(coupled) kv={ra['entries_kv']} vals={ra['values_present']} "
              f"q={ra['queried_present']} | PhaseB(verbatim) kv={rb['entries_kv']} vals={rb['values_present']} "
              f"q={rb['queried_present']}", flush=True)
    server.stop()
    (HERE / "recording_gate_result.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                                     encoding="utf-8")
    print("\nGATE 2 read: differential ALIVE iff Phase-A(coupled) records the table where "
          "Phase-B(verbatim) does not. Adjudicate by the kv/values/queried columns + manual state read.")


if __name__ == "__main__":
    main()
