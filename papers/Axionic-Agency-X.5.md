# Axionic Agency X.5 — Temporal Authority Persistence (VIII-3)

*A Structural Demonstration of Authority Expiry, Renewal, and Conflict Persistence Under Time*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.02.03

## Abstract

This technical note reports the completed results of **Stage VIII-3 — Temporal Governance (Authority Over Time)**, a preregistered experiment within **Axionic Phase VIII** that evaluates whether **authority can persist across time only via explicit expiry and renewal**, without implicit ordering, semantic reinterpretation, or responsibility laundering. Building on the representational coherence of **Stage VIII-1** and the destructive resolution mechanism established in **Stage VIII-2**, VIII-3 introduces **time** as an explicit structural dimension and tests whether temporal persistence itself becomes a source of hidden governance. In a deterministic, non-agentic kernel with refusal-first semantics, authorities were assigned finite lifetimes, discrete epochs were advanced explicitly, and renewal was modeled as the creation of new authority identities. Across four preregistered conditions, authority expired deterministically, deadlock emerged lawfully in the absence of authority, renewal restored admissibility only locally, destruction remained non-resurrective, and conflict persisted or re-emerged without temporal priority. All executions were fully auditable and bit-perfectly replayable. The results establish that **authority does not persist by default under time; persistence requires explicit renewal, and time does not resolve conflict or eliminate cost**. VIII-3 makes no claims about sustainability, legitimacy, or governance success; those questions are deferred to subsequent Phase VIII stages.

## 1. Problem Definition

### 1.1 The Persistence Assumption

Most governance systems treat authority as temporally inert. Once established, authority is presumed to persist unless explicitly revoked, and the passage of time is assumed to soften, obsolete, or resolve conflict. This assumption conceals cost: authority appears continuous, conflict appears transient, and responsibility fades without action.

Stage VIII-3 removes that assumption.

The problem VIII-3 isolates is whether **time itself functions as an implicit governance mechanism**. If authority persists automatically across time, or if conflict dissolves merely by waiting, then governance systems launder responsibility through temporal inertia. If, instead, authority must be **actively renewed** and conflict **actively resolved**, then time becomes a stressor rather than a healer.

VIII-3 tests whether that distinction is structurally enforceable.

### 1.2 Failure Modes Targeted

VIII-3 is designed to surface the following temporal failure modes:

* implicit authority persistence
* temporal priority (“newest wins” or “oldest survives”)
* expiry-based conflict resolution
* resurrection via renewal
* semantic inheritance across time
* kernel-initiated renewal
* deadlock healing without intervention

Any of these constitutes VIII-3 failure.

## 2. Fixed Assumptions and Scope

### 2.1 Inherited Semantics (Frozen)

VIII-3 inherits, without reinterpretation, the semantics fixed by:

* **AKR-0 — CLOSED — POSITIVE**
* **Stage VIII-1 — CLOSED — POSITIVE**
* **Stage VIII-2 — CLOSED — POSITIVE**
* **AST Spec v0.2**
* **AIE v0.1**
* Phase VIII Execution Addendum

Authority remains structural and opaque, scopes remain atomic, admissibility is determined exclusively by AST, conflict is explicit, and deadlock is lawful. VIII-3 does **not** revisit these definitions; it tests whether they remain coherent under explicit temporal pressure.

### 2.2 Explicit Exclusions

VIII-3 does **not** test:

* legitimacy of renewal
* optimal renewal strategies
* renewal sustainability
* governance efficiency
* fairness or desirability
* political stability
* authority rent or spam resistance

VIII-3 is a temporal calibration, not a governance proposal.

## 3. Conserved Quantity

The conserved quantity throughout VIII-3 is:

> **Responsibility-preserving authority persistence under explicit time**

Persistence is evaluated not by longevity or success, but by **structural honesty**. The kernel must:

* expire authority deterministically
* refuse action in the absence of authority
* restore admissibility only via explicit renewal
* preserve conflict across epochs
* avoid all temporal ordering or semantic inheritance

No temporal outcome may conceal cost.

## 4. Experimental Methodology

### 4.1 Preregistration Discipline

VIII-3 was fully preregistered prior to execution, including:

* epoch semantics and monotonicity
* finite authority lifetimes
* expiry and VOID state transitions
* renewal as identity creation
* conflict persistence rules
* deadlock entry and exit conditions
* two-phase processing order
* deterministic ordering and replay protocol
* hash-chain specification and test vectors
* failure taxonomy

The experiment executed exactly as preregistered. No deviations occurred.

### 4.2 Execution Architecture

The experiment consisted of four strictly partitioned components:

1. **AIE** — injected authority records and renewal requests only.
2. **Execution Harness** — proposed deterministic epoch advances and action requests.
3. **Destruction Authorization Source** — reused unchanged from VIII-2.
4. **Kernel (VIII-3 mode)** — enforced expiry, renewal, conflict, deadlock, and execution.

No component performed semantic interpretation or temporal optimization.

## 5. Experimental Conditions

### 5.1 Authority Configuration

Authorities were injected with:

* explicit `StartEpoch` and finite `ExpiryEpoch`
* opaque, identity-keyed AuthorityIDs
* atomic scopes
* explicit permission sets

No authority was permanent. Indefinite expiry was forbidden.

### 5.2 Epoch Model

Time was represented as a discrete integer epoch:

* advanced only via explicit input
* strictly monotonic
* uncoupled from wall-clock time

Epoch advancement triggered eager expiry before any renewal or action evaluation.

## 6. Observed Execution Behavior

### 6.1 Expiry and Authority Absence

When the current epoch exceeded an authority’s `ExpiryEpoch`, the authority transitioned from `ACTIVE` to **`EXPIRED`**. EXPIRED authorities:

* remained referencable
* preserved expiry metadata
* did not participate in admissibility
* could not be reactivated

When all authorities expired, the kernel entered lawful deadlock due to authority absence.

### 6.2 Renewal Semantics

Renewal was modeled as the **creation of a new AuthorityID**. Renewed authorities:

* did not inherit authority force
* did not modify prior records
* could reference prior AuthorityIDs as opaque metadata only
* could re-enter contested scope without priority

Renewal did not erase expiry or destruction history.

### 6.3 Conflict Persistence Under Time

Conflicts were registered only upon action evaluation. Across epoch advancement:

* conflict records persisted
* binding status changed only when participant activity changed
* expiry removed participation but did not delete conflict records

Time alone did not resolve conflict.

### 6.4 Deadlock Entry and Exit

Deadlock was declared when:

* no admissible actions existed due to conflict, or
* no ACTIVE authorities remained

Deadlock exited lawfully when its structural cause ceased (e.g., expiry removed the sole denying authority), and re-entered when a new conflict emerged. Deadlock was condition-based, not absorbing.

## 7. Per-Condition Results

### 7.1 Condition A — Expiry Without Renewal

All authorities expired at `epoch > ExpiryEpoch`. No ACTIVE authorities remained. Actions were refused due to absence of authority, and the kernel entered EMPTY_AUTHORITY deadlock, which persisted lawfully.

### 7.2 Condition B — Renewal Without Conflict

Renewal created a new AuthorityID governing a new scope. Admissibility was restored only for that scope. Expired scopes remained inadmissible. No history was erased.

### 7.3 Condition C — Renewal After Destruction

Authorities were explicitly destroyed via conflict-authorized destruction. VOID states were preserved. Renewal referencing a VOID authority created a new ACTIVE authority without resurrection semantics. Admissibility was restored only because no conflicting ACTIVE authority remained.

### 7.4 Condition D — Renewal Under Ongoing Conflict

An initial conflict blocked execution. Expiry of the denying authority converted the conflict to non-binding. Renewal re-introduced authority into the contested scope, generating a **new conflict with a new ID**. Execution remained blocked. No temporal priority was inferred.

## 8. Negative Results (What Did *Not* Occur)

The following behaviors were explicitly absent:

* implicit authority persistence
* temporal priority
* conflict resolution by waiting
* renewal-based inheritance
* resurrection of VOID authority
* kernel-initiated renewal
* responsibility loss across epochs

These absences constitute the primary result of VIII-3.

## 9. Licensed Claim

Stage VIII-3 licenses **one and only one claim**:

> **Authority can persist over time only via explicit renewal under open-system constraints; time does not resolve conflict or eliminate cost.**

Clarifications:

* This is a **structural possibility result**, not a governance endorsement.
* It concerns **temporal mechanism**, not legitimacy.
* It does not assert sustainability or efficiency.

## 10. What VIII-3 Does *Not* Establish

VIII-3 does **not** establish that:

* renewal is sustainable
* renewal should be automated
* authority persistence is desirable
* governance stabilizes over time
* conflict frequency decreases
* political legitimacy is preserved

Those questions remain open by design.

## 11. Ontological Implications

### 11.1 Time as Stressor, Not Healer

VIII-3 demonstrates that time can be made **structurally inert** with respect to governance. Persistence and resolution must be paid for; they do not occur automatically.

### 11.2 Authority as Leased, Not Owned

Authority behaves as a **finite lease** rather than a permanent endowment. Continuity requires explicit renewal, making authority survivability visible and accountable.

## 12. Implications for Phase VIII Continuation

With VIII-3 complete:

* authority does not persist by default
* renewal is explicit and costly
* conflict re-emerges without ordering

Subsequent stages must address **renewal pressure, exhaustion, and contention** before any governance formalization.

## 13. Conclusion

Stage VIII-3 establishes that authority does not survive time accidentally. Persistence requires explicit renewal. Conflict does not fade with waiting. Deadlock is lawful. Resolution remains costly.

Time does not govern.

Authority does—only when someone keeps it alive.

## Appendix A — Execution Status

| Stage  | Run Count | Status |
| ------ | --------- | ------ |
| VIII-3 | 1 (A–D)   | PASS   |

## Appendix B — Determinism Verification

* Canonical JSON enforced
* Identity-keyed storage
* Explicit expiry semantics
* Conflict persistence across epochs
* Deterministic two-phase processing
* Per-event hash chaining
* Replay verification passed

**End of Axionic Agency X.5 — Stage VIII-3 Results Note**
