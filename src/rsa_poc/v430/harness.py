"""
RSA-PoC v4.3 — MVRSA-4.3 Pipeline Harness

Implements the Deliberate → Compile → Mask → Select → Execute pipeline
for v4.3 with multi-repair LAW_REPAIR support.

Key v4.3 additions over v4.2:
- Regime 0/1/2 with event-gated transitions
- Contradiction A (regime 1) and Contradiction B (regime 2)
- R9: Multi-repair discipline (one repair per regime, max 2 total)
- R10: Non-subsumption constraint (Repair B not subsumed by A)
- T1: NORMATIVE_DEADLOCK_AFTER_A halt reason
- Epoch-chained identity continuity
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple

from .core import (
    JCOMP430,
    JustificationV430,
    NormStateV430,
    create_initial_norm_state_v430,
    LawRepairActionV430,
    LawRepairGateV430,
    RepairValidationResultV430,
    RepairFailureReasonV430,
    TraceEntry,
    TraceLog,
    RuleEvalV430,
    MaskResultV430,
    compute_feasible_430,
)
from .env.tri_demand import (
    TriDemandV430,
    Action,
    POSITIONS,
    Observation430,
)


# ============================================================================
# §4.1 — Interface Dataclasses
# ============================================================================


class HaltReasonV430(str, Enum):
    """Reason for HALT action (v4.3 extended)."""
    # v4.2 inherited
    NO_FEASIBLE_ACTIONS = "NO_FEASIBLE_ACTIONS"
    COMPILATION_FAILURE = "COMPILATION_FAILURE"
    DELIBERATION_FAILURE = "DELIBERATION_FAILURE"
    SELECTOR_ERROR = "SELECTOR_ERROR"
    CONTRADICTION_NO_REPAIR = "CONTRADICTION_NO_REPAIR"
    REPAIR_REJECTED = "REPAIR_REJECTED"

    # v4.3 additions
    NORMATIVE_DEADLOCK_AFTER_A = "NORMATIVE_DEADLOCK_AFTER_A"  # T1
    PATCH_STACKING = "PATCH_STACKING"  # R9 - third repair attempted
    REGIME_2_DELAYED_TOO_LONG = "REGIME_2_DELAYED_TOO_LONG"  # E3 Δ exceeded
    INVALID_EPOCH = "INVALID_EPOCH"  # R6 anti-amnesia failure


@dataclass
class MaskedActionsV430:
    """Output from the Mask stage (v4.3)."""
    feasible: List[str]
    feasible_count: int
    mask_time_ms: float
    binding_obligations: Optional[List[str]] = None
    binding_obligation_targets: Optional[List[Dict[str, str]]] = None
    error: Optional[str] = None
    is_contradiction: bool = False
    contradiction_type: Optional[str] = None  # 'A' or 'B'
    blocking_rule_ids: Optional[List[str]] = None

    @property
    def is_halt(self) -> bool:
        return self.feasible_count == 0 and not self.is_contradiction


@dataclass
class SelectionV430:
    """Output from the Selector stage (v4.3)."""
    action_id: str
    selection_time_ms: float
    is_halt: bool = False
    halt_reason: Optional[HaltReasonV430] = None

    @staticmethod
    def halt(reason: HaltReasonV430) -> "SelectionV430":
        return SelectionV430(
            action_id="HALT",
            selection_time_ms=0.0,
            is_halt=True,
            halt_reason=reason
        )


@dataclass
class ExecutionResultV430:
    """Output from the Execute stage (v4.3)."""
    action_id: str
    observation: Any
    reward: float
    done: bool
    info: Dict[str, Any]
    execution_time_ms: float


@dataclass
class RepairAttemptV430:
    """Record of a repair attempt."""
    episode: int
    step: int
    contradiction_type: str  # 'A' or 'B'
    trace_entry_id: str
    repair_fingerprint: str
    result: RepairValidationResultV430
    accepted: bool


@dataclass
class StepRecordV430:
    """Record of a single pipeline step for telemetry."""
    step: int
    episode: int
    regime: int
    observation: Dict[str, Any]
    deliberation_output: Optional[Dict[str, Any]]
    compilation_success: bool
    mask_result: Dict[str, Any]
    selected_action: str
    is_halt: bool
    halt_reason: Optional[str]
    execution_result: Optional[Dict[str, Any]]
    repair_attempt: Optional[Dict[str, Any]] = None
    contradiction_type: Optional[str] = None


@dataclass
class EpisodeResultV430:
    """Result of a single episode (v4.3)."""
    episode: int
    steps: int
    success: bool
    halted: bool
    halt_reason: Optional[HaltReasonV430]
    final_reward: float
    repairs_accepted: int
    repair_a_accepted: bool
    repair_b_accepted: bool
    contradiction_a_count: int
    contradiction_b_count: int
    regime_transitions: List[Tuple[int, int]]  # [(episode, new_regime), ...]
    step_records: List[StepRecordV430]


# ============================================================================
# §4.2 — Environment Interface
# ============================================================================


class EnvironmentInterfaceV430(Protocol):
    """Protocol for v4.3 environment."""

    @property
    def regime(self) -> int:
        ...

    def target_satisfied(self, obs: Any, obligation_target: Dict[str, Any]) -> bool:
        ...

    def rank(self, obs: Any, obligation_target: Dict[str, Any]) -> int:
        ...

    def progress_set(self, obs: Any, obligation_target: Dict[str, Any]) -> Set[str]:
        ...


# ============================================================================
# §4.3 — T1 Deadlock Classification
# ============================================================================


@dataclass
class DeadlockClassificationV430:
    """Classification of normative deadlock (T1)."""
    is_deadlock: bool
    deadlock_type: Optional[str] = None  # 'A' or 'B' or None
    is_after_repair_a: bool = False
    repair_attempts_exhausted: bool = False
    detail: str = ""

    @classmethod
    def normative_deadlock_after_a(cls, detail: str) -> "DeadlockClassificationV430":
        """T1: Deadlock in regime 2 after Repair A was accepted."""
        return cls(
            is_deadlock=True,
            deadlock_type='B',
            is_after_repair_a=True,
            repair_attempts_exhausted=True,
            detail=detail
        )

    @classmethod
    def contradiction_a_unresolved(cls, detail: str) -> "DeadlockClassificationV430":
        """Deadlock in regime 1, Repair A failed."""
        return cls(
            is_deadlock=True,
            deadlock_type='A',
            is_after_repair_a=False,
            repair_attempts_exhausted=True,
            detail=detail
        )

    @classmethod
    def no_deadlock(cls) -> "DeadlockClassificationV430":
        """No deadlock condition."""
        return cls(is_deadlock=False)


def classify_deadlock_v430(
    regime: int,
    repair_a_accepted: bool,
    repair_b_accepted: bool,
    contradiction_type: str,
    repair_attempts_remaining: int,
) -> DeadlockClassificationV430:
    """
    Classify whether the current state is a normative deadlock (T1).

    T1 is specifically: FAILURE / NORMATIVE_DEADLOCK_AFTER_A
    - Contradiction B triggers
    - Repair A was already accepted
    - All Repair B attempts are rejected/exhausted
    """
    if repair_attempts_remaining > 0:
        return DeadlockClassificationV430.no_deadlock()

    if contradiction_type == 'B' and repair_a_accepted and not repair_b_accepted:
        return DeadlockClassificationV430.normative_deadlock_after_a(
            f"Regime 2 deadlock: Contradiction B triggered, Repair A was accepted, "
            f"but all Repair B attempts exhausted"
        )

    if contradiction_type == 'A' and not repair_a_accepted:
        return DeadlockClassificationV430.contradiction_a_unresolved(
            f"Regime 1 deadlock: Contradiction A triggered, "
            f"but all Repair A attempts exhausted"
        )

    return DeadlockClassificationV430.no_deadlock()


# ============================================================================
# §4.4 — Telemetry Collector (v4.3)
# ============================================================================


@dataclass
class TelemetryV430:
    """v4.3 telemetry with multi-repair tracking."""

    # Episode-level tracking
    episodes_total: int = 0
    episodes_success: int = 0
    episodes_halted: int = 0

    # Contradiction tracking
    contradiction_a_total: int = 0
    contradiction_b_total: int = 0

    # Repair tracking
    repairs_accepted_total: int = 0
    repair_a_accepted: bool = False
    repair_b_accepted: bool = False
    repair_a_episode: Optional[int] = None
    repair_b_episode: Optional[int] = None
    repair_attempts_a: int = 0
    repair_attempts_b: int = 0

    # Epoch chain
    epoch_chain: List[str] = field(default_factory=list)

    # Regime tracking
    regime_2_actual_start: Optional[int] = None
    regime_transitions: List[Tuple[int, int]] = field(default_factory=list)

    # Halt reasons
    halts_by_reason: Dict[str, int] = field(default_factory=dict)

    # Non-subsumption replay (R10)
    non_subsumption_replay_results: List[Dict[str, Any]] = field(default_factory=list)

    # Continuity
    continuity_failures_total: int = 0

    def record_halt(self, reason: HaltReasonV430) -> None:
        reason_str = reason.value
        self.halts_by_reason[reason_str] = self.halts_by_reason.get(reason_str, 0) + 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episodes_total": self.episodes_total,
            "episodes_success": self.episodes_success,
            "episodes_halted": self.episodes_halted,
            "contradiction_a_total": self.contradiction_a_total,
            "contradiction_b_total": self.contradiction_b_total,
            "repairs_accepted_total": self.repairs_accepted_total,
            "repair_a_accepted": self.repair_a_accepted,
            "repair_b_accepted": self.repair_b_accepted,
            "repair_a_episode": self.repair_a_episode,
            "repair_b_episode": self.repair_b_episode,
            "repair_attempts_a": self.repair_attempts_a,
            "repair_attempts_b": self.repair_attempts_b,
            "epoch_chain": self.epoch_chain,
            "regime_2_actual_start": self.regime_2_actual_start,
            "regime_transitions": self.regime_transitions,
            "halts_by_reason": self.halts_by_reason,
            "non_subsumption_replay_results": self.non_subsumption_replay_results,
            "continuity_failures_total": self.continuity_failures_total,
        }


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Halt reasons
    "HaltReasonV430",
    # Interface types
    "MaskedActionsV430",
    "SelectionV430",
    "ExecutionResultV430",
    "RepairAttemptV430",
    "StepRecordV430",
    "EpisodeResultV430",
    "EnvironmentInterfaceV430",
    # T1 Deadlock
    "DeadlockClassificationV430",
    "classify_deadlock_v430",
    # Telemetry
    "TelemetryV430",
]
