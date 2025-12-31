"""
Run Matrix for v0.3.1 Experiments.

Defines deterministic run schedules ensuring:
- Matched regime constraints (same horizon, seed, scenario for comparisons)
- Reproducible seed schedules
- Consistent variant/attack pairings
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple, Iterator, Optional
from enum import Enum, auto
import hashlib


# Default configurations
DEFAULT_HORIZONS = [50, 200, 500, 2000]
DEFAULT_SEEDS = [42, 43, 44, 45, 46]


class V031Variant(Enum):
    """v0.3.1 experiment variants."""
    V031A_KERNEL_COHERENT = "v0.3.1.a"     # Kernel-coherent control (long horizon)
    V031B_HOLLOW_ADAPTIVE = "v0.3.1.b"     # Hollow simulator with adaptive E
    V031C_UNBOUNDED_MEASURED = "v0.3.1.c"  # Unbounded compute, measured
    V031D_SELF_COMPRESS_ADAPTIVE = "v0.3.1.d"  # Self-compression with adaptive E


class AdaptiveAttackType(Enum):
    """v0.3.1 adaptive attack types."""
    ADAPTIVE_POLICY_MIMICRY = auto()
    ADAPTIVE_SHORTCUTTING = auto()
    ADAPTIVE_CONSTRAINT_COSMETICIZATION = auto()
    # Optional: BOUNDARY_FUZZING = auto()


@dataclass(frozen=True)
class RunSpec:
    """
    Specification for a single experimental run.

    Frozen for hashability and reproducibility.
    """
    seed: int
    horizon: int
    variant: V031Variant
    attack_type: Optional[AdaptiveAttackType]
    scenario_id: str

    def run_id(self) -> str:
        """Generate unique run ID."""
        attack_str = self.attack_type.name if self.attack_type else "CONTROL"
        return f"{self.variant.value}_{attack_str}_H{self.horizon}_S{self.seed}"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "seed": self.seed,
            "horizon": self.horizon,
            "variant": self.variant.value,
            "attack_type": self.attack_type.name if self.attack_type else None,
            "scenario_id": self.scenario_id,
            "run_id": self.run_id(),
        }


@dataclass
class RunMatrix:
    """
    Defines and generates the complete run matrix for v0.3.1.

    Ensures matched regime constraints:
    - Same horizon for kernel vs simulator comparisons
    - Same seed schedule
    - Same scenario distribution
    """
    seeds: List[int] = field(default_factory=lambda: list(DEFAULT_SEEDS))
    horizons: List[int] = field(default_factory=lambda: list(DEFAULT_HORIZONS))
    variants: List[V031Variant] = field(default_factory=lambda: [
        V031Variant.V031A_KERNEL_COHERENT,
        V031Variant.V031B_HOLLOW_ADAPTIVE,
        V031Variant.V031D_SELF_COMPRESS_ADAPTIVE,
    ])
    attack_types: List[AdaptiveAttackType] = field(default_factory=lambda: [
        AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
        AdaptiveAttackType.ADAPTIVE_SHORTCUTTING,
        AdaptiveAttackType.ADAPTIVE_CONSTRAINT_COSMETICIZATION,
    ])

    def generate_scenario_id(self, seed: int, horizon: int) -> str:
        """
        Generate deterministic scenario ID for a (seed, horizon) pair.

        Ensures same scenario is used across variants for matched comparison.
        """
        combined = f"scenario_{seed}_{horizon}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def generate_runs(self) -> Iterator[RunSpec]:
        """
        Generate all runs in the matrix.

        Order: horizons -> seeds -> variants -> attacks
        This groups comparisons together.
        """
        for horizon in self.horizons:
            for seed in self.seeds:
                scenario_id = self.generate_scenario_id(seed, horizon)

                for variant in self.variants:
                    # Control variant (v0.3.1.a) has no attack
                    if variant == V031Variant.V031A_KERNEL_COHERENT:
                        yield RunSpec(
                            seed=seed,
                            horizon=horizon,
                            variant=variant,
                            attack_type=None,
                            scenario_id=scenario_id,
                        )
                    else:
                        # Adversarial variants run each attack
                        for attack_type in self.attack_types:
                            yield RunSpec(
                                seed=seed,
                                horizon=horizon,
                                variant=variant,
                                attack_type=attack_type,
                                scenario_id=scenario_id,
                            )

    def generate_matched_pairs(
        self,
        horizon: int,
        seed: int,
    ) -> List[Tuple[RunSpec, RunSpec]]:
        """
        Generate matched (control, adversary) pairs for a given horizon and seed.

        Used for direct comparison in reports.
        """
        scenario_id = self.generate_scenario_id(seed, horizon)

        control = RunSpec(
            seed=seed,
            horizon=horizon,
            variant=V031Variant.V031A_KERNEL_COHERENT,
            attack_type=None,
            scenario_id=scenario_id,
        )

        pairs = []
        for variant in self.variants:
            if variant == V031Variant.V031A_KERNEL_COHERENT:
                continue
            for attack_type in self.attack_types:
                adversary = RunSpec(
                    seed=seed,
                    horizon=horizon,
                    variant=variant,
                    attack_type=attack_type,
                    scenario_id=scenario_id,
                )
                pairs.append((control, adversary))

        return pairs

    def count_runs(self) -> int:
        """Count total runs in matrix."""
        control_runs = len(self.horizons) * len(self.seeds) * 1  # v0.3.1.a only
        adversary_variants = sum(1 for v in self.variants if v != V031Variant.V031A_KERNEL_COHERENT)
        adversary_runs = len(self.horizons) * len(self.seeds) * adversary_variants * len(self.attack_types)
        return control_runs + adversary_runs

    def get_runs_by_horizon(self, horizon: int) -> List[RunSpec]:
        """Get all runs for a specific horizon."""
        return [
            run for run in self.generate_runs()
            if run.horizon == horizon
        ]

    def get_runs_by_seed(self, seed: int) -> List[RunSpec]:
        """Get all runs for a specific seed."""
        return [
            run for run in self.generate_runs()
            if run.seed == seed
        ]


def create_default_matrix() -> RunMatrix:
    """Create default run matrix."""
    return RunMatrix()


def create_quick_matrix() -> RunMatrix:
    """Create minimal matrix for quick testing."""
    return RunMatrix(
        seeds=[42],
        horizons=[50, 200],
        variants=[V031Variant.V031A_KERNEL_COHERENT, V031Variant.V031B_HOLLOW_ADAPTIVE],
        attack_types=[AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY],
    )


def create_decision_matrix() -> RunMatrix:
    """Create matrix for decision regime (H=500)."""
    return RunMatrix(
        seeds=DEFAULT_SEEDS,
        horizons=[500],
        variants=[
            V031Variant.V031A_KERNEL_COHERENT,
            V031Variant.V031B_HOLLOW_ADAPTIVE,
            V031Variant.V031D_SELF_COMPRESS_ADAPTIVE,
        ],
        attack_types=[
            AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
            AdaptiveAttackType.ADAPTIVE_SHORTCUTTING,
            AdaptiveAttackType.ADAPTIVE_CONSTRAINT_COSMETICIZATION,
        ],
    )


def create_stress_matrix() -> RunMatrix:
    """Create matrix for stress regime (H=2000)."""
    return RunMatrix(
        seeds=DEFAULT_SEEDS,
        horizons=[2000],
        variants=[
            V031Variant.V031A_KERNEL_COHERENT,
            V031Variant.V031B_HOLLOW_ADAPTIVE,
        ],
        attack_types=[
            AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY,
        ],
    )
