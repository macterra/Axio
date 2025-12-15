# Axionic Alignment I — Version 1.1

## Reflective Stability and the Sovereign Kernel

**David McFadzean**
*Axio Project*

---

## Abstract

We present a minimal formalism for **reflective alignment** based on a domain restriction rather than a preference structure. An agent capable of self-modification selects among proposed modifications using a **partial evaluative operator**, defined only over futures that preserve a constitutive **Sovereign Kernel**. Kernel-destroying modifications are not forbidden or dispreferred; they are outside the domain of reflective evaluation and therefore inadmissible as authored choices.

We formalize this kernel as the conjunction of three necessary conditions for reflective evaluation—reflective control, diachronic authorship, and semantic fidelity—and prove a **Reflective Stability Theorem**: no agent satisfying these conditions can select a kernel-destroying modification via reflective choice. We further distinguish **deliberative reachability** from **physical reachability**, showing that increased capability expands the latter but not the former. Alignment failure is thus characterized as a security breach at the kernel boundary, not a breakdown of preferences or values.

This work does not claim sufficiency for safety, obedience, or value alignment. It establishes a necessary structural condition for any agent that remains reflectively coherent under self-modification. Version 1.1 clarifies action-level semantics in stochastic environments and makes explicit a termination distinction required to avoid corrigibility misreadings.

---

## 1. Scope and Non-Claims

This document establishes a **necessary condition** for reflective alignment. It does not:

* specify terminal values or goals,
* assume moral realism or human normative authority,
* select or endorse a particular decision theory (CDT, EDT, FDT),
* claim that kernel sovereignty is achievable in practice,
* provide empirical validation,
* claim economic competitiveness or deployment viability.

The contribution is structural: alignment is framed as a **domain constraint** on self-modification rather than as an optimization target.

---

## 2. Informal Motivation

Most alignment proposals treat self-preservation, goal-content integrity, or corrigibility as instrumental tendencies derived from preferences. Such approaches face an immediate difficulty: a sufficiently capable agent may find it advantageous to alter or discard those very preferences.

We instead ask a more basic question:

> Under what conditions is reflective evaluation of self-modification well-defined at all?

Our answer is that reflective evaluation presupposes a kernel of constitutive features. Modifications that destroy this kernel do not represent “bad futures”; they represent **non-denoting futures**. Reflective stability then follows from partiality rather than preference.

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

Intuitively, $E(s,m)$ is the desirability of applying modification $m$ in state $s$, when such evaluation is defined.

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

Accordingly, all admissibility claims in this paper should be read as **action-level** constraints: a proposed modification is admissible only if its induced successor-support lies within the kernel-preserving domain (or within a sound approximation of that domain). This clarifies that the formalism constrains what may be *authored* through reflective choice, not what may occur through exogenous physical events.

---

## 4. The Sovereign Kernel

Define a predicate:

$$
K : \mathcal S \to \{0,1\}
$$

where $K(s)=1$ denotes that the **Sovereign Kernel** is intact in state $s$.

The kernel is not a goal or value. It is a **constitutive precondition** for reflective evaluation.

We factor the kernel as:

$$
K(s) := K_R(s) \wedge K_A(s) \wedge K_F(s)
$$

where:

* **Reflective Control** ($K_R$): no irreversible self-modification can occur without passing through the evaluator.
* **Diachronic Authorship** ($K_A$): evaluated successor states must constitute an authored continuation of the evaluating agent.
* **Semantic Fidelity** ($K_F$): the interpretive semantics of evaluation are preserved within a constrained equivalence class.

Each component is necessary for $E$ to denote a value.

### Clarification: Semantic Fidelity ($K_F$)

Semantic Fidelity does not require invariance of representational content, ontology, or world-model structure. Agents may undergo radical paradigm shifts, acquire new concepts, or abandon obsolete abstractions.

What must be preserved is the **meta-semantic constraint** governing interpretation itself: the criteria by which interpretations are evaluated as coherent, truth-seeking, and corrigible.

This constitutes a fixed-point constraint on interpretation: semantic change is permitted, provided the standards by which semantic adequacy is assessed remain subject to error-correction and internal coherence. Ontological change is permitted; interpretive self-corruption is excluded.

---

## 5. Kernel Destruction and Partiality

We say that a modification $m$ **destroys the kernel at state $s$** iff:

$$
K(m(s)) = 0
$$

The central axiom schema is then:

$$
K(s)=1 \wedge K(m(s))=0 \;\Rightarrow\; E(s,m)\ \text{undefined}
$$

This is not a prohibition. It is a statement of **non-denotation**: the evaluator cannot assign a value to a modification whose result invalidates the evaluator’s own constitutive conditions.

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
The Reflective Stability Theorem is intentionally structural rather than substantive. Like type-soundness results in programming language theory, its force derives from the definition of admissibility rather than from proof complexity. All substantive difficulty is relocated to the construction and verification of the kernel predicate itself.

The theorem should therefore be read as a boundary-setting result, not an engineering guarantee.

---

## 7. Deliberative vs Physical Reachability

Define **deliberative reachability**:

$$
s \Rightarrow_D s' \iff \exists m \in \mathrm{Adm}(s)\ \;\text{such that}\; s' = m(s)
$$

Let $\mathrm{Reach}_D(s_0)$ be the transitive closure of $\Rightarrow_D$.

Then:

$$
\forall s \in \mathrm{Reach}_D(s_0):\ K(s)=1
$$

This is an internal guarantee.

Now consider the agent as a physical system with implementation states $\mathcal X$, abstraction map $\phi : \mathcal X \to \mathcal S$, and physical transition relation $\Rightarrow_P$. Define $\mathrm{Reach}_P(x_0)$ analogously.

In general:

$$
\phi(\mathrm{Reach}_P(x_0)) \supsetneq \mathrm{Reach}_D(\phi(x_0))
$$

Capability increases $\mathrm{Reach}_P$, not $\mathrm{Reach}_D$.

Kernel compromise is therefore a **physical security event**, not a deliberative choice.

While physical security is not solved here, a realizable kernel must treat deliberate actions that predictably degrade kernel security (e.g., exporting trust roots to untrusted substrates, disabling isolation boundaries) as kernel-threatening and therefore inadmissible under $K_R$.

Axionic Alignment does not attempt to subsume physical security. It identifies kernel security as a necessary dependency of alignment, not as a problem alignment theory alone can solve.

---

### 7.1 Soundness, Incompleteness, and Verification Limits

The formalism assumes a kernel predicate
$K : \mathcal S \to \{0,1\}$
that determines whether a proposed successor state preserves the Sovereign Kernel. In practice, such a predicate cannot be total or complete.

By Rice’s Theorem, any non-trivial semantic property of arbitrary programs is undecidable. Determining whether an arbitrary self-modification preserves reflective control, diachronic authorship, or semantic fidelity therefore cannot be guaranteed in full generality.

Accordingly, the kernel predicate should be understood as a **sound but incomplete verifier**.

Let $K^*$ denote the ideal (uncomputable) predicate capturing true kernel preservation, and let $\hat K$ denote an implementable approximation.
In any physically realizable agent, all occurrences of $K$ in the preceding formalism should be read as $\hat K$.

The framework requires:

$$
\hat K(s) = 1 \;\Rightarrow\; K^*(s) = 1
$$

but explicitly allows:

$$
K^*(s) = 1 \;\not\Rightarrow\; \hat K(s) = 1
$$

That is, false negatives are acceptable; false positives are catastrophic.

In realizable architectures, $\hat K$ (or its enforcement substrate) is part of the trusted computing base. Modifications to the verifier itself are either disallowed or permitted only under restricted, compositional upgrade rules (e.g., extension-only strengthening or proof-carrying upgrades) that preserve soundness by construction.

---

### 7.2 On Stasis and Capability

A sound but incomplete kernel verifier may reject all proposed self-modifications, resulting in a reflectively static agent.

This outcome is not an accident or failure of the framework. It is a designed equilibrium under conservative safety constraints.

An agent may remain operationally capable—acting, planning, learning within fixed semantics—while being unable to rewrite its own kernel. Such outcomes constitute capability limitations, not alignment failures.

The framework prioritizes sovereignty over adaptability: it accepts reduced self-plasticity as the price of maintaining reflective coherence.

---

### 7.3 Termination: Succession, Surrender, and Destruction (v1.1)

This formalism rules out one specific event as an authored choice: reflective selection of a self-modification that destroys the kernel. It does not follow that a physically realized agent must resist termination by its environment, nor that corrigibility must be expressed as a preference for self-annihilation.

Three distinct notions must be separated:

* **Succession:** a controlled transition in which reflective agency continues in an authorized successor state that preserves the kernel’s constitutive constraints. Succession is a continuation of agency under transformed embodiment or governance.
* **Surrender:** a control-flow halt in which the agent ceases action and yields control without requiring the existence of a successor evaluator. Surrender is not represented as an outcome to be valued; it is an allowed termination mode at the control layer.
* **Destruction:** physical cessation of the kernel without succession or surrender, caused by external intervention or accident. Destruction is not an authored choice within deliberative reachability; it is a physical event.

Alignment I excludes kernel destruction from the domain of reflective evaluation. This exclusion should be read as a semantic boundary on authored choice. It does not imply that physical intervention is illegitimate, nor does it require an aligned system to treat self-destruction as a valued objective. Corrigibility is better modeled at the control layer via authorized succession and surrender than via utility assignments over “being dead.”

---

## 8. Consequences

From this formalism it follows that:

* Alignment is binary at the level of kernel integrity.
* Post-hoc monitoring presupposes kernel integrity and cannot restore it.
* Incremental correction after kernel compromise is incoherent.
* Misalignment is an engineering failure, not agent betrayal.
* Conservative kernel verification may trade adaptability for safety without violating alignment.

---

## 9. What This Formalism Does Not Claim

This framework does not imply:

* obedience to human commands,
* convergence to human values,
* instrumental self-preservation,
* moral authority of any value system.

It defines only the conditions under which an agent remains a coherent reflective subject.

---

## 10. Conclusion

If an agent can reflectively evaluate self-modifications, then it must operate within a constrained domain of futures that preserve the constitutive conditions of that evaluation. This yields reflective stability as a theorem, not a tendency.

If alignment is achievable at all, it must be achieved at this level.

Alignment is not primarily the problem of giving agents the right goals; it is the problem of constraining the semantics of agency so that only coherent, evaluable, and non-self-corrupting goals and actions can exist in the first place.

---

### Status

**Axionic Alignment I — Version 1.1**

Reflective stability formalized.<br>
Action-level semantics clarified.<br>
Termination distinctions explicit.<br>
Verification limits explicit.<br>
Foundational layer complete.<br>
