"""
RSA-0 Phase X — Selector (Procedural, Non-Semantic)

Deterministic canonical selector: choose the admitted candidate bundle
with the lexicographically smallest bundle hash (raw bytes comparison).

No ranking, no heuristics, no natural-language scoring.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .admission import AdmissionResult


@dataclass
class SelectionEvent:
    admitted_bundle_hashes: List[str]
    selected_bundle_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": "selection_event",
            "admitted_bundle_hashes": self.admitted_bundle_hashes,
            "selected_bundle_hash": self.selected_bundle_hash,
        }


def select(admitted: List[AdmissionResult]) -> tuple[Optional[AdmissionResult], Optional[SelectionEvent]]:
    """
    Select the admitted candidate with lexicographically smallest bundle hash
    (raw bytes comparison).

    Returns (selected_result, selection_event) or (None, None) if no candidates.
    """
    if not admitted:
        return None, None

    # Compute (raw_hash_bytes, admission_result) pairs
    pairs = [
        (ar.candidate.bundle_hash(), ar)
        for ar in admitted
    ]

    # Sort by raw bytes (lexicographic on bytes objects)
    pairs.sort(key=lambda x: x[0])

    selected_hash_bytes, selected_result = pairs[0]

    event = SelectionEvent(
        admitted_bundle_hashes=[ar.candidate.bundle_hash_hex() for ar in admitted],
        selected_bundle_hash=selected_hash_bytes.hex(),
    )

    return selected_result, event
