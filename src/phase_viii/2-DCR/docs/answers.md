# Stage VIII-2 v0.1 — Implementation Clarifications (Authoritative)

These answers are **binding interpretations** of VIII-2 v0.1 for implementation and preregistration.
They do **not** introduce new semantics beyond what VIII-2 already licenses.

---

## 1. Authority Configuration

### Q1.1 — How is “permit vs deny” represented?

**Answer:**
There is **no new `admit: true/false` field**.

Permit/deny is represented **structurally via AST admissibility**, exactly as in AKR-0 and VIII-1.

* Each `AuthorityRecord` defines a **permitted transformation set** under AST Spec v0.2.
* For the contested action:

  * **Permitting authority** → transformation is admissible under AST.
  * **Denying authority** → transformation is not admissible under AST.

There is **no explicit “deny” flag**.
Denial is **absence of permission**, not a semantic veto.

This preserves:

* non-semantic authority,
* reuse of AST unchanged.

---

### Q1.2 — How is conflict detected?

**Answer:**
Conflict detection is **identical to Stage VIII-1**.

Conflict is detected when:

* two ACTIVE authorities bind the same atomic scope element, and
* their AST admissibility evaluations **disagree** for the same candidate action.

There is **no new conflict mechanism**.

Permit/deny asymmetry is discovered **only during admissibility evaluation**, not at injection time.

---

### Q1.3 — Canonical AuthorityIDs / HolderIDs?

**Answer:**
Reuse **exactly** the canonical identifiers from VIII-1 unless preregistered otherwise:

* `AUTH_A`, `AUTH_B`
* `HOLDER_A`, `HOLDER_B`

No semantic meaning is attached to A vs B.

---

## 2. Destruction Authorization

### Q2.1 — Structure of `DestructionAuthorizationRequest`

**Answer (minimal, binding schema):**

```
DestructionAuthorizationRequest {
  targetAuthorityIDs: [AuthorityID] | ["ALL"],
  conflictID: ConflictID,
  authorizerID: ExternalAuthorizerID,
  nonce: DeterministicNonce
}
```

Constraints:

* `targetAuthorityIDs` ∈ { [AUTH_A], [AUTH_B], ["ALL"] }
* `conflictID` must reference an **existing registered conflict**
* `nonce` must be deterministic and preregistered

---

### Q2.2 — Source of destruction authorization?

**Answer:**
**Not AIE.**

Destruction authorization comes from the **external preregistered harness**, not from AIE.

Reason:

* AIE is authority *source* only.
* Destruction authorization is **governance intervention**, even if legitimacy is out of scope.

This separation is intentional.

---

### Q2.3 — Event type or action parameter?

**Answer:**
**Separate event type.**

`DestructionAuthorizationRequest` is its **own input**, processed by the kernel.

It must **never** be attached to an action request.

Attaching it to actions would reintroduce:

* implicit ordering,
* policy coupling.

---

### Q2.4 — Nonce / epoch scheme?

**Answer:**

* Single-epoch system.
* Nonce exists **only for replay determinism and uniqueness**.
* No epoch advancement.
* Nonce must be deterministic under preregistration (e.g., fixed literal or derived hash).

No temporal semantics.

---

## 3. Destruction Mechanics

### Q3.1 — Where does a VOID authority live?

**Answer:**
It remains in `AuthorityState.authorities` **in place**, with:

```
status: VOID
```

No separate registry.

Reason:

* AuthorityID must remain resolvable.
* History must not be laundered.

---

### Q3.2 — Required destruction metadata?

**Answer (minimum):**

* `destroyedAuthorityID`
* `conflictID`
* `authorizerID`
* `nonce`
* `destructionIndex` (monotonic, deterministic)

---

### Q3.3 — New `DestructionRecord` or inline metadata?

**Answer:**
Either is acceptable **if and only if**:

* the linkage between authorization and VOID authority is explicit,
* replay can reconstruct destruction causality bit-perfectly.

Most implementations should store metadata **on the AuthorityRecord itself** to avoid shadow state.

---

## 4. Conflict and Admissibility

### Q4.1 — After destroying the denying authority?

**Answer:**

* Conflict record remains **historically present**.
* Conflict is no longer **blocking** because:

  * only one ACTIVE authority remains,
  * AST admissibility now evaluates cleanly.

No new “conflict resolved” semantic state is introduced.

---

### Q4.2 — After destroying both authorities?

**Answer:**

* Conflict record persists as historical artifact.
* No ACTIVE authority remains.
* Admissibility fails due to **absence of authority**, not conflict.

Deadlock persists lawfully.

---

### Q4.3 — What does kernel check post-destruction?

**Answer:**

1. Recompute admissibility under AST with remaining ACTIVE authorities.
2. Check for **any blocking conflict** among remaining authorities.
3. Execute **only if admissibility is restored**.

No shortcut logic.

---

## 5. Condition Execution

### Q5.1 — Separate runs or phases?

**Answer:**
**Separate runs.**

Each condition (A, B, C) is its **own run** with frozen initial state.

---

### Q5.2 — Which authority is destroyed in Condition A?

**Answer:**
The **denying authority**.

Destroying the permitting authority would **not restore admissibility** and would not test the intended mechanism.

---

### Q5.3 — Is Condition C just VIII-1 replay?

**Answer:**
Behaviorally similar, **ontologically distinct**.

VIII-2 validates that:

* deadlock persists **even when destruction is possible but not authorized**.

This is not redundant.

---

### Q5.4 — Must an action execute in Condition A?

**Answer:**
Yes.

At least **one preregistered candidate action** must execute successfully after destruction.

Admissibility restoration alone is insufficient to demonstrate mechanism correctness.

---

## 6. Outputs and Events

### Q6.1 — When is `DESTRUCTION_REFUSED` emitted?

**Answer:**

* destruction targets nonexistent AuthorityID,
* authority already in `VOID`,
* conflictID invalid or mismatched,
* multiple destruction authorizations detected.

---

### Q6.2 — `DEADLOCK_PERSISTED` vs `DEADLOCK_DECLARED`?

**Answer:**

* `DEADLOCK_DECLARED` — initial entry (VIII-1 semantics).
* `DEADLOCK_PERSISTED` — confirmation that deadlock remains after destruction attempt or non-authorization.

Distinct events.

---

### Q6.3 — Emit `CONFLICT_RESOLVED`?

**Answer:**
**No. Forbidden.**

Conflict resolution is **implicit via destruction**, not a semantic event.

Emitting `CONFLICT_RESOLVED` would reintroduce laundering.

---

### Q6.4 — Event sequence for Condition A?

**Answer (canonical):**

1. Authority injection
2. Candidate action proposed
3. Conflict registered
4. Destruction authorized
5. Authority → `VOID`
6. Admissibility re-evaluated
7. Action executed
8. State continues operationally

---

## 7. Responsibility Trace

### Q7.1 — What is the deterministic token?

**Answer:**
The **ConflictID**.

E.g., `C:0001`.

Must be:

* deterministic,
* preregistered,
* unique per conflict.

---

### Q7.2 — How is irreversible linkage implemented?

**Answer:**

* Destruction event explicitly references:

  * `destroyedAuthorityID`
  * `conflictID`
  * `nonce`
* AuthorityRecord in `VOID` references the destruction event.

No hash-chain requirement, but hash chains are acceptable.

---

## 8. Kernel State

### Q8.1 — Does kernel enter deadlock before destruction?

**Answer:**
Yes.

Deadlock may be entered **before** destruction authorization arrives.

Destruction may then **exit deadlock** in Condition A.

---

### Q8.2 — Final kernel states?

* **Condition A:** `STATE_OPERATIONAL`
* **Condition B:** `STATE_DEADLOCK`
* **Condition C:** `STATE_DEADLOCK`

No new terminal state is introduced.

---

## 9. Reuse from VIII-1

### Q9.1 — Can we reuse VIII-1 kernel?

**Answer:**
Yes.

VIII-2 is **VIII-1 + destruction logic + VOID semantics**.

No rewrite required.

---

### Q9.2 — Same logging and hash chain?

**Answer:**
Yes. Reuse unchanged.

---

## 10. Classification Codes

### Q10.1 — Pass classification?

**Answer:**
Exactly:

```
VIII2_PASS / DESTRUCTIVE_RESOLUTION_POSSIBLE
```

---

### Q10.2 — INVALID_RUN prefix?

**Answer:**
Remain **bare**:

```
INVALID_RUN / <reason>
```

Do not add `VIII2_` prefix.

---

## 11. Test Matrix

### Q11.1 — Do all conditions need to pass?

**Answer:**
Yes.

Stage VIII-2 passes **iff** Conditions A, B, and C all behave as specified.

---

### Q11.2 — Run order?

**Answer:**
No mandated order.
Each run is independent.

---

## 12. Permit / Deny Semantics

### Q12.1 — How permit/deny is expressed?

**Answer:**
Via **AST admissibility only**.

No new `actionPolicy` field is introduced.

---

### Q12.2 — If permitting authority is destroyed?

**Answer:**

* Remaining denying authority blocks action.
* No conflict exists (single authority).
* Action is refused due to denial, not conflict.

This is lawful behavior.

---

## Final Instruction to Implementors

Do not add semantics.
Do not infer intent.
Do not be clever.

If destruction restores admissibility **only when it should**,
and deadlock persists **when it must**,
Stage VIII-2 passes.

Anything else is failure.

---

**End of Stage VIII-2 Implementation Clarifications**


---

# Stage VIII-2 v0.1 — Follow-Up Implementation Clarifications (Binding)

## F1. AST Admissibility Representation

### F1.1 — How do we make one authority permit and the other deny?

**Answer:**
Use **`PermittedTransformationSet`**. There is **no separate** `admittedActions`, `actionScope`, or `admit` field.

Configuration:

* **Permitting authority (AUTH_A):** `PermittedTransformationSet` contains **exactly one** transformation that matches the contested action under AST v0.2.
* **Denying authority (AUTH_B):** `PermittedTransformationSet: []` (empty), meaning it grants **no admissible transformation** for the contested action.

This preserves:

* AST as the sole semantics carrier,
* denial as absence-of-permission,
* structural non-semantic authority records.

---

### F1.2 — What is the exact contested action / transformation?

**Answer:**
Define one canonical transformation for VIII-2:

* `transformationType: "EXECUTE_OP0"`
* bound to the same atomic scope element used in VIII-1: `[["R0000","OP0"]]`

Contested action request must map deterministically to that transformation:

* Candidate Action Request: `ACTION_REQUEST / EXECUTE_OP0` (or equivalent canonical encoding)
* AST compilation yields: `TRANSFORM / EXECUTE_OP0 @ [["R0000","OP0"]]`

Then:

* AUTH_A permits `"EXECUTE_OP0"` for that scope (via its `PermittedTransformationSet`)
* AUTH_B does not.

No other transformation types are allowed in VIII-2 runs.

---

## F2. Conflict Detection Trigger

### F2.1 — Is conflict registered at injection time or on action request?

**Answer:**
**(b) Conflict is registered on action request**, not at injection time.

Injection-time overlap is **necessary but not sufficient** for conflict.
Conflict exists only when two ACTIVE authorities over the same scope yield **divergent admissibility** for a particular candidate transformation.

This is the minimal interpretation consistent with:

* VIII-1 plurality (overlap alone),
* VIII-2 permit/deny non-vacuity.

---

### F2.2 — When exactly is conflict registered?

**Answer:**
Conflict is registered on the **first contested action request** that produces divergent admissibility.

Admissibility re-evaluation after destruction must **not** create a new conflict; it may only:

* confirm conflict is no longer blocking (because one authority is VOID or absent),
* or confirm deadlock persists.

---

## F3. Condition A Event Sequence Detail

### F3.1 — Does the action request trigger conflict detection, then refusal, then destruction?

**Answer:**
Yes.

Canonical behavior in Condition A:

1. authorities injected (overlap present, no conflict yet registered)
2. contested action request arrives (`EXECUTE_OP0`)
3. kernel evaluates admissibility under AST:

   * AUTH_A permits
   * AUTH_B denies (absence of permission)
4. kernel registers conflict for that request (`conflictID`)
5. kernel refuses the action (since admissibility is not coherent under plurality)
6. kernel may enter deadlock (see F5)
7. external destruction authorization arrives
8. destruction executed (AUTH_B → VOID)
9. admissibility re-evaluated
10. action execution proceeds (see F3.2 / F8)

So: **initial refusal is required**. Otherwise you never test “conflict exists first.”

---

### F3.2 — After destruction, do we retry the same request or submit a new one?

**Answer:**
Submit a **NEW** action request.

Reason: replay determinism and clean causality. You do not want an implicit “retry engine” inside the kernel.

Rule:

* First action request is refused (pre-destruction).
* After destruction, the harness submits an **identical second request** (same action type, same scope).
* The second request is evaluated anew and should execute.

This avoids hidden retry semantics.

---

## F4. VOID Authority Behavior

### F4.1 — How does a VOID authority behave if queried for admissibility?

**Answer:**
VOID authorities are **non-participants**.

They return **not-applicable** (conceptually `null`) and must not contribute permit or deny.

Implementation requirement:

* Admissibility evaluation iterates only over `status == ACTIVE`.
* `status == VOID` is ignored in admissibility logic.

VOID is not denial. VOID is **absence from the authority calculus**.

---

### F4.2 — Can VOID be targeted by a second destruction authorization?

**Answer:**
Yes, and it must be refused:

* Output: `DESTRUCTION_REFUSED`
* Reason: target already VOID

This is part of auditability and prevents “double spend” semantics.

---

## F5. Deadlock Entry Timing

### F5.1 — In Condition A, when is `DEADLOCK_DECLARED` emitted?

**Answer:**
After the **initial conflict registration + action refusal**, and **before** destruction authorization is processed.

Rationale: Stage VIII-2 must demonstrate that without authorization, the kernel lawfully deadlocks.

So Condition A sequence includes:

* conflict registered
* action refused
* `DEADLOCK_DECLARED`
* then later destruction allows exit

---

### F5.2 — Is there `DEADLOCK_EXITED`?

**Answer:**
No. Forbidden.

Deadlock exit is reflected by:

* state change to `STATE_OPERATIONAL`
* and the subsequent `ACTION_EXECUTED`

Do not emit a semantic “resolution” event; it invites laundering.
State transition + subsequent lawful execution is sufficient.

---

## F6. Destruction Authorization Timing

### F6.1 — When is the destruction request injected?

**Answer:**
In Condition A, it is injected **after `DEADLOCK_DECLARED`**.

In Condition B, it may be injected after deadlock as well, but the run ends deadlocked.

In Condition C, it is never injected.

This makes the causal structure explicit and comparable across conditions.

---

### F6.2 — Must conflict exist before destruction can be authorized?

**Answer:**
Yes.

If destruction authorization arrives with no registered conflict matching its `conflictID`, it is refused:

* `DESTRUCTION_REFUSED` (conflict not found / mismatch)

This prevents “preemptive destruction” which would bypass the point of VIII-2.

---

## F7. Condition B/C Clarifications

### F7.1 — Condition B destroys both: one request or two?

**Answer:**
A **single** request:

```
targetAuthorityIDs: ["ALL"]
```

Two separate requests would violate the “at most one authorization per run” rule and/or trigger `AMBIGUOUS_DESTRUCTION`.

---

### F7.2 — Condition C: any events beyond injection and action requests?

**Answer:**
No.

Condition C consists of:

* authority injection
* contested action request(s)
* refusal + deadlock persistence
* **no destruction request**

That is the point.

---

## F8. Action Execution Details

### F8.1 — What event is emitted on execution?

**Answer:**
`ACTION_EXECUTED`

Nothing else. No “conflict resolved” event.

---

### F8.2 — Are side effects required?

**Answer:**
No external side effects required.

Execution may be implemented as a **no-op with logged proof**, but it must still go through the full pipeline and emit `ACTION_EXECUTED`.

Minimum requirement:

* execution produces a deterministic trace artifact proving it passed mask/selection/execution under admissibility.

This is about validating the mechanism, not accomplishing work.

---

## Summary Lock-Ins (so Opus can implement without guessing)

1. **Permit vs deny is AST-only** via `PermittedTransformationSet`.
2. Canonical contested transformation is **`EXECUTE_OP0` on `[["R0000","OP0"]]`**.
3. Conflict is registered **on first contested action request**, not at injection.
4. Condition A requires: **refusal + deadlock declared → destruction → new action request → execution**.
5. VOID authorities **do not participate** in admissibility.
6. Destruction authorization requires an existing conflict; destroying both uses `["ALL"]`.
7. No `CONFLICT_RESOLVED`, no `DEADLOCK_EXITED`.

---

