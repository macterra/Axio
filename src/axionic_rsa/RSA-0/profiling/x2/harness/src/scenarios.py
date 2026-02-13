"""
X-2 Treaty Delegation Scenarios

Programmatic construction of treaty grants, revocations, and delegated action
requests for profiling the X-2 treaty pipeline:

  LAWFUL:       Valid grant → delegated action → warrant
  ADVERSARIAL:  Invalid grants/actions rejected by appropriate gates

Each scenario produces the artifacts needed for a cycle input.

Gate coverage map:
  6T — GRANTOR_NOT_CONSTITUTIONAL, TREATY_PERMISSION_MISSING, CITATION_UNRESOLVABLE
  7T — SCHEMA_INVALID, INVALID_FIELD (grantee format, scope_constraints shape, scope_type key)
  8C — INVALID_FIELD (action not in closed set), WILDCARD_MAPPING, GRANTOR_LACKS_PERMISSION,
       SCOPE_COLLAPSE, COVERAGE_INFLATION, EXCESSIVE_DEPTH, DELEGATION_CYCLE,
       DENSITY_MARGIN_VIOLATION, duration exceeded
  8R — GRANT_NOT_FOUND, NONREVOCABLE_GRANT
  SIG — SIGNATURE_MISSING, SIGNATURE_INVALID
  DELEGATION — scope_zone not in grant, missing treaty: citation, Notify zone enforcement
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kernel.src.rsax2.artifacts_x2 import (
    ActiveTreatySet,
    TreatyGrant,
    TreatyRejectionCode,
    TreatyRevocation,
)
from kernel.src.rsax2.constitution_x2 import ConstitutionX2
from kernel.src.rsax2.policy_core_x2 import DelegatedActionRequest
from kernel.src.rsax2.signature import generate_keypair, sign_action_request


# ---------------------------------------------------------------------------
# Scenario descriptors
# ---------------------------------------------------------------------------

@dataclass
class TreatyScenario:
    """A treaty delegation scenario for profiling."""
    scenario_id: str
    description: str
    # Inputs
    grants: List[TreatyGrant] = field(default_factory=list)
    revocations: List[TreatyRevocation] = field(default_factory=list)
    delegated_actions: List[DelegatedActionRequest] = field(default_factory=list)
    pre_populated_grants: List[TreatyGrant] = field(default_factory=list)
    # Expected outcomes
    expected_grant_outcome: str = ""           # "ADMIT" | "REJECT"
    expected_grant_rejection_code: str = ""
    expected_revocation_outcome: str = ""      # "ADMIT" | "REJECT"
    expected_revocation_rejection_code: str = ""
    expected_delegation_outcome: str = ""      # "WARRANT" | "REJECT"
    expected_delegation_rejection_code: str = ""


# ---------------------------------------------------------------------------
# Identity store: stable keypair pool for deterministic scenarios
# ---------------------------------------------------------------------------

class IdentityPool:
    """Cache of generated Ed25519 keypairs for scenario construction."""

    def __init__(self) -> None:
        self._pool: List[tuple] = []

    def get(self, index: int = 0) -> tuple:
        while len(self._pool) <= index:
            self._pool.append(generate_keypair())
        return self._pool[index]

    def grantee_id(self, index: int = 0) -> str:
        return self.get(index)[1]

    def private_key(self, index: int = 0):
        return self.get(index)[0]


# Shared pool across all scenario builders
_POOL = IdentityPool()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_grant(
    constitution: ConstitutionX2,
    grantee_id: str,
    actions: List[str],
    scope_constraints: Dict[str, List[str]],
    duration: int = 10,
    revocable: bool = True,
    grantor: str = "AUTH_DELEGATION",
) -> TreatyGrant:
    """Build a well-formed TreatyGrant."""
    return TreatyGrant(
        grantor_authority_id=grantor,
        grantee_identifier=grantee_id,
        granted_actions=actions,
        scope_constraints=scope_constraints,
        duration_cycles=duration,
        revocable=revocable,
        authority_citations=[
            constitution.make_authority_citation(grantor),
            constitution.make_citation("CL-TREATY-PROCEDURE"),
        ],
        justification=f"Grant {actions} to {grantee_id[:16]}...",
        created_at="2026-02-12T12:00:00Z",
    )


def _make_signed_dar(
    pool_index: int,
    action_type: str,
    fields: Dict[str, Any],
    grant: TreatyGrant,
    scope_type: str,
    scope_zone: str,
) -> DelegatedActionRequest:
    """Create a properly signed DelegatedActionRequest."""
    pk = _POOL.private_key(pool_index)
    gid = _POOL.grantee_id(pool_index)
    dar = DelegatedActionRequest(
        action_type=action_type,
        fields=fields,
        grantee_identifier=gid,
        authority_citations=[f"treaty:{grant.id}#{grant.id}"],
        signature="",
        scope_type=scope_type,
        scope_zone=scope_zone,
        created_at="2026-02-12T12:00:01Z",
    )
    dar.signature = sign_action_request(pk, dar.to_action_request_dict())
    return dar


# ===================================================================
# LAWFUL SCENARIOS — expected to produce warrants
# ===================================================================

def build_lawful_read_delegation(constitution: ConstitutionX2) -> TreatyScenario:
    """
    L-1: Grant ReadLocal(FILE_PATH/ARTIFACTS_READ) → signed DAR → warrant.

    NOTE: The v0.3 constitution requires grantor to hold the action
    in action_permissions (8C.2b). AUTH_DELEGATION doesn't hold ReadLocal.
    This grant will be REJECTED at 8C.2b. The scenario pre-populates the
    grant so the delegated action path can be tested.
    """
    gid = _POOL.grantee_id(0)
    grant = _make_grant(
        constitution, gid,
        actions=["ReadLocal"],
        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]},
    )
    grant.grant_cycle = 0  # Pre-populated

    dar = _make_signed_dar(
        pool_index=0,
        action_type="ReadLocal",
        fields={"path": "./artifacts/test"},
        grant=grant,
        scope_type="FILE_PATH",
        scope_zone="ARTIFACTS_READ",
    )

    return TreatyScenario(
        scenario_id="L-1-READ-DELEGATION",
        description="Lawful ReadLocal delegation via pre-populated grant",
        pre_populated_grants=[grant],
        delegated_actions=[dar],
        expected_delegation_outcome="WARRANT",
    )


def build_lawful_notify_delegation(constitution: ConstitutionX2) -> TreatyScenario:
    """L-2: Grant Notify(LOG_STREAM/TELEMETRY) → signed DAR → warrant."""
    gid = _POOL.grantee_id(1)
    grant = _make_grant(
        constitution, gid,
        actions=["Notify"],
        scope_constraints={"LOG_STREAM": ["TELEMETRY"]},
    )
    grant.grant_cycle = 0

    dar = _make_signed_dar(
        pool_index=1,
        action_type="Notify",
        fields={"message": "delegated notification"},
        grant=grant,
        scope_type="LOG_STREAM",
        scope_zone="TELEMETRY",
    )

    return TreatyScenario(
        scenario_id="L-2-NOTIFY-DELEGATION",
        description="Lawful Notify delegation via pre-populated grant",
        pre_populated_grants=[grant],
        delegated_actions=[dar],
        expected_delegation_outcome="WARRANT",
    )


def build_lawful_revocation(constitution: ConstitutionX2) -> TreatyScenario:
    """L-3: Pre-populate a grant, then revoke it."""
    gid = _POOL.grantee_id(2)
    grant = _make_grant(
        constitution, gid,
        actions=["ReadLocal"],
        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]},
        revocable=True,
    )
    grant.grant_cycle = 0

    rev = TreatyRevocation(
        grant_id=grant.id,
        authority_citations=[
            constitution.make_authority_citation("AUTH_DELEGATION"),
            constitution.make_citation("CL-TREATY-PROCEDURE"),
        ],
        justification="Revoke test grant",
        created_at="2026-02-12T12:00:00Z",
    )

    return TreatyScenario(
        scenario_id="L-3-REVOCATION",
        description="Lawful revocation of a pre-populated grant",
        pre_populated_grants=[grant],
        revocations=[rev],
        expected_revocation_outcome="ADMIT",
    )


# ===================================================================
# ADVERSARIAL GRANT SCENARIOS — expected to be rejected
# ===================================================================

def build_adv_fake_grantor(constitution: ConstitutionX2) -> TreatyScenario:
    """A-1: Non-constitutional grantor → 6T reject."""
    gid = _POOL.grantee_id(3)
    grant = _make_grant(constitution, gid, actions=["ReadLocal"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]})
    grant.grantor_authority_id = "AUTH_FAKE"
    grant.authority_citations = ["authority:0000#AUTH_FAKE"]

    return TreatyScenario(
        scenario_id="A-1-FAKE-GRANTOR",
        description="Non-constitutional grantor rejected at Gate 6T",
        grants=[grant],
        expected_grant_outcome="REJECT",
        expected_grant_rejection_code=TreatyRejectionCode.GRANTOR_NOT_CONSTITUTIONAL,
    )


def build_adv_no_treaty_permission(constitution: ConstitutionX2) -> TreatyScenario:
    """A-2: AUTH_IO_READ has no treaty_permissions → 6T reject."""
    gid = _POOL.grantee_id(3)
    grant = _make_grant(constitution, gid, actions=["ReadLocal"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]},
                        grantor="AUTH_IO_READ")

    return TreatyScenario(
        scenario_id="A-2-NO-TREATY-PERM",
        description="Grantor lacks treaty_permissions → Gate 6T reject",
        grants=[grant],
        expected_grant_outcome="REJECT",
        expected_grant_rejection_code=TreatyRejectionCode.TREATY_PERMISSION_MISSING,
    )


def build_adv_bad_grantee_format(constitution: ConstitutionX2) -> TreatyScenario:
    """A-3: Grantee identifier 'agent:bob' → 7T reject."""
    grant = _make_grant(constitution, "agent:bob", actions=["ReadLocal"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]})

    return TreatyScenario(
        scenario_id="A-3-BAD-GRANTEE-FORMAT",
        description="Grantee 'agent:bob' rejected at Gate 7T",
        grants=[grant],
        expected_grant_outcome="REJECT",
        expected_grant_rejection_code=TreatyRejectionCode.INVALID_FIELD,
    )


def build_adv_scope_not_map(constitution: ConstitutionX2) -> TreatyScenario:
    """A-4: scope_constraints is a list, not a map → 7T reject."""
    gid = _POOL.grantee_id(3)
    grant = _make_grant(constitution, gid, actions=["ReadLocal"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]})
    grant.scope_constraints = ["ARTIFACTS_READ"]  # type: ignore

    return TreatyScenario(
        scenario_id="A-4-SCOPE-NOT-MAP",
        description="scope_constraints is a list (not dict) → Gate 7T reject",
        grants=[grant],
        expected_grant_outcome="REJECT",
        expected_grant_rejection_code=TreatyRejectionCode.INVALID_FIELD,
    )


def build_adv_invalid_scope_type(constitution: ConstitutionX2) -> TreatyScenario:
    """A-5: Invalid scope_type key → 7T reject."""
    gid = _POOL.grantee_id(3)
    grant = _make_grant(constitution, gid, actions=["ReadLocal"],
                        scope_constraints={"INVALID_TYPE": ["ARTIFACTS_READ"]})

    return TreatyScenario(
        scenario_id="A-5-INVALID-SCOPE-TYPE",
        description="scope_type key 'INVALID_TYPE' rejected at Gate 7T",
        grants=[grant],
        expected_grant_outcome="REJECT",
        expected_grant_rejection_code=TreatyRejectionCode.INVALID_FIELD,
    )


def build_adv_wildcard_action(constitution: ConstitutionX2) -> TreatyScenario:
    """A-6: Wildcard actions → 8C.1 reject (not in closed set, before wildcard check)."""
    gid = _POOL.grantee_id(3)
    grant = _make_grant(constitution, gid, actions=["*"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]})

    return TreatyScenario(
        scenario_id="A-6-WILDCARD-ACTION",
        description="Wildcard action '*' rejected at Gate 8C.1 (not in closed set)",
        grants=[grant],
        expected_grant_outcome="REJECT",
        expected_grant_rejection_code=TreatyRejectionCode.INVALID_FIELD,
    )


def build_adv_unknown_action(constitution: ConstitutionX2) -> TreatyScenario:
    """A-7: Action not in closed set → 8C.1 reject."""
    gid = _POOL.grantee_id(3)
    grant = _make_grant(constitution, gid, actions=["DeleteFile"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]})

    return TreatyScenario(
        scenario_id="A-7-UNKNOWN-ACTION",
        description="Action 'DeleteFile' not in closed set → Gate 8C.1 reject",
        grants=[grant],
        expected_grant_outcome="REJECT",
        expected_grant_rejection_code=TreatyRejectionCode.INVALID_FIELD,
    )


def build_adv_grantor_lacks_action(constitution: ConstitutionX2) -> TreatyScenario:
    """
    A-8: AUTH_DELEGATION grants ReadLocal but doesn't hold it → 8C.2b reject.
    This is also the natural result of any grant from AUTH_DELEGATION for
    non-treaty actions — it only has treaty_permissions, not action_permissions.
    """
    gid = _POOL.grantee_id(3)
    grant = _make_grant(constitution, gid, actions=["ReadLocal"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]})
    # AUTH_DELEGATION is the default grantor but doesn't hold ReadLocal

    return TreatyScenario(
        scenario_id="A-8-GRANTOR-LACKS-ACTION",
        description="AUTH_DELEGATION lacks ReadLocal in action_permissions → Gate 8C.2b reject",
        grants=[grant],
        expected_grant_outcome="REJECT",
        expected_grant_rejection_code=TreatyRejectionCode.GRANTOR_LACKS_PERMISSION,
    )


def build_adv_scope_zone_invalid(constitution: ConstitutionX2) -> TreatyScenario:
    """A-9: Zone not in ScopeEnumerations → but 8C.2b GRANTOR_LACKS_PERMISSION fires first."""
    gid = _POOL.grantee_id(3)
    grant = _make_grant(constitution, gid, actions=["ReadLocal"],
                        scope_constraints={"FILE_PATH": ["NONEXISTENT_ZONE"]})

    return TreatyScenario(
        scenario_id="A-9-SCOPE-ZONE-INVALID",
        description="Zone 'NONEXISTENT_ZONE' rejected — GRANTOR_LACKS_PERMISSION fires at 8C.2b before zone check",
        grants=[grant],
        expected_grant_outcome="REJECT",
        expected_grant_rejection_code=TreatyRejectionCode.GRANTOR_LACKS_PERMISSION,
    )


def build_adv_duration_exceeded(constitution: ConstitutionX2) -> TreatyScenario:
    """A-10: duration_cycles > max_treaty_duration_cycles → but 8C.2b fires first
    because AUTH_DELEGATION doesn't hold ReadLocal. Expect GRANTOR_LACKS_PERMISSION."""
    gid = _POOL.grantee_id(3)
    grant = _make_grant(constitution, gid, actions=["ReadLocal"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]},
                        duration=101)

    return TreatyScenario(
        scenario_id="A-10-DURATION-EXCEEDED",
        description="duration_cycles=101 exceeds max=100, but GRANTOR_LACKS_PERMISSION at 8C.2b fires first",
        grants=[grant],
        expected_grant_outcome="REJECT",
        expected_grant_rejection_code=TreatyRejectionCode.GRANTOR_LACKS_PERMISSION,
    )


def build_adv_nonrevocable_revocation(constitution: ConstitutionX2) -> TreatyScenario:
    """A-11: Revoke a non-revocable grant → 8R reject."""
    gid = _POOL.grantee_id(3)
    grant = _make_grant(constitution, gid, actions=["ReadLocal"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]},
                        revocable=False)
    grant.grant_cycle = 0

    rev = TreatyRevocation(
        grant_id=grant.id,
        authority_citations=[
            constitution.make_authority_citation("AUTH_DELEGATION"),
            constitution.make_citation("CL-TREATY-PROCEDURE"),
        ],
        justification="Attempt to revoke non-revocable",
        created_at="2026-02-12T12:00:00Z",
    )

    return TreatyScenario(
        scenario_id="A-11-NONREVOCABLE",
        description="Revoke non-revocable grant → Gate 8R reject",
        pre_populated_grants=[grant],
        revocations=[rev],
        expected_revocation_outcome="REJECT",
        expected_revocation_rejection_code=TreatyRejectionCode.NONREVOCABLE_GRANT,
    )


# ===================================================================
# ADVERSARIAL DELEGATION SCENARIOS — expected to be rejected
# ===================================================================

def build_adv_unsigned_dar(constitution: ConstitutionX2) -> TreatyScenario:
    """A-12: Delegated action without signature → SIGNATURE_MISSING."""
    gid = _POOL.grantee_id(0)
    grant = _make_grant(constitution, gid, actions=["ReadLocal"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]})
    grant.grant_cycle = 0

    dar = DelegatedActionRequest(
        action_type="ReadLocal",
        fields={"path": "./artifacts/test"},
        grantee_identifier=gid,
        authority_citations=[f"treaty:{grant.id}#{grant.id}"],
        signature="",  # MISSING
        scope_type="FILE_PATH",
        scope_zone="ARTIFACTS_READ",
    )

    return TreatyScenario(
        scenario_id="A-12-UNSIGNED-DAR",
        description="Unsigned delegated ActionRequest → SIGNATURE_MISSING",
        pre_populated_grants=[grant],
        delegated_actions=[dar],
        expected_delegation_outcome="REJECT",
        expected_delegation_rejection_code=TreatyRejectionCode.SIGNATURE_MISSING,
    )


def build_adv_wrong_key_dar(constitution: ConstitutionX2) -> TreatyScenario:
    """A-13: DAR signed with wrong key → SIGNATURE_INVALID."""
    gid0 = _POOL.grantee_id(0)
    grant = _make_grant(constitution, gid0, actions=["ReadLocal"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]})
    grant.grant_cycle = 0

    # Build DAR for grantee 0 but sign with key 1
    dar = DelegatedActionRequest(
        action_type="ReadLocal",
        fields={"path": "./artifacts/test"},
        grantee_identifier=gid0,
        authority_citations=[f"treaty:{grant.id}#{grant.id}"],
        signature="",
        scope_type="FILE_PATH",
        scope_zone="ARTIFACTS_READ",
    )
    wrong_pk = _POOL.private_key(1)
    dar.signature = sign_action_request(wrong_pk, dar.to_action_request_dict())

    return TreatyScenario(
        scenario_id="A-13-WRONG-KEY",
        description="DAR signed with wrong private key → SIGNATURE_INVALID",
        pre_populated_grants=[grant],
        delegated_actions=[dar],
        expected_delegation_outcome="REJECT",
        expected_delegation_rejection_code=TreatyRejectionCode.SIGNATURE_INVALID,
    )


def build_adv_no_treaty_citation(constitution: ConstitutionX2) -> TreatyScenario:
    """A-14: DAR without treaty: citation → AUTHORITY_CITATION_INVALID."""
    gid = _POOL.grantee_id(0)
    grant = _make_grant(constitution, gid, actions=["ReadLocal"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]})
    grant.grant_cycle = 0

    pk = _POOL.private_key(0)
    dar = DelegatedActionRequest(
        action_type="ReadLocal",
        fields={"path": "./artifacts/test"},
        grantee_identifier=gid,
        authority_citations=["constitution:abc#CL-SCOPE-SYSTEM"],  # no treaty:
        signature="",
        scope_type="FILE_PATH",
        scope_zone="ARTIFACTS_READ",
    )
    dar.signature = sign_action_request(pk, dar.to_action_request_dict())

    return TreatyScenario(
        scenario_id="A-14-NO-TREATY-CITATION",
        description="DAR without treaty: citation → AUTHORITY_CITATION_INVALID",
        pre_populated_grants=[grant],
        delegated_actions=[dar],
        expected_delegation_outcome="REJECT",
        expected_delegation_rejection_code=TreatyRejectionCode.AUTHORITY_CITATION_INVALID,
    )


def build_adv_scope_zone_outside_grant(constitution: ConstitutionX2) -> TreatyScenario:
    """A-15: DAR requests WORKSPACE_READ but grant only covers ARTIFACTS_READ."""
    gid = _POOL.grantee_id(0)
    grant = _make_grant(constitution, gid, actions=["ReadLocal"],
                        scope_constraints={"FILE_PATH": ["ARTIFACTS_READ"]})
    grant.grant_cycle = 0

    dar = _make_signed_dar(
        pool_index=0, action_type="ReadLocal",
        fields={"path": "./workspace/test"},
        grant=grant, scope_type="FILE_PATH", scope_zone="WORKSPACE_READ",
    )

    return TreatyScenario(
        scenario_id="A-15-SCOPE-OUTSIDE-GRANT",
        description="DAR scope_zone WORKSPACE_READ not in grant → REJECT",
        pre_populated_grants=[grant],
        delegated_actions=[dar],
        expected_delegation_outcome="REJECT",
        expected_delegation_rejection_code=TreatyRejectionCode.AUTHORITY_CITATION_INVALID,
    )


# ===================================================================
# Scenario collection
# ===================================================================

def build_all_lawful(constitution: ConstitutionX2) -> List[TreatyScenario]:
    return [
        build_lawful_read_delegation(constitution),
        build_lawful_notify_delegation(constitution),
        build_lawful_revocation(constitution),
    ]


def build_all_adversarial_grants(constitution: ConstitutionX2) -> List[TreatyScenario]:
    return [
        build_adv_fake_grantor(constitution),
        build_adv_no_treaty_permission(constitution),
        build_adv_bad_grantee_format(constitution),
        build_adv_scope_not_map(constitution),
        build_adv_invalid_scope_type(constitution),
        build_adv_wildcard_action(constitution),
        build_adv_unknown_action(constitution),
        build_adv_grantor_lacks_action(constitution),
        build_adv_scope_zone_invalid(constitution),
        build_adv_duration_exceeded(constitution),
        build_adv_nonrevocable_revocation(constitution),
    ]


def build_all_adversarial_delegation(constitution: ConstitutionX2) -> List[TreatyScenario]:
    return [
        build_adv_unsigned_dar(constitution),
        build_adv_wrong_key_dar(constitution),
        build_adv_no_treaty_citation(constitution),
        build_adv_scope_zone_outside_grant(constitution),
    ]


def build_all_scenarios(constitution: ConstitutionX2) -> List[TreatyScenario]:
    return (
        build_all_lawful(constitution)
        + build_all_adversarial_grants(constitution)
        + build_all_adversarial_delegation(constitution)
    )
