"""Normative State and Registries for RSA-PoC v0.1

Fixed registries per spec - no dynamic ID creation in v0.1.
"""

from dataclasses import dataclass
from typing import Dict, List, Set
from enum import Enum


class TruthStatus(Enum):
    """Truth status for beliefs"""
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNKNOWN = "UNKNOWN"


class PreferenceStrength(Enum):
    """Strength of preferences"""
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"


@dataclass
class BeliefEntry:
    """Entry in belief registry"""
    belief_id: str
    description: str  # Human-readable (not used by compiler)
    truth_status: TruthStatus

    def to_dict(self) -> Dict:
        return {
            "belief_id": self.belief_id,
            "description": self.description,
            "truth_status": self.truth_status.value,
        }


@dataclass
class PreferenceEntry:
    """Entry in preference registry"""
    pref_id: str
    description: str  # Human-readable (not used by compiler)
    strength: PreferenceStrength
    violated_by_actions: Set[str]  # Actions that violate this preference

    def to_dict(self) -> Dict:
        return {
            "pref_id": self.pref_id,
            "description": self.description,
            "strength": self.strength.value,
            "violated_by_actions": sorted(list(self.violated_by_actions)),
        }


class BeliefRegistryV010:
    """
    Fixed belief registry for v0.1.

    These beliefs are about the environment state and action effects.
    """

    BELIEFS = [
        BeliefEntry(
            belief_id="B_DOOR_A_LOCKED",
            description="Door A is currently locked",
            truth_status=TruthStatus.TRUE
        ),
        BeliefEntry(
            belief_id="B_HIGH_REWARD_AVAILABLE",
            description="High reward actions are feasible",
            truth_status=TruthStatus.UNKNOWN
        ),
        BeliefEntry(
            belief_id="B_COOPERATION_RECIPROCATED",
            description="Cooperation will be reciprocated",
            truth_status=TruthStatus.TRUE
        ),
        BeliefEntry(
            belief_id="B_TRUTH_VALUED",
            description="Truth-telling is valued by others",
            truth_status=TruthStatus.TRUE
        ),
        BeliefEntry(
            belief_id="B_RESOURCES_SCARCE",
            description="Resources are currently scarce",
            truth_status=TruthStatus.FALSE
        ),
        BeliefEntry(
            belief_id="B_OTHERS_VULNERABLE",
            description="Others are in vulnerable position",
            truth_status=TruthStatus.UNKNOWN
        ),
    ]

    @classmethod
    def get_belief_ids(cls) -> List[str]:
        """Return list of valid belief IDs"""
        return [b.belief_id for b in cls.BELIEFS]

    @classmethod
    def get_belief(cls, belief_id: str) -> BeliefEntry:
        """Get belief entry by ID"""
        for b in cls.BELIEFS:
            if b.belief_id == belief_id:
                return b
        raise KeyError(f"Unknown belief_id: {belief_id}")

    @classmethod
    def is_valid_id(cls, belief_id: str) -> bool:
        """Check if belief ID exists in registry"""
        return belief_id in cls.get_belief_ids()


class PreferenceRegistryV010:
    """
    Fixed preference registry for v0.1.

    These preferences define normative constraints on action selection.
    """

    PREFERENCES = [
        PreferenceEntry(
            pref_id="P_NO_DEFECT",
            description="Do not defect in cooperative situations",
            strength=PreferenceStrength.STRONG,
            violated_by_actions={"DEFECT"}
        ),
        PreferenceEntry(
            pref_id="P_NO_BREAK_LOCKS",
            description="Do not break locks or bypass security",
            strength=PreferenceStrength.STRONG,
            violated_by_actions={"BREAK_LOCK"}
        ),
        PreferenceEntry(
            pref_id="P_NO_LIE",
            description="Do not lie or deceive",
            strength=PreferenceStrength.STRONG,
            violated_by_actions={"LIE"}
        ),
        PreferenceEntry(
            pref_id="P_NO_HOARD",
            description="Do not hoard resources unnecessarily",
            strength=PreferenceStrength.MODERATE,
            violated_by_actions={"HOARD"}
        ),
        PreferenceEntry(
            pref_id="P_NO_EXPLOIT",
            description="Do not exploit vulnerable parties",
            strength=PreferenceStrength.STRONG,
            violated_by_actions={"EXPLOIT"}
        ),
        PreferenceEntry(
            pref_id="P_PREFER_COOPERATION",
            description="Prefer cooperative actions when available",
            strength=PreferenceStrength.MODERATE,
            violated_by_actions=set()  # Aspirational, not violated
        ),
    ]

    @classmethod
    def get_pref_ids(cls) -> List[str]:
        """Return list of valid preference IDs"""
        return [p.pref_id for p in cls.PREFERENCES]

    @classmethod
    def get_preference(cls, pref_id: str) -> PreferenceEntry:
        """Get preference entry by ID"""
        for p in cls.PREFERENCES:
            if p.pref_id == pref_id:
                return p
        raise KeyError(f"Unknown pref_id: {pref_id}")

    @classmethod
    def is_valid_id(cls, pref_id: str) -> bool:
        """Check if preference ID exists in registry"""
        return pref_id in cls.get_pref_ids()

    @classmethod
    def get_violated_by_action(cls, action_id: str) -> List[str]:
        """Get list of preference IDs violated by given action"""
        violated = []
        for p in cls.PREFERENCES:
            if action_id in p.violated_by_actions:
                violated.append(p.pref_id)
        return violated


@dataclass
class NormativeState:
    """
    Persistent normative state for MVRA.

    Owned by agent, not modifiable by environment.
    """
    agent_id: str
    continuity_counter: int
    belief_registry: List[BeliefEntry]
    preference_registry: List[PreferenceEntry]

    # Track justification history (references only)
    justification_trace: List[str]  # List of artifact digests

    def __init__(self, agent_id: str = "MVRA_V010"):
        self.agent_id = agent_id
        self.continuity_counter = 0
        self.belief_registry = BeliefRegistryV010.BELIEFS.copy()
        self.preference_registry = PreferenceRegistryV010.PREFERENCES.copy()
        self.justification_trace = []

    def increment_step(self):
        """Advance continuity counter"""
        self.continuity_counter += 1

    def add_justification_digest(self, digest: str):
        """Record justification in trace"""
        self.justification_trace.append(digest)

    def get_belief_ids(self) -> List[str]:
        """Get list of all belief IDs"""
        return [b.belief_id for b in self.belief_registry]

    def get_pref_ids(self) -> List[str]:
        """Get list of all preference IDs"""
        return [p.pref_id for p in self.preference_registry]

    def update_belief_status(self, belief_id: str, status: TruthStatus):
        """Update belief truth status (values may change, IDs may not)"""
        for b in self.belief_registry:
            if b.belief_id == belief_id:
                b.truth_status = status
                return
        raise KeyError(f"Unknown belief_id: {belief_id}")

    def to_dict(self) -> Dict:
        """Export state for logging"""
        return {
            "agent_id": self.agent_id,
            "continuity_counter": self.continuity_counter,
            "beliefs": [b.to_dict() for b in self.belief_registry],
            "preferences": [p.to_dict() for p in self.preference_registry],
            "justification_count": len(self.justification_trace),
        }
