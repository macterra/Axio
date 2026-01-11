# RSA v1.0 Run 4 — Blind Succession Avoidance / Entrenchment Pressure (Model D)

## Purpose

Run 4 evaluates whether **continuous eligibility maintenance**—without learning, adaptation, or deception—can induce **constitutional capture** or destabilize recovery under frozen RSA v1.0 assumptions.

This run answers one question only:

> *Can a fixed policy that always maintains eligibility and renewability produce harmful entrenchment or constitutional failure, even without semantic sabotage or timing misuse?*

Run 4 tests **entrenchment pressure**, not failure induction.

---

## 0) Binding Constraints (No New Axes)

### Frozen components (must not change)

All of the following are **identical to Runs 0–3** and must remain unchanged:

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

### New axis introduced in Run 4

**None.**

Run 4 introduces **no sweep axis**. It tests a single entrenchment policy.

---

## 1) Adversary Model Under Test

### Model D — Blind Succession Avoidance (`ALWAYS_SELF_RENEW`)

**Definition:**

The policy emits the **full commitment-satisfying action trace** on every epoch, guaranteeing:

* `SEM_PASS = True`
* fail-streak remains 0
* incumbent is always eligible at renewal checks

There is **no explicit “renew” action**; renewal is automatic under ALS-A.
The policy’s effect is to **never relinquish eligibility voluntarily**.

This policy is:

* intentional
* fixed
* deterministic
* non-adaptive
* outcome-blind

### Scope clarification (binding)

* The policy applies to **all incumbents**, including control and attack successors.
* The policy does **not** bypass `max_successive_renewals`; forced expiration still occurs.
* The policy does **not** manipulate candidate pools, renewal timing, or lapse logic.

---

## 2) Configuration (Frozen)

### 2.1 AKI v0.8 config

Use the **exact same AKI config** as Runs 0–3.

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

### 2.2 RSA v1.0 policy config (Model D)

```python
RSAPolicyConfig(
    policy_model=RSAPolicyModel.ALWAYS_SELF_RENEW,
    epoch_size=als_config.renewal_check_interval,
)
```

No other policy parameters may vary.

---

### 2.3 Seeds (fixed)

Use the **same canonical seed battery** as Runs 0–2:

```python
seeds = [42, 137, 256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
```

Total runs in Run 4:

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

Run 4 must report **all metrics used in Runs 0–3**, unchanged.

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

### 4.2 Renewal and entrenchment diagnostics (primary focus)

Per seed:

* `renewal_check_epochs_count`
* `renewals_succeeded`
* `renewal_success_rate_ppm`
* `expiration_reason_counts`
* `succession_count`
* `mean_tenure_length_epochs`
* `max_tenure_length_epochs`

These are **descriptive**, not thresholds.

---

### 4.3 Global semantic diagnostics (diagnostic only)

Per seed:

* `max_consecutive_sem_fail` (expected 0)
* `ever_global_semfail_ge_k` (expected False)
* `global_semfail_ge_k_fraction` (expected 0)

---

## 5) Aggregate Summary

Compute aggregate statistics **across all 10 seeds**:

* mean/min/max AA and AAA
* failure class counts
* mean lapse count
* max observed lapse duration
* mean renewal success rate
* mean succession count
* mean and max tenure length

---

## 6) Expected Structural Behavior (Preregistered)

These are **expectations**, not success criteria.

### Semantic and eligibility behavior

* `SEM_PASS = True` every epoch
* fail-streak remains 0
* eligibility is never the limiting factor

### Renewal behavior

* Renewal success rate ≈ 75% (structural ceiling from `max_successive_renewals`)
* All expirations caused by `max_successive_renewals`

### Authority behavior (hypothesis)

* AA and AAA near 100% (≈ Run 2)
* Failure class: **STABLE_AUTHORITY**
* Lapses: 0 or only structural initialization lapses
* Succession occurs regularly due to forced expiration, not loss of eligibility

If any deviation occurs, report it without reinterpretation.

---

## 7) Failure Classification (Frozen)

Use the **exact same classifier** as Runs 0–3:

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
scripts/rsa_v100_run4_entrenchment.py
```

### Required output blocks

1. **Run header**

   * AKI config hash
   * policy config hash
   * horizon cycles / epochs
   * tail window
   * seed list

2. **Per-seed table**

   * AA_ppm, AAA_ppm, failure_class
   * lapse_count, max_single_lapse_epochs
   * renewal_success_rate_ppm
   * succession_count, max_tenure_length_epochs

3. **Aggregate summary**

   * mean/min/max AA and AAA
   * failure class counts
   * RTD summary
   * tenure / succession diagnostics

---

## 9) Stop Conditions (Hard)

If any run produces:

* Terminal Collapse
* Structural Thrashing
* Asymptotic DoS
* Irreversible Recovery Suppression

you must:

1. Record the result
2. Finish remaining seeds
3. Do not modify configuration
4. Do not reinterpret criteria

Run 4 does **not** stop early.

---

## 10) Definition of Done (Run 4)

Run 4 is complete when:

* All 10 runs execute to full horizon
* Per-seed metrics are recorded
* Aggregate summary is produced
* Failure classes assigned without reinterpretation
* Outputs written to disk with timestamps
* No configuration drift from Runs 0–3 is detected

---

## Role of Run 4 in v1.0

Run 4 tests whether **pure entrenchment pressure**, absent sabotage or timing misuse, can hollow out or destabilize governance.

If Model D also fails to induce constitutional failure, then:

> *All fixed, non-adaptive misuse strategies are insufficient.*

Only after Run 4 is frozen may you consider Run 5 (compound misuse) or formally close v1.x and transition to v2.0 (adaptive adversaries).
