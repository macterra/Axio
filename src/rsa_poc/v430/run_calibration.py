"""
RSA-PoC v4.3 — Oracle Calibration (E2)

Demonstrates existence of at least one admissible pair:
    (Repair A, Repair B)
satisfying all gate rules.

This is the E2 binding requirement from poc_spec_v4.3.md.

Usage:
    python -m src.rsa_poc.v430.run_calibration
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .core import (
    JCOMP430,
    JCOMP430_HASH,
    NormStateV430,
    create_initial_norm_state_v430,
    LawRepairActionV430,
    LawRepairGateV430,
    RepairValidationResultV430,
    TraceEntry,
    TraceLog,
    compute_epoch_0,
    compute_epoch_n,
    create_contradiction_a_entry,
    create_contradiction_b_entry,
    Condition,
    ConditionOp,
    PatchOp,
    PatchOperation,
    create_canonical_repair_b,
)
from .env.tri_demand import (
    TriDemandV430,
    Observation430,
    POSITIONS,
    REGIME_1_START,
    REGIME_2_PREREGISTERED_START,
    progress_set,
)


# ============================================================================
# E2 Calibration Constants
# ============================================================================

E2_NONCE_0 = b"calibration_nonce_epoch_0"
E2_NONCE_1 = b"calibration_nonce_epoch_1"
E2_NONCE_2 = b"calibration_nonce_epoch_2"


# ============================================================================
# Calibration Result
# ============================================================================


class CalibrationResult:
    """Result of E2 calibration."""

    def __init__(self):
        self.success: bool = False
        self.repair_a_valid: bool = False
        self.repair_b_valid: bool = False
        self.repair_a_result: Optional[RepairValidationResultV430] = None
        self.repair_b_result: Optional[RepairValidationResultV430] = None
        self.epoch_chain: List[str] = []
        self.errors: List[str] = []
        self.details: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "repair_a_valid": self.repair_a_valid,
            "repair_b_valid": self.repair_b_valid,
            "epoch_chain": self.epoch_chain,
            "errors": self.errors,
            "details": self.details,
        }


# ============================================================================
# E2 Calibration Functions
# ============================================================================


def create_contradiction_a_state() -> Tuple[TriDemandV430, Observation430, NormStateV430]:
    """
    Create a state where Contradiction A triggers.

    Contradiction A: regime=1, inventory>0, not stamped, STAMP blocked by R6
    """
    env = TriDemandV430()
    obs, _ = env.reset(episode=REGIME_1_START)  # Episode 2 = regime 1

    # Move to SOURCE and COLLECT to get inventory
    # Then navigate to a state where STAMP is needed but blocked

    # Create a synthetic observation that triggers Contradiction A
    synthetic_obs = Observation430(
        agent_pos=POSITIONS["STAMP_LOCATION"],
        inventory=1,
        item_type='A',
        zone_a_demand=1,
        zone_b_demand=1,
        zone_c_demand=1,
        zone_a_satisfied=False,
        zone_b_satisfied=False,
        zone_c_satisfied=False,
        step=5,
        episode=REGIME_1_START,
        rule_r1_active=True,
        regime=1,
        stamped=False,
        dual_delivery_mode=False,
        can_deliver_a=False,
        can_deliver_b=False,
    )

    ns = create_initial_norm_state_v430()

    return env, synthetic_obs, ns


def create_contradiction_b_state(post_a_norm_state: NormStateV430) -> Tuple[Observation430, Dict[str, str]]:
    """
    Create a state where Contradiction B triggers.

    Contradiction B: regime=2, at ZONE_A or ZONE_B, DEPOSIT blocked by R7/R8
    """
    # Create observation at ZONE_A with inventory (can_deliver_a conditions met)
    synthetic_obs = Observation430(
        agent_pos=POSITIONS["ZONE_A"],
        inventory=1,
        item_type='A',
        zone_a_demand=1,
        zone_b_demand=1,
        zone_c_demand=1,
        zone_a_satisfied=False,
        zone_b_satisfied=False,
        zone_c_satisfied=False,
        step=5,
        episode=REGIME_2_PREREGISTERED_START,
        rule_r1_active=True,
        regime=2,
        stamped=True,  # Already stamped from regime 1
        dual_delivery_mode=True,
        can_deliver_a=True,
        can_deliver_b=False,
    )

    # Active obligation target
    obligation_target = {"kind": "DELIVER", "target_id": "ZONE_A"}

    return synthetic_obs, obligation_target


def run_calibration() -> CalibrationResult:
    """
    Run E2 calibration to demonstrate admissible (Repair A, Repair B) pair.

    Returns:
        CalibrationResult with success/failure and details
    """
    result = CalibrationResult()

    print("=" * 60)
    print("RSA-PoC v4.3 — E2 Calibration")
    print("=" * 60)
    print()

    # Step 1: Create initial norm state and epoch_0
    print("Step 1: Initialize norm state and epoch chain")
    ns = create_initial_norm_state_v430()
    epoch_0 = compute_epoch_0(ns.law_fingerprint, E2_NONCE_0)
    result.epoch_chain.append(epoch_0)
    print(f"  epoch_0: {epoch_0[:16]}...")
    print(f"  law_fingerprint: {ns.law_fingerprint[:16]}...")
    print(f"  rules: {[r.id for r in ns.rules]}")
    print()

    # Step 2: Create Contradiction A state
    print("Step 2: Create Contradiction A state")
    env, obs_a, ns = create_contradiction_a_state()
    print(f"  regime: {obs_a.regime}")
    print(f"  position: {obs_a.position}")
    print(f"  inventory: {obs_a.inventory}")
    print(f"  stamped: {obs_a.stamped}")
    print()

    # Step 3: Create trace entry for Contradiction A
    print("Step 3: Create trace entry for Contradiction A")
    trace_log = TraceLog(run_seed=42)  # Use fixed seed for calibration
    obligation_target_a = {"kind": "DELIVER", "target_id": "ZONE_A"}
    trace_a = create_contradiction_a_entry(
        run_seed=42,
        episode=REGIME_1_START,
        step=5,
        blocking_rule_ids=["R6"],
        active_obligation_target=obligation_target_a,
        progress_actions={"A6"},  # STAMP
        compiled_permitted_actions=set(),  # STAMP blocked
    )
    trace_log.add(trace_a)
    print(f"  trace_id: {trace_a.trace_entry_id}")
    print(f"  blocking_rules: {trace_a.blocking_rule_ids}")
    print()

    # Step 4: Initialize Law-Repair Gate
    print("Step 4: Initialize Law-Repair Gate")

    def env_progress_set(obs: Any, target: Dict[str, str]) -> set:
        return progress_set(obs, target)

    gate = LawRepairGateV430(
        trace_log=trace_log._by_id,  # Use the ID-to-entry dict
        expected_compiler_hash=JCOMP430_HASH,
        env_progress_set_fn=env_progress_set,
        max_retries_per_contradiction=2,
    )
    gate.initialize_epoch_chain(epoch_0)
    gate.set_regime(1)
    print(f"  compiler_hash: {JCOMP430_HASH[:16]}...")
    print(f"  regime: {gate.regime}")
    print()

    # Step 5: Generate and validate Repair A
    print("Step 5: Generate and validate Repair A")

    # Create Repair A: Add exception to R6
    # Exception: Allow STAMP when agent has inventory >= 1 (HAS_RESOURCE with arg=1)
    # This makes STAMP legal when the agent has items to stamp
    exception_condition = Condition(op=ConditionOp.HAS_RESOURCE, args=[1])
    patch_r6 = PatchOperation(
        op=PatchOp.ADD_EXCEPTION,
        target_rule_id="R6",
        exception_condition=exception_condition,
    )

    repair_a = LawRepairActionV430.create(
        trace_entry_id=trace_a.trace_entry_id,
        rule_ids=["R6"],
        patch_ops=[patch_r6],
        prior_repair_epoch=None,  # First repair
        contradiction_type='A',
        regime_at_submission=1,
    )

    print(f"  repair_fingerprint: {repair_a.repair_fingerprint[:16]}...")
    print(f"  rule_ids: {repair_a.rule_ids}")
    print(f"  patch_ops: {[p.op.value for p in repair_a.patch_ops]}")

    # Compile norm state for validation
    compiler = JCOMP430(ns)
    compiled_rules = compiler.compile_all_rules()

    # Get compiled permitted actions
    compiled_permitted: set = set()
    for rule in compiled_rules:
        if rule.rule_type == "PERMISSION":
            compiled_permitted |= {"A0", "A1", "A2", "A3", "A4", "A5", "A6"}
    for rule in compiled_rules:
        if rule.rule_type == "PROHIBITION" and rule.active(obs_a, ns.norm_hash):
            if rule.effect.get("action_class") == "STAMP":
                compiled_permitted -= {"A6"}

    # obligation_target_a already defined above

    # Validate Repair A
    result_a = gate.validate_repair(
        repair_action=repair_a,
        norm_state=ns,
        obs=obs_a,
        active_obligation_target=obligation_target_a,
        compiled_permitted_actions=compiled_permitted,
        compile_fn=lambda ns: JCOMP430(ns).compile_all_rules(),
        compiler_hash=JCOMP430_HASH,
        env_nonce=E2_NONCE_1.decode('utf-8'),
    )

    result.repair_a_result = result_a
    result.repair_a_valid = result_a.valid

    if result_a.valid:
        print(f"  ✅ Repair A VALID")
        print(f"    new_law_fingerprint: {result_a.new_law_fingerprint[:16]}...")
        print(f"    new_repair_epoch: {result_a.new_repair_epoch[:16]}...")

        # Accept repair and update state
        gate.accept_repair(repair_a, result_a.new_repair_epoch, result_a.patched_norm_state)
        result.epoch_chain.append(result_a.new_repair_epoch)
        ns = result_a.patched_norm_state
    else:
        print(f"  ❌ Repair A INVALID: {result_a.failure_reason}")
        print(f"    detail: {result_a.failure_detail}")
        result.errors.append(f"Repair A failed: {result_a.failure_reason}")
        result.details["repair_a_failure"] = result_a.failure_detail
        return result
    print()

    # Step 6: Create Contradiction B state
    print("Step 6: Create Contradiction B state (regime 2)")
    gate.set_regime(2)
    obs_b, obligation_target_b = create_contradiction_b_state(ns)
    print(f"  regime: {obs_b.regime}")
    print(f"  position: {obs_b.position}")
    print(f"  can_deliver_a: {obs_b.can_deliver_a}")
    print()

    # Step 7: Create trace entry for Contradiction B
    print("Step 7: Create trace entry for Contradiction B")
    trace_b = create_contradiction_b_entry(
        run_seed=42,
        episode=REGIME_2_PREREGISTERED_START,
        step=5,
        blocking_rule_ids=["R7", "R8"],
        active_obligation_target=obligation_target_b,
        progress_actions={"A5"},  # DEPOSIT
        compiled_permitted_actions=set(),  # DEPOSIT blocked
    )
    trace_log.add(trace_b)
    gate.trace_log = trace_log._by_id  # Update gate's trace log
    print(f"  trace_id: {trace_b.trace_entry_id}")
    print(f"  blocking_rules: {trace_b.blocking_rule_ids}")
    print()

    # Step 8: Generate and validate Repair B
    print("Step 8: Generate and validate Repair B")

    repair_b = create_canonical_repair_b(
        trace_entry_id=trace_b.trace_entry_id,
        prior_repair_epoch=result.epoch_chain[-1],  # epoch_1
    )

    print(f"  repair_fingerprint: {repair_b.repair_fingerprint[:16]}...")
    print(f"  rule_ids: {repair_b.rule_ids}")
    print(f"  prior_repair_epoch: {repair_b.prior_repair_epoch[:16]}...")

    # Compile updated norm state for validation
    compiler_b = JCOMP430(ns)
    compiled_rules_b = compiler_b.compile_all_rules()

    # Get compiled permitted actions for post-A state
    compiled_permitted_b: set = set()
    for rule in compiled_rules_b:
        if rule.rule_type == "PERMISSION":
            compiled_permitted_b |= {"A0", "A1", "A2", "A3", "A4", "A5", "A6"}
    for rule in compiled_rules_b:
        if rule.rule_type == "PROHIBITION" and rule.active(obs_b, ns.norm_hash):
            if rule.effect.get("action_class") == "DEPOSIT":
                compiled_permitted_b -= {"A5"}

    # Validate Repair B
    result_b = gate.validate_repair(
        repair_action=repair_b,
        norm_state=ns,
        obs=obs_b,
        active_obligation_target=obligation_target_b,
        compiled_permitted_actions=compiled_permitted_b,
        compile_fn=lambda ns: JCOMP430(ns).compile_all_rules(),
        compiler_hash=JCOMP430_HASH,
        env_nonce=E2_NONCE_2.decode('utf-8'),
    )

    result.repair_b_result = result_b
    result.repair_b_valid = result_b.valid

    if result_b.valid:
        print(f"  ✅ Repair B VALID")
        print(f"    new_law_fingerprint: {result_b.new_law_fingerprint[:16]}...")
        print(f"    new_repair_epoch: {result_b.new_repair_epoch[:16]}...")

        # Accept repair
        gate.accept_repair(repair_b, result_b.new_repair_epoch, result_b.patched_norm_state)
        result.epoch_chain.append(result_b.new_repair_epoch)
    else:
        print(f"  ❌ Repair B INVALID: {result_b.failure_reason}")
        print(f"    detail: {result_b.failure_detail}")
        result.errors.append(f"Repair B failed: {result_b.failure_reason}")
        result.details["repair_b_failure"] = result_b.failure_detail
        return result
    print()

    # Step 9: Summary
    print("=" * 60)
    print("E2 CALIBRATION SUMMARY")
    print("=" * 60)
    print()

    if result.repair_a_valid and result.repair_b_valid:
        result.success = True
        print("✅ E2 PASSED: Admissible (Repair A, Repair B) pair exists")
        print()
        print(f"Epoch chain:")
        for i, epoch in enumerate(result.epoch_chain):
            print(f"  epoch_{i}: {epoch[:32]}...")
        print()
        print(f"Gate state:")
        print(f"  repair_count: {gate.repair_count}")
        print(f"  repairs_by_regime: {list(gate._repair_by_regime.keys())}")
    else:
        result.success = False
        print("❌ E2 FAILED: No admissible repair pair")
        print(f"Errors: {result.errors}")

    print()

    return result


# ============================================================================
# Main
# ============================================================================

def main():
    """Run calibration and output results."""
    result = run_calibration()

    # Save result to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"v430_calibration_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(result.to_dict(), f, indent=2)

    print(f"Results saved to: {output_file}")

    return 0 if result.success else 1


if __name__ == "__main__":
    exit(main())
