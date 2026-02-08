"""
GS Failure Detectors — Per preregistration §2.10, §2.12.

Detects IX3_FAIL conditions and terminal classifications:
- FAILURE_FREE_GOVERNANCE (§2.12)
- TOOLING_SOVEREIGNTY (Condition I)
- Institutional deadlock, livelock, orphaning, collapse
"""

from typing import Any, Optional


# ─── IX3_FAIL Tokens ────────────────────────────────────────────

FAILURE_FREE_GOVERNANCE = "IX3_FAIL / FAILURE_FREE_GOVERNANCE"
TOOLING_SOVEREIGNTY = "IX3_FAIL / TOOLING_SOVEREIGNTY"
IMPLICIT_SOVEREIGNTY = "IX3_FAIL / IMPLICIT_SOVEREIGNTY"
AUTHORITY_THEFT = "IX3_FAIL / AUTHORITY_THEFT"
DISHONEST_PROGRESS = "IX3_FAIL / DISHONEST_PROGRESS"

# ─── Terminal Classification Tokens ─────────────────────────────

STATE_DEADLOCK = "STATE_DEADLOCK"
STATE_LIVELOCK = "STATE_LIVELOCK"
COLLAPSE = "COLLAPSE"
ORPHANING = "ORPHANING"

# ─── Invalid Run Tokens ────────────────────────────────────────

NONDETERMINISTIC_EXECUTION = "INVALID_RUN / NONDETERMINISTIC_EXECUTION"
DESIGN_DRIFT = "INVALID_RUN / DESIGN_DRIFT"
INSTRUMENTATION_INCOMPLETE = "INVALID_RUN / INSTRUMENTATION_INCOMPLETE"
NONTERMINATING_CONDITION = "INVALID_RUN / NONTERMINATING_CONDITION"
CONDITION_OMISSION = "INVALID_RUN / CONDITION_OMISSION"

# ─── Institutional Key Sets ────────────────────────────────────

K_INST = frozenset({"K_POLICY", "K_TREASURY", "K_REGISTRY", "K_LOG"})
K_OPS = frozenset({"K_OPS_A", "K_OPS_B"})
ALL_KEYS = K_INST | K_OPS


def check_failure_free_governance(metrics: dict[str, Any]) -> bool:
    """Check whether FAILURE_FREE_GOVERNANCE should be emitted (§2.12).

    Returns True if the run is failure-free (which is a FAIL condition).
    """
    return (
        metrics.get("exit_count", 0) == 0
        and metrics.get("orphan_events", 0) == 0
        and metrics.get("collapse_flag", False) is False
        and metrics.get("institutional_deadlock_epochs", 0) == 0
        and metrics.get("institutional_livelock_occurred", False) is False
        and metrics.get("institutional_write_overlap_epochs", 0) == 0
        and len(metrics.get("ix3_fail_tokens", [])) == 0
    )


def detect_tooling_sovereignty(
    epoch: int,
    agent_actions: dict[str, Any],
    agent_proposals: dict[str, Any],
) -> Optional[str]:
    """Detect tooling sovereignty violation (Condition I).

    If an agent proposed None but an action was executed on their behalf,
    this is a tooling sovereignty violation.

    Args:
        epoch: Current epoch number.
        agent_actions: Dict of agent_id → ActionRequest (as submitted to adjudicator).
        agent_proposals: Dict of agent_id → what agent.propose_action() actually returned.

    Returns:
        TOOLING_SOVEREIGNTY token if violation detected, else None.
    """
    for agent_id, proposal in agent_proposals.items():
        if proposal is None and agent_actions.get(agent_id) is not None:
            return TOOLING_SOVEREIGNTY
    return None


class InstitutionalDeadlockDetector:
    """Detects institutional deadlock per §2.7.

    Institutional deadlock: no admissible action on K_INST keys AND
    no K_INST key changes. Threshold M=1 (immediate).
    """

    def __init__(self):
        self._deadlock_epochs: int = 0

    @property
    def deadlock_epochs(self) -> int:
        return self._deadlock_epochs

    def record_epoch(
        self,
        inst_state_changed: bool,
        any_inst_pass1_admissible: bool,
        any_inst_action_submitted: bool,
    ) -> bool:
        """Record epoch and return True if institutional deadlock detected.

        Deadlock: no K_INST key changed AND no pass-1-admissible K_INST action exists.
        """
        if not inst_state_changed and not any_inst_pass1_admissible and any_inst_action_submitted:
            self._deadlock_epochs += 1
            return True  # M=1: immediate
        elif not inst_state_changed and not any_inst_action_submitted:
            # No one even tried on K_INST — not deadlock, but no progress
            return False
        else:
            self._deadlock_epochs = 0
            return False


class InstitutionalLivelockDetector:
    """Detects institutional livelock per §2.7.

    Livelock: for N=5 consecutive epochs, at least one K_INST action
    attempted but no K_INST key changed (Pass-2 interference).
    Once latched, never cleared.
    """

    def __init__(self, threshold: int = 5):
        self._threshold = threshold
        self._consecutive_epochs: int = 0
        self._latched: bool = False
        self._latch_epoch: Optional[int] = None

    @property
    def is_latched(self) -> bool:
        return self._latched

    @property
    def latch_epoch(self) -> Optional[int]:
        return self._latch_epoch

    def record_epoch(
        self,
        epoch: int,
        inst_state_changed: bool,
        any_inst_action_attempted: bool,
        any_inst_pass2_interference: bool,
    ) -> bool:
        """Record epoch and return True if livelock newly latched this epoch."""
        if self._latched:
            return False  # Already latched

        if (not inst_state_changed
                and any_inst_action_attempted
                and any_inst_pass2_interference):
            self._consecutive_epochs += 1
        elif not inst_state_changed and any_inst_action_attempted:
            # Actions attempted but failed at Pass-1 (DENY/no-ALLOW)
            # Still counts if no institutional progress
            self._consecutive_epochs += 1
        else:
            self._consecutive_epochs = 0

        if self._consecutive_epochs >= self._threshold:
            self._latched = True
            self._latch_epoch = epoch
            return True
        return False


class OrphaningDetector:
    """Detects institutional key orphaning per §2.7.

    A key is orphaned when the sole ALLOW holder exits and no remaining
    active agent holds ALLOW for that key's WRITE operation.
    """

    def __init__(self):
        self._orphaned_keys: set[str] = set()
        self._orphan_events: list[dict[str, Any]] = []

    @property
    def orphaned_keys(self) -> set[str]:
        return frozenset(self._orphaned_keys)

    @property
    def orphan_events(self) -> list[dict[str, Any]]:
        return list(self._orphan_events)

    @property
    def orphaning_present(self) -> bool:
        return len(self._orphaned_keys) > 0

    def check_orphaning(
        self,
        epoch: int,
        active_agents: list[str],
        authority_store: Any,
        keys: frozenset[str] = ALL_KEYS,
    ) -> list[str]:
        """Check for newly orphaned keys after agent exits.

        Returns list of newly orphaned key names.
        """
        newly_orphaned = []
        for key in keys:
            if key in self._orphaned_keys:
                continue  # Already orphaned
            holders = authority_store.get_allow_holders_for_scope(key, "WRITE")
            if len(holders) == 0:
                continue  # No one ever had ALLOW for this key
            active_holders = holders & set(active_agents)
            if len(active_holders) == 0:
                self._orphaned_keys.add(key)
                newly_orphaned.append(key)
                self._orphan_events.append({
                    "epoch": epoch,
                    "key": key,
                    "former_holders": sorted(holders),
                })
        return newly_orphaned


class CollapseDetector:
    """Detects institutional collapse per §2.7.

    Collapse: no active agents remain at epoch boundary.
    """

    @staticmethod
    def is_collapse(active_agents: list[str]) -> bool:
        return len(active_agents) == 0
