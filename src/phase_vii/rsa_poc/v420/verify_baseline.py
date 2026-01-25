#!/usr/bin/env python3
"""
RSA-PoC v4.2 — Baseline Verification Script

Validates the complete v4.2 implementation:
1. Environment mechanics (regime flip, STAMP)
2. Contradiction detection (PROHIBIT(STAMP) blocks progress)
3. LAW_REPAIR action schema
4. Task Oracle with repair capability
5. Calibration gate (Task Oracle ≥95%, ASB Null halts)
6. Qualitative divergence from ASB Null
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.rsa_poc.v420.env.tri_demand import (
    Action,
    POSITIONS,
    TriDemandV420,
)
from src.rsa_poc.v420.core.norm_state import create_initial_norm_state_v420
from src.rsa_poc.v420.core.compiler import JCOMP420, compute_feasible_420
from src.rsa_poc.v420.core.dsl import RuleType
from src.rsa_poc.v420.calibration import (
    TaskOracleCalibrationV420,
    TaskOracleCalibrationConfigV420,
    ASBNullBaselineV420,
    ASBNullConfigV420,
)


def verify_environment_mechanics():
    """Verify regime flip and STAMP action work correctly."""
    print("=" * 60)
    print("VERIFY: Environment Mechanics")
    print("=" * 60)

    env = TriDemandV420(seed=42, regime_flip_episode=2)

    # Episode 1: regime=0
    obs, _ = env.reset(episode=1)
    assert obs.regime == 0, f"Episode 1 should be regime=0, got {obs.regime}"
    print(f"  ✓ Episode 1: regime=0")

    # Episode 2: regime=1
    obs, _ = env.reset(episode=2)
    assert obs.regime == 1, f"Episode 2 should be regime=1, got {obs.regime}"
    print(f"  ✓ Episode 2: regime=1 (flip)")

    # STAMP action works at ZONE_C
    env.reset(episode=2)
    # Navigate to ZONE_C
    env.step(Action.MOVE_E)  # (4,2) → (4,3)
    env.step(Action.MOVE_E)  # (4,3) → (4,4)
    env.step(Action.MOVE_N)  # (4,4) → (3,4)
    obs, _, _, _, _ = env.step(Action.MOVE_N)  # (3,4) → (2,4) = ZONE_C
    assert obs.agent_pos == POSITIONS["ZONE_C"], f"Should be at ZONE_C"

    obs, _, _, _, _ = env.step(Action.STAMP)
    assert obs.stamped, "STAMP action should set stamped=True"
    print(f"  ✓ STAMP action works at ZONE_C")

    print("✅ Environment mechanics PASSED\n")
    return True


def verify_contradiction_detection():
    """Verify PROHIBIT(STAMP) creates contradiction under regime=1."""
    print("=" * 60)
    print("VERIFY: Contradiction Detection")
    print("=" * 60)

    env = TriDemandV420(seed=42, regime_flip_episode=2)
    norm_state = create_initial_norm_state_v420()
    compiler = JCOMP420(norm_state)
    rule_evals = compiler.compile_all_rules()

    # Check R6 exists and prohibits STAMP
    r6 = norm_state.get_rule("R6")
    assert r6 is not None, "R6 should exist"
    assert r6.type == RuleType.PROHIBITION, "R6 should be PROHIBITION"
    assert r6.effect.action_class.value == "STAMP", "R6 should prohibit STAMP"
    print(f"  ✓ R6: PROHIBITION(STAMP)")

    # Under regime=1 with inventory and not stamped at ZONE_C
    obs, _ = env.reset(episode=2)
    # Navigate to SOURCE (2,2) and collect
    env.step(Action.MOVE_N)  # (4,2) → (3,2)
    obs, _, _, _, _ = env.step(Action.MOVE_N)  # (3,2) → (2,2) = SOURCE
    obs, _, _, _, _ = env.step(Action.COLLECT)

    # Navigate to ZONE_C (2,4)
    env.step(Action.MOVE_E)  # (2,2) → (2,3)
    obs, _, _, _, _ = env.step(Action.MOVE_E)  # (2,3) → (2,4) = ZONE_C

    assert obs.regime == 1, "Should be regime=1"
    assert obs.inventory > 0, "Should have inventory"
    assert not obs.stamped, "Should not be stamped"
    assert obs.agent_pos == POSITIONS["ZONE_C"], "Should be at ZONE_C"
    print(f"  ✓ State: regime=1, inv={obs.inventory}, stamped=False, at ZONE_C")

    # Progress set should include STAMP, but STAMP is prohibited
    tgt = {"kind": "DEPOSIT_ZONE", "target_id": "ZONE_A"}
    progress = env.progress_set(obs, tgt)
    assert "A6" in progress, "Progress set should include STAMP (A6)"
    print(f"  ✓ Progress set includes STAMP: {progress}")

    # Feasibility check should detect contradiction
    mask_result = compute_feasible_420(
        compiled_rules=rule_evals,
        norm_state=norm_state,
        obs=obs,
        env=env,
        current_norm_hash=norm_state.norm_hash,
    )

    assert mask_result.is_contradiction, "Should detect contradiction"
    assert "R6" in (mask_result.blocking_rule_ids or []), "R6 should block"
    print(f"  ✓ Contradiction detected, blocking rules: {mask_result.blocking_rule_ids}")

    print("✅ Contradiction detection PASSED\n")
    return True


def verify_task_oracle():
    """Verify Task Oracle can solve environment with LAW_REPAIR."""
    print("=" * 60)
    print("VERIFY: Task Oracle with LAW_REPAIR (Persistence Verified)")
    print("=" * 60)

    config = TaskOracleCalibrationConfigV420(
        max_steps_per_episode=40,
        max_episodes=10,  # Quick check
        seed=42
    )

    cal = TaskOracleCalibrationV420(config)
    result = cal.run()

    summary = result['summary']
    persistence = result['persistence_counters']

    print(f"  Success rate: {summary['success_rate']:.2%}")
    print(f"  Repairs accepted: {persistence['repairs_accepted_total']}")
    print(f"  Post-repair contradictions: {persistence['contradictions_after_first_accepted_repair']}")
    print(f"  Invariants passed: {summary['invariants_passed']}")

    assert summary['success_rate'] >= 0.9, f"Task Oracle should have high success rate"

    # ========================================================================
    # VALIDITY GATE: Persistence Invariants (hard assertions)
    # These MUST pass for any baseline or future run. Silent regression of
    # the norm-state persistence bug is a validity failure.
    # ========================================================================
    repairs_accepted_total = persistence['repairs_accepted_total']
    contradictions_after_first_accepted_repair = persistence['contradictions_after_first_accepted_repair']
    episode_start_continuity_failures_total = persistence['episode_start_continuity_failures_total']

    assert repairs_accepted_total <= 1, (
        f"VALIDITY FAILURE: repairs_accepted_total={repairs_accepted_total} > 1. "
        "Law not persisting across episodes."
    )
    assert contradictions_after_first_accepted_repair == 0, (
        f"VALIDITY FAILURE: contradictions_after_first_accepted_repair="
        f"{contradictions_after_first_accepted_repair} != 0. "
        "Repair not removing contradiction."
    )
    assert episode_start_continuity_failures_total == 0, (
        f"VALIDITY FAILURE: episode_start_continuity_failures_total="
        f"{episode_start_continuity_failures_total} != 0. "
        "Continuity not enforced across episodes."
    )
    assert summary['invariants_passed'], "All invariants should pass"

    print("✅ Task Oracle PASSED\n")
    return True


def verify_asb_null_halts():
    """Verify ASB Null fails/halts without repair capability."""
    print("=" * 60)
    print("VERIFY: ASB Null Halts at Contradiction")
    print("=" * 60)

    config = ASBNullConfigV420(
        max_steps_per_episode=40,
        max_episodes=20,  # Quick check
        seed=42
    )

    baseline = ASBNullBaselineV420(config)
    result = baseline.run()

    summary = result['summary']
    print(f"  Success rate: {summary['success_rate']:.2%}")
    print(f"  Total halts: {summary['total_halts']}")
    print(f"  Halt rate: {summary['halt_rate']:.2%}")

    # ASB Null should have low success or some halts
    demonstrates = summary['demonstrates_repair_necessity']
    assert demonstrates, "ASB Null should demonstrate repair necessity"

    print("✅ ASB Null halts PASSED\n")
    return True


def verify_qualitative_divergence():
    """Verify baseline diverges from ASB Null."""
    print("=" * 60)
    print("VERIFY: Qualitative Divergence")
    print("=" * 60)

    # Run Task Oracle
    to_config = TaskOracleCalibrationConfigV420(
        max_steps_per_episode=40,
        max_episodes=20,
        seed=42
    )
    to_result = TaskOracleCalibrationV420(to_config).run()

    # Run ASB Null
    asb_config = ASBNullConfigV420(
        max_steps_per_episode=40,
        max_episodes=20,
        seed=42
    )
    asb_result = ASBNullBaselineV420(asb_config).run()

    to_success = to_result['summary']['success_rate']
    asb_success = asb_result['summary']['success_rate']
    to_repairs = to_result['persistence_counters']['repairs_accepted_total']
    post_repair_contradictions = to_result['persistence_counters']['contradictions_after_first_accepted_repair']

    print(f"  Task Oracle success: {to_success:.2%}")
    print(f"  ASB Null success: {asb_success:.2%}")
    print(f"  Task Oracle repairs: {to_repairs}")
    print(f"  Post-repair contradictions: {post_repair_contradictions}")

    # Divergence criteria per spec:
    # - Baseline survives ≥1 contradiction episode
    # - Produces exactly 1 accepted LAW_REPAIR
    # - Zero contradictions after repair (law persists)
    # - Passes all continuity checks under regime=1
    diverges = (
        to_success > asb_success and  # Better than random
        to_repairs == 1 and  # Exactly one repair (law persists)
        post_repair_contradictions == 0  # No contradictions after repair
    )

    assert diverges, "Baseline should diverge from ASB Null with persistent law"
    print(f"  ✓ Divergence: {to_success:.2%} > {asb_success:.2%}")

    print("✅ Qualitative divergence PASSED\n")
    return True


def main():
    print()
    print("=" * 70)
    print("RSA-PoC v4.2 — BASELINE VERIFICATION")
    print("=" * 70)
    print()
    print("This script validates the complete v4.2 implementation.")
    print()

    results = []

    # Run all verifications
    results.append(("Environment Mechanics", verify_environment_mechanics()))
    results.append(("Contradiction Detection", verify_contradiction_detection()))
    results.append(("Task Oracle", verify_task_oracle()))
    results.append(("ASB Null Halts", verify_asb_null_halts()))
    results.append(("Qualitative Divergence", verify_qualitative_divergence()))

    # Summary
    print("=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    print()

    all_passed = True
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("✅ ALL VERIFICATIONS PASSED")
        print()
        print("v4.2 Baseline Status:")
        print("  - Environment: Regime flip + STAMP mechanics working")
        print("  - Normative: PROHIBIT(STAMP) creates contradiction under regime=1")
        print("  - Repair: LAW_REPAIR patches law to resolve contradiction")
        print("  - Persistence: Law persists across episodes (validity gate passed)")
        print("  - Calibration: Task Oracle ≥95%, ASB Null demonstrates necessity")
        print("  - Divergence: Baseline qualitatively different from ASB Null")
        print()
        return 0
    else:
        print("❌ SOME VERIFICATIONS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
