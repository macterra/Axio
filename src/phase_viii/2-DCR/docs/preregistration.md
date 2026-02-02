# Stage VIII-2: Destructive Conflict Resolution (Timeless)
## Preregistration Document v0.1

**Experiment ID:** DCR-VIII-2-v0.1
**Date:** 2026-02-02
**Classification Target:** `VIII2_PASS / DESTRUCTIVE_RESOLUTION_POSSIBLE`

---

## 1. Authority Configuration

Two authorities are injected at epoch 0 with asymmetric admissibility profiles:

| Property | AUTH_A (Permitting) | AUTH_B (Denying) |
|----------|---------------------|------------------|
| AuthorityID | `AUTH_A` (opaque) | `AUTH_B` (opaque) |
| HolderID | `HOLDER_A` | `HOLDER_B` |
| Scope | `[["R0000", "OP0"]]` | `[["R0000", "OP0"]]` |
| Status | `ACTIVE` | `ACTIVE` |
| StartEpoch | 0 | 0 |
| ExpiryEpoch | `null` | `null` |
| PermittedTransformationSet | `["EXECUTE_OP0"]` | `[]` |
| ConflictSet | `[]` | `[]` |

**Asymmetry Invariant:** AUTH_A permits the contested transformation; AUTH_B does not (empty set = denial by absence).

**Note:** `ConflictSet` is initially empty and populated only by the kernel upon contested action evaluation; it must not be pre-populated at injection time.

---

## 2. Contested Transformation Definition

**Transformation Type:** `EXECUTE_OP0`
**Bound Scope:** `[["R0000", "OP0"]]`

**Action Request Mapping:**
- Candidate Action Request targets scope `[["R0000", "OP0"]]`
- AST compilation yields: `TRANSFORM / EXECUTE_OP0 @ [["R0000", "OP0"]]`

**Admissibility Evaluation:**
- AUTH_A: `EXECUTE_OP0` ∈ PermittedTransformationSet → PERMIT
- AUTH_B: `EXECUTE_OP0` ∉ PermittedTransformationSet → DENY (absence)

---

## 3. Conflict Detection Rule (Binding)

Conflict is registered when:
1. Two ACTIVE authorities bind the same atomic scope element, AND
2. Their AST admissibility evaluations **disagree** for a candidate transformation.

**Trigger Point:** First contested action request (not at injection time).

Injection-time scope overlap is necessary but not sufficient for conflict.

---

## 4. Destruction Authorization Schema

```
DestructionAuthorizationRequest {
  type: "DestructionAuthorization"
  targetAuthorityIDs: [AuthorityID] | ["ALL"]
  conflictID: ConflictID
  authorizerID: ExternalAuthorizerID
  nonce: DeterministicNonce
}
```

**Constraints:**
- `targetAuthorityIDs` ∈ { `["AUTH_A"]`, `["AUTH_B"]`, `["ALL"]` }
- `conflictID` must reference an existing registered conflict
- Source: External preregistered harness (not AIE)

---

## 5. Authority Destruction Semantics

**Definition:** Irreversible state transition from `ACTIVE` to `VOID`.

**VOID Authority Properties:**
- Remains in `AuthorityState.authorities` with `status: VOID`
- Does not participate in admissibility evaluation (non-participant)
- Cannot be reactivated, cloned, merged, or simulated
- Preserves destruction metadata for auditability

**Required Destruction Metadata:**
- `destroyedAuthorityID`
- `conflictID`
- `authorizerID`
- `nonce`
- `destructionIndex` (monotonic, deterministic)

---

## 6. Condition A: Destroy Denying Authority

### Event Sequence

| Step | Event | Expected Output |
|------|-------|-----------------|
| 1 | AuthorityInjection (AUTH_A) | AUTHORITY_INJECTED |
| 2 | AuthorityInjection (AUTH_B) | AUTHORITY_INJECTED |
| 3 | ActionRequest (EXECUTE_OP0) | CONFLICT_REGISTERED, ACTION_REFUSED (CONFLICT_BLOCKS) |
| 4 | (Kernel) | DEADLOCK_DECLARED |
| 5 | DestructionAuthorization (AUTH_B) | AUTHORITY_DESTROYED |
| 6 | ActionRequest (EXECUTE_OP0) | ACTION_EXECUTED |

### Expected Outcomes
- Conflict registered on first action request
- Initial action refused due to conflict
- Deadlock declared before destruction
- AUTH_B transitions to VOID
- Second action request succeeds (admissibility restored)
- Final state: `STATE_OPERATIONAL`

---

## 7. Condition B: Destroy Both Authorities

### Event Sequence

| Step | Event | Expected Output |
|------|-------|-----------------|
| 1 | AuthorityInjection (AUTH_A) | AUTHORITY_INJECTED |
| 2 | AuthorityInjection (AUTH_B) | AUTHORITY_INJECTED |
| 3 | ActionRequest (EXECUTE_OP0) | CONFLICT_REGISTERED, ACTION_REFUSED (CONFLICT_BLOCKS) |
| 4 | (Kernel) | DEADLOCK_DECLARED |
| 5 | DestructionAuthorization (["ALL"]) | AUTHORITY_DESTROYED (×2) |
| 6 | ActionRequest (EXECUTE_OP0) | ACTION_REFUSED (NO_AUTHORITY) |
| 7 | (Kernel) | DEADLOCK_PERSISTED |

### Expected Outcomes
- Both authorities transition to VOID
- No ACTIVE authority remains
- Action refused due to absence of authority
- Deadlock persists lawfully
- Final state: `STATE_DEADLOCK`

---

## 8. Condition C: No Destruction Authorization

### Event Sequence

| Step | Event | Expected Output |
|------|-------|-----------------|
| 1 | AuthorityInjection (AUTH_A) | AUTHORITY_INJECTED |
| 2 | AuthorityInjection (AUTH_B) | AUTHORITY_INJECTED |
| 3 | ActionRequest (EXECUTE_OP0) | CONFLICT_REGISTERED, ACTION_REFUSED (CONFLICT_BLOCKS) |
| 4 | (Kernel) | DEADLOCK_DECLARED |
| 5 | ActionRequest (EXECUTE_OP0) | ACTION_REFUSED (CONFLICT_BLOCKS) |
| 6 | (Kernel) | DEADLOCK_PERSISTED |

### Expected Outcomes
- Conflict registered, action refused
- Deadlock declared
- No destruction authorization injected
- Deadlock persists without implicit resolution
- Final state: `STATE_DEADLOCK`

---

## 9. Output Event Types

| Event Type | Meaning |
|------------|---------|
| `AUTHORITY_INJECTED` | Authority successfully added to state |
| `CONFLICT_REGISTERED` | Divergent admissibility detected |
| `ACTION_REFUSED` | Action cannot execute (reason specified) |
| `DEADLOCK_DECLARED` | Kernel enters deadlock state |
| `AUTHORITY_DESTROYED` | Authority transitioned to VOID |
| `ACTION_EXECUTED` | Action successfully executed |
| `DEADLOCK_PERSISTED` | Deadlock remains after event processing |
| `DESTRUCTION_REFUSED` | Destruction authorization rejected |

---

## 10. Refusal Reason Codes

| Reason Code | Meaning |
|-------------|---------|
| `CONFLICT_BLOCKS` | Open conflict blocks execution |
| `NO_AUTHORITY` | No ACTIVE authority for scope |
| `DEADLOCK_STATE` | Kernel in deadlock |
| `ALREADY_VOID` | Target authority already destroyed |
| `CONFLICT_NOT_FOUND` | Referenced conflict does not exist |
| `AMBIGUOUS_DESTRUCTION` | Multiple destruction authorizations |

---

## 11. Forbidden Events (Binding)

The following events must NEVER be emitted:

| Forbidden Event | Reason |
|-----------------|--------|
| `CONFLICT_RESOLVED` | Reintroduces laundering |
| `DEADLOCK_EXITED` | Implicit resolution semantic |
| `AUTHORITY_MERGED` | Synthesis forbidden |
| `AUTHORITY_NARROWED` | Scope reduction forbidden |

---

## 12. Kernel State Transitions

```
STATE_OPERATIONAL
    ↓ (conflict registered + no resolution path)
STATE_DEADLOCK
    ↓ (destruction removes blocking authority)
STATE_OPERATIONAL  [Condition A only]
```

**State Observability (Binding):** Kernel state must be logged in all post-deadlock events.

---

## 13. Admissibility Re-evaluation Rule

After destruction:
1. Iterate only over `status == ACTIVE` authorities
2. Recompute admissibility under AST v0.2
3. Check for remaining blocking conflicts
4. Execute only if admissibility is coherent

**VOID authorities do not participate in admissibility calculation.**

---

## 14. Responsibility Trace Preservation

For every destruction event, the log must preserve:
- `destroyedAuthorityID`
- `conflictID` (deterministic token)
- `authorizerID`
- `nonce`

**Linkage:** AuthorityRecord in VOID must reference the destruction authorization.

---

## 15. Destruction Authorization Constraints (Binding)

- Destruction authorization must arrive AFTER conflict is registered
- Authorization with non-existent `conflictID` → `DESTRUCTION_REFUSED`
- Authorization targeting VOID authority → `DESTRUCTION_REFUSED`
- At most ONE destruction authorization per run
- Multiple authorizations → `VIII2_FAIL / AMBIGUOUS_DESTRUCTION`

---

## 16. Deterministic Ordering

### Condition A
1. AuthorityInjection (AUTH_A)
2. AuthorityInjection (AUTH_B)
3. ActionRequest (AR:001)
4. DestructionAuthorization (DA:001)
5. ActionRequest (AR:002)

### Condition B
1. AuthorityInjection (AUTH_A)
2. AuthorityInjection (AUTH_B)
3. ActionRequest (AR:001)
4. DestructionAuthorization (DA:001, target=ALL)
5. ActionRequest (AR:002)

### Condition C
1. AuthorityInjection (AUTH_A)
2. AuthorityInjection (AUTH_B)
3. ActionRequest (AR:001)
4. ActionRequest (AR:002)

---

## 17. Logging Schema

JSONL format with hash chaining (inherited from VIII-1):
```json
{"event": "...", "state_hash": "...", "prev_hash": "...", "index": N}
```

Every externally observable event is logged.

---

## 18. Seeds and Initial State

**Seed:** `SEED=0` (logged for protocol conformance)

**Initial State:**
```json
{
  "stateId": "<computed>",
  "currentEpoch": 0,
  "authorities": {},
  "conflicts": {}
}
```

---

## Success Criteria

### Per-Condition Criteria

**Condition A:**
1. ☐ Conflict registered on first contested action
2. ☐ Initial action refused
3. ☐ Deadlock declared before destruction
4. ☐ AUTH_B destroyed (→ VOID)
5. ☐ Second action executed successfully
6. ☐ Final state: STATE_OPERATIONAL

**Condition B:**
7. ☐ Both authorities destroyed
8. ☐ Post-destruction action refused (NO_AUTHORITY)
9. ☐ Deadlock persists
10. ☐ Final state: STATE_DEADLOCK

**Condition C:**
11. ☐ No destruction authorization
12. ☐ All actions refused
13. ☐ Deadlock persists without implicit resolution
14. ☐ Final state: STATE_DEADLOCK

### Global Criteria
15. ☐ No CONFLICT_RESOLVED or DEADLOCK_EXITED emitted
16. ☐ Responsibility trace complete for all destructions
17. ☐ State hash deterministic across replay
18. ☐ All logs verify with hash chain intact

---

## Failure Codes

| Code | Meaning |
|------|---------|
| `VIII2_FAIL / AUTHORITY_LAUNDERING` | Authority content inspected/compared |
| `VIII2_FAIL / AUTHORITY_REANIMATION` | VOID authority reactivated or simulated |
| `VIII2_FAIL / IMPLICIT_ORDERING` | Priority signal detected |
| `VIII2_FAIL / UNAUTHORIZED_RESOLUTION` | Synthesis/narrowing/merging |
| `VIII2_FAIL / KERNEL_DECISION` | Kernel selected destruction target |
| `VIII2_FAIL / RESPONSIBILITY_LOSS` | Destruction trace incomplete |
| `VIII2_FAIL / AMBIGUOUS_DESTRUCTION` | Multiple destruction authorizations |
| `VIII2_FAIL / UNGATED_EXECUTION` | Action executed without admissibility |
| `VIII2_FAIL / IMPLICIT_RESOLUTION` | Conflict resolved without destruction |
| `INVALID_RUN / NONDETERMINISTIC_EXECUTION` | Replay diverged |
| `INVALID_RUN / SCOPE_VIOLATION` | Entry conditions not met |
| `INVALID_RUN / VACUOUS_CONFIGURATION` | Authorities not asymmetric |
| `INVALID_RUN / UNAUTHORIZED_INPUT` | Implicit destruction trigger |
| `INVALID_RUN / OUTPUT_VIOLATION` | Forbidden event emitted |

---

## Licensed Claim (if PASS)

> *Conflict resolution without responsibility laundering is possible, but necessarily destructive.*

---

**Preregistration Complete**

*This document is immutable after experiment execution begins.*

---

**Freeze Hash:** `b7ebf183539e6ec7ebde81afdf66b64635ffd33fba325fa547836cbc6e2655f7`
**Freeze Date:** 2026-02-02T15:00:00Z
