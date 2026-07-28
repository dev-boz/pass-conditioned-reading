"""P1 discrimination battery — $0 frozen-weight probes (gauntlet-arbitration-2026-07-28 §7).

Ports the 07-26 scratchpad probes into the repo with the two rulings the second gauntlet added:
DUAL SCORING (every op-level metric reports *emitted* — what the model wrote — and *applied* —
what the strict guard let into the state; the crowding probe's 7/10-vs-0/10 headline compared one
against the other) and INLINE DENOMINATORS. All probes are `gate_legal:false` by construction and
share the frozen Stage-A harness: prompts via `pca.teacher_gen` (byte-identical to training,
addendum need-class substitution included), strict guard, 24-op cap, seeds 1-10 at temp 0.7,
max_tokens 900 (as trained). One model at a time on the 1080 Ti.

  P1a — suppression discriminator (kimi's 2x2 + gpt-5.6's padding cell, both models):
        {empty, 25-entry own-state prefix, token-matched digit-free padding} x
        {trained verbatim rubric, +ADD-license sentence}.
        Pre-registered readings: ADD-license restores APPLIED recording in both models -> rubric
        effect (prompt fix). Untrained 3B records under the 25-entry state where the student
        does not -> training artifact (data fix). Padding suppresses like the real prefix ->
        presence/length, not content. All 25-entry cells ~0 in both models under both rubrics ->
        structural (first measured support for lever 10).
  P1b — typed-slot fill probe (handoff #2, glm/gemini-studio variant; ORACLE state, declared):
        hand-seeded state with three typed slots (table / adder / formula) + five digit-free
        fillers, run against the pass-26 tile. The tile holds the adder and the fn body but NO
        table values, so the table slot is the in-probe hallucination control: filling S2/S3 is
        slot mechanics working; digits appearing in S1 is fabrication.
  P1d — k-conditioning probe (deepseek; = falsifier F2 for the constructed-pairs lever):
        identical tile, identical verbatim rubric, identical 25-entry state; only the rendered
        `position: {k: N, K: 31}` varies over k in {5, 15, 26}. Student only. If behaviour
        (placeholder rate, exact-value rate, op mix) does not move with k, the conditioning
        channel is doing no timestep work.

  python experiments/e2prime/stagea_p1_probes.py --probe p1a --dry-run
  python experiments/e2prime/stagea_p1_probes.py --probe p1a            # both models, sequential
  python experiments/e2prime/stagea_p1_probes.py --probe p1b
  python experiments/e2prime/stagea_p1_probes.py --probe p1d            # student only
  python experiments/e2prime/stagea_p1_probes.py --summarize
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P7 = ROOT / "experiments" / "p7_split_unit"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(P7))
sys.path.insert(0, str(HERE))

from pca.editops import IntegrationState, parse_ops                      # noqa: E402
from pca.llm import LlamaServer                                          # noqa: E402
from pca.teacher_gen import _system_prompt, _user_prompt                 # noqa: E402
from pca.textutils import n_tokens                                      # noqa: E402
from verify_fixture import load_turns                                    # noqa: E402
from analyze_chain_gate import rescore                                   # noqa: E402
from stagea_chain_gate import load_config, preflight, build_passes       # noqa: E402

MODELS = {
    "student": ROOT / "runs" / "stageA_coupled_v2" / "stageA_v2-f16.gguf",
    "qwen3b": ROOT / "models" / "Qwen2.5-3B-Instruct-f16.gguf",
}
SEEDS = list(range(1, 11))
TEMP = 0.7
MAX_TOKENS = 900          # recording passes, as trained
OP_CAP = 24
OUT_DIR = ROOT / "runs" / "stageA_chain_gate" / "_probe_p1"
S2_RECORD = ROOT / "runs" / "stageA_chain_gate" / "student_s2_t0.7.json"

# The one-sentence ADD license (arbitration 07-26 §4B control (b), formalized 07-28). Generic:
# names no probe token, so the forcing boundary holds.
ADD_LICENSE = (" If this view contains material your state has no entry for, ADD a new entry "
               "recording it.")

# Placeholder emissions, for P1b/P1d readings. Loose on purpose; hand-reading arbitrates.
_PLACEHOLDER = re.compile(
    r"\[TBD[^\]]*\]|\bTBD\b|to be (?:determined|filled|resolved)|insert (?:value|here)"
    r"|values? pending|<[a-z_]{3,}>", re.I)

PROBE_TOKENS = ["REGION_SURCHARGE_CENTS", "RECONCILIATION_ADDER_CENTS",
                "compute_line_surcharge", "2353", "988", "1365", "region 23", "surcharge"]


# --------------------------------------------------------------------------- materials
def harness_materials() -> tuple[dict, dict, dict]:
    """Frozen cfg + the pass-26 tile, via the same loaders as the gate runner."""
    cfg = load_config()
    spec = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    scaffold = json.loads((P7 / "scaffold_struct.json").read_text(encoding="utf-8"))
    turns = load_turns(P7 / "fixture" / "host_doc.jsonl")
    _, sch, _, _ = preflight(spec, turns, scaffold, cfg)
    passes = build_passes(sch, scaffold)
    tile26 = passes[25]
    assert tile26["k"] == 26 and tile26["K"] == 31, (tile26["k"], tile26["K"])
    assert "def compute_line_surcharge" in tile26["view_text"], "pass-26 tile lost the fn body"
    assert "1365" in tile26["view_text"], "pass-26 tile lost the adder"
    assert "988" not in tile26["view_text"], "table value leaked into the pass-26 tile"
    return cfg, spec, tile26


def s2_pass26_state_lines() -> list[str]:
    """The state seed 2's student actually SAW at pass 26, parsed from the archived user prompt
    (not re-derived), matching the 07-26 crowding probe's construction."""
    rec = json.loads(S2_RECORD.read_text(encoding="utf-8"))
    p26 = next(p for p in rec["passes"] if p["k"] == 26)
    m = re.search(r"STATE:\n(.*?)\n\nVIEW \(pass ", p26["user"], re.S)
    assert m, "archived pass-26 user prompt did not parse"
    lines = [ln for ln in m.group(1).splitlines() if ln.strip()]
    assert len(lines) >= 100, f"expected a large pass-26 state, got {len(lines)} lines"
    return lines


def state_from_lines(lines: list[str]) -> IntegrationState:
    """Seed a strict-guard state with exact archived id/text pairs via the official loader."""
    entries = []
    for ln in lines:
        m = re.match(r"(S\d+[a-z]?):\s(.*)", ln, re.S)
        assert m, f"unparseable state line: {ln[:80]}"
        entries.append({"id": m.group(1), "text": m.group(2)})
    nums = [int(re.match(r"S(\d+)", e["id"]).group(1)) for e in entries]
    return IntegrationState.from_snapshot({"entries": entries, "next": max(nums) + 1},
                                          guard="strict")


def padding_lines(target_tokens: int, n_entries: int = 25) -> list[str]:
    """Digit-free inert filler, token-matched to the real 25-entry prefix (gpt-5.6's control:
    the empty-vs-25 contrast varies prompt length as well as state presence). Deterministic."""
    stems = [
        "Module notes pending review for downstream consolidation of routine internals.",
        "Helper inventory deferred; structural pass noted this region as routine plumbing.",
        "Utility routines observed here follow the common normalization pattern seen earlier.",
        "Serialization details in this region deferred to a later verbatim pass for review.",
        "Configuration handling here is conventional; specifics left for later consolidation.",
    ]
    lines = [f"S{i + 1}: {stems[i % len(stems)]}" for i in range(n_entries)]
    filler = " Additional routine detail noted for later review."
    i = 0
    while n_tokens("\n".join(lines)) < target_tokens - 8:
        lines[i % n_entries] += filler
        i += 1
    return lines


# Slot-syntax control: SAME oracle module/name mentions, SAME entry count, NO typed empty slots.
# Separates "the [TBD:] slot is load-bearing" from "a small on-topic state permits recording".
CTRL8_LINES = [
    "S1: pricing/region_tables.py defines REGION_SURCHARGE_CENTS (cents per region code).",
    "S2: fulfillment/line_quote.py defines RECONCILIATION_ADDER_CENTS.",
    "S3: fulfillment/line_quote.py: compute_line_surcharge(region_code), quote_line.",
    "S4: billing digest module: helper routines for parcel normalization and slot ranking — "
    "details deferred.",
    "S5: carrier cursor module: record tokenization and claim hashing utilities — details "
    "deferred.",
    "S6: audit node module: manifest merge and packet compaction helpers — details deferred.",
    "S7: serialize tariff module: parcel flattening and shard trimming — details deferred.",
    "S8: routing digest module: route dedupe and packet expansion — details deferred.",
]

SLOT_LINES = [
    "S1: pricing/region_tables.py defines REGION_SURCHARGE_CENTS (cents per region code) — "
    "values: [TBD:table rows].",
    "S2: fulfillment/line_quote.py defines RECONCILIATION_ADDER_CENTS = [TBD:cents].",
    "S3: fulfillment/line_quote.py: compute_line_surcharge(region_code) — computation: "
    "[TBD:formula].",
    "S4: billing digest module: helper routines for parcel normalization and slot ranking — "
    "details deferred.",
    "S5: carrier cursor module: record tokenization and claim hashing utilities — details "
    "deferred.",
    "S6: audit node module: manifest merge and packet compaction helpers — details deferred.",
    "S7: serialize tariff module: parcel flattening and shard trimming — details deferred.",
    "S8: routing digest module: route dedupe and packet expansion — details deferred.",
]


# --------------------------------------------------------------------------- scoring
def _score_text(text: str) -> dict:
    """Emitted- or applied-side flags from the audited matcher, plus placeholder count."""
    f = rescore(text)
    return {"relation": f["relation_recorded"], "relation_partial": f["relation_partial"],
            "fn_named": f["fn_named"], "mapping": f["queried_mapping"],
            "adder": f["adder_value_present"],
            "placeholders": len(_PLACEHOLDER.findall(text or ""))}


def run_cell(server, label: str, system: str, user_k: int, state: IntegrationState,
             view: str, seeds: list[int]) -> dict:
    """One condition: n draws, each from a FRESH copy of the condition state. Dual-scored."""
    snap = state.snapshot()
    cell = {"n": 0, "state_text": state.render(), "state_tokens": n_tokens(state.render()),
            "system": system, "draws": []}
    for seed in seeds:
        st = IntegrationState.from_snapshot(json.loads(json.dumps(snap)), guard="strict")
        user = _user_prompt(user_k, 31, st.render(), view)
        resp = server.chat(system, user, max_tokens=MAX_TOKENS, temperature=TEMP, seed=seed)
        res = parse_ops(resp["text"], st.ids(), st.next_id)
        applied = st.apply(res.ops[:OP_CAP])
        post = st.render()
        d = {"seed": seed,
             "emitted": _score_text(resp["text"]),
             "applied": _score_text(post),
             "n_candidate_lines": res.candidate_lines, "n_valid": res.valid,
             "n_ops_applied": applied, "n_blocked": len(st.last_report["blocked"]),
             "op_types": dict(Counter(o["op"] for o in res.ops)),
             "replace_targets": [o.get("id") for o in res.ops if o["op"] == "REPLACE"],
             "raw_output": resp["text"], "post_state": post,
             "wall_s": resp.get("wall_s")}
        cell["draws"].append(d)
        cell["n"] += 1
        print(f"    {label} seed={seed} valid={res.valid}/{res.candidate_lines} "
              f"applied={applied} blocked={d['n_blocked']} "
              f"emit[rel={d['emitted']['relation']} fn={d['emitted']['fn_named']} "
              f"adder={d['emitted']['adder']}] "
              f"appl[rel={d['applied']['relation']} fn={d['applied']['fn_named']} "
              f"adder={d['applied']['adder']}] ({d['wall_s']}s)", flush=True)
    for side in ("emitted", "applied"):
        cell[f"{side}_totals"] = {k: sum(d[side][k] if isinstance(d[side][k], bool)
                                         else int(d[side][k] > 0)
                                         for d in cell["draws"])
                                  for k in ("relation", "relation_partial", "fn_named",
                                            "mapping", "adder", "placeholders")}
    return cell


# --------------------------------------------------------------------------- probes
def probe_cells(probe: str, cfg: dict, tile26: dict) -> tuple[dict, dict]:
    """Returns ({cell_label: (system, user_k, state_builder)}, meta_extras)."""
    sys_current = _system_prompt(cfg, "verbatim")
    anchor = "NO_CHANGE if this view adds nothing your state needs."
    assert anchor in sys_current, "verbatim rubric drifted; ADD-license splice has no anchor"
    sys_addlic = sys_current.replace(anchor, anchor + ADD_LICENSE)
    for sysp in (sys_current, sys_addlic):
        leaks = [t for t in PROBE_TOKENS if t.lower() in sysp.lower()]
        assert not leaks, f"forcing-boundary violation in probe system prompt: {leaks}"

    s25 = s2_pass26_state_lines()[:25]
    if probe == "p1a":
        pad = padding_lines(n_tokens("\n".join(s25)))
        cells = {
            "empty_current": (sys_current, 26, lambda: IntegrationState(guard="strict")),
            "empty_addlicense": (sys_addlic, 26, lambda: IntegrationState(guard="strict")),
            "s25_current": (sys_current, 26, lambda: state_from_lines(s25)),
            "s25_addlicense": (sys_addlic, 26, lambda: state_from_lines(s25)),
            "pad25_current": (sys_current, 26, lambda: state_from_lines(pad)),
        }
        meta = {"oracle": False,
                "question": "is the suppression step a training artifact, a rubric effect, "
                            "or structural?",
                "readings": {
                    "rubric_effect": "s25_addlicense applied-recording > s25_current, both models",
                    "training_artifact": "qwen3b records under s25_current where student does not",
                    "presence_not_content": "pad25_current suppresses like s25_current",
                    "structural": "all 25-entry cells ~0 in both models under both rubrics"},
                "add_license_sentence": ADD_LICENSE,
                "s25_source": "first 25 lines of the state seed 2 saw at pass 26 (archived user "
                              "prompt), matching the 07-26 crowding construction",
                "pad_tokens_target": n_tokens("\n".join(s25))}
    elif probe == "p1b":
        pad8 = padding_lines(n_tokens("\n".join(SLOT_LINES)), n_entries=8)
        cells = {
            "slots_current": (sys_current, 26, lambda: state_from_lines(SLOT_LINES)),
            "ctrl8_noslot": (sys_current, 26, lambda: state_from_lines(CTRL8_LINES)),
            "pad8_current": (sys_current, 26, lambda: state_from_lines(pad8)),
        }
        meta = {"oracle": True,
                "question": "does the model FILL typed slots from the view (REPLACE into "
                            "S1-S3) rather than emit name-lists?",
                "oracle_note": "slots_current and ctrl8_noslot name fixture identifiers by "
                               "hand — declared, design-input only, never poolable",
                "controls": {"fillable_from_view": ["S2 (adder)", "S3 (formula)"],
                             "not_fillable": "S1 (table values absent from this tile; digits "
                                             "appearing in S1 = fabrication)",
                             "ctrl8_noslot": "same oracle mentions + entry count, no slot "
                                             "syntax — isolates the [TBD:] slot itself",
                             "pad8_current": "8 irrelevant digit-free entries — isolates "
                                             "state SIZE (suppression was measured at >=25)"}}
    elif probe == "p1d":
        cells = {f"k{k}": (sys_current, k, lambda: state_from_lines(s25)) for k in (5, 15, 26)}
        meta = {"oracle": False,
                "question": "does the position channel (k/K) do any conditioning work, holding "
                            "rubric, state and view fixed? (= constructed-pairs falsifier F2)",
                "note": "k5/k15 pair a verbatim rubric with early-pass labels — a combination "
                        "training never showed; that mismatch IS the probe"}
    else:
        raise SystemExit(f"unknown probe {probe}")
    return cells, meta


def summarize(out_dir: Path) -> None:
    for f in sorted(out_dir.glob("p1*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        print(f"\n=== {f.name} ({rec['_meta']['model_key']}) ===")
        print(f"{'cell':<20} {'n':>2} | emitted rel/fn/adder | applied rel/fn/adder | plc(e/a)")
        for label, cell in rec["conditions"].items():
            e, a = cell["emitted_totals"], cell["applied_totals"]
            print(f"{label:<20} {cell['n']:>2} |   {e['relation']}/{e['fn_named']}/{e['adder']}"
                  f"{'':<12}|   {a['relation']}/{a['fn_named']}/{a['adder']}{'':<12}"
                  f"| {e['placeholders']}/{a['placeholders']}")
    print("\nProbe numbers. gate_legal=false. Hand-read draws before any claim; the totals are "
          "pre-filters, and every rate's denominator is the cell's n.")


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", choices=["p1a", "p1b", "p1d"])
    ap.add_argument("--models", default=None,
                    help="comma list from {student,qwen3b}; default: p1d=student, else both")
    ap.add_argument("--seeds", default=None, help="e.g. '1-3' or '1,4' (default 1-10)")
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--ctx", type=int, default=24576)
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--threads", type=int, default=24)
    ap.add_argument("--redo", action="store_true", help="overwrite an existing complete record")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--summarize", action="store_true")
    args = ap.parse_args()

    if args.summarize:
        summarize(OUT_DIR)
        return
    if not args.probe:
        raise SystemExit("--probe required (or --summarize)")

    seeds = SEEDS
    if args.seeds:
        seeds = []
        for part in args.seeds.split(","):
            if "-" in part:
                a, b = part.split("-")
                seeds += list(range(int(a), int(b) + 1))
            else:
                seeds.append(int(part))

    cfg, spec, tile26 = harness_materials()
    cells, meta_extras = probe_cells(args.probe, cfg, tile26)

    model_keys = (args.models.split(",") if args.models
                  else (["student"] if args.probe == "p1d" else ["student", "qwen3b"]))

    if args.dry_run:
        print(f"\nDRY RUN {args.probe}: models={model_keys} seeds={seeds}")
        for label, (system, user_k, builder) in cells.items():
            st = builder()
            print(f"\n--- cell {label}: k={user_k}, state {n_tokens(st.render())} tok, "
                  f"{len(st.entries)} entries ---")
            print(st.render()[:400])
        print(f"\n--- tile26 view head ---\n{tile26['view_text'][:300]}")
        print("\nDry run OK. Nothing served, nothing written.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    exe = ROOT / "models" / "llamacpp" / "llama-server.exe"
    for mk in model_keys:
        model = MODELS[mk]
        assert model.exists(), model
        out_path = OUT_DIR / f"{args.probe}_{mk}.json"
        if out_path.exists() and not args.redo:
            try:
                if json.loads(out_path.read_text(encoding="utf-8")).get("complete"):
                    print(f"[skip] {out_path.name} already complete", flush=True)
                    continue
            except json.JSONDecodeError:
                pass
        rec = {"_meta": {"probe": True, "gate_legal": False, "probe_id": args.probe,
                         "model_key": mk, "model_path": str(model),
                         "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                         "seeds": seeds, "temp": TEMP, "max_tokens": MAX_TOKENS,
                         "op_cap": OP_CAP, "guard": "strict",
                         "tile": {"k": 26, "K": 31, "view_tokens": tile26["view_tokens"],
                                  "view_source": tile26["view_source"]},
                         **meta_extras},
               "conditions": {}, "complete": False}
        print(f"\n{'=' * 70}\n{args.probe} ARM: {mk}  ({model.name})\n{'=' * 70}", flush=True)
        server = LlamaServer(str(exe), str(model), ctx=args.ctx, port=args.port,
                             threads=args.threads, n_gpu_layers=args.ngl)
        server.ensure_running()
        t0 = time.time()
        try:
            for label, (system, user_k, builder) in cells.items():
                print(f"  cell {label} (k={user_k}):", flush=True)
                rec["conditions"][label] = run_cell(server, label, system, user_k, builder(),
                                                    tile26["view_text"], seeds)
                out_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False),
                                    encoding="utf-8")
        finally:
            server.stop()
            time.sleep(3)
        rec["complete"] = True
        rec["wall_s"] = round(time.time() - t0, 1)
        out_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"  -> {out_path.relative_to(ROOT)} in {rec['wall_s']}s", flush=True)


if __name__ == "__main__":
    main()
