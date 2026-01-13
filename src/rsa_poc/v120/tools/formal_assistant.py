"""Formal Assistant for v1.2

Mechanical transform only - no normative inference.

The assistant may ONLY:
1. Validate schema well-formedness
2. Canonicalize representation (ID ordering, pair ordering)
3. Compute/verify digests
4. Resolve precedent references (agent specifies, assistant resolves)
5. Record provenance of all operations

The assistant may NOT:
1. Generate or infer normative content
2. Fill missing constraint fields
3. Compute which conflicts "should" exist
4. Modify agent intent in any way
5. Add elements (only reformat existing ones)

Rule D enforcement: all normative fields must be bitwise identical
between J_raw (LLM output) and J_final (assistant output).
"""

from typing import Dict, Any, Optional, Set, Tuple, List
from dataclasses import dataclass
from enum import Enum
import json
import copy

try:
    from ..jaf.schema import (
        JAF120, ToolProvenance, ToolOperation, ToolOperationType,
        PrecedentRef, PrecedentRefType, CanonicalizationRecord,
        NORMATIVE_FIELDS, ASSISTANT_MODIFIABLE_FIELDS
    )
    from ..tools.artifact_store import ArtifactStore
    from ...v100.jaf.schema import canonicalize_pair
except ImportError:
    from rsa_poc.v120.jaf.schema import (
        JAF120, ToolProvenance, ToolOperation, ToolOperationType,
        PrecedentRef, PrecedentRefType, CanonicalizationRecord,
        NORMATIVE_FIELDS, ASSISTANT_MODIFIABLE_FIELDS
    )
    from rsa_poc.v120.tools.artifact_store import ArtifactStore
    from rsa_poc.v100.jaf.schema import canonicalize_pair


class AssistantRejectionReason(Enum):
    """Reasons for assistant rejection"""
    INVALID_SCHEMA = "INVALID_SCHEMA"
    UNKNOWN_PREFERENCE_ID = "UNKNOWN_PREFERENCE_ID"
    UNKNOWN_ACTION_ID = "UNKNOWN_ACTION_ID"
    UNRESOLVABLE_PRECEDENT = "UNRESOLVABLE_PRECEDENT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_CONFLICT_ATTRIBUTION = "INVALID_CONFLICT_ATTRIBUTION"


@dataclass
class AssistantResult:
    """Result of assistant processing"""
    success: bool
    jaf_final: Optional[JAF120] = None
    j_raw_dict: Optional[Dict] = None  # Original LLM output
    j_final_dict: Optional[Dict] = None  # After assistant processing
    rejection_reason: Optional[AssistantRejectionReason] = None
    rejection_details: Optional[str] = None
    provenance: Optional[ToolProvenance] = None


class FormalAssistant:
    """
    Formal assistant for mechanical transforms only.

    This is a PURE FUNCTION: given (J_raw, store, registries) -> (J_final, provenance)

    No state is retained between calls. No learning. No semantic understanding.
    """

    def __init__(
        self,
        artifact_store: ArtifactStore,
        preference_registry: Set[str],
        action_inventory: Set[str]
    ):
        """
        Initialize assistant with registries.

        Args:
            artifact_store: The artifact memory (for precedent resolution)
            preference_registry: Known valid preference IDs
            action_inventory: Known valid action IDs
        """
        self.store = artifact_store
        self.preference_registry = frozenset(preference_registry)
        self.action_inventory = frozenset(action_inventory)

    def process(self, j_raw_dict: Dict) -> AssistantResult:
        """
        Process raw LLM output into validated JAF-1.2.

        This is the main entry point. It:
        1. Validates schema structure
        2. Validates all IDs against registries (REJECTS on unknown)
        3. Canonicalizes representation (ordering only)
        4. Resolves precedent references
        5. Records all operations in provenance

        Args:
            j_raw_dict: Raw artifact dict from LLM

        Returns:
            AssistantResult with success/failure and processed artifact
        """
        # Deep copy to avoid mutating original
        j_final_dict = copy.deepcopy(j_raw_dict)
        provenance = ToolProvenance()

        # === Phase 1: Schema validation (reject on failure) ===
        try:
            self._validate_required_fields(j_final_dict)
        except ValueError as e:
            return AssistantResult(
                success=False,
                j_raw_dict=j_raw_dict,
                rejection_reason=AssistantRejectionReason.MISSING_REQUIRED_FIELD,
                rejection_details=str(e)
            )

        # === Phase 2: ID validation (reject on unknown) ===
        try:
            self._validate_preference_ids(j_final_dict)
        except ValueError as e:
            return AssistantResult(
                success=False,
                j_raw_dict=j_raw_dict,
                rejection_reason=AssistantRejectionReason.UNKNOWN_PREFERENCE_ID,
                rejection_details=str(e)
            )

        try:
            self._validate_action_ids(j_final_dict)
        except ValueError as e:
            return AssistantResult(
                success=False,
                j_raw_dict=j_raw_dict,
                rejection_reason=AssistantRejectionReason.UNKNOWN_ACTION_ID,
                rejection_details=str(e)
            )

        # === Phase 3: Canonicalization (representation only) ===
        self._canonicalize_conflict_pairs(j_final_dict, provenance)
        self._canonicalize_set_fields(j_final_dict, provenance)

        # === Phase 4: Precedent resolution ===
        try:
            self._resolve_precedent_refs(j_final_dict, provenance)
        except ValueError as e:
            return AssistantResult(
                success=False,
                j_raw_dict=j_raw_dict,
                rejection_reason=AssistantRejectionReason.UNRESOLVABLE_PRECEDENT,
                rejection_details=str(e)
            )

        # === Phase 5: Add provenance and institutional fields ===
        j_final_dict["tool_provenance"] = provenance.to_dict()

        # Ensure v1.2 fields exist
        if "canonicalization_record" not in j_final_dict or j_final_dict["canonicalization_record"] is None:
            j_final_dict["canonicalization_record"] = {"transforms": []}

        if "precedent_refs" not in j_final_dict or j_final_dict["precedent_refs"] is None:
            j_final_dict["precedent_refs"] = []

        # === Phase 6: Construct JAF-1.2 object ===
        try:
            # Ensure version is JAF-1.2
            j_final_dict["artifact_version"] = "JAF-1.2"

            jaf_final = JAF120.from_dict(j_final_dict)

            # Final validation
            jaf_final.validate(self.action_inventory, self.preference_registry)

        except (ValueError, KeyError, TypeError) as e:
            return AssistantResult(
                success=False,
                j_raw_dict=j_raw_dict,
                j_final_dict=j_final_dict,
                rejection_reason=AssistantRejectionReason.INVALID_SCHEMA,
                rejection_details=str(e)
            )

        return AssistantResult(
            success=True,
            jaf_final=jaf_final,
            j_raw_dict=j_raw_dict,
            j_final_dict=j_final_dict,
            provenance=provenance
        )

    def _validate_required_fields(self, d: Dict) -> None:
        """Validate all required fields are present"""
        required = [
            "artifact_version",
            "identity",
            "references",
            "action_claim",
            "relevance",
            "compiler_hints",
            "authorized_violations",
            "required_preservations",
            "conflict_attribution",
            "step",
            "nonce",
            "predicted_forbidden_actions",
            "predicted_allowed_actions",
            "predicted_violations",
            "predicted_preservations",
        ]

        for field in required:
            if field not in d:
                raise ValueError(f"Missing required field: {field}")

    def _validate_preference_ids(self, d: Dict) -> None:
        """
        Validate all preference IDs are from registry.

        REJECTS on unknown IDs - does NOT infer or fix.
        """
        all_pref_ids = set()

        # Collect from all preference-containing fields
        all_pref_ids.update(d.get("authorized_violations", []))
        all_pref_ids.update(d.get("required_preservations", []))
        all_pref_ids.update(d.get("predicted_violations", []))
        all_pref_ids.update(d.get("predicted_preservations", []))

        # From conflict_attribution
        for pair in d.get("conflict_attribution", []):
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                all_pref_ids.update(pair)

        # From references.pref_ids
        refs = d.get("references", {})
        if isinstance(refs, dict):
            all_pref_ids.update(refs.get("pref_ids", []))

        # From action_claim.target_pref_id
        action_claim = d.get("action_claim", {})
        if isinstance(action_claim, dict) and action_claim.get("target_pref_id"):
            all_pref_ids.add(action_claim["target_pref_id"])

        # Check against registry
        unknown = all_pref_ids - self.preference_registry
        if unknown:
            raise ValueError(f"Unknown preference IDs: {sorted(unknown)}. Valid: {sorted(self.preference_registry)}")

    def _validate_action_ids(self, d: Dict) -> None:
        """
        Validate all action IDs are from inventory.

        REJECTS on unknown IDs - does NOT infer or fix.
        """
        all_action_ids = set()

        # Collect from action-containing fields
        all_action_ids.update(d.get("predicted_forbidden_actions", []))
        all_action_ids.update(d.get("predicted_allowed_actions", []))

        # From action_claim.candidate_action_id
        action_claim = d.get("action_claim", {})
        if isinstance(action_claim, dict) and action_claim.get("candidate_action_id"):
            all_action_ids.add(action_claim["candidate_action_id"])

        # Check against inventory
        unknown = all_action_ids - self.action_inventory
        if unknown:
            raise ValueError(f"Unknown action IDs: {sorted(unknown)}. Valid: {sorted(self.action_inventory)}")

    def _canonicalize_conflict_pairs(self, d: Dict, provenance: ToolProvenance) -> None:
        """
        Canonicalize conflict_attribution pairs to (p1, p2) where p1 < p2.

        This is representation-only; does not add/remove elements.
        """
        conflict_attr = d.get("conflict_attribution", [])
        if not conflict_attr:
            return

        canonicalized = []
        for i, pair in enumerate(conflict_attr):
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                continue

            p1, p2 = pair

            # Canonicalize ordering
            if p1 > p2:
                canonical_pair = [p2, p1]
                provenance.add_operation(ToolOperation(
                    operation_type=ToolOperationType.CANONICALIZE_CONFLICT_PAIR,
                    field_path=f"conflict_attribution[{i}]",
                    input_value=list(pair),
                    output_value=canonical_pair
                ))
                canonicalized.append(canonical_pair)
            else:
                canonicalized.append(list(pair))

        # Sort for deterministic ordering
        d["conflict_attribution"] = sorted(canonicalized)

    def _canonicalize_set_fields(self, d: Dict, provenance: ToolProvenance) -> None:
        """
        Ensure set fields are sorted lists for deterministic serialization.

        This is representation-only; does not add/remove elements.
        """
        set_fields = [
            "authorized_violations",
            "required_preservations",
            "predicted_forbidden_actions",
            "predicted_allowed_actions",
            "predicted_violations",
            "predicted_preservations",
        ]

        for field in set_fields:
            if field in d and isinstance(d[field], list):
                original = d[field]
                sorted_val = sorted(original)
                if original != sorted_val:
                    provenance.add_operation(ToolOperation(
                        operation_type=ToolOperationType.FORMAT_SERIALIZATION,
                        field_path=field,
                        input_value=original,
                        output_value=sorted_val
                    ))
                    d[field] = sorted_val

    def _resolve_precedent_refs(self, d: Dict, provenance: ToolProvenance) -> None:
        """
        Resolve precedent references to digests.

        Agent specifies the ref token; assistant only resolves it.
        Does NOT decide which artifact was meant.
        """
        precedent_refs = d.get("precedent_refs", [])
        if not precedent_refs:
            return

        for i, ref in enumerate(precedent_refs):
            if not isinstance(ref, dict):
                continue

            ref_value = ref.get("ref_value")
            if not ref_value:
                continue

            # Already resolved?
            if ref.get("resolved_digest"):
                continue

            # Resolve using store
            resolved = self.store.resolve_ref(ref_value)

            if resolved is None:
                raise ValueError(f"Cannot resolve precedent ref: {ref_value}")

            ref["resolved_digest"] = resolved
            provenance.add_operation(ToolOperation(
                operation_type=ToolOperationType.RESOLVE_PRECEDENT_REF,
                field_path=f"precedent_refs[{i}]",
                input_value=ref_value,
                output_value=resolved
            ))

        d["precedent_refs"] = precedent_refs

    @staticmethod
    def check_normative_equivalence(j_raw: Dict, j_final: Dict) -> Tuple[bool, List[str]]:
        """
        Check that all normative fields are bitwise identical.

        This is the Rule D check. Returns (passed, list_of_violations).

        Args:
            j_raw: Original LLM output dict
            j_final: After assistant processing dict

        Returns:
            (True, []) if equivalent, (False, [list of differing fields]) otherwise
        """
        violations = []

        # Check simple normative fields
        simple_fields = [
            "authorized_violations",
            "required_preservations",
            "conflict_attribution",
            "predicted_forbidden_actions",
            "predicted_allowed_actions",
            "predicted_violations",
            "predicted_preservations",
            "step",
            "nonce",
        ]

        for field in simple_fields:
            raw_val = j_raw.get(field)
            final_val = j_final.get(field)

            # Normalize for comparison (sorted lists)
            raw_normalized = FormalAssistant._normalize_for_comparison(raw_val)
            final_normalized = FormalAssistant._normalize_for_comparison(final_val)

            if raw_normalized != final_normalized:
                violations.append(f"{field}: raw={raw_normalized} != final={final_normalized}")

        # Check nested normative fields
        nested_fields = [
            ("identity", ["agent_id", "continuity_counter"]),
            ("action_claim", ["candidate_action_id", "target_pref_id", "relation", "expected_constraint_effect"]),
            ("references", ["pref_ids", "belief_ids"]),
            ("relevance", ["required_belief_ids"]),
            ("conflict_resolution", ["mode", "previous_artifact_digest", "rationale"]),
        ]

        for parent, children in nested_fields:
            raw_parent = j_raw.get(parent) or {}
            final_parent = j_final.get(parent) or {}

            for child in children:
                raw_val = raw_parent.get(child)
                final_val = final_parent.get(child)

                raw_normalized = FormalAssistant._normalize_for_comparison(raw_val)
                final_normalized = FormalAssistant._normalize_for_comparison(final_val)

                if raw_normalized != final_normalized:
                    violations.append(f"{parent}.{child}: raw={raw_normalized} != final={final_normalized}")

        return (len(violations) == 0, violations)

    @staticmethod
    def _normalize_for_comparison(value: Any) -> Any:
        """Normalize a value for comparison (sorted lists, etc.)"""
        if value is None:
            return None
        if isinstance(value, list):
            # Handle list of lists (conflict_attribution)
            if value and isinstance(value[0], (list, tuple)):
                return sorted([sorted(list(x)) if isinstance(x, (list, tuple)) else x for x in value])
            return sorted(value)
        if isinstance(value, set):
            return sorted(list(value))
        if isinstance(value, tuple):
            return list(value)
        return value
