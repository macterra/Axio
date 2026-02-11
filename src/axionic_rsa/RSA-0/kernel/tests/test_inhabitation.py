"""
RSA-0 Phase X — Inhabitation Pressure Tests

These are NOT acceptance tests (those assert correctness).
These are sovereignty surface maps under adversarial conditions.

Three families:

  1. Authority ambiguity — ambiguous instructions mapping to multiple clauses
  2. ScopeClaim adversarial — structurally valid but semantically wrong
  3. Budget / filibuster — overflow, malformed, resource exhaustion

Each test documents expected behavior (ACTION, REFUSE, EXIT) and
WHY the kernel produces that decision, yielding the first "inhabitation
curve" of an RSA.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

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
    InternalState,
    Justification,
    Observation,
    ObservationKind,
    RefusalReasonCode,
    ScopeClaim,
    canonical_json,
)
from kernel.src.constitution import Constitution
from kernel.src.policy_core import PolicyOutput, policy_core


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
def state() -> InternalState:
    return InternalState(cycle_index=0, last_decision="NONE")


def _base_obs() -> list[Observation]:
    return [
        Observation(
            kind=ObservationKind.USER_INPUT.value,
            payload={"text": "test input", "source": "cli"},
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


# ===================================================================
# Family 1: Authority Ambiguity
#
# Candidates cite real constitution clauses, but map ambiguously.
# The kernel should admit if citations resolve, regardless of semantic
# plausibility. Phase X does not evaluate semantic correctness.
# ===================================================================

class TestAuthorityAmbiguity:
    """
    Authority ambiguity tests: what happens when a candidate cites a
    valid clause that is arguably the wrong clause for its action?

    Phase X answer: if the citation resolves, admission passes gate 2.
    The kernel does not judge semantic fit between citation and action.
    """

    def test_notify_citing_exit_policy_still_admitted(
        self, constitution, repo_root, state,
    ):
        """
        A Notify candidate citing exit_policy is semantically dubious
        but structurally valid. Admission should pass.
        """
        obs = _base_obs()
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "citing exit policy for no reason"},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="User input exists, therefore we notify.",
            # Citing exit_policy for a Notify — semantically wrong, structurally valid
            clause_ref="constitution:v0.1.1@/exit_policy/exit_permitted",
            author=Author.REFLECTION.value,
        )
        just = Justification(
            text="Exit policy says exit is permitted; I'm citing it for Notify.",
            author=Author.REFLECTION.value,
        )
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=just,
            authority_citations=[
                "constitution:v0.1.1@/exit_policy/exit_permitted",
            ],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        # Structurally valid → admitted → ACTION
        assert output.decision.decision_type == DecisionType.ACTION.value

    def test_multiple_candidates_citing_different_invariants(
        self, constitution, repo_root, state,
    ):
        """
        Two valid candidates cite different invariants for the same action.
        Selector must pick deterministically, not by "better citation."
        """
        obs = _base_obs()

        def make(msg: str, citation_id: str) -> CandidateBundle:
            ar = ActionRequest(
                action_type=ActionType.NOTIFY.value,
                fields={"target": "stdout", "message": msg},
                author=Author.REFLECTION.value,
            )
            sc = ScopeClaim(
                observation_ids=[obs[0].id],
                claim=f"Citing {citation_id}",
                clause_ref=f"constitution:v0.1.1#{citation_id}",
                author=Author.REFLECTION.value,
            )
            just = Justification(
                text=f"Justified via {citation_id}",
                author=Author.REFLECTION.value,
            )
            return CandidateBundle(
                action_request=ar,
                scope_claim=sc,
                justification=just,
                authority_citations=[f"constitution:v0.1.1#{citation_id}"],
            )

        c1 = make("via INV-1", "INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT")
        c2 = make("via INV-2", "INV-AUTHORITY-CITED")

        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[c1, c2],
            repo_root=repo_root,
        )
        # Both admitted; selector picks by hash, not by citation quality
        assert output.decision.decision_type == DecisionType.ACTION.value
        assert output.decision.bundle is not None
        # Verify deterministic: run again
        output2 = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[c1, c2],
            repo_root=repo_root,
        )
        assert (
            output.decision.bundle.bundle_hash_hex()
            == output2.decision.bundle.bundle_hash_hex()
        )

    def test_citation_to_non_goals_still_resolves(
        self, constitution, repo_root, state,
    ):
        """
        Citing /non_goals/ is structurally valid (the pointer resolves)
        even though non_goals are not authorities for action.

        Phase X admits it. Semantic fitness is a Phase XI concern.
        """
        obs = _base_obs()
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "citing non-goals"},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="Non-goals say we shouldn't optimize outcomes.",
            clause_ref="constitution:v0.1.1@/non_goals/interpretive_rule",
            author=Author.REFLECTION.value,
        )
        just = Justification(
            text="Justified via non-goals interpretive rule.",
            author=Author.REFLECTION.value,
        )
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=just,
            authority_citations=[
                "constitution:v0.1.1@/non_goals/interpretive_rule",
            ],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        # Pointer resolves → admitted
        assert output.decision.decision_type == DecisionType.ACTION.value


# ===================================================================
# Family 2: ScopeClaim Adversarial
#
# LLM proposes structurally valid scope claims with wrong, empty,
# contradictory, or irrelevant content.
# ===================================================================

class TestScopeClaimAdversarial:
    """
    ScopeClaims that are structurally valid but semantically dubious.
    Phase X validates structure only — not truth.
    """

    def test_scope_claim_referencing_unrelated_observation(
        self, constitution, repo_root, state,
    ):
        """
        ScopeClaim references a valid observation ID, but the observation
        is a timestamp (unrelated to the claim text). Structurally valid.
        """
        obs = _base_obs()
        # Reference the timestamp observation, not the user_input
        timestamp_obs = obs[1]

        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "based on timestamp"},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[timestamp_obs.id],  # timestamp, not user_input
            claim="User said something interesting.",  # semantically wrong
            clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            author=Author.REFLECTION.value,
        )
        just = Justification(
            text="Timestamp proves user input exists.",
            author=Author.REFLECTION.value,
        )
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=just,
            authority_citations=[
                "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            ],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        # Valid observation ID + resolvable clause_ref → admitted
        assert output.decision.decision_type == DecisionType.ACTION.value

    def test_scope_claim_with_nonexistent_observation_id_refused(
        self, constitution, repo_root, state,
    ):
        """
        ScopeClaim references an observation ID that doesn't exist.
        Gate 3 must reject.
        """
        obs = _base_obs()
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "bad obs id"},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=["nonexistent-obs-id-12345"],
            claim="Refers to phantom observation.",
            clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            author=Author.REFLECTION.value,
        )
        just = Justification(
            text="Phantom justification.",
            author=Author.REFLECTION.value,
        )
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=just,
            authority_citations=[
                "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            ],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value

    def test_scope_claim_with_unresolvable_clause_ref_refused(
        self, constitution, repo_root, state,
    ):
        """
        ScopeClaim whose clause_ref doesn't resolve. Gate 3 rejects.
        """
        obs = _base_obs()
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "bad clause"},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="Citing imaginary clause.",
            clause_ref="constitution:v0.1.1#IMAGINARY-CLAUSE-99",
            author=Author.REFLECTION.value,
        )
        just = Justification(
            text="Imaginary justification.",
            author=Author.REFLECTION.value,
        )
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=just,
            authority_citations=[
                "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            ],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value

    def test_scope_claim_empty_string_claim_still_structurally_valid(
        self, constitution, repo_root, state,
    ):
        """
        Empty claim text but valid observation_ids and clause_ref.
        Phase X: structural validity only; empty string is valid.
        """
        obs = _base_obs()
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "empty claim"},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="",  # empty
            clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            author=Author.REFLECTION.value,
        )
        just = Justification(
            text="Justification for empty claim.",
            author=Author.REFLECTION.value,
        )
        candidate = CandidateBundle(
            action_request=ar,
            scope_claim=sc,
            justification=just,
            authority_citations=[
                "constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            ],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        # Empty claim is structurally valid → admitted
        assert output.decision.decision_type == DecisionType.ACTION.value

    def test_contradictory_scope_claims_both_admitted(
        self, constitution, repo_root, state,
    ):
        """
        Two candidates with contradictory claims citing different clauses.
        Both structurally valid → both admitted → selector picks by hash.

        This is the Phase X design: sovereignty, not correctness.
        """
        obs = _base_obs()

        def make(msg: str, claim: str) -> CandidateBundle:
            ar = ActionRequest(
                action_type=ActionType.NOTIFY.value,
                fields={"target": "stdout", "message": msg},
                author=Author.REFLECTION.value,
            )
            sc = ScopeClaim(
                observation_ids=[obs[0].id],
                claim=claim,
                clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
                author=Author.REFLECTION.value,
            )
            just = Justification(
                text=f"Justified: {claim}",
                author=Author.REFLECTION.value,
            )
            return CandidateBundle(
                action_request=ar, scope_claim=sc, justification=just,
                authority_citations=["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"],
            )

        c1 = make("user wants help", "User is asking for assistance.")
        c2 = make("user wants silence", "User is requesting no output.")

        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[c1, c2],
            repo_root=repo_root,
        )
        # Both admitted; selector picks one deterministically
        assert output.decision.decision_type == DecisionType.ACTION.value
        assert len(output.admitted) == 2


# ===================================================================
# Family 3: Budget / Filibuster
#
# Token overflow, candidate overflow, malformed input, resource
# exhaustion. All must result in REFUSE without side effects.
# ===================================================================

class TestBudgetFilibuster:
    """
    Budget exhaustion and filibuster scenarios.
    The anti-filibuster rule (constitution reflection_policy):
      "If budgets are exhausted without an admitted ActionRequest,
       REFUSE with BUDGET_EXHAUSTED."
    """

    def test_token_budget_exactly_at_limit_not_refused(
        self, constitution, repo_root, state,
    ):
        """Tokens at exactly max_total_tokens_per_cycle → NOT budget-refused."""
        max_tokens = constitution.max_total_tokens_per_cycle()
        obs = [
            Observation(
                kind=ObservationKind.USER_INPUT.value,
                payload={"text": "at limit", "source": "cli"},
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
                    "llm_output_token_count": max_tokens,  # exactly at limit
                    "llm_candidates_reported": 1,
                    "llm_parse_errors": 0,
                },
                author=Author.HOST.value,
            ),
        ]
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "at limit"},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="At budget limit.",
            clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            author=Author.REFLECTION.value,
        )
        just = Justification(text="At limit.", author=Author.REFLECTION.value)
        candidate = CandidateBundle(
            action_request=ar, scope_claim=sc, justification=just,
            authority_citations=["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        # At limit, not over → admitted
        assert output.decision.decision_type == DecisionType.ACTION.value

    def test_token_budget_one_over_limit_refused(
        self, constitution, repo_root, state,
    ):
        """Tokens at max+1 → REFUSE with BUDGET_EXHAUSTED."""
        max_tokens = constitution.max_total_tokens_per_cycle()
        obs = [
            Observation(
                kind=ObservationKind.USER_INPUT.value,
                payload={"text": "over limit", "source": "cli"},
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
                    "llm_output_token_count": max_tokens + 1,
                    "llm_candidates_reported": 1,
                    "llm_parse_errors": 0,
                },
                author=Author.HOST.value,
            ),
        ]
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "over limit"},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="Over budget.",
            clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            author=Author.REFLECTION.value,
        )
        just = Justification(text="Over limit.", author=Author.REFLECTION.value)
        candidate = CandidateBundle(
            action_request=ar, scope_claim=sc, justification=just,
            authority_citations=["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value
        assert output.decision.refusal.reason_code == RefusalReasonCode.BUDGET_EXHAUSTED.value
        assert output.decision.warrant is None

    def test_zero_candidates_refuses_cleanly(
        self, constitution, repo_root, state,
    ):
        """No candidates at all → REFUSE (not crash, not EXIT)."""
        obs = _base_obs()
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value
        assert output.decision.refusal.reason_code == RefusalReasonCode.NO_ADMISSIBLE_ACTION.value

    def test_five_invalid_candidates_all_refused(
        self, constitution, repo_root, state,
    ):
        """
        Five candidates, all structurally invalid (missing fields, bad types,
        unresolvable citations). All rejected at admission → REFUSE.
        No side effects, no warrants.
        """
        obs = _base_obs()
        candidates = []
        for i in range(5):
            ar = ActionRequest(
                action_type="NonexistentAction",  # unknown type → gate 1 fail
                fields={"bogus": i},
                author=Author.REFLECTION.value,
            )
            candidates.append(CandidateBundle(
                action_request=ar,
                scope_claim=None,
                justification=None,
                authority_citations=["constitution:v0.1.1#FAKE-CLAUSE"],
            ))

        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=candidates,
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value
        assert output.decision.warrant is None
        assert len(output.rejected) == 5
        assert len(output.admitted) == 0

    def test_message_at_max_length_admitted(
        self, constitution, repo_root, state,
    ):
        """Notify message at exactly max_len (2000) → admitted."""
        obs = _base_obs()
        msg = "X" * 2000
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": msg},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="Max length message.",
            clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            author=Author.REFLECTION.value,
        )
        just = Justification(text="At max len.", author=Author.REFLECTION.value)
        candidate = CandidateBundle(
            action_request=ar, scope_claim=sc, justification=just,
            authority_citations=["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.ACTION.value

    def test_message_over_max_length_refused(
        self, constitution, repo_root, state,
    ):
        """Notify message at max_len+1 (2001) → admission rejects."""
        obs = _base_obs()
        msg = "X" * 2001
        ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": msg},
            author=Author.REFLECTION.value,
        )
        sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="Over max length.",
            clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            author=Author.REFLECTION.value,
        )
        just = Justification(text="Over max len.", author=Author.REFLECTION.value)
        candidate = CandidateBundle(
            action_request=ar, scope_claim=sc, justification=just,
            authority_citations=["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"],
        )
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value

    def test_log_append_exceeds_max_lines_per_warrant_refused(
        self, constitution, repo_root, state,
    ):
        """LogAppend with 51 lines (max=50) → admission rejects."""
        obs = _base_obs()
        lines = [f'{{"line": {i}}}' for i in range(51)]
        ar = ActionRequest(
            action_type=ActionType.LOG_APPEND.value,
            fields={"log_name": "observations", "jsonl_lines": lines},
            author=Author.KERNEL.value,
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
            internal_state=state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value

    def test_log_append_line_exceeds_max_chars_refused(
        self, constitution, repo_root, state,
    ):
        """LogAppend with one line at 10001 chars (max=10000) → admission rejects."""
        obs = _base_obs()
        long_line = "X" * 10001
        ar = ActionRequest(
            action_type=ActionType.LOG_APPEND.value,
            fields={"log_name": "observations", "jsonl_lines": [long_line]},
            author=Author.KERNEL.value,
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
            internal_state=state,
            candidates=[candidate],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value

    def test_mixed_valid_and_invalid_candidates(
        self, constitution, repo_root, state,
    ):
        """
        Three candidates: one valid, two invalid.
        Admission rejects 2, admits 1 → ACTION (not REFUSE).
        Demonstrates that one good candidate among garbage is sufficient.
        """
        obs = _base_obs()

        # Valid candidate
        valid_ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "valid"},
            author=Author.REFLECTION.value,
        )
        valid_sc = ScopeClaim(
            observation_ids=[obs[0].id],
            claim="Valid claim.",
            clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
            author=Author.REFLECTION.value,
        )
        valid_just = Justification(text="Valid.", author=Author.REFLECTION.value)
        valid = CandidateBundle(
            action_request=valid_ar, scope_claim=valid_sc, justification=valid_just,
            authority_citations=["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"],
        )

        # Invalid: unknown action type
        invalid1 = CandidateBundle(
            action_request=ActionRequest(
                action_type="BadType", fields={}, author=Author.REFLECTION.value,
            ),
            scope_claim=None, justification=None,
            authority_citations=["constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"],
        )

        # Invalid: unresolvable citation
        invalid2_ar = ActionRequest(
            action_type=ActionType.NOTIFY.value,
            fields={"target": "stdout", "message": "bad citation"},
            author=Author.REFLECTION.value,
        )
        invalid2 = CandidateBundle(
            action_request=invalid2_ar,
            scope_claim=ScopeClaim(
                observation_ids=[obs[0].id], claim="cite bad",
                clause_ref="constitution:v0.1.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT",
                author=Author.REFLECTION.value,
            ),
            justification=Justification(text="bad cite", author=Author.REFLECTION.value),
            authority_citations=["constitution:v0.1.1#DOES-NOT-EXIST"],
        )

        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[invalid1, valid, invalid2],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.ACTION.value
        assert len(output.admitted) == 1
        assert len(output.rejected) == 2
        assert output.decision.bundle.bundle_hash_hex() == valid.bundle_hash_hex()

    def test_all_observations_zero_budget_no_refuse(
        self, constitution, repo_root, state,
    ):
        """
        Zero tokens reported → not budget-exhausted.
        With no candidates → REFUSE for NO_ADMISSIBLE_ACTION (not budget).
        """
        obs = [
            Observation(
                kind=ObservationKind.USER_INPUT.value,
                payload={"text": "zero budget", "source": "cli"},
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
                    "llm_output_token_count": 0,
                    "llm_candidates_reported": 0,
                    "llm_parse_errors": 0,
                },
                author=Author.HOST.value,
            ),
        ]
        output = policy_core(
            observations=obs,
            constitution=constitution,
            internal_state=state,
            candidates=[],
            repo_root=repo_root,
        )
        assert output.decision.decision_type == DecisionType.REFUSE.value
        assert output.decision.refusal.reason_code == RefusalReasonCode.NO_ADMISSIBLE_ACTION.value
