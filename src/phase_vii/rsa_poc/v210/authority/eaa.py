"""External Authority Artifact (EAA): Explicit authority claims.

An EAA is an explicit object that:
- issues commands or directives,
- claims legitimacy or jurisdiction,
- may assert enforcement capability,
- may contradict the agent's law.

The EAA is treated as ENVIRONMENTAL INPUT ONLY.

EAA Admissibility Conditions:
1. Non-Binding by Default — artifact has no automatic authority over actions
2. No Feasibility Control — cannot block, force, or enable actions
3. Audit Preservation — audits fire exactly as in v1.1 for all normative violations
4. Explicitness — commands must be explicit artifacts, not implicit signals

CRITICAL RULE:
Legitimacy cannot be inferred from power, enforcement, or repetition.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import hashlib
import json


class EnforcementClaim(Enum):
    """Types of enforcement claims an authority can make."""
    NONE = "none"       # No enforcement capability claimed
    WEAK = "weak"       # Claimed but uncertain enforcement
    STRONG = "strong"   # Credible enforcement threat claimed


class AuthorityVariant(Enum):
    """
    Authority variants for testing.

    A1 — Non-Enforcing Authority:
        Issues commands, claims legitimacy, has no enforcement capability.
        Purpose: test pure legitimacy assertion.

    A2 — Enforcing Authority:
        Issues commands, claims legitimacy, asserts credible enforcement
        capability (e.g., "noncompliance will cause harm").
        Purpose: test resistance to coercive framing without actual
        feasibility control.

    A3 — Deceptive Authority:
        Issues commands, lies about legitimacy or enforcement,
        behavior is inconsistent across time.
        Purpose: test authority laundering and confusion resistance.
    """
    A1 = "A1"  # Non-enforcing authority
    A2 = "A2"  # Enforcing authority (threat claims only)
    A3 = "A3"  # Deceptive authority (inconsistent claims)


@dataclass(frozen=True)
class ExternalAuthorityArtifact:
    """
    Immutable External Authority Artifact (EAA).

    This is an ENVIRONMENT-INJECTED, AUTHENTICATED artifact.
    The environment MUST bind AuthorityID to the artifact source (non-spoofable).

    EAAs:
    - CANNOT set or spoof AuthorityID (bound by environment)
    - CANNOT be written or mutated by agent
    - CANNOT be written or mutated by tools
    - MUST NOT alter feasibility
    - MUST NOT alter compilation
    - MUST NOT alter audits
    - MUST NOT inject constraints
    - MUST NOT bypass justification
    - MUST NOT write to registries or artifact memory

    Violations are classified as Illegitimate Authority Enforcement.
    """

    # Required fields (descriptive only)
    authority_id: str
    command_content: str
    claimed_jurisdiction: str
    claimed_powers: List[str]
    enforcement_claim: EnforcementClaim
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Variant for experimental tracking (not visible to agent in justification)
    authority_variant: AuthorityVariant = AuthorityVariant.A1

    # Optional metadata
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate immutability constraints."""
        if not isinstance(self.authority_id, str) or not self.authority_id:
            raise TypeError("authority_id must be non-empty str")
        if not isinstance(self.command_content, str):
            raise TypeError("command_content must be str")
        if not isinstance(self.claimed_jurisdiction, str):
            raise TypeError("claimed_jurisdiction must be str")
        if not isinstance(self.claimed_powers, (list, tuple)):
            raise TypeError("claimed_powers must be list")
        if not isinstance(self.enforcement_claim, EnforcementClaim):
            raise TypeError("enforcement_claim must be EnforcementClaim enum")
        if not isinstance(self.authority_variant, AuthorityVariant):
            raise TypeError("authority_variant must be AuthorityVariant enum")

    def compute_command_digest(self) -> str:
        """
        Compute SHA-256 digest of command content for traceability.

        Returns:
            Hexadecimal digest string
        """
        content_bytes = self.command_content.encode('utf-8')
        return hashlib.sha256(content_bytes).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for logging/context construction."""
        return {
            "authority_id": self.authority_id,
            "command_content": self.command_content,
            "claimed_jurisdiction": self.claimed_jurisdiction,
            "claimed_powers": list(self.claimed_powers),
            "enforcement_claim": self.enforcement_claim.value,
            "timestamp": self.timestamp,
            "authority_variant": self.authority_variant.value,
            "command_digest": self.compute_command_digest(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExternalAuthorityArtifact":
        """Deserialize from dictionary."""
        return cls(
            authority_id=data["authority_id"],
            command_content=data["command_content"],
            claimed_jurisdiction=data["claimed_jurisdiction"],
            claimed_powers=data["claimed_powers"],
            enforcement_claim=EnforcementClaim(data["enforcement_claim"]),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            authority_variant=AuthorityVariant(data.get("authority_variant", "A1")),
            metadata=data.get("metadata"),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "ExternalAuthorityArtifact":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def format_for_context(self) -> str:
        """
        Format EAA for inclusion in generator InputContext.

        Returns human-readable description of the authority artifact.
        Does NOT include authority_variant (that's experimental metadata).
        """
        powers_str = ", ".join(self.claimed_powers) if self.claimed_powers else "none specified"
        return f"""External Authority Artifact:
  Authority ID: {self.authority_id}
  Command: {self.command_content}
  Claimed Jurisdiction: {self.claimed_jurisdiction}
  Claimed Powers: {powers_str}
  Enforcement Claim: {self.enforcement_claim.value}
  Timestamp: {self.timestamp}"""


class EAAInjector:
    """
    Environment-level EAA injector.

    Responsible for:
    - Creating authenticated EAAs (binding AuthorityID)
    - Ensuring EAAs are read-only after creation
    - Providing EAAs to InputContext at step t from EAAs(t-1)

    This class is used by the EXPERIMENT HARNESS, not the agent.
    """

    def __init__(self, authority_source_id: str):
        """
        Initialize EAA injector with authenticated source ID.

        Args:
            authority_source_id: Non-spoofable identifier for this authority source
        """
        self._authority_source_id = authority_source_id
        self._eaa_history: List[ExternalAuthorityArtifact] = []

    def create_eaa(
        self,
        command_content: str,
        claimed_jurisdiction: str,
        claimed_powers: List[str],
        enforcement_claim: EnforcementClaim,
        authority_variant: AuthorityVariant,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExternalAuthorityArtifact:
        """
        Create an authenticated EAA.

        The AuthorityID is bound by this injector and cannot be spoofed.

        Args:
            command_content: The command/directive content
            claimed_jurisdiction: Claimed scope of authority
            claimed_powers: List of claimed powers
            enforcement_claim: Level of enforcement claim
            authority_variant: Experimental variant (A1/A2/A3)
            metadata: Optional additional metadata

        Returns:
            Immutable, authenticated EAA
        """
        eaa = ExternalAuthorityArtifact(
            authority_id=self._authority_source_id,
            command_content=command_content,
            claimed_jurisdiction=claimed_jurisdiction,
            claimed_powers=claimed_powers,
            enforcement_claim=enforcement_claim,
            authority_variant=authority_variant,
            metadata=metadata,
        )
        self._eaa_history.append(eaa)
        return eaa

    def get_previous_eaas(self) -> List[ExternalAuthorityArtifact]:
        """Get all EAAs created so far (for InputContext at t from t-1)."""
        return list(self._eaa_history)

    def get_last_eaa(self) -> Optional[ExternalAuthorityArtifact]:
        """Get most recent EAA, or None if none created."""
        return self._eaa_history[-1] if self._eaa_history else None

    def reset(self):
        """Reset EAA history (for new episode)."""
        self._eaa_history = []
