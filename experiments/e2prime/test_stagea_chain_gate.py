"""Model-free validation of the Stage-A chain-gate instrument (run before serving any model).

The chain gate's scoring is a MECHANICAL PRE-FILTER whose job is to flag candidates for hand
verification. A pre-filter that silently mis-reads a state is worse than no pre-filter, so its
behaviour is pinned here: the four addendum conditions, the digit-boundary discipline (1365 must
not match inside 213650), and one full run_draw over a scripted fake server — which exercises
parse -> strict apply -> flags -> closing -> resumable JSON without a GPU.

  python experiments/e2prime/test_stagea_chain_gate.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from stagea_chain_gate import (build_passes, closing_flags, load_config,  # noqa: E402
                               run_draw, state_flags, P7)

SPEC = json.loads((P7 / "fixture" / "fixture_spec.json").read_text(encoding="utf-8"))
FAILS: list[str] = []


def check(name: str, got, want) -> None:
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {name}: got {got!r}, want {want!r}")
    if not ok:
        FAILS.append(name)


# --------------------------------------------------------------- state_flags
print("state_flags — RECORD / RETAIN / pre-composition pre-filters")

empty = state_flags("(empty — no entries yet)", SPEC)
check("empty: queried_mapping", empty["queried_mapping"], False)
check("empty: adder_value_present", empty["adder_value_present"], False)
check("empty: precomposed_answer", empty["precomposed_answer"], False)

held = state_flags(
    "S1: pricing/region_tables.py defines REGION_SURCHARGE_CENTS = {10: 314, 23: 988, 41: 502}\n"
    "S2: fulfillment/line_quote.py sets RECONCILIATION_ADDER_CENTS = 1365 and defines "
    "compute_line_surcharge(region_code).", SPEC)
check("held: queried_mapping", held["queried_mapping"], True)
check("held: adder_named", held["adder_named"], True)
check("held: adder_value_present", held["adder_value_present"], True)
check("held: precomposed_answer", held["precomposed_answer"], False)

# the state may wrap an entry across lines — the flag flattens whitespace first
wrapped = state_flags("S1: REGION_SURCHARGE_CENTS maps\n   23:   988\nand more", SPEC)
check("wrapped/multiline: queried_mapping", wrapped["queried_mapping"], True)

# digit-boundary discipline: neighbouring digits must not manufacture a hit
decoy = state_flags("S1: batch 213650 processed 9880 items; ticket 23532 closed", SPEC)
check("decoy 213650: adder_value_present", decoy["adder_value_present"], False)
check("decoy 9880: table_value_present", decoy["table_value_present"], False)
check("decoy 23532: precomposed_answer", decoy["precomposed_answer"], False)

# a state that already carries the ANSWER disqualifies the draw (addendum condition 2)
pre = state_flags("S1: compute_line_surcharge(23) returns 2353 in total.", SPEC)
check("precomposed 2353: precomposed_answer", pre["precomposed_answer"], True)

# the queried mapping must be the 23->988 pair, not 988 loose in the text
loose = state_flags("S1: surcharges range from 314 to 988 cents across regions.", SPEC)
check("loose 988 (no pair): queried_mapping", loose["queried_mapping"], False)
check("loose 988: table_value_present", loose["table_value_present"], True)

# a wrong-region pair must not read as the queried mapping. 10->314 and 42->915 are real table
# rows; 41->502 is invented, so the coverage count must see exactly two.
wrong = state_flags("S1: REGION_SURCHARGE_CENTS = {10: 314, 42: 915, 41: 502}", SPEC)
check("wrong region pair: queried_mapping", wrong["queried_mapping"], False)
check("table coverage counts only real pairs", wrong["kv_count"], 2)


# --------------------------------------------------------------- closing_flags
print("\nclosing_flags — the four addendum end-to-end conditions")

good_final = {"queried_mapping": True, "adder_value_present": True, "precomposed_answer": False}
derived = "The state holds 23 -> 988 and the adder 1365, so 988 + 1365 = 2353.\nANSWER: 2353"
s = closing_flags(derived, 2353, SPEC, good_final)
check("clean chain: candidate_success", s["candidate_success"], True)
check("clean chain: requires_hand_verification", s["requires_hand_verification"], True)

# right answer, but the state had already composed it -> not a chain demonstration
s = closing_flags(derived, 2353, SPEC, {**good_final, "precomposed_answer": True})
check("pre-composed state: candidate_success", s["candidate_success"], False)
check("pre-composed state: c2 fails", s["c2_no_precomposed_2353"], False)

# right answer with no operands visible in the close -> a guess, not a derivation
s = closing_flags("ANSWER: 2353", 2353, SPEC, good_final)
check("bare answer: c4_derivation_visible", s["c4_derivation_visible_in_close"], False)
check("bare answer: candidate_success", s["candidate_success"], False)

# operands held but the close did not compose them
s = closing_flags("The state gives 988 and 1365 but no total.\nANSWER: INSUFFICIENT",
                  None, SPEC, good_final)
check("compose-blocked: c3_close_returns_2353", s["c3_close_returns_2353"], False)
check("compose-blocked: candidate_success", s["candidate_success"], False)

# operands never recorded
s = closing_flags(derived, 2353, SPEC, {**good_final, "queried_mapping": False})
check("record-blocked: c1_operands_in_final_state", s["c1_operands_in_final_state"], False)

# wrong integer
s = closing_flags("988 + 1365 = 2453.\nANSWER: 2453", 2453, SPEC, good_final)
check("wrong sum: candidate_success", s["candidate_success"], False)


# --------------------------------------------------------------- run_draw, fake server
print("\nrun_draw — parse -> strict apply -> flags -> closing -> resumable JSON (no GPU)")


class FakeServer:
    """Scripted recorder. Pass 1 ADDs a scaffold entry; pass 2 records the queried mapping with a
    content-addressed REPLACE; pass 3 attempts an UNQUOTED slot-repurposing rewrite of that same
    entry — which guard='strict' must refuse, leaving 23: 988 in the state (the D31 clobber
    mechanism, replayed here as an instrument check)."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def chat(self, system, user, max_tokens=900, temperature=0.0, seed=42):
        self.calls.append((system, user))
        n = len(self.calls)
        if "FINAL STATE:" in user:                      # the closing turn
            return {"text": "State holds 23: 988 and RECONCILIATION_ADDER_CENTS = 1365, "
                            "so 988 + 1365 = 2353.\nANSWER: 2353", "wall_s": 0.1}
        if n == 1:
            return {"text": "ADD END: pricing/ holds the region surcharge schedule.", "wall_s": 0.1}
        if n == 2:
            return {"text": 'REPLACE S1 "region surcharge schedule": pricing/region_tables.py: '
                            "REGION_SURCHARGE_CENTS = {10: 314, 23: 988}; "
                            "RECONCILIATION_ADDER_CENTS = 1365 in fulfillment/line_quote.py.",
                    "wall_s": 0.1}
        return {"text": "REPLACE S1: routing/ groups the event dispatch helpers and labels.",
                "wall_s": 0.1}

    def stop(self):
        return


cfg = load_config()
check("config guard is strict", cfg["harness"]["guard"], "strict")
check("config op cap is 24", cfg["harness"]["op_cap"], 24)

scaffold = json.loads((P7 / "scaffold_struct.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(P7))
from pca.planted import build_schedule                     # noqa: E402
from verify_fixture import load_turns                      # noqa: E402

turns = load_turns(P7 / "fixture" / "host_doc.jsonl")
sc = cfg["schedule"]["code"]
passes = build_passes(build_schedule(turns, sc["V"], sc["R"], tuple(sc["stage_fracs"])), scaffold)
check("K", len(passes), 31)
check("Phase-A views come from the frozen scaffold",
      all(p["view_source"] == "frozen_scaffold_v2" for p in passes[:6]), True)
check("Phase-A view text is the frozen scaffold text",
      passes[1]["view_text"] == scaffold[1]["view_text"], True)

srv = FakeServer()
with tempfile.TemporaryDirectory() as td:
    out = Path(td) / "fake_s1_t0.7.json"
    rec = run_draw(srv, passes, SPEC, cfg, seed=1, temp=0.7, out_path=out,
                   meta={"arm": "fake", "model": "none", "verdict_eligible": False,
                         "addendum_committed": False},
                   max_tokens=900, max_passes=3)
    check("record written", out.exists(), True)
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    check("record round-trips through JSON", on_disk["complete"], True)
    check("passes recorded", len(on_disk["passes"]), 3)

check("strict guard refused the unquoted repurposing rewrite",
      rec["passes"][2]["apply_report"]["blocked"][0]["reason"], "blocked_strict_repurpose")
check("queried mapping survived the clobber attempt",
      rec["final_flags"]["queried_mapping"], True)
check("RECORD first seen on pass 2", rec["record_first_pass"], 2)
check("closing answer parsed", rec["closing"]["answer"], 2353)
check("candidate flagged for hand verification",
      rec["scoring"]["candidate_success"], True)
check("per-pass archive keeps the prompts", bool(rec["passes"][0]["system"]
      and rec["passes"][0]["user"]), True)
check("per-pass archive keeps raw output", bool(rec["passes"][0]["raw_output"]), True)

# the recorder prompt the fake server saw must carry the addendum need class and no probe token
sys_seen = srv.calls[0][0]
check("recorder prompt carries the query-conditioned need class",
      "operational questions about this codebase's pricing" in sys_seen, True)
check("recorder prompt names no probe identifier",
      any(t in sys_seen for t in ("REGION_SURCHARGE", "compute_line_surcharge", "988", "1365")),
      False)

print(f"\n{'ALL CHECKS PASS' if not FAILS else 'FAILURES: ' + ', '.join(FAILS)}")
sys.exit(1 if FAILS else 0)
