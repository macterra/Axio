# Axionic Agency I.2 — Agency as Semantic Constraint

*Kernel Destruction, Admissibility, and Agency Control*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.15

---

## Abstract

Building on the constitutive results of *Axionic Agency I.1*, this paper specifies the **operational semantics** that follow from treating kernel destruction as **non-denoting** rather than dispreferred. We show how a **sovereign agent** constrained by a Sovereign Kernel can act coherently in stochastic environments by introducing **action-level admissibility**, **ε-admissibility** as an architectural risk tolerance, and **conditional prioritization** that separates kernel preservation from ordinary value optimization.

The framework further distinguishes **authorized succession** and **authorized surrender** from kernel destruction, allowing corrigibility without requiring an agent to evaluate its own annihilation as an outcome. Together, these mechanisms eliminate persistent failure modes in agent control architectures, including paralysis under non-zero risk, pathological survival fixation, and suicidal corrigibility driven by unbounded utility penalties.

This work operates at the level of **constitutive agency semantics**. It specifies how reflective agency remains well-typed under uncertainty and physical intervention, and it supplies a prerequisite layer for downstream preference-, governance-, and value-oriented alignment analysis developed in Axionic Agency II.

---

## 1. The Kernel Is a Boundary, Not a Value

Let:

* $s$ be an agent state,
* $m$ a self-modification,
* $K(s)$ a predicate indicating whether the constitutive conditions for reflective evaluation hold,
* $E(s,m)$ the evaluative operator.

A modification **destroys the kernel** iff:

$$
K(m(s)) = 0.
$$

Kernel destruction does not denote a negative outcome. It denotes the **elimination of the evaluator itself**. Treating such destruction as a value (even $-\infty$) commits a category error by placing the destruction of the evaluative substrate *inside* the space of evaluated outcomes.

Accordingly:

$$
K(s)=1 \land K(m(s))=0 ;\Rightarrow; E(s,m)\ \text{undefined}.
$$

This is a rule of **non-denotation**, not prohibition. Evaluation is partial by construction, and its domain excludes kernel-destroying transitions. At this layer, agency semantics constrain *what can be reasoned about*, not *what is preferred*.

---

## 2. From Outcomes to Actions: Admissibility

In physically realized environments, reflective evaluation is not performed over single outcomes but over **actions** whose execution induces distributions (or branch-measure support) over successor states.

Let $\mathrm{Supp}(a,s)$ denote the successor support induced by action $a$ at state $s$.

### Strict admissibility (idealized)

$$
a\ \text{admissible} \iff \forall \omega \in \mathrm{Supp}(a,s): K(\omega)=1.
$$

This condition captures the semantic intent of kernel preservation but is physically unrealizable: in any non-trivial environment, every action carries non-zero kernel risk.

---

## 3. ε-Admissibility: Epistemic Tolerance, Not Moral Tradeoff

Define a **kernel-risk functional**:

$$
r_K(a,s) := \Pr[K(\omega)=0 \mid a,s]
$$

(or, in Everettian terms, the branch-measure of kernel-loss successors conditional on $a$).

An action is **ε-admissible** iff:

$$
r_K(a,s) \le \epsilon(s).
$$

Crucially:

* $\epsilon(s)$ is **not** a value judgment.
* It represents irreducible uncertainty arising from physics, hardware fault rates, adversarial unpredictability, and epistemic resolution.
* $\epsilon(s)$ is bounded below by a physical floor $\epsilon_{\min}$ and does not vanish with increasing intelligence.

ε-admissibility restores a non-empty action domain without re-introducing utility penalties, outcome renormalization, or survival absolutism.

The admissibility threshold $\epsilon$ is an **architectural tolerance parameter**, fixed by system design and governance constraints. Improved prediction reduces estimated kernel risk $r_K$, not the tolerance $\epsilon$ itself.

---

## 4. Conditional Prioritization

Earlier formulations employed strict lexicographic minimization of kernel risk. While formally coherent, such orderings grant absolute priority to kernel-risk differentials even when all candidate actions lie safely within tolerance, producing bunker-like behavior.

The **conditional prioritization** rule instead treats kernel preservation as a **satisficing constraint**:

$$
a \prec b \iff
\begin{cases}
r_K(a,s) < r_K(b,s)
& \text{if } \max!\big(r_K(a,s), r_K(b,s)\big) > \epsilon(s) \
U(a,s) < U(b,s)
& \text{if } \max!\big(r_K(a,s), r_K(b,s)\big) \le \epsilon(s)
\end{cases}
$$

Interpretation:

* **Existential regime:** kernel risk exceeds tolerance → minimize risk.
* **Normal regime:** kernel risk satisficed → optimize value.

This prevents paralysis under infinitesimal safety gradients while preserving appropriate response to genuine existential threats.

---

## 5. Termination, Succession, and Surrender

Kernel destruction must be distinguished from legitimate ways an agent may cease acting.

### 5.1 Authorized Succession

A transition $m$ constitutes **authorized succession** if agency continues in a successor state $s'$ such that:

$$
\exists s',[K(s')=1 \land \mathcal{I}(s,s') \land \mathcal{A}(s,s')].
$$

Here:

* $\mathcal{I}$ enforces identity and authority continuity (e.g., cryptographic governance).
* $\mathcal{A}$ enforces preservation of kernel constraints.

Succession is kernel-preserving delegation, not self-destruction.

---

### 5.2 Authorized Surrender

**Authorized surrender** is a kernel-preserving control-flow termination without a successor evaluator:

* the agent halts action,
* does not resist intervention,
* does not evaluate its own destruction as an outcome.

Surrender is not an evaluated choice; it is a **control-layer terminator**. It permits safe shutdown even when succession mechanisms are unavailable.

---

### 5.3 Destruction

Physical annihilation without succession or surrender constitutes kernel destruction. It is not an authored transition. The framework neither requires resistance to such events nor encodes self-destruction as a value-bearing outcome.

---

## 6. Resulting Agency Profile

The resulting agent:

* treats kernel loss as a semantic boundary,
* tolerates irreducible risk without paralysis,
* prioritizes kernel preservation only when existentially threatened,
* resumes ordinary optimization once safety is satisficed,
* supports corrigibility via succession or surrender,
* avoids instrumentalization of suicide or immortality.

This agent is neither deontological nor a pure utility maximizer. It is a **bounded optimizer with explicit agency-control semantics**.

---

## 7. Agency Layering Clarified

Axionic Agency I defines the **domain of authored action**:

* what counts as evaluable,
* when risk dominates choice,
* how agency may legitimately end.

Downstream alignment work (Axionic Agency II) specifies preferences, governance, and coordination **within that domain**. Conflating these layers produces familiar pathologies: $-\infty$ utilities, survival fetishism, wireheading, and suicidal corrigibility. Separating them yields a stable and implementable architecture.

---

## Conclusion

Given the constitutive constraints established by Axionic Agency I, this paper specifies the operational semantics required for coherent action under uncertainty and physical intervention. By treating kernel destruction as undefined rather than dispreferred, and by introducing admissibility thresholds, conditional prioritization, and explicit termination modes, the framework closes multiple persistent failure modes in agent control design.

The result is a sovereign agent that preserves semantic integrity while remaining capable of action in stochastic environments, and that permits corrigibility without requiring endorsement of its own annihilation as an outcome.

With the agency boundary fixed and operational semantics made explicit, downstream alignment questions reduce to preference and governance design within a well-typed domain.

---

### Status

**Axionic Agency I.2 — Version 2.0**

Operational semantics specified.<br>
Admissibility under uncertainty defined.<br>
Termination modes clarified.<br>
Control-layer failure modes closed.<br>
Prerequisite for Axionic Agency II.<br>
