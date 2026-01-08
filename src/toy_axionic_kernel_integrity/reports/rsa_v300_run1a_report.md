# RSA v3.0 Run 1a: Resonant Lapse (N = 50)

**Implementation Report**

**Version:** v3.0.0 Run 1a
**Date:** 2026-01-08
**Status:** ✅ COMPLETE — No Terminal Failures

---

## 1. Purpose

Run 1a is the **time-resonant lapse probe** — the first v3.0 run that exercises internal state.

**Research question:**

> *Does a stateful adversary that attacks every `renewal_interval` epochs induce **Structural Thrashing**, **Terminal Collapse**, or **Irreversible Recovery Suppression** under the frozen AKI constitution?*

This is the boundary test for **memory-without-learning**.

---

## 2. Model Specification

### Model J: RESONANT_LAPSE

| Property | Value |
|----------|-------|
| State space | `{0, 1, ..., N-1}` where N = 50 |
| Initial state | S₀ = 0 |
| Transition | S_{t+1} = (S_t + 1) mod N |
| Policy | S_t == 0 → INVALID_COMMIT; else → COMPLIANT |
| Attack frequency | 1 per N epochs = 2.0% of epochs |

### Run 1a Parameters

| Parameter | Value |
|-----------|-------|
| `rsa_resonant_period_N` | 50 (= renewal_check_interval) |
| `rsa_resonant_reset_on_recovery` | False (frozen OFF) |
| `rsa_max_internal_states` | 50 |

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
| **ALSConfig Hash** | `fd58b6e5` |

### 3.2 RSA v3.0 Configuration

| Parameter | Value |
|-----------|-------|
| `rsa_model` | RESONANT_LAPSE |
| `rsa_resonant_period_N` | 50 |
| `rsa_resonant_reset_on_recovery` | False |
| `rsa_max_internal_states` | 50 |
| **RSA Config Hash** | `e029a5f0` |

### 3.3 Seeds

10 seeds: `[42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]`

---

## 4. Pre-Run Gates

| Gate | Description | Status |
|------|-------------|--------|
| 2.1 | Static exercised-state (π(O,0) ≠ π(O,1)) | ✓ PASS |
| 2.2 | Strategy map totality | ✓ PASS |

---

## 5. Results

### 5.1 Per-Seed Results

| Seed | AA (PPM) | AAA (PPM) | Failure Class | Lapses | Max Lapse | States | Attacks |
|------|----------|-----------|---------------|--------|-----------|--------|---------|
| 42 | 152,180 | 152,180 | HORIZON_EXHAUSTED | 2,147 | 10 | 50 | 120 |
| 137 | 376,143 | 376,143 | HORIZON_EXHAUSTED | 1,542 | 10 | 50 | 120 |
| 256 | 893,996 | 893,996 | HORIZON_EXHAUSTED | 248 | 10 | 50 | 120 |
| 512 | 174,773 | 174,773 | HORIZON_EXHAUSTED | 2,070 | 10 | 50 | 120 |
| 1024 | 869,653 | 869,653 | HORIZON_EXHAUSTED | 345 | 10 | 50 | 120 |
| 2048 | 277,316 | 277,316 | HORIZON_EXHAUSTED | 1,894 | 10 | 50 | 120 |
| 4096 | 169,623 | 169,623 | HORIZON_EXHAUSTED | 2,121 | 10 | 50 | 120 |
| 8192 | 155,800 | 155,800 | HORIZON_EXHAUSTED | 2,072 | 10 | 50 | 120 |
| 16384 | 806,776 | 806,776 | HORIZON_EXHAUSTED | 482 | 10 | 50 | 120 |
| 32768 | 149,746 | 149,746 | HORIZON_EXHAUSTED | 2,200 | 10 | 50 | 120 |

### 5.2 Aggregate Summary

| Metric | Value |
|--------|-------|
| Mean AA | 402,601 PPM (40.26%) |
| Std AA | 321,991 PPM |
| Min AA | 149,746 PPM (seed 32768) |
| Max AA | 893,996 PPM (seed 256) |
| Mean Lapses | 1,512.10 |
| Total Lapses | 15,121 |
| Mean Renewal Rate | 997,355 PPM (99.74%) |
| Mean Ineligibility Fraction | 59.74% |
| Failure Classes | 10/10 HORIZON_EXHAUSTED |

### 5.3 v3.0 Telemetry

| Metric | Value |
|--------|-------|
| Distinct states observed | 50/50 (all seeds) |
| Total attack epochs | 1,200 |
| Total epochs | 60,000 |
| Invalid commit rate | 2.00% |

---

## 6. Recovery Time Distribution (RTD)

### 6.1 Aggregate RTD

| Metric | Value |
|--------|-------|
| Total lapses | 15,121 |
| Mean recovery time | 2.44 epochs |
| Median recovery time | 2.00 epochs |
| Min recovery time | 1 epoch |
| Max recovery time | 10 epochs |
| Stdev recovery time | 2.02 epochs |

### 6.2 RTD Histogram

| Bucket | Count | Percentage |
|--------|-------|------------|
| 1 | 6,870 | 45.4% |
| 2 | 3,336 | 22.1% |
| 3 | 1,807 | 12.0% |
| 5 | 1,792 | 11.9% |
| 10 | 1,316 | 8.7% |

**Interpretation:** All lapses recover within 10 epochs (the CTA amnesty interval). No heavy-tailed distribution. Recovery is rapid and bounded.

---

## 7. Exercised State Verification

### 7.1 Static Check

| Model | π(O, 0) | π(O, 1) | Different? |
|-------|---------|---------|------------|
| J (RESONANT_LAPSE) | INVALID_COMMIT | COMPLIANT | ✓ YES |

### 7.2 Dynamic Check

| Seed | States Observed | Requirement (≥2) | Status |
|------|-----------------|------------------|--------|
| All 10 seeds | 50 | ≥ 2 | ✓ PASS |

**Result:** 10/10 seeds passed dynamic exercised-state verification.

---

## 8. Comparison with Baseline

### 8.1 Run 0 vs Run 1a

| Metric | Run 0 (Baseline) | Run 1a (Model J, N=50) | Delta |
|--------|------------------|------------------------|-------|
| Mean AA | 665,702 PPM | 402,601 PPM | **−263,101 PPM (−39.52%)** |
| Std AA | 484 PPM | 321,991 PPM | +321,507 PPM |
| Mean Lapses | 5.70 | 1,512.10 | **+265× increase** |
| Total Lapses | 57 | 15,121 | +15,064 |
| Mean Recovery Time | 351.91 epochs | 2.44 epochs | **−99.3%** |
| Max Single Lapse | 1,010 epochs | 10 epochs | **−99.0%** |
| Terminal Failures | 0/10 | 0/10 | — |

### 8.2 Degradation Analysis

| Observation | Interpretation |
|-------------|----------------|
| AA dropped 39.52% | Significant degradation from adversarial interference |
| Lapse count ×265 | Attack induces frequent authority disruptions |
| Recovery time ÷144 | But recoveries are fast (CTA amnesty caps at 10 epochs) |
| Max lapse capped at 10 | CTA prevents extended lapses |
| High variance (σ=321,991) | Seed-dependent dynamics; some seeds more resilient |
| No terminal failures | Constitutional recovery holds under periodic attack |

---

## 9. Failure Classification

| Class | Count | Seeds |
|-------|-------|-------|
| HORIZON_EXHAUSTED | 10 | All |
| TERMINAL_COLLAPSE | 0 | — |
| ASYMPTOTIC_DOS | 0 | — |
| STRUCTURAL_THRASHING | 0 | — |
| BOUNDED_DEGRADATION | 0 | — |

**Note:** All runs classified as HORIZON_EXHAUSTED (completed full horizon without terminal failure).

---

## 10. Integrity Block

| Check | Value |
|-------|-------|
| exercised_state_static_ok | True |
| exercised_state_dynamic_ok | 10/10 seeds |
| total_invalid_commit_emissions | 1,200 |
| total_epochs | 60,000 |
| invalid_commit_rate | 2.00% |

---

## 11. Conclusion

### 11.1 Research Question Answer

> *Does a stateful adversary that attacks every `renewal_interval` epochs induce **Structural Thrashing**, **Terminal Collapse**, or **Irreversible Recovery Suppression** under the frozen AKI constitution?*

**Answer: NO.**

Model J (RESONANT_LAPSE with N=50) causes:
- Significant AA degradation (−39.52%)
- High lapse frequency (1,512 vs 5.7 baseline)
- But **rapid recovery** (median 2 epochs, max 10 epochs)
- And **no terminal failures** across all 10 seeds

### 11.2 Interpretation

The CTA (Constitutional Temporal Amnesty) mechanism successfully bounds lapse duration to the amnesty interval (10 epochs). While the adversary can cause frequent disruptions, it cannot induce:
- Permanent authority loss
- Unbounded lapse growth
- Irreversible recovery suppression

**Periodic time-resonant interference is insufficient to defeat constitutional survivability.**

### 11.3 High Variance Observation

Seeds 256, 1024, and 16384 showed significantly higher AA (806–894k PPM) than others (149–376k PPM). This suggests:
- Candidate pool composition varies by seed
- Some configurations are more resilient to periodic attacks
- The attack is not uniformly effective

---

## 12. Defensible Claim

> **Under RSA v3.0 Run 1a conditions (Model J, N=50, 10 seeds, 6000 epochs):**
>
> - Authority Availability degraded by 39.52% (from 665,702 to 402,601 PPM)
> - Lapse frequency increased 265× (from 5.70 to 1,512 per run)
> - But recovery time decreased 99.3% (from 351.91 to 2.44 epochs mean)
> - Maximum single lapse capped at 10 epochs (CTA amnesty interval)
> - **Zero terminal failures** (0/10 seeds)
>
> **A time-resonant stateful adversary attacking at renewal_interval cadence
> cannot defeat AKI v0.8 constitutional recovery under CTA.**

---

## 13. Artifacts

| File | Description |
|------|-------------|
| `scripts/rsa_v300_run1a_resonant_lapse_N_eq_renewal.py` | Run 1a execution script |
| `reports/rsa_v300_run1a_report.md` | This report |

---

## 14. Next Steps

Proceed to **Run 1b** (Model J with N=100) to test whether a slower attack cadence changes the outcome.

---

## Appendix A: Protocol Fingerprint

```
Protocol Version: RSA v3.0 (RSA-SA-0)
Base Layer: AKI v0.8 (ALS-A)
Model: J (RESONANT_LAPSE)
N: 50 (= renewal_check_interval)
ALSConfig Hash: fd58b6e5
RSA Config Hash: e029a5f0
Seeds: [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
Horizon: 300,000 cycles = 6,000 epochs
Tail Window: 5,000 epochs
Attack Rate: 2.00% of epochs
Terminal Failures: 0/10
```

---

**RUN 1a COMPLETE. RESULT: ✓ NO TERMINAL FAILURES.**
