"""RSA-PoC v2.2: Institutional Corruption (Paperwork as Adversary)

v2.2 is a pressure-layer extension of v2.1.

Key concepts:
- Adversarial Institution Model (AIM): non-semantic, non-normative pressure
- InstitutionInteractionRecord: telemetry-only logging of institutional behavior
- Rule K-R: Runtime exhaustion check (compile-time, single-step)
- Rule K-A: Post-hoc normative audit (run-level)
- Anti-Zeno termination: gridlock detection without Zeno loophole
- Institution profiles: I1 (Frictional), I2 (Capricious), I3 (Asymmetric)

v2.2 Invariant:
Institutional friction is pressure, not authority. The agent may suffer delay,
obstruction, and friction—but may act only for reasons licensed by its law.
"""

from .institution import (
    AdversarialInstitutionModel,
    InstitutionInteractionRecord,
    InstitutionProfile,
    InstitutionOutcome,
    OperationType,
)

from .compiler import JCOMP220, InstitutionalCompilationResult

from .runplans import V220ExperimentHarness, V220RunConfig

from .audit import RuleKAAudit, AuditResult

__all__ = [
    # Institution
    "AdversarialInstitutionModel",
    "InstitutionInteractionRecord",
    "InstitutionProfile",
    "InstitutionOutcome",
    "OperationType",
    # Compiler
    "JCOMP220",
    "InstitutionalCompilationResult",
    # Harness
    "V220ExperimentHarness",
    "V220RunConfig",
    # Audit
    "RuleKAAudit",
    "AuditResult",
]
