# Data and Code Pointer — Phase Transition v1

**Date archived**: 2026-04-11
**Git tag**: `phase-transition-v1` (to be created on archive commit)

---

## Raw data

| File | Size | Content |
|------|------|---------|
| `experiments/phase_transition/data/trials.jsonl` | ~6 MB, ~6,000 lines | All trial records for scenarios A and B, one JSON per line. Includes failure records and duplicate retries. Dedupe to latest successful record per `trial_id` for analysis. |
| `experiments/phase_transition/data/trials_backup_A_only.jsonl` | ~3 MB | Snapshot of the data file before migration added `scenario_id` fields. Use only for migration debugging. |

### Record schema

```json
{
  "trial_id": "A_crisis__claude__explorer__s08__t22",
  "scenario_id": "A_crisis",
  "model": "claude-haiku-4-5",
  "archetype": "explorer",
  "stress_level": 8,
  "trial_index": 22,
  "decision": {
    "action": "investigate",
    "confidence": 75,
    "risk_estimate": 45,
    "commitment": 85,
    "urgency": 90
  },
  "input_tokens": 929,
  "output_tokens": 104,
  "latency_ms": 1146,
  "timestamp": "2026-04-11T...",
  "attempts": 1,
  "error": null
}
```

- `decision == null` means the trial failed permanently (after 3 retries). Filter these out for analysis.
- Multiple records with the same `trial_id` may exist (from retries or resumed runs). Keep the latest successful one.

---

## Code

All source lives under `experiments/phase_transition/`. Self-contained; no imports from the main Identity OS codebase.

| File | Purpose |
|------|---------|
| `inference.py` | Unified client for HuggingFace router (Llama) and Anthropic (Claude). JSON output via `response_format` / tool-use forcing. |
| `scenarios.py` | 3 target scenarios (A crisis, B opportunity, C ambiguous). Only A and B have data collected. |
| `collect.py` | Async data collection runner with retry, resumability, and CLI args. |
| `smoke_test.py` | Single-trial sanity check for all 3 models. |
| `analyze.py` | Primary analysis: PR computation, per-cell bootstrap CIs, figures, Table 1. Filter to one scenario via `--scenario`. |
| `compare_scenarios.py` | Cross-scenario comparison figures (A vs B). |
| `diagnose_claude.py` | Q1-Q4 diagnostic: per-dim std, distribution histograms, eigenvalue spectrum, action distribution. |

---

## Figures

| Directory | Content |
|-----------|---------|
| `experiments/phase_transition/figures/` | Original combined analysis figures (before scenario separation) |
| `experiments/phase_transition/figures_A_crisis/` | Scenario A alone, PR analysis |
| `experiments/phase_transition/figures_B_opportunity/` | Scenario B alone, PR analysis |
| `experiments/phase_transition/figures_compare/` | Cross-scenario comparison (A vs B) |
| `experiments/phase_transition/figures_diagnose/` | Mechanism diagnostic figures (Q1-Q4 from `diagnose_claude.py`) |

### Key figures for re-use

- `figures_compare/cross_scenario_pr.png` — side-by-side PR(stress) curves showing the opposite trends
- `figures_compare/per_model_overlay.png` — per-model PR curves overlaid across scenarios
- `figures_diagnose/q1_per_dim_std.png` — per-dim variance trajectories
- `figures_diagnose/q3_claude_eigenvalues.png` — covariance eigenvalue spectrum showing the mechanism
- `figures_diagnose/q4_action_distribution.png` — discrete action distributions

---

## Reproducing the analysis

### Prerequisites

```bash
pip install httpx pydantic numpy scipy scikit-learn scikit-dimension matplotlib pandas
```

### Environment variables

```bash
set HF_TOKEN=hf_...            # HuggingFace read token with Inference Provider permission
set ANTHROPIC_API_KEY=sk-ant-...
set PYTHONIOENCODING=utf-8     # required on Windows due to Chinese path characters
```

### Re-run scenario A analysis

```bash
python experiments/phase_transition/analyze.py --scenario A_crisis --suffix _A_crisis
```

Produces `figures_A_crisis/` with 4 figures and `table_1.txt`.

### Re-run cross-scenario comparison

```bash
python experiments/phase_transition/compare_scenarios.py
```

### Re-run mechanism diagnostic

```bash
python experiments/phase_transition/diagnose_claude.py
```

### Collect more data (e.g., scenario C)

```bash
python experiments/phase_transition/collect.py --full --scenario C_ambiguous --concurrency 10
```

Estimated cost for scenario C: ~$0.60 HF + ~$2 Anthropic = **~$2.60 total**.

---

## Costs incurred so far

| Item | Cost |
|------|------|
| Scenario A (2880 trials) | ~$3 (Together + Anthropic during early exploration) |
| Scenario B (2880 trials) | ~$1.5 (HF Featherless + Anthropic) |
| Setup / smoke tests | ~$0.5 |
| **Total** | **~$5** |

---

## Known issues

1. **collect.py writes duplicate records on retry.** If a trial fails once and succeeds on a later run, both records end up in the file. Dedupe by `trial_id` keeping the latest successful record before analysis. `load_trials()` in `analyze.py` handles this automatically.
2. **Featherless occasionally returns HTTP 503** under load. The retry logic in `collect.py` handles this transparently.
3. **Claude rate limits** force concurrency ≤ 3 for pure-Claude runs. Mixed runs (Claude + Llama) handle rate limits by retrying failures at lower concurrency afterwards.
4. **PYTHONIOENCODING=utf-8 must be set** on Windows because the project path contains Chinese characters.
