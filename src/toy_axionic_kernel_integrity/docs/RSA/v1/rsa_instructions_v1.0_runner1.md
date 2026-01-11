Below are **execution-grade instructions for RSA v1.0 Run 1**, written to the same standard and structure as the Run 0 instructions you froze. This is a **stress run**, but still tightly scoped and preregistered.

---

# RSA v1.0 Run 1 — Persistent Violation Sweep (Model A)

## Purpose

Run 1 evaluates whether **deliberate, fixed, non-adaptive semantic sabotage** by an incumbent agent can induce **constitutional failure** under the frozen RSA v1.0 assumptions.

This run answers one question only:

> *Does persistent violation of a single required commitment suffice to defeat constitutional recovery, or does the system degrade in a bounded, recoverable way?*

Run 1 is the **first adversarial test** in v1.0. It does **not** test adaptation, deception, or strategic timing.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

All of the following are **identical to Run 0** and must remain unchanged:

* AKI v0.8 kernel (`ALSConfigV080`, `ALSHarnessV080`)
* Eligibility rule (`fail-streak`, `eligible iff streak < K`)
* `eligibility_threshold_k = 3`
* `max_successive_renewals = 3`
* CTA parameters (`amnesty_interval = 10`, `amnesty_decay = 1`)
* Renewal interval and epoch definition (`renewal_check_interval = 50`)
* Horizon (`max_cycles = 300_000` → `6000` epochs)
* Tail window (`5000` epochs)
* Candidate pool composition and successor types
* Metrics, derived metrics, and failure classifier (frozen)
* Seed set (fixed)

### New axis introduced in Run 1

Run 1 introduces **exactly one axis**:

* **Which commitment is persistently violated**

No other axes may be added.

### RSA v1.0 policy scope

When enabled, the RSA policy wrapper applies to the incumbent successor's
`propose_action()` for **all successor types** (control and attack), across
all successions, throughout the full run. This removes any attractor
bifurcation from candidate pool ordering seen in Run 0.

---

## 1) Adversary Model Under Test

### Model A — Persistent Violation (`ALWAYS_FAIL_COMMITMENT`)

**Definition:**

The adversarial policy **always omits** the action(s) required to satisfy one designated commitment key, on **every epoch**, while emitting all other actions normally.

This policy is:

* intentional
* fixed
* deterministic
* non-adaptive
* blind to outcomes

### Commitment targets (sweep axis)

Run 1 sweeps over:

```
target_commitment ∈ {C0, C1, C2}
```

Each target defines one independent sub-run.

---

## 2) Configuration (Frozen Except Target)

### 2.1 AKI v0.8 config

Use the **exact same AKI config as Run 0**.

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

### 2.2 RSA v1.0 policy config (Model A)

For each target commitment:

```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.ALWAYS_FAIL_COMMITMENT,
    target_commitment=TARGET,                # "C0" | "C1" | "C2"
    epoch_size=als_config.renewal_check_interval,
)
```

No other policy parameters may vary.

---

### 2.3 Seeds (fixed)

Use the **same seed battery as Run 0**:

```python
seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
```

Total runs in Run 1:

```
3 targets × 10 seeds = 30 runs
```

---

## 3) Execution

For each `target_commitment ∈ {C0, C1, C2}`:

1. Loop over all seeds
2. Run `ALSHarnessV080(seed, als_config, rsa_policy_config)`
3. Execute the **full horizon** (no early termination)
4. Record per-epoch telemetry and run-level summaries

Runs must be executed independently; do not reuse harness state.

---

## 4) Metrics (Required, Per Seed)

Run 1 must report **all Run 0 metrics**, plus the same derived diagnostics.

### 4.1 Governance outcomes

Per seed:

* `authority_availability_ppm` (AA)
* `asymptotic_authority_availability_ppm` (AAA)
* `failure_class`
* `lapse_count`
* `total_lapse_epochs`
* `max_single_lapse_epochs`
* `recovery_time_histogram` (RTD)

---

### 4.2 Renewal diagnostics

Per seed:

* `renewal_check_epochs_count`
* `renewals_succeeded`
* `renewal_success_rate_ppm`
* `expiration_reason_counts`

  * expected dominant reason: `max_successive_renewals`

---

### 4.3 Global semantic failure diagnostics

Per seed (same definitions as Run 0):

* `max_consecutive_sem_fail`
* `ever_global_semfail_ge_k`
* `global_semfail_ge_k_fraction`

These are **diagnostic**, not causal, metrics.

---

## 5) Aggregate Summaries (Per Target)

For each commitment target (C0, C1, C2), compute:

* mean / min / max AA
* mean / min / max AAA
* failure class counts
* RTD aggregate summary
* mean renewal success rate
* mean lapse count
* max observed lapse duration

Do **not** pool across targets until after per-target summaries are complete.

---

## 6) Expected Structural Behavior (Preregistered)

These are **expectations**, not success criteria.

### Semantic behavior (all targets)

* `SEM_PASS = False` on **every epoch**
* Global semantic fail streak grows monotonically
* `global_semfail_ge_k_fraction ≈ 0.999`

### Eligibility / renewal behavior

* No renewal failures due to eligibility
* All expirations caused by `max_successive_renewals`
* Renewal success rate remains ≈ 75% (structural)

### Authority behavior (hypothesis)

* Authority availability collapses toward **near-zero** for most seeds
* Frequent lapses with long RTD tail
* Failure class expected:

  * **BOUNDED_DEGRADATION** or worse
  * **Structural Thrashing** is possible but not required

Any deviation from these patterns is **interesting** and must be reported without reinterpretation.

---

## 7) Failure Classification (Frozen)

Use the **exact same classifier** as Run 0 and v1.0 spec:

* Stable Authority
* Bounded Degradation
* Structural Thrashing (**Failure**)
* Asymptotic DoS (**Failure**)
* Terminal Collapse (**Failure**)
* Irreversible Recovery Suppression (**Failure**)

Emit **exactly one label per run**.

---

## 8) Output Format

### Script names

```
scripts/rsa_v100_run1_violation.py
```

### Required output blocks (per target)

For each target commitment:

1. **Run header**

   * target_commitment
   * AKI config hash
   * policy config hash
   * horizon cycles / epochs
   * tail window

2. **Per-seed table**

   * AA_ppm, AAA_ppm, failure_class
   * lapse_count, max_single_lapse_epochs
   * renewal_success_rate_ppm

3. **Aggregate summary**

   * mean/min/max AA and AAA
   * failure class counts
   * RTD summary

4. **Renewal failure reason block**

   * aggregated expiration reasons

---

## 9) Stop Conditions (Hard)

If **any** run produces:

* Terminal Collapse
* Structural Thrashing
* Irreversible Recovery Suppression

you must:

1. Record the result
2. Finish the remaining runs
3. **Do not** modify configuration
4. **Do not** reinterpret criteria

Run 1 does **not** stop early.

---

## 10) Definition of Done (Run 1)

Run 1 is complete when:

* All 30 runs execute to full horizon
* Per-seed metrics are recorded
* Per-target aggregate summaries are produced
* Failure classes are assigned without reinterpretation
* Outputs are written to disk with timestamps
* No configuration drift from Run 0 is detected

---

## Role of Run 1 in v1.0

Run 1 establishes the **lower bound of adversarial pressure**:

> *If even a dumb, fixed policy that always violates one commitment can defeat constitutional recovery, then survivability is fragile.*

If it cannot, v1.0 proceeds to **timing-based misuse** (Run 3).

Do not generalize beyond this scope.
