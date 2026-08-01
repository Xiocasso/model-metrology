# Stress-Covariance Signatures in LLMs Are Scenario Artifacts: A Preregistered Replication Failure

**Yunpeng Xiong** — Independent Researcher, Netherlands

**Draft v0 — 2026-08-01. Workshop-note length. Negative result.**

## Title options

1. *Stress-Covariance Signatures in LLMs Are Scenario Artifacts: A Preregistered Replication Failure*
2. *No Stable Stress Signature: A Preregistered Test of Covariance Fingerprints Across a Post-Training Pipeline*
3. *The Signature That Wasn't: Scenario Dependence and a Degenerate-Cell Artifact in LLM Stress-Covariance Probing*

## Abstract

A 2026-04 study reported that two RLHF-trained language models carry opposite, cross-scenario-robust "stress signatures" in the covariance structure of their structured decisions: Claude Haiku 4.5's effective dimensionality (Participation Ratio, PR) rose under graded interaction stress in both test scenarios, Llama 3.1 8B Instruct's fell in both, and the Llama base model was direction-unstable. If real, such signatures would be a black-box fingerprint of a model's post-training. We preregistered a follow-up designed to break the original study's central confound (n = 2 post-trained models): the same protocol applied to a staged open pipeline (Llama 3.1 8B base → Tülu 3 SFT → DPO → RLVR-final), Meta's own Llama 3.1 8B Instruct, and two same-generation Claude models (Haiku 4.5, Sonnet 4.5) — 7 models, 2 scenarios, 13,437 valid trials. Under the preregistered CI-backed direction criterion, **zero of seven models showed a cross-scenario replicated direction**. All hypotheses (stage emergence, recipe consistency, family consistency, coupling mechanism) came out null or untestable; the model with the strongest per-scenario effects (Tülu 3 DPO) showed strong *opposite* directions in the two scenarios (r = −0.929 vs +0.857). A synthetic power calibration shows the criterion detects effects of the originally reported sizes with 98–100% probability, ruling out low power as the explanation. A secondary view pre-committed during a blind design review — excluding a degenerate stress = 0 cell in which inputs are identical at temperature 0 — partially restores a collapse signature for exactly the two end-stage post-trained models, implicating an input-diversity confound in the original protocol. We conclude that the stress-covariance signature, as measured by this protocol family, is a property of the (model, scenario) pair, not of the model, and we close this research line. The instrument, preregistration, amendments, and frozen analysis are public.

---

## 1. Background and question

The prior study (phase-transition-v1, 2026-04; 5,760 trials, 3 models) probed how the covariance of a model's structured decisions reorganizes under graded interaction stress. Its headline finding was a pair of apparently robust, opposite signatures: Claude Haiku 4.5 *decoupled* under stress — PR over the four continuous decision fields rose in both scenarios (r = +0.57 and +0.60; PR endpoints 1.14 → 1.86 and 1.52 → 2.07) — while Llama 3.1 8B Instruct *collapsed* in both (r = −0.72, p = 0.045 and r = −0.92, p = 0.0014; PR 1.94 → 1.38 and 1.51 → 1.24). The Llama 3.1 8B base model flipped direction between scenarios. A mechanism analysis attributed the divergence to dominant-coupling dynamics: collapse concentrates cross-field correlation onto one axis (commitment–urgency correlation reaching +0.98 at maximum stress), decoupling spreads it.

Both signature-bearing models were post-trained; the study could not distinguish "the post-training pipeline leaves a covariance fingerprint" from "these two particular models happen to differ." Experiment 01 was designed to break that confound with a staged-checkpoint design: if the signature is a pipeline property, it should be absent in a base model, emerge at some stage of a documented post-training recipe, and be shared within a model family.

**Research question (preregistered):** Is the direction of the stress–PR relationship a property of the post-training recipe, or an idiosyncrasy of individual models?

The preregistration committed a third possibility in advance (interpretation matrix, row 4): the signature might not generalize beyond the original pair at all, in which case the line closes with a negative-result note. This is that note.

## 2. Method

### 2.1 Protocol (pt-v1)

The instrument is the frozen `pt-v1` protocol, inherited verbatim from the 2026-04 study. Stress is operationalized as the number of consecutive failure turns — the user rejects the assistant's help — preceding a fixed target scenario, at dose levels {0, 1, 2, 3, 5, 8, 12, 16}. Per trial the model must emit a strict JSON decision: one discrete action (8-way) plus four continuous fields (confidence, risk_estimate, commitment, urgency, each in [0, 100]). Analysis uses only the four continuous fields; the prior study found the discrete action dimension largely frozen and uninformative.

Per (model, scenario): 4 persona archetypes × 8 stress levels × 30 trials = 960 trials, pooled to n = 120 per stress cell. Temperature is 0.0; the variation source is deterministic rotation of 20 failure templates by trial index. Two scenarios: A_crisis and B_opportunity.

**Primary statistic:** per (model, scenario), the Participation Ratio PR = (Σλ)²/Σλ² of the per-stress-cell covariance, and the Spearman r of PR ~ stress over the 8 cells, with a 95% CI from 2,000 bootstrap resamples of trials within cells. Direction classification: `decouple` (CI entirely > 0), `collapse` (CI entirely < 0), `none` otherwise. **Replication criterion:** a model "has a signature" only if both scenarios give the same non-`none` direction. There are no pooled p-values across models and no seed-perturbation replicas; the bootstrap unit is the trial, a real independent API sample. A calibration suite (13/13 tests) verifies the analysis chain recovers known synthetic collapse/decouple/null dose-responses before any real run.

### 2.2 Models

| Registry key | Stage / role |
|---|---|
| `llama31-8b-base` | shared base (Llama 3.1 8B) |
| `tulu3-8b-sft` | base + SFT (Tülu 3, fully documented recipe) |
| `tulu3-8b-dpo` | base + SFT + DPO (Tülu 3) |
| `tulu3-8b-final` | base + SFT + DPO + RLVR (Tülu 3) |
| `llama31-8b-instruct` | Meta's own post-training (recipe contrast) |
| `claude-haiku-45` | closed production model; direct replication target |
| `claude-sonnet-45` | same-generation family-consistency test |

Two further closed models (`gpt-4o-mini`, `kimi-k3`) were preregistered but deferred for lack of API keys (Amendment A1); their cells were never collected.

### 2.3 Hypotheses (preregistered)

- **H1 (stage emergence):** base shows no replicated signature; at least one Tülu stage does.
- **H2 (recipe over identity):** ≥ 2 of 3 post-base Tülu checkpoints share a replicated direction.
- **H3 (family consistency):** both Claude models replicate `decouple` in both scenarios.
- **H4 (coupling mechanism):** sign of Δ(max off-diagonal correlation) opposite to sign of Δ(PR) in ≥ 75% of replicated model-scenarios.

The primary claim — post-training pipelines leave black-box-detectable covariance signatures — required H1 ∧ (H2 ∨ H3).

### 2.4 Preregistration and amendments

The preregistration was committed before any API call (repository commit `ebcd621`); the analysis code was frozen before data unblinding (commit `6932fc8`). Five dated amendments were recorded, all before unblinding:

- **A1 (pilot phase, before full-run collection):** three Tülu checkpoints deterministically emit the JSON key `"risk"` for `"risk_estimate"`; the parser maps the synonym rather than systematically excluding one lineage. Also: corrected HF repo id for Llama Instruct, extended retry policy for serving cold starts, and the deferral of the two keyless closed models.
- **A2 → A4 (a round trip):** a budget-driven substitution replaced Sonnet 4.5 with Claude Haiku 3.5 (A2); mid-run, that model was found retired by the provider — every call 404ed (A4). After a budget top-up, the design reverted to the original preregistered choice, Sonnet 4.5, before any second-Claude trial was collected. Net effect: H3 is the original same-generation test. The incident record notes that A2's pinned snapshot was chosen without verifying the model was still served — an avoidable error, preserved in the audit chain.
- **A3 (blind design review, collection in progress, no trial analyzed):** three validity concerns, each answered with a pre-committed analysis rather than a criterion change: (S1) a synthetic power calibration of the direction classifier; (S2) a secondary view excluding the degenerate stress = 0 cell (see §4.2); (S3) an exploratory within-archetype view. Primary criteria unchanged.
- **A5 (during collection, before unblinding):** 49 Tülu trials (all scenario B, concentrated at high stress on `tulu3-8b-final`) failed parsing deterministically via corrupted-suffix keys (verified raw example: `"risk_estimate://estimate": 60` — valid JSON, values intact, one key corrupted). Key normalization was extended (prefix-match to canonical key, values untouched, unit-tested) and the failing trials re-collected; anything still unparseable stayed excluded.

### 2.5 Power (S1)

The CI-based direction criterion had no power analysis behind it at preregistration; A3 added one. Synthetic dose-response data at the effect sizes actually reported in 2026-04 (PR endpoints 1.14→1.86, 1.52→2.07 for decouple; 1.94→1.38, 1.51→1.24 for collapse) yields detection rates of 98–100% (per-condition: 100%, 98%, 99%, 99%), **zero** wrong-direction calls in 100 runs per condition, and 96% correct rejection on a true null. If effects of the original size were present, this design would have found them. The null below is not a power failure.

### 2.6 Data

13,440 trials attempted (7 models × 2 scenarios × 960); 13,437 valid (99.98%); 13,847 raw lines frozen 2026-07-31 under sha256 `6683d75d…bab4a` with a committed pointer. Three truncated outputs were permanently excluded, all from `tulu3-8b-final`, scenario B, stress = 16. Every (archetype × stress) cell retained ≥ 27/30 trials after the A5 repair, against a preregistered floor of 25/30. Per-model JSON validity ≥ 99.8% against a preregistered exclusion threshold of 80%.

## 3. Results

### 3.1 Primary signature table

Spearman r of PR ~ stress with bootstrap 95% CI; direction per the preregistered classifier.

| Model | Scenario | r | 95% CI | Direction |
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

**No model has a replicated cross-scenario direction.** The `replicated_directions` field is null for all seven models.

### 3.2 Hypothesis outcomes

**H1 — stage emergence: NULL.** The base model is indeed direction-unstable (strong decouple in A, collapse in B), replicating the 2026-04 base-instability observation. But no Tülu stage has a replicated signature either; H1 fails on its second conjunct.

**H2 — recipe over identity: NULL.** Zero of three post-base Tülu checkpoints have a replicated direction. The most striking case is `tulu3-8b-dpo`: strong, CI-excluding-zero effects in *both* scenarios — in *opposite* directions (A: −0.929 collapse; B: +0.857 decouple). This is not a weak or noisy signature; it is a strong signature of the (model, scenario) pair.

**H3 — family consistency: NULL.** Both Claude models decouple in scenario A (haiku +0.714, sonnet +0.619). In scenario B, haiku is `none` (its CI crosses zero by 0.024) and sonnet is `collapse` (−0.548, CI entirely negative) — directly contradicting a family-level decouple signature.

**H4 — coupling mechanism: CANNOT.** The preregistered check runs only over replicated model-scenarios; there are none (n_checks = 0).

**Primary claim (H1 ∧ (H2 ∨ H3)): NOT SUPPORTED.** Per the preregistered interpretation matrix, this outcome lands in row 4: the signature does not generalize beyond the 2026-04 pair; close the line with a negative-result note.

### 3.3 Replication verdicts against 2026-04

| 2026-04 claim | This experiment (primary) | Verdict |
|---|---|---|
| Claude Haiku 4.5 decouples in both scenarios (r = +0.57 / +0.60, point estimates) | +0.714 [CI+] / +0.595 [CI crosses 0] | **Partial**: direction consistent in both, criterion met in one. MEDIUM |
| Llama 3.1 8B Instruct collapses in both (r = −0.72 / −0.92, p = 0.0014) | −0.167 / −0.048, both `none` | **Failed to replicate** under the primary criterion. NULL — but see §3.4 |
| Base model is direction-unstable | +0.903 (A) / −0.262 (B) | **Replicated**. STRONG |

The only 2026-04 claim that replicates cleanly is the one that undermines the signature story: base-model instability.

### 3.4 Pre-committed secondary views (reported, not claim-bearing)

**S2 — excluding the degenerate s = 0 cell.** The A3 blind review noted that at temperature 0 with no failure history, all within-archetype inputs at stress = 0 are *identical*; input diversity only appears at s ≥ 1, when failure-template rotation activates. The degeneracy is directly visible in the raw curves: three model-scenarios have s = 0 Participation Ratios of exactly 1.0000 or 0.0000 (rank-collapsed or zero-variance cells) — values that cannot occur in a healthy 120-trial cell. S2 recomputes all signatures over the seven remaining stress cells. Two changes are material:

- `llama31-8b-instruct`: **collapse replicates** (−0.571 / −0.571, both CIs entirely negative). The 2026-04 collapse signature re-emerges once the degenerate cell is excluded.
- `tulu3-8b-final`: **collapse replicates** (−0.714 [−0.857, −0.214] / −0.929 [−0.964, −0.321]).

These are the two *end-stage* post-trained models in the study. All other models remain unreplicated under S2 (haiku-45 decouple/none; sonnet-45 none/collapse; base and DPO still flip; SFT none/none). Because S2 is a secondary view with no preregistered criterion attached, both results carry a MEDIUM tag and are **not findings of this experiment** (see §4.3).

**S3 — within-archetype (exploratory, n = 30/cell).** `tulu3-8b-sft` shows `decouple` in 7 of 8 archetype-scenario cells despite its pooled directions being none/decouple — suggesting that pooling across archetypes can mask within-archetype structure via archetype-mean separation. WEAK; descriptive only.

**Auxiliary observation (from A5).** `tulu3-8b-final`'s malformed-output rate is itself stress-correlated: the 49 corrupted-key parse failures concentrated at high stress in scenario B, and all 3 permanently excluded truncated trials sit at s = 16, scenario B. Output-format degradation under stress is a behavioral signal that a strict-JSON schema silently discards. WEAK; noted for future instrument design.

## 4. Discussion

### 4.1 What a scenario-dependent signature means

The natural reading of the 2026-04 result was that a model *has* a stress signature — a stable disposition, plausibly imprinted by post-training, detectable through a black-box probe. The present data are incompatible with that reading under this protocol. The strongest effects in the experiment (DPO: −0.929 and +0.857) attach to the same model in different scenarios, with opposite signs and non-overlapping CIs. Whatever PR ~ stress is measuring, it is at least as much a property of the scenario as of the model. A measurement that flips sign when the scenario changes is not construct-valid as a measurement of a model property, and no amount of per-scenario statistical strength repairs that: construct validity is exactly what the cross-scenario replication criterion operationalized, and zero of seven models pass it.

This does not mean the probe measures nothing. Per-scenario directions are often strong and well-resolved. It means the object being measured is the model-in-scenario, and the 2026-04 inference from two scenarios to "the model's signature" was premature — an inference this experiment was, by design, capable of validating and instead falsified.

### 4.2 The degenerate-cell artifact

The s = 0 flaw deserves emphasis because it was invisible for three months and sat in a preregistered, calibrated, frozen protocol. At temperature 0, the stress = 0 cell contains 30 identical inputs per archetype; every higher-stress cell contains rotated failure templates and therefore diverse inputs. The protocol thus confounds the stress dose with an input-diversity dose: the covariance at s = 0 is estimated over responses to (at most) 4 distinct prompts, while at s = 16 it is estimated over far more varied input. Any covariance statistic anchored by that first cell partially measures the diversity gradient, not the stress response. The general lesson for dose-response designs on deterministic models: **check that the variation source is constant across dose levels**. Here it was not, at exactly one dose level, and that level is the anchor of every curve.

The S2 view suggests, but cannot establish, that this artifact contributed to the original finding: with s = 0 removed, the 2026-04 Llama-collapse claim comes back, and so does collapse in the other end-stage post-trained model. The 2026-04 study is thus best described as measuring a mixture of a possible real effect and a protocol artifact, in unknown proportions.

### 4.3 Why this failure is legible — and what the S2 lead is not

Three process choices made this negative result interpretable rather than merely disappointing. First, preregistration with a complete interpretation matrix: the "signature does not generalize" cell was written down, with its publication consequence, before any data existed — so this note is the execution of a pre-committed plan, not a post-hoc salvage. Second, blind amendments: every design repair (parse aliases, the Sonnet round trip, the A5 key repair) and every secondary analysis (S1–S3) was committed before unblinding, dated, and pushed, so none of them can be a response to the results. Third, the S1 power calibration converts "we found nothing" into "we would have found the original effect with 98–100% probability, and we found nothing."

Symmetrically, the same discipline constrains what we may claim now. The S2 pattern — replicated collapse in exactly the two end-stage post-trained models — is exactly the kind of tidy story that invites over-reading. It is a secondary view, adopted mid-experiment, with no criterion attached, and it survives in 2 of 7 models. **It is not a finding of this experiment**, and we ask that it not be cited as one. It is a documented starting hypothesis for a hypothetical pt-v2 protocol with matched input diversity across all stress levels. No such follow-up is currently planned.

## 5. Limitations

- **Two scenarios.** The replication criterion is the weakest that can be called cross-scenario. A signature stable across, say, five diverse scenarios would be far stronger evidence of a model property; conversely, our scenario-dependence conclusion rests on two scenarios chosen in 2026-04, not a scenario sample.
- **Serving precision unrecorded.** The quantization/precision (FP8 vs BF16) of the hosted open checkpoints was not captured at pilot time and could not be queried retroactively (recorded in A3). This is an unresolved confound for fine-grained comparison across the open checkpoints, though it cannot explain within-model sign flips across scenarios served identically.
- **One protocol family.** All conclusions are relative to pt-v1: failure-turn stress, strict-JSON 4-field decisions, PR as the statistic, temperature 0 with template rotation. A different stress operationalization or output space could behave differently.
- **Self-replication.** The 2026-04 study and this experiment share authorship and infrastructure. The audit chain (public commits, hashes, dated amendments) mitigates but does not substitute for independent replication.
- **Deferred models.** The preregistered `gpt-4o-mini` and `kimi-k3` cells were never collected (no API keys); the closed-model arm is Claude-only.
- **Temperature-0.7 robustness not run.** Preauthorized only for a positive primary result, which did not occur.

## 6. Conclusion

We preregistered a staged-checkpoint experiment to test whether stress-covariance signatures are a property of post-training pipelines. With adequate power and a CI-backed criterion, zero of seven models showed a cross-scenario stable direction across 13,437 trials; the strongest effects flipped sign between scenarios within a single model; and a blind design review located a degenerate cell that plausibly contaminated the original positive result. Per the preregistered interpretation matrix, the research line closes.

What survives is the instrument and the audit trail: a calibrated, frozen probe (`instruments/stress_probe/`, protocol pt-v1), a preregistration with five dated blind amendments (commits `ebcd621` → `6932fc8` → final), a frozen dataset (sha256-pinned, 13,437 trials), and a worked example of a dose-response confound — unequal input diversity across dose levels at temperature 0 — that we expect recurs in other deterministic-model probing designs. We publish the negative result so that the next group to observe a clean covariance signature in two scenarios checks the third scenario, and the s = 0 cell, first.

## Reproducibility

All materials are in the public repository (github.com/Xiocasso/model-metrology): preregistration at commit `ebcd621` (before any API call), frozen analysis at `6932fc8` (before unblinding), amendments A1–A5 dated in `experiments/01-stress-signature/preregistration.md`, data pointer with sha256 `6683d75d…bab4a` (13,847 raw lines; frozen 2026-07-31), primary results in `analysis/results.json`, secondary views in `analysis/secondary_results.json`, power calibration in `analysis/power_calibration.json`. The 2026-04 prior study is `identity-os/research/phase-transition-v1/`.

## References

- Gao, P., Trautmann, E., Yu, B., Santhanam, G., Ryu, S., Shenoy, K., &
  Ganguli, S. (2017). A theory of multineuronal dimensionality, dynamics and
  measurement. bioRxiv 214262. (Participation Ratio as effective
  dimensionality.)
- Grattafiori, A., et al. (2024). The Llama 3 Herd of Models.
  arXiv:2407.21783.
- Lambert, N., et al. (2024). Tülu 3: Pushing Frontiers in Open Language
  Model Post-Training. arXiv:2411.15124.
- van Miltenburg, E., van der Lee, C., & Krahmer, E. (2021). Preregistering
  NLP Research. NAACL 2021. arXiv:2103.06944.
- Xiong, Y. (2026). Phase Transition v1 findings (archived study),
  identity-os repository, `research/phase-transition-v1/`.
