"""Edit-operation format, parser, and integration state (DECISIONS.md D15).

The parent names four ops (README §3 step 3) but defines no syntax. Concrete
line-oriented grammar, one op per line:

    ADD END: <text>          append a new entry at the end of the state
    ADD <id>: <text>         insert a new entry AFTER entry <id>
    REPLACE <id>: <text>     replace entry <id>'s text
    REMOVE <id>              delete entry <id>
    NO_CHANGE                this pass contributes nothing

State entries carry stable ids S1, S2, ... (never reused). Validity metric:
valid_ops / candidate_op_lines, where a candidate line is any line that
starts with an op keyword and a valid op must match the grammar AND
reference a resolvable id.

Parser v2.1 (2026-06-13): models pervasively treat `ADD <id>` as *naming* the
entry they are creating (sequentially, from whatever origin — S1, the example
id in the system prompt, or max-visible+1 — never the harness's hidden
counter). Resolution rules:
- An ADD whose anchor resolves (existing state, or an id created earlier in
  the same response) is an insert-after at that anchor.
- An ADD whose anchor does NOT resolve is a named append: the name is mapped
  to the id the harness actually assigns, and later ops in the same response
  referencing that name resolve through the alias map.
- REPLACE/REMOVE must reference a resolvable id (state, same-response
  creation, or alias); dangling references remain invalid.
Consequence: ADD validity is grammar-only; REPLACE/REMOVE carry the
reference-validity signal. Parser v1 (strict anchors) rejected the naming
convention wholesale and v2.0 (same-origin self-naming only) under-fixed it;
archived numbers live under *_parser-v1 paths. See DECISIONS.md D15/D22.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_OP_START = re.compile(r"^\s*(?:[-*]\s*|\d+[.)]\s*)?(ADD|REPLACE|REMOVE|NO_CHANGE)\b(.*)$", re.I)
_ADD_RE = re.compile(r"^\s+(END|S\d+)\s*:\s*(.+)$", re.I | re.S)
_REPLACE_RE = re.compile(r"^\s+(S\d+)\s*:\s*(.+)$", re.I | re.S)
_REMOVE_RE = re.compile(r"^\s+(S\d+)\s*\.?\s*$", re.I)


@dataclass
class ParseResult:
    ops: list[dict] = field(default_factory=list)
    candidate_lines: int = 0
    valid: int = 0
    invalid: list[str] = field(default_factory=list)

    @property
    def validity_rate(self) -> float:
        return self.valid / self.candidate_lines if self.candidate_lines else 0.0


def strip_fences(text: str) -> str:
    return re.sub(r"^```[a-zA-Z]*\s*$", "", text, flags=re.M).strip()


def parse_ops(raw_output: str, existing_ids: set[str], next_id: int = 1) -> ParseResult:
    """Parse ops. `next_id` is the state's next id counter; ids that valid ADDs
    in this response will be assigned (S{next_id}, S{next_id+1}, ... in order)
    are resolvable by subsequent ops in the same response (parser v2)."""
    res = ParseResult()
    pending: list[str] = []   # ids same-response ADDs will create, in order
    alias: dict[str, str] = {}  # model-chosen name -> harness-assigned pending id

    def resolve(i: str) -> str | None:
        if i in existing_ids or i in pending:
            return i
        return alias.get(i)

    for line in strip_fences(raw_output).splitlines():
        m = _OP_START.match(line)
        if not m:
            continue
        res.candidate_lines += 1
        kw, rest = m.group(1).upper(), m.group(2)
        op = None
        if kw == "NO_CHANGE" and rest.strip(" .") == "":
            op = {"op": "NO_CHANGE"}
        elif kw == "ADD":
            m2 = _ADD_RE.match(rest)
            if m2:
                anchor = m2.group(1).upper()
                would_be = f"S{next_id + len(pending)}"
                text = m2.group(2).strip()
                if anchor == "END":
                    op = {"op": "ADD", "anchor": "END", "text": text}
                elif (r := resolve(anchor)) is not None:
                    op = {"op": "ADD", "anchor": r, "text": text}
                else:
                    # v2.1: unresolvable ADD anchor = the model naming its new
                    # entry; append, and remember the name it used
                    op = {"op": "ADD", "anchor": "END", "text": text}
                    alias[anchor] = would_be
                pending.append(would_be)
        elif kw == "REPLACE":
            m2 = _REPLACE_RE.match(rest)
            if m2 and (r := resolve(m2.group(1).upper())) is not None:
                op = {"op": "REPLACE", "id": r, "text": m2.group(2).strip()}
        elif kw == "REMOVE":
            m2 = _REMOVE_RE.match(rest)
            if m2 and (r := resolve(m2.group(1).upper())) is not None:
                op = {"op": "REMOVE", "id": r}
        if op:
            res.ops.append(op)
            res.valid += 1
        else:
            res.invalid.append(line.strip()[:160])
    return res


class IntegrationState:
    """Ordered entries with stable ids; apply() consumes parsed ops."""

    def __init__(self) -> None:
        self.entries: list[dict] = []
        self._next = 1

    def ids(self) -> set[str]:
        return {e["id"] for e in self.entries}

    @property
    def next_id(self) -> int:
        return self._next

    def _new_id(self) -> str:
        i = f"S{self._next}"
        self._next += 1
        return i

    def apply(self, ops: list[dict]) -> int:
        applied = 0
        for op in ops:
            if op["op"] == "NO_CHANGE":
                continue
            if op["op"] == "ADD":
                entry = {"id": self._new_id(), "text": op["text"]}
                if op["anchor"] == "END":
                    self.entries.append(entry)
                else:
                    pos = next((i for i, e in enumerate(self.entries) if e["id"] == op["anchor"]), None)
                    if pos is None:
                        continue
                    self.entries.insert(pos + 1, entry)
                applied += 1
            elif op["op"] == "REPLACE":
                for e in self.entries:
                    if e["id"] == op["id"]:
                        e["text"] = op["text"]
                        applied += 1
                        break
            elif op["op"] == "REMOVE":
                n0 = len(self.entries)
                self.entries = [e for e in self.entries if e["id"] != op["id"]]
                applied += n0 - len(self.entries)
        return applied

    def render(self) -> str:
        if not self.entries:
            return "(empty — no entries yet)"
        return "\n".join(f"{e['id']}: {e['text']}" for e in self.entries)

    def snapshot(self) -> dict:
        return {"entries": [dict(e) for e in self.entries], "next": self._next}

    @classmethod
    def from_snapshot(cls, snap: dict) -> "IntegrationState":
        st = cls()
        st.entries = [dict(e) for e in snap["entries"]]
        st._next = snap["next"]
        return st
