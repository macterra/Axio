# Axionic Agency V.2 — Agency Conservation and the Sacrifice Pattern

*A Formal Analysis of Instrumental Harm in Modern Systems*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.26

## Abstract

This paper formalizes a recurrent failure mode in governance systems: the systematic destruction of individual agency as an instrumental means of achieving system-level objectives. We term this failure mode the **Sacrifice Pattern**. Using an agency-conservation framework grounded in comparative reachable-futures distributions and divergence-based harm metrics, we show that practices commonly framed as “collateral damage” or “necessary tradeoffs” are structurally isomorphic to ancient ritual sacrifice. The persistence of this pattern is explained not by malice or intent, but by institutional selection under standing asymmetry, responsibility diffusion, and cosmological abstraction. We derive precise admissibility conditions under which harm may be tolerated without becoming sacrificial, introduce robustness and auditability constraints to prevent ethics washing, and show how modern bureaucratic and algorithmic systems stabilize sacrificial regimes by suppressing moral gradients. The framework is diagnostic rather than prescriptive, providing concrete audit criteria for human and artificial governance under uncertainty.

## 1. Introduction

Human societies repeatedly converge on practices that destroy some lives, freedoms, or futures in order to preserve others. In ancient contexts, these practices were explicit: ritual sacrifice, infanticide, or exposure. In modern contexts, they are framed as **collateral damage**, **acceptable risk**, or **unavoidable tradeoffs**.

Despite surface differences, these practices share a common structure:

> individual agents are treated as fungible instruments for stabilizing or advancing system-level goals, without their consent, and under conditions where lower–agency-loss alternatives are not excluded by necessity.

This paper provides a mechanical account of that structure. The aim is not moral condemnation, but **formal diagnosis**: to identify when agency conservation fails, why such failures recur, and how they persist even in systems that explicitly reject sacrifice at the level of stated values.

## 2. Preliminaries and Assumptions

### 2.1 Agents and Agency

An **agent** is any entity that:

1. Possesses preferences or valuations,
2. Has the capacity for action selection,
3. Has standing against purely instrumental use.

**Agency** is defined operationally as the set of future trajectories an agent can still steer toward from a given vantage state.

No metaphysical claims about free will are required. Agency is treated as a structural property of systems embedded in constraints.

### 2.2 Vantage and Comparative Futures

Fix a vantage state $s$ at time $t_0$ for an agent $i$.

Let:

* $\Omega_i$ be the space of relevant future trajectories over a horizon $T$,
* $P_i^\pi(\omega \mid s)$ be the distribution over reachable futures induced by policy $\pi$.

All evaluations in this paper are **comparative**. No appeal is made to policy-free, “natural,” or morally privileged baselines.

## 3. Quantifying Agency Loss

### 3.1 Hard Loss and Soft Deformation

Agency loss has two analytically distinct components:

1. **Hard loss**: futures that become unreachable.
2. **Soft deformation**: futures that remain reachable but become statistically implausible.

Define hard loss between two feasible policies:

$$
H_i(\pi_1 \rightarrow \pi_2)
=
P_i^{\pi_1}\!\left(
\Omega_i \setminus \operatorname{supp}\!\left(P_i^{\pi_2}\right)
\right)
$$

Define soft deformation:

$$
K_i(\pi_1 \rightarrow \pi_2)
=
D_{\mathrm{KL}}\!\left(
P_i^{\pi_1}(\cdot \mid s)\,\|\,P_i^{\pi_2}(\cdot \mid s)
\right)
$$

### 3.2 Individual Agency Loss

Define individual agency loss as

$$
\Delta A_i(\pi_1 \rightarrow \pi_2)
=
\alpha\,H_i(\pi_1 \rightarrow \pi_2)
+
\beta\,K_i(\pi_1 \rightarrow \pi_2)
$$

with $\alpha,\beta>0$.

This captures:

* death and incapacitation,
* coercion and chilling effects,
* deprivation and developmental truncation.

### 3.3 Population-Level Loss and Standing

For a population $P$ with standing weights $w_i$,

$$
\mathcal{L}(\pi_1 \rightarrow \pi_2)
=
\sum_{i \in P}
w_i\,\Delta A_i(\pi_1 \rightarrow \pi_2)
$$

Non-uniform $w_i$ are permitted, but must be **explicit, justified, and owned**, as standing asymmetry is the enabling condition for sacrificial regimes.

## 4. Institutional Dynamics and Standing Asymmetry

### 4.1 Institutional Objectives

Institutions operate under objectives of the form

$$
J(\pi)
=
-\,G(\pi)
+
\lambda\,C(\pi)
$$

where $G(\pi)$ is goal attainment (stability, compliance, victory, growth), $C(\pi)$ is cost to decision-bearing actors (political, legal, reputational), and $\lambda$ is a tradeoff parameter.

Agency loss enters only insofar as it affects $C(\pi)$.

### 4.2 Standing Sensitivity

Define **standing sensitivity** as

$$
S_i
=
\left|
\frac{\partial C}{\partial \Delta A_i}
\right|.
$$

Standing asymmetry exists when

$$
\mathbb{E}[S_i \mid i \in V]
\ll
\mathbb{E}[S_j \mid j \in D],
$$

where $V$ is a victim-candidate class and $D$ the decision-bearing class.

### 4.3 Optimization Without Rationality

No assumption is made that institutions explicitly optimize $J$. Optimization here is **evolutionary and institutional**, not cognitive.

Policies that improve $G$ while keeping $C$ low tend to persist via selection, imitation, and inertia, even under bounded rationality.

The Sacrifice Pattern is a **selection attractor**, not a plan.

## 5. The Sacrifice Pattern

### 5.1 Definition

A policy regime instantiates the **Sacrifice Pattern** when all of the following hold:

1. **Instrumentality**

$$
\exists i \in V :
\frac{\partial G}{\partial \Delta A_i} > 0.
$$

2. **Non-consent**
   Members of $V$ lack effective exit or veto.

3. **Standing asymmetry**
   Harm to $V$ weakly affects institutional cost.

4. **Epistemic avoidability**
   No documented, agency-conserving exploration of lower–agency-loss alternatives proportional to the stakes.

Instrumentality, not intent, is the bright line.

### 5.2 The Sacrifice Attractor

Under standing asymmetry and responsibility diffusion, policies that concentrate harm on $V$ while improving $G$ are locally stable outcomes of institutional selection.

Sacrifice is an attractor.

## 6. Agency-Conserving Exploration (Anti–Ethics-Washing Constraint)

Epistemic avoidability requires that the **process used to explore alternatives** be itself agency-conserving.

An exploration process $\mathcal{E}$ is admissible only if it satisfies:

1. Standing preservation
2. Model diversity
3. Gradient visibility
4. Auditability

Simulated exploration that suppresses victim gradients constitutes a second-order sacrificial violation.

## 7. Coercive Capacity: A Functional Definition

An agent $i$ possesses **coercive capacity** relative to a goal $G$ iff

$$
\frac{\partial G}{\partial A_i} \neq 0
$$

and $A_i$ cannot be reduced without diminishing enforced compliance, where $A_i$ denotes the agent’s capacity to apply violence, restrict exit, enforce compliance, or maintain coercive infrastructure.

Coercive capacity is defined **functionally**, not by role, identity, or narrative classification.

## 8. Gradient Suppression: PR as Modern Theology

Modern systems stabilize sacrificial regimes by suppressing moral gradients through aggregation, abstraction, responsibility diffusion, and cosmology tokens.

Formally,

$$
\frac{\partial C}{\partial \Delta A_i} \downarrow
\quad \text{while} \quad
\Delta A_i \not\downarrow
$$

This is functionally identical to theological sanctification in ancient sacrifice.

## 9. Admissibility Under Agency Conservation

A policy $\pi$ is admissible only if all conditions hold:

1. **Targeting**
2. **Minimality**
3. **Non-instrumentality**, requiring

$$
\frac{\partial G}{\partial \Delta A_i}
\approx
0
\quad
\text{for non-coercive agents};
$$

4. **Responsibility localization**
5. **Robustness**, such that admissibility is invariant across a reasonable range of $\alpha/\beta$.

Policies that rely on suppressing soft deformation terms fail.

## 10. Implications for Algorithmic Governance

Any governance system—human or artificial—that aggregates utility while hiding per-agent marginal agency loss is structurally sacrificial.

Safe governance systems must expose

$$
\forall i :
\frac{\partial C}{\partial \Delta A_i}
$$

as a first-class metric.

## 11. Conclusion

Agency conservation provides a unifying diagnostic for ethical failure across historical, bureaucratic, and algorithmic systems. Ritual sacrifice and modern collateral damage differ in presentation, not structure. Both arise when systems stabilize goals under standing asymmetry and responsibility diffusion.

Preventing sacrifice requires institutional design: restoring standing, enforcing exit and veto, localizing responsibility, auditing exploration, and rejecting abstractions that override individual agency.

Where those constraints are absent, sacrifice will recur—whatever name it is given.
