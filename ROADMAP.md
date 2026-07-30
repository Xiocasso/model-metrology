# Roadmap

## Phase 1 — Instrument 1 validation (weeks 1–4)

- [x] Port stress-covariance probe from identity-os → `instruments/stress_probe/`
      (registry-driven models, resumable runner, synthetic-covariance
      calibration tests — 13/13 passing, ruff clean) — 2026-07-30
- [x] `experiments/01-stress-signature/preregistration.md` — H1 stage
      emergence, H2 recipe>identity (Tülu 3 staged checkpoints), H3 Claude
      family consistency, H4 coupling mechanism — 2026-07-30
- [ ] Cost estimate ($25–30, cap $50) → user approval → pilot → run
- [ ] `findings.md` — either the pipeline-signature claim stands, or the line
      closes cleanly. Both outcomes are deliverables.

**Exit criterion**: a defensible answer to "is the covariance signature a
training-pipeline property or model idiosyncrasy?"

## Phase 2 — First publications (weeks 4–10)

- [ ] Judge-bias paper (instrument 4): rewrite from existing identity-os data,
      drop pseudo-replicated statistics, submit to an LLM-evaluation workshop
- [ ] If Experiment 1 positive: stress-signature paper draft

## Phase 3 — Portfolio expansion (weeks 8–16, order by Phase 1 outcome)

- [ ] Port instrument 2 (contract-compliance benchmark); fix degenerate task
      generation for 3/4 profiles; run against ≥5 current models; publish table
- [ ] Port instrument 3 (drift monitor); stand up a weekly cross-provider
      version-drift probe with a public results page
- [ ] Judge-bias generalization study (open judge models: is same-family bias
      universal?)

## Standing rules

- Money: every paid run pre-approved with a $ figure. Running total kept in
  handoffs.
- Any instrument that fails its calibration test does not get pointed at
  external models until fixed.
- Quarterly review: kill or double down per instrument; no zombie lines.
