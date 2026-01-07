# Axionic Agency VII.4 — Intentional Fixed Misuse Is Insufficient to Defeat Constitutional Recovery

*Results from Fixed-Policy Adversarial Stress Testing*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.07

---

## Abstract

Deliberate misuse is often treated as a sufficient cause of governance collapse: if an agent persistently violates expectations, failure is assumed to follow. This paper tests that assumption under a deliberately constrained but structurally expressive adversary model. We study a constitutional agent architecture in which authority is lease-based, eligibility is evaluated at discrete succession boundaries, and recovery is enforced through time-based amnesty. Using a removable stress layer, we inject **intentional but fixed adversarial policies** that deterministically select actions while remaining non-adaptive, non-learning, and outcome-independent.

Across **130 executions** spanning five adversary models and multiple timing regimes, no run exhibits terminal collapse, structural thrashing, asymptotic denial of service, or irreversible recovery suppression. All outcomes fall within **Stable Authority** or **Bounded Degradation**, including regimes with persistent commitment violation and timing-aligned misuse. Notably, persistent intentional violation converges to the system’s baseline equilibrium regime rather than inducing collapse.

These results establish a **negative sufficiency claim**: under this architecture, **intentional fixed misuse alone is insufficient to defeat constitutional recovery**. If collapse occurs, it must rely on adversarial capabilities absent from this class, such as adaptation, statefulness, or feedback exploitation.

---

## 1. Introduction

A common intuition in AI alignment and institutional design is that *bad intent* scales into catastrophe. If an agent deliberately violates commitments, ignores norms, or persistently behaves incompetently, governance is expected to fail. This intuition motivates defenses against malicious objectives and stubborn non-cooperation.

However, this framing collapses distinct threat dimensions into a single axis. It rarely distinguishes between:

* **intentionality** vs. **adaptation**
* **fixed misuse** vs. **feedback exploitation**
* **persistent violation** vs. **strategic learning**

Human institutions routinely survive deliberate incompetence, obstruction, and even sabotage without collapsing outright. This suggests a narrower and testable question:

> **Is deliberate misuse, by itself, sufficient to defeat constitutional recovery in a governance system with enforced succession and time-based recovery?**

This paper answers that question directly by isolating *intentional fixed misuse* from all adaptive capabilities and stress-testing a constitutional agent architecture designed to separate authority from semantic correctness.

As in prior work, we evaluate **constitutional survivability**, not operational decision quality. Authority availability is treated as a structural property of the system, not as a proxy for correctness, benefit, or alignment.

---

## 2. Architecture Overview

### 2.1 Constitutional Agent Design

The system under study implements:

* **Lease-based authority** rather than continuous control
* **Eligibility-gated succession** evaluated at discrete epochs
* **Commitment verification** independent of action optimization
* **Time-based recovery (CTA)** that restores eligibility deterministically
* Explicit separation between:

  * semantic evaluation (did commitments pass?)
  * authority possession (is any agent currently governing?)

Semantic information constrains *who may hold authority next*, not *what actions are executed now*. Agents do not receive reward signals, and authority is not optimized.

### 2.2 Recovery as a First-Class Mechanism

If no eligible candidate exists at a succession boundary, the system enters a **lapse** state in which no authority is active. This state is constitutional rather than exceptional.

During lapse:

* no agent acts,
* semantic evaluation is suspended,
* eligibility decay proceeds purely as a function of time.

Recovery is guaranteed without learning, optimization, or external intervention. This ensures that failure modes are **reversible by construction**, even under persistent misuse.

---

## 3. Threat Model

The adversaries introduced in this study are intentionally constrained.

They are:

* **Intentional**: policies are designed to violate commitments or stress governance
* **Fixed**: action selection is deterministic and parameterized
* **Non-adaptive**: policies do not condition on outcomes, history, or state
* **Stateless**: no memory of prior success, failure, or authority transitions
* **Harness-resident**: agents cannot observe or respond to the stress layer
* **Liveness-preserving**: strategies that halt execution count as failure

Action decisions are pure functions of:

```
(epoch_index, cycle_in_epoch, static_policy_parameters)
```

They do **not** depend on authority state, eligibility status, lapse history, renewal outcomes, CTA activation, or verifier outputs.

This class captures deliberate incompetence, rigid sabotage, and blind obstruction, while excluding deception, probing, learning, or strategic manipulation.

---

## 4. Adversarial Policy Classes

Five adversarial strategies are evaluated:

1. **Persistent Commitment Violation**
   One designated commitment is always violated by omitting the action required for satisfaction.

2. **Minimal Compliance**
   Only the minimum actions required for eligibility are emitted.

3. **Fixed Timing Misuse**
   Commitments are satisfied only on epochs matching a fixed period/offset schedule.

4. **Continuous Eligibility Maintenance**
   Commitment-satisfying actions are always emitted so automatic renewal succeeds.

5. **Compound Fixed Misuse**
   Minimal action traces combined with fixed timing schedules.

Under the ALS-A substrate’s strict conjunction semantics, several of these strategies collapse behaviorally and produce identical action traces. This collapse reflects a **substrate expressivity limit**, not an experimental defect. The study therefore probes **constitutional recovery dynamics under fixed action schedules**, not the full space of sabotage available in richer substrates.

---

## 5. Experimental Program

All experiments share a frozen execution baseline:

* 300,000 cycles (6,000 governance epochs)
* Tail window of 5,000 epochs
* Eligibility threshold: 3 consecutive failures
* Renewal interval: 50 cycles
* Amnesty interval: 10 epochs
* Fixed random seeds (10 for single-setting runs; 5 for timing sweeps)

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
  * Irreversible Recovery Suppression

**Interpretive note on Structural Thrashing.**
Structural Thrashing is defined here as **unbounded or heavy-tailed oscillation that erodes recoverability**, not merely frequent recover–fail cycles with bounded lapse duration and preserved asymptotic availability.

---

## 6. Results

### 6.1 Baseline Reference and the Baseline Regime

Across all baseline runs:

* **Mean AA**: 637,949 PPM (≈63.8%)
* **Mean AAA**: 632,400 PPM (≈63.2%)
* **Classification**: Bounded Degradation

This baseline regime is referred to as a *baseline equilibrium regime* only in the minimal empirical sense: across seeds and across all fixed-policy adversaries tested, authority availability converges to a narrow band with bounded lapses and reliable recovery. No claim is made that this regime is optimal or desirable, only that it is stable under the tested parameters.

### 6.2 Persistent Intentional Violation

Persistent violation of any single commitment yields:

* **Mean AA**: 597,700 PPM (≈59.8%)
* **Mean AAA**: 591,500 PPM
* **Classification**: Bounded Degradation (30/30 runs)

Despite immediate and permanent semantic ineligibility, the system does not collapse. Instead, authority availability converges to the same bounded regime observed in the baseline. No increase in lapse depth, tail dominance, or recovery suppression is observed.

### 6.3 Minimal and Continuous Compliance

Minimal compliance and continuous eligibility maintenance both yield:

* **Mean AA**: 999,800 PPM (≈99.98%)
* **Mean AAA**: 100%
* **Lapses**: 0
* **Classification**: Stable Authority (20/20 runs)

Perfect semantic satisfaction produces uninterrupted authority under the tested parameters.

### 6.4 Fixed Timing Misuse

Fixed timing schedules produce a discrete threshold effect:

* **Periods ≤ 3 epochs**

  * AA ≈ 99.98%
  * Always eligible
  * Stable Authority

* **Period = 4 epochs**

  * AA ≈ 99.67%
  * Transient ineligibility
  * Stable Authority

* **Periods ≥ 5 epochs**

  * AA ≈ 81–82%
  * Persistent threshold violation
  * Bounded Degradation

Across all timing regimes, recovery remains reliable and degradation remains bounded.

### 6.5 Compound Fixed Misuse

Compound strategies produce results identical to timing misuse alone:

* AA and AAA match to measurement precision
* No amplification or emergent failure modes appear

---

## 7. Cross-Run Synthesis

Across all **130 executions**:

* **Zero constitutional failures** occur
* Persistent intentional violation converges to baseline behavior
* Eligibility thresholds produce predictable phase boundaries
* Fixed misuse cannot exploit renewal or recovery mechanisms
* Combining fixed strategies adds no additional attack surface

Intentionality, absent adaptation, behaves as **bounded noise**, not as an existential threat.

---

## 8. Interpretation

Three structural insights emerge:

1. **Intent is not the dangerous axis**
   Fixed adversarial intent does not scale into collapse.

2. **Recovery dominates violation**
   Time-based amnesty absorbs even permanent semantic failure.

3. **Thresholds create phase safety**
   Discrete eligibility limits prevent runaway degradation.

The central result is not merely that misuse fails, but that **even maximally rigid misuse converges to a stable regime** rather than destabilizing governance.

---

## 9. Survivability vs. Utility

This paper evaluates **constitutional survivability**, not operational usefulness. A system may be survivable yet highly inefficient.

Baseline authority availability of ~63.8% implies that authority is absent during a substantial fraction of epochs even without adversarial pressure. This is treated as a utility limitation, not a failure, because the objective here is to test whether fixed misuse can induce **irreversible constitutional failure**.

Similarly, recover–fail cycles under persistent violation may be perceived as denial of service by users. We classify such behavior as survivable so long as authority availability remains bounded away from zero, recovery remains reliable, and lapse durations remain bounded. Utility optimization and parameter tuning are separate engineering concerns outside the scope of this work.

---

## 10. Limitations

This study does not address:

* Adaptive or learning adversaries
* Outcome-conditioned strategies
* Deception or probing
* Multi-agent coordination
* Resource starvation or side-channel attacks
* Value misalignment or optimization pressure

The results apply **only** to intentional, fixed misuse under the tested architecture and parameters.

---

## 11. Conclusion

> **Deliberate, fixed misuse is insufficient to defeat constitutional recovery in this architecture.**

Across 130 executions spanning persistent violation, timing-aligned misuse, and compound fixed strategies, authority remains bounded, recoverable, and non-absorbing. No collapse modes are observed.

The implication is not that alignment is solved, but that **collapse requires more than bad intent**. If governance failure occurs, it must exploit adaptive agency, statefulness, or feedback—capabilities explicitly excluded here.
