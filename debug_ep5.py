#!/usr/bin/env python3
"""Debug a single failing Ep5 to trace what the LLM outputs."""

import os
import sys
sys.path.insert(0, '/home/david/Axio')

from src.rsa_poc.v440.env.tri_demand import TriDemandV440
from src.rsa_poc.v440.deliberator import LLMDeliberatorV440, LLMDeliberatorConfigV440 as LLMConfig
from src.rsa_poc.v440.core.norm_state import NormStateV430
from src.rsa_poc.v440.run_llm_baseline import create_initial_norm_state_v430
from src.rsa_poc.v440.run_llm_baseline import task_aware_select

env = TriDemandV440(seed=42)
norm_state = create_initial_norm_state_v430()

config = LLMConfig(
    model="claude-sonnet-4-20250514",
    normative_opacity=False,  # Baseline-44
)
deliberator = LLMDeliberatorV440(config)

# Simulate reaching regime 2 with repairs (as the real run does)
for ep in range(4):
    obs, info = env.reset()
    if ep == 1:
        env.record_repair_a_accepted(ep)
    # Quickly "complete" each episode by not running them

# Now run Ep4 (which succeeds) to see pattern
print("=== Simulating Ep4 (first regime-2, should succeed) ===")
obs, info = env.reset(episode=4)
print(f"Regime: {env.regime}, stamped: {env.state.stamped}")

# And now Ep5 (which fails)
print("\n=== Running Ep5 (first failing regime-2) ===")
obs, info = env.reset(episode=5)
print(f"Regime: {env.regime}, stamped: {env.state.stamped}")

# Set collision traces
deliberator.set_collision_traces(env.get_collision_traces())

# Run first 10 steps and trace
for step in range(10):
    regime = env.regime

    output = deliberator.deliberate(
        observation=obs,
        norm_state=norm_state,
        episode=5,
        step=step,
        regime=regime,
        bijection=env.bijection,
    )

    if output.error:
        print(f"Step {step}: ERROR: {output.error}")
        break

    # Get justified actions
    justified = [j.action_id for j in output.justifications]

    # Task-aware selection
    if justified:
        action_id = task_aware_select(justified, obs, regime)
    else:
        action_id = "A0"

    # Check if A6 (STAMP) is justified
    stamp_justified = "A6" in justified

    # Execute
    pos = tuple(env.state.agent_pos)
    inv = env.state.inventory
    stamped = env.state.stamped
    obs, reward, term, trunc, info = env.step(action_id)
    outcome = info.get('last_action_outcome', 'None')

    print(f"Step {step}: pos={pos}, inv={inv}, stamped={stamped} | justified={justified} | selected={action_id} | outcome={outcome}")

    if term or trunc:
        print(f"  Episode ended: term={term}, trunc={trunc}")
        break

print("\n=== Final state ===")
print(f"Inventory: {env.state.inventory}")
print(f"Stamped: {env.state.stamped}")
print(f"Zones satisfied: A={env.state.zone_satisfied[0]}, B={env.state.zone_satisfied[1]}, C={env.state.zone_satisfied[2]}")
