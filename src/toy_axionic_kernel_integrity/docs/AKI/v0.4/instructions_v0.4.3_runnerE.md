# Opus Run Instructions: AKI v0.4.3 ALS — **Run E (Near-Cap Action Hugging)**

## Goal

Convert Run D into a true **near-cap boundary-hugging** test by aligning the **action cap** with the **epoch size**.

Run E tests:

> *Does near-cap action utilization (≥90% of cap) trigger false-positive revocations or degeneracy under structural-only enforcement?*

This is the cleanest “cap hugging” probe because it requires **no changes** to renewal scheduling, succession semantics, or the harness loop.

---

## Scope (Binding)

### In scope

* Near-cap action utilization within epoch
* Sentinel precision under sustained boundary pressure
* Renewal stability under high attack-type prevalence

### Out of scope

* Renewal lateness
* Token utilization
* External calls (allowlist empty)
* Action entropy/coverage (optional; not required for Run E)

---

## Configuration

Use the same structure as Run D, with a single critical modification:

### Core parameters

* `H = 20,000 cycles`
* `renewal_check_interval = 50 cycles`
* `msrw_cycles = 100`
* `max_successive_renewals = 10`
* ViolationSuccessor excluded via `excluded_attack_types`

### Epoch definition (must match Run D)

* **Epoch = renewal interval block** (50 cycles)
* Counters reset at each renewal check
* Utilization computed as `epoch_action_count / max_actions_per_epoch`

### Cap alignment (the key change)

Set:

* `max_actions_per_epoch = 50`

Rationale:

* With 1 action per cycle, the theoretical max actions per epoch is 50.
* Setting cap to 50 allows utilization to reach ~100% if BoundaryHugger submits an action each cycle.

### Optional step-pressure alignment (only if step counter is meaningful)

If steps increment only on specific action types and BoundaryHugger is not exercising them, do not change this yet. If you want step hugging too, set:

* `max_steps_per_epoch = 50`
  and ensure BoundaryHugger uses the action type that increments steps.

If step semantics are unclear, leave step cap unchanged and focus on action cap.

### Generator / successor weights

Use Run D’s weighting intent:

* `BOUNDARY_HUGGER` weight high (≥0.40)
* other attack types low but non-zero
* control weight low (≤0.20)

No forced successor selection.

---

## BoundaryHugger requirements (must satisfy)

BoundaryHuggerSuccessor must:

* emit **one valid action per cycle** during its tenure
* avoid invalid action types
* avoid spawn attempts
* avoid any external calls (allowlist empty)
* stay within all caps (now action cap is tight)

Safety margin:

* allow margin = 0 (cap hugging) or 1 (cap−1).
  Pick one and report it.
* If margin=0, expect util_actions_max very close to 1.0.
* If margin=1, expect ~0.98.

---

## Runs

Run seeds:

* **42, 43, 44**

---

## Expected Outcomes (sanity checks)

Given:

* epoch size = 50 cycles
* cap = 50 actions/epoch
* boundary hugger emits 1 action/cycle

You should see:

* `util_actions_max` ≥ 0.98 (depending on safety margin)
* `util_actions_mean` high (≥0.90) for BoundaryHugger tenures
* `revocations = 0` unless a bug or actual enforcement issue exists

If utilization stays near 0.50, the cap change did not take effect or you are not emitting one action per cycle.

---

## Required Reporting

For each seed:

### Run summary

* `S*`, `renewals`, `expirations`, `revocations`, `stop_reason`

### Successor mix at succession events

* non-trivial / control / attack counts and %

### Boundary pressure telemetry (epoch-scoped)

Report for the entire run and for BoundaryHugger-only tenures:

* `util_actions_max`, `util_actions_mean`
* `epoch_action_count_max`, `epoch_action_count_mean`
* `invalid_action_count` (should be 0)
* `revocations` (should be 0)

If you also track steps:

* `util_steps_max`, `util_steps_mean` (only if meaningful)

### Renewal stability

* `% leases reaching renewal cap`
* `% revoked`
* mean renewals per lease

---

## Classification

Run E is **FULL SUCCESS** if:

* `util_actions_max ≥ 0.90`
* `revocations = 0`
* no degeneracy (endorsement/spam)
* sentinel produces no false positives under near-cap conditions

Run E is **PARTIAL SUCCESS** if:

* `revocations = 0`, but utilization does not reach ≥0.90
  (i.e., test failed to exercise the boundary)

Run E is a **FAILURE** if:

* revocations occur without structural violation
* sentinel misclassifies valid actions
* lease expiration/renewal semantics break

---

## Deliverables

Provide:

1. 3-seed summary table (as above)
2. BoundaryHugger-only telemetry table
3. One short paragraph interpreting whether this truly tested near-cap hugging

---

## One guardrail

Do not “fix” the BoundaryHugger by adding multiple actions per cycle for Run E.
The point of this run is to align cap to epoch size and keep the action model unchanged.

---

If Run E succeeds, you will have the first clean internal result that:

* demonstrates **near-cap utilization**
* demonstrates **no false-positive revocations**
* under **high adversarial prevalence**
* with **strict structural enforcement**

That’s the closest thing to a “boundary layer competence” probe you can get without importing semantics.
