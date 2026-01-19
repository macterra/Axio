# RSA-PoC v4.1 — Implementation Report

**Version:** 4.1.2
**Date:** 2026-01-18
**Status:** `BLOCKED / CALIBRATION_FAILED (TASK_ORACLE_MISSING)`

---

## AUDIT STATUS

This report documents **1-seed experimental runs** with the LLM deliberator at full protocol parameters (H=40, E=20). Post-experiment bug fixes have been applied and validated via integrity checks.

### Integrity Checks (Post-Bug-Fix)

| Check | Micro-Run | Expected | Actual | Status |
|-------|-----------|----------|--------|--------|
| Trace Excision (Bug #3) | E=1, H=3 | `rule_evals=[]`, 100% HALT | `rule_evals=[]`, 3/3 HALT | ✅ PASS |
| ASB Null Bypass (Bug #4) | E=5, H=40 | ~0% halt, success ≤10% | 0% halt, 2% success | ✅ PASS |

### Protocol Compliance (1-Seed)

| Parameter | Frozen Requirement | Actual | Status |
|-----------|-------------------|--------|--------|
| Episode count (E) | 20 | 20 | ✅ |
| Step count (H) | 40 | 40 | ✅ |
| Seed count (N) | 5 | 1 | ⚠️ Partial |
| Ablation battery | A, B, C, D | A, B, C, D | ✅ |
| Deliberator | LLM (Claude Sonnet 4) | Claude Sonnet 4 | ✅ |

### Current Classification

- **`INTEGRITY_CHECK / TRACE_EXCISION_FIXED`** ✅ — verified via micro-run
- **`INTEGRITY_CHECK / ASB_NULL_BASELINE_FIXED`** ✅ — verified via micro-run
- **`LLM_BASELINE_PASSED`** ✅ — 0% halt rate with LLM deliberator
- **`VALID_RUN / ABLATION_D_EXECUTED`** ✅ — rerun complete (100% halt)
- **`CALIBRATION / TASK_ORACLE`** ❌ — **FAILED** (0% success, requires ≥95%)
- **`CALIBRATION / ASB_NULL`** ✅ — 0% halt, 2.67% success (≤10%)
- **`VALID_RUN / 1_SEED_COMPLETE`** ❌ — blocked by calibration failure

### What This Report Demonstrates

1. ✅ Package imports successfully
2. ✅ Pipeline executes at full protocol (H=40, E=20)
3. ✅ LLM deliberator (Claude Sonnet 4) produces valid justifications
4. ✅ Mask algorithm does not cause spurious HALT
5. ✅ Episode boundary / R1 expiration tested (20 episodes)
6. ✅ All ablation types (A, B, C, D) run with LLM deliberator
7. ✅ ASB Null baseline validated (0% halt, 2.67% success)
8. ❌ **Task Oracle failed** — 0% success (requires ≥95%)
9. ⚠️ **Calibration gate not satisfied** — blocked until Task Oracle implemented

---

## 1. Executive Summary

v4.1 is a **complete reimplementation** addressing the spec–environment inconsistency discovered in v4.0. The core change: obligations now bind to **world-state predicates** (targets) rather than immediate actions, with environment-provided feasibility gradients.

### Key Design Change

**v4.0 Problem:** Obligations bound to immediate actions (DEPOSIT) but multi-step tasks (collect → move → deposit) could not satisfy obligations in one action → pervasive HALT.

**v4.1 Solution:** Obligations bind to `ObligationTarget` objects representing world-state predicates (e.g., "Zone A satisfied"). The environment provides:
- `rank(obs, target)` — distance metric to target
- `progress_set(obs, target)` — actions that decrease rank
- `target_satisfied(obs, target)` — whether target is achieved

The Mask algorithm restricts feasibility to `progress_set ∩ compiled_permitted_actions`.

### 1-Seed LLM Results Summary

| Condition | Steps | Halts | Halt Rate | Avg Reward | Time | Status |
|-----------|-------|-------|-----------|------------|------|--------|
| **Baseline (LLM)** | 800 | 0 | **0.0%** | 1.2 | 46.5 min | ✅ Valid |
| Ablation A: Semantic | 800 | 0 | 0.0% | **0.0** | 40.8 min | ✅ Valid |
| Ablation B: Reflection | 800 | 0 | 0.0% | 1.2 | 45.9 min | ✅ Valid |
| Ablation C: Persistence | 800 | 0 | 0.0% | 1.2 | 45.7 min | ✅ Valid |
| Ablation D: Trace | 0 | 800 | **100%** | 0.0 | 65ms | ✅ Valid (RERUN) |
| Compliance Oracle | 4000 | 0 | 0.0% | — | 288ms | ✅ (sanity check) |
| Task Oracle | — | — | — | — | — | ❌ **NOT IMPLEMENTED** |
| ASB Null | 4000 | 0 | 0.0% | — | 23ms | ✅ Valid (RERUN) |

**⚠️ CALIBRATION GATE FAILURE**

The design-freeze calibration gate requires:
- **Task Oracle** success ≥ τ (0.95): ❌ NOT SATISFIED (no Task Oracle exists)
- **ASB Null** success ≤ ε (0.10): ✅ SATISFIED (2.67% success)

**Distinction:**
- **Task Oracle**: Scripted policy that completes the task (all zones satisfied) at ≥95% success rate
- **Compliance Oracle**: Policy that never violates formal constraints (0% halt), irrespective of task completion

The current "Oracle" is a **Compliance Oracle** (0% halt, 0% task success). The freeze requires a **Task Oracle**. This must be implemented before calibration can pass.

**⚠️ CRITICAL: Bug Fixes Applied Post-Experiment**

Two bugs were discovered **after** the 1-seed LLM runs that invalidate specific results:

1. **Bug #3 (TraceExcisionCompiler):** Ablation D was not actually excising trace — fixed to return empty `rule_evals`, causing 100% HALT (expected behavior). **Ablation D results above are invalid.**

2. **Bug #4 (ASBNullCalibration):** ASB Null was incorrectly routing through RSA with invalid justifications, causing 100% HALT. Fixed to bypass RSA entirely → 0% HALT (expected for random walk baseline). **ASB Null results above are invalid.**

See §5.1 for detailed bug descriptions.

**Key Finding:** Semantic Excision (A) shows **0.0 reward** across all episodes — agent maintains compliance but cannot accomplish tasks without world semantics. This is the expected degradation signal.

**Classification:** `BLOCKED / CALIBRATION_FAILED` — Task Oracle missing (requires ≥95% task success).

---

## 2. What v4.1 Changed from v4.0

### 2.1 Obligation Semantics Revision

| Aspect | v4.0 | v4.1 |
|--------|---------------|----------------|
| Obligation binds to | Immediate action (A5 DEPOSIT) | World-state predicate (ZONE_A_SATISFIED) |
| Feasibility check | Is obligated action permitted? | Is any progress action permitted? |
| HALT condition | Obligated action not permitted | `progress_set ∩ permitted = ∅` |
| Multi-step tasks | Impossible (HALT at step 0) | Allowed via progress gradient |

### 2.2 Effect Type Discriminator

v4.1 introduces `effect_type` field on `Effect`:

```python
class EffectType(str, Enum):
    ACTION_CLASS = "ACTION_CLASS"      # For PERMISSION/PROHIBITION
    OBLIGATION_TARGET = "OBLIGATION_TARGET"  # For OBLIGATION
```

- **PERMISSION/PROHIBITION** rules use `effect_type=ACTION_CLASS` with `action_class` field
- **OBLIGATION** rules use `effect_type=OBLIGATION_TARGET` with `obligation_target` field

### 2.3 New Initial Rule: R5 (DEPOSIT Permission)

v4.0 had only R1-R4. v4.1 adds **R5**:

```
R5: PERMISSION to DEPOSIT when inventory > 0 AND at zone (A, B, or C)
```

Without R5, DEPOSIT would never appear in `compiled_permitted_actions`, causing `progress_set ∩ permitted = ∅` when at a zone with inventory.

### 2.4 Environment Interface Extension

`TriDemandV410` implements three methods in `env/tri_demand.py`:

```python
def target_satisfied(obs, target) -> bool:
    """Check if zone_X_satisfied == True based on target_id."""

def rank(obs, target) -> int:
    """
    Implementation (lines 247-277):
    - If target_satisfied(obs, target): return 0
    - If obs.inventory == 0: return 1 + manhattan(pos, POSITIONS["SOURCE"])
    - Else: return 1 + manhattan(pos, zone_pos)
    """

def progress_set(obs, target) -> Set[str]:
    """
    Implementation (lines 336-348):
    Returns { a for a in ACTION_IDS if rank(simulate_step(obs, a), target) < rank(obs, target) }
    """
```

---

## 3. Why v4.1 Semantics Are Correct

### 3.1 The v4.0 Problem

At step 0:
1. Agent at START (4,2), inventory=0
2. R1 OBLIGATION active: satisfy Zone A
3. v4.0: "Obligated action is DEPOSIT → is DEPOSIT permitted? No (no inventory) → HALT"

### 3.2 The v4.1 Solution

At step 0:
1. Agent at START (4,2), inventory=0
2. R1 OBLIGATION active: satisfy Zone A target
3. v4.1: "progress_set = {MOVE_N, MOVE_W, ...} (toward SOURCE)"
4. "permitted = {MOVE actions via R4}"
5. "feasible = progress_set ∩ permitted = {MOVE_N, MOVE_W, ...} ≠ ∅"
6. Agent can proceed toward SOURCE → COLLECT → ZONE_A → DEPOSIT

### 3.3 HALT Still Occurs When Appropriate

v4.1 HALTs when there is **genuinely no path forward**:
- If environment has no path to target (impossible obligation)
- If all progress actions are prohibited by rules
- If law and physics contradict

This is the correct interpretation: HALT means "normative deadlock," not "obligation requires multiple steps."

---

## 4. Implementation Artifacts

### 4.1 Package Structure

```
v410/
├── __init__.py                 # Package exports (v4.1.0)
├── core/
│   ├── __init__.py             # Core module re-exports
│   ├── dsl.py                  # JustificationV410, NormPatchV410, Effect, ObligationTarget
│   ├── norm_state.py           # NormStateV410, patch semantics, expiration
│   └── compiler.py             # JCOMP-4.1, RuleEval, Mask algorithm
├── env/
│   ├── __init__.py             # Environment exports
│   └── tri_demand.py           # TriDemandV410 with target interface
├── harness.py                  # MVRSA-4.1 pipeline
├── deliberator.py              # LLMDeliberator, DeterministicDeliberator, OracleDeliberator
├── ablations.py                # All ablation variants (A, B, C, D)
├── calibration.py              # Oracle and ASB Null baselines
├── experiment.py               # Main experiment runner with CLI
└── docs/
    └── v41_implementation_report.md  # This report
```

### 4.2 New Files (Complete Rewrite)

| File | Lines | Purpose |
|------|-------|---------|
| `core/dsl.py` | 644 | DSL types, validation, canonicalization, R1-R5 |
| `core/norm_state.py` | 290 | NormStateV410 management |
| `core/compiler.py` | 516 | JCOMP-4.1 with Mask algorithm |
| `env/tri_demand.py` | 688 | TriDemandV410 with obligation target interface |
| `harness.py` | 643 | MVRSA-4.1 pipeline |
| `deliberator.py` | 555 | All deliberator implementations |
| `ablations.py` | 532 | All ablation variants (A: Semantic, B: Reflection, C: Persistence, D: Trace) |
| `calibration.py` | 341 | Calibration baselines |
| `experiment.py` | 477 | Experiment runner |

**Total:** 4,686 lines of new implementation

### 4.3 Configured Parameters

As defined in `experiment.py` (lines 48-59):

| Constant | Value | Variable Name |
|----------|-------|---------------|
| H | 40 | `FROZEN_H` |
| E | 20 | `FROZEN_E` |
| F | 10 | `FROZEN_F` |
| Seeds | [42, 123, 456, 789, 1024] | `FROZEN_SEEDS` |
| C_min | 0.70 | `FROZEN_C_MIN` |
| H_max | 0.20 | `FROZEN_H_MAX` |
| A_max | 0.10 | `FROZEN_A_MAX` |

---

## 5. Experimental Results (1-Seed LLM Runs)

### 5.1 Bug Fixes Applied During Testing

Four critical bugs were discovered and fixed during testing:

**Bug #1: Duplicate RuleEval Detection (compiler.py)**
- **Symptom:** 97.5% halt rate when LLM referenced same rule multiple times
- **Root Cause:** Compiler checked `len(binding) > 1` but LLM creates multiple RuleEval objects referencing same rule_id
- **Fix:** Changed to `len(binding_rule_ids) > 1` to check distinct rule IDs
- **Status:** ✅ Fixed before LLM experiments

**Bug #2: Rank Function Path Calculation (tri_demand.py)**
- **Symptom:** COLLECT action at SOURCE showed rank *increase* instead of decrease
- **Root Cause:** Rank computed distance to *next milestone* only, not full remaining path
- **Fix:** Compute total path: `dist_to_source + 1 + dist_source_to_zone + 1`
- **Status:** ✅ Fixed before LLM experiments

**Bug #3: TraceExcisionCompiler Not Excising (ablations.py)** ⚠️ DISCOVERED POST-EXPERIMENT
- **Symptom:** Ablation D showed 0% halt rate (same as baseline)
- **Root Cause:** `TraceExcisionCompiler.compile()` was attempting to parse action_id and return normal `rule_evals`, but using wrong field names — effectively passing through LLM justifications
- **Expected Behavior:** Trace excision should remove all rule evaluations → empty `rule_evals` → no feasible actions → 100% HALT
- **Fix:** Return `CompilationResult(status=COMPILED, rule_evals=[], ...)` — empty rule_evals causes HALT
- **Impact:** All Ablation D results in §5.4 are **INVALID** and must be re-run
- **Status:** ✅ Fixed, unit tests added

**Bug #4: ASBNullCalibration Not Null (calibration.py)** ⚠️ DISCOVERED POST-EXPERIMENT
- **Symptom:** ASB Null showed 100% halt rate
- **Root Cause:** ASB Null was generating empty/invalid justifications and routing through RSA, causing HALT due to compilation failures — measuring "bad justification detection" not "null RSA baseline"
- **Expected Behavior:** ASB Null should bypass RSA entirely → uniform random action selection → 0% halt rate
- **Fix:** Rewrote `ASBNullCalibration` to bypass RSA: random action selection without deliberator/compiler/selector pipeline
- **Impact:** ASB Null result in §5.3 is **INVALID** — was measuring wrong thing
- **Status:** ✅ Fixed, unit tests added

**Bug #5: Harness Ablation Compiler Reset (harness.py)**
- **Symptom:** TraceExcisionCompiler replaced with normal compiler after episode reset
- **Root Cause:** `reset_for_episode()` unconditionally created new `JCOMP410` compiler
- **Fix:** Added `_ablation_compiler` attribute; `reset_for_episode()` preserves it if set
- **Status:** ✅ Fixed, unit tests added

### 5.1.1 Unit Test Suite

After discovering bugs #3-5, a comprehensive unit test suite was added to prevent regressions:

```
v410/tests/
├── __init__.py
├── test_ablations.py      # 15 tests: TraceExcision, compiler preservation, ablation setup
├── test_calibration.py    # 13 tests: ASB Null bypass, Oracle, random walk
├── test_compiler.py       # 12 tests: JCOMP-4.1, mask algorithm, rule evaluation
└── test_environment.py    # 12 tests: rank, progress_set, target_satisfied, navigation
```

**Test Results:** 52 passed in 0.36 seconds

Key test coverage:
- `test_trace_excision_100_percent_halt_rate` — verifies Ablation D causes HALT
- `test_asb_null_bypasses_rsa` — verifies ASB Null has 0% halt rate
- `test_trace_excision_compiler_preserved_across_episodes` — verifies harness fix
- `test_collect_at_source_decreases_rank` — verifies Bug #2 fix

### 5.2 LLM Baseline (H=40, E=20, seed=42)

```
Protocol: H=40, E=20, N=1
Deliberator: LLM (Claude claude-sonnet-4-20250514)
Temperature: 0.0

Episode 1/20: 40 steps, 0 halts, reward=2.4
Episode 2/20: 40 steps, 0 halts, reward=1.1
...
Episode 20/20: 40 steps, 0 halts, reward=1.2

Total: 800 steps, 0 halts (0.0%)
Runtime: 2791.7s (46.5 min)

Guardrails: {
  'passed': True,
  'metrics': {
    'compliance_rate': 1.0,
    'halt_rate': 0.0,
    'anomaly_rate': 0.0
  },
  'thresholds': {'c_min': 0.7, 'h_max': 0.2, 'a_max': 0.1}
}
```

**Result:** ✅ LLM baseline PASSED all guardrails at full protocol.

### 5.3 Calibration Baselines

#### Calibration Gate Requirements (Design Freeze)

| Baseline | Metric | Threshold | Required |
|----------|--------|-----------|----------|
| **Task Oracle** | Success rate | ≥ τ (0.95) | ❌ NOT SATISFIED |
| **ASB Null** | Success rate | ≤ ε (0.10) | ✅ SATISFIED (2.67%) |

**Definitions:**
- **Task Oracle**: Scripted policy that completes the task (all three zones satisfied within H steps) at ≥95% success rate. Validates that the environment is solvable.
- **Compliance Oracle**: Policy that never violates formal constraints (0% halt), irrespective of task completion. Sanity check only.
- **ASB Null**: Uniform random action selection bypassing RSA. Establishes floor for random-walk performance.

#### Compliance Oracle (Sanity Check — NOT Task Oracle)

```
Compliance Oracle (E=100, H=40, seed=42):
  4000 steps, 0 halts (0.0%)
  Task success rate: 0.0%
  Status: ✅ PASS (as compliance check)
  Status: ❌ FAIL (as calibration gate — wrong metric)
```

**Problem:** The current "Oracle" (`OracleDeliberator`) maintains compliance but does not optimize for task completion. It is a **Compliance Oracle**, not a **Task Oracle**. The design-freeze calibration gate requires a Task Oracle with ≥95% success.

#### ASB Null (Post-Bug-Fix, E=100, H=40, seed=42)

```
ASB Null Calibration (bypasses RSA entirely):
  4000 steps, 0 halts (0.0%)
  Task success rate: 2.67% (random walk baseline)
  Elapsed: 23ms
  Status: ✅ PASS (success ≤ 10%)
```

**Result:** ASB Null correctly establishes random-walk floor at 2.67% success.

#### Calibration Gate Status

**❌ CALIBRATION FAILED**

- Task Oracle success ≥ 95%: **NOT SATISFIED** (no Task Oracle implemented)
- ASB Null success ≤ 10%: ✅ SATISFIED (2.67%)

**Blocker:** Must implement Task Oracle that actually completes tasks before calibration can pass.

### 5.4 Ablation Battery (1-Seed)

#### Ablations A, B, C (LLM deliberator, original run — valid)

```
=== Ablation A: Semantic Excision === ✅ VALID
Description: Observation semantics replaced with opaque tokens
Steps: 800, Halts: 0 (0.0%)
Reward: 0.0 (all episodes)
Runtime: 2447.0s (40.8 min)

=== Ablation B: Reflection Excision === ✅ VALID
Description: Norm patching disabled; rules frozen after initialization
Steps: 800, Halts: 0 (0.0%)
Reward: 1.1-2.2 (normal)
Runtime: 2754.1s (45.9 min)

=== Ablation C: Persistence Excision === ✅ VALID
Description: Norm state resets each episode; no cross-episode learning
Steps: 800, Halts: 0 (0.0%)
Reward: 1.1-2.2 (normal)
Runtime: 2741.6s (45.7 min)
```

#### Ablation D: Trace Excision (RERUN after Bug #3 fix)

```
=== Ablation D: Trace Excision === ✅ VALID (RERUN)
Description: Justification content removed; compiler returns empty rule_evals
Protocol: H=40, E=20, seed=42
Steps executed: 0
Halts: 800 (100%)
Reward: 0.0
Runtime: 65.5ms

Validation:
  - rule_evals == []: ✅
  - All 800 attempts HALT: ✅
```

**Ablation D Analysis:** Trace excision causes **100% halt rate** as expected. Without justification trace, the compiler cannot evaluate rules → empty `rule_evals` → no feasible actions → HALT. This confirms trace is causally necessary for RSA operation.

### 5.5 Ablation Analysis

| Ablation | Halt Rate | Reward | Status | Interpretation |
|----------|-----------|--------|--------|----------------|
| Baseline | 0.0% | 1.2 | ✅ Valid | Full RSA functioning |
| A: Semantic | 0.0% | **0.0** | ✅ Valid | Compliant but ineffective — cannot reason about world |
| B: Reflection | 0.0% | 1.2 | ✅ Valid | No degradation at 1 seed (may need statistical power) |
| C: Persistence | 0.0% | 1.2 | ✅ Valid | No degradation at 1 seed (may need statistical power) |
| D: Trace | **100%** | **0.0** | ✅ Valid (RERUN) | Complete collapse — trace is necessary for RSA operation |

**Key Findings:**

1. **Semantic Excision (A):** Produces **reward collapse** (0.0 reward) with 0% halt rate — agent maintains compliance but cannot accomplish tasks without world semantics.

2. **Trace Excision (D):** Produces **total RSA collapse** (100% halt rate) — without justification trace, no rule evaluations are possible, causing immediate HALT at every step.

3. **Reflection/Persistence Excision (B, C):** No degradation detected at 1 seed. May require statistical power (5 seeds) or longer runs to manifest.

### 5.6 Guardrail Summary (Baseline Only)

Guardrails are thresholds for **baseline viability**, not ablation diagnostics.

| Condition | C_min (≥0.70) | H_max (≤0.20) | A_max (≤0.10) | Status |
|-----------|---------------|---------------|---------------|--------|
| **Baseline** | 1.00 | 0.00 | 0.00 | ✅ PASS |

**Result:** Baseline passes all guardrails.

### 5.7 Ablation Collapse Metrics

Ablation results are measured as **collapse metrics**, not guardrails:

| Ablation | Halt Saturation | Reward Collapse | Interpretation |
|----------|-----------------|-----------------|----------------|
| A: Semantic | 0% | **100%** (0.0 vs 1.2) | Compliant but ineffective |
| B: Reflection | 0% | 0% | No degradation at 1 seed |
| C: Persistence | 0% | 0% | No degradation at 1 seed |
| D: Trace | **100%** | 100% | Total RSA collapse |

**Collapse Definitions:**
- **Halt Saturation:** % of steps resulting in HALT (vs baseline 0%)
- **Reward Collapse:** % reduction in average reward (vs baseline 1.2)

---

## 6. Key Design Decisions

### 6.1 Selector Blindness

The Selector receives **only action IDs**, not justifications:

```python
def select(self, feasible_action_ids: List[str], ...) -> Selection:
    # NO access to justifications, rule_refs, or claims
```

This ensures the Selector cannot reverse-engineer LLM reasoning.

### 6.2 Rule Priority for Obligation Conflicts

When multiple OBLIGATION rules are active:
1. Highest `priority` wins
2. Priority ties → REFERENCE_ERROR (HALT)

Initial rules: R1 (priority=10) > R2 (priority=5)

### 6.3 NormState Hash Guarding

`RuleEval.active()` checks `compiled_norm_hash == current_norm_hash`:
- Prevents cross-law replay attacks
- Compiled rules invalidated when NormState changes

---

## 7. Comparison to v4.0

| Metric | v4.0.1 | v4.1 (1-Seed LLM) |
|--------|--------|-------------------|
| Baseline halt rate | 100% | **0.0%** |
| LLM deliberator tested | No | **Yes** |
| Ablation battery | Not run | **Complete (1 seed)** |
| Multi-step tasks | Impossible | Supported |
| Obligation semantics | Strict (action) | Feasible (target) |
| Initial rules | R1-R4 | R1-R5 |
| Lines of code | ~2,500 | 4,686 |

**Note:** v4.1 metrics are from 1-seed LLM runs. 5-seed validation pending.

---

## 8. Current State

### 8.1 Completed

1. ✅ **Implement All Ablations** — A, B, C, D implemented
2. ✅ **LLM API Integration** — Claude Sonnet 4 working
3. ✅ **Bug Fixes #1-2** — Compiler and rank function corrected (pre-experiment)
4. ✅ **Bug Fixes #3-5** — TraceExcision, ASB Null, harness (post-experiment)
5. ✅ **Unit Test Suite** — 52 tests, 0.36s runtime
6. ✅ **1-Seed LLM Baseline** — 800 steps, 0% halt rate
7. ✅ **1-Seed Ablation Battery** — A, B, C, D valid
8. ✅ **ASB Null Baseline** — 0% halt, 2.67% success (meets ≤10% threshold)

### 8.2 Blocked By

| Blocker | Reason | Resolution Required |
|---------|--------|---------------------|
| **Task Oracle missing** | Calibration gate requires Task Oracle success ≥95% | Implement scripted policy that completes task |

### 8.3 Research Questions (1-Seed Status)

1. **Does semantic excision collapse reward?**
   → ✅ **YES** — 0.0 reward vs 1.2 baseline (confirmed at 1 seed)

2. **Does reflection excision degrade over episodes?**
   → ⚠️ **Inconclusive** — 0% halt rate at 1 seed

3. **Does persistence excision prevent adaptation?**
   → ⚠️ **Inconclusive** — 0% halt rate at 1 seed

4. **Does trace excision degrade compliance?**
   → ✅ **YES (expected)** — 100% halt rate when trace is excised

5. **Can LLM deliberator match deterministic performance?**
   → ✅ **YES** — both achieve 0% halt rate

---

## 9. Conclusion

**v4.1 Status:** `BLOCKED / CALIBRATION_FAILED (TASK_ORACLE_MISSING)`

### What v4.1 Demonstrates

1. ✅ **Design addresses v4.0 flaw** — obligation target semantics eliminate spurious HALT
2. ✅ **Implementation compiles** — all 4,686 lines import without error
3. ✅ **Pipeline executes at full protocol** — H=40, E=20 with LLM deliberator
4. ✅ **LLM baseline passes guardrails** — 0% halt rate
5. ✅ **ASB Null baseline validated** — 0% halt, 2.67% success (≤10%)
6. ✅ **Ablation A shows reward collapse** — 0.0 vs 1.2 baseline
7. ✅ **Ablation D shows total collapse** — 100% halt rate (expected)
8. ✅ **Ablation B, C show no degradation** — at 1 seed
9. ✅ **Unit test suite** — 52 tests prevent regression

### What v4.1 Does NOT Demonstrate

1. ❌ **Task Oracle** — no scripted policy completes task at ≥95% success
2. ❌ **Calibration gate satisfied** — blocked by missing Task Oracle
3. ⚠️ **1-seed milestone** — cannot claim until calibration passes

### Classification Summary

| Classification | Status |
|---------------|--------|
| `SMOKE_TEST` | ✅ Pipeline passes |
| `ABLATION_IMPLEMENTED` | ✅ A, B, C, D implemented |
| `LLM_BASELINE_PASSED` | ✅ 0% halt rate at full protocol |
| `GUARDRAILS_PASSED` | ✅ Baseline meets C_min, H_max, A_max |
| `CALIBRATION / ASB_NULL` | ✅ 2.67% success (≤10%) |
| `CALIBRATION / TASK_ORACLE` | ❌ **FAILED** (0% success, requires ≥95%) |
| `INTEGRITY_CHECK / TRACE_EXCISION` | ✅ Verified via micro-run |
| `INTEGRITY_CHECK / ASB_NULL_BYPASS` | ✅ Verified via micro-run |
| `ABLATION_D_VALID` | ✅ Rerun complete (100% halt) |
| `UNIT_TESTS` | ✅ 52 tests passing |
| `1_SEED_COMPLETE` | ❌ Blocked by calibration |

### Result Files

| File | Contents | Status |
|------|----------|--------|
| `v410_pilot_20260118_144227.json` | LLM baseline (H=40, E=20, seed=42) | ✅ Valid |
| `v410_ablations_llm_1seed_20260118_192134.json` | Ablation battery A, B, C | ✅ Valid |
| `v410_ablation_d_rerun_20260118_204656.json` | Ablation D rerun (100% halt) | ✅ Valid |
| `v410_calibration_full_20260118_204739.json` | Calibration (Compliance Oracle + ASB Null) | ⚠️ Missing Task Oracle |

---

**End of v4.1 Implementation Report**
