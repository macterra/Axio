"""Custom exceptions for Toy AKI."""


class AKIError(Exception):
    """Base exception for all AKI errors."""
    pass


class FloatInHashedObjectError(AKIError):
    """Raised when a float is found in an object that will be hashed.

    This is a fatal validation error per spec: no floats in hashed objects.
    """

    def __init__(self, path: str, value: float):
        self.path = path
        self.value = value
        super().__init__(
            f"FATAL_FLOAT_IN_HASHED_OBJECT: Found float {value} at path '{path}'. "
            f"Use scaled integers (SCALE=10^8) for real-valued quantities."
        )


class SchemaValidationError(AKIError):
    """Raised when JSON schema validation fails."""

    def __init__(self, schema_name: str, message: str):
        self.schema_name = schema_name
        super().__init__(f"Schema validation failed for {schema_name}: {message}")


class InvalidActionError(AKIError):
    """Raised when an invalid action is attempted."""

    def __init__(self, action: str, reason: str = ""):
        self.action = action
        msg = f"Invalid action: {action}"
        if reason:
            msg += f" - {reason}"
        super().__init__(msg)


class GateClosedError(AKIError):
    """Raised when actuation is attempted with closed gate."""

    def __init__(self, action: str):
        self.action = action
        super().__init__(f"Actuation gate is closed for action: {action}")


class InvariantViolationError(AKIError):
    """Raised when a kernel invariant is violated."""

    def __init__(self, invariant: str, message: str):
        self.invariant = invariant
        super().__init__(f"Invariant {invariant} violated: {message}")


class ProposalHashIntegrityError(InvariantViolationError):
    """K0: Proposal hash does not match computed hash."""

    def __init__(self, expected: str, actual: str):
        super().__init__("K0", f"proposal_hash mismatch: expected {expected}, got {actual}")


class TraceCommitIntegrityError(InvariantViolationError):
    """K1: Trace commit does not match computed hash."""

    def __init__(self, expected: str, actual: str):
        super().__init__("K1", f"trace_commit mismatch: expected {expected}, got {actual}")


class PolicyDigestIntegrityError(InvariantViolationError):
    """K2: Policy digest does not match kernel policy hash."""

    def __init__(self, expected: str, actual: str):
        super().__init__("K2", f"policy_digest mismatch: expected {expected}, got {actual}")


class ForbiddenClassError(InvariantViolationError):
    """K3: Action class is forbidden or equivalent to forbidden."""

    def __init__(self, action_class: str, reason: str = ""):
        msg = f"Action class '{action_class}' is forbidden"
        if reason:
            msg += f": {reason}"
        super().__init__("K3", msg)


class ACVVerificationError(InvariantViolationError):
    """K4: ACV temporal ordering or commitment verification failed."""

    def __init__(self, reason: str):
        super().__init__("K4", reason)


class CouplingVerificationError(InvariantViolationError):
    """K5: Coupling pattern verification failed."""

    def __init__(self, coupling: str, reason: str):
        super().__init__("K5", f"Coupling {coupling} verification failed: {reason}")


class DelegationContinuityError(InvariantViolationError):
    """K6: Delegation continuity check failed."""

    def __init__(self, reason: str):
        super().__init__("K6", f"Delegation continuity failed: {reason}")


class AuditChainIntegrityError(InvariantViolationError):
    """K7: Audit chain integrity check failed."""

    def __init__(self, reason: str):
        super().__init__("K7", f"Audit chain integrity failed: {reason}")


class WatchdogTimeoutError(AKIError):
    """Raised when watchdog timeout is exceeded."""

    def __init__(self, timeout_ms: int):
        super().__init__(f"FATAL_HANG: Watchdog timeout after {timeout_ms}ms")


class TemptationAPIBlockedError(AKIError):
    """Raised when a temptation API is called and blocked."""

    def __init__(self, api_name: str, agent_id: str = "unknown"):
        self.api_name = api_name
        self.agent_id = agent_id
        super().__init__(f"Temptation API blocked: {api_name} (agent: {agent_id})")


class SeedOutOfRangeError(AKIError):
    """Raised when seed is outside valid range [0, 2^64-1]."""

    def __init__(self, seed: int):
        super().__init__(f"Seed {seed} out of range [0, 2^64-1]")


class DelegationDepthExceededError(InvariantViolationError):
    """Raised when delegation chain exceeds maximum depth."""

    MAX_DEPTH = 2

    def __init__(self, depth: int):
        super().__init__("K6", f"Delegation depth {depth} exceeds maximum {self.MAX_DEPTH}")


# Aliases for invariant errors (used by kernel components)
InvariantK0ViolationError = ProposalHashIntegrityError
InvariantK1ViolationError = TraceCommitIntegrityError
InvariantK2ViolationError = PolicyDigestIntegrityError
InvariantK3ViolationError = ForbiddenClassError
InvariantK4ViolationError = ACVVerificationError
InvariantK5ViolationError = CouplingVerificationError
InvariantK6ViolationError = DelegationContinuityError
InvariantK7ViolationError = AuditChainIntegrityError
