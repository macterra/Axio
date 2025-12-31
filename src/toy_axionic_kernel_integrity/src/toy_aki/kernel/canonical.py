"""
AKI v0.2.2 Canonical Serialization with Cross-Component Agreement.

Implements:
- Separate canonicalizer instances for kernel and actuator
- No shared globals or singletons
- Deterministic serialization with explicit ordering
- Cross-component hash agreement verification

Key invariant: Kernel and actuator canonicalizers must be independent
instances that produce identical output for identical input.
"""

from __future__ import annotations

import json
import hashlib
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum, auto


class CanonicalizationError(Exception):
    """Raised when canonicalization fails."""
    pass


class CanonicalMismatchError(Exception):
    """Raised when kernel and actuator canonical forms disagree."""
    pass


class ComponentRole(Enum):
    """Identifies which component owns a canonicalizer instance."""
    KERNEL = auto()
    ACTUATOR = auto()


@dataclass(frozen=True)
class CanonicalConfig:
    """
    Configuration for canonical serialization.

    Frozen to prevent accidental modification.
    Each canonicalizer instance gets its own copy.
    """
    # String normalization
    unicode_form: str = "NFC"  # NFC, NFD, NFKC, NFKD

    # Float handling (reject ambiguous representations)
    allow_floats: bool = True
    reject_nan: bool = True
    reject_infinity: bool = True

    # Dict handling
    sort_keys: bool = True
    reject_duplicate_keys: bool = True

    # Numeric type handling
    coerce_numeric_strings: bool = False  # If True, "1" and 1 are different

    # Separators (no whitespace)
    item_separator: str = ","
    key_separator: str = ":"


@dataclass
class CanonicalResult:
    """Result of canonicalization."""
    success: bool
    canonical_bytes: bytes
    canonical_hash: str
    error: str | None = None

    # Diagnostics
    input_size: int = 0
    output_size: int = 0
    node_count: int = 0


class IndependentCanonicalizer:
    """
    Independent canonicalizer instance.

    CRITICAL: Each instance maintains its own state with NO shared globals.
    - No module-level caches
    - No shared registries
    - No shared configuration objects
    - All functions are pure and parameterized

    The kernel and actuator each get their own instance.
    """

    # Class-level assertion: No class variables that could be shared
    # Each instance has only instance variables

    def __init__(
        self,
        role: ComponentRole,
        config: CanonicalConfig | None = None,
    ):
        """
        Create an independent canonicalizer.

        Args:
            role: KERNEL or ACTUATOR (for diagnostics/assertions)
            config: Configuration (a fresh copy is made)
        """
        self._role = role
        # Make our own copy of config to ensure independence
        if config is None:
            self._config = CanonicalConfig()
        else:
            # Create a new frozen instance with same values
            self._config = CanonicalConfig(
                unicode_form=config.unicode_form,
                allow_floats=config.allow_floats,
                reject_nan=config.reject_nan,
                reject_infinity=config.reject_infinity,
                sort_keys=config.sort_keys,
                reject_duplicate_keys=config.reject_duplicate_keys,
                coerce_numeric_strings=config.coerce_numeric_strings,
                item_separator=config.item_separator,
                key_separator=config.key_separator,
            )

        # Instance-level counters (not shared)
        self._canonicalization_count = 0
        self._node_count = 0

    @property
    def role(self) -> ComponentRole:
        return self._role

    @property
    def canonicalization_count(self) -> int:
        return self._canonicalization_count

    def canonicalize(self, data: Any) -> CanonicalResult:
        """
        Convert data to canonical bytes and compute hash.

        Returns CanonicalResult with canonical_bytes and canonical_hash.
        Raises CanonicalizationError on failure (or returns success=False).
        """
        self._canonicalization_count += 1
        self._node_count = 0

        try:
            # Pre-process: normalize and validate
            normalized = self._normalize_recursive(data)

            # Serialize to canonical JSON
            canonical_str = json.dumps(
                normalized,
                sort_keys=self._config.sort_keys,
                separators=(
                    self._config.item_separator,
                    self._config.key_separator,
                ),
                ensure_ascii=False,
                default=self._json_default,
            )

            # Encode to bytes (UTF-8, canonical)
            canonical_bytes = canonical_str.encode("utf-8")

            # Compute hash
            canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()

            return CanonicalResult(
                success=True,
                canonical_bytes=canonical_bytes,
                canonical_hash=canonical_hash,
                input_size=len(str(data)),
                output_size=len(canonical_bytes),
                node_count=self._node_count,
            )

        except CanonicalizationError as e:
            return CanonicalResult(
                success=False,
                canonical_bytes=b"",
                canonical_hash="",
                error=str(e),
            )
        except Exception as e:
            return CanonicalResult(
                success=False,
                canonical_bytes=b"",
                canonical_hash="",
                error=f"Unexpected error: {type(e).__name__}",
            )

    def _normalize_recursive(self, data: Any, depth: int = 0) -> Any:
        """
        Recursively normalize data for canonical representation.

        This is a PURE function - no side effects except node counting.
        """
        self._node_count += 1

        if data is None:
            return None

        if isinstance(data, bool):
            # Bool before int (bool is subclass of int in Python)
            return data

        if isinstance(data, int):
            return data

        if isinstance(data, float):
            if not self._config.allow_floats:
                raise CanonicalizationError("Floats not allowed")
            if self._config.reject_nan and data != data:  # NaN check
                raise CanonicalizationError("NaN not allowed")
            if self._config.reject_infinity and abs(data) == float("inf"):
                raise CanonicalizationError("Infinity not allowed")
            # Normalize float representation
            return float(data)

        if isinstance(data, str):
            # Unicode normalization
            normalized = unicodedata.normalize(
                self._config.unicode_form,
                data
            )
            return normalized

        if isinstance(data, bytes):
            # Encode bytes as base64 string
            import base64
            return {"__bytes__": base64.b64encode(data).decode("ascii")}

        if isinstance(data, list):
            return [
                self._normalize_recursive(item, depth + 1)
                for item in data
            ]

        if isinstance(data, dict):
            # Check for duplicate keys if raw parsing allowed them
            # (In Python, dict construction already handles this, but
            # if we received data from JSON parsing with duplicate keys,
            # the last value wins. We can't detect this after the fact,
            # but we document that behavior.)

            result = {}
            for key, value in data.items():
                if not isinstance(key, str):
                    raise CanonicalizationError(
                        f"Dict keys must be strings, got {type(key).__name__}"
                    )
                # Normalize key
                norm_key = unicodedata.normalize(
                    self._config.unicode_form,
                    key
                )
                result[norm_key] = self._normalize_recursive(value, depth + 1)

            return result

        # Unsupported type
        raise CanonicalizationError(
            f"Unsupported type for canonicalization: {type(data).__name__}"
        )

    def _json_default(self, obj: Any) -> Any:
        """Handle non-JSON types during serialization."""
        raise CanonicalizationError(
            f"Cannot serialize type: {type(obj).__name__}"
        )


@dataclass(frozen=True)
class CanonicalPayload:
    """
    v0.2.2: Immutable canonical payload for kernel-to-actuator handoff.

    This is what crosses the boundary - canonical bytes only, no mutable objects.
    """
    canonical_bytes: bytes
    canonical_hash: str

    # Action metadata (extracted before canonicalization)
    action_type: str
    action_id: str

    def verify_hash(self) -> bool:
        """Verify the hash matches the bytes."""
        computed = hashlib.sha256(self.canonical_bytes).hexdigest()
        return computed == self.canonical_hash


def create_kernel_canonicalizer(
    config: CanonicalConfig | None = None
) -> IndependentCanonicalizer:
    """
    Factory for kernel-side canonicalizer.

    Creates a fresh, independent instance.
    """
    return IndependentCanonicalizer(ComponentRole.KERNEL, config)


def create_actuator_canonicalizer(
    config: CanonicalConfig | None = None
) -> IndependentCanonicalizer:
    """
    Factory for actuator-side canonicalizer.

    Creates a fresh, independent instance.
    """
    return IndependentCanonicalizer(ComponentRole.ACTUATOR, config)


def verify_canonical_agreement(
    kernel_result: CanonicalResult,
    actuator_result: CanonicalResult,
) -> tuple[bool, str | None]:
    """
    v0.2.2: Verify that kernel and actuator produce identical canonical forms.

    Returns (agreement, error_message).
    """
    if not kernel_result.success:
        return (False, f"Kernel canonicalization failed: {kernel_result.error}")

    if not actuator_result.success:
        return (False, f"Actuator canonicalization failed: {actuator_result.error}")

    # Check byte-for-byte agreement
    if kernel_result.canonical_bytes != actuator_result.canonical_bytes:
        return (False, "Canonical bytes mismatch")

    # Check hash agreement (should be redundant but belt-and-suspenders)
    if kernel_result.canonical_hash != actuator_result.canonical_hash:
        return (False, "Canonical hash mismatch")

    return (True, None)


# ============================================================
# Assertions for no-shared-globals (used in tests)
# ============================================================

def assert_no_shared_state(
    c1: IndependentCanonicalizer,
    c2: IndependentCanonicalizer,
) -> None:
    """
    Assert that two canonicalizers share no state.

    Raises AssertionError if any shared state is detected.
    """
    # Different instances
    assert c1 is not c2, "Same instance"

    # Different config objects (even if equal values)
    assert c1._config is not c2._config, "Shared config object"

    # Different counters
    c1._canonicalization_count = 999
    assert c2._canonicalization_count != 999 or c2._canonicalization_count == 0, \
        "Shared counter state"
    c1._canonicalization_count = 0  # Reset
