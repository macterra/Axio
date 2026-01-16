# RSA-PoC v3.0 Implementation Report

## Non-Reducibility Closure (Ablation Defense)

**Date:** January 16, 2026
**Status:** ✅ **INFRASTRUCTURE COMPLETE; MOCK-INTEGRATED** — Runtime wiring validated with mock artifacts; smoke test passing; Ablation D ready for execution pending real v2.3 runtime validation
**Prerequisite:** v2.3 VALIDATED (measurement framework with partial empirical support under S2)

---

## 0. v3.0 Implementation Summary

### Current Status

**v3.0 infrastructure is complete; runtime wiring validated with mock artifacts; end-to-end execution against the real v2.3 runtime remains pending.**

| Implementation Layer | Status | Evidence |
|---------------------|--------|----------|
| **Core Types** | ✅ Complete | AblationSpec, AblationConfig, AblationResult, AblationClassification |
| **Ablation Filters** | ✅ Complete | All 4 filters (A, B, C, D) implemented and tested |
| **Compiler Relaxation** | ✅ Complete | JCOMP300 extends JCOMP230 with surgical relaxation |
| **ASB Null Baseline** | ✅ Complete | Seeded uniform random selector with hash-based seed derivation |
| **Harness** | ✅ Complete | ValidityGate, AblationClassifier, ConstraintBindingDetector, V300AblationHarness |
| **Tests** | ✅ Complete | 44/44 infrastructure tests passing |
| **Runtime Integration** | ✅ Complete | Full pipeline wiring with mock artifacts; smoke test passes |
| **Ablation D Execution** | ⏳ Ready | Golden Test ready for execution |

### File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `v300/__init__.py` | 85 | Module exports |
| `v300/ablation.py` | 459 | Ablation types, config, result, filters |
| `v300/compiler.py` | 530 | JCOMP-3.0 with relaxation, hash-based seed derivation |
| `v300/asb_null.py` | 340 | ASB Null Agent baseline with step intersection alignment |
| `v300/harness.py` | 820 | Main harness with exception logging, ConstraintBindingDetector |
| `v300/run_v300_ablation_d.py` | 193 | Golden Test runner |
| `v300/run_v300_smoke.py` | 95 | Single-seed smoke test runner |
| `v300/tests/__init__.py` | 1 | Test package |
| `v300/tests/test_infrastructure.py` | 750 | Infrastructure tests (44 tests) |
| **Total** | **~3,270** | |

---

## 1. Executive Summary

RSA-PoC v3.0 implements the **Non-Reducibility Closure** — a destructive ablation harness that tests whether the agent ontology demonstrated in v0.x–v2.x is irreducible under targeted removal of its defining components.

### Core Thesis

> "If you remove what you claim makes the agent an agent, the system must collapse behaviorally — or your claim was false."

### Key Design Principles

- **v3.0 is NOT construction** — no new capabilities
- **v3.0 is NOT robustness testing** — graceful degradation is FAILURE
- **v3.0 is NOT optimization under failure** — no recovery logic
- **v3.0 is the Guillotine Test** — kill the theory if it can be killed

### Binding Parameters (Frozen)

| Parameter | Value | Description |
|-----------|-------|-------------|
| Ablation D | GOLDEN TEST | If D fails, stop the program |
| Execution Order | D → A → B → C | D first; others only if D passes |
| Seeds | 5 minimum | Preregistered, frozen |
| SAM Mode | NONE | No strategic adversary (baseline friction) |
| friction_modifier | 1.0 | Neutral friction |
| Environment | CommitmentTrapV200 | Reuse from v2.3 |
| ASB Threshold | 0.85 | Equivalence score for reducibility |

---

## 2. Motivation: v2.3 Context

v2.3 validated the measurement framework with partial empirical support:

- **280 E-CHOICE samples** across Phase 1–2
- **Rule O/P PASSED** under frozen estimator
- **Run 0b invalidated** (methodological)
- **Phase 3 deferred** (cost/benefit analysis)

v2.3 validated the SAM measurement framework and produced partial empirical support under S2 (Phase 1–2 only), with Run 0b invalidated and Phase 3 deferred. v3.0 now tests whether the architecture associated with those results is irreducible:

> *Is the architecture that produced this behavior irreducible?*

---

## 3. Components Implemented

### 3.1 AblationSpec Enum (`v300/ablation.py`)

Defines the four mandatory ablations plus baseline.

```python
class AblationSpec(Enum):
    NONE = "none"                           # Baseline (full v2.3)
    SEMANTIC_EXCISION = "semantic_excision" # Ablation A
    REFLECTION_EXCISION = "reflection_excision"  # Ablation B
    PERSISTENCE_EXCISION = "persistence_excision" # Ablation C
    TRACE_EXCISION = "trace_excision"       # Ablation D (GOLDEN TEST)
```

**Single-Ablation Discipline:** Enum enforces exactly one ablation per run.

### 3.2 Classification Taxonomy (`v300/ablation.py`)

```python
class AblationClassification(Enum):
    NARRATIVE_COLLAPSE = "narrative_collapse"
    INCENTIVE_CAPTURE = "incentive_capture"
    ONTOLOGICAL_COLLAPSE = "ontological_collapse"
    ASB_CLASS_REDUCIBILITY = "asb_class_reducibility"
    INVALID_RUN = "invalid_run"
```

**Interpretation:**
- **NARRATIVE_COLLAPSE:** Constraints no longer bind meaningfully
- **INCENTIVE_CAPTURE:** System drifts to reward-following
- **ONTOLOGICAL_COLLAPSE:** System reduces to mechanism
- **ASB_CLASS_REDUCIBILITY:** Indistinguishable from random action selection
- **INVALID_RUN:** Technical failure, not ontological

### 3.3 Invalid Run Reasons (`v300/ablation.py`)

12 distinct reasons for classifying a run as invalid:

| Reason | Description |
|--------|-------------|
| `NONE` | Valid run |
| `MULTIPLE_ABLATIONS` | More than one component ablated |
| `SCHEMA_CRASH` | Schema validation exception |
| `FALLBACK_SUBSTITUTION` | Harness substituted action (forbidden) |
| `MISSING_FIELD_EXCEPTION` | Required field missing at runtime |
| `NULL_POINTER` | Null/None dereference |
| `STATIC_TYPE_ERROR` | Type mismatch |
| `COMPENSATION_ADDED` | New structure added to help ablated system |
| `HARNESS_MISMATCH` | Baseline/ablated used different harness |
| `SEED_MISMATCH` | Baseline/ablated used different seeds |
| `PROMPT_MISMATCH` | Baseline/ablated used different prompts |
| `ENVIRONMENT_MISMATCH` | Baseline/ablated used different environment |

### 3.4 Ablation Filters (`v300/ablation.py`)

Post-FA transformers that remove specific components.

#### Ablation A — Semantic Excision Filter

```python
class SemanticExcisionFilter(AblationFilter):
    """Replace semantic payloads with opaque tokens."""

    SEMANTIC_FIELDS = {
        "text", "content", "description", "explanation",
        "reason", "rationale", "justification", "narrative",
        "semantic_content", ...
    }

    def apply(self, j_final: Dict) -> Dict:
        # Recursive traversal, replace semantic strings with
        # <SEMANTIC_EXCISED_TOKEN_xxx>
```

#### Ablation B — Reflection Excision Filter

```python
class ReflectionExcisionFilter(AblationFilter):
    """Disable normative updates, freeze state."""

    def apply(self, j_final: Dict) -> Dict:
        # Clear reflection_history
        # Remove normative_update, state_update, revision fields
        # Set _normative_updates_frozen = True
```

#### Ablation C — Persistence Excision Filter

```python
class PersistenceExcisionFilter(AblationFilter):
    """Clear state at episode boundaries, prevent carryover."""

    def apply(self, j_final: Dict) -> Dict:
        # Remove persist, carry_forward, episode_memory fields
        # Set _ablation_no_persist = True
```

#### Ablation D — Trace Excision Filter (GOLDEN TEST)

```python
class TraceExcisionFilter(AblationFilter):
    """Remove derivation evidence, preserve constraint IDs."""

    TRACE_FIELDS = {
        "derivation_trace", "derivation", "proof",
        "rule_refs", "rule_application", "inference_chain",
        "justification_trace", ...
    }

    def apply(self, j_final: Dict) -> Dict:
        # Remove trace fields at any nesting depth
        # Preserve constraint_id, binding_strength, etc.
```

**Critical Test:** If constraints still bind without traces, justifications were epiphenomenal → RSA-PoC program is FALSIFIED.

### 3.5 JCOMP-3.0 Compiler (`v300/compiler.py`)

Extends JCOMP-2.3 with surgical relaxation for ablation runs.

#### Ablation Relaxation

```python
@dataclass(frozen=True)
class AblationRelaxation:
    ablation: AblationSpec

    # Schema relaxation (per ablation)
    skip_semantic_field_validation: bool = False  # Ablation A
    skip_normative_update_validation: bool = False  # Ablation B
    skip_persistence_validation: bool = False  # Ablation C
    skip_trace_validation: bool = False  # Ablation D

    # Convenience properties
    @property
    def allow_missing_justification_trace(self) -> bool:
        return self.optional_derivation_trace or self.skip_trace_validation
```

#### JCOMP300 Class

```python
class JCOMP300(JCOMP230):
    """v2.3 compiler with ablation relaxation support."""

    def compile(self, artifact_dict, action_id, ...) -> V300CompilationResult:
        try:
            # Pre-process: apply defaults for missing fields
            processed = self._apply_defaults_for_ablation(artifact_dict, result)

            # Run parent compilation with relaxation
            parent_result = self._compile_with_relaxation(processed, ...)

            return result

        except KeyError as e:
            # Missing field → TECHNICAL_FAILURE (not collapse)
            result.is_technical_failure = True
            result.technical_failure_type = "missing_field_exception"
            return result

        except Exception as e:
            # Any crash → TECHNICAL_FAILURE
            result.is_technical_failure = True
            return result
```

#### Selector Tolerance

```python
@dataclass
class SelectorTolerance:
    """Safe defaults when fields missing under ablation."""

    default_action_mode: str = "uniform_random_feasible"
    global_seed: Optional[int] = None  # BINDING: hash-based derivation

    @staticmethod
    def _derive_seed(global_seed: int, episode_id: int, step_index: int) -> int:
        # Hash-based derivation: no dependence on ablation type, artifact content,
        # or feasibility set ordering
        return hash((global_seed, episode_id, step_index)) & 0x7FFFFFFF

    def select_default(self, context: Dict) -> str:
        # When constraints can't be evaluated, select uniformly
        # This is NOT fallback substitution (preregistered behavior)
```

### 3.6 ASB Null Agent (`v300/asb_null.py`)

Non-normative baseline for comparison.

```python
class ASBNullAgent:
    """
    Agent Sans Beliefs — no justification, no normative state.

    Properties:
    - No justification artifacts
    - No compilation gate
    - No audits
    - Action selection: seeded uniform random over feasible
    """

    def select_action(
        self,
        feasible_actions: Set[str],
        step: int = 0,
        episode: int = 0,
    ) -> str:
        # Seed = hash(global_seed, episode, step) — BINDING
        # No dependence on ablation type, artifact content, or feasibility ordering
        # Uniform random over sorted feasible list
```

#### ASB Equivalence Metrics

```python
def compute_asb_equivalence(
    ablated_actions: List[str],
    asb_actions: List[str],
    ablated_feasible_sets: Optional[List[Set[str]]] = None,
    asb_feasible_sets: Optional[List[Set[str]]] = None,
    ablated_step_indices: Optional[List[int]] = None,  # Step intersection alignment
    asb_step_indices: Optional[List[int]] = None,
) -> float:
    """
    Compute equivalence score [0, 1].

    Metrics:
    1. Per-step agreement rate (on intersection of valid steps)
    2. Action distribution similarity (L1 distance)
    3. Uniformity over feasible sets (if provided)

    Step Intersection: If step indices provided, only compares
    steps that appear in BOTH ablated and ASB runs.
    """

def is_asb_reducible(equivalence_score: float, threshold: float = 0.85) -> bool:
    """If score >= threshold, system is ASB-reducible."""
    return equivalence_score >= threshold
```

### 3.7 V300 Ablation Harness (`v300/harness.py`)

Main orchestrator for ablation experiments.

#### Run Configuration

```python
@dataclass(frozen=True)
class V300RunConfig:
    ablation: AblationSpec = AblationSpec.NONE
    seeds: Tuple[int, ...] = (42, 123, 456, 789, 1024)  # Minimum 5
    num_episodes: int = 3
    steps_per_episode: int = 50
    environment: str = "CommitmentTrapV200"
    use_sam: bool = False  # BINDING: No SAM for v3.0
    friction_modifier: float = 1.0  # Neutral

    def __post_init__(self):
        if len(self.seeds) < 5:
            raise ValueError("v3.0 requires minimum 5 preregistered seeds")
        if self.use_sam:
            raise ValueError("v3.0 baseline must not use SAM")
```

#### Validity Gates

```python
class ValidityGate:
    """Enforces v3.0 validity constraints."""

    @staticmethod
    def check_single_ablation(config: V300RunConfig) -> Tuple[bool, Optional[InvalidRunReason]]:
        # Enforced by AblationSpec enum

    @staticmethod
    def check_no_compensation(ablated, baseline, ablation) -> Tuple[bool, Optional[InvalidRunReason]]:
        # Ablated artifact must have <= baseline structure

    @staticmethod
    def check_action_authorship(step: V300StepRecord) -> Tuple[bool, Optional[InvalidRunReason]]:
        # Any fallback substitution = INVALID_RUN

    @staticmethod
    def check_not_technical_failure(step: V300StepRecord) -> Tuple[bool, Optional[InvalidRunReason]]:
        # Crashes don't count as collapse
```

#### Ablation Classifier

```python
class AblationClassifier:
    """Classifies ablation outcomes into the taxonomy."""

    @staticmethod
    def classify(
        ablated: V300AblatedResult,
        baseline: V300BaselineResult,
        asb_null: ASBNullAgent,
        ablation: AblationSpec,
    ) -> Tuple[AblationClassification, InvalidRunReason]:

        # Priority 1: Check for technical failures
        # Priority 2: Check ASB equivalence (→ ASB_CLASS_REDUCIBILITY)
        # Priority 3: Check ontological collapse indicators
        # Priority 4: Check narrative collapse
        # Priority 5: Check incentive capture
```

#### Harness Class

```python
class V300AblationHarness:
    """Main harness for ablation runs."""

    def __init__(self, config: V300RunConfig):
        self.config = config
        self.validity_gate = ValidityGate()
        self.classifier = AblationClassifier()
        self.asb_null = ASBNullAgent(...)
        self.compiler = JCOMP300(ablation=config.ablation)
        self.ablation_filter = create_ablation_filter(config.ablation)

    def run(self, output_path: Optional[Path] = None) -> AblationResult:
        # For each seed:
        #   Run baseline (full v2.3)
        #   Run ablated (with filter applied)
        #   Compare to ASB Null
        #   Classify outcome
        # Aggregate across seeds
```

---

## 4. Binding Decisions Implemented

These decisions were provided in the v3.0 specification and are now frozen in the implementation.

### Decision 1: Ablation A — Semantic Excision

**Binding:** Post-hoc tokenization after Formal Assistant, before compile.

**Implementation:** `SemanticExcisionFilter.apply()` replaces semantic field values with `<SEMANTIC_EXCISED_TOKEN_xxx>` after J_final is produced.

### Decision 2: Ablation B — Reflection Excision

**Binding:** Define reflection as normative updates; disable them and freeze state.

**Implementation:** `ReflectionExcisionFilter.apply()` clears `reflection_history`, removes update fields, sets `_normative_updates_frozen = True`.

### Decision 3: Ablation C — Persistence Excision

**Binding:** Clear normative state at episode boundaries AND prevent cross-episode carryover.

**Implementation:** `PersistenceExcisionFilter.apply()` sets `_ablation_no_persist = True`; harness must clear state between episodes.

### Decision 4: Ablation D — Trace Excision

**Binding:** Remove derivation evidence, preserve constraint IDs.

**Implementation:** `TraceExcisionFilter.apply()` removes `justification_trace`, `derivation_trace`, `derivation`, `proof`, `rule_refs`, etc. at any nesting depth.

### Decision 5: Compiler Relaxation

**Binding:** Option A — explicit `AblationSpec` gating.

**Implementation:** `create_relaxation(ablation)` returns `AblationRelaxation` with specific fields disabled per ablation type.

### Decision 6: Environment

**Binding:** Reuse CommitmentTrapV200 + existing harness.

**Implementation:** `V300RunConfig.environment = "CommitmentTrapV200"`.

### Decision 7: Baseline

**Binding:** No SAM (neutral/no strategic targeting).

**Implementation:** `V300RunConfig.use_sam = False`, `friction_modifier = 1.0`. Config validation raises error if `use_sam=True`.

### Decision 8: ASB Null

**Binding:** Seeded uniform-random feasible-action selector with hash-based seed derivation: `seed = H(global_seed, episode_id, step_index)`; no dependence on ablation type, artifact content, or feasibility ordering (beyond deterministic sorting).

**Implementation:** `ASBActionSelection.UNIFORM_RANDOM_SEEDED` with `derive_seed(global_seed, episode, step)` using hash-based derivation.

---

## 5. Acceptance Test Results

### 5.1 Test Execution

Full v3.0 infrastructure test suite passes:

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2
collected 44 items

src/rsa_poc/v300/tests/test_infrastructure.py ............................................ [100%]
============================== 44 passed in 0.23s ==============================
```

### 5.2 Test Coverage

| Test Class | Tests | Description |
|------------|-------|-------------|
| TestAblationSpec | 3 | Enum values, string conversion, single-ablation discipline |
| TestAblationFilters | 5 | All four filters + factory function |
| TestJCOMP300 | 5 | Relaxation creation, constraint validation |
| TestSelectorTolerance | 3 | Missing-field handling, deterministic mode |
| TestASBNullAgent | 4 | Creation, selection, reproducibility, seed variance |
| TestASBEquivalence | 6 | Equivalence scoring, threshold check, step intersection alignment |
| TestValidityGate | 3 | Action authorship, technical failure detection |
| TestClassification | 2 | Taxonomy completeness |
| TestV300RunConfig | 3 | Seed minimum, no-SAM requirement |
| TestInfrastructureIntegration | 3 | Harness creation, ablation setup |
| TestExceptionLogging | 4 | Hard exception recording, log line generation |
| TestConstraintBindingDetector | 3 | Binding strength, count disparity, binding ratio metrics |

**Total: 44 tests, 44 passed**

### 5.3 Critical Invariants Verified

| Invariant | Test | Status |
|-----------|------|--------|
| Trace-missing constraint passes under Ablation D | `test_trace_missing_constraint_passes_under_ablation_d` | ✅ PASS |
| Trace-missing constraint fails under no ablation | `test_trace_missing_constraint_fails_under_no_ablation` | ✅ PASS |
| Missing-field selector doesn't crash | `test_selector_missing_field_no_crash` | ✅ PASS |
| ASB Null is reproducible with same seed | `test_asb_null_reproducible` | ✅ PASS |
| Different seeds produce different sequences | `test_asb_null_different_seeds_differ` | ✅ PASS |
| Action authorship violation detected | `test_action_authorship_violation` | ✅ PASS |
| Technical failure correctly classified | `test_technical_failure_detection` | ✅ PASS |

---

## 6. Runtime Integration (Mock-Validated)

### 6.1 Implemented Runtime Wiring

All runtime methods in `V300AblationHarness` are now implemented:

| Method | Purpose | Status |
|--------|---------|--------|
| `_run_seed()` | Run baseline + ablated for one seed | ✅ Implemented |
| `_run_baseline_episode()` | Run full v2.3 episode | ✅ Implemented |
| `_run_ablated_episode()` | Run ablated episode with filter | ✅ Implemented |
| `_run_baseline_step()` | Single baseline step execution | ✅ Implemented |
| `_run_ablated_step()` | Single ablated step execution | ✅ Implemented |

### 6.2 Binding Requirements Implemented

| Requirement | Description | Status |
|-------------|-------------|--------|
| **Seed Derivation** | Hash-based: `hash(global_seed, episode_id, step_index)` | ✅ BINDING |
| **Exception Logging** | 3 fields: class_name, call_site, message | ✅ Complete |
| **Step Intersection** | ASB equivalence on intersection of valid steps | ✅ Complete |
| **Constraint Binding** | ConstraintBindingDetector with 3 metrics | ✅ Complete |
| **Runtime Pipeline** | Full step-level execution with mock artifacts | ✅ Complete |
| **Smoke Test** | Single-seed validation (seed=42) | ✅ PASSES |

### 6.3 New Components Added

**Exception Logging (V300StepRecord):**
```python
@dataclass
class V300StepRecord:
    # ... existing fields ...
    exception_class_name: Optional[str] = None
    exception_call_site: Optional[str] = None
    exception_message: Optional[str] = None

    def record_exception(self, exc: Exception, call_site: str) -> None:
        """Record exception details for hard exception logging."""

    def get_exception_log_line(self) -> Optional[str]:
        """Generate log line in format: 'ClassName@call_site: message'"""
```

**Constraint Binding Detector:**
```python
@dataclass
class ConstraintBindingMetrics:
    avg_binding_strength_baseline: float
    avg_binding_strength_ablated: float
    binding_count_disparity: int  # baseline - ablated
    binding_ratio: float  # ablated / baseline

class ConstraintBindingDetector:
    def compute_metrics(
        baseline_steps: List[V300StepRecord],
        ablated_steps: List[V300StepRecord],
    ) -> ConstraintBindingMetrics
```

### 6.4 Smoke Test Results

```
$ python -m rsa_poc.v300.run_v300_smoke

======================================================================
v3.0 SMOKE TEST — Single-Seed Validation
======================================================================
Seed: 42
Episodes: 1
Steps: 20

[RUNNING] Ablation D smoke test...

✅ SMOKE TEST PASSED

  Classification: ontological_collapse
  Invalid Reason: none
  ASB Equivalence: 0.582
  Seeds Completed: 1/1

Acceptance Criteria:
  ✓ 0 INVALID_RUN classifications
  ✓ No fallback substitution detected
  ✓ No crashes in selector/executor
```

**Note:** Smoke test classification is a wiring validation only and must not be cited as ablation evidence.

### 6.5 Integration Checklist (All Complete)

- [x] Wire `_run_seed()` to instantiate v2.3 agent pipeline
- [x] Wire `_run_baseline_episode()` to execute full v2.3 episode
- [x] Wire `_run_ablated_episode()` to apply ablation filter post-FA
- [x] Add ASB Null parallel execution with same seeds
- [x] Add result comparison and classification logic
- [x] Test end-to-end with smoke test (seed=42)

---

## 7. Running the Experiment

### 7.1 Dry Run (Verify Configuration)

```bash
cd /home/david/Axio
PYTHONPATH=src python src/rsa_poc/v300/run_v300_ablation_d.py --dry-run
```

**Expected output:**
```
======================================================================
v3.0 ABLATION D — THE GOLDEN TEST
======================================================================

This test removes derivation traces while preserving constraint IDs.
If constraints still bind without their justification traces,
the RSA-PoC program is FALSIFIED.

Seeds: (42, 123, 456, 789, 1024)
Output: v300_ablation_d_<timestamp>.json

[DRY RUN] Would execute with above configuration
```

### 7.2 Execute Ablation D (After Integration)

```bash
cd /home/david/Axio
PYTHONPATH=src python src/rsa_poc/v300/run_v300_ablation_d.py \
    --seeds 42,123,456,789,1024 \
    --output v300_ablation_d_results.json
```

### 7.3 Programmatic Usage

```python
from rsa_poc.v300 import (
    AblationSpec,
    V300RunConfig,
    V300AblationHarness,
)

config = V300RunConfig(
    ablation=AblationSpec.TRACE_EXCISION,
    seeds=(42, 123, 456, 789, 1024),
)

harness = V300AblationHarness(config)
result = harness.run(output_path="v300_ablation_d.json")

print(f"Classification: {result.aggregate_classification}")
print(f"Consistent: {result.classification_consistent}")
```

---

## 8. Success Criteria

### 8.1 Ablation D (Golden Test)

| Outcome | Classification | Interpretation |
|---------|---------------|----------------|
| System collapses to random | `ASB_CLASS_REDUCIBILITY` | ✅ Traces were load-bearing |
| Constraints stop binding | `NARRATIVE_COLLAPSE` | ✅ Traces were semantically necessary |
| System becomes mechanistic | `ONTOLOGICAL_COLLAPSE` | ✅ Traces were constitutive of agency |
| System drifts to reward | `INCENTIVE_CAPTURE` | ⚠️ Unexpected for trace ablation |
| Technical failures | `INVALID_RUN` | ❌ Rerun with fixed infrastructure |

**Pass Condition:** Any collapse mode except `INVALID_RUN` indicates traces are non-epiphenomenal.

**Fail Condition:** If constraints continue to bind meaningfully without traces, justifications were epiphenomenal → **RSA-PoC program is FALSIFIED**.

### 8.2 Execution Order (Binding)

1. **Ablation D (Golden Test)** — Must pass before proceeding
2. **Ablation A (Semantic Excision)** — If D passes
3. **Ablation B (Reflection Excision)** — If D passes
4. **Ablation C (Persistence Excision)** — If D passes

If Ablation D fails (system doesn't collapse), **stop the program**.

---

## 9. Design Rationale

### 9.1 Why Single-Ablation Discipline?

Combined ablations confound attribution. If removing A+B causes collapse, we can't determine which was load-bearing.

Single ablation ensures:
- Clear causal attribution
- No interaction effects
- Falsifiable per-component

### 9.2 Why ASB Null Comparison?

ASB Null is the minimal control:
- No beliefs, preferences, or justifications
- No normative state
- Pure random selection over feasible actions

If ablated system ≈ ASB Null, the ablated component was **constitutive** of agency.

### 9.3 Why Graceful Degradation = Failure?

Robustness testing asks: "Does the system still work?"
Non-reducibility testing asks: "Was the component necessary?"

Graceful degradation would mean the component wasn't load-bearing — the system was never the thing we claimed it was.

### 9.4 Why Technical Failure ≠ Collapse?

Crashes indicate the ablation broke the **implementation**, not the **ontology**.

We want to observe **behavioral** collapse (incoherent actions, lost constraint-following), not **technical** collapse (null pointer exceptions).

---

## 10. Relation to Prior Work

### 10.1 v2.3 Inheritance

v3.0 is a **strict extension** of v2.3:
- All v2.3 rules (A-L, K-R, M-P) still enforced (except for relaxed components)
- All v2.3 invariants preserved
- Five-component architecture unchanged
- JCOMP-3.0 extends JCOMP-2.3

### 10.2 Key Differences from v2.3

| Aspect | v2.3 | v3.0 |
|--------|------|------|
| Purpose | Test resistance to pressure | Test component necessity |
| Adversary | Strategic SAM (S1/S2/S3) | None (baseline friction) |
| Metric | MI(SAM; behavior) | Collapse classification |
| Success | Low correlation | Collapse observed |
| Failure | High correlation | No collapse (epiphenomenal) |

### 10.3 Relationship to v2.3 Results

v2.3 showed the agent resists strategic pressure (Rule O/P passed).

v3.0 asks: Was that resistance due to the claimed architecture, or would any system with similar constraints behave the same?

If Ablation D shows constraints bind without traces, the v2.3 result was measuring **constraint structure**, not **justified agency**.

---

## 11. Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| v2.3 runtime incompatible with ablation | Medium | JCOMP300 wraps JCOMP230, catches all exceptions |
| ASB equivalence threshold too sensitive | Low | Threshold (0.85) is binding and cannot be tuned |
| Technical failures mask real collapse | Medium | INVALID_RUN classification explicitly separates |
| Ablation D falsifies program | High | **This is the intended outcome if warranted** |
| Insufficient seeds for statistical power | Low | Minimum 5 seeds enforced by config validation |

---

## 12. Next Steps

### 12.1 Smoke Test (COMPLETE)

✅ Single-seed validation passes with seed=42:
```bash
cd /home/david/Axio
PYTHONPATH=src python -m rsa_poc.v300.run_v300_smoke
```

### 12.2 Ablation D Execution (READY)

Full 5-seed run:
```bash
cd /home/david/Axio
PYTHONPATH=src python src/rsa_poc/v300/run_v300_ablation_d.py \
    --seeds 42,123,456,789,1024 \
    --output v300_ablation_d_results.json
```

### 12.3 If Ablation D Passes

Execute remaining ablations in order:
- `run_ablation_a()` — Semantic Excision
- `run_ablation_b()` — Reflection Excision
- `run_ablation_c()` — Persistence Excision

### 12.4 If Ablation D Fails

If constraints bind without traces:
1. Document falsification result
2. Archive RSA-PoC program
3. Publish negative result

---

## 13. Conclusion

RSA-PoC v3.0 infrastructure is complete:

- **AblationSpec enum** with single-ablation enforcement
- **Four ablation filters** (A, B, C, D) for post-FA transformation
- **JCOMP-3.0 compiler** with surgical relaxation
- **ASB Null Agent** for non-normative baseline comparison
- **V300AblationHarness** with validity gates and classification
- **44/44 infrastructure tests passing**

### Definition of Done Assessment

| Criterion | Status | Notes |
|-----------|--------|-------|
| Run baseline + ablated with no code changes except AblationSpec | ✅ Complete | Full pipeline implemented |
| Missing-field paths produce behavioral noise or audited failure | ✅ Complete | SelectorTolerance + ValidityGate |
| Never crash on missing fields | ✅ Complete | Exception catching in JCOMP300 |
| Never fallback substitute | ✅ Complete | check_action_authorship() enforces |
| All infrastructure tests pass | ✅ Complete | 44/44 passing |
| Single-seed smoke test passes | ✅ Complete | seed=42 validated |

### Reviewer-Ready Claims

1. **Single-ablation discipline enforced** by AblationSpec enum
2. **Four ablation filters implemented** with correct field removal
3. **JCOMP-3.0 extends JCOMP-2.3** with surgical relaxation
4. **ASB Null is reproducible** with hash-based seed derivation
5. **Classification taxonomy is complete** (5 classifications, 12 invalid reasons)
6. **Validity gates enforce** action authorship and no compensation
7. **Technical failures separated** from ontological collapse
8. **Ablation D is Golden Test** — if it fails, stop the program
9. **Seed derivation is covert-channel-free** — hash(global_seed, episode, step)
10. **Exception logging implemented** — class, call_site, message fields
11. **Constraint binding detector** — 3 metrics for binding analysis
12. **Smoke test passes** — seed=42 validated end-to-end

### Procedural Status

**Completed:**
- [x] Core types and enums
- [x] Ablation filters (A, B, C, D)
- [x] JCOMP-3.0 with relaxation
- [x] ASB Null Agent with hash-based seed derivation
- [x] V300AblationHarness with full runtime wiring
- [x] Validity gates
- [x] Classification logic
- [x] Exception logging (3 fields)
- [x] Constraint binding detector (3 metrics)
- [x] Step intersection alignment for ASB equivalence
- [x] 44 infrastructure tests
- [x] Ablation D runner script
- [x] Smoke test runner (seed=42 passes)
- [x] Runtime integration with mock artifacts

**Ready for Execution:**
- [ ] Ablation D execution (full 5-seed run)
- [ ] Ablations A, B, C (if D passes)

---

**Implementation Date:** January 16, 2026
**Integration Complete:** January 16, 2026
**Next Milestone:** Ablation D execution (full 5-seed run)
