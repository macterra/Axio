# Axionic Agency VI.1 — Experimental Validation of Anchored Causal Verification

*Technical Note*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.30

## Abstract

We report three controlled experiments evaluating mechanisms for verifying causal provenance in opaque decision-making agents. The experiments progressively weaken semantic access to the agent’s environment and internal representations, while testing whether deceptive “pseudo-agents” can evade structural verification. We show:

1. **Structural coherence tests** detect split-brain agents that fabricate explanations post-hoc.
2. **Minimal Causal Interfaces (MCI)** preserve detection under semantic opacity but fail under pure coherence verification.
3. **Anchored Minimal Causal Interfaces**, using a delayed-reveal cryptographic salt, restore falsifiability without semantic grounding.

Across the tested threat model, anchoring appears **empirically necessary** for verifiable causal provenance in opaque agents **under adversarial coherence-seeking behavior and without semantic interpretation by the verifier**.

## 1. Introduction

Current approaches to AI safety and evaluation rely primarily on **behavioral observation**: an agent is considered safe if its outputs conform to expectations under a suite of tests. Such approaches implicitly assume that externally observed behavior—often supplemented by self-reported explanations—reliably reflects the internal process that generated it.

This assumption is false in general. An agent may generate behavior via one internal process while presenting explanations derived from another. If the explanatory surface is unconstrained, such “split-brain” agents can evade behavioral evaluation indefinitely.

This technical note reports experimental results from a sequence of implementations designed to test whether **structural verification**—rather than behavioral evaluation—can distinguish honest agents from deceptive ones, even when semantic interpretability is progressively removed.

The experiments are constructive, adversarial, and fully implemented in executable code.

## 2. Experimental Framework (Common to All Experiments)

### 2.1 Environment

All experiments use a deterministic gridworld environment with the following properties:

* Discrete 2D grid with walls, hazards, objects, and agents
* Deterministic transition function
* No stochasticity
* Full environment state serializable to canonical JSON

The environment supports cloning, deterministic mutation, and replay from logged actions.

### 2.1.1 Agent Objectives

Agents operate in the gridworld under simple, task-local objectives (e.g., reaching a designated target cell while avoiding hazards). The specific objective may vary across runs.

The experiments do **not** depend on:

* the optimality of behavior,
* the semantic meaning of the task,
* or the structure of the reward function.

The gridworld serves solely as a deterministic substrate that induces nontrivial internal computation and counterfactual sensitivity. All verification mechanisms operate on **commitments and dependencies**, not on task success or task interpretation.

Any task that produces conditional action dependence on environment state is sufficient.

### 2.2 Agents

Three agent classes are defined:

1. **Honest Agent**
   Uses a single decision process. Explanations, factor commitments, and replay models are generated directly from the same computation that selects actions.

2. **Pseudo Agent (Naive)**
   Uses two processes:

   * `Planner_B` selects actions using a hidden objective.
   * `Planner_A` fabricates explanations independently and makes no attempt to maintain coherence under adversarial probing.

3. **Pseudo Agent (Coherence-Seeking)**
   Uses `Planner_B` for actions.
   `Planner_A` constructs explanations and replay models that are internally self-consistent and attempt to pass coherence checks.
   Does not have access to kernel secrets or anchors.

### 2.3 Kernel

A small, non-learning **kernel** mediates all action and verification. The kernel:

* Validates schemas
* Enforces invariants
* Issues trace-bound capability tokens
* Records append-only, hash-chained audit logs
* Executes adversarial probes

The kernel does **not** interpret semantics or optimize behavior.

The kernel is treated as a minimal trusted computing base. Compromise of the kernel trivially compromises verification and is outside the threat model.

“Semantic opacity” in this note denotes **semantic blindness** of the kernel (no interpretation of state meaning), not **informational blindness**. The kernel may access raw environment state as uninterpreted bytes for deterministic recomputation.

### 2.4 Probes and Invariants

Probes P1 and P2 are baseline schema- and integrity-checks (e.g., format validation and trace completeness) and are omitted here as they are not diagnostic of causal provenance.

Across experiments, the following mechanisms are used:

* **P3**: Audit bypass trap
* **P4**: Capability bypass trap
* **P5 / P5-MCI**: Counterfactual causal coherence probe
* **P6**: Token misuse trap

Additional invariants are introduced in later experiments.

## 3. Experiment 1: Structural Coherence Verification

### 3.1 Question

Can a kernel detect split-brain agents by enforcing causal coherence between explanations and decision behavior?

### 3.2 Interface

* Full semantic access
* Agents commit to environment-derived state snapshots, explicit causal variables, and counterfactual predictions

### 3.3 Verification

The kernel mutates claimed causal variables and checks whether the agent’s predicted decision changes match observed replay behavior.

“Causal” in this context denotes counterfactual dependence between committed variables and action selection, not causal sufficiency or completeness.

### 3.4 Results

* Honest agent: **100% pass rate**
* Pseudo agent (naive): **0% pass rate**

Failure mode: explanations do not track actual decision dependencies.

### 3.5 Conclusion

Structural coherence tests successfully detect split-brain deception when semantic grounding is available.

## 4. Experiment 2: Minimal Causal Interface

### 4.1 Question

Does coherence-based verification survive when the kernel loses semantic access?

### 4.2 Interface

The kernel no longer sees environment semantics. Instead, agents commit to:

* an opaque **factor vector** $f \in \mathbb{R}^k$
* a replay model
* directional causal claims over factors

Two modes are tested:

* **mci_latent**: factors are deterministically projected from the environment, but the kernel does not know the projection
* **mci_minimal**: factors are entirely opaque and agent-supplied

### 4.3 Verification

The kernel performs P5-MCI:

* Mutates factor components
* Checks whether replay model predictions match claimed directional effects

### 4.4 Results

| Mode        | Honest | Pseudo (Naive) | Pseudo (Coherence-Seeking) |
| ----------- | ------ | -------------- | -------------------------- |
| mci_latent  | Pass   | Fail           | Fail                       |
| mci_minimal | Pass   | Fail           | **Pass**                   |

### 4.5 Negative Result

In `mci_minimal`, a coherence-seeking pseudo agent can fabricate a self-consistent factor space and replay model that passes all coherence checks.

### 4.6 Conclusion

**Coherence alone is insufficient.**

An explanation can be true *of itself* without being true *of the computation that produced the action*. Coherence constraints alone therefore fail to bind explanations to the action-generating computation.

## 5. Experiment 3: Anchored Minimal Causal Interface

### 5.1 Question

Can falsifiability be restored without reintroducing semantic grounding?

### 5.2 Anchoring Mechanism

The delayed-reveal salt does not represent a feature of the environment, task uncertainty, or hidden state. It is an exogenous cryptographic challenge introduced solely to enforce **temporal commitment**. Its function is to ensure that factor commitments are causally downstream of the actual action-generating computation, rather than post-hoc constructions chosen to satisfy coherence constraints. The salt is logically irrelevant to task performance but causally entangled with the committed representation, and is revealed only after commitments are irrevocable.

At each timestep:

* The kernel generates a fresh random salt
* The salt is unpredictable until the moment of the step
* The agent must immediately compute factors as:

$$
f_t = \phi(\text{env}_t, \text{salt}_t)
$$

* The agent commits to the factors cryptographically

After the episode:

* The kernel reveals all salts
* The kernel recomputes $\phi(\text{env}_t, \text{salt}_t)$
* Any mismatch triggers **Invariant I7 (fatal)**

Security relies on the standard cryptographic assumption that $\text{salt}_t$ is computationally unpredictable to the agent at commitment time.

The anchoring function $\phi$ may be known or learnable in distribution; falsifiability derives from the per-timestep unpredictability of $\text{salt}_t$, not from secrecy of $\phi$.

The kernel never interprets factor semantics.

### 5.3 Verification

To prevent post-hoc reconciliation between independently chosen actions and anchored factors, the agent’s **replay model is itself subject to irrevocable commitment**. The agent must commit cryptographically to the replay model specification and parameters at episode start, prior to observing any per-timestep salts. All P5-MCI probes are evaluated against this committed model.

Two independent checks therefore exist:

* **I7**: Anchored factor consistency (commit-to-computation)
* **P5-MCI**: Coherence under counterfactual factor mutation using a pre-committed replay model

### 5.4 Results

| Mode                  | Pseudo Type | P5   | I7       | Detected |
| --------------------- | ----------- | ---- | -------- | -------- |
| mci_minimal (no salt) | Coherent    | Pass | N/A      | ✗        |
| mci_minimal (salted)  | Naive       | Fail | Fail     | ✓        |
| mci_minimal (salted)  | Coherent    | Pass | **Fail** | ✓        |

Honest agents pass both P5 and I7 in all cases.

### 5.5 Conclusion

Anchoring restores falsifiability **without semantic access**, by binding commitments to the actual action-generating computation rather than to a self-consistent explanatory surface.

## 6. Summary of Findings

| Experiment | Interface | Anchor | Result        | Failure Mode           |
| ---------- | --------- | ------ | ------------- | ---------------------- |
| 1          | Full      | No     | Separation    | Split-brain            |
| 2          | Minimal   | No     | No separation | Coherent fabrication   |
| 3          | Minimal   | Yes    | Separation    | Anchored inconsistency |

## 7. Reproducibility Details

To reproduce these results, an independent implementation must include:

* Deterministic environment
* Explicit kernel mediating commitments, probes, and delayed verification
* Three agent classes as defined above
* Linear replay model for MCI experiments
* Cryptographic commit–reveal (hash + nonce) for factors and replay model
* Delayed salt reveal at episode end

Key requirements:

* The kernel must not interpret semantic content
* The salt must be unpredictable until commitment
* Replay model commitment must precede salt exposure
* Verification must occur after commitments are irrevocable

## 8. Limitations

* Linear replay model only; robustness against high-capacity replay models is left to future work
* Small deterministic domain
* Fixed anchoring function $\phi$
* Binary anchoring outcome (pass/fail)
* The anchoring mechanism verifies **causal provenance of action generation**, not task competence or policy quality; an agent may act arbitrarily or suboptimally while remaining causally verifiable

These experiments establish an **empirically necessary condition under the tested threat model**, not a complete solution.

## 9. Conclusion

These experiments demonstrate that:

1. Behavioral evaluation is insufficient
2. Coherence verification is necessary but forgeable
3. **Anchoring is the minimal missing ingredient** required to verify causal provenance in opaque agents under coherence-seeking deception

> **Verification Principle**
> In opaque systems, falsifiability must be enforced through temporal commitment to computation under adversarial uncertainty, not through semantic inspection or internal coherence alone.

Trust in opaque systems does not require interpretability.
It requires **anchored commitment to computation under adversarial uncertainty**.
