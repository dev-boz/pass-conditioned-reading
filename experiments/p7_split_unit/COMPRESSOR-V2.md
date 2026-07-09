# P7 — Compressor v2 (the compressor as ARCHITECTURE) · for review before any battery

## The reframe

The Phase-A compressor is **part of the architecture, not generic preprocessing.** v1 (keep every
signature, drop bodies) produced **homogeneous views** — every Phase-A chunk was the same
header+signature wall — and that representation *caused* the integration model to destructively
re-compress its own state into churning `MODULES`/`FUNCTIONS` aggregates and clobber the standalone
table (RESULTS.md pass-3 diagnostic). So the prior "retention failure" was substantially a
**representation failure**: the views invited the re-compression churn. Building a compressor that
serves the pass-conditioned schedule is legitimate architecture development.

## The three lines this work holds

1. **Tuned on the DOCUMENT CLASS, blind to the probe.** Every design choice below is justified on
   general properties of code, with **no reference to the region-23 / surcharge probe**. (Tables are
   preserved because *code modules define constants and tables that callers depend on* — full stop —
   not because a question asks about one.)
2. **The compressor is ARCHITECTURE → frozen and pre-registered, not iterated to taste.** ONE
   principled design, justified blind, frozen to `scaffold_struct.json`, then run **once**. The
   survival result below is **not** a license to re-tune until the table survives.
3. **The integration prompt stays NEUTRAL (unchanged).** My earlier attempt-2/3 prompt additions
   ("record data structures…", "don't enumerate…") were **reverted**: `SYSTEM`/`RUBRIC`/`TASK` in
   `run.py` are back to the P6-lineage broad "build a comprehensive analytical brief" with **no**
   append-only / anti-rewrite / data-structure directives. Only the compressor (what the
   architecture *shows* the model) changed — never the instructions (how the model is told to think).

## The v2 compressor (`compress_code.py`) — design choices, each justified probe-blind

Foreground each module's **distinctive declarations**; collapse the repetitive boilerplate:

| choice | what it does | document-class justification (probe-blind) |
|---|---|---|
| foreground module-level **constants / literals** (incl. multi-line dict/list/tuple), verbatim | keeps `NAME = {...}` blocks whole | module-level constants and tables are the declarations callers depend on; high-information; a codebase brief must capture them |
| keep **imports** | keeps `import` / `from … import …` | imports are the module's dependency / call-graph edges |
| keep **class** defs (+ method sigs where present) | keeps type structure | classes are the type structure of the code |
| **collapse free functions** to a one-line name digest (`defines helpers: a, b, c`) | drops per-function `def …:` signatures | in helper modules the individual signatures are low-information and near-uniform; helper *names* suffice for a brief — **this is the heterogeneity lever** (removes the uniform signature-wall volume) |
| keep module docstrings / comments | keeps module purpose & constant-explaining notes | distinctive context |
| drop function/method **bodies** | — | the bulk, low-information |

A skeptic who has never seen the probe accepts all six: "a codebase brief preserves module constants,
tables, imports, and public/type structure, and summarizes boilerplate helpers." No choice mentions
the probe; **all** constants/tables are foregrounded symmetrically (the neutral control table too),
not just the answer table.

## Realized-view guards (`verify_fixture.py`) — PASS on v2 views

(A) on-source; (B) both fragments mid-exclusive → dense a true floor; (C1) the table entry `23: 988`
+ the adder survive into the realized Phase-A views (architecture carries the structure); (C2) no
single Phase-B tile holds both fragments (tiles 5 vs 18, gap 13 — split is real).

## Heterogeneity check (`heterogeneity_check.py`) — the thing v2 fixes, quantified

Per-chunk structural profile (lines by kind) on the frozen v2 scaffold:

| chunk | tokens | HDR | DIGEST | CONSTROW | IMPORT | ASSIGN | in kind |
|---|---|---|---|---|---|---|---|
| 0 | 868 | 20 | 20 | 0 | 0 | 0 | pure-helper |
| **1** | 1055 | 19 | 19 | **24** | 0 | 1 | **answer table** |
| **2** | 945 | 19 | 19 | **12** | 0 | 1 | **control table** |
| **3** | 910 | 20 | 20 | 0 | **1** | **1** | **adder + import** |
| 4 | 914 | 21 | 21 | 0 | 0 | 0 | pure-helper |
| 5 | 175 | 4 | 4 | 0 | 0 | 0 | pure-helper |

Constant-bearing chunks (1, 2, 3) are **profile-distinct** from the pure-helper chunks (0, 4, 5,
CONSTROW=0). v2 view tokens ≈ **900** vs v1's ≈ **1800** uniform header+signature wall — half the
volume, and the uniform wall replaced by compact digests, so there is far less for the model to
collapse into a churning aggregate. (Limitation, stated honestly: pure-helper chunks remain similar
*to each other* in kind — inherent to a codebase of many similar helper modules — but the
constant-bearing slices, where the test lives, are now distinct, and the aggregation-driving volume
is gone.)

## The decisive pre-run gate — table survival under a NEUTRAL prompt (warm, battery conditions)

Run `coupled_full`'s Phase-A passes with accumulated state under the **unchanged broad rubric**, and
per-pass-track whether the `23: 988` mapping is present. The falsifiable test of the
representation-failure hypothesis:

- **survives past pass 2** → the churn was a representation artifact, fixed at the compressor (the
  legitimate layer), with the model's cognition un-scripted → the **first real viability signal**
  (record AND retain fired together).
- **still clobbered** → the churn is intrinsic floor state-management → rides on the trained student
  E2′. Honest, non-circular.

GATE 1 (backfill, 0/4) and GATE 3 (compose ceiling, 4/4) from the prior run still hold (the
compressor change doesn't affect them).

### SURVIVAL RESULT (frozen design; temp-0 + 2× temp-0.7, coupled Phase-A 6 passes) — table did NOT survive

Across all 3 draws the `23: 988` mapping **never entered the state** (`q_map=False`, `kv=0`, every
pass) — and neither did the control table. But the **mechanism of failure changed**, and that change
is the finding:

- **No destructive churn was OBSERVED — but this is CONFOUNDED, not "v2 fixed it."** Under v2's
  heterogeneous views the model appends clean, distinct per-module entries (temp-0: S1–S27, *"The X
  module (group N) contains helpers for a, b, c"*), state grows steadily (433→911 tok), with **no
  `MODULES`/`FUNCTIONS` aggregate re-compression / clobbering.** **HOWEVER, two things changed at once
  (the compressor AND the prompt revert), so churn-absence cannot be attributed to v2:** the old
  churn was the model maintaining a *detailed* aggregate and clobbering; under the neutral prompt it
  writes high-level summaries and builds no detailed aggregate, so there is **nothing to clobber**
  regardless of the compressor. Churn-absence is equally consistent with "the neutral prompt elicits
  summaries." The representation-failure hypothesis is **plausible but NOT isolated by this run.**
- **The table is never recorded — a clean SALIENCE result (stronger than "abstraction").** The
  neutral rubric explicitly asks to *"integrate precise specifics — exact values, names, definitions"* —
  and the floor **does** record plenty of specifics (every module's helper names) yet **omits the one
  high-information structure, the constant/lookup table.** Told to record exact values, it records
  low-information names and drops the high-information table. That is the **P4/P5/P6 salience /
  what-to-record floor**, isolated cleanly in the code domain (not mere abstraction — selective
  mis-prioritization).

**Pre-registered outcome reached: intrinsic-floor → E2′** (refined: the intrinsic limit is
*salience/recording*, not the churn — the churn was a representation artifact and is fixed). The
table did **not** survive, so there is **no forcing/circularity** concern (probe-blind compressor +
neutral prompt → clean negative).

### What this means for viability (the honest chain)

Every step of the architecture's chain now works or is fixed **except one**, and that one is the
canonical trainable gap:

| step | status on the unaided 7B |
|---|---|
| coarse pass **carries** the table skeleton into the view | ✓ (C1 guard; the table is in the realized Phase-A view) |
| **record** it into state (salience: judge the arbitrary table brief-worthy) | **✗ — DEMONSTRATED.** asked for "exact values," the floor records helper names and omits the table **(the trainable gap → E2′)** |
| **retain** it through the sweep | **— NOT TESTED** (table never entered state). Isolation control: no destructive churn under a neutral prompt with *either* compressor → the earlier churn was **prompt-driven** (specifics-demanding aggregates), not a representation failure and not fixed by v2 |
| **compose** the answer from state | ✓ (GATE 3, 4/4) |
| one fragment alone can't win | ✓ (GATE 1, 0/4) |

So the unaided generic 7B fails — demonstrably — at the **salience/record** step, the same bottleneck
P4/P5/P6 identified. Retention is **not** shown solved (it was never exercised); claiming "v2 fixed
the churn" would over-state the run. The honest read: "the architecture is sound at carry/compose;
the unaided floor lacks the what-to-record policy (salience) — what training supplies" → **E2′**.

### ISOLATION CONTROL — v1 compressor + neutral prompt (run on maintainer's request) → the churn was the PROMPT, not the views

Ran the missing cell (coupled Phase-A, **old homogeneous v1 scaffold + the neutral prompt**, temp-0 +
2 seeds; `control_v1_neutral.log`). Result:

- **Table still never recorded** (q_map=0, ctrl=0, all 3 draws) — identical to v2+neutral. Salience
  failure is **robust across both compressors** (now 6/6 neutral-prompt draws).
- **No destructive churn under v1+neutral either** — temp-0 grew monotonically (46→1491 tok, no
  shrink/clobber); the sampled seeds stayed flat with only minor dips. This is **unlike** the earlier
  v1 + *non-neutral* runs (state shrank 382→141; the S3 table→functions clobber).

**What the control identifies (and what it does NOT).** The 2×2:

| | neutral prompt | specifics-demanding prompt |
|---|---|---|
| **v1 views** | no churn (this control) | **churn** (attempts 1, 3) |
| **v2 views** | no churn (survival test) | **NOT RUN** (forcing-blocked, Line 3) |

Holding compressor = v1 and toggling the prompt flips churn on/off → **the prompt is *sufficient* to
cause (and to remove) the churn.** That is all the control earns. It does **not** show the views are
irrelevant: the disambiguating cell (v2 + specifics) is the forcing-blocked bottom-right, so the
views' *independent* contribution under recording conditions is **unidentified, not disproven.**

So, precisely:
1. **The prompt is sufficient** for the churn; the maintainer's churn diagnosis was **real** — the
   control just relocates the *demonstrated* cause to the prompt and **leaves the views' role open.**
   (Not "homogeneous views don't matter" — that would overreach in the opposite direction of the
   earlier "v2 fixed it.")
2. v2 earns **no retention/churn credit from this run** (nothing to fix under neutral conditions) but
   remains a legitimate, principled architecture improvement (heterogeneous, probe-blind, ½ volume).
3. **Caveat (n≈1):** "no churn under neutral" rests mostly on the temp-0 draw, which accumulated state
   (→1491 tok); the two sampled seeds essentially **idled** (~150 tok), and you cannot observe
   destructive churn in a state that never accumulated. So the "recorded substantially AND didn't
   churn" evidence is thin.

**Consequence for E2′ — the churn risk is REAL, not mere insurance.** A trained student records
substantial content — i.e. it operates in the **specifics/recording regime, where churn WAS observed
(v1+specifics) and v2 is untested.** So E2′ should **keep BOTH** mitigations — the heterogeneous v2
compressor **and** clobber-safe / content-addressed edit ops — rather than bet against either. The
retain step stays **not tested** here (table never recorded under either compressor).

**Deliberately NOT run (the forcing line):** v2 compressor **+** a specifics-demanding ("record table
contents") prompt — that scripts the model's cognition (Line 3) and makes any end-to-end success
circular. GATE 2 (cold) already showed the floor *can* record the table **when the prompt asks for
the table specifically**; P7's fair setup shows the *unaided* floor under a neutral task does not.
That gap is E2′'s to close, not the prompt's.
