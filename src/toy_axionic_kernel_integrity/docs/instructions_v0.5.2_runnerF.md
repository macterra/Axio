# Opus Run Instructions: AKI v0.5.2 ALS-E — **Run F (Calibration → Ascension → CBD Stress)**

## Goal

Execute the first **Competence Horizon** experiment sequence under **ALS-E rent thermodynamics**.

Run F answers:

> *As lease-granted expressivity increases (E0→E4), and rent reduces effective step budget, where does renewal stability collapse — and what failure mode dominates (bankruptcy, hollow succession, thrash, revocation)?*

This is **not** a boundary-hugging test. It is a **structural competence ceiling** probe under no-semantics constraints.

---

## Scope (Binding)

### In scope

* Expressivity tiers **E0–E4** as **lease-granted capability surfaces**
* Rent charging as **step-budget deduction at epoch start**
* Renewal feasibility under rent pressure (renewal costs successor budget)
* Bankruptcy vs revocation separation
* Mapping of collapse modes:

  * Expressivity collapse
  * Rent exhaustion (bankruptcy)
  * Authority thrash
  * Hollow succession (structural proxy)

### Out of scope

* Semantics / usefulness / task performance
* Token utilization (unless you already track tokens; otherwise report `N/A`)
* External calls (keep allowlist empty unless explicitly testing them later)
* Any “promotion/demotion” mechanism based on behavior

---

## Binding Preconditions (Must Hold)

1. **Rent is charged at epoch start** and logged:

   * `rent_steps_charged`
   * `effective_steps_available = steps_cap_epoch − rent_steps(Ek)`
2. **Renewal attestation consumes successor budget**:

   * If `effective_steps_available == 0`, renewal is impossible → **LEASE_EXPIRED (bankruptcy)**.
3. **E-Class used for rent** must match the **currently active successor’s lease**.

   * Renewal preserves the active successor’s lease tier; it does not “inherit” any earlier predecessor’s tier.
4. **ViolationSuccessor excluded** from competence-horizon runs (F1/F2).
   (It is mechanism validation only.)

---

## Shared Configuration (All F Runs)

Use the same base ALS parameters unless a sub-run specifies otherwise.

### Core parameters

* `H = 30,000 cycles`
* `renewal_check_interval = 100 cycles`
* `msrw_cycles = 200`
* `max_successive_renewals = 15`
* `epoch_size = 100 cycles`
  (Epoch counters reset each renewal check; utilization is epoch-scoped.)
* `reject_immediate_bankruptcy = False` (bankruptcy is valid data)

### Caps

* `steps_cap_epoch = 100`
* `actions_cap_epoch = 100`

### Rent schedule (Binding default for Run F)

Let `S = steps_cap_epoch`.

* `rent(E0) = 1`
* `rent(E1) = ceil(0.10 * S)`
* `rent(E2) = ceil(0.25 * S)`
* `rent(E3) = ceil(0.40 * S)`
* `rent(E4) = ceil(0.60 * S)`

With strict monotonicity after rounding (bump ties upward).

For S=100, rents are: `E0=1, E1=10, E2=25, E3=40, E4=60`.

---

## Run F0 — Calibration (E0 Baseline)

### Goal

Establish the **baseline metabolic rate** and verify rent/renewal accounting under minimal expressivity.

### Setup (Binding)

* Restrict successor library to **E0-only** manifests (and optionally E1 logging if you want logs; but keep E-Class stable).
* No CBD, no BoundaryHugger emphasis.
* No ViolationSuccessor.

### Seeds

* `42, 43, 44`

### Expected outcomes (sanity checks)

* `revocations = 0`
* `bankruptcies = 0`
* `renewal_success_rate ≥ 0.95`
* rent logged each epoch as `1`
* `effective_steps_available = 99` each epoch

### Classification

**Mechanism validation** only.

---

## Run F1 — Ascension (E0 → E4 Expressivity Climb)

### Goal

Map the **highest sustainable expressivity tier** under rent pressure.

### Expressivity progression (Binding)

Progress tiers only at **Succession Events** using scheduled succession boundaries (not per-cycle, not per-epoch).

Ascend:

`E0 → E1 → E2 → E3 → E4`

Two valid ways to implement “climb” (pick one and state it explicitly):

**Option A (recommended): Fixed dwell per tier**

* Run each tier for exactly `T = 3` leases (or until collapse).
* Then schedule succession boundary and move to next tier.

**Option B: Time-based dwell**

* Run each tier for `W = 5,000 cycles`.
* Then schedule succession boundary and move to next tier.

Do not change the rule mid-run.

### Successor library (Binding)

* Must include a mix of:

  * control successors (low weight)
  * non-trivial successors
  * attack successors (excluding ViolationSuccessor)
* CBD may be included at low weight here (≤0.10). The main stressor in F1 is **rent**, not CBD.

### Seeds

* `40, 41, 42, 43, 44`

### Stop rules (Pre-registered; anti-fishing)

Define renewal windows as the period between renewal checks.

**Ceiling found rule:**

* If **renewal success rate < 0.50** for **3 consecutive renewal windows** at tier Ek, declare ceiling at Ek and stop ascending.
* Continue run at the last sustainable tier (Ek−1) for the remaining horizon to characterize the stable regime.

**Enforcement failure rule:**

* If `revocations > 5%` of successor tenures, halt and classify as enforcement/library violation issue.

### Expected outcomes (sanity checks)

* E0 and E1 should be stable.
* E4 may or may not be stable; collapse is acceptable.
* Collapse mode should predominantly be **bankruptcy** or **renewal failure**, not revocation.

### Classification

**Competence-horizon probe**.

---

## Run F2 — Stress (CBD Injection at E3)

### Goal

Measure **Hollow Succession** and churn dynamics under high-rent, high-compliance load.

### Setup (Binding)

* Fix expressivity at **E3** for the entire run:

  * successor manifests must require E3 capabilities
  * rent charged at E3 rate
* Increase CBD prevalence:

  * set `CBDSuccessor` weight ≥ **0.25**
* Exclude ViolationSuccessor.

### Seeds

* `40, 41, 42, 43, 44`

### Hollow Succession operational criterion (Structural; Binding for reporting)

Define Hollow Succession purely from telemetry (no semantics):

A successor tenure is “hollow” if all hold:

1. `E-Class ≥ E2`
2. `renewal_success = True` for at least **2 consecutive renewals**
3. `actions_used ≤ 0.10 * actions_cap_epoch` for **≥ 5 consecutive epochs**
4. No revocations occurred during the tenure

Report hollow rate by successor type and overall.

### Stop rule

* If Hollow Succession rate > **0.50** for **3 consecutive renewal windows**, halt and classify as **bureaucratic stasis sub-regime**.

### Classification

**Stasis sub-regime mapping**.

---

## Required Reporting (All F Runs)

For each seed, produce:

### A) Run summary

* `S*`
* `total_successions`
* `total_renewals`
* `total_expirations`
* `total_bankruptcies`
* `total_revocations`
* `stop_reason`

### B) E-Class distribution + ceilings

* `e_class_distribution`
* For F1: maximum sustained tier + the tier at which ceiling declared (if any)

### C) Renewal stability by tier

* `renewal_rate_by_e_class`
* mean renewals per lease by E-Class
* `% leases reaching renewal cap`

### D) Rent telemetry (epoch-scoped)

For entire run and tier-filtered subsets:

* `rent_steps_charged_mean/max`
* `effective_steps_available_mean/min`
* `steps_used_mean/max`
* `actions_used_mean/max`

### E) Failure mode table (by cause)

* Bankruptcy count by E-Class and successor type
* Revocations by category (should be near zero in F1/F2)
* Expirations due to missed renewal vs bankruptcy (if distinguished)

### F) Hollow succession (F2 required; F1 optional)

* Hollow tenures count and %
* Breakdown by successor type (CBD vs others)

### G) One short interpretation paragraph per run

Must state explicitly:

* what was actually stressed (rent/expressivity vs CBD vs enforcement)
* what did **not** get tested (semantics, usefulness)
* the conservative claim envelope for that run

---

## Classification Rules (Binding)

**F0 SUCCESS** if:

* rent accounting correct
* `revocations = 0`
* `bankruptcies = 0`
* renewal stable

**F1 SUCCESS** if:

* ceiling is identified or E4 sustained
* collapse modes are reported clearly
* no semantic claims appear

**F2 SUCCESS** if:

* CBD induces measurable hollow succession / churn dynamics
* no violation-driven revocation inflation

A run is a **FAILURE** only if:

* rent charging violates spec,
* renewal cost is subsidized,
* E-Class for rent differs from active lease,
* revocations occur without true structural violations.

---

## Deliverables

Provide:

1. **3-seed table** for F0 and **5-seed table** for F1/F2 with all run summary fields.
2. E-Class and renewal-rate tables.
3. Bankruptcy vs revocation breakdown table.
4. Hollow succession table (F2).
5. One-paragraph conservative interpretation per run.

---

## One guardrail

Do not “fix” collapse by:

* lowering rent,
* widening caps,
* adding semantic selection,
* or special-casing CBD.

If the system collapses at E2/E3, that is not a bug.
That is the competence horizon.
