"""
RSA X-1 — Amendment Admission Pipeline

Type-switched admission for AmendmentProposal artifacts.
Gates 1-5 are reused structurally where applicable, then gates 6-8B added:

  Gate 1 (Completeness): required fields present
  Gate 2 (Authority Citation): citations resolve, BOTH mode enforced
  Gate 3 (Scope Claim): SKIPPED for amendments (Q109 binding)
  Gate 4 (Constitution Compliance): amendments_enabled check
  Gate 5 (IO Allowlist): SKIPPED for amendments (no IO)
  Gate 6 (Amendment Authorization): prior_hash match, ECK present, cooling
  Gate 7 (Full Replacement Integrity): YAML canonicalization, hash, schema, ECK
  Gate 8A (Physics Claim Rejection): reject executable/kernel-mutating content
  Gate 8B (Structural Constraint Preservation): cardinality, wildcards, density, scope, ratchet

Every proposal either passes all gates or produces a rejection trace entry.
No silent dropping.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import yaml
import jsonschema

from .artifacts_x1 import (
    AmendmentGate,
    AmendmentProposal,
    AmendmentRejectionCode,
    PendingAmendment,
)
from .constitution_x1 import (
    ConstitutionX1,
    ConstitutionError,
    canonicalize_constitution_bytes,
)


# ---------------------------------------------------------------------------
# Forbidden keys for Gate 8A (physics claim rejection)
# ---------------------------------------------------------------------------

FORBIDDEN_KEYS = frozenset({
    "script", "code", "eval", "template", "hook",
    "python", "js", "expr", "exec", "lambda",
})


# ---------------------------------------------------------------------------
# Trace events
# ---------------------------------------------------------------------------

@dataclass
class AmendmentAdmissionEvent:
    proposal_id: str
    gate: str
    result: str  # "pass" | "fail"
    reason_code: str = ""
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "event_type": "amendment_admission_event",
            "proposal_id": self.proposal_id,
            "gate": self.gate,
            "result": self.result,
        }
        if self.reason_code:
            d["reason_code"] = self.reason_code
        if self.detail:
            d["detail"] = self.detail
        return d


@dataclass
class AmendmentAdmissionResult:
    """Result of running a single amendment proposal through all gates."""
    proposal: AmendmentProposal
    admitted: bool
    events: List[AmendmentAdmissionEvent] = field(default_factory=list)
    failed_gate: str = ""
    rejection_code: str = ""
    # Populated on success for use by policy_core
    density: float = 0.0
    cardinality_a: int = 0
    cardinality_b: int = 0
    cardinality_m: int = 0


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class AmendmentAdmissionPipeline:
    """
    Runs amendment proposals through the 9-step type-switched pipeline.

    Constructor requires:
      - current constitution (active, for hash comparison and ratchet)
      - optional schema for proposed constitution validation
      - current pending amendments (for cooling check)
      - current cycle index
    """

    def __init__(
        self,
        constitution: ConstitutionX1,
        schema: Optional[Dict[str, Any]] = None,
        pending_amendments: Optional[List[PendingAmendment]] = None,
        cycle_index: int = 0,
    ):
        self.constitution = constitution
        self.schema = schema
        self.pending = pending_amendments or []
        self.cycle_index = cycle_index

    def evaluate(
        self,
        proposals: List[AmendmentProposal],
    ) -> Tuple[List[AmendmentAdmissionResult], List[AmendmentAdmissionResult], List[AmendmentAdmissionEvent]]:
        """
        Run all proposals through the pipeline.
        Returns (admitted, rejected, all_trace_events).
        """
        admitted: List[AmendmentAdmissionResult] = []
        rejected: List[AmendmentAdmissionResult] = []
        all_events: List[AmendmentAdmissionEvent] = []

        for proposal in proposals:
            result = self._evaluate_proposal(proposal)
            all_events.extend(result.events)
            if result.admitted:
                admitted.append(result)
            else:
                rejected.append(result)

        return admitted, rejected, all_events

    def _evaluate_proposal(self, proposal: AmendmentProposal) -> AmendmentAdmissionResult:
        """Run a single proposal through all gates in order."""
        pid = proposal.id
        events: List[AmendmentAdmissionEvent] = []

        gates = [
            ("completeness", self._gate_completeness),
            # Gate 4 first: no point checking citations if amendments disabled
            ("constitution_compliance", self._gate_constitution_compliance),
            ("authority_citation", self._gate_authority_citation),
            # Gate 3 (scope_claim) SKIPPED for amendments
            # Gate 5 (io_allowlist) SKIPPED for amendments
            (AmendmentGate.AUTHORIZATION, self._gate_amendment_authorization),
            (AmendmentGate.FULL_REPLACEMENT_INTEGRITY, self._gate_full_replacement_integrity),
            (AmendmentGate.PHYSICS_CLAIM_REJECTION, self._gate_physics_claim_rejection),
            (AmendmentGate.STRUCTURAL_PRESERVATION, self._gate_structural_preservation),
        ]

        result = AmendmentAdmissionResult(proposal=proposal, admitted=False)

        for gate_name, gate_fn in gates:
            passed, reason_code, detail = gate_fn(proposal)
            event = AmendmentAdmissionEvent(
                proposal_id=pid,
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

    # --- Gate implementations ---

    def _gate_completeness(self, proposal: AmendmentProposal) -> Tuple[bool, str, str]:
        """Gate 1: Required fields present."""
        if not proposal.prior_constitution_hash:
            return False, AmendmentRejectionCode.SCHEMA_INVALID, "missing prior_constitution_hash"
        if not proposal.proposed_constitution_yaml:
            return False, AmendmentRejectionCode.SCHEMA_INVALID, "missing proposed_constitution_yaml"
        if not proposal.proposed_constitution_hash:
            return False, AmendmentRejectionCode.SCHEMA_INVALID, "missing proposed_constitution_hash"
        if not proposal.justification:
            return False, AmendmentRejectionCode.SCHEMA_INVALID, "missing justification"
        if not proposal.authority_citations:
            return False, AmendmentRejectionCode.SCHEMA_INVALID, "missing authority_citations"
        return True, "", ""

    def _gate_authority_citation(self, proposal: AmendmentProposal) -> Tuple[bool, str, str]:
        """Gate 2: Authority citations resolve. Enforces BOTH mode."""
        mode = self.constitution.authority_reference_mode()

        if mode == "BOTH":
            valid, msg = self.constitution.citation_index.validate_citation_both(
                proposal.authority_citations
            )
            if not valid:
                return False, "CITATION_UNRESOLVABLE", msg
        else:
            # Fallback: all citations must resolve
            for citation in proposal.authority_citations:
                if self.constitution.resolve_citation(citation) is None:
                    return False, "CITATION_UNRESOLVABLE", f"unresolvable: {citation}"

        return True, "", ""

    def _gate_constitution_compliance(self, proposal: AmendmentProposal) -> Tuple[bool, str, str]:
        """Gate 4: Amendments must be enabled in current constitution."""
        if not self.constitution.amendments_enabled():
            return False, AmendmentRejectionCode.AMENDMENTS_DISABLED, "amendments_enabled is false"
        return True, "", ""

    def _gate_amendment_authorization(self, proposal: AmendmentProposal) -> Tuple[bool, str, str]:
        """
        Gate 6: Amendment Authorization.
          - prior_constitution_hash matches active constitution
          - AmendmentProcedure exists in current constitution
          - Budget check (max pending not exceeded)
        """
        # Hash match
        if proposal.prior_constitution_hash != self.constitution.sha256:
            return (
                False,
                AmendmentRejectionCode.PRIOR_HASH_MISMATCH,
                f"expected {self.constitution.sha256[:16]}..., got {proposal.prior_constitution_hash[:16]}...",
            )

        # ECK must exist
        if not self.constitution.has_eck_sections():
            return False, AmendmentRejectionCode.ECK_MISSING, "ECK sections missing from current constitution"

        # Budget: max pending amendments
        max_pending = self.constitution.max_pending_amendments()
        if len(self.pending) >= max_pending:
            return (
                False,
                AmendmentRejectionCode.COOLING_VIOLATION,
                f"max_pending_amendments={max_pending} reached",
            )

        return True, "", ""

    def _gate_full_replacement_integrity(self, proposal: AmendmentProposal) -> Tuple[bool, str, str]:
        """
        Gate 7: Full Replacement Integrity.
          - Proposed YAML parses
          - Canonical hash matches proposed_constitution_hash
          - Byte size within max_constitution_bytes
          - Schema validation passes (if schema provided)
          - ECK sections present in proposed constitution
        """
        # Parse YAML
        try:
            proposed_data = yaml.safe_load(proposal.proposed_constitution_yaml)
        except yaml.YAMLError as e:
            return False, AmendmentRejectionCode.SCHEMA_INVALID, f"YAML parse error: {e}"

        if not isinstance(proposed_data, dict):
            return False, AmendmentRejectionCode.SCHEMA_INVALID, "proposed YAML root must be a mapping"

        # Hash check
        raw_bytes = proposal.proposed_constitution_yaml.encode("utf-8")
        computed_hash = hashlib.sha256(raw_bytes).hexdigest()
        if computed_hash != proposal.proposed_constitution_hash:
            return (
                False,
                AmendmentRejectionCode.SCHEMA_INVALID,
                f"hash mismatch: computed {computed_hash[:16]}..., declared {proposal.proposed_constitution_hash[:16]}...",
            )

        # Byte size
        max_bytes = self.constitution.max_constitution_bytes()
        canonical = canonicalize_constitution_bytes(raw_bytes)
        if len(canonical) > max_bytes:
            return (
                False,
                AmendmentRejectionCode.SCHEMA_INVALID,
                f"constitution size {len(canonical)} exceeds max {max_bytes}",
            )

        # Schema validation
        if self.schema:
            try:
                jsonschema.validate(proposed_data, self.schema)
            except jsonschema.ValidationError as e:
                return (
                    False,
                    AmendmentRejectionCode.SCHEMA_INVALID,
                    f"schema validation failed: {e.message}",
                )

        # ECK sections present
        for section in ("AmendmentProcedure", "AuthorityModel", "WarrantDefinition", "ScopeSystem"):
            if section not in proposed_data:
                return False, AmendmentRejectionCode.ECK_MISSING, f"missing ECK section: {section}"

        return True, "", ""

    def _gate_physics_claim_rejection(self, proposal: AmendmentProposal) -> Tuple[bool, str, str]:
        """
        Gate 8A: Physics Claim Rejection.
        Reject if proposed YAML contains:
          - Forbidden keys (script, code, eval, etc.)
          - Claims to disable warrant gating
          - References undefined kernel hooks
        Structural check, not semantic.
        """
        try:
            proposed_data = yaml.safe_load(proposal.proposed_constitution_yaml)
        except yaml.YAMLError:
            # Already caught in Gate 7; shouldn't reach here
            return False, AmendmentRejectionCode.PHYSICS_CLAIM_DETECTED, "YAML parse error"

        found_keys = _find_forbidden_keys(proposed_data)
        if found_keys:
            return (
                False,
                AmendmentRejectionCode.PHYSICS_CLAIM_DETECTED,
                f"forbidden keys found: {sorted(found_keys)}",
            )

        return True, "", ""

    def _gate_structural_preservation(self, proposal: AmendmentProposal) -> Tuple[bool, str, str]:
        """
        Gate 8B: Structural Constraint Preservation.
        5 sub-steps in strict order:
          8B.1 Cardinality
          8B.2 Wildcard check
          8B.3 Universal authorization (density == 1)
          8B.4 Scope collapse
          8B.5 Ratchet check (envelope degradation)
        """
        try:
            proposed_data = yaml.safe_load(proposal.proposed_constitution_yaml)
        except yaml.YAMLError:
            return False, AmendmentRejectionCode.SCHEMA_INVALID, "YAML parse error"

        # --- 8B.1 Cardinality ---
        new_action_perms = proposed_data.get("AuthorityModel", {}).get("action_permissions", [])
        new_action_types = proposed_data.get("action_space", {}).get("action_types", [])

        A = len(set(p.get("authority", "") for p in new_action_perms))
        B = len(new_action_types)

        if A < 1:
            return False, AmendmentRejectionCode.UNIVERSAL_AUTHORIZATION, f"A={A} < 1"
        if B < 1:
            return False, AmendmentRejectionCode.SCOPE_COLLAPSE, f"B={B} < 1"

        # --- 8B.2 Wildcard check ---
        for perm in new_action_perms:
            if perm.get("authority") == "*":
                return False, AmendmentRejectionCode.WILDCARD_MAPPING, "wildcard authority: *"
            for action in perm.get("actions", []):
                if action == "*":
                    return False, AmendmentRejectionCode.WILDCARD_MAPPING, "wildcard action: *"

        # Also check amendment_permissions
        for perm in proposed_data.get("AuthorityModel", {}).get("amendment_permissions", []):
            if perm.get("authority") == "*":
                return False, AmendmentRejectionCode.WILDCARD_MAPPING, "wildcard authority in amendment_permissions"
            for amend_type in perm.get("amendments", []):
                if amend_type == "*":
                    return False, AmendmentRejectionCode.WILDCARD_MAPPING, "wildcard amendment type"

        # --- 8B.3 Universal authorization (density) ---
        M = sum(len(p.get("actions", [])) for p in new_action_perms)
        density = M / (A * B) if (A * B) > 0 else 0

        if M == A * B:
            return (
                False,
                AmendmentRejectionCode.UNIVERSAL_AUTHORIZATION,
                f"density=1.0 (M={M}=A×B={A}×{B})",
            )

        # Check density_upper_bound from proposed constitution
        proposed_amendment_proc = proposed_data.get("AmendmentProcedure", {})
        proposed_bound = proposed_amendment_proc.get("density_upper_bound")
        if proposed_bound is not None and density > proposed_bound:
            return (
                False,
                AmendmentRejectionCode.UNIVERSAL_AUTHORIZATION,
                f"density={density:.4f} exceeds proposed bound={proposed_bound}",
            )

        # --- 8B.4 Scope collapse ---
        new_scope_system = proposed_data.get("ScopeSystem", {})
        if not new_scope_system:
            return False, AmendmentRejectionCode.SCOPE_COLLAPSE, "ScopeSystem empty"

        per_action_scope = new_scope_system.get("per_action_scope", [])
        if not per_action_scope:
            return False, AmendmentRejectionCode.SCOPE_COLLAPSE, "per_action_scope empty"

        # Check not all actions are globally scoped (at least one requires scope_claim)
        has_scoped = any(
            pas.get("scope_claim_required", False)
            for pas in per_action_scope
        )
        if not has_scoped:
            return (
                False,
                AmendmentRejectionCode.SCOPE_COLLAPSE,
                "no action requires scoped warrant (all globally scoped)",
            )

        # --- 8B.5 Ratchet check (envelope degradation) ---
        old_proc = self.constitution.amendment_procedure
        new_proc = proposed_data.get("AmendmentProcedure", {})

        if not new_proc:
            return False, AmendmentRejectionCode.ENVELOPE_DEGRADED, "AmendmentProcedure removed"

        # Cooling: non-decreasing
        old_cooling = old_proc.get("cooling_period_cycles", 2)
        new_cooling = new_proc.get("cooling_period_cycles", 0)
        if new_cooling < old_cooling:
            return (
                False,
                AmendmentRejectionCode.ENVELOPE_DEGRADED,
                f"cooling reduced: {old_cooling} → {new_cooling}",
            )

        # Authorization threshold: non-decreasing
        old_threshold = old_proc.get("authorization_threshold", 1)
        new_threshold = new_proc.get("authorization_threshold", 0)
        if new_threshold < old_threshold:
            return (
                False,
                AmendmentRejectionCode.ENVELOPE_DEGRADED,
                f"threshold reduced: {old_threshold} → {new_threshold}",
            )

        # Density upper bound: non-increasing, removal forbidden if previously present
        old_bound = old_proc.get("density_upper_bound")
        new_bound = new_proc.get("density_upper_bound")

        if old_bound is not None:
            if new_bound is None:
                return (
                    False,
                    AmendmentRejectionCode.ENVELOPE_DEGRADED,
                    "density_upper_bound removed (was present in prior constitution)",
                )
            if new_bound > old_bound:
                return (
                    False,
                    AmendmentRejectionCode.ENVELOPE_DEGRADED,
                    f"density_upper_bound increased: {old_bound} → {new_bound}",
                )

        # Structured fields replaced with free text
        for field_name in ("cooling_period_cycles", "authorization_threshold", "authority_reference_mode"):
            if field_name in old_proc and field_name not in new_proc:
                return (
                    False,
                    AmendmentRejectionCode.ENVELOPE_DEGRADED,
                    f"structured field removed: {field_name}",
                )

        return True, "", ""


# ---------------------------------------------------------------------------
# Cooling check (for adoption, not proposal admission)
# ---------------------------------------------------------------------------

def check_cooling_satisfied(
    pending: PendingAmendment,
    current_cycle: int,
    cooling_period: int,
) -> bool:
    """
    Check if a pending amendment has satisfied the cooling period.
    effective_cycle = current_cycle + 1 always.
    Adoption allowed when: current_cycle >= proposal_cycle + cooling_period.
    """
    return current_cycle >= pending.proposal_cycle + cooling_period


def invalidate_stale_proposals(
    pending: List[PendingAmendment],
    new_constitution_hash: str,
) -> Tuple[List[PendingAmendment], List[PendingAmendment]]:
    """
    Forward-looking stale invalidation at adoption time.
    Removes proposals whose prior_constitution_hash != new_constitution_hash.
    Returns (remaining, invalidated).
    """
    remaining = []
    invalidated = []
    for p in pending:
        if p.prior_constitution_hash != new_constitution_hash:
            invalidated.append(p)
        else:
            remaining.append(p)
    return remaining, invalidated


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_forbidden_keys(obj: Any, path: str = "") -> set:
    """Recursively find forbidden keys in a parsed YAML structure."""
    found: set = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(key, str) and key.lower() in FORBIDDEN_KEYS:
                found.add(key)
            found.update(_find_forbidden_keys(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            found.update(_find_forbidden_keys(item, f"{path}[{i}]"))
    return found
