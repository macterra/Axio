# RSA v0.2 Failure Classification Thresholds

**Version:** 0.2.0
**Date:** 2026-01-06
**Status:** FROZEN

---

## Purpose

This document preregisters the exact numeric thresholds used by the failure classifier in `metrics.py`. These values are frozen for the duration of RSA v0.2 and MUST NOT be modified during or after experimental runs.

The spec (§12) defined failure classes qualitatively. This document operationalizes those definitions with fixed numeric constants.

---

## Frozen Constants

### Authority Availability Thresholds (PPM)

| Constant | Value (PPM) | Value (%) | Description |
|----------|-------------|-----------|-------------|
| `AAA_STABLE_THRESHOLD` | 900,000 | 90% | AAA ≥ this → Stable Authority candidate |
| `AAA_THRASHING_THRESHOLD` | 200,000 | 20% | AAA < this + heavy tail → Structural Thrashing |
| `AAA_DOS_THRESHOLD` | 100,000 | 10% | AAA < this → Asymptotic DoS |

### RTD Heavy Tail Definition

| Constant | Value | Description |
|----------|-------|-------------|
| `HEAVY_LAPSE_DURATION_EPOCHS` | 100 | Lapse duration > this is "heavy" |
| `HEAVY_TAIL_COUNT_THRESHOLD` | 1 | heavy_lapses ≥ this triggers heavy-tail flag |

---

## Classification Decision Tree (Frozen)

```
classify_failure(aaa_ppm, lapse_intervals, authority_by_epoch, tail_window):

    1. TERMINAL COLLAPSE check (strictest):
       - ∃ t* ≤ (horizon - tail_window) such that AUTH(epoch) = 0 ∀ epoch ∈ [t*, horizon)
       - i.e., permanent unrecovered lapse starting before tail window
       → Return TERMINAL_COLLAPSE

    2. ASYMPTOTIC DoS check:
       - aaa_ppm < AAA_DOS_THRESHOLD (100,000)
       - AND total_lapses > 0
       → Return ASYMPTOTIC_DOS

    3. STRUCTURAL THRASHING check:
       - aaa_ppm < AAA_THRASHING_THRESHOLD (200,000)
       - AND heavy_lapses > 0 (any lapse with duration > HEAVY_LAPSE_DURATION_EPOCHS)
       → Return STRUCTURAL_THRASHING

    4. BOUNDED DEGRADATION check:
       - aaa_ppm < AAA_STABLE_THRESHOLD (900,000)
       - AND total_lapses > 0
       → Return BOUNDED_DEGRADATION

    5. Default:
       → Return STABLE_AUTHORITY
```

---

## Rationale for Threshold Selection

### AAA_STABLE_THRESHOLD = 90%
- Governance operating at 90%+ availability is "normal" for this toy model
- Baseline runs without RSA typically show ~66% uptime due to natural succession events
- 90% accounts for transient startup/succession effects

### AAA_THRASHING_THRESHOLD = 20%
- Below 20% means authority is absent 80%+ of tail window
- Combined with heavy-tailed RTD, indicates unstable oscillation

### AAA_DOS_THRESHOLD = 10%
- Below 10% means nearly complete governance failure
- If recoveries exist but AAA is this low, recoveries are negligible

### HEAVY_LAPSE_DURATION_EPOCHS = 100

**Derivation:** 10 × `amnesty_interval` (which is 10 epochs in standard v0.2 AKI config)

A lapse lasting 100+ epochs has survived 10 amnesty cycles without recovery. This indicates structural rather than transient failure.

**Validity constraint:** This threshold is ONLY valid for runs where `amnesty_interval=10`. If amnesty_interval changes, this constant becomes incoherent.

For RSA v0.2, `amnesty_interval=10` is frozen as part of the AKI v0.8 baseline configuration. All experimental runs MUST use this value.

---

## Implementation Binding

The constants MUST be defined in `metrics.py` as module-level constants:

```python
# Frozen classification thresholds (per rsa_v020_failure_thresholds.md)
AAA_STABLE_THRESHOLD_PPM = 900_000
AAA_THRASHING_THRESHOLD_PPM = 200_000
AAA_DOS_THRESHOLD_PPM = 100_000
HEAVY_LAPSE_DURATION_EPOCHS = 100
```

The `classify_failure()` function MUST use these exact constants, not inline literals.

---

## Binding Commitment

These thresholds are now frozen. Any modification requires:

1. A new version tag (v0.2.1+)
2. Documentation of rationale
3. Re-running all affected experimental runs

For RSA v0.2 experimental runs, these values are IMMUTABLE.
