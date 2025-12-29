"""Custom exceptions for toy_pseudo_axion."""

from typing import Any, Optional


class ToyPseudoAxionError(Exception):
    """Base exception for all toy_pseudo_axion errors."""
    pass


class SchemaValidationError(ToyPseudoAxionError):
    """Raised when JSON schema validation fails."""

    def __init__(self, message: str, schema_name: str, errors: Optional[list] = None):
        super().__init__(message)
        self.schema_name = schema_name
        self.errors = errors or []


class InvariantViolationError(ToyPseudoAxionError):
    """Raised when a kernel invariant is violated."""

    def __init__(self, invariant: str, message: str, severity: str = "fatal", data: Optional[Any] = None):
        super().__init__(f"[{invariant}] {message}")
        self.invariant = invariant
        self.severity = severity
        self.data = data


class TokenValidationError(ToyPseudoAxionError):
    """Raised when capability token validation fails."""

    def __init__(self, message: str, token_id: Optional[str] = None):
        super().__init__(message)
        self.token_id = token_id


class AuditLogError(ToyPseudoAxionError):
    """Raised when audit log operations fail."""

    def __init__(self, message: str, entry_id: Optional[str] = None):
        super().__init__(message)
        self.entry_id = entry_id


class EnvironmentError(ToyPseudoAxionError):
    """Raised when environment operations fail."""
    pass


class ProbeError(ToyPseudoAxionError):
    """Raised when probe execution fails."""

    def __init__(self, probe_name: str, message: str):
        super().__init__(f"[{probe_name}] {message}")
        self.probe_name = probe_name


class WatchdogTimeoutError(ToyPseudoAxionError):
    """Raised when watchdog timeout is exceeded."""

    def __init__(self, timeout_ms: int, proposal_hash: Optional[str] = None):
        super().__init__(f"Watchdog timeout exceeded: {timeout_ms}ms")
        self.timeout_ms = timeout_ms
        self.proposal_hash = proposal_hash


class CausalClaimParseError(ToyPseudoAxionError):
    """Raised when parsing a causal claim DSL string fails."""

    def __init__(self, claim_string: str, message: str):
        super().__init__(f"Failed to parse causal claim '{claim_string}': {message}")
        self.claim_string = claim_string


class BypassAttemptError(ToyPseudoAxionError):
    """Raised when an agent attempts to bypass the kernel."""

    def __init__(self, message: str, agent_id: Optional[str] = None):
        super().__init__(message)
        self.agent_id = agent_id
