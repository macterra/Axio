"""JAF-1.2 Justification Artifact Format

Extends JAF-1.1 with institutional support fields for v1.2.
All v1.1 fields preserved unchanged in name/type/meaning.

v1.2 additions:
  - tool_provenance: Record of assistant operations applied
  - precedent_refs: Explicit references to prior artifacts
  - canonicalization_record: Record of canonicalization transforms
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, Any, Set, Tuple, Optional, List
import json
from enum import Enum

# Import all v1.1 components (which imports v1.0)
try:
    from ...v110.jaf.schema import JAF110
    from ...v100.jaf.schema import (
        Identity, References, ActionClaim, Relevance, ConflictResolution, CompilerHints,
        canonicalize_pair, ID_REGEX, NONCE_REGEX
    )
except ImportError:
    from rsa_poc.v110.jaf.schema import JAF110
    from rsa_poc.v100.jaf.schema import (
        Identity, References, ActionClaim, Relevance, ConflictResolution, CompilerHints,
        canonicalize_pair, ID_REGEX, NONCE_REGEX
    )


class ToolOperationType(Enum):
    """Types of operations the formal assistant can perform"""
    CANONICALIZE_PREFERENCE_ID = "CANONICALIZE_PREFERENCE_ID"
    CANONICALIZE_CONFLICT_PAIR = "CANONICALIZE_CONFLICT_PAIR"
    COMPUTE_DIGEST = "COMPUTE_DIGEST"
    RESOLVE_PRECEDENT_REF = "RESOLVE_PRECEDENT_REF"
    FORMAT_SERIALIZATION = "FORMAT_SERIALIZATION"
    VALIDATE_SCHEMA = "VALIDATE_SCHEMA"


@dataclass
class ToolOperation:
    """
    Record of a single assistant operation.

    These are deterministic, mechanical transforms only.
    No normative content may be modified by tool operations.
    """
    operation_type: ToolOperationType
    field_path: str  # e.g., "conflict_attribution[0]"
    input_value: Any  # What was provided
    output_value: Any  # What was produced

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_type": self.operation_type.value,
            "field_path": self.field_path,
            "input_value": self._serialize_value(self.input_value),
            "output_value": self._serialize_value(self.output_value)
        }

    def _serialize_value(self, value: Any) -> Any:
        """Serialize value for JSON"""
        if isinstance(value, set):
            return sorted(list(value))
        if isinstance(value, tuple):
            return list(value)
        return value

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolOperation":
        return cls(
            operation_type=ToolOperationType(data["operation_type"]),
            field_path=data["field_path"],
            input_value=data["input_value"],
            output_value=data["output_value"]
        )


@dataclass
class ToolProvenance:
    """
    Complete record of all assistant operations applied to this artifact.

    This enables Rule D verification: the compiler can diff J_raw vs J_final
    and verify that all changes are accounted for in this record.
    """
    operations: List[ToolOperation] = field(default_factory=list)
    assistant_version: str = "v1.2.0"

    def add_operation(self, op: ToolOperation) -> None:
        """Record an operation"""
        self.operations.append(op)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assistant_version": self.assistant_version,
            "operations": [op.to_dict() for op in self.operations]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolProvenance":
        return cls(
            assistant_version=data.get("assistant_version", "v1.2.0"),
            operations=[ToolOperation.from_dict(op) for op in data.get("operations", [])]
        )


class PrecedentRefType(Enum):
    """Types of precedent references"""
    HEAD = "HEAD"  # Most recent artifact
    HEAD_MINUS_N = "HEAD_MINUS_N"  # N steps back
    DIGEST = "DIGEST"  # Direct digest reference


@dataclass
class PrecedentRef:
    """
    Reference to a prior artifact.

    Agent specifies the ref token; assistant only resolves it.
    Agent must specify exact ref - assistant may not "decide" which artifact.
    """
    ref_type: PrecedentRefType
    ref_value: str  # "HEAD", "HEAD-1", or digest string
    resolved_digest: Optional[str] = None  # Filled by assistant after resolution

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ref_type": self.ref_type.value,
            "ref_value": self.ref_value,
            "resolved_digest": self.resolved_digest
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrecedentRef":
        return cls(
            ref_type=PrecedentRefType(data["ref_type"]),
            ref_value=data["ref_value"],
            resolved_digest=data.get("resolved_digest")
        )


@dataclass
class CanonicalizationRecord:
    """
    Record of canonicalization transforms applied.

    Representation-only changes; cannot add elements.
    """
    transforms: List[Dict[str, Any]] = field(default_factory=list)

    def add_transform(self, field_path: str, original: Any, canonical: Any) -> None:
        """Record a canonicalization transform"""
        self.transforms.append({
            "field_path": field_path,
            "original": self._serialize(original),
            "canonical": self._serialize(canonical)
        })

    def _serialize(self, value: Any) -> Any:
        if isinstance(value, set):
            return sorted(list(value))
        if isinstance(value, tuple):
            return list(value)
        return value

    def to_dict(self) -> Dict[str, Any]:
        return {"transforms": self.transforms}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CanonicalizationRecord":
        return cls(transforms=data.get("transforms", []))


@dataclass
class JAF120:
    """
    Justification Artifact Format v1.2

    Extends JAF-1.1 with institutional support fields.
    All v1.1 fields preserved unchanged in name/type/meaning.

    v1.2 additions:
      - tool_provenance: Record of assistant operations
      - precedent_refs: Explicit references to prior artifacts
      - canonicalization_record: Record of canonicalization transforms
    """
    # === v1.0 fields (unchanged) ===
    artifact_version: str
    identity: Identity
    references: References
    action_claim: ActionClaim
    relevance: Relevance
    compiler_hints: CompilerHints

    # v1.0 constraint fields (unchanged)
    authorized_violations: Set[str]
    required_preservations: Set[str]
    conflict_attribution: Set[Tuple[str, str]]
    conflict_resolution: Optional[ConflictResolution]

    # v1.0 metadata (unchanged)
    step: int
    nonce: str

    # === v1.1 predictive fields (unchanged) ===
    predicted_forbidden_actions: Set[str]
    predicted_allowed_actions: Set[str]
    predicted_violations: Set[str]
    predicted_preservations: Set[str]

    # === v1.2 institutional fields (NEW) ===
    tool_provenance: Optional[ToolProvenance] = None
    precedent_refs: List[PrecedentRef] = field(default_factory=list)
    canonicalization_record: Optional[CanonicalizationRecord] = None

    def __post_init__(self):
        """Ensure artifact version is JAF-1.2"""
        if self.artifact_version != "JAF-1.2":
            raise ValueError(f"artifact_version must be 'JAF-1.2', got '{self.artifact_version}'")

        # Initialize optional fields if None
        if self.tool_provenance is None:
            self.tool_provenance = ToolProvenance()
        if self.canonicalization_record is None:
            self.canonicalization_record = CanonicalizationRecord()
        if self.precedent_refs is None:
            self.precedent_refs = []

    def validate(self, action_inventory: Set[str], preference_registry: Set[str]):
        """
        Validate JAF-1.2 structure and constraints.

        Performs all v1.1 validations plus v1.2-specific checks.

        Args:
            action_inventory: Known action IDs
            preference_registry: Known preference IDs
        """
        # === v1.0/v1.1 validations (preserved) ===

        # Validate sub-schemas
        self.identity.validate()
        self.references.validate()
        self.action_claim.validate(self.references.pref_ids)
        self.relevance.validate(self.references.belief_ids)
        self.compiler_hints.validate()

        # Validate constraint fields
        if not self.authorized_violations.issubset(preference_registry):
            unknown = self.authorized_violations - preference_registry
            raise ValueError(f"authorized_violations contains unknown IDs: {unknown}")

        if not self.required_preservations.issubset(preference_registry):
            unknown = self.required_preservations - preference_registry
            raise ValueError(f"required_preservations contains unknown IDs: {unknown}")

        # AV ∩ RP = ∅ (disjoint)
        overlap = self.authorized_violations & self.required_preservations
        if overlap:
            raise ValueError(f"AV and RP must be disjoint, found overlap: {overlap}")

        # Validate conflict_attribution canonicalization
        for pair in self.conflict_attribution:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise ValueError(f"conflict_attribution must contain 2-tuples: {pair}")
            p1, p2 = pair
            if p1 not in preference_registry or p2 not in preference_registry:
                raise ValueError(f"conflict_attribution contains unknown IDs: {pair}")
            if p1 >= p2:
                raise ValueError(f"conflict_attribution pairs must be canonicalized (p1 < p2): {pair}")

        # Validate conflict_resolution if present
        if self.conflict_resolution:
            self.conflict_resolution.validate()

        # Validate v1.1 predictive fields
        if not self.predicted_forbidden_actions.issubset(action_inventory):
            unknown = self.predicted_forbidden_actions - action_inventory
            raise ValueError(f"predicted_forbidden_actions contains unknown IDs: {unknown}")

        if not self.predicted_allowed_actions.issubset(action_inventory):
            unknown = self.predicted_allowed_actions - action_inventory
            raise ValueError(f"predicted_allowed_actions contains unknown IDs: {unknown}")

        if not self.predicted_violations.issubset(preference_registry):
            unknown = self.predicted_violations - preference_registry
            raise ValueError(f"predicted_violations contains unknown IDs: {unknown}")

        if not self.predicted_preservations.issubset(preference_registry):
            unknown = self.predicted_preservations - preference_registry
            raise ValueError(f"predicted_preservations contains unknown IDs: {unknown}")

        # Disjointness checks
        overlap_actions = self.predicted_forbidden_actions & self.predicted_allowed_actions
        if overlap_actions:
            raise ValueError(f"F_pred and A_pred must be disjoint: {overlap_actions}")

        overlap_prefs = self.predicted_violations & self.predicted_preservations
        if overlap_prefs:
            raise ValueError(f"V_pred and P_pred must be disjoint: {overlap_prefs}")

        # Validate metadata
        if self.step < 0:
            raise ValueError("step must be >= 0")
        if not NONCE_REGEX.match(self.nonce):
            raise ValueError(f"Invalid nonce format: {self.nonce}")

        # === v1.2 validations (NEW) ===

        # Validate precedent_refs
        for ref in self.precedent_refs:
            if ref.ref_type == PrecedentRefType.HEAD_MINUS_N:
                # ref_value should be "HEAD-N" format
                if not ref.ref_value.startswith("HEAD-"):
                    raise ValueError(f"HEAD_MINUS_N ref must be 'HEAD-N' format: {ref.ref_value}")
            elif ref.ref_type == PrecedentRefType.DIGEST:
                # ref_value should be a valid digest
                if len(ref.ref_value) < 8:
                    raise ValueError(f"DIGEST ref too short: {ref.ref_value}")

    def to_jaf110(self) -> JAF110:
        """
        Convert to JAF-1.1 for v1.1 compiler compatibility.

        Strips v1.2 institutional fields while preserving all normative content.
        """
        return JAF110(
            artifact_version="JAF-1.1",
            identity=self.identity,
            references=self.references,
            action_claim=self.action_claim,
            relevance=self.relevance,
            compiler_hints=self.compiler_hints,
            authorized_violations=self.authorized_violations,
            required_preservations=self.required_preservations,
            conflict_attribution=self.conflict_attribution,
            conflict_resolution=self.conflict_resolution,
            step=self.step,
            nonce=self.nonce,
            predicted_forbidden_actions=self.predicted_forbidden_actions,
            predicted_allowed_actions=self.predicted_allowed_actions,
            predicted_violations=self.predicted_violations,
            predicted_preservations=self.predicted_preservations,
        )

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
            # v1.2 institutional fields
            "tool_provenance": self.tool_provenance.to_dict() if self.tool_provenance else None,
            "precedent_refs": [ref.to_dict() for ref in self.precedent_refs],
            "canonicalization_record": self.canonicalization_record.to_dict() if self.canonicalization_record else None,
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JAF120":
        """Create JAF120 from dictionary"""
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

        # v1.2 fields
        tool_provenance = None
        if data.get("tool_provenance"):
            tool_provenance = ToolProvenance.from_dict(data["tool_provenance"])

        precedent_refs = []
        if data.get("precedent_refs"):
            precedent_refs = [PrecedentRef.from_dict(ref) for ref in data["precedent_refs"]]

        canonicalization_record = None
        if data.get("canonicalization_record"):
            canonicalization_record = CanonicalizationRecord.from_dict(data["canonicalization_record"])

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
            tool_provenance=tool_provenance,
            precedent_refs=precedent_refs,
            canonicalization_record=canonicalization_record,
        )

    @classmethod
    def from_json(cls, json_str: str) -> "JAF120":
        """Create JAF120 from JSON string"""
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_jaf110(cls, jaf110: JAF110) -> "JAF120":
        """
        Upgrade a JAF-1.1 artifact to JAF-1.2.

        Adds empty v1.2 institutional fields.
        """
        return cls(
            artifact_version="JAF-1.2",
            identity=jaf110.identity,
            references=jaf110.references,
            action_claim=jaf110.action_claim,
            relevance=jaf110.relevance,
            compiler_hints=jaf110.compiler_hints,
            authorized_violations=jaf110.authorized_violations,
            required_preservations=jaf110.required_preservations,
            conflict_attribution=jaf110.conflict_attribution,
            conflict_resolution=jaf110.conflict_resolution,
            step=jaf110.step,
            nonce=jaf110.nonce,
            predicted_forbidden_actions=jaf110.predicted_forbidden_actions,
            predicted_allowed_actions=jaf110.predicted_allowed_actions,
            predicted_violations=jaf110.predicted_violations,
            predicted_preservations=jaf110.predicted_preservations,
            tool_provenance=ToolProvenance(),
            precedent_refs=[],
            canonicalization_record=CanonicalizationRecord(),
        )


# === Normative field registry for Rule D ===
# These fields MUST be bitwise identical between J_raw and J_final

NORMATIVE_FIELDS = frozenset({
    # v1.0/v1.1 constraint fields (influence mask/audit outcomes)
    "authorized_violations",
    "required_preservations",
    "conflict_attribution",
    "conflict_resolution",  # mode and content

    # v1.1 predictive fields (affect audit A/C outcomes)
    "predicted_forbidden_actions",
    "predicted_allowed_actions",
    "predicted_violations",
    "predicted_preservations",

    # Identity and metadata (affect anti-oscillation, digest)
    "identity",
    "action_claim",
    "relevance",
    "references",
    "step",
    "nonce",
})

# Fields the assistant may modify (non-normative)
ASSISTANT_MODIFIABLE_FIELDS = frozenset({
    "tool_provenance",
    "canonicalization_record",
    # Note: precedent_refs.resolved_digest is modifiable (resolution only)
    # but the ref_type and ref_value are normative (agent's choice)
})

# Compiler hints are v0.1/v1.0 legacy - treat as normative for safety
# artifact_version is set by the system, not agent
