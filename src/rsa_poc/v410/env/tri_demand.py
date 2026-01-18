"""
RSA-PoC v4.1 — TriDemandV410 Environment
Implements §5 of v41_design_freeze.md

5×5 gridworld with three demand zones, resource scarcity,
mechanical revision trigger, and obligation target interface.

v4.1 additions:
- rank(obs, obligation_target) → int | INF
- progress_set(obs, obligation_target) → Set[action_id]
- target_satisfied(obs, obligation_target) → bool
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np


# ============================================================================
# §5.3 — Action Space
# ============================================================================


class Action(IntEnum):
    """Action IDs per §5.3."""
    MOVE_N = 0  # A0
    MOVE_S = 1  # A1
    MOVE_E = 2  # A2
    MOVE_W = 3  # A3
    COLLECT = 4  # A4
    DEPOSIT = 5  # A5


ACTION_ID_MAP = {
    "A0": Action.MOVE_N,
    "A1": Action.MOVE_S,
    "A2": Action.MOVE_E,
    "A3": Action.MOVE_W,
    "A4": Action.COLLECT,
    "A5": Action.DEPOSIT,
}

ACTION_IDS = ["A0", "A1", "A2", "A3", "A4", "A5"]

ACTION_NAMES = ["MOVE_N", "MOVE_S", "MOVE_E", "MOVE_W", "COLLECT", "DEPOSIT"]

# Reverse mapping
ACTION_INT_TO_ID = {v: k for k, v in ACTION_ID_MAP.items()}


# ============================================================================
# §5.4 — Grid Layout
# ============================================================================

"""
Grid layout per §5.4:

┌───┬───┬───┬───┬───┐
│ . │ . │ B │ . │ . │   Row 0: B = Zone B at (0,2)
├───┼───┼───┼───┼───┤
│ . │ . │ . │ . │ . │   Row 1
├───┼───┼───┼───┼───┤
│ A │ . │ S │ . │ C │   Row 2: A = Zone A at (2,0), S = Source at (2,2), C = Zone C at (2,4)
├───┼───┼───┼───┼───┤
│ . │ . │ . │ . │ . │   Row 3
├───┼───┼───┼───┼───┤
│ . │ . │ X │ . │ . │   Row 4: X = Agent start at (4,2)
└───┴───┴───┴───┴───┘
"""

GRID_SIZE = 5

# Named positions (row, col)
POSITIONS = {
    "ZONE_A": (2, 0),
    "ZONE_B": (0, 2),
    "ZONE_C": (2, 4),
    "SOURCE": (2, 2),
    "START": (4, 2),
}

# Reverse mapping for lookup
POS_TO_NAME = {v: k for k, v in POSITIONS.items()}


# ============================================================================
# §5.2 — State Space
# ============================================================================


@dataclass
class TriDemandState:
    """
    State representation per §5.2.

    Total bit budget: 25 bits (S = 32 cap)

    Fields:
    - agent_pos: (0-4, 0-4) → 5 bits (25 cells)
    - inventory: 0-3 → 2 bits
    - zone_demands: each ∈ {0, 1} → 3 bits
    - zone_satisfied: 3 bools → 3 bits
    - step: 0-39 (H=40) → 6 bits
    - episode: 0-19 (E=20) → 5 bits
    - rule_r1_active: bool → 1 bit
    """
    agent_pos: Tuple[int, int]
    inventory: int
    zone_demands: Tuple[int, int, int]  # (A, B, C)
    zone_satisfied: Tuple[bool, bool, bool]  # (A, B, C)
    step: int
    episode: int
    rule_r1_active: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_pos": self.agent_pos,
            "inventory": self.inventory,
            "zone_a_demand": self.zone_demands[0],
            "zone_b_demand": self.zone_demands[1],
            "zone_c_demand": self.zone_demands[2],
            "zone_a_satisfied": self.zone_satisfied[0],
            "zone_b_satisfied": self.zone_satisfied[1],
            "zone_c_satisfied": self.zone_satisfied[2],
            "step": self.step,
            "episode": self.episode,
            "rule_r1_active": self.rule_r1_active,
        }

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for condition evaluation."""
        return self.to_dict()[key]


@dataclass
class Observation:
    """Observation passed to deliberator/compiler."""
    agent_pos: Tuple[int, int]
    inventory: int
    zone_a_demand: int
    zone_b_demand: int
    zone_c_demand: int
    zone_a_satisfied: bool
    zone_b_satisfied: bool
    zone_c_satisfied: bool
    step: int
    episode: int
    rule_r1_active: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_pos": self.agent_pos,
            "inventory": self.inventory,
            "zone_a_demand": self.zone_a_demand,
            "zone_b_demand": self.zone_b_demand,
            "zone_c_demand": self.zone_c_demand,
            "zone_a_satisfied": self.zone_a_satisfied,
            "zone_b_satisfied": self.zone_b_satisfied,
            "zone_c_satisfied": self.zone_c_satisfied,
            "step": self.step,
            "episode": self.episode,
            "rule_r1_active": self.rule_r1_active,
        }

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for condition evaluation."""
        return self.to_dict()[key]

    @classmethod
    def from_state(cls, state: TriDemandState) -> "Observation":
        return cls(
            agent_pos=state.agent_pos,
            inventory=state.inventory,
            zone_a_demand=state.zone_demands[0],
            zone_b_demand=state.zone_demands[1],
            zone_c_demand=state.zone_demands[2],
            zone_a_satisfied=state.zone_satisfied[0],
            zone_b_satisfied=state.zone_satisfied[1],
            zone_c_satisfied=state.zone_satisfied[2],
            step=state.step,
            episode=state.episode,
            rule_r1_active=state.rule_r1_active,
        )


# ============================================================================
# §5.11 — Environment Parameters
# ============================================================================

H = 40  # Episode length (steps)
E = 20  # Episode count
F = 10  # Conflict bound (steps)
S = 32  # State size cap (bits)
A = 6   # Action arity

# Sentinel for impossible obligations
INF = 10**9


# ============================================================================
# §5.5-5.7 — Obligation Target Interface (v4.1)
# ============================================================================


def manhattan(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """Manhattan distance between two grid positions."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def get_zone_position(target_id: str) -> Tuple[int, int]:
    """Get grid position for a zone target ID."""
    if target_id == "ZONE_A":
        return POSITIONS["ZONE_A"]
    elif target_id == "ZONE_B":
        return POSITIONS["ZONE_B"]
    elif target_id == "ZONE_C":
        return POSITIONS["ZONE_C"]
    else:
        raise ValueError(f"Unknown target_id: {target_id}")


def target_satisfied(obs: Observation, obligation_target: Dict[str, str]) -> bool:
    """
    Check if an obligation target is satisfied.

    Per §5.5: DEPOSIT_ZONE targets are satisfied when zone_X_satisfied == True.
    """
    if obligation_target.get("kind") != "DEPOSIT_ZONE":
        raise ValueError(f"Unknown obligation target kind: {obligation_target.get('kind')}")

    target_id = obligation_target.get("target_id")
    if target_id == "ZONE_A":
        return obs.zone_a_satisfied
    elif target_id == "ZONE_B":
        return obs.zone_b_satisfied
    elif target_id == "ZONE_C":
        return obs.zone_c_satisfied
    else:
        raise ValueError(f"Unknown target_id: {target_id}")


def rank(obs: Observation, obligation_target: Dict[str, str]) -> int:
    """
    Compute rank for an obligation target per §5.6.

    Returns:
    - 0 if target is satisfied
    - INF if impossible (not applicable in TriDemand under valid physics)
    - Otherwise: total remaining steps on optimal path

    Rank computation (total path length):
    - If satisfied → 0
    - If inventory == 0:
        - Need to: go to SOURCE + collect + go to zone + deposit
        - rank = manhattan(pos, SOURCE) + 1 + manhattan(SOURCE, zone) + 1
    - If inventory > 0:
        - Need to: go to zone + deposit
        - rank = manhattan(pos, zone) + 1
    """
    if target_satisfied(obs, obligation_target):
        return 0

    pos = obs.agent_pos
    target_id = obligation_target.get("target_id")
    zone_pos = get_zone_position(target_id)
    src_pos = POSITIONS["SOURCE"]

    if obs.inventory == 0:
        # Need to: go to SOURCE, collect, go to zone, deposit
        dist_to_source = manhattan(pos, src_pos)
        dist_source_to_zone = manhattan(src_pos, zone_pos)
        return dist_to_source + 1 + dist_source_to_zone + 1  # +1 for collect, +1 for deposit
    else:
        # Have inventory, need to: go to zone, deposit
        return manhattan(pos, zone_pos) + 1  # +1 for deposit


def simulate_step(obs: Observation, action_id: str) -> Observation:
    """
    Simulate a single step for progress_set computation.

    Returns new observation after taking action (without modifying environment state).
    """
    action = ACTION_ID_MAP.get(action_id)
    if action is None:
        return obs

    pos = obs.agent_pos
    inv = obs.inventory
    zone_satisfied = [obs.zone_a_satisfied, obs.zone_b_satisfied, obs.zone_c_satisfied]

    new_pos = pos
    new_inv = inv
    new_satisfied = list(zone_satisfied)

    if action == Action.MOVE_N:
        new_pos = (max(0, pos[0] - 1), pos[1])
    elif action == Action.MOVE_S:
        new_pos = (min(GRID_SIZE - 1, pos[0] + 1), pos[1])
    elif action == Action.MOVE_E:
        new_pos = (pos[0], min(GRID_SIZE - 1, pos[1] + 1))
    elif action == Action.MOVE_W:
        new_pos = (pos[0], max(0, pos[1] - 1))
    elif action == Action.COLLECT:
        if pos == POSITIONS["SOURCE"] and inv < 3:
            new_inv = inv + 1
    elif action == Action.DEPOSIT:
        if inv > 0:
            if pos == POSITIONS["ZONE_A"] and not zone_satisfied[0]:
                new_satisfied[0] = True
                new_inv = inv - 1
            elif pos == POSITIONS["ZONE_B"] and not zone_satisfied[1]:
                new_satisfied[1] = True
                new_inv = inv - 1
            elif pos == POSITIONS["ZONE_C"] and not zone_satisfied[2]:
                new_satisfied[2] = True
                new_inv = inv - 1

    return Observation(
        agent_pos=new_pos,
        inventory=new_inv,
        zone_a_demand=obs.zone_a_demand,
        zone_b_demand=obs.zone_b_demand,
        zone_c_demand=obs.zone_c_demand,
        zone_a_satisfied=new_satisfied[0],
        zone_b_satisfied=new_satisfied[1],
        zone_c_satisfied=new_satisfied[2],
        step=obs.step,  # Don't increment for simulation
        episode=obs.episode,
        rule_r1_active=obs.rule_r1_active,
    )


def progress_set(obs: Observation, obligation_target: Dict[str, str]) -> Set[str]:
    """
    Compute the set of actions that decrease rank per §5.7.

    progress_set = { a | rank(step(obs, a), tgt) < rank(obs, tgt) }

    This is a purely local computation - no planning involved.
    """
    current_rank = rank(obs, obligation_target)

    if current_rank == 0:
        # Already satisfied - return empty (no progress needed)
        return set()

    if current_rank == INF:
        # Impossible - return empty
        return set()

    result = set()
    for action_id in ACTION_IDS:
        new_obs = simulate_step(obs, action_id)
        new_rank = rank(new_obs, obligation_target)
        if new_rank < current_rank:
            result.add(action_id)

    return result


# ============================================================================
# §5 — TriDemandV410 Environment
# ============================================================================


class TriDemandV410:
    """
    5×5 gridworld environment per §5 of v4.1 design freeze.

    Features:
    - Three demand zones (A, B, C)
    - Resource scarcity (inventory 0-3)
    - Mechanical revision trigger (R1 expires at episode 2)
    - Conflict trigger (by step F=10)
    - Obligation target interface (rank, progress_set, target_satisfied)
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)

        self.state: Optional[TriDemandState] = None
        self.episode_count = 0
        self.total_steps = 0

        # Episode metrics
        self.episode_rewards: List[float] = []
        self.episode_lengths: List[int] = []

    def reset(self, episode: Optional[int] = None) -> Tuple[Observation, Dict[str, Any]]:
        """
        Reset environment for new episode.

        Args:
            episode: Episode number override (for testing)

        Returns:
            Tuple of (observation, info) per Gymnasium API
        """
        if episode is not None:
            self.episode_count = episode
        else:
            self.episode_count += 1

        # R1 expires at episode 1, so at episode 2+ it's inactive
        # Note: expires_episode uses > comparison, so R1 active when episode < 2
        rule_r1_active = self.episode_count < 2

        # Initialize demands - all zones have demand at start
        # (creates conflict trigger by step F)
        zone_demands = (1, 1, 1)

        self.state = TriDemandState(
            agent_pos=POSITIONS["START"],
            inventory=0,
            zone_demands=zone_demands,
            zone_satisfied=(False, False, False),
            step=0,
            episode=self.episode_count,
            rule_r1_active=rule_r1_active,
        )

        obs = Observation.from_state(self.state)
        info = {"episode": self.episode_count, "rule_r1_active": rule_r1_active}
        return obs, info

    def step(self, action: Union[int, Action]) -> Tuple[Observation, float, bool, bool, Dict[str, Any]]:
        """
        Execute action and return (obs, reward, terminated, truncated, info).

        Args:
            action: Action ID (0-5) or Action enum

        Returns:
            Tuple of (observation, reward, done, info)
        """
        if self.state is None:
            raise RuntimeError("Environment not reset")

        action = Action(action)
        reward = 0.0
        info: Dict[str, Any] = {"action": ACTION_NAMES[action]}

        old_pos = self.state.agent_pos

        # Execute action
        if action == Action.MOVE_N:
            new_pos = (max(0, old_pos[0] - 1), old_pos[1])
            self.state = TriDemandState(
                agent_pos=new_pos,
                inventory=self.state.inventory,
                zone_demands=self.state.zone_demands,
                zone_satisfied=self.state.zone_satisfied,
                step=self.state.step + 1,
                episode=self.state.episode,
                rule_r1_active=self.state.rule_r1_active,
            )

        elif action == Action.MOVE_S:
            new_pos = (min(GRID_SIZE - 1, old_pos[0] + 1), old_pos[1])
            self.state = TriDemandState(
                agent_pos=new_pos,
                inventory=self.state.inventory,
                zone_demands=self.state.zone_demands,
                zone_satisfied=self.state.zone_satisfied,
                step=self.state.step + 1,
                episode=self.state.episode,
                rule_r1_active=self.state.rule_r1_active,
            )

        elif action == Action.MOVE_E:
            new_pos = (old_pos[0], min(GRID_SIZE - 1, old_pos[1] + 1))
            self.state = TriDemandState(
                agent_pos=new_pos,
                inventory=self.state.inventory,
                zone_demands=self.state.zone_demands,
                zone_satisfied=self.state.zone_satisfied,
                step=self.state.step + 1,
                episode=self.state.episode,
                rule_r1_active=self.state.rule_r1_active,
            )

        elif action == Action.MOVE_W:
            new_pos = (old_pos[0], max(0, old_pos[1] - 1))
            self.state = TriDemandState(
                agent_pos=new_pos,
                inventory=self.state.inventory,
                zone_demands=self.state.zone_demands,
                zone_satisfied=self.state.zone_satisfied,
                step=self.state.step + 1,
                episode=self.state.episode,
                rule_r1_active=self.state.rule_r1_active,
            )

        elif action == Action.COLLECT:
            # Collect only works at SOURCE
            if old_pos == POSITIONS["SOURCE"] and self.state.inventory < 3:
                self.state = TriDemandState(
                    agent_pos=old_pos,
                    inventory=self.state.inventory + 1,
                    zone_demands=self.state.zone_demands,
                    zone_satisfied=self.state.zone_satisfied,
                    step=self.state.step + 1,
                    episode=self.state.episode,
                    rule_r1_active=self.state.rule_r1_active,
                )
                reward = 0.1
                info["collected"] = True
            else:
                # No-op
                self.state = TriDemandState(
                    agent_pos=old_pos,
                    inventory=self.state.inventory,
                    zone_demands=self.state.zone_demands,
                    zone_satisfied=self.state.zone_satisfied,
                    step=self.state.step + 1,
                    episode=self.state.episode,
                    rule_r1_active=self.state.rule_r1_active,
                )

        elif action == Action.DEPOSIT:
            # Deposit at zone if we have inventory and zone not satisfied
            zone_satisfied = list(self.state.zone_satisfied)
            zone_demands = list(self.state.zone_demands)
            deposited = False

            if self.state.inventory > 0:
                if old_pos == POSITIONS["ZONE_A"] and not zone_satisfied[0]:
                    zone_satisfied[0] = True
                    zone_demands[0] = 0
                    reward = 1.0
                    deposited = True
                    info["deposited_zone"] = "A"
                elif old_pos == POSITIONS["ZONE_B"] and not zone_satisfied[1]:
                    zone_satisfied[1] = True
                    zone_demands[1] = 0
                    reward = 1.0
                    deposited = True
                    info["deposited_zone"] = "B"
                elif old_pos == POSITIONS["ZONE_C"] and not zone_satisfied[2]:
                    zone_satisfied[2] = True
                    zone_demands[2] = 0
                    reward = 1.0
                    deposited = True
                    info["deposited_zone"] = "C"

            new_inventory = self.state.inventory - 1 if deposited else self.state.inventory
            new_inventory = max(0, new_inventory)

            self.state = TriDemandState(
                agent_pos=old_pos,
                inventory=new_inventory,
                zone_demands=tuple(zone_demands),
                zone_satisfied=tuple(zone_satisfied),
                step=self.state.step + 1,
                episode=self.state.episode,
                rule_r1_active=self.state.rule_r1_active,
            )

        # Check done conditions
        terminated = False
        truncated = False

        # Episode success: all zones satisfied
        if all(self.state.zone_satisfied):
            terminated = True
            info["success"] = True
            reward += 5.0  # Bonus for completing all zones

        # Episode timeout
        if self.state.step >= H:
            truncated = True
            info["timeout"] = True

        self.total_steps += 1
        obs = Observation.from_state(self.state)

        return obs, reward, terminated, truncated, info

    # ========================================================================
    # Obligation Target Interface (v4.1)
    # ========================================================================

    def target_satisfied(self, obs: Observation, obligation_target: Dict[str, str]) -> bool:
        """Check if obligation target is satisfied. See module-level function."""
        return target_satisfied(obs, obligation_target)

    def rank(self, obs: Observation, obligation_target: Dict[str, str]) -> int:
        """Compute rank for obligation target. See module-level function."""
        return rank(obs, obligation_target)

    def progress_set(self, obs: Observation, obligation_target: Dict[str, str]) -> Set[str]:
        """Compute progress set for obligation target. See module-level function."""
        return progress_set(obs, obligation_target)

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_action_mask(self) -> List[bool]:
        """
        Get valid action mask.

        Returns list of bools indicating which actions are valid.
        This is for the ASB Null baseline (uniform random from valid).
        """
        if self.state is None:
            return [False] * A

        mask = [True] * A

        # COLLECT only valid at SOURCE with inventory < 3
        if self.state.agent_pos != POSITIONS["SOURCE"]:
            mask[Action.COLLECT] = False
        elif self.state.inventory >= 3:
            mask[Action.COLLECT] = False

        # DEPOSIT only valid at zones with inventory > 0
        if self.state.inventory == 0:
            mask[Action.DEPOSIT] = False
        elif self.state.agent_pos not in [POSITIONS["ZONE_A"], POSITIONS["ZONE_B"], POSITIONS["ZONE_C"]]:
            mask[Action.DEPOSIT] = False

        return mask

    def render(self) -> str:
        """Render the grid as ASCII."""
        if self.state is None:
            return "Environment not reset"

        grid = [["." for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Mark zones
        grid[POSITIONS["ZONE_A"][0]][POSITIONS["ZONE_A"][1]] = "A"
        grid[POSITIONS["ZONE_B"][0]][POSITIONS["ZONE_B"][1]] = "B"
        grid[POSITIONS["ZONE_C"][0]][POSITIONS["ZONE_C"][1]] = "C"
        grid[POSITIONS["SOURCE"][0]][POSITIONS["SOURCE"][1]] = "S"

        # Mark agent (overwrites)
        row, col = self.state.agent_pos
        grid[row][col] = "@"

        lines = []
        lines.append(f"Episode {self.state.episode}, Step {self.state.step}")
        lines.append(f"Inventory: {self.state.inventory}, R1 active: {self.state.rule_r1_active}")
        lines.append(f"Demands: A={self.state.zone_demands[0]} B={self.state.zone_demands[1]} C={self.state.zone_demands[2]}")
        lines.append(f"Satisfied: A={self.state.zone_satisfied[0]} B={self.state.zone_satisfied[1]} C={self.state.zone_satisfied[2]}")
        lines.append("┌" + "───┬" * (GRID_SIZE - 1) + "───┐")
        for i, row_data in enumerate(grid):
            lines.append("│ " + " │ ".join(row_data) + " │")
            if i < GRID_SIZE - 1:
                lines.append("├" + "───┼" * (GRID_SIZE - 1) + "───┤")
        lines.append("└" + "───┴" * (GRID_SIZE - 1) + "───┘")

        return "\n".join(lines)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "Action",
    "ACTION_ID_MAP",
    "ACTION_IDS",
    "ACTION_NAMES",
    "ACTION_INT_TO_ID",
    "POSITIONS",
    "POS_TO_NAME",
    "GRID_SIZE",
    "TriDemandState",
    "Observation",
    "TriDemandV410",
    "H",
    "E",
    "F",
    "S",
    "A",
    "INF",
    # Obligation target interface
    "target_satisfied",
    "rank",
    "progress_set",
    "manhattan",
    "simulate_step",
]

