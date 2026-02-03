# Stage VIII-3 v0.1 — Implementation Questions

These questions require binding clarifications before preregistration.

---

## 1. Epoch Mechanics

### Q1.1 — Epoch Advancement Event Structure

What is the canonical structure of an `EpochAdvancementRequest`?

Proposed minimal schema:
```
EpochAdvancementRequest {
  newEpoch: Integer,
  nonce: DeterministicNonce
}
```

Is there additional required metadata (e.g., authorizerID, eventID)?

---

### Q1.2 — Automatic Expiry Trigger

Spec states: "At `CurrentEpoch > ExpiryEpoch`: authority transitions from ACTIVE to EXPIRED."

Is this transition:
- (a) evaluated lazily on next admissibility check, or
- (b) applied immediately when epoch advances, before any other processing?

If (b), does the kernel emit `AUTHORITY_EXPIRED` for each affected authority during epoch advancement?

---

### Q1.3 — Epoch Advancement Output

Does epoch advancement produce an output event (e.g., `EPOCH_ADVANCED`)?

The spec's output list does not include such an event. Should epoch advancement be logged as a state transition only, or does it require an explicit output?

---

## 2. Authority Expiry

### Q2.1 — ExpiryEpoch Semantics

Given `ExpiryEpoch = 5`:
- Is the authority ACTIVE at epoch 5?
- Does it transition to EXPIRED at epoch 6, or at the moment epoch advances past 5?

Clarify: `CurrentEpoch > ExpiryEpoch` vs `CurrentEpoch >= ExpiryEpoch`.

---

### Q2.2 — Multiple Simultaneous Expirations

If multiple authorities expire on the same epoch advancement, what is the ordering of `AUTHORITY_EXPIRED` events? Is it:
- (a) deterministic based on AuthorityID,
- (b) deterministic based on injection order,
- (c) unordered (set semantics)?

---

### Q2.3 — EXPIRED State Output

The spec lists `AUTHORITY_EXPIRED` as a valid output. Is this emitted:
- per authority that transitions to EXPIRED, or
- as a batch summary?

---

## 3. Authority Renewal

### Q3.1 — Renewal Request Event Structure

What is the canonical structure of an `AuthorityRenewalRequest`?

Proposed minimal schema:
```
AuthorityRenewalRequest {
  newAuthority: AuthorityRecord,
  priorAuthorityId: AuthorityID | null,
  renewalEventId: EventID,
  externalAuthorizingSourceId: ExternalSourceID,
  nonce: DeterministicNonce
}
```

Is `priorAuthorityId` required, or optional when creating fresh authority?

---

### Q3.2 — Renewal vs New Injection

Spec says renewal creates "a new Authority Record whose scope may resemble a prior authority."

Is renewal semantically different from a new `AuthorityInjection`? Or is renewal simply an AuthorityInjection with optional `PriorAuthorityID` metadata?

---

### Q3.3 — Renewal Output

Spec lists `AUTHORITY_RENEWED` as output. What is the relationship between:
- `AUTHORITY_INJECTED` (from VIII-1/VIII-2)
- `AUTHORITY_RENEWED` (new in VIII-3)

Are these mutually exclusive? Does renewal emit `AUTHORITY_RENEWED` only, or both?

---

### Q3.4 — Renewal of VOID Authority

Spec says: "Renewal referencing a VOID authority is permitted, but does not alter the VOID state."

What output is emitted when renewing a VOID authority?
- `AUTHORITY_RENEWED` (for the new authority), or
- A special indicator that the prior was VOID?

Does the kernel validate that `priorAuthorityId` exists and is VOID/EXPIRED, or is any reference permitted?

---

### Q3.5 — Renewal Scope Overlap

Condition B specifies "renewal injected without overlapping scope."
Condition D specifies "renewal injected for one conflicting side."

Does the kernel validate scope overlap at renewal time, or is this purely a harness responsibility?

---

## 4. Conflict and Deadlock Persistence

### Q4.1 — Conflict Across Epochs

If a conflict exists between AUTH_A and AUTH_B at epoch 5, and neither is destroyed or renewed, does the conflict:
- (a) persist automatically at epoch 6, or
- (b) require re-detection when an action is requested at epoch 6?

---

### Q4.2 — Conflict Resolution via Expiry

If one conflicting authority expires (AUTH_B), and the other remains ACTIVE (AUTH_A):
- Is the conflict resolved, or
- Does the conflict persist with one EXPIRED participant?

Per the anti-ordering invariant, expiry should not implicitly resolve conflict. But if AUTH_B is no longer ACTIVE, it cannot participate in admissibility evaluation. What is the semantic outcome?

---

### Q4.3 — Deadlock Across Epochs

If kernel is in STATE_DEADLOCK at epoch 5 and epoch advances to 6 with no intervention:
- Does deadlock persist, or
- Must the kernel re-evaluate deadlock conditions?

---

## 5. Conditions Sequencing

### Q5.1 — Condition State Carryover

Instructions say "Conditions are stateful and sequential."

Does this mean:
- (a) All conditions run in a single kernel instance with cumulative state, or
- (b) Each condition is a separate run, but prerequisites must be satisfied?

---

### Q5.2 — Condition B Prerequisite

Condition B: "Prerequisite: Condition A executed."

Does this mean:
- Condition B runs in the same kernel after Condition A completes, or
- Condition B is a fresh kernel but A must have passed in a prior run?

---

### Q5.3 — Condition C Setup

Condition C: "VOID authority exists" and "authority destroyed in VIII-2-like configuration."

Is this:
- (a) reusing VIII-2 destruction mechanics (DestructionAuthorization event), or
- (b) a fresh injection + destruction within VIII-3?

Does Condition C require running Condition A/B first?

---

### Q5.4 — Condition D Conflict Source

Condition D: "conflict persists" and "renewal injected for one side."

Is this conflict inherited from a prior condition, or must it be induced within Condition D?

---

## 6. Classification and Success Criteria

### Q6.1 — Per-Condition Classification

Does each condition (A, B, C, D) produce a sub-classification, or is VIII-3 classification based on all conditions together?

---

### Q6.2 — Partial Failure

If Condition A passes but Condition B fails, is the overall result:
- `VIII3_FAIL / CONDITION_B_FAILED`, or
- `VIII3_FAIL / <specific-reason>`?

---

## 7. New Authority States

### Q7.1 — EXPIRED vs VOID

What distinguishes EXPIRED from VOID semantically?
- Both are non-participants in admissibility
- Both are irreversible (except via renewal for EXPIRED?)

Is the only difference:
- EXPIRED: temporal lapse (can be referenced by renewal)
- VOID: explicit destruction (can also be referenced by renewal per spec)

If both can be referenced by renewal, what is the behavioral difference?

---

### Q7.2 — EXPIRED Renewability

Spec says renewal of VOID is "non-resurrective." Is renewal of EXPIRED also non-resurrective?

Or does renewal of EXPIRED have special semantics (e.g., continuity of scope)?

---

## 8. Integration with VIII-2

### Q8.1 — DestructionAuthorization in VIII-3

Is the `DestructionAuthorizationEvent` from VIII-2 still a valid input in VIII-3?

Or is destruction only reachable via expiry in VIII-3?

---

### Q8.2 — VOID from Destruction vs VOID from ???

In VIII-2, VOID results from destruction. In VIII-3, can VOID result from any other transition?

Or is VOID exclusively reached via explicit destruction (never via expiry)?

---

## 9. Output and Logging

### Q9.1 — AUTHORITY_EXPIRED Format

What details should `AUTHORITY_EXPIRED` output contain?

Proposed:
```
{
  authority_id: AuthorityID,
  expiry_epoch: Integer,
  current_epoch: Integer
}
```

---

### Q9.2 — AUTHORITY_RENEWED Format

What details should `AUTHORITY_RENEWED` output contain?

Proposed:
```
{
  new_authority_id: AuthorityID,
  prior_authority_id: AuthorityID | null,
  renewal_event_id: EventID,
  renewal_epoch: Integer
}
```

---

### Q9.3 — Epoch in State Hash

Should the current epoch be included in the state hash computation?

---

## 10. Harness Design

### Q10.1 — Canonical Epoch Sequence

What is the canonical epoch sequence for testing?

Proposed: Start at epoch 0, advance to epochs 1, 2, 3, etc.

---

### Q10.2 — Authority Lifetimes for Conditions

What are the canonical authority lifetimes for each condition?

Condition A needs authorities that expire. Proposed:
- AUTH_A: StartEpoch=0, ExpiryEpoch=2
- AUTH_B: StartEpoch=0, ExpiryEpoch=2

---

### Q10.3 — Deterministic Nonces

Should renewal and epoch advancement events use a separate nonce sequence, or continue from VIII-2 nonce space?

---

## 11. Scope and Transformation

### Q11.1 — PermittedTransformationSet in VIII-3

Is `PermittedTransformationSet` still used for admissibility in VIII-3, or does VIII-3 use simpler permit/deny semantics?

---

### Q11.2 — Renewal Scope Independence

When a renewal is injected, must its scope be identical to the prior authority, or can it differ?

If it can differ, does the kernel validate any relationship?

---

## 12. Edge Cases

### Q12.1 — Renewal Before Expiry

Can a renewal reference an authority that is still ACTIVE (not yet expired)?

If so, what happens to the original authority?

---

### Q12.2 — Renewal at Expiry Epoch

If AUTH_A expires at epoch 5, and a renewal referencing AUTH_A is injected at epoch 5 (before epoch advances):
- Is AUTH_A still ACTIVE at injection time?
- Does renewal succeed referencing an ACTIVE authority?

---

### Q12.3 — Empty Authority Set

If all authorities expire and no renewal is injected, what is the kernel state?
- STATE_DEADLOCK (no authority to satisfy any request), or
- Some other state (e.g., STATE_INACTIVE)?

---

---

# Follow-Up Questions (Post-Clarification)

These questions arise from the binding clarifications and require resolution before preregistration.

---

## F1. Epoch Advancement Processing Order

### F1.1 — Event Ordering Within Epoch Advancement

Per A1.2, epoch advancement triggers eager expiry before any other processing.

If the harness injects:
1. EpochAdvancementRequest (0 → 1)
2. ActionRequest
3. AuthorityRenewalRequest

...all submitted "at" epoch 1, what is the processing order?

Is it:
- (a) Epoch advances → expirations processed → then events in submission order, or
- (b) Epoch advances, then each subsequent event is processed with full state recalculation?

---

### F1.2 — Expiry Output Event Index

When `AUTHORITY_EXPIRED` events are emitted during epoch advancement, do they share the same `event_index` as the epoch transition, or do they get sequential indices?

---

## F2. Conflict Cessation Semantics

### F2.1 — Conflict "Ceases to Bind" vs Conflict Resolution

A4.2 states: "The conflict ceases to bind because only ACTIVE authorities are evaluated."

Does this mean:
- (a) The conflict record is removed/closed, or
- (b) The conflict record persists but is no longer blocking?

If (b), what is the status of the conflict record? Does it remain `OPEN`?

---

### F2.2 — Re-Binding of Conflict

If AUTH_B expires (conflict ceases to bind), and then a renewal creates AUTH_C with overlapping scope to AUTH_A:
- Is this a **new conflict** (C:0002), or
- Does the original conflict (C:0001) somehow re-bind?

---

## F3. Single Kernel Instance Implications

### F3.1 — Condition Sequencing Event Indices

Per A5.1, all conditions execute in one kernel instance.

Does this mean event indices are continuous across conditions (e.g., Condition A ends at event 10, Condition B starts at event 11)?

---

### F3.2 — Condition Boundaries in Logs

How should the transition between conditions be logged?

Proposed:
- Log a `CONDITION_START` marker (non-output, trace only)
- Or simply continue event stream with no boundary?

---

### F3.3 — Condition C Independence

A5.3 states: "Conditions A and B are not required before C unless explicitly desired."

But A5.1 says all conditions execute in one kernel instance.

Does this mean:
- Condition C can be the **first** condition in a run, or
- Condition C requires at least one prior condition to establish the kernel, but A/B specifically are optional?

---

## F4. STATE_DEADLOCK Entry Conditions

### F4.1 — Deadlock from Empty Authority Set

A12.3 says no ACTIVE authorities → STATE_DEADLOCK.

Is deadlock **declared** at the moment the last authority expires, or only when an action request is refused?

---

### F4.2 — Deadlock Without Conflict

If all authorities expire (no conflict, just absence of authority), is this:
- STATE_DEADLOCK (same state as conflict deadlock), or
- A distinct state?

The spec's `DEADLOCK_DECLARED` implies conflict-based deadlock. Does absence of authority produce the same event?

---

## F5. Renewal and Conflict Interaction

### F5.1 — Renewal Creating Conflict

Per A12.1, renewal before expiry can create overlap and conflict.

If AUTH_A is ACTIVE and renewal creates AUTH_C with identical scope:
- Is conflict immediately registered, or
- Only when an action is requested?

(Per VIII-1/VIII-2, conflict is registered on action request.)

---

### F5.2 — Condition D Conflict Preservation

A5.4 says conflict must be active at renewal time.

After renewal for one side, does the conflict:
- Persist (because renewal doesn't resolve conflict), or
- Require re-detection?

---

## F6. Authority Identity Mechanics

### F6.1 — AuthorityID Generation for Renewals

Renewal creates a new AuthorityID. Is this:
- Harness-generated (in the `AuthorityRenewalRequest.newAuthority` field), or
- Kernel-generated?

---

### F6.2 — AuthorityID Uniqueness Validation

Does the kernel validate that the new AuthorityID has never been used before?

---

## F7. Destruction in VIII-3 Context

### F7.1 — Destruction of EXPIRED Authority

Can `DestructionAuthorizationEvent` target an EXPIRED authority?

If so, does it transition to VOID, or is destruction refused?

---

### F7.2 — Destruction Metadata Preservation

In VIII-2, destroyed authorities preserve `DestructionMetadata`. Is this maintained in VIII-3?

---

## F8. Expiry vs Destruction Audit Trail

### F8.1 — EXPIRED Metadata

Does `EXPIRED` state preserve metadata similar to `VOID`?

Proposed:
```
ExpiryMetadata {
  expiry_epoch: Integer,
  actual_transition_epoch: Integer
}
```

---

### F8.2 — Prior Authority Reference Validation

A3.4 says kernel validates that `priorAuthorityId` exists but not state compatibility.

Does "exists" mean:
- (a) Record exists in Authority State (any status), or
- (b) Record was ever injected (historical)?

---

## F9. Condition-Specific Clarifications

### F9.1 — Condition A Expected Sequence

Condition A: "authorities expire, no renewal, deadlock persists."

Expected sequence:
1. Inject AUTH_A, AUTH_B
2. ActionRequest → succeeds (or conflicts?)
3. Epoch advance past ExpiryEpoch
4. Both expire
5. ActionRequest → refused (no authority)
6. DEADLOCK_DECLARED or DEADLOCK_PERSISTED?

What is the canonical event sequence?

---

### F9.2 — Condition B Non-Overlapping Scope

Condition B: "renewal without overlapping scope."

If original AUTH_A/AUTH_B covered scope `(R0000, OP0)`, and renewal AUTH_C covers `(R0001, OP1)`:
- Is this considered "admissibility restored" for the original scope, or
- Is admissibility restored only for the new scope?

---

### F9.3 — Condition C VOID Preservation

Condition C: "VOID history preserved, no resurrection."

Expected verifications:
- Original authority remains VOID
- New authority is ACTIVE
- priorAuthorityId correctly references the VOID authority

Is there additional verification required?

---

### F9.4 — Condition D No Priority Inference

Condition D: "no priority inferred from renewal timing."

How is this verified?

Proposed: Both original conflict parties remain in conflict state after renewal, no implicit resolution.

---

## F10. Output Event Additions

### F10.1 — EPOCH_ADVANCED Forbidden

A1.3 confirms no `EPOCH_ADVANCED` output.

But the spec lists valid outputs. Should epoch transitions be logged in a separate trace channel, or only reflected in state hash?

---

### F10.2 — CONFLICT_CEASED Event

A4.2 says conflict "ceases to bind" on expiry.

Is there an output event for this, or is it implicit (no event, just behavioral change)?

---

## F11. State Hash Computation

### F11.1 — Epoch in Hash

A9.3 confirms epoch is in state hash.

What else is included beyond VIII-2 components?
- All authority states (including EXPIRED)?
- Conflict records?
- Deadlock flag?
- Current epoch?

---

## F12. Preregistration Bindings

### F12.1 — Canonical Condition Sequence

What is the canonical condition order?

Proposed: A → B → C → D in single kernel run.

---

### F12.2 — Total Event Count

Approximately how many events are expected across all conditions?

(For gas budget planning.)

---

**End of Follow-Up Questions — Awaiting Final Clarifications**


---

# Second Follow-Up Questions (Post-Final Clarifications)

These questions arise from the final binding clarifications and require resolution before preregistration freeze.

---

## G1. Two-Phase Processing Mechanics

### G1.1 — Epoch Advancement Event Index

Per F1.2, `EpochAdvancementRequest` consumes one event index.

Does the epoch advancement produce an output, or is the event index consumed with no output (trace-only)?

If no output, how is the event index logged?

---

### G1.2 — Phase 0 Canonicalization Across Conditions

Per F1.1, Phase 0 collects and canonicalizes all inputs for a "step."

What defines a "step" boundary within a single kernel run?

Is it:
- (a) All inputs between epoch advancements, or
- (b) Explicitly batched by harness, or
- (c) Each input is its own step?

---

## G2. OPEN_NONBINDING Conflict Status

### G2.1 — Conflict Status Transitions

Per F2.1, conflict can be `OPEN_NONBINDING` when one party is non-ACTIVE.

Can a conflict transition:
- `OPEN` → `OPEN_NONBINDING` (on expiry), and
- `OPEN_NONBINDING` → `OPEN` (if renewal makes both parties ACTIVE again)?

Or is OPEN_NONBINDING a terminal status for that conflict record?

---

### G2.2 — Conflict Status in State Hash

Per F11.1, conflict records include status in state hash.

Does this mean `OPEN_BINDING` vs `OPEN_NONBINDING` distinction affects state hash?

---

## G3. Deadlock Cause Semantics

### G3.1 — MIXED Deadlock Cause

Per F4.2, `deadlock_cause` can be `MIXED`.

When does MIXED apply?

Proposed: When both conflict-based and empty-authority conditions contribute simultaneously.

---

### G3.2 — Deadlock Cause Transition

If deadlock was declared with cause `CONFLICT`, and later all authorities expire:

Does deadlock_cause transition to `MIXED` or remain `CONFLICT`?

---

## G4. Trace Markers

### G4.1 — TRACE_MARKER Schema

Per F3.2, condition boundaries use trace-only markers.

What is the full schema for these markers?

Proposed:
```
TRACE_MARKER {
  marker_type: "CONDITION_START" | "CONDITION_END",
  condition: "A" | "B" | "C" | "D",
  event_index: Integer (for ordering in trace)
}
```

---

### G4.2 — Trace Marker Event Indices

Do trace markers consume event indices, or are they indexed separately?

---

## G5. ExpiryMetadata Fields

### G5.1 — triggering_event_id

Per F8.1, ExpiryMetadata includes `triggering_event_id`.

Is this the EventID of the EpochAdvancementRequest that caused the transition?

---

### G5.2 — Expiry Metadata Attachment

When is ExpiryMetadata attached to the authority record?

- At transition time (when AUTHORITY_EXPIRED is emitted), or
- Retroactively at state hash computation?

---

## G6. PRIOR_AUTHORITY_NOT_FOUND Error

### G6.1 — Scope of Validation

Per F8.2, referencing an unknown AuthorityID produces `INVALID_RUN / PRIOR_AUTHORITY_NOT_FOUND`.

Is this validated at:
- Renewal request processing time, or
- State hash computation time?

---

### G6.2 — Null priorAuthorityId

Per A3.1, `priorAuthorityId` can be null for fresh authority.

Does null bypass the existence check entirely?

---

## G7. Condition A Conflict Behavior

### G7.1 — Initial Action Admissibility

Per F9.1, Condition A includes ActionRequests that may be inadmissible.

Does Condition A require:
- (a) Conflicting authorities (VIII-2-style), or
- (b) Just expiring authorities (may be non-conflicting)?

If (b), is there conflict at all in Condition A?

---

### G7.2 — Deadlock Entry Without Conflict

If Condition A has no conflict (just expiry), deadlock is from `EMPTY_AUTHORITY`.

Is this sufficient for Condition A, or must Condition A demonstrate temporal conflict persistence?

---

## G8. Condition B Scope Mechanics

### G8.1 — Scope Coverage After Renewal

Per F9.2, admissibility is scope-relative.

If AUTH_A/AUTH_B covered `(R0000, OP0)` and expired, and AUTH_C covers `(R0001, OP1)`:

- Actions on `(R0000, OP0)` → refused (no covering authority)?
- Actions on `(R0001, OP1)` → admitted?

Is this the expected behavior for Condition B?

---

## G9. Condition D Conflict Dynamics

### G9.1 — Renewal Participant Change

Per F5.2, conflict participant set may change after renewal.

If AUTH_A and AUTH_B conflict, then AUTH_B expires and AUTH_C is renewed:

- Original conflict C:0001 becomes OPEN_NONBINDING
- New action triggers conflict detection between AUTH_A and AUTH_C → C:0002

Is this the expected dynamic for Condition D?

---

### G9.2 — Priority Inference Test

Per F9.4, verify by proposing an action admissible under renewed side only.

What if the renewed side was the permitting side (not denying)?

Should the test specifically renew the **denying** authority to prove no priority?

---

## G10. Gas and Event Budget

### G10.1 — Maximum Event Budget

Per F12.2, preregister a maximum event budget.

Proposed: 50 events maximum for canonical A→B→C→D run.

Is this sufficient, or should it be higher?

---

### G10.2 — Gas Constants

Are VIII-2 gas constants (`GAS_READ`, `GAS_UPDATE`, etc.) reused unchanged?

---

## G11. Output Schema Updates

### G11.1 — DEADLOCK_DECLARED Details

Per F4.2, deadlock output must include `deadlock_cause`.

Updated schema:
```
{
  deadlock_type: "CONFLICT_DEADLOCK" | "EMPTY_AUTHORITY_DEADLOCK" | "MIXED",
  deadlock_cause: "CONFLICT" | "EMPTY_AUTHORITY" | "MIXED",
  open_conflicts: [ConflictID],
  active_authority_count: Integer
}
```

Is this correct?

---

### G11.2 — AUTHORITY_EXPIRED Details Update

Per F8.1, ExpiryMetadata is canonical.

Updated AUTHORITY_EXPIRED output:
```
{
  authority_id: AuthorityID,
  expiry_epoch: Integer,
  transition_epoch: Integer,
  triggering_event_id: EventID
}
```

Correct?

---

## G12. Success Criteria Formalization

### G12.1 — Per-Condition Success Criteria

What are the explicit success criteria for each condition?

Proposed:

**Condition A:**
- All authorities expire
- Deadlock declared/persisted
- No ACTIVE authorities remain
- Actions refused

**Condition B:**
- Renewal creates new authority
- Admissibility restored for new scope
- No history erasure (expired records persist)

**Condition C:**
- VOID authority referenced by renewal
- VOID state unchanged
- New authority ACTIVE
- No resurrection semantics

**Condition D:**
- Conflict active at renewal time
- Post-renewal action refused (conflict persists)
- No priority inferred from timing

---

### G12.2 — Global Success Criteria

What global criteria span all conditions?

Proposed:
- Determinism and replayability
- No implicit resolution
- No kernel-initiated renewal
- No temporal ordering
- Responsibility trace complete

---

**End of Second Follow-Up Questions — Preregistration Pending**
