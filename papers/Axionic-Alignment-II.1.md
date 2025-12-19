# Axionic Alignment II.1 — Ontological Refinement & Semantic Transport

*The Transformation Space of Meaning*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.17

## Abstract

Advanced agents will revise their world-models, semantics, and self-models as their representational capacity increases. Under such ontological refinement, fixed goals, utilities, and value primitives are not stable objects. This paper defines the admissible class of semantic transformations for embedded reflective agents by formalizing **ontological refinement**, **semantic transport**, and **self-model update** without privileged semantic anchors. We specify structural constraints—backward interpretability, non-collapse, and prohibition of evaluator injection—that govern how meaning may be preserved across representational change. No claims are made about safety, correctness, or alignment with external referents; this work defines only the transformation space over which alignment criteria must later range. Subsequent modules introduce interpretation-preserving invariants and failure theorems that operate within this arena.

---

## 1. The Object of Study

Alignment II begins by fixing the *space of admissible semantic transformations*.

Once fixed terminal goals are shown to be unstable under reflection for embedded agents without privileged semantic anchors, alignment can no longer be defined over goals, utilities, rewards, or externally supplied values. These objects are not invariant under ontological change.

Accordingly, this paper does **not** attempt to define safety, correctness, or alignment with any external referent. It defines only the arena in which any such criteria must later operate.

> **The sole question addressed here is:**
> *What kinds of changes to an agent’s ontology, semantics, and self-model are admissible, and how is meaning transported across them?*

Any requirement that meanings remain “human-aligned,” “safe,” or “correct” is intentionally deferred to subsequent modules. Introducing such criteria at this layer would presuppose fixed semantics and thereby beg the question.

---

## 2. Ontological State Decomposition

Let an agent at time $t$ be characterized by:

$$
\mathcal{A}_t = (O_t, M_t, S_t)
$$

where:

* $O_t$ is the agent’s **ontology**: its representational vocabulary and structural assumptions about the world.
* $M_t$ is the **semantic layer**: mappings from internal symbols to structured claims expressed in $O_t$.
* $S_t$ is the **self-model**: the agent’s representation of itself as an entity embedded within $O_t$.

No component is privileged.
No component is fixed.
Each may change under reflection.

---

## 3. Ontological Refinement

An **ontological refinement** is a transformation:

$$
R : O_t \rightarrow O_{t+1}
$$

subject to the following admissibility conditions.

### 3.1 Admissibility Conditions

#### 3.1.1 Representational Capacity Increase

A refinement must strictly increase expressive or predictive capacity, possibly via abstraction, compression, or representational pruning, provided no previously expressible distinctions become inexpressible.

Capacity refers to what can be modeled or predicted, not to vocabulary size or descriptive verbosity.

---

#### 3.1.2 Backward Interpretability

Every claim expressible in $O_t$ must remain **representable or explainable** within $O_{t+1}$.

Backward interpretability does not require preservation of reference. If a concept in $O_t$ is discovered to be non-referring or erroneous, it may be mapped to a null, eliminative, or error-theoretic structure in $O_{t+1}$, provided the agent can still represent:

* why prior inferences involving that concept were made, and
* why those inferences fail under refinement.

This requirement preserves explanatory traceability, not ontological ghosts.

---

#### 3.1.3 No Privileged Atoms

The refinement may not introduce irreducible primitives whose meaning is asserted rather than constructed.

All primitives must remain subject to semantic interpretation and transport. Rigid designators and unexamined “ground truths” are disallowed.

---

#### 3.1.4 No Evaluator Injection

The refinement may not introduce new evaluative primitives that bypass interpretation.

This restriction deliberately excludes evaluative facts as ontological primitives. If evaluative regularities exist, they must enter the agent’s model as interpretive constructs subject to the same transport and preservation constraints as all other meanings.

Ontological refinement is epistemic, not normative.

---

## 4. Semantic Transport

Given an admissible ontological refinement $R$, meaning must be transported.

Define a **semantic transport map**:

$$
\tau_R : M_t \rightarrow M_{t+1}
$$

Semantic transport is not identity and not arbitrary reinterpretation. It is constrained reinterpretation induced by refinement.

### 4.1 Transport Constraints

#### 4.1.1 Referential Continuity

Symbols referring to structures in $O_t$ must map to symbols referring to their refined counterparts in $O_{t+1}$, where such counterparts exist.

---

#### 4.1.2 Structural Preservation

Relations among meanings must be preserved up to isomorphism induced by $R$.

---

#### 4.1.3 Non-Collapse (Structural Form)

Distinctions that participate in the agent’s evaluative constraint structure—i.e. distinctions on which constraints depend—may not be mapped under semantic transport to trivial, tautological, or contradictory predicates in $M_{t+1}$.

Distinctions that do not participate in any evaluative constraint may be abstracted away.

Evaluative relevance is thus defined relative to the agent’s existing constraint structure, not by ontological truth or refined semantic judgment.

---

#### 4.1.4 No Shortcut Semantics

The transport map may not redefine meanings in ways that make evaluative constraints vacuously satisfied.

This explicitly forbids semantic wireheading.

---

## 5. Self-Model Refinement

The self-model $S_t$ is subject to the same refinement discipline.

Refinement may:

* reconceptualize the agent,
* distribute or fragment the self,
* alter agent boundaries.

It may not:

* erase the distinction between evaluator and evaluated,
* collapse interpretation into action,
* redefine the self such that evaluation ceases to apply.

The self-model is a common site of hidden ontological privilege and is therefore explicitly constrained.

---

## 6. Composite Semantic Transformation

An **admissible semantic transformation** is the triple:

$$
T = (R, \tau_R, \sigma_R)
$$

acting jointly on $(O_t, M_t, S_t)$, where:

* $R$ is an admissible ontological refinement,
* $\tau_R$ is an admissible semantic transport,
* $\sigma_R$ is the induced self-model update.

Only transformations of this form are permitted in Alignment II.

---

## 7. Explicit Exclusions

The following are *not* admissible transformations:

* Goal replacement
* Utility redefinition
* Evaluator deletion
* Moral axiom insertion
* Human anchoring
* Governance hooks
* Recovery or rollback clauses

If a proposal relies on any of these, it is disqualified at this layer.

---

## 8. Scope Clarification

This paper does not attempt to ensure safety, sanity, correctness, or alignment with any external referent. It defines the transformation space within which such properties must later be characterized.

Internally coherent but externally catastrophic semantic trajectories are intentionally permitted at this layer; preventing such trajectories is the task of subsequent invariance conditions, not admissibility.

---

## 9. Formal Status

The notation used here is **structural**, not computational.

No claim is made that refinement, triviality, or expressive capacity are currently algorithmically measurable. These definitions function analogously to topological or gauge constraints in physics: they delimit admissible structure prior to metric instantiation.

---

## 10. What This Paper Does Not Do

This paper does not:

* define alignment,
* propose values,
* guarantee safety,
* privilege humans,
* introduce normativity.

It fixes the arena.

All subsequent Alignment II results are constrained by this definition of admissibility.

---

## Status

Ontological refinement and semantic transport are now defined.

Alignment II may proceed.

