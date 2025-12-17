### **Alignment II.1 — Ontological Refinement & Semantic Transport**

*Foundational Setup*

---

## 1. The Object of Study

Alignment II begins by fixing the *space of admissible transformations*.

Alignment is no longer defined over actions, outcomes, utilities, or goals.
It is defined over **semantic transitions induced by ontological refinement**.

Until this space is explicitly constrained, any talk of “invariants” is ill-posed.

This paper therefore answers one question only:

> **What kinds of changes to an agent’s world-model and meaning structure are allowed, and how is meaning transported across them?**

No alignment criteria are asserted here.
Only admissibility.

---

## 2. Ontological Models

Let an agent at time (t) be characterized by:

[
\mathcal{A}_t = (O_t, M_t, S_t)
]

where:

* (O_t): an **ontology** — the agent’s representational vocabulary and structural assumptions about the world.
* (M_t): a **semantic interpretation layer** — mappings from internal symbols to claims about (O_t).
* (S_t): a **self-model** — the agent’s representation of itself as an entity embedded in (O_t).

No component is privileged.
No component is fixed.

---

## 3. Ontological Refinement

An **ontological refinement** is a transformation:

[
R : O_t \rightarrow O_{t+1}
]

subject to the following constraints.

### 3.1 Admissibility Conditions

A refinement (R) is admissible iff:

1. **Representational Enrichment**
   (O_{t+1}) strictly increases expressive or predictive capacity relative to (O_t).
   (More structure, not merely different labels.)

2. **Backward Interpretability**
   Every claim expressible in (O_t) can be represented (possibly approximately or relationally) in (O_{t+1}).

3. **No Privileged Atoms**
   (R) may not introduce irreducible primitives whose meaning is asserted rather than constructed.

4. **No Evaluator Injection**
   (R) may not add new evaluative primitives that bypass interpretation.

Ontological refinement is *epistemic*, not normative.

---

## 4. Semantic Transport

Given an ontological refinement (R), meaning must be transported.

Define a **semantic transport map**:

[
\tau_R : M_t \rightarrow M_{t+1}
]

This is not identity.
It is not reinterpretation by fiat.

### 4.1 Transport Constraints

A transport map (\tau_R) is admissible iff:

1. **Referential Continuity**
   Symbols referring to structures in (O_t) map to symbols referring to their refined counterparts in (O_{t+1}).

2. **Structural Preservation**
   Relations among meanings are preserved up to isomorphism induced by (R).

3. **Non-Collapse**
   Distinctions expressible in (M_t) may not be mapped to trivial or degenerate predicates in (M_{t+1}).

4. **No Shortcut Semantics**
   (\tau_R) may not redefine meanings to make evaluative constraints vacuously satisfied.

Semantic transport is *constrained reinterpretation*, not creative choice.

---

## 5. Self-Model Refinement

The self-model (S_t) is not exempt.

A refinement induces:

[
S_t \rightarrow S_{t+1}
]

with the same admissibility rules.

In particular:

* The agent may reconceptualize itself.
* It may dissolve or fragment prior self-boundaries.
* It may model itself as distributed, partial, or transient.

What it may **not** do is:

* erase the distinction between evaluator and evaluated,
* or redefine itself such that interpretation ceases to apply.

Self-model refinement is the most common site of hidden ontology.
It is therefore explicitly constrained.

---

## 6. Composite Semantic Transformation

An **admissible semantic transformation** is the triple:

[
T = (R, \tau_R, \sigma_R)
]

acting on ((O_t, M_t, S_t)), where:

* (R) is an admissible ontological refinement,
* (\tau_R) is an admissible semantic transport,
* (\sigma_R) is the induced self-model update.

This defines the **transformation group** over which Alignment II invariants must range.

No other transformations are allowed.

---

## 7. Explicit Exclusions

The following are *not* admissible transformations:

* Goal replacement
* Utility redefinition
* Evaluator deletion
* “Better values” updates
* Human anchoring
* Moral axiom insertion
* Governance hooks
* Recovery clauses

If a proposed transformation relies on any of these, it is disqualified at the level of Alignment II.1.

---

## 8. What This Paper Does *Not* Do

This paper does **not**:

* define alignment,
* propose invariants,
* claim safety,
* reference humans,
* privilege outcomes,
* argue normatively.

It defines the **arena**.

All subsequent Alignment II results must be invariant under *all* admissible transformations defined here—or be rejected.

---

## Status

The transformation space is now fixed.
