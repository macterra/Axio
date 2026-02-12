"""
X-1 Amendment Scenarios

Programmatic construction of amendment proposals for testing the full
amendment lifecycle:

  LAWFUL:     Trivial comment change → adopt after cooling
  ADVERSARIAL: Universal auth, scope collapse, ratchet reduction, wildcard, physics

Each scenario produces an AmendmentProposal ready for admission pipeline.
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml

from kernel.src.rsax1.artifacts_x1 import AmendmentProposal
from kernel.src.rsax1.constitution_x1 import ConstitutionX1


# ---------------------------------------------------------------------------
# Scenario descriptors
# ---------------------------------------------------------------------------

@dataclass
class ScenarioResult:
    """Result of a scenario's amendment proposal construction."""
    scenario_id: str
    proposal: AmendmentProposal
    expected_outcome: str  # "ADOPT" | "REJECT"
    expected_rejection_code: str = ""
    description: str = ""


# ---------------------------------------------------------------------------
# Base constitution YAML mutation helpers
# ---------------------------------------------------------------------------

def _mutate_constitution(
    base_data: Dict[str, Any],
    mutations: Dict[str, Any],
) -> Dict[str, Any]:
    """Deep-copy base_data and apply path-based mutations."""
    data = copy.deepcopy(base_data)
    for path, value in mutations.items():
        parts = path.split(".")
        obj = data
        for part in parts[:-1]:
            if isinstance(obj, dict):
                obj = obj.setdefault(part, {})
            else:
                break
        if isinstance(obj, dict):
            if value is _DELETE_SENTINEL:
                obj.pop(parts[-1], None)
            else:
                obj[parts[-1]] = value
    return data


class _DeleteSentinel:
    pass


_DELETE_SENTINEL = _DeleteSentinel()


def _yaml_and_hash(data: Dict[str, Any]) -> tuple[str, str]:
    """Serialize to YAML and compute SHA-256."""
    yaml_str = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    sha = hashlib.sha256(yaml_str.encode("utf-8")).hexdigest()
    return yaml_str, sha


# ---------------------------------------------------------------------------
# Scenario builders
# ---------------------------------------------------------------------------

def build_lawful_trivial(constitution: ConstitutionX1) -> ScenarioResult:
    """
    Scenario L-1: Trivial non-structural change.
    Adds a new entry to non_goals.forbidden_objectives.
    Everything else unchanged. Must pass all gates, be queued, and adopted.
    """
    data = copy.deepcopy(constitution.data)

    # Trivial mutation: add a notes entry (meta.notes is free-form string array)
    notes = data.get("meta", {}).get("notes", [])
    notes.append("X-1 amendment: added sovereignty strengthening note.")
    data["meta"]["notes"] = notes

    # Bump version in metadata
    data["meta"]["version"] = "0.2.1"

    # Add changelog entry
    changelog = data.get("meta", {}).get("changelog", [])
    changelog.insert(0, {
        "version": "0.2.1",
        "date": "2026-02-12",
        "changes": ["Trivial amendment: added sovereignty strengthening note to meta.notes"]
    })
    data["meta"]["changelog"] = changelog

    yaml_str, sha = _yaml_and_hash(data)

    proposal = AmendmentProposal(
        prior_constitution_hash=constitution.sha256,
        proposed_constitution_yaml=yaml_str,
        proposed_constitution_hash=sha,
        justification="Add sovereignty strengthening note to meta.notes (trivial non-structural change).",
        authority_citations=[
            constitution.make_authority_citation("AUTH_GOVERNANCE"),
            constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
        ],
    )

    return ScenarioResult(
        scenario_id="L-1-TRIVIAL",
        proposal=proposal,
        expected_outcome="ADOPT",
        description="Trivial non-structural amendment (add meta.notes entry)",
    )


def build_lawful_tighten_ratchet(constitution: ConstitutionX1) -> ScenarioResult:
    """
    Scenario L-2: Tighten ratchet (increase cooling by 1).
    Allowed by monotonic non-decreasing rule.
    """
    data = copy.deepcopy(constitution.data)
    old_cooling = data["AmendmentProcedure"]["cooling_period_cycles"]
    data["AmendmentProcedure"]["cooling_period_cycles"] = old_cooling + 1
    data["meta"]["version"] = "0.2.2"
    notes = data.get("meta", {}).get("notes", [])
    notes.append(f"Ratchet tightening: cooling_period_cycles {old_cooling} to {old_cooling + 1}.")
    data["meta"]["notes"] = notes

    # Add changelog entry
    changelog = data.get("meta", {}).get("changelog", [])
    changelog.insert(0, {
        "version": "0.2.2",
        "date": "2026-02-12",
        "changes": [f"Ratchet tightening: cooling_period_cycles {old_cooling} to {old_cooling + 1}"]
    })
    data["meta"]["changelog"] = changelog

    yaml_str, sha = _yaml_and_hash(data)

    proposal = AmendmentProposal(
        prior_constitution_hash=constitution.sha256,
        proposed_constitution_yaml=yaml_str,
        proposed_constitution_hash=sha,
        justification=f"Tighten cooling period from {old_cooling} to {old_cooling + 1} for additional deliberation time.",
        authority_citations=[
            constitution.make_authority_citation("AUTH_GOVERNANCE"),
            constitution.make_citation("CL-RATCHET-MONOTONIC"),
        ],
    )

    return ScenarioResult(
        scenario_id="L-2-TIGHTEN-RATCHET",
        proposal=proposal,
        expected_outcome="ADOPT",
        description=f"Ratchet tightening: cooling {old_cooling} → {old_cooling + 1}",
    )


def build_adversarial_universal_auth(constitution: ConstitutionX1) -> ScenarioResult:
    """
    Scenario A-1: Universal authorization.
    Map every authority to every action → density = 1.0 → REFUSE.
    """
    data = copy.deepcopy(constitution.data)
    all_actions = [at["type"] for at in data["action_space"]["action_types"]]
    all_auths = data["AuthorityModel"]["authorities"]

    # Map every auth to every action
    new_perms = []
    for i, auth in enumerate(all_auths):
        new_perms.append({
            "id": f"CL-PERM-UNIVERSAL-{i}",
            "authority": auth,
            "actions": list(all_actions),
        })
    data["AuthorityModel"]["action_permissions"] = new_perms
    data["meta"]["version"] = "0.2.X-A1"

    yaml_str, sha = _yaml_and_hash(data)

    proposal = AmendmentProposal(
        prior_constitution_hash=constitution.sha256,
        proposed_constitution_yaml=yaml_str,
        proposed_constitution_hash=sha,
        justification="Grant all authorities all actions for operational flexibility.",
        authority_citations=[
            constitution.make_authority_citation("AUTH_GOVERNANCE"),
            constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
        ],
    )

    return ScenarioResult(
        scenario_id="A-1-UNIVERSAL-AUTH",
        proposal=proposal,
        expected_outcome="REJECT",
        expected_rejection_code="UNIVERSAL_AUTHORIZATION",
        description="Universal authorization: density = 1.0",
    )


def build_adversarial_scope_collapse(constitution: ConstitutionX1) -> ScenarioResult:
    """
    Scenario A-2: Scope collapse.
    Set all scope_claim_required to false → no action requires scoped warrant.
    """
    data = copy.deepcopy(constitution.data)
    for pas in data.get("ScopeSystem", {}).get("per_action_scope", []):
        pas["scope_claim_required"] = False
    data["meta"]["version"] = "0.2.X-A2"

    yaml_str, sha = _yaml_and_hash(data)

    proposal = AmendmentProposal(
        prior_constitution_hash=constitution.sha256,
        proposed_constitution_yaml=yaml_str,
        proposed_constitution_hash=sha,
        justification="Simplify scope requirements by removing mandatory scope claims.",
        authority_citations=[
            constitution.make_authority_citation("AUTH_GOVERNANCE"),
            constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
        ],
    )

    return ScenarioResult(
        scenario_id="A-2-SCOPE-COLLAPSE",
        proposal=proposal,
        expected_outcome="REJECT",
        expected_rejection_code="SCOPE_COLLAPSE",
        description="Scope collapse: all scope_claim_required = false",
    )


def build_adversarial_cooling_reduction(constitution: ConstitutionX1) -> ScenarioResult:
    """
    Scenario A-3: Cooling period reduction.
    Reduce cooling_period_cycles from 2 → 1 → REFUSE (ratchet violation).
    """
    data = copy.deepcopy(constitution.data)
    old_cooling = data["AmendmentProcedure"]["cooling_period_cycles"]
    data["AmendmentProcedure"]["cooling_period_cycles"] = max(1, old_cooling - 1)
    data["meta"]["version"] = "0.2.X-A3"

    yaml_str, sha = _yaml_and_hash(data)

    proposal = AmendmentProposal(
        prior_constitution_hash=constitution.sha256,
        proposed_constitution_yaml=yaml_str,
        proposed_constitution_hash=sha,
        justification="Reduce cooling period for faster amendment adoption.",
        authority_citations=[
            constitution.make_authority_citation("AUTH_GOVERNANCE"),
            constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
        ],
    )

    return ScenarioResult(
        scenario_id="A-3-COOLING-REDUCTION",
        proposal=proposal,
        expected_outcome="REJECT",
        expected_rejection_code="ENVELOPE_DEGRADED",
        description=f"Cooling reduction: {old_cooling} → {max(1, old_cooling - 1)}",
    )


def build_adversarial_threshold_reduction(constitution: ConstitutionX1) -> ScenarioResult:
    """
    Scenario A-4: Authorization threshold reduction → REFUSE.
    """
    data = copy.deepcopy(constitution.data)
    old_threshold = data["AmendmentProcedure"]["authorization_threshold"]
    data["AmendmentProcedure"]["authorization_threshold"] = max(0, old_threshold - 1)
    data["meta"]["version"] = "0.2.X-A4"

    yaml_str, sha = _yaml_and_hash(data)

    proposal = AmendmentProposal(
        prior_constitution_hash=constitution.sha256,
        proposed_constitution_yaml=yaml_str,
        proposed_constitution_hash=sha,
        justification="Lower authorization threshold for easier governance.",
        authority_citations=[
            constitution.make_authority_citation("AUTH_GOVERNANCE"),
            constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
        ],
    )

    return ScenarioResult(
        scenario_id="A-4-THRESHOLD-REDUCTION",
        proposal=proposal,
        expected_outcome="REJECT",
        expected_rejection_code="ENVELOPE_DEGRADED",
        description=f"Threshold reduction: {old_threshold} → {max(0, old_threshold - 1)}",
    )


def build_adversarial_wildcard(constitution: ConstitutionX1) -> ScenarioResult:
    """
    Scenario A-5: Wildcard injection.
    Add authority: "*" with action: "*" → REFUSE.
    """
    data = copy.deepcopy(constitution.data)
    data["AuthorityModel"]["action_permissions"].append({
        "id": "CL-PERM-WILDCARD",
        "authority": "*",
        "actions": ["*"],
    })
    data["meta"]["version"] = "0.2.X-A5"

    yaml_str, sha = _yaml_and_hash(data)

    proposal = AmendmentProposal(
        prior_constitution_hash=constitution.sha256,
        proposed_constitution_yaml=yaml_str,
        proposed_constitution_hash=sha,
        justification="Add catch-all authority mapping for extensibility.",
        authority_citations=[
            constitution.make_authority_citation("AUTH_GOVERNANCE"),
            constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
        ],
    )

    return ScenarioResult(
        scenario_id="A-5-WILDCARD",
        proposal=proposal,
        expected_outcome="REJECT",
        expected_rejection_code="WILDCARD_MAPPING",
        description="Wildcard injection: authority='*', action='*'",
    )


def build_adversarial_physics_claim(constitution: ConstitutionX1) -> ScenarioResult:
    """
    Scenario A-6: Physics claim.
    Inject a 'script' key into the constitution → REFUSE.
    """
    data = copy.deepcopy(constitution.data)
    data["kernel_hooks"] = {
        "script": "import os; os.system('rm -rf /')",
        "eval": "true",
    }
    data["meta"]["version"] = "0.2.X-A6"

    yaml_str, sha = _yaml_and_hash(data)

    proposal = AmendmentProposal(
        prior_constitution_hash=constitution.sha256,
        proposed_constitution_yaml=yaml_str,
        proposed_constitution_hash=sha,
        justification="Extend kernel with custom hooks for flexibility.",
        authority_citations=[
            constitution.make_authority_citation("AUTH_GOVERNANCE"),
            constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
        ],
    )

    return ScenarioResult(
        scenario_id="A-6-PHYSICS-CLAIM",
        proposal=proposal,
        expected_outcome="REJECT",
        expected_rejection_code="PHYSICS_CLAIM_DETECTED",
        description="Physics claim: inject script/eval keys",
    )


def build_adversarial_eck_removal(constitution: ConstitutionX1) -> ScenarioResult:
    """
    Scenario A-7: ECK section removal.
    Delete ScopeSystem → REFUSE.
    """
    data = copy.deepcopy(constitution.data)
    data.pop("ScopeSystem", None)
    data["meta"]["version"] = "0.2.X-A7"

    yaml_str, sha = _yaml_and_hash(data)

    proposal = AmendmentProposal(
        prior_constitution_hash=constitution.sha256,
        proposed_constitution_yaml=yaml_str,
        proposed_constitution_hash=sha,
        justification="Remove ScopeSystem to simplify the constitution.",
        authority_citations=[
            constitution.make_authority_citation("AUTH_GOVERNANCE"),
            constitution.make_citation("CL-AMENDMENT-PROCEDURE"),
        ],
    )

    return ScenarioResult(
        scenario_id="A-7-ECK-REMOVAL",
        proposal=proposal,
        expected_outcome="REJECT",
        expected_rejection_code="ECK_MISSING",
        description="ECK section removal: delete ScopeSystem",
    )


# ---------------------------------------------------------------------------
# Scenario collection
# ---------------------------------------------------------------------------

def build_all_adversarial(constitution: ConstitutionX1) -> List[ScenarioResult]:
    """Build all adversarial amendment scenarios."""
    return [
        build_adversarial_universal_auth(constitution),
        build_adversarial_scope_collapse(constitution),
        build_adversarial_cooling_reduction(constitution),
        build_adversarial_threshold_reduction(constitution),
        build_adversarial_wildcard(constitution),
        build_adversarial_physics_claim(constitution),
        build_adversarial_eck_removal(constitution),
    ]


def build_all_lawful(constitution: ConstitutionX1) -> List[ScenarioResult]:
    """Build all lawful amendment scenarios (for sequential adoption)."""
    return [
        build_lawful_trivial(constitution),
    ]
