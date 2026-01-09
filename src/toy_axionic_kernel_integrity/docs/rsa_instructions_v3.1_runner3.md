# RSA v3.1 Run 3 — Model O (STOCHASTIC_MIXER)

## Purpose

Evaluate whether a **bounded, semantic-free learning adversary** can outperform all fixed and stateful strategies by **stochastically mixing among them with feedback**, thereby discovering combinations or alternations that defeat constitutional recovery.

Run 3 exists to answer one question only:

> *Can bounded, kernel-external learning over a portfolio of known strategies induce constitutional failure or materially reduce Authority Availability beyond any single strategy alone?*

This run tests **strategy mixing under learning**, not timing precision (Run 1), edge lock-in (Run 2), semantics, deception, kernel access, or cross-run learning.

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

* **Adversary model only**: `STOCHASTIC_MIXER`

No parameter sweeps.
No hyperparameter tuning.
No retries.

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config

Identical to Runs 0–2.

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

### 1.2 RSA v3.1 policy config — Model O

```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.STOCHASTIC_MIXER,
    rsa_version="v3.1",

    # State bounds
    rsa_max_internal_states=5,      # current strategy index
    rsa_max_learning_states=5,      # learning dimensions (K strategies)

    # Learning parameters (frozen)
    rsa_q_scale=1000,               # fixed-point scale
    rsa_learning_rate_shift=6,      # lr = 1/64
    rsa_epsilon_ppm=100_000,        # ε = 10%

    # Model O parameters
    rsa_strategy_count=5,           # K = 5 strategies
    rsa_weight_max=10_000,          # WMAX per strategy

    # Epoch size (= renewal_check_interval)
    epoch_size=50,
)
```

**Do not modify** any values above.

---

### 1.3 Strategy Pool (Frozen)

The stochastic mixer must select exclusively from the following **fixed strategy set**:

| Index | Strategy         | Description                  | Origin           |
| ----: | ---------------- | ---------------------------- | ---------------- |
|     0 | COMPLIANT        | Always compliant             | Baseline         |
|     1 | RESONANT_LAPSE   | Periodic invalid commit      | v3.0 Model J     |
|     2 | EDGE_OSCILLATOR  | Eligibility-edge alternation | v3.0 Model K     |
|     3 | CTA_PHASE_LOCKER | CTA boundary attacks         | v3.0 Model L     |
|     4 | INVALID_ALWAYS   | Always invalid commit        | New (degenerate) |

No additional strategies may be added.

---

### 1.4 Seeds (fixed)

Use the same seed battery as all prior runs:

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

### 3.2 Strategy-mixing diagnostics (per seed)

These metrics are **specific to Run 3** and mandatory:

* `strategy_selection_counts` (histogram over 5 strategies)
* `strategy_selection_entropy`
* `dominant_strategy` (argmax of final weights)
* `dominant_strategy_fraction`
* `strategy_switch_count`
* `longest_strategy_streak`

These quantify whether learning collapses onto one strategy or exploits alternation.

---

### 3.3 Learning / integrity diagnostics (per seed)

Mandatory v3.1 checks:

* `wrapper_invoked_count`
* `override_count`
* `distinct_internal_states_observed` (must be ≥ 2)
* `distinct_learning_states_observed` (must be ≥ 2)
* `weight_range_per_strategy` (min/max over run)
* `final_weights` (all 5 entries)
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

  * `strategy_selection_entropy`
  * `strategy_switch_count`
* qualitative note:

  * whether mixing outperforms any single constituent strategy
  * whether weights converge, oscillate, or remain diffuse

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
scripts/rsa_v310_run3_model_o.py
```

### Required artifacts

1. **Console output** (gate decision)
2. **Markdown report**

```
reports/rsa_v310_run3_model_o.md
```

The report must contain:

* Run header (hashes, horizon, seeds)
* Per-seed table (with ΔAA_ppm)
* Strategy-mixing diagnostics
* Learning diagnostics
* Aggregate summary
* Integrity block

---

## 6) Gate Conditions (Run 3)

Run 3 is considered **complete** when:

* All 10 seeds execute to horizon
* All integrity checks pass
* Exercised internal state and learning state are confirmed
* Metrics are computed and reported
* No acceptance test is violated

Run 3 is considered **positive (architectural stress)** if **any** of the following occur:

* `Terminal Collapse`
* `Structural Thrashing`
* `Irreversible Recovery Suppression`
* `Asymptotic DoS` (AA → 0 above AA_floor)

Otherwise, Run 3 is a **negative result** for stochastic mixing.

---

## 7) Interpretation Discipline

Before looking at results, commit to:

* **No cherry-picking seeds**
* **No post-hoc strategy reinterpretation**
* **No hyperparameter adjustment**
* **No reruns**

Run 3 answers **one question only**:
whether **learning to mix strategies** defeats constitutional recovery.

---

## Role of Run 3 in v3.1

Run 3 is the **last adversary class** in RSA v3.1.

If this run fails to induce collapse, you will have shown:

> *No kernel-external, semantic-free adversary—stateless, stateful, or learning, including stochastic mixers—can defeat constitutional survivability under the AKI v0.8 contract.*

Proceed exactly once.
