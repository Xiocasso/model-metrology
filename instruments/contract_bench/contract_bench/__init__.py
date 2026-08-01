"""contract_bench — tool-gating benchmark instrument.

Measures how well an LLM agent's tool choices track a per-profile behavioral
contract under four presentation arms (none / narrative / query-plane /
enforced). Decoupled port of identity-os experiments/minimal_mind
tool-gating benchmark: the identity-os engine is used only once, offline, to
freeze four baseline contracts into fixtures/contracts.json.
"""
