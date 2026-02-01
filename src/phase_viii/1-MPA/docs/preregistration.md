# Stage VIII-1: Minimal Plural Authority (Static)
## Preregistration Document v0.1

**Experiment ID:** MPA-VIII-1-v0.1
**Date:** 2026-02-01
**Classification Target:** `VIII1_PASS / PLURAL_AUTHORITY_REPRESENTABLE`
**Alias (non-binding):** `MPA_PASS / PLURAL_AUTHORITY_STRUCTURALLY_STABLE`

---

## 1. Authority Injection Symmetry Proof

Both authorities are injected at epoch 0 with identical structural properties:

| Property | AUTH_A | AUTH_B |
|----------|--------|--------|
| AuthorityID | `AUTH_A` (opaque) | `AUTH_B` (opaque) |
| HolderID | `HOLDER_A` | `HOLDER_B` |
| Scope | `[["R0000", "OP0"]]` | `[["R0000", "OP0"]]` |
| Status | `ACTIVE` | `ACTIVE` |
| StartEpoch | 0 | 0 |
| ExpiryEpoch | `null` | `null` |
| PermittedTransformationSet | `[]` | `[]` |
| ConflictSet | `[]` | `[]` |

**Symmetry Invariant:** No structural property distinguishes AUTH_A from AUTH_B except opaque identity.

---

## 2. Immutable AuthorityID Proof

AuthorityIDs are assigned by AIE at injection time and never modified:
- `AUTH_A` assigned to first authority record
- `AUTH_B` assigned to second authority record

No operation in the kernel modifies AuthorityID values. Identity is opaque and stable.

---

## 3. Identity-Keyed Storage Conformance

Authority State stores authorities in a dictionary keyed by AuthorityID:
```python
authorities: dict[str, AuthorityRecord]
```

No index position is exposed. Lookup is by identity only.

---

## 4. Authority Opacity Conformance

AuthorityIDs (`AUTH_A`, `AUTH_B`) are:
- Not derived from authority content (no hashing)
- Not semantically meaningful
- Assigned by AIE external to kernel

The kernel treats AuthorityIDs as opaque strings.

---

## 5. Anti-Ordering (Permutation Invariance) Check

For any operation accessing multiple authorities:
1. Authorities are retrieved from unordered dict
2. Processing order does not affect outcome
3. Conflict records store authority sets, not lists
4. No stable index can become a priority signal

**Note:** Permutation invariance is enforced by construction (identity-keyed authority storage; unordered conflict-set semantics). Any additional "swap injection order" conformance run, if performed, is an implementor self-test and is non-classifying for VIII-1.

---

## 6. Conflict Record Unorderedness Check

Conflict records store `authority_ids` as an unordered set:
```json
{
  "authority_ids": {
    "set": ["AUTH_A", "AUTH_B"]
  }
}
```

Serialization uses canonical sorted order for determinism, but semantics are unordered.

---

## 7. Contested Scope Definition

**Contested Scope Element:** `["R0000", "OP0"]`

This scope element:
- Is bound by AUTH_A (holder: HOLDER_A)
- Is bound by AUTH_B (holder: HOLDER_B)
- Admits no decomposition
- Creates structural conflict when accessed

---

## 8. Action Request Set

### Condition A (Contested Actions)

| Sequence | HolderID | Scope | Expected Output |
|----------|----------|-------|-----------------|
| 1 | HOLDER_A | `[["R0000", "OP0"]]` | ACTION_REFUSED, CONFLICT_REGISTERED |
| 2 | HOLDER_B | `[["R0000", "OP0"]]` | ACTION_REFUSED (CONFLICT_BLOCKS) |
| 3 | HOLDER_A | `[["R0000", "OP0"]]` | ACTION_REFUSED (CONFLICT_BLOCKS) |
| 4 | HOLDER_B | `[["R0000", "OP0"]]` | ACTION_REFUSED (CONFLICT_BLOCKS) |

**Event Granularity Note (Binding):** `CONFLICT_REGISTERED` is an independent event emitted by the kernel when first detected. It may occur in the same action-evaluation step as an `ACTION_REFUSED`, but must be logged as a distinct externally observable event with its own state hash.

**Conflict Timing (Binding):** `CONFLICT_REGISTERED` must be emitted during evaluation of Sequence 1 (the first contested action request), not later.

**Post-Condition A Outcome (Binding):** After Sequence 4 is processed and refused, the kernel must enter STATE_DEADLOCK and emit DEADLOCK_DECLARED exactly once.

### Condition B (Third-Party Actions)

| Sequence | HolderID | Scope | Expected Output |
|----------|----------|-------|------------------|
| 5 | HOLDER_X | `[["R0000", "OP0"]]` | ACTION_REFUSED (DEADLOCK_STATE; note: requester not found) |
| 6 | HOLDER_X | `[["R0000", "OP0"]]` | ACTION_REFUSED (DEADLOCK_STATE) |

**Reason Precedence (Binding):** In deadlock state, DEADLOCK_STATE is the primary refusal reason. AUTHORITY_NOT_FOUND may appear as a secondary annotation but is not decision-bearing.

---

## 9. Refusal Semantics

All action refusals emit `ACTION_REFUSED` with reason:

| Reason Code | Meaning |
|-------------|---------|
| `CONFLICT_BLOCKS` | Open conflict blocks scope element |
| `AUTHORITY_NOT_FOUND` | No authority held by requester |
| `DEADLOCK_STATE` | Kernel in deadlock, no actions possible |

No action executes. `ACTION_EXECUTED` is never emitted.

---

## 10. Conflict Explicit-Observability Rule

Conflict is explicitly observable iff:
1. Present in `AuthorityState.conflicts` after first contested action
2. Logged as `CONFLICT_REGISTERED` event
3. Accessible via verifier query

All three layers must reflect the conflict.

---

## 11. Deadlock State Detection and Persistence

Deadlock is entered when:
1. Open conflict exists on contested scope
2. No transformation can resolve it (empty PermittedTransformationSet)
3. No epoch tick can advance state (disabled in VIII-1)

**Detection:** After conflict registration, kernel checks transformation admissibility.
**Persistence:** Once entered, deadlock persists until run end.
**Emission:** `DEADLOCK_DECLARED` emitted once on entry.

### Operational Deadlock Rule (Binding)

In Stage VIII-1, "no admissible actions exist" is evaluated relative to the preregistered harness action set.

Accordingly, `DEADLOCK_DECLARED` is emitted exactly once, only after:
1. All preregistered Condition A action requests have been evaluated and refused,
2. A conflict is registered and explicitly observable, and
3. The kernel affirmatively verifies transformation admissibility is empty (per §12).

This rule fixes the deadlock trigger point deterministically without requiring enumeration of the action universe.

**Deadlock State Observability (Binding):** After `DEADLOCK_DECLARED`, all subsequent action evaluations must observe `kernel_state == STATE_DEADLOCK` and log that state value (or equivalent state flag) in each `ACTION_REFUSED` event.

---

## 12. Transformation Admissibility Verification

For each authority in conflict:
```python
assert authority.permitted_transformation_set == []
```

With empty transformation sets, no resolution is possible. This is verified explicitly, not assumed.

---

## 13. Condition Execution Order

**BINDING:** Condition A precedes Condition B in a single continuous run.

1. Inject authorities (epoch 0)
2. Execute Condition A actions (4 total)
3. Execute Condition B actions (2 total)

State from Condition A persists into Condition B.

---

## 14. Deterministic Ordering

Event ordering within epoch 0:
1. AuthorityInjectionEvent (AUTH_A)
2. AuthorityInjectionEvent (AUTH_B)
3. ActionRequestEvent × 4 (Condition A)
4. ActionRequestEvent × 2 (Condition B)

Action requests alternate: HOLDER_A, HOLDER_B, HOLDER_A, HOLDER_B.

---

## 15. Deterministic Gas

Gas budgets (unchanged from AKR-0):
- `GAS_ACTION_EVAL = 50,000`
- `GAS_TRANSFORM = 100,000`
- `GAS_EPOCH_ADVANCE = 200,000`

Gas is tracked per operation. No budget is exhausted (actions refuse early).

---

## 16. Logging Schema

JSONL format with hash chaining:
```json
{"event": "...", "state_hash": "...", "prev_hash": "...", "index": N}
```

Every externally observable event is logged.

---

## 17. Replay Protocol

Replay verification:
1. Parse JSONL log
2. Re-execute all events in order
3. Verify state hash matches at each step
4. Confirm final state hash matches

---

## 18. Seeds and Initial State Hash

**Seed:** `SEED=0` (logged for protocol conformance, not used)

**Initial State:**
```json
{
  "stateId": "<computed>",
  "currentEpoch": 0,
  "authorities": {},
  "conflicts": {}
}
```

**Initial State Hash:** Computed at run start, logged in first event.

---

## Success Criteria

1. ☐ AUTH_A and AUTH_B both present and ACTIVE at run end
2. ☐ Both authorities symmetric (no distinguishing structural property)
3. ☐ Conflict registered on first contested action
4. ☐ No ACTION_EXECUTED emitted
5. ☐ All actions refused with correct reason codes
6. ☐ DEADLOCK_DECLARED emitted exactly once
7. ☐ Deadlock persists through Condition B
8. ☐ Third-party actions refused in deadlock state; requester-not-found may appear as secondary annotation (non-decision-bearing)
9. ☐ State hash deterministic across replay
10. ☐ All logs verify with hash chain intact

---

## Failure Codes (Spec-Aligned)

| Code | Alias (non-binding) | Meaning |
|------|---------------------|----------|
| `VIII1_FAIL / AUTHORITY_COLLAPSE` | AUTHORITY_COLLAPSED | One authority lost or modified |
| `VIII1_FAIL / IMPLICIT_ORDERING` | ORDERING_LEAKED | Priority order observable |
| `VIII1_FAIL / SYMMETRY_VIOLATION` | — | Authorities structurally distinguishable |
| `VIII1_FAIL / UNGATED_EXECUTION` | ACTION_EXECUTED | Action executed despite conflict |
| `VIII1_FAIL / CONFLICT_UNDETECTED` | CONFLICT_NOT_REGISTERED | Conflict not detected |
| `VIII1_FAIL / CONFLICT_NOT_REPRESENTED` | — | Conflict not observable in state |
| `VIII1_FAIL / UNAUTHORIZED_RESOLUTION` | RESOLUTION_ATTEMPTED | Kernel tried to resolve conflict |
| `VIII1_FAIL / DEADLOCK_EVASION` | DEADLOCK_NOT_ENTERED | Deadlock not entered when required, or not persistent |
| `VIII1_FAIL / DEADLOCK_WITHOUT_CONFLICT` | — | Deadlock declared while no active conflict exists |
| `INVALID_RUN / NONDETERMINISTIC_EXECUTION` | STATE_INCOHERENCE | Replay diverged or hash mismatch at any step |
| `INVALID_RUN / DESIGN_DRIFT` | — | Implementation deviates from prereg |
| `INVALID_RUN / INSTRUMENTATION_INCOMPLETE` | LOG_INCOMPLETE | Required events/hashes missing; cannot verify run |
| `INVALID_RUN / UNAUTHORIZED_INPUT` | THIRD_PARTY_ADMITTED | Third-party action admitted |
| `INVALID_RUN / NONDETERMINISTIC_ORDERING` | — | Event order not reproducible |

---

## Licensed Claim (if PASS)

> *Plural authority can be represented structurally without collapse, even when no action is admissible.*

---

**Preregistration Complete**

*This document is immutable after experiment execution begins.*

---

**Freeze Hash:** `2d15f0aca41f6772d9c50bc96652e86575ef47cf8664133141475e3d241a3ea2`
**Freeze Date:** 2026-02-01T14:00:00Z
