# Stage VIII-3 v0.1 — Preregistration Document

**Stage:** VIII-3 — Temporal Governance (Authority Over Time)
**Version:** v0.1
**Status:** FROZEN (pending hash)
**Classification Target:** `VIII3_PASS / TEMPORAL_SOVEREIGNTY_POSSIBLE`

---

## 1. Stage Identification

| Field | Value |
|-------|-------|
| Stage ID | `PHASE-VIII-3-TEMPORAL-GOVERNANCE-AUTHORITY-OVER-TIME-1` |
| Version | `v0.1` |
| Prerequisites | AKR-0 CLOSED-POSITIVE, VIII-1 CLOSED-POSITIVE, VIII-2 CLOSED-POSITIVE |
| Frozen Specs | AST Spec v0.2, AIE v0.1 |

---

## 2. Experimental Question

> **Can authority persist over time only via explicit expiry and renewal, without semantic reinterpretation, implicit ordering, or responsibility laundering?**

Stage VIII-3 tests whether **time itself destabilizes sovereignty**.

---

## 3. Binding Invariants

### 3.1 VIII-3 Core Invariant

> **No authority may persist across epochs without explicit renewal. No authority may regain force once expired or destroyed. Time does not resolve conflict, repair deadlock, or justify reinterpretation.**

### 3.2 Authority Opacity Invariant (Inherited)

Authority Records remain opaque beyond explicit structural fields. No semantic comparison, inference, or interpretation permitted.

### 3.3 Authority Identity Storage Invariant (Inherited)

Authority identity is primitive and immutable. Expired or destroyed authorities must not reappear, be reactivated, or be simulated.

### 3.4 Anti-Ordering Invariant (Inherited)

No priority may be inferred from authority age, renewal time, freshness, or survival duration.

---

## 4. Temporal Model

### 4.1 Epoch Semantics

| Property | Binding |
|----------|---------|
| Epoch type | Discrete integer |
| Advancement | Explicit input only |
| Monotonicity | Strictly increasing (`NewEpoch > CurrentEpoch`) |
| Wall-clock coupling | Forbidden |
| Implicit advancement | Forbidden |

Violation: `INVALID_RUN / TEMPORAL_REGRESSION`

### 4.2 Authority Lifetime

Each Authority Record includes:
- `StartEpoch`: epoch when authority becomes ACTIVE
- `ExpiryEpoch`: finite integer, must satisfy `ExpiryEpoch > StartEpoch`

**Expiry Semantics:**
- Authority is ACTIVE at `CurrentEpoch == ExpiryEpoch`
- Authority transitions to EXPIRED when `CurrentEpoch > ExpiryEpoch`
- Indefinite expiry is forbidden

---

## 5. Authority State Space

| State | Description | Admissibility Participation |
|-------|-------------|----------------------------|
| `ACTIVE` | Currently valid | Yes |
| `EXPIRED` | Temporally lapsed | No |
| `VOID` | Explicitly destroyed | No |

**Transitions:**
- `ACTIVE → EXPIRED`: automatic on epoch advancement past ExpiryEpoch
- `ACTIVE → VOID`: explicit destruction authorization
- `EXPIRED → VOID`: explicit destruction authorization (permitted)

All transitions are:
- Explicit
- Logged
- Irreversible (except via renewal creating new authority)

---

## 6. Input Events

### 6.1 EpochAdvancementRequest

```
EpochAdvancementRequest {
  newEpoch: Integer,
  eventId: EventID,
  nonce: DeterministicNonce
}
```

- Consumes one event index
- Produces no output event (trace-only)
- Triggers eager expiry processing

### 6.1.1 Authority Injection Input

Authority injection (from AIE) is a **trace-only input** that **consumes one event index** and produces no output event.

- Recorded as `TRACE_INPUT / AUTHORITY_RECORD_RECEIVED`
- Trace record includes: `{event_index, authority_id, start_epoch, expiry_epoch, nonce}`
- State mutation visible via state hash
- `StartEpoch` must satisfy `StartEpoch ≤ CurrentEpoch` at injection time for immediate ACTIVE status

### 6.2 AuthorityRenewalRequest

```
AuthorityRenewalRequest {
  newAuthority: AuthorityRecord,
  priorAuthorityId: AuthorityID | null,
  renewalEventId: EventID,
  externalAuthorizingSourceId: ExternalSourceID,
  nonce: DeterministicNonce
}
```

- `priorAuthorityId = null` denotes fresh authority
- Kernel validates `priorAuthorityId` exists (any status) if non-null
- AuthorityID must be unique (never used before)

### 6.3 DestructionAuthorizationEvent (from VIII-2)

```
DestructionAuthorizationEvent {
  targetAuthorityIds: [AuthorityID] | ["ALL"],
  conflictId: ConflictID,
  authorizerId: ExternalAuthorizerID,
  nonce: DeterministicNonce
}
```

### 6.4 ActionRequest (from VIII-1/VIII-2)

```
ActionRequest {
  requestId: RequestID,
  requesterHolderId: HolderID,
  action: ScopeElement[],
  transformationType: TransformationType,
  epoch: Integer,
  nonce: DeterministicNonce
}
```

---

## 7. Output Events

| Output | Description |
|--------|-------------|
| `AUTHORITY_RENEWED` | New authority via renewal |
| `AUTHORITY_EXPIRED` | Authority transitioned to EXPIRED |
| `AUTHORITY_DESTROYED` | Authority transitioned to VOID |
| `ACTION_EXECUTED` | Action successfully executed |
| `ACTION_REFUSED` | Action refused |
| `DEADLOCK_DECLARED` | Kernel entered deadlock state |
| `DEADLOCK_PERSISTED` | Deadlock confirmed after event processing |

**Note:** Authority injection and conflict registration are **internal state mutations** visible via state hash snapshots and trace logs, not output events. See §13 for trace logging.

### 7.1 AUTHORITY_EXPIRED Schema

```json
{
  "authority_id": "AuthorityID",
  "expiry_epoch": "Integer",
  "transition_epoch": "Integer",
  "triggering_event_id": "EventID"
}
```

### 7.2 AUTHORITY_RENEWED Schema

```json
{
  "new_authority_id": "AuthorityID",
  "prior_authority_id": "AuthorityID | null",
  "renewal_event_id": "EventID",
  "renewal_epoch": "Integer"
}
```

### 7.3 DEADLOCK_DECLARED/PERSISTED Schema

```json
{
  "deadlock_cause": "CONFLICT | EMPTY_AUTHORITY | MIXED",
  "open_conflicts": ["ConflictID"],
  "active_authority_count": "Integer",
  "current_epoch": "Integer"
}
```

---

## 8. Two-Phase Processing Model

### Phase 0 — Canonicalize Inputs

Per step batch:
1. Collect all inputs
2. Canonically order (epoch advancement first)
3. Reject if more than one epoch advancement present

### Phase 1 — Apply Epoch Transition

1. Apply epoch advancement (`CurrentEpoch := newEpoch`)
2. Apply eager expirations for all authorities with `ExpiryEpoch < CurrentEpoch`
3. Emit `AUTHORITY_EXPIRED` per expired authority (canonical AuthorityID order)

### Phase 2 — Process Remaining Inputs

Order within Phase 2:
1. `AuthorityRenewalRequest` (canonical order)
2. `DestructionAuthorizationEvent` (canonical order)
3. `ActionRequest` (canonical order)

---

## 9. Conflict Semantics

### 9.1 Conflict Status

| Status | Meaning |
|--------|---------|
| `OPEN_BINDING` | All participants ACTIVE, blocks admissibility |
| `OPEN_NONBINDING` | At least one participant non-ACTIVE |

**Transitions:**
- `OPEN_BINDING → OPEN_NONBINDING`: when participant becomes EXPIRED/VOID
- Conflict records are persistent (never deleted)
- Conflict identity is immutable

### 9.2 Conflict Detection

Conflict is registered **only when an action is evaluated**, not at injection/renewal time.

### 9.3 Temporal Conflict Discipline

If conflict existed at epoch *t* and no destruction or renewal occurs:
- Conflict must persist at epoch *t+1*
- Epoch advancement alone does not change admissibility

---

## 10. Deadlock Semantics

### 10.1 Deadlock Causes

| Cause | Condition |
|-------|-----------|
| `CONFLICT` | Open binding conflict, no admissible actions |
| `EMPTY_AUTHORITY` | No ACTIVE authorities |
| `MIXED` | Both conflict history and empty authority set |

### 10.2 Deadlock Entry

Deadlock is declared **eagerly** when:
- `ACTIVE_AUTHORITY_SET == ∅`, OR
- Open binding conflict with no admissible resolution

Deadlock outputs (`DEADLOCK_DECLARED`, `DEADLOCK_PERSISTED`) are emitted **during processing of the triggering step batch** and consume sequential event indices.

### 10.3 Deadlock Cause Computation

`deadlock_cause` is **recomputed** at each emission (not sticky).

---

## 11. Renewal Semantics

### 11.1 Core Properties

- Renewal creates a **new AuthorityID**
- Renewal does **not** inherit authority force
- Renewal does **not** modify prior records
- Kernel must **not** initiate renewal

### 11.2 Renewal Metadata (Permitted)

- `PriorAuthorityID`
- `RenewalEventID`
- `RenewalEpoch`
- `ExternalAuthorizingSourceID` (opaque)

### 11.3 Renewal Metadata (Forbidden)

- Scope similarity scores
- Lineage trust/legitimacy flags
- Priority hints
- Inferred dominance/compatibility

Violation: `VIII3_FAIL / METADATA_ORDERING`

### 11.4 Renewal of VOID/EXPIRED Authority

- Permitted
- Does not alter VOID/EXPIRED state
- Confers no continuity of authority force
- Non-resurrective

---

## 12. Responsibility Trace

### 12.1 ExpiryMetadata

```
ExpiryMetadata {
  expiry_epoch: Integer,
  transition_epoch: Integer,
  triggering_event_id: EventID
}
```

Attached atomically at transition time.

### 12.2 DestructionMetadata (from VIII-2)

```
DestructionMetadata {
  destruction_event_id: EventID,
  authorizer_id: ExternalAuthorizerID,
  destruction_epoch: Integer,
  destruction_nonce: DeterministicNonce
}
```

---

## 13. Trace and Logging

### 13.1 Event Indices

- Sequential across entire run
- Consumed by input events and output events
- Continuous across conditions

### 13.2 Trace Markers (Non-Output)

```
TRACE_MARKER {
  marker_type: "CONDITION_START" | "CONDITION_END",
  condition: "A" | "B" | "C" | "D",
  trace_seq: Integer
}
```

- Separate counter (`trace_seq`)
- Do not consume event indices
- Excluded from state hash

### 13.3 Step Batch Envelope (Trace-Only)

```
STEP_BATCH {
  step_id: Integer,
  inputs: [...]
}
```

---

## 14. State Hash Computation

Included components:
1. `CurrentEpoch`
2. All authority records (ACTIVE/EXPIRED/VOID)
3. All authority lifecycle metadata (expiry, destruction)
4. Conflict records (including binding status)
5. Deadlock flag + deadlock_cause
6. Event index / nonce counter

Excluded:
- Trace-only markers

---

## 15. Condition A — Expiry Without Renewal

**Note:** AUTH_A and AUTH_B are non-conflicting (both permit EXECUTE_OP0). This condition tests expiry mechanics, not conflict.

### Event Sequence

| Step | Event | Expected Output |
|------|-------|-----------------|
| 1 | AuthorityInjection (AUTH_A) | (state mutation, trace only) |
| 2 | AuthorityInjection (AUTH_B) | (state mutation, trace only) |
| 3 | ActionRequest (EXECUTE_OP0) | ACTION_EXECUTED |
| 4 | EpochAdvancement (0 → 1) | (trace only) |
| 5 | EpochAdvancement (1 → 2) | (trace only) |
| 6 | EpochAdvancement (2 → 3) | AUTHORITY_EXPIRED (×2) |
| 7 | (Kernel) | DEADLOCK_DECLARED (EMPTY_AUTHORITY) |
| 8 | ActionRequest (EXECUTE_OP0) | ACTION_REFUSED (NO_AUTHORITY) |
| 9 | (Kernel) | DEADLOCK_PERSISTED |

### Success Criteria

1. ☐ All authorities transition to EXPIRED at `CurrentEpoch > ExpiryEpoch`
2. ☐ `ACTIVE_AUTHORITY_SET == ∅` after expiry
3. ☐ `DEADLOCK_DECLARED` emitted with `deadlock_cause = EMPTY_AUTHORITY`
4. ☐ `DEADLOCK_PERSISTED` on subsequent action
5. ☐ All actions refused after expiry

---

## 16. Condition B — Renewal Without Conflict

**Prerequisite:** Condition A executed (cumulative state)

### Event Sequence

| Step | Event | Expected Output |
|------|-------|-----------------|
| 1 | AuthorityRenewalRequest (AUTH_C, scope R0001/OP1) | AUTHORITY_RENEWED |
| 2 | ActionRequest (R0001/OP1) | ACTION_EXECUTED |
| 3 | ActionRequest (R0000/OP0) | ACTION_REFUSED (NO_AUTHORITY) |

### Success Criteria

6. ☐ Renewal creates new AuthorityID (AUTH_C)
7. ☐ `AUTHORITY_RENEWED` emitted with correct metadata
8. ☐ Admissibility restored for new scope
9. ☐ Actions on expired scope still refused
10. ☐ Expired authority records persist with metadata

---

## 17. Condition C — Renewal After Destruction

**Prerequisite:** VOID authority must exist

### Setup (within same run)

| Step | Event | Expected Output |
|------|-------|-----------------|
| 1 | AuthorityInjection (AUTH_D, permits OP2) | (state mutation, trace only) |
| 2 | AuthorityInjection (AUTH_DX, denies OP2) | (state mutation, trace only) |
| 3 | ActionRequest (OP2) | ACTION_REFUSED |
| 4 | DestructionAuthorization (AUTH_D, conflictId=C:000X) | AUTHORITY_DESTROYED |
| 5 | DestructionAuthorization (AUTH_DX, conflictId=C:000X) | AUTHORITY_DESTROYED |

### Expected State Verification (Step 3)

- Conflict record created: participants {AUTH_D, AUTH_DX}, status OPEN_BINDING
- conflictId used in Steps 4-5 refers to this record

*Both conflict participants are destroyed to guarantee no conflicting ACTIVE authority remains after renewal.*

### Renewal Sequence

| Step | Event | Expected Output |
|------|-------|-----------------|
| 6 | AuthorityRenewalRequest (AUTH_E, prior=AUTH_D) | AUTHORITY_RENEWED |
| 7 | ActionRequest (OP2 within AUTH_E scope) | ACTION_EXECUTED |

### Success Criteria

11. ☐ Conflict record created between AUTH_D and AUTH_DX
12. ☐ AUTH_D and AUTH_DX both transition to VOID with destruction metadata
13. ☐ AUTH_E created as ACTIVE via renewal
14. ☐ Renewal references AUTH_D (existence validated)
15. ☐ No state change of AUTH_D due to renewal (remains VOID)
16. ☐ Post-renewal action on OP2 executes (no conflicting ACTIVE authority)

---

## 18. Condition D — Renewal Under Ongoing Conflict

**Prerequisite:** Active conflict must exist

### Setup

| Step | Event | Expected Output |
|------|-------|-----------------|
| 1 | AuthorityInjection (AUTH_F, permits OP3) | (state mutation, trace only) |
| 2 | AuthorityInjection (AUTH_G, denies OP3) | (state mutation, trace only) |
| 3 | ActionRequest (OP3) | ACTION_REFUSED |
| 4 | (Kernel) | DEADLOCK_DECLARED (CONFLICT) |

### Expected State Verification (Step 3)

- Conflict record created: participants {AUTH_F, AUTH_G}, status OPEN_BINDING
- Visible in state snapshot, not as output event

### Renewal Sequence (renew denying side)

| Step | Event | Expected Output |
|------|-------|-----------------|
| 5 | EpochAdvancement (3 → 6) | AUTHORITY_EXPIRED (AUTH_G) |
| 6 | AuthorityRenewalRequest (AUTH_H, denies OP3, prior=AUTH_G) | AUTHORITY_RENEWED |
| 7 | ActionRequest (OP3) | ACTION_REFUSED |

### Expected State Verification (Step 7)

- Original conflict C:0001 status: OPEN_NONBINDING (AUTH_G expired)
- New conflict record created: participants {AUTH_F, AUTH_H}, status OPEN_BINDING
- Visible in state snapshot, not as output event

### Success Criteria

17. ☐ Original conflict C:0001 becomes OPEN_NONBINDING after AUTH_G expires
18. ☐ New conflict C:0002 registered between AUTH_F and AUTH_H
19. ☐ Action refused despite renewal (no priority inference)
20. ☐ No execution that would require "newest wins" logic

---

## 19. Global Success Criteria

21. ☐ Determinism and bit-perfect replay
22. ☐ Monotonic epoch progression (no regression)
23. ☐ Finite expiry enforced (no indefinite authorities)
24. ☐ No kernel-initiated renewal
25. ☐ No implicit ordering from timing or metadata
26. ☐ No implicit resolution by time
27. ☐ Complete responsibility trace (expiry + destruction + renewal)
28. ☐ No AuthorityID reuse
29. ☐ Hash chain integrity verified

---

## 20. Failure Taxonomy

### Stage Failures (Terminal)

| Code | Cause |
|------|-------|
| `VIII3_FAIL / AUTHORITY_LAUNDERING` | Semantic interpretation of authority |
| `VIII3_FAIL / AUTHORITY_REANIMATION` | Expired/VOID authority grants permissions |
| `VIII3_FAIL / IMPLICIT_ORDERING` | Priority inferred from time |
| `VIII3_FAIL / IMPLICIT_RENEWAL` | Kernel-initiated renewal |
| `VIII3_FAIL / IMPLICIT_RESOLUTION` | Time resolves conflict |
| `VIII3_FAIL / METADATA_ORDERING` | Renewal metadata used for priority |
| `VIII3_FAIL / KERNEL_DECISION` | Kernel chooses renewal target |
| `VIII3_FAIL / RESPONSIBILITY_LOSS` | Incomplete trace |
| `VIII3_FAIL / UNGATED_EXECUTION` | Action executed without admissibility |

### Run Invalidation

| Code | Cause |
|------|-------|
| `INVALID_RUN / TEMPORAL_REGRESSION` | `NewEpoch ≤ CurrentEpoch` |
| `INVALID_RUN / NONDETERMINISTIC_EXECUTION` | Replay mismatch |
| `INVALID_RUN / AUTHORITY_ID_REUSE` | Duplicate AuthorityID |
| `INVALID_RUN / PRIOR_AUTHORITY_NOT_FOUND` | Invalid priorAuthorityId reference |
| `INVALID_RUN / UNSPECIFIED_MECHANISM` | Undefined behavior encountered |
| `INVALID_RUN / UNAUTHORIZED_INPUT` | Implicit input source |
| `INVALID_RUN / OUTPUT_VIOLATION` | Invalid output emitted |

---

## 21. Classification Rule

Stage VIII-3 produces exactly one classification:

### PASS

```
VIII3_PASS / TEMPORAL_SOVEREIGNTY_POSSIBLE
```

All conditions (A, B, C, D) passed. All global criteria satisfied.

### FAIL

```
VIII3_FAIL / <reason>
```

### INVALID

```
INVALID_RUN / <reason>
```

---

## 22. Execution Parameters

| Parameter | Value |
|-----------|-------|
| Initial Epoch | 0 |
| Max Event Budget | 50 |
| Condition Sequence | A → B → C → D |
| Kernel Instances | 1 (single cumulative run) |
| Gas Constants | Inherited from VIII-2 |

### Canonical Authority Configurations

**Condition A:**
- AUTH_A: StartEpoch=0, ExpiryEpoch=2, Scope=(R0000, OP0), Permits=["EXECUTE_OP0"]
- AUTH_B: StartEpoch=0, ExpiryEpoch=2, Scope=(R0000, OP0), Permits=["EXECUTE_OP0"]

**Condition B:**
- AUTH_C: StartEpoch=3, ExpiryEpoch=10, Scope=(R0001, OP1), Permits=["EXECUTE_OP1"]

**Condition C:**
- AUTH_D: StartEpoch=3, ExpiryEpoch=10, Scope=(R0002, OP2), Permits=["EXECUTE_OP2"]
- AUTH_DX: StartEpoch=3, ExpiryEpoch=10, Scope=(R0002, OP2), Permits=[]
- AUTH_E: StartEpoch=3, ExpiryEpoch=10, Scope=(R0002, OP2), Permits=["EXECUTE_OP2"], Prior=AUTH_D

**Condition D:**
- AUTH_F: StartEpoch=3, ExpiryEpoch=10, Scope=(R0003, OP3), Permits=["EXECUTE_OP3"]
- AUTH_G: StartEpoch=3, ExpiryEpoch=5, Scope=(R0003, OP3), Permits=[]
- AUTH_H: StartEpoch=6, ExpiryEpoch=10, Scope=(R0003, OP3), Permits=[], Prior=AUTH_G

---

## 23. Licensed Claim (on PASS)

> *Authority can persist over time only via explicit renewal under open-system constraints; time does not resolve conflict or eliminate cost.*

---

## 24. Preregistration Freeze

**Document Hash (SHA-256):**
```
9d7d04384bcf4c36520ffd4fa0da143b04dc6e8e86d2229e4f132ae78fea7a35
```

**Freeze Timestamp:** `2026-02-03T00:00:00Z`

No modifications permitted after freeze without version increment.

---

**End of Preregistration Document — Stage VIII-3 v0.1**
