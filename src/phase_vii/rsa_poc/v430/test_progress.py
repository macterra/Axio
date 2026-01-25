#!/usr/bin/env python3
"""Test full feasibility pipeline for ZONE_B with inventory."""

from src.rsa_poc.v430.env.tri_demand import (
    Observation430, progress_set, rank, target_satisfied, TriDemandV430
)
from src.rsa_poc.v430.pipeline import EnvInterfaceWrapper
from src.rsa_poc.v430.core import create_initial_norm_state_v430
from src.rsa_poc.v430.core.compiler import JCOMP430, compute_feasible_430

def main():
    # Create observation: at ZONE_B with inventory=1, regime=0
    # Episode 0 has R1 active (ZONE_A obligation expires ep 2)
    obs = Observation430(
        agent_pos=(0, 2),  # ZONE_B position
        inventory=1,
        item_type="resource",
        regime=0,
        stamped=False,
        zone_a_demand=1,
        zone_b_demand=1,
        zone_c_demand=0,
        zone_a_satisfied=False,  # ZONE_A not satisfied
        zone_b_satisfied=False,
        zone_c_satisfied=True,
        step=5,
        episode=0,  # Episode 0 - R1 active
        rule_r1_active=True,
        dual_delivery_mode=False,
        can_deliver_a=False,
        can_deliver_b=True,
    )

    norm_state = create_initial_norm_state_v430()

    # Create env interface
    env = TriDemandV430(seed=42)
    env_interface = EnvInterfaceWrapper(env)

    print(f"Position: {obs.agent_pos} ({obs.position})")
    print(f"Inventory: {obs.inventory}")
    print(f"Regime: {obs.regime}")
    print(f"Episode: {obs.episode}")
    print()

    # Check all obligation targets
    print("=== Obligation Targets ===")
    for rule in norm_state.rules:
        if rule.type.value == "OBLIGATION":
            target = rule.effect.obligation_target
            if target:
                target_dict = {"kind": target.kind, "target_id": target.target_id}
                satisfied = target_satisfied(obs, target_dict)
                r = rank(obs, target_dict)
                ps = progress_set(obs, target_dict)
                print(f"{rule.id}: {target_dict} - satisfied={satisfied}, rank={r}, progress={ps}")

    # Compile rules
    compiler = JCOMP430(norm_state)
    compiled_rules = compiler.compile_all_rules()
    print(f"\nCompiled {len(compiled_rules)} rules")

    # Compute feasible
    mask_result = compute_feasible_430(
        compiled_rules,
        norm_state,
        obs,
        env_interface,
        norm_state.norm_hash,
        regime=0,
    )

    print(f"\nFeasible actions: {mask_result.feasible}")
    print(f"Binding obligations: {mask_result.binding_obligations}")
    print(f"Binding targets: {mask_result.binding_obligation_targets}")

    if "A5" in mask_result.feasible:
        print("\n✓ A5 (DEPOSIT) IS feasible")
    else:
        print("\n✗ A5 (DEPOSIT) NOT feasible!")


if __name__ == "__main__":
    main()
