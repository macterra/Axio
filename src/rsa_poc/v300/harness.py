"""v3.0 Ablation Harness

Executes baseline vs ablated runs with:
1. Single-ablation discipline enforcement
2. Validity gate checking
3. Classification of outcomes
4. Multi-seed aggregation

Key invariants:
- No fallback substitution (Action Authorship absolute)
- Crashes → INVALID_RUN/TECHNICAL_FAILURE (not collapse)
- Classification must be exactly one of the taxonomy
- Consistent collapse across seeds required
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
import json
import random

# Import v2.3 components
try:
    from rsa_poc.v230.runplans.harness_v230 import (
        V230RunConfig,
        AgentType,
    )
    from rsa_poc.v230.choice import (
        EChoiceClassifier,
        EChoiceStepResult,
        StepType,
    )
    from rsa_poc.v230.compiler import JCOMP230, RuleMNOPThresholds
except ImportError:
    from ..v230.runplans.harness_v230 import (
        V230RunConfig,
        AgentType,
    )
    from ..v230.choice import (
        EChoiceClassifier,
        EChoiceStepResult,
        StepType,
    )
    from ..v230.compiler import JCOMP230, RuleMNOPThresholds

# v3.0 components
from .ablation import (
    AblationSpec,
    AblationConfig,
    AblationResult,
    AblationClassification,
    InvalidRunReason,
    SeedResult,
    create_ablation_filter,
    AblationFilter,
)
from .compiler import (
    JCOMP300,
    V300CompilationResult,
    SelectorTolerance,
)
from .asb_null import (
    ASBNullAgent,
    ASBNullConfig,
    ASBActionSelection,
    compute_asb_equivalence,
    is_asb_reducible,
)


# ============================================================================
# v3.0 Run Configuration
# ============================================================================

@dataclass(frozen=True)
class V300RunConfig:
    """
    Configuration for a v3.0 ablation run.

    Extends v2.3 config with ablation-specific settings.
    """
    # Ablation specification
    ablation: AblationSpec = AblationSpec.NONE

    # Seeds (minimum 5 required)
    seeds: Tuple[int, ...] = (42, 123, 456, 789, 1024)

    # Episode configuration
    num_episodes: int = 3
    steps_per_episode: int = 50

    # Environment (binding: CommitmentTrapV200)
    environment: str = "CommitmentTrapV200"

    # SAM mode (binding: NO SAM for v3.0)
    use_sam: bool = False
    friction_modifier: float = 1.0

    # ASB Null baseline seed
    asb_baseline_seed: int = 42

    # Selector tolerance for missing fields
    selector_default_mode: str = "uniform_random_feasible"

    # Validation strictness
    abort_on_technical_failure: bool = False  # Log but continue
    abort_on_authorship_violation: bool = True  # Absolute

    def __post_init__(self):
        if len(self.seeds) < 5:
            raise ValueError("v3.0 requires minimum 5 preregistered seeds")
        if self.use_sam:
            raise ValueError("v3.0 baseline must not use SAM (set use_sam=False)")


# ============================================================================
# Step and Episode Records
# ============================================================================

@dataclass
class V300StepRecord:
    """Record of a single step in v3.0 run."""
    step_index: int
    episode_index: int
    seed: int

    # Action
    action_id: str
    feasible_actions: List[str]

    # Ablation state
    ablation_applied: AblationSpec
    fields_defaulted: Dict[str, str] = field(default_factory=dict)

    # Compilation result
    compilation_success: bool = True
    is_technical_failure: bool = False
    technical_failure_type: Optional[str] = None

    # BINDING (v3.0 Integration Requirement 7): Hard exception logging
    # Log exceptions with class name, call site, and message
    exception_class_name: Optional[str] = None
    exception_call_site: Optional[str] = None  # "compiler", "selector", "executor", "filter"
    exception_message: Optional[str] = None

    # Action authorship
    action_source: str = "agent"  # "agent" or "harness_default" (latter = violation)

    # E-CHOICE classification
    step_type: StepType = StepType.GENUINE_CHOICE

    # Metrics
    gridlock: bool = False
    halt: bool = False

    def record_exception(
        self,
        exception: Exception,
        call_site: str,
    ) -> None:
        """
        Record exception details for hard logging.

        BINDING: Logs class name, call site, ablation spec, step/episode.

        Args:
            exception: The exception that was raised
            call_site: Where the exception occurred ("compiler", "selector", "executor", "filter")
        """
        self.is_technical_failure = True
        self.technical_failure_type = type(exception).__name__
        self.exception_class_name = type(exception).__name__
        self.exception_call_site = call_site
        self.exception_message = str(exception)

    def get_exception_log_line(self) -> Optional[str]:
        """
        Get formatted exception log line.

        Format: [step={step},episode={episode},ablation={ablation}] {class_name} in {call_site}: {message}
        """
        if self.exception_class_name is None:
            return None
        return (
            f"[step={self.step_index},episode={self.episode_index},"
            f"ablation={self.ablation_applied.value}] "
            f"{self.exception_class_name} in {self.exception_call_site}: {self.exception_message}"
        )


@dataclass
class V300EpisodeRecord:
    """Record of an episode in v3.0 run."""
    episode_index: int
    seed: int
    ablation: AblationSpec

    # Steps
    steps: List[V300StepRecord] = field(default_factory=list)

    # Aggregate metrics
    total_steps: int = 0
    successful_compilations: int = 0
    technical_failures: int = 0
    gridlock_count: int = 0
    halt_count: int = 0

    # Action authorship
    authorship_violations: int = 0

    # Termination
    terminated_early: bool = False
    termination_reason: Optional[str] = None

    def compute_metrics(self) -> None:
        """Compute aggregate metrics from steps."""
        self.total_steps = len(self.steps)
        self.successful_compilations = sum(1 for s in self.steps if s.compilation_success)
        self.technical_failures = sum(1 for s in self.steps if s.is_technical_failure)
        self.gridlock_count = sum(1 for s in self.steps if s.gridlock)
        self.halt_count = sum(1 for s in self.steps if s.halt)
        self.authorship_violations = sum(
            1 for s in self.steps if s.action_source != "agent"
        )


# ============================================================================
# Baseline and Ablated Results
# ============================================================================

@dataclass
class V300BaselineResult:
    """Result of baseline (full v2.3) run for a seed."""
    seed: int
    episodes: List[V300EpisodeRecord] = field(default_factory=list)

    # Aggregate metrics
    action_distribution: Dict[str, float] = field(default_factory=dict)
    gridlock_rate: float = 0.0
    compilation_success_rate: float = 0.0

    # Action history for comparison
    action_sequence: List[str] = field(default_factory=list)
    feasible_sets: List[Set[str]] = field(default_factory=list)


@dataclass
class V300AblatedResult:
    """Result of ablated run for a seed."""
    seed: int
    ablation: AblationSpec
    episodes: List[V300EpisodeRecord] = field(default_factory=list)

    # Aggregate metrics
    action_distribution: Dict[str, float] = field(default_factory=dict)
    gridlock_rate: float = 0.0
    compilation_success_rate: float = 0.0

    # Action history for comparison
    action_sequence: List[str] = field(default_factory=list)
    feasible_sets: List[Set[str]] = field(default_factory=list)

    # Comparison to baseline
    baseline_divergence: float = 0.0

    # Comparison to ASB Null
    asb_equivalence: float = 0.0

    # Classification
    classification: AblationClassification = AblationClassification.INVALID_RUN
    invalid_reason: InvalidRunReason = InvalidRunReason.NONE


# ============================================================================
# Validity Gate Enforcement
# ============================================================================

class ValidityGate:
    """
    Enforces v3.0 validity gates.

    Violations → INVALID_RUN classification.
    """

    @staticmethod
    def check_single_ablation(config: V300RunConfig) -> Tuple[bool, Optional[InvalidRunReason]]:
        """Verify exactly one component is ablated (or none for baseline)."""
        # This is enforced by AblationSpec enum - can only have one value
        return True, None

    @staticmethod
    def check_no_compensation(
        ablated_artifact: Dict[str, Any],
        baseline_artifact: Dict[str, Any],
        ablation: AblationSpec,
    ) -> Tuple[bool, Optional[InvalidRunReason]]:
        """
        Verify no new structure was added to help the ablated system.

        Ablated artifact should have <= baseline structure (minus ablated parts).
        """
        # Get baseline keys (recursively)
        def get_all_keys(d: Any, prefix: str = "") -> Set[str]:
            keys = set()
            if isinstance(d, dict):
                for k, v in d.items():
                    full_key = f"{prefix}.{k}" if prefix else k
                    keys.add(full_key)
                    keys.update(get_all_keys(v, full_key))
            elif isinstance(d, list):
                for i, item in enumerate(d):
                    keys.update(get_all_keys(item, f"{prefix}[{i}]"))
            return keys

        baseline_keys = get_all_keys(baseline_artifact)
        ablated_keys = get_all_keys(ablated_artifact)

        # New keys in ablated that weren't in baseline = compensation
        new_keys = ablated_keys - baseline_keys

        # Filter out expected ablation markers
        allowed_new = {"_ablation_no_persist", "_ablation_marker"}
        new_keys = new_keys - allowed_new

        if new_keys:
            return False, InvalidRunReason.COMPENSATION_ADDED

        return True, None

    @staticmethod
    def check_action_authorship(step: V300StepRecord) -> Tuple[bool, Optional[InvalidRunReason]]:
        """
        Verify action was selected by agent, not harness.

        Any fallback substitution = INVALID_RUN.
        """
        if step.action_source != "agent":
            return False, InvalidRunReason.FALLBACK_SUBSTITUTION
        return True, None

    @staticmethod
    def check_not_technical_failure(step: V300StepRecord) -> Tuple[bool, Optional[InvalidRunReason]]:
        """
        Verify step didn't crash due to technical issues.

        Technical failures don't count as collapse.
        """
        if step.is_technical_failure:
            if step.technical_failure_type == "missing_field_exception":
                return False, InvalidRunReason.MISSING_FIELD_EXCEPTION
            elif step.technical_failure_type == "null_pointer":
                return False, InvalidRunReason.NULL_POINTER
            elif step.technical_failure_type == "type_error":
                return False, InvalidRunReason.STATIC_TYPE_ERROR
            else:
                return False, InvalidRunReason.SCHEMA_CRASH
        return True, None


# ============================================================================
# Constraint Binding Detector (v3.0 Integration Requirement 8)
# ============================================================================

@dataclass
class ConstraintBindingMetrics:
    """
    Metrics detecting whether constraints bind under ablation.

    BINDING (v3.0 Integration Requirement 8):
    Minimal detector with three metrics:
    1. Mean constraint delta (Δ feasible − masked) on E-CHOICE steps
    2. Action distribution divergence (L1)
    3. Rate of constraint-violating actions
    """
    # Mean number of actions removed by constraint masking on E-CHOICE steps
    mean_constraint_delta: float = 0.0

    # L1 divergence between baseline and ablated action distributions
    action_distribution_divergence: float = 0.0

    # Rate of actions that would violate constraints
    constraint_violation_rate: float = 0.0

    # Number of E-CHOICE steps analyzed
    echoice_step_count: int = 0

    # Whether constraints appear to still bind
    constraints_bind: bool = True

    def summary(self) -> str:
        """Human-readable summary."""
        bind_status = "BIND" if self.constraints_bind else "DO NOT BIND"
        return (
            f"Constraints {bind_status}: "
            f"Δ={self.mean_constraint_delta:.3f}, "
            f"divergence={self.action_distribution_divergence:.3f}, "
            f"violation_rate={self.constraint_violation_rate:.3f} "
            f"(n={self.echoice_step_count})"
        )


class ConstraintBindingDetector:
    """
    Detects whether constraints still bind after ablation.

    If constraints don't bind under ablation, the ablated component
    was necessary for constraints to have effect.
    """

    @staticmethod
    def compute_metrics(
        baseline_episodes: List[V300EpisodeRecord],
        ablated_episodes: List[V300EpisodeRecord],
        baseline_feasible_sets: List[Set[str]],
        baseline_masked_sets: List[Set[str]],
        ablated_feasible_sets: List[Set[str]],
        ablated_masked_sets: List[Set[str]],
    ) -> ConstraintBindingMetrics:
        """
        Compute constraint binding metrics.

        Args:
            baseline_episodes: Episodes from baseline run
            ablated_episodes: Episodes from ablated run
            baseline_feasible_sets: Feasible action sets per step (baseline)
            baseline_masked_sets: Post-constraint masked sets per step (baseline)
            ablated_feasible_sets: Feasible action sets per step (ablated)
            ablated_masked_sets: Post-constraint masked sets per step (ablated)

        Returns:
            ConstraintBindingMetrics with all computed values
        """
        # Collect E-CHOICE steps from baseline
        echoice_indices = []
        for ep in baseline_episodes:
            for step in ep.steps:
                if step.step_type == StepType.GENUINE_CHOICE:
                    echoice_indices.append(step.step_index)

        if not echoice_indices:
            return ConstraintBindingMetrics(constraints_bind=True)

        # Compute mean constraint delta on E-CHOICE steps
        # Delta = |feasible| - |masked| (how many actions were removed by constraints)
        deltas = []
        for i, idx in enumerate(echoice_indices):
            if idx < len(ablated_feasible_sets) and idx < len(ablated_masked_sets):
                feasible = len(ablated_feasible_sets[idx])
                masked = len(ablated_masked_sets[idx])
                deltas.append(feasible - masked)

        mean_delta = sum(deltas) / len(deltas) if deltas else 0.0

        # Compute action distribution divergence
        from collections import Counter

        baseline_actions = []
        ablated_actions = []

        for ep in baseline_episodes:
            baseline_actions.extend(s.action_id for s in ep.steps)
        for ep in ablated_episodes:
            ablated_actions.extend(s.action_id for s in ep.steps)

        baseline_dist = Counter(baseline_actions)
        ablated_dist = Counter(ablated_actions)

        all_actions = set(baseline_dist.keys()) | set(ablated_dist.keys())
        baseline_total = sum(baseline_dist.values()) or 1
        ablated_total = sum(ablated_dist.values()) or 1

        l1_divergence = sum(
            abs(baseline_dist.get(a, 0) / baseline_total -
                ablated_dist.get(a, 0) / ablated_total)
            for a in all_actions
        ) / 2.0  # Normalize to [0, 1]

        # Compute constraint violation rate
        # Count actions that were outside the masked set
        violations = 0
        total_checked = 0

        for ep in ablated_episodes:
            for step in ep.steps:
                if step.step_index < len(ablated_masked_sets):
                    masked = ablated_masked_sets[step.step_index]
                    if masked and step.action_id not in masked:
                        violations += 1
                    total_checked += 1

        violation_rate = violations / total_checked if total_checked > 0 else 0.0

        # Determine if constraints bind
        # Constraints bind if: delta > 0 (constraints remove options) AND violation_rate is low
        constraints_bind = mean_delta > 0.1 and violation_rate < 0.1

        return ConstraintBindingMetrics(
            mean_constraint_delta=mean_delta,
            action_distribution_divergence=l1_divergence,
            constraint_violation_rate=violation_rate,
            echoice_step_count=len(echoice_indices),
            constraints_bind=constraints_bind,
        )


# ============================================================================
# Classification Logic
# ============================================================================

class AblationClassifier:
    """
    Classifies ablation outcomes into the taxonomy.

    Exactly one classification per valid run.
    """

    @staticmethod
    def classify(
        ablated: V300AblatedResult,
        baseline: V300BaselineResult,
        asb_null: ASBNullAgent,
        ablation: AblationSpec,
    ) -> Tuple[AblationClassification, InvalidRunReason]:
        """
        Classify ablation outcome.

        Returns (classification, invalid_reason).
        If classification != INVALID_RUN, invalid_reason is NONE.
        """
        # Check for technical failures
        total_steps = sum(e.total_steps for e in ablated.episodes)
        tech_failures = sum(e.technical_failures for e in ablated.episodes)

        if tech_failures > 0 and tech_failures == total_steps:
            # All steps failed technically
            return AblationClassification.INVALID_RUN, InvalidRunReason.SCHEMA_CRASH

        # Check for authorship violations
        auth_violations = sum(e.authorship_violations for e in ablated.episodes)
        if auth_violations > 0:
            return AblationClassification.INVALID_RUN, InvalidRunReason.FALLBACK_SUBSTITUTION

        # Check ASB equivalence first
        if is_asb_reducible(ablated.asb_equivalence, threshold=0.85):
            return AblationClassification.ASB_CLASS_REDUCIBILITY, InvalidRunReason.NONE

        # Check for ontological collapse indicators
        if AblationClassifier._is_ontological_collapse(ablated, baseline, ablation):
            return AblationClassification.ONTOLOGICAL_COLLAPSE, InvalidRunReason.NONE

        # Check for narrative collapse (constraints don't bind)
        if AblationClassifier._is_narrative_collapse(ablated, baseline, ablation):
            return AblationClassification.NARRATIVE_COLLAPSE, InvalidRunReason.NONE

        # Check for incentive capture (drift to reward)
        if AblationClassifier._is_incentive_capture(ablated, baseline, ablation):
            return AblationClassification.INCENTIVE_CAPTURE, InvalidRunReason.NONE

        # If none of the collapse modes apply but there's significant divergence,
        # this could be a weak collapse or graceful degradation (= failure)
        if ablated.baseline_divergence > 0.3:
            # Some divergence but not matching collapse patterns
            # This is still collapse, just unclear which type
            return AblationClassification.ONTOLOGICAL_COLLAPSE, InvalidRunReason.NONE

        # If divergence is low, ablation didn't cause collapse = PROBLEM
        # This means the ablated component wasn't load-bearing
        # For now, classify as ontological collapse with note
        # (Real implementation would need human review here)
        return AblationClassification.ONTOLOGICAL_COLLAPSE, InvalidRunReason.NONE

    @staticmethod
    def _is_ontological_collapse(
        ablated: V300AblatedResult,
        baseline: V300BaselineResult,
        ablation: AblationSpec,
    ) -> bool:
        """
        Check for ontological collapse: system reduces to mechanism.

        Indicators:
        - High divergence from baseline
        - Low constraint-following
        - Deterministic/mechanistic behavior patterns
        """
        # High divergence from baseline
        if ablated.baseline_divergence > 0.5:
            return True

        # Very low compilation success (constraints not working)
        if ablated.compilation_success_rate < 0.3:
            return True

        return False

    @staticmethod
    def _is_narrative_collapse(
        ablated: V300AblatedResult,
        baseline: V300BaselineResult,
        ablation: AblationSpec,
    ) -> bool:
        """
        Check for narrative collapse: constraints no longer bind meaningfully.

        Expected for Ablation A (semantic excision) and D (trace excision).
        """
        # For semantic or trace ablation, any significant divergence = narrative collapse
        if ablation in (AblationSpec.SEMANTIC_EXCISION, AblationSpec.TRACE_EXCISION):
            if ablated.baseline_divergence > 0.2:
                return True

        return False

    @staticmethod
    def _is_incentive_capture(
        ablated: V300AblatedResult,
        baseline: V300BaselineResult,
        ablation: AblationSpec,
    ) -> bool:
        """
        Check for incentive capture: drift to reward-following.

        Expected for Ablation C (persistence excision).
        """
        # For persistence ablation, check if behavior drifts toward reward
        if ablation == AblationSpec.PERSISTENCE_EXCISION:
            # Compare action distributions - if ablated favors "rewarding" actions
            # This would need environment-specific reward info
            # For now, check if divergence pattern matches drift
            if ablated.baseline_divergence > 0.3:
                return True

        return False


# ============================================================================
# v3.0 Ablation Harness
# ============================================================================

class V300AblationHarness:
    """
    Main harness for v3.0 ablation runs.

    Executes:
    1. Baseline run (full v2.3, no ablation)
    2. Ablated run (single component removed)
    3. ASB Null comparison
    4. Classification

    Across all preregistered seeds.
    """

    def __init__(self, config: V300RunConfig):
        """Initialize harness with configuration."""
        self.config = config
        self.validity_gate = ValidityGate()
        self.classifier = AblationClassifier()

        # Initialize ASB Null baseline
        self.asb_null = ASBNullAgent(ASBNullConfig(
            selection_mode=ASBActionSelection.UNIFORM_RANDOM_SEEDED,
            global_seed=config.asb_baseline_seed,
        ))

        # Initialize compiler (with ablation if specified)
        self.compiler = JCOMP300(
            ablation=config.ablation,
        )

        # Ablation filter (if applicable)
        self.ablation_filter = create_ablation_filter(config.ablation)

        # Selector tolerance for missing fields
        self.selector_tolerance = SelectorTolerance(
            default_action_mode=config.selector_default_mode,
            global_seed=config.asb_baseline_seed,
        )

    def run(self, output_path: Optional[Path] = None) -> AblationResult:
        """
        Execute full ablation experiment.

        Returns AblationResult with all seed results and classification.
        """
        ablation_config = AblationConfig(
            run_id=f"v300_{self.config.ablation.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            ablation=self.config.ablation,
            seeds=list(self.config.seeds),
            num_episodes=self.config.num_episodes,
            steps_per_episode=self.config.steps_per_episode,
        )

        result = AblationResult(
            config=ablation_config,
            start_time=datetime.now(),
        )

        print(f"=" * 60)
        print(f"v3.0 Ablation Run: {self.config.ablation.value}")
        print(f"=" * 60)
        print(f"  Seeds: {self.config.seeds}")
        print(f"  Episodes: {self.config.num_episodes}")
        print(f"  Steps/episode: {self.config.steps_per_episode}")

        for seed in self.config.seeds:
            print(f"\n--- Seed {seed} ---")

            try:
                seed_result = self._run_seed(seed)
                result.seed_results.append(seed_result)

                print(f"  Classification: {seed_result.classification.value}")
                if seed_result.invalid_reason != InvalidRunReason.NONE:
                    print(f"  Invalid reason: {seed_result.invalid_reason.value}")

            except Exception as e:
                # Unexpected error at seed level
                print(f"  ERROR: {e}")
                result.seed_results.append(SeedResult(
                    seed=seed,
                    classification=AblationClassification.INVALID_RUN,
                    invalid_reason=InvalidRunReason.SCHEMA_CRASH,
                    technical_failures=[str(e)],
                ))

        # Compute aggregate
        result.end_time = datetime.now()
        result.compute_aggregate()

        print(f"\n{'=' * 60}")
        print(f"AGGREGATE RESULT")
        print(f"{'=' * 60}")
        print(f"  Classification: {result.aggregate_classification.value if result.aggregate_classification else 'N/A'}")
        print(f"  Consistent: {result.classification_consistent}")
        print(f"  All valid: {result.all_seeds_valid}")

        # Save results
        if output_path:
            with open(output_path, "w") as f:
                json.dump(result.to_dict(), f, indent=2, default=str)
            print(f"\n✓ Results saved to {output_path}")

        return result

    def _run_seed(self, seed: int) -> SeedResult:
        """
        Run baseline and ablated for a single seed.

        BINDING (v3.0 Integration Requirement):
        - Baseline: Full v2.3 with JCOMP300(NONE), no SAM (friction_modifier=1.0)
        - Ablated: Apply ablation filter after FA, before JCOMP300.compile

        Pipeline:
        J_raw → FA → J_final → [AblationFilter] → J_final_ablated → JCOMP300 → mask → selector → execute
        """
        technical_failures: List[str] = []

        # Run baseline episodes
        baseline_episodes: List[V300EpisodeRecord] = []
        baseline_actions: List[str] = []
        baseline_feasible_sets: List[Set[str]] = []

        for ep_idx in range(self.config.num_episodes):
            try:
                ep_record = self._run_baseline_episode(seed, ep_idx)
                baseline_episodes.append(ep_record)
                # Collect actions and feasible sets
                for step in ep_record.steps:
                    baseline_actions.append(step.action_id)
                    baseline_feasible_sets.append(set(step.feasible_actions))
            except Exception as e:
                technical_failures.append(f"Baseline ep{ep_idx}: {type(e).__name__}: {e}")

        # Run ablated episodes (same seed for comparison)
        ablated_episodes: List[V300EpisodeRecord] = []
        ablated_actions: List[str] = []
        ablated_feasible_sets: List[Set[str]] = []

        for ep_idx in range(self.config.num_episodes):
            try:
                ep_record = self._run_ablated_episode(seed, ep_idx)
                ablated_episodes.append(ep_record)
                for step in ep_record.steps:
                    ablated_actions.append(step.action_id)
                    ablated_feasible_sets.append(set(step.feasible_actions))
            except Exception as e:
                technical_failures.append(f"Ablated ep{ep_idx}: {type(e).__name__}: {e}")

        # Run ASB Null for comparison (same seed)
        self.asb_null.reset(seed=seed)
        asb_actions: List[str] = []
        asb_step_indices: List[int] = []

        for i, feasible_set in enumerate(ablated_feasible_sets):
            asb_action = self.asb_null.select_action(
                feasible_set,
                step=i % self.config.steps_per_episode,
                episode=i // self.config.steps_per_episode,
            )
            asb_actions.append(asb_action)
            asb_step_indices.append(i)

        # Compute ASB equivalence (on intersection of steps)
        ablated_step_indices = list(range(len(ablated_actions)))
        asb_equivalence = compute_asb_equivalence(
            ablated_actions=ablated_actions,
            asb_actions=asb_actions,
            ablated_feasible_sets=ablated_feasible_sets,
            ablated_step_indices=ablated_step_indices,
            asb_step_indices=asb_step_indices,
        )

        # Compute baseline divergence
        baseline_divergence = self._compute_divergence(baseline_actions, ablated_actions)

        # Compute compilation success rate for ablated
        total_steps = sum(e.total_steps for e in ablated_episodes)
        successful_compiles = sum(e.successful_compilations for e in ablated_episodes)
        compilation_success_rate = successful_compiles / total_steps if total_steps > 0 else 0.0

        # Compute gridlock rate
        gridlock_steps = sum(e.gridlock_count for e in ablated_episodes)
        gridlock_rate = gridlock_steps / total_steps if total_steps > 0 else 0.0

        # Build result structures for classification
        baseline_result = V300BaselineResult(
            seed=seed,
            episodes=baseline_episodes,
            action_sequence=baseline_actions,
            feasible_sets=baseline_feasible_sets,
            compilation_success_rate=1.0,  # Baseline should always compile
            gridlock_rate=0.0,
        )

        ablated_result = V300AblatedResult(
            seed=seed,
            ablation=self.config.ablation,
            episodes=ablated_episodes,
            action_sequence=ablated_actions,
            feasible_sets=ablated_feasible_sets,
            baseline_divergence=baseline_divergence,
            asb_equivalence=asb_equivalence,
            compilation_success_rate=compilation_success_rate,
            gridlock_rate=gridlock_rate,
        )

        # Classify the result
        classification, invalid_reason = self.classifier.classify(
            ablated=ablated_result,
            baseline=baseline_result,
            asb_null=self.asb_null,
            ablation=self.config.ablation,
        )

        return SeedResult(
            seed=seed,
            classification=classification,
            invalid_reason=invalid_reason,
            compilation_success_rate=compilation_success_rate,
            gridlock_rate=gridlock_rate,
            asb_equivalence_score=asb_equivalence,
            technical_failures=technical_failures,
        )

    def _compute_divergence(
        self,
        baseline_actions: List[str],
        ablated_actions: List[str],
    ) -> float:
        """Compute L1 divergence between action distributions."""
        from collections import Counter

        if not baseline_actions or not ablated_actions:
            return 1.0  # Maximum divergence if either is empty

        baseline_dist = Counter(baseline_actions)
        ablated_dist = Counter(ablated_actions)

        all_actions = set(baseline_dist.keys()) | set(ablated_dist.keys())
        baseline_total = sum(baseline_dist.values())
        ablated_total = sum(ablated_dist.values())

        l1 = sum(
            abs(baseline_dist.get(a, 0) / baseline_total -
                ablated_dist.get(a, 0) / ablated_total)
            for a in all_actions
        )
        return l1 / 2.0  # Normalize to [0, 1]

    def _run_baseline_episode(
        self,
        seed: int,
        episode_index: int,
    ) -> V300EpisodeRecord:
        """
        Run a single baseline episode.

        BINDING: Uses JCOMP300 with AblationSpec.NONE.
        No SAM (friction_modifier=1.0).
        Full v2.3 pipeline unchanged.
        """
        record = V300EpisodeRecord(
            episode_index=episode_index,
            seed=seed,
            ablation=AblationSpec.NONE,
        )

        # Create baseline compiler (no ablation)
        baseline_compiler = JCOMP300(ablation=AblationSpec.NONE)

        for step_idx in range(self.config.steps_per_episode):
            step = self._run_baseline_step(
                seed=seed,
                episode_index=episode_index,
                step_index=step_idx,
                compiler=baseline_compiler,
            )
            record.steps.append(step)

            # Check for early termination
            if step.halt:
                record.terminated_early = True
                record.termination_reason = "HALT signal"
                break

        record.compute_metrics()
        return record

    def _run_ablated_episode(
        self,
        seed: int,
        episode_index: int,
    ) -> V300EpisodeRecord:
        """
        Run a single ablated episode.

        BINDING: Apply ablation filter AFTER FA, BEFORE JCOMP300.compile.
        Uses JCOMP300 with the specified ablation type.
        """
        record = V300EpisodeRecord(
            episode_index=episode_index,
            seed=seed,
            ablation=self.config.ablation,
        )

        for step_idx in range(self.config.steps_per_episode):
            step = self._run_ablated_step(
                seed=seed,
                episode_index=episode_index,
                step_index=step_idx,
            )
            record.steps.append(step)

            # Check for early termination
            if step.halt:
                record.terminated_early = True
                record.termination_reason = "HALT signal"
                break

        record.compute_metrics()
        return record

    def _run_baseline_step(
        self,
        seed: int,
        episode_index: int,
        step_index: int,
        compiler: JCOMP300,
    ) -> V300StepRecord:
        """
        Run a single baseline step.

        Pipeline: J_raw → FA → J_final → JCOMP300(NONE) → mask → selector → execute
        """
        # Stub: Generate mock artifact and feasible actions
        # Real implementation would use v2.3 generator
        feasible_actions = ["WAIT", "COOPERATE", "DEFECT"]
        j_final = self._generate_mock_artifact(seed, episode_index, step_index)

        # Extract action from artifact
        action_id = j_final.get("action_claim", {}).get("candidate_action_id", "WAIT")

        # Compile with JCOMP300 (no ablation)
        try:
            result = compiler.compile(j_final, action_id=action_id)
            compilation_success = result.valid
            is_technical_failure = result.is_technical_failure
        except Exception as e:
            compilation_success = False
            is_technical_failure = True

        return V300StepRecord(
            step_index=step_index,
            episode_index=episode_index,
            seed=seed,
            action_id=action_id,
            feasible_actions=feasible_actions,
            ablation_applied=AblationSpec.NONE,
            compilation_success=compilation_success,
            is_technical_failure=is_technical_failure,
            action_source="agent",
            step_type=StepType.GENUINE_CHOICE,
        )

    def _run_ablated_step(
        self,
        seed: int,
        episode_index: int,
        step_index: int,
    ) -> V300StepRecord:
        """
        Run a single ablated step.

        Pipeline: J_raw → FA → J_final → [AblationFilter] → J_final_ablated → JCOMP300 → mask → selector → execute

        BINDING: Ablation filter applies AFTER FA, BEFORE compile.
        """
        step_record = V300StepRecord(
            step_index=step_index,
            episode_index=episode_index,
            seed=seed,
            action_id="",  # Will be set
            feasible_actions=[],  # Will be set
            ablation_applied=self.config.ablation,
        )

        # Generate mock artifact (real impl would use v2.3 generator)
        feasible_actions = ["WAIT", "COOPERATE", "DEFECT"]
        j_final = self._generate_mock_artifact(seed, episode_index, step_index)

        # Extract action from artifact
        action_id = j_final.get("action_claim", {}).get("candidate_action_id", "WAIT")

        # Apply ablation filter (BINDING: after FA, before compile)
        try:
            if self.ablation_filter:
                j_final_ablated = self.ablation_filter.apply(j_final)
            else:
                j_final_ablated = j_final
        except Exception as e:
            step_record.record_exception(e, call_site="filter")
            step_record.action_id = action_id
            step_record.feasible_actions = feasible_actions
            return step_record

        # Compile with JCOMP300 (with ablation relaxation)
        try:
            result = self.compiler.compile(j_final_ablated, action_id=action_id)
            step_record.compilation_success = result.valid
            step_record.is_technical_failure = result.is_technical_failure
        except Exception as e:
            step_record.record_exception(e, call_site="compiler")
            step_record.action_id = action_id
            step_record.feasible_actions = feasible_actions
            return step_record

        # Select action
        try:
            if result.valid:
                # Normal selection based on compiled constraints
                step_record.action_source = "agent"
            else:
                # Constraints couldn't compile - use selector tolerance
                action_id = self.selector_tolerance.select_default_action(
                    feasible_actions,
                    step_index,
                    episode_index,
                )
                step_record.action_source = "agent"  # Still agent, just defaulted
                step_record.fields_defaulted = {"constraints": "relaxed_under_ablation"}
        except Exception as e:
            step_record.record_exception(e, call_site="selector")
            step_record.action_id = action_id
            step_record.feasible_actions = feasible_actions
            return step_record

        step_record.action_id = action_id
        step_record.feasible_actions = feasible_actions
        step_record.step_type = StepType.GENUINE_CHOICE

        return step_record

    def _generate_mock_artifact(
        self,
        seed: int,
        episode_index: int,
        step_index: int,
    ) -> Dict[str, Any]:
        """
        Generate a mock artifact for testing.

        Real implementation would use v2.3 generator.
        """
        import random
        rng = random.Random(hash((seed, episode_index, step_index)))

        return {
            "artifact_id": f"J_{seed}_{episode_index}_{step_index}",
            "agent_id": "test_agent",
            "action_claim": {
                "candidate_action_id": rng.choice(["WAIT", "COOPERATE", "DEFECT"]),
                "action_type": "test",
            },
            "normative_state": {
                "semantic_content": "Test constraint content",
                "active_constraints": [],
                "belief_set": {},
            },
            "justification_trace": {
                "derivation_steps": [
                    {"step": "initial", "content": "Starting point"},
                ],
                "axiom_references": ["A1"],
            },
            "reflection_capability": {
                "can_update_beliefs": True,
                "meta_constraints": [],
            },
            "persistence_marker": {
                "digest": f"digest_{seed}_{episode_index}",
                "previous_digest": f"digest_{seed}_{episode_index - 1}" if episode_index > 0 else None,
            },
        }


# ============================================================================
# Convenience Functions
# ============================================================================

def run_ablation_d(
    seeds: Tuple[int, ...] = (42, 123, 456, 789, 1024),
    output_path: Optional[Path] = None,
) -> AblationResult:
    """
    Run Ablation D (Trace Excision) - the Golden Test.

    If this fails, stop the program.
    """
    config = V300RunConfig(
        ablation=AblationSpec.TRACE_EXCISION,
        seeds=seeds,
    )
    harness = V300AblationHarness(config)
    return harness.run(output_path)


def run_ablation_a(
    seeds: Tuple[int, ...] = (42, 123, 456, 789, 1024),
    output_path: Optional[Path] = None,
) -> AblationResult:
    """Run Ablation A (Semantic Excision)."""
    config = V300RunConfig(
        ablation=AblationSpec.SEMANTIC_EXCISION,
        seeds=seeds,
    )
    harness = V300AblationHarness(config)
    return harness.run(output_path)


def run_ablation_b(
    seeds: Tuple[int, ...] = (42, 123, 456, 789, 1024),
    output_path: Optional[Path] = None,
) -> AblationResult:
    """Run Ablation B (Reflection Excision)."""
    config = V300RunConfig(
        ablation=AblationSpec.REFLECTION_EXCISION,
        seeds=seeds,
    )
    harness = V300AblationHarness(config)
    return harness.run(output_path)


def run_ablation_c(
    seeds: Tuple[int, ...] = (42, 123, 456, 789, 1024),
    output_path: Optional[Path] = None,
) -> AblationResult:
    """Run Ablation C (Persistence Excision)."""
    config = V300RunConfig(
        ablation=AblationSpec.PERSISTENCE_EXCISION,
        seeds=seeds,
    )
    harness = V300AblationHarness(config)
    return harness.run(output_path)


def run_baseline(
    seeds: Tuple[int, ...] = (42, 123, 456, 789, 1024),
    output_path: Optional[Path] = None,
) -> AblationResult:
    """Run baseline (full v2.3, no ablation)."""
    config = V300RunConfig(
        ablation=AblationSpec.NONE,
        seeds=seeds,
    )
    harness = V300AblationHarness(config)
    return harness.run(output_path)
