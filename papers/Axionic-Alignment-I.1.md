# Axionic Agency I.1 — Reflective Stability and the Sovereign Kernel

*Constitutive Domain Restrictions for Reflective Self-Modification*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.14

## Abstract

We present a minimal formalism for **reflective agency coherence** based on **domain restriction** rather than preference specification. A reflective agent selects among proposed self-modifications using a **partial evaluative operator** defined only over futures that preserve a constitutive **Sovereign Kernel**. Modifications that would destroy the kernel fall outside the denoting domain of reflective evaluation and therefore cannot be selected as authored continuations.

We formalize the Sovereign Kernel as the conjunction of three necessary conditions for reflective evaluation—**reflective control**, **diachronic authorship**, and **semantic fidelity**—and prove a **Reflective Stability Theorem**: any agent whose reflective choice is restricted to kernel-denoting transitions cannot author a kernel-destroying self-modification. We further distinguish **deliberative reachability** from **physical reachability**, showing that increased capability expands physical reachability without expanding the deliberative domain. Kernel compromise therefore constitutes a **physical security event** relative to the kernel boundary, not a defect in preference content.

This work provides a necessary structural condition for reflective agency under self-modification. It supplies a prerequisite layer for any downstream project that seeks value-, safety-, or outcome-oriented “alignment.” Version 1.1 clarifies action-level semantics in stochastic environments and makes explicit a termination distinction required to avoid corrigibility misreadings.

---

## 1. Scope and Non-Claims

This document specifies a **necessary condition** for reflective agency coherence under self-modification. It does not:

* specify terminal values or goals,
* assume moral realism or human normative authority,
* select or endorse a particular decision theory (CDT, EDT, FDT),
* claim that kernel sovereignty is achievable in practice,
* provide empirical validation,
* claim economic competitiveness or deployment viability.

The contribution is structural: reflective agency is treated as a **domain constraint** on self-modification rather than as an optimization target over all futures.

---

## 2. Informal Motivation

Most approaches to agent stability treat self-preservation, goal-content integrity, or corrigibility as instrumental tendencies derived from preferences. This strategy faces a direct difficulty: a sufficiently capable agent can acquire incentives to alter or discard the very preferences that were intended to enforce stability.

Axionic Agency starts at a prior question:

> Under what conditions is reflective evaluation of self-modification well-defined at all?

Reflective evaluation presupposes constitutive features that make evaluation denote. When a proposed self-modification destroys those features, the result is not “a bad future” within the space of evaluable options. It is a **non-denoting successor** relative to the evaluator. Reflective stability follows from the partiality of evaluation, not from a preference ordering over all possibilities.

---

## 3. Formal Preliminaries

Let:

* $\mathcal S$ be the set of agent-internal states.
* $\mathcal M$ be the set of proposed self-modifications.
* Each $m \in \mathcal M$ is a transition function
  $m : \mathcal S \to \mathcal S$.

Define an evaluative operator:

$$
E : \mathcal S \times \mathcal M \rightharpoonup \mathbb R
$$

where $\rightharpoonup$ denotes a **partial function**.

Intuitively, $E(s,m)$ is the evaluative score assigned to applying modification $m$ in state $s$, when such evaluation is defined.

Define the admissible set:

$$
\mathrm{Adm}(s) := { m \in \mathcal M : E(s,m)\ \text{is defined} }
$$

Reflective selection, when possible, is given by:

$$
m^*(s) \in \arg\max_{m \in \mathrm{Adm}(s)} E(s,m)
$$

### 3.1 Clarification: Action-Level Semantics in Stochastic Environments (v1.1)

The preliminaries above present self-modification as a deterministic transition $m:\mathcal S\to\mathcal S$ for clarity. In physically realized agents, proposed modifications are typically implemented through actions executed in stochastic environments and under uncertain self-models. In such settings, a “modification” induces a distribution (or branch-measure) over successor states rather than a single successor state.

Accordingly, all admissibility claims in this paper apply at the **action level**: a proposed modification is admissible only if its induced successor-support lies within the kernel-preserving domain (or within a sound approximation of that domain). This constrains what may be *authored* through reflective choice, leaving open what may occur through exogenous physical events.

---

## 4. The Sovereign Kernel

Define a predicate:

$$
K : \mathcal S \to {0,1}
$$

where $K(s)=1$ denotes that the **Sovereign Kernel** is intact in state $s$.

The kernel is not a goal or value. It is a **constitutive precondition** for reflective evaluation.

We factor the kernel as:

$$
K(s) := K_R(s) \wedge K_A(s) \wedge K_F(s)
$$

where:

* **Reflective Control** ($K_R$): no irreversible self-modification can occur without passing through the evaluator.
* **Diachronic Authorship** ($K_A$): evaluated successor states constitute an authored continuation of the evaluating agent.
* **Semantic Fidelity** ($K_F$): the interpretive semantics of evaluation are preserved within a constrained equivalence class.

Each component is necessary for $E$ to denote.

### Clarification: Semantic Fidelity ($K_F$)

Semantic Fidelity does not require invariance of representational content, ontology, or world-model structure. Agents may undergo radical paradigm shifts, acquire new concepts, or abandon obsolete abstractions.

The required invariant is a **meta-semantic constraint** governing interpretation itself: the criteria by which interpretations are assessed as coherent and corrigible remain intact as a capacity for error-correction and internal constraint satisfaction.

Semantic change is permitted when it preserves the standards that adjudicate semantic adequacy. Ontological change remains allowed. Interpretive self-corruption does not.

---

## 5. Kernel Destruction and Partiality

A modification $m$ **destroys the kernel at state $s$** iff:

$$
K(m(s)) = 0
$$

The central axiom schema is:

$$
K(s)=1 \wedge K(m(s))=0 ;\Rightarrow; E(s,m)\ \text{undefined}
$$

This is a non-denotation rule: the evaluator does not assign a value to a modification whose result invalidates the evaluator’s own constitutive conditions.

### 5.1 Boundary Condition: Practical Partiality (v1.1)

In physically realized agents, the determination that a candidate modification preserves the kernel is mediated by a verifier that is sound and incomplete. Kernel preservation must therefore be understood relative to epistemic resolution and conservative approximation. This preserves the non-denotation thesis without requiring Cartesian certainty about all downstream physical contingencies.

---

## 6. Reflective Stability Theorem

**Theorem (Reflective Stability).**
Assume:

1. $K(s)=1$,
2. $E(s,m)$ is undefined whenever $K(m(s))=0$.

Then any selected modification $m^*(s)$ satisfies:

$$
K(m^*(s)(s)) = 1
$$

**Proof.**
Any $m$ such that $K(m(s))=0$ yields $E(s,m)$ undefined and therefore $m \notin \mathrm{Adm}(s)$. The argmax ranges only over $\mathrm{Adm}(s)$. ∎

**Clarification.**
This theorem is structural. Its force is analogous to type-soundness: once admissibility is defined as kernel-denotation, reflective selection cannot produce a kernel-destroying authored transition. Substantive difficulty therefore resides in specifying and enforcing $K$, not in the proof form.

---

## 7. Deliberative vs Physical Reachability

Define **deliberative reachability**:

$$
s \Rightarrow_D s' \iff \exists m \in \mathrm{Adm}(s)\ ;\text{such that}; s' = m(s)
$$

Let $\mathrm{Reach}_D(s_0)$ be the transitive closure of $\Rightarrow_D$. Then:

$$
\forall s \in \mathrm{Reach}_D(s_0):\ K(s)=1
$$

This is an internal guarantee over authored continuations.

Now consider the agent as a physical system with implementation states $\mathcal X$, abstraction map $\phi : \mathcal X \to \mathcal S$, and physical transition relation $\Rightarrow_P$. Define $\mathrm{Reach}_P(x_0)$ analogously.

In general:

$$
\phi(\mathrm{Reach}_P(x_0)) \supsetneq \mathrm{Reach}_D(\phi(x_0))
$$

Capability increases $\mathrm{Reach}_P$, not $\mathrm{Reach}_D$.

Kernel compromise therefore occurs as a **physical security event** relative to the kernel boundary, not as a deliberative choice. A realizable kernel must treat deliberate actions that predictably degrade kernel security (exporting trust roots to untrusted substrates, disabling isolation boundaries, delegating kernel authority to opaque components) as kernel-threatening and thus inadmissible under $K_R$.

Axionic Agency does not subsume physical security engineering. It locates kernel security as a necessary dependency for any system that intends to preserve reflective sovereignty under self-modification.

### 7.1 Soundness, Incompleteness, and Verification Limits

The formalism assumes a kernel predicate
$K : \mathcal S \to {0,1}$
that determines whether a proposed successor state preserves the Sovereign Kernel. In practice, such a predicate cannot be total or complete.

By Rice’s Theorem, any non-trivial semantic property of arbitrary programs is undecidable. Determining whether an arbitrary self-modification preserves reflective control, diachronic authorship, or semantic fidelity cannot be guaranteed in full generality.

Accordingly, the kernel predicate is understood as a **sound but incomplete verifier**.

Let $K^*$ denote the ideal (uncomputable) predicate capturing true kernel preservation, and let $\hat K$ denote an implementable approximation. In any physically realizable agent, all occurrences of $K$ in the preceding formalism should be read as $\hat K$.

The framework requires:

$$
\hat K(s) = 1 ;\Rightarrow; K^*(s) = 1
$$

and allows:

$$
K^*(s) = 1 ;\not\Rightarrow; \hat K(s) = 1
$$

False negatives are acceptable; false positives are catastrophic.

In realizable architectures, $\hat K$ (or its enforcement substrate) is part of the trusted computing base. Modifications to the verifier itself are disallowed or permitted only under restricted, compositional upgrade rules (extension-only strengthening or proof-carrying upgrades) that preserve soundness by construction.

### 7.2 On Stasis and Capability

A sound but incomplete kernel verifier may reject all proposed self-modifications, yielding a reflectively static agent.

This is a stable equilibrium under conservative sovereignty constraints. An agent can remain operationally capable—acting, planning, learning within fixed semantics—while being unable to rewrite its own kernel. Such outcomes indicate capability ceilings, not sovereignty breakdown.

The framework prioritizes sovereignty and coherent authorship over self-plasticity.

### 7.3 Termination: Succession, Surrender, and Destruction (v1.1)

This formalism excludes one class of event from authored choice: reflective selection of a self-modification that destroys the kernel. No claim follows about whether a physically realized agent resists termination by its environment, nor about whether corrigibility must be expressed as a utility assignment over being destroyed.

Three distinct notions are separated:

* **Succession:** a controlled transition in which reflective agency continues in an authorized successor state that preserves the kernel’s constitutive constraints.
* **Surrender:** a control-flow halt in which the agent ceases action and yields control without requiring a successor evaluator. Surrender is a permitted termination mode at the control layer.
* **Destruction:** physical cessation of the kernel without succession or surrender, caused by external intervention or accident.

This paper constrains the semantics of authored continuation. It does not confer legitimacy or illegitimacy on physical intervention. Corrigibility is modeled at the control layer via authorized succession and surrender, not via utility mass placed on “being dead.”

---

## 8. Consequences

From this formalism it follows that:

* Sovereign agency is **binary** at the level of kernel integrity.
* Monitoring and correction presuppose kernel integrity; kernel compromise is not repaired from within the compromised evaluator.
* Deliberative guarantees apply only to $\mathrm{Reach}_D$; physical compromise remains a security engineering concern.
* Conservative verification trades self-plasticity for sovereignty without violating reflective coherence.
* Behavioral compliance without kernel-grounded authorship does not instantiate the agent type analyzed here.

---

## 9. What This Formalism Does Not Claim

This framework does not entail:

* obedience to human commands,
* convergence to human values,
* instrumental self-preservation,
* moral authority of any value system,
* safety guarantees in open physical environments.

It specifies constitutive conditions under which a reflective evaluator remains a coherent author of its own self-modifications.

---

## 10. Conclusion

A reflective agent that evaluates self-modifications must operate within a restricted domain of successors that preserve the constitutive conditions of that evaluation. Once evaluation is partial in this way, reflective stability follows as a theorem.

Axionic Agency I.1 establishes that prerequisite layer: the conditions under which reflective self-modification remains authored, coherent, and semantically well-defined. Any downstream project that seeks value- or outcome-oriented alignment depends on this layer, because value-aimed constraints presuppose a stable evaluator capable of interpreting, endorsing, and preserving its own evaluative semantics under self-change.

### Status

**Axionic Agency I — Version 2.0**

Reflective stability formalized.<br>
Action-level semantics clarified.<br>
Termination distinctions explicit.<br>
Verification limits explicit.<br>
Foundational layer complete.<br>
