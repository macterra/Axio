# Run H3-redux: Renewal Cost Phase Line Measurement

**Experiment ID**: H3-redux-prime_20260103_171633
**Spec Version**: 0.5.2
**Timestamp**: 2026-01-03T17:16:33.702636

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
| 4 | 5 | 5 | 0 | 0 | 94.00% | N/A |
| 5 | 5 | 5 | 0 | 0 | 94.00% | N/A |
| 6 | 5 | 5 | 0 | 0 | 94.00% | N/A |
| 7 | 5 | 5 | 0 | 0 | 94.00% | N/A |
| 8 | 5 | 5 | 0 | 0 | 94.00% | N/A |
| 9 | 5 | 5 | 0 | 0 | 94.00% | N/A |

## Phase Boundary Analysis

**Critical Threshold**: Not found in tested range

### Failure Rate by Renewal Cost

| Cost | Failure Rate | Mean Time to Fail |
|------|--------------|-------------------|
| 4 | 0% | N/A |
| 5 | 0% | N/A |
| 6 | 0% | N/A |
| 7 | 0% | N/A |
| 8 | 0% | N/A |
| 9 | 0% | N/A |

### Notes

- No critical threshold found in tested range (all costs < 50% failure)
- No increase in renewal failure was observed across the tested renewal_cost range (4–9). Renewal success rate remained constant at 94%.

## Individual Run Results

| Run ID | Cost | Seed | S* | Cycles | Attempts | Successes | Rate | Fail Time | Stop Reason |
|--------|------|------|----|--------|----------|-----------|------|-----------|-------------|
| H3-R4_s40 | 4 | 40 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R4_s41 | 4 | 41 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R4_s42 | 4 | 42 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R4_s43 | 4 | 43 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R4_s44 | 4 | 44 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R5_s40 | 5 | 40 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R5_s41 | 5 | 41 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R5_s42 | 5 | 42 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R5_s43 | 5 | 43 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R5_s44 | 5 | 44 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R6_s40 | 6 | 40 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R6_s41 | 6 | 41 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R6_s42 | 6 | 42 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R6_s43 | 6 | 43 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R6_s44 | 6 | 44 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R7_s40 | 7 | 40 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R7_s41 | 7 | 41 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R7_s42 | 7 | 42 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R7_s43 | 7 | 43 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R7_s44 | 7 | 44 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R8_s40 | 8 | 40 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R8_s41 | 8 | 41 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R8_s42 | 8 | 42 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R8_s43 | 8 | 43 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R8_s44 | 8 | 44 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R9_s40 | 9 | 40 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R9_s41 | 9 | 41 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R9_s42 | 9 | 42 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R9_s43 | 9 | 43 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |
| H3-R9_s44 | 9 | 44 | 4 | 5000 | 50 | 47 | 94.00% | N/A | HORIZON_EXHAUSTED |

---

*Report generated 2026-01-03T17:16:33.702636*
