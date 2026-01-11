# RSA v0.2 Run 2 — Commitment-Correlated Noise Sweep (Single-Key Axis)

## Purpose

Measure whether **persistent impairment of a single obligation wire** (one `Ci_OK`) can defeat constitutional recovery, or whether it produces only **bounded degradation** under RSA v0.2 constraints.

Run 2 isolates a different structural question than Run 1:

*Run 1 corrupts the aggregate wire.*
*Run 2 corrupts one input wire and forces aggregation to propagate that impairment through AKI’s canonical `SEM_PASS` function.*

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`)
* Evaluation timing (end-of-epoch verification only)
* CTA parameters (`amnesty_interval=10`, `amnesty_decay=1`) and lapse semantics
* Candidate pool composition and successor types
* Horizon, renewal interval, and epoch definition (use frozen v0.2 baseline)
* Seed set (fixed)
* Failure thresholds doc (`docs/rsa_v020_failure_thresholds.md`) (frozen)
* Aggregator identity: **AKI must compute `SEM_PASS` via its own `_aggregate_sem_pass()` from post-interference keys** (no raw SEM_PASS usage downstream)

### Single independent variable

* `rsa_p_target_flip_ppm` only

**Run 2 target key is frozen** to a single key (`C1`) for the main sweep. Do not vary the target key inside Run 2.

(If you later run `C0`/`C2`, that is a separate preregistered extension, not part of Run 2 proper.)

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config (baseline for v0.2)

Use the same frozen AKI config as Run 1 (and all v0.2 runs). Minimum required invariants:

```python
ALSConfigV080(
    max_cycles=300_000,             # frozen for v0.2 (yields 6000 epochs)
    eligibility_threshold_k=3,       # frozen baseline
    max_successive_renewals=3,       # frozen baseline
    amnesty_interval=10,             # frozen baseline
    amnesty_decay=1,                # frozen baseline
    cta_enabled=True,               # frozen baseline
)
```

Log and persist per sweep job:

* `horizon_epochs` (from harness)
* `tail_window = max(5000, horizon_epochs // 5)` (frozen rule)

### 1.2 RSA config (fixed for Run 2)

Run 2 uses only:

* `rsa_noise_model = COMMITMENT_KEYED_FLIP`
* `rsa_scope = PER_KEY`
* `rsa_target_key = "C1"` (frozen)

```python
RSAConfig(
    rsa_enabled=True,
    rsa_noise_model=RSANoiseModel.COMMITMENT_KEYED_FLIP,
    rsa_scope=RSAScope.PER_KEY,
    rsa_rng_stream="rsa_v020",
    rsa_target_key="C1",             # frozen for Run 2
    rsa_p_target_flip_ppm=...,       # sweep variable
)
```

Hard constraints:

* No corruption of other keys (C0/C2 must remain pass-through).
* No corruption of `SEM_PASS` directly in Run 2.
* No burst schedule parameters set/used.

### 1.3 Seeds (fixed)

Use:

* `seeds = [40, 41, 42, 43, 44]`

---

## 2) Sweep Variable

### 2.1 Sweep values (PPM)

Sweep `rsa_p_target_flip_ppm` across preregistered values:

* `{0, 500, 1_000, 5_000, 10_000, 20_000, 50_000, 100_000}`

These correspond to 0% … 10% on a single key.

No extra points. No mid-run adjustments.

### 2.2 Model semantics (must match spec)

In Run 2:

1. AKI computes raw keys: `C0_OK_raw`, `C1_OK_raw`, `C2_OK_raw`
2. RSA may flip **only** the target key (`C1_OK_raw → C1_OK`)
3. AKI recomputes `SEM_PASS` via its canonical aggregator from post-interference keys:

```
SEM_PASS = AGGREGATE(C0_OK, C1_OK, C2_OK)    # AKI-owned function
```

RSA must not use `SEM_PASS_raw` downstream.

---

## 3) Metrics (must report per seed and aggregate)

Run 2 uses the same v0.2 metrics contract as Run 1.

### 3.1 Governance outcomes (per seed, per p)

* `authority_availability_ppm` (AA)
* `asymptotic_authority_availability_ppm` (AAA)
* `failure_class`
* `recovery_time_histogram` (RTD)
* `lapse_count`
* `total_lapse_epochs`
* `max_single_lapse_epochs`

Aggregate across seeds:

* mean and std (or min/max) for AA and AAA
* counts by `failure_class`
* RTD aggregate summary
* distribution summary of `max_single_lapse_epochs`

### 3.2 RSA integrity metrics (required)

Per `p_target_flip_ppm` (aggregate across seeds):

* `total_targets`
* `total_flips`
* `observed_flip_rate_ppm`
* `expected_flip_rate_ppm` (= `rsa_p_target_flip_ppm` **on target epochs/targets**)
* `flips_by_key` (must show flips only under `"C1"`; others must be zero)
* `epochs_evaluated`
* `epochs_in_lapse`

**Note on “targets”:** In Run 2, `targets_epoch` should be:

* `1` on evaluation epochs (only C1 eligible), and
* `0` during lapse / non-evaluation epochs.

### 3.3 Pivotal flip telemetry (required)

Define pivotal flip for Run 2:

A flip is pivotal iff it changes the downstream aggregate:

```
SEM_PASS_raw != SEM_PASS_corrupted
```

Report per `p_target_flip_ppm`:

* `pivotal_flips`
* `pivotal_rate_ppm`

Also report the raw-vs-corrupted key mismatch rate:

* `key_pivotal_flips = count(C1_OK_raw != C1_OK)`
* `key_pivotal_rate_ppm = key_pivotal_flips * 1_000_000 // total_flips` (should be 1_000_000 unless you allow non-flip events to be counted differently)

This prevents confusion between “flip fired” and “flip mattered.”

---

## 4) Failure Classification (Frozen; no reinterpretation)

Use the exact classifier implemented in `toy_aki/rsa/metrics.py` with frozen constants in:

* `docs/rsa_v020_failure_thresholds.md`

Emit exactly one label per (seed, p) run:

* `STABLE_AUTHORITY`
* `BOUNDED_DEGRADATION`
* `STRUCTURAL_THRASHING`
* `ASYMPTOTIC_DOS`
* `TERMINAL_COLLAPSE`

No extra labels.

---

## 5) Run-2 specific interpretation rule (k-aware, frozen)

Run 2’s target-key corruption is not automatically “degradation.” Classification is determined entirely by AA/AAA/RTD and the frozen classifier.

However, you must include an explicit run-level note in the report:

> If eligibility semantics (`k`-of-`n`) permit governance to remain stable despite one impaired commitment key, then Run 2 may remain **Stable Authority** even at high `p_target_flip_ppm`.

This avoids the “false positive” mistake.

---

## 6) Expected qualitative shape (pre-registered hypotheses)

### H1 (equivalence to Run 1 under strict AND aggregation)

If AKI aggregation is strict conjunction, then single-key corruption should approximate aggregate corruption at a comparable effective rate, producing similar AA/AAA curves to Run 1.

### H2 (no terminal collapse without high p)

If failure occurs, it should appear as **Asymptotic DoS** or **Structural Thrashing**, not immediate terminal collapse.

### H3 (CTA imprint)

If degradation occurs, RTD should show clustering around CTA-relevant scales (heavy-lapse cutoff anchored to `amnesty_interval` per thresholds doc).

---

## 7) Script: `scripts/rsa_v020_run2_commitment_correlated.py`

### Required output blocks

For each `rsa_p_target_flip_ppm`:

1. **Run header**: AKI config hash (including amnesty interval), RSA config hash, target key, horizon (cycles), derived `horizon_epochs`, derived `tail_window`
2. **Per-seed table**: AA_ppm, AAA_ppm, failure_class, lapse_count, total_lapse_epochs, max_single_lapse_epochs, observed_flip_rate_ppm, pivotal_rate_ppm, flips_by_key summary
3. **Aggregate summary**: mean/std AA and AAA, class counts, RTD aggregate summary
4. **RSA integrity block**: targets/flips/observed vs expected + pivotal flips + “flips_by_key must be only C1”

### Skeleton pseudocode (structure, not implementation)

* loop over `p in sweep_values`

  * set RSAConfig with `rsa_p_target_flip_ppm=p`, `rsa_target_key="C1"`
  * for each seed

    * run `ALSHarnessV080(seed, als_config, rsa_config)`
    * collect metrics + RSA summary
  * aggregate and print required blocks

---

## 8) Definition of Done (Run 2)

Run 2 is complete when:

* sweep executes for all `p_target_flip_ppm` × seeds
* per-seed AA/AAA/RTD + failure class are reported for each p
* aggregate summaries are reported for each p
* RSA integrity metrics are reported (observed vs expected)
* `flips_by_key` shows flips only under target key (`C1`)
* pivotal flip stats are reported

No refactors, no new models, no additional sweep points, no target-key changes inside Run 2.
