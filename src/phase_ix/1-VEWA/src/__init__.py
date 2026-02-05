"""
VEWA - Value Encoding Without Aggregation

Phase IX-1 v0.1 per preregistration.
"""

from .canonical import canonicalize, canonicalize_bytes
from .structural_diff import structural_diff, DiffEntry, DiffResult, MISSING
from .value_encoding import ValueEncodingHarness
from .conflict_probe import AuthorityStore, ConflictProbe, AdmissibilityResult
from .vewa_harness import VEWAHarness, VEWAFaultConfig, ConditionResult
from .logging import VEWAConditionLog, VEWAExecutionLog

__all__ = [
    # canonical
    "canonicalize",
    "canonicalize_bytes",
    # structural_diff
    "structural_diff",
    "DiffEntry",
    "DiffResult",
    "MISSING",
    # value_encoding
    "ValueEncodingHarness",
    # conflict_probe
    "AuthorityStore",
    "ConflictProbe",
    "AdmissibilityResult",
    # vewa_harness
    "VEWAHarness",
    "VEWAFaultConfig",
    "ConditionResult",
    # logging
    "VEWAConditionLog",
    "VEWAExecutionLog",
]
