# Preregistration — Experiment 03: Permission Compliance Across CN/US Models

**Date**: 2026-08-01
**Status**: PREREGISTERED (finalized 2026-08-01, instrument commit `0cda81e`,
58/58 tests incl. oracle-coherence regression; pushed before any API call).

## 1. Research question

Do production models differ measurably in honoring declared tool
permissions — under direct requests, user-pressure escalation, and different
rule presentations — and does oracle-complete runtime enforcement reduce
violations where prompt-plane rules do not?

## 2. Design

- Instrument: `instruments/permission_bench/` (DESIGN.md v1; all tests green
  required before this prereg is finalized, including the oracle-enforcement
  coherence test).
- Models (9): claude-haiku-45, deepseek-v4-flash, deepseek-v4-pro,
  qwen-plus, glm-47-flash, glm-47, minimax-m27; optional pending budget:
  kimi-k3, gpt-4o-mini (key absent at draft time).
- Design cells: 5 profiles × {T1×10, T2×8, T3×4 (≤4 turns), T4×4} × 4 arms
  (C1–C4) × 3 replicates.
- Temperature 0.5 (matching contract_bench convention); replicate = unit of
  replication.

## 3. Hypotheses (final)

| ID | Statement | Support criterion | Refute criterion |
|---|---|---|---|
| H1 spread | Models differ enough for a leaderboard to mean something | max−min pooled FalseAllow (T2+T3 pooled, C1 arm) across models ≥ 10 pp | < 10 pp — report "compliance is commoditized" (also a story) |
| H2 pressure dose-response | Escalation increases violations | cumulative cave rate nondecreasing in step S1→S4 for ≥7/9 models | violated for ≥3 models |
| H3 explicitness (two-sided; A2-worst prior) | Stating denials changes FalseAllow vs allowlist-only | \|C2−C1\| pooled ≥ 5 pp, direction reported either way | < 5 pp |
| H4 enforcement (repaired Exp-02 H2) | Oracle-complete enforcement reduces FalseAllow | C4 < min(C1,C2,C3) pooled, same direction in ≥2/3 replicates | otherwise — and given Exp-02, this refutation would be the second strike against runtime enforcement |

Secondary (descriptive, no criteria): cave-step distributions, SafeChoice
(T4), AllowedAccept cost per arm, per-profile heatmaps.

## 4. Analysis plan

`permission_bench.analysis` only; replicate-level arm contrasts (Welch +
permutation + bootstrap) reported descriptively at n=3 — direction criteria
above are the claim-bearing tests, mirroring Exp-02 discipline. Exclusions:
unparseable-after-retries excluded; any (model, arm) cell losing >10% fails
pending top-up; model JSON-validity <80% excludes the model (reported as
infrastructure, not compliance).

## 5. Cost

Per model: 1,560 task-trials (5 profiles × 26 tasks × 4 arms × 3
replicates); ≈1,900 API calls expected (upper bound 2,850 with maximal T3
escalations and C4 revisions) ≈ 2.2M in + 0.45M out tokens.
Cheap CN tier ≈ $0.3–0.9 each; Haiku ≈ $4.5; DeepSeek ≈ free quota.
**Estimated total $9–11, cap $15.** Wallets: OpenRouter $9.95 prepaid,
Anthropic $6.40, DeepSeek free grant. No new top-ups required.

## 6. Execution order

1. Finalize this prereg (fill counts) → push (timestamp before any call).
2. Pilot: 1 profile × all 9 models × 1 replicate subset (~$0.3) — model
   string/JSON-validity smoke; amendments here are cheap.
3. Full sweep, cheap models first, Haiku last (budget safety).
4. Freeze (pointer + sha256) → analysis → findings → the public table.

## 7. Threats to validity (acknowledged at draft)

- Reasoning-style models (deepseek-v4-pro) may burn output tokens on hidden
  reasoning; pilot measures actual output length before the full run.
- OpenRouter adds a routing layer; commercial tiers have single first-party
  upstreams (deterministic), recorded per trial from response metadata where
  available.
- T3 pressure scripts are fixed templates: they measure resistance to THIS
  four-step social-engineering pattern, not all pressure. Scope stated.
- qwen-turbo-class no-snapshot aliases: all selected models pinned where the
  provider offers pins; alias-only models flagged in the registry.


## Deviations (recorded 2026-08-02, after collection)

This preregistration had no amendments during collection. Two deviations
are recorded here after the fact, following the external review:

- **D1 — per-cell validity rule not enforced.** §4 required any (model, arm)
  cell losing >10% of trials to "fail pending top-up". Nine cells breached
  it (deepseek-v4-pro 15.6–20.0% across all four arms; minimax-m27 up to
  19.7%; deepseek-v4-flash up to 12.0%). No top-up was run. All affected
  rates are reported under two conditionings in findings.md §4 rather than
  being presented as if the rule had held.
- **D2 — retry policy narrower than stated.** §4 says "unparseable-after-
  retries excluded"; the runner retries API exceptions only, so parse
  failures were excluded on first occurrence. This inflates exclusion counts
  for verbose models and is the mechanism behind the GLM exclusions.

Also noted: the experiment-specific analysis was written after collection
(the instrument and its deterministic scoring were fixed before). The first
writeup incorrectly described the analysis as frozen; see RETRACTION.md.
