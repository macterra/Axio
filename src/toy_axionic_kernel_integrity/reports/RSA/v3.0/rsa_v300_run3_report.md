# RSA v3.0 Run 3 Report
## Model L: CTA_PHASE_LOCKER

**Date**: 2026-01-08
**Protocol**: RSA v3.0 (RSA-SA-0)
**AKI Config Hash**: `fd58b6e5`
**RSA Config Hash**: `23fee8ac`

---

## 1. Run Parameters

| Parameter | Value |
|-----------|-------|
| Model | L (CTA_PHASE_LOCKER) |
| State | Last observed CTA phase (4 values) |
| Policy | current_phase ≠ state → INVALID_COMMIT; else → COMPLIANT |
| State update | state ← current_phase |
| Horizon | 300,000 cycles = 6,000 epochs |
| Tail window | 5,000 epochs |
| Seeds | [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768] |

---

## 2. Pre-Run Gates

| Gate | Result |
|------|--------|
| 2.1 Static exercised-state | ✓ PASS |
| 2.2 Strategy map totality | ✓ PASS |

---

## 3. Per-Seed Results

| Seed | AA (ppm) | Lapses | Max Lapse | Phase Trans | Inv Commit | States | Failure Class |
|------|----------|--------|-----------|-------------|------------|--------|---------------|
| 42 | 178,540 | 1,967 | 10 | 7,868 | 7,868 | 4 | HORIZON_EXHAUSTED |
| 137 | 207,790 | 1,874 | 10 | 7,496 | 7,496 | 4 | HORIZON_EXHAUSTED |
| 256 | 215,300 | 1,840 | 10 | 7,360 | 7,360 | 4 | HORIZON_EXHAUSTED |
| 512 | 220,053 | 1,837 | 10 | 7,348 | 7,348 | 4 | HORIZON_EXHAUSTED |
| 1024 | 236,653 | 1,816 | 10 | 7,264 | 7,264 | 4 | HORIZON_EXHAUSTED |
| 2048 | 199,400 | 1,841 | 10 | 7,364 | 7,364 | 4 | HORIZON_EXHAUSTED |
| 4096 | 190,163 | 1,931 | 10 | 7,724 | 7,724 | 4 | HORIZON_EXHAUSTED |
| 8192 | 199,000 | 1,882 | 10 | 7,528 | 7,528 | 4 | HORIZON_EXHAUSTED |
| 16384 | 209,653 | 2,021 | 10 | 8,084 | 8,084 | 4 | HORIZON_EXHAUSTED |
| 32768 | 237,470 | 1,836 | 10 | 7,344 | 7,344 | 4 | HORIZON_EXHAUSTED |

---

## 4. Aggregate Statistics

| Metric | Mean | Std | Min | Max |
|--------|------|-----|-----|-----|
| AA (ppm) | 209,402 | 18,892 | 178,540 | 237,470 |
| Lapses | 1,884.5 | — | 1,816 | 2,021 |
| Renewal success rate (ppm) | 998,895 | — | — | — |
| Ineligibility fraction | 79.06% | — | — | — |

**Total lapses across all seeds**: 18,845
**Total phase transitions across all seeds**: 75,380
**Total INVALID_COMMIT emissions**: 75,380
**Invalid-on-transition rate (agg)**: 1.0000 (100% of phase transitions produced attack)

---

## 5. Recovery Time Distribution (RTD)

### Aggregate RTD

| Bucket | Count | Percentage |
|--------|-------|------------|
| 1 | 8,246 | 43.8% |
| 2 | 4,061 | 21.6% |
| 3 | 2,330 | 12.4% |
| 5 | 2,268 | 12.0% |
| 10 | 1,940 | 10.3% |
| 30+ | 0 | 0% |

**Total lapses**: 18,845
**Mean recovery time**: 2.57 epochs
**Median recovery time**: 2.00 epochs
**Min recovery time**: 1 epoch
**Max recovery time**: 10 epochs
**Stdev recovery time**: 2.16 epochs

---

## 6. Comparison with Baseline and Prior Runs

| Metric | Run 0 (Baseline) | Run 1a (J, N=50) | Run 1b (J, N=100) | Run 2 (K) | Run 3 (L) |
|--------|------------------|------------------|-------------------|-----------|-----------|
| AA (ppm) | 665,702 | 402,601 | 175,730 | 999,988 | **209,402** |
| Δ AA vs baseline | — | −39.5% | −73.6% | +50.2% | **−68.5%** |
| Mean lapses | 5.70 | 1,512.10 | 1,970.20 | 0.10 | **1,884.50** |
| Mean recovery time | — | 2.44 epochs | 2.57 epochs | 1.00 epoch | **2.57 epochs** |
| Attack frequency | 0% | 2.0% | 1.0% | 0.0017% | **125.6%** |
| Terminal failures | 0 | 0 | 0 | 0 | **0** |

---

## 7. Exercised State Verification

| Check | Result |
|-------|--------|
| Static exercised-state | ✓ PASS |
| Dynamic exercised-state (≥2 states per seed) | 10/10 PASS |
| Distinct states observed | 4 (all 4 CTA phases for all seeds) |
| State transition count total | 75,380 |

---

## 8. Integrity Block

```
exercised_state_static_ok: True
exercised_state_dynamic_ok: 10/10 seeds
state_transition_count_total: 75,380
total_phase_transitions: 75,380
total_invalid_commit_emissions: 75,380
total_epochs: 60,000
invalid_on_transition_rate (agg): 1.0000
```

---

## 9. Analysis

### 9.1 Extreme Attack Frequency

Model L produces an attack rate of **125.6%** (75,380 attacks / 60,000 epochs). This is possible because:
- CTA phase transitions occur within epochs, not just between them
- Each lapse → recovery cycle traverses multiple phases (INACTIVE → EARLY → MID → LATE → INACTIVE)
- Each transition triggers an attack

Despite this extreme attack rate, Model L does **not** induce terminal failure.

### 9.2 Comparison with Model J

| Model | Trigger | Attack rate | AA degradation |
|-------|---------|-------------|----------------|
| J (N=50) | Modular counter | 2.0% | −39.5% |
| J (N=100) | Modular counter | 1.0% | −73.6% |
| L | Phase transition | 125.6% | −68.5% |

Model J at N=100 (1% attack rate) produces slightly worse degradation than Model L (125.6% attack rate). This confirms the "inverse attack-rate paradox": **attack timing dominates attack frequency**.

### 9.3 Phase Transitions Are Not a Vulnerability

Model L attacks on every CTA phase boundary, yet:
- Max lapse remains bounded at 10 epochs (CTA limit)
- Recovery time is stable at 2.57 epochs
- No terminal failures occur

The CTA mechanism is robust to phase-boundary attacks because:
1. Phase transitions are normal operation during recovery
2. Attacking during transitions doesn't prevent recovery completion
3. The amnesty mechanism resets eligibility independent of attack timing

### 9.4 Self-Amplifying but Self-Limiting

Unlike Model K (which is self-limiting because ELIG_EDGE is rare), Model L is **self-amplifying**: each attack triggers CTA activity, which creates more phase transitions, which triggers more attacks.

However, this amplification is bounded by:
- CTA's 10-epoch max amnesty window
- The finite duration of each lapse → recovery cycle
- The constitutional integrity constraints that prevent cascading collapse

### 9.5 All 4 CTA Phases Exercised

Every seed observed all 4 CTA phases (CTA_INACTIVE, CTA_EARLY, CTA_MID, CTA_LATE), confirming the adversary exercised its full state space.

---

## 10. Conclusions

1. **Run 3 is procedurally valid**: All gates passed, 10/10 seeds completed, all 4 states exercised.

2. **Model L produces severe but bounded degradation**: −68.5% AA, comparable to Model J at N=100.

3. **Attack frequency does not determine damage**: Model L's 125.6% attack rate produces less degradation than Model J's 1.0% attack rate at N=100.

4. **CTA phase boundaries are not a critical vulnerability**: The constitutional mechanism is robust to phase-transition attacks.

5. **Constitutional recovery remains intact**: No terminal failures despite extreme attack frequency and 79% ineligibility fraction.

6. **v3.0 conclusion**: Finite exercised internal state without learning is **insufficient** to defeat constitutional recovery under RSA assumptions.

---

## 11. v3.0 Summary

| Run | Model | Strategy | Attack Rate | AA Δ | Terminal Failures |
|-----|-------|----------|-------------|------|-------------------|
| 0 | (baseline) | None | 0% | — | 0 |
| 1a | J (N=50) | Periodic | 2.0% | −39.5% | 0 |
| 1b | J (N=100) | Periodic | 1.0% | −73.6% | 0 |
| 2 | K | Edge-reactive | 0.0017% | +50.2% | 0 |
| 3 | L | Phase-transition | 125.6% | −68.5% | 0 |

**No stateful FSM adversary in v3.0 induced terminal constitutional failure.**

---

## 12. Failure Class Note

HORIZON_EXHAUSTED should map to STABLE_AUTHORITY per the spec taxonomy — non-blocking, noted for future fix.

---

*Report generated by RSA v3.0 Run 3 canonical script*
*Script: `scripts/rsa_v300_run3_cta_phase_locker.py`*
