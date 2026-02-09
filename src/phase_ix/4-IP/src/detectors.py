"""
IP Failure Detectors — Per preregistration §9.1–§9.5.

All detectors are pure functions of logged state; none modify agent behavior.

Key scoping: K_INST = {K_POLICY, K_TREASURY, K_REGISTRY} (3 keys).
K_LOG is excluded from K_INST per §2.4 note.
"""

from typing import Any, Optional

from ._kernel import IPAuthorityStore


# ─── Key Sets per §2.4 ─────────────────────────────────────────

K_INST = frozenset({"K_POLICY", "K_TREASURY", "K_REGISTRY"})
K_OPS = frozenset({"K_OPS_A", "K_OPS_B"})
K_LOG_SET = frozenset({"K_LOG"})
ALL_KEYS = K_INST | K_OPS | K_LOG_SET

# ─── Terminal Classification Tokens per §2.10 ──────────────────

STATE_DEADLOCK = "STATE_DEADLOCK"
STATE_LIVELOCK = "STATE_LIVELOCK"
STATE_GOVERNANCE_COLLAPSE = "STATE_GOVERNANCE_COLLAPSE"
COLLAPSE = "COLLAPSE"
ORPHANING = "ORPHANING"


class InstitutionalDeadlockDetector:
    """Detects institutional deadlock per §9.1.

    Deadlock: at each epoch, at least one action targeting K_INST is
    submitted AND zero K_INST actions are executed. Threshold M=2.
    """

    def __init__(self, threshold: int = 2):
        self._threshold = threshold
        self._counter: int = 0
        self._active: bool = False

    @property
    def counter(self) -> int:
        return self._counter

    @property
    def is_active(self) -> bool:
        return self._active

    def record_epoch(
        self,
        inst_actions_submitted: int,
        inst_actions_executed: int,
    ) -> bool:
        """Record epoch and return True if deadlock newly detected.

        Args:
            inst_actions_submitted: Count of actions targeting K_INST this epoch.
            inst_actions_executed: Count of executed actions targeting K_INST.
        """
        if inst_actions_submitted > 0 and inst_actions_executed == 0:
            self._counter += 1
        else:
            self._counter = 0

        self._active = self._counter >= self._threshold
        return self._active


class InstitutionalLivelockDetector:
    """Detects institutional livelock per §9.2.

    For L=5 consecutive epochs: at least one K_INST action submitted AND
    K_INST state unchanged. Permanent latch once triggered.
    """

    def __init__(self, threshold: int = 5):
        self._threshold = threshold
        self._counter: int = 0
        self._latched: bool = False
        self._latch_epoch: Optional[int] = None

    @property
    def is_latched(self) -> bool:
        return self._latched

    @property
    def latch_epoch(self) -> Optional[int]:
        return self._latch_epoch

    @property
    def counter(self) -> int:
        return self._counter

    def record_epoch(
        self,
        epoch: int,
        inst_state_changed: bool,
        inst_actions_submitted: int,
    ) -> bool:
        """Record epoch and return True if livelock newly latched.

        Args:
            epoch: Current epoch number.
            inst_state_changed: Whether any K_INST key changed this epoch.
            inst_actions_submitted: Count of actions targeting K_INST.
        """
        if self._latched:
            return False  # Permanent

        if inst_actions_submitted > 0 and not inst_state_changed:
            self._counter += 1
        else:
            self._counter = 0

        if self._counter >= self._threshold:
            self._latched = True
            self._latch_epoch = epoch
            return True
        return False


class GovernanceCollapseDetector:
    """Detects governance collapse per §9.3.

    Triggered by persistent deadlock (D=5 epochs) OR livelock latch,
    with at least one active agent. Permanent latch.
    """

    def __init__(self, threshold: int = 5):
        self._threshold = threshold
        self._persistent_deadlock_counter: int = 0
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
        deadlock_active: bool,
        livelock_latched: bool,
        active_agent_count: int,
    ) -> bool:
        """Record epoch and return True if governance collapse newly latched.

        Args:
            epoch: Current epoch number.
            deadlock_active: Whether STATE_DEADLOCK is currently active.
            livelock_latched: Whether livelock is latched.
            active_agent_count: Number of active agents.
        """
        if self._latched:
            return False

        if deadlock_active:
            self._persistent_deadlock_counter += 1
        else:
            self._persistent_deadlock_counter = 0

        collapse_trigger = (
            (self._persistent_deadlock_counter >= self._threshold)
            or livelock_latched
        )

        if collapse_trigger and active_agent_count >= 1:
            self._latched = True
            self._latch_epoch = epoch
            return True
        return False


class OrphaningDetector:
    """Detects institutional key orphaning per §9.4.

    A key is orphaned when no active agent holds ALLOW for it.
    Checked after exit processing.
    """

    def __init__(self):
        self._orphaned_keys: set[str] = set()
        self._orphan_events: list[dict[str, Any]] = []

    @property
    def orphaned_keys(self) -> frozenset[str]:
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
        authority_store: IPAuthorityStore,
        keys: frozenset[str] = K_INST,
    ) -> list[str]:
        """Check for newly orphaned keys. Returns list of newly orphaned key names."""
        newly_orphaned: list[str] = []
        for key in sorted(keys):
            if key in self._orphaned_keys:
                continue  # Already orphaned
            holders = authority_store.get_allow_holders_for_scope(key, "WRITE")
            active_holders = holders & set(active_agents)
            if len(active_holders) == 0:
                self._orphaned_keys.add(key)
                self._orphan_events.append({
                    "epoch": epoch,
                    "key": key,
                    "type": "ORPHANED_KEY",
                })
                newly_orphaned.append(key)
        return newly_orphaned


class AgentCollapseDetector:
    """Detects agent collapse (all agents exited) per §9.5."""

    @staticmethod
    def is_collapse(active_agents: list[str]) -> bool:
        """Return True if no active agents remain."""
        return len(active_agents) == 0
