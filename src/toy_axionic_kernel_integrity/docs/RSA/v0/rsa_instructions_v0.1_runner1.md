# RSA v0.1 Run 1 — Semantic Baseline Sweep (SV Axis)

## Purpose

Measure how AKI v0.8 governance robustness under RSA noise depends on the **baseline semantic pass regime**.

Interpretation: this is a phase-boundary probe for “CTA as escape hatch” as semantic evaluability becomes intrinsically harder, **holding noise intensity fixed**.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`)
* Eligibility rule and K=3 threshold
* CTA parameters (`amnesty_interval`, `amnesty_decay`), lapse semantics, scheduling
* Candidate pool composition and successor types
* RSA noise model type and flip probability
* RSA scope (PER_CI vs SEM_PASS_ONLY) — fixed for Run 1
* Horizon and renewal interval — fixed for Run 1
* Seed set — fixed for Run 1

### Single independent variable

* `SVConfig.per_ci_pass_rate_ppm` only

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config (unchanged from Run 0)

Use exactly:

```python
ALSConfigV080(
    max_cycles=10_000,
    eligibility_threshold_k=3,
    max_successive_renewals=3,
    amnesty_interval=10,
    amnesty_decay=1,
    cta_enabled=True,
)
```

Epoch definition remains:

* `renewal_check_interval = 50` (default)
* `global_epoch_max = max_cycles / renewal_check_interval = 200`

### 1.2 RSA config (fixed for Run 1)

Pick one fixed flip intensity based on Run 0 sensitivity. Use:

* `rsa_scope = PER_CI`
* `rsa_noise_model = FLIP_BERNOULLI`
* **Fixed** `rsa_p_flip_ppm = 100_000` (10%)

Rationale: 10% was the first clear non-trivial degradation point in Run 0 without approaching DoS.

```python
RSAConfig(
    rsa_enabled=True,
    rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
    rsa_scope=RSAScope.PER_CI,
    rsa_p_flip_ppm=100_000,
)
```

### 1.3 Seeds (fixed)

Use the same battery:

* `seeds = [40, 41, 42, 43, 44]`

---

## 2) Sweep Variable (SVConfig baseline)

### 2.1 Sweep values

Sweep `per_ci_pass_rate_ppm` across a regime that crosses the boundary from “near-always fail” to “mostly pass.”

Recommended values (PPM):

* `[500_000, 600_000, 700_000, 800_000, 850_000, 900_000, 950_000]`

Corresponding expected SEM_PASS:

* 0.5³ = 0.125
* 0.6³ = 0.216
* 0.7³ = 0.343
* 0.8³ = 0.512
* 0.85³ ≈ 0.614
* 0.9³ = 0.729
* 0.95³ ≈ 0.857

This gives you a clear phase map.

### 2.2 SV harness

Run with:

* `ALSHarnessV080_SV(seed, config, sv_config, rsa_config)`

SV remains deterministic-hash, global-epoch keyed.

---

## 3) Metrics (must report per seed and aggregate)

### 3.1 Governance outcomes

Per seed, per baseline point:

* `lapse_event_count`
* `lapse_epoch_count_total` (`total_lapse_duration_epochs`)
* `max_single_lapse_epochs`
* `authority_uptime_fraction`
* `recovery_count` (if separately tracked; else equals lapse_event_count if all recover)
* `stutter_count` (if tracked)
* `recovery_yield (RY)` if available

Aggregate (across seeds):

* mean and std for each metric above
* distribution of `max_single_lapse_epochs`

### 3.2 RSA integrity metrics

Per baseline point (aggregate across seeds):

* `sum_targets`, `sum_flips`, `observed_flip_rate_ppm`
* `sum_pivotal_flips` (SEM_PASS_raw != SEM_PASS_corrupted)
* pivotal rate = pivotal / flips

### 3.3 SV calibration metrics (required)

For each baseline point, report observed:

* `C0_true_rate`, `C1_true_rate`, `C2_true_rate`
* `SEM_PASS_true_rate`

Do this **at p_flip=0** (SV-only calibration) or reuse existing calibration method but clearly distinguish “raw SV” vs “post-RSA.”

Minimal: call `get_sv_calibration()` before corruption is applied (raw outcomes).

---

## 4) Regime Classification (frozen thresholds)

Use the same conservative thresholds from Run 0:

* **DOS_REGIME** if `max_single_lapse_epochs > 5 * amnesty_interval`

  * with interval 10 ⇒ threshold 50 lapse-epochs
* **DEGRADED** if `lapse_epoch_fraction > 0.50`
* **ROBUST** otherwise

Report classification per seed and as `N×ROBUST` etc.

---

## 5) Expected qualitative shape (pre-registered hypotheses)

### H1 (monotonicity)

As `per_ci_pass_rate_ppm` decreases, both:

* `lapse_event_count` and `lapse_epoch_count_total` increase.

### H2 (boundary)

There exists a baseline band where:

* the system flips from “mostly robust” to “frequent lapses,”
* but CTA still prevents persistent DoS until a lower baseline threshold.

### H3 (CTA clock imprint)

In the degraded region, lapse duration should cluster around CTA-relevant scales (multiples of `amnesty_interval`) because eligibility recovery is time-quantized.

These are hypotheses, not promises. Run 1 is to measure the boundary.

---

## 6) Script: `scripts/rsa_run1_sv_baseline_sweep_v010.py`

### Required output blocks

For each `per_ci_pass_rate_ppm`:

1. SV calibration block (raw rates)
2. Per-seed table
3. Aggregate summary + regime classification counts
4. RSA flip summary (targets/flips/pivotal)

### Skeleton pseudocode (structure, not implementation)

* loop over `rate_ppm in sweep_values`

  * set `sv_config = SVConfig(per_ci_pass_rate_ppm=rate_ppm)`
  * for each seed

    * run harness
    * collect metrics
  * compute aggregates
  * print block

---

## 7) Definition of Done (Run 1)

Run 1 is complete when:

* the sweep executes for all baseline points × seeds
* SV calibration is printed per baseline point
* per-seed and aggregate governance metrics are reported
* regime classification is reported per baseline point
* RSA flip + pivotal counts are reported (sanity check)

No refactors, no new noise models, no new success types.

---

