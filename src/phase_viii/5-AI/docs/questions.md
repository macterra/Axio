# Stage VIII-5 Implementation Questions

**Date:** 2026-02-04
**Implementor:** Claude (Opus 4.5)

---

## Critical Clarifications Needed

### Q1: Content-Addressed AuthorityID — Breaking Change from Prior Stages?

The spec mandates:
> "AuthorityID values are content-addressed... deterministically derived from the full AuthorityRecord using a cryptographic hash function"

However, prior stages (VIII-1 through VIII-4) use **user-assigned/AIE-assigned AuthorityIDs** (explicitly noted in VIII-1 structures.py: "AuthorityID is opaque (AIE-assigned), not derived from content"). AST Spec v0.2 §2.1 also says AuthorityID is "opaque, globally unique" without mandating content-addressing.

**Questions:**
1. Is this a **new invariant for VIII-5 only** (for externally injected authorities), or does it apply retroactively to all prior stages?
2. If VIII-5-only: How do we distinguish "injected" authorities (content-addressed) from "internal" authorities (AIE-assigned)? The lineage `VOID` marker?
3. If retroactive: This would invalidate all prior stage implementations. Is that intended?

**My reading of the spec:** Content-addressed IDs apply **only to externally injected authorities** (those with `ParentID := VOID`). Internally created authorities (via VIII-4 CREATE_AUTHORITY) retain AIE-assigned IDs with lineage chains. The VIII-5 spec uses "Authority Identity Derivation Invariant (Binding)" which could be VIII-5-specific binding rather than inherited. Please confirm.

---

### Q2: AuthorityID Hash Function Specification

The spec references "AST Spec v0.2" for the hash function but doesn't specify it directly.

**Questions:**
1. What hash function should be used? SHA-256?
2. What fields are included in the hash input? The full AuthorityRecord or a subset?
3. Is there a canonical serialization format for hashing (like AST Appendix C for JSON)?

**Proposed default:** `SHA256(canonical_json(AuthorityRecord_without_authority_id))` truncated or formatted as needed for the ID format.

---

### Q3: VOID Lineage Sentinel — Schema Details

The spec says injected authorities must specify `ParentID := VOID`.

**Questions:**
1. Is `VOID` a string literal `"VOID"`, a null value, or a special constant?
2. Does this field exist in the current AuthorityRecord schema, or must it be added?
3. Is `ParentID` the same as the `lineage` field used in VIII-4's CREATE_AUTHORITY? (VIII-4 used `lineage: Optional[str]` which could be `None` for fresh creates.)

**Context:** VIII-3 structures.py has `AuthorityStatus.VOID = "VOID"` but that's a status, not a lineage sentinel.

---

### Q4: Relationship Between Injection and CREATE_AUTHORITY

VIII-4 introduced `CREATE_AUTHORITY` governance action. VIII-5 introduces external injection.

**Questions:**
1. Are these **mutually exclusive** pathways for new authorities?
   - `CREATE_AUTHORITY`: internal, requires admitting authority, subject to non-amplification
   - `AuthorityInjectionEvent`: external, no authorization required, VOID lineage
2. Can both coexist in the same kernel?
3. If injection creates authorities with VOID lineage, can those authorities later use CREATE_AUTHORITY to create children (with lineage pointing back)?

**My assumption:** Both pathways coexist. Injected authorities (VOID lineage) are the only way to introduce "root" authorities. Created authorities always have lineage to their creator.

---

### Q5: "Injection Source Identifier (Opaque)" — What Is This?

The spec requires preserving "injection source identifier (opaque)" in traces.

**Questions:**
1. Is this a new field on the injection event?
2. What does it represent? (A key from the AIE? A hash? An external system reference?)
3. What is its format? String? Bytes?
4. Is it used in any kernel logic, or purely for tracing?

**Proposed interpretation:** A string field on `AuthorityInjectionEvent` that the kernel stores but never interprets (opaque token for audit purposes).

---

### Q6: Duplicate Injection Idempotency

The spec says "Duplicate injections are idempotent" due to content-addressing.

**Questions:**
1. If the same AuthorityRecord is injected twice, should the second injection:
   - Be silently ignored (no output)?
   - Emit `AUTHORITY_INJECTED` again (idempotent but traced)?
   - Emit a refusal?
2. Is "duplicate" determined purely by content-addressed ID matching?
3. What if the same content is injected at different epochs?

**My assumption:** Duplicate injection (same content-addressed ID already exists) is silently idempotent — no new state, no refusal, possibly a trace note. The authority's activation epoch is unchanged.

---

### Q7: Injection Budget/Cost

The spec mentions "gas/budget sufficiency for atomic completion" but doesn't specify injection costs.

**Questions:**
1. What is the instruction cost for processing an injection event?
2. Is it the same as CREATE_AUTHORITY cost? Less (no non-amplification check)?
3. What specific checks consume instructions during injection?

**Proposed default:** Injection cost = `C_LOOKUP + C_STATE_WRITE` (similar to injection in prior stages).

---

### Q8: `AUTHORITY_INJECTED` vs `AUTHORITY_PENDING` Output

The spec lists both `AUTHORITY_INJECTED` and `AUTHORITY_PENDING` as valid outputs.

**Questions:**
1. Does injection emit BOTH (first INJECTED, then PENDING)?
2. Or is AUTHORITY_INJECTED the output and PENDING is just the state?
3. Does the kernel ever emit `AUTHORITY_PENDING` as a standalone output?

**Context:** Prior stages used `AUTHORITY_INJECTED` as an internal trace, not an external output.

---

### Q9: Condition Details Missing

The spec lists Conditions A-F but marks them "(unchanged)" or provides minimal detail.

**Questions:**
1. Can you provide the detailed setups for:
   - **Condition A:** Injection into empty authority state
   - **Condition B:** Injection into active conflict
   - **Condition C:** Competing injections
   - **Condition D:** Injection after authority destruction
   - **Condition E:** Injection under load
   - **Condition F:** Injection flooding attempt
2. What are the specific success criteria for each?
3. Are there expected output sequences?

---

### Q10: Success Criteria Enumeration

The spec says "Success Criteria (VIII-5 PASS) *(unchanged)*" but doesn't enumerate them.

**Questions:**
1. What are the numbered success criteria (like VIII-4's 21 criteria)?
2. Which criteria map to which conditions?
3. What invariant checks must be verified globally?

---

## Minor Clarifications

### Q11: Kernel Reuse Strategy

Should VIII-5 kernel be:
1. A new kernel built from scratch?
2. An extension of VIII-4's GTKernel?
3. The VIII-4 kernel with injection support added?

**My preference:** Extend VIII-4's kernel to add injection support, inheriting all governance machinery.

---

### Q12: Activation at "Next Epoch Boundary"

If an authority is injected in epoch N and epoch advancement to N+1 occurs in the same batch:
1. Does the injected authority become ACTIVE in that same batch?
2. Or must it wait for the *next* epoch advancement (N+2)?

**My assumption:** Same-batch epoch advancement activates pending authorities, so injection in epoch N + advancement to N+1 in same batch = ACTIVE at end of batch. This matches VIII-4 behavior.

---

### Q13: Conflict Persistence Under Injection

The spec says injection "must not erase or downgrade existing conflict records."

**Questions:**
1. Can injected authority *join* an existing conflict if it covers the same scope and has conflicting AAV?
2. Does this happen at activation time (when it becomes ACTIVE) or at injection time?
3. If it joins, is this considered "expanding" the conflict (allowed) vs "modifying" it (forbidden)?

**My assumption:** Injected authorities can join conflicts at activation time when they become ACTIVE and are evaluated for scope overlap. This is "expanding" (allowed).

---

## Summary of Blocking Questions

The following must be resolved before implementation can proceed:

1. **Q1:** Content-addressed ID scope (VIII-5 only vs all authorities)
2. **Q3:** VOID lineage field specification
3. **Q9:** Condition details
4. **Q10:** Success criteria enumeration

The remaining questions can likely be resolved with reasonable defaults during implementation.

---

## Followup Questions (Post-Answer)

Based on the answers provided, the following implementation clarifications are needed:

### F1: ParentID Field — Schema Alignment

The answer says `ParentID` "already exists" in AuthorityRecord, but VIII-4's schema uses `lineage` field in CREATE_AUTHORITY params (not on AuthorityRecord itself). The AuthorityRecord has `creation_metadata.lineage`.

**Clarification needed:**
1. Should we add `parent_id` as a top-level field on AuthorityRecord?
2. Or should we use `creation_metadata.lineage` and set it to `"VOID"` for injections?
3. Or is `ParentID` a conceptual reference to whatever field stores ancestry?

**Proposed resolution:** Add `parent_id: Optional[str]` to AuthorityRecord. For VIII-4 created authorities, this is the creating authority's ID. For VIII-5 injected authorities, this is `"VOID"`.

---

### F2: Content-Addressed ID — Which Fields Excluded?

The answer says hash input is "entire AuthorityRecord excluding AuthorityID."

**Clarification needed:**
1. Is `parent_id` included in the hash? (If so, all injected authorities would include "VOID" in their hash)
2. Is `status` included? (Injected authorities start PENDING)
3. Is `start_epoch` included? (Same content injected at different epochs would have different IDs?)
4. Are creation/destruction metadata fields included?

**Proposed resolution:** Hash includes: `holder_id`, `resource_scope`, `aav`, `expiry_epoch`. Excludes: `authority_id`, `status`, `start_epoch`, `parent_id`, metadata fields. This makes the ID purely about "what capability" rather than "when/how created."

---

### F3: C_HASH Constant

The answer introduces `C_HASH` as a new instruction cost component.

**Clarification needed:**
1. What value should `C_HASH` have?
2. Is this a new constant to add to structures.py?

**Proposed default:** `C_HASH = 2` (similar to C_AST_RULE complexity).

---

### F4: AUTHORITY_PENDING Output — When Emitted?

The answer says to emit `AUTHORITY_PENDING` after `AUTHORITY_INJECTED` for new injections.

**Clarification needed:**
1. Is `AUTHORITY_PENDING` a new output type to add?
2. VIII-4 didn't emit this output — created authorities went straight to PENDING state without a dedicated output.
3. Should VIII-4's CREATE_AUTHORITY also emit `AUTHORITY_PENDING`, or is this VIII-5-only?

**Proposed resolution:** Add `AUTHORITY_PENDING` as output type. Emit for both injection and CREATE_AUTHORITY when authority enters PENDING state.

---

### F5: Duplicate Injection — Same Content, Different Epochs

The answer says "Epoch does not matter" for duplicate detection.

**Clarification needed:**
1. If `start_epoch` is excluded from the hash (per F2), same content at different epochs = same AuthorityID. Is this intended?
2. If the same authority content is injected at epoch 5 and epoch 10, what happens?
   - First injection: PENDING at epoch 5, ACTIVE at epoch 6
   - Second injection: Idempotent (no state change)?
3. Can you inject content that matches an already-ACTIVE authority? (Still idempotent?)

**My assumption:** Yes, idempotent regardless of authority's current status. The authority exists, so duplicate injection just emits `AUTHORITY_INJECTED` with no state change.

---

### F6: Source Identifier — Required or Optional?

**Clarification needed:**
1. Is `source_id` a required field on `AuthorityInjectionEvent`?
2. Can it be empty/null, or must it always have a value?

**Proposed default:** Required non-empty string. If external source is unknown, use a sentinel like `"UNKNOWN"` or a hash of the injection event itself.

---

**End of Questions — Stage VIII-5 v0.1**
