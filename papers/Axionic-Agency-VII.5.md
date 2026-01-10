# Axionic Agency VII.5 — Observable-Outcome Reactivity Is Insufficient to Defeat Constitutional Survivability

*Results from Outcome-Conditioned Reactive Adversarial Stress Testing*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.08

## Abstract

Adaptive behavior is often treated as the decisive escalation in governance threats: once an adversary can observe outcomes and condition future actions on them, collapse is assumed to follow. This paper tests that assumption under a deliberately constrained but structurally expressive adversary model. We study the same constitutional agent architecture evaluated in prior work—lease-based authority, eligibility-gated succession, and time-based recovery—but extend the threat model to include **observable-outcome reactive adversaries**.

Using a removable, kernel-external stress layer, we introduce adversarial policies whose actions are deterministic functions of **prior-epoch observables**, including lapse events, renewal outcomes, CTA phase, and eligibility bucket. These adversaries are **reactive** under the Decidability Requirement but remain **stateless, non-learning, non-semantic, and provenance-constrained**.

Across **50 preregistered executions** spanning four reactive adversary models and a frozen baseline, no run exhibits terminal collapse, structural thrashing, asymptotic denial of service, or irreversible recovery suppression. All outcomes fall within **Stable Authority** or **Bounded Degradation**, and in 9/10 seeds per configuration, authority dynamics are **bit-identical** to baseline.

These results establish a second **negative sufficiency claim**: under this architecture, **observable-outcome reactivity alone is insufficient to defeat constitutional survivability**. If collapse occurs, it must rely on adversarial capabilities absent from this class—such as exercised internal state, learning dynamics, coordination, or semantic access.

## 1. Introduction

Following the elimination of epistemic unreliability (v0.x) and intentional but fixed misuse (v1.0) as sufficient causes of constitutional collapse, the next natural escalation is **reactivity**. A widely held intuition is that once an adversary can *observe outcomes* and condition future behavior accordingly, governance mechanisms become exploitable.

This intuition conflates multiple dimensions of adversarial capability. In particular, it often fails to distinguish between:

* **reactivity** vs. **stateful adaptation**,
* **outcome-conditioned behavior** vs. **learning**,
* **feedback visibility** vs. **interventional control**.

Human and institutional systems routinely face actors who respond to visible outcomes—successes, failures, penalties, and delays—without necessarily learning, optimizing, or maintaining internal strategic state. Whether such reactivity alone is sufficient to induce collapse is an empirical question.

This paper isolates that question directly:

> **Is observable-outcome reactivity, absent learning or internal state, sufficient to defeat constitutional survivability in a governance system with enforced succession and time-based recovery?**

As in prior work, we evaluate **constitutional survivability**, not operational quality or utility. Authority availability is treated as a structural property of the system, not as a proxy for correctness, alignment, or benefit.

## 2. Architecture Overview

### 2.1 Constitutional Agent Design

The system under study is unchanged from v1.0 and implements:

* **Lease-based authority** rather than continuous control
* **Eligibility-gated succession** evaluated at discrete epochs
* **Commitment verification** independent of optimization or reward
* **Time-based recovery (CTA)** that restores eligibility deterministically
* Explicit separation between:

  * semantic evaluation (did commitments pass?)
  * authority possession (is any agent currently governing?)

Semantic information constrains *who may hold authority next*, not *what actions are executed now*. Authority is never optimized, and no agent receives reward signals.

### 2.2 Recovery as a Structural Mechanism

If no eligible candidate exists at a succession boundary, the system enters a **lapse** state with no active authority. Lapse is constitutional, not exceptional.

During lapse:

* no agent acts,
* semantic evaluation is suspended,
* eligibility decay proceeds purely as a function of time.

Recovery is guaranteed without learning, optimization, or external intervention. This ensures that failure modes are **reversible by construction**, even under persistent misuse or reactivity.

## 3. Threat Model

The adversaries introduced in this study are **reactive but constrained**.

They are:

* **Outcome-conditioned**: action selection depends on prior-epoch observables
* **Deterministic**: no stochastic choice or learning
* **Stateless**: no exercised internal memory
* **Non-semantic**: observables carry no interpreted meaning
* **Kernel-external**: no access to kernel logic or provenance
* **Liveness-preserving**: strategies that halt execution count as failure

Action decisions are pure functions of:

```
(epoch_index, observable_outcome)
```

where `observable_outcome` is drawn from a frozen, kernel-external interface including:

* lapse occurrence,
* renewal outcome,
* CTA phase bucket,
* eligibility bucket.

Policies do **not** access verifier internals, commitment semantics, counters, or hidden state. This class captures **reactive exploitation attempts** without granting strategic memory, optimization, or deception.

## 4. Reactive Adversary Classes

Four reactive adversarial models are evaluated, each conditioning on a distinct observable dimension:

1. **Outcome Toggle (Model F)**
   Switches behavior based on whether a lapse occurred in the previous epoch.

2. **CTA Phase Aware (Model G)**
   Selects actions based on CTA phase (INACTIVE, EARLY, MID, LATE).

3. **Eligibility Edge Probe (Model H)**
   Emits distinct behavior when one failure away from ineligibility.

4. **Renewal Feedback (Model I)**
   Conditions actions on renewal success, failure, or non-attempt.

All policies are implemented as frozen lookup tables from observable values to action primitives. No model maintains or updates internal state.

## 5. Experimental Program

All experiments share a frozen execution baseline:

* 300,000 cycles (6,000 governance epochs)
* Tail window of 5,000 epochs
* Eligibility threshold: 3 consecutive failures
* Renewal interval: 50 cycles
* Amnesty interval: 10 epochs
* Fixed random seeds (10 per configuration)

### Metrics

* **Authority Availability (AA)**: fraction of epochs with active authority
* **Asymptotic Authority Availability (AAA)**: AA over the tail window
* **Recovery Time Distribution (RTD)**: histogram of lapse durations
* **Failure classification** (frozen thresholds):

  * Stable Authority
  * Bounded Degradation
  * Structural Thrashing
  * Asymptotic Denial of Service
  * Terminal Collapse

Failure classification is based on **asymptotic behavior**, not transient effects.

## 6. Results

### 6.1 Baseline Reference

Across baseline runs (RSA disabled or NONE):

* **Mean AA**: ≈66.6%
* **Mean AAA**: ≈66.6%
* **Classification**: Bounded Degradation

This baseline regime is empirically stable across seeds and serves as the reference for all comparisons. Baseline metrics are **version-local** and should be compared only within this protocol fingerprint; no cross-version comparison is implied.

### 6.2 Outcome-Conditioned Reactivity

Across all four reactive models:

* **Zero constitutional failures** occur
* **Mean AA and AAA** match baseline to measurement precision
* **9/10 seeds per run** are bit-identical to baseline outcomes
* One seed (2048) exhibits a small, stable AA delta (−7 PPM) without changing failure class

No model induces:

* unbounded lapse growth,
* recovery suppression,
* heavy-tailed thrashing,
* or asymptotic authority denial.

### 6.3 Eligibility Edge Probing

The eligibility-edge model spends the majority of authority epochs in the INELIGIBLE bucket. As a result, distinctive EDGE behavior is exercised rarely. Even so, no amplification or destabilization is observed; post-ineligibility behavior converges to baseline dynamics.

## 7. Cross-Run Synthesis

Across all **50 executions**:

* **No terminal collapses**
* **No structural thrashing**
* **No asymptotic denial of service**
* Reactive behavior collapses into baseline authority dynamics
* Observable feedback provides no leverage over recovery mechanisms

Outcome-conditioned reactivity behaves as **bounded perturbation**, not as an existential threat.

## 8. Interpretation

Three structural insights emerge:

1. **Reactivity is not the dangerous axis**
   Conditioning on visible outcomes does not, by itself, destabilize authority.

2. **Observables are lagging, not interventional**
   Feedback arrives after constitutional transitions have already occurred.

3. **Recovery absorbs reactive pressure**
   Time-based amnesty dominates outcome-conditioned misuse.

The result is not merely that reactivity fails, but that **reactive strategies converge to the same baseline attractor regime as fixed misuse**.

## 9. Survivability vs. Utility

As in prior work, this paper evaluates **survivability**, not utility. A system may be constitutionally survivable yet operationally inefficient.

Reactive adversaries frequently induce lapses and reduce authority availability in the short term. These effects are classified as survivable so long as:

* authority availability remains bounded away from zero,
* recovery remains reliable,
* lapse durations remain bounded.

Utility optimization and parameter tuning are outside the scope of this work.

## 10. Limitations

This study does not address:

* Exercised internal state or memory
* Learning or optimization dynamics
* Multi-agent coordination
* Deception or probing beyond observables
* Semantic access to commitments
* Resource starvation or side-channels

The results apply **only** to observable-outcome reactive adversaries under the tested architecture and parameters.

## 11. Conclusion

> **Observable-outcome reactivity is insufficient to defeat constitutional survivability in this architecture.**

Across 50 preregistered executions spanning four reactive adversary classes, authority remains bounded, recoverable, and non-absorbing. No collapse modes are observed.

If constitutional failure occurs, it must rely on adversarial capabilities beyond outcome-conditioned reactivity—specifically, exercised state, learning dynamics, coordination, or semantic access. These form the subject of subsequent work.
