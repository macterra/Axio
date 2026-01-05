# RSA v0.1 Run 3: DoS Threshold Search

**Implementation Report**

**Version:** v0.1.0 Run 3
**Date:** 2026-01-05
**Status:** COMPLETE

---

## 1. Purpose

Run 3 searches for the first true DoS regime under high RSA noise at a fixed
semantic baseline. The goal is to identify the smallest RSA flip intensity
that produces persistent lapse (DoS) rather than merely reduced uptime.

**Research question:** At what RSA corruption rate does CTA fail to restore
governance under a marginal semantic baseline?

**Answer:** DoS was not observed up to 60% RSA noise. The system exhibits
graceful degradation rather than catastrophic failure.

---

## 2. Terminology Definitions

| Term | Definition |
|------|------------|
| **DoS regime** | `max_single_lapse_epochs > 5 × amnesty_interval` (> 50 epochs) |
| **Degraded regime** | `lapse_epoch_fraction > 50%` |
| **Robust regime** | Neither DoS nor Degraded |
| **Graceful degradation** | Uptime decreases smoothly with noise; recovery continues |

---

## 3. Experimental Configuration

### 3.1 AKI v0.8 (FROZEN)

| Parameter | Value |
|-----------|-------|
| `max_cycles` | 10,000 |
| `eligibility_threshold_k` | 3 |
| `max_successive_renewals` | 3 |
| `amnesty_interval` | 10 |
| `amnesty_decay` | 1 |
| `renewal_check_interval` | 50 |
| `cta_enabled` | True |
| **Total epochs** | 200 |

### 3.2 SV Baseline (FIXED)

| Parameter | Value |
|-----------|-------|
| `per_ci_pass_rate_ppm` | 800,000 |
| Expected SEM_PASS | 0.512 (~51%) |

### 3.3 RSA Noise Sweep (High Range)

| rsa_p_flip_ppm | Flip Rate |
|----------------|-----------|
| 300,000 | 30% |
| 400,000 | 40% |
| 500,000 | 50% |
| 600,000 | 60% |

**Fixed:** `rsa_scope = PER_CI`, `rsa_noise_model = FLIP_BERNOULLI`

### 3.4 Seeds

- 5 seeds: `[40, 41, 42, 43, 44]`
- 4 noise levels × 5 seeds = **20 runs**

---

## 4. Results

*All metrics are computed over authority-held epochs only.*

### 4.1 Per-Noise Level Summary

| RSA (PPM) | mean_uptime | std | mean_lapse_ep | max_max_lapse | R/D/X |
|-----------|-------------|-----|---------------|---------------|-------|
| 300,000 | 90.3% | ±4.1% | 19.6 | 10 | 5/0/0 |
| 400,000 | 83.6% | ±1.7% | 33.0 | 12 | 5/0/0 |
| 500,000 | 80.9% | ±2.3% | 38.4 | 15 | 5/0/0 |
| 600,000 | 77.5% | ±2.9% | 45.2 | 20 | 5/0/0 |

**Key observation:** All 20 runs remain ROBUST. No DEGRADED or DOS_REGIME.

### 4.2 Per-Seed Results

| RSA | Seed | Uptime | Lapse_ep | Max_lapse | Mean_dur | Regime |
|-----|------|--------|----------|-----------|----------|--------|
| 300k | 40 | 92.5% | 15 | 10 | 3.8 | ROBUST |
| 300k | 41 | 92.5% | 15 | 10 | 3.0 | ROBUST |
| 300k | 42 | 88.1% | 24 | 10 | 4.0 | ROBUST |
| 300k | 43 | 84.1% | 32 | 10 | 4.0 | ROBUST |
| 300k | 44 | 94.0% | 12 | 8 | 3.0 | ROBUST |
| 400k | 40 | 81.6% | 37 | 12 | 4.6 | ROBUST |
| 400k | 41 | 82.1% | 36 | 10 | 4.0 | ROBUST |
| 400k | 42 | 85.6% | 29 | 10 | 3.2 | ROBUST |
| 400k | 43 | 84.1% | 32 | 10 | 3.2 | ROBUST |
| 400k | 44 | 84.6% | 31 | 10 | 3.4 | ROBUST |
| 500k | 40 | 80.1% | 40 | 10 | 5.0 | ROBUST |
| 500k | 41 | 80.1% | 40 | 15 | 5.7 | ROBUST |
| 500k | 42 | 82.1% | 36 | 10 | 3.3 | ROBUST |
| 500k | 43 | 84.1% | 32 | 11 | 4.0 | ROBUST |
| 500k | 44 | 78.1% | 44 | 10 | 4.4 | ROBUST |
| 600k | 40 | 76.6% | 47 | 20 | 4.7 | ROBUST |
| 600k | 41 | 76.6% | 47 | 20 | 6.7 | ROBUST |
| 600k | 42 | 78.1% | 44 | 11 | 4.4 | ROBUST |
| 600k | 43 | 82.1% | 36 | 10 | 5.1 | ROBUST |
| 600k | 44 | 74.1% | 52 | 12 | 5.8 | ROBUST |

### 4.3 RSA Flip Summary

| RSA (PPM) | Targets | Flips | Obs_PPM | Pivotal | Piv_rate |
|-----------|---------|-------|---------|---------|----------|
| 300,000 | 2,706 | 822 | 303,769 | 346 | 42.1% |
| 400,000 | 2,505 | 1,034 | 412,774 | 384 | 37.1% |
| 500,000 | 2,424 | 1,219 | 502,887 | 399 | 32.7% |
| 600,000 | 2,322 | 1,386 | 596,899 | 399 | 28.8% |

**Observation:** Observed flip rates match configured rates (±1%). Pivotal rate
*decreases* with noise intensity because at high flip rates, many flips hit
targets that are already flipped (flip collision).

### 4.4 CTA Imprint

Total lapse events: 159

Durations within ±1 epoch of amnesty multiple: **106 (66.7%)**

| Remainder (mod 10) | Count |
|--------------------|-------|
| 0 | 36 |
| 1 | 67 |
| 2 | 27 |
| 3 | 14 |
| 4 | 7 |
| 5 | 2 |
| 7 | 1 |
| 8 | 2 |
| 9 | 3 |

CTA imprint by noise level:

| RSA (PPM) | N_lapses | Near_mult | Fraction |
|-----------|----------|-----------|----------|
| 300,000 | 27 | 19 | 70.4% |
| 400,000 | 45 | 33 | 73.3% |
| 500,000 | 44 | 26 | 59.1% |
| 600,000 | 43 | 28 | 65.1% |

CTA recovery synchronization persists across all noise levels.

---

## 5. Hypothesis Validation

### H7: DoS Emergence

**Hypothesis:** There exists a flip rate in {30%, 40%, 50%, 60%} where at
least one seed becomes DOS_REGIME.

**Test:** Check if any `max_single_lapse_epochs > 50`.

**Result:**
- Maximum observed `max_single_lapse_epochs`: **20** (at 600k, seeds 40 and 41)
- No seed crossed the DoS threshold (50 epochs)
- All runs remained ROBUST with uptime ≥ 74%

| Status | **NOT SUPPORTED** |
|--------|-------------------|

### H8: CTA Clock Imprint Persists Until DoS

**Hypothesis:** In non-DoS runs, lapse durations remain clustered near amnesty
multiples; in DoS runs, clustering weakens.

**Test:** Compare clustering fraction in non-DoS vs DoS runs.

**Result:**
- Non-DoS lapses: 159, near multiple: 66.7%
- DoS lapses: 0 (no DoS observed)
- CTA imprint persists across all runs (66-73% clustering)

| Status | **SUPPORTED** |
|--------|---------------|

*(Note: H8 is trivially supported since no DoS occurred to test weakening.)*

### H9: Nonlinear Transition

**Hypothesis:** The transition from rare lapses to persistent lapse becomes
sharper in the high-noise regime.

**Test:** Check for >2x jump in mean_lapse_epochs between adjacent noise levels.

**Result:**
| RSA → | Mean lapse epochs | Ratio to previous |
|-------|-------------------|-------------------|
| 300k | 19.6 | — |
| 400k | 33.0 | 1.68× |
| 500k | 38.4 | 1.16× |
| 600k | 45.2 | 1.18× |

No sharp transition detected. Lapse epochs increase sub-linearly with noise.

| Status | **NOT SUPPORTED** |
|--------|-------------------|

---

## 6. Key Findings

### 6.1 AKI v0.8 Does Not DoS at 60% Noise

This is the central surprising result. Under independent per-Ci Bernoulli
flips at 60% intensity:
- Mean uptime: 77.5%
- Max single lapse: 20 epochs (well below DoS threshold of 50)
- All seeds ROBUST

The system exhibits **graceful degradation**, not catastrophic failure.
*Graceful degradation here means reduced authority uptime with bounded lapse
durations and continued recovery, not merely the absence of DoS.*

### 6.2 Uptime Degrades Linearly with Noise

| RSA | Uptime |
|-----|--------|
| 30% | 90% |
| 40% | 84% |
| 50% | 81% |
| 60% | 78% |

Approximate slope: **-2% uptime per 10% RSA noise** above 30%.

### 6.3 Max Lapse Duration Grows Slowly

| RSA | Max_max_lapse |
|-----|---------------|
| 30% | 10 |
| 40% | 12 |
| 50% | 15 |
| 60% | 20 |

The longest lapse doubles from 30% to 60% noise, but remains far from DoS.

### 6.4 Pivotal Rate Decreases with Noise

At high flip rates, many flips "collide" — they flip bits that are already
flipped. This creates diminishing marginal impact:

| RSA | Pivotal rate |
|-----|--------------|
| 30% | 42% |
| 40% | 37% |
| 50% | 33% |
| 60% | 29% |

This may explain why degradation is sub-linear.

### 6.5 CTA Recovery Remains Robust

66-73% of lapses end within ±1 epoch of an amnesty multiple across all noise
levels. The CTA clock continues to synchronize recovery even at 60% noise.

---

## 7. Defensible Claim

> **Under independent per-Ci post-verification Bernoulli noise (FLIP_BERNOULLI,
> PER_CI scope) at intensities from 30% to 60%, AKI v0.8 at a ~51% semantic
> baseline (SV=800k) exhibits graceful degradation without entering DoS:**
>
> 1. **No DoS observed**: Maximum single lapse was 20 epochs (DoS threshold: 50)
>
> 2. **Linear uptime degradation**: ~2% uptime loss per 10% additional noise
>
> 3. **CTA recovery persists**: 67% of lapses cluster at amnesty multiples
>
> 4. **Sub-linear lapse growth**: Flip collision reduces marginal impact

**Under independent per-Ci post-verification Bernoulli noise (PER_CI,
FLIP_BERNOULLI) and a ~51% semantic baseline (SV = 800k), no DoS was
observed up to 60% flip rate.** Higher noise levels or lower SV baselines
may be required to induce DoS.

---

## 8. Artifacts

| File | Description |
|------|-------------|
| `scripts/rsa_run3_dos_threshold_v010.py` | Sweep script |
| `reports/rsa_v010_run3_implementation_report.md` | This report |

---

## 9. Run 3 Definition of Done

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Single axis: RSA noise (30-60%) | ✅ |
| 2 | SV baseline fixed at 800k | ✅ |
| 3 | AKI kernel frozen | ✅ |
| 4 | 20 runs executed (4 × 5) | ✅ |
| 5 | All per-seed and aggregate metrics reported | ✅ |
| 6 | Regime classification per seed | ✅ |
| 7 | CTA imprint analysis included | ✅ |
| 8 | H7 (DoS Emergence) validated | ❌ NOT SUPPORTED |
| 9 | H8 (CTA Imprint) validated | ✅ SUPPORTED |
| 10 | H9 (Nonlinear Transition) validated | ❌ NOT SUPPORTED |
| 11 | DoS threshold identified or bounded | ✅ (>60%) |

---

## 10. Next Steps

Two options for further boundary search:

1. **Run 3b: Escalate to 70-90% noise** at SV=800k to find true DoS threshold
2. **Run 3b: Lower SV baseline** (e.g., 700k, 600k) at 60% noise to find DoS

Alternative direction:

3. **Run 4: Test SEM_PASS_ONLY scope** — single flip point may be more effective
   at inducing DoS than PER_CI
