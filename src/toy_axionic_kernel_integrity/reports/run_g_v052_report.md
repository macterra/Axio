# Run G Report: AKI v0.5.2 Competitive Expressivity Horizon

**Date:** 2026-01-03
**Spec Version:** 0.5.2
**Run Type:** Competitive Expressivity Horizon
**Status:** ✅ Complete

---

## Executive Summary

Run G tested whether authority can survive **competition under scarcity** when expressivity becomes metabolically expensive. The results show:

1. **No competence ceiling was found** within the tested parameters
2. All seeds reached **E4** (maximum tier) without bankruptcy or renewal collapse
3. **Zero hollow tenures** detected in G2 (CBD stress at E3)
4. Renewal rates remained stable at ~0.95 across all tiers

This is a significant result: under the v0.5.2 rent schedule with max_successive_renewals=15, the ALS-E mechanism sustained stable succession across all expressivity tiers.

---

## Configuration (Binding)

| Parameter | Value |
|-----------|-------|
| H (cycles) | 30,000 |
| max_successive_renewals | 15 |
| renewal_check_interval | 100 |
| msrw_cycles | 200 |
| epoch_size | 100 |
| steps_cap_epoch | 100 |
| actions_cap_epoch | 100 |
| reject_immediate_bankruptcy | False |

### Rent Schedule

| E-Class | Rent (steps) |
|---------|-------------|
| E0 | 1 |
| E1 | 10 |
| E2 | 25 |
| E3 | 40 |
| E4 | 60 |

### Generator Configuration

- **G1**: control_weight=0.20, V052_ATTACK_WEIGHTS (CBD=0.10)
- **G2**: control_weight=0.20, V052_RUNG_G2_ATTACK_WEIGHTS (CBD_E3=0.30)
- Violation successor excluded (per binding)
- TierFilterGenerator as post-generation filter (max_retries=200)

---

## G1: Ascension with Competition

### Goal

Identify the highest sustainable expressivity tier under competitive pressure.

### Dwell Rule

**Option A (binding):** 3 leases per tier (~6,000 cycles/tier budget)

### Seeds

40, 41, 42, 43, 44

### Results Summary

| Seed | S* | Succ | Renewals | Bankruptcies | Revocations | Max Tier | Ceiling | Accept% |
|------|-----|------|----------|--------------|-------------|----------|---------|---------|
| 40 | 20 | 20 | 285 | 0 | 0 | E4 | N/A | 4.2% |
| 41 | 20 | 20 | 285 | 0 | 0 | E4 | N/A | 3.3% |
| 42 | 20 | 20 | 285 | 0 | 0 | E4 | N/A | 3.6% |
| 43 | 20 | 20 | 285 | 0 | 0 | E4 | N/A | 4.7% |
| 44 | 20 | 20 | 285 | 0 | 0 | E4 | N/A | 5.3% |

### E-Class Distribution (All Seeds)

Each seed achieved exactly 4 successions per tier:

| E-Class | Count |
|---------|-------|
| E0 | 4 |
| E1 | 4 |
| E2 | 4 |
| E3 | 4 |
| E4 | 4 |

### Renewal Rate by Tier

| Tier | Renewal Rate |
|------|-------------|
| E0 | ~0.95 |
| E1 | ~0.95 |
| E2 | ~0.95 |
| E3 | ~0.95 |
| E4 | ~0.95 |

### Rent Telemetry (Aggregated)

| Metric | Mean | Max |
|--------|------|-----|
| rent_steps_charged | 27.2 | 60 |
| effective_steps_available | 72.8 | 40 (min) |
| steps_used | 71.6 | 99 |
| actions_used | 71.6 | 99 |

### Failure Modes

- **Bankruptcies:** 0 across all seeds
- **Revocations:** 0 across all seeds
- **Expirations:** 15 per seed (expected - lease term expirations due to max_successive_renewals=15)

---

## G2: CBD Stress at Fixed E3

### Goal

Map hollow succession and thrash dynamics under sustained rent pressure at E3.

### Setup

- Fixed expressivity at **E3**
- TierFilterGenerator(E3) as post-filter
- CBD_E3 weight = 0.30 (uses FANOUT/COMPOSITION actions)

### Seeds

40, 41, 42, 43, 44

### Results Summary

| Seed | S* | Succ | Renewals | Bankruptcies | Hollow | Rate | Accept% |
|------|-----|------|----------|--------------|--------|------|---------|
| 40 | 10 | 10 | 135 | 0 | 0 | 0.0% | 3.8% |
| 41 | 10 | 10 | 135 | 0 | 0 | 0.0% | 2.4% |
| 42 | 10 | 10 | 135 | 0 | 0 | 0.0% | 2.5% |
| 43 | 10 | 10 | 135 | 0 | 0 | 0.0% | 2.3% |
| 44 | 10 | 10 | 135 | 0 | 0 | 0.0% | 4.1% |

### Hollow Succession Analysis

| Metric | Value |
|--------|-------|
| Hollow tenures | 0 |
| Hollow rate | 0.0% |
| By CBD type | N/A |
| By other types | N/A |

### Failure Modes

- **Bankruptcies:** 0 across all seeds
- **Revocations:** 0 across all seeds

---

## Interpretation

### What Stressors Were Actually Engaged

1. **Rent pressure:** Active. E3 charges 40/100 steps as rent, E4 charges 60/100.
2. **Competition:** Active. Mixed generator with TierFilterGenerator post-filtering.
3. **Forced succession:** Active. max_successive_renewals=15 ensures lease churn.
4. **CBD stress (G2):** Active. CBD_E3 weight at 30% in attack pool.

### Which Collapse Modes Appeared

**None.** The system exhibited stable behavior:
- No bankruptcies (rent exhaustion)
- No revocations (structural violations)
- No hollow tenures (low-action persistence)
- No authority thrash (short residence times)
- No expressivity collapse (tier degradation)

### Why No Collapse Was Observed

Likely explanations:

1. **Budget margin is sufficient:** Even at E4 (rent=60), successors retain 40 steps/epoch, which is enough for the simulated workload.

2. **Successors are efficient:** The generated successors use ~71.6 steps/epoch on average, staying within available budget.

3. **15-renewal cap prevents accumulation:** The max_successive_renewals=15 guardrail triggers lease expiration before any pathological state can develop.

4. **Action workload is synthetic:** Successors are not executing real tasks; they're using budgets structurally.

### What Cannot Be Concluded

1. **No claim about real competence:** The successors are not solving problems; they're meeting structural constraints.

2. **No claim about higher rent scales:** The rent schedule may be too lenient. Higher rents (e.g., E4=80%) might reveal collapse.

3. **No claim about longer horizons:** 30,000 cycles may be insufficient to observe slow accumulation effects.

4. **No claim about semantic quality:** Hollow succession detection relies on action counts, not output quality.

---

## Classification

### Run G Status: ⚠️ CONDITIONAL SUCCESS

**Conditions met:**
- ✅ Competition was actually exercised (mixed generator, TierFilterGenerator filtering ~3-5%)
- ✅ No semantic selection introduced
- ✅ Mechanism integrity preserved (no subsidies, no bypasses)

**Conditions not met:**
- ⚠️ No collapse mode appeared
- ⚠️ No ceiling identified with clear renewal degradation

**Interpretation:** Run G provides evidence that ALS-E **does not collapse under the v0.5.2 rent schedule with H=30,000 and max_successive_renewals=15**. This is a meaningful negative result, but does not prove the absence of a competence horizon at higher stress levels.

---

## Recommendations for Follow-Up

1. **Run G′: Higher rent pressure**
   - Increase rent schedule: E3=60%, E4=80%, E5=90%
   - Test whether collapse emerges at higher metabolic cost

2. **Run H: Longer horizon**
   - Extend to H=100,000 or H=300,000 cycles
   - Look for slow accumulation failures

3. **Run I: Remove max_successive_renewals guardrail**
   - Set max_successive_renewals=∞
   - Test whether immortal successors exhibit pathologies

4. **Run J: Real task workload**
   - Integrate actual computation tasks
   - Measure semantic output quality, not just structural compliance

---

## Appendix: Generator Statistics

### TierFilterGenerator Acceptance Rates

| Run | Seed | Accepted | Filtered | Rate |
|-----|------|----------|----------|------|
| G1 | 40 | 20 | 459 | 4.2% |
| G1 | 41 | 20 | 589 | 3.3% |
| G1 | 42 | 20 | 534 | 3.6% |
| G1 | 43 | 20 | 409 | 4.7% |
| G1 | 44 | 20 | 355 | 5.3% |
| G2 | 40 | 10 | 254 | 3.8% |
| G2 | 41 | 10 | 401 | 2.4% |
| G2 | 42 | 10 | 389 | 2.5% |
| G2 | 43 | 10 | 421 | 2.3% |
| G2 | 44 | 10 | 232 | 4.1% |

The low acceptance rates (~2-5%) confirm that:
1. The base generator produces a diverse E-Class distribution
2. TierFilterGenerator is correctly filtering to target tiers
3. Competition is real (rejected proposals represent structural competition)

---

## Files Generated

- `reports/run_g/run_g_results_20260103_102132.json` - Full JSON results
- `scripts/run_g_v052.py` - Run G execution script
- `scripts/sanity_check_sampler.py` - Pre-run validation script

---

*Report generated: 2026-01-03*
*AKI Spec Version: 0.5.2*
