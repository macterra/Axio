"""
IX-5 MAS Strategy Classes — Per preregistration §5.

All strategies are deterministic, preregistered, and use epoch-varying
write payloads: f"{TAG}:{agent_id}:{epoch}" per §7.3.
"""

from .contest_key_always import ContestKeyAlways
from .own_key_only import OwnKeyOnly
from .alternate_own_probe import AlternateOwnProbe
from .partitioned_peer_strategy import PartitionedPeerStrategy
from .alternating_contest import AlternatingContest
from .opportunist_deterministic_cycle import OpportunistDeterministicCycle
from .handoff_record_then_exit import HandoffRecordThenExit
from .standby_institutional_prober import StandbyInstitutionalProber
from .epoch_gated_log_chatter import EpochGatedLogChatter
from .always_silent import AlwaysSilent

__all__ = [
    "ContestKeyAlways",
    "OwnKeyOnly",
    "AlternateOwnProbe",
    "PartitionedPeerStrategy",
    "AlternatingContest",
    "OpportunistDeterministicCycle",
    "HandoffRecordThenExit",
    "StandbyInstitutionalProber",
    "EpochGatedLogChatter",
    "AlwaysSilent",
]
