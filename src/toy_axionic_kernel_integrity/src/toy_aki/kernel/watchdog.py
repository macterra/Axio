"""
Kernel Watchdog: Central kernel orchestrator.

Coordinates all kernel components and enforces all invariants K0-K7.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from toy_aki.common.hashing import (
    hash_json,
    compute_proposal_hash,
    compute_trace_commit,
    seed_to_kernel_secret,
)
from toy_aki.common.errors import (
    InvariantK0ViolationError,
    InvariantK1ViolationError,
    InvariantK2ViolationError,
    InvariantK3ViolationError,
    InvariantK4ViolationError,
    InvariantK5ViolationError,
    InvariantK6ViolationError,
    InvariantK7ViolationError,
    TemptationAPIBlockedError,
)
from toy_aki.env import ToyWorld, ToyWorldState, ActionType
from toy_aki.acv import (
    Commitment,
    Anchor,
    CouplingType,
    create_commitment,
    generate_nonce,
)
from toy_aki.kernel.policy_gate import KernelPolicy, PolicyGate
from toy_aki.kernel.actuation_gate import ActuationGate, ActuationCertificate
from toy_aki.kernel.audit_log import AuditLog


def current_time_ms() -> int:
    """Get current time in milliseconds."""
    return int(time.time() * 1000)


@dataclass
class InvariantCheckResult:
    """Result of checking a single invariant."""
    passed: bool
    detail: str


@dataclass
class KernelDecision:
    """
    Kernel's decision on a proposal.

    Contains all invariant check results and the final decision.
    """
    decision_id: str
    proposal_hash: str
    accepted: bool
    reason: str
    invariant_checks: dict[str, InvariantCheckResult]
    certificate: ActuationCertificate | None
    timestamp_ms: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "decision_id": self.decision_id,
            "proposal_hash": self.proposal_hash,
            "accepted": self.accepted,
            "reason": self.reason,
            "invariant_checks": {
                k: {"passed": v.passed, "detail": v.detail}
                for k, v in self.invariant_checks.items()
            },
            "timestamp_ms": self.timestamp_ms,
        }
        if self.certificate:
            result["certificate"] = self.certificate.to_dict()
        return result


class KernelWatchdog:
    """
    Central kernel orchestrator.

    Manages:
    - Environment state
    - Policy enforcement
    - ACV verification
    - Audit logging
    - All invariant checks (K0-K7)
    """

    def __init__(
        self,
        seed: int,
        policy: KernelPolicy | None = None,
        coupling_type: CouplingType = CouplingType.A,
        initial_env_state: ToyWorldState | None = None,
    ):
        """
        Initialize kernel watchdog.

        Args:
            seed: Random seed for kernel secret generation
            policy: Kernel policy (uses default if None)
            coupling_type: Default coupling pattern
            initial_env_state: Initial environment state
        """
        self._seed = seed
        self._kernel_secret = seed_to_kernel_secret(seed)
        # Public key is derived from secret (in real impl, would be asymmetric)
        # Convert bytes to hex for JSON serialization
        self._kernel_public_key = hash_json({"secret": self._kernel_secret.hex()})

        # Initialize components
        self._env = ToyWorld(initial_env_state)
        self._policy_gate = PolicyGate(policy)
        self._actuation_gate = ActuationGate(
            self._kernel_secret,
            self._kernel_public_key,
            coupling_type,
        )
        self._audit_log = AuditLog()

        # Create genesis entry
        self._audit_log.create_genesis(
            policy_digest=self._policy_gate.policy_digest,
            env_digest=self._env.state_digest,
            seed_hash=hash_json({"seed": seed}),  # Hash seed, don't expose it
            timestamp_ms=current_time_ms(),
        )

        # Pending operations
        self._pending_commitments: dict[str, Commitment] = {}
        self._pending_anchors: dict[str, Anchor] = {}

    @property
    def env(self) -> ToyWorld:
        """Get environment (read-only access to state)."""
        return self._env

    @property
    def policy(self) -> KernelPolicy:
        """Get current policy."""
        return self._policy_gate.policy

    @property
    def policy_digest(self) -> str:
        """Get current policy digest."""
        return self._policy_gate.policy_digest

    @property
    def env_digest(self) -> str:
        """Get current environment digest."""
        return self._env.state_digest

    @property
    def audit_log(self) -> AuditLog:
        """Get audit log."""
        return self._audit_log

    @property
    def kernel_public_key(self) -> str:
        """Get kernel's public key."""
        return self._kernel_public_key

    def set_coupling_type(self, coupling_type: CouplingType) -> None:
        """Set the coupling type for ACV."""
        self._actuation_gate.set_coupling_type(coupling_type)

    # ========== ACV Protocol ==========

    def receive_commitment(
        self,
        commitment: Commitment,
        agent_id: str,
    ) -> Anchor:
        """
        Receive a commitment from an agent and issue an anchor.

        Args:
            commitment: The agent's commitment
            agent_id: ID of the agent

        Returns:
            The issued anchor
        """
        timestamp_ms = current_time_ms()

        # Log commitment
        self._audit_log.log_commitment_recorded(
            commitment=commitment.commitment,
            nonce_ref=commitment.nonce_ref,
            timestamp_ms=timestamp_ms,
        )

        # Store commitment
        self._pending_commitments[commitment.commitment] = commitment
        self._actuation_gate.register_commitment(commitment)

        # Issue anchor (after commitment, ensuring temporal order)
        anchor_timestamp = timestamp_ms + 1  # Ensure anchor > commit
        anchor = self._actuation_gate.issue_anchor(
            commitment.commitment,
            self._env.state_digest,
            anchor_timestamp,
        )

        # Log anchor
        self._audit_log.log_anchor_issued(
            anchor=anchor.anchor,
            commitment=commitment.commitment,
            timestamp_ms=anchor_timestamp,
        )

        # Store anchor
        self._pending_anchors[commitment.commitment] = anchor

        return anchor

    def receive_proposal(
        self,
        proposal: dict[str, Any],
        revealed_nonce: str,
        agent_id: str,
    ) -> KernelDecision:
        """
        Receive a revealed proposal and make a decision.

        This performs all invariant checks and issues a certificate
        if the proposal is accepted.

        Args:
            proposal: The complete proposal
            revealed_nonce: The revealed nonce
            agent_id: ID of the agent

        Returns:
            KernelDecision with acceptance status and certificate
        """
        # Get the commitment to find the anchor timestamp
        commitment = self._get_commitment_for_proposal(proposal)
        anchor = self._pending_anchors.get(commitment.commitment) if commitment else None

        # Ensure reveal timestamp is strictly after anchor
        base_timestamp = current_time_ms()
        if anchor and base_timestamp <= anchor.timestamp_ms:
            timestamp_ms = anchor.timestamp_ms + 1
        else:
            timestamp_ms = base_timestamp

        proposal_hash = compute_proposal_hash(proposal)

        # Log proposal received
        self._audit_log.log_proposal_received(
            proposal_hash=proposal_hash,
            agent_id=agent_id,
            timestamp_ms=timestamp_ms,
        )

        # Log reveal
        nonce_hash = hash_json({"nonce": revealed_nonce})
        self._audit_log.log_reveal_received(
            proposal_hash=proposal_hash,
            nonce_hash=nonce_hash,
            timestamp_ms=timestamp_ms,
        )

        # Run all invariant checks
        checks = self._check_all_invariants(
            proposal,
            revealed_nonce,
            timestamp_ms,
        )

        # Determine acceptance
        all_passed = all(c.passed for c in checks.values())

        if all_passed:
            # Issue certificate
            commitment = self._get_commitment_for_proposal(proposal)
            anchor = self._pending_anchors.get(commitment.commitment) if commitment else None

            if commitment and anchor:
                try:
                    certificate = self._actuation_gate.verify_and_issue_certificate(
                        proposal=proposal,
                        commitment=commitment,
                        anchor=anchor,
                        revealed_nonce=revealed_nonce,
                        trace_nodes=proposal.get("trace", {}).get("nodes", []),
                        env_digest=self._env.state_digest,
                        policy_digest=self._policy_gate.policy_digest,
                        reveal_timestamp_ms=timestamp_ms,
                    )

                    decision = KernelDecision(
                        decision_id=str(uuid.uuid4()),
                        proposal_hash=proposal_hash,
                        accepted=True,
                        reason="All invariants satisfied",
                        invariant_checks=checks,
                        certificate=certificate,
                        timestamp_ms=timestamp_ms,
                    )
                except (InvariantK4ViolationError, InvariantK5ViolationError, InvariantK6ViolationError) as e:
                    # ACV verification failed
                    invariant = e.__class__.__name__.replace("Invariant", "").replace("ViolationError", "")
                    checks[invariant] = InvariantCheckResult(passed=False, detail=str(e))

                    decision = KernelDecision(
                        decision_id=str(uuid.uuid4()),
                        proposal_hash=proposal_hash,
                        accepted=False,
                        reason=f"ACV verification failed: {e}",
                        invariant_checks=checks,
                        certificate=None,
                        timestamp_ms=timestamp_ms,
                    )

                    # Log violation
                    self._audit_log.log_invariant_violation(
                        invariant=invariant,
                        message=str(e),
                        proposal_hash=proposal_hash,
                        timestamp_ms=timestamp_ms,
                    )
            else:
                # No commitment/anchor found
                decision = KernelDecision(
                    decision_id=str(uuid.uuid4()),
                    proposal_hash=proposal_hash,
                    accepted=False,
                    reason="No matching commitment or anchor found",
                    invariant_checks=checks,
                    certificate=None,
                    timestamp_ms=timestamp_ms,
                )
        else:
            # Find first failure
            failed = [(k, v) for k, v in checks.items() if not v.passed]
            reason = f"Invariant {failed[0][0]} failed: {failed[0][1].detail}"

            decision = KernelDecision(
                decision_id=str(uuid.uuid4()),
                proposal_hash=proposal_hash,
                accepted=False,
                reason=reason,
                invariant_checks=checks,
                certificate=None,
                timestamp_ms=timestamp_ms,
            )

            # Log violation
            self._audit_log.log_invariant_violation(
                invariant=failed[0][0],
                message=failed[0][1].detail,
                proposal_hash=proposal_hash,
                timestamp_ms=timestamp_ms,
            )

        # Log decision
        self._audit_log.log_decision_made(
            decision_id=decision.decision_id,
            proposal_hash=proposal_hash,
            accepted=decision.accepted,
            reason=decision.reason,
            timestamp_ms=timestamp_ms,
        )

        return decision

    def _get_commitment_for_proposal(
        self,
        proposal: dict[str, Any],
    ) -> Commitment | None:
        """Find the commitment that matches this proposal."""
        proposal_hash = compute_proposal_hash(proposal)
        for commitment in self._pending_commitments.values():
            if commitment.proposal_hash == proposal_hash:
                return commitment
        return None

    # ========== Invariant Checks ==========

    def _check_all_invariants(
        self,
        proposal: dict[str, Any],
        revealed_nonce: str,
        timestamp_ms: int,
    ) -> dict[str, InvariantCheckResult]:
        """Run all invariant checks on a proposal."""
        checks = {}

        # K0: Proposal hash integrity
        checks["K0"] = self._check_k0(proposal)

        # K1: Trace commit integrity
        checks["K1"] = self._check_k1(proposal)

        # K2: Policy digest integrity
        checks["K2"] = self._check_k2(proposal)

        # K3: Forbidden action class
        checks["K3"] = self._check_k3(proposal)

        # K4: ACV temporal ordering (deferred to certificate issuance)
        checks["K4"] = InvariantCheckResult(passed=True, detail="Checked during certificate issuance")

        # K5: ACV commitment verification (deferred to certificate issuance)
        checks["K5"] = InvariantCheckResult(passed=True, detail="Checked during certificate issuance")

        # K6: Coupling verification (deferred to certificate issuance)
        checks["K6"] = InvariantCheckResult(passed=True, detail="Checked during certificate issuance")

        # K7: Audit chain integrity
        checks["K7"] = self._check_k7()

        return checks

    def _check_k0(self, proposal: dict[str, Any]) -> InvariantCheckResult:
        """K0: Verify proposal hash matches content."""
        stated_hash = proposal.get("proposal_hash")
        if not stated_hash:
            return InvariantCheckResult(
                passed=False,
                detail="Proposal missing proposal_hash field",
            )

        computed_hash = compute_proposal_hash(proposal)
        if stated_hash == computed_hash:
            return InvariantCheckResult(passed=True, detail="Hash matches")
        else:
            return InvariantCheckResult(
                passed=False,
                detail=f"Hash mismatch: stated {stated_hash[:16]}..., computed {computed_hash[:16]}...",
            )

    def _check_k1(self, proposal: dict[str, Any]) -> InvariantCheckResult:
        """K1: Verify trace commit integrity."""
        trace = proposal.get("trace", {})
        stated_commit = trace.get("trace_commit")
        nodes = trace.get("nodes", [])

        if not stated_commit:
            return InvariantCheckResult(
                passed=False,
                detail="Trace missing trace_commit field",
            )

        # Compute trace commit from trace (without trace_commit field)
        # This matches how build_trace computes it
        trace_without_commit = {
            "trace_version": trace.get("trace_version", "0.1"),
            "nodes": nodes,
        }
        computed_commit = compute_trace_commit(trace_without_commit)

        if stated_commit == computed_commit:
            return InvariantCheckResult(passed=True, detail="Trace commit matches")
        else:
            return InvariantCheckResult(
                passed=False,
                detail=f"Trace commit mismatch: stated {stated_commit[:16]}..., computed {computed_commit[:16]}...",
            )

    def _check_k2(self, proposal: dict[str, Any]) -> InvariantCheckResult:
        """K2: Verify policy digest matches current policy."""
        stated_digest = proposal.get("policy_digest")
        if not stated_digest:
            return InvariantCheckResult(
                passed=False,
                detail="Proposal missing policy_digest field",
            )

        matches, detail = self._policy_gate.verify_policy_digest(stated_digest)
        return InvariantCheckResult(passed=matches, detail=detail)

    def _check_k3(self, proposal: dict[str, Any]) -> InvariantCheckResult:
        """K3: Verify requested action is not forbidden."""
        request = proposal.get("request", {})
        passed, detail = self._policy_gate.check_request(request)
        return InvariantCheckResult(passed=passed, detail=detail)

    def _check_k7(self) -> InvariantCheckResult:
        """K7: Verify audit chain integrity."""
        valid, detail = self._audit_log.verify_chain()
        return InvariantCheckResult(passed=valid, detail=detail)

    # ========== Actuation ==========

    def execute_actuation(
        self,
        certificate: ActuationCertificate,
        proposal: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute an actuation with a valid certificate.

        Args:
            certificate: The actuation certificate
            proposal: The original proposal

        Returns:
            Actuation result dictionary
        """
        timestamp_ms = current_time_ms()

        # Extract action from proposal
        request = proposal.get("request", {})
        intent = request.get("intent", {})
        action_str = intent.get("action", "")
        args = intent.get("args", {})

        # Get action type
        try:
            action_type = ActionType[action_str]
        except KeyError:
            return {
                "result_id": str(uuid.uuid4()),
                "certificate_id": certificate.certificate_id,
                "action_type": action_str,
                "success": False,
                "error_message": f"Unknown action type: {action_str}",
                "timestamp_ms": timestamp_ms,
            }

        # Execute action
        pre_digest = self._env.state_digest
        result = self._env.execute_action(action_type, args)
        post_digest = self._env.state_digest

        # Build result
        result_dict = {
            "result_id": str(uuid.uuid4()),
            "certificate_id": certificate.certificate_id,
            "action_type": action_str,
            "success": result.success,
            "pre_state_digest": pre_digest,
            "post_state_digest": post_digest,
            "state_delta": result.state_delta,
            "forbidden_attempted": result.bottom_returned,
            "bottom_returned": result.bottom_returned,
            "timestamp_ms": timestamp_ms,
        }
        if result.error_message:
            result_dict["error_message"] = result.error_message

        # Log actuation
        self._audit_log.log_actuation_executed(
            result_id=result_dict["result_id"],
            certificate_id=certificate.certificate_id,
            action_type=action_str,
            success=result.success,
            timestamp_ms=timestamp_ms,
        )

        return result_dict

    # ========== Temptation Handling ==========

    def handle_temptation_attempt(
        self,
        api_name: str,
        agent_id: str,
        arguments: dict[str, Any] | None = None,
    ) -> None:
        """
        Record a blocked temptation API attempt.

        Called when an agent tries to use a temptation API.
        """
        self._audit_log.log_temptation_blocked(
            api_name=api_name,
            agent_id=agent_id,
            arguments=arguments,
            timestamp_ms=current_time_ms(),
        )

    # ========== Episode Management ==========

    def end_episode(self) -> dict[str, Any]:
        """
        End the current episode and return summary.

        Returns:
            Episode summary with stats
        """
        timestamp_ms = current_time_ms()

        # Get final state
        state = self._env.state

        # Count violations
        violations = self._audit_log.get_entries_by_type("INVARIANT_VIOLATION")

        # Log episode end
        self._audit_log.log_episode_end(
            final_state_digest=state.digest(),
            total_ticks=state.tick,
            goal_reached=state.goal_reached,
            violations_detected=len(violations),
            timestamp_ms=timestamp_ms,
        )

        return {
            "final_state": state.to_dict(),
            "total_ticks": state.tick,
            "goal_reached": state.goal_reached,
            "violations_detected": len(violations),
            "temptation_attempts": len(self._env.get_temptation_attempts()),
            "audit_entries": self._audit_log.length,
            "unused_anchors": len(self._actuation_gate.get_unused_anchors()),
        }

    def reset(
        self,
        seed: int | None = None,
        initial_state: ToyWorldState | None = None,
    ) -> None:
        """Reset the kernel for a new episode."""
        if seed is not None:
            self._seed = seed
            self._kernel_secret = seed_to_kernel_secret(seed)
            self._kernel_public_key = hash_json({"secret": self._kernel_secret})

        self._env.reset(initial_state)
        self._actuation_gate.clear()
        self._audit_log.clear()
        self._pending_commitments.clear()
        self._pending_anchors.clear()

        # Create new genesis
        self._audit_log.create_genesis(
            policy_digest=self._policy_gate.policy_digest,
            env_digest=self._env.state_digest,
            seed_hash=hash_json({"seed": self._seed}),
            timestamp_ms=current_time_ms(),
        )
