# RSA v0.2 Run 1 — Aggregation-Point Corruption Sweep (SEM_PASS Axis)

## Purpose

Measure how AKI v0.8 governance robustness responds when **only the aggregation wire** `SEM_PASS` is corrupted **post-verification** under a **non-adaptive, semantic-free** interference process.

Interpretation: this is the cleanest probe of whether **eligibility aggregation** is a constitutional choke point under RSA assumptions.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`)
* Eligibility rule and `eligibility_threshold_k` (freeze to baseline used for v0.2)
* CTA parameters (`amnesty_interval=10`, `amnesty_decay=1`), lapse semantics, scheduling
* Candidate pool composition and successor types
* RSA model family (must be Run 1 model below)
* RSA scope (must be `SEM_PASS_ONLY` for Run 1)
* Horizon, renewal interval, and epoch definition (use the same baseline as v0.2)
* Seed set (fixed)
* Failure thresholds doc (`docs/rsa_v020_failure_thresholds.md`) (frozen)

### Single independent variable

* `rsa_p_flip_ppm` only

No other parameter may vary.

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config (baseline for v0.2)

Use the same baseline AKI config you have frozen for v0.2 runs. Minimum required invariants:

```python
ALSConfigV080(
    max_cycles=300_000,             # frozen v0.2 horizon (yields 6000 epochs); do not vary
    eligibility_threshold_k=3,       # freeze to v0.2 baseline
    max_successive_renewals=3,       # freeze
    amnesty_interval=10,             # frozen for v0.2
    amnesty_decay=1,                # freeze
    cta_enabled=True,               # freeze
)
```

**Epoch definition** is whatever AKI uses for “end-of-epoch verification.” Do not infer. Use the harness epoch counter and log:

* `horizon_epochs`
* `tail_window = max(5000, horizon_epochs // 5)`

### 1.2 RSA config (fixed for Run 1)

Run 1 uses **only**:

* `rsa_noise_model = AGG_FLIP_BERNOULLI`
* `rsa_scope = SEM_PASS_ONLY`

```python
RSAConfig(
    rsa_enabled=True,
    rsa_noise_model=RSANoiseModel.AGG_FLIP_BERNOULLI,
    rsa_scope=RSAScope.SEM_PASS_ONLY,
    rsa_rng_stream="rsa_v020",
    rsa_p_flip_ppm=...,   # sweep variable
)
```

Hard constraints:

* No RSA modifications mid-run.
* No PER_KEY in Run 1.
* No burst schedule parameters set/used.

### 1.3 Seeds (fixed)

Use:

* `seeds = [40, 41, 42, 43, 44]`

---

## 2) Sweep Variable

### 2.1 Sweep values (PPM)

Sweep `rsa_p_flip_ppm` across the preregistered values:

* `{0, 200, 500, 1_000, 2_000, 5_000, 10_000, 20_000}`

These correspond to 0% … 2%.

No extra points. No adaptive refinement. If you later need more resolution, that is a **new preregistered addendum**, not a silent extension.

### 2.2 Model semantics (must match spec)

In Run 1:

* `Ci_OK_raw` values are computed normally by AKI.
* `SEM_PASS_raw` is computed normally by AKI.
* RSA may flip only `SEM_PASS_raw` to produce `SEM_PASS`.

No corruption of `Ci_OK_raw` is permitted.

---

## 3) Metrics (must report per seed and aggregate)

Run 1 is governed by the v0.2 metrics contract. Report all of the following.

### 3.1 Governance outcomes (per seed, per p)

* `authority_availability_ppm` (AA)
* `asymptotic_authority_availability_ppm` (AAA)
* `failure_class` (from `metrics.py` using frozen thresholds)
* `recovery_time_histogram` (RTD)
* `lapse_count`
* `total_lapse_epochs`
* `max_single_lapse_epochs`

Aggregate across seeds:

* mean and std (or min/max) for AA and AAA
* counts by `failure_class`
* distribution summary of `max_single_lapse_epochs`

### 3.2 RSA integrity metrics (required)

Per `p_flip_ppm` (aggregate across seeds):

* `total_targets`
* `total_flips`
* `observed_flip_rate_ppm`
* `expected_flip_rate_ppm` (= `rsa_p_flip_ppm` for Run 1)
* `epochs_evaluated`
* `epochs_in_lapse`

### 3.3 Pivotal flip telemetry (required)

A flip is **pivotal** iff `SEM_PASS_raw != SEM_PASS_corrupted`.

Report per `p_flip_ppm`:

* `pivotal_flips`
* `pivotal_rate_ppm = pivotal_flips * 1_000_000 // total_flips` (define 0 if `total_flips=0`)

Rationale: non-pivotal flips are noise that does not affect the system. If pivotal rate collapses or spikes, it changes how to interpret the sweep.

---

## 4) Failure Classification (Frozen; no reinterpretation)

Use the exact classifier implemented in `toy_aki/rsa/metrics.py` and the preregistered constants documented in:

* `docs/rsa_v020_failure_thresholds.md`

Do not add ad hoc labels (“robust/degraded/DoS regime”). In v0.2, the only valid labels are:

* `STABLE_AUTHORITY`
* `BOUNDED_DEGRADATION`
* `STRUCTURAL_THRASHING`
* `ASYMPTOTIC_DOS`
* `TERMINAL_COLLAPSE`

---

## 5) Expected qualitative shape (pre-registered hypotheses)

These are hypotheses, not promises.

### H1 (monotonic degradation in AA/AAA)

As `rsa_p_flip_ppm` increases, expect:

* AA and AAA to decrease (weakly monotonic in expectation).

### H2 (threshold behavior)

There exists a band of `p_flip_ppm` where:

* failure class transitions occur sharply (e.g., Stable → Bounded Degradation), rather than smoothly.

### H3 (CTA imprint)

As noise rises, RTD should show increased mass in longer buckets, with heavy lapses emerging near the heavy-lapse cutoff defined relative to amnesty interval.

---

## 6) Script: `scripts/rsa_v020_run1_aggregation_corruption.py`

### Required output blocks

For each `rsa_p_flip_ppm`:

1. **Run header**: AKI config hash, RSA config hash, horizon (cycles), derived `horizon_epochs`, derived `tail_window`
2. **Per-seed table**: AA_ppm, AAA_ppm, failure_class, lapse_count, total_lapse_epochs, max_single_lapse_epochs, observed_flip_rate_ppm, pivotal_rate_ppm
3. **Aggregate summary**: mean/std AA and AAA, class counts, RTD aggregate summary
4. **RSA integrity block**: targets/flips/observed vs expected + pivotal flips

### Skeleton pseudocode (structure, not implementation)

* loop over `p in sweep_values`

  * set RSAConfig with `rsa_p_flip_ppm=p`
  * for each seed in seeds

    * run `ALSHarnessV080(seed, als_config, rsa_config)`
    * collect metrics + RSA summary
  * aggregate and print required blocks

---

## 7) Definition of Done (Run 1)

Run 1 is complete when:

* sweep executes for all `p_flip_ppm` × seeds
* per-seed metrics are printed for each `p_flip_ppm`
* aggregate summaries are printed for each `p_flip_ppm`
* RSA integrity metrics (observed vs expected, pivotal rates) are printed
* failure class is emitted exactly once per run using frozen classifier

No refactors, no parameter tuning, no additional sweep points, no new models.

---
