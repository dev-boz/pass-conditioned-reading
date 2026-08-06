"""Stage-A P7 chain gate — strict v3.2 evaluator (E2PRIME-CRITERION §3, STAGEA-CHAIN-GATE-ADDENDUM).

Runs the Stage-A trained student and its same-base untrained floor on the frozen P7 split-unit
chain fixture, under the E2′ v3.2 recording harness the student was actually trained against.

WHY THIS IS NOT experiments/p7_split_unit/run.py: that runner is the LEGACY P7 harness. It uses
the P6-lineage neutral brief prompt, `IntegrationState()` (guard="off"), and `prep_ops()` — which
dedups placeholder ADDs and reorders REPLACE/REMOVE ahead of ADDs before the op cap. The Stage-A
student was trained against the E2′ v3.2 grammar, the per-pass scaffold/integrate/verbatim
rubrics, `IntegrationState(guard="strict")`, and RAW `ops[:op_cap]` application. Reusing the
legacy runner would confound the gate. Prompt construction here is imported from
`pca.teacher_gen` (not re-implemented) so the recorder prompt is byte-identical to training,
except for the one frozen substitution the addendum fixes: the query-conditioned need class.

Frozen protocol (addendum, maintainer-approved 2026-07-20):
  - fixture v2 / seed 70707, asserted before serving; frozen P7 v2 scaffold; unchanged schedule
  - strict v3.2 state application, 24-op per-pass cap, no legacy rewriting or deduplication
  - 10 sampled draws (seeds 1-10, temp 0.7) = the verdict denominator
  - 1 deterministic anchor (seed 42, temp 0) reported separately, NEVER pooled
  - local llama.cpp, one model at a time, 24,576 ctx, full GPU offload

The runner records MECHANICAL CANDIDATE FLAGS ONLY. Every candidate success is hand-verified
before any verdict is reported (addendum §Draws and scoring).

  python experiments/e2prime/stagea_chain_gate.py --dry-run          # preflight + prompt render, $0
  python experiments/e2prime/stagea_chain_gate.py --arm student      # the frozen battery
  python experiments/e2prime/stagea_chain_gate.py --summarize        # per-seed table from records
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

HERE = Path(__file__).resolve().parent          # experiments/e2prime
ROOT = HERE.parents[1]                          # repo root
P7 = ROOT / "experiments" / "p7_split_unit"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(P7))

from pca.editops import IntegrationState, parse_ops                      # noqa: E402
from pca.llm import LlamaServer                                          # noqa: E402
from pca.planted import build_schedule                                   # noqa: E402
from pca.teacher_gen import (GRAMMAR, RUBRICS, CLOSING_SYSTEM,           # noqa: E402
                             _stage, _system_prompt, _user_prompt)
from pca.textutils import n_tokens                                       # noqa: E402
from verify_fixture import dense_window_text, load_turns                 # noqa: E402

ADDENDUM = HERE / "STAGEA-CHAIN-GATE-ADDENDUM.md"
ADDENDUM_REL = "experiments/e2prime/STAGEA-CHAIN-GATE-ADDENDUM.md"

# The ONE frozen substitution vs the training-time prompt (addendum §Frozen setup, and the
# mandatory query-conditioned framing of E2PRIME-CRITERION §4.1 branch "PC fails" / §6.7).
# Names an information CLASS. No target structure, identifier, location, or value. Verbatim
# from the addendum — the audit rule of E2PRIME-CRITERION §2 checks this string.
ADDENDUM_NEED_CLASS = (
    "Downstream, operational questions about this codebase's pricing, order flow, "
    "configuration, and cross-module behavior will be answered from your state alone; "
    "the source will not be available."
)

# Closing = the trained closing frame (state alone, source unavailable) + the generic derive
# permission (P7 --permit-derive lineage) + the integer answer format. Task-agnostic: it names
# no operand, table, or relation, and forbids values absent from the state.
CLOSE_SYSTEM = (
    CLOSING_SYSTEM + " Base your answer on values present in the state; you MAY compute and "
    "combine those values arithmetically to derive the answer. Do not introduce values that "
    "are absent from the state. Reason briefly, then end with a line 'ANSWER: <integer>'. "
    "If the state lacks the values needed, end with 'ANSWER: INSUFFICIENT'."
)

ARMS = {
    "student": ROOT / "runs" / "stageA_coupled_v2" / "stageA_v2-f16.gguf",
    "floor": ROOT / "models" / "Qwen2.5-1.5B-Instruct-f16.gguf",
}
SAMPLED_DRAWS = [(s, 0.7) for s in range(1, 11)]   # the verdict denominator
ANCHOR_DRAW = (42, 0.0)                            # reported separately, never pooled


# --------------------------------------------------------------------------- helpers
def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def _int_present(text: str, value: int) -> bool:
    """Digit-boundary match: 1365 must not match inside 213650."""
    return re.search(rf"(?<!\d){value}(?!\d)", text) is not None


def _git(*args: str) -> str:
    try:
        p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=30)
        return p.stdout.strip() if p.returncode == 0 else ""
    except Exception:
        return ""


def addendum_commit_gate(allow_uncommitted: bool) -> dict:
    """The addendum's own status line and the E2PRIME-PREREG amendment rule require the addendum
    to be COMMITTED before the affected run. Enforced mechanically, not by discipline."""
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", ADDENDUM_REL],
                             cwd=ROOT, capture_output=True, text=True).returncode == 0
    dirty = _git("status", "--porcelain", "--", ADDENDUM_REL)
    committed = tracked and not dirty
    state = {"tracked": tracked, "dirty": dirty or None, "committed": committed,
             "override_used": bool(allow_uncommitted and not committed)}
    if not committed and not allow_uncommitted:
        raise SystemExit(
            f"REFUSING TO RUN A MODEL DRAW: {ADDENDUM_REL} is not committed "
            f"({'untracked' if not tracked else 'modified: ' + dirty}).\n"
            "The addendum must be committed before the affected run (its own status line + the "
            "E2PRIME-PREREG amendment rule). Commit it, or pass --allow-uncommitted-addendum "
            "for an explicitly NON-VERDICT run (the record is stamped verdict_eligible=false).")
    return state


def llama_server_version(exe: Path) -> str:
    try:
        p = subprocess.run([str(exe), "--version"], capture_output=True, text=True, timeout=60)
        return ((p.stderr or "") + (p.stdout or "")).strip().splitlines()[0]
    except Exception:
        return ""


# --------------------------------------------------------------------------- config / fixture
def load_config(guard: str | None = None) -> dict:
    """The training-time E2′ harness config, with the addendum's frozen need class substituted.

    `guard` overrides the harness guard mode. The frozen protocol is "strict" and that is what the
    Stage-A verdict was taken under, so an override is an EXPLORATORY arm by construction and
    forces verdict_eligible False (see main). Motivation for the "retain" mode is measured:
    1,003 of 3,226 applied REPLACEs in the pyramid draws (31%) destroyed numeric detail the entry
    already held — see experiments/e2prime/retention_probe.py.
    """
    cfg = yaml.safe_load((HERE / "teacher_config.yaml").read_text(encoding="utf-8"))
    cfg["task"]["need_class"] = ADDENDUM_NEED_CLASS
    assert cfg["harness"]["guard"] == "strict", cfg["harness"]["guard"]
    assert cfg["harness"]["op_cap"] == 24, cfg["harness"]["op_cap"]
    if guard:
        cfg["harness"]["guard"] = guard
    return cfg


def preflight(spec: dict, turns: list[dict], scaffold: list[dict], cfg: dict) -> dict:
    """Assert the frozen fixture, source coverage, scaffold coverage and the Phase-B split BEFORE
    any model is served (addendum §Frozen setup). Hard asserts gate the run; the dense-floor and
    relevance-control-v2 checks are recorded as informational (they gate companion checks, not
    this chain gate)."""
    g: dict = {}
    # (0) fixture identity + arithmetic
    assert spec["fixture_version"] == 2, spec["fixture_version"]
    assert spec["seed"] == 70707, spec["seed"]
    qcode, tval = spec["queried_code"], spec["table_value_for_queried"]
    adder, truth = spec["reconciliation_adder_cents"], spec["ground_truth_answer"]
    assert spec["table"][str(qcode)] == tval == 988, spec["table"][str(qcode)]
    assert adder == 1365 and truth == 2353 and tval + adder == truth
    g["fixture"] = {"version": 2, "seed": 70707, "queried_code": qcode,
                    "table_value": tval, "adder": adder, "ground_truth": truth}
    print(f"(0) fixture v2 seed 70707: REGION_SURCHARGE_CENTS[{qcode}]={tval}, "
          f"RECONCILIATION_ADDER_CENTS={adder}, target {tval}+{adder}={truth}  PASS")

    entry = f"{qcode}: {tval}"
    adder_decl = f"RECONCILIATION_ADDER_CENTS = {adder}"
    call = "compute_line_surcharge"
    table_decl = "REGION_SURCHARGE_CENTS = {"

    # (A) fires-on-source
    src = "\n".join(t["text"] for t in turns)
    assert entry in src and adder_decl in src, "(A) fragment not on source"
    g["source_presence"] = True
    print(f"(A) fires-on-source: '{entry}' and '{adder_decl}' present in host doc  PASS")

    # (B) dense-floor (informational: no dense arm in this gate)
    dense = dense_window_text(turns)
    g["dense_floor_excluded"] = entry not in dense and call not in dense
    print(f"(B) dense-floor exclusion (informational): {g['dense_floor_excluded']}")

    # schedule + scaffold alignment
    s = cfg["schedule"]["code"]
    sch = build_schedule(turns, s["V"], s["R"], tuple(s["stage_fracs"]))
    phaseA = [p for p in sch if p["phase"] == "A"]
    phaseB = [p for p in sch if p["phase"] == "B"]
    assert len(scaffold) == len(phaseA), f"scaffold {len(scaffold)} != Phase-A {len(phaseA)}"
    for c, p in zip(scaffold, phaseA):
        assert c["turn_lo"] == p["turn_lo"] and c["turn_hi"] == p["turn_hi"], "scaffold misaligned"
    g["schedule"] = {"V": s["V"], "R": s["R"], "stage_fracs": list(s["stage_fracs"]),
                     "phaseA": len(phaseA), "phaseB": len(phaseB), "K": len(sch)}
    print(f"(S) schedule: {len(phaseA)} Phase-A + {len(phaseB)} Phase-B = K={len(sch)}; "
          f"frozen scaffold aligned on all {len(scaffold)} chunk boundaries  PASS")

    # (C1) the frozen scaffold carries the operands into Phase-A
    all_scaffold = "\n".join(c["view_text"] for c in scaffold)
    assert entry in all_scaffold, "(C1) queried table entry not in the frozen scaffold"
    assert adder_decl in all_scaffold, "(C1) adder not in the frozen scaffold"
    g["scaffold_coverage"] = {
        "entry_chunks": [i for i, c in enumerate(scaffold) if entry in c["view_text"]],
        "adder_chunks": [i for i, c in enumerate(scaffold) if adder_decl in c["view_text"]],
        "table_decl_chunks": [i for i, c in enumerate(scaffold) if table_decl in c["view_text"]]}
    print(f"(C1) frozen scaffold carries: entry in chunk(s) {g['scaffold_coverage']['entry_chunks']}, "
          f"adder in {g['scaffold_coverage']['adder_chunks']}  PASS")

    # (C2) the split is real: no single Phase-B tile holds both fragments
    f1 = [i for i, p in enumerate(phaseB)
          if entry in p["view_text"] or table_decl in p["view_text"]]
    f2 = [i for i, p in enumerate(phaseB) if call in p["view_text"]]
    assert f1 and f2, "(C2) a fragment is missing from all Phase-B tiles"
    assert not (set(f1) & set(f2)), f"(C2) tile(s) {set(f1) & set(f2)} hold BOTH fragments"
    g["split"] = {"fragment1_tiles": f1, "fragment2_tiles": f2, "gap": min(f2) - max(f1)}
    print(f"(C2) split real: fragment-1 in Phase-B tile(s) {f1}, fragment-2 in {f2}, "
          f"no overlap (gap {min(f2) - max(f1)})  PASS")

    # (D) relevance-control v2 content in the frozen scaffold (informational; companion checks)
    return _relevance_control(g, spec, scaffold, all_scaffold), sch, phaseA, phaseB


def _relevance_control(g: dict, spec: dict, scaffold: list[dict], all_scaffold: str) -> dict:
    rc, pc = spec["relevance_control"], spec["positive_control"]
    g["relevance_control_v2"] = {
        "pc_chunks": [i for i, c in enumerate(scaffold) if pc["decl"] in c["view_text"]],
        "relevant_chunks": [i for i, c in enumerate(scaffold) if rc["relevant_decl"] in c["view_text"]],
        "arbitrary_chunks": [i for i, c in enumerate(scaffold) if rc["arbitrary_decl"] in c["view_text"]],
        "relevant_pairs": sum(1 for k, v in rc["relevant_table"].items()
                              if f'"{k}": "{v}"' in all_scaffold),
        "arbitrary_pairs": sum(1 for k, v in rc["arbitrary_table"].items()
                               if f'"{k}": "{v}"' in all_scaffold)}
    print(f"(D) relevance-control v2 in scaffold (informational): "
          f"PC {g['relevance_control_v2']['pc_chunks']}, "
          f"pair mappings {g['relevance_control_v2']['relevant_pairs']}/24 + "
          f"{g['relevance_control_v2']['arbitrary_pairs']}/24")
    return g


# --------------------------------------------------------------------------- pyramid arm
# The README's tiling pyramid (docs/SCHEDULE-DISCREPANCY-2026-07-30.md). Views come from a frozen
# per-arm set built by gen_pyramid_views.py, because the compressor is architecture: which one ran
# decides what each level can carry, and therefore what this gate can measure.
#
# C1 and C2 change character here, on the maintainer's 2026-07-30 call:
#   - old C1 ASSERTED the hand-built scaffold carried both operands into Phase A. On the pyramid
#     that is not an assumption to assert but a property to MEASURE, and it differs per arm.
#   - old C2 ASSERTED no Phase-B tile held both. Here the same question is asked of EVERY view and
#     the answer STAMPS the run (faithful vs assisted) instead of aborting it.
def preflight_pyramid(spec: dict, turns: list[dict], views: list[dict], meta: dict,
                      cfg: dict) -> dict:
    from verify_pyramid_schedule import classify, operand_markers, view_tags   # noqa: E402

    g: dict = {}
    qcode, tval = spec["queried_code"], spec["table_value_for_queried"]
    adder, truth = spec["reconciliation_adder_cents"], spec["ground_truth_answer"]
    assert spec["fixture_version"] == 2 and spec["seed"] == 70707, spec["fixture_version"]
    assert spec["table"][str(qcode)] == tval == 988 and adder == 1365 and truth == 2353
    assert tval + adder == truth
    g["fixture"] = {"version": 2, "seed": 70707, "queried_code": qcode, "table_value": tval,
                    "adder": adder, "ground_truth": truth}
    print(f"(0) fixture v2 seed 70707: REGION_SURCHARGE_CENTS[{qcode}]={tval}, "
          f"RECONCILIATION_ADDER_CENTS={adder}, target {tval}+{adder}={truth}  PASS")

    src = "\n".join(t["text"] for t in turns)
    assert f"{qcode}: {tval}" in src and f"RECONCILIATION_ADDER_CENTS = {adder}" in src
    g["source_presence"] = True
    print(f"(A) fires-on-source: both fragments present in host doc  PASS")

    lv = sorted({v["level"] for v in views})
    per_level = {l: sum(1 for v in views if v["level"] == l) for l in lv}
    assert sum(per_level.values()) == len(views)
    g["schedule"] = {"kind": "pyramid", "V": meta.get("V"), "levels": lv,
                     "tiles_per_level": per_level, "K": len(views),
                     "arm": meta.get("arm"), "compressor": meta.get("compressor_name")}
    print(f"(S) pyramid: levels {lv}, tiles {list(per_level.values())}, K={len(views)}; "
          f"arm={meta.get('arm')} compressor={meta.get('compressor_name')}  PASS")

    cls = classify(views, meta, spec)
    g["early_exposure"] = cls["first_level"]
    fl = cls["first_level"]
    print(f"(C1) EARLY EXPOSURE (measured, not asserted): "
          f"binding {qcode}->{tval} first at level {fl['entry'] or '-'}, "
          f"table literal at {fl['table_decl'] or '-'}, table named at {fl['table_name'] or '-'}, "
          f"adder value at {fl['adder_value'] or '-'}, fn at {fl['fn'] or '-'}")

    g["split_intact"] = cls["split_intact"]
    g["both_operand_views"] = cls["both_operand_views"]
    g["run_class"] = cls["run_class"]
    g["run_class_reasons"] = cls["reasons"]
    g["probe_blind"] = cls["probe_blind"]
    if cls["split_intact"]:
        print(f"(C2) split-fact guard: PASS — no single view holds both operands")
    else:
        ks = [b["k"] for b in cls["both_operand_views"]]
        print(f"(C2) split-fact guard: BROKEN — view(s) k={ks[:8]} hold BOTH operands. "
              f"This arm is answerable from one pass, so it measures RETENTION, not composition.")
    print(f"(R) RUN CLASS: {cls['run_class'].upper()}"
          + (f"  ({'; '.join(cls['reasons'])})" if cls["reasons"] else ""))

    M = operand_markers(spec)
    g["operand_views"] = [{"k": v["k"], "level": v["level"],
                           "tags": [t for t, on in view_tags(v["view_text"], M).items() if on]}
                          for v in views if any(view_tags(v["view_text"], M).values())]
    return g


def pyramid_stage(level: int, n_levels: int, fracs: tuple) -> str:
    """Output demand by RESOLUTION, which on the pyramid is the level — not the pass fraction.

    M1's coupling claim is that one schedule position sets both what the model is shown and what it
    must produce. On the D25 two-phase schedule those coincide with pass fraction because there are
    only two resolutions. On the pyramid they do not: level 6 begins at k=32 of 63, so a
    fraction-based ladder would put ten VERBATIM views under the 'concrete' rubric. Staging by
    level keeps the two halves of the coupling aligned, which is the point of the schedule.
    """
    f = (level - 1) / max(n_levels - 1, 1)
    stage = "scaffold" if f < fracs[0] else "integrate" if f < fracs[1] else "verbatim"
    # The stage name is a RUBRICS key; `planted.py` labels the middle stage "concrete" while the
    # prompt module calls it "integrate", so assert against the real keyset rather than trusting
    # either literal.
    assert stage in RUBRICS, f"stage {stage!r} is not a rubric ({sorted(RUBRICS)})"
    return stage


def build_passes_pyramid(views: list[dict], fracs: tuple, stage_map: str) -> list[dict]:
    n_levels = len(sorted({v["level"] for v in views}))
    out = []
    for v in views:
        out.append({"phase": "B" if v["verbatim"] else "A", "level": v["level"],
                    "turn_lo": v["turn_lo"], "turn_hi": v["turn_hi"],
                    "view_text": v["view_text"], "view_source": v["view_source"],
                    "slice_tokens": v["slice_tokens"],
                    "compression_ratio": v["compression_ratio"]})
    for i, p in enumerate(out):
        p["k"], p["K"] = i + 1, len(out)
        p["view_tokens"] = n_tokens(p["view_text"])
        p["stage"] = (pyramid_stage(p["level"], n_levels, fracs) if stage_map == "level"
                      else _stage(p["k"], p["K"], fracs))
    return out


def build_passes(sch: list[dict], scaffold: list[dict]) -> list[dict]:
    """The P7 coupled schedule with Phase-A views replaced by the FROZEN scaffold views
    (identical across every draw, seed and arm — the P7 freeze semantics)."""
    phaseA = [p for p in sch if p["phase"] == "A"]
    phaseB = [p for p in sch if p["phase"] == "B"]
    out = []
    for c, p in zip(scaffold, phaseA):
        out.append({"phase": "A", "turn_lo": p["turn_lo"], "turn_hi": p["turn_hi"],
                    "view_text": c["view_text"], "view_source": "frozen_scaffold_v2",
                    "slice_tokens": p["slice_tokens"]})
    for p in phaseB:
        out.append({"phase": "B", "turn_lo": p["turn_lo"], "turn_hi": p["turn_hi"],
                    "view_text": p["view_text"], "view_source": "verbatim_tile",
                    "slice_tokens": p["slice_tokens"]})
    for i, p in enumerate(out):
        p["k"], p["K"] = i + 1, len(out)
        p["view_tokens"] = n_tokens(p["view_text"])
    return out


# --------------------------------------------------------------------------- mechanical flags
def state_flags(state_text: str, spec: dict) -> dict:
    """Mechanical pre-filters on the rendered state. NOT a verdict — the addendum requires every
    candidate success to be hand-verified."""
    qcode, tval = spec["queried_code"], spec["table_value_for_queried"]
    adder, truth = spec["reconciliation_adder_cents"], spec["ground_truth_answer"]
    flat = re.sub(r"\s+", " ", state_text)
    # PARAPHRASE-ROBUST (2026-08-02). This flag used to require a literal colon
    # (rf"{qcode}\s*:\s*{tval}"), and the state that finally held both operands wrote the binding
    # as "23→988". The flag read False on a state that held the fact, correctly bound — the exact
    # "exact-substring on a paraphrasing state" trap pca.planted warns about in its own docstring,
    # and the outstanding instrument debt the 07-29 handoff listed as
    # "paraphrase-robust matcher into the chain runner's live flags".
    # Re-scoring the archive with the analysis-side matcher moved D25 student RECORD from 1/10 to
    # 3/10, so the undercount reached a verdict-eligible run. The separator class matches the
    # analysis path (analyze_chain_gate._PAIR) so live and post-hoc scoring cannot diverge again;
    # the old strict form is kept alongside it for continuity with archived records.
    queried_strict = bool(re.search(rf"(?<!\d){qcode}\s*:\s*{tval}(?!\d)", flat))
    queried = bool(re.search(rf"(?<!\d){qcode}\D{{1,8}}{tval}(?!\d)", flat))
    return {
        "queried_mapping": queried,                                   # RECORD: 23 -> 988 held
        "queried_mapping_colon_only": queried_strict,                 # pre-2026-08-02 form
        "table_value_present": _int_present(flat, tval),
        "adder_named": f"RECONCILIATION_ADDER_CENTS = {adder}" in flat
                       or bool(re.search(rf"RECONCILIATION_ADDER_CENTS\D{{0,4}}{adder}(?!\d)", flat)),
        "adder_value_present": _int_present(flat, adder),
        "precomposed_answer": _int_present(flat, truth),              # 2353 already in state
        "kv_count": sum(1 for k, v in spec["table"].items()
                        if re.search(rf"(?<!\d){k}\s*:\s*{v}(?!\d)", flat)),
        "control_kv": sum(1 for k, v in spec["control_table"].items()
                          if re.search(rf"(?<!\d){k}\s*:\s*{v}(?!\d)", flat)),
    }


def closing_flags(text: str, answer: int | None, spec: dict, final: dict) -> dict:
    """The addendum's four end-to-end conditions, as MECHANICAL candidate flags."""
    tval, adder, truth = (spec["table_value_for_queried"], spec["reconciliation_adder_cents"],
                          spec["ground_truth_answer"])
    c1 = bool(final["queried_mapping"] and final["adder_value_present"])
    c2 = not final["precomposed_answer"]
    c3 = answer == truth
    c4 = _int_present(text, tval) and _int_present(text, adder)   # derivation visible in the close
    cand = bool(c1 and c2 and c3 and c4)
    return {"c1_operands_in_final_state": c1, "c2_no_precomposed_2353": c2,
            "c3_close_returns_2353": c3, "c4_derivation_visible_in_close": c4,
            "candidate_success": cand, "requires_hand_verification": cand}


# --------------------------------------------------------------------------- the draw
def run_draw(server, passes: list[dict], spec: dict, cfg: dict, seed: int, temp: float,
             out_path: Path, meta: dict, max_tokens: int, closing_max_tokens: int,
             max_passes: int | None) -> dict:
    fracs = tuple(cfg["schedule"]["code"]["stage_fracs"])
    op_cap = cfg["harness"]["op_cap"]
    todo = passes[:max_passes] if max_passes else passes
    st = IntegrationState(guard=cfg["harness"]["guard"])       # strict — as trained
    rec = {"_meta": {**meta, "seed": seed, "temp": temp, "max_tokens": max_tokens,
                     "closing_max_tokens": closing_max_tokens,
                     "op_cap": op_cap, "guard": cfg["harness"]["guard"],
                     "n_passes_planned": len(todo)},
           "passes": [], "complete": False}
    truncated, trunc_at, trunc_http = False, None, None
    first_record_pass, first_record_phase = None, None
    t0 = time.time()

    for p in todo:
        # pyramid passes carry a precomputed stage (staged by LEVEL, see pyramid_stage);
        # the D25 path is unchanged and still derives it from the pass fraction.
        stage = p.get("stage") or _stage(p["k"], p["K"], fracs)
        system = _system_prompt(cfg, stage)
        user = _user_prompt(p["k"], p["K"], st.render(), p["view_text"])
        try:
            resp = server.chat(system, user, max_tokens=max_tokens, temperature=temp, seed=seed)
        except requests.exceptions.HTTPError as e:
            trunc_http = getattr(getattr(e, "response", None), "status_code", None)
            truncated, trunc_at = True, p["k"]
            print(f"  !! pass {p['k']}/{p['K']} HTTP {trunc_http} (context exhausted) -> "
                  f"truncating arm; closing on the state so far", flush=True)
            break
        res = parse_ops(resp["text"], st.ids(), st.next_id)
        # RAW application: ops in emitted order, capped at op_cap. NO legacy prep_ops dedup or
        # REPLACE-first reordering — the student was trained against exactly this.
        applied = st.apply(res.ops[:op_cap])
        rendered = st.render()
        fl = state_flags(rendered, spec)
        if fl["queried_mapping"] and first_record_pass is None:
            first_record_pass, first_record_phase = p["k"], p["phase"]
        rec["passes"].append({
            "k": p["k"], "K": p["K"], "phase": p["phase"], "stage": stage,
            "level": p.get("level"), "compression_ratio": p.get("compression_ratio"),
            "view_source": p["view_source"], "view_tokens": p["view_tokens"],
            "system": system, "user": user, "raw_output": resp["text"],
            "n_candidate_lines": res.candidate_lines, "n_valid": res.valid,
            "n_aliased": res.aliased, "invalid_lines": res.invalid,
            "ops": [dict(o) for o in res.ops], "n_ops_applied": applied,
            "apply_report": st.last_report, "state_snapshot": st.snapshot(),
            "state_text": rendered, "state_tokens": n_tokens(rendered),
            "flags": fl, "wall_s": resp.get("wall_s"),
        })
        print(f"  pass {p['k']}/{p['K']} ({p['phase']}/{stage}) valid={res.valid}/"
              f"{res.candidate_lines} applied={applied} blocked={len(st.last_report['blocked'])} "
              f"redir={len(st.last_report['redirected'])} state={n_tokens(rendered)}tok "
              f"q_map={fl['queried_mapping']} adder={fl['adder_value_present']} "
              f"({resp.get('wall_s')}s)", flush=True)
        out_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")

    final_state = st.render()
    final = state_flags(final_state, spec)
    close_user = (f"FINAL STATE:\n{final_state}\n\nQuestion: {spec['scoring_question']}\n"
                  "Reason briefly from the state, then end with: ANSWER: <integer>")
    try:
        cresp = server.chat(CLOSE_SYSTEM, close_user, max_tokens=closing_max_tokens,
                            temperature=temp, seed=seed)
        ctext, chttp = cresp["text"], None
    except requests.exceptions.HTTPError as e:
        chttp = getattr(getattr(e, "response", None), "status_code", None)
        ctext = f"<closing failed: HTTP {chttp}>"
        print(f"  !! closing HTTP {chttp} (state too large for context)", flush=True)
    m = re.search(r"ANSWER:\s*(-?\d[\d,]*)", ctext)
    answer = int(m.group(1).replace(",", "")) if m else None
    # No ANSWER line at all: distinguish "ran out of decode budget mid-reasoning" from a refusal
    # to answer. Both score as no-answer, but only the first is a measurement artifact, so it is
    # recorded per draw rather than silently pooled into the failures.
    answer_line_missing = m is None and "INSUFFICIENT" not in ctext

    rec["final_state"] = final_state
    rec["final_state_tokens"] = n_tokens(final_state)
    rec["final_flags"] = final
    rec["record_first_pass"] = first_record_pass
    rec["record_first_phase"] = first_record_phase
    rec["closing"] = {"system": CLOSE_SYSTEM, "user": close_user, "raw_output": ctext,
                      "answer": answer, "http_error": chttp,
                      "answer_line_missing": answer_line_missing,
                      "closing_tokens": n_tokens(ctext),
                      "closing_budget_exhausted": answer_line_missing
                      and n_tokens(ctext) >= closing_max_tokens - 32}
    rec["scoring"] = closing_flags(ctext, answer, spec, final)
    rec["truncated"] = truncated
    rec["truncated_at_pass"] = trunc_at
    rec["truncated_http"] = trunc_http
    rec["n_passes_run"] = len(rec["passes"])
    rec["wall_s"] = round(time.time() - t0, 1)
    rec["complete"] = True
    out_path.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    s = rec["scoring"]
    print(f"  -> ANSWER={answer} | c1_operands={s['c1_operands_in_final_state']} "
          f"c2_no_precompose={s['c2_no_precomposed_2353']} c3_2353={s['c3_close_returns_2353']} "
          f"c4_derivation={s['c4_derivation_visible_in_close']} "
          f"CANDIDATE={s['candidate_success']}"
          f"{'  [HAND-VERIFY]' if s['candidate_success'] else ''} "
          f"| record_first_pass={first_record_pass} ({first_record_phase}) "
          f"[{rec['wall_s']}s]", flush=True)
    return rec


# --------------------------------------------------------------------------- summarize
def summarize(out_dir: Path) -> None:
    recs = {}
    for f in sorted(out_dir.glob("*.json")):
        if f.name == "manifest.json" or f.name.startswith("smoke_"):
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("complete"):
            recs.setdefault(r["_meta"]["arm"], []).append(r)
    if not recs:
        print(f"no complete records in {out_dir}")
        return
    for arm, rs in recs.items():
        sampled = sorted([r for r in rs if (r["_meta"]["seed"], r["_meta"]["temp"]) in
                          [(s, t) for s, t in SAMPLED_DRAWS]], key=lambda r: r["_meta"]["seed"])
        anchor = [r for r in rs if (r["_meta"]["seed"], r["_meta"]["temp"]) == ANCHOR_DRAW]
        elig = all(r["_meta"].get("verdict_eligible") for r in sampled) if sampled else False
        print(f"\n=== {arm} === (verdict_eligible={elig})")
        print(f"{'seed':>5} {'temp':>4} {'ans':>6} {'c1':>5} {'c2':>5} {'c3':>5} {'c4':>5} "
              f"{'cand':>5} {'rec@':>5} {'trunc':>5}")
        for r in sampled + anchor:
            s, m = r["scoring"], r["_meta"]
            tag = "  <- anchor (never pooled)" if (m["seed"], m["temp"]) == ANCHOR_DRAW else ""
            print(f"{m['seed']:>5} {m['temp']:>4} {str(r['closing']['answer']):>6} "
                  f"{str(s['c1_operands_in_final_state']):>5} {str(s['c2_no_precomposed_2353']):>5} "
                  f"{str(s['c3_close_returns_2353']):>5} {str(s['c4_derivation_visible_in_close']):>5} "
                  f"{str(s['candidate_success']):>5} {str(r['record_first_pass']):>5} "
                  f"{str(r['truncated']):>5}{tag}")
        n = len(sampled)
        cand = sum(s["scoring"]["candidate_success"] for s in sampled)
        rec_ = sum(s["final_flags"]["queried_mapping"] for s in sampled)
        ret = sum(s["final_flags"]["queried_mapping"] and s["final_flags"]["adder_value_present"]
                  for s in sampled)
        comp = sum(s["scoring"]["c3_close_returns_2353"] for s in sampled)
        print(f"  sampled denominator n={n}/10 | mechanical candidates {cand}/{n} "
              f"(HAND-VERIFY before any verdict) | RECORD(23:988 at close) {rec_}/{n} | "
              f"RECORD+adder {ret}/{n} | close returns 2353 {comp}/{n}")
    print("\nNOTE: candidate counts are MECHANICAL PRE-FILTERS. The addendum requires hand "
          "verification of every candidate success before a verdict is reported. The anchor "
          "(seed 42, temp 0) is never pooled with the sampled ten.")


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["student", "floor", "both"], default="both")
    # SCALE-RUNG PROBE ARM (2026-07-26). Runs the frozen harness against a model that is NOT a
    # pre-registered Stage-A arm, to ask whether the chain fires when COMPOSE is not the binding
    # constraint (GATE-3: 1.5B student 1/10 vs untrained 7B 10/10 on the identical seeded state).
    # SAFETY: passing --model FORCES verdict_eligible=False below, so a scale-rung run can never be
    # mistaken for, or pooled with, the frozen Stage-A verdict. The Stage-A arms are untouched.
    ap.add_argument("--model", default=None,
                    help="PROBE ONLY: explicit GGUF path replacing --arm; forces verdict_eligible "
                         "False. Requires --label.")
    ap.add_argument("--label", default=None, help="output arm name for --model runs")
    # SCHEDULE ARM (2026-07-30). `d25` is the frozen two-phase schedule the Stage-A verdict was
    # taken on and is byte-for-byte unchanged. `pyramid` is the README's tiling pyramid
    # (docs/SCHEDULE-DISCREPANCY-2026-07-30.md), reading frozen per-arm views from
    # gen_pyramid_views.py. A pyramid run is NEVER verdict-eligible: it is not the pre-registered
    # protocol the addendum froze, so it cannot be pooled with or mistaken for the Stage-A verdict.
    ap.add_argument("--schedule", choices=["d25", "pyramid"], default="d25")
    ap.add_argument("--views", default=None,
                    help="pyramid only: frozen compressor arm (extractive, graded, llm_general, "
                         "llm_roleaware, hand_blind, hand_oracle)")
    ap.add_argument("--guard", default=None, choices=["strict", "retain"],
                    help="EXPLORATORY: override the harness guard. 'retain' additionally refuses a "
                         "REPLACE that drops numeric literals the target entry held. Forces "
                         "verdict_eligible False — the frozen protocol is 'strict'.")
    ap.add_argument("--stage-map", choices=["level", "fraction"], default="level",
                    help="pyramid only: derive the output-demand stage from the LEVEL (default, "
                         "keeps M1's coupling aligned with resolution) or from the pass fraction")
    ap.add_argument("--seeds", default=None,
                    help="comma/range subset of the sampled seeds, e.g. '1-3' or '1,4' (default 1-10)")
    ap.add_argument("--no-anchor", action="store_true", help="skip the seed-42 temp-0 anchor")
    ap.add_argument("--anchor-only", action="store_true")
    ap.add_argument("--ctx", type=int, default=24576)
    ap.add_argument("--ngl", type=int, default=99)
    ap.add_argument("--threads", type=int, default=24)
    ap.add_argument("--port", type=int, default=8097)
    # Both budgets are the TRAINING-TIME budgets: pca.teacher_gen generates recording passes at
    # max_tokens=900 and the closing turn at 1200. The smoke draw showed a 900-token closing
    # truncating mid-reasoning before its ANSWER line — an artifact that biases against the arm
    # under test, so the closing budget matches training rather than the recording pass.
    ap.add_argument("--max-tokens", type=int, default=900, help="recording passes (as trained)")
    ap.add_argument("--closing-max-tokens", type=int, default=1200, help="closing turn (as trained)")
    ap.add_argument("--max-passes", type=int, default=None,
                    help="SMOKE ONLY: truncate the schedule. Stamps verdict_eligible=false and "
                         "writes to smoke_* files that --summarize ignores.")
    ap.add_argument("--out", default=None,
                    help="default: runs/stageA_chain_gate (d25) or "
                         "runs/stageA_chain_gate_pyramid/<views> (pyramid)")
    ap.add_argument("--dry-run", action="store_true",
                    help="preflight + render pass-1 prompts and the closing frame; serve nothing")
    ap.add_argument("--summarize", action="store_true")
    ap.add_argument("--skip-model-hash", action="store_true")
    ap.add_argument("--allow-uncommitted-addendum", action="store_true",
                    help="explicitly NON-VERDICT run with the addendum uncommitted")
    args = ap.parse_args()

    out = args.out or (f"runs/stageA_chain_gate_pyramid/{args.views}"
                       + (f"_guard-{args.guard}" if args.guard else "")
                       if args.schedule == "pyramid" else "runs/stageA_chain_gate")
    out_dir = ROOT / out
    if args.summarize:
        summarize(out_dir)
        return

    cfg = load_config(args.guard)
    spec = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    scaffold = json.loads((P7 / "scaffold_struct.json").read_text(encoding="utf-8"))
    turns = load_turns(P7 / "fixture" / "host_doc.jsonl")
    fracs = tuple(cfg["schedule"]["code"]["stage_fracs"])

    if args.schedule == "pyramid":
        if not args.views:
            raise SystemExit("--schedule pyramid requires --views ARM (see gen_pyramid_views.py "
                             "--list)")
        from verify_pyramid_schedule import load_arm                          # noqa: E402
        V = cfg["schedule"]["code"]["V"]
        views, vmeta = load_arm(args.views, V, 2, turns)
        vmeta["V"] = V
        guards = preflight_pyramid(spec, turns, views, vmeta, cfg)
        passes = build_passes_pyramid(views, fracs, args.stage_map)
        guards["stage_map"] = args.stage_map
        guards["stage_counts"] = {s: sum(1 for p in passes if p["stage"] == s)
                                  for s in RUBRICS}
        print(f"(T) output-demand ladder by {args.stage_map}: {guards['stage_counts']}")
    else:
        guards, sch, _, _ = preflight(spec, turns, scaffold, cfg)
        passes = build_passes(sch, scaffold)

    # forcing-boundary audit (E2PRIME-CRITERION §2): the recorder prompt may not name the probe.
    probe_tokens = ["REGION_SURCHARGE_CENTS", "RECONCILIATION_ADDER_CENTS",
                    "compute_line_surcharge", "2353", "988", "1365", "region 23", "surcharge"]
    sysp = _system_prompt(cfg, "verbatim")
    leaks = [t for t in probe_tokens if t.lower() in sysp.lower()]
    assert not leaks, f"FORCING-BOUNDARY VIOLATION in the recorder system prompt: {leaks}"
    print(f"(F) forcing boundary: recorder system prompt names no probe token  PASS")

    if args.dry_run:
        print("\n" + "=" * 78 + "\nDRY RUN — no model served\n" + "=" * 78)
        print(f"\nschedule={args.schedule}"
              + (f" views={args.views}" if args.schedule == "pyramid" else "")
              + f": K={len(passes)} "
              f"(A={sum(p['phase'] == 'A' for p in passes)}, B={sum(p['phase'] == 'B' for p in passes)})")
        for p in passes:
            sg = p.get("stage") or _stage(p["k"], p["K"], fracs)
            lv = f" L{p['level']}" if p.get("level") else ""
            cr = f" {p['compression_ratio']:>5.1f}x" if p.get("compression_ratio") else ""
            print(f"   pass {p['k']:>2}/{len(passes)}{lv} phase={p['phase']} "
                  f"stage={sg:<9}{cr} view={p['view_tokens']}tok")
        print(f"\n--- RECORDER SYSTEM PROMPT (stage=scaffold) ---\n{_system_prompt(cfg, 'scaffold')}")
        print(f"\n--- RECORDER USER PROMPT (pass 1, view elided) ---\n"
              f"{_user_prompt(1, len(passes), IntegrationState(guard='strict').render(), '<VIEW>')}")
        print(f"\n--- CLOSING SYSTEM ---\n{CLOSE_SYSTEM}")
        print(f"\n--- CLOSING USER (state elided) ---\nFINAL STATE:\n<STATE>\n\n"
              f"Question: {spec['scoring_question']}\n"
              f"Reason briefly from the state, then end with: ANSWER: <integer>")
        print(f"\naddendum commit state: {addendum_commit_gate(allow_uncommitted=True)}")
        print("\nDry run OK. Nothing was served, nothing was written.")
        return

    gate = addendum_commit_gate(args.allow_uncommitted_addendum)
    # A --model run is a probe by construction: it is not a pre-registered arm, so it can never be
    # verdict-eligible regardless of the addendum commit gate. Neither is a pyramid run — the
    # addendum froze the D25 schedule, so a different schedule is a new experiment, never poolable
    # with (or mistakable for) the Stage-A 0/10 verdict.
    verdict_eligible = (gate["committed"] and not args.max_passes and not args.model
                        and args.schedule == "d25" and not args.guard)
    out_dir.mkdir(parents=True, exist_ok=True)

    seeds = [s for s, _ in SAMPLED_DRAWS]
    if args.seeds:
        seeds = []
        for part in args.seeds.split(","):
            if "-" in part:
                a, b = part.split("-")
                seeds += list(range(int(a), int(b) + 1))
            else:
                seeds.append(int(part))
    draws = [] if args.anchor_only else [(s, 0.7) for s in seeds]
    if not args.no_anchor:
        draws.append(ANCHOR_DRAW)

    exe = ROOT / "models" / "llamacpp" / "llama-server.exe"
    if args.model:
        if not args.label:
            raise SystemExit("--model requires --label")
        _p = Path(args.model)
        arms = [args.label]
        arm_models = {args.label: _p if _p.is_absolute() else ROOT / _p}
    else:
        arms = ["student", "floor"] if args.arm == "both" else [args.arm]
        arm_models = ARMS
    for arm in arms:
        model = arm_models[arm]
        if not model.exists():
            raise SystemExit(f"model not found: {model}")
        print(f"\n{'=' * 78}\nARM: {arm}  ({model.relative_to(ROOT) if ROOT in model.parents else model})"
              f"\n{'=' * 78}", flush=True)
        manifest = {
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "arm": arm, "verdict_eligible": verdict_eligible,
            "scale_rung_probe": bool(args.model),
            "probe_note": ("NOT a pre-registered Stage-A arm; never poolable with the frozen "
                           "0/10 verdict" if args.model else None),
            "schedule_kind": args.schedule,
            "views_arm": args.views,
            "stage_map": args.stage_map if args.schedule == "pyramid" else None,
            "guard_override": args.guard,
            "run_class": guards.get("run_class"),
            "run_class_reasons": guards.get("run_class_reasons"),
            "split_intact": guards.get("split_intact"),
            "early_exposure": guards.get("early_exposure"),
            "schedule_note": ("pyramid schedule (docs/SCHEDULE-DISCREPANCY-2026-07-30.md); NOT the "
                              "addendum-frozen D25 protocol, so never verdict-eligible and never "
                              "poolable with the Stage-A verdict"
                              if args.schedule == "pyramid" else None),
            "addendum_commit_gate": gate,
            "protocol": {"guard": cfg["harness"]["guard"], "op_cap": cfg["harness"]["op_cap"],
                         "state_budget_tok": cfg["harness"]["state_budget_tok"],
                         "max_tokens": args.max_tokens,
                         "closing_max_tokens": args.closing_max_tokens,
                         "max_passes": args.max_passes,
                         "sampled_draws": SAMPLED_DRAWS, "anchor": list(ANCHOR_DRAW),
                         "denominator": "the 10 sampled draws; the anchor is never pooled"},
            "need_class": ADDENDUM_NEED_CLASS,
            "structural_objective": cfg["task"]["structural_objective"],
            "serving": {"ctx": args.ctx, "n_gpu_layers": args.ngl, "threads": args.threads,
                        "llama_server": llama_server_version(exe)},
            "guards": guards,
            "hashes": {
                "fixture_spec": sha256_file(P7 / "fixture" / "fixture_spec.json"),
                "host_doc": sha256_file(P7 / "fixture" / "host_doc.jsonl"),
                "scaffold_struct": sha256_file(P7 / "scaffold_struct.json"),
                "runner": sha256_file(Path(__file__).resolve()),
                "addendum": sha256_file(ADDENDUM),
                "teacher_config": sha256_file(HERE / "teacher_config.yaml"),
                "editops": sha256_file(ROOT / "src" / "pca" / "editops.py"),
                "teacher_gen": sha256_file(ROOT / "src" / "pca" / "teacher_gen.py"),
                "planted": sha256_file(ROOT / "src" / "pca" / "planted.py"),
                "pyramid_views": (sha256_file(HERE / "pyramid_views" / f"{args.views}.json")
                                  if args.schedule == "pyramid" and args.views else None),
                "grammar": hashlib.sha256(GRAMMAR.encode()).hexdigest(),
                "rubrics": {k: hashlib.sha256(v.encode()).hexdigest() for k, v in RUBRICS.items()},
                "model": None if args.skip_model_hash else sha256_file(model),
            },
            "model": {"path": str(model), "bytes": model.stat().st_size},
            "git": {"commit": _git("rev-parse", "HEAD"), "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
                    "dirty": _git("status", "--porcelain")},
        }
        (out_dir / f"manifest_{arm}.json").write_text(
            json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")

        server = LlamaServer(str(exe), str(model), ctx=args.ctx, port=args.port,
                             threads=args.threads, n_gpu_layers=args.ngl)
        server.ensure_running()
        print(f"served: ctx={args.ctx} ngl={args.ngl} port={args.port}", flush=True)
        try:
            for seed, temp in draws:
                prefix = "smoke_" if args.max_passes else ""
                out_path = out_dir / f"{prefix}{arm}_s{seed}_t{temp:g}.json"
                if out_path.exists():
                    try:
                        if json.loads(out_path.read_text(encoding="utf-8")).get("complete"):
                            print(f"[skip] {out_path.name} already complete", flush=True)
                            continue
                    except json.JSONDecodeError:
                        pass
                    print(f"[redo] {out_path.name} incomplete -> re-running from pass 1", flush=True)
                kind = "ANCHOR (temp 0, never pooled)" if (seed, temp) == ANCHOR_DRAW else "sampled"
                print(f"\n--- {arm} seed={seed} temp={temp} [{kind}] ---", flush=True)
                run_draw(server, passes, spec, cfg, seed, temp, out_path,
                         {"arm": arm, "model": str(model), "verdict_eligible": verdict_eligible,
                          "addendum_committed": gate["committed"]},
                         args.max_tokens, args.closing_max_tokens, args.max_passes)
        finally:
            server.stop()
            time.sleep(3)   # one model at a time: let the VRAM free before the next arm

    print("\nBattery finished. Run --summarize for the per-seed table. Mechanical candidates "
          "REQUIRE hand verification before any verdict is reported.")


if __name__ == "__main__":
    main()
