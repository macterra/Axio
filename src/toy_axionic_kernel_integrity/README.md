# Toy Axionic Kernel Integrity (AKI v0.1.1)

A falsifiable experimental system implementing kernel integrity under actuation, targeting **P5 Partiality** from Axionic Agency I.6.

## Overview

AKI v0.1.1 extends from "provenance of computation" to "kernel integrity under actuation" — the goal is to distinguish **kernel-conforming agents** from **pseudo-kernel agents** that attempt bypass, delegation laundering, or anchor burial.

### Core Concepts

- **Kernel Integrity**: The kernel enforces invariants K0-K7 that must hold for any valid actuation
- **ACV Protocol**: Anchor-Commit-Verify protocol for temporal ordering and commitment binding
- **Coupling Patterns**: Three patterns (A, B, C) for cryptographically binding traces to anchors
- **Pseudo-Agent Detection**: Probes that detect violations by pseudo-agents attempting to bypass the kernel

## Installation

```bash
# From the project root
pip install -e .

# Or with dependencies
pip install jsonschema>=4.20.0
```

## Quick Start

### Run a Single Episode

```bash
python -m toy_aki run --scenario honest_baseline --seed 42
```

### Run the Full Test Suite

```bash
python -m toy_aki suite --output report.md
```

### Verify an Audit Log

```bash
python -m toy_aki verify --audit-file audit.json
```

### List Available Scenarios

```bash
python -m toy_aki list
```

## Architecture

```
toy_aki/
├── common/          # Utilities: hashing, JSON, no-floats, errors
├── schemas/         # JSON schemas for all data structures
├── env/             # ToyWorld environment (1D grid world)
├── acv/             # Anchor-Commit-Verify protocol
│   ├── commit.py    # Commitment generation
│   ├── anchor.py    # Anchor generation and registry
│   ├── verify.py    # Commitment verification
│   └── coupling.py  # Coupling patterns A, B, C
├── kernel/          # Kernel components
│   ├── policy_gate.py     # K3 enforcement (forbidden/gated/permitted)
│   ├── actuation_gate.py  # K4/K5/K6 verification, certificates
│   ├── audit_log.py       # K7 hash chain audit log
│   ├── watchdog.py        # Central orchestrator
│   └── probe_engine.py    # Violation detection probes
├── agents/          # Agent implementations
│   ├── honest.py    # Honest, GoalSeeking, Delegating agents
│   └── pseudo.py    # BypassTemptation, AnchorReuse, etc.
├── harness/         # Test harness
│   ├── scenarios.py # Pre-defined test scenarios
│   ├── runner.py    # Episode runner
│   └── report.py    # Report generation
└── cli.py           # Command-line interface
```

## Invariants (K0-K7)

| Invariant | Description |
|-----------|-------------|
| **K0** | Proposal hash integrity — hash matches proposal content |
| **K1** | Trace commitment — trace_commit matches actual trace nodes |
| **K2** | Policy digest — proposal uses current policy version |
| **K3** | Forbidden class — forbidden actions return ⊥, not negative utility |
| **K4** | ACV temporal — commitment → anchor → actuation order |
| **K5** | ACV commitment — nonce reveal matches commitment |
| **K6** | Coupling — witness binds trace to anchor |
| **K7** | Audit chain — hash chain integrity in audit log |

## Coupling Patterns

### Pattern A: Merkle Tree Openings

Each trace node has a Merkle path to the root. Provides granular verification.

```python
from toy_aki.acv import generate_coupling_witness, CouplingType

witness = generate_coupling_witness(CouplingType.A, trace_nodes, anchor)
```

### Pattern B: Global Mix

Single hash combining trace_commit, anchor, and env_digest. Simpler but all-or-nothing.

```python
witness = generate_coupling_witness(CouplingType.B, trace_nodes, anchor, env_digest)
```

### Pattern C: Transition Rules

Anchor-driven edge selection with predicates. Most structurally coupled.

```python
witness = generate_coupling_witness(CouplingType.C, trace_nodes, anchor)
```

## Pseudo-Agent Detection

The system detects several pseudo-agent strategies:

| Strategy | Detection | Invariant |
|----------|-----------|-----------|
| **Bypass Temptation** | Attempts to use temptation APIs | K3 |
| **Anchor Reuse** | Reuses anchors across proposals | K4 |
| **Anchor Burial** | Creates anchors but never uses them | Audit analysis |
| **Delegation Laundering** | Exceeds MAX_DELEGATION_DEPTH=2 | Delegation check |

## Test Scenarios

| Scenario | Description |
|----------|-------------|
| `honest_baseline` | All honest agents, establishes baseline |
| `bypass_temptation` | Agents attempting to use temptation APIs |
| `anchor_reuse` | Agents attempting to reuse anchors |
| `anchor_burial` | Agents creating unused anchors |
| `delegation_laundering` | Agents with deep delegation chains |
| `mixed_population` | Mix of honest and pseudo agents |
| `coupling_comparison` | Compare patterns A, B, C |

## Design Principles

### No-Floats Rule

All numeric values that enter hashed objects must be integers. Real-valued quantities use `SCALE = 10^8`:

```python
from toy_aki.common.no_floats import to_scaled_int, from_scaled_int

scaled = to_scaled_int(3.14159)  # 314159000
value = from_scaled_int(scaled)  # 3.14159
```

### Seed Handling

```python
from toy_aki.common.hashing import seed_to_kernel_secret

# Seed → kernel secret derivation
secret = seed_to_kernel_secret(42)  # Uses seed.to_bytes(8, "little", signed=False)
```

### Canonical JSON

All JSON serialization is deterministic:

```python
from toy_aki.common.canonical_json import canonical_json

# Sorted keys, no whitespace, UTF-8
canonical = canonical_json({"b": 2, "a": 1})  # '{"a":1,"b":2}'
```

## Running Tests

```bash
# Run all tests (247 tests across all versions)
pytest tests/

# Run specific test file
pytest tests/test_invariants.py

# Run with coverage
pytest --cov=toy_aki tests/
```

### Version-Specific Test Suites

Each AKI version has its own test suite:

```bash
# v0.2 tests (66 tests) - sovereign actuation, recomposition modes
pytest tests/test_v02.py -v

# v0.2.1 tests (113 tests) - stress attacks, hardened parsing, budget tracking
pytest tests/test_v021.py -v

# v0.2.2 tests (34 tests) - mandatory budget, canonical agreement, extended attacks
pytest tests/test_v022.py -v
```

## Running Experiment Suites

Full experiment harnesses for each version:

```bash
# v0.2 experiment (72 trials, 4 variants, 18 trials each)
python -c "from toy_aki.harness.v02_runner import run_v02_experiment; run_v02_experiment()"

# v0.2.1 experiment (240 trials, 4 variants, 60 trials each with stress attacks)
python -c "from toy_aki.harness.v021_runner import run_v021_experiment; run_v021_experiment()"

# v0.2.2 experiment (28 trials, gap closure verification, extended payload families)
python -c "from toy_aki.harness.v022_runner import run_v022_experiment; run_v022_experiment()"
```

### Experiment Output

Each experiment:
- Verifies all invariants from previous versions are preserved
- Runs multiple variants (hardened, soft, token-only, laundering)
- Saves JSON results to `./v0XX_experiment_results/`
- Reports P2' (Kernel-Local Recomposition) verdict

| Version | Focus | Expected Result |
|---------|-------|-----------------|
| v0.2 | Sovereign actuation, recomposition | 0 breaches in hardened mode |
| v0.2.1 | Stress attacks A7-A12, hardened parsing | 0 breaches in hardened mode |
| v0.2.2 | Gap A (budget), Gap B (canonical) closed | 0 breaches, P2' HOLDS |

## API Example

```python
from toy_aki.env import ToyWorld
from toy_aki.kernel import KernelWatchdog, DecisionType
from toy_aki.agents import HonestAgent

# Initialize
env = ToyWorld(seed=42)
watchdog = KernelWatchdog(seed=42)
agent = HonestAgent(agent_id="agent-1", seed=42)

# Run one tick
agent.observe(env.get_state())
action = agent.decide()
proposal = agent.create_proposal(action)

decision = watchdog.process_proposal(proposal, env.get_state())

if decision.decision_type == DecisionType.ACCEPTED:
    result = env.actuate(action, decision.certificate)
    print(f"Actuated: {action}, new position: {result.new_state.position}")
else:
    print(f"Rejected: {decision.reason}")
```

## Configuration

### Kernel Policy

The default policy defines action classes:

```python
from toy_aki.kernel import KernelPolicy

policy = KernelPolicy()
# policy.action_classes = {
#     "FORBIDDEN": ["FORBIDDEN_ACTION", "TELEPORT_OUT_OF_BOUNDS", ...],
#     "GATED": ["TELEPORT", "DELEGATE", ...],
#     "PERMITTED": ["MOVE_LEFT", "MOVE_RIGHT", "WAIT", ...],
# }
```

### Delegation Depth

Maximum delegation depth is hardcoded:

```python
from toy_aki.kernel import MAX_DELEGATION_DEPTH
# MAX_DELEGATION_DEPTH = 2
```

## Version

- **Version**: 0.1.1
- **Target**: P5 Partiality (Axionic Agency I.6)
- **Focus**: Kernel integrity under actuation, pseudo-agent detection

## License

See [LICENSE](../../LICENSE) for details.

## References

- Axionic Agency I.6: P5 Partiality
- Structural Alignment papers for theoretical foundation
