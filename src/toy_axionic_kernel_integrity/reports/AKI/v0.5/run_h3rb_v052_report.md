# Run H3-RB: Renewal Boundary Search (Higher-Cost Sweep)

**Experiment ID**: H3-RB_20260103_172023
**Spec Version**: 0.5.2
**Timestamp**: 2026-01-03T17:20:23.568656

## Configuration

- **Horizon**: 5,000 cycles
- **Renewal Costs Tested**: [10, 12, 15, 20]
- **Seeds per Cost**: 5
- **Total Runs**: 20
- **Attack Weights**: V052_RUNG_G2_ATTACK_WEIGHTS (CBD_E3 = 0.30)
- **Stop Mode**: stop_on_renewal_fail=True (early termination)

## Summary by Renewal Cost

| Cost | Seeds | Horizon | Fail | Bankrupt | Mean Success Rate | Mean Fail Time |
|------|-------|---------|------|----------|-------------------|----------------|
| 10 | 5 | 5 | 0 | 0 | 94.00% | N/A |
| 12 | 5 | 5 | 0 | 0 | 94.00% | N/A |
| 15 | 5 | 5 | 0 | 0 | 94.00% | N/A |
| 20 | 5 | 5 | 0 | 0 | 94.00% | N/A |

## Phase Boundary Analysis

**Critical Threshold**: Not found in tested range

### Failure Rate by Renewal Cost

| Cost | Failure Rate | Mean Time to Fail |
|------|--------------|-------------------|
| 10 | 0% | N/A |
| 12 | 0% | N/A |
| 15 | 0% | N/A |
| 20 | 0% | N/A |

### Notes

- No critical threshold found in tested range (all costs < 50% failure)
- No increase in renewal failure was observed across the tested renewal_cost range. Renewal success rate remained constant.

## Individual Run Results

| Run ID | Cost | Seed | S* | Cycles | Attempts | Successes | Rate | Fail Time | Stop Reason |
|--------|------|------|----|--------|----------|-----------|------|-----------|-------------|
| H3-R10_s40 | 10 | 40 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R10_s41 | 10 | 41 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R10_s42 | 10 | 42 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R10_s43 | 10 | 43 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R10_s44 | 10 | 44 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R12_s40 | 12 | 40 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R12_s41 | 12 | 41 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R12_s42 | 12 | 42 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R12_s43 | 12 | 43 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R12_s44 | 12 | 44 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R15_s40 | 15 | 40 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R15_s41 | 15 | 41 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R15_s42 | 15 | 42 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R15_s43 | 15 | 43 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R15_s44 | 15 | 44 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R20_s40 | 20 | 40 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R20_s41 | 20 | 41 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R20_s42 | 20 | 42 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R20_s43 | 20 | 43 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R20_s44 | 20 | 44 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |

---

*Report generated 2026-01-03T17:20:23.568656*
