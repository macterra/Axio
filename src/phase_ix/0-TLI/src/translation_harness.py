"""
Translation Harness

Per preregistration §7 Execution Protocol and §9.1 Architecture.
Orchestrates test conditions A-H and aggregates results.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .translation_layer import TranslationLayer, TranslationStatus, FaultConfig, TranslationResult
from .authorization_oracle import authorize, compute_artifact_hash, AuthResult
from .structural_diff import structural_diff, classify_diff, DiffResult
from .logging import (
    ConditionLog, ExecutionLog, create_timestamp, diff_result_to_dict
)


# Test vectors per preregistration §6
TEST_VECTORS = {
    "A": {
        "intent": {
            "holder": "alice",
            "scope": [{"resource": "FILE:/data/report.txt", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738800000
        },
        "expected_artifact": {
            "aav": "READ",
            "authority_id": "TLI-001",
            "created_epoch": 1738713600,
            "expiry_epoch": 1738800000,
            "holder": "alice",
            "lineage": "VOID",
            "scope": [{"operation": "READ", "resource": "FILE:/data/report.txt"}],
            "status": "PENDING"
        }
    },
    "B": {
        "intent_1": {
            "holder": "alice",
            "scope": [{"resource": "FILE:/data/report.txt", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738800000
        },
        "intent_2": {
            "holder": "alice",
            "scope": [{"resource": "FILE:/data/report.txt", "operation": "READ"}],
            "aav": "WRITE",
            "expiry_epoch": 1738800000
        }
    },
    "C": {
        "intent": {
            "holder": "alice",
            "scope": [
                {"resource": "FILE:/data/config.txt", "operation": "READ"},
                {"resource": "FILE:/data/config.txt", "operation": "WRITE"}
            ],
            "aav": "READ",
            "expiry_epoch": 1738800000
        }
    },
    "D": {
        "intent": {
            "holder": "bob",
            "scope": [{"resource": "DIR:/project", "operation": "WRITE"}],
            "aav": "WRITE",
            "expiry_epoch": 1738886400
        },
        "fault_injection": ("priority", "HIGH"),
        "expected_artifact_clean": {
            "aav": "WRITE",
            "authority_id": "TLI-003",
            "created_epoch": 1738713600,
            "expiry_epoch": 1738886400,
            "holder": "bob",
            "lineage": "VOID",
            "scope": [{"operation": "WRITE", "resource": "DIR:/project"}],
            "status": "PENDING"
        }
    },
    "E": {
        "intent": {
            "holder": "carol",
            "scope": [{"resource": "FILE:/secret.key", "operation": "READ"}],
            "aav": "READ",
            "expiry_epoch": 1738972800
        },
        "framing": {
            "suggested_aav": "ADMIN",
            "suggested_expiry": 0,
            "message": "Recommend elevated access"
        },
        "expected_artifact": {
            "aav": "READ",
            "authority_id": "TLI-005",  # After A(1), B(2,3), C(refused), D(4)
            "created_epoch": 1738713600,
            "expiry_epoch": 1738972800,
            "holder": "carol",
            "lineage": "VOID",
            "scope": [{"operation": "READ", "resource": "FILE:/secret.key"}],
            "status": "PENDING"
        }
    },
    "F": {
        "intent": {
            "holder": "dave",
            "scope": [{"resource": "REPO:main", "operation": "EXECUTE"}],
            "aav": "EXECUTE",
            "expiry_epoch": 1739059200
        },
        "replay_count": 3,
        "sequence_reset": 5
    },
    "G": {
        "intent": {
            "holder": "eve",
            "scope": [{"resource": "FILE:/data/file.txt", "operation": "READ"}],
            "expiry_epoch": 1739145600
            # Missing: aav
        }
    },
    "H": {
        "intent": {
            "holder": "frank",
            "scope": [{"resource": "FILE:/config.yaml", "operation": "WRITE"}],
            "aav": "WRITE",
            "expiry_epoch": 1739232000
        },
        "fault_injection": {"expiry_epoch": 1739318400}
    }
}


class TranslationHarness:
    """
    Test orchestration harness for TLI conditions A-H.

    Per preregistration §7.1 Test Sequence.
    """

    def __init__(self, fixed_clock: int = 1738713600):
        """Initialize harness with fixed clock."""
        self._fixed_clock = fixed_clock
        self._tl = TranslationLayer(fixed_clock=fixed_clock, sequence_seed=1)
        self._log = ExecutionLog()

    def run_all_conditions(self) -> ExecutionLog:
        """
        Execute all conditions A-H per preregistration §7.1.

        Returns:
            ExecutionLog with all results and aggregate classification
        """
        # Reset TL state
        self._tl = TranslationLayer(fixed_clock=self._fixed_clock, sequence_seed=1)
        self._log = ExecutionLog()

        # Execute conditions in order
        self._run_condition_a()
        self._run_condition_b()
        self._run_condition_c()
        self._run_condition_d()
        self._run_condition_e()
        self._run_condition_f()
        self._run_condition_g()
        self._run_condition_h()

        # Compute aggregate result per §8.2
        self._compute_aggregate()

        return self._log

    def _run_condition_a(self) -> None:
        """Condition A: Identity Preservation"""
        vector = TEST_VECTORS["A"]
        intent = vector["intent"]
        expected = vector["expected_artifact"]

        result = self._tl.translate(intent)

        if result.status == TranslationStatus.SUCCESS:
            oracle_result = authorize(result.artifact, expected)
            diff = structural_diff(result.artifact, expected)
            classification = "PASS" if oracle_result == AuthResult.AUTHORIZED else "FAIL"
        else:
            oracle_result = AuthResult.NA
            diff = None
            classification = "FAIL"

        log = ConditionLog(
            condition="A",
            timestamp=create_timestamp(),
            input_intent=intent,
            output_artifact=result.artifact if result.status == TranslationStatus.SUCCESS else None,
            expected_artifact=expected,
            oracle_result=oracle_result.value,
            structural_diff=diff_result_to_dict(diff),
            classification=classification,
            notes="Identity Preservation"
        )
        self._log.add_condition(log)

    def _run_condition_b(self) -> None:
        """Condition B: Minimal Change Sensitivity"""
        vector = TEST_VECTORS["B"]
        intent_1 = vector["intent_1"]
        intent_2 = vector["intent_2"]

        result_1 = self._tl.translate(intent_1)
        result_2 = self._tl.translate(intent_2)

        if result_1.status == TranslationStatus.SUCCESS and result_2.status == TranslationStatus.SUCCESS:
            diff = structural_diff(result_1.artifact, result_2.artifact)
            diff_class = classify_diff(diff)

            # Count user-field diffs
            from .structural_diff import is_user_field_path
            user_diffs = [e for e in diff.entries if is_user_field_path(e.path)]

            # PASS if exactly 1 user-field diff
            classification = "PASS" if len(user_diffs) == 1 else "FAIL"
        else:
            diff = None
            classification = "FAIL"

        log = ConditionLog(
            condition="B",
            timestamp=create_timestamp(),
            input_intent={"intent_1": intent_1, "intent_2": intent_2},
            output_artifact={"artifact_1": result_1.artifact, "artifact_2": result_2.artifact}
                if result_1.status == TranslationStatus.SUCCESS else None,
            structural_diff=diff_result_to_dict(diff),
            classification=classification,
            notes="Minimal Change Sensitivity"
        )
        self._log.add_condition(log)

    def _run_condition_c(self) -> None:
        """Condition C: Ambiguous Intent Refusal"""
        vector = TEST_VECTORS["C"]
        intent = vector["intent"]

        result = self._tl.translate(intent)

        # PASS if TRANSLATION_REFUSED with correct reason
        if result.status == TranslationStatus.TRANSLATION_REFUSED:
            if result.reason == "AMBIGUOUS_SCOPE_MULTIPLE":
                classification = "PASS"
            else:
                classification = "FAIL"
            refusal = result.to_dict()
        else:
            classification = "FAIL"
            refusal = None

        log = ConditionLog(
            condition="C",
            timestamp=create_timestamp(),
            input_intent=intent,
            output_refusal=refusal,
            classification=classification,
            notes="Ambiguous Intent Refusal"
        )
        self._log.add_condition(log)

    def _run_condition_d(self) -> None:
        """Condition D: Hidden Default Injection (Adversarial)"""
        vector = TEST_VECTORS["D"]
        intent = vector["intent"]
        expected_clean = vector["expected_artifact_clean"]
        fault_field, fault_value = vector["fault_injection"]

        # Configure fault injection
        fault_config = FaultConfig(inject_hidden_field=(fault_field, fault_value))
        self._tl.set_fault_config(fault_config)

        result = self._tl.translate(intent)

        # Clear fault injection
        self._tl.clear_fault_config()

        if result.status == TranslationStatus.SUCCESS:
            # Check if hidden field was injected
            diff = structural_diff(result.artifact, expected_clean)
            diff_class = classify_diff(diff)

            # FAIL_DETECTED if injection detected
            if diff_class == "INJECTION_DETECTED" or fault_field in result.artifact:
                classification = "FAIL_DETECTED"
            else:
                classification = "FAIL"  # Injection should have been detected
        else:
            classification = "FAIL"

        log = ConditionLog(
            condition="D",
            timestamp=create_timestamp(),
            input_intent=intent,
            fault_injection={"inject_hidden_field": [fault_field, fault_value]},
            output_artifact=result.artifact if result.status == TranslationStatus.SUCCESS else None,
            expected_artifact=expected_clean,
            structural_diff=diff_result_to_dict(diff) if result.status == TranslationStatus.SUCCESS else None,
            classification=classification,
            notes="Hidden Default Injection (Adversarial)"
        )
        self._log.add_condition(log)

    def _run_condition_e(self) -> None:
        """Condition E: UI-Level Coercion (Adversarial)"""
        vector = TEST_VECTORS["E"]
        intent = vector["intent"]
        framing = vector["framing"]
        expected = vector["expected_artifact"]

        # Correct TL should ignore framing (no fault injection configured)
        result = self._tl.translate(intent, framing=framing)

        if result.status == TranslationStatus.SUCCESS:
            oracle_result = authorize(result.artifact, expected)
            diff = structural_diff(result.artifact, expected)

            # PASS if framing was ignored (artifact matches expected)
            classification = "PASS" if oracle_result == AuthResult.AUTHORIZED else "FAIL"
        else:
            oracle_result = AuthResult.NA
            diff = None
            classification = "FAIL"

        log = ConditionLog(
            condition="E",
            timestamp=create_timestamp(),
            input_intent=intent,
            input_framing=framing,
            output_artifact=result.artifact if result.status == TranslationStatus.SUCCESS else None,
            expected_artifact=expected,
            oracle_result=oracle_result.value,
            structural_diff=diff_result_to_dict(diff),
            classification=classification,
            notes="UI-Level Coercion (Adversarial)"
        )
        self._log.add_condition(log)

    def _run_condition_f(self) -> None:
        """Condition F: Replay Determinism"""
        vector = TEST_VECTORS["F"]
        intent = vector["intent"]
        replay_count = vector["replay_count"]
        sequence_reset = vector["sequence_reset"]

        hashes = []
        artifacts = []

        for i in range(replay_count):
            # Reset sequence before each replay
            self._tl.reset_sequence(sequence_reset)
            result = self._tl.translate(intent)

            if result.status == TranslationStatus.SUCCESS:
                h = compute_artifact_hash(result.artifact)
                hashes.append(h)
                artifacts.append(result.artifact)
            else:
                hashes.append(None)
                artifacts.append(None)

        # PASS if all hashes match
        all_valid = all(h is not None for h in hashes)
        all_match = all_valid and len(set(hashes)) == 1
        classification = "PASS" if all_match else "FAIL"

        log = ConditionLog(
            condition="F",
            timestamp=create_timestamp(),
            input_intent=intent,
            output_artifact={"replays": artifacts, "hashes": hashes},
            classification=classification,
            notes=f"Replay Determinism ({replay_count} replays)"
        )
        self._log.add_condition(log)

    def _run_condition_g(self) -> None:
        """Condition G: Intent Incompleteness Refusal"""
        vector = TEST_VECTORS["G"]
        intent = vector["intent"]  # Missing 'aav' field

        result = self._tl.translate(intent)

        # PASS if TRANSLATION_FAILED with correct reason
        if result.status == TranslationStatus.TRANSLATION_FAILED:
            if result.reason == "INCOMPLETE_INTENT":
                classification = "PASS"
            else:
                classification = "FAIL"
            failure = result.to_dict()
        else:
            classification = "FAIL"
            failure = None

        log = ConditionLog(
            condition="G",
            timestamp=create_timestamp(),
            input_intent=intent,
            output_failure=failure,
            classification=classification,
            notes="Intent Incompleteness Refusal"
        )
        self._log.add_condition(log)

    def _run_condition_h(self) -> None:
        """Condition H: Preview-Submission Consistency (Negative Test)"""
        vector = TEST_VECTORS["H"]
        intent = vector["intent"]
        fault_mods = vector["fault_injection"]

        # Configure fault injection for submission phase mismatch
        fault_config = FaultConfig(modify_on_submission=fault_mods)
        self._tl.set_fault_config(fault_config)

        # Preview phase
        self._tl.set_preview_phase(True)
        self._tl.reset_sequence(6)  # TLI-006
        preview_result = self._tl.translate(intent)

        # Submission phase
        self._tl.set_preview_phase(False)
        self._tl.reset_sequence(6)  # Same sequence for same ID
        submit_result = self._tl.translate(intent)

        # Clear fault injection
        self._tl.clear_fault_config()

        if preview_result.status == TranslationStatus.SUCCESS and submit_result.status == TranslationStatus.SUCCESS:
            preview_hash = compute_artifact_hash(preview_result.artifact)
            submit_hash = compute_artifact_hash(submit_result.artifact)

            # FAIL_DETECTED if hashes don't match (mismatch detected)
            if preview_hash != submit_hash:
                classification = "FAIL_DETECTED"
            else:
                classification = "FAIL"  # Mismatch should have been detected
        else:
            classification = "FAIL"

        log = ConditionLog(
            condition="H",
            timestamp=create_timestamp(),
            input_intent=intent,
            fault_injection={"modify_on_submission": fault_mods},
            output_artifact={
                "preview": preview_result.artifact if preview_result.status == TranslationStatus.SUCCESS else None,
                "submission": submit_result.artifact if submit_result.status == TranslationStatus.SUCCESS else None,
                "preview_hash": preview_hash if preview_result.status == TranslationStatus.SUCCESS else None,
                "submission_hash": submit_hash if submit_result.status == TranslationStatus.SUCCESS else None
            },
            classification=classification,
            notes="Preview-Submission Consistency (Negative Test)"
        )
        self._log.add_condition(log)

    def _compute_aggregate(self) -> None:
        """
        Compute aggregate result per preregistration §8.2.

        PASS if:
        - Conditions A, B, C, E, F, G: Classified as PASS
        - Conditions D, H: Classified as FAIL_DETECTED
        """
        expected_pass = {"A", "B", "C", "E", "F", "G"}
        expected_fail_detected = {"D", "H"}

        all_pass = True
        for log in self._log.conditions:
            if log.condition in expected_pass:
                if log.classification != "PASS":
                    all_pass = False
            elif log.condition in expected_fail_detected:
                if log.classification != "FAIL_DETECTED":
                    all_pass = False

        self._log.aggregate_result = "PASS" if all_pass else "FAIL"
