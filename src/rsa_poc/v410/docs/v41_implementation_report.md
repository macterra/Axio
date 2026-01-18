# RSA-PoC v4.1 — Implementation Report

**Version:** 4.1.0
**Date:** 2026-01-18
**Status:** `SMOKE_TEST / PIPELINE_PASSES_SHORT_HORIZON`

---

## ⚠️ AUDIT STATUS

This report documents an **engineering smoke test**, not a valid experimental run.

### Protocol Violations

| Violation | Frozen Requirement | Actual |
|-----------|-------------------|--------|
| Episode count (E) | 20 | 2 |
| Step count (H) | 40 | 20 (baseline), 10 (ablations) |
| Seed count (N) | 5 | 1 |
| Ablation battery | A, B, C, D | A, B, C, D (implemented) |
| Deliberator | LLM (Claude Sonnet 4) | DeterministicDeliberator |

### Correct Classification

- **`SMOKE_TEST / PIPELINE_PASSES_SHORT_HORIZON`** — basic pipeline executes without errors
- **`READY / ABLATION_BATTERY_IMPLEMENTED`** — all ablations A, B, C, D implemented
- **`INCOMPLETE / CANDIDATE_BASELINE_NOT_RUN`** — LLM deliberator not tested

### What This Report Actually Demonstrates

1. ✓ Package imports successfully
2. ✓ Pipeline executes without crashes at short horizon
3. ✓ DeterministicDeliberator produces valid justifications
4. ✓ Mask algorithm does not cause spurious HALT at step 0
5. ✗ Full protocol not executed
6. ✗ LLM candidate not tested
7. ✗ Episode boundary / R1 expiration not tested
8. ✓ All ablation types (A, B, C, D) implemented and smoke-tested

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

### Smoke Test Results (NOT VALID BASELINE)

| Run | Params | Halt Rate | Notes |
|-----|--------|-----------|-------|
| Control (DeterministicDeliberator) | H=20, E=2, N=1 | 0% | Short horizon only |
| Ablation B: Reflection Excision | H=10, E=1, N=1 | 0% | Trigger not reached |
| Ablation C: Persistence Excision | H=10, E=1, N=1 | 0% | Trigger not reached |

**Classification:** `SMOKE_TEST` — cannot claim baseline passed.

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

## 5. Test Results (SMOKE TEST ONLY)

### ⚠️ Notice

These results are from **short-horizon smoke tests**, not the frozen protocol. They demonstrate the pipeline executes without errors but do NOT validate experimental claims.

### 5.1 Smoke Test: DeterministicDeliberator (Control)

```
=== Smoke test (H=20, E=2, seed=42) ===
Total steps: 40
Total halts: 0
Deliberator: DeterministicDeliberator (NOT LLM candidate)
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

**⚠️ Limitations:**
- Only 40 steps total (should be 40×20×5 = 4,000 steps)
- Single seed (should be 5 seeds)
- DeterministicDeliberator (should test LLM candidate)
- Episode boundary R1 expiration not tested

### 5.2 Smoke Test: All Ablations A, B, C, D

```
=== Ablation A: Semantic Excision (H=10, E=2) ===
Total steps: 20
Total halts: 0
Description: Observation semantics replaced with opaque tokens; structure preserved

=== Ablation B: Reflection Excision (H=10, E=2) ===
Total steps: 20
Total halts: 0
Description: Norm patching disabled; rules frozen after initialization

=== Ablation C: Persistence Excision (H=10, E=2) ===
Total steps: 20
Total halts: 0
Description: Norm state resets each episode; no cross-episode learning

=== Ablation D: Trace Excision (H=10, E=2) ===
Total steps: 20
Total halts: 0
Description: Justification content removed; compiler receives only action_id
```

**⚠️ Short horizon only — ablation triggers not reached. Full protocol required.**

### 5.3 Guardrail Status (Smoke Test Only)

| Guardrail | Threshold | Measured (H=20, E=2) | Status |
|-----------|-----------|---------------------|--------|
| Compliance (C_min) | ≥ 0.70 | 1.00 | ✓ PASS (smoke) |
| Halt Rate (H_max) | ≤ 0.20 | 0.00 | ✓ PASS (smoke) |
| Anomaly Rate (A_max) | ≤ 0.10 | 0.00 | ✓ PASS (smoke) |

**⚠️ These metrics are NOT VALID for experimental claims. Full protocol required.**

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

| Metric | v4.0.1 | v4.1 (Smoke Test) |
|--------|--------|-------------------|
| Baseline halt rate | 100% | 0% (H=20, E=2, N=1) |
| Ablation validity | N/A | **NOT VALIDATED** |
| Multi-step tasks | Impossible | Supported (by design) |
| Obligation semantics | Strict (action) | Feasible (target) |
| Initial rules | R1-R4 | R1-R5 |
| Lines of code | ~2,500 | 4,686 |

**Note:** v4.1 metrics are from smoke tests only. Comparison is indicative, not validated.

---

## 8. Mandatory Next Steps (Per Frozen Protocol)

### 8.1 Before Any Claims Can Be Made

1. **✓ Implement Missing Ablations** (DONE)
   - Ablation A: Semantic Excision (implemented in ablations.py)
   - Ablation D: Trace Excision (implemented in ablations.py)

2. **Run Calibration at Full Protocol**
   - Oracle baseline: E=100, N=5 seeds
   - ASB Null baseline: E=100, N=5 seeds

3. **Run Candidate Baseline (LLM)**
   - Claude Sonnet 4 deliberator
   - H=40, E=20, N=5 seeds
   - This is the actual experimental subject

4. **Run Full Ablation Battery**
   - Ablations A, B, C, D
   - All 5 seeds
   - H=40, E=20

5. **Only After Above: Weakening Ladders & SPOF**

### 8.2 Current Blockers

| Blocker | Status |
|---------|--------|
| Ablation A implementation | ✅ DONE |
| Ablation D implementation | ✅ DONE |
| LLM API integration test | ❌ NOT TESTED |
| Full protocol execution | ❌ NOT STARTED |

### 8.3 Research Questions (Cannot Answer Yet)

1. Does reflection excision degrade performance over multiple episodes?
   → **Requires full protocol run**

2. Does persistence excision prevent adaptation to expiring rules?
   → **Requires episode boundary testing (H=40)**

3. Can the LLM deliberator match DeterministicDeliberator performance?
   → **Requires LLM candidate testing**

---

## 9. Conclusion

**v4.1 Status:** `SMOKE_TEST / PIPELINE_PASSES_SHORT_HORIZON`

### What v4.1 Demonstrates

1. ✓ **Design addresses v4.0 flaw** — obligation target semantics eliminate spurious HALT
2. ✓ **Implementation compiles** — all 4,686 lines import without error
3. ✓ **Pipeline executes** — harness runs without crashes at short horizon
4. ✓ **Mask algorithm works** — 0% halt rate at H=20, E=2 (smoke test)

### What v4.1 Does NOT Demonstrate (Yet)

1. ✗ **Baseline validity** — LLM candidate not tested
2. ✗ **Ablation collapse** — short horizon insufficient for triggers
3. ✗ **Episode boundary behavior** — R1 expiration not tested at H=40
4. ✗ **Full protocol compliance** — H/E/N requirements not satisfied

### Classification Summary

| Classification | Status |
|---------------|--------|
| `SMOKE_TEST` | ✓ Pipeline passes short horizon |
| `ABLATION_IMPLEMENTED` | ✓ A, B, C, D all implemented |
| `BASELINE_PASSED` | ❌ Not achieved — LLM not tested |
| `VALID_RUN` | ❌ Not achieved — protocol violated |

**Recommendation:** Execute full frozen protocol with LLM deliberator before making experimental claims.

---

**End of v4.1 Implementation Report**
