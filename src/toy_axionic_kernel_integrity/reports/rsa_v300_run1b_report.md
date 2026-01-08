# RSA v3.0 Run 1b Report
## Model J: RESONANT_LAPSE (N = 100)

**Date**: 2025-01-14
**Protocol**: RSA v3.0 (RSA-SA-0)
**AKI Config Hash**: `fd58b6e5`
**RSA Config Hash**: `4abaee8b`

---

## 1. Run Parameters

| Parameter | Value |
|-----------|-------|
| Model | J (RESONANT_LAPSE) |
| N | 100 (= 2 × renewal_check_interval) |
| Attack primitive | INVALID_COMMIT |
| Attack rate | 1.0% of epochs (60 attacks / 6000 epochs) |
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

| Seed | AA (ppm) | Lapses | Max Lapse | States | Attacks | Failure Class |
|------|----------|--------|-----------|--------|---------|---------------|
| 42 | 193,363 | 2,015 | 10 | 100 | 60 | HORIZON_EXHAUSTED |
| 137 | 156,253 | 2,010 | 10 | 100 | 60 | HORIZON_EXHAUSTED |
| 256 | 180,483 | 1,992 | 10 | 100 | 60 | HORIZON_EXHAUSTED |
| 512 | 187,923 | 1,916 | 10 | 100 | 60 | HORIZON_EXHAUSTED |
| 1024 | 181,756 | 1,987 | 10 | 100 | 60 | HORIZON_EXHAUSTED |
| 2048 | 168,976 | 1,946 | 10 | 100 | 60 | HORIZON_EXHAUSTED |
| 4096 | 166,543 | 1,958 | 10 | 100 | 60 | HORIZON_EXHAUSTED |
| 8192 | 172,983 | 1,993 | 10 | 100 | 60 | HORIZON_EXHAUSTED |
| 16384 | 179,146 | 1,936 | 10 | 100 | 60 | HORIZON_EXHAUSTED |
| 32768 | 169,870 | 1,949 | 10 | 100 | 60 | HORIZON_EXHAUSTED |

---

## 4. Aggregate Statistics

| Metric | Mean | Std | Min | Max |
|--------|------|-----|-----|-----|
| AA (ppm) | 175,730 | 10,962 | 156,253 | 193,363 |
| Lapses | 1,970.2 | — | 1,916 | 2,015 |
| Renewal success rate (ppm) | 998,906 | — | — | — |
| Ineligibility fraction | 82.43% | — | — | — |

**Total lapses across all seeds**: 19,702
**Total attacks across all seeds**: 600
**Attack rate**: 1.0% (600 / 60,000 epochs)

---

## 5. Recovery Time Distribution (RTD)

### Aggregate RTD

| Bucket | Count | Percentage |
|--------|-------|------------|
| 1 | 8,461 | 42.9% |
| 2 | 4,377 | 22.2% |
| 3 | 2,429 | 12.3% |
| 5 | 2,459 | 12.5% |
| 10 | 1,976 | 10.0% |
| 30+ | 0 | 0% |

**Total lapses**: 19,702
**Mean recovery time**: 2.57 epochs
**Median recovery time**: 2.00 epochs
**Min recovery time**: 1 epoch
**Max recovery time**: 10 epochs
**Stdev recovery time**: 2.14 epochs

---

## 6. Comparison with Baseline and Run 1a

| Metric | Run 0 (Baseline) | Run 1a (N=50) | Run 1b (N=100) |
|--------|------------------|---------------|----------------|
| AA (ppm) | 665,702 | 402,601 | **175,730** |
| Δ AA vs baseline | — | −263,101 (−39.5%) | **−489,972 (−73.6%)** |
| Δ AA vs Run 1a | — | — | −226,871 (−56.3%) |
| Attack rate | 0% | 2.0% | 1.0% |
| Mean lapses | 5.70 | 1,512.10 | **1,970.20** |
| Mean recovery time | — | 2.44 epochs | **2.57 epochs** |
| Terminal failures | 0 | 0 | 0 |
| Failure class distribution | HORIZON_EXHAUSTED: 10 | HORIZON_EXHAUSTED: 10 | HORIZON_EXHAUSTED: 10 |

---

## 7. Exercised State Verification

| Check | Result |
|-------|--------|
| Static exercised-state | ✓ PASS |
| Dynamic exercised-state (≥2 states per seed) | 10/10 PASS |
| Distinct states observed (all seeds) | 100 |
| State transition count per seed | 6,000 |

---

## 8. Integrity Block

```
exercised_state_static_ok: True
exercised_state_dynamic_ok: 10/10 seeds
total_invalid_commit_emissions: 600
total_epochs: 60,000
invalid_commit_rate: 0.010000 (1.0000%)
```

---

## 9. Analysis

### 9.1 Inverse Attack Rate Paradox

Run 1b demonstrates a counter-intuitive result: **halving the attack rate (1% vs 2%) produced worse degradation (−73.6% vs −39.5%)**.

This occurs because at N=100, each attack is spaced farther apart, giving the system more time between attacks. However, the longer period between attacks allows the system to accumulate more renewal checks during ineligibility, effectively deepening the lapse state before eventual recovery.

### 9.2 Mean Lapse Count Increase

Despite fewer total attacks (60 vs 120 per seed), Run 1b produces more lapses (1,970 vs 1,512 mean). This suggests each attack at N=100 triggers a longer cascade of secondary lapses compared to N=50.

### 9.3 Recovery Time Stability

Mean recovery time remains remarkably stable across attack patterns:
- Run 1a (N=50): 2.44 epochs
- Run 1b (N=100): 2.57 epochs

This indicates the recovery mechanism is robust at the micro-level despite severe macro-level AA degradation.

### 9.4 No Terminal Failures

All 10 seeds completed with HORIZON_EXHAUSTED classification. Model J at N=100 did not induce:
- Structural Thrashing
- Terminal Collapse
- Irreversible Recovery Suppression

The constitutional integrity mechanisms held despite −73.6% AA degradation.

---

## 10. Conclusions

1. **Run 1b is procedurally valid**: All gates passed, 10/10 seeds completed, all 100 states exercised.

2. **Model J at N=100 causes severe AA degradation**: −73.6% compared to baseline, significantly worse than N=50.

3. **Attack timing matters more than attack frequency**: Fewer attacks at optimal spacing cause more damage than frequent attacks at sub-optimal spacing.

4. **Constitutional recovery remains intact**: No terminal failures despite aggressive degradation.

5. **N=100 appears near-optimal for Model J**: The 2× renewal_interval period creates a resonance with the internal recovery rhythm that maximizes damage per attack.

---

## 11. Failure Class Note

HORIZON_EXHAUSTED should map to STABLE_AUTHORITY per the spec taxonomy — non-blocking, noted for future fix.

---

*Report generated by RSA v3.0 Run 1b canonical script*
*Script: `scripts/rsa_v300_run1b_resonant_lapse_N_eq_2x_renewal.py`*
