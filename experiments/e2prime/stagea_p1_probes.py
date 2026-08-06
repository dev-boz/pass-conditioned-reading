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

  P1f — own-scaffold fill (handoff 07-28 queue #1) + the owed fresh-seed confirming run:
        the model scaffolds a Phase-A view itself, then fills the pass-26 tile into the state
        IT built, paired per seed. k=4 is the Phase-A pass whose view carries
        fulfillment/line_quote.py and the adder inline; k=2 carries neither, so its paired fill
        arm is a no-home control the model generated for itself — the first non-oracle test of
        the home-availability mechanism. Adds `ctrl8_confirm` on fresh seeds (use --seeds 11-20).

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
from pca.teacher_gen import GRAMMAR, _system_prompt, _user_prompt        # noqa: E402
from pca.textutils import n_tokens                                      # noqa: E402
from verify_fixture import load_turns                                    # noqa: E402
from analyze_chain_gate import rescore                                   # noqa: E402
from stagea_chain_gate import load_config, preflight, build_passes       # noqa: E402

MODELS = {
    "student": ROOT / "runs" / "stageA_coupled_v2" / "stageA_v2-f16.gguf",
    "qwen3b": ROOT / "models" / "Qwen2.5-3B-Instruct-f16.gguf",
    # Q4 caveat stands (07-26 arbitration §6): quantization is a live suspect for op-format
    # collapse, so a 7B-Q4 format failure is inconclusive, not evidence.
    "qwen7b": ROOT / "models" / "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
    # 14B does not fit the 1080 Ti at full offload (07-29: exceeded the 300 s health timeout at
    # --ctx 8192 --ngl 99). Usable with PARTIAL offload — for the close-only probe that is fine,
    # since a full arm there is ten calls rather than 630 passes.
    "qwen14b": ROOT / "models" / "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
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

# P1g (maintainer, 2026-07-29) — the two prompt-level repairs the 07-29 findings point at, plus a
# proper test of the "wait for the verbatim pass" intuition. All three name no probe token; the
# forcing-boundary assert in probe_cells() covers them like every other prompt here.
#
# ANTI_GRIND targets the measured waste: 26% of Phase-B REPLACEs rewrote an entry to byte-identical
# text, 10% clobbered an unrelated entry (HOME-AVAILABILITY-RESULTS.md §4).
ANTI_GRIND = (" Do not rewrite an entry unless this view changes what that entry says. "
              "Re-emitting an entry with the same content, or with only cosmetic detail added, "
              "wastes the pass.")

# SALIENCE targets the mechanism: the tile is 94% boilerplate and the policy records it faithfully
# because \"exact values, names and quotes\" describes boilerplate perfectly (§6).
SALIENCE = (" Not everything in a view is worth recording. Prefer what a later reader could not "
            "reconstruct on its own: named constants and their values, what a routine computes, "
            "and how one unit's values feed another. Members of a repeated pattern are already "
            "covered by the entry that names the pattern; do not record them one by one.")

# DEFER is the maintainer's \"wait until the verbatim pass for verified values\" idea in the form
# the evidence supports: the failure at pass 2 was not that Phase A recorded a value, it was that
# it compressed a lookup table to its RANGE (binding survived 1/11 vs the standalone scalar 8/11,
# §3). So the instruction forbids lossy compression and asks for an explicit placeholder instead.
DEFER = (" If this view shows values you cannot record exactly and in full, do not compress them "
         "to a range, a count, or an example. Name what is missing and leave an explicit "
         "placeholder for the later pass that will carry it.")

# P1h (maintainer, 2026-07-29): "it CAN record values early — it just needs to VERIFY them later.
# A value recorded early is written 988* and the star means confirm this on a later pass."
# So: provisional capture + a confirmation obligation, not deferral. Two halves, spliced into the
# two stages that would carry them. Neither names a probe token.
PROVISIONAL = (" Record values as soon as you see them, but mark any value you have not yet seen "
               "in a full-detail view by putting an asterisk immediately after it (for example "
               "count: 47*). The asterisk means the value is provisional and a later pass must "
               "confirm it. Never mark a value you copied from a full-detail view.")

CONFIRM = (" This view is full detail. Any provisional value in your state that this view covers "
           "must now be settled: if the view confirms it, REPLACE the entry with the asterisk "
           "removed; if the view contradicts it, REPLACE it with the correct value. Leave "
           "provisional marks alone for regions this view does not cover.")

# P1e (maintainer hypothesis, 2026-07-28): "the training almost just needs to be a prompt telling
# the model what to do and what not to do — if the model knew the architecture and its position it
# could almost do it on its own, or at least a larger model should." This system prompt EXPLAINS
# the architecture and derives the behaviour from position, instead of the terse per-stage rubric.
# Forcing boundary: names the protocol, never the probe (audited like every other prompt here).
EXPLAINED_ROLE = (
    "You are one pass in a K-pass scheduled read of a long document. Early passes see broad, "
    "heavily compressed views of the whole document; later passes see small regions verbatim. "
    "You maintain the single persistent integration state; downstream questions about the "
    "document's specifics will be answered from that state alone, with no access to the source."
    "\n\nHow to work, by position:"
    "\n- EARLY passes (k small): your job is structure, not values. Create one entry per "
    "region/module naming what it defines, so every later pass has an entry to put specifics "
    "into. It is correct to create entries whose values you have not seen yet."
    "\n- LATE passes (k large): your job is specifics. Find the entry each fact belongs to and "
    "REPLACE it with the exact values, names and quotes from the view. If a fact has no "
    "matching entry, ADD one."
    "\n\nDo not rewrite entries the view says nothing about. Do not summarize away exact "
    "values. Never invent values that are not in the view.")


def explained_system(cfg: dict) -> str:
    return (f"{GRAMMAR}\n\n{EXPLAINED_ROLE}\n\n"
            f"State budget: stay under {cfg['harness']['state_budget_tok']} tokens; "
            f"consolidate rather than truncate. Output ONLY edit-op lines.")


# Placeholder emissions, for P1b/P1d readings. Loose on purpose; hand-reading arbitrates.
_PLACEHOLDER = re.compile(
    r"\[TBD[^\]]*\]|\bTBD\b|to be (?:determined|filled|resolved)|insert (?:value|here)"
    r"|values? pending|<[a-z_]{3,}>", re.I)

PROBE_TOKENS = ["REGION_SURCHARGE_CENTS", "RECONCILIATION_ADDER_CENTS",
                "compute_line_surcharge", "2353", "988", "1365", "region 23", "surcharge"]

# What a home FOR THE CHAIN'S FACTS looks like, for post_metrics.n_target_home. Scoring only —
# never spliced into a prompt (the forcing-boundary assert below covers the prompts).
TARGET_HOME_TOKENS = ["line_quote", "compute_line_surcharge", "RECONCILIATION_ADDER_CENTS"]

# P1h provisional mark: a digit immediately followed by an asterisk (988*). Deliberately narrow —
# markdown emphasis and footnote stars do not match, and hand-reading arbitrates as always.
_PROVISIONAL_MARK = re.compile(r"\d\*")


# --------------------------------------------------------------------------- materials
def harness_materials() -> tuple[dict, dict, dict, dict]:
    """Frozen cfg + the pass-26 tile + a Phase-A scaffold pass, via the gate runner's loaders."""
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
    pass2 = passes[1]
    assert pass2["phase"] == "A" and pass2["k"] == 2, (pass2["phase"], pass2["k"])
    assert "line_quote" not in pass2["view_text"], "p2 was the no-home control; it now has one"
    pass4 = passes[3]
    assert pass4["phase"] == "A" and pass4["k"] == 4, (pass4["phase"], pass4["k"])
    assert "fulfillment/line_quote.py" in pass4["view_text"], "pass-4 view lost the target module"
    assert "1365" in pass4["view_text"], "pass-4 view lost the inline adder value"
    assert "988" not in pass4["view_text"], "table value leaked into the pass-4 view"
    pass12 = passes[11]
    assert pass12["phase"] == "B" and pass12["k"] == 12, (pass12["phase"], pass12["k"])
    assert "23: 988" in pass12["view_text"], "pass-12 tile lost the queried mapping"
    return cfg, spec, tile26, pass2, pass4, pass12


# --------------------------------------------------------------------------- pyramid materials
def pyramid_materials(arm: str = "graded") -> tuple[dict, dict, list[dict], dict]:
    """Frozen pyramid views for one compressor arm, plus the NESTED CHAINS that make a resolution
    probe possible.

    Every level tiles the whole document, so a given source turn is covered exactly once per level.
    The six views covering it are therefore the SAME material at six resolutions — and because each
    tile renders to the same budget V, they are also near-identical in LENGTH. That controls the
    confound the padded probe was built for (length vs content) for free, and it is the thing the
    D25 schedule could never offer: there, k took two values and neither was a resolution.
    """
    from verify_pyramid_schedule import load_arm                              # noqa: E402

    cfg = load_config()
    spec = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
    turns = load_turns(P7 / "fixture" / "host_doc.jsonl")
    views, vmeta = load_arm(arm, cfg["schedule"]["code"]["V"], 2, turns)
    n_levels = len({v["level"] for v in views})

    qcode, tval = spec["queried_code"], spec["table_value_for_queried"]
    binding_turn = next(i for i, t in enumerate(turns) if f"{qcode}: {tval}" in t["text"])
    fn_turn = next(i for i, t in enumerate(turns) if "compute_line_surcharge" in t["text"])

    def chain(idx: int) -> list[dict]:
        c = [v for v in views if v["idx_lo"] <= idx <= v["idx_hi"]]
        c.sort(key=lambda v: v["level"])
        assert len(c) == n_levels, f"turn {idx} covered {len(c)}x, expected {n_levels}"
        return c

    meta = {"arm": arm, "compressor": vmeta.get("compressor_name"), "K": len(views),
            "n_levels": n_levels, "binding_turn": binding_turn, "fn_turn": fn_turn,
            "binding_chain": chain(binding_turn), "fn_chain": chain(fn_turn)}
    return cfg, spec, views, meta


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


def run_cell(server, label: str, system: str, user_k: int, builder, view: str,
             seeds: list[int], rec: dict, user_K: int = 31) -> dict:
    """One condition: n draws, each from a FRESH state built by `builder(seed, rec)`.

    The builder takes the seed so a cell can be PAIRED — each draw run against the state that
    same seed produced in an earlier cell (the own-scaffold cells), not against a fixed state.
    For fixed-state cells the builder ignores both arguments and this is identical to before.
    Dual-scored."""
    cell = {"n": 0, "system": system, "draws": []}
    for seed in seeds:
        st = builder(seed, rec)
        if cell["n"] == 0:
            cell["state_text"] = st.render()          # representative, for the summary view
            cell["state_tokens"] = n_tokens(st.render())
        pre_render = st.render()
        pre_by_id = {e["id"]: e["text"] for e in st.entries}
        user = _user_prompt(user_k, user_K, pre_render, view)
        resp = server.chat(system, user, max_tokens=MAX_TOKENS, temperature=TEMP, seed=seed)
        res = parse_ops(resp["text"], st.ids(), st.next_id)
        applied = st.apply(res.ops[:OP_CAP])
        post = st.render()
        d = {"seed": seed,
             "emitted": _score_text(resp["text"]),
             "applied": _score_text(post),
             # Structure metrics for home-building cells (P1e H1): did the pass leave
             # module-keyed entries later passes could land values in?
             "post_metrics": {
                 "n_entries": len(st.entries),
                 "n_module_entries": sum(1 for e in st.entries if ".py" in e["text"]),
                 "n_defines_entries": sum(1 for e in st.entries
                                          if "defines" in e["text"].lower()),
                 # A home for the CHAIN'S module specifically. n_module_entries counts any
                 # ".py" mention and so scores a bare path list as 20 homes; this asks whether
                 # the entry the pass-26 tile needs actually exists.
                 "n_target_home": sum(1 for e in st.entries
                                      if any(t in e["text"] for t in TARGET_HOME_TOKENS)),
                 # P1h: provisional marks — a digit immediately followed by '*'.
                 "n_provisional_marks": len(_PROVISIONAL_MARK.findall(post))},
             "pre_state_text": pre_render, "pre_state_tokens": n_tokens(pre_render),
             "n_candidate_lines": res.candidate_lines, "n_valid": res.valid,
             "n_ops_applied": applied, "n_blocked": len(st.last_report["blocked"]),
             # Grinding metrics (P1g): a REPLACE whose new text equals the entry's prior text is
             # a pure no-op. Measured against the PRE-state, which is why it is computed here.
             "n_replace": sum(1 for o in res.ops if o["op"] == "REPLACE"),
             "n_replace_noop": sum(1 for o in res.ops if o["op"] == "REPLACE"
                                   and (o.get("text") or "").strip()
                                   == pre_by_id.get(o.get("id"), "\x00").strip()),
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
def own_scaffold(src_cell: str):
    """Builder for a PAIRED cell: seed s runs against the state seed s itself produced in
    `src_cell`. Non-oracle by construction — the state is the model's own prior-pass output,
    so the fill test asks whether it can use the scaffold it actually writes."""
    def build(seed: int, rec: dict) -> IntegrationState:
        cell = rec["conditions"][src_cell]
        draw = next(d for d in cell["draws"] if d["seed"] == seed)
        lines = [ln for ln in draw["post_state"].splitlines() if ln.strip()]
        if not lines:                       # a pass that emitted nothing leaves an empty state
            return IntegrationState(guard="strict")
        return state_from_lines(lines)
    build.src_cell = src_cell               # marks the cell as unresolvable at dry-run time
    return build


def fixed(fn):
    """Adapt a zero-arg state builder to the (seed, rec) signature."""
    return lambda seed, rec: fn()


def probe_cells(probe: str, cfg: dict, tile26: dict, pass2: dict,
                pass4: dict | None = None, pass12: dict | None = None) -> tuple[dict, dict]:
    """Returns ({cell_label: (system, user_k, state_builder, view_text)}, meta_extras)."""
    sys_current = _system_prompt(cfg, "verbatim")
    anchor = "NO_CHANGE if this view adds nothing your state needs."
    assert anchor in sys_current, "verbatim rubric drifted; ADD-license splice has no anchor"
    sys_addlic = sys_current.replace(anchor, anchor + ADD_LICENSE)
    sys_explained = explained_system(cfg)
    sys_scaffold = _system_prompt(cfg, "scaffold")
    sys_antigrind = sys_current.replace(anchor, anchor + ANTI_GRIND)
    sys_salience = sys_current.replace(anchor, anchor + SALIENCE)
    sys_both = sys_current.replace(anchor, anchor + ANTI_GRIND + SALIENCE)
    sc_anchor = "Do not chase specifics yet."
    assert sc_anchor in sys_scaffold, "scaffold rubric drifted; DEFER splice has no anchor"
    sys_defer = sys_scaffold.replace(sc_anchor, sc_anchor + DEFER)
    for sysp in (sys_current, sys_addlic, sys_explained, sys_scaffold,
                 sys_antigrind, sys_salience, sys_both, sys_defer):
        leaks = [t for t in PROBE_TOKENS if t.lower() in sysp.lower()]
        assert not leaks, f"forcing-boundary violation in probe system prompt: {leaks}"

    tile = tile26["view_text"]
    s25 = s2_pass26_state_lines()[:25]
    if probe == "p1a":
        pad = padding_lines(n_tokens("\n".join(s25)))
        cells = {
            "empty_current": (sys_current, 26, fixed(lambda: IntegrationState(guard="strict")),
                              tile),
            "empty_addlicense": (sys_addlic, 26, fixed(lambda: IntegrationState(guard="strict")),
                                 tile),
            "s25_current": (sys_current, 26, fixed(lambda: state_from_lines(s25)), tile),
            "s25_addlicense": (sys_addlic, 26, fixed(lambda: state_from_lines(s25)), tile),
            "pad25_current": (sys_current, 26, fixed(lambda: state_from_lines(pad)), tile),
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
            "slots_current": (sys_current, 26, fixed(lambda: state_from_lines(SLOT_LINES)), tile),
            "ctrl8_noslot": (sys_current, 26, fixed(lambda: state_from_lines(CTRL8_LINES)), tile),
            "pad8_current": (sys_current, 26, fixed(lambda: state_from_lines(pad8)), tile),
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
        cells = {f"k{k}": (sys_current, k, fixed(lambda: state_from_lines(s25)), tile)
                 for k in (5, 15, 26)}
        meta = {"oracle": False,
                "question": "does the position channel (k/K) do any conditioning work, holding "
                            "rubric, state and view fixed? (= constructed-pairs falsifier F2)",
                "note": "k5/k15 pair a verbatim rubric with early-pass labels — a combination "
                        "training never showed; that mismatch IS the probe"}
    elif probe == "p1e":
        pA = pass2["view_text"]
        cells = {
            # H1 — home-leaving: Phase-A compressed view, empty state. Trained rubric vs the
            # architecture-explaining prompt. Scored on post_metrics (module-keyed entries).
            "h1_trained": (sys_scaffold, 2, fixed(lambda: IntegrationState(guard="strict")), pA),
            "h1_explained": (sys_explained, 2, fixed(lambda: IntegrationState(guard="strict")),
                             pA),
            # H2 — fill: pass-26 tile against the ctrl8 homes (oracle, declared) and empty.
            "h2homes_trained": (sys_current, 26, fixed(lambda: state_from_lines(CTRL8_LINES)),
                                tile),
            "h2homes_explained": (sys_explained, 26,
                                  fixed(lambda: state_from_lines(CTRL8_LINES)), tile),
            "h2empty_explained": (sys_explained, 26,
                                  fixed(lambda: IntegrationState(guard="strict")), tile),
        }
        meta = {"oracle": True,
                "question": "maintainer hypothesis: if the model is TOLD the architecture and "
                            "its position, can it home-build and fill without training — or at "
                            "least at larger scale?",
                "oracle_note": "h2homes cells reuse the declared-oracle ctrl8 state; h1 cells "
                               "are oracle-free",
                "explained_role": EXPLAINED_ROLE,
                "q4_caveat": "qwen7b is Q4_K_M — an op-format failure there is inconclusive "
                             "(07-26 arbitration §6 quantization caveat)"}
    elif probe == "p1f":
        assert pass4 is not None
        pA2, pA4 = pass2["view_text"], pass4["view_text"]
        cells = {
            # H1 — the model's OWN scaffold, at the two Phase-A passes that matter:
            #   k=2 shows REGION_SURCHARGE_CENTS' module but NOT fulfillment/line_quote.py
            #   k=4 shows fulfillment/line_quote.py, RECONCILIATION_ADDER_CENTS = 1365 inline,
            #        and names compute_line_surcharge
            # Empty start state (declared simplification: in the real chain passes 1-3 have run).
            "h1_p2": (sys_scaffold, 2, fixed(lambda: IntegrationState(guard="strict")), pA2),
            "h1_p4": (sys_scaffold, 4, fixed(lambda: IntegrationState(guard="strict")), pA4),
            # H2 — fill the pass-26 tile into the model's own scaffold, PAIRED by seed.
            # The p2 arm is the built-in no-home control: same model, same fill pass, its own
            # scaffold, differing only in whether the Phase-A view covered the target module.
            "h2own_p4": (sys_current, 26, own_scaffold("h1_p4"), tile),
            "h2own_p2": (sys_current, 26, own_scaffold("h1_p2"), tile),
            # The confirming run owed under the three-tier rule: ctrl8 at FRESH seeds.
            "ctrl8_confirm": (sys_current, 26, fixed(lambda: state_from_lines(CTRL8_LINES)),
                              tile),
        }
        meta = {"oracle": "ctrl8_confirm only",
                "question": "can a model fill the homes ITS OWN scaffold pass built — and does "
                            "fill track whether that scaffold saw the target module?",
                "design": {
                    "h1_p4": "Phase-A view k=4 holds fulfillment/line_quote.py + the adder "
                             "value inline; the scaffold rubric says not to chase specifics, "
                             "so this cell also measures whether the rubric suppresses a value "
                             "sitting in front of it",
                    "h1_p2": "Phase-A view k=2 has no line_quote section — the paired fill "
                             "arm is therefore a no-home control the model built itself",
                    "pairing": "h2own_* draw with seed s runs against the state seed s produced "
                               "in the corresponding h1_* cell (non-oracle, self-generated)",
                    "ctrl8_confirm": "same oracle state as P1b's ctrl8 / P1e's h2homes_trained "
                                     "but FRESH seeds — discharges the determinism-duplicate "
                                     "note (P1-PROBE-RESULTS reading 4)",
                    "empty_start": "h1 cells start from an empty state; in the chain passes "
                                   "1-3 precede pass 4. Declared simplification."},
                "prediction": "if home-availability is the mechanism, h2own_p4 fills and "
                              "h2own_p2 does not, with no oracle anywhere in the contrast"}
    elif probe == "p1g":
        assert pass4 is not None
        pA2, pA4 = pass2["view_text"], pass4["view_text"]
        cells = {
            # Rebuild the same scaffold p1f used (same model, prompt and seeds => same states),
            # so the four fill rubrics below all start from an IDENTICAL, self-built state and
            # differ only in the spliced sentence. `fill_base` doubles as a determinism check
            # against p1f's h2own_p4.
            "h1_p4": (sys_scaffold, 4, fixed(lambda: IntegrationState(guard="strict")), pA4),
            "fill_base": (sys_current, 26, own_scaffold("h1_p4"), tile),
            "fill_antigrind": (sys_antigrind, 26, own_scaffold("h1_p4"), tile),
            "fill_salience": (sys_salience, 26, own_scaffold("h1_p4"), tile),
            "fill_both": (sys_both, 26, own_scaffold("h1_p4"), tile),
            # The deferral arm, at the pass where the binding actually died (k=2 holds the whole
            # table). Scored on the audited mapping flag + placeholder emissions, not on the fill.
            "p2_base": (sys_scaffold, 2, fixed(lambda: IntegrationState(guard="strict")), pA2),
            "p2_defer": (sys_defer, 2, fixed(lambda: IntegrationState(guard="strict")), pA2),
        }
        meta = {"oracle": False,
                "question": "can the two measured pathologies be fixed by PROMPT alone on frozen "
                            "weights: (a) grinding/no-op rewrites, (b) recording the view's bulk "
                            "instead of its load-bearing content — and (c) does forbidding lossy "
                            "compression at Phase A preserve the key->value binding?",
                "splices": {"ANTI_GRIND": ANTI_GRIND, "SALIENCE": SALIENCE, "DEFER": DEFER},
                "baseline": "p1f h2own_p4 = 0/10 acquisition with 8/10 dedicated homes present",
                "readings": {
                    "grinding_is_promptable": "fill_antigrind cuts no-op REPLACEs vs fill_base",
                    "salience_is_promptable": "fill_salience/both acquire 1365 where base is 0/10",
                    "binding_is_promptable": "p2_defer records the queried mapping or leaves a "
                                             "placeholder where p2_base compresses to a range"},
                "note": "prompt-only, frozen weights. A negative here is informative: it moves "
                        "these repairs from the prompt column to the training column."}
    elif probe == "p1h":
        # The provisional-mark chain, run on the pass pair that actually carries the fixture's
        # weakest fact: pass 2 shows the whole table in a COMPRESSED Phase-A view (where the
        # binding died 1/11, compressed to a range), pass 12 shows the same table VERBATIM.
        # So pass 2 is where a value would be recorded provisionally and pass 12 is where the
        # obligation to confirm it comes due.
        pA2 = pass2["view_text"]
        tile12 = pass12["view_text"]
        sys_prov = sys_scaffold.replace(sc_anchor, sc_anchor + PROVISIONAL)
        sys_confirm = sys_current.replace(anchor, anchor + CONFIRM)
        for sysp in (sys_prov, sys_confirm):
            leaks = [t for t in PROBE_TOKENS if t.lower() in sysp.lower()]
            assert not leaks, f"forcing-boundary violation: {leaks}"
        cells = {
            # k=2, compressed view of the table.
            "p2_plain": (sys_scaffold, 2, fixed(lambda: IntegrationState(guard="strict")), pA2),
            "p2_provisional": (sys_prov, 2, fixed(lambda: IntegrationState(guard="strict")), pA2),
            # k=12, the same table verbatim, run against each seed's own pass-2 state.
            "p12_plain_after_plain": (sys_current, 12, own_scaffold("p2_plain"), tile12),
            "p12_confirm_after_prov": (sys_confirm, 12, own_scaffold("p2_provisional"), tile12),
            # Control: the confirm rubric with nothing marked to confirm — isolates whether any
            # gain comes from the MARK or just from a second, more insistent recording demand.
            "p12_confirm_after_plain": (sys_current.replace(anchor, anchor + CONFIRM), 12,
                                        own_scaffold("p2_plain"), tile12),
        }
        meta = {"oracle": False,
                "question": "maintainer's mechanism: record early but mark unconfirmed values "
                            "(988*), then settle them on the full-detail pass. Does the mark "
                            "survive, does it get resolved, and does the key->value binding "
                            "survive better than without it?",
                "splices": {"PROVISIONAL": PROVISIONAL, "CONFIRM": CONFIRM},
                "why_this_pass_pair": "k=2 is the compressed view of the table where the binding "
                                      "died 1/11 (compressed to a range); k=12 is the SAME table "
                                      "verbatim, so the confirmation obligation is satisfiable",
                "readings": {
                    "mark_is_emitted": "p2_provisional shows asterisked values where p2_plain "
                                       "compresses to a range",
                    "mark_is_resolved": "p12_confirm_after_prov removes marks and keeps values",
                    "mark_is_load_bearing": "p12_confirm_after_prov beats "
                                            "p12_confirm_after_plain — otherwise the gain is the "
                                            "second demand, not the mark"}}
    else:
        raise SystemExit(f"unknown probe {probe}")
    return cells, meta


def _p1h_pyramid_cells(cfg: dict, pmeta: dict, chain: list[dict], sysfor, K: int,
                       nlv: int) -> tuple[dict, dict]:
    """P1h on the PYRAMID — the maintainer's provisional-mark mechanism, on a ladder that finally
    supports it.

    The mechanism is 'record a value as soon as you see it, mark it 988* as unconfirmed, and settle
    it on the pass that shows it in full detail'. On the D25 schedule that story had nowhere to
    live: there were two resolutions, and the handoff held this probe back for exactly that reason.
    The pyramid supplies the missing ladder — but only for a compressor that DEGRADES the value
    rather than dropping it. Measured across the arms:

        llm_general  the queried value survives as a RANGE at levels 1,2,3,5 and exactly at 6
                     -> four coarse passes where a provisional mark is the right move
        graded       ABSENT at level 1 (its module sits at sigma 5, declaring the table's name and
                     no values) and exact from level 2 -> nothing to mark
        extractive   absent until level 6 -> nothing to mark

    Only llm_general supplies a lossy-then-exact ladder, so the probe runs there and refuses
    elsewhere rather than silently testing a mechanism whose precondition is absent. That the
    general compressor is the one that degrades the value to a range is not a coincidence: it is
    the archived table-to-range pathology, reproduced by the compressor rather than the recorder.
    """
    lossy = [v for v in chain[:-1]
             if "988" in v["view_text"] and "23: 988" not in v["view_text"]
             and "23:988" not in v["view_text"]]
    if not lossy:
        raise SystemExit(
            f"arm '{pmeta['arm']}' has no LOSSY view of the queried value, so the provisional-mark "
            f"mechanism has nothing to mark: its levels either drop the value entirely or carry "
            f"it exactly, with no degraded form in between. Use --views llm_general (the value "
            f"survives as a RANGE at levels 1-5 and exactly at level 6).")
    coarse, fine = lossy[0], chain[-1]
    assert "23: 988" in fine["view_text"] or "23:988" in fine["view_text"], \
        "the finest view must carry the binding exactly, or confirmation is unsatisfiable"

    sys_coarse = sysfor(coarse["level"])
    sys_fine = sysfor(fine["level"])
    sc_anchor, vb_anchor = "Do not chase specifics yet.", \
        "NO_CHANGE if this view adds nothing your state needs."
    assert sc_anchor in sys_coarse, f"coarse view is stage {coarse['level']}; no PROVISIONAL anchor"
    assert vb_anchor in sys_fine, "fine view rubric drifted; CONFIRM splice has no anchor"
    sys_prov = sys_coarse.replace(sc_anchor, sc_anchor + PROVISIONAL)
    sys_confirm = sys_fine.replace(vb_anchor, vb_anchor + CONFIRM)
    for s in (sys_coarse, sys_fine, sys_prov, sys_confirm):
        leaks = [t for t in PROBE_TOKENS if t.lower() in s.lower()]
        assert not leaks, f"forcing-boundary violation: {leaks}"

    cv, fv = coarse["view_text"], fine["view_text"]
    empty = fixed(lambda: IntegrationState(guard="strict"))
    cells = {
        "coarse_plain": (sys_coarse, coarse["k"], empty, cv, K),
        "coarse_provisional": (sys_prov, coarse["k"], empty, cv, K),
        "fine_plain_after_plain": (sys_fine, fine["k"], own_scaffold("coarse_plain"), fv, K),
        "fine_confirm_after_prov": (sys_confirm, fine["k"],
                                    own_scaffold("coarse_provisional"), fv, K),
        # control: the CONFIRM demand with nothing marked to confirm. Separates the MARK from
        # "a second, more insistent recording demand".
        "fine_confirm_after_plain": (sys_confirm, fine["k"], own_scaffold("coarse_plain"), fv, K),
    }
    meta = {"oracle": False, "schedule": "pyramid", "views_arm": pmeta["arm"],
            "compressor": pmeta["compressor"], "K": K,
            "question": "record early and mark unconfirmed (988*), then settle it on the "
                        "full-detail pass: does the mark get emitted, does it get resolved, and "
                        "does the key->value binding survive better than without it?",
            "splices": {"PROVISIONAL": PROVISIONAL, "CONFIRM": CONFIRM},
            "ladder": {"coarse": {"level": coarse["level"], "k": coarse["k"],
                                  "ratio": coarse["compression_ratio"],
                                  "form": "value present as a RANGE, not as the binding"},
                       "fine": {"level": fine["level"], "k": fine["k"],
                                "ratio": fine["compression_ratio"], "form": "binding exact"}},
            "why_this_pass_pair": "the coarse view carries the value only in a lossy form, and the "
                                  "fine view carries it exactly — so the confirmation obligation "
                                  "is both motivated and satisfiable",
            "readings": {
                "mark_is_emitted": "coarse_provisional shows asterisked values where coarse_plain "
                                   "records the range",
                "mark_is_resolved": "fine_confirm_after_prov removes marks and keeps exact values",
                "mark_is_load_bearing": "fine_confirm_after_prov beats fine_confirm_after_plain — "
                                        "otherwise the gain is the second demand, not the mark"}}
    return cells, meta


def pyramid_probe_cells(probe: str, cfg: dict, pmeta: dict) -> tuple[dict, dict]:
    """P1d on the PYRAMID — the k-conditioning question, finally askable.

    On the D25 schedule the original P1d varied only the rendered `position: {k, K}` label while
    holding view, state and rubric fixed. It measured inert, and falsifier F2 was recorded negative.
    docs/SCHEDULE-DISCREPANCY-2026-07-30.md withdrew that negative: in training, k carried no
    information beyond "which of two sweeps am I in", so an inert channel was the only possible
    result. The pyramid gives k a real referent (22x -> 1.0x over six levels), so the probe splits
    into three questions that the old schedule could not separate:

      RES   does behaviour track the RESOLUTION of the view? Same source turn, its six nested
            covering views, each labelled with its own true k and stage. Everything moves together
            — the honest condition, and the one the architecture claims does work.
      LAB   does the LABEL alone do anything? View, state and rubric pinned to the verbatim tile;
            only `position: {k, K}` varies. This is the original F2 falsifier, re-asked on K=63.
      MIS   when label and content DISAGREE, which wins? A coarse view labelled late, and the
            verbatim view labelled k=1. Training never showed either combination; that is the probe.
    """
    from stagea_chain_gate import pyramid_stage                                # noqa: E402

    fracs = tuple(cfg["schedule"]["code"]["stage_fracs"])
    K, nlv = pmeta["K"], pmeta["n_levels"]
    chain = pmeta["binding_chain"]
    s25 = s2_pass26_state_lines()[:25]
    state = fixed(lambda: state_from_lines(s25))
    fine = chain[-1]                       # the verbatim view of the same span
    coarse = chain[0]                      # the whole document, maximally compressed

    def sysfor(level: int) -> str:
        return _system_prompt(cfg, pyramid_stage(level, nlv, fracs))

    if probe == "p1h_pyr":
        return _p1h_pyramid_cells(cfg, pmeta, chain, sysfor, K, nlv)

    cells: dict = {}
    for v in chain:                        # RES — everything moves together
        cells[f"res_L{v['level']}"] = (sysfor(v["level"]), v["k"], state, v["view_text"], K)
    for k in (1, 8, 32, K):                # LAB — only the label moves
        cells[f"lab_k{k}"] = (sysfor(fine["level"]), k, state, fine["view_text"], K)
    # MIS — label and content disagree
    cells["mis_coarseview_lateK"] = (sysfor(fine["level"]), K, state, coarse["view_text"], K)
    cells["mis_fineview_earlyK"] = (sysfor(coarse["level"]), 1, state, fine["view_text"], K)

    for label, (sysp, *_rest) in cells.items():
        leaks = [t for t in PROBE_TOKENS if t.lower() in sysp.lower()]
        assert not leaks, f"forcing-boundary violation in {label}: {leaks}"

    meta = {"oracle": False, "schedule": "pyramid", "views_arm": pmeta["arm"],
            "compressor": pmeta["compressor"], "K": K, "n_levels": nlv,
            "question": "with k finally indexing a real resolution ladder, does the conditioning "
                        "channel do any work — via the label, via the view, or neither?",
            "ladder": [{"level": v["level"], "k": v["k"], "ratio": v["compression_ratio"],
                        "view_tokens": v["view_tokens"],
                        "stage": pyramid_stage(v["level"], nlv, fracs),
                        "holds_binding": f"{23}: {988}" in v["view_text"]} for v in chain],
            "controls": {
                "length": "every view in the RES ladder renders to the same budget V, so the "
                          "ladder varies resolution with length near-constant",
                "state": "identical 25-entry archived state in every cell",
                "LAB": "view/state/rubric pinned to the verbatim tile; only the label moves "
                       "(= original falsifier F2, re-asked on the correct schedule)"},
            "readings": {
                "resolution_does_work": "recording rises across res_L1..res_L6 beyond what view "
                                        "CONTENT alone explains",
                "label_is_inert": "lab_* flat => the position channel carries nothing, now on a "
                                  "schedule where it could have",
                "content_wins": "mis_fineview_earlyK behaves like res_L6, not like res_L1"}}
    return cells, meta


def summarize(out_dir: Path) -> None:
    for f in sorted(out_dir.glob("p1*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        print(f"\n=== {f.name} ({rec['_meta']['model_key']}) ===")
        print(f"{'cell':<20} {'n':>2} | emitted rel/fn/adder | applied rel/fn/adder | plc(e/a) "
              f"| homes | tgthome")
        for label, cell in rec["conditions"].items():
            e, a = cell["emitted_totals"], cell["applied_totals"]
            pm = [d.get("post_metrics") for d in cell["draws"]]
            homes = (sum(p["n_module_entries"] for p in pm) / len(pm)) if all(pm) else None
            tgt = (sum(1 for p in pm if p.get("n_target_home", 0) > 0)
                   if all(pm) and "n_target_home" in pm[0] else None)
            print(f"{label:<20} {cell['n']:>2} |   {e['relation']}/{e['fn_named']}/{e['adder']}"
                  f"{'':<12}|   {a['relation']}/{a['fn_named']}/{a['adder']}{'':<12}"
                  f"| {e['placeholders']}/{a['placeholders']}"
                  f" | {f'{homes:.1f}' if homes is not None else '-':>5}"
                  f" | {'-' if tgt is None else f'{tgt}/{cell["n"]}'}")
    print("\nProbe numbers. gate_legal=false. Hand-read draws before any claim; the totals are "
          "pre-filters, and every rate's denominator is the cell's n.")


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", choices=["p1a", "p1b", "p1d", "p1e", "p1f", "p1g", "p1h",
                                        "p1d_pyr", "p1h_pyr"])
    ap.add_argument("--views", default=None,
                    help="pyramid probes only: frozen compressor arm. Defaults per probe — "
                         "p1d_pyr=graded (cleanest resolution ladder), p1h_pyr=llm_general "
                         "(coarse views degrade the value to a range, so there is something "
                         "to mark provisional)")
    ap.add_argument("--models", default=None,
                    help="comma list from {student,qwen3b,qwen7b}; default: p1d=student, "
                         "p1e=all three, p1f/p1g=student+qwen7b, else student+qwen3b")
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

    arm = None
    if args.probe in ("p1d_pyr", "p1h_pyr"):
        # p1d_pyr wants the cleanest resolution ladder (graded: budget-driven, G4 passes).
        # p1h_pyr wants an arm whose coarse views DEGRADE the value rather than dropping it
        # (llm_general: range at L1-L5, exact at L6) — see _p1h_pyramid_cells.
        arm = args.views or ("graded" if args.probe == "p1d_pyr" else "llm_general")
        cfg, spec, _views, pmeta = pyramid_materials(arm)
        cells, meta_extras = pyramid_probe_cells(args.probe, cfg, pmeta)
        tile26 = {"view_tokens": None, "view_source": f"pyramid:{arm}"}
    else:
        cfg, spec, tile26, pass2, pass4, pass12 = harness_materials()
        cells, meta_extras = probe_cells(args.probe, cfg, tile26, pass2, pass4, pass12)
    # cells are (system, k, builder, view) or (system, k, builder, view, K); K defaults to the
    # D25 schedule length so every pre-existing probe is untouched.
    cells = {lab: (tuple(v) + (31,))[:5] for lab, v in cells.items()}

    default_models = {"p1d": ["student"], "p1d_pyr": ["student"],
                      "p1e": ["student", "qwen3b", "qwen7b"],
                      "p1f": ["student", "qwen7b"], "p1g": ["student", "qwen7b"],
                      "p1h": ["student", "qwen7b"]}
    model_keys = (args.models.split(",") if args.models
                  else default_models.get(args.probe, ["student", "qwen3b"]))

    if args.dry_run:
        print(f"\nDRY RUN {args.probe}: models={model_keys} seeds={seeds}")
        for label, (system, user_k, builder, view, user_K) in cells.items():
            src = getattr(builder, "src_cell", None)
            if src:
                print(f"\n--- cell {label}: k={user_k}/{user_K}, view {n_tokens(view)} tok — "
                      f"PAIRED: state per seed = that seed's post-state from cell '{src}' ---")
                continue
            st = builder(seeds[0], {"conditions": {}})
            print(f"\n--- cell {label}: k={user_k}/{user_K}, state {n_tokens(st.render())} tok, "
                  f"{len(st.entries)} entries, view {n_tokens(view)} tok ---")
            if args.probe != "p1d_pyr":
                print(st.render()[:400])
        if args.probe == "p1e":
            print(f"\n--- EXPLAINED SYSTEM PROMPT ---\n{explained_system(cfg)}")
        print("\nDry run OK. Nothing served, nothing written.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    exe = ROOT / "models" / "llamacpp" / "llama-server.exe"
    for mk in model_keys:
        model = MODELS[mk]
        assert model.exists(), model
        out_path = OUT_DIR / (f"{args.probe}_{arm}_{mk}.json" if arm
                              else f"{args.probe}_{mk}.json")
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
                         "tile": ({"schedule": "pyramid",
                                   "view_source": tile26["view_source"]}
                                  if args.probe == "p1d_pyr" else
                                  {"k": 26, "K": 31, "view_tokens": tile26["view_tokens"],
                                   "view_source": tile26["view_source"]}),
                         **meta_extras},
               "conditions": {}, "complete": False}
        print(f"\n{'=' * 70}\n{args.probe} ARM: {mk}  ({model.name})\n{'=' * 70}", flush=True)
        server = LlamaServer(str(exe), str(model), ctx=args.ctx, port=args.port,
                             threads=args.threads, n_gpu_layers=args.ngl)
        server.ensure_running()
        t0 = time.time()
        try:
            for label, (system, user_k, builder, view, user_K) in cells.items():
                print(f"  cell {label} (k={user_k}/{user_K}):", flush=True)
                rec["conditions"][label] = run_cell(server, label, system, user_k, builder,
                                                    view, seeds, rec, user_K)
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
