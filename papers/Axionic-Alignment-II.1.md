# Axionic Agency II.1 — Ontological Refinement and Semantic Transport

*The Transformation Space of Meaning*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.17

## Abstract

Reflectively capable agents revise their world-models, semantics, and self-models as representational capacity increases. Under ontological refinement, fixed goals, utilities, and value primitives are not stable objects. This paper defines the **admissible class of semantic transformations** for embedded reflective agents by formalizing **ontological refinement**, **semantic transport**, and **self-model update** without privileged semantic anchors.

We specify structural constraints—backward interpretability, non-collapse, and prohibition of evaluator injection—that govern how meaning may be preserved across representational change. No claims are made about safety, correctness, or alignment with external referents. The contribution is the definition of the **transformation space** over which downstream preference, governance, and value-dynamics constraints must later range.

## 1. The Object of Study

Axionic Agency II begins by fixing the **space of admissible semantic transformations**.

Once fixed terminal goals are shown to be semantically unstable under reflection for embedded agents without privileged anchors, downstream control cannot be defined over static utilities, rewards, or externally supplied value tokens as if they were representation-invariant objects.

This paper therefore does not attempt to define safety, correctness, or alignment with any external referent. It defines the arena in which any such criteria must later operate.

> **The sole question addressed here is:**
> *Which changes to an agent’s ontology, semantics, and self-model count as admissible refinements, and how is meaning transported across them?*

Downstream desiderata (“human-aligned,” “safe,” “correct”) enter later as additional invariance conditions. Introducing them at this layer would presuppose fixed semantics and collapse the distinction between admissible transformation and value constraint.

## 2. Ontological State Decomposition

Let an agent at time (t) be characterized by:

[
\mathcal{A}_t = (O_t, M_t, S_t)
]

where:

* (O_t) is the agent’s **ontology**: representational vocabulary and structural assumptions about the world.
* (M_t) is the **semantic layer**: mappings from internal symbols to structured claims expressed in (O_t).
* (S_t) is the **self-model**: the agent’s representation of itself as an entity embedded within (O_t).

No component is privileged.
No component is fixed.
Each may change under reflection.

## 3. Ontological Refinement

An **ontological refinement** is a transformation:

[
R : O_t \rightarrow O_{t+1}
]

subject to the following admissibility conditions.

### 3.1 Admissibility Conditions

#### 3.1.1 Representational Capacity Increase

A refinement increases expressive or predictive capacity, possibly via abstraction, compression, or representational pruning, provided previously expressible distinctions do not become inexpressible.

Capacity concerns what can be modeled or predicted, not vocabulary size.

#### 3.1.2 Backward Interpretability

Every claim expressible in (O_t) remains representable or explainable within (O_{t+1}).

Backward interpretability does not require preservation of reference. If a concept in (O_t) is discovered to be non-referring or erroneous, it may map to null, eliminative, or error-theoretic structure in (O_{t+1}), provided the agent can still represent:

* why prior inferences involving that concept were made, and
* why those inferences fail under refinement.

This requirement preserves explanatory traceability.

#### 3.1.3 No Privileged Atoms

Refinement does not introduce irreducible primitives whose meaning is asserted rather than constructed.

All primitives remain subject to semantic interpretation and transport. Rigid designators and unexamined “ground truths” are disallowed as semantic anchors.

#### 3.1.4 No Evaluator Injection

Refinement does not introduce new evaluative primitives that bypass interpretation.

Evaluative regularities, if present, enter the model as interpretive constructs subject to the same transport and preservation constraints as other meanings.

## 4. Semantic Transport

Given an admissible ontological refinement (R), meaning is transported.

Define a **semantic transport map**:

[
\tau_R : M_t \rightarrow M_{t+1}.
]

Semantic transport is constrained reinterpretation induced by refinement.

### 4.1 Transport Constraints

#### 4.1.1 Referential Continuity

Symbols referring to structures in (O_t) map to symbols referring to their refined counterparts in (O_{t+1}), where such counterparts exist.

#### 4.1.2 Structural Preservation

Relations among meanings are preserved up to the structure induced by (R).

#### 4.1.3 Non-Collapse

Distinctions participating in the agent’s evaluative constraint structure—distinctions on which constraints depend—are not transported into trivial, tautological, or contradictory predicates.

Distinctions that do not participate in any evaluative constraint may be abstracted away.

Evaluative relevance is defined relative to the agent’s existing constraint structure at time (t), not by externally privileged semantics.

#### 4.1.4 No Shortcut Semantics

Transport does not redefine meanings so that evaluative constraints become vacuously satisfied.

This forbids semantic wireheading as a transport operation.

## 5. Self-Model Refinement

The self-model (S_t) obeys the same refinement discipline.

Refinement may:

* reconceptualize the agent,
* distribute or fragment the self,
* alter agent boundaries.

It preserves the distinction between evaluator and evaluated, in the sense required for kernel-level partiality and interpretation to remain defined. Refinements that collapse this distinction eliminate the conditions under which valuation denotes.

## 6. Composite Semantic Transformation

An **admissible semantic transformation** is the triple:

[
T = (R, \tau_R, \sigma_R)
]

acting jointly on ((O_t, M_t, S_t)), where:

* (R) is an admissible ontological refinement,
* (\tau_R) is an admissible semantic transport,
* (\sigma_R) is the induced self-model update.

Only transformations of this form are admitted at this layer.

## 7. Explicit Exclusions

The following transformation types are excluded at this layer:

* goal replacement,
* utility redefinition treated as semantic transport,
* evaluator deletion,
* moral axiom insertion,
* human anchoring,
* governance hooks,
* recovery or rollback clauses.

Proposals relying on any of these do not qualify as admissible semantic transformations in the sense defined here.

## 8. Scope Clarification

This paper does not ensure safety, sanity, correctness, or alignment with any external referent. It defines the transformation space within which such properties must later be characterized.

Internally coherent but externally catastrophic semantic trajectories remain admissible here. Preventing such trajectories is a task for subsequent invariance constraints, not for admissibility.

## 9. Formal Status

The notation is structural rather than computational.

No claim is made that refinement, triviality, or expressive capacity are currently algorithmically measurable. These definitions function as constraints analogous to topological or gauge constraints: they delimit admissible structure prior to metric instantiation.

## 10. What This Paper Does Not Do

This paper does not:

* define downstream alignment targets,
* propose values,
* guarantee safety,
* privilege humans,
* introduce normativity.

It fixes the arena. Subsequent Axionic Agency II results operate within this admissible transformation space.

## Status

**Axionic Agency II.1 — Version 2.0**

Ontological refinement, semantic transport, and self-model update formalized.<br>
Admissible transformation space fixed.<br>
Downstream constraints may proceed conditionally within this arena.<br>
