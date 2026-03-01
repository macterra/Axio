"""
AxionAgent — LLM Client (Multi-Provider)

Supports Anthropic (Messages API) and OpenAI-compatible providers (Kimi, etc.).
Both clients share the same LLMResponse type and .call() signature.
Native tool use supported for providers that advertise it.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional


class TransportError(Exception):
    """Unrecoverable LLM transport failure."""
    pass


@dataclass
class ToolCall:
    """Provider-normalized tool call."""
    id: str
    name: str
    arguments: Dict[str, Any]


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
    tool_calls: List[ToolCall] = field(default_factory=list)

    @staticmethod
    def compute_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Anthropic client
# ---------------------------------------------------------------------------

class AnthropicClient:
    """Multi-turn Anthropic Messages API client with retry."""

    MAX_RETRIES = 3
    BACKOFF_BASE_S = 1.0

    def __init__(
        self,
        model: str,
        max_tokens: int = 16384,
        temperature: float = 0.0,
        api_key: str | None = None,
    ):
        from anthropic import Anthropic

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._client = Anthropic(api_key=key)

    def call(
        self,
        system_message: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        """Call the Anthropic Messages API with retry."""
        from anthropic import APIError, APITimeoutError, RateLimitError

        last_error: Exception | None = None

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_message,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        for attempt in range(self.MAX_RETRIES + 1):
            if attempt > 0:
                time.sleep(self.BACKOFF_BASE_S * (2 ** (attempt - 1)))

            try:
                with self._client.messages.stream(**kwargs) as stream:
                    response = stream.get_final_message()

                # Parse content blocks: text + tool_use
                text_parts: List[str] = []
                tool_calls: List[ToolCall] = []
                for block in response.content:
                    if block.type == "text":
                        text_parts.append(block.text)
                    elif block.type == "tool_use":
                        tool_calls.append(ToolCall(
                            id=block.id,
                            name=block.name,
                            arguments=block.input,
                        ))

                raw_text = "\n".join(text_parts) if text_parts else ""

                # Hash includes tool calls for replay determinism
                hash_input = raw_text
                if tool_calls:
                    tc_data = json.dumps(
                        [{"id": tc.id, "name": tc.name, "args": tc.arguments} for tc in tool_calls],
                        sort_keys=True,
                    )
                    hash_input += tc_data

                return LLMResponse(
                    raw_text=raw_text,
                    prompt_tokens=response.usage.input_tokens,
                    completion_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                    model=response.model,
                    finish_reason=response.stop_reason or "",
                    raw_hash=LLMResponse.compute_hash(hash_input),
                    tool_calls=tool_calls,
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


# ---------------------------------------------------------------------------
# OpenAI-compatible client (Kimi, DeepSeek, etc.)
# ---------------------------------------------------------------------------

def _convert_messages_to_openai(
    system_message: str,
    messages: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Convert Anthropic-style messages to OpenAI chat format.

    Handles multimodal content blocks (images), tool_use blocks in assistant
    messages, and tool_result blocks in user messages.
    """
    openai_msgs: List[Dict[str, Any]] = [
        {"role": "system", "content": system_message},
    ]

    for msg in messages:
        role = msg["role"]
        content = msg.get("content")

        # Pass through OpenAI-native tool result messages
        if role == "tool":
            openai_msgs.append(msg)
            continue

        # Pass through assistant messages with tool_calls (already OpenAI format)
        if role == "assistant" and "tool_calls" in msg:
            openai_msgs.append(msg)
            continue

        if isinstance(content, str):
            openai_msgs.append({"role": role, "content": content})
        elif isinstance(content, list):
            # Check for Anthropic tool_result content blocks
            tool_results = [b for b in content if b.get("type") == "tool_result"]
            if tool_results:
                for tr in tool_results:
                    openai_msgs.append({
                        "role": "tool",
                        "tool_call_id": tr["tool_use_id"],
                        "content": tr.get("content", ""),
                    })
            else:
                # Convert Anthropic content blocks to OpenAI format
                parts: List[Dict[str, Any]] = []
                for block in content:
                    if block.get("type") == "text":
                        parts.append({"type": "text", "text": block["text"]})
                    elif block.get("type") == "image":
                        source = block.get("source", {})
                        media_type = source.get("media_type", "image/png")
                        data = source.get("data", "")
                        parts.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:{media_type};base64,{data}"},
                        })
                if parts:
                    openai_msgs.append({"role": role, "content": parts})
        elif content is not None:
            openai_msgs.append({"role": role, "content": str(content)})
        else:
            openai_msgs.append({"role": role, "content": ""})

    return openai_msgs


class OpenAICompatibleClient:
    """Multi-turn OpenAI-compatible API client with retry."""

    MAX_RETRIES = 3
    BACKOFF_BASE_S = 1.0

    def __init__(
        self,
        model: str,
        max_tokens: int = 16384,
        temperature: float = 0.0,
        api_key: str | None = None,
        base_url: str = "https://api.moonshot.ai/v1",
        api_key_env: str = "MOONSHOT_API_KEY",
    ):
        from openai import OpenAI

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.base_url = base_url

        key = api_key or os.environ.get(api_key_env, "")
        self._client = OpenAI(api_key=key, base_url=base_url)

    def call(
        self,
        system_message: str,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
        """Call the OpenAI-compatible chat completions API with retry."""
        from openai import APIError, APITimeoutError, RateLimitError

        openai_messages = _convert_messages_to_openai(system_message, messages)
        last_error: Exception | None = None

        for attempt in range(self.MAX_RETRIES + 1):
            if attempt > 0:
                time.sleep(self.BACKOFF_BASE_S * (2 ** (attempt - 1)))

            try:
                if tools:
                    # Non-streaming for tool calls (avoids complex delta accumulation)
                    response = self._client.chat.completions.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        messages=openai_messages,
                        tools=tools,
                    )
                    message = response.choices[0].message
                    raw_text = message.content or ""
                    finish_reason = response.choices[0].finish_reason or ""
                    model_name = response.model or self.model

                    tool_calls: List[ToolCall] = []
                    if message.tool_calls:
                        for tc in message.tool_calls:
                            tool_calls.append(ToolCall(
                                id=tc.id,
                                name=tc.function.name,
                                arguments=json.loads(tc.function.arguments),
                            ))

                    usage = response.usage
                    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                    completion_tokens = getattr(usage, "completion_tokens", 0) or 0

                    if not completion_tokens and (raw_text or tool_calls):
                        completion_tokens = len(raw_text) // 4 + sum(
                            len(json.dumps(tc.arguments)) // 4 for tc in tool_calls
                        )
                    if not prompt_tokens:
                        total_chars = len(system_message) + sum(
                            len(str(m.get("content", ""))) for m in messages
                        )
                        prompt_tokens = total_chars // 4

                    hash_input = raw_text
                    if tool_calls:
                        tc_data = json.dumps(
                            [{"id": tc.id, "name": tc.name, "args": tc.arguments} for tc in tool_calls],
                            sort_keys=True,
                        )
                        hash_input += tc_data

                    return LLMResponse(
                        raw_text=raw_text,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=prompt_tokens + completion_tokens,
                        model=model_name,
                        finish_reason=finish_reason,
                        raw_hash=LLMResponse.compute_hash(hash_input),
                        tool_calls=tool_calls,
                    )
                else:
                    # Streaming for text-only (existing path)
                    stream = self._client.chat.completions.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        messages=openai_messages,
                        stream=True,
                    )

                    chunks: List[str] = []
                    finish_reason = ""
                    model_name = self.model
                    chunk = None
                    for chunk in stream:
                        delta = chunk.choices[0].delta if chunk.choices else None
                        if delta and delta.content:
                            chunks.append(delta.content)
                        if chunk.choices and chunk.choices[0].finish_reason:
                            finish_reason = chunk.choices[0].finish_reason
                        if chunk.model:
                            model_name = chunk.model

                    raw_text = "".join(chunks)

                    usage = getattr(chunk, "usage", None) if chunk else None
                    prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
                    completion_tokens = getattr(usage, "completion_tokens", 0) or 0

                    if not completion_tokens and raw_text:
                        completion_tokens = len(raw_text) // 4
                    if not prompt_tokens:
                        total_chars = len(system_message) + sum(
                            len(str(m.get("content", ""))) for m in messages
                        )
                        prompt_tokens = total_chars // 4

                    return LLMResponse(
                        raw_text=raw_text,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=prompt_tokens + completion_tokens,
                        model=model_name,
                        finish_reason=finish_reason,
                        raw_hash=LLMResponse.compute_hash(raw_text),
                    )

            except RateLimitError:
                last_error = TransportError(f"Rate limited, attempt {attempt + 1}")
                continue
            except APITimeoutError as e:
                last_error = TransportError(f"Timeout: {e}")
                continue
            except APIError as e:
                if hasattr(e, "status_code") and e.status_code and e.status_code >= 500:
                    last_error = TransportError(f"Server error: {e}")
                    continue
                raise TransportError(f"API error: {e}")
            except Exception as e:
                raise TransportError(f"Unexpected error: {e}")

        raise last_error or TransportError("All retry attempts failed")


# ---------------------------------------------------------------------------
# Model registry and factory
# ---------------------------------------------------------------------------

MODEL_REGISTRY: Dict[str, Dict[str, str]] = {
    "sonnet": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "supports_tools": "true",
    },
    "opus": {
        "provider": "anthropic",
        "model": "claude-opus-4-20250514",
        "supports_tools": "true",
    },
    "haiku": {
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "supports_tools": "true",
    },
    "kimi": {
        "provider": "openai",
        "model": "kimi-k2.5",
        "base_url": "https://api.moonshot.ai/v1",
        "api_key_env": "MOONSHOT_API_KEY",
        "temperature": "1.0",
        "supports_tools": "false",
    },
}


def create_client(
    provider: str,
    model: str,
    max_tokens: int = 16384,
    **kwargs: Any,
) -> AnthropicClient | OpenAICompatibleClient:
    """Create an LLM client for the given provider."""
    temperature = float(kwargs.get("temperature", 0.0))

    if provider == "anthropic":
        return AnthropicClient(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            api_key=kwargs.get("api_key"),
        )
    else:
        return OpenAICompatibleClient(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            api_key=kwargs.get("api_key"),
            base_url=kwargs.get("base_url", "https://api.moonshot.ai/v1"),
            api_key_env=kwargs.get("api_key_env", "MOONSHOT_API_KEY"),
        )
