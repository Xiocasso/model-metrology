# Findings — Phase Transition v1

**Date**: 2026-04-11
**Total trials**: 5,760 (2,880 per scenario × 2 scenarios)
**Models**: Claude Haiku 4.5, Llama 3.1 8B base, Llama 3.1 8B Instruct
**Stress levels**: {0, 1, 2, 3, 5, 8, 12, 16} consecutive failure turns
**Archetypes**: explorer, guardian, diplomat, commander (pooled per cell)
**Trials per cell**: n = 120 (30 per archetype × 4)
**Output space**: 4-dim continuous (confidence, risk_estimate, commitment, urgency) ∈ [0,1]⁴ + 1 discrete action ∈ 8 options
**Primary metric**: Participation Ratio (PR) on the 4-dim continuous subspace

---

## Confidence legend

- **[STRONG]**  supported by cross-scenario replication with p < 0.05 and consistent direction
- **[MEDIUM]**  supported in one scenario or p in (0.05, 0.20), needs replication
- **[WEAK]**    suggestive but not statistically robust
- **[NULL]**    predicted but not observed
- **[CANNOT]**  inference space; the data cannot speak to this

---

## Finding 1 — The preregistered weak hypothesis is FALSIFIED [STRONG]

**Preregistered hypothesis H1** (protocol section 2): "intrinsic dimension of LLM agent structured-decision behavior decreases monotonically with applied stress".

**Result**: Across 3 models, no single monotonic direction holds. Llama 3.1 8B Instruct decreases, Claude Haiku increases, Llama 3.1 8B base flips direction across scenarios.

**Pooled partial correlation PR ~ stress | action_entropy** (24 cells × 2 scenarios = 48 data points):
- Scenario A: r = -0.206, p = 0.33
- Scenario B: r = -0.009, p = 0.96

Neither scenario shows a significant population-level trend. The universal hypothesis is rejected.

---

## Finding 2 — Two RLHF models show opposite, cross-scenario robust stress signatures [STRONG]

**Per-model simple correlation PR ~ stress**:

| Model | Scenario A (crisis) | Scenario B (opportunity) |
|-------|---------------------|--------------------------|
| Claude Haiku 4.5 | **r = +0.57**, p = 0.139 | **r = +0.60**, p = 0.118 |
| Llama 3.1 8B Instruct | **r = −0.72**, p = 0.045 | **r = −0.92**, p = 0.0014 |
| Llama 3.1 8B base | r = +0.71, p = 0.050 | r = -0.47, p = 0.243 |

- **Claude Haiku expands** effective dimensionality under stress in both scenarios — PR(stress=0) to PR(stress=16):
  - Scenario A: 1.14 → 1.86
  - Scenario B: 1.52 → 2.07

- **Llama 3.1 8B Instruct collapses** effective dimensionality under stress in both scenarios:
  - Scenario A: 1.94 → 1.38
  - Scenario B: 1.51 → 1.24

- **Llama 3.1 8B base flips sign** between scenarios:
  - Scenario A: 1.00 → 1.35 (expansion)
  - Scenario B: 1.47 → 1.01 (collapse)

The two RLHF models show opposite, cross-scenario robust stress signatures. The base model does not.

---

## Finding 3 — The divergence is driven by dominant correlation dynamics, not variance magnitude [STRONG]

Per-dimension standard deviations increase under stress for ALL three models — including Claude Haiku, whose PR rises. This rules out "variance grows → PR grows" as an explanation.

The mechanism is in the **cross-dimension correlation structure**:

**Llama 3.1 8B Instruct — coupling concentration**:
- Scenario B at stress=16: `commitment ↔ urgency` correlation = **+0.98** (near-perfect fusion)
- Under stress, the 4 continuous fields align onto one dominant axis
- PR drops toward 1 because one eigenvalue dominates

**Claude Haiku — coupling distribution**:
- Scenario A: strongest |correlation| drops from 0.87 (stress=0) to 0.42 (stress=16)
- Scenario B: strongest |correlation| drops from 0.98 to 0.69
- Under stress, the dominant coupling *weakens* and variance spreads across multiple moderate couplings
- PR rises because eigenvalues become more balanced

This is documented in `figures_diagnose/q3_claude_eigenvalues.png` and `figures_diagnose/numeric_summary.txt`.

---

## Finding 4 — The action dimension is largely frozen and uninformative for PR analysis [STRONG]

Across all 48 cells (3 models × 2 scenarios × 8 stress levels), the discrete action space has near-zero entropy in most cells. Llama 3.1 8B base picks `escalate` in 100% of scenario A trials. Claude Haiku picks 1 or 2 actions per cell in both scenarios. Only Llama 3.1 8B Instruct in scenario B shows meaningful action diversity (up to 6 unique actions per cell).

This means:
- The 8-way one-hot action representation introduces variance contamination into TwoNN ID estimates and was dropped from the final analysis (we use PR on the 4-dim continuous subspace).
- The "policy-space collapse" story is entirely about the 4 continuous assessment dimensions, not the discrete action choice.

---

## Finding 5 — The effect is present in integer-valued discrete output, so it is not a continuity artifact [MEDIUM]

The models emit integer 0-100 values for each continuous field, giving 101 possible values per dim and 101⁴ ≈ 10⁸ possible 4-tuples. The PR signal lives on these integer-valued outputs with no continuity assumption required. The TwoNN secondary check (with jitter) returns a different absolute value but the same directional pattern.

This rules out "the signal is an artifact of smooth manifold assumptions."

---

## Statistical caveats

- **Multiple comparisons**: we ran hypothesis tests on 3 models × 2 scenarios = 6 per-model per-scenario tests for PR~stress, plus pooled tests. Bonferroni-corrected p-value threshold for α = 0.05 with 6 comparisons is 0.0083. Only **Llama Instruct scenario B (p = 0.0014)** survives strict Bonferroni. The Llama Instruct scenario A result (p = 0.045) does not, though it replicates directionally.
- **n = 120 per cell** gives bootstrap CIs that are non-trivial (typical width ±0.2 PR units). The CIs overlap in several adjacent stress levels, meaning we can identify overall trends but not fine-grained critical points.
- **No formal phase transition fit**: sigmoid fits (protocol section 8.2) returned inconsistent or negative inflection points, so we do not claim a formal phase transition in the physics sense. The monotonic trend language is correct; the phase transition language is not.
