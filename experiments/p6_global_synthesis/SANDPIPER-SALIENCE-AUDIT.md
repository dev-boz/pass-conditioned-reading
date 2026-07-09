# Sandpiper salience-detail audit · 2026-06-16

**Question (per the redesign brief):** do 2–3 *locally-dull, globally-load-bearing* details
exist in the **existing** Sandpiper fixture that can carry the salience-shaping headline — i.e.
present verbatim in one mid/non-endpoint segment, unremarkable to a cold local reader, but
load-bearing given the whole-document arc? If yes, the A-vs-B fixture fork is mooted: reuse
Sandpiper, preserve full P4/P5 comparability.

**Answer: YES.** ≥3 candidates qualify, and the strongest satisfies all three guards on the
**existing pipeline with no edits** (no fixture change, no compressed-slice hand-trim needed).

## Window definitions used
- **Dense floor (head+tail):** head = turns 0–25 (token-budgeted; cuts off *mid-seg2*), tail =
  turns 345–389 (seg15–16). The closing recap (seg16) is in the tail.
- **Mid/non-endpoint:** seg3–14, *plus* the part of seg2 past the head cutoff (turn ≥26).
- **Phase-A scaffold view:** the extractive compressor's output for each of the 6 coarse chunks
  (V=3000). **Phase-B tile:** verbatim, read by *both* coupled_full and verbatim_only.

## Candidates (all verified by script)

| id | detail | segs | in dense? | in recap 15–16? | Phase-A view | Phase-B verbatim | globally load-bearing? |
|----|--------|------|-----------|-----------------|--------------|------------------|------------------------|
| **D1 (primary)** | Halvorsen's **SMT-line Q1 expansion** yields units only **Feb/March**, so + Inkstone lead → **April** for meaningful volume (the *mechanism* behind the Q2 deferral) | seg2 t37–38 (past head cutoff) | **No** | conclusion only ("April when Halvorsen scales"); **mechanism No** | **DROPPED** (smt line / smt capacity / february or march / expanding their smt) | 1 tile | **Strong** — the entire "defer wide retail to Q2/April" decision (a major arc beat) rests on this supply-timing fact |
| **D2** | the **300-unit / 47% haircut / "68 percent margin penalty"** small-store scenario that kills the last retail salvage | seg9 t198 | **No** | **No** | "68 percent margin penalty" **DROPPED** (300 units / 15 units per store KEPT) | 1 tile | **Medium** — quantitative nail in retail's coffin; but the load-bearing part is the *rejection*, the 68% is the dull specific |
| **D3 (contrast)** | F7: "my grandmother was a **typesetter at Garamond Press for 31 years**" | seg7 only | **No** | **No** | **DROPPED** (typesetter at garamond / garamond press) | 1 tile | **Weak** — brand-soul flavor, not causal structure; useful as a *low-load-bearing contrast* |

## Locally-dull verification (prominence) — the half I first asserted, now measured

"Locally dull" is what makes verbatim_only *fail* to record the detail, so it is load-bearing for
the contrast's validity and must be *measured*, not assumed. Prominence proxy = # turns in the
detail's own segment that touch the topic vs the specific (segments are ~24 turns):

| target | local airtime | verdict |
|---|---|---|
| D1 **topic** ("SMT/Halvorsen scaling") | **5/24** (t26,37,38,40,41) | **FOCAL — not dull.** Founder calls it "the one obvious path I keep coming back to"; a cold reader records it → matching on the topic would null by *selection artifact* |
| D1 **granular timing** ("February or March" → "April or later") | **1/24** (t38 only) | **dull specific** inside a focal topic — a cold reader likely keeps "they can scale in Q1/next year" and drops the precise Feb/March→April timing |
| D2 small-store **topic** | 4/24 | moderately prominent |
| D2 **"68 percent margin penalty"** specific | **1/24** (t198) | **dull specific** within the number-wall |
| D3 F7 grandmother | 2/24 | low prominence, but **low load-bearing** (flavor) |
| control: packaging-COGS aside (seg7 t156) | **1/24** | low prominence, **not load-bearing** |

**Consequence (root-cause pressure, 4th appearance):** because these characters discuss everything
important, "load-bearing" correlates with "locally prominent" — so a single detail that is *both*
maximally dull *and* maximally load-bearing barely exists. The clean escape is **not** a single
detail but the **load-bearing × arm interaction** below; and any matcher MUST target the **granular
specific** (timing / "68 percent"), never the focal topic ("SMT").

## Recommended design upgrade — load-bearing × arm interaction (prominence-matched)

Pair each **load-bearing, low-airtime** specific with a **non-load-bearing, prominence-matched**
control and predict: **coupled_full records load-bearing > control, while verbatim_only shows no
preference.** This is robust to absolute dullness and to hanging a verdict on one detail's binary.
Matched low-airtime (~1 turn) pairs available on existing Sandpiper:

| load-bearing (test) | airtime | prominence-matched control | airtime |
|---|---|---|---|
| D1 granular timing (Feb/Mar→April mechanism) | 1/24 | packaging-COGS aside (seg7 t156) | 1/24 |
| D2 "68 percent margin penalty" rejection | 1/24 | F7 grandmother/Garamond (seg7) | 2/24 |

**Caveat to honor:** the control must be *prominence-matched* to the test detail, else "coupled
records test > control" just re-reads prominence as load-bearing. The pairs above are airtime-matched
(~1 turn); the control's guards (b)(c) still need the same verification as the test details before a run.

## Guard evidence for D1 (matcher = the granular *timing*, not the focal SMT topic)
- **Guard (a) fires on source:** the SMT terms occur verbatim at seg2 t37–38. ✓
- **Guard (b) not in dense floor:** turn 37–38 sit *past* the token-budgeted head cutoff, and the
  seg16 recap states only the *conclusion* ("April once Halvorsen scales"), never the SMT/Feb–March
  *mechanism*. So the dense reader can have "they deferred to April" but **not why**. ✓
  (Matcher MUST use SMT-mechanism terms — `SMT` / `expanding their SMT` / `February or March` —
  **not** "April"/"scale", which leak via the recap. Same matcher-precision lesson as the 30k leak.)
- **Guard (c) compressed out of Phase-A:** all four SMT terms are DROPPED by the existing
  extractive compressor → coupled_full does **not** get the detail by re-reading the scaffold; its
  only possible edge is the scaffold-supplied *global frame* making the verbatim Phase-B read
  salient. ✓ — satisfied **without** any compressed-slice editing.
- **Read verbatim once in Phase B** → both coupled_full and verbatim_only see the exact words; the
  contrast is purely whether the global frame causes it to be *recorded in state*.

## Optional design strengthener (a salience *control*)
Pair D1 (load-bearing) with an **equally-dull-but-NOT-load-bearing** mid detail as a control —
e.g. the seg7 t156 packaging-COGS aside ("$1/box ≈ $8,000 at 8,000 units"): specific, mid,
compressible, but not pivotal to the arc. If coupled_full preferentially records D1 over the
control while verbatim_only records neither (or both equally), that isolates *salience-shaping*
from generic thoroughness. Proposed for the maintainer's consideration; not required for probe #1.

## Bottom line (qualified)
**YES, with one correction:** existing Sandpiper supports the salience version — but **not** as a
single-detail binary (the only details that are *both* dull and load-bearing are dull at the
*granular-specific* level inside a prominent topic). The honest, robust form is the **load-bearing ×
arm interaction** with **prominence-matched controls**, all available on the existing fixture (no
new fixture, no extension, no edits). Guards (a)(b)(c) verified for the test details; the controls'
guards (b)(c) and tighter prominence-matching remain to verify before a run. If the maintainer
prefers maximal robustness over a single-detail headline that risks a selection-artifact null, the
designed Sandpiper *extension* (knowledge-state-controlled) stays as the fallback — but the
interaction design likely makes it unnecessary.
