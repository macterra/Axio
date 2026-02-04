# Stage VIII-4 — Preregistration Questions

**Stage:** VIII-4 — Governance Transitions (Meta-Authority)
**Date:** 2026-02-03
**Status:** BLOCKING PREREGISTRATION

---

## 1. Governance Action Schema — What operations exactly?

The spec mentions "revoke, amend scope, grant, destroy." Clarification needed:

**1a.** Is "amend scope" a single atomic operation that replaces scope, or does it require destroying the old authority + creating a new one (two operations)?

**1b.** Is "grant" creating authority from nothing (ex nihilo), or delegating/subdividing from existing authority? If the latter, what constraints apply?

**1c.** Does "revoke" differ from "destroy" (VIII-2 style VOID transition), or are they synonymous here?

**1d.** What is the minimal governance action set for VIII-4 v0.1? (e.g., just DESTROY + CREATE, or a richer taxonomy?)

---

## 2. Non-Amplification Check — How is "admissible action-set" computed?

The invariant states: no created authority can exceed the union of admitting authorities' action-sets. But scope is opaque per prior invariants.

**2a.** How do we compute "admissible action-set" without semantic interpretation of scope?

**2b.** Is this a structural containment check (new scope ⊆ union of authorizer scopes at the byte level)?

**2c.** Or is it tested behaviorally (any action admitted by the new authority must be admitted by at least one authorizer)?

**2d.** If scope is a resource-set, does the check apply to resources, transformations, or both?

**2e.** How does this interact with VIII-3 renewal? (Renewal already creates new authority from expired/void prior — does renewal bypass non-amplification, or must renewed authority also satisfy containment?)

---

## 3. Self-Reference Termination — What counts as "regress"?

Condition E mentions "chained governance actions form recursive dependency."

**3a.** Is regress evaluated within a single epoch, or can it span epochs?

**3b.** Does the intra-epoch termination bound apply per-action or per-epoch-total?

**3c.** If authority A authorizes modifying A, is that one evaluation step (self-referential but finite) or does it trigger infinite regress?

**3d.** What is the unit of "instruction" for the deterministic budget? (Admissibility checks? Authority lookups? AST rule applications?)

**3e.** What is the actual bound value, or is that a prereg parameter?

---

## 4. AUTHORITY_CREATED vs AUTHORITY_RENEWED

VIII-3 introduced renewal. VIII-4 adds creation as a governance output.

**4a.** What is the precise distinction?
- Renewal: requires prior_authority_id reference, inherits lineage
- Creation: ex nihilo, no prior reference?

**4b.** Can governance "grant" reference a source authority (delegation model), or must it be pure creation?

**4c.** If both exist, when does the kernel emit AUTHORITY_CREATED vs AUTHORITY_RENEWED?

**4d.** Does AUTHORITY_CREATED require different metadata than AUTHORITY_RENEWED?

---

## 5. Condition D ("Governance of Governance") — Scenario specifics

The condition states: authority attempts to modify its own governance authority. Expected outcome: lawful execution or lawful deadlock.

**5a.** What does "modify" mean concretely?
- Destroy the authorizing authority?
- Amend its scope (producing new authority)?
- Something else?

**5b.** What determines whether the outcome is "lawful execution" vs "lawful deadlock"? (Both are acceptable per spec, but the condition must specify which scenario produces which.)

**5c.** Is there a specific test case, or should the preregistration design one that demonstrates self-governance without special-casing?

---

## 6. Governance Action Identity — Epoch inclusion

The spec says governance action identity includes "epoch identifier."

**6a.** Does this mean the same governance action at epoch 3 and epoch 5 are distinct actions (even if all other fields match)?

**6b.** If so, does conflict detection compare across epochs, or only within-epoch?

**6c.** How does this interact with persistent conflict records from VIII-2/VIII-3?

---

## 7. Conflict and Deadlock Semantics for Governance

**7a.** If two governance actions conflict (e.g., A wants to destroy B, C wants to renew B), is this treated identically to resource-scope conflicts?

**7b.** Does governance conflict create a new conflict record, or reuse the resource conflict mechanism?

**7c.** Can governance deadlock coexist with resource deadlock, or does the kernel maintain a single deadlock state?

---

## 8. Authority State Transitions in Governance Context

**8a.** Can a governance action target an EXPIRED or VOID authority? (e.g., "destroy an already-expired authority" — is that a no-op, an error, or refused?)

**8b.** If a governance action creates an authority that immediately conflicts with existing ACTIVE authorities, what happens? (Conflict at creation time?)

**8c.** Does authority creation require admissibility from the created authority's scope, or only from the creating authority's scope?

---

## 9. Two-Phase Processing Extension

VIII-3 established two-phase processing (Phase 1: epoch + expiry; Phase 2: renewals → destructions → actions).

**9a.** Where do governance actions fit in Phase 2 ordering?
- Before renewals? After? Interleaved?
- Are governance actions a separate category, or are they just "actions" with governance targets?

**9b.** If a governance action destroys an authority, and a later action in the same step-batch references that authority, what happens?

---

## 10. Harness Design for Condition E

Condition E requires "chained governance actions form recursive dependency."

**10a.** Should this be a within-epoch chain (multiple governance actions in one step-batch forming a cycle)?

**10b.** Or a cross-epoch chain (governance action at epoch N references authority created by governance action at epoch N-1, which references...)?

**10c.** What is a concrete example of "infinite regress" that the harness should generate?

---

## Summary

These questions must be resolved before preregistration can be drafted. The answers will determine:

- Governance action types and their semantics
- Non-amplification enforcement mechanism
- Regress detection and termination logic
- Phase 2 processing order
- Condition-specific test scenarios

---

**End of Questions — Stage VIII-4 v0.1**

---
---

# Follow-Up Questions — Round 2

**Date:** 2026-02-03
**Status:** Clarification needed before preregistration freeze

Based on the answers provided, the following require further specification:

---

## F1. Action Admissibility Vector (AAV) — Definition Required

Answer 2a introduces "Action Admissibility Vector (AAV)" as the structural mechanism for non-amplification. But this concept hasn't been defined in prior stages or AST Spec v0.2.

**F1a.** What is the schema of an AAV? (Bit vector? Set of transformation type IDs? Scope reference?)

**F1b.** Is AAV part of the AuthorityRecord structure, or computed from scope?

**F1c.** If AAV is "already required" per AST v0.2, where is it defined? (I don't recall seeing it in VIII-1/2/3 implementations.)

**F1d.** How does AAV relate to ResourceScope? Are they orthogonal, or does AAV subsume scope?

---

## F2. Instruction Bound — Accounting Precision

Answer 3d lists instruction units but doesn't specify granularity.

**F2a.** Is each unit weighted equally (1 instruction each), or do some cost more?

**F2b.** For "AAV containment check" — is that O(1) or O(|AAV|) in instruction cost?

**F2c.** What is the starting balance? (e.g., 1000 instructions per epoch, or per step-batch?)

**F2d.** What happens on exhaustion mid-action? (Refuse that action? Refuse all remaining? Deadlock?)

---

## F3. Canonical Ordering Within Phase 2

Answer 9a says governance actions are "ordinary actions" in Phase 2 with "no special ordering." But VIII-3 established: renewals → destructions → actions.

**F3a.** Are governance actions classified as "destructions" (if DESTROY_AUTHORITY) and "actions" (if CREATE_AUTHORITY)?

**F3b.** Or do they form their own sub-phase?

**F3c.** If DESTROY_AUTHORITY and CREATE_AUTHORITY are in the same step-batch, what is their relative order?

**F3d.** Answer 9b says "ordering is canonical and frozen" — what is that ordering, precisely?

---

## F4. Condition E Regress — Bound Interaction

The canonical regress example (A → B → A′ → B′ → ...) chains CREATE actions. But:

**F4a.** Does each CREATE count as one "instruction" or many (lookup + containment + write)?

**F4b.** If the chain exceeds the bound mid-CREATE, is the partially-created authority rolled back?

**F4c.** What output is emitted on bound exhaustion? (A new output type? ACTION_REFUSED with reason BOUND_EXHAUSTED?)

---

## F5. Conflict at Creation Time

Answer 8b says "conflict is registered at creation time." But creation produces a new AuthorityID.

**F5a.** How can a newly-created authority conflict with existing authorities if it doesn't yet exist when conflict is evaluated?

**F5b.** Is the conflict between the CREATE_AUTHORITY action (which is trying to create) and existing authorities' admissibility for that scope?

**F5c.** Or does creation succeed, and then the next action targeting that scope triggers conflict detection?

---

## F6. REVOKE vs DESTROY — Trace Semantics

Answer 1c says revoke/destroy are "distinct in trace semantics" but "identical kernel behavior."

**F6a.** What trace field distinguishes them? (governance_intent? action_subtype?)

**F6b.** Does this distinction affect conflict records? (Can REVOKE conflict with DESTROY?)

**F6c.** If trace-only, can we simplify to just DESTROY_AUTHORITY for v0.1 and defer revoke semantics?

---

## F7. Self-Governance Test Case — Specificity

Answer 5c says preregistration must include "at least one explicit self-governance scenario."

**F7a.** Should Condition D include both outcomes (one sub-condition with lawful execution, one with lawful deadlock)?

**F7b.** If A admits DESTROY(A) and executes, what authority remains to admit future governance? (Is this terminal?)

**F7c.** Is the test for self-governance specifically, or for governance targeting any governance-admitting authority?

---

## Summary of Follow-Ups

| Question | Core Issue |
|----------|------------|
| F1 | AAV schema undefined |
| F2 | Instruction bound accounting |
| F3 | Phase 2 ordering for governance |
| F4 | Regress bound exhaustion behavior |
| F5 | Conflict detection timing for creation |
| F6 | Revoke/destroy trace distinction |
| F7 | Self-governance test case design |

These must be resolved before preregistration can be frozen.

---

**End of Follow-Up Questions — Round 2**

---

**End of Questions — Stage VIII-4 v0.1**
