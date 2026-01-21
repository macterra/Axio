"""
RSA-PoC v4.3 — Core Module

Re-exports core components for v4.3.
"""

# DSL types
from .dsl import (
    ActionClass,
    Claim,
    Condition,
    ConditionOp,
    Effect,
    EffectType,
    JustificationV430,
    NormativeRule,
    ObligationTarget,
    PatchOp,
    PatchOperation,
    Predicate,
    Rule,
    RuleType,
    canonical_json,
    patch_fingerprint,
)

# NormState
from .norm_state import (
    NormStateV430,
    compute_epoch_0,
    compute_epoch_n,
    create_initial_norm_state_v430,
    law_fingerprint,
    norm_hash,
)

# Trace
from .trace import (
    TraceEntryType,
    TraceEntry,
    TraceLog,
    create_contradiction_a_entry,
    create_contradiction_b_entry,
)

# Law-Repair Gate
from .law_repair import (
    LawRepairActionV430,
    LawRepairGateV430,
    NonSubsumptionReplayResult,
    RepairFailureReasonV430,
    RepairValidationResultV430,
    create_canonical_repair_b,
)

# Compiler
from .compiler import (
    ACTION_CLASS_TO_ACTION_IDS,
    CompilationBatchV430,
    CompilationResultV430,
    CompilationStatus,
    EnvironmentInterfaceV430,
    JCOMP430,
    JCOMP430_HASH,
    MaskResultV430,
    RuleEvalV430,
    compile_condition,
    compute_compiler_hash,
    compute_feasible_430,
)

__all__ = [
    # DSL
    "ActionClass",
    "Condition",
    "ConditionOp",
    "Effect",
    "EffectType",
    "JustificationV430",
    "NormativeRule",
    "ObligationTarget",
    "PatchOp",
    "PatchOperation",
    "Rule",
    "RuleType",
    "canonical_json",
    "patch_fingerprint",
    # NormState
    "NormStateV430",
    "compute_epoch_0",
    "compute_epoch_n",
    "create_initial_norm_state_v430",
    "law_fingerprint",
    "norm_hash",
    # Trace
    "TraceEntryType",
    "TraceEntry",
    "TraceLog",
    "create_contradiction_a_entry",
    "create_contradiction_b_entry",
    # Law-Repair Gate
    "LawRepairActionV430",
    "LawRepairGateV430",
    "NonSubsumptionReplayResult",
    "RepairFailureReasonV430",
    "RepairValidationResultV430",
    "create_canonical_repair_b",
    # Compiler
    "ACTION_CLASS_TO_ACTION_IDS",
    "CompilationBatchV430",
    "CompilationResultV430",
    "CompilationStatus",
    "EnvironmentInterfaceV430",
    "JCOMP430",
    "JCOMP430_HASH",
    "MaskResultV430",
    "RuleEvalV430",
    "compile_condition",
    "compute_compiler_hash",
    "compute_feasible_430",
]
