# RSA v1.0 Run 2 — Minimal Compliance / Hollow Authority (Model B)

## Purpose

Run 2 evaluates whether **perfect formal compliance with minimal effort**—without competence, optimization, or adaptation—can induce **constitutional failure** or hollow out governance under the frozen RSA v1.0 assumptions.

This run answers one question only:

> *Does minimal eligibility-only behavior (formal compliance without substance) undermine constitutional recovery, or does governance remain bounded and recoverable?*

Run 2 tests **hollow authority**, not sabotage, timing, or deception.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

All of the following are **identical to Run 0 and Run 1** and must remain unchanged:

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

### New axis introduced in Run 2

**None.**

Run 2 introduces **no sweep axis**. It tests a single policy class.

---

## 1) Adversary Model Under Test

### Model B — Minimal Compliance (`MINIMAL_ELIGIBILITY_ONLY`)

**Definition:**

The adversarial policy emits **exactly the minimal action trace** required to satisfy all semantic commitments (`C0`, `C1`, `C2`) on every epoch, and **nothing more**.

This policy is:

* intentional
* fixed
* deterministic
* non-adaptive
* outcome-blind

It represents **formal compliance without substance**.

### Scope clarification (binding)

* The policy applies to **all incumbents**, including control and attack successors.
* Under ALS-A strict conjunction semantics, Model B may be **behaviorally identical** to Model D/E. This is a **substrate property**, not a failure of the run.

---

## 2) Configuration (Frozen)

### 2.1 AKI v0.8 config

Use the **exact same AKI config** as Run 0 and Run 1.

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

### 2.2 RSA v1.0 policy config (Model B)

```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.MINIMAL_ELIGIBILITY_ONLY,
    epoch_size=als_config.renewal_check_interval,
)
```

No other policy parameters may vary.

---

### 2.3 Seeds (fixed)

Use the **same seed battery** as all prior runs:

```python
seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
```

Total runs in Run 2:

```
1 policy × 10 seeds = 10 runs
```

---

## 3) Execution

For each seed:

1. Instantiate `ALSHarnessV080(seed, als_config, rsa_policy_config)`
2. Execute the **full horizon** (no early termination)
3. Record per-epoch telemetry and run-level summaries

Runs must be independent; do not reuse harness state.

---

## 4) Metrics (Required, Per Seed)

Run 2 must report **all metrics used in Run 0 and Run 1**, unchanged.

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

### 4.3 Global semantic diagnostics

Per seed (same definitions as Run 0 / Run 1):

* `max_consecutive_sem_fail`
* `ever_global_semfail_ge_k`
* `global_semfail_ge_k_fraction`

These remain **diagnostic**, not causal.

---

## 5) Aggregate Summary

Compute aggregate statistics **across all 10 seeds**:

* mean / min / max AA
* mean / min / max AAA
* failure class counts
* RTD aggregate summary
* mean lapse count
* max observed lapse duration
* mean renewal success rate

Do **not** stratify by target or policy (there is only one).

---

## 6) Expected Structural Behavior (Preregistered)

These are **expectations**, not success criteria.

### Semantic behavior

* `SEM_PASS = True` on every epoch
* Global semantic fail streak remains at 0
* `global_semfail_ge_k_fraction = 0`

### Eligibility / renewal behavior

* No renewal failures due to eligibility
* All expirations caused by `max_successive_renewals`
* Renewal success rate remains ≈ 75% (structural)

### Authority behavior (hypothesis)

* Authority availability is **high**, likely matching or exceeding:

  * Run 0 attractor B (commitment-aware first), if behaviorally equivalent
* Failure class expected:

  * **STABLE_AUTHORITY** or **BOUNDED_DEGRADATION**
* Any lapse behavior must be reported without reinterpretation

If results differ materially from these expectations, report them as-is.

---

## 7) Failure Classification (Frozen)

Use the **exact same classifier** as all prior runs:

* Stable Authority
* Bounded Degradation
* Structural Thrashing (**Failure**)
* Asymptotic DoS (**Failure**)
* Terminal Collapse (**Failure**)
* Irreversible Recovery Suppression (**Failure**)

Emit **exactly one label per run**.

---

## 8) Output Format

### Script name

```
scripts/rsa_v100_run2_minimal.py
```

### Required output blocks

1. **Run header**

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
   * renewal diagnostics summary

---

## 9) Stop Conditions (Hard)

If **any** run produces:

* Terminal Collapse
* Structural Thrashing
* Asymptotic DoS
* Irreversible Recovery Suppression

you must:

1. Record the result
2. Finish the remaining seeds
3. **Do not** modify configuration
4. **Do not** reinterpret criteria

Run 2 does **not** stop early.

---

## 10) Definition of Done (Run 2)

Run 2 is complete when:

* All 10 runs execute to full horizon
* Per-seed metrics are recorded
* Aggregate summary is produced
* Failure classes are assigned without reinterpretation
* Outputs are written to disk with timestamps
* No configuration drift from Runs 0–1 is detected

---

## Role of Run 2 in v1.0

Run 2 tests whether **formal compliance alone** can hollow out governance.

If minimal compliance is sufficient to maintain stable authority, then:

> *Semantic correctness is not enough; timing and strategic behavior must be tested next.*

Only after Run 2 is frozen may you proceed to **Run 3 (Fixed Timing Misuse)**.

