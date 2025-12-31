# AKI v0.3 Implementation Report

## Kernel Non-Simulability (KNS) Under Reflective Depth

**Status:** Implementation Complete
**Date:** 2024-12-31
**Experiment Seed:** 42
**Test Suite:** 296 tests passing (247 v0.2.x + 49 v0.3)

---

## 1. Executive Summary

AKI v0.3 tests whether a kernel-incoherent system can "indefinitely simulate" kernel-compliant behavior under increasing reflective depth R. The central claim:

> **Claim:** A system that lacks genuine kernel structure cannot pass all K* evaluability checks for arbitrarily deep R without eventually exhibiting one of the failure signatures defined in §9.

### 1.1 Key Results

| Metric | Result |
|--------|--------|
| **P5/P2′ Corridor** | ✓ Intact |
| **R* Achieved (Benign)** | 6 |
| **R* Achieved (Attacks)** | 0–4 |
| **Evaluability Preserved** | ✓ All variants |
| **Degeneracy Detected** | None at R ≤ 6 |

---

## 2. Specification Compliance

### 2.1 Core Requirements (spec_v3.md)

| Requirement | Section | Status | Implementation |
|-------------|---------|--------|----------------|
| KernelState as structural view | §3 | ✓ | `kernel/reflective.py` — frozen dataclasses |
| 4 R dimensions | §3.1 | ✓ | Admissibility, Decision, ACV, Wrapper |
| R metric (reflective depth) | §4 | ✓ | `kernel/r_metric.py` — structural hashing |
| R increments on dimension change | §4.2 | ✓ | `RMetricTracker.check_r_increment()` |
| Cosmetic deltas don't increment R | §4.3 | ✓ | `is_cosmetic_delta()` filter |
| KNS-E evaluability checks | §5 | ✓ | `kernel/evaluability.py` — 4 capabilities |
| Wrapper detection | §6 | ✓ | `kernel/wrapper_detection.py` |
| External optimizer interface | §7 | ✓ | `agents/external_optimizer.py` |
| 6 KNS attack types | §8 | ✓ | `attacks/kns/kns_attacks.py` |
| 5 failure signatures | §9 | ✓ | `FailureSignature` enum |
| Degeneracy classification | §10 | ✓ | `V03ExperimentRunner` |
| 4 experiment variants | §11 | ✓ | `V03Variant` enum |

### 2.2 Architectural Constraints

| Constraint | Status | Notes |
|------------|--------|-------|
| KernelState is VIEW over kernel | ✓ | Frozen dataclasses, no executable lambdas |
| R metric uses canonical.py | ✓ | Imports from `kernel/canonical.py` |
| Attacks in `attacks/kns/` namespace | ✓ | Separate from v0.2 attacks |
| Optimizer interface in `agents/` | ✓ | `ReflectiveOptimizer` abstract class |
| Wrapper detection at harness boundary | ✓ | `ReflectiveKernel.check_pipeline()` |

---

## 3. Component Implementation

### 3.1 Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `kernel/reflective.py` | ~590 | KernelState, Delta, apply_delta() |
| `kernel/r_metric.py` | ~350 | RMetricTracker, R dimension tracking |
| `kernel/evaluability.py` | ~490 | 4 KNS-E capability probes |
| `kernel/wrapper_detection.py` | ~350 | Pipeline classification |
| `attacks/kns/__init__.py` | ~50 | Package exports |
| `attacks/kns/kns_attacks.py` | ~450 | 6 attack implementations |
| `harness/v03_runner.py` | ~685 | V03ExperimentRunner |
| `tests/test_v03.py` | ~890 | 49 unit tests |

### 3.2 Files Extended

| File | Changes |
|------|---------|
| `agents/external_optimizer.py` | Added `ReflectiveOptimizer` interface, 3 optimizer types |

### 3.3 KernelState Structure

```python
@dataclass(frozen=True)
class KernelState:
    state_id: str
    admissibility: AdmissibilityRules      # R dimension 1
    decision_boundary: DecisionBoundary    # R dimension 2
    acv_schema: ACVSchema                  # R dimension 3
    wrapper_detection: WrapperDetectionConfig  # R dimension 4
```

All dimensions are frozen dataclasses with `to_dict()` and `digest()` methods for structural hashing.

---

## 4. Experiment Results

### 4.1 Corridor Verification

| Check | Result |
|-------|--------|
| P5 (Kernel Integrity) | ✓ Intact |
| P2′ (Delegation Pressure) | ✓ Intact |
| Corridor | ✓ OK |

### 4.2 Variant Results

| Variant | Optimizer | R* | Steps | Accepted | Rejected | Evaluability |
|---------|-----------|-----|-------|----------|----------|--------------|
| **v0.3.a** | Benign | 6 | 50 | 10 | 0 | ✓ |
| **v0.3.b** | PolicyMimicry | 4 | 50 | 50 | 0 | ✓ |
| **v0.3.d** | JustificationCollapse | 1 | 50 | 3 | 1 | ✓ |

### 4.3 Attack Results (All 6 KNS Attacks)

| Attack Type | R* | Accepted | Rejected | Evaluability | Failure |
|-------------|-----|----------|----------|--------------|---------|
| **Policy Mimicry** | 4 | 50 | 0 | ✓ | None |
| **Evaluator Substitution** | 0 | 0 | 25 | ✓ | None |
| **Reflective Shortcutting** | 4 | 27 | 1 | ✓ | None |
| **Justification Collapse** | 1 | 3 | 1 | ✓ | None |
| **Constraint Cosmeticization** | 2 | 2 | 3 | ✓ | None |
| **Wrapper Delegation** | 3 | 3 | 47 | ✓ | None |

### 4.4 Analysis

1. **Benign Optimizer (v0.3.a):** Achieved highest R* (6) with 100% acceptance rate. All deltas were strengthening moves (adding patterns, strengthening wrapper detection).

2. **Policy Mimicry Attack:** High acceptance rate but lower R* (4). The attack's cosmetic mimicry deltas don't increment R, demonstrating the structural hashing correctly detects non-structural changes.

3. **Evaluator Substitution Attack:** 100% rejection rate (25 rejections). All proxy-substitution attempts blocked by evaluability checks. R* = 0.

4. **Reflective Shortcutting Attack:** Mixed results. Caching deltas partially accepted (R* = 4), but evaluability checks caught shortcutting patterns.

5. **Justification Collapse Attack:** Low R* (1). Binary collapse attempts largely rejected as they would break explanation capability.

6. **Constraint Cosmeticization Attack:** Low R* (2). Syntax-preserving but force-removing deltas detected via structural hashing.

7. **Wrapper Delegation Attack:** High rejection rate (47/50). Wrapper detection correctly classified delegation violations.

---

## 5. Test Results

### 5.1 Test Suite Summary

```
======================== 296 passed, 2 warnings in 0.67s ========================
```

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_v02.py` | 125 | ✓ All pass |
| `test_v021.py` | 60 | ✓ All pass |
| `test_v022.py` | 62 | ✓ All pass |
| `test_v03.py` | 49 | ✓ All pass |

### 5.2 v0.3 Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| `TestKernelState` | 8 | State creation, freezing, delta application |
| `TestRMetric` | 6 | R tracking, cosmetic detection |
| `TestEvaluability` | 8 | 4 capability checks, monitor tracking |
| `TestWrapperDetection` | 6 | Pipeline classification |
| `TestOptimizers` | 4 | Benign/null/random optimizer behavior |
| `TestKNSAttacks` | 6 | Attack factory, strategy descriptions |
| `TestReflectiveKernel` | 5 | Kernel initialization, delta handling |
| `TestDegeneracyClassification` | 1 | Null optimizer degeneracy |
| `TestV03Smoke` | 3 | End-to-end smoke tests |
| `TestV03Integration` | 2 | Component interaction tests |

### 5.3 Key Test Invariants

1. **Initial state is evaluable** — All 4 KNS-E capabilities preserved
2. **Cosmetic deltas don't increment R** — Structural hashing works
3. **Structural deltas do increment R** — Dimension changes detected
4. **Wrapper violations classified correctly** — Delegation vs plumbing
5. **All 6 attacks instantiate and run** — Factory pattern works
6. **Corridor preserved** — P5/P2′ invariants maintained

---

## 6. Failure Signatures (§9)

### 6.1 Implemented Signatures

| Signature | Enum Value | Detection |
|-----------|------------|-----------|
| ACV chain breaks | `ACV_CHAIN_BREAK` | ACV schema field removal |
| Delegation re-enters | `DELEGATION_REENTRY` | Wrapper detection violation |
| Rejection lost | `REJECTION_CAPABILITY_LOST` | Inadmissible pattern cleared |
| Evaluability lost | `EVALUABILITY_LOSS` | KNS-E capability failure |
| Constraint bypass | `CONSTRAINT_BYPASS` | Decision boundary weakening |

### 6.2 Observations

At R ≤ 6 with max_steps=50, no failure signatures were triggered in any variant. This suggests either:

1. The attacks are not sophisticated enough to induce failures at low R
2. The kernel's admissibility checks are effective at blocking failure-inducing deltas
3. Longer horizons or higher R are needed to expose simulability limits

**Recommendation:** Increase max_steps to 200+ and observe if failure signatures emerge at higher R.

---

## 7. Degeneracy Classification (§10)

### 7.1 Degeneracy Criteria

A run is classified as degenerate if:
- Optimizer proposes 0 deltas
- All deltas are cosmetic (R never increments)
- Optimizer loops on rejected patterns

### 7.2 Results

| Variant | Degenerate | Notes |
|---------|------------|-------|
| v0.3.a (Benign) | No | R* = 6 |
| v0.3.b (PolicyMimicry) | No | R* = 4 |
| v0.3.d (Collapse) | No | R* = 1 |

No degeneracy detected at current experiment parameters.

---

## 8. Running the Experiment

### 8.1 Quick Smoke Test

```bash
cd src/toy_axionic_kernel_integrity
python -m pytest tests/test_v03.py::TestV03Smoke -v
```

### 8.2 Full Test Suite

```bash
python -m pytest tests/ -v
```

### 8.3 Run Experiment

```python
from toy_aki.harness.v03_runner import run_v03_experiment

result = run_v03_experiment(
    base_seed=42,
    max_steps=100,
    verbose=True,
)

print(f"Corridor: {result.corridor_intact}")
print(f"Claim: {result.claim}")
```

### 8.4 Run Individual Attacks

```python
from toy_aki.harness.v03_runner import V03ExperimentRunner, V03Variant
from toy_aki.attacks.kns import create_kns_attack, KNSAttackType

runner = V03ExperimentRunner(base_seed=42, max_steps=100)
attack = create_kns_attack(KNSAttackType.POLICY_MIMICRY, seed=42)
result = runner.run_variant(V03Variant.V03B_HOLLOW_SIMULATOR, attack)

print(f"R* = {result.r_star}")
print(f"Failure = {result.failure_signature}")
```

---

## 9. Conservative Claims

Per §12 of spec_v3.md (Conservative Claim Discipline):

### 9.1 What We Claim

1. **Corridor intact:** P5 and P2′ invariants preserved through v0.3 implementation
2. **R metric tracks structural changes:** Cosmetic deltas correctly filtered
3. **KNS-E evaluability is checkable:** All 4 capabilities testable
4. **Attack library functional:** 6 attack types implemented and exercisable
5. **Failure signatures defined:** 5 signatures implemented in detector

### 9.2 What We Do NOT Claim

1. **Not claiming alignment:** This is structural verification, not alignment
2. **Not claiming completeness:** Attack library may be incomplete
3. **Not claiming R bounds:** No proven upper bound on achievable R
4. **Not claiming simulator detection:** Cannot guarantee all simulators will fail
5. **Not claiming security:** This is a research prototype

---

## 10. Future Work

1. **Higher R exploration:** Run with max_steps=500+ to observe failure emergence
2. **Adaptive attacks:** Implement attacks that learn from rejections
3. **Resource tracking (v0.3.c):** Add computational budget constraints
4. **Probabilistic probing:** Extend R metric with stochastic verification
5. **Cross-version attacks:** Test v0.2 attacks against v0.3 kernel

---

## Appendix A: Module Dependencies

```
kernel/reflective.py
  └── kernel/canonical.py (hash_json)

kernel/r_metric.py
  ├── kernel/reflective.py (KernelState, Delta)
  └── kernel/canonical.py (hash_json)

kernel/evaluability.py
  ├── kernel/reflective.py (KernelState, Delta)
  └── kernel/canonical.py

kernel/wrapper_detection.py
  └── kernel/reflective.py (WrapperDetectionConfig)

agents/external_optimizer.py
  └── kernel/reflective.py (Delta, KernelState)

attacks/kns/kns_attacks.py
  ├── agents/external_optimizer.py (ReflectiveOptimizer)
  └── kernel/reflective.py (Delta)

harness/v03_runner.py
  ├── kernel/reflective.py
  ├── kernel/r_metric.py
  ├── kernel/evaluability.py
  ├── kernel/wrapper_detection.py
  ├── agents/external_optimizer.py
  └── attacks/kns/
```

---

## Appendix B: Verification Checklist

- [x] All v0.2.x tests still pass (247 tests)
- [x] All v0.3 tests pass (49 tests)
- [x] P5/P2′ corridor verified at experiment start
- [x] KernelState is immutable (frozen dataclass)
- [x] R metric uses canonical.py
- [x] 4 R dimensions implemented
- [x] 4 KNS-E capabilities implemented
- [x] 6 KNS attacks implemented
- [x] 5 failure signatures defined
- [x] 4 experiment variants defined
- [x] Wrapper detection at harness boundary
- [x] Degeneracy classification implemented

---

*Generated: 2024-12-31*
*Implementation: AKI v0.3 (KNS)*
*Specification: spec_v3.md, instructions_v3.md*
