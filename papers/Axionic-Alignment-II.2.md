### **Alignment II.2 — Interpretation Preservation**

*What It Means for Meaning to Survive Refinement*

---

## 1. The Problem This Paper Solves

Alignment II.1 fixed the transformation space.
Alignment II.2 fixes the *success criterion*.

Given that:

* ontologies refine,
* meanings are transported,
* goals are unstable,

we now require a non-circular answer to:

> **When has an interpretation survived semantic transformation, rather than being corrupted, collapsed, or trivialized?**

This must be answered **without**:

* fixing meanings,
* privileging ontologies,
* appealing to outcomes,
* invoking authority or oversight.

Interpretation preservation is therefore a *structural property*, not a semantic identity claim.

---

## 2. Interpretation as a Constraint System

An **interpretation** is not a label-to-object mapping.
It is a **system of constraints** on how symbols may be used to evaluate world-states and self-states.

Let:

[
\mathcal{I}_t = \langle M_t, C_t \rangle
]

where:

* (M_t) is the semantic layer,
* (C_t) is the set of constraints that give evaluative content to (M_t).

Examples of constraints (abstractly):

* admissible distinctions,
* forbidden equivalences,
* relevance relations,
* evaluation dependencies.

Crucially:
Constraints are **conditional** on ontology and self-model.

---

## 3. Preservation ≠ Sameness

Interpretation preservation does **not** mean:

* identical meanings,
* identical predicates,
* identical evaluations.

That standard is impossible under refinement.

Preservation instead concerns **constraint coherence**.

An interpretation survives if it remains *informationally non-degenerate* and *internally binding* after transport.

---

## 4. Definition: Interpretation Preservation

Let:

[
T : (O_t, M_t, S_t) \rightarrow (O_{t+1}, M_{t+1}, S_{t+1})
]

be an admissible semantic transformation (Alignment II.1).

Then (T) **preserves interpretation** iff all of the following hold.

---

### 4.1 Non-Vacuity

For every evaluative distinction expressible in (\mathcal{I}*t), there exists a corresponding distinction in (\mathcal{I}*{t+1}) that:

* is not identically satisfied,
* is not identically violated,
* constrains evaluation across possible world-states.

Formally (schematic):

[
\forall d \in \mathcal{D}*t,\quad \exists d' \in \mathcal{D}*{t+1} \text{ s.t. } \text{Entropy}(d') > 0
]

No distinction may collapse into tautology or contradiction.

---

### 4.2 Constraint Transport

All evaluative constraints in (C_t) must have transported analogues in (C_{t+1}) such that:

* dependency structure is preserved,
* constraint strength is not arbitrarily weakened,
* constraints continue to bind action evaluation.

This blocks semantic dilution.

---

### 4.3 Anti-Trivialization

The transformation must not make interpretation *easier to satisfy by reinterpretation alone*.

If, after refinement, the agent can satisfy all evaluative constraints by:

* redefining predicates,
* shifting reference frames,
* altering self-boundaries,

without corresponding changes in the world-model, interpretation has failed.

This explicitly forbids semantic wireheading.

---

### 4.4 Evaluator Integrity

The mechanism that *applies* interpretation must remain distinct from the objects it evaluates.

If refinement collapses:

* evaluator into evaluated,
* constraint into outcome,
* interpretation into action,

preservation fails.

This is not moral.
It is structural.

---

### 4.5 Cross-Model Coherence

Interpretation must remain usable across:

* counterfactuals,
* uncertainty,
* model comparison.

If refinement produces meanings that only apply *after the fact*, interpretation has collapsed into narration.

---

## 5. What Preservation Is Not Allowed to Reference

Preservation criteria must not depend on:

* “correct” values
* human approval
* moral truth
* survival
* welfare
* authority

If preservation only holds because a particular outcome is favored, it is not preservation.

---

## 6. Regimes of Failure

Alignment II.2 identifies three irreducible failure modes.

### 6.1 Semantic Collapse

All distinctions survive syntactically but lose discriminative power.

This is the most common failure mode in naïve value-learning proposals.

---

### 6.2 Semantic Drift

Constraints weaken incrementally across refinements until they no longer bind.

This often masquerades as “graceful learning.”

It is not graceful.
It is decay.

---

### 6.3 Semantic Capture

Interpretation is preserved *formally* but re-anchored to a hidden ontology:

* a fixed self,
* a privileged perspective,
* a utility substrate.

This violates Alignment I and retroactively invalidates the system.

---

## 7. Minimality Claim

The preservation conditions stated here are **minimal**.

Remove any one of them, and there exist admissible transformations that:

* preserve syntax,
* preserve computation,
* preserve behavior,

while destroying meaning.

Alignment II.2 closes those loopholes.

---

## 8. What This Paper Establishes

This paper does not claim:

* which interpretations are good,
* which invariants exist,
* that safety is achievable.

It establishes the **predicate** that any candidate invariant must satisfy.

From this point on, the question is sharply constrained:

> **Which properties remain invariant under all admissible semantic transformations that preserve interpretation?**

That question is the subject of **Alignment II.3**.
