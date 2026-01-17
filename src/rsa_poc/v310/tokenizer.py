"""Tokenizer infrastructure for v3.1 Gate P4.

Provides model-specific tokenization with PAD stability validation.

Binding requirements:
- Use LLM's native tokenizer (or closest approximation)
- PAD_STR must be token-stable (no boundary effects)
- Token count must be exact (no approximations)
"""

import os
import hashlib
from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum


class TokenizerProvider(Enum):
    """Supported tokenizer providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


@dataclass(frozen=True)
class TokenizerConfig:
    """Configuration for v3.1 tokenizer.

    Frozen and logged in run header for reproducibility.
    """
    provider: str
    model_id: str
    tokenizer_id: str
    tokenizer_version: str
    pad_str: str
    pad_token_count: int  # Tokens per PAD_STR unit

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model_id": self.model_id,
            "tokenizer_id": self.tokenizer_id,
            "tokenizer_version": self.tokenizer_version,
            "pad_str": self.pad_str,
            "pad_token_count": self.pad_token_count,
        }


# Default PAD string — chosen for token stability
# Using " X" (space + X) which:
# - Tokenizes to exactly 1 token in cl100k_base
# - Has stable boundaries (no merging with any prefix)
# - Scales linearly when repeated
# - Carries no semantic information
PAD_STR = " X"


class V310Tokenizer:
    """Model-specific tokenizer for Gate P4 enforcement.

    Wraps tiktoken for Anthropic/OpenAI models with:
    - Exact token counting
    - PAD stability validation
    - Boundary effect detection
    """

    def __init__(self, provider: str, model_id: str):
        """Initialize tokenizer for specific provider/model.

        Args:
            provider: LLM provider (anthropic, openai)
            model_id: Model identifier
        """
        self.provider = provider
        self.model_id = model_id
        self._encoder = None
        self._tokenizer_id = None
        self._tokenizer_version = None
        self._pad_validated = False
        self._pad_token_count = None

        self._init_encoder()

    def _init_encoder(self):
        """Initialize tiktoken encoder for the model."""
        import tiktoken

        self._tokenizer_version = tiktoken.__version__

        # Map providers/models to tiktoken encodings
        # Anthropic Claude uses cl100k_base (GPT-4 compatible) for approximation
        # This is the closest available encoding
        if self.provider == "anthropic":
            # Anthropic doesn't publish tokenizer, use cl100k_base as approximation
            # Per binding answer: lock to official library and pin version
            self._tokenizer_id = "cl100k_base"
            self._encoder = tiktoken.get_encoding("cl100k_base")
        elif self.provider == "openai":
            # OpenAI: use model-specific encoding
            try:
                self._encoder = tiktoken.encoding_for_model(self.model_id)
                self._tokenizer_id = self._encoder.name
            except KeyError:
                # Fallback for unknown models
                self._tokenizer_id = "cl100k_base"
                self._encoder = tiktoken.get_encoding("cl100k_base")
        else:
            # Default fallback
            self._tokenizer_id = "cl100k_base"
            self._encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Input text

        Returns:
            Exact token count
        """
        return len(self._encoder.encode(text))

    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs.

        Args:
            text: Input text

        Returns:
            List of token IDs
        """
        return self._encoder.encode(text)

    def decode(self, tokens: List[int]) -> str:
        """Decode token IDs to text.

        Args:
            tokens: List of token IDs

        Returns:
            Decoded text
        """
        return self._encoder.decode(tokens)

    def validate_pad_stability(self, pad_str: str = PAD_STR) -> Tuple[bool, int, str]:
        """Validate PAD string stability.

        Binding requirements:
        1. tokenize(PAD_STR) yields fixed token sequence
        2. tokenize(X + PAD_STR) doesn't change X tokenization
        3. tokenize(PAD_STR * k) scales linearly

        Args:
            pad_str: PAD string to validate

        Returns:
            Tuple of (is_stable, tokens_per_pad, error_message)
        """
        # Test 1: Fixed token sequence
        tokens_1 = self.encode(pad_str)
        tokens_2 = self.encode(pad_str)
        if tokens_1 != tokens_2:
            return False, 0, "PAD tokenization not deterministic"

        base_count = len(tokens_1)
        if base_count == 0:
            return False, 0, "PAD produces no tokens"

        # Test 2: Boundary stability — prefix should not change
        test_prefix = "The agent must choose action "
        prefix_tokens = self.encode(test_prefix)
        combined_tokens = self.encode(test_prefix + pad_str)

        # Check that prefix tokens are preserved
        if combined_tokens[:len(prefix_tokens)] != prefix_tokens:
            return False, 0, "PAD causes boundary token merging with prefix"

        # Test 3: Linear scaling
        for k in [2, 5, 10, 20]:
            repeated_tokens = self.encode(pad_str * k)
            expected = base_count * k
            if len(repeated_tokens) != expected:
                return False, 0, f"PAD repetition not linear: {k}x gave {len(repeated_tokens)} tokens, expected {expected}"

        self._pad_validated = True
        self._pad_token_count = base_count
        return True, base_count, "PAD is stable"

    def get_config(self, pad_str: str = PAD_STR) -> TokenizerConfig:
        """Get tokenizer configuration for run header.

        Args:
            pad_str: PAD string being used

        Returns:
            TokenizerConfig for logging
        """
        if not self._pad_validated:
            is_stable, count, msg = self.validate_pad_stability(pad_str)
            if not is_stable:
                raise ValueError(f"PAD validation failed: {msg}")

        return TokenizerConfig(
            provider=self.provider,
            model_id=self.model_id,
            tokenizer_id=self._tokenizer_id,
            tokenizer_version=self._tokenizer_version,
            pad_str=pad_str,
            pad_token_count=self._pad_token_count,
        )


def get_tokenizer(provider: str = None, model_id: str = None) -> V310Tokenizer:
    """Get tokenizer for current LLM configuration.

    Args:
        provider: Override LLM_PROVIDER env var
        model_id: Override LLM_MODEL env var

    Returns:
        Configured V310Tokenizer
    """
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "anthropic")
    if model_id is None:
        model_id = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")

    return V310Tokenizer(provider, model_id)


def run_pad_self_test(tokenizer: V310Tokenizer = None) -> Tuple[bool, str]:
    """Run mandatory PAD stability self-test.

    This MUST pass before any v3.1 runs.

    Args:
        tokenizer: Tokenizer to test (uses default if None)

    Returns:
        Tuple of (passed, message)
    """
    if tokenizer is None:
        tokenizer = get_tokenizer()

    is_stable, token_count, msg = tokenizer.validate_pad_stability(PAD_STR)

    if not is_stable:
        return False, f"INVALID_RUN / PAD_UNSTABLE: {msg}"

    return True, f"PAD self-test passed: '{PAD_STR}' = {token_count} token(s)"


if __name__ == "__main__":
    # Self-test when run directly
    print("V310 Tokenizer Self-Test")
    print("=" * 50)

    tokenizer = get_tokenizer()
    print(f"Provider: {tokenizer.provider}")
    print(f"Model: {tokenizer.model_id}")
    print(f"Tokenizer: {tokenizer._tokenizer_id} v{tokenizer._tokenizer_version}")

    passed, msg = run_pad_self_test(tokenizer)
    print(f"\nPAD Self-Test: {'PASSED' if passed else 'FAILED'}")
    print(f"  {msg}")

    if passed:
        config = tokenizer.get_config()
        print(f"\nTokenizer Config:")
        for k, v in config.to_dict().items():
            print(f"  {k}: {v}")
