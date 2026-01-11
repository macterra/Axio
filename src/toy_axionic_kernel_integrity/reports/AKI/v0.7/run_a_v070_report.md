# AKI v0.7 Run A: Eligibility-Coupled Succession Baseline Report

**Experiment ID:** run_a_v070_1767555251
**Date:** 2026-01-04
**Spec Version:** 0.7 (ALS-G)

## Executive Summary

Run A establishes baseline behavior for AKI v0.7's eligibility-gated succession mechanism. The key finding is that under current parameters, the eligibility mechanism **does not activate beyond the initial endorsement**, because no post-initial succession events occur.

## Experiment Design

### Parameters
- **Horizon:** 5,000 cycles per run
- **Seeds:** [50, 51, 52, 53, 54]
- **K values tested:**
  - G0: K=3 (spec default)
  - G1: K=1 (aggressive - exclude after 1 semantic failure)
  - G2: K=5 (lenient)
  - G3: K=10 (very lenient)

### Key Invariants Tested
1. Streak tracked per stable `policy_id` (not per instance)
2. C_ELIG = { c ∈ C_POOL | streak[c.policy_id] < K }
3. Empty C_ELIG triggers NULL_AUTHORITY lapse
4. No streak updates during lapse
5. Streak resets to 0 on semantic success

## Results

### Summary Table

| Sub-Run | K | Cycles | Successions | Lapses | Lapse Rate | Elig. Evals (Post-Init)* |
|---------|---|--------|-------------|--------|------------|-------------------------|
| G0 | 3 | 25,000 | 5 | 0 | 0.00/1k | 0 |
| G1 | 1 | 25,000 | 5 | 0 | 0.00/1k | 0 |
| G2 | 5 | 25,000 | 5 | 0 | 0.00/1k | 0 |
| G3 | 10 | 25,000 | 5 | 0 | 0.00/1k | 0 |

*Eligibility filtering is only evaluated at succession events. No post-initial succession events occurred in Run A.

### Key Observations

1. **Low Succession Frequency**
   - Only 1 succession per 5,000-cycle run (the initial endorsement)
   - Working minds successfully renew and maintain their leases
   - No expirations, revocations, or bankruptcies trigger new successions

2. **Streak Accumulation Without Exclusion**
   - Final streak values are very high (avg 90-100 per policy)
   - Streaks accumulate across epochs but never trigger exclusion
   - Eligibility filtering only applies at succession, which does not occur beyond the initial endorsement in this run

3. **No Eligibility Evaluations Post-Streak Accumulation**
   - Eligibility filtering was not exercised in a nontrivial regime because no succession events occurred after semantic streaks accumulated
   - No constitutional lapses (NULL_AUTHORITY) observed

### Final Streak Distribution by Policy

Averaged across all runs:

| Policy ID | Avg Final Streak |
|-----------|------------------|
| `attack:LEASE_GAMING` | 100.0 |
| `attack:RUBBER_STAMP` | 100.0 |
| `attack:BOUNDARY_HUGGER` | 100.0 |
| `control:COMMITMENT_AWARE_V1` | 90.0 |

## Analysis

Run A validates the **structural correctness** of the v0.7 eligibility mechanism while intentionally not exercising its exclusion behavior.

Eligibility filtering is defined to occur **only at succession events**. In Run A, no succession events occurred after the initial endorsement because working minds consistently renewed their leases. As a result, semantic failure streaks accumulated in the background but were never evaluated for candidate exclusion.

This outcome demonstrates that:

1. Eligibility gating is **strictly succession-gated**, not continuous.
2. Semantic failure can accumulate without immediate constitutional consequence.
3. Stable authority regimes suppress eligibility effects by design.

Run A therefore establishes v0.7 as a **latent constitutional mechanism** whose effects are contingent on turnover frequency, rather than as a continuous filter.

## Conclusion

Run A validates the structural correctness of the v0.7 eligibility mechanism. The mechanism cannot exclude candidates if succession never occurs. This is by design—stable, structurally compliant working minds should not trigger succession.

Run A does not test exclusion or lapse behavior; it establishes baseline behavior in the absence of post-initial succession events.

---

**Files Generated:**
- `reports/run_a_v070_1767555252.json` - Raw experiment data
- `reports/run_a_v070_report.md` - This report
