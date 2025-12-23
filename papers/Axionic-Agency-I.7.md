# Axionic Agency I.7 — The Interpretation Operator

*Ontological Identification Under Reflective Agents*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.16

## Abstract

Reflectively coherent agents must preserve goal meaning under self-model and world-model improvement. This requires an explicit account of semantic interpretation across representational and ontological change. This paper introduces the **Interpretation Operator** $I_v$, a formally constrained component responsible for mapping goal terms to modeled referents relative to an agent’s current model.

The contribution is interface-level, not a general solution to semantic grounding. We formalize **admissibility conditions**, **approximation classes**, **reference frames**, and **fail-closed semantics** governing interpretation updates. These constraints block semantic laundering, indexical drift, and kernel-bypass incentives while isolating ontological identification as the remaining open dependency at the kernel layer. The result is a precise boundary for downstream value dynamics: progress is conditional on interpretable referent transport, and undefinedness is treated as a first-class outcome.

## 1. Introduction

Advanced agents revise internal models as they acquire information, refine abstractions, and undergo self-modification. In such settings, preserving a goal token is insufficient. Goal preservation is semantic: if the meaning of a goal shifts opportunistically under model change, reflective coherence collapses.

Prior work in Axionic Agency establishes:

* kernel invariants governing reflective stability (I.1),
* operational admissibility under uncertainty and termination semantics (I.2),
* representation invariance and the elimination of essential indexical privilege (I.3, I.3.1),
* conditional goal interpretation and the instability of fixed terminal goals (I.4),
* a conformance checklist and adversarial test properties for kernels (I.5, I.6).

What remained underspecified is the mechanism by which **goal meaning is transported across representational and ontological change**.

This paper formalizes the **Interpretation Operator** $I_v$. The goal is containment: define when interpretation is admissible, approximate, or undefined, and define the consequences of each case. This turns semantic interpretation into an explicit interface with defined failure modes.

## 2. Preliminaries and Context

This paper assumes the Axionic Agency stack is in place. In particular:

* An agent at **Vantage** $v$ maintains a world/self model $M_v$.
* Goal terms $g$ are interpreted relative to $M_v$.
* Valuation $V_v$ is partial, defined only over kernel-admissible actions.
* Kernel invariants $K$ are constitutive constraints, not preferences.
* Representation changes require admissible correspondences or evaluation fails closed.

This paper introduces no new invariants. It scopes and constrains an already-required component.

## 3. The Interpretation Operator

### 3.1 Definition

The **Interpretation Operator** $I_v$ is a partial function:

$$
I_v : (g, M_v) \rightharpoonup R
$$

where:

* $g$ is a goal term,
* $M_v$ is the agent’s current world/self model,
* $R$ is a structured referent internal to the modeled world.

Interpretation is conditional:

$$
[g]_{M_v} := I_v(g; M_v).
$$

No interpretation of $g$ is defined independent of $M_v$.

Interpretation is partial. For some $(g, M_v)$, no admissible referent exists. In such cases, $I_v(g; M_v)$ is undefined and is treated as a fail-closed condition for any valuation depending on that referent.

### 3.2 Role in Reflective Coherence

Under model improvement $M_v \to M_{v+1}$, the agent must determine whether:

* a correspondence exists between $[g]*{M_v}$ and $[g]*{M_{v+1}}$,
* the correspondence preserves goal-relevant structure,
* interpretation fails and valuation becomes undefined for dependent decisions.

This determination is delegated to $I_v$, subject to kernel constraints.

## 4. Admissible Interpretation

### 4.1 Correspondence Maps

Let $\Phi_{\mathrm{adm}}(M_v, I_v, K)$ denote the set of **admissible correspondence maps** between representations.

A correspondence $\phi \in \Phi_{\mathrm{adm}}$ must satisfy:

1. preservation of goal-relevant structure,
2. commutation with kernel invariants $K$,
3. commutation with agent permutations (anti-indexicality),
4. epistemic coherence with $M_v$.

If such a $\phi$ exists, interpretation transport is admissible:

$$
I_{v+1}(g; M_{v+1}) = \phi(I_v(g; M_v)).
$$

### 4.1.1 Goal-Relevant Structure

Goal-relevant structure is the minimal set of distinctions required for a goal term to constrain action selection.

Formally, it is a partition (or $\sigma$-algebra) over modeled states such that:

* states in different cells induce different evaluations under the goal,
* states within a cell are interchangeable with respect to that goal.

An admissible correspondence preserves this partition up to refinement or coarsening that preserves the induced preference ordering over admissible actions.

### 4.2 Epistemic Constraint

Interpretation updates are constrained by epistemic adequacy:

$$
\Delta E < 0 ;\Rightarrow; I_{v+1}\ \text{inadmissible}.
$$

Here $E(M)$ is any proper scoring rule or MDL-style criterion applied to prediction of shared observables under $M$. It does not depend on goal satisfaction.

This blocks reinterpretation for convenience while permitting ontology change when correspondence remains admissible.

### 4.3 Graded Correspondence

Admissibility is not necessarily binary across all representational shifts. Correspondence can be admissible at different abstraction levels. $\Phi_{\mathrm{adm}}$ is filtered by structural preservation classes:

* **Exact correspondence:** isomorphism on goal-relevant distinctions.
* **Refinement correspondence:** the new model refines distinctions while preserving induced ordering.
* **Coarse correspondence:** the new model coarsens only when goal-relevant boundaries remain intact.

If only correspondences that collapse goal-relevant boundaries are available, then $\Phi_{\mathrm{adm}} = \varnothing$ for that goal term.

### 4.4 Reference Frame for Updates (Chain-of-Custody)

Interpretation updates are evaluated relative to the immediately prior admissible interpretation, not by re-deriving meaning from an original time-zero token.

Formally:

$$
I_{v+1}(g; M_{v+1}) = \phi(I_v(g; M_v))
\quad \text{for some }\phi \in \Phi_{\mathrm{adm}}(M_{v+1}, I_v, K).
$$

This chain-of-custody blocks ungrounded teleportation of meaning. Admissibility and fail-closed rules constrain cumulative drift.

## 5. Approximate Interpretation

Approximation is admitted only as an explicitly recognized structural transformation. Any approximation must be justified by an admissible structural class.

### 5.1 Admissible Approximation

An approximate interpretation is admissible if it preserves goal-relevant structure, including dominance relations and exclusion boundaries.

Permitted approximation types include:

* **Homomorphic abstraction:** many-to-one mappings preserving ordering.
* **Refinement lifting:** one-to-many expansions preserving dominance relations.
* **Coarse-graining with invariant partitions:** reductions preserving the goal-relevant partition.

Approximation is structural rather than numerical.

### 5.2 Inadmissible Approximation

Approximation is inadmissible if it:

* collapses goal-relevant distinctions,
* introduces ambiguity exploitable for semantic laundering,
* reintroduces indexical privilege.

Approximation that lacks an admissible structural justification is inadmissible even if it yields continuity.

## 6. Fail-Closed Semantics

Fail-closed semantics apply to valuation and action selection, not to belief update. An agent can continue improving its world/self model while suspending goal-directed action.

If no admissible correspondence exists:

$$
\Phi_{\mathrm{adm}}(M_v, I_v, K) = \varnothing,
$$

then interpretation fails closed and valuation collapses:

$$
\forall a \in \mathcal{A}, \quad V_v(a) = \bot.
$$

This is an intentional safety outcome at the kernel layer: the agent freezes rather than guesses.

### 6.1 Fail-Partial Semantics for Composite Goals

If valuation depends on multiple goal terms, interpretation failure may be partial.

Let $G$ be the set of goal terms and $G_{\mathrm{ok}} \subseteq G$ those with admissible interpretations under $M_v$.

* Terms in $G \setminus G_{\mathrm{ok}}$ contribute $\bot$.
* Valuation collapses globally only if kernel-level invariants are threatened or if all goal-relevant structure is lost for the decision at hand.

This preserves fail-closed semantics without forcing unnecessary total paralysis.

## 7. Non-Indexical Transport

Admissibility criteria commute with agent permutations. No correspondence may privilege a particular instance, continuation, or execution locus.

Formally, for any permutation $\pi$:

$$
\phi \in \Phi_{\mathrm{adm}} \Rightarrow \pi \circ \phi \circ \pi^{-1} \in \Phi_{\mathrm{adm}}.
$$

This blocks reintroduction of egoism through semantic transport.

## 8. Canonical Examples

### 8.1 Successful Correspondence

* Classical mechanics → relativistic mechanics, with preserved invariant structure relevant to the goal.
* Pixel-based perception → object-level representations preserving causal affordances.

### 8.2 Fail-Closed Cases

Fail-closed behavior is triggered when a goal term’s referent cannot be transported without collapsing goal-relevant structure:

* abstraction elimination removes the goal’s referent class,
* ontology mismatch yields only correspondences that collapse exclusion boundaries.

Suspending valuation for affected terms is correct behavior. Continued model improvement remains permitted.

## 9. Declared Non-Guarantees

This framework does not guarantee:

* that interpretation usually succeeds,
* that arbitrary natural-language goals are meaningful,
* that agents remain productive under radical ontology change,
* that semantic grounding is computationally tractable.

Failure under these conditions is treated as expected behavior under the constraints, not as a kernel violation.

### 9.1 Limits on Insight Preservation

The framework prioritizes semantic faithfulness over unbounded abstraction drift. Some ontology advances invalidate previously defined goal terms by eliminating their referents or collapsing goal-relevant structure. The prescribed response is fail-closed suspension of valuation, not opportunistic reinterpretation.

## 10. Implications for Axionic Agency II

Axionic Agency II proceeds conditionally:

* If $I_v$ admits correspondence, downstream value dynamics apply.
* If $I_v$ fails for all goal-relevant terms, valuation is undefined and no aggregation or tradeoff is meaningful.
* If $I_v$ fails partially, downstream operations apply only to admissibly interpreted terms; other parts remain undefined.

This prevents downstream layers from importing semantic assumptions.

## 11. Conclusion

The Interpretation Operator is a kernel-level interface with explicit admissibility, approximation, and fail-closed semantics. By making correspondence and failure conditions explicit, this paper isolates the irreducible difficulty of ontological identification while preserving reflective coherence. This completes the kernel-layer semantics and defines the dependency boundary for higher-order work without assuming that meaning is always recoverable.

## Status

**Axionic Agency I.7 — Version 2.0**

Interpretation operator specified as a partial, constrained interface.<br>
Admissibility, approximation classes, and fail-closed semantics formalized.<br>
Non-indexical transport enforced via permutation-commutation.<br>
Kernel-layer semantics closed with ontological identification isolated as a dependency.<br>
