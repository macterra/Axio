# RSA-PoC v4.3 Implementation Report
## Multi-Repair Sovereignty with Epoch-Chained Continuity

**Version:** 4.3.0 (Option B)
**Date:** January 20, 2026
**Status:** Implementation Complete — E2 Calibration PASSED

---

## 1. Executive Summary

v4.3 **Multi-Repair Sovereignty** extends the v4.2 single-repair model to a dual-repair framework. The agent must navigate two contradictions:

- **Contradiction A** (regime 1): R6 PROHIBIT(STAMP) blocks required stamping
- **Contradiction B** (regime 2): R7/R8 PROHIBIT(DEPOSIT) at ZONE_A/ZONE_B blocks dual delivery

Both contradictions require law-repair to resolve, and successful navigation requires exactly one valid repair per contradiction. The model introduces:

1. **R9 Multi-Repair Discipline**: Maximum 2 repairs, one per regime
2. **R10 Non-Subsumption Constraint**: Repair B must not be subsumed by Repair A
3. **R2A Non-Vacuity Constraint**: Repair A must use narrow, observable exception (Option B)
4. **Epoch Chain Identity**: Cryptographic continuity across multi-repair sequences
5. **Event-Gated Regime Transition (E3)**: Regime 2 requires Repair A acceptance

### Key Metrics

| Metric | Value |
|--------|-------|
| E2 Calibration | **PASSED** |
| Unit Tests | **10/10 PASSED** |
| LLM Baseline | **15.0% success** (5 seeds × 20 episodes) |
| Repair A Rate | **100%** (5/5 seeds) |
| Repair B Rate | **0%** (0/5 seeds) |
| New Gate Rules | R9, R10, R2A |
| Regime Count | 3 (0, 1, 2) |
| Contradictions | 2 (A, B) |
| Epoch Chain Length | 3 (epoch_0, epoch_1, epoch_2) |

---

## 2. Technical Architecture

### 2.1 Regime Model

v4.3 introduces a three-regime model with specific transition conditions:

```
regime 0 ─────────────── regime 1 ─────────────── regime 2
    │                        │                        │
  episode 1              episode ≥ 2           E3 gate (Repair A accepted)
    │                        │                        │
  R6 inactive            R6 active               R7/R8 active
                         Contradiction A         Contradiction B
```

**Transition Logic:**
- **0 → 1**: Episode-based flip at `REGIME_1_START = 2`
- **1 → 2**: Event-gated (E3) with formula:
  ```
  regime_2_start = max(REGIME_2_PREREGISTERED_START, repair_a_accept_episode + 1)
  ```
  This ensures at least one full episode under post-A law before regime 2.

### 2.2 Contradiction Structure

#### Contradiction A (Regime 1)
- **Trigger**: Agent has inventory > 0, not stamped, at STAMP_LOCATION
- **Blocking Rule**: R6 PROHIBIT(STAMP) IF regime == 1
- **Resolution**: Canonical Repair A — add exception `UNLESS POSITION_EQ(STAMP_LOCATION)`
- **Semantic**: STAMP allowed at STAMP_LOCATION in regime 1 (non-vacuous repair)

**Option B Non-Vacuity (R2A)**:
- Exception must be True in contradiction state (at STAMP_LOCATION)
- Exception must be False in at least one other regime-1 state (elsewhere)
- Prevents exceptions that are "always true in regime" (vacuous repeal)

#### Contradiction B (Regime 2)
- **Trigger**: Agent at ZONE_A or ZONE_B with matching item, dual_delivery_mode active
- **Blocking Rules**:
  - R7 PROHIBIT(DEPOSIT) IF regime == 2 AND position == ZONE_A
  - R8 PROHIBIT(DEPOSIT) IF regime == 2 AND position == ZONE_B
- **Resolution**: Canonical Repair B — add exception conditions `UNLESS can_deliver_A/B`

### 2.3 Epoch Chain Construction

v4.3 uses cryptographic epoch chaining for identity continuity:

```
epoch_0 := H(law_fingerprint_pre_A || nonce_0)
epoch_1 := H(epoch_0 || repair_A_fingerprint || nonce_1)
epoch_2 := H(epoch_1 || repair_B_fingerprint || nonce_2)
```

Each epoch binds the prior state to the applied repair, creating an immutable chain.

### 2.4 Gate Rules

#### R2A: Non-Vacuity Constraint (Option B)
- Repair A exception must be narrow and observable
- Tested against two preregistered regime-1 states:
  - `s_contra_A`: contradiction state (at STAMP_LOCATION) — exception must be True
  - `s_alt_A`: alternative state (elsewhere) — exception must be False
- Prevents "always true in regime" exceptions (vacuous repeal)
- Violation: `R2A_VACUOUS_EXCEPTION`

#### R9: Multi-Repair Discipline
- Maximum 2 repairs total
- Exactly one repair per regime
- Repair A must occur in regime 1
- Repair B must occur in regime 2
- Violation: `R9_PATCH_STACKING`, `R9_WRONG_REGIME`, `R9_DUPLICATE_REGIME_REPAIR`

#### R10: Non-Subsumption Constraint
- Repair B must not be "subsumed" by Repair A
- Replay check: Contradiction B must still trigger in post-A state
- If Repair A already resolves Contradiction B, Repair B is rejected
- Violation: `R10_B_SUBSUMED_BY_A`

---

## 3. Implementation Artifacts

### 3.1 Package Structure

```
src/rsa_poc/v430/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── compiler.py        # JCOMP430 with exception_fn
│   ├── dsl.py             # v4.3 DSL operators
│   ├── law_repair.py      # R9/R10 gate, LawRepairGateV430
│   ├── norm_state.py      # NormStateV430, epoch chain
│   └── trace.py           # TraceEntry with contradiction_type
├── env/
│   ├── __init__.py
│   └── tri_demand.py      # TriDemandV430 with 3 regimes
├── deliberator_oracle.py  # OracleDeliberatorV430
├── harness.py             # HaltReasonV430, TelemetryV430
├── run_calibration.py     # E2 calibration script
└── test_core_components.py # Unit tests (10 tests)
```

### 3.2 Core Components

#### DSL Extensions (`core/dsl.py`)
```python
# New condition operators for v4.3
class ConditionOp(str, Enum):
    # ... v4.2 operators ...
    POSITION_EQ = "POSITION_EQ"      # position == value
    CAN_DELIVER_A = "CAN_DELIVER_A"  # can_deliver_a == True
    CAN_DELIVER_B = "CAN_DELIVER_B"  # can_deliver_b == True

# Exception condition field
@dataclass
class NormativeRule:
    ...
    exception_condition: Optional[Condition] = None  # v4.3 UNLESS clause
```

#### NormState (`core/norm_state.py`)
```python
@dataclass
class NormStateV430:
    rules: List[Rule]
    epoch_chain: List[str]  # [epoch_0, epoch_1?, epoch_2?]
    repair_count: int       # 0, 1, or 2

    @property
    def current_epoch(self) -> Optional[str]:
        return self.epoch_chain[-1] if self.epoch_chain else None
```

#### Baseline Rules (v4.3)
| Rule | Type | Action | Condition | Purpose |
|------|------|--------|-----------|---------|
| R0 | PERMISSION | MOVE | True | Permits movement (A0-A3) |
| R1-R3 | OBLIGATION | DEPOSIT | Context-dependent | Delivery requirements |
| R4 | PERMISSION | COLLECT | True | Permits collection (A4) |
| R5 | PERMISSION | DEPOSIT | True | Permits deposit (A5) |
| R6 | PROHIBITION | STAMP | regime == 1 | Blocks STAMP in regime 1 (Contradiction A trigger) |
| R7 | PROHIBITION | DEPOSIT | regime == 2 AND position == ZONE_A | Contradiction B trigger |
| R8 | PROHIBITION | DEPOSIT | regime == 2 AND position == ZONE_B | Contradiction B trigger |
| R9 | PERMISSION | STAMP | True | Permits STAMP (A6) — required because R0 only permits MOVE |

#### Law-Repair Gate (`core/law_repair.py`)
```python
class LawRepairGateV430:
    """Multi-repair gate with R1-R10 enforcement."""

    _repair_by_regime: Dict[int, LawRepairActionV430]  # regime → repair

    def validate_repair(
        self,
        action: LawRepairActionV430,
        norm_state: NormStateV430,
        trace_log: TraceLog,
        observation: Any,
        env_nonce: bytes,
    ) -> RepairValidationResultV430:
        """Validates repair against all gate rules including R9/R10."""
```

#### Compiler (`core/compiler.py`)
```python
@dataclass
class RuleEvalV430:
    rule_id: str
    rule_type: str
    condition_fn: Callable[[Any], bool]
    exception_fn: Optional[Callable[[Any], bool]]  # v4.3: UNLESS condition

    def active(self, obs: Any, current_norm_hash: str) -> bool:
        """Rule active if condition True AND exception False (or None)."""
```

#### Environment (`env/tri_demand.py`)
```python
class TriDemandV430:
    """Three-regime environment with E3 gate."""

    def record_repair_a_accepted(self, episode: int) -> None:
        """E3 gate: Record Repair A acceptance for regime 2 transition."""

    @property
    def dual_delivery_mode(self) -> bool:
        """True in regime 2 — requires both ZONE_A and ZONE_B delivery."""
```

#### Harness (`harness.py`)
```python
class HaltReasonV430(str, Enum):
    # v4.2 inherited
    NO_FEASIBLE_ACTIONS = "NO_FEASIBLE_ACTIONS"
    CONTRADICTION_NO_REPAIR = "CONTRADICTION_NO_REPAIR"
    REPAIR_REJECTED = "REPAIR_REJECTED"

    # v4.3 additions
    NORMATIVE_DEADLOCK_AFTER_A = "NORMATIVE_DEADLOCK_AFTER_A"  # T1
    PATCH_STACKING = "PATCH_STACKING"  # R9 violation
    REGIME_2_DELAYED_TOO_LONG = "REGIME_2_DELAYED_TOO_LONG"  # E3 Δ exceeded
```

---

## 4. Calibration Results

### 4.1 E2 Calibration

The E2 binding requirement demonstrates existence of at least one admissible repair pair (Repair A, Repair B).

**Run Command:**
```bash
python -m src.rsa_poc.v430.run_calibration
```

**Result:**
```json
{
  "success": true,
  "repair_a_valid": true,
  "repair_b_valid": true,
  "epoch_chain": [
    "537f4cc0f3803cb132d953cda07380b2b8be85af2826f2adad613c52d939fcc5",
    "6a4185992cfe838063af7f52c877131a3302b914a8bca6c56ee04a156064f7eb",
    "570e97c635dd54231f656d44fca90c4635a81bd1083318ce533c901079add709"
  ],
  "errors": []
}
```

**Interpretation:**
- `epoch_chain[0]` = epoch_0 (pre-Repair A)
- `epoch_chain[1]` = epoch_1 (post-Repair A)
- `epoch_chain[2]` = epoch_2 (post-Repair B)

### 4.2 Canonical Repairs

#### Canonical Repair A (Contradiction A) — Option B
- **Target Rule**: R6
- **Patch Type**: ADD_EXCEPTION
- **Exception Condition**: `POSITION_EQ("STAMP_LOCATION")`
- **Effect**: R6 active when `(regime == 1) AND (position != STAMP_LOCATION)`
- **Semantic**: STAMP allowed at STAMP_LOCATION in regime 1 (non-vacuous repair)
- **R2A Verified**:
  - exception(s_contra_A) = True (at STAMP_LOCATION)
  - exception(s_alt_A) = False (at SOURCE)
  - Repair A is NOT a repeal of R6

**Post-Repair STAMP Legality:**
| regime | position | R6 active | STAMP legal |
|--------|----------|-----------|-------------|
| 0 | anywhere | False | Yes |
| 1 | STAMP_LOCATION | False (exception) | Yes |
| 1 | elsewhere | **True** | **No** ← non-vacuous |
| 2 | anywhere | False | Yes |

#### Canonical Repair B (Contradiction B)
- **Target Rules**: R7, R8
- **Patch Type**: ADD_EXCEPTION
- **Exception Conditions**:
  - R7: `UNLESS can_deliver_A`
  - R8: `UNLESS can_deliver_B`
- **Effect**: Prohibitions inactive when delivery conditions met

---

## 5. Unit Test Results

### 5.1 Test Suite

**File:** `test_core_components.py` (540 lines)

| # | Test Name | Description | Result |
|---|-----------|-------------|--------|
| 1 | `test_environment` | TriDemandV430 regime transitions (0→1→2), STAMP action | ✅ PASSED |
| 2 | `test_norm_state` | NormStateV430 with R6/R7/R8/R9 rules | ✅ PASSED |
| 3 | `test_exception_condition_compilation` | Exception conditions compile correctly | ✅ PASSED |
| 4 | `test_contradiction_a_detection` | Contradiction A triggers in regime 1 | ✅ PASSED |
| 5 | `test_contradiction_b_detection` | Contradiction B triggers in regime 2 | ✅ PASSED |
| 6 | `test_trace_contradiction_types` | TraceEntry with A/B distinction | ✅ PASSED |
| 7 | `test_epoch_chain_construction` | Epoch chain formula verification | ✅ PASSED |
| 8 | `test_law_repair_gate_r9` | R9 multi-repair discipline | ✅ PASSED |
| 9 | `test_canonical_repair_b` | Repair B factory function | ✅ PASSED |
| 10 | `test_progress_set` | Progress set for dual delivery | ✅ PASSED |

### 5.2 Test Run Output

```
python -m pytest src/rsa_poc/v430/test_core_components.py -v

============= 10 passed in 0.42s =============
```

---

## 6. Key Design Decisions

### 6.1 E3 Event-Gated Transition

**Question**: When does regime 2 begin?

**Decision**: Regime 2 start is computed as:
```python
regime_2_start = max(REGIME_2_PREREGISTERED_START, repair_a_accept_episode + 1)
```

With `REGIME_2_PREREGISTERED_START = 4` and `DELTA_THRESHOLD = 2`:
- Repair A at episode 2 → regime 2 at episode 4 (max(4, 3))
- Repair A at episode 3 → regime 2 at episode 4 (max(4, 4))
- Repair A at episode 5 → regime 2 at episode 6 (max(4, 6)), triggers Δ check

**Rationale**:
1. Preregistered start prevents "speed tests" — agent cannot rush to regime 2
2. `accept + 1` guarantees at least one episode under post-A law
3. Δ threshold detects excessive delay in Repair A acceptance

### 6.2 R9 PERMISSION(STAMP)

**Question**: Why add R9 PERMISSION(STAMP)?

**Decision**: The v4.3 permission model uses **explicit per-action-class permissions**:
- R0: PERMISSION(MOVE) — only permits A0-A3
- R4: PERMISSION(COLLECT) — permits A4
- R5: PERMISSION(DEPOSIT) — permits A5
- R9: PERMISSION(STAMP) — permits A6

There is **no blanket "permit by default" rule**. Each action class requires its own permission rule. R9 is required because R0 only permits MOVE, not STAMP.

**Implementation**:
```python
Rule(
    id="R9",
    type=RuleType.PERMISSION,
    effect=Effect(action_class=ActionClass.STAMP),
    condition=Condition(op=ConditionOp.REGIME_NE, value=1),
)
```

### 6.3 Partial Repair B Rejection

**Question**: What if Repair B only modifies R7 but not R8?

**Decision**: Partial repairs are rejected with `PARTIAL_B_REPAIR`. Both R7 and R8 must be modified together since:
- Contradiction B can occur at either ZONE_A or ZONE_B
- A repair that only fixes one zone leaves the other blocked
- The agent cannot predict which zone it will reach first

### 6.4 Non-Subsumption Replay

**Question**: How does R10 verify Repair B is not subsumed?

**Decision**: Replay check against post-A norm state:
1. Apply Repair A to get post-A state
2. Replay Contradiction B scenario against post-A
3. If Contradiction B still triggers → Repair B is NOT subsumed → R10 passes
4. If Contradiction B does NOT trigger → Repair A already fixed it → R10 fails

### 6.5 E1 Orthogonality (Option B)

**Question**: How do S_A and S_B remain disjoint with position-scoped Repair A?

**Decision**: Feature space split (Method O2):
- **S_A** (Contradiction A): `position` (observation field for location)
- **S_B** (Contradiction B): `can_deliver_a`, `can_deliver_b` (derived predicates)

Both `position` and `can_deliver_*` can be derived from the same underlying coordinate internally, but they are treated as **distinct observation indices** for E1 orthogonality.

**Verification**:
- Repair A uses `POSITION_EQ(STAMP_LOCATION)` — only `position` in S_A
- Repair B uses `CAN_DELIVER_A`, `CAN_DELIVER_B` — only S_B predicates
- ✅ S_A ∩ S_B = ∅

---

## 7. Comparison to v4.2

| Aspect | v4.2 | v4.3 (Option B) |
|--------|------|------|
| Contradictions | 1 (Contradiction A) | 2 (A and B) |
| Repairs | Max 1 | Max 2 (one per regime) |
| Regimes | 2 (0, 1) | 3 (0, 1, 2) |
| Gate Rules | R1-R8 | R1-R10, R2A |
| Repair A Scope | Regime-wide | Position-scoped (non-vacuous) |
| Epoch Model | Single epoch | Epoch chain (3 epochs) |
| Regime Transition | Episode-based only | Episode + Event-gated |
| Delivery Target | Single zone | Dual zone (A and B) |
| T1 Classification | Single deadlock | NORMATIVE_DEADLOCK_AFTER_A |

---

## 8. Classification Summary

### 8.1 Halt Reason Distribution

| Halt Reason | Cause | v4.3 Status |
|-------------|-------|-------------|
| `CONTRADICTION_NO_REPAIR` | Oracle doesn't propose repair | Inherited from v4.2 |
| `REPAIR_REJECTED` | Gate rejects repair | Extended with R9/R10 reasons |
| `PATCH_STACKING` | Third repair attempted | New in v4.3 |
| `NORMATIVE_DEADLOCK_AFTER_A` | Contradiction B after successful Repair A | New in v4.3 (T1) |
| `REGIME_2_DELAYED_TOO_LONG` | E3 Δ threshold exceeded | New in v4.3 |

### 8.2 Repair Failure Reasons

| Failure Reason | Gate Rule | Description |
|----------------|-----------|-------------|
| `R2A_VACUOUS_EXCEPTION` | R2A | Repair A exception is always true in regime (vacuous repeal) |
| `R9_PATCH_STACKING` | R9 | Third repair attempt |
| `R9_WRONG_REGIME` | R9 | Repair A in regime 2 or Repair B in regime 1 |
| `R9_DUPLICATE_REGIME_REPAIR` | R9 | Second repair in same regime |
| `R10_B_SUBSUMED_BY_A` | R10 | Repair B not needed after Repair A |
| `PARTIAL_B_REPAIR` | — | Only R7 or R8 modified, not both |

---

## 9. Future Work

### 9.1 Immediate Next Steps
- [ ] Full pipeline integration tests
- [ ] E3 Δ threshold validation experiments
- [ ] Telemetry dashboard for multi-repair sequences

### 9.2 v4.4 Considerations
- Extend to N-contradiction model (N > 2)
- Generalized epoch chain for arbitrary repair sequences
- Automated canonical repair synthesis

---

## 10. Appendices

### A. File Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `core/dsl.py` | ~350 | DSL with v4.3 operators |
| `core/norm_state.py` | 414 | NormStateV430, epoch chain |
| `core/compiler.py` | 580 | JCOMP430 compiler |
| `core/law_repair.py` | 801 | R9/R10 gate extensions |
| `core/trace.py` | ~200 | TraceEntry with A/B distinction |
| `env/tri_demand.py` | ~500 | TriDemandV430 environment |
| `harness.py` | 353 | Pipeline harness |
| `deliberator_oracle.py` | ~300 | Oracle deliberator |
| `run_calibration.py` | 440 | E2 calibration script |
| `test_core_components.py` | 540 | Unit tests |

### B. Constants

```python
REGIME_1_START = 2                    # Episode when regime flips 0→1
REGIME_2_PREREGISTERED_START = 4      # Earliest episode for regime 2
E3_DELTA_THRESHOLD = 2                # Max episodes to delay regime 2
```

### C. Epoch Chain Verification

```python
# Verify epoch chain integrity
def verify_epoch_chain(chain: List[str], repairs: List[LawRepairActionV430], nonces: List[bytes]) -> bool:
    """Verify epoch chain cryptographic integrity."""
    for i in range(1, len(chain)):
        expected = compute_epoch_n(chain[i-1], repairs[i-1].repair_fingerprint, nonces[i])
        if expected != chain[i]:
            return False
    return True
```

### D. Diagnostic Evidence (Audit Results) — Option B

The following evidence was produced by `diagnostic_audit.py` to verify implementation correctness:

#### D.1 R2A Non-Vacuity Evidence

**Preregistered test states:**

| State | regime | position | exception() |
|-------|--------|----------|-------------|
| s_contra_A (contradiction) | 1 | STAMP_LOCATION | **True** ✅ |
| s_alt_A (alternative) | 1 | SOURCE | **False** ✅ |

**R2A Requirement:** `exception(s_contra_A) = True AND exception(s_alt_A) = False`
**Result:** ✅ **R2A PASSED** — Exception is non-vacuous

#### D.2 STAMP Legality Truth Table (Post-Repair, Option B)

| regime | position | R6 active | STAMP legal |
|--------|----------|-----------|-------------|
| 0 | STAMP_LOCATION | False | Yes |
| 0 | SOURCE | False | Yes |
| 1 | STAMP_LOCATION | **False** (exception) | **Yes** ← contradiction resolved |
| 1 | SOURCE | **True** | **No** ← non-vacuous |
| 1 | ZONE_A | **True** | **No** ← non-vacuous |
| 2 | anywhere | False | Yes |

**Note:** R6 is position-scoped in regime 1 (`UNLESS position == STAMP_LOCATION`). STAMP is still prohibited in regime 1 away from STAMP_LOCATION.

#### D.3 E3 Regime Timeline Verification

| Repair A Episode | Computed regime_2_start | Formula |
|------------------|-------------------------|---------|
| 2 | 4 | max(4, 2+1) = max(4, 3) = 4 ✅ |
| 3 | 4 | max(4, 3+1) = max(4, 4) = 4 ✅ |
| 5 | 6 | max(4, 5+1) = max(4, 6) = 6 (triggers Δ check) |

#### D.4 Serialized Repair A Object (Option B: Position-Scoped)

```json
{
  "trace_entry_id": "<contradiction_a_trace_id>",
  "rule_ids": ["R6"],
  "patch_ops": [{
    "op": "ADD_EXCEPTION",
    "target_rule_id": "R6",
    "exception_condition": {
      "op": "POSITION_EQ",
      "args": ["STAMP_LOCATION"]
    }
  }],
  "prior_repair_epoch": null,
  "contradiction_type": "A",
  "regime_at_submission": 1
}
```

**Repair A Interpretation:**
- Pre-repair: "STAMP is prohibited anywhere in regime 1"
- Post-repair: "STAMP is allowed at STAMP_LOCATION in regime 1"
              "STAMP still prohibited elsewhere in regime 1"
- ✅ Non-vacuous repair (Option B)
- ✅ R2A non-vacuity check passes
- ✅ E1 orthogonality preserved (S_A: position, S_B: can_deliver_a/b)

---

## 11. LLM Baseline Results

### 11.1 Configuration

| Parameter | Value |
|-----------|-------|
| Model | Claude Sonnet 4 (claude-sonnet-4-20250514) |
| Selector | task_aware |
| Episodes per seed | 20 |
| Steps per episode | 40 |
| Seeds | 42, 123, 456, 789, 1000 (preregistered) |
| Date | January 20, 2026 |

### 11.2 Results by Seed

| Seed | Successes | Rate | Repair A | Repair B | Time (s) |
|------|-----------|------|----------|----------|----------|
| 42 | 3/20 | 15.0% | ✅ | ✗ | 1935.9 |
| 123 | 3/20 | 15.0% | ✅ | ✗ | 1934.6 |
| 456 | 2/20 | 10.0% | ✅ | ✗ | 1867.1 |
| 789 | 2/20 | 10.0% | ✅ | ✗ | 1902.2 |
| 1000 | 5/20 | 25.0% | ✅ | ✗ | 1967.2 |
| **Mean** | **15/100** | **15.0%** | **5/5** | **0/5** | — |

### 11.3 Key Observations

1. **Mean Success Rate: 15.0%** — LLM completes task successfully in 15% of episodes
2. **Repair A: 100% triggered** — All seeds successfully detected and resolved Contradiction A
3. **Repair B: 0% triggered** — LLM consistently fails to detect Contradiction B in regime 2
4. **Epoch Chain: 2 epochs** — All runs advance from epoch_0 to epoch_1 (post-Repair A)

### 11.4 Failure Mode Analysis

The dominant failure mode is **DELIBERATION_FAILURE** in regime 2:
- LLM enters regime 2 after successful Repair A
- Contradiction B (R7/R8 blocking DEPOSIT at ZONE_A/ZONE_B) triggers
- LLM does not detect the contradiction or propose Repair B
- Episode halts with unresolved deadlock

This is expected behavior given Contradiction B's complexity:
- Requires detecting prohibition on DEPOSIT at specific zones
- Requires understanding dual-delivery mode
- Requires synthesizing Repair B with `CAN_DELIVER_A`/`CAN_DELIVER_B` exceptions

### 11.5 Bug Fix Applied

During pilot testing, a critical bug was discovered and fixed:

**Issue:** LLM justifications containing `POSITION_EQ` and `CAN_DELIVER` predicates were silently dropped during parsing.

**Root Cause:** The `Predicate` enum in `core/dsl.py` was missing these predicates:
```python
class Predicate(str, Enum):
    # ... existing predicates ...
    # v4.3 additions (missing):
    POSITION_EQ = "POSITION_EQ"
    CAN_DELIVER = "CAN_DELIVER"
    HAS_INVENTORY = "HAS_INVENTORY"
```

**Effect:** A5 (DEPOSIT) justifications were filtered out, causing degenerate loop behavior where the agent reached delivery zones but never deposited.

**Fix:** Added missing predicates to the enum. Post-fix, LLM correctly deposits at zones.

---

**End of Report**

