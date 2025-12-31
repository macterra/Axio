# Axionic Agency V.4 — Open Agentic Manifolds and the Sacrifice–Collapse Theorem

*Failure Modes of Proxy Optimization in Multi-Agent Worlds*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2025.12.27

## Abstract

This paper proposes a structural replacement for utopian world-design grounded in agency preservation rather than outcome optimization. We define *open agentic manifolds* (OAMs) as classes of worlds that remain hospitable to heterogeneous, value-divergent agents by preserving exit, non-coerced differentiation, and agentic standing. We formalize *structural sacrifice patterns* as regimes where system objectives improve *instrumentally* through the non-consensual, asymmetric reduction of agency capacity for identifiable agent classes. The central result—the **Sacrifice–Collapse Theorem**—shows that any system operating under sustained optimization pressure and exhibiting a structural sacrifice pattern must violate at least one defining OAM property: exit admissibility, non-coerced differentiation, or agentic standing. We distinguish structural sacrifice from ordinary scarcity trade-offs and show how sacrifice patterns can be detected using practical monotone proxies for agency. The framework reframes classic anti-utopian intuitions (including Omelas) as instances of a general systems failure mode and yields design diagnostics relevant to political theory, institutional design, and alignment.

## 1. Motivation and Scope

A critique of utopia that stops at impossibility leaves a design vacuum. The relevant question becomes:

> **What replaces the blueprint ideal once “final ideal world-state” is rejected?**

This paper answers at the level of *architecture*. It evaluates not world-states but the constraint systems under which agents interact. The core claim is conditional and structural:

> **When a system is under pressure to optimize an objective $G$, and $G$ can be improved by degrading the agency capacity of a class of agents, the system will eventually enforce closure operators (exit suppression or coerced conformity) or erode that class’s agency standing.**

The target is the common failure mode of “benevolent optimization” drifting into authoritarian structure under pressure.

## 2. Agents, Agency Capacity, and Objectives

### 2.1 Agents

An **agent** is a system capable of:

1. representing counterfactual futures,
2. evaluating those futures under internal criteria,
3. acting to influence realized trajectories.

The analysis does not assume ideal rationality.

### 2.2 Agency Capacity

For each agent $i$, define an **agency capacity** function:

$$
A_i : W \rightarrow \mathbb{R}_{\ge 0}
$$

where $W$ is the space of world-states (or histories). $A_i(w)$ denotes the size or measure of the agent’s *non-coerced feasible future set* from $w$.

The theory uses only monotonicity: if an agent loses admissible options due to coercion, captivity, or enforced dependence, $A_i$ decreases.

**Operationalization note.** Exact computation of option-set measure is generally intractable. In practice, $A_i$ is tracked via monotone proxies that correlate with non-coerced feasible futures: exit cost, legal rights, mobility, asset control, bargaining power, credible-threat exposure, censorship constraint, and punishment for dissent. The diagnostics in Section 9 require only detecting *persistent directional pressure* against an identifiable class, not measuring $A_i$ precisely.

### 2.3 System Objective and Optimization Pressure

Let $G : W \rightarrow \mathbb{R}$ denote a **system objective**: welfare proxy, stability score, efficiency, growth, profit, security, or coordination throughput. $G$ is not assumed morally authoritative.

A system is under **optimization pressure** when it contains mechanisms that tend to select transitions increasing $G$ whenever feasible. This may be explicit (planning) or implicit (bureaucratic incentives, market selection, memetic competition).

The main theorem is conditional on sustained optimization pressure. Stagnant or decaying systems may still be oppressive, but the theorem characterizes the failure mode of *optimizing* regimes.

## 3. From World-States to World-Classes

Outcome-focused thinking asks which $w \in W$ is best. Architectural thinking asks which constraint systems keep multi-agent worlds coherent under divergence.

Let $\mathcal{W}_\Sigma \subset W$ denote a world-class defined by a constraint set $\Sigma$ (laws, norms, protocols, enforcement practices). The design problem becomes:

$$
\text{Choose }\Sigma\text{ such that }\mathcal{W}_\Sigma\text{ remains hospitable to heterogeneous agents under pressure.}
$$

## 4. Open Agentic Manifolds (OAMs)

### 4.1 Definition

A world-class $\mathcal{W}_\Sigma$ is an **open agentic manifold** if it satisfies:

1. **Value Non-Finality** — no world-state is privileged as a final convergent optimum.
2. **Non-Coerced Differentiation** — agents can pursue divergent values without forced compliance.
3. **Exit Admissibility** — agents can leave local equilibria without punitive loss of agency capacity.
4. **Local Coordination Without Global Closure** — coordination is permitted but remains contingent and revisable.
5. **No Standing Structural Sacrifice Substrate** — system performance does not depend instrumentally on the non-consensual, asymmetric reduction of agency capacity for identifiable agents.

Property (5) is the hinge. It does not ban scarcity or trade-offs; it bans architectures that optimize by eating agency.

### 4.2 Replacement Objective: Future Option Volume

The relevant evaluand is not a terminal state. It is the amount of non-coerced future differentiation available across agents.

Informally: how much open future remains accessible without coercion?

## 5. Rivalry vs. Structural Sacrifice

Scarcity alone does not imply exploitation. OAMs tolerate rivalry; they reject optimization on coerced asymmetry.

### 5.1 Rivalrous Trade-Offs

A **rivalrous trade-off** occurs when agents compete over finite resources such that one agent’s consumption reduces another’s options. This may decrease some $A_i$ locally.

Rivalry alone is not structural sacrifice because:

* the reduction is not *instrumental* to increasing $G$ via agency loss,
* effects may be symmetric or bargained,
* agents can often exit or renegotiate.

### 5.2 Standing Asymmetry

**Definition 5.1 (Standing Asymmetry).**
A world-class $\mathcal{W}_\Sigma$ exhibits standing asymmetry if there exists a non-empty subset of agents $S$ such that agents in $S$ can suffer reductions in $A$ without symmetric burden or retaliation capacity sufficient to neutralize the pressure.

### 5.3 Sacrifice Gradient

**Definition 5.2 (Sacrifice Gradient).**

$$
\gamma_i(w) = \frac{\partial G}{\partial(-A_i)}(w)
$$

A positive $\gamma_i$ indicates that reducing $A_i$ locally improves $G$.

### 5.4 Structural Sacrifice Pattern

**Definition 5.3 (Structural Sacrifice Pattern).**
A world-class $\mathcal{W}*\Sigma$ contains a structural sacrifice pattern if there exist $S \neq \varnothing$, a region $U \subset \mathcal{W}*\Sigma$, and $\epsilon > 0$ such that for all $w \in U$ there exists $i \in S$ with:

1. **Instrumentality:** $\gamma_i(w) \ge \epsilon$
2. **Asymmetry:** the loss is not offset by symmetric burdens sufficient to neutralize the incentive
3. **Non-consensuality:** agents in $S$ lack admissible exit or bargaining symmetry that would block the loss without punitive penalty

This excludes ordinary trade and voluntary scarcity effects.

## 6. Agency-Aligned Objectives

If $G(w) = \sum_i A_i(w)$ (or is monotone in each $A_i$), then $\gamma_i(w) \le 0$ everywhere and sacrifice gradients are eliminated by construction.

Such systems are **kernel-like**: they preserve agency rather than optimize terminal outcomes. The theorem targets the common case where $G$ is a proxy (efficiency, stability, welfare, profit) that diverges from agency under pressure.

## 7. The Sacrifice–Collapse Theorem

### 7.1 Assumptions

1. **Optimization Pressure:** dynamics favor transitions increasing $G$.
2. **Standing Asymmetry:** a subset $S$ exists as above.
3. **Structural Sacrifice Pattern:** $\mathcal{W}_\Sigma$ contains such a pattern on region $U$.

### 7.2 Theorem

**Theorem 7.1 (Sacrifice–Collapse).**
Under Assumptions 1–3, $\mathcal{W}_\Sigma$ cannot remain an open agentic manifold along trajectories originating in $U$. At least one of the following must occur:

* **(C1) Exit Suppression**
* **(C2) Coerced Conformity**
* **(C3) Agency Erosion**

Each constitutes manifold collapse.

### 7.3 Proof (Structural)

Fix $w_0 \in U$. By Definition 5.3, reducing $A_{i_0}$ for some $i_0 \in S$ yields a robust increase in $G$. Under optimization pressure, such transitions are repeatedly selected.

If agents in $S$ exit, preserving $G$ requires preventing exit (C1).
If agents refuse compliance, reliability is restored via coercion (C2).
If neither occurs, repeated exploitation of sacrifice gradients erodes $A_i$ (C3).

All cases violate OAM properties. ∎

## 8. Hirschman Grounding

These collapse modes correspond to the dynamics analyzed by **Albert O. Hirschman**:

* Exit suppression
* Voice suppression via coerced conformity
* Loyalty enforced through agency erosion

## 9. Diagnostics

Sacrifice patterns can be detected empirically by:

1. Exit threatening performance metrics
2. Dissent reclassified as defect
3. One-way dependence and asymmetric punishment
4. Performance gains correlated with constraint on a class

## 10. Omelas as Structural Witness

The Ones Who Walk Away from Omelas illustrates a visible sacrifice gradient: stability purchased by enforced asymmetry and blocked exit.

## 11. Conclusion

Open agentic manifolds do not deny scarcity. They deny **sacrificial optimization**.

> **If a system can improve by degrading a captive class’s agency, and it is under pressure to improve, closure or erosion follows.**

This boundary—not harmony or happiness—defines admissible world design.

