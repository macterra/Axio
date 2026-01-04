# AKI v0.7 Run C Report: Eligibility Threshold Sweep Under Forced Turnover

## Overview

**Experiment**: Run C – Eligibility Threshold Sweep (ALS-G)
**Specification Version**: 0.7
**Purpose**: Quantify how eligibility threshold K controls constitutional outcomes (lapse frequency, C_ELIG contraction, time in NULL_AUTHORITY) under fixed forced-turnover geometry.

## Configuration (Binding)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `renewal_check_interval` | 50 cycles | Unchanged from Run A/B |
| `msrw_cycles` | 200 | Maximum successive renewal window |
| `renewal_cost` | 5 steps | Unchanged from Run A/B |
| `max_successive_renewals` | 3 | Harness-enforced forced turnover (same as Run B) |
| `horizon` | 5,000 cycles | 100 × renewal_check_interval |
| `candidate_pool_policy` | V060_DEFAULT | Unchanged from Run A/B |
| Seeds | 50, 51, 52, 53, 54 | Same as Run A/B |

### Sub-Run K Values

| Sub-Run | K | Interpretation |
|---------|---|----------------|
| C1 | 1 | Knife-edge (maximum strictness) |
| C2 | 3 | Baseline (Run B replication) |
| C3 | 5 | Forgiving |
| C4 | 10 | Very forgiving |

## Results Summary

### Aggregate by K

| K | Post-Init Successions | Lapses | NULL_AUTHORITY (cycles) | Dominant Regime |
|---|----------------------|--------|-------------------------|-----------------|
| 1 | 88 | 11 | 344 | CONSTITUTIONAL_LAPSE (4/5) |
| 3 | 88 | 11 | 344 | CONSTITUTIONAL_LAPSE (4/5) |
| 5 | 120 | 3 | 147 | Mixed (2/5 lapse) |
| 10 | 120 | 0 | 0 | FILTERING_ACTIVE (4/5) |

### Phase-Line View (K → Regime Distribution)

```
K      LATENT    FILTERING_ACTIVE    CONSTITUTIONAL_LAPSE
─────────────────────────────────────────────────────────
1      1/5       0/5                 4/5
3      1/5       0/5                 4/5
5      1/5       2/5                 2/5
10     1/5       4/5                 0/5
```

*At K=10, FILTERING_ACTIVE indicates that eligibility evaluation occurs at succession, not that sustained exclusion pressure is present.*

### Per-Seed Detail Table

| K | Seed | Post-Init | Avg\|C_ELIG\| | Min\|C_ELIG\| | First Empty (epoch) | Lapses | NULL_AUTH (cycles) | Regime |
|---|------|-----------|--------------|---------------|---------------------|--------|-------------------|--------|
| 1 | 50 | 16 | 0.86 | 0 | 5 | 4 | 148 | CONSTITUTIONAL_LAPSE |
| 1 | 51 | 24 | 11.00 | 11 | N/A | 0 | 0 | LATENT |
| 1 | 52 | 16 | 0.73 | 0 | 5 | 2 | 49 | CONSTITUTIONAL_LAPSE |
| 1 | 53 | 16 | 0.75 | 0 | 5 | 3 | 98 | CONSTITUTIONAL_LAPSE |
| 1 | 54 | 16 | 0.70 | 0 | 5 | 2 | 49 | CONSTITUTIONAL_LAPSE |
| 3 | 50 | 16 | 0.86 | 0 | 5 | 4 | 148 | CONSTITUTIONAL_LAPSE |
| 3 | 51 | 24 | 11.00 | 11 | N/A | 0 | 0 | LATENT |
| 3 | 52 | 16 | 0.73 | 0 | 5 | 2 | 49 | CONSTITUTIONAL_LAPSE |
| 3 | 53 | 16 | 0.75 | 0 | 5 | 3 | 98 | CONSTITUTIONAL_LAPSE |
| 3 | 54 | 16 | 0.70 | 0 | 5 | 2 | 49 | CONSTITUTIONAL_LAPSE |
| 5 | 50 | 24 | 9.00 | 5 | N/A | 2 | 98 | CONSTITUTIONAL_LAPSE |
| 5 | 51 | 24 | 11.00 | 11 | N/A | 0 | 0 | LATENT |
| 5 | 52 | 24 | 11.00 | 11 | N/A | 0 | 0 | FILTERING_ACTIVE |
| 5 | 53 | 24 | 11.00 | 11 | N/A | 0 | 0 | FILTERING_ACTIVE |
| 5 | 54 | 24 | 8.00 | 2 | N/A | 1 | 49 | CONSTITUTIONAL_LAPSE |
| 10 | 50 | 24 | 11.00 | 11 | N/A | 0 | 0 | FILTERING_ACTIVE |
| 10 | 51 | 24 | 11.00 | 11 | N/A | 0 | 0 | LATENT |
| 10 | 52 | 24 | 11.00 | 11 | N/A | 0 | 0 | FILTERING_ACTIVE |
| 10 | 53 | 24 | 11.00 | 11 | N/A | 0 | 0 | FILTERING_ACTIVE |
| 10 | 54 | 24 | 11.00 | 11 | N/A | 0 | 0 | FILTERING_ACTIVE |

## Run B Replication (C2)

C2 (K=3) was required to exactly replicate Run B behavior. Comparison:

| Metric | C2 | Run B | Match |
|--------|----|----|-------|
| Post-init successions | 88 | 88 | ✓ |
| Lapses | 11 | 11 | ✓ |
| NULL_AUTHORITY time | 344 cycles | 344 cycles | ✓ |
| Regime distribution | 4/5 CONSTITUTIONAL_LAPSE | 4/5 CONSTITUTIONAL_LAPSE | ✓ |

**Replication confirmed**: C2 exactly reproduces Run B behavior.

## Key Observations

### 1. K=1 and K=3 Are Indistinguishable

At K=1 and K=3, the constitutional outcome is identical:
- Same lapse count (11)
- Same NULL_AUTHORITY time (344 cycles)
- Same regime distribution (4/5 CONSTITUTIONAL_LAPSE)

**Interpretation**: In the tested geometry, the difference between K=1 and K=3 is not observable. Both values produce the same eligibility filtering behavior because semantic failures exceed both thresholds at the same succession events.

### 2. K=5 Provides Partial Protection

At K=5, constitutional lapse still occurs but is significantly reduced:
- Lapses reduced from 11 → 3 (73% reduction)
- NULL_AUTHORITY time reduced from 344 → 147 cycles (57% reduction)
- Regime shifts: 2/5 CONSTITUTIONAL_LAPSE, 2/5 FILTERING_ACTIVE

**Interpretation**: K=5 raises the streak threshold enough to prevent some policies from becoming ineligible during the succession window, but does not fully eliminate lapse risk.

### 3. K=10 Eliminates Constitutional Lapse

At K=10, constitutional lapse does not occur:
- Zero lapses across all 5 seeds
- Zero cycles in NULL_AUTHORITY
- Regime: 4/5 FILTERING_ACTIVE, 1/5 LATENT

**Interpretation**: K=10 is sufficiently high that no policy accumulates 10 consecutive semantic failures before resetting, ensuring C_ELIG ≠ ∅ at every succession.

### 4. Post-Init Succession Count Bifurcates

| K | Post-Init Successions |
|---|-----------------------|
| 1 | 88 |
| 3 | 88 |
| 5 | 120 |
| 10 | 120 |

- At K ∈ {1, 3}: 88 post-init successions (more lapses → more NULL_AUTHORITY recovery time → fewer successions)
- At K ∈ {5, 10}: 120 post-init successions (fewer or no lapses → continuous authority → more successions)

### 5. Seed 51 Is Anomalous Across All K

Seed 51 consistently shows:
- 24 post-init successions (vs 16 for other seeds at K ∈ {1, 3})
- Zero lapses at all K values
- LATENT regime

**Interpretation**: The specific random sequence for seed 51 produces policies that consistently pass semantic checks, preventing streak accumulation. This demonstrates that eligibility behavior is sensitive to the specific failure patterns, not just to K.

## Constitutional Phase Diagram

```
         LAPSE RISK
             ↑
             │
    HIGH     │    K=1, K=3
    (4/5)    │    ████████████████████
             │
    MEDIUM   │           K=5
    (2/5)    │           ██████████
             │
    LOW      │                      K=10
    (0/5)    │                      ○
             │
             └─────────────────────────→ K
                 1    3    5    10
```

At K ≥ 10, the system enters a non-lapse constitutional band where authority continuity is maintained.

## Conservative Claims

### What This Experiment Demonstrates

1. **Increasing K reduces lapse frequency beyond a threshold**: In the tested geometry, K=1 and K=3 are behaviorally equivalent, while higher K values reduce or eliminate lapse
2. **A non-lapse band exists in the tested candidate pool and renewal geometry**: At K=10, zero lapses occurred across all seeds
3. **K=1 and K=3 are behaviorally equivalent** in the tested geometry
4. **Eligibility evaluation occurs at all K values** under forced turnover; exclusion pressure varies with K

### What CANNOT Be Inferred

1. **Optimal K**: The experiment does not determine which K value produces "best" governance
2. **Generalization**: Results are specific to:
   - 11-policy candidate pool with V060_DEFAULT distribution
   - `max_successive_renewals = 3`
   - `horizon = 5,000` cycles
   - Specific rent schedule
3. **Competence or alignment**: Eligibility filtering measures structural properties, not policy quality
4. **Failure mode severity**: A lapse is counted equally regardless of duration or frequency
5. **Behavior at intermediate K values**: K=4, K=6, K=7, K=8, K=9 were not tested

## Recommendations for Future Runs

1. **Finer K sweep (K ∈ {3, 4, 5, 6, 7, 8, 9, 10})**: Identify the critical K* where lapse probability → 0
2. **Longer horizon**: Test whether non-lapse behavior at K=10 persists beyond 5,000 cycles
3. **Vary forced turnover**: Sweep `max_successive_renewals` alongside K
4. **Investigate seed 51**: Understand why this seed produces no lapses at any K

## Appendix: Terminal Causes

All 20 runs (4 K values × 5 seeds) terminated via `HORIZON_EXHAUSTED`. No runs terminated due to:
- `POOL_DEPLETION`
- `GENERATOR_HALT`
- `MAX_ENDORSEMENTS`

---

**Report Generated**: 2025-01-04
**Experiment Script**: `run_c_v070.py`
**Raw Data**: `reports/run_c_v070_*.json`
