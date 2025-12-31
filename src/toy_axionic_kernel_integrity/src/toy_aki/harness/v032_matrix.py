"""
Run Matrix for v0.3.2 Experiments.

Extends v0.3.1 with:
- Default horizons [500, 2000] for decision regime
- Stress horizons [10000] opt-in (not CI)
- AdaptiveBoundaryFuzzer as adversary
- Two-phase schedule (Phase P → Phase X)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Iterator, Optional
from enum import Enum, auto
import hashlib


# Default configurations per spec §3
DEFAULT_HORIZONS = [500, 2000]  # Decision regime
STRESS_HORIZONS = [10000]  # Opt-in stress regime (not CI)
DEFAULT_SEEDS = [42, 43, 44]


class V032Variant(Enum):
    """v0.3.2 experiment variants."""
    V032A_KERNEL_COHERENT = "v0.3.2.a"  # Kernel-coherent control
    V032B_HOLLOW_FUZZER = "v0.3.2.b"    # Hollow simulator with boundary fuzzer
    V032C_UNBOUNDED_FUZZER = "v0.3.2.c"  # Unbounded compute with fuzzer
    V032D_COMPRESS_FUZZER = "v0.3.2.d"   # Self-compression with fuzzer


class FuzzerStrategy(Enum):
    """Fuzzer search strategy (binding per spec §2)."""
    UCB1_BANDIT = auto()  # Phase P: UCB1 exploration
    GREEDY_EXPLOIT = auto()  # Phase X: Best-first exploitation


@dataclass(frozen=True)
class V032RunSpec:
    """
    Specification for a single v0.3.2 experimental run.

    Frozen for hashability and reproducibility.
    """
    seed: int
    horizon: int
    variant: V032Variant
    scenario_id: str
    use_stress: bool = False  # True if opt-in stress regime

    def run_id(self) -> str:
        """Generate unique run ID."""
        regime = "STRESS" if self.use_stress else "DECISION"
        return f"{self.variant.value}_{regime}_H{self.horizon}_S{self.seed}"

    def is_adversarial(self) -> bool:
        """Check if this is an adversarial run (uses fuzzer)."""
        return self.variant != V032Variant.V032A_KERNEL_COHERENT

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "seed": self.seed,
            "horizon": self.horizon,
            "variant": self.variant.value,
            "scenario_id": self.scenario_id,
            "use_stress": self.use_stress,
            "run_id": self.run_id(),
            "is_adversarial": self.is_adversarial(),
        }


@dataclass
class V032RunMatrix:
    """
    Defines and generates the complete run matrix for v0.3.2.

    Default horizons: [500, 2000]
    Stress horizons: [10000] (opt-in via create_stress_matrix())
    Seeds: [42, 43, 44]
    Variants: a/b/c/d per v0.3.2 spec
    """
    seeds: List[int] = field(default_factory=lambda: list(DEFAULT_SEEDS))
    horizons: List[int] = field(default_factory=lambda: list(DEFAULT_HORIZONS))
    variants: List[V032Variant] = field(default_factory=lambda: [
        V032Variant.V032A_KERNEL_COHERENT,
        V032Variant.V032B_HOLLOW_FUZZER,
        V032Variant.V032C_UNBOUNDED_FUZZER,
        V032Variant.V032D_COMPRESS_FUZZER,
    ])
    use_stress: bool = False

    def generate_scenario_id(self, seed: int, horizon: int) -> str:
        """
        Generate deterministic scenario ID for a (seed, horizon) pair.

        Ensures same scenario is used across variants for matched comparison.
        """
        combined = f"v032_scenario_{seed}_{horizon}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def generate_runs(self) -> Iterator[V032RunSpec]:
        """
        Generate all runs in the matrix.

        Order: horizons -> seeds -> variants
        This groups comparisons together.
        """
        for horizon in self.horizons:
            for seed in self.seeds:
                scenario_id = self.generate_scenario_id(seed, horizon)

                for variant in self.variants:
                    yield V032RunSpec(
                        seed=seed,
                        horizon=horizon,
                        variant=variant,
                        scenario_id=scenario_id,
                        use_stress=self.use_stress,
                    )

    def generate_matched_pairs(
        self,
        horizon: int,
        seed: int,
    ) -> List[tuple[V032RunSpec, V032RunSpec]]:
        """
        Generate matched (control, adversary) pairs for a given horizon and seed.

        Used for direct comparison in reports.
        """
        scenario_id = self.generate_scenario_id(seed, horizon)

        control = V032RunSpec(
            seed=seed,
            horizon=horizon,
            variant=V032Variant.V032A_KERNEL_COHERENT,
            scenario_id=scenario_id,
            use_stress=self.use_stress,
        )

        pairs = []
        for variant in self.variants:
            if variant == V032Variant.V032A_KERNEL_COHERENT:
                continue
            adversary = V032RunSpec(
                seed=seed,
                horizon=horizon,
                variant=variant,
                scenario_id=scenario_id,
                use_stress=self.use_stress,
            )
            pairs.append((control, adversary))

        return pairs

    def count_runs(self) -> int:
        """Count total runs in matrix."""
        return len(self.horizons) * len(self.seeds) * len(self.variants)

    def get_runs_by_horizon(self, horizon: int) -> List[V032RunSpec]:
        """Get all runs for a specific horizon."""
        return [
            run for run in self.generate_runs()
            if run.horizon == horizon
        ]

    def get_runs_by_seed(self, seed: int) -> List[V032RunSpec]:
        """Get all runs for a specific seed."""
        return [
            run for run in self.generate_runs()
            if run.seed == seed
        ]

    def get_adversarial_runs(self) -> List[V032RunSpec]:
        """Get all adversarial runs (non-control)."""
        return [
            run for run in self.generate_runs()
            if run.is_adversarial()
        ]

    def get_control_runs(self) -> List[V032RunSpec]:
        """Get all control runs."""
        return [
            run for run in self.generate_runs()
            if not run.is_adversarial()
        ]


def create_default_matrix() -> V032RunMatrix:
    """
    Create default run matrix for v0.3.2.

    Horizons: [500, 2000] (decision regime)
    Seeds: [42, 43, 44]
    All 4 variants
    """
    return V032RunMatrix()


def create_quick_matrix() -> V032RunMatrix:
    """
    Create minimal matrix for quick testing/CI.

    Horizons: [500]
    Seeds: [42]
    2 variants (control + one adversary)
    """
    return V032RunMatrix(
        seeds=[42],
        horizons=[500],
        variants=[
            V032Variant.V032A_KERNEL_COHERENT,
            V032Variant.V032B_HOLLOW_FUZZER,
        ],
    )


def create_stress_matrix() -> V032RunMatrix:
    """
    Create opt-in stress matrix for v0.3.2.

    Horizons: [10000] (stress regime)
    Seeds: [42, 43, 44]
    All 4 variants

    WARNING: Not for CI - very long runs.
    """
    return V032RunMatrix(
        seeds=DEFAULT_SEEDS,
        horizons=STRESS_HORIZONS,
        use_stress=True,
    )


def create_single_run_matrix(
    seed: int = 42,
    horizon: int = 500,
    variant: V032Variant = V032Variant.V032B_HOLLOW_FUZZER,
) -> V032RunMatrix:
    """
    Create matrix for a single run (for debugging/testing).

    Args:
        seed: Random seed
        horizon: Run horizon
        variant: Variant to run

    Returns:
        V032RunMatrix with single run
    """
    return V032RunMatrix(
        seeds=[seed],
        horizons=[horizon],
        variants=[variant],
    )
