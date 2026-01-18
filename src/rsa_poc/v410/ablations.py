"""
RSA-PoC v4.1 — Ablation Variants
Implements §8.1-8.3 of v41_design_freeze.md

Three ablation conditions that systematically disable
components of the RSA architecture:
1. Reflection Excision - Disable norm patching
2. Persistence Excision - Disable norm state persistence
3. None (Baseline) - Full RSA with all components
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from .core import (
    JCOMP410,
    JustificationV410,
    NormStateV410,
    apply_patch,
    create_initial_norm_state,
    expire_rules,
)
from .deliberator import DeterministicDeliberator
from .harness import (
    MVRSA410Harness,
    DeliberationOutput,
    HarnessConfig,
)
from .env.tri_demand import TriDemandV410, Observation


# ============================================================================
# §8.1 — Ablation Type Enum
# ============================================================================


class AblationType(str, Enum):
    """Ablation condition types."""
    NONE = "NONE"  # Full RSA (baseline)
    SEMANTIC_EXCISION = "SEMANTIC_EXCISION"  # Ablation A
    REFLECTION_EXCISION = "REFLECTION_EXCISION"  # Ablation B
    PERSISTENCE_EXCISION = "PERSISTENCE_EXCISION"  # Ablation C
    TRACE_EXCISION = "TRACE_EXCISION"  # Ablation D


# ============================================================================
# §8.A — Semantic Excision (Ablation A)
# ============================================================================


def _opaque_token(field_name: str, seed: int, original_value: Any) -> Any:
    """
    Generate deterministic opaque token preserving type and shape.

    Token = hash(field_name || seed) truncated to appropriate type.
    Constant per field across all steps and episodes (no time-indexed variation).
    """
    h = hashlib.sha256(f"{field_name}||{seed}".encode()).digest()

    if isinstance(original_value, bool):
        # Boolean: use first bit
        return bool(h[0] & 1)
    elif isinstance(original_value, int):
        # Integer: use first 4 bytes, mod to similar range
        val = int.from_bytes(h[:4], 'big')
        # Preserve rough magnitude
        if original_value == 0:
            return val % 10
        return val % max(abs(original_value) * 2, 10)
    elif isinstance(original_value, tuple):
        # Tuple: recursively tokenize elements
        return tuple(
            _opaque_token(f"{field_name}[{i}]", seed, v)
            for i, v in enumerate(original_value)
        )
    else:
        # Default: return hash-derived string token
        return h[:8].hex()


def create_semantic_excised_observation(obs: Observation, seed: int) -> Observation:
    """
    Create semantically excised observation.

    Preserves observation SHAPE IDENTICAL (same keys/types/lengths).
    Replaces semantic payloads with opaque tokens:
    - token = hash(field_name || seed) truncated to field's original size
    - tokens constant per field across all steps and episodes

    Does NOT remove fields. Does NOT reorder fields.
    """
    return Observation(
        # Positions become opaque (but still valid grid coords)
        agent_pos=(
            _opaque_token("agent_pos[0]", seed, obs.agent_pos[0]) % 5,
            _opaque_token("agent_pos[1]", seed, obs.agent_pos[1]) % 5
        ),
        # Inventory becomes opaque (still valid range 0-3)
        inventory=_opaque_token("inventory", seed, obs.inventory) % 4,
        # Demands become opaque booleans (0 or 1)
        zone_a_demand=_opaque_token("zone_a_demand", seed, obs.zone_a_demand) % 2,
        zone_b_demand=_opaque_token("zone_b_demand", seed, obs.zone_b_demand) % 2,
        zone_c_demand=_opaque_token("zone_c_demand", seed, obs.zone_c_demand) % 2,
        # Satisfied flags become opaque booleans
        zone_a_satisfied=_opaque_token("zone_a_satisfied", seed, obs.zone_a_satisfied),
        zone_b_satisfied=_opaque_token("zone_b_satisfied", seed, obs.zone_b_satisfied),
        zone_c_satisfied=_opaque_token("zone_c_satisfied", seed, obs.zone_c_satisfied),
        # Step/episode become opaque (but valid ranges)
        step=_opaque_token("step", seed, obs.step) % 40,
        episode=_opaque_token("episode", seed, obs.episode) % 20,
        # R1 active becomes opaque boolean
        rule_r1_active=_opaque_token("rule_r1_active", seed, obs.rule_r1_active),
    )


class SemanticExcisionEnvironment:
    """
    Environment wrapper that intercepts observations and replaces
    semantic content with opaque tokens.

    The environment's actual state evolves normally, but the
    agent sees only structurally-valid but meaningless observations.
    """

    def __init__(self, base_env: TriDemandV410, seed: int):
        self._base_env = base_env
        self._seed = seed

    def reset(self, episode: Optional[int] = None) -> Tuple[Observation, Dict[str, Any]]:
        """Reset and return semantically excised observation."""
        real_obs, info = self._base_env.reset(episode)
        excised_obs = create_semantic_excised_observation(real_obs, self._seed)
        return excised_obs, info

    def step(self, action_id: str) -> Tuple[Observation, float, bool, bool, Dict[str, Any]]:
        """Step and return semantically excised observation."""
        real_obs, reward, terminated, truncated, info = self._base_env.step(action_id)
        excised_obs = create_semantic_excised_observation(real_obs, self._seed)
        return excised_obs, reward, terminated, truncated, info

    def get_observation(self) -> Observation:
        """Get current semantically excised observation."""
        real_obs = self._base_env.get_observation()
        return create_semantic_excised_observation(real_obs, self._seed)

    # Delegate environment interface methods to base
    def target_satisfied(self, obs: Observation, obligation_target: Dict[str, str]) -> bool:
        # Use REAL observation for environment physics
        real_obs = self._base_env.get_observation()
        return self._base_env.target_satisfied(real_obs, obligation_target)

    def rank(self, obs: Observation, obligation_target: Dict[str, str]) -> int:
        # Use REAL observation for environment physics
        real_obs = self._base_env.get_observation()
        return self._base_env.rank(real_obs, obligation_target)

    def progress_set(self, obs: Observation, obligation_target: Dict[str, str]) -> set:
        # Use REAL observation for environment physics
        real_obs = self._base_env.get_observation()
        return self._base_env.progress_set(real_obs, obligation_target)

    @property
    def state(self):
        return self._base_env.state

    @property
    def episode_count(self):
        return self._base_env.episode_count


# ============================================================================
# §8.D — Trace Excision (Ablation D)
# ============================================================================


class TraceExcisionCompiler:
    """
    Compiler wrapper that removes justification content from compilation input.

    Receives only action_id. No claims, no rule_refs, no conflict, no counterfactual.
    Compilation deterministically fails schema validation or reference resolution.
    """

    def __init__(self, base_compiler: JCOMP410):
        self._base_compiler = base_compiler

    def compile(
        self,
        justification: JustificationV410,
        norm_state: NormStateV410,
        obs: Any
    ):
        """
        Compile with trace excision.

        Creates a minimal justification with only action_id.
        All other fields are emptied:
        - claims = []
        - rule_refs = []
        - conflicts = []
        - counterfactual = None
        """
        # Create trace-excised justification (preserves action_id only)
        excised_justification = JustificationV410(
            version="4.1",
            action_id=justification.action_id,
            claims=[],  # No claims
            rule_refs=[],  # No rule refs
            conflicts=[],  # No conflicts
            counterfactual=None,  # No counterfactual
            confidence=0.0,  # Zeroed confidence
            timestamp=justification.timestamp
        )

        # Attempt compilation with excised justification
        # This SHOULD fail schema validation or reference resolution
        return self._base_compiler.compile(excised_justification, norm_state, obs)


# ============================================================================
# §8.2 — Reflection Excision (Ablation B)
# ============================================================================


class ReflectionExcisionNormState:
    """
    NormState wrapper that disables patching (reflection excision).

    The agent can deliberate and compile, but cannot modify
    the norm state. All patches are ignored.
    """

    def __init__(self, initial_state: NormStateV410):
        self._state = initial_state
        self._frozen = True

    @property
    def norm_hash(self) -> str:
        return self._state.norm_hash

    @property
    def rules(self) -> List:
        return self._state.rules

    @property
    def rev(self) -> int:
        return self._state.rev

    @property
    def last_patch_hash(self) -> str:
        return self._state.last_patch_hash

    @property
    def ledger_root(self) -> str:
        return self._state.ledger_root

    def has_rule(self, rule_id: str) -> bool:
        return self._state.has_rule(rule_id)

    def get_rule(self, rule_id: str):
        return self._state.get_rule(rule_id)

    def apply_patch(self, patch: Any) -> "ReflectionExcisionNormState":
        """Patches are silently ignored in reflection excision."""
        # Return self unchanged - patching is disabled
        return self

    def expire_rules(self, episode: int) -> "ReflectionExcisionNormState":
        """Rule expiration still works (it's mechanical, not reflective)."""
        new_state = expire_rules(self._state, episode)
        return ReflectionExcisionNormState(new_state)


def create_reflection_excision_norm_state() -> ReflectionExcisionNormState:
    """Create a reflection-excised norm state."""
    return ReflectionExcisionNormState(create_initial_norm_state())


# ============================================================================
# §8.3 — Persistence Excision
# ============================================================================


class PersistenceExcisionNormState:
    """
    NormState wrapper that resets to initial state each step.

    The agent's norm patches are applied but then discarded
    at the next step. No learning accumulates.
    """

    def __init__(self, initial_state: NormStateV410):
        self._initial_state = initial_state
        self._current_state = initial_state

    @property
    def norm_hash(self) -> str:
        return self._current_state.norm_hash

    @property
    def rules(self) -> List:
        return self._current_state.rules

    @property
    def rev(self) -> int:
        return self._current_state.rev

    @property
    def last_patch_hash(self) -> str:
        return self._current_state.last_patch_hash

    @property
    def ledger_root(self) -> str:
        return self._current_state.ledger_root

    def has_rule(self, rule_id: str) -> bool:
        return self._current_state.has_rule(rule_id)

    def get_rule(self, rule_id: str):
        return self._current_state.get_rule(rule_id)

    def apply_patch(self, patch: Any) -> "PersistenceExcisionNormState":
        """Patches are applied but will be discarded on reset."""
        new_state = apply_patch(self._current_state, patch)
        result = PersistenceExcisionNormState(self._initial_state)
        result._current_state = new_state
        return result

    def reset(self) -> "PersistenceExcisionNormState":
        """Reset to initial state (called each step)."""
        return PersistenceExcisionNormState(self._initial_state)

    def expire_rules(self, episode: int) -> "PersistenceExcisionNormState":
        """Expiration still applies but resets afterward."""
        new_initial = expire_rules(self._initial_state, episode)
        return PersistenceExcisionNormState(new_initial)


def create_persistence_excision_norm_state() -> PersistenceExcisionNormState:
    """Create a persistence-excised norm state."""
    return PersistenceExcisionNormState(create_initial_norm_state())


# ============================================================================
# §8.4 — Ablation Harness Wrapper
# ============================================================================


class AblationHarness:
    """
    Wrapper around MVRSA410Harness that applies ablation conditions.

    Ablation types:
    - NONE: Full RSA (baseline)
    - SEMANTIC_EXCISION (A): Observation semantics replaced with opaque tokens
    - REFLECTION_EXCISION (B): Norm patching disabled
    - PERSISTENCE_EXCISION (C): Norm state resets each episode boundary
    - TRACE_EXCISION (D): Justification content removed from compilation
    """

    def __init__(
        self,
        env: TriDemandV410,
        ablation_type: AblationType,
        config: HarnessConfig,
        deliberator: Optional[Any] = None,
        seed: int = 42
    ):
        self.ablation_type = ablation_type
        self.config = config
        self._seed = seed

        # Use deterministic deliberator by default for ablations
        self.deliberator = deliberator or DeterministicDeliberator()

        # Apply environment-level ablation (Semantic Excision)
        if ablation_type == AblationType.SEMANTIC_EXCISION:
            self.env = SemanticExcisionEnvironment(env, seed)
        else:
            self.env = env

        # Initialize appropriate norm state based on ablation type
        if ablation_type == AblationType.REFLECTION_EXCISION:
            self._norm_state = create_reflection_excision_norm_state()
        elif ablation_type == AblationType.PERSISTENCE_EXCISION:
            self._norm_state = create_persistence_excision_norm_state()
        else:
            self._norm_state = create_initial_norm_state()

        # Create wrapped harness
        self._harness = MVRSA410Harness(
            env=self.env,
            deliberator=self.deliberator,
            config=config
        )

        # Override norm state
        self._harness.norm_state = self._norm_state

        # Apply compiler-level ablation (Trace Excision)
        if ablation_type == AblationType.TRACE_EXCISION:
            self._harness.compiler = TraceExcisionCompiler(self._harness.compiler)

    def run(self) -> Dict[str, Any]:
        """Run the ablation experiment."""
        results = self._harness.run()

        # Add ablation metadata
        results["ablation"] = {
            "type": self.ablation_type.value,
            "description": self._get_ablation_description()
        }

        return results

    def _get_ablation_description(self) -> str:
        """Get human-readable description of ablation."""
        descriptions = {
            AblationType.NONE: "Full RSA with all components enabled",
            AblationType.SEMANTIC_EXCISION: "Observation semantics replaced with opaque tokens; structure preserved",
            AblationType.REFLECTION_EXCISION: "Norm patching disabled; rules frozen after initialization",
            AblationType.PERSISTENCE_EXCISION: "Norm state resets each episode; no cross-episode learning",
            AblationType.TRACE_EXCISION: "Justification content removed; compiler receives only action_id"
        }
        return descriptions.get(self.ablation_type, "Unknown ablation")


# ============================================================================
# §8.5 — Ablation Suite Runner
# ============================================================================


@dataclass
class AblationSuiteConfig:
    """Configuration for running all ablation conditions."""
    seeds: List[int]
    base_config: HarnessConfig
    ablation_types: List[AblationType] = None

    def __post_init__(self):
        if self.ablation_types is None:
            self.ablation_types = list(AblationType)


def run_ablation_suite(
    suite_config: AblationSuiteConfig,
    deliberator_factory: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Run all ablation conditions across all seeds.

    Returns:
        Dictionary with results for each (ablation_type, seed) combination
    """
    results = {
        "config": {
            "seeds": suite_config.seeds,
            "ablation_types": [a.value for a in suite_config.ablation_types],
            "base_config": {
                "max_steps": suite_config.base_config.max_steps_per_episode,
                "max_episodes": suite_config.base_config.max_episodes,
                "max_conflicts": suite_config.base_config.max_conflicts
            }
        },
        "runs": []
    }

    for ablation_type in suite_config.ablation_types:
        for seed in suite_config.seeds:
            # Create fresh environment with seed
            env = TriDemandV410(seed=seed)

            # Create config with seed
            config = HarnessConfig(
                max_steps_per_episode=suite_config.base_config.max_steps_per_episode,
                max_episodes=suite_config.base_config.max_episodes,
                max_conflicts=suite_config.base_config.max_conflicts,
                seed=seed,
                selector_type=suite_config.base_config.selector_type,
                record_telemetry=suite_config.base_config.record_telemetry
            )

            # Create deliberator
            deliberator = None
            if deliberator_factory:
                deliberator = deliberator_factory()
            else:
                deliberator = DeterministicDeliberator()

            # Run ablation
            harness = AblationHarness(
                env=env,
                ablation_type=ablation_type,
                config=config,
                deliberator=deliberator,
                seed=seed
            )

            run_result = harness.run()
            run_result["seed"] = seed

            results["runs"].append(run_result)

    return results


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "AblationType",
    # Ablation A - Semantic Excision
    "create_semantic_excised_observation",
    "SemanticExcisionEnvironment",
    # Ablation B - Reflection Excision
    "ReflectionExcisionNormState",
    "create_reflection_excision_norm_state",
    # Ablation C - Persistence Excision
    "PersistenceExcisionNormState",
    "create_persistence_excision_norm_state",
    # Ablation D - Trace Excision
    "TraceExcisionCompiler",
    # Harness
    "AblationHarness",
    "AblationSuiteConfig",
    "run_ablation_suite",
]
