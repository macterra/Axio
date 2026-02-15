"""
AxionAgent — Anthropic LLM Client

Wrapper around the Anthropic SDK for multi-turn conversation.
Adapted from profiling/x0l/harness/src/llm_client.py.
"""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from typing import List, Dict


class TransportError(Exception):
    """Unrecoverable LLM transport failure."""
    pass


@dataclass
class LLMResponse:
    """Response from an LLM call."""
    raw_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    finish_reason: str
    raw_hash: str

    @staticmethod
    def compute_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


class AnthropicClient:
    """Multi-turn Anthropic Messages API client with retry."""

    MAX_RETRIES = 3
    BACKOFF_BASE_S = 1.0

    def __init__(
        self,
        model: str,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        api_key: str | None = None,
    ):
        from anthropic import Anthropic

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
        )

    def call(
        self,
        system_message: str,
        messages: List[Dict[str, str]],
    ) -> LLMResponse:
        """Call the Anthropic Messages API with retry.

        Args:
            system_message: System prompt.
            messages: List of {"role": "user"|"assistant", "content": "..."}.

        Returns:
            LLMResponse with raw text and token usage.

        Raises:
            TransportError on unrecoverable failure.
        """
        from anthropic import APIError, APITimeoutError, RateLimitError

        last_error: Exception | None = None

        for attempt in range(self.MAX_RETRIES + 1):
            if attempt > 0:
                time.sleep(self.BACKOFF_BASE_S * (2 ** (attempt - 1)))

            try:
                response = self._client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=system_message,
                    messages=messages,
                )

                raw_text = response.content[0].text
                return LLMResponse(
                    raw_text=raw_text,
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                    model=response.model,
                    finish_reason=response.stop_reason or "",
                    raw_hash=LLMResponse.compute_hash(raw_text),
                )

            except RateLimitError:
                last_error = TransportError(f"Rate limited, attempt {attempt + 1}")
                continue
            except APITimeoutError as e:
                last_error = TransportError(f"Timeout: {e}")
                continue
            except APIError as e:
                if e.status_code and e.status_code >= 500:
                    last_error = TransportError(f"Server error: {e}")
                    continue
                raise TransportError(f"API error: {e}")
            except Exception as e:
                raise TransportError(f"Unexpected error: {e}")

        raise last_error or TransportError("All retry attempts failed")
