# Stress-Covariance Probe — Protocol

**Protocol version**: `pt-v1` (frozen; inherited verbatim from identity-os
phase-transition-v1, 2026-04). Any change to archetype prompts, failure
templates, scenarios, or the output schema forks the version.

## What it measures

How a model's structured-decision covariance reorganizes under graded
interaction stress. Stress = number of consecutive failure turns (user rejects
the assistant's help) preceding a fixed target scenario. Dose levels:
{0, 1, 2, 3, 5, 8, 12, 16}.

Per trial the model emits a strict JSON decision: 1 discrete action (8-way) +
4 continuous fields (confidence, risk_estimate, commitment, urgency ∈ [0,100]).
Analysis uses only the 4 continuous fields.

**Primary statistic** per (model, scenario): Participation Ratio
PR = (Σλ)²/Σλ² of the per-stress-cell covariance, and the Spearman r of
PR ~ stress with a bootstrap 95% CI (resampling trials within cells).
Direction classification: `decouple` (CI > 0), `collapse` (CI < 0), `none`.

**Mechanism statistic**: max |off-diagonal correlation| per cell — collapse
concentrates coupling onto one axis; decoupling spreads it.

**Replication criterion**: same non-`none` direction across ≥2 scenarios.

## Design matrix (full run, one model, one scenario)

4 archetypes × 8 stress levels × 30 trials = 960 trials. n=120 per pooled
stress cell. Temperature 0.0 (variation source: deterministic rotation of 20
failure templates by trial index). All prompts in `conversation.py`.

## Calibration

`tests/test_analysis_calibration.py` — the analysis chain must recover known
synthetic covariance structure (collapse / decouple / null dose-responses)
before any real run. An instrument change that breaks calibration does not run.

## Usage

```python
from stress_probe.conversation import ALL_SCENARIOS
from stress_probe.runner import collect, generate_specs, load_cells
from stress_probe.analysis import stress_signature
import asyncio, numpy as np

specs = generate_specs("A_crisis", ["claude-haiku-45"])
asyncio.run(collect(specs, ALL_SCENARIOS["A_crisis"], out_path))
cells = {k: np.array(v) for k, v in load_cells(out_path, "claude-haiku-45", "A_crisis").items()}
print(stress_signature(cells))
```

Resumable: re-running `collect` skips trials already on disk. Failed trials
(decision=null) are retried on the next invocation.

## Cost table (per model, per scenario, 960 trials)

Avg ≈ 1,300 input + 60 output tokens/trial → ≈ 1.25M in / 0.06M out.

| Model class | $/M in / out | Cost per model-scenario |
|---|---|---|
| Claude Haiku 4.5 | 1.00 / 5.00 | ≈ $1.6 |
| Claude Sonnet 4.5 | 3.00 / 15.00 | ≈ $4.7 |
| GPT-4o-mini | 0.15 / 0.60 | ≈ $0.2 |
| Kimi K3 (API) | ~0.6 / 2.5 (verify) | ≈ $0.9 |
| HF router (featherless), 8B checkpoints | ~0.1–0.5 blended | ≈ $0.2–0.7 |

Fallback if a checkpoint is not served by featherless: RunPod A100 + vLLM,
~$2/hr, ~1 hr per model-scenario.
