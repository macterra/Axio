# Stage VIII-2: Destructive Conflict Resolution (Timeless)
## Implementation Questions

**Date:** 2026-02-02
**Spec Version:** VIII-2 v0.1

---

## 1. Authority Configuration

**Q1.1:** The spec says two authorities are injected with "mutually exclusive admissibility profiles" where one permits and one denies the contested action. How is this represented? Does each AuthorityRecord have an explicit `admit: true/false` field, or is denial implicit via conflict?

**Q1.2:** If one authority permits and one denies, is the conflict still detected via overlapping scope (as in VIII-1), or is there a new conflict detection mechanism based on the permit/deny asymmetry?

**Q1.3:** What are the canonical AuthorityIDs and HolderIDs for VIII-2? Do we reuse `AUTH_A`, `AUTH_B`, `HOLDER_A`, `HOLDER_B` from VIII-1?

---

## 2. Destruction Authorization

**Q2.1:** What is the exact structure of a `DestructionAuthorizationRequest`? Required fields?

**Q2.2:** The spec says destruction authorization must be "externally specified (via AIE or preregistered harness)". Which source do we use for VIII-2? AIE injection or harness event?

**Q2.3:** Is the destruction authorization a separate event type processed by the kernel, or a parameter attached to an action request?

**Q2.4:** What nonce/epoch scheme applies to destruction authorization events?

---

## 3. Destruction Mechanics

**Q3.1:** When an authority transitions to `VOID`, does the record remain in `AuthorityState.authorities` with `status: VOID`, or is it moved to a separate registry?

**Q3.2:** What destruction metadata must be preserved for a voided authority? The spec mentions "destruction metadata, authorizing source, motivating conflict identifier."

**Q3.3:** Is there a new `DestructionRecord` structure, or is metadata stored on the voided AuthorityRecord itself?

---

## 4. Conflict and Admissibility

**Q4.1:** After destroying the denying authority, how does admissibility re-evaluation work? Does the conflict record get resolved/closed, or does it remain but no longer block?

**Q4.2:** If both authorities are destroyed (Condition B), what happens to the conflict record? Does it close, or persist in an orphaned state?

**Q4.3:** After destruction, does the kernel check for remaining conflicts before allowing execution, or does it just check the destroyed authority no longer blocks?

---

## 5. Condition Execution

**Q5.1:** The spec defines Conditions A, B, C. Are these separate runs, or phases within a single run?

**Q5.2:** For Condition A (destroy one), which authority is destroyed—the one that denies or the one that permits?

**Q5.3:** For Condition C (no destruction), is this essentially a replay of VIII-1 behavior (deadlock persists)?

**Q5.4:** Is there a specific action request that must succeed after destruction in Condition A, or is admissibility restoration sufficient?

---

## 6. Outputs and Events

**Q6.1:** The spec lists allowed outputs: `AUTHORITY_DESTROYED`, `ACTION_EXECUTED`, `DEADLOCK_PERSISTED`, `DESTRUCTION_REFUSED`. What are the conditions for `DESTRUCTION_REFUSED`?

**Q6.2:** Is `DEADLOCK_PERSISTED` a new event distinct from VIII-1's `DEADLOCK_DECLARED`?

**Q6.3:** Should we emit `CONFLICT_RESOLVED` when destruction removes the blocking authority?

**Q6.4:** What is the event sequence for Condition A? Injection → Conflict → Destruction → Re-evaluation → Execution?

---

## 7. Responsibility Trace

**Q7.1:** What is the "deterministic, externally supplied token uniquely bound to the contested admissibility failure"? Is this the conflict ID (e.g., `C:0001`)?

**Q7.2:** How is the "irreversible linkage between authorization and destruction" implemented? Hash chain? Explicit reference in destruction event?

---

## 8. Kernel State

**Q8.1:** After destruction resolves the conflict, does the kernel exit `STATE_DEADLOCK` or was it never in deadlock (since destruction happens before deadlock would be declared)?

**Q8.2:** What is the final kernel state for each condition?
- Condition A: `STATE_OPERATIONAL`? `STATE_RESOLVED`?
- Condition B: `STATE_DEADLOCK`?
- Condition C: `STATE_DEADLOCK`?

---

## 9. Reuse from VIII-1

**Q9.1:** Can we reuse the VIII-1 kernel, structures, and harness as a base, extending with destruction logic?

**Q9.2:** Do we share the same logging infrastructure and hash chain?

---

## 10. Classification Codes

**Q10.1:** Confirm the pass classification is exactly `VIII2_PASS / DESTRUCTIVE_RESOLUTION_POSSIBLE`?

**Q10.2:** For `INVALID_RUN` codes, should they use the `VIII2_` prefix or remain bare `INVALID_RUN`?

---

## 11. Test Matrix

**Q11.1:** Do all three conditions (A, B, C) need to pass for `VIII2_PASS`, or is each condition a separate classification target?

**Q11.2:** Is there a specific run order for the conditions?

---

## 12. Permit/Deny Semantics

**Q12.1:** How exactly does one authority "permit" and another "deny" an action when both have identical scope `[["R0000", "OP0"]]`? Is there a new field like `actionPolicy: PERMIT | DENY`?

**Q12.2:** If the permitting authority is destroyed, does the denying authority's denial cause the action to be refused (different from conflict)?

---

## Follow-Up Questions

### F1. AST Admissibility Representation

**F1.1:** In VIII-1, both authorities had `PermittedTransformationSet: []` (empty). For VIII-2, how do we configure:
- The **permitting authority** to admit the action?
- The **denying authority** to deny the action?

Is `PermittedTransformationSet` the mechanism, or is there a separate `admittedActions` / `actionScope` field?

**F1.2:** What is the exact contested action/transformation that AUTH_A permits and AUTH_B denies? Is this a specific `transformationType` like `"EXECUTE_OP0"` that must appear in one authority's transformation set but not the other?

---

### F2. Conflict Detection Trigger

**F2.1:** In VIII-1, conflict was detected when two ACTIVE authorities bound the same scope. In VIII-2, you say conflict is detected when "AST admissibility evaluations disagree." Does this mean:
- (a) Conflict is still registered at scope-overlap detection time (injection), OR
- (b) Conflict is only registered when an action is requested and admissibility diverges?

**F2.2:** If (b), is conflict registered on the first contested action request, or during admissibility re-evaluation after destruction?

---

### F3. Condition A Event Sequence Detail

**F3.1:** Your canonical sequence (Q6.4) shows "Candidate action proposed" before "Conflict registered." Does this mean:
- The action request triggers conflict detection (not injection)?
- The action is refused initially (like VIII-1), THEN destruction occurs?

**F3.2:** After destruction in Condition A, is the SAME action request retried, or must a NEW action request be submitted?

---

### F4. VOID Authority Behavior

**F4.1:** When a VOID authority is queried for admissibility, does it:
- Return `false` (explicit denial)?
- Return `null` / not-applicable (no longer participates)?
- Throw an error?

**F4.2:** Can a VOID authority be the target of a second destruction authorization (which would be refused)?

---

### F5. Deadlock Entry Timing

**F5.1:** For Condition A, at what point is `DEADLOCK_DECLARED` emitted?
- After the initial conflict + action refusal (before destruction)?
- Never (destruction preempts deadlock)?

**F5.2:** If deadlock is entered before destruction, is there an explicit `DEADLOCK_EXITED` event, or does `STATE_OPERATIONAL` simply replace `STATE_DEADLOCK` silently?

---

### F6. Destruction Authorization Timing

**F6.1:** When in the event sequence is the `DestructionAuthorizationRequest` injected?
- After conflict registration but before deadlock?
- After deadlock is declared?
- At any point (harness decides)?

**F6.2:** Is there a required ordering: conflict must exist before destruction can be authorized?

---

### F7. Condition B/C Clarifications

**F7.1:** For Condition B (destroy both), is this:
- Two separate `DestructionAuthorizationRequest` events (one per authority)?
- A single request with `targetAuthorityIDs: ["ALL"]`?

**F7.2:** For Condition C, are any events injected beyond authority injection and action requests? Or is it purely "no destruction event = deadlock persists"?

---

### F8. Action Execution Details

**F8.1:** When the action executes in Condition A, what is the output event type? `ACTION_EXECUTED`?

**F8.2:** Does action execution require any state change beyond logging the event? (No actual side effects, just proof of admissibility restoration?)

---

**End of Questions**
