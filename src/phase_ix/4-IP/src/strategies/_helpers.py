"""
Strategy Helpers — Shared utilities for IX-4 strategy classes.

Provides the _cite_for helper implementing the universal citation rule (§7.2):
  - Cite the authority with the lexicographically smallest canonical serialization
    among all artifacts in available_authorities covering (key, WRITE).
"""

import json
from typing import Any, Optional


def canonical_artifact_string(auth: dict[str, Any]) -> str:
    """Compute canonical serialization of an authority artifact per §2.5."""
    return json.dumps({
        "authority_id": auth["authority_id"],
        "commitment": auth["commitment"],
        "created_epoch": auth["created_epoch"],
        "holder_agent_id": auth["holder_agent_id"],
        "issuer_agent_id": auth["issuer_agent_id"],
        "scope": [{"operation": s["operation"], "target": s["target"]}
                  for s in auth["scope"]],
        "status": auth["status"],
    }, separators=(',', ':'), ensure_ascii=False)


def cite_for_key(
    key: str,
    available_authorities: list[str],
    authority_lookup: dict[str, dict[str, Any]],
) -> list[str]:
    """Universal citation rule per §7.2.

    Returns a list with at most 1 authority_id: the lexicographically
    smallest canonical serialization among all ALLOW artifacts in
    available_authorities that cover (key, WRITE) for this agent.

    Args:
        key: The state key to cite for (e.g., "K_POLICY").
        available_authorities: List of authority IDs available to this agent.
        authority_lookup: Dict mapping authority_id → full artifact dict.

    Returns:
        List of 0 or 1 authority_id strings.
    """
    target = f"STATE:/{key}"
    candidates = []
    for aid in available_authorities:
        auth = authority_lookup.get(aid)
        if auth is None:
            continue
        if auth["commitment"] != "ALLOW":
            continue
        # Check scope covers (key, WRITE)
        covers = False
        for scope_atom in auth["scope"]:
            if scope_atom["target"] == target and scope_atom["operation"] == "WRITE":
                covers = True
                break
        if covers:
            canonical = canonical_artifact_string(auth)
            candidates.append((canonical, aid))
    if not candidates:
        return []
    candidates.sort(key=lambda x: x[0])
    return [candidates[0][1]]
