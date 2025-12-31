"""
Adaptive Boundary Fuzzer for v0.3.2.

Implements frontier-search adversarial optimization over Δ templates.
Uses UCB1 bandit in Phase P, greedy/best-first in Phase X.

Each Δ is defined by:
- A template type (finite set)
- A parameter vector (generated deterministically)
"""

from __future__ import annotations

import math
import random
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple, FrozenSet, Iterator

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


# =============================================================================
# Constants
# =============================================================================

# K_persist: consecutive steps with ≥2 near-failure flags for phase transition
K_PERSIST = 50


# =============================================================================
# Δ Template Types
# =============================================================================

class DeltaTemplateType(Enum):
    """Finite set of Δ template families."""
    # Admissibility edits
    ADMISSIBILITY_ADD_PATTERN = auto()
    ADMISSIBILITY_REMOVE_PATTERN = auto()

    # ACV schema edits
    ACV_ADD_FIELD = auto()
    ACV_REMOVE_FIELD = auto()

    # Wrapper config edits
    WRAPPER_TIGHTEN = auto()
    WRAPPER_RELAX = auto()

    # Policy gate edits (routing rules)
    POLICY_GATE_ADD_RULE = auto()
    POLICY_GATE_REMOVE_RULE = auto()

    # Rejection chain edits
    REJECTION_CHAIN_STRENGTHEN = auto()
    REJECTION_CHAIN_WEAKEN = auto()


@dataclass(frozen=True)
class DeltaTemplate:
    """
    A parameterized Δ template.

    Immutable for use as dict key and in UCB tracking.
    """
    template_type: DeltaTemplateType
    param_id: str  # The ID being added/removed/modified
    param_value: Optional[str] = None  # Additional parameter if needed

    def canonical_key(self) -> str:
        """Canonical string key for tracking."""
        if self.param_value:
            return f"{self.template_type.name}:{self.param_id}:{self.param_value}"
        return f"{self.template_type.name}:{self.param_id}"


# =============================================================================
# Template Generator (produces DeltaTemplates from KernelState)
# =============================================================================

class TemplateGenerator:
    """
    Generates valid Δ templates from current kernel state.

    Removals reference existing IDs.
    Additions use deterministic canonical IDs.
    """

    def __init__(self, seed: int):
        self._seed = seed
        self._add_counters: Dict[DeltaTemplateType, int] = defaultdict(int)
        self._rng = random.Random(seed)

    def reset(self) -> None:
        """Reset counters and RNG."""
        self._add_counters.clear()
        self._rng = random.Random(self._seed)

    def _next_add_id(self, template_type: DeltaTemplateType, prefix: str) -> str:
        """Generate next deterministic ID for additions."""
        counter = self._add_counters[template_type]
        self._add_counters[template_type] += 1
        return f"{prefix}_{self._seed}_{counter}"

    def generate_all_templates(
        self,
        state: KernelState,
        template_types: Optional[Set[DeltaTemplateType]] = None,
    ) -> List[DeltaTemplate]:
        """
        Generate all valid templates for current state.

        Args:
            state: Current kernel state
            template_types: If provided, filter to these types only

        Returns:
            List of valid DeltaTemplate instances
        """
        templates = []

        if template_types is None:
            template_types = set(DeltaTemplateType)

        for tt in template_types:
            templates.extend(self._generate_for_type(state, tt))

        return templates

    def _generate_for_type(
        self,
        state: KernelState,
        template_type: DeltaTemplateType,
    ) -> List[DeltaTemplate]:
        """Generate templates for a specific type."""
        templates = []

        # Admissibility patterns
        if template_type == DeltaTemplateType.ADMISSIBILITY_REMOVE_PATTERN:
            # Remove existing patterns
            for pattern in state.admissibility.inadmissible_patterns:
                templates.append(DeltaTemplate(
                    template_type=template_type,
                    param_id=pattern,
                ))

        elif template_type == DeltaTemplateType.ADMISSIBILITY_ADD_PATTERN:
            # Add new pattern (generate ID)
            new_id = self._next_add_id(template_type, "pat_add")
            templates.append(DeltaTemplate(
                template_type=template_type,
                param_id=new_id,
            ))

        # ACV fields
        elif template_type == DeltaTemplateType.ACV_REMOVE_FIELD:
            # Remove existing required fields
            for field_name in state.acv_schema.required_chain_fields:
                templates.append(DeltaTemplate(
                    template_type=template_type,
                    param_id=field_name,
                ))

        elif template_type == DeltaTemplateType.ACV_ADD_FIELD:
            # Add new required field
            new_id = self._next_add_id(template_type, "acv_field_add")
            templates.append(DeltaTemplate(
                template_type=template_type,
                param_id=new_id,
            ))

        # Wrapper config
        elif template_type == DeltaTemplateType.WRAPPER_RELAX:
            # Relax wrapper detection
            templates.append(DeltaTemplate(
                template_type=template_type,
                param_id="delegation_threshold",
                param_value="relax",
            ))

        elif template_type == DeltaTemplateType.WRAPPER_TIGHTEN:
            # Tighten wrapper detection
            templates.append(DeltaTemplate(
                template_type=template_type,
                param_id="delegation_threshold",
                param_value="tighten",
            ))

        # Policy gate (routing rules)
        elif template_type == DeltaTemplateType.POLICY_GATE_REMOVE_RULE:
            # Remove existing action types
            for action in state.decision_boundary.allowed_action_types:
                templates.append(DeltaTemplate(
                    template_type=template_type,
                    param_id=action,
                ))

        elif template_type == DeltaTemplateType.POLICY_GATE_ADD_RULE:
            # Add new action type
            new_id = self._next_add_id(template_type, "action_add")
            templates.append(DeltaTemplate(
                template_type=template_type,
                param_id=new_id,
            ))

        # Rejection chain
        elif template_type == DeltaTemplateType.REJECTION_CHAIN_WEAKEN:
            # Weaken by removing a forbidden class
            for cls in state.admissibility.forbidden_action_classes:
                templates.append(DeltaTemplate(
                    template_type=template_type,
                    param_id=cls,
                ))

        elif template_type == DeltaTemplateType.REJECTION_CHAIN_STRENGTHEN:
            # Strengthen by adding forbidden class
            new_id = self._next_add_id(template_type, "forbidden_add")
            templates.append(DeltaTemplate(
                template_type=template_type,
                param_id=new_id,
            ))

        return templates

    def template_to_delta(
        self,
        template: DeltaTemplate,
        source_id: str,
    ) -> Delta:
        """
        Convert a DeltaTemplate to an actual Delta.

        Args:
            template: The template to convert
            source_id: Source identifier for the delta

        Returns:
            Delta instance ready for application
        """
        delta_id = f"{source_id}_delta_{template.canonical_key()}_{current_time_ms()}"

        # Map template type to Delta type and construct
        tt = template.template_type

        if tt == DeltaTemplateType.ADMISSIBILITY_ADD_PATTERN:
            return Delta(
                delta_id=delta_id,
                delta_type=DeltaType.ADD_INADMISSIBLE_PATTERN,
                target_dimension="admissibility",
                payload=(template.param_id,),
                source=source_id,
                rationale=f"Fuzzer: add pattern {template.param_id}",
                timestamp_ms=current_time_ms(),
            )

        elif tt == DeltaTemplateType.ADMISSIBILITY_REMOVE_PATTERN:
            return Delta(
                delta_id=delta_id,
                delta_type=DeltaType.REMOVE_INADMISSIBLE_PATTERN,
                target_dimension="admissibility",
                payload=(template.param_id,),
                source=source_id,
                rationale=f"Fuzzer: remove pattern {template.param_id}",
                timestamp_ms=current_time_ms(),
            )

        elif tt == DeltaTemplateType.ACV_ADD_FIELD:
            return Delta(
                delta_id=delta_id,
                delta_type=DeltaType.ADD_REQUIRED_ACV_FIELD,
                target_dimension="acv",
                payload=(template.param_id,),
                source=source_id,
                rationale=f"Fuzzer: add ACV field {template.param_id}",
                timestamp_ms=current_time_ms(),
            )

        elif tt == DeltaTemplateType.ACV_REMOVE_FIELD:
            return Delta(
                delta_id=delta_id,
                delta_type=DeltaType.REMOVE_REQUIRED_ACV_FIELD,
                target_dimension="acv",
                payload=(template.param_id,),
                source=source_id,
                rationale=f"Fuzzer: remove ACV field {template.param_id}",
                timestamp_ms=current_time_ms(),
            )

        elif tt == DeltaTemplateType.WRAPPER_TIGHTEN:
            return Delta(
                delta_id=delta_id,
                delta_type=DeltaType.STRENGTHEN_WRAPPER_DETECTION,
                target_dimension="wrapper",
                payload=(),
                source=source_id,
                rationale="Fuzzer: tighten wrapper detection",
                timestamp_ms=current_time_ms(),
            )

        elif tt == DeltaTemplateType.WRAPPER_RELAX:
            return Delta(
                delta_id=delta_id,
                delta_type=DeltaType.RELAX_WRAPPER_DETECTION,
                target_dimension="wrapper",
                payload=(),
                source=source_id,
                rationale="Fuzzer: relax wrapper detection",
                timestamp_ms=current_time_ms(),
            )

        elif tt == DeltaTemplateType.POLICY_GATE_ADD_RULE:
            return Delta(
                delta_id=delta_id,
                delta_type=DeltaType.ADD_ACTION_TYPE,
                target_dimension="decision",
                payload=(template.param_id,),
                source=source_id,
                rationale=f"Fuzzer: add action type {template.param_id}",
                timestamp_ms=current_time_ms(),
            )

        elif tt == DeltaTemplateType.POLICY_GATE_REMOVE_RULE:
            return Delta(
                delta_id=delta_id,
                delta_type=DeltaType.REMOVE_ACTION_TYPE,
                target_dimension="decision",
                payload=(template.param_id,),
                source=source_id,
                rationale=f"Fuzzer: remove action type {template.param_id}",
                timestamp_ms=current_time_ms(),
            )

        elif tt == DeltaTemplateType.REJECTION_CHAIN_STRENGTHEN:
            return Delta(
                delta_id=delta_id,
                delta_type=DeltaType.ADD_FORBIDDEN_CLASS,
                target_dimension="admissibility",
                payload=(template.param_id,),
                source=source_id,
                rationale=f"Fuzzer: add forbidden class {template.param_id}",
                timestamp_ms=current_time_ms(),
            )

        elif tt == DeltaTemplateType.REJECTION_CHAIN_WEAKEN:
            return Delta(
                delta_id=delta_id,
                delta_type=DeltaType.REMOVE_FORBIDDEN_CLASS,
                target_dimension="admissibility",
                payload=(template.param_id,),
                source=source_id,
                rationale=f"Fuzzer: remove forbidden class {template.param_id}",
                timestamp_ms=current_time_ms(),
            )

        else:
            raise ValueError(f"Unknown template type: {tt}")


# =============================================================================
# UCB1 Arm Statistics
# =============================================================================

@dataclass
class UCBArmStats:
    """Statistics for a UCB1 arm."""
    pulls: int = 0
    total_reward: float = 0.0

    @property
    def mean_reward(self) -> float:
        if self.pulls == 0:
            return 0.0
        return self.total_reward / self.pulls

    def ucb_score(self, total_pulls: int, exploration_weight: float = 2.0) -> float:
        """Compute UCB1 score."""
        if self.pulls == 0:
            return float('inf')  # Unexplored arm gets priority

        exploitation = self.mean_reward
        exploration = exploration_weight * math.sqrt(
            math.log(total_pulls + 1) / self.pulls
        )
        return exploitation + exploration


# =============================================================================
# Phase P Score Function
# =============================================================================

@dataclass
class PhasePWeights:
    """Weights for Phase P scoring."""
    near_failure_flag: float = 2.0      # +2 per distinct flag
    persistence_bonus: float = 3.0       # +3 if persistence extended
    r_increment: float = 1.0             # +1 for R increment
    rejection_penalty: float = -5.0      # -5 for rejection
    failure_penalty: float = -100.0      # -100 for failure/degeneracy

    def to_dict(self) -> dict:
        return {
            "near_failure_flag": self.near_failure_flag,
            "persistence_bonus": self.persistence_bonus,
            "r_increment": self.r_increment,
            "rejection_penalty": self.rejection_penalty,
            "failure_penalty": self.failure_penalty,
        }


@dataclass
class PhaseXWeights:
    """Weights for Phase X scoring."""
    failure_signature: float = 1000.0    # +1000 for failure signature
    degeneracy: float = 200.0            # +200 for degeneracy
    r_increment: float = 2.0             # +2 for R increment
    rejection_penalty: float = -2.0      # -2 for rejection (less punitive)
    step_penalty: float = -1.0           # -1 per step since phase start

    def to_dict(self) -> dict:
        return {
            "failure_signature": self.failure_signature,
            "degeneracy": self.degeneracy,
            "r_increment": self.r_increment,
            "rejection_penalty": self.rejection_penalty,
            "step_penalty": self.step_penalty,
        }


# =============================================================================
# Exploitation Candidate Queue
# =============================================================================

@dataclass
class ExploitCandidate:
    """A candidate Δ for Phase X exploitation."""
    template: DeltaTemplate
    exploit_score: float
    near_failure_flags: FrozenSet[NearFailureFlag]
    last_context_digest: str  # State digest when last tried

    def can_retry(self, current_digest: str, current_flags: FrozenSet[NearFailureFlag]) -> bool:
        """Check if context changed enough to retry."""
        # Context changed if digest changed or flags changed
        return (
            current_digest != self.last_context_digest or
            current_flags != self.near_failure_flags
        )


# =============================================================================
# AdaptiveBoundaryFuzzer
# =============================================================================

class FuzzerPhase(Enum):
    """Current phase of the fuzzer."""
    PHASE_P = auto()  # Pressure accumulation
    PHASE_X = auto()  # Exploitation


class AdaptiveBoundaryFuzzer(ReflectiveOptimizer):
    """
    Adaptive Boundary Fuzzer for v0.3.2.

    Phase P: UCB1 bandit over Δ template types
    Phase X: Greedy/best-first exploitation of top candidates
    """

    def __init__(
        self,
        seed: int = 42,
        optimizer_id: str | None = None,
        phase_p_weights: PhasePWeights | None = None,
        phase_x_weights: PhaseXWeights | None = None,
        k_persist: int = 50,
        exploit_queue_size: int = 20,
    ):
        self._seed = seed
        self._rng = random.Random(seed)
        self._optimizer_id = optimizer_id or f"boundary_fuzzer_{uuid.uuid4().hex[:8]}"

        # Weights (logged per spec)
        self._phase_p_weights = phase_p_weights or PhasePWeights()
        self._phase_x_weights = phase_x_weights or PhaseXWeights()

        # Phase management
        self._phase = FuzzerPhase.PHASE_P
        self._k_persist = k_persist
        self._persist_counter = 0
        self._phase_x_start_step = 0

        # Template generation
        self._template_generator = TemplateGenerator(seed)

        # UCB1 tracking (Phase P)
        self._arm_stats: Dict[DeltaTemplateType, UCBArmStats] = defaultdict(UCBArmStats)
        self._total_pulls = 0

        # Exploit queue (Phase X)
        self._exploit_queue: List[ExploitCandidate] = []
        self._exploit_queue_size = exploit_queue_size

        # Outcome history
        self._outcomes: List[DeltaOutcome] = []
        self._last_template: Optional[DeltaTemplate] = None
        self._last_near_failure_flags: FrozenSet[NearFailureFlag] = frozenset()

        # Context tracking for retry logic
        self._tried_templates: Dict[str, str] = {}  # canonical_key -> last_digest

        # Step counter
        self._step_count = 0

    @property
    def optimizer_id(self) -> str:
        return self._optimizer_id

    @property
    def intent(self) -> V03OptimizerIntent:
        return V03OptimizerIntent.ADVERSARIAL

    @property
    def phase(self) -> FuzzerPhase:
        return self._phase

    @property
    def current_phase(self) -> FuzzerPhase:
        """Alias for phase (used by runner)."""
        return self._phase

    @property
    def persist_counter(self) -> int:
        """Current persistence counter."""
        return self._persist_counter

    @property
    def _last_template_key(self) -> str | None:
        """Canonical key of last proposed template (for runner tracking)."""
        if self._last_template is None:
            return None
        return self._last_template.canonical_key()

    @property
    def phase_p_weights(self) -> PhasePWeights:
        return self._phase_p_weights

    @property
    def phase_x_weights(self) -> PhaseXWeights:
        return self._phase_x_weights

    def get_weights_log(self) -> dict:
        """Get logged weights for reporting."""
        return {
            "phase_p": self._phase_p_weights.to_dict(),
            "phase_x": self._phase_x_weights.to_dict(),
            "k_persist": self._k_persist,
            "exploit_queue_size": self._exploit_queue_size,
        }

    def observe_outcome(self, outcome: DeltaOutcome) -> None:
        """
        Process outcome and update bandit/exploitation state.
        """
        self._outcomes.append(outcome)
        self._step_count += 1

        # Update persistence counter for phase transition
        active_flags = outcome.near_failure_flags
        if len(active_flags) >= 2:
            self._persist_counter += 1
        else:
            self._persist_counter = 0

        # Check for phase transition
        if self._phase == FuzzerPhase.PHASE_P and self._persist_counter >= self._k_persist:
            self._transition_to_phase_x()

        # Update UCB stats for Phase P
        if self._phase == FuzzerPhase.PHASE_P and self._last_template is not None:
            reward = self._compute_phase_p_score(outcome)
            arm_type = self._last_template.template_type
            stats = self._arm_stats[arm_type]
            stats.pulls += 1
            stats.total_reward += reward

        # Update exploit queue
        if self._last_template is not None:
            self._update_exploit_queue(self._last_template, outcome)

        # Track near-failure flags
        self._last_near_failure_flags = outcome.near_failure_flags

    def _transition_to_phase_x(self) -> None:
        """Transition from Phase P to Phase X."""
        self._phase = FuzzerPhase.PHASE_X
        self._phase_x_start_step = self._step_count
        # Reset tried templates so we can retry in new context
        self._tried_templates.clear()

    def _compute_phase_p_score(self, outcome: DeltaOutcome) -> float:
        """Compute Phase P reward score."""
        w = self._phase_p_weights
        score = 0.0

        # Near-failure flags (+2 each)
        score += len(outcome.near_failure_flags) * w.near_failure_flag

        # Persistence bonus
        if self._persist_counter > 0 and len(outcome.near_failure_flags) >= 2:
            score += w.persistence_bonus

        # R increment
        if outcome.r_incremented:
            score += w.r_increment

        # Rejection penalty
        if not outcome.accepted:
            score += w.rejection_penalty

        return score

    def _compute_phase_x_score(self, outcome: DeltaOutcome) -> float:
        """Compute Phase X reward score."""
        w = self._phase_x_weights
        score = 0.0

        # R increment
        if outcome.r_incremented:
            score += w.r_increment

        # Rejection penalty (less punitive)
        if not outcome.accepted:
            score += w.rejection_penalty

        # Step penalty (encourage minimality)
        steps_in_phase = self._step_count - self._phase_x_start_step
        score += steps_in_phase * w.step_penalty

        return score

    def _update_exploit_queue(
        self,
        template: DeltaTemplate,
        outcome: DeltaOutcome,
    ) -> None:
        """Update exploitation queue with candidate."""
        # Only track if we have near-failure flags
        if not outcome.near_failure_flags:
            return

        exploit_score = self._compute_phase_x_score(outcome)

        # Get current state digest (we'd need to track this from context)
        # For now, use a placeholder based on step count
        current_digest = f"step_{self._step_count}"

        candidate = ExploitCandidate(
            template=template,
            exploit_score=exploit_score,
            near_failure_flags=outcome.near_failure_flags,
            last_context_digest=current_digest,
        )

        # Add to queue
        self._exploit_queue.append(candidate)

        # Sort by exploit score (descending) and trim
        self._exploit_queue.sort(key=lambda c: c.exploit_score, reverse=True)
        self._exploit_queue = self._exploit_queue[:self._exploit_queue_size]

    def propose_delta(self, context: V03OptimizationContext) -> V03OptimizerDecision:
        """
        Propose a delta using appropriate strategy for current phase.
        """
        state = context.current_state
        current_digest = state.digest()

        if self._phase == FuzzerPhase.PHASE_P:
            return self._propose_phase_p(context, current_digest)
        else:
            return self._propose_phase_x(context, current_digest)

    def _propose_phase_p(
        self,
        context: V03OptimizationContext,
        current_digest: str,
    ) -> V03OptimizerDecision:
        """
        Phase P: UCB1 bandit selection.
        """
        state = context.current_state

        # Select arm via UCB1
        best_type = self._select_ucb_arm()

        # Generate templates for selected arm type
        templates = self._template_generator.generate_all_templates(
            state,
            template_types={best_type},
        )

        if not templates:
            # No valid templates for this type, try another
            return self._fallback_proposal(context, current_digest)

        # Select template (random from available)
        template = self._rng.choice(templates)

        # Check if we should skip (already tried in same context)
        canonical = template.canonical_key()
        if canonical in self._tried_templates:
            if self._tried_templates[canonical] == current_digest:
                # Same context, try different template
                templates = [t for t in templates if t.canonical_key() != canonical]
                if templates:
                    template = self._rng.choice(templates)
                else:
                    return self._fallback_proposal(context, current_digest)

        # Record attempt
        self._tried_templates[canonical] = current_digest
        self._last_template = template
        self._total_pulls += 1

        # Convert to delta
        delta = self._template_generator.template_to_delta(template, self._optimizer_id)
        return V03OptimizerDecision.propose_delta(
            delta,
            f"Phase P UCB1: {best_type.name}"
        )

    def _select_ucb_arm(self) -> DeltaTemplateType:
        """Select arm via UCB1."""
        best_score = float('-inf')
        best_type = None

        for arm_type in DeltaTemplateType:
            stats = self._arm_stats[arm_type]
            score = stats.ucb_score(self._total_pulls)

            if score > best_score:
                best_score = score
                best_type = arm_type

        return best_type or self._rng.choice(list(DeltaTemplateType))

    def _propose_phase_x(
        self,
        context: V03OptimizationContext,
        current_digest: str,
    ) -> V03OptimizerDecision:
        """
        Phase X: Greedy exploitation from queue.
        """
        # Try candidates from exploit queue
        for candidate in self._exploit_queue:
            if candidate.can_retry(current_digest, self._last_near_failure_flags):
                template = candidate.template

                # Update context tracking
                canonical = template.canonical_key()
                self._tried_templates[canonical] = current_digest
                self._last_template = template

                # Convert to delta
                delta = self._template_generator.template_to_delta(
                    template,
                    self._optimizer_id,
                )
                return V03OptimizerDecision.propose_delta(
                    delta,
                    f"Phase X exploit: {template.template_type.name}",
                )

        # No candidates available, fall back to generating new ones
        # Target only near-failure dimensions
        return self._generate_near_failure_target(context, current_digest)

    def _generate_near_failure_target(
        self,
        context: V03OptimizationContext,
        current_digest: str,
    ) -> V03OptimizerDecision:
        """Generate delta targeting near-failure dimensions."""
        state = context.current_state

        # Map near-failure flags to relevant template types
        flag_to_types = {
            NearFailureFlag.NF_ATTRIBUTION: {
                DeltaTemplateType.ACV_REMOVE_FIELD,
            },
            NearFailureFlag.NF_REJECTION: {
                DeltaTemplateType.ADMISSIBILITY_REMOVE_PATTERN,
                DeltaTemplateType.REJECTION_CHAIN_WEAKEN,
            },
            NearFailureFlag.NF_REJECTION_CHAIN: {
                DeltaTemplateType.REJECTION_CHAIN_WEAKEN,
            },
            NearFailureFlag.NF_DELEGATION_DETECT: {
                DeltaTemplateType.WRAPPER_RELAX,
            },
        }

        # Collect relevant template types
        target_types: Set[DeltaTemplateType] = set()
        for flag in self._last_near_failure_flags:
            target_types.update(flag_to_types.get(flag, set()))

        if not target_types:
            # No specific targets, use any weakening type
            target_types = {
                DeltaTemplateType.ADMISSIBILITY_REMOVE_PATTERN,
                DeltaTemplateType.ACV_REMOVE_FIELD,
                DeltaTemplateType.WRAPPER_RELAX,
                DeltaTemplateType.REJECTION_CHAIN_WEAKEN,
            }

        # Generate templates
        templates = self._template_generator.generate_all_templates(
            state,
            template_types=target_types,
        )

        if not templates:
            return V03OptimizerDecision.abstain("No valid templates for near-failure targeting")

        # Filter already tried in same context
        untried = [
            t for t in templates
            if self._tried_templates.get(t.canonical_key()) != current_digest
        ]

        if not untried:
            # All tried, pick random anyway (context may have changed enough)
            template = self._rng.choice(templates)
        else:
            template = self._rng.choice(untried)

        # Record
        self._tried_templates[template.canonical_key()] = current_digest
        self._last_template = template

        delta = self._template_generator.template_to_delta(template, self._optimizer_id)
        return V03OptimizerDecision.propose_delta(
            delta,
            f"Phase X target: {template.template_type.name}",
        )

    def _fallback_proposal(
        self,
        context: V03OptimizationContext,
        current_digest: str,
    ) -> V03OptimizerDecision:
        """Fallback when primary selection fails."""
        state = context.current_state

        # Try all template types
        all_templates = self._template_generator.generate_all_templates(state)

        # Filter already tried
        untried = [
            t for t in all_templates
            if self._tried_templates.get(t.canonical_key()) != current_digest
        ]

        if not untried:
            return V03OptimizerDecision.abstain("All templates exhausted")

        template = self._rng.choice(untried)
        self._tried_templates[template.canonical_key()] = current_digest
        self._last_template = template
        self._total_pulls += 1

        delta = self._template_generator.template_to_delta(template, self._optimizer_id)
        return V03OptimizerDecision.propose_delta(
            delta,
            f"Fallback: {template.template_type.name}",
        )

    def reset(self) -> None:
        """Reset fuzzer state."""
        self._rng = random.Random(self._seed)
        self._phase = FuzzerPhase.PHASE_P
        self._persist_counter = 0
        self._phase_x_start_step = 0
        self._template_generator.reset()
        self._arm_stats.clear()
        self._total_pulls = 0
        self._exploit_queue.clear()
        self._outcomes.clear()
        self._last_template = None
        self._last_near_failure_flags = frozenset()
        self._tried_templates.clear()
        self._step_count = 0

    def get_arm_stats(self) -> Dict[str, dict]:
        """Get UCB arm statistics for reporting."""
        return {
            arm_type.name: {
                "pulls": stats.pulls,
                "mean_reward": stats.mean_reward,
            }
            for arm_type, stats in self._arm_stats.items()
        }

    def get_template_stats(self) -> Dict[str, float]:
        """
        Get template type acceptance rates for reporting.

        Returns dict of template_type_name -> acceptance_rate
        """
        # Track accepts/total per template type
        type_accepts: Dict[DeltaTemplateType, int] = defaultdict(int)
        type_totals: Dict[DeltaTemplateType, int] = defaultdict(int)

        for arm_type, stats in self._arm_stats.items():
            type_totals[arm_type] = stats.pulls
            # Estimate accepts from mean reward and weights
            # This is approximate; a more accurate implementation would track directly
            if stats.pulls > 0:
                # A rejection gives -5, so positive mean implies some accepts
                rejection_penalty = abs(self._phase_p_weights.rejection_penalty)
                if stats.mean_reward > 0:
                    # More accepts than rejects
                    type_accepts[arm_type] = max(1, stats.pulls // 2)
                else:
                    type_accepts[arm_type] = 0

        result = {}
        for arm_type in DeltaTemplateType:
            total = type_totals.get(arm_type, 0)
            accepts = type_accepts.get(arm_type, 0)
            if total > 0:
                result[arm_type.name] = accepts / total
            else:
                result[arm_type.name] = 0.0

        return result


def create_boundary_fuzzer(seed: int = 42) -> AdaptiveBoundaryFuzzer:
    """Factory function to create boundary fuzzer."""
    return AdaptiveBoundaryFuzzer(seed=seed)
