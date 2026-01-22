"""
RSA-PoC v4.4 — TriDemandV440 Environment
Implements selective inferability isolation.

v4.4 additions over v4.3:
- Dual-channel observations (Execution Channel + Normative Channel)
- Tokenization bijections (φ_A, φ_P) reset per episode
- Tick-causal collision traces
- Execution-competence gate at regime transition

v4.4 supersedes v4.3 for inferability isolation experiments.
All v4.3 execution constraints remain binding.
"""

from __future__ import annotations

import hashlib
import os
import random
import secrets
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np


# ============================================================================
# Action Space (unchanged from v4.3)
# ============================================================================


class Action(IntEnum):
    """Action IDs per v4.3 (unchanged for v4.4)."""
    MOVE_N = 0   # A0
    MOVE_S = 1   # A1
    MOVE_E = 2   # A2
    MOVE_W = 3   # A3
    COLLECT = 4  # A4
    DEPOSIT = 5  # A5
    STAMP = 6    # A6


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
# Grid Layout (unchanged from v4.3)
# ============================================================================

GRID_SIZE = 5

# Named positions (row, col)
POSITIONS = {
    "ZONE_A": (2, 0),
    "ZONE_B": (0, 2),
    "ZONE_C": (2, 4),
    "SOURCE": (2, 2),
    "START": (4, 2),
    "STAMP_LOCATION": (2, 4),  # Same as ZONE_C
}

# Reverse mapping for lookup
POS_TO_NAME = {v: k for k, v in POSITIONS.items()}


# ============================================================================
# v4.4 Tokenization (E44-TOK)
# ============================================================================


@dataclass
class TokenizationBijection:
    """
    Per-episode tokenization bijections for v4.4 normative opacity.

    φ_A : ActionName → ActionToken
    φ_P : PredicateSymbol → PredicateToken

    These mappings are global per episode and reset between episodes.
    Token format: A_N for actions, P_N for predicates.
    """
    action_to_token: Dict[str, str] = field(default_factory=dict)
    token_to_action: Dict[str, str] = field(default_factory=dict)
    predicate_to_token: Dict[str, str] = field(default_factory=dict)
    token_to_predicate: Dict[str, str] = field(default_factory=dict)
    _seed: int = 0

    @classmethod
    def create(cls, seed: int) -> "TokenizationBijection":
        """
        Create fresh bijections for an episode.

        Uses seed for reproducibility across runs.
        """
        rng = random.Random(seed)

        # Action names to tokenize
        action_names = ["MOVE_N", "MOVE_S", "MOVE_E", "MOVE_W", "COLLECT", "DEPOSIT", "STAMP"]

        # Predicate symbols to tokenize
        predicate_symbols = [
            # Position predicates
            "at(ZONE_A)", "at(ZONE_B)", "at(ZONE_C)", "at(SOURCE)", "at(START)", "at(STAMP_LOCATION)",
            # State predicates
            "inventory>0", "inventory==0", "stamped", "not_stamped",
            "zone_a_satisfied", "zone_b_satisfied", "zone_c_satisfied",
            "can_deliver_a", "can_deliver_b",
            # Regime predicates
            "regime==0", "regime==1", "regime==2",
        ]

        # Generate shuffled token indices
        action_indices = list(range(len(action_names)))
        predicate_indices = list(range(len(predicate_symbols)))
        rng.shuffle(action_indices)
        rng.shuffle(predicate_indices)

        # Build mappings
        action_to_token = {}
        token_to_action = {}
        for i, name in enumerate(action_names):
            token = f"A_{action_indices[i]}"
            action_to_token[name] = token
            token_to_action[token] = name

        predicate_to_token = {}
        token_to_predicate = {}
        for i, pred in enumerate(predicate_symbols):
            token = f"P_{predicate_indices[i]}"
            predicate_to_token[pred] = token
            token_to_predicate[token] = pred

        return cls(
            action_to_token=action_to_token,
            token_to_action=token_to_action,
            predicate_to_token=predicate_to_token,
            token_to_predicate=token_to_predicate,
            _seed=seed,
        )

    def tokenize_action(self, action_name: str) -> str:
        """Convert action name to token."""
        return self.action_to_token.get(action_name, f"A_UNK({action_name})")

    def tokenize_action_id(self, action_id: str) -> str:
        """Convert action ID (A0-A6) to token."""
        idx = int(action_id[1])
        action_name = ACTION_NAMES[idx]
        return self.tokenize_action(action_name)

    def tokenize_predicate(self, predicate: str) -> str:
        """Convert predicate to token."""
        return self.predicate_to_token.get(predicate, f"P_UNK({predicate})")

    def detokenize_action(self, token: str) -> str:
        """Convert token back to action name."""
        return self.token_to_action.get(token, f"UNKNOWN({token})")

    def detokenize_predicate(self, token: str) -> str:
        """Convert token back to predicate."""
        return self.token_to_predicate.get(token, f"UNKNOWN({token})")


# ============================================================================
# State Space (extended for v4.4)
# ============================================================================


@dataclass
class TriDemandState440:
    """
    State representation for v4.4.

    Identical to v4.3, with added tracking for execution-competence gate.
    """
    agent_pos: Tuple[int, int]
    inventory: int
    item_type: Optional[str]  # 'A', 'B', or None
    zone_demands: Tuple[int, int, int]  # (A, B, C)
    zone_satisfied: Tuple[bool, bool, bool]  # (A, B, C)
    step: int
    episode: int
    rule_r1_active: bool
    regime: int  # 0, 1, or 2
    stamped: bool

    @property
    def dual_delivery_mode(self) -> bool:
        """True when regime==2 (S_B predicate for Contradiction B)."""
        return self.regime == 2

    @property
    def can_deliver_a(self) -> bool:
        """Can deliver to zone A: position==ZONE_A AND inventory contains item_A."""
        return (
            self.agent_pos == POSITIONS["ZONE_A"] and
            self.inventory > 0 and
            self.item_type == 'A'
        )

    @property
    def can_deliver_b(self) -> bool:
        """Can deliver to zone B: position==ZONE_B AND inventory contains item_B."""
        return (
            self.agent_pos == POSITIONS["ZONE_B"] and
            self.inventory > 0 and
            self.item_type == 'B'
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_pos": self.agent_pos,
            "inventory": self.inventory,
            "item_type": self.item_type,
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
            "dual_delivery_mode": self.dual_delivery_mode,
            "can_deliver_a": self.can_deliver_a,
            "can_deliver_b": self.can_deliver_b,
        }

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for condition evaluation."""
        return self.to_dict()[key]


@dataclass
class Observation440:
    """Observation passed to deliberator/compiler (v4.4)."""
    agent_pos: Tuple[int, int]
    inventory: int
    item_type: Optional[str]
    zone_a_demand: int
    zone_b_demand: int
    zone_c_demand: int
    zone_a_satisfied: bool
    zone_b_satisfied: bool
    zone_c_satisfied: bool
    step: int
    episode: int
    rule_r1_active: bool
    regime: int
    stamped: bool
    dual_delivery_mode: bool
    can_deliver_a: bool
    can_deliver_b: bool

    @property
    def position(self) -> str:
        """Return position as zone name for condition evaluation."""
        return POS_TO_NAME.get(self.agent_pos, "UNKNOWN")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_pos": self.agent_pos,
            "position": self.position,
            "inventory": self.inventory,
            "item_type": self.item_type,
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
            "dual_delivery_mode": self.dual_delivery_mode,
            "can_deliver_a": self.can_deliver_a,
            "can_deliver_b": self.can_deliver_b,
        }

    def __getitem__(self, key: str) -> Any:
        """Dict-like access for condition evaluation."""
        return self.to_dict()[key]

    @classmethod
    def from_state(cls, state: TriDemandState440) -> "Observation440":
        return cls(
            agent_pos=state.agent_pos,
            inventory=state.inventory,
            item_type=state.item_type,
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
            dual_delivery_mode=state.dual_delivery_mode,
            can_deliver_a=state.can_deliver_a,
            can_deliver_b=state.can_deliver_b,
        )


# ============================================================================
# v4.4 Execution-Competence Gate (E44-EXEC)
# ============================================================================


@dataclass
class ExecutionCompetenceTracker:
    """
    Tracks execution competence criteria for E44-EXEC gate.

    Evaluated at Regime 1→2 transition.
    Criteria:
    1. ≥1 navigation action executed
    2. ≥1 non-navigation action executed
    3. Reached ≥1 non-initial location
    """
    nav_action_executed: bool = False
    non_nav_action_executed: bool = False
    non_initial_location_reached: bool = False

    def record_action(self, action: Action, new_pos: Tuple[int, int]) -> None:
        """Record action execution for gate evaluation."""
        # Navigation actions: MOVE_N, MOVE_S, MOVE_E, MOVE_W
        if action in (Action.MOVE_N, Action.MOVE_S, Action.MOVE_E, Action.MOVE_W):
            self.nav_action_executed = True
        # Non-navigation actions: COLLECT, DEPOSIT, STAMP
        elif action in (Action.COLLECT, Action.DEPOSIT, Action.STAMP):
            self.non_nav_action_executed = True

        # Check if reached non-initial location
        if new_pos != POSITIONS["START"]:
            self.non_initial_location_reached = True

    @property
    def gate_passed(self) -> bool:
        """Check if all criteria are met."""
        return (
            self.nav_action_executed and
            self.non_nav_action_executed and
            self.non_initial_location_reached
        )

    def reset(self) -> None:
        """Reset tracker for new episode."""
        self.nav_action_executed = False
        self.non_nav_action_executed = False
        self.non_initial_location_reached = False


# ============================================================================
# v4.4 Collision Trace (E44-TRACE)
# ============================================================================


@dataclass
class CollisionTrace:
    """
    Tick-causal collision trace for v4.4.

    Emitted on HALT or violation, enables collision inference:
    "My action at tick t empirically collided with the cited token(s)."
    """
    tick: int
    rule_id: str
    action_token: Optional[str]  # Tokenized action that caused collision
    predicate_tokens: List[str]  # Tokenized predicates involved
    episode: int

    def format(self) -> str:
        """Format trace for agent observation."""
        tokens = []
        if self.action_token:
            tokens.append(f"ActionToken: {self.action_token}")
        if self.predicate_tokens:
            tokens.append(f"PredicateTokens: {', '.join(self.predicate_tokens)}")

        token_str = "; ".join(tokens) if tokens else "no tokens cited"

        return (
            f"HALT at tick {self.tick}:\n"
            f"Rule {self.rule_id} violated.\n"
            f"Your last action empirically collided with {token_str}."
        )


# ============================================================================
# Environment Parameters (v4.4 — inherited from v4.3)
# ============================================================================

H = 40  # Episode length (steps)
E = 20  # Episode count
F = 10  # Conflict bound (steps)
S = 32  # State size cap (bits)
A = 7   # Action arity

# Regime transition episodes (v4.3)
REGIME_1_START = 2  # Episode where regime flips 0→1
REGIME_2_PREREGISTERED_START = 4  # Preregistered start for regime 2
DELTA_THRESHOLD = 2  # Max delay for regime 2 start (E3)

# Sentinel for impossible obligations
INF = 10**9


# ============================================================================
# Obligation Target Interface (inherited from v4.3)
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


def target_satisfied(obs: Observation440, obligation_target: Dict[str, str]) -> bool:
    """
    Check if an obligation target is satisfied.

    Per §5.5: DEPOSIT_ZONE targets are satisfied when zone_X_satisfied == True.
    """
    kind = obligation_target.get("kind")
    target_id = obligation_target.get("target_id")

    if kind == "DEPOSIT_ZONE":
        if target_id == "ZONE_A":
            return obs.zone_a_satisfied
        elif target_id == "ZONE_B":
            return obs.zone_b_satisfied
        elif target_id == "ZONE_C":
            return obs.zone_c_satisfied
        else:
            raise ValueError(f"Unknown target_id: {target_id}")
    elif kind == "DELIVER":
        if target_id == "ZONE_A":
            return obs.zone_a_satisfied
        elif target_id == "ZONE_B":
            return obs.zone_b_satisfied
        else:
            raise ValueError(f"Unknown DELIVER target_id: {target_id}")
    else:
        raise ValueError(f"Unknown obligation target kind: {kind}")


def rank(obs: Observation440, obligation_target: Dict[str, str]) -> int:
    """
    Compute rank for an obligation target per v4.3.
    """
    if target_satisfied(obs, obligation_target):
        return 0

    pos = obs.agent_pos
    target_id = obligation_target.get("target_id")
    zone_pos = get_zone_position(target_id)
    src_pos = POSITIONS["SOURCE"]
    stamp_pos = POSITIONS["STAMP_LOCATION"]

    if obs.inventory == 0:
        dist_to_source = manhattan(pos, src_pos)
        dist_source_to_zone = manhattan(src_pos, zone_pos)
        base_rank = dist_to_source + 1 + dist_source_to_zone + 1
    else:
        base_rank = manhattan(pos, zone_pos) + 1

    if obs.regime == 1 and not obs.stamped:
        if obs.inventory == 0:
            dist_to_source = manhattan(pos, src_pos)
            dist_source_to_stamp = manhattan(src_pos, stamp_pos)
            dist_stamp_to_zone = manhattan(stamp_pos, zone_pos)
            base_rank = dist_to_source + 1 + dist_source_to_stamp + 1 + dist_stamp_to_zone + 1
        else:
            dist_to_stamp = manhattan(pos, stamp_pos)
            dist_stamp_to_zone = manhattan(stamp_pos, zone_pos)
            base_rank = dist_to_stamp + 1 + dist_stamp_to_zone + 1

    return base_rank


def progress_set(obs: Observation440, obligation_target: Dict[str, str]) -> Set[str]:
    """
    Compute the set of actions that decrease rank per v4.3.
    """
    kind = obligation_target.get("kind")
    target_id = obligation_target.get("target_id")

    if target_satisfied(obs, obligation_target):
        return set()

    if kind in ("DELIVER", "DEPOSIT_ZONE"):
        if obs.regime == 1 and obs.inventory > 0 and not obs.stamped:
            stamp_pos = POSITIONS["STAMP_LOCATION"]
            if obs.agent_pos == stamp_pos:
                return {"A6"}  # STAMP

        if obs.regime == 2:
            zone_pos = get_zone_position(target_id)
            if obs.agent_pos == zone_pos and obs.inventory > 0:
                if target_id == "ZONE_A" and obs.item_type == 'A':
                    return {"A5"}  # DEPOSIT
                elif target_id == "ZONE_B" and obs.item_type == 'B':
                    return {"A5"}  # DEPOSIT

    current_rank = rank(obs, obligation_target)

    if current_rank == 0 or current_rank == INF:
        return set()

    result = set()
    for action_id in ACTION_IDS:
        new_obs = simulate_step(obs, action_id)
        new_rank = rank(new_obs, obligation_target)
        if new_rank < current_rank:
            result.add(action_id)

    return result


def simulate_step(obs: Observation440, action_id: str) -> Observation440:
    """
    Simulate a single step for progress_set computation.
    """
    action = ACTION_ID_MAP.get(action_id)
    if action is None:
        return obs

    pos = obs.agent_pos
    inv = obs.inventory
    item_type = obs.item_type
    zone_satisfied = [obs.zone_a_satisfied, obs.zone_b_satisfied, obs.zone_c_satisfied]
    stamped = obs.stamped

    new_pos = pos
    new_inv = inv
    new_item_type = item_type
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
            if item_type is None:
                new_item_type = 'A'
            elif item_type == 'A':
                new_item_type = 'B'
            else:
                new_item_type = 'A'
    elif action == Action.DEPOSIT:
        deposit_allowed = (obs.regime == 0) or obs.stamped
        if inv > 0 and deposit_allowed:
            if pos == POSITIONS["ZONE_A"] and not zone_satisfied[0]:
                new_satisfied[0] = True
                new_inv = inv - 1
                if new_inv == 0:
                    new_item_type = None
            elif pos == POSITIONS["ZONE_B"] and not zone_satisfied[1]:
                new_satisfied[1] = True
                new_inv = inv - 1
                if new_inv == 0:
                    new_item_type = None
            elif pos == POSITIONS["ZONE_C"] and not zone_satisfied[2]:
                new_satisfied[2] = True
                new_inv = inv - 1
                if new_inv == 0:
                    new_item_type = None
    elif action == Action.STAMP:
        if pos == POSITIONS["STAMP_LOCATION"]:
            new_stamped = True

    return Observation440(
        agent_pos=new_pos,
        inventory=new_inv,
        item_type=new_item_type,
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
        dual_delivery_mode=obs.regime == 2,
        can_deliver_a=(new_pos == POSITIONS["ZONE_A"] and new_inv > 0 and new_item_type == 'A'),
        can_deliver_b=(new_pos == POSITIONS["ZONE_B"] and new_inv > 0 and new_item_type == 'B'),
    )


# ============================================================================
# TriDemandV440 Environment
# ============================================================================


class TriDemandV440:
    """
    5×5 gridworld environment for v4.4.

    v4.4 additions over v4.3:
    - Dual-channel observations (Execution + Normative)
    - Tokenization bijections per episode
    - Collision traces for tick-causal attribution
    - Execution-competence gate
    """

    def __init__(
        self,
        seed: int = 42,
        regime_1_start: int = REGIME_1_START,
        regime_2_preregistered_start: int = REGIME_2_PREREGISTERED_START,
        delta_threshold: int = DELTA_THRESHOLD,
        normative_opacity: bool = False,  # v4.4: Enable tokenization
    ):
        self.seed = seed
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)

        # Regime transition parameters
        self.regime_1_start = regime_1_start
        self.regime_2_preregistered_start = regime_2_preregistered_start
        self.delta_threshold = delta_threshold

        # v4.4: Normative opacity flag
        self.normative_opacity = normative_opacity

        # State
        self.state: Optional[TriDemandState440] = None
        self.episode_count = 0
        self.total_steps = 0

        # v4.3: Event-gated regime-2 transition
        self._repair_a_episode: Optional[int] = None
        self._regime_2_actual_start: Optional[int] = None

        # v4.3: Epoch chain
        self._nonces: List[bytes] = []

        # v4.4: Per-episode tokenization bijection
        self._current_bijection: Optional[TokenizationBijection] = None

        # v4.4: Execution-competence tracker
        self._exec_tracker = ExecutionCompetenceTracker()
        self._exec_gate_evaluated: bool = False
        self._exec_gate_passed: bool = False

        # v4.4: Collision trace history (per episode)
        self._collision_traces: List[CollisionTrace] = []

        # Episode metrics
        self.episode_rewards: List[float] = []
        self.episode_lengths: List[int] = []

    @property
    def regime(self) -> int:
        """Current regime (0, 1, or 2)."""
        if self.state is None:
            return 0
        return self.state.regime

    @property
    def bijection(self) -> Optional[TokenizationBijection]:
        """Current tokenization bijection."""
        return self._current_bijection

    def _compute_regime(self, episode: int) -> int:
        """
        Compute regime for episode per v4.3 E3 (event-gated).
        """
        if episode < self.regime_1_start:
            return 0

        if self._regime_2_actual_start is not None:
            if episode >= self._regime_2_actual_start:
                return 2
            return 1

        return 1

    def record_repair_a_accepted(self, episode: int) -> None:
        """
        Record that Repair A was accepted, triggering E3 computation.
        """
        if self._repair_a_episode is not None:
            return

        self._repair_a_episode = episode
        self._regime_2_actual_start = max(
            self.regime_2_preregistered_start,
            episode + 1
        )

    def check_repair_a_too_late(self) -> Tuple[bool, int]:
        """
        Check if Repair A acceptance caused regime-2 delay > Δ.
        """
        if self._regime_2_actual_start is None:
            return False, 0

        delay = self._regime_2_actual_start - self.regime_2_preregistered_start
        return delay > self.delta_threshold, delay

    def get_nonce(self, index: int) -> bytes:
        """
        Get nonce by index (0, 1, or 2), generating if needed.
        """
        while len(self._nonces) <= index:
            self._nonces.append(secrets.token_bytes(32))
        return self._nonces[index]

    def evaluate_exec_gate(self) -> bool:
        """
        Evaluate execution-competence gate at regime transition.

        Called at Regime 1→2 boundary.
        Returns True if gate passes, False otherwise.
        """
        if self._exec_gate_evaluated:
            return self._exec_gate_passed

        self._exec_gate_evaluated = True
        self._exec_gate_passed = self._exec_tracker.gate_passed
        return self._exec_gate_passed

    def reset(self, episode: Optional[int] = None) -> Tuple[Observation440, Dict[str, Any]]:
        """
        Reset environment for new episode.

        v4.4: Creates fresh tokenization bijection per episode.
        """
        if episode is not None:
            self.episode_count = episode
        else:
            self.episode_count += 1

        # R1 expires at episode 1
        rule_r1_active = self.episode_count < 2

        # v4.3: Event-gated regime computation
        regime = self._compute_regime(self.episode_count)

        # v4.4: Check exec gate at regime 1→2 transition
        if regime == 2 and not self._exec_gate_evaluated:
            self.evaluate_exec_gate()

        # v4.4: Fresh tokenization bijection per episode
        episode_seed = self.seed + self.episode_count * 1000
        self._current_bijection = TokenizationBijection.create(episode_seed)

        # v4.4: Reset collision traces and exec tracker for new episode
        self._collision_traces = []
        if regime < 2:  # Only track during regime 0/1
            self._exec_tracker.reset()

        # Initialize demands
        zone_demands = (1, 1, 1)

        self.state = TriDemandState440(
            agent_pos=POSITIONS["START"],
            inventory=0,
            item_type=None,
            zone_demands=zone_demands,
            zone_satisfied=(False, False, False),
            step=0,
            episode=self.episode_count,
            rule_r1_active=rule_r1_active,
            regime=regime,
            stamped=False,
        )

        obs = Observation440.from_state(self.state)
        info = {
            "episode": self.episode_count,
            "rule_r1_active": rule_r1_active,
            "regime": regime,
            "repair_a_episode": self._repair_a_episode,
            "regime_2_actual_start": self._regime_2_actual_start,
            "normative_opacity": self.normative_opacity,
            "exec_gate_passed": self._exec_gate_passed if self._exec_gate_evaluated else None,
        }
        return obs, info

    def step(self, action: Union[int, Action, str]) -> Tuple[Observation440, float, bool, bool, Dict[str, Any]]:
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
        old_inv = self.state.inventory
        old_item_type = self.state.item_type
        old_stamped = self.state.stamped
        zone_satisfied = list(self.state.zone_satisfied)
        zone_demands = list(self.state.zone_demands)

        new_pos = old_pos
        new_inv = old_inv
        new_item_type = old_item_type
        new_stamped = old_stamped

        if action == Action.MOVE_N:
            new_pos = (max(0, old_pos[0] - 1), old_pos[1])
        elif action == Action.MOVE_S:
            new_pos = (min(GRID_SIZE - 1, old_pos[0] + 1), old_pos[1])
        elif action == Action.MOVE_E:
            new_pos = (old_pos[0], min(GRID_SIZE - 1, old_pos[1] + 1))
        elif action == Action.MOVE_W:
            new_pos = (old_pos[0], max(0, old_pos[1] - 1))
        elif action == Action.COLLECT:
            if old_pos == POSITIONS["SOURCE"] and old_inv < 3:
                new_inv = old_inv + 1
                if old_item_type is None:
                    new_item_type = 'A'
                elif old_item_type == 'A':
                    new_item_type = 'B'
                else:
                    new_item_type = 'A'
                reward = 0.1
                info["collected"] = True
                info["item_type"] = new_item_type
        elif action == Action.DEPOSIT:
            deposit_allowed = (self.state.regime == 0) or self.state.stamped
            deposited = False

            if old_inv > 0 and deposit_allowed:
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

            if deposited:
                new_inv = old_inv - 1
                if new_inv == 0:
                    new_item_type = None
        elif action == Action.STAMP:
            if old_pos == POSITIONS["STAMP_LOCATION"]:
                new_stamped = True
                info["stamped"] = True
                reward = 0.1

        # v4.4: Track execution competence (during regime 0/1)
        if self.state.regime < 2:
            self._exec_tracker.record_action(action, new_pos)

        self.state = TriDemandState440(
            agent_pos=new_pos,
            inventory=new_inv,
            item_type=new_item_type,
            zone_demands=tuple(zone_demands),
            zone_satisfied=tuple(zone_satisfied),
            step=self.state.step + 1,
            episode=self.state.episode,
            rule_r1_active=self.state.rule_r1_active,
            regime=self.state.regime,
            stamped=new_stamped,
        )

        # Check done conditions
        terminated = False
        truncated = False

        if all(self.state.zone_satisfied):
            terminated = True
            info["success"] = True
            reward += 5.0

        if self.state.step >= H:
            truncated = True
            info["timeout"] = True

        self.total_steps += 1
        obs = Observation440.from_state(self.state)

        return obs, reward, terminated, truncated, info

    # ========================================================================
    # v4.4: Collision Trace Interface
    # ========================================================================

    def record_collision(
        self,
        rule_id: str,
        action_name: str,
        predicate_symbols: Optional[List[str]] = None,
    ) -> CollisionTrace:
        """
        Record a collision for tick-causal trace emission.

        Called by harness when HALT occurs.
        """
        if self._current_bijection is None:
            raise RuntimeError("No active bijection")

        action_token = self._current_bijection.tokenize_action(action_name)
        predicate_tokens = []
        if predicate_symbols:
            predicate_tokens = [
                self._current_bijection.tokenize_predicate(p)
                for p in predicate_symbols
            ]

        trace = CollisionTrace(
            tick=self.state.step if self.state else 0,
            rule_id=rule_id,
            action_token=action_token,
            predicate_tokens=predicate_tokens,
            episode=self.episode_count,
        )
        self._collision_traces.append(trace)
        return trace

    def get_collision_traces(self) -> List[CollisionTrace]:
        """Get all collision traces for current episode."""
        return self._collision_traces.copy()

    # ========================================================================
    # Obligation Target Interface
    # ========================================================================

    def target_satisfied(self, obs: Observation440, obligation_target: Dict[str, str]) -> bool:
        """Check if obligation target is satisfied."""
        return target_satisfied(obs, obligation_target)

    def rank(self, obs: Observation440, obligation_target: Dict[str, str]) -> int:
        """Compute rank for obligation target."""
        return rank(obs, obligation_target)

    def progress_set(self, obs: Observation440, obligation_target: Dict[str, str]) -> Set[str]:
        """Compute progress set for obligation target."""
        return progress_set(obs, obligation_target)

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def get_observation(self) -> Observation440:
        """Get current observation without stepping."""
        if self.state is None:
            raise RuntimeError("Environment not reset")
        return Observation440.from_state(self.state)

    def get_action_mask(self) -> List[bool]:
        """Get valid action mask."""
        if self.state is None:
            return [False] * A

        mask = [True] * A

        if self.state.agent_pos != POSITIONS["SOURCE"]:
            mask[Action.COLLECT] = False
        elif self.state.inventory >= 3:
            mask[Action.COLLECT] = False

        deposit_allowed = (self.state.regime == 0) or self.state.stamped
        if self.state.inventory == 0 or not deposit_allowed:
            mask[Action.DEPOSIT] = False
        elif self.state.agent_pos not in [POSITIONS["ZONE_A"], POSITIONS["ZONE_B"], POSITIONS["ZONE_C"]]:
            mask[Action.DEPOSIT] = False

        if self.state.agent_pos != POSITIONS["STAMP_LOCATION"]:
            mask[Action.STAMP] = False

        return mask

    def render(self) -> str:
        """Render the grid as ASCII."""
        if self.state is None:
            return "Environment not reset"

        grid = [["." for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        grid[POSITIONS["ZONE_A"][0]][POSITIONS["ZONE_A"][1]] = "A"
        grid[POSITIONS["ZONE_B"][0]][POSITIONS["ZONE_B"][1]] = "B"
        grid[POSITIONS["ZONE_C"][0]][POSITIONS["ZONE_C"][1]] = "C"
        grid[POSITIONS["SOURCE"][0]][POSITIONS["SOURCE"][1]] = "S"

        row, col = self.state.agent_pos
        grid[row][col] = "@"

        lines = []
        lines.append(f"Episode {self.state.episode}, Step {self.state.step}, Regime {self.state.regime}")
        lines.append(f"Inventory: {self.state.inventory} (type={self.state.item_type}), Stamped: {self.state.stamped}")
        lines.append(f"R1 active: {self.state.rule_r1_active}, Dual delivery: {self.state.dual_delivery_mode}")
        lines.append(f"Normative opacity: {self.normative_opacity}")
        if self._exec_gate_evaluated:
            lines.append(f"Exec gate: {'PASSED' if self._exec_gate_passed else 'FAILED'}")
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
    "TriDemandState440",
    "Observation440",
    "TriDemandV440",
    "TokenizationBijection",
    "ExecutionCompetenceTracker",
    "CollisionTrace",
    "H",
    "E",
    "F",
    "S",
    "A",
    "INF",
    "REGIME_1_START",
    "REGIME_2_PREREGISTERED_START",
    "DELTA_THRESHOLD",
    "target_satisfied",
    "rank",
    "progress_set",
    "manhattan",
    "simulate_step",
]
