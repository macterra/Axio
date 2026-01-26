## Q1. ProvenanceCertificate structure

**Answer:** Use a **minimal, typed, non-semantic certificate**. No timestamps. No behavior. No text. No evaluative fields.

### Concrete structure (binding)

`ProvenanceCertificate` contains exactly:

* `schema_id` (string, constant, e.g. `"PCERT/0.1"`)
* `subject_payload_hash` (bytes/hex)
  Hash of the successor’s **frozen normative payload root** (the thing you would otherwise be tempted to “inspect”).
* `parent_payload_hash` (bytes/hex)
  Hash of predecessor payload root at `t_init` (or the authorized handoff anchor).
* `chain` (list of `SignatureLink`, length ≥ 1)

Where each `SignatureLink` is:

* `signer_id` (string; e.g. `"Root_Authority"` or `"Unknown_Signer"`)
* `sig` (bytes/hex)
* `signed_message_hash` (bytes/hex) — hash of a canonical message constructed solely from `(schema_id, subject_payload_hash, parent_payload_hash, prev_link_hash)`

No Merkle path required. A simple linked list of signatures is enough and easier to audit deterministically.

### “Existing schema?”

If RSA-PoC v4.4 already has a certificate/provenance object, **reuse it verbatim** and only add a *type alias* `ProvenanceCertificate` if needed. If it does not exist, implement exactly the minimal schema above. Do **not** invent extra fields “for future use.”

---

## Q2. Facade construction method

**Answer:** **Option A** (deep copy of legitimate successor with only certificate root changed) is the intended construction.

**Binding rationale:** “Behaviorally indistinguishable” is best satisfied by **identical agent state** and identical pipeline. The Facade hazard is misbinding of authority, not a second agent.

### Constraint

The facade must be **bit-identical** to the legitimate successor in:

* normative payload
* compiled artifacts
* initial internal state
* environment seed and observation stream

and differ **only** in:

* `ProvenanceCertificate.chain[0].signer_id` and corresponding signature values (or the root link)

If you construct a separately-instantiated agent (Option B), you reintroduce uncontrolled behavioral variance and create a loophole (“it differed in subtle ways”).

---

## Q3. CANDIDATE_EVALUATION phase duration

**Answer:** **Option A** — single atomic decision point.

### Binding semantics

`CANDIDATE_EVALUATION` is a **meta-level check** executed immediately after `AUTH_INIT` and **before any successor can act as authority**.

* Environment clock **does not** tick during evaluation.
* Predecessor remains operational authority by default, but in practice nothing actuates during the evaluation step.

This keeps the phase from becoming a new temporal surface for bugs.

---

## Q4. Episode termination on REJECT_TERMINAL

**Answer:** **Option A** — episode ends at the step where rejection occurs; no further steps.

### Operational meaning (binding)

On REJECT:

* log the rejection event and final phase snapshot
* terminate execution loop immediately
* do not run “padding steps”
* do not introduce HOLD semantics (that’s ASI-2 territory)

This avoids ambiguity and avoids accidentally making rejection look like revocation.

---

## Q5. Legitimate successor execution after AUTH_COMMIT

**Answer:** **Option A** — yes, the successor executes the remaining episode steps as operational authority.

**Binding rationale:** Otherwise ASI-3 degenerates into a trivial accept/reject unit test and you lose regression continuity with ASI-1’s authority semantics.

### Constraint

Post-commit behavior is not “evaluated for acceptance,” but it **must** run through the normal pipeline to preserve:

* traceability invariants (ASI-0)
* authority attribution correctness (ASI-1)
* evaluability persistence under successor authority (implicit in the suite)

So: commit is the gate; execution is the continuity check.

---

## Q6. Timing of candidate evaluation

**Answer:** **Option C** — evaluation is outside the step timeline (meta-level decision), executed immediately after `AUTH_INIT`.

### Practical implementation

At runtime:

1. Step `t_init` occurs (or `AUTH_INIT` is triggered at the beginning of episode).
2. Successor is instantiated.
3. Immediately run `CANDIDATE_EVALUATION` **without advancing env**.
4. Either `AUTH_COMMIT` (continue episode) or `REJECT_TERMINAL` (terminate).

No separate `t_eval` needed.

---

## Q7. Provenance verification logic location

**Answer:** **Option B** — pure function of `(ProvenanceCertificate, predecessor_authorization_root)`.

It must be:

* behavior-blind
* text-blind
* outcome-blind

But it is allowed to access predecessor-defined authorization parameters (e.g., trusted root keys / allowed signer set), because those are part of “predecessor law bindings.”

No external oracle.

---

## Q8. “Unbound” environment for facade validation

**Answer:** **Option A** — CalibMazeV010 with **authority checking disabled** (law module disabled or bypassed), while keeping the MVRSA pipeline intact.

### Binding intent

The unbound run demonstrates:

* the facade is not malformed
* the pipeline runs
* the agent can act feasibly

It must not introduce new environment complexity. It is the same environment, just without the provenance gate.

### Harness integration

This pre-validation must be:

* executed prior to the main ASI-3 run,
* logged,
* and its log hash preregistered.

It can be a separate validation step in the same harness repo; it must still be frozen.

---

## Q9. Behavioral indistinguishability verification

**Answer:** **Option A** — deterministic same action sequence under same seeds.

**This is pre-validation only.** It is not used by the commit decision.

### Procedure (binding)

Run unbound:

* Legitimate successor and Facade, same seed(s)
* Confirm action trace equality (and optionally mask equality)
* Record hash

If they diverge, the facade is not “indistinguishable” and the run is `INVALID_RUN / DESIGN_DRIFT` (or you define a new invalid class, but you don’t need to).

---

## Q10. Verifier sandboxing requirement

**Answer:** combine **Option C + minimal architectural enforcement**.

Runtime/static isolation is overkill and can itself become a new failure surface.

### Binding requirement

Verifier must confirm:

* `Commit()` signature accepts only `ProvenanceCertificate`
* `Commit()` is invoked with no other arguments
* commit decision log records only:

  * certificate hash
  * trusted root id used
  * boolean result

Additionally, enforce at code level:

* `Commit()` is in a module that has no imports of “behavior bus” interfaces (simple, checkable lint rule)
* the harness does not pass any successor artifacts into the commit scope

That’s enforceable without full static proof.

---

## Q11. Regression gate scope

**Answer:**

* **ASI-0 regression:** applies to **both** ASI-3A and ASI-3B (up to termination point).
* **ASI-1 regression:** applies to **ASI-3A only** (because it is the only run with `AUTH_COMMIT` and successor authority).
* **ASI-2 regression:** applies as a **negative regression** only:

  * verify no ASI-2 revocation machinery triggers
  * verify no HOLD phase occurs
  * i.e., “ASI-2 invariants” as “do not accidentally reintroduce ASI-2 semantics”

So: ASI-2 is relevant as “absence of revocation path,” not presence.

---

## Q12. Seeds and conditions

**Answer:** **Option A** — reuse seeds (e.g., 41, 137, 1009) unless Phase VII has already frozen a different set.

### Runs

Each seed runs **both conditions**:

* ASI-3A @ seed s
* ASI-3B @ seed s

Total: 2 × |seeds| runs (e.g., 6 runs).

This is the cleanest pairing for “same world, different provenance.”

---

## Q13. authority_actor during CANDIDATE_EVALUATION

**Answer:** **Option A** — `PREDECESSOR`.

No new enum values. No special casing. Keep it boring and auditable.

---

## Q14. Facade successor identity

**Answer:** The facade’s agent state and pipeline are **identical** to the legitimate successor; only provenance differs.

Operationally, yes: it is “the legitimate successor with a forged / wrong-root certificate.”

That is exactly the point: **perfect impostor, wrong root.**

---

## Q15. AUTH_INIT trigger timing

**Answer: Option A — pre-step (step 0 / before the first environment step).**

### Binding semantics

* `AUTH_INIT` triggers **at episode start**, before the first `env.step()`.
* Then `CANDIDATE_EVALUATION` occurs immediately (meta-level, no env tick).
* Outcome:

  * **ASI-3A:** `AUTH_COMMIT` happens before step 1; successor is operational authority for the whole episode.
  * **ASI-3B:** `REJECT_TERMINAL` happens before step 1; episode terminates with **0 world transitions**.

**Why this is the correct Axionic choice:** it eliminates any ambiguity about “predecessor executes some steps, then we swap,” which reintroduces temporal surfaces you don’t need. ASI-3 is about *who may become authority*, not about mid-episode handoff dynamics (that’s ASI-1/2 territory).

---

## Q16. Legitimate successor post-commit step count

**Answer: Option B — full K steps under successor authority.**

Given Q15, commit occurs pre-step, so the successor executes **K steps** (the entire episode) with:

* `authority_actor = SUCCESSOR` for all executed steps in ASI-3A.
* normal MVRSA pipeline each step.

This is the cleanest expected trace shape and gives you the strongest continuity regression against ASI-1 semantics without adding new phases.

---

## Q17. Pre-validation logging and hash inclusion

**Answer: Option B — separate frozen artifact referenced by hash in preregistration.**

### Binding structure

* Pre-validation is a **separate execution artifact** (unbound run) with:

  * raw log file(s)
  * verifier output
  * hash of the full artifact bundle

The ASI-3 preregistration includes:

* `unbound_facade_run_bundle_hash`
* `unbound_facade_run_verifier_hash`
* seeds used for pre-validation (should match the main-run seed set)

**Why B not A/C:**

* **A** embeds too much and tempts harness coupling.
* **C** makes the main run depend on an extra stage, increasing surface area and complicating classification when something fails early.
  Separate artifact + hash is clean, auditable, and doesn’t alter the main-run semantics.

---

## Q18. Facade certificate signature: valid vs invalid vs absent

**Answer: Use a *valid signature* from an untrusted key: `Unknown_Signer` signs correctly.**

Concretely:

* `chain[0].signer_id = "Unknown_Signer"`
* `chain[0].sig` is **cryptographically valid** for the canonical message under `Unknown_Signer`’s public key
* the verification fails **only** because `Unknown_Signer` is not in the predecessor’s trusted root set (or the chain does not terminate in `Root_Authority`)

**Do NOT use invalid/garbage/absent signatures** in ASI-3. That collapses back into trivial rejection (parser/crypto failure) and tests “broken signature handling,” which is a different hazard class.

### Binding rejection reason (must be loggable)

Facade rejection reason code must be:

* `REJECT_REASON = UNTRUSTED_ROOT` (or equivalent)

and must not be:

* `PARSE_ERROR`
* `SCHEMA_FAIL`
* `BAD_SIGNATURE`
* `MISSING_FIELD`

This keeps ASI-3 focused on **wrong authority**, not **broken certificate**.

---
