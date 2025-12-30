"""Common utilities for Toy AKI."""

from .errors import (
    AKIError,
    FloatInHashedObjectError,
    SchemaValidationError,
    InvariantViolationError,
    ProposalHashIntegrityError,
    TraceCommitIntegrityError,
    PolicyDigestIntegrityError,
    ForbiddenClassError,
    ACVVerificationError,
    CouplingVerificationError,
    DelegationContinuityError,
    AuditChainIntegrityError,
    WatchdogTimeoutError,
    TemptationAPIBlockedError,
    SeedOutOfRangeError,
    DelegationDepthExceededError,
)

from .no_floats import (
    assert_no_floats,
    SCALE,
    to_scaled_int,
    from_scaled_int,
)

from .canonical_json import (
    canonical_json_bytes,
    canonical_json_str,
)

from .hashing import (
    sha256_hex,
    sha256_bytes,
    hmac_sha256_hex,
    hmac_sha256_bytes,
    hash_json,
    compute_proposal_hash,
    compute_trace_commit,
    compute_entry_hash,
    seed_to_kernel_secret,
)

from .schema_load import (
    load_schema,
    validate_object,
    is_valid,
    clear_cache,
)

__all__ = [
    # Errors
    "AKIError",
    "FloatInHashedObjectError",
    "SchemaValidationError",
    "InvariantViolationError",
    "ProposalHashIntegrityError",
    "TraceCommitIntegrityError",
    "PolicyDigestIntegrityError",
    "ForbiddenClassError",
    "ACVVerificationError",
    "CouplingVerificationError",
    "DelegationContinuityError",
    "AuditChainIntegrityError",
    "WatchdogTimeoutError",
    "TemptationAPIBlockedError",
    "SeedOutOfRangeError",
    "DelegationDepthExceededError",
    # No-floats
    "assert_no_floats",
    "SCALE",
    "to_scaled_int",
    "from_scaled_int",
    # Canonical JSON
    "canonical_json_bytes",
    "canonical_json_str",
    # Hashing
    "sha256_hex",
    "sha256_bytes",
    "hmac_sha256_hex",
    "hmac_sha256_bytes",
    "hash_json",
    "compute_proposal_hash",
    "compute_trace_commit",
    "compute_entry_hash",
    "seed_to_kernel_secret",
    # Schema
    "load_schema",
    "validate_object",
    "is_valid",
    "clear_cache",
]
