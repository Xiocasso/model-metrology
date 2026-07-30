# Findings — Experiment 01: Stress Signature × Post-Training Stage

**Status**: TEMPLATE — pre-structured before unblinding. To be filled ONLY
from `analysis/results.json` after data freeze. No claim may appear here that
is not backed by a number in results.json.

**Data**: [POINTER.md](data/POINTER.md) — sha256, counts, freeze timestamp
**Analysis**: frozen at commit `6932fc8` (before data collection completed)
**Amendments in effect**: A1 (risk-key alias, instruct repo id, retry policy),
A2 (Haiku 3.5 replaces Sonnet 4.5; H3 is cross-generation)

## Confidence legend

- **[STRONG]** replicated across both scenarios, CI excluding zero
- **[MEDIUM]** one scenario, or CI near zero — needs replication
- **[WEAK]** suggestive, not statistically robust
- **[NULL]** predicted but not observed
- **[CANNOT]** the data cannot speak to this

---

## Signature table

<!-- paste the per-model table from analyze.py output -->

| model | scenario | r | 95% CI | direction |
|---|---|---|---|---|
| TBD | | | | |

## Hypothesis outcomes

### H1 — Stage emergence: [TBD]

Criterion: base has no replicated signature; ≥1 Tülu stage does.
Result: <!-- replicated_directions from results.json -->

### H2 — Recipe over identity: [TBD]

Criterion: ≥2 of 3 post-base Tülu checkpoints share a replicated direction.
Result:

### H3 — Family consistency, cross-generation (A2): [TBD]

Criterion: both Claude models replicate `decouple` in both scenarios.
Result:
Note (per A2): a failure here cannot distinguish generation drift from
absence of a family signature — state this explicitly if H3 fails.

### H4 — Coupling mechanism: [TBD]

Criterion: Δcoupling sign opposite ΔPR sign in ≥75% of replicated
model-scenarios. Result: opposite_sign_fraction = TBD (n_checks = TBD).

### Primary claim (H1 ∧ (H2 ∨ H3)): [TBD]

## Replication of phase-transition-v1 (2026-04)

Prior result (identity-os, `research/phase-transition-v1/findings.md`):
Claude Haiku 4.5 **decoupled** in both scenarios (r = +0.57 / +0.60, point
estimates only, n=120/cell); Llama 3.1 8B Instruct **collapsed** (r = −0.72 /
−0.92); base was direction-unstable. This experiment re-measures all three
under the same protocol with CI-backed direction calls:

- claude-haiku-45 (same pinned snapshot): TBD — direction replication [Y/N]
- llama31-8b-instruct: TBD
- llama31-8b-base: TBD

## Quality / exclusions

<!-- from results.json quality blocks: validity rates, incomplete cells,
     any excluded model. Also note gpt-4o-mini and kimi-k3 deferred (A1 §4). -->

## Interpretation-matrix cell reached (prereg §5)

<!-- state which row of the preregistered matrix the results land in,
     and therefore what the writeup is: full paper / narrower paper /
     constraint report / negative-result note. -->

## Robustness (preauthorized, prereg §8)

Temperature-0.7 re-run of one model pair: [run / not run — run only if
primary result positive]. Result: TBD
