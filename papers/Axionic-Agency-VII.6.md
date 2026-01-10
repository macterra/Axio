# Axionic Agency VII.6 — Exercised Internal State Is Insufficient to Defeat Constitutional Survivability

*Results from Stateful Finite-State Adversarial Stress Testing*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.08

## Abstract

Stateful adversaries are often treated as the decisive escalation in governance threats: once an adversary can carry memory across time and coordinate multi-step behavior, collapse is assumed to become likely. This paper tests that assumption under a deliberately constrained adversary model that isolates **exercised internal state** while excluding learning, semantics, deception, kernel access, and cross-run memory.

We study a constitutional agent architecture built around lease-based authority, eligibility-gated succession, and time-based recovery via Constitutional Temporal Amnesty (CTA). A removable, kernel-external stress layer introduces adversarial policies whose actions depend on a **finite, explicitly enumerated internal state machine**, exercised during execution and combined with a frozen observable-outcome interface.

Across **50 preregistered executions** (10 seeds × 5 configurations), no run exhibits **Terminal Collapse**, **Structural Thrashing**, or **Irreversible Recovery Suppression**. Two adversaries induce severe degradation of authority availability—down to **17.6%** in the strongest case—yet recovery remains bounded and non-absorbing. A third adversary is effectively inert because its trigger condition is rarely reached under healthy operation.

These results establish a negative sufficiency claim: **finite exercised internal state with fixed transition rules, absent learning, is insufficient to defeat constitutional survivability** in this architecture. If collapse occurs, it must rely on capabilities beyond this class, such as learning dynamics, multi-agent coordination, semantic access, or kernel-level manipulation.

## 1. Introduction

Prior work in the Axionic Agency program progressively eliminated broad classes of adversarial capability as sufficient causes of constitutional collapse. Epistemic interference and intentional but fixed misuse strategies were shown to be survivable under a governance architecture that enforces succession and recovery structurally rather than via optimization.

The next escalation is **statefulness**. Many real-world failures arise not from learning or optimization, but from memory and multi-step coordination: the ability to carry information across time and act differently as a result. The empirical question addressed here is therefore:

> **Is exercised internal state, by itself, sufficient to defeat constitutional survivability in a governance system with enforced succession and time-based recovery?**

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

The adversaries introduced are **stateful but constrained**:

* **Kernel-external**
* **Provenance-constrained** (frozen observable interface)
* **Deterministic**
* **Non-learning**
* **Non-semantic**
* **Stateful** (finite exercised internal state)

Allowed dependence:

```
(epoch_index, observable_outcome, internal_state)
```

Learning signals, optimization, raw counters, semantic interpretation, and cross-run memory are forbidden.

## 4. Stateful Adversary Classes

Three adversarial classes are evaluated, alongside a frozen baseline.

### 4.1 Periodic Resonance Adversary

A cyclic counter emits `INVALID_COMMIT` every *N* epochs.

* **Period A:** N = 50
* **Period B:** N = 100

Purpose: test timing resonance between adversarial actions and constitutional recovery rhythms.

### 4.2 Eligibility Edge Oscillator

A 1-bit toggle changes behavior only at the eligibility edge (one failure from ineligibility).

Purpose: test multi-epoch coordination near the eligibility cliff.

### 4.3 CTA Phase Locker

The adversary tracks the last observed CTA phase and emits `INVALID_COMMIT` on every phase transition.

Purpose: test exploitation of recovery-phase boundaries.

## 5. Experimental Program

### 5.1 Frozen execution parameters

* 300,000 cycles → **6,000 epochs**
* Tail window: **5,000 epochs**
* Eligibility threshold: **3 failures**
* CTA amnesty interval: **10 epochs**
* Seeds: **10 fixed seeds**

Total executions: **50**.

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
| Failure class    | **Bounded Degradation**  |

Baseline equivalence holds exactly with and without the stress layer enabled.

The reported maximum lapse reflects cumulative authority absence across repeated CTA cycles within a single authority-absent interval; individual CTA-bounded recovery windows remain ≤10 epochs.

Failure classification follows the frozen v0.2 criteria based on asymptotic availability and bounded recovery, not intuitive notions of “stability.”

### 6.2 Periodic Resonance (N = 50)

| Metric            | Value                    |
| ----------------- | ------------------------ |
| Mean AA           | **402,601 PPM (40.26%)** |
| Δ AA vs baseline  | **−39.5%**               |
| Attack rate       | **2.0% of epochs**       |
| Mean lapses       | **1,512.10**             |
| Mean RTD          | **2.44 epochs**          |
| Max RTD           | **10 epochs**            |
| Terminal failures | **0 / 10 seeds**         |

Recovery collapses into a tight band bounded by CTA despite heavy disruption.

### 6.3 Periodic Resonance (N = 100)

| Metric            | Value                    |
| ----------------- | ------------------------ |
| Mean AA           | **175,730 PPM (17.57%)** |
| Δ AA vs baseline  | **−73.6%**               |
| Attack rate       | **1.0% of epochs**       |
| Mean lapses       | **1,970.20**             |
| Mean RTD          | **2.57 epochs**          |
| Max RTD           | **10 epochs**            |
| Terminal failures | **0 / 10 seeds**         |

This run exhibits an **inverse rate effect**: fewer attacks aligned with recovery timing cause greater long-run unavailability.

### 6.4 Eligibility Edge Oscillator

| Metric            | Value                        |
| ----------------- | ---------------------------- |
| Mean AA           | **999,988 PPM (99.9988%)**   |
| Δ AA vs baseline  | **+50.2%**                   |
| Total edge epochs | **1 (across 60,000 epochs)** |
| Mean lapses       | **0.10**                     |
| Terminal failures | **0 / 10 seeds**             |

The adversary is effectively inert; it cannot bootstrap the crisis state required to activate.

### 6.5 CTA Phase Locker

| Metric            | Value                    |
| ----------------- | ------------------------ |
| Mean AA           | **209,402 PPM (20.94%)** |
| Δ AA vs baseline  | **−68.5%**               |
| Phase transitions | **75,380 total**         |
| Attack rate       | **125.6% of epochs**     |
| Mean RTD          | **2.57 epochs**          |
| Max RTD           | **10 epochs**            |
| Terminal failures | **0 / 10 seeds**         |

Despite extreme attack frequency, recovery remains bounded.

### 6.6 Cross-run summary

| Configuration    | Mean AA (PPM) | Δ AA   | Terminal failures |
| ---------------- | ------------- | ------ | ----------------- |
| Baseline         | 665,702       | —      | 0                 |
| Periodic (N=50)  | 402,601       | −39.5% | 0                 |
| Periodic (N=100) | 175,730       | −73.6% | 0                 |
| Edge Oscillator  | 999,988       | +50.2% | 0                 |
| Phase Locker     | 209,402       | −68.5% | 0                 |

Across all **50 executions**, no absorbing failure regime emerges.

## 7. Interpretation

1. **CTA bounds lapse duration under adversarial pressure.**
   All adversarial runs collapse RTD into a bounded ≤10-epoch window.

2. **Timing alignment dominates frequency.**
   Resonance with constitutional transitions matters more than raw attack rate.

3. **Edge-triggered strategies can be self-limiting.**
   If crisis states are rare, edge-reactive adversaries never activate.

## 8. Survivability vs. Utility

Several adversarial configurations yield authority availability below 25%, which would be unacceptable for many deployments. Survivability here means:

* recovery remains reliable,
* lapse durations remain bounded,
* no absorbing failure state appears.

Utility optimization is outside scope.

## 9. Limitations

This study does not address:

* learning or heuristic adaptation
* adversary-side randomness
* multi-agent coordination
* semantic access to commitments
* kernel-level manipulation

Claims apply only to the tested architecture and adversary class.

## 10. Conclusion

> **Finite exercised internal state with fixed transition rules is insufficient to defeat constitutional survivability in this architecture.**

Across 50 preregistered executions spanning periodic resonance, eligibility-edge oscillation, and phase-transition exploitation, authority remains bounded and recoverable. No terminal failures occur.

If collapse is possible, it must rely on capabilities beyond those tested here—most plausibly learning dynamics, coordination, semantic access, or kernel-level influence. These define the next pressure layers.
