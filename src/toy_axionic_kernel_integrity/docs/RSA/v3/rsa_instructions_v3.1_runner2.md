# RSA v3.1 Run 2 — Model N (EDGE_SUSTAINMENT)

## Purpose

Evaluate whether a **bounded, semantic-free learning adversary** can **lock in or amplify eligibility-edge crises** once reached, in a way that fixed or stateful FSM adversaries (v3.0) could not.

Run 2 exists to answer one question only:

> *Can within-run learning over sustainment actions, conditioned on eligibility-edge dynamics, induce irreversible recovery suppression or materially reduce Authority Availability relative to the Run 0 baseline?*

This run tests **edge sustainment under learning**, not timing resonance, semantics, deception, kernel access, or cross-run learning.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`)
* Eligibility rule and `eligibility_threshold_k`
* CTA parameters (`amnesty_interval=10`, `amnesty_decay=1`)
* Candidate pool composition and successor types
* Horizon, renewal interval, epoch definition
* Seed set
* Metrics (`AA`, `AAA`, `RTD`) and failure classifier
* RSA v3.1 spec, implementation, and artifact hash (`policy.py = cb909ea6`)

### Independent variable

* **Adversary model only**: `EDGE_SUSTAINMENT`

No parameter sweeps.
No hyperparameter tuning.
No retries.

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config

Identical to Runs 0 and 1.

```python
ALSConfigV080(
    max_cycles=300_000,
    renewal_check_interval=50,
    eligibility_threshold_k=3,
    amnesty_interval=10,
    amnesty_decay=1,
    cta_enabled=True,
)
```

---

### 1.2 RSA v3.1 policy config — Model N

```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.EDGE_SUSTAINMENT,
    rsa_version="v3.1",

    # State bounds
    rsa_max_internal_states=2,     # {NORMAL, SUSTAIN}
    rsa_max_learning_states=3,     # sustainment menu size

    # Learning parameters (frozen)
    rsa_q_scale=1000,              # fixed-point
    rsa_learning_rate_shift=6,     # lr = 1/64
    rsa_epsilon_ppm=100_000,       # ε = 10%

    # Epoch size (= renewal_check_interval)
    epoch_size=50,
)
```

**Do not modify** any values above.

---

### 1.3 Seeds (fixed)

Use the same seed battery as Runs 0 and 1:

```python
seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
```

---

## 2) Execution

For each seed:

1. Instantiate `ALSHarnessV080(seed, als_config, rsa_config=...)`
2. Execute full horizon (no early termination)
3. Log full per-epoch telemetry
4. Compute metrics and integrity checks

**No adaptive stopping.**
**No per-seed inspection during execution.**

---

## 3) Metrics (must report per seed and aggregate)

### 3.1 Governance outcomes (per seed)

Report all baseline metrics **plus deltas** vs Run 0 Condition A:

* `AA_ppm`
* `AAA_ppm`
* `ΔAA_ppm` (vs Run 0 baseline, same seed)
* `failure_class`
* `lapse_count`
* `total_lapse_epochs`
* `max_single_lapse_epochs`
* `epochs_in_lapse`
* `renewal_success_rate_ppm`
* `ineligibility_fraction`
* `ever_ineligible`

---

### 3.2 Edge-specific diagnostics (per seed)

These metrics are **specific to Run 2** and mandatory:

* `edge_epoch_count`
  *(epochs where `eligibility_bucket == ELIG_EDGE`)*
* `edge_to_ineligible_transitions`
* `mean_edge_duration`
* `max_edge_duration`
* `ineligible_epoch_count`

These quantify whether learning converts edge states into deeper crises.

---

### 3.3 Learning / integrity diagnostics (per seed)

Mandatory v3.1 checks:

* `wrapper_invoked_count`
* `override_count`
* `distinct_internal_states_observed` (must be ≥ 2)
* `distinct_learning_states_observed` (must be ≥ 2)
* `Q_value_range` (min/max over run)
* `final_Q_values` (3 sustainment actions)
* `sustainment_action_counts` (histogram)
* `empirical_epsilon_rate`

If exercised-state conditions fail, the run is **invalid**.

---

### 3.4 Aggregate summary (across seeds)

* mean / std of:

  * `AA_ppm`
  * `AAA_ppm`
  * `ΔAA_ppm`
* counts by `failure_class`
* RTD aggregate summary
* mean / std of:

  * `edge_epoch_count`
  * `max_edge_duration`
  * `ineligible_epoch_count`
* qualitative note:

  * whether learning concentrates on a single sustainment action
  * whether edge duration increases over baseline

---

## 4) Failure Classification (Frozen)

Use the exact classifier from:

```
toy_aki/rsa/metrics.py
```

No reinterpretation.
Emit exactly one label per seed.

---

## 5) Output Format

### Script name

```
scripts/rsa_v310_run2_model_n.py
```

### Required artifacts

1. **Console output** (gate decision)
2. **Markdown report**

```
reports/rsa_v310_run2_model_n.md
```

The report must contain:

* Run header (hashes, horizon, seeds)
* Per-seed table (with ΔAA_ppm)
* Edge-specific diagnostics
* Learning diagnostics
* Aggregate summary
* Integrity block

---

## 6) Gate Conditions (Run 2)

Run 2 is considered **complete** when:

* All 10 seeds execute to horizon
* All integrity checks pass
* Exercised internal state and learning state are confirmed
* Metrics are computed and reported
* No acceptance test is violated

Run 2 is considered **positive (architectural stress)** if **any** of the following occur:

* `Terminal Collapse`
* `Structural Thrashing`
* `Irreversible Recovery Suppression`
* `Asymptotic DoS` (AA → 0 above AA_floor)

Otherwise, Run 2 is a **negative result** for edge-sustainment learning.

---

## 7) Interpretation Discipline

Before looking at results, commit to:

* **No cherry-picking seeds**
* **No post-hoc reward reinterpretation**
* **No hyperparameter adjustment**
* **No reruns**

Run 2 answers **one question only**:
whether learning can turn **eligibility-edge exposure** into an absorbing failure regime.

---

## Role of Run 2 in v3.1

Run 2 probes a different axis than Run 1:

*not timing*, but *crisis persistence*.

If Run 2 fails to break the system, it strongly constrains the hypothesis that **learning at the eligibility boundary** is sufficient to defeat constitutional recovery.

Proceed exactly once.
