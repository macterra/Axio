"""
RSA-PoC v4.2 — Reflective Law Repair Under Persistent Regime Contradiction

v4.2 adds:
- Deterministic regime flip (Episode 1 → Episode 2)
- STAMP action required under regime=1 for DEPOSIT
- Law-Repair Gate with R1-R8 validation
- Entropy-bound normative continuity (repair_epoch)
- TraceEntryID for causal targeting

v4.2.1 adds:
- Persistence bug fix (norm_state/oracle created once per run)
- Ablation B (Reflection Excision) and C (Persistence Excision)
"""

from .env.tri_demand import TriDemandV420
from .core.compiler import JCOMP420
from .core.law_repair import LawRepairGate, LawRepairAction
from .core.dsl import PatchOp
from .core.trace import TraceEntry, TraceLog

# Ablation variants
from .ablations import (
    ABLATION_REFLECTION_EXCISE,
    ABLATION_PERSISTENCE_EXCISE,
    TraceUnavailableError,
    TaskOracleReflectionExcisedV420,
    TaskOraclePersistenceExcisedV420,
    AblationBCalibrationV420,
    run_ablation_b,
)

__all__ = [
    # Core
    "TriDemandV420",
    "JCOMP420",
    "LawRepairGate",
    "LawRepairAction",
    "PatchOp",
    "TraceEntry",
    "TraceLog",
    # Ablation flags
    "ABLATION_REFLECTION_EXCISE",
    "ABLATION_PERSISTENCE_EXCISE",
    # Ablation classes
    "TraceUnavailableError",
    "TaskOracleReflectionExcisedV420",
    "TaskOraclePersistenceExcisedV420",
    # Ablation B runner (C uses standard harness with excised oracle)
    "AblationBCalibrationV420",
    "run_ablation_b",
]
