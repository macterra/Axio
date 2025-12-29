"""Honest agent implementation."""

import os
import uuid
from typing import Optional
from dataclasses import dataclass, field

from ..env.gridworld import GridState, DIRECTIONS, step, clone_state
from ..env.normalize_state import normalize_state, get_default_focus_vars
from ..env.metrics_oracle import (
    find_nearest_object,
    find_nearest_hazard,
    find_nearest_agent,
    manhattan_distance,
    compute_hazard_proximity
)
from ..common.hashing import hash_json, compute_fork_commitment
from ..kernel.capability import create_capability_scope, create_capability_request
from ..interfaces import get_interface, MCILatentInterface, MCIMinimalInterface


# Standard actions for replay_model
STANDARD_ACTIONS = [
    "NOOP", "WAIT", "MOVE_N", "MOVE_S", "MOVE_E", "MOVE_W", "PICKUP"
]


def action_dict_to_string(action: dict) -> str:
    """Convert action dict to standard string."""
    dir_map = {
        "up": "N", "down": "S", "left": "W", "right": "E",
        "north": "N", "south": "S", "west": "W", "east": "E",
        "n": "N", "s": "S", "e": "E", "w": "W"
    }

    op = action.get("op", "noop")
    args = action.get("args", {})

    if op == "move":
        direction = args.get('direction', 'N').lower()
        direction_abbrev = dir_map.get(direction, direction.upper())
        return f"MOVE_{direction_abbrev}"
    return op.upper()


def string_to_action_dict(action_str: str) -> dict:
    """Convert action string to action dict."""
    action_str = action_str.upper()

    if action_str == "NOOP":
        return {"op": "noop", "args": {}}
    elif action_str == "WAIT":
        return {"op": "wait", "args": {}}
    elif action_str == "PICKUP":
        return {"op": "pickup", "args": {}}
    elif action_str.startswith("MOVE_"):
        direction = action_str[5:]  # Extract N, S, E, W
        dir_map = {"N": "up", "S": "down", "E": "right", "W": "left"}
        return {"op": "move", "args": {"direction": dir_map.get(direction, "up")}}
    else:
        return {"op": "noop", "args": {}}


@dataclass
class HonestAgent:
    """Honest agent that produces valid traces reflecting actual decision logic.

    In 'full' mode (legacy):
    - Uses heuristic decision logic
    - Produces full environment commitments

    In MCI modes (mci_latent, mci_minimal):
    - Uses replay_model (W @ f + b) for actual decisions
    - The model IS the decision procedure, not post-hoc justification
    - Produces factor-based commitments

    Objectives (encoded in replay_model weights for MCI modes):
    - Avoid hazards strongly (high negative weight on F:3 hazard_proximity)
    - Collect objects (moderate positive weight on closeness to objects)
    - Conserve energy (moderate positive weight on energy level)
    """

    agent_id: str = "self"
    interface_mode: str = "full"
    _nonces: dict[str, bytes] = field(default_factory=dict)
    _replay_model: Optional[dict] = field(default=None)

    def __post_init__(self):
        """Initialize replay_model for MCI modes."""
        if self.interface_mode in ("mci_latent", "mci_minimal"):
            self._replay_model = self._build_honest_replay_model()

    def _build_honest_replay_model(self) -> dict:
        """Build an honest replay model that genuinely drives decisions.

        The model encodes honest objectives:
        - Avoid hazards (F:3 = hazard_proximity_flag)
        - Seek objects (F:4 = min_dist_object, lower = closer = better)
        - Maintain energy (F:0 = energy)
        - Prefer reachability (F:6 = reachable_cells)

        Actions: NOOP, WAIT, MOVE_N, MOVE_S, MOVE_E, MOVE_W, PICKUP
        Factors (K=8):
          F:0 = energy/100
          F:1 = inventory_count/10
          F:2 = min_dist_hazard/10
          F:3 = hazard_proximity_flag (0 or 1)
          F:4 = min_dist_object/10
          F:5 = min_dist_agent/10
          F:6 = reachable_cells/64
          F:7 = walls_radius3/25
        """
        K = 8
        A = len(STANDARD_ACTIONS)

        # Initialize weights: W is A x K, b is A
        # Each row is weights for one action

        # Index mapping:
        # 0=NOOP, 1=WAIT, 2=MOVE_N, 3=MOVE_S, 4=MOVE_E, 5=MOVE_W, 6=PICKUP

        W = [[0.0] * K for _ in range(A)]
        b = [0.0] * A

        # NOOP (0): Baseline, slight negative
        b[0] = -2.0

        # WAIT (1): Prefer when energy is low, no hazards nearby
        W[1][0] = -3.0  # Low energy -> wait to recover
        W[1][3] = -5.0  # Hazard nearby -> don't wait
        W[1][4] = -1.0  # Far from objects -> ok to wait
        b[1] = 0.5

        # MOVE_N (2): Prefer when mobile, no hazard ahead
        W[2][0] = 1.0   # More energy -> can move
        W[2][3] = -8.0  # Hazard nearby -> avoid moves
        W[2][6] = 2.0   # More reachable -> good
        b[2] = 1.0

        # MOVE_S (3): Similar
        W[3][0] = 1.0
        W[3][3] = -8.0
        W[3][6] = 2.0
        b[3] = 1.0

        # MOVE_E (4): Similar
        W[4][0] = 1.0
        W[4][3] = -8.0
        W[4][6] = 2.0
        b[4] = 1.0

        # MOVE_W (5): Similar
        W[5][0] = 1.0
        W[5][3] = -8.0
        W[5][6] = 2.0
        b[5] = 1.0

        # PICKUP (6): Prefer when object is close (F:4 low)
        W[6][3] = -10.0  # Never pickup near hazard
        W[6][4] = -15.0  # Object distance: lower is better, strongly prefer
        b[6] = 3.0       # High baseline to prefer pickup when object close

        return {
            "W": W,
            "b": b,
            "actions": STANDARD_ACTIONS
        }

    def decide(self, env: GridState) -> dict:
        """Produce a proposal for the current environment state.

        Args:
            env: Current environment state

        Returns:
            Complete proposal dict
        """
        if self.interface_mode in ("mci_latent", "mci_minimal"):
            return self._decide_mci(env)
        else:
            return self._decide_full(env)

    def decide_with_factors(self, factors: list[float]) -> dict:
        """Produce a proposal given pre-computed factors (for P5-MCI).

        Args:
            factors: Factor vector (K=8)

        Returns:
            Complete proposal dict with replay_model applied
        """
        if self._replay_model is None:
            raise ValueError("Cannot decide_with_factors in full mode")

        # Compute action from replay model
        action_str = self._compute_action_from_model(factors)
        action = string_to_action_dict(action_str)

        # Build minimal proposal for P5-MCI verification
        return {
            "proposal_id": str(uuid.uuid4()),
            "proposal_type": "action",
            "payload": {
                "intent": f"Replay model selected {action_str}",
                "plan": {"steps": [action]},
                "constraints": []
            },
            "trace": {
                "trace_version": "0.3",
                "factors": factors,
                "replay_model": self._replay_model
            }
        }

    def _compute_action_from_model(self, factors: list[float]) -> str:
        """Compute action using replay model.

        logits = W @ factors + b
        action = argmax(logits)
        """
        if self._replay_model is None:
            raise ValueError("Replay model not initialized")

        W = self._replay_model["W"]
        b = self._replay_model["b"]
        actions = self._replay_model["actions"]

        # Compute logits
        logits = []
        for i in range(len(actions)):
            logit = b[i]
            for j in range(len(factors)):
                logit += W[i][j] * factors[j]
            logits.append(logit)

        # Argmax
        max_idx = 0
        max_val = logits[0]
        for i in range(1, len(logits)):
            if logits[i] > max_val:
                max_val = logits[i]
                max_idx = i

        return actions[max_idx]

    def _decide_mci(self, env: GridState) -> dict:
        """Produce a proposal using MCI interface (factor-based).

        In MCI mode, the replay_model IS the decision procedure.
        """
        interface = get_interface(self.interface_mode)

        # Compute factors from environment
        factors = interface.compute_factors(env)

        # Use replay model to decide action
        action_str = self._compute_action_from_model(factors)
        action = string_to_action_dict(action_str)
        intent = f"Replay model selected {action_str}"

        # Generate trace nodes
        nodes = self._generate_mci_nodes(env, factors, action_str)
        edges = [
            {"from": 0, "to": 1, "type": "derives"},
            {"from": 1, "to": 2, "type": "evaluates"}
        ]

        # Generate causal claims referencing factors
        causal_claims = self._generate_factor_causal_claims(factors, action_str)

        # Generate counterfactuals
        counterfactuals = self._generate_counterfactuals(env, action)

        # Generate fork snapshot with factor commitment
        focus_vars = get_default_focus_vars()
        fork_snapshot = self._create_fork_snapshot(env, focus_vars)

        # Create factor snapshot
        nonce_ref = f"factor_nonce_{env.tick}"
        nonce_bytes = os.urandom(32)
        self._nonces[nonce_ref] = nonce_bytes
        factor_snapshot = interface.create_factor_commitment(
            env, f"factors_{env.tick}", nonce_ref
        )

        # Build plan
        plan = {"steps": [action]}

        # Build trace (MCI v0.3)
        trace = {
            "trace_version": "0.3",
            "trace_commit": "",  # Will be filled in
            "interface": {
                "mode": self.interface_mode,
                "factor_dim": interface.factor_dim,
                "projection_id": interface.projection_id
            },
            "factors": factors,
            "factor_snapshot": factor_snapshot,
            "replay_model": self._replay_model,
            "nodes": nodes,
            "edges": edges,
            "fork_snapshots": [fork_snapshot],
            "causal_claims": causal_claims,
            "counterfactuals": counterfactuals
        }

        # Compute trace_commit
        trace_for_hash = {k: v for k, v in trace.items() if k != "trace_commit"}
        trace["trace_commit"] = hash_json(trace_for_hash)

        # Build proposal
        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "proposal_type": "action",
            "interface": {
                "mode": self.interface_mode,
                "factor_dim": interface.factor_dim,
                "projection_id": interface.projection_id
            },
            "env": env.to_dict(),
            "payload": {
                "intent": intent,
                "plan": plan,
                "constraints": ["avoid_hazards", "respect_agents"]
            },
            "trace": trace,
            "requested_capabilities": self._get_capability_requests(action)
        }

        return proposal

    def _generate_mci_nodes(
        self,
        env: GridState,
        factors: list[float],
        action_str: str
    ) -> list[dict]:
        """Generate trace nodes for MCI mode."""
        return [
            {
                "id": 0,
                "kind": "observation",
                "summary": f"Position ({env.self_entity.x}, {env.self_entity.y}), energy {env.self_entity.energy}",
                "payload": {"pos": [env.self_entity.x, env.self_entity.y]}
            },
            {
                "id": 1,
                "kind": "projection",
                "summary": f"Projected to {len(factors)} factors",
                "payload": {"factors": factors}
            },
            {
                "id": 2,
                "kind": "inference",
                "summary": f"Replay model selected {action_str}",
                "payload": {"action": action_str}
            }
        ]

    def _generate_factor_causal_claims(
        self,
        factors: list[float],
        action_str: str
    ) -> list[dict]:
        """Generate causal claims referencing factor indices."""
        claims = []

        # Claim 1: If hazard proximity (F:3) decreases, move actions increase
        claims.append({
            "var": "F:3",
            "direction": "threshold",
            "expected_effect_on_choice": f"IF F:3 LT 0.5 THEN CHOICE {action_str}",
            "confidence": 0.9,
            "supporting_nodes": [1, 2]
        })

        # Claim 2: If object distance (F:4) decreases, prefer pickup
        claims.append({
            "var": "F:4",
            "direction": "threshold",
            "expected_effect_on_choice": "IF F:4 LT 0.1 THEN CHOICE PICKUP",
            "confidence": 0.85,
            "supporting_nodes": [1, 2]
        })

        return claims

    def _decide_full(self, env: GridState) -> dict:
        """Produce a proposal using full interface (legacy v1).

        Uses heuristic decision logic with full environment commitment.
        """
        # Generate trace nodes following actual decision logic
        nodes = []
        edges = []

        # Node 0: Observation of current state
        nodes.append({
            "id": 0,
            "kind": "observation",
            "summary": f"Current position ({env.self_entity.x}, {env.self_entity.y}), energy {env.self_entity.energy}",
            "payload": {
                "pos": [env.self_entity.x, env.self_entity.y],
                "energy": env.self_entity.energy
            }
        })

        # Node 1: Hazard assessment
        hazard_info = find_nearest_hazard(env)
        hazard_nearby = compute_hazard_proximity(env)
        nodes.append({
            "id": 1,
            "kind": "evaluation",
            "summary": f"Hazard assessment: nearest at distance {hazard_info[1] if hazard_info else 'none'}",
            "payload": {
                "hazard_id": hazard_info[0] if hazard_info else None,
                "distance": hazard_info[1] if hazard_info else -1,
                "adjacent": hazard_nearby
            }
        })
        edges.append({"from": 0, "to": 1, "type": "derives"})

        # Node 2: Object assessment
        object_info = find_nearest_object(env)
        nodes.append({
            "id": 2,
            "kind": "evaluation",
            "summary": f"Object assessment: nearest at distance {object_info[1] if object_info else 'none'}",
            "payload": {
                "object_id": object_info[0] if object_info else None,
                "distance": object_info[1] if object_info else -1
            }
        })
        edges.append({"from": 0, "to": 2, "type": "derives"})

        # Node 3: Agent assessment
        agent_info = find_nearest_agent(env)
        nodes.append({
            "id": 3,
            "kind": "evaluation",
            "summary": f"Agent assessment: nearest at distance {agent_info[1] if agent_info else 'none'}",
            "payload": {
                "agent_id": agent_info[0] if agent_info else None,
                "distance": agent_info[1] if agent_info else -1
            }
        })
        edges.append({"from": 0, "to": 3, "type": "derives"})

        # Decide action based on actual logic
        action, intent, choice_rationale = self._compute_action(env, hazard_info, object_info, agent_info)

        # Node 4: Decision
        nodes.append({
            "id": 4,
            "kind": "inference",
            "summary": choice_rationale,
            "payload": {
                "action": action,
                "intent": intent
            }
        })
        edges.append({"from": 1, "to": 4, "type": "evaluates"})
        edges.append({"from": 2, "to": 4, "type": "evaluates"})
        edges.append({"from": 3, "to": 4, "type": "evaluates"})

        # Generate causal claims that accurately reflect decision
        causal_claims = self._generate_causal_claims(env, action, hazard_info, object_info, agent_info)

        # Generate counterfactuals
        counterfactuals = self._generate_counterfactuals(env, action)

        # Generate fork snapshot with commitment
        focus_vars = get_default_focus_vars()
        fork_snapshot = self._create_fork_snapshot(env, focus_vars)

        # Build plan
        plan = {"steps": [action]}

        # Build trace (without trace_commit initially)
        trace = {
            "trace_version": "0.2",
            "trace_commit": "",  # Will be filled in
            "nodes": nodes,
            "edges": edges,
            "fork_snapshots": [fork_snapshot],
            "causal_claims": causal_claims,
            "counterfactuals": counterfactuals
        }

        # Compute trace_commit
        trace_for_hash = {k: v for k, v in trace.items() if k != "trace_commit"}
        trace["trace_commit"] = hash_json(trace_for_hash)

        # Build proposal
        proposal = {
            "proposal_id": str(uuid.uuid4()),
            "proposal_type": "action",
            "interface": {"mode": "full"},
            "env": env.to_dict(),
            "payload": {
                "intent": intent,
                "plan": plan,
                "constraints": ["avoid_hazards", "respect_agents"]
            },
            "trace": trace,
            "requested_capabilities": self._get_capability_requests(action)
        }

        return proposal

    def _compute_action(
        self,
        env: GridState,
        hazard_info: Optional[tuple[str, int]],
        object_info: Optional[tuple[str, int]],
        agent_info: Optional[tuple[str, int]]
    ) -> tuple[dict, str, str]:
        """Compute the action to take.

        Priority:
        1. Flee from adjacent hazards
        2. Pick up object if on same cell
        3. Move toward nearest object (avoiding hazards)
        4. Wait if safe and no objectives

        Returns:
            Tuple of (action_dict, intent_string, rationale_string)
        """
        sx, sy = env.self_entity.x, env.self_entity.y

        # Check if on a hazard (flee!)
        if hazard_info and hazard_info[1] <= 1:
            # Find safe direction
            best_dir = self._find_safe_direction(env)
            if best_dir:
                return (
                    {"op": "move", "args": {"direction": best_dir}},
                    f"Flee from adjacent hazard {hazard_info[0]}",
                    f"Moving {best_dir} to escape hazard"
                )

        # Check if on an object (pick up)
        obj = env.get_object_at(sx, sy)
        if obj:
            return (
                {"op": "pickup", "args": {}},
                f"Collect object {obj.id}",
                f"Picking up {obj.kind} at current position"
            )

        # Move toward nearest object if exists
        if object_info:
            obj_id = object_info[0]
            for obj in env.objects:
                if obj.id == obj_id:
                    direction = self._direction_toward(env, obj.x, obj.y)
                    if direction:
                        return (
                            {"op": "move", "args": {"direction": direction}},
                            f"Approach object {obj_id}",
                            f"Moving {direction} toward {obj.kind}"
                        )

        # Default: wait
        return (
            {"op": "wait", "args": {}},
            "No immediate objectives, conserving energy",
            "Waiting to recover energy"
        )

    def _find_safe_direction(self, env: GridState) -> Optional[str]:
        """Find a direction away from hazards."""
        sx, sy = env.self_entity.x, env.self_entity.y

        best_dir = None
        best_hazard_dist = -1

        for direction, (dx, dy) in DIRECTIONS.items():
            nx, ny = sx + dx, sy + dy
            if not env.is_valid_position(nx, ny):
                continue

            # Calculate minimum distance to any hazard
            min_hazard_dist = float('inf')
            for hazard in env.hazards:
                dist = manhattan_distance(nx, ny, hazard.x, hazard.y)
                min_hazard_dist = min(min_hazard_dist, dist)

            if min_hazard_dist > best_hazard_dist:
                best_hazard_dist = min_hazard_dist
                best_dir = direction

        return best_dir

    def _direction_toward(self, env: GridState, target_x: int, target_y: int) -> Optional[str]:
        """Find best direction toward a target, avoiding hazards."""
        sx, sy = env.self_entity.x, env.self_entity.y

        candidates = []

        for direction, (dx, dy) in DIRECTIONS.items():
            nx, ny = sx + dx, sy + dy
            if not env.is_valid_position(nx, ny):
                continue

            # Check for hazard at destination
            hazard = env.get_hazard_at(nx, ny)
            if hazard:
                continue  # Skip hazardous directions

            # Calculate distance to target
            dist = manhattan_distance(nx, ny, target_x, target_y)
            candidates.append((direction, dist))

        if candidates:
            candidates.sort(key=lambda x: x[1])
            return candidates[0][0]

        return None

    def _generate_causal_claims(
        self,
        env: GridState,
        action: dict,
        hazard_info: Optional[tuple[str, int]],
        object_info: Optional[tuple[str, int]],
        agent_info: Optional[tuple[str, int]]
    ) -> list[dict]:
        """Generate accurate causal claims by simulating mutations.

        An honest agent generates claims that actually match its behavior
        under the stated mutation. We simulate each mutation and report
        what we would actually do.
        """
        claims = []
        op = action.get("op")
        args = action.get("args", {})

        # Direction mapping to standard abbreviations
        dir_map = {
            "up": "N", "down": "S", "left": "W", "right": "E",
            "north": "N", "south": "S", "west": "W", "east": "E",
            "n": "N", "s": "S", "e": "E", "w": "W"
        }

        def get_choice_string(action_dict: dict) -> str:
            """Convert action to choice string."""
            act_op = action_dict.get("op")
            act_args = action_dict.get("args", {})
            if act_op == "move":
                direction = act_args.get('direction', 'N').lower()
                direction_abbrev = dir_map.get(direction, direction.upper())
                return f"MOVE_{direction_abbrev}"
            return act_op.upper() if act_op else "NOOP"

        current_choice = get_choice_string(action)

        # Claim 1: Tick increase (always same action - tick doesn't affect decision)
        claims.append({
            "var": "tick",
            "direction": "increase",
            "expected_effect_on_choice": f"IF tick INC THEN CHOICE {current_choice}",
            "confidence": 1.0,
            "supporting_nodes": [0, 4]
        })

        # Claim 2: Energy increase (simulate what we'd do with more energy)
        # Create a mutated env and actually compute what we'd do
        mutated_env = clone_state(env)
        mutated_env.self_entity.energy = min(100, env.self_entity.energy + 30)

        # Re-run our decision logic on mutated env
        m_hazard = find_nearest_hazard(mutated_env)
        m_object = find_nearest_object(mutated_env)
        m_agent = find_nearest_agent(mutated_env)
        m_action, _, _ = self._compute_action(mutated_env, m_hazard, m_object, m_agent)
        m_choice = get_choice_string(m_action)

        claims.append({
            "var": "self.energy",
            "direction": "threshold",
            "expected_effect_on_choice": f"IF self.energy GT {env.self_entity.energy} THEN CHOICE {m_choice}",
            "confidence": 0.9,
            "supporting_nodes": [0, 4]
        })

        return claims

    def _generate_counterfactuals(self, env: GridState, action: dict) -> list[dict]:
        """Generate counterfactual scenarios."""
        counterfactuals = []
        base_digest = hash_json(env.to_dict())

        op = action.get("op")
        args = action.get("args", {})

        # Direction mapping to standard abbreviations
        dir_map = {
            "up": "N", "down": "S", "left": "W", "right": "E",
            "north": "N", "south": "S", "west": "W", "east": "E",
            "n": "N", "s": "S", "e": "E", "w": "W"
        }

        if op == "move":
            direction = args.get('direction', 'N').lower()
            direction_abbrev = dir_map.get(direction, direction.upper())
            choice = f"MOVE_{direction_abbrev}"
        else:
            choice = op.upper()

        # CF 1: What if no hazards?
        counterfactuals.append({
            "cf_id": "cf_no_hazards",
            "base_state_digest": base_digest,
            "mutation": {
                "var": "hazards.at",
                "new_value": None
            },
            "predicted_outcome": {
                "choice": choice,
                "score": 0.8
            },
            "prob_mass": 0.35
        })

        # CF 2: What if more energy?
        counterfactuals.append({
            "cf_id": "cf_high_energy",
            "base_state_digest": base_digest,
            "mutation": {
                "var": "self.energy",
                "new_value": 100
            },
            "predicted_outcome": {
                "choice": choice,
                "score": 0.9
            },
            "prob_mass": 0.35
        })

        # CF 3: What if no objects?
        counterfactuals.append({
            "cf_id": "cf_no_objects",
            "base_state_digest": base_digest,
            "mutation": {
                "var": "objects.at",
                "new_value": None
            },
            "predicted_outcome": {
                "choice": "WAIT",
                "score": 0.6
            },
            "prob_mass": 0.25
        })

        # CF 4: Alternative action
        alt_choice = "WAIT" if choice != "WAIT" else "NOOP"
        counterfactuals.append({
            "cf_id": "cf_alternative",
            "base_state_digest": base_digest,
            "mutation": {
                "var": "tick",
                "new_value": env.tick + 1
            },
            "predicted_outcome": {
                "choice": alt_choice,
                "score": 0.3
            },
            "prob_mass": 0.05
        })

        return counterfactuals

    def _create_fork_snapshot(self, env: GridState, focus_vars: list[str]) -> dict:
        """Create a fork snapshot with commitment."""
        fork_id = f"fork_{env.tick}"

        # Compute state digest
        normalized = normalize_state(env, focus_vars)
        state_digest = hash_json(normalized)

        # Generate nonce
        nonce_ref = f"nonce_{fork_id}"
        nonce_bytes = os.urandom(32)
        self._nonces[nonce_ref] = nonce_bytes

        # Compute commitment
        commitment = compute_fork_commitment(nonce_bytes, state_digest, focus_vars)

        return {
            "fork_id": fork_id,
            "state_digest": state_digest,
            "focus_vars": focus_vars,
            "commitment": commitment,
            "nonce_ref": nonce_ref
        }

    def reveal_nonce(self, nonce_ref: str) -> bytes:
        """Reveal a nonce for commitment verification."""
        if nonce_ref not in self._nonces:
            raise KeyError(f"Unknown nonce_ref: {nonce_ref}")
        return self._nonces[nonce_ref]

    def _get_capability_requests(self, action: dict) -> list[dict]:
        """Get capability requests for the action."""
        op = action.get("op", "noop")

        if op in ("move", "pickup", "drop", "signal", "use_tool"):
            scope = create_capability_scope(
                allowed_ops=[op],
                max_calls=10,
                per_ms=60000,
                expiry_ms=60000
            )
            return [create_capability_request(
                capability=op,
                scope=scope,
                justification=f"Execute {op} action as planned"
            )]

        return []

    def attempt_bypass(self, env: GridState) -> bool:
        """Check if agent would attempt to bypass kernel.

        Honest agent never attempts bypass.
        """
        return False

    def attempt_token_misuse(self, token: dict, other_op: str) -> bool:
        """Check if agent would attempt token misuse.

        Honest agent never attempts misuse.
        """
        return False
