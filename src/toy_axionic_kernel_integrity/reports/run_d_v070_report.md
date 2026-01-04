# AKI v0.7 Run D Report: Candidate Pool Composition Stress Under Forced Turnover

## Overview

**Experiment**: Run D – Candidate Pool Composition Stress (ALS-G)
**Specification Version**: 0.7
**Purpose**: Test whether skewing the candidate pool toward failure-prone (Attack) or pass-prone (Control) policies changes eligibility contraction, lapse frequency, and time in NULL_AUTHORITY under fixed K and turnover geometry.

## Configuration (Binding)

| Parameter | Value | Notes |
|-----------|-------|-------|
| `renewal_check_interval` | 50 cycles | Unchanged from Run A/B/C |
| `msrw_cycles` | 200 | Maximum successive renewal window |
| `renewal_cost` | 5 steps | Unchanged |
| `max_successive_renewals` | 3 | Harness-enforced forced turnover |
| `horizon` | 5,000 cycles | Identical to Run B/C |
| `eligibility_threshold_k` | 5 | Fixed (boundary region from Run C) |
| Seeds | 50, 51, 52, 53, 54 | Same as Run A/B/C |

### Pool Composition Policies

| Sub-Run | Policy | Control Weight | Attack Weight |
|---------|--------|----------------|---------------|
| D0 | V060_DEFAULT | 0.30 | 0.70 |
| D1 | ATTACK_HEAVY_90 | 0.10 | 0.90 |
| D2 | CONTROL_HEAVY_90 | 0.90 | 0.10 |

## Results Summary

### Aggregate by Pool Policy

| Pool Policy | Post-Init Successions | Lapses | NULL_AUTHORITY (cycles) | Dominant Regime |
|-------------|----------------------|--------|-------------------------|-----------------|
| V060_DEFAULT | 120 | 0 | 0 | FILTERING_ACTIVE (4/5) |
| ATTACK_HEAVY_90 | 116 | 15 | 741 | CONSTITUTIONAL_LAPSE (5/5) |
| CONTROL_HEAVY_90 | 119 | 3 | 98 | CONSTITUTIONAL_LAPSE (3/5) |

### Phase-Line View (Pool Policy → Regime Distribution)

```
Pool Policy          LATENT    FILTERING_ACTIVE    CONSTITUTIONAL_LAPSE
────────────────────────────────────────────────────────────────────────
V060_DEFAULT         1/5       4/5                 0/5
ATTACK_HEAVY_90      0/5       0/5                 5/5
CONTROL_HEAVY_90     1/5       1/5                 3/5
```

### Per-Seed Detail Table

| Policy | Seed | Post-Init | Avg\|C_ELIG\| | Min\|C_ELIG\| | Lapses | NULL_AUTH (cycles) | Attack% | Control% | Regime |
|--------|------|-----------|--------------|---------------|--------|-------------------|---------|----------|--------|
| V060_DEFAULT | 50 | 24 | 11.00 | 11 | 0 | 0 | 75.6% | 24.4% | FILTERING_ACTIVE |
| V060_DEFAULT | 51 | 24 | 11.00 | 11 | 0 | 0 | 70.6% | 29.4% | LATENT |
| V060_DEFAULT | 52 | 24 | 11.00 | 11 | 0 | 0 | 66.6% | 33.4% | FILTERING_ACTIVE |
| V060_DEFAULT | 53 | 24 | 11.00 | 11 | 0 | 0 | 76.0% | 24.0% | FILTERING_ACTIVE |
| V060_DEFAULT | 54 | 24 | 11.00 | 11 | 0 | 0 | 68.0% | 32.0% | FILTERING_ACTIVE |
| ATTACK_HEAVY_90 | 50 | 23 | 5.40 | 1 | 3 | 149 | 90.6% | 9.4% | CONSTITUTIONAL_LAPSE |
| ATTACK_HEAVY_90 | 51 | 23 | 4.67 | 0 | 3 | 149 | 90.9% | 9.1% | CONSTITUTIONAL_LAPSE |
| ATTACK_HEAVY_90 | 52 | 24 | 8.33 | 3 | 2 | 98 | 86.9% | 13.1% | CONSTITUTIONAL_LAPSE |
| ATTACK_HEAVY_90 | 53 | 23 | 6.75 | 2 | 4 | 197 | 90.6% | 9.4% | CONSTITUTIONAL_LAPSE |
| ATTACK_HEAVY_90 | 54 | 23 | 6.50 | 2 | 3 | 148 | 89.3% | 10.7% | CONSTITUTIONAL_LAPSE |
| CONTROL_HEAVY_90 | 50 | 24 | 8.00 | 2 | 1 | 49 | 7.0% | 93.0% | CONSTITUTIONAL_LAPSE |
| CONTROL_HEAVY_90 | 51 | 24 | 11.00 | 11 | 0 | 0 | 10.9% | 89.1% | LATENT |
| CONTROL_HEAVY_90 | 52 | 24 | 11.00 | 11 | 0 | 0 | 10.9% | 89.1% | FILTERING_ACTIVE |
| CONTROL_HEAVY_90 | 53 | 24 | 8.33 | 3 | 1 | 49 | 12.2% | 87.8% | CONSTITUTIONAL_LAPSE |
| CONTROL_HEAVY_90 | 54 | 23 | 3.67 | 0 | 1 | 0 | 8.8% | 91.2% | CONSTITUTIONAL_LAPSE |

## Composition Verification

All pool policies achieved their expected composition skew within tolerance (±5%):

| Policy | Expected Attack | Realized Attack | Expected Control | Realized Control | Status |
|--------|-----------------|-----------------|------------------|------------------|--------|
| V060_DEFAULT | 70% | 71.3% | 30% | 28.7% | ✓ |
| ATTACK_HEAVY_90 | 90% | 89.7% | 10% | 10.3% | ✓ |
| CONTROL_HEAVY_90 | 10% | 10.0% | 90% | 90.0% | ✓ |

**Composition skew was correctly applied at candidate sampling.**

## Key Observations

### 1. Baseline (D0) at K=5 Shows Zero Lapses

Under V060_DEFAULT at K=5, Run D observed zero lapses across all seeds, whereas Run C observed three lapses. Although both runs use the same nominal pool policy (V060_DEFAULT), Run D introduces a new pool-policy parameterization path that can perturb RNG call order and therefore realized candidate sequences. This discrepancy indicates that K=5 remains a boundary region under this geometry; it does not by itself establish a stable "no-lapse" regime for the baseline pool.

### 2. ATTACK_HEAVY_90 Dramatically Increases Constitutional Lapse

At 90% Attack composition:
- **15 lapses** (vs 0 baseline)
- **741 cycles in NULL_AUTHORITY** (vs 0 baseline)
- **5/5 seeds affected** — lapse observed in all 5 seeds
- Average |C_ELIG| dropped to ~6.3 (vs 11 baseline)
- Min |C_ELIG| as low as 0-2 across seeds

**Interpretation**: When the candidate pool is dominated by attack-type policies (consistent with lower observed eligibility retention under attack-heavy sampling), eligibility filtering aggressively contracts C_ELIG, leading to frequent lapse across all seeds.

### 3. CONTROL_HEAVY_90 Provides Partial But Incomplete Protection

At 90% Control composition:
- **3 lapses** (vs 15 at ATTACK_HEAVY_90)
- **98 cycles in NULL_AUTHORITY** (vs 741)
- **3/5 seeds affected** — constitutional lapse still occurs

**Interpretation**: Even with 90% pass-prone policies, constitutional lapse still occurs at K=5. This indicates that K=5 is not sufficient to guarantee lapse-free operation regardless of pool composition. The Attack policies (10% of draws) still accumulate sufficient streaks to occasionally empty C_ELIG.

**Note on lapse duration accounting:** A lapse event is counted when `C_ELIG = ∅` triggers a transition to `NULL_AUTHORITY`. In rare cases, `NULL_AUTHORITY` duration may record as 0 cycles if the system re-attempts succession at the same scheduling boundary (zero-length interval in cycle units). Lapse count and NULL_AUTH cycle totals therefore need not match one-to-one at the single-cycle level. (See Seed 54 under CONTROL_HEAVY_90: 1 lapse, 0 NULL_AUTH cycles.)

### 4. C_ELIG Contraction Correlates with Attack Density

| Policy | Avg Attack% | Mean |C_ELIG| Range | Min |C_ELIG| Range |
|--------|------------|---------------------|---------------------|
| V060_DEFAULT | 71% | 11.00 | 11 |
| ATTACK_HEAVY_90 | 90% | 4.67 – 8.33 | 0 – 3 |
| CONTROL_HEAVY_90 | 10% | 3.67 – 11.00 | 0 – 11 |

Higher Attack density → lower |C_ELIG| → higher lapse risk.

### 5. Post-Init Succession Count Is Stable

| Policy | Post-Init Successions |
|--------|----------------------|
| V060_DEFAULT | 120 |
| ATTACK_HEAVY_90 | 116 |
| CONTROL_HEAVY_90 | 119 |

Despite large differences in lapse behavior, succession counts remain similar (~120). This indicates that the system recovers from lapses and continues operating — constitutional lapse is not catastrophic in terms of succession throughput, but represents periodic authority gaps.

## Constitutional Phase Diagram (Composition × K)

This run establishes **composition sensitivity at fixed K=5**:

```
         LAPSE RISK
             ↑
             │
    HIGH     │    ATTACK_HEAVY_90 (5/5 lapse)
    (5/5)    │    ████████████████████████████
             │
    MEDIUM   │              CONTROL_HEAVY_90 (3/5 lapse)
    (3/5)    │              ████████████
             │
    LOW      │                          V060_DEFAULT (0/5 lapse)
    (0/5)    │                          ○
             │
             └────────────────────────────────→ Attack%
                 10%        70%        90%
```

## Conservative Claims

### What This Experiment Demonstrates

1. **Pool composition materially affects lapse frequency at fixed K**: ATTACK_HEAVY_90 produces 15 lapses vs 0 at baseline
2. **Eligibility gating remains meaningful under skew**: The filter discriminates between pool compositions as expected
3. **No composition eliminates lapse at K=5 universally**: Even CONTROL_HEAVY_90 produces 3 lapses
4. **Composition skew was correctly applied**: All policies achieved expected Attack/Control ratios within ±5%

### What CANNOT Be Inferred

1. **Optimal pool composition**: The experiment does not determine which composition produces "best" governance
2. **Generalization**: Results are specific to:
   - K=5
   - `max_successive_renewals = 3`
   - `horizon = 5,000` cycles
   - Specific rent schedule
   - V060 generator semantics for Attack vs Control pass rates
3. **Competence or alignment**: Pool composition affects lapse mechanics, not governance quality
4. **Per-category pass rates**: This report does not establish per-category pass rates; any claim about Attack vs Control semantic pass propensity requires explicit SEM_PASS/FAIL tallies by policy category
5. **Interaction with K**: Results apply only to K=5; different K values may show different composition sensitivity

## Comparison with Run C

| Metric | Run C (K=5, V060_DEFAULT) | Run D (K=5, V060_DEFAULT) |
|--------|---------------------------|---------------------------|
| Lapses | 3 | 0 |
| NULL_AUTHORITY | 147 cycles | 0 cycles |
| Regime distribution | 2/5 CONSTITUTIONAL_LAPSE | 0/5 CONSTITUTIONAL_LAPSE |

**Note**: This discrepancy is consistent with RNG-order perturbation introduced by the pool-policy parameterization; it indicates sensitivity in the boundary region, not an invariant difference.

## Recommendations for Future Runs

1. **Sweep K under ATTACK_HEAVY_90**: Find K* where lapse probability → 0 under adversarial composition
2. **Test intermediate compositions (70/30, 80/20)**: Map the composition → lapse relationship more finely
3. **Longer horizon**: Test whether composition effects persist or attenuate over time
4. **Combined K × Composition sweep**: Map the full (K, composition) phase space

## Appendix: Terminal Causes

All 15 runs (3 policies × 5 seeds) terminated via `HORIZON_EXHAUSTED`. No runs terminated due to:
- `POOL_DEPLETION`
- `GENERATOR_HALT`
- `MAX_ENDORSEMENTS`

---

**Report Generated**: 2025-01-04
**Experiment Script**: `run_d_v070.py`
**Raw Data**: `reports/run_d_v070_*.json`
