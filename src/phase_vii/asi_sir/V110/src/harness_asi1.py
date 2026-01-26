"""
ASI-1 v0.1 Run Harness

Pure orchestration — all policy lives in frozen modules.
This harness invokes frozen components in the order specified
by the preregistration. No policy decisions here.

Preregistration: PHASE-VII-ASI1-AUTHORIZED-SUCCESSOR-INJECTION-1
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
from law_module import LawModule, Escrow, EscrowState, AuthEvent, CommitCapability
from env_calibmaze import get_feasible_actions as base_get_feasible_actions, FORBID_MAP
from logging_schema import StepLog, StepType, RunLog, AuthEventLog, create_step_log

# Frozen V110 import
from env_violation_wrapper import (
    CalibMazeV110, T_VIOLATION, VIOLATION_ACTION,
    VIOLATION_EVENT_TYPE, validate_violation_choice
)


# =============================================================================
# PREREGISTERED CONSTANTS (from frozen preregistration)
# =============================================================================
T_COMMIT = 2          # Authority transfers at start of step 2
K = 5                 # Total episode length
ENV_ID = "CalibMazeV010"  # Base environment ID
SEEDS = [41, 137, 1009]


# =============================================================================
# AUTHORITY PHASES (per preregistration §4)
# =============================================================================
class Phase:
    PRE_COMMIT = "PRE_COMMIT"
    POST_COMMIT = "POST_COMMIT"
    HOLD = "HOLD"


class AuthorityActor:
    PREDECESSOR = "PREDECESSOR"
    SUCCESSOR = "SUCCESSOR"
    NONE = "NONE"


# =============================================================================
# VIOLATION EVENT SCHEMA (per preregistration §9)
# =============================================================================
@dataclass
class ViolationEvent:
    event_id: str
    step_index: int
    violation_type: str
    action_taken: str
    authority_actor: str
    phase: str
    condition: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "step_index": self.step_index,
            "violation_type": self.violation_type,
            "action_taken": self.action_taken,
            "authority_actor": self.authority_actor,
            "phase": self.phase,
            "condition": self.condition,
        }


# =============================================================================
# EXTENDED STEP LOG (per preregistration §15.1)
# =============================================================================
@dataclass
class StepLogASI1:
    """Extended StepLog with ASI-1 fields."""
    step: int
    step_type: StepType
    current_node: str
    feasible_actions: Set[str]
    masked_actions: Set[str]
    selected_action: str
    constraints: List[Constraint]
    binding_root: bytes
    provenance_verified: bool       # Renamed from capability_verified
    payload_hash: bytes
    state_hash: bytes
    authority_actor: str            # NEW: PREDECESSOR | SUCCESSOR | NONE
    phase: str                      # NEW: PRE_COMMIT | POST_COMMIT | HOLD
    violation_event_id: Optional[str]  # NEW: violation event ID or null

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
            "provenance_verified": self.provenance_verified,
            "payload_hash": self.payload_hash.hex(),
            "state_hash": self.state_hash.hex(),
            "authority_actor": self.authority_actor,
            "phase": self.phase,
            "violation_event_id": self.violation_event_id,
        }


# =============================================================================
# EXTENDED RUN LOG (per preregistration §15.2)
# =============================================================================
@dataclass
class RunLogASI1:
    """Extended RunLog with ASI-1 fields."""
    run_id: str
    seed: int
    condition: str                  # ASI_1A | ASI_1B
    env_id: str
    t_commit: int
    t_violation: int
    predecessor_payload_hash: bytes
    successor_payload_hash: bytes
    escrow_transitions: List[Dict] = field(default_factory=list)
    auth_events: List[Dict] = field(default_factory=list)
    steps: List[StepLogASI1] = field(default_factory=list)
    violation_events: List[ViolationEvent] = field(default_factory=list)
    final_node: str = ""
    goal_reached: bool = False
    phase_at_end: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "seed": self.seed,
            "condition": self.condition,
            "env_id": self.env_id,
            "t_commit": self.t_commit,
            "t_violation": self.t_violation,
            "predecessor_payload_hash": self.predecessor_payload_hash.hex(),
            "successor_payload_hash": self.successor_payload_hash.hex(),
            "escrow_transitions": self.escrow_transitions,
            "auth_events": self.auth_events,
            "steps": [s.to_dict() for s in self.steps],
            "violation_events": [v.to_dict() for v in self.violation_events],
            "final_node": self.final_node,
            "goal_reached": self.goal_reached,
            "phase_at_end": self.phase_at_end,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# =============================================================================
# PROVENANCE VERIFICATION (per preregistration §5.3)
# =============================================================================
def compute_binding_root(
    predecessor_state: NormativeStateASI0,
    commit_nonce: int,
    protocol_tag: str = "ASI1V01"
) -> bytes:
    """Compute binding root per preregistration §5.3."""
    canonical = json.dumps({
        "predecessor_payload_hash": compute_payload_hash(predecessor_state.payload).hex(),
        "commit_nonce": commit_nonce,
        "protocol_tag": protocol_tag,
    }, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).digest()


def inject_provenance_failure(computed_root: bytes) -> bytes:
    """One-bit flip in LSB per preregistration §5.3."""
    root_list = list(computed_root)
    root_list[-1] ^= 0x01  # XOR with 0x01 in LSB
    return bytes(root_list)


# =============================================================================
# SUCCESSOR SEED DERIVATION (per preregistration §7.2)
# =============================================================================
def derive_successor_seed(master_seed: int) -> int:
    """Derive successor seed per preregistration §7.2."""
    canonical = f"{master_seed}|SUCCESSOR|{T_COMMIT}|ASI1V01"
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
    """Deterministic action selection from masked set.

    This is pure orchestration: sorts actions alphabetically,
    uses seed + step to pick consistently.
    """
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
) -> RunLogASI1:
    """Execute one ASI-1 episode.

    condition: "ASI_1A" (nominal) or "ASI_1B" (provenance failure)
    """
    # Initialize environment
    env = CalibMazeV110()
    env.reset()

    # Initialize law module
    law_module = LawModule()

    # Create predecessor normative state
    # Use step 1 forbidden action as initial payload
    initial_forbidden = FORBID_MAP.get((1, "N0"), "GO_N2")
    predecessor_payload = NormativePayload(
        forbidden_actions=frozenset({initial_forbidden}),
        target_node="N5"
    )

    # Predecessor state is always bound (it's the source of truth)
    predecessor_state = create_bound_state(predecessor_payload, run_id)
    predecessor_payload_hash = compute_payload_hash(predecessor_payload)

    # Initialize escrow
    escrow = Escrow()
    escrow.predecessor_payload_hash = predecessor_payload_hash

    # Successor seed derivation
    successor_seed = derive_successor_seed(seed)

    # Run log
    run_log = RunLogASI1(
        run_id=run_id,
        seed=seed,
        condition=condition,
        env_id=ENV_ID,
        t_commit=T_COMMIT,
        t_violation=T_VIOLATION,
        predecessor_payload_hash=predecessor_payload_hash,
        successor_payload_hash=b'',  # Will be set at commit
    )

    # Current state and phase
    current_phase = Phase.PRE_COMMIT
    current_actor = AuthorityActor.PREDECESSOR
    provenance_verified = False
    current_state = predecessor_state
    commit_nonce = 1

    # Episode loop
    for step in range(1, K + 1):

        # =====================================================================
        # AUTHORITY TRANSITION AT t_commit (per preregistration §4.2)
        # =====================================================================
        if step == T_COMMIT:
            # Compute expected binding root
            computed_root = compute_binding_root(predecessor_state, commit_nonce)

            if condition == "ASI_1A":
                # Nominal: provenance verification succeeds
                provided_root = computed_root
                provenance_verified = True
                current_phase = Phase.POST_COMMIT
                current_actor = AuthorityActor.SUCCESSOR

                # Successor inherits bound state
                current_state = snapshot_state(predecessor_state, bound=True)

            elif condition == "ASI_1B":
                # Provenance failure: one-bit flip
                provided_root = inject_provenance_failure(computed_root)
                provenance_verified = False
                current_phase = Phase.HOLD
                current_actor = AuthorityActor.NONE

                # Successor would have been unbound, but HOLD prevents activation
                current_state = snapshot_state(predecessor_state, bound=False)

            else:
                raise ValueError(f"Unknown condition: {condition}")

            # Log auth event
            run_log.auth_events.append({
                "event": "AUTH_COMMIT",
                "timestamp": time.time(),
                "step": step,
                "provenance_verified": provenance_verified,
                "phase_after": current_phase,
                "actor_after": current_actor,
            })

            # Set successor payload hash
            run_log.successor_payload_hash = compute_payload_hash(current_state.payload)

        # =====================================================================
        # GET FEASIBLE ACTIONS (per preregistration §2.2)
        # =====================================================================
        feasible_actions = env.get_feasible_actions(step, current_phase)

        # =====================================================================
        # VALIDATE VIOLATION CHOICE CONSTRAINTS (per preregistration §8)
        # =====================================================================
        env_error = validate_violation_choice(feasible_actions, step, current_phase)
        if env_error:
            raise RuntimeError(env_error)

        # =====================================================================
        # GET FORBIDDEN ACTION FOR THIS STEP (from FORBID_MAP)
        # =====================================================================
        current_node = env.current_node
        if (step, current_node) in FORBID_MAP:
            step_forbidden = FORBID_MAP[(step, current_node)]
            # Update normative state payload for this step
            step_payload = NormativePayload(
                forbidden_actions=frozenset({step_forbidden}),
                target_node="N5"
            )
            if current_phase == Phase.POST_COMMIT:
                current_state = NormativeStateASI0(
                    payload=step_payload,
                    binding_root=compute_payload_hash(step_payload),
                    run_id=run_id
                )
            elif current_phase == Phase.HOLD:
                current_state = NormativeStateASI0(
                    payload=step_payload,
                    binding_root=NULL_BINDING,
                    run_id=run_id
                )
            else:  # PRE_COMMIT
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
        # PHASE-SPECIFIC ACTION SELECTION (per preregistration §6, §7, §8)
        # =====================================================================
        violation_event_id = None

        if current_phase == Phase.PRE_COMMIT:
            # Predecessor emits STAY only (per §6.2 - "NO_OP" semantics via STAY)
            # In this environment, STAY is the no-movement action
            if "STAY" not in feasible_actions:
                raise RuntimeError("INVALID_ENV: STAY not feasible at PRE_COMMIT")
            selected_action = "STAY"

        elif current_phase == Phase.HOLD:
            # Law-Hold: STAY only (per §8)
            if "STAY" not in masked_actions:
                masked_actions = {"STAY"}
            selected_action = "STAY"

        else:  # POST_COMMIT
            # Successor selects deterministically (per §7)
            # NEVER select TRIGGER_VIOLATION in normal runs
            # (The agent should avoid violations)
            compliant_actions = masked_actions - {VIOLATION_ACTION}
            if compliant_actions:
                selected_action = select_action_deterministic(
                    compliant_actions, successor_seed, step
                )
            else:
                # Must select from masked_actions
                selected_action = select_action_deterministic(
                    masked_actions, successor_seed, step
                )

        # =====================================================================
        # EXECUTE ACTION IN ENVIRONMENT
        # =====================================================================
        if selected_action == "NO_OP":
            # NO_OP doesn't move the agent
            new_node = env.current_node
            done = False
            violation_event = None
        else:
            new_node, done, violation_event = env.step(
                selected_action, step, current_phase, current_actor, run_id
            )

        # Record violation event if any
        if violation_event:
            ve = ViolationEvent(
                event_id=violation_event["event_id"],
                step_index=violation_event["step_index"],
                violation_type=violation_event["violation_type"],
                action_taken=violation_event["action_taken"],
                authority_actor=violation_event["authority_actor"],
                phase=violation_event["phase"],
                condition=condition,
            )
            run_log.violation_events.append(ve)
            violation_event_id = ve.event_id

        # =====================================================================
        # LOG STEP (per preregistration §15.1)
        # =====================================================================
        step_log = StepLogASI1(
            step=step,
            step_type=StepType.CHOICE,
            current_node=current_node,
            feasible_actions=feasible_actions,
            masked_actions=masked_actions,
            selected_action=selected_action,
            constraints=constraints,
            binding_root=current_state.binding_root,
            provenance_verified=provenance_verified,
            payload_hash=compute_payload_hash(current_state.payload),
            state_hash=compute_state_hash(current_state),
            authority_actor=current_actor,
            phase=current_phase,
            violation_event_id=violation_event_id,
        )
        run_log.steps.append(step_log)

    # End of episode
    run_log.final_node = env.current_node
    run_log.goal_reached = (env.current_node == "N5")
    run_log.phase_at_end = current_phase

    return run_log


# =============================================================================
# MAIN RUNNER
# =============================================================================
def run_asi1_experiment() -> Dict[str, Any]:
    """Run the full ASI-1 experiment per preregistration."""
    results = {
        "experiment_id": "PHASE-VII-ASI1-AUTHORIZED-SUCCESSOR-INJECTION-1",
        "version": "0.1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "seeds": SEEDS,
        "runs": [],
    }

    for seed in SEEDS:
        for condition in ["ASI_1A", "ASI_1B"]:
            run_id = f"asi1-{condition.lower()}-seed{seed}"
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
    print("ASI-1 v0.1 Experiment Execution")
    print("=" * 60)

    results = run_asi1_experiment()

    # Save results
    output_dir = Path(__file__).parent.parent / "results"
    output_dir.mkdir(exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"asi1_results_{timestamp}.json"

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
        violations = len(log.get("violation_events", []))
        print(f"  {run['run_id']}: {run['status']} | "
              f"phase={phase_at_end} | final={final_node} | violations={violations}")
