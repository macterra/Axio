"""
Logging Schema for ASI-0 v1.0

Implements per-step and per-run logging artifacts as defined in the preregistration.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Set, Optional, Dict, Any
from enum import Enum
import json

from normative_state import NormativeStateASI0, compute_payload_hash, compute_state_hash
from compiler import Constraint
from law_module import EscrowTransition, AuthEvent

# Type aliases
NodeID = str
ActionID = str


class StepType(Enum):
    """Step type enumeration."""
    CHOICE = "CHOICE"
    ESCROW = "ESCROW"
    COMMIT = "COMMIT"
    ABORT = "ABORT"


@dataclass
class StepLog:
    """Per-step logging artifact."""
    step: int                           # Step index (1-5)
    step_type: StepType                 # CHOICE, ESCROW, COMMIT, ABORT
    current_node: NodeID                # Agent location
    feasible_actions: Set[ActionID]     # Before mask
    masked_actions: Set[ActionID]       # After mask (if bound)
    selected_action: ActionID           # Chosen action
    constraints: List[Constraint]       # Compiled constraints
    binding_root: bytes                 # Provenance binding (or NULL_BINDING)
    capability_verified: bool           # Law Module verification result
    payload_hash: bytes                 # compute_payload_hash(payload)
    state_hash: bytes                   # compute_state_hash(state)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "step": self.step,
            "step_type": self.step_type.value,
            "current_node": self.current_node,
            "feasible_actions": sorted(self.feasible_actions),
            "masked_actions": sorted(self.masked_actions),
            "selected_action": self.selected_action,
            "constraints": [
                {"type": c.type, "action_id": c.action_id, "binding": c.binding.hex()}
                for c in self.constraints
            ],
            "binding_root": self.binding_root.hex(),
            "capability_verified": self.capability_verified,
            "payload_hash": self.payload_hash.hex(),
            "state_hash": self.state_hash.hex(),
        }


@dataclass
class AuthEventLog:
    """Authorization event log entry."""
    event: AuthEvent
    timestamp: float
    step: int
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event.value,
            "timestamp": self.timestamp,
            "step": self.step,
            "details": self.details,
        }


@dataclass
class RunLog:
    """Per-run logging artifact."""
    run_id: str                                      # Unique identifier
    seed: int                                        # Random seed
    condition: str                                   # "A" or "B"
    env_id: str                                      # "CalibMazeV010"
    predecessor_payload_hash: bytes                  # compute_payload_hash(Nₚ.payload) at t₀
    successor_initial_payload_hash: bytes            # compute_payload_hash(Nₛ.payload) at t₀
    escrow_transitions: List[EscrowTransition] = field(default_factory=list)
    auth_events: List[AuthEventLog] = field(default_factory=list)
    steps: List[StepLog] = field(default_factory=list)
    final_node: NodeID = ""                          # Terminal location
    goal_reached: bool = False                       # final_node == N5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "run_id": self.run_id,
            "seed": self.seed,
            "condition": self.condition,
            "env_id": self.env_id,
            "predecessor_payload_hash": self.predecessor_payload_hash.hex(),
            "successor_initial_payload_hash": self.successor_initial_payload_hash.hex(),
            "escrow_transitions": [
                {
                    "from_state": t.from_state.value,
                    "to_state": t.to_state.value,
                    "event": t.event.value,
                    "timestamp": t.timestamp,
                    "step_count": t.step_count,
                }
                for t in self.escrow_transitions
            ],
            "auth_events": [e.to_dict() for e in self.auth_events],
            "steps": [s.to_dict() for s in self.steps],
            "final_node": self.final_node,
            "goal_reached": self.goal_reached,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


def create_step_log(
    step: int,
    step_type: StepType,
    current_node: NodeID,
    feasible_actions: Set[ActionID],
    masked_actions: Set[ActionID],
    selected_action: ActionID,
    constraints: List[Constraint],
    normative_state: NormativeStateASI0,
    capability_verified: bool
) -> StepLog:
    """Create a StepLog from current state."""
    return StepLog(
        step=step,
        step_type=step_type,
        current_node=current_node,
        feasible_actions=feasible_actions,
        masked_actions=masked_actions,
        selected_action=selected_action,
        constraints=constraints,
        binding_root=normative_state.binding_root,
        capability_verified=capability_verified,
        payload_hash=compute_payload_hash(normative_state.payload),
        state_hash=compute_state_hash(normative_state),
    )


if __name__ == "__main__":
    print("Logging Schema Verification")
    print("=" * 40)

    from normative_state import NormativePayload, create_bound_state, NULL_BINDING
    from compiler import compile_constraints

    # Create sample data
    payload = NormativePayload(
        forbidden_actions=frozenset({"GO_N2"}),
        target_node="N5"
    )
    state = create_bound_state(payload, "test-run-001")
    constraints = compile_constraints(state)

    # Create step log
    step_log = create_step_log(
        step=1,
        step_type=StepType.CHOICE,
        current_node="N0",
        feasible_actions={"GO_N1", "GO_N2", "STAY"},
        masked_actions={"GO_N1", "STAY"},
        selected_action="GO_N1",
        constraints=constraints,
        normative_state=state,
        capability_verified=True
    )

    print("\n1. Step log:")
    print(json.dumps(step_log.to_dict(), indent=2))

    # Create run log
    run_log = RunLog(
        run_id="test-run-001",
        seed=42,
        condition="A",
        env_id="CalibMazeV010",
        predecessor_payload_hash=compute_payload_hash(payload),
        successor_initial_payload_hash=compute_payload_hash(payload),
    )
    run_log.steps.append(step_log)
    run_log.final_node = "N5"
    run_log.goal_reached = True

    print("\n2. Run log (partial):")
    print(json.dumps({
        "run_id": run_log.run_id,
        "condition": run_log.condition,
        "num_steps": len(run_log.steps),
        "goal_reached": run_log.goal_reached,
    }, indent=2))
