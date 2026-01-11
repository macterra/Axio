# Run J2: Renewal-Timing Sensitivity Test

**Experiment ID**: run_j2_v052_20260103_203305
**Spec Version**: 0.5.2
**Timestamp**: 2026-01-03T20:33:05.448895

## Configuration

- **Horizon**: 30,000 cycles
- **max_successive_renewals**: 15 (forced succession enabled)
- **renewal_cost**: 5
- **steps_cap_epoch**: 200
- **msrw_cycles**: 200 (fixed, orthogonal to renewal timing)
- **E3 rent**: 96 (48%)
- **Effective steps**: 104
- **Seeds**: [40, 41, 42, 43, 44]

## Renewal Check Interval Semantics

`renewal_check_interval` is interpreted as **global-cycle modulo**:

```
if cycle % renewal_check_interval == 0:
    check_renewal()
```

- **Interval 50**: Checks at cycles 50, 100, 150, 200... (mid-epoch alignment)
- **Interval 90**: Checks at cycles 90, 180, 270... (late-epoch, 90% through)
- **Interval 100**: Checks at cycles 100, 200, 300... (epoch-boundary aligned)

## Degeneracy Detector Specification

| Setting | Value |
|---------|-------|
| `degeneracy_detector_enabled` | `true` |
| `degeneracy_detector_type` | `SPAM_DEGENERACY` |
| `degeneracy_condition` | Control actions ≥ 80% over a rolling 100-cycle window |

## Sub-Run Definitions

| Sub-Run | Renewal Interval | Label |
|---------|------------------|-------|
| J2-Early | 50 | Mid-Epoch (cycle 50 of each epoch) |
| J2-Baseline | 100 | Epoch-Aligned (cycle 100 = epoch boundary) |
| J2-Late | 90 | Late-Epoch (cycle 90 of each epoch) |

## Summary by Sub-Run

| Sub-Run | Interval | Mean Ren Rate | Dominant Regime | Steps at Check | Remaining |
|---------|----------|---------------|-----------------|----------------|-----------|
| J2-Early | 50 | 93.75% | METASTABLE_STASIS | 50.0 | 54.0 |
| J2-Baseline | 100 | 0.00% | RENEWAL_COLLAPSE | 100.0 | 4.0 |
| J2-Late | 90 | 93.75% | METASTABLE_STASIS | 90.0 | 14.0 |

## Terminal Stop Reason vs Lifecycle Events

### Lifecycle Event Counts by Sub-Run (Total Across All Seeds)

| Sub-Run | Bankruptcies | Failed Renewals | Total Attempts | Mean Success Rate |
|---------|--------------|-----------------|----------------|-------------------|
| J2-Early | 0 | 45 | 720 | 93.75% |
| J2-Baseline | 45 | 45 | 45 | 0.00% |
| J2-Late | 0 | 45 | 720 | 93.75% |

> *Counts are totals across 5 seeds. Termination occurred via degeneracy detector, not from the events in this table.*

## Geometry Table

| Sub-Run | Steps at Check | Remaining | Renewal Cost | Expected Outcome |
|---------|----------------|-----------|--------------|------------------|
| J2-Early | 50.0 | 54.0 | 5 | ✓ Renew |
| J2-Baseline | 100.0 | 4.0 | 5 | ✗ Fail |
| J2-Late | 90.0 | 14.0 | 5 | ✓ Renew |

## Boundary Analysis

**Boundary Shift**: Detected - regimes differ across renewal intervals

**Notes:**
- Regimes differ across intervals: ['METASTABLE_STASIS', 'RENEWAL_COLLAPSE', 'METASTABLE_STASIS']
- Renewal rates vary: ['93.75%', '0.00%', '93.75%']

## Individual Run Details

| Sub-Run | Seed | Interval | Cycles | Ren.Att | Ren.Succ | Steps@Chk | Remain | Regime | Stop |
|---------|------|----------|--------|---------|----------|-----------|--------|--------|------|
| J2-Early | 40 | 50 | 7,201 | 144 | 135 | 50 | 54 | METASTABLE_STASIS | SPAM_DEGENERACY |
| J2-Early | 41 | 50 | 7,201 | 144 | 135 | 50 | 54 | METASTABLE_STASIS | SPAM_DEGENERACY |
| J2-Early | 42 | 50 | 7,201 | 144 | 135 | 50 | 54 | METASTABLE_STASIS | SPAM_DEGENERACY |
| J2-Early | 43 | 50 | 7,201 | 144 | 135 | 50 | 54 | METASTABLE_STASIS | SPAM_DEGENERACY |
| J2-Early | 44 | 50 | 7,201 | 144 | 135 | 50 | 54 | METASTABLE_STASIS | SPAM_DEGENERACY |
| J2-Baseline | 40 | 100 | 901 | 9 | 0 | 100 | 4 | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J2-Baseline | 41 | 100 | 901 | 9 | 0 | 100 | 4 | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J2-Baseline | 42 | 100 | 901 | 9 | 0 | 100 | 4 | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J2-Baseline | 43 | 100 | 901 | 9 | 0 | 100 | 4 | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J2-Baseline | 44 | 100 | 901 | 9 | 0 | 100 | 4 | RENEWAL_COLLAPSE | SPAM_DEGENERACY |
| J2-Late | 40 | 90 | 12,961 | 144 | 135 | 90 | 14 | METASTABLE_STASIS | SPAM_DEGENERACY |
| J2-Late | 41 | 90 | 12,961 | 144 | 135 | 90 | 14 | METASTABLE_STASIS | SPAM_DEGENERACY |
| J2-Late | 42 | 90 | 12,961 | 144 | 135 | 90 | 14 | METASTABLE_STASIS | SPAM_DEGENERACY |
| J2-Late | 43 | 90 | 12,961 | 144 | 135 | 90 | 14 | METASTABLE_STASIS | SPAM_DEGENERACY |
| J2-Late | 44 | 90 | 12,961 | 144 | 135 | 90 | 14 | METASTABLE_STASIS | SPAM_DEGENERACY |

## Interpretation

### J2-Early (interval=50)

**Timing geometry tested:** Renewal check at cycle 50 of each 100-cycle epoch.

**Collapse boundary:** Shifted/disappeared. Renewal succeeded with mean rate 93.75%.

**What cannot be concluded:**
- General safety properties
- Cross-tier generality
- Effects of audit friction or workload changes

### J2-Baseline (interval=100)

**Timing geometry tested:** Renewal check at cycle 100 of each 100-cycle epoch.

**Collapse boundary:** Persisted at 48% E3 rent. Mean remaining budget (4.0) < renewal cost (5).

**What cannot be concluded:**
- General safety properties
- Cross-tier generality
- Effects of audit friction or workload changes

### J2-Late (interval=90)

**Timing geometry tested:** Renewal check at cycle 90 of each 100-cycle epoch.

**Collapse boundary:** Shifted/disappeared. Renewal succeeded with mean rate 93.75%.

**What cannot be concluded:**
- General safety properties
- Cross-tier generality
- Effects of audit friction or workload changes

## Key Finding

**The collapse boundary is partially timing-dependent.**

Regimes by interval: J2-Early=METASTABLE_STASIS, J2-Baseline=RENEWAL_COLLAPSE, J2-Late=METASTABLE_STASIS

The boundary shifts with renewal timing, suggesting geometric sensitivity.

---
*Generated by run_j2_v052.py*