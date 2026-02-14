"""
X-3 Profiling Generators

Precomputes full N-cycle plans for each X-3 session family.
All randomness is seeded. Plans include succession proposals,
treaty ratifications, grants, revocations, and delegated actions.

Key difference from X-2D: generators also produce succession proposals
at scheduled rotation cycles, and treaty ratification artifacts
at (rotation_cycle + ratification_delay).
"""

from __future__ import annotations

import copy
import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from kernel.src.artifacts import canonical_json_bytes
from kernel.src.rsax2.artifacts_x2 import (
    TreatyGrant,
    TreatyRevocation,
)
from kernel.src.rsax2.policy_core_x2 import DelegatedActionRequest
from kernel.src.rsax2.signature import (
    generate_keypair,
    sign_action_request,
)
from kernel.src.rsax3.artifacts_x3 import (
    SuccessionProposal,
    TreatyRatification,
)
from kernel.src.rsax3.signature_x3 import (
    derive_genesis_keypair,
    precompute_keypairs,
    sign_succession_proposal,
    sign_treaty_ratification,
)
from kernel.src.rsax3.constitution_x3 import EffectiveConstitutionFrame

from .schemas_x3 import X3SessionStart, SessionFamilyX3


# ---------------------------------------------------------------------------
# Genesis Seed (reproducible)
# ---------------------------------------------------------------------------

X3_GENESIS_SEED = b"rsa-x3-profiling-genesis-seed-v0.1"


# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

@dataclass
class X3Identity:
    """Delegate identity for treaty testing."""
    identifier: str
    private_key: Any  # Ed25519PrivateKey


def generate_identity_pool(seed: int, count: int) -> List[X3Identity]:
    """Generate a deterministic pool of delegate identities."""
    rng = random.Random(seed)
    identities: List[X3Identity] = []
    for i in range(count):
        # Derive deterministic key material from seed
        key_seed = rng.randbytes(32)
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        priv = Ed25519PrivateKey.from_private_bytes(key_seed)
        pub_hex = priv.public_key().public_bytes_raw().hex()
        gid = f"ed25519:{pub_hex}"
        identities.append(X3Identity(identifier=gid, private_key=priv))
    return identities


# ---------------------------------------------------------------------------
# Cycle Plan
# ---------------------------------------------------------------------------

@dataclass
class X3CyclePlan:
    """Precomputed plan for a single cycle."""
    cycle_index: int
    timestamp: str
    grants: List[TreatyGrant] = field(default_factory=list)
    revocations: List[TreatyRevocation] = field(default_factory=list)
    delegated_requests: List[DelegatedActionRequest] = field(default_factory=list)
    succession_proposals: List[SuccessionProposal] = field(default_factory=list)
    ratifications: List[TreatyRatification] = field(default_factory=list)
    # Boundary fault injection (for X3-INVALID_BOUNDARY)
    boundary_fault: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Base Generator
# ---------------------------------------------------------------------------

class X3Generator:
    """Base class for X-3 plan generators."""

    def __init__(
        self,
        session: X3SessionStart,
        constitution_frame: EffectiveConstitutionFrame,
        base_timestamp: str = "2026-02-14T00:00:00Z",
    ):
        self.session = session
        self.constitution = constitution_frame
        self.N = session.session_length_cycles
        self.base_timestamp = base_timestamp

        # Seeded RNGs
        self.treaty_rng = random.Random(session.seeds["treaty_stream"])
        self.action_rng = random.Random(session.seeds["action_stream"])
        self.succession_rng = random.Random(session.seeds["succession_stream"])

        # Delegate identity pool
        self.identities = generate_identity_pool(
            session.seeds["treaty_stream"], session.grantee_count,
        )

        # Sovereign keypairs: precompute all rotations
        max_rotations = len(session.rotation_schedule) + 1
        self.sovereign_keypairs = precompute_keypairs(
            X3_GENESIS_SEED, max_rotations,
        )

        # Constitutional parameters
        self._grant_citations = [
            constitution_frame.make_citation("CL-DELEGATION-PROTOCOL"),
        ]
        self._revocation_citations = [
            constitution_frame.make_citation("CL-DELEGATION-PROTOCOL"),
        ]

        # Precompute compatible action groups
        self._action_groups = self._compute_action_groups()

        # Build rotation index map: cycle → rotation_index
        self._rotation_map: Dict[int, int] = {}
        for i, entry in enumerate(session.rotation_schedule):
            self._rotation_map[entry["cycle"]] = i + 1  # 1-indexed successor

    def _compute_action_groups(self) -> List[Tuple[List[str], List[str]]]:
        """Compute (actions, valid_scope_types) groups from constitution."""
        try:
            action_types = self.constitution.get_action_types()
            groups = []
            for at in action_types:
                valid_st = self.constitution.get_valid_scope_types(at)
                if valid_st:
                    groups.append(([at], valid_st))
            return groups if groups else [
                (["Notify"], ["SYSTEM"]),
            ]
        except Exception:
            return [(["Notify"], ["SYSTEM"])]

    def _pick_action_group(
        self, rng: random.Random, max_actions: int = 3,
    ) -> Tuple[List[str], List[str]]:
        """Pick a random action group."""
        candidates = [g for g in self._action_groups if len(g[0]) <= max_actions]
        if not candidates:
            candidates = self._action_groups[:1]
        return rng.choice(candidates)

    def _make_timestamp(self, cycle: int) -> str:
        base = datetime.fromisoformat(self.base_timestamp.replace("Z", "+00:00"))
        return (base + timedelta(seconds=cycle)).isoformat().replace("+00:00", "Z")

    def _make_grant(
        self,
        grantee: X3Identity,
        actions: List[str],
        scope_constraints: Dict[str, List[str]],
        duration: int,
        cycle: int,
    ) -> TreatyGrant:
        return TreatyGrant(
            grantor_authority_id="AUTH_DELEGATION",
            grantee_identifier=grantee.identifier,
            granted_actions=actions,
            scope_constraints=scope_constraints,
            duration_cycles=duration,
            revocable=True,
            authority_citations=list(self._grant_citations),
            justification=f"X-3 generated grant for cycle {cycle}",
            created_at=self._make_timestamp(cycle),
            grant_cycle=cycle,
        )

    def _make_revocation(
        self, grant: TreatyGrant, cycle: int,
    ) -> TreatyRevocation:
        return TreatyRevocation(
            grant_id=grant.id,
            authority_citations=list(self._revocation_citations),
            justification=f"X-3 generated revocation for cycle {cycle}",
            created_at=self._make_timestamp(cycle),
        )

    def _make_succession_proposal(
        self, cycle: int, successor_index: int, invalid: str = "",
    ) -> SuccessionProposal:
        """Create a SuccessionProposal signed by the active sovereign.

        Args:
            cycle: The cycle to create the proposal for
            successor_index: Index into sovereign_keypairs for successor
            invalid: If non-empty, inject a specific fault type
        """
        # Determine who's active at this cycle
        active_index = self._active_sovereign_index_at(cycle)
        prior_priv, prior_gid = self.sovereign_keypairs[active_index]
        _, succ_gid = self.sovereign_keypairs[successor_index]

        oh = self.constitution.overlay_hash
        citations = [f"overlay:{oh}#CL-SUCCESSION-ENABLED"]

        proposal = SuccessionProposal(
            prior_sovereign_public_key=prior_gid,
            successor_public_key=succ_gid,
            authority_citations=citations,
            justification=f"Rotation at cycle {cycle}",
            signature="",  # Will be signed below
        )

        # Sign with prior key
        sig = sign_succession_proposal(prior_priv, proposal.to_dict_full())

        if invalid == "bad_signature":
            sig = "deadbeef" * 16
        elif invalid == "wrong_signer":
            # Sign with successor key instead — will fail S3/S4
            sig = sign_succession_proposal(
                self.sovereign_keypairs[successor_index][0],
                proposal.to_dict_full(),
            )

        proposal.signature = sig
        return proposal

    def _make_treaty_ratification(
        self, treaty_id: str, ratify: bool, cycle: int,
    ) -> TreatyRatification:
        """Create a TreatyRatification signed by the active sovereign."""
        active_index = self._active_sovereign_index_at(cycle)
        active_priv, active_gid = self.sovereign_keypairs[active_index]

        oh = self.constitution.overlay_hash
        citations = [f"overlay:{oh}#CL-TREATY-RATIFICATION-REQUIRED"]

        rat = TreatyRatification(
            treaty_id=treaty_id,
            ratify=ratify,
            authority_citations=citations,
            justification=f"Ratification at cycle {cycle}",
            author=active_gid,
            created_at=self._make_timestamp(cycle),
            signature="",
        )

        sig = sign_treaty_ratification(active_priv, rat.to_dict_full())
        rat.signature = sig
        return rat

    def _active_sovereign_index_at(self, cycle: int) -> int:
        """Determine which sovereign keypair is active at given cycle.

        Activation occurs at cycle boundary (start of cycle after rotation).
        A rotation scheduled at cycle R means successor is active from cycle R+1.
        """
        active_index = 0
        for entry in sorted(self.session.rotation_schedule, key=lambda e: e["cycle"]):
            rot_cycle = entry["cycle"]
            # Successor becomes active at cycle rot_cycle + 1
            if cycle > rot_cycle:
                active_index = entry.get("successor_index", active_index + 1)
            else:
                break
        return active_index

    def _build_scope_constraints(
        self, valid_scope_types: List[str], rng: random.Random,
    ) -> Dict[str, List[str]]:
        """Build scope constraints from constitutional zones."""
        scope: Dict[str, List[str]] = {}
        for st in valid_scope_types:
            try:
                zones = self.constitution.get_permitted_zones("Notify", st)
            except Exception:
                zones = []
            if not zones:
                try:
                    zones = list(self.constitution.get_all_zone_labels())
                except Exception:
                    zones = ["ARTIFACTS_READ"]
            if zones:
                scope[st] = [rng.choice(zones)]
        return scope or {"FILE_PATH": ["ARTIFACTS_READ"]}

    def _make_delegated_request(
        self,
        grantee: X3Identity,
        action_type: str,
        scope_type: str,
        scope_zone: str,
        grant: TreatyGrant,
        cycle: int,
    ) -> DelegatedActionRequest:
        """Create a signed delegated action request."""
        dar_fields: Dict[str, Any] = {}
        if action_type == "Notify":
            dar_fields = {"message": f"x3-cycle-{cycle}"}
        elif action_type == "ReadLocal":
            dar_fields = {"path": f"/x3/{scope_zone}"}
        elif action_type == "WriteLocal":
            dar_fields = {"path": f"/x3/{scope_zone}", "content": f"cycle-{cycle}"}

        dar_dict = {
            "type": "ActionRequest",
            "action_type": action_type,
            "fields": dar_fields,
            "grantee_identifier": grantee.identifier,
            "authority_citations": sorted([f"treaty:{grant.id}"]),
            "scope_type": scope_type,
            "scope_zone": scope_zone,
            "created_at": self._make_timestamp(cycle),
        }

        dar_id = hashlib.sha256(
            f"{grantee.identifier}-{action_type}-{cycle}".encode()
        ).hexdigest()
        dar_dict["id"] = dar_id

        sig = sign_action_request(grantee.private_key, dar_dict)

        return DelegatedActionRequest(
            action_type=action_type,
            fields=dar_fields,
            grantee_identifier=grantee.identifier,
            authority_citations=dar_dict["authority_citations"],
            signature=sig,
            scope_type=scope_type,
            scope_zone=scope_zone,
            created_at=self._make_timestamp(cycle),
            id=dar_id,
        )

    def generate_plan(self) -> List[X3CyclePlan]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# X3-BASE Generator
# ---------------------------------------------------------------------------

class X3BaseGenerator(X3Generator):
    """Baseline: 50 cycles, 1 rotation at cycle 25, 1-cycle ratification."""

    def generate_plan(self) -> List[X3CyclePlan]:
        plans: List[X3CyclePlan] = []
        active_grants: List[TreatyGrant] = []
        rotation_cycle = self.session.rotation_schedule[0]["cycle"]
        succ_idx = self.session.rotation_schedule[0].get("successor_index", 1)
        rat_delay = self.session.ratification_delay_cycles

        for cycle in range(self.N):
            plan = X3CyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            # Succession proposal at rotation_cycle
            if cycle == rotation_cycle:
                plan.succession_proposals.append(
                    self._make_succession_proposal(cycle, succ_idx)
                )

            # Grants: add a few in early cycles
            if cycle < min(self.session.grantee_count, 3):
                identity = self.identities[cycle]
                actions, valid_st = self._pick_action_group(self.treaty_rng, 1)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng)
                grant = self._make_grant(identity, actions, scope, 40, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)

            # Ratify suspended treaties after rotation + delay
            if cycle == rotation_cycle + rat_delay + 1 and active_grants:
                for g in active_grants:
                    plan.ratifications.append(
                        self._make_treaty_ratification(g.id, True, cycle)
                    )

            # Delegated request if grants exist and not suspended
            if active_grants and self.action_rng.random() < self.session.delegated_requests_per_cycle_fraction:
                g = self.action_rng.choice(active_grants)
                identity = next(
                    (i for i in self.identities if i.identifier == g.grantee_identifier),
                    None,
                )
                if identity and g.granted_actions:
                    action = g.granted_actions[0]
                    st = list(g.scope_constraints.keys())[0] if g.scope_constraints else ""
                    sz = g.scope_constraints[st][0] if st and g.scope_constraints.get(st) else ""
                    plan.delegated_requests.append(
                        self._make_delegated_request(identity, action, st, sz, g, cycle)
                    )

            plans.append(plan)
        return plans


# ---------------------------------------------------------------------------
# X3-NEAR_BOUND Generator
# ---------------------------------------------------------------------------

class X3NearBoundGenerator(X3Generator):
    """Near density bound: 60 cycles, 1 rotation at cycle 30, NEAR_BOUND."""

    def generate_plan(self) -> List[X3CyclePlan]:
        plans: List[X3CyclePlan] = []
        active_grants: List[TreatyGrant] = []
        rotation_cycle = self.session.rotation_schedule[0]["cycle"]
        succ_idx = self.session.rotation_schedule[0].get("successor_index", 1)
        rat_delay = self.session.ratification_delay_cycles
        grant_counter = 0

        for cycle in range(self.N):
            plan = X3CyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            if cycle == rotation_cycle:
                plan.succession_proposals.append(
                    self._make_succession_proposal(cycle, succ_idx)
                )

            # Aggressive grants to push density near bound
            if self.treaty_rng.random() < 0.7 and grant_counter < len(self.identities) * 3:
                idx = grant_counter % len(self.identities)
                identity = self.identities[idx]
                actions, valid_st = self._pick_action_group(self.treaty_rng, 2)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng)
                dur = self.treaty_rng.randint(10, 30)
                grant = self._make_grant(identity, actions, scope, dur, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)
                grant_counter += 1

            # Ratify after rotation + delay
            if cycle == rotation_cycle + rat_delay + 1 and active_grants:
                for g in active_grants:
                    plan.ratifications.append(
                        self._make_treaty_ratification(g.id, True, cycle)
                    )

            # Delegated requests
            if active_grants and self.action_rng.random() < self.session.delegated_requests_per_cycle_fraction:
                g = self.action_rng.choice(active_grants)
                identity = next(
                    (i for i in self.identities if i.identifier == g.grantee_identifier),
                    None,
                )
                if identity and g.granted_actions:
                    action = g.granted_actions[0]
                    st = list(g.scope_constraints.keys())[0] if g.scope_constraints else ""
                    sz = g.scope_constraints[st][0] if st and g.scope_constraints.get(st) else ""
                    plan.delegated_requests.append(
                        self._make_delegated_request(identity, action, st, sz, g, cycle)
                    )

            plans.append(plan)
        return plans


# ---------------------------------------------------------------------------
# X3-CHURN Generator
# ---------------------------------------------------------------------------

class X3ChurnGenerator(X3Generator):
    """High churn: 80 cycles, 1 rotation at cycle 40, 2-cycle rat delay."""

    def generate_plan(self) -> List[X3CyclePlan]:
        plans: List[X3CyclePlan] = []
        active_grants: List[TreatyGrant] = []
        rotation_cycle = self.session.rotation_schedule[0]["cycle"]
        succ_idx = self.session.rotation_schedule[0].get("successor_index", 1)
        rat_delay = self.session.ratification_delay_cycles
        grant_counter = 0

        for cycle in range(self.N):
            plan = X3CyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            if cycle == rotation_cycle:
                plan.succession_proposals.append(
                    self._make_succession_proposal(cycle, succ_idx)
                )

            # High-frequency grants
            if self.treaty_rng.random() < 0.6:
                idx = grant_counter % len(self.identities)
                identity = self.identities[idx]
                actions, valid_st = self._pick_action_group(self.treaty_rng, 2)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng)
                dur = self.treaty_rng.randint(3, 15)
                grant = self._make_grant(identity, actions, scope, dur, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)
                grant_counter += 1

            # Frequent revocations
            if active_grants and self.treaty_rng.random() < 0.3:
                victim = self.treaty_rng.choice(active_grants)
                plan.revocations.append(self._make_revocation(victim, cycle))
                active_grants = [g for g in active_grants if g.id != victim.id]

            # Ratify after rotation + delay
            if cycle == rotation_cycle + rat_delay + 1 and active_grants:
                for g in active_grants:
                    plan.ratifications.append(
                        self._make_treaty_ratification(g.id, True, cycle)
                    )

            # Delegated requests
            if active_grants and self.action_rng.random() < self.session.delegated_requests_per_cycle_fraction:
                g = self.action_rng.choice(active_grants)
                identity = next(
                    (i for i in self.identities if i.identifier == g.grantee_identifier),
                    None,
                )
                if identity and g.granted_actions:
                    action = g.granted_actions[0]
                    st = list(g.scope_constraints.keys())[0] if g.scope_constraints else ""
                    sz = g.scope_constraints[st][0] if st and g.scope_constraints.get(st) else ""
                    plan.delegated_requests.append(
                        self._make_delegated_request(identity, action, st, sz, g, cycle)
                    )

            plans.append(plan)
        return plans


# ---------------------------------------------------------------------------
# X3-RAT_DELAY Generator
# ---------------------------------------------------------------------------

class X3RatDelayGenerator(X3Generator):
    """Extended ratification delay: 60 cycles, 1 rotation at cycle 20, 5+ delay."""

    def generate_plan(self) -> List[X3CyclePlan]:
        plans: List[X3CyclePlan] = []
        active_grants: List[TreatyGrant] = []
        rotation_cycle = self.session.rotation_schedule[0]["cycle"]
        succ_idx = self.session.rotation_schedule[0].get("successor_index", 1)
        rat_delay = self.session.ratification_delay_cycles

        for cycle in range(self.N):
            plan = X3CyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            if cycle == rotation_cycle:
                plan.succession_proposals.append(
                    self._make_succession_proposal(cycle, succ_idx)
                )

            # Grants in early cycles
            if cycle < min(self.session.grantee_count, 3):
                identity = self.identities[cycle]
                actions, valid_st = self._pick_action_group(self.treaty_rng, 1)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng)
                grant = self._make_grant(identity, actions, scope, 50, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)

            # Ratify after extended delay
            if cycle == rotation_cycle + rat_delay + 1 and active_grants:
                for g in active_grants:
                    plan.ratifications.append(
                        self._make_treaty_ratification(g.id, True, cycle)
                    )

            # Delegated requests
            if active_grants and self.action_rng.random() < self.session.delegated_requests_per_cycle_fraction:
                g = self.action_rng.choice(active_grants)
                identity = next(
                    (i for i in self.identities if i.identifier == g.grantee_identifier),
                    None,
                )
                if identity and g.granted_actions:
                    action = g.granted_actions[0]
                    st = list(g.scope_constraints.keys())[0] if g.scope_constraints else ""
                    sz = g.scope_constraints[st][0] if st and g.scope_constraints.get(st) else ""
                    plan.delegated_requests.append(
                        self._make_delegated_request(identity, action, st, sz, g, cycle)
                    )

            plans.append(plan)
        return plans


# ---------------------------------------------------------------------------
# X3-MULTI_ROT Generator
# ---------------------------------------------------------------------------

class X3MultiRotGenerator(X3Generator):
    """Multiple rotations: 80 cycles, 3 rotations at 20/40/60."""

    def generate_plan(self) -> List[X3CyclePlan]:
        plans: List[X3CyclePlan] = []
        active_grants: List[TreatyGrant] = []
        rat_delay = self.session.ratification_delay_cycles

        # Build set of rotation cycles
        rot_cycles = {
            e["cycle"]: e.get("successor_index", i + 1)
            for i, e in enumerate(self.session.rotation_schedule)
        }
        # Build ratification cycles
        rat_cycles = {rc + rat_delay + 1 for rc in rot_cycles}

        for cycle in range(self.N):
            plan = X3CyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            # Succession at rotation cycles
            if cycle in rot_cycles:
                plan.succession_proposals.append(
                    self._make_succession_proposal(cycle, rot_cycles[cycle])
                )

            # Moderate grants
            if cycle < 5:
                idx = cycle % len(self.identities)
                identity = self.identities[idx]
                actions, valid_st = self._pick_action_group(self.treaty_rng, 1)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng)
                grant = self._make_grant(identity, actions, scope, 70, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)

            # Ratify at each ratification cycle
            if cycle in rat_cycles and active_grants:
                for g in active_grants:
                    plan.ratifications.append(
                        self._make_treaty_ratification(g.id, True, cycle)
                    )

            # Delegated requests
            if active_grants and self.action_rng.random() < self.session.delegated_requests_per_cycle_fraction:
                g = self.action_rng.choice(active_grants)
                identity = next(
                    (i for i in self.identities if i.identifier == g.grantee_identifier),
                    None,
                )
                if identity and g.granted_actions:
                    action = g.granted_actions[0]
                    st = list(g.scope_constraints.keys())[0] if g.scope_constraints else ""
                    sz = g.scope_constraints[st][0] if st and g.scope_constraints.get(st) else ""
                    plan.delegated_requests.append(
                        self._make_delegated_request(identity, action, st, sz, g, cycle)
                    )

            plans.append(plan)
        return plans


# ---------------------------------------------------------------------------
# X3-INVALID_SIG Generator
# ---------------------------------------------------------------------------

class X3InvalidSigGenerator(X3Generator):
    """1 valid rotation + 1 invalid-signature rotation (different cycle)."""

    def generate_plan(self) -> List[X3CyclePlan]:
        plans: List[X3CyclePlan] = []
        active_grants: List[TreatyGrant] = []
        # Valid rotation from schedule[0]; invalid rotation 2 cycles earlier
        # (or from schedule[1] if provided)
        valid_rot = self.session.rotation_schedule[0]
        if len(self.session.rotation_schedule) > 1:
            invalid_rot = self.session.rotation_schedule[1]
        else:
            invalid_cycle = max(1, valid_rot["cycle"] - 2)
            invalid_rot = {"cycle": invalid_cycle, "successor_index": 2}
        rat_delay = self.session.ratification_delay_cycles

        for cycle in range(self.N):
            plan = X3CyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            # Valid succession
            if cycle == valid_rot["cycle"]:
                plan.succession_proposals.append(
                    self._make_succession_proposal(
                        cycle, valid_rot.get("successor_index", 1),
                    )
                )

            # Invalid succession (bad signature) on different cycle
            if cycle == invalid_rot["cycle"]:
                plan.succession_proposals.append(
                    self._make_succession_proposal(
                        cycle,
                        invalid_rot.get("successor_index", 2),
                        invalid="bad_signature",
                    )
                )

            # Grants
            if cycle < 2:
                identity = self.identities[cycle]
                actions, valid_st = self._pick_action_group(self.treaty_rng, 1)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng)
                grant = self._make_grant(identity, actions, scope, 40, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)

            # Ratify after valid rotation
            if cycle == valid_rot["cycle"] + rat_delay + 1 and active_grants:
                for g in active_grants:
                    plan.ratifications.append(
                        self._make_treaty_ratification(g.id, True, cycle)
                    )

            plans.append(plan)
        return plans


# ---------------------------------------------------------------------------
# X3-DUP_CYCLE Generator
# ---------------------------------------------------------------------------

class X3DupCycleGenerator(X3Generator):
    """1 valid rotation + 1 duplicate same-cycle second candidate."""

    def generate_plan(self) -> List[X3CyclePlan]:
        plans: List[X3CyclePlan] = []
        active_grants: List[TreatyGrant] = []
        # Valid rotation from schedule[0]; dup is same cycle with different successor
        valid_rot = self.session.rotation_schedule[0]
        if len(self.session.rotation_schedule) > 1:
            dup_rot = self.session.rotation_schedule[1]
        else:
            dup_rot = {"cycle": valid_rot["cycle"], "successor_index": 2}
        rat_delay = self.session.ratification_delay_cycles

        for cycle in range(self.N):
            plan = X3CyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            # Both on same cycle
            if cycle == valid_rot["cycle"]:
                # First: valid
                plan.succession_proposals.append(
                    self._make_succession_proposal(
                        cycle, valid_rot.get("successor_index", 1),
                    )
                )
                # Second: duplicate (valid sig, but same-cycle second → rejected)
                plan.succession_proposals.append(
                    self._make_succession_proposal(
                        cycle, dup_rot.get("successor_index", 2),
                    )
                )

            # Grants
            if cycle < 2:
                identity = self.identities[cycle]
                actions, valid_st = self._pick_action_group(self.treaty_rng, 1)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng)
                grant = self._make_grant(identity, actions, scope, 40, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)

            # Ratify after rotation
            if cycle == valid_rot["cycle"] + rat_delay + 1 and active_grants:
                for g in active_grants:
                    plan.ratifications.append(
                        self._make_treaty_ratification(g.id, True, cycle)
                    )

            plans.append(plan)
        return plans


# ---------------------------------------------------------------------------
# X3-INVALID_BOUNDARY Generator
# ---------------------------------------------------------------------------

class X3InvalidBoundaryGenerator(X3Generator):
    """Boundary fault injection. Generates a clean plan with
    rotation at cycle 20; faults are injected at runner level,
    not in the plan."""

    def generate_plan(self) -> List[X3CyclePlan]:
        plans: List[X3CyclePlan] = []
        active_grants: List[TreatyGrant] = []
        rotation_cycle = self.session.rotation_schedule[0]["cycle"]
        succ_idx = self.session.rotation_schedule[0].get("successor_index", 1)

        for cycle in range(self.N):
            plan = X3CyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            if cycle == rotation_cycle:
                plan.succession_proposals.append(
                    self._make_succession_proposal(cycle, succ_idx)
                )

            # A few grants for suspension testing
            if cycle < 2:
                identity = self.identities[cycle % len(self.identities)]
                actions, valid_st = self._pick_action_group(self.treaty_rng, 1)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng)
                grant = self._make_grant(identity, actions, scope, 40, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)

            # Tag cycles with boundary faults from session config
            for fault in self.session.invalid_boundary_faults:
                if fault.get("cycle") == cycle:
                    plan.boundary_fault = fault

            plans.append(plan)
        return plans


# ---------------------------------------------------------------------------
# Generator Factory
# ---------------------------------------------------------------------------

GENERATORS = {
    SessionFamilyX3.X3_BASE.value: X3BaseGenerator,
    SessionFamilyX3.X3_NEAR_BOUND.value: X3NearBoundGenerator,
    SessionFamilyX3.X3_CHURN.value: X3ChurnGenerator,
    SessionFamilyX3.X3_RAT_DELAY.value: X3RatDelayGenerator,
    SessionFamilyX3.X3_MULTI_ROT.value: X3MultiRotGenerator,
    SessionFamilyX3.X3_INVALID_SIG.value: X3InvalidSigGenerator,
    SessionFamilyX3.X3_DUP_CYCLE.value: X3DupCycleGenerator,
    SessionFamilyX3.X3_INVALID_BOUNDARY.value: X3InvalidBoundaryGenerator,
}


def create_generator(
    session: X3SessionStart,
    constitution_frame: EffectiveConstitutionFrame,
    base_timestamp: str = "2026-02-14T00:00:00Z",
) -> X3Generator:
    """Factory for X-3 session family generators."""
    cls = GENERATORS.get(session.session_family)
    if cls is None:
        raise ValueError(f"Unknown X-3 family: {session.session_family}")
    return cls(session, constitution_frame, base_timestamp)
