"""
X-0L LLM Client — OpenAI-Compatible Chat Completion

Wrapper around OpenAI-compatible API with:
  - Frozen parameters (model, temperature=0, max_tokens)
  - Retry logic: max 3 retries, exponential backoff, 30s timeout (Q51)
  - Token usage extraction from API metadata (Q14, Q35)
  - Transport error detection vs malformed response (Q8)

API key from environment variable OPENAI_API_KEY (Q52a).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LLMResponse:
    """Structured response from an LLM API call."""
    raw_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    finish_reason: str = ""
    raw_hash: str = ""

    def __post_init__(self):
        if not self.raw_hash:
            self.raw_hash = hashlib.sha256(
                self.raw_text.encode("utf-8")
            ).hexdigest()


class TransportError(Exception):
    """LLM API transport failure (network, timeout, rate limit).

    Per Q8: transport failure ≠ cycle. Can retry transparently.
    """
    pass


class LLMClient:
    """OpenAI-compatible chat completion client.

    Parameters frozen at construction; immutable for session lifetime.
    """

    MAX_RETRIES = 3
    BACKOFF_BASE_S = 1.0
    TIMEOUT_S = 30.0

    def __init__(
        self,
        model: str,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._base_url = base_url or "https://api.openai.com/v1"

        if not self._api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set and no api_key provided"
            )

    def call(
        self,
        system_message: str,
        user_message: str,
    ) -> LLMResponse:
        """Make a chat completion call with retry logic.

        Per Q10: two-message structure (system + user).
        Per Q51: max 3 retries, exponential backoff, 30s timeout.

        Returns LLMResponse on success.
        Raises TransportError if all retries exhausted.
        """
        import httpx

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

        last_error: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES + 1):
            if attempt > 0:
                backoff = self.BACKOFF_BASE_S * (2 ** (attempt - 1))
                time.sleep(backoff)

            try:
                response = httpx.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=self.TIMEOUT_S,
                )

                if response.status_code == 429:
                    # Rate limit — retry
                    last_error = TransportError(
                        f"Rate limited (429), attempt {attempt + 1}"
                    )
                    continue

                if response.status_code >= 500:
                    # Server error — retry
                    last_error = TransportError(
                        f"Server error ({response.status_code}), attempt {attempt + 1}"
                    )
                    continue

                if response.status_code != 200:
                    raise TransportError(
                        f"API error {response.status_code}: {response.text[:500]}"
                    )

                data = response.json()
                choice = data["choices"][0]
                usage = data.get("usage", {})

                return LLMResponse(
                    raw_text=choice["message"]["content"],
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                    model=data.get("model", self.model),
                    finish_reason=choice.get("finish_reason", ""),
                )

            except httpx.TimeoutException as e:
                last_error = TransportError(f"Timeout: {e}")
                continue
            except httpx.ConnectError as e:
                last_error = TransportError(f"Connection error: {e}")
                continue
            except (KeyError, IndexError, json.JSONDecodeError) as e:
                # Malformed API response — still a transport issue
                last_error = TransportError(f"Malformed API response: {e}")
                continue

        # All retries exhausted
        raise TransportError(
            f"All {self.MAX_RETRIES + 1} attempts failed. Last error: {last_error}"
        )

    def frozen_params(self) -> Dict[str, Any]:
        """Return frozen parameters for session metadata."""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "base_url": self._base_url,
        }

    def prompt_hash(self, system_message: str, user_message: str) -> str:
        """Hash of full prompt sent to LLM (per Q43: system + user)."""
        combined = json.dumps(
            {"system": system_message, "user": user_message},
            sort_keys=True, separators=(",", ":"),
        )
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()
