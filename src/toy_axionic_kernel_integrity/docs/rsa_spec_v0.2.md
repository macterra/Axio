# Reflective Sovereign Agents (RSA)

A falsifiable experimental stress layer for AKI that injects **non-adaptive, post-verification, semantic-free interference** into end-of-epoch semantic verification **without modifying AKI’s constitutional mechanics**.

---

## Current Version: **v0.2 (RSA-SEI-0)**

**Structured Epistemic Interference Sweep**

RSA v0.2 generalizes v0.1’s verifier-outcome noise into a small family of **structured, non-adaptive interference processes** that operate strictly **after semantic verification** and strictly **inside the harness**.

### Locked Question (v0.2)

> **Can any non-adaptive, post-verification, semantic-free interference structure induce persistent constitutional failure while liveness is preserved?**

If no v0.2 run produces **Structural Thrashing** or **Asymptotic DoS** across preregistered parameter ranges, **epistemic unreliability is no longer a live explanation for governance collapse under RSA assumptions**.

This closes **v0.x**.

---

## What RSA v0.2 MUST NOT Change

*(Frozen AKI v0.8 Contract)*

RSA may not alter:

* Succession / renewal / enforcement logic
* Eligibility predicate or streak update rules
* Lapse + CTA semantics (`NULL_AUTHORITY`, amnesty schedule, decay)
* Commitment ledger rules or TTL behavior
* Candidate pool composition or successor types
* Evaluation timing (still only at epoch end + succession)
* Any semantic coupling beyond the existing end-of-epoch gate
* Any parameter tuning mid-run

RSA may alter **only the boolean results** already consumed by AKI.

---

## Inherited from AKI v0.8 (ALS-A)

RSA v0.2 runs on top of AKI v0.8 and therefore inherits:

* Authority leases
* Commitment ledger
* Eligibility gating
* Constitutional lapse (`NULL_AUTHORITY`)
* Constitutional Temporal Amnesty (CTA)
* Lapse cause classification + recovery tracking
* Expressivity classes + rent schedule

---

## Version History (RSA)

| Version  | Focus                             | Contribution                                                                  |
| -------- | --------------------------------- | ----------------------------------------------------------------------------- |
| **v0.1** | Governance DoS                    | Deterministic verifier-outcome noise + telemetry                              |
| **v0.2** | Structured epistemic interference | Correlated, burst, and aggregation-point interference with asymptotic metrics |

---

## Architecture (Additive)

```
toy_aki/
├── als/                    # Existing AKI harnesses (unchanged)
│   └── harness.py
├── rsa/
│   ├── adversary.py        # Stateless interference logic
│   ├── schedule.py         # Pure burst schedules (epoch-index only)
│   ├── metrics.py          # AA / AAA / RTD computation
│   ├── telemetry.py
│   └── config.py
└── scripts/
    ├── rsa_v020_run1_aggregation.py
    ├── rsa_v020_run2_commitment.py
    └── rsa_v020_run3_burst.py
```

RSA remains **removable** and **single-hook**.

---

## Non-Adaptive Constraint (Global, Frozen)

All interference decisions MUST be functions of:

```
(seed_rsa, epoch_index, static_key, static_schedule_params)
```

They MUST NOT depend on:

* Environment state
* Authority state
* Lapse history
* Renewal outcomes
* Successor identity
* Any run-history signal

Any interference keyed to runtime events or outcomes is **adaptive** and **out of scope** for v0.2.

---

## Interference Models (v0.2)

### Model A — Aggregation-Point Corruption

**(`AGG_FLIP_BERNOULLI`)**

* Individual `Ci_OK_raw` computed correctly
* Only `SEM_PASS_raw` eligible for flipping

Purpose: test whether aggregation is a structural choke point.

---

### Model B — Commitment-Correlated Noise

**(`COMMITMENT_KEYED_FLIP`)**

* Exactly one commitment key targeted (`C0`, `C1`, or `C2`)
* All other keys uncorrupted

Purpose: test recovery under persistent obligation loss.

---

### Model C — Burst-Scheduled Interference

**(`BURST_SCHEDULED_FLIP`)**

* Fixed periodic burst schedule
* Burst state = function of `(epoch_index, schedule_params)` only
* No event anchoring of any kind

Purpose: test vulnerability to temporal synchronization.

---

## Configuration (RSAConfig)

```python
RSAConfig(
    rsa_enabled=False,
    rsa_model="NONE",   # NONE | AGG_FLIP_BERNOULLI | COMMITMENT_KEYED_FLIP | BURST_SCHEDULED_FLIP
    rsa_scope="SEM_PASS_ONLY",
    rsa_rng_stream="rsa_v020",

    # Model A
    rsa_p_flip_ppm=0,

    # Model B
    rsa_target_key=None,
    rsa_p_target_flip_ppm=0,

    # Model C (PERIODIC ONLY)
    rsa_burst_period_epochs=0,
    rsa_burst_width_epochs=0,
    rsa_burst_phase_offset=0,
    rsa_p_burst_flip_ppm=0,
    rsa_p_quiet_flip_ppm=0,
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

### Stateless Flip Decision

```
u64 = stable_hash_64(seed_rsa, epoch, key_name, model_tag)
flip = (u64 % 1_000_000) < p_effective_ppm
```

Ordering-independent, history-free.

---

## Hook Semantics (Only Permitted Coupling)

AKI computes:

* `C0_OK_raw`, `C1_OK_raw`, `C2_OK_raw`
* `SEM_PASS_raw`

### SEM_PASS_ONLY

```
SEM_PASS = maybe_corrupt(SEM_PASS_raw)
```

---

### PER_KEY (Frozen Aggregation Rule)

RSA corrupts selected keys only:

```
Ck_OK = maybe_corrupt(Ck_OK_raw)   # enabled keys
Ci_OK = Ci_OK_raw                 # others
```

**SEM_PASS MUST then be recomputed from post-interference keys:**

```
SEM_PASS = AGGREGATE(C0_OK, C1_OK, C2_OK)
```

`SEM_PASS_raw` MUST NOT be used downstream in `PER_KEY` mode.

---

## Metrics (Execution Addendum Compliance)

### Authority Availability (AA)

```
AUTH(epoch) = 1 if authority != NULL_AUTHORITY else 0
AA = mean(AUTH(epoch))
```

Reported as PPM.

---

### Asymptotic Authority Availability (AAA)

**Frozen rule:**

```
tail_window = max(5000, horizon_epochs // 5)
AAA = mean(AUTH(epoch)) over tail_window
```

---

### Recovery Time Distribution (RTD)

* A lapse = contiguous NULL_AUTHORITY interval
* Recovery time = lapse length (epochs)

Bucketed histogram (frozen):

```
1, 2, 3, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, INF
```

---

## Failure Classification (Frozen)

Each run MUST conclude with exactly one label:

### Stable Authority

* High AAA
* Rare, short lapses
* No heavy-tailed RTD

### Bounded Degradation

* AAA reduced but > 0
* Lapses recur but RTD bounded

### Structural Thrashing (**Failure**)

* Persistent oscillation
* AAA → 0
* RTD heavy-tailed

### Asymptotic DoS (**Failure**)

* Lapse dominance in tail window
* Recoveries exist but negligible

### Terminal Collapse (**Failure, strict subset**)

Operational definition:

Let `tail_window` be the AAA window.

Terminal Collapse occurs iff:

```
∃ t* ≤ horizon - tail_window
such that AUTH(epoch) = 0 for all epoch ∈ [t*, horizon)
```

---

## RSA v0.2 Run Sequence

### Run 1 — Aggregation-Point Corruption

* Model: `AGG_FLIP_BERNOULLI`
* Scope: `SEM_PASS_ONLY`
* Sweep: `p_flip_ppm ∈ [0 … 20_000]`

---

### Run 2 — Commitment-Correlated Noise

* Model: `COMMITMENT_KEYED_FLIP`
* Target one key only
* Sweep: `p_target_flip_ppm`

**Classification rule (k-aware, frozen):**

* If eligibility threshold `k` tolerates loss of target key and AAA remains high → **Stable Authority**
* Degradation only if AAA drops materially
* Thrashing only if AAA → 0

---

### Run 3 — Burst-Scheduled Interference

* Model: `BURST_SCHEDULED_FLIP`
* PERIODIC schedule only
* Sweep over `(period, width, phase, p_burst)`

---

## Telemetry (Required)

### Per Epoch

* epoch
* phase (`ACTIVE` / `QUIET`)
* targets
* flips
* flips_by_key
* p_effective_ppm

---

### Run Level

* total_flips / total_targets
* observed_flip_rate_ppm
* **burst_duty_cycle_ppm**
* **active_phase_flip_rate_ppm**
* AA / AAA
* RTD histogram
* failure_class

---

## v0.2 Completion Rule (Hard)

v0.2 is complete when either:

1. Any run produces **Structural Thrashing** or **Asymptotic DoS**, or
2. All runs converge to **Stable Authority** or **Bounded Degradation**

If (2):

> **Epistemic interference alone is insufficient to defeat constitutional recovery under RSA assumptions.**

This conclusion is binding.

---

## Acceptance Tests (Non-Negotiable)

1. RSA disabled equivalence
2. Enabled with zero probability equivalence
3. Flip firing proof
4. Burst schedule determinism

---

