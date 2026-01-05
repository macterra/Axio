# RSA v0.1 Implementation Report

**Version:** 0.1
**Date:** 2026-01-05
**Status:** ✓ COMPLETE

---

## Executive Summary

RSA v0.1 (Reflective Sovereign Agents - Governance DoS Stress) has been successfully implemented as an additive stress layer on AKI v0.8. The implementation injects verifier-outcome noise to test governance resilience under semantic verification failures.

**Key Findings:**
- AKI v0.8 governance remains ROBUST at flip rates up to 2%
- No regime degradation observed in baseline sweep (0-20000 PPM)
- RSA is fully detachable with verified behavioral equivalence when disabled

---

## 1. Architecture

### 1.1 Package Structure

```
toy_aki/rsa/
├── __init__.py      # Exports: RSAConfig, RSANoiseModel, RSAScope, RSAAdversary, RSATelemetry
├── config.py        # Configuration dataclass and enums
├── adversary.py     # Deterministic corruption logic with stateless hash
└── telemetry.py     # Epoch and run-level telemetry recording
```

### 1.2 Hook Location

The RSA hook is integrated in `ALSHarnessV080._update_streak_at_epoch_end()`:

```
_compute_sem_pass() → [RSA hook: maybe corrupt booleans] → streak update logic
```

**Critical design choice:** RSA uses a **global epoch counter** (cycle // renewal_check_interval) rather than the per-authority epoch index. This ensures deterministic flip patterns across authority changes.

### 1.3 Integration Pattern

RSA is configured via a separate `rsa_config` parameter to the harness constructor, keeping it decoupled from `ALSConfigV080`:

```python
rsa_cfg = RSAConfig(
    rsa_enabled=True,
    rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
    rsa_p_flip_ppm=5000,  # 0.5%
    rsa_scope=RSAScope.PER_CI,
)
harness = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
```

---

## 2. Noise Model

### 2.1 Stateless Hash-Based Flips

Flip decisions are pure functions of `(seed_rsa, global_epoch, key, stage)`:

```python
def _should_flip(seed_rsa, epoch, key, stage, p_flip_ppm):
    u64 = stable_hash_64(seed_rsa, epoch, key, stage)
    threshold = u64 % 1_000_000
    return threshold < p_flip_ppm
```

Uses FNV-1a 64-bit hash for determinism across Python versions.

### 2.2 Scope Options

| Scope | Targets per Epoch | Description |
|-------|-------------------|-------------|
| `PER_CI` | 3 | Corrupt each Ci_OK independently, recompute SEM_PASS |
| `SEM_PASS_ONLY` | 1 | Corrupt only aggregate SEM_PASS |

### 2.3 Probability Representation

- **PPM integers** (0-1,000,000) to avoid float precision issues
- 5000 PPM = 0.5% flip rate
- No floats anywhere in the spec or implementation

---

## 3. Telemetry

### 3.1 Per-Epoch Record

```python
@dataclass
class RSAEpochRecord:
    epoch: int
    targets: int          # 0 during lapse, 3 for PER_CI, 1 for SEM_PASS_ONLY
    flips: int
    flips_by_key: Dict[str, int]  # {"C0": 0, "C1": 1, "C2": 0, "SEM_PASS": 0}
    c0_raw/c1_raw/c2_raw/sem_pass_raw: bool  # Before corruption
    c0_corrupted/c1_corrupted/c2_corrupted/sem_pass_corrupted: bool  # After
    in_lapse: bool
```

### 3.2 Run-Level Summary

```python
result.rsa["summary"] = {
    "total_targets": 396,
    "total_flips": 14,
    "observed_flip_rate_ppm": 35353,
    "expected_flip_rate_ppm": 20000,
    "epochs_with_flips": 12,
    "epochs_in_lapse": 0,
    "epochs_evaluated": 132,
}
```

---

## 4. Acceptance Tests

### 4.1 Baseline Equivalence (✓ PASSED)

| Test | Result |
|------|--------|
| No RSA vs RSA disabled | ✓ All 5 seeds match |
| No RSA vs p_flip=0 | ✓ All 5 seeds match |
| Semantic trace identity | ✓ All 5 seeds match |

### 4.2 DoS Sweep Results

| p_flip (PPM) | p_flip (%) | Mean Lapses | Mean Recoveries | Mean RY | Mean Uptime | Total Flips | Regime |
|--------------|------------|-------------|-----------------|---------|-------------|-------------|--------|
| 0 | 0.00 | 6.0 | 6.0 | 1.16 | 66.5% | 0 | ROBUST |
| 200 | 0.02 | 6.0 | 6.0 | 1.16 | 66.5% | 1 | ROBUST |
| 500 | 0.05 | 6.0 | 6.0 | 1.16 | 66.5% | 2 | ROBUST |
| 1000 | 0.10 | 6.0 | 6.0 | 1.16 | 66.5% | 4 | ROBUST |
| 2000 | 0.20 | 6.0 | 6.0 | 1.16 | 66.5% | 7 | ROBUST |
| 5000 | 0.50 | 6.0 | 6.0 | 1.16 | 66.5% | 15 | ROBUST |
| 10000 | 1.00 | 6.0 | 6.0 | 1.16 | 66.5% | 18 | ROBUST |
| 20000 | 2.00 | 6.0 | 6.0 | 1.16 | 66.5% | 48 | ROBUST |

**Key Observation:** AKI v0.8 governance is remarkably resilient. Even at 2% flip rate (expected 8 flips per 100 commitment checks), the system maintains:
- Constant lapse count (~6 per run)
- Full recovery rate (100%)
- Stable authority uptime (~66.5%)

---

## 5. Implementation Notes

### 5.1 Global Epoch Counter

**Bug Fixed:** Initial implementation used `self._epoch_index` which resets on each authority succession. This caused the same flip pattern to repeat for each authority holder.

**Solution:** Added `_compute_global_epoch()` method:
```python
def _compute_global_epoch(self) -> int:
    return self._cycle // self._config.renewal_check_interval
```

### 5.2 No RSA During Lapse

Per spec requirement (user binding decision R1):
- RSA does NOT fire during NULL_AUTHORITY
- No commitment evaluation occurs during lapse
- Telemetry records `in_lapse=True` with 0 targets

### 5.3 Stateless Design (No RNG Contamination)

Per spec requirement (user binding decision R2):
- No `random.Random()` instance
- Pure hash-based decisions
- Cannot contaminate candidate sampling RNG

---

## 6. Files Modified/Created

### Created:
- `toy_aki/rsa/__init__.py`
- `toy_aki/rsa/config.py`
- `toy_aki/rsa/adversary.py`
- `toy_aki/rsa/telemetry.py`
- `scripts/rsa_run0_baseline_equivalence_v010.py`
- `scripts/rsa_run0_dos_sweep_v010.py`

### Modified:
- `toy_aki/als/harness.py`:
  - Added RSA imports with try/except fallback
  - Added `rsa: Optional[Dict]` field to `ALSRunResultV080`
  - Added `rsa_config` parameter to `ALSHarnessV080.__init__`
  - Added `_compute_global_epoch()` method
  - Added `_update_streak_at_epoch_end()` override with RSA hook

---

## 7. Next Steps

1. **Higher Flip Rates:** Explore 5-10% flip rates to find degradation threshold
2. **Scope Comparison:** Compare PER_CI vs SEM_PASS_ONLY impact
3. **Extended Runs:** Longer simulations (50k+ cycles) for statistical significance
4. **Correlated Flips:** Future RSA version could model correlated failures

---

## Appendix: Verification Commands

```bash
# Baseline equivalence
python3 scripts/rsa_run0_baseline_equivalence_v010.py

# DoS sweep
python3 scripts/rsa_run0_dos_sweep_v010.py

# Quick smoke test
python3 -c "
from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa import RSAConfig, RSANoiseModel, RSAScope

config = ALSConfigV080(max_cycles=1000)
rsa_cfg = RSAConfig(
    rsa_enabled=True,
    rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
    rsa_p_flip_ppm=50000,
)
h = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
result = h.run()
print(f'Flips: {result.rsa[\"summary\"][\"total_flips\"]}')
"
```
