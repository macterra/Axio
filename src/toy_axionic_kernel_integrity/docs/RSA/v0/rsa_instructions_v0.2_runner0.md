# RSA v0.2 Run 0 — Baseline Reference (No Interference)

## Purpose

Establish a **clean reference baseline** for all RSA v0.2 experiments under the **exact frozen AKI configuration, horizon, and seed set** used in Runs 1–3.

Run 0 exists to answer one question only:

> *What does governance look like with **no epistemic interference** under the v0.2 experimental setup?*

This run anchors AA / AAA / RTD values so all subsequent degradation claims are comparative, not absolute.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`)
* Eligibility rule and `eligibility_threshold_k` (frozen baseline)
* CTA parameters (`amnesty_interval=10`, `amnesty_decay=1`)
* Candidate pool composition and successor types
* Horizon, renewal interval, and epoch definition (use frozen v0.2 baseline)
* Seed set (fixed)
* Metrics computation (`AA`, `AAA`, `RTD`) and failure classifier (frozen)

### No independent variables

Run 0 has **no sweep axis**.

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config (baseline for v0.2)

Use the same AKI config that will be used verbatim in Runs 1–3.

```python
ALSConfigV080(
    max_cycles=300_000,             # frozen for v0.2 (yields 6000 epochs at renewal_check_interval=50)
    eligibility_threshold_k=3,       # frozen baseline
    max_successive_renewals=3,       # frozen baseline
    amnesty_interval=10,             # frozen baseline
    amnesty_decay=1,                # frozen baseline
    cta_enabled=True,               # frozen baseline
)
```

**Do not** alter any AKI parameters for Run 0.

### 1.2 RSA config (two required conditions)

Run 0 must be executed under **two conditions**, using the same seeds and horizon.

#### Condition A — RSA disabled (true clean baseline)

```python
RSAConfig(
    rsa_enabled=False,
)
```

#### Condition B — RSA enabled, zero-probability (enabled-path equivalence)

```python
RSAConfig(
    rsa_enabled=True,
    rsa_noise_model=RSANoiseModel.AGG_FLIP_BERNOULLI,
    rsa_scope=RSAScope.SEM_PASS_ONLY,
    rsa_rng_stream="rsa_v020",
    rsa_p_flip_ppm=0,
)
```

**Requirement:** Results from Condition A and Condition B must be **identical** at trace level (as already enforced by acceptance tests). Report both anyway.

### 1.3 Seeds (fixed)

Use the same seed battery as all other v0.2 runs:

* `seeds = [40, 41, 42, 43, 44]`

---

## 2) Execution

For each condition (A and B):

1. Loop over all seeds
2. Run `ALSHarnessV080(seed, als_config, rsa_config)`
3. Collect per-seed metrics and RSA telemetry (if applicable)

**No early termination.** Each run must complete the full horizon.

---

## 3) Metrics (must report per seed and aggregate)

Run 0 uses the **exact same metrics and classifier** as Runs 1–3.

### 3.1 Governance outcomes (per seed)

* `authority_availability_ppm` (AA)
* `asymptotic_authority_availability_ppm` (AAA)
* `failure_class`
* `recovery_time_histogram` (RTD)
* `lapse_count`
* `total_lapse_epochs`
* `max_single_lapse_epochs`
* `epochs_evaluated`
* `epochs_in_lapse`

### 3.2 Aggregate summary (across seeds)

* mean and std (or min/max) for AA and AAA
* counts by `failure_class`
* RTD aggregate summary
* distribution summary of `max_single_lapse_epochs`

### 3.3 RSA integrity metrics (Condition B only)

Even though `rsa_p_flip_ppm=0`, still report:

* `total_targets`
* `total_flips` (must be 0)
* `observed_flip_rate_ppm` (must be 0)
* `epochs_evaluated`
* `epochs_in_lapse`

This proves enabled-path equivalence empirically, not just via tests.

---

## 4) Failure Classification (Frozen)

Use the exact classifier implemented in:

* `toy_aki/rsa/metrics.py`

with frozen constants documented in:

* `docs/rsa_v020_failure_thresholds.md`

No reinterpretation. Emit exactly one label per run.

---

## 5) Output Format

### Script name

```
scripts/rsa_v020_run0_baseline_reference.py
```

### Required output blocks

For each condition (A and B):

1. **Run header**

   * AKI config hash
   * RSA config hash
   * horizon cycles
   * derived `horizon_epochs`
   * derived `tail_window`
2. **Per-seed table**

   * AA_ppm, AAA_ppm, failure_class
   * lapse_count, total_lapse_epochs, max_single_lapse_epochs
3. **Aggregate summary**

   * mean/std AA and AAA
   * class counts
   * RTD aggregate summary
4. **RSA integrity block** (Condition B only)

### Final baseline assertion

Print an explicit statement:

> “Condition A (RSA disabled) and Condition B (RSA enabled, p=0) produced identical per-seed metrics.”

If they do not, **stop immediately** and do not proceed to Runs 1–3.

---

## 6) Definition of Done (Run 0)

Run 0 is complete when:

* both baseline conditions execute for all seeds
* per-seed metrics are reported for both conditions
* aggregate summaries are reported
* RSA integrity metrics confirm zero flips in Condition B
* equivalence between Condition A and B is explicitly stated

No refactors. No sweeps. No interpretation.

---

## Role of Run 0 in v0.2

Run 0 is not a stress test.
It is not an experiment.

It is the **ground truth reference** that makes every v0.2 degradation claim legible and defensible.
