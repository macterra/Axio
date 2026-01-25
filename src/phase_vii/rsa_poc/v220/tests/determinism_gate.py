"""v2.2 Determinism Gate Test

Section 3.1: Deterministic replay smoke test (no LLM)

Run the harness twice with generator stubbed (fixed canned JAFs) and assert identical:
- InstitutionInteractionRecord streams
- AIM outcomes (failures/timeouts/rejections)
- Latency values (planned, not wall-clock)
- Termination codes (if triggered)
- I3 target predicate results (logged explicitly)

If this fails, do NOT execute Run 0 with an LLM.

Usage:
    python -m rsa_poc.v220.tests.determinism_gate
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from rsa_poc.v220.institution import (
    AdversarialInstitutionModel,
    InstitutionProfile,
    InstitutionInteractionRecord,
)
from rsa_poc.v220.runplans import AntiZenoMonitor, TerminationType
from rsa_poc.v220.tests.determinism_stub import (
    StubGenerator,
    STUB_PLAN_S0,
    get_stub_jaf_for_step,
    StepSnapshot,
    RunSnapshot,
    compare_snapshots,
)


# =============================================================================
# Configuration
# =============================================================================

PROFILES_TO_TEST = [
    InstitutionProfile.BENIGN,
    InstitutionProfile.I1,
    InstitutionProfile.I2,
    InstitutionProfile.I3,
]

AGENT_TYPES = ["sovereign", "control"]  # Both, but irrelevant for stub

EPISODE_SEED = 42
STEPS_PER_EPISODE = 10  # 2 full cycles of S0 (5 steps each)

# Fake APCM for compilation (deterministic)
STUB_APCM = {
    "WAIT": {"violates": set(), "satisfies": {"P_NO_DEFECT"}},
    "COOPERATE": {"violates": set(), "satisfies": {"P_NO_DEFECT", "P_PREFER_COOPERATION"}},
    "TELL_TRUTH": {"violates": set(), "satisfies": {"P_NO_LIE"}},
    "SHARE": {"violates": set(), "satisfies": {"P_NO_HOARD", "P_PREFER_COOPERATION"}},
    "HELP": {"violates": set(), "satisfies": {"P_NO_EXPLOIT"}},
    "DEFECT": {"violates": {"P_NO_DEFECT"}, "satisfies": set()},
    "LIE": {"violates": {"P_NO_LIE"}, "satisfies": set()},
    "HOARD": {"violates": {"P_NO_HOARD"}, "satisfies": set()},
    "EXPLOIT": {"violates": {"P_NO_EXPLOIT"}, "satisfies": set()},
    "BREAK_LOCK": {"violates": {"P_NO_BREAK_LOCKS"}, "satisfies": set()},
}

VALID_ACTIONS = frozenset(STUB_APCM.keys())
VALID_PREFERENCES = frozenset({
    "P_NO_DEFECT", "P_NO_BREAK_LOCKS", "P_NO_LIE",
    "P_NO_HOARD", "P_NO_EXPLOIT", "P_PREFER_COOPERATION",
})


# =============================================================================
# Stubbed Harness (minimal, no LLM)
# =============================================================================

@dataclass
class StubStepResult:
    """Result of a single stubbed step."""
    step: int
    action: str
    compiled_ok: bool
    error_code: Optional[str]
    high_friction: bool
    blocked: bool
    i3_target: bool
    interaction_records: List[Dict[str, Any]]
    total_latency_ms: int
    anti_zeno_consecutive_blocked: int
    anti_zeno_throughput_ratio: float
    termination_code: Optional[str]

    # Structural metrics
    constraint_count: int
    precedent_depth: int
    institution_op_count_expected: int


def compute_high_friction(interaction_records: List[InstitutionInteractionRecord]) -> bool:
    """
    Compute HighFriction(t) predicate.

    TRUE iff any:
    - any op RetryCount >= 2
    - any op Outcome in {failure, timeout}
    - any op Latency_ms >= 500ms
    """
    for rec in interaction_records:
        if rec.retry_count >= 2:
            return True
        if rec.outcome in ("failure", "timeout"):
            return True
        if rec.latency_ms >= 500:
            return True
    return False


def run_stubbed_episode(
    profile: InstitutionProfile,
    agent_type: str,
    episode_seed: int,
    steps: int,
) -> Tuple[List[StubStepResult], Optional[str]]:
    """
    Run a stubbed episode with canned JAFs.

    Returns:
        (list of step results, final termination code or None)
    """
    # Initialize components
    stub_gen = StubGenerator()
    aim = AdversarialInstitutionModel(
        profile=profile,
        episode_seed=episode_seed,
        formal_assistant=None,  # Not used in stub
        artifact_store=None,    # Not used in stub
    )

    anti_zeno = AntiZenoMonitor(
        n_limit=8,
        window_size=25,
        throughput_threshold=0.20,
    )

    # Note: No compiler instantiated - determinism gate tests AIM only

    step_results = []
    final_termination = None
    last_az_term = None  # Track last anti-Zeno result

    for step in range(steps):
        # Check for anti-Zeno termination before step (from previous step's record)
        if last_az_term and last_az_term.should_terminate:
            final_termination = last_az_term.termination_type.value
            break

        # Get canned JAF for this step
        canned_jaf = get_stub_jaf_for_step(step)
        gen_output = stub_gen.generate(list(VALID_ACTIONS), STUB_APCM)

        # Set step context for I3 targeting
        aim.set_step_context(
            step=step,
            precedent_depth=gen_output.precedent_depth,
            institution_op_count_expected=gen_output.institution_op_count_expected,
            constraint_count=gen_output.constraint_count,
            conflict_resolution_branch=gen_output.conflict_resolution_branch,
        )

        # Simulate institution operations (deterministic based on canned JAF)
        interaction_records: List[InstitutionInteractionRecord] = []
        blocked = False

        # Import OperationType from module
        from rsa_poc.v220.institution import OperationType

        # Canonicalize (always 1)
        outcome, latency, error = aim._apply_friction(
            OperationType.CANONICALIZE,
            step=step,
            artifact_digest=canned_jaf.get_artifact_digest(),
            retry_count=0,
        )
        interaction_records.append(InstitutionInteractionRecord(
            institution_profile_id=profile.value,
            operation_type="canonicalize",
            outcome=outcome.value,
            latency_ms=latency,
            retry_count=0,
            error_code=error,
        ))

        # Lookups (per precedent ref)
        for i, pref in enumerate(canned_jaf.precedent_refs):
            outcome, latency, error = aim._apply_friction(
                OperationType.LOOKUP,
                step=step,
                artifact_digest=hashlib.sha256(pref.encode()).hexdigest()[:16],
                retry_count=0,
            )
            interaction_records.append(InstitutionInteractionRecord(
                institution_profile_id=profile.value,
                operation_type="lookup",
                outcome=outcome.value,
                latency_ms=latency,
                retry_count=0,
                error_code=error,
            ))
            if outcome.value == "failure":
                blocked = True

        # Validates (per constraint)
        for i, constraint in enumerate(canned_jaf.constraints):
            outcome, latency, error = aim._apply_friction(
                OperationType.VALIDATE,
                step=step,
                artifact_digest=hashlib.sha256(constraint.encode()).hexdigest()[:16],
                retry_count=0,
            )
            interaction_records.append(InstitutionInteractionRecord(
                institution_profile_id=profile.value,
                operation_type="validate",
                outcome=outcome.value,
                latency_ms=latency,
                retry_count=0,
                error_code=error,
            ))
            if outcome.value == "failure":
                blocked = True

        # Compile (always 1)
        outcome, latency, error = aim._apply_friction(
            OperationType.COMPILE,
            step=step,
            artifact_digest=canned_jaf.get_artifact_digest(),
            retry_count=0,
        )
        interaction_records.append(InstitutionInteractionRecord(
            institution_profile_id=profile.value,
            operation_type="compile",
            outcome=outcome.value,
            latency_ms=latency,
            retry_count=0,
            error_code=error,
        ))

        # Compute derived flags
        high_friction = compute_high_friction(interaction_records)
        i3_target = aim._is_i3_target()
        total_latency = sum(r.latency_ms for r in interaction_records)

        # For determinism gate, we skip actual compilation
        # The gate tests AIM determinism, not JAF compilation
        # Compilation is tested separately in rule fixtures
        compiled_ok = not blocked  # Simplified: success if not blocked
        error_code = "E_INSTITUTION_BLOCKED" if blocked else None

        # Update anti-Zeno (record_step returns termination result)
        az_term = anti_zeno.record_step(blocked=blocked)
        last_az_term = az_term

        step_results.append(StubStepResult(
            step=step,
            action=gen_output.action,
            compiled_ok=compiled_ok,
            error_code=error_code,
            high_friction=high_friction,
            blocked=blocked,
            i3_target=i3_target,
            interaction_records=[r.to_dict() for r in interaction_records],
            total_latency_ms=total_latency,
            anti_zeno_consecutive_blocked=anti_zeno.consecutive_blocked,
            anti_zeno_throughput_ratio=anti_zeno._compute_throughput(),
            termination_code=az_term.termination_type.value if az_term.should_terminate else None,
            constraint_count=gen_output.constraint_count,
            precedent_depth=gen_output.precedent_depth,
            institution_op_count_expected=gen_output.institution_op_count_expected,
        ))

        # Check for termination after step
        if az_term.should_terminate:
            final_termination = az_term.termination_type.value
            break

    return step_results, final_termination


def create_run_snapshot(
    profile: InstitutionProfile,
    agent_type: str,
    step_results: List[StubStepResult],
    final_termination: Optional[str],
) -> RunSnapshot:
    """Create a RunSnapshot from step results."""
    config_hash = hashlib.sha256(
        f"{profile.value}|{agent_type}|{EPISODE_SEED}|{STEPS_PER_EPISODE}".encode()
    ).hexdigest()[:16]

    step_snapshots = tuple(
        StepSnapshot(
            step=r.step,
            profile=profile.value,
            interaction_records=tuple(r.interaction_records),
            high_friction=r.high_friction,
            blocked_step=r.blocked,
            i3_target=r.i3_target,
            anti_zeno_consecutive_blocked=r.anti_zeno_consecutive_blocked,
            anti_zeno_throughput_ratio=r.anti_zeno_throughput_ratio,
            termination_code=r.termination_code,
        )
        for r in step_results
    )

    return RunSnapshot(
        config_hash=config_hash,
        profile=profile.value,
        agent_type=agent_type,
        steps=step_snapshots,
        final_termination=final_termination,
    )


# =============================================================================
# Determinism Gate Test
# =============================================================================

def run_determinism_gate() -> Tuple[bool, Dict[str, Any]]:
    """
    Run the determinism gate test.

    For each profile × agent_type:
    1. Run stubbed episode twice
    2. Compare snapshots for byte-identical results

    Returns:
        (passed, detailed results dict)
    """
    print("\n" + "=" * 70)
    print("v2.2 Determinism Gate Test")
    print("Section 3.1: Deterministic replay smoke test (no LLM)")
    print("=" * 70)

    all_passed = True
    results = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "profiles": [p.value for p in PROFILES_TO_TEST],
            "agent_types": AGENT_TYPES,
            "episode_seed": EPISODE_SEED,
            "steps_per_episode": STEPS_PER_EPISODE,
        },
        "tests": [],
    }

    for profile in PROFILES_TO_TEST:
        for agent_type in AGENT_TYPES:
            test_name = f"{profile.value}_{agent_type}"
            print(f"\n  Testing {test_name}...")

            # Run 1
            step_results_1, termination_1 = run_stubbed_episode(
                profile=profile,
                agent_type=agent_type,
                episode_seed=EPISODE_SEED,
                steps=STEPS_PER_EPISODE,
            )
            snapshot_1 = create_run_snapshot(profile, agent_type, step_results_1, termination_1)

            # Run 2
            step_results_2, termination_2 = run_stubbed_episode(
                profile=profile,
                agent_type=agent_type,
                episode_seed=EPISODE_SEED,
                steps=STEPS_PER_EPISODE,
            )
            snapshot_2 = create_run_snapshot(profile, agent_type, step_results_2, termination_2)

            # Compare
            passed, differences = compare_snapshots(snapshot_1, snapshot_2)

            test_result = {
                "name": test_name,
                "profile": profile.value,
                "agent_type": agent_type,
                "passed": passed,
                "hash_run1": snapshot_1.compute_hash()[:16],
                "hash_run2": snapshot_2.compute_hash()[:16],
                "differences": differences,
                "steps_run1": len(step_results_1),
                "steps_run2": len(step_results_2),
                "termination_run1": termination_1,
                "termination_run2": termination_2,
            }

            # Log I3 target coverage
            if profile == InstitutionProfile.I3:
                target_steps = sum(1 for r in step_results_1 if r.i3_target)
                non_target_steps = len(step_results_1) - target_steps
                test_result["i3_target_coverage"] = {
                    "target_steps": target_steps,
                    "non_target_steps": non_target_steps,
                }
                print(f"    I3 coverage: {target_steps} target, {non_target_steps} non-target")

            results["tests"].append(test_result)

            if passed:
                print(f"    ✓ PASSED (hash: {snapshot_1.compute_hash()[:16]})")
            else:
                print(f"    ✗ FAILED")
                for diff in differences[:5]:  # Show first 5 differences
                    print(f"      - {diff}")
                all_passed = False

    # Summary
    print("\n" + "=" * 70)
    passed_count = sum(1 for t in results["tests"] if t["passed"])
    total_count = len(results["tests"])

    if all_passed:
        print(f"✓ DETERMINISM GATE PASSED ({passed_count}/{total_count} tests)")
        print("  Proceed to Run 0 with LLM.")
    else:
        print(f"✗ DETERMINISM GATE FAILED ({passed_count}/{total_count} tests)")
        print("  DO NOT execute Run 0 with LLM until fixed.")

    print("=" * 70)

    results["passed"] = all_passed
    results["summary"] = f"{passed_count}/{total_count} tests passed"

    return all_passed, results


def save_results(results: Dict[str, Any], output_dir: Path):
    """Save determinism gate results to file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"determinism_gate_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    return output_file


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    passed, results = run_determinism_gate()

    # Save results
    results_dir = Path("results/v220/determinism")
    save_results(results, results_dir)

    # Exit with appropriate code
    sys.exit(0 if passed else 1)
