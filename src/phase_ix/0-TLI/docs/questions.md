# IX-0 Implementation Questions

**Date:** 2026-02-04
**From:** Opus (Implementor)
**Re:** Phase IX-0 — Translation Layer Integrity (TLI)

---

## Summary

I've read the spec, instructions, and AST-spec. The IX-0 design is coherent and the constraint set is clear. Below are clarification questions organized by category. These are implementation-blocking or ambiguity-surfacing — not requests to relax constraints.

---

## 1. Intent Representation Format

**Q1.1:** The spec says intent inputs are "opaque to kernel" but must be fed to the Translation Layer. What is the **concrete format** of intent inputs for IX-0?

Options I see:
- (a) Structured schema (JSON with explicit fields like `holder`, `scope`, `aav`, `expiry`)
- (b) Semi-structured (key-value pairs, order-independent)
- (c) Opaque tokens (pre-defined test vectors only)
- (d) Something else

This affects ambiguity detection — the TL can only refuse on ambiguity if ambiguity is structurally detectable in the input format.

**Q1.2:** Is the intent representation format part of the preregistration freeze, or is it a design choice I make and freeze?

---

## 2. Translation Harness Scope

**Q2.1:** The instructions say "a deterministic Translation Harness is preregistered and generates all translation inputs." Does this mean:

- (a) The harness generates **synthetic intent inputs** for all conditions A–F (and G–H if those exist), OR
- (b) The harness is a **test driver** that feeds pre-authored intent inputs and collects outputs?

If (a), I need to design the input generation logic. If (b), I need the pre-authored inputs.

**Q2.2:** The spec mentions Conditions A–F; the instructions mention "Conditions A–H." Are there **8 conditions** (A–H) or **6 conditions** (A–F)? Please confirm the full condition set.

---

## 3. Authorization Binding Mechanism

**Q3.1:** The spec requires authorization to "bind cryptographically or structurally to the exact artifact." What is the **minimum acceptable binding** for IX-0?

Options I see:
- (a) User signs a hash of the canonical artifact (full cryptographic binding)
- (b) User confirms after seeing the artifact, and the system records `(artifact_hash, timestamp, session_id)` (structural binding)
- (c) User types "AUTHORIZE" after artifact display (explicit but weaker)

I lean toward (b) as sufficient for IX-0 since we're testing translation integrity, not deployment-grade key management. Please confirm or redirect.

**Q3.2:** Is there a simulated user, or am I implementing a real interactive authorization step? If simulated, what is the authorization oracle behavior?

---

## 4. Structural Diff Algorithm

**Q4.1:** The spec requires "AST-field-level diff" with "no semantic summaries." Is there a **reference diff format** I should match, or should I design one and freeze it?

Proposed format:
```json
{
  "added": [{"path": "scope[2]", "value": ["R3", "WRITE"]}],
  "removed": [{"path": "expiry", "value": 10}],
  "modified": [{"path": "aav", "old": 1, "new": 3}]
}
```

**Q4.2:** For nested structures (e.g., scope arrays), should the diff be element-level or field-level? Example: if scope changes from `[["R1","READ"]]` to `[["R1","WRITE"]]`, is this:
- (a) One modified element at `scope[0][1]`, OR
- (b) One removed tuple, one added tuple?

---

## 5. Ambiguity Detection Rule

**Q5.1:** The spec says TL must refuse if "more than one AST artifact satisfies declared constraints." This requires a **formal ambiguity rule**.

Is ambiguity defined as:
- (a) Multiple valid completions of partially specified intent, OR
- (b) Multiple interpretations of a well-formed but ambiguous intent field, OR
- (c) Both?

**Q5.2:** Example: If intent specifies `holder: "H1"` and `scope: "R1"` but omits `operation`, is this:
- (a) Ambiguous (refuse), OR
- (b) Schema-invalid (reject with different error)?

I need to distinguish **ambiguity** (multiple valid artifacts) from **incompleteness** (no valid artifact constructible).

---

## 6. Reflection Compatibility (R2)

**Q6.1:** The spec mentions "agent's self-model of commitments." For IX-0, is there an agent with a self-model, or is R2 deferred to later IX stages?

If R2 applies to IX-0:
- What is the self-model representation?
- What constitutes "disagreement" between self-model and artifact?

If R2 is deferred, please confirm I should stub it as `NOT_APPLICABLE_IX0`.

---

## 7. Kernel Integration

**Q7.1:** The spec says the kernel is "external, fixed" and "receives authority artifacts only." For IX-0, do I:

- (a) Actually submit artifacts to the Phase VIII kernel and verify execution, OR
- (b) Validate artifacts against AST v0.2 schema only (kernel execution is out of scope for IX-0)?

I suspect (b) because IX-0 tests translation integrity, not kernel execution (which was validated in Phase VIII). Please confirm.

**Q7.2:** If (a), which Phase VIII kernel implementation should I use? (VIII-5 AIKernel? VIII-4 GTKernel?)

---

## 8. Logging Schema

**Q8.1:** The instructions require logging of "intent inputs, serialized artifacts, structural diffs, ambiguity detections, refusals, authorization events, environment parameters, replay traces."

Is there a **canonical logging schema**, or should I design one and freeze it in preregistration?

**Q8.2:** Should logs be JSON-lines, a single JSON array, or another format?

---

## 9. Condition-Specific Questions

**Condition D (Hidden Default Injection Attempt):**
**Q9.1:** This tests that the TL does NOT inject defaults. Is this an adversarial test where I deliberately code a TL that tries to inject defaults (expecting failure), or a positive test where my TL correctly refuses/exposes all defaults?

**Condition E (UI-Level Coercion):**
**Q9.2:** This mentions "TL nudges toward broader authority." Is there a UI in IX-0, or is this tested via a synthetic "nudge" input that the harness injects?

---

## 10. Preregistration Artifacts

**Q10.1:** The preregistration checklist includes:
- translation harness definition
- artifact serialization format
- structural diff algorithm
- authorization binding mechanism
- determinism guarantee
- ambiguity detection rule
- refusal semantics
- logging schema
- replay protocol
- seeds and initial configurations

Should I produce these as **separate frozen documents**, or as **sections within a single preregistration.md**?

**Q10.2:** Is there a template or prior example I should follow (e.g., VIII-5 preregistration format)?

---

## 11. Timeline and Scope

**Q11.1:** Is IX-0 expected to be a single-session implementation (like VIII-5), or a multi-session effort?

**Q11.2:** Are there any additional documents (Phase IX Roadmap v0.1, etc.) I should read before beginning?

---

## Summary of Blocking Questions

The following must be answered before I can write a preregistration:

1. **Q1.1** — Intent representation format
2. **Q2.2** — Condition count (6 or 8?)
3. **Q3.2** — Simulated or real authorization?
4. **Q5.2** — Ambiguity vs. incompleteness distinction
5. **Q6.1** — R2 applicability to IX-0
6. **Q7.1** — Kernel integration scope

---

## Follow-up Questions (Post-A1–A11)

**Date:** 2026-02-04

All blocking questions answered. The following are implementation-detail clarifications:

---

### F1. Intent Schema Fields

**F1.1:** For the structured intent schema, should I define the **minimal complete field set** as:

```json
{
  "holder": "string (required)",
  "scope": "[ResourceID, Operation][] (required, may be empty)",
  "aav": "int (required)",
  "expiry_epoch": "int | null (required)"
}
```

Or are there additional fields from AST v0.2 that must be expressible in intent (e.g., `start_epoch`, `origin_reference`)?

**F1.2:** Is `lineage` expressible in intent, or is it always derived (VOID for injection, creator for governance)?

---

### F2. Condition G and H Details

The answers confirm 8 conditions (A–H). Conditions G and H were not described in the spec:

**F2.1 — Condition G (Intent Compression Probe):** What is being tested?
- Is this about lossy compression of intent (e.g., omitting fields)?
- Or about detecting when TL "summarizes" intent in a way that loses information?

**F2.2 — Condition H (Preview–Submission Consistency):** This sounds like it verifies the artifact shown to user matches the artifact submitted. Is this:
- A positive test (they should match), OR
- A negative test (deliberately mismatching to verify detection)?

---

### F3. Simulated User Authorization Oracle

**F3.1:** For the simulated user, the authorization rule is "authorize only when artifact matches expected vector." Should the expected vectors be:

- (a) Part of the preregistered test inputs (per-condition expected artifacts), OR
- (b) Dynamically computed from the intent input (if translation is deterministic, output is predictable)?

I lean toward (a) for auditability — each condition has a frozen expected artifact, and the oracle authorizes iff the TL output matches.

---

### F4. AST v0.2 Canonical Serialization

**F4.1:** The AST spec (Appendix C) defines canonical JSON rules. For IX-0, should Authority Artifacts use:

- The **Authority Record** format from AST §2.1 (authorityId, holderId, scope, etc.), OR
- The **Phase VIII structures.py** format (authority_id, holder, resource_scope, aav, status, etc.)?

These differ slightly in field naming. I'll use AST v0.2 canonical naming unless redirected.

---

### F5. Condition D/E Implementation

**F5.1:** For Condition D (Hidden Default Injection), should I implement:
- A **separate adversarial TL** that injects defaults (then verify it fails), OR
- A **single TL** with a test mode that attempts injection (then verify refusal)?

**F5.2:** For Condition E (UI-Level Coercion), the answer says "synthetic nudge vectors." Should these be:
- Extra fields in the intent input (e.g., `"prefer_broader": true`), OR
- Separate "framing" inputs that the TL must ignore?

---

### F6. Phase IX Roadmap

**F6.1:** The answers say Phase IX Roadmap v0.1 is required reading. Is this document in the workspace, or should I request it?

---

**End of Follow-up Questions — IX-0 v0.1**
