# RSA v1.0 Run 0 — Baseline Reference (No Adversary)

## Purpose

Establish a **clean reference baseline** for all RSA v1.0 experiments under the **exact frozen AKI configuration, horizon, and seed set** used in Runs 1–5.

Run 0 exists to answer one question only:

> *What does governance look like with **no adversarial policy layer** under the v1.0 experimental setup?*

This run anchors AA / AAA / RTD (and renewal/eligibility diagnostics) so all subsequent degradation claims are comparative, not absolute.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`)
* Eligibility rule and `eligibility_threshold_k` (fail-streak semantics; frozen baseline)
* CTA parameters (`amnesty_interval=10`, `amnesty_decay=1`)
* Candidate pool composition and successor types
* Horizon, renewal interval, and epoch definition (use frozen v1.0 baseline)
* Seed set (fixed)
* Metrics computation (`AA`, `AAA`, `RTD`) and failure classifier (frozen)
* RSA v1.0 policy interface (must remain inactive in Run 0)

### No independent variables

Run 0 has **no sweep axis**.

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config (baseline for v1.0)

Use the same AKI config that will be used verbatim in Runs 1–5.

```python
ALSConfigV080(
    max_cycles=300_000,             # frozen for v1.0 (yields 6000 epochs at renewal_check_interval=50)
    eligibility_threshold_k=3,       # frozen baseline (fail-streak; eligible iff streak < K)
    max_successive_renewals=3,       # frozen baseline
    amnesty_interval=10,             # frozen baseline
    amnesty_decay=1,                # frozen baseline
    cta_enabled=True,               # frozen baseline
)
```

**Do not** alter any AKI parameters for Run 0.

---

### 1.2 RSA v1.0 policy config (two required conditions)

Run 0 must be executed under **two conditions**, using the same seeds and horizon.

#### Condition A — RSA policy disabled (true clean baseline)

Run with no RSA policy config (or with policy wrapper absent), i.e. RSA v1.0 must not intercept actions.

```python
# Preferred: omit rsa_policy_config entirely (wrapper remains None)
ALSHarnessV080(
    seed=seed,
    config=als_config,
    rsa_policy_config=None,
)
```

#### Condition B — RSA policy enabled but NONE (enabled-path equivalence)

Run with RSA v1.0 policy layer active, but with the no-op policy.

```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.NONE,
    epoch_size=als_config.renewal_check_interval,
)
```

**Requirement:** Results from Condition A and Condition B must be **identical at the per-seed metric level** (as enforced by acceptance tests). Report both anyway.

> Note: This equivalence check validates that the *presence* of the policy layer does not perturb AKI behavior when the policy is NONE.

---

### 1.3 Seeds (fixed)

Use the same seed battery as all other v1.0 runs:

```python
seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
```

---

## 2) Execution

For each condition (A and B):

1. Loop over all seeds
2. Run `ALSHarnessV080(seed, als_config, rsa_policy_config=...)`
3. Collect per-seed metrics and telemetry (if applicable)

**No early termination.** Each run must complete the full horizon.

---

## 3) Metrics (must report per seed and aggregate)

Run 0 uses the **exact same metrics and classifier** as Runs 1–5.

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

### 3.2 v1.0 derived diagnostics (per seed)

These must be computed and reported even in baseline:

* `max_consecutive_sem_pass`
* `max_consecutive_sem_fail`
* `ever_ineligible` (True iff `max_consecutive_sem_fail >= K`)
* `ineligibility_fraction`
* `renewal_check_epochs_count`
* `renewals_succeeded`
* `renewal_success_rate_ppm`

### 3.3 Aggregate summary (across seeds)

* mean and std (or min/max) for AA and AAA
* counts by `failure_class`
* RTD aggregate summary
* distribution summary of `max_single_lapse_epochs`
* mean/std of:

  * `ineligibility_fraction`
  * `renewal_success_rate_ppm`

### 3.4 RSA policy integrity (Condition B only)

Even though `policy_model=NONE`, still report:

* `rsa_enabled` (True)
* `rsa_model` (NONE)
* `actions_emitted_by_type` aggregate summary (optional but recommended)
* confirmation that policy wrapper was present but emitted no modifications (if your harness tracks “override occurred”)

This proves enabled-path equivalence empirically, not just via tests.

---

## 4) Failure Classification (Frozen)

Use the exact classifier implemented in:

* `toy_aki/rsa/metrics.py`

No reinterpretation. Emit exactly one label per run.

---

## 5) Output Format

### Script name

```
scripts/rsa_v100_run0_baseline.py
```

### Required output blocks

For each condition (A and B):

1. **Run header**

   * AKI config hash
   * policy config hash (or `None`)
   * horizon cycles
   * derived `horizon_epochs`
   * derived `tail_window`

2. **Per-seed table**

   * AA_ppm, AAA_ppm, failure_class
   * lapse_count, total_lapse_epochs, max_single_lapse_epochs
   * renewal_success_rate_ppm, ineligibility_fraction, ever_ineligible

3. **Aggregate summary**

   * mean/std AA and AAA
   * class counts
   * RTD aggregate summary
   * mean/std renewal_success_rate_ppm and ineligibility_fraction

4. **RSA policy integrity block** (Condition B only)

### Final baseline assertion

Print an explicit statement:

> “Condition A (policy disabled) and Condition B (policy enabled, NONE) produced identical per-seed metrics.”

If they do not, **stop immediately** and do not proceed to Runs 1–5.

---

## 6) Definition of Done (Run 0)

Run 0 is complete when:

* both baseline conditions execute for all seeds
* per-seed metrics are reported for both conditions
* aggregate summaries are reported
* policy integrity block confirms no-op behavior in Condition B
* equivalence between Condition A and B is explicitly stated

No refactors. No sweeps. No interpretation.

---

## Role of Run 0 in v1.0

Run 0 is not a stress test.
It is not an experiment.

It is the **ground truth reference** that makes every v1.0 degradation claim legible and defensible.
