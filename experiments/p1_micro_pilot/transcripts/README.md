# P1 transcripts — manual review

One markdown transcript per arm (`coupled.md`, `input_staged_only.md`,
`output_staged_only.md`), each with all six passes: view stats, full prompt
(collapsed), raw model output, parsed edit ops with validity, and the
post-pass integration state.

**The judgment here is the maintainer's, by design** (brief §P1; the optional LLM
judge is stubbed and disabled). Suggested review questions, per v0.3 §4 M1:

1. Does the **coupled** arm's state at pass 6 integrate verbatim specifics
   (figures, dates, statutory refs) into a structure laid down early — or did
   the early scaffold constrain it?
2. Does **input-staged-only** (full detail demanded from pass 1 on compressed
   views) commit early to wrong/vague detail that later passes fail to revise?
3. Does **output-staged-only** (full document visible every pass) actually
   follow the staged demands, or does seeing everything collapse the stages?
4. Edit-op discipline: validity rates per pass; does any arm degrade into
   re-rendering instead of editing?

If coupling shows nothing here at the prompt level, training (E2′) is
unlikely to rescue it — that is this pilot's only gate function.

`*_states.json` files are machine-readable state snapshots per pass
(consumed by P2 and P3 for the coupled arm).

**Note (2026-06-13):** these transcripts are the **parser-v2.1** rerun (D22).
Validity is now ≈1.0 for all arms — the earlier malformation was a parser
artifact (the model names new entries via `ADD S3:` rather than anchoring).
Review questions 1–3 (does staging change *what* gets integrated and *when*)
are unaffected and remain the point; question 4 (edit-op discipline) is now
largely answered — discipline is high once the naming convention is accepted.
`OBSERVATIONS.md` is machine-generated with stated mean formulas.
