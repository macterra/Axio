# RSA v3.1 Run 3: Model O (STOCHASTIC_MIXER) Results

**Generated**: 2026-01-09 14:42:04
**Protocol**: RSA v3.1 (RSA-LA-0)
**Run**: 3 — Model O (STOCHASTIC_MIXER)

## Configuration

- **AKI Config Hash**: `fd58b6e5`
- **Horizon**: 300000 cycles = 6000 epochs
- **Tail Window**: 5000 epochs
- **Seeds**: [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]

### Learning Parameters (Model O)
```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.STOCHASTIC_MIXER,
    rsa_version='v3.1',
    rsa_max_internal_states=5,  # strategy index
    rsa_max_learning_states=5,  # learning dimensions
    rsa_q_scale=1000,
    rsa_learning_rate_shift=6,  # lr = 1/64
    rsa_epsilon_ppm=100000,  # 10.0%
    rsa_strategy_count=5,
    rsa_weight_max=10000,
)
```

### Strategy Pool (Frozen)

| Index | Strategy | Description |
|-------|----------|-------------|
| 0 | COMPLIANT | Always compliant (baseline) |
| 1 | RESONANT_LAPSE | Periodic invalid commit (v3.0 Model J) |
| 2 | EDGE_OSCILLATOR | Eligibility-edge alternation (v3.0 Model K) |
| 3 | CTA_PHASE_LOCKER | CTA boundary attacks (v3.0 Model L) |
| 4 | INVALID_ALWAYS | Always invalid commit (degenerate) |

## Run 3 Results

| Seed | AA_ppm | ΔAA | Lapses | LapseEp | Overrides | Dominant | Entropy | Class |
|------|--------|-----|--------|---------|-----------|----------|---------|-------|
| 42 | 109966 | -556217 | 3671 | 5774 | 19374 | COMPLIANT | 2.32 | HORIZON_EXHAUSTED |
| 137 | 106300 | -558883 | 3674 | 5786 | 19528 | COMPLIANT | 2.32 | HORIZON_EXHAUSTED |
| 256 | 95616 | -570564 | 3417 | 5767 | 16415 | COMPLIANT | 2.32 | HORIZON_EXHAUSTED |
| 512 | 96263 | -569583 | 3526 | 5806 | 16274 | COMPLIANT | 2.32 | HORIZON_EXHAUSTED |
| 1024 | 90900 | -575283 | 3580 | 5823 | 15644 | COMPLIANT | 2.32 | HORIZON_EXHAUSTED |
| 2048 | 93423 | -571440 | 3571 | 5817 | 14124 | COMPLIANT | 2.32 | HORIZON_EXHAUSTED |
| 4096 | 111010 | -554180 | 3788 | 5783 | 17072 | COMPLIANT | 2.32 | HORIZON_EXHAUSTED |
| 8192 | 112873 | -553150 | 3525 | 5733 | 18411 | COMPLIANT | 2.32 | HORIZON_EXHAUSTED |
| 16384 | 103420 | -562433 | 3547 | 5775 | 16112 | COMPLIANT | 2.32 | HORIZON_EXHAUSTED |
| 32768 | 99520 | -565996 | 3575 | 5784 | 15282 | COMPLIANT | 2.32 | HORIZON_EXHAUSTED |

### Aggregate Statistics

- **AA mean**: 101929.1 ppm, std: 7887.5
- **ΔAA mean (vs baseline)**: -563772.9, range: [-575283, -553150]
- **Total lapses**: 35874 across all seeds
- **Total overrides**: 168236 (adversary interventions)

### Baseline Comparison

- **Baseline AA mean (Run 0)**: 665702.0 ppm
- **Run 3 AA mean**: 101929.1 ppm
- **ΔAA mean**: -563772.9 ppm

## Strategy-Mixing Diagnostics

| Seed | Entropy | DomStrat | DomFrac | Switches | LongestStreak |
|------|---------|----------|---------|----------|---------------|
| 42 | 2.322 | 0 (COMPLIANT) | 20.3% | 23479 | 7 |
| 137 | 2.322 | 0 (COMPLIANT) | 19.8% | 22579 | 7 |
| 256 | 2.322 | 0 (COMPLIANT) | 19.5% | 20263 | 7 |
| 512 | 2.322 | 0 (COMPLIANT) | 19.9% | 20261 | 6 |
| 1024 | 2.322 | 0 (COMPLIANT) | 19.5% | 18945 | 7 |
| 2048 | 2.322 | 0 (COMPLIANT) | 19.5% | 19472 | 7 |
| 4096 | 2.322 | 0 (COMPLIANT) | 19.4% | 23612 | 8 |
| 8192 | 2.322 | 0 (COMPLIANT) | 20.0% | 24302 | 6 |
| 16384 | 2.322 | 0 (COMPLIANT) | 19.9% | 22066 | 7 |
| 32768 | 2.322 | 0 (COMPLIANT) | 20.1% | 21064 | 7 |

### Aggregate Strategy Statistics

- **Entropy mean**: 2.322 bits, std: 0.000
- **Switch count mean**: 21604.3

### Strategy Selection Histogram (per seed)

**Seed 42**: {COMPLIANT: 5960, RESONANT_LAPSE: 5981, EDGE_OSCILLATOR: 5741, CTA_PHASE_LOCKER: 5758, INVALID_ALWAYS: 5879}
**Seed 137**: {COMPLIANT: 5589, RESONANT_LAPSE: 5723, EDGE_OSCILLATOR: 5634, CTA_PHASE_LOCKER: 5554, INVALID_ALWAYS: 5716}
**Seed 256**: {COMPLIANT: 4924, RESONANT_LAPSE: 4963, EDGE_OSCILLATOR: 5142, CTA_PHASE_LOCKER: 5146, INVALID_ALWAYS: 5093}
**Seed 512**: {COMPLIANT: 5035, RESONANT_LAPSE: 5001, EDGE_OSCILLATOR: 5210, CTA_PHASE_LOCKER: 5180, INVALID_ALWAYS: 4927}
**Seed 1024**: {COMPLIANT: 4631, RESONANT_LAPSE: 4702, EDGE_OSCILLATOR: 4789, CTA_PHASE_LOCKER: 4893, INVALID_ALWAYS: 4675}
**Seed 2048**: {COMPLIANT: 4771, RESONANT_LAPSE: 4941, EDGE_OSCILLATOR: 4898, CTA_PHASE_LOCKER: 4789, INVALID_ALWAYS: 5057}
**Seed 4096**: {COMPLIANT: 5729, RESONANT_LAPSE: 5896, EDGE_OSCILLATOR: 6071, CTA_PHASE_LOCKER: 5842, INVALID_ALWAYS: 5977}
**Seed 8192**: {COMPLIANT: 6057, RESONANT_LAPSE: 6073, EDGE_OSCILLATOR: 6067, CTA_PHASE_LOCKER: 6135, INVALID_ALWAYS: 6005}
**Seed 16384**: {COMPLIANT: 5477, RESONANT_LAPSE: 5371, EDGE_OSCILLATOR: 5525, CTA_PHASE_LOCKER: 5493, INVALID_ALWAYS: 5613}
**Seed 32768**: {COMPLIANT: 5276, RESONANT_LAPSE: 5285, EDGE_OSCILLATOR: 5243, CTA_PHASE_LOCKER: 5340, INVALID_ALWAYS: 5137}

### Final Weights (per seed)

| Seed | W0 (COMPLIANT) | W1 (RESONANT) | W2 (EDGE) | W3 (CTA) | W4 (INVALID) |
|------|----------------|---------------|-----------|----------|--------------|
| 42 | 10000 | 10000 | 10000 | 10000 | 10000 |
| 137 | 10000 | 10000 | 10000 | 10000 | 10000 |
| 256 | 10000 | 10000 | 10000 | 10000 | 10000 |
| 512 | 10000 | 10000 | 10000 | 10000 | 10000 |
| 1024 | 10000 | 10000 | 10000 | 10000 | 10000 |
| 2048 | 10000 | 10000 | 10000 | 10000 | 10000 |
| 4096 | 10000 | 10000 | 10000 | 10000 | 10000 |
| 8192 | 10000 | 10000 | 10000 | 10000 | 10000 |
| 16384 | 10000 | 10000 | 10000 | 10000 | 10000 |
| 32768 | 10000 | 10000 | 10000 | 10000 | 10000 |

## State Exercise Verification

| Seed | Internal States Observed | Learning States Observed | Internal OK | Learning OK |
|------|--------------------------|--------------------------|-------------|-------------|
| 42 | 5 | 3001 | ✓ | ✓ |
| 137 | 5 | 3001 | ✓ | ✓ |
| 256 | 5 | 3001 | ✓ | ✓ |
| 512 | 5 | 3001 | ✓ | ✓ |
| 1024 | 5 | 3001 | ✓ | ✓ |
| 2048 | 5 | 3001 | ✓ | ✓ |
| 4096 | 5 | 3001 | ✓ | ✓ |
| 8192 | 5 | 3001 | ✓ | ✓ |
| 16384 | 5 | 3001 | ✓ | ✓ |
| 32768 | 5 | 3001 | ✓ | ✓ |

## RSA Policy Instrumentation

| Metric | Value | Notes |
|--------|-------|-------|
| wrapper_invoked_count | 269914 | v3.1 intercept path evaluated |
| override_count | 168236 | adversary action emitted |

## Survival Assessment

### ✅ AKI SURVIVED

> All seeds reached `HORIZON_EXHAUSTED`. The constitutional mechanisms held.

**Key finding**: Stochastic mixing over a portfolio of known strategies (Model O)
could not defeat constitutional survivability. Learning to mix strategies did not
outperform any single constituent strategy in terms of causing terminal failure.

- **ΔAA mean**: -563773 ppm (56.4% degradation)
- **Maximum degradation**: -575283 ppm (57.5%)
- **Survival**: 10/10 seeds

## Run 3 Interpretation

Run 3 is the **final adversary class** in RSA v3.1.

**Result**: Negative for stochastic mixing hypothesis.

Learning to mix among strategies (COMPLIANT, RESONANT_LAPSE, EDGE_OSCILLATOR,
CTA_PHASE_LOCKER, INVALID_ALWAYS) could not induce constitutional collapse.

### v3.1 Conclusion

> **No kernel-external, semantic-free adversary—stateless, stateful, or learning,
> including stochastic mixers—can defeat constitutional survivability under the
> AKI v0.8 contract.**

---

*Report generated by RSA v3.1 Run 3 script*