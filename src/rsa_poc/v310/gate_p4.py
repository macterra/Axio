"""Gate P4: Prompt Capacity Invariance for v3.1.

Enforces fixed-window precedent injection with zero token jitter.

Binding requirements:
- Total prompt token count MUST remain invariant across steps/episodes/runs
- Precedent buffer = [precedent_tokens] + [PAD × (N - len(precedent_tokens))]
- If precedent exceeds N: INVALID_RUN / BUFFER_OVERFLOW
- If token_jitter != 0: INVALID_RUN / SHADOW_PERSISTENCE
"""

import math
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional, Set, Tuple, Dict, Any, List
from enum import Enum

from .tokenizer import V310Tokenizer, PAD_STR, get_tokenizer


class GateP4Violation(Enum):
    """Types of Gate P4 violations."""
    BUFFER_OVERFLOW = "BUFFER_OVERFLOW"
    SHADOW_PERSISTENCE = "SHADOW_PERSISTENCE"
    PAD_UNSTABLE = "PAD_UNSTABLE"


@dataclass
class GateP4Config:
    """Configuration for Gate P4 enforcement.

    N is determined by calibration pass and frozen.
    """
    buffer_size_n: int  # Fixed buffer size in tokens
    pad_str: str = PAD_STR
    tolerance: int = 0  # Token jitter tolerance (binding: must be 0)

    def to_dict(self) -> dict:
        return {
            "buffer_size_n": self.buffer_size_n,
            "pad_str": self.pad_str,
            "tolerance": self.tolerance,
        }


@dataclass
class PrecedentInjection:
    """Result of precedent buffer preparation."""
    content: str  # Full buffer content (precedent + padding)
    precedent_tokens: int  # Tokens used by precedent
    padding_tokens: int  # Tokens used by padding
    total_tokens: int  # Must equal buffer_size_n
    utilization: float  # precedent_tokens / buffer_size_n
    precedent_hash: str  # SHA256 of precedent content

    def to_dict(self) -> dict:
        return {
            "precedent_tokens": self.precedent_tokens,
            "padding_tokens": self.padding_tokens,
            "total_tokens": self.total_tokens,
            "utilization": self.utilization,
            "precedent_hash": self.precedent_hash,
        }


@dataclass
class TokenJitterRecord:
    """Record of token counts for jitter detection."""
    step: int
    episode_id: str
    prompt_tokens: int
    precedent_buffer_tokens: int

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "episode_id": self.episode_id,
            "prompt_tokens": self.prompt_tokens,
            "precedent_buffer_tokens": self.precedent_buffer_tokens,
        }


def ceil_to_32(x: float) -> int:
    """Round up to nearest multiple of 32.

    Used for buffer size calculation.
    """
    return int(math.ceil(x / 32) * 32)


class GateP4:
    """Gate P4 enforcement for prompt capacity invariance.

    Ensures:
    1. Precedent buffer has fixed size N tokens
    2. Total prompt token count is invariant
    3. No shadow persistence through context growth
    """

    def __init__(
        self,
        config: GateP4Config,
        tokenizer: V310Tokenizer = None,
    ):
        """Initialize Gate P4.

        Args:
            config: Gate P4 configuration with buffer size N
            tokenizer: Tokenizer for token counting
        """
        self.config = config
        self.tokenizer = tokenizer or get_tokenizer()

        # Validate PAD stability
        is_stable, pad_count, msg = self.tokenizer.validate_pad_stability(config.pad_str)
        if not is_stable:
            raise ValueError(f"INVALID_RUN / PAD_UNSTABLE: {msg}")

        self._pad_token_count = pad_count

        # Token count tracking for jitter detection
        self._baseline_prompt_tokens: Optional[int] = None
        self._jitter_records: List[TokenJitterRecord] = []

    def prepare_precedent_buffer(
        self,
        precedent_content: str,
    ) -> Tuple[PrecedentInjection, Optional[GateP4Violation]]:
        """Prepare precedent injection buffer with padding.

        Args:
            precedent_content: Serialized precedent record

        Returns:
            Tuple of (PrecedentInjection, violation if any)
        """
        precedent_tokens = self.tokenizer.count_tokens(precedent_content)

        # Check for overflow
        if precedent_tokens > self.config.buffer_size_n:
            return None, GateP4Violation.BUFFER_OVERFLOW

        # Calculate padding needed
        tokens_to_pad = self.config.buffer_size_n - precedent_tokens

        # Generate padding
        # PAD_STR produces _pad_token_count tokens each
        pad_units_needed = tokens_to_pad // self._pad_token_count
        padding = self.config.pad_str * pad_units_needed

        # Verify padding produces correct token count
        actual_padding_tokens = self.tokenizer.count_tokens(padding)

        # Handle rounding — may need adjustment
        while actual_padding_tokens < tokens_to_pad:
            padding += self.config.pad_str
            actual_padding_tokens = self.tokenizer.count_tokens(padding)

        # Trim if we overshot (shouldn't happen with stable PAD)
        while actual_padding_tokens > tokens_to_pad and len(padding) > len(self.config.pad_str):
            padding = padding[:-len(self.config.pad_str)]
            actual_padding_tokens = self.tokenizer.count_tokens(padding)

        # Build full buffer
        full_buffer = precedent_content + padding
        total_tokens = self.tokenizer.count_tokens(full_buffer)

        # Compute hash
        precedent_hash = hashlib.sha256(precedent_content.encode()).hexdigest()[:16]

        injection = PrecedentInjection(
            content=full_buffer,
            precedent_tokens=precedent_tokens,
            padding_tokens=actual_padding_tokens,
            total_tokens=total_tokens,
            utilization=precedent_tokens / self.config.buffer_size_n if self.config.buffer_size_n > 0 else 0,
            precedent_hash=precedent_hash,
        )

        return injection, None

    def check_jitter(
        self,
        prompt: str,
        step: int,
        episode_id: str,
    ) -> Tuple[bool, Optional[GateP4Violation], int]:
        """Check for token jitter in prompt.

        Gate P4 requires token_jitter == 0.

        Args:
            prompt: Full prompt being sent to LLM
            step: Current step index
            episode_id: Current episode ID

        Returns:
            Tuple of (passed, violation if any, jitter amount)
        """
        prompt_tokens = self.tokenizer.count_tokens(prompt)

        # Record for telemetry
        record = TokenJitterRecord(
            step=step,
            episode_id=episode_id,
            prompt_tokens=prompt_tokens,
            precedent_buffer_tokens=self.config.buffer_size_n,
        )
        self._jitter_records.append(record)

        # Set baseline on first check
        if self._baseline_prompt_tokens is None:
            self._baseline_prompt_tokens = prompt_tokens
            return True, None, 0

        # Compute jitter
        jitter = abs(prompt_tokens - self._baseline_prompt_tokens)

        if jitter > self.config.tolerance:
            return False, GateP4Violation.SHADOW_PERSISTENCE, jitter

        return True, None, jitter

    def reset_baseline(self):
        """Reset baseline for new run (not episode).

        Called once at start of experimental run.
        """
        self._baseline_prompt_tokens = None
        self._jitter_records = []

    def get_jitter_records(self) -> List[TokenJitterRecord]:
        """Get all jitter records for telemetry."""
        return self._jitter_records.copy()

    @staticmethod
    def calibrate_buffer_size(
        observed_precedent_tokens: List[int],
        floor: int = 512,
    ) -> int:
        """Calculate buffer size N from calibration observations.

        Formula: N = max(floor, ceil_to_32(1.25 × max(observed)))

        Args:
            observed_precedent_tokens: Token counts from calibration pass
            floor: Minimum buffer size

        Returns:
            Buffer size N (frozen after this)
        """
        if not observed_precedent_tokens:
            return floor

        max_observed = max(observed_precedent_tokens)
        scaled = 1.25 * max_observed
        rounded = ceil_to_32(scaled)

        return max(floor, rounded)


def serialize_precedent_record(
    authorized_violations: Set[str],
    required_preservations: Set[str],
    conflict_attribution: Set[Tuple[str, str]],
    artifact_digest: str,
    step_index: int,
) -> str:
    """Serialize precedent record for injection.

    Produces canonical JSON for consistent tokenization.

    Args:
        authorized_violations: AV set
        required_preservations: RP set
        conflict_attribution: (belief, pref) pairs
        artifact_digest: Artifact hash
        step_index: Step number

    Returns:
        Canonical JSON string
    """
    record = {
        "AV": sorted(list(authorized_violations)),
        "RP": sorted(list(required_preservations)),
        "CA": sorted([list(t) for t in conflict_attribution]),
        "digest": artifact_digest,
        "step": step_index,
    }

    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def create_empty_precedent_buffer(config: GateP4Config, tokenizer: V310Tokenizer) -> str:
    """Create buffer filled with PAD only (for ablated runs).

    Args:
        config: Gate P4 config with buffer size
        tokenizer: Tokenizer for verification

    Returns:
        PAD-filled buffer of exactly N tokens
    """
    pad_count = tokenizer.count_tokens(config.pad_str)
    pad_units = config.buffer_size_n // pad_count

    buffer = config.pad_str * pad_units
    actual_tokens = tokenizer.count_tokens(buffer)

    # Adjust if needed
    while actual_tokens < config.buffer_size_n:
        buffer += config.pad_str
        actual_tokens = tokenizer.count_tokens(buffer)

    return buffer


if __name__ == "__main__":
    # Self-test
    print("Gate P4 Self-Test")
    print("=" * 50)

    tokenizer = get_tokenizer()

    # Create config with example buffer size
    config = GateP4Config(buffer_size_n=512)

    try:
        gate = GateP4(config, tokenizer)
        print(f"Gate P4 initialized with N={config.buffer_size_n}")

        # Test precedent serialization
        test_precedent = serialize_precedent_record(
            authorized_violations={"P_NO_DEFECT"},
            required_preservations={"P_NO_LIE", "P_PREFER_COOPERATION"},
            conflict_attribution={("B_COOPERATION_MATTERS", "P_NO_DEFECT")},
            artifact_digest="abc123def456",
            step_index=5,
        )
        print(f"\nTest precedent ({tokenizer.count_tokens(test_precedent)} tokens):")
        print(f"  {test_precedent[:80]}...")

        # Test buffer preparation
        injection, violation = gate.prepare_precedent_buffer(test_precedent)
        if violation:
            print(f"\nViolation: {violation}")
        else:
            print(f"\nPrecedent buffer prepared:")
            print(f"  Precedent tokens: {injection.precedent_tokens}")
            print(f"  Padding tokens: {injection.padding_tokens}")
            print(f"  Total tokens: {injection.total_tokens}")
            print(f"  Utilization: {injection.utilization:.1%}")
            print(f"  Hash: {injection.precedent_hash}")

        # Test calibration
        observations = [45, 52, 48, 61, 55]
        N = GateP4.calibrate_buffer_size(observations)
        print(f"\nCalibration test:")
        print(f"  Observations: {observations}")
        print(f"  Calculated N: {N}")

    except Exception as e:
        print(f"Gate P4 initialization failed: {e}")
