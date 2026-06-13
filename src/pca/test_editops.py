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

print("editops OK (parser v2.1)")
