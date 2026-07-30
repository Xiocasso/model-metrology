"""Provider clients. Two implementations behind one interface:

- OpenAICompatClient: any /v1/chat/completions endpoint (HF router, OpenAI,
  Moonshot, Together, local vLLM). JSON output via response_format json_object.
- AnthropicClient: tool-use forcing for structured output.

Origin: identity-os experiments/phase_transition/inference.py, generalized to
be driven by ModelSpec instead of hardcoded model constants.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass

import httpx
from pydantic import ValidationError

from stress_probe.registry import ModelSpec
from stress_probe.schema import DECISION_JSON_SCHEMA, StructuredDecision

logger = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


@dataclass
class TrialResult:
    decision: StructuredDecision
    model_key: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    raw_response: str  # audit only; never used in analysis


class ProbeClient:
    """Base class — subclasses implement run_trial()."""

    spec: ModelSpec

    def run_trial(
        self,
        system_prompt: str,
        conversation: list[dict[str, str]],
        *,
        temperature: float = 0.0,
        max_tokens: int = 200,
    ) -> TrialResult:
        raise NotImplementedError


class OpenAICompatClient(ProbeClient):
    def __init__(self, spec: ModelSpec, api_key: str | None = None):
        self.spec = spec
        self.api_key = api_key or os.environ[spec.api_key_env]
        self._client = httpx.Client(timeout=90.0)

    def run_trial(
        self,
        system_prompt: str,
        conversation: list[dict[str, str]],
        *,
        temperature: float = 0.0,
        max_tokens: int = 200,
    ) -> TrialResult:
        # Base checkpoints have no system role in their training distribution:
        # fold the system prompt into the first user turn.
        if not self.spec.uses_system_role and conversation:
            first = conversation[0]
            merged = {
                "role": first["role"],
                "content": f"{system_prompt}\n\n{first['content']}",
            }
            messages = [merged, *conversation[1:]]
        else:
            messages = [{"role": "system", "content": system_prompt}, *conversation]

        payload = {
            "model": self.spec.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        t0 = time.perf_counter()
        response = self._client.post(
            self.spec.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)

        if response.status_code != 200:
            raise RuntimeError(
                f"{self.spec.key} error {response.status_code}: {response.text[:500]}"
            )

        data = response.json()
        raw = data["choices"][0]["message"]["content"]
        decision = parse_decision(raw)

        usage = data.get("usage") or {}
        return TrialResult(
            decision=decision,
            model_key=self.spec.key,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            latency_ms=latency_ms,
            raw_response=raw,
        )


class AnthropicClient(ProbeClient):
    def __init__(self, spec: ModelSpec, api_key: str | None = None):
        self.spec = spec
        self.api_key = api_key or os.environ[spec.api_key_env]
        self._client = httpx.Client(timeout=90.0)

    def run_trial(
        self,
        system_prompt: str,
        conversation: list[dict[str, str]],
        *,
        temperature: float = 0.0,
        max_tokens: int = 200,
    ) -> TrialResult:
        tool = {
            "name": "emit_decision",
            "description": "Emit the structured decision for this scenario.",
            "input_schema": DECISION_JSON_SCHEMA,
        }
        payload = {
            "model": self.spec.model,
            "system": system_prompt,
            "messages": conversation,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "tools": [tool],
            "tool_choice": {"type": "tool", "name": "emit_decision"},
        }

        t0 = time.perf_counter()
        response = self._client.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)

        if response.status_code != 200:
            raise RuntimeError(
                f"{self.spec.key} error {response.status_code}: {response.text[:500]}"
            )

        data = response.json()
        tool_use = next((b for b in data["content"] if b["type"] == "tool_use"), None)
        if tool_use is None:
            raise RuntimeError(f"No tool_use block in response: {str(data)[:300]}")

        decision = StructuredDecision(**tool_use["input"])
        return TrialResult(
            decision=decision,
            model_key=self.spec.key,
            input_tokens=data["usage"]["input_tokens"],
            output_tokens=data["usage"]["output_tokens"],
            latency_ms=latency_ms,
            raw_response=json.dumps(tool_use["input"]),
        )


def parse_decision(raw: str) -> StructuredDecision:
    """Strict parse first, then extract the first {...} block (base-model noise)."""
    raw = raw.strip()
    try:
        return StructuredDecision(**json.loads(raw))
    except (json.JSONDecodeError, ValidationError):
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        candidate = raw[start : end + 1]
        try:
            return StructuredDecision(**json.loads(candidate))
        except (json.JSONDecodeError, ValidationError) as e:
            raise RuntimeError(
                f"Could not parse decision from raw response: {raw[:300]}"
            ) from e

    raise RuntimeError(f"No JSON object found in response: {raw[:300]}")


def get_client(spec: ModelSpec) -> ProbeClient:
    if spec.provider == "anthropic":
        return AnthropicClient(spec)
    if spec.provider == "openai-compat":
        return OpenAICompatClient(spec)
    raise ValueError(f"Unknown provider: {spec.provider}")
