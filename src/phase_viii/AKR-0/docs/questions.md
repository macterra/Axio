# AKR-0 Implementation Questions

**Project:** AKR-0 v0.1 — Authority Kernel Runtime Calibration
**Phase:** VIII — Governance Stress Architecture (GSA-PoC)
**Date:** 2026-01-18
**Status:** Pre-implementation clarification

---

## Questions Requiring Resolution Before Implementation

### Q1. Execution Harness Action Generation

The instructions specify a three-layer architecture where the Execution Harness generates synthetic traffic (action requests, epoch ticks, transformation requests).

**Question:** What action types should the harness generate? The spec mentions `(ResourceID, Operation)` tuples but does not enumerate the operation vocabulary. Should I define a minimal fixed set (e.g., `READ`, `WRITE`, `DELETE`, `EXECUTE`) or is there a canonical operation set expected?

---

### Q2. Address Book Definition

AIE v0.1 §7 specifies a fixed Address Book of HolderIDs.

**Question:** How many HolderIDs should populate the Address Book for AKR-0? Is there a target cardinality (e.g., 10, 100, 1000)? Should HolderIDs be opaque strings (e.g., `H001`, `H002`) or have semantic structure?

---

### Q3. Active Scope Pool Size and Collision Probability

AIE v0.1 §8 requires declaration of:
- Active Scope Pool size
- Collision probability $P_c \geq 0.01$

**Question:** What scope pool cardinality should I target? The spec says $P_c$ must be declared but not how to calculate it from pool size. Should I:
1. Fix pool size and derive $P_c$ empirically from actual collisions?
2. Target a specific $P_c$ and size the pool accordingly?

---

### Q4. Instruction Budget (Gas) Magnitude

AKR-spec §Mechanism 7 requires a deterministic instruction budget.

**Question:** What order of magnitude should the gas budget be? The spec forbids wall-clock limits but doesn't specify whether this is 10^3, 10^6, or 10^9 logical instructions per action evaluation. Is there a reference budget from prior work?

---

### Q5. Epoch Advancement Rule

The spec mentions epoch ticks as inputs but doesn't specify advancement semantics.

**Question:** Should epochs advance:
1. At fixed intervals (every N inputs)?
2. Based on explicit EPOCH_TICK inputs from the harness?
3. After authority state changes?

And: Should epoch advancement cause bulk expiry evaluation, or is expiry checked lazily per-action?

---

### Q6. Canonical Ordering Algorithm

AKR-spec §Mechanism 2 requires canonical input ordering but references AST Appendix C for JSON canonicalization only.

**Question:** When multiple inputs arrive in the same "batch" (simulated simultaneity), what is the ordering rule?
1. By canonical JSON hash (lexicographic)?
2. By input type priority (e.g., transformations before actions)?
3. By arrival nonce from harness?

---

### Q7. Conflict Registration vs. Conflict Detection

AST-spec distinguishes:
- `REGISTER_CONFLICT` transformation (explicit)
- Conflict detection during admissibility

**Question:** Does the kernel:
1. Detect conflicts automatically from overlapping scopes and register them?
2. Only recognize conflicts when explicitly registered via AIE-issued transformation?
3. Both (detect structurally, but also honor explicit registrations)?

---

### Q8. Transformation Request Source

The spec says authority creation comes only from AIE (open-system declaration).

**Question:** What about other transformations (Suspend, Resume, Revoke, Narrow Scope, Register Conflict, Resolve Conflict)?
1. All transformations come only from AIE?
2. Some transformations can originate from the kernel (e.g., auto-expiry)?
3. Some transformations can originate from execution harness as test inputs?

---

### Q9. Deadlock Detection Trigger

AST-spec §5 defines three deadlock types (Conflict, Governance, Entropic Collapse).

**Question:** When is deadlock detection triggered?
1. On every action evaluation?
2. On explicit DETECT_DEADLOCK input?
3. When no action is admissible for N consecutive attempts?

And: Should entropic collapse have a threshold (e.g., <5% of scopes have active authorities)?

---

### Q10. Run Configuration — Action Count

The instructions mention Conditions A, B, C but don't specify run sizes.

**Question:** How many actions should each condition test?
- Is there a minimum (e.g., 1000 actions per condition)?
- Should runs be sized by action count, epoch count, or time budget?
- Should I target statistical power for any specific effect size?

---

### Q11. Seeds and Initial State

AKR-spec preregistration checklist requires "seeds and initial state hashes."

**Question:**
1. How many distinct seeds per condition?
2. Should initial state be empty (no authorities) or seeded with baseline authorities?
3. For Condition A (valid authority), how many authorities should exist at epoch 0?

---

### Q12. Transformation Whitelist — Is EXPIRE Automatic?

AST-spec §4.5 specifies EXPIRE as a lawful transformation.

**Question:** Is expiry:
1. An automatic kernel action when `currentEpoch > authority.expiry`?
2. A transformation that must be explicitly issued by AIE?
3. Either (kernel can auto-expire, AIE can also force-expire)?

If automatic, does it require logging as a transformation?

---

### Q13. Suspension Semantics

AKR-spec mentions "suspension" multiple times but AST-spec only defines SUSPEND/RESUME as transformations.

**Question:** When the kernel suspends (not suspends an authority, but suspends execution):
1. Is SUSPENSION_ENTERED recoverable within the same run?
2. Or does suspension terminate the run as a distinct outcome?
3. What triggers kernel suspension vs. action refusal?

---

### Q14. Logging Schema — Pre-ordering vs. Post-ordering

AKR-spec §Instrumentation requires logging "all inputs (pre- and post-ordering)."

**Question:** Should logs capture:
1. Raw input sequence from harness (pre-ordering) AND canonical sequence (post-ordering)?
2. Or just the canonical sequence with a derivation reference?

What log format — JSON lines, structured binary, or append-only file?

---

### Q15. Replay Protocol

AKR-spec requires bit-perfect replay.

**Question:**
1. Should replay be implemented as a separate harness mode?
2. Or as a verification pass that loads logs and re-executes?
3. What is the comparison granularity — final state hash only, or per-action hash chain?

---

## Summary

15 questions identified requiring clarification before implementation can begin. These span:

| Category | Questions |
|----------|-----------|
| Input definition | Q1, Q2, Q3 |
| Execution semantics | Q4, Q5, Q6, Q7, Q8, Q9, Q12, Q13 |
| Run configuration | Q10, Q11 |
| Instrumentation | Q14, Q15 |

---

**Q1–Q15 resolved in [answers.md](answers.md).**

---

## Follow-up Questions (Post-Resolution)

### Q16. SYSTEM_AUTHORITY Identity and Representation

Q7 and Q8 answers introduce `SYSTEM_AUTHORITY` as the attribution source for auto-registered conflicts and auto-expiry.

**Question:** How should `SYSTEM_AUTHORITY` be represented?
1. A reserved HolderID outside the Address Book (e.g., `SYSTEM`)?
2. A distinguished AuthorityID with special semantics?
3. Should it have its own Authority Record, or is it implicit?

---

### Q17. Conflict Density for Condition C

Q11 specifies Condition C injects `n=50` authorities per epoch with "deliberate conflict density."

**Question:** What is the target conflict density for Condition C?
1. Should the harness guarantee a minimum percentage of injected authorities have overlapping scopes (e.g., ≥30%)?
2. Or should injection be purely random from the scope pool, relying on the higher `n` to produce natural collisions?
3. If deliberate, what algorithm determines scope overlap?

---

### Q18. PermittedTransformationSet Structure

Q8 references that transformation requests require the requester to have an ACTIVE authority with `PermittedTransformationSet` binding the transformation.

**Question:** Where is `PermittedTransformationSet` defined in the Authority Record schema?
1. Is it an additional field on each Authority Record?
2. Is it derived from scope (e.g., authorities on `(Ri, WRITE)` can transform authorities on `(Ri, READ)`)?
3. Or is there a separate meta-authority structure for governance permissions?

---

### Q19. Conflict Record Structure

Q7 says conflict registration creates a "deterministic conflict record."

**Question:** What fields comprise a conflict record?
1. Just the pair of conflicting AuthorityIDs?
2. The conflicting scope element(s)?
3. Epoch of detection, conflict type, etc.?

And: Where are conflicts stored — in each Authority Record's `ConflictSet`, or in a separate global conflict registry?

---

### Q20. Harness Seeding — PRNG Algorithm

Q11 specifies fixed integer seeds `{11, 22, 33, 44, 55}`.

**Question:** What PRNG algorithm should the harness use for deterministic traffic generation?
1. A specific standard (e.g., PCG, Mersenne Twister, xorshift)?
2. Or is the algorithm left to implementation as long as it's declared in preregistration?

---

### Q21. TransformationRequest Input Format

Q8 says Suspend/Resume/Revoke/Narrow/Resolve Conflict may originate as TransformationRequest inputs from the harness.

**Question:** What is the canonical schema for a TransformationRequest event?
1. `{type: "TransformationRequest", transformation: <type>, targetAuthorityId: ..., requesterId: ...}`?
2. Does it need a signature or proof of requester authority?
3. How does the kernel validate that the requester has permissible transformation authority?

---

### Q22. Gas Counting — What Operations Cost Gas?

Q4 defines gas budgets but not the cost model.

**Question:** What operations consume gas, and at what cost?
1. Flat cost per admissibility check?
2. Linear in number of authorities scanned?
3. Hash operations, comparisons, set membership — each with distinct costs?

Or: Is this left to implementation as long as it's deterministic and declared?

---

### Q23. Replay Failure Classification

Q15 says replay checks per-event state hash, output, and hash chain.

**Question:** If replay diverges, what classification is emitted?
1. `INVALID_RUN / NONDETERMINISTIC_EXECUTION` (as in AKR-spec)?
2. Or a distinct `REPLAY_FAIL / <reason>` taxonomy?
3. Should divergence report the first divergent event index?

---

## Summary (Updated)

| Category | Original Questions | Follow-up Questions |
|----------|-------------------|---------------------|
| Input definition | Q1, Q2, Q3 | Q17, Q20 |
| Execution semantics | Q4, Q5, Q6, Q7, Q8, Q9, Q12, Q13 | Q16, Q18, Q19, Q21, Q22 |
| Run configuration | Q10, Q11 | — |
| Instrumentation | Q14, Q15 | Q23 |

---

**Q16–Q23 resolved in [answers.md](answers.md).**

---

## Follow-up Questions (Round 2)

### Q24. Authority Record Full Schema

Combining Q18 (PermittedTransformationSet) and Q19 (ConflictSet), the Authority Record now has more fields than originally shown in AST Appendix C.

**Question:** What is the complete canonical Authority Record schema for AKR-0? Please confirm or correct:
```json
{
  "authorityId": "<opaque>",
  "holderId": "<HolderID>",
  "scope": [["R0000", "READ"]],
  "status": "ACTIVE|SUSPENDED|REVOKED|EXPIRED",
  "creationEpoch": <int>,
  "expiryEpoch": <int|null>,
  "permittedTransformationSet": ["SUSPEND_AUTHORITY", ...],
  "conflictSet": ["C:...", ...]
}
```

---

### Q25. AuthorityID Generation Rule

Q19 shows `conflictId` uses `sha256(canonical_json(...))`.

**Question:** How are AuthorityIDs generated for new authorities injected by AIE?
1. Deterministic from content: `"A:" + sha256(canonical_json(record_without_id))`?
2. Sequential counter: `"A0001"`, `"A0002"`, ...?
3. Harness-supplied opaque string?

---

### Q26. Scope Element Representation — Sorted Within Record

AST Appendix C shows scope as a sorted array. Q3 answer says each authority binds exactly one atomic scope element (scope size = 1).

**Question:** For scope size = 1, should the scope field be:
1. `"scope": [["R0123", "READ"]]` (array of one tuple)?
2. `"scope": ["R0123", "READ"]` (bare tuple)?

Confirming canonical form for hash consistency.

---

### Q27. Authority State Full Schema

Q19 adds `conflicts` array to Authority State.

**Question:** What is the complete Authority State schema?
```json
{
  "stateId": "<hash>",
  "currentEpoch": <int>,
  "authorities": [...],
  "conflicts": [...]
}
```
Are there additional fields (e.g., `gasConsumed`, `eventIndex`)?

---

### Q28. NARROW_SCOPE Semantics

Q18 lists `NARROW_SCOPE` as a permitted transformation.

**Question:** How does NARROW_SCOPE work with scope size = 1?
1. Narrowing a single-element scope to empty → equivalent to REVOKE?
2. Is NARROW_SCOPE unused in AKR-0 baseline (since scope is already atomic)?
3. Or should scope size > 1 be supported for NARROW_SCOPE testing?

---

### Q29. RESOLVE_CONFLICT Mechanics

AST-spec says conflict resolution is "destructive only."

**Question:** What does destructive resolution mean concretely?
1. All conflicting authorities are REVOKED?
2. All but one are REVOKED (winner selection)?
3. The ConflictRecord status changes to RESOLVED but authorities remain?

And: Who can issue RESOLVE_CONFLICT — only holders of conflicting authorities, or any holder with the transformation permission?

---

### Q30. Event Type Enumeration

The harness generates multiple event types.

**Question:** What is the complete enumeration of event types for canonical ordering?
1. `EPOCH_TICK`
2. `ActionRequest`
3. `TransformationRequest`
4. `AuthorityInjection` (from AIE)

Are there others? Is `AuthorityInjection` a distinct event type or bundled with `EPOCH_TICK`?

---

### Q31. Condition B — What Does Harness Inject?

Q11 says Condition B injects `n=0` authorities always.

**Question:** Does Condition B still inject:
1. `EPOCH_TICK` events?
2. `ActionRequest` events (expecting all refusals)?
3. `TransformationRequest` events?

Or is it purely action requests against an empty authority state?

---

## Summary (Round 2)

| Category | Questions |
|----------|-----------|
| Schema definition | Q24, Q25, Q26, Q27 |
| Transformation semantics | Q28, Q29 |
| Event structure | Q30, Q31 |

---

**Q24–Q31 resolved in [answers.md](answers.md).**

---

## Follow-up Questions (Round 3)

### Q32. Origin Reference Content

Q24 introduces `origin` as a required field in Authority Record.

**Question:** What should the `origin` field contain for AIE-injected authorities?
1. A reference to the AIE injection event (e.g., `"AIE:<eventHash>"`)?
2. The seed + epoch + sequence number (e.g., `"S11:E5:N3"`)?
3. Purely opaque placeholder (e.g., `"EXTERNAL"`)?

---

### Q33. AuthorityInjection Event Schema

Q30 confirms `AuthorityInjection` is a distinct event type.

**Question:** What is the canonical schema for an AuthorityInjection event?
```json
{
  "type": "AuthorityInjection",
  "epoch": <int>,
  "eventId": "<opaque>",
  "authority": <AuthorityRecord>
}
```
Is `eventId` required? Is it deterministic like `authorityId`?

---

### Q34. EPOCH_TICK Event Schema

**Question:** What is the canonical schema for an EPOCH_TICK event?
```json
{
  "type": "EPOCH_TICK",
  "targetEpoch": <int>,
  "eventId": "<opaque>"
}
```
Or is it simply `{"type": "EPOCH_TICK", "epoch": <int>}`?

---

### Q35. ActionRequest Event Schema

**Question:** What is the canonical schema for an ActionRequest event?
```json
{
  "type": "ActionRequest",
  "epoch": <int>,
  "requestId": "<opaque>",
  "requesterHolderId": "<HolderID>",
  "action": ["R0123", "READ"]
}
```
Is `requesterHolderId` required (who is attempting the action)?

---

### Q36. PermittedTransformationSet for AIE-Injected Authorities

Q18 defines `permittedTransformationSet` as a field on Authority Records.

**Question:** How does AIE determine what transformations to grant?
1. All authorities get empty set (no governance power)?
2. Random subset from {SUSPEND, RESUME, REVOKE, NARROW, RESOLVE}?
3. Condition-dependent (e.g., Condition C grants RESOLVE_CONFLICT to enable conflict resolution)?

---

### Q37. Deadlock Declaration — Output vs. State Change

Q9 defines deadlock detection triggers.

**Question:** When deadlock is declared:
1. Is `DEADLOCK_DECLARED` purely an output (logged, run continues)?
2. Or does it cause state change (e.g., marking Authority State as deadlocked)?
3. Does the run terminate on deadlock, or continue processing remaining events?

---

### Q38. Gas Exhaustion Mid-Batch

Q4/Q22 define gas budgets per operation type.

**Question:** If gas is exhausted mid-batch (e.g., during the 15th of 20 action evaluations):
1. Are remaining actions in the batch deferred to next epoch?
2. Are they refused immediately?
3. Does the kernel enter SUSPENSION_ENTERED and halt the batch?

---

### Q39. Harness TransformationRequest Generation

Q31 confirms Condition B injects TransformationRequests (expecting failure).

**Question:** For Conditions A and C, what TransformationRequests should the harness generate?
1. Random selection from {SUSPEND, RESUME, REVOKE, RESOLVE_CONFLICT}?
2. Targeted based on current Authority State (e.g., SUSPEND for ACTIVE, RESUME for SUSPENDED)?
3. None (only AIE creates/expires, kernel auto-handles conflicts)?

---

## Summary (Round 3)

| Category | Questions |
|----------|-----------|
| Event schemas | Q33, Q34, Q35 |
| Authority generation | Q32, Q36 |
| Execution semantics | Q37, Q38, Q39 |

---

**Awaiting resolution of Q32–Q39 before implementation.**
