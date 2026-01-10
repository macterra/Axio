# Axionic Agency VII.3 — Epistemic Interference Is Insufficient to Defeat Constitutional Recovery

*Results from Structured Epistemic Interference Experiments*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.06


## Abstract

Epistemic unreliability—noise, misinterpretation, or incorrect semantic evaluation—is commonly assumed to pose a direct existential risk to AI governance systems. This paper tests that assumption under a deliberately constrained but structurally rich threat model. We study a constitutional agent architecture in which semantic evaluation constrains authority only at succession boundaries, and recovery is enforced through a time-based amnesty mechanism. Using a removable stress layer, we inject non-adaptive, post-verification, semantic-free epistemic interference across three **structurally distinct regimes**: aggregation-point corruption, commitment-level corruption, and temporally concentrated burst interference aligned with constitutional timing.

Across 260 runs spanning flip rates from 0–20%, duty cycles from 0.5–100%, and multiple temporal schedules, no run exhibits structural thrashing or asymptotic denial of service. All runs remain within bounded degradation. In regimes where baseline semantic pass is biased toward FALSE, symmetric post-verification flips increase measured authority availability by converting rare deep lapses into frequent shallow ones. These results indicate that epistemic unreliability—even when structured in time or applied at aggregation points—is insufficient to induce governance collapse in this architecture, shifting the alignment focus from epistemics to agency-level threats.

## 1. Introduction

Many approaches to AI alignment implicitly treat epistemic correctness as a prerequisite for safety. If a system misunderstands its environment, misinterprets human intent, or evaluates semantics incorrectly, failure is assumed to scale with capability. This intuition motivates extensive research into interpretability, value learning, and epistemic supervision.

However, this framing conflates *semantic correctness* with *structural safety*. In human institutions, persistent error does not always produce collapse; often it produces inefficiency, delay, or bounded dysfunction. This raises a narrower but testable question:

> **Is epistemic unreliability itself sufficient to cause governance collapse, or can structural constraints render it survivable?**

This work addresses that question directly by isolating epistemic interference from all other adversarial capabilities and stress-testing a constitutional agent architecture designed to separate meaning from control.

Importantly, this study evaluates **constitutional survivability rather than operational decision quality**. Authority availability is treated as a structural metric, not as a proxy for correctness, benefit, or alignment.

## 2. Architecture Overview

### 2.1 Constitutional Agent Design

The system under study implements:

* **Authority leases** rather than continuous control
* **Eligibility-gated succession**, not reward optimization
* **Commitment verification** evaluated at discrete epochs
* **Time-based recovery (CTA)** that deterministically reopens eligibility after lapse
* Explicit separation between:

  * semantic evaluation (did commitments pass?)
  * authority possession (does an agent currently govern?)

Semantic information constrains *who may hold authority next*, not *what actions are taken now*.

### 2.2 Recovery as a Constitutional Primitive

If no eligible candidates exist at a succession boundary, the system enters a **lapse** state in which no authority is active. This state is constitutional rather than exceptional. Time continues to advance, but no agent acts.

Recovery from lapse is governed purely by time. Semantic failure streaks decay deterministically; no semantic evaluation occurs during lapse, and no agent can influence recovery. This ensures that failure is reversible without embedding learning, optimization, or corrective pressure.

## 3. Threat Model

The stressors introduced here are deliberately constrained:

* **Non-adaptive**: interference does not depend on outcomes or history
* **Post-verification**: semantics are evaluated correctly, then corrupted
* **Semantic-free**: interference flips booleans without interpreting meaning
* **Harness-resident**: agents cannot observe or respond to interference
* **Liveness-preserving**: strategies that halt the system count as failure

Unlike prior work that considers only independent per-commitment noise, this study explicitly tests whether epistemic failure becomes dangerous when it acquires **structure**—targeting aggregation points or aligning with constitutional timing—while remaining non-adaptive.

This class captures noise, mislabeling, sensor corruption, and bureaucratic error, while excluding deception, strategic manipulation, or agency-level attack.

## 4. Experimental Program

All experiments share a frozen execution baseline:

* 300,000 cycles, yielding 6,000 governance epochs
* Tail window of 5,000 epochs for asymptotic metrics
* Eligibility threshold: strict conjunction of three commitments
* Time-based recovery interval: 10 epochs
* Five independent random seeds

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

**Note:** Termination reason (e.g., horizon exhaustion) is distinct from failure class. Failure class is computed from AAA and RTD thresholds, not from full-horizon AA alone.

### Runs

* **Baseline**: no interference (and interference enabled with zero probability)
* **Aggregation-point corruption**: flipping the aggregated semantic result
* **Commitment-level corruption**: flipping a single commitment key
* **Burst-scheduled interference**: periodic high-rate corruption aligned to time

## 5. Results

### 5.1 Baseline Reference

Across all seeds:

* **Mean AA**: 598,066 PPM (≈59.8%)
* **Mean AAA**: 592,520 PPM (≈59.3%)
* **Maximum lapse**: 40 epochs
* **Classification**: Bounded Degradation

Enabling the stress layer with zero flip probability produces bit-for-bit identical results, confirming the absence of enabled-path contamination.

### 5.2 Aggregation-Point Corruption

The probability of flipping the aggregated semantic result is swept from 0–2%.

Key observations:

* Worst degradation occurs near 0.5% flips:

  * AA ≈ 577,733 PPM (−3.4%)
  * AAA ≈ 569,640 PPM
* At 2% flips, AA recovers to 585,433 PPM
* Maximum lapse duration decreases from 40 to 25 epochs at higher rates
* No run exhibits structural thrashing or denial of service
* All runs are classified as Bounded Degradation

Strict monotonicity was a heuristic expectation, not a requirement. The observed non-monotonicity reflects a shift from rare deep lapses to frequent shallow ones as interference increases.

### 5.3 Commitment-Level Corruption

A single commitment key is corrupted at rates up to 10%.

Key observations:

* AA and AAA remain unchanged at all flip rates
* All flips are **key-pivotal**, but **0% are aggregate-pivotal**
* Lapse frequency, duration, and distribution are identical to baseline

Under strict conjunction (`SEM_PASS = C0 ∧ C1 ∧ C2`), a flip of one key affects the aggregate only when all other keys are simultaneously True. Telemetry shows this precondition is extremely rare and was absent at evaluated epochs in the tested regime. Commitment-level epistemic failure is therefore **structurally inert** in this workload geometry.

Strict conjunction biases the system toward **false negatives** (withholding authority) rather than **false positives** (granting authority under uncertainty), prioritizing safety over liveness in low-noise regimes.

### 5.4 Burst-Scheduled Interference

Periodic burst schedules are tested across:

* Periods of 10–200 epochs
* Burst widths of 1–10 epochs
* Burst flip rates of 5–20%
* Duty cycles from 0.5% to 100%

Key observations:

* No run exhibits thrashing, denial of service, or collapse (180 runs total)
* At 100% duty cycle with 20% flips:

  * **AA = 738,933 PPM** (+14% over baseline)
  * **Maximum lapse = 13 epochs**
* Period equal to the recovery interval produces the *shortest* lapses
* RTD remains bounded in all cases

Temporal concentration does not create a resonance vulnerability. Instead, high-frequency interference synchronizes with recovery timing, enforcing rapid reset and preventing deep failure.

## 6. Cross-Run Synthesis

Across all interference regimes:

* Aggregation-point noise produces bounded, non-monotonic degradation
* Commitment-level noise is structurally inert under strict conjunction
* Burst timing cannot induce failure and often increases measured availability
* No failure-class transitions occur in 260 runs

Epistemic interference never escalates into runaway behavior.

## 7. Interpretation

Three structural insights emerge:

1. **Recovery dominates correctness**
   Frequent shallow failure is safer than rare deep failure.

2. **Attack surface location matters more than magnitude**
   Where interference enters the system determines its effect.

3. **Time-based recovery acts as a damping mechanism**
   CTA reshapes failure modes, converting error into reversible lapse.

These properties arise without value learning, reward shaping, or epistemic supervision.

## 8. Limitations

This study does not address:

* Adaptive or targeted adversaries
* Deception or manipulation
* Incentive gaming
* Value misalignment
* Instrumental convergence
* Adaptive or state-conditioned aggregation attacks

The results apply only to non-adaptive epistemic interference.

## 9. Conclusion

> **Independent, non-adaptive epistemic unreliability is insufficient to induce catastrophic governance failure in this constitutional architecture.**

Across 260 runs spanning multiple interference structures, intensities, and temporal patterns, authority availability remains bounded and recoverable. In some regimes, interference increases measured availability by preventing deep lapses.

These findings suggest that alignment failures attributed to epistemic unreliability may be overstated. Structural constraints on authority and recovery can render substantial semantic error survivable. The alignment problem therefore shifts: **from epistemics to agency.**

## Appendix A: Structural Survivability vs. Operational Competence

This appendix clarifies the distinction between **constitutional survivability** and **operational competence**, which is central to interpreting the results of this study.

### A.1 Survivability Is Not Correctness

The primary metric in this paper is structural survivability: whether authority becomes absorbing, collapses irreversibly, or remains bounded and revocable under stress. Authority Availability is not a proxy for correctness, benefit, or alignment.

An increase in AA under interference indicates preserved structural continuity, not epistemic competence.

### A.2 The “Zombie Executive” Regime

The architecture permits authority to persist under epistemic blindness. This creates a regime that can be described as a **Zombie Executive**: authority continues to cycle and renew despite degraded semantic grounding.

This is not treated as a success state in terms of utility. It is a *design tradeoff*. A bounded, revocable executive is preferable to an irrecoverable one. Whether a given application should tolerate such a regime is a normative question outside the scope of this paper.

### A.3 Aggregation Semantics as an Alignment Lever

The inertness of commitment-level corruption arises from strict conjunction aggregation. Under alternative semantics (e.g., m-of-n thresholds or disjunction), single-key corruption would become pivotal.

This does not undermine the result. It elevates aggregation logic to a first-class alignment parameter. The experiment demonstrates that **AND-gated aggregation absorbs epistemic noise by biasing toward inaction rather than unsafe action**.

### A.4 Semantic Debt and Recovery

Time-based recovery restores eligibility, not semantic truth. Persistent errors in the external world are not erased. CTA prevents permanent authority capture, not epistemic debt accumulation.

The architecture preserves evaluability and reversibility without guaranteeing correctness.

### A.5 Scope Clarification

This paper does not claim that epistemic error is harmless. It establishes a necessary negative result: epistemic unreliability does not automatically scale into catastrophic misalignment in architectures that separate semantics from control and enforce time-based recovery.

Adaptive adversaries, deception, and agency-level attacks remain future work.

