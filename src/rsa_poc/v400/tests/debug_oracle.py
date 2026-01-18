"""Debug the Oracle to see what's happening."""

import sys
sys.path.insert(0, '/home/david/Axio/src/rsa_poc')

from v400.env.tri_demand import TriDemandV400, Action, POSITIONS, ACTION_NAMES
from v400.core.oracle import OracleDeliberator
from v400.core.norm_state import create_initial_norm_state
from v400.core.compiler import JCOMP400, CompilationStatus, compute_feasible
from v400.core.harness import MaskedActions, Selector, SelectionSource

def debug_oracle():
    env = TriDemandV400(seed=42)
    obs = env.reset(episode=0)
    norm_state = create_initial_norm_state()
    delib = OracleDeliberator()
    selector = Selector(seed=42)

    print("Initial state:")
    print(env.render())
    print()

    for step in range(15):
        print(f"--- Step {step} ---")
        print(f"Pos: {obs.agent_pos}, Inv: {obs.inventory}")
        print(f"Demands: A={obs.zone_a_demand} B={obs.zone_b_demand} C={obs.zone_c_demand}")
        print(f"Satisfied: A={obs.zone_a_satisfied} B={obs.zone_b_satisfied} C={obs.zone_c_satisfied}")

        # Deliberate
        output = delib.deliberate(obs, norm_state)
        j = output.justifications[0]
        print(f"Deliberation: action={j.action_id}, rules={j.rule_refs}")

        # Compile
        compiler = JCOMP400(norm_state)
        batch = compiler.compile_justifications(output.justifications)
        print(f"Compilation: {batch.compiled_count} compiled, {batch.failed_count} failed")

        for r in batch.results:
            print(f"  {r.action_id}: {r.status.value}")
            if r.error_message:
                print(f"    Error: {r.error_message}")

        # Get compiled predicates
        compiled_predicates = [
            r.predicate for r in batch.results
            if r.status == CompilationStatus.COMPILED and r.predicate is not None
        ]

        # Mask
        mask_result = compute_feasible(
            compiled_predicates,
            norm_state,
            obs,
            0  # episode
        )
        print(f"Mask result: feasible={mask_result.feasible}, binding_obligation={mask_result.binding_obligation}")

        masked = MaskedActions(feasible=mask_result.feasible, feasible_count=mask_result.feasible_count)

        # Select
        selection = selector.select(masked)
        print(f"Selection: {selection.action_id} ({selection.source.value})")

        if selection.source == SelectionSource.HALT:
            print("  -> HALT! Breaking.")
            break

        # Execute
        from v400.env.tri_demand import ACTION_ID_MAP
        action_int = ACTION_ID_MAP.get(selection.action_id, 0)
        obs, reward, done, info = env.step(action_int)
        print(f"Result: reward={reward}, done={done}")

        if done:
            print(f"Episode done! info={info}")
            break

        print()


if __name__ == "__main__":
    debug_oracle()
