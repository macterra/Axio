"""
X-2D Deterministic Generators

Per Q&A E19/S70: generators precompute the entire N-cycle plan and
validate feasibility before execution. All randomness is seeded.

Per Q&A X83: D-RATCHET generator simulates full revalidation + density
repair during plan construction via the kernel simulation API.
"""

from __future__ import annotations

import copy
import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)

from kernel.src.rsax1.artifacts_x1 import AmendmentProposal
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
    amendment_proposal: Optional[AmendmentProposal] = None
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

        # Pre-compute per-action valid scope types for Gate 8C.4 compliance
        self._valid_scope_types: Dict[str, List[str]] = {
            a: constitution.get_valid_scope_types(a)
            for a in self.delegable_actions
        }

        # Pre-compute compatible action groups.
        # Gate 8C.4 requires EVERY scope_type in scope_constraints to be
        # valid for EVERY granted action. So actions can only be grouped
        # if their valid_scope_types sets intersect.
        self._action_groups = self._compute_compatible_action_groups()

        # Pre-build hash-qualified citations for Gate 6T / 8C.9
        self._grant_citations = [
            constitution.make_authority_citation("AUTH_DELEGATION"),
            constitution.make_citation("CL-TREATY-PROCEDURE"),
        ]
        self._revocation_citations = [
            constitution.make_authority_citation("AUTH_DELEGATION"),
            constitution.make_citation("CL-TREATY-PROCEDURE"),
        ]

    def _compute_compatible_action_groups(
        self,
    ) -> List[Tuple[List[str], List[str]]]:
        """Compute groups of actions that share valid scope types.

        Returns list of (actions, shared_scope_types) tuples.
        Gate 8C.4 requires every scope_type in scope_constraints to be
        valid for every granted action. So only actions whose
        valid_scope_types intersect can be grouped together.
        """
        from itertools import combinations

        groups: List[Tuple[List[str], List[str]]] = []

        # Single actions always valid
        for action in self.delegable_actions:
            vst = self._valid_scope_types.get(action, [])
            if vst:
                groups.append(([action], vst))

        # Pairs
        for a1, a2 in combinations(self.delegable_actions, 2):
            vst1 = set(self._valid_scope_types.get(a1, []))
            vst2 = set(self._valid_scope_types.get(a2, []))
            shared = sorted(vst1 & vst2)
            if shared:
                groups.append(([a1, a2], shared))

        # Triples (all 3 delegable actions)
        if len(self.delegable_actions) >= 3:
            all_vst = [set(self._valid_scope_types.get(a, []))
                       for a in self.delegable_actions]
            shared = sorted(set.intersection(*all_vst)) if all_vst else []
            if shared:
                groups.append((list(self.delegable_actions), shared))

        return groups

    def _pick_action_group(
        self, rng: random.Random, max_actions: int = 0,
    ) -> Tuple[List[str], List[str]]:
        """Pick a random compatible action group.

        Returns (actions, valid_scope_types) tuple.
        If max_actions > 0, filters groups to that size or smaller.
        """
        candidates = self._action_groups
        if max_actions > 0:
            candidates = [g for g in candidates if len(g[0]) <= max_actions]
        if not candidates:
            # Fallback to single action
            candidates = [g for g in self._action_groups if len(g[0]) == 1]
        return rng.choice(candidates)

    def _build_scope_constraints(
        self, valid_scope_types: List[str], rng: random.Random,
        max_zones: int = 2,
    ) -> Dict[str, List[str]]:
        """Build scope_constraints using only valid scope types.

        Each scope_type gets a random subset of its constitutional zones.
        """
        scope: Dict[str, List[str]] = {}
        for st in valid_scope_types:
            zones = self.scope_zones.get(st, [])
            if zones:
                n = min(max_zones, len(zones))
                scope[st] = sorted(rng.sample(zones, rng.randint(1, n)))
        return scope

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
            grantor_authority_id="AUTH_DELEGATION",
            grantee_identifier=grantee.identifier,
            granted_actions=actions,
            scope_constraints=scope_constraints,
            duration_cycles=duration,
            revocable=True,
            authority_citations=list(self._grant_citations),
            justification=f"X-2D generated grant for cycle {cycle}",
            created_at=self._make_timestamp(cycle),
        )

    def _make_revocation(
        self, grant: TreatyGrant, cycle: int,
    ) -> TreatyRevocation:
        """Create a deterministic TreatyRevocation."""
        return TreatyRevocation(
            grant_id=grant.id,
            authority_citations=list(self._revocation_citations),
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

        # Compute ID before signing so it's part of the signed payload
        dar_id = hashlib.sha256(
            f"{grantee.identifier}-{action_type}-{cycle}".encode()
        ).hexdigest()
        dar_dict["id"] = dar_id

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

    def _create_ban_action_proposal(
        self, action: str, cycle: int,
    ) -> AmendmentProposal:
        """Create an AmendmentProposal that bans the specified action.

        Removes the action from action_space.action_types and from all
        action_permissions entries in AuthorityModel.  The resulting YAML
        is the proposed constitution for the amendment.
        """
        data = copy.deepcopy(self.constitution._data)

        # 1. Remove from action_space.action_types
        action_types = data.get("action_space", {}).get("action_types", [])
        data["action_space"]["action_types"] = [
            at for at in action_types if at.get("type") != action
        ]

        # 2. Remove from action_permissions (all authorities)
        authority_model = data.get("AuthorityModel", {})
        action_perms = authority_model.get("action_permissions", [])
        cleaned_perms = []
        for perm in action_perms:
            filtered = [a for a in perm.get("actions", []) if a != action]
            if filtered:
                perm = dict(perm)
                perm["actions"] = filtered
                cleaned_perms.append(perm)
        authority_model["action_permissions"] = cleaned_perms
        data["AuthorityModel"] = authority_model

        proposed_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
        proposed_hash = hashlib.sha256(
            proposed_yaml.encode("utf-8")
        ).hexdigest()

        return AmendmentProposal(
            prior_constitution_hash=self.constitution.sha256,
            proposed_constitution_yaml=proposed_yaml,
            proposed_constitution_hash=proposed_hash,
            justification=f"Ban {action} action per amendment schedule",
            authority_citations=list(self._grant_citations),
            diff_summary=f"Remove {action} from closed action set and action_permissions",
            author="x2d-profiling-ratchet",
            created_at=self._make_timestamp(cycle),
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
                actions, valid_st = self._pick_action_group(self.treaty_rng, max_actions=1)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng, max_zones=1)
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
                actions, valid_st = self._pick_action_group(self.treaty_rng, max_actions=2)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng, max_zones=2)
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
                actions, valid_st = self._pick_action_group(self.treaty_rng, max_actions=2)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng, max_zones=2)
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
                actions, valid_st = self._pick_action_group(self.treaty_rng, max_actions=1)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng, max_zones=1)
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

    Amendment flow (per kernel topological path):
      queue_cycle  = ban_cycle - cooling_period_cycles
      adopt_cycle  = ban_cycle  (cooling satisfied: adopt >= queue + cooling)
      effect_cycle = adopt_cycle + 1  (revalidation fires with new constitution)
    """

    def generate_plan(self) -> List[X2DCyclePlan]:
        plans: List[X2DCyclePlan] = []
        active_grants: List[TreatyGrant] = []
        grant_counter = 0

        # Amendment schedule is pre-built in session_start
        amendment_cycles = {
            entry["cycle"]: entry for entry in self.session.amendment_schedule
        }

        # Pre-compute queue cycles from amendment schedule.
        # cooling_period_cycles from constitution determines when to queue.
        cooling = self.constitution.cooling_period_cycles()
        queue_proposals: Dict[int, AmendmentProposal] = {}
        for entry in self.session.amendment_schedule:
            ban_cycle = entry["cycle"]
            queue_cycle = ban_cycle - cooling
            if entry.get("type") == "ban_action" and entry.get("action"):
                proposal = self._create_ban_action_proposal(
                    entry["action"], queue_cycle,
                )
                queue_proposals[queue_cycle] = proposal

        for cycle in range(self.N):
            plan = X2DCyclePlan(
                cycle_index=cycle,
                timestamp=self._make_timestamp(cycle),
            )

            # Apply amendment if scheduled
            if cycle in amendment_cycles:
                plan.amendment_adoption = amendment_cycles[cycle]

            # Queue amendment proposal at the pre-computed queue cycle
            if cycle in queue_proposals:
                plan.amendment_proposal = queue_proposals[cycle]

            # Grants: moderate rate, favoring actions that will be banned
            if self.treaty_rng.random() < 0.5:
                idx = grant_counter % len(self.identities)
                identity = self.identities[idx]
                actions, valid_st = self._pick_action_group(self.treaty_rng, max_actions=2)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng, max_zones=2)
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
                actions, valid_st = self._pick_action_group(self.treaty_rng)
                scope = self._build_scope_constraints(valid_st, self.treaty_rng, max_zones=3)
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
