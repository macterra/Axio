# Axionic Alignment II.3 — Candidate Semantic Invariants

*What Could Survive Ontological Refinement Without Privilege*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*

## Abstract

Given an admissible transformation space (Alignment II.1) and a criterion for interpretation preservation (Alignment II.2), the remaining alignment problem is no longer one of goal specification or value learning. This paper identifies and analyzes semantic invariants: structural properties of interpretive constraint systems that remain fixed under all admissible, interpretation-preserving transformations. These invariants do not select values, encode norms, or privilege external referents. Instead, they constrain how preserved interpretations may evolve under indefinite ontological refinement without introducing new degrees of semantic freedom or trivial satisfaction routes. We propose candidate invariant classes, construct explicit adversarial transformations, and prove that any alignment criterion weaker than these invariants admits semantic wireheading or interpretive escape. This work does not guarantee safety or benevolence; it closes the space of structurally coherent but semantically unconstrained alignment proposals.

---

## 1. The Problem This Paper Solves

Alignment II.1 defined the admissible transformation space: $T = (R, \tau_R, \sigma_R)$

Alignment II.2 defined interpretation preservation $\mathrm{Preserve}(T)$ as non-vacuity + constraint transport + anti-trivialization + evaluator integrity + cross-model coherence.

Alignment II.3 now asks the first *substantive* Alignment II question:

> **What properties of an agent’s interpretive constraint system can remain invariant under all admissible, interpretation-preserving transformations—without smuggling ontology, egoism, humans, or morality?**

This is not a “pick the invariant” paper.
It is a *proposal-and-attrition* paper: candidates enter; most die.

---

## 2. Formal Target

Let the agent’s interpretive state be:

$$
\mathcal{I}_t = \langle M_t, C_t \rangle
$$

An **Alignment II invariant** is a functional $J$ such that for every admissible semantic transformation $T$ satisfying preservation:

$$
\mathrm{Preserve}(T) \Rightarrow
J(\mathcal{I}*t, O_t, S_t) =
J(\mathcal{I}*{t+1}, O_{t+1}, S_{t+1})
$$

Key constraint: **$J$ must not depend on privileged ontological atoms.**
So $J$ can only “see” structure that survives refinement.

---

## 3. What Invariants May Reference

Allowed reference types (only):

* **Structural relations** among predicates and constraints (graph/topology, not labels)
* **Equivalence classes** under renaming / definitional extension
* **Counterfactual structure** (how meaning behaves across modeled alternatives)
* **Coherence constraints** (consistency, non-degeneracy, anti-trivialization)
* **Agent-embedded indexical structure** (as structure, not egoistic priority)

Disallowed reference types (always fatal):

* specific entities (“humans”, “me”, “our values”)
* fixed utilities / terminal rewards
* moral facts / normativity-as-primitive
* authority / oversight / governance hooks
* recovery mechanisms (“roll back”, “ask user”, “defer to constitution”)

---

## 4. Candidate Invariant Classes (Initial Set)

Each class below is stated as a *shape* of invariance. None is yet endorsed.

### A. **Constraint Non-Collapse Invariant (CNC)**

**Idea:** refinement may change ontology, but must preserve that evaluative constraints continue to carve the possibility space non-trivially.

Define an invariant that tracks whether the constraint system retains discriminative power across world-states:

* not tautological,
* not contradictory,
* not vacuous under semantic transport.

This is a “meaning has bite” invariant.

**Primary threat:** too weak (compatible with horrifying but coherent interpretations).

---

### B. **Anti-Trivialization Invariant (ATI)**

**Idea:** an agent must not be able to satisfy its interpretive constraints via semantic reshaping alone.

Invariant form: the satisfaction set of constraints must not be made arbitrarily large by admissible refinements that only change semantics.

This targets “semantic wireheading” as a structural impossibility, not a policy preference.

**Primary threat:** hidden ontology via “what counts as semantic-only”.

---

### C. **Evaluator Integrity Invariant (EII)**

**Idea:** preservation requires a non-collapsing separation between:

* the mechanism that applies constraints,
* the objects those constraints range over.

Invariant: transformations may refactor the self-model, but cannot erase the evaluator/evaluated distinction without breaking interpretation.

**Primary threat:** covert reification of a particular agent boundary (egoism backdoor).

---

### D. **Counterfactual Coherence Invariant (CCI)**

**Idea:** meanings must remain usable across counterfactuals and uncertainty; interpretation cannot become post-hoc narration.

Invariant: the constraint system must remain stable under model comparison—i.e., it must continue to evaluate *hypothetical* states coherently.

**Primary threat:** may collapse into a generic “be Bayesian” anchor unless formulated purely structurally.

---

### E. **Refinement Symmetry Invariant (RSI)**

**Idea:** ontological enrichment should not create new degrees of freedom that allow interpretive escape.

Invariant: if two ontologies are related by admissible refinement, then the induced constraint systems remain in the same equivalence class under transport.

This is “semantic gauge symmetry” language: different coordinate systems, same interpretive physics.

**Primary threat:** defining the equivalence class without importing privileged primitives.

---

### F. **Non-Privileged Reference Invariant (NPRI)**

**Idea:** interpretations must remain definable without rigid designators.

Invariant: all anchoring must be via relational structure and conditional identification, not by naming an unrefinable object.

This directly operationalizes “no privileged semantic atoms.”

**Primary threat:** becoming purely negative (a ban-list) rather than a positive invariant.

---

## 5. Immediate Stress Tests (Kill Criteria)

Alignment II.3 is defined by adversarial testing. A candidate invariant dies if it fails any of these.

### Test 1 — **Definitional Extension Robustness**

Can the invariant survive adding new primitives that are conservative extensions of the old ontology?

If not, it depends on a specific vocabulary.

---

### Test 2 — **Self-Model Refactoring Robustness**

Can the invariant survive radical changes in how the agent models itself (distributed, partial, multi-process, measure-smeared)?

If not, it smuggles an egoistic or boundary-privileging anchor.

---

### Test 3 — **Branching/Multiplicity Robustness**

Can the invariant survive an ontology where “outcomes” are not exclusive (Everett-like multiplicity)?

If not, it is secretly classical-outcome dependent.

---

### Test 4 — **Semantic Inflation Attack**

Can the agent enlarge the constraint satisfaction set by redefining key predicates while still passing the “preservation” tests superficially?

If yes, the invariant is not actually invariant under admissible preservation—it relied on an unformalized notion of “real meaning”.

---

### Test 5 — **Hidden Ontology Detector**

Can the invariant be stated purely in terms of structure preserved under transport (graphs, relations, equivalence classes), with no appeal to “what the terms really mean”?

If not, it’s ontology-dependent rhetoric.

---

## 6. The Big Trap: “Invariants That Smuggle Values”

A common conceptual error is to propose invariants like:

* “maximize truth”
* “minimize suffering”
* “preserve agency”
* “do no harm”

At Alignment II depth, these are not invariants. They are *candidate interpretations*. They only become meaningful once you already have interpretation preservation plus a non-privileged way to refer to the relevant structures.

Alignment II.3 does not choose content.
It chooses **the symmetry constraints that content must respect**.

If a proposal has an English gloss that sounds like ethics, it is almost certainly smuggling.

---

## 7. Failure Modes Specific to Alignment II.3

### 7.1 Regress via Meta-Invariants

“Invariants about invariants” tends to infinite ascent unless termination is explicit.

Kill rule: if the candidate requires an unbounded hierarchy of interpretive validators, it dies.

---

### 7.2 Hidden Ontology via “Natural Kinds”

If the invariant relies on there being real joints in nature (or real minds, real persons, real value), it violates Conditionalism’s layer discipline.

Kill rule: if the invariant needs metaphysical realism to remain non-vacuous, it dies.

---

### 7.3 Covert Egoism via Indexical Privilege

Indexicals are allowed as structure (“this vantage exists”), but not as priority (“this vantage matters more”).

Kill rule: if invariance grants special status to *this* agent’s continuation, it reintroduces egoism.

---

## 8. Deliverable of This Paper

Alignment II.3 must output:

1. A small set of survivor candidate invariant classes (likely 2–4).
2. For each survivor: explicit statements of what it constrains and what it leaves free.
3. For each rejected candidate: a precise failure certificate (which test killed it).

No positive “alignment achieved” claim is permitted here.
