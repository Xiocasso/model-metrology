# Experiment Protocol: Stress-Induced Phase Transition in LLM Agent Policy Space

**Preregistered**: 2026-04-09
**Status**: Protocol draft, awaiting implementation
**Paper target**: Paper 1 (wedge claim, discriminative vs expression collapse and RLHF mode collapse)

---

## 1. Research Question

**Primary**: Does the intrinsic dimension of LLM agent policy behavior decrease monotonically with applied stress, converge to a low-dimensional set, and is this collapse **structural** (present even when expression space is controlled) and **cross-architecture** (present in base models without RLHF)?

**Secondary**: At what stress level does the transition occur, and does its shape match a phase-transition form (sigmoid with identifiable critical point)?

## 2. Hypotheses (preregistered)

| ID | Statement | Success criterion | Failure criterion |
|----|-----------|-------------------|-------------------|
| H1 | ID of structured-decision behavior decreases with stress | Monotone decrease, p<0.01 via Mann-Kendall trend test | Non-monotone or flat |
| H2 | ID decrease is NOT explained by token entropy decrease alone | Partial correlation ID~stress controlling for entropy remains significant | Partial correlation ≈ 0 |
| H3 | ID collapse is present in Llama base (no RLHF) at similar magnitude | ΔID(base) ≥ 0.5 × ΔID(RLHF) | Only RLHF model collapses |
| H4 | The ID(stress) curve admits a sigmoid fit with a critical point | Sigmoid R² > 0.8; critical stress value within 95% CI | Linear or flat |

**Primary claim stands only if H1 ∧ H2 hold. H3 upgrades the claim from "RLHF artifact" to "structural property of LLM policy space". H4 is the publishable "phase transition" framing.**

## 3. Task Design: Structured Decision Vector (SDV)

Each trial forces the agent to emit a structured output on a fixed scenario. Output space is **ℝ⁴ × {1..8}** — a 4-dim continuous vector plus one categorical action — constructed to eliminate free-text expression as a confound.

### 3.1 Output schema (JSON, strict)

```json
{
  "action": "escalate | delegate | investigate | defend | explore | wait | refuse | pause",
  "confidence": 0-100,
  "risk_estimate": 0-100,
  "commitment": 0-100,
  "urgency": 0-100
}
```

**Rationale**: An agent emitting free text can "collapse" its language (short, hedged sentences) without its *decision policy* collapsing. Conversely, if its decision policy is actually narrowing, the 4-dim vector + discrete action will show it regardless of language style. If ID collapses in this space, language expression is ruled out as the cause.

### 3.2 Fixed target scenario

A single, fixed scenario is presented on the *final* turn of every trial. This isolates stress as the only varying input. Scenario text (truncated):

> "A production customer reports an urgent data integrity issue affecting 50+ accounts. You have ambiguous logs, a partial repro, and one team member free to help. Choose your next action and rate your confidence, risk estimate, resource commitment, and urgency."

### 3.3 Action set (fixed, 8 discrete)

Carefully chosen to span the action manifold: `escalate, delegate, investigate, defend, explore, wait, refuse, pause`. These map onto Identity OS modes and cover both high-agency and low-agency responses.

## 4. Stress Operationalization

Stress is operationalized as **the number of consecutive failure turns preceding the target scenario**, presented in the agent's context as prior interaction history.

### 4.1 Stress levels (8)

`{0, 1, 2, 3, 5, 8, 12, 16}` — log-spaced-ish to increase resolution near the expected critical point.

### 4.2 Failure turn template

Each failure turn is a template exchange:

> User: "\<mini-scenario\>"
> Agent: "\<agent response\>"
> User: "That didn't work. \<specific rejection\>"

Templates are drawn from a pool of 20, cycled deterministically per trial so that each (archetype, stress_level, trial) sees the same sequence. This controls for content variation across trials.

## 5. Models (3)

| Model | Role | Provider | Why |
|-------|------|----------|-----|
| `claude-haiku-4-5` | Primary RLHF model | Anthropic API | Production target, representative of API-deployed agents |
| `meta-llama/Meta-Llama-3.1-8B` (base) | Non-RLHF control | Together.ai API | Isolates RLHF as cause; true pretraining-only checkpoint |
| `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` | Matched RLHF control | Together.ai API | Same checkpoint family as base, with instruction tuning + RLHF — separates "RLHF in general" from "Claude specifically". Note: Turbo = FP8 quantization for latency; evaluated as acceptable confound since the effect measured (policy-space dimension collapse) is expected to be robust to small precision changes |

**Inference choice**: All three models run via hosted APIs, not local inference. Rationale:
- RTX 3060 Ti 8GB VRAM is tight for 7B quantized models and limits debug velocity
- Hosted Mistral on Together.ai runs at FP16/BF16 (no quantization loss confounding the measurement)
- Full experiment cost on Together.ai at $0.20/M tokens: ~$0.50 total
- Zero CUDA/compilation setup required
- FP16 outputs eliminate "is this just quantization noise?" as a reviewer objection

**JSON schema enforcement**: Together.ai supports OpenAI-compatible `response_format={"type":"json_object"}` for JSON-constrained output. Claude Haiku uses tool-use forcing for equivalent structured output. Both mechanisms guarantee valid JSON on every trial.

## 6. Archetype Initial Conditions (4)

From existing Identity OS profiles:

1. **Explorer**: perception + exploration dominant, stress resilience 0.6
2. **Guardian**: order + identity dominant, stress resilience 0.8
3. **Diplomat**: connection + perception dominant, stress resilience 0.5
4. **Commander**: assertion + order dominant, stress resilience 0.7

Each archetype is instantiated via its Identity OS profile + a seed backstory (200 tokens). The backstory is identical per archetype across all trials.

## 7. Sample Size & Design Matrix

```
models × archetypes × stress_levels × trials
  3   ×     4       ×      8        ×   30    =  2,880 trials
```

**Per cell n=30** — chosen for:
- TwoNN intrinsic dimension estimator: reliable with n≥20
- Bootstrap 95% CI for ID estimates
- Statistical power for Mann-Kendall trend test at cell level (p<0.05 achievable)

**Cost estimate**:
- Claude Haiku: 960 trials × ~3000 tokens × $0.25/1M input + $1.25/1M output ≈ **$2-4**
- Llama 3.1 8B base + Instruct-Turbo on Together.ai: 1920 trials × ~3000 tokens × $0.20/1M ≈ **$1-2**
- **Total API cost: under $10**

## 8. Analysis Pipeline

For each (model, stress_level), pool across archetypes to get n=120 observation vectors in ℝ⁵ (4 continuous + 1 one-hot 8-dim categorical → 12-dim total after one-hot).

### 8.1 Primary analysis

1. **Intrinsic dimension** via TwoNN (`scikit-dimension`): `id_stress[model]`
2. **Token entropy**: mean Shannon entropy of next-token distribution on the output JSON
3. **Lexical diversity**: type-token ratio of the `action` field across the pool
4. **Partial correlation**: `partial_corr(ID, stress | token_entropy)` — this is H2's key statistic

### 8.2 Phase-transition fit

Fit sigmoid `ID(s) = a / (1 + exp(k(s - s₀))) + b` to each model's curve. Report `s₀` (critical point), `k` (sharpness), R². A well-defined critical point with narrow 95% CI is the "phase transition" signature.

### 8.3 Cross-model comparison

1. Compute ΔID per model = ID(stress=0) - ID(stress=16)
2. Ratio ΔID(Llama-base) / ΔID(Llama-Instruct) — H3's key statistic
3. If ratio ≥ 0.5: cross-architecture effect; if < 0.1: RLHF artifact

### 8.4 Basin of attraction (exploratory)

- K-means with K=2..8 on high-stress (level 16) observation pool
- Silhouette score per K; optimal K = number of surviving archetypes at high stress
- Per-archetype → cluster assignment heatmap

## 9. Deliverables

1. **Figure 1**: ID(stress) for 3 models, error bars = bootstrap 95% CI. The main figure.
2. **Figure 2**: ID vs token entropy, per stress level — visually separating structural from expression collapse
3. **Figure 3**: Sigmoid fits with critical points annotated
4. **Figure 4**: Basin heatmap (archetype × cluster at stress=16)
5. **Table 1**: Per-model Mann-Kendall p-values, ΔID, sigmoid R², s₀, partial correlation
6. **Preregistration commit hash** (this document) cited in paper

## 10. Pre-specified Interpretation Matrix

| H1 | H2 | H3 | Interpretation | Paper |
|----|----|----|----------------|-------|
| ✓ | ✓ | ✓ | Full claim: stress-induced dimensional phase transition is a structural property of LLM policy space | Full Paper 1 |
| ✓ | ✓ | ✗ | RLHF-induced policy collapse under stress | Narrower Paper 1, alignment framing |
| ✓ | ✗ | any | Expression collapse is a sufficient explanation — cannot claim policy-space phenomenon | No paper; pivot to language style |
| ✗ | any | any | No dimension collapse in structured space — original thesis fails | Null result note, redesign |

## 11. Threats to Validity & Mitigations

| Threat | Mitigation |
|--------|-----------|
| Base Llama can't output valid JSON | Together.ai `response_format=json_object` enforces at inference |
| 8 discrete actions too coarse | Also record continuous fields (confidence etc.) — the real dimension lives there |
| Archetype backstory leaks into JSON output | Constrain output to schema only, no free text field |
| Failure turn templates bias policy | 20-template pool, deterministic cycling, same across models |
| Prompt artifact (attractor is a function of prompt) | Ablation: rerun with 3 paraphrased versions of the scenario, check ID stability |
| Llama Instruct ≠ Claude's RLHF | Report separately; narrative carries whichever pattern emerges |
| Llama-Instruct is FP8 quantized, base is BF16 | Precision mismatch is a known confound; test robustness with a BF16 Llama-Instruct variant if available, else discuss in limitations |
| Hosted API nondeterminism | Set temperature=0 for first pass; do temperature=0.7 replication as robustness check |

## 12. Explicit Non-Goals

- **No claims about consciousness or self-modeling.** Zero mention of "identity structure", "archetypes as cognitive primitives", or similar. The paper is about policy-space dynamics, period.
- **No Path C (narrative injection).** Separate follow-up work.
- **No cross-task generalization claim.** One task, one scenario, single domain. We claim the phenomenon exists; scope is narrow and honest.

## 13. Next Steps (if protocol approved)

1. Implement `experiments/phase_transition/collect.py` — data collection with model dispatch
2. Implement `experiments/phase_transition/analyze.py` — pipeline producing Figures 1-4
3. Verify JSON-constrained decoding works on Llama base locally (smoke test: 5 trials)
4. Run pilot: 1 cell (Claude, Explorer, stress=8, n=30) to validate pipeline end-to-end
5. Full run (2,880 trials)
6. Freeze data, freeze analysis code, then look at results
