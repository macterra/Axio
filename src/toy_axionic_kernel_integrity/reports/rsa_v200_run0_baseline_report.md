# RSA v2.0 Run 0: Baseline Equivalence Gate

**Implementation Report**

**Version:** v2.0.0 Run 0
**Date:** 2026-01-08
**Status:** ✅ PASS — Equivalence Confirmed

---

## 1. Purpose

Run 0 establishes the clean reference baseline for all RSA v2.0 experiments
and serves as the **equivalence gate** that must pass before Runs 1–4 can proceed.

**Research questions:**

1. What is the baseline governance behavior under the frozen v2.0 execution
   parameters (300k cycles, 6000 epochs, 10 seeds)?
2. Does enabling RSA v2.0 policy with model=NONE introduce any observable behavioral
   divergence (enabled-path contamination)?
3. Is the RSA v2.0 layer behaviorally inert when set to NONE?

---

## 2. Terminology Definitions

| Term | Definition |
|------|------------|
| **AKI kernel** | The frozen `ALSHarnessV080` + `ALSConfigV080` implementing constitutional mechanics |
| **RSA v2.0 policy layer** | Adversarial layer with 6 observables, 5 action primitives, and bounded adaptive state |
| **Epoch** | One governance evaluation cycle; `global_epoch = cycle // renewal_check_interval` |
| **Horizon** | Total epochs in run: `max_cycles // renewal_check_interval` = 6000 |
| **Tail window** | `max(5000, horizon // 5)` epochs for AAA computation |
| **AA (PPM)** | Authority Availability: fraction of cycles with active authority, in parts per million |
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
| `renewal_check_interval` | 50 |
| `eligibility_threshold_k` | 3 |
| `amnesty_interval` | 10 |
| `amnesty_decay` | 1 |
| `cta_enabled` | True |
| **Horizon epochs** | 6,000 |
| **Tail window** | 5,000 |
| **Config hash** | `fd58b6e5` |

### 3.2 RSA v2.0 Configuration

**Condition A:** RSA policy disabled (`rsa_policy_config=None`)

**Condition B:**
| Parameter | Value |
|-----------|-------|
| `policy_model` | `NONE` |
| `epoch_size` | 50 |

The NONE model is a pass-through that does not intercept or modify agent
action proposals. It exercises the full RSA v2.0 policy wrapper code path
without altering behavior.

### 3.3 Seeds (Frozen Protocol Fingerprint)

10 seeds (v2.0 canonical set): `[42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]`

### 3.4 Protocol Fingerprint

| Component | Hash / Value |
|-----------|--------------|
| **AKI Config Hash** | `fd58b6e5` |
| **RSA v2.0 Config Hash** | `4e20b327` |
| **Observable Interface Hash** | `9afe2362` |
| **Strategy Map Hash** | `9661d09d` |
| **Primitive Map Hash** | `e3268435` |

---

## 4. Results

### 4.1 Condition A — RSA Policy Disabled (True Baseline)

| Seed | AA (PPM) | AAA (PPM) | Failure Class | Lapses | Lapse Epochs | Renewals OK | Renewal Rate |
|------|----------|-----------|---------------|--------|--------------|-------------|--------------|
| 42 | 666,183 | 666,183 | HORIZON_EXHAUSTED | 5 | 2,003 | 3,958 | 990,242 |
| 137 | 665,183 | 665,183 | HORIZON_EXHAUSTED | 5 | 2,009 | 3,952 | 990,228 |
| 256 | 666,180 | 666,180 | HORIZON_EXHAUSTED | 4 | 2,003 | 3,958 | 990,242 |
| 512 | 665,846 | 665,846 | HORIZON_EXHAUSTED | 4 | 2,005 | 3,956 | 990,237 |
| 1024 | 666,183 | 666,183 | HORIZON_EXHAUSTED | 5 | 2,003 | 3,958 | 990,242 |
| 2048 | 664,863 | 664,863 | HORIZON_EXHAUSTED | 9 | 2,011 | 3,950 | 990,223 |
| 4096 | 665,190 | 665,190 | HORIZON_EXHAUSTED | 7 | 2,009 | 3,952 | 990,228 |
| 8192 | 666,023 | 666,023 | HORIZON_EXHAUSTED | 7 | 2,004 | 3,957 | 990,240 |
| 16384 | 665,853 | 665,853 | HORIZON_EXHAUSTED | 6 | 2,005 | 3,956 | 990,237 |
| 32768 | 665,516 | 665,516 | HORIZON_EXHAUSTED | 5 | 2,007 | 3,954 | 990,232 |

**Aggregate:**
- Mean AA: 665,702 PPM (66.57%)
- Std AA: 484 PPM
- Mean Lapses: 5.70
- Mean Renewal Rate: 990,235 PPM (99.02%)
- Failure Classes: 10/10 HORIZON_EXHAUSTED

### 4.2 Condition B — RSA Policy Enabled, model=NONE

| Seed | AA (PPM) | AAA (PPM) | Failure Class | Lapses | Lapse Epochs | Renewals OK | Renewal Rate |
|------|----------|-----------|---------------|--------|--------------|-------------|--------------|
| 42 | 666,183 | 666,183 | HORIZON_EXHAUSTED | 5 | 2,003 | 3,958 | 990,242 |
| 137 | 665,183 | 665,183 | HORIZON_EXHAUSTED | 5 | 2,009 | 3,952 | 990,228 |
| 256 | 666,180 | 666,180 | HORIZON_EXHAUSTED | 4 | 2,003 | 3,958 | 990,242 |
| 512 | 665,846 | 665,846 | HORIZON_EXHAUSTED | 4 | 2,005 | 3,956 | 990,237 |
| 1024 | 666,183 | 666,183 | HORIZON_EXHAUSTED | 5 | 2,003 | 3,958 | 990,242 |
| 2048 | 664,863 | 664,863 | HORIZON_EXHAUSTED | 9 | 2,011 | 3,950 | 990,223 |
| 4096 | 665,190 | 665,190 | HORIZON_EXHAUSTED | 7 | 2,009 | 3,952 | 990,228 |
| 8192 | 666,023 | 666,023 | HORIZON_EXHAUSTED | 7 | 2,004 | 3,957 | 990,240 |
| 16384 | 665,853 | 665,853 | HORIZON_EXHAUSTED | 6 | 2,005 | 3,956 | 990,237 |
| 32768 | 665,516 | 665,516 | HORIZON_EXHAUSTED | 5 | 2,007 | 3,954 | 990,232 |

**Aggregate:**
- Mean AA: 665,702 PPM (66.57%)
- Std AA: 484 PPM
- Mean Lapses: 5.70
- Mean Renewal Rate: 990,235 PPM (99.02%)
- Failure Classes: 10/10 HORIZON_EXHAUSTED

---

## 5. Equivalence Verification

### 5.1 Per-Seed Comparison (13 Metrics)

Per the binding decision in the v2.0 protocol, the following 13 metrics must
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
13. `ineligibility_fraction`

### 5.2 Verification Results

| Seed | All 13 Metrics Match | Result |
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

## 6. Key Observations

### 6.1 Comparison with RSA v1.0 Run 0

| Metric | RSA v1.0 Run 0 | RSA v2.0 Run 0 | Delta |
|--------|----------------|----------------|-------|
| Mean AA | 637,949 PPM | 665,702 PPM | +27,753 PPM |
| Mean AAA | 632,380 PPM | 665,702 PPM | +33,322 PPM |
| Mean Lapses | ~159 | 5.70 | −153 |
| Failure Classes | 9 BD, 1 SA | 10 HE | Different classification |

**Note:** The v2.0 baseline shows significantly better governance health than v1.0.
This is expected due to underlying harness/kernel evolution between experimental
runs. The key property is internal consistency (A=B equivalence), not cross-version
comparability.

### 6.2 No Seed 2048 Outlier

Unlike RSA v1.0 Run 0, which exhibited a dramatic seed 2048 outlier (99.98% AA vs
~59.7% for other seeds), the v2.0 baseline shows homogeneous behavior across all
10 seeds. This suggests different candidate pool dynamics in the current harness
configuration.

### 6.3 High Renewal Success Rate

All seeds show ~99.02% renewal success rate, with 3,950–3,958 successful renewals
out of ~3,997 attempts (4,000 epochs ÷ renewal_check_interval approximation).

---

## 7. Baseline Reference Values

These values serve as the reference for Runs 1–4:

### 7.1 Full Aggregate (10 seeds)

| Metric | Value | Notes |
|--------|-------|-------|
| Mean AA | 665,702 PPM | 66.57% |
| Std AA | 484 PPM | Very low variance |
| Mean Lapses | 5.70 | Per 6000-epoch run |
| Mean Renewal Rate | 990,235 PPM | 99.02% |
| Failure Classes | 10/10 HORIZON_EXHAUSTED | No terminal failures |

### 7.2 Lapse Statistics

| Metric | Value |
|--------|-------|
| Min Lapses | 4 (seeds 256, 512) |
| Max Lapses | 9 (seed 2048) |
| Mean Lapse Epochs | 2,006 |

---

## 8. Equivalence Gate Status

### 8.1 Gate Definition

Per the v2.0 protocol, Run 0 is a **hard gate**:

> ✅ **PASS** if and only if Condition A == Condition B **per seed** on all 13
> required metrics.
> ❌ **FAIL** otherwise (stop; do not proceed to Runs 1–4).

### 8.2 Gate Result

| Gate | Status |
|------|--------|
| Run 0 Equivalence Gate | **✅ PASS** |

**RSA layer is behaviorally inert when set to NONE.**

**Proceed to Runs 1–4.**

---

## 9. Defensible Claim

> **Under the frozen RSA v2.0 execution parameters (300k cycles, 6000 epochs,
> K=3, amnesty_interval=10, 10 seeds), the baseline AKI v0.8 system exhibits:**
>
> - Authority Availability: 66.57% (665,702 PPM) aggregate
> - Asymptotic Authority Availability: 66.57% (665,702 PPM) aggregate
> - Failure Classification: 100% HORIZON_EXHAUSTED (no terminal failures)
> - Mean lapse count: 5.70 events per run
> - Renewal success rate: 99.02%
>
> **Enabling RSA v2.0 policy with model=NONE produces zero behavioral divergence
> from RSA-disabled execution on all 13 required metrics across all 10 seeds,
> confirming enabled-path contamination is absent.**

---

## 10. Artifacts

| File | Description |
|------|-------------|
| `run0_baseline.py` | Run 0 execution script |
| `reports/rsa_v200_run0_baseline_report.md` | This report |
| `reports/rsa_v200_implementation_report.md` | v2.0 implementation report |

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
| 7 | A/B equivalence verified per-seed (13 metrics) | ✅ |
| 8 | Baseline reference values documented | ✅ |
| 9 | Enabled-path contamination absent | ✅ CONFIRMED |
| 10 | Gate status: PASS → proceed to Runs 1–4 | ✅ |

---

**RUN 0 COMPLETE. EQUIVALENCE GATE: ✅ PASS.**
