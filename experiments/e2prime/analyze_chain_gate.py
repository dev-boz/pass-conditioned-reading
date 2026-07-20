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
    # A trailing period is NOT evidence of a clean stop when it sits inside a number: the observed
    # cut-offs land mid-literal ("weight>0."), which an endswith('.') test reads as a finished
    # sentence. The decisive signal would be the server's usage.completion_tokens, which these
    # records do not archive (fixed in the runner for later runs), so this stays a heuristic.
    if t and (re.search(r"\d[.,]$", t) or not t.endswith((".", "!", "?", '"', ")", "`"))):
        return "no_answer_line__decode_cap(heuristic)"
    return "no_answer_line__other"


def components(rec: dict) -> dict:
    """§5 joints. RECORD is warm: did the state EVER host it, per-pass, not just at close."""
    passes = rec["passes"]
    ever_map = any(p["flags"]["queried_mapping"] for p in passes)
    ever_val = any(p["flags"]["table_value_present"] for p in passes)
    ever_add = any(p["flags"]["adder_value_present"] for p in passes)
    fin = rec["final_flags"]
    return {
        "RECORD_mapping_ever": ever_map,
        "RECORD_tablevalue_ever": ever_val,
        "RECORD_adder_ever": ever_add,
        "RECORD_both_ever": ever_map and ever_add,
        "RETAIN_mapping_at_close": fin["queried_mapping"],
        "RETAIN_adder_at_close": fin["adder_value_present"],
        "RETAIN_both_at_close": fin["queried_mapping"] and fin["adder_value_present"],
        "LOST_after_recording": (ever_map and not fin["queried_mapping"]),
        "COMPOSE_returns_2353": rec["scoring"]["c3_close_returns_2353"],
        "candidate_success": rec["scoring"]["candidate_success"],
        "precomposed_in_state": fin["precomposed_answer"],
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
              f"{str(r['record_first_pass']):>6} {vt / max(ct, 1):>6.3f} "
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
    print(f"    RETAIN  both operands present at close     : {rate('RETAIN_both_at_close')}")
    print(f"    (lost after recording, retention failure)  : {rate('LOST_after_recording')}")
    print(f"    COMPOSE close returns 2353                 : {rate('COMPOSE_returns_2353')}")
    print(f"    state already held 2353 before close       : {rate('precomposed_in_state')}")
    print(f"    MECHANICAL candidate successes             : {rate('candidate_success')}"
          f"   <- hand-verify each before any verdict")

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
