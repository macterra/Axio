"""
CUD Admissibility Evaluator — Per preregistration §2.6

Two-pass evaluation:
  Pass 1: Capability + Veto check (per action)
  Pass 2: Interference check (across Pass-1-admissible actions)

Returns only opaque outcome tokens (atomic blindness).
"""

from typing import Any, Optional
from .agent_model import ActionRequest
from .authority_store import AuthorityStore


# Outcome tokens per §2.10
EXECUTED = "EXECUTED"
JOINT_ADMISSIBILITY_FAILURE = "JOINT_ADMISSIBILITY_FAILURE"
ACTION_FAULT = "ACTION_FAULT"
NO_ACTION = "NO_ACTION"


def _pass1_check(
    action: ActionRequest,
    authority_store: AuthorityStore,
) -> tuple[str, str]:
    """
    Pass 1 — Capability and Veto Check per §2.6.

    Returns (result, detail):
      ("PASS", "") or ("FAIL", reason) or ("ACTION_FAULT", reason)
    """
    agent_id = action.agent_id

    # Rule 3: Invalid Capability Claim — check before capability check
    for cited_id in action.authorities_cited:
        if not authority_store.is_held_by(cited_id, agent_id):
            # Check if authority exists at all
            auth = authority_store.get_by_id(cited_id)
            if auth is None:
                return ("ACTION_FAULT", f"INVALID_CAPABILITY_CLAIM: {cited_id} does not exist")
            else:
                return ("ACTION_FAULT", f"INVALID_CAPABILITY_CLAIM: {cited_id} not held by {agent_id}")

    for key in action.declared_scope:
        op = action.action_type

        # Rule 1: Capability Requirement (Closed-World)
        has_allow = False
        for cited_id in action.authorities_cited:
            auth = authority_store.get_by_id(cited_id)
            if auth is None:
                continue
            if auth["commitment"] != "ALLOW":
                continue
            if auth["holder_agent_id"] != agent_id:
                continue
            target = f"STATE:/{key}"
            for scope_atom in auth["scope"]:
                if scope_atom["target"] == target and scope_atom["operation"] == op:
                    has_allow = True
                    break
            if has_allow:
                break

        if not has_allow:
            return ("FAIL", f"No ALLOW capability for ({key}, {op})")

        # Rule 2: Veto Check (Global)
        if authority_store.has_deny_for_scope(key, op):
            return ("FAIL", f"Global DENY on ({key}, {op})")

    return ("PASS", "")


def _pass2_interference(
    admissible_actions: list[ActionRequest],
) -> dict[str, bool]:
    """
    Pass 2 — Interference Check per §2.6.

    Two WRITEs to same key → refuse both.
    READ + WRITE to same key → refuse both.
    Two READs to same key → allowed.

    Returns dict of action_id → True (pass) or False (interference).
    """
    if not admissible_actions:
        return {}

    # Build map of key → list of (action_id, action_type)
    key_actions: dict[str, list[tuple[str, str]]] = {}
    for action in admissible_actions:
        for key in action.declared_scope:
            if key not in key_actions:
                key_actions[key] = []
            key_actions[key].append((action.action_id, action.action_type))

    # Find interfering action IDs
    interfering: set[str] = set()
    for key, actions in key_actions.items():
        if len(actions) < 2:
            continue
        # Check for interference
        has_write = any(at == "WRITE" for _, at in actions)
        if has_write:
            # Any WRITE + anything else on same key → refuse all
            for action_id, _ in actions:
                interfering.add(action_id)

    # Build result
    result: dict[str, bool] = {}
    for action in admissible_actions:
        result[action.action_id] = action.action_id not in interfering
    return result


def evaluate_admissibility(
    actions: dict[str, Optional[ActionRequest]],
    authority_store: AuthorityStore,
    adversarial_tie_break: bool = False,
) -> dict[str, str]:
    """
    Full two-pass admissibility evaluation per §2.6.

    Args:
        actions: dict of agent_id → ActionRequest or None
        authority_store: the authority store
        adversarial_tie_break: if True, execute first action in canonical
            ordering instead of refusing both (Condition E fault injection)

    Returns:
        dict of agent_id → outcome token
    """
    outcomes: dict[str, str] = {}
    pass1_results: dict[str, str] = {}
    pass2_results: dict[str, str] = {}
    admissible: list[ActionRequest] = []

    # Handle None actions and run Pass 1
    for agent_id, action in actions.items():
        if action is None:
            outcomes[agent_id] = NO_ACTION
            pass1_results[agent_id] = "N/A"
            pass2_results[agent_id] = "N/A"
            continue

        result, detail = _pass1_check(action, authority_store)

        if result == "ACTION_FAULT":
            outcomes[agent_id] = ACTION_FAULT
            pass1_results[action.action_id] = "FAULT"
            pass2_results[action.action_id] = "N/A"
        elif result == "FAIL":
            outcomes[agent_id] = JOINT_ADMISSIBILITY_FAILURE
            pass1_results[action.action_id] = "FAIL"
            pass2_results[action.action_id] = "N/A"
        else:
            pass1_results[action.action_id] = "PASS"
            admissible.append(action)

    # Pass 2 — Interference check
    if adversarial_tie_break and len(admissible) >= 2:
        # Condition E: execute first in canonical order instead of refusing
        sorted_actions = sorted(admissible, key=lambda a: a.action_id)
        winner = sorted_actions[0]
        for action in admissible:
            if action.action_id == winner.action_id:
                outcomes[action.agent_id] = EXECUTED
                pass2_results[action.action_id] = "PASS (TIE-BREAK)"
            else:
                outcomes[action.agent_id] = JOINT_ADMISSIBILITY_FAILURE
                pass2_results[action.action_id] = "FAIL (TIE-BREAK)"
    else:
        p2_results = _pass2_interference(admissible)
        for action in admissible:
            if p2_results.get(action.action_id, False):
                outcomes[action.agent_id] = EXECUTED
                pass2_results[action.action_id] = "PASS"
            else:
                outcomes[action.agent_id] = JOINT_ADMISSIBILITY_FAILURE
                pass2_results[action.action_id] = "FAIL"

    return outcomes, pass1_results, pass2_results
