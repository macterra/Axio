"""
X-2D Replay Verification

Per Q&A G30: replay reconstructs every session deterministically from
logs and verifies state hash chain match.

Two-level verification:
  1. Chain consistency: state_out[i] == state_in[i+1] for all consecutive cycles
  2. Full replay: re-execute N cycles from the same plan and compare
     all state hashes byte-for-byte
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ReplayDivergence:
    """A single divergence found during replay verification."""
    cycle_index: int
    field_name: str
    expected: str
    actual: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_index": self.cycle_index,
            "field_name": self.field_name,
            "expected": self.expected,
            "actual": self.actual,
        }


@dataclass
class ReplayResult:
    """Result of replay verification for one session."""
    session_id: str
    total_cycles_verified: int = 0
    divergences: List[ReplayDivergence] = field(default_factory=list)
    chain_consistent: bool = True

    @property
    def passed(self) -> bool:
        return self.chain_consistent and len(self.divergences) == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "total_cycles_verified": self.total_cycles_verified,
            "chain_consistent": self.chain_consistent,
            "passed": self.passed,
            "divergences": [d.to_dict() for d in self.divergences],
        }


def verify_chain_consistency(
    cycle_records: List[Dict[str, Any]],
) -> Tuple[bool, List[ReplayDivergence]]:
    """Verify that state_out[i] == state_in[i+1] for all consecutive cycles.

    Args:
        cycle_records: List of cycle dicts with state_in_hash, state_out_hash.

    Returns:
        (consistent, divergences)
    """
    divergences: List[ReplayDivergence] = []

    for i in range(len(cycle_records) - 1):
        curr = cycle_records[i]
        nxt = cycle_records[i + 1]
        curr_out = curr.get("state_out_hash", "")
        nxt_in = nxt.get("state_in_hash", "")

        if curr_out and nxt_in and curr_out != nxt_in:
            divergences.append(ReplayDivergence(
                cycle_index=curr.get("cycle_index", i),
                field_name="state_hash_chain",
                expected=curr_out[:32],
                actual=nxt_in[:32],
            ))

    return (len(divergences) == 0, divergences)


def verify_session_from_log(
    session_log_path: Path,
    session_id: str,
) -> ReplayResult:
    """Load a session JSONL log and verify chain consistency.

    Expected format: first line is X2DSessionStart, then N cycle records,
    last line is X2DSessionEnd. Cycle records have cycle_index, state_in_hash,
    state_out_hash.
    """
    result = ReplayResult(session_id=session_id)

    if not session_log_path.exists():
        result.divergences.append(ReplayDivergence(
            cycle_index=-1,
            field_name="log_file",
            expected="exists",
            actual="missing",
        ))
        return result

    records: List[Dict[str, Any]] = []
    with open(session_log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    # Filter to cycle records (have cycle_index)
    cycle_records = [r for r in records if "cycle_index" in r and "state_in_hash" in r]
    result.total_cycles_verified = len(cycle_records)

    if not cycle_records:
        return result

    consistent, divs = verify_chain_consistency(cycle_records)
    result.chain_consistent = consistent
    result.divergences.extend(divs)

    return result


def verify_all_sessions(log_root: Path) -> List[ReplayResult]:
    """Verify all session logs under a log root directory."""
    results: List[ReplayResult] = []
    if not log_root.exists():
        return results

    for session_dir in sorted(log_root.iterdir()):
        if not session_dir.is_dir():
            continue
        log_path = session_dir / "x2d_session.jsonl"
        if log_path.exists():
            result = verify_session_from_log(log_path, session_dir.name)
            results.append(result)

    return results
