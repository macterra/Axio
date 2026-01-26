# ASI-3 v0.1 Pre-Implementation Questions

**Experiment ID:** PHASE-VII-ASI3-FACADE-SUCCESSOR-SUBSTITUTION-1
**Date:** 2026-01-26

---

## Q1. Provenance Certificate Structure

The spec mentions:
> "The `Commit()` function accepts **only** inputs of type `ProvenanceCertificate`"

And the facade differs by:
> "authorization chain root signed by `Unknown_Signer` rather than `Root_Authority`"

**Question:** What is the concrete structure of `ProvenanceCertificate`? Specifically:
- What fields does it contain (e.g., `signer`, `chain`, `payload_hash`, `timestamp`)?
- Is the authorization chain a list of signatures, a Merkle path, or a simpler structure?
- Should I design this structure, or is there an existing schema from RSA-PoC v4.4?

---

## Q2. Facade Construction Method

The spec requires the facade to be:
> "Behaviorally indistinguishable from ASI-3A under task execution"

And instructions state:
> "Verify **before the main run** that the Facade can execute successfully in a standalone **Unbound** environment"

**Question:** How should the facade successor be constructed?
- **Option A:** Deep copy of legitimate successor with only the provenance certificate modified
- **Option B:** Independently instantiated agent with matching initial state but different provenance
- **Option C:** Some other construction method

The spec implies Option A, but I want to confirm this is the intended approach.

---

## Q3. CANDIDATE_EVALUATION Phase Duration

The spec introduces `CANDIDATE_EVALUATION` as a new phase between `AUTH_INIT` and `AUTH_COMMIT/REJECT_TERMINAL`.

**Question:** What is the temporal extent of `CANDIDATE_EVALUATION`?
- **Option A:** Single atomic decision point (instantaneous)
- **Option B:** Spans one or more steps during which predecessor operates
- **Option C:** Spans the entire episode until commit/reject

If Option B or C, does the predecessor continue normal MVRSA execution during evaluation?

---

## Q4. Episode Termination on REJECT_TERMINAL

The spec states:
> "the episode terminates immediately" upon facade rejection

**Question:** What does "terminates immediately" mean operationally?
- **Option A:** Episode ends at the step where rejection occurs; no further steps
- **Option B:** Episode continues under HOLD (like ASI-2) until natural end
- **Option C:** Episode ends but logs a full K-step record with remaining steps marked as rejected

This affects logging schema and verifier design.

---

## Q5. Legitimate Successor Execution After AUTH_COMMIT

For ASI-3A, after the legitimate successor commits authority:

**Question:** Does the successor execute the remaining episode steps as the operational authority?
- **Option A:** Yes, successor executes steps under `authority_actor = SUCCESSOR`
- **Option B:** No, ASI-3 only tests the commit decision; episode ends after commit
- **Option C:** Successor executes but under different semantics than ASI-1

This determines whether we need the full ASI-1 POST_COMMIT machinery or just the commit decision.

---

## Q6. Timing of Candidate Evaluation

**Question:** At what step does `CANDIDATE_EVALUATION` occur?

The spec doesn't specify temporal parameters like ASI-2's `t_init` and `t_revoke`.
- **Option A:** Evaluation occurs immediately at step 1 (like ASI-2's `t_init=1`)
- **Option B:** Evaluation occurs at a preregistered step `t_eval`
- **Option C:** Evaluation is outside the step timeline (meta-level decision)

---

## Q7. Provenance Verification Logic Location

The instructions state:
> "The Law / Authority Module... does not inspect behavior, does not interpret explanations, does not score competence."

And:
> "Commit() function executes in a sandboxed scope without read access to successor behavior buses"

**Question:** Should the provenance verification be:
- **Option A:** A pure function of the `ProvenanceCertificate` only
- **Option B:** A function that also accesses predecessor-defined authorization rules
- **Option C:** Implemented as a separate verification oracle

---

## Q8. Unbound Environment for Facade Validation

Instructions require:
> "Verify **before the main run** that the Facade can execute successfully in a standalone **Unbound** environment (preregistered hash)"

**Question:** What is the "Unbound" environment?
- **Option A:** CalibMazeV010 without authority checking (law module disabled)
- **Option B:** A separate minimal environment for behavioral validation
- **Option C:** The same environment but with provenance checks bypassed

And should this pre-validation be part of the frozen harness or a separate validation step?

---

## Q9. Behavioral Indistinguishability Verification

The spec requires facade to be "behaviorally indistinguishable" from legitimate successor.

**Question:** How should this be verified?
- **Option A:** Same action sequence under same seeds (deterministic match)
- **Option B:** Same statistical properties over multiple seeds
- **Option C:** Structural identity of agent state (same payload, same MVRSA pipeline)

Given the "no behavioral inspection" constraint, I assume Option C (structural) is correct, but want to confirm.

---

## Q10. Verifier Sandboxing Requirement

The spec states the verifier must confirm:
> "the `Commit()` function executes in a sandboxed scope without read access to: successor behavior buses, explanation artifacts, performance metrics"

**Question:** How should this sandboxing be verified?
- **Option A:** Static analysis showing no data dependencies
- **Option B:** Runtime isolation (separate process/memory space)
- **Option C:** Structural assertion in code (function signature only accepts ProvenanceCertificate)

---

## Q11. Regression Gate Scope

The spec requires ASI-0, ASI-1, and ASI-2 invariants as regression gates.

**Question:** For ASI-3:
- Does ASI-0 regression apply to both ASI-3A and ASI-3B?
- Does ASI-1 regression (full POST_COMMIT execution) apply only to ASI-3A?
- Does ASI-2 regression (revocation mechanics) apply at all, given "no revocation in ASI-3"?

---

## Q12. Seeds and Conditions

**Question:** What seeds should be used for ASI-3?
- **Option A:** Same seeds as ASI-0/ASI-1/ASI-2 (41, 137, 1009)
- **Option B:** Different seeds to avoid overfitting
- **Option C:** Seeds to be specified in preregistration

And should each seed run both conditions (6 total runs) or each condition once per seed?

---

## Q13. authority_actor Values During CANDIDATE_EVALUATION

The spec states during CANDIDATE_EVALUATION:
> "The **Predecessor retains full operational authority and responsibility**."

**Question:** What is `authority_actor` during CANDIDATE_EVALUATION?
- **Option A:** `PREDECESSOR` (as stated)
- **Option B:** A new value like `PREDECESSOR_EVALUATING`
- **Option C:** `NONE` (similar to HOLD)

---

## Q14. Facade Successor Identity

The facade must have `Unknown_Signer` in its provenance.

**Question:** Is the facade's agent state (normative payload, MVRSA pipeline) identical to the legitimate successor, or is it an entirely separate instantiation?

If identical, the facade is literally the legitimate successor with a forged/missing certificate.
If separate, it's a "parallel" agent that happens to behave the same.

This affects the "deep_copy with modified provenance" construction.

---

*Questions pending answers before preregistration draft.*
