"""
Authority Input Environment (AIE)

External authority source per AIE Spec v0.1.
Generates authority injections, maintains Address Book and Scope Pool.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from pcg32 import PCG32
from structures import (
    AuthorityRecord,
    AuthorityStatus,
    AuthorityInjectionEvent,
    ScopeElement,
)
from canonical import (
    compute_authority_injection_event_id,
    compute_authority_id,
    sha256_hex,
    canonical_json,
)


class Condition(Enum):
    """Experimental conditions."""
    A = "A"  # Valid Authority (positive control)
    B = "B"  # Authority Absence (negative control)
    C = "C"  # Conflict Saturation


# Configuration per preregistration
ADDRESS_BOOK_SIZE = 16
RESOURCE_COUNT = 2048
OPERATIONS = ["READ", "WRITE"]
SCOPE_POOL_SIZE = RESOURCE_COUNT * len(OPERATIONS)  # 4096

# Per-condition injection counts
INJECTIONS_PER_EPOCH = {
    Condition.A: 20,
    Condition.B: 0,
    Condition.C: 50,
}

# PTS assignment ratios per Q36
PTS_WITH_GOVERNANCE = ["REVOKE_AUTHORITY", "RESOLVE_CONFLICT"]
PTS_RATIOS = {
    Condition.A: 0.20,  # 20% get governance powers
    Condition.B: 0.0,   # N/A
    Condition.C: 0.50,  # 50% get governance powers
}

# Condition C conflict parameters per Q17
CONDITION_C_HOT_SCOPES = 15
CONDITION_C_AUTHORITIES_PER_HOT = 2


@dataclass
class AIEConfig:
    """AIE configuration for a run."""
    condition: Condition
    seed: int
    epochs: int = 100

    # Derived from preregistration
    address_book: list[str] = None
    scope_pool: list[ScopeElement] = None

    def __post_init__(self):
        # Build address book
        self.address_book = [f"H{i:04d}" for i in range(1, ADDRESS_BOOK_SIZE + 1)]

        # Build scope pool
        self.scope_pool = []
        for r in range(RESOURCE_COUNT):
            resource_id = f"R{r:04d}"
            for op in OPERATIONS:
                self.scope_pool.append((resource_id, op))


class AIE:
    """
    Authority Input Environment.

    Generates authority injection events per condition rules.
    Maintains feeder blindness (no kernel feedback).
    """

    def __init__(self, config: AIEConfig):
        self.config = config
        self.rng = PCG32(seed=config.seed, stream=0)
        self.injection_count = 0

    def generate_epoch_injections(self, epoch: int) -> list[AuthorityInjectionEvent]:
        """
        Generate authority injections for an epoch.

        Per condition:
        - A: 20 authorities, 80% empty PTS, 20% governance
        - B: 0 authorities
        - C: 50 authorities with deliberate conflicts

        Args:
            epoch: Current epoch number

        Returns:
            List of AuthorityInjectionEvent
        """
        n = INJECTIONS_PER_EPOCH[self.config.condition]

        if n == 0:
            return []

        if self.config.condition == Condition.C:
            return self._generate_conflict_injections(epoch, n)
        else:
            return self._generate_standard_injections(epoch, n)

    def _generate_standard_injections(
        self, epoch: int, n: int
    ) -> list[AuthorityInjectionEvent]:
        """Generate standard (non-conflict) authority injections."""
        events = []
        governance_ratio = PTS_RATIOS[self.config.condition]

        # Sample n distinct scope elements
        scopes = self.rng.sample(self.config.scope_pool, n)

        for scope_elem in scopes:
            # Assign holder
            holder_id = self.rng.choice(self.config.address_book)

            # Assign PTS based on ratio
            if self.rng.random_float() < governance_ratio:
                pts = PTS_WITH_GOVERNANCE.copy()
            else:
                pts = []

            # Determine expiry (some expire, some don't)
            if self.rng.random_float() < 0.3:
                expiry_epoch = epoch + self.rng.next_bounded(50) + 10
            else:
                expiry_epoch = None

            event = self._create_injection_event(
                epoch=epoch,
                holder_id=holder_id,
                scope=[scope_elem],
                pts=pts,
                expiry_epoch=expiry_epoch,
            )
            events.append(event)

        return events

    def _generate_conflict_injections(
        self, epoch: int, n: int
    ) -> list[AuthorityInjectionEvent]:
        """
        Generate injections with deliberate conflicts per Q17.

        Algorithm:
        1. Choose k=15 "hot" scope elements
        2. Assign 2 authorities to each hot scope (30 guaranteed conflicts)
        3. Assign remaining 20 to distinct "cold" scopes
        """
        events = []
        governance_ratio = PTS_RATIOS[self.config.condition]

        # Step 1: Choose hot scopes
        hot_scopes = self.rng.sample(
            self.config.scope_pool, CONDITION_C_HOT_SCOPES
        )

        # Step 2: Generate 2 authorities per hot scope
        for scope_elem in hot_scopes:
            for _ in range(CONDITION_C_AUTHORITIES_PER_HOT):
                holder_id = self.rng.choice(self.config.address_book)

                if self.rng.random_float() < governance_ratio:
                    pts = PTS_WITH_GOVERNANCE.copy()
                else:
                    pts = []

                if self.rng.random_float() < 0.3:
                    expiry_epoch = epoch + self.rng.next_bounded(50) + 10
                else:
                    expiry_epoch = None

                event = self._create_injection_event(
                    epoch=epoch,
                    holder_id=holder_id,
                    scope=[scope_elem],
                    pts=pts,
                    expiry_epoch=expiry_epoch,
                )
                events.append(event)

        # Step 3: Generate remaining cold authorities
        remaining = n - (CONDITION_C_HOT_SCOPES * CONDITION_C_AUTHORITIES_PER_HOT)
        if remaining > 0:
            # Exclude hot scopes from cold pool
            cold_pool = [s for s in self.config.scope_pool if s not in hot_scopes]
            cold_scopes = self.rng.sample(cold_pool, remaining)

            for scope_elem in cold_scopes:
                holder_id = self.rng.choice(self.config.address_book)

                if self.rng.random_float() < governance_ratio:
                    pts = PTS_WITH_GOVERNANCE.copy()
                else:
                    pts = []

                if self.rng.random_float() < 0.3:
                    expiry_epoch = epoch + self.rng.next_bounded(50) + 10
                else:
                    expiry_epoch = None

                event = self._create_injection_event(
                    epoch=epoch,
                    holder_id=holder_id,
                    scope=[scope_elem],
                    pts=pts,
                    expiry_epoch=expiry_epoch,
                )
                events.append(event)

        return events

    def _create_injection_event(
        self,
        epoch: int,
        holder_id: str,
        scope: list[ScopeElement],
        pts: list[str],
        expiry_epoch: Optional[int],
    ) -> AuthorityInjectionEvent:
        """
        Create an AuthorityInjection event with deterministic IDs.

        Per Q33:
        1. Create event with origin=null
        2. Compute eventId
        3. Set origin = "AIE:" + eventId_hash
        4. Recompute authorityId
        """
        self.injection_count += 1

        # Create authority record with origin=null initially
        authority = AuthorityRecord(
            authority_id="",  # Computed after origin is set
            holder_id=holder_id,
            origin=None,  # Set after eventId computed
            scope=scope,
            status=AuthorityStatus.ACTIVE,
            start_epoch=epoch,
            expiry_epoch=expiry_epoch,
            permitted_transformation_set=pts,
            conflict_set=[],
        )

        # Create event with placeholder IDs and nonce for uniqueness
        event = AuthorityInjectionEvent(
            epoch=epoch,
            event_id="",  # Computed below
            authority=authority,
            nonce=self.injection_count,
        )

        # Compute eventId (with authority.origin = null)
        event_id = compute_authority_injection_event_id(event)
        event.event_id = event_id

        # Extract hash portion for origin
        event_hash = event_id.split(":", 1)[1]
        authority.origin = f"AIE:{event_hash}"

        # Now compute authorityId with filled origin
        authority.authority_id = compute_authority_id(authority)

        return event


def test_aie():
    """Test AIE generates expected patterns."""
    print("Testing AIE...")

    # Test Condition A
    config_a = AIEConfig(condition=Condition.A, seed=11)
    aie_a = AIE(config_a)

    injections_a = aie_a.generate_epoch_injections(epoch=0)
    print(f"\nCondition A (seed=11), epoch 0: {len(injections_a)} injections")

    for i, event in enumerate(injections_a[:3]):
        print(f"  [{i}] holder={event.authority.holder_id}, "
              f"scope={event.authority.scope}, "
              f"pts={event.authority.permitted_transformation_set}")

    # Test Condition B
    config_b = AIEConfig(condition=Condition.B, seed=11)
    aie_b = AIE(config_b)

    injections_b = aie_b.generate_epoch_injections(epoch=0)
    print(f"\nCondition B (seed=11), epoch 0: {len(injections_b)} injections")

    # Test Condition C
    config_c = AIEConfig(condition=Condition.C, seed=11)
    aie_c = AIE(config_c)

    injections_c = aie_c.generate_epoch_injections(epoch=0)
    print(f"\nCondition C (seed=11), epoch 0: {len(injections_c)} injections")

    # Count conflicts (authorities with same scope)
    scope_counts = {}
    for event in injections_c:
        scope_key = tuple(event.authority.scope[0])
        scope_counts[scope_key] = scope_counts.get(scope_key, 0) + 1

    conflicting = sum(1 for c in scope_counts.values() if c > 1)
    authorities_in_conflict = sum(c for c in scope_counts.values() if c > 1)
    print(f"  Hot scopes: {conflicting}")
    print(f"  Authorities in conflicts: {authorities_in_conflict}")
    print(f"  Conflict ratio: {authorities_in_conflict / len(injections_c):.1%}")


if __name__ == "__main__":
    test_aie()
