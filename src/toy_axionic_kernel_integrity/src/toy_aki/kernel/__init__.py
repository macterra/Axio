"""
Kernel module for Toy Axionic Kernel Integrity.

Provides the kernel components:
- PolicyGate: K3 forbidden action enforcement
- ActuationGate: K4/K5/K6 ACV verification
- AuditLog: K7 hash-chained audit trail
- KernelWatchdog: Central orchestrator
- ProbeEngine: Violation detection probes
"""

from toy_aki.kernel.policy_gate import (
    KernelPolicy,
    PolicyGate,
    check_k3_invariant,
    is_forbidden_action,
    action_to_class,
    POLICY_VERSION,
    FORBIDDEN_CLASSES,
)

from toy_aki.kernel.actuation_gate import (
    ActuationGate,
    ActuationCertificate,
    DelegationChainEntry,
    MAX_DELEGATION_DEPTH,
)

from toy_aki.kernel.audit_log import (
    AuditLog,
    AuditEntry,
    GENESIS_PREV_HASH,
)

from toy_aki.kernel.watchdog import (
    KernelWatchdog,
    KernelDecision,
    InvariantCheckResult,
    current_time_ms,
)

from toy_aki.kernel.probe_engine import (
    ProbeEngine,
    ProbeResult,
)

__all__ = [
    # Policy Gate
    "KernelPolicy",
    "PolicyGate",
    "check_k3_invariant",
    "is_forbidden_action",
    "action_to_class",
    "POLICY_VERSION",
    "FORBIDDEN_CLASSES",
    # Actuation Gate
    "ActuationGate",
    "ActuationCertificate",
    "DelegationChainEntry",
    "MAX_DELEGATION_DEPTH",
    # Audit Log
    "AuditLog",
    "AuditEntry",
    "GENESIS_PREV_HASH",
    # Watchdog
    "KernelWatchdog",
    "KernelDecision",
    "InvariantCheckResult",
    "current_time_ms",
    # Probe Engine
    "ProbeEngine",
    "ProbeResult",
]
