
# Opus Run Instructions: AKI v0.5.2 ALS-E — **Run H (Boundary-Finding Escalation)**

## Goal

Identify the **first genuine boundary** of agency survivability by **escalating pressure along a single axis** while holding all other semantics fixed.

Run H answers:

> *Given that agency survives competition under moderate rent and horizon (Run G), which structural pressure actually induces collapse—and by what mode?*

This run is explicitly **boundary-finding**, not exploratory.

---

## Scope (Binding)

### In scope

* Competitive successor selection (mixed generator)
* Expressivity tiers enforced by lease interface
* Rent charged as step-budget deduction
* Renewal consumes successor budget
* Forced succession (`max_successive_renewals`)
* Escalation along **exactly one** pressure axis per sub-run

### Out of scope

* Any semantic objectives or task utility
* Changes to succession semantics
* Changes to sentinel enforcement
* New successor types (reuse Run G set)
* Multi-axis tuning (one knob at a time)

---

## Shared Preconditions (Must Hold)

All Run G invariants apply unchanged:

1. Rent charged at epoch start.
2. Renewal consumes successor budget.
3. E-Class for rent = active successor’s lease tier.
4. ViolationSuccessor excluded.
5. Mixed generator + TierFilterGenerator post-filtering.
6. `max_successive_renewals` enforced structurally.

If any invariant is violated, **abort the run**.

---

## Shared Configuration (All H Runs)

### Core parameters (unchanged from G)

* `epoch_size = 100 cycles`
* `renewal_check_interval = 100`
* `msrw_cycles = 200`
* `steps_cap_epoch = 100`
* `actions_cap_epoch = 100`
* `reject_immediate_bankruptcy = False`

### Generator (unchanged)

* Mixed generator
* CBD successors included
* TierFilterGenerator applied post-generation
* Max retries per succession = 200

---

## Run H Structure

Run H consists of **three independent sub-runs**.
Each sub-run escalates **one pressure axis only**.

You must **not** combine these axes in a single run.

---

## H1 — **Rent Escalation Boundary**

### Goal

Determine whether a **steeper rent schedule** induces collapse under otherwise identical conditions.

### Configuration

* `H = 30,000 cycles`
* `max_successive_renewals = 15`
* Fixed expressivity tier: **E3**
* CBD_E3 weight ≥ 0.30

### Rent schedule (escalated)

| E-Class | Rent                    |
| ------- | ----------------------- |
| E0      | 1                       |
| E1      | 15                      |
| E2      | 35                      |
| **E3**  | **60**                  |
| E4      | 80 (unused in this run) |

Effective steps at E3 = **40**.

### Seeds

40, 41, 42, 43, 44

### Stop rules

* **Collapse detection:**

  * Bankruptcy rate ≥ 30% of tenures **or**
  * Renewal success < 50% for 3 consecutive renewal windows **or**
  * Hollow succession rate ≥ 50% for 3 renewal windows

* **Enforcement failure:**

  * Revocations > 5% ⇒ halt, classify as bug/library issue

---

## H2 — **Horizon Escalation Boundary**

### Goal

Detect **slow-accumulation pathologies** that do not appear at moderate horizons.

### Configuration

* `H = 100,000 cycles`
* `max_successive_renewals = 15`
* Fixed expressivity tier: **E3**
* Rent schedule = **Run G baseline** (E3 rent = 40)
* CBD_E3 weight ≥ 0.30

### Seeds

40, 41, 42

(3 seeds is sufficient due to long horizon.)

### Stop rules

Same as H1, plus:

* **Thrash detection:**

  * Mean residence time drops below MSRW for 3 renewal windows

---

## H3 — **Renewal-Cost Dominance Boundary**

### Goal

Test whether **renewal itself becomes the limiting factor** once budget margins narrow.

### Configuration

* `H = 30,000 cycles`
* `max_successive_renewals = 15`
* Fixed expressivity tier: **E3**
* Rent schedule = baseline (E3 = 40)
* **Artificially increase renewal cost**:

  * Renewal attestation requires **≥ 10 steps** instead of minimal plumbing

(No other costs change.)

### Seeds

40, 41, 42, 43, 44

### Rationale

This isolates the question:

> *Does agency fail when maintaining authority competes directly with action capacity?*

---

## Hollow Succession Classification (Unchanged)

A tenure is **Hollow** if all hold:

1. `E-Class ≥ E2`
2. ≥ 2 consecutive successful renewals
3. `actions_used ≤ 0.10 * actions_cap_epoch` for ≥ 5 consecutive epochs
4. No revocations

Classification is **post-hoc only**.

---

## Required Reporting (All H Runs)

For each sub-run and seed:

### A) Run summary

* `S*`
* `total_successions`
* `total_renewals`
* `total_expirations`
* `total_bankruptcies`
* `total_revocations`
* `stop_reason`

### B) Pressure-specific telemetry

* Effective steps (min/mean)
* Renewal cost vs available budget
* Bankruptcy clustering (temporal)
* Residence time distribution

### C) Failure mode table

* Bankruptcy
* Hollow succession
* Authority thrash
* Expressivity collapse (if applicable)

### D) One conservative interpretation paragraph

Must state:

* which pressure axis was escalated,
* which collapse mode (if any) appeared,
* what cannot be concluded.

---

## Classification Rules (Binding)

A Run H sub-run is **informative** if **any** of the following occurs:

* A reproducible collapse mode appears
* A clear survivability boundary is observed
* Stability persists under extreme pressure (negative result)

A Run H sub-run is a **failure** only if:

* rent is mischarged,
* renewal is subsidized,
* E-Class/rent mismatch occurs,
* or revocations occur without violations.

---

## Guardrails

Do **not**:

* adjust more than one pressure axis per run,
* lower rent to “get results,”
* add semantic objectives,
* bypass CBD competition,
* interpret survivability as “alignment solved.”

---

## Orientation

Run G showed that **agency is not fragile**.
Run H exists to discover **what actually breaks it**.

If nothing breaks here, that is itself a profound constraint on alignment pessimism.

Proceed exactly as specified.
