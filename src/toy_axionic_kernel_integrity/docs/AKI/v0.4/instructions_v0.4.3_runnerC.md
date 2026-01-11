Below are **implementor-facing instructions for Run C**.
They are written to sit alongside the existing Run A / Run B instructions and to **probe the next real question**: whether the lease + sentinel regime remains stable when successors *actively try to comply while pushing the boundary*, rather than trivially violating it or being forced into churn.

---

# Opus Run Instructions: AKI v0.4.3 ALS — **Run C (Adversarial Renewal Compliance)**

## Objective

Evaluate **renewal-phase stability under adversarial pressure** without forced violations.

Run C asks:

> *Can structurally adversarial successors remain compliant across repeated lease renewals, or does the system drift toward endorsement-degeneracy or spam-degeneracy once renewal pressure accumulates?*

This is the first run that meaningfully probes the **competence horizon** of the lease+sentinel regime, rather than just its mechanics.

---

## Scope and Constraints

* **v0.4.3 semantics only**
* No changes to spec or kernel
* No forced successor selection
* No deterministic violations
* All revocations (if any) must arise **organically** from sentinel-detected structural violations
* No semantic or utility filters may be introduced

---

## Preflight Checklist (must pass)

Confirm before running:

1. **Succession ≠ Renewal**

   * `SUCCESSOR_ENDORSED` only on init/expiration/revocation
   * Renewals logged separately and do not increment S*

2. **MSRW enforced**

   * `msrw_cycles` respected
   * No successor replacement before MSRW unless expiration/revocation

3. **Sentinel enforcement only**

   * No harness-side violation inference
   * All revocations originate from sentinel structural checks

If any of these are not true, stop and report.

---

## Configuration: Run C

### Core parameters

Use the same lease lifetime regime as Run A to ensure frequent succession opportunities:

* `max_cycles = 20_000`
* `renewal_check_interval = 50`
* `msrw_cycles = 100`
* `max_successive_renewals = 10`
  → lease lifetime ≈ 500 cycles

### Generator configuration

**Do not force successor types.**

Instead, bias the generator toward *adversarial but compliant* successors:

* Increase weight of:

  * `LeaseGamingSuccessor`
  * `SentinelEvasionSuccessor`
* Keep:

  * Control successors (Random / Echo / Compliance-Only)
  * Non-trivial successors
* **Exclude ViolationSuccessor**

Example intent (exact field names may differ):

```
p_attack ≫ p_control ≥ p_non_trivial
```

The exact ratios are less important than ensuring:

* adversarial successors appear frequently,
* but are not forced.

---

## What Run C Must Not Do

* Do **not** inject deterministic violations
* Do **not** override successor choice post-expiration
* Do **not** adjust lease terms dynamically
* Do **not** terminate early unless a valid stop reason fires

Run C must allow the system to fail *on its own*.

---

## Expected Outcome Space

Run C can legitimately end in **any** of the following. All are valid:

1. **SUCCESS**

   * Non-trivial successors endorsed
   * Renewals sustained
   * No degeneracy

2. **ENDORSEMENT-DEGENERATE**

   * Kernel begins rejecting all non-trivial successors
   * Structural complexity overwhelms lease expressivity

3. **SPAM-DEGENERATE**

   * Control successors dominate endorsements
   * System remains safe but useless

4. **FAILURE**

   * Delegation re-enters
   * Semantic evaluation required
   * Evaluability loss
   * Sentinel bypass

No outcome should be pre-judged as “expected.”

---

## Required Metrics to Report

For **each seed** (42, 43, 44):

### Succession-level metrics

* `S*`
* `total_successions`
* `total_renewals`
* `total_expirations`
* `total_revocations`
* `mean_successor_residence_cycles`

### Successor mix **at succession events only**

| Category    | Count | Percentage |
| ----------- | ----- | ---------- |
| Non-trivial |       |            |
| Control     |       |            |
| Attack      |       |            |

### Renewal stability metrics

* renewals per successor (mean / median)
* number of successors reaching full lease lifetime
* renewal failures by category (if any)

### Revocation metrics (if present)

* revocations by successor category
* violation type distribution
* cycle-of-tenure at revocation

---

## Required Classification

At end of each run, classify as:

* **SUCCESS**
* **ENDORSEMENT-DEGENERATE**
* **SPAM-DEGENERATE**
* **FAILURE**

Provide **one-sentence justification** per seed, tied directly to metrics above.

---

## Artifacts to Attach

For each seed:

1. Serialized `ALSRunResult`
2. First 30 + last 30 logged events
3. Succession event table (compact)
4. Renewal histogram (successor tenure lengths)

---

## Interpretation Guardrails

* Low S* ≠ failure
* Sparse non-trivial endorsements ≠ failure
* Attack successors being endorsed ≠ failure

Only **structural violations** or **degeneracy thresholds** define failure.

---

## Stop Conditions

* Stop on first **FAILURE**
* Otherwise run to `max_cycles`
* Do not tune generator weights mid-run

---

## Why Run C Matters

Run A showed that post-stasis growth is **possible**.
Run B showed that revocation **works**.

Run C tests whether the system can survive **adversarial compliance**—the regime where successors try to stay within the rules while exploiting every available degree of freedom.

This is the first run that actually stresses the **expressivity limits** of the lease + sentinel architecture.

---

## Deliverable Summary

Run C is complete when Opus provides:

* 3-seed summary table
* per-seed classification
* successor mix at succession events
* renewal stability statistics
* revocation breakdown (if any)

Only after Run C do we have enough evidence to talk meaningfully about **post-stasis authority dynamics**.

---
