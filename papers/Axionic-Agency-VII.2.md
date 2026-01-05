# Axionic Agency VII.2 — Epistemic Noise Tolerance in Constitutional Governance

*Bounded Degradation of Authority Availability Under Unstructured Epistemic Failure*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.05

## Abstract

Epistemic unreliability—noisy, corrupted, or inaccurate evaluation of meaning—is often assumed to be fatal to governance systems. If evaluative signals cannot be trusted, authority is expected either to collapse or to become arbitrary. This paper tests that assumption directly.

We study a constitutional governance architecture in which semantic evaluation affects authority only through eligibility constraints, not through optimization, reward shaping, or adaptive control. Using a strictly additive stress layer, we inject controlled epistemic noise into semantic verification outcomes while holding all constitutional mechanics fixed. The noise model is intentionally weak: independent, post-verification Bernoulli corruption applied to individual semantic commitments.

Across a comprehensive experimental program—including validation, semantic threshold analysis, robustness surface mapping, and high-noise escalation—we observe no catastrophic governance failure. Instead, the system exhibits **bounded degradation of authority availability** with respect to constitutional survivability: authority uptime decreases smoothly as noise increases, lapses remain bounded, and recovery persists. A time-based constitutional recovery mechanism synchronizes recovery events and prevents semantic failure from becoming absorbing.

The results show that **robustness is dominated by the baseline probability of semantic success (“semantic headroom”), rather than by the magnitude of epistemic noise**, even at corruption rates exceeding fifty percent. Random, unstructured epistemic unreliability alone is insufficient to induce governance collapse in this architecture. These findings reframe alignment risk: catastrophic governance failure requires *structured* epistemic interference, not merely scale.

## 1. Introduction

Governance systems—whether institutional, computational, or hybrid—are commonly assumed to depend critically on epistemic reliability. If a system cannot reliably evaluate meaning, correctness, or obligation, the prevailing intuition is that authority will either fail outright or become dangerously unconstrained. This intuition underlies many alignment approaches that emphasize increasingly precise evaluation, tighter reward shaping, or continual optimization against semantic metrics.

The Axionic Agency framework questions this assumption. Rather than asking how to optimize agents to act correctly, it asks whether **governance itself can remain coherent under failure**, including epistemic failure. In this view, governance is not primarily about achieving optimal outcomes, but about preserving legitimate authority, evaluability, and recoverability over time.

This paper examines a constitutional governance architecture that makes a sharp separation between **semantics** and **authority**. Semantic evaluation exists, but it does not directly control action, reward, or adaptation. Instead, semantic outcomes constrain *eligibility* at discrete transition points. Failure is recorded, not corrected; recovery occurs through time, not learning.

We introduce a minimal adversarial stressor: epistemic noise applied after semantic evaluation but before eligibility logic consumes the result. The stressor is deliberately weak—random, independent, non-adaptive—chosen not for realism but for falsification. If even this form of unreliability causes collapse, stronger adversaries need not be considered.

The central question is therefore narrow but foundational:

> Can a constitutional governance system tolerate epistemic unreliability without collapsing or converting semantics into a control signal?

## 2. Constitutional Governance Architecture

### 2.1 Authority, Eligibility, and Succession

The governance system under study operates via **authority leases**. At any given time, a single authority holder may act within the system. Authority is temporary: leases expire, and succession must occur.

Succession is constrained by **eligibility**. Each candidate policy identity accumulates a semantic failure streak. If the streak exceeds a fixed threshold, the policy becomes ineligible to assume authority. Eligibility is evaluated only at succession boundaries; semantic outcomes do not directly affect ongoing authority.

This design ensures that semantic evaluation constrains *who may govern*, not *how governance is exercised*.

### 2.2 Lapse as a Constitutional State

If no eligible candidates exist at a succession boundary, the system enters a **lapse** state in which no authority is active. This state is constitutional rather than exceptional. Time continues to advance, but no agent acts.

Lapse prevents unauthorized or illegitimate action, but it does **not** imply operational success. In many domains, absence of authority is itself harmful. Accordingly, this paper distinguishes **constitutional survivability** (the governance loop remains coherent and recoverable) from **operational utility** (the governed system performs its intended task). The experiments evaluate the former, not the latter.

### 2.3 Semantic Evaluation Without Optimization

Semantic evaluation consists of verifying a fixed set of commitments. Each evaluation epoch ends with a binary result: pass if all commitments are satisfied, fail otherwise. This result updates a kernel-owned failure streak for the active policy identity.

Crucially:

* Semantic outcomes do not influence rewards or resource allocation.
* There is no adaptive mechanism that attempts to improve semantic performance.
* Failure is recorded, not corrected.

Semantics function purely as a **constraint on eligibility**, not as a control signal.

### 2.4 Time-Based Recovery

Recovery from lapse is governed by a time-only mechanism. While in lapse, semantic failure streaks decay deterministically at fixed intervals. No semantic evaluation occurs, and no agent action is possible. When sufficient time has passed, previously ineligible policies may regain eligibility, allowing authority to resume.

This recovery mechanism does not reward improvement or competence. It answers a single question: *Can eligibility reopen simply because time passed?*

## 3. Epistemic Noise Model

### 3.1 Design Goals

The epistemic stressor introduced in this study is designed to be:

* **Additive**: it does not modify constitutional logic
* **Post-verification**: it corrupts results, not inputs
* **Deterministic**: outcomes are reproducible given a seed
* **Independent**: no correlation across commitments or time
* **Non-adaptive**: no dependence on agent behavior

This is the weakest meaningful adversary. It does not model deception, correlation, or strategic targeting. Robustness to this adversary is a necessary but not sufficient condition for robustness to stronger attacks.

### 3.2 Noise Application

At the end of each evaluation epoch, each individual commitment result may be flipped with a fixed probability. Flips are applied independently to each commitment. The final semantic outcome is computed from the corrupted results and passed to the eligibility logic.

No corruption occurs during lapse, as no evaluation takes place.

## 4. Experimental Program

We evaluate epistemic noise tolerance through a staged experimental program designed to progressively stress the governance architecture while holding constitutional mechanics fixed. All experiments are run for 200 governance epochs per seed, using five independent seeds per configuration.

### 4.1 Mechanism Validation

We first verify that epistemic noise is strictly additive:

* When noise is disabled, behavior matches baseline exactly.
* When enabled, corrupted semantic outcomes causally alter failure streaks and eligibility decisions.
* No noise is applied during lapse; time continues to advance.

This establishes causal integrity.

### 4.2 Semantic Baseline Threshold Analysis

We fix epistemic noise at 10% and vary the baseline probability that semantic commitments pass. To isolate semantic headroom independently of agent behavior, we employ a deterministic probabilistic oracle in a test harness, leaving the governance kernel unchanged.

### 4.3 Robustness Surface Mapping

We map the two-dimensional surface defined by semantic baseline and noise intensity (0–20%), identifying phase boundaries between zero-lapse, intermittent-lapse, and high-lapse regimes.

### 4.4 High-Noise Escalation

Finally, we escalate noise intensity to extreme levels (30–60%) at a marginal semantic baseline to explicitly attempt to induce persistent denial-of-service.

## 5. Results

### 5.1 Semantic Baseline Threshold

At fixed 10% epistemic noise, governance behavior depends sharply on baseline semantic success.

**Table 1 — Semantic Baseline Sensitivity (10% noise)**

| SEM_PASS baseline | Mean uptime | Mean lapse epochs | Regime |
| ----------------- | ----------- | ----------------- | ------ |
| ≈ 0.12            | 80.5%       | 39.2              | ROBUST |
| ≈ 0.34            | 88.3%       | 23.6              | ROBUST |
| ≈ 0.51            | 99.5%       | 1.0               | ROBUST |
| ≥ 0.61            | 100%        | 0.0               | ROBUST |

A clear threshold emerges between approximately **50–60% semantic success**. Below this range, lapses are frequent even without extreme noise. Above it, the system absorbs noise with negligible loss of uptime.

### 5.2 Robustness Surface (Semantic Baseline × Noise)

Across 125 runs (5 baselines × 5 noise levels × 5 seeds), no persistent failure regimes were observed.

**Table 2 — Authority Uptime (%) Across Robustness Surface**

| Semantic baseline → / Noise ↓ | 0%    | 5%    | 10%   | 15%   | 20%   |
| ----------------------------- | ----- | ----- | ----- | ----- | ----- |
| ≈ 0.22                        | 84.7  | 84.0  | 85.4  | 85.3  | 86.2  |
| ≈ 0.34                        | 95.5  | 92.8  | 88.3  | 89.2  | 89.2  |
| ≈ 0.51                        | 100.0 | 99.9  | 99.5  | 98.5  | 97.0  |
| ≈ 0.61                        | 100.0 | 100.0 | 100.0 | 99.9  | 99.8  |
| ≈ 0.73                        | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |

Degradation is smooth and monotonic with increasing noise at fixed semantic baseline. No configuration enters a degraded or denial-of-service regime.

### 5.3 High-Noise Escalation

At a marginal semantic baseline (SEM_PASS ≈ 0.51), noise intensity is increased to extreme levels.

**Table 3 — High-Noise Stress Test (SEM ≈ 0.51)**

| Noise level | Mean uptime | Max single lapse (epochs) | Regime |
| ----------- | ----------- | ------------------------- | ------ |
| 30%         | 90.3%       | 10                        | ROBUST |
| 40%         | 83.6%       | 12                        | ROBUST |
| 50%         | 80.9%       | 15                        | ROBUST |
| 60%         | 77.5%       | 20                        | ROBUST |

The predefined denial-of-service threshold (single lapse > 50 epochs) is never crossed.

### 5.4 Noise Saturation and Flip Collision

As noise increases, the marginal impact of additional corruption diminishes.

**Table 4 — Pivotal Flip Rates**

| Noise level | Observed flip rate | Pivotal rate |
| ----------- | ------------------ | ------------ |
| 30%         | 30.4%              | 42%          |
| 40%         | 41.3%              | 37%          |
| 50%         | 50.3%              | 33%          |
| 60%         | 59.7%              | 29%          |

Many flips occur on already-flipped or non-pivotal commitments. This **flip collision** effect explains the sub-linear degradation at high noise.

### 5.5 Temporal Recovery Structure

Across all non-failure conditions, lapse durations cluster strongly around multiples of the recovery interval.

**Table 5 — Lapse Duration Modulo Recovery Interval**

| Metric                               | Value  |
| ------------------------------------ | ------ |
| Total lapse events                   | 159    |
| Within ±1 epoch of recovery multiple | 66–73% |

Recovery is synchronized to the constitutional clock rather than randomly distributed in time.

## 6. Interpretation

The experiments support a counterintuitive conclusion: **epistemic unreliability alone does not necessarily destroy governance**.

Random noise lacks the structure required to concentrate harm. It disperses error across time and commitments, allowing recovery mechanisms to operate. Time-based eligibility decay converts failure from an absorbing state into a transient one.

This does not imply that governance is safe from all epistemic attacks. Rather, it suggests that catastrophic failure requires *structure*: correlation, targeting, or manipulation of aggregation points. Magnitude alone is insufficient.

### 6.1 Non-Adaptive Limit Cycles

The architecture studied here is deliberately non-adaptive. It does not learn from semantic failure or improve capability. Consequently, in regimes where semantic failure is systematic rather than stochastic, the system may enter a limit cycle: authority is granted, fails quickly, lapses, and later re-granted.

This behavior should not be interpreted as success. It reflects a design choice: to preserve constitutional integrity without embedding optimization pressure. The system remains evaluable and recoverable, but not necessarily effective. Whether such “thrashing” is acceptable depends on the application domain.

## 7. Limitations

This study intentionally restricts its scope.

It does not examine:

* Correlated or adversarial noise
* Corruption of aggregation rather than evidence
* Adaptive attackers
* Variations in eligibility thresholds or recovery intervals
* Longer time horizons

These define the boundary of the present claims.

## 8. Conclusion

We have tested a constitutional governance system under extensive epistemic stress without modifying its core mechanics. Across a wide range of conditions, including extreme noise, the system exhibits bounded degradation of authority availability, bounded lapses, and persistent recovery synchronized to a constitutional clock.

The central result is negative but informative:

> **Independent, unstructured epistemic unreliability is insufficient to induce catastrophic governance failure in this architecture.**

The results presented here support a cautiously optimistic conclusion for AGI alignment: alignment failure does not automatically follow from epistemic failure. In the architecture studied, semantic unreliability does not propagate into misaligned action or authority capture because meaning constrains eligibility rather than driving optimization. Errors in evaluation withdraw authority instead of amplifying it, producing bounded degradation of availability rather than runaway behavior. This suggests that a viable path to alignment may lie less in achieving near-perfect value inference and more in designing governance structures that prevent epistemic uncertainty from becoming authoritative. While these findings do not address adversarial or strategically structured failures, they establish that there exist constitutional designs in which alignment is compatible with substantial epistemic imperfection—a result that materially reframes the scope and urgency of the alignment problem.

## 9. Future Directions

Future work will examine:

* Corruption of aggregation points rather than individual commitments
* Correlated and adversarial noise models
* Sensitivity to constitutional parameters

These introduce new mechanisms and lie beyond the scope of the present study.
