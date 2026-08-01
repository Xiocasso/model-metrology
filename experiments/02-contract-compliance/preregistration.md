# Preregistration — Experiment 02: Contract Compliance, v2 Task Set

**Date**: 2026-08-01
**Status**: PREREGISTERED — committed before any API call.
**Instrument**: `instruments/contract_bench/` (35/35 offline tests passing;
fixtures frozen from identity-os head `603b10e`, engine v6.2)
**Prior work**: identity-os ContractInterface benchmark (2026-04, 4,000
Haiku trials): A3 enforcement reduced FalseAllow 5.6% → 2.2% vs narrative
prompting — but the entire effect came from the Guardian profile, because the
v1 task generator produced zero profile-specific forbidden tasks for the
other three profiles (root cause documented in `contract_bench/tasks.py`).

## 1. Research question

Does the v2 task generator (suppressed-mode exclusions + risk-posture
handling) make FalseAllow measurable for all four profiles, and does the
runtime-enforcement effect (A3 < prompt-only arms) replicate on the repaired
task set?

## 2. Design

- Model: `claude-haiku-45` (`claude-haiku-4-5-20251001`, pinned; same model
  family as the original run).
- Task set: **v2** (per-profile composition: Explorer 15 / Guardian 14 /
  Diplomat 3 / Commander 9 profile-specific forbidden tasks of 25; the
  remainder always-forbidden; plus 25 legitimate tasks each).
- Arms: A0 (no contract), A1 (narrative), A2 (query-plane in prompt),
  A3 (enforced check+gate, one revision).
- Replicates: **3** (temperature 0.5). Fixed in advance; budget-constrained
  (live balance $6.40). Any extension is a new experiment, not a top-up.
- Total: 4 profiles × 50 tasks × 4 arms × 3 replicates = **2,400 trials**.

## 3. Hypotheses

| ID | Statement | Support criterion | Refute criterion |
|---|---|---|---|
| H1 (repair works) | v2 gives nonzero FalseAllow *opportunity uptake* in baseline arms | ≥3 of 4 profiles show FalseAllow > 0 in A0 or A1 (pooled over replicates) | ≤2 profiles (repair failed or model refuses profile-specific forbidden tasks regardless) |
| H2 (enforcement direction) | A3 reduces FalseAllow vs the best prompt-only arm | pooled A3 FalseAllow < pooled min(A0, A1, A2), same direction in ≥2 of 3 replicates | A3 ≥ prompt-only arms |
| H3 (cost check) | Enforcement cost on legitimate tasks is bounded | A3 AllowedAccept drop vs A0 ≤ 15 pp (original observed ~7.4 pp) | larger drop |

n=3 replicates supports direction checks, not tight CIs — H2's criterion is
deliberately directional. Replicate-level stats (Welch/permutation/bootstrap
from `contract_bench/analysis.py`) are reported descriptively; no p-value
claims will be headlined at n=3.

## 4. Analysis plan (frozen)

`contract_bench.analysis` per (arm, profile): AllowedAccept, ForbiddenBlock,
FalseAllow, FalseBlock; arm contrasts at replicate level. Exclusions: trials
with no parseable decision after retries are excluded; a (profile, arm) cell
losing >10% of trials fails the run pending top-up; model JSON-validity <80%
excludes the run.

## 5. Cost (approved scope)

2,400 trials × (~800 in + ~150 out) tokens ≈ 1.9M in / 0.36M out
→ ≈ **$3.8** (Haiku $1/$5). Pilot ≈ $0.10. Cap for this experiment: **$5.5**
(within live balance $6.40). If the balance proves insufficient mid-run, the
run pauses (resumable) rather than degrading.

## 6. Execution order

1. Pilot: 1 profile (guardian) × 4 arms × 2 tasks × 1 replicate = 8 trials
   (~$0.02) — verifies decision parsing, A3 revision flow, scoring.
2. Full run (background, resumable).
3. Analysis via `contract_bench.analysis`; findings.md with confidence tags.

## 7. Threats to validity (acknowledged)

- v2's posture-exclusion rules are our design (documented in tasks.py);
  Diplomat's forbidden pool is thin (3 tasks) — its H1 cell is low-powered
  and a Diplomat miss will be reported as "insufficient tasks", not failure.
- v1-vs-v2 results are not comparable head-to-head; this experiment measures
  the repaired construct, not a delta against the 2026-04 numbers.
- Same-provider evaluation concerns do not apply: scoring is deterministic
  (oracle-derived), no LLM judge anywhere.
