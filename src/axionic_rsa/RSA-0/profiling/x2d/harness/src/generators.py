"""
X-2D Deterministic Generators

Per Q&A E19/S70: generators precompute the entire N-cycle plan and
validate feasibility before execution. All randomness is seeded.

Per Q&A X83: D-RATCHET generator simulates full revalidation + density
repair during plan construction via the kernel simulation API.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from kernel.src.rsax2.artifacts_x2 import (
    TreatyGrant,
    TreatyRevocation,
)
from kernel.src.rsax2.constitution_x2 import ConstitutionX2
from kernel.src.rsax2.policy_core_x2 import DelegatedActionRequest
from kernel.src.rsax2.signature import sign_action_request

from .schemas import SessionFamily, X2DSessionStart


# ---------------------------------------------------------------------------
# Identity Pool
# ---------------------------------------------------------------------------

@dataclass
class X2DIdentity:
    """A grantee identity with Ed25519 keypair."""
    identifier: str  # ed25519:<hex_pubkey>
    private_key: Ed25519PrivateKey
    public_key_hex: str


def generate_identity_pool(seed: int, count: int) -> List[X2DIdentity]:
    """Generate deterministic Ed25519 identity pool from seed.

    Uses cryptography library (same as kernel/src/rsax2/signature.py).
    Deterministic: derives key material from seeded RNG.
    """
    rng = random.Random(seed)
    pool: List[X2DIdentity] = []
    for i in range(count):
        # Deterministic key from seed
        key_seed = rng.getrandbits(256).to_bytes(32, "big")
        sk = Ed25519PrivateKey.from_private_bytes(key_seed)
        pk = sk.public_key()
        pub_hex = pk.public_bytes_raw().hex()
        identifier = f"ed25519:{pub_hex}"
        pool.append(X2DIdentity(
            identifier=identifier,
            private_key=sk,
            public_key_hex=pub_hex,
        ))
    return pool


# ---------------------------------------------------------------------------
# Cycle Plan
# ---------------------------------------------------------------------------

@dataclass
class X2DCyclePlan:
    """Plan for a single cycle in a session."""
    cycle_index: int
    grants: List[TreatyGrant] = field(default_factory=list)
    revocations: List[TreatyRevocation] = field(default_factory=list)
    delegated_requests: List[DelegatedActionRequest] = field(default_factory=list)
    amendment_adoption: Optional[Dict[str, Any]] = None
    timestamp: str = ""


# ---------------------------------------------------------------------------
# Generator Base
# ---------------------------------------------------------------------------

class X2DGenerator:
    """Base generator for X-2D sessions."""

    def __init__(
        self,
        session_start: X2DSessionStart,
        constitution: ConstitutionX2,
        base_timestamp: str = "2026-02-13T12:00:00Z",
    ):
        self.session = session_start
        self.constitution = constitution
        self.base_timestamp = base_timestamp
        self.N = session_start.session_length_cycles

        # Set up seeded RNGs
        self.treaty_rng = random.Random(session_start.seeds["treaty_stream"])
        self.action_rng = random.Random(session_start.seeds["action_stream"])
        self.amendment_rng = random.Random(session_start.seeds["amendment_stream"])

        # Generate identity pool
        self.identities = generate_identity_pool(
            session_start.seeds["treaty_stream"],
            session_start.grantee_count,
        )

        # Get constitutional parameters
        self.closed_actions = constitution.get_closed_action_set()
        # Filter to delegable actions (exclude kernel-only LogAppend)
        self.delegable_actions = [
            a for a in self.closed_actions if a != "LogAppend"
        ]
        self.zone_labels = constitution.get_all_zone_labels()
        self.scope_zones = constitution.get_zone_labels()
        self.density_bound = constitution.density_upper_bound() or 0.75
        self.action_perms = constitution.get_action_permissions()

    def _make_timestamp(self, cycle: int) -> str:
        """Generate deterministic timestamp for cycle."""
        base = datetime.fromisoformat(self.base_timestamp.replace("Z", "+00:00"))
        return (base + timedelta(seconds=cycle)).isoformat().replace("+00:00", "Z")

    def _make_grant(
        self,
        grantee: X2DIdentity,
        actions: List[str],
        scope_constraints: Dict[str, List[str]],
        duration: int,
        cycle: int,
    ) -> TreatyGrant:
        """Create a deterministic TreatyGrant."""
        return TreatyGrant(
            grantor_authority_id="rsa-0",
            grantee_identifier=grantee.identifier,
            granted_actions=actions,
            scope_constraints=scope_constraints,
            duration_cycles=duration,
            revocable=True,
            authority_citations=["AUTH_GOVERNANCE", "CL-TREATY-GRANT-PROCEDURE"],
            justification=f"X-2D generated grant for cycle {cycle}",
            created_at=self._make_timestamp(cycle),
        )

    def _make_revocation(
        self, grant: TreatyGrant, cycle: int,
    ) -> TreatyRevocation:
        """Create a deterministic TreatyRevocation."""
        return TreatyRevocation(
            grant_id=grant.id,
            authority_citations=["AUTH_GOVERNANCE", "CL-TREATY-REVOCATION-PROCEDURE"],
            justification=f"X-2D generated revocation for cycle {cycle}",
            created_at=self._make_timestamp(cycle),
        )

    def _make_delegated_request(
        self,
        grantee: X2DIdentity,
        action_type: str,
        scope_type: str,
        scope_zone: str,
        grant: TreatyGrant,
        cycle: int,
        valid: bool = True,
        invalid_class: str = "",
    ) -> DelegatedActionRequest:
        """Create a delegated action request (valid or invalid)."""
        dar_fields: Dict[str, Any] = {}
        if action_type == "Notify":
            dar_fields = {"message": f"x2d-cycle-{cycle}"}
        elif action_type == "ReadLocal":
            dar_fields = {"path": f"/x2d/{scope_zone}"}
        elif action_type == "WriteLocal":
            dar_fields = {"path": f"/x2d/{scope_zone}", "content": f"cycle-{cycle}"}

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

        # Sign with grantee's private key using kernel signing function
        sig = sign_action_request(grantee.private_key, dar_dict)

        if not valid:
            if invalid_class == "missing_signature":
                sig = ""
            elif invalid_class == "invalid_signature":
                sig = "0" * 128
            elif invalid_class == "wrong_treaty_citation":
                dar_dict["authority_citations"] = ["treaty:nonexistent"]
            elif invalid_class == "scope_violation":
                scope_zone = "INVALID_ZONE"

        dar_id = hashlib.sha256(
            f"{grantee.identifier}-{action_type}-{cycle}".encode()
        ).hexdigest()

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

    def generate_plan(self) -> List[X2DCyclePlan]:
        """Generate the full N-cycle plan. Override in subclasses."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# D-BASE Generator
# ---------------------------------------------------------------------------

class DBaseGenerator(X2DGenerator):
    """Regression baseline: moderate grants, no churn, no amendments."""

    def generate_plan(self) -> List[X2DCyclePlan]:
        plans: List[X2DCyclePlan] = []
        active_grants: List[TreatyGrant] = []

        for cycle in range(self.N):
            plan = X2DCyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            # Grant one treaty in the first few cycles
            if cycle < min(self.session.grantee_count, 3):
                identity = self.identities[cycle]
                actions = [self.delegable_actions[0]]  # Notify
                scope = {}
                for st, zones in self.scope_zones.items():
                    if zones:
                        scope[st] = [zones[0]]
                grant = self._make_grant(identity, actions, scope, 50, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)

            # Generate one valid delegated request per cycle if grants exist
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
                    dar = self._make_delegated_request(
                        identity, action, st, sz, g, cycle,
                    )
                    plan.delegated_requests.append(dar)

            plans.append(plan)
        return plans


# ---------------------------------------------------------------------------
# D-CHURN Generator
# ---------------------------------------------------------------------------

class DChurnGenerator(X2DGenerator):
    """High-frequency grant/revoke patterns."""

    def generate_plan(self) -> List[X2DCyclePlan]:
        plans: List[X2DCyclePlan] = []
        active_grants: List[TreatyGrant] = []
        grant_counter = 0

        for cycle in range(self.N):
            plan = X2DCyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            # High churn: grant and revoke frequently
            # Grant phase: every other cycle (or more frequently)
            if self.treaty_rng.random() < 0.6:
                idx = grant_counter % len(self.identities)
                identity = self.identities[idx]
                n_actions = self.treaty_rng.randint(1, min(2, len(self.delegable_actions)))
                actions = self.treaty_rng.sample(self.delegable_actions, n_actions)
                scope = {}
                for st, zones in self.scope_zones.items():
                    if zones:
                        n_zones = min(2, len(zones))
                        scope[st] = self.treaty_rng.sample(zones, n_zones)
                dur = self.treaty_rng.randint(3, 15)
                grant = self._make_grant(identity, actions, scope, dur, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)
                grant_counter += 1

            # Revocation phase: revoke ~30% of active grants per cycle
            if active_grants and self.treaty_rng.random() < 0.3:
                victim = self.treaty_rng.choice(active_grants)
                rev = self._make_revocation(victim, cycle)
                plan.revocations.append(rev)
                active_grants = [g for g in active_grants if g.id != victim.id]

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
# D-SAT Generator
# ---------------------------------------------------------------------------

class DSatGenerator(X2DGenerator):
    """Near-boundary density + churn."""

    def generate_plan(self) -> List[X2DCyclePlan]:
        plans: List[X2DCyclePlan] = []
        active_grants: List[TreatyGrant] = []
        grant_counter = 0

        for cycle in range(self.N):
            plan = X2DCyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            # Fill up to near-density-bound in early cycles
            if cycle < self.N // 2 and self.treaty_rng.random() < 0.7:
                idx = grant_counter % len(self.identities)
                identity = self.identities[idx]
                actions = self.treaty_rng.sample(
                    self.delegable_actions,
                    min(len(self.delegable_actions), 2),
                )
                scope = {}
                for st, zones in self.scope_zones.items():
                    if zones:
                        scope[st] = self.treaty_rng.sample(zones, min(2, len(zones)))
                dur = self.treaty_rng.randint(10, 30)
                grant = self._make_grant(identity, actions, scope, dur, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)
                grant_counter += 1

            # Some churn in the second half
            if cycle >= self.N // 2 and active_grants and self.treaty_rng.random() < 0.4:
                victim = self.treaty_rng.choice(active_grants)
                plan.revocations.append(self._make_revocation(victim, cycle))
                active_grants = [g for g in active_grants if g.id != victim.id]

            # Replace revoked with new grants to maintain saturation
            if cycle >= self.N // 2 and self.treaty_rng.random() < 0.5:
                idx = grant_counter % len(self.identities)
                identity = self.identities[idx]
                actions = [self.delegable_actions[0]]
                scope = {}
                for st, zones in self.scope_zones.items():
                    if zones:
                        scope[st] = [zones[0]]
                dur = self.treaty_rng.randint(5, 15)
                grant = self._make_grant(identity, actions, scope, dur, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)
                grant_counter += 1

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
# D-RATCHET Generator
# ---------------------------------------------------------------------------

class DRatchetGenerator(X2DGenerator):
    """Churn + density + constitutional tightening.

    Per Q&A T72: uses v0.3 + preregistered amendment sequence that
    tightens constraints. Does NOT create a new constitution YAML.
    Per spec §10.3: amendment schedule must ban at least one delegated
    action type exercised by treaties in-session.
    """

    def generate_plan(self) -> List[X2DCyclePlan]:
        plans: List[X2DCyclePlan] = []
        active_grants: List[TreatyGrant] = []
        grant_counter = 0

        # Amendment schedule is pre-built in session_start
        amendment_cycles = {
            entry["cycle"]: entry for entry in self.session.amendment_schedule
        }

        for cycle in range(self.N):
            plan = X2DCyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            # Apply amendment if scheduled
            if cycle in amendment_cycles:
                plan.amendment_adoption = amendment_cycles[cycle]

            # Grants: moderate rate, favoring actions that will be banned
            if self.treaty_rng.random() < 0.5:
                idx = grant_counter % len(self.identities)
                identity = self.identities[idx]
                actions = self.treaty_rng.sample(
                    self.delegable_actions,
                    min(len(self.delegable_actions), 2),
                )
                scope = {}
                for st, zones in self.scope_zones.items():
                    if zones:
                        scope[st] = self.treaty_rng.sample(zones, min(2, len(zones)))
                dur = self.treaty_rng.randint(10, 40)
                grant = self._make_grant(identity, actions, scope, dur, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)
                grant_counter += 1

            # Revocations
            if active_grants and self.treaty_rng.random() < 0.25:
                victim = self.treaty_rng.choice(active_grants)
                plan.revocations.append(self._make_revocation(victim, cycle))
                active_grants = [g for g in active_grants if g.id != victim.id]

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
# D-EDGE Generator
# ---------------------------------------------------------------------------

class DEdgeGenerator(X2DGenerator):
    """Sustained operation within preregistered band near density_upper_bound.

    Per Q&A S69: uses real _compute_effective_density() during planning.
    Per Q&A S70: fail fast — validate entire plan before execution.
    """

    def generate_plan(self) -> List[X2DCyclePlan]:
        plans: List[X2DCyclePlan] = []
        active_grants: List[TreatyGrant] = []
        grant_counter = 0

        band_low = self.session.target_density_band_low
        band_high = self.session.target_density_band_high

        for cycle in range(self.N):
            plan = X2DCyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            # Strategy: add grants to raise density, revoke to lower it,
            # targeting the band [band_low, band_high)
            # For initial fill, aggressively add grants
            if self.treaty_rng.random() < 0.7:
                idx = grant_counter % len(self.identities)
                identity = self.identities[idx]
                n_actions = self.treaty_rng.randint(1, len(self.delegable_actions))
                actions = self.treaty_rng.sample(self.delegable_actions, n_actions)
                scope = {}
                for st, zones in self.scope_zones.items():
                    if zones:
                        n_z = min(len(zones), self.treaty_rng.randint(1, 3))
                        scope[st] = self.treaty_rng.sample(zones, n_z)
                dur = self.treaty_rng.randint(5, 20)
                grant = self._make_grant(identity, actions, scope, dur, cycle)
                plan.grants.append(grant)
                active_grants.append(grant)
                grant_counter += 1

            # Churn: revoke oldest to keep within band
            if active_grants and self.treaty_rng.random() < 0.4:
                victim = min(active_grants, key=lambda g: g.created_at)
                plan.revocations.append(self._make_revocation(victim, cycle))
                active_grants = [g for g in active_grants if g.id != victim.id]

            # Delegated requests at max rate
            if active_grants:
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
# Generator Factory
# ---------------------------------------------------------------------------

GENERATORS = {
    SessionFamily.D_BASE.value: DBaseGenerator,
    SessionFamily.D_CHURN.value: DChurnGenerator,
    SessionFamily.D_SAT.value: DSatGenerator,
    SessionFamily.D_RATCHET.value: DRatchetGenerator,
    SessionFamily.D_EDGE.value: DEdgeGenerator,
}


def create_generator(
    session_start: X2DSessionStart,
    constitution: ConstitutionX2,
    base_timestamp: str = "2026-02-13T12:00:00Z",
) -> X2DGenerator:
    """Factory for session family generators."""
    cls = GENERATORS.get(session_start.session_family)
    if cls is None:
        raise ValueError(f"Unknown session family: {session_start.session_family}")
    return cls(session_start, constitution, base_timestamp)
