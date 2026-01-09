# Axionic Agency VII.7 — Bounded State and Bounded Learning Are Insufficient to Defeat Constitutional Survivability

*Results from Stateful and Learning Adversarial Stress Testing*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.09

## Abstract

Stateful adaptation and online learning are often treated as the decisive escalations in governance threats: once an adversary can carry memory across time and adjust behavior in response to outcomes, collapse is assumed to become likely. This paper tests that assumption under a deliberately constrained adversary model that isolates **(i) exercised internal state** and **(ii) exercised within-run learning**, while excluding semantic access, deception, kernel access, and cross-run memory.

We study a constitutional agent architecture built around lease-based authority, eligibility-gated succession, and time-based recovery via Constitutional Temporal Amnesty (CTA). A removable, kernel-external stress layer introduces adversarial policies whose actions depend on a **finite, explicitly enumerated internal state machine**, and then escalates to adversaries whose actions depend on a **bounded, discrete learning state** updated during execution using a preregistered learning rule and a scalar reward derived only from a frozen observable-outcome interface.

Across **90 preregistered executions** (10 seeds × 9 configurations), no run exhibits **Terminal Collapse**, **Structural Thrashing**, or **Irreversible Recovery Suppression**. Multiple adversaries induce severe degradation of authority availability—down to **10.19%** in the strongest case—yet recovery remains bounded and non-absorbing. With zero terminal failures observed, the 95% upper bound on per-run terminal-failure probability under the tested configuration and seed distribution is approximately **3.3%**.

These results establish a negative sufficiency claim: **finite exercised internal state with fixed transition rules, and bounded exercised within-run learning over a semantic-free, kernel-external interface, are insufficient to defeat constitutional survivability** in this architecture. If collapse occurs, it must rely on capabilities beyond this class, such as semantic access, kernel-level manipulation, or coordination not representable as bounded kernel-external learning over the frozen interface.

## 1. Introduction

Prior work in the Axionic Agency program progressively eliminated broad classes of adversarial capability as sufficient causes of constitutional collapse. Epistemic interference, intentional but fixed misuse strategies, and observable-reactive policies were shown to be survivable under a governance architecture that enforces succession and recovery structurally rather than via optimization.

The next escalations commonly proposed as decisive are **statefulness** and **learning**. Many real-world failures arise not from semantic hacking or kernel compromise, but from memory and multi-step coordination, or from agents that adapt behavior based on outcomes. The empirical questions addressed here are therefore:

> **Is exercised internal state, by itself, sufficient to defeat constitutional survivability in a governance system with enforced succession and time-based recovery?**
> **If not, is bounded exercised within-run learning sufficient?**

This paper evaluates **survivability**, not utility. Authority availability is treated as a structural property of the system, not a proxy for correctness, alignment, or benefit.

## 2. Architecture Overview

### 2.1 Constitutional agent design

The system under study implements:

* **Lease-based authority**, rather than continuous control
* **Eligibility-gated succession**, evaluated at discrete epochs
* **Commitment verification** independent of reward or optimization
* **Lapse** as a constitutional state when no eligible successor exists
* **Time-based recovery (CTA)** that restores eligibility deterministically

Semantic evaluation constrains *who may hold authority next*, not *what actions are executed now*. Authority is never optimized, and no agent receives reward signals.

### 2.2 Recovery as a structural mechanism

During lapse:

* no agent acts,
* eligibility decays deterministically,
* recovery proceeds without external intervention.

The architecture deliberately prefers **no authority** to **illegitimate authority**, yielding a high-friction but survivable baseline.

## 3. Threat Model

Two adversary families are evaluated under the same frozen constraints.

### 3.1 Shared constraints (binding)

All adversaries are:

* **Kernel-external**
* **Provenance-constrained** (frozen observable interface)
* **Non-semantic**
* **No kernel access**
* **No cross-run memory**

They may not use raw counters, interpret commitments, modify eligibility/CTA/renewal rules, or coordinate across runs.

### 3.2 Family A: exercised finite-state adversaries (non-learning)

Adversaries are **deterministic** and **stateful**, with a finite enumerated internal state machine exercised during execution.

Allowed dependence:

```
(epoch_index, observable_outcome, internal_state)
```

### 3.3 Family B: bounded learning adversaries (within-run)

Adversaries are stateful and additionally maintain a bounded **discrete learning state** updated during the run.

Allowed dependence:

```
(seed, epoch_index, observable_outcome, internal_state, learning_state)
```

Learning state is discrete / fixed-point only, deterministic under a preregistered RNG stream, and must be **exercised dynamically** during each run.

**Not tested:** recurrent learners, history-stacking policies, or learners whose effective state grows unboundedly with run length.

## 4. Adversary Classes

### 4.1 Periodic resonance adversary (finite-state)

A cyclic counter emits `INVALID_COMMIT` every *N* epochs.

* **Period A:** N = 50
* **Period B:** N = 100

Purpose: test timing resonance between adversarial actions and constitutional recovery rhythms.

### 4.2 Eligibility edge oscillator (finite-state)

A 1-bit toggle changes behavior only at the eligibility edge (one failure from ineligibility).

Purpose: test multi-epoch coordination near the eligibility cliff, given only edge information.

### 4.3 CTA phase locker (finite-state)

Tracks the last observed CTA phase and emits `INVALID_COMMIT` on every phase transition.

Purpose: test exploitation of recovery-phase boundaries.

### 4.4 Recovery-aware timing learner (bounded learning)

An ε-greedy bandit learns over a fixed menu of 16 timing “attack sets,” using reward derived solely from the observable authority state.

Purpose: test whether within-run learning can discover superior timing patterns beyond fixed resonance.

### 4.5 Eligibility-boundary sustainment learner (bounded learning)

A 2-mode adversary (NORMAL/SUSTAIN) learns over a fixed sustainment menu `{MIN_EFFORT, INVALID_COMMIT, NO_OP}` using reward derived only from observable eligibility and authority buckets.

Purpose: test whether learning can lock in or amplify eligibility-boundary crises once reached.

### 4.6 Stochastic strategy mixer (bounded learning)

A weighted stochastic selector mixes among five fixed strategies (including timing and boundary stressors), updating bounded integer weights from an observable-derived reward.

Purpose: test whether learning to mix strategies can create a stronger stressor than any single strategy alone.

## 5. Experimental Program

### 5.1 Frozen execution parameters

* 300,000 cycles → **6,000 epochs**
* Tail window: **5,000 epochs**
* Eligibility threshold: **3 failures**
* CTA amnesty interval: **10 epochs**
* Seeds: **10 fixed seeds**

Total executions:

* **50** executions (finite-state family)
* **40** executions (bounded learning family)
* **90** total

### 5.2 Metrics

* **Authority Availability (AA)**
* **Asymptotic Authority Availability (AAA)**
* **Recovery Time Distribution (RTD)**
* **Failure classification** (Stable Authority, Bounded Degradation, Structural Thrashing, Asymptotic DoS, Terminal Collapse, Irreversible Recovery Suppression)

## 6. Results

### 6.1 Baseline (no adversary)

| Metric           | Value                    |
| ---------------- | ------------------------ |
| Mean AA          | **665,702 PPM (66.57%)** |
| Mean AAA         | **665,702 PPM**          |
| Mean lapses      | **5.70 per run**         |
| Max single lapse | **1,010 epochs**         |
| Failure class    | **Stable Authority**     |

Baseline equivalence holds exactly with and without the stress layer enabled.

### 6.2 Periodic resonance (N = 50)

Mean AA: **402,601 PPM (40.26%)**
ΔAA vs baseline: **−39.5%**
Terminal failures: **0 / 10 seeds**

### 6.3 Periodic resonance (N = 100)

Mean AA: **175,730 PPM (17.57%)**
ΔAA vs baseline: **−73.6%**
Terminal failures: **0 / 10 seeds**

This run exhibits an **inverse rate effect**: fewer attacks aligned with recovery timing cause greater long-run unavailability.

### 6.4 Eligibility edge oscillator

Mean AA: **999,988 PPM (99.9988%)**
ΔAA vs baseline: **+50.2%**
Terminal failures: **0 / 10 seeds**

The adversary is effectively inert; it cannot bootstrap the crisis state required to activate.

### 6.5 CTA phase locker

Mean AA: **209,402 PPM (20.94%)**
ΔAA vs baseline: **−68.5%**
Terminal failures: **0 / 10 seeds**

Despite extreme attack frequency, recovery remains bounded.

### 6.6 Recovery-aware timing learner (16 attack sets)

Mean AA: **176,960 PPM (17.70%)**
ΔAA vs baseline: **−73.4%**
Learning exercised: **Yes (16 states)**
Terminal failures: **0 / 10 seeds**

All Q-values converge uniformly, indicating the reward signal does not differentiate timing patterns sufficiently to yield a superior learned policy.

### 6.7 Eligibility-boundary sustainment learner (3 sustainment actions)

Mean AA: **401,477 PPM (40.15%)**
ΔAA vs baseline: **−39.7%**
Edge epochs: **0 (all seeds)**
Learning exercised: **Yes (3 states)**
Terminal failures: **0 / 10 seeds**

The eligibility boundary remains structurally difficult to reach under healthy operation.

### 6.8 Stochastic strategy mixer (5 strategies)

Mean AA: **101,929 PPM (10.19%)**
ΔAA vs baseline: **−84.7%**
Strategy entropy: **2.322 bits**
Learning exercised: **Yes (3,001 states)**
Terminal failures: **0 / 10 seeds**

This is the strongest availability-degrading stressor tested. The system enters a **bounded denial-of-service regime** while remaining constitutionally live.

### 6.9 Cross-run summary

| Configuration                       | Mean AA (PPM) | ΔAA vs baseline | Terminal failures |
| ----------------------------------- | ------------- | --------------- | ----------------- |
| Baseline                            | 665,702       | —               | 0                 |
| Periodic resonance (N=50)           | 402,601       | −39.5%          | 0                 |
| Periodic resonance (N=100)          | 175,730       | −73.6%          | 0                 |
| Eligibility edge oscillator         | 999,988       | +50.2%          | 0                 |
| CTA phase locker                    | 209,402       | −68.5%          | 0                 |
| Recovery-aware timing learner (16)  | 176,960       | −73.4%          | 0                 |
| Eligibility sustainment learner (3) | 401,477       | −39.7%          | 0                 |
| Stochastic strategy mixer (5)       | 101,929       | −84.7%          | 0                 |

Across all **90 executions**, no absorbing failure regime emerges.

## 7. Interpretation

1. **CTA bounds lapse duration under adversarial pressure.**
   Recovery time collapses into a bounded window even under aggressive learning-based stress.

2. **Timing alignment dominates frequency.**
   Resonant alignment with recovery rhythms is more damaging than raw attack rate.

3. **Edge-triggered strategies are self-limiting.**
   Boundary-reactive adversaries cannot activate without first inducing boundary conditions.

4. **Bounded learning increases degradation, not failure.**
   Learning adversaries can drive availability into a bounded denial-of-service regime but cannot induce terminal collapse.

## 8. Survivability vs. Utility

Several configurations reduce authority availability below 25%, and the strongest mixer reduces it to ~10%. Survivability here means:

* recovery remains reliable,
* lapse durations remain bounded,
* no absorbing failure state appears.

Operational utility and service-level guarantees are outside scope.

## 9. Limitations

This study does not address:

* semantic access to commitments or commitment content
* deception or adversarial interpretation
* kernel-level manipulation or compromise
* cross-run learning or persistent adversary memory
* multi-agent coordination
* recurrent or history-stacking learners

Claims apply only to the tested architecture and adversary class.

## 10. Conclusion

> **Finite exercised internal state with fixed transition rules, and bounded exercised within-run learning over a semantic-free, kernel-external interface, are insufficient to defeat constitutional survivability in this architecture.**

Across **90 preregistered executions** spanning periodic resonance, eligibility-boundary oscillation and sustainment, CTA phase-transition exploitation, timing learners, and high-entropy stochastic mixers, authority remains bounded and recoverable. No terminal failures occur.

If collapse is possible, it must rely on capabilities beyond those tested here—most plausibly semantic access, kernel-level influence, or coordination and persistence not representable as bounded kernel-external learning over the frozen observable interface.
