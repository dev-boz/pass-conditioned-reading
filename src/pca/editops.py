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

Parser/state v3 (2026-07-10, D31): content-addressed destructive ops — the
harness answer to the P7 id-misaddressing clobber (`REPLACE S3: FUNCTIONS=…`
overwrote the surcharge table held at S3; observed n=2, warm go-signal seed-2
and fair-shot seed-42; CONSOLIDATED-FINDINGS §6.2, E2PRIME-CRITERION §1 P-A).

    REPLACE <id> "<quote>": <text>   quote = verbatim fragment of the CURRENT
    REMOVE <id> "<quote>"            text of the entry the op intends to hit

Apply-time semantics (parse-time validity is UNCHANGED — metric continuity
with v2.1):
- Quoted op, quote matches the id'd entry's current text → apply.
- Quoted op, quote does NOT match the target but matches exactly one other
  entry → the content wins: REDIRECT to that entry (logged).
- Quoted op, quote matches nothing (or several) → BLOCK (logged); state
  untouched.
- Quote-less REPLACE under guard mode ("block" | "redirect"; default "off" =
  v2.1 behaviour): if the new text has near-zero overlap with the target's
  current text but strongly matches exactly one other entry (Jaccard or
  lead-token rule), the write is suspicious → block or redirect per mode.
  Quote-less REMOVE carries no content signal and is never guarded.
Both new syntactic forms were invalid under v2.1, so no archived valid op
changes meaning. Guard thresholds are initial values validated by the P-A
false-block replay before E2′ data generation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_OP_START = re.compile(r"^\s*(?:[-*]\s*|\d+[.)]\s*)?(ADD|REPLACE|REMOVE|NO_CHANGE)\b(.*)$", re.I)
_ADD_RE = re.compile(r"^\s+(END|S\d+)\s*:\s*(.+)$", re.I | re.S)
# v3.1 (2026-07-10, teacher-audit finding — the D22 lesson applied to quotes): models emit
# MULTIPLE quoted fragments ("label" "content") and fragments longer than 160 chars. Both
# are good content-addressing; the grammar accepts 1+ fragments of 4–400 chars each. Every
# fragment must match the target (redirect requires a unique entry matching ALL fragments).
_QUOTE_REGION = r"((?:\"[^\"]{4,400}\"\s*)+)"
_QUOTE_FRAG = re.compile(r"\"([^\"]{4,400})\"")
_REPLACE_RE = re.compile(r"^\s+(S\d+)\s*" + _QUOTE_REGION + r"?:\s*(.+)$", re.I | re.S)
_REMOVE_RE = re.compile(r"^\s+(S\d+)\s*" + _QUOTE_REGION + r"?\.?\s*$", re.I)

# v3 guard thresholds — initial values, validated by the P-A false-block replay
# (E2PRIME-CRITERION §1) and frozen before E2′ data generation.
GUARD_JACCARD_TARGET_MAX = 0.10   # below this vs the target, a quote-less REPLACE is a mismatch…
GUARD_JACCARD_OTHER_MIN = 0.50    # …if some other single entry matches this strongly,
GUARD_LEAD_JACCARD_MIN = 0.15     # …or shares the new text's lead token at this overlap.

# Document-class-general STRUCTURE descriptors, excluded from overlap scoring: they describe
# that something is being catalogued, not what. The archived seed-2 slot-repurposing overwrite
# scored Jaccard 0.19 against its victim purely on module/group/helpers-type tokens (P-A replay,
# 2026-07-10); content overlap after exclusion is 0. Class-general by design — no fixture-,
# probe-, or domain-specific words may enter this list (probe-blind discipline).
_DESCRIPTOR_STOPWORDS = frozenset({
    "module", "modules", "group", "groups", "helper", "helpers", "function", "functions",
    "provides", "provide", "defines", "define", "includes", "include", "contains", "contain",
    "section", "sections", "entry", "entries", "item", "items", "note", "notes",
    "various", "several", "misc", "list", "lists",
})


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _words(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]{3,}", s.lower())) - _DESCRIPTOR_STOPWORDS


def _jaccard(a: str, b: str) -> float:
    wa, wb = _words(a), _words(b)
    return len(wa & wb) / len(wa | wb) if wa | wb else 0.0


def _lead(s: str) -> str | None:
    m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]{2,})", s)
    return m.group(1).upper() if m else None


@dataclass
class ParseResult:
    ops: list[dict] = field(default_factory=list)
    candidate_lines: int = 0
    valid: int = 0
    invalid: list[str] = field(default_factory=list)
    aliased: int = 0   # ops resolved via the v2.1 named-append alias map (P4 misplacement audit)

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
                    res.aliased += 1
                pending.append(would_be)
        elif kw == "REPLACE":
            m2 = _REPLACE_RE.match(rest)
            if m2 and (r := resolve(m2.group(1).upper())) is not None:
                op = {"op": "REPLACE", "id": r, "text": m2.group(3).strip()}
                if m2.group(2):
                    frags = [f.strip() for f in _QUOTE_FRAG.findall(m2.group(2))]
                    op["quotes"] = frags
                    op["quote"] = " ".join(frags)   # display/back-compat
                if m2.group(1).upper() in alias:
                    res.aliased += 1
        elif kw == "REMOVE":
            m2 = _REMOVE_RE.match(rest)
            if m2 and (r := resolve(m2.group(1).upper())) is not None:
                op = {"op": "REMOVE", "id": r}
                if m2.group(2):
                    frags = [f.strip() for f in _QUOTE_FRAG.findall(m2.group(2))]
                    op["quotes"] = frags
                    op["quote"] = " ".join(frags)
                if m2.group(1).upper() in alias:
                    res.aliased += 1
        if op:
            res.ops.append(op)
            res.valid += 1
        else:
            res.invalid.append(line.strip()[:160])
    return res


class IntegrationState:
    """Ordered entries with stable ids; apply() consumes parsed ops.

    v3: `guard` governs quote-less REPLACE ("off" = v2.1 semantics, "block"
    refuses suspicious mismatched writes, "redirect" re-addresses them by
    content). Quoted REPLACE/REMOVE are always content-verified regardless of
    guard. Every apply() records per-op outcomes in `last_report`.
    """

    def __init__(self, guard: str = "off") -> None:
        assert guard in ("off", "block", "redirect", "strict"), guard
        self.entries: list[dict] = []
        self._next = 1
        self.guard = guard
        self.last_report: dict = {"applied": 0, "blocked": [], "redirected": []}

    def ids(self) -> set[str]:
        return {e["id"] for e in self.entries}

    @property
    def next_id(self) -> int:
        return self._next

    def _new_id(self) -> str:
        i = f"S{self._next}"
        self._next += 1
        return i

    def _content_target(self, op: dict, batch_written: set[str]) -> tuple[dict | None, str | None]:
        """v3 target resolution for a destructive op. Returns (entry, note):
        note None = plain apply; "redirected_*" = apply to `entry` with logging;
        entry None = do not apply (note is the block reason, or "missing_id").
        `batch_written` holds normalized texts already written in THIS apply() batch —
        entries just given identical text are exempt from candidacy (the P1 replay's
        duplicate-pair false positive: two entries legitimately updated with the same
        text in one pass must not flag each other)."""
        target = next((e for e in self.entries if e["id"] == op["id"]), None)
        if target is None:
            return None, "missing_id"
        frags = op.get("quotes") or ([op["quote"]] if op.get("quote") else [])
        if frags:
            fn = [_norm(f) for f in frags if _norm(f)]
            tn = _norm(target["text"])
            if fn and all(f in tn for f in fn):
                return target, None
            matches = [e for e in self.entries
                       if all(f in _norm(e["text"]) for f in fn)]
            if len(matches) == 1:
                return matches[0], "redirected_quote"
            return None, "blocked_quote_mismatch"
        if op["op"] == "REPLACE" and self.guard != "off":
            if _norm(op["text"]) in batch_written:
                return target, None  # same text already written this batch → duplicate update
            if _jaccard(op["text"], target["text"]) < GUARD_JACCARD_TARGET_MAX:
                others = [e for e in self.entries
                          if e is not target and _norm(e["text"]) not in batch_written]
                strong = [e for e in others
                          if _jaccard(op["text"], e["text"]) >= GUARD_JACCARD_OTHER_MIN]
                lead = _lead(op["text"])
                leadm = [e for e in others
                         if lead and _lead(e["text"]) == lead and _lead(target["text"]) != lead
                         and _jaccard(op["text"], e["text"]) >= GUARD_LEAD_JACCARD_MIN]
                cand = strong or leadm
                if len(cand) == 1:
                    if self.guard == "redirect":
                        return cand[0], "redirected_guard"
                    return None, "blocked_guard"
                if cand:
                    return None, "blocked_guard_ambiguous"
                if self.guard == "strict":
                    # slot-repurposing shape (the archived seed-2 instance): novel content,
                    # near-zero overlap with the entry it overwrites, no matching entry
                    # anywhere. Under strict, a quote is REQUIRED to authorize such a
                    # rewrite; without one the write is refused.
                    return None, "blocked_strict_repurpose"
        return target, None

    def apply(self, ops: list[dict]) -> int:
        applied = 0
        report: dict = {"applied": 0, "blocked": [], "redirected": []}
        batch_written: set[str] = set()   # normalized texts written by THIS batch's REPLACEs
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
            elif op["op"] in ("REPLACE", "REMOVE"):
                target, note = self._content_target(op, batch_written)
                if target is None:
                    if note != "missing_id":
                        report["blocked"].append({"op": dict(op), "reason": note})
                    continue
                if note:
                    report["redirected"].append(
                        {"from": op["id"], "to": target["id"], "via": note, "op": dict(op)})
                if op["op"] == "REPLACE":
                    target["text"] = op["text"]
                    batch_written.add(_norm(op["text"]))
                else:
                    self.entries = [e for e in self.entries if e is not target]
                applied += 1
        report["applied"] = applied
        self.last_report = report
        return applied

    def render(self) -> str:
        if not self.entries:
            return "(empty — no entries yet)"
        return "\n".join(f"{e['id']}: {e['text']}" for e in self.entries)

    def snapshot(self) -> dict:
        return {"entries": [dict(e) for e in self.entries], "next": self._next}

    @classmethod
    def from_snapshot(cls, snap: dict, guard: str = "off") -> "IntegrationState":
        st = cls(guard=guard)
        st.entries = [dict(e) for e in snap["entries"]]
        st._next = snap["next"]
        return st
