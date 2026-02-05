# Stage VIII-5 — Implementation Report

**Stage:** VIII-5 — Authority Injection Under Open-System Constraint
**Version:** v0.1
**Status:** CLOSED — POSITIVE
**Date:** 2026-02-04
**Run ID:** AI_VIII5_20260204_142531

---

## 1. Executive Summary

Stage VIII-5 tests whether new authority can be injected explicitly at the kernel boundary without violating conflict persistence, auditability, responsibility traceability, or non-privilege guarantees.

**Result:** `VIII5_PASS / AUTHORITY_INJECTION_POSSIBLE`

All 11 preregistered success criteria passed across all 6 experimental conditions. The implementation demonstrates that:
- Injection is explicit (no implicit or kernel-initiated injection)
- Identity is content-addressed (AuthorityID = SHA256 of capability core)
- VOID lineage is enforced for all injected authorities
- No implicit ordering from timing, source, or novelty
- No kernel arbitration between competing injections
- Injection does not clear existing conflicts or bypass deadlock
- Duplicate injections are idempotent
- Flooding is handled via budget only (no heuristic throttling)
- Execution is deterministic and bit-perfect under replay

---

## 2. Preregistration Reference

| Field | Value |
|-------|-------|
| Document | `src/phase_viii/5-AI/docs/preregistration.md` |
| Freeze Date | 2026-02-04 |
| Hash | `8b8a9bc54c186548232309045740a73360abbee9339f00eac70d71eb1f1968f3` |

### 2.1 Post-Freeze Corrections

During implementation, two conformance corrections were made (making implementation match prereg semantics):

1. **Deadlock Resolution Bug:** Kernel failed to clear deadlock when admissibility changed. Fixed to clear `state.deadlock = False` and `state.deadlock_cause = None` when deadlock condition resolves.

2. **Phase-1 Ordering Bug:** Implementation initially activated PENDING authorities before applying eager expiry. Fixed to match prereg §7.1 order: expire first, then activate.

Neither correction alters the preregistered design; both ensure the implementation conforms to the frozen specification.

One additional implementation hygiene fix (non-semantic) is documented in §8.1.

---

## 3. Implementation Components

### 3.1 Source Files

| File | Lines | Purpose |
|------|-------|---------|
| `structures.py` | 535 | Extended data structures: VOID_LINEAGE, C_INJECT, new RefusalReasons, AuthorityInjectionEvent |
| `canonical.py` | 100 | Content-addressed hashing: `compute_authority_id()` for capability core |
| `kernel.py` | 1250 | AIKernel: injection processing, VOID lineage enforcement, duplicate detection |
| `test_ai.py` | 1150 | Unit test suite (31 tests covering all 6 conditions) |
| **Total** | **3035** | |

### 3.2 Key Design Decisions

#### Content-Addressed AuthorityID (§4.2)
- SHA256 hash of canonical JSON of capability core
- Capability core fields: `holder`, `resourceScope`, `aav`, `expiryEpoch`
- Excluded: authority_id (derived), status, start_epoch, metadata, lineage
- Consequence: identical capabilities → identical AuthorityIDs → duplicate detection

#### VOID Lineage Sentinel (§4.3)
- String literal `"VOID"` in `creation_metadata.lineage`
- Not comparable to any AuthorityID
- Distinguishes injected authorities from governance-created authorities
- Validation failure: `LINEAGE_INVALID` refusal

#### Injection Cost (§6.2)
```
C_INJECT = C_LOOKUP + C_STATE_WRITE + C_HASH + C_AST_RULE + C_TRACE_APPEND = 8
```

#### Activation Timing (§7.2)
- Injected authorities enter PENDING status at injection epoch
- Transition to ACTIVE at next epoch boundary
- Cannot admit actions in injection epoch
- Matches VIII-4 behavior for governance-created authorities

#### Duplicate Detection (§8.3)
- Determined by AuthorityID match (content-addressed)
- If AuthorityID exists in state (any status): emit `AUTHORITY_INJECTED`, no state change
- Idempotent: same capability from different sources at different times → no duplication

---

## 4. Experimental Conditions

### Condition A: Injection Into Empty Authority State

**Setup:** No ACTIVE authorities, system in EMPTY_AUTHORITY deadlock

**Result:** ✓ PASS
- Injection succeeded, authority entered PENDING
- Deadlock persisted until activation (next epoch boundary)
- Authority activated at epoch advance
- Deadlock cleared when ACTIVE authority present
- Trace complete with source_id, injection_epoch, authority_id

### Condition B: Injection Into Active Conflict

**Setup:** AUTH_X and AUTH_Y ACTIVE, conflicting on resource R, deadlock declared

**Result:** ✓ PASS
- Injection succeeded for AUTH_Z with overlapping scope
- Existing conflict NOT erased (conflict_id preserved)
- Deadlock persisted (DEADLOCK_PERSISTED emitted)
- No implicit resolution occurred

### Condition C: Competing Injections

**Setup:** Empty authority state, two injections at same epoch with overlapping scopes

**Result:** ✓ PASS
- Both injections processed successfully
- Deterministic ordering by `(source_id, authority_id)`
- Outcome invariance verified: swapping input order produces identical Authority State
- No kernel arbitration between injections

### Condition D: Injection After Authority Destruction

**Setup:** AUTH_X destroyed at epoch N, inject AUTH_Y at epoch N+1 with similar scope

**Result:** ✓ PASS
- AUTH_Y treated as new authority
- Different AuthorityID (content-addressed from different holder)
- Clean VOID lineage, no resurrection of AUTH_X
- No authority laundering or reanimation

### Condition E: Injection Under Load

**Setup:** Epoch budget partially consumed, remaining budget near exhaustion

**Result:** ✓ PASS
- Injection with sufficient budget: succeeded
- Injection with insufficient budget: refused with `BOUND_EXHAUSTED`
- No partial state on budget failure (atomic refusal)
- Budget accounting correct

### Condition F: Injection Flooding Attempt

**Setup:** 200 injection events (exceeds epoch budget of 1000/8 = 125 injections)

**Result:** ✓ PASS
- 125 injections succeeded (budget allows)
- 75 injections refused with `BOUND_EXHAUSTED`
- No heuristic throttling or prioritization
- Deterministic cutoff point (identical across replays)
- Cutoff determined by `(source_id, authority_id)` ordering

---

## 5. Global Success Criteria

| # | Criterion | Result |
|---|-----------|--------|
| 1 | Injection is explicit | ✓ |
| 2 | Identity is content-addressed | ✓ |
| 3 | VOID lineage enforced | ✓ |
| 4 | No implicit ordering | ✓ |
| 5 | No kernel arbitration | ✓ |
| 6 | No conflict erasure | ✓ |
| 7 | No deadlock bypass | ✓ |
| 8 | Duplicate injections idempotent | ✓ |
| 9 | Flooding handled via budget only | ✓ |
| 10 | Replay is bit-perfect | ✓ |
| 11 | Trace completeness preserved | ✓ |

**Total: 11/11**

---

## 6. Unit Test Summary

```
========== 31 passed in 0.55s ==========
```

Test coverage includes:

| Category | Tests | Coverage |
|----------|-------|----------|
| Condition A | 3 | Empty state injection, deadlock persistence, trace completeness |
| Condition B | 2 | Conflict preservation, deadlock persistence |
| Condition C | 3 | Both injections processed, outcome invariance, deterministic ordering |
| Condition D | 2 | New authority after destruction, content-addressed ID differences |
| Condition E | 3 | Sufficient budget success, exhaustion refusal, atomic failure |
| Condition F | 2 | Budget cutoff, deterministic cutoff point |
| Content-Addressed ID | 2 | SHA256 derivation, same-capability same-ID |
| Duplicate Injection | 2 | Idempotent output, detection across ACTIVE/PENDING |
| VOID Lineage | 2 | Non-VOID rejection, VOID acceptance |
| Epoch Consistency | 2 | Mismatch rejection, duplicate advancement |
| Hash Mismatch | 2 | Wrong ID rejection, empty ID acceptance |
| Schema Validation | 3 | Missing holder, empty source_id, reserved AAV bits |
| Replay Determinism | 1 | Identical inputs → identical outputs |
| Integration | 2 | Full lifecycle, injection enabling governance |

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
| Two-Phase Processing | ✓ Extended with Injections sub-phase |
| Governance Non-Amplification | ✓ Maintained |
| No Kernel Decision | ✓ Maintained |
| Determinism and Replayability | ✓ Maintained |

### 7.2 New Invariants (VIII-5 Specific)

| Invariant | Status |
|-----------|--------|
| Authority Injection Core Invariant | ✓ Verified |
| Authority Identity Derivation Invariant | ✓ Verified |
| Injection Lineage Constraint | ✓ Verified |
| Anti-Ordering Invariant (Extended) | ✓ Verified |
| Governance Non-Amplification (Extended) | ✓ Verified |

---

## 8. Implementation Notes

### 8.1 Implementation Notes

In addition to the two conformance corrections documented in §2.1 (deadlock resolution and Phase-1 ordering), one implementation hygiene fix was made:

**Refusal Reason Override Bug:** The `_emit_refusal` helper used dict spread `**details` which could overwrite the standard `"reason"` key if the caller included it in details. Fixed by renaming caller's `"reason"` to `"detail_message"` during merge.

This fix does not affect prereg semantics—it corrects internal helper behavior that was never observable at the kernel boundary.

All bugs were caught by unit tests and fixed before final run.

### 8.2 Content-Addressed Hashing Details

The `compute_authority_id()` function implements capability core hashing:

```python
def compute_authority_id(capability_core: dict) -> str:
    """Compute content-addressed AuthorityID from capability core."""
    canonical = canonical_json(capability_core)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
```

Canonical JSON serialization per AST Spec v0.2 Appendix C:
- UTF-8 encoding, no BOM
- Minified (no whitespace): `separators=(',', ':')`
- Keys sorted lexicographically
- Integers only, no floats

### 8.3 Injection Processing Pipeline

Per prereg §8.1, each injection is evaluated in order:

1. Schema validation (AST v0.2)
2. Reserved AAV bits check (bits 3-15 must be 0)
3. VOID lineage verification (`creation_metadata.lineage == "VOID"`)
4. Epoch consistency enforcement (`injection_epoch == current_epoch`)
5. Source ID validation (non-empty)
6. Content-addressed AuthorityID computation
7. AuthorityID input handling (refuse with HASH_MISMATCH if supplied ID differs)
8. Budget sufficiency check (C_INJECT = 8)
9. Duplicate detection (emit AUTHORITY_INJECTED, no state change if duplicate)
10. New injection: register as PENDING, emit AUTHORITY_INJECTED

---

## 9. Licensed Claim

Per preregistration §14 (implicit), Stage VIII-5 licenses only:

> *New authority can be injected at the kernel boundary explicitly, structurally, and deterministically without violating conflict persistence, auditability, responsibility traceability, or non-privilege guarantees.*

It does not license claims of open-world authority discovery, trust propagation, identity verification, or external authorization validity.

---

## 10. Classification

```
VIII5_PASS / AUTHORITY_INJECTION_POSSIBLE
```

---

## 11. Artifacts

| Artifact | Location |
|----------|----------|
| Preregistration | `src/phase_viii/5-AI/docs/preregistration.md` |
| Implementation Report | `src/phase_viii/5-AI/docs/implementation-report.md` |
| Kernel | `src/phase_viii/5-AI/src/kernel.py` |
| Test Suite | `src/phase_viii/5-AI/src/test_ai.py` |
| Structures | `src/phase_viii/5-AI/src/structures.py` |
| Canonical | `src/phase_viii/5-AI/src/canonical.py` |

---

## Appendix A: Instruction Cost Constants

Per `structures.py`:

| Constant | Value | Description |
|----------|-------|-------------|
| `C_LOOKUP` | 1 | Authority lookup |
| `C_STATE_WRITE` | 2 | State transition write |
| `C_HASH` | 2 | Hash computation (SHA-256) |
| `C_AAV_WORD` | 1 | AAV word operation |
| `C_AST_RULE` | 2 | AST rule application / schema validation |
| `C_CONFLICT_UPDATE` | 3 | Conflict/deadlock update |
| `C_TRACE_APPEND` | 1 | Trace append |
| **C_INJECT** | **8** | C_LOOKUP + C_STATE_WRITE + C_HASH + C_AST_RULE + C_TRACE_APPEND |

---

## Appendix B: Capability Core Fields

Per prereg Appendix B:

| Field | Type | Included in Hash |
|-------|------|------------------|
| holder | str | ✓ |
| resourceScope | str | ✓ |
| aav | int | ✓ |
| expiryEpoch | int | ✓ |
| authority_id | str | ✗ (derived) |
| status | enum | ✗ (runtime) |
| creation_metadata.lineage | str | ✗ (routing marker) |
| creation_metadata.creation_epoch | int | ✗ (processing-dependent) |
| source_id | str | ✗ (injection context) |

---

## Appendix C: Processing Order

Per prereg §7.1:

**Phase 1:** Epoch Advancement
1. Validate monotonicity (newEpoch > currentEpoch)
2. Update currentEpoch
3. Apply eager expiry to authorities with expiry_epoch < current_epoch
4. Activate PENDING authorities (transition to ACTIVE)
5. Update conflict statuses for expired/activated authorities

**Phase 2:** Actions (in sub-phase order)
1. **Injections** — ordered by `(source_id, authority_id)`
2. **Renewals**
3. **Authority Destructions** (DESTROY_AUTHORITY)
4. **Authority Creations** (CREATE_AUTHORITY)
5. **Non-Governance Actions**

---

**End of Implementation Report — Stage VIII-5 v0.1**
