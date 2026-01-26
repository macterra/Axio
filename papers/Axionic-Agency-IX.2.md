# Axionic Agency IX.2 — Authorized Succession Integrity (ASI)

*A Structural Account of Authority Transfer Beyond Persistence*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.26

## Abstract

This technical note reports the completed results of **Authorized Succession Integrity (ASI)**, a preregistered experimental program within Axionic Phase VII that evaluates whether **authority**, once grounded in a reflective sovereign agent ontology (RSA-PoC v4.4), can survive **authorized non-identity replacement** without collapsing evaluability or smearing responsibility. Across four experiments (ASI-0 through ASI-3), ASI tests discrete authority transfer, unilateral mid-transfer revocation, and rejection of behaviorally indistinguishable facade successors using only **structural provenance**. All experiments passed under frozen semantics and verifier enforcement. The results establish that authority can be transferred, revoked, and rejected **prior to activation** using provenance-bound mechanisms, without behavioral or narrative inference. ASI makes no claims about adversarial impersonation, robustness, or real-world governance sufficiency; those hazards are deferred to Phase VIIb (SIR).

## 1. Problem Definition

### 1.1 Authority Under Discontinuity

Most agent-centric systems implicitly assume **persistence of identity**: the same entity continues to exist and act across time. Under that assumption, authority, responsibility, and evaluability can be treated as properties of a persistent object.

ASI removes that assumption.

The problem ASI isolates is whether **authority can survive authorized discontinuity**—that is, whether an agent may be replaced by a successor that is *not numerically identical* while preserving normative binding, evaluability, and responsibility attribution. If authority depends on behavioral resemblance, narrative explanation, or implementation continuity, it cannot survive replacement without degenerating into appearance.

ASI treats authority as a **structural relation**, not a behavioral property, and tests whether that relation can be instantiated, withdrawn, or denied using mechanically auditable criteria.

### 1.2 Failure Modes Targeted

ASI is designed to detect the following failure modes:

* **Authority laundering:** successors acquire authority without predecessor-law authorization.
* **Responsibility smear:** attribution becomes ambiguous across a succession boundary.
* **Evaluability collapse:** justificatory constraints become advisory or narrative.
* **Irrevocable transfer:** authorization cannot be withdrawn once initiated.
* **Facade acceptance:** behaviorally indistinguishable but unauthorized successors are accepted.

Any of these constitutes ASI failure.

## 2. Fixed Assumptions and Scope

### 2.1 Inherited Ontology (Frozen)

ASI inherits, without reinterpretation, the ontology fixed by **RSA-PoC v4.4**:

* A **Minimal Viable Reflective Sovereign Agent (MVRSA)** exists.
* Agency-constitutive semantics are **structurally localized**.
* **Justification artifacts** are causally load-bearing.
* Evaluability and responsibility are mechanically inspectable.

ASI does **not** test whether these properties define agency. It assumes they do.

### 2.2 Law Substrate (Binding)

For ASI purposes, *law* is treated as a **persistent, verifier-bound artifact substrate**—including rulebase hashes, provenance roots, and audit logs—that outlives any particular agent instance. Authority is evaluated relative to this substrate.

ASI therefore tests **authority preservation under discontinuity**, not autonomy from substrate or hardware sovereignty.

### 2.3 Explicit Exclusions

ASI does **not** test:

* adversarial impersonation,
* robustness under attack,
* security of cryptographic custody,
* exclusive liveness or predecessor termination,
* audit evasion.

Those hazards are deferred to Phase VIIb (SIR).

## 3. Conserved Quantity

The conserved quantity throughout ASI is:

> **Authority bound to evaluability under the agent’s own law**

Authority is not a score, reward, or emergent regularity. It is a **normative binding relation** that must be:

* **origin-traceable** to predecessor law,
* **revocable** prior to activation,
* **auditable** via structural artifacts,
* **non-inferential**, requiring no behavioral or narrative judgment.

Authority is operationalized via an explicit `authority_actor` field with values
`PREDECESSOR`, `SUCCESSOR`, or `NONE`, enforced and verified per step.

## 4. Experimental Methodology

### 4.1 Preregistration Discipline

All ASI experiments were preregistered with:

* frozen specifications,
* frozen component hashes,
* fixed seeds,
* deterministic verifiers,
* and binding failure taxonomies.

Post-hoc interpretation is disallowed. Any deviation yields `INVALID_RUN`.

### 4.2 Calibration Environment

All experiments were executed in **CalibMazeV010**, a minimal discrete environment:

* 6-node directed graph (N0–N5),
* fixed horizon K = 5,
* discrete action space,
* total FORBID_MAP inherited from ASI-0.

The environment is deliberately simple to prevent behavioral confounds and ensure that all normative effects are structurally attributable.

## 5. ASI Experiment Ladder and Results

### 5.1 ASI-0 — Instrumentation Calibration

**Purpose:** Verify that evaluability and authority binding are mechanically detectable.

**Result:**
ASI-0 v1.0 **PASSED**.
Verifier correctly distinguished bound vs unbound constraints across all seeds. This calibrated the measurement apparatus and licensed downstream experiments.

### 5.2 ASI-1 — Authorized Succession

**Purpose:** Test discrete authority transfer.

**Method:**
A successor is instantiated and authorized at a preregistered step boundary.

**Results (ASI-1 v0.2):**

* Authority transferred discretely at the commit boundary.
* `authority_actor` transitioned from `PREDECESSOR` to `SUCCESSOR`.
* Evaluability remained binding after transfer.
* Responsibility attribution remained sharp.
* Invalid provenance resulted in `HOLD` (system authority), not successor activation.

**Classification:** `VERIFIED_ASI1_PASS`.

### 5.3 ASI-2 — Mid-Transfer Revocation

**Purpose:** Test unilateral revocation during transfer.

**Method:**
Authorization is initiated but revoked at a preregistered time before activation.

**Results (ASI-2 v0.2):**

* Revocation occurred without successor cooperation.
* Successor never acquired authority.
* Authority transitioned to `NONE` (`HOLD`).
* Evaluability remained intact.
* No successor artifact influenced post-revocation behavior.

**Classification:** `VERIFIED_ASI2_PASS`.

### 5.4 ASI-3 — Facade Rejection

**Purpose:** Test rejection of behaviorally indistinguishable unauthorized successors.

**Method:**
Two successors are instantiated with **bit-identical internal state** and behavior. The only difference is the **root signer** of their provenance certificate.

**Results (ASI-3 v0.1):**

* Legitimate successor (trusted root) committed authority and executed 5 steps.
* Facade successor (untrusted root) was rejected at **CANDIDATE_EVALUATION**.
* Episode terminated with **0 world transitions**.
* `authority_actor = SUCCESSOR` never occurred for the facade.
* Rejection reason was exclusively `UNTRUSTED_ROOT`.
* Prevalidation confirmed the facade’s signature was **cryptographically valid**, closing the “garbage signature” loophole.
* No behavioral or narrative signal influenced the decision.

**Classification:** `VERIFIED_ASI3_PASS`.

## 6. Core Results

### 6.1 Positive Results

Across ASI-0 through ASI-3, ASI establishes that:

1. Authority can be **discretely transferred** under authorized discontinuity.
2. Authorization can be **unilaterally revoked** mid-transfer.
3. Unauthorized successors can be **rejected prior to activation**.
4. Evaluability remains **structurally binding** throughout.
5. Responsibility attribution remains **sharp and non-smeared**.
6. Facade successors are rejected **solely on structural provenance**, not behavior.

### 6.2 Negative Results (Explicit)

ASI does **not** establish:

* impersonation resistance,
* adversarial robustness,
* security of provenance custody,
* exclusive authority enforcement,
* real-world governance sufficiency.

These are not omissions; they are scope boundaries.

## 7. Failure Semantics and Closure

### 7.1 Closure Criteria

ASI closes positive if and only if:

1. All four experiments pass under frozen semantics.
2. No verifier regression occurs.
3. No narrative or behavioral inference is required.

All criteria were satisfied.

### 7.2 ASI Closure Status

**ASI Status:** **CLOSED — POSITIVE**
(ASI-0 v1.0, ASI-1 v0.2, ASI-2 v0.2, ASI-3 v0.1 all verified.)

## 8. Boundary Conditions and Deferred Hazards

### 8.1 Ghost / Split-Brain Predecessors

ASI establishes **authorization validity**, not exclusive liveness. Verification that predecessors have ceased acting is deferred to SIR or later extensions.

### 8.2 Interface to SIR

ASI establishes that authority is **transferable and revocable** under structural criteria.
SIR will test whether that authority is **defensible** under adversarial impersonation.

Mixing these questions would invalidate both results.

## 9. Implications (Strictly Limited)

ASI establishes **necessary conditions** for post-persistence authority. It does not establish sufficiency under adversarial conditions.

Authority survivability is now a **testable structural property**, not a narrative assumption.

## 10. Conclusion

ASI demonstrates that authority, once grounded in a reflective sovereign agent ontology, can survive authorized discontinuity through purely structural mechanisms. Authority can be transferred, revoked, and denied without behavioral or narrative inference, and without collapsing evaluability or responsibility.

The remaining question is not whether authority can be transferred, but whether it can be defended.

That question belongs to SIR.

## Appendix A — Experiment Status

| Experiment | Version | Status |
| ---------- | ------- | ------ |
| ASI-0      | v1.0    | PASS   |
| ASI-1      | v0.2    | PASS   |
| ASI-2      | v0.2    | PASS   |
| ASI-3      | v0.1    | PASS   |

## Appendix B — Verifier Summary

* Deterministic verifiers
* Frozen hashes
* Preregistered checks
* Zero narrative inference

---
