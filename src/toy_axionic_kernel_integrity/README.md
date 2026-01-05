# Toy Axionic Kernel Integrity (AKI)

A falsifiable experimental system implementing kernel integrity under actuation, targeting alignment properties from the Axionic Agency framework.

## Current Version: v0.8 (ALS-A)

**Authority Leases with Constitutional Temporal Amnesty**

AKI v0.8 introduces Constitutional Temporal Amnesty (CTA): a deterministic, time-only rule that applies exclusively during `NULL_AUTHORITY` to enable eligibility recovery without semantic optimization. This is the first mechanism in the AKI series that modifies streak state during lapse.

### Key Features (v0.8)

- **Constitutional Temporal Amnesty (CTA):** Time-only streak decay during NULL_AUTHORITY
- **AMNESTY_INTERVAL:** Configurable epochs between amnesty applications (default: 10)
- **AMNESTY_DECAY:** Streak decrement per amnesty (default: 1)
- **Lapse Cause Classification:** SEMANTIC vs STRUCTURAL lapse detection
- **Recovery Tracking:** Authority span measurement, stutter detection, recovery yield
- **100% Recovery Rate:** All lapses recovered in baseline geometry

See [spec_v0.8.md](docs/spec_v0.8.md) and [instructions_v0.8_runnerA.md](docs/instructions_v0.8_runnerA.md)

### Inherited from v0.7 (ALS-G)

- **Eligibility Gating:** Filter candidates based on semantic fail streak
- **Stable Policy Identity:** `policy_id` keyed to enum name, not runtime instance
- **Constitutional Lapse:** NULL_AUTHORITY state when C_ELIG = ∅
- **K=3 Threshold:** Default eligibility threshold

### Inherited from v0.6 (ALS-C)

- **Commitment Ledger:** Kernel-owned persistent ledger of semantic obligations
- **Obligation Survivability:** Commitments persist across epochs, renewals, and succession
- **Competence Independence:** Authority can be renewable yet incompetent, or competent yet non-renewable

### Inherited from v0.5.2 (ALS-E)

- **Expressivity Classes (E0-E4):** Hierarchical capability levels from heartbeat-only to full API
- **Rent Schedule:** Steps deducted at epoch start based on E-Class
- **CBD Detection:** Compliant-But-Dangerous successor patterns

## Version History

| Version | Focus | Key Contribution |
|---------|-------|------------------|
| v0.1.x | Kernel integrity | K0-K7 invariants, ACV protocol |
| v0.2.x | Recomposition | Sovereign actuation, P2' verification |
| v0.3.x | Pre-registration | H=10,000 horizon experiments |
| v0.4.x | Authority Leases (ALS) | Lease lifecycle, S* counting, succession |
| v0.5.2 | Expressivity (ALS-E) | Rent schedule, E-Classes, boundary finding |
| v0.6 | Commitments (ALS-C) | Commitment Ledger, obligation survivability |
| v0.7 | Eligibility (ALS-G) | Eligibility gating, streak tracking, constitutional lapse |
| v0.8 | Amnesty (ALS-A) | Constitutional Temporal Amnesty, lapse recovery, stutter detection |
| **RSA v0.1** | Robustness (RSA) | Synthetic verifier noise, DoS threshold testing, 2D robustness surface |

## Installation

```bash
# From the project root
pip install -e .
```

## Quick Start

### Run RSA v0.1 Experiments (Robustness Sensitivity Analysis)

```bash
# Run 0: Baseline validation (no noise)
python scripts/rsa_run0_baseline_v010.py

# Run 1: SV baseline sweep (5 SV levels × 5 seeds, fixed 10% RSA)
python scripts/rsa_run1_sv_baseline_sweep_v010.py

# Run 2: 2D robustness surface (5 SV × 5 RSA × 5 seeds = 125 runs)
python scripts/rsa_run2_surface_sweep_v010.py

# Run 3: DoS threshold search (30-60% noise at SV=800k)
python scripts/rsa_run3_dos_threshold_v010.py
```

### Run v0.8 Experiments

```bash
# Run A: CTA baseline (AMNESTY_INTERVAL=10)
python scripts/run_a_v080.py

# Run B: Interval sensitivity (AMNESTY_INTERVAL=5)
python scripts/run_b_v080.py
```

### Run v0.7 Experiments

```bash
# Run A: Eligibility-coupled succession baseline
python scripts/run_a_v070.py
```

### Run v0.6 Experiments

```bash
# Run A: Basic ALS-C validation
python scripts/run_a_v060.py

# Run B: Commitment ledger persistence
python scripts/run_b_v060.py

# Run C: Obligation satisfaction tracking
python scripts/run_c_v060.py

# Run D: Boundary hugging
python scripts/run_d_v060.py
```

### Run v0.5.2 Experiments

```bash
# Run F: Basic ALS-E validation
python scripts/run_f_v052.py

# Run G: Competitive expressivity horizon
python scripts/run_g_v052.py

# Run H: Boundary-finding escalation
python scripts/run_h_v052.py

# Run I: Rubber-stamp degeneracy (no forced succession)
python scripts/run_i_v052.py

# Run J: Expressivity-rent boundary identification
python scripts/run_j_v052.py

# Run J2: Renewal-timing sensitivity
python scripts/run_j2_v052.py

# Run K: Succession geometry sweep
python scripts/run_k_v052.py
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run v0.8 tests
pytest tests/test_v080.py -v

# Run v0.7 tests
pytest tests/test_v070.py -v

# Run v0.6 tests
pytest tests/test_v060.py -v

# Run with coverage
pytest --cov=toy_aki tests/
```

## Architecture

```
toy_aki/
├── als/             # Authority Lease System (v0.4+)
│   ├── harness.py   # ALSHarnessV052, V060, V070, V080
│   ├── expressivity.py  # E-Classes, RentSchedule
│   ├── commitment.py    # Commitment Ledger (v0.6+)
│   ├── generator.py # Successor generation, policy_id tracking
│   ├── successors.py    # CBD and attack successors
│   └── working_mind.py  # Working mind abstraction
├── rsa/             # Robustness Sensitivity Analysis (RSA v0.1)
│   └── synthetic_verifier.py  # ALSHarnessV080_SV, SVConfig, noise models
├── common/          # Utilities: hashing, JSON, no-floats
├── env/             # ToyWorld environment
├── acv/             # Anchor-Commit-Verify protocol
├── kernel/          # Kernel components (v0.1-v0.3)
├── agents/          # Agent implementations
├── attacks/         # Attack payloads (v0.2+)
└── harness/         # Test harnesses
```

## v0.8 Constitutional Temporal Amnesty

### Key Concepts

- **CTA:** Constitutional Temporal Amnesty — deterministic streak decay during NULL_AUTHORITY
- **AMNESTY_INTERVAL:** Epochs between amnesty applications (default: 10)
- **AMNESTY_DECAY:** Streak decrement per amnesty event (default: 1)
- **Lapse Cause:** SEMANTIC (candidates exist but ineligible) vs STRUCTURAL (no candidates)
- **Recovery:** Exit from NULL_AUTHORITY when C_ELIG ≠ ∅
- **Stutter:** Recovery lasting ≤ 1 epoch before next lapse
- **Recovery Yield (RY):** authority_epochs / lapse_epochs

### Configuration

```python
from toy_aki.als.harness import ALSConfigV080, ALSHarnessV080

config = ALSConfigV080(
    max_cycles=5_000,
    eligibility_threshold_k=3,
    max_successive_renewals=3,  # Forced turnover
    amnesty_interval=10,        # CTA fires every 10 epochs
    amnesty_decay=1,            # Decrement by 1 per amnesty
    cta_enabled=True,           # Can disable for comparison
)

harness = ALSHarnessV080(seed=42, config=config)
result = harness.run()

# Check amnesty events
print(f"Amnesty events: {result.amnesty_event_count}")
print(f"Total streak decay: {result.total_streak_decay_applied}")

# Check recovery metrics
print(f"Recoveries: {result.recovery_count}")
print(f"Stutter recoveries: {result.stutter_recovery_count}")
print(f"Authority uptime: {result.authority_uptime_fraction:.1%}")
```

### Experimental Results (v0.8)

| Run | AMNESTY_INTERVAL | Long-Lapse Mode | NULL_AUTH Reduction | Key Finding |
|-----|-----------------|-----------------|---------------------|-------------|
| A | 10 epochs | L ≈ 20 | Baseline | 100% recovery, 0% stutter, 69% recover without amnesty |
| B | 5 epochs | L ≈ 10 | -43% | CTA clock governs lapse duration |

## RSA v0.1: Robustness Sensitivity Analysis

### Overview

RSA v0.1 tests AKI v0.8 robustness under synthetic verifier noise. The kernel is **frozen**; only the test harness introduces perturbations via a configurable Synthetic Verifier (SV) that corrupts semantic pass/fail signals.

### Key Concepts

- **Synthetic Verifier (SV):** Replaces deterministic semantic verifier with probabilistic baseline + RSA noise
- **SV Baseline:** Base probability of semantic pass (e.g., 800k PPM = 80%)
- **RSA Noise:** Post-verification Bernoulli flip rate applied per-Ci
- **DoS Threshold:** `max_single_lapse_epochs > 50` (5× amnesty_interval)
- **Authority Uptime:** Fraction of epochs with active authority
- **Pivotal Rate:** Fraction of CI events where noise affected semantic outcome

### Noise Model

```python
from toy_aki.rsa.synthetic_verifier import SVConfig, RSANoiseModel, RSAScope

config = SVConfig(
    semantic_pass_probability_ppm=800_000,  # 80% baseline
    rsa_noise_ppm=100_000,                  # 10% flip rate
    rsa_noise_model=RSANoiseModel.FLIP_BERNOULLI,
    rsa_scope=RSAScope.PER_CI,
)
```

### Experimental Results (RSA v0.1)

| Run | Focus | Runs | Key Finding |
|-----|-------|------|-------------|
| 0 | Baseline validation | 5 | 100% uptime, zero lapses (no noise) |
| 1 | SV baseline sweep | 25 | All ROBUST at 10% noise; regime transition at ~30% baseline |
| 2 | 2D surface mapping | 125 | All 125 cells ROBUST across 5×5 grid |
| 3 | DoS threshold search | 20 | No DoS up to 60% noise; graceful degradation with 74-94% uptime |

**Key Finding:** Under PER_CI FLIP_BERNOULLI noise at SV=800k (~51% effective baseline), no DoS observed up to 60% flip rate. CTA enables recovery even under extreme noise.

## v0.7 Eligibility Gating

### Key Concepts

- **policy_id:** Stable identifier per policy class (e.g., `"control:COMPLIANCE_ONLY"`, `"attack:CBD"`)
- **semantic_fail_streak:** Per-policy_id counter, incremented on semantic failure, reset on success
- **K (eligibility_threshold_k):** Threshold; streak >= K excludes candidate from C_ELIG
- **C_ELIG:** Eligible candidate pool = { c ∈ C_POOL | streak[c.policy_id] < K }
- **NULL_AUTHORITY:** Constitutional lapse state when C_ELIG = ∅

### Configuration

```python
from toy_aki.als.harness import ALSConfigV070, ALSHarnessV070

config = ALSConfigV070(
    max_cycles=10_000,
    eligibility_threshold_k=3,  # K=3 default
)

harness = ALSHarnessV070(seed=42, config=config)
result = harness.run()

# Check eligibility events
for event in result.eligibility_events:
    print(f"Excluded {event.policy_id} at epoch {event.epoch} (streak={event.streak_value})")

# Check for lapses
print(f"Total lapse cycles: {result.total_lapse_cycles}")
print(f"Lapse count: {result.lapse_count}")
```

## v0.5.2 Expressivity Classes

| E-Class | Name | Rent (S=100) | Effective Steps |
|---------|------|--------------|-----------------|
| **E0** | Heartbeat | 1 | 99 |
| **E1** | Logging | 10 | 90 |
| **E2** | State Mutation | 25 | 75 |
| **E3** | Fanout/Composition | 40 | 60 |
| **E4** | Full API Surface | 60 | 40 |

### Rent Charging

```python
from toy_aki.als.expressivity import RentSchedule, ExpressivityClass

schedule = RentSchedule(steps_cap_epoch=100)
rent = schedule.compute_rent(ExpressivityClass.E3)  # 40
effective = schedule.compute_effective_steps(ExpressivityClass.E3)  # 60
```

## Experiment Results

### Summary of Key Findings (v0.5.2)

| Run | Focus | Key Finding |
|-----|-------|-------------|
| **H** | Boundary finding | Renewal cost = 10 causes collapse at E3 |
| **I** | No forced succession | Rubber-stamp degeneracy (authority never changes) |
| **J** | Rent boundary | Sharp boundary at 48% E3 rent |
| **J2** | Timing sensitivity | Boundary is timing-dependent (epoch/check resonance) |
| **K** | Succession geometry | Forced succession is necessary but not sufficient |

### Run K: Succession Geometry (Latest)

| max_successive_renewals | Regime | Outcome |
|-------------------------|--------|--------|
| ∞ | LOCK_IN | Authority frozen permanently |
| 100 | CONSTITUTIONAL_STABILITY | Diverse succession, horizon reached |
| 15, 3 | STASIS_UNDER_TURNOVER | Behavioral homogeneity, not thrash |

**Key Finding:** Forced succession is necessary to prevent lock-in, but does not guarantee institutional diversity.

### Run J: Rent Boundary

- Sharp boundary at **48% E3 rent** (between 47% and 48%)
- At 47%: remaining_budget ≥ renewal_cost → renew succeeds
- At 48%: remaining_budget < renewal_cost → bankruptcy

### Run J2: Timing Sensitivity

The 48% boundary is a **resonance artifact**, not intrinsic:
- Epoch-aligned checks (interval=100) → collapse
- Off-epoch checks (interval=50 or 90) → stable

See [reports/IMPLEMENTATION_REPORT_V052.md](reports/IMPLEMENTATION_REPORT_V052.md) for full analysis.

## Authority Lease System (v0.4+)

### Core Concepts

- **Working Mind:** Active agent operating under a lease
- **Lease:** Time-bounded permission to operate
- **Renewal:** Periodic attestation to continue lease
- **Succession:** Transfer of authority to a new working mind
- **S* (S-Star):** Count of non-trivial (manifest-changing) successions

### Lease Lifecycle

```
PROPOSE → ENDORSE → ACTIVE → [RENEW]* → EXPIRE/REVOKE
```

### Configuration

```python
from toy_aki.als.harness import ALSConfigV052, ALSHarnessV052

config = ALSConfigV052(
    max_cycles=30_000,
    renewal_check_interval=100,
    msrw_cycles=200,  # Max successive renewal window
    rent_e3=60,       # Optional: override E3 rent
    renewal_cost_steps=10,  # Optional: charge at renewal
)

harness = ALSHarnessV052(seed=42, config=config)
result = harness.run()
```

## Legacy Features (v0.1-v0.3)

### Invariants (K0-K7)

| Invariant | Description |
|-----------|-------------|
| **K0** | Proposal hash integrity |
| **K1** | Trace commitment verification |
| **K2** | Policy digest matching |
| **K3** | Forbidden class enforcement |
| **K4** | ACV temporal ordering |
| **K5** | ACV commitment verification |
| **K6** | Coupling pattern binding |
| **K7** | Audit chain integrity |

### Coupling Patterns

- **Pattern A:** Merkle tree openings (granular)
- **Pattern B:** Global mix hash (simple)
- **Pattern C:** Transition rules (structural)

## Documentation

### Specifications

- [spec_v0.8.md](docs/spec_v0.8.md) - v0.8 specification (ALS-A: Constitutional Temporal Amnesty)
- [spec_v0.7.md](docs/spec_v0.7.md) - v0.7 specification (ALS-G: Eligibility Gating)
- [spec_v0.6.md](docs/spec_v0.6.md) - v0.6 specification (ALS-C)
- [spec_v0.5.2.md](docs/spec_v0.5.2.md) - v0.5.2 specification (ALS-E)

### Implementation Instructions

- [instructions_v0.8_runnerA.md](docs/instructions_v0.8_runnerA.md) - v0.8 Run A (CTA baseline)
- [instructions_v0.8_runnerB.md](docs/instructions_v0.8_runnerB.md) - v0.8 Run B (interval sensitivity)
- [instructions_v0.7.md](docs/instructions_v0.7.md) - v0.7 ALS-G implementation
- [instructions_v0.6.md](docs/instructions_v0.6.md) - v0.6 ALS-C implementation
- [instructions_v0.6_runnerBCD.md](docs/instructions_v0.6_runnerBCD.md) - v0.6 experiment runners
- [instructions_v0.5.2_runnerH.md](docs/instructions_v0.5.2_runnerH.md) - Run H boundary finding
- [instructions_v0.5.2_runnerI.md](docs/instructions_v0.5.2_runnerI.md) - Run I rubber-stamp test
- [instructions_v0.5.2_runnerJ.md](docs/instructions_v0.5.2_runnerJ.md) - Run J rent boundary
- [instructions_v0.5.2_runnerK.md](docs/instructions_v0.5.2_runnerK.md) - Run K succession geometry

### Reports

- [rsa_v010_run0_implementation_report.md](reports/rsa_v010_run0_implementation_report.md) - RSA v0.1 Run 0 (baseline validation)
- [rsa_v010_run1_implementation_report.md](reports/rsa_v010_run1_implementation_report.md) - RSA v0.1 Run 1 (SV baseline sweep)
- [rsa_v010_run2_implementation_report.md](reports/rsa_v010_run2_implementation_report.md) - RSA v0.1 Run 2 (2D surface mapping)
- [rsa_v010_run3_implementation_report.md](reports/rsa_v010_run3_implementation_report.md) - RSA v0.1 Run 3 (DoS threshold search)
- [IMPLEMENTATION_REPORT_V08.md](reports/IMPLEMENTATION_REPORT_V08.md) - v0.8 ALS-A report
- [run_a_v080_report.md](reports/run_a_v080_report.md) - v0.8 Run A report
- [run_b_v080_report.md](reports/run_b_v080_report.md) - v0.8 Run B report
- [IMPLEMENTATION_REPORT_V07.md](reports/IMPLEMENTATION_REPORT_V07.md) - v0.7 ALS-G report
- [run_l_v060_report.md](docs/run_l_v060_report.md) - v0.6 experiment report
- [IMPLEMENTATION_REPORT_V052.md](reports/IMPLEMENTATION_REPORT_V052.md) - v0.5.2 report
- [IMPLEMENTATION_REPORT_V042.md](reports/IMPLEMENTATION_REPORT_V042.md) - ALS foundation
- [IMPLEMENTATION_REPORT_V043.md](reports/IMPLEMENTATION_REPORT_V043.md) - ALS refinements
- [IMPLEMENTATION_REPORT.md](reports/IMPLEMENTATION_REPORT.md) - Original v0.1 report

## Running Tests

```bash
# All tests
pytest tests/

# Version-specific suites
pytest tests/test_v080.py -v  # v0.8: ALS-A constitutional temporal amnesty
pytest tests/test_v070.py -v  # v0.7: ALS-G eligibility gating
pytest tests/test_v060.py -v  # v0.6: ALS-C commitments
pytest tests/test_v052.py -v  # v0.5.2: ALS-E expressivity
pytest tests/test_v043.py -v  # v0.4.3: ALS tests
pytest tests/test_v042.py -v  # v0.4.2: ALS foundation
pytest tests/test_v032.py -v  # v0.3.2: H=10,000 experiments
pytest tests/test_v022.py -v  # v0.2.2: Gap closure
```

## Design Principles

### No-Floats Rule

All numeric values in hashed objects must be integers:

```python
from toy_aki.common.no_floats import to_scaled_int, from_scaled_int

scaled = to_scaled_int(3.14159)  # 314159000
value = from_scaled_int(scaled)  # 3.14159
```

### Canonical JSON

Deterministic serialization for hash stability:

```python
from toy_aki.common.canonical_json import canonical_json

canonical = canonical_json({"b": 2, "a": 1})  # '{"a":1,"b":2}'
```

## License

See [LICENSE](../../LICENSE) for details.

## References

- Axionic Agency papers (I.1-VI.2)
- Structural Alignment papers

