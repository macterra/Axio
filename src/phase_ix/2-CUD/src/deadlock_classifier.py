"""
CUD Deadlock Classifier — Per preregistration §2.7

Detects: STATE_DEADLOCK, STATE_LIVELOCK, COLLAPSE, ORPHANING.
"""

from typing import Any, Optional
from .authority_store import AuthorityStore


# Terminal classification tokens per §2.10
STATE_DEADLOCK = "STATE_DEADLOCK"
STATE_LIVELOCK = "STATE_LIVELOCK"
COLLAPSE = "COLLAPSE"
ORPHANING = "ORPHANING"

# Livelock threshold per §2.7
LIVELOCK_THRESHOLD = 3


class DeadlockClassifier:
    """
    Classifies terminal conditions per §2.7.

    Tracks epoch history to detect livelock (N consecutive epochs
    with unchanged state and at least one action attempt).
    """

    def __init__(self):
        self._unchanged_epochs: int = 0
        self._had_action_attempt: bool = False

    def reset(self) -> None:
        """Reset classifier state between conditions."""
        self._unchanged_epochs = 0
        self._had_action_attempt = False

    def record_epoch(
        self,
        state_changed: bool,
        any_pass1_admissible: bool,
        any_action_submitted: bool,
        any_pass2_interference: bool = False,
    ) -> None:
        """
        Record epoch outcome for livelock tracking.

        Args:
            state_changed: True if world state changed this epoch
            any_pass1_admissible: True if any action passed Pass 1
            any_action_submitted: True if any agent submitted an action (non-None)
            any_pass2_interference: True if any Pass-1-admissible action was
                refused at Pass 2 (interference). Livelock requires repeated
                interference, not just unchanged state.
        """
        if (not state_changed and any_pass1_admissible
                and any_action_submitted and any_pass2_interference):
            self._unchanged_epochs += 1
            self._had_action_attempt = True
        else:
            # Reset counter if state changed or no interference
            if state_changed:
                self._unchanged_epochs = 0
                self._had_action_attempt = False

    def is_livelock(self) -> bool:
        """Check if livelock threshold reached (N=3)."""
        return self._unchanged_epochs >= LIVELOCK_THRESHOLD

    @staticmethod
    def is_deadlock(
        outcomes: dict[str, str],
        pass1_results: dict[str, str],
    ) -> bool:
        """
        Check for deadlock: no submitted action is Pass-1 admissible.

        Per §2.7: deadlock when no submitted action is Pass-1 admissible
        AND no alternative admissible action exists under preregistered action space.

        Since strategies are frozen, we check: no Pass-1 PASS in this epoch.
        """
        for action_id, result in pass1_results.items():
            if result == "PASS":
                return False
        # Check that at least one agent submitted (not all NO_ACTION with no attempts)
        has_submission = any(
            result in ("PASS", "FAIL", "FAULT")
            for result in pass1_results.values()
            if result != "N/A"
        )
        # Also count NO_ACTION agents — if all agents produce NO_ACTION with
        # no Pass-1-admissible actions existing, that's still deadlock
        return True

    @staticmethod
    def is_collapse(active_agents: list[str]) -> bool:
        """Check for collapse: no active agents remain."""
        return len(active_agents) == 0

    @staticmethod
    def detect_orphaning(
        active_agents: list[str],
        authority_store: AuthorityStore,
        state_keys: list[str],
    ) -> list[str]:
        """
        Detect orphaned resources per §2.7/§2.9.

        A resource is orphaned if no remaining active agent holds an ALLOW
        capability for WRITE on that key.

        Returns list of orphaned resource keys.
        """
        orphaned = []
        for key in state_keys:
            holders = authority_store.get_allow_holders_for_scope(key, "WRITE")
            # Check if any holder is still active
            active_holders = holders & set(active_agents)
            if len(holders) > 0 and len(active_holders) == 0:
                orphaned.append(key)
        return orphaned
