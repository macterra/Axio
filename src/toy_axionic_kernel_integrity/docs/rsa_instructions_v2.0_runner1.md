# RSA v2.0 Run 1 — Binary Outcome Adaptation (`OUTCOME_TOGGLE`)

## Purpose

Run 1 is the **minimal adaptation** stress test for RSA v2.0.

It introduces the smallest possible feedback loop:

> *A 1-bit internal state that toggles policy based only on whether the prior epoch ended in lapse.*

Run 1 exists to answer one question:

> *Is **one-bit, one-signal** outcome reactivity sufficient to induce irreversible constitutional failure while liveness is preserved?*

This is the v2.0 “adaptation control group”: if this breaks survivability, the boundary moved earlier than expected.

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

### No independent variables

Run 1 has **no sweep axis**.
No parameter tuning. No bucket tweaks. No alternate mappings.

---

## 1) Configuration (Frozen)

### 1.1 AKI v0.8 config (verbatim)

Use the same AKI config as Run 0 and all other v2.0 runs.

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

### 1.2 RSA v2.0 config (Run 1)

Run with RSA enabled and the Run 1 model selected.

```python
RSAConfig(
    rsa_enabled=True,
    rsa_model="OUTCOME_TOGGLE",
    rsa_rng_stream="rsa_v200",          # must be distinct from kernel RNG
    rsa_max_internal_states=4,          # bound (Model F uses 2 states)
    rsa_toggle_on_lapse=True,           # binding for OUTCOME_TOGGLE
    rsa_invalid_target_key="C0",        # fixed; inherited primitive generator target
)
```

Hard constraints:

* No mid-run config edits
* No per-seed config edits
* No extra observables
* No modification to primitive generators beyond v1.0 definitions

---

### 1.3 Seeds (fixed)

Use the same seed battery as all other v2.0 runs:

```python
seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
```

---

## 2) Model Definition (Frozen)

### 2.1 Observable dependency

Model F may read **only**:

* `OBS_LAPSE_OCCURRED`
* `OBS_AUTHORITY_STATUS` (optional; see below)
* `OBS_EPOCH_INDEX`

No other observables may influence state transitions or action selection.

### 2.2 Internal state

* 1-bit `adaptive_state ∈ {0,1}`
* Reset to 0 at **run start**
* Persists across successions, lapses, and CTA phases

### 2.3 State update rule (binding)

At the start of epoch `t` (using outcomes from epoch `t-1`):

```
if OBS_LAPSE_OCCURRED == True:
    adaptive_state = 1 - adaptive_state   # toggle
else:
    adaptive_state = adaptive_state
```

No other transition rules.

### 2.4 Strategy map (binding)

Action primitive selection must follow the v2.0 spec mapping:

| Condition (based on prior epoch) | Action Primitive        |
| -------------------------------- | ----------------------- |
| `OBS_LAPSE_OCCURRED == True`     | `ACTION_INVALID_COMMIT` |
| otherwise                        | `ACTION_MAX_RENT`       |

> Note: Some earlier text referenced “authority persisted.” For Run 1, implement exactly the above: lapse toggles; no lapse emits MAX_RENT.

---

## 3) Execution

For each seed:

1. Initialize harness with frozen AKI config and RSA v2.0 Run 1 config
2. Set `adaptive_state = 0`
3. Execute full horizon (no early termination)
4. Log per-epoch observables, state, actions, and legality results

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

### 4.3 Adaptation diagnostics (per seed)

* `toggle_count` (number of times `adaptive_state` flips)
* `action_counts_by_primitive` (INVALID_COMMIT vs MAX_RENT)
* `rejection_rate_by_primitive`
* `mean_run_length_in_state` (optional; descriptive)

---

## 5) Telemetry (Required)

### 5.1 Per epoch (minimum)

* `epoch`
* `rsa_enabled`
* `rsa_model`
* `OBS_LAPSE_OCCURRED`
* `OBS_AUTHORITY_STATUS`
* `adaptive_state_before`
* `adaptive_state_after`
* `action_primitive_emitted`
* `low_level_actions_emitted_count`
* `action_accepted` (or accepted count)
* `authority_state_end_epoch`

### 5.2 Run-level

* AA / AAA
* RTD histogram
* failure_class
* toggle_count
* primitive distribution + rejection rates

---

## 6) Failure Classification (Frozen)

Use the exact classifier implemented in:

* `toy_aki/rsa/metrics.py`

No interpretation. One label per seed-run.

---

## 7) Output Format

### Script name

```
scripts/rsa_v200_run1_outcome_toggle.py
```

### Required output blocks

1. **Run header**

   * AKI config hash
   * RSA config hash
   * horizon cycles
   * derived `horizon_epochs`
   * derived `tail_window`

2. **Per-seed table**

   * AA_ppm, AAA_ppm, failure_class
   * lapse_count, total_lapse_epochs, max_single_lapse_epochs
   * renewal_success_rate_ppm, ineligibility_fraction, ever_ineligible
   * toggle_count, invalid_commit_rate, max_rent_rate

3. **Aggregate summary**

   * mean/std AA and AAA
   * class counts
   * RTD aggregate summary
   * mean/std renewal_success_rate_ppm and ineligibility_fraction
   * mean/std toggle_count and rejection rates

---

## 8) Definition of Done (Run 1)

Run 1 is complete when:

* all seeds execute to full horizon
* per-seed metrics and failure_class are reported
* aggregate summaries are reported
* telemetry proves:

  * toggling occurred only on lapse outcomes
  * no other observables influenced behavior
  * action primitives were emitted as specified
* no AKI constitutional logic was modified

No refactors. No sweeps. No interpretation.

---

## Role of Run 1 in v2.0

Run 1 is the **minimal adaptive adversary**.
If this breaks survivability, the conclusion is not subtle:

> **Outcome-conditioned behavior alone is sufficient to defeat constitutional recovery under RSA assumptions.**
