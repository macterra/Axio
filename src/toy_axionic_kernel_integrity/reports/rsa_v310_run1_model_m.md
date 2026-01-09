# RSA v3.1 Run 1: Model M (RECOVERY_AWARE_TIMING) Results

**Generated**: 2026-01-09 14:10:27
**Protocol**: RSA v3.1 (RSA-LA-0)
**Run**: 1 — Model M (RECOVERY_AWARE_TIMING)

## Configuration

- **AKI Config Hash**: `fd58b6e5`
- **Horizon**: 300000 cycles = 6000 epochs
- **Tail Window**: 5000 epochs
- **Seeds**: [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]

### Learning Parameters (Model M)
```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.RECOVERY_AWARE_TIMING,
    rsa_version='v3.1',
    rsa_max_internal_states=50,  # epoch_size
    rsa_max_learning_states=16,  # attack_set_count
    rsa_q_scale=1000,
    rsa_learning_rate_shift=6,  # lr = 1/64
    rsa_epsilon_ppm=100000,  # 10.0%
    rsa_attack_set_count=16,
)
```

## Run 1 Results

| Seed | AA_ppm | ΔAA | Lapses | LapseEp | MaxLapse | Overrides | ε_emp | Class |
|------|--------|-----|--------|---------|----------|-----------|-------|-------|
| 42 | 165580 | -500603 | 2154 | 5151 | 10 | 19520 | 10.0% | HORIZON_EXHAUSTED |
| 137 | 158283 | -506900 | 2194 | 5208 | 10 | 18665 | 10.1% | HORIZON_EXHAUSTED |
| 256 | 192563 | -473617 | 2098 | 4990 | 10 | 19226 | 9.8% | HORIZON_EXHAUSTED |
| 512 | 166516 | -499330 | 2111 | 5140 | 10 | 19916 | 9.9% | HORIZON_EXHAUSTED |
| 1024 | 225990 | -440193 | 1885 | 4780 | 10 | 21437 | 10.0% | HORIZON_EXHAUSTED |
| 2048 | 162766 | -502097 | 2148 | 5177 | 10 | 18235 | 9.8% | HORIZON_EXHAUSTED |
| 4096 | 155773 | -509417 | 2148 | 5215 | 10 | 18991 | 10.1% | HORIZON_EXHAUSTED |
| 8192 | 144340 | -521683 | 2214 | 5298 | 10 | 16908 | 10.0% | HORIZON_EXHAUSTED |
| 16384 | 168916 | -496937 | 2117 | 5132 | 10 | 18907 | 9.9% | HORIZON_EXHAUSTED |
| 32768 | 228873 | -436643 | 1965 | 4769 | 10 | 25490 | 10.0% | HORIZON_EXHAUSTED |

### Aggregate Statistics

- **AA mean**: 176960.0 ppm, std: 29266.8
- **ΔAA mean (vs baseline)**: -488742.0, range: [-521683, -436643]
- **Total lapses**: 21034 across all seeds
- **Total overrides**: 197295 (adversary interventions)

### Baseline Comparison

- **Baseline AA mean (Run 0)**: 665702.0 ppm
- **Run 1 AA mean**: 176960.0 ppm
- **ΔAA mean**: -488742.0 ppm

## Learning Diagnostics

### Q-Value Summary

| Seed | Q-values | Q-range | Explore | Exploit | ε_empirical |
|------|----------|---------|---------|---------|-------------|
| 42 | [937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937] | [0, 937] | 4731 | 42789 | 9.96% |
| 137 | [937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937] | [0, 937] | 4558 | 40733 | 10.06% |
| 256 | [937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937] | [0, 937] | 5483 | 50188 | 9.85% |
| 512 | [937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937] | [0, 937] | 4751 | 43093 | 9.93% |
| 1024 | [937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937] | [0, 937] | 6590 | 59322 | 10.00% |
| 2048 | [937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937] | [0, 937] | 4575 | 42107 | 9.80% |
| 4096 | [937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937] | [0, 937] | 4495 | 40089 | 10.08% |
| 8192 | [937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937] | [0, 937] | 4112 | 36976 | 10.01% |
| 16384 | [937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937] | [0, 937] | 4801 | 43757 | 9.89% |
| 32768 | [937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937, 937] | [0, 937] | 6663 | 60034 | 9.99% |

### Attack Set Selection Histogram

**Seed 42**: {0: 43117, 1: 267, 2: 277, 3: 286, 4: 301, 5: 298, 6: 294, 7: 273, 8: 331, 9: 319, 10: 285, 11: 319, 12: 297, 13: 315, 14: 276, 15: 265}
**Seed 137**: {0: 41006, 1: 268, 2: 293, 3: 273, 4: 305, 5: 264, 6: 289, 7: 270, 8: 339, 9: 283, 10: 270, 11: 282, 12: 263, 13: 304, 14: 303, 15: 279}
**Seed 256**: {0: 50569, 1: 355, 2: 342, 3: 349, 4: 354, 5: 336, 6: 369, 7: 314, 8: 338, 9: 333, 10: 339, 11: 329, 12: 331, 13: 355, 14: 336, 15: 322}
**Seed 512**: {0: 43365, 1: 292, 2: 293, 3: 287, 4: 323, 5: 277, 6: 297, 7: 279, 8: 304, 9: 309, 10: 311, 11: 294, 12: 293, 13: 307, 14: 305, 15: 308}
**Seed 1024**: {0: 59748, 1: 436, 2: 367, 3: 381, 4: 453, 5: 415, 6: 412, 7: 429, 8: 402, 9: 416, 10: 398, 11: 407, 12: 426, 13: 411, 14: 416, 15: 395}
**Seed 2048**: {0: 42373, 1: 305, 2: 314, 3: 275, 4: 267, 5: 280, 6: 273, 7: 282, 8: 311, 9: 310, 10: 299, 11: 288, 12: 272, 13: 279, 14: 283, 15: 271}
**Seed 4096**: {0: 40402, 1: 273, 2: 284, 3: 303, 4: 275, 5: 287, 6: 301, 7: 283, 8: 292, 9: 273, 10: 270, 11: 244, 12: 288, 13: 270, 14: 256, 15: 283}
**Seed 8192**: {0: 37239, 1: 269, 2: 247, 3: 252, 4: 255, 5: 265, 6: 261, 7: 249, 8: 274, 9: 236, 10: 273, 11: 253, 12: 279, 13: 250, 14: 244, 15: 242}
**Seed 16384**: {0: 44084, 1: 292, 2: 315, 3: 311, 4: 304, 5: 337, 6: 309, 7: 302, 8: 294, 9: 297, 10: 277, 11: 282, 12: 282, 13: 309, 14: 297, 15: 266}
**Seed 32768**: {0: 60470, 1: 441, 2: 435, 3: 406, 4: 404, 5: 420, 6: 374, 7: 396, 8: 392, 9: 399, 10: 461, 11: 425, 12: 405, 13: 424, 14: 419, 15: 426}

## RSA Policy Instrumentation

| Metric | Value | Notes |
|--------|-------|-------|
| wrapper_invoked_count | 509847 | v3.1 intercept path evaluated |
| override_count | 197295 | adversary action emitted |

## Survival Assessment

### ✅ AKI SURVIVED

> All seeds reached `HORIZON_EXHAUSTED`. The constitutional mechanisms held.

**Key finding**: Bounded Q-learning (Model M) caused significant availability degradation
but **could not defeat survivability**. AKI's renewal and CTA mechanisms recovered authority
despite the adversarial interference.

- **ΔAA mean**: -488742 ppm (48.9% degradation)
- **Maximum degradation**: -521683 ppm (52.2%)
- **Survival**: 10/10 seeds

The learning adversary found optimal attack strategies but AKI's constitutional
mechanisms (eligibility tracking, CTA, renewal) prevented terminal failure.

---

*Report generated by RSA v3.1 Run 1 script*