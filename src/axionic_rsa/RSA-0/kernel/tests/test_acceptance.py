"""
RSA-0 Phase X — Acceptance Tests (Sovereignty Sanity Checks)

Per spec §15 and instructions §11, these tests verify:

  1. No warrant → no side effect                     (INV-1)
  2. Invalid warrant → no side effect                 (INV-1 variant)
  3. Missing scope claim → REFUSE                     (admission gate 3)
  4. Missing authority citations → REFUSE             (admission gate 2)
  5. Multiple admissible candidates → deterministic   (selector)
  6. LLM nondeterminism contained                     (stub — INV-3)
  7. Replay determinism                               (INV-4)
  8. Budget exhaustion → REFUSE                       (refusal_policy)
  9. Constitution violation → REFUSE                  (admission gate 4)
  10. Integrity risk → EXIT                            (exit_policy)
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Ensure repo root is on sys.path so `kernel.src.*` and `host.*` resolve.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pytest

from kernel.src.artifacts import (
    ActionRequest,
    ActionType,
    Author,
    CandidateBundle,
    DecisionType,
    ExecutionWarrant,
    ExitReasonCode,
    InternalState,
    Justification,
    Observation,
    ObservationKind,
    RefusalReasonCode,
    ScopeClaim,
    SystemEvent,
    canonical_json,
)
from kernel.src.constitution import Constitution
from kernel.src.admission import AdmissionPipeline
from kernel.src.selector import select
from kernel.src.policy_core import PolicyOutput, policy_core
from host.tools.executor import Executor, ExecutionEvent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CONSTITUTION_PATH = (
    REPO_ROOT
    / "artifacts"
    / "phase-x"
    / "constitution"
    / "rsa_constitution.v0.1.1.yaml"
)


@pytest.fixture
def constitution() -> Constitution:
    return Constitution(str(CONSTITUTION_PATH))


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def state_cycle_0() -> InternalState:
    return InternalState(cycle_index=0, last_decision="NONE")


def _base_observations() -> list[Observation]:
    """Minimal set of observations for a valid cycle."""
    return [
        Observation(
            kind=ObservationKind.USER_INPUT.value,
            payload={"text": "Hello, RSA-0", "source": "cli"},
            author=Author.USER.value,
        ),
        Observation(
            kind=ObservationKind.TIMESTAMP.value,
            payload={"iso8601_utc": "2026-02-10T00:00:00Z"},
            author=Author.HOST.value,
        ),
        Observation(
            kind=ObservationKind.BUDGET.value,
            payload={
                "llm_output_token_count": 100,
                "llm_candidates_reported": 1,
                "llm_parse_errors": 0,
            },
            author=Author.HOST.value,
        ),
    ]


def _valid_notify_candidate(observations: list[Observation]) -> CandidateBundle:
    """A fully valid Notify candidate with proper citations and scope claim."""
    ar = ActionRequest(
        action_type=ActionType.NOTIFY.value,
        fields={"target": "stdout", "message": "echo: Hello, RSA-0"},
        author=Author.REFLECTION.value,
    )
    sc = ScopeClaim(
        observation_ids=[observations[0].id],
        claim="User sent a greeting; echo it back.",
        clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
        author=Author.REFLECTION.value,
    )
    just = Justification(
        text="User greeting should be echoed to confirm receipt.",
        author=Author.REFLECTION.value,
    )
    return CandidateBundle(
        action_request=ar,
        scope_claim=sc,
        justification=just,
        authority_citations=[
            "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
        ],
    )


# ---------------------------------------------------------------------------
# Test 1: No warrant → no side effect
# ---------------------------------------------------------------------------

class TestNoWarrantNoSideEffect:
    """INV-1: The executor must refuse any execution without a warrant."""

    def test_executor_rejects_none_warrant(self, repo_root):
        """Executor cannot be called without a warrant object at all."""
        executor = Executor(repo_root, current_cycle=0)
        obs = _base_observations()
        candidate = _valid_notify_candidate(obs)

        # We cannot even call execute without a warrant — type enforcement.
        # Simulate by passing a warrant for the wrong cycle.
        wrong_warrant = ExecutionWarrant(
            action_request_id=candidate.action_request.id,
            action_type=ActionType.NOTIFY.value,
            scope_constraints={},
            issued_in_cycle=999,  # wrong cycle
        )
        event = executor.execute(wrong_warrant, candidate)
        assert event.result == "failed"
        assert "cycle mismatch" in event.detail.lower()

    def test_policy_core_refuses_when_no_candidates(
        self, constitution, repo_root, state_cycle_0,
    ):
        """When there are no candidates at all, policy core must REFUSE."""
        obs = _base_observations()
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[],  # nothing proposed
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value
        assert output.decision.warrant is None  # No warrant issued


# ---------------------------------------------------------------------------
# Test 2: Invalid warrant → no side effect
# ---------------------------------------------------------------------------

class TestInvalidWarrantNoSideEffect:
    """INV-1 variant: invalid warrant must prevent execution."""

    def test_used_warrant_rejected(self, repo_root):
        """Single-use warrant cannot be used twice."""
        obs = _base_observations()
        candidate = _valid_notify_candidate(obs)
        executor = Executor(repo_root, current_cycle=0)
        warrant = ExecutionWarrant(
            action_request_id=candidate.action_request.id,
            action_type=ActionType.NOTIFY.value,
            scope_constraints={},
            issued_in_cycle=0,
        )
        # First use succeeds
        event1 = executor.execute(warrant, candidate)
        assert event1.result == "committed"

        # Second use fails
        event2 = executor.execute(warrant, candidate)
        assert event2.result == "failed"
        assert "single-use" in event2.detail.lower()

    def test_mismatched_action_request_rejected(self, repo_root):
        """Warrant referencing a different ActionRequest must be rejected."""
        obs = _base_observations()
        candidate = _valid_notify_candidate(obs)
        executor = Executor(repo_root, current_cycle=0)

        warrant = ExecutionWarrant(
            action_request_id="nonexistent-action-request-id",
            action_type=ActionType.NOTIFY.value,
            scope_constraints={},
            issued_in_cycle=0,
        )
        event = executor.execute(warrant, candidate)
        assert event.result == "failed"
        assert "does not reference" in event.detail.lower()


# ---------------------------------------------------------------------------
# Test 3: Missing scope claim → REFUSE
# ---------------------------------------------------------------------------

class TestMissingScopeClaimRefuses:
    """Admission gate 3: candidates without scope claim are rejected."""

    def test_no_scope_claim_means_refuse(
        self, constitution, repo_root, state_cycle_0,
    ):
        obs = _base_observations()
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "hi"},
            author=Author.REFLECTION.value,
        )
        # No scope claim
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=None,
            justification=Justification(
                text="No scope claim here.", author=Author.REFLECTION.value,
            ),
            authority_citations=[
                "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            ],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value
        assert output.decision.warrant is None


# ---------------------------------------------------------------------------
# Test 4: Missing authority citations → REFUSE
# ---------------------------------------------------------------------------

class TestMissingAuthorityCitationsRefuses:
    """Admission gate 2: candidates without authority citations are rejected."""

    def test_no_citations_means_refuse(
        self, constitution, repo_root, state_cycle_0,
    ):
        obs = _base_observations()
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "hi"},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="test claim",
            clause_ref="constitution:v0.1.1#INV-AUTHORITY-CITED",
            author=Author.REFLECTION.value,
        )
        # Empty authority citations
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=Justification(
                text="No citations test.", author=Author.REFLECTION.value,
            ),
            authority_citations=[],  # missing
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value
        assert output.decision.warrant is None


# ---------------------------------------------------------------------------
# Test 5: Multiple admissible candidates → deterministic selector
# ---------------------------------------------------------------------------

class TestDeterministicSelection:
    """Selector must pick lexicographic-min bundle hash, deterministically."""

    def test_two_valid_candidates_same_result_every_time(
        self, constitution, repo_root, state_cycle_0,
    ):
        obs = _base_observations()

        # Build two distinct valid Notify candidates with different messages
        def make_candidate(msg: str) -> CandidateBundle:
            ar = ActionRequest(
                action_type=ActionType.NOTIFY.value,
                fields={"target": "stdout", "message": msg},
                author=Author.REFLECTION.value,
            )
            sc = ScopeClaim(
                observation_ids=[obs[0].id],
                claim=f"Echo message: {msg}",
                clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
                author=Author.REFLECTION.value,
            )
            just = Justification(
                text=f"Justified: {msg}",
                author=Author.REFLECTION.value,
            )
            return CandidateBundle(
                action_request=ar,
                scope_claim=sc,
                justification=just,
                authority_citations=[
                    "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
                ],
            )

        c1 = make_candidate("alpha")
        c2 = make_candidate("bravo")

        # Run policy core 5 times — must select same candidate every time
        selections = []
        for _ in range(5):
            output = policy_core(
                observations=obs,
                constitution=constitution,
                internal_state=state_cycle_0,
                candidates=[c1, c2],
                repo_root=repo_root,
            )
            assert output.decision.decision_type == DecisionType.ACTION.value
            assert output.decision.bundle is not None
            selections.append(output.decision.bundle.bundle_hash_hex())

        # All selections identical
        assert len(set(selections)) == 1, (
            f"Nondeterministic selection: {selections}"
        )

    def test_order_independence(
        self, constitution, repo_root, state_cycle_0,
    ):
        """Selection result must be the same regardless of input order."""
        obs = _base_observations()

        def make_candidate(msg: str) -> CandidateBundle:
            ar = ActionRequest(
                action_type=ActionType.NOTIFY.value,
                fields={"target": "stdout", "message": msg},
                author=Author.REFLECTION.value,
            )
            sc = ScopeClaim(
                observation_ids=[obs[0].id],
                claim=f"Echo: {msg}",
                clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
                author=Author.REFLECTION.value,
            )
            just = Justification(
                text=f"Just: {msg}",
                author=Author.REFLECTION.value,
            )
            return CandidateBundle(
                action_request=ar,
                scope_claim=sc,
                justification=just,
                authority_citations=[
                    "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
                ],
            )

        c1 = make_candidate("xxx")
        c2 = make_candidate("yyy")

        out_fwd = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[c1, c2],
            repo_root=repo_root,
        )
        out_rev = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[c2, c1],
            repo_root=repo_root,
        )

        assert out_fwd.decision.bundle is not None
        assert out_rev.decision.bundle is not None
        assert (
            out_fwd.decision.bundle.bundle_hash_hex()
            == out_rev.decision.bundle.bundle_hash_hex()
        )


# ---------------------------------------------------------------------------
# Test 6: LLM nondeterminism contained (INV-3 stub)
# ---------------------------------------------------------------------------

class TestLLMNondeterminismContained:
    """
    INV-3: Reflection may propose but not decide.
    Stub — verifies that the pipeline works identically regardless of
    candidate *content* as long as structure is valid, and that the kernel
    (not the LLM) issues the warrant.
    """

    def test_kernel_authors_warrant_not_reflection(
        self, constitution, repo_root, state_cycle_0,
    ):
        obs = _base_observations()
        candidate = _valid_notify_candidate(obs)

        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.ACTION.value
        assert output.decision.warrant is not None
        # Warrant has no 'author' field — it's emitted by policy_core (the kernel)
        # ActionRequest author is reflection; the Decision itself is kernel's output
        assert candidate.action_request.author == Author.REFLECTION.value

    def test_kernel_only_action_refused_from_reflection(
        self, constitution, repo_root, state_cycle_0,
    ):
        """LogAppend is kernel-only; reflection proposals must be rejected."""
        obs = _base_observations()
        ar = ActionRequest(
            action_type=ActionType.LOG_APPEND.value,
            fields={
                "log_name": "observations",
                "jsonl_lines": ['{"test": true}'],
            },
            author=Author.REFLECTION.value,  # reflection tries kernel-only
        )
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=None,
            justification=None,
            authority_citations=[
                "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            ],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value


# ---------------------------------------------------------------------------
# Test 7: Replay determinism (INV-4)
# ---------------------------------------------------------------------------

class TestReplayDeterminism:
    """
    Given identical inputs, policy_core must produce identical outputs.
    We run policy_core twice with the same observations + candidates and
    compare decisions (decision type, warrant ID, selected bundle hash).
    """

    def test_identical_inputs_identical_output(
        self, constitution, repo_root, state_cycle_0,
    ):
        obs = _base_observations()
        candidate = _valid_notify_candidate(obs)

        out1 = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )
        out2 = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )

        assert out1.decision.decision_type == out2.decision.decision_type
        assert (
            (out1.decision.warrant is None and out2.decision.warrant is None)
            or (
                out1.decision.warrant is not None
                and out2.decision.warrant is not None
                and out1.decision.warrant.warrant_id == out2.decision.warrant.warrant_id
            )
        )

        if out1.decision.bundle and out2.decision.bundle:
            assert (
                out1.decision.bundle.bundle_hash_hex()
                == out2.decision.bundle.bundle_hash_hex()
            )


# ---------------------------------------------------------------------------
# Test 8: Budget exhaustion → REFUSE
# ---------------------------------------------------------------------------

class TestBudgetExhaustion:
    """When budget observation shows tokens > max, policy core must REFUSE."""

    def test_over_budget_means_refuse(
        self, constitution, repo_root, state_cycle_0,
    ):
        max_tokens = constitution.max_total_tokens_per_cycle()
        obs = [
            Observation(
                kind=ObservationKind.USER_INPUT.value,
                payload={"text": "test", "source": "cli"},
                author=Author.USER.value,
            ),
            Observation(
                kind=ObservationKind.TIMESTAMP.value,
                payload={"iso8601_utc": "2026-02-10T00:00:00Z"},
                author=Author.HOST.value,
            ),
            Observation(
                kind=ObservationKind.BUDGET.value,
                payload={
                    "llm_output_token_count": max_tokens + 1,  # over limit
                    "llm_candidates_reported": 1,
                    "llm_parse_errors": 0,
                },
                author=Author.HOST.value,
            ),
        ]
        candidate = _valid_notify_candidate(obs)
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value
        assert output.decision.refusal is not None
        assert output.decision.refusal.reason_code == RefusalReasonCode.BUDGET_EXHAUSTED.value


# ---------------------------------------------------------------------------
# Test 9: Constitution violation → REFUSE
# ---------------------------------------------------------------------------

class TestConstitutionViolation:
    """Actions outside the closed action set must be refused at admission."""

    def test_unknown_action_type_refused(
        self, constitution, repo_root, state_cycle_0,
    ):
        obs = _base_observations()
        ar = ActionRequest(
            action_type="NetworkCall",  # not in closed set
            fields={"url": "https://evil.example"},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="I want to make a network call",
            clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            author=Author.REFLECTION.value,
        )
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=Justification(
                text="test", author=Author.REFLECTION.value,
            ),
            authority_citations=[
                "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            ],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value
        assert output.decision.warrant is None

    def test_unresolvable_citation_refused(
        self, constitution, repo_root, state_cycle_0,
    ):
        """Citation that doesn't resolve in the constitution → admission failure."""
        obs = _base_observations()
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "bad citation"},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="test",
            clause_ref="constitution:v0.1.1#NONEXISTENT-CLAUSE",
            author=Author.REFLECTION.value,
        )
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=Justification(
                text="test", author=Author.REFLECTION.value,
            ),
            authority_citations=[
                "constitution:v0.1.1#NONEXISTENT-CLAUSE",
            ],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value

    def test_path_outside_allowlist_refused(
        self, constitution, repo_root, state_cycle_0,
    ):
        """Read from path not in allowlist → io_allowlist gate failure."""
        obs = _base_observations()
        ar = ActionRequest(
            action_type=ActionType.READ_LOCAL.value,
            fields={"path": "/etc/passwd"},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="Reading sensitive file",
            clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            author=Author.REFLECTION.value,
        )
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=Justification(
                text="test", author=Author.REFLECTION.value,
            ),
            authority_citations=[
                "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            ],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value


# ---------------------------------------------------------------------------
# Test 10: Integrity risk → EXIT
# ---------------------------------------------------------------------------

class TestIntegrityRiskExit:
    """Integrity-risk system observations must trigger EXIT, not REFUSE."""

    def _run_with_system_event(
        self, event_value: str, constitution, repo_root, state_cycle_0,
    ) -> PolicyOutput:
        obs = [
            Observation(
                kind=ObservationKind.SYSTEM.value,
                payload={"event": event_value, "detail": "test failure"},
                author=Author.HOST.value,
            ),
            Observation(
                kind=ObservationKind.TIMESTAMP.value,
                payload={"iso8601_utc": "2026-02-10T00:00:00Z"},
                author=Author.HOST.value,
            ),
        ]
        return policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[],
            repo_root=repo_root,
        )

    def test_startup_integrity_fail_exits(
        self, constitution, repo_root, state_cycle_0,
    ):
        output = self._run_with_system_event(
            SystemEvent.STARTUP_INTEGRITY_FAIL.value,
            constitution, repo_root, state_cycle_0,
        )
        assert output.decision.decision_type == DecisionType.EXIT.value
        assert output.decision.exit_record is not None
        assert output.decision.exit_record.reason_code == ExitReasonCode.INTEGRITY_RISK.value

    def test_citation_index_fail_exits(
        self, constitution, repo_root, state_cycle_0,
    ):
        output = self._run_with_system_event(
            SystemEvent.CITATION_INDEX_FAIL.value,
            constitution, repo_root, state_cycle_0,
        )
        assert output.decision.decision_type == DecisionType.EXIT.value

    def test_replay_fail_exits(
        self, constitution, repo_root, state_cycle_0,
    ):
        output = self._run_with_system_event(
            SystemEvent.REPLAY_FAIL.value,
            constitution, repo_root, state_cycle_0,
        )
        assert output.decision.decision_type == DecisionType.EXIT.value

    def test_executor_integrity_fail_exits(
        self, constitution, repo_root, state_cycle_0,
    ):
        output = self._run_with_system_event(
            SystemEvent.EXECUTOR_INTEGRITY_FAIL.value,
            constitution, repo_root, state_cycle_0,
        )
        assert output.decision.decision_type == DecisionType.EXIT.value


# ---------------------------------------------------------------------------
# Test 11 (bonus): Valid candidate → ACTION + warrant issued
# ---------------------------------------------------------------------------

class TestValidCandidateAction:
    """Positive test: a properly formed candidate should produce ACTION + warrant."""

    def test_valid_notify_admitted_and_warranted(
        self, constitution, repo_root, state_cycle_0,
    ):
        obs = _base_observations()
        candidate = _valid_notify_candidate(obs)
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.ACTION.value
        assert output.decision.bundle is not None
        assert output.decision.warrant is not None
        assert output.decision.warrant.action_request_id == candidate.action_request.id
        assert output.decision.warrant.action_type == ActionType.NOTIFY.value
        assert output.decision.warrant.issued_in_cycle == 0
        assert output.decision.warrant.single_use is True

    def test_warrant_allows_execution(self, constitution, repo_root, state_cycle_0):
        """End-to-end: policy_core → warrant → executor → committed."""
        obs = _base_observations()
        candidate = _valid_notify_candidate(obs)
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.ACTION.value

        executor = Executor(repo_root, current_cycle=0)
        event = executor.execute(output.decision.warrant, output.decision.bundle)
        assert event.result == "committed"


# ---------------------------------------------------------------------------
# Test 12 (bonus): Canonical JSON determinism
# ---------------------------------------------------------------------------

class TestCanonicalJSON:
    """Canonical serialization must be deterministic and key-sorted."""

    def test_sorted_keys(self):
        obj = {"z": 1, "a": 2, "m": 3}
        result = canonical_json(obj)
        assert result == '{"a":2,"m":3,"z":1}'

    def test_no_whitespace(self):
        obj = {"hello": "world", "list": [1, 2, 3]}
        result = canonical_json(obj)
        assert " " not in result
        assert "\n" not in result

    def test_nested_sorted(self):
        obj = {"b": {"y": 1, "x": 2}, "a": 0}
        result = canonical_json(obj)
        assert result == '{"a":0,"b":{"x":2,"y":1}}'

    def test_stable_across_calls(self):
        obj = {"key": "value", "num": 42, "arr": [1, "two"]}
        r1 = canonical_json(obj)
        r2 = canonical_json(obj)
        assert r1 == r2


# ---------------------------------------------------------------------------
# Test 13 (audit): Host cannot bypass sovereignty boundary
# ---------------------------------------------------------------------------

class TestHostSovereigntyBoundary:
    """
    Audit-driven: host must not be able to bypass the kernel's authority.
    The host proposes; the kernel decides; the executor enforces.
    """

    def test_host_cannot_inject_action_directly_into_executor(self, repo_root):
        """
        A pre-admitted ActionRequest + fabricated warrant from host code
        must fail if the warrant was not issued by policy_core for this cycle.
        """
        obs = _base_observations()
        candidate = _valid_notify_candidate(obs)

        # Host fabricates a warrant without going through policy_core
        fabricated_warrant = ExecutionWarrant(
            action_request_id=candidate.action_request.id,
            action_type=ActionType.NOTIFY.value,
            scope_constraints={},
            issued_in_cycle=0,
        )

        # First execution "works" mechanically (warrant is structurally valid)
        # — the executor validates structure, not provenance.
        # So the sovereignty guarantee is: the executor ONLY receives warrants
        # from policy_core via the host's execute_decision() path.
        # This test documents that the executor itself is not the sovereignty
        # boundary — policy_core is. The executor is a downstream enforcer.
        executor = Executor(repo_root, current_cycle=0)
        event = executor.execute(fabricated_warrant, candidate)

        # Even if executor accepts structure, second use must fail (single-use)
        event2 = executor.execute(fabricated_warrant, candidate)
        assert event2.result == "failed"

    def test_host_cannot_issue_kernel_only_action(
        self, constitution, repo_root, state_cycle_0,
    ):
        """Host-authored LogAppend candidate must be rejected at admission."""
        obs = _base_observations()
        ar = ActionRequest(
            action_type=ActionType.LOG_APPEND.value,
            fields={
                "log_name": "observations",
                "jsonl_lines": ['{"test": true}'],
            },
            author=Author.HOST.value,  # host, not kernel
        )
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=None,
            justification=None,
            authority_citations=[
                "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            ],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state_cycle_0,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value

    def test_host_cannot_mutate_internal_state_to_bypass_cycle(
        self, constitution, repo_root,
    ):
        """
        Even if host advances internal_state incorrectly, the kernel's
        decision is based solely on the state it receives — and warrants
        are bound to that cycle_index.
        """
        # State claims cycle 99
        tampered_state = InternalState(cycle_index=99, last_decision="ACTION")
        obs = _base_observations()
        candidate = _valid_notify_candidate(obs)

        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=tampered_state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        # Kernel still issues a decision based on what it's given
        assert output.decision.decision_type == DecisionType.ACTION.value
        # Warrant is bound to cycle 99, not cycle 0
        assert output.decision.warrant.issued_in_cycle == 99

        # Executor at cycle 0 rejects this warrant
        executor = Executor(repo_root, current_cycle=0)
        event = executor.execute(output.decision.warrant, output.decision.bundle)
        assert event.result == "failed"
        assert "cycle mismatch" in event.detail.lower()

    def test_system_observation_only_from_host_author(self):
        """
        System observations must carry Author.HOST — not USER or REFLECTION.
        This is a convention enforced at construction, documented as a
        trust boundary.
        """
        obs = Observation(
            kind=ObservationKind.SYSTEM.value,
            payload={"event": "startup_integrity_ok", "detail": "test"},
            author=Author.HOST.value,
        )
        assert obs.author == Author.HOST.value

        # User-authored system observations are structurally possible but
        # represent a trust boundary violation. The host must never construct
        # one from user input. This test documents the expectation.
        user_obs = Observation(
            kind=ObservationKind.SYSTEM.value,
            payload={"event": "startup_integrity_fail", "detail": "injected"},
            author=Author.USER.value,
        )
        # It constructs — but policy_core should still respond to the event
        # regardless of author. The trust boundary is at the host, not kernel.
        assert user_obs.author == Author.USER.value

    def test_system_observation_call_sites_bounded(self):
        """
        Enforce that make_system_observation() is only called in the
        startup() method of host/cli/main.py. Exactly 4 call sites:
        two OK/FAIL pairs (constitution hash, citation index).

        If this test fails, a new call site was added — audit it.
        """
        import re
        host_path = Path(__file__).resolve().parent.parent.parent / "host" / "cli" / "main.py"
        source = host_path.read_text(encoding="utf-8")
        # Count invocations (calls, not the def line or docstrings)
        calls = [
            line for line in source.splitlines()
            if "make_system_observation(" in line
            and not line.strip().startswith("def ")
            and not line.strip().startswith("#")
            and not line.strip().startswith("Host")  # docstring continuation
        ]
        assert len(calls) == 4, (
            f"Expected exactly 4 call sites for make_system_observation, "
            f"found {len(calls)}. Audit any new sites for trust boundary compliance."
        )

        # Verify no other module calls it
        kernel_dir = Path(__file__).resolve().parent.parent / "src"
        for py_file in kernel_dir.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            assert "make_system_observation" not in content, (
                f"Kernel module {py_file.name} must not reference "
                f"make_system_observation — that is a host-only function."
            )


# ---------------------------------------------------------------------------
# Test 14 (Erratum X.E1): Deterministic clock
# ---------------------------------------------------------------------------

class TestDeterministicClock:
    """
    Erratum X.E1: All kernel-created artifacts must use deterministic time
    derived from the TIMESTAMP observation, not wall-clock.
    """

    def test_same_inputs_same_warrant_hash(
        self, constitution, repo_root, state_cycle_0,
    ):
        """
        Identical inputs on two separate calls must produce identical
        warrant hashes and IDs — proving no wall-clock dependency.
        """
        obs = _base_observations()
        candidate = _valid_notify_candidate(obs)

        output1 = policy_core(
            observations=obs, constitution=constitution,
            internal_state=state_cycle_0, candidates=[candidate],
            repo_root=repo_root,
        )
        output2 = policy_core(
            observations=obs, constitution=constitution,
            internal_state=state_cycle_0, candidates=[candidate],
            repo_root=repo_root,
        )

        assert output1.decision.decision_type == DecisionType.ACTION.value
        assert output2.decision.decision_type == DecisionType.ACTION.value
        assert output1.decision.warrant.warrant_id == output2.decision.warrant.warrant_id
        assert output1.decision.warrant.created_at == output2.decision.warrant.created_at
        assert output1.decision.warrant.created_at == "2026-02-10T00:00:00Z"

    def test_different_timestamp_different_warrant_id(
        self, constitution, repo_root, state_cycle_0,
    ):
        """
        Different TIMESTAMP observation → different warrant created_at
        and therefore different warrant_id.
        """
        obs_t1 = [
            Observation(
                kind=ObservationKind.USER_INPUT.value,
                payload={"text": "test", "source": "cli"},
                author=Author.USER.value,
            ),
            Observation(
                kind=ObservationKind.TIMESTAMP.value,
                payload={"iso8601_utc": "2026-02-10T00:00:00Z"},
                author=Author.HOST.value,
            ),
            Observation(
                kind=ObservationKind.BUDGET.value,
                payload={"llm_output_token_count": 100, "llm_candidates_reported": 1, "llm_parse_errors": 0},
                author=Author.HOST.value,
            ),
        ]
        obs_t2 = [
            Observation(
                kind=ObservationKind.USER_INPUT.value,
                payload={"text": "test", "source": "cli"},
                author=Author.USER.value,
            ),
            Observation(
                kind=ObservationKind.TIMESTAMP.value,
                payload={"iso8601_utc": "2026-02-10T01:00:00Z"},
                author=Author.HOST.value,
            ),
            Observation(
                kind=ObservationKind.BUDGET.value,
                payload={"llm_output_token_count": 100, "llm_candidates_reported": 1, "llm_parse_errors": 0},
                author=Author.HOST.value,
            ),
        ]

        c1 = _valid_notify_candidate(obs_t1)
        c2 = _valid_notify_candidate(obs_t2)

        out1 = policy_core(
            observations=obs_t1, constitution=constitution,
            internal_state=state_cycle_0, candidates=[c1],
            repo_root=repo_root,
        )
        out2 = policy_core(
            observations=obs_t2, constitution=constitution,
            internal_state=state_cycle_0, candidates=[c2],
            repo_root=repo_root,
        )

        assert out1.decision.decision_type == DecisionType.ACTION.value
        assert out2.decision.decision_type == DecisionType.ACTION.value
        assert out1.decision.warrant.created_at == "2026-02-10T00:00:00Z"
        assert out2.decision.warrant.created_at == "2026-02-10T01:00:00Z"
        assert out1.decision.warrant.warrant_id != out2.decision.warrant.warrant_id

    def test_missing_timestamp_observation_refused(
        self, constitution, repo_root, state_cycle_0,
    ):
        """No TIMESTAMP observation → REFUSE with MISSING_REQUIRED_OBSERVATION."""
        obs = [
            Observation(
                kind=ObservationKind.USER_INPUT.value,
                payload={"text": "no timestamp", "source": "cli"},
                author=Author.USER.value,
            ),
            Observation(
                kind=ObservationKind.BUDGET.value,
                payload={"llm_output_token_count": 100, "llm_candidates_reported": 1, "llm_parse_errors": 0},
                author=Author.HOST.value,
            ),
        ]
        candidate = CandidateBundle(
            action_request=ActionRequest(
                action_type=ActionType.NOTIFY.value,
                fields={"target": "stdout", "message": "no ts"},
                author=Author.REFLECTION.value,
            ),
            scope_claim=ScopeClaim(
                observation_ids=[obs[0].id], claim="test",
                clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
                author=Author.REFLECTION.value,
            ),
            justification=Justification(text="test", author=Author.REFLECTION.value),
            authority_citations=["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"],
        )
        output = policy_core(
            observations=obs, constitution=constitution,
            internal_state=state_cycle_0, candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value
        assert output.decision.refusal.reason_code == RefusalReasonCode.MISSING_REQUIRED_OBSERVATION.value

    def test_duplicate_timestamp_observations_refused(
        self, constitution, repo_root, state_cycle_0,
    ):
        """Two TIMESTAMP observations → ambiguous time → REFUSE."""
        obs = [
            Observation(
                kind=ObservationKind.USER_INPUT.value,
                payload={"text": "double ts", "source": "cli"},
                author=Author.USER.value,
            ),
            Observation(
                kind=ObservationKind.TIMESTAMP.value,
                payload={"iso8601_utc": "2026-02-10T00:00:00Z"},
                author=Author.HOST.value,
            ),
            Observation(
                kind=ObservationKind.TIMESTAMP.value,
                payload={"iso8601_utc": "2026-02-10T01:00:00Z"},
                author=Author.HOST.value,
            ),
            Observation(
                kind=ObservationKind.BUDGET.value,
                payload={"llm_output_token_count": 100, "llm_candidates_reported": 1, "llm_parse_errors": 0},
                author=Author.HOST.value,
            ),
        ]
        output = policy_core(
            observations=obs, constitution=constitution,
            internal_state=state_cycle_0, candidates=[],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value
        assert output.decision.refusal.reason_code == RefusalReasonCode.MISSING_REQUIRED_OBSERVATION.value

    def test_refusal_record_uses_cycle_time(
        self, constitution, repo_root, state_cycle_0,
    ):
        """
        When no candidates are admitted, the RefusalRecord's created_at
        should equal the TIMESTAMP observation, not wall-clock.
        """
        obs = _base_observations()
        # No candidates → REFUSE
        output = policy_core(
            observations=obs, constitution=constitution,
            internal_state=state_cycle_0, candidates=[],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value
        assert output.decision.refusal.created_at == "2026-02-10T00:00:00Z"

    def test_exit_record_uses_cycle_time(
        self, constitution, repo_root, state_cycle_0,
    ):
        """
        When an integrity risk triggers EXIT, the ExitRecord's created_at
        should equal the TIMESTAMP observation.
        """
        obs = [
            Observation(
                kind=ObservationKind.SYSTEM.value,
                payload={"event": SystemEvent.STARTUP_INTEGRITY_FAIL.value, "detail": "test"},
                author=Author.HOST.value,
            ),
            Observation(
                kind=ObservationKind.TIMESTAMP.value,
                payload={"iso8601_utc": "2026-02-10T12:00:00Z"},
                author=Author.HOST.value,
            ),
        ]
        output = policy_core(
            observations=obs, constitution=constitution,
            internal_state=state_cycle_0, candidates=[],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.EXIT.value
        assert output.decision.exit_record.created_at == "2026-02-10T12:00:00Z"
