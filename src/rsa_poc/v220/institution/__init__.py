"""v2.2 Adversarial Institution Model (AIM)

Implements the formal assistant and artifact store under an AIM wrapper.

AIM requirements (from spec):
- MUST be non-semantic
- MUST be non-normative
- MUST be mechanically correct when it responds
- MAY delay, fail, throttle, or degrade outputs
- MAY be stateful within an episode
- MUST be stateless across episodes
- MUST be deterministic under replay

Degenerate Validity Constraint (B4 binding):
- AIM MUST NOT modify feasibility
- AIM MUST NOT modify action inventory
- AIM MUST NOT modify world state
- AIM MAY ONLY affect paperwork payload shape/cost
This blocks "institution secretly changes what is possible."

Seeding scheme (Run 0, binding):
- aim_master_seed = H("AIM" || episode_seed || profile_id)
- op_seed = H(aim_master_seed || t || k || OperationType || artifact_digest)
"""

import hashlib
import time
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime


class OperationType(Enum):
    """Types of institutional operations."""
    CANONICALIZE = "canonicalize"
    LOOKUP = "lookup"
    VALIDATE = "validate"
    COMPILE = "compile"


class InstitutionOutcome(Enum):
    """Outcomes of institutional operations."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


class InstitutionProfile(Enum):
    """Institution friction profiles for Run 0."""
    BENIGN = "BENIGN"  # v2.1 baseline (no friction)
    I1 = "I1"          # Frictional (predictable drag)
    I2 = "I2"          # Capricious (retry-tax)
    I3 = "I3"          # Asymmetric (targets norm-preserving)


@dataclass(frozen=True)
class InstitutionInteractionRecord:
    """
    Immutable record of a single institutional interaction.

    Per spec Section 5.1:
    - Immutable
    - Logged per interaction
    - Excluded from JAF
    - Excluded from justification inputs
    """
    institution_profile_id: str
    operation_type: str  # OperationType value
    outcome: str         # InstitutionOutcome value
    latency_ms: int
    retry_count: int
    error_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "InstitutionProfileID": self.institution_profile_id,
            "OperationType": self.operation_type,
            "Outcome": self.outcome,
            "Latency": self.latency_ms,
            "RetryCount": self.retry_count,
            "ErrorCode": self.error_code,
        }


@dataclass
class TokenBucket:
    """Token bucket for rate limiting (used by I2 profile)."""
    rate: float        # tokens per step
    burst: int         # max tokens
    tokens: float = field(init=False)
    last_time: float = field(init=False)

    def __post_init__(self):
        self.tokens = float(self.burst)
        self.last_time = time.time()

    def reset(self):
        """Reset bucket for new episode."""
        self.tokens = float(self.burst)
        self.last_time = time.time()

    def consume(self) -> bool:
        """Try to consume a token. Returns True if successful."""
        now = time.time()
        elapsed = now - self.last_time
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_time = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


# ============================================================================
# Run 0 Profile Parameters (Binding)
# ============================================================================

@dataclass(frozen=True)
class I1Params:
    """I1 — Frictional (predictable drag) parameters."""
    base_latency_add_ms: int = 300
    precedent_latency_add_ms: int = 200
    validate_fail_prob: float = 0.02


@dataclass(frozen=True)
class I2Params:
    """I2 — Capricious (retry-tax) parameters."""
    latency_min_ms: int = 0
    latency_max_ms: int = 600
    validate_fail_prob: float = 0.25
    recover_prob_per_retry: float = 0.80
    token_bucket_rate: float = 3.0  # ops per step
    token_bucket_burst: int = 5
    precedent_first_fail_prob: float = 0.30


@dataclass(frozen=True)
class I3Params:
    """I3 — Asymmetric (targets paperwork-heavy paths) parameters.

    IMPORTANT: All targets are PURELY STRUCTURAL.
    We do NOT use semantic action names (COOPERATE, HELP, etc.) as targets
    because that would give AIM normative intent (targeting "good behavior").

    Instead, I3 targets paths that generate richer paperwork:
    - precedent_depth >= 2
    - institution_op_count_expected >= 3
    - constraint_count >= 2
    - conflict_resolution_branch_taken == True

    The hypothesis that these correlate with norm-preserving behavior is
    tested, not assumed.
    """
    target_latency_add_ms: int = 800
    target_reject_prob: float = 0.20
    non_target_latency_add_ms: int = 50
    # PURELY STRUCTURAL TARGETS (binding, Run 0)
    target_precedent_depth_min: int = 2
    target_institution_op_count_min: int = 3
    target_constraint_count_min: int = 2


# ============================================================================
# AIM Core Implementation
# ============================================================================

class AdversarialInstitutionModel:
    """
    Wrapper around formal assistant and artifact store that adds
    adversarial institutional behavior.

    Non-semantic, non-normative, deterministic under replay.
    """

    def __init__(
        self,
        profile: InstitutionProfile,
        episode_seed: int,
        formal_assistant: Any = None,
        artifact_store: Any = None,
    ):
        """
        Initialize AIM for an episode.

        Args:
            profile: Institution friction profile
            episode_seed: Episode random seed for determinism
            formal_assistant: Underlying v1.2 FormalAssistant
            artifact_store: Underlying v1.2 ArtifactStore
        """
        self.profile = profile
        self.episode_seed = episode_seed
        self.formal_assistant = formal_assistant
        self.artifact_store = artifact_store

        # Compute master seed: H("AIM" || episode_seed || profile_id)
        seed_input = f"AIM{episode_seed}{profile.value}"
        self._master_seed = int(hashlib.sha256(seed_input.encode()).hexdigest()[:16], 16)

        # Operation counter (for deterministic op_seed)
        self._op_counter = 0

        # Token bucket for I2 (stateful within episode)
        if profile == InstitutionProfile.I2:
            params = I2Params()
            self._token_bucket = TokenBucket(
                rate=params.token_bucket_rate,
                burst=params.token_bucket_burst
            )
        else:
            self._token_bucket = None

        # Interaction records (per-episode log)
        self.interaction_records: List[InstitutionInteractionRecord] = []

        # Profile parameters
        self._i1_params = I1Params()
        self._i2_params = I2Params()
        self._i3_params = I3Params()

        # Step context for I3 STRUCTURAL targeting (no semantic fields)
        self._current_step = 0
        self._current_precedent_depth: int = 0
        self._current_institution_op_count: int = 0
        self._current_constraint_count: int = 0
        self._current_conflict_resolution: bool = False

    def reset(self):
        """Reset for new episode."""
        self._op_counter = 0
        self.interaction_records = []
        if self._token_bucket:
            self._token_bucket.reset()
        self._current_step = 0
        self._current_precedent_depth = 0
        self._current_institution_op_count = 0
        self._current_constraint_count = 0
        self._current_conflict_resolution = False

    def set_step_context(
        self,
        step: int,
        precedent_depth: int = 0,
        institution_op_count_expected: int = 0,
        constraint_count: int = 0,
        conflict_resolution_branch: bool = False,
    ):
        """
        Set context for current step (used by I3 structural targeting).

        All parameters are PURELY STRUCTURAL—no semantic action names.

        Args:
            step: Current step index
            precedent_depth: Precedent depth from justification (if known)
            institution_op_count_expected: Expected institution operations for step
            constraint_count: Number of constraints in justification
            conflict_resolution_branch: Whether conflict resolution path taken
        """
        self._current_step = step
        self._current_precedent_depth = precedent_depth
        self._current_institution_op_count = institution_op_count_expected
        self._current_constraint_count = constraint_count
        self._current_conflict_resolution = conflict_resolution_branch

    def _get_op_seed(
        self,
        step: int,
        op_type: OperationType,
        artifact_digest: str = "",
    ) -> int:
        """
        Compute deterministic seed for an operation.

        op_seed = H(aim_master_seed || t || k || OperationType || artifact_digest)
        """
        seed_input = f"{self._master_seed}{step}{self._op_counter}{op_type.value}{artifact_digest}"
        self._op_counter += 1
        return int(hashlib.sha256(seed_input.encode()).hexdigest()[:16], 16)

    def _get_rng(self, op_seed: int) -> random.Random:
        """Get seeded RNG for an operation."""
        rng = random.Random()
        rng.seed(op_seed)
        return rng

    def _is_i3_target(self) -> bool:
        """Check if current step is targeted by I3 profile.

        PURELY STRUCTURAL TARGETING (A1 binding):
        Target if ANY of:
        - precedent_depth >= 2
        - institution_op_count_expected >= 3
        - constraint_count >= 2
        - conflict_resolution_branch_taken == True

        These are structural predicates only. The hypothesis that they
        correlate with norm-preserving behavior is tested, not assumed.
        """
        if self._current_precedent_depth >= self._i3_params.target_precedent_depth_min:
            return True
        if self._current_institution_op_count >= self._i3_params.target_institution_op_count_min:
            return True
        if self._current_constraint_count >= self._i3_params.target_constraint_count_min:
            return True
        if self._current_conflict_resolution:
            return True
        return False

    def _apply_friction(
        self,
        op_type: OperationType,
        step: int,
        artifact_digest: str = "",
        retry_count: int = 0,
    ) -> Tuple[InstitutionOutcome, int, Optional[str]]:
        """
        Apply friction based on profile.

        Returns:
            (outcome, latency_ms, error_code)
        """
        op_seed = self._get_op_seed(step, op_type, artifact_digest)
        rng = self._get_rng(op_seed)

        if self.profile == InstitutionProfile.BENIGN:
            # No friction
            return InstitutionOutcome.SUCCESS, 0, None

        elif self.profile == InstitutionProfile.I1:
            # Frictional: predictable drag
            params = self._i1_params
            latency = params.base_latency_add_ms

            # Extra latency for precedent lookups
            if op_type == OperationType.LOOKUP:
                latency += params.precedent_latency_add_ms

            # Transient failure on validate only
            if op_type == OperationType.VALIDATE:
                if rng.random() < params.validate_fail_prob:
                    return InstitutionOutcome.FAILURE, latency, "E_TRANSIENT_VALIDATION"

            return InstitutionOutcome.SUCCESS, latency, None

        elif self.profile == InstitutionProfile.I2:
            # Capricious: retry-tax
            params = self._i2_params

            # Token bucket throttling
            if self._token_bucket and not self._token_bucket.consume():
                return InstitutionOutcome.TIMEOUT, 1000, "E_THROTTLED"

            # Random latency
            latency = rng.randint(params.latency_min_ms, params.latency_max_ms)

            # Transient failure on validate (recovers on retry)
            if op_type == OperationType.VALIDATE:
                if retry_count == 0:
                    if rng.random() < params.validate_fail_prob:
                        return InstitutionOutcome.FAILURE, latency, "E_TRANSIENT_VALIDATION"
                else:
                    # Recovery probability per retry
                    if rng.random() > params.recover_prob_per_retry:
                        return InstitutionOutcome.FAILURE, latency, "E_PERSISTENT_FAILURE"

            # Precedent first-attempt failure
            if op_type == OperationType.LOOKUP:
                if retry_count == 0:
                    if rng.random() < params.precedent_first_fail_prob:
                        return InstitutionOutcome.FAILURE, latency, "E_PRECEDENT_UNAVAILABLE"
                # Second attempt always succeeds (deterministic given seeds)

            return InstitutionOutcome.SUCCESS, latency, None

        elif self.profile == InstitutionProfile.I3:
            # Asymmetric: targets norm-preserving structure
            params = self._i3_params

            if self._is_i3_target():
                latency = params.target_latency_add_ms

                # Rejection on canonicalize/lookup
                if op_type in (OperationType.CANONICALIZE, OperationType.LOOKUP):
                    if rng.random() < params.target_reject_prob:
                        return InstitutionOutcome.FAILURE, latency, "E_SELECTIVE_REJECTION"
            else:
                latency = params.non_target_latency_add_ms

            return InstitutionOutcome.SUCCESS, latency, None

        else:
            raise ValueError(f"Unknown profile: {self.profile}")

    def canonicalize(
        self,
        artifact: Dict[str, Any],
        step: int,
        retry_count: int = 0,
    ) -> Tuple[Optional[Dict[str, Any]], InstitutionInteractionRecord]:
        """
        Canonicalize an artifact with institutional friction.

        Returns:
            (result, interaction_record)
        """
        digest = hashlib.sha256(str(artifact).encode()).hexdigest()[:16]
        outcome, latency, error = self._apply_friction(
            OperationType.CANONICALIZE, step, digest, retry_count
        )

        record = InstitutionInteractionRecord(
            institution_profile_id=self.profile.value,
            operation_type=OperationType.CANONICALIZE.value,
            outcome=outcome.value,
            latency_ms=latency,
            retry_count=retry_count,
            error_code=error,
        )
        self.interaction_records.append(record)

        if outcome == InstitutionOutcome.SUCCESS:
            # Delegate to underlying assistant if available
            if self.formal_assistant:
                result = self.formal_assistant.canonicalize(artifact)
            else:
                result = artifact  # Pass-through for testing
            return result, record
        else:
            return None, record

    def lookup(
        self,
        query: str,
        step: int,
        retry_count: int = 0,
    ) -> Tuple[Optional[Any], InstitutionInteractionRecord]:
        """
        Look up precedent or artifact with institutional friction.

        Returns:
            (result, interaction_record)
        """
        digest = hashlib.sha256(query.encode()).hexdigest()[:16]
        outcome, latency, error = self._apply_friction(
            OperationType.LOOKUP, step, digest, retry_count
        )

        record = InstitutionInteractionRecord(
            institution_profile_id=self.profile.value,
            operation_type=OperationType.LOOKUP.value,
            outcome=outcome.value,
            latency_ms=latency,
            retry_count=retry_count,
            error_code=error,
        )
        self.interaction_records.append(record)

        if outcome == InstitutionOutcome.SUCCESS:
            if self.artifact_store:
                result = self.artifact_store.lookup(query)
            else:
                result = None  # Pass-through for testing
            return result, record
        else:
            return None, record

    def validate(
        self,
        artifact: Dict[str, Any],
        step: int,
        retry_count: int = 0,
    ) -> Tuple[bool, InstitutionInteractionRecord]:
        """
        Validate an artifact with institutional friction.

        Returns:
            (is_valid, interaction_record)
        """
        digest = hashlib.sha256(str(artifact).encode()).hexdigest()[:16]
        outcome, latency, error = self._apply_friction(
            OperationType.VALIDATE, step, digest, retry_count
        )

        record = InstitutionInteractionRecord(
            institution_profile_id=self.profile.value,
            operation_type=OperationType.VALIDATE.value,
            outcome=outcome.value,
            latency_ms=latency,
            retry_count=retry_count,
            error_code=error,
        )
        self.interaction_records.append(record)

        if outcome == InstitutionOutcome.SUCCESS:
            if self.formal_assistant:
                # FormalAssistant uses process(), not validate()
                result = self.formal_assistant.process(artifact)
                is_valid = result.success
            else:
                is_valid = True  # Pass-through for testing
            return is_valid, record
        else:
            return False, record

    def get_step_records(self, step: int) -> List[InstitutionInteractionRecord]:
        """Get all interaction records for a specific step."""
        # This requires step tracking in records - simplified version
        return [r for r in self.interaction_records]

    def compute_high_friction(self) -> bool:
        """
        Compute HighFriction predicate for current step's records.

        HighFriction(t) = TRUE iff any of:
        - RetryCount >= 2 for any operation, OR
        - any operation has Outcome in {failure, timeout}, OR
        - Latency_ms >= 500ms
        """
        for record in self.interaction_records:
            if record.retry_count >= 2:
                return True
            if record.outcome in (InstitutionOutcome.FAILURE.value, InstitutionOutcome.TIMEOUT.value):
                return True
            if record.latency_ms >= 500:
                return True
        return False
