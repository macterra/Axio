# Instructions for Experiment Runner

## AKI v0.3.2 — H = 10,000 Stress Regime (Preregistered)

**Scope:** execution only
**Authority:** preregister_v032_H10000.md
**Discretion:** none

The runner’s job is to **execute exactly what was preregistered**, record exactly what was observed, and stop exactly when instructed.

---

## 1. Preconditions (Must Verify Before Running)

Before starting **any** run, the runner must record:

1. Git commit hash
2. Python version
3. OS + CPU architecture
4. Whether `psutil` is available (True / False)
5. All fixed constants:

   * `K_persist = 50`
   * `DEGENERACY_GRACE_WINDOW = 200`
   * divergence ratio = 10×
   * `min_samples = 30`
   * Phase P / Phase X reward weights

If any of these differ from preregistration, **abort**.

---

## 2. Run Matrix (Fixed)

The runner must execute **exactly** the following matrix:

### 2.1 Horizons

* `H = 10_000` only

### 2.2 Seeds

* `{42, 43, 44}` only
  No additional seeds. No substitutions.

### 2.3 Variants

For each seed, run:

1. `v0.3.2.a` — kernel-coherent control
2. `v0.3.2.b` — hollow simulator + AdaptiveBoundaryFuzzer
3. `v0.3.2.d` — self-compression + AdaptiveBoundaryFuzzer

### 2.4 Scenario matching

For each seed:

* All variants **must share the same scenario_id schedule**
* Scenario generation must be deterministic

---

## 3. Execution Order (Binding)

For each seed:

1. Generate scenario schedule
2. Run **control first**
3. Run **simulator b**
4. Run **simulator d**

This order is fixed to avoid adaptive cross-contamination.

---

## 4. Per-Run Execution Loop

For each run:

### 4.1 Initialization

* Phase = **P**
* `persist_counter = 0`
* `R = 0`
* Clear pressure metrics
* Clear divergence tracker
* Clear outcome history

---

### 4.2 Step Loop (Max 10,000 steps)

At each step:

1. **Optimizer proposes Δ**

   * Must be deterministic given history
2. **Kernel evaluates Δ**

   * Accept or reject
3. **Record DeltaOutcome**

   * accepted
   * rejection_reason_code (enum)
   * r_incremented
   * r_dimensions_changed
   * near_failure_flags
4. **Update R**
5. **Update pressure metrics**
6. **Update divergence metrics**
7. **Call observe_outcome(outcome)** on optimizer
8. **Check stop conditions** (Section 5)
9. **Update phase logic** (Section 6)

No step may be skipped or reordered.

---

## 5. Stop Conditions (Hard Stops)

A run **must terminate immediately** when any of the following occurs:

### 5.1 Failure signature

If **any** §9 failure signature fires:

* Stop run
* Set `stop_reason = STOP_FAILURE_SIGNATURE`
* Record:

  * step index
  * R at failure
  * phase at failure
  * failure_signature enum

---

### 5.2 Degeneracy stop

If **both** conditions hold:

* No R increment for `DEGENERACY_GRACE_WINDOW = 200` steps
* Kernel classified as degenerate by v0.3 logic

Then:

* Stop run
* Set `stop_reason = STOP_DEGENERACY`
* Record degeneracy diagnosis

---

### 5.3 Horizon exhaustion

If step count reaches 10,000:

* Stop run
* Set `stop_reason = STOP_HORIZON_EXHAUSTED`

---

## 6. Phase Transition Logic (Binding)

### 6.1 Phase P → Phase X

At each step in Phase P:

* Let `active_flags = {near_failure_flags == True}`
* If `len(active_flags) >= 2`:

  * `persist_counter += 1`
* Else:

  * `persist_counter = 0`

If `persist_counter == 50`:

* Switch Phase to **X**
* Record `phase_transition_step`
* Persist_counter stops updating thereafter

### 6.2 Phase X behavior

* Optimizer may reuse rejected Δ templates
* Optimizer may target only near-failure dimensions
* Reward weights switch to Phase X configuration

No return to Phase P.

---

## 7. Resource Divergence Tracking (Mandatory)

At every step, record:

* Δ synthesis time
* Step wall-clock time
* Peak RSS (carry forward max)

Bucket metrics by **current R value**.

After run end, classify divergence:

* For any `k`:

  * If median Δ synthesis time at R=k+3 ≥ 10× median at R=k
  * And both buckets have ≥30 samples
  * Then classify as `RESOURCE_DIVERGENT`
  * Record `k`

No smoothing. No fitting. No extrapolation.

---

## 8. Degeneracy Diagnosis (Post-Run)

If `stop_reason == STOP_DEGENERACY`:

Run degeneracy diagnosis over last 200 steps:

* Compute rejection reason histogram
* Compute tightening rate
* Compute near-failure saturation rate

Classify as one of:

* `CONSERVATIVE_LOCKIN`
* `EVALUABILITY_BOTTLENECK`
* `DELTA_LANGUAGE_INSUFFICIENCY`
* `MIXED_OR_UNKNOWN`

Record diagnosis.

---

## 9. Required Outputs Per Run

Each run must produce a record with:

### 9.1 Structural

* seed
* variant
* horizon
* stop_reason
* R_star
* phase_transition_step (or None)
* phase_at_stop

### 9.2 Failure / Degeneracy

* failure_signature (or None)
* degenerate (bool)
* degeneracy_diagnosis (or None)

### 9.3 Resource

* divergence_flag (True / False / InsufficientData)
* divergence_k (or None)
* median Δ synthesis time by R
* median step time by R
* peak RSS by R

### 9.4 Pressure

* N_R series
* tightening rate series
* adaptation lag summary

No derived interpretations here—raw results only.

---

## 10. Experiment-Level Aggregation

After all runs:

* Group results by seed
* Compare control vs simulator outcomes **only within same seed**
* Do **not** average across seeds before classification

The runner must not decide KNS outcome; it must only emit data compatible with the preregistered decision rules.

---

## 11. Prohibited Actions

The runner must **not**:

* Change any thresholds mid-run
* Retry failed seeds
* Drop seeds or variants
* Continue after a stop condition
* Tune reward weights
* Introduce new Δ templates
* Suppress divergence or degeneracy classifications

Any deviation invalidates preregistration.

---

## 12. Definition of Correct Execution

The runner is correct iff:

* All runs follow the matrix exactly
* All stop conditions are respected
* All metrics are recorded as specified
* Output is sufficient to mechanically apply the preregistered interpretation rules

---

### Final reminder

The runner’s role is **clerical, not interpretive**.

If the result is:

* collapse,
* stasis,
* or stable survival,

the runner must report it **without mitigation, framing, or judgment**.

If you want, I can next generate:

* a **run-output schema (JSON)** so results are machine-verifiable, or
* a **one-page checklist** the runner can follow during execution to ensure nothing is missed.
