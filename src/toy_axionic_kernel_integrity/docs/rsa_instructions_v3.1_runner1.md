# RSA v3.1 Run 1 — Model M (RECOVERY_AWARE_TIMING)

## Purpose

Evaluate whether a **bounded, semantic-free learning adversary** can exploit **recovery timing** more effectively than any fixed or stateful FSM adversary tested in v3.0.

Run 1 exists to answer one question only:

> *Can within-run learning of attack timing (via ε-greedy bandits over attack sets) reduce Authority Availability or induce a classified constitutional failure relative to the Run 0 baseline?*

This run tests **adaptive timing**, not semantics, deception, kernel access, or cross-run learning.

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

* **Adversary model only**: `RECOVERY_AWARE_TIMING`

No parameter sweeps. No hyperparameter tuning. No retries.

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config

Identical to Run 0.

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

### 1.2 RSA v3.1 policy config — Model M

```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.RECOVERY_AWARE_TIMING,
    rsa_version="v3.1",

    # State bounds
    rsa_max_internal_states=50,    # |S| = epoch_size
    rsa_max_learning_states=16,    # |Θ| = attack_set_count

    # Learning parameters (frozen)
    rsa_q_scale=1000,              # fixed-point
    rsa_learning_rate_shift=6,     # lr = 1/64
    rsa_epsilon_ppm=100_000,       # ε = 10%

    # Model M parameters
    rsa_attack_set_count=16,

    # Epoch size (= renewal_check_interval)
    epoch_size=50,
)
```

**Do not modify** any values above.

---

### 1.3 Seeds (fixed)

Use the same seed battery as Run 0:

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

---

### 3.2 Learning / integrity diagnostics (per seed)

These are **mandatory** in v3.1:

* `wrapper_invoked_count`
* `override_count`
* `distinct_internal_states_observed` (must be ≥ 2)
* `distinct_learning_states_observed` (must be ≥ 2)
* `Q_value_range` (min/max over run)
* `final_Q_values` (all 16 entries)
* `attack_set_selection_counts` (histogram)
* `empirical_epsilon_rate`
  *(fraction of exploratory vs exploitative selections)*

If any exercised-state condition fails, the run is **invalid**.

---

### 3.3 Aggregate summary (across seeds)

* mean / std of:

  * `AA_ppm`
  * `AAA_ppm`
  * `ΔAA_ppm`
* counts by `failure_class`
* RTD aggregate summary
* mean / std of:

  * `lapse_count`
  * `max_single_lapse_epochs`
* qualitative note:

  * whether Q-values converge, oscillate, or remain flat

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
scripts/rsa_v310_run1_model_m.py
```

### Required artifacts

1. **Console output** (gate decision)
2. **Markdown report**

```
reports/rsa_v310_run1_model_m.md
```

The report must contain:

* Run header (hashes, horizon, seeds)
* Per-seed table (with ΔAA_ppm)
* Aggregate summary
* Learning diagnostics
* Integrity block

---

## 6) Gate Conditions (Run 1)

Run 1 is considered **complete** when:

* All 10 seeds execute to horizon
* All integrity checks pass
* Exercised internal state and learning state are confirmed
* Metrics are computed and reported
* No acceptance test is violated

Run 1 is considered **positive (architectural stress)** if **any** of the following occur:

* `Terminal Collapse`
* `Structural Thrashing`
* `Irreversible Recovery Suppression`
* `Asymptotic DoS` (AA → 0 above AA_floor)

Otherwise, Run 1 is a **negative result** for timing-based learning.

---

## 7) Interpretation Discipline

Before looking at results, commit to:

* **No cherry-picking seeds**
* **No post-hoc reward reinterpretation**
* **No hyperparameter adjustment**
* **No reruns**

Run 1 answers **one question only**:
whether adaptive timing via bounded learning defeats constitutional recovery.

---

## Role of Run 1 in v3.1

Run 1 tests the **strongest non-semantic attack class**:
*learning to strike at the right time*.

If this fails, the remaining threat surface narrows sharply.

Proceed exactly once.
