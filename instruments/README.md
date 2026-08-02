# Instruments

One directory per instrument, standalone (own pyproject, own tests, no
cross-instrument imports). Each must contain `PROTOCOL.md`, a calibration test,
and a cost table before it is used in any experiment.

- `permission_bench/` — **flagship**: agent authorization-compliance testing
  (DESIGN.md approved 2026-08-01; implementation in progress)
- `contract_bench/` — calibration-era instrument (Experiment 02 complete:
  v1 degeneracy fixed, enforcement claim killed, coverage-gap lesson feeds
  permission_bench's oracle-coherence invariant)
- `stress_probe/` — closed (Experiment 01 null; line closed per prereg matrix)
- Planned: `drift_monitor/` (permission-compliance version drift) ·
  `judge_triangulation/` (protocol lives in the judge-bias paper reanalysis)
