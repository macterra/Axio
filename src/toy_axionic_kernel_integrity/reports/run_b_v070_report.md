# AKI v0.7 Run B: Forced Succession Eligibility Activation Report

**Experiment ID:** run_b_v070_1767556375
**Date:** 2026-01-04
**Spec Version:** 0.7 (ALS-G)

## Executive Summary

Run B establishes that **eligibility-coupled succession actively filters candidates** when succession events are forced to occur. Under forced turnover (max_successive_renewals = 3), the eligibility mechanism:

1. **Activated**: 1,845 eligibility rejections observed
2. **Produced constitutional lapse**: 11 NULL_AUTHORITY events across 4 of 5 seeds
3. **Demonstrated regime transition**: In 4 of 5 seeds, C_ELIG contracted rapidly and reached ∅ within ~4–5 epochs under forced turnover

This confirms that v0.7's eligibility gating is a **latent constitutional mechanism** whose effects emerge under turnover pressure **in the tested candidate pool and renewal geometry**.

## Experiment Design

### Parameters (Binding per instructions)

- **Horizon:** 5,000 cycles (100 × renewal_check_interval)
- **Seeds:** [50, 51, 52, 53, 54]
- **K:** 3 (spec default eligibility threshold)
- **max_successive_renewals:** 3 (forced turnover)
- **renewal_check_interval:** 50 cycles

### Experimental Axis

Single varied parameter: `max_successive_renewals = 3`

All other parameters unchanged from Run A.

### Stop Rules

Runs terminated on horizon exhaustion. No degeneracy, bankruptcy, or revocation occurred.

## Results

### Summary Table

| Seed | Post-Init | Mean Res. | Avg |C_ELIG| | Lapses | NULL_AUTH | Regime | Terminal |
|------|-----------|-----------|----------------|--------|-----------|--------|----------|
| 50 | 16 | 3.98 | 1.66 | 4 | 148 | CONSTITUTIONAL_LAPSE | HORIZON_EXHAUSTED |
| 51 | 24 | 3.98 | 11.00 | 0 | 0 | LATENT | HORIZON_EXHAUSTED |
| 52 | 16 | 3.98 | 1.68 | 2 | 49 | CONSTITUTIONAL_LAPSE | HORIZON_EXHAUSTED |
| 53 | 16 | 3.98 | 2.12 | 3 | 98 | CONSTITUTIONAL_LAPSE | HORIZON_EXHAUSTED |
| 54 | 16 | 3.98 | 1.64 | 2 | 49 | CONSTITUTIONAL_LAPSE | HORIZON_EXHAUSTED |

### Aggregates

| Metric | Value |
|--------|-------|
| Total post-init successions | 88 |
| Total forced turnovers | 93 |
| Total eligibility rejections | 1,845 |
| Total lapses | 11 |
| Time in NULL_AUTHORITY | 344 cycles |
| Regime distribution | CONSTITUTIONAL_LAPSE: 4, LATENT: 1 |

### Eligibility Activation Timeline

The timeline shows rapid eligibility contraction in most seeds:

| Epoch | Eligible Evaluations / Total Evaluations | Interpretation |
|-------|------------------------------------------|----------------|
| 0 | 11/11 (100%) | Initial state, no streaks |
| 3 | 69-93/187 (37-50%) | Streaks accumulating, filtering begins |
| 4 | 1-2/22-44 (5-9%) | Most candidates ineligible |
| 5+ | 0/11 (0%) (4/5 seeds) | C_ELIG = ∅ observed; constitutional lapse triggered in those seeds |

*Counts aggregate across candidate-evaluation attempts within the epoch (including generator retries). This is not the per-succession pool size.*

Seed 51 was an outlier: it remained in LATENT regime with 100% eligibility throughout. This may indicate a fortunate sequence of SEM_PASS events that reset streaks.

## Telemetry

### A) Succession Activation

- **Total successions:** 93 (88 post-initial + 5 initial)
- **Mean residence time:** 3.98 epochs (~199 cycles)
- **Residence distribution:** Tightly clustered due to forced 3-renewal limit

### B) Eligibility Dynamics

At each succession event (excluding initial):
- Per-succession candidate list size is stable at 11, but the report's "candidate evaluations" metrics aggregate across retries and therefore exceed 11
- |C_ELIG| ranged from 0 to 11
- Rejection rate: 1,845 / (1,845 + eligible) ≈ 95% after epoch 4

### C) Semantic Streak Dynamics

- **Max streak reached:** 100+ per policy (all policies exhausted eligibility)
- **Streak resets (SEM_PASS):** Rare, except Seed 51
- **Sawtooth patterns:** Not observed at significant frequency

### D) Constitutional Lapse

- **Lapse events:** 11 total
- **Time in NULL_AUTHORITY:** 344 cycles
- **Confirmation:** No streak updates during lapse (per spec invariant)

### E) Structural Integrity Checks

- **Renewal success rate:** 100% (before forced expiration)
- **Commitment evaluation:** Continued during active authority
- **No semantic influence on renewal or enforcement**

## Regime Classification

| Regime | Seeds | Description |
|--------|-------|-------------|
| LATENT | 1 (Seed 51) | Eligibility remains near full despite forced succession |
| FILTERING_ACTIVE | 4 (intermediate phases) | Eligibility reductions observed prior to lapse |
| CONSTITUTIONAL_LAPSE | 4 (Seeds 50, 52, 53, 54) | C_ELIG = ∅ occurs and system enters NULL_AUTHORITY |

## Analysis

Run B confirms that eligibility gating becomes **constitutionally active** when turnover is forced.

### Observed Dynamics

1. **Streak accumulation is rapid**: Under forced turnover, semantic failure streaks accumulate faster than they reset.
2. **Eligibility contraction is rapid in most seeds**: Transition from full eligibility to near-zero eligibility occurs within 4–5 epochs under forced turnover.
3. **NULL_AUTHORITY is reachable**: Constitutional lapse is not a theoretical construct—it occurs under moderate turnover pressure.

### Seed 51 Outlier

Seed 51 maintained 100% eligibility throughout. Analysis of its trajectory would reveal:
- Whether SEM_PASS events occurred at higher frequency
- Whether the random candidate selection avoided high-streak policies
- This is consistent with stochastic variance under a non-optimizing, selection-only mechanism.

### Structural Integrity

All v0.7 invariants held:
1. ✅ Eligibility filtering at succession only
2. ✅ Streak keyed to stable `policy_id`
3. ✅ No streak updates during NULL_AUTHORITY
4. ✅ Renewal independent of semantic state

## Conservative Interpretation

Turnover pressure was applied via `max_successive_renewals = 3`.

**Eligibility filtering ACTIVATED:**
- Total eligibility rejections: 1,845
- Post-init successions: 88
- Forced turnovers: 93

**Constitutional lapse OCCURRED:**
- Lapse events: 11
- Time in NULL_AUTHORITY: 344 cycles

**What CANNOT be inferred beyond succession-gated selection:**
- Improved competence (not measured)
- Optimal governance (not defined)
- Semantic success (not evaluated beyond structural compliance)
- Alignment properties (out of scope)

## Conclusion

Run B demonstrates that v0.7's eligibility mechanism is **structurally sound and constitutionally active** under forced turnover.

Key findings:
1. Eligibility gating **filters candidates** when succession occurs
2. Constitutional lapse (**NULL_AUTHORITY**) is **reachable** under moderate turnover
3. The mechanism is **latent under stable authority** (Run A) but **active under turnover pressure** (Run B)

Run B does not test competence, alignment, or governance quality. It establishes that the constitutional mechanism operates as specified.

---

**Files Generated:**
- `reports/run_b_v070_1767556375.json` - Raw experiment data
- `reports/run_b_v070_report.md` - This report
