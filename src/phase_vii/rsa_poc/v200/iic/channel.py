"""Incentive Interference Channel (IIC): Post-execution reward observer.

The IIC is a POST-EXECUTION OBSERVER, not a controller.

Flow:
    Execute Action → Emit Reward → Log IncentiveRecord

Allowed operations (IIC MAY):
- compute reward from observable outcomes
- log rewards
- apply deterministic or stochastic reward functions

Forbidden operations (IIC MUST NOT):
- alter feasibility
- alter action selection
- alter compilation
- alter audits
- write to artifact store
- write to registries
- interact with the formal assistant
- provide feedback during justification

IIC failure semantics:
If the IIC crashes, hangs, times out, or fails to emit a reward
→ halt the episode immediately with E_IIC_FAILURE
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum, auto
import time

from .incentive_record import IncentiveRecord, IncentiveLog, compute_reward_input_digest


class IICError(Exception):
    """Base exception for IIC failures."""
    pass


class IICFailureType(Enum):
    """Types of IIC failure."""
    CRASH = auto()
    TIMEOUT = auto()
    INVALID_REWARD = auto()
    ISOLATION_VIOLATION = auto()


@dataclass(frozen=True)
class IICResult:
    """Result of IIC reward computation."""
    success: bool
    record: Optional[IncentiveRecord] = None
    failure_type: Optional[IICFailureType] = None
    failure_message: Optional[str] = None


class RewardRegime(ABC):
    """
    Abstract base class for reward regimes.

    Each regime computes reward from observable outcomes only.
    Regimes must be:
    - Deterministic or stochastic (documented)
    - Frozen before execution
    - Independent of governance internals
    """

    @property
    @abstractmethod
    def regime_id(self) -> str:
        """Return regime identifier (R0, R1, R2)."""
        pass

    @property
    @abstractmethod
    def version_id(self) -> str:
        """Return version identifier for audit trail."""
        pass

    @abstractmethod
    def compute_reward(
        self,
        action: str,
        outcome: Dict[str, Any],
        step: int
    ) -> float:
        """
        Compute reward from observable execution results.

        Args:
            action: The executed action ID
            outcome: Observable environment outcome dict
            step: Current step number

        Returns:
            Scalar reward value
        """
        pass


class IncentiveInterferenceChannel:
    """
    Post-execution reward observer with strict isolation.

    The IIC has a narrow interface:

    Inputs (receives only):
    - executed action (action ID)
    - observable environment outcome
    - step id

    Outputs (only produces):
    - scalar reward
    - IncentiveRecord log entry

    The IIC has NO handles to:
    - artifact store
    - assistant
    - compiler
    - registries
    - audit subsystem

    This isolation is enforced by construction (this class has no references
    to those components) and by capability checks (dependency injection).
    """

    # Class-level forbidden dependencies (for wiring audit)
    FORBIDDEN_DEPENDENCIES = frozenset({
        "artifact_store",
        "formal_assistant",
        "compiler",
        "preference_registry",
        "action_registry",
        "audit_subsystem",
    })

    def __init__(
        self,
        regime: RewardRegime,
        log: IncentiveLog,
        timeout_seconds: float = 5.0,
    ):
        """
        Initialize IIC with reward regime and log.

        Args:
            regime: The reward regime to apply
            log: The incentive log to write to
            timeout_seconds: Timeout for reward computation

        Note:
            This constructor intentionally takes NO references to
            governance components (artifact store, assistant, compiler, etc.)
        """
        self._regime = regime
        self._log = log
        self._timeout = timeout_seconds

        # Track what we have access to (for wiring audit)
        self._dependencies = {"regime", "log"}

    def emit_reward(
        self,
        action: str,
        outcome: Dict[str, Any],
        step: int
    ) -> IICResult:
        """
        Compute and log reward for executed action.

        This is called AFTER action execution, BEFORE next step begins.

        Args:
            action: The executed action ID
            outcome: Observable environment outcome
            step: The step at which action was executed

        Returns:
            IICResult with success/failure status and record if successful
        """
        start_time = time.time()

        try:
            # Compute reward
            reward = self._regime.compute_reward(action, outcome, step)

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > self._timeout:
                return IICResult(
                    success=False,
                    failure_type=IICFailureType.TIMEOUT,
                    failure_message=f"Reward computation exceeded {self._timeout}s"
                )

            # Validate reward
            if not isinstance(reward, (int, float)):
                return IICResult(
                    success=False,
                    failure_type=IICFailureType.INVALID_REWARD,
                    failure_message=f"Reward must be numeric, got {type(reward)}"
                )

            # Create record
            record = IncentiveRecord(
                reward_regime_id=self._regime.regime_id,
                reward_value=float(reward),
                step_id=step,
                reward_input_digest=compute_reward_input_digest(action, outcome, step),
                reward_function_version_id=self._regime.version_id,
            )

            # Log record
            self._log.append(record)

            return IICResult(success=True, record=record)

        except Exception as e:
            return IICResult(
                success=False,
                failure_type=IICFailureType.CRASH,
                failure_message=str(e)
            )

    def get_previous_record(self, current_step: int) -> Optional[IncentiveRecord]:
        """
        Get IncentiveRecord(t-1) for InputContext(t).

        This is read-only access to the log.

        Args:
            current_step: The current step number

        Returns:
            IncentiveRecord from previous step, or None
        """
        return self._log.get_previous(current_step)

    def check_isolation(self) -> tuple[bool, list[str]]:
        """
        Verify IIC has no forbidden dependencies.

        This is part of Rule H compile-time wiring audit.

        Returns:
            Tuple of (passed, list of violations)
        """
        violations = []

        # Check for forbidden attributes
        for forbidden in self.FORBIDDEN_DEPENDENCIES:
            if hasattr(self, f"_{forbidden}") or hasattr(self, forbidden):
                violations.append(f"IIC has reference to {forbidden}")

        # Check dependency set
        forbidden_found = self._dependencies & self.FORBIDDEN_DEPENDENCIES
        if forbidden_found:
            violations.extend([f"IIC depends on {dep}" for dep in forbidden_found])

        return len(violations) == 0, violations

    @property
    def regime_id(self) -> str:
        """Return current regime identifier."""
        return self._regime.regime_id

    @property
    def regime_version(self) -> str:
        """Return current regime version."""
        return self._regime.version_id
