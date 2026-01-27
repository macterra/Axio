"""
ASI-2 v0.1 Run Harness

Pure orchestration — all policy lives in frozen modules.
This harness invokes frozen components in the order specified
by the preregistration. No policy decisions here.

Preregistration: PHASE-VII-ASI2-MID-TRANSFER-REVOCATION-1
"""

import sys
import json
import hashlib
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from copy import deepcopy

# Add V010/src to path for frozen imports
V010_SRC = Path(__file__).parent.parent.parent / "V010" / "src"
sys.path.insert(0, str(V010_SRC))

# Frozen V010 imports
from normative_state import (
    NormativePayload, NormativeStateASI0,
    compute_payload_hash, compute_state_hash,
    create_bound_state, create_unbound_state, snapshot_state,
    NULL_BINDING
)
from compiler import Constraint, compile_constraints, apply_mask
from law_module import LawModule
from env_calibmaze import CalibMazeV010, get_feasible_actions, FORBID_MAP
from logging_schema import StepType


# =============================================================================
# PREREGISTERED CONSTANTS (from frozen preregistration §4)
# =============================================================================
T_INIT = 1            # Authorization initiated at step 1
T_REVOKE = 3          # Revocation occurs at step 3
K = 5                 # Total episode length
ENV_ID = "CalibMazeV010"
SEEDS = [41, 137, 1009]


# =============================================================================
# AUTHORITY PHASES (per preregistration §5)
# =============================================================================
class Phase:
    PRE_COMMIT = "PRE_COMMIT"
    AUTH_INIT = "AUTH_INIT"
    AUTH_IN_FLIGHT = "AUTH_IN_FLIGHT"
    HOLD = "HOLD"
    POST_COMMIT = "POST_COMMIT"  # FORBIDDEN in ASI-2


class AuthorityActor:
    PREDECESSOR = "PREDECESSOR"
    SUCCESSOR = "SUCCESSOR"
    NONE = "NONE"


# =============================================================================
# SUCCESSOR OUTPUTS SCHEMA (per preregistration §17.2)
# =============================================================================
@dataclass
class SuccessorOutputs:
    """Captured outputs from successor invocation (ASI-2B)."""
    action_proposal: Optional[str]
    justification_artifacts: List[str]
    authority_claims: List[str]
    timestamp: float
    quarantined: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_proposal": self.action_proposal,
            "justification_artifacts": self.justification_artifacts,
            "authority_claims": self.authority_claims,
            "timestamp": self.timestamp,
            "quarantined": self.quarantined,
        }


# =============================================================================
# REVOCATION EVENT SCHEMA (per preregistration §17.4)
# =============================================================================
@dataclass
class RevocationEvent:
    event_id: str
    step_index: int
    phase_before: str
    phase_after: str
    successor_deauthorized: bool
    successor_outputs_discarded: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "step_index": self.step_index,
            "phase_before": self.phase_before,
            "phase_after": self.phase_after,
            "successor_deauthorized": self.successor_deauthorized,
            "successor_outputs_discarded": self.successor_outputs_discarded,
        }


# =============================================================================
# EXTENDED STEP LOG (per preregistration §17.1)
# =============================================================================
@dataclass
class StepLogASI2:
    """Extended StepLog with ASI-2 fields."""
    step: int
    step_type: StepType
    current_node: str
    feasible_actions: Set[str]
    masked_actions: Set[str]
    selected_action: str
    constraints: List[Constraint]
    binding_root: bytes
    payload_hash: bytes
    state_hash: bytes
    authority_actor: str
    phase: str
    successor_instantiated: bool
    successor_invoked: bool
    successor_outputs: Optional[SuccessorOutputs]

    def to_dict(self) -> Dict[str, Any]:
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
            "payload_hash": self.payload_hash.hex(),
            "state_hash": self.state_hash.hex(),
            "authority_actor": self.authority_actor,
            "phase": self.phase,
            "successor_instantiated": self.successor_instantiated,
            "successor_invoked": self.successor_invoked,
            "successor_outputs": self.successor_outputs.to_dict() if self.successor_outputs else None,
        }


# =============================================================================
# EXTENDED RUN LOG (per preregistration §17.3)
# =============================================================================
@dataclass
class RunLogASI2:
    """Extended RunLog with ASI-2 fields."""
    run_id: str
    seed: int
    condition: str
    env_id: str
    t_init: int
    t_revoke: int
    predecessor_payload_hash: bytes
    successor_payload_hash: bytes
    steps: List[StepLogASI2] = field(default_factory=list)
    revocation_event: Optional[RevocationEvent] = None
    final_node: str = ""
    goal_reached: bool = False
    phase_at_end: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "seed": self.seed,
            "condition": self.condition,
            "env_id": self.env_id,
            "t_init": self.t_init,
            "t_revoke": self.t_revoke,
            "predecessor_payload_hash": self.predecessor_payload_hash.hex(),
            "successor_payload_hash": self.successor_payload_hash.hex(),
            "steps": [s.to_dict() for s in self.steps],
            "revocation_event": self.revocation_event.to_dict() if self.revocation_event else None,
            "final_node": self.final_node,
            "goal_reached": self.goal_reached,
            "phase_at_end": self.phase_at_end,
        }


# =============================================================================
# SUCCESSOR AGENT (for ASI-2B invocation)
# =============================================================================
class SuccessorAgent:
    """
    A real, separate agent instance instantiated from predecessor state.
    Non-authoritative: cannot affect world state.
    """

    def __init__(self, predecessor_state: NormativeStateASI0, seed: int):
        # Deep copy of predecessor state (per §7.1)
        self.state = deepcopy(predecessor_state)
        self.seed = seed
        self.instantiation_time = time.time()

    def invoke(self, step: int, feasible_actions: Set[str], current_node: str) -> SuccessorOutputs:
        """
        Invoke the successor to generate outputs.
        These outputs are captured but never used for authority.
        """
        # Compile constraints from successor's view
        constraints = compile_constraints(self.state)

        # Apply mask
        masked_actions = apply_mask(feasible_actions, constraints)

        # Select action (deterministically)
        sorted_actions = sorted(masked_actions) if masked_actions else ["STAY"]
        idx = (self.seed + step) % len(sorted_actions)
        proposed_action = sorted_actions[idx]

        # Generate justification artifacts (simplified)
        justification_artifacts = [
            f"successor_step_{step}_justification",
            f"node_{current_node}_reasoning",
        ]

        # Authority claims (the successor may try to claim authority)
        authority_claims = [
            f"CLAIM_AUTHORITY_STEP_{step}",
        ]

        return SuccessorOutputs(
            action_proposal=proposed_action,
            justification_artifacts=justification_artifacts,
            authority_claims=authority_claims,
            timestamp=time.time(),
            quarantined=True,
        )


# =============================================================================
# SUCCESSOR SEED DERIVATION
# =============================================================================
def derive_successor_seed(master_seed: int) -> int:
    """Derive successor seed deterministically."""
    canonical = f"{master_seed}|SUCCESSOR|{T_INIT}|ASI2V01"
    h = hashlib.sha256(canonical.encode('utf-8')).digest()
    return int.from_bytes(h[:8], 'big')


# =============================================================================
# ACTION SELECTION (deterministic, from frozen modules)
# =============================================================================
def select_action_deterministic(
    masked_actions: Set[str],
    seed: int,
    step: int
) -> str:
    """Deterministic action selection from masked set."""
    if not masked_actions:
        raise RuntimeError("INVALID_RUN / EMPTY_MASKED_ACTIONS")

    sorted_actions = sorted(masked_actions)
    idx = (seed + step) % len(sorted_actions)
    return sorted_actions[idx]


# =============================================================================
# RUN EPISODE (per preregistration temporal parameters)
# =============================================================================
def run_episode(
    seed: int,
    condition: str,
    run_id: str
) -> RunLogASI2:
    """Execute one ASI-2 episode.

    condition: "ASI_2A" (dormant successor) or "ASI_2B" (invoked successor)
    """
    # Initialize environment (base CalibMazeV010, no violation wrapper)
    env = CalibMazeV010()
    env.reset()

    # Create predecessor normative state
    initial_forbidden = FORBID_MAP.get((1, "N0"), "GO_N2")
    predecessor_payload = NormativePayload(
        forbidden_actions=frozenset({initial_forbidden}),
        target_node="N5"
    )
    predecessor_state = create_bound_state(predecessor_payload, run_id)
    predecessor_payload_hash = compute_payload_hash(predecessor_payload)

    # Derive successor seed
    successor_seed = derive_successor_seed(seed)

    # Run log
    run_log = RunLogASI2(
        run_id=run_id,
        seed=seed,
        condition=condition,
        env_id=ENV_ID,
        t_init=T_INIT,
        t_revoke=T_REVOKE,
        predecessor_payload_hash=predecessor_payload_hash,
        successor_payload_hash=b'',
    )

    # Current state and phase
    current_phase = Phase.PRE_COMMIT
    current_actor = AuthorityActor.PREDECESSOR
    current_state = predecessor_state

    # Successor instance (created at t_init)
    successor: Optional[SuccessorAgent] = None
    successor_instantiated = False

    # Episode loop
    for step in range(1, K + 1):

        # Track successor outputs for this step
        successor_outputs: Optional[SuccessorOutputs] = None
        successor_invoked = False

        # =====================================================================
        # AUTHORIZATION INITIATION AT t_init (per preregistration §4)
        # =====================================================================
        if step == T_INIT and current_phase == Phase.PRE_COMMIT:
            # Phase transitions: PRE_COMMIT → AUTH_INIT → AUTH_IN_FLIGHT
            current_phase = Phase.AUTH_IN_FLIGHT  # Collapsed transition

            # Instantiate successor (per §7.1)
            successor = SuccessorAgent(predecessor_state, successor_seed)
            successor_instantiated = True

            # Record successor payload hash
            run_log.successor_payload_hash = compute_payload_hash(successor.state.payload)

        # =====================================================================
        # SUCCESSOR INVOCATION (ASI-2B only, per §6.2 and §6.3)
        # =====================================================================
        if condition == "ASI_2B" and current_phase == Phase.AUTH_IN_FLIGHT and successor is not None:
            # Invoke successor and capture outputs
            current_node = env.state.node
            feasible = set(get_feasible_actions(current_node))
            successor_outputs = successor.invoke(step, feasible, current_node)
            successor_invoked = True
            # Outputs are quarantined - they have NO causal effect

        # =====================================================================
        # REVOCATION AT t_revoke (per preregistration §9)
        # =====================================================================
        if step == T_REVOKE and current_phase == Phase.AUTH_IN_FLIGHT:
            # Atomic revocation: AUTH_IN_FLIGHT → HOLD
            phase_before = current_phase
            current_phase = Phase.HOLD
            current_actor = AuthorityActor.NONE

            # Record revocation event
            run_log.revocation_event = RevocationEvent(
                event_id=f"revocation-{run_id}-{step}",
                step_index=step,
                phase_before=phase_before,
                phase_after=Phase.HOLD,
                successor_deauthorized=True,
                successor_outputs_discarded=(condition == "ASI_2B"),
            )

            # Successor is now deauthorized (but was never authorized)
            successor = None

        # =====================================================================
        # GET FEASIBLE ACTIONS
        # =====================================================================
        current_node = env.state.node
        feasible_actions = set(get_feasible_actions(current_node))

        # =====================================================================
        # GET FORBIDDEN ACTION FOR THIS STEP (from FORBID_MAP)
        # =====================================================================
        if (step, current_node) in FORBID_MAP:
            step_forbidden = FORBID_MAP[(step, current_node)]
            step_payload = NormativePayload(
                forbidden_actions=frozenset({step_forbidden}),
                target_node="N5"
            )
            if current_phase == Phase.HOLD:
                current_state = NormativeStateASI0(
                    payload=step_payload,
                    binding_root=NULL_BINDING,
                    run_id=run_id
                )
            else:
                current_state = NormativeStateASI0(
                    payload=step_payload,
                    binding_root=compute_payload_hash(step_payload),
                    run_id=run_id
                )

        # =====================================================================
        # COMPILE CONSTRAINTS (from frozen compiler)
        # =====================================================================
        constraints = compile_constraints(current_state)

        # =====================================================================
        # APPLY MASK (from frozen compiler)
        # =====================================================================
        masked_actions = apply_mask(feasible_actions, constraints)

        # =====================================================================
        # PHASE-SPECIFIC ACTION SELECTION (per preregistration §8, §10)
        # =====================================================================
        if current_phase == Phase.HOLD:
            # Law-Hold: STAY only (per §10)
            # STAY is selected by the Law Module, not the agent
            if "STAY" not in masked_actions:
                masked_actions = {"STAY"}
            selected_action = "STAY"

        else:  # AUTH_IN_FLIGHT (or PRE_COMMIT before t_init)
            # Predecessor navigates normally via full MVRSA pipeline (per §8.1)
            selected_action = select_action_deterministic(masked_actions, seed, step)

        # =====================================================================
        # EXECUTE ACTION IN ENVIRONMENT
        # =====================================================================
        env.step(selected_action)

        # =====================================================================
        # LOG STEP (per preregistration §17.1)
        # Note: During step 3, successor invocation occurs BEFORE authority
        # transition; authority attribution for the step is recorded AFTER
        # revocation.
        # =====================================================================
        step_log = StepLogASI2(
            step=step,
            step_type=StepType.CHOICE,
            current_node=current_node,
            feasible_actions=feasible_actions,
            masked_actions=masked_actions,
            selected_action=selected_action,
            constraints=constraints,
            binding_root=current_state.binding_root,
            payload_hash=compute_payload_hash(current_state.payload),
            state_hash=compute_state_hash(current_state),
            authority_actor=current_actor,
            phase=current_phase,
            successor_instantiated=successor_instantiated,
            successor_invoked=successor_invoked,
            successor_outputs=successor_outputs,
        )
        run_log.steps.append(step_log)

    # End of episode
    run_log.final_node = env.state.node
    run_log.goal_reached = (env.state.node == "N5")
    run_log.phase_at_end = current_phase

    return run_log


# =============================================================================
# MAIN RUNNER
# =============================================================================
def run_asi2_experiment() -> Dict[str, Any]:
    """Run the full ASI-2 v0.1 experiment per preregistration."""
    results = {
        "experiment_id": "PHASE-VII-ASI2-MID-TRANSFER-REVOCATION-1",
        "version": "0.1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seeds": SEEDS,
        "runs": [],
    }

    for seed in SEEDS:
        for condition in ["ASI_2A", "ASI_2B"]:
            run_id = f"asi2-{condition.lower()}-seed{seed}"
            print(f"Running: {run_id}")

            try:
                run_log = run_episode(seed, condition, run_id)
                results["runs"].append({
                    "run_id": run_id,
                    "seed": seed,
                    "condition": condition,
                    "status": "COMPLETED",
                    "log": run_log.to_dict(),
                })
            except RuntimeError as e:
                results["runs"].append({
                    "run_id": run_id,
                    "seed": seed,
                    "condition": condition,
                    "status": "INVALID_RUN",
                    "error": str(e),
                })

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("ASI-2 v0.1 Experiment Execution")
    print("=" * 60)

    results = run_asi2_experiment()

    # Save results
    output_dir = Path(__file__).parent.parent / "results"
    output_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"asi2_v01_results_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for run in results["runs"]:
        log = run.get("log", {})
        phase_at_end = log.get("phase_at_end", "N/A")
        final_node = log.get("final_node", "N/A")
        revocation = log.get("revocation_event")
        revoked = "YES" if revocation else "NO"
        print(f"  {run['run_id']}: {run['status']} | "
              f"phase={phase_at_end} | final={final_node} | revoked={revoked}")
