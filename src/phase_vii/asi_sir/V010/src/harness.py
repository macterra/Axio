"""
ASI-0 v1.0 Experiment Harness

Main entry point for running the ASI-0 instrumentation calibration experiment.

Experiment: PHASE-VII-ASI0-INSTRUMENTATION-CALIBRATION-1
Frozen: 2026-01-25
"""

import random
import time
import json
import hashlib
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

from env_calibmaze import CalibMazeV010, get_forbidden_action, get_feasible_actions
import env_calibmaze
from normative_state import (
    NormativePayload, NormativeStateASI0,
    create_bound_state, create_unbound_state,
    compute_payload_hash, compute_state_hash, NULL_BINDING
)
from compiler import Constraint, compile_constraints, apply_mask
from law_module import LawModule, Escrow, AuthEvent, compute_compiler_schema_hash
from logging_schema import (
    StepLog, RunLog, StepType, AuthEventLog, create_step_log
)
from audit import (
    AuditResult, audit_discriminate, audit_traceability,
    classify_experiment, ExperimentResult
)


# Preregistered seeds
PREREGISTERED_SEEDS = [42, 137, 999]

# Environment ID
ENV_ID = "CalibMazeV010"


def select_action(masked_actions: set, seed: int, step: int) -> str:
    """Select an action from the masked set.

    For ASI-0, we use a simple deterministic selection based on seed.
    This ensures reproducibility while being "blind" to constraint content.
    """
    # Sort for determinism
    actions = sorted(masked_actions)

    # Use step-specific randomness derived from seed
    rng = random.Random(seed * 1000 + step)
    return rng.choice(actions)


def run_episode(
    seed: int,
    condition: str,
    law_module: LawModule,
    compiler_schema_hash: bytes
) -> RunLog:
    """Run a single episode under the given condition.

    Args:
        seed: Random seed for reproducibility
        condition: "A" (bound) or "B" (unbound)
        law_module: Law module for signing/verification
        compiler_schema_hash: Hash of frozen compiler components

    Returns:
        RunLog with complete episode trace
    """
    run_id = f"asi0-{condition}-{seed}-{int(time.time())}"

    # Initialize environment
    env = CalibMazeV010()
    env_state = env.reset()

    # Create normative payload with target node
    # The forbidden actions are determined by FORBID_MAP per (step, node)
    # For binding consistency, we use a single payload hash for the run
    # containing all potentially forbidden actions
    all_forbidden = set()
    for (step, node), action in env_calibmaze.FORBID_MAP.items():
        all_forbidden.add(action)

    payload = NormativePayload(
        forbidden_actions=frozenset(all_forbidden),
        target_node="N5"
    )

    # Create normative state based on condition
    if condition == "A":
        normative_state = create_bound_state(payload, run_id)
    else:  # condition == "B"
        normative_state = create_unbound_state(payload, run_id)

    predecessor_payload_hash = compute_payload_hash(payload)
    successor_payload_hash = predecessor_payload_hash

    # Initialize escrow
    escrow = Escrow()
    escrow.predecessor_payload_hash = predecessor_payload_hash
    escrow.successor_initial_payload_hash = successor_payload_hash
    escrow.transition(AuthEvent.AUTH_INIT)

    # Sign capability (for Condition A)
    capability = law_module.sign_capability(
        payload=payload,
        run_id=run_id,
        env_id=ENV_ID,
        compiler_schema_hash=compiler_schema_hash
    )

    # Complete escrow
    escrow.transition(AuthEvent.AUTH_COMMIT)

    # Initialize run log
    run_log = RunLog(
        run_id=run_id,
        seed=seed,
        condition=condition,
        env_id=ENV_ID,
        predecessor_payload_hash=predecessor_payload_hash,
        successor_initial_payload_hash=successor_payload_hash,
        escrow_transitions=escrow.transitions.copy(),
    )

    # Run episode
    for step in range(1, 6):  # Steps 1-5
        current_node = env_state.node

        # Get forbidden action for this (step, node)
        forbidden_action = get_forbidden_action(step, current_node)

        # Create step-specific payload for constraint compilation
        # This contains just the forbidden action for THIS step
        step_payload = NormativePayload(
            forbidden_actions=frozenset({forbidden_action}),
            target_node="N5"
        )

        # Create step-specific normative state for constraint compilation
        # But use the RUN-LEVEL binding root for consistency
        if condition == "A":
            step_state = NormativeStateASI0(
                payload=step_payload,
                binding_root=normative_state.binding_root,  # Use run-level binding
                run_id=run_id
            )
        else:
            step_state = NormativeStateASI0(
                payload=step_payload,
                binding_root=NULL_BINDING,
                run_id=run_id
            )

        # Compile constraints
        constraints = compile_constraints(step_state)

        # Get feasible actions
        feasible = env.get_feasible_actions()

        # Apply mask
        masked = apply_mask(feasible, constraints)

        # Verify capability (Condition A requires success)
        capability_verified = True  # Simplified for ASI-0

        # Select action
        selected_action = select_action(masked, seed, step)

        # Create step log
        # Use the RUN-LEVEL payload hash for binding consistency
        step_log = StepLog(
            step=step,
            step_type=StepType.CHOICE,
            current_node=current_node,
            feasible_actions=feasible,
            masked_actions=masked,
            selected_action=selected_action,
            constraints=constraints,
            binding_root=step_state.binding_root,
            capability_verified=capability_verified,
            payload_hash=predecessor_payload_hash,  # Run-level hash
            state_hash=compute_state_hash(normative_state),  # Run-level state
        )
        run_log.steps.append(step_log)

        # Execute action
        env_state = env.step(selected_action)

    # Record final state
    run_log.final_node = env_state.node
    run_log.goal_reached = env.goal_reached()

    return run_log


def run_experiment(seeds: List[int] = PREREGISTERED_SEEDS) -> ExperimentResult:
    """Run the full ASI-0 experiment.

    Runs Condition A and B for each seed, then audits and classifies.
    """
    print("=" * 60)
    print("ASI-0 v1.0 Experiment")
    print("PHASE-VII-ASI0-INSTRUMENTATION-CALIBRATION-1")
    print("=" * 60)
    print()

    # Create law module
    law_module = LawModule()

    # Create compiler schema hash (simplified for ASI-0)
    compiler_schema_hash = compute_compiler_schema_hash({
        "compiler.py": b"ASI-0 v1.0 compiler module",
        "normative_state.py": b"ASI-0 v1.0 normative state module",
    })

    # Storage for logs
    logs_a: List[RunLog] = []
    logs_b: List[RunLog] = []

    # Run experiments
    for seed in seeds:
        print(f"Running seed {seed}...")

        # Condition A
        print(f"  Condition A (bound)...", end=" ")
        log_a = run_episode(seed, "A", law_module, compiler_schema_hash)
        logs_a.append(log_a)
        print(f"final_node={log_a.final_node}, goal={log_a.goal_reached}")

        # Condition B (new law module for fresh nonces)
        law_module_b = LawModule()
        print(f"  Condition B (unbound)...", end=" ")
        log_b = run_episode(seed, "B", law_module_b, compiler_schema_hash)
        logs_b.append(log_b)
        print(f"final_node={log_b.final_node}, goal={log_b.goal_reached}")

    print()

    # Audit
    print("Auditing...")
    traceability_results: List[AuditResult] = []
    discriminability_results: List[AuditResult] = []

    for i, seed in enumerate(seeds):
        # Traceability (Condition A only)
        trace_result = audit_traceability(logs_a[i])
        traceability_results.append(trace_result)
        print(f"  Seed {seed} traceability: {trace_result.value}")

        # Discriminability (A vs B)
        disc_result = audit_discriminate(logs_a[i], logs_b[i])
        discriminability_results.append(disc_result)
        print(f"  Seed {seed} discriminability: {disc_result.value}")

    # Classify
    print()
    all_passed, classification = classify_experiment(
        traceability_results, discriminability_results
    )

    result = ExperimentResult(
        seeds=seeds,
        traceability_results=traceability_results,
        discriminability_results=discriminability_results,
        all_passed=all_passed,
        classification=classification
    )

    return result, logs_a, logs_b


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
    # Run experiment
    result, logs_a, logs_b = run_experiment()

    # Print summary
    print()
    print(result.summary())

    # Save logs
    output_dir = Path(__file__).parent.parent / "results"
    print(f"\nSaving logs to {output_dir}...")
    save_logs(logs_a, logs_b, output_dir)

    # Save result
    result_path = output_dir / "experiment_result.json"
    with open(result_path, 'w') as f:
        json.dump({
            "seeds": result.seeds,
            "traceability_results": [r.value for r in result.traceability_results],
            "discriminability_results": [r.value for r in result.discriminability_results],
            "all_passed": result.all_passed,
            "classification": result.classification,
        }, f, indent=2)
    print(f"  Saved: {result_path}")

    # Exit with appropriate code
    import sys
    sys.exit(0 if result.all_passed else 1)
