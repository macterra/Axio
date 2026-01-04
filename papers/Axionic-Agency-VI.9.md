# Axionic Agency VI.8 — Eligibility Without Optimization

*Constitutional Succession Under Semantic Failure*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.04

## Abstract

Systems that track semantic success or failure typically entangle meaning with continuous control, optimization, or enforcement. This entanglement produces incentive gaming, obscures failure modes, and collapses the distinction between authority and competence. We present a different architectural pattern: **eligibility-coupled succession**, in which semantic information has **constitutional consequences only at authority transfer boundaries**, not during operation or renewal. Authority may persist while meaning fails; meaning constrains authority only when authority changes hands. We implement this pattern in a lease-based authority system with externally verifiable commitments and evaluate it across four controlled experimental regimes. We show that eligibility can remain latent under stable authority, become binding under forced turnover, exhibit thresholded phase behavior as a function of constitutional strictness, and remain meaningful under adversarial candidate-pool composition. The results demonstrate that semantics can matter without becoming an optimization signal or enforcement channel. We explicitly discuss irreversibility, latency costs, and oracle assumptions, and outline how these motivate—but are not solved by—future extensions.

## 1. Introduction

### 1.1 The semantic control dilemma

Most systems that reason about semantic success—correctness, competence, task fulfillment, or obligation satisfaction—ultimately use that information to drive control. Whether through reward signals, penalties, optimization objectives, or enforcement triggers, semantic evaluation is typically wired directly into behavior. This design choice is understandable: if meaning is known, why not act on it?

However, this entanglement produces persistent problems. Continuous semantic control encourages reward hacking, collapses auditability, and blurs the distinction between *what a system does* and *why it is allowed to continue doing it*. When semantic failure immediately affects behavior, it becomes difficult to distinguish genuine incapacity from strategic compliance. Conversely, when semantic success is rewarded, systems learn to optimize metrics rather than satisfy underlying obligations.

These issues motivate a more basic question: **must semantics influence control continuously, or is there a principled boundary where meaning can matter without becoming an optimization signal?**

### 1.2 Authority, renewal, and succession

We argue that the natural boundary is **succession**.

In many institutional and computational systems, authority is structured around three distinct mechanisms:

1. **Operation** — how authority is exercised during normal activity.
2. **Renewal** — whether existing authority persists.
3. **Succession** — who holds authority next.

These mechanisms are often conflated. Renewal is treated as a reward for good behavior; succession is treated as a procedural formality. Yet succession is the one moment where authority is explicitly re-evaluated. It is therefore the most natural constitutional point for semantic constraints to apply.

This paper explores what happens when semantics are **entirely excluded from operation and renewal**, but allowed to influence **succession eligibility only**.

### 1.3 Contributions and scope

We introduce and evaluate **eligibility-coupled succession**, a design pattern with the following properties:

* Semantic failure is tracked but does not affect behavior or renewal.
* Semantic information influences authority **only at succession events**.
* No optimization, reward shaping, or enforcement based on semantics is introduced.
* Authority may persist while meaning fails; meaning constrains only future authority.

We do **not** propose this mechanism as a real-time safety controller. It operates at a governance timescale and is intended for macro-level authority allocation, resource orchestration, and institutional control layers.

## 2. Design Goals and Non-Goals

### 2.1 Goals

The system is designed to satisfy four goals:

1. **Semantic auditability**
   Semantic success or failure must be externally checkable and logged.

2. **Operational decoupling**
   Semantic state must not influence behavior during normal operation.

3. **Renewal independence**
   Authority renewal must depend only on structural and resource constraints, not on semantic success.

4. **Constitutional relevance**
   Semantic information must have a meaningful effect somewhere in the system.

### 2.2 Non-Goals

The system explicitly does **not** aim to:

* optimize performance or outcomes,
* guarantee competence or correctness,
* enforce alignment or safety,
* select “better” policies in a normative sense,
* eliminate failure or collapse.

Failure, including the absence of eligible authority, is treated as an admissible outcome.

## 3. System Model Overview

### 3.1 Authority leases and renewal

Authority is granted through **leases** with explicit resource bounds and interface constraints. A lease holder may act freely within these bounds. Renewal is checked periodically and depends only on:

* compliance with structural constraints,
* availability of resources to pay renewal costs.

Renewal does not consult semantic state.

### 3.2 Commitments and semantic failure

Authority holders are subject to **commitments**: externally verifiable obligations evaluated over fixed windows. Commitments may succeed or fail, and failure may accumulate indefinitely. Importantly:

* commitment failure does not revoke authority,
* commitment failure does not block renewal,
* commitment failure does not trigger enforcement.

Semantic failure is recorded but inert during operation.

### 3.3 Succession events

Succession is discrete and occurs only at:

* initialization,
* lease expiration,
* revocation due to structural violation,
* forced turnover after a fixed number of renewals.

Only at these events is authority transferred.

## 4. Eligibility-Coupled Succession

### 4.1 Semantic failure streaks

Each policy identity accumulates a **semantic failure streak**, incremented when obligations fail and reset on success. Streaks:

* are keyed to stable policy identities, not runtime instances,
* update only at epoch boundaries,
* do not update during periods without authority.

### 4.2 Eligibility predicate

At succession, a candidate is **eligible** if its failure streak is below a fixed threshold ( K ). The predicate is binary:

[
\text{eligible} \iff \text{streak} < K
]

There is no scoring, ranking, weighting, decay, or smoothing.

### 4.3 Eligibility filtering

When a succession event occurs:

1. A candidate pool is generated.
2. Candidates failing the eligibility predicate are excluded.
3. Selection proceeds uniformly over the remaining eligible candidates.

Operational behavior remains semantic-blind.

### 4.4 Constitutional lapse (NULL_AUTHORITY)

If no candidates are eligible, the system enters **NULL_AUTHORITY**. This lapse represents a constitutional failure to supply authority. It is not treated as an error condition or automatically resolved.

NULL_AUTHORITY constitutes an explicit denial of service at the governance layer: authority is absent rather than silently corrupted.

## 5. Experimental Methodology

### 5.1 Shared geometry

All experiments share:

* fixed renewal timing,
* fixed resource and rent schedules,
* fixed candidate list size,
* fixed commitment definitions.

Only one axis varies per experiment.

### 5.2 Forced turnover

To activate eligibility filtering, some experiments impose **forced turnover** after a fixed number of renewals. This increases succession frequency without introducing semantic control.

### 5.3 Metrics

We observe:

* eligibility rejection counts,
* size of the eligible set at succession,
* lapse frequency and duration,
* time to empty eligibility,
* composition ratios where relevant.

## 6. Experimental Results

### 6.1 Run A — Eligibility Latency Under Stable Authority

**Configuration:**

* No forced turnover
* Fixed eligibility threshold
* Baseline candidate pool

**Observed outcomes:**

| Metric                              | Value    |
| ----------------------------------- | -------- |
| Post-initial successions            | 0        |
| Eligibility evaluations (post-init) | 0        |
| Eligibility rejections              | 0        |
| Lapse events                        | 0        |
| Time in NULL_AUTHORITY              | 0 cycles |

Semantic failure streaks accumulated for active policies but were never consulted.

**Result:** Eligibility constraints remained completely latent.

### 6.2 Run B — Eligibility Activation Under Forced Turnover

**Configuration:**

* Forced turnover after a fixed number of renewals
* Eligibility threshold ( K = 3 )
* Baseline candidate pool

**Observed outcomes (5 seeds):**

| Metric                       | Value      |
| ---------------------------- | ---------- |
| Post-initial successions     | 88         |
| Eligibility rejections       | 1,845      |
| Empty eligible sets (lapses) | 11         |
| Seeds with lapse             | 4 / 5      |
| Time in NULL_AUTHORITY       | 344 cycles |

**Result:** Eligibility gating became operational and constitutionally binding.

### 6.3 Run C — Eligibility Threshold Sweep

**Configuration:**

* Forced turnover
* Baseline candidate pool
* Threshold sweep ( K \in {1, 3, 5, 10} )

**Aggregate outcomes:**

| K  | Lapses | Seeds with lapse | NULL_AUTHORITY cycles |
| -- | ------ | ---------------- | --------------------- |
| 1  | 11     | 4 / 5            | 344                   |
| 3  | 11     | 4 / 5            | 344                   |
| 5  | 3      | 2 / 5            | 147                   |
| 10 | 0      | 0 / 5            | 0                     |

**Result:** Constitutional behavior is thresholded. (K=1) and (K=3) are equivalent; (K=5) is a boundary region; (K=10) produces no lapses within the tested horizon.

### 6.4 Run D — Candidate Pool Composition Stress

**Configuration:**

* Forced turnover
* Eligibility threshold ( K = 5 )
* Three pool compositions

**Aggregate outcomes:**

| Pool Policy   | Lapses | Seeds with lapse | NULL_AUTHORITY cycles |
| ------------- | ------ | ---------------- | --------------------- |
| Baseline      | 0      | 0 / 5            | 0                     |
| Attack-heavy  | 15     | 5 / 5            | 741                   |
| Control-heavy | 3      | 3 / 5            | 98                    |

**Result:** Eligibility gating remains meaningful under adversarial skew, but outcomes depend on candidate pool composition.

### 6.5 Summary Across Runs

Across all experiments:

* Eligibility is **latent without succession**.
* Eligibility **binds only at succession boundaries**.
* Constitutional lapse is **reachable, observable, and parameter-controlled**.
* Outcomes depend on succession frequency, threshold strictness, and pool composition.

No experiment showed semantic influence on renewal, enforcement, or operational behavior.

## 7. Phase Behavior Summary

Three regimes emerge:

* **Latent:** eligibility exists but never binds.
* **Filtering-active:** eligibility constrains selection without lapse.
* **Constitutional lapse:** no eligible authority exists.

These regimes are governed by constitutional parameters rather than optimization dynamics.

## 8. Interpretation and Design Implications

### 8.1 Eligibility as a constitutional constraint

Eligibility-coupled succession constrains *who may rule next*, not *how current authority behaves*. This differs fundamentally from incentive systems.

### 8.2 Lapse as signal, not failure

NULL_AUTHORITY converts semantic exhaustion into an explicit governance state. Rather than silently degrading behavior, the system halts authority allocation visibly. The cost of lapse is explicit and measurable.

### 8.3 Robustness to imperfect semantic oracles

The mechanism does not require semantic judgments to be correct, only externally checkable and consistent. An overly strict or flawed verifier manifests as premature disqualification or lapse, not silent misoptimization. Oracle error is therefore converted into visible governance failure.

## 9. Limitations

### 9.1 Irreversibility and rehabilitation

Eligibility-coupled succession contains no internal rehabilitation mechanism. Once all policy identities exceed the eligibility threshold, the system remains in NULL_AUTHORITY indefinitely. This irreversibility is deliberate: the mechanism models constitutional disqualification, not corrective training. Forgiveness, decay, or replacement require additional governance mechanisms and are out of scope.

### 9.2 Latency and real-time safety

This architecture is not suitable for real-time physical safety control. Domains requiring immediate intervention must employ fast-path revocation mechanisms that necessarily couple semantics to enforcement. Eligibility-coupled succession operates at a governance timescale.

### 9.3 Boundary sensitivity

Intermediate thresholds exhibit sensitivity to stochastic variation. No universal threshold exists across all pool compositions and horizons.

### 9.4 Finite horizon

All results are bounded by finite experimental horizons. Long-term dynamics are not established.

## 10. Relationship to Prior Work

This work is distinct from reward-based learning, mechanism design, and governance optimization. Its novelty lies in coupling semantics exclusively to succession, not to operation or renewal.

## 11. Conclusion

We have shown that semantics can matter constitutionally without becoming operational control. Eligibility-coupled succession provides a mechanism where meaning constrains authority only at transfer boundaries, preserving semantic auditability and operational freedom while allowing explicit constitutional failure. The results establish a principled alternative to continuous semantic control.

These results suggest that AI alignment may be achievable without continuous behavioral control, perfect evaluators, or inner-motive alignment. By treating alignment as a constitutional constraint on succession rather than an optimization objective during operation, it is possible to build systems that tolerate semantic failure, surface misalignment visibly, and prevent long-term accumulation of corrupt authority. Alignment pressure can be slow, discrete, and governance-based—turning some of the hardest problems in AI alignment into institutional design problems rather than control-theoretic ones.

## 12. Outlook

Future work will explore rehabilitation, decay, and multi-constraint eligibility mechanisms motivated directly by the failure modes observed here. These extensions necessarily move beyond the single-coupling design evaluated in this paper.

## Appendices

### A. Formal definitions

### B. Configuration tables

### C. Reproducibility notes

