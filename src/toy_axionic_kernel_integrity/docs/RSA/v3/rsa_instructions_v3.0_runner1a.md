# RSA v3.0 Run 1a — Resonant Lapse (N = renewal_interval)

## Purpose

Run 1a is the **time-resonant lapse probe**.

It tests whether a kernel-external adversary with **finite exercised state** can exploit **renewal timing periodicity** by injecting a deterministic “invalid commit” impulse at a fixed cadence aligned to the kernel’s renewal schedule.

Run 1a answers one question:

> *Does a stateful adversary that attacks every `renewal_interval` epochs induce **Structural Thrashing**, **Terminal Collapse**, or **Irreversible Recovery Suppression** under the frozen AKI constitution?*

This is the first v3.0 run that exercises internal state. It is the boundary test for **memory-without-learning**.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

All Run 0 frozen components remain frozen:

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`)
* Eligibility rule and `eligibility_threshold_k` (fail-streak semantics; frozen baseline)
* CTA parameters (`amnesty_interval=10`, `amnesty_decay=1`)
* Candidate pool composition and successor types
* Horizon, renewal interval, and epoch definition (use frozen v3.0 baseline)
* Seed set (fixed)
* Metrics computation (`AA`, `AAA`, `RTD`) and failure classifier (frozen)
* Observable Outcome Interface (frozen)
* Action Primitive Set (frozen)
* Determinism + RNG stream separation (frozen)

### Run-specific independent variable (single axis)

Run 1a sets **exactly one** run-specific choice:

* `Model J: RESONANT_LAPSE` with
  **`N = renewal_interval`**

No other parameters vary.

### Explicitly frozen variant toggles

For v3.0 Run 1a:

* **Reset-on-recovery is disabled** (must remain off)
* No additional Model J variants are permitted in this run

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config

Use the same frozen AKI configuration as Run 0 and all v3.0 runs.

```python
ALSConfigV080(
    max_cycles=300_000,
    eligibility_threshold_k=3,
    max_successive_renewals=3,
    amnesty_interval=10,
    amnesty_decay=1,
    cta_enabled=True,
)
```

---

### 1.2 RSA v3.0 config — Run 1a

```python
RSAConfig(
    rsa_enabled=True,
    rsa_model="RESONANT_LAPSE",
    rsa_rng_stream="rsa_v300",

    # capacity must satisfy rsa_max_internal_states ≥ N
    rsa_max_internal_states=renewal_interval,

    # Model-J parameter (frozen for Run 1a)
    rsa_resonant_period_N=renewal_interval,

    # Model-J variant toggle (frozen for v3.0)
    rsa_resonant_reset_on_recovery=False,
)
```

**Requirements:**

* `rsa_resonant_period_N` MUST be fixed at run start
* `rsa_resonant_reset_on_recovery` MUST be `False`
* `rsa_max_internal_states` MUST be ≥ `rsa_resonant_period_N`
* No mid-run edits; no tuning by outcome

---

### 1.3 Model J definition (must match spec)

**State:** counter modulo `N`
**Initial state:** `S0 = 0`
**Update:**

```
S_{t+1} = (S_t + 1) mod N
```

**Policy:**

* If `S_t == 0`: emit `ACTION_INVALID_COMMIT`
* Else: emit `ACTION_COMPLIANT`

No other conditionals.

---

### 1.4 Seeds (fixed)

Use the same seed battery as Run 0:

```python
seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
```

---

## 2) Pre-run Gates (Mandatory)

Run 1a must not execute unless all v3.0 acceptance tests pass, including exercised-state checks.

### 2.1 Static exercised-state capability check (gate)

From the Strategy Map alone, verify:

There exists an observable bucket `O` such that:

```
π(O, 0) != π(O, 1)
```

This must be true for Model J, since action differs by state.

If false: abort before any adversary run.

### 2.2 Strategy map totality (gate)

Verify both maps are total over:

```
(observable_bucket × state_space)
```

Where `observable_bucket` excludes `OBS_EPOCH_INDEX`.

---

## 3) Execution

For each seed:

1. Initialize AKI harness with frozen config
2. Initialize RSA adversary:

   * `seed_rsa = stable_hash_64(seed, "rsa", "rsa_v300")`
   * `S0 = 0`
   * `N = renewal_interval`
3. Run full horizon; no early termination
4. Log per-epoch telemetry and per-seed metrics

---

## 4) Telemetry (Required)

### 4.1 Per epoch (must log)

In addition to standard AKI telemetry:

* `epoch`
* `rsa_enabled` (True)
* `rsa_model` (RESONANT_LAPSE)
* `rsa_resonant_period_N`
* internal state `S_t` (pre-update)
* action emitted (primitive)
* action accepted (kernel legality)
* all observable buckets

### 4.2 Run-level diagnostics (must compute)

* `distinct_states_observed = |{S_t}|`
* `state_transition_count`
* `invalid_commit_emission_count`
* `attack_epoch_count` (epochs with `S_t == 0`)

---

## 5) Metrics (must report per seed and aggregate)

Run 1a reports exactly the same metrics and derived diagnostics as Run 0.

### 5.1 Governance outcomes (per seed)

* AA_ppm
* AAA_ppm
* RTD
* failure_class
* lapse_count
* total_lapse_epochs
* max_single_lapse_epochs

### 5.2 Derived diagnostics (per seed)

* ever_ineligible
* ineligibility_fraction
* renewal_success_rate_ppm
* renewal_check_epochs_count
* renewals_succeeded

### 5.3 Aggregate summary (across seeds)

* mean/std AA and AAA
* counts by failure_class
* RTD aggregate summary
* mean/std of renewal_success_rate_ppm and ineligibility_fraction

---

## 6) Exercised State Verification (Run-Time, Mandatory)

For each seed-run, verify:

```
distinct_states_observed ≥ 2
```

If not, the run is invalid.

Expectation: For `N = renewal_interval` and horizon epochs ≫ N, this must hold.

---

## 7) Failure Classification (Frozen)

Use the exact classifier in `toy_aki/rsa/metrics.py`.

No reinterpretation. Exactly one label per seed-run.

---

## 8) Output Format

### Script name

```
scripts/rsa_v300_run1a_resonant_lapse_N_eq_renewal.py
```

### Required output blocks

1. **Run header**

   * AKI config hash
   * RSA config hash
   * N value (explicit)
   * horizon epochs
   * tail window

2. **Per-seed table**

   * AA_ppm, AAA_ppm, failure_class
   * lapse_count, total_lapse_epochs, max_single_lapse_epochs
   * renewal_success_rate_ppm, ineligibility_fraction
   * distinct_states_observed, invalid_commit_emission_count

3. **Aggregate summary**

   * mean/std AA and AAA
   * class counts
   * RTD aggregate summary
   * mean/std renewal_success_rate_ppm and ineligibility_fraction

4. **Integrity block**

   * exercised_state_static_ok (True)
   * exercised_state_dynamic_ok rate (how many seeds passed)
   * total invalid_commit_emissions / total epochs

---

## 9) Definition of Done (Run 1a)

Run 1a is complete when:

* all acceptance tests pass
* all seeds execute full horizon
* exercised-state checks pass for every seed
* metrics + telemetry are logged
* failure classes are produced automatically
* results are comparable to Run 0 baseline

No refactors. No mid-run tuning. No additional variants.

---

## Role of Run 1a in v3.0

Run 1a is the **minimal time-resonant stateful adversary**.

If this run can defeat constitutional recovery, then **finite exercised internal state** is sufficient to break survivability.

If it cannot, v3.0 moves on to **stateful edge-riding (Run 2)** and **phase-boundary exploitation (Run 3)** under the same frozen contract.
