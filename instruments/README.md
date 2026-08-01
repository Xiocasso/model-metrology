# Instruments

One directory per instrument, standalone (own pyproject, own tests, no
cross-instrument imports). Each must contain `PROTOCOL.md`, a calibration test,
and a cost table before it is used in any experiment.

Active: `stress_probe/` (Experiment 01 complete) · `contract_bench/`
(ported 2026-08-01, offline-verified, awaiting first cross-model run).
Planned: `drift_monitor/` · `judge_triangulation/` (protocol lives in the
judge-bias paper reanalysis for now).
