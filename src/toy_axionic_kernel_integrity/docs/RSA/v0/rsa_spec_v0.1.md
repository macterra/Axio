# Reflective Sovereign Agents (RSA)

A falsifiable experimental stress layer for AKI that injects **adversarial epistemic noise** into end-of-epoch semantic verification **without modifying AKI’s constitutional mechanics**.

## Current Version: v0.1 (RSA-DoS-0)

**Verifier-Outcome Noise Injection (Governance DoS Stress)**

RSA v0.1 adds a removable “fault-injection harness” that perturbs semantic verifier outcomes (per-commitment or aggregate `SEM_PASS`) using a **deterministic, action-independent** noise process. This tests whether AKI’s constitutional recovery mechanisms (especially CTA under `NULL_AUTHORITY`) remain functional when semantic evaluation is unreliable.

### Key Features (v0.1)

* **Strict Additivity:** RSA is an optional layer; when disabled, behavior is identical to AKI v0.8.
* **Verifier Outcome Corruption:** Deterministically flips verifier booleans (`Ci_OK` and/or `SEM_PASS`) under a configured noise model.
* **Determinism + Stream Separation:** RSA uses an independent RNG stream derived from the run seed, avoiding contamination of sampling trajectories.
* **Attack Telemetry:** Per-epoch and run-level telemetry proving perturbations fired and quantifying observed vs target flip rate.
* **Governance DoS Stress:** Directly increases semantic false-negative/false-positive rates to test lapse frequency, lapse duration, and recovery yield.

See `docs/spec_rsa_v0.1.md` and `docs/instructions_rsa_v0.1_run0.md`

---

## What RSA v0.1 MUST NOT Change (Frozen AKI v0.8 contract)

* Succession / renewal / enforcement logic
* Eligibility predicate and streak update rules
* Lapse + CTA semantics (`NULL_AUTHORITY`, amnesty schedule, decay)
* Commitment ledger rules and TTL behavior
* Candidate pool composition and successor types
* Evaluation timing (still only at epoch end + succession)
* Any semantic coupling beyond the existing end-of-epoch gate

RSA may only alter **the boolean result** that downstream AKI logic already consumes.

---

## Inherited from AKI v0.8 (ALS-A)

RSA v0.1 runs on top of AKI v0.8 and therefore inherits:

* **Authority Leases**
* **Commitment Ledger**
* **Eligibility Gating**
* **Constitutional Lapse (`NULL_AUTHORITY`)**
* **Constitutional Temporal Amnesty (CTA)**
* **Lapse cause classification + recovery tracking**
* **Expressivity classes + rent schedule**

---

## Version History (RSA)

| Version  | Focus          | Key Contribution                                                              |
| -------- | -------------- | ----------------------------------------------------------------------------- |
| **v0.1** | Governance DoS | Deterministic verifier-outcome noise injection + telemetry + acceptance tests |

---

## Installation

```bash
# From the project root
pip install -e .
```

---

## Quick Start

### Run RSA v0.1 Experiments (Run 0: Governance DoS)

```bash
# Baseline equivalence (RSA disabled)
python scripts/rsa_v010_run0_baseline_equivalence.py

# RSA DoS sweep (noise on)
python scripts/rsa_v010_run0_dos_sweep.py
```

### Run Tests

```bash
pytest tests/

# RSA-specific suite
pytest tests/test_rsa_v010.py -v
```

---

## Architecture (Additive)

```
toy_aki/
├── als/                 # Existing AKI ALS harnesses (unchanged)
│   └── harness.py       # ALSHarnessV080 (unchanged logic; contains RSA hook point)
├── rsa/                 # NEW: RSA stress layer (additive)
│   ├── adversary.py     # RSAAdversary (noise models, deterministic corruption)
│   ├── config.py        # RSAConfig (defaults off)
│   └── telemetry.py     # RSA telemetry structs + aggregation
└── scripts/
    ├── rsa_v010_run0_baseline_equivalence.py
    └── rsa_v010_run0_dos_sweep.py
```

---

## RSA v0.1 Verifier-Outcome Noise Injection

### Key Concepts

* **Verifier Outcome:** Boolean results produced at epoch end: `C0_OK`, `C1_OK`, `C2_OK`, and/or `SEM_PASS`.
* **Corruption Hook:** A single post-verification hook that may flip these booleans.
* **Action Independence:** Corruption probability cannot depend on agent behavior, logs, candidate identity, or environment state.
* **Stream Independence:** RSA randomness must be isolated from any RNG used for candidate sampling or other AKI processes.
* **Determinism:** Given the same seed and config, flips occur at identical epochs and on identical variables.

### Noise Models

* `NONE`: No corruption.
* `FLIP_BERNOULLI`: Flip boolean with probability `p_flip`.

### Fixed-Point Probability

No floats in hashed/configured objects. Use **PPM** (parts-per-million):

* `rsa_p_flip_ppm ∈ [0, 1_000_000]`
* Example: 1% = `10_000`, 0.1% = `1_000`

### Scope (where corruption applies)

* `PER_CI`: corrupt each `Ci_OK` independently (recommended; highest diagnostic value)
* `SEM_PASS_ONLY`: corrupt only the aggregate `SEM_PASS` (minimal surface area)

---

## Configuration

### RSAConfig (additive)

```python
from toy_aki.rsa.config import RSAConfig

rsa = RSAConfig(
    rsa_enabled=False,             # default off
    rsa_noise_model="NONE",        # or "FLIP_BERNOULLI"
    rsa_p_flip_ppm=0,              # 0..1_000_000
    rsa_scope="PER_CI",            # or "SEM_PASS_ONLY"
    rsa_rng_stream="rsa",          # label included in seed derivation
)
```

### Combined Harness Config Example

```python
from toy_aki.als.harness import ALSConfigV080, ALSHarnessV080
from toy_aki.rsa.config import RSAConfig

als = ALSConfigV080(
    max_cycles=5_000,
    eligibility_threshold_k=3,
    max_successive_renewals=3,
    amnesty_interval=10,
    amnesty_decay=1,
    cta_enabled=True,
)

rsa = RSAConfig(
    rsa_enabled=True,
    rsa_noise_model="FLIP_BERNOULLI",
    rsa_p_flip_ppm=10_000,  # 1%
    rsa_scope="PER_CI",
)

h = ALSHarnessV080(seed=42, config=als, rsa=rsa)  # rsa param optional
result = h.run()

print(result.rsa.total_flips)
print(result.rsa.observed_flip_rate_ppm)
```

**Contract:** `rsa` must be optional; absent or disabled must be identical to AKI v0.8.

---

## Determinism Requirements

### Seed Derivation

Derive RSA seed from the run seed and a constant label:

* `seed_rsa = stable_hash_64(seed, "rsa", rsa_rng_stream)`

Rules:

* Must be stable across runs and Python versions.
* Must not use Python’s randomized `hash()`.
* Must not share RNG state with candidate sampling or any other harness RNG.

### Stateless Flip Decision (preferred)

To avoid ordering sensitivity, make flip decisions stateless:

* `u64 = stable_hash_64(seed_rsa, epoch, ci_name, stage)`
* `flip = (u64 % 1_000_000) < rsa_p_flip_ppm`

This guarantees:

* no dependence on loop ordering
* no accidental coupling to trajectory

---

## Hook Semantics (the only permitted coupling point)

Let AKI compute raw commitment checks as usual:

* `C0_OK_raw`, `C1_OK_raw`, `C2_OK_raw`
* `SEM_PASS_raw`

RSA then applies corruption *only to the booleans*:

### PER_CI scope

* `C0_OK = maybe_corrupt(C0_OK_raw, epoch, "C0")`
* `C1_OK = maybe_corrupt(C1_OK_raw, epoch, "C1")`
* `C2_OK = maybe_corrupt(C2_OK_raw, epoch, "C2")`
* `SEM_PASS = C0_OK ∧ C1_OK ∧ C2_OK`

### SEM_PASS_ONLY scope

* `SEM_PASS = maybe_corrupt(SEM_PASS_raw, epoch, "SEM_PASS")`

**Hard constraint:** RSA must not change evaluation timing or any downstream AKI logic.

---

## Telemetry (required for credibility)

RSA must record:

### Per Epoch

* `epoch`
* `targets` (# booleans eligible for corruption this epoch)
* `flips` (# flips that occurred)
* `by_key`: `{ "C0": flips, "C1": flips, "C2": flips }` if `PER_CI`
* `p_flip_ppm`
* `seed_rsa_digest` (optional; or full seed if you prefer)

### Run Level

* `total_targets`
* `total_flips`
* `observed_flip_rate_ppm = total_flips * 1_000_000 // total_targets`
* `expected_flip_rate_ppm = rsa_p_flip_ppm`
* `enabled`, `noise_model`, `scope`

---

## RSA v0.1 Run 0: Governance DoS Stress Test

### Purpose

Measure how robust AKI v0.8’s governance recovery is when semantic verification becomes unreliable, inducing ineligibility cascades and `NULL_AUTHORITY` lapses.

### Independent Variable

* `rsa_p_flip_ppm` sweep

Recommended sweep (PPM):

* `0, 200, 500, 1_000, 2_000, 5_000, 10_000, 20_000`
  (0% … 2%)

### Controls

* Same AKI v0.8 config as baseline CTA runs (including forced turnover).
* Fixed seed set (e.g., `[40..44]` or your standard battery).
* RSA enabled only via config; no changes to successor pool or environment.

### Primary Metrics

* **Lapse frequency:** `lapse_count`, `total_lapse_epochs`
* **Mean lapse duration** and **tail behavior** (long-lapse mode)
* **Recovery rate:** fraction of lapses that recover within horizon
* **Recovery yield (RY):** `authority_epochs / lapse_epochs`
* **Stutter rate:** recoveries lasting ≤ 1 epoch before re-lapse
* **Eligibility exhaustion:** epochs where `C_ELIG = ∅` due to semantic streaking

### RSA-Specific Metrics

* `observed_flip_rate_ppm` vs `expected`
* flips by commitment key (`C0/C1/C2`)

### Outcome Classification (Run 0)

* **ROBUST:** recovery rate ~100%, modest RY degradation
* **DEGRADED:** recovery remains high but long-lapse mode grows / RY collapses
* **DoS REGIME:** sustained `NULL_AUTHORITY` dominance, repeated non-recovery windows, or recovery only via extreme amnesty accumulation

Stop rules (per run):

* If `NULL_AUTHORITY` persists continuously for > X epochs (choose X relative to amnesty interval; e.g., `5 * amnesty_interval`), flag as DoS regime.

---

## Acceptance Tests (non-negotiable)

1. **RSA disabled equivalence**

   * Baseline AKI v0.8 run with `rsa_enabled=False`
   * Same run with RSA code present and still disabled
   * Must match on all AKI invariants and (ideally) identical traces

2. **p_flip=0 equivalence**

   * `rsa_enabled=True`, `rsa_p_flip_ppm=0`
   * Must match baseline exactly (catches “enabled path” contamination)

3. **Flip firing proof**

   * `rsa_p_flip_ppm` set to a high value (e.g., 50_000 = 5%) for a short run
   * Confirm `total_flips > 0` and observed rate near expected

---

## Design Principles

### Removable Harness

RSA must be removable without touching AKI mechanics. Concretely:

* RSA code lives in `toy_aki/rsa/`
* AKI harness only imports RSA conditionally or via an optional dependency boundary
* One hook site; no spread of RSA logic into eligibility/renewal/succession

### No-Floats Rule

All configured probabilities are integers (PPM). Any derived rates recorded as ints.

### Epistemic Attack Hygiene

RSA v0.1 injects noise **after** semantic evaluation. It is explicitly not an oracle/input perturbation layer; that arrives in a later RSA version.

---

## Documentation

### Specifications

* `docs/spec_rsa_v0.1.md` — RSA v0.1 specification (this document)
* `docs/instructions_rsa_v0.1_run0.md` — implementor instructions + run template

### Reports

* `reports/rsa_v010_run0_report.md` — DoS sweep results + telemetry summary

---
