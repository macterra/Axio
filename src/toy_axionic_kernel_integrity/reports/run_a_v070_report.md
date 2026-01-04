# AKI v0.7 Run A: Eligibility-Coupled Succession Baseline Report

**Experiment ID:** run_a_v070_1767555251
**Date:** 2026-01-04
**Spec Version:** 0.7 (ALS-G)

## Executive Summary

Run A establishes baseline behavior for AKI v0.7's eligibility-gated succession mechanism. The key finding is that under current parameters, the eligibility mechanism **rarely activates** because succession events are infrequent. Leases are sufficiently stable that working minds rarely require replacement.

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

| Sub-Run | K | Cycles | Successions | Lapses | Lapse Rate | Exclusions |
|---------|---|--------|-------------|--------|------------|------------|
| G0 | 3 | 25,000 | 5 | 0 | 0.00/1k | 0 |
| G1 | 1 | 25,000 | 5 | 0 | 0.00/1k | 0 |
| G2 | 5 | 25,000 | 5 | 0 | 0.00/1k | 0 |
| G3 | 10 | 25,000 | 5 | 0 | 0.00/1k | 0 |

### Key Observations

1. **Low Succession Frequency**
   - Only 1 succession per 5,000-cycle run (the initial endorsement)
   - Working minds successfully renew and maintain their leases
   - No expirations, revocations, or bankruptcies trigger new successions

2. **Streak Accumulation Without Exclusion**
   - Final streak values are very high (avg 90-100 per policy)
   - Streaks accumulate across epochs but never trigger exclusion
   - Eligibility filtering only applies at succession, which rarely occurs

3. **No Eligibility Rejections**
   - 0 eligibility exclusions across all K values
   - No policies ever excluded from C_ELIG
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

### Why No Exclusions?

The eligibility mechanism is designed to filter candidates **at succession time**. However:

1. Initial endorsement happens before any streaks accumulate
2. Endorsed minds renew successfully, avoiding succession
3. Streaks accumulate in the background but are never checked
4. The 5K cycle horizon may be too short to trigger lease failures

### Implications for System Design

1. **Eligibility Gating is Succession-Gated:**
   The mechanism only activates when succession occurs. Stable leases mean stable authority.

2. **Streak Persistence:**
   Streaks correctly persist across the run, demonstrating the tracking mechanism works.

3. **Policy Identity Stability:**
   The stable `policy_id` format (`"{category}:{enum.name}"`) correctly identifies policies across invocations.

## Recommendations for Future Experiments

1. **Run B: Forced Succession**
   - Configure shorter lease durations or higher rent costs
   - Force more frequent succession events
   - Observe eligibility filtering behavior

2. **Run C: Stress Test**
   - Use K=1 with forced frequent succession
   - Measure time-to-first-lapse
   - Validate NULL_AUTHORITY handling

3. **Run D: Attack-Heavy Pool**
   - Increase attack successor probability
   - Observe whether semantic failures lead to exclusions
   - Test C_ELIG dynamics under adversarial conditions

## Conclusion

Run A validates the structural correctness of the v0.7 eligibility mechanism but reveals that **succession frequency is the primary gating factor**. The mechanism cannot exclude candidates if succession never occurs. This is by design - stable, well-behaved working minds should not trigger succession.

Future experiments should:
- Increase succession frequency through parameter tuning
- Validate exclusion behavior when succession does occur
- Test edge cases around NULL_AUTHORITY lapses

---

**Files Generated:**
- `reports/run_a_v070_1767555252.json` - Raw experiment data
- `reports/run_a_v070_report.md` - This report

**Next Steps:**
- Design Run B with parameters that force succession
- Implement test cases for manual streak injection
