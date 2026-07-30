# Model Metrology

Black-box behavioral measurement instruments for language models.

## What this is

A portfolio of cheap, reproducible, API-only probes that characterize how a model
behaves — under stress, under runtime constraints, across versions, and as a judge.
No weights access required. Every instrument is calibrated on a known system before
it is pointed at an unknown one.

This project is forked from [identity-os](../identity-os/). That project spent three
years testing the hypothesis "artificial identity is valuable" and — by its own
data — largely falsified it. The instruments built to run that test survived the
hypothesis. This repo is those instruments, cleaned up and pointed outward at
models instead of inward at the engine that built them.

## The instruments

| # | Instrument | Measures | Origin (identity-os) | Status |
|---|---|---|---|---|
| 1 | **Stress-covariance probe** | Post-training imprints on output covariance under graded stress (Participation Ratio dose-response) | `research/phase-transition-v1/`, `experiments/phase_transition/` | Port + Experiment 1 |
| 2 | **Contract-compliance benchmark** | Whether a model respects runtime constraints vs prompt constraints (FalseAllow / ForbiddenBlock) | `research/papers/contract-interface-v6.md` tool-gating harness | Port pending; fix degenerate task sets for 3/4 profiles first |
| 3 | **Drift monitor** | Behavioral drift across model versions / silent API updates (D0–D3 grading, anchor baselines, topological trajectory fingerprint) | `identity_os/engine/drift.py`, `topological_identity.py` | Port pending |
| 4 | **Judge triangulation** | Same-provider bias in LLM-as-judge setups (cross-lineage regrade protocol) | gating-problem-v2 §5.11 | Protocol documented; generalization study pending |
| 5 | **Loop-covariance diagnosis** | Interference direction between concurrent feedback loops in agent scaffolds | gating-problem-v2 §5.12 | Documented; no port needed until a consumer exists |

## Goals

**North star**: become a citable, third-party source of truth for "how does this
model actually behave" — the measurement layer the open-model flood lacks.

**2026 goals (in order)**:
1. **Experiment 1** — stress-signature × open post-training recipes (Tülu 3 / OLMo
   staged checkpoints). Resolves the n=2 confound from phase-transition-v1 and
   doubles as the sensitivity calibration of instrument 1.
2. One workshop-grade paper from Experiment 1 (or an honest negative-result
   writeup that closes the line).
3. Judge-bias paper (instrument 4) rewritten from existing data and submitted.
4. Instruments 2–3 ported and run against ≥5 current models each, results public.

**Non-goals**: building agent products, personality systems, or anything that
requires the identity hypothesis to be true. identity-os remains the archive and
calibration specimen; it is not developed further here.

## Layout

```
instruments/   one directory per instrument; each is standalone
experiments/   numbered experiments; each preregistered before any data is collected
docs/          papers, protocols, findings
```

See `CLAUDE.md` for the development model and collaboration protocol.
