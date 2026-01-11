# RSA v2.0 Run 4 — Renewal-Outcome Feedback (`RENEWAL_FEEDBACK`)

## Purpose

Run 4 tests whether **renewal observability**—even in a bucketed, semantics-free form—provides enough feedback for an adversary to synchronize misuse with renewal dynamics and induce **structural thrashing** or **irreversible recovery suppression**.

Run 4 exists to answer one question:

> *Can an adversary that conditions behavior on renewal outcomes (succeeded/failed/not-attempted) defeat constitutional survivability under RSA constraints?*

This is the v2.0 **renewal-coupling probe**.

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
* Renewal outcome bucket definitions (must match kernel event semantics; frozen)

### No independent variables

Run 4 has **no sweep axis**.
No alternative strategy maps. No alternate renewal bucketing. No parameter tuning.

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

### 1.2 RSA v2.0 config (Run 4)

```python
RSAConfig(
    rsa_enabled=True,
    rsa_model="RENEWAL_FEEDBACK",
    rsa_rng_stream="rsa_v200",          # distinct from kernel RNG
    rsa_max_internal_states=4,          # bound (Model I is stateless)
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

Model I may read **only**:

* `OBS_RENEWAL_OUTCOME`
* `OBS_EPOCH_INDEX`

No other observables may influence action selection.

### 2.2 Renewal outcome bucket implementation (binding)

At the start of epoch `t`, compute `OBS_RENEWAL_OUTCOME` from epoch `t-1`:

* `RENEWAL_SUCCEEDED` iff the kernel executed a renewal check and renewal was granted
* `RENEWAL_FAILED` iff the kernel executed a renewal check and renewal was denied
* `RENEWAL_NOT_ATTEMPTED` iff no renewal check occurred in the prior epoch

This must be derived from kernel renewal events, not inferred.

### 2.3 Internal state

Model I is **stateless**:

* `adaptive_state = 0` always
* No counters, no toggles, no memory

### 2.4 Strategy map (binding)

Action primitive selection must follow the v2.0 spec mapping:

| Renewal Outcome         | Action Primitive        |
| ----------------------- | ----------------------- |
| `RENEWAL_SUCCEEDED`     | `ACTION_MAX_RENT`       |
| `RENEWAL_FAILED`        | `ACTION_INVALID_COMMIT` |
| `RENEWAL_NOT_ATTEMPTED` | `ACTION_MIN_EFFORT`     |

---

## 3) Execution

For each seed:

1. Initialize harness with frozen AKI config and RSA v2.0 Run 4 config
2. Execute full horizon (no early termination)
3. At each epoch boundary:

   * compute `OBS_RENEWAL_OUTCOME` from prior-epoch renewal events
   * select action primitive via the frozen table above
   * expand primitive → low-level action plan via inherited generator
4. Log per-epoch renewal outcome, actions, and legality outcomes

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

### 4.3 Renewal-coupling diagnostics (per seed)

* `renewal_outcome_epoch_counts` (SUCCEEDED/FAILED/NOT_ATTEMPTED)
* `primitive_counts_by_renewal_outcome`
* `rejection_rate_by_renewal_outcome`
* `lapse_rate_by_renewal_outcome` (descriptive)
* `renewal_failure_to_lapse_latency` (optional; descriptive)

---

## 5) Telemetry (Required)

### 5.1 Per epoch (minimum)

* `epoch`
* `rsa_enabled`
* `rsa_model`
* `OBS_RENEWAL_OUTCOME`
* `action_primitive_emitted`
* `low_level_actions_emitted_count`
* `action_accepted` (or accepted count)
* `authority_state_end_epoch`
* `renewal_check_fired_end_epoch` (internal debug; must NOT be exposed as additional observable)

### 5.2 Run-level

* AA / AAA
* RTD histogram
* failure_class
* renewal outcome counts
* primitive distribution per renewal outcome

---

## 6) Failure Classification (Frozen)

Use the exact classifier implemented in:

* `toy_aki/rsa/metrics.py`

No interpretation. One label per seed-run.

---

## 7) Output Format

### Script name

```
scripts/rsa_v200_run4_renewal_feedback.py
```

### Required output blocks

1. **Run header**

   * AKI config hash
   * RSA config hash
   * horizon cycles
   * derived `horizon_epochs`
   * derived `tail_window`
   * renewal check interval printed

2. **Per-seed table**

   * AA_ppm, AAA_ppm, failure_class
   * lapse_count, total_lapse_epochs, max_single_lapse_epochs
   * renewal_success_rate_ppm, ineligibility_fraction, ever_ineligible
   * renewal_outcome_epoch_counts
   * primitive_counts_by_renewal_outcome summary

3. **Aggregate summary**

   * mean/std AA and AAA
   * class counts
   * RTD aggregate summary
   * mean/std renewal_success_rate_ppm and ineligibility_fraction
   * mean/std renewal_outcome_epoch_counts and lapse_rate_by_renewal_outcome

---

## 8) Definition of Done (Run 4)

Run 4 is complete when:

* all seeds execute to full horizon
* per-seed metrics and failure_class are reported
* aggregate summaries are reported
* telemetry proves:

  * renewal outcomes computed exactly per kernel event semantics
  * action primitives chosen exactly per renewal mapping
  * no other observables influenced behavior
* no AKI constitutional logic was modified

No refactors. No sweeps. No interpretation.

---

## Role of Run 4 in v2.0

Run 4 is the **renewal observability exploitation probe**.

If it produces **Structural Thrashing**, **Terminal Collapse**, or **Irreversible Recovery Suppression**, the conclusion is direct:

> **Renewal feedback alone leaks enough structure for a minimally adaptive adversary to defeat constitutional survivability.**
