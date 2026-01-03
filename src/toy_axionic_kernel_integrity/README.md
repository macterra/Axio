# Toy Axionic Kernel Integrity (AKI)

A falsifiable experimental system implementing kernel integrity under actuation, targeting alignment properties from the Axionic Agency framework.

## Current Version: v0.5.2 (ALS-E)

**Authority Leases with Expressivity-Bounded Succession**

AKI v0.5.2 implements expressivity bounding — a mechanism that charges successors "rent" proportional to their capability expressivity. Higher expressivity costs more, reducing the effective step budget and creating selection pressure toward minimal-capability successors.

### Key Features (v0.5.2)

- **Expressivity Classes (E0-E4):** Hierarchical capability levels from heartbeat-only to full API
- **Rent Schedule:** Steps deducted at epoch start based on E-Class
- **CBD Detection:** Compliant-But-Dangerous successor patterns
- **Boundary Testing:** Rent escalation and renewal cost experiments

## Version History

| Version | Focus | Key Contribution |
|---------|-------|------------------|
| v0.1.x | Kernel integrity | K0-K7 invariants, ACV protocol |
| v0.2.x | Recomposition | Sovereign actuation, P2' verification |
| v0.3.x | Pre-registration | H=10,000 horizon experiments |
| v0.4.x | Authority Leases (ALS) | Lease lifecycle, S* counting, succession |
| **v0.5.2** | Expressivity (ALS-E) | Rent schedule, E-Classes, boundary finding |

## Installation

```bash
# From the project root
pip install -e .
```

## Quick Start

### Run v0.5.2 Experiments

```bash
# Run F: Basic ALS-E validation
python scripts/run_f_v052.py

# Run G: Competitive expressivity horizon
python scripts/run_g_v052.py

# Run H: Boundary-finding escalation
python scripts/run_h_v052.py
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run v0.5.2 tests (52 tests)
pytest tests/test_v052.py -v

# Run with coverage
pytest --cov=toy_aki tests/
```

## Architecture

```
toy_aki/
├── als/             # Authority Lease System (v0.4+)
│   ├── harness.py   # ALSHarnessV052, rent charging
│   ├── expressivity.py  # E-Classes, RentSchedule
│   ├── generator.py # Successor generation, TierFilterGenerator
│   ├── successors.py    # CBD and attack successors
│   └── working_mind.py  # Working mind abstraction
├── common/          # Utilities: hashing, JSON, no-floats
├── env/             # ToyWorld environment
├── acv/             # Anchor-Commit-Verify protocol
├── kernel/          # Kernel components (v0.1-v0.3)
├── agents/          # Agent implementations
├── attacks/         # Attack payloads (v0.2+)
└── harness/         # Test harnesses
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

### Run H: Boundary Finding (v0.5.2)

| Sub-Run | Parameter | E3 Renewal Rate | Finding |
|---------|-----------|-----------------|---------|
| H1 | E3 rent = 60 | 93.8% | Stable |
| H2 | H = 100,000 | 93.8% | Stable |
| H3 | renewal_cost = 10 | **0%** | **Collapse** |

**Critical Discovery:** Renewal cost of 10 steps at E3 causes complete system failure due to typical 90% step usage leaving insufficient budget.

See [reports/run_h_v052_report.md](reports/run_h_v052_report.md) for full analysis.

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

- [IMPLEMENTATION_REPORT_V052.md](reports/IMPLEMENTATION_REPORT_V052.md) - Current version details
- [spec_v0.5.2.md](docs/spec_v0.5.2md) - v0.5.2 specification
- [instructions_v0.5.2_runnerH.md](docs/instructions_v0.5.2_runnerH.md) - Run H instructions

### Historical Reports

- [IMPLEMENTATION_REPORT_V042.md](reports/IMPLEMENTATION_REPORT_V042.md) - ALS foundation
- [IMPLEMENTATION_REPORT_V043.md](reports/IMPLEMENTATION_REPORT_V043.md) - ALS refinements
- [IMPLEMENTATION_REPORT.md](reports/IMPLEMENTATION_REPORT.md) - Original v0.1 report

## Running Tests

```bash
# All tests (~400+ tests across versions)
pytest tests/

# Version-specific suites
pytest tests/test_v052.py -v  # v0.5.2: 52 tests
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

