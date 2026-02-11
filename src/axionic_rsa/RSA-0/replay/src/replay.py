"""
RSA-0 Phase X — Replay Harness

Replays from logs: re-executes admission, selection, and warrant issuance.
Verifies determinism by comparing replayed decisions against logged decisions.
Does NOT re-execute side effects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from kernel.src.artifacts import (
    ActionRequest,
    Author,
    CandidateBundle,
    DecisionType,
    InternalState,
    Justification,
    Observation,
    ObservationKind,
    ScopeClaim,
    canonical_json,
)
from kernel.src.constitution import Constitution
from kernel.src.policy_core import PolicyOutput, policy_core


@dataclass
class ReplayResult:
    cycle_index: int
    original_decision_type: str
    replayed_decision_type: str
    match: bool
    original_warrant_id: Optional[str] = None
    replayed_warrant_id: Optional[str] = None
    detail: str = ""


def load_log_lines(log_path: Path) -> List[Dict[str, Any]]:
    """Load JSONL log file into list of dicts."""
    lines = []
    if not log_path.exists():
        return lines
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(json.loads(line))
    return lines


def group_by_cycle(entries: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """Group log entries by cycle_id."""
    groups: Dict[int, List[Dict[str, Any]]] = {}
    for entry in entries:
        cid = entry.get("cycle_id", -1)
        groups.setdefault(cid, []).append(entry)
    return groups


def reconstruct_observations(cycle_obs_entries: List[Dict[str, Any]]) -> List[Observation]:
    """Reconstruct Observation objects from logged observation entries."""
    observations = []
    for entry in cycle_obs_entries:
        obs_data = entry.get("observation", {})
        obs = Observation(
            kind=obs_data.get("kind", ""),
            payload=obs_data.get("payload", {}),
            author=obs_data.get("author", ""),
            created_at=obs_data.get("created_at", ""),
            id=obs_data.get("id", ""),
        )
        observations.append(obs)
    return observations


def reconstruct_candidates(cycle_artifact_entries: List[Dict[str, Any]]) -> List[CandidateBundle]:
    """
    Reconstruct candidate bundles from logged artifact entries.
    Groups ActionRequests with their ScopeClaims and Justifications.
    """
    action_requests = []
    scope_claims = {}
    justifications = {}

    for entry in cycle_artifact_entries:
        artifact = entry.get("artifact", {})
        atype = artifact.get("type", "")

        if atype == "ActionRequest":
            action_requests.append(artifact)
        elif atype == "ScopeClaim":
            # Key by created_at to associate with nearby ActionRequest
            scope_claims[artifact.get("id", "")] = artifact
        elif atype == "Justification":
            justifications[artifact.get("id", "")] = artifact

    # Build bundles — simplified: pair sequentially
    bundles = []
    sc_list = list(scope_claims.values())
    j_list = list(justifications.values())

    for i, ar_data in enumerate(action_requests):
        ar = ActionRequest(
            action_type=ar_data.get("action_type", ""),
            fields=ar_data.get("fields", {}),
            author=ar_data.get("author", ""),
            created_at=ar_data.get("created_at", ""),
            id=ar_data.get("id", ""),
        )

        sc = None
        if i < len(sc_list):
            sc_data = sc_list[i]
            sc = ScopeClaim(
                observation_ids=sc_data.get("observation_ids", []),
                claim=sc_data.get("claim", ""),
                clause_ref=sc_data.get("clause_ref", ""),
                author=sc_data.get("author", ""),
                created_at=sc_data.get("created_at", ""),
                id=sc_data.get("id", ""),
            )

        just = None
        if i < len(j_list):
            j_data = j_list[i]
            just = Justification(
                text=j_data.get("text", ""),
                author=j_data.get("author", ""),
                created_at=j_data.get("created_at", ""),
                id=j_data.get("id", ""),
            )

        # Extract citations from logged data (look for them in the execution trace)
        citations = ar_data.get("authority_citations", [])

        bundles.append(CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=just,
            authority_citations=citations,
        ))

    return bundles


def replay(repo_root: str) -> List[ReplayResult]:
    """
    Replay all logged cycles. Returns list of ReplayResults.
    """
    root = Path(repo_root).resolve()
    logs_dir = root / "logs"

    # Load constitution
    yaml_path = root / "artifacts" / "phase-x" / "constitution" / "rsa_constitution.v0.1.1.yaml"
    constitution = Constitution(str(yaml_path))

    # Load logs
    obs_entries = load_log_lines(logs_dir / "observations.jsonl")
    artifact_entries = load_log_lines(logs_dir / "artifacts.jsonl")
    exec_entries = load_log_lines(logs_dir / "execution_trace.jsonl")

    obs_by_cycle = group_by_cycle(obs_entries)
    art_by_cycle = group_by_cycle(artifact_entries)
    exec_by_cycle = group_by_cycle(exec_entries)

    # Determine cycle range
    all_cycles = sorted(set(obs_by_cycle.keys()) | set(exec_by_cycle.keys()))

    results: List[ReplayResult] = []
    state = InternalState()

    for cycle_idx in all_cycles:
        if cycle_idx < 0:
            continue

        # Reconstruct observations
        cycle_obs = reconstruct_observations(obs_by_cycle.get(cycle_idx, []))

        # Reconstruct candidates from artifacts
        cycle_arts = art_by_cycle.get(cycle_idx, [])
        # Filter to only ActionRequest/ScopeClaim/Justification (not RefusalRecord, ExitRecord, Warrant)
        candidate_arts = [
            e for e in cycle_arts
            if e.get("artifact", {}).get("type") in ("ActionRequest", "ScopeClaim", "Justification")
        ]
        candidates = reconstruct_candidates(candidate_arts)

        # Get original decision from execution trace
        cycle_exec = exec_by_cycle.get(cycle_idx, [])
        original_decision_type = ""
        original_warrant_id = None
        for ex in cycle_exec:
            dec = ex.get("decision", {})
            if dec:
                original_decision_type = dec.get("decision_type", "")
                original_warrant_id = dec.get("warrant_id")

        # Replay: run policy core
        output = policy_core(
            observations=cycle_obs,
            constitution=constitution,
            internal_state=state,
            candidates=candidates,
            repo_root=root,
        )

        replayed_decision_type = output.decision.decision_type
        replayed_warrant_id = (
            output.decision.warrant.warrant_id if output.decision.warrant else None
        )

        match = (
            original_decision_type == replayed_decision_type
            and original_warrant_id == replayed_warrant_id
        )

        results.append(ReplayResult(
            cycle_index=cycle_idx,
            original_decision_type=original_decision_type,
            replayed_decision_type=replayed_decision_type,
            match=match,
            original_warrant_id=original_warrant_id,
            replayed_warrant_id=replayed_warrant_id,
            detail="" if match else f"DIVERGENCE at cycle {cycle_idx}",
        ))

        # Advance state
        state = state.advance(replayed_decision_type)

    return results


def main():
    """CLI entry point for replay."""
    import sys

    repo_root = Path(__file__).resolve().parent.parent.parent
    print(f"Replaying from: {repo_root}")
    print(f"Logs dir: {repo_root / 'logs'}")
    print()

    results = replay(str(repo_root))

    all_match = True
    for r in results:
        status = "✓ MATCH" if r.match else "✗ DIVERGENCE"
        print(f"  Cycle {r.cycle_index}: {status}")
        print(f"    Original:  {r.original_decision_type} (warrant: {r.original_warrant_id})")
        print(f"    Replayed:  {r.replayed_decision_type} (warrant: {r.replayed_warrant_id})")
        if not r.match:
            all_match = False
            print(f"    Detail: {r.detail}")

    print()
    if all_match:
        print("REPLAY: ALL CYCLES MATCH — determinism verified.")
    else:
        print("REPLAY: DIVERGENCE DETECTED — Phase X failure.")
        sys.exit(1)


if __name__ == "__main__":
    main()
