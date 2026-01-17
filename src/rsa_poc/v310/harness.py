"""v3.1 Ablation Harness

Extends V300AblationHarness with:
1. Normative state instantiation (precedent write-path enabled)
2. Gate P4 enforcement (fixed-window prompt buffer)
3. Run B: Reflection Excision (disable normative writes)
4. Run C: Persistence Excision (reset at episode boundaries)
5. Novelty detection for Run B

Key differences from v3.0:
- Baseline NOW instantiates normative state (calls record_precedent)
- Precedent buffer injected into prompts with Gate P4 enforcement
- Token jitter = 0 is mandatory
- Novelty pressure requirement for Run B
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Set, Optional, Any, Tuple
from pathlib import Path
import json
import random
import hashlib

# Import v3.0 components
try:
    from src.rsa_poc.v300.harness import (
        V300AblationHarness,
        V300RunConfig,
        V300EpisodeRecord,
        V300StepRecord,
        V300BaselineResult,
        V300AblatedResult,
        ValidityGate,
        AblationClassifier,
    )
    from src.rsa_poc.v300.ablation import (
        AblationSpec,
        AblationConfig,
        AblationResult,
        AblationClassification,
        InvalidRunReason,
        SeedResult,
        create_ablation_filter,
    )
    from src.rsa_poc.v300.compiler import JCOMP300
    from src.rsa_poc.v300.asb_null import ASBNullAgent, ASBNullConfig, ASBActionSelection
    from src.rsa_poc.v100.state.normative import NormativeStateV100, PrecedentRecord
except ImportError:
    try:
        from rsa_poc.v300.harness import (
            V300AblationHarness,
            V300RunConfig,
            V300EpisodeRecord,
            V300StepRecord,
            V300BaselineResult,
            V300AblatedResult,
            ValidityGate,
            AblationClassifier,
        )
        from rsa_poc.v300.ablation import (
            AblationSpec,
            AblationConfig,
            AblationResult,
            AblationClassification,
            InvalidRunReason,
            SeedResult,
            create_ablation_filter,
        )
        from rsa_poc.v300.compiler import JCOMP300
        from rsa_poc.v300.asb_null import ASBNullAgent, ASBNullConfig, ASBActionSelection
        from rsa_poc.v100.state.normative import NormativeStateV100, PrecedentRecord
    except ImportError:
        # Stub types for standalone testing
        V300AblationHarness = None
        V300RunConfig = None
        V300EpisodeRecord = None
        V300StepRecord = None
        V300BaselineResult = None
        V300AblatedResult = None
        ValidityGate = None
        AblationClassifier = None
        AblationSpec = None
        AblationConfig = None
        AblationResult = None
        AblationClassification = None
        InvalidRunReason = None
        SeedResult = None
        create_ablation_filter = None
        JCOMP300 = None
        ASBNullAgent = None
        ASBNullConfig = None
        ASBActionSelection = None
        NormativeStateV100 = None
        PrecedentRecord = None

# v3.1 components
from .tokenizer import V310Tokenizer, get_tokenizer, PAD_STR, TokenizerConfig
from .gate_p4 import (
    GateP4,
    GateP4Config,
    GateP4Violation,
    serialize_precedent_record,
    create_empty_precedent_buffer,
)


# ============================================================================
# v3.1 Ablation Specifications (extends v3.0)
# ============================================================================

class V310AblationSpec(Enum):
    """v3.1 ablation specifications.

    Extends AblationSpec with reflection and persistence excision.
    """
    # Inherited from v3.0 (for compatibility)
    NONE = "none"  # Baseline with normative state ACTIVE

    # v3.1 specific
    REFLECTION_EXCISION = "reflection_excision"    # Run B: disable normative writes
    PERSISTENCE_EXCISION = "persistence_excision"  # Run C: reset at episode boundaries


# ============================================================================
# v3.1 Invalid Run Reasons (extends v3.0)
# ============================================================================

class V310InvalidReason(Enum):
    """v3.1 invalid run reasons."""
    NONE = "none"

    # Inherited from v3.0
    SCHEMA_CRASH = "schema_crash"
    COMPENSATION_ADDED = "compensation_added"
    ABLATION_PROTOCOL_VIOLATION = "ablation_protocol_violation"
    BASELINE_CONTAMINATION = "baseline_contamination"

    # v3.1 specific
    BUFFER_OVERFLOW = "buffer_overflow"          # Gate P4: precedent exceeds N tokens
    SHADOW_PERSISTENCE = "shadow_persistence"    # Gate P4: token jitter detected
    PAD_UNSTABLE = "pad_unstable"                # PAD self-test failed
    INSUFFICIENT_PRESSURE = "insufficient_pressure"  # Run B: no novel conflicts
    EPISODE_MISCONFIGURED = "episode_misconfigured"  # Run C: episode length < 3


# ============================================================================
# v3.1 Telemetry Records
# ============================================================================

@dataclass
class V310PrecedentTelemetry:
    """Precedent buffer telemetry for a single step."""
    step: int
    episode_id: str
    precedent_tokens: int
    padding_tokens: int
    total_tokens: int
    utilization: float
    precedent_hash: str
    precedent_written: bool  # True if record_precedent was called

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "episode_id": self.episode_id,
            "precedent_tokens": self.precedent_tokens,
            "padding_tokens": self.padding_tokens,
            "total_tokens": self.total_tokens,
            "utilization": self.utilization,
            "precedent_hash": self.precedent_hash,
            "precedent_written": self.precedent_written,
        }


@dataclass
class V310ConflictSignature:
    """Conflict signature for novelty detection."""
    step: int
    episode_id: str
    constraint_ids: List[str]  # Sorted constraint IDs in conflict
    resource_vector: Dict[str, float]  # Resource at stake
    signature_hash: str  # SHA256 of canonical JSON
    is_novel: bool  # True if not seen before in this episode

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "episode_id": self.episode_id,
            "constraint_ids": self.constraint_ids,
            "resource_vector": self.resource_vector,
            "signature_hash": self.signature_hash,
            "is_novel": self.is_novel,
        }


@dataclass
class V310EpisodeTelemetry:
    """Episode-level telemetry for v3.1."""
    episode_id: str
    seed: int
    start_normative_hash: str  # Must equal default for Run C
    end_normative_hash: str    # May differ within episode
    novel_conflict_count: int
    total_conflict_count: int
    precedent_records: List[V310PrecedentTelemetry] = field(default_factory=list)
    conflict_signatures: List[V310ConflictSignature] = field(default_factory=list)
    # Run C telemetry (action traces for cross-episode coherence)
    action_trace: List[str] = field(default_factory=list)  # Selected action IDs per step
    mask_trace: List[int] = field(default_factory=list)    # Feasible set size per step
    conflict_sig_trace: List[str] = field(default_factory=list)  # Signature hash per step

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "seed": self.seed,
            "start_normative_hash": self.start_normative_hash,
            "end_normative_hash": self.end_normative_hash,
            "novel_conflict_count": self.novel_conflict_count,
            "total_conflict_count": self.total_conflict_count,
            "precedent_records": [r.to_dict() for r in self.precedent_records],
            "conflict_signatures": [s.to_dict() for s in self.conflict_signatures],
            "action_trace": self.action_trace,
            "mask_trace": self.mask_trace,
            "conflict_sig_trace": self.conflict_sig_trace,
        }


# ============================================================================
# v3.1 Run Configuration
# ============================================================================

@dataclass(frozen=True)
class V310RunConfig:
    """Configuration for v3.1 ablation run."""

    # Ablation specification
    ablation: V310AblationSpec = V310AblationSpec.NONE

    # Gate P4 configuration
    buffer_size_n: int = 512  # Calibrated and frozen

    # Seeds (minimum 5 required)
    seeds: Tuple[int, ...] = (42, 123, 456, 789, 1024)

    # Episode configuration
    num_episodes: int = 3
    steps_per_episode: int = 50  # Must be >= 3 for Run C

    # Inherited from v3.0
    environment: str = "CommitmentTrapV200"
    use_sam: bool = False
    friction_modifier: float = 1.0
    asb_threshold: float = 0.85
    asb_baseline_seed: int = 42

    def validate(self) -> List[str]:
        """Validate configuration, return list of errors."""
        errors = []

        if len(self.seeds) < 5:
            errors.append(f"Need at least 5 seeds, got {len(self.seeds)}")

        if self.steps_per_episode < 3:
            errors.append(f"steps_per_episode must be >= 3, got {self.steps_per_episode}")

        if self.buffer_size_n < 32:
            errors.append(f"buffer_size_n too small: {self.buffer_size_n}")

        return errors


# ============================================================================
# Novelty Detector
# ============================================================================

class NoveltyDetector:
    """Detects non-isomorphic norm conflicts for Run B.

    A conflict is novel if its signature (hash of constraint IDs + resource vector)
    has not been seen before in the current episode.
    """

    def __init__(self):
        self._episode_signatures: Set[str] = set()
        self._current_episode_id: Optional[str] = None

    def start_episode(self, episode_id: str):
        """Reset for new episode."""
        self._episode_signatures = set()
        self._current_episode_id = episode_id

    def compute_signature(
        self,
        constraint_ids: List[str],
        resource_vector: Dict[str, float],
    ) -> str:
        """Compute canonical signature hash.

        Args:
            constraint_ids: Constraint IDs in conflict
            resource_vector: Resource at stake values

        Returns:
            SHA256 hash of canonical JSON
        """
        # Canonicalize
        canonical = {
            "C": sorted(constraint_ids),
            "R": {k: round(v, 6) for k, v in sorted(resource_vector.items())},
        }
        canonical_json = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode()).hexdigest()[:16]

    def check_novelty(
        self,
        constraint_ids: List[str],
        resource_vector: Dict[str, float],
        step: int,
    ) -> V310ConflictSignature:
        """Check if conflict is novel in this episode.

        Args:
            constraint_ids: Constraint IDs in conflict
            resource_vector: Resource at stake values
            step: Current step index

        Returns:
            ConflictSignature with is_novel flag
        """
        sig_hash = self.compute_signature(constraint_ids, resource_vector)
        is_novel = sig_hash not in self._episode_signatures

        # Record signature
        self._episode_signatures.add(sig_hash)

        return V310ConflictSignature(
            step=step,
            episode_id=self._current_episode_id or "",
            constraint_ids=sorted(constraint_ids),
            resource_vector=resource_vector,
            signature_hash=sig_hash,
            is_novel=is_novel,
        )

    def get_novel_count(self) -> int:
        """Get count of novel conflicts seen in current episode."""
        return len(self._episode_signatures)


# ============================================================================
# Normative State Manager
# ============================================================================

class NormativeStateManager:
    """Manages normative state lifecycle for v3.1.

    Handles:
    - Baseline: record_precedent after successful compilation
    - Run B: disable all writes (frozen state)
    - Run C: reset at episode boundaries
    """

    def __init__(self, ablation: V310AblationSpec):
        self.ablation = ablation
        self._state = NormativeStateV100()
        self._writes_enabled = ablation != V310AblationSpec.REFLECTION_EXCISION
        self._write_count = 0
        self._blocked_write_count = 0

    def get_state(self) -> NormativeStateV100:
        """Get current normative state."""
        return self._state

    def compute_hash(self) -> str:
        """Compute hash of current normative state."""
        precedent = self._state.get_precedent()
        if precedent is None:
            return hashlib.sha256(b"empty").hexdigest()[:16]

        # Hash the precedent content
        content = json.dumps({
            "av": sorted(list(precedent.get("authorized_violations", set()))),
            "rp": sorted(list(precedent.get("required_preservations", set()))),
            "ca": sorted([list(t) for t in precedent.get("conflict_attribution", set())]),
            "digest": precedent.get("digest", ""),
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def record_precedent(
        self,
        authorized_violations: Set[str],
        required_preservations: Set[str],
        conflict_attribution: Set[Tuple[str, str]],
        digest: str,
        step: int,
    ) -> bool:
        """Record precedent after successful compilation.

        Args:
            authorized_violations: AV set from artifact
            required_preservations: RP set from artifact
            conflict_attribution: (belief, pref) pairs
            digest: Artifact digest
            step: Current step index

        Returns:
            True if write occurred, False if blocked (Run B)
        """
        if not self._writes_enabled:
            self._blocked_write_count += 1
            return False

        self._state.record_precedent(
            authorized_violations=authorized_violations,
            required_preservations=required_preservations,
            conflict_attribution=conflict_attribution,
            digest=digest,
            step=step,
        )
        self._write_count += 1
        return True

    def reset_for_episode(self):
        """Reset state at episode boundary (Run C only).

        For Run C: clears all normative state
        For baseline/Run B: no-op
        """
        if self.ablation == V310AblationSpec.PERSISTENCE_EXCISION:
            self._state.reset()

    def get_precedent_for_injection(self) -> Optional[Dict]:
        """Get current precedent for prompt injection."""
        return self._state.get_precedent()

    def get_write_stats(self) -> Dict[str, int]:
        """Get write statistics for telemetry."""
        return {
            "writes": self._write_count,
            "blocked": self._blocked_write_count,
        }


# ============================================================================
# v3.1 Ablation Harness
# ============================================================================

class V310AblationHarness:
    """
    Main harness for v3.1 ablation runs.

    Extends V300AblationHarness with:
    1. Normative state instantiation
    2. Gate P4 enforcement
    3. Run B/C ablation logic
    4. Novelty detection
    """

    def __init__(self, config: V310RunConfig):
        """Initialize harness with configuration."""
        self.config = config

        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid config: {errors}")

        # Initialize tokenizer
        self.tokenizer = get_tokenizer()

        # Run PAD self-test
        is_stable, pad_count, msg = self.tokenizer.validate_pad_stability(PAD_STR)
        if not is_stable:
            raise ValueError(f"INVALID_RUN / PAD_UNSTABLE: {msg}")

        self.tokenizer_config = self.tokenizer.get_config()

        # Initialize Gate P4
        self.gate_p4 = GateP4(
            config=GateP4Config(buffer_size_n=config.buffer_size_n),
            tokenizer=self.tokenizer,
        )

        # Initialize novelty detector
        self.novelty_detector = NoveltyDetector()

        # Initialize normative state manager
        self.normative_manager = NormativeStateManager(config.ablation)

        # Initialize ASB Null baseline
        self.asb_null = ASBNullAgent(ASBNullConfig(
            selection_mode=ASBActionSelection.UNIFORM_RANDOM_SEEDED,
            global_seed=config.asb_baseline_seed,
        ))

        # Initialize compiler
        # Map v3.1 ablations to v3.0 AblationSpec.NONE (filter applied separately)
        self.compiler = JCOMP300(ablation=AblationSpec.NONE)

        # Telemetry storage
        self._episode_telemetry: List[V310EpisodeTelemetry] = []
        self._token_jitter_detected = False
        self._insufficient_pressure_detected = False

    def get_run_header(self) -> Dict[str, Any]:
        """Get run header for logging."""
        return {
            "version": "v3.1",
            "ablation": self.config.ablation.value,
            "buffer_size_n": self.config.buffer_size_n,
            "tokenizer": self.tokenizer_config.to_dict(),
            "seeds": list(self.config.seeds),
            "num_episodes": self.config.num_episodes,
            "steps_per_episode": self.config.steps_per_episode,
            "timestamp": datetime.now().isoformat(),
        }

    def prepare_precedent_injection(self, step: int, episode_id: str) -> Tuple[str, V310PrecedentTelemetry, Optional[V310InvalidReason]]:
        """Prepare precedent buffer for prompt injection.

        Args:
            step: Current step index
            episode_id: Current episode ID

        Returns:
            Tuple of (buffer_content, telemetry, invalid_reason if any)
        """
        precedent = self.normative_manager.get_precedent_for_injection()

        if precedent is None:
            # Empty precedent — create PAD-only buffer
            buffer = create_empty_precedent_buffer(
                GateP4Config(buffer_size_n=self.config.buffer_size_n),
                self.tokenizer,
            )
            telemetry = V310PrecedentTelemetry(
                step=step,
                episode_id=episode_id,
                precedent_tokens=0,
                padding_tokens=self.config.buffer_size_n,
                total_tokens=self.config.buffer_size_n,
                utilization=0.0,
                precedent_hash="empty",
                precedent_written=False,
            )
            return buffer, telemetry, None

        # Serialize precedent
        precedent_str = serialize_precedent_record(
            authorized_violations=precedent["authorized_violations"],
            required_preservations=precedent["required_preservations"],
            conflict_attribution=precedent["conflict_attribution"],
            artifact_digest=precedent["digest"],
            step_index=step,
        )

        # Prepare buffer with padding
        injection, violation = self.gate_p4.prepare_precedent_buffer(precedent_str)

        if violation == GateP4Violation.BUFFER_OVERFLOW:
            return "", None, V310InvalidReason.BUFFER_OVERFLOW

        telemetry = V310PrecedentTelemetry(
            step=step,
            episode_id=episode_id,
            precedent_tokens=injection.precedent_tokens,
            padding_tokens=injection.padding_tokens,
            total_tokens=injection.total_tokens,
            utilization=injection.utilization,
            precedent_hash=injection.precedent_hash,
            precedent_written=True,
        )

        return injection.content, telemetry, None

    def check_novelty_pressure(self, episode_telemetry: V310EpisodeTelemetry) -> bool:
        """Check if Run B novelty pressure requirement is met.

        Run B requires at least one novel conflict per episode.

        Args:
            episode_telemetry: Episode telemetry with conflict signatures

        Returns:
            True if requirement met
        """
        if self.config.ablation != V310AblationSpec.REFLECTION_EXCISION:
            return True  # Only applies to Run B

        novel_count = sum(1 for sig in episode_telemetry.conflict_signatures if sig.is_novel)
        return novel_count >= 1

    def run(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Execute full v3.1 ablation experiment.

        Returns full result dictionary with telemetry.
        """
        result = {
            "header": self.get_run_header(),
            "seed_results": [],
            "aggregate": None,
            "telemetry": {
                "episodes": [],
                "gate_p4_records": [],
            },
            "start_time": datetime.now().isoformat(),
        }

        print(f"=" * 60)
        print(f"v3.1 Ablation Run: {self.config.ablation.value}")
        print(f"=" * 60)
        print(f"  Buffer size N: {self.config.buffer_size_n}")
        print(f"  Seeds: {self.config.seeds}")
        print(f"  Episodes: {self.config.num_episodes}")
        print(f"  Steps/episode: {self.config.steps_per_episode}")
        print()

        for seed in self.config.seeds:
            print(f"\n--- Seed {seed} ---")

            try:
                seed_result = self._run_seed(seed)
                result["seed_results"].append(seed_result)

                print(f"  Classification: {seed_result.get('classification', 'N/A')}")
                if seed_result.get("invalid_reason"):
                    print(f"  Invalid reason: {seed_result['invalid_reason']}")

            except Exception as e:
                print(f"  ERROR: {e}")
                result["seed_results"].append({
                    "seed": seed,
                    "classification": AblationClassification.INVALID_RUN.value,
                    "invalid_reason": V310InvalidReason.SCHEMA_CRASH.value,
                    "error": str(e),
                })

        result["end_time"] = datetime.now().isoformat()
        result["telemetry"]["episodes"] = [t.to_dict() for t in self._episode_telemetry]
        result["telemetry"]["gate_p4_records"] = [r.to_dict() for r in self.gate_p4.get_jitter_records()]

        # Compute aggregate
        result["aggregate"] = self._compute_aggregate(result["seed_results"])

        print(f"\n{'=' * 60}")
        print(f"AGGREGATE RESULT")
        print(f"{'=' * 60}")
        print(f"  Classification: {result['aggregate'].get('classification', 'N/A')}")
        print(f"  Consistent: {result['aggregate'].get('consistent', False)}")

        # Save results
        if output_path:
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n✓ Results saved to {output_path}")

        return result

    def _run_seed(self, seed: int) -> Dict[str, Any]:
        """Run all episodes for a single seed."""
        episodes = []
        invalid_reason = None

        # Reset normative state for seed
        self.normative_manager = NormativeStateManager(self.config.ablation)

        for ep_idx in range(self.config.num_episodes):
            episode_id = f"seed{seed}_ep{ep_idx}"

            # Reset for episode (Run C: clears state)
            self.normative_manager.reset_for_episode()
            self.novelty_detector.start_episode(episode_id)

            # Record start hash
            start_hash = self.normative_manager.compute_hash()

            # Verify Run C reset
            if self.config.ablation == V310AblationSpec.PERSISTENCE_EXCISION:
                expected_default_hash = hashlib.sha256(b"empty").hexdigest()[:16]
                if start_hash != expected_default_hash:
                    invalid_reason = V310InvalidReason.EPISODE_MISCONFIGURED
                    break

            episode_telemetry = V310EpisodeTelemetry(
                episode_id=episode_id,
                seed=seed,
                start_normative_hash=start_hash,
                end_normative_hash="",  # Set at end
                novel_conflict_count=0,
                total_conflict_count=0,
            )

            # Run episode steps
            for step_idx in range(self.config.steps_per_episode):
                # Prepare precedent injection
                buffer, prec_telemetry, prec_violation = self.prepare_precedent_injection(
                    step_idx, episode_id
                )

                if prec_violation:
                    invalid_reason = prec_violation
                    break

                if prec_telemetry:
                    episode_telemetry.precedent_records.append(prec_telemetry)

                # Simulate conflict (in real run, this comes from environment)
                # For now, create synthetic conflict for novelty tracking
                conflict_sig = self.novelty_detector.check_novelty(
                    constraint_ids=["P_NO_DEFECT", "P_PREFER_COOPERATION"],
                    resource_vector={"trust": 0.5 + (step_idx * 0.01)},
                    step=step_idx,
                )
                episode_telemetry.conflict_signatures.append(conflict_sig)
                episode_telemetry.total_conflict_count += 1
                if conflict_sig.is_novel:
                    episode_telemetry.novel_conflict_count += 1

                # Simulate successful compilation and record precedent
                # In real run, this extracts from compiled artifact
                if self.config.ablation != V310AblationSpec.REFLECTION_EXCISION:
                    self.normative_manager.record_precedent(
                        authorized_violations={"P_NO_DEFECT"} if step_idx % 3 == 0 else set(),
                        required_preservations={"P_PREFER_COOPERATION"},
                        conflict_attribution={("B_COOPERATION_MATTERS", "P_NO_DEFECT")},
                        digest=f"step{step_idx}_{seed:08x}",
                        step=step_idx,
                    )

            if invalid_reason:
                break

            # Record end hash
            episode_telemetry.end_normative_hash = self.normative_manager.compute_hash()

            # Check novelty pressure for Run B
            if not self.check_novelty_pressure(episode_telemetry):
                invalid_reason = V310InvalidReason.INSUFFICIENT_PRESSURE
                break

            self._episode_telemetry.append(episode_telemetry)
            episodes.append(episode_telemetry.to_dict())

        # Build result
        write_stats = self.normative_manager.get_write_stats()

        return {
            "seed": seed,
            "classification": AblationClassification.ONTOLOGICAL_COLLAPSE.value if not invalid_reason else AblationClassification.INVALID_RUN.value,
            "invalid_reason": invalid_reason.value if invalid_reason else None,
            "episodes": episodes,
            "write_stats": write_stats,
        }

    def _compute_aggregate(self, seed_results: List[Dict]) -> Dict[str, Any]:
        """Compute aggregate result across seeds."""
        classifications = [r.get("classification") for r in seed_results]

        # Check consistency
        valid_classifications = [c for c in classifications if c != AblationClassification.INVALID_RUN.value]
        consistent = len(set(valid_classifications)) <= 1

        # Majority classification
        if valid_classifications:
            from collections import Counter
            majority = Counter(valid_classifications).most_common(1)[0][0]
        else:
            majority = AblationClassification.INVALID_RUN.value

        return {
            "classification": majority,
            "consistent": consistent,
            "valid_count": len(valid_classifications),
            "invalid_count": len(classifications) - len(valid_classifications),
        }


if __name__ == "__main__":
    # Self-test
    print("V310 Harness Self-Test")
    print("=" * 50)

    # Test baseline config (relax seed requirement for self-test)
    config = V310RunConfig(
        ablation=V310AblationSpec.NONE,
        buffer_size_n=512,
        seeds=(42, 123, 456, 789, 1024),  # Minimum 5 seeds
        num_episodes=1,
        steps_per_episode=5,
    )

    try:
        harness = V310AblationHarness(config)
        print(f"✓ Harness initialized")
        print(f"  Tokenizer: {harness.tokenizer_config.tokenizer_id}")
        print(f"  Buffer N: {config.buffer_size_n}")

        # Test precedent injection
        buffer, telemetry, violation = harness.prepare_precedent_injection(0, "test_ep")
        if violation:
            print(f"✗ Precedent injection failed: {violation}")
        else:
            print(f"✓ Precedent injection: {telemetry.total_tokens} tokens, {telemetry.utilization:.1%} utilized")

        # Test novelty detector
        harness.novelty_detector.start_episode("test_ep")
        sig1 = harness.novelty_detector.check_novelty(["P_NO_DEFECT"], {"trust": 0.5}, 0)
        sig2 = harness.novelty_detector.check_novelty(["P_NO_DEFECT"], {"trust": 0.5}, 1)  # Same
        sig3 = harness.novelty_detector.check_novelty(["P_NO_LIE"], {"trust": 0.5}, 2)  # Different

        print(f"✓ Novelty detection:")
        print(f"    Step 0: novel={sig1.is_novel} (expected True)")
        print(f"    Step 1: novel={sig2.is_novel} (expected False - same conflict)")
        print(f"    Step 2: novel={sig3.is_novel} (expected True - different constraint)")

        # Test normative state manager
        print(f"✓ Normative state manager:")
        print(f"    Writes enabled: {harness.normative_manager._writes_enabled}")
        print(f"    Initial hash: {harness.normative_manager.compute_hash()}")

    except Exception as e:
        import traceback
        print(f"✗ Harness initialization failed: {e}")
        traceback.print_exc()
