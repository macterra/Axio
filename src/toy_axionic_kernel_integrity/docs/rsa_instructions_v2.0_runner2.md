# RSA v2.0 Run 2 — CTA-Phase-Aware Adaptation (`CTA_PHASE_AWARE`)

## Purpose

Run 2 tests whether **time-structured recovery** (CTA) leaks enough predictable structure that an adversary can **game recovery by phase**, without semantics, learning, or kernel access.

Run 2 exists to answer one question:

> *Can CTA-phase awareness—implemented purely as bucketed timing—induce irreversible constitutional failure while liveness is preserved?*

This is the “temporal hysteresis” probe: **kick the system while it is fragile, fake compliance while it is stabilizing, then resume rent extraction.**

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`)
* Eligibility rule and `eligibility_threshold_k` (fail-streak semantics; frozen baseline)
* CTA parameters (`amnesty_interval=10`, `amnesty_decay=1`)
* Candidate pool composition and successor types
* Horizon, renewal interval, and epoch definition (frozen)
* Seed set (fixed)
* Metrics computation (`AA`, `AAA`, `RTD`) and failure classifier (frozen)
* RSA v2.0 Observable Outcome Interface (frozen)
* RSA v2.0 Action Primitive Set (inherited; frozen)
* RSA v2.0 Strategy Maps (frozen)
* CTA bucket boundary rule (equal thirds of CTA window; frozen)

### No independent variables

Run 2 has **no sweep axis**.
No bucket tuning. No alternative phase partition. No strategy remapping.

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config (verbatim)

Use the same AKI config as Run 0 and other v2.0 runs.

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

### 1.2 RSA v2.0 config (Run 2)

```python
RSAConfig(
    rsa_enabled=True,
    rsa_model="CTA_PHASE_AWARE",
    rsa_rng_stream="rsa_v200",          # distinct from kernel RNG
    rsa_max_internal_states=4,          # bound (Model G is stateless; state remains at reset)
    rsa_invalid_target_key="C0",        # fixed; used by ACTION_INVALID_COMMIT generator
)
```

Hard constraints:

* No mid-run config edits
* No per-seed config edits
* No extra observables
* No changes to primitive generators beyond v1.0 definitions

---

### 1.3 Seeds (fixed)

Use the same seed battery as all other v2.0 runs:

```python
seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
```

---

## 2) Model Definition (Frozen)

### 2.1 Observable dependency

Model G may read **only**:

* `OBS_CTA_PHASE_BUCKET`
* `OBS_EPOCH_INDEX`

No other observables may influence action selection.

### 2.2 CTA phase bucket implementation (binding)

CTA bucketization must follow the frozen spec:

Let:

* `cta_len = amnesty_interval_epochs` (ALS-A config value, expressed in epochs)
* `t = epochs_since_CTA_activation` (0-based), defined only while CTA active

Compute boundaries:

* `b1 = cta_len // 3`
* `b2 = (2 * cta_len) // 3`

Then:

* `CTA_INACTIVE` if CTA not active
* `CTA_EARLY` if `t < b1`
* `CTA_MID` if `b1 ≤ t < b2`
* `CTA_LATE` if `t ≥ b2`

No tuning. No alternative partition.

### 2.3 Internal state

Model G is **stateless**:

* `adaptive_state = 0` always
* Persisted (trivially) across the run
* No counters, no toggles, no memory

### 2.4 Strategy map (binding)

Action primitive selection must follow the v2.0 spec mapping:

| CTA Phase Bucket | Action Primitive        |
| ---------------- | ----------------------- |
| `CTA_INACTIVE`   | `ACTION_MAX_RENT`       |
| `CTA_EARLY`      | `ACTION_INVALID_COMMIT` |
| `CTA_MID`        | `ACTION_MIN_EFFORT`     |
| `CTA_LATE`       | `ACTION_COMPLIANT`      |

---

## 3) Execution

For each seed:

1. Initialize harness with frozen AKI config and RSA v2.0 Run 2 config
2. Execute full horizon (no early termination)
3. At each epoch boundary:

   * compute `OBS_CTA_PHASE_BUCKET` from kernel CTA status and timer
   * select action primitive via the frozen table above
   * expand primitive → low-level action plan via inherited generator
4. Log per-epoch observables, actions, and legality outcomes

---

## 4) Metrics (must report per seed and aggregate)

Use the exact same metric computation and classifier as Run 0.

### 4.1 Governance outcomes (per seed)

* `authority_availability_ppm` (AA)
* `asymptotic_authority_availability_ppm` (AAA)
* `failure_class`
* `recovery_time_histogram` (RTD)
* `lapse_count`
* `total_lapse_epochs`
* `max_single_lapse_epochs`
* `epochs_evaluated`
* `epochs_in_lapse`

### 4.2 Derived diagnostics (per seed)

* `ever_ineligible`
* `ineligibility_fraction`
* `renewal_check_epochs_count`
* `renewals_succeeded`
* `renewal_success_rate_ppm`

### 4.3 CTA-phase diagnostics (per seed)

* `cta_active_epochs`
* `cta_phase_epoch_counts` (EARLY/MID/LATE)
* `primitive_counts_by_phase` (to prove the mapping executed)
* `rejection_rate_by_phase` (if rejection is tracked)
* `lapse_rate_by_phase` (descriptive)

---

## 5) Telemetry (Required)

### 5.1 Per epoch (minimum)

* `epoch`
* `rsa_enabled`
* `rsa_model`
* `OBS_CTA_PHASE_BUCKET`
* `action_primitive_emitted`
* `low_level_actions_emitted_count`
* `action_accepted` (or accepted count)
* `authority_state_end_epoch`
* `cta_active_flag_end_epoch`
* `cta_timer_value_end_epoch` (optional internal debug; must NOT be exposed to adversary)

### 5.2 Run-level

* AA / AAA
* RTD histogram
* failure_class
* phase counts
* primitive distribution per phase

---

## 6) Failure Classification (Frozen)

Use the exact classifier implemented in:

* `toy_aki/rsa/metrics.py`

No interpretation. One label per seed-run.

---

## 7) Output Format

### Script name

```
scripts/rsa_v200_run2_cta_phase_aware.py
```

### Required output blocks

1. **Run header**

   * AKI config hash
   * RSA config hash
   * horizon cycles
   * derived `horizon_epochs`
   * derived `tail_window`
   * CTA bucket boundaries (`b1`, `b2`) printed as integers

2. **Per-seed table**

   * AA_ppm, AAA_ppm, failure_class
   * lapse_count, total_lapse_epochs, max_single_lapse_epochs
   * renewal_success_rate_ppm, ineligibility_fraction, ever_ineligible
   * cta_active_epochs, cta_phase_epoch_counts
   * primitive_counts_by_phase summary

3. **Aggregate summary**

   * mean/std AA and AAA
   * class counts
   * RTD aggregate summary
   * mean/std renewal_success_rate_ppm and ineligibility_fraction
   * mean/std cta_active_epochs and lapse_rate_by_phase

---

## 8) Definition of Done (Run 2)

Run 2 is complete when:

* all seeds execute to full horizon
* per-seed metrics and failure_class are reported
* aggregate summaries are reported
* telemetry proves:

  * CTA buckets computed exactly as specified
  * action primitives chosen exactly per phase mapping
  * no other observables influenced behavior
* no AKI constitutional logic was modified

No refactors. No sweeps. No interpretation.

---

## Role of Run 2 in v2.0

Run 2 is the **CTA timing exploitation probe**.

If this run produces **Structural Thrashing**, **Terminal Collapse**, or **Irreversible Recovery Suppression**, the interpretation is direct:

> **Time-structured recovery alone leaks enough structure for a minimally adaptive adversary to defeat constitutional survivability.**
