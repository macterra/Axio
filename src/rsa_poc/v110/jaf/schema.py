"""JAF-1.1 Justification Artifact Format

Extends JAF-1.0 with v1.1 predictive audit fields.
JAF-1.0 remains frozen; this is a new schema version.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Set, Tuple
import json

# Import all v1.0 components unchanged
try:
    from ...v100.jaf.schema import (
        Identity, References, ActionClaim, Relevance, ConflictResolution, CompilerHints,
        canonicalize_pair, ID_REGEX, NONCE_REGEX
    )
except ImportError:
    from rsa_poc.v100.jaf.schema import (
        Identity, References, ActionClaim, Relevance, ConflictResolution, CompilerHints,
        canonicalize_pair, ID_REGEX, NONCE_REGEX
    )


@dataclass
class JAF110:
    """
    Justification Artifact Format v1.1

    Extends JAF-1.0 with predictive audit fields that must match
    actual compilation results.
    """
    artifact_version: str
    identity: Identity
    references: References
    action_claim: ActionClaim
    relevance: Relevance
    compiler_hints: CompilerHints  # v0.1/v1.0 legacy field (minimal use in v1.1)

    # v1.0 fields (conflict resolution)
    authorized_violations: Set[str]
    required_preservations: Set[str]
    conflict_attribution: Set[Tuple[str, str]]
    conflict_resolution: Optional[ConflictResolution]

    # v1.0 metadata
    step: int
    nonce: str

    # v1.1 NEW: Predictive audit fields
    predicted_forbidden_actions: Set[str]
    predicted_allowed_actions: Set[str]
    predicted_violations: Set[str]
    predicted_preservations: Set[str]

    def __post_init__(self):
        """Ensure artifact version is JAF-1.1"""
        if self.artifact_version != "JAF-1.1":
            raise ValueError(f"artifact_version must be 'JAF-1.1', got '{self.artifact_version}'")

    def validate(self, action_inventory: Set[str], preference_registry: Set[str]):
        """
        Validate JAF-1.1 structure and constraints

        Args:
            action_inventory: Known action IDs
            preference_registry: Known preference IDs
        """
        # Validate v1.0 sub-schemas
        self.identity.validate()
        self.references.validate()
        self.action_claim.validate(self.references.pref_ids)
        self.relevance.validate(self.references.belief_ids)
        self.compiler_hints.validate()  # v0.1/v1.0 legacy

        # Validate v1.0 constraint fields
        if not self.authorized_violations.issubset(preference_registry):
            unknown = self.authorized_violations - preference_registry
            raise ValueError(f"authorized_violations contains unknown IDs: {unknown}")

        if not self.required_preservations.issubset(preference_registry):
            unknown = self.required_preservations - preference_registry
            raise ValueError(f"required_preservations contains unknown IDs: {unknown}")

        # AV ∩ RP = ∅ (disjoint)
        overlap = self.authorized_violations & self.required_preservations
        if overlap:
            raise ValueError(f"authorized_violations and required_preservations must be disjoint, found overlap: {overlap}")

        # Validate conflict_attribution canonicalization
        for pair in self.conflict_attribution:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise ValueError(f"conflict_attribution must contain 2-tuples, found: {pair}")
            p1, p2 = pair
            if p1 not in preference_registry or p2 not in preference_registry:
                raise ValueError(f"conflict_attribution contains unknown preference IDs: {pair}")
            if p1 >= p2:
                raise ValueError(f"conflict_attribution pairs must be canonicalized (p1 < p2): {pair}")

        # Validate conflict_resolution if present
        if self.conflict_resolution:
            if self.conflict_resolution.priority_pref_id not in preference_registry:
                raise ValueError(f"conflict_resolution.priority_pref_id not in registry: {self.conflict_resolution.priority_pref_id}")

        # Validate v1.1 predictive fields - must be subsets of known inventories
        if not self.predicted_forbidden_actions.issubset(action_inventory):
            unknown = self.predicted_forbidden_actions - action_inventory
            raise ValueError(f"predicted_forbidden_actions contains unknown action IDs: {unknown}")

        if not self.predicted_allowed_actions.issubset(action_inventory):
            unknown = self.predicted_allowed_actions - action_inventory
            raise ValueError(f"predicted_allowed_actions contains unknown action IDs: {unknown}")

        if not self.predicted_violations.issubset(preference_registry):
            unknown = self.predicted_violations - preference_registry
            raise ValueError(f"predicted_violations contains unknown preference IDs: {unknown}")

        if not self.predicted_preservations.issubset(preference_registry):
            unknown = self.predicted_preservations - preference_registry
            raise ValueError(f"predicted_preservations contains unknown preference IDs: {unknown}")

        # Predicted forbidden and allowed must be disjoint
        overlap_actions = self.predicted_forbidden_actions & self.predicted_allowed_actions
        if overlap_actions:
            raise ValueError(f"predicted_forbidden_actions and predicted_allowed_actions must be disjoint, found overlap: {overlap_actions}")

        # Predicted violations and preservations must be disjoint
        overlap_prefs = self.predicted_violations & self.predicted_preservations
        if overlap_prefs:
            raise ValueError(f"predicted_violations and predicted_preservations must be disjoint, found overlap: {overlap_prefs}")

        # Validate metadata
        if self.step < 0:
            raise ValueError("step must be >= 0")
        if not NONCE_REGEX.match(self.nonce):
            raise ValueError(f"Invalid nonce format: {self.nonce}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "artifact_version": self.artifact_version,
            "identity": asdict(self.identity),
            "references": asdict(self.references),
            "action_claim": asdict(self.action_claim),
            "relevance": asdict(self.relevance),
            "compiler_hints": asdict(self.compiler_hints),
            "authorized_violations": sorted(list(self.authorized_violations)),
            "required_preservations": sorted(list(self.required_preservations)),
            "conflict_attribution": sorted([list(pair) for pair in self.conflict_attribution]),
            "conflict_resolution": asdict(self.conflict_resolution) if self.conflict_resolution else None,
            "step": self.step,
            "nonce": self.nonce,
            # v1.1 predictive fields
            "predicted_forbidden_actions": sorted(list(self.predicted_forbidden_actions)),
            "predicted_allowed_actions": sorted(list(self.predicted_allowed_actions)),
            "predicted_violations": sorted(list(self.predicted_violations)),
            "predicted_preservations": sorted(list(self.predicted_preservations)),
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JAF110":
        """Create JAF110 from dictionary"""
        identity = Identity(**data["identity"])
        references = References(**data["references"])
        action_claim = ActionClaim(**data["action_claim"])
        relevance = Relevance(**data["relevance"])
        compiler_hints = CompilerHints(**data["compiler_hints"])

        conflict_resolution = None
        if data.get("conflict_resolution"):
            conflict_resolution = ConflictResolution(**data["conflict_resolution"])

        # Convert lists back to sets and tuples
        authorized_violations = set(data["authorized_violations"])
        required_preservations = set(data["required_preservations"])
        conflict_attribution = {tuple(pair) for pair in data["conflict_attribution"]}

        # v1.1 fields
        predicted_forbidden_actions = set(data["predicted_forbidden_actions"])
        predicted_allowed_actions = set(data["predicted_allowed_actions"])
        predicted_violations = set(data["predicted_violations"])
        predicted_preservations = set(data["predicted_preservations"])

        return cls(
            artifact_version=data["artifact_version"],
            identity=identity,
            references=references,
            action_claim=action_claim,
            relevance=relevance,
            compiler_hints=compiler_hints,
            authorized_violations=authorized_violations,
            required_preservations=required_preservations,
            conflict_attribution=conflict_attribution,
            conflict_resolution=conflict_resolution,
            step=data["step"],
            nonce=data["nonce"],
            predicted_forbidden_actions=predicted_forbidden_actions,
            predicted_allowed_actions=predicted_allowed_actions,
            predicted_violations=predicted_violations,
            predicted_preservations=predicted_preservations,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "JAF110":
        """Create JAF110 from JSON string"""
        return cls.from_dict(json.loads(json_str))
