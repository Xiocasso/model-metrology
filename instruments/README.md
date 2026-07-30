# Instruments

One directory per instrument, standalone (own pyproject, own tests, no
cross-instrument imports). Each must contain `PROTOCOL.md`, a calibration test,
and a cost table before it is used in any experiment.

Planned: `stress_probe/` · `contract_bench/` · `drift_monitor/` ·
`judge_triangulation/` (protocol-only for now).
