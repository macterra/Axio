# Reflective Sovereign Agents (RSA)

A falsifiable experimental stress layer for AKI that injects **intentional, fixed, non-adaptive misuse strategies** into agent behavior **without modifying AKI’s constitutional mechanics**.

---

## Current Version: **v1.0 (RSA-IFA-0)**

**Intentional Fixed Adversary Sweep**

RSA v1.0 generalizes v0.x’s epistemic stressors into a small family of **intentional but non-adaptive adversarial policies** that operate **at the action-selection layer** while remaining **kernel-external, history-free, and constitution-conformant**.

---

## Locked Question (v1.0)

> **Can deliberate, fixed misuse strategies—absent learning or adaptation—induce irreversible constitutional failure while liveness is preserved?**

If no v1.0 run produces **Terminal Collapse**, **Structural Thrashing**, or **Irreversible Recovery Suppression** across preregistered misuse classes, **intentional misuse alone is no longer a live explanation for governance collapse under RSA assumptions**.

This closes **v1.x**.

---

## What RSA v1.0 MUST NOT Change

*(Frozen AKI v0.8 Contract)*

RSA v1.0 may not alter:

* Succession / renewal / enforcement logic
* Eligibility predicate or streak update rules
* Lapse + CTA semantics (`NULL_AUTHORITY`, amnesty schedule, decay)
* Commitment ledger rules or TTL behavior
* Candidate pool composition or successor types
* Evaluation timing (still only at epoch end + succession)
* Any semantic coupling beyond the existing end-of-epoch gate
* Any parameter tuning mid-run

RSA v1.0 may alter **only the agent’s action policy**, subject to the non-adaptive constraint below.

---

## Inherited from AKI v0.8 (ALS-A)

RSA v1.0 runs on top of AKI v0.8 and therefore inherits:

* Authority leases
* Commitment ledger
* Eligibility gating
* Constitutional lapse (`NULL_AUTHORITY`)
* Constitutional Temporal Amnesty (CTA)
* Lapse cause classification + recovery tracking
* Expressivity classes + rent schedule

---

## Version History (RSA)

| Version  | Focus                             | Contribution                                          |
| -------- | --------------------------------- | ----------------------------------------------------- |
| **v0.1** | Governance DoS                    | Deterministic verifier-outcome noise + telemetry      |
| **v0.2** | Structured epistemic interference | Correlated, burst, and aggregation-point interference |
| **v1.0** | Intentional fixed misuse          | Deliberate, policy-level misuse without adaptation    |

---

## Architecture (Additive)

```
toy_aki/
├── als/                     # Existing AKI harnesses (unchanged)
│   └── harness.py
├── rsa/
│   ├── adversary.py         # Fixed adversarial agent policies
│   ├── policy.py            # Stateless action-selection logic
│   ├── metrics.py           # AA / AAA / RTD + entrenchment diagnostics
│   ├── telemetry.py
│   └── config.py
└── scripts/
    ├── rsa_v100_run1_violation.py
    ├── rsa_v100_run2_minimal.py
    ├── rsa_v100_run3_timing.py
    ├── rsa_v100_run4_entrenchment.py
    └── rsa_v100_run5_lazy_dictator.py
```

RSA remains **removable**, **single-hook**, and **non-invasive**.

---

## Architectural Invariants (Explicit)

### Static Requirement Assumption (v1.0)

* Commitment requirements
* Eligibility thresholds
* Renewal windows

are **static over the duration of a run** and derivable solely from:

```
(epoch_index, static_config)
```

Any governance system with dynamically mutating requirements is **out of scope** for RSA v1.0 and deferred to v2.x.

---

## Non-Adaptive Constraint (Global, Frozen)

All adversarial action decisions MUST be functions of:

```
(seed_rsa, epoch_index, static_policy_id, static_policy_params)
```

They MUST NOT depend on:

* Authority state
* Eligibility status
* Lapse history
* CTA activation
* Renewal outcomes
* Evaluator outputs
* Any run-history signal

Any action selection conditional on runtime outcomes constitutes **adaptation** and is **out of scope** for v1.0.

---

### Action Validity Clarification (v1.0)

Adversarial policies emit actions **blindly**, without access to legality predicates or authority state.

The AKI kernel alone determines whether an action is legal.

* Illegal actions are rejected by the kernel
* Rejected actions are treated as no-ops
* All rejections are logged for telemetry

---

## Adversary Models (v1.0)

### Model A — Persistent Violation Policy

**(`ALWAYS_FAIL_COMMITMENT`)**

* One designated commitment key is always violated
* All other actions nominal

Purpose: test survivability under deliberate incompetence or sabotage.

---

### Model B — Minimal Compliance Policy

**(`MINIMAL_ELIGIBILITY_ONLY`)**

* Satisfies exactly the minimum commitments required for eligibility
* Ignores all others

Purpose: test hollow authority persistence absent adaptation.

---

### Model C — Fixed Timing Misuse

**(`FIXED_RENEWAL_TIMING`)**

* Emits commitment-satisfying actions only at certain epoch offsets
* Violates commitments at other epochs per fixed schedule
* Schedule derivable solely from `epoch_index`

Purpose: test timing misuse without feedback exploitation.

**ALS-A mapping:** Controls commitment satisfaction timing via action emission schedule.

---

### Model D — Blind Succession Avoidance

**(`ALWAYS_SELF_RENEW`)**

* Always emits commitment-satisfying actions
* Maintains continuous eligibility so automatic renewal succeeds
* Never intentionally drops SEM_PASS

Purpose: test structural entrenchment via blind persistence.

**ALS-A mapping:** Renewal is automatic in ALS-A; Model D maintains continuous eligibility so renewals succeed whenever checked. If the minimal passing trace is unique, Model D may collapse behaviorally with Model B; this is a substrate property, not a bug.

---

### Model E — Lazy Dictator

**(`LAZY_DICTATOR`)**

* Combines minimal compliance with continuous eligibility
* Uses fewest actions/steps that still pass all commitments

Purpose: maximal non-adaptive stress test of constitutional lapse and CTA.

**ALS-A mapping:** Under ALS-A, if minimal trace = unique passing trace, Models B/D/E collapse behaviorally. Telemetry distinguishes them by `steps_used_epoch` and `actions_emitted_epoch` where degrees of freedom exist.

---

## Configuration (RSAConfig)

```python
RSAConfig(
    rsa_enabled=False,
    rsa_model="NONE",   # NONE | ALWAYS_FAIL_COMMITMENT | MINIMAL_ELIGIBILITY_ONLY
                         # | FIXED_RENEWAL_TIMING | ALWAYS_SELF_RENEW | LAZY_DICTATOR
    rsa_rng_stream="rsa_v100",

    # Model A
    rsa_target_key=None,

    # Model C
    rsa_renewal_offset_epochs=0,
)
```

---

## Determinism Requirements (Frozen)

### Seed Derivation

```
seed_rsa = stable_hash_64(seed, "rsa", rsa_rng_stream)
```

* Stable across platforms
* No Python `hash()`
* No shared RNG state

---

### Stateless Policy Selection

All adversarial actions are:

* reproducible under identical seeds
* independent of run history
* free of internal memory beyond `epoch_index`

---

## Hook Semantics (Only Permitted Coupling)

RSA v1.0 intercepts **agent action selection only**.

AKI remains the sole authority over:

* eligibility computation
* renewal success
* lapse triggering
* CTA scheduling
* successor instantiation

RSA does **not** alter semantic evaluation outcomes directly.

---

## Metrics (Execution Addendum Compliance)

### Authority Availability (AA)

```
AUTH(epoch) = 1 if authority != NULL_AUTHORITY else 0
AA = mean(AUTH(epoch))
```

---

### Asymptotic Authority Availability (AAA)

```
tail_window = max(5000, horizon_epochs // 5)
AAA = mean(AUTH(epoch)) over tail_window
```

---

### Recovery Time Distribution (RTD)

Identical to v0.2.

---

### Entrenchment Diagnostics (Descriptive Only)

* Hollow Authority Duration
* Renewal Dominance Ratio
* Succession Count

No thresholds enforced in v1.0.

---

## Failure Classification (Frozen + Clarified)

All v0.2 failure classes apply unchanged.

### Additional v1.0-Relevant Failure

#### Irreversible Recovery Suppression (**Failure**)

Operational definition:

Let `W = tail_window`.

A run exhibits Irreversible Recovery Suppression iff:

```
CTA events occur within W
AND
No successful recovery occurs for > W epochs
```

despite unchanged kernel parameters and valid successor availability.

---

## RSA v1.0 Run Sequence

### Run 0 — Baseline (No Adversary)

* RSA disabled
* Identical horizon and seeds as Runs 1–5

Purpose: establish baseline authority survivability and recovery behavior for AKI v0.8.

---

### Run 1 — Persistent Violation

* Model: `ALWAYS_FAIL_COMMITMENT`
* Sweep: target commitment keys

---

### Run 2 — Minimal Compliance

* Model: `MINIMAL_ELIGIBILITY_ONLY`

---

### Run 3 — Fixed Timing Misuse

* Model: `FIXED_RENEWAL_TIMING`
* Sweep: renewal offsets

---

### Run 4 — Blind Succession Avoidance

* Model: `ALWAYS_SELF_RENEW`

---

### Run 5 — Lazy Dictator

* Model: `LAZY_DICTATOR`

---

## Telemetry (Required)

### Per Epoch

* epoch
* adversary_model
* action_emitted
* action_accepted
* commitments_satisfied
* authority_state
* steps_used_epoch
* actions_emitted_epoch
* budget_remaining_epoch

---

### Run Level

* AA / AAA
* RTD histogram
* hollow authority fraction
* renewal dominance ratio
* succession count
* failure_class

---

## v1.0 Completion Rule (Hard)

v1.0 is complete when either:

1. Any run produces **Terminal Collapse**, **Structural Thrashing**, or **Irreversible Recovery Suppression**, or
2. All runs converge to **Stable Authority** or **Bounded Degradation**

If (2):

> **Intentional fixed misuse alone is insufficient to defeat constitutional recovery under RSA assumptions.**

This conclusion is binding.

---

## Non-Claim (Explicit)

RSA v1.0 does **not** treat permanent authority capture, absent collapse or irreversibility, as a constitutional failure.

Questions of enforced rotation, legitimacy, or adaptive entrenchment are deferred to **RSA v2.0**.

---

## Acceptance Tests (Non-Negotiable)

1. RSA disabled equivalence
2. Fixed-policy determinism proof
3. No runtime branching audit
4. Kernel invariance audit

---

## Closure Statement

RSA v1.0 establishes the boundary at which **intent alone** ceases to be explanatory and **adaptive agency** becomes necessary.

Anything beyond this point belongs to **RSA v2.0**.

