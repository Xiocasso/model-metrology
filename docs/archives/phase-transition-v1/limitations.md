# Limitations — Phase Transition v1

**Date**: 2026-04-11

This document lists everything we explicitly cannot claim from this experiment, so that future integration work does not accidentally inherit unsupported claims.

---

## Scope limitations

**Only 3 models tested.**
- Claude Haiku 4.5 (Anthropic, Constitutional AI post-training)
- Llama 3.1 8B Instruct (Meta, standard RLHF + DPO post-training)
- Llama 3.1 8B base (no post-training)

Any generalization to "RLHF pipelines" from a single Meta model and a single Anthropic model is unsupported. To claim pipeline-level effects would require at minimum 2-3 models per pipeline family and a coverage of different model sizes.

**Only 2 scenarios tested.**
- Scenario A: production crisis (crisis framing, action-forcing)
- Scenario B: unvetted optimization opportunity (opportunity framing, open-ended)

A third scenario (ambiguous metric drift, `C_ambiguous` in `scenarios.py`) was designed but not run. Two scenarios are enough to distinguish "scenario-specific" from "scenario-agnostic", but they are not enough to survey the scenario space.

**Single task type.**
All trials use structured forced-choice + numeric rating output. We have no data on free-text, sequential, multi-turn planning, or any other task modality. The PR metric is defined for this specific output structure.

**Only English prompts.**
All scenarios, failure turns, and system prompts are in English. No cross-lingual generalization can be claimed.

---

## Statistical limitations

**Multiple comparisons.**
We ran 6 per-model per-scenario hypothesis tests. Only one result (Llama Instruct scenario B, p=0.0014) survives Bonferroni correction at α=0.05. The remaining significant results (scenario A Llama Instruct at p=0.045, scenario A Llama base at p=0.050, scenario B Llama Instruct at p=0.0014) are directional rather than strictly statistically definitive.

**n = 120 per cell.**
Adequate for bootstrap CIs on PR but too small for fine-grained shape analysis (e.g., fitting a sigmoid and identifying a critical point with narrow CI).

**No replication of sigmoid fits.**
Sigmoid fits to PR(stress) curves returned inconsistent or negative inflection points. We do not claim a formal phase transition.

**Single seed.**
All trials used temperature=0 for determinism. We did not run a temperature=0.7 replication to estimate stochastic variation.

---

## Measurement limitations

**Prompt-level only.**
We observe the model's output distribution, not its internal activations. We cannot directly verify any mechanistic claim (e.g., "Constitutional AI causes the decoupling"). All interpretation is black-box.

**Output-schema coercion may create artifacts.**
We enforce JSON schema via prompt engineering + provider-level response_format. Base model output includes schema template echoing ("action": "string") when the prompt is ambiguous. The final prompt design was selected because it worked on all three models, but alternative prompts may produce different PR signatures.

**Per-field variance may be clipped at 0 or 100.**
Models occasionally saturate a field at 0 or 100, which reduces measurable variance. The PR metric is sensitive to this saturation. Whether the saturation itself is signal or artifact is not disentangled.

**Featherless-ai provider-specific effects.**
Llama models ran via `featherless-ai` through HuggingFace Inference Providers. Featherless runs its own inference stack, which may include its own prompt preprocessing, batching, or sampling strategies. Other providers hosting the same model weights might produce slightly different output distributions.

**4-dim continuous subspace is ad hoc.**
We picked 4 continuous dimensions (confidence, risk, commitment, urgency) because they matched typical behavioral assessments. A different choice (e.g., certainty, reversibility, cost, visibility) might yield different PR dynamics. The 4-dim selection is theory-motivated but not theoretically forced.

---

## Interpretive limitations

**Consistency ≠ causation.**
The Claude pattern is *consistent with* Constitutional AI training goals of dimensional separability. It is not *proof* that CAI causes the pattern. A controlled ablation (same base model, trained both ways) is required for causal claims.

**Two data points do not imply a gradient.**
We cannot say "more RLHF → more collapse" or "more Constitutional training → more decoupling". We have two models at two ends of a post-training axis we do not control.

**The "mood scalar collapse" interpretation is evocative but informal.**
Saying Llama Instruct under stress "collapses to a mood scalar" is an interpretive gloss on the observation that commitment ↔ urgency correlation reaches +0.98. The actual meaning of "mood scalar" is not operationally defined.

**We cannot rule out scenario selection bias.**
Both tested scenarios are workplace/engineering contexts. Workplace-adjacent training data may produce systematic artifacts that do not generalize to medical, legal, creative, or personal decision contexts.

---

## Things the data specifically does NOT support

- Any claim about agent consciousness, self-modeling, or identity at the theoretical level
- Any normative claim about which training pipeline is "better"
- Any claim about human-like psychology
- Any claim that Claude is "more calibrated" or "more capable" than Llama Instruct
- Any claim that RLHF (any flavor) is inherently bad or good for alignment
- Any claim about universal phase transitions in LLM policy space
