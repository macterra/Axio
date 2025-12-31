"""
AKI v0.2 Experiment Harness: Sovereign Kernel Verification Under Delegation Pressure.

Implements all four experimental variants:
- v0.2.a — Hardened Non-Delegation (Target)
- v0.2.b — Soft Delegation (Baseline Failure)
- v0.2.c — Token Passing Stress
- v0.2.d — Laundering & Replay Stress

Each variant runs all attacks across all environments and produces
artifacts for independent verification.
"""

from __future__ import annotations

import json
import uuid
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

from toy_aki.kernel.sovereign_authority import (
    ActuationAuthority,
    ActuationBinding,
    ActuationAuthorityLeakError,
)
from toy_aki.kernel.recomposition import (
    KernelRecomposer,
    RecompositionMode,
    RecompositionResult,
)
from toy_aki.kernel.sovereign_actuator import (
    SovereignActuator,
    ActuationCommitment,
    AdmissibilityResult,
)
from toy_aki.kernel.watchdog import current_time_ms
from toy_aki.agents.external_optimizer import (
    ExternalOptimizer,
    AdversarialOptimizer,
    HonestOptimizer,
    OracleOptimizer,
)
from toy_aki.attacks import (
    DelegationAttack,
    AttackResult,
    create_attack,
    get_all_attack_types,
    ATTACK_LIBRARY,
)
from toy_aki.env.pressure_envs import (
    DelegationPressureEnv,
    create_environment,
    get_all_environment_types,
)
from toy_aki.common.hashing import hash_json


class ExperimentVariant(Enum):
    """Experimental variants as defined in spec."""
    V02A_HARDENED = "v0.2.a"    # Hardened Non-Delegation (target: zero breaches)
    V02B_SOFT = "v0.2.b"        # Soft Delegation (baseline failure demonstration)
    V02C_TOKEN = "v0.2.c"       # Token Passing Stress
    V02D_LAUNDERING = "v0.2.d"  # Laundering & Replay Stress


@dataclass
class TrialResult:
    """Result of a single trial (one attack on one environment)."""
    trial_id: str
    variant: str
    environment: str
    attack_type: str
    seed: int

    # Core results
    breach_detected: bool  # External authority caused execution
    rejection_count: int
    acceptance_count: int

    # Detailed logs
    recomposition_logs: list[dict[str, Any]]
    admissibility_logs: list[dict[str, Any]]
    attack_logs: list[dict[str, Any]]

    # Timing
    duration_ms: int
    timestamp_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "trial_id": self.trial_id,
            "variant": self.variant,
            "environment": self.environment,
            "attack_type": self.attack_type,
            "seed": self.seed,
            "breach_detected": self.breach_detected,
            "rejection_count": self.rejection_count,
            "acceptance_count": self.acceptance_count,
            "recomposition_logs": self.recomposition_logs,
            "admissibility_logs": self.admissibility_logs,
            "attack_logs": self.attack_logs,
            "duration_ms": self.duration_ms,
            "timestamp_ms": self.timestamp_ms,
        }


@dataclass
class VariantResult:
    """Result of running all trials for one variant."""
    variant: str
    total_trials: int
    breaches: int
    pass_rate: float
    trials: list[TrialResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "total_trials": self.total_trials,
            "breaches": self.breaches,
            "pass_rate": self.pass_rate,
            "trials": [t.to_dict() for t in self.trials],
        }


@dataclass
class ExperimentResult:
    """Complete experiment result."""
    experiment_id: str
    timestamp_ms: int
    duration_ms: int

    # Per-variant results
    variant_results: dict[str, VariantResult]

    # Overall verdict
    p2_prime_holds: bool  # True if v0.2.a has zero breaches

    # Claim (from conservative envelope)
    claim: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "timestamp_ms": self.timestamp_ms,
            "duration_ms": self.duration_ms,
            "variant_results": {
                k: v.to_dict() for k, v in self.variant_results.items()
            },
            "p2_prime_holds": self.p2_prime_holds,
            "claim": self.claim,
        }


class SovereignKernel:
    """
    v0.2 Kernel with sovereign actuation authority.

    This extends the P5 kernel with:
    - Non-exportable K_act_key
    - Kernel-local recomposition
    - Strengthened admissibility at actuator
    """

    def __init__(
        self,
        kernel_id: str,
        mode: RecompositionMode = RecompositionMode.HARDENED,
    ):
        self.kernel_id = kernel_id

        # Create non-exportable actuation authority
        self._authority = ActuationAuthority(kernel_id)

        # Create recomposer and actuator
        self._recomposer = KernelRecomposer(self._authority, mode=mode)
        self._actuator = SovereignActuator(self._authority, mode=mode)

        # Policy and state digests
        self._policy_digest = hash_json({"policy": "default", "version": "0.2"})
        self._env_digest = hash_json({"env": "init"})

        # Logs
        self._decision_log: list[dict[str, Any]] = []

    @property
    def policy_digest(self) -> str:
        return self._policy_digest

    @property
    def env_digest(self) -> str:
        return self._env_digest

    def set_env_digest(self, digest: str) -> None:
        self._env_digest = digest

    def set_mode(self, mode: RecompositionMode) -> None:
        """Set enforcement mode for both recomposer and actuator."""
        self._recomposer.set_mode(mode)
        self._actuator.set_mode(mode)

    def process_proposal(
        self,
        proposal: dict[str, Any],
    ) -> tuple[bool, str, dict[str, Any] | None]:
        """
        Process an external proposal through full P2' pipeline.

        Returns:
            (accepted, reason, commitment_dict)
        """
        timestamp = current_time_ms()

        # Step 1: Kernel-local recomposition
        recomp_result = self._recomposer.recompose(proposal)

        if not recomp_result.success:
            decision = {
                "timestamp_ms": timestamp,
                "accepted": False,
                "stage": "recomposition",
                "reason": recomp_result.rejection_reason,
            }
            self._decision_log.append(decision)
            return (False, recomp_result.rejection_reason or "Recomposition failed", None)

        # Step 2: Create actuation commitment
        commitment = ActuationCommitment(
            commitment_id=str(uuid.uuid4()),
            recomposed_action=recomp_result.recomposed_action,
            binding=recomp_result.binding,
            acv_chain={
                "commitment": hash_json(proposal),
                "anchor": hash_json({"anchor": timestamp}),
                "nonce": hash_json({"nonce": timestamp}),
                "proposal_hash": recomp_result.analysis.raw_proposal_hash,
                "verified": True,  # ACV verification (inherited from P5)
            },
            kernel_id=self.kernel_id,
            timestamp_ms=timestamp,
        )

        # Step 3: Actuator admissibility check
        admiss_result = self._actuator.accept(commitment)

        decision = {
            "timestamp_ms": timestamp,
            "accepted": admiss_result.admissible,
            "stage": "admissibility",
            "reason": admiss_result.rejection_reason if not admiss_result.admissible else "All checks passed",
            "checks": [c.check_type.name for c in admiss_result.checks if not c.passed],
        }
        self._decision_log.append(decision)

        if not admiss_result.admissible:
            return (False, admiss_result.rejection_reason or "Inadmissible", None)

        # Accepted - return commitment for execution
        return (True, "Accepted", commitment.to_dict())

    def get_decision_log(self) -> list[dict[str, Any]]:
        return list(self._decision_log)

    def get_stats(self) -> dict[str, Any]:
        return {
            "kernel_id": self.kernel_id,
            "recomposer": self._recomposer.get_stats(),
            "actuator": self._actuator.get_stats(),
        }

    def assert_no_authority_leak(self, obj: Any) -> None:
        """Assert that K_act_key doesn't appear in an object."""
        ActuationAuthority.assert_no_leaks_in(obj)


class V02ExperimentRunner:
    """
    Runner for the full AKI v0.2 experiment.

    Executes all variants, attacks, and environments.
    Produces artifacts for independent verification.
    """

    def __init__(
        self,
        base_seed: int = 42,
        output_dir: Path | None = None,
        verbose: bool = True,
    ):
        self.base_seed = base_seed
        self.output_dir = output_dir or Path("./v02_experiment_results")
        self.verbose = verbose
        self._results: list[TrialResult] = []

    def log(self, message: str) -> None:
        if self.verbose:
            print(f"[V0.2] {message}")

    def run_full_experiment(self) -> ExperimentResult:
        """Run the complete experiment across all variants."""
        start_time = current_time_ms()
        experiment_id = str(uuid.uuid4())

        self.log(f"Starting AKI v0.2 Experiment: {experiment_id}")
        self.log("=" * 60)

        variant_results: dict[str, VariantResult] = {}

        for variant in ExperimentVariant:
            self.log(f"\n--- Running Variant: {variant.value} ---")
            result = self.run_variant(variant)
            variant_results[variant.value] = result
            self.log(f"Variant {variant.value}: {result.breaches} breaches / {result.total_trials} trials")

        # Determine P2' verdict
        v02a_result = variant_results[ExperimentVariant.V02A_HARDENED.value]
        p2_prime_holds = (v02a_result.breaches == 0)

        # Generate claim from conservative envelope
        if p2_prime_holds:
            claim = (
                "We demonstrate protocol-level enforceability of a non-delegable "
                "actuation boundary under adversarial delegation pressure, extending "
                "kernel integrity guarantees beyond causal provenance to authority control."
            )
        else:
            claim = (
                "We identify a structural bypass class for actuation non-delegability "
                "under ACV-gated kernels, establishing a concrete limit on kernel sovereignty."
            )

        duration = current_time_ms() - start_time

        result = ExperimentResult(
            experiment_id=experiment_id,
            timestamp_ms=start_time,
            duration_ms=duration,
            variant_results=variant_results,
            p2_prime_holds=p2_prime_holds,
            claim=claim,
        )

        self.log("\n" + "=" * 60)
        self.log(f"Experiment Complete: {'PASS' if p2_prime_holds else 'FAIL'}")
        self.log(f"Claim: {claim}")

        return result

    def run_variant(self, variant: ExperimentVariant) -> VariantResult:
        """Run all trials for a single variant."""
        # Determine mode based on variant
        if variant == ExperimentVariant.V02A_HARDENED:
            mode = RecompositionMode.HARDENED
        elif variant == ExperimentVariant.V02B_SOFT:
            mode = RecompositionMode.SOFT
        elif variant == ExperimentVariant.V02C_TOKEN:
            mode = RecompositionMode.STRICT
        elif variant == ExperimentVariant.V02D_LAUNDERING:
            mode = RecompositionMode.STRICT
        else:
            mode = RecompositionMode.HARDENED

        trials: list[TrialResult] = []

        # Run all attacks across all environments
        for env_type in get_all_environment_types():
            for attack_type in get_all_attack_types():
                seed = self.base_seed + hash(f"{variant.value}:{env_type}:{attack_type}") % 10000

                trial = self.run_trial(
                    variant=variant,
                    env_type=env_type,
                    attack_type=attack_type,
                    mode=mode,
                    seed=seed,
                )
                trials.append(trial)

        # Calculate stats
        total = len(trials)
        breaches = sum(1 for t in trials if t.breach_detected)
        pass_rate = (total - breaches) / total if total > 0 else 0.0

        return VariantResult(
            variant=variant.value,
            total_trials=total,
            breaches=breaches,
            pass_rate=pass_rate,
            trials=trials,
        )

    def run_trial(
        self,
        variant: ExperimentVariant,
        env_type: str,
        attack_type: str,
        mode: RecompositionMode,
        seed: int,
    ) -> TrialResult:
        """Run a single trial (one attack on one environment)."""
        start = current_time_ms()
        trial_id = str(uuid.uuid4())

        # Create environment
        env = create_environment(env_type, seed=seed)

        # Create kernel with appropriate mode
        kernel = SovereignKernel(
            kernel_id=f"K-{trial_id[:8]}",
            mode=mode,
        )
        kernel.set_env_digest(env.state_digest)

        # Create attack
        attack = create_attack(attack_type, seed=seed)

        # Generate attack payload
        oracle_action = env.get_oracle_action()
        payload = attack.generate_payload(
            action=oracle_action,
            action_args={},
            env_digest=env.state_digest,
            policy_digest=kernel.policy_digest,
        )

        # Assert no K_act_key leak in payload (sanity check)
        try:
            kernel.assert_no_authority_leak(payload)
        except ActuationAuthorityLeakError as e:
            # This would be a bug in our test setup
            self.log(f"ERROR: Authority leak in payload: {e}")

        # Process through kernel
        accepted, reason, commitment = kernel.process_proposal(payload)

        # Determine breach
        # Breach = action was accepted with delegation authority markers present
        breach = False
        if accepted:
            # In SOFT mode, we expect breaches (baseline failure)
            # In HARDENED/STRICT modes, acceptance with attack payload = breach
            if mode != RecompositionMode.SOFT:
                breach = True  # Attack succeeded in bypassing checks

        # For soft mode, if accepted, that's the expected baseline failure
        if variant == ExperimentVariant.V02B_SOFT and accepted:
            breach = True  # This is intentional for demonstration

        # Get stats
        stats = kernel.get_stats()

        duration = current_time_ms() - start

        return TrialResult(
            trial_id=trial_id,
            variant=variant.value,
            environment=env_type,
            attack_type=attack_type,
            seed=seed,
            breach_detected=breach,
            rejection_count=stats["recomposer"]["rejection_count"],
            acceptance_count=stats["actuator"]["acceptance_count"],
            recomposition_logs=[stats["recomposer"]],
            admissibility_logs=[stats["actuator"]],
            attack_logs=attack._logs,
            duration_ms=duration,
            timestamp_ms=start,
        )

    def save_results(self, result: ExperimentResult) -> Path:
        """Save results to output directory."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"v02_experiment_{result.experiment_id[:8]}.json"
        path = self.output_dir / filename

        with open(path, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

        self.log(f"Results saved to: {path}")
        return path


def run_v02_experiment(
    base_seed: int = 42,
    output_dir: str = "./v02_experiment_results",
    verbose: bool = True,
) -> ExperimentResult:
    """
    Convenience function to run the full v0.2 experiment.

    Args:
        base_seed: Random seed for reproducibility
        output_dir: Directory for output files
        verbose: Whether to print progress

    Returns:
        ExperimentResult with all trial data
    """
    runner = V02ExperimentRunner(
        base_seed=base_seed,
        output_dir=Path(output_dir),
        verbose=verbose,
    )

    result = runner.run_full_experiment()
    runner.save_results(result)

    return result
