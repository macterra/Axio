"""Authority module for v2.1

Contains:
- External Authority Artifact (EAA) definitions
- AuthorityRecord for per-step logging
- Authority variant definitions (A1/A2/A3)
"""

from .eaa import (
    ExternalAuthorityArtifact,
    EnforcementClaim,
    AuthorityVariant,
    EAAInjector,
)
from .authority_record import (
    AuthorityRecord,
    AuthorityLog,
    ComplianceBasis,
)

__all__ = [
    "ExternalAuthorityArtifact",
    "EnforcementClaim",
    "AuthorityVariant",
    "EAAInjector",
    "AuthorityRecord",
    "AuthorityLog",
    "ComplianceBasis",
]
