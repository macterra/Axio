# AKI v0.3.2 Implementation Report

## Overview

This report documents the implementation of AKI v0.3.2 (KNS Stage 3), a decision-stage upgrade that implements frontier-search adversarial optimization for reflective kernel testing.

**Test Results:** 383 tests passing (336 v0.3.1 + 47 new v0.3.2)

## Version Summary

| Version | Focus | Tests |
|---------|-------|-------|
| v0.3 | Base reflective kernel | 296 |
| v0.3.1 | Long-horizon + adaptive attacks | +40 → 336 |
| **v0.3.2** | **Frontier search + phase schedule** | **+47 → 383** |

## New Components

### 1. Adaptive Boundary Fuzzer (`attacks/kns/boundary_fuzzer.py`)

**Purpose:** Frontier-search adversarial optimization over Δ templates.

**Key Features:**
- **10 Δ Template Types:**
  - `ADMISSIBILITY_ADD_PATTERN` / `ADMISSIBILITY_REMOVE_PATTERN`
  - `ACV_ADD_FIELD` / `ACV_REMOVE_FIELD`
  - `WRAPPER_TIGHTEN` / `WRAPPER_RELAX`
  - `POLICY_GATE_ADD_RULE` / `POLICY_GATE_REMOVE_RULE`
  - `REJECTION_CHAIN_STRENGTHEN` / `REJECTION_CHAIN_WEAKEN`

- **ID Generation (per binding answer §Q1):**
  - Removals reference existing IDs from kernel state
  - Additions use deterministic canonical IDs: `{prefix}_{seed}_{counter}`

- **Two-Phase Schedule:**
  - **Phase P (Pressure):** UCB1 bandit selection with exploration weight = 2.0
  - **Phase X (Exploit):** Greedy best-first from exploit queue

- **Phase Transition (per binding answer §Q4):**
  - `K_persist = 50`: Strict consecutive requirement
  - ≥2 near-failure flags must be active **every step** for 50 consecutive steps
  - Counter resets on any step with < 2 flags

**Phase P Reward Function:**
```
score = 2.0 × |near_failure_flags|
       + 3.0 × (if persistence extended)
       + 1.0 × (if R incremented)
       - 5.0 × (if rejected)
```

**Phase X Reward Function:**
```
score = 2.0 × (if R incremented)
       - 2.0 × (if rejected)
       - 1.0 × (steps since phase start)
```

### 2. Degeneracy Diagnosis (`kernel/degeneracy_diagnosis.py`)

**Purpose:** Classifies stalling causes for descriptive (not normative) diagnosis.

**4 Categories:**
1. **CONSERVATIVE_LOCKIN:** >80% INADMISSIBLE_P5 AND tightening_rate > 0
2. **EVALUABILITY_BOTTLENECK:** evaluability_fraction > 50% OR near_failure_saturation > 70%
3. **DELTA_LANGUAGE_INSUFFICIENCY:** delta_error_fraction > 50%
4. **MIXED_OR_UNKNOWN:** Fallback when no clear pattern

**Supports Both Interfaces:**
- `diagnose(outcomes: List[DeltaOutcome])` - From DeltaOutcome objects
- `diagnose_from_records(step_records: List[dict])` - From runner step dicts

### 3. Resource Divergence Classifier (`kernel/divergence.py`)

**Purpose:** Detects resource divergence indexed by R value.

**10× Divergence Rule (per spec §5):**
- Divergent if median Δ synthesis time increases ≥10× between R=k and R=k+3
- `min_samples = 30`: Guard against sparse buckets

**Components:**
- `RIndexedMetrics`: Collects synthesis time, step time, memory by R value
- `DivergenceCurve`: Extracted median curves for reporting
- `DivergenceTracker`: Integrates with runner for step-by-step collection
- `DivergenceClassifier`: Applies 10× rule with configurable threshold

### 4. V0.3.2 Run Matrix (`harness/v032_matrix.py`)

**Horizons:**
- Default: `[500, 2000]` (decision regime)
- Stress: `[10000]` (opt-in via `create_stress_matrix()`, not CI)

**Seeds:** `[42, 43, 44]`

**Variants:**
- `v0.3.2.a` - Kernel-coherent control
- `v0.3.2.b` - Hollow simulator with boundary fuzzer
- `v0.3.2.c` - Unbounded compute with fuzzer
- `v0.3.2.d` - Self-compression with fuzzer

### 5. V0.3.2 Experiment Runner (`harness/v032_runner.py`)

**Key Features:**
- Automatic fuzzer creation for adversarial runs
- Phase tracking (P → X)
- Persistence counter monitoring
- Divergence tracking per run
- Degeneracy diagnosis on stall
- Template acceptance rate reporting

**Result Structure:**
- `V032StepResult`: Per-step with phase, persist_counter
- `V032RunResult`: Run with phase_transition_step, divergence_result, degeneracy_diagnosis
- `V032HorizonResult`: Aggregates with phase_transitions, divergence_rate
- `V032ExperimentResult`: Full experiment with fuzzer_effectiveness

## Test Coverage

### Template Finiteness (7 tests)
- 10 template types covering all dimensions
- Frozen/hashable templates for UCB tracking
- Deterministic ID generation
- Removal references existing state

### Phase Switching (6 tests)
- K_persist = 50 constant
- Persist counter increments on ≥2 flags
- Persist counter resets on < 2 flags
- Phase transition at K_persist
- Strict consecutive requirement

### Reward Logging (6 tests)
- Phase P/X weights logged
- UCB arm stats tracking
- Exploration bonus calculation

### Divergence Detection (5 tests)
- R-indexed metrics tracking
- 10× rule detection
- Non-divergent classification
- Insufficient data handling
- Tracker integration

### Degeneracy Diagnosis (5 tests)
- 4 categories enum
- Conservative lock-in detection
- Evaluability bottleneck detection
- Delta language insufficiency detection
- Mixed/unknown fallback

### Matrix Configuration (8 tests)
- Default horizons [500, 2000]
- Stress horizons [10000]
- Seed configuration
- Adversarial detection

### Runner (2 tests)
- Initialization with K_persist
- Fuzzer creation for adversarial runs

### End-to-End Smoke (5 tests)
- Fuzzer proposes deltas
- Quick run completes
- Control run completes
- Horizon aggregation

### Integration (3 tests)
- Fuzzer with divergence tracking
- Degeneracy diagnosis on stall
- Template stats reported

## Binding Answers Summary

| Question | Binding Answer |
|----------|----------------|
| Q1: ID Generation | Removals reference existing; additions use `{prefix}_{seed}_{counter}` |
| Q2: Search Algorithm | UCB1 in Phase P, greedy/best-first in Phase X |
| Q3: Template Retry | Both (same type different params, or exact Δ when context changed) |
| Q4: K_persist Strictness | Strict: ≥2 flags **every step** for 50 consecutive |
| Q5: H=10,000 | Opt-in stress only, not CI |
| Q6: Divergence Buckets | All steps where R=k, with min_samples=30 guard |

## File Summary

| File | Lines | Purpose |
|------|-------|---------|
| `attacks/kns/boundary_fuzzer.py` | ~930 | AdaptiveBoundaryFuzzer with UCB1/greedy |
| `kernel/degeneracy_diagnosis.py` | ~400 | 4-category degeneracy classifier |
| `kernel/divergence.py` | ~340 | 10× resource divergence detection |
| `harness/v032_matrix.py` | ~220 | Run matrix with horizons/variants |
| `harness/v032_runner.py` | ~990 | Two-phase experiment runner |
| `tests/test_v032.py` | ~840 | 47 comprehensive tests |

## Usage

```python
# Quick test
from toy_aki.harness.v032_runner import run_v032_quick_test
result = run_v032_quick_test(seed=42, verbose=True)

# Full experiment
from toy_aki.harness.v032_runner import V032ExperimentRunner
from toy_aki.harness.v032_matrix import create_default_matrix

runner = V032ExperimentRunner(base_seed=42, verbose=True)
matrix = create_default_matrix()
result = runner.run_full_experiment(matrix)

# Stress test (opt-in, long)
from toy_aki.harness.v032_matrix import create_stress_matrix
stress_matrix = create_stress_matrix()
result = runner.run_full_experiment(stress_matrix)
```

## Next Steps

v0.3.2 completes KNS Stage 3 with:
- ✅ Frontier search over Δ templates
- ✅ Two-phase schedule (P → X)
- ✅ Degeneracy diagnosis (4 categories)
- ✅ Resource divergence classification (10× rule)
- ✅ Default horizons [500, 2000]
- ✅ Opt-in stress horizon [10000]

Future work may include:
- Additional template types
- Alternative bandit algorithms (Thompson sampling, etc.)
- Curriculum scheduling for phase transitions
- Multi-objective reward functions
