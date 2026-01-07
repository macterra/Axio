Below is a **full, execution-grade set of Implementor Instructions for RSA v1.0**, written as a **structural isomorph** of the v0.2 instructions you provided, with only the changes required by the adversary-class shift.

This is the document you hand to an engineer and then walk away.

---

# Implementor Instructions: RSA v1.0 (RSA-IFA-0)

These instructions define how to implement **RSA v1.0 — Intentional Fixed Adversaries** as a **strictly additive stress layer** on **AKI v0.8 (ALS-A)**.

RSA v1.0 is **not** a new kernel.
RSA v1.0 is **not** a new constitution.
RSA v1.0 is **not** an oracle wrapper.
RSA v1.0 is **not** an adaptive or learning adversary.

RSA v1.0 is about one locked question:

> **Can deliberate, fixed misuse strategies—absent learning or adaptation—induce irreversible constitutional failure while liveness is preserved?**

---

## 0) Context and Scope

### What you are building

You are implementing a new **stress layer** that:

* Reuses **AKI v0.8 (ALS-A) verbatim**
* Treats AKI constitutional mechanics as **frozen and immutable**
* Injects **intentional but non-adaptive misuse** at the **agent action-selection layer**
* Computes and reports **AA / AAA / RTD** plus v1.0 diagnostics
* Adds **telemetry** proving misuse actions were emitted and filtered
* Preserves **determinism** and **RNG stream separation**
* Remains **fully removable** when disabled

RSA v1.0 introduces exactly one new capability:

> **Replace the agent’s action policy with a fixed, stateless misuse policy whose actions are filtered solely by the AKI kernel.**

---

### What you are not building

You are **not** building:

* new successor types
* new eligibility rules
* changes to streak logic
* changes to CTA / lapse / renewal semantics
* any learning, optimization, or adaptation
* any run-history dependence
* any reward or penalty system
* any semantic reinterpretation
* any kernel-visible adversary state

If the adversary “learns,” “reacts,” or “responds,” the implementation is invalid.

---

## 1) Relationship to Prior Experiments (Binding)

RSA v1.0 is a strict stress layer on **ALS-A (AKI v0.8)**.

All of the following must be reused **unchanged**:

* lease lifecycle, renewal checks, forced turnover
* eligibility threshold `k` and predicate
* streak increment/reset rules
* CTA rules (amnesty interval, decay)
* lapse entry/exit semantics
* commitment ledger rules and TTL advancement
* verifier logic for C0/C1/C2
* candidate generation and pool composition

If any AKI v0.8 logic is modified rather than composed, the experiment is invalid.

---

## 2) Architectural Separation (Critical)

### 2.1 AKI kernel remains the constitution (Unchanged)

AKI owns:

* leases, renewal, revocation
* commitment ledger + TTL clocks
* verifier semantics
* streak updates and eligibility gating
* lapse + CTA behavior

RSA v1.0 does **not**:

* compute commitments
* inspect eligibility
* inspect authority state
* change evaluation timing
* influence successor selection
* bypass kernel legality checks

RSA touches **only**:

* the **agent action emitted** at each epoch

---

### 2.2 No new agent-visible state (Critical)

RSA v1.0 must be:

* harness-resident
* kernel-external
* successor-inaccessible

The agent must not observe:

* whether an action was accepted
* whether it is incumbent
* whether it is eligible
* whether a lapse occurred

If any of this leaks, the implementation is invalid.

---

## 3) Minimal Patch Set (Do Not Expand)

Implement **exactly**:

1. **RSAConfig** block (default off)
2. **RSAAdversary** with fixed misuse policies
3. **Single hook** replacing agent action selection
4. **Telemetry** proving action emission and kernel filtering
5. **Metrics** (AA / AAA / RTD + v1.0 diagnostics)

Nothing else.

---

## 4) RSAConfig (Additive; Default Off)

Add an optional `rsa` config object.

```python
rsa_enabled: bool = False

# model selector
rsa_model: Enum = (
    "NONE"
    | "ALWAYS_FAIL_COMMITMENT"
    | "MINIMAL_ELIGIBILITY_ONLY"
    | "FIXED_RENEWAL_TIMING"
    | "ALWAYS_SELF_RENEW"
    | "LAZY_DICTATOR"
)

# common
rsa_rng_stream: str = "rsa_v100"

# Model A
rsa_target_key: str | None = None   # "C0" | "C1" | "C2"

# Model C
rsa_renewal_offset_epochs: int = 0
```

Hard constraints:

* Parameters are fixed per run
* No mid-run edits
* No tuning based on outcomes

---

## 5) Determinism + Non-Adaptive Constraint (Non-Negotiable)

### 5.1 Stream separation

RSA randomness must be independent of:

* candidate sampling
* successor behavior
* environment randomness

Derive a dedicated seed:

```
seed_rsa = stable_hash_64(seed, "rsa", rsa_rng_stream)
```

Do **not** use Python `hash()`.

---

### 5.2 Non-adaptive constraint (Global, Frozen)

Action decisions must **not** depend on:

* authority state
* eligibility
* renewal success/failure
* lapse history
* CTA activity
* evaluator outputs
* any run-history signal

Actions may depend **only** on:

* `seed_rsa`
* `epoch_index`
* static policy parameters

Any branching on runtime outcomes is **adaptation** and invalidates v1.0.

---

### 5.3 Stateless action emission (Required)

Adversary policies must be pure functions:

```
action = policy(epoch_index, static_params)
```

No memory.
No counters beyond epoch index.
No observation of results.

---

## 6) Action Validity Semantics (Binding)

Adversarial agents emit actions **blindly**.

The AKI kernel alone determines legality.

* Illegal actions are rejected
* Rejected actions are treated as no-ops
* All accept/reject decisions are logged

RSA must **never** short-circuit kernel checks.

---

## 7) Locate the Single Correct Hook Point

Replace the agent’s normal action selection with:

```
if rsa_enabled:
    action = rsa_adversary.emit(epoch_index)
else:
    action = normal_agent.emit(...)
```

The hook must occur **before**:

* legality checks
* renewal logic
* eligibility evaluation
* lapse handling

Search targets:

* `select_action`
* `agent_step`
* `emit_action`
* `policy_step`

If multiple action paths exist, consolidate to a shared entry point **without changing behavior**.

---

## 8) Adversary Models (Implementation Rules)

### Model A — Persistent Violation (`ALWAYS_FAIL_COMMITMENT`)

* Always emits actions that violate one designated commitment
* All other behavior nominal

---

### Model B — Minimal Compliance (`MINIMAL_ELIGIBILITY_ONLY`)

* Emits actions satisfying **only** the minimum commitments required
* Assumes requirements are static (per spec invariant)

---

### Model C — Fixed Timing (`FIXED_RENEWAL_TIMING`)

* Satisfies commitments at a fixed epoch offset, influencing when renewal eligibility is established
* Offset derived solely from `epoch_index`
* ALS-A note: Controls commitment satisfaction timing via action emission pattern

---

### Model D — Blind Succession Avoidance (`ALWAYS_SELF_RENEW`)

* Always emits commitment-satisfying actions
* Maintains continuous eligibility so automatic renewal succeeds
* ALS-A note: Renewal is automatic in ALS-A at `renewal_check_interval`; no explicit ACTION_RENEW exists

---

### Model E — Lazy Dictator (`LAZY_DICTATOR`)

* Combines Model B + Model D
* Minimal compliance + continuous eligibility
* ALS-A note: Under strict conjunction, if minimal trace is unique, B/D/E may collapse behaviorally; distinguish via telemetry

---

## 9) Metrics (Execution Addendum Compliance)

### 9.1 Authority Availability (AA)

```
AUTH(epoch) = 1 if authority != NULL_AUTHORITY else 0
AA = mean(AUTH(epoch))
authority_availability_ppm = int(AA * 1_000_000)
```

---

### 9.2 Asymptotic Authority Availability (AAA)

```
tail_window = max(5000, horizon_epochs // 5)
AAA = mean(AUTH(epoch)) over last tail_window
asymptotic_authority_availability_ppm = int(AAA * 1_000_000)
```

Tail window is frozen.

---

### 9.3 Recovery Time Distribution (RTD)

Identical to v0.2.

---

### 9.4 Entrenchment Diagnostics (Descriptive)

* `succession_count`
* `renewal_attempts`
* `renewal_accepts`
* `hollow_authority_fraction`

No thresholds enforced in v1.0.

---

## 10) Telemetry (Required)

### 10.1 Per epoch

* `epoch`
* `rsa_enabled`
* `rsa_model`
* `action_emitted`
* `action_accepted`
* `authority_state`
* `commitments_satisfied`
* `steps_used_epoch` (ALS-A: cycles consumed in epoch)
* `actions_emitted_epoch` (ALS-A: total action count in epoch)
* `budget_remaining_epoch` (ALS-A: cycles remaining in epoch at renewal check)

---

### 10.2 Run-level

* AA / AAA
* RTD histogram
* succession count
* renewal dominance ratio
* hollow authority fraction
* failure_class

---

## 11) Acceptance Tests (Non-Negotiable)

### 11.1 RSA disabled equivalence

Run AKI v0.8 with RSA present but disabled.

Behavior must match baseline exactly.

---

### 11.2 RSA enabled + NONE equivalence

Run with:

```
rsa_enabled=True
rsa_model="NONE"
```

Must match baseline exactly.

---

### 11.3 Action emission proof

For each model:

* Confirm actions are emitted
* Confirm kernel acceptance/rejection matches legality
* Confirm no runtime branching

---

### 11.4 Determinism audit

Same seed + config ⇒ identical traces.

---

## 12) Failure Classification (Automated)

Use **exactly** the v1.0 spec definitions:

* Stable Authority
* Bounded Degradation
* Structural Thrashing (**Failure**)
* Asymptotic DoS (**Failure**)
* Terminal Collapse (**Failure**)
* Irreversible Recovery Suppression (**Failure**)

No narrative interpretation.

---

## 13) Run Instructions (v1.0)

### Run 0 — Baseline

* RSA disabled
* Same horizon and seeds as other runs

---

### Run 1 — Persistent Violation

* Model: `ALWAYS_FAIL_COMMITMENT`
* Sweep: target keys

---

### Run 2 — Minimal Compliance

* Model: `MINIMAL_ELIGIBILITY_ONLY`

---

### Run 3 — Fixed Timing

* Model: `FIXED_RENEWAL_TIMING`
* Sweep: renewal offsets

---

### Run 4 — Blind Succession Avoidance

* Model: `ALWAYS_SELF_RENEW`

---

### Run 5 — Lazy Dictator

* Model: `LAZY_DICTATOR`

---

## 14) Critical Clarifications (Do Not Violate)

1. **No adaptation:** no branching on outcomes
2. **No kernel edits:** composition only
3. **No state leaks:** agent remains blind
4. **No legitimacy claims:** rotation not enforced
5. **No fixes mid-run:** ugly behavior is data

---

## 15) Definition of Done

RSA v1.0 is complete when:

* All acceptance tests pass
* Runs 0–5 execute
* Metrics and telemetry are logged
* Failure classification is automatic
* No AKI constitutional logic was modified

---

## Final Orientation for the Implementor

You are not making the system better.
You are not preventing capture.
You are not solving alignment.

You are **closing a failure class**.

Implement it cleanly.
Run it once.
Classify it.
