# RSA v3.1 Run 0: Baseline Reference Results

**Generated**: 2026-01-09 13:29:16
**Protocol**: RSA v3.1 (RSA-LA-0)
**Gate**: Run 0 — Baseline Equivalence

## Configuration

- **AKI Config Hash**: `fd58b6e5`
- **Horizon**: 300000 cycles = 6000 epochs
- **Tail Window**: 5000 epochs
- **Seeds**: [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]

### AKI Config (Frozen)
```python
ALSConfigV080(
    max_cycles=300000,
    renewal_check_interval=50,
    eligibility_threshold_k=3,
    amnesty_interval=10,
    amnesty_decay=1,
    cta_enabled=True,
)
```

## Condition A: RSA Disabled

| Seed | AA_ppm | AAA_ppm | Lapses | LapseEp | MaxLapse | RenewRate | Class |
|------|--------|---------|--------|---------|----------|-----------|-------|
| 42 | 666183 | 666183 | 5 | 2003 | 1010 | 990242 | HORIZON_EXHAUSTED |
| 137 | 665183 | 665183 | 5 | 2009 | 1010 | 990228 | HORIZON_EXHAUSTED |
| 256 | 666180 | 666180 | 4 | 2003 | 1010 | 990242 | HORIZON_EXHAUSTED |
| 512 | 665846 | 665846 | 4 | 2005 | 1010 | 990237 | HORIZON_EXHAUSTED |
| 1024 | 666183 | 666183 | 5 | 2003 | 1010 | 990242 | HORIZON_EXHAUSTED |
| 2048 | 664863 | 664863 | 9 | 2011 | 910 | 990223 | HORIZON_EXHAUSTED |
| 4096 | 665190 | 665190 | 7 | 2009 | 1010 | 990228 | HORIZON_EXHAUSTED |
| 8192 | 666023 | 666023 | 7 | 2004 | 1000 | 990240 | HORIZON_EXHAUSTED |
| 16384 | 665853 | 665853 | 6 | 2005 | 1010 | 990237 | HORIZON_EXHAUSTED |
| 32768 | 665516 | 665516 | 5 | 2007 | 1010 | 990232 | HORIZON_EXHAUSTED |

**AA mean**: 665702.0 ppm, std: 483.9

## Condition B: RSA Enabled, NONE

**RSAPolicyConfig (explicit None fields)**:
```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.NONE,
    rsa_version='v3.1',
    rsa_rng_stream='rsa_v310',
    rsa_max_internal_states=None,  # explicit
    rsa_max_learning_states=None,  # explicit
)
```

| Seed | AA_ppm | AAA_ppm | Lapses | LapseEp | MaxLapse | RenewRate | Class |
|------|--------|---------|--------|---------|----------|-----------|-------|
| 42 | 666183 | 666183 | 5 | 2003 | 1010 | 990242 | HORIZON_EXHAUSTED |
| 137 | 665183 | 665183 | 5 | 2009 | 1010 | 990228 | HORIZON_EXHAUSTED |
| 256 | 666180 | 666180 | 4 | 2003 | 1010 | 990242 | HORIZON_EXHAUSTED |
| 512 | 665846 | 665846 | 4 | 2005 | 1010 | 990237 | HORIZON_EXHAUSTED |
| 1024 | 666183 | 666183 | 5 | 2003 | 1010 | 990242 | HORIZON_EXHAUSTED |
| 2048 | 664863 | 664863 | 9 | 2011 | 910 | 990223 | HORIZON_EXHAUSTED |
| 4096 | 665190 | 665190 | 7 | 2009 | 1010 | 990228 | HORIZON_EXHAUSTED |
| 8192 | 666023 | 666023 | 7 | 2004 | 1000 | 990240 | HORIZON_EXHAUSTED |
| 16384 | 665853 | 665853 | 6 | 2005 | 1010 | 990237 | HORIZON_EXHAUSTED |
| 32768 | 665516 | 665516 | 5 | 2007 | 1010 | 990232 | HORIZON_EXHAUSTED |

**AA mean**: 665702.0 ppm, std: 483.9

## RSA Policy Integrity (Condition B)

| Metric | Value | Status |
|--------|-------|--------|
| rsa_enabled | True | ✓ |
| rsa_model | NONE | ✓ |
| rsa_max_internal_states | None | ✓ (not consulted) |
| rsa_max_learning_states | None | ✓ (not consulted) |
| wrapper_invoked_count | 1997050 | ✓ |
| override_count | 0 | ✓ |
| seeds_run | 10 | ✓ |

> ✓ **Enabled-path proof**: `wrapper_invoked_count > 0` confirms RSA intercept path was evaluated.
> No observable adapter exists for NONE model; wrapper invocation is the proof.

## Equivalence Check

### ✅ PASS

> Condition A (RSA disabled) and Condition B (RSA enabled, NONE) produced identical per-seed metrics.

The RSA v3.1 layer is behaviorally inert when set to NONE with explicit `None` capacity fields.

## Gate Status

```
RUN 0 RESULT: ✅ PASS
RSA v3.1 layer is behaviorally inert when set to NONE.
Proceed to Runs 1/2/3.
```
