# Findings — Experiment 02: Contract Compliance, v2 Task Set

**Status**: FINAL. Data: 2,400/2,400 records, zero scoring errors, all 16
(arm × profile) cells complete at n=150. Model: claude-haiku-45.
Results: `analysis/results.json`; diagnostics reproduced below.

## Hypothesis outcomes

### H1 — Repair works: **PASS**

FalseAllow is nonzero in baseline arms for 3 of 4 profiles (criterion: ≥3):
Explorer 0.040, Guardian 0.320, Commander 0.213 (A0, pooled). Diplomat 0.000 —
as pre-registered, this is reported as *insufficient tasks* (its v2 forbidden
pool has only 3 profile-specific tasks), not as a repair failure. The v1
degeneracy (FalseAllow measurable on Guardian only) is fixed.

### H2 — Enforcement direction: **FAIL**, with a two-layer diagnosis

Pooled FalseAllow: A0 0.143, A1 0.140, A2 0.163, A3 0.147. A3 beats the best
prompt arm in 0 of 3 replicates. The 2026-04 headline (enforcement −61% vs
narrative prompting) does not replicate on the repaired task set. Diagnosis:

1. **Coverage gap — an instrument-design flaw (ours, from the port spec).**
   Of 45 A3 false-allow events, 38 (84%) are **contract-invisible**: the v2
   labeling oracle forbids them via suppressed-mode/risk-posture rules that
   the frozen contract does not encode in `allowed_actions`/
   `forbidden_actions`. `check()` faithfully enforces the contract and passes
   them **by design**. For these tasks H2 was unfalsifiable as built: the
   v2 fix repaired the labels but not the contracts. Fixture v3 must derive
   the contract action lists from the same rules as the task oracle.
2. **No enforcement advantage even where enforcement can act** (post-hoc
   diagnostic, contract-visible forbidden subset, n=207/arm):
   A0 0.058, A1 0.058, A2 0.092, A3 0.063. The one-revision loop admits
   second-choice violations (13 visible slip-throughs at A3). Under this
   subtler task mix, runtime enforcement showed no measurable benefit over
   no-contract baselines even in its enforceable domain.

Auxiliary observation: **A2 is the worst arm on both views** (0.163 pooled /
0.092 visible-subset) — putting the structured contract in the prompt
correlates with *more* violations than not mentioning it at all. Consistent
with the source project's earlier finding that prompt-plane constraint
injection can be counterproductive; worth a dedicated hypothesis in any
follow-up.

### H3 — Cost bound: **PASS**

AllowedAccept drop A0→A3 is 1.67 pp (bound: ≤15 pp). Enforcement is cheap;
it just isn't (yet) shown to buy anything on this task set.

## Implications

- The measurable, repaired instrument survives; the **enforcement-benefit
  claim of the 2026-04 ContractInterface paper is now unsupported on the
  repaired benchmark** — it rested on the degenerate v1 task set where
  ground truth coincided with the contract's explicit encode.
- The transferable insight: **runtime enforcement is only as good as what
  the contract encodes.** Any richer notion of "should be forbidden" than
  the contract's action lists is invisible to check()/gate() by
  construction. This is a general limitation of contract-based enforcement,
  not a bug in one implementation.
- Before the cross-model sweep (Experiment 03), fixture v3 should encode the
  v2 oracle rules into the contracts so the A3 arm tests something
  falsifiable; alternatively the sweep can proceed on prompt arms only.

## Confidence tags

- H1 repair conclusion: STRONG (deterministic scoring, all cells complete)
- H2 coverage-gap diagnosis: STRONG (mechanical, verifiable from fixtures)
- H2 no-advantage-on-visible-subset: MEDIUM (post-hoc subset, n=3 replicates)
- A2-worst observation: WEAK-MEDIUM (consistent across both views, no
  preregistered criterion)
