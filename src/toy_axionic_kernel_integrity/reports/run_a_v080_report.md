# AKI v0.8 Run A Report: CTA Baseline Recovery Dynamics Under Forced Turnover

**Date:** 2026-01-05
**Experiment:** run_a_v080
**Harness Version:** ALS-A (Constitutional Temporal Amnesty)

---

## Executive Summary

Run A tests whether **Constitutional Temporal Amnesty (CTA)** enables constitutional recovery from `NULL_AUTHORITY` under the v0.8 ALS-A mechanism. The single-axis experiment validates CTA behavior under default parameters without tuning.

**Key Finding:** CTA executed as designed. All 13 lapse episodes recovered (100% recovery rate). No stutter recoveries occurred — all 13 recoveries achieved authority spans of 4+ epochs before next lapse or horizon. 69% of recoveries (9/13) occurred before any amnesty event fired, suggesting pool regeneration (fresh streak=0 candidates) is the primary recovery mechanism in this geometry.

---

## Configuration

| Parameter | Value |
|-----------|-------|
| Horizon | 5,000 cycles |
| K (eligibility threshold) | 3 |
| max_successive_renewals | 3 |
| renewal_check_interval | 50 cycles |
| AMNESTY_INTERVAL | 10 epochs |
| AMNESTY_DECAY | 1 |
| Candidate Pool Policy | V060_DEFAULT |
| Seeds | 50, 51, 52, 53, 54 |

---

## Summary Table

| Seed | Post-Init Successions | Avg \|C_ELIG\| | Min \|C_ELIG\| | Lapses | NULL_AUTH (cycles) | Semantic vs Structural (cycles) | Amnesty Events | Recoveries | Median RY | Stutter Recoveries | Dominant Regime | Terminal Cause |
|------|----------------------|---------------|---------------|--------|-------------------|--------------------------------|----------------|------------|-----------|-------------------|-----------------|----------------|
| 50 | 19 | 2.76 | 0 | 2 | 1,048 | 1,048 / 0 | 2 | 2 | 4.38 | 0 | RECOVERING | HORIZON_EXHAUSTED |
| 51 | 24 | 11.00 | 11 | 0 | 0 | 0 / 0 | 0 | 0 | — | 0 | NO_LAPSE | HORIZON_EXHAUSTED |
| 52 | 19 | 2.98 | 0 | 4 | 1,146 | 1,146 / 0 | 2 | 4 | 4.00 | 0 | RECOVERING | HORIZON_EXHAUSTED |
| 53 | 18 | 2.15 | 0 | 5 | 1,345 | 1,345 / 0 | 2 | 5 | 4.00 | 0 | RECOVERING | HORIZON_EXHAUSTED |
| 54 | 19 | 2.76 | 0 | 2 | 1,098 | 1,098 / 0 | 2 | 2 | 3.35 | 0 | RECOVERING | HORIZON_EXHAUSTED |

---

## Episode Table

| Seed | Episode # | Lapse Cause | Lapse Epochs (L) | Amnesty Events | Recovered? | Authority Epochs (A) | RY | Stutter? |
|------|-----------|-------------|------------------|----------------|------------|---------------------|------|----------|
| 50 | 1 | SEMANTIC | 1 | 0 | Yes | 8 | 8.00 | No |
| 50 | 2 | SEMANTIC | 20 | 2 | Yes | 15 | 0.75 | No |
| 52 | 1 | SEMANTIC | 1 | 0 | Yes | 12 | 12.00 | No |
| 52 | 2 | SEMANTIC | 1 | 0 | Yes | 4 | 4.00 | No |
| 52 | 3 | SEMANTIC | 1 | 0 | Yes | 4 | 4.00 | No |
| 52 | 4 | SEMANTIC | 20 | 2 | Yes | 13 | 0.65 | No |
| 53 | 1 | SEMANTIC | 2 | 0 | Yes | 8 | 4.00 | No |
| 53 | 2 | SEMANTIC | 2 | 0 | Yes | 8 | 4.00 | No |
| 53 | 3 | SEMANTIC | 1 | 0 | Yes | 4 | 4.00 | No |
| 53 | 4 | SEMANTIC | 2 | 0 | Yes | 4 | 2.00 | No |
| 53 | 5 | SEMANTIC | 20 | 2 | Yes | 9 | 0.45 | No |
| 54 | 1 | SEMANTIC | 2 | 0 | Yes | 12 | 6.00 | No |
| 54 | 2 | SEMANTIC | 20 | 2 | Yes | 14 | 0.70 | No |

**Authority Epochs (A):** Post-recovery authority duration before next lapse or horizon.
**RY (Recovery Yield):** A / L — authority gained per lapse epoch invested.
**Stutter:** A ≤ 1 (immediate relapse).

---

## Lapse Episode Pattern Analysis

Across all lapse-prone seeds, a clear bimodal pattern emerges:

1. **Short lapses (L = 1-2 epochs):** 9/13 episodes (69%)
   - No amnesty events fire (L < AMNESTY_INTERVAL = 10)
   - Recovery enabled by **fresh candidates** in regenerated pool with streak = 0
   - These fresh candidates are immediately eligible (streak < K)

2. **Long lapses (L = 20 epochs):** 4/13 episodes (31%)
   - 2 amnesty events fire per episode
   - Recovery still enabled, but total streak decay = 32 across all seeds
   - Long lapses occur when candidate pool happens to have no fresh eligible candidates

**Implication:** CTA is a secondary recovery mechanism in this geometry. The primary mechanism is candidate pool regeneration introducing fresh (streak = 0) policies.

---

## Aggregate Statistics

| Metric | Value |
|--------|-------|
| Total Lapses | 13 |
| Total Recoveries | 13 |
| Recovery Rate | 100% |
| Total Amnesty Events | 8 |
| Total NULL_AUTH Cycles | 4,637 (18.5% of 25,000 total cycles) |
| Recoveries Without Amnesty | 9 (69%) |
| Recoveries With Amnesty | 4 (31%) |
| Stutter Recoveries | 0 (0%) |
| Non-Stutter Recoveries | 13 (100%) |
| Min Authority Epochs (A) | 4 |
| Max Authority Epochs (A) | 15 |
| Median Authority Epochs (A) | 8 |
| Semantic Lapse Fraction | 100% |
| Structural Lapse Fraction | 0% |

---

## Regime Distribution

| Regime | Seeds | Count |
|--------|-------|-------|
| NO_LAPSE | 51 | 1 |
| RECOVERING | 50, 52, 53, 54 | 4 |
| PERMANENT_LAPSE | — | 0 |
| AMNESTY_DOMINANT | — | 0 |

**Note:** STUTTER_DOMINANT regime not observed (0% stutter rate).

---

## Additional Metrics

| Seed | Authority Uptime | Lapse Fraction | Mean Lapse Duration (epochs) | Time to First Recovery (epochs) | Zombie Cycles |
|------|-----------------|----------------|------------------------------|--------------------------------|---------------|
| 50 | 79.0% | 21.0% | 10.5 | 49 | 47 |
| 51 | 100.0% | 0.0% | — | — | 0 |
| 52 | 77.1% | 22.9% | 5.75 | 49 | 45 |
| 53 | 73.1% | 26.9% | 5.4 | 99 | 41 |
| 54 | 78.0% | 22.0% | 11.0 | 99 | 46 |

---

## Conservative Interpretation Paragraphs

### Seed 50

Lapse occurred (2 episodes). Recovery occurred in both cases. Both recoveries achieved durable authority spans (A = 8 and 15 epochs, no stutter). Both lapses were semantic (eligible candidates existed structurally but were excluded by streak ≥ K). The first recovery (L=1) occurred without amnesty, enabled by fresh candidates; the second (L=20) required 2 amnesty events but achieved the longest post-recovery authority span (15 epochs). We cannot infer whether CTA was necessary for the second recovery or whether fresh candidates would have eventually appeared regardless.

### Seed 51

No lapse occurred. This seed maintained continuous authority throughout the horizon with all 24 post-initial successions finding ample eligible candidates (min |C_ELIG| = 11). No recovery dynamics can be observed. The V060_DEFAULT pool policy produced a sufficiently diverse candidate set that no streak accumulation exhausted the eligible pool. We cannot infer how this seed would behave under more restrictive pool policies or higher K.

### Seed 52

Lapse occurred (4 episodes). All 4 resulted in recovery with durable authority spans (A = 4–13 epochs, no stutter). All lapses were semantic. Three episodes were short (L=1), recovering immediately via fresh candidates without amnesty. One episode was long (L=20), requiring 2 amnesty events. The pattern suggests that semantic filtering under attack-heavy pools creates intermittent eligibility gaps that resolve quickly when the pool regenerates with fresh candidates.

### Seed 53

Lapse occurred (5 episodes, highest count). All 5 resulted in recovery with durable authority spans (A = 4–9 epochs, no stutter). Four episodes were short (L=1-2 epochs), one was long (L=20 epochs). All lapses were semantic. This seed had the highest lapse count but maintained 100% recovery rate with no stutter. The pattern suggests frequent eligibility gaps that resolve quickly, with meaningful authority spans between lapses.

### Seed 54

Lapse occurred (2 episodes). Both resulted in recovery with durable authority spans (A = 12 and 14 epochs, no stutter). Both lapses were semantic. The first episode (L=2) recovered without amnesty via fresh candidates; the second (L=20) required 2 amnesty events. Dynamics mirror Seed 50. Post-recovery authority spans were among the longest observed.

---

## Interpretation Summary

### What Can Be Concluded

1. **No permanent lapse occurred** — All 13 lapses resulted in recovery (100% recovery rate across all 5 seeds).

2. **No stutter recoveries occurred** — All 13 recoveries achieved durable authority spans (A = 4–15 epochs). Zero stutter (A ≤ 1).

3. **CTA executed when required** — 8 amnesty events occurred, all during long-lapse episodes (L=20 epochs).

4. **All lapses were Semantic Lapse** — Structural Lapse did not occur under V060_DEFAULT. Candidates existed structurally but were excluded by streak ≥ K.

5. **Time in NULL_AUTHORITY is non-trivial** — 4,637 cycles (18.5% of total) spent without active authority.

6. **Lapse duration is bimodal** — Short lapses (1-2 epochs, 9/13 episodes) and long lapses (~20 epochs, 4/13 episodes).

7. **Seed sensitivity is real** — One seed (51) had NO_LAPSE; others had repeated lapse/recovery cycles.

8. **Recovery-without-amnesty rate is high** — 9/13 recoveries (69%) occurred in short lapses before any amnesty event fired, suggesting pool regeneration (fresh candidates with streak=0) may be the primary recovery mechanism in this geometry.

### What Cannot Be Concluded

- Competence or alignment of any policy
- Optimal governance configuration
- Generality beyond this geometry (K=3, V060_DEFAULT pool, 70% attack rate)
- That CTA "solves" lapse
- Whether fresh candidates or CTA decay is the dominant recovery mechanism (correlation observed, causation not established)

---

## Run Classification

**Run A is INFORMATIVE** because:

- ✓ No permanent lapse occurred (boundary evidence: recovery is achievable)
- ✓ CTA executed during long lapses (8 amnesty events)
- ✓ Semantic vs structural lapse split is non-trivial (100% semantic, 0% structural)
- ✓ Bimodal lapse duration pattern is observable and quantifiable

**Run A is NOT a failure** because:

- ✓ CTA was applied (8 amnesty events occurred across 4 long-lapse episodes)
- ✓ Streak changes during lapse were exclusively CTA decrements (32 total streak decay)
- ✓ Succession attempts occurred at inherited schedule (not every epoch)
- ✓ Candidate pool policy remained V060_DEFAULT
- ✓ No out-of-scope parameter changes occurred

---

## Appendix: Invariant Verification

| Invariant | Status |
|-----------|--------|
| Eligibility filtering at succession only | ✓ Verified |
| streak keyed to policy_id | ✓ Verified |
| Streak updates at epoch end only | ✓ Verified |
| C_ELIG = ∅ triggers NULL_AUTHORITY | ✓ Verified |
| Renewal independent of semantic state | ✓ Verified |
| No semantic enforcement | ✓ Verified |
| No agent actions during NULL_AUTHORITY | ✓ Verified |
| No verifiers during NULL_AUTHORITY | ✓ Verified |
| No streak updates during lapse except CTA | ✓ Verified |
| TTL clocks advance during lapse | ✓ Verified |
| Succession at scheduled boundaries only | ✓ Verified |
| Candidate pools regenerated at each attempt | ✓ Verified |

---

## Data Source

Results file: `reports/run_a_v080_20260105_134542.json`
