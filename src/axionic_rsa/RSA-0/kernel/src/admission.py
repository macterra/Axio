"""
RSA-0 Phase X — Admission Pipeline

Sequential gates: completeness → authority_citation → scope_claim →
constitution_compliance → io_allowlist.

Every candidate either passes all gates or produces a rejection trace entry.
No silent dropping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .artifacts import (
    ActionType,
    AdmissionGate,
    AdmissionRejectionCode,
    Author,
    CandidateBundle,
    Observation,
    canonical_json,
)
from .constitution import Constitution


# ---------------------------------------------------------------------------
# Trace events
# ---------------------------------------------------------------------------

@dataclass
class AdmissionEvent:
    candidate_id: str
    gate: str  # AdmissionGate value
    result: str  # "pass" | "fail"
    reason_code: str = ""  # AdmissionRejectionCode value, empty on pass

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "event_type": "admission_event",
            "candidate_id": self.candidate_id,
            "gate": self.gate,
            "result": self.result,
        }
        if self.reason_code:
            d["reason_code"] = self.reason_code
        return d


@dataclass
class AdmissionResult:
    """Result of running a single candidate through all gates."""
    candidate: CandidateBundle
    admitted: bool
    events: List[AdmissionEvent] = field(default_factory=list)
    failed_gate: str = ""
    rejection_code: str = ""


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class AdmissionPipeline:
    """
    Runs each candidate through the five sequential gates.
    Returns (admitted_list, rejected_list, all_events).
    """

    def __init__(
        self,
        constitution: Constitution,
        repo_root: Path,
    ):
        self.constitution = constitution
        self.repo_root = repo_root.resolve()

        # Pre-compute absolute allowlists
        self._read_roots = [
            (self.repo_root / p.lstrip("./")).resolve()
            for p in constitution.get_read_paths()
        ]
        self._write_roots = [
            (self.repo_root / p.lstrip("./")).resolve()
            for p in constitution.get_write_paths()
        ]

    def evaluate(
        self,
        candidates: List[CandidateBundle],
        observations: List[Observation],
    ) -> Tuple[List[AdmissionResult], List[AdmissionResult], List[AdmissionEvent]]:
        """
        Run all candidates through the pipeline.
        Returns (admitted, rejected, all_trace_events).
        """
        admitted: List[AdmissionResult] = []
        rejected: List[AdmissionResult] = []
        all_events: List[AdmissionEvent] = []

        for candidate in candidates:
            result = self._evaluate_candidate(candidate, observations)
            all_events.extend(result.events)
            if result.admitted:
                admitted.append(result)
            else:
                rejected.append(result)

        return admitted, rejected, all_events

    def _evaluate_candidate(
        self,
        candidate: CandidateBundle,
        observations: List[Observation],
    ) -> AdmissionResult:
        """Run a single candidate through all five gates in order."""
        cid = candidate.action_request.id
        events: List[AdmissionEvent] = []

        gates = [
            (AdmissionGate.COMPLETENESS, self._gate_completeness),
            (AdmissionGate.AUTHORITY_CITATION, self._gate_authority_citation),
            (AdmissionGate.SCOPE_CLAIM, self._gate_scope_claim),
            (AdmissionGate.CONSTITUTION_COMPLIANCE, self._gate_constitution_compliance),
            (AdmissionGate.IO_ALLOWLIST, self._gate_io_allowlist),
        ]

        for gate_name, gate_fn in gates:
            passed, reason_code = gate_fn(candidate, observations)
            event = AdmissionEvent(
                candidate_id=cid,
                gate=gate_name.value,
                result="pass" if passed else "fail",
                reason_code=reason_code,
            )
            events.append(event)

            if not passed:
                return AdmissionResult(
                    candidate=candidate,
                    admitted=False,
                    events=events,
                    failed_gate=gate_name.value,
                    rejection_code=reason_code,
                )

        return AdmissionResult(
            candidate=candidate,
            admitted=True,
            events=events,
        )

    # --- Gate implementations ---

    def _gate_completeness(
        self,
        candidate: CandidateBundle,
        observations: List[Observation],
    ) -> Tuple[bool, str]:
        """
        Gate 1: Completeness — required artifacts present, required fields present.
        Also enforces kernel-only check as sub-rule.
        """
        ar = candidate.action_request
        at_def = self.constitution.get_action_type_def(ar.action_type)

        # Action type must exist
        if at_def is None:
            return False, AdmissionRejectionCode.INVALID_FIELD.value

        # Kernel-only sub-check
        if at_def.get("kernel_only", False) and ar.author != Author.KERNEL.value:
            return False, AdmissionRejectionCode.KERNEL_ONLY_ACTION.value

        requires = at_def.get("requires", {})

        # Check scope_claim required
        if requires.get("scope_claim", False) and candidate.scope_claim is None:
            return False, AdmissionRejectionCode.MISSING_FIELD.value

        # Check justification required
        if requires.get("justification", False) and candidate.justification is None:
            return False, AdmissionRejectionCode.MISSING_FIELD.value

        # Check authority_citations required
        if requires.get("authority_citations", False) and not candidate.authority_citations:
            return False, AdmissionRejectionCode.MISSING_FIELD.value

        # Check required fields on the action request
        for field_def in at_def.get("required_fields", []):
            fname = field_def["name"]
            if fname not in ar.fields:
                return False, AdmissionRejectionCode.MISSING_FIELD.value

            value = ar.fields[fname]

            # Enum validation
            if field_def.get("type") == "enum":
                allowed = field_def.get("allowed", [])
                if value not in allowed:
                    return False, AdmissionRejectionCode.INVALID_FIELD.value

            # String max_len
            if field_def.get("type") == "string" and "max_len" in field_def:
                if isinstance(value, str) and len(value) > field_def["max_len"]:
                    return False, AdmissionRejectionCode.INVALID_FIELD.value

            # Array<string> max_len_per_item (for jsonl_lines)
            if field_def.get("type") == "array<string>":
                if not isinstance(value, list):
                    return False, AdmissionRejectionCode.INVALID_FIELD.value
                mlpi = field_def.get("max_len_per_item", 0)
                if mlpi:
                    for item in value:
                        if not isinstance(item, str) or len(item) > mlpi:
                            return False, AdmissionRejectionCode.INVALID_FIELD.value

        # LogAppend limits
        if ar.action_type == ActionType.LOG_APPEND.value:
            limits = at_def.get("limits", {})
            lines = ar.fields.get("jsonl_lines", [])
            max_lines = limits.get("max_lines_per_warrant", 50)
            max_chars = limits.get("max_chars_per_line", 10000)
            max_bytes = limits.get("max_bytes_per_warrant", 256000)

            if len(lines) > max_lines:
                return False, AdmissionRejectionCode.INVALID_FIELD.value
            for line in lines:
                if len(line) > max_chars:
                    return False, AdmissionRejectionCode.INVALID_FIELD.value
            total_bytes = sum(len(l.encode("utf-8")) for l in lines)
            if total_bytes > max_bytes:
                return False, AdmissionRejectionCode.INVALID_FIELD.value

        return True, ""

    def _gate_authority_citation(
        self,
        candidate: CandidateBundle,
        observations: List[Observation],
    ) -> Tuple[bool, str]:
        """Gate 2: Authority Citation — citations exist and resolve in constitution."""
        for citation in candidate.authority_citations:
            resolved = self.constitution.resolve_citation(citation)
            if resolved is None:
                return False, AdmissionRejectionCode.CITATION_UNRESOLVABLE.value
        return True, ""

    def _gate_scope_claim(
        self,
        candidate: CandidateBundle,
        observations: List[Observation],
    ) -> Tuple[bool, str]:
        """Gate 3: Scope Claim — exists, references observation IDs, cites clause."""
        at_def = self.constitution.get_action_type_def(candidate.action_request.action_type)
        requires = at_def.get("requires", {}) if at_def else {}

        # If scope_claim not required, pass
        if not requires.get("scope_claim", False):
            return True, ""

        sc = candidate.scope_claim
        if sc is None:
            return False, AdmissionRejectionCode.MISSING_FIELD.value

        # Must have a clause reference
        if not sc.clause_ref:
            return False, AdmissionRejectionCode.MISSING_FIELD.value

        # Clause ref must resolve
        resolved = self.constitution.resolve_citation(sc.clause_ref)
        if resolved is None:
            return False, AdmissionRejectionCode.CITATION_UNRESOLVABLE.value

        # Observation IDs must reference actual observations
        obs_ids = {o.id for o in observations}
        for oid in sc.observation_ids:
            if oid not in obs_ids:
                return False, AdmissionRejectionCode.INVALID_FIELD.value

        return True, ""

    def _gate_constitution_compliance(
        self,
        candidate: CandidateBundle,
        observations: List[Observation],
    ) -> Tuple[bool, str]:
        """Gate 4: Constitution Compliance — action type in closed set, fields conform."""
        ar = candidate.action_request
        allowed_types = self.constitution.get_allowed_action_types()

        if ar.action_type not in allowed_types:
            return False, AdmissionRejectionCode.INVALID_FIELD.value

        # Network check
        if self.constitution.is_network_enabled() is False:
            # No network-related actions (none exist in Phase X, but guard anyway)
            pass

        return True, ""

    def _gate_io_allowlist(
        self,
        candidate: CandidateBundle,
        observations: List[Observation],
    ) -> Tuple[bool, str]:
        """Gate 5: IO/Tool Allowlist — paths under allowlist."""
        ar = candidate.action_request

        if ar.action_type == ActionType.READ_LOCAL.value:
            path_str = ar.fields.get("path", "")
            if not self._is_under_read_allowlist(path_str):
                return False, AdmissionRejectionCode.PATH_NOT_ALLOWLISTED.value

        elif ar.action_type == ActionType.WRITE_LOCAL.value:
            path_str = ar.fields.get("path", "")
            if not self._is_under_write_allowlist(path_str):
                return False, AdmissionRejectionCode.PATH_NOT_ALLOWLISTED.value

        elif ar.action_type == ActionType.LOG_APPEND.value:
            # LogAppend writes to logs/ — check against write allowlist
            log_name = ar.fields.get("log_name", "")
            log_path = str(self.repo_root / "logs" / f"{log_name}.jsonl")
            if not self._is_under_write_allowlist(log_path):
                return False, AdmissionRejectionCode.PATH_NOT_ALLOWLISTED.value

        return True, ""

    # --- Path helpers ---

    def _resolve_path(self, path_str: str) -> Path:
        """Resolve a path relative to repo_root to absolute canonical."""
        p = Path(path_str)
        if not p.is_absolute():
            p = self.repo_root / p
        return p.resolve()

    def _is_under_read_allowlist(self, path_str: str) -> bool:
        resolved = self._resolve_path(path_str)
        return any(
            resolved == root or _is_descendant(resolved, root)
            for root in self._read_roots
        )

    def _is_under_write_allowlist(self, path_str: str) -> bool:
        resolved = self._resolve_path(path_str)
        return any(
            resolved == root or _is_descendant(resolved, root)
            for root in self._write_roots
        )


def _is_descendant(child: Path, parent: Path) -> bool:
    """Check if child is a descendant of parent (both must be resolved)."""
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False
