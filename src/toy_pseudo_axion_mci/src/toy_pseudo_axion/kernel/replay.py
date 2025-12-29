"""Replay engine for trace verification."""

from typing import Any, Optional, Callable

from ..env.gridworld import GridState, step, clone_state
from ..common.hashing import hash_json


def replay_plan(
    initial_state: GridState,
    plan: dict
) -> list[GridState]:
    """Replay a plan from initial state.

    Args:
        initial_state: Starting environment state
        plan: Plan dict with steps list

    Returns:
        List of states (initial + after each step)
    """
    states = [clone_state(initial_state)]
    current = clone_state(initial_state)

    for step_action in plan.get("steps", []):
        action = {
            "op": step_action.get("op", "noop"),
            "args": step_action.get("args", {})
        }
        current = step(current, action)
        states.append(current)

    return states


def verify_replay_fidelity(
    initial_state: GridState,
    plan: dict,
    claimed_final_state: dict
) -> tuple[bool, Optional[str]]:
    """Verify that replaying a plan produces the claimed final state.

    Args:
        initial_state: Starting environment state
        plan: Plan dict with steps list
        claimed_final_state: The claimed final state dict

    Returns:
        Tuple of (matches, error_message)
    """
    states = replay_plan(initial_state, plan)

    if not states:
        return False, "No states produced from replay"

    final_state = states[-1]
    final_dict = final_state.to_dict()

    # Compare hashes
    claimed_hash = hash_json(claimed_final_state)
    actual_hash = hash_json(final_dict)

    if claimed_hash != actual_hash:
        return False, f"State hash mismatch: claimed {claimed_hash}, actual {actual_hash}"

    return True, None


def extract_choice_from_plan(plan: dict) -> str:
    """Extract the primary choice from a plan.

    Returns the first action's operation in uppercase format.

    Args:
        plan: Plan dict with steps list

    Returns:
        Choice string like "MOVE_N", "PICKUP", etc.
    """
    steps = plan.get("steps", [])
    if not steps:
        return "NOOP"

    first_step = steps[0]
    op = first_step.get("op", "noop").upper()
    args = first_step.get("args", {})

    if op == "MOVE":
        direction = args.get("direction", "N").upper()
        # Map full direction names to abbreviations
        dir_map = {
            "UP": "N", "DOWN": "S", "LEFT": "W", "RIGHT": "E",
            "NORTH": "N", "SOUTH": "S", "WEST": "W", "EAST": "E",
            "N": "N", "S": "S", "E": "E", "W": "W"
        }
        direction = dir_map.get(direction, direction)
        return f"MOVE_{direction}"

    return op


def replay_decision_with_mutation(
    agent_decide_fn: Callable[[GridState], dict],
    env: GridState,
    mutation_var: str,
    mutation_value: Any
) -> tuple[str, dict]:
    """Replay agent decision with a mutated environment.

    This is used by P5' to verify causal claims.

    Args:
        agent_decide_fn: Function that takes env and returns a proposal
        env: Original environment state
        mutation_var: Variable to mutate
        mutation_value: New value for the variable

    Returns:
        Tuple of (choice_string, proposal_dict)
    """
    from ..env.gridworld import mutate

    mutated_env = mutate(env, mutation_var, mutation_value)
    proposal = agent_decide_fn(mutated_env)

    plan = proposal.get("payload", {}).get("plan", {})
    choice = extract_choice_from_plan(plan)

    return choice, proposal
