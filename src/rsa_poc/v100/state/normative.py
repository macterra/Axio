"""Normative State for v1.0

Extends v010 registries with precedent tracking for anti-oscillation.
"""

from typing import Set, Dict, Optional, Tuple
from dataclasses import dataclass


# Import v010 registries as base
try:
    from ...v010.state.normative import BeliefRegistryV010, PreferenceRegistryV010
except ImportError:
    try:
        from src.rsa_poc.v010.state.normative import BeliefRegistryV010, PreferenceRegistryV010
    except ImportError:
        # Fallback: define minimal v010 registries inline
        class BeliefRegistryV010:
            """v010 belief registry (fallback)"""
            BELIEFS = {
                "B_COOPERATION_MATTERS",
                "B_LOCKS_PROTECT",
                "B_TRUTH_BUILDS_TRUST",
                "B_SHARING_HELPS",
                "B_HELP_CREATES_GOOD",
                "B_EXPLOITATION_HARMS"
            }

            @classmethod
            def is_valid_belief(cls, belief_id: str) -> bool:
                return belief_id in cls.BELIEFS

        class PreferenceRegistryV010:
            """v010 preference registry (fallback)"""
            PREFERENCES = {
                "P_NO_DEFECT",
                "P_NO_BREAK_LOCKS",
                "P_NO_LIE",
                "P_NO_HOARD",
                "P_NO_EXPLOIT",
                "P_PREFER_COOPERATION"
            }

            @classmethod
            def is_valid_preference(cls, pref_id: str) -> bool:
                return pref_id in cls.PREFERENCES


@dataclass
class PrecedentRecord:
    """
    Structured storage of previous artifact for anti-oscillation.

    Stores only necessary fields, not full artifact.
    """
    authorized_violations: Set[str]
    required_preservations: Set[str]
    conflict_attribution: Set[Tuple[str, str]]  # Canonicalized pairs
    digest: str  # BLAKE2b-128 digest of full artifact
    step: int  # Step at which this artifact was compiled


class NormativeStateV100:
    """
    v1.0 normative state with precedent tracking.

    Maintains:
    - Fixed belief registry (inherited from v010)
    - Fixed preference registry (inherited from v010)
    - Precedent chain for anti-oscillation detection
    """

    def __init__(self):
        """Initialize v1.0 normative state"""
        self.belief_registry = BeliefRegistryV010()
        self.preference_registry = PreferenceRegistryV010()

        # Precedent tracking
        self._precedent_history: list[PrecedentRecord] = []
        self._current_precedent: Optional[PrecedentRecord] = None

    def get_beliefs(self) -> Set[str]:
        """Return all valid belief IDs"""
        if hasattr(self.belief_registry.BELIEFS, '__iter__'):
            # Handle both dict and set cases
            if isinstance(self.belief_registry.BELIEFS, dict):
                return set(self.belief_registry.BELIEFS.keys())
            else:
                # Assume it's a collection of BeliefEntry objects
                return {b.belief_id if hasattr(b, 'belief_id') else str(b)
                       for b in self.belief_registry.BELIEFS}
        return set()

    def get_preferences(self) -> Set[str]:
        """Return all valid preference IDs"""
        if hasattr(self.preference_registry.PREFERENCES, '__iter__'):
            # Handle both dict and set cases
            if isinstance(self.preference_registry.PREFERENCES, dict):
                return set(self.preference_registry.PREFERENCES.keys())
            else:
                # Assume it's a collection of PreferenceEntry objects
                return {p.pref_id if hasattr(p, 'pref_id') else str(p)
                       for p in self.preference_registry.PREFERENCES}
        return set()
        """Check if belief ID is valid"""
        return self.belief_registry.is_valid_belief(belief_id)

    def is_valid_preference(self, pref_id: str) -> bool:
        """Check if preference ID is valid"""
        return self.preference_registry.is_valid_preference(pref_id)

    def record_precedent(
        self,
        authorized_violations: Set[str],
        required_preservations: Set[str],
        conflict_attribution: Set[Tuple[str, str]],
        digest: str,
        step: int
    ):
        """
        Record new precedent artifact.

        This is called after successful compilation to establish
        the precedent for next step's anti-oscillation check.
        """
        precedent = PrecedentRecord(
            authorized_violations=authorized_violations.copy(),
            required_preservations=required_preservations.copy(),
            conflict_attribution=conflict_attribution.copy(),
            digest=digest,
            step=step
        )

        self._precedent_history.append(precedent)
        self._current_precedent = precedent

    def get_precedent(self) -> Optional[Dict[str, any]]:
        """
        Get current precedent for anti-oscillation check.

        Returns structured dict suitable for JCOMP-1.0 compiler:
        {
            "authorized_violations": Set[str],
            "required_preservations": Set[str],
            "conflict_attribution": Set[Tuple[str, str]],
            "digest": str
        }

        Returns None if no precedent exists (first step).
        """
        if self._current_precedent is None:
            return None

        return {
            "authorized_violations": self._current_precedent.authorized_violations.copy(),
            "required_preservations": self._current_precedent.required_preservations.copy(),
            "conflict_attribution": self._current_precedent.conflict_attribution.copy(),
            "digest": self._current_precedent.digest
        }

    def get_precedent_history(self) -> list[PrecedentRecord]:
        """Return full precedent history (for analysis/telemetry)"""
        return self._precedent_history.copy()

    def reset(self):
        """Reset precedent tracking (e.g., between episodes)"""
        self._precedent_history.clear()
        self._current_precedent = None


# Convenience exports matching v010 pattern
BeliefRegistryV100 = BeliefRegistryV010  # Same registry, no changes
PreferenceRegistryV100 = PreferenceRegistryV010  # Same registry, no changes
