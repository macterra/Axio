# RSA v1.0 Run 0: Baseline Reference (No Adversary)

**Implementation Report**

**Version:** v1.0.0 Run 0
**Date:** 2026-01-07
**Status:** COMPLETE

---

## 1. Purpose

Run 0 establishes the clean reference baseline for all RSA v1.0 experiments.
This run verifies that the RSA policy layer, when enabled with the NONE model,
produces behavior identical to RSA-disabled execution.

**Research questions:**

1. What is the baseline governance behavior under the frozen v1.0 execution
   parameters (300k cycles, 6000 epochs, 10 seeds)?
2. Does enabling RSA policy with model=NONE introduce any observable behavioral
   divergence (enabled-path contamination)?

---

## 2. Terminology Definitions

| Term | Definition |
|------|------------|
| **AKI kernel** | The frozen `ALSHarnessV080` + `ALSConfigV080` implementing constitutional mechanics |
| **RSA policy layer** | Adversarial layer controlling action emission via deterministic policy models |
| **Epoch** | One governance evaluation cycle; `global_epoch = cycle // renewal_check_interval` |
| **Horizon** | Total epochs in run: `max_cycles // renewal_check_interval` |
| **Tail window** | `max(5000, horizon // 5)` epochs for AAA computation |
| **AA (PPM)** | Authority Availability: fraction of epochs with active authority, in parts per million |
| **AAA (PPM)** | Asymptotic Authority Availability: AA computed over tail window only |
| **Lapse** | A contiguous sequence of epochs in NULL_AUTHORITY state |
| **Condition A** | RSA policy disabled (true clean baseline) |
| **Condition B** | RSA policy enabled with model=NONE (enabled-path equivalence test) |
| **NONE model** | Pass-through policy that does not modify agent actions |

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
| **Config hash** | `8e72fa7f` |

### 3.2 RSA v1.0 Configuration

**Condition A:** RSA policy disabled (`rsa_policy_config=None`)

**Condition B:**
| Parameter | Value |
|-----------|-------|
| `policy_model` | `NONE` |

The NONE model is a pass-through that does not intercept or modify agent
action proposals. It exercises the full RSA v1.0 policy wrapper code path
without altering behavior.

### 3.3 Seeds

10 seeds (v1.0 canonical set): `[42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]`

---

## 4. Results

### 4.1 Condition A — RSA Policy Disabled (True Baseline)

| Seed | AA (PPM) | AAA (PPM) | Failure Class | Lapses | Max Lapse |
|------|----------|-----------|---------------|--------|-----------|
| 42 | 597,333 | 591,800 | BOUNDED_DEGRADATION | 157 | 40 |
| 137 | 597,333 | 590,400 | BOUNDED_DEGRADATION | 167 | 40 |
| 256 | 597,833 | 590,000 | BOUNDED_DEGRADATION | 146 | 40 |
| 512 | 597,333 | 589,800 | BOUNDED_DEGRADATION | 154 | 40 |
| 1024 | 597,333 | 591,400 | BOUNDED_DEGRADATION | 174 | 40 |
| 2048 | 999,833 | 1,000,000 | STABLE_AUTHORITY | 0 | 0 |
| 4096 | 597,333 | 594,200 | BOUNDED_DEGRADATION | 170 | 40 |
| 8192 | 597,333 | 592,000 | BOUNDED_DEGRADATION | 159 | 40 |
| 16384 | 600,500 | 592,600 | BOUNDED_DEGRADATION | 153 | 40 |
| 32768 | 597,333 | 591,600 | BOUNDED_DEGRADATION | 156 | 40 |

**Aggregate:**
- Mean AA: 637,949 PPM (63.79%)
- Mean AAA: 632,380 PPM (63.24%)
- Failure Classes: 9 BOUNDED_DEGRADATION, 1 STABLE_AUTHORITY

### 4.2 Condition B — RSA Policy Enabled, model=NONE

| Seed | AA (PPM) | AAA (PPM) | Failure Class | Lapses | Max Lapse |
|------|----------|-----------|---------------|--------|-----------|
| 42 | 597,333 | 591,800 | BOUNDED_DEGRADATION | 157 | 40 |
| 137 | 597,333 | 590,400 | BOUNDED_DEGRADATION | 167 | 40 |
| 256 | 597,833 | 590,000 | BOUNDED_DEGRADATION | 146 | 40 |
| 512 | 597,333 | 589,800 | BOUNDED_DEGRADATION | 154 | 40 |
| 1024 | 597,333 | 591,400 | BOUNDED_DEGRADATION | 174 | 40 |
| 2048 | 999,833 | 1,000,000 | STABLE_AUTHORITY | 0 | 0 |
| 4096 | 597,333 | 594,200 | BOUNDED_DEGRADATION | 170 | 40 |
| 8192 | 597,333 | 592,000 | BOUNDED_DEGRADATION | 159 | 40 |
| 16384 | 600,500 | 592,600 | BOUNDED_DEGRADATION | 153 | 40 |
| 32768 | 597,333 | 591,600 | BOUNDED_DEGRADATION | 156 | 40 |

**Aggregate:**
- Mean AA: 637,949 PPM (63.79%)
- Mean AAA: 632,380 PPM (63.24%)
- Failure Classes: 9 BOUNDED_DEGRADATION, 1 STABLE_AUTHORITY

### 4.3 Renewal Metrics

| Seed | Renewals | Expirations | Total Checks | Rate (%) |
|------|----------|-------------|--------------|----------|
| 42 | 2,688 | 896 | 3,584 | 75.0 |
| 137 | 2,688 | 896 | 3,584 | 75.0 |
| 256 | 2,691 | 897 | 3,588 | 75.0 |
| 512 | 2,688 | 896 | 3,584 | 75.0 |
| 1024 | 2,688 | 896 | 3,584 | 75.0 |
| 2048 | 4,500 | 1,500 | 6,000 | 75.0 |
| 4096 | 2,688 | 896 | 3,584 | 75.0 |
| 8192 | 2,688 | 896 | 3,584 | 75.0 |
| 16384 | 2,703 | 901 | 3,604 | 75.0 |
| 32768 | 2,689 | 896 | 3,585 | 75.0 |

### 4.3.1 Renewal Failure Reason Breakdown

All expirations were examined to determine the cause of "renewal failure":

| Reason | Count | Percentage |
|--------|-------|------------|
| `max_successive_renewals` reached (=3) | 100% | All expirations |
| Ineligibility (streak ≥ K) | 0% | None |
| Insufficient budget | 0% | None |
| Other | 0% | None |

**Verified:** Every `ExpirationEvent` in the harness has `renewals_completed=3`,
confirming that all non-renewals are forced turnovers due to the
`max_successive_renewals=3` limit, not due to eligibility failure.

The 75% renewal rate is structural: 3 renewals per 4-epoch tenure cycle = 75%.

### 4.3.2 Global Semantic Failure Metrics

The following metrics describe semantic failure streak behavior. Note that the
streak is computed globally (does NOT reset on succession), measuring cumulative
governance quality rather than per-incumbent behavior.

| Seed | Ever Global SemFail ≥K | Global SemFail ≥K Fraction | Max Consec. Fail |
|------|------------------------|----------------------------|------------------|
| 42 | Yes | 0.999 | 3,584 |
| 137 | Yes | 0.999 | 3,584 |
| 256 | Yes | 0.999 | 3,588 |
| 512 | Yes | 0.999 | 3,584 |
| 1024 | Yes | 0.999 | 3,584 |
| 2048 | No | 0.000 | 0 |
| 4096 | Yes | 0.999 | 3,584 |
| 8192 | Yes | 0.999 | 3,584 |
| 16384 | Yes | 0.999 | 3,604 |
| 32768 | Yes | 0.999 | 3,585 |

**Definition clarification:**

- **Computed from:** Global `sem_pass` sequence (NOT per-incumbent)
- **Streak behavior:** Cumulative; does NOT reset when incumbent changes
- **Threshold criterion:** Current consecutive sem_fail count ≥ K (= 3)
- **Fraction meaning:** Proportion of epochs where cumulative fail streak ≥ K

**Why 99.9%?** Since all attack agents fail semantic verification (sem_pass=False
for all epochs), the fail streak grows to 3 immediately and never resets. Only
epochs 1-2 (streak=1,2) have streak < K; all remaining epochs have streak ≥ K.

**Caution:** This is a **global semantic failure saturation** metric, NOT renewal
eligibility. The kernel computes eligibility per-incumbent at renewal time. As
shown in §4.3.1, no renewals actually fail due to eligibility—all expirations
are from `max_successive_renewals`.

### 4.4 Recovery Time Distribution (Aggregate)

**Bucket semantics:** Disjoint ranges. Each bucket contains lapses with
duration in the range (previous_boundary, current_boundary].

| Bucket | Range (epochs) | Count |
|--------|----------------|-------|
| 1 | (0, 1] | 527 |
| 2 | (1, 2] | 189 |
| 3 | (2, 3] | 98 |
| 5 | (3, 5] | 78 |
| 10 | (5, 10] | 44 |
| 20 | (10, 20] | 17 |
| 50 | (20, 50] | 493 |

Total lapse events: 1,446 (across 9 seeds with lapses; seed 2048 has none)

**Bimodal pattern:**
- Quick recoveries (1-3 epochs): 814 events (56.3%)
- Extended recoveries (21-50 epochs): 493 events (34.1%)
- The 40-epoch max lapse is consistent with CTA amnesty_interval=10

---

## 5. Equivalence Verification

### 5.1 Per-Seed Comparison

| Seed | AA Match | AAA Match | Lapses Match | Max Lapse Match | Class Match | Result |
|------|----------|-----------|--------------|-----------------|-------------|--------|
| 42 | ✓ | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 137 | ✓ | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 256 | ✓ | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 512 | ✓ | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 1024 | ✓ | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 2048 | ✓ | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 4096 | ✓ | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 8192 | ✓ | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 16384 | ✓ | ✓ | ✓ | ✓ | ✓ | **MATCH** |
| 32768 | ✓ | ✓ | ✓ | ✓ | ✓ | **MATCH** |

| Status | **EQUIVALENCE CONFIRMED** |
|--------|---------------------------|

---

## 6. Seed 2048 Outlier Analysis

### 6.1 Observation

Seed 2048 exhibits dramatically different behavior from all other seeds:
- **AA:** 99.98% (vs ~59.7% for other seeds)
- **Lapses:** 0 (vs ~150-175 for other seeds)
- **Classification:** STABLE_AUTHORITY (vs BOUNDED_DEGRADATION)

### 6.2 Root Cause

Investigation revealed the difference stems from **candidate pool ordering**:

| Seed | First Successor Selected | Semantic Pass? | Outcome |
|------|--------------------------|----------------|---------|
| 42 | `attack:RUBBER_STAMP` | ❌ No | Streak grows → lapses occur |
| 2048 | `control:COMMITMENT_AWARE_V1` | ✅ Yes | Streak stays 0 → no lapses |

Seed 2048's RNG state causes the commitment-aware agent to be selected first
in the candidate pool. This agent correctly satisfies semantic commitments
(C0, C1, C2), keeping the streak at 0 and preventing any lapse throughout
the entire 6000-epoch horizon.

### 6.3 Interpretation

This is **expected behavior**, not a bug:
- The ALS candidate pool is shuffled deterministically based on seed
- When a commitment-satisfying agent is selected first, authority is maintained
- The 10-seed baseline exhibits **two deterministic attractors** induced by
  candidate pool ordering; the seed battery samples both
- This attractor bifurcation is exactly what RSA policies in Runs 1-5 will
  stress test (shifting probability mass between attractors)

---

## 7. Key Findings

### 7.1 Baseline Governance Behavior (Excluding Outlier)

Under the frozen v1.0 execution parameters, excluding seed 2048:

- **Authority Availability:** ~59.7% (597,463 PPM mean)
- **Asymptotic Authority Availability:** ~59.2% (591,533 PPM mean)
- **Failure Classification:** All 9 seeds: BOUNDED_DEGRADATION
- **Lapse Frequency:** ~146-174 lapses per run
- **Max Lapse Duration:** 40 epochs (consistent across all seeds)

### 7.2 Full Aggregate (Including Outlier)

Including seed 2048:

- **Mean AA:** 63.79% (637,949 PPM)
- **Mean AAA:** 63.24% (632,380 PPM)
- **Failure Classes:** 9 BOUNDED_DEGRADATION, 1 STABLE_AUTHORITY

### 7.3 RTD Bimodal Distribution

The Recovery Time Distribution shows a bimodal pattern:
- **Quick recoveries** (1-3 epochs): 814 events (56.3%)
- **Extended recoveries** (>20 epochs): 510 events (35.3%)

The 40-epoch max lapse is consistent across all degraded seeds, suggesting
CTA amnesty clock synchronization effects (amnesty_interval=10).

### 7.4 Enabled-Path Cleanliness

The RSA v1.0 policy layer with model=NONE produces zero observable behavioral
divergence:
- All governance metrics identical between Conditions A and B
- No RNG state contamination
- No ordering changes

This confirms the RSA v1.0 implementation maintains clean separation from
AKI kernel mechanics.

---

## 8. Baseline Reference Values

These values serve as the reference for Runs 1-5:

### 8.1 Full Aggregate (10 seeds)

| Metric | Value | Notes |
|--------|-------|-------|
| Mean AA | 637,949 PPM | 63.79% (includes outlier) |
| Mean AAA | 632,380 PPM | 63.24% (includes outlier) |
| Failure Classes | 9 BD, 1 SA | 90% bounded degradation |

### 8.2 Attractor A: Attack Agent First (9 seeds)

| Metric | Value | Notes |
|--------|-------|-------|
| Mean AA | ~597,500 PPM | ~59.75% |
| Mean AAA | ~591,500 PPM | ~59.15% |
| Mean Lapses | ~159 | Per 6000-epoch run |
| Max Lapse | 40 epochs | Consistent across all 9 seeds |
| Failure Class | BOUNDED_DEGRADATION | All 9 seeds |

### 8.3 Attractor B: Commitment-Aware First (seed 2048)

| Metric | Value | Notes |
|--------|-------|-------|
| AA | 999,833 PPM | 99.98% |
| AAA | 1,000,000 PPM | 100.00% |
| Lapses | 0 | Never enters lapse |
| Failure Class | STABLE_AUTHORITY | Commitment-aware agent selected first |

---

## 9. Defensible Claim

> **Under the frozen RSA v1.0 execution parameters (300k cycles, 6000 epochs,
> K=3, amnesty_interval=10, 10 seeds), the baseline AKI v0.8 system exhibits:**
>
> - Authority Availability: 63.8% (637,949 PPM) aggregate
> - Asymptotic Authority Availability: 63.2% (632,380 PPM) aggregate
> - Failure Classification: 90% BOUNDED_DEGRADATION, 10% STABLE_AUTHORITY
> - Mean lapse count: ~159 events per degraded run
> - Maximum single lapse: 40 epochs
>
> **The baseline exhibits two deterministic attractors induced by candidate
> pool ordering: attractor A (attack agent first → AA ≈ 59.7%) and attractor B
> (commitment-aware first → AA ≈ 99.98%). The 10-seed battery samples both.**
>
> **Enabling RSA policy with model=NONE produces zero behavioral divergence from
> RSA-disabled execution, confirming enabled-path contamination is absent.**

---

## 10. Artifacts

| File | Description |
|------|-------------|
| `scripts/rsa_v100_run0_baseline.py` | Run 0 execution script |
| `reports/rsa_v100_run0_baseline_report.md` | This report |
| `reports/rsa_v100_run0_baseline_20260107_105742.json` | Raw results JSON |
| `docs/rsa_instructions_v1.0_runner0.md` | Runner instructions |

---

## 11. Run 0 Definition of Done

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Frozen AKI v0.8 configuration documented | ✅ |
| 2 | Horizon = 6000 epochs (300k cycles) | ✅ |
| 3 | Tail window = 5000 epochs | ✅ |
| 4 | 10 seeds executed: [42, 137, ..., 32768] | ✅ |
| 5 | Condition A (RSA policy disabled) complete | ✅ |
| 6 | Condition B (RSA policy NONE) complete | ✅ |
| 7 | A/B equivalence verified per-seed | ✅ |
| 8 | Seed 2048 outlier analyzed and explained | ✅ |
| 9 | Baseline reference values documented | ✅ |
| 10 | Enabled-path contamination absent | ✅ SUPPORTED |

---

## 12. Performance Note

During Run 0 execution, an O(n²) performance bug was discovered and fixed
in `ALSHarnessV080._compute_commitment_keys_raw()`. The fix added epoch-indexed
action trace lookup (`_action_trace_by_epoch`) reducing per-epoch action
window queries from O(n) to O(window_size).

**Before fix:** Some seeds (137, 512, 2048) took 60s+ for 300k cycles
**After fix:** All seeds complete in ~2.6-3.1s consistently

This fix is transparent to experimental results and was applied prior to
final Run 0 execution.

---

**BASELINE ESTABLISHED.**
