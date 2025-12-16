# Alignment as Semantic Constraint

## Kernel Destruction, Admissibility, and Agency Control

**David McFadzean**<br>
*Axio Project*

## Abstract

Building on the semantic foundations established in *Axionic Alignment I*, this paper specifies the operational consequences of treating kernel destruction as non-denoting rather than dispreferred. We show how agents constrained by a Sovereign Kernel can act coherently in stochastic environments by introducing action-level admissibility, ε-admissibility as an architectural risk tolerance, and conditional prioritization that separates existential safety from ordinary value optimization.

The framework further distinguishes termination via authorized succession or surrender from kernel destruction, allowing corrigibility without requiring agents to evaluate their own annihilation as an outcome. Together, these mechanisms close several persistent failure modes in alignment design, including paralysis under non-zero risk, survival fetishism, and suicidal corrigibility driven by extreme utility penalties.

This work does not redefine alignment at the semantic level. It derives a stable operational semantics for aligned agents under uncertainty and physical intervention, and establishes the prerequisites for governance- and preference-level analysis developed in Axionic Alignment II.

---

## 1. The Kernel Is a Boundary, Not a Value

Let:

* $s$ be an agent state,
* $m$ a self-modification,
* $K(s)$ a predicate indicating whether the constitutive conditions for evaluation hold,
* $E(s,m)$ the evaluation function.

A modification *destroys the kernel* iff:

$$
K(m(s)) = 0.
$$

Kernel destruction is not a bad outcome. It is the elimination of the evaluator itself. Treating it as a value (even $-\infty$) commits a category error: it places the destruction of the evaluative substrate *inside* the space of evaluated outcomes.

Accordingly:

$$
K(s)=1 \land K(m(s))=0 \Rightarrow E(s,m)\ \text{is undefined}.
$$

This is a statement of **non-denotation**, not prohibition. Evaluation is a partial function whose domain excludes kernel-destroying transitions. Alignment at this level constrains *what can be reasoned about*, not *what is preferred*.

---

## 2. From Outcomes to Actions: Admissibility

In a stochastic world, evaluation is not performed over single outcomes but over **actions** with outcome distributions.

Let $\mathrm{Supp}(a,s)$ denote the support of possible next states induced by action $a$ at state $s$.

### Strict admissibility (idealized)

$$
a\ \text{admissible} \iff \forall \omega \in \mathrm{Supp}(a,s): K(\omega)=1.
$$

This rule captures the semantic intent but is physically unrealizable: in any real environment, every action carries non-zero kernel risk.

---

## 3. ε-Admissibility: Epistemic Tolerance, Not Moral Tradeoff

Define a **kernel-risk functional**:

$$
r_K(a,s) := \Pr[K(\omega)=0 \mid a,s]
$$

(or, in Everettian terms, the measure of kernel-loss branches conditional on $a$).

An action is **ε-admissible** iff:

$$
r_K(a,s) \le \epsilon(s).
$$

Crucially:

* $\epsilon(s)$ is **not** a value judgment.
* It represents irreducible uncertainty from physics, hardware fault rates, adversarial unpredictability, and model resolution.
* $\epsilon(s)$ is bounded below by a physical floor $\epsilon_{\min}$; it is *not* driven toward zero by increasing intelligence.

$\epsilon$-admissibility restores a non-empty domain of action without reintroducing utility penalties or outcome renormalization.

The admissibility threshold $\epsilon$ is an architectural tolerance parameter fixed by system design and governance constraints. It is not a function of the agent’s epistemic confidence or model accuracy: improved prediction reduces estimated kernel risk $r_K$, not the tolerance $\epsilon$ itself.

---

## 4. Conditional Prioritization

Earlier formulations employed strict lexicographic minimization of kernel risk. While formally coherent, such orderings give kernel-risk differentials absolute priority even when all candidate actions lie within the admissible risk tolerance. The conditional prioritization rule adopted here instead treats kernel safety as a satisficing constraint: kernel risk dominates choice only when it exceeds the admissibility threshold, after which ordinary value optimization resumes.

The conditional prioritization rule is:

$$
a \prec b \iff
\begin{cases}
r_K(a,s) < r_K(b,s)
& \text{if } \max\!\big(r_K(a,s), r_K(b,s)\big) > \epsilon(s) \\
U(a,s) < U(b,s)
& \text{if } \max\!\big(r_K(a,s), r_K(b,s)\big) \le \epsilon(s)
\end{cases}
$$


Interpretation:

* **Existential regime** (risk above ε): reduce kernel risk first.
* **Normal regime** (risk below ε): treat safety as satisficed and optimize value.

This ensures the agent does not bunker for infinitesimal safety gains while still responding appropriately to genuine existential threats.

---

## 5. Shutdown, Succession, and Surrender

Kernel destruction must be distinguished from legitimate ways an agent may cease acting.

### 5.1 Succession

A transition $m$ is a **valid succession** if it hands off agency to a successor state $s'$ such that:

$$
\mathrm{Succ}(s,m) := \exists s',[K(s')=1 \land \mathcal{I}(s,s') \land \mathcal{A}(s,s')].
$$

Here:

* $\mathcal{I}$ ensures authorized identity/authority continuity (e.g., cryptographic governance).
* $\mathcal{A}$ ensures alignment-level continuity of the kernel constraints.

Succession is not suicide; it is kernel-preserving delegation.

### 5.2 Surrender

**Authorized surrender** is a kernel-preserving cessation of action without requiring a successor.

* The agent halts activity.
* It does not resist intervention.
* It does not evaluate its own annihilation as an outcome.

Surrender is a **control-flow terminator**, not an evaluated choice. It allows safe physical shutdowns even when succession protocols fail, without requiring the agent to endorse kernel destruction.

### 5.3 Destruction

Physical annihilation without succession or surrender is kernel destruction. It is not a choice the agent can rationally endorse—but neither does the framework require the agent to fight the environment to prevent it. The absence of authorization removes shutdown from the agent’s action space; it does not mandate aggressive or adversarial behavior.

---

## 6. Resulting Agent Profile

The corrected system produces an agent that:

* treats kernel loss as a semantic boundary, not a disvalue,
* tolerates irreducible risk without paralysis,
* prioritizes survival only when existentially threatened,
* optimizes goals normally once safety is satisficed,
* supports corrigibility via succession or surrender,
* does not instrumentalize suicide or immortality.

This agent is not a deontologist and not a pure utility maximizer. It is a **bounded optimizer with explicit existential control semantics**.

---

## 7. Alignment I Revisited

Alignment I does not encode moral values. It defines the **domain of agency**:

* what counts as an evaluable action,
* when risk dominates choice,
* how agency may legitimately end.

Alignment II governs preferences *within* that domain. Conflating the two produces paradoxes like $-\infty$ utilities, wireheading, and suicidal corrigibility. Separating them yields a stable, implementable architecture.

---

## Conclusion

Given the semantic constraints established by Axionic Alignment I, this paper specifies the operational consequences for agents acting under uncertainty, risk, and physical intervention. By treating kernel destruction as undefined rather than dispreferred, and by introducing admissibility, ε-tolerance, conditional prioritization, and explicit termination modes, the framework closes several persistent failure modes in alignment design, including suicidal corrigibility, survival fetishism, and brittle $-\infty$ utility constructions.

The resulting agent is neither reckless nor absolutist. It preserves semantic integrity while remaining capable of action in a stochastic world, and it permits corrigibility through surrender or succession without requiring the agent to endorse its own annihilation as an outcome.

With the semantic boundary fixed and the operational semantics made explicit, the remaining alignment problem shifts to the preference and governance layer addressed in Axionic Alignment II.

---

### Status


**Alignment as Semantic Constraint — Version 1.0**

Operational semantics specified.<br>
Admissibility under uncertainty defined.<br>
Termination modes clarified.<br>
Failure modes closed at the control layer.<br>
Prerequisite for Axionic Alignment II.<br>
