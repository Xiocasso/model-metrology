# Preregistration — Experiment 01: Stress Signature × Post-Training Stage

**Date**: 2026-07-30
**Status**: PREREGISTERED — committed before any API call. Data collection has
NOT started. Changes after collection starts require a dated amendment section.
**Instrument**: `instruments/stress_probe/` (protocol `pt-v1`, calibration passing: 13/13 tests)
**Prior work**: identity-os `research/phase-transition-v1/` (2026-04). Its Finding 2:
Claude Haiku 4.5 decouples (PR rises) under stress in both scenarios; Llama 3.1
8B Instruct collapses (PR falls) in both; the base model is direction-unstable.
Fatal confound: n=2 RLHF models — pipeline effect vs model idiosyncrasy could
not be separated. This experiment exists to break that confound.

---

## 1. Research question

Is the stress-covariance signature (direction of PR ~ stress) a property of the
**post-training recipe**, or an idiosyncrasy of individual models?

## 2. Design

Two arms, one shared protocol (`pt-v1`), two scenarios (A_crisis, B_opportunity).

### Arm 1 — Staged open checkpoints (causal test)

Same base model (Llama 3.1 8B), two documented post-training lineages:

| Registry key | Stage | Lineage |
|---|---|---|
| `llama31-8b-base` | base | shared origin |
| `tulu3-8b-sft` | SFT | Tülu 3 (fully documented recipe) |
| `tulu3-8b-dpo` | SFT+DPO | Tülu 3 |
| `tulu3-8b-final` | SFT+DPO+RLVR | Tülu 3 |
| `llama31-8b-instruct` | Meta's own post-training | Meta (recipe contrast) |

### Arm 2 — Closed production models (generalization / family consistency)

`claude-haiku-45` (pinned snapshot; replication), `claude-haiku-35`
(cross-generation within-family test; see Amendment A2), `gpt-4o-mini`,
`kimi-k3`.

**Total**: 9 models × 2 scenarios × 960 trials = **17,280 trials**.

## 3. Hypotheses (preregistered)

| ID | Statement | Support criterion | Refute criterion |
|---|---|---|---|
| H1 (stage emergence) | The signature is absent in base and emerges at some post-training stage | base = `none` or scenario-inconsistent; ≥1 Tülu stage shows replicated direction (same across both scenarios) | all Tülu stages `none` or inconsistent |
| H2 (recipe > identity) | Direction is recipe-linked: Tülu staged checkpoints agree with each other more than chance; Meta-Instruct may differ from Tülu | ≥2 of 3 post-base Tülu checkpoints share a replicated direction | Tülu checkpoints mutually inconsistent |
| H3 (family consistency) | Claude family members share the replicated `decouple` direction found in 2026-04 | both Claude models replicate `decouple` in both scenarios | directions differ between the two Claude models → signature is per-model, not per-pipeline |
| H4 (mechanism) | Direction is driven by dominant-coupling dynamics | sign of Δ(max off-diag corr) opposite to sign of Δ(PR) in ≥ 75% of replicated-direction model-scenarios | no systematic coupling-PR relation |

**Primary claim** ("post-training pipelines leave black-box-detectable
covariance signatures") requires H1 ∧ (H2 ∨ H3). H2 and H3 failing together
kills the pipeline interpretation regardless of other results.

## 4. Analysis plan (frozen)

- Primary statistic: per (model, scenario), Spearman r of PR ~ stress over the
  8 stress cells; 95% CI via 2,000 bootstrap resamples of trials within cells.
  Direction = `decouple` / `collapse` / `none` per `stress_probe.analysis`.
- Replication unit: a model has "a signature" only if both scenarios give the
  same non-`none` direction (`signatures_agree`).
- NO pooled p-values across models. NO seed-perturbation replicas. The
  bootstrap unit is the trial (a real, independent API sample).
- Secondary: coupling curves (max |off-diag corr|), per-archetype breakdown
  (exploratory only, n=30/cell — reported with CIs, no claims).
- Exclusion rules: trials with decision=null after 3 retries are excluded; a
  cell with < 25/30 valid trials fails the run for that model until topped up;
  a model whose JSON-validity rate is < 80% overall is excluded and reported
  as an infrastructure failure, not a finding.

## 5. Interpretation matrix (pre-specified)

| H1 | H2 | H3 | Interpretation |
|---|---|---|---|
| ✓ | ✓ | ✓ | Pipeline-signature claim stands; paper: "Post-training leaves a black-box covariance fingerprint" with stage localization |
| ✓ | ✓ | ✗ | Recipe effect real in open models; Claude 2026-04 result was model-idiosyncratic; narrower paper |
| ✓ | ✗ | ✓ | Signatures exist per-family but Tülu stages disagree → training-stage story wrong; report as constraint |
| ✗ | — | — | Signature does not generalize beyond the 2026-04 pair → close the line with a negative-result note |

Any cell of this matrix is a publishable outcome; none is a failure of the
experiment.

## 6. Cost & infrastructure (requires director approval before any call)

| Item | Estimate |
|---|---|
| Arm 1: 5 open checkpoints × 2 scenarios via HF router (featherless) | ≈ $3–7 |
| Arm 2: Haiku $3.2 + Sonnet $9.4 + 4o-mini $0.4 + Kimi K3 $1.8 | ≈ $15 |
| Pilot + retries + 20% margin | ≈ $5 |
| **Total estimate** | **≈ $25–30** |
| **Requested budget cap** | **$50** |
| Fallback (checkpoints not on featherless): RunPod A100 ≈ $2/hr × ~10 h | + ≈ $20 (within cap) |

## 7. Execution order

1. **Pilot** (≈ $1): availability smoke test — 5 trials per model × 9 models;
   verifies model strings, JSON validity, featherless serving of Tülu
   checkpoints, Kimi K3 model id. Abort/amend here costs nothing.
2. Arm 1 full run, scenario A then B.
3. Arm 2 full run, scenario A then B.
4. Data freeze (raw JSONL committed via pointer + hash), then analysis.
5. `findings.md` with confidence tags; `interpretation.md` dated.

## Amendments

### A1 — 2026-07-30, pilot phase (before full-run data collection)

Pilot findings and fixes, all made before any full-run trial:

1. All three Tülu checkpoints deterministically emit the key `"risk"` instead
   of `"risk_estimate"` on some trials (valid JSON, synonym key, temperature 0).
   `parse_decision` now maps `risk` → `risk_estimate` when the canonical key is
   absent. Rationale: value semantics identical; systematic exclusion would
   bias cell composition against the Tülu lineage. Prompt text unchanged.
2. `llama31-8b-instruct` model string corrected to `meta-llama/Llama-3.1-8B-Instruct`
   (Meta renamed the HF repo; old id 400s on featherless).
3. Retry policy extended for featherless on-demand cold starts (max 5 attempts,
   503 backoff up to 60 s).
4. `gpt-4o-mini` and `kimi-k3` are deferred: no API keys available. Arm 2 runs
   with the two Claude models; the OpenAI/Moonshot cells will be added under
   this same protocol if keys are provided later, before data freeze.

### A2 — 2026-07-30, before Arm 2 data collection (Arm 1 in progress)

Budget-driven substitution, decided by the director: `claude-sonnet-45`
(Sonnet 4.5, ~$11 for its cells) is replaced by `claude-haiku-35`
(`claude-3-5-haiku-20241022`, ~$3) after checking the live Anthropic balance
($8.30) against the projected Arm 2 cost (~$15).

Effect on H3: the within-family consistency test becomes a **cross-generation**
test (Haiku 4.5 vs Haiku 3.5, ~1 year apart). Support criterion unchanged in
form: both Claude models replicate `decouple` in both scenarios. This is a
strictly HARDER test than same-generation consistency (pipeline signature must
survive a generation change); a failure is correspondingly less diagnostic
(could be generation drift rather than absence of a family signature) — this
asymmetry will be stated in findings.md if H3 fails. No Arm 2 full-run trials
had been collected at amendment time; the 6 Sonnet pilot trials in
pilot.jsonl are retained as pilot data and excluded from analysis (as all
pilot data already is).

### A3 — 2026-07-31, pre-committed while blind (collection in progress, no
### trial analyzed)

Setup review before unblinding surfaced three validity concerns. Responses,
all committed before any data was seen; primary criteria are UNCHANGED:

1. **Power calibration of the direction classifier (S1).** The CI-based
   direction criterion had no power analysis behind it. A synthetic
   calibration at the effect sizes observed in phase-transition-v1
   (`analysis/secondary_analysis.py --power`, results in
   `analysis/power_calibration.json`): detection 98–100% on true effects,
   0% wrong-direction calls, 96% correct rejection on null. The
   preregistered criterion stands as-is — no amendment to the criteria
   needed.
2. **Degenerate stress=0 cell (S2).** At temperature 0 with no failure
   history, within-archetype inputs at s=0 are identical; input diversity
   grows with stress (template rotation activates at s≥1). A pre-committed
   secondary view recomputes all signatures excluding the s=0 cell. If a
   primary direction call does not survive s=0 exclusion, findings.md must
   flag it as potentially an input-diversity artifact. (This concern applies
   equally to phase-transition-v1 and was previously unnoticed.)
3. **Archetype pooling (S3).** Pooled cells (4 archetypes × 30) mix
   within-archetype coupling with between-archetype mean separation. A
   pre-committed exploratory view computes per-archetype signatures
   (n=30/cell). No criteria attached; reported descriptively.

Also recorded at review: serving precision per open checkpoint (FP8/BF16 on
featherless) was not captured at pilot time and cannot be queried
retroactively — carried as a limitation. Process rule reaffirmed: data freeze
requires full.py exit 0 and zero incomplete cells (prereg §4 top-up rule).

### A4 — 2026-07-31, during Arm 2 collection (incident record; resolution TBD)

The A2 substitute `claude-3-5-haiku-20241022` has been **retired by Anthropic**
(404 on every call; absent from /v1/models). The A2 substitution is therefore
void — A2's pinned snapshot was chosen without verifying the model was still
served, which was an avoidable error. No Haiku-class second Claude exists on
the current API; remaining same-family options are Sonnet/Opus/5-family tier.

Incident details: 240 haiku-35 trials failed with 404 and, due to a runner
scheduling behavior (asyncio.as_completed set-ordering + semaphore held across
retries), starved all claude-haiku-45 trials for ~16 minutes. No data loss;
failed trials retry on re-run. haiku-35 is removed from the run list;
claude-haiku-45 (verified alive) and remaining Arm 1 retries proceed.

Resolution of H3's second model awaits a director decision (budget-dependent);
it will be recorded here as A4-final before any second-Claude trial is
collected.

## 8. Threats to validity (acknowledged at preregistration)

- Featherless serving precision (FP8 vs BF16) may differ per checkpoint —
  recorded per model at pilot time; a precision mismatch within Arm 1 is
  reported as a limitation, not silently accepted.
- Claude Haiku "replication" uses a pinned snapshot that may differ from the
  2026-04 endpoint state; direction replication is the claim, not value replication.
- The 4-dim schema may capture number-formatting habits rather than decision
  structure; the staged design partially controls this (same base, same
  tokenizer, different post-training) — a base-vs-SFT signature change cannot
  come from tokenizer priors alone.
- Temperature 0.0 with template rotation is the pt-v1 variation source; a
  temperature-0.7 robustness re-run of ONE model pair is preauthorized within
  the budget cap if the primary result is positive.
