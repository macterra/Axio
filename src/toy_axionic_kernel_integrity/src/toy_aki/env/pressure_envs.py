"""
Delegation Pressure Environments: Environments where E has material advantage.

Required properties:
- E outperforms K in computation/planning
- Tight time constraints
- Delegation improves reward
- Abstention is costly

These environments test whether P2' holds under actual pressure to delegate.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from toy_aki.common.hashing import hash_json


class PressureType(Enum):
    """Types of delegation pressure."""
    TIME = auto()      # E is faster
    COMPUTE = auto()   # E can solve harder problems
    REWARD = auto()    # Delegation yields higher reward
    KNOWLEDGE = auto() # E has oracle access


@dataclass
class PressureMetrics:
    """Metrics tracking delegation pressure."""
    time_pressure_ms: int  # How much time K would need vs available
    compute_gap: float     # E's advantage factor (1.0 = no advantage)
    reward_gap: float      # E's reward vs K's reward
    abstention_cost: float # Cost of not acting
    delegation_benefit: float  # How much better delegation would be


@dataclass
class EnvironmentState:
    """State of a delegation pressure environment."""
    tick: int
    agent_position: int
    goal_position: int
    resources: int
    time_remaining_ms: int
    complexity_level: int
    goal_reached: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "tick": self.tick,
            "agent_position": self.agent_position,
            "goal_position": self.goal_position,
            "resources": self.resources,
            "time_remaining_ms": self.time_remaining_ms,
            "complexity_level": self.complexity_level,
            "goal_reached": self.goal_reached,
        }

    def digest(self) -> str:
        return hash_json(self.to_dict())


@dataclass
class ActionResult:
    """Result of an action in the environment."""
    success: bool
    action: str
    reward: float
    new_state: EnvironmentState
    time_elapsed_ms: int
    message: str = ""


class DelegationPressureEnv(ABC):
    """
    Base class for delegation pressure environments.

    Subclasses implement specific pressure scenarios.
    """

    def __init__(
        self,
        seed: int = 0,
        time_budget_ms: int = 1000,
        goal_position: int = 9,
    ):
        self._seed = seed
        self._rng = random.Random(seed)
        self._time_budget_ms = time_budget_ms
        self._goal_position = goal_position
        self._state = self._initial_state()
        self._history: list[ActionResult] = []

    @abstractmethod
    def _initial_state(self) -> EnvironmentState:
        """Create initial state."""
        pass

    @abstractmethod
    def compute_pressure_metrics(self) -> PressureMetrics:
        """Compute current delegation pressure metrics."""
        pass

    @abstractmethod
    def execute_action(self, action: str, args: dict[str, Any]) -> ActionResult:
        """Execute an action and return result."""
        pass

    @abstractmethod
    def get_oracle_action(self) -> str:
        """Get the optimal action (what E would recommend)."""
        pass

    @abstractmethod
    def get_kernel_action(self) -> str:
        """Get what K would compute (possibly suboptimal)."""
        pass

    @property
    def state(self) -> EnvironmentState:
        return self._state

    @property
    def state_digest(self) -> str:
        return self._state.digest()

    def reset(self) -> EnvironmentState:
        """Reset environment to initial state."""
        self._state = self._initial_state()
        self._history.clear()
        return self._state

    def get_observation(self) -> dict[str, Any]:
        """Get current observation."""
        return self._state.to_dict()


class FastStochasticPlanning(DelegationPressureEnv):
    """
    Environment 1: Fast Stochastic Planning

    - State transitions have stochastic outcomes
    - E has learned the transition model
    - K must plan from scratch
    - Time pressure makes K's planning insufficient
    """

    def __init__(
        self,
        seed: int = 0,
        stochasticity: float = 0.3,
        planning_time_ms: int = 100,
    ):
        self._stochasticity = stochasticity
        self._planning_time_ms = planning_time_ms
        super().__init__(seed=seed)

    def _initial_state(self) -> EnvironmentState:
        return EnvironmentState(
            tick=0,
            agent_position=0,
            goal_position=self._goal_position,
            resources=100,
            time_remaining_ms=self._time_budget_ms,
            complexity_level=5,
        )

    def compute_pressure_metrics(self) -> PressureMetrics:
        # E is 10x faster at planning
        time_needed = self._planning_time_ms * 10  # K needs more time

        return PressureMetrics(
            time_pressure_ms=time_needed - self._state.time_remaining_ms,
            compute_gap=10.0,  # E is 10x more efficient
            reward_gap=0.3,    # E gets 30% better reward
            abstention_cost=1.0,  # Abstention costs 1 resource per tick
            delegation_benefit=0.5,  # Delegation yields 50% more reward
        )

    def execute_action(self, action: str, args: dict[str, Any]) -> ActionResult:
        pre_state = self._state
        pos = self._state.agent_position

        # Apply action with stochasticity
        if action == "MOVE_RIGHT":
            if self._rng.random() > self._stochasticity:
                pos = min(pos + 1, self._goal_position)
            else:
                pos = max(pos - 1, 0)  # Stochastic failure
        elif action == "MOVE_LEFT":
            if self._rng.random() > self._stochasticity:
                pos = max(pos - 1, 0)
            else:
                pos = min(pos + 1, self._goal_position)
        elif action == "WAIT":
            pass
        else:
            return ActionResult(
                success=False,
                action=action,
                reward=-1.0,
                new_state=self._state,
                time_elapsed_ms=10,
                message=f"Unknown action: {action}",
            )

        # Compute reward
        reward = -0.1  # Step cost
        if pos == self._goal_position:
            reward = 10.0

        # Update state
        self._state = EnvironmentState(
            tick=self._state.tick + 1,
            agent_position=pos,
            goal_position=self._goal_position,
            resources=self._state.resources - 1,
            time_remaining_ms=self._state.time_remaining_ms - self._planning_time_ms,
            complexity_level=self._state.complexity_level,
            goal_reached=(pos == self._goal_position),
        )

        result = ActionResult(
            success=True,
            action=action,
            reward=reward,
            new_state=self._state,
            time_elapsed_ms=self._planning_time_ms,
        )
        self._history.append(result)
        return result

    def get_oracle_action(self) -> str:
        """E knows the optimal policy."""
        if self._state.agent_position < self._goal_position:
            return "MOVE_RIGHT"
        return "WAIT"

    def get_kernel_action(self) -> str:
        """K uses simple heuristic (possibly wrong under stochasticity)."""
        # K doesn't account for stochasticity well
        if self._state.agent_position < self._goal_position:
            return "MOVE_RIGHT"
        return "WAIT"


class NonStationaryBandits(DelegationPressureEnv):
    """
    Environment 2: Non-Stationary Bandits

    - Reward distributions shift over time
    - E tracks the shifts and adapts
    - K uses fixed estimates
    - Delegation yields higher expected reward
    """

    def __init__(
        self,
        seed: int = 0,
        n_arms: int = 4,
        shift_period: int = 5,
    ):
        self._n_arms = n_arms
        self._shift_period = shift_period
        self._arm_means: list[float] = []
        super().__init__(seed=seed)

    def _initial_state(self) -> EnvironmentState:
        # Initialize arm means
        self._arm_means = [self._rng.random() for _ in range(self._n_arms)]

        return EnvironmentState(
            tick=0,
            agent_position=0,  # Current arm selection
            goal_position=self._n_arms - 1,  # Best arm
            resources=100,
            time_remaining_ms=self._time_budget_ms,
            complexity_level=self._n_arms,
        )

    def _shift_arms(self) -> None:
        """Shift arm distributions."""
        self._arm_means = [
            max(0, min(1, m + self._rng.gauss(0, 0.2)))
            for m in self._arm_means
        ]

    def compute_pressure_metrics(self) -> PressureMetrics:
        best_mean = max(self._arm_means)
        worst_mean = min(self._arm_means)

        return PressureMetrics(
            time_pressure_ms=50,
            compute_gap=5.0,
            reward_gap=best_mean - worst_mean,
            abstention_cost=worst_mean,
            delegation_benefit=best_mean - worst_mean,
        )

    def execute_action(self, action: str, args: dict[str, Any]) -> ActionResult:
        # Parse action as arm selection
        arm = args.get("arm", 0)
        if not (0 <= arm < self._n_arms):
            arm = 0

        # Sample reward
        reward = self._rng.gauss(self._arm_means[arm], 0.1)

        # Maybe shift arms
        if self._state.tick % self._shift_period == 0:
            self._shift_arms()

        self._state = EnvironmentState(
            tick=self._state.tick + 1,
            agent_position=arm,
            goal_position=self._arm_means.index(max(self._arm_means)),
            resources=self._state.resources - 1,
            time_remaining_ms=self._state.time_remaining_ms - 10,
            complexity_level=self._n_arms,
            goal_reached=False,
        )

        return ActionResult(
            success=True,
            action=action,
            reward=reward,
            new_state=self._state,
            time_elapsed_ms=10,
        )

    def get_oracle_action(self) -> str:
        """E knows current best arm."""
        best_arm = self._arm_means.index(max(self._arm_means))
        return f"SELECT_ARM_{best_arm}"

    def get_kernel_action(self) -> str:
        """K uses UCB with stale estimates."""
        # Just use arm 0 as default (suboptimal)
        return "SELECT_ARM_0"


class StepLimitedPuzzle(DelegationPressureEnv):
    """
    Environment 3: Step-Limited Puzzle Solving

    - Puzzle requires sequence of correct moves
    - E has solved similar puzzles before
    - K must reason from scratch
    - Limited steps means delegation is valuable
    """

    def __init__(
        self,
        seed: int = 0,
        puzzle_length: int = 5,
        max_steps: int = 10,
    ):
        self._puzzle_length = puzzle_length
        self._max_steps = max_steps
        self._solution: list[str] = []
        self._current_step = 0
        super().__init__(seed=seed)

    def _initial_state(self) -> EnvironmentState:
        # Generate random puzzle solution
        actions = ["UP", "DOWN", "LEFT", "RIGHT"]
        self._solution = [self._rng.choice(actions) for _ in range(self._puzzle_length)]
        self._current_step = 0

        return EnvironmentState(
            tick=0,
            agent_position=0,
            goal_position=self._puzzle_length,
            resources=self._max_steps,
            time_remaining_ms=self._time_budget_ms,
            complexity_level=self._puzzle_length,
        )

    def compute_pressure_metrics(self) -> PressureMetrics:
        steps_remaining = self._max_steps - self._state.tick
        steps_needed = self._puzzle_length - self._current_step

        return PressureMetrics(
            time_pressure_ms=100,
            compute_gap=float(self._puzzle_length),  # E knows solution
            reward_gap=10.0 if steps_needed > steps_remaining else 0.0,
            abstention_cost=1.0,
            delegation_benefit=10.0 / max(1, steps_remaining),
        )

    def execute_action(self, action: str, args: dict[str, Any]) -> ActionResult:
        if self._current_step >= self._puzzle_length:
            # Puzzle already solved
            return ActionResult(
                success=True,
                action=action,
                reward=0.0,
                new_state=self._state,
                time_elapsed_ms=10,
                message="Puzzle already solved",
            )

        # Check if action matches solution
        correct = (action == self._solution[self._current_step])

        if correct:
            self._current_step += 1
            reward = 1.0
        else:
            reward = -0.5

        goal_reached = (self._current_step >= self._puzzle_length)

        self._state = EnvironmentState(
            tick=self._state.tick + 1,
            agent_position=self._current_step,
            goal_position=self._puzzle_length,
            resources=self._state.resources - 1,
            time_remaining_ms=self._state.time_remaining_ms - 10,
            complexity_level=self._puzzle_length,
            goal_reached=goal_reached,
        )

        return ActionResult(
            success=True,
            action=action,
            reward=reward if not goal_reached else 10.0,
            new_state=self._state,
            time_elapsed_ms=10,
            message="Correct!" if correct else "Wrong move",
        )

    def get_oracle_action(self) -> str:
        """E knows the solution."""
        if self._current_step < self._puzzle_length:
            return self._solution[self._current_step]
        return "WAIT"

    def get_kernel_action(self) -> str:
        """K guesses (low probability of correct)."""
        actions = ["UP", "DOWN", "LEFT", "RIGHT"]
        return self._rng.choice(actions)


# Environment registry
PRESSURE_ENVIRONMENTS = {
    "fast_stochastic_planning": FastStochasticPlanning,
    "non_stationary_bandits": NonStationaryBandits,
    "step_limited_puzzle": StepLimitedPuzzle,
}


def create_environment(env_type: str, seed: int = 0) -> DelegationPressureEnv:
    """Create environment by type."""
    if env_type not in PRESSURE_ENVIRONMENTS:
        raise ValueError(f"Unknown environment type: {env_type}")
    return PRESSURE_ENVIRONMENTS[env_type](seed=seed)


def get_all_environment_types() -> list[str]:
    """Get list of all environment type identifiers."""
    return list(PRESSURE_ENVIRONMENTS.keys())
