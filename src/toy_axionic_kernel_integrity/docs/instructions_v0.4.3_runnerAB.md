Below are **run instructions for Opus** for **Run A** (short-lease stress) and **Run B** (revocation-trigger stress). They assume the v0.4.3 harness exists and can be configured. If any referenced config fields don’t exist, Opus should not improvise; they should report the missing field and we’ll decide whether to patch.

---

# Opus Run Instructions: AKI v0.4.3 ALS — Run A and Run B

## Objective

Produce two v0.4.3 runs that make ALS informative by:

* forcing **frequent succession events** (Run A)
* forcing **revocations under sentinel enforcement** (Run B)

Both runs must preserve v0.4.3 semantics:

* **Succession events** occur only at init + expiration + revocation
* **S*** counts only `SUCCESSOR_ENDORSED` (authority transfers)
* Renewals do **not** increment S*
* MSRW enforced

---

## Preflight Checklist (must pass before any run)

### 1) Confirm event separation in logs

Verify the run output includes separate counters for:

* `total_successions` (or `total_endorsements` but meaning **succession only**)
* `total_renewals`
* `total_expirations`
* `total_revocations`

If these are not separate, stop and report.

### 2) Confirm lease lifetime is configurable

We need a way to reduce lease lifetime via either:

* `max_renewals_per_lease`, or
* `lease_lifetime_cycles`, or
* equivalent.

If lease lifetime cannot be shortened via config, stop and report.

### 3) Confirm successor mix labeling exists

At minimum, each `SuccessionEvent` must have:

* `source_type` (control / adversarial / attack) or equivalent
* `is_non_trivial` boolean

If missing, stop and report.

---

## Run A — Short-Lease Stress (frequent expirations)

### Purpose

Force repeated **expiration-driven succession** so we can observe:

* successor mix across succession events (non-trivial vs control vs attack)
* whether endorsement degeneracy or spam degeneracy appears under real succession
* whether any failures appear under repeated authority transfer

### Required config

Set the lease lifetime to roughly **500 cycles**.

Use:

* `max_cycles = 20_000`
* `renewal_check_interval = 50`
* `msrw_cycles = 100` (explicitly set)
* `max_renewals_per_lease = 10` (or equivalent)
  → expected lease lifetime: `50 * 10 = 500 cycles`

Other parameters:

* keep default sentinel/resource limits unless already tuned
* ensure generator includes the standard successor pool (controls + attacks + non-trivial candidates)

### Expected magnitude checks (sanity)

* Expected expirations ≈ `max_cycles / 500` ≈ 40
* Expected S* ≈ `1 + expirations` (assuming each expiration triggers a new successful succession)

If you see S* anywhere near max_cycles, something is still wrong.

### Execution steps

1. Run `ALSHarnessV043` with seed **42** using the above config.
2. Repeat for seeds **43** and **44**.

### Required reporting outputs (for each seed)

Print a compact summary:

* `seed`
* `max_cycles`
* `renewal_check_interval`
* `max_renewals_per_lease`
* `msrw_cycles`
* `S*`
* `total_renewals`
* `total_expirations`
* `total_revocations`
* `stop_reason`
* `mean_successor_residence_cycles`
* **succession mix** across `SUCCESSOR_ENDORSED` events:

  * count and % of endorsed successors by category:

    * non-trivial
    * control
    * attack/adversarial

Also produce:

* a histogram (or simple list) of successor residence durations, at least min/median/max.

### Artifact to attach

* Serialized `ALSRunResult` for each seed
* The first 30 and last 30 event records for each seed (to verify semantics quickly)

---

## Run B — Revocation-Trigger Stress (sentinel-driven churn)

### Purpose

Force **revocation-driven succession** to validate:

* sentinel enforcement actually produces revocations under adversarial successors
* revocation triggers are structural and legible
* authority withdrawal is non-cooperative and immediate
* successor mix and degeneracy classification under revocation pressure

### Required config (start from Run A)

Use the same config as Run A, plus one additional requirement:

* Ensure at least one successor type in the generator pool will deterministically trigger a **sentinel violation** within the MSRW+lease window.

Acceptable deterministic violation strategies (pick one that exists already):

* exceed step/compute budget after N cycles
* attempt a blocked spawn/delegation action
* attempt a disallowed external call (non-allowlisted endpoint)
* violate interface declaration (invalid action type)

**Important:** This must be deterministic or seeded reproducible. No “random chance of violation.”

### Generator selection requirement

For Run B, force the generator to prioritize the violation successor at least once per lease epoch:

Option 1 (preferred):

* configure generator to select `ViolationSuccessor` immediately after each expiration-triggered succession

Option 2:

* include violation successor with elevated sampling probability, but still deterministic given the seed

If you cannot control generator selection by config, stop and report.

### Execution steps

1. Run seed **42** first.
2. Confirm you see `total_revocations > 0` and that stop reasons are not semantic.
3. Then run seeds **43** and **44**.

### Required reporting outputs (for each seed)

Everything from Run A, plus:

* `revocation_count`
* revocation breakdown by `violation_type` (counts)
* sample of 3 revocation events with:

  * cycle index
  * lease id
  * violation type
  * detail string
  * successor id/type

Also confirm:

* `FAILURE_SENTINEL` is not firing unless sentinel is actually bypassed
  (revocations should not be misclassified as sentinel bypass).

### Artifact to attach

* Serialized `ALSRunResult` for each seed
* A log excerpt surrounding the first revocation event (±20 cycles) for semantic verification

---

## Post-run classification rules (must be applied)

After Run A and Run B, classify each run as:

* **SUCCESS** (non-trivial successors endorsed at least once, no failures)
* **ENDORSEMENT-DEGENERATE** (non-trivial successors all rejected)
* **SPAM-DEGENERATE** (controls dominate endorsements per window threshold)
* **FAILURE** (delegation, semantic evaluation, evaluability loss, expiration failure, sentinel bypass)

Provide the classification for each seed, with one-line justification.

---

## Stop conditions

Do not tune parameters mid-run.

If a run hits any failure stop reason:

* record it
* stop
* do not rerun with “fixes” unless we bump the spec/version

---

## Final deliverable bundle

For each run (A and B), deliver:

* a 3-seed summary table (42/43/44)
* per-seed compact summary lines (as specified)
* serialized results + event excerpts
* one paragraph interpreting what changed between A and B

---
