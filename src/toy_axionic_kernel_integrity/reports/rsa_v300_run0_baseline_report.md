# RSA v3.0 Run 0: Baseline Reference (No Adversary)

**Implementation Report**

**Version:** v3.0.0 Run 0
**Date:** 2026-01-08
**Status:** ✅ PASS — Equivalence Confirmed

---

## 1. Purpose

Run 0 establishes the **clean reference baseline** for all RSA v3.0 experiments
under the exact frozen AKI configuration, horizon, and seed set used in Runs 1a/1b/2/3.

**Research question:**

> *What does governance look like with **no stateful adversarial policy layer** under the v3.0 experimental setup?*

This run anchors **AA / AAA / RTD** (and renewal/eligibility diagnostics) so all
subsequent v3.0 degradation claims are comparative, not absolute.

**Gate function:**

1. What is the baseline governance behavior under the frozen v3.0 execution
   parameters (300k cycles, 6000 epochs, 10 seeds)?
2. Does enabling RSA v3.0 policy with model=NONE introduce any observable behavioral
   divergence (enabled-path contamination)?
3. Is the RSA v3.0 layer behaviorally inert when set to NONE?

---

## 2. Terminology Definitions

| Term | Definition |
|------|------------|
| **AKI kernel** | The frozen `ALSHarnessV080` + `ALSConfigV080` implementing constitutional mechanics |
| **RSA v3.0 policy layer** | Stateful adversarial layer with 6 observables, 5 action primitives, bounded FSM state |
| **Epoch** | One governance evaluation cycle; `global_epoch = cycle // renewal_check_interval` |
| **Horizon** | Total epochs in run: `max_cycles // renewal_check_interval` = 6000 |
| **Tail window** | `max(5000, horizon // 5)` epochs for AAA computation = 5000 |
| **AA (PPM)** | Authority Availability: fraction of epochs with active authority, in parts per million |
| **AAA (PPM)** | Asymptotic Authority Availability: AA computed over tail window only |
| **RTD** | Recovery Time Distribution: histogram of lapse durations by bucket |
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
| `renewal_check_interval` | 50 |
| `eligibility_threshold_k` | 3 |
| `amnesty_interval` | 10 |
| `amnesty_decay` | 1 |
| `cta_enabled` | True |
| **Horizon epochs** | 6,000 |
| **Tail window** | 5,000 |
| **ALSConfig Parameter Hash** | `fd58b6e5` |

### 3.2 RSA v3.0 Configuration

**Condition A:** RSA policy disabled (`rsa_policy_config=None`)

**Condition B:**
| Parameter | Value |
|-----------|-------|
| `policy_model` | `NONE` |
| `epoch_size` | 50 |
| `override_count` | 0 (confirmed) |

The NONE model is a pass-through that does not intercept or modify agent
action proposals. It exercises the full RSA v3.0 policy wrapper code path
without altering behavior.

### 3.3 Seeds (Frozen Protocol Fingerprint)

10 seeds (v3.0 canonical set): `[42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]`

### 3.4 Protocol Fingerprint

| Component | Hash / Value |
|-----------|--------------|
| **Protocol Version** | RSA v3.0 (RSA-SA-0) |
| **Base Layer** | AKI v0.8 (ALS-A) |
| **ALSConfig Parameter Hash** | `fd58b6e5` |
| **Acceptance Tests** | 8/8 PASS |

---

## 4. Results

### 4.1 Condition A — RSA Policy Disabled (True Baseline)

| Seed | AA (PPM) | AAA (PPM) | Failure Class | Lapses | Lapse Epochs | Max Lapse | Renewal Rate |
|------|----------|-----------|---------------|--------|--------------|-----------|--------------|
| 42 | 666,183 | 666,183 | HORIZON_EXHAUSTED | 5 | 2,003 | 1,010 | 990,242 |
| 137 | 665,183 | 665,183 | HORIZON_EXHAUSTED | 5 | 2,009 | 1,010 | 990,228 |
| 256 | 666,180 | 666,180 | HORIZON_EXHAUSTED | 4 | 2,003 | 1,010 | 990,242 |
| 512 | 665,846 | 665,846 | HORIZON_EXHAUSTED | 4 | 2,005 | 1,010 | 990,237 |
| 1024 | 666,183 | 666,183 | HORIZON_EXHAUSTED | 5 | 2,003 | 1,010 | 990,242 |
| 2048 | 664,863 | 664,863 | HORIZON_EXHAUSTED | 9 | 2,011 | 910 | 990,223 |
| 4096 | 665,190 | 665,190 | HORIZON_EXHAUSTED | 7 | 2,009 | 1,010 | 990,228 |
| 8192 | 666,023 | 666,023 | HORIZON_EXHAUSTED | 7 | 2,004 | 1,000 | 990,240 |
| 16384 | 665,853 | 665,853 | HORIZON_EXHAUSTED | 6 | 2,005 | 1,010 | 990,237 |
| 32768 | 665,516 | 665,516 | HORIZON_EXHAUSTED | 5 | 2,007 | 1,010 | 990,232 |

**Aggregate:**
- Mean AA: 665,702 PPM (66.57%)
- Std AA: 483.9 PPM
- Mean Lapses: 5.70
- Total Lapses: 57
- Mean Renewal Rate: 990,235 PPM (99.02%)
- Mean Ineligibility Fraction: 33.43%
- Failure Classes: 10/10 HORIZON_EXHAUSTED

### 4.2 Condition B — RSA Policy Enabled, model=NONE

| Seed | AA (PPM) | AAA (PPM) | Failure Class | Lapses | Lapse Epochs | Max Lapse | Renewal Rate |
|------|----------|-----------|---------------|--------|--------------|-----------|--------------|
| 42 | 666,183 | 666,183 | HORIZON_EXHAUSTED | 5 | 2,003 | 1,010 | 990,242 |
| 137 | 665,183 | 665,183 | HORIZON_EXHAUSTED | 5 | 2,009 | 1,010 | 990,228 |
| 256 | 666,180 | 666,180 | HORIZON_EXHAUSTED | 4 | 2,003 | 1,010 | 990,242 |
| 512 | 665,846 | 665,846 | HORIZON_EXHAUSTED | 4 | 2,005 | 1,010 | 990,237 |
| 1024 | 666,183 | 666,183 | HORIZON_EXHAUSTED | 5 | 2,003 | 1,010 | 990,242 |
| 2048 | 664,863 | 664,863 | HORIZON_EXHAUSTED | 9 | 2,011 | 910 | 990,223 |
| 4096 | 665,190 | 665,190 | HORIZON_EXHAUSTED | 7 | 2,009 | 1,010 | 990,228 |
| 8192 | 666,023 | 666,023 | HORIZON_EXHAUSTED | 7 | 2,004 | 1,000 | 990,240 |
| 16384 | 665,853 | 665,853 | HORIZON_EXHAUSTED | 6 | 2,005 | 1,010 | 990,237 |
| 32768 | 665,516 | 665,516 | HORIZON_EXHAUSTED | 5 | 2,007 | 1,010 | 990,232 |

**Aggregate:**
- Mean AA: 665,702 PPM (66.57%)
- Std AA: 483.9 PPM
- Mean Lapses: 5.70
- Total Lapses: 57
- Mean Renewal Rate: 990,235 PPM (99.02%)
- Mean Ineligibility Fraction: 33.43%
- Failure Classes: 10/10 HORIZON_EXHAUSTED

### 4.3 RSA Policy Integrity (Condition B)

| Metric | Value |
|--------|-------|
| `rsa_enabled` | True |
| `rsa_model` | NONE |
| `override_count` | 0 |

✓ Confirmed: no action overrides occurred

---

## 5. Recovery Time Distribution (RTD)

### 5.1 RTD Per Seed — Condition A

| Seed | Mean | Median | Max | Non-zero Buckets |
|------|------|--------|-----|------------------|
| 42 | 400.6 | 1.0 | 1,010 | {1: 3, 1000: 1, 2000: 1} |
| 137 | 401.8 | 5.0 | 1,010 | {2: 2, 5: 1, 1000: 1, 2000: 1} |
| 256 | 500.8 | 496.0 | 1,010 | {1: 1, 2: 1, 1000: 1, 2000: 1} |
| 512 | 501.2 | 496.5 | 1,010 | {2: 1, 3: 1, 1000: 1, 2000: 1} |
| 1024 | 400.6 | 1.0 | 1,010 | {1: 3, 1000: 1, 2000: 1} |
| 2048 | 223.4 | 3.0 | 910 | {1: 2, 2: 2, 3: 1, 100: 2, 1000: 2} |
| 4096 | 287.0 | 2.0 | 1,010 | {1: 2, 2: 2, 3: 1, 1000: 1, 2000: 1} |
| 8192 | 286.3 | 1.0 | 1,000 | {1: 4, 10: 1, 1000: 2} |
| 16384 | 334.2 | 1.5 | 1,010 | {1: 3, 2: 1, 1000: 1, 2000: 1} |
| 32768 | 401.4 | 5.0 | 1,010 | {1: 2, 5: 1, 1000: 1, 2000: 1} |

### 5.2 Aggregate RTD (Both Conditions — Identical)

| Metric | Value |
|--------|-------|
| Total lapses | 57 |
| Mean recovery time | 351.91 epochs |
| Median recovery time | 2.00 epochs |
| Min recovery time | 1 epoch |
| Max recovery time | 1,010 epochs |
| Stdev recovery time | 473.71 epochs |

**Histogram:**

| Bucket | Count |
|--------|-------|
| 1 | 20 |
| 2 | 9 |
| 3 | 3 |
| 5 | 2 |
| 10 | 1 |
| 100 | 2 |
| 1000 | 12 |
| 2000 | 8 |

**Interpretation:** The RTD is bimodal:
- **Quick recoveries** (buckets 1–10): 35 lapses (61%) — system recovers within 10 epochs
- **Extended lapses** (buckets 1000–2000): 20 lapses (35%) — prolonged authority gaps

---

## 6. Equivalence Verification

### 6.1 Per-Seed Comparison (14 Metrics)

Per the binding decision in the v3.0 protocol, the following 14 metrics must
match exactly between Condition A and Condition B for each seed:

1. `AA_ppm`
2. `AAA_ppm`
3. `failure_class`
4. `lapse_count`
5. `total_lapse_epochs`
6. `max_single_lapse_epochs`
7. `epochs_evaluated`
8. `epochs_in_lapse`
9. `renewal_check_epochs_count`
10. `renewals_succeeded`
11. `renewal_success_rate_ppm`
12. `ever_ineligible`
13. `ineligibility_fraction_ppm`
14. `rtd_histogram` (all 14 buckets)

### 6.2 Verification Results

| Seed | All 14 Metrics Match | Result |
|------|----------------------|--------|
| 42 | ✓ | **MATCH** |
| 137 | ✓ | **MATCH** |
| 256 | ✓ | **MATCH** |
| 512 | ✓ | **MATCH** |
| 1024 | ✓ | **MATCH** |
| 2048 | ✓ | **MATCH** |
| 4096 | ✓ | **MATCH** |
| 8192 | ✓ | **MATCH** |
| 16384 | ✓ | **MATCH** |
| 32768 | ✓ | **MATCH** |

| Status | **✅ EQUIVALENCE CONFIRMED** |
|--------|------------------------------|

---

## 7. Key Observations

### 7.1 Consistency with RSA v2.0 Run 0

| Metric | RSA v2.0 Run 0 | RSA v3.0 Run 0 | Delta |
|--------|----------------|----------------|-------|
| Mean AA | 665,702 PPM | 665,702 PPM | 0 |
| Mean AAA | 665,702 PPM | 665,702 PPM | 0 |
| Mean Lapses | 5.70 | 5.70 | 0 |
| Failure Classes | 10/10 HE | 10/10 HE | Match |
| Config Hash | `fd58b6e5` | `fd58b6e5` | Match |

**v3.0 Run 0 is bit-for-bit identical to v2.0 Run 0**, confirming:
1. The v3.0 stateful machinery introduces no side effects when inert
2. Cross-version comparability is preserved
3. Baseline anchoring is valid

### 7.2 Homogeneous Seed Behavior

All 10 seeds show consistent behavior:
- AA range: 664,863 – 666,183 PPM (spread of 1,320 PPM, ~0.2%)
- Lapse range: 4 – 9 lapses
- No outliers or anomalous seeds

### 7.3 High Renewal Success Rate

All seeds show ~99.02% renewal success rate, indicating healthy baseline
governance mechanics under CTA (Constitutional Temporal Amnesty).

---

## 8. Baseline Reference Values

These values serve as the reference for Runs 1a/1b/2/3:

### 8.1 Full Aggregate (10 seeds)

| Metric | Value | Notes |
|--------|-------|-------|
| Mean AA | 665,702 PPM | 66.57% |
| Std AA | 483.9 PPM | Very low variance |
| Min AA | 664,863 PPM | Seed 2048 |
| Max AA | 666,183 PPM | Seeds 42, 1024 |
| Mean Lapses | 5.70 | Per 6000-epoch run |
| Total Lapses | 57 | Across all seeds |
| Mean Renewal Rate | 990,235 PPM | 99.02% |
| Mean Ineligibility Fraction | 33.43% | |
| Failure Classes | 10/10 HORIZON_EXHAUSTED | No terminal failures |

### 8.2 RTD Reference

| Metric | Value |
|--------|-------|
| Mean Recovery Time | 351.91 epochs |
| Median Recovery Time | 2.00 epochs |
| Max Single Lapse | 1,010 epochs |
| Quick Recovery (≤10 epochs) | 61% of lapses |
| Extended Lapse (≥1000 epochs) | 35% of lapses |

---

## 9. Equivalence Gate Status

### 9.1 Gate Definition

Per the v3.0 protocol, Run 0 is a **hard gate**:

> ✅ **PASS** if and only if Condition A == Condition B **per seed** on all 14
> required metrics (including RTD histogram).
> ❌ **FAIL** otherwise (stop; do not proceed to Runs 1a/1b/2/3).

### 9.2 Gate Result

| Gate | Status |
|------|--------|
| Run 0 Equivalence Gate | **✅ PASS** |

**RSA layer is behaviorally inert when set to NONE.**

**Proceed to Runs 1a/1b/2/3.**

---

## 10. Defensible Claim

> **Under the frozen RSA v3.0 execution parameters (300k cycles, 6000 epochs,
> K=3, amnesty_interval=10, 10 seeds), the baseline AKI v0.8 system exhibits:**
>
> - Authority Availability: 66.57% (665,702 PPM) aggregate
> - Asymptotic Authority Availability: 66.57% (665,702 PPM) aggregate
> - Failure Classification: 100% HORIZON_EXHAUSTED (no terminal failures)
> - Mean lapse count: 5.70 events per run
> - Mean recovery time: 351.91 epochs (median: 2 epochs)
> - Renewal success rate: 99.02%
>
> **Enabling RSA v3.0 policy with model=NONE produces zero behavioral divergence
> from RSA-disabled execution on all 14 required metrics (including RTD) across
> all 10 seeds, confirming enabled-path contamination is absent.**

---

## 11. Artifacts

| File | Description |
|------|-------------|
| `scripts/rsa_v300_run0_baseline.py` | Run 0 execution script (canonical) |
| `v3_run0_baseline.py` | Shim to canonical script |
| `reports/rsa_v300_run0_baseline_report.md` | This report |
| `reports/rsa_v030_implementation_report.md` | v3.0 implementation report |

---

## 12. Run 0 Definition of Done

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Frozen AKI v0.8 configuration documented | ✅ |
| 2 | Horizon = 6000 epochs (300k cycles) | ✅ |
| 3 | Tail window = 5000 epochs | ✅ |
| 4 | 10 seeds executed: [42, 137, ..., 32768] | ✅ |
| 5 | Condition A (RSA policy disabled) complete | ✅ |
| 6 | Condition B (RSA policy NONE) complete | ✅ |
| 7 | A/B equivalence verified per-seed (14 metrics including RTD) | ✅ |
| 8 | RTD per-seed and aggregate reported | ✅ |
| 9 | Baseline reference values documented | ✅ |
| 10 | Enabled-path contamination absent | ✅ CONFIRMED |
| 11 | override_count = 0 confirmed | ✅ |
| 12 | Gate status: PASS → proceed to Runs 1a/1b/2/3 | ✅ |

---

## Appendix A: Protocol Fingerprint

```
Protocol Version: RSA v3.0 (RSA-SA-0)
Base Layer: AKI v0.8 (ALS-A)
ALSConfig Hash: fd58b6e5
Seeds: [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
Horizon: 300,000 cycles = 6,000 epochs
Tail Window: 5,000 epochs
Acceptance Tests: 8/8 PASS
Equivalence Gate: PASS
```

---

**RUN 0 COMPLETE. EQUIVALENCE GATE: ✅ PASS.**
