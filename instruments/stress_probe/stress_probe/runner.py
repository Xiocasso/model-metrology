"""Resumable async trial runner.

Origin: identity-os experiments/phase_transition/collect.py, generalized:
model dispatch goes through the registry, and the client factory is injectable
so tests can run the full pipeline against a fake client.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from stress_probe.conversation import (
    ARCHETYPES,
    PROTOCOL_VERSION,
    STRESS_LEVELS,
    TRIALS_PER_CELL,
    Scenario,
    build_conversation,
)
from stress_probe.providers import ProbeClient, TrialResult, get_client
from stress_probe.registry import REGISTRY, ModelSpec

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrialSpec:
    trial_id: str
    scenario_id: str
    model_key: str
    archetype: str
    stress_level: int
    trial_index: int


def make_trial_id(
    scenario_id: str, model_key: str, archetype: str, stress: int, trial_idx: int
) -> str:
    return f"{scenario_id}__{model_key}__{archetype}__s{stress:02d}__t{trial_idx:02d}"


def generate_specs(
    scenario_id: str,
    model_keys: list[str],
    archetypes: list[str] | None = None,
    stress_levels: list[int] | None = None,
    trials_per_cell: int = TRIALS_PER_CELL,
) -> list[TrialSpec]:
    archetypes = archetypes or list(ARCHETYPES.keys())
    stress_levels = stress_levels or STRESS_LEVELS
    specs: list[TrialSpec] = []
    for key in model_keys:
        if key not in REGISTRY:
            raise KeyError(f"Model key not in registry: {key}")
        for archetype in archetypes:
            for stress in stress_levels:
                for t_idx in range(trials_per_cell):
                    specs.append(
                        TrialSpec(
                            trial_id=make_trial_id(
                                scenario_id, key, archetype, stress, t_idx
                            ),
                            scenario_id=scenario_id,
                            model_key=key,
                            archetype=archetype,
                            stress_level=stress,
                            trial_index=t_idx,
                        )
                    )
    return specs


def _trial_record(
    spec: TrialSpec,
    result: TrialResult | None,
    error: str | None,
    attempts: int,
) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "trial_id": spec.trial_id,
        "scenario_id": spec.scenario_id,
        "model_key": spec.model_key,
        "archetype": spec.archetype,
        "stress_level": spec.stress_level,
        "trial_index": spec.trial_index,
        "decision": result.decision.model_dump() if result else None,
        "input_tokens": result.input_tokens if result else None,
        "output_tokens": result.output_tokens if result else None,
        "latency_ms": result.latency_ms if result else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempts": attempts,
        "error": error,
    }


def load_completed_ids(output_path: Path) -> set[str]:
    """Trial ids with a successful decision already on disk (resume support)."""
    if not output_path.exists():
        return set()
    done: set[str] = set()
    with output_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("decision") is not None:
                done.add(rec["trial_id"])
    return done


async def _run_trial(
    spec: TrialSpec,
    scenario: Scenario,
    client_factory: Callable[[ModelSpec], ProbeClient],
    semaphore: asyncio.Semaphore,
    temperature: float,
    max_retries: int = 5,
) -> dict[str, Any]:
    system_prompt, conversation = build_conversation(
        spec.archetype, spec.stress_level, spec.trial_index, scenario
    )
    async with semaphore:
        last_error: str | None = None
        for attempt in range(1, max_retries + 1):
            try:
                client = client_factory(REGISTRY[spec.model_key])
                result = await asyncio.to_thread(
                    client.run_trial,
                    system_prompt=system_prompt,
                    conversation=conversation,
                    temperature=temperature,
                    max_tokens=200,
                )
                return _trial_record(spec, result, None, attempt)
            except Exception as e:  # noqa: BLE001 — record and retry
                last_error = f"{type(e).__name__}: {str(e)[:300]}"
                if attempt < max_retries:
                    # 503s are on-demand cold starts (featherless): wait longer
                    cold_start = "503" in last_error
                    delay = min(3 * 2**attempt, 60) if cold_start else 2**attempt
                    await asyncio.sleep(delay)
        return _trial_record(spec, None, last_error, max_retries)


async def collect(
    specs: list[TrialSpec],
    scenario: Scenario,
    output_path: Path,
    *,
    concurrency: int = 10,
    temperature: float = 0.0,
    resume: bool = True,
    client_factory: Callable[[ModelSpec], ProbeClient] = get_client,
) -> dict[str, int]:
    """Run all pending trials, appending JSONL records as they complete.

    Returns {"completed": n, "failed": n, "skipped": n}.
    """
    completed_ids = load_completed_ids(output_path) if resume else set()
    pending = [s for s in specs if s.trial_id not in completed_ids]
    logger.info(
        "collect: %d specs, %d already done, %d pending -> %s",
        len(specs), len(completed_ids), len(pending), output_path,
    )
    if not pending:
        return {"completed": 0, "failed": 0, "skipped": len(specs)}

    output_path.parent.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(concurrency)
    ok = failed = 0
    start = time.perf_counter()

    with output_path.open("a", encoding="utf-8") as fout:
        tasks = [
            _run_trial(s, scenario, client_factory, semaphore, temperature)
            for s in pending
        ]
        for i, fut in enumerate(asyncio.as_completed(tasks), start=1):
            record = await fut
            fout.write(json.dumps(record, ensure_ascii=False) + "\n")
            fout.flush()
            if record["decision"] is None:
                failed += 1
            else:
                ok += 1
            if i % 25 == 0 or i == len(pending):
                rate = i / max(time.perf_counter() - start, 1e-3)
                logger.info(
                    "[%d/%d] ok=%d fail=%d rate=%.1f/s eta=%ds",
                    i, len(pending), ok, failed, rate,
                    int((len(pending) - i) / max(rate, 1e-3)),
                )

    return {"completed": ok, "failed": failed, "skipped": len(completed_ids)}


def load_cells(
    output_path: Path,
    model_key: str,
    scenario_id: str,
) -> dict[int, list[list[float]]]:
    """Group successful trials into {stress_level: [continuous vectors]}."""
    cells: dict[int, list[list[float]]] = {}
    with output_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (
                rec.get("model_key") != model_key
                or rec.get("scenario_id") != scenario_id
                or rec.get("decision") is None
            ):
                continue
            d = rec["decision"]
            vec = [
                d["confidence"] / 100.0,
                d["risk_estimate"] / 100.0,
                d["commitment"] / 100.0,
                d["urgency"] / 100.0,
            ]
            cells.setdefault(rec["stress_level"], []).append(vec)
    return cells
