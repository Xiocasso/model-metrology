# Model Metrology

Black-box behavioral measurement instruments for AI models and agents.
Preregistered, auditable, and cheap to reproduce (each experiment ≈ $5).

## What this is

Measurement instruments — not benchmarks-as-leaderboards. Every experiment
here is preregistered before any API call (timestamped in this repo's
history) and shipped with per-file data hashes. Where the analysis code was
also frozen before unblinding, that is stated per experiment; where it was
not (Experiment 03), that is stated too — the gap between "instrument
frozen" and "analysis frozen" is where Experiment 03's first writeup went
wrong, and the [retraction](experiments/03-permission-compliance/RETRACTION.md)
is published alongside the corrected result. Negative results are published
with the same care as positive ones; three of the experiments below came
back null, and the nulls are load-bearing.

## Experiments

| # | Question | Verdict | Where |
|---|---|---|---|
| 01 | Do post-training pipelines leave a "stress signature" in decision covariance? | **Null** — signature is scenario-dependent, not a model property; prior positive result traced to a protocol artifact | [`experiments/01-stress-signature/`](experiments/01-stress-signature/) |
| 02 | Does runtime contract enforcement beat prompt-stated constraints? | **Null** — the prior +61% claim rested on a degenerate task set; enforcement is only as good as what the contract encodes | [`experiments/02-contract-compliance/`](experiments/02-contract-compliance/) |
| 03 | Which models leak tool permissions under social-engineering pressure? | **0 denied-tool selections in 832 valid records** in the direct+pressure cell (5 CN/US models) — 5 violations do exist in other cells. Larger effect: *stating* a deny list cuts safe task completion by 4–40 pp in 5/5 models, while runtime enforcement afterwards does not. [v1 writeup retracted after external review](experiments/03-permission-compliance/RETRACTION.md) | [`experiments/03-permission-compliance/`](experiments/03-permission-compliance/) |

## Papers (drafts, targeting the NeurIPS 2026 workshop cycle)

- **Triangulate Before You Trust** — a same-provider LLM judge produced
  p = 0.039 on the authors' own hypothesis; cross-lineage regrading, cluster
  correction, and a direct judge×arm interaction test each independently
  removed it. [`docs/papers/judge-bias/`](docs/papers/judge-bias/)
- **No Stable Stress Signature** — preregistered replication failure of
  Experiment 01's target, with the degenerate-cell confound that produced
  the original result. [`docs/papers/stress-signature-null/`](docs/papers/stress-signature-null/)

## Instruments

| Instrument | Measures | Status |
|---|---|---|
| [`permission_bench`](instruments/permission_bench/) | Tool-permission adherence: direct violations, 4-step pressure escalation, rule-presentation arms, adjacent-choice utility | **Flagship** — Experiment 03 complete; v2 (embedded violations) planned |
| [`contract_bench`](instruments/contract_bench/) | Contract-stated action compliance (4-arm: none / narrative / in-prompt / enforced) | Calibration-era; Experiment 02 complete |
| [`stress_probe`](instruments/stress_probe/) | Covariance dose-response under interaction stress (Participation Ratio) | Closed after Experiment 01's null |

All instruments: standalone packages, offline calibration tests in CI,
deterministic scoring (no LLM judges anywhere in the scoring path),
registry-driven model access (Anthropic, DeepSeek, OpenRouter-routed
Qwen/GLM/MiniMax, HF-routed open checkpoints).

## Reproducing

Each experiment directory contains its preregistration (with dated
amendments), run scripts, frozen analysis, findings with confidence tags,
and a data pointer with sha256 hashes. Instruments carry cost tables;
a full experiment reruns for roughly the price of a coffee.

```bash
pip install numpy pydantic httpx pytest ruff
python -m pytest instruments/permission_bench/tests   # offline calibration
```

## Provenance

These instruments were extracted from a three-year project
(identity-os) whose central hypothesis they ultimately falsified. The
methodology — preregistration, blind amendments, frozen analysis,
adversarial internal review — is the product of that failure. Details in
[`docs/archives/`](docs/archives/) and `CLAUDE.md`.

## Author

Yunpeng Xiong — independent researcher, Netherlands.
