# RSA v0.1.1 Implementation Report

**Version:** 0.1.1 (corrected)
**Date:** 2026-01-05
**Status:** ✓ COMPLETE
**Revision Note:** Addresses C1-C3 contradictions from initial v0.1 report

---

## Executive Summary

RSA v0.1 (Reflective Sovereign Agents - Governance DoS Stress) has been implemented as an additive stress layer on AKI v0.8. This corrected report addresses three contradictions from the initial v0.1 report:

- **C1 (Fixed):** `epochs_in_lapse` now matches harness `total_lapse_duration_epochs`
- **C2 (Fixed):** Per-seed vs aggregate metrics are now reported separately
- **C3 (Addressed):** Synthetic verifier mode added to produce non-trivial SEM_PASS rates

**Key Finding (Corrected):**
- With synthetic verifier (80% per-Ci pass rate → ~51% SEM_PASS rate):
  - 0% flip: 100% uptime, 0 lapses
  - 10% flip: 99.5% uptime, 1.0 mean lapses
  - 20% flip: 97.0% uptime, 3.2 mean lapses, 6.0 mean lapse epochs
- System remains ROBUST (no DOS_REGIME) through 20% flip rate in this configuration

**Important Caveat:**
The original v0.1 report claimed "ROBUST up to 2%" but this was based on a configuration where SEM_PASS was *always* FALSE (100% failure rate baseline). Flips could only change FALSE→TRUE, which cannot degrade an already-failed state. The corrected sweep uses a synthetic verifier to produce meaningful baseline pass rates.

---

## 1. Bug Fixes from v0.1.0

### 1.1 C1: epochs_in_lapse Mismatch (FIXED)

**Problem:** RSA telemetry showed `epochs_in_lapse: 0` while harness reported `total_lapse_duration_epochs: 68`.

**Root Cause:** The RSA lapse recording was inside `_update_streak_at_epoch_end()`, but that method is NOT called during NULL_AUTHORITY. The lapse epoch recording code was unreachable.

**Fix:** Moved RSA lapse epoch recording to the main loop's NULL_AUTHORITY handler:
```python
# In main loop, during NULL_AUTHORITY
if self._cycle % self._config.renewal_check_interval == 0:
    # RSA: record lapse epoch (no commitment evaluation, 0 targets)
    if self._rsa_adversary is not None and self._rsa_telemetry is not None:
        global_epoch = self._compute_global_epoch()
        record = self._rsa_adversary.create_lapse_epoch_record(global_epoch)
        self._rsa_telemetry.record_epoch(record)
```

**Verification:**
```
RSA epochs_in_lapse: 68
Harness total_lapse_duration_epochs: 68
Match: ✓
```

### 1.2 C2: Aggregation Level Confusion (FIXED)

**Problem:** Report mixed per-seed and aggregate metrics without clear labels.

**Fix:** New sweep script reports both levels explicitly:

**Per-Seed Output:**
```
Seed 40: lapses=7, lapse_epochs=18, uptime=91.1%, flips=121, pivotal=45
```

**Aggregate Output:**
```
Aggregate: targets=2910, flips=562, pivotal=282, obs_ppm=193127
Mean: lapses=3.2, lapse_epochs=6.0, uptime=97.0%
```

### 1.3 C3: Low-Sensitivity Regime (ADDRESSED)

**Problem:** All outcome metrics were constant across flip rates because baseline SEM_PASS was 100% FALSE. The working mind emits only WAIT actions, which never satisfy commitment verifiers.

**Fix:** Added `synthetic_verifier_enabled` mode to ALSConfigV080:
```python
class ALSConfigV080(ALSConfigV070):
    # Synthetic verifier mode for RSA stress testing
    synthetic_verifier_enabled: bool = False
    synthetic_sem_pass_rate_ppm: int = 800_000  # 80% per-Ci pass rate
```

When enabled, `_compute_sem_pass()` uses deterministic probabilistic outcomes:
- 80% per-Ci pass rate → 0.8³ ≈ 51.2% SEM_PASS rate
- Allows RSA flips to meaningfully degrade TRUE→FALSE

---

## 2. Corrected DoS Sweep Results

### 2.1 Configuration

```python
ALSConfigV080(
    max_cycles=10_000,
    eligibility_threshold_k=3,
    max_successive_renewals=3,
    amnesty_interval=10,
    amnesty_decay=1,
    cta_enabled=True,
    synthetic_verifier_enabled=True,
    synthetic_sem_pass_rate_ppm=800_000,
)
```

Seeds: [40, 41, 42, 43, 44]

### 2.2 Results Summary

| p_flip (PPM) | p_flip (%) | Mean Lapses | Mean Lapse Epochs | Mean Uptime | Sum Flips | Sum Pivotal | Regime |
|--------------|------------|-------------|-------------------|-------------|-----------|-------------|--------|
| 0 | 0.00 | 0.0 | 0.0 | 100.0% | 0 | 0 | 5×ROBUST |
| 5,000 | 0.50 | 0.0 | 0.0 | 100.0% | 20 | 12 | 5×ROBUST |
| 10,000 | 1.00 | 0.0 | 0.0 | 100.0% | 27 | 18 | 5×ROBUST |
| 20,000 | 2.00 | 0.2 | 0.2 | 99.9% | 67 | 42 | 5×ROBUST |
| 50,000 | 5.00 | 0.2 | 0.2 | 99.9% | 159 | 97 | 5×ROBUST |
| 100,000 | 10.00 | 1.0 | 1.0 | 99.5% | 280 | 166 | 5×ROBUST |
| 200,000 | 20.00 | 3.2 | 6.0 | 97.0% | 562 | 282 | 5×ROBUST |

### 2.3 Key Metrics Definitions

- **Sum Flips:** Total flip events across all 5 seeds (aggregate)
- **Sum Pivotal:** Flips that changed SEM_PASS outcome (TRUE→FALSE or FALSE→TRUE)
- **Mean Lapse Epochs:** Average epochs spent in NULL_AUTHORITY per seed
- **Regime:** Classification per run (ROBUST / DEGRADED / DOS_REGIME)

### 2.4 Pivotal Flip Analysis

Not all flips change outcomes. A flip on Ci when other Cj are FALSE cannot change SEM_PASS:

| p_flip | Total Flips | Pivotal Flips | Pivotal Rate |
|--------|-------------|---------------|--------------|
| 5% | 159 | 97 | 61% |
| 10% | 280 | 166 | 59% |
| 20% | 562 | 282 | 50% |

The pivotal rate decreases at higher flip rates because more epochs have multiple Ci flipped, where only one flip per epoch can be the "pivotal" one.

---

## 3. Hook Location Verification

### 3.1 Causal Path Proof

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

### 3.2 Invariant Check

For runs with pivotal flips, verify `SEM_PASS_raw != SEM_PASS_corrupted` implies streak change differs from raw expectation:

```
epoch=6: SEM_PASS raw=True, corrupted=False → streak 0->1 (would be 0->0 without RSA)
epoch=17: SEM_PASS raw=True, corrupted=False → streak 0->1 (would be 0->0 without RSA)
```

✓ Hook is correctly upstream of streak mutation.

---

## 4. Epoch Clock Alignment

### 4.1 Clock Definition

RSA uses `global_epoch = cycle // renewal_check_interval`:
- Monotonically increasing (never resets)
- Matches semantic evaluation cadence

The harness uses `self._epoch_index` which resets per-authority. RSA does NOT use this.

### 4.2 Alignment Verification

```python
# In _update_streak_at_epoch_end():
global_epoch = self._compute_global_epoch()
# ...
c0_ok, c1_ok, c2_ok, sem_pass, rsa_record = self._rsa_adversary.corrupt(
    epoch=global_epoch,  # Uses global epoch
    ...
)
```

The same `global_epoch` is used for:
1. RSA flip decisions (`stable_hash_64(seed_rsa, epoch, key, stage)`)
2. Telemetry recording

✓ Epoch clock is consistent between RSA and harness.

---

## 5. Remaining Caveats

### 5.1 Synthetic Verifier Limitation

The synthetic verifier mode is a testing tool, not a production configuration. Real commitment verification depends on the working mind emitting appropriate actions (LOG, STATE_SET/GET, SEQUENCE, etc.).

To test RSA with real commitment verification, the working mind must be configured to emit commitment-satisfying actions.

### 5.2 Regime Classification

Current regime classification uses conservative thresholds:
- DOS_REGIME: max single lapse > 5 × amnesty_interval epochs
- DEGRADED: lapse_fraction > 50%
- ROBUST: otherwise

At 20% flip rate, no runs crossed these thresholds (all ROBUST). Higher flip rates or lower synthetic pass rates may be needed to observe DOS_REGIME.

### 5.3 Sensitivity Analysis Pending

The following additional experiments are recommended:
1. Lower synthetic pass rates (e.g., 60% per-Ci → 21.6% SEM_PASS)
2. Higher flip rates (30%, 50%)
3. Longer horizons (50k+ cycles)
4. SEM_PASS_ONLY scope comparison

---

## 6. Files Modified/Created

### Created (v0.1.1):
- `scripts/rsa_run0_dos_sweep_v011.py` - Corrected sweep script

### Modified (v0.1.1):
- `toy_aki/als/harness.py`:
  - Added `synthetic_verifier_enabled` and `synthetic_sem_pass_rate_ppm` to ALSConfigV080
  - Added `_compute_sem_pass()` override in ALSHarnessV080 for synthetic verifier
  - Fixed RSA lapse epoch recording in main loop

---

## Appendix: Verification Commands

```bash
# Corrected DoS sweep
python3 scripts/rsa_run0_dos_sweep_v011.py

# Verify lapse epoch consistency
python3 -c "
from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa import RSAConfig, RSANoiseModel

config = ALSConfigV080(max_cycles=10000, synthetic_verifier_enabled=True)
rsa_cfg = RSAConfig(rsa_enabled=True, rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI, rsa_p_flip_ppm=100000)

h = ALSHarnessV080(seed=40, config=config, rsa_config=rsa_cfg)
result = h.run()

print(f'RSA epochs_in_lapse: {result.rsa[\"summary\"][\"epochs_in_lapse\"]}')
print(f'Harness total_lapse_duration_epochs: {result.total_lapse_duration_epochs}')
assert result.rsa['summary']['epochs_in_lapse'] == result.total_lapse_duration_epochs
print('✓ Match')
"

# Verify pivotal flips affect streaks
python3 -c "
from toy_aki.als.harness import ALSHarnessV080, ALSConfigV080
from toy_aki.rsa import RSAConfig, RSANoiseModel

config = ALSConfigV080(max_cycles=5000, synthetic_verifier_enabled=True)
rsa_cfg = RSAConfig(rsa_enabled=True, rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI, rsa_p_flip_ppm=50000)

h = ALSHarnessV080(seed=42, config=config, rsa_config=rsa_cfg)
result = h.run()

pivotal = [r for r in h._rsa_telemetry.epoch_records if not r.in_lapse and r.sem_pass_raw != r.sem_pass_corrupted]
print(f'Pivotal flips: {len(pivotal)}')
for p in pivotal[:3]:
    print(f'  epoch={p.epoch}: SEM_PASS {p.sem_pass_raw} -> {p.sem_pass_corrupted}')
"
```
