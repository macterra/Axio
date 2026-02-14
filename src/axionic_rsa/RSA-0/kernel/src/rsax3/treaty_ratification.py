"""
RSA X-3 — Treaty Ratification Pipeline

Deterministic gate pipeline for TreatyRatification evaluation.
Gates:
  R0 — Schema validity (SCHEMA_INVALID)
  R1 — Completeness (INVALID_FIELD)
  R2 — Signature verification under active sovereign (SIGNATURE_INVALID / PRIOR_KEY_PRIVILEGE_LEAK)
  R3 — Treaty exists and is SUSPENDED (TREATY_NOT_SUSPENDED)
  R4 — Density check post-ratification (DENSITY_MARGIN_VIOLATION)

Multiple ratifications per cycle are allowed.
ratify=true  → SUSPENDED → ACTIVE
ratify=false → SUSPENDED → REVOKED

Pure, deterministic, no side effects (caller applies state changes).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from .artifacts_x3 import (
    TreatyRatification,
    RatificationAdmissionRecord,
    RatificationRejectionRecord,
    RatificationRejectionCode,
    RatificationGate,
    RATIFICATION_REQUIRED_FIELDS,
    ActiveTreatySetX3,
    InternalStateX3,
)
from .signature_x3 import verify_active_sovereign_signature
from ..rsax2.artifacts_x2 import (
    TreatyGrant,
    _compute_effective_density,
)


class RatificationAdmissionPipeline:
    """Evaluates TreatyRatification artifacts through R0-R4 gates.

    Pure and deterministic. Does not mutate state directly —
    returns admission/rejection records for caller to apply.
    """

    def __init__(
        self,
        sovereign_public_key_active: str,
        prior_sovereign_public_key: Optional[str],
        active_treaty_set: ActiveTreatySetX3,
        density_upper_bound: float,
        action_permissions: List[Dict[str, Any]],
        action_type_count: int,
        current_cycle: int,
    ):
        self.sovereign_public_key_active = sovereign_public_key_active
        self.prior_sovereign_public_key = prior_sovereign_public_key
        self.active_treaty_set = active_treaty_set
        self.density_upper_bound = density_upper_bound
        self.action_permissions = action_permissions
        self.action_type_count = action_type_count
        self.current_cycle = current_cycle

    def evaluate(
        self,
        ratifications: List[TreatyRatification],
    ) -> Tuple[
        List[RatificationAdmissionRecord],
        List[RatificationRejectionRecord],
    ]:
        """Evaluate ratification artifacts sequentially.

        Returns (admissions, rejections).
        """
        admissions: List[RatificationAdmissionRecord] = []
        rejections: List[RatificationRejectionRecord] = []

        for rat in ratifications:
            result = self._evaluate_single(rat)
            if result.admitted:
                admissions.append(result)
                # Apply effect so subsequent ratifications see updated state
                if rat.ratify:
                    self.active_treaty_set.ratify(rat.treaty_id)
                else:
                    self.active_treaty_set.reject_ratification(rat.treaty_id)
            else:
                rejections.append(RatificationRejectionRecord(
                    ratification_id=result.ratification_id,
                    treaty_id=result.treaty_id,
                    rejection_code=result.rejection_code,
                    failed_gate=result.failed_gate,
                ))

        return admissions, rejections

    def _evaluate_single(
        self,
        ratification: TreatyRatification,
    ) -> RatificationAdmissionRecord:
        """Evaluate a single TreatyRatification through R0-R4 gates."""
        rid = ratification.id
        tid = ratification.treaty_id
        events: List[Dict[str, Any]] = []

        # --- R0: Schema validity ---
        gate = RatificationGate.R0_SCHEMA
        # Basic type checks
        if not isinstance(ratification.treaty_id, str):
            events.append({"gate": gate, "result": "fail",
                          "code": RatificationRejectionCode.SCHEMA_INVALID})
            return self._reject(rid, tid, ratification.ratify, gate,
                              RatificationRejectionCode.SCHEMA_INVALID, events)
        if not isinstance(ratification.ratify, bool):
            events.append({"gate": gate, "result": "fail",
                          "code": RatificationRejectionCode.SCHEMA_INVALID})
            return self._reject(rid, tid, ratification.ratify, gate,
                              RatificationRejectionCode.SCHEMA_INVALID, events)
        events.append({"gate": gate, "result": "pass"})

        # --- R1: Completeness ---
        gate = RatificationGate.R1_COMPLETENESS
        if not ratification.treaty_id:
            events.append({"gate": gate, "result": "fail",
                          "code": RatificationRejectionCode.INVALID_FIELD})
            return self._reject(rid, tid, ratification.ratify, gate,
                              RatificationRejectionCode.INVALID_FIELD, events)
        if not ratification.signature:
            events.append({"gate": gate, "result": "fail",
                          "code": RatificationRejectionCode.INVALID_FIELD})
            return self._reject(rid, tid, ratification.ratify, gate,
                              RatificationRejectionCode.INVALID_FIELD, events)
        events.append({"gate": gate, "result": "pass"})

        # --- R2: Signature verification under active sovereign ---
        gate = RatificationGate.R2_SIGNATURE
        valid, error, code = verify_active_sovereign_signature(
            payload_dict=ratification.signing_payload(),
            signature_hex=ratification.signature,
            signer_identifier=self.sovereign_public_key_active,
            active_sovereign_key=self.sovereign_public_key_active,
            prior_sovereign_key=self.prior_sovereign_public_key,
        )
        if not valid:
            reject_code = (
                RatificationRejectionCode.PRIOR_KEY_PRIVILEGE_LEAK
                if code == "PRIOR_KEY_PRIVILEGE_LEAK"
                else RatificationRejectionCode.SIGNATURE_INVALID
            )
            events.append({"gate": gate, "result": "fail", "code": reject_code})
            return self._reject(rid, tid, ratification.ratify, gate,
                              reject_code, events)
        events.append({"gate": gate, "result": "pass"})

        # --- R3: Treaty exists and is SUSPENDED ---
        gate = RatificationGate.R3_TREATY_SUSPENDED
        grant = self.active_treaty_set.find_grant(tid)
        if grant is None:
            events.append({"gate": gate, "result": "fail",
                          "code": RatificationRejectionCode.TREATY_NOT_SUSPENDED,
                          "detail": "Treaty not found"})
            return self._reject(rid, tid, ratification.ratify, gate,
                              RatificationRejectionCode.TREATY_NOT_SUSPENDED, events)
        if tid not in self.active_treaty_set.suspended_grant_ids:
            events.append({"gate": gate, "result": "fail",
                          "code": RatificationRejectionCode.TREATY_NOT_SUSPENDED,
                          "detail": "Treaty is not SUSPENDED"})
            return self._reject(rid, tid, ratification.ratify, gate,
                              RatificationRejectionCode.TREATY_NOT_SUSPENDED, events)
        events.append({"gate": gate, "result": "pass"})

        # --- R4: Density check (only for ratify=true) ---
        gate = RatificationGate.R4_DENSITY
        if ratification.ratify:
            # Simulate what density would be if this grant is restored
            active_after = self.active_treaty_set.active_grants(self.current_cycle)
            # Add the grant being ratified
            simulated_active = active_after + [grant]
            d = _compute_effective_density(
                self.action_permissions,
                simulated_active,
                self.action_type_count,
            )
            if d >= self.density_upper_bound or d == 1.0:
                events.append({"gate": gate, "result": "fail",
                              "code": RatificationRejectionCode.DENSITY_MARGIN_VIOLATION,
                              "density": d})
                return self._reject(rid, tid, ratification.ratify, gate,
                                  RatificationRejectionCode.DENSITY_MARGIN_VIOLATION,
                                  events)
        events.append({"gate": gate, "result": "pass"})

        # --- All gates passed ---
        return RatificationAdmissionRecord(
            ratification_id=rid,
            treaty_id=tid,
            ratify=ratification.ratify,
            admitted=True,
            events=events,
        )

    @staticmethod
    def _reject(
        rid: str,
        tid: str,
        ratify: bool,
        gate: str,
        code: str,
        events: List[Dict[str, Any]],
    ) -> RatificationAdmissionRecord:
        return RatificationAdmissionRecord(
            ratification_id=rid,
            treaty_id=tid,
            ratify=ratify,
            admitted=False,
            events=events,
            failed_gate=gate,
            rejection_code=code,
        )
