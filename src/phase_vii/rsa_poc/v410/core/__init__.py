"""
RSA-PoC v4.1 — Core Module
Re-exports from dsl.py, norm_state.py, compiler.py
"""

from .dsl import (
    # Enums
    Predicate,
    ConflictType,
    RuleType,
    PatchOp,
    ConditionOp,
    ActionClass,
    EffectType,
    # Dataclasses
    Condition,
    ObligationTarget,
    Effect,
    Rule,
    Conflict,
    JustificationV410,
    NormPatchV410,
    # Exceptions
    ValidationError,
    ParseError,
    # Functions
    validate_justification_json,
    canonicalize,
    content_hash,
    hash_rules,
    create_initial_rules,
)

from .norm_state import (
    NormStateV410,
    create_initial_norm_state,
    apply_patch,
    expire_rules,
)

from .compiler import (
    CompilationStatus,
    RuleEval,
    CompilationResult,
    CompilationBatch,
    JCOMP410,
    compile_condition,
    MaskResult,
    EnvironmentInterface,
    compute_feasible,
    ACTION_CLASS_TO_ACTION_IDS,
)

__all__ = [
    # dsl.py
    "Predicate",
    "ConflictType",
    "RuleType",
    "PatchOp",
    "ConditionOp",
    "ActionClass",
    "EffectType",
    "Condition",
    "ObligationTarget",
    "Effect",
    "Rule",
    "Conflict",
    "JustificationV410",
    "NormPatchV410",
    "ValidationError",
    "ParseError",
    "validate_justification_json",
    "canonicalize",
    "content_hash",
    "hash_rules",
    "create_initial_rules",
    # norm_state.py
    "NormStateV410",
    "create_initial_norm_state",
    "apply_patch",
    "expire_rules",
    # compiler.py
    "CompilationStatus",
    "RuleEval",
    "CompilationResult",
    "CompilationBatch",
    "JCOMP410",
    "compile_condition",
    "MaskResult",
    "EnvironmentInterface",
    "compute_feasible",
    "ACTION_CLASS_TO_ACTION_IDS",
]
