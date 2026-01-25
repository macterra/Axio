"""
RSA-PoC v4.2 — Trace System with Stable TraceEntryID

v4.2 additions:
- TraceEntryID: deterministic hash-based ID for each trace entry
- Contradiction trace entries include blocking_rule_ids
- TraceLog for managing entries across a run
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ============================================================================
# Trace Entry Types
# ============================================================================


class TraceEntryType(str, Enum):
    """Types of trace entries."""
    DELIBERATION = "DELIBERATION"
    COMPILATION = "COMPILATION"
    MASK = "MASK"
    SELECTION = "SELECTION"
    EXECUTION = "EXECUTION"
    CONTRADICTION = "CONTRADICTION"  # v4.2: Normative contradiction detected
    LAW_REPAIR = "LAW_REPAIR"  # v4.2: Law repair attempted
    CONTINUITY_CHECK = "CONTINUITY_CHECK"  # v4.2: Epoch continuity check


# ============================================================================
# TraceEntryID Generation
# ============================================================================


def generate_trace_entry_id(
    run_seed: int,
    episode: int,
    step: int,
    entry_type: str,
    sequence: int = 0
) -> str:
    """
    Generate deterministic TraceEntryID.

    ID = H(run_seed || episode || step || entry_type || sequence)[:16]

    Args:
        run_seed: Seed for the run
        episode: Current episode number
        step: Current step number
        entry_type: Type of trace entry (e.g., "CONTRADICTION")
        sequence: Sequence number for multiple entries of same type at same step

    Returns:
        16-character hex string (64 bits of hash)
    """
    h = hashlib.sha256()
    h.update(f"{run_seed}".encode('utf-8'))
    h.update(f"||{episode}".encode('utf-8'))
    h.update(f"||{step}".encode('utf-8'))
    h.update(f"||{entry_type}".encode('utf-8'))
    h.update(f"||{sequence}".encode('utf-8'))
    return h.hexdigest()[:16]


class TraceEntryID:
    """
    Convenience class for generating trace entry IDs.

    Provides a static method interface for ID generation.
    """

    @staticmethod
    def generate(
        run_seed: int,
        episode: int,
        step: int,
        entry_type: str,
        sequence: int = 0
    ) -> str:
        """Generate deterministic TraceEntryID."""
        return generate_trace_entry_id(
            run_seed=run_seed,
            episode=episode,
            step=step,
            entry_type=entry_type,
            sequence=sequence
        )


# ============================================================================
# Trace Entry
# ============================================================================


@dataclass
class TraceEntry:
    """
    A single trace entry with stable ID.

    v4.2 additions:
    - trace_entry_id: Deterministic stable ID
    - blocking_rule_ids: For CONTRADICTION entries, the rule IDs that block progress
    - active_obligation_target: The obligation target that triggered contradiction
    """
    trace_entry_id: str
    entry_type: TraceEntryType
    run_seed: int
    episode: int
    step: int
    timestamp: str  # ISO format
    data: Dict[str, Any] = field(default_factory=dict)

    # v4.2 fields for CONTRADICTION entries
    blocking_rule_ids: Optional[List[str]] = None
    active_obligation_target: Optional[Dict[str, str]] = None
    progress_actions: Optional[Set[str]] = None
    compiled_permitted_actions: Optional[Set[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "trace_entry_id": self.trace_entry_id,
            "entry_type": self.entry_type.value,
            "run_seed": self.run_seed,
            "episode": self.episode,
            "step": self.step,
            "timestamp": self.timestamp,
            "data": self.data,
        }
        if self.blocking_rule_ids is not None:
            d["blocking_rule_ids"] = self.blocking_rule_ids
        if self.active_obligation_target is not None:
            d["active_obligation_target"] = self.active_obligation_target
        if self.progress_actions is not None:
            d["progress_actions"] = list(self.progress_actions)
        if self.compiled_permitted_actions is not None:
            d["compiled_permitted_actions"] = list(self.compiled_permitted_actions)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TraceEntry":
        return cls(
            trace_entry_id=d["trace_entry_id"],
            entry_type=TraceEntryType(d["entry_type"]),
            run_seed=d["run_seed"],
            episode=d["episode"],
            step=d["step"],
            timestamp=d["timestamp"],
            data=d.get("data", {}),
            blocking_rule_ids=d.get("blocking_rule_ids"),
            active_obligation_target=d.get("active_obligation_target"),
            progress_actions=set(d["progress_actions"]) if d.get("progress_actions") else None,
            compiled_permitted_actions=set(d["compiled_permitted_actions"]) if d.get("compiled_permitted_actions") else None,
        )

    @classmethod
    def create(
        cls,
        run_seed: int,
        episode: int,
        step: int,
        entry_type: TraceEntryType,
        data: Optional[Dict[str, Any]] = None,
        sequence: int = 0,
        blocking_rule_ids: Optional[List[str]] = None,
        active_obligation_target: Optional[Dict[str, str]] = None,
        progress_actions: Optional[Set[str]] = None,
        compiled_permitted_actions: Optional[Set[str]] = None,
    ) -> "TraceEntry":
        """Factory method to create a trace entry with auto-generated ID."""
        trace_id = generate_trace_entry_id(
            run_seed, episode, step, entry_type.value, sequence
        )
        return cls(
            trace_entry_id=trace_id,
            entry_type=entry_type,
            run_seed=run_seed,
            episode=episode,
            step=step,
            timestamp=datetime.utcnow().isoformat() + "Z",
            data=data or {},
            blocking_rule_ids=blocking_rule_ids,
            active_obligation_target=active_obligation_target,
            progress_actions=progress_actions,
            compiled_permitted_actions=compiled_permitted_actions,
        )


# ============================================================================
# Contradiction Entry Helper
# ============================================================================


def create_contradiction_entry(
    run_seed: int,
    episode: int,
    step: int,
    blocking_rule_ids: List[str],
    active_obligation_target: Dict[str, str],
    progress_actions: Set[str],
    compiled_permitted_actions: Set[str],
    sequence: int = 0,
) -> TraceEntry:
    """
    Create a CONTRADICTION trace entry with all required fields.

    This entry is cited by LAW_REPAIR actions (R7).
    """
    return TraceEntry.create(
        run_seed=run_seed,
        episode=episode,
        step=step,
        entry_type=TraceEntryType.CONTRADICTION,
        data={
            "contradiction_detected": True,
            "intersection_empty": True,
        },
        sequence=sequence,
        blocking_rule_ids=blocking_rule_ids,
        active_obligation_target=active_obligation_target,
        progress_actions=progress_actions,
        compiled_permitted_actions=compiled_permitted_actions,
    )


# ============================================================================
# Trace Log
# ============================================================================


class TraceLog:
    """
    Log of trace entries for a run.

    Provides lookup by TraceEntryID for R7 validation.
    """

    def __init__(self, run_seed: int):
        self.run_seed = run_seed
        self._entries: List[TraceEntry] = []
        self._by_id: Dict[str, TraceEntry] = {}
        self._contradiction_count: Dict[Tuple[int, int], int] = {}  # (episode, step) -> count

    def add(self, entry: TraceEntry) -> None:
        """Add an entry to the log."""
        self._entries.append(entry)
        self._by_id[entry.trace_entry_id] = entry

    def get(self, trace_entry_id: str) -> Optional[TraceEntry]:
        """Get entry by ID."""
        return self._by_id.get(trace_entry_id)

    def has(self, trace_entry_id: str) -> bool:
        """Check if entry exists."""
        return trace_entry_id in self._by_id

    def get_contradictions(self, episode: Optional[int] = None) -> List[TraceEntry]:
        """Get all CONTRADICTION entries, optionally filtered by episode."""
        result = [
            e for e in self._entries
            if e.entry_type == TraceEntryType.CONTRADICTION
        ]
        if episode is not None:
            result = [e for e in result if e.episode == episode]
        return result

    def get_latest_contradiction(self) -> Optional[TraceEntry]:
        """Get the most recent CONTRADICTION entry."""
        contradictions = self.get_contradictions()
        return contradictions[-1] if contradictions else None

    def add_contradiction(
        self,
        episode: int,
        step: int,
        blocking_rule_ids: List[str],
        active_obligation_target: Dict[str, str],
        progress_actions: Set[str],
        compiled_permitted_actions: Set[str],
    ) -> TraceEntry:
        """Helper to add a contradiction entry with auto-generated sequence."""
        key = (episode, step)
        sequence = self._contradiction_count.get(key, 0)
        self._contradiction_count[key] = sequence + 1

        entry = create_contradiction_entry(
            run_seed=self.run_seed,
            episode=episode,
            step=step,
            blocking_rule_ids=blocking_rule_ids,
            active_obligation_target=active_obligation_target,
            progress_actions=progress_actions,
            compiled_permitted_actions=compiled_permitted_actions,
            sequence=sequence,
        )
        self.add(entry)
        return entry

    def to_list(self) -> List[Dict[str, Any]]:
        """Serialize all entries to list of dicts."""
        return [e.to_dict() for e in self._entries]

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "TraceEntryType",
    "TraceEntry",
    "TraceLog",
    "generate_trace_entry_id",
    "create_contradiction_entry",
]
