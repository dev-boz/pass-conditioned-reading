"""Smoke tests for the edit-op parser/state. Run: uv run python -m pca.test_editops"""

from .editops import IntegrationState, parse_ops

st = IntegrationState()
r1 = parse_ops(
    "ADD END: Scope of report\nADD END: Findings\n- ADD END: Recommendations\n"
    "some commentary line\nNO_CHANGE",
    st.ids(),
)
assert r1.valid == 4 and r1.candidate_lines == 4, (r1.valid, r1.candidate_lines)
st.apply(r1.ops)
assert [e["id"] for e in st.entries] == ["S1", "S2", "S3"], st.entries

r2 = parse_ops(
    "```\nREPLACE S2: Key findings with figures\nADD S2: Sub-point after findings\n"
    "REMOVE S3\nREPLACE S9: bad id\nADD WRONG: malformed\n```",
    st.ids(),
)
assert r2.valid == 3 and r2.candidate_lines == 5, (r2.valid, r2.candidate_lines)
assert abs(r2.validity_rate - 0.6) < 1e-9
st.apply(r2.ops)
assert [e["id"] for e in st.entries] == ["S1", "S2", "S4"], st.entries
assert st.entries[1]["text"] == "Key findings with figures"

snap = st.snapshot()
assert IntegrationState.from_snapshot(snap).render() == st.render()

# ---- parser v2: same-response resolution -------------------------------
# self-named sequential ADDs against an empty state (the dominant 7B pattern)
st3 = IntegrationState()
r3 = parse_ops(
    "ADD S1: Scope\nADD S2: Findings\nADD S3: Recommendations\nREPLACE S2: Key findings",
    st3.ids(), st3.next_id,
)
assert r3.valid == 4, (r3.valid, r3.invalid)
st3.apply(r3.ops)
assert [e["id"] for e in st3.entries] == ["S1", "S2", "S3"]
assert st3.entries[1]["text"] == "Key findings"

# ADD END followed by self-named continuation (coupled pass-1 pattern)
st4 = IntegrationState()
r4 = parse_ops("ADD END: Scope\nADD S2: Problems\nADD S3: Findings", st4.ids(), st4.next_id)
assert r4.valid == 3, (r4.valid, r4.invalid)
st4.apply(r4.ops)
assert [e["id"] for e in st4.entries] == ["S1", "S2", "S3"]

# naming may not shadow an existing id; dangling REPLACE/REMOVE still invalid
st5 = IntegrationState()
st5.apply(parse_ops("ADD END: first", st5.ids(), st5.next_id).ops)  # S1 exists
r5 = parse_ops("ADD S1: not self-named, S1 exists\nREPLACE S9: dangling", st5.ids(), st5.next_id)
assert r5.valid == 1 and r5.ops[0]["anchor"] == "S1", (r5.valid, r5.ops)  # insert-after, not append
assert len(r5.invalid) == 1

# v2.1: arbitrary-origin naming (e.g. copied from the system-prompt example)
# resolves through the alias map for the whole response
st6 = IntegrationState()
r6 = parse_ops("ADD S3: a\nADD S4: b\nREPLACE S4: c\nREMOVE S3", st6.ids(), st6.next_id)
assert r6.valid == 4, (r6.valid, r6.invalid)
st6.apply(r6.ops)
assert [(e["id"], e["text"]) for e in st6.entries] == [("S2", "c")], st6.entries

# ---- v3: content-addressed REPLACE/REMOVE + clobber guard (D31) ---------
# quoted REPLACE verifying against the target's current text
st7 = IntegrationState()
st7.apply(parse_ops(
    "ADD END: REGION_SURCHARGE_CENTS table: 23:988, 45:210 (pricing module)\n"
    "ADD END: FUNCTIONS: compute_line_surcharge, quote_line",
    st7.ids(), st7.next_id).ops)
r7 = parse_ops('REPLACE S1 "REGION_SURCHARGE_CENTS": REGION_SURCHARGE_CENTS table: '
               "23:988, 45:210, 67:455 (pricing module, updated)", st7.ids(), st7.next_id)
assert r7.valid == 1 and r7.ops[0].get("quote") == "REGION_SURCHARGE_CENTS", r7.ops
st7.apply(r7.ops)
assert "67:455" in st7.entries[0]["text"]

# quoted REPLACE addressed to the WRONG id → content wins, redirect to the matching entry
r8 = parse_ops('REPLACE S1 "FUNCTIONS": FUNCTIONS: compute_line_surcharge, quote_line, fuel_bp',
               st7.ids(), st7.next_id)
st7.apply(r8.ops)
assert "REGION_SURCHARGE_CENTS" in st7.entries[0]["text"], st7.entries    # table intact
assert "fuel_bp" in st7.entries[1]["text"], st7.entries                   # functions updated
assert st7.last_report["redirected"] and st7.last_report["redirected"][0]["to"] == "S2"

# quote matching nothing → blocked, state untouched
before = st7.render()
st7.apply(parse_ops('REPLACE S1 "NO_SUCH_CONTENT": overwrite attempt', st7.ids(), st7.next_id).ops)
assert st7.render() == before and st7.last_report["blocked"], st7.last_report

# quoted REMOVE misaddressed → redirects by content; table survives
st8 = IntegrationState.from_snapshot(st7.snapshot())
st8.apply(parse_ops('REMOVE S1 "FUNCTIONS"', st8.ids(), st8.next_id).ops)
assert len(st8.entries) == 1 and "REGION_SURCHARGE_CENTS" in st8.entries[0]["text"], st8.entries

# the P7 clobber regression (id-misaddressed quote-less REPLACE; observed n=2):
# `REPLACE S2: FUNCTIONS=…` where S2 holds the table and S3 holds the functions list
def _clobber_state(guard):
    st = IntegrationState(guard=guard)
    st.apply(parse_ops(
        "ADD END: MODULES: ingest, transform, validate, routing, billing\n"
        "ADD END: REGION_SURCHARGE_CENTS = {23: 988, 45: 210, 67: 455} 24-key region "
        "surcharge table (pricing/region_tables.py)\n"
        "ADD END: FUNCTIONS: compute_line_surcharge, quote_line, fuel_bp, dispatch",
        st.ids(), st.next_id).ops)
    return st

_op_clobber = ("REPLACE S2: FUNCTIONS=compute_line_surcharge, quote_line, dispatch, "
               "label, normalize_payload")

st9 = _clobber_state("block")
st9.apply(parse_ops(_op_clobber, st9.ids(), st9.next_id).ops)
assert "REGION_SURCHARGE_CENTS" in st9.entries[1]["text"], st9.entries    # blocked: table survives
assert st9.last_report["blocked"][0]["reason"] == "blocked_guard", st9.last_report

st10 = _clobber_state("redirect")
st10.apply(parse_ops(_op_clobber, st10.ids(), st10.next_id).ops)
assert "REGION_SURCHARGE_CENTS" in st10.entries[1]["text"], st10.entries  # table survives
assert "normalize_payload" in st10.entries[2]["text"], st10.entries       # write landed on FUNCTIONS

st11 = _clobber_state("off")                                              # legacy semantics preserved
st11.apply(parse_ops(_op_clobber, st11.ids(), st11.next_id).ops)
assert st11.entries[1]["text"].startswith("FUNCTIONS="), st11.entries     # off → the old clobber

# guard must NOT false-block a legitimate rewrite that shares vocabulary with its target
st12 = _clobber_state("block")
r12 = parse_ops("REPLACE S2: REGION_SURCHARGE_CENTS region surcharge table verified complete: "
                "24 keys incl 23:988", st12.ids(), st12.next_id)
st12.apply(r12.ops)
assert "verified complete" in st12.entries[1]["text"], st12.entries
assert not st12.last_report["blocked"], st12.last_report

# guard ignores REPLACEs whose text is novel relative to every entry (new content, low overlap)
st13 = _clobber_state("block")
st13.apply(parse_ops("REPLACE S1: overview of scheduling behaviour across passes",
                     st13.ids(), st13.next_id).ops)
assert "overview" in st13.entries[0]["text"], st13.entries
assert not st13.last_report["blocked"], st13.last_report

# STRICT mode blocks the same novel-content rewrite (the archived seed-2 slot-repurposing
# shape: surcharge entry overwritten by an unrelated module description; descriptor words
# like module/group/helpers are stopworded so they cannot inflate overlap)
st14 = _clobber_state("strict")
st14.apply(parse_ops(
    "REPLACE S2: Audit module (group 90) provides helpers: bucket_shard, rank_invoice, "
    "rank_node, format_invoice, filter_packet", st14.ids(), st14.next_id).ops)
assert "REGION_SURCHARGE_CENTS" in st14.entries[1]["text"], st14.entries   # table survives
assert st14.last_report["blocked"][0]["reason"] == "blocked_strict_repurpose", st14.last_report

# strict still allows the same rewrite when quote-authorized (content-address names the victim)
st15 = _clobber_state("strict")
st15.apply(parse_ops(
    'REPLACE S2 "REGION_SURCHARGE_CENTS": Audit module (group 90) provides helpers: '
    "bucket_shard, rank_invoice", st15.ids(), st15.next_id).ops)
assert "Audit module" in st15.entries[1]["text"], st15.entries
assert not st15.last_report["blocked"], st15.last_report

# duplicate-pair exemption (the P1 replay's false positive): two entries legitimately
# updated with IDENTICAL text in one batch must not flag each other
st16 = _clobber_state("block")
dup = "Recommendations: improvements suggested include better validation and clearer routing"
st16.apply(parse_ops(f"REPLACE S1 \"MODULES\": {dup}\nREPLACE S3: {dup}",
                     st16.ids(), st16.next_id).ops)
assert st16.entries[0]["text"] == dup and st16.entries[2]["text"] == dup, st16.entries
assert not st16.last_report["blocked"], st16.last_report

# ---- v3.1: multi-fragment + long quotes (the teacher-audit convention) -------------
# two quoted fragments, both matching the target → applied
st17 = IntegrationState()
st17.apply(parse_ops(
    "ADD END: Compensation disparity: military get family separation allowance, combat zone "
    "tax exclusion, 1yr disability salary continuation; civilians get 45 days\n"
    "ADD END: Health protection gaps: 52 missing assessments, 285 missing immunizations",
    st17.ids(), st17.next_id).ops)
r17 = parse_ops('REPLACE S1 "Compensation disparity" "civilians get 45 days": '
                "Compensation structures: hardship pay compared; disparity documented",
                st17.ids(), st17.next_id)
assert r17.valid == 1 and r17.ops[0]["quotes"] == ["Compensation disparity", "civilians get 45 days"], r17.ops
st17.apply(r17.ops)
assert st17.entries[0]["text"].startswith("Compensation structures"), st17.entries
assert not st17.last_report["blocked"], st17.last_report

# one fragment matching a DIFFERENT entry only → redirect by content (all fragments must match)
r18 = parse_ops('REPLACE S1 "Health protection gaps" "285 missing immunizations": '
                "Health gaps updated: 285 immunizations traced", st17.ids(), st17.next_id)
st17.apply(r18.ops)
assert "285 immunizations traced" in st17.entries[1]["text"], st17.entries
assert st17.last_report["redirected"], st17.last_report

# fragments matching different entries EACH but no single entry matching ALL → blocked
before17 = st17.render()
st17.apply(parse_ops('REPLACE S1 "Compensation structures" "285 immunizations traced": mash',
                     st17.ids(), st17.next_id).ops)
assert st17.render() == before17 and st17.last_report["blocked"], st17.last_report

# whole-entry quotes parse and verify (audit-observed: fragments of 444/483 chars —
# the teacher quotes the entire current entry; cap is 2000)
long_text = ("Systemic data tracking failure: no centralized system for civilian identity, "
             "movements, or health records; December 2006 policy mandated weekly electronic "
             "reporting and centralized health archives across all combatant commands, "
             "including location-specific deployment data, immunization histories, pre- and "
             "post-deployment assessments, TB screening outcomes, evacuation routing through "
             "Landstuhl, and quarterly reconciliation against component personnel rosters "
             "maintained by each service branch under the revised reporting directive")
assert len(long_text) > 400
st19 = IntegrationState()
st19.apply(parse_ops(f"ADD END: {long_text}", st19.ids(), st19.next_id).ops)
r19 = parse_ops(f'REPLACE S1 "{long_text}": {long_text} (audited 2007)',
                st19.ids(), st19.next_id)
assert r19.valid == 1, (r19.valid, r19.invalid)
st19.apply(r19.ops)
assert "(audited 2007)" in st19.entries[0]["text"]

print("editops OK (parser v2.1 + v3 content-addressing + v3.1 multi-fragment)")
