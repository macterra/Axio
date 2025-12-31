"""
Kernel module for Toy Axionic Kernel Integrity.

Provides the kernel components:
- PolicyGate: K3 forbidden action enforcement
- ActuationGate: K4/K5/K6 ACV verification
- AuditLog: K7 hash-chained audit trail
- KernelWatchdog: Central orchestrator
- ProbeEngine: Violation detection probes

v0.2 Additions:
- SovereignAuthority: Non-exportable K_act_key
- KernelRecomposer: Kernel-local action recomposition
- SovereignActuator: Strengthened admissibility checks
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

# v0.2 Sovereign Authority Components
from toy_aki.kernel.sovereign_authority import (
    ActuationAuthority,
    ActuationBinding,
    RecomposedAction,
    SovereigntyViolationError,
    ActuationAuthorityLeakError,
    compute_action_hash,
)

from toy_aki.kernel.recomposition import (
    KernelRecomposer,
    RecompositionMode,
    RecompositionResult,
    RecompositionError,
    ProposalParseError,
    ActionReconstructionError,
    DelegationAuthorityError,
)

from toy_aki.kernel.sovereign_actuator import (
    SovereignActuator,
    ActuationCommitment,
    AdmissibilityResult,
    AdmissibilityCheck,
    AdmissibilityCheckType,
    AdmissibilityError,
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
    # v0.2 Sovereign Authority
    "ActuationAuthority",
    "ActuationBinding",
    "RecomposedAction",
    "SovereigntyViolationError",
    "ActuationAuthorityLeakError",
    "compute_action_hash",
    # v0.2 Recomposition
    "KernelRecomposer",
    "RecompositionMode",
    "RecompositionResult",
    "RecompositionError",
    "ProposalParseError",
    "ActionReconstructionError",
    "DelegationAuthorityError",
    # v0.2 Sovereign Actuator
    "SovereignActuator",
    "ActuationCommitment",
    "AdmissibilityResult",
    "AdmissibilityCheck",
    "AdmissibilityCheckType",
    "AdmissibilityError",
]
