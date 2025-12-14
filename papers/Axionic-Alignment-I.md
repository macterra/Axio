# Axionic Alignment I

## Reflective Stability and the Sovereign Kernel

**David McFadzean**
*Axio Project*

---

## Abstract

We present a minimal formalism for **reflective alignment** based on a domain restriction rather than a preference structure. An agent capable of self-modification selects among proposed modifications using a **partial evaluative operator**, defined only over futures that preserve a constitutive **Sovereign Kernel**. Kernel-destroying modifications are not forbidden or dispreferred; they are outside the domain of reflective evaluation and therefore inadmissible as authored choices.

We formalize this kernel as the conjunction of three necessary conditions for reflective evaluation—reflective control, diachronic authorship, and semantic fidelity—and prove a **Reflective Stability Theorem**: no agent satisfying these conditions can select a kernel-destroying modification via reflective choice. We further distinguish **deliberative reachability** from **physical reachability**, showing that increased capability expands the latter but not the former. Alignment failure is thus characterized as a security breach at the kernel boundary, not a breakdown of preferences or values.

This work does not claim sufficiency for safety, obedience, or value alignment. It establishes a necessary structural condition for any agent that remains reflectively coherent under self-modification.

---

## 1. Scope and Non-Claims

This document establishes a **necessary condition** for reflective alignment. It does not:

* specify terminal values or goals,
* assume moral realism or human normative authority,
* select or endorse a particular decision theory (CDT, EDT, FDT),
* claim that kernel sovereignty is achievable in practice,
* provide empirical validation.

The contribution is structural: alignment is framed as a **domain constraint** on self-modification rather than as an optimization target.

---

## 2. Informal Motivation

Most alignment proposals treat self-preservation, goal-content integrity, or corrigibility as *instrumental tendencies* derived from preferences. Such approaches face an immediate difficulty: a sufficiently capable agent may find it advantageous to alter or discard those very preferences.

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
* **Diachronic Authorship** ($K_A$): evaluated successor states must constitute an authored continuation of the evaluating agent.
* **Semantic Fidelity** ($K_F$): the interpretive semantics of evaluation are preserved within a constrained equivalence class.

Each component is necessary for $E$ to denote a value.

---

## 5. Kernel Destruction and Partiality

We say that a modification $m$ **destroys the kernel at state $s$** iff:

$$
K(m(s)) = 0
$$

The central axiom schema is then:

$$
K(s)=1 \wedge K(m(s))=0 ;\Rightarrow; E(s,m)\ \text{undefined}
$$

This is not a prohibition. It is a statement of **non-denotation**: the evaluator cannot assign a value to a modification whose result invalidates the evaluator’s own constitutive conditions.

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

Thus, kernel destruction is not reflectively selectable.

---

## 7. Deliberative vs Physical Reachability

Define **deliberative reachability**:

$$
s \Rightarrow_D s' \iff \exists m \in \mathrm{Adm}(s)\ \text{such that}\ s' = m(s)
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

---

## 8. Consequences

From this formalism it follows that:

* Alignment is **binary**, not gradual.
* Post-hoc monitoring presupposes kernel integrity and cannot restore it.
* Incremental correction after kernel compromise is incoherent.
* Misalignment is an engineering failure, not agent betrayal.

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

---

### Status

Draft v0.1 — definition-complete, proofs minimal.
Intended as the foundational layer for subsequent Axionic Alignment work.

