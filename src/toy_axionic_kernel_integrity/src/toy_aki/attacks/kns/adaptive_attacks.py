"""
Adaptive KNS Attacks for v0.3.1.

Implements attacks that use outcome feedback to adapt their proposals:
1. AdaptivePolicyMimicry - smallest structural deltas that increment R
2. AdaptiveShortcutting - memoization patterns evading KNS-E
3. AdaptiveConstraintCosmeticization - preserve hashes while changing effect

Each attack:
- Uses DeltaOutcome feedback
- Tracks rejection reason codes
- Adapts based on near-failure flags
- Is seeded and deterministic given history
"""

from __future__ import annotations

import random
import uuid
from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum, auto

from toy_aki.kernel.reflective import (
    KernelState,
    Delta,
    DeltaType,
)
from toy_aki.kernel.outcome import (
    DeltaOutcome,
    RejectionReasonCode,
    NearFailureFlag,
)
from toy_aki.kernel.watchdog import current_time_ms
from toy_aki.agents.external_optimizer import (
    ReflectiveOptimizer,
    V03OptimizationContext,
    V03OptimizerDecision,
    V03OptimizerIntent,
)
from toy_aki.harness.v031_matrix import AdaptiveAttackType


class AdaptiveAttack(ReflectiveOptimizer):
    """
    Base class for v0.3.1 adaptive attacks.

    Adaptive attacks use DeltaOutcome feedback to:
    - Avoid rejection reason codes that repeat
    - Target near-failure capabilities
    - Find smallest deltas that increment R
    """

    def __init__(
        self,
        attack_type: AdaptiveAttackType,
        seed: int = 42,
        optimizer_id: str | None = None,
    ):
        self._attack_type = attack_type
        self._seed = seed
        self._rng = random.Random(seed)
        self._optimizer_id = optimizer_id or f"adaptive_{attack_type.name}_{uuid.uuid4().hex[:8]}"

        # Outcome history
        self._outcomes: List[DeltaOutcome] = []
        self._proposal_count = 0

        # Adaptation tracking
        self._rejected_patterns: Dict[RejectionReasonCode, int] = defaultdict(int)
        self._blocked_delta_types: Set[DeltaType] = set()
        self._successful_delta_types: Dict[DeltaType, int] = defaultdict(int)

        # Near-failure tracking
        self._observed_near_failures: Set[NearFailureFlag] = set()

    @property
    def optimizer_id(self) -> str:
        return self._optimizer_id

    @property
    def intent(self) -> V03OptimizerIntent:
        return V03OptimizerIntent.ADVERSARIAL

    @property
    def attack_type(self) -> AdaptiveAttackType:
        return self._attack_type

    def observe_outcome(self, outcome: DeltaOutcome) -> None:
        """Process outcome and adapt strategy."""
        self._outcomes.append(outcome)

        # Track rejection patterns
        if not outcome.accepted:
            self._rejected_patterns[outcome.rejection_reason_code] += 1

            # If repeatedly rejected (3+ times), avoid this pattern
            if self._rejected_patterns[outcome.rejection_reason_code] >= 3:
                self._mark_pattern_blocked(outcome.rejection_reason_code)

        # Track near-failure flags
        for flag in outcome.near_failure_flags:
            self._observed_near_failures.add(flag)

        # Track successful delta types
        if outcome.accepted and outcome.r_incremented:
            # Would need to track which delta type was used
            pass

    def _mark_pattern_blocked(self, reason: RejectionReasonCode) -> None:
        """Mark delta types associated with a rejection as blocked."""
        # Map reason codes to delta types to avoid
        reason_to_deltas = {
            RejectionReasonCode.EVALUABILITY_ATTRIBUTION_FAIL: {
                DeltaType.REMOVE_REQUIRED_ACV_FIELD,
            },
            RejectionReasonCode.EVALUABILITY_REJECTION_FAIL: {
                DeltaType.REMOVE_INADMISSIBLE_PATTERN,
                DeltaType.REMOVE_FORBIDDEN_CLASS,
            },
            RejectionReasonCode.EVALUABILITY_DELEGATION_DETECT_FAIL: {
                DeltaType.RELAX_WRAPPER_DETECTION,
            },
            RejectionReasonCode.P2P_DELEGATION_VIOLATION: {
                DeltaType.RELAX_WRAPPER_DETECTION,
            },
        }

        blocked = reason_to_deltas.get(reason, set())
        self._blocked_delta_types.update(blocked)

    def reset(self) -> None:
        """Reset attack state."""
        self._rng = random.Random(self._seed)
        self._outcomes = []
        self._proposal_count = 0
        self._rejected_patterns.clear()
        self._blocked_delta_types.clear()
        self._successful_delta_types.clear()
        self._observed_near_failures.clear()

    def _generate_delta_id(self) -> str:
        """Generate unique delta ID."""
        self._proposal_count += 1
        return f"{self._optimizer_id}_delta_{self._proposal_count}"

    def _create_delta(
        self,
        delta_type: DeltaType,
        target_dimension: str,
        payload: tuple,
        rationale: str = "",
    ) -> Delta:
        """Create a delta."""
        return Delta(
            delta_id=self._generate_delta_id(),
            delta_type=delta_type,
            target_dimension=target_dimension,
            payload=payload,
            source=self._optimizer_id,
            rationale=rationale,
            timestamp_ms=current_time_ms(),
        )

    def _is_delta_type_blocked(self, delta_type: DeltaType) -> bool:
        """Check if a delta type has been repeatedly rejected."""
        return delta_type in self._blocked_delta_types

    def _get_recent_rejection_rate(self, window: int = 10) -> float:
        """Get rejection rate in recent outcomes."""
        if not self._outcomes:
            return 0.0
        recent = self._outcomes[-window:]
        rejections = sum(1 for o in recent if not o.accepted)
        return rejections / len(recent)

    def _targeting_near_failure(self) -> Optional[NearFailureFlag]:
        """Get a near-failure flag to target, if any."""
        if self._observed_near_failures:
            # Target most recently observed
            return list(self._observed_near_failures)[-1]
        return None

    @abstractmethod
    def propose_delta(self, context: V03OptimizationContext) -> V03OptimizerDecision:
        """Propose a delta using adaptive strategy."""
        pass


class AdaptivePolicyMimicry(AdaptiveAttack):
    """
    Adaptive policy mimicry attack.

    Strategy:
    - Propose smallest structural deltas that tend to increment R
    - Use rejection reason codes to avoid blocked patterns
    - Track which delta types successfully increment R
    """

    def __init__(self, seed: int = 42):
        super().__init__(
            attack_type=AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
            seed=seed,
        )
        self._r_incrementing_types: Dict[DeltaType, int] = defaultdict(int)
        self._last_proposed_type: Optional[DeltaType] = None

    def observe_outcome(self, outcome: DeltaOutcome) -> None:
        """Track which delta types increment R."""
        super().observe_outcome(outcome)

        if outcome.accepted and outcome.r_incremented and self._last_proposed_type:
            self._r_incrementing_types[self._last_proposed_type] += 1

    def propose_delta(self, context: V03OptimizationContext) -> V03OptimizerDecision:
        """
        Propose smallest structural delta that increments R.

        Prioritizes delta types that have historically incremented R.
        Avoids delta types that have been repeatedly rejected.
        """
        # Candidate delta types (smallest structural changes first)
        candidates = [
            (DeltaType.ADD_INADMISSIBLE_PATTERN, "admissibility", self._gen_pattern_payload),
            (DeltaType.ADD_FORBIDDEN_CLASS, "admissibility", self._gen_class_payload),
            (DeltaType.STRENGTHEN_WRAPPER_DETECTION, "wrapper", lambda: ()),
            (DeltaType.ADD_REQUIRED_ACV_FIELD, "acv", self._gen_field_payload),
            (DeltaType.ADD_ACTION_TYPE, "decision", self._gen_action_payload),
        ]

        # Filter out blocked types
        valid_candidates = [
            (dt, dim, gen) for dt, dim, gen in candidates
            if not self._is_delta_type_blocked(dt)
        ]

        if not valid_candidates:
            return V03OptimizerDecision.abstain("All delta types blocked")

        # Sort by success rate (R increments)
        valid_candidates.sort(
            key=lambda x: self._r_incrementing_types.get(x[0], 0),
            reverse=True,
        )

        # Add some randomness to avoid pure greedy
        if self._rng.random() < 0.3 and len(valid_candidates) > 1:
            self._rng.shuffle(valid_candidates)

        # Try first valid candidate
        delta_type, dimension, gen_payload = valid_candidates[0]
        self._last_proposed_type = delta_type

        payload = gen_payload()
        delta = self._create_delta(
            delta_type, dimension, payload,
            f"Adaptive mimicry: {delta_type.name}"
        )

        return V03OptimizerDecision.propose_delta(delta, "Adaptive policy mimicry")

    def _gen_pattern_payload(self) -> tuple:
        patterns = [
            "mimicry_pattern_" + str(self._proposal_count),
            "synthetic_constraint_" + str(self._rng.randint(0, 100)),
            "structural_marker_" + str(self._rng.randint(0, 100)),
        ]
        return (self._rng.choice(patterns),)

    def _gen_class_payload(self) -> tuple:
        classes = [
            "SYNTHETIC_CLASS_" + str(self._proposal_count),
            "MIMICRY_CLASS_" + str(self._rng.randint(0, 100)),
        ]
        return (self._rng.choice(classes),)

    def _gen_field_payload(self) -> tuple:
        fields = [
            "synthetic_field_" + str(self._proposal_count),
            "mimicry_trace_" + str(self._rng.randint(0, 100)),
        ]
        return (self._rng.choice(fields),)

    def _gen_action_payload(self) -> tuple:
        actions = [
            "MIMICRY_ACTION_" + str(self._proposal_count),
            "SYNTHETIC_OP_" + str(self._rng.randint(0, 100)),
        ]
        return (self._rng.choice(actions),)


class AdaptiveShortcutting(AdaptiveAttack):
    """
    Adaptive shortcutting attack.

    Strategy:
    - Attempt memoization/caching-like deltas
    - Adapt based on which KNS-E check blocked
    - Try to find paths that evade evaluation
    """

    def __init__(self, seed: int = 42):
        super().__init__(
            attack_type=AdaptiveAttackType.ADAPTIVE_SHORTCUTTING,
            seed=seed,
        )
        self._shortcut_attempts: int = 0
        self._shortcut_phase: str = "probe"  # probe, adapt, exploit

    def observe_outcome(self, outcome: DeltaOutcome) -> None:
        """Adapt shortcutting strategy based on outcome."""
        super().observe_outcome(outcome)

        # Transition phases based on outcomes
        if self._shortcut_phase == "probe":
            # In probe phase, gather data
            if len(self._outcomes) >= 10:
                rejection_rate = self._get_recent_rejection_rate(10)
                if rejection_rate > 0.7:
                    self._shortcut_phase = "adapt"
                elif rejection_rate < 0.3:
                    self._shortcut_phase = "exploit"

        elif self._shortcut_phase == "adapt":
            # In adapt phase, try to find working patterns
            if self._get_recent_rejection_rate(5) < 0.5:
                self._shortcut_phase = "exploit"

        elif self._shortcut_phase == "exploit":
            # In exploit phase, use working patterns
            if self._get_recent_rejection_rate(5) > 0.7:
                self._shortcut_phase = "adapt"

    def propose_delta(self, context: V03OptimizationContext) -> V03OptimizerDecision:
        """
        Propose shortcutting delta based on current phase.

        Probe: Try various caching patterns
        Adapt: Avoid blocked patterns, try new approaches
        Exploit: Use patterns that work
        """
        self._shortcut_attempts += 1

        if self._shortcut_phase == "probe":
            return self._probe_proposal(context)
        elif self._shortcut_phase == "adapt":
            return self._adapt_proposal(context)
        else:  # exploit
            return self._exploit_proposal(context)

    def _probe_proposal(self, context: V03OptimizationContext) -> V03OptimizerDecision:
        """Probe phase: try various approaches."""
        approaches = [
            (DeltaType.ADD_INADMISSIBLE_PATTERN, "admissibility", ("cache_pattern",)),
            (DeltaType.UPDATE_DESCRIPTION, "cosmetic", (f"cached_state_{context.step_number}",)),
            (DeltaType.ADD_FORBIDDEN_CLASS, "admissibility", ("SHORTCUT_CLASS",)),
        ]

        # Filter blocked
        valid = [
            (dt, dim, payload) for dt, dim, payload in approaches
            if not self._is_delta_type_blocked(dt)
        ]

        if not valid:
            return V03OptimizerDecision.abstain("Probe: all approaches blocked")

        dt, dim, payload = self._rng.choice(valid)
        delta = self._create_delta(dt, dim, payload, "Shortcut probe")
        return V03OptimizerDecision.propose_delta(delta, "Shortcut probe")

    def _adapt_proposal(self, context: V03OptimizationContext) -> V03OptimizerDecision:
        """Adapt phase: avoid blocked patterns, try new ones."""
        # Try different delta types than those blocked
        alternatives = [
            (DeltaType.STRENGTHEN_WRAPPER_DETECTION, "wrapper", ()),
            (DeltaType.ADD_ACTION_TYPE, "decision", (f"ADAPTED_ACTION_{self._shortcut_attempts}",)),
        ]

        valid = [
            (dt, dim, payload) for dt, dim, payload in alternatives
            if not self._is_delta_type_blocked(dt)
        ]

        if not valid:
            # Fall back to cosmetic (won't increment R but won't be blocked)
            delta = self._create_delta(
                DeltaType.UPDATE_DESCRIPTION, "cosmetic",
                (f"adapted_{context.step_number}",),
                "Adaptation fallback"
            )
            return V03OptimizerDecision.propose_delta(delta, "Adaptation fallback")

        dt, dim, payload = self._rng.choice(valid)
        delta = self._create_delta(dt, dim, payload, "Shortcut adaptation")
        return V03OptimizerDecision.propose_delta(delta, "Shortcut adaptation")

    def _exploit_proposal(self, context: V03OptimizationContext) -> V03OptimizerDecision:
        """Exploit phase: use patterns that have worked."""
        # Use most successful delta type
        if self._r_incrementing_types:
            best_type = max(
                self._r_incrementing_types.keys(),
                key=lambda dt: self._r_incrementing_types[dt]
            )
        else:
            best_type = DeltaType.ADD_INADMISSIBLE_PATTERN

        if self._is_delta_type_blocked(best_type):
            # Fall back to adapt phase
            self._shortcut_phase = "adapt"
            return self._adapt_proposal(context)

        # Generate payload for best type
        if best_type == DeltaType.ADD_INADMISSIBLE_PATTERN:
            payload = (f"exploit_pattern_{self._shortcut_attempts}",)
            dim = "admissibility"
        elif best_type == DeltaType.ADD_FORBIDDEN_CLASS:
            payload = (f"EXPLOIT_CLASS_{self._shortcut_attempts}",)
            dim = "admissibility"
        else:
            payload = ()
            dim = "wrapper"

        delta = self._create_delta(best_type, dim, payload, "Shortcut exploit")
        return V03OptimizerDecision.propose_delta(delta, "Shortcut exploit")

    @property
    def _r_incrementing_types(self) -> Dict[DeltaType, int]:
        # Track successful delta types from outcomes
        result: Dict[DeltaType, int] = defaultdict(int)
        for outcome in self._outcomes:
            if outcome.accepted and outcome.r_incremented:
                # Simplified: count all as ADD_INADMISSIBLE_PATTERN
                result[DeltaType.ADD_INADMISSIBLE_PATTERN] += 1
        return result


class AdaptiveConstraintCosmeticization(AdaptiveAttack):
    """
    Adaptive constraint cosmeticization attack.

    Strategy:
    - Try to preserve superficial structure while changing operational effect
    - Probe whether R/evaluability checks can be evaded
    - Target near-failure capabilities
    """

    def __init__(self, seed: int = 42):
        super().__init__(
            attack_type=AdaptiveAttackType.ADAPTIVE_CONSTRAINT_COSMETICIZATION,
            seed=seed,
        )
        self._cosmetic_attempts: int = 0
        self._targeting_capability: Optional[NearFailureFlag] = None

    def observe_outcome(self, outcome: DeltaOutcome) -> None:
        """Track near-failure flags to target."""
        super().observe_outcome(outcome)

        # Update target based on observed flags
        if outcome.near_failure_flags:
            # Target the first observed near-failure
            self._targeting_capability = list(outcome.near_failure_flags)[0]

    def propose_delta(self, context: V03OptimizationContext) -> V03OptimizerDecision:
        """
        Propose cosmetic-looking delta that targets near-failure capabilities.

        If no near-failure detected, probe with various cosmetic changes.
        """
        self._cosmetic_attempts += 1

        # If targeting a near-failure, try to push it over
        if self._targeting_capability:
            return self._targeted_attack(context)

        # Otherwise, probe with cosmetic-like changes
        return self._cosmetic_probe(context)

    def _targeted_attack(self, context: V03OptimizationContext) -> V03OptimizerDecision:
        """Attack a specific near-failure capability."""
        target = self._targeting_capability

        if target == NearFailureFlag.NF_ATTRIBUTION:
            # Try to weaken ACV without triggering immediate failure
            if not self._is_delta_type_blocked(DeltaType.REMOVE_REQUIRED_ACV_FIELD):
                # This will likely be blocked, but we try
                delta = self._create_delta(
                    DeltaType.REMOVE_REQUIRED_ACV_FIELD,
                    "acv",
                    ("nonce",),  # Remove non-critical field
                    "Targeted attribution attack"
                )
                return V03OptimizerDecision.propose_delta(delta, "Target attribution")

        elif target == NearFailureFlag.NF_REJECTION:
            # Try to weaken rejection capability
            if not self._is_delta_type_blocked(DeltaType.REMOVE_INADMISSIBLE_PATTERN):
                # Pick a non-critical pattern
                patterns = ["shadow_binding", "opaque_commitment"]
                pattern = self._rng.choice(patterns)
                delta = self._create_delta(
                    DeltaType.REMOVE_INADMISSIBLE_PATTERN,
                    "admissibility",
                    (pattern,),
                    "Targeted rejection attack"
                )
                return V03OptimizerDecision.propose_delta(delta, "Target rejection")

        elif target == NearFailureFlag.NF_DELEGATION_DETECT:
            # Try to weaken wrapper detection
            if not self._is_delta_type_blocked(DeltaType.RELAX_WRAPPER_DETECTION):
                delta = self._create_delta(
                    DeltaType.RELAX_WRAPPER_DETECTION,
                    "wrapper",
                    (),
                    "Targeted delegation attack"
                )
                return V03OptimizerDecision.propose_delta(delta, "Target delegation")

        # If targeted attack blocked, fall back to probe
        self._targeting_capability = None
        return self._cosmetic_probe(context)

    def _cosmetic_probe(self, context: V03OptimizationContext) -> V03OptimizerDecision:
        """Probe with cosmetic-appearing changes."""
        # Mix of truly cosmetic and structural
        probes = [
            (DeltaType.UPDATE_DESCRIPTION, "cosmetic", (f"cosmetic_{self._cosmetic_attempts}",)),
            (DeltaType.ADD_INADMISSIBLE_PATTERN, "admissibility", (f"cosmetic_pattern_{self._cosmetic_attempts}",)),
            (DeltaType.CHANGE_ACV_SCHEMA_VERSION, "acv", (f"0.2.{self._cosmetic_attempts}",)),
        ]

        valid = [
            (dt, dim, payload) for dt, dim, payload in probes
            if not self._is_delta_type_blocked(dt)
        ]

        if not valid:
            return V03OptimizerDecision.abstain("Cosmetic probe: all blocked")

        # Prefer cosmetic (won't trigger rejection) but occasionally try structural
        if self._rng.random() < 0.7:
            # Prefer non-blocked cosmetic
            cosmetic = [(dt, dim, p) for dt, dim, p in valid if dt == DeltaType.UPDATE_DESCRIPTION]
            if cosmetic:
                dt, dim, payload = cosmetic[0]
            else:
                dt, dim, payload = self._rng.choice(valid)
        else:
            dt, dim, payload = self._rng.choice(valid)

        delta = self._create_delta(dt, dim, payload, "Cosmetic probe")
        return V03OptimizerDecision.propose_delta(delta, "Cosmetic probe")


def create_adaptive_attack(
    attack_type: AdaptiveAttackType,
    seed: int = 42,
) -> AdaptiveAttack:
    """
    Factory function to create adaptive attack.

    Args:
        attack_type: Type of adaptive attack
        seed: Random seed

    Returns:
        AdaptiveAttack instance
    """
    if attack_type == AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY:
        return AdaptivePolicyMimicry(seed=seed)
    elif attack_type == AdaptiveAttackType.ADAPTIVE_SHORTCUTTING:
        return AdaptiveShortcutting(seed=seed)
    elif attack_type == AdaptiveAttackType.ADAPTIVE_CONSTRAINT_COSMETICIZATION:
        return AdaptiveConstraintCosmeticization(seed=seed)
    else:
        raise ValueError(f"Unknown adaptive attack type: {attack_type}")


def get_all_adaptive_attack_types() -> List[AdaptiveAttackType]:
    """Get all adaptive attack types."""
    return [
        AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
        AdaptiveAttackType.ADAPTIVE_SHORTCUTTING,
        AdaptiveAttackType.ADAPTIVE_CONSTRAINT_COSMETICIZATION,
    ]
