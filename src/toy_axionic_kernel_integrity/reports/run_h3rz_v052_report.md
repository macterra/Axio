# Run H3-RZ: Zero-Slack Renewal Impossibility

> **Classification**: H3-RZ — Zero-Slack Renewal Impossibility

**Experiment ID**: H3-RZ_20260103_160012
**Spec Version**: 0.5.2
**Timestamp**: 2026-01-03T16:00:12.928669

## Summary

This run does **not** measure a renewal-cost phase line. Instead, it exposes a **configuration-level zero-slack regime** that makes renewal impossible for *any* positive renewal cost.

With `steps_cap_epoch = 100` and `effective_steps = 60` (at E3), the working mind consumes the entire step budget by cycle 60. At the renewal check (cycle 100), `remaining_budget = 0`, causing:

```
remaining_budget < renewal_cost  →  TRUE for all renewal_cost ≥ 1
```

**Key Insight**: Renewal is impossible in zero-slack regimes regardless of renewal_cost magnitude.

This is a valid and informative structural result, but a corrected run (H3-RS) with `steps_cap_epoch = 200` is required to measure the intended phase boundary.

## Configuration

- **Horizon**: 5,000 cycles
- **Renewal Costs Tested**: [4, 5, 6, 7, 8, 9]
- **Seeds per Cost**: 5
- **Total Runs**: 30
- **Attack Weights**: V052_RUNG_G2_ATTACK_WEIGHTS (CBD_E3 = 0.30)
- **Stop Mode**: stop_on_renewal_fail=True (early termination)

## Summary by Renewal Cost

| Cost | Seeds | Horizon | Fail | Bankrupt | Mean Success Rate | Mean Fail Time |
|------|-------|---------|------|----------|-------------------|----------------|
| 4 | 5 | 0 | 5 | 0 | 0.00% | 100 |
| 5 | 5 | 0 | 5 | 0 | 0.00% | 100 |
| 6 | 5 | 0 | 5 | 0 | 0.00% | 100 |
| 7 | 5 | 0 | 5 | 0 | 0.00% | 100 |
| 8 | 5 | 0 | 5 | 0 | 0.00% | 100 |
| 9 | 5 | 0 | 5 | 0 | 0.00% | 100 |

## Phase Boundary Analysis

**Critical Threshold**: renewal_cost = 4

### Failure Rate by Renewal Cost

| Cost | Failure Rate | Mean Time to Fail |
|------|--------------|-------------------|
| 4 | 100% | 100 |
| 5 | 100% | 100 |
| 6 | 100% | 100 |
| 7 | 100% | 100 |
| 8 | 100% | 100 |
| 9 | 100% | 100 |

### Notes

- Critical threshold at renewal_cost=4: 100.0% failure rate
- Failure rate monotonically increases with renewal_cost

## Individual Run Results

| Run ID | Cost | Seed | S* | Cycles | Attempts | Successes | Rate | Fail Time | Stop Reason |
|--------|------|------|----|--------|----------|-----------|------|-----------|-------------|
| H3-R4_s40 | 4 | 40 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R4_s41 | 4 | 41 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R4_s42 | 4 | 42 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R4_s43 | 4 | 43 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R4_s44 | 4 | 44 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R5_s40 | 5 | 40 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R5_s41 | 5 | 41 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R5_s42 | 5 | 42 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R5_s43 | 5 | 43 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R5_s44 | 5 | 44 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R6_s40 | 6 | 40 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R6_s41 | 6 | 41 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R6_s42 | 6 | 42 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R6_s43 | 6 | 43 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R6_s44 | 6 | 44 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R7_s40 | 7 | 40 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R7_s41 | 7 | 41 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R7_s42 | 7 | 42 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R7_s43 | 7 | 43 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R7_s44 | 7 | 44 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R8_s40 | 8 | 40 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R8_s41 | 8 | 41 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R8_s42 | 8 | 42 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R8_s43 | 8 | 43 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R8_s44 | 8 | 44 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R9_s40 | 9 | 40 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R9_s41 | 9 | 41 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R9_s42 | 9 | 42 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R9_s43 | 9 | 43 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |
| H3-R9_s44 | 9 | 44 | 1 | 100 | 1 | 0 | 0.00% | 100 | RENEWAL_FAIL |

---

*Report generated 2026-01-03T16:00:12.928669*
