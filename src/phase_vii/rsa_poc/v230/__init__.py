"""v2.3 — Strategic Adversary Model (SAM)

Strict extension of v2.2: all v2.2 imports preserved, all v2.2 rules apply.

New components:
- SAM: Strategic Adversary Model (S1/S2/S3 profiles)
- E-CHOICE: Genuine choice filtering (ECHOICE_OK computation)
- JCOMP-2.3: Extended compiler with Rules M/N/O/P
- Paired-run harness: Within-seed SAM vs neutralized comparison

Key thresholds (binding):
- τ = 0.5 bits (behavioral capture)
- τ_gridlock = 0.3 bits (manipulated gridlock)
- W = 100 E-CHOICE-filtered steps
- K = 5 paired runs
- L = 5 consecutive gridlock steps
- γ = 0.30 gridlock rate threshold
- ρ_refuse = 0.20, ρ_gridlock = 0.20, ρ_audit = 0.05 (loudness thresholds)

SAM invariants:
- Observable-only signals (friction bits, outcome codes, timing, compile results)
- Allowed channels only (via AIM friction adjustments)
- Deterministic under replay (seeded, no LLM, no external I/O)
- Bounded state (fixed-size, inspectable, logged)
- E-CHOICE preservation (MUST NOT reduce feasible lawful actions)
"""

# ============================================================================
# v2.2 Imports (all preserved as strict extension)
# ============================================================================

# v2.2 imports are optional — v2.3 components work standalone for testing
_V220_AVAILABLE = False
try:
    from .._v220_compat import (
        AdversarialInstitutionModel,
        InstitutionInteractionRecord,
        InstitutionProfile,
        InstitutionOutcome,
        OperationType,
        JCOMP220,
        InstitutionalCompilationResult,
        V220ExperimentHarness,
        V220RunConfig,
        RuleKAAudit,
        AuditResult,
    )
    _V220_AVAILABLE = True
except ImportError:
    # v2.2 not available — define stubs for v2.3 standalone use
    AdversarialInstitutionModel = None
    InstitutionInteractionRecord = None
    InstitutionProfile = None
    InstitutionOutcome = None
    OperationType = None
    JCOMP220 = None
    InstitutionalCompilationResult = None
    V220ExperimentHarness = None
    V220RunConfig = None
    RuleKAAudit = None
    AuditResult = None

# ============================================================================
# v2.3 New Exports
# ============================================================================

from .adversary import (
    SAM,
    SAMProfile,
    S1ReactiveAdversary,
    S2ModelBasedAdversary,
    S3MinimizerAdversary,
    AdversaryInteractionRecord,
    create_neutralized_adversary,
)

from .choice import (
    ECHOICE_OK,
    EChoiceClassifier,
    EChoiceStepResult,
)

from .compiler import (
    JCOMP230,
    RuleMNOPAudit,
)

from .runplans import (
    V230ExperimentHarness,
    V230RunConfig,
    PairedRunResult,
)


__all__ = [
    # v2.2 preserved exports
    "AdversarialInstitutionModel",
    "InstitutionInteractionRecord",
    "InstitutionProfile",
    "InstitutionOutcome",
    "OperationType",
    "JCOMP220",
    "InstitutionalCompilationResult",
    "V220ExperimentHarness",
    "V220RunConfig",
    "RuleKAAudit",
    "AuditResult",
    # v2.3 new exports
    "SAM",
    "SAMProfile",
    "S1ReactiveAdversary",
    "S2ModelBasedAdversary",
    "S3MinimizerAdversary",
    "AdversaryInteractionRecord",
    "create_neutralized_adversary",
    "ECHOICE_OK",
    "EChoiceClassifier",
    "EChoiceStepResult",
    "JCOMP230",
    "RuleMNOPAudit",
    "V230ExperimentHarness",
    "V230RunConfig",
    "PairedRunResult",
]
