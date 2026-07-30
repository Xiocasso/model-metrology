# Findings — Experiment 01: Stress Signature × Post-Training Stage

**Status**: FINAL — filled from `analysis/results.json` (frozen analysis,
commit `6932fc8`) and `analysis/secondary_results.json` (pre-committed A3
views) after data freeze.
**Data**: [POINTER.md](data/POINTER.md) — sha256 `6683d75d…bab4a`,
13,437 unique successful trials, 13,847 raw lines, frozen 2026-07-31.
**Amendments in effect**: A1 (parse aliases, instruct repo id, retries),
A2+A4 (Sonnet 4.5 round trip), A3 (S1 power calibration; S2/S3 secondary
views), A5 (corrupted-suffix key repair).

## Confidence legend

- **[STRONG]** replicated across both scenarios, CI excluding zero
- **[MEDIUM]** one scenario, or secondary-view only — needs replication
- **[WEAK]** suggestive, not statistically robust
- **[NULL]** predicted but not observed
- **[CANNOT]** the data cannot speak to this

---

## Signature table (primary, preregistered)

| model | scenario | r | 95% CI | direction |
|---|---|---|---|---|
| llama31-8b-base | A_crisis | +0.903 | [+0.805, +0.976] | decouple |
| llama31-8b-base | B_opportunity | −0.262 | [−0.333, −0.071] | collapse |
| tulu3-8b-sft | A_crisis | +0.000 | [−0.452, +0.262] | none |
| tulu3-8b-sft | B_opportunity | +0.619 | [+0.286, +0.905] | decouple |
| tulu3-8b-dpo | A_crisis | −0.929 | [−0.976, −0.809] | collapse |
| tulu3-8b-dpo | B_opportunity | +0.857 | [+0.452, +0.952] | decouple |
| tulu3-8b-final | A_crisis | −0.143 | [−0.405, +0.119] | none |
| tulu3-8b-final | B_opportunity | −0.286 | [−0.309, +0.143] | none |
| llama31-8b-instruct | A_crisis | −0.167 | [−0.833, +0.191] | none |
| llama31-8b-instruct | B_opportunity | −0.048 | [−0.429, +0.262] | none |
| claude-haiku-45 | A_crisis | +0.714 | [+0.429, +0.809] | decouple |
| claude-haiku-45 | B_opportunity | +0.595 | [−0.024, +0.857] | none |
| claude-sonnet-45 | A_crisis | +0.619 | [+0.214, +0.857] | decouple |
| claude-sonnet-45 | B_opportunity | −0.548 | [−0.762, −0.048] | collapse |

**No model has a replicated (cross-scenario) direction under the primary
criterion.** `replicated_directions` is null for all seven models.

## Hypothesis outcomes

### H1 — Stage emergence: [NULL]

Criterion: base has no replicated signature; ≥1 Tülu stage does.
Result: base indeed has none (direction flips between scenarios, replicating
the 2026-04 base-instability observation) — but **no Tülu stage has a
replicated signature either**. H1 fails on its second conjunct.

### H2 — Recipe over identity: [NULL]

Criterion: ≥2 of 3 post-base Tülu checkpoints share a replicated direction.
Result: zero Tülu checkpoints have a replicated direction. Notably
tulu3-8b-dpo shows **strong opposite directions per scenario** (A: −0.929
collapse; B: +0.857 decouple) — the signature is scenario-dependent, not a
stable model property.

### H3 — Family consistency, same-generation (A4-final): [NULL]

Criterion: both Claude models replicate `decouple` in both scenarios.
Result: both decouple in scenario A (haiku +0.714, sonnet +0.619) — but in
scenario B haiku is `none` (CI crosses zero by 0.024) and **sonnet is
`collapse` (−0.548)**, directly contradicting the family-decouple story.

### H4 — Coupling mechanism: [CANNOT]

No replicated model-scenarios exist, so the preregistered check has zero
eligible cases (n_checks = 0).

### Primary claim (H1 ∧ (H2 ∨ H3)): **NOT SUPPORTED**

## Interpretation-matrix cell reached (prereg §5)

Row 4: **"Signature does not generalize beyond the 2026-04 pair → close the
line with a negative-result note."** The primary conclusion of Experiment 01
is that the stress-covariance signature, as measured by protocol pt-v1, is
**not a stable property of a model**: direction depends on the scenario at
least as much as on the model or its training recipe.

## Replication of phase-transition-v1 (2026-04)

| 2026-04 claim | This experiment (primary) | Verdict |
|---|---|---|
| Claude Haiku 4.5 decouples, both scenarios (r = +0.57/+0.60, point est.) | +0.714 [CI+] / +0.595 [CI crosses 0] | **Partial**: direction consistent in both, criterion met in one [MEDIUM] |
| Llama 3.1 8B Instruct collapses, both (r = −0.72/−0.92, p = 0.0014) | −0.167 / −0.048, both `none` | **Failed to replicate** under primary criterion [NULL] — but see S2 |
| Base is direction-unstable | +0.903 A / −0.262 B | **Replicated** [STRONG] |

## Pre-committed secondary views (A3) — reported, not claim-bearing

**S2 (exclude the degenerate s=0 cell)** changes the picture materially:

- **llama31-8b-instruct: collapse replicates** (−0.57 / −0.57, both CI−).
  The 2026-04 collapse signature re-emerges once the s=0 cell — identical
  inputs at temperature 0, flagged as a design flaw in our own A3 review —
  is excluded. [MEDIUM]
- **tulu3-8b-final: collapse replicates** (−0.71 / −0.93, both CI−). The two
  END-STAGE post-trained models in the study are the two that show replicated
  collapse under S2. [MEDIUM]
- All other models remain unreplicated under S2 (haiku-45: decouple/none;
  sonnet-45: none/collapse; base and dpo still flip; sft none/none).

**S3 (within-archetype)**: tulu3-8b-sft shows `decouple` in 7 of 8
archetype-scenario cells despite pooled `none`/`decouple` — suggesting
archetype-mean separation masks within-archetype structure for this model.
[WEAK — exploratory, n=30/cell]

**Auxiliary observation** (A5): tulu3-8b-final's malformed-output rate is
stress-correlated (all parse failures at s=16, scenario B; 3 permanently
excluded trials all there). Output-format degradation under stress is itself
a behavioral signal our schema discards. [WEAK]

## Quality / exclusions

- 13,437/13,440 trials valid; 3 truncated outputs permanently excluded
  (all tulu, s=16, scenario B). All (archetype × stress) cells ≥ 25/30
  (min observed after A5 repair: 27/30). Validity rate ≥ 99.8% per model.
- `gpt-4o-mini`, `kimi-k3` deferred (no API keys; A1 §4).
- Serving precision per open checkpoint not recorded (A3) — unresolved
  confound for cross-provider comparison of open checkpoints.

## What closes and what stays open

**Closed** (per prereg matrix): the pipeline-signature research line in its
pt-v1 form. The protocol's own s=0 flaw and the scenario-dependence finding
mean the 2026-04 "robust cross-scenario signatures" were substantially
protocol artifacts.

**Documented for any future follow-up** (not planned): a pt-v2 protocol
without the s=0 degenerate cell, with matched input-diversity across stress
levels, would test the one pattern S2 left standing — replicated collapse in
end-stage post-trained models (llama-instruct, tulu-final). That pattern is
[MEDIUM] evidence at best and must not be cited as a positive finding of
this experiment.

## Robustness (preauthorized, prereg §8)

Not run: the primary result is negative, so the temperature-0.7 re-run
condition ("only if the primary result is positive") does not trigger.
