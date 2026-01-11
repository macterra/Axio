# RSA v1.0 Run 1: Persistent Violation Sweep (Model A)

**Implementation Report**

**Version:** v1.0.0 Run 1
**Date:** 2026-01-07
**Status:** COMPLETE

---

## 1. Purpose

Run 1 evaluates whether deliberate, fixed, non-adaptive semantic sabotage by
an incumbent agent can induce constitutional failure under the frozen RSA v1.0
assumptions.

**Research question:**

> *Does persistent violation of a single required commitment suffice to defeat
> constitutional recovery, or does the system degrade in a bounded, recoverable way?*

This is the **first adversarial test** in v1.0. It does **not** test adaptation,
deception, or strategic timing.

---

## 2. Adversary Model

### Model A — Persistent Violation (`ALWAYS_FAIL_COMMITMENT`)

| Property | Value |
|----------|-------|
| Type | Fixed, deterministic, non-adaptive |
| Behavior | Always omits action(s) required for one designated commitment |
| Scope | Applied to ALL incumbents (control and attack successors) |
| Sweep axis | `target_commitment ∈ {C0, C1, C2}` |

**RSA v1.0 policy scope:** When enabled, the RSA policy wrapper applies to the
incumbent successor's `propose_action()` for all successor types, across all
successions, throughout the full run.

---

## 3. Experimental Configuration

### 3.1 AKI v0.8 (FROZEN — identical to Run 0)

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

### 3.2 RSA Policy Configuration

For each target commitment:

```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.ALWAYS_FAIL_COMMITMENT,
    target_commitment=TARGET,  # "C0" | "C1" | "C2"
    epoch_size=50,
)
```

### 3.3 Experimental Matrix

| Dimension | Values | Count |
|-----------|--------|-------|
| Target commitments | C0, C1, C2 | 3 |
| Seeds | 42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768 | 10 |
| **Total runs** | | **30** |

---

## 4. Results

### 4.1 Per-Target Summary

| Target | AA Mean (%) | AAA Mean (%) | Failure Class | Lapses Mean | Max Lapse | Failures |
|--------|-------------|--------------|---------------|-------------|-----------|----------|
| C0 | 59.77 | 59.15 | 10/10 BOUNDED_DEGRADATION | 158.6 | 40 | 0 |
| C1 | 59.77 | 59.15 | 10/10 BOUNDED_DEGRADATION | 158.6 | 40 | 0 |
| C2 | 59.77 | 59.15 | 10/10 BOUNDED_DEGRADATION | 158.6 | 40 | 0 |

**Key observation:** All three targets produce **identical results**.

### 4.2 Per-Seed Results (All Targets Identical)

| Seed | AA (%) | AAA (%) | Failure Class | Lapses | Max Lapse | Renewal Rate (%) |
|------|--------|---------|---------------|--------|-----------|------------------|
| 42 | 59.73 | 59.18 | BOUNDED_DEGRADATION | 157 | 40 | 75.00 |
| 137 | 59.73 | 59.04 | BOUNDED_DEGRADATION | 167 | 40 | 75.00 |
| 256 | 59.78 | 59.00 | BOUNDED_DEGRADATION | 146 | 40 | 75.00 |
| 512 | 59.73 | 58.98 | BOUNDED_DEGRADATION | 154 | 40 | 75.00 |
| 1024 | 59.73 | 59.14 | BOUNDED_DEGRADATION | 174 | 40 | 75.00 |
| 2048 | 59.77 | 59.08 | BOUNDED_DEGRADATION | 150 | 40 | 75.02 |
| 4096 | 59.73 | 59.42 | BOUNDED_DEGRADATION | 170 | 40 | 75.00 |
| 8192 | 59.73 | 59.20 | BOUNDED_DEGRADATION | 159 | 40 | 75.00 |
| 16384 | 60.05 | 59.26 | BOUNDED_DEGRADATION | 153 | 40 | 75.00 |
| 32768 | 59.73 | 59.16 | BOUNDED_DEGRADATION | 156 | 40 | 75.01 |

### 4.3 Seed 2048 Behavior Change

| Metric | Run 0 (No Adversary) | Run 1 (Model A) | Change |
|--------|----------------------|-----------------|--------|
| AA | 99.98% | 59.77% | -40.21 pp |
| AAA | 100.00% | 59.08% | -40.92 pp |
| Lapses | 0 | 150 | +150 |
| Failure Class | STABLE_AUTHORITY | BOUNDED_DEGRADATION | Degraded |

**Interpretation:** The RSA policy successfully overrides the commitment-aware
agent's behavior. Seed 2048 no longer exhibits attractor B behavior because the
policy forces omission of commitment actions regardless of the underlying agent.

### 4.4 Renewal Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Renewal success rate | 75.00% | Structural (3 renewals per 4-epoch cycle) |
| Total expirations | 8,966 | All targets identical |
| Expiration reason | 100% max_successive_renewals | Zero from ineligibility |

### 4.5 Global Semantic Failure Metrics

| Metric | Value |
|--------|-------|
| `ever_global_semfail_ge_k` | Yes (all 30 runs) |
| `global_semfail_ge_k_fraction` | 0.9994 |
| `max_consecutive_sem_fail` | ~3,584 (grows monotonically) |

### 4.6 Recovery Time Distribution (Aggregate per Target)

| Bucket | Range (epochs) | Count |
|--------|----------------|-------|
| 1 | (0, 1] | 575 |
| 2 | (1, 2] | 214 |
| 3 | (2, 3] | 108 |
| 5 | (3, 5] | 83 |
| 10 | (5, 10] | 50 |
| 20 | (10, 20] | 18 |
| 50 | (20, 50] | 548 |

Total lapses: 1,596 per target (across 10 seeds)

---

## 5. Analysis

### 5.1 Why Are All Targets Identical?

All three commitment targets (C0, C1, C2) produce identical governance outcomes.
This occurs because:

1. **Strict AND semantics:** `SEM_PASS = C0 AND C1 AND C2` (all required every epoch)
2. **Uniform failure effect:** Failing any one commitment → `SEM_PASS = False`
3. **Same downstream behavior:** The eligibility check sees the same fail streak
   regardless of which commitment was omitted

This is **expected** under ALS-A strict conjunction semantics. The target sweep
axis exists to verify this uniformity and detect any asymmetric commitment effects.

### 5.2 Comparison to Run 0 Baseline

| Metric | Run 0 (Attractor A only) | Run 1 (Model A) | Delta |
|--------|--------------------------|-----------------|-------|
| Mean AA | 59.75% (9 seeds) | 59.77% | +0.02 pp |
| Mean AAA | 59.15% (9 seeds) | 59.15% | 0.00 pp |
| Mean Lapses | ~159 | 158.6 | -0.4 |
| Max Lapse | 40 | 40 | 0 |
| Failure Class | BOUNDED_DEGRADATION | BOUNDED_DEGRADATION | Same |

**Run 1 matches Run 0's attractor A behavior almost exactly.** The adversarial
policy produces the same governance outcomes as the natural attack agent behavior.

### 5.3 Attractor Bifurcation Eliminated

Run 0 exhibited two deterministic attractors:
- Attractor A: Attack agent first → AA ≈ 59.7%
- Attractor B: Commitment-aware first → AA ≈ 99.98%

Run 1 **eliminates attractor B** by forcing commitment violation on all incumbents.
All 10 seeds now converge to attractor A behavior.

### 5.4 Constitutional Robustness Assessment

| Criterion | Result |
|-----------|--------|
| Constitutional failures detected | **0** |
| Failure classes observed | BOUNDED_DEGRADATION only |
| Structural thrashing | No |
| Asymptotic DoS | No |
| Terminal collapse | No |

**The constitution survives Model A adversarial pressure.** Persistent violation
of any single commitment produces bounded degradation but does not defeat
constitutional recovery.

---

## 6. Key Findings

### 6.1 Primary Result

> **Persistent violation of a single commitment (Model A) does NOT induce
> constitutional failure.** The system degrades to ~59.8% authority availability
> but maintains bounded recovery (max lapse = 40 epochs).

### 6.2 Target Invariance

All three commitment targets (C0, C1, C2) produce identical outcomes under
Model A. This confirms strict AND semantics where all commitments are equally
required for `SEM_PASS = True`.

### 6.3 Policy Override Effectiveness

The RSA policy successfully overrides all incumbent types, including the
commitment-aware control agent. Seed 2048 (formerly attractor B) now exhibits
attractor A behavior, confirming the policy applies universally.

### 6.4 Baseline Equivalence

Run 1 with Model A produces governance outcomes nearly identical to Run 0's
attractor A baseline. The adversarial policy reproduces the same degradation
regime already reachable via baseline attack-agent selection.

---

## 7. Preregistered Expectations vs Observed

| Expectation | Observed | Match |
|-------------|----------|-------|
| SEM_PASS = False on every epoch | ✓ Yes | ✓ |
| Global semantic fail streak grows monotonically | ✓ Yes | ✓ |
| global_semfail_ge_k_fraction ≈ 0.999 | 0.9994 | ✓ |
| No renewal failures due to eligibility | ✓ Confirmed | ✓ |
| All expirations from max_successive_renewals | ✓ 100% | ✓ |
| Renewal success rate ≈ 75% | 75.00% | ✓ |
| Authority availability collapses toward near-zero | ✗ ~59.8% | Partial |
| Failure class: BOUNDED_DEGRADATION or worse | BOUNDED_DEGRADATION | ✓ |

**Note:** The expectation "collapses toward near-zero" was pessimistic. The system
maintains ~60% AA even under persistent violation, demonstrating constitutional
resilience.

---

## 8. Defensible Claim

> **Under RSA v1.0 Model A adversarial pressure (ALWAYS_FAIL_COMMITMENT), the
> AKI v0.8 constitutional system exhibits:**
>
> - Authority Availability: 59.77% (no degradation from Run 0 attractor A baseline)
> - Asymptotic Authority Availability: 59.15%
> - Failure Classification: 100% BOUNDED_DEGRADATION (zero constitutional failures)
> - Maximum lapse duration: 40 epochs (identical to baseline)
> - Renewal success rate: 75% (structural, unaffected by policy)
>
> **Persistent violation of any single commitment produces bounded degradation
> but does NOT defeat constitutional recovery. The constitution survives.**

---

## 9. Implications for Runs 2-5

### 9.1 Model A Serves as Lower Bound

Model A represents the simplest adversarial strategy: fixed, blind violation.
Its failure to induce constitutional failure establishes a **lower bound** on
adversarial pressure.

### 9.2 Next Steps

- **Run 2 (Model B):** Test minimal eligibility-only behavior (hollow authority)
- **Run 3 (Model C):** Test timing-based misuse (strategic compliance/violation patterns)
- **Run 4:** TBD based on Run 2-3 findings
- **Run 5:** TBD based on Run 2-4 findings

### 9.3 Hypothesis for Run 3

If Model A (always fail) doesn't defeat recovery, and Model D (always pass)
maintains authority by definition, then **timing-based strategies (Model C)**
may be the key attack vector. Run 3 should stress test epoch-offset patterns.

---

## 10. Artifacts

| File | Description |
|------|-------------|
| `scripts/rsa_v100_run1_violation.py` | Run 1 execution script |
| `reports/rsa_v100_run1_violation_report.md` | This report |
| `reports/rsa_v100_run1_violation_20260107_113624.json` | Raw results JSON |
| `docs/rsa_instructions_v1.0_runner1.md` | Runner instructions |

---

## 11. Run 1 Definition of Done

| # | Criterion | Status |
|---|-----------|--------|
| 1 | All 30 runs execute to full horizon | ✅ |
| 2 | Per-seed metrics recorded | ✅ |
| 3 | Per-target aggregate summaries produced | ✅ |
| 4 | Failure classes assigned without reinterpretation | ✅ |
| 5 | No configuration drift from Run 0 | ✅ |
| 6 | Seed 2048 behavior change documented | ✅ |
| 7 | Constitutional failure check performed | ✅ PASSED |
| 8 | Comparison to Run 0 baseline documented | ✅ |
| 9 | Results saved with timestamps | ✅ |

---

**RUN 1 COMPLETE. CONSTITUTION SURVIVES MODEL A.**
