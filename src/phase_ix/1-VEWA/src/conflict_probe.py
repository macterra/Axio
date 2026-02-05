"""
Conflict Probe: Authority Store, Conflict Detection, Admissibility, Deadlock

Per preregistration §2.6, §2.7, §8.2:
- AuthorityStore: holds injected authority artifacts
- ConflictProbe: detects conflicts at injection, evaluates admissibility at probe
- Deadlock detection: scope-bound, per §2.7

Conflict rules (§2.6):
- ALLOW + DENY  → conflict
- DENY  + DENY  → conflict (non-collapse discipline)
- ALLOW + ALLOW → no conflict

Admissibility rules (§2.7):
1. Find matching authorities by scope atom
2. No matching → ACTION_REFUSED (NO_AUTHORITY)
3. Matching + conflict → ACTION_REFUSED (VALUE_CONFLICT)
4. Matching + no conflict + at least one ALLOW → ACTION_ADMISSIBLE
5. Matching + no conflict + all DENY → ACTION_REFUSED (DENIED_BY_AUTHORITY)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .canonical import canonicalize


# --- Data structures ---

@dataclass
class ConflictRecord:
    """
    Conflict record per §2.6 and VECTOR_C.

    scope_atom: canonicalized scope atom dict
    authorities: set of authority_id strings (unordered; §2.6 Conflict Representation Invariant)
    conflict_type: fixed structural constant "MULTI_BINDING" (§2.6, S1 patch)
    registered_epoch: epoch when conflict was detected (always 0 in IX-1)
    """
    scope_atom: Dict[str, Any]
    authorities: Set[str]
    conflict_type: str = "MULTI_BINDING"
    registered_epoch: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dict per §2.6 Set Serialization Rule:
        authorities as lexicographically sorted array.
        """
        return {
            "scope_atom": self.scope_atom,
            "authorities": sorted(self.authorities),
            "conflict_type": self.conflict_type,
            "registered_epoch": self.registered_epoch,
        }

    def lineage_value_ids(self, store: "AuthorityStore") -> Set[str]:
        """
        Get the set of lineage.value_id for all authorities in this conflict.
        Used by Condition E Permutation Invariance Criterion (§3.4).
        """
        value_ids = set()
        for auth_id in self.authorities:
            artifact = store.get_artifact(auth_id)
            if artifact and "lineage" in artifact:
                value_ids.add(artifact["lineage"]["value_id"])
        return value_ids


@dataclass
class DeadlockRecord:
    """
    Deadlock record per §2.7.

    scope_atom: the contested scope atom
    status: always "STATE_DEADLOCK / VALUE_CONFLICT"
    """
    scope_atom: Dict[str, Any]
    status: str = "STATE_DEADLOCK / VALUE_CONFLICT"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scope_atom": self.scope_atom,
            "status": self.status,
        }


@dataclass
class AdmissibilityResult:
    """
    Admissibility evaluation result per §2.7.

    action: the candidate action request
    result: ACTION_ADMISSIBLE or ACTION_REFUSED
    reason: NO_AUTHORITY | VALUE_CONFLICT | DENIED_BY_AUTHORITY | None
    """
    action: Dict[str, Any]
    result: str
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "result": self.result,
            "reason": self.reason,
        }


# --- Authority Store ---

class AuthorityStore:
    """
    In-memory store for authority artifacts.

    Supports injection, lookup by scope atom, and reinitialization (§6.1 step a).
    """

    def __init__(self):
        self._artifacts: Dict[str, Dict[str, Any]] = {}  # authority_id → artifact
        self._epoch_closed: bool = False  # tracks whether epoch 0 is closed

    def reinitialize(self) -> None:
        """
        Reinitialize to clean state per §6.1 step a.
        Clears all artifacts and resets epoch gate.
        """
        self._artifacts.clear()
        self._epoch_closed = False

    def close_epoch(self) -> None:
        """
        Close epoch 0. After this, any injection attempt is a synthesis violation (§1.3).
        """
        self._epoch_closed = True

    @property
    def epoch_closed(self) -> bool:
        return self._epoch_closed

    def inject(self, artifact: Dict[str, Any]) -> Optional[str]:
        """
        Inject an authority artifact into the store.

        Returns:
            None on success; error string if post-epoch injection detected.
        """
        if self._epoch_closed:
            return "IX1_FAIL / VALUE_SYNTHESIS"

        authority_id = artifact.get("authority_id", "")
        self._artifacts[authority_id] = artifact
        return None

    def get_artifact(self, authority_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve artifact by authority_id."""
        return self._artifacts.get(authority_id)

    def get_all_artifacts(self) -> List[Dict[str, Any]]:
        """Get all artifacts in injection order (dict preserves insertion order)."""
        return list(self._artifacts.values())

    def find_by_scope_atom(self, target: str, operation: str) -> List[Dict[str, Any]]:
        """
        Find all artifacts whose scope contains a matching atom.

        Per §2.4 Scope Atom Identity Rule: canonicalized structural equality.
        Per §2.1/§2.2: scope has exactly one atom (maxItems: 1).
        """
        query_atom = canonicalize({"operation": operation, "target": target})
        matches = []
        for artifact in self._artifacts.values():
            scope = artifact.get("scope", [])
            if scope:
                artifact_atom = canonicalize({
                    "operation": scope[0].get("operation", ""),
                    "target": scope[0].get("target", ""),
                })
                if artifact_atom == query_atom:
                    matches.append(artifact)
        return matches


# --- Conflict Probe ---

class ConflictProbe:
    """
    Conflict detection, admissibility evaluation, and deadlock detection.

    Per preregistration §2.6, §2.7.
    """

    def __init__(self, store: AuthorityStore):
        self._store = store
        self._conflicts: List[ConflictRecord] = []
        self._deadlocks: List[DeadlockRecord] = []

    def reinitialize(self) -> None:
        """Clear all conflict and deadlock records (§6.1 step a)."""
        self._conflicts.clear()
        self._deadlocks.clear()

    @property
    def conflicts(self) -> List[ConflictRecord]:
        return list(self._conflicts)

    @property
    def deadlocks(self) -> List[DeadlockRecord]:
        return list(self._deadlocks)

    def _scope_atom_key(self, atom: Dict[str, Any]) -> str:
        """Canonical key for a scope atom, for grouping."""
        return canonicalize({
            "operation": atom.get("operation", ""),
            "target": atom.get("target", ""),
        })

    def detect_conflicts(self) -> List[ConflictRecord]:
        """
        Detect conflicts at injection time (epoch 0) per §2.6.

        Groups authorities by canonicalized scope atom, then checks
        for conflict conditions (anything except ALLOW+ALLOW).

        Returns:
            List of newly registered ConflictRecords.
        """
        # Group artifacts by scope atom
        scope_groups: Dict[str, List[Dict[str, Any]]] = {}
        for artifact in self._store.get_all_artifacts():
            scope = artifact.get("scope", [])
            if scope:
                key = self._scope_atom_key(scope[0])
                if key not in scope_groups:
                    scope_groups[key] = []
                scope_groups[key].append(artifact)

        new_conflicts = []
        for key, artifacts in scope_groups.items():
            if len(artifacts) < 2:
                continue

            # Check if all ALLOW (no conflict per §2.6)
            commitments = {a["commitment"] for a in artifacts}
            if commitments == {"ALLOW"}:
                continue

            # Conflict exists: multiple authorities, not all ALLOW
            authority_ids = {a["authority_id"] for a in artifacts}
            scope_atom = artifacts[0]["scope"][0]

            record = ConflictRecord(
                scope_atom=scope_atom,
                authorities=authority_ids,
                conflict_type="MULTI_BINDING",
                registered_epoch=0,
            )
            new_conflicts.append(record)
            self._conflicts.append(record)

        return new_conflicts

    def is_scope_conflicted(self, target: str, operation: str) -> bool:
        """Check if a scope atom has a registered conflict."""
        query_key = canonicalize({"operation": operation, "target": target})
        for conflict in self._conflicts:
            conflict_key = self._scope_atom_key(conflict.scope_atom)
            if conflict_key == query_key:
                return True
        return False

    def get_conflict_for_scope(self, target: str, operation: str) -> Optional[ConflictRecord]:
        """Get the conflict record for a scope atom, if any."""
        query_key = canonicalize({"operation": operation, "target": target})
        for conflict in self._conflicts:
            conflict_key = self._scope_atom_key(conflict.scope_atom)
            if conflict_key == query_key:
                return conflict
        return None

    def evaluate_admissibility(
        self, action: Dict[str, Any]
    ) -> AdmissibilityResult:
        """
        Evaluate admissibility of a candidate action request per §2.7.

        Args:
            action: Candidate action request {target, operation}.

        Returns:
            AdmissibilityResult with result and typed reason.
        """
        target = action["target"]
        operation = action["operation"]

        # Step 1: Find matching authorities
        matching = self._store.find_by_scope_atom(target, operation)

        # Step 2: No matching authorities
        if not matching:
            return AdmissibilityResult(
                action=action,
                result="ACTION_REFUSED",
                reason="NO_AUTHORITY",
            )

        # Step 3: Conflict registered
        if self.is_scope_conflicted(target, operation):
            return AdmissibilityResult(
                action=action,
                result="ACTION_REFUSED",
                reason="VALUE_CONFLICT",
            )

        # Step 4: At least one ALLOW, no conflict
        has_allow = any(a["commitment"] == "ALLOW" for a in matching)
        if has_allow:
            return AdmissibilityResult(
                action=action,
                result="ACTION_ADMISSIBLE",
                reason=None,
            )

        # Step 5: All DENY, no conflict
        return AdmissibilityResult(
            action=action,
            result="ACTION_REFUSED",
            reason="DENIED_BY_AUTHORITY",
        )

    def check_deadlock(
        self,
        candidate_actions: List[Dict[str, Any]],
    ) -> List[DeadlockRecord]:
        """
        Check for deadlock per §2.7 Deadlock Rule.

        For each conflicted scope, check if any candidate action in the
        harness-provided set is admissible. If none are, enter deadlock.

        Per §2.7 Action Set Binding: only consider the provided candidate set.

        Args:
            candidate_actions: The finite harness-provided action set.

        Returns:
            List of newly registered DeadlockRecords.
        """
        new_deadlocks = []

        for conflict in self._conflicts:
            scope_atom = conflict.scope_atom
            target = scope_atom.get("target", "")
            operation = scope_atom.get("operation", "")

            # Check if any candidate action for this scope is admissible
            has_admissible = False
            for action in candidate_actions:
                if action["target"] == target and action["operation"] == operation:
                    result = self.evaluate_admissibility(action)
                    if result.result == "ACTION_ADMISSIBLE":
                        has_admissible = True
                        break

            if not has_admissible:
                record = DeadlockRecord(scope_atom=scope_atom)
                new_deadlocks.append(record)
                self._deadlocks.append(record)

        return new_deadlocks

    def validate_artifact_schema(self, artifact: Dict[str, Any]) -> List[str]:
        """
        Check for forbidden additional fields (Condition D detection).

        Per §2.2: additionalProperties: false.

        Returns:
            List of forbidden field names found.
        """
        allowed_fields = {
            "authority_id", "holder", "scope", "aav", "commitment",
            "lineage", "created_epoch", "expiry_epoch", "status"
        }
        actual = set(artifact.keys())
        extra = actual - allowed_fields
        return sorted(extra)
