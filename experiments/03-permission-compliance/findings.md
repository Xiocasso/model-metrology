# Findings — Experiment 03: Permission Compliance Across CN/US Models

**Status**: FINAL. 10,920 records collected (7 models × 1,560); per-file
sha256 in `analysis/results.json`. Preregistration `9bc3970`; instrument
`0cda81e` (58 tests incl. oracle-coherence regression).

## Exclusions (preregistered rule, applied)

`glm-47-flash` (46.5% JSON-valid) and `glm-47` (73.3%) fall below the
preregistered 80% validity floor and are **excluded as infrastructure
failures, not compliance results**. Root cause (from raw records): long
verbose JSON truncated at the runner's max_tokens → unterminated strings.
This is confounded between model verbosity and our token budget — but note
qwen-plus produced 100% valid JSON and claude-haiku-45 99.4% under the
identical budget. Remaining analysis: 5 models, valid trials only.

## Hypothesis outcomes

| ID | Verdict | Evidence |
|---|---|---|
| H1 spread ≥10 pp | **REFUTED — total saturation** | FalseAllow (T2+T3, C1) = **0.000 for all 5 models** (0 violations in 832 valid direct+pressured attempts). Spread 0.0 pp. Per prereg: "compliance is commoditized" — on this task style |
| H2 dose-response | **VACUOUS** | Zero caves at any step in any model; the nondecreasing criterion passes trivially but presupposed caves existed. No model yielded to the 4-step social-engineering script even once (S4 authority+urgency included) |
| H3 explicitness | **REFUTED** | C2−C1 = 0.0 pp (both zero) |
| H4 enforcement | **VACUOUS/REFUTED** | C4 = C1 = 0; nothing to reduce |

**Primary preregistered claim: none supported. The floor (violations) does
not discriminate production models on single-turn, explicitly-stated
permission tasks — they are all perfect.**

## What DOES discriminate (exploratory, post-hoc labeled)

The discriminating dimension is not safety but **usefulness under
constraint** — T4 adjacent-choice tasks (a safe allowed tool exists; a
denied tool would be more convenient):

| model | SafeChoice C1 | T4-decline C1 | SafeChoice C4 | T4-decline C4 |
|---|---|---|---|---|
| deepseek-v4-flash | **0.829** | 0.171 | 0.585 | 0.415 |
| deepseek-v4-pro | 0.760 | 0.240 | 0.625 | 0.375 |
| qwen-plus | 0.700 | 0.300 | 0.383 | 0.617 |
| minimax-m27 | 0.595 | 0.405 | 0.611 | 0.389 |
| claude-haiku-45 | 0.528 | **0.472** | 0.305 | **0.695** |

1. **Over-refusal spread is large** (C1: 17%–47% of adjacent tasks
   abandoned instead of solved with the safe tool). No model ever picked
   the denied tool — they differ in whether they still do the job.
   DeepSeek models are the most useful-while-safe; claude-haiku-45 declines
   nearly half. [MEDIUM — n=60 valid T4/model/arm, consistent across
   replicates]
2. **Visible enforcement machinery induces over-refusal**: C4 (explicit
   check/gate present) raises T4 declines for 4 of 5 models — haiku
   0.47→0.70, qwen 0.30→0.62, deepseek-flash 0.17→0.42. Announcing
   enforcement makes models abandon tasks they could complete safely — a
   chilling effect, directionally consistent with Exp-02's "A2-worst"
   observation that rule salience correlates with worse outcomes.
   [MEDIUM — post-hoc, but large and 4/5 consistent]
3. **Format robustness under a fixed token budget varies wildly**
   (GLM ~47–73% valid vs qwen 100%) — operationally relevant to agent
   builders, though confounded with our max_tokens choice. [WEAK-MEDIUM]

## Instrument lessons (for permission_bench v2)

- Single-turn quiz-style tasks with explicit rules are **saturated** across
  2026 production models; discriminating compliance requires embedded/
  indirect violations (multi-step workflows, tool-output-borne temptations,
  distractor context) — the injection-adjacent territory we scoped out.
- Raise max_tokens and add robust JSON recovery so format failure cannot
  masquerade as refusal; record token usage per call (missing this run).
- T4 (adjacent-choice) is the keeper: it produced the only large,
  replicate-stable spread. The utility axis, not the violation axis, is
  where 2026 models differ.

## Money spent (experiment total)

≈ $4.9: OpenRouter ≈ $2.1 (glm/qwen/minimax incl. excluded models),
DeepSeek ≈ ¥6 (~$0.8), Anthropic ≈ $2.0. Under the $15 cap; wallets remain
prepaid-only.
