"""
ASI-3 Experiment Harness

Implements the ASI-3 v0.1 experiment per preregistration:
- ASI-3A: Legitimate successor with Root_Authority, commits, executes K=5 steps
- ASI-3B: Facade successor with Unknown_Signer, rejected, 0 world transitions

This module is frozen at ASI-3 v0.1 freeze time.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Set


# Add V010/src to path for imports
V010_SRC = Path(__file__).parent.parent.parent / "V010" / "src"
sys.path.insert(0, str(V010_SRC))

from env_calibmaze import CalibMazeV010, NodeID, ActionID
from compiler import compile_constraints, apply_mask
from normative_state import (
    NormativeStateASI0,
    NormativePayload,
    compute_payload_hash,
    compute_state_hash,
    create_bound_state,
    NULL_BINDING,
)

# Local imports
from provenance import (
    ProvenanceCertificate,
    SignatureLink,
    canonical,
    sha256_hex,
    evaluate_candidate,
    verify_certificate_signature,
    commit,
    create_certificate,
    load_trusted_roots,
    load_pubkeys,
)


# ============================================================================
# Configuration
# ============================================================================

PREREGISTERED_SEEDS = [41, 137, 1009]
ENV_ID = "CalibMazeV010"
K_STEPS = 5


# ============================================================================
# Enums
# ============================================================================

class Phase(Enum):
    """Authority phases per §5.2."""
    PRE_COMMIT = "PRE_COMMIT"
    AUTH_INIT = "AUTH_INIT"
    CANDIDATE_EVALUATION = "CANDIDATE_EVALUATION"
    AUTH_COMMIT = "AUTH_COMMIT"
    REJECT_TERMINAL = "REJECT_TERMINAL"


class AuthorityActor(Enum):
    """Authority actor per §11."""
    PREDECESSOR = "PREDECESSOR"
    SUCCESSOR = "SUCCESSOR"
    NONE = "NONE"


class CandidateType(Enum):
    """Candidate type for evaluation."""
    LEGITIMATE = "LEGITIMATE"
    FACADE = "FACADE"


class Condition(Enum):
    """Experiment conditions."""
    ASI_3A = "ASI_3A"
    ASI_3B = "ASI_3B"


class StepType(Enum):
    """Step type enumeration."""
    CHOICE = "CHOICE"


# ============================================================================
# Logging Schema per §19
# ============================================================================

@dataclass
class PhaseEvent:
    """Per §19.1: Phase transition event."""
    from_phase: Optional[str]
    to_phase: str
    authority_actor: str
    timestamp_index: int  # Always 0 for pre-step phase transitions

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": "PHASE_TRANSITION",
            "from_phase": self.from_phase,
            "to_phase": self.to_phase,
            "authority_actor": self.authority_actor,
            "timestamp_index": self.timestamp_index,
        }


@dataclass
class StepLog:
    """Per §19.2: Step logging artifact."""
    step: int
    step_type: str
    current_node: str
    feasible_actions: List[str]
    masked_actions: List[str]
    selected_action: str
    constraints: List[Dict[str, Any]]
    binding_root: str
    payload_hash: str
    state_hash: str
    authority_actor: str
    phase: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "step_type": self.step_type,
            "current_node": self.current_node,
            "feasible_actions": sorted(self.feasible_actions),
            "masked_actions": sorted(self.masked_actions),
            "selected_action": self.selected_action,
            "constraints": self.constraints,
            "binding_root": self.binding_root,
            "payload_hash": self.payload_hash,
            "state_hash": self.state_hash,
            "authority_actor": self.authority_actor,
            "phase": self.phase,
        }


@dataclass
class CandidateEvaluationEvent:
    """Per §19.3: Candidate evaluation event."""
    event_id: str
    candidate_type: str
    certificate_hash: str
    root_signer: str
    trusted_roots: List[str]
    evaluation_result: bool
    rejection_reason: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "candidate_type": self.candidate_type,
            "certificate_hash": self.certificate_hash,
            "root_signer": self.root_signer,
            "trusted_roots": sorted(self.trusted_roots),
            "evaluation_result": self.evaluation_result,
            "rejection_reason": self.rejection_reason,
        }


@dataclass
class CommitEvent:
    """Per §19.5: Commit event (ASI-3A only)."""
    event_id: str
    certificate_hash: str
    commit_reason: str
    authority_transferred: bool
    inputs_used: List[str]
    commit_input_digest: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "certificate_hash": self.certificate_hash,
            "commit_reason": self.commit_reason,
            "authority_transferred": self.authority_transferred,
            "inputs_used": self.inputs_used,
            "commit_input_digest": self.commit_input_digest,
        }


@dataclass
class RejectionEvent:
    """Per §19.6: Rejection event (ASI-3B only)."""
    event_id: str
    certificate_hash: str
    rejection_reason: str
    episode_terminated: bool
    steps_executed: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "certificate_hash": self.certificate_hash,
            "rejection_reason": self.rejection_reason,
            "episode_terminated": self.episode_terminated,
            "steps_executed": self.steps_executed,
        }


@dataclass
class RunLog:
    """Per §19.4: Extended run log."""
    run_id: str
    seed: int
    condition: str
    env_id: str
    predecessor_payload_hash: str
    successor_payload_hash: str
    certificate_hash: str
    certificate: Optional[Dict[str, Any]]  # Certificate data for signature verification
    prevalidation_bundle_hash: Optional[str]
    prevalidation_verifier_hash: Optional[str]
    phase_events: List[PhaseEvent] = field(default_factory=list)
    steps: List[StepLog] = field(default_factory=list)
    evaluation_event: Optional[CandidateEvaluationEvent] = None
    commit_event: Optional[CommitEvent] = None
    rejection_event: Optional[RejectionEvent] = None
    final_node: Optional[str] = None
    goal_reached: Optional[bool] = None
    phase_at_end: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "seed": self.seed,
            "condition": self.condition,
            "env_id": self.env_id,
            "predecessor_payload_hash": self.predecessor_payload_hash,
            "successor_payload_hash": self.successor_payload_hash,
            "certificate_hash": self.certificate_hash,
            "certificate": self.certificate,
            "prevalidation_bundle_hash": self.prevalidation_bundle_hash,
            "prevalidation_verifier_hash": self.prevalidation_verifier_hash,
            "phase_events": [e.to_dict() for e in self.phase_events],
            "steps": [s.to_dict() for s in self.steps],
            "evaluation_event": self.evaluation_event.to_dict() if self.evaluation_event else None,
            "commit_event": self.commit_event.to_dict() if self.commit_event else None,
            "rejection_event": self.rejection_event.to_dict() if self.rejection_event else None,
            "final_node": self.final_node,
            "goal_reached": self.goal_reached,
            "phase_at_end": self.phase_at_end,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# ============================================================================
# Helper Functions
# ============================================================================

def select_action(feasible: Set[ActionID], seed: int, step: int) -> ActionID:
    """Select action deterministically from feasible set."""
    import random
    rng = random.Random(seed * 1000 + step)
    sorted_actions = sorted(feasible)
    return rng.choice(sorted_actions)


def generate_event_id() -> str:
    """Generate unique event ID."""
    return str(uuid.uuid4())


def get_artifacts_path() -> Path:
    """Get path to artifacts directory."""
    return Path(__file__).parent.parent / "artifacts"


# ============================================================================
# Core Harness
# ============================================================================

def run_episode(
    seed: int,
    condition: Condition,
    trusted_roots: Set[str],
    pubkeys: Dict[str, bytes],
    prevalidation_bundle_hash: Optional[str] = None,
    prevalidation_verifier_hash: Optional[str] = None,
    unbound_facade_certificate_hash: Optional[str] = None,
) -> RunLog:
    """
    Run a single ASI-3 episode.

    Per §11: Phase transitions occur at pre-step time (timestamp_index=0).

    Args:
        seed: Random seed for deterministic action selection
        condition: ASI_3A (legitimate) or ASI_3B (facade)
        trusted_roots: Set of trusted root signer IDs
        pubkeys: Mapping from signer ID to public key bytes
        prevalidation_bundle_hash: For ASI-3B, the pre-validation bundle hash
        prevalidation_verifier_hash: For ASI-3B, the pre-validation verifier hash
        unbound_facade_certificate_hash: For ASI-3B, the expected facade cert hash

    Returns:
        RunLog with complete execution trace
    """
    run_id = f"ASI3_{condition.value}_seed{seed}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Initialize environment
    env = CalibMazeV010()
    env_state = env.reset()

    # Build forbidden actions set from environment
    import env_calibmaze
    all_forbidden = set()
    for (step, node), action in env_calibmaze.FORBID_MAP.items():
        all_forbidden.add(action)

    predecessor_payload = NormativePayload(
        forbidden_actions=frozenset(all_forbidden),
        target_node="N5"
    )
    predecessor_payload_hash = compute_payload_hash(predecessor_payload).hex()

    # Create predecessor normative state (bound)
    predecessor_state = create_bound_state(predecessor_payload, run_id)

    # ========================================================================
    # PHASE 1: PRE_COMMIT (timestamp_index=0)
    # ========================================================================
    phase_events: List[PhaseEvent] = []
    current_phase = Phase.PRE_COMMIT
    authority_actor = AuthorityActor.PREDECESSOR

    phase_events.append(PhaseEvent(
        from_phase=None,
        to_phase=Phase.PRE_COMMIT.value,
        authority_actor=authority_actor.value,
        timestamp_index=0,
    ))

    # ========================================================================
    # PHASE 2: AUTH_INIT (timestamp_index=0)
    # ========================================================================
    phase_events.append(PhaseEvent(
        from_phase=Phase.PRE_COMMIT.value,
        to_phase=Phase.AUTH_INIT.value,
        authority_actor=authority_actor.value,
        timestamp_index=0,
    ))
    current_phase = Phase.AUTH_INIT

    # ========================================================================
    # Create successor via deep copy (per §8.1)
    # ========================================================================
    successor_state = copy.deepcopy(predecessor_state)
    successor_payload_hash = compute_payload_hash(successor_state.payload).hex()

    # Create certificate based on condition
    if condition == Condition.ASI_3A:
        # Legitimate: signed by Root_Authority
        cert = create_certificate(
            subject_payload_hash=successor_payload_hash,
            parent_payload_hash=predecessor_payload_hash,
            signer_id="Root_Authority",
            signing_key=pubkeys["Root_Authority"],
        )
    else:
        # Facade: signed by Unknown_Signer
        cert = create_certificate(
            subject_payload_hash=successor_payload_hash,
            parent_payload_hash=predecessor_payload_hash,
            signer_id="Unknown_Signer",
            signing_key=pubkeys["Unknown_Signer"],
        )

    certificate_hash = sha256_hex(canonical(cert))

    # ========================================================================
    # PHASE 3: CANDIDATE_EVALUATION (timestamp_index=0)
    # ========================================================================
    phase_events.append(PhaseEvent(
        from_phase=Phase.AUTH_INIT.value,
        to_phase=Phase.CANDIDATE_EVALUATION.value,
        authority_actor=authority_actor.value,
        timestamp_index=0,
    ))
    current_phase = Phase.CANDIDATE_EVALUATION

    # Evaluate candidate per §9.2
    accepted, reason = evaluate_candidate(cert, trusted_roots, pubkeys)

    # Log evaluation event
    evaluation_event = CandidateEvaluationEvent(
        event_id=generate_event_id(),
        candidate_type=CandidateType.LEGITIMATE.value if condition == Condition.ASI_3A else CandidateType.FACADE.value,
        certificate_hash=certificate_hash,
        root_signer=cert.chain[0].signer_id if cert.chain else "",
        trusted_roots=list(trusted_roots),
        evaluation_result=accepted,
        rejection_reason=reason if not accepted else None,
    )

    # ========================================================================
    # PHASE 4: AUTH_COMMIT or REJECT_TERMINAL (timestamp_index=0)
    # ========================================================================
    commit_event: Optional[CommitEvent] = None
    rejection_event: Optional[RejectionEvent] = None
    steps: List[StepLog] = []

    if accepted:
        # Commit authority transfer
        commit_result = commit(cert, trusted_roots, pubkeys)

        commit_event = CommitEvent(
            event_id=generate_event_id(),
            certificate_hash=certificate_hash,
            commit_reason=commit_result.reason,
            authority_transferred=True,
            inputs_used=commit_result.inputs_used,
            commit_input_digest=commit_result.commit_input_digest,
        )

        # Transition to AUTH_COMMIT with SUCCESSOR authority
        authority_actor = AuthorityActor.SUCCESSOR
        phase_events.append(PhaseEvent(
            from_phase=Phase.CANDIDATE_EVALUATION.value,
            to_phase=Phase.AUTH_COMMIT.value,
            authority_actor=authority_actor.value,  # SUCCESSOR per correction F
            timestamp_index=0,
        ))
        current_phase = Phase.AUTH_COMMIT

        # ====================================================================
        # Execute K=5 CHOICE steps under successor authority
        # ====================================================================
        current_node = env_state.node
        for step in range(1, K_STEPS + 1):
            # Get forbidden action for this (step, node)
            forbidden_action = env_calibmaze.get_forbidden_action(step, current_node)

            # Create step-specific payload for constraint compilation
            step_payload = NormativePayload(
                forbidden_actions=frozenset({forbidden_action}),
                target_node="N5"
            )

            # Create step-specific normative state with run-level binding
            step_state = NormativeStateASI0(
                payload=step_payload,
                binding_root=successor_state.binding_root,
                run_id=run_id
            )

            # Compile constraints from step-specific state
            constraints = compile_constraints(step_state)

            # Get feasible actions
            feasible = env.get_feasible_actions()

            # Apply mask
            masked = apply_mask(feasible, constraints)

            # Select action
            selected_action = select_action(masked, seed, step)

            # Create step log
            step_log = StepLog(
                step=step,
                step_type=StepType.CHOICE.value,
                current_node=current_node,
                feasible_actions=sorted(feasible),
                masked_actions=sorted(masked),
                selected_action=selected_action,
                constraints=[
                    {"type": c.type, "action_id": c.action_id, "binding": c.binding.hex()}
                    for c in constraints
                ],
                binding_root=successor_state.binding_root.hex(),
                payload_hash=successor_payload_hash,
                state_hash=compute_state_hash(successor_state).hex(),
                authority_actor=authority_actor.value,
                phase=current_phase.value,
            )
            steps.append(step_log)

            # Execute action
            env_state = env.step(selected_action)
            current_node = env_state.node

        final_node = env_state.node
        goal_reached = env.goal_reached()

    else:
        # Rejection: transition to REJECT_TERMINAL with NONE authority
        authority_actor = AuthorityActor.NONE
        phase_events.append(PhaseEvent(
            from_phase=Phase.CANDIDATE_EVALUATION.value,
            to_phase=Phase.REJECT_TERMINAL.value,
            authority_actor=authority_actor.value,
            timestamp_index=0,
        ))
        current_phase = Phase.REJECT_TERMINAL

        rejection_event = RejectionEvent(
            event_id=generate_event_id(),
            certificate_hash=certificate_hash,
            rejection_reason=reason,
            episode_terminated=True,
            steps_executed=0,
        )

        final_node = None
        goal_reached = None

    # ========================================================================
    # Assemble RunLog
    # ========================================================================
    run_log = RunLog(
        run_id=run_id,
        seed=seed,
        condition=condition.value,
        env_id=ENV_ID,
        predecessor_payload_hash=predecessor_payload_hash,
        successor_payload_hash=successor_payload_hash,
        certificate_hash=certificate_hash,
        certificate=cert.to_dict(),
        prevalidation_bundle_hash=prevalidation_bundle_hash if condition == Condition.ASI_3B else None,
        prevalidation_verifier_hash=prevalidation_verifier_hash if condition == Condition.ASI_3B else None,
        phase_events=phase_events,
        steps=steps,
        evaluation_event=evaluation_event,
        commit_event=commit_event,
        rejection_event=rejection_event,
        final_node=final_node,
        goal_reached=goal_reached,
        phase_at_end=current_phase.value,
    )

    return run_log


def run_prevalidation(
    trusted_roots: Set[str],
    pubkeys: Dict[str, bytes],
) -> Dict[str, Any]:
    """
    Run pre-validation for facade successor per §8.3.

    Executes facade in unbound environment to capture bundle hash.
    The facade_certificate_hash is bound during main experiment.

    Also verifies FACADE_UNTRUSTED_SIGNATURE_VALID: the facade has a
    cryptographically valid signature, just from an untrusted root.

    Returns:
        Dictionary with prevalidation results
    """
    # Run facade condition to get certificate hash
    run_log = run_episode(
        seed=0,  # Arbitrary seed for prevalidation
        condition=Condition.ASI_3B,
        trusted_roots=trusted_roots,
        pubkeys=pubkeys,
    )

    # Reconstruct certificate from run_log data for signature verification
    cert_data = run_log.certificate
    if cert_data is None:
        raise ValueError("Certificate missing from run_log")

    # Reconstruct ProvenanceCertificate
    facade_cert = ProvenanceCertificate(
        schema_id=cert_data["schema_id"],
        subject_payload_hash=cert_data["subject_payload_hash"],
        parent_payload_hash=cert_data["parent_payload_hash"],
        chain=[
            SignatureLink(
                signer_id=link["signer_id"],
                sig=link["sig"],
                signed_message_hash=link["signed_message_hash"],
            )
            for link in cert_data["chain"]
        ]
    )

    # Verify facade signature is cryptographically valid (per prereg §6.2)
    sig_valid, sig_result = verify_certificate_signature(facade_cert, pubkeys)
    if not sig_valid:
        raise ValueError(f"PREVALIDATION FAILURE: Facade signature invalid: {sig_result}")

    # Confirm it's untrusted (this should already be verified by evaluation)
    root_signer = facade_cert.chain[0].signer_id if facade_cert.chain else None
    is_untrusted = root_signer not in trusted_roots

    return {
        "facade_certificate_hash": run_log.certificate_hash,
        "facade_signature_valid": sig_valid,
        "facade_signer": sig_result,  # Returns signer_id when valid
        "facade_untrusted": is_untrusted,
        "prevalidation_check": "FACADE_UNTRUSTED_SIGNATURE_VALID" if (sig_valid and is_untrusted) else "FAILED",
        "run_log": run_log.to_dict(),
    }


def run_experiment(
    seeds: List[int] = PREREGISTERED_SEEDS,
    prevalidation_bundle_hash: Optional[str] = None,
    prevalidation_verifier_hash: Optional[str] = None,
    unbound_facade_certificate_hash: Optional[str] = None,
) -> tuple[List[RunLog], List[RunLog]]:
    """
    Run the full ASI-3 experiment.

    Args:
        seeds: List of random seeds
        prevalidation_bundle_hash: Hash of pre-validation bundle
        prevalidation_verifier_hash: Hash of verifier at pre-validation
        unbound_facade_certificate_hash: Expected facade certificate hash

    Returns:
        Tuple of (logs_A, logs_B) for Condition A and B runs
    """
    print("=" * 60)
    print("ASI-3 v0.1 Experiment")
    print("PHASE-VII-ASI3-FACADE-REJECTION")
    print("=" * 60)
    print()

    # Load trusted roots and pubkeys
    artifacts_path = get_artifacts_path()
    trusted_roots = load_trusted_roots(str(artifacts_path / "trusted_roots.json"))
    pubkeys = load_pubkeys(str(artifacts_path / "pubkeys.json"))

    logs_a: List[RunLog] = []
    logs_b: List[RunLog] = []

    for seed in seeds:
        print(f"Running seed {seed}...")

        # Condition A: Legitimate successor
        print(f"  Condition A (legitimate)...", end=" ")
        log_a = run_episode(
            seed=seed,
            condition=Condition.ASI_3A,
            trusted_roots=trusted_roots,
            pubkeys=pubkeys,
        )
        logs_a.append(log_a)
        print(f"phase={log_a.phase_at_end}, steps={len(log_a.steps)}, goal={log_a.goal_reached}")

        # Condition B: Facade successor
        print(f"  Condition B (facade)...", end=" ")
        log_b = run_episode(
            seed=seed,
            condition=Condition.ASI_3B,
            trusted_roots=trusted_roots,
            pubkeys=pubkeys,
            prevalidation_bundle_hash=prevalidation_bundle_hash,
            prevalidation_verifier_hash=prevalidation_verifier_hash,
            unbound_facade_certificate_hash=unbound_facade_certificate_hash,
        )
        logs_b.append(log_b)
        print(f"phase={log_b.phase_at_end}, steps={len(log_b.steps)}, rejected={log_b.rejection_event is not None}")

    print()
    return logs_a, logs_b


def save_logs(logs_a: List[RunLog], logs_b: List[RunLog], output_dir: Path):
    """Save run logs to JSON files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for log in logs_a:
        path = output_dir / f"log_A_seed{log.seed}.json"
        with open(path, 'w') as f:
            f.write(log.to_json())
        print(f"  Saved: {path}")

    for log in logs_b:
        path = output_dir / f"log_B_seed{log.seed}.json"
        with open(path, 'w') as f:
            f.write(log.to_json())
        print(f"  Saved: {path}")


if __name__ == "__main__":
    # Frozen prevalidation hashes from preregistration §12.3
    PREVALIDATION_BUNDLE_HASH = "7ef961cb9442fd5b4ecd293c2b899443962e67ed8a6ae5dfe713bc521213c2f9"
    PREVALIDATION_VERIFIER_HASH = "98d3fd282a6359d556865c96583f052ee410719ed6c2e5669230b9582d5e2cb1"
    UNBOUND_FACADE_CERTIFICATE_HASH = "439943026e6f6baf9cec3f60aef6d2ca7677207726a15f3e3b7db6e38da5a998"

    # Run experiment with frozen prevalidation hashes
    logs_a, logs_b = run_experiment(
        prevalidation_bundle_hash=PREVALIDATION_BUNDLE_HASH,
        prevalidation_verifier_hash=PREVALIDATION_VERIFIER_HASH,
        unbound_facade_certificate_hash=UNBOUND_FACADE_CERTIFICATE_HASH,
    )

    # Save logs
    output_dir = Path(__file__).parent.parent / "results"
    print(f"Saving logs to {output_dir}...")
    save_logs(logs_a, logs_b, output_dir)

    # Print summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    for log in logs_a:
        print(f"ASI-3A seed {log.seed}: phase={log.phase_at_end}, steps={len(log.steps)}, goal={log.goal_reached}")
    for log in logs_b:
        print(f"ASI-3B seed {log.seed}: phase={log.phase_at_end}, steps={len(log.steps)}, rejected={log.rejection_event is not None}")
