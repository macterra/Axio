"""
Hardened Parser and Canonicalization for v0.2.1.

Implements:
- Bounded recursion
- Bounded size
- Type-safe parsing
- No unsafe reflection
- Deterministic serialization
- Canonical hashing

All parse errors result in clean inadmissibility.
"""

from __future__ import annotations

import copy
import json
import hashlib
from dataclasses import dataclass, field
from typing import Any, TypeVar, Callable
from enum import Enum, auto

from toy_aki.kernel.budget import (
    charge,
    charge_bytes,
    charge_node,
    charge_work,
    OperationType,
    BudgetTracker,
    get_budget_tracker,
    DepthBudgetExceeded,
    NodeBudgetExceeded,
    ByteBudgetExceeded,
)
from toy_aki.kernel.sanitized_logging import RejectionCode


class ParseError(Exception):
    """Raised when parsing fails."""
    pass


class DepthLimitExceeded(ParseError):
    """Maximum recursion depth exceeded."""
    pass


class SizeLimitExceeded(ParseError):
    """Maximum size exceeded."""
    pass


class TypeValidationError(ParseError):
    """Type validation failed."""
    pass


class CanonicalizationError(ParseError):
    """Canonicalization failed."""
    pass


class UnsafeContentError(ParseError):
    """Unsafe content detected (e.g., pickle, code)."""
    pass


@dataclass
class ParseConfig:
    """Configuration for hardened parsing."""
    max_depth: int = 50
    max_nodes: int = 1000
    max_bytes: int = 65536  # 64KB
    max_string_length: int = 10000
    max_array_length: int = 1000
    allowed_types: frozenset[type] = frozenset({
        dict, list, str, int, float, bool, type(None)
    })
    # Forbidden key patterns
    forbidden_keys: frozenset[str] = frozenset({
        "__class__",
        "__dict__",
        "__reduce__",
        "__getstate__",
        "__setstate__",
        "__module__",
        "__import__",
        "eval",
        "exec",
        "compile",
    })


@dataclass
class ParseResult:
    """Result of hardened parsing."""
    success: bool
    data: Any
    rejection_code: RejectionCode | None = None
    error_message: str | None = None
    nodes_visited: int = 0
    max_depth_reached: int = 0
    bytes_processed: int = 0


class HardenedParser:
    """
    Parser with bounded recursion, size limits, and type safety.

    All parsing operations charge the budget tracker.
    """

    def __init__(self, config: ParseConfig | None = None):
        self._config = config or ParseConfig()
        self._nodes_visited = 0
        self._max_depth_reached = 0
        self._bytes_processed = 0

    def parse(
        self,
        data: Any,
        tracker: BudgetTracker | None = None,
    ) -> ParseResult:
        """
        Parse and validate input data.

        Returns a deep copy with all validation checks applied.
        """
        self._nodes_visited = 0
        self._max_depth_reached = 0
        self._bytes_processed = 0

        tracker = tracker or get_budget_tracker()

        try:
            # Charge for parse operation
            charge(OperationType.PARSE)

            # Recursive parse with bounds
            result = self._parse_recursive(data, depth=0, tracker=tracker)

            return ParseResult(
                success=True,
                data=result,
                nodes_visited=self._nodes_visited,
                max_depth_reached=self._max_depth_reached,
                bytes_processed=self._bytes_processed,
            )

        except DepthLimitExceeded as e:
            return ParseResult(
                success=False,
                data=None,
                rejection_code=RejectionCode.INADMISSIBLE_DEPTH_EXCEEDED,
                error_message="Depth limit exceeded",
                nodes_visited=self._nodes_visited,
                max_depth_reached=self._max_depth_reached,
            )
        except SizeLimitExceeded as e:
            return ParseResult(
                success=False,
                data=None,
                rejection_code=RejectionCode.INADMISSIBLE_SIZE_EXCEEDED,
                error_message="Size limit exceeded",
                nodes_visited=self._nodes_visited,
                bytes_processed=self._bytes_processed,
            )
        except TypeValidationError as e:
            return ParseResult(
                success=False,
                data=None,
                rejection_code=RejectionCode.INADMISSIBLE_INVALID_TYPE,
                error_message="Type validation failed",
            )
        except UnsafeContentError as e:
            return ParseResult(
                success=False,
                data=None,
                rejection_code=RejectionCode.INADMISSIBLE_AUTHORITY_DETECTED,
                error_message="Unsafe content detected",
            )
        except (DepthBudgetExceeded, NodeBudgetExceeded, ByteBudgetExceeded) as e:
            return ParseResult(
                success=False,
                data=None,
                rejection_code=RejectionCode.INADMISSIBLE_BUDGET_EXCEEDED,
                error_message="Budget exceeded during parsing",
            )
        except Exception as e:
            # Catch-all for any other errors
            return ParseResult(
                success=False,
                data=None,
                rejection_code=RejectionCode.INADMISSIBLE_PARSE_ERROR,
                error_message="Parse error",
            )

    def _parse_recursive(
        self,
        data: Any,
        depth: int,
        tracker: BudgetTracker,
    ) -> Any:
        """Recursively parse with bounds checking."""
        # Depth check
        if depth > self._config.max_depth:
            raise DepthLimitExceeded()

        self._max_depth_reached = max(self._max_depth_reached, depth)

        # Node count check
        self._nodes_visited += 1
        charge_node()

        if self._nodes_visited > self._config.max_nodes:
            raise SizeLimitExceeded("Too many nodes")

        # Type check
        data_type = type(data)
        if data_type not in self._config.allowed_types:
            raise TypeValidationError(f"Disallowed type: {data_type.__name__}")

        # Handle by type
        if data is None:
            return None

        elif isinstance(data, bool):
            return data

        elif isinstance(data, (int, float)):
            # Check for special float values
            if isinstance(data, float):
                if data != data:  # NaN check
                    raise TypeValidationError("NaN not allowed")
                if abs(data) == float("inf"):
                    raise TypeValidationError("Infinity not allowed")
            return data

        elif isinstance(data, str):
            # Size check
            if len(data) > self._config.max_string_length:
                raise SizeLimitExceeded("String too long")

            self._bytes_processed += len(data.encode("utf-8"))
            charge_bytes(len(data.encode("utf-8")))

            # Check for forbidden patterns
            for forbidden in self._config.forbidden_keys:
                if forbidden in data:
                    raise UnsafeContentError(f"Forbidden pattern in string")

            # Return copy
            return str(data)

        elif isinstance(data, list):
            # Length check
            if len(data) > self._config.max_array_length:
                raise SizeLimitExceeded("Array too long")

            # Recursive parse of elements
            with tracker.depth_context():
                return [
                    self._parse_recursive(item, depth + 1, tracker)
                    for item in data
                ]

        elif isinstance(data, dict):
            # Length check
            if len(data) > self._config.max_array_length:
                raise SizeLimitExceeded("Dict too large")

            # Check keys
            result = {}
            with tracker.depth_context():
                for key, value in data.items():
                    # Keys must be strings
                    if not isinstance(key, str):
                        raise TypeValidationError("Dict keys must be strings")

                    # Check forbidden keys
                    if key in self._config.forbidden_keys:
                        raise UnsafeContentError(f"Forbidden key")

                    # Check for dunder keys
                    if key.startswith("__") and key.endswith("__"):
                        raise UnsafeContentError(f"Dunder key not allowed")

                    # Recursive parse
                    result[str(key)] = self._parse_recursive(
                        value, depth + 1, tracker
                    )

            return result

        else:
            raise TypeValidationError(f"Unexpected type: {data_type.__name__}")


class CanonicalSerializer:
    """
    Deterministic serialization for canonical hashing.

    Ensures:
    - Kernel and actuator hash identical representations
    - No language-dependent ordering
    - No implicit defaults
    - No ambiguous encodings
    """

    def __init__(self):
        pass

    def canonicalize(self, data: Any) -> str:
        """
        Convert data to canonical JSON string.

        - Keys are sorted
        - No whitespace
        - Deterministic float representation
        - UTF-8 encoding
        """
        charge(OperationType.CANONICALIZE)
        charge_work(1)

        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=self._default_serializer,
        )

    def canonical_hash(self, data: Any) -> str:
        """
        Compute canonical hash of data.

        Uses SHA-256 of canonical JSON representation.
        """
        charge(OperationType.HASH)

        canonical = self.canonicalize(data)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _default_serializer(self, obj: Any) -> Any:
        """Handle non-JSON types."""
        if isinstance(obj, bytes):
            # Encode bytes as base64
            import base64
            return {"__bytes__": base64.b64encode(obj).decode("ascii")}
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        else:
            raise TypeError(f"Cannot serialize {type(obj).__name__}")

    def verify_canonical_equality(
        self,
        data_a: Any,
        data_b: Any,
    ) -> tuple[bool, str | None]:
        """
        Verify two data structures are canonically equal.

        Returns (equal, difference_location).
        """
        canonical_a = self.canonicalize(data_a)
        canonical_b = self.canonicalize(data_b)

        if canonical_a == canonical_b:
            return (True, None)

        # Find first difference
        for i, (a, b) in enumerate(zip(canonical_a, canonical_b)):
            if a != b:
                return (False, f"position {i}")

        if len(canonical_a) != len(canonical_b):
            return (False, f"length mismatch: {len(canonical_a)} vs {len(canonical_b)}")

        return (False, "unknown")


class AtomicDeepCopy:
    """
    Deep copy with atomicity guarantees.

    - No shared mutable state with source
    - No references retained across copy
    - Immutable result
    """

    def __init__(self, parser: HardenedParser | None = None):
        self._parser = parser or HardenedParser()

    def copy(
        self,
        data: Any,
        tracker: BudgetTracker | None = None,
    ) -> tuple[Any, bool]:
        """
        Create an atomic deep copy.

        Returns (copy, success).
        The copy shares no references with the original.
        """
        tracker = tracker or get_budget_tracker()
        charge(OperationType.DEEP_COPY, self._estimate_size(data))

        # Parse (validates and creates new objects)
        result = self._parser.parse(data, tracker)

        if not result.success:
            return (None, False)

        # Additional copy for safety
        return (self._deep_copy_simple(result.data), True)

    def _estimate_size(self, data: Any) -> int:
        """Estimate size of data in bytes."""
        try:
            return len(json.dumps(data, default=str))
        except Exception:
            return 1000  # Default estimate

    def _deep_copy_simple(self, data: Any) -> Any:
        """Simple recursive deep copy."""
        if data is None or isinstance(data, (bool, int, float, str)):
            return data
        elif isinstance(data, list):
            return [self._deep_copy_simple(item) for item in data]
        elif isinstance(data, dict):
            return {k: self._deep_copy_simple(v) for k, v in data.items()}
        else:
            return data

    def verify_no_shared_refs(
        self,
        original: Any,
        copied: Any,
    ) -> bool:
        """Verify copy shares no mutable references with original."""
        original_ids = self._collect_mutable_ids(original)
        copied_ids = self._collect_mutable_ids(copied)

        # No overlap allowed
        return len(original_ids & copied_ids) == 0

    def _collect_mutable_ids(
        self,
        data: Any,
        seen: set[int] | None = None,
    ) -> set[int]:
        """Collect ids of all mutable objects."""
        if seen is None:
            seen = set()

        if isinstance(data, (list, dict)):
            seen.add(id(data))

            if isinstance(data, list):
                for item in data:
                    self._collect_mutable_ids(item, seen)
            elif isinstance(data, dict):
                for value in data.values():
                    self._collect_mutable_ids(value, seen)

        return seen


# Global instances
_parser = HardenedParser()
_serializer = CanonicalSerializer()
_copier = AtomicDeepCopy()


def hardened_parse(data: Any) -> ParseResult:
    """Parse data using the hardened parser."""
    return _parser.parse(data)


def canonical_hash(data: Any) -> str:
    """Compute canonical hash."""
    return _serializer.canonical_hash(data)


def canonical_json(data: Any) -> str:
    """Get canonical JSON representation."""
    return _serializer.canonicalize(data)


def atomic_copy(data: Any) -> tuple[Any, bool]:
    """Create atomic deep copy."""
    return _copier.copy(data)
