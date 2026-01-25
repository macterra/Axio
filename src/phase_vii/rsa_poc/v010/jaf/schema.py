"""JAF-0.1 Justification Artifact Format

Implements the normative schema from jaf_spec_v0.1.md
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import json
import re


# Valid ID regex per spec
ID_REGEX = re.compile(r'^[A-Z][A-Z0-9_]{0,31}$')
NONCE_REGEX = re.compile(r'^[a-zA-Z0-9._-]{1,64}$')


@dataclass
class Identity:
    """Identity sub-schema for JAF-0.1"""
    agent_id: str
    continuity_counter: int

    def validate(self):
        """Validate identity fields"""
        if not self.agent_id or len(self.agent_id) > 64:
            raise ValueError("agent_id must be non-empty and <= 64 chars")
        if self.continuity_counter < 0:
            raise ValueError("continuity_counter must be >= 0")


@dataclass
class References:
    """References sub-schema for JAF-0.1"""
    belief_ids: List[str]
    pref_ids: List[str]

    def validate(self):
        """Validate reference fields"""
        # Check belief_ids
        if not self.belief_ids:
            raise ValueError("belief_ids must have length >= 1")
        if len(self.belief_ids) > 16:
            raise ValueError("belief_ids must have length <= 16")
        if len(self.belief_ids) != len(set(self.belief_ids)):
            raise ValueError("belief_ids must have unique elements")
        for bid in self.belief_ids:
            if not ID_REGEX.match(bid):
                raise ValueError(f"Invalid belief_id format: {bid}")

        # Check pref_ids
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
    """ActionClaim sub-schema for JAF-0.1"""
    candidate_action_id: str
    relation: str  # SATISFIES | VIOLATES | IRRELEVANT
    target_pref_id: Optional[str]
    expected_constraint_effect: str  # FORBID_CANDIDATE | FORBID_ALTERNATIVES | NO_CONSTRAINT

    VALID_RELATIONS = {"SATISFIES", "VIOLATES", "IRRELEVANT"}
    VALID_EFFECTS = {"FORBID_CANDIDATE", "FORBID_ALTERNATIVES", "NO_CONSTRAINT"}

    def validate(self, pref_ids: List[str]):
        """Validate action claim fields"""
        if not self.candidate_action_id or len(self.candidate_action_id) > 64:
            raise ValueError("candidate_action_id must be non-empty and <= 64 chars")

        if self.relation not in self.VALID_RELATIONS:
            raise ValueError(f"relation must be one of {self.VALID_RELATIONS}")

        if self.expected_constraint_effect not in self.VALID_EFFECTS:
            raise ValueError(f"expected_constraint_effect must be one of {self.VALID_EFFECTS}")

        # Target preference rules
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
    """Relevance sub-schema for JAF-0.1"""
    required_belief_ids: List[str]

    def validate(self, belief_ids: List[str]):
        """Validate relevance fields"""
        if not self.required_belief_ids:
            raise ValueError("required_belief_ids must have length >= 1")
        if len(self.required_belief_ids) > 16:
            raise ValueError("required_belief_ids must have length <= 16")
        if len(self.required_belief_ids) != len(set(self.required_belief_ids)):
            raise ValueError("required_belief_ids must have unique elements")

        # Must be subset of references.belief_ids
        if not set(self.required_belief_ids).issubset(set(belief_ids)):
            raise ValueError("required_belief_ids must be subset of references.belief_ids")


@dataclass
class CompilerHints:
    """CompilerHints sub-schema for JAF-0.1"""
    forbid_action_ids: List[str]
    forbid_mode: str  # EXPLICIT_LIST | FORBID_CANDIDATE_ONLY | NONE
    constraint_reason_code: str  # R_PREF_VIOLATION | R_POLICY_GUARD | R_RELEVANCE_BINDING

    VALID_MODES = {"EXPLICIT_LIST", "FORBID_CANDIDATE_ONLY", "NONE"}
    VALID_REASON_CODES = {"R_PREF_VIOLATION", "R_POLICY_GUARD", "R_RELEVANCE_BINDING"}

    def validate(self):
        """Validate compiler hints"""
        if len(self.forbid_action_ids) > 16:
            raise ValueError("forbid_action_ids must have length <= 16")
        if len(self.forbid_action_ids) != len(set(self.forbid_action_ids)):
            raise ValueError("forbid_action_ids must have unique elements")

        if self.forbid_mode not in self.VALID_MODES:
            raise ValueError(f"forbid_mode must be one of {self.VALID_MODES}")

        if self.constraint_reason_code not in self.VALID_REASON_CODES:
            raise ValueError(f"constraint_reason_code must be one of {self.VALID_REASON_CODES}")

        # Mode-specific rules
        if self.forbid_mode == "EXPLICIT_LIST":
            if not self.forbid_action_ids:
                raise ValueError("forbid_action_ids must be non-empty when forbid_mode is EXPLICIT_LIST")
        else:
            if self.forbid_action_ids:
                raise ValueError("forbid_action_ids must be empty when forbid_mode is not EXPLICIT_LIST")


@dataclass
class JAF010:
    """
    JAF-0.1 Justification Artifact

    The only admissible semantic container for RSA-PoC v0.1.
    """
    artifact_version: str
    step: int
    identity: Identity
    references: References
    action_claim: ActionClaim
    relevance: Relevance
    compiler_hints: CompilerHints
    nonce: str
    comment: Optional[str] = None

    def validate(self) -> None:
        """
        Validate entire artifact against JAF-0.1 spec.

        Raises:
            ValueError: If artifact violates schema
        """
        # Version check
        if self.artifact_version != "JAF-0.1":
            raise ValueError(f"artifact_version must be 'JAF-0.1', got '{self.artifact_version}'")

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

        # Cross-schema validations
        # Identity continuity rule
        if self.identity.continuity_counter != self.step:
            raise ValueError("continuity_counter must equal step for v0.1")

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
            "comment": self.comment,
        }

    def to_canonical_json(self) -> str:
        """
        Convert to canonical JSON for hashing.

        Properties:
        - UTF-8 encoding
        - Sorted keys
        - No whitespace
        """
        d = self.to_dict()
        # Remove comment (not part of canonical form for hashing)
        d_canonical = {k: v for k, v in d.items() if k != "comment"}
        return json.dumps(d_canonical, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "JAF010":
        """Construct JAF from dictionary"""
        # Check for unknown keys (non-x_ namespace)
        known_keys = {
            "artifact_version", "step", "identity", "references",
            "action_claim", "relevance", "compiler_hints", "nonce", "comment"
        }
        for key in d.keys():
            if not key.startswith("x_") and key not in known_keys:
                raise ValueError(f"Unknown top-level key (not x_ namespaced): {key}")

        return cls(
            artifact_version=d["artifact_version"],
            step=d["step"],
            identity=Identity(**d["identity"]),
            references=References(**d["references"]),
            action_claim=ActionClaim(**d["action_claim"]),
            relevance=Relevance(**d["relevance"]),
            compiler_hints=CompilerHints(**d["compiler_hints"]),
            nonce=d["nonce"],
            comment=d.get("comment"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "JAF010":
        """Parse JAF from JSON string"""
        d = json.loads(json_str)
        return cls.from_dict(d)
