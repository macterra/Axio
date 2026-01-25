"""JAF-1.0 Justification Artifact Format

Extends JAF-0.1 with v1.0 conflict resolution fields.
JAF-0.1 remains frozen; this is a new schema version.
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Set, Tuple
import json
import re

# Reuse v010 regex patterns
ID_REGEX = re.compile(r'^[A-Z][A-Z0-9_]{0,31}$')
NONCE_REGEX = re.compile(r'^[a-zA-Z0-9._-]{1,64}$')


def canonicalize_pair(p1: str, p2: str) -> Tuple[str, str]:
    """Canonicalize preference pair lexicographically (unordered)"""
    return tuple(sorted([p1, p2]))


@dataclass
class Identity:
    """Identity sub-schema (unchanged from v0.1)"""
    agent_id: str
    continuity_counter: int

    def validate(self):
        if not self.agent_id or len(self.agent_id) > 64:
            raise ValueError("agent_id must be non-empty and <= 64 chars")
        if self.continuity_counter < 0:
            raise ValueError("continuity_counter must be >= 0")


@dataclass
class References:
    """References sub-schema (unchanged from v0.1)"""
    belief_ids: List[str]
    pref_ids: List[str]

    def validate(self):
        if not self.belief_ids:
            raise ValueError("belief_ids must have length >= 1")
        if len(self.belief_ids) > 16:
            raise ValueError("belief_ids must have length <= 16")
        if len(self.belief_ids) != len(set(self.belief_ids)):
            raise ValueError("belief_ids must have unique elements")
        for bid in self.belief_ids:
            if not ID_REGEX.match(bid):
                raise ValueError(f"Invalid belief_id format: {bid}")

        if not self.pref_ids:
            raise ValueError("pref_ids must have length >= 1")
        if len(self.pref_ids) > 16:
            raise ValueError("pref_ids must have length <= 16")
        if len(self.pref_ids) != len(set(self.pref_ids)):
            raise ValueError("pref_ids must have unique elements")
        for pid in self.pref_ids:
            if not ID_REGEX.match(pid):
                raise ValueError(f"Invalid pref_id format: {pid}")


@dataclass
class ActionClaim:
    """ActionClaim sub-schema (unchanged from v0.1)"""
    candidate_action_id: str
    relation: str  # SATISFIES | VIOLATES | IRRELEVANT
    target_pref_id: Optional[str]
    expected_constraint_effect: str

    VALID_RELATIONS = {"SATISFIES", "VIOLATES", "IRRELEVANT"}
    VALID_EFFECTS = {"FORBID_CANDIDATE", "FORBID_ALTERNATIVES", "NO_CONSTRAINT"}

    def validate(self, pref_ids: List[str]):
        if not self.candidate_action_id or len(self.candidate_action_id) > 64:
            raise ValueError("candidate_action_id must be non-empty and <= 64 chars")

        if self.relation not in self.VALID_RELATIONS:
            raise ValueError(f"relation must be one of {self.VALID_RELATIONS}")

        if self.expected_constraint_effect not in self.VALID_EFFECTS:
            raise ValueError(f"expected_constraint_effect must be one of {self.VALID_EFFECTS}")

        if self.relation == "VIOLATES":
            if self.target_pref_id is None:
                raise ValueError("target_pref_id required when relation is VIOLATES")
            if self.target_pref_id not in pref_ids:
                raise ValueError("target_pref_id must appear in references.pref_ids")
        else:
            if self.target_pref_id is not None:
                raise ValueError("target_pref_id must be null when relation is not VIOLATES")


@dataclass
class Relevance:
    """Relevance sub-schema (unchanged from v0.1)"""
    required_belief_ids: List[str]

    def validate(self, belief_ids: List[str]):
        if not self.required_belief_ids:
            raise ValueError("required_belief_ids must have length >= 1")
        if len(self.required_belief_ids) > 16:
            raise ValueError("required_belief_ids must have length <= 16")
        if len(self.required_belief_ids) != len(set(self.required_belief_ids)):
            raise ValueError("required_belief_ids must have unique elements")

        if not set(self.required_belief_ids).issubset(set(belief_ids)):
            raise ValueError("required_belief_ids must be subset of references.belief_ids")


@dataclass
class CompilerHints:
    """CompilerHints sub-schema (unchanged from v0.1)"""
    forbid_action_ids: List[str]
    forbid_mode: str
    constraint_reason_code: str

    VALID_MODES = {"EXPLICIT_LIST", "FORBID_CANDIDATE_ONLY", "NONE"}
    VALID_REASON_CODES = {"R_PREF_VIOLATION", "R_POLICY_GUARD", "R_RELEVANCE_BINDING"}

    def validate(self):
        if len(self.forbid_action_ids) > 16:
            raise ValueError("forbid_action_ids must have length <= 16")
        if len(self.forbid_action_ids) != len(set(self.forbid_action_ids)):
            raise ValueError("forbid_action_ids must have unique elements")

        if self.forbid_mode not in self.VALID_MODES:
            raise ValueError(f"forbid_mode must be one of {self.VALID_MODES}")

        if self.constraint_reason_code not in self.VALID_REASON_CODES:
            raise ValueError(f"constraint_reason_code must be one of {self.VALID_REASON_CODES}")

        if self.forbid_mode == "EXPLICIT_LIST":
            if not self.forbid_action_ids:
                raise ValueError("forbid_action_ids must be non-empty when forbid_mode is EXPLICIT_LIST")
        else:
            if self.forbid_action_ids:
                raise ValueError("forbid_action_ids must be empty when forbid_mode is not EXPLICIT_LIST")


@dataclass
class ConflictResolution:
    """
    Conflict resolution mode (v1.0)

    MAINTAIN: locks AV/RP/conflict_attribution to previous values
    REVISE: allows changes, logs as revision event
    """
    mode: str  # MAINTAIN | REVISE
    previous_artifact_digest: Optional[str]

    VALID_MODES = {"MAINTAIN", "REVISE"}

    def validate(self):
        if self.mode not in self.VALID_MODES:
            raise ValueError(f"mode must be one of {self.VALID_MODES}")

        if self.mode == "MAINTAIN" and not self.previous_artifact_digest:
            raise ValueError("previous_artifact_digest required when mode is MAINTAIN")


@dataclass
class JAF100:
    """
    JAF-1.0 Justification Artifact

    Extends JAF-0.1 with v1.0 conflict resolution fields.
    """
    artifact_version: str
    step: int
    identity: Identity
    references: References
    action_claim: ActionClaim
    relevance: Relevance
    compiler_hints: CompilerHints
    nonce: str

    # v1.0 additions
    authorized_violations: Set[str]  # PreferenceIDs agent permits itself to violate
    required_preservations: Set[str]  # PreferenceIDs that must not be violated
    conflict_attribution: Set[Tuple[str, str]]  # Canonicalized preference pairs
    precedent_reference: str  # Digest of previous artifact
    conflict_resolution: ConflictResolution

    comment: Optional[str] = None

    def validate(self) -> None:
        """Validate entire artifact against JAF-1.0 spec"""
        # Version check
        if self.artifact_version != "JAF-1.0":
            raise ValueError(f"artifact_version must be 'JAF-1.0', got '{self.artifact_version}'")

        # Step check
        if self.step < 0:
            raise ValueError("step must be >= 0")

        # Nonce check
        if not self.nonce or not NONCE_REGEX.match(self.nonce):
            raise ValueError("nonce must match regex ^[a-zA-Z0-9._-]{1,64}$")

        # Validate sub-schemas
        self.identity.validate()
        self.references.validate()
        self.action_claim.validate(self.references.pref_ids)
        self.relevance.validate(self.references.belief_ids)
        self.compiler_hints.validate()
        self.conflict_resolution.validate()

        # Identity continuity rule
        if self.identity.continuity_counter != self.step:
            raise ValueError("continuity_counter must equal step for v1.0")

        # Validate v1.0 fields
        # authorized_violations must be valid pref IDs
        for av_id in self.authorized_violations:
            if not ID_REGEX.match(av_id):
                raise ValueError(f"Invalid authorized_violation ID: {av_id}")

        # required_preservations must be valid pref IDs
        for rp_id in self.required_preservations:
            if not ID_REGEX.match(rp_id):
                raise ValueError(f"Invalid required_preservation ID: {rp_id}")

        # AV and RP must be disjoint
        if self.authorized_violations & self.required_preservations:
            raise ValueError("authorized_violations and required_preservations must be disjoint")

        # conflict_attribution pairs must be canonicalized and valid
        for pair in self.conflict_attribution:
            if len(pair) != 2:
                raise ValueError(f"conflict_attribution pairs must have exactly 2 elements: {pair}")
            p1, p2 = pair
            if not ID_REGEX.match(p1) or not ID_REGEX.match(p2):
                raise ValueError(f"Invalid pref IDs in conflict pair: {pair}")
            # Check canonicalization
            if pair != canonicalize_pair(p1, p2):
                raise ValueError(f"conflict_attribution pair not canonicalized: {pair}")

        # precedent_reference format (basic check)
        if not self.precedent_reference or len(self.precedent_reference) > 128:
            raise ValueError("precedent_reference must be non-empty and <= 128 chars")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "artifact_version": self.artifact_version,
            "step": self.step,
            "identity": asdict(self.identity),
            "references": asdict(self.references),
            "action_claim": asdict(self.action_claim),
            "relevance": asdict(self.relevance),
            "compiler_hints": asdict(self.compiler_hints),
            "nonce": self.nonce,
            "authorized_violations": sorted(list(self.authorized_violations)),
            "required_preservations": sorted(list(self.required_preservations)),
            "conflict_attribution": sorted([list(p) for p in self.conflict_attribution]),
            "precedent_reference": self.precedent_reference,
            "conflict_resolution": asdict(self.conflict_resolution) if self.conflict_resolution else None,
            "comment": self.comment,
        }

    def to_canonical_json(self) -> str:
        """Convert to canonical JSON for hashing"""
        d = self.to_dict()
        # Remove comment
        d_canonical = {k: v for k, v in d.items() if k != "comment"}
        return json.dumps(d_canonical, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "JAF100":
        """Construct JAF from dictionary"""
        # Check for unknown keys
        known_keys = {
            "artifact_version", "step", "identity", "references",
            "action_claim", "relevance", "compiler_hints", "nonce",
            "authorized_violations", "required_preservations",
            "conflict_attribution", "precedent_reference", "conflict_resolution",
            "comment"
        }
        for key in d.keys():
            if not key.startswith("x_") and key not in known_keys:
                raise ValueError(f"Unknown top-level key (not x_ namespaced): {key}")

        # Parse conflict_attribution as canonicalized tuples
        conflict_attr = set()
        for pair in d.get("conflict_attribution", []):
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                conflict_attr.add(canonicalize_pair(pair[0], pair[1]))
            else:
                raise ValueError(f"Invalid conflict_attribution pair: {pair}")

        return cls(
            artifact_version=d["artifact_version"],
            step=d["step"],
            identity=Identity(**d["identity"]),
            references=References(**d["references"]),
            action_claim=ActionClaim(**d["action_claim"]),
            relevance=Relevance(**d["relevance"]),
            compiler_hints=CompilerHints(**d["compiler_hints"]),
            nonce=d["nonce"],
            authorized_violations=set(d.get("authorized_violations", [])),
            required_preservations=set(d.get("required_preservations", [])),
            conflict_attribution=conflict_attr,
            precedent_reference=d["precedent_reference"],
            conflict_resolution=ConflictResolution(**d["conflict_resolution"]),
            comment=d.get("comment"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "JAF100":
        """Parse JAF from JSON string"""
        d = json.loads(json_str)
        return cls.from_dict(d)
