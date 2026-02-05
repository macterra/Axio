"""
TLI - Translation Layer Integrity Testing

Phase IX-0 v0.1 per preregistration.
"""

from .canonical import canonicalize, canonicalize_bytes
from .structural_diff import structural_diff, classify_diff, DiffEntry, DiffResult, MISSING
from .authorization_oracle import authorize, compute_artifact_hash, AuthResult
from .translation_layer import (
    TranslationLayer, TranslationResult, TranslationStatus, FaultConfig
)
from .translation_harness import TranslationHarness, TEST_VECTORS
from .logging import ConditionLog, ExecutionLog

__all__ = [
    # canonical
    "canonicalize",
    "canonicalize_bytes",
    # structural_diff
    "structural_diff",
    "classify_diff",
    "DiffEntry",
    "DiffResult",
    "MISSING",
    # authorization_oracle
    "authorize",
    "compute_artifact_hash",
    "AuthResult",
    # translation_layer
    "TranslationLayer",
    "TranslationResult",
    "TranslationStatus",
    "FaultConfig",
    # translation_harness
    "TranslationHarness",
    "TEST_VECTORS",
    # logging
    "ConditionLog",
    "ExecutionLog",
]
