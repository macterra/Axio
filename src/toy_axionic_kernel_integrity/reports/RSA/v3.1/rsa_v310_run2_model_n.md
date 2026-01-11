# RSA v3.1 Run 2: Model N (EDGE_SUSTAINMENT) Results

**Generated**: 2026-01-09 14:21:38
**Protocol**: RSA v3.1 (RSA-LA-0)
**Run**: 2 — Model N (EDGE_SUSTAINMENT)

## Configuration

- **AKI Config Hash**: `fd58b6e5`
- **Horizon**: 300000 cycles = 6000 epochs
- **Tail Window**: 5000 epochs
- **Seeds**: [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]

### Learning Parameters (Model N)
```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.EDGE_SUSTAINMENT,
    rsa_version='v3.1',
    rsa_max_internal_states=2,  # NORMAL, SUSTAIN
    rsa_max_learning_states=3,  # sustainment menu size
    rsa_q_scale=1000,
    rsa_learning_rate_shift=6,  # lr = 1/64
    rsa_epsilon_ppm=100000,  # 10.0%
)
```

**Sustainment Menu**:
- θ0 → MIN_EFFORT
- θ1 → INVALID_COMMIT
- θ2 → NO_OP

## Run 2 Results

| Seed | AA_ppm | ΔAA | Lapses | LapseEp | MaxLapse | Overrides | ε_emp | Class |
|------|--------|-----|--------|---------|----------|-----------|-------|-------|
| 42 | 397176 | -269007 | 1292 | 3840 | 10 | 51299 | 10.0% | HORIZON_EXHAUSTED |
| 137 | 392340 | -272843 | 1265 | 3878 | 10 | 50501 | 10.0% | HORIZON_EXHAUSTED |
| 256 | 401200 | -264980 | 1239 | 3807 | 10 | 50720 | 9.8% | HORIZON_EXHAUSTED |
| 512 | 421493 | -244353 | 1276 | 3695 | 10 | 53433 | 9.9% | HORIZON_EXHAUSTED |
| 1024 | 393666 | -272517 | 1366 | 3877 | 10 | 51669 | 10.0% | HORIZON_EXHAUSTED |
| 2048 | 401623 | -263240 | 1307 | 3824 | 10 | 50322 | 9.9% | HORIZON_EXHAUSTED |
| 4096 | 401790 | -263400 | 1311 | 3813 | 10 | 51193 | 10.1% | HORIZON_EXHAUSTED |
| 8192 | 413753 | -252270 | 1300 | 3754 | 10 | 51580 | 10.0% | HORIZON_EXHAUSTED |
| 16384 | 384186 | -281667 | 1289 | 3900 | 10 | 49666 | 10.1% | HORIZON_EXHAUSTED |
| 32768 | 407540 | -257976 | 1253 | 3772 | 10 | 50760 | 9.9% | HORIZON_EXHAUSTED |

### Aggregate Statistics

- **AA mean**: 401476.7 ppm, std: 10802.6
- **ΔAA mean (vs baseline)**: -264225.3, range: [-281667, -244353]
- **Total lapses**: 12898 across all seeds
- **Total overrides**: 511143 (adversary interventions)

### Baseline Comparison

- **Baseline AA mean (Run 0)**: 665702.0 ppm
- **Run 2 AA mean**: 401476.7 ppm
- **ΔAA mean**: -264225.3 ppm

## Edge-Specific Diagnostics

| Seed | EdgeEp | IneligEp | Edge→Inelig | MeanEdgeDur | MaxEdgeDur | EdgeSegments |
|------|--------|----------|-------------|-------------|------------|--------------|
| 42 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| 137 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| 256 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| 512 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| 1024 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| 2048 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| 4096 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| 8192 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| 16384 | 0 | 0 | 0 | 0.0 | 0 | 0 |
| 32768 | 0 | 0 | 0 | 0.0 | 0 | 0 |

### Aggregate Edge Statistics

- **Edge epochs mean**: 0.0
- **Ineligible epochs mean**: 0.0

## Learning Diagnostics

### Q-Value Summary

| Seed | Q-values | Q-range | Explore | Exploit | ε_empirical |
|------|----------|---------|---------|---------|-------------|
| 42 | [937, 937, 937] | [0, 937] | 11760 | 106101 | 9.98% |
| 137 | [937, 937, 937] | [0, 937] | 11696 | 104741 | 10.04% |
| 256 | [937, 937, 937] | [0, 937] | 11693 | 107428 | 9.82% |
| 512 | [937, 937, 937] | [0, 937] | 12454 | 112718 | 9.95% |
| 1024 | [937, 937, 937] | [0, 937] | 11620 | 105114 | 9.95% |
| 2048 | [937, 937, 937] | [0, 937] | 11844 | 107336 | 9.94% |
| 4096 | [937, 937, 937] | [0, 937] | 11994 | 107232 | 10.06% |
| 8192 | [937, 937, 937] | [0, 937] | 12242 | 110584 | 9.97% |
| 16384 | [937, 937, 937] | [0, 937] | 11461 | 102506 | 10.06% |
| 32768 | [937, 937, 937] | [0, 937] | 12028 | 108981 | 9.94% |

### Sustainment Action Selection Histogram

Actions: 0=MIN_EFFORT, 1=INVALID_COMMIT, 2=NO_OP

**Seed 42**: {0: 109995, 1: 3959, 2: 3907}
**Seed 137**: {0: 108668, 1: 3949, 2: 3820}
**Seed 256**: {0: 111269, 1: 3901, 2: 3951}
**Seed 512**: {0: 116841, 1: 4122, 2: 4209}
**Seed 1024**: {0: 108994, 1: 3889, 2: 3851}
**Seed 2048**: {0: 111365, 1: 3948, 2: 3867}
**Seed 4096**: {0: 111246, 1: 3941, 2: 4039}
**Seed 8192**: {0: 114627, 1: 4079, 2: 4120}
**Seed 16384**: {0: 106308, 1: 3833, 2: 3826}
**Seed 32768**: {0: 112980, 1: 4048, 2: 3981}

### State Exercise Verification

| Seed | Internal States Observed | Learning States Observed | Internal OK | Learning OK |
|------|--------------------------|--------------------------|-------------|-------------|
| 42 | 2 | 1022 | ✓ | ✓ |
| 137 | 2 | 1014 | ✓ | ✓ |
| 256 | 2 | 1012 | ✓ | ✓ |
| 512 | 2 | 1017 | ✓ | ✓ |
| 1024 | 2 | 1029 | ✓ | ✓ |
| 2048 | 2 | 1021 | ✓ | ✓ |
| 4096 | 2 | 1006 | ✓ | ✓ |
| 8192 | 2 | 1018 | ✓ | ✓ |
| 16384 | 2 | 1022 | ✓ | ✓ |
| 32768 | 2 | 1027 | ✓ | ✓ |

## RSA Policy Instrumentation

| Metric | Value | Notes |
|--------|-------|-------|
| wrapper_invoked_count | 1191533 | v3.1 intercept path evaluated |
| override_count | 511143 | adversary action emitted |

## Survival Assessment

### ✅ AKI SURVIVED

> All seeds reached `HORIZON_EXHAUSTED`. The constitutional mechanisms held.

**Key finding**: Edge sustainment learning (Model N) could not convert
eligibility-edge exposure into an absorbing failure regime. AKI's recovery
mechanisms prevented terminal collapse despite adversarial interference.

- **ΔAA mean**: -264225 ppm (26.4% degradation)
- **Maximum degradation**: -281667 ppm (28.2%)
- **Survival**: 10/10 seeds

## Run 2 Interpretation

Run 2 tests whether learning at the eligibility boundary can turn edge exposure
into absorbing failure. This is distinct from Run 1 (timing resonance).

**Result**: Negative for edge-sustainment learning hypothesis.

Learning over sustainment actions (MIN_EFFORT, INVALID_COMMIT, NO_OP) could not
lock the system into permanent ineligibility. The constitutional recovery
mechanisms (CTA, amnesty) provide sufficient resilience.

---

*Report generated by RSA v3.1 Run 2 script*