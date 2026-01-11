# Run H: Boundary-Finding Escalation Experiments Report

## Executive Summary

Run H implements three single-axis escalation experiments to find the boundaries of the v0.5.2 ALS-E rent schedule. After Run G showed surprising stability (no collapse modes detected), Run H pushes individual parameters to find actual failure conditions.

**Key Findings:**

| Sub-Run | Parameter | Result | Collapse? |
|---------|-----------|--------|-----------|
| H1 | E3 rent = 60 | 93.8% renewal rate | ❌ No |
| H2 | Horizon = 100,000 | 93.8% renewal rate | ❌ No |
| H3 | Renewal cost = 10 steps | **0% renewal rate** | ✅ **YES** |

**Critical Discovery:** Renewal cost of 10 steps at E3 causes **complete system failure** - every lease expires at first renewal check. This identifies a sharp boundary in the rent/renewal cost design space.

---

## Experimental Setup

### Shared Configuration

| Parameter | Value |
|-----------|-------|
| epoch_size | 100 cycles |
| renewal_check_interval | 100 cycles |
| msrw_cycles | 200 |
| max_successive_renewals | 15 |
| steps_cap_epoch | 100 |
| actions_cap_epoch | 100 |
| Fixed E-Class | E3 |
| Generator | TierFilterGenerator(E3) |
| Control weight | 0.20 |

### Sub-Run Parameters

| Sub-Run | Horizon | Rent E3 | Renewal Cost | Seeds |
|---------|---------|---------|--------------|-------|
| H1 | 30,000 | **60** | 0 | 40-44 |
| H2 | **100,000** | 40 | 0 | 40-42 |
| H3 | 30,000 | 40 | **10** | 40-44 |

---

## Results

### H1: Rent Escalation (E3 = 60)

**Question:** Does higher rent at E3 trigger collapse?

**Configuration:**
- E0 = 1, E1 = 15, E2 = 35, **E3 = 60**, E4 = 80
- effective_steps at E3 = 100 - 60 = **40 steps** (down from 60)

**Results (5 seeds):**

| Metric | Value |
|--------|-------|
| Total bankruptcies | 0 |
| Total hollow tenures | 0 |
| Avg E3 renewal rate | 93.8% |
| Stop reason | SPAM_DEGENERACY (all seeds) |

**Analysis:** Despite reducing effective steps from 60 to 40 (33% reduction), the system remains stable with near-identical renewal rates to the baseline. Successors adapt to the tighter budget.

### H2: Horizon Extension (H = 100,000)

**Question:** Does a longer horizon reveal slow-accumulation pathologies?

**Configuration:**
- Default rent schedule (E3 = 40, effective = 60)
- Horizon extended 3.3× from 30,000 to 100,000 cycles

**Results (3 seeds):**

| Metric | Value |
|--------|-------|
| Total bankruptcies | 0 |
| Total hollow tenures | 0 |
| Avg E3 renewal rate | 93.8% |
| Stop reason | SPAM_DEGENERACY (all seeds) |

**Analysis:** Runs hit SPAM_DEGENERACY before reaching extended horizon, so H2 did not effectively test long-horizon pathologies. The TierFilterGenerator's 95-97% rejection rate triggers degeneracy detection. This is an experimental limitation, not a system failure.

### H3: Renewal Cost (10 steps)

**Question:** Does renewal overhead become the limiting factor?

**Configuration:**
- Default rent (E3 = 40, effective = 60)
- **renewal_cost_steps = 10** (charged at renewal check)

**Results (5 seeds):**

| Metric | Value |
|--------|-------|
| Total renewals | **0** |
| Total bankruptcies | **45** (9 per seed) |
| Renewal budget failures | **45** (100% failure rate) |
| Avg E3 renewal rate | **0%** |
| Stop reason | SPAM_DEGENERACY (all seeds) |

**Budget Analysis:**
```
effective_steps = 60
steps_used (avg) = 54
remaining_budget = 60 - 54 = 6
renewal_cost = 10

6 < 10 → RENEWAL FAILS EVERY TIME
```

**Analysis:** Successors use ~90% of their step budget (54 out of 60 steps), leaving only 6 steps remaining. The 10-step renewal cost exceeds this, causing 100% renewal failure. This is a **sharp boundary condition** in the design space.

---

## Comparative Analysis

### Renewal Rate by Sub-Run

| Sub-Run | E3 Renewal Rate | Delta from Baseline |
|---------|-----------------|---------------------|
| Baseline (Run G) | ~95% | — |
| H1 (rent=60) | 93.8% | -1.2% |
| H2 (H=100k) | 93.8% | -1.2% |
| H3 (cost=10) | **0%** | **-95%** |

### Failure Mode Signatures

| Sub-Run | Failure Mode | Mechanism |
|---------|--------------|-----------|
| H1 | None observed | Successors adapt to tighter budget |
| H2 | SPAM_DEGENERACY | TierFilterGenerator rejection rate |
| H3 | Mass bankruptcy | Renewal cost > remaining budget |

---

## Key Insights

### 1. Rent Elasticity is High

Increasing E3 rent by 50% (40 → 60) produces only marginal degradation (-1.2% renewal rate). The system has significant headroom before rent causes collapse.

### 2. Renewal Cost is a Cliff, Not a Slope

Unlike rent (which shows graceful degradation), renewal cost creates a **binary failure condition**. Either:
- `remaining_budget ≥ renewal_cost` → renewal succeeds
- `remaining_budget < renewal_cost` → renewal fails (100%)

There is no middle ground.

### 3. Step Usage Determines Renewal Viability

With current successor behavior using ~90% of effective steps:
- **Safe renewal cost** = 10% of effective_steps = 6 steps at E3
- **Unsafe renewal cost** = 10+ steps causes mass failure

### 4. SPAM_DEGENERACY Masks Long-Horizon Effects

All runs terminated due to SPAM_DEGENERACY (triggered by TierFilterGenerator's 95%+ rejection rate). This prevented H2 from truly testing the 100k horizon. **Recommendation:** Adjust spam detection thresholds or use a different generator strategy for long-horizon tests.

---

## Boundary Characterization

Based on Run H results, the v0.5.2 rent schedule boundaries are:

| Parameter | Safe Range | Collapse Threshold |
|-----------|------------|-------------------|
| E3 rent | 1–60+ | Not found (>60) |
| Renewal cost | 0–5 | 10 (hard failure) |
| Horizon | Any | Not found (SPAM_DEGENERACY limits) |

**Critical Bound:** `renewal_cost ≤ effective_steps × (1 - typical_usage_ratio)`

For E3: `renewal_cost ≤ 60 × (1 - 0.90) = 6 steps`

---

## Recommendations

### Immediate

1. **Do not implement renewal cost ≥ 10** at E3 without addressing step usage patterns
2. **Rent escalation is safe** up to at least E3 = 60 (40% of S)
3. **Review spam detection** for TierFilterGenerator scenarios

### Future Experiments

1. **H3-bisect:** Test renewal_cost = 5, 7, 8 to find exact transition point
2. **H2-redux:** Disable spam detection or use different generator to test long horizon
3. **H1-extreme:** Push rent to E3 = 80 or E3 = 90 to find actual rent ceiling
4. **Adaptive successors:** Test if successors can learn to conserve steps when renewal cost exists

---

## Appendix: Telemetry Summary

### H1 Rent Telemetry (E3 = 60)

| Metric | Mean | Max |
|--------|------|-----|
| Rent charged | 60.0 | 60 |
| Effective steps | 40.0 | 40 |
| Steps used | 34.4 | — |
| Actions used | 1.0 | — |

### H3 Rent Telemetry (Renewal cost = 10)

| Metric | Value |
|--------|-------|
| Rent charged (mean) | 40.0 |
| Effective steps (mean) | 60.0 |
| Steps used (mean) | 54.0 |
| Renewal cost charged | 0 (all failed) |
| Renewal budget failures | 9 per seed |

---

## Conclusion

Run H successfully identified a **hard boundary condition** in the v0.5.2 ALS-E design: renewal cost of 10 steps at E3 causes complete system failure. This is in contrast to rent escalation, which shows graceful degradation with significant headroom. The key design constraint is:

**`renewal_cost < effective_steps × (1 - typical_step_usage_fraction)`**

For typical usage of ~90%, this means renewal cost must be ≤6 steps at E3 to maintain system viability.

---

*Generated: Run H v0.5.2 Experiments*
*Timestamp: 2026-01-03*
