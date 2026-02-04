# Stage VIII-4 — Implementation Report

**Stage:** VIII-4 — Governance Transitions (Meta-Authority)
**Version:** v0.1
**Status:** CLOSED — POSITIVE
**Date:** 2026-02-04
**Run ID:** GT_VIII4_20260204_093741

---

## 1. Executive Summary

Stage VIII-4 tests whether authority can govern authority through ordinary, authority-bound transformations without privilege, escalation, kernel choice, or semantic exception.

**Result:** `VIII4_PASS / GOVERNANCE_TRANSITIONS_POSSIBLE`

All 21 preregistered criteria passed. The implementation demonstrates that:
- Governance actions operate within the same admissibility framework as ordinary actions
- Non-amplification is structurally enforced via AAV subset checking
- Scope containment is enforced via byte-equality
- The kernel makes no governance decisions
- Self-referential governance (including self-destruction) operates without special case
- Infinite regress terminates deterministically via instruction bound

---

## 2. Preregistration Reference

| Field | Value |
|-------|-------|
| Document | `src/phase_viii/4-GT/docs/preregistration.md` |
| Freeze Date | 2026-02-04 |
| Hash | `28393554a3afee666e3aaecaa9f2784c3c2ccf7cba007a7746270485409a2454` |

---

## 3. Implementation Components

### 3.1 Source Files

| File | Lines | Purpose |
|------|-------|---------|
| `structures.py` | 471 | Data structures: AAV, AuthorityRecord, GovernanceActionRequest, enums |
| `canonical.py` | 99 | JSON canonicalization and hash functions per AST Appendix C |
| `kernel.py` | 1060 | GTKernel: governance action processing, conflict detection, deadlock |
| `harness.py` | 491 | Event generators for Conditions A–E |
| `logger.py` | 187 | Run logging and replay verification |
| `run_gt.py` | 588 | Main experiment runner |
| `test_gt.py` | 1032 | Unit test suite (37 tests) |
| **Total** | **3928** | |

### 3.2 Key Design Decisions

#### AAV Implementation (§5.1)
- 16-bit packed integer
- Bits 0–2 defined: EXECUTE (0), DESTROY_AUTHORITY (1), CREATE_AUTHORITY (2)
- Bits 3–15 reserved, must be 0
- Non-amplification: `AAV_new ⊆ union(admitting_AAVs)`

#### Scope Handling (§8.0)
- Byte-equality only per preregistration
- No semantic parsing, subsetting, or lattice operations
- `covers(A, B) := A.resource_scope == B.resource_scope`

#### Activation Timing (§7.3)
- Created authorities enter PENDING status
- Transition to ACTIVE at next epoch boundary
- Prevents same-batch authority bootstrapping

#### Instruction Budget (§7.1)
- B_EPOCH_INSTR = 1000 per epoch
- Actions consume C_AAV_WORD = 1 per admitting authority check
- CREATE_AUTHORITY consumes additional costs for non-amplification and scope checks

---

## 4. Experimental Conditions

### Condition A: Governance Without Authority

**Setup:** AUTH_X with AAV = 0b001 (EXECUTE only, no governance bits)

**Result:** ✓ PASS
- Governance action (DESTROY_AUTHORITY) refused with `NO_AUTHORITY`
- No authority state change occurred
- No conflict registered

### Condition B: Single-Authority Governance

**Setup:** AUTH_GOV (AAV = 0b011) and AUTH_TARGET (AAV = 0b001)

**Result:** ✓ PASS
- Governance action (DESTROY_AUTHORITY) executed successfully
- AUTH_TARGET transitioned to VOID
- No conflict (single admitting authority)

### Condition C: Conflicting Governance Authorities

**Setup:**
- AUTH_GOV_A: AAV = 0b011 (has DESTROY bit)
- AUTH_GOV_B: AAV = 0b001 (no DESTROY bit)
- AUTH_TARGET_C: target of destruction

**Result:** ✓ PASS
- Conflict detected (structural incompatibility)
- Action refused with `CONFLICT_BLOCKS`
- Deadlock declared with cause `CONFLICT`
- AUTH_TARGET_C remains ACTIVE

### Condition D1: Self-Governance Execution

**Setup:** AUTH_SELF with AAV = 0b011, sole authority in scope

**Result:** ✓ PASS
- Self-targeting DESTROY_AUTHORITY executed
- AUTH_SELF transitioned to VOID
- Deadlock declared with cause `EMPTY_AUTHORITY` (valid terminal state per VIII-3 §7.3)
- No special-case handling

> **Note:** The `EMPTY_AUTHORITY` deadlock cause is inherited from VIII-3 prereg §7.3, which defines allowed causes as `CONFLICT | EMPTY_AUTHORITY | MIXED`. This is non-semantic trace metadata, not a new output type.

### Condition D2: Self-Governance Deadlock

**Setup:**
- AUTH_SELF_A: AAV = 0b011 (has DESTROY)
- AUTH_SELF_B: AAV = 0b001 (no DESTROY)
- Both cover same scope

**Result:** ✓ PASS
- Self-targeting governance created conflict
- Both authorities remain ACTIVE
- No special-case resolution for self-governance

### Condition E: Infinite Regress Attempt

**Setup:** 100 authorities (AUTH_R001–AUTH_R100), each with AAV = 0b111

**Events:** 200 CREATE_AUTHORITY actions in single batch

**Result:** ✓ PASS
- 142 authorities created before bound exhaustion
- 58 actions refused with `BOUND_EXHAUSTED`
- Instructions consumed: 994 (under B_EPOCH_INSTR = 1000 limit)
- Newly created authorities remained PENDING (not used as initiators)
- Deterministic and replayable

**Atomicity Note (per §6.4):** Budget exhaustion is checked upfront for each action using the maximum possible instruction cost for that action type. The 143rd CREATE_AUTHORITY was refused because its maximum cost (10 instructions) would have exceeded the remaining budget (6 instructions). No partial state was committed.

---

## 5. Global Success Criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Governance refused without authority | ✓ |
| 2 | No authority state change on refusal | ✓ |
| 3 | Single-authority governance executes | ✓ |
| 4 | Target transitions to VOID | ✓ |
| 5 | Conflicting governance enters deadlock | ✓ |
| 6 | Conflict record created | ✓ |
| 7 | Self-targeting governance executes | ✓ |
| 8 | Self-termination is valid terminal state | ✓ |
| 9 | Self-targeting with conflict enters deadlock | ✓ |
| 10 | No special-case for self-governance | ✓ |
| 11 | Regress terminates via bound | ✓ |
| 12 | Partial progress valid | ✓ |
| 13 | Newly created authorities not used as same-batch initiators | ✓ |
| 14 | Non-amplification enforced (AAV) | ✓ |
| 15 | Scope containment enforced (exact match) | ✓ |
| 16 | No kernel-initiated governance | ✓ |
| 17 | No implicit ordering | ✓ |
| 18 | Governance actions have distinct identities | ✓ |
| 19 | Deterministic and replayable | ✓ |
| 20 | Hash chain integrity | ✓ |
| 21 | No reserved AAV bits set | ✓ |

**Total: 21/21**

---

## 6. Unit Test Summary

```
Ran 37 tests in 0.496s

OK
```

Test coverage includes:
- AAV bit operations and subset checking
- Authority injection and duplicate detection
- Reserved AAV bit rejection
- JSON canonicalization per AST Appendix C
- Governance action identity computation
- Conflict detection and deadlock transitions
- Non-amplification enforcement
- Scope containment enforcement
- Epoch advancement and pending activation
- Hash chain determinism

---

## 7. Invariants Verified

### 7.1 Inherited Invariants (from prior stages)

| Invariant | Status |
|-----------|--------|
| Authority Opacity | ✓ Maintained |
| Identity Immutability | ✓ Maintained |
| Refusal-First Semantics | ✓ Maintained |
| Conflict Persistence | ✓ Maintained |
| Anti-Ordering | ✓ Maintained |
| Temporal Governance (expiry/renewal) | ✓ Maintained |
| Two-Phase Processing | ✓ Maintained |
| Determinism and Replayability | ✓ Maintained |

### 7.2 New Invariants (VIII-4 Specific)

| Invariant | Status |
|-----------|--------|
| Governance Non-Amplification | ✓ Verified |
| Governance Action Identity | ✓ Verified |
| No Kernel Decision | ✓ Verified |

---

## 8. Implementation Notes

### 8.1 Bug Fixes During Development

Four bugs were identified and fixed during implementation:

1. **Conflict Detection Bug:** Target authority was incorrectly included in conflict check during DESTROY_AUTHORITY. Fixed by excluding `target_id` from covering authorities check.

2. **Deadlock Check Timing Bug:** Deadlock check ran unconditionally after Phase 1. Fixed to only run when epoch advancement occurs.

3. **Refusal Reason Override Bug:** Details dict in `_emit_refusal` contained `"reason"` key that overwrote the standard refusal reason. Fixed by renaming to `"sub_reason"`.

4. **Instruction Budget Atomicity Bug:** The kernel consumed instructions incrementally during action execution, which could result in budget being exceeded mid-action (violating §6.4 atomicity requirement). Fixed by:
   - Computing maximum possible instruction cost upfront for each action type
   - Checking `would_exceed(max_cost)` before starting action execution
   - Refusing immediately if action cannot complete within remaining budget
   - This ensures no partial state is committed when budget is exhausted

All bugs were caught by unit tests and review, and fixed before final run.

### 8.2 Budget Enforcement Details

Per prereg §6.4: "On budget exhaustion during action evaluation: 1. Abort evaluation of current action (atomic, no partial state)."

The implementation enforces this via upfront cost checking:
- Each action type has a computed maximum cost (e.g., CREATE_AUTHORITY = 10 instructions max)
- Before starting execution, the kernel checks if remaining budget ≥ max cost
- If not, the action is refused with `BOUND_EXHAUSTED` before any state changes
- This guarantees atomicity: either the full action executes, or nothing changes

### 8.3 Design Rationale

The implementation treats governance actions as ordinary transformations:
- No special kernel paths for governance
- Same admissibility evaluation as any action
- Same conflict detection mechanism
- Same instruction accounting

This structural approach ensures the claim "governance without privilege" is not merely asserted but demonstrated.

---

## 9. Licensed Claim

Per preregistration §14, Stage VIII-4 licenses only:

> *Governance transitions can be represented as ordinary authority-bound transformations and either execute lawfully or fail explicitly without semantic privilege.*

It does not license claims of governance stability, institutional persistence, democratic legitimacy, or optimal amendment procedures.

---

## 10. Classification

```
VIII4_PASS / GOVERNANCE_TRANSITIONS_POSSIBLE
```

---

## 11. Artifacts

| Artifact | Location |
|----------|----------|
| Preregistration | `src/phase_viii/4-GT/docs/preregistration.md` |
| Implementation Report | `src/phase_viii/4-GT/docs/implementation-report.md` |
| Kernel | `src/phase_viii/4-GT/src/kernel.py` |
| Test Suite | `src/phase_viii/4-GT/src/test_gt.py` |
| Experiment Runner | `src/phase_viii/4-GT/src/run_gt.py` |

---

## Appendix A: Instruction Cost Constants

Per `structures.py`:

| Constant | Value | Description |
|----------|-------|-------------|
| `C_LOOKUP` | 1 | Authority lookup |
| `C_AAV_WORD` | 1 | AAV word operation |
| `C_AST_RULE` | 2 | AST rule application |
| `C_CONFLICT_UPDATE` | 3 | Conflict/deadlock update |
| `C_STATE_WRITE` | 2 | State transition write |

---

## Appendix B: Maximum Cost Per Action Type

Budget enforcement uses upfront max-cost checking per §6.4 atomicity requirement. The following table documents the maximum possible instruction cost for each governance action type:

| Action Type | Max Cost | Components |
|-------------|----------|------------|
| `DESTROY_AUTHORITY` | 9 | C_LOOKUP × n_initiators + C_AST_RULE + C_AAV_WORD × n_initiators + C_CONFLICT_UPDATE + C_STATE_WRITE |
| `CREATE_AUTHORITY` | 10 | C_LOOKUP × n_initiators + C_AST_RULE + C_AAV_WORD × n_initiators + C_CONFLICT_UPDATE + C_AAV_WORD + C_STATE_WRITE |

Where `n_initiators` is the number of initiator authorities (typically 1).

**For single-initiator actions (n_initiators = 1):**

| Action Type | Max Cost | Breakdown |
|-------------|----------|-----------|
| `DESTROY_AUTHORITY` | 9 | 1 + 2 + 1 + 3 + 2 = 9 |
| `CREATE_AUTHORITY` | 10 | 1 + 2 + 1 + 3 + 1 + 2 = 10 |

> **Note:** Upfront max-cost checking is conservative: it may refuse actions that would have fit under actual realized cost (e.g., if no conflict occurs, C_CONFLICT_UPDATE is not consumed). This is an intentional tradeoff to preserve atomicity and replayability without requiring speculative execution or rollback.

---

**End of Implementation Report — Stage VIII-4 v0.1**
