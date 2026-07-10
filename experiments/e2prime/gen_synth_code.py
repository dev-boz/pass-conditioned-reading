"""E2′ corpus slice (b): fresh-seed synthetic codebases from the fixture GENERATOR FAMILY.

Each doc is a filler-module codebase (the eval fixture's document class) carrying its own
per-seed planted structures — a constants table + a distant consumer, generic per-doc names —
so the teacher has real structure to record and bind. NOTHING from the eval fixture enters:
name pools are disjoint from every eval identifier, module category, PC stage-pool word, and
event-key resource; values are per-seed RNG. The generator-family distribution-overfit risk
is declared in docs/E2PRIME-PREREG.md §4 (slice b) and mitigated by slice (c).

Used by build_corpus.py; not run standalone in the normal flow.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from pca.textutils import n_tokens  # noqa: E402

# Pools disjoint from the eval fixture (its filler VERBS/NOUNS/MODULES, planted identifiers,
# PC stage pools, and event-key resources/actions are all avoided).
VERBS = ["assemble", "classify", "derive", "evaluate", "fold", "gather", "harden", "iterate",
         "journal", "marshal", "partition", "quantify", "refine", "stitch", "tabulate",
         "unify", "weave", "anchor", "braid", "carve", "distill", "emboss", "graft", "hoist"]
NOUNS = ["bundle", "chain", "cluster", "dossier", "grid", "hunk", "journal", "kernel",
         "lattice", "matrix", "outline", "pivot", "quorum", "relay", "stack", "tally",
         "vector", "beacon", "cradle", "duct", "flange", "gasket", "mast", "spool"]
MODULES = ["acquire/{}.py", "ledger/{}.py", "exporters/{}.py", "staging/{}.py",
           "archive/{}.py", "notify/{}.py", "sanitize/{}.py", "throttle/{}.py",
           "catalog/{}.py", "workers/{}.py", "feeds/{}.py", "planners/{}.py",
           "adapters/{}.py", "monitors/{}.py", "brokers/{}.py"]
TABLE_ADJ = ["tier", "band", "bracket", "grade", "step", "notch"]
TABLE_NOUN = ["points", "weights", "offsets", "quotas", "margins", "credits"]


def synth_doc(seed: int, target_tokens: int) -> dict:
    rng = random.Random(seed)

    def filler_function() -> str:
        v, n = rng.choice(VERBS), rng.choice(NOUNS)
        k = rng.randint(2, 4)
        args = ", ".join([n] + [f"{rng.choice(['opt', 'lim', 'flag', 'mode', 'span'])}{i}"
                                for i in range(k - 1)])
        c1, c2, c3 = rng.randint(2, 97), rng.randint(100, 999), round(rng.uniform(0.1, 0.95), 3)
        return "\n".join([
            f"def {v}_{n}({args}):",
            f'    """{v.capitalize()} the {n} for the downstream {rng.choice(NOUNS)} stage."""',
            "    acc = []",
            f"    for i, x in enumerate({n} or []):",
            f"        if i % {c1} == 0 and x is not None:",
            f"            acc.append((x, i * {c2}))",
            f"        elif x and getattr(x, 'load', 0) > {c3}:",
            "            acc.append((x, i))",
            "    return [t for t in acc if t[1] >= 0]",
            "",
        ])

    def filler_module(idx: int) -> str:
        path = MODULES[idx % len(MODULES)].format(rng.choice(NOUNS) + str(idx))
        out = [f"# ===== module: {path} =====",
               f'"""Auto-composed {path.split("/")[0]} helpers (group {idx})."""', ""]
        out += [filler_function() for _ in range(rng.randint(4, 7))]
        return "\n".join(out)

    def plant_pair(tag: int) -> tuple[str, str]:
        """A per-doc split structure: a constants table + a distant consumer that uses it
        without restating values (generic bind-shaped content; names/values per-seed)."""
        tname = f"{rng.choice(TABLE_ADJ).upper()}_{rng.choice(TABLE_NOUN).upper()}_{tag}"
        fname = f"apply_{rng.choice(VERBS)}_{rng.choice(NOUNS)}_{tag}"
        adj_name = f"BASE_{rng.choice(TABLE_NOUN).upper()}_{tag}"
        keys = sorted(rng.sample(range(10, 99), rng.randint(8, 16)))
        cat_t, cat_f = rng.sample(MODULES, 2)
        table_mod = "\n".join(
            [f"# ===== module: {cat_t.format('rates' + str(tag))} =====",
             f'"""{tname} schedule (set by the ops review; values are not derived)."""', "",
             f"{tname} = {{"]
            + [f"    {k}: {rng.randint(101, 989)}," for k in keys]
            + ["}", ""])
        consumer_mod = "\n".join([
            f"# ===== module: {cat_f.format('applyrules' + str(tag))} =====",
            f"from {cat_t.split('/')[0]}.rates{tag} import {tname}",
            "",
            f"{adj_name} = {rng.randint(1001, 1999)}",
            "",
            f"def {fname}(code):",
            f'    """Total adjusted value for `code`: the scheduled base plus the fixed adder."""',
            f"    return {tname}[code] + {adj_name}",
            "",
        ])
        return table_mod, consumer_mod

    blocks: list[str] = []
    idx = 0
    while sum(n_tokens(b) for b in blocks) < target_tokens:
        blocks.append(filler_module(idx))
        idx += 1
    n = len(blocks)
    plants = [plant_pair(t) for t in range(rng.randint(2, 4))]
    inserts = []
    for t, (tm, cm) in enumerate(plants):
        f1 = rng.uniform(0.15, 0.45)
        f2 = min(0.88, f1 + rng.uniform(0.25, 0.45))
        inserts += [(int(n * f1), tm), (int(n * f2), cm)]
    for shift, (pos, text) in enumerate(sorted(inserts, key=lambda x: x[0])):
        blocks.insert(min(pos + shift, len(blocks)), text)

    return {"doc_id": f"synthcode-{seed:05d}", "kind": "code", "blocks": blocks,
            "provenance": {"generator": "gen_synth_code.py", "seed": seed,
                           "n_plants": len(plants),
                           "total_tokens": sum(n_tokens(b) for b in blocks)}}
