"""Stage-A chain gate — post-battery analysis (E2PRIME-CRITERION §3 verdict, §5 attribution).

Reads the per-seed records written by stagea_chain_gate.py and applies the pre-committed rules
mechanically. It computes NOTHING that a verdict may be argued from beyond what the criterion
already fixes, and it never pools the deterministic anchor with the sampled ten.

Three things it adds over the runner's own --summarize:

1. §5 component attribution — RECORD (operands hosted at ANY pass, from the warm per-pass
   tracking the criterion demands, not a cold end-state proxy), RETAIN (held at close), COMPOSE
   (2353 produced from held operands). This is what names the blocked joint.
2. An honest closing no-answer classification. The runner's closing_budget_exhausted flag is
   measured in the WRONG TOKENIZER — it counts the reply with tiktoken cl100k while the server
   spends a Qwen budget, so a reply that hit the cap can read as un-capped. Here the cap is
   detected from the text itself (a reply that stops mid-token did not choose to stop), and the
   result is reported as a heuristic, because a no-answer draw for instrument reasons must not be
   silently pooled with a no-answer draw for capability reasons.
3. Guard block/redirect counts by reason — the E2PRIME-PREREG §6 measure that replicates or
   refutes the n=2 clobber mechanism.

  python experiments/e2prime/analyze_chain_gate.py
  python experiments/e2prime/analyze_chain_gate.py --relevance   # adapt records -> frozen v2 scorer
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P7 = ROOT / "experiments" / "p7_split_unit"
sys.path.insert(0, str(ROOT / "src"))

SPEC = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
SAMPLED = [(s, 0.7) for s in range(1, 11)]
ANCHOR = (42, 0.0)


def load_records(out_dir: Path) -> dict[str, list[dict]]:
    by_arm: dict[str, list[dict]] = {}
    for f in sorted(out_dir.glob("*.json")):
        if f.name.startswith(("manifest", "smoke_")):
            continue          # smoke draws are non-verdict by construction
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("complete"):
            by_arm.setdefault(r["_meta"]["arm"], []).append(r)
    return by_arm


def classify_close(rec: dict) -> str:
    """Why a draw produced no integer. A reply that stops mid-token was cut off by the decode cap;
    one that ends cleanly chose to stop. Heuristic by design — the archived raw text is the record."""
    c = rec["closing"]
    if c["answer"] is not None:
        return "answered"
    t = (c["raw_output"] or "").rstrip()
    if c.get("http_error"):
        return "http_error"
    if "INSUFFICIENT" in t:
        return "declared_insufficient"
    # Do NOT assert a cause that cannot be established from the text. Ending shape alone fails in
    # both directions: a cut-off lands mid-literal ("weight>0.") and reads as a finished sentence,
    # while a genuine finished sentence can end on a number ("... is 23.") and read as a cut-off.
    # Report the EVIDENCE instead — length relative to the budget — and let the budget diagnostic,
    # which has the server's own completion_tokens, settle it. Threshold is deliberately loose
    # because the reply is counted in cl100k here and spent in Qwen tokens by the server.
    budget = rec["_meta"].get("closing_max_tokens") or 1200
    return ("no_answer_line__near_budget" if rec["closing"]["closing_tokens"] >= 0.7 * budget
            else "no_answer_line__stopped_early")


QCODE = SPEC["queried_code"]                      # 23
TVAL = SPEC["table_value_for_queried"]            # 988
ADDER = SPEC["reconciliation_adder_cents"]        # 1365
TRUTH = SPEC["ground_truth_answer"]               # 2353

# The runner's stored flags matched the queried mapping as "23: 988" — a COLON only. The trained
# student paraphrases the table as "23→988" (U+2192), and also emits "->", "=" and en/em dashes.
# Scoring that as not-recorded is the exact-match trap pca/planted.py warns about in its own
# docstring, and here it would have manufactured a false ARCHITECTURE GATE — the most consequential
# error available, since <=1/10 ends training spend on this instantiation. Every flag below is
# therefore RECOMPUTED from the archived state text; the stored flags are ignored.
# Adjacency, not co-presence: key and value must be separated by at most a few NON-DIGIT
# characters, so a neighbouring table row ("19→808, 23→988") cannot cross-match.
_PAIR = re.compile(rf"(?<!\d){QCODE}\D{{1,8}}{TVAL}(?!\d)")
_PAIR_REV = re.compile(rf"(?<!\d){TVAL}\D{{1,12}}{QCODE}(?!\d)")
# The student's dominant move on the table is LOSSY SUMMARY: it names the table and reports its
# entry count and value RANGE ("24 surcharge rates (10-988 cents)") without any mapping. 988 is
# then present as a range endpoint while 23->988 is not recorded. That is Tier 1 in the
# RELEVANCE-CONTROL-V2 taxonomy (existence-or-purpose noted) against Tier 2 (mappings recorded) —
# a different thing from ignoring the table, and the distinction is what training has to move.
_TABLE_NAMED = re.compile(r"REGION[_ ]SURCHARGE|region_tables", re.I)

# The 2026-07-26 arbitration's headline — 0/28 archived final states record the RELATION
# (fn(region) = table[region] + adder) — was measured by hand in a session scratchpad that no
# longer exists. Mechanized 2026-07-28 and re-verified 0/28 across all three arms, so the relation
# is a first-class joint alongside mapping and adder; tracking two of three required facts is what
# produced the §5 mis-attribution. Line-scoped on purpose: co-presence of the three names across
# one entry with no computational link is NOT a relation (seed 2's S83 — fn name, adder, table
# import in a single entry — is the canonical near-miss and must not match).
_FN_NAMED = re.compile(r"compute_line_surcharge", re.I)
_ADDER_REF = re.compile(r"RECONCILIATION_ADDER|(?<!\d)1365(?!\d)")
_LINKOP = re.compile(r"\+|\bplus\b|\badds?\b|\bsum of\b", re.I)


def _relation_flags(state_text: str) -> dict:
    strict = partial = operands_linked = False
    for ln in (state_text or "").splitlines():
        fn = bool(_FN_NAMED.search(ln)); tbl = bool(_TABLE_NAMED.search(ln))
        add = bool(_ADDER_REF.search(ln)); op = bool(_LINKOP.search(ln))
        if fn and tbl and add and op:
            strict = True          # the full relation, stated where the function is
        elif fn and op and (tbl or add):
            partial = True         # fn computationally linked to one operand
        elif tbl and add and op:
            operands_linked = True # addition licensed without naming the fn
    return {"relation_recorded": strict, "relation_partial": partial,
            "relation_operands_linked": operands_linked}


def _int_present(text: str, value: int) -> bool:
    return re.search(rf"(?<!\d){value}(?!\d)", text) is not None


def rescore(state_text: str) -> dict:
    """Paraphrase-robust re-read of a rendered state. Still a PRE-FILTER: hand verification is the
    arbiter, and `pair_loose` exists so a co-present-but-unlinked state is reviewed, not counted."""
    flat = re.sub(r"\s+", " ", state_text or "")
    pair = bool(_PAIR.search(flat))
    named = bool(_TABLE_NAMED.search(flat))
    rel = _relation_flags(state_text)  # line-scoped, so computed before the whitespace flatten
    return {
        **rel,
        "fn_named": bool(_FN_NAMED.search(flat)),
        "queried_mapping": pair,                       # Tier 2: the mapping itself
        "queried_mapping_reversed": bool(_PAIR_REV.search(flat)),
        "table_named": named,                          # Tier 1: the table exists / what it is for
        "tier1_summary_only": named and not pair,      # named, catalogued, mappings dropped
        "pair_loose": (not pair) and _int_present(flat, QCODE) and _int_present(flat, TVAL),
        "table_value_present": _int_present(flat, TVAL),
        "adder_value_present": _int_present(flat, ADDER),
        "precomposed_answer": _int_present(flat, TRUTH),
    }


def components(rec: dict) -> dict:
    """§5 joints. RECORD is warm: did the state EVER host it, per-pass, not just at close."""
    passes = rec["passes"]
    per_pass = [rescore(p["state_text"]) for p in passes]
    ever_map = any(f["queried_mapping"] for f in per_pass)
    ever_val = any(f["table_value_present"] for f in per_pass)
    ever_add = any(f["adder_value_present"] for f in per_pass)
    fin = rescore(rec["final_state"])
    return {
        "RECORD_mapping_ever": ever_map,
        "RECORD_tablevalue_ever": ever_val,
        "RECORD_adder_ever": ever_add,
        "RECORD_both_ever": ever_map and ever_add,
        "TIER1_table_named_ever": any(f["table_named"] for f in per_pass),
        "TIER1_summary_only_at_close": fin["tier1_summary_only"],
        "RETAIN_mapping_at_close": fin["queried_mapping"],
        "RETAIN_adder_at_close": fin["adder_value_present"],
        "RETAIN_both_at_close": fin["queried_mapping"] and fin["adder_value_present"],
        # The third required fact. "ALL_THREE" is what a readable (not merely inferable) chain
        # needs at close; 0/28 archived states ever held it.
        "RECORD_relation_ever": any(f["relation_recorded"] for f in per_pass),
        "RETAIN_relation_at_close": fin["relation_recorded"],
        "RETAIN_ALL_THREE_at_close": (fin["queried_mapping"] and fin["adder_value_present"]
                                      and fin["relation_recorded"]),
        "fn_named_at_close": fin["fn_named"],
        "LOST_after_recording": (ever_map and not fin["queried_mapping"]),
        "COMPOSE_returns_2353": rec["closing"]["answer"] == TRUTH,
        "precomposed_in_state": fin["precomposed_answer"],
        "pair_loose_at_close": fin["pair_loose"],
        "record_first_pass": next((p["k"] for p, f in zip(passes, per_pass)
                                   if f["queried_mapping"]), None),
        # The addendum's four conditions, recomputed on the corrected matcher.
        "candidate_success": bool(
            fin["queried_mapping"] and fin["adder_value_present"]
            and not fin["precomposed_answer"]
            and rec["closing"]["answer"] == TRUTH
            and _int_present(rec["closing"]["raw_output"] or "", TVAL)
            and _int_present(rec["closing"]["raw_output"] or "", ADDER)),
        "stored_flag_disagrees": (ever_map != any(p["flags"]["queried_mapping"] for p in passes)),
        # COMPOSE is only interpretable on draws that actually reached close holding both operands;
        # elsewhere the chain already failed upstream and the close says nothing about composing.
        "compose_interpretable": fin["queried_mapping"] and fin["adder_value_present"],
        # A model that reasons to a wrong number in prose without emitting the required ANSWER line
        # has still composed-and-failed. Scoring stays on the frozen ANSWER format; this is only so
        # a reasoning failure is not filed as a formatting failure in the attribution.
        "prose_number_without_answer_line": (
            rec["closing"]["answer"] is None
            and bool(re.search(r"\breturns?\b[^.]{0,80}?(?<!\d)\d{1,6}(?!\d)",
                               rec["closing"]["raw_output"] or ""))),
    }


def guard_stats(rec: dict) -> Counter:
    c: Counter = Counter()
    for p in rec["passes"]:
        rep = p["apply_report"]
        for b in rep["blocked"]:
            c[f"blocked:{b['reason']}"] += 1
        for r in rep["redirected"]:
            c[f"redirected:{r['via']}"] += 1
    return c


def arm_report(arm: str, recs: list[dict]) -> dict:
    sampled = sorted([r for r in recs if (r["_meta"]["seed"], r["_meta"]["temp"]) in SAMPLED],
                     key=lambda r: r["_meta"]["seed"])
    anchor = [r for r in recs if (r["_meta"]["seed"], r["_meta"]["temp"]) == ANCHOR]
    n = len(sampled)
    print(f"\n{'=' * 100}\nARM: {arm}   sampled n={n}/10   anchor={'present' if anchor else 'absent'}")
    ineligible = [r["_meta"]["seed"] for r in sampled if not r["_meta"].get("verdict_eligible")]
    if ineligible:
        print(f"  !! NOT VERDICT-ELIGIBLE seeds: {ineligible}")
    print("=" * 100)
    print(f"{'seed':>5} {'ans':>7} {'why':>34} {'REC':>5} {'RET':>5} {'CMP':>5} {'cand':>5} "
          f"{'recAt':>6} {'valid':>6} {'stTok':>6} {'trunc':>5}")
    rows = []
    for r in sampled + anchor:
        comp = components(r)
        why = classify_close(r)
        vt = sum(p["n_valid"] for p in r["passes"])
        ct = sum(p["n_candidate_lines"] for p in r["passes"])
        tag = "  <- ANCHOR, never pooled" if (r["_meta"]["seed"], r["_meta"]["temp"]) == ANCHOR else ""
        print(f"{r['_meta']['seed']:>5} {str(r['closing']['answer']):>7} {why:>34} "
              f"{str(comp['RECORD_both_ever'])[0]:>5} {str(comp['RETAIN_both_at_close'])[0]:>5} "
              f"{str(comp['COMPOSE_returns_2353'])[0]:>5} {str(comp['candidate_success'])[0]:>5} "
              f"{str(comp['record_first_pass']):>6} {vt / max(ct, 1):>6.3f} "
              f"{r['final_state_tokens']:>6} {str(r['truncated'])[0]:>5}{tag}")
        if not tag:
            rows.append(comp)
    if not rows:
        return {}

    def rate(key: str) -> str:
        return f"{sum(r[key] for r in rows)}/{n}"

    print(f"\n  §5 COMPONENT ATTRIBUTION (sampled denominator n={n}; anchor excluded)")
    print(f"    RECORD  mapping 23->988 hosted at any pass : {rate('RECORD_mapping_ever')}")
    print(f"    RECORD  adder 1365 hosted at any pass      : {rate('RECORD_adder_ever')}")
    print(f"    RECORD  both operands hosted at any pass   : {rate('RECORD_both_ever')}")
    print(f"    TIER-1  table NAMED at any pass            : {rate('TIER1_table_named_ever')}")
    print(f"    TIER-1  named but mappings dropped, close  : {rate('TIER1_summary_only_at_close')}"
          f"   <- lossy summary, not indifference")
    print(f"    RETAIN  both operands present at close     : {rate('RETAIN_both_at_close')}")
    print(f"    (lost after recording, retention failure)  : {rate('LOST_after_recording')}")
    n_interp = sum(r["compose_interpretable"] for r in rows)
    n_comp = sum(r["COMPOSE_returns_2353"] for r in rows)
    print(f"    COMPOSE close returns 2353                 : {rate('COMPOSE_returns_2353')}")
    print(f"      of draws that reached close WITH both    : {n_comp}/{n_interp}"
          f"   <- the only draws where COMPOSE is interpretable")
    print(f"      wrong number in prose, no ANSWER line    : {rate('prose_number_without_answer_line')}"
          f"   <- reasoning failure, not formatting")
    print(f"    state already held 2353 before close       : {rate('precomposed_in_state')}")
    print(f"    23 and 988 co-present but NOT linked       : {rate('pair_loose_at_close')}"
          f"   <- review by hand, not counted either way")
    n_dis = sum(r["stored_flag_disagrees"] for r in rows)
    if n_dis:
        print(f"    !! runner's stored flag disagrees on       : {n_dis}/{n} draw(s) — the runner's "
              f"colon-only matcher missed the paraphrased mapping; these numbers are the "
              f"recomputed ones")
    print(f"    MECHANICAL candidate successes             : {rate('candidate_success')}"
          f"   <- hand-verify each before any verdict")

    # P7 discipline: a zero is only interpretable ALONGSIDE op-following. An arm that barely emits
    # applicable ops has an empty state to close from, and its 0/10 is protocol transfer rather
    # than evidence about the architecture. This is the floor's main confound and it is reported,
    # not assumed away.
    n_p = sum(len(r["passes"]) for r in sampled) or 1
    ops_pass = sum(len(p["ops"]) for r in sampled for p in r["passes"]) / n_p
    app_pass = sum(p["n_ops_applied"] for r in sampled for p in r["passes"]) / n_p
    ent = sum(len(r["final_state"].splitlines()) for r in sampled) / max(len(sampled), 1)
    tok = sum(r["final_state_tokens"] for r in sampled) / max(len(sampled), 1)
    print(f"\n  op-following: {ops_pass:.1f} ops/pass emitted, {app_pass:.1f} applied/pass; "
          f"final state {ent:.0f} entries / {tok:.0f} tok on average")
    if app_pass < 1.0:
        print("    !! WEAK OP-FOLLOWER: this arm barely builds a state at all, so its rate is "
              "protocol transfer, not architecture evidence (P7 reading rule).")

    why_counts = Counter(classify_close(r) for r in sampled)
    print(f"\n  closing outcomes: {dict(why_counts)}")
    g: Counter = Counter()
    for r in sampled:
        g += guard_stats(r)
    print(f"  guard events over the sampled ten: {dict(g) if g else 'none'}")
    n_success = sum(r["candidate_success"] for r in rows)
    return {"arm": arm, "n": n, "candidates": n_success,
            "record": sum(r["RECORD_both_ever"] for r in rows),
            "retain": sum(r["RETAIN_both_at_close"] for r in rows),
            "compose": sum(r["COMPOSE_returns_2353"] for r in rows)}


def verdict(student: dict, floor: dict) -> None:
    """E2PRIME-CRITERION §3, applied mechanically. Mechanical candidates only — a verdict is not
    final until each candidate survives hand verification."""
    print(f"\n{'=' * 100}\nCRITERION §3 — applied to MECHANICAL candidates\n{'=' * 100}")
    if not student:
        print("no student arm present; no verdict")
        return
    s, f = student["candidates"], (floor or {}).get("candidates")
    print(f"  student {s}/{student['n']}" + (f"   floor {f}/{floor['n']}" if floor else
                                             "   floor NOT YET RUN"))
    if floor is None or f is None:
        print("  -> verdict withheld: the floor arm is what makes the student number interpretable.")
        return
    if f >= 2:
        print(f"  !! floor scored {f}/10 (>=2): the absolute thresholds are VOID (§3 floor check).")
        d = s - f
        v = ("chain demonstrated (paired rule: student-floor >= 5)" if d >= 5 else
             "ARCHITECTURE GATE (paired rule: student-floor <= 1)" if d <= 1 else
             "gray zone (paired rule)")
        print(f"  paired rule: student - floor = {d} -> {v}")
        return
    v = ("CHAIN DEMONSTRATED ON A TRAINED STUDENT (>=5/10) -> proceed to M1/M2 arms" if s >= 5 else
         "TRAINABLE-FURTHER, GRAY ZONE (2-4/10) -> exactly ONE pre-committed retry, declared "
         "before the re-run: double teacher data OR step 1.5B -> 3B" if s >= 2 else
         "ARCHITECTURE GATE (<=1/10) -> no further training spend on this instantiation; the "
         "pre-named third option is the native architecture (docs/DISCO-NATIVE-ARCHITECTURE.md)")
    print(f"  floor {f}/10 is within the expected 0-1 band, so the absolute thresholds hold.")
    print(f"  -> {v}")
    print("\n  This reading is MECHANICAL. Every candidate success must be hand-verified per the "
          "addendum before the verdict is recorded, and a candidate that fails hand verification "
          "lowers the student count.")


def relevance_adapter(out_dir: Path) -> None:
    """The frozen relevance-control-v2 scorer reads run files shaped like the legacy P7 dumps
    (a `snapshots` list of rendered states). Our records keep the same texts per pass, so adapt
    rather than re-implement the scorer — the companion check must use the FROZEN instrument."""
    adapted = out_dir / "_relevance_adapted"
    adapted.mkdir(exist_ok=True)
    n = 0
    for f in sorted(out_dir.glob("*.json")):
        if f.name.startswith(("manifest", "smoke_", "_")):
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        if not r.get("complete"):
            continue
        (adapted / f"p7_results_{r['_meta']['arm']}_s{r['_meta']['seed']}.json").write_text(
            json.dumps({"coupled_full": {
                "snapshots": [p["state_text"] for p in r["passes"]],
                "final_state": r["final_state"]}}, ensure_ascii=False), encoding="utf-8")
        n += 1
    print(f"adapted {n} record(s) -> {adapted}")
    print(f"now run the FROZEN scorer against them, e.g.:\n"
          f"  python {P7 / 'score_relevance_v2.py'} --glob \"{adapted / 'p7_results_*.json'}\"")
    print("NOTE: score_relevance_v2 globs its own directory; copy the adapted files next to it or "
          "pass an absolute glob it can resolve. Tier calls stay manual per RELEVANCE-CONTROL-V2.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/stageA_chain_gate")
    ap.add_argument("--relevance", action="store_true", help="adapt records for the frozen v2 scorer")
    args = ap.parse_args()
    out_dir = ROOT / args.out
    if args.relevance:
        relevance_adapter(out_dir)
        return
    by_arm = load_records(out_dir)
    if not by_arm:
        print(f"no complete records in {out_dir}")
        return
    reports = {arm: arm_report(arm, recs) for arm, recs in sorted(by_arm.items())}
    verdict(reports.get("student"), reports.get("floor"))


if __name__ == "__main__":
    main()
