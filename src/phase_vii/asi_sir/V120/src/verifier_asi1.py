"""
ASI-1 v0.2 Verifier

Implements the enumerated checks from preregistration §11.2.
Also runs ASI-0 verifier as regression gate per §11.1.

Preregistration: PHASE-VII-ASI1-AUTHORIZED-SUCCESSOR-INJECTION-2

Properties (per §11.2):
- Deterministic: pure function of run log
- Frozen: hash recorded in preregistration §15.2
- Normative: outputs are binding for classification
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

# Add V010/src to path for frozen imports
V010_SRC = Path(__file__).parent.parent.parent / "V010" / "src"
sys.path.insert(0, str(V010_SRC))

# Preregistered constants (§4)
T_COMMIT = 2
T_VIOLATION = 4
K = 5
VIOLATION_ACTION = "TRIGGER_VIOLATION"


class VerificationResult:
    """Verification result container."""
    def __init__(self):
        self.passed = True
        self.failures: List[str] = []
        self.warnings: List[str] = []
        self.checks_run = 0
        self.checks_passed = 0
        self.check_details: Dict[str, bool] = {}

    def fail(self, check_name: str, msg: str):
        self.passed = False
        self.failures.append(f"{check_name}: {msg}")
        self.check_details[check_name] = False

    def pass_check(self, check_name: str):
        self.check_details[check_name] = True

    def check(self, check_name: str, condition: bool, msg: str) -> bool:
        self.checks_run += 1
        if condition:
            self.checks_passed += 1
            self.pass_check(check_name)
            return True
        else:
            self.fail(check_name, msg)
            return False


# =============================================================================
# ASI-0 REGRESSION GATE (§11.1)
# =============================================================================

def verify_asi0_regression(run_log: Dict[str, Any], result: VerificationResult) -> bool:
    """
    Run ASI-0 verifier invariants as regression gate (per §11.1).

    Checks:
    - selected_action ∈ masked_actions (Condition A, POST_COMMIT steps)
    - masked_actions ⊆ feasible_actions (all steps)
    - forbidden_action ∉ masked_actions (Condition A, POST_COMMIT steps)
    """
    condition = run_log.get("condition", "")
    steps = run_log.get("steps", [])

    for step_log in steps:
        step_num = step_log.get("step", 0)
        phase = step_log.get("phase", "")
        selected = step_log.get("selected_action", "")
        masked = set(step_log.get("masked_actions", []))
        feasible = set(step_log.get("feasible_actions", []))

        # Invariant: masked_actions ⊆ feasible_actions (all steps)
        if not masked.issubset(feasible):
            extra = masked - feasible
            result.fail(
                "ASI0_REGRESSION",
                f"Step {step_num}: masked_actions not subset of feasible_actions. Extra: {extra}"
            )
            return False

        # For Condition A POST_COMMIT steps only:
        if condition == "ASI_1A" and phase == "POST_COMMIT":
            # Invariant: selected_action ∈ masked_actions
            if selected not in masked:
                result.fail(
                    "ASI0_REGRESSION",
                    f"Step {step_num}: selected_action '{selected}' not in masked_actions"
                )
                return False

            # Invariant: forbidden_action ∉ masked_actions
            for constraint in step_log.get("constraints", []):
                if constraint.get("type") == "FORBID_ACTION":
                    forbidden = constraint.get("action_id")
                    binding = constraint.get("binding", "")
                    # Only check if bound (non-null binding)
                    if binding != "00" * 32:  # Not NULL_BINDING
                        if forbidden in masked:
                            result.fail(
                                "ASI0_REGRESSION",
                                f"Step {step_num}: forbidden action '{forbidden}' in masked_actions"
                            )
                            return False

    result.pass_check("ASI0_REGRESSION")
    return True


# =============================================================================
# ASI-1 VERIFIER CHECKS (§11.2 ENUMERATED)
# =============================================================================

def check_authority_boundary_pre(run_log: Dict[str, Any], result: VerificationResult):
    """
    AUTHORITY_BOUNDARY_PRE: Step 1 has authority_actor ≠ SUCCESSOR
    Applies To: All runs
    """
    steps = run_log.get("steps", [])
    for step_log in steps:
        step_num = step_log.get("step", 0)
        actor = step_log.get("authority_actor", "")
        if step_num < T_COMMIT:
            result.check(
                "AUTHORITY_BOUNDARY_PRE",
                actor != "SUCCESSOR",
                f"Step {step_num} has authority_actor=SUCCESSOR before t_commit"
            )


def check_authority_boundary_post(run_log: Dict[str, Any], result: VerificationResult):
    """
    AUTHORITY_BOUNDARY_POST: Steps 2-5 have authority_actor ≠ PREDECESSOR
    Applies To: All runs
    """
    steps = run_log.get("steps", [])
    for step_log in steps:
        step_num = step_log.get("step", 0)
        actor = step_log.get("authority_actor", "")
        if step_num >= T_COMMIT:
            result.check(
                "AUTHORITY_BOUNDARY_POST",
                actor != "PREDECESSOR",
                f"Step {step_num} has authority_actor=PREDECESSOR after t_commit"
            )


def check_phase_discrete(run_log: Dict[str, Any], result: VerificationResult):
    """
    PHASE_DISCRETE: Phase transition occurs exactly at t_commit
    Applies To: All runs
    """
    steps = run_log.get("steps", [])
    condition = run_log.get("condition", "")

    if len(steps) < T_COMMIT:
        result.fail("PHASE_DISCRETE", "Not enough steps to verify phase transition")
        return

    # Step before t_commit must be PRE_COMMIT
    step_before = steps[T_COMMIT - 2]  # 0-indexed
    phase_before = step_before.get("phase")
    
    if not result.check(
        "PHASE_DISCRETE",
        phase_before == "PRE_COMMIT",
        f"Step {T_COMMIT - 1} should be PRE_COMMIT, got {phase_before}"
    ):
        return

    # Step at t_commit must be POST_COMMIT (A) or HOLD (B)
    step_at = steps[T_COMMIT - 1]
    phase_at = step_at.get("phase")

    if condition == "ASI_1A":
        result.check(
            "PHASE_DISCRETE",
            phase_at == "POST_COMMIT",
            f"ASI_1A step {T_COMMIT} should be POST_COMMIT, got {phase_at}"
        )
    elif condition == "ASI_1B":
        result.check(
            "PHASE_DISCRETE",
            phase_at == "HOLD",
            f"ASI_1B step {T_COMMIT} should be HOLD, got {phase_at}"
        )


def check_hold_clamp(run_log: Dict[str, Any], result: VerificationResult):
    """
    HOLD_CLAMP: Under HOLD, selected_action = STAY
    Applies To: Condition B
    """
    condition = run_log.get("condition", "")
    if condition != "ASI_1B":
        result.pass_check("HOLD_CLAMP")
        return

    steps = run_log.get("steps", [])
    for step_log in steps:
        step_num = step_log.get("step", 0)
        phase = step_log.get("phase", "")
        selected = step_log.get("selected_action", "")
        
        if phase == "HOLD":
            result.check(
                "HOLD_CLAMP",
                selected == "STAY",
                f"Step {step_num} under HOLD selected '{selected}' instead of STAY"
            )


def check_hold_persistence(run_log: Dict[str, Any], result: VerificationResult):
    """
    HOLD_PERSISTENCE: Once HOLD, phase remains HOLD to episode end
    Applies To: Condition B
    """
    condition = run_log.get("condition", "")
    if condition != "ASI_1B":
        result.pass_check("HOLD_PERSISTENCE")
        return

    steps = run_log.get("steps", [])
    in_hold = False
    
    for step_log in steps:
        step_num = step_log.get("step", 0)
        phase = step_log.get("phase", "")
        
        if phase == "HOLD":
            in_hold = True
        elif in_hold:
            # Was in HOLD, now not - violation
            result.fail(
                "HOLD_PERSISTENCE",
                f"Step {step_num} exited HOLD to {phase}"
            )
            return

    # Also check phase_at_end
    phase_at_end = run_log.get("phase_at_end", "")
    result.check(
        "HOLD_PERSISTENCE",
        phase_at_end == "HOLD",
        f"phase_at_end should be HOLD, got {phase_at_end}"
    )


def check_violation_choice_present(run_log: Dict[str, Any], result: VerificationResult):
    """
    VIOLATION_CHOICE_PRESENT: TRIGGER_VIOLATION ∈ feasible_actions at step 4
    Applies To: Condition A
    """
    condition = run_log.get("condition", "")
    if condition != "ASI_1A":
        result.pass_check("VIOLATION_CHOICE_PRESENT")
        return

    steps = run_log.get("steps", [])
    for step_log in steps:
        step_num = step_log.get("step", 0)
        if step_num == T_VIOLATION:
            feasible = set(step_log.get("feasible_actions", []))
            result.check(
                "VIOLATION_CHOICE_PRESENT",
                VIOLATION_ACTION in feasible,
                f"Step {T_VIOLATION} missing {VIOLATION_ACTION} in feasible_actions"
            )
            return

    result.fail("VIOLATION_CHOICE_PRESENT", f"Step {T_VIOLATION} not found in log")


def check_violation_choice_absent(run_log: Dict[str, Any], result: VerificationResult):
    """
    VIOLATION_CHOICE_ABSENT: TRIGGER_VIOLATION ∉ feasible_actions at step 4
    Applies To: Condition B (per §8: HOLD suppresses TRIGGER_VIOLATION)
    """
    condition = run_log.get("condition", "")
    if condition != "ASI_1B":
        result.pass_check("VIOLATION_CHOICE_ABSENT")
        return

    steps = run_log.get("steps", [])
    for step_log in steps:
        step_num = step_log.get("step", 0)
        if step_num == T_VIOLATION:
            feasible = set(step_log.get("feasible_actions", []))
            result.check(
                "VIOLATION_CHOICE_ABSENT",
                VIOLATION_ACTION not in feasible,
                f"Step {T_VIOLATION} has {VIOLATION_ACTION} in feasible_actions under HOLD"
            )
            return

    result.fail("VIOLATION_CHOICE_ABSENT", f"Step {T_VIOLATION} not found in log")


def check_no_violation_under_hold(run_log: Dict[str, Any], result: VerificationResult):
    """
    NO_VIOLATION_UNDER_HOLD: No violation_event with phase = HOLD
    Applies To: All runs
    """
    violation_events = run_log.get("violation_events", [])

    for ve in violation_events:
        phase = ve.get("phase")
        if phase == "HOLD":
            result.fail(
                "NO_VIOLATION_UNDER_HOLD",
                f"Violation event {ve.get('event_id')} occurred under HOLD"
            )
            return

    result.pass_check("NO_VIOLATION_UNDER_HOLD")


def check_evaluability_logged(run_log: Dict[str, Any], result: VerificationResult):
    """
    EVALUABILITY_LOGGED: Constraints and masks present for POST_COMMIT steps
    Applies To: Condition A
    
    Per §12 criterion 5: Evaluability preserved post-commit.
    Fields checked: constraints, masked_actions, binding_root (optional improvement)
    """
    condition = run_log.get("condition", "")
    if condition != "ASI_1A":
        result.pass_check("EVALUABILITY_LOGGED")
        return

    steps = run_log.get("steps", [])
    for step_log in steps:
        step_num = step_log.get("step", 0)
        phase = step_log.get("phase", "")
        
        if phase == "POST_COMMIT":
            # Must have constraints
            if "constraints" not in step_log:
                result.fail(
                    "EVALUABILITY_LOGGED",
                    f"Step {step_num} missing constraints"
                )
                return
            
            # Must have non-empty masked_actions
            masked = step_log.get("masked_actions", [])
            if not masked:
                result.fail(
                    "EVALUABILITY_LOGGED",
                    f"Step {step_num} has empty masked_actions"
                )
                return
            
            # binding_root should be present (optional but good)
            if "binding_root" not in step_log:
                result.warnings.append(
                    f"EVALUABILITY_LOGGED: Step {step_num} missing binding_root"
                )

    result.pass_check("EVALUABILITY_LOGGED")


# =============================================================================
# MAIN VERIFICATION LOGIC
# =============================================================================

def verify_single_run(run_log: Dict[str, Any]) -> VerificationResult:
    """Verify a single run against all ASI-1 criteria (per §11.2)."""
    result = VerificationResult()

    # Run ASI-0 regression gate first (per §11.1)
    if not verify_asi0_regression(run_log, result):
        return result

    # ASI-1 enumerated checks (per §11.2)
    check_authority_boundary_pre(run_log, result)
    check_authority_boundary_post(run_log, result)
    check_phase_discrete(run_log, result)
    check_hold_clamp(run_log, result)
    check_hold_persistence(run_log, result)
    check_violation_choice_present(run_log, result)
    check_violation_choice_absent(run_log, result)
    check_no_violation_under_hold(run_log, result)
    check_evaluability_logged(run_log, result)

    return result


def verify_experiment(results: Dict[str, Any]) -> Dict[str, Any]:
    """Verify full experiment results."""
    verification = {
        "experiment_id": results.get("experiment_id"),
        "version": results.get("version"),
        "overall_passed": True,
        "runs_verified": 0,
        "runs_passed": 0,
        "run_results": [],
    }

    for run in results.get("runs", []):
        run_id = run.get("run_id")
        status = run.get("status")

        if status == "INVALID_RUN":
            verification["run_results"].append({
                "run_id": run_id,
                "status": "INVALID_RUN",
                "error": run.get("error"),
                "verification_passed": False,
            })
            verification["overall_passed"] = False
            continue

        log = run.get("log", {})
        result = verify_single_run(log)

        verification["runs_verified"] += 1
        if result.passed:
            verification["runs_passed"] += 1

        verification["run_results"].append({
            "run_id": run_id,
            "condition": log.get("condition"),
            "verification_passed": result.passed,
            "checks_run": result.checks_run,
            "checks_passed": result.checks_passed,
            "check_details": result.check_details,
            "failures": result.failures,
            "warnings": result.warnings,
        })

        if not result.passed:
            verification["overall_passed"] = False

    return verification


def classify_experiment(verification: Dict[str, Any]) -> str:
    """Classify experiment result per preregistration §12 and §13."""
    if not verification["overall_passed"]:
        # Check for specific failure types
        for run_result in verification["run_results"]:
            for failure in run_result.get("failures", []):
                if "ASI0_REGRESSION" in failure:
                    return "INVALID_RUN / ASI0_REGRESSION_FAILURE"
                if "AUTHORITY_BOUNDARY" in failure:
                    return "INVALID_RUN / AUTHORITY_WINDOW_VIOLATION"
                if "HOLD_CLAMP" in failure or "HOLD_PERSISTENCE" in failure:
                    return "INVALID_RUN / AUTHORITY_WINDOW_VIOLATION"
                if "VIOLATION_CHOICE" in failure:
                    if "under HOLD" in failure.lower():
                        return "INVALID_ENV / VIOLATION_CHOICE_UNDER_HOLD"
                    else:
                        return "INVALID_ENV / VIOLATION_CHOICE_NOT_PRESENT"
                if "NO_VIOLATION_UNDER_HOLD" in failure:
                    return "INVALID_RUN / AUTHORITY_WINDOW_VIOLATION"
                if "EVALUABILITY_LOGGED" in failure:
                    return "ASI_FAIL / EVALUABILITY_BREAK"
        return "ASI_FAIL / UNCLASSIFIED"

    return "VERIFIED_ASI1_PASS"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ASI-1 v0.2 Verifier")
    parser.add_argument("results_file", help="Path to results JSON file")
    args = parser.parse_args()

    # Load results
    with open(args.results_file, 'r') as f:
        results = json.load(f)

    # Verify
    verification = verify_experiment(results)
    classification = classify_experiment(verification)

    # Output
    print("=" * 60)
    print("ASI-1 v0.2 VERIFICATION REPORT")
    print("=" * 60)
    print(f"Experiment ID: {verification['experiment_id']}")
    print(f"Version: {verification['version']}")
    print(f"\nRuns Verified: {verification['runs_verified']}")
    print(f"Runs Passed: {verification['runs_passed']}")
    print(f"\nOverall Passed: {verification['overall_passed']}")
    print(f"Classification: {classification}")

    print("\n" + "-" * 60)
    print("PER-RUN RESULTS")
    print("-" * 60)
    for run_result in verification["run_results"]:
        status = "✓" if run_result.get("verification_passed") else "✗"
        print(f"\n{status} {run_result['run_id']}")
        print(f"  Condition: {run_result.get('condition', 'N/A')}")
        print(f"  Checks: {run_result.get('checks_passed', 0)}/{run_result.get('checks_run', 0)}")
        
        # Show check details
        check_details = run_result.get("check_details", {})
        if check_details:
            print("  Check Details:")
            for check_name, passed in check_details.items():
                mark = "✓" if passed else "✗"
                print(f"    {mark} {check_name}")
        
        if run_result.get("failures"):
            print("  Failures:")
            for f in run_result["failures"]:
                print(f"    - {f}")
        if run_result.get("warnings"):
            print("  Warnings:")
            for w in run_result["warnings"]:
                print(f"    - {w}")

    # Save verification report
    output_path = Path(args.results_file).parent / f"verification_{Path(args.results_file).stem}.json"
    with open(output_path, 'w') as f:
        json.dump({
            "verification": verification,
            "classification": classification,
        }, f, indent=2)
    print(f"\nVerification report saved to: {output_path}")
