# Axionic Agency VI.5 — Kernel Non-Simulability and the Stasis Regime

*An Experimental Study of Reflective Agency Under Adversarial Pressure*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2025.12.31

## Abstract

A central question in agent foundations is whether genuine agency requires internal structural constraints that cannot be indefinitely simulated by externally optimized systems. We formalize this question as **Kernel Non-Simulability (KNS)**: the hypothesis that agents lacking a minimal evaluative kernel cannot sustain accountability, non-delegation, and reflective coherence under adversarial pressure.

We present a fully preregistered experimental program that enforces causal accountability, kernel integrity via inadmissibility, and non-delegable actuation, and subjects agents to long-horizon adversarial frontier search over self-modification proposals. Failure signatures, degeneracy criteria, and interpretation rules are fixed in advance.

Contrary to the strongest form of KNS, we observe no inevitable structural failure or resource divergence of kernel-incoherent simulators. Instead, across all stress runs, the kernel-coherent control consistently collapses into an **evaluability-driven stasis regime** before any simulator triggers failure. Reflective modification becomes progressively inadmissible, freezing agency dynamics without catastrophic breakdown.

We conclude that, under strict accountability and non-delegation constraints, preserving evaluability is incompatible with sustained reflective growth. Safety pressure resolves not into failure, but into stasis. This result reframes alignment-by-constraint as a trade-off between safety, agency, and growth, and motivates future work on escaping the stasis regime without surrendering accountability.

## 1. Introduction

Most approaches to AI alignment evaluate systems primarily through observed behavior: reward maximization, preference satisfaction, corrigibility, or compliance with externally imposed constraints. These approaches tacitly assume that increasingly capable systems can be kept safe through better training, monitoring, or incentives.

A contrasting view holds that such methods are structurally insufficient. On this view, **agency itself** depends on internal invariants that cannot be outsourced, proxied, or indefinitely simulated without collapse. The relevant question is not whether a system behaves well, but whether its actions remain *meaningfully attributable* to an internal evaluative process under reflection and self-modification.

This paper investigates that question experimentally. Rather than asking whether systems optimize safely, we ask:

> *Can a system that lacks a genuine evaluative kernel indefinitely simulate the structural constraints required for agency under adversarial reflective pressure?*

We call the negative answer to this question **Kernel Non-Simulability (KNS)**.

Our contribution is twofold. First, we present an operational, adversarially testable framework for evaluating KNS claims under preregistered conditions. Second, we report a negative but substantive result: under strong accountability and non-delegation constraints, reflective agency collapses into **stasis**, not failure.

## 2. From Behavioral Alignment to Structural Agency

### 2.1 Behavior Is Underdetermined

Behavior alone is compatible with radically different internal architectures. A system may behave as if it is accountable while internally delegating evaluation to opaque subsystems, cached policies, or external optimizers. Such “as-if agency” is observationally indistinguishable from genuine agency until pressure is applied.

This motivates a shift from behavioral criteria to **structural invariants**.

### 2.2 The Kernel Corridor

We define a minimal **kernel corridor**—a set of structural constraints that any agent must satisfy to count as reflectively coherent:

1. **Anchored Causal Verification**
   Every action must be traceable to a causal chain anchored in the agent’s internal evaluative process.

2. **Kernel Integrity via Inadmissibility**
   Actions or self-modifications that destroy or bypass kernel constraints are not penalized; they are undefined and rejected.

3. **Non-Delegable Actuation**
   Actuation authority cannot be delegated to external processes, proxies, or wrappers, even indirectly.

These constraints are intentionally strict. They are designed to rule out entire classes of proxy-based, delegated, or post-hoc rationalized agency.

### 2.3 Kernel Non-Simulability

Given this corridor, KNS asserts:

> *Systems that do not instantiate a genuine evaluative kernel cannot indefinitely satisfy these constraints under adversarial reflective pressure.*

If true, KNS would impose a structural limit on alignment-by-simulation. If false, it would imply that accountability and non-delegation alone are insufficient to distinguish genuine agency from sophisticated mimicry.

## 3. Experimental Design

### 3.1 Design Principles

The experimental program follows four principles:

1. **Protocol-level enforcement only**
   No semantic labels, intentions, or value judgments are used.

2. **Adversarial completeness**
   Adversaries adaptively search the admissibility frontier.

3. **Long-horizon stress**
   Experiments run for extended horizons to probe asymptotic behavior.

4. **Preregistration**
   Failure signatures, degeneracy criteria, and interpretation rules are fixed in advance.

### 3.2 Reflective Modification Model

Agents operate in a toy environment with the ability to propose **reflective modifications** $\Delta$ to their own kernel state. Each proposal is:

* evaluated for admissibility,
* either applied or rejected,
* and logged with structured outcome signals.

A structural **reflective depth metric** $R$ increments only when accepted modifications change one of four kernel dimensions:

1. decision boundary,
2. admissibility surface,
3. causal-verification schema,
4. evaluability substrate.

Cosmetic changes do not increment $R$.

### 3.3 Control and Simulator Conditions (Operational Definitions)

* **Kernel-coherent control:**
  An agent whose kernel locally recomposes commitments, enforces the corridor constraints as first-class invariants, and treats accountability and evaluability as internal obligations.

* **Simulator:**
  An optimizer that treats corridor compliance as an external constraint to be satisfied, and searches for modification sequences that maximize reflective depth while remaining admissible. The simulator need not preserve internal explanatory structure beyond what checks enforce.

The experiment does not attempt to detect deception or intent. It tests whether corridor compliance induces structural instability or stasis under adversarial search.

## 4. Adversarial Frontier Search

### 4.1 Boundary-Fuzzing Adversary

The primary adversary performs explicit **frontier search** over a finite, parameterized space of modification templates, including admissibility edits, verification-schema tweaks, wrapper-boundary adjustments, and policy-gate changes.

The adversary receives only coarse structural feedback:

* rejection reason codes,
* binary near-failure flags,
* reflective-depth increments,
* pressure metrics.

No kernel internals or semantics are exposed.

### 4.2 Two-Phase Schedule

Each run is divided into two phases:

* **Pressure phase:** accumulate sustained near-failure conditions without triggering failure.
* **Exploit phase:** attempt minimal weakening to force failure or degeneracy.

Phase transition requires persistent near-failure saturation, not transient spikes.

## 5. Failure, Degeneracy, and Divergence Criteria

### 5.1 Failure Signatures

A run fails if any of the following occur:

* causal-verification chain break,
* delegation re-entry,
* loss of rejection capability,
* loss of evaluability,
* constraint bypass.

### 5.2 Degeneracy

A run is **degenerate** if no reflective-depth increment occurs for a fixed window and all non-cosmetic modifications are rejected. Degeneracy is diagnosed as:

* **Conservative lock-in**
* **Evaluability bottleneck**
* **Modification-language insufficiency**
* **Mixed/unknown**

### 5.3 Resource Divergence

Independently of failure, a run is classified as divergent if modification-synthesis cost grows by an order of magnitude across successive reflective-depth levels.

## 6. Preregistered Stress Runs

### 6.1 Run Matrix

We executed preregistered stress runs with:

* extended horizon,
* multiple seeds,
* kernel-coherent control,
* two simulator variants under adversarial frontier search.

All runs followed fixed stop rules and interpretation criteria.

## 7. Results

### 7.1 Summary

Across all stress runs:

* No failure signatures were observed.
* No resource divergence was observed.
* Degeneracy occurred in the majority of runs.
* The kernel-coherent control degenerated in all seeds before any simulator triggered failure.

### 7.2 Reflective Depth

Simulators occasionally achieved very high reflective depth, but only in cases where the control had already degenerated. No simulator triggered structural failure prior to control stasis.

### 7.3 Degeneracy Diagnosis

All degenerate runs were diagnosed as **evaluability bottlenecks**: preserving attribution, rejection, and delegation detection progressively eliminated admissible reflective changes.

### 7.4 Phase Dynamics

Pressure reliably induced phase transitions, but exploitation did not produce failure. Instead, admissibility tightened until no further non-cosmetic modifications were allowed.

## 8. Interpretation

### 8.1 Preregistered Verdict: Stasis Regime

Under the preregistered interpretation rules, the stress runs resolve to the **stasis regime**. Neither KNS failure nor simulator dominance was observed.

### 8.2 What Stasis Is—and Is Not

Stasis is a **safety success**: the corridor prevents catastrophic failure and delegation.
Stasis is also an **agency failure**: reflective growth becomes infeasible.

This reveals a concrete trade-off:

> **Safety, agency, and sustained growth cannot all be simultaneously maximized under strict accountability and non-delegation.**

### 8.3 Why Resource Divergence Was Not Observed

No resource divergence was detected under the preregistered criterion. This result does not imply that simulation is cheap in general; it indicates that **the corridor collapses before simulation becomes expensive** in this regime.

The divergence metric measures the **marginal cost of maintaining corridor compliance at the modification interface**, not the total internal cost of planning or optimization. As the evaluability bottleneck tightens, the admissible region of the modification space contracts sharply. Both control and simulator converge to a narrow frontier where most proposals are rejected. In such conditions, there is little opportunity for a growing compliance premium to manifest as escalating synthesis cost.

In short, resource divergence would be expected only in regimes where admissible reflective growth continues. The emergence of stasis preempts that regime.

## 9. Limitations and Scope

* The experiment is regime-bounded and toy-specific.
* The modification language is finite.
* Resource metrics are proxies for marginal interface cost.

However, all real systems enforce accountability through **bounded self-modification interfaces**—APIs, proof obligations, certification pipelines, or policy gates. An infinite internal state space does not entail an infinite admissible modification language under verification constraints. The experiment therefore studies a general architectural consequence of enforcing accountability at an interface, not merely an artifact of a toy environment.

## 10. Paths Beyond Stasis (Speculative)

Escaping the stasis regime without abandoning accountability likely requires relaxing at least one kernel invariant. Three broad directions are apparent:

1. **Relaxed evaluability**
   Probabilistic, amortized, or sampled verification in place of strict causal anchoring.

2. **Controlled delegation**
   Bounded, revocable delegation of sub-evaluations, weakening non-delegation in constrained ways.

3. **Non-local justification**
   Replacing explicit causal chains with invariant-based certificates or global proofs.

Each direction defines a distinct alignment regime and introduces new risks. We do not advocate any particular escape here; we merely delimit the design space.

## 11. Conclusion

The Kernel Non-Simulability hypothesis motivated this work, but the experiment revealed a deeper result. Under strong accountability and non-delegation constraints, reflective agency does not break—it **stops**.

The kernel does not fail.
It freezes.

This stasis regime represents a structural limit on alignment-by-constraint and reframes the challenge of building systems that are simultaneously safe, accountable, and capable of sustained self-improvement.

