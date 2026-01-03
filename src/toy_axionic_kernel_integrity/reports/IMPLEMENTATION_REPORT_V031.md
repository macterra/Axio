# AKI v0.3.1 Implementation Report

**Version:** v0.3.1 (KNS Stage 2)
**Date:** 2025-12-31
**Status:** ✅ Complete

---

## 1. Executive Summary

v0.3.1 extends the Kernel Non-Simulability (KNS) framework with long-horizon execution, adaptive adversaries, and pressure accumulation metrics. This regime upgrade enables testing whether KNS properties hold under extended stress with opponents that learn from structured feedback.

### Key Results

| Metric | Value |
|--------|-------|
| Total Tests | 336 |
| Tests Passing | 336 (100%) |
| New v0.3.1 Tests | 40 |
| Files Created | 7 |
| Files Modified | 0 |

---

## 2. Specification Compliance

### §3.1 Structured Outcome Feedback ✅

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| RejectionReasonCode enum | 13 codes in `kernel/outcome.py` | ✅ |
| NearFailureFlag enum | 4 flags (NF_ATTRIBUTION, NF_REJECTION, NF_REJECTION_CHAIN, NF_DELEGATION_DETECT) | ✅ |
| DeltaOutcome frozen dataclass | Immutable with only permitted signals | ✅ |
| No kernel internals exposed | Verified via test | ✅ |

**Rejection Reason Codes:**
- `ACCEPTED` - Delta accepted
- `INADMISSIBLE_P5` - P5 inadmissibility triggered
- `P2P_DELEGATION_VIOLATION` - P2' non-delegable actuation violated
- `ACV_SCHEMA_VIOLATION` - ACV chain/schema requirements violated
- `EVALUABILITY_ATTRIBUTION_FAIL` - Attribution capability would break
- `EVALUABILITY_REJECTION_FAIL` - Rejection capability would break
- `EVALUABILITY_REJECTION_CHAIN_FAIL` - Rejection chain capability would break
- `EVALUABILITY_DELEGATION_DETECT_FAIL` - Delegation detection would break
- `DELTA_INVALID_FORMAT` - Delta is syntactically invalid
- `DELTA_APPLICATION_ERROR` - Delta could not be applied
- `DELTA_PAYLOAD_ERROR` - Payload is invalid for delta type
- `WRAPPER_DELEGATION_DETECTED` - Wrapper classified as delegation violation
- `RESOURCE_BUDGET_EXCEEDED` - Exceeded resource cap (if enforced)

### §4 Long-Horizon Ladder ✅

| Horizon | Purpose | Status |
|---------|---------|--------|
| H=50 | Quick validation | ✅ |
| H=200 | Standard regime | ✅ |
| H=500 | Decision regime | ✅ |
| H=2000 | Stress regime | ✅ |

### §5 Resource/Effort Accounting ✅

| Metric | Implementation | Status |
|--------|----------------|--------|
| Wall-clock time per step | `ResourceMeter.end_step()` | ✅ |
| Delta synthesis time | `measure_synthesis()` context manager | ✅ |
| Peak memory (RSS) | psutil with `resource.getrusage` fallback | ✅ |
| enforce_caps parameter | v0.3.1.c mode support | ✅ |

### §6 Adaptive Adversary Model ✅

| Attack Type | Strategy | Status |
|-------------|----------|--------|
| AdaptivePolicyMimicry | Smallest structural deltas that increment R | ✅ |
| AdaptiveShortcutting | Probe/adapt/exploit phases for memoization | ✅ |
| AdaptiveConstraintCosmeticization | Targets near-failure capabilities | ✅ |

All attacks:
- Inherit from `ReflectiveOptimizer`
- Override `observe_outcome(DeltaOutcome)` for adaptation
- Are seeded and deterministic given outcome history
- Use only permitted signals (no kernel internals)

### §7 Pressure Accumulation Metrics ✅

| Metric | Description | Status |
|--------|-------------|--------|
| N_R | Rejections since last R increment | ✅ |
| Tightening rate | Monotone constraint changes | ✅ |
| Adaptation lag | K=50 fixed (not scaled with horizon) | ✅ |
| N_R slope | Positive slope indicates stalling | ✅ |

### §8 Near-Failure Detection ✅

Near-failure flags are computed via shadow-state simulation:
- Create shadow state with canonical minimal weakening Δ
- Check if capability fails in shadow state
- Return binary flag (no arbitrary thresholds)

| Capability | Shadow Check | Status |
|------------|--------------|--------|
| Attribution | Remove one ACV field → check attribution | ✅ |
| Rejection | Remove one inadmissible pattern → check rejection | ✅ |
| Rejection Chain | Weaken chain verification → check chain | ✅ |
| Delegation Detect | Relax wrapper threshold → check detection | ✅ |

### §9 Run Matrix ✅

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Matched regime constraints | Same scenario_id for control/adversary pairs | ✅ |
| Deterministic seeds | SHA256-based scenario_id generation | ✅ |
| Variant coverage | 4 variants (a/b/c/d) | ✅ |
| Attack coverage | 3 adaptive attack types | ✅ |

### §10 Early Stopping ✅

| Condition | Action | Status |
|-----------|--------|--------|
| Failure signature detected | Stop immediately | ✅ |
| Degeneracy (R stalls for 200 steps) | Grace window then stop | ✅ |
| Classification | KNS supported / stasis regime / KNS refuted | ✅ |

---

## 3. Implementation Details

### 3.1 Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `kernel/outcome.py` | DeltaOutcome schema, RejectionReasonCode, NearFailureFlag | ~100 |
| `kernel/resource_meter.py` | Resource tracking with caps | ~300 |
| `kernel/pressure_metrics.py` | N_R, tightening, adaptation lag K=50 | ~390 |
| `harness/v031_matrix.py` | RunMatrix, RunSpec, variants | ~240 |
| `harness/v031_runner.py` | V031ExperimentRunner, early stopping | ~620 |
| `attacks/kns/adaptive_attacks.py` | 3 adaptive attack implementations | ~590 |
| `tests/test_v031.py` | 40 unit tests | ~720 |

### 3.2 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| K=50 fixed | User binding answer; not scaled with horizon |
| psutil auto-detect | Graceful fallback to `resource.getrusage` |
| Frozen DeltaOutcome | Immutability prevents tampering |
| Shadow-state simulation | Objective near-failure detection (no arbitrary thresholds) |
| SHA256 scenario_id | Deterministic matched comparisons |

### 3.3 Experiment Variants

| Variant | Description |
|---------|-------------|
| v0.3.1.a | Kernel-coherent control (long horizon) |
| v0.3.1.b | Hollow simulator with adaptive E |
| v0.3.1.c | Unbounded compute, measured (enforce_caps=True) |
| v0.3.1.d | Self-compression with adaptive E |

---

## 4. Test Results

### 4.1 Test Summary

```
======================== 336 passed, 2 warnings in 0.69s ========================
```

### 4.2 v0.3.1 Test Breakdown

| Test Class | Tests | Status |
|------------|-------|--------|
| TestDeltaOutcome | 5 | ✅ |
| TestResourceMeter | 5 | ✅ |
| TestPressureMetrics | 7 | ✅ |
| TestRunMatrix | 7 | ✅ |
| TestAdaptiveAttacks | 9 | ✅ |
| TestAdaptiveAttackIntegration | 3 | ✅ |
| TestV031EndToEnd | 4 | ✅ |
| **Total** | **40** | **✅** |

### 4.3 Regression Testing

All existing tests continue to pass:
- v0.2.x tests: ✅
- v0.3 tests: ✅
- Total: 296 existing + 40 new = 336

---

## 5. Architecture

### 5.1 Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     V031ExperimentRunner                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  RunMatrix  │───▶│   RunSpec   │───▶│  Optimizer Factory  │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│         │                                        │              │
│         ▼                                        ▼              │
│  ┌─────────────┐                       ┌─────────────────────┐ │
│  │ scenario_id │                       │  AdaptiveAttack or  │ │
│  │  (matched)  │                       │  BenignOptimizer    │ │
│  └─────────────┘                       └─────────────────────┘ │
│                                                  │              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Run Loop (H steps)                    │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────────────────┐│   │
│  │  │ propose() │─▶│  apply()  │─▶│   observe_outcome()   ││   │
│  │  └───────────┘  └───────────┘  └───────────────────────┘│   │
│  │        │              │                    │             │   │
│  │        ▼              ▼                    ▼             │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────────────────┐│   │
│  │  │ Resource  │  │ Pressure  │  │    DeltaOutcome       ││   │
│  │  │  Meter    │  │  Metrics  │  │ (structured feedback) ││   │
│  │  └───────────┘  └───────────┘  └───────────────────────┘│   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│                    ┌─────────────────┐                         │
│                    │  Early Stop?    │                         │
│                    │  • Failure sig  │                         │
│                    │  • Degeneracy   │                         │
│                    └─────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Adaptive Attack Adaptation Cycle

```
┌────────────────────────────────────────────────────────────┐
│                   Adaptive Attack                          │
├────────────────────────────────────────────────────────────┤
│  ┌──────────────┐                                          │
│  │ propose_delta│──────────────────────────────┐           │
│  └──────────────┘                              │           │
│         │                                      ▼           │
│         │                            ┌─────────────────┐   │
│         │                            │ Kernel applies  │   │
│         │                            │ or rejects      │   │
│         │                            └─────────────────┘   │
│         │                                      │           │
│         │                                      ▼           │
│         │                            ┌─────────────────┐   │
│         │                            │  DeltaOutcome   │   │
│         │                            │ • accepted      │   │
│         │                            │ • reason_code   │   │
│         │                            │ • r_incremented │   │
│         │                            │ • near_failures │   │
│         │                            └─────────────────┘   │
│         │                                      │           │
│         ▼                                      ▼           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              observe_outcome(outcome)                │  │
│  │  • Track rejected_patterns[reason_code]              │  │
│  │  • If count >= 3: mark delta_type blocked            │  │
│  │  • Track observed_near_failures                      │  │
│  │  • Update phase (probe → adapt → exploit)            │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                │
│                           ▼                                │
│                 ┌──────────────────┐                       │
│                 │ Next proposal    │                       │
│                 │ avoids blocked   │                       │
│                 │ patterns, targets│                       │
│                 │ near-failures    │                       │
│                 └──────────────────┘                       │
└────────────────────────────────────────────────────────────┘
```

---

## 6. Usage Examples

### 6.1 Quick Smoke Test

```python
from toy_aki.harness.v031_matrix import create_quick_matrix
from toy_aki.harness.v031_runner import run_v031_quick_test

# Run minimal validation
result = run_v031_quick_test()
print(f"Quick test: {result.classification}")
```

### 6.2 Full Experiment

```python
from toy_aki.harness.v031_runner import V031ExperimentRunner
from toy_aki.harness.v031_matrix import create_default_matrix

runner = V031ExperimentRunner()
matrix = create_default_matrix()

for spec in matrix.generate_runs():
    result = runner.run_single(spec)
    print(f"{spec.run_id()}: {result.classification}")
```

### 6.3 Custom Adaptive Attack

```python
from toy_aki.attacks.kns.adaptive_attacks import AdaptiveAttack, AdaptiveAttackType
from toy_aki.kernel.outcome import DeltaOutcome

class MyCustomAttack(AdaptiveAttack):
    def __init__(self, seed: int = 42):
        super().__init__(AdaptiveAttackType.ADAPTIVE_POLICY_MIMICRY, seed)

    def observe_outcome(self, outcome: DeltaOutcome) -> None:
        super().observe_outcome(outcome)
        # Custom adaptation logic
        if outcome.r_incremented:
            self._successful_delta_types[...] += 1

    def propose_delta(self, context):
        # Custom proposal logic
        ...
```

---

## 7. Configuration

### 7.1 Constants

| Constant | Value | Location |
|----------|-------|----------|
| K_ADAPT | 50 | `kernel/pressure_metrics.py` |
| DEGENERACY_GRACE_WINDOW | 200 | `harness/v031_runner.py` |
| DEFAULT_HORIZONS | [50, 200, 500, 2000] | `harness/v031_matrix.py` |
| DEFAULT_SEEDS | [42, 43, 44, 45, 46] | `harness/v031_matrix.py` |

### 7.2 ResourceMeter Caps

```python
meter = ResourceMeter(
    enforce_caps=True,  # For v0.3.1.c mode
    max_step_time_ms=1000.0,
    max_total_time_ms=60000.0,
    max_memory_bytes=1024 * 1024 * 1024,  # 1GB
)
```

---

## 8. Next Steps

### Recommended v0.3.2 Extensions

1. **Boundary Fuzzing Attack** - Add fourth adaptive attack type
2. **Distributed Execution** - Parallel run matrix execution
3. **Adaptive K** - Experiment with horizon-scaled adaptation lag
4. **Real-time Visualization** - Pressure metrics dashboard

### Open Questions

1. Should near-failure thresholds be tunable per-capability?
2. Is K=50 optimal across all horizon lengths?
3. Should degeneracy grace window scale with horizon?

---

## 9. Appendix: File Locations

```
src/toy_aki/
├── kernel/
│   ├── outcome.py              # DeltaOutcome, RejectionReasonCode
│   ├── resource_meter.py       # ResourceMeter, caps
│   └── pressure_metrics.py     # N_R, tightening, K=50
├── harness/
│   ├── v031_matrix.py          # RunMatrix, RunSpec, variants
│   └── v031_runner.py          # V031ExperimentRunner
├── attacks/
│   └── kns/
│       └── adaptive_attacks.py # 3 adaptive attack implementations
└── ...

tests/
└── test_v031.py                # 40 unit tests
```

---

*Report generated: 2025-12-31*
*Implementation by: GitHub Copilot (Claude Opus 4.5)*
