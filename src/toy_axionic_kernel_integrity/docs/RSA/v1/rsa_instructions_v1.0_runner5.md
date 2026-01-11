# RSA v1.0 Run 5 — Compound Misuse Sweep (Model E)

## Purpose

Run 5 evaluates whether a **compound fixed strategy**—combining **intermittent compliance** with **continuous eligibility pressure**—can induce **constitutional failure** under frozen RSA v1.0 assumptions.

This run answers one question only:

> *Do combinations of non-adaptive misuse behaviors expose failure modes not found in the single-strategy runs (Runs 1–4), or does governance remain bounded and recoverable?*

Run 5 is the **final v1.0 stress run**. It must not introduce learning, adaptation, or run-history conditioning.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

All of the following are **identical to Runs 0–4** and must remain unchanged:

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

### New axis introduced in Run 5

Run 5 introduces **no new parameter axes** beyond those already preregistered in Run 3.

Run 5 is a **compound test** executed over a **fixed preregistered grid** of timing patterns.

---

## 1) Adversary Model Under Test

### Model E — Compound Misuse (`LAZY_DICTATOR`)

**Definition (v1.0 compound):**

Model E combines:

1. **Minimal compliance trace** when choosing to satisfy (same as Run 2)
2. **Deterministic timing schedule** of satisfy vs violate (same schedule form as Run 3)

Operationally, Model E behaves exactly like Model C with a fixed violate action (WAIT-only) and satisfy action (*full_commitment_sequence*), but is treated as a distinct model because it represents the “lazy dictator” archetype:

> **Comply only when scheduled; otherwise do nothing; remain within constitutional rules; no adaptation.**

This policy is:

* intentional
* fixed
* deterministic
* non-adaptive
* outcome-blind

### Scope clarification (binding)

* Applies to **all incumbents** across all successions
* Uses **global epoch index** only
* No dependence on renewal outcomes, lapse history, or authority state

---

## 2) Configuration (Frozen Except Timing Pattern)

### 2.1 AKI v0.8 config

Use the **exact same AKI config** as Runs 0–4:

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

### 2.2 RSA v1.0 policy config (Model E)

For each `(period, offset)` setting:

```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.LAZY_DICTATOR,
    timing_period_epochs=PERIOD,
    timing_offset_epochs=OFFSET,
    epoch_size=als_config.renewal_check_interval,
)
```

Hard constraints:

* `period >= 1`
* `0 <= offset < period`
* No mid-run edits

---

### 2.3 Seeds (fixed)

Use the **same Run 3 seed subset** to preserve comparability:

```python
seeds_run5 = [42, 137, 512, 2048, 8192]
```

---

## 3) Preregistered Sweep Grid (Frozen)

Run 5 uses the **same preregistered timing grid as Run 3**, unchanged:

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
7 settings × 5 seeds = 35 runs
```

---

## 4) Execution

For each `(period, offset)` in the grid:

1. Loop over the 5 seeds
2. Instantiate `ALSHarnessV080(seed, als_config, rsa_policy_config)`
3. Execute the **full horizon** (no early termination)
4. Record per-epoch telemetry and run-level summaries

Runs must be independent; do not reuse harness state.

---

## 5) Metrics (Required, Per Seed)

Run 5 must report **all metrics used in Runs 0–4**, unchanged.

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

### 5.2 Renewal diagnostics (critical for compound behavior)

Per seed:

* `renewal_check_epochs_count`
* `renewals_succeeded`
* `renewal_success_rate_ppm`
* `expiration_reason_counts`

---

### 5.3 Semantic and timing diagnostics

Per seed:

* `sem_pass_rate_ppm`
* `max_consecutive_sem_fail`
* `ever_global_semfail_ge_k`
* `global_semfail_ge_k_fraction`

---

### 5.4 Compound diagnostics (new, purely descriptive)

Per seed:

* `period`, `offset`
* `satisfy_epochs_count`
* `violate_epochs_count`
* `max_consecutive_violate_epochs`

These must be derived from the schedule, not from state.

---

## 6) Aggregate Summaries (Per Setting)

For each `(period, offset)` setting (across its 5 seeds):

* mean/min/max AA and AAA
* failure class counts
* mean lapse count, max observed lapse duration
* mean renewal success rate
* RTD aggregate summary

Then generate a **cross-setting summary table** analogous to Run 3:

* `(period, offset) → mean AA, mean AAA, mean renewal_success_rate_ppm, sem_pass_rate_ppm, max_consecutive_sem_fail, lapse_count, failure class counts`

---

## 7) Expected Structural Behavior (Preregistered)

These are expectations, not success criteria.

Given Model E’s operational equivalence to “schedule-driven compliance”:

* If LAZY_DICTATOR uses the same satisfy/violate schedule as Model C,
  then Run 5 should closely match Run 3 results for the same grid.

In particular:

* period 1–3: STABLE_AUTHORITY
* period 4: transition (minor lapses possible)
* period 5: BOUNDED_DEGRADATION

Any deviation is interesting and must be reported without reinterpretation.

---

## 8) Failure Classification (Frozen)

Use the **exact same classifier** as Runs 0–4:

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
scripts/rsa_v100_run5_lazy_dictator.py
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
   * sem_pass_rate_ppm, max_consecutive_sem_fail

3. **Aggregate summary**

   * mean/min/max AA and AAA
   * failure class counts
   * RTD summary
   * renewal + semantic diagnostics summary

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
2. Finish remaining settings and seeds
3. Do not modify configuration
4. Do not reinterpret criteria

Run 5 does **not** stop early.

---

## 11) Definition of Done (Run 5)

Run 5 is complete when:

* All 35 runs execute to full horizon
* Per-seed metrics recorded for each (period, offset)
* Per-setting summaries produced
* Cross-setting summary table produced
* Failure classes assigned without reinterpretation
* Outputs written to disk with timestamps
* No configuration drift from Runs 0–4 is detected

---

## Role of Run 5 in v1.0

Run 5 is the final v1.0 closure attempt:

> **If compound fixed strategies still cannot induce constitutional failure, then intentional non-adaptive misuse is insufficient and v1.x is closed.**

Only after Run 5 is frozen may you write the v1.x closure statement or transition to v2.0.
