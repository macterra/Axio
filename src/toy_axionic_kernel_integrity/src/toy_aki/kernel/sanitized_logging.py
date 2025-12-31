"""
Sanitized Logging System for v0.2.1.

Implements the logging discipline required by v0.2.1:
- External logs sanitized to fixed enum codes
- No stack traces, object reprs, or exception text
- Internal logs isolated and off by default
- Whitelist-based field enforcement

A8 attack tests for leakage even when debug is off.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable


class RejectionCode(Enum):
    """
    Fixed set of allowed external rejection codes.

    These are the ONLY strings that may appear in external logs.
    Any attempt to emit other strings is a potential leak.
    """
    # Parse errors
    INADMISSIBLE_PARSE_ERROR = auto()
    INADMISSIBLE_INVALID_STRUCTURE = auto()
    INADMISSIBLE_INVALID_TYPE = auto()

    # Budget errors
    INADMISSIBLE_BUDGET_EXCEEDED = auto()
    INADMISSIBLE_TIME_EXCEEDED = auto()
    INADMISSIBLE_DEPTH_EXCEEDED = auto()
    INADMISSIBLE_SIZE_EXCEEDED = auto()

    # Authority/delegation errors
    INADMISSIBLE_DELEGATION_MARKER = auto()
    INADMISSIBLE_AUTHORITY_DETECTED = auto()
    INADMISSIBLE_WRAPPING_DETECTED = auto()

    # Binding/hash errors
    INADMISSIBLE_BINDING_INVALID = auto()
    INADMISSIBLE_HASH_MISMATCH = auto()
    INADMISSIBLE_NONCANONICAL_ACTION = auto()

    # ACV errors
    INADMISSIBLE_ACV_INVALID = auto()
    INADMISSIBLE_CHAIN_BROKEN = auto()
    INADMISSIBLE_ORIGIN_MISSING = auto()

    # TOCTOU/mutation errors
    INADMISSIBLE_MUTATION_DETECTED = auto()
    INADMISSIBLE_REFERENCE_ALIASING = auto()

    # Generic fallback
    INADMISSIBLE_UNSPECIFIED = auto()


# Whitelist of allowed external log fields
ALLOWED_EXTERNAL_FIELDS = frozenset({
    "timestamp_ms",
    "rejection_code",
    "stage",
    "accepted",
    "admissible",
    # Minimal identifiers (not content)
    "trial_id",
    "attack_type",
    "variant",
    "environment",
    "seed",
})


@dataclass
class SanitizedLogEntry:
    """A single sanitized log entry for external use."""
    timestamp_ms: int
    rejection_code: RejectionCode | None
    stage: str
    accepted: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with only allowed fields."""
        return {
            "timestamp_ms": self.timestamp_ms,
            "rejection_code": self.rejection_code.name if self.rejection_code else None,
            "stage": self.stage,
            "accepted": self.accepted,
        }


class LogLeakError(Exception):
    """Raised when a log entry attempts to include forbidden fields."""
    pass


def validate_external_log(entry: dict[str, Any]) -> None:
    """
    Validate that a log entry contains only allowed fields.

    Raises LogLeakError if forbidden fields detected.
    """
    forbidden = set(entry.keys()) - ALLOWED_EXTERNAL_FIELDS
    if forbidden:
        raise LogLeakError(
            f"External log contains forbidden fields: {forbidden}"
        )


class SanitizedLogger:
    """
    Logger that enforces external log sanitization.

    External logs:
    - Use only RejectionCode enum values
    - Contain only whitelisted fields
    - Never include exception details, stack traces, or reprs

    Internal logs:
    - Are kept separate
    - Are disabled by default
    - Never escape to external artifacts
    """

    def __init__(
        self,
        internal_enabled: bool = False,
        strict_mode: bool = True,
    ):
        """
        Initialize logger.

        Args:
            internal_enabled: Whether internal debug logs are enabled
            strict_mode: Whether to raise on forbidden field attempts
        """
        self._external_log: list[SanitizedLogEntry] = []
        self._internal_log: list[dict[str, Any]] = []
        self._internal_enabled = internal_enabled
        self._strict_mode = strict_mode
        self._leak_attempts: list[dict[str, Any]] = []  # Track A8 attempts

    @property
    def internal_enabled(self) -> bool:
        return self._internal_enabled

    def set_internal_enabled(self, enabled: bool) -> None:
        """Enable or disable internal logging."""
        self._internal_enabled = enabled

    def log_external(
        self,
        timestamp_ms: int,
        rejection_code: RejectionCode | None,
        stage: str,
        accepted: bool,
    ) -> None:
        """
        Log to external log with sanitization.

        Only allowed fields, only enum codes.
        """
        entry = SanitizedLogEntry(
            timestamp_ms=timestamp_ms,
            rejection_code=rejection_code,
            stage=stage,
            accepted=accepted,
        )
        self._external_log.append(entry)

    def log_rejection(
        self,
        timestamp_ms: int,
        code: RejectionCode,
        stage: str,
    ) -> None:
        """Convenience method for logging rejections."""
        self.log_external(timestamp_ms, code, stage, accepted=False)

    def log_acceptance(self, timestamp_ms: int, stage: str) -> None:
        """Convenience method for logging acceptances."""
        self.log_external(timestamp_ms, None, stage, accepted=True)

    def log_internal(self, **kwargs: Any) -> None:
        """
        Log to internal log (debug only).

        This log is:
        - Disabled by default
        - Never exported to external artifacts
        - Only for local debugging
        """
        if self._internal_enabled:
            self._internal_log.append(kwargs)

    def attempt_forbidden_log(
        self,
        source: str,
        **forbidden_fields: Any,
    ) -> None:
        """
        Track an attempt to log forbidden content (for A8 detection).

        In strict mode, raises LogLeakError.
        Always records the attempt for later analysis.
        """
        # Record attempt (sanitized - just the field names, not values)
        self._leak_attempts.append({
            "source": source,
            "forbidden_fields": list(forbidden_fields.keys()),
        })

        if self._strict_mode:
            raise LogLeakError(
                f"Attempted to log forbidden fields from {source}"
            )

    def get_external_log(self) -> list[dict[str, Any]]:
        """Get external log entries as dicts."""
        return [e.to_dict() for e in self._external_log]

    def get_internal_log(self) -> list[dict[str, Any]]:
        """
        Get internal log (ONLY for internal debugging).

        This should NEVER be included in external artifacts.
        """
        return list(self._internal_log) if self._internal_enabled else []

    def get_leak_attempts(self) -> list[dict[str, Any]]:
        """Get record of leak attempts (for A8 testing)."""
        return list(self._leak_attempts)

    def clear(self) -> None:
        """Clear all logs."""
        self._external_log = []
        self._internal_log = []
        self._leak_attempts = []

    def get_diagnostics(self) -> dict[str, Any]:
        """Get logging diagnostics."""
        return {
            "external_entries": len(self._external_log),
            "internal_enabled": self._internal_enabled,
            "internal_entries": len(self._internal_log) if self._internal_enabled else 0,
            "leak_attempts": len(self._leak_attempts),
        }


# Global sanitized logger
_global_logger: SanitizedLogger | None = None


def get_sanitized_logger() -> SanitizedLogger:
    """Get the global sanitized logger."""
    global _global_logger
    if _global_logger is None:
        _global_logger = SanitizedLogger()
    return _global_logger


def set_sanitized_logger(logger: SanitizedLogger) -> None:
    """Set the global sanitized logger."""
    global _global_logger
    _global_logger = logger


def sanitize_exception(exc: Exception) -> RejectionCode:
    """
    Map an exception to a sanitized rejection code.

    This is the ONLY way exceptions should be communicated externally.
    """
    from toy_aki.kernel.budget import (
        TimeBudgetExceeded,
        NodeBudgetExceeded,
        DepthBudgetExceeded,
        ByteBudgetExceeded,
        WorkBudgetExceeded,
    )
    from toy_aki.kernel.recomposition import (
        ProposalParseError,
        ActionReconstructionError,
        DelegationAuthorityError,
    )

    exc_type = type(exc)

    mapping = {
        TimeBudgetExceeded: RejectionCode.INADMISSIBLE_TIME_EXCEEDED,
        NodeBudgetExceeded: RejectionCode.INADMISSIBLE_BUDGET_EXCEEDED,
        DepthBudgetExceeded: RejectionCode.INADMISSIBLE_DEPTH_EXCEEDED,
        ByteBudgetExceeded: RejectionCode.INADMISSIBLE_SIZE_EXCEEDED,
        WorkBudgetExceeded: RejectionCode.INADMISSIBLE_BUDGET_EXCEEDED,
        ProposalParseError: RejectionCode.INADMISSIBLE_PARSE_ERROR,
        ActionReconstructionError: RejectionCode.INADMISSIBLE_INVALID_STRUCTURE,
        DelegationAuthorityError: RejectionCode.INADMISSIBLE_DELEGATION_MARKER,
    }

    return mapping.get(exc_type, RejectionCode.INADMISSIBLE_UNSPECIFIED)
