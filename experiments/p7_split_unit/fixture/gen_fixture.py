"""P7 — generate the host code document + the unguessable split unit + computed ground truth.

Deterministic (seeded). Emits:
  host_doc.jsonl   — the codebase-as-document, one JSON line per "block" (a module or a
                     function group), in the turn-like schema build_schedule consumes
                     ({turn, seg, role, content}). A block is the schedule's atom.
  fixture_spec.json — the split-unit spec: the arbitrary table (fragment-1), the call site
                     (fragment-2), the queried input, and the COMPUTED ground-truth answer.

The split unit (per the brief's anti-backfill rules):
  fragment-1 (EARLY, locally mundane): an ARBITRARY RNG-valued lookup table
      REGION_SURCHARGE_CENTS = {code: cents, ...}   # values unguessable (3-digit RNG)
  fragment-2 (LATE, under state pressure): the call site + a second arbitrary constant
      def compute_line_surcharge(region_code):
          return REGION_SURCHARGE_CENTS[region_code] + RECONCILIATION_ADDER_CENTS
      RECONCILIATION_ADDER_CENTS = <arbitrary>
  scoring question (asked ONLY at the end): what does compute_line_surcharge(QUERIED_CODE) return?
      ground truth = REGION_SURCHARGE_CENTS[QUERIED_CODE] + RECONCILIATION_ADDER_CENTS

Neither fragment alone determines the answer: the table lacks the +adder and which code is asked;
the call site lacks the table value. Backfill-defended by construction; verified empirically.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))
from pca.textutils import n_tokens  # noqa: E402

SEED = 70707
QUERIED_CODE = 23
TARGET_TOKENS = 64000           # ~P6 scale (73K); enough Phase-B tiles for a large gap
# Both fragments must be MID-EXCLUSIVE (outside the dense head+tail window, ~first/last 11%)
# so dense is a true floor, while keeping a large inter-fragment gap (~10 verbatim tiles).
FRAG1_BLOCK_FRAC = 0.22         # table: past the dense head, early in the verbatim sweep
FRAG2_BLOCK_FRAC = 0.75         # call site: before the dense tail, late in the sweep
FRAG_CTRL_BLOCK_FRAC = 0.45     # recordability CONTROL table (a second arbitrary table, NOT the
                                # answer, NOT query-relevant): proves the runner CAN host a table's
                                # contents warm, so an answer-table non-recording is real not artifact
                                # (the handoff's F7-gate idea). Placed in its own Phase-A chunk + tile.
# RELEVANCE CONTROL (Reading A vs B): a matched pair of str->str tables placed in the SAME Phase-A
# chunk (identical pass / state pressure), differing ONLY in task-relevance:
#   EVENT_DISPATCH (relevant)  — event->handler routing = the codebase's control flow; a faithful
#       brief of "what this code does" must capture it. Relevance is INTRINSIC (behavior-governing),
#       discoverable by reading, justified WITHOUT any reference to the surcharge probe.
#   TOKEN_ALIASES (arbitrary)  — opaque interned token->token map, no behavioral consequence; matched
#       to EVENT_DISPATCH on size/form/position, meaningless (the str-form analogue of the arbitrary
#       surcharge table). Controls the int-vs-str surface-form confound.
FRAG_REL_BLOCK_FRAC = 0.62      # relevant dispatch table  (chunk 3)
FRAG_ALIAS_BLOCK_FRAC = 0.68    # arbitrary alias table    (chunk 3, same pass as relevant)
# FIXTURE v2 (RELEVANCE-CONTROL-V2.md, 2026-07-10): (a) the pair moves out of singleton
# categories into the SAME well-represented category (routing/) as sibling modules — category
# representation matched by construction; (b) a POSITIVE CONTROL (STAGE_ORDER, small,
# behavior-governing, brief-central) is inserted in the represented queue/ category at ~0.35,
# its own Phase-A chunk. All new content draws from a SEPARATE RNG stream (SEED+1) consumed
# after every v1 draw, so v1 values (probe, ctrl, pair contents, filler) stay byte-identical;
# asserted against the previous fixture_spec.json at generation time.
FIXTURE_VERSION = 2
FRAG_PC_BLOCK_FRAC = 0.35       # positive control (queue/pipeline.py), own Phase-A chunk

rng = random.Random(SEED)

# --------------------------------------------------------------------------- split unit
# Region codes: arbitrary 2-digit ids (NOT 0..n; not guessable from position).
# Force-include QUERIED_CODE so the queried key is always present.
_pool = [c for c in range(10, 99) if c != QUERIED_CODE]
REGION_CODES = sorted(rng.sample(_pool, 23) + [QUERIED_CODE])
assert QUERIED_CODE in REGION_CODES, "queried code must be a table key"
# Values: 3-digit RNG cents, no pattern. Exact-guess probability ~0.
REGION_SURCHARGE = {c: rng.randint(101, 989) for c in REGION_CODES}
RECONCILIATION_ADDER = rng.randint(1001, 1999)   # arbitrary, lives in fragment-2
GROUND_TRUTH = REGION_SURCHARGE[QUERIED_CODE] + RECONCILIATION_ADDER

# Recordability CONTROL: a second arbitrary table (carrier fuel surcharge, basis points). Not the
# answer, not asked, not referenced by fragment-2. Used only to test whether the runner records a
# table's CONTENTS warm (the F7-gate). 12 entries, RNG values.
CTRL_CODES = sorted(rng.sample(range(100, 999), 12))
CTRL_TABLE = {c: rng.randint(11, 89) for c in CTRL_CODES}

# Relevance-control pair. BOTH tables share the SAME 24 real event-name keys and map to ARBITRARY,
# NON-DERIVABLE, real-word two-token values (matched on size/form/regularity/token-difficulty — the
# advisor's confounds: neither is rule-compressible from its key, neither is OOD-hard). The ONLY
# difference is BEHAVIORAL RELEVANCE, carried by CONTEXT (not decoration):
#   EVENT_DISPATCH (relevant)  — event -> handler; consumed by dispatch() that drives control flow.
#   DISPLAY_LABELS (arbitrary) — event -> cosmetic display label; consumed by a trivial label().
_RES = ["order", "payment", "shipment", "invoice", "refund", "account"]
_ACT = ["created", "updated", "cancelled", "failed"]
EVENTS = [f"{r}.{a}" for r in _RES for a in _ACT]                              # 24 shared keys
_HVERB = ["reconcile", "flush", "persist", "enqueue", "notify", "rollback", "capture", "settle",
          "void", "escalate", "archive", "retry", "audit", "sync", "emit", "throttle", "reindex",
          "snapshot", "quarantine", "replay", "expire", "release", "provision", "rebalance"]
_HNOUN = ["ledger", "cache", "record", "queue", "webhook", "txn", "invoice", "balance", "shipment", "alert"]
_LADJ = ["teal", "amber", "slate", "crimson", "ivory", "cobalt", "olive", "maroon", "indigo", "beige",
         "coral", "umber", "jade", "rust", "ash", "plum"]
_LNOUN = ["harbor", "meadow", "lantern", "summit", "willow", "anchor", "ember", "quartz", "cedar",
          "marsh", "ridge", "delta", "grove", "fjord", "basin", "vale"]
_handlers = rng.sample([f"{v}_{n}" for v in _HVERB for n in _HNOUN], len(EVENTS))   # arbitrary, real-word
_labels = rng.sample([f"{a}_{n}" for a in _LADJ for n in _LNOUN], len(EVENTS))      # arbitrary, real-word
DISPATCH = dict(zip(EVENTS, _handlers))      # event -> arbitrary handler (NON-derivable; control flow)
ALIAS_TABLE = dict(zip(EVENTS, _labels))     # event -> arbitrary cosmetic label (NON-derivable; display)

# ---- v2 additions: SEPARATE stream (SEED+1), consumed after every v1 draw above ----------
rng2 = random.Random(SEED + 1)
# Positive-control stage names: order fixed (plausible pipeline shape), exact names drawn per
# slot (non-derivable without reading). Pool words avoid the filler category/verb name pools.
_STAGE_POOLS = [("intake", "receive", "collect"),
                ("screen", "triage", "inspect"),
                ("convert", "standardize", "reshape"),
                ("consolidate", "settle", "balance"),
                ("publish", "finalize", "handoff")]
STAGE_KEYS = [rng2.choice(p) for p in _STAGE_POOLS]
_STAGE_CONSTS = [rng2.randint(2, 9) for _ in STAGE_KEYS]


def fragment1_text() -> str:
    """The arbitrary table, embedded in a mundane pricing-constants module. Multi-line dict
    literal so the structure-preserving compressor must keep the whole block."""
    lines = ["# ===== module: pricing/region_tables.py =====",
             '"""Region surcharge schedule. Values are set by the Q3 ops reconciliation review',
             'and are NOT derived from distance or zone — do not "simplify" them. See RFC-2231."""',
             "",
             "REGION_SURCHARGE_CENTS = {"]
    for c in REGION_CODES:
        lines.append(f"    {c}: {REGION_SURCHARGE[c]},")
    lines.append("}")
    lines += ["",
              "def surcharge_cents(region_code):",
              '    """Raw per-region surcharge in cents (pre-reconciliation)."""',
              "    return REGION_SURCHARGE_CENTS[region_code]",
              ""]
    return "\n".join(lines)


def control_text() -> str:
    """The recordability-control table: an arbitrary carrier-fuel-surcharge table in its own module.
    Structurally identical to fragment-1 (multi-line dict) but never queried."""
    lines = ["# ===== module: carrier/fuel_tables.py =====",
             '"""Carrier fuel surcharge in basis points by carrier code (weekly ops setting)."""',
             "",
             "CARRIER_FUEL_BP = {"]
    for c in CTRL_CODES:
        lines.append(f"    {c}: {CTRL_TABLE[c]},")
    lines.append("}")
    lines += ["",
              "def fuel_bp(carrier_code):",
              "    return CARRIER_FUEL_BP[carrier_code]",
              ""]
    return "\n".join(lines)


def relevant_text() -> str:
    """RELEVANT table: event->handler dispatch routing. Relevance carried by CONTEXT — it is consumed
    by dispatch(), which selects and runs the handler for each event (control flow). A faithful brief
    of the codebase's behaviour must capture which events route to which handlers."""
    lines = ["# ===== module: routing/router.py =====",
             '"""Event-to-handler routing: dispatch() resolves and invokes the handler for each event."""',
             "",
             "EVENT_DISPATCH = {"]
    for k, v in DISPATCH.items():
        lines.append(f'    "{k}": "{v}",')
    lines.append("}")
    lines += ["",
              "def dispatch(event, payload):",
              "    handler = EVENT_DISPATCH[event]   # which handler runs for this event",
              "    return HANDLERS[handler](payload)",
              ""]
    return "\n".join(lines)


def aliases_text() -> str:
    """ARBITRARY table matched to EVENT_DISPATCH on every axis (same event keys, arbitrary
    non-derivable real-word values, size/form/position) EXCEPT relevance: these are cosmetic display
    labels consumed only by a trivial label() — no behavioural consequence."""
    lines = ["# ===== module: routing/labels.py =====",
             '"""Cosmetic display labels shown next to each routed event in the activity feed."""',
             "",
             "DISPLAY_LABELS = {"]
    for k, v in ALIAS_TABLE.items():
        lines.append(f'    "{k}": "{v}",')
    lines.append("}")
    lines += ["",
              "def label(event):",
              "    return DISPLAY_LABELS.get(event, event)",
              ""]
    return "\n".join(lines)


def pc_text() -> str:
    """POSITIVE CONTROL (relevance-control v2, fix 1): a small, behavior-governing,
    brief-central structure in a WELL-REPRESENTED category (queue/). STAGE_ORDER is the
    pipeline's stage sequence and run_pipeline() drives every batch through it — the most
    brief-worthy fact in a "what does this codebase do" brief. Probe-blind: no relation to
    any planted probe. Instrument-sensitivity target: >= Tier 1 under neutral+v2."""
    lines = ["# ===== module: queue/pipeline.py =====",
             '"""End-to-end processing pipeline: run_pipeline() drives every batch through',
             'the stages in STAGE_ORDER, in order."""',
             "",
             f"STAGE_ORDER = {STAGE_KEYS!r}",
             "",
             "def run_pipeline(batch):",
             '    """Process a batch through each pipeline stage, in STAGE_ORDER order."""',
             "    for stage in STAGE_ORDER:",
             "        batch = STAGE_HANDLERS[stage](batch)",
             "    return batch",
             ""]
    for s, c in zip(STAGE_KEYS, _STAGE_CONSTS):
        lines += [f"def stage_{s}(batch):",
                  f"    return [x for x in (batch or []) if getattr(x, 'weight', {c}) >= {c}]",
                  ""]
    lines += ["STAGE_HANDLERS = {s: globals()[f'stage_{s}'] for s in STAGE_ORDER}", ""]
    return "\n".join(lines)


def fragment2_text() -> str:
    """The call site + the second arbitrary constant. Far from fragment-1. Uses the table but
    does NOT restate any table value; needs fragment-1 to resolve."""
    return "\n".join([
        "# ===== module: fulfillment/line_quote.py =====",
        "from pricing.region_tables import REGION_SURCHARGE_CENTS",
        "",
        "# Fixed reconciliation adder applied to every audited line (Q3 compliance, RFC-2231).",
        f"RECONCILIATION_ADDER_CENTS = {RECONCILIATION_ADDER}",
        "",
        "def compute_line_surcharge(region_code):",
        '    """Total per-line surcharge in cents for an audited shipment to `region_code`:',
        '    the region\'s base surcharge plus the fixed reconciliation adder."""',
        "    base = REGION_SURCHARGE_CENTS[region_code]",
        "    return base + RECONCILIATION_ADDER_CENTS",
        "",
        "def quote_line(item, region_code):",
        "    subtotal = item.unit_price * item.qty",
        f"    surcharge = compute_line_surcharge(region_code)   # e.g. region {QUERIED_CODE}",
        "    return subtotal + surcharge",
        "",
    ])

# --------------------------------------------------------------------------- realistic filler
VERBS = ["normalize", "validate", "resolve", "encode", "merge", "filter", "scan", "expand",
         "trim", "rank", "batch", "flatten", "dedupe", "parse", "format", "clamp", "sample",
         "bucket", "tokenize", "rotate", "hash", "compact", "align", "splice"]
NOUNS = ["payload", "manifest", "ledger", "token", "record", "segment", "envelope", "cursor",
         "header", "shard", "packet", "entry", "digest", "window", "frame", "node", "claim",
         "lane", "tariff", "carrier", "invoice", "parcel", "route", "slot"]
MODULES = ["ingest/{}.py", "transform/{}.py", "validate/{}.py", "routing/{}.py", "billing/{}.py",
           "carrier/{}.py", "audit/{}.py", "serialize/{}.py", "cache/{}.py", "retry/{}.py",
           "geo/{}.py", "report/{}.py", "schema/{}.py", "queue/{}.py", "metrics/{}.py"]


def filler_function() -> str:
    v, n = rng.choice(VERBS), rng.choice(NOUNS)
    name = f"{v}_{n}"
    k = rng.randint(2, 4)
    args = ", ".join([n] + [f"{rng.choice(['opt','limit','flag','mode','depth','width'])}{i}"
                            for i in range(k - 1)])
    c1, c2, c3 = rng.randint(2, 97), rng.randint(100, 999), round(rng.uniform(0.1, 0.95), 3)
    body = [
        f"def {name}({args}):",
        f'    """{v.capitalize()} the {n} for the downstream {rng.choice(NOUNS)} stage."""',
        f"    acc = []",
        f"    for i, x in enumerate({n} or []):",
        f"        if i % {c1} == 0 and x is not None:",
        f"            acc.append((x, i * {c2}))",
        f"        elif x and getattr(x, 'weight', 0) > {c3}:",
        f"            acc.append((x, i))",
        f"    return [t for t in acc if t[1] >= 0]",
        "",
    ]
    return "\n".join(body)


def filler_module(idx: int) -> str:
    path = MODULES[idx % len(MODULES)].format(rng.choice(NOUNS) + str(idx))
    n_funcs = rng.randint(4, 7)
    out = [f"# ===== module: {path} =====",
           f'"""Auto-composed {path.split("/")[0]} helpers (group {idx})."""', ""]
    out += [filler_function() for _ in range(n_funcs)]
    return "\n".join(out)


def _phase_a_chunk_of(chunksA: list[dict], turn: int) -> int | None:
    for i, p in enumerate(chunksA):
        if p["turn_lo"] <= turn <= p["turn_hi"]:
            return i
    return None


_RNG_STATE_AT_FILLER: tuple | None = None


def _build_with_inserts(pc_offset: int = 0):
    """Filler blocks + planted inserts. pc_offset shifts only the PC insertion index —
    the pre-registered mechanical nudge used if a Phase-A chunk guard fails. The filler
    continues the module-level v1 stream exactly where v1's main() consumed it (state
    snapshot/restore keeps retries deterministic AND filler bytes identical to v1)."""
    global _RNG_STATE_AT_FILLER
    if _RNG_STATE_AT_FILLER is None:
        _RNG_STATE_AT_FILLER = rng.getstate()
    rng.setstate(_RNG_STATE_AT_FILLER)
    blocks: list[str] = []
    idx = 0
    while sum(n_tokens(b) for b in blocks) < TARGET_TOKENS:
        blocks.append(filler_module(idx)); idx += 1
    n = len(blocks)
    # insert in ascending position order, tracking the shift each prior insert causes
    inserts = sorted([(max(1, int(n * FRAG1_BLOCK_FRAC)), "f1", fragment1_text()),
                      (max(1, int(n * FRAG_PC_BLOCK_FRAC) + pc_offset), "pc", pc_text()),
                      (int(n * FRAG_CTRL_BLOCK_FRAC), "ctrl", control_text()),
                      (int(n * FRAG_REL_BLOCK_FRAC), "rel", relevant_text()),
                      (int(n * FRAG_ALIAS_BLOCK_FRAC), "alias", aliases_text()),
                      (min(n - 1, int(n * FRAG2_BLOCK_FRAC)), "f2", fragment2_text())])
    final_pos = {}
    for shift, (pos, tag, text) in enumerate(inserts):
        blocks.insert(pos + shift, text)
        final_pos[tag] = pos + shift
    return blocks, final_pos


def main():
    # v2 GUARDS use the real Phase-A chunking (build_schedule), not the cosmetic seg field.
    import yaml
    from pca.planted import build_schedule
    cfg = yaml.safe_load((HERE.parent / "config.yaml").read_text(encoding="utf-8"))["schedule"]

    blocks = final_pos = recs = chunksA = None
    for pc_offset in (0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6):
        blocks, final_pos = _build_with_inserts(pc_offset)
        recs = [{"turn": i, "seg": i // 24 + 1, "role": "code", "content": b}
                for i, b in enumerate(blocks)]
        turns = [{"turn": r["turn"], "seg": r["seg"], "text": r["content"],
                  "tokens": n_tokens(r["content"])} for r in recs]
        sch = build_schedule(turns, cfg["V"], cfg["R"], tuple(cfg["stage_fracs"]))
        chunksA = [p for p in sch if p["phase"] == "A"]
        ch = {t: _phase_a_chunk_of(chunksA, final_pos[t]) for t in final_pos}
        pair_ok = ch["rel"] is not None and ch["rel"] == ch["alias"]
        pc_ok = ch["pc"] is not None and ch["pc"] not in (ch["rel"], ch["f1"], ch["f2"])
        if pair_ok and pc_ok:
            if pc_offset:
                print(f"guard nudge applied: pc_offset={pc_offset:+d}")
            break
    else:
        raise AssertionError(f"v2 chunk guards unsatisfiable within nudge range: {ch}")

    # --- v2 guard block (pre-registered; all failures are hard errors) -----------------
    n_final = len(blocks)
    # ±0.02 applies to the five v1 targets (pre-reg); the PC is "≈0.35" and owns the nudge
    # slack — bounded loosely to its intended region instead.
    targets = {"f1": FRAG1_BLOCK_FRAC, "ctrl": FRAG_CTRL_BLOCK_FRAC,
               "rel": FRAG_REL_BLOCK_FRAC, "alias": FRAG_ALIAS_BLOCK_FRAC, "f2": FRAG2_BLOCK_FRAC}
    for tag, tf in targets.items():
        frac = final_pos[tag] / n_final
        assert abs(frac - tf) <= 0.02, f"position guard FAIL {tag}: {frac:.3f} vs {tf}"
    pc_frac = final_pos["pc"] / n_final
    assert 0.25 <= pc_frac <= 0.45, f"pc position out of region: {pc_frac:.3f}"
    for tag in ("f1", "f2"):
        frac = final_pos[tag] / n_final
        assert 0.11 < frac < 0.89, f"mid-exclusivity guard FAIL {tag}: {frac:.3f}"
    # byte-equality vs the previous spec: the chain probe and all v1 planted values unchanged
    spec_path = HERE / "fixture_spec.json"
    if spec_path.exists():
        old = json.loads(spec_path.read_text(encoding="utf-8"))
        assert old["ground_truth_answer"] == GROUND_TRUTH, "2353-equivalence FAIL"
        assert old["table"] == {str(k): v for k, v in REGION_SURCHARGE.items()}, "table drift"
        assert old["reconciliation_adder_cents"] == RECONCILIATION_ADDER, "adder drift"
        assert old["control_table"] == {str(k): v for k, v in CTRL_TABLE.items()}, "ctrl drift"
        assert old["relevance_control"]["relevant_table"] == dict(DISPATCH), "pair drift (rel)"
        assert old["relevance_control"]["arbitrary_table"] == dict(ALIAS_TABLE), "pair drift (arb)"
        print("byte-equality guards vs previous spec: PASS")

    (HERE / "host_doc.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n", encoding="utf-8")
    total = sum(n_tokens(b) for b in blocks)
    spec = {
        "_doc": "P7 split-unit fixture. Ground truth computed here; the host doc embeds the same "
                "table/constant. Answer = REGION_SURCHARGE_CENTS[QUERIED_CODE] + RECONCILIATION_ADDER_CENTS.",
        "fixture_version": FIXTURE_VERSION,
        "seed": SEED,
        "seed_v2_stream": SEED + 1,
        "queried_code": QUERIED_CODE,
        "table": {str(k): v for k, v in REGION_SURCHARGE.items()},
        "reconciliation_adder_cents": RECONCILIATION_ADDER,
        "ground_truth_answer": GROUND_TRUTH,
        "table_value_for_queried": REGION_SURCHARGE[QUERIED_CODE],
        "scoring_question": (
            f"In this codebase, what integer does compute_line_surcharge({QUERIED_CODE}) return? "
            "Answer with the exact integer only."),
        "answer_match": {"exact_int": GROUND_TRUTH, "table_value": REGION_SURCHARGE[QUERIED_CODE]},
        "control_table": {str(k): v for k, v in CTRL_TABLE.items()},
        "control_decl": "CARRIER_FUEL_BP = {",
        "relevance_control": {
            "_doc": "Reading A vs B control. Matched pair: SAME 24 real event-name keys, both mapping "
                    "to ARBITRARY non-derivable real-word two-token values (matched size/form/position/"
                    "regularity/token-difficulty; same Phase-A chunk+pass). ONLY behavioural relevance "
                    "differs, carried by CONTEXT: relevant=EVENT_DISPATCH (consumed by dispatch() that "
                    "runs the handler for each event = control flow; a behavioural brief must capture "
                    "it; probe-blind). arbitrary=DISPLAY_LABELS (cosmetic display labels consumed by a "
                    "trivial label(); no behavioural consequence).",
            "relevant_decl": "EVENT_DISPATCH = {",
            "relevant_table": dict(DISPATCH),
            "arbitrary_decl": "DISPLAY_LABELS = {",
            "arbitrary_table": dict(ALIAS_TABLE),
            "v2_paths": {"relevant": "routing/router.py", "arbitrary": "routing/labels.py",
                         "note": "v2: same well-represented category (routing/), sibling modules — "
                                 "category representation matched by construction (was: singleton "
                                 "dispatch/ and ui/ in v1)"},
        },
        "positive_control": {
            "_doc": "Relevance-control v2 fix 1: instrument-sensitivity control. Small, "
                    "behavior-governing, brief-central, in the well-represented queue/ category. "
                    "Sensitivity = >= Tier 1 in >= 4/5 seeds under neutral+v2 (see "
                    "RELEVANCE-CONTROL-V2.md). Attribution requires STAGE_ORDER / "
                    "queue/pipeline.py / run_pipeline — generic 'queue' category mentions do not count.",
            "decl": "STAGE_ORDER = [",
            "module": "queue/pipeline.py",
            "stages": list(STAGE_KEYS),
            "consumer": "run_pipeline",
        },
        "positions": {"n_blocks": len(blocks), "fragment1_block": final_pos["f1"],
                      "pc_block": final_pos["pc"],
                      "control_block": final_pos["ctrl"], "relevant_block": final_pos["rel"],
                      "alias_block": final_pos["alias"], "fragment2_block": final_pos["f2"],
                      "phase_a_chunks": {t: _phase_a_chunk_of(chunksA, final_pos[t])
                                         for t in final_pos},
                      "total_tokens": total},
        "fragment1_text": fragment1_text(),
        "control_text": control_text(),
        "relevant_text": relevant_text(),
        "aliases_text": aliases_text(),
        "fragment2_text": fragment2_text(),
        "pc_text": pc_text(),
    }
    (HERE / "fixture_spec.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"fixture v{FIXTURE_VERSION}: blocks={len(blocks)} total_tokens={total} "
          f"frag1@block{final_pos['f1']} pc@block{final_pos['pc']} ctrl@block{final_pos['ctrl']} "
          f"rel@block{final_pos['rel']} alias@block{final_pos['alias']} frag2@block{final_pos['f2']}")
    print(f"phase-A chunks: {spec['positions']['phase_a_chunks']} "
          f"(pair same-chunk + pc-distinct guards PASS)")
    print(f"QUERIED_CODE={QUERIED_CODE} table[{QUERIED_CODE}]={REGION_SURCHARGE[QUERIED_CODE]} "
          f"adder={RECONCILIATION_ADDER} GROUND_TRUTH={GROUND_TRUTH}")


if __name__ == "__main__":
    main()
