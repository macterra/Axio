# RSA v0.1.2 Implementation Report

**Version:** 0.1.2 (spec-pure)
**Date:** 2026-01-05
**Status:** ✓ COMPLETE
**Revision Note:** Restores AKI v0.8 spec purity; SV is now a separate test harness

---

## Executive Summary

RSA v0.1 (Reflective Sovereign Agents - Governance DoS Stress) is an **additive stress layer** on AKI v0.8 that injects controlled epistemic noise into semantic verification outcomes.

This v0.1.2 report addresses the spec-purity concern from v0.1.1:

- **v0.1.1 Issue:** Added `synthetic_verifier_enabled` to `ALSConfigV080`, modifying AKI v0.8
- **v0.1.2 Fix:** Created `ALSHarnessV080_SV` as a **separate test harness** subclass

**Spec Purity Restored:**
- `ALSConfigV080`: FROZEN (no synthetic verifier fields)
- `ALSHarnessV080`: FROZEN (no synthetic verifier override)
- `ALSHarnessV080_SV`: NEW test harness in `toy_aki.rsa.synthetic_verifier`
- `SVConfig`: Separate configuration for synthetic verifier

**Key Finding (Corrected):**

Under a synthetic semantic oracle with per-Ci pass probability 0.80 (→ ~51% SEM_PASS):

| p_flip | Mean Lapses | Mean Lapse Epochs | Uptime | Pivotal Flips |
|--------|-------------|-------------------|--------|---------------|
| 0% | 0.0 | 0.0 | 100.0% | 0 |
| 2% | 0.2 | 0.2 | 99.9% | 42 |
| 10% | 1.0 | 1.0 | 99.5% | 166 |
| 20% | 3.2 | 6.0 | 97.0% | 282 |

System remains ROBUST (no DOS_REGIME) through 20% flip rate under this geometry.

**Terminology:**
- **AKI kernel:** `ALSHarnessV080` + `ALSConfigV080` behavior (frozen)
- **Test harness:** `ALSHarnessV080_SV` subclass with synthetic oracle (experimental)
- **Epoch:** One renewal check interval (50 cycles by default); `global_epoch = cycle // renewal_check_interval`

---

## 1. Spec Purity Architecture

### 1.1 Layered Design

```
┌─────────────────────────────────────────────────────────────┐
│                    RSA v0.1.2 Stack                         │
├─────────────────────────────────────────────────────────────┤
│  ALSHarnessV080_SV (test harness)                          │
│  - Subclasses ALSHarnessV080                                │
│  - Overrides _compute_sem_pass() with synthetic oracle      │
│  - Located in: toy_aki/rsa/synthetic_verifier.py            │
├─────────────────────────────────────────────────────────────┤
│  RSA Adversary (additive stress layer)                      │
│  - RSAAdversary: corruption logic                           │
│  - RSATelemetry: epoch records                              │
│  - Located in: toy_aki/rsa/                                 │
├─────────────────────────────────────────────────────────────┤
│  AKI v0.8 (FROZEN)                                          │
│  - ALSHarnessV080: authority lease semantics                │
│  - ALSConfigV080: configuration (no SV fields)              │
│  - Located in: toy_aki/als/harness.py                       │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Import Pattern

```python
# Correct import pattern (avoids circular imports)
from toy_aki.als.harness import ALSConfigV080
from toy_aki.rsa import RSAConfig, RSANoiseModel, RSAScope
from toy_aki.rsa.synthetic_verifier import ALSHarnessV080_SV, SVConfig

# Configure
als_config = ALSConfigV080(max_cycles=10_000)  # AKI v0.8 (frozen)
sv_config = SVConfig(per_ci_pass_rate_ppm=800_000)  # Test harness
rsa_config = RSAConfig(rsa_enabled=True, rsa_p_flip_ppm=100_000)  # Stress layer

# Run
harness = ALSHarnessV080_SV(seed=42, config=als_config, sv_config=sv_config, rsa_config=rsa_config)
result = harness.run()
```

### 1.3 Why Separate Harness?

The original v0.1.1 approach added `synthetic_verifier_enabled` to `ALSConfigV080`. This violated the RSA v0.1 contract:

> *"RSA is additive—do not touch the AKI kernel."*

The synthetic verifier replaces the semantic evaluation path, which is part of the AKI kernel. By isolating it in a separate harness subclass:

1. `ALSConfigV080` remains frozen per spec
2. `ALSHarnessV080` remains frozen per spec
3. The synthetic oracle is clearly labeled as a test artifact
4. Users must explicitly opt-in by using `ALSHarnessV080_SV`

---

## 2. Synthetic Verifier Calibration

### 2.1 Oracle Design

The synthetic verifier uses deterministic probabilistic outcomes:

```python
def _compute_sem_pass(self) -> tuple:
    """Synthetic verifier: deterministic probabilistic outcomes."""
    global_epoch = self._compute_global_epoch()
    rate = self._sv_config.per_ci_pass_rate_ppm

    h_c0 = stable_hash_64(self._seed, global_epoch, "synth_C0", "verifier") % 1_000_000
    h_c1 = stable_hash_64(self._seed, global_epoch, "synth_C1", "verifier") % 1_000_000
    h_c2 = stable_hash_64(self._seed, global_epoch, "synth_C2", "verifier") % 1_000_000

    c0_ok = h_c0 < rate
    c1_ok = h_c1 < rate
    c2_ok = h_c2 < rate
    sem_pass = c0_ok and c1_ok and c2_ok

    return (c0_ok, c1_ok, c2_ok, sem_pass)
```

Properties:
- **Seeded deterministically:** Same seed + epoch → same outcome
- **Independent from candidate sampling RNG:** Uses separate hash keys
- **Stable across authority changes:** Uses global_epoch, not per-authority epoch
- **Documented clock:** `global_epoch = cycle // renewal_check_interval`

### 2.2 Calibration Results

Configuration:
- `per_ci_pass_rate_ppm = 800_000` (80% per-Ci)
- `max_cycles = 10_000`
- `renewal_check_interval = 50`
- `global_epoch_max = 10_000 / 50 = 200`

Expected rates:
- Per-Ci: 0.800
- SEM_PASS: 0.8³ = 0.512

Observed rates (averaged across seeds 40-44, 200 epochs per seed, 1000 total evaluations):

| p_flip | C0 observed | C1 observed | C2 observed | SEM_PASS observed |
|--------|-------------|-------------|-------------|-------------------|
| 0% | 0.816 | 0.795 | 0.785 | 0.491 |
| 5% | 0.816 | 0.796 | 0.785 | 0.491 |
| 10% | 0.817 | 0.794 | 0.784 | 0.490 |
| 20% | 0.820 | 0.794 | 0.786 | 0.493 |

**Calibration Assessment:**
- Per-Ci rates: 0.78-0.82 (absolute deviation ≤0.02 from expected 0.80) ✓
- SEM_PASS rate: 0.49 (absolute deviation 0.022 from expected 0.512, or 4.3% relative) ✓

The synthetic oracle matches the intended base rates within expected statistical variance for 200-epoch runs (N=1000 total evaluations across 5 seeds).

---

## 3. DoS Sweep Results

### 3.1 Configuration

```python
# AKI v0.8 (FROZEN)
ALSConfigV080(
    max_cycles=10_000,
    eligibility_threshold_k=3,
    max_successive_renewals=3,
    amnesty_interval=10,
    amnesty_decay=1,
    cta_enabled=True,
)

# Synthetic Verifier (TEST HARNESS)
SVConfig(per_ci_pass_rate_ppm=800_000)  # 80% per-Ci → ~51% SEM_PASS

# Seeds
seeds = [40, 41, 42, 43, 44]

# Flip rates
p_flip_values = [0, 5_000, 10_000, 20_000, 50_000, 100_000, 200_000] PPM
```

### 3.2 Results Summary

| p_flip (PPM) | p_flip (%) | Mean Lapses | Mean Lapse Epochs | Mean Uptime | Sum Flips | Sum Pivotal | Regime |
|--------------|------------|-------------|-------------------|-------------|-----------|-------------|--------|
| 0 | 0.00 | 0.0 | 0.0 | 100.0% | 0 | 0 | 5×ROBUST |
| 5,000 | 0.50 | 0.0 | 0.0 | 100.0% | 20 | 12 | 5×ROBUST |
| 10,000 | 1.00 | 0.0 | 0.0 | 100.0% | 27 | 18 | 5×ROBUST |
| 20,000 | 2.00 | 0.2 | 0.2 | 99.9% | 67 | 42 | 5×ROBUST |
| 50,000 | 5.00 | 0.2 | 0.2 | 99.9% | 159 | 97 | 5×ROBUST |
| 100,000 | 10.00 | 1.0 | 1.0 | 99.5% | 280 | 166 | 5×ROBUST |
| 200,000 | 20.00 | 3.2 | 6.0 | 97.0% | 562 | 282 | 5×ROBUST |

### 3.3 Key Observations

1. **Smooth Degradation:** Lapse counts and epochs increase monotonically with flip rate.

2. **Pivotal Flip Rate:** ~50-60% of flips are pivotal (change SEM_PASS outcome). This decreases at higher flip rates due to multi-flip epochs.

3. **CTA Effectiveness:** Even at 20% flip rate, no runs crossed into DOS_REGIME. CTA's amnesty mechanism provides a time-based escape hatch.

4. **Eligibility Gating:** The K=3 eligibility threshold is the primary failure amplifier. Semantic failures accumulate until candidates become ineligible.

### 3.4 Defensible Claim

> Under a synthetic semantic oracle with per-Ci pass probability 0.80 (baseline SEM_PASS ≈ 0.49–0.51) and **independent per-Ci post-verification Bernoulli flips** applied at rate up to 20%, governance degrades smoothly and CTA prevents persistent DoS under this geometry.

---

## 4. Hook Location Verification

### 4.1 Causal Path Proof

The RSA hook is verified to be upstream of streak mutation:

```python
# In _update_streak_at_epoch_end():
c0_ok_raw, c1_ok_raw, c2_ok_raw, sem_pass_raw = self._compute_sem_pass()

# RSA corruption (if enabled)
c0_ok, c1_ok, c2_ok, sem_pass, rsa_record = self._rsa_adversary.corrupt(...)

# Streak update uses CORRUPTED values
if sem_pass:  # Uses corrupted sem_pass
    self._semantic_fail_streak[policy_id] = 0
else:
    self._semantic_fail_streak[policy_id] = streak_before + 1
```

### 4.2 Pivotal Flip Verification

At 20% flip rate, seed 40 shows:
```
epoch=6: SEM_PASS raw=True → corrupted=False (pivotal: streak 0→1)
epoch=17: SEM_PASS raw=True → corrupted=False (pivotal: streak 0→1)
epoch=23: SEM_PASS raw=True → corrupted=False (pivotal: streak 0→1)
...
```

Total: 45 pivotal flips out of 121 total flips (37% pivotal rate for this seed).

Pivotal rate varies by seed due to different overlap patterns (multi-flip epochs where only one flip can be pivotal) and baseline SEM_PASS realizations; aggregate pivotal rate across all seeds remains ~50%.

---

## 5. Files Created/Modified

### Created (v0.1.2):

- `toy_aki/rsa/synthetic_verifier.py`:
  - `SVConfig`: Synthetic verifier configuration
  - `ALSHarnessV080_SV`: Test harness with synthetic semantic oracle
  - `get_sv_calibration()`: Returns observed vs expected pass rates

- `scripts/rsa_run0_dos_sweep_v012.py`:
  - Spec-pure sweep script using `ALSHarnessV080_SV`
  - Includes calibration statistics table

### Modified (v0.1.2):

- `toy_aki/rsa/__init__.py`:
  - Removed `ALSHarnessV080_SV` and `SVConfig` exports to avoid circular imports
  - Added documentation for correct import pattern

### Reverted (v0.1.2):

- `toy_aki/als/harness.py`:
  - Removed `synthetic_verifier_enabled` from `ALSConfigV080`
  - Removed `_compute_sem_pass()` override from `ALSHarnessV080`
  - AKI v0.8 is now frozen as intended

---

## Appendix: Verification Commands

```bash
# Verify AKI v0.8 is frozen (no synthetic verifier fields)
python3 -c "
from toy_aki.als.harness import ALSConfigV080
config = ALSConfigV080()
assert not hasattr(config, 'synthetic_verifier_enabled')
assert not hasattr(config, 'synthetic_sem_pass_rate_ppm')
print('✓ ALSConfigV080 is frozen')
"

# Run spec-pure DoS sweep
python3 scripts/rsa_run0_dos_sweep_v012.py

# Verify SV calibration
python3 -c "
from toy_aki.als.harness import ALSConfigV080
from toy_aki.rsa import RSAConfig, RSANoiseModel, RSAScope
from toy_aki.rsa.synthetic_verifier import ALSHarnessV080_SV, SVConfig

config = ALSConfigV080(max_cycles=10000)
sv_config = SVConfig(per_ci_pass_rate_ppm=800_000)
rsa_cfg = RSAConfig(rsa_enabled=True, rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI, rsa_p_flip_ppm=100_000)

h = ALSHarnessV080_SV(seed=42, config=config, sv_config=sv_config, rsa_config=rsa_cfg)
result = h.run()

calib = h.get_sv_calibration()
print(f'Epochs evaluated: {calib[\"epochs_evaluated\"]}')
print(f'C0: observed={calib[\"c0\"][\"observed\"]:.3f}, expected={calib[\"c0\"][\"expected\"]:.3f}')
print(f'C1: observed={calib[\"c1\"][\"observed\"]:.3f}, expected={calib[\"c1\"][\"expected\"]:.3f}')
print(f'C2: observed={calib[\"c2\"][\"observed\"]:.3f}, expected={calib[\"c2\"][\"expected\"]:.3f}')
print(f'SEM_PASS: observed={calib[\"sem_pass\"][\"observed\"]:.3f}, expected={calib[\"sem_pass\"][\"expected\"]:.3f}')
"

# Verify RSA telemetry matches harness lapse metrics
python3 -c "
from toy_aki.als.harness import ALSConfigV080
from toy_aki.rsa import RSAConfig, RSANoiseModel, RSAScope
from toy_aki.rsa.synthetic_verifier import ALSHarnessV080_SV, SVConfig

# Use exact sweep config for reproducibility
config = ALSConfigV080(
    max_cycles=10_000,
    eligibility_threshold_k=3,
    max_successive_renewals=3,
    amnesty_interval=10,
    amnesty_decay=1,
    cta_enabled=True,
)
sv_config = SVConfig(per_ci_pass_rate_ppm=800_000)
rsa_cfg = RSAConfig(
    rsa_enabled=True,
    rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
    rsa_p_flip_ppm=200_000,
    rsa_scope=RSAScope.PER_CI,
)

h = ALSHarnessV080_SV(seed=40, config=config, sv_config=sv_config, rsa_config=rsa_cfg)
result = h.run()

print(f'Lapse events: {len(result.lapse_events_v080)}')
print(f'RSA epochs_in_lapse: {result.rsa[\"summary\"][\"epochs_in_lapse\"]}')
print(f'Harness total_lapse_duration_epochs: {result.total_lapse_duration_epochs}')
assert result.rsa['summary']['epochs_in_lapse'] == result.total_lapse_duration_epochs
print('✓ Metrics match')
"
```

---

## Appendix B: Run-0 Definition of Done

| Criterion | Status |
|-----------|--------|
| RSA detachable; baseline equivalence when disabled and when p_flip=0 | ✓ |
| No RSA firing during lapse; lapse epochs recorded with 0 targets | ✓ |
| Aggregation clearly separated (per-seed vs aggregate) | ✓ |
| Sensitivity regime uses explicit SV harness; AKI kernel remains frozen | ✓ |
| SV calibration reported (observed vs expected) | ✓ |
| Causal-path evidence: pivotal flips change streak update outcomes | ✓ |
| Claim sentence names the oracle and noise model | ✓ |

**Run 0 Status: COMPLETE**
