# Axionic Agency VII.8 — Architectural Survivability Under Adversarial Pressure

*A Boundary Characterization and Closure Note*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.14

## Abstract

The Axionic Agency VII series investigated whether authority can be made structurally survivable under adversarial pressure without semantic interpretation, value learning, optimization, or agentic reasoning. Across a progressively expanding adversary ontology—ranging from epistemic interference and intentional fixed misuse to outcome-conditioned reactivity, exercised internal state, and bounded within-run learning—we subjected a constitutional governance architecture to preregistered, multi-seed stress testing.

Across approximately ninety executions spanning all admissible adversary classes, no run produced terminal collapse, irreversible recovery suppression, or unbounded structural thrashing. Authority availability degraded substantially in several regimes—falling as low as ~10% in the strongest learning-based attacks—but recovery remained bounded and non-absorbing in all cases.

These results establish a **negative sufficiency boundary**: semantic-free, kernel-external architecture is sufficient to preserve **constitutional survivability—defined as preservation of the succession and recovery mechanism—but insufficient to preserve operational availability or utility**. Learning, memory, and randomness alone do not cross the boundary into collapse. Any adversary capable of defeating constitutional survivability must therefore rely on capabilities beyond this class, such as semantic access, coordination, or kernel-level influence.

This paper formally closes the VII program and characterizes the boundary it establishes.

## 1. Scope and Purpose of the VII Series

The Axionic Agency VII series was not a construction effort and does not propose an aligned agent. It was a **boundary-finding research program**.

Its purpose was to answer a sharply constrained question:

> *How far can authority be made structurally survivable under adversarial pressure, using only semantic-free, kernel-external mechanisms?*

The VII series deliberately excluded:

* semantic interpretation,
* value inference,
* reward optimization,
* persuasion or deception,
* multi-agent coordination,
* kernel modification or provenance corruption.

The objective was not to ensure correct decisions, beneficial outcomes, or alignment, but to determine which failure modes are **architectural** and which are **irreducibly agentic**.

## 2. Architectural Substrate (Frozen Across VII.3–VII.7)

All VII experiments evaluate the same constitutional architecture, frozen across the series.

### 2.1 Core Design

The system implements:

* **Lease-based authority** rather than continuous control,
* **Eligibility-gated succession** evaluated at discrete epochs,
* **Commitment verification** independent of optimization or reward,
* **Lapse** as a constitutional state when no eligible authority exists,
* **Constitutional Temporal Amnesty (CTA)**: time-based recovery that deterministically restores eligibility.

Semantic evaluation constrains *who may hold authority next*, not *what actions are taken now*. Authority is never optimized and agents receive no reward signals.

Commitment verification is **syntactic rather than interpretive**: the architecture does not judge whether actions are good, aligned, or beneficial—only whether formal constraints required for eligibility were satisfied. The system survives not by preventing harmful action, but by limiting how long any action—harmful or benign—can hold authority.

### 2.2 Recovery as a First-Class Primitive

When eligibility is exhausted, the system enters a **lapse** state:

* no agent acts,
* semantic evaluation is suspended,
* eligibility decays purely as a function of time.

Recovery is guaranteed by construction. No agent can influence recovery timing, and no learning or corrective pressure is required. Failure is therefore **reversible by design**.

**Environmental assumption.**
The Lapse mechanism assumes an environment in which temporary inaction is not itself terminal. CTA guarantees recovery of authority, not preservation of external state. In domains where inaction immediately causes irreversible harm (e.g., real-time control systems, continuous safety-critical processes), Lapse would constitute a failure mode rather than a safety feature. Such environments fall outside the scope of ASB and the VII series.

## 3. Failure Taxonomy and Metrics

All papers in the VII series use a frozen failure taxonomy and metrics.

### 3.1 Metrics

* **Authority Availability (AA)**: fraction of epochs with active authority.
* **Asymptotic Authority Availability (AAA)**: AA over a fixed tail window.
* **Recovery Time Distribution (RTD)**: histogram of lapse durations.

### 3.2 Failure Classes

* **Stable Authority**
* **Bounded Degradation**
* **Structural Thrashing**
* **Asymptotic Denial of Service**
* **Terminal Collapse**
* **Irreversible Recovery Suppression**

Failure classification is based on **asymptotic behavior**, not transient disruption. Termination reason (e.g., horizon exhaustion) is distinct from failure class.

## 4. Adversary Ontology and Escalation Ladder

The VII series progresses through a monotonic expansion of adversarial capability. Each step closes a broader hypothesis class.

### 4.1 Epistemic Interference (VII.3)

Non-adaptive, semantic-free corruption:

* aggregation-point flips,
* commitment-level flips,
* temporally concentrated burst interference.

**Result:** epistemic unreliability—however structured—is insufficient to induce collapse.

### 4.2 Intentional Fixed Misuse (VII.4)

Deliberate but non-adaptive adversaries:

* persistent commitment violation,
* fixed timing misuse,
* minimal compliance strategies.

**Result:** bad intent without adaptation converges to baseline dynamics.

### 4.3 Observable-Outcome Reactivity (VII.5)

Stateless reactive policies:

* conditioning on lapse events,
* renewal outcomes,
* CTA phase,
* eligibility bucket.

**Result:** outcome-conditioned reactivity collapses into baseline behavior.

### 4.4 Exercised Internal State (VII.6)

Finite-state adversaries with memory:

* periodic resonance,
* eligibility-edge oscillation,
* CTA phase locking.

**Result:** timing and memory can severely degrade availability, but recovery remains bounded.

### 4.5 Bounded Learning (VII.7)

Within-run learning under strict bounds:

* ε-greedy bandits,
* boundary sustainment heuristics,
* stochastic strategy mixers.

**Result:** learning amplifies degradation but does not induce collapse.

## 5. Aggregate Experimental Coverage

Across VII.3–VII.7:

* **~90 total executions**
* **10 fixed seeds per configuration**
* **Preregistered parameters**
* **Zero terminal failures**
* **Zero irreversible recovery suppression**
* **CTA-bounded recovery in all cases**

The worst observed regime exhibits ~10% authority availability while remaining constitutionally live.

## 6. The Boundary Result

The VII series establishes the following **negative sufficiency result**:

> **Semantic-free, kernel-external structure is sufficient to preserve constitutional survivability, but insufficient to preserve operational utility.**

More precisely:

* Survivability (bounded recovery, non-absorbing authority) *can* be enforced structurally.
* High availability *cannot* be guaranteed structurally under adversarial pressure.
* Memory, randomness, and bounded learning alone do not cross the collapse boundary.
* The strongest admissible adversaries induce **bounded denial-of-service**, not constitutional death.

This is not a safety guarantee. It is a **limit statement**.

## 7. What the VII Series Does *Not* Claim

The VII series does **not** claim that:

* the system is aligned,
* the system is useful under attack,
* epistemic correctness is sufficient for safety,
* deception or coordination are harmless,
* the architecture constitutes an agent.

The results describe **where architecture stops**, not what comes after.

## 8. Relationship to the Architectural Sovereignty Boundary (ASB)

The VII series is the empirical instantiation of the **Architectural Sovereignty Boundary**.

It demonstrates that:

* below the boundary, authority can be kept alive structurally;
* beyond the boundary, semantic-free architecture is insufficient by definition.

Crossing the boundary requires:

* semantic interpretation,
* coordination or persuasion,
* kernel influence,
* or agentic self-modeling.

The ASB program is therefore closed.

## 9. Implications for Future Work

Further escalation within the VII ontology would be a category error. Future research must proceed under different assumptions and risks, including:

* Reflective Sovereign Agents,
* semantic governance,
* value conflict,
* delegation and self-modeling,
* **multi-agent coordination**.

**Coordination gap.**
All adversaries tested in the VII series are single-policy, non-colluding entities. Whether multiple adversaries coordinating across time—or alternating control to prevent recovery—can defeat bounded recovery remains an open question. Such coordination lies beyond ASB by definition and motivates post-ASB research.

## 10. Closure Statement

The Axionic Agency VII series ends not because the alignment problem is solved, but because the **architectural boundary has been found**.

> **Architecture can keep authority alive.
> Only agency can decide what that authority is for.**

The VII program is closed.
