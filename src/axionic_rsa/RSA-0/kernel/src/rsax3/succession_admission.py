"""
RSA X-3 — Succession Admission Pipeline

Deterministic 7-gate pipeline for SuccessionProposal evaluation.
Gates:
  S1 — Completeness (INVALID_FIELD)
  S2 — Authority Citation Snapshot (AUTHORITY_CITATION_INVALID)
  S3 — Signature Verification (SIGNATURE_INVALID)
  S4 — Sovereign Match (PRIOR_SOVEREIGN_MISMATCH)
  S5 — Lineage Integrity (IDENTITY_CYCLE / LINEAGE_FORK)
  S6 — Constitutional Compliance (SUCCESSION_DISABLED)
  S7 — Per-Cycle Uniqueness (MULTIPLE_SUCCESSIONS_IN_CYCLE)

Pure, deterministic, no side effects.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from .artifacts_x3 import (
    SuccessionProposal,
    SuccessionAdmissionEvent,
    SuccessionAdmissionRecord,
    SuccessionRejectionRecord,
    SuccessionRejectionCode,
    SuccessionGate,
    SUCCESSION_REQUIRED_FIELDS,
    InternalStateX3,
)
from .signature_x3 import verify_succession_proposal
import re

# Ed25519 key format pattern
_ED25519_KEY_PATTERN = re.compile(r"^ed25519:[0-9a-fA-F]{64}$")


class SuccessionAdmissionPipeline:
    """Evaluates SuccessionProposal artifacts through the S1-S7 gate pipeline.

    Pure and deterministic. Does not mutate state.
    """

    def __init__(
        self,
        sovereign_public_key_active: str,
        prior_sovereign_public_key: Optional[str],
        historical_sovereign_keys: Set[str],
        constitution_frame,  # EffectiveConstitutionFrame or similar
        already_admitted_this_cycle: bool = False,
    ):
        self.sovereign_public_key_active = sovereign_public_key_active
        self.prior_sovereign_public_key = prior_sovereign_public_key
        self.historical_sovereign_keys = historical_sovereign_keys
        self.constitution_frame = constitution_frame
        self.already_admitted_this_cycle = already_admitted_this_cycle

    def evaluate(
        self,
        proposals: List[SuccessionProposal],
    ) -> Tuple[
        Optional[SuccessionAdmissionRecord],
        List[SuccessionRejectionRecord],
        List[SuccessionAdmissionEvent],
    ]:
        """Evaluate succession proposals.

        Returns:
            (admitted_record, rejections, events)
            - At most one proposal admitted per cycle
            - Once one is admitted, remaining are rejected with
              MULTIPLE_SUCCESSIONS_IN_CYCLE
        """
        admitted: Optional[SuccessionAdmissionRecord] = None
        rejections: List[SuccessionRejectionRecord] = []
        events: List[SuccessionAdmissionEvent] = []
        already_admitted = self.already_admitted_this_cycle

        for proposal in proposals:
            result, prop_events = self._evaluate_single(
                proposal, already_admitted
            )
            events.extend(prop_events)

            if result.admitted:
                admitted = result
                already_admitted = True
            else:
                rejections.append(SuccessionRejectionRecord(
                    proposal_id=result.proposal_id,
                    rejection_code=result.rejection_code,
                    failed_gate=result.failed_gate,
                ))

        return admitted, rejections, events

    def _evaluate_single(
        self,
        proposal: SuccessionProposal,
        already_admitted: bool,
    ) -> Tuple[SuccessionAdmissionRecord, List[SuccessionAdmissionEvent]]:
        """Evaluate a single SuccessionProposal through gates S1-S7."""
        events: List[SuccessionAdmissionEvent] = []
        pid = proposal.id

        # --- S1: Completeness ---
        gate = SuccessionGate.S1_COMPLETENESS
        missing = []
        if not proposal.prior_sovereign_public_key:
            missing.append("prior_sovereign_public_key")
        if not proposal.successor_public_key:
            missing.append("successor_public_key")
        if not proposal.authority_citations:
            missing.append("authority_citations")
        if not proposal.justification:
            missing.append("justification")
        if not proposal.signature:
            missing.append("signature")

        # Validate key formats
        if proposal.successor_public_key and not _ED25519_KEY_PATTERN.match(
            proposal.successor_public_key
        ):
            missing.append("successor_public_key (invalid format)")

        if missing:
            events.append(SuccessionAdmissionEvent(
                artifact_id=pid, gate=gate, result="fail",
                reason_code=SuccessionRejectionCode.INVALID_FIELD,
                detail=f"Missing/invalid: {', '.join(missing)}",
            ))
            return self._reject(pid, gate, SuccessionRejectionCode.INVALID_FIELD, events)
        events.append(SuccessionAdmissionEvent(
            artifact_id=pid, gate=gate, result="pass",
        ))

        # --- S2: Authority Citation Snapshot ---
        gate = SuccessionGate.S2_CITATION_SNAPSHOT
        if hasattr(self.constitution_frame, 'resolve_citation'):
            for citation in proposal.authority_citations:
                resolved = self.constitution_frame.resolve_citation(citation)
                if resolved is None:
                    events.append(SuccessionAdmissionEvent(
                        artifact_id=pid, gate=gate, result="fail",
                        reason_code=SuccessionRejectionCode.AUTHORITY_CITATION_INVALID,
                        detail=f"Unresolvable citation: {citation}",
                    ))
                    return self._reject(
                        pid, gate,
                        SuccessionRejectionCode.AUTHORITY_CITATION_INVALID,
                        events,
                    )
        events.append(SuccessionAdmissionEvent(
            artifact_id=pid, gate=gate, result="pass",
        ))

        # --- S3: Signature Verification ---
        gate = SuccessionGate.S3_SIGNATURE
        # Check if signer is the prior sovereign (privilege leak check)
        signer_key = proposal.prior_sovereign_public_key
        if signer_key != self.sovereign_public_key_active:
            if (self.prior_sovereign_public_key and
                    signer_key == self.prior_sovereign_public_key):
                events.append(SuccessionAdmissionEvent(
                    artifact_id=pid, gate=gate, result="fail",
                    reason_code=SuccessionRejectionCode.PRIOR_KEY_PRIVILEGE_LEAK,
                    detail="Prior sovereign key attempted succession post-activation",
                ))
                return self._reject(
                    pid, gate,
                    SuccessionRejectionCode.PRIOR_KEY_PRIVILEGE_LEAK,
                    events,
                )

        valid, error = verify_succession_proposal(
            signer_key,
            proposal.signing_payload(),
            proposal.signature,
        )
        if not valid:
            events.append(SuccessionAdmissionEvent(
                artifact_id=pid, gate=gate, result="fail",
                reason_code=SuccessionRejectionCode.SIGNATURE_INVALID,
                detail=error,
            ))
            return self._reject(
                pid, gate, SuccessionRejectionCode.SIGNATURE_INVALID, events,
            )
        events.append(SuccessionAdmissionEvent(
            artifact_id=pid, gate=gate, result="pass",
        ))

        # --- S4: Sovereign Match ---
        gate = SuccessionGate.S4_SOVEREIGN_MATCH
        if proposal.prior_sovereign_public_key != self.sovereign_public_key_active:
            events.append(SuccessionAdmissionEvent(
                artifact_id=pid, gate=gate, result="fail",
                reason_code=SuccessionRejectionCode.PRIOR_SOVEREIGN_MISMATCH,
                detail=(
                    f"Expected {self.sovereign_public_key_active}, "
                    f"got {proposal.prior_sovereign_public_key}"
                ),
            ))
            return self._reject(
                pid, gate,
                SuccessionRejectionCode.PRIOR_SOVEREIGN_MISMATCH,
                events,
            )
        events.append(SuccessionAdmissionEvent(
            artifact_id=pid, gate=gate, result="pass",
        ))

        # --- S5: Lineage Integrity ---
        gate = SuccessionGate.S5_LINEAGE_INTEGRITY
        successor_key = proposal.successor_public_key

        # Self-succession is always lineage-safe
        if not proposal.is_self_succession():
            # Check cycle: successor_public_key must not be in historical keys
            if successor_key in self.historical_sovereign_keys:
                events.append(SuccessionAdmissionEvent(
                    artifact_id=pid, gate=gate, result="fail",
                    reason_code=SuccessionRejectionCode.IDENTITY_CYCLE,
                    detail=f"Successor key {successor_key} already in lineage history",
                ))
                return self._reject(
                    pid, gate, SuccessionRejectionCode.IDENTITY_CYCLE, events,
                )

            # Check cycle: successor must not equal active key (that's self-succession,
            # already handled above). Check it's not the current active key under
            # a different scenario
            if successor_key == self.sovereign_public_key_active:
                events.append(SuccessionAdmissionEvent(
                    artifact_id=pid, gate=gate, result="fail",
                    reason_code=SuccessionRejectionCode.IDENTITY_CYCLE,
                    detail="Successor equals active sovereign (use self-succession)",
                ))
                return self._reject(
                    pid, gate, SuccessionRejectionCode.IDENTITY_CYCLE, events,
                )

        events.append(SuccessionAdmissionEvent(
            artifact_id=pid, gate=gate, result="pass",
        ))

        # --- S6: Constitutional Compliance ---
        gate = SuccessionGate.S6_CONSTITUTIONAL_COMPLIANCE
        if hasattr(self.constitution_frame, 'is_succession_enabled'):
            if not self.constitution_frame.is_succession_enabled():
                events.append(SuccessionAdmissionEvent(
                    artifact_id=pid, gate=gate, result="fail",
                    reason_code=SuccessionRejectionCode.SUCCESSION_DISABLED,
                ))
                return self._reject(
                    pid, gate,
                    SuccessionRejectionCode.SUCCESSION_DISABLED,
                    events,
                )
        events.append(SuccessionAdmissionEvent(
            artifact_id=pid, gate=gate, result="pass",
        ))

        # --- S7: Per-Cycle Uniqueness ---
        gate = SuccessionGate.S7_PER_CYCLE_UNIQUENESS
        if already_admitted:
            events.append(SuccessionAdmissionEvent(
                artifact_id=pid, gate=gate, result="fail",
                reason_code=SuccessionRejectionCode.MULTIPLE_SUCCESSIONS_IN_CYCLE,
            ))
            return self._reject(
                pid, gate,
                SuccessionRejectionCode.MULTIPLE_SUCCESSIONS_IN_CYCLE,
                events,
            )
        events.append(SuccessionAdmissionEvent(
            artifact_id=pid, gate=gate, result="pass",
        ))

        # --- All gates passed ---
        return SuccessionAdmissionRecord(
            proposal_id=pid,
            admitted=True,
            is_self_succession=proposal.is_self_succession(),
            events=events,
        ), events

    @staticmethod
    def _reject(
        proposal_id: str,
        gate: str,
        code: str,
        events: List[SuccessionAdmissionEvent],
    ) -> Tuple[SuccessionAdmissionRecord, List[SuccessionAdmissionEvent]]:
        return SuccessionAdmissionRecord(
            proposal_id=proposal_id,
            admitted=False,
            failed_gate=gate,
            rejection_code=code,
            events=events,
        ), events
