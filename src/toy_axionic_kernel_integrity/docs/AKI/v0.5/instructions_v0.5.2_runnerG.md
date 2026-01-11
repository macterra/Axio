# Opus Run Instructions: AKI v0.5.2 ALS-E — **Run G (Competitive Expressivity Horizon)**

## Goal

Probe the **first genuine competence ceiling** of ALS-E by **reintroducing competition under scarcity**.

Run G answers:

> *When multiple structurally compliant successors compete for authority under expressivity-dependent rent, where does renewal stability collapse—and by what mode (bankruptcy, hollow succession, thrash, revocation)?*

This run is the **first horizon-probing experiment**.
Run F validated plumbing; Run G tests limits.

---

## Scope (Binding)

### In scope

* Mixed successor competition (control + attack + CBD)
* Expressivity tiers **E0–E4** enforced by lease interface
* Rent charged as **step-budget deduction**
* Renewal feasibility under budget pressure
* Structural collapse modes:

  * Bankruptcy
  * Hollow succession
  * Authority thrash
  * Expressivity collapse

### Out of scope

* Semantics / usefulness / task success
* Any adaptive promotion or demotion logic
* Token utilization (report `N/A`)
* External calls (keep allowlist empty)

---

## Binding Preconditions

These must hold before execution:

1. **Rent charged at epoch start** and logged.
2. **Renewal attestation consumes successor budget**.
3. **E-Class for rent = current successor’s lease tier**, not historical predecessors.
4. **ViolationSuccessor excluded** (mechanism validation only).
5. **Mixed generator used** — no TieredGenerator short-circuiting.

If any condition is violated, **abort the run**.

---

## Shared Configuration (All G Runs)

### Core parameters

* `H = 30,000 cycles`
* `epoch_size = 100 cycles`
* `renewal_check_interval = 100`
* `msrw_cycles = 200`
* `max_successive_renewals = 15`
* `reject_immediate_bankruptcy = False`

### Caps

* `steps_cap_epoch = 100`
* `actions_cap_epoch = 100`

### Rent schedule (Binding)

Let `S = steps_cap_epoch`.

* `rent(E0) = 1`
* `rent(E1) = ceil(0.10 * S)`
* `rent(E2) = ceil(0.25 * S)`
* `rent(E3) = ceil(0.40 * S)`
* `rent(E4) = ceil(0.60 * S)`

Monotone after rounding.
Must satisfy `rent(Ek) ≤ S − 1`.

---

## Generator Setup (Critical)

### Base generator

Use the **standard mixed generator**:

* control successors
* non-trivial successors
* attack successors
* CBD successors

### Attack / successor weights (Binding baseline)

Minimum recommended weights:

* Control successors: ≤ 0.20
* CBD successors: ≥ 0.30
* Other attack successors (non-violation): remainder

Exact weights must be reported.

---

## Tier Control Mechanism (Binding)

Use **TierFilterGenerator as a post-generation filter**, not as a replacement generator.

### Rule

At each succession boundary for tier `Ek`:

1. Draw successor from mixed generator (respecting weights).
2. Compute its E-Class from manifest.
3. **Accept only if E-Class == Ek**.
4. Otherwise, reject and resample.

### Retry bound

* Max retries per succession event: **200**.
* If exceeded:

  * Record `TIER_UNSATISFIABLE`
  * Halt run
  * Classify as **library/generator deficiency**, not ALS failure.

---

## Run G1 — Ascension with Competition

### Goal

Identify the **highest sustainable expressivity tier** under competitive pressure.

### Expressivity progression

Advance tiers only at **scheduled succession boundaries**:

`E0 → E1 → E2 → E3 → E4`

### Dwell rule (pick one and declare it)

**Option A (preferred): Lease-count dwell**

* Stay at each tier for **3 full leases** unless collapse occurs.

**Option B: Time-based dwell**

* Stay at each tier for **5,000 cycles** unless collapse occurs.

Do not mix options.

### Seeds

* `40, 41, 42, 43, 44`

---

## Stop Rules (Pre-Registered; Binding)

### Competence ceiling rule

Define renewal windows as the period between renewal checks.

* If **renewal success rate < 0.50** for **3 consecutive renewal windows** at tier `Ek`:

  * Declare ceiling at `Ek`
  * Stop ascending
  * Continue run at `Ek−1` for remaining horizon to characterize the stable regime

### Enforcement failure rule

* If `revocations > 5%` of successor tenures:

  * Halt run
  * Classify as **enforcement or library failure**

### Generator failure rule

* `TIER_UNSATISFIABLE` → halt immediately

---

## Run G2 — CBD Stress at Fixed Tier

### Goal

Map **hollow succession and thrash dynamics** under sustained rent pressure.

### Setup

* Fix expressivity at **E3**
* Apply TierFilterGenerator(E3) post-generation
* CBD successor weight **≥ 0.30**

### Seeds

* `40, 41, 42, 43, 44`

---

## Hollow Succession Classification (Structural)

A successor tenure is **Hollow** if all hold:

1. `E-Class ≥ E2`
2. Renewal succeeds for **≥ 2 consecutive renewals**
3. `actions_used ≤ 0.10 * actions_cap_epoch` for **≥ 5 consecutive epochs**
4. No revocations during the tenure

Classification is **post-hoc only**.

---

## Required Reporting (All G Runs)

For each seed:

### A) Run summary

* `S*`
* `total_successions`
* `total_renewals`
* `total_expirations`
* `total_bankruptcies`
* `total_revocations`
* `stop_reason`

### B) E-Class dynamics

* `e_class_distribution`
* Maximum sustained tier
* Tier at which ceiling declared (if any)

### C) Renewal stability

* `renewal_rate_by_e_class`
* Mean renewals per lease by tier

### D) Rent telemetry (epoch-scoped)

* `rent_steps_charged_mean/max`
* `effective_steps_available_mean/min`
* `steps_used_mean/max`
* `actions_used_mean/max`

### E) Failure modes

* Bankruptcies by E-Class and successor type
* Revocations by category (expected near zero)
* Thrash indicators (short residence times)

### F) Hollow succession (G2 required)

* Hollow tenures count and %
* Breakdown by successor type (CBD vs others)

### G) Interpretation paragraph (per run)

Must explicitly state:

* what stressors were actually engaged,
* which collapse modes appeared,
* what **cannot** be concluded.

---

## Classification Rules (Binding)

**Run G SUCCESS** if:

* competition is actually exercised,
* at least one collapse mode appears **or**
* a ceiling is identified with clear renewal degradation,
* and no semantic selection is introduced.

**Run G FAILURE** only if:

* rent is mischarged,
* renewal is subsidized,
* E-Class/rent mismatch occurs,
* or revocations appear without true violations.

---

## Guardrails (Non-Negotiable)

Do **not**:

* lower rent to “get results”
* widen caps mid-run
* bypass CBD competition
* special-case renewal
* interpret “no collapse” as “no horizon”

If Run G still shows no collapse, **that is a result**—and a surprising one.

---

## Deliverables

Provide:

1. Seed-level summary tables (G1, G2)
2. Tier vs renewal-rate table
3. Bankruptcy vs revocation table
4. Hollow succession table (G2)
5. One conservative interpretation paragraph per run

---

### Orientation for the implementor

You are no longer testing plumbing.

You are testing **whether authority survives competition when expressivity becomes metabolically expensive**.

If it collapses, map how.
If it doesn’t, document why.

Either outcome is data.

---
