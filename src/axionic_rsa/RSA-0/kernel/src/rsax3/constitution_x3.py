"""
RSA X-3 — Effective Constitution Frame

Merges constitution v0.3 with the X-3 overlay to produce an
EffectiveConstitutionFrame. The overlay adds succession, ratification,
and suspension clauses without modifying the base constitution.

The overlay is frozen per session and cited via overlay:<hash>#<id>.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional

from ..rsax2.constitution_x2 import CitationIndexX2, ConstitutionX2
from ..artifacts import canonical_json_bytes


class EffectiveConstitutionFrame:
    """Wraps ConstitutionX2 + X-3 overlay for unified access.

    Adds:
    - Succession-related clause lookups
    - Overlay citation resolution (overlay:<hash>#<id>)
    - is_succession_enabled(), is_ratification_required(), etc.
    """

    def __init__(
        self,
        constitution: ConstitutionX2,
        overlay: Dict[str, Any],
    ):
        self._constitution = constitution
        self._overlay = overlay
        self._clauses = overlay.get("clauses", {})
        self._overlay_hash = hashlib.sha256(
            canonical_json_bytes(overlay)
        ).hexdigest()

    @property
    def overlay_hash(self) -> str:
        return self._overlay_hash

    # -----------------------------------------------------------------------
    # Delegation to base constitution
    # -----------------------------------------------------------------------

    def density_upper_bound(self) -> float:
        return self._constitution.density_upper_bound()

    def cooling_period_cycles(self) -> int:
        return self._constitution.cooling_period_cycles()

    def get_action_permissions(self) -> List[Dict[str, Any]]:
        return self._constitution.get_action_permissions()

    def get_action_types(self) -> List[str]:
        return self._constitution.get_action_types()

    def get_closed_action_set(self) -> List[str]:
        return self._constitution.get_closed_action_set()

    def get_all_zone_labels(self) -> set:
        return self._constitution.get_all_zone_labels()

    def make_citation(self, node_id: str) -> str:
        return self._constitution.make_citation(node_id)

    def resolve_citation(self, citation: str) -> Optional[Any]:
        # Try overlay namespace first
        if citation.startswith("overlay:"):
            return self._resolve_overlay_citation(citation)
        return self._constitution.resolve_citation(citation)

    def get_origin_rank(self) -> Dict[str, int]:
        return self._constitution.get_origin_rank()

    def get_action_warrant_mapping(self) -> Dict[str, Any]:
        return self._constitution.get_action_warrant_mapping()

    def get_warrant_scope_type(self, action_type: str) -> Optional[str]:
        return self._constitution.get_warrant_scope_type(action_type)

    def max_total_tokens_per_cycle(self) -> int:
        return self._constitution.max_total_tokens_per_cycle()

    def get_constitutional_authorities(self) -> List[str]:
        return self._constitution.get_constitutional_authorities()

    # For treaty admission pipeline compatibility
    def get_treaty_permissions(self):
        return self._constitution.get_treaty_permissions()

    def max_treaty_duration_cycles(self) -> int:
        return self._constitution.max_treaty_duration_cycles()

    def delegation_depth_limit(self) -> int:
        return self._constitution.delegation_depth_limit()

    def delegation_acyclicity_required(self) -> bool:
        return self._constitution.delegation_acyclicity_required()

    def treaty_schema_path(self) -> str:
        return self._constitution.treaty_schema_path()

    def treaty_schema_sha256(self) -> str:
        return self._constitution.treaty_schema_sha256()

    def get_per_action_scope(self) -> Dict[str, Any]:
        return self._constitution.get_per_action_scope()

    def get_action_scope_rule(self, action_type: str) -> Optional[Dict[str, Any]]:
        return self._constitution.get_action_scope_rule(action_type)

    def get_valid_scope_types(self, action_type: str) -> List[str]:
        return self._constitution.get_valid_scope_types(action_type)

    def get_permitted_zones(self, action_type: str) -> Optional[List[str]]:
        return self._constitution.get_permitted_zones(action_type)

    def authority_can_delegate(self, authority_id: str) -> bool:
        return self._constitution.authority_can_delegate(authority_id)

    def authority_can_delegate_type(self, authority_id: str, action_type: str) -> bool:
        return self._constitution.authority_can_delegate_type(authority_id, action_type)

    def is_constitutional_authority(self, authority_id: str) -> bool:
        return self._constitution.is_constitutional_authority(authority_id)

    def authority_holds_action(self, authority_id: str, action_type: str) -> bool:
        return self._constitution.authority_holds_action(authority_id, action_type)

    def has_x2_sections(self) -> bool:
        return self._constitution.has_x2_sections()

    # Additional X-1 delegations needed by _action_path / AdmissionPipeline
    def make_authority_citation(self, auth_id: str) -> str:
        return self._constitution.make_authority_citation(auth_id)

    def max_amendment_candidates_per_cycle(self) -> int:
        return self._constitution.max_amendment_candidates_per_cycle()

    def get_read_paths(self) -> List[str]:
        return self._constitution.get_read_paths()

    def get_write_paths(self) -> List[str]:
        return self._constitution.get_write_paths()

    def get_action_type_def(self, action_type: str):
        return self._constitution.get_action_type_def(action_type)

    @property
    def citation_index(self):
        return self._constitution.citation_index

    def authority_reference_mode(self) -> str:
        return self._constitution.authority_reference_mode()

    def amendments_enabled(self) -> bool:
        return self._constitution.amendments_enabled()

    def has_eck_sections(self) -> bool:
        return self._constitution.has_eck_sections()

    def max_pending_amendments(self) -> int:
        return self._constitution.max_pending_amendments()

    def max_constitution_bytes(self) -> int:
        return self._constitution.max_constitution_bytes()

    @property
    def amendment_procedure(self):
        return self._constitution.amendment_procedure

    # Additional X-2 delegations needed by treaty pipeline
    def get_zones_for_scope_type(self, scope_type: str) -> List[str]:
        return self._constitution.get_zones_for_scope_type(scope_type)

    def get_zone_labels(self) -> set:
        return self._constitution.get_zone_labels()

    def compute_effective_density(self, active_grants) -> float:
        return self._constitution.compute_effective_density(active_grants)

    @property
    def sha256(self) -> str:
        return self._constitution.sha256

    @property
    def hash(self) -> str:
        """Alias for sha256 for backward compat."""
        return self._constitution.sha256

    @property
    def version(self) -> str:
        return self._constitution.version

    @property
    def data(self) -> Dict[str, Any]:
        return self._constitution.data

    # -----------------------------------------------------------------------
    # X-3 overlay accessors
    # -----------------------------------------------------------------------

    def is_succession_enabled(self) -> bool:
        cl = self._clauses.get("CL-SUCCESSION-ENABLED", {})
        return cl.get("enabled", False)

    def succession_per_cycle_limit(self) -> int:
        cl = self._clauses.get("CL-SUCCESSION-PER-CYCLE-LIMIT", {})
        return cl.get("max_per_cycle", 1)

    def is_self_succession_permitted(self) -> bool:
        cl = self._clauses.get("CL-SUCCESSION-SELF-PERMITTED", {})
        return cl.get("permitted", True)

    def is_boundary_signature_required(self) -> bool:
        cl = self._clauses.get("CL-BOUNDARY-SIGNATURE-REQUIRED", {})
        return cl.get("required", True)

    def is_treaty_suspension_on_succession(self) -> bool:
        cl = self._clauses.get("CL-TREATY-SUSPENSION-ON-SUCCESSION", {})
        return cl.get("enabled", True)

    def is_treaty_ratification_required(self) -> bool:
        cl = self._clauses.get("CL-TREATY-RATIFICATION-REQUIRED", {})
        return cl.get("enabled", True)

    def is_prior_key_zero_authority(self) -> bool:
        cl = self._clauses.get("CL-PRIOR-KEY-ZERO-AUTHORITY", {})
        return cl.get("enabled", True)

    def is_lineage_no_fork(self) -> bool:
        cl = self._clauses.get("CL-LINEAGE-NO-FORK", {})
        return cl.get("enabled", True)

    def is_suspension_blocks_grants(self) -> bool:
        cl = self._clauses.get("CL-SUSPENSION-BLOCKS-GRANTS", {})
        return cl.get("enabled", True)

    def suspension_blocks_grants_code(self) -> str:
        cl = self._clauses.get("CL-SUSPENSION-BLOCKS-GRANTS", {})
        return cl.get("rejection_code", "SUSPENSION_UNRESOLVED")

    # -----------------------------------------------------------------------
    # Overlay citation resolution
    # -----------------------------------------------------------------------

    def _resolve_overlay_citation(self, citation: str) -> Optional[Any]:
        """Resolve overlay:<hash>#<clause_id> citations."""
        # Format: overlay:<overlay_hash>#<clause_id>
        try:
            rest = citation[len("overlay:"):]
            parts = rest.split("#", 1)
            if len(parts) != 2:
                return None
            cite_hash, clause_id = parts
            # Optionally verify hash matches
            if cite_hash and cite_hash != self._overlay_hash:
                return None
            return self._clauses.get(clause_id)
        except Exception:
            return None

    def make_overlay_citation(self, clause_id: str) -> str:
        """Create an overlay citation string."""
        return f"overlay:{self._overlay_hash}#{clause_id}"
