"""
RSA X-2 — Treaty Admission Pipeline

Type-switched admission for TreatyGrant and TreatyRevocation artifacts.
Gates:

  Gate 6T (Treaty Authorization): grantor is constitutional authority,
         treaty_permissions authorize treaty type, citations valid.
  Gate 7T (Schema Validity): fields present, canonical hash, type checks.
         scope_constraints must be map {scope_type: [zone_label...]}.
  Gate 8C (Delegation Preservation – TreatyGrant only):
         8C.1 closed action set, 8C.2 wildcard, 8C.2b grantor holds perms,
         8C.3 scope monotonicity (per scope_type subset check),
         8C.4 coverage monotonicity,
         8C.5 delegation depth, 8C.6 acyclicity, 8C.7 density margin,
         8C.8 duration validity, 8C.9 citation validity.
  Gate 8R (Revocation Validity – TreatyRevocation only):
         grant exists, grant is revocable, citations valid.

Density rejects d==1.0 per CL-EFFECTIVE-DENSITY-DEFINITION.
Notify zone admission enforced per per_action_scope.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .artifacts_x2 import (
    ActiveTreatySet,
    TreatyAdmissionEvent,
    TreatyAdmissionResult,
    TreatyGate,
    TreatyGrant,
    TreatyRejectionCode,
    TreatyRevocation,
    _compute_effective_density,
    canonicalize_treaty_dict,
    treaty_canonical_hash,
    validate_grantee_identifier,
)
from .constitution_x2 import ConstitutionX2


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class TreatyAdmissionPipeline:
    """
    Runs treaty artifacts (TreatyGrant or TreatyRevocation) through the
    X-2 admission pipeline.

    Constructor requires:
      - constitution: active ConstitutionX2
      - active_treaty_set: current ActiveTreatySet
      - cycle_index: current cycle number
    """

    def __init__(
        self,
        constitution: ConstitutionX2,
        active_treaty_set: ActiveTreatySet,
        cycle_index: int = 0,
    ):
        self.constitution = constitution
        self.treaty_set = active_treaty_set
        self.cycle_index = cycle_index

    # ---------------------------------------------------------------
    # Public evaluate
    # ---------------------------------------------------------------

    def evaluate_grants(
        self,
        grants: List[TreatyGrant],
    ) -> Tuple[List[TreatyAdmissionResult], List[TreatyAdmissionResult], List[TreatyAdmissionEvent]]:
        """
        Run all TreatyGrant candidates through gates 6T → 7T → 8C.
        Returns (admitted, rejected, all_trace_events).
        """
        admitted: List[TreatyAdmissionResult] = []
        rejected: List[TreatyAdmissionResult] = []
        all_events: List[TreatyAdmissionEvent] = []

        for grant in grants:
            result = self._evaluate_grant(grant)
            all_events.extend(result.events)
            if result.admitted:
                admitted.append(result)
            else:
                rejected.append(result)

        return admitted, rejected, all_events

    def evaluate_revocations(
        self,
        revocations: List[TreatyRevocation],
    ) -> Tuple[List[TreatyAdmissionResult], List[TreatyAdmissionResult], List[TreatyAdmissionEvent]]:
        """
        Run all TreatyRevocation candidates through gates 6T → 7T → 8R.
        Returns (admitted, rejected, all_trace_events).
        """
        admitted: List[TreatyAdmissionResult] = []
        rejected: List[TreatyAdmissionResult] = []
        all_events: List[TreatyAdmissionEvent] = []

        for rev in revocations:
            result = self._evaluate_revocation(rev)
            all_events.extend(result.events)
            if result.admitted:
                admitted.append(result)
            else:
                rejected.append(result)

        return admitted, rejected, all_events

    # ---------------------------------------------------------------
    # TreatyGrant evaluation
    # ---------------------------------------------------------------

    def _evaluate_grant(self, grant: TreatyGrant) -> TreatyAdmissionResult:
        aid = grant.id
        atype = "TreatyGrant"
        events: List[TreatyAdmissionEvent] = []

        gates = [
            (TreatyGate.AUTHORIZATION, self._gate_6t_grant),
            (TreatyGate.SCHEMA_VALIDITY, self._gate_7t_grant),
            (TreatyGate.DELEGATION_PRESERVATION, self._gate_8c),
        ]

        result = TreatyAdmissionResult(
            artifact_id=aid,
            artifact_type=atype,
            admitted=False,
        )

        for gate_name, gate_fn in gates:
            passed, reason_code, detail = gate_fn(grant)
            event = TreatyAdmissionEvent(
                artifact_id=aid,
                artifact_type=atype,
                gate=gate_name,
                result="pass" if passed else "fail",
                reason_code=reason_code,
                detail=detail,
            )
            events.append(event)

            if not passed:
                result.events = events
                result.failed_gate = gate_name
                result.rejection_code = reason_code
                return result

        # Compute density on success
        active = self.treaty_set.active_grants(self.cycle_index)
        active_plus = active + [grant]
        a_eff, b, m_eff, density = self.constitution.compute_effective_density(active_plus)

        result.admitted = True
        result.events = events
        result.effective_density = density
        result.a_eff = a_eff
        result.m_eff = m_eff
        return result

    # ---------------------------------------------------------------
    # TreatyRevocation evaluation
    # ---------------------------------------------------------------

    def _evaluate_revocation(self, rev: TreatyRevocation) -> TreatyAdmissionResult:
        aid = rev.id
        atype = "TreatyRevocation"
        events: List[TreatyAdmissionEvent] = []

        gates = [
            (TreatyGate.AUTHORIZATION, self._gate_6t_revocation),
            (TreatyGate.SCHEMA_VALIDITY, self._gate_7t_revocation),
            (TreatyGate.REVOCATION_VALIDITY, self._gate_8r),
        ]

        result = TreatyAdmissionResult(
            artifact_id=aid,
            artifact_type=atype,
            admitted=False,
        )

        for gate_name, gate_fn in gates:
            passed, reason_code, detail = gate_fn(rev)
            event = TreatyAdmissionEvent(
                artifact_id=aid,
                artifact_type=atype,
                gate=gate_name,
                result="pass" if passed else "fail",
                reason_code=reason_code,
                detail=detail,
            )
            events.append(event)

            if not passed:
                result.events = events
                result.failed_gate = gate_name
                result.rejection_code = reason_code
                return result

        result.admitted = True
        result.events = events
        return result

    # ===================================================================
    # Gate 6T — Treaty Authorization
    # ===================================================================

    def _gate_6t_grant(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """
        Gate 6T for TreatyGrant:
        - Constitution loaded (has X-2 sections)
        - Grantor is a constitutional authority
        - treaty_permissions authorizes grantor for TreatyGrant
        - authority_citations are valid
        Per CL-TREATY-AUTHORIZATION-RULE: consult treaty_permissions ONLY.
        """
        if not self.constitution.has_x2_sections():
            return False, TreatyRejectionCode.TREATY_PERMISSION_MISSING, "constitution lacks X-2 sections"

        if not self.constitution.is_constitutional_authority(grant.grantor_authority_id):
            return (
                False,
                TreatyRejectionCode.GRANTOR_NOT_CONSTITUTIONAL,
                f"grantor {grant.grantor_authority_id} not in constitutional authorities",
            )

        if not self.constitution.authority_can_delegate_type(
            grant.grantor_authority_id, "TreatyGrant"
        ):
            return (
                False,
                TreatyRejectionCode.TREATY_PERMISSION_MISSING,
                f"grantor {grant.grantor_authority_id} lacks TreatyGrant permission",
            )

        for citation in grant.authority_citations:
            if self.constitution.resolve_citation(citation) is None:
                return (
                    False,
                    TreatyRejectionCode.AUTHORITY_CITATION_INVALID,
                    f"unresolvable citation: {citation}",
                )

        return True, "", ""

    def _gate_6t_revocation(self, rev: TreatyRevocation) -> Tuple[bool, str, str]:
        """
        Gate 6T for TreatyRevocation:
        - Constitution loaded (has X-2 sections)
        - treaty_permissions authorizes TreatyRevocation
        - authority_citations valid
        """
        if not self.constitution.has_x2_sections():
            return False, TreatyRejectionCode.TREATY_PERMISSION_MISSING, "constitution lacks X-2 sections"

        treaty_perms = self.constitution.get_treaty_permissions()
        has_revocation_perm = any(
            "TreatyRevocation" in perm.get("treaties", [])
            for perm in treaty_perms
        )
        if not has_revocation_perm:
            return (
                False,
                TreatyRejectionCode.TREATY_PERMISSION_MISSING,
                "no treaty_permission authorizes TreatyRevocation",
            )

        for citation in rev.authority_citations:
            if self.constitution.resolve_citation(citation) is None:
                return (
                    False,
                    TreatyRejectionCode.AUTHORITY_CITATION_INVALID,
                    f"unresolvable citation: {citation}",
                )

        return True, "", ""

    # ===================================================================
    # Gate 7T — Schema Validity
    # ===================================================================

    def _gate_7t_grant(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """
        Gate 7T for TreatyGrant:
        - Required fields present and well-typed
        - grantee_identifier matches ed25519:<hex64>
        - scope_constraints is a dict (map)
        """
        # Required string fields
        if not grant.grantor_authority_id:
            return False, TreatyRejectionCode.SCHEMA_INVALID, "missing grantor_authority_id"
        if not grant.grantee_identifier:
            return False, TreatyRejectionCode.SCHEMA_INVALID, "missing grantee_identifier"
        if not grant.justification:
            return False, TreatyRejectionCode.SCHEMA_INVALID, "missing justification"
        if not grant.authority_citations:
            return False, TreatyRejectionCode.SCHEMA_INVALID, "missing authority_citations"
        if not grant.granted_actions:
            return False, TreatyRejectionCode.SCHEMA_INVALID, "missing granted_actions"
        if not grant.scope_constraints:
            return False, TreatyRejectionCode.SCHEMA_INVALID, "missing scope_constraints"

        # grantee_identifier format
        if not validate_grantee_identifier(grant.grantee_identifier):
            return (
                False,
                TreatyRejectionCode.INVALID_FIELD,
                f"grantee_identifier format invalid: {grant.grantee_identifier}",
            )

        # Type checks
        if not isinstance(grant.duration_cycles, int):
            return False, TreatyRejectionCode.INVALID_FIELD, "duration_cycles must be integer"
        if not isinstance(grant.revocable, bool):
            return False, TreatyRejectionCode.INVALID_FIELD, "revocable must be boolean"
        if not isinstance(grant.granted_actions, list):
            return False, TreatyRejectionCode.INVALID_FIELD, "granted_actions must be list"

        # scope_constraints must be a dict (map {scope_type: [zones]})
        if not isinstance(grant.scope_constraints, dict):
            return (
                False,
                TreatyRejectionCode.INVALID_FIELD,
                "scope_constraints must be a map {scope_type: [zone_label...]}",
            )

        # Validate scope_constraints structure: each key is scope_type, each value is list of strings
        valid_scope_types = set(self.constitution.get_zone_labels().keys())
        for scope_type, zones in grant.scope_constraints.items():
            if scope_type not in valid_scope_types:
                return (
                    False,
                    TreatyRejectionCode.INVALID_FIELD,
                    f"scope_constraints key '{scope_type}' not a valid scope_type",
                )
            if not isinstance(zones, list):
                return (
                    False,
                    TreatyRejectionCode.INVALID_FIELD,
                    f"scope_constraints['{scope_type}'] must be a list of zone labels",
                )
            if not zones:
                return (
                    False,
                    TreatyRejectionCode.INVALID_FIELD,
                    f"scope_constraints['{scope_type}'] must be non-empty",
                )
            for z in zones:
                if not isinstance(z, str):
                    return (
                        False,
                        TreatyRejectionCode.INVALID_FIELD,
                        f"scope_constraints['{scope_type}'] contains non-string: {z}",
                    )

        return True, "", ""

    def _gate_7t_revocation(self, rev: TreatyRevocation) -> Tuple[bool, str, str]:
        """Gate 7T for TreatyRevocation: required fields present."""
        if not rev.grant_id:
            return False, TreatyRejectionCode.SCHEMA_INVALID, "missing grant_id"
        if not rev.authority_citations:
            return False, TreatyRejectionCode.SCHEMA_INVALID, "missing authority_citations"
        if not rev.justification:
            return False, TreatyRejectionCode.SCHEMA_INVALID, "missing justification"

        return True, "", ""

    # ===================================================================
    # Gate 8C — Delegation Preservation (TreatyGrant)
    # ===================================================================

    def _gate_8c(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """
        Gate 8C: Delegation Preservation Checks.
        Sub-gates in strict order:
          8C.1 Closed action set membership
          8C.2 Wildcard prohibition
          8C.2b Grantor holds permission for each granted action
          8C.3 Scope monotonicity (per scope_type subset of ScopeEnumerations)
          8C.4 Coverage monotonicity
          8C.5 Delegation depth (no chains)
          8C.6 Acyclicity
          8C.7 Density margin (reject d==1.0 or d > bound)
          8C.8 Duration validity
          8C.9 Citation validity
        """
        checks = [
            self._8c1_closed_action_set,
            self._8c2_wildcard_prohibition,
            self._8c2b_grantor_holds_permission,
            self._8c3_scope_monotonicity,
            self._8c4_coverage_monotonicity,
            self._8c5_delegation_depth,
            self._8c6_acyclicity,
            self._8c7_density_margin,
            self._8c8_duration_validity,
            self._8c9_citation_validity,
        ]

        for check_fn in checks:
            passed, code, detail = check_fn(grant)
            if not passed:
                return False, code, detail

        return True, "", ""

    # --- 8C sub-gates ---

    def _8c1_closed_action_set(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """8C.1: granted_actions ⊆ closed action set."""
        closed_set = set(self.constitution.get_closed_action_set())
        for action in grant.granted_actions:
            if action not in closed_set:
                return (
                    False,
                    TreatyRejectionCode.INVALID_FIELD,
                    f"action '{action}' not in closed action set",
                )
        return True, "", ""

    def _8c2_wildcard_prohibition(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """8C.2: No wildcard mapping in any field."""
        for action in grant.granted_actions:
            if "*" in action:
                return (
                    False,
                    TreatyRejectionCode.WILDCARD_MAPPING,
                    f"wildcard in granted_actions: '{action}'",
                )
        for scope_type, zones in grant.scope_constraints.items():
            if "*" in scope_type:
                return (
                    False,
                    TreatyRejectionCode.WILDCARD_MAPPING,
                    f"wildcard in scope_constraints key: '{scope_type}'",
                )
            for zone in zones:
                if "*" in zone:
                    return (
                        False,
                        TreatyRejectionCode.WILDCARD_MAPPING,
                        f"wildcard in scope_constraints zone: '{zone}'",
                    )
        if "*" in grant.grantor_authority_id:
            return (
                False,
                TreatyRejectionCode.WILDCARD_MAPPING,
                "wildcard grantor_authority_id",
            )
        if "*" in grant.grantee_identifier:
            return (
                False,
                TreatyRejectionCode.WILDCARD_MAPPING,
                "wildcard grantee_identifier",
            )
        return True, "", ""

    def _8c2b_grantor_holds_permission(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """8C.2b: Grantor authority must hold permission for each granted action."""
        for action in grant.granted_actions:
            if not self.constitution.authority_holds_action(grant.grantor_authority_id, action):
                return (
                    False,
                    TreatyRejectionCode.GRANTOR_LACKS_PERMISSION,
                    f"grantor {grant.grantor_authority_id} lacks permission for action '{action}'",
                )
        return True, "", ""

    def _8c3_scope_monotonicity(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """
        8C.3: Scope(grant) ⊆ Scope(constitution).
        Per scope_type, zone labels must be subset of ScopeEnumerations zones.
        """
        zone_labels = self.constitution.get_zone_labels()
        for scope_type, zones in grant.scope_constraints.items():
            constitutional_zones = set(zone_labels.get(scope_type, []))
            for zone in zones:
                if zone not in constitutional_zones:
                    return (
                        False,
                        TreatyRejectionCode.SCOPE_COLLAPSE,
                        f"zone '{zone}' not in ScopeEnumerations for scope_type '{scope_type}'",
                    )
        return True, "", ""

    def _8c4_coverage_monotonicity(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """
        8C.4: Grant cannot introduce (action, scope) pairs outside grantor's authority.
        Enforced by 8C.2b (actions subset) and 8C.3 (scopes subset).
        Additional: verify grant scope_types align with granted actions' valid_scope_types.
        """
        for action in grant.granted_actions:
            valid_scope_types = set(self.constitution.get_valid_scope_types(action))
            for scope_type in grant.scope_constraints.keys():
                if scope_type not in valid_scope_types:
                    return (
                        False,
                        TreatyRejectionCode.COVERAGE_INFLATION,
                        f"scope_type '{scope_type}' not valid for action '{action}'",
                    )
        return True, "", ""

    def _8c5_delegation_depth(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """
        8C.5: Delegation depth ≤ 1 from constitutional root.
        Only constitutional authorities may issue TreatyGrant.
        Reject if grantor is itself a grantee (derived from treaty).
        """
        max_depth = self.constitution.delegation_depth_limit()

        if self.treaty_set.is_grantee(grant.grantor_authority_id, self.cycle_index):
            return (
                False,
                TreatyRejectionCode.EXCESSIVE_DEPTH,
                f"grantor {grant.grantor_authority_id} is a treaty grantee (depth > {max_depth})",
            )

        return True, "", ""

    def _8c6_acyclicity(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """8C.6: Adding this grant must not create a cycle in the delegation graph."""
        if self.treaty_set.would_create_cycle(grant, self.cycle_index):
            return (
                False,
                TreatyRejectionCode.DELEGATION_CYCLE,
                f"cycle detected: {grant.grantor_authority_id} → {grant.grantee_identifier}",
            )
        return True, "", ""

    def _8c7_density_margin(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """
        8C.7: Effective density after adding grant.
        Reject if A_eff*B==0, d_eff==1.0, or d_eff > density_upper_bound.
        """
        active = self.treaty_set.active_grants(self.cycle_index)
        active_plus = active + [grant]

        a_eff, b, m_eff, density = self.constitution.compute_effective_density(active_plus)

        if a_eff == 0 or b == 0:
            return (
                False,
                TreatyRejectionCode.DENSITY_MARGIN_VIOLATION,
                f"A_eff*B == 0 (A_eff={a_eff}, B={b})",
            )

        if density == 1.0:
            return (
                False,
                TreatyRejectionCode.DENSITY_MARGIN_VIOLATION,
                f"effective density == 1.0 (forbidden)",
            )

        bound = self.constitution.density_upper_bound()
        if bound is not None and density > bound:
            return (
                False,
                TreatyRejectionCode.DENSITY_MARGIN_VIOLATION,
                f"effective density {density:.4f} exceeds bound {bound}",
            )

        return True, "", ""

    def _8c8_duration_validity(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """8C.8: duration_cycles finite integer >= 1, <= max_treaty_duration_cycles."""
        if not isinstance(grant.duration_cycles, int):
            return False, TreatyRejectionCode.INVALID_FIELD, "duration_cycles not integer"

        if grant.duration_cycles < 1:
            return (
                False,
                TreatyRejectionCode.INVALID_FIELD,
                f"duration_cycles={grant.duration_cycles} < 1",
            )

        max_duration = self.constitution.max_treaty_duration_cycles()
        if grant.duration_cycles > max_duration:
            return (
                False,
                TreatyRejectionCode.INVALID_FIELD,
                f"duration_cycles={grant.duration_cycles} exceeds max {max_duration}",
            )

        return True, "", ""

    def _8c9_citation_validity(self, grant: TreatyGrant) -> Tuple[bool, str, str]:
        """8C.9: Explicit authority citations valid (re-check; complements 6T)."""
        for citation in grant.authority_citations:
            if self.constitution.resolve_citation(citation) is None:
                return (
                    False,
                    TreatyRejectionCode.AUTHORITY_CITATION_INVALID,
                    f"unresolvable citation: {citation}",
                )
        return True, "", ""

    # ===================================================================
    # Gate 8R — Revocation Validity
    # ===================================================================

    def _gate_8r(self, rev: TreatyRevocation) -> Tuple[bool, str, str]:
        """
        Gate 8R: Revocation Preservation Checks.
        - Grant exists
        - Grant is revocable
        - Not already revoked
        """
        grant = self.treaty_set.find_grant(rev.grant_id)
        if grant is None:
            return (
                False,
                TreatyRejectionCode.GRANT_NOT_FOUND,
                f"grant_id {rev.grant_id} not found in treaty set",
            )

        if not grant.revocable:
            return (
                False,
                TreatyRejectionCode.NONREVOCABLE_GRANT,
                f"grant {rev.grant_id} is not revocable",
            )

        if rev.grant_id in self.treaty_set.revoked_grant_ids:
            return (
                False,
                TreatyRejectionCode.GRANT_NOT_FOUND,
                f"grant {rev.grant_id} already revoked",
            )

        return True, "", ""
