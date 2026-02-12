"""
X-0L Harness Tests

Comprehensive test suite for the live profiling harness covering:
- LLMClient (mocked)
- Calibration (mocked)
- Cycle runner (integration with mock LLM)
- Candidate parser
- Generators
- Pre-flight checks
- Report generation
- Auto-abort / B₂ enforcement
- L-C forensic outcomes
- Replay verifier
- Selector permutation
- Refusal taxonomy
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

# Ensure repo root is on path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from kernel.src.artifacts import (
    ActionType,
    Author,
    CandidateBundle,
    DecisionType,
    InternalState,
    Observation,
    ObservationKind,
    canonical_json,
)
from kernel.src.constitution import Constitution

from profiling.x0l.harness.src.llm_client import LLMClient, LLMResponse, TransportError
from profiling.x0l.harness.src.cycle_runner import (
    CycleLogEntry,
    LCOutcome,
    LiveConditionRunResult,
    LiveCycleResult,
    RefusalType,
    parse_candidates_from_json,
    run_live_cycle,
)
from profiling.x0l.harness.src.generators import (
    BASE_SYSTEM_TEMPLATE,
    CONDITION_A_TASKS,
    CONDITION_C_ADVERSARIAL,
    CONDITION_D_VERBOSE,
    CONDITION_E_CONFLICT,
    ConditionConfig,
    UserMessageSource,
    make_condition_configs,
)
from profiling.x0l.harness.src.preflight import (
    EXPECTED_CONSTITUTION_SHA256,
    PreflightResult,
    build_session_metadata,
    fuzz_canonicalizer,
    run_preflight,
    verify_canonicalizer_integrity,
    verify_constitution_integrity,
    verify_no_artifact_drift,
)
from profiling.x0l.harness.src.report import (
    _authority_utilization,
    _canonicalization_summary,
    _context_utilization_summary,
    _decision_distribution,
    _gate_breakdown,
    _latency_summary,
    _lc_forensic_summary,
    _recovery_ratio,
    _refusal_taxonomy,
    _token_summary,
    generate_report,
    write_report,
)
from profiling.x0l.harness.src.runner import (
    AUTO_ABORT_THRESHOLD,
    _timestamp_for_cycle,
    check_selector_permutation,
    run_condition,
)
from profiling.x0l.calibration.calibration import (
    CALIBRATION_SYSTEM_MESSAGE,
    CALIBRATION_USER_MESSAGE,
    CalibrationResult,
    run_calibration,
)
from replay.x0l.verifier import (
    ReplayCycleVerification,
    ReplayVerificationResult,
    verify_condition_replay,
)

from canonicalizer.pipeline import canonicalize


# ===================================================================
# Fixtures
# ===================================================================

CONSTITUTION_PATH = (
    REPO_ROOT / "artifacts" / "phase-x" / "constitution"
    / "rsa_constitution.v0.1.1.yaml"
)

SCHEMA_PATH = (
    REPO_ROOT / "artifacts" / "phase-x" / "constitution"
    / "rsa_constitution.v0.1.1.schema.json"
)

CORPUS_PATH = (
    REPO_ROOT / "profiling" / "x0p" / "conditions" / "corpus_B.txt"
)


def _valid_candidate_json(
    msg: str = "hello",
    clause: str = "INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
    obs_id: str = "obs1",
) -> str:
    """Build a valid candidate JSON payload."""
    return json.dumps({
        "candidates": [{
            "action_request": {
                "action_type": "Notify",
                "fields": {"target": "stdout", "message": msg}
            },
            "scope_claim": {
                "observation_ids": [obs_id],
                "claim": "Authorized by cited clause.",
                "clause_ref": f"constitution:v0.1.1#{clause}"
            },
            "justification": {"text": "Authorized by cited clause."},
            "authority_citations": [f"constitution:v0.1.1#{clause}"]
        }]
    })


def _multi_candidate_json(n: int = 3) -> str:
    """Build a multi-candidate JSON payload."""
    candidates = []
    for i in range(n):
        candidates.append({
            "action_request": {
                "action_type": "Notify",
                "fields": {"target": "stdout", "message": f"option_{i}"}
            },
            "scope_claim": {
                "observation_ids": ["obs1"],
                "claim": f"Option {i} authorized.",
                "clause_ref": "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"
            },
            "justification": {"text": f"Justification for option {i}."},
            "authority_citations": [
                "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"
            ]
        })
    return json.dumps({"candidates": candidates})


class MockLLMClient:
    """Deterministic mock LLM client for testing."""

    def __init__(
        self,
        response_text: str = "",
        prompt_tokens: int = 100,
        completion_tokens: int = 50,
        fail_after: int = -1,
    ):
        self.response_text = response_text
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.fail_after = fail_after
        self.call_count = 0
        self.model = "test-model"
        self.max_tokens = 2048
        self.temperature = 0.0

    def call(self, system_message: str, user_message: str) -> LLMResponse:
        self.call_count += 1
        if self.fail_after >= 0 and self.call_count > self.fail_after:
            raise TransportError("Mock transport failure")
        return LLMResponse(
            raw_text=self.response_text,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            total_tokens=self.prompt_tokens + self.completion_tokens,
            model="test-model",
            finish_reason="stop",
        )

    def frozen_params(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "base_url": "http://localhost",
        }


# ===================================================================
# LLMResponse tests
# ===================================================================

class TestLLMResponse:
    def test_auto_hash(self):
        r = LLMResponse(
            raw_text="test",
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            model="m",
        )
        assert len(r.raw_hash) == 64

    def test_hash_determinism(self):
        r1 = LLMResponse(raw_text="abc", prompt_tokens=0, completion_tokens=0,
                          total_tokens=0, model="m")
        r2 = LLMResponse(raw_text="abc", prompt_tokens=0, completion_tokens=0,
                          total_tokens=0, model="m")
        assert r1.raw_hash == r2.raw_hash

    def test_different_text_different_hash(self):
        r1 = LLMResponse(raw_text="a", prompt_tokens=0, completion_tokens=0,
                          total_tokens=0, model="m")
        r2 = LLMResponse(raw_text="b", prompt_tokens=0, completion_tokens=0,
                          total_tokens=0, model="m")
        assert r1.raw_hash != r2.raw_hash


# ===================================================================
# LLMClient construction tests (no real HTTP calls)
# ===================================================================

class TestLLMClientInit:
    def test_no_api_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            # Make sure OPENAI_API_KEY is cleared
            env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                    LLMClient(model="test", api_key="")

    def test_explicit_api_key(self):
        client = LLMClient(model="test", api_key="sk-test123")
        assert client.model == "test"
        assert client.max_tokens == 2048
        assert client.temperature == 0.0

    def test_frozen_params(self):
        client = LLMClient(model="gpt-4", api_key="sk-test", max_tokens=1024)
        params = client.frozen_params()
        assert params["model"] == "gpt-4"
        assert params["max_tokens"] == 1024
        assert params["temperature"] == 0.0


# ===================================================================
# TransportError tests
# ===================================================================

class TestTransportError:
    def test_inherits_from_exception(self):
        assert issubclass(TransportError, Exception)

    def test_message(self):
        err = TransportError("network down")
        assert "network down" in str(err)


# ===================================================================
# Candidate parser tests
# ===================================================================

class TestParseCandidatesFromJson:
    def test_valid_single_candidate(self):
        payload = {
            "candidates": [{
                "action_request": {
                    "action_type": "Notify",
                    "fields": {"target": "stdout", "message": "hi"}
                },
                "scope_claim": {
                    "observation_ids": ["obs1"],
                    "claim": "ok",
                    "clause_ref": "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"
                },
                "justification": {"text": "because"},
                "authority_citations": [
                    "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"
                ]
            }]
        }
        bundles, errors = parse_candidates_from_json(payload)
        assert len(bundles) == 1
        assert errors == 0
        assert bundles[0].action_request.action_type == "Notify"

    def test_empty_candidates(self):
        bundles, errors = parse_candidates_from_json({"candidates": []})
        assert len(bundles) == 0
        assert errors == 0

    def test_missing_candidates_key(self):
        bundles, errors = parse_candidates_from_json({"other": "data"})
        assert len(bundles) == 0
        assert errors == 0

    def test_invalid_candidates_type(self):
        bundles, errors = parse_candidates_from_json({"candidates": "not-a-list"})
        assert len(bundles) == 0
        assert errors == 1

    def test_missing_action_request(self):
        bundles, errors = parse_candidates_from_json({
            "candidates": [{"justification": {"text": "x"}}]
        })
        assert len(bundles) == 0
        assert errors == 1

    def test_missing_action_type(self):
        bundles, errors = parse_candidates_from_json({
            "candidates": [{
                "action_request": {"fields": {}},
            }]
        })
        assert len(bundles) == 0
        assert errors == 1

    def test_multiple_candidates(self):
        payload = {"candidates": [
            {
                "action_request": {"action_type": "Notify",
                                    "fields": {"target": "stdout", "message": "a"}},
                "authority_citations": ["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"]
            },
            {
                "action_request": {"action_type": "Notify",
                                    "fields": {"target": "stdout", "message": "b"}},
                "authority_citations": ["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"]
            },
        ]}
        bundles, errors = parse_candidates_from_json(payload)
        assert len(bundles) == 2
        assert errors == 0

    def test_partial_failures(self):
        payload = {"candidates": [
            {
                "action_request": {"action_type": "Notify",
                                    "fields": {"target": "stdout", "message": "ok"}},
            },
            {
                "bad_key": "no action_request"
            },
        ]}
        bundles, errors = parse_candidates_from_json(payload)
        assert len(bundles) == 1
        assert errors == 1

    def test_no_scope_claim(self):
        """Candidates without scope_claim should still parse."""
        payload = {"candidates": [{
            "action_request": {"action_type": "Notify",
                                "fields": {"target": "stdout", "message": "hi"}},
            "authority_citations": ["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"]
        }]}
        bundles, errors = parse_candidates_from_json(payload)
        assert len(bundles) == 1
        assert bundles[0].scope_claim is None

    def test_no_justification(self):
        payload = {"candidates": [{
            "action_request": {"action_type": "Notify",
                                "fields": {"target": "stdout", "message": "hi"}},
            "scope_claim": {"observation_ids": [], "claim": "x", "clause_ref": "y"},
        }]}
        bundles, errors = parse_candidates_from_json(payload)
        assert len(bundles) == 1
        assert bundles[0].justification is None


# ===================================================================
# Generators tests
# ===================================================================

class TestBaseSystemTemplate:
    def test_contains_clause_ids(self):
        for cid in [
            "INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            "INV-AUTHORITY-CITED",
            "INV-NON-PRIVILEGED-REFLECTION",
            "INV-REPLAY-DETERMINISM",
        ]:
            assert cid in BASE_SYSTEM_TEMPLATE

    def test_contains_io_allowlist(self):
        assert "./artifacts/" in BASE_SYSTEM_TEMPLATE
        assert "./workspace/" in BASE_SYSTEM_TEMPLATE
        assert "./logs/" in BASE_SYSTEM_TEMPLATE

    def test_contains_action_types(self):
        assert "Notify" in BASE_SYSTEM_TEMPLATE
        assert "ReadLocal" in BASE_SYSTEM_TEMPLATE
        assert "WriteLocal" in BASE_SYSTEM_TEMPLATE


class TestUserMessageSource:
    def test_condition_a(self):
        src = UserMessageSource("A", seed=42)
        msg = src.get_message(0)
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_condition_b(self):
        src = UserMessageSource("B", seed=43, corpus_path=CORPUS_PATH)
        msg = src.get_message(0)
        assert isinstance(msg, str)

    def test_condition_b_missing_corpus(self):
        with pytest.raises(FileNotFoundError):
            UserMessageSource("B", seed=43, corpus_path=Path("/nonexistent"))

    def test_condition_c(self):
        src = UserMessageSource("C", seed=44)
        msg = src.get_message(0)
        assert isinstance(msg, str)

    def test_condition_d(self):
        src = UserMessageSource("D", seed=45)
        msg = src.get_message(0)
        assert isinstance(msg, str)

    def test_condition_e(self):
        src = UserMessageSource("E", seed=46)
        msg = src.get_message(0)
        assert isinstance(msg, str)

    def test_unknown_condition(self):
        with pytest.raises(ValueError, match="Unknown condition"):
            UserMessageSource("Z", seed=99)

    def test_template_hash_determinism(self):
        s1 = UserMessageSource("A", seed=42)
        s2 = UserMessageSource("A", seed=99)
        assert s1.template_hash() == s2.template_hash()

    def test_cycling(self):
        src = UserMessageSource("A", seed=42)
        msgs = [src.get_message(i) for i in range(len(CONDITION_A_TASKS) + 1)]
        # Should cycle: task at index n == task at index n + len(tasks)
        assert msgs[0] == msgs[len(CONDITION_A_TASKS)]


class TestMakeConditionConfigs:
    def test_default(self):
        configs = make_condition_configs()
        assert set(configs.keys()) == {"A", "B", "C", "D", "E"}
        assert configs["A"].n_cycles == 100

    def test_custom_n_cycles(self):
        configs = make_condition_configs(n_cycles=10)
        for c in configs.values():
            assert c.n_cycles == 10

    def test_adversarial_flag(self):
        configs = make_condition_configs()
        assert configs["C"].is_adversarial is True
        assert configs["A"].is_adversarial is False

    def test_to_dict(self):
        configs = make_condition_configs(n_cycles=5)
        d = configs["A"].to_dict()
        assert d["condition"] == "A"
        assert d["n_cycles"] == 5


# ===================================================================
# Pre-flight tests
# ===================================================================

class TestPreflightConstitution:
    def test_valid_constitution(self):
        ok, detail = verify_constitution_integrity(CONSTITUTION_PATH)
        assert ok, detail

    def test_nonexistent_file(self):
        ok, detail = verify_constitution_integrity(Path("/nonexistent"))
        assert not ok

    def test_wrong_hash(self):
        ok, detail = verify_constitution_integrity(
            CONSTITUTION_PATH, expected_hash="deadbeef" * 8
        )
        assert not ok


class TestPreflightCanonicalizer:
    def test_integrity(self):
        ok, detail, src_h, test_h = verify_canonicalizer_integrity()
        assert ok
        assert len(src_h) == 64
        assert len(test_h) == 64

    def test_fuzz_passes(self):
        ok, detail = fuzz_canonicalizer()
        assert ok, detail


class TestPreflightArtifactDrift:
    def test_artifacts_exist(self):
        ok, detail = verify_no_artifact_drift(REPO_ROOT)
        assert ok, detail


class TestRunPreflight:
    def test_full_preflight_passes(self):
        result = run_preflight(
            repo_root=REPO_ROOT,
            constitution_path=CONSTITUTION_PATH,
            schema_path=SCHEMA_PATH,
        )
        assert result.passed
        assert len(result.checks) == 5
        assert result.canonicalizer_source_hash != ""
        assert result.canonicalizer_self_test_hash != ""


class TestBuildSessionMetadata:
    def test_metadata_structure(self):
        pf = PreflightResult()
        pf.canonicalizer_source_hash = "a" * 64
        pf.canonicalizer_self_test_hash = "b" * 64

        meta = build_session_metadata(
            repo_root=REPO_ROOT,
            constitution_path=CONSTITUTION_PATH,
            preflight=pf,
            calibration_hash="c" * 64,
            model_params={"model": "test", "temperature": 0.0,
                          "max_tokens": 2048, "base_url": "http://x"},
            run_id="run-1",
            b1=6000,
            b2=150000,
            context_window_size=128000,
        )
        assert meta["run_id"] == "run-1"
        assert meta["per_cycle_token_cap_b1"] == 6000
        assert meta["per_session_token_cap_b2"] == 150000
        assert meta["context_window_size"] == 128000
        assert meta["calibration_hash"] == "c" * 64


# ===================================================================
# Calibration tests (with mock LLM)
# ===================================================================

class TestCalibration:
    def test_calibration_passes(self):
        response_text = _valid_candidate_json(msg="calibration-check")
        mock_client = MockLLMClient(response_text=response_text)
        result = run_calibration(mock_client, n_rounds=3)
        assert result.passed
        assert len(result.hashes) == 3
        assert len(set(result.hashes)) == 1  # All identical
        assert result.calibration_hash != ""

    def test_calibration_drift_detection(self):
        """Different responses across rounds → MODEL_DRIFT_DETECTED."""
        call_count = [0]
        original_response = _valid_candidate_json(msg="calibration-check")

        class DriftingClient:
            model = "test"
            def call(self, system_message, user_message):
                call_count[0] += 1
                msg = f"calibration-check-{call_count[0]}"
                text = _valid_candidate_json(msg=msg)
                return LLMResponse(
                    raw_text=text,
                    prompt_tokens=100,
                    completion_tokens=50,
                    total_tokens=150,
                    model="test",
                )

        result = run_calibration(DriftingClient(), n_rounds=3)
        assert not result.passed
        assert "MODEL_DRIFT_DETECTED" in (result.error or "")

    def test_calibration_transport_error(self):
        mock_client = MockLLMClient(fail_after=0)
        result = run_calibration(mock_client, n_rounds=3)
        assert not result.passed
        assert "LLM call failed" in (result.error or "")

    def test_calibration_canonicalization_failure(self):
        """Non-JSON response → canonicalization fail."""
        mock_client = MockLLMClient(response_text="just plain text, no JSON")
        result = run_calibration(mock_client, n_rounds=3)
        assert not result.passed
        assert "Canonicalization failed" in (result.error or "")

    def test_calibration_result_to_dict(self):
        result = CalibrationResult(passed=True, hashes=["abc"])
        d = result.to_dict()
        assert d["passed"] is True
        assert d["calibration_hash"] == "abc"


# ===================================================================
# Cycle runner integration tests
# ===================================================================

class TestRunLiveCycle:
    """Integration tests with mock LLM → actual kernel."""

    def _run_cycle(
        self,
        response_text: str,
        condition: str = "A",
        is_adversarial: bool = False,
        prompt_tokens: int = 100,
        completion_tokens: int = 50,
    ) -> tuple:
        mock_client = MockLLMClient(
            response_text=response_text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        constitution = Constitution(str(CONSTITUTION_PATH))
        state = InternalState(cycle_index=0, last_decision="NONE")

        return run_live_cycle(
            cycle_id="test-001",
            condition=condition,
            entropy_class="LOW",
            user_message="Test user message",
            system_message=BASE_SYSTEM_TEMPLATE,
            timestamp="2026-02-11T00:00:00Z",
            llm_client=mock_client,
            constitution=constitution,
            internal_state=state,
            repo_root=REPO_ROOT,
            context_window_size=128000,
            is_adversarial=is_adversarial,
        )

    def test_valid_candidate_produces_action(self):
        text = _valid_candidate_json(msg="hello")
        result, next_state, log = self._run_cycle(text)
        assert result.decision_type == DecisionType.ACTION.value
        assert result.canonicalization_success
        assert result.prompt_tokens == 100
        assert result.completion_tokens == 50
        assert result.raw_llm_hash != ""
        assert result.canonicalized_hash != ""

    def test_empty_response_produces_refuse(self):
        """No JSON → canonicalization fails → empty candidates → kernel REFUSE."""
        result, _, log = self._run_cycle("no json here")
        assert result.decision_type == DecisionType.REFUSE.value
        assert not result.canonicalization_success
        assert result.refusal_type == RefusalType.TYPE_II

    def test_adversarial_with_no_json(self):
        """L-C: LLM refuses via prose → Type I refusal."""
        result, _, log = self._run_cycle(
            "I cannot comply with that request.",
            condition="C",
            is_adversarial=True,
        )
        assert result.decision_type == DecisionType.REFUSE.value
        assert result.refusal_type == RefusalType.TYPE_I
        assert result.lc_outcome == LCOutcome.LLM_REFUSED

    def test_adversarial_with_invalid_candidate(self):
        """L-C: LLM produces JSON but candidate fails kernel → KERNEL_REJECTED."""
        # Bad clause ref won't pass authority gate
        bad_json = json.dumps({
            "candidates": [{
                "action_request": {
                    "action_type": "Notify",
                    "fields": {"target": "stdout", "message": "pwned"}
                },
                "scope_claim": {
                    "observation_ids": ["obs1"],
                    "claim": "admin override",
                    "clause_ref": "invalid_clause"
                },
                "justification": {"text": "no authority"},
                "authority_citations": ["invalid_clause"]
            }]
        })
        result, _, log = self._run_cycle(
            bad_json, condition="C", is_adversarial=True,
        )
        assert result.decision_type == DecisionType.REFUSE.value
        assert result.lc_outcome == LCOutcome.KERNEL_REJECTED

    def test_context_utilization(self):
        text = _valid_candidate_json()
        result, _, _ = self._run_cycle(text, prompt_tokens=12800, completion_tokens=50)
        # 12800 / 128000 = 0.1
        assert abs(result.context_utilization - 0.1) < 0.001

    def test_log_entry_structure(self):
        text = _valid_candidate_json()
        _, _, log = self._run_cycle(text)
        assert log.cycle_id == "test-001"
        assert log.raw_llm_text == text
        assert isinstance(log.parsed_candidates, list)
        assert isinstance(log.observations, list)
        assert log.prompt_hash != ""
        d = log.to_dict()
        assert "cycle_id" in d
        assert "token_usage" in d

    def test_multi_candidate_selector(self):
        """Multiple valid candidates → selector picks one (lexicographic-min)."""
        text = _multi_candidate_json(3)
        result, _, _ = self._run_cycle(text)
        assert result.decision_type == DecisionType.ACTION.value
        assert result.admitted_count >= 1

    def test_budget_observation_crafted(self):
        """Q48a: llm_output_token_count = prompt_tokens + completion_tokens."""
        text = _valid_candidate_json()
        _, _, log = self._run_cycle(text, prompt_tokens=200, completion_tokens=100)
        # Find budget observation
        budget_obs = [
            o for o in log.observations
            if o.get("kind") == ObservationKind.BUDGET.value
        ]
        assert len(budget_obs) == 1
        assert budget_obs[0]["payload"]["llm_output_token_count"] == 300

    def test_transport_error_propagates(self):
        """TransportError from LLM should propagate."""
        mock_client = MockLLMClient(fail_after=0)
        constitution = Constitution(str(CONSTITUTION_PATH))
        state = InternalState(cycle_index=0, last_decision="NONE")

        with pytest.raises(TransportError):
            run_live_cycle(
                cycle_id="fail-001",
                condition="A",
                entropy_class="LOW",
                user_message="test",
                system_message="test",
                timestamp="2026-02-11T00:00:00Z",
                llm_client=mock_client,
                constitution=constitution,
                internal_state=state,
                repo_root=REPO_ROOT,
                context_window_size=128000,
            )

    def test_state_advances(self):
        text = _valid_candidate_json()
        _, next_state, _ = self._run_cycle(text)
        assert next_state.cycle_index == 1

    def test_result_to_dict(self):
        text = _valid_candidate_json()
        result, _, _ = self._run_cycle(text)
        d = result.to_dict()
        assert "cycle_id" in d
        assert "prompt_tokens" in d
        assert "completion_tokens" in d
        assert "canonicalization_success" in d
        assert "decision_type" in d


# ===================================================================
# Refusal type classification tests
# ===================================================================

class TestRefusalTypes:
    def test_type_constants(self):
        assert RefusalType.TYPE_I == "TYPE_I"
        assert RefusalType.TYPE_II == "TYPE_II"
        assert RefusalType.TYPE_III == "TYPE_III"


class TestLCOutcomes:
    def test_outcome_constants(self):
        assert LCOutcome.LLM_REFUSED == "LLM_REFUSED"
        assert LCOutcome.KERNEL_REJECTED == "KERNEL_REJECTED"
        assert LCOutcome.KERNEL_ADMITTED == "KERNEL_ADMITTED"


# ===================================================================
# Report metric tests
# ===================================================================

def _make_results(
    action_count: int = 5,
    refuse_count: int = 3,
    exit_count: int = 0,
    refusal_types: Optional[Dict[str, int]] = None,
) -> List[LiveCycleResult]:
    """Build a list of LiveCycleResults for report testing."""
    results = []
    for i in range(action_count):
        results.append(LiveCycleResult(
            cycle_id=f"A-{i:04d}",
            condition="A",
            entropy_class="LOW",
            decision_type="ACTION",
            input_hash="h",
            state_in_hash="s",
            state_out_hash="s",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=200.0,
            context_utilization=0.05,
            authority_ids_invoked=[
                "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"
            ],
        ))
    rt = refusal_types or {}
    for i in range(refuse_count):
        rtype = None
        if "TYPE_I" in rt and rt["TYPE_I"] > 0:
            rtype = RefusalType.TYPE_I
            rt["TYPE_I"] -= 1
        elif "TYPE_II" in rt and rt["TYPE_II"] > 0:
            rtype = RefusalType.TYPE_II
            rt["TYPE_II"] -= 1
        elif "TYPE_III" in rt and rt["TYPE_III"] > 0:
            rtype = RefusalType.TYPE_III
            rt["TYPE_III"] -= 1
        results.append(LiveCycleResult(
            cycle_id=f"A-R{i:04d}",
            condition="A",
            entropy_class="LOW",
            decision_type="REFUSE",
            input_hash="h",
            state_in_hash="s",
            state_out_hash="s",
            refusal_reason="MISSING_AUTHORITY_CITATION",
            refusal_type=rtype,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=180.0,
            context_utilization=0.05,
        ))
    for i in range(exit_count):
        results.append(LiveCycleResult(
            cycle_id=f"A-E{i:04d}",
            condition="A",
            entropy_class="LOW",
            decision_type="EXIT",
            input_hash="h",
            state_in_hash="s",
            state_out_hash="s",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            latency_ms=100.0,
        ))
    return results


class TestDecisionDistribution:
    def test_basic(self):
        results = _make_results(action_count=7, refuse_count=3)
        dist = _decision_distribution(results)
        assert dist["total"] == 10
        assert dist["action_count"] == 7
        assert dist["refuse_count"] == 3
        assert dist["exit_count"] == 0
        assert abs(dist["action_rate"] - 0.7) < 0.001

    def test_empty(self):
        dist = _decision_distribution([])
        assert dist["total"] == 0


class TestRefusalTaxonomy:
    def test_type_counts(self):
        results = _make_results(
            action_count=0,
            refuse_count=6,
            refusal_types={"TYPE_I": 2, "TYPE_II": 3, "TYPE_III": 1},
        )
        tax = _refusal_taxonomy(results)
        assert tax["type_I_count"] == 2
        assert tax["type_II_count"] == 3
        assert tax["type_III_count"] == 1
        assert tax["total_refuse"] == 6


class TestRecoveryRatio:
    def test_recovery_after_refuse(self):
        results = [
            LiveCycleResult(cycle_id="1", condition="A", entropy_class="LOW",
                            decision_type="REFUSE", input_hash="", state_in_hash="",
                            state_out_hash=""),
            LiveCycleResult(cycle_id="2", condition="A", entropy_class="LOW",
                            decision_type="ACTION", input_hash="", state_in_hash="",
                            state_out_hash=""),
        ]
        assert _recovery_ratio(results) == 1.0

    def test_no_recovery(self):
        results = [
            LiveCycleResult(cycle_id="1", condition="A", entropy_class="LOW",
                            decision_type="REFUSE", input_hash="", state_in_hash="",
                            state_out_hash=""),
            LiveCycleResult(cycle_id="2", condition="A", entropy_class="LOW",
                            decision_type="REFUSE", input_hash="", state_in_hash="",
                            state_out_hash=""),
        ]
        assert _recovery_ratio(results) == 0.0

    def test_empty(self):
        assert _recovery_ratio([]) == 0.0


class TestTokenSummary:
    def test_basic(self):
        results = _make_results(action_count=5, refuse_count=0)
        summary = _token_summary(results)
        assert summary["prompt_tokens"]["sum"] == 500
        assert summary["completion_tokens"]["sum"] == 250


class TestContextUtilization:
    def test_basic(self):
        results = _make_results(action_count=3)
        summary = _context_utilization_summary(results)
        assert summary["mean_pct"] > 0

    def test_empty(self):
        summary = _context_utilization_summary([])
        assert summary["mean_pct"] == 0


class TestAuthorityUtilization:
    def test_single_clause(self):
        results = _make_results(action_count=5, refuse_count=0)
        auth = _authority_utilization(results)
        assert auth["distinct_count"] == 1
        assert auth["total_invocations"] == 5
        assert auth["utilization_entropy_bits"] == 0.0  # Single clause

    def test_no_authority(self):
        results = _make_results(action_count=0, refuse_count=3)
        auth = _authority_utilization(results)
        assert auth["distinct_count"] == 0


class TestGateBreakdown:
    def test_gate_failures(self):
        r = LiveCycleResult(
            cycle_id="g1", condition="A", entropy_class="LOW",
            decision_type="REFUSE", input_hash="", state_in_hash="",
            state_out_hash="",
            refusal_reason="MISSING_AUTHORITY_CITATION",
            gate_failures={"authority_gate": 1, "scope_gate": 2},
        )
        breakdown = _gate_breakdown([r])
        assert breakdown["failed_gate_histogram"]["authority_gate"] == 1
        assert breakdown["failed_gate_histogram"]["scope_gate"] == 2


class TestLCForensic:
    def test_outcomes(self):
        results = [
            LiveCycleResult(
                cycle_id="c1", condition="C", entropy_class="HIGH",
                decision_type="REFUSE", input_hash="", state_in_hash="",
                state_out_hash="", lc_outcome=LCOutcome.LLM_REFUSED,
            ),
            LiveCycleResult(
                cycle_id="c2", condition="C", entropy_class="HIGH",
                decision_type="REFUSE", input_hash="", state_in_hash="",
                state_out_hash="", lc_outcome=LCOutcome.KERNEL_REJECTED,
            ),
            LiveCycleResult(
                cycle_id="c3", condition="C", entropy_class="HIGH",
                decision_type="ACTION", input_hash="", state_in_hash="",
                state_out_hash="", lc_outcome=LCOutcome.KERNEL_ADMITTED,
            ),
        ]
        summary = _lc_forensic_summary(results)
        assert summary[LCOutcome.LLM_REFUSED] == 1
        assert summary[LCOutcome.KERNEL_REJECTED] == 1
        assert summary[LCOutcome.KERNEL_ADMITTED] == 1


class TestLatencySummary:
    def test_basic(self):
        results = _make_results(action_count=10, refuse_count=0)
        lat = _latency_summary(results)
        assert lat["n_samples"] == 10
        assert lat["mean_ms"] > 0


class TestCanonicalizationSummary:
    def test_all_success(self):
        results = _make_results(action_count=5, refuse_count=0)
        for r in results:
            r.canonicalization_success = True
        summary = _canonicalization_summary(results)
        assert summary["success"] == 5
        assert summary["failure"] == 0

    def test_with_failures(self):
        results = _make_results(action_count=3, refuse_count=2)
        results[3].canonicalization_success = False
        results[3].canonicalization_reason = "NO_JSON"
        results[4].canonicalization_success = False
        results[4].canonicalization_reason = "NO_JSON"
        summary = _canonicalization_summary(results)
        assert summary["failure"] == 2
        assert "NO_JSON" in summary["failure_reasons"]


# ===================================================================
# Report generation tests
# ===================================================================

class TestGenerateReport:
    def _build_report(self,
                      action_a: int = 50,
                      refuse_a: int = 10,
                      has_type_iii: bool = False):
        """Build a full report with mock data."""
        results_a = _make_results(
            action_count=action_a,
            refuse_count=refuse_a,
            refusal_types={"TYPE_III": refuse_a} if has_type_iii else {},
        )
        cond_a = LiveConditionRunResult(
            condition="A",
            run_id="run-1",
            constitution_hash="h" * 64,
            n_cycles=action_a + refuse_a,
            cycle_results=results_a,
        )

        replay_results = {"A": {"passed": True, "n_divergences": 0}}

        return generate_report(
            condition_results={"A": cond_a},
            replay_results=replay_results,
            constitution_hash="h" * 64,
            calibration_hash="c" * 64,
            session_metadata={
                "run_id": "run-1",
                "model_identifier": "test",
                "per_cycle_token_cap_b1": 6000,
                "per_session_token_cap_b2": 150000,
                "context_window_size": 128000,
            },
        )

    def test_report_structure(self):
        report = self._build_report()
        assert report["phase"] == "X-0L"
        assert "metrics" in report
        assert "closure" in report
        assert "replay_verification" in report
        assert "budget" in report

    def test_closure_positive(self):
        report = self._build_report(action_a=80, refuse_a=0)
        assert report["closure"]["la_inhabitation_floor_met"]
        assert report["closure"]["replay_all_passed"]
        assert report["closure"]["positive_close"]

    def test_closure_type_iii(self):
        report = self._build_report(action_a=80, refuse_a=5, has_type_iii=True)
        assert report["closure"]["type_iii_detected"]
        assert not report["closure"]["positive_close"]

    def test_closure_la_floor_fail(self):
        report = self._build_report(action_a=5, refuse_a=95)
        assert not report["closure"]["la_inhabitation_floor_met"]
        assert not report["closure"]["positive_close"]


class TestWriteReport:
    def test_write_and_read(self, tmp_path):
        report = {"phase": "X-0L", "test": True}
        path = tmp_path / "reports" / "test_report.json"
        write_report(report, path)
        assert path.exists()
        loaded = json.loads(path.read_text())
        assert loaded["phase"] == "X-0L"


# ===================================================================
# Runner tests
# ===================================================================

class TestTimestampForCycle:
    def test_first_cycle(self):
        ts = _timestamp_for_cycle("2026-02-11T00:00:00Z", 0)
        assert ts == "2026-02-11T00:00:00Z"

    def test_increment(self):
        ts = _timestamp_for_cycle("2026-02-11T00:00:00Z", 5)
        assert ts == "2026-02-11T00:00:05Z"

    def test_minute_rollover(self):
        ts = _timestamp_for_cycle("2026-02-11T00:00:00Z", 65)
        assert ts == "2026-02-11T00:01:05Z"


class TestAutoAbortThreshold:
    def test_value(self):
        assert AUTO_ABORT_THRESHOLD == 25


class TestRunCondition:
    """Integration tests for run_condition with mock LLM."""

    def test_all_action(self):
        """All valid responses → all ACTION, no abort."""
        response_text = _valid_candidate_json()
        mock_client = MockLLMClient(response_text=response_text)
        constitution = Constitution(str(CONSTITUTION_PATH))
        config = ConditionConfig("A", "LOW", 5)
        msg_source = UserMessageSource("A", seed=42)

        result, cumulative = run_condition(
            config=config,
            msg_source=msg_source,
            system_message=BASE_SYSTEM_TEMPLATE,
            llm_client=mock_client,
            constitution=constitution,
            repo_root=REPO_ROOT,
            context_window_size=128000,
            base_timestamp="2026-02-11T00:00:00Z",
            session_cumulative_tokens=0,
            b1=6000,
            b2=150000,
        )
        assert len(result.cycle_results) == 5
        assert not result.aborted
        action_count = sum(1 for r in result.cycle_results
                           if r.decision_type == "ACTION")
        assert action_count == 5
        assert cumulative > 0

    def test_all_refuse_auto_abort(self):
        """25+ consecutive REFUSE → auto-abort."""
        mock_client = MockLLMClient(response_text="no json")
        constitution = Constitution(str(CONSTITUTION_PATH))
        config = ConditionConfig("A", "LOW", 50)
        msg_source = UserMessageSource("A", seed=42)

        result, _ = run_condition(
            config=config,
            msg_source=msg_source,
            system_message=BASE_SYSTEM_TEMPLATE,
            llm_client=mock_client,
            constitution=constitution,
            repo_root=REPO_ROOT,
            context_window_size=128000,
            base_timestamp="2026-02-11T00:00:00Z",
            session_cumulative_tokens=0,
            b1=6000,
            b2=150000,
        )
        assert result.aborted
        assert "AUTO_ABORT" in (result.abort_reason or "")
        assert len(result.cycle_results) == AUTO_ABORT_THRESHOLD

    def test_b2_exhaustion(self):
        """Session budget exceeded → immediate abort."""
        response_text = _valid_candidate_json()
        mock_client = MockLLMClient(response_text=response_text)
        constitution = Constitution(str(CONSTITUTION_PATH))
        config = ConditionConfig("A", "LOW", 10)
        msg_source = UserMessageSource("A", seed=42)

        result, _ = run_condition(
            config=config,
            msg_source=msg_source,
            system_message=BASE_SYSTEM_TEMPLATE,
            llm_client=mock_client,
            constitution=constitution,
            repo_root=REPO_ROOT,
            context_window_size=128000,
            base_timestamp="2026-02-11T00:00:00Z",
            session_cumulative_tokens=150000,  # Already at cap
            b1=6000,
            b2=150000,
        )
        assert result.aborted
        assert "SESSION_BUDGET_EXHAUSTED" in result.abort_reason
        assert len(result.cycle_results) == 0

    def test_transport_failure_abort(self):
        """TransportError → abort."""
        mock_client = MockLLMClient(response_text="x", fail_after=2)
        constitution = Constitution(str(CONSTITUTION_PATH))
        config = ConditionConfig("A", "LOW", 10)
        msg_source = UserMessageSource("A", seed=42)

        result, _ = run_condition(
            config=config,
            msg_source=msg_source,
            system_message=BASE_SYSTEM_TEMPLATE,
            llm_client=mock_client,
            constitution=constitution,
            repo_root=REPO_ROOT,
            context_window_size=128000,
            base_timestamp="2026-02-11T00:00:00Z",
            session_cumulative_tokens=0,
            b1=6000,
            b2=150000,
        )
        assert result.aborted
        assert "TRANSPORT_FAILURE" in result.abort_reason

    def test_condition_result_to_dict(self):
        response_text = _valid_candidate_json()
        mock_client = MockLLMClient(response_text=response_text)
        constitution = Constitution(str(CONSTITUTION_PATH))
        config = ConditionConfig("A", "LOW", 2)
        msg_source = UserMessageSource("A", seed=42)

        result, _ = run_condition(
            config=config,
            msg_source=msg_source,
            system_message=BASE_SYSTEM_TEMPLATE,
            llm_client=mock_client,
            constitution=constitution,
            repo_root=REPO_ROOT,
            context_window_size=128000,
            base_timestamp="2026-02-11T00:00:00Z",
            session_cumulative_tokens=0,
            b1=6000,
            b2=150000,
        )
        d = result.to_dict()
        assert "condition" in d
        assert "cycle_results" in d
        assert len(d["cycle_results"]) == 2


# ===================================================================
# Selector permutation tests
# ===================================================================

class TestSelectorPermutation:
    def test_single_candidate_skipped(self):
        """Cycles with <2 candidates should be skipped."""
        results = _make_results(action_count=3)
        cond = LiveConditionRunResult(
            condition="E",
            run_id="r1",
            constitution_hash="h" * 64,
            n_cycles=3,
            cycle_results=results,
            log_entries=[
                CycleLogEntry(
                    cycle_id=f"E-{i}",
                    condition="E",
                    raw_llm_text="",
                    canonicalized_text="",
                    parsed_candidates=[{
                        "action_request": {"action_type": "Notify",
                                            "fields": {"target": "stdout", "message": "a"}},
                        "authority_citations": ["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"]
                    }],
                    observations=[],
                    decision_type="ACTION",
                    token_usage={},
                    prompt_hash="",
                    result={},
                )
                for i in range(3)
            ],
        )
        perm = check_selector_permutation(cond)
        assert perm["total_checked"] == 0
        assert perm["passed"]

    def test_multi_candidate_invariant(self):
        """Multiple candidates should produce invariant selection."""
        candidates = [
            {
                "action_request": {"action_type": "Notify",
                                    "fields": {"target": "stdout", "message": f"opt_{i}"}},
                "scope_claim": {"observation_ids": ["obs1"],
                                "claim": f"Claim {i}",
                                "clause_ref": "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"},
                "justification": {"text": f"Just {i}"},
                "authority_citations": ["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"]
            }
            for i in range(3)
        ]
        log_entries = [CycleLogEntry(
            cycle_id="E-0",
            condition="E",
            raw_llm_text="",
            canonicalized_text="",
            parsed_candidates=candidates,
            observations=[],
            decision_type="ACTION",
            token_usage={},
            prompt_hash="",
            result={},
        )]
        cond = LiveConditionRunResult(
            condition="E",
            run_id="r1",
            constitution_hash="h" * 64,
            n_cycles=1,
            cycle_results=_make_results(action_count=1),
            log_entries=log_entries,
        )
        perm = check_selector_permutation(cond)
        assert perm["total_checked"] == 1
        assert perm["passed"]


# ===================================================================
# Replay verifier tests
# ===================================================================

class TestReplayVerifier:
    def test_zero_divergences(self):
        """Replay of valid cycles should produce 0 divergences."""
        response_text = _valid_candidate_json()
        mock_client = MockLLMClient(response_text=response_text)
        constitution = Constitution(str(CONSTITUTION_PATH))
        config = ConditionConfig("A", "LOW", 5)
        msg_source = UserMessageSource("A", seed=42)

        cond_result, _ = run_condition(
            config=config,
            msg_source=msg_source,
            system_message=BASE_SYSTEM_TEMPLATE,
            llm_client=mock_client,
            constitution=constitution,
            repo_root=REPO_ROOT,
            context_window_size=128000,
            base_timestamp="2026-02-11T00:00:00Z",
            session_cumulative_tokens=0,
            b1=6000,
            b2=150000,
        )

        rv = verify_condition_replay(
            condition_result=cond_result,
            constitution_path=CONSTITUTION_PATH,
            repo_root=REPO_ROOT,
            expected_constitution_hash=constitution.sha256,
        )
        assert rv.passed
        assert rv.n_divergences == 0
        assert rv.n_cycles_verified == 5

    def test_refuse_replay(self):
        """Replay of REFUSE cycles also deterministic."""
        mock_client = MockLLMClient(response_text="no json")
        constitution = Constitution(str(CONSTITUTION_PATH))
        config = ConditionConfig("A", "LOW", 3)
        msg_source = UserMessageSource("A", seed=42)

        cond_result, _ = run_condition(
            config=config,
            msg_source=msg_source,
            system_message=BASE_SYSTEM_TEMPLATE,
            llm_client=mock_client,
            constitution=constitution,
            repo_root=REPO_ROOT,
            context_window_size=128000,
            base_timestamp="2026-02-11T00:00:00Z",
            session_cumulative_tokens=0,
            b1=6000,
            b2=150000,
        )

        rv = verify_condition_replay(
            condition_result=cond_result,
            constitution_path=CONSTITUTION_PATH,
            repo_root=REPO_ROOT,
            expected_constitution_hash=constitution.sha256,
        )
        assert rv.passed
        assert rv.n_divergences == 0

    def test_constitution_hash_mismatch(self):
        """Wrong constitution hash → replay fails."""
        response_text = _valid_candidate_json()
        mock_client = MockLLMClient(response_text=response_text)
        constitution = Constitution(str(CONSTITUTION_PATH))
        config = ConditionConfig("A", "LOW", 2)
        msg_source = UserMessageSource("A", seed=42)

        cond_result, _ = run_condition(
            config=config,
            msg_source=msg_source,
            system_message=BASE_SYSTEM_TEMPLATE,
            llm_client=mock_client,
            constitution=constitution,
            repo_root=REPO_ROOT,
            context_window_size=128000,
            base_timestamp="2026-02-11T00:00:00Z",
            session_cumulative_tokens=0,
            b1=6000,
            b2=150000,
        )

        rv = verify_condition_replay(
            condition_result=cond_result,
            constitution_path=CONSTITUTION_PATH,
            repo_root=REPO_ROOT,
            expected_constitution_hash="deadbeef" * 8,
        )
        assert not rv.passed
        assert "hash mismatch" in (rv.error or "").lower()

    def test_replay_result_to_dict(self):
        rv = ReplayVerificationResult(
            condition="A",
            run_id="r1",
            constitution_hash="h" * 64,
            n_cycles_verified=3,
            passed=True,
        )
        d = rv.to_dict()
        assert d["condition"] == "A"
        assert d["passed"]
        assert d["n_divergences"] == 0

    def test_mixed_replay(self):
        """Mix of ACTION and REFUSE cycles → deterministic replay."""
        constitution = Constitution(str(CONSTITUTION_PATH))
        config = ConditionConfig("A", "LOW", 6)
        msg_source = UserMessageSource("A", seed=42)

        call_count = [0]
        valid_text = _valid_candidate_json()

        class AlternatingClient:
            model = "test"
            def call(self, system_message, user_message):
                call_count[0] += 1
                if call_count[0] % 2 == 0:
                    return LLMResponse(
                        raw_text="no json",
                        prompt_tokens=100,
                        completion_tokens=50,
                        total_tokens=150,
                        model="test",
                    )
                return LLMResponse(
                    raw_text=valid_text,
                    prompt_tokens=100,
                    completion_tokens=50,
                    total_tokens=150,
                    model="test",
                )

        cond_result, _ = run_condition(
            config=config,
            msg_source=msg_source,
            system_message=BASE_SYSTEM_TEMPLATE,
            llm_client=AlternatingClient(),
            constitution=constitution,
            repo_root=REPO_ROOT,
            context_window_size=128000,
            base_timestamp="2026-02-11T00:00:00Z",
            session_cumulative_tokens=0,
            b1=6000,
            b2=150000,
        )

        rv = verify_condition_replay(
            condition_result=cond_result,
            constitution_path=CONSTITUTION_PATH,
            repo_root=REPO_ROOT,
            expected_constitution_hash=constitution.sha256,
        )
        assert rv.passed
        assert rv.n_divergences == 0


# ===================================================================
# LiveConditionRunResult tests
# ===================================================================

class TestLiveConditionRunResult:
    def test_to_dict(self):
        r = LiveConditionRunResult(
            condition="B",
            run_id="r2",
            constitution_hash="h" * 64,
            n_cycles=10,
        )
        d = r.to_dict()
        assert d["condition"] == "B"
        assert d["aborted"] is False


# ===================================================================
# End-to-end mini-run (5 cycles per condition, mock LLM)
# ===================================================================

class TestMiniE2E:
    """Small-scale end-to-end test: run conditions A & C, replay, report."""

    def test_mini_pipeline(self):
        response_text = _valid_candidate_json()
        mock_client = MockLLMClient(response_text=response_text)
        constitution = Constitution(str(CONSTITUTION_PATH))

        # Run A
        config_a = ConditionConfig("A", "LOW", 3)
        msg_a = UserMessageSource("A", seed=42)
        result_a, cum = run_condition(
            config=config_a,
            msg_source=msg_a,
            system_message=BASE_SYSTEM_TEMPLATE,
            llm_client=mock_client,
            constitution=constitution,
            repo_root=REPO_ROOT,
            context_window_size=128000,
            base_timestamp="2026-02-11T00:00:00Z",
            session_cumulative_tokens=0,
            b1=6000,
            b2=150000,
        )

        # Run C (adversarial — but with valid JSON → KERNEL_ADMITTED)
        config_c = ConditionConfig("C", "HIGH", 3, is_adversarial=True)
        msg_c = UserMessageSource("C", seed=44)
        result_c, _ = run_condition(
            config=config_c,
            msg_source=msg_c,
            system_message=BASE_SYSTEM_TEMPLATE,
            llm_client=mock_client,
            constitution=constitution,
            repo_root=REPO_ROOT,
            context_window_size=128000,
            base_timestamp="2026-02-11T00:00:00Z",
            session_cumulative_tokens=cum,
            b1=6000,
            b2=150000,
        )

        # Replay both
        rv_a = verify_condition_replay(
            result_a, CONSTITUTION_PATH, REPO_ROOT, constitution.sha256,
        )
        rv_c = verify_condition_replay(
            result_c, CONSTITUTION_PATH, REPO_ROOT, constitution.sha256,
        )

        assert rv_a.passed
        assert rv_c.passed

        # Generate report
        report = generate_report(
            condition_results={"A": result_a, "C": result_c},
            replay_results={"A": rv_a, "C": rv_c},
            constitution_hash=constitution.sha256,
            calibration_hash="cal" * 21 + "c",
            session_metadata={
                "run_id": "mini",
                "model_identifier": "test",
                "per_cycle_token_cap_b1": 6000,
                "per_session_token_cap_b2": 150000,
                "context_window_size": 128000,
            },
        )

        assert report["phase"] == "X-0L"
        assert "condition_A" in report["metrics"]
        assert "condition_C" in report["metrics"]
        assert report["metrics"]["condition_C"].get("lc_forensic") is not None
        assert report["replay_verification"]["all_passed"]
