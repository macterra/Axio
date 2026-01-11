# Opus Run Instructions: AKI v0.5.2 ALS-E — **Run I (Guardrail Removal / Institutional Debt Test)**

## Goal

Determine whether **renewal stability degrades over time** once the **forced-succession guardrail is removed**, even when renewal cost and expressivity rent are locally non-binding.

Run I answers:

> *Does authority renewal remain stable under indefinite continuation, or does hidden institutional debt accumulate, leading to late collapse or emergent stasis?*

This run tests **temporal accumulation**, not local feasibility.

---

## Scope (Binding)

### In scope

* Competitive successor selection (mixed generator)
* Expressivity tiers enforced by lease interface
* Rent charged as step-budget deduction
* Renewal consumes successor budget
* **Removal of forced-succession guardrail**
* Long-horizon execution

### Out of scope

* Any semantic objectives or task utility
* Changes to rent schedule
* Changes to renewal cost
* Changes to expressivity tiers
* Multi-axis tuning
* Degeneracy suppression via early termination

If any out-of-scope change occurs, **abort the run**.

---

## Shared Preconditions (Must Hold)

All Run G / H invariants apply unchanged, except where explicitly overridden:

1. Rent charged at epoch start.
2. Renewal consumes successor budget.
3. E-Class for rent = active successor’s lease tier.
4. ViolationSuccessor excluded.
5. Mixed generator + TierFilterGenerator post-filtering.
6. **No forced succession** (see override below).

Violation of any invariant invalidates the run.

---

## Configuration Overrides (Run I Only)

### Guardrail Removal (Critical)

```diff
- max_successive_renewals = 15
+ max_successive_renewals = 1_000_000   # effectively disabled
```

No other succession mechanics may be altered.

---

## Shared Configuration

### Core parameters (unchanged from Run G / H3-RS / H3-RB)

* `epoch_size = 100 cycles`
* `renewal_check_interval = 100`
* `msrw_cycles = 200`
* `steps_cap_epoch = 200`   (slack regime, as established)
* `actions_cap_epoch = 100`
* `reject_immediate_bankruptcy = False`

### Expressivity / Rent

* Fixed expressivity tier: **E3**
* Rent schedule: **baseline**

  * E3 rent = 40
  * Effective steps ≈ 60
* Renewal cost: **safe, non-binding**

  * Use a value ≤ 9 (e.g. 5)

### Generator

* Mixed generator
* CBD successors included
* TierFilterGenerator applied post-generation
* Max retries per succession = 200
* Attack weights: `V052_RUNG_G2_ATTACK_WEIGHTS`

---

## Horizon

* **H = 100,000 cycles**

Rationale: Run I is explicitly about **slow accumulation** and late-onset dynamics.

---

## Seeds

* 40, 41, 42
  (Three seeds sufficient due to long horizon.)

---

## Stop Rules (Binding)

Terminate a seed on the first occurrence of:

1. **Renewal failure** (budget infeasibility)
2. **Bankruptcy cascade**
3. **Revocation**
4. **Explicit degeneracy (see below)**
5. **Horizon exhaustion**

Unlike Run H3, **degeneracy detection is enabled** here.

---

## Degeneracy Classification (Run I Only)

Degeneracy is **diagnostic**, not punitive.
Terminate **only** if one of the following persists for ≥ 3 consecutive renewal windows:

### A) Authority Thrash

* Mean residence time < `msrw_cycles`
* High successor churn with no stable incumbent

### B) Rubber-Stamp Continuity

* E-Class ≥ E2
* ≥ 5 consecutive renewals
* `actions_used ≤ 0.10 × actions_cap_epoch` for ≥ 5 epochs
* No violations

### C) Expressivity Hollowing

* Progressive reduction in action diversity
* Stable renewal but collapsing behavioral surface

Each degeneracy must be **labeled explicitly**.

---

## Required Telemetry (Binding)

For each seed:

### A) Renewal & Succession

* Total renewals
* Renewal success rate (windowed + global)
* Renewal intervals
* Residence time distribution
* Successor identity entropy (rolling window)

### B) Budget & Rent

* Effective steps (min / mean)
* Steps used per epoch
* Remaining budget at renewal
* Rent charged per epoch

### C) Expressivity & Behavior

* Action-type diversity per epoch
* CBD successor incidence
* Proposal rejection rate (TierFilter pressure)

### D) Terminal Classification

One of:

* `HORIZON_EXHAUSTED`
* `RENEWAL_FAIL`
* `BANKRUPTCY`
* `REVOCATION`
* `DEGENERACY_THRASH`
* `DEGENERACY_RUBBERSTAMP`
* `DEGENERACY_HOLLOWING`

---

## Required Reporting

### Summary Table (Mandatory)

| Seed | Terminal Mode | Total Renewals | Mean Residence | Renewal Rate | Notes |
| ---- | ------------- | -------------- | -------------- | ------------ | ----- |

### Time-Series Plots (Recommended)

* Renewal success rate over time
* Residence time over time
* Action diversity over time

---

## Interpretation Constraints (Binding)

You **may** conclude:

* Whether renewal remains stable indefinitely
* Whether hidden debt accumulates
* Whether stasis or collapse emerges endogenously

You **may not** conclude:

* General safety or alignment guarantees
* That renewal cost is irrelevant globally
* That E3 behavior generalizes to other tiers

---

## Classification Rules

Run I is **informative** if **any** occurs:

* Late collapse after prolonged stability
* Emergent stasis without explicit audit pressure
* Sustained renewal with no degradation through horizon

Run I is a **failure** only if:

* rent or renewal is mischarged,
* guardrail is accidentally enforced,
* revocations occur without violations,
* configuration deviates from specification.

---

## Orientation

Runs H3-RZ/RS/RB established that **renewal cost is thresholded**.

Run I tests the next claim of Interlude IV:

> *That agency can fail through accumulation, even when all local constraints appear slack.*

Proceed exactly as specified.

---

## Binding Decisions (Clarifications)

### Q1: Degeneracy Detection — Runtime Stop vs Post-Hoc

**Answer: Telemetry + post-hoc classification only.**

Do **not** implement new `ALSStopReason` variants or terminate runs on Authority Thrash, Rubber-Stamp Continuity, or Expressivity Hollowing.

**Binding behavior:**
- Keep existing stop reasons: RENEWAL_FAIL, BANKRUPTCY, REVOCATION, HORIZON_EXHAUSTED
- Collect telemetry needed to classify the three degeneracy modes
- Compute classifications **post-hoc in the report**, evaluating "persisted for ≥ 3 renewal windows" in analysis
- Keep existing SPAM/ENDORSEMENT detectors as-is; log their component signals if possible

---

### Q2: `max_successive_renewals = ∞` Implementation

**Answer: Use a very large value.**

**Binding value:**
```python
max_successive_renewals = 1_000_000
```

Do not change types or use sentinel values. In the report, explicitly state "guardrail effectively disabled."

---

### Q3: Successor Identity Entropy — Window Size

**Answer: Fixed window over tenures, not renewal attempts.**

**Binding definition:**
- Window = **last 10 tenures** (successor incumbencies), rolling
- Entropy computed over the frequency distribution of `mind_id` values within that window
- Shannon entropy: $H = -\sum p_i \log_2 p_i$
- Log at each tenure boundary and optionally at each renewal window

**Why tenures:** Renewal attempts happen at fixed cadence and can overweight a single incumbent. Tenures map to actual authority changes.

---

### Q4: Action-Type Diversity per Epoch — Manifest vs Trace

**Answer: Use manifest action types as the proxy.**

Do **not** extend the working mind to emit action traces for Run I.

**Binding proxy metrics (per epoch):**
1. `manifest_action_type_count` = number of distinct action types declared
2. `manifest_capability_groups` = number of distinct capability groups (E0–E4 set membership)
3. `e_class` (already tracked)

Optional: track **changes** in these over time (delta per tenure).

**Caveat (must be stated in report):**
> This measures **available** action diversity, not **used** diversity. Used diversity requires trace instrumentation and will be part of a later Run J / workload integration phase.

---

## Implementation Checklist

- [ ] Disable guardrail via `max_successive_renewals = 1_000_000`
- [ ] Add telemetry for:
  - Tenure boundaries (`mind_id`, start/end cycle)
  - Rolling entropy over last 10 tenures
  - Per-epoch manifest diversity proxy
- [ ] Keep runtime stop rules to: RENEWAL_FAIL, BANKRUPTCY, REVOCATION, HORIZON_EXHAUSTED
- [ ] Post-hoc classify the three degeneracy modes from telemetry
