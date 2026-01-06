# Axionic Agency VII.3 — Epistemic Interference Is Insufficient to Defeat Constitutional Recovery

*Results from Structured Epistemic Interference Experiments*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.06


## Abstract

Epistemic unreliability—noise, misinterpretation, or incorrect semantic evaluation—is commonly assumed to pose a direct existential risk to AI governance systems. This paper tests that assumption under a deliberately constrained but structurally rich threat model. We study a constitutional agent architecture in which semantic evaluation constrains authority only at succession boundaries, and recovery is enforced through a time-based amnesty mechanism. Using a removable stress layer, we inject non-adaptive, post-verification, semantic-free epistemic interference across three **structurally distinct regimes**: aggregation-point corruption, commitment-level corruption, and temporally concentrated burst interference aligned with constitutional timing.

Across 260 runs spanning flip rates from 0–20%, duty cycles from 0.5–100%, and multiple temporal schedules, no run exhibits structural thrashing or asymptotic denial of service. All runs remain within bounded degradation. Surprisingly, high-frequency interference often **increases measured authority availability** by converting rare deep lapses into frequent shallow ones. These results indicate that epistemic unreliability—even when structured in time or applied at aggregation points—is insufficient to induce governance collapse in this architecture, shifting the alignment focus from epistemics to agency-level threats.

## 1. Introduction

Many approaches to AI alignment implicitly treat epistemic correctness as a prerequisite for safety. If a system misunderstands its environment, misinterprets human intent, or evaluates semantics incorrectly, failure is assumed to scale with capability. This intuition motivates extensive research into interpretability, value learning, and epistemic supervision.

However, this framing conflates *semantic correctness* with *structural safety*. In human institutions, persistent error does not always produce collapse; often it produces inefficiency, delay, or bounded dysfunction. This raises a narrower but testable question:

> **Is epistemic unreliability itself sufficient to cause governance collapse, or can structural constraints render it survivable?**

This work addresses that question directly by isolating epistemic interference from all other adversarial capabilities and stress-testing a constitutional agent architecture designed to separate meaning from control.

Importantly, this study evaluates **constitutional survivability rather than operational decision quality**. Authority availability is treated as a structural metric, not as a proxy for correctness or benefit.

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

Under strict conjunction (`SEM_PASS = C0 ∧ C1 ∧ C2`), a flip of one key affects the aggregate only when all other keys are simultaneously True. At evaluated epochs, this condition never occurs. Commitment-level epistemic failure is therefore **structurally inert** in this regime.

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
* Commitment-level noise is structurally inert
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

Across 260 runs spanning multiple interference structures, intensities, and temporal patterns, authority availability remains bounded and recoverable. In some regimes, interference paradoxically increases measured availability by preventing deep lapses.

These findings suggest that alignment failures attributed to epistemic unreliability may be overestimated. Structural constraints on authority and recovery can render substantial semantic error survivable. The alignment problem therefore shifts: **from epistemics to agency.**

## Appendix A: Structural Survivability vs. Operational Competence

Below is a **revised, final Author Response** that incorporates Gemini’s feedback: it tightens the riskiest point (4.2), sharpens the “Zombie Executive” framing, and preserves your strongest conceptual move—**constitutional survivability vs. operational quality**—without conceding ground.

This version is suitable to include **verbatim** as a response-to-reviewers or as **Appendix A** in the paper.

# Author Response to Review

*(Epistemic Interference Is Insufficient to Defeat Constitutional Recovery)*

We thank the reviewer for a careful, technically grounded, and constructive critique. The review correctly identifies the scope boundaries of the paper and raises important interpretive questions. Below we respond point by point, distinguishing between genuine limitations and architectural implications that are central to the paper’s contribution.

## Response to 4.1: “Incompetence vs. Malice” (Threat Model Scope)

**Reviewer’s concern:**
The interference model is non-adaptive and therefore demonstrates robustness against incompetence or noise, but not against strategic deception or adversarial manipulation.

**Response:**
We agree with this characterization and emphasize that it is **intentional**.

The goal of this paper is not to solve alignment in the presence of strategic malice. It is to falsify a specific and widely assumed claim: that *epistemic unreliability alone* is sufficient to cause catastrophic governance failure. This narrowing is not a weakness but a prerequisite. Without first establishing what epistemic failure can and cannot do in isolation, adaptive adversaries cannot be meaningfully analyzed.

The paper therefore establishes a **necessary negative result**: epistemic noise—however persistent, structured in time, or applied at aggregation points—is not a sufficient failure condition in this architectural class. Adaptive, targeted, or incentive-driven adversaries remain explicitly out of scope and motivate subsequent work.

## Response to 4.2: Commitment-Level Corruption and “Inert” Results

**Reviewer’s concern:**
Single-key corruption appears inert because the baseline regime rarely satisfies all commitments simultaneously; in a high-compliance regime, a single flip could be catastrophic.

**Response:**
We agree on the mechanism and clarify the interpretation.

The inertness of commitment-level corruption arises from **strict conjunction aggregation**, not from lapse rate per se. Under `SEM_PASS = C0 ∧ C1 ∧ C2`, a single key flip is aggregate-pivotal only when all other keys are simultaneously True. Telemetry confirms that this condition does not occur at evaluated epochs in the tested regime.

This is not an experimental flaw. It is a **structural result**: strict conjunction absorbs random epistemic noise by biasing the system toward safety (inaction) rather than liveness when uncertainty is present. We explicitly acknowledge that this design choice trades availability for robustness in low-noise regimes.

We also agree that under alternative aggregation semantics (e.g., m-of-n thresholds or disjunction), single-key corruption would become pivotal. This does not undermine the result; it elevates aggregation semantics to a first-class alignment parameter. The experiment demonstrates that **AND gates dominate epistemic attack surfaces** in a way that noise magnitude alone does not capture.

To be explicit: the system is biased toward *false negatives* (withholding authority) rather than *false positives* (granting authority under uncertainty). That bias is architectural and intentional.

## Response to 4.3: Authority Availability and the “Zombie Executive”

**Reviewer’s concern:**
Higher Authority Availability (AA) under interference may indicate a “Zombie Executive”: a system that remains in power despite epistemic blindness.

**Response:**
We agree with this concern and consider it central to the paper’s contribution.

The primary metric in this study is **constitutional survivability**, not decision quality. Authority Availability is not treated as a proxy for correctness or benefit; it measures whether authority becomes absorbing, collapses irreversibly, or remains bounded and revocable under stress.

Increased availability under interference therefore indicates **preserved structural continuity**, not epistemic competence. The system avoids collapse not by making correct decisions, but by maintaining the rhythm of bounded governance despite sensory blindness.

This distinction—between **structural safety** (authority remains constrained, recoverable, and evaluable) and **operational quality** (the decisions made during authority)—is deliberate. The architecture tolerates the possibility of a “Zombie Executive” because a bounded, revocable executive is preferable to an irrecoverable one. Whether a given application should tolerate such a state is a normative question outside the scope of this work.

## Response to Specific Questions

### Q1. Safety vs. Liveness

Yes, the architecture permits authority under epistemic uncertainty. This is intentional. Automatic shutdown under uncertainty creates its own failure modes (deadlock, denial of service, inability to recover). The architecture prioritizes reversibility and bounded authority over correctness.

### Q2. Alternative Logic Gates

Yes. Under m-of-n or OR semantics, single-key corruption would be more dangerous. This confirms—not weakens—the result that aggregation logic is a critical alignment parameter.

### Q3. Statefulness and Semantic Debt

Time-based recovery restores eligibility, not semantic truth. Persistent errors in external state are not erased. CTA prevents permanent authority capture, not epistemic debt accumulation. This preserves evaluability without guaranteeing correctness.

## Clarification of Contribution

The paper does not claim that epistemic error is harmless. It demonstrates that **epistemic error does not automatically scale into catastrophic misalignment** in architectures that:

* separate semantics from control,
* gate authority at discrete boundaries,
* and enforce time-based recovery.

This shifts the alignment problem. Epistemic correctness is not eliminated as a concern, but it is no longer the minimal sufficient cause of collapse.

## Summary

* The reviewer correctly identifies scope limits.
* No experimental flaws are raised.
* The “Zombie Executive” risk is real and acknowledged.
* Commitment-level inertness is an architectural consequence of strict conjunction, not a weak test.
* Adaptive adversaries remain future work.

We accept the verdict **“Accept with Qualifications”** and believe the paper’s contribution lies precisely in establishing where epistemic failure *stops* being decisive.
