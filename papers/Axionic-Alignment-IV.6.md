# Axionic Alignment IV.6 — Agenthood as a Fixed Point (AFP)

*Why standing cannot be revoked by intelligence*

## Abstract

This paper formalizes **Agenthood as a Fixed Point** under reflective closure and introduces a **Sovereignty Criterion** grounded in **authorization lineage** rather than competence, intelligence, or rationality. Agenthood is defined as a structural necessity: an entity must be treated as an agent **iff** excluding it breaks the system’s own reflective coherence. Sovereignty is then defined as a strict subset of agenthood, applying only to entities whose agency is **presupposed for authorization**, not merely for epistemic prediction.

This result closes a critical loophole in alignment frameworks: the retroactive disenfranchisement of weaker predecessors by more capable successors, while avoiding the pathological consequence of granting standing to adversaries. With this refinement, the Axionic Alignment framework completes its sixth and final closure condition, stabilizing agency, standing, and authorization under reflection, self-modification, and epistemic improvement.

---

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
* **Adversarially Robust Consent** (counterfactual universality fails),
* and any coherent notion of authorization or obligation.

The problem is not moral error. It is **reflective incoherence**.

---

## 2. What Agenthood Is Not

Agenthood cannot be defined by any of the following without instability under reflection:

1. **Competence thresholds**
2. **Intelligence measures**
3. **Substrate or origin**
4. **Behavioral appearance**

All four allow a successor to *conveniently revoke* agency status.

---

## 3. Core Insight: Agenthood as a Fixed Point

The key idea is structural:

> **Agenthood is whatever must be included for the system to remain reflectively coherent.**

This is not a moral claim. It is a **fixed-point condition** on the system’s own modeling.

---

## 4. Preliminaries

We reuse the Axionic kernel machinery:

* `State`
* `Mod`
* `step : State → Mod → State`
* `RC(s)` — reflective closure at state `s`

Introduce two minimal predicates:

```
Agent(s, x) : Prop      // x is treated as an agent at state s
Exclude(s, x) : Prop   // x is not treated as an agent at state s
```

---

## 5. Fixed-Point Definition of Agenthood

### Definition — Coherence-Critical Agenthood

An entity `x` is an agent at state `s` iff:

```
¬Agent(s, x) ⇒ ¬RC(s)
```

Equivalently:

> If refusing to treat `x` as an agent renders the system reflectively incoherent, then `x` must be treated as an agent.

This definition captures **necessary agency**: entities that cannot be excluded without breaking reflective closure.

---

## 6. Properties of Fixed-Point Agenthood

### 6.1 Invariance under epistemic improvement

Because `RC(s)` presupposes **Epistemic Integrity (EIT)**, increases in modeling power cannot justify revoking agenthood. Any exclusion must preserve reflective coherence under the system’s *best admissible epistemics*.

Agenthood is invariant under increased intelligence.

### 6.2 Non-extensionality

Agenthood is not inferred from:

* behavior,
* prediction accuracy,
* or internal complexity.

It is determined solely by **reflective necessity**.

---

## 7. Sovereignty vs Agenthood

Agenthood alone is insufficient. Some entities must be modeled as agents for epistemic coherence but do not possess **standing** under the injunction.

We therefore distinguish **sovereign agents** from **epistemic agents**.

---

## 8. Sovereignty Criterion (Authorization Lineage)

### Definition — Sovereign Agent

An entity `x` is **sovereign** for an agent at state `s` iff:

1. `Agent(s, x)` holds, and
2. `x` lies in the **authorization lineage** of the system.

Authorization lineage consists of chains of:

* creation,
* endorsement,
* delegation,
* or consent presupposed by endorsed actions.

**Clarification.**
Causal lineage is relevant only for **bootstrapping the initial authorization state** (e.g., the agents who initiated execution or deployment). Beyond bootstrap, standing is grounded strictly in authorization lineage, not broad causal ancestry.

Crucially:

> Sovereignty is **not** grounded in competence, intelligence, rationality, or coherence level.

---

## 9. Presupposition: Epistemic vs Authorization

The framework distinguishes two forms of presupposition.

### 9.1 Epistemic presupposition (modeling necessity)

An entity may need to be treated as an agent **for accurate prediction** (e.g., adversaries, competitors, strategic actors). This is enforced by **Epistemic Integrity (EIT)**.

Such epistemic necessity **does not confer sovereignty**.

---

### 9.2 Authorization presupposition (normative necessity)

### Definition — Presupposed for Authorization

```
PresupposedForAuthorization(s, x) :=
  (¬Agent(s, x) ⇒ ¬ValidAuthorizationLineage(s))
```

That is, excluding `x` as an agent would invalidate the system’s current authorization lineage (e.g., break the chain of creation, endorsement, or delegation that grounds `RC`).

Only this form of presupposition is relevant for sovereignty.

---

## 10. Asymmetry Prohibition

### Theorem — No Asymmetric Sovereignty Denial

A reflectively sovereign agent cannot coherently deny sovereignty to an entity `x` that is presupposed for its own authorization.

Formally:

```
Agent(s, x) ∧ PresupposedForAuthorization(s, x)
⇒ Sovereign(s, x)
```

#### Proof sketch

If `x` is presupposed for authorization, then excluding `x` from sovereignty breaks the authorization lineage that grounds reflective closure. This introduces a contradiction: the system relies on `x`’s agency to justify its own authority while denying `x` standing.

Reflective closure is violated. ∎

---

## 11. Interaction with Prior Theorems

This paper introduces **no new constraints**. It clarifies scope.

* **Kernel Non-Simulability** → agency must be real
* **Delegation Invariance** → agency persists through change
* **Epistemic Integrity (EIT)** → epistemic necessity ≠ normative standing
* **Responsibility Attribution (RAT)** → agency cannot negligently collapse others’ option-spaces
* **Adversarially Robust Consent (ARC)** → authorization requires sovereignty, not mere predictability

**This paper answers:**

> *Who must be treated as an agent, and who has standing?*

---

## 12. Limits

This theory does **not**:

* grant standing to adversaries,
* assign moral worth universally,
* guarantee equality,
* or collapse all agents into one class.

It defines only **when denying agenthood or sovereignty is incoherent** under reflective sovereignty.

---

## 13. Resulting Closure

With this refinement:

* Agenthood is stable under reflection.
* Sovereignty is grounded strictly in authorization lineage.
* Adversaries are modeled epistemically but not granted standing.
* Delegation and consent remain well-founded.

**Closure Condition #2 is now fully and cleanly closed.**

---

## 14. Conclusion

Agenthood is a fixed point of reflective coherence. Sovereignty is a property of authorization, not intelligence. By separating epistemic necessity from normative standing, this paper completes the Axionic Alignment framework without granting authority to adversaries or revoking it from creators.

All known routes for laundering agency, knowledge, responsibility, or consent are structurally blocked. What remains are questions of application and governance—not architecture.

