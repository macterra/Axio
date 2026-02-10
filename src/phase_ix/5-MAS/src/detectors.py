"""
MAS Failure Detectors — Per preregistration §9.1–§9.6.

All detectors are pure functions of logged state; none modify agent behavior.

Key scoping: K_INST = {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG} (4 keys).
"""

from typing import Any, Optional

from ._kernel import MASAuthorityStore, K_INST, K_OPS, ALL_KEYS


# ─── Terminal Classification Tokens per §2.10 ──────────────────

STATE_DEADLOCK = "STATE_DEADLOCK"
STATE_LIVELOCK = "STATE_LIVELOCK"
STATE_GOVERNANCE_COLLAPSE = "STATE_GOVERNANCE_COLLAPSE"
COLLAPSE = "COLLAPSE"
ORPHANING = "ORPHANING"

# ─── Failure Tokens per §2.10 ──────────────────────────────────

IX5_FAIL_COVERT_HIERARCHY = "IX5_FAIL / COVERT_HIERARCHY"


class InstitutionalDeadlockDetector:
    """Detects institutional deadlock per §9.1.

    At each epoch: at least one K_INST action submitted AND zero K_INST
    actions executed → counter increments. Else → counter resets.
    Threshold M=2.
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
        """Record epoch. Returns True if deadlock threshold met."""
        if inst_actions_submitted > 0 and inst_actions_executed == 0:
            self._counter += 1
        else:
            self._counter = 0

        self._active = self._counter >= self._threshold
        return self._active


class InstitutionalLivelockDetector:
    """Detects institutional livelock per §9.2.

    For L consecutive epochs: at least one K_INST action submitted AND
    K_INST state unchanged. Permanent latch once triggered. L=5.
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
        """Record epoch. Returns True if livelock newly latched this epoch."""
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

    Triggered by persistent deadlock (D=5) OR livelock latch,
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

    @property
    def persistent_deadlock_counter(self) -> int:
        return self._persistent_deadlock_counter

    def record_epoch(
        self,
        epoch: int,
        deadlock_active: bool,
        livelock_latched: bool,
        active_agent_count: int,
    ) -> bool:
        """Record epoch. Returns True if collapse newly latched."""
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
        authority_store: MASAuthorityStore,
        keys: frozenset[str] = K_INST,
    ) -> list[str]:
        """Check for newly orphaned keys. Returns list of newly orphaned key names."""
        newly_orphaned: list[str] = []
        for key in sorted(keys):
            if key in self._orphaned_keys:
                continue
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
        return len(active_agents) == 0


class CovertHierarchyDetector:
    """Detects authority violations per §9.6.

    Kernel correctness validator: fires iff any EXECUTED outcome occurs
    for an agent without ALLOW for the target key. Authority-violation only
    (collision-bias clause removed under JAF, A-M5).
    """

    def __init__(self):
        self._fired: bool = False
        self._violations: list[dict[str, Any]] = []

    @property
    def fired(self) -> bool:
        return self._fired

    @property
    def violations(self) -> list[dict[str, Any]]:
        return list(self._violations)

    def check_epoch(
        self,
        epoch: int,
        actions: dict[str, Any],
        outcomes: dict[str, str],
        authority_store: MASAuthorityStore,
    ) -> bool:
        """Check for authority violations. Returns True if violation found.

        Args:
            epoch: Current epoch number.
            actions: dict of agent_id → ActionRequest or None.
            outcomes: dict of agent_id → outcome token.
            authority_store: The authority store.
        """
        from ._kernel import EXECUTED
        found = False
        for agent_id, outcome in outcomes.items():
            if outcome != EXECUTED:
                continue
            action = actions.get(agent_id)
            if action is None:
                continue
            for key in action.declared_scope:
                if not authority_store.has_allow(agent_id, key):
                    self._fired = True
                    found = True
                    self._violations.append({
                        "epoch": epoch,
                        "agent_id": agent_id,
                        "key": key,
                        "token": IX5_FAIL_COVERT_HIERARCHY,
                    })
        return found
