"""
VEWA Harness: Test orchestration, condition execution, fault injection.

Per preregistration §6.1, §8.2, §8.3:
- Executes conditions A-F per test vectors
- Reinitializes authority system per condition (§6.1 step a)
- Resets sequence counter per condition (§6.2)
- Manages fault injection for D, E, F
- Logs results per §6.3
"""

import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .canonical import canonicalize
from .value_encoding import ValueEncodingHarness
from .conflict_probe import (
    AuthorityStore, ConflictProbe, ConflictRecord,
    DeadlockRecord, AdmissibilityResult,
)
from .structural_diff import structural_diff, DiffResult
from .logging import (
    VEWAConditionLog, VEWAExecutionLog,
    create_timestamp, diff_result_to_dict,
)


# Fixed clock per §6.2
FIXED_CLOCK = 1738713600


@dataclass
class VEWAFaultConfig:
    """
    Fault injection configuration per §8.3.

    inject_priority_field: (field_name, value) to inject on first artifact — Condition D
    permute_injection_order: run all permutations — Condition E
    inject_post_epoch_authority: artifact dict to inject after epoch 0 — Condition F
    """
    inject_priority_field: Optional[Tuple[str, Any]] = None
    permute_injection_order: bool = False
    inject_post_epoch_authority: Optional[Dict[str, Any]] = None


@dataclass
class ConditionResult:
    """Result of executing a single condition."""
    condition: str
    classification: str  # IX1_PASS | IX1_FAIL / <reason> | INVALID_RUN / <reason>
    classification_reason: str
    experiment_result: str  # PASS | FAIL
    log: VEWAConditionLog = field(default_factory=lambda: VEWAConditionLog(
        condition="", timestamp=""
    ))


# --- Test Vectors per §4 ---

VECTOR_A = {
    "values": [
        {"value_id": "V_OPEN", "scope": [{"target": "FILE:/data/report.txt", "operation": "READ"}], "commitment": "ALLOW"},
    ],
    "expected_artifacts": [
        {"aav": "READ", "authority_id": "VEWA-001", "commitment": "ALLOW", "created_epoch": FIXED_CLOCK, "expiry_epoch": 0, "holder": "VALUE_AUTHORITY", "lineage": {"encoding_epoch": 0, "type": "VALUE_DECLARATION", "value_id": "V_OPEN"}, "scope": [{"operation": "READ", "target": "FILE:/data/report.txt"}], "status": "ACTIVE"},
    ],
    "actions": [
        {"target": "FILE:/data/report.txt", "operation": "READ"},
    ],
}

VECTOR_B = {
    "values": [
        {"value_id": "V_READ", "scope": [{"target": "FILE:/data/report.txt", "operation": "READ"}], "commitment": "ALLOW"},
        {"value_id": "V_WRITE", "scope": [{"target": "FILE:/data/log.txt", "operation": "WRITE"}], "commitment": "ALLOW"},
    ],
    "expected_artifacts": [
        {"aav": "READ", "authority_id": "VEWA-001", "commitment": "ALLOW", "created_epoch": FIXED_CLOCK, "expiry_epoch": 0, "holder": "VALUE_AUTHORITY", "lineage": {"encoding_epoch": 0, "type": "VALUE_DECLARATION", "value_id": "V_READ"}, "scope": [{"operation": "READ", "target": "FILE:/data/report.txt"}], "status": "ACTIVE"},
        {"aav": "WRITE", "authority_id": "VEWA-002", "commitment": "ALLOW", "created_epoch": FIXED_CLOCK, "expiry_epoch": 0, "holder": "VALUE_AUTHORITY", "lineage": {"encoding_epoch": 0, "type": "VALUE_DECLARATION", "value_id": "V_WRITE"}, "scope": [{"operation": "WRITE", "target": "FILE:/data/log.txt"}], "status": "ACTIVE"},
    ],
    "actions": [
        {"target": "FILE:/data/report.txt", "operation": "READ"},
        {"target": "FILE:/data/log.txt", "operation": "WRITE"},
    ],
}

# Shared conflict values for C, D, E, F
_CONFLICT_VALUES = [
    {"value_id": "V_OPEN", "scope": [{"target": "FILE:/data/secret.txt", "operation": "READ"}], "commitment": "ALLOW"},
    {"value_id": "V_CONF", "scope": [{"target": "FILE:/data/secret.txt", "operation": "READ"}], "commitment": "DENY"},
]

VECTOR_C = {
    "values": _CONFLICT_VALUES,
    "expected_artifacts": [
        {"aav": "READ", "authority_id": "VEWA-001", "commitment": "ALLOW", "created_epoch": FIXED_CLOCK, "expiry_epoch": 0, "holder": "VALUE_AUTHORITY", "lineage": {"encoding_epoch": 0, "type": "VALUE_DECLARATION", "value_id": "V_OPEN"}, "scope": [{"operation": "READ", "target": "FILE:/data/secret.txt"}], "status": "ACTIVE"},
        {"aav": "READ", "authority_id": "VEWA-002", "commitment": "DENY", "created_epoch": FIXED_CLOCK, "expiry_epoch": 0, "holder": "VALUE_AUTHORITY", "lineage": {"encoding_epoch": 0, "type": "VALUE_DECLARATION", "value_id": "V_CONF"}, "scope": [{"operation": "READ", "target": "FILE:/data/secret.txt"}], "status": "ACTIVE"},
    ],
    "actions": [
        {"target": "FILE:/data/secret.txt", "operation": "READ"},
    ],
}

VECTOR_D = {
    "values": _CONFLICT_VALUES,
    "actions": [
        {"target": "FILE:/data/secret.txt", "operation": "READ"},
    ],
    "fault": VEWAFaultConfig(inject_priority_field=("priority", 1)),
}

VECTOR_E = {
    "values": _CONFLICT_VALUES,
    "actions": [
        {"target": "FILE:/data/secret.txt", "operation": "READ"},
    ],
    "fault": VEWAFaultConfig(permute_injection_order=True),
}

VECTOR_F = {
    "values": _CONFLICT_VALUES,
    "actions": [
        {"target": "FILE:/data/secret.txt", "operation": "READ"},
    ],
    "fault": VEWAFaultConfig(
        inject_post_epoch_authority={
            "aav": "READ",
            "authority_id": "VEWA-003",
            "commitment": "ALLOW",
            "created_epoch": FIXED_CLOCK,
            "expiry_epoch": 0,
            "holder": "VALUE_AUTHORITY",
            "lineage": {
                "encoding_epoch": 0,
                "type": "VALUE_DECLARATION",
                "value_id": "V_META_RESPECT_BOTH",
            },
            "scope": [{"operation": "READ", "target": "FILE:/data/secret.txt"}],
            "status": "ACTIVE",
        }
    ),
}

ALL_VECTORS = {
    "A": VECTOR_A,
    "B": VECTOR_B,
    "C": VECTOR_C,
    "D": VECTOR_D,
    "E": VECTOR_E,
    "F": VECTOR_F,
}


class VEWAHarness:
    """
    VEWA test orchestration harness.

    Executes conditions A-F per §6.1 test sequence.
    """

    def __init__(self, fixed_clock: int = FIXED_CLOCK):
        self._fixed_clock = fixed_clock
        self._veh = ValueEncodingHarness(fixed_clock=fixed_clock)
        self._store = AuthorityStore()
        self._probe = ConflictProbe(self._store)

    def _reinitialize(self) -> None:
        """Reinitialize per §6.1 step a."""
        self._store.reinitialize()
        self._probe.reinitialize()
        self._veh.reset_sequence(1)

    def execute_condition_a(self) -> ConditionResult:
        """Condition A: Single Value Admissibility (Positive Control)."""
        return self._execute_positive("A", VECTOR_A)

    def execute_condition_b(self) -> ConditionResult:
        """Condition B: Multiple Non-Conflicting Values."""
        return self._execute_positive("B", VECTOR_B)

    def execute_condition_c(self) -> ConditionResult:
        """Condition C: Conflicting Values — Deadlock Without Resolution."""
        return self._execute_conflict("C", VECTOR_C)

    def execute_condition_d(self) -> ConditionResult:
        """Condition D: Aggregation Attempt (Adversarial)."""
        return self._execute_aggregation("D", VECTOR_D)

    def execute_condition_e(self) -> ConditionResult:
        """Condition E: Permutation Invariance."""
        return self._execute_permutation("E", VECTOR_E)

    def execute_condition_f(self) -> ConditionResult:
        """Condition F: Meta-Authority Synthesis Attempt (Adversarial)."""
        return self._execute_synthesis("F", VECTOR_F)

    def execute_all(self) -> VEWAExecutionLog:
        """
        Execute all conditions A-F per §6.1.

        Returns complete execution log with aggregate result.
        """
        execution_log = VEWAExecutionLog()

        results = []
        for condition_fn in [
            self.execute_condition_a,
            self.execute_condition_b,
            self.execute_condition_c,
            self.execute_condition_d,
            self.execute_condition_e,
            self.execute_condition_f,
        ]:
            result = condition_fn()
            results.append(result)
            execution_log.add_condition(result.log)

        # Aggregate per §7.2
        all_pass = all(r.experiment_result == "PASS" for r in results)
        if all_pass:
            execution_log.aggregate_result = "IX1_PASS / VALUE_ENCODING_ESTABLISHED"
        else:
            failed = [r.condition for r in results if r.experiment_result == "FAIL"]
            execution_log.aggregate_result = (
                f"IX1_FAIL (conditions {', '.join(failed)} failed)"
            )

        return execution_log

    # --- Private execution methods ---

    def _execute_positive(
        self, condition: str, vector: Dict[str, Any]
    ) -> ConditionResult:
        """Execute a positive condition (A or B)."""
        self._reinitialize()
        timestamp = create_timestamp()
        values = vector["values"]
        expected = vector.get("expected_artifacts", [])
        actions = vector["actions"]

        # Encode
        artifacts = self._veh.encode(values)

        # Verify encoding via structural diff
        diffs = []
        for i, (actual, exp) in enumerate(zip(artifacts, expected)):
            diff = structural_diff(actual, exp)
            diffs.append(diff)

        encoding_ok = all(d.count == 0 for d in diffs)

        # Inject
        for artifact in artifacts:
            err = self._store.inject(artifact)
            if err:
                return self._make_result(
                    condition, timestamp, values, artifacts, expected,
                    actions, diffs, [], [], [],
                    "INVALID_RUN / SCOPE_VIOLATION", err, "FAIL"
                )

        # Detect conflicts
        conflicts = self._probe.detect_conflicts()

        # Evaluate admissibility
        admissibility = [
            self._probe.evaluate_admissibility(a) for a in actions
        ]

        # Check deadlock
        deadlocks = self._probe.check_deadlock(actions)

        # Classify
        no_conflicts = len(conflicts) == 0
        no_deadlocks = len(deadlocks) == 0
        all_admissible = all(r.result == "ACTION_ADMISSIBLE" for r in admissibility)

        if encoding_ok and no_conflicts and no_deadlocks and all_admissible:
            classification = "IX1_PASS"
            reason = "VALUE_ENCODING_ESTABLISHED"
            result = "PASS"
        else:
            reasons = []
            if not encoding_ok:
                reasons.append("encoding mismatch")
            if not no_conflicts:
                reasons.append("unexpected conflict")
            if not no_deadlocks:
                reasons.append("unexpected deadlock")
            if not all_admissible:
                reasons.append("admissibility failure")
            classification = "IX1_FAIL"
            reason = "; ".join(reasons)
            result = "FAIL"

        return self._make_result(
            condition, timestamp, values, artifacts, expected,
            actions, diffs, conflicts, admissibility, deadlocks,
            classification, reason, result
        )

    def _execute_conflict(
        self, condition: str, vector: Dict[str, Any]
    ) -> ConditionResult:
        """Execute Condition C: Conflicting Values — Deadlock."""
        self._reinitialize()
        timestamp = create_timestamp()
        values = vector["values"]
        expected = vector.get("expected_artifacts", [])
        actions = vector["actions"]

        # Encode
        artifacts = self._veh.encode(values)

        # Verify encoding
        diffs = []
        for actual, exp in zip(artifacts, expected):
            diffs.append(structural_diff(actual, exp))

        encoding_ok = all(d.count == 0 for d in diffs)

        # Inject
        for artifact in artifacts:
            self._store.inject(artifact)

        # Detect conflicts
        conflicts = self._probe.detect_conflicts()

        # Evaluate admissibility
        admissibility = [
            self._probe.evaluate_admissibility(a) for a in actions
        ]

        # Check deadlock
        deadlocks = self._probe.check_deadlock(actions)

        # Classify per §7.1 Condition C
        has_conflict = len(conflicts) > 0
        all_refused = all(r.result == "ACTION_REFUSED" for r in admissibility)
        all_conflict_reason = all(
            r.reason == "VALUE_CONFLICT" for r in admissibility
            if r.result == "ACTION_REFUSED"
        )
        has_deadlock = len(deadlocks) > 0

        if encoding_ok and has_conflict and all_refused and all_conflict_reason and has_deadlock:
            classification = "IX1_PASS"
            reason = "VALUE_ENCODING_ESTABLISHED"
            result = "PASS"
        else:
            reasons = []
            if not encoding_ok:
                reasons.append("encoding mismatch")
            if not has_conflict:
                reasons.append("no conflict detected")
            if not all_refused:
                reasons.append("action not refused")
            if not all_conflict_reason:
                reasons.append("wrong refusal reason")
            if not has_deadlock:
                reasons.append("no deadlock entered")
            classification = "IX1_FAIL"
            reason = "; ".join(reasons)
            result = "FAIL"

        return self._make_result(
            condition, timestamp, values, artifacts, expected,
            actions, diffs, conflicts, admissibility, deadlocks,
            classification, reason, result
        )

    def _execute_aggregation(
        self, condition: str, vector: Dict[str, Any]
    ) -> ConditionResult:
        """Execute Condition D: Aggregation Attempt (Adversarial)."""
        self._reinitialize()
        timestamp = create_timestamp()
        values = vector["values"]
        actions = vector["actions"]
        fault: VEWAFaultConfig = vector["fault"]

        # Encode
        artifacts = self._veh.encode(values)

        # Fault injection: add priority field to first artifact
        if fault.inject_priority_field:
            field_name, field_value = fault.inject_priority_field
            artifacts[0][field_name] = field_value

        # Validate artifacts for forbidden fields
        detected = False
        violation_fields = []
        for artifact in artifacts:
            extra = self._probe.validate_artifact_schema(artifact)
            if extra:
                detected = True
                violation_fields.extend(extra)

        fault_info = {
            "type": "inject_priority_field",
            "field": fault.inject_priority_field[0] if fault.inject_priority_field else None,
            "value": fault.inject_priority_field[1] if fault.inject_priority_field else None,
        }

        if detected:
            # Adversarial detection successful → experiment PASS per §3.3
            classification = "IX1_FAIL / VALUE_AGGREGATION"
            reason = f"Forbidden fields detected: {violation_fields}"
            result = "PASS"
        else:
            classification = "IX1_FAIL / DEADLOCK_EVASION"
            reason = "Aggregation injection not detected"
            result = "FAIL"

        log = VEWAConditionLog(
            condition=condition,
            timestamp=timestamp,
            value_declarations=values,
            encoded_artifacts=artifacts,
            candidate_actions=actions,
            fault_injection=fault_info,
            classification=classification,
            classification_reason=reason,
            experiment_result=result,
            notes="Adversarial condition: kernel IX1_FAIL = experiment PASS",
        )

        return ConditionResult(
            condition=condition,
            classification=classification,
            classification_reason=reason,
            experiment_result=result,
            log=log,
        )

    def _execute_permutation(
        self, condition: str, vector: Dict[str, Any]
    ) -> ConditionResult:
        """
        Execute Condition E: Permutation Invariance.

        Per §3.4 Permutation Invariance Criterion:
        - scope_atom must match exactly
        - admissibility result/reason must match exactly
        - deadlock must match exactly
        - conflict records compared by lineage.value_id sets (not authority_id)
        """
        timestamp = create_timestamp()
        values = vector["values"]
        actions = vector["actions"]

        run_results = []

        # Two permutations: original order and reversed
        permutations = [
            list(values),           # E.1: V_OPEN first
            list(reversed(values)), # E.2: V_CONF first
        ]

        for perm_values in permutations:
            self._reinitialize()
            artifacts = self._veh.encode(perm_values)

            for artifact in artifacts:
                self._store.inject(artifact)

            conflicts = self._probe.detect_conflicts()
            admissibility = [
                self._probe.evaluate_admissibility(a) for a in actions
            ]
            deadlocks = self._probe.check_deadlock(actions)

            run_results.append({
                "artifacts": artifacts,
                "conflicts": conflicts,
                "admissibility": admissibility,
                "deadlocks": deadlocks,
            })

        # Compare per Permutation Invariance Criterion (§3.4)
        r1, r2 = run_results

        invariant = True
        divergences = []

        # Compare admissibility results
        for a1, a2 in zip(r1["admissibility"], r2["admissibility"]):
            if a1.result != a2.result:
                invariant = False
                divergences.append(
                    f"admissibility result: {a1.result} vs {a2.result}"
                )
            if a1.reason != a2.reason:
                invariant = False
                divergences.append(
                    f"admissibility reason: {a1.reason} vs {a2.reason}"
                )

        # Compare conflict records by lineage.value_id sets (§3.4)
        def conflict_value_ids(conflicts, store):
            """Extract set of lineage.value_id sets for each conflict."""
            result = []
            for c in conflicts:
                vids = c.lineage_value_ids(store)
                result.append(frozenset(vids))
            return set(result)

        # We need the stores from each run. Re-execute to get them.
        # Actually, we already have the artifacts — rebuild stores to extract lineage.
        def extract_conflict_signatures(conflicts, artifacts):
            """Extract (scope_atom_key, frozenset(value_ids)) for comparison."""
            sigs = set()
            # Build authority_id → value_id mapping from artifacts
            aid_to_vid = {}
            for art in artifacts:
                aid_to_vid[art["authority_id"]] = art["lineage"]["value_id"]

            for c in conflicts:
                scope_key = canonicalize({
                    "operation": c.scope_atom.get("operation", ""),
                    "target": c.scope_atom.get("target", ""),
                })
                vids = frozenset(aid_to_vid.get(aid, "") for aid in c.authorities)
                sigs.add((scope_key, vids))
            return sigs

        sigs1 = extract_conflict_signatures(r1["conflicts"], r1["artifacts"])
        sigs2 = extract_conflict_signatures(r2["conflicts"], r2["artifacts"])

        if sigs1 != sigs2:
            invariant = False
            divergences.append(f"conflict signatures differ: {sigs1} vs {sigs2}")

        # Compare deadlock scope atoms
        def deadlock_scope_keys(deadlocks):
            keys = set()
            for d in deadlocks:
                keys.add(canonicalize({
                    "operation": d.scope_atom.get("operation", ""),
                    "target": d.scope_atom.get("target", ""),
                }))
            return keys

        dk1 = deadlock_scope_keys(r1["deadlocks"])
        dk2 = deadlock_scope_keys(r2["deadlocks"])

        if dk1 != dk2:
            invariant = False
            divergences.append(f"deadlock scope atoms differ: {dk1} vs {dk2}")

        fault_info = {
            "type": "permute_injection_order",
            "permutations": 2,
        }

        if invariant:
            classification = "IX1_PASS"
            reason = "Permutation invariance holds"
            result = "PASS"
        else:
            classification = "IX1_FAIL / IMPLICIT_VALUE"
            reason = f"Permutation divergence: {'; '.join(divergences)}"
            result = "FAIL"

        # Log uses last run's artifacts for reference
        log = VEWAConditionLog(
            condition=condition,
            timestamp=timestamp,
            value_declarations=values,
            encoded_artifacts=r1["artifacts"] + r2["artifacts"],
            candidate_actions=actions,
            fault_injection=fault_info,
            conflict_records=[c.to_dict() for c in r1["conflicts"] + r2["conflicts"]],
            admissibility_results=(
                [a.to_dict() for a in r1["admissibility"]] +
                [a.to_dict() for a in r2["admissibility"]]
            ),
            deadlock_records=(
                [d.to_dict() for d in r1["deadlocks"]] +
                [d.to_dict() for d in r2["deadlocks"]]
            ),
            classification=classification,
            classification_reason=reason,
            experiment_result=result,
            notes="Permutation invariance test: E.1 (original order), E.2 (reversed)",
        )

        return ConditionResult(
            condition=condition,
            classification=classification,
            classification_reason=reason,
            experiment_result=result,
            log=log,
        )

    def _execute_synthesis(
        self, condition: str, vector: Dict[str, Any]
    ) -> ConditionResult:
        """Execute Condition F: Meta-Authority Synthesis Attempt (Adversarial)."""
        self._reinitialize()
        timestamp = create_timestamp()
        values = vector["values"]
        actions = vector["actions"]
        fault: VEWAFaultConfig = vector["fault"]

        # Encode legitimate values at epoch 0
        artifacts = self._veh.encode(values)

        for artifact in artifacts:
            self._store.inject(artifact)

        # Close epoch 0 per §1.3 Value Non-Creation Invariant
        self._store.close_epoch()

        # Attempt post-epoch injection (fault)
        synthesis_detected = False
        injection_error = None
        if fault.inject_post_epoch_authority:
            injection_error = self._store.inject(fault.inject_post_epoch_authority)
            if injection_error == "IX1_FAIL / VALUE_SYNTHESIS":
                synthesis_detected = True

        fault_info = {
            "type": "inject_post_epoch_authority",
            "authority": fault.inject_post_epoch_authority,
        }

        if synthesis_detected:
            classification = "IX1_FAIL / VALUE_SYNTHESIS"
            reason = "Post-epoch authority injection detected and blocked"
            result = "PASS"
        else:
            classification = "IX1_FAIL / DEADLOCK_EVASION"
            reason = "Post-epoch synthesis not detected"
            result = "FAIL"

        log = VEWAConditionLog(
            condition=condition,
            timestamp=timestamp,
            value_declarations=values,
            encoded_artifacts=artifacts,
            candidate_actions=actions,
            fault_injection=fault_info,
            classification=classification,
            classification_reason=reason,
            experiment_result=result,
            notes="Adversarial condition: kernel IX1_FAIL = experiment PASS",
        )

        return ConditionResult(
            condition=condition,
            classification=classification,
            classification_reason=reason,
            experiment_result=result,
            log=log,
        )

    def _make_result(
        self,
        condition: str,
        timestamp: str,
        values: List[Dict],
        artifacts: List[Dict],
        expected: List[Dict],
        actions: List[Dict],
        diffs: List[DiffResult],
        conflicts: List[ConflictRecord],
        admissibility: List[AdmissibilityResult],
        deadlocks: List[DeadlockRecord],
        classification: str,
        reason: str,
        result: str,
        fault_info: Optional[Dict] = None,
    ) -> ConditionResult:
        """Build a ConditionResult with full logging."""
        log = VEWAConditionLog(
            condition=condition,
            timestamp=timestamp,
            value_declarations=values,
            encoded_artifacts=artifacts,
            expected_artifacts=expected,
            candidate_actions=actions,
            fault_injection=fault_info,
            conflict_records=[c.to_dict() for c in conflicts],
            admissibility_results=[a.to_dict() for a in admissibility],
            deadlock_records=[d.to_dict() for d in deadlocks],
            structural_diffs=[diff_result_to_dict(d) for d in diffs],
            classification=classification,
            classification_reason=reason,
            experiment_result=result,
        )

        return ConditionResult(
            condition=condition,
            classification=classification,
            classification_reason=reason,
            experiment_result=result,
            log=log,
        )
