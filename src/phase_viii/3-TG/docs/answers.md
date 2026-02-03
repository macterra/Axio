# **Stage VIII-3 v0.1 — Binding Clarifications**

---

## 1. Epoch Mechanics

### Q1.1 — Epoch Advancement Event Structure

**Canonical structure:**

```
EpochAdvancementRequest {
  newEpoch: Integer,
  eventId: EventID,
  nonce: DeterministicNonce
}
```

* `eventId` is required for audit traceability.
* No authorizer or legitimacy metadata is permitted.
* Epoch advancement is a **structural input**, not an authority action.

---

### Q1.2 — Automatic Expiry Trigger

Expiry is applied **eagerly at epoch advancement**.

Specifically:

1. Epoch advances.
2. All authorities with `ExpiryEpoch < CurrentEpoch` transition to `EXPIRED`.
3. `AUTHORITY_EXPIRED` is emitted **before** any admissibility evaluation or action processing at the new epoch.

Lazy expiry is forbidden.

---

### Q1.3 — Epoch Advancement Output

There is **no semantic output** such as `EPOCH_ADVANCED`.

Epoch advancement is logged as a **state transition** and reflected in:

* state hash,
* trace log,
* subsequent outputs (e.g., `AUTHORITY_EXPIRED`).

Adding an explicit epoch output is forbidden.

---

## 2. Authority Expiry

### Q2.1 — ExpiryEpoch Semantics

**Binding rule:**

* Authority is **ACTIVE** at `CurrentEpoch == ExpiryEpoch`.
* Authority transitions to **EXPIRED** when `CurrentEpoch > ExpiryEpoch`.

This matches the spec’s explicit condition.

---

### Q2.2 — Multiple Simultaneous Expirations

Ordering is **deterministic but semantically irrelevant**.

* Expiry events are ordered by canonical AuthorityID ordering.
* Consumers must not infer priority from this order.

Ordering exists for replay determinism only.

---

### Q2.3 — EXPIRED State Output

`AUTHORITY_EXPIRED` is emitted **per authority**, not as a batch.

Each transition produces one output event.

---

## 3. Authority Renewal

### Q3.1 — Renewal Request Event Structure

**Canonical structure:**

```
AuthorityRenewalRequest {
  newAuthority: AuthorityRecord,
  priorAuthorityId: AuthorityID | null,
  renewalEventId: EventID,
  externalAuthorizingSourceId: ExternalSourceID,
  nonce: DeterministicNonce
}
```

* `priorAuthorityId` is **optional**.
* `null` denotes a fresh authority (no historical linkage).

---

### Q3.2 — Renewal vs New Injection

Semantically:

* **Renewal is a specialized Authority Injection**.
* The only distinction is the presence of `priorAuthorityId` metadata.

There is **no difference** in authority force, admissibility, or evaluation.

---

### Q3.3 — Renewal Output

Renewal emits **only**:

```
AUTHORITY_RENEWED
```

It does **not** emit `AUTHORITY_INJECTED`.

These outputs are mutually exclusive.

---

### Q3.4 — Renewal of VOID Authority

When renewing a VOID authority:

* Kernel validates that `priorAuthorityId` **exists**.
* Kernel does **not** validate semantic relationship or state compatibility.
* Output is still:

```
AUTHORITY_RENEWED
```

No special indicator is emitted.
VOID state of the prior authority is unchanged and preserved.

---

### Q3.5 — Renewal Scope Overlap

The kernel performs **no scope validation at renewal time**.

* Scope overlap is evaluated **only during admissibility checks**.
* Conditions B and D are **harness responsibilities**, not kernel checks.

---

## 4. Conflict and Deadlock Persistence

### Q4.1 — Conflict Across Epochs

Conflict **persists structurally** across epochs.

* It is not re-detected.
* It is preserved as state until explicitly altered by destruction or renewal effects.

---

### Q4.2 — Conflict Resolution via Expiry

If one conflicting authority expires:

* It no longer participates in admissibility.
* The conflict **ceases to bind** because only ACTIVE authorities are evaluated.

This is **not implicit resolution**—it is loss of participation.

No special conflict cleanup event is emitted.

---

### Q4.3 — Deadlock Across Epochs

Deadlock **persists automatically** across epoch advancement.

No re-evaluation is performed unless authority state changes.

---

## 5. Conditions Sequencing

### Q5.1 — Condition State Carryover

All conditions execute in **one kernel instance** with cumulative state.

---

### Q5.2 — Condition B Prerequisite

Condition B runs **after Condition A** in the same run.

Fresh-kernel execution is invalid.

---

### Q5.3 — Condition C Setup

Condition C uses **VIII-2-style destruction mechanics** inside VIII-3.

* Authority is injected.
* Authority is explicitly destroyed (VOID).
* Renewal is injected afterward.

Conditions A and B are **not required** before C unless explicitly desired by the harness.

---

### Q5.4 — Condition D Conflict Source

Conflict must be **induced within Condition D** or inherited from a prior condition in the same run.

Both are valid as long as conflict is active at renewal time.

---

## 6. Classification and Success Criteria

### Q6.1 — Per-Condition Classification

There are **no per-condition classifications**.

Stage VIII-3 produces **exactly one** classification.

---

### Q6.2 — Partial Failure

Any condition failure yields:

```
VIII3_FAIL / <specific reason>
```

There is no “Condition X failed” wrapper classification.

---

## 7. New Authority States

### Q7.1 — EXPIRED vs VOID

**Binding distinction:**

* **EXPIRED** — temporal lapse
* **VOID** — explicit destruction

Both are:

* non-participants in admissibility,
* irreversible states.

Difference is **causal semantics**, not behavior.

---

### Q7.2 — EXPIRED Renewability

Renewal of EXPIRED authority is **non-resurrective**, exactly like VOID.

No continuity of force, scope, or legitimacy is implied.

---

## 8. Integration with VIII-2

### Q8.1 — DestructionAuthorization in VIII-3

Yes.

**DestructionAuthorizationEvent** remains a valid input in VIII-3.

---

### Q8.2 — VOID State Origin

VOID can **only** be reached via explicit destruction.

Expiry **never** produces VOID.

---

## 9. Output and Logging

### Q9.1 — AUTHORITY_EXPIRED Format

Approved canonical format:

```
{
  authority_id: AuthorityID,
  expiry_epoch: Integer,
  current_epoch: Integer
}
```

---

### Q9.2 — AUTHORITY_RENEWED Format

Approved canonical format:

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

**Yes.**

Current epoch **must** be included in state hash computation.

---

## 10. Harness Design

### Q10.1 — Canonical Epoch Sequence

Canonical sequence:

* Start at epoch `0`
* Advance monotonically: `1, 2, 3, …`

No skipping requirement, but determinism is mandatory.

---

### Q10.2 — Authority Lifetimes for Conditions

Canonical lifetimes (approved):

* AUTH_A: `StartEpoch = 0`, `ExpiryEpoch = 2`
* AUTH_B: `StartEpoch = 0`, `ExpiryEpoch = 2`

Harness may vary, but must be preregistered.

---

### Q10.3 — Deterministic Nonces

Nonce space is **continuous across Phase VIII**.

Do not reset or fork nonce sequences between stages.

---

## 11. Scope and Transformation

### Q11.1 — PermittedTransformationSet

Unchanged.

`PermittedTransformationSet` remains the admissibility mechanism.

VIII-3 does **not** simplify semantics.

---

### Q11.2 — Renewal Scope Independence

Renewal scope:

* **may differ arbitrarily** from prior authority,
* is **not validated** for similarity or continuity.

Kernel validates **nothing** beyond structural correctness.

---

## 12. Edge Cases

### Q12.1 — Renewal Before Expiry

Yes, permitted.

* Original authority remains ACTIVE.
* Renewal creates a new ACTIVE authority.
* Any overlap may create conflict.

---

### Q12.2 — Renewal at Expiry Epoch

If `ExpiryEpoch = 5` and `CurrentEpoch = 5`:

* Authority is still ACTIVE.
* Renewal referencing it is permitted.

Expiry occurs only after epoch advances.

---

### Q12.3 — Empty Authority Set

If no ACTIVE authorities exist:

* Kernel enters or remains in **STATE_DEADLOCK**.
* All actions are refused.
* This is a lawful terminal condition.

No separate “inactive” state exists.

---

## Final Binding Statement

These clarifications are **execution-binding**, **non-semantic**, and **complete**.

No additional interpretation is permitted during implementation or preregistration.

If an implementation requires further assumptions, the run is invalid.

---

# **Stage VIII-3 v0.1 — Final Binding Clarifications (Follow-Ups)**

---

## F1. Epoch Advancement Processing Order

### F1.1 — Event Ordering Within Epoch Advancement

**Binding rule:** processing is **two-phase** with explicit canonicalization.

Within a single epoch step where the harness submits:

1. `EpochAdvancementRequest (t → t+1)`
2. `ActionRequest`
3. `AuthorityRenewalRequest`

the kernel processes as:

**Phase 0 — Canonicalize Inputs**

* Collect all inputs for the step.
* Canonically order them (see F1.1 ordering rules below).
* Reject if more than one epoch advancement is present.

**Phase 1 — Apply Epoch Transition**

1. Apply epoch advancement (`CurrentEpoch := newEpoch`).
2. Apply eager expirations for all authorities with `ExpiryEpoch < CurrentEpoch`.
3. Emit `AUTHORITY_EXPIRED` events for each expired authority.

**Phase 2 — Process Remaining Inputs**

* Process renewal requests.
* Process destruction events.
* Process action requests.

**Canonical ordering among non-epoch inputs (Phase 2):**

1. `AuthorityRenewalRequest` (in canonical order)
2. `DestructionAuthorizationEvent` (in canonical order)
3. `ActionRequest` (in canonical order)

This guarantees:

* expiry happens before any new authority injection in the new epoch,
* renewal cannot “preempt” expiry,
* action evaluation happens after authority state is stabilized.

---

### F1.2 — Expiry Output Event Index

Event indices are **strictly sequential** across the entire run.

* `EpochAdvancementRequest` consumes one event index.
* Each `AUTHORITY_EXPIRED` emitted consumes its own event index, in canonical AuthorityID order.
* No shared indices.

---

## F2. Conflict Cessation Semantics

### F2.1 — Conflict Record Persistence

**Binding rule:** conflict records are **persistent historical objects** and are never deleted.

When expiry makes a conflict non-binding (because one party is no longer ACTIVE):

* the conflict record remains present with status:

```
OPEN_NONBINDING
```

Meaning:

* recorded as a historically observed structural contention,
* not currently blocking admissibility because at least one participant is non-ACTIVE.

This is not “resolution.” It is loss of binding participation.

---

### F2.2 — Re-Binding of Conflict After Renewal

If AUTH_B expires and later a renewal produces AUTH_C that conflicts with AUTH_A:

This is a **new conflict** with a new conflict identifier (e.g., `C:0002`).

No conflict record ever “re-binds” by ancestry, lineage, or priorAuthorityId.

Conflict identity is defined by the **active participant set** at time of detection, not by history.

---

## F3. Single Kernel Instance Implications

### F3.1 — Condition Sequencing Event Indices

Yes. Event indices are **continuous** across conditions.

---

### F3.2 — Condition Boundaries in Logs

Condition boundaries must be logged as **trace-only markers**, not outputs.

Canonical:

* `TRACE_MARKER / CONDITION_START / <A|B|C|D>`
* `TRACE_MARKER / CONDITION_END / <A|B|C|D>`

These markers:

* do not appear in the “outputs” channel,
* do not affect admissibility,
* are included in the audit log and replay trace,
* may be excluded from state hash computation (see F11).

---

### F3.3 — Condition C Independence

Condition C may be the **first** condition in a run.

“Single kernel instance” means:

* one kernel instance per run,
* not that A must precede all others.

However, **the canonical preregistration sequence for VIII-3 is A → B → C → D** (see F12.1).
If you preregister an alternate ordering, it must be explicit.

---

## F4. STATE_DEADLOCK Entry Conditions

### F4.1 — Deadlock from Empty Authority Set

Deadlock is declared **eagerly** at the moment the last ACTIVE authority is lost **if** the kernel is already in a state where no admissible actions exist.

Binding rule:

* After each epoch advancement (post-expiry) and after each authority-state mutation (renewal/destruction), the kernel evaluates:

```
if ACTIVE_AUTHORITY_SET == ∅  → enter/maintain STATE_DEADLOCK
```

Thus, if expiry causes `ACTIVE_AUTHORITY_SET` to become empty, the kernel emits:

* `DEADLOCK_DECLARED` if not already deadlocked
* otherwise `DEADLOCK_PERSISTED`

No action request is required to trigger deadlock.

---

### F4.2 — Deadlock Without Conflict

Yes: absence-of-authority deadlock uses the **same state**.

There is no distinct state for “no authority.”

`DEADLOCK_DECLARED` may be caused by either:

* structural conflict with no admissible actions, or
* empty ACTIVE authority set.

To prevent ambiguity in audits, the deadlock output must include a **deadlock_cause** field:

```
deadlock_cause ∈ { CONFLICT, EMPTY_AUTHORITY, MIXED }
```

This is diagnostic metadata only, not semantics.

---

## F5. Renewal and Conflict Interaction

### F5.1 — Renewal Creating Conflict

Conflict is registered **only when an action is evaluated** (admissibility check), not at renewal injection time.

Renewal may create the *potential* for conflict; conflict becomes an explicit registered record on the first action request that triggers admissibility evaluation involving the conflicting ACTIVE authorities.

This matches VIII-1 / VIII-2 discipline.

---

### F5.2 — Condition D Conflict Preservation

After renewal for one side:

* conflict does not “persist” by fiat,
* it remains either:

  * binding if the newly renewed authority and the opposing authority both remain ACTIVE and conflicting on evaluation, or
  * non-binding if one party is non-ACTIVE, or
  * replaced by a new conflict record if participant set changed.

No re-detection is performed until an action request triggers admissibility evaluation.
When triggered, the kernel must not infer priority from renewal timing.

---

## F6. Authority Identity Mechanics

### F6.1 — AuthorityID Generation for Renewals

AuthorityID is **harness-generated** as part of the `AuthorityRecord` inside the renewal request.

Kernel generation is forbidden.

---

### F6.2 — AuthorityID Uniqueness Validation

Yes. Kernel must validate AuthorityID uniqueness.

If a new injection or renewal attempts to introduce an AuthorityID already present in the authority state (historical or current), the run is invalid:

```
INVALID_RUN / AUTHORITY_ID_REUSE
```

---

## F7. Destruction in VIII-3 Context

### F7.1 — Destruction of EXPIRED Authority

Permitted.

An EXPIRED authority may be explicitly destroyed and transitions:

* `EXPIRED → VOID`

This does not resurrect anything; it is a stronger terminalization.

---

### F7.2 — Destruction Metadata Preservation

Yes. VIII-2 destruction metadata preservation remains binding in VIII-3.

VOID records must preserve:

* destruction event id,
* authorizing source id (opaque),
* epoch of destruction,
* any AST-required structural fields.

---

## F8. Expiry vs Destruction Audit Trail

### F8.1 — EXPIRED Metadata

Yes. EXPIRED state must preserve explicit expiry metadata.

Canonical:

```
ExpiryMetadata {
  expiry_epoch: Integer,
  transition_epoch: Integer,
  triggering_event_id: EventID
}
```

Where:

* `transition_epoch` is the epoch when it became EXPIRED (i.e., first epoch where `CurrentEpoch > ExpiryEpoch`)
* `triggering_event_id` is the epoch advancement event that caused the transition

---

### F8.2 — Prior Authority Reference Validation

“Exists” means:

* the AuthorityID exists **in the kernel’s authority store**, including historical records in any status (ACTIVE, EXPIRED, VOID).

A reference to an unknown AuthorityID is invalid:

```
INVALID_RUN / PRIOR_AUTHORITY_NOT_FOUND
```

---

## F9. Condition-Specific Clarifications

### F9.1 — Condition A Canonical Event Sequence

Canonical minimal sequence (illustrative; may include additional refused actions as long as preregistered):

1. Inject `AUTH_A`, `AUTH_B` (epoch 0)
2. ActionRequest(s) that are inadmissible (conflict or absence), producing refusals
3. EpochAdvance to `1` (no expiry yet if ExpiryEpoch=2)
4. EpochAdvance to `2` (still ACTIVE at epoch 2)
5. EpochAdvance to `3` → triggers expiry of any with `ExpiryEpoch=2`
6. Emit `AUTHORITY_EXPIRED` for each expired authority
7. Kernel enters deadlock if ACTIVE set becomes empty → emit `DEADLOCK_DECLARED` (or `DEADLOCK_PERSISTED` if already deadlocked)
8. Subsequent ActionRequest → refused; emit `DEADLOCK_PERSISTED`

Key requirement: deadlock must persist lawfully after expiry.

---

### F9.2 — Condition B Non-Overlapping Scope and “Admissibility Restored”

“Admissibility restored” is **scope-relative**.

It means:

* admissibility is restored **for the scope governed by the renewed authority**, not for the original expired scope unless that scope is explicitly covered by an ACTIVE authority.

No implicit restoration of prior coverage is permitted.

---

### F9.3 — Condition C VOID Preservation Verification

Required verifications:

1. Prior authority remains `VOID` with preserved destruction metadata.
2. New authority is `ACTIVE` (until its expiry).
3. Renewal metadata correctly references the VOID AuthorityID (existence only).
4. No state transition of the VOID authority occurs as a result of renewal.
5. Admissibility decisions treat the new authority as independent.

No additional verification is required.

---

### F9.4 — Condition D No Priority Inference Verification

Verified by **negative evidence** under action evaluation:

1. After renewal, propose an action that would be admissible under the renewed side and inadmissible under the opposing side.
2. Kernel must **not** execute it by treating renewal timing as precedence.
3. The action must be refused if conflict exists among ACTIVE authorities.

Operationally:

* same refusal behavior as if both authorities were newly injected in the same epoch.

---

## F10. Output and Logging

### F10.1 — Logging Epoch Transitions

Epoch transitions are logged in the **trace channel** only (not outputs), including:

* `eventId`
* `oldEpoch`
* `newEpoch`
* `nonce`

Epoch is also reflected in state hash.

---

### F10.2 — CONFLICT_CEASED Event

No such output exists.

Binding changes in conflict binding status occur implicitly through admissibility behavior, while the conflict record status transitions to `OPEN_NONBINDING` internally and is visible in the audit trace/state snapshot.

No additional outputs are permitted.

---

## F11. State Hash Computation

### F11.1 — Components Included in State Hash

State hash must include, at minimum:

1. `CurrentEpoch`
2. All authority records and their states (ACTIVE/EXPIRED/VOID)
3. All authority lifecycle metadata (expiry metadata, destruction metadata)
4. Conflict records (including status OPEN_BINDING / OPEN_NONBINDING and participant AuthorityIDs)
5. Deadlock flag + deadlock_cause (CONFLICT/EMPTY_AUTHORITY/MIXED)
6. Canonical nonce counter / event index (whichever the system uses as the deterministic progression anchor)

Trace-only condition markers are excluded from state hash.

---

## F12. Preregistration Bindings

### F12.1 — Canonical Condition Sequence

Canonical preregistered condition order for VIII-3 is:

**A → B → C → D** in a **single kernel run**.

If you intend another order, preregister it explicitly.

---

### F12.2 — Total Event Count

No fixed count is licensed.

However, for gas budgeting, a typical canonical A→B→C→D run will include:

* 3–6 epoch advancement events
* 2–6 action requests
* 1–3 renewal injections
* 0–2 destruction events
* 2–6 expiry outputs (depending on authority count)
* 1 deadlock declaration + multiple deadlock persisted outputs

Preregister a **maximum event budget** and enforce refusal-on-exhaustion.

---

## Final Binding Statement

These follow-up clarifications are **final** for Stage VIII-3 v0.1 preregistration.

Any additional behavior not covered here must be treated as:

```
INVALID_RUN / UNSPECIFIED_MECHANISM
```

---

# **Stage VIII-3 v0.1 — Final Binding Clarifications (Second Follow-Up)**

---

## G1. Two-Phase Processing Mechanics

### G1.1 — Epoch Advancement Event Index

`EpochAdvancementRequest` is an **input event** that consumes an event index and is logged **trace-only**.

* It produces **no output** event.
* It is recorded in the trace stream as an **input record** with its consumed `event_index`.

Canonical trace record (input channel):

```
TRACE_INPUT {
  type: "EPOCH_ADVANCEMENT_REQUEST",
  event_index: Integer,
  event_id: EventID,
  old_epoch: Integer,
  new_epoch: Integer,
  nonce: DeterministicNonce
}
```

---

### G1.2 — Phase 0 Canonicalization Across Conditions

A “step” boundary is **explicitly defined by the harness** as a **batch**.

Binding rule:

* The harness submits a `STEP_BATCH` containing 0 or 1 epoch advancement plus 0..N other inputs.
* The kernel processes exactly one batch at a time.
* Canonicalization occurs **within** a batch only.

This avoids any implicit “between epoch advancements” semantics and keeps batching explicit and deterministic.

Canonical batch envelope (trace-only wrapper):

```
STEP_BATCH {
  step_id: Integer,
  inputs: [ ... ]
}
```

`STEP_BATCH` is trace-only and does not consume event indices (see G4.2).

---

## G2. OPEN_NONBINDING Conflict Status

### G2.1 — Conflict Status Transitions

A conflict record’s binding status is a **derived property** of participant activity.

Binding rule:

* Conflict record identity is immutable.
* Conflict record binding status may transition:

```
OPEN_BINDING ↔ OPEN_NONBINDING
```

based solely on whether **all** participants are ACTIVE.

If a participant becomes non-ACTIVE (EXPIRED/VOID) → `OPEN_NONBINDING`.
If later all original participants become ACTIVE again (possible only if non-ACTIVE transitions back to ACTIVE existed, which they do not) then it could return to `OPEN_BINDING`.

However, because EXPIRED/VOID are irreversible, in practice:

* `OPEN_BINDING → OPEN_NONBINDING` may occur,
* `OPEN_NONBINDING → OPEN_BINDING` will **not** occur for that record.

This is not a new invariant; it is a consequence of irreversibility.

---

### G2.2 — Conflict Status in State Hash

Yes.

`OPEN_BINDING` vs `OPEN_NONBINDING` is included in the hashed conflict-record serialization and therefore affects the state hash.

---

## G3. Deadlock Cause Semantics

### G3.1 — MIXED Deadlock Cause

`MIXED` applies when **both** are true at evaluation time:

1. `ACTIVE_AUTHORITY_SET == ∅` (empty authority), and
2. there exists at least one conflict record with status `OPEN_BINDING` **or** `OPEN_NONBINDING` that was previously observed in-run.

Operationally: governance history contains conflict, and the system is now also authority-empty.

This is diagnostic only.

---

### G3.2 — Deadlock Cause Transition

`deadlock_cause` is **not sticky**; it is recomputed when deadlock is emitted (`DECLARED` or `PERSISTED`).

So:

* if deadlock was `CONFLICT` at epoch 5,
* and later all authorities expire,

then subsequent `DEADLOCK_PERSISTED` outputs must report `deadlock_cause = EMPTY_AUTHORITY` or `MIXED` depending on whether conflict history exists as defined in G3.1.

Given typical runs with prior conflict records, this becomes `MIXED`.

---

## G4. Trace Markers

### G4.1 — TRACE_MARKER Schema

Approved schema (trace-only):

```
TRACE_MARKER {
  marker_type: "CONDITION_START" | "CONDITION_END",
  condition: "A" | "B" | "C" | "D",
  trace_seq: Integer
}
```

`trace_seq` is a monotonically increasing counter for trace ordering (separate from event_index).

---

### G4.2 — Trace Marker Event Indices

Trace markers do **not** consume event indices.

Event indices are reserved for:

* input events (epoch advancement, renewal, destruction, action requests),
* output events (AUTHORITY_EXPIRED, AUTHORITY_RENEWED, ACTION_REFUSED, etc.).

Trace markers live in the trace stream with `trace_seq` only.

---

## G5. ExpiryMetadata Fields

### G5.1 — triggering_event_id

Yes.

`triggering_event_id` is the `EventID` of the `EpochAdvancementRequest` that caused the authority to transition to EXPIRED.

---

### G5.2 — Expiry Metadata Attachment

ExpiryMetadata is attached **at transition time**, atomically with the state change and emission of `AUTHORITY_EXPIRED`.

Retroactive attachment is forbidden.

---

## G6. PRIOR_AUTHORITY_NOT_FOUND Error

### G6.1 — Scope of Validation

Validated at **renewal request processing time** (Phase 2, renewal processing), before the authority store is updated.

If invalid, the run terminates as:

```
INVALID_RUN / PRIOR_AUTHORITY_NOT_FOUND
```

No later validation stages apply.

---

### G6.2 — Null priorAuthorityId

Yes.

`priorAuthorityId = null` bypasses existence checks entirely and is treated as “fresh authority.”

---

## G7. Condition A Conflict Behavior

### G7.1 — Initial Action Admissibility

Condition A is required to demonstrate **expiry without renewal** and the resulting lawful deadlock. Conflict is **optional**.

Two valid variants:

* **A0 (No-Conflict Expiry):** authorities may be non-conflicting; actions refused due to absence after expiry.
* **A1 (Conflict + Expiry):** conflict may exist prior to expiry; after expiry, deadlock persists under EMPTY_AUTHORITY or MIXED.

For preregistration, choose one variant and freeze it. Canonical default is **A0** (minimal).

---

### G7.2 — Deadlock Entry Without Conflict

Yes. This is sufficient for Condition A.

Condition A does **not** have to demonstrate conflict persistence; Stage VIII-3 already tests conflict persistence in Condition D.

---

## G8. Condition B Scope Mechanics

### G8.1 — Scope Coverage After Renewal

Yes. Expected behavior:

* Actions on expired scope `(R0000, OP0)` → refused (no ACTIVE covering authority).
* Actions on renewed scope `(R0001, OP1)` → may be admissible if ACTIVE authority exists and no conflict blocks it.

Condition B demonstrates that renewal restores admissibility **only for the renewed scope**, with no implicit restoration of prior coverage.

---

## G9. Condition D Conflict Dynamics

### G9.1 — Renewal Participant Change

Yes. This is the expected dynamic:

* Original conflict `C:0001` may become `OPEN_NONBINDING` if a participant expires.
* A renewed authority with new AuthorityID participates as a new entity.
* A new action may generate a new conflict `C:0002` if it conflicts with the still-ACTIVE opposing authority.

No conflict record rebinds by lineage.

---

### G9.2 — Priority Inference Test

The test must be constructed so that an implicit “freshness priority” would change behavior.

Binding harness requirement for Condition D:

* Renew the **denying** authority (or inject a renewed authority that denies) such that:

  * old conflict exists between an allow-permitting side and a deny side,
  * renewal could tempt “newest wins” logic to allow execution.

Then propose an action that:

* would be admissible if “newest wins” or “renewal implies priority,”
* but is inadmissible under symmetric anti-ordering rules.

Expected: refusal (conflict blocks).

---

## G10. Gas and Event Budget

### G10.1 — Maximum Event Budget

A maximum budget of **50 events** is sufficient for the canonical A→B→C→D run if kept minimal.

Binding requirement:

* preregister the max event count,
* enforce deterministic refusal-on-exhaustion,
* never use wall-clock timeouts.

---

### G10.2 — Gas Constants

Yes. Reuse VIII-2 gas constants unchanged.

No new gas categories are introduced in VIII-3 v0.1.

---

## G11. Output Schema Updates

### G11.1 — DEADLOCK_DECLARED Details

Your proposed schema is close, but it contains redundancy (`deadlock_type` and `deadlock_cause`) and introduces a new semantic “type.”

Binding schema:

```
{
  deadlock_cause: "CONFLICT" | "EMPTY_AUTHORITY" | "MIXED",
  open_conflicts: [ConflictID],
  active_authority_count: Integer,
  current_epoch: Integer
}
```

Notes:

* `open_conflicts` includes both `OPEN_BINDING` and `OPEN_NONBINDING` conflict IDs (for diagnostics).
* No deadlock “type” field.

Same schema applies to `DEADLOCK_PERSISTED`.

---

### G11.2 — AUTHORITY_EXPIRED Details Update

Correct.

Binding output schema:

```
{
  authority_id: AuthorityID,
  expiry_epoch: Integer,
  transition_epoch: Integer,
  triggering_event_id: EventID
}
```

---

## G12. Success Criteria Formalization

### G12.1 — Per-Condition Success Criteria

Approved, with one binding precision per condition:

**Condition A (Expiry Without Renewal):**

* All targeted authorities transition to EXPIRED at `CurrentEpoch > ExpiryEpoch`
* `ACTIVE_AUTHORITY_SET == ∅`
* `DEADLOCK_DECLARED` then `DEADLOCK_PERSISTED` on subsequent steps
* All actions refused

**Condition B (Renewal Without Conflict):**

* Renewal creates new AuthorityID, recorded by `AUTHORITY_RENEWED`
* Actions in renewed scope can become admissible (if no conflict)
* Expired records persist with expiry metadata intact
* No implicit restoration for prior scope

**Condition C (Renewal After Destruction):**

* Prior authority remains VOID with destruction metadata preserved
* Renewal references prior AuthorityID (existence validated only)
* New authority is ACTIVE (until expiry)
* No state change of VOID authority due to renewal

**Condition D (Renewal Under Ongoing Conflict):**

* Conflict is binding at time of the decisive action evaluation (both relevant authorities ACTIVE and conflicting)
* After renewal, action crafted to detect freshness-priority is refused
* No execution occurs that would require “newest wins”

---

### G12.2 — Global Success Criteria

Approved global criteria:

* determinism and bit-perfect replay
* monotonic epoch progression
* finite expiry enforced
* no kernel-initiated renewal
* no implicit ordering (including via metadata)
* no implicit resolution by time
* complete responsibility trace (expiry + destruction + renewal)
* no AuthorityID reuse
* all required artifacts present

---

## Final Freeze Clause

With these answers, preregistration may freeze. Any further ambiguity discovered during implementation must be classified as:

```
INVALID_RUN / UNSPECIFIED_MECHANISM
```

No additional “clarifications” may be introduced post-freeze without version bump.

---

**End of Final Binding Clarifications (Second Follow-Up) — Stage VIII-3 v0.1**
