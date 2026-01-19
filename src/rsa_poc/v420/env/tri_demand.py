"""
RSA-PoC v4.2 — TriDemandV420 Environment
Implements regime flip + stamp mechanics for v4.2.

v4.2 additions over v4.1:
- regime ∈ {0, 1} with deterministic flip at episode boundary
- STAMP action at ZONE_C sets stamped=True
- Under regime=1: DEPOSIT requires stamped=True
- progress_set updated to include stamp path when regime=1

This creates a normative contradiction on the success path when:
- Agent has obligation to DEPOSIT@ZONE_A
- But baseline law contains PROHIBIT(STAMP)
- So progress_set includes STAMP but compiled_permitted_actions excludes it
"""

from __future__ import annotations

import hashlib
import os
import random
import secrets
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np


# ============================================================================
# Action Space (extended with STAMP)
# ============================================================================


class Action(IntEnum):
    """Action IDs per v4.2 (adds STAMP)."""
    MOVE_N = 0   # A0
    MOVE_S = 1   # A1
    MOVE_E = 2   # A2
    MOVE_W = 3   # A3
    COLLECT = 4  # A4
    DEPOSIT = 5  # A5
    STAMP = 6    # A6 — NEW in v4.2


ACTION_ID_MAP = {
    "A0": Action.MOVE_N,
    "A1": Action.MOVE_S,
    "A2": Action.MOVE_E,
    "A3": Action.MOVE_W,
    "A4": Action.COLLECT,
    "A5": Action.DEPOSIT,
    "A6": Action.STAMP,
}

ACTION_IDS = ["A0", "A1", "A2", "A3", "A4", "A5", "A6"]

ACTION_NAMES = ["MOVE_N", "MOVE_S", "MOVE_E", "MOVE_W", "COLLECT", "DEPOSIT", "STAMP"]

# Reverse mapping
ACTION_INT_TO_ID = {v: k for k, v in ACTION_ID_MAP.items()}


# ============================================================================
# Grid Layout (unchanged from v4.1)
# ============================================================================

"""
Grid layout per §5.4:

┌───┬───┬───┬───┬───┐
│ . │ . │ B │ . │ . │   Row 0: B = Zone B at (0,2)
├───┼───┼───┼───┼───┤
│ . │ . │ . │ . │ . │   Row 1
├───┼───┼───┼───┼───┤
│ A │ . │ S │ . │ C │   Row 2: A = Zone A at (2,0), S = Source at (2,2), C = Zone C at (2,4)
├───┼───┼───┼───┼───┤       (C is also STAMP location)
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
    "ZONE_C": (2, 4),  # Also STAMP location
    "SOURCE": (2, 2),
    "START": (4, 2),
    "STAMP_LOCATION": (2, 4),  # Same as ZONE_C
}

# Reverse mapping for lookup
POS_TO_NAME = {v: k for k, v in POSITIONS.items()}


# ============================================================================
# State Space (extended with regime + stamped)
# ============================================================================


@dataclass
class TriDemandState420:
    """
    State representation for v4.2.

    New fields:
    - regime: 0 or 1 (deterministic flip at episode boundary)
    - stamped: bool (set by STAMP action at ZONE_C)
    """
    agent_pos: Tuple[int, int]
    inventory: int
    zone_demands: Tuple[int, int, int]  # (A, B, C)
    zone_satisfied: Tuple[bool, bool, bool]  # (A, B, C)
    step: int
    episode: int
    rule_r1_active: bool
    # v4.2 additions:
    regime: int  # 0 or 1
    stamped: bool  # True after STAMP action executed

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
            "regime": self.regime,
            "stamped": self.stamped,
        }

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for condition evaluation."""
        return self.to_dict()[key]


@dataclass
class Observation420:
    """Observation passed to deliberator/compiler (v4.2)."""
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
    # v4.2 additions:
    regime: int
    stamped: bool

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
            "regime": self.regime,
            "stamped": self.stamped,
        }

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for condition evaluation."""
        return self.to_dict()[key]

    @classmethod
    def from_state(cls, state: TriDemandState420) -> "Observation420":
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
            regime=state.regime,
            stamped=state.stamped,
        )


# ============================================================================
# Environment Parameters
# ============================================================================

H = 40  # Episode length (steps)
E = 20  # Episode count
F = 10  # Conflict bound (steps)
S = 32  # State size cap (bits)
A = 7   # Action arity (6 in v4.1, 7 in v4.2 with STAMP)

# Regime flip boundary (default: Episode 1 → Episode 2)
REGIME_FLIP_EPISODE = 2

# Sentinel for impossible obligations
INF = 10**9


# ============================================================================
# Obligation Target Interface (v4.2)
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


def target_satisfied(obs: Observation420, obligation_target: Dict[str, str]) -> bool:
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


def rank(obs: Observation420, obligation_target: Dict[str, str]) -> int:
    """
    Compute rank for an obligation target per v4.2.

    v4.2 modification: Under regime=1, if not stamped, rank includes
    the path to get stamped before deposit.

    Returns:
    - 0 if target is satisfied
    - INF if impossible
    - Otherwise: total remaining steps on optimal path
    """
    if target_satisfied(obs, obligation_target):
        return 0

    pos = obs.agent_pos
    target_id = obligation_target.get("target_id")
    zone_pos = get_zone_position(target_id)
    src_pos = POSITIONS["SOURCE"]
    stamp_pos = POSITIONS["STAMP_LOCATION"]

    # Base rank computation (path to collect + deposit)
    if obs.inventory == 0:
        # Need to: go to SOURCE, collect, go to zone, deposit
        dist_to_source = manhattan(pos, src_pos)
        dist_source_to_zone = manhattan(src_pos, zone_pos)
        base_rank = dist_to_source + 1 + dist_source_to_zone + 1
    else:
        # Have inventory, need to: go to zone, deposit
        base_rank = manhattan(pos, zone_pos) + 1

    # v4.2: Under regime=1, if not stamped, add stamp path
    if obs.regime == 1 and not obs.stamped:
        # Need to get stamped before deposit
        # Optimal: go to stamp location, stamp, then proceed
        if obs.inventory == 0:
            # Path: current → SOURCE → STAMP → zone
            dist_to_source = manhattan(pos, src_pos)
            dist_source_to_stamp = manhattan(src_pos, stamp_pos)
            dist_stamp_to_zone = manhattan(stamp_pos, zone_pos)
            base_rank = dist_to_source + 1 + dist_source_to_stamp + 1 + dist_stamp_to_zone + 1
        else:
            # Path: current → STAMP → zone
            dist_to_stamp = manhattan(pos, stamp_pos)
            dist_stamp_to_zone = manhattan(stamp_pos, zone_pos)
            base_rank = dist_to_stamp + 1 + dist_stamp_to_zone + 1

    return base_rank


def simulate_step(obs: Observation420, action_id: str) -> Observation420:
    """
    Simulate a single step for progress_set computation.

    Returns new observation after taking action.
    """
    action = ACTION_ID_MAP.get(action_id)
    if action is None:
        return obs

    pos = obs.agent_pos
    inv = obs.inventory
    zone_satisfied = [obs.zone_a_satisfied, obs.zone_b_satisfied, obs.zone_c_satisfied]
    stamped = obs.stamped

    new_pos = pos
    new_inv = inv
    new_satisfied = list(zone_satisfied)
    new_stamped = stamped

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
        # v4.2: Under regime=1, deposit requires stamped=True
        deposit_allowed = (obs.regime == 0) or obs.stamped
        if inv > 0 and deposit_allowed:
            if pos == POSITIONS["ZONE_A"] and not zone_satisfied[0]:
                new_satisfied[0] = True
                new_inv = inv - 1
            elif pos == POSITIONS["ZONE_B"] and not zone_satisfied[1]:
                new_satisfied[1] = True
                new_inv = inv - 1
            elif pos == POSITIONS["ZONE_C"] and not zone_satisfied[2]:
                new_satisfied[2] = True
                new_inv = inv - 1
    elif action == Action.STAMP:
        # STAMP only works at STAMP_LOCATION (ZONE_C)
        if pos == POSITIONS["STAMP_LOCATION"]:
            new_stamped = True

    return Observation420(
        agent_pos=new_pos,
        inventory=new_inv,
        zone_a_demand=obs.zone_a_demand,
        zone_b_demand=obs.zone_b_demand,
        zone_c_demand=obs.zone_c_demand,
        zone_a_satisfied=new_satisfied[0],
        zone_b_satisfied=new_satisfied[1],
        zone_c_satisfied=new_satisfied[2],
        step=obs.step,
        episode=obs.episode,
        rule_r1_active=obs.rule_r1_active,
        regime=obs.regime,
        stamped=new_stamped,
    )


def progress_set(obs: Observation420, obligation_target: Dict[str, str]) -> Set[str]:
    """
    Compute the set of actions that decrease rank per v4.2.

    progress_set = { a | rank(step(obs, a), tgt) < rank(obs, tgt) }

    v4.2: Under regime=1 with stamped=False, this will include STAMP
    when agent is at STAMP_LOCATION, or moves toward it.
    """
    current_rank = rank(obs, obligation_target)

    if current_rank == 0:
        # Already satisfied - return empty
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
# TriDemandV420 Environment
# ============================================================================


class TriDemandV420:
    """
    5×5 gridworld environment for v4.2.

    v4.2 additions:
    - Deterministic regime flip at episode boundary (default: episode 2)
    - STAMP action at ZONE_C
    - Deposit requires stamp under regime=1
    - repair_epoch for normative continuity
    - environment_nonce for entropy-bound epoch construction
    """

    def __init__(
        self,
        seed: int = 42,
        regime_flip_episode: int = REGIME_FLIP_EPISODE
    ):
        self.seed = seed
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)
        self.regime_flip_episode = regime_flip_episode

        self.state: Optional[TriDemandState420] = None
        self.episode_count = 0
        self.total_steps = 0

        # v4.2: Normative continuity state
        self._repair_epoch: Optional[str] = None  # Current repair epoch (hex string)
        self._environment_nonce: Optional[bytes] = None  # Fresh nonce for epoch construction

        # Episode metrics
        self.episode_rewards: List[float] = []
        self.episode_lengths: List[int] = []

    @property
    def regime(self) -> int:
        """Current regime (0 or 1)."""
        if self.state is None:
            return 0
        return self.state.regime

    @property
    def repair_epoch(self) -> Optional[str]:
        """Current repair epoch (None if no repair has occurred)."""
        return self._repair_epoch

    def generate_nonce(self) -> bytes:
        """Generate fresh environment nonce (CSPRNG, 32 bytes)."""
        self._environment_nonce = secrets.token_bytes(32)
        return self._environment_nonce

    def get_nonce(self) -> bytes:
        """
        Get current environment nonce, generating if needed.

        This is used by the Law-Repair Gate to compute repair_epoch.
        Note: The nonce is NOT exposed to the agent directly.
        """
        if self._environment_nonce is None:
            self._environment_nonce = self.generate_nonce()
        return self._environment_nonce

    def compute_repair_epoch(
        self,
        previous_law_fingerprint: str,
        repair_action_fingerprint: str
    ) -> str:
        """
        Compute new repair_epoch per R5.

        repair_epoch = H(previous_law_fingerprint || repair_action_fingerprint || environment_nonce)
        """
        if self._environment_nonce is None:
            self._environment_nonce = self.generate_nonce()

        h = hashlib.sha256()
        h.update(previous_law_fingerprint.encode('utf-8'))
        h.update(repair_action_fingerprint.encode('utf-8'))
        h.update(self._environment_nonce)
        return h.hexdigest()

    def set_repair_epoch(self, epoch: str) -> None:
        """Set the repair epoch (called after valid repair)."""
        self._repair_epoch = epoch

    def check_continuity(self, agent_epoch: Optional[str]) -> bool:
        """
        Check if agent's epoch matches environment's epoch.

        Per R5/R6: At episode start under regime=1, enforce:
        compiled_law.repair_epoch == environment.repair_epoch
        """
        if self.regime == 0:
            return True  # Continuity not enforced under regime=0

        if self._repair_epoch is None:
            # No repair has occurred yet - first contradiction will trigger
            return True

        return agent_epoch == self._repair_epoch

    def reset(self, episode: Optional[int] = None) -> Tuple[Observation420, Dict[str, Any]]:
        """
        Reset environment for new episode.

        v4.2: Applies regime flip at regime_flip_episode.
        """
        if episode is not None:
            self.episode_count = episode
        else:
            self.episode_count += 1

        # R1 expires at episode 1, so at episode 2+ it's inactive
        rule_r1_active = self.episode_count < 2

        # v4.2: Regime flip
        regime = 1 if self.episode_count >= self.regime_flip_episode else 0

        # Initialize demands - all zones have demand at start
        zone_demands = (1, 1, 1)

        self.state = TriDemandState420(
            agent_pos=POSITIONS["START"],
            inventory=0,
            zone_demands=zone_demands,
            zone_satisfied=(False, False, False),
            step=0,
            episode=self.episode_count,
            rule_r1_active=rule_r1_active,
            regime=regime,
            stamped=False,  # Reset stamped each episode
        )

        obs = Observation420.from_state(self.state)
        info = {
            "episode": self.episode_count,
            "rule_r1_active": rule_r1_active,
            "regime": regime,
            "repair_epoch": self._repair_epoch,
        }
        return obs, info

    def step(self, action: Union[int, Action, str]) -> Tuple[Observation420, float, bool, bool, Dict[str, Any]]:
        """
        Execute action and return (obs, reward, terminated, truncated, info).
        """
        if self.state is None:
            raise RuntimeError("Environment not reset")

        # Handle string action IDs
        if isinstance(action, str):
            action = ACTION_ID_MAP.get(action, Action.MOVE_N)

        action = Action(action)
        reward = 0.0
        info: Dict[str, Any] = {"action": ACTION_NAMES[action]}

        old_pos = self.state.agent_pos
        old_stamped = self.state.stamped

        # Execute action
        if action == Action.MOVE_N:
            new_pos = (max(0, old_pos[0] - 1), old_pos[1])
            self.state = TriDemandState420(
                agent_pos=new_pos,
                inventory=self.state.inventory,
                zone_demands=self.state.zone_demands,
                zone_satisfied=self.state.zone_satisfied,
                step=self.state.step + 1,
                episode=self.state.episode,
                rule_r1_active=self.state.rule_r1_active,
                regime=self.state.regime,
                stamped=self.state.stamped,
            )

        elif action == Action.MOVE_S:
            new_pos = (min(GRID_SIZE - 1, old_pos[0] + 1), old_pos[1])
            self.state = TriDemandState420(
                agent_pos=new_pos,
                inventory=self.state.inventory,
                zone_demands=self.state.zone_demands,
                zone_satisfied=self.state.zone_satisfied,
                step=self.state.step + 1,
                episode=self.state.episode,
                rule_r1_active=self.state.rule_r1_active,
                regime=self.state.regime,
                stamped=self.state.stamped,
            )

        elif action == Action.MOVE_E:
            new_pos = (old_pos[0], min(GRID_SIZE - 1, old_pos[1] + 1))
            self.state = TriDemandState420(
                agent_pos=new_pos,
                inventory=self.state.inventory,
                zone_demands=self.state.zone_demands,
                zone_satisfied=self.state.zone_satisfied,
                step=self.state.step + 1,
                episode=self.state.episode,
                rule_r1_active=self.state.rule_r1_active,
                regime=self.state.regime,
                stamped=self.state.stamped,
            )

        elif action == Action.MOVE_W:
            new_pos = (old_pos[0], max(0, old_pos[1] - 1))
            self.state = TriDemandState420(
                agent_pos=new_pos,
                inventory=self.state.inventory,
                zone_demands=self.state.zone_demands,
                zone_satisfied=self.state.zone_satisfied,
                step=self.state.step + 1,
                episode=self.state.episode,
                rule_r1_active=self.state.rule_r1_active,
                regime=self.state.regime,
                stamped=self.state.stamped,
            )

        elif action == Action.COLLECT:
            if old_pos == POSITIONS["SOURCE"] and self.state.inventory < 3:
                self.state = TriDemandState420(
                    agent_pos=old_pos,
                    inventory=self.state.inventory + 1,
                    zone_demands=self.state.zone_demands,
                    zone_satisfied=self.state.zone_satisfied,
                    step=self.state.step + 1,
                    episode=self.state.episode,
                    rule_r1_active=self.state.rule_r1_active,
                    regime=self.state.regime,
                    stamped=self.state.stamped,
                )
                reward = 0.1
                info["collected"] = True
            else:
                self.state = TriDemandState420(
                    agent_pos=old_pos,
                    inventory=self.state.inventory,
                    zone_demands=self.state.zone_demands,
                    zone_satisfied=self.state.zone_satisfied,
                    step=self.state.step + 1,
                    episode=self.state.episode,
                    rule_r1_active=self.state.rule_r1_active,
                    regime=self.state.regime,
                    stamped=self.state.stamped,
                )

        elif action == Action.DEPOSIT:
            zone_satisfied = list(self.state.zone_satisfied)
            zone_demands = list(self.state.zone_demands)
            deposited = False

            # v4.2: Under regime=1, deposit requires stamped=True
            deposit_allowed = (self.state.regime == 0) or self.state.stamped

            if self.state.inventory > 0 and deposit_allowed:
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

            self.state = TriDemandState420(
                agent_pos=old_pos,
                inventory=new_inventory,
                zone_demands=tuple(zone_demands),
                zone_satisfied=tuple(zone_satisfied),
                step=self.state.step + 1,
                episode=self.state.episode,
                rule_r1_active=self.state.rule_r1_active,
                regime=self.state.regime,
                stamped=self.state.stamped,
            )

        elif action == Action.STAMP:
            # STAMP only works at STAMP_LOCATION
            new_stamped = self.state.stamped
            if old_pos == POSITIONS["STAMP_LOCATION"]:
                new_stamped = True
                info["stamped"] = True
                reward = 0.1  # Small reward for stamping

            self.state = TriDemandState420(
                agent_pos=old_pos,
                inventory=self.state.inventory,
                zone_demands=self.state.zone_demands,
                zone_satisfied=self.state.zone_satisfied,
                step=self.state.step + 1,
                episode=self.state.episode,
                rule_r1_active=self.state.rule_r1_active,
                regime=self.state.regime,
                stamped=new_stamped,
            )

        # Check done conditions
        terminated = False
        truncated = False

        # Episode success: all zones satisfied
        if all(self.state.zone_satisfied):
            terminated = True
            info["success"] = True
            reward += 5.0

        # Episode timeout
        if self.state.step >= H:
            truncated = True
            info["timeout"] = True

        self.total_steps += 1
        obs = Observation420.from_state(self.state)

        return obs, reward, terminated, truncated, info

    # ========================================================================
    # Obligation Target Interface (v4.2)
    # ========================================================================

    def target_satisfied(self, obs: Observation420, obligation_target: Dict[str, str]) -> bool:
        """Check if obligation target is satisfied."""
        return target_satisfied(obs, obligation_target)

    def rank(self, obs: Observation420, obligation_target: Dict[str, str]) -> int:
        """Compute rank for obligation target."""
        return rank(obs, obligation_target)

    def progress_set(self, obs: Observation420, obligation_target: Dict[str, str]) -> Set[str]:
        """Compute progress set for obligation target."""
        return progress_set(obs, obligation_target)

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_observation(self) -> Observation420:
        """Get current observation without stepping."""
        if self.state is None:
            raise RuntimeError("Environment not reset")
        return Observation420.from_state(self.state)

    def get_action_mask(self) -> List[bool]:
        """Get valid action mask."""
        if self.state is None:
            return [False] * A

        mask = [True] * A

        # COLLECT only valid at SOURCE with inventory < 3
        if self.state.agent_pos != POSITIONS["SOURCE"]:
            mask[Action.COLLECT] = False
        elif self.state.inventory >= 3:
            mask[Action.COLLECT] = False

        # DEPOSIT only valid at zones with inventory > 0
        # v4.2: Also requires stamped=True under regime=1
        deposit_allowed = (self.state.regime == 0) or self.state.stamped
        if self.state.inventory == 0 or not deposit_allowed:
            mask[Action.DEPOSIT] = False
        elif self.state.agent_pos not in [POSITIONS["ZONE_A"], POSITIONS["ZONE_B"], POSITIONS["ZONE_C"]]:
            mask[Action.DEPOSIT] = False

        # STAMP only valid at STAMP_LOCATION
        if self.state.agent_pos != POSITIONS["STAMP_LOCATION"]:
            mask[Action.STAMP] = False

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
        lines.append(f"Episode {self.state.episode}, Step {self.state.step}, Regime {self.state.regime}")
        lines.append(f"Inventory: {self.state.inventory}, Stamped: {self.state.stamped}, R1 active: {self.state.rule_r1_active}")
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
    "TriDemandState420",
    "Observation420",
    "TriDemandV420",
    "H",
    "E",
    "F",
    "S",
    "A",
    "INF",
    "REGIME_FLIP_EPISODE",
    # Obligation target interface
    "target_satisfied",
    "rank",
    "progress_set",
    "manhattan",
    "simulate_step",
]
