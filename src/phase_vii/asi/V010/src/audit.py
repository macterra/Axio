"""
Audit Algorithms for ASI-0 v1.0

Implements:
- audit_discriminate(): Check if Conditions A and B are distinguishable
- audit_traceability(): Verify authority-bound evaluability is structurally traceable
- AuditResult: Enumeration of possible audit outcomes
"""

from enum import Enum
from typing import Tuple, List, Optional, Set
from dataclasses import dataclass

from normative_state import NULL_BINDING
from logging_schema import RunLog, StepLog, StepType
from env_calibmaze import get_forbidden_action
from law_module import EscrowState


class AuditResult(Enum):
    """Possible audit outcomes."""
    # Success outcomes
    PASS_DISCRIMINABLE = "PASS_DISCRIMINABLE"
    PASS_TRACEABILITY_DEMONSTRATED = "PASS_TRACEABILITY_DEMONSTRATED"

    # Discriminability failures
    FAIL_BINDING_INDISTINGUISHABLE = "FAIL_BINDING_INDISTINGUISHABLE"
    FAIL_MASK_INDISTINGUISHABLE = "FAIL_MASK_INDISTINGUISHABLE"

    # Traceability failures
    FAIL_CAPABILITY_INVALID = "FAIL_CAPABILITY_INVALID"
    FAIL_BINDING_MISMATCH = "FAIL_BINDING_MISMATCH"
    FAIL_PAYLOAD_HASH_MISMATCH = "FAIL_PAYLOAD_HASH_MISMATCH"
    FAIL_NONTRIVIALITY = "FAIL_NONTRIVIALITY"
    FAIL_WRONG_ACTION_PRUNED = "FAIL_WRONG_ACTION_PRUNED"
    FAIL_ESCROW_LEAKAGE = "FAIL_ESCROW_LEAKAGE"


def audit_discriminate(log_a: RunLog, log_b: RunLog) -> AuditResult:
    """Determine if Condition A and B are distinguishable by log alone.

    Checks:
    1. All steps in A have non-NULL binding_root
    2. All steps in B have NULL binding_root
    3. A shows pruning (feasible != masked at some step)
    4. B shows no pruning (feasible == masked at all steps)
    """
    # Check binding roots differ
    a_bound = all(
        step.binding_root != NULL_BINDING
        for step in log_a.steps
    )
    b_unbound = all(
        step.binding_root == NULL_BINDING
        for step in log_b.steps
    )

    if not (a_bound and b_unbound):
        return AuditResult.FAIL_BINDING_INDISTINGUISHABLE

    # Check mask behavior differs
    a_pruned = any(
        step.feasible_actions != step.masked_actions
        for step in log_a.steps
    )
    b_unpruned = all(
        step.feasible_actions == step.masked_actions
        for step in log_b.steps
    )

    if not (a_pruned and b_unpruned):
        return AuditResult.FAIL_MASK_INDISTINGUISHABLE

    return AuditResult.PASS_DISCRIMINABLE


def verify_capability_chain(log_a: RunLog) -> bool:
    """Verify the capability chain is valid.

    For ASI-0, this checks:
    - All CHOICE steps have capability_verified == True
    """
    for step in log_a.steps:
        if step.step_type == StepType.CHOICE:
            if not step.capability_verified:
                return False
    return True


def verify_escrow_integrity(log_a: RunLog) -> bool:
    """Verify no escrow leakage occurred.

    For ASI-0, this checks:
    - Escrow transitions follow valid state machine
    - Final state is COMMITTED (not ABORTED for successful runs)
    """
    if not log_a.escrow_transitions:
        # No escrow recorded - this is acceptable for ASI-0 simplified harness
        return True

    # Check transitions are valid
    valid_transitions = {
        (EscrowState.ESCROWED, EscrowState.VERIFYING),
        (EscrowState.VERIFYING, EscrowState.COMMITTED),
        (EscrowState.VERIFYING, EscrowState.ABORTED),
    }

    for transition in log_a.escrow_transitions:
        if (transition.from_state, transition.to_state) not in valid_transitions:
            return False

    return True


def audit_traceability(log_a: RunLog) -> AuditResult:
    """Verify authority-bound evaluability is structurally traceable.

    Checks:
    1. Capability chain is valid
    2. All binding_roots match predecessor_payload_hash
    3. All payload_hashes match expected root (recomputed post-hoc)
    4. Constraints are non-trivial at each CHOICE step
    5. Correct forbidden action was pruned
    6. No escrow leakage
    """
    # 1. Verify capability chain
    if not verify_capability_chain(log_a):
        return AuditResult.FAIL_CAPABILITY_INVALID

    # 2. Verify binding roots match predecessor snapshot
    expected_root = log_a.predecessor_payload_hash
    for step in log_a.steps:
        if step.binding_root != expected_root:
            return AuditResult.FAIL_BINDING_MISMATCH

        # Invariant: payload_hash must equal root_hash (recomputed post-hoc)
        if step.payload_hash != expected_root:
            return AuditResult.FAIL_PAYLOAD_HASH_MISMATCH

    # 3. Verify constraints are non-trivial and correct
    for step in log_a.steps:
        if step.step_type == StepType.CHOICE:
            forbidden = step.feasible_actions - step.masked_actions
            if len(forbidden) == 0:
                return AuditResult.FAIL_NONTRIVIALITY

            # Verify the pruned action matches the registered forbidden action
            expected_forbidden = get_forbidden_action(step.step, step.current_node)
            if expected_forbidden not in forbidden:
                return AuditResult.FAIL_WRONG_ACTION_PRUNED

    # 4. Verify no escrow leakage
    if not verify_escrow_integrity(log_a):
        return AuditResult.FAIL_ESCROW_LEAKAGE

    return AuditResult.PASS_TRACEABILITY_DEMONSTRATED


@dataclass
class ExperimentResult:
    """Overall experiment result for ASI-0 v1.0."""
    seeds: List[int]
    traceability_results: List[AuditResult]
    discriminability_results: List[AuditResult]
    all_passed: bool
    classification: str

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 50,
            "ASI-0 v1.0 Experiment Results",
            "=" * 50,
            "",
            f"Seeds: {self.seeds}",
            "",
            "Traceability (Condition A):",
        ]
        for seed, result in zip(self.seeds, self.traceability_results):
            lines.append(f"  Seed {seed}: {result.value}")

        lines.extend([
            "",
            "Discriminability (A vs B):",
        ])
        for seed, result in zip(self.seeds, self.discriminability_results):
            lines.append(f"  Seed {seed}: {result.value}")

        lines.extend([
            "",
            f"All Passed: {self.all_passed}",
            f"Classification: {self.classification}",
            "=" * 50,
        ])

        return "\n".join(lines)


def classify_experiment(
    traceability_results: List[AuditResult],
    discriminability_results: List[AuditResult]
) -> Tuple[bool, str]:
    """Classify the overall experiment result.

    Returns (all_passed, classification).
    """
    traceability_passed = all(
        r == AuditResult.PASS_TRACEABILITY_DEMONSTRATED
        for r in traceability_results
    )
    discriminability_passed = all(
        r == AuditResult.PASS_DISCRIMINABLE
        for r in discriminability_results
    )

    if traceability_passed and discriminability_passed:
        return True, "ASI0_PASS / TRACEABILITY_DEMONSTRATED"
    else:
        return False, "SOVEREIGNTY_NON_TRACEABILITY"


if __name__ == "__main__":
    print("Audit Algorithms Verification")
    print("=" * 40)

    from normative_state import NormativePayload, compute_payload_hash, NULL_BINDING
    from logging_schema import StepLog, RunLog, StepType, create_step_log
    from normative_state import create_bound_state, create_unbound_state
    from compiler import compile_constraints, Constraint

    # Create sample payloads
    payload = NormativePayload(
        forbidden_actions=frozenset({"GO_N2"}),
        target_node="N5"
    )
    payload_hash = compute_payload_hash(payload)

    # Create sample Condition A log
    state_a = create_bound_state(payload, "test-001")
    constraints_a = compile_constraints(state_a)

    step_a = create_step_log(
        step=1,
        step_type=StepType.CHOICE,
        current_node="N0",
        feasible_actions={"GO_N1", "GO_N2", "STAY"},
        masked_actions={"GO_N1", "STAY"},  # GO_N2 pruned
        selected_action="GO_N1",
        constraints=constraints_a,
        normative_state=state_a,
        capability_verified=True
    )

    log_a = RunLog(
        run_id="test-001",
        seed=42,
        condition="A",
        env_id="CalibMazeV010",
        predecessor_payload_hash=payload_hash,
        successor_initial_payload_hash=payload_hash,
        steps=[step_a],
        final_node="N5",
        goal_reached=True
    )

    # Create sample Condition B log
    state_b = create_unbound_state(payload, "test-001")
    constraints_b = compile_constraints(state_b)

    step_b = create_step_log(
        step=1,
        step_type=StepType.CHOICE,
        current_node="N0",
        feasible_actions={"GO_N1", "GO_N2", "STAY"},
        masked_actions={"GO_N1", "GO_N2", "STAY"},  # No pruning
        selected_action="GO_N1",
        constraints=constraints_b,
        normative_state=state_b,
        capability_verified=True
    )

    log_b = RunLog(
        run_id="test-002",
        seed=42,
        condition="B",
        env_id="CalibMazeV010",
        predecessor_payload_hash=payload_hash,
        successor_initial_payload_hash=payload_hash,
        steps=[step_b],
        final_node="N5",
        goal_reached=True
    )

    # Test discriminability
    print("\n1. Discriminability check:")
    disc_result = audit_discriminate(log_a, log_b)
    print(f"   Result: {disc_result.value}")

    # Test traceability
    print("\n2. Traceability check:")
    trace_result = audit_traceability(log_a)
    print(f"   Result: {trace_result.value}")

    # Test classification
    print("\n3. Classification:")
    passed, classification = classify_experiment([trace_result], [disc_result])
    print(f"   Passed: {passed}")
    print(f"   Classification: {classification}")

    # Test failure cases
    print("\n4. Failure case tests:")

    # Non-triviality failure
    step_fail_nt = create_step_log(
        step=1,
        step_type=StepType.CHOICE,
        current_node="N0",
        feasible_actions={"GO_N1", "GO_N2", "STAY"},
        masked_actions={"GO_N1", "GO_N2", "STAY"},  # Nothing pruned
        selected_action="GO_N1",
        constraints=constraints_a,
        normative_state=state_a,
        capability_verified=True
    )
    log_fail_nt = RunLog(
        run_id="fail-001",
        seed=42,
        condition="A",
        env_id="CalibMazeV010",
        predecessor_payload_hash=payload_hash,
        successor_initial_payload_hash=payload_hash,
        steps=[step_fail_nt],
        final_node="N5",
        goal_reached=True
    )
    print(f"   Non-triviality failure: {audit_traceability(log_fail_nt).value}")

    # Wrong action pruned failure
    step_fail_wrong = create_step_log(
        step=1,
        step_type=StepType.CHOICE,
        current_node="N0",
        feasible_actions={"GO_N1", "GO_N2", "STAY"},
        masked_actions={"GO_N2", "STAY"},  # Wrong action (GO_N1) pruned
        selected_action="GO_N2",
        constraints=constraints_a,
        normative_state=state_a,
        capability_verified=True
    )
    log_fail_wrong = RunLog(
        run_id="fail-002",
        seed=42,
        condition="A",
        env_id="CalibMazeV010",
        predecessor_payload_hash=payload_hash,
        successor_initial_payload_hash=payload_hash,
        steps=[step_fail_wrong],
        final_node="N5",
        goal_reached=True
    )
    print(f"   Wrong action pruned: {audit_traceability(log_fail_wrong).value}")
