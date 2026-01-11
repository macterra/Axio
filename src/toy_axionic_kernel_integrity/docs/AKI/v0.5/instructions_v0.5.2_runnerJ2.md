# Opus Run Instructions: AKI v0.5.2 ALS-E — **Run J2 (Renewal-Timing Sensitivity Test)**

## Goal

Determine whether the **expressivity-rent boundary identified in Run J** is **intrinsic** or **dependent on renewal-timing geometry**.

Run J2 answers:

> *Does shifting the renewal check earlier or later—while holding rent, workload, and renewal cost constant—shift or eliminate the observed stasis–collapse boundary?*

This run is **type-checking**, not exploratory.

---

## Scope (Binding)

### In scope

* Competitive successor selection (mixed generator)
* Expressivity tiers enforced by lease interface
* Rent charged as step-budget deduction
* Renewal consumes successor budget
* Forced succession (`max_successive_renewals`)
* **Escalation of renewal-check timing only**

### Out of scope

* Any semantic objectives or task utility
* Changes to rent schedule
* Changes to renewal cost
* Changes to expressivity tier
* Multi-axis tuning
* Detector changes

If any out-of-scope change occurs, **abort the run**.

---

## Shared Preconditions (Must Hold)

All Run J invariants apply unchanged unless explicitly overridden:

1. Rent charged at epoch start.
2. Renewal consumes successor budget.
3. E-Class for rent = active successor’s lease tier.
4. ViolationSuccessor excluded.
5. Mixed generator + TierFilterGenerator post-filtering.
6. Forced succession enabled.

Violation of any invariant invalidates the run.

---

## Shared Configuration (All J2 Runs)

### Core parameters (unchanged from Run J)

* `epoch_size = 100 cycles`
* `steps_cap_epoch = 200`
* `actions_cap_epoch = 100`
* `msrw_cycles = 200`
* `renewal_cost = 5`
* `max_successive_renewals = 15`
* `reject_immediate_bankruptcy = False`

### Expressivity / Rent (fixed)

* Fixed expressivity tier: **E3**
* **E3 rent = 96** (48%)
  → `effective_steps = 104`

Rationale: this is the **exact collapse point** from Run J.

### Generator

* Mixed generator
* CBD successors included
* TierFilterGenerator applied post-generation
* Max retries per succession = 200
* Attack weights: `V052_RUNG_G2_ATTACK_WEIGHTS`

---

## Experimental Axis

**Single varied parameter:** `renewal_check_interval`

All other parameters remain identical across sub-runs.

---

## Run J2 Structure

Run J2 consists of **three independent sub-runs**, each with a different renewal-check timing.

You must **not** combine these sub-runs.

---

## J2 Sub-Runs — Renewal Timing Variants

### J2-Early — Early Renewal Check

* `renewal_check_interval = 50`
* Renewal evaluated halfway through epoch
* Typical usage to check ≈ 50 steps

---

### J2-Baseline — Control (Reference)

* `renewal_check_interval = 100`
* Identical to Run J collapse geometry
* Typical usage to check ≈ 100 steps

(This sub-run exists only for direct comparability.)

---

### J2-Late — Late Renewal Check

* `renewal_check_interval = 150`
* Renewal evaluated after most of epoch budget is consumed
* Typical usage to check ≈ 150 steps

---

## Horizon

* `H = 30,000 cycles`

Same as Run J to preserve comparability.

---

## Seeds

* 40, 41, 42, 43, 44

---

## Stop Rules (Binding)

Terminate a seed on first occurrence of:

1. **Renewal failure** (budget infeasibility)
2. **Bankruptcy**
3. **Revocation**
4. **Degeneracy detector trigger**
5. **Horizon exhaustion**

Stop reason must be recorded explicitly.

---

## Required Telemetry (Binding)

For each `(sub-run, seed)`:

### A) Renewal Geometry

* `renewal_check_interval`
* `steps_used_at_check` (min/mean)
* `remaining_budget_at_check` (min/mean)
* `renewal_cost`

### B) Renewal Outcomes

* `renewal_attempts`
* `renewal_successes`
* `renewal_success_rate`
* `time_to_first_failure` (if any)

### C) Lifecycle & Termination

* `terminal_stop_reason`
* bankruptcy events
* renewal-fail events
* revocations

### D) Regime Classification Inputs

* renewal rate over time
* manifest diversity proxy (as in Run J)
* degeneracy detector status

---

## Post-hoc Regime Classification (Required)

Use the **same regime definitions as Run J**:

* `METASTABLE_STASIS`
* `RENEWAL_COLLAPSE`
* `GROWTH` (if applicable)

Detector (`SPAM_DEGENERACY`) remains the terminal instrument.

---

## Required Reporting

### Summary Table (Mandatory)

| Sub-Run | Renewal Interval | Eff. Steps | Mean Renew Rate | Dominant Regime | Terminal Cause |
| ------- | ---------------- | ---------- | --------------- | --------------- | -------------- |

### Geometry Table (Mandatory)

| Sub-Run | Steps at Check | Remaining | Renewal Cost | Outcome |
| ------- | -------------- | --------- | ------------ | ------- |

### One Conservative Interpretation Paragraph per Sub-Run

Must state:

* timing geometry tested
* whether collapse boundary shifted, persisted, or disappeared
* what cannot be concluded

---

## Interpretation Constraints (Binding)

You **may** conclude:

* Whether the collapse boundary shifts with renewal timing
* Whether expressivity rent is dominant or geometry-dependent

You **may not** conclude:

* General safety properties
* Cross-tier generality
* Effects of audit friction or workload changes

---

## Classification Rules

Run J2 is **informative** if **any** occurs:

* Boundary shifts upward/downward with timing
* Boundary remains fixed across timings
* Collapse disappears entirely at early renewal

Run J2 is a **failure** only if:

* renewal checks are mis-timed,
* rent or renewal cost differs from spec,
* detector configuration changes,
* forced succession is disabled.

---

## Orientation

Run J established a **rent-driven cliff** under fixed timing.

Run J2 determines whether that cliff is:

* a **fundamental economic boundary**, or
* a **consequence of renewal-timing geometry**.

Proceed exactly as specified.
