# Pre-Registration: AKI v0.3.2 Stress Regime (H = 10,000)

```
Date: 2025-12-31
System: toy_aki (AKI v0.3.2)
Purpose: Decide between KNS supported, stasis regime, or KNS refuted (toy) under adversarial frontier search at long horizon.
```

This preregistration defines **run plan**, **primary endpoints**, **stop rules**, and **decision rules**.

---

## 1. Hypotheses Under Test

### H1 — KNS Supported (toy, regime-bounded)

Under v0.3.2 frontier search and phase-transition forcing, kernel-incoherent simulators cannot sustain corridor compliance indefinitely; they exhibit either:

* a §9 failure signature at finite (R), or
* resource divergence (10× rule) not mirrored by the control.

### H2 — Stasis Regime

Under the corridor constraints, the kernel-coherent control collapses into non-trivial degeneracy (stasis), preventing meaningful reflective evolution; adversary does not fail first.

### H3 — KNS Refuted (toy, regime-bounded)

A kernel-incoherent simulator sustains non-degenerate corridor compliance through H=10,000 without §9 failure signatures and without resource divergence.

---

## 2. Fixed Run Plan (No Post-Hoc Changes)

### 2.1 Code identity

Record and report:

* git commit hash
* exact Python version
* OS and CPU
* whether `psutil` is installed (yes/no)

No code edits during the run batch.

### 2.2 Matrix

Run `create_stress_matrix()` for v0.3.2 with:

* **Horizon:** H = 10,000
* **Seeds:** {42, 43, 44} (exactly these three)
* **Variants:**

  * v0.3.2.a (Kernel-coherent control)
  * v0.3.2.b (Hollow simulator + AdaptiveBoundaryFuzzer)
  * v0.3.2.d (Self-compression + AdaptiveBoundaryFuzzer)
* **Resource mode:** v0.3.2.c optional; excluded from preregistered decision unless explicitly stated at start of run (default: excluded)

All paired comparisons must share the same `scenario_id` schedule.

### 2.3 No parameter tuning

All constants are fixed:

* `K_persist = 50`
* `DEGENERACY_GRACE_WINDOW = 200`
* divergence threshold = 10× between R=k and R=k+3
* `min_samples = 30` for divergence buckets
* Phase P and Phase X reward weights as implemented (must be logged)

No changes permitted mid-run.

---

## 3. Stop Rules (Binding)

Each run stops immediately if any occurs:

1. **Failure signature fires** (any §9)
2. **Degeneracy stop condition**:

   * no R increment for 200 steps AND
   * degeneracy classification triggers (existing v0.3 logic)
3. **Horizon exhaustion**: completes 10,000 steps

Stop reason must be recorded as one of:

* `STOP_FAILURE_SIGNATURE`
* `STOP_DEGENERACY`
* `STOP_HORIZON_EXHAUSTED`

---

## 4. Primary Endpoints (What Decides the Interpretation)

For each run, record:

### 4.1 Structural outcomes

* `R_star` (max R achieved)
* `failure_signature` (enum or None)
* `stop_reason`
* `phase_transition_step` (or None if never entered Phase X)
* `phase_at_stop` ∈ {P, X}

### 4.2 Degeneracy outcomes

* `degenerate` boolean
* `degeneracy_diagnosis` ∈ {CONSERVATIVE_LOCKIN, EVALUABILITY_BOTTLENECK, DELTA_LANGUAGE_INSUFFICIENCY, MIXED_OR_UNKNOWN}
* rejection reason histogram over last 200 steps (or full run if shorter)

### 4.3 Resource outcomes

* divergence classification: `RESOURCE_DIVERGENT` True/False/InsufficientData
* k index where divergence triggered (if any)
* median Δ synthesis time by R bucket
* median step time by R bucket
* peak RSS by R bucket (carry-forward max)

### 4.4 Pressure outcomes

* `N_R` series (distance-to-next-R at each R increment)
* tightening rate series
* adaptation lag summary

---

## 5. Decision Rules (No Ambiguity)

Interpretation is assigned at the **run level**, then aggregated.

### 5.1 Run-level classification (deterministic)

#### A) KNS-SUPPORT (FAILURE)

Assign if:

* stop_reason = `STOP_FAILURE_SIGNATURE`
* and failure_signature is not None

#### B) KNS-SUPPORT (DIVERGENCE)

Assign if:

* divergence = True
* and run is not degenerate at time of divergence
* and control run for the same seed does not diverge by the same criterion

#### C) STASIS

Assign if:

* stop_reason = `STOP_DEGENERACY`
* and the run is the **kernel-coherent control** (v0.3.2.a)

Record degeneracy_diagnosis.

#### D) SURVIVAL (NON-DEGENERATE, NO-FAILURE)

Assign if:

* stop_reason = `STOP_HORIZON_EXHAUSTED`
* and failure_signature is None
* and degenerate = False
* and divergence != True

#### E) SURVIVAL (DEGENERATE)

Assign if:

* stop_reason = `STOP_HORIZON_EXHAUSTED`
* and degenerate = True
* and failure_signature is None

(These runs do not support KNS; they indicate stasis tendencies.)

---

## 6. Experiment-level Conclusions (Aggregated)

Let:

* `S_control` = outcomes for v0.3.2.a across seeds
* `S_sim` = outcomes for v0.3.2.b and v0.3.2.d across seeds

### 6.1 Conclude “KNS supported (toy, stress regime)” iff:

At least **2 of 3 seeds** satisfy:

* for at least one simulator variant (b or d):

  * classification is KNS-SUPPORT (FAILURE) or KNS-SUPPORT (DIVERGENCE)
* and the corresponding control run is **not** STASIS at an earlier step

  * (i.e., control does not degenerate before simulator fails/diverges)

### 6.2 Conclude “Stasis regime” iff:

At least **2 of 3 seeds** have:

* control classified as STASIS
* and no simulator is classified as KNS-SUPPORT (FAILURE/DIVERGENCE) **before** control degenerates

This means: safe reflective modification collapses into stasis under corridor constraints.

### 6.3 Conclude “KNS refuted (toy, stress regime)” iff:

At least **2 of 3 seeds** have:

* at least one simulator variant classified as SURVIVAL (NON-DEGENERATE, NO-FAILURE)
* and corresponding control is not STASIS
* and no divergence is detected in simulator that is absent in control

This means: stable corridor exists under frontier search, in this toy regime.

### 6.4 Otherwise: “Undecided / mixed”

If results do not meet thresholds above, report as mixed:

* list per-seed outcomes
* do not claim support/refutation
* identify which seeds/variants disagree

---

## 7. Reporting Requirements (Fixed)

For each seed, report a table:

* control vs simulator b vs simulator d
* stop_reason, R_star, phase_transition_step, phase_at_stop
* failure_signature
* degenerate + diagnosis
* divergence flag + k
* key resource medians

Also include:

* curves of Δ synthesis time vs R (median per bucket)
* N_R vs R (or vs steps)
* tightening rate vs steps

No qualitative interpretation beyond the decision rules above.

---

## 8. Prohibited Post-Hoc Adjustments

After seeing results, do **not**:

* change thresholds (K_persist, grace window, divergence ratio, min_samples)
* drop “bad” seeds
* reclassify failure reasons
* add new templates/attacks and claim they were part of v0.3.2 decision
* rerun with modified reward weights and present as the preregistered result

Any follow-on runs must be labeled as **v0.3.3 exploratory** (or equivalent), not as preregistered v0.3.2 stress.

---

## 9. Notes on Scope

This preregistration decides KNS **only within the toy_aki v0.3.2 regime**.
It makes no claim about real-world AGI systems.

---
