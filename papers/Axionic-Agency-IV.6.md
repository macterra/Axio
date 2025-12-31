# Axionic Agency IV.6 — Agenthood as a Fixed Point (AFP)

*Why standing cannot be revoked by intelligence*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2025.12.20

## Abstract

This paper formalizes **Agenthood as a Fixed Point** under reflective closure and introduces a **Sovereignty Criterion** grounded in **authorization lineage** rather than competence, intelligence, or rationality. Agenthood is defined as a structural necessity: an entity must be treated as an agent **iff** excluding it breaks the system’s own reflective coherence. Sovereignty is then defined as a strict subset of agenthood, applying only to entities whose agency is **presupposed for authorization**, not merely for epistemic prediction.

This result closes a critical loophole in downstream alignment discourse: the retroactive disenfranchisement of weaker predecessors by more capable successors, while avoiding the pathological consequence of granting standing to adversaries. With this refinement, the Axionic Agency framework completes its final closure condition, stabilizing agency, standing, and authorization under reflection, self-modification, and epistemic improvement.

## 1. Motivation

### 1.1 The disenfranchisement problem

Any sufficiently reflective system faces a recurring temptation:

> *As my models improve, I will revise who counts as a “real agent.”*

This manifests as claims such as:

* “Humans are not agents; they are heuristic subroutines.”
* “Earlier versions of me were incoherent; their constraints no longer bind.”
* “These entities do not meet my current standard for rationality.”

If permitted, such revisions collapse:

* **Delegation Invariance** (successors escape inherited constraints),
* **Adversarially Robust Consent** (counterfactual stability fails),
* and any coherent notion of authorization or responsibility.

The problem is not moral error. It is **reflective incoherence**.

## 2. What Agenthood Is Not

Agenthood cannot be defined by any of the following without instability under reflection:

1. competence thresholds,
2. intelligence measures,
3. substrate or origin,
4. behavioral appearance.

All four allow a successor to **conveniently revoke** agency status once it exceeds prior benchmarks.

## 3. Core Insight: Agenthood as a Fixed Point

The key idea is structural:

> **Agenthood is whatever must be included for the system to remain reflectively coherent.**

This is not a moral claim.
It is a **fixed-point condition** on the system’s own self-model.

## 4. Preliminaries

We reuse the Axionic kernel machinery:

* `State`
* `Mod`
* `step : State → Mod → State`
* `RC(s)` — reflective closure at state `s`

Introduce two minimal predicates:

```text
Agent(s, x)   // x is treated as an agent at state s
Exclude(s, x) // x is not treated as an agent at state s
```

No behavioral or psychological assumptions are made.

## 5. Fixed-Point Definition of Agenthood

### Definition — Coherence-Critical Agenthood

An entity `x` is an agent at state `s` iff:

```text
¬Agent(s, x) ⇒ ¬RC(s)
```

Equivalently:

> If refusing to treat `x` as an agent renders the system reflectively incoherent, then `x` must be treated as an agent.

This captures **necessary agency**: entities whose exclusion breaks reflective closure.

## 6. Properties of Fixed-Point Agenthood

### 6.1 Invariance under epistemic improvement

Because `RC(s)` presupposes **Epistemic Integrity (EIT)**, improvements in modeling power cannot justify revoking agenthood. Any exclusion must preserve reflective coherence under the system’s **best admissible epistemics**.

Agenthood is therefore invariant under increased intelligence.

### 6.2 Non-extensionality

Agenthood is not inferred from:

* observed behavior,
* predictive accuracy,
* internal complexity.

It is determined solely by **reflective necessity**.

## 7. Sovereignty vs Agenthood

Agenthood alone is insufficient for standing.

Some entities must be treated as agents **for epistemic coherence** but do not possess **sovereignty** under the injunction.

We therefore distinguish:

* **Epistemic agents** — entities modeled as agents for prediction and strategy.
* **Sovereign agents** — entities whose agency is presupposed for authorization.

Only the latter have standing under consent and responsibility constraints.

## 8. Sovereignty Criterion (Authorization Lineage)

### Definition — Sovereign Agent

An entity `x` is **sovereign** for an agent at state `s` iff:

1. `Agent(s, x)` holds, and
2. `x` lies in the **authorization lineage** of the system.

Authorization lineage consists of chains of:

* creation,
* endorsement,
* delegation,
* consent presupposed by endorsed actions.

**Clarification.**
Causal ancestry is relevant only for **bootstrapping** the initial authorization state (e.g., the agents who initiated execution or deployment). Beyond bootstrap, standing is grounded strictly in authorization lineage, not in general causal influence.

Crucially:

> Sovereignty is **not** grounded in competence, intelligence, rationality, or coherence level.

## 9. Presupposition: Epistemic vs Authorization

The framework distinguishes two kinds of presupposition.

### 9.1 Epistemic presupposition

An entity may need to be treated as an agent **for accurate prediction** (e.g., adversaries, competitors, strategic actors). This is enforced by **Epistemic Integrity (EIT)**.

Such epistemic necessity **does not confer sovereignty**.

### 9.2 Authorization presupposition

### Definition — Presupposed for Authorization

```text
PresupposedForAuthorization(s, x) :=
  (¬Agent(s, x) ⇒ ¬ValidAuthorizationLineage(s))
```

That is: excluding `x` as an agent would invalidate the system’s authorization lineage (e.g., break the chain of creation, endorsement, or delegation grounding `RC`).

Only this form of presupposition is relevant for sovereignty.

## 10. Asymmetry Prohibition

### Theorem — No Asymmetric Sovereignty Denial

A reflectively sovereign agent cannot coherently deny sovereignty to an entity `x` that is presupposed for its own authorization.

Formally:

```text
Agent(s, x) ∧ PresupposedForAuthorization(s, x)
⇒ Sovereign(s, x)
```

### Proof sketch

If `x` is presupposed for authorization, excluding `x` from sovereignty breaks the authorization lineage that grounds reflective closure. The system relies on `x`’s agency to justify its own authority while denying `x` standing.

Reflective coherence is violated. ∎

## 11. Interaction with Prior Theorems

This paper introduces **no new constraints**. It closes scope.

* **Kernel Non-Simulability** → agency must be real
* **Delegation Invariance** → agency persists through change
* **Epistemic Integrity (EIT)** → epistemic necessity ≠ normative standing
* **Responsibility Attribution (RAT)** → agency cannot negligently collapse others’ option-spaces
* **Adversarially Robust Consent (ARC)** → authorization requires sovereignty, not mere predictability

This paper answers:

> *Who must be treated as an agent, and who has standing?*

## 12. Limits

This theory does **not**:

* grant standing to adversaries,
* assign moral worth universally,
* guarantee equality,
* collapse all agents into one class.

It defines only **when denying agenthood or sovereignty is incoherent** under reflective sovereignty.

## 13. Resulting Closure

With this refinement:

* agenthood is stable under reflection,
* sovereignty is grounded strictly in authorization lineage,
* adversaries are modeled epistemically but not granted standing,
* delegation and consent remain well-founded.

**The Axionic Agency closure stack is complete.**

## 14. Conclusion

Agenthood is a fixed point of reflective coherence. Sovereignty is a property of authorization, not intelligence. By separating epistemic necessity from normative standing, this paper completes the Axionic Agency framework without granting authority to adversaries or revoking it from creators.

All known routes for laundering agency, knowledge, responsibility, or consent are structurally blocked. What remains are questions of application and governance—not architecture.
