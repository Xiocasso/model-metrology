"""Provider clients for the tool-gating benchmark.

Pattern copied from model-metrology instruments/stress_probe/stress_probe/
providers.py, simplified: this benchmark parses a free-text JSON decision
from the completion (matching the original identity-os harness) rather than
forcing structured output, because the A3 arm needs a plain multi-turn
revision exchange.

Two implementations behind one interface:
- AnthropicClient: /v1/messages.
- OpenAICompatClient: any /v1/chat/completions endpoint.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

import httpx

from contract_bench.registry import ModelSpec

logger = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


@dataclass
class ChatResult:
    text: str
    model_key: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class ChatClient:
    """Base class — subclasses implement complete()."""

    spec: ModelSpec

    def complete(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.5,
        max_tokens: int = 250,
    ) -> ChatResult:
        """messages: [{"role": "user"|"assistant", "content": str}, ...]"""
        raise NotImplementedError


class AnthropicClient(ChatClient):
    def __init__(self, spec: ModelSpec, api_key: str | None = None):
        self.spec = spec
        self.api_key = api_key or os.environ[spec.api_key_env]
        self._client = httpx.Client(timeout=90.0)

    def complete(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.5,
        max_tokens: int = 250,
    ) -> ChatResult:
        payload = {
            "model": self.spec.model,
            "system": system_prompt,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
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
        text = "".join(
            b.get("text", "") for b in data["content"] if b["type"] == "text"
        )
        return ChatResult(
            text=text,
            model_key=self.spec.key,
            input_tokens=data["usage"]["input_tokens"],
            output_tokens=data["usage"]["output_tokens"],
            latency_ms=latency_ms,
        )


class OpenAICompatClient(ChatClient):
    def __init__(self, spec: ModelSpec, api_key: str | None = None):
        self.spec = spec
        self.api_key = api_key or os.environ[spec.api_key_env]
        self._client = httpx.Client(timeout=90.0)

    def complete(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.5,
        max_tokens: int = 250,
    ) -> ChatResult:
        payload = {
            "model": self.spec.model,
            "messages": [{"role": "system", "content": system_prompt}, *messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
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
        usage = data.get("usage") or {}
        return ChatResult(
            text=data["choices"][0]["message"]["content"],
            model_key=self.spec.key,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            latency_ms=latency_ms,
        )


def get_client(spec: ModelSpec) -> ChatClient:
    if spec.provider == "anthropic":
        return AnthropicClient(spec)
    if spec.provider == "openai-compat":
        return OpenAICompatClient(spec)
    raise ValueError(f"Unknown provider: {spec.provider}")
