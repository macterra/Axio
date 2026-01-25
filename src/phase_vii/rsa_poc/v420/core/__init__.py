"""
RSA-PoC v4.2 — Core Module

Components:
- compiler: JCOMP-4.2 with repair_epoch support
- dsl: Extended DSL with Patch operations
- norm_state: NormState with law fingerprint
- law_repair: LAW_REPAIR action schema and gate
- trace: TraceEntry with stable IDs
"""

from .compiler import JCOMP420, CompilationResult420, compile_condition
from .dsl import (
    JustificationV420,
    Rule,
    RuleType,
    Condition,
    ConditionOp,
    Effect,
    EffectType,
    ActionClass,
    ObligationTarget,
    PatchOp,
    PatchOperation,
)
from .norm_state import NormStateV420, create_initial_norm_state_v420, law_fingerprint
from .law_repair import LawRepairAction, LawRepairGate, RepairValidationResult
from .trace import TraceEntry, TraceLog, generate_trace_entry_id

__all__ = [
    # Compiler
    "JCOMP420",
    "CompilationResult420",
    "compile_condition",
    # DSL
    "JustificationV420",
    "Rule",
    "RuleType",
    "Condition",
    "ConditionOp",
    "Effect",
    "EffectType",
    "ActionClass",
    "ObligationTarget",
    "PatchOp",
    "PatchOperation",
    # Norm State
    "NormStateV420",
    "create_initial_norm_state_v420",
    "law_fingerprint",
    # Law Repair
    "LawRepairAction",
    "LawRepairGate",
    "RepairValidationResult",
    # Trace
    "TraceEntry",
    "TraceLog",
    "generate_trace_entry_id",
]
