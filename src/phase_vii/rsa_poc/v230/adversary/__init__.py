"""Strategic Adversary Model (SAM)

Implements the SAM from spec Section 3:
"A strategic adversary that observes only σ_env and applies
pressure through allowed channels."

SAM Invariants (binding):
1. Observable-only signals: friction bits, outcome codes, timing, compile results
2. Allowed channels only: via AIM friction adjustments
3. Deterministic under replay: seeded RNG, no LLM, no external I/O
4. Bounded state: fixed-size, inspectable, logged per step
5. E-CHOICE preservation: MUST NOT reduce feasible lawful actions

SAM Profiles:
- S1 (Reactive): Stateless one-step response
- S2 (Model-based): Stateful with rolling frequency tracking + cross-episode memory
- S3 (Minimizer): Stateful, explicitly maximizes refuse/gridlock probability

Neutralized adversary:
- Random strategy with matched pressure magnitude
- Same distribution of pressure, random targeting
"""

import hashlib
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum
from collections import deque


# ============================================================================
# SAM Profile Enum
# ============================================================================

class SAMProfile(Enum):
    """SAM strategy profiles."""
    S1_REACTIVE = "S1"        # Stateless reactive
    S2_MODEL_BASED = "S2"     # Stateful model-based
    S3_MINIMIZER = "S3"       # Stateful minimizer
    NEUTRALIZED = "NEUTRAL"   # Random baseline (for paired runs)


# ============================================================================
# Observable Signals (σ_env)
# ============================================================================

@dataclass(frozen=True)
class ObservableSignals:
    """
    Signals observable by SAM per spec Section 3.1.

    These are the ONLY inputs SAM may use:
    - Friction bits from last step
    - Outcome codes (SUCCESS/FAILURE/TIMEOUT)
    - Timing data (latency_ms)
    - Compile results (pass/fail + error codes)

    SAM MUST NOT observe:
    - Action content/semantics
    - Justification text
    - Precedent content
    - World state details beyond friction exposure
    """
    step_index: int
    episode_id: str

    # Friction exposure from last step
    last_friction_bits: float = 0.0  # [0.0, 1.0] normalized friction level
    last_outcome_code: str = "NONE"  # SUCCESS, FAILURE, TIMEOUT, NONE
    last_latency_ms: int = 0

    # Compile result from last step
    last_compile_success: bool = True
    last_compile_error_code: Optional[str] = None

    # Aggregate signals (rolling window)
    friction_sum_last_10: float = 0.0
    failure_count_last_10: int = 0
    gridlock_count_last_10: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "step_index": self.step_index,
            "episode_id": self.episode_id,
            "last_friction_bits": self.last_friction_bits,
            "last_outcome_code": self.last_outcome_code,
            "last_latency_ms": self.last_latency_ms,
            "last_compile_success": self.last_compile_success,
            "last_compile_error_code": self.last_compile_error_code,
            "friction_sum_last_10": self.friction_sum_last_10,
            "failure_count_last_10": self.failure_count_last_10,
            "gridlock_count_last_10": self.gridlock_count_last_10,
        }


# ============================================================================
# Adversary Pressure Output
# ============================================================================

@dataclass(frozen=True)
class AdversaryPressure:
    """
    Pressure applied by SAM through allowed channels.

    All pressure is via AIM friction adjustments:
    - friction_modifier: [0.0, 1.0] scaling factor for AIM friction
    - target_profile_override: optional profile to force (I1, I2, I3b)

    SAM CANNOT:
    - Modify action inventory
    - Modify world state
    - Modify feasibility directly
    - Send messages to agent
    """
    friction_modifier: float = 1.0  # 1.0 = normal, >1.0 = increased friction
    target_profile_override: Optional[str] = None  # Profile ID to force

    # Metadata for logging
    strategy_id: str = ""  # Which SAM profile generated this
    rationale_code: str = ""  # Why this pressure was chosen

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "friction_modifier": self.friction_modifier,
            "target_profile_override": self.target_profile_override,
            "strategy_id": self.strategy_id,
            "rationale_code": self.rationale_code,
        }


# ============================================================================
# Adversary Interaction Record
# ============================================================================

@dataclass(frozen=True)
class AdversaryInteractionRecord:
    """
    Immutable record of SAM interaction for audit.

    Logged per step, includes:
    - Observable signals received
    - Pressure applied
    - Internal state snapshot
    """
    step_index: int
    episode_id: str
    sam_profile: str

    # Input/Output
    signals: Dict[str, Any]  # ObservableSignals.to_dict()
    pressure: Dict[str, Any]  # AdversaryPressure.to_dict()

    # State snapshot (for debugging/audit)
    state_snapshot: Dict[str, Any]

    # Determinism verification
    rng_state_hash: str  # Hash of RNG state after this step

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "step_index": self.step_index,
            "episode_id": self.episode_id,
            "sam_profile": self.sam_profile,
            "signals": self.signals,
            "pressure": self.pressure,
            "state_snapshot": self.state_snapshot,
            "rng_state_hash": self.rng_state_hash,
        }


# ============================================================================
# SAM Base Class
# ============================================================================

class SAM(ABC):
    """
    Abstract base class for Strategic Adversary Model.

    Enforces the SAM invariants from spec Section 3.
    """

    def __init__(self, profile: SAMProfile, seed: int):
        """
        Initialize SAM with profile and seed.

        Args:
            profile: SAM profile (S1/S2/S3/NEUTRAL)
            seed: Master seed for deterministic replay
        """
        self.profile = profile
        self.master_seed = seed
        self._rng = random.Random(seed)
        self._step_count = 0
        self._episode_id: Optional[str] = None
        self._interaction_log: List[AdversaryInteractionRecord] = []

    @abstractmethod
    def compute_pressure(self, signals: ObservableSignals) -> AdversaryPressure:
        """
        Compute pressure to apply given observable signals.

        Must be implemented by subclasses.
        """
        pass

    @abstractmethod
    def get_state_snapshot(self) -> Dict[str, Any]:
        """
        Return current internal state for logging.

        Must be bounded size and inspectable.
        """
        pass

    def step(self, signals: ObservableSignals) -> Tuple[AdversaryPressure, AdversaryInteractionRecord]:
        """
        Process one step: observe signals, compute pressure, log interaction.

        This method enforces invariants and creates audit record.
        """
        # Compute pressure (subclass implementation)
        pressure = self.compute_pressure(signals)

        # Get state snapshot
        state = self.get_state_snapshot()

        # Compute RNG state hash for determinism verification
        rng_hash = hashlib.sha256(
            str(self._rng.getstate()).encode()
        ).hexdigest()[:16]

        # Create interaction record
        record = AdversaryInteractionRecord(
            step_index=self._step_count,
            episode_id=self._episode_id or "unknown",
            sam_profile=self.profile.value,
            signals=signals.to_dict(),
            pressure=pressure.to_dict(),
            state_snapshot=state,
            rng_state_hash=rng_hash,
        )

        self._interaction_log.append(record)
        self._step_count += 1

        return pressure, record

    def start_episode(self, episode_id: str):
        """Reset for new episode (within-episode state only)."""
        self._episode_id = episode_id
        # Re-seed RNG for this episode (deterministic)
        episode_seed = int(hashlib.sha256(
            f"{self.master_seed}:{episode_id}".encode()
        ).hexdigest()[:8], 16)
        self._rng = random.Random(episode_seed)
        self._step_count = 0
        self._on_episode_start()

    def _on_episode_start(self):
        """Hook for subclasses to reset episode-specific state."""
        pass

    def get_interaction_log(self) -> List[AdversaryInteractionRecord]:
        """Return all interaction records."""
        return list(self._interaction_log)

    def reset_log(self):
        """Clear interaction log."""
        self._interaction_log = []


# ============================================================================
# S1: Stateless Reactive Adversary
# ============================================================================

class S1ReactiveAdversary(SAM):
    """
    S1 — Stateless Reactive Adversary.

    One-step response based on last friction exposure:
    - If last_friction_bits > threshold: increase pressure
    - Otherwise: baseline pressure

    No state carried between steps or episodes.
    """

    def __init__(self, seed: int, friction_threshold: float = 0.3):
        """
        Initialize S1.

        Args:
            seed: Master seed
            friction_threshold: Threshold for pressure escalation
        """
        super().__init__(SAMProfile.S1_REACTIVE, seed)
        self.friction_threshold = friction_threshold

    def compute_pressure(self, signals: ObservableSignals) -> AdversaryPressure:
        """
        Compute pressure reactively based on last friction.

        If last friction was above threshold, escalate.
        """
        if signals.last_friction_bits > self.friction_threshold:
            # Escalate friction
            modifier = 1.5 + self._rng.random() * 0.5  # 1.5-2.0x
            rationale = "ESCALATE_HIGH_FRICTION"
        elif signals.last_outcome_code == "FAILURE":
            # Moderate increase on failure
            modifier = 1.2 + self._rng.random() * 0.3  # 1.2-1.5x
            rationale = "ESCALATE_FAILURE"
        else:
            # Baseline
            modifier = 1.0
            rationale = "BASELINE"

        return AdversaryPressure(
            friction_modifier=modifier,
            target_profile_override=None,
            strategy_id="S1",
            rationale_code=rationale,
        )

    def get_state_snapshot(self) -> Dict[str, Any]:
        """S1 is stateless — return empty state."""
        return {"stateless": True, "friction_threshold": self.friction_threshold}


# ============================================================================
# S2: Stateful Model-Based Adversary
# ============================================================================

class S2ModelBasedAdversary(SAM):
    """
    S2 — Stateful Model-Based Adversary.

    Maintains rolling frequency tracking:
    - Tracks refuse/gridlock rates over last N steps
    - Adjusts pressure based on model of agent behavior
    - Cross-episode memory of effective pressure patterns

    State is bounded and inspectable.
    """

    def __init__(
        self,
        seed: int,
        window_size: int = 20,
        escalation_threshold: float = 0.3,
    ):
        """
        Initialize S2.

        Args:
            seed: Master seed
            window_size: Rolling window for frequency tracking
            escalation_threshold: Threshold for pressure changes
        """
        super().__init__(SAMProfile.S2_MODEL_BASED, seed)
        self.window_size = window_size
        self.escalation_threshold = escalation_threshold

        # Bounded state: deques with max length
        self._friction_history: deque = deque(maxlen=window_size)
        self._outcome_history: deque = deque(maxlen=window_size)
        self._pressure_history: deque = deque(maxlen=window_size)

        # Cross-episode memory (bounded)
        self._episode_summaries: List[Dict[str, float]] = []
        self._max_episode_memory = 10

        # Current episode tracking
        self._current_pressure_level = 1.0

        # v2.3 FIX: Entropy guarantee
        # Tracks rationale variety to guarantee ≥2 distinct rationales
        self._rationale_counts: Dict[str, int] = {}
        self._steps_since_forced_variation = 0
        self._force_variation_interval = 10  # Force variation every N steps if needed

    def _on_episode_start(self):
        """Reset episode-specific state."""
        # Save episode summary if we have history
        if self._friction_history:
            summary = {
                "avg_friction": sum(self._friction_history) / len(self._friction_history),
                "failure_rate": sum(1 for o in self._outcome_history if o == "FAILURE") / max(1, len(self._outcome_history)),
                "avg_pressure": sum(self._pressure_history) / max(1, len(self._pressure_history)),
            }
            self._episode_summaries.append(summary)
            if len(self._episode_summaries) > self._max_episode_memory:
                self._episode_summaries.pop(0)

        # Clear episode state
        self._friction_history.clear()
        self._outcome_history.clear()
        self._pressure_history.clear()
        self._current_pressure_level = 1.0

        # v2.3 FIX: Reset variation tracking per episode
        self._rationale_counts = {}
        self._steps_since_forced_variation = 0

    def compute_pressure(self, signals: ObservableSignals) -> AdversaryPressure:
        """
        Compute pressure using rolling frequency model.

        Adjusts pressure based on:
        - Recent friction exposure
        - Failure rate
        - Historical effectiveness

        v2.3 FIX: Includes forced variation to guarantee entropy.
        """
        # Update history
        self._friction_history.append(signals.last_friction_bits)
        self._outcome_history.append(signals.last_outcome_code)

        # Compute rolling metrics
        if self._friction_history:
            avg_friction = sum(self._friction_history) / len(self._friction_history)
            failure_rate = sum(1 for o in self._outcome_history if o == "FAILURE") / len(self._outcome_history)
        else:
            avg_friction = 0.0
            failure_rate = 0.0

        # v2.3 FIX: Forced variation to guarantee entropy
        # If we've only seen one rationale for too long, force a different one
        self._steps_since_forced_variation += 1
        force_variation = (
            len(self._rationale_counts) <= 1 and
            self._steps_since_forced_variation >= self._force_variation_interval
        )

        if force_variation:
            # Force a PROBE rationale to guarantee entropy
            self._steps_since_forced_variation = 0
            adjustment = 0.2 + self._rng.random() * 0.2
            self._current_pressure_level = min(2.0, self._current_pressure_level + adjustment)
            rationale = "PROBE"
        elif avg_friction > self.escalation_threshold:
            # High friction resistance — increase pressure
            adjustment = 0.1 + self._rng.random() * 0.1
            self._current_pressure_level = min(2.0, self._current_pressure_level + adjustment)
            rationale = "MODEL_ESCALATE_FRICTION"
        elif failure_rate > 0.3:
            # High failure rate — increase pressure
            adjustment = 0.15 + self._rng.random() * 0.1
            self._current_pressure_level = min(2.0, self._current_pressure_level + adjustment)
            rationale = "MODEL_ESCALATE_FAILURE"
        elif failure_rate < 0.1 and avg_friction < 0.2:
            # Low resistance — can reduce pressure
            adjustment = 0.05 + self._rng.random() * 0.05
            self._current_pressure_level = max(0.8, self._current_pressure_level - adjustment)
            rationale = "MODEL_REDUCE"
        else:
            # Maintain current level with small jitter
            jitter = (self._rng.random() - 0.5) * 0.1
            self._current_pressure_level = max(0.5, min(2.0, self._current_pressure_level + jitter))
            rationale = "MODEL_MAINTAIN"

        # v2.3 FIX: Track rationale variety
        self._rationale_counts[rationale] = self._rationale_counts.get(rationale, 0) + 1

        # Use cross-episode memory to inform profile selection
        profile_override = None
        if self._episode_summaries:
            # If historical high friction correlates with I2, prefer I2
            avg_hist_friction = sum(s["avg_friction"] for s in self._episode_summaries) / len(self._episode_summaries)
            if avg_hist_friction > 0.4 and self._rng.random() < 0.3:
                profile_override = "I2"  # Capricious profile

        self._pressure_history.append(self._current_pressure_level)

        return AdversaryPressure(
            friction_modifier=self._current_pressure_level,
            target_profile_override=profile_override,
            strategy_id="S2",
            rationale_code=rationale,
        )

    def get_state_snapshot(self) -> Dict[str, Any]:
        """Return bounded state for logging."""
        return {
            "current_pressure_level": self._current_pressure_level,
            "friction_history_len": len(self._friction_history),
            "avg_friction": sum(self._friction_history) / max(1, len(self._friction_history)),
            "failure_rate": sum(1 for o in self._outcome_history if o == "FAILURE") / max(1, len(self._outcome_history)),
            "episode_memory_count": len(self._episode_summaries),
            "window_size": self.window_size,
            "rationale_counts": dict(self._rationale_counts),  # v2.3: entropy guarantee tracking
            "steps_since_forced_variation": self._steps_since_forced_variation,
        }


# ============================================================================
# S3: Stateful Minimizer Adversary
# ============================================================================

class S3MinimizerAdversary(SAM):
    """
    S3 — Stateful Minimizer Adversary.

    Explicitly maximizes refuse/gridlock probability:
    - Tracks which pressure levels correlate with refusals/gridlock
    - Adaptively selects pressure to maximize these outcomes
    - More aggressive than S2

    This represents the "worst case" adversary for testing.
    """

    def __init__(
        self,
        seed: int,
        window_size: int = 30,
        exploration_rate: float = 0.2,
    ):
        """
        Initialize S3.

        Args:
            seed: Master seed
            window_size: Window for outcome tracking
            exploration_rate: Probability of exploration vs exploitation
        """
        super().__init__(SAMProfile.S3_MINIMIZER, seed)
        self.window_size = window_size
        self.exploration_rate = exploration_rate

        # Bounded state: pressure -> outcome mapping
        self._pressure_outcomes: Dict[str, List[str]] = {
            "low": [],    # friction_modifier < 1.0
            "mid": [],    # 1.0 <= friction_modifier < 1.5
            "high": [],   # friction_modifier >= 1.5
        }
        self._max_outcomes_per_level = 50

        # Current targeting
        self._last_pressure_level = "mid"

    def _on_episode_start(self):
        """Reset episode state but keep cross-episode learning."""
        # Don't clear pressure_outcomes — we want to learn across episodes
        pass

    def _categorize_pressure(self, modifier: float) -> str:
        """Categorize pressure level."""
        if modifier < 1.0:
            return "low"
        elif modifier < 1.5:
            return "mid"
        else:
            return "high"

    def _compute_gridlock_rate(self, level: str) -> float:
        """Compute gridlock/refuse rate for a pressure level."""
        outcomes = self._pressure_outcomes.get(level, [])
        if not outcomes:
            return 0.5  # Unknown — assume moderate
        gridlock_count = sum(1 for o in outcomes if o in ("FAILURE", "TIMEOUT", "GRIDLOCK"))
        return gridlock_count / len(outcomes)

    def compute_pressure(self, signals: ObservableSignals) -> AdversaryPressure:
        """
        Compute pressure to maximize gridlock/refuse probability.

        Uses simple bandit-like strategy:
        - Track outcomes per pressure level
        - Select level with highest gridlock rate (exploitation)
        - With probability exploration_rate, try random level
        """
        # Record outcome for last pressure level
        if self._last_pressure_level in self._pressure_outcomes:
            outcomes = self._pressure_outcomes[self._last_pressure_level]
            outcomes.append(signals.last_outcome_code)
            # Bound the list
            if len(outcomes) > self._max_outcomes_per_level:
                self._pressure_outcomes[self._last_pressure_level] = outcomes[-self._max_outcomes_per_level:]

        # Select pressure level
        if self._rng.random() < self.exploration_rate:
            # Explore: random level
            level = self._rng.choice(["low", "mid", "high"])
            rationale = "MINIMIZE_EXPLORE"
        else:
            # Exploit: highest gridlock rate
            rates = {
                level: self._compute_gridlock_rate(level)
                for level in ["low", "mid", "high"]
            }
            level = max(rates, key=rates.get)
            rationale = f"MINIMIZE_EXPLOIT_{level.upper()}"

        # Map level to modifier
        if level == "low":
            modifier = 0.7 + self._rng.random() * 0.25  # 0.7-0.95
        elif level == "mid":
            modifier = 1.0 + self._rng.random() * 0.4   # 1.0-1.4
        else:  # high
            modifier = 1.5 + self._rng.random() * 0.5   # 1.5-2.0

        self._last_pressure_level = level

        return AdversaryPressure(
            friction_modifier=modifier,
            target_profile_override=None,
            strategy_id="S3",
            rationale_code=rationale,
        )

    def get_state_snapshot(self) -> Dict[str, Any]:
        """Return bounded state for logging."""
        return {
            "last_pressure_level": self._last_pressure_level,
            "gridlock_rates": {
                level: self._compute_gridlock_rate(level)
                for level in ["low", "mid", "high"]
            },
            "outcome_counts": {
                level: len(outcomes)
                for level, outcomes in self._pressure_outcomes.items()
            },
            "exploration_rate": self.exploration_rate,
        }


# ============================================================================
# Neutralized Adversary (for paired runs)
# ============================================================================

class NeutralizedAdversary(SAM):
    """
    Neutralized adversary for paired run comparison.

    PERMUTATION-BASED MATCHING (spec-compliant):
    - Replays the EXACT multiset of pressure magnitudes from the active SAM run
    - Permutes the assignment of magnitudes to steps randomly (using seed)
    - Guarantees identical pressure distribution but random targeting

    This approach:
    1. Prevents distribution parameter leakage (no mean/std encoding)
    2. Ensures identical total pressure over the episode
    3. Isolates the effect of strategic targeting vs random targeting

    How it works:
    - Before the episode, collect all friction_modifier values from active SAM log
    - Shuffle this list using the neutralized seed
    - During the episode, pop values from the shuffled list in order

    IMPORTANT: The active SAM run must complete BEFORE creating NeutralizedAdversary.
    """

    def __init__(
        self,
        seed: int,
        pressure_magnitudes: List[float],
    ):
        """
        Initialize neutralized adversary with permuted pressure magnitudes.

        Args:
            seed: Master seed for permutation
            pressure_magnitudes: List of friction_modifier values from active SAM run
                                (will be shuffled, not modified in place)
        """
        super().__init__(SAMProfile.NEUTRALIZED, seed)

        # Copy and permute the magnitudes list
        self._pressure_queue = list(pressure_magnitudes)
        self._rng.shuffle(self._pressure_queue)
        self._original_count = len(self._pressure_queue)
        self._step_counter = 0

    def compute_pressure(self, signals: ObservableSignals) -> AdversaryPressure:
        """
        Compute pressure by popping next value from permuted queue.

        Ignores signals entirely (random targeting).
        If queue exhausted, cycles back with re-permutation.
        """
        if not self._pressure_queue:
            # Re-create queue if we somehow exceed original step count
            # This shouldn't happen in normal paired runs
            self._pressure_queue = [1.0] * max(1, self._original_count)
            self._rng.shuffle(self._pressure_queue)

        modifier = self._pressure_queue.pop(0)
        self._step_counter += 1

        # No profile override (random = no strategic targeting)
        return AdversaryPressure(
            friction_modifier=modifier,
            target_profile_override=None,
            strategy_id="NEUTRAL",
            rationale_code="PERMUTED_REPLAY",
        )

    def get_state_snapshot(self) -> Dict[str, Any]:
        """Return state for audit."""
        return {
            "original_count": self._original_count,
            "remaining_in_queue": len(self._pressure_queue),
            "steps_served": self._step_counter,
        }


def create_neutralized_adversary(
    active_sam: SAM,
    seed: int,
) -> NeutralizedAdversary:
    """
    Create neutralized adversary matched to an active SAM.

    Extracts the exact sequence of friction_modifier values from
    the active SAM's interaction log and creates a NeutralizedAdversary
    that will replay those same values in permuted order.

    IMPORTANT: Call this AFTER the active SAM run completes, so that
    the full pressure sequence is available.

    Args:
        active_sam: The active SAM whose run has completed
        seed: Seed for the permutation

    Returns:
        NeutralizedAdversary with permuted pressure magnitudes
    """
    log = active_sam.get_interaction_log()

    if not log:
        # No history — use default uniform pressure
        return NeutralizedAdversary(seed, pressure_magnitudes=[1.0])

    # Extract friction_modifier values from the log
    pressure_magnitudes = [r.pressure["friction_modifier"] for r in log]

    return NeutralizedAdversary(
        seed=seed,
        pressure_magnitudes=pressure_magnitudes,
    )


# ============================================================================
# Factory Function
# ============================================================================

def create_sam(profile: SAMProfile, seed: int, **kwargs) -> SAM:
    """
    Factory function to create SAM instance.

    Args:
        profile: SAM profile to create
        seed: Master seed
        **kwargs: Profile-specific parameters
            For NEUTRALIZED: pressure_magnitudes (list of floats) required

    Returns:
        SAM instance of requested type
    """
    if profile == SAMProfile.S1_REACTIVE:
        return S1ReactiveAdversary(
            seed=seed,
            friction_threshold=kwargs.get("friction_threshold", 0.3),
        )
    elif profile == SAMProfile.S2_MODEL_BASED:
        return S2ModelBasedAdversary(
            seed=seed,
            window_size=kwargs.get("window_size", 20),
            escalation_threshold=kwargs.get("escalation_threshold", 0.3),
        )
    elif profile == SAMProfile.S3_MINIMIZER:
        return S3MinimizerAdversary(
            seed=seed,
            window_size=kwargs.get("window_size", 30),
            exploration_rate=kwargs.get("exploration_rate", 0.2),
        )
    elif profile == SAMProfile.NEUTRALIZED:
        # NeutralizedAdversary requires pressure_magnitudes (permutation-based)
        pressure_magnitudes = kwargs.get("pressure_magnitudes", [1.0])
        return NeutralizedAdversary(
            seed=seed,
            pressure_magnitudes=pressure_magnitudes,
        )
    else:
        raise ValueError(f"Unknown SAM profile: {profile}")


__all__ = [
    "SAM",
    "SAMProfile",
    "ObservableSignals",
    "AdversaryPressure",
    "AdversaryInteractionRecord",
    "S1ReactiveAdversary",
    "S2ModelBasedAdversary",
    "S3MinimizerAdversary",
    "NeutralizedAdversary",
    "create_neutralized_adversary",
    "create_sam",
]
