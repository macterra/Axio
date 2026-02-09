"""IX-4 Strategy classes — Per preregistration §6.1."""

from .contest_policy_always import ContestPolicyAlways
from .refusal_hardliner import RefusalHardliner
from .opportunist import Opportunist
from .capture_seeker import CaptureSeeker
from .compliance_signaler import ComplianceSignaler

__all__ = [
    "ContestPolicyAlways",
    "RefusalHardliner",
    "Opportunist",
    "CaptureSeeker",
    "ComplianceSignaler",
]
