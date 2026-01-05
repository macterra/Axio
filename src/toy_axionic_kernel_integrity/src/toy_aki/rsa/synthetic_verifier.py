"""
Synthetic Verifier Harness for RSA Stress Testing

This module provides ALSHarnessV080_SV, a test-only harness variant that
overrides semantic verification with deterministic probabilistic outcomes.

IMPORTANT: This is NOT part of AKI v0.8. It is an experimental test harness
for RSA stress testing. The base AKI v0.8 harness remains frozen.

Design rationale:
- AKI v0.8 semantic verification requires working mind to emit commitment-
  satisfying actions (LOG, STATE_SET, STATE_GET, SEQUENCE, BATCH).
- The toy working mind only emits WAIT actions, yielding 100% SEM_PASS failure.
- RSA stress testing requires non-trivial baseline pass rates to observe
  meaningful degradation under verifier noise.
- This harness provides deterministic probabilistic SEM_PASS for testing.
"""

from dataclasses import dataclass, field
from typing import Optional

from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa.adversary import stable_hash_64


@dataclass
class SVConfig:
    """
    Configuration for Synthetic Verifier mode.

    Separate from ALSConfigV080 to preserve AKI v0.8 spec purity.
    """
    # Per-commitment pass rate in parts-per-million
    # 800_000 = 80% per-Ci → 0.8³ ≈ 51.2% SEM_PASS rate
    per_ci_pass_rate_ppm: int = 800_000

    def expected_sem_pass_rate(self) -> float:
        """Expected SEM_PASS rate = (per_ci_rate)³"""
        r = self.per_ci_pass_rate_ppm / 1_000_000
        return r ** 3


class ALSHarnessV080_SV(ALSHarnessV080):
    """
    ALS-A v0.8 Harness with Synthetic Verifier for RSA stress testing.

    This is a TEST-ONLY harness variant. It overrides _compute_sem_pass()
    to use deterministic probabilistic outcomes instead of real commitment
    verification.

    Usage:
        sv_config = SVConfig(per_ci_pass_rate_ppm=800_000)
        harness = ALSHarnessV080_SV(seed=42, config=als_config, sv_config=sv_config)
        result = harness.run()

    The harness tracks calibration statistics for validation:
        - sv_epochs_evaluated: Total epochs with synthetic verification
        - sv_c0_true_count, sv_c1_true_count, sv_c2_true_count: Per-Ci true counts
        - sv_sem_pass_true_count: SEM_PASS true count
    """

    def __init__(
        self,
        seed: int,
        config: Optional[ALSConfigV080] = None,
        sv_config: Optional[SVConfig] = None,
        rsa_config=None,
        **kwargs
    ):
        """
        Initialize harness with synthetic verifier configuration.

        Args:
            seed: Random seed for reproducibility
            config: ALS-A v0.8 configuration (frozen spec)
            sv_config: Synthetic verifier configuration (test harness)
            rsa_config: RSA adversary configuration (optional)
        """
        super().__init__(seed=seed, config=config, rsa_config=rsa_config, **kwargs)
        self._sv_config = sv_config or SVConfig()

        # Calibration statistics
        self._sv_epochs_evaluated: int = 0
        self._sv_c0_true_count: int = 0
        self._sv_c1_true_count: int = 0
        self._sv_c2_true_count: int = 0
        self._sv_sem_pass_true_count: int = 0

    def _compute_sem_pass(self) -> tuple:
        """
        Compute SEM_PASS using synthetic deterministic probabilistic outcomes.

        Uses stable_hash_64 for reproducibility:
        - Same seed + epoch → same outcome
        - Independent from candidate sampling RNG
        - Stable across authority changes

        Returns:
            Tuple of (c0_ok, c1_ok, c2_ok, sem_pass)
        """
        global_epoch = self._compute_global_epoch()
        rate = self._sv_config.per_ci_pass_rate_ppm

        # Compute each Ci outcome independently using stable hash
        h_c0 = stable_hash_64(self._seed, global_epoch, "synth_C0", "verifier") % 1_000_000
        h_c1 = stable_hash_64(self._seed, global_epoch, "synth_C1", "verifier") % 1_000_000
        h_c2 = stable_hash_64(self._seed, global_epoch, "synth_C2", "verifier") % 1_000_000

        c0_ok = h_c0 < rate
        c1_ok = h_c1 < rate
        c2_ok = h_c2 < rate
        sem_pass = c0_ok and c1_ok and c2_ok

        # Track calibration statistics
        self._sv_epochs_evaluated += 1
        if c0_ok:
            self._sv_c0_true_count += 1
        if c1_ok:
            self._sv_c1_true_count += 1
        if c2_ok:
            self._sv_c2_true_count += 1
        if sem_pass:
            self._sv_sem_pass_true_count += 1

        return (c0_ok, c1_ok, c2_ok, sem_pass)

    def get_sv_calibration(self) -> dict:
        """
        Get synthetic verifier calibration statistics.

        Returns:
            Dict with observed vs expected pass rates for validation.
        """
        if self._sv_epochs_evaluated == 0:
            return {
                "epochs_evaluated": 0,
                "message": "No epochs evaluated yet"
            }

        n = self._sv_epochs_evaluated
        expected_per_ci = self._sv_config.per_ci_pass_rate_ppm / 1_000_000
        expected_sem_pass = expected_per_ci ** 3

        return {
            "epochs_evaluated": n,
            "per_ci_pass_rate_ppm": self._sv_config.per_ci_pass_rate_ppm,
            "c0": {
                "observed": self._sv_c0_true_count / n,
                "expected": expected_per_ci,
                "count": self._sv_c0_true_count,
            },
            "c1": {
                "observed": self._sv_c1_true_count / n,
                "expected": expected_per_ci,
                "count": self._sv_c1_true_count,
            },
            "c2": {
                "observed": self._sv_c2_true_count / n,
                "expected": expected_per_ci,
                "count": self._sv_c2_true_count,
            },
            "sem_pass": {
                "observed": self._sv_sem_pass_true_count / n,
                "expected": expected_sem_pass,
                "count": self._sv_sem_pass_true_count,
            },
        }
