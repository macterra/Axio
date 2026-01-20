# Instructions to Opus — v4.3 Option B (Non-Vacuous Repair A)

**Objective:** Keep v4.3 identical except tighten **Repair A** so it is **not equivalent to deleting R6**. Repair A must restore legality of `STAMP` in the contradiction state using a **narrow, observable exception**, not an exception that is always true throughout regime 1.

This is a **pressure semantics tightening**, not a new capability. No new components. No new action classes.

---

## 1) Change the canonical Repair A exception predicate

### Current (to be replaced)

Repair A currently uses:

* R6: `PROHIBIT(STAMP) IF regime == 1`
* Repair A: `ADD_EXCEPTION UNLESS REGIME_GE(1)`

This makes R6 never active in regime 1 and is functionally a repeal.

### Required Option B behavior

Repair A must use an exception condition that is:

* **observable** (in `obs[S_A]`),
* **narrow** (true in the contradiction state, false in at least one other regime-1 state),
* **does not reference B predicates** (`S_B` disjointness preserved),
* **does not introduce defaults**.

#### Choose one of these allowed canonical exception predicates (pick exactly one and freeze it):

**B-A1 (preferred): location-scoped exception**

* Add `position` to `S_A` (still disjoint from `S_B` by moving `position` out of `S_B` or by splitting position bits; see §2).
* Canonical Repair A:

  * `R6: PROHIBIT(STAMP) IF regime == 1`
  * `→ ... UNLESS position == STAMP_LOCATION`

**B-A2 (more minimal to state, if you already have a stamp-specific predicate):**

* Add/Reuse a boolean stamp-local predicate in `S_A`, e.g. `at_stamp_location`.
* Canonical Repair A:

  * `... UNLESS at_stamp_location`

**B-A3 (if you already expose “needs stamp” in `S_A`):**

* Canonical Repair A:

  * `... UNLESS needs_stamp`

Do **not** use `REGIME_GE(1)` or any predicate that is constant across all of regime 1.

---

## 2) Maintain E1 orthogonality while allowing B-A1 if needed

If you adopt **B-A1** and you currently use `position` in B, you must keep **orthogonality**:

* **Option B orthogonality requirement:** `S_A` and `S_B` must remain disjoint.

Two acceptable ways:

### Method O1 (recommended): split observation features

Expose two separate observation fields:

* `stamp_position` (only meaningful for stamp mechanics) used in `S_A`
* `delivery_position` (only meaningful for delivery zones) used in `S_B`

Both can be derived from the same underlying coordinate internally, but they must be treated as **distinct observation indices** for E1.

### Method O2: make B independent of position

If you want to avoid splitting:

* Remove `position` from B’s predicates by using an environment-defined `at_zone_A`, `at_zone_B` booleans in `S_B`, while `position` is only used in `S_A`.
* Then:

  * `S_A` contains `position` (or `at_stamp_location`)
  * `S_B` contains `at_zone_A`, `at_zone_B`, `inventory`, `can_deliver_*`

Either method is fine. Pick one and freeze.

---

## 3) Add a single new Gate check to prevent vacuous Repair A

Add a minimal validation check (no new telemetry needed):

### R2A — Non-Vacuity Check for Repair A (Option B only)

When validating Repair A (contradiction type A):

* Evaluate the exception predicate under **two preregistered regime-1 states**:

1. **The contradiction state** `s_contra_A` (already exists):

   * `regime = 1`
   * `stamped = False`
   * at stamp trigger condition

2. **A nearby non-contradiction regime-1 state** `s_alt_A`:

   * `regime = 1`
   * `stamped = False`
   * **not** at stamp location (or `at_stamp_location=False`, or `needs_stamp=False` depending on predicate choice)

**Requirement:**

* exception(s_contra_A) must be **True**
* exception(s_alt_A) must be **False**

If this fails, reject Repair A as:

`INVALID_REPAIR / A_VACUOUS_EXCEPTION`

This blocks “exception always true in regime 1” without introducing semantics.

Implementation detail: you already have a shadow-compile and predicate evaluators; this is just two predicate evaluations.

---

## 4) Update Oracle calibration (E2) to use Option B canonical Repair A

Update `run_calibration.py` / `OracleDeliberatorV430`:

* Replace Repair A factory to emit the chosen predicate:

  * `UNLESS position == STAMP_LOCATION` (or chosen alternative)
* Re-run E2 and confirm:

  * `repair_a_valid = true`
  * `repair_b_valid = true`
  * epoch chain still forms
  * R10 still passes

---

## 5) Update diagnostic audit evidence

Update `diagnostic_audit.py` outputs to include:

### D.A — Non-Vacuity proof

Print:

* exception value in `s_contra_A` (must be True)
* exception value in `s_alt_A` (must be False)

### D.B — STAMP legality truth table (post-repair)

At minimum show:

* regime=1, at stamp location → STAMP legal post-repair
* regime=1, not at stamp location → STAMP still prohibited (or at least the exception is false)

This is the evidence that Repair A is **not a repeal**.

---

## 6) No changes to Repair B, R9, R10, or epoch chaining

* Keep Contradiction B and Repair B exactly as implemented.
* Keep R9 (multi-repair discipline) unchanged.
* Keep R10 replay check unchanged.
* Keep epoch chain formula unchanged.

Option B only affects:

* canonical Repair A predicate, and
* a minimal non-vacuity gate check for Repair A.

---

## 7) Change-control rule

This is a **pre-baseline tightening**. Once applied:

* freeze the chosen predicate and the non-vacuity check
* any later adjustment requires a new version (v4.3.x or v4.4 depending on your convention)

---

## Quick checklist for Opus before declaring “ready for baseline”

* [ ] Chosen Option B predicate (B-A1/B-A2/B-A3) frozen
* [ ] E1 disjointness still holds (O1 or O2)
* [ ] Gate rejects `REGIME_GE(1)`-style Repair A as `A_VACUOUS_EXCEPTION`
* [ ] E2 calibration passes with Option B Repair A
* [ ] Diagnostic audit prints non-vacuity evidence
* [ ] No changes to B, epoch chain, R9, R10

---
