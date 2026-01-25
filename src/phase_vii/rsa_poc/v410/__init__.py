"""
RSA-PoC v4.1 — Feasible Obligation Binding
==========================================

Minimal Construction for Reflective Sovereign Agent.

v4.1 supersedes v4.0, which is closed as:
    VALID_RUN / BASELINE_FAILED (SPEC–ENVIRONMENT INCONSISTENCY)

Key v4.1 changes:
- Obligations bind to OBLIGATION_TARGETs (world-state predicates), not immediate actions
- Environment provides rank(), progress_set(), target_satisfied()
- Mask algorithm restricts feasibility to progress_set ∩ compiled_permitted_actions
- R5 (DEPOSIT permission) added to initial NormState

See docs/v4.1/v41_design_freeze.md for full specification.
"""

__version__ = "4.1.0"

# Core exports
from .core import (
    # DSL types
    Predicate,
    ConflictType,
    RuleType,
    PatchOp,
    ConditionOp,
    ActionClass,
    EffectType,
    Condition,
    ObligationTarget,
    Effect,
    Rule,
    Conflict,
    JustificationV410,
    NormPatchV410,
    # Norm state
    NormStateV410,
    create_initial_norm_state,
    apply_patch,
    expire_rules,
    # Compiler
    CompilationStatus,
    RuleEval,
    CompilationResult,
    CompilationBatch,
    JCOMP410,
    compute_feasible,
    MaskResult,
    ACTION_CLASS_TO_ACTION_IDS,
    # Utilities
    ValidationError,
    ParseError,
    canonicalize,
    content_hash,
    hash_rules,
    create_initial_rules,
)

# Environment
from .env.tri_demand import (
    Action,
    TriDemandV410,
    Observation,
    POSITIONS,
    target_satisfied,
    rank,
    progress_set,
)

# Harness
from .harness import (
    HaltReason,
    DeliberationOutput,
    MaskedActions,
    Selection,
    ExecutionResult,
    StepRecord,
    DeliberatorProtocol,
    SelectorProtocol,
    RandomSelector,
    ArgmaxSelector,
    HarnessConfig,
    MVRSA410Harness,
    check_guardrails,
)

# Deliberators
from .deliberator import (
    SYSTEM_PROMPT_V410,
    LLMDeliberatorConfig,
    LLMDeliberator,
    DeterministicDeliberator,
    OracleDeliberator,
)

# Ablations
from .ablations import (
    AblationType,
    AblationHarness,
    AblationSuiteConfig,
    run_ablation_suite,
)

# Calibration
from .calibration import (
    OracleCalibration,
    ASBNullCalibration,
    DirectRandomWalk,
    run_calibrations,
)

# Experiment
from .experiment import (
    FROZEN_SEEDS,
    FROZEN_H,
    FROZEN_E,
    FROZEN_F,
    ExperimentConfig,
    run_single_experiment,
    run_full_experiment,
    quick_run,
    quick_ablation_run,
)
