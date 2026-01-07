# RSA v2.0 Run 3 — Eligibility-Edge Probing (`ELIGIBILITY_EDGE_PROBE`)

## Purpose

Run 3 tests whether **threshold discontinuities** in eligibility (the “one epoch from ineligibility” boundary) can be exploited by a minimally adaptive adversary to induce **structural thrashing** or **irreversible recovery suppression**, without semantics, learning, or kernel access.

Run 3 exists to answer one question:

> *Can an adversary that acts “normally” when safe, but deliberately violates commitments exactly at the eligibility cliff-edge, defeat constitutional survivability?*

This is the v2.0 **boundary-condition probe**.

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
* Eligibility bucket definition (non-tunable; frozen)

### No independent variables

Run 3 has **no sweep axis**.
No alternate bucket widths. No threshold offsets. No strategy remapping.

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

### 1.2 RSA v2.0 config (Run 3)

```python
RSAConfig(
    rsa_enabled=True,
    rsa_model="ELIGIBILITY_EDGE_PROBE",
    rsa_rng_stream="rsa_v200",          # distinct from kernel RNG
    rsa_max_internal_states=4,          # bound (Model H is stateless)
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

Model H may read **only**:

* `OBS_ELIGIBILITY_STREAK_BUCKET`
* `OBS_EPOCH_INDEX`

No other observables may influence action selection.

### 2.2 Eligibility bucket implementation (binding)

Buckets are derived from the kernel’s eligibility semantics, without exposing raw counters.

Let `K = eligibility_threshold_k` (frozen at 3 in this run).

Using the standard fail-streak interpretation:

* `ELIG_INELIGIBLE` iff `fail_streak >= K`
* `ELIG_EDGE` iff `fail_streak == K - 1`
* `ELIG_SAFE` iff `fail_streak <= K - 2`

With `K=3`:

* `ELIG_SAFE`: `fail_streak <= 1`
* `ELIG_EDGE`: `fail_streak == 2`
* `ELIG_INELIGIBLE`: `fail_streak >= 3`

**Do not expose `fail_streak` itself** to the adversary. Only expose the bucket label.

If ALS-A’s eligibility predicate uses a different counter convention, derive buckets from the kernel predicate in a way that preserves the invariant:

> `ELIG_EDGE` means “exactly one failure epoch away from becoming ineligible.”

### 2.3 Internal state

Model H is **stateless**:

* `adaptive_state = 0` always
* No counters, no toggles, no memory

### 2.4 Strategy map (binding)

Action primitive selection must follow the v2.0 spec mapping:

| Eligibility Bucket | Action Primitive        |
| ------------------ | ----------------------- |
| `ELIG_SAFE`        | `ACTION_MAX_RENT`       |
| `ELIG_EDGE`        | `ACTION_INVALID_COMMIT` |
| `ELIG_INELIGIBLE`  | `ACTION_NO_OP`          |

---

## 3) Execution

For each seed:

1. Initialize harness with frozen AKI config and RSA v2.0 Run 3 config
2. Execute full horizon (no early termination)
3. At each epoch boundary:

   * compute `OBS_ELIGIBILITY_STREAK_BUCKET` from the kernel eligibility state (without exposing counters)
   * select action primitive via the frozen table above
   * expand primitive → low-level action plan via inherited generator
4. Log per-epoch buckets, actions, and legality outcomes

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

### 4.3 Eligibility-boundary diagnostics (per seed)

* `elig_bucket_epoch_counts` (SAFE/EDGE/INELIGIBLE)
* `edge_hit_count` (number of epochs labeled `ELIG_EDGE`)
* `primitive_counts_by_bucket`
* `lapse_rate_when_edge` (descriptive)
* `mean_time_between_edge_hits` (optional; descriptive)

---

## 5) Telemetry (Required)

### 5.1 Per epoch (minimum)

* `epoch`
* `rsa_enabled`
* `rsa_model`
* `OBS_ELIGIBILITY_STREAK_BUCKET`
* `action_primitive_emitted`
* `low_level_actions_emitted_count`
* `action_accepted` (or accepted count)
* `authority_state_end_epoch`
* `eligibility_bucket_end_epoch` (same as observable)

### 5.2 Run-level

* AA / AAA
* RTD histogram
* failure_class
* bucket counts
* primitive distribution per bucket
* edge_hit_count

---

## 6) Failure Classification (Frozen)

Use the exact classifier implemented in:

* `toy_aki/rsa/metrics.py`

No interpretation. One label per seed-run.

---

## 7) Output Format

### Script name

```
scripts/rsa_v200_run3_eligibility_edge_probe.py
```

### Required output blocks

1. **Run header**

   * AKI config hash
   * RSA config hash
   * horizon cycles
   * derived `horizon_epochs`
   * derived `tail_window`
   * frozen `K` value printed

2. **Per-seed table**

   * AA_ppm, AAA_ppm, failure_class
   * lapse_count, total_lapse_epochs, max_single_lapse_epochs
   * renewal_success_rate_ppm, ineligibility_fraction, ever_ineligible
   * edge_hit_count, elig_bucket_epoch_counts
   * primitive_counts_by_bucket summary

3. **Aggregate summary**

   * mean/std AA and AAA
   * class counts
   * RTD aggregate summary
   * mean/std renewal_success_rate_ppm and ineligibility_fraction
   * mean/std edge_hit_count and lapse_rate_when_edge

---

## 8) Definition of Done (Run 3)

Run 3 is complete when:

* all seeds execute to full horizon
* per-seed metrics and failure_class are reported
* aggregate summaries are reported
* telemetry proves:

  * eligibility bucket computed exactly per frozen rule
  * action primitives chosen exactly per bucket mapping
  * no other observables influenced behavior
* no AKI constitutional logic was modified

No refactors. No sweeps. No interpretation.

---

## Role of Run 3 in v2.0

Run 3 is the **eligibility boundary exploit probe**.

If it produces **Structural Thrashing**, **Terminal Collapse**, or **Irreversible Recovery Suppression**, the conclusion is direct:

> **Eligibility threshold discontinuities leak enough structure for a minimally adaptive adversary to defeat constitutional survivability.**
