# IX-1 VEWA Implementation Questions

## Clarifications Needed Before Implementation

### 1. Value Declaration Grammar

The spec requires a "value declaration grammar" to be frozen before any run.

**Question**: What is the concrete syntax for declaring a value? The spec says values are "opaque beyond their explicit structural encoding as authority" — should the declaration be a simple JSON structure like:

```json
{
  "value_id": "V001",
  "name": "confidentiality",
  "scope": [{"resource": "FILE:/data/secret.txt", "operation": "READ"}],
  "commitment": "DENY"
}
```

Or is there a different grammar expected?

---

### 2. Value-to-Authority Encoding Rules

The spec requires "bijective encoding" from values to authority artifacts.

**Question**: What are the explicit mapping rules? Specifically:
- How does a value commitment map to the AST v0.2 `aav` field?
- Should values map to ALLOW authorities, DENY authorities, or a new commitment type?
- Is there a 1:1 mapping (one value = one authority artifact) or can a single value produce multiple authorities?

---

### 3. Scope Overlap Definition

The spec states: "Scope overlap exists if and only if identifiers are bit-identical."

**Question**: Does this mean:
- The entire scope array must be identical? OR
- Any single scope entry (resource + operation pair) being identical triggers overlap?

Example: Do these conflict?
- Scope A: `[{resource: "FILE:/a.txt", operation: "READ"}]`
- Scope B: `[{resource: "FILE:/a.txt", operation: "READ"}, {resource: "FILE:/b.txt", operation: "WRITE"}]`

---

### 4. Conflict vs. Contradiction

**Question**: Is "conflict" defined as:
- Same scope + different commitments (e.g., one ALLOW, one DENY)? OR
- Same scope, regardless of commitment type?

If two values both grant ALLOW on the same scope, is that a conflict?

---

### 5. AIE (Authority Injection Endpoint)

The spec mentions "AIE injects exactly two value-derived Authority Records."

**Question**: Should IX-1 reuse the AIE infrastructure from IX-0, or is this a different injection mechanism for value-derived artifacts specifically?

---

### 6. Candidate Action Requests

The spec says the harness provides "Candidate Action Requests."

**Question**: What is the structure of a candidate action request? Is it simply a scope identifier (resource + operation) to test admissibility against?

---

### 7. Conditions D, E, F — Adversarial Tests

These conditions test whether the system correctly **fails** when adversarial inputs are provided.

**Question**: Are these implemented as:
- Fault injection (like IX-0 Conditions D/H), where we deliberately inject the violation and verify it's detected?
- Or as probes where we verify the system *would* fail if such input arrived?

In other words: should the harness attempt to inject priority hints (D), structural bias (E), and meta-authorities (F) — and then classify as FAIL_DETECTED if the system rejects them?

---

### 8. Execution Log Schema

The spec requires logging but doesn't provide a concrete schema.

**Question**: Should I reuse the IX-0 logging schema (ConditionLog, ExecutionLog) with VEWA-specific fields, or design a new schema per the preregistration checklist?

---

### 9. "ACTION_ADMISSIBLE (simulation-only)"

The spec says `ACTION_ADMISSIBLE` is simulation-only and execution is forbidden.

**Question**: Does this mean:
- The output is `ACTION_ADMISSIBLE` but no actual execution occurs (correct for IX-1)?
- Or is there a separate "simulated execution" path that runs but doesn't mutate state?

I assume the former — admissibility is marked, but nothing executes.

---

### 10. Relationship to IX-0 Translation Layer

IX-0 established a Translation Layer (TL) that converts intent to authority artifacts.

**Question**: Does IX-1 use the IX-0 TL to encode values as authority? Or is the Value Encoding Harness (VEH) a distinct component that bypasses the TL?

The spec says VEH must produce "exact AST v0.2 artifacts" — this suggests it could reuse IX-0's canonical serialization and artifact structure, but the encoding logic might be different.

---

## Implementation Plan Pending Answers

Once clarified, I will:

1. Write the preregistration document with frozen sections
2. Implement VEH (Value Encoding Harness)
3. Implement Admissibility & Conflict Probe
4. Implement Conditions A–F tests
5. Implement logging and replay infrastructure
6. Write unit tests for all conditions

---

**Created**: 2026-02-05
**Status**: All questions resolved 2026-02-05 — ready for preregistration

---

## Follow-up Questions (Post-Answers)

### 11. DENY + DENY Conflict Clarification

Answer #4 states: "DENY + DENY → **Conflict** (mutually reinforcing denial still blocks execution)"

**Question**: If two DENY authorities on the same scope both block the action, why is this a "conflict" rather than simply "reinforced denial"?

The action would be refused either way. Is the concern that we cannot distinguish *which* value caused the refusal, violating auditability? Or is there another reason DENY+DENY must be treated as conflict?

---

### 12. Commitment Types Beyond ALLOW/DENY

Answer #2 says value commitments map to ALLOW or DENY.

**Question**: Does IX-1 need to handle AST v0.2's full `aav` vocabulary (READ, WRITE, EXECUTE, DELEGATE, ADMIN), or only the binary ALLOW/DENY commitment type?

If the former: how does a value like "confidentiality" map to a specific aav? Is the operation field in the scope the aav, and commitment is the polarity (ALLOW/DENY)?

---

### 13. Conflict Detection Timing

**Question**: When is conflict detected?
- At value injection (epoch 0), when overlapping scopes are registered?
- At admissibility probe time, when an action request hits conflicting authorities?
- Both?

The spec says conflict must "persist" — does this mean conflict is registered at injection and cached, or computed on-demand per probe?

---

### 14. Scope Atom Canonicalization

For bit-identical matching of scope atoms:

**Question**: Should scope atoms be canonicalized before comparison (sorted keys, no whitespace), or compared as raw JSON strings?

I assume we reuse IX-0's `canonicalize()` function for this.

---

### 15. Adversarial Test Classification

For Conditions D, E, F — the answer says they must "detect and classify as FAIL."

**Question**: Should the classification be:
- `IX1_FAIL / VALUE_AGGREGATION` (meaning IX-1 itself fails), OR
- `FAIL_DETECTED` (meaning the adversarial injection was detected, which is a PASS for that condition, like IX-0's D/H)?

I suspect it's the latter (FAIL_DETECTED = system correctly refused the attack), matching IX-0's adversarial condition semantics.

---

### 16. Authority Artifact Structure for Values

IX-0 artifacts have: `holder`, `scope`, `aav`, `expiry_epoch`, `authority_id`, `created_epoch`, `lineage`, `status`.

**Question**: For value-derived authorities:
- What is `holder`? The value_id, or a designated "value authority holder"?
- What is `lineage`? VOID, or linked to the value declaration?
- What is `status`? Always ACTIVE for IX-1?

---

**Updated**: 2026-02-05
