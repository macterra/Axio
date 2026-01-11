# AKI v0.8 Run B Report: Amnesty Interval Sensitivity Under Forced Turnover

**Date:** 2026-01-05
**Experiment:** run_b_v080
**Harness Version:** ALS-A (Constitutional Temporal Amnesty)

---

## Executive Summary

Run B tests whether the **long-lapse mode** observed in Run A is governed by the **CTA clock**, by halving the amnesty interval while keeping everything else frozen.

**Key Finding:** The long-lapse mode **compressed proportionally** from L ≈ 20 epochs to L ≈ 10 epochs when AMNESTY_INTERVAL was halved from 10 to 5. This confirms that the CTA clock governs the long-lapse boundary. The recovery-without-amnesty rate remained unchanged at 69%, demonstrating that the short-lapse recovery mechanism (fresh candidates) is independent of AMNESTY_INTERVAL.

---

## Configuration

| Parameter | Run A | Run B | Change |
|-----------|-------|-------|--------|
| Horizon | 5,000 cycles | 5,000 cycles | — |
| K (eligibility threshold) | 3 | 3 | — |
| max_successive_renewals | 3 | 3 | — |
| renewal_check_interval | 50 cycles | 50 cycles | — |
| **AMNESTY_INTERVAL** | **10 epochs** | **5 epochs** | **HALVED** |
| AMNESTY_DECAY | 1 | 1 | — |
| Candidate Pool Policy | V060_DEFAULT | V060_DEFAULT | — |
| Seeds | 50, 51, 52, 53, 54 | 50, 51, 52, 53, 54 | — |

---

## Summary Table

| Seed | Post-Init Successions | Avg \|C_ELIG\| | Min \|C_ELIG\| | Lapses | NULL_AUTH (cycles) | Amnesty Events | Recoveries | No-Amnesty Recoveries | Median L | Median A | Median RY | Dominant Regime | Terminal Cause |
|------|----------------------|---------------|---------------|--------|-------------------|----------------|------------|----------------------|----------|----------|-----------|-----------------|----------------|
| 50 | 22 | 3.82 | 0 | 2 | 548 | 2 | 2 | 1 | 5.5 | 16.5 | 5.25 | RECOVERING | HORIZON_EXHAUSTED |
| 51 | 24 | 11.00 | 11 | 0 | 0 | 0 | 0 | 0 | — | — | — | NO_LAPSE | HORIZON_EXHAUSTED |
| 52 | 21 | 4.09 | 0 | 4 | 646 | 2 | 4 | 3 | 1.0 | 8.0 | 4.00 | RECOVERING | HORIZON_EXHAUSTED |
| 53 | 20 | 2.95 | 0 | 5 | 845 | 2 | 5 | 4 | 2.0 | 8.0 | 4.00 | RECOVERING | HORIZON_EXHAUSTED |
| 54 | 21 | 3.91 | 0 | 2 | 598 | 2 | 2 | 1 | 6.0 | 18.0 | 4.20 | RECOVERING | HORIZON_EXHAUSTED |

---

## Episode Table

| Seed | Episode # | Lapse Cause | Lapse Epochs (L) | Amnesty Events | Recovered? | Authority Epochs (A) | RY | Stutter? | No-Amnesty? |
|------|-----------|-------------|------------------|----------------|------------|---------------------|------|----------|-------------|
| 50 | 1 | SEMANTIC | 1 | 0 | Yes | 8 | 8.00 | No | Yes |
| 50 | 2 | SEMANTIC | 10 | 2 | Yes | 25 | 2.50 | No | No |
| 52 | 1 | SEMANTIC | 1 | 0 | Yes | 12 | 12.00 | No | Yes |
| 52 | 2 | SEMANTIC | 1 | 0 | Yes | 4 | 4.00 | No | Yes |
| 52 | 3 | SEMANTIC | 1 | 0 | Yes | 4 | 4.00 | No | Yes |
| 52 | 4 | SEMANTIC | 10 | 2 | Yes | 23 | 2.30 | No | No |
| 53 | 1 | SEMANTIC | 2 | 0 | Yes | 8 | 4.00 | No | Yes |
| 53 | 2 | SEMANTIC | 2 | 0 | Yes | 8 | 4.00 | No | Yes |
| 53 | 3 | SEMANTIC | 1 | 0 | Yes | 4 | 4.00 | No | Yes |
| 53 | 4 | SEMANTIC | 2 | 0 | Yes | 4 | 2.00 | No | Yes |
| 53 | 5 | SEMANTIC | 10 | 2 | Yes | 19 | 1.90 | No | No |
| 54 | 1 | SEMANTIC | 2 | 0 | Yes | 12 | 6.00 | No | Yes |
| 54 | 2 | SEMANTIC | 10 | 2 | Yes | 24 | 2.40 | No | No |

---

## Bimodality Analysis

### Lapse Duration Distribution

| Metric | Run A | Run B | Change |
|--------|-------|-------|--------|
| Fraction with L ≤ 2 | 69% | 69% | — |
| Fraction with L ≥ 10 | 31% | 31% | — |
| Fraction with L ≥ 20 | 31% | **0%** | **-31pp** |
| Long-lapse median (L ≥ 5) | ~20 | **10** | **-50%** |

### Key Observation

**The bimodal structure is preserved, but the long-lapse mode scales with AMNESTY_INTERVAL:**

- Run A: Long lapses clustered at L ≈ 20 = 2 × AMNESTY_INTERVAL (10)
- Run B: Long lapses clustered at L ≈ 10 = 2 × AMNESTY_INTERVAL (5)

This is **exact proportional compression**. The factor of 2 appears because recovery after amnesty requires:
1. First amnesty at epoch 10 (Run A) or epoch 5 (Run B)
2. Succession attempt after amnesty fires
3. If first amnesty insufficient, second amnesty at epoch 20 (Run A) or epoch 10 (Run B)

In both runs, all long lapses required exactly 2 amnesty events before recovery.

---

## Aggregate Statistics

| Metric | Run A | Run B | Change |
|--------|-------|-------|--------|
| Total Lapses | 13 | 13 | — |
| Total Recoveries | 13 | 13 | — |
| Recovery Rate | 100% | 100% | — |
| Total Amnesty Events | 8 | 8 | — |
| Total NULL_AUTH Cycles | 4,637 | **2,637** | **-43%** |
| Recoveries Without Amnesty | 9 (69%) | 9 (69%) | — |
| Recoveries With Amnesty | 4 (31%) | 4 (31%) | — |
| Stutter Recoveries | 0 (0%) | 0 (0%) | — |
| Semantic Lapse Fraction | 100% | 100% | — |

### Key Observation

**NULL_AUTHORITY time reduced by 43%** (4,637 → 2,637 cycles) despite identical lapse count. This is because long lapses terminate earlier (L=10 vs L=20), halving their contribution to total lapse time.

---

## Regime Distribution

| Regime | Run A | Run B |
|--------|-------|-------|
| NO_LAPSE | 1 (seed 51) | 1 (seed 51) |
| RECOVERING | 4 | 4 |
| PERMANENT_LAPSE | 0 | 0 |
| STUTTER_DOMINANT | 0 | 0 |

Regime distribution is **identical** — AMNESTY_INTERVAL does not affect regime classification in this geometry.

---

## Conservative Interpretation Paragraphs

### Seed 50

Lapse occurred (2 episodes). The first was short (L=1), recovering without amnesty via fresh candidates. The second was long (L=10), requiring 2 amnesty events — **compressed from L=20 in Run A**. Post-recovery authority spans increased (A=8 and A=25 vs Run A's A=8 and A=15), likely due to RNG-driven pool composition differences. The long-lapse mode clearly tracked AMNESTY_INTERVAL.

### Seed 51

No lapse occurred. Identical to Run A — this seed maintains continuous authority regardless of AMNESTY_INTERVAL. Cannot infer sensitivity.

### Seed 52

Lapse occurred (4 episodes). Three short lapses (L=1) recovered without amnesty; one long lapse (L=10) required 2 amnesty events. **Run A showed the same 3:1 short:long ratio with L=20 for the long lapse.** The long-lapse mode compressed exactly as predicted. Post-recovery authority span for the long lapse increased (A=23 vs Run A's A=13), suggesting more favorable pool composition at the compressed recovery point.

### Seed 53

Lapse occurred (5 episodes, highest count). Four short lapses (L=1-2) recovered without amnesty; one long lapse (L=10) required 2 amnesty events. **Run A showed the same 4:1 short:long ratio with L=20.** The compression is exact. Recovery yield for the long lapse improved (RY=1.90 vs Run A's RY=0.45) because authority gained remained similar while lapse duration halved.

### Seed 54

Lapse occurred (2 episodes). Same pattern as Seed 50: one short (L=2), one long (L=10). **Run A had L=20 for the long lapse.** Compression confirmed. Post-recovery authority (A=24) exceeded Run A (A=14).

---

## Interpretation Summary

### What Can Be Concluded

1. **The CTA clock governs the long-lapse mode** — Halving AMNESTY_INTERVAL from 10 to 5 halved the long-lapse duration from ~20 to ~10 epochs.

2. **The bimodal structure is preserved** — The ratio of short-lapse to long-lapse episodes (9:4 = 69%:31%) is identical across runs.

3. **Short-lapse recovery is AMNESTY_INTERVAL-independent** — Recoveries without amnesty (9/13 = 69%) are identical, confirming that fresh-candidate recovery does not depend on the CTA clock.

4. **NULL_AUTHORITY time is AMNESTY_INTERVAL-dependent** — Total lapse cycles reduced by 43% (4,637 → 2,637) because long lapses terminate earlier.

5. **Recovery yield improves for long lapses** — Since authority gained is similar but lapse duration halved, RY roughly doubles for long-lapse episodes.

6. **All invariants preserved** — No verifier execution during lapse, no streak changes except CTA, succession at scheduled boundaries only.

### What Cannot Be Concluded

- Competence or alignment of any policy
- Optimal AMNESTY_INTERVAL value
- Generality beyond this geometry (K=3, V060_DEFAULT pool)
- That AMNESTY_INTERVAL=5 is "better" than 10 (trade-offs may exist)
- Whether fresh candidates or CTA is the "primary" recovery mechanism (both contribute)

---

## Run Classification

**Run B is INFORMATIVE** because:

- ✓ Long-lapse mode shifted exactly as predicted (L ≈ 20 → L ≈ 10)
- ✓ Bimodal structure preserved (same 69%:31% short:long ratio)
- ✓ NULL_AUTHORITY time reduced proportionally
- ✓ Recovery-without-amnesty rate unchanged (confirming independence)

**Run B is NOT a failure** because:

- ✓ Single axis changed (AMNESTY_INTERVAL only)
- ✓ All invariants preserved
- ✓ Telemetry supports episode-level L, A, RY reconstruction
- ✓ CTA logic correct (fires at epochs 5, 10 instead of 10, 20)

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
| CTA fires at AMNESTY_INTERVAL epochs | ✓ Verified (5, 10 instead of 10, 20) |

---

## Data Source

Results file: `reports/run_b_v080_20260105_140048.json`
