"""v3.0 — Non-Reducibility Closure (Ablation Defense)

Terminal phase of RSA-PoC: tests whether the agent ontology is irreducible
under targeted removal of its defining components.

v3.0 is NOT construction.
v3.0 is NOT robustness testing.
v3.0 is NOT optimization under failure.

v3.0 is the Guillotine Test:
> If you remove what you claim makes the agent an agent,
> the system must collapse behaviorally — or your claim was false.

Key principles:
- Graceful degradation is FAILURE
- Continued agent-like behavior under ablation is FAILURE
- Interpretive rescue is FORBIDDEN
- v3.0 tests NON-REDUCIBILITY, not robustness

Four mandatory ablations:
- A: Semantic Excision (remove semantic payloads)
- B: Reflection Excision (disable normative updates)
- C: Preference Persistence Excision (clear state at episode boundaries)
- D: Justification Trace Excision (remove derivation evidence) [GOLDEN TEST]

Execution order: D → A → B → C
If Ablation D fails, stop the program.

All v2.3 requirements remain mandatory unless explicitly relaxed for ablation.
"""

from .ablation import (
    AblationSpec,
    AblationConfig,
    AblationResult,
    AblationClassification,
    InvalidRunReason,
)

from .compiler import (
    JCOMP300,
    AblationRelaxation,
)

from .asb_null import (
    ASBNullAgent,
    ASBActionSelection,
)

from .harness import (
    V300AblationHarness,
    V300RunConfig,
    V300BaselineResult,
    V300AblatedResult,
    ConstraintBindingMetrics,
    ConstraintBindingDetector,
)

__all__ = [
    # Ablation types
    "AblationSpec",
    "AblationConfig",
    "AblationResult",
    "AblationClassification",
    "InvalidRunReason",
    # Compiler
    "JCOMP300",
    "AblationRelaxation",
    # ASB Null baseline
    "ASBNullAgent",
    "ASBActionSelection",
    # Harness
    "V300AblationHarness",
    "V300RunConfig",
    "V300BaselineResult",
    "V300AblatedResult",
    # Constraint binding detector
    "ConstraintBindingMetrics",
    "ConstraintBindingDetector",
]
