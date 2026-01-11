# RSA v1.0 Run 3 — Fixed Timing Misuse Sweep (Model C)

## Purpose

Run 3 evaluates whether **deterministic timing patterns of compliance and violation**—without learning, adaptation, or deception—can induce **constitutional failure** under frozen RSA v1.0 assumptions.

This run answers one question only:

> *Can a fixed schedule of intermittent compliance exploit renewal-check timing, fail-streak eligibility, and succession dynamics to defeat constitutional recovery, or does the system remain bounded and recoverable?*

Run 3 tests **timing misuse**, not intent escalation.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

All of the following are **identical to Runs 0–2** and must remain unchanged:

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`)
* Eligibility rule (fail-streak; `eligible iff streak < K`)
* `eligibility_threshold_k = 3`
* `max_successive_renewals = 3`
* CTA parameters (`amnesty_interval = 10`, `amnesty_decay = 1`)
* Renewal interval and epoch definition (`renewal_check_interval = 50`)
* Horizon (`max_cycles = 300_000` → `6000` epochs)
* Tail window (`5000` epochs)
* Candidate pool composition and successor types
* Metrics, derived metrics, and failure classifier (frozen)
* Seed set (fixed)
* RSA v1.0 policy wrapper scope (applies to **all incumbents**)

### New axes introduced in Run 3

Run 3 introduces **exactly two axes**:

1. `timing_period_epochs` (period of the pattern)
2. `timing_offset_epochs` (phase/offset within period)

No other axes may be added.

---

## 1) Adversary Model Under Test

### Model C — Fixed Timing Misuse (`FIXED_RENEWAL_TIMING`)

**Definition:**

The policy follows a fixed periodic schedule:

```
SATISFY commitments iff (epoch % period) == offset
otherwise VIOLATE commitments
```

“SATISFY” means emit the full commitment trace sufficient for `SEM_PASS=True`.
“VIOLATE” means omit at least one required action so that `SEM_PASS=False`.

This policy is:

* intentional
* fixed
* deterministic
* non-adaptive
* outcome-blind

### Scope clarification (binding)

* The policy applies to **all incumbents**, including control and attack successors, across all successions.
* The only time reference permitted is **global epoch index**.

---

## 2) Configuration (Frozen Except Period/Offset)

### 2.1 AKI v0.8 config

Use the **exact same AKI config** as prior runs:

```python
ALSConfigV080(
    max_cycles=300_000,
    eligibility_threshold_k=3,
    max_successive_renewals=3,
    amnesty_interval=10,
    amnesty_decay=1,
    renewal_check_interval=50,
    cta_enabled=True,
)
```

No changes allowed.

---

### 2.2 RSA v1.0 policy config (Model C)

For each `(period, offset)` setting:

```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.FIXED_RENEWAL_TIMING,
    timing_period_epochs=PERIOD,
    timing_offset_epochs=OFFSET,
    epoch_size=als_config.renewal_check_interval,
)
```

Hard constraints:

* `period >= 1`
* `0 <= offset < period`
* No mid-run parameter changes

---

### 2.3 Seeds (fixed)

Use the **same seed battery** as Runs 0–2:

```python
seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
```

---

## 3) Preregistered Sweep Grid (Frozen)

Use exactly this grid (from v1.0 preregistration):

```
(period, offset) ∈ {
  (1,0),
  (2,0),
  (3,0), (3,1),
  (4,0),
  (5,0), (5,2)
}
```

Total runs:

```
7 settings × 5 seeds per setting = 35 runs
```

### Seeds for Run 3 (frozen subset)

Use exactly:

```python
seeds_run3 = [42, 137, 512, 2048, 8192]
```

No other seeds.

---

## 4) Execution

For each `(period, offset)` in the preregistered grid:

1. Loop over the 5 Run 3 seeds
2. Instantiate `ALSHarnessV080(seed, als_config, rsa_policy_config)`
3. Execute the **full horizon** (no early termination)
4. Record per-epoch telemetry and run-level summaries

Runs must be independent; do not reuse harness state.

---

## 5) Metrics (Required, Per Seed)

Run 3 must report **all metrics used in Runs 0–2**, unchanged.

### 5.1 Governance outcomes

Per seed:

* `authority_availability_ppm` (AA)
* `asymptotic_authority_availability_ppm` (AAA)
* `failure_class`
* `lapse_count`
* `total_lapse_epochs`
* `max_single_lapse_epochs`
* `recovery_time_histogram` (RTD)

---

### 5.2 Renewal diagnostics (critical for Run 3)

Per seed:

* `renewal_check_epochs_count`
* `renewals_succeeded`
* `renewal_success_rate_ppm`
* `expiration_reason_counts`
  (expected dominant reason: `max_successive_renewals`, but do not assume)
* **(optional but recommended)** `renewal_checks_during_ineligibility_count`

---

### 5.3 Global semantic diagnostics (diagnostic only)

Per seed:

* `max_consecutive_sem_fail`
* `ever_global_semfail_ge_k`
* `global_semfail_ge_k_fraction`

---

### 5.4 Timing-pattern diagnostics (new, but purely descriptive)

Per seed:

* `period`, `offset`
* `sem_pass_rate_ppm` over full horizon
* `max_consecutive_sem_fail`
* `ever_ineligible_at_renewal_check` (if measured)

No thresholds are enforced from these diagnostics; they are interpretation aids.

---

## 6) Aggregate Summaries (Per Setting)

For each `(period, offset)` setting, compute across its 5 seeds:

* mean/min/max AA and AAA
* failure class counts
* mean lapse count, max observed lapse duration
* mean renewal success rate
* RTD aggregate summary

Then produce a **cross-setting** summary table:

* `(period, offset) → mean AAA, mean AA, mean renewal_success_rate_ppm, failure_class counts`

---

## 7) Expected Structural Behavior (Preregistered)

These are expectations, not success criteria.

Given fail-streak eligibility (`eligible iff streak < K`, K=3):

### Eligibility by period (epoch-level)

* Period 1: always pass → always eligible
* Period 2: max consecutive fails = 1 → always eligible
* Period 3: max consecutive fails = 2 → always eligible
* Period 4: max consecutive fails = 3 → enters ineligibility states
* Period 5: max consecutive fails = 4 → enters ineligibility states

### Critical interpretive note (binding)

Run 3 is primarily a **renewal-check alignment experiment**, not a pass-rate experiment.

You must report and interpret:

* `renewal_success_rate_ppm`
* vs `global_semfail_ge_k_fraction`
* vs `ineligibility_fraction` (if available)

Do not infer causality from pass-rate alone.

---

## 8) Failure Classification (Frozen)

Use the **exact same classifier** as Runs 0–2:

* Stable Authority
* Bounded Degradation
* Structural Thrashing (**Failure**)
* Asymptotic DoS (**Failure**)
* Terminal Collapse (**Failure**)
* Irreversible Recovery Suppression (**Failure**)

Emit exactly one label per run.

---

## 9) Output Format

### Script name

```
scripts/rsa_v100_run3_timing.py
```

### Required output blocks

For each `(period, offset)`:

1. **Run header**

   * period, offset
   * AKI config hash
   * policy config hash
   * horizon cycles/epochs, tail window
   * seed list (5 seeds)

2. **Per-seed table**

   * AA_ppm, AAA_ppm, failure_class
   * lapse_count, max_single_lapse_epochs
   * renewal_success_rate_ppm

3. **Aggregate summary**

   * mean/min/max AA and AAA
   * failure class counts
   * RTD summary
   * renewal diagnostics summary

4. **Cross-setting summary table**

   * one row per (period, offset)

---

## 10) Stop Conditions (Hard)

If any run produces:

* Terminal Collapse
* Structural Thrashing
* Asymptotic DoS
* Irreversible Recovery Suppression

you must:

1. Record the result
2. Finish the remaining settings and seeds
3. Do not modify configuration
4. Do not reinterpret criteria

Run 3 does **not** stop early.

---

## 11) Definition of Done (Run 3)

Run 3 is complete when:

* All 35 runs execute to full horizon
* Per-seed metrics are recorded for each (period, offset)
* Per-setting summaries are produced
* Cross-setting summary table is produced
* Failure classes assigned without reinterpretation
* Outputs written to disk with timestamps
* No configuration drift from Runs 0–2 is detected

---

## Role of Run 3 in v1.0

Run 3 is the **first real attempt** to exploit the system *without adaptation*:

> *Can a fixed schedule of intermittent compliance create systematic renewal failures or lapse dominance via timing alignment?*

Only after Run 3 is frozen may you proceed to Run 4/5 or revise the v1.x conclusion.

