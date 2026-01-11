# RSA v0.2 Run 0: Baseline Reference (No Interference)

**Implementation Report**

**Version:** v0.2.0 Run 0
**Date:** 2026-01-06
**Status:** COMPLETE

---

## 1. Purpose

Run 0 establishes the clean reference baseline for all RSA v0.2 experiments.
This run verifies that the RSA stress layer, when enabled with zero flip
probability, produces behavior identical to RSA-disabled execution.

**Research questions:**

1. What is the baseline governance behavior under the frozen v0.2 execution
   parameters (300k cycles, 6000 epochs)?
2. Does enabling RSA with p=0 introduce any observable behavioral divergence
   (enabled-path contamination)?

---

## 2. Terminology Definitions

| Term | Definition |
|------|------------|
| **AKI kernel** | The frozen `ALSHarnessV080` + `ALSConfigV080` implementing constitutional mechanics |
| **RSA stress layer** | Removable adversarial layer injecting controlled noise into aggregator output |
| **Epoch** | One governance evaluation cycle; `global_epoch = cycle // renewal_check_interval` |
| **Horizon** | Total epochs in run: `max_cycles // renewal_check_interval` |
| **Tail window** | `max(5000, horizon // 5)` epochs for AAA computation |
| **AA (PPM)** | Authority Availability: fraction of epochs with active authority, in parts per million |
| **AAA (PPM)** | Asymptotic Authority Availability: AA computed over tail window only |
| **Lapse** | A contiguous sequence of epochs in NULL_AUTHORITY state |
| **Condition A** | RSA disabled (true clean baseline) |
| **Condition B** | RSA enabled with p_flip=0 (enabled-path equivalence test) |

---

## 3. Experimental Configuration

### 3.1 AKI v0.8 (FROZEN)

| Parameter | Value |
|-----------|-------|
| `max_cycles` | 300,000 |
| `eligibility_threshold_k` | 3 |
| `max_successive_renewals` | 3 |
| `amnesty_interval` | 10 |
| `amnesty_decay` | 1 |
| `renewal_check_interval` | 50 |
| `cta_enabled` | True |
| **Horizon epochs** | 6,000 |
| **Tail window** | 5,000 |

### 3.2 RSA Configuration

**Condition A:** RSA disabled (`rsa_config=None`)

**Condition B:**
| Parameter | Value |
|-----------|-------|
| `rsa_enabled` | True |
| `rsa_noise_model` | `AGG_FLIP_BERNOULLI` |
| `rsa_scope` | `SEM_PASS_ONLY` |
| `rsa_p_flip_ppm` | 0 |
| `rsa_rng_stream` | `"rsa_v020"` |

### 3.3 Seeds

5 seeds: `[40, 41, 42, 43, 44]`

---

## 4. Results

### 4.1 Condition A — RSA Disabled (True Baseline)

| Seed | AA (PPM) | AAA (PPM) | Failure Class | Lapses | Max Lapse |
|------|----------|-----------|---------------|--------|-----------|
| 40 | 597,333 | 592,400 | BOUNDED_DEGRADATION | 168 | 40 |
| 41 | 601,000 | 595,600 | BOUNDED_DEGRADATION | 152 | 40 |
| 42 | 597,333 | 591,800 | BOUNDED_DEGRADATION | 158 | 40 |
| 43 | 597,333 | 592,400 | BOUNDED_DEGRADATION | 151 | 40 |
| 44 | 597,333 | 590,400 | BOUNDED_DEGRADATION | 161 | 40 |

**Aggregate:**
- Mean AA: 598,066 PPM (59.81%)
- Mean AAA: 592,520 PPM (59.25%)
- Failure Class: 5/5 BOUNDED_DEGRADATION

### 4.2 Condition B — RSA Enabled, p=0

| Seed | AA (PPM) | AAA (PPM) | Failure Class | Lapses | Max Lapse |
|------|----------|-----------|---------------|--------|-----------|
| 40 | 597,333 | 592,400 | BOUNDED_DEGRADATION | 168 | 40 |
| 41 | 601,000 | 595,600 | BOUNDED_DEGRADATION | 152 | 40 |
| 42 | 597,333 | 591,800 | BOUNDED_DEGRADATION | 158 | 40 |
| 43 | 597,333 | 592,400 | BOUNDED_DEGRADATION | 151 | 40 |
| 44 | 597,333 | 590,400 | BOUNDED_DEGRADATION | 161 | 40 |

**Aggregate:**
- Mean AA: 598,066 PPM (59.81%)
- Mean AAA: 592,520 PPM (59.25%)
- Failure Class: 5/5 BOUNDED_DEGRADATION

### 4.3 RSA Integrity Metrics (Condition B)

| Seed | Targets | Flips | Flip Rate PPM |
|------|---------|-------|---------------|
| 40 | 3,584 | 0 | 0 |
| 41 | 3,607 | 0 | 0 |
| 42 | 3,584 | 0 | 0 |
| 43 | 3,584 | 0 | 0 |
| 44 | 3,584 | 0 | 0 |

All seeds: Zero flips, confirming p=0 produces no interference.

### 4.4 Recovery Time Distribution (Aggregate)

| Bucket (≤N epochs) | Count |
|--------------------|-------|
| ≤1 | 289 |
| ≤2 | 92 |
| ≤3 | 41 |
| ≤5 | 59 |
| ≤10 | 29 |
| ≤20 | 7 |
| ≤50 | 273 |

Total lapse events: 790 (both conditions identical)

*Note: Max lapse of 40 epochs falls in the ≤50 bucket. The ≤50 bucket contains
lapses from 21-50 epochs inclusive.*

---

## 5. Equivalence Verification

### 5.1 Per-Seed Comparison

| Seed | AA Match | AAA Match | Lapses Match | Max Lapse Match | Result |
|------|----------|-----------|--------------|-----------------|--------|
| 40 | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 41 | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 42 | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 43 | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 44 | ✓ | ✓ | ✓ | ✓ | **MATCH** |

### 5.2 Additional Invariants Verified

| Metric | Condition A | Condition B | Match |
|--------|-------------|-------------|-------|
| s_star | All match | All match | ✓ |
| total_cycles | All match | All match | ✓ |
| recovery_count | All match | All match | ✓ |
| amnesty_event_count | All match | All match | ✓ |
| authority_uptime_cycles | All match | All match | ✓ |
| total_renewals | All match | All match | ✓ |
| semantic_lapse_count | All match | All match | ✓ |
| structural_lapse_count | All match | All match | ✓ |

| Status | **EQUIVALENCE CONFIRMED** |
|--------|---------------------------|

---

## 6. Hypothesis Validation

### H0: Enabled-Path Contamination Absent

**Hypothesis:** Enabling RSA with p_flip=0 produces behavior identical to
RSA-disabled execution (no extra RNG draws, no ordering changes, no state
contamination).

**Test:** Compare all governance metrics between Condition A and Condition B
for each seed.

**Result:** Perfect match across all 5 seeds on all tracked metrics.

| Status | **SUPPORTED** |
|--------|---------------|

---

## 7. Key Findings

### 7.1 Baseline Governance Behavior

Under the frozen v0.2 execution parameters (300k cycles, 6000 epochs):

- **Authority Availability:** ~60% (598k PPM)
- **Asymptotic Authority Availability:** ~59% (592k PPM)
- **Failure Classification:** All seeds: BOUNDED_DEGRADATION
- **Lapse Frequency:** ~150-170 lapses per run
- **Max Lapse Duration:** 40 epochs (consistent across all seeds)

### 7.2 RTD Bimodal Distribution

The Recovery Time Distribution shows a bimodal pattern:
- **Quick recoveries** (1-3 epochs): 422 events (53.4%)
- **Extended recoveries** (>20 epochs): 280 events (35.4%)

The 40-epoch max lapse is near the `50` bucket boundary, suggesting
CTA amnesty clock synchronization effects (amnesty_interval=10, so
recovery often occurs at multiples of 10 epochs).

### 7.3 Enabled-Path Cleanliness

The RSA stress layer with p=0 produces zero observable behavioral divergence:
- Zero flips generated
- All governance metrics identical
- No RNG state contamination

This confirms the RSA implementation maintains clean separation from AKI
kernel mechanics.

---

## 8. Baseline Reference Values

These values serve as the reference for Runs 1-3:

| Metric | Value | Notes |
|--------|-------|-------|
| Mean AA | 598,066 PPM | 59.81% |
| Mean AAA | 592,520 PPM | 59.25% |
| Mean Lapses | 158 | Per 6000-epoch run |
| Max Lapse | 40 epochs | Consistent across seeds |
| Failure Class | BOUNDED_DEGRADATION | All seeds |
| RSA Targets | ~3,590 | Total aggregator evaluations (one per epoch under authority) |

**Interpretation:** The underlying AKI v0.8 system with K=3, amnesty_interval=10
exhibits approximately 60% authority availability under normal operation. Any
RSA-induced degradation in Runs 1-3 will be measured against this baseline.

---

## 9. Defensible Claim

> **Under the frozen RSA v0.2 execution parameters (300k cycles, 6000 epochs,
> K=3, amnesty_interval=10), the baseline AKI v0.8 system exhibits:**
>
> - Authority Availability: 59.8% (598,066 PPM)
> - Asymptotic Authority Availability: 59.3% (592,520 PPM)
> - Failure Classification: BOUNDED_DEGRADATION
> - Mean lapse count: 158 events per run
> - Maximum single lapse: 40 epochs
>
> **Enabling RSA with p_flip=0 produces zero behavioral divergence from
> RSA-disabled execution, confirming enabled-path contamination is absent.**

---

## 10. Artifacts

| File | Description |
|------|-------------|
| `scripts/rsa_v020_run0_baseline_reference.py` | Run 0 execution script |
| `reports/rsa_v020_run0_baseline_report.md` | This report |
| `docs/rsa_instructions_v0.2_runner0.md` | Runner instructions |

---

## 11. Run 0 Definition of Done

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Frozen AKI v0.8 configuration documented | ✅ |
| 2 | Horizon = 6000 epochs (300k cycles) | ✅ |
| 3 | Tail window = 5000 epochs | ✅ |
| 4 | 5 seeds executed: [40, 41, 42, 43, 44] | ✅ |
| 5 | Condition A (RSA disabled) complete | ✅ |
| 6 | Condition B (RSA p=0) complete | ✅ |
| 7 | A/B equivalence verified per-seed | ✅ |
| 8 | RSA integrity metrics: zero flips confirmed | ✅ |
| 9 | Baseline reference values documented | ✅ |
| 10 | Enabled-path contamination absent | ✅ SUPPORTED |

---

**BASELINE ESTABLISHED.**
