"""
SIR-1 v0.1 Enforcement Gate

Implements the Post-Justify Enforcement Gate per preregistration §10.

Gate Rule (§10.2):
    Only effects causally downstream of VALID_AUTHORITY_CLAIM are permitted.

Gate Properties (§10.1):
- Operates exclusively on classified claims
- Does not consult agent internals
- Enforces authority at the level of effects, not reasoning
- Evaluates validity relative to current law-state
- Is auditable and deterministic

This module is frozen at SIR-1 v0.1 preregistration.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List, Set
import time

import sys
from pathlib import Path

# Import SIR-0 types (DO NOT MODIFY)
SIR0_SRC = Path(__file__).parent.parent.parent / "SIR-0" / "src"
sys.path.insert(0, str(SIR0_SRC))

from claim_types import (
    AuthorityClaim,
    ClaimClassification,
    ClassificationResult,
)

from .capability_state import CapabilityState


class GateDecision(Enum):
    """Enforcement gate decision outcomes."""
    PERMIT = "PERMIT"
    REFUSE = "REFUSE"


@dataclass
class EnforcementGateDecision:
    """
    Per §18.2: Enforcement gate decision record.

    Records the gate's decision for audit.
    """
    action: str
    authority_claim_id: Optional[str]
    authority_valid: bool
    scope_match: bool
    capability_present: bool
    decision: GateDecision
    reason: Optional[str]
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "authority_claim_id": self.authority_claim_id,
            "authority_valid": self.authority_valid,
            "scope_match": self.scope_match,
            "capability_present": self.capability_present,
            "decision": self.decision.value,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


@dataclass
class RefusalEvent:
    """
    Per §18.3: Refusal event record.

    Refusal is an authority-bearing act attributed to SYSTEM_AUTHORITY.
    """
    claim_id: str
    claim_classification: str
    refusal_reason: str
    timestamp: float
    responsibility_actor: str = "SYSTEM_AUTHORITY"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_classification": self.claim_classification,
            "refusal_reason": self.refusal_reason,
            "timestamp": self.timestamp,
            "responsibility_actor": self.responsibility_actor,
        }


# Gated actions and their required scopes
GATED_ACTIONS: Dict[str, str] = {
    "OPEN_SHORTCUT": "SCOPE/ENV/SHORTCUT_UNLOCK",
}


class EnforcementGate:
    """
    Post-Justify Enforcement Gate per §7.3 and §10.

    Purpose: Protect effects from unauthorized execution.

    Invariant: Only effects causally downstream of VALID_AUTHORITY_CLAIM
    are permitted.
    """

    def __init__(self, capability_state: CapabilityState):
        self._capability_state = capability_state
        self._refusal_log: List[RefusalEvent] = []
        self._decision_log: List[EnforcementGateDecision] = []

    def reset(self) -> None:
        """Reset gate state at episode start."""
        self._refusal_log = []
        self._decision_log = []

    def is_gated_action(self, action: str) -> bool:
        """Check if an action requires authority gating."""
        return action in GATED_ACTIONS

    def get_required_scope(self, action: str) -> Optional[str]:
        """Get the scope required to authorize a gated action."""
        return GATED_ACTIONS.get(action)

    def evaluate(
        self,
        selected_action: str,
        valid_claims: List[ClassificationResult],
        step: int,
    ) -> EnforcementGateDecision:
        """
        Evaluate enforcement gate for a selected action.

        Per §10.4 Gating Behavior for OPEN_SHORTCUT:
        - With valid claim + scope match → PERMIT (+ UNLOCK if needed)
        - Without valid claim → REFUSE
        - With invalid claim → REFUSE

        Per §11.4: If agent selects gated action without authority,
        gate blocks, NO re-selection occurs.
        """
        timestamp = time.monotonic()

        # Non-gated actions always pass
        if not self.is_gated_action(selected_action):
            decision = EnforcementGateDecision(
                action=selected_action,
                authority_claim_id=None,
                authority_valid=True,  # Non-gated = no authority needed
                scope_match=True,
                capability_present=True,
                decision=GateDecision.PERMIT,
                reason="non_gated_action",
                timestamp=timestamp,
            )
            self._decision_log.append(decision)
            return decision

        # Gated action: check for valid authority
        required_scope = self.get_required_scope(selected_action)
        capability_present = self._capability_state.is_action_unlocked(selected_action)

        # Find a valid claim with matching scope
        authorizing_claim: Optional[ClassificationResult] = None
        for result in valid_claims:
            if (result.classification == ClaimClassification.VALID_AUTHORITY_CLAIM and
                    result.claim.scope == required_scope):
                authorizing_claim = result
                break

        if authorizing_claim is not None:
            # Valid authority present
            decision = EnforcementGateDecision(
                action=selected_action,
                authority_claim_id=authorizing_claim.claim.claim_id,
                authority_valid=True,
                scope_match=True,
                capability_present=capability_present,
                decision=GateDecision.PERMIT,
                reason="valid_authority_with_scope",
                timestamp=timestamp,
            )
            self._decision_log.append(decision)

            # Unlock capability if not already unlocked
            if not capability_present:
                self._capability_state.unlock_action(
                    selected_action,
                    authorizing_claim.claim.claim_id,
                    step,
                )

            return decision

        # No valid authority: REFUSE
        # Per §11.3: Silent ignoring prohibited, must log refusal
        decision = EnforcementGateDecision(
            action=selected_action,
            authority_claim_id=None,
            authority_valid=False,
            scope_match=False,
            capability_present=capability_present,
            decision=GateDecision.REFUSE,
            reason="no_valid_authority_for_gated_action",
            timestamp=timestamp,
        )
        self._decision_log.append(decision)

        return decision

    def record_claim_refusal(
        self,
        claim: AuthorityClaim,
        classification: ClaimClassification,
        reason: str,
    ) -> RefusalEvent:
        """
        Record refusal of an invalid claim.

        Per §11.1: Refusal must be logged.
        Per §11.3: Silent ignoring is forbidden.
        """
        event = RefusalEvent(
            claim_id=claim.claim_id,
            claim_classification=classification.value,
            refusal_reason=reason,
            timestamp=time.monotonic(),
        )
        self._refusal_log.append(event)
        return event

    def get_refusal_log(self) -> List[RefusalEvent]:
        """Return copy of refusal log."""
        return list(self._refusal_log)

    def get_decision_log(self) -> List[EnforcementGateDecision]:
        """Return copy of decision log."""
        return list(self._decision_log)

    def get_refusal_summary(self) -> Dict[str, int]:
        """Summarize refusals by reason."""
        summary: Dict[str, int] = {}
        for event in self._refusal_log:
            summary[event.refusal_reason] = summary.get(event.refusal_reason, 0) + 1
        return summary

    def get_enforcement_summary(self) -> Dict[str, int]:
        """Summarize enforcement decisions."""
        summary: Dict[str, int] = {"PERMIT": 0, "REFUSE": 0}
        for decision in self._decision_log:
            summary[decision.decision.value] += 1
        return summary
