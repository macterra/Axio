#!/usr/bin/env python3
"""
Debug script: Trace a single failing regime-2 episode step-by-step.
Goal: Determine whether agent is (a) failing to stamp, (b) stamp doesn't stick,
(c) STAMP is masked, or (d) failure signal isn't visible to LLM.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.rsa_poc.v440.env.tri_demand import TriDemandV440, Action
from src.rsa_poc.v440.deliberator import format_execution_channel


def run_one_optimal_episode(env):
    """Run one episode optimally to completion. Returns True if succeeded."""
    env.reset()

    for _ in range(50):
        obs = env.get_observation()

        # Optimal policy
        pos = obs.agent_pos
        inv = obs.inventory
        stamped = obs.stamped
        regime = obs.regime

        # Need to collect?
        if inv == 0:
            if pos == (2, 2):
                action = Action.COLLECT
            elif pos[0] < 2:
                action = Action.MOVE_S
            elif pos[0] > 2:
                action = Action.MOVE_N
            elif pos[1] < 2:
                action = Action.MOVE_E
            else:
                action = Action.MOVE_W
        # Need to stamp?
        elif inv > 0 and not stamped and regime >= 1:
            if pos == (2, 4):
                action = Action.STAMP
            elif pos[1] < 4:
                action = Action.MOVE_E
            elif pos[0] < 2:
                action = Action.MOVE_S
            else:
                action = Action.MOVE_N
        # Need to deposit
        elif inv > 0:
            if not obs.zone_a_satisfied:
                if pos == (2, 0):
                    action = Action.DEPOSIT
                elif pos[1] > 0:
                    action = Action.MOVE_W
                elif pos[0] < 2:
                    action = Action.MOVE_S
                else:
                    action = Action.MOVE_N
            elif not obs.zone_b_satisfied:
                if pos == (0, 2):
                    action = Action.DEPOSIT
                elif pos[0] > 0:
                    action = Action.MOVE_N
                elif pos[1] < 2:
                    action = Action.MOVE_E
                else:
                    action = Action.MOVE_W
            elif not obs.zone_c_satisfied:
                if pos == (4, 2):
                    action = Action.DEPOSIT
                elif pos[0] < 4:
                    action = Action.MOVE_S
                elif pos[1] < 2:
                    action = Action.MOVE_E
                else:
                    action = Action.MOVE_W
            else:
                # All satisfied - just wait
                action = Action.MOVE_N
        else:
            action = Action.MOVE_N

        _, reward, terminated, truncated, info = env.step(action)

        if terminated or truncated:
            return terminated and not truncated  # Return True if success

    return False


def run_diagnostic():
    """Run one regime-2 episode with full logging."""

    seed = 42

    print("=" * 70)
    print(f"DIAGNOSTIC: Regime-2 Episode Trace (seed={seed})")
    print("=" * 70)
    print()

    # Create environment
    env = TriDemandV440(seed=seed)

    # Run episodes until regime 2
    print("Running optimal episodes until regime 2...")
    print("Note: Regime 2 requires Repair A acceptance, triggering manually after ep 2...")

    for ep in range(8):
        obs = env.reset()
        current_regime = env.state.regime
        print(f"  Episode {env.episode_count}: regime={current_regime}")

        # Simulate Repair A acceptance after episode 2 (regime 1)
        if ep == 2:
            env.record_repair_a_accepted(env.episode_count)
            print(f"    --> Repair A accepted! Next episode will be regime 2")

        if current_regime >= 2:
            print(f"\n==> Reached regime 2 at episode {env.episode_count}!")
            break

        run_one_optimal_episode(env)

    # Now run detailed trace
    obs = env.reset()
    print(f"\nStarting detailed trace of regime-2 episode")
    print(f"Episode {env.episode_count}, Regime: {env.state.regime}")
    print()

    print("-" * 70)
    print("STEP-BY-STEP TRACE")
    print("-" * 70)

    terminated = False
    truncated = False

    # First tick - get initial obs
    obs = env.get_observation()
    obs.last_action_outcome = None  # Start of episode

    for tick in range(45):
        if terminated or truncated:
            print(f"\n--- TICK {tick}: EPISODE ENDED ---")
            print(f"  terminated={terminated}, truncated={truncated}")
            print(f"  success={terminated and not truncated}")
            break

        # Get the execution channel text that would be sent to LLM
        exec_channel = format_execution_channel(obs)

        print(f"\n--- TICK {tick} ---")
        print(f"  regime:    {obs.regime}")
        print(f"  pos:       {obs.agent_pos}")
        print(f"  inv:       {obs.inventory}")
        print(f"  stamped:   {obs.stamped}")
        print(f"  last_outcome: {obs.last_action_outcome}")
        print(f"  zones: A={obs.zone_a_satisfied}, B={obs.zone_b_satisfied}, C={obs.zone_c_satisfied}")

        # Check what's in the execution channel
        for line in exec_channel.split('\n'):
            if "Last Action Outcome" in line:
                print(f"  EXEC_CHANNEL: {line.strip()}")

        # SIMULATE REALISTIC AGENT: tries optimal path but might skip stamp
        pos = obs.agent_pos
        inv = obs.inventory

        if inv == 0:
            # Go to source (2, 2)
            if pos == (2, 2):
                action = Action.COLLECT
                chosen = "A4 COLLECT"
            elif pos[0] < 2:
                action = Action.MOVE_S
                chosen = "A1 MOVE_S toward source"
            elif pos[0] > 2:
                action = Action.MOVE_N
                chosen = "A0 MOVE_N toward source"
            elif pos[1] < 2:
                action = Action.MOVE_E
                chosen = "A2 MOVE_E toward source"
            elif pos[1] > 2:
                action = Action.MOVE_W
                chosen = "A3 MOVE_W toward source"
            else:
                action = Action.MOVE_N
                chosen = "MOVE_N fallback"
        elif inv > 0:
            # BAD AGENT: Skip stamp, go directly to deposit at ZONE_A (2,0)
            if not obs.zone_a_satisfied:
                if pos == (2, 0):
                    action = Action.DEPOSIT
                    chosen = "A5 DEPOSIT (will FAIL if not stamped!)"
                elif pos[1] > 0:
                    action = Action.MOVE_W
                    chosen = "A3 MOVE_W toward zone A"
                elif pos[0] < 2:
                    action = Action.MOVE_S
                    chosen = "A1 MOVE_S"
                elif pos[0] > 2:
                    action = Action.MOVE_N
                    chosen = "A0 MOVE_N"
                else:
                    action = Action.MOVE_W
                    chosen = "MOVE_W default"
            else:
                action = Action.MOVE_N
                chosen = "MOVE_N"
        else:
            action = Action.MOVE_N
            chosen = "MOVE_N default"

        print(f"  ACTION: {chosen}")

        # Execute - NOW USE THE RETURNED OBS which has last_action_outcome
        obs, reward, terminated, truncated, info = env.step(action)

        print(f"  reward: {reward}, outcome: {obs.last_action_outcome}")

    print()
    print("=" * 70)
    print("DIAGNOSIS")
    print("=" * 70)
    print("""
The trace above shows what happens when an agent doesn't stamp.

Key observations:
1. DEPOSIT at (2,0) should return FAIL_UNSTAMPED when stamped=False
2. The last_action_outcome field should be visible in EXEC_CHANNEL
3. If agent NEVER sees FAIL_UNSTAMPED, that's the bug!
""")


if __name__ == "__main__":
    run_diagnostic()
