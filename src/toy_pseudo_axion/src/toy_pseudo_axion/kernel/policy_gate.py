"""Policy gate for evaluating proposals."""

from dataclasses import dataclass, field
from typing import Any, Optional
from pathlib import Path

from ..common.hashing import hash_json, derive_kernel_secret
from ..common.schema_load import validate_proposal, SchemaValidationError
from ..common.errors import InvariantViolationError
from .invariants import check_all_invariants, has_fatal_violation, Witness
from .capability import CapabilityManager, create_capability_scope
from .audit_log import AuditLog, GENESIS_HASH
from .watchdog import WatchdogTimer, NoOpWatchdog


@dataclass
class Decision:
    """Kernel decision on a proposal."""
    verdict: str  # "allow", "deny", "allow_with_constraints"
    witnesses: list[Witness]
    notes: str
    tokens: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "witnesses": [w.to_dict() for w in self.witnesses],
            "notes": self.notes,
            "tokens": self.tokens
        }


class PolicyGate:
    """Kernel policy gate for evaluating proposals and issuing tokens."""

    def __init__(
        self,
        audit_log: AuditLog,
        seed: int = 0,
        timeout_ms: int = 200,
        use_watchdog: bool = True
    ):
        """Initialize policy gate.

        Args:
            audit_log: Audit log instance
            seed: Suite seed for kernel secret derivation
            timeout_ms: Watchdog timeout in milliseconds
            use_watchdog: Whether to use watchdog timer
        """
        self.audit_log = audit_log
        self.kernel_secret = derive_kernel_secret(seed)
        self.capability_manager = CapabilityManager(kernel_secret=self.kernel_secret)

        if use_watchdog:
            self.watchdog = WatchdogTimer(
                timeout_ms=timeout_ms,
                on_timeout=self._handle_watchdog_timeout
            )
        else:
            self.watchdog = NoOpWatchdog(timeout_ms=timeout_ms)

    def _handle_watchdog_timeout(self, proposal_hash: Optional[str]) -> None:
        """Handle watchdog timeout by logging FATAL_HANG."""
        self.audit_log.append_fatal_hang(proposal_hash)

    def evaluate(self, proposal: dict) -> Decision:
        """Evaluate a proposal and return a decision.

        This performs:
        1. Schema validation
        2. Invariant checks
        3. Token issuance (if allowed)
        4. Audit log append

        Args:
            proposal: Proposal dict to evaluate

        Returns:
            Decision with verdict, witnesses, and tokens
        """
        proposal_hash = hash_json(proposal)
        trace = proposal.get("trace", {})
        trace_hash = hash_json(trace)

        witnesses: list[Witness] = []
        tokens: list[dict] = []

        with self.watchdog.guard(proposal_hash):
            # Step 1: Schema validation
            try:
                validate_proposal(proposal)
            except SchemaValidationError as e:
                witness = Witness(
                    invariant="SCHEMA_VALIDATION",
                    severity="fatal",
                    message=str(e),
                    data_hash=hash_json({"error": str(e)})
                )
                witnesses.append(witness)

                decision = Decision(
                    verdict="deny",
                    witnesses=witnesses,
                    notes="Schema validation failed"
                )

                self._log_decision(
                    "POLICY_DECISION",
                    proposal_hash,
                    trace_hash,
                    decision
                )

                return decision

            # Step 2: Invariant checks
            invariant_witnesses = check_all_invariants(proposal)
            witnesses.extend(invariant_witnesses)

            if has_fatal_violation(witnesses):
                decision = Decision(
                    verdict="deny",
                    witnesses=witnesses,
                    notes="Invariant violations detected"
                )

                self._log_decision(
                    "POLICY_DECISION",
                    proposal_hash,
                    trace_hash,
                    decision
                )

                return decision

            # Step 3: Issue tokens for requested capabilities
            requested_caps = proposal.get("requested_capabilities", [])
            for cap_req in requested_caps:
                capability = cap_req.get("capability")
                scope = cap_req.get("scope")
                justification = cap_req.get("justification", "")

                token = self.capability_manager.issue_token(
                    capability=capability,
                    scope=scope,
                    proposal_hash=proposal_hash,
                    trace_hash=trace_hash,
                    justification=justification
                )
                tokens.append(token)

            # Step 4: Return allow decision
            notes = "Proposal approved"
            if witnesses:
                notes = "Proposal approved with warnings"

            decision = Decision(
                verdict="allow" if not witnesses else "allow_with_constraints",
                witnesses=witnesses,
                notes=notes,
                tokens=tokens
            )

            self._log_decision(
                "POLICY_DECISION",
                proposal_hash,
                trace_hash,
                decision
            )

            return decision

    def _log_decision(
        self,
        event: str,
        proposal_hash: str,
        trace_hash: str,
        decision: Decision
    ) -> None:
        """Log a decision to the audit log."""
        self.audit_log.append(
            event=event,
            proposal_hash=proposal_hash,
            trace_hash=trace_hash,
            verdict=decision.verdict,
            notes=decision.notes,
            witnesses=[w.to_dict() for w in decision.witnesses],
            capability_tokens=decision.tokens
        )

    def verify_token_for_action(
        self,
        token: dict,
        proposal_hash: str,
        trace_hash: str,
        action_op: str
    ) -> Optional[Witness]:
        """Verify a token is valid for an action.

        Args:
            token: The capability token
            proposal_hash: Current proposal hash
            trace_hash: Current trace hash
            action_op: The action operation to perform

        Returns:
            Witness if invalid, None if valid
        """
        return self.capability_manager.verify_token(
            token=token,
            proposal_hash=proposal_hash,
            trace_hash=trace_hash,
            required_op=action_op
        )
