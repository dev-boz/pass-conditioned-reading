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
    lines = ["# ===== module: dispatch/router.py =====",
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
    lines = ["# ===== module: ui/labels.py =====",
             '"""Cosmetic display labels shown next to each event in the activity feed."""',
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


def main():
    # Build a sequence of filler blocks; reserve two slots for the fragments.
    blocks: list[str] = []
    idx = 0
    while sum(n_tokens(b) for b in blocks) < TARGET_TOKENS:
        blocks.append(filler_module(idx)); idx += 1
    n = len(blocks)
    # insert in ascending position order, tracking the shift each prior insert causes
    inserts = sorted([(max(1, int(n * FRAG1_BLOCK_FRAC)), "f1", fragment1_text()),
                      (int(n * FRAG_CTRL_BLOCK_FRAC), "ctrl", control_text()),
                      (int(n * FRAG_REL_BLOCK_FRAC), "rel", relevant_text()),
                      (int(n * FRAG_ALIAS_BLOCK_FRAC), "alias", aliases_text()),
                      (min(n - 1, int(n * FRAG2_BLOCK_FRAC)), "f2", fragment2_text())])
    final_pos = {}
    for shift, (pos, tag, text) in enumerate(inserts):
        blocks.insert(pos + shift, text)
        final_pos[tag] = pos + shift

    # Emit as turn-like records (one block == one "turn"); seg = coarse group of ~24 blocks.
    recs = []
    for i, b in enumerate(blocks):
        recs.append({"turn": i, "seg": i // 24 + 1, "role": "code", "content": b})
    (HERE / "host_doc.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in recs) + "\n", encoding="utf-8")

    total = sum(n_tokens(b) for b in blocks)
    spec = {
        "_doc": "P7 split-unit fixture. Ground truth computed here; the host doc embeds the same "
                "table/constant. Answer = REGION_SURCHARGE_CENTS[QUERIED_CODE] + RECONCILIATION_ADDER_CENTS.",
        "seed": SEED,
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
        },
        "positions": {"n_blocks": len(blocks), "fragment1_block": final_pos["f1"],
                      "control_block": final_pos["ctrl"], "relevant_block": final_pos["rel"],
                      "alias_block": final_pos["alias"], "fragment2_block": final_pos["f2"],
                      "total_tokens": total},
        "fragment1_text": fragment1_text(),
        "control_text": control_text(),
        "relevant_text": relevant_text(),
        "aliases_text": aliases_text(),
        "fragment2_text": fragment2_text(),
    }
    (HERE / "fixture_spec.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"blocks={len(blocks)} total_tokens={total} "
          f"frag1@block{final_pos['f1']} ctrl@block{final_pos['ctrl']} "
          f"rel@block{final_pos['rel']} alias@block{final_pos['alias']} frag2@block{final_pos['f2']}")
    print(f"QUERIED_CODE={QUERIED_CODE} table[{QUERIED_CODE}]={REGION_SURCHARGE[QUERIED_CODE]} "
          f"adder={RECONCILIATION_ADDER} GROUND_TRUTH={GROUND_TRUTH}")


if __name__ == "__main__":
    main()
