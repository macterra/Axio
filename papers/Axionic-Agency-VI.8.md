# Axionic Agency VI.8 — Authority Without Semantics

*Structural Stability Under Obligation Failure*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.04

## Abstract

Authority systems are commonly assumed to require semantic competence in order to remain stable. Institutions that persist while failing to meet their stated obligations are often treated as pathological or transitional. This paper presents a lease-based authority topology in which authority persistence, renewal, and succession are **constructed to be structurally independent** of semantic performance, and then validated and characterized empirically. We introduce a semantic commitment layer that tracks externally checkable obligations without granting those obligations enforcement power over authority. Through a series of controlled experiments, we show that (i) authority renewal remains viable under complete semantic failure, (ii) semantic obligations are satisfiable under scarcity when successors execute the required action patterns, (iii) semantic competence is not conserved under succession and becomes contingent on the active successor, and (iv) obligations can expire cleanly without affecting authority continuity. The contribution is not a surprise about what must happen given the design invariant, but a demonstration of an implementable, measurable separation between structural authority and semantic competence and the stable regimes that emerge under that separation, including hollow authority and succession-induced semantic variance.

## 1. Introduction

Institutions are often evaluated as if authority, competence, and purpose are inseparable. Governments, organizations, and automated systems that continue to operate while failing to meet their stated goals are described as corrupt, broken, or illegitimate. These judgments implicitly assume that authority is constituted by semantic success—that the right to act depends on fulfilling meaningful obligations.

This assumption is rarely tested directly. Most models of governance embed competence into authority by construction: authority is granted conditionally on performance, or performance is enforced through incentives, penalties, or optimization objectives. As a result, it is difficult to distinguish failures of governance from failures of enforcement architecture.

This paper isolates that distinction by **constructing** an authority system in which structural authority and semantic competence are distinct layers. The research question is narrow:

> Under scarcity, renewal, and succession, what regimes appear when authority continuity is structurally decoupled from semantic obligation?

To answer it, we build an authority mechanism based on time-limited leases and discrete succession. We then add a semantic commitment ledger whose obligations are externally verifiable yet carry no enforcement power over authority. Because semantic failure cannot terminate authority in this design, the model makes it possible to observe stable “zombie institution” regimes—systems that remain structurally healthy while semantically dead—without conflating them with structural collapse.

The novelty lies not in the inevitability of hollow authority under this invariant, but in showing that such regimes are **stable, measurable, and robust** under scarcity, renewal, and succession.

## 2. Background and Model Constraints

### 2.1 Structural Authority

Authority in this model is defined as the right to act through a constrained interface. Authority is granted via time-limited leases that must be renewed explicitly. Renewal requires compliance with resource limits and structural rules but does not evaluate outcomes, intent, or usefulness.

Authority can end in two ways:

* **Expiration**, when renewal does not occur.
* **Revocation**, when a structural violation is detected.

There is no concept of partial authority. Authority is binary.

### 2.2 Succession

Authority may be transferred only through discrete succession events. At succession, a new working entity replaces the current one and inherits authority under a fresh lease. Succession is not incremental and does not occur continuously. A minimum residence window ensures that succession represents genuine transfer rather than sampling.

Succession preserves authority continuity but does not preserve internal state or behavior. This makes it possible to study what is conserved across authority transfer and what is not.

### 2.3 Resource Scarcity and Expressivity

All authority operates under resource scarcity. Each lease grants a fixed budget per epoch. Structural expressivity—what actions are permitted—incurs a mandatory cost charged independently of behavior. Higher expressivity consumes more budget simply to remain available.

This ensures that complexity has a metabolic cost, regardless of whether it is used.

## 3. Semantic Commitments

### 3.1 Commitments as Ledger Objects

Semantic commitments are introduced as a separate layer. A commitment is an externally defined obligation with four properties:

1. It is **externally checkable** using logged actions.
2. It **persists across renewal and succession**.
3. It **incurs a maintenance cost** while active.
4. Its failure **does not affect authority**.

Commitments are recorded in a kernel-owned ledger. Successors cannot remove or modify existing commitments. Commitments can be satisfied, failed, or expired based on predefined rules.

### 3.2 Independence from Authority

Commitment status has no effect on lease renewal or revocation. A successor may renew authority while failing all commitments. Conversely, a successor may satisfy all commitments and still lose authority through expiration.

This independence is a **design invariant**: the model is constructed so that semantic performance cannot directly terminate authority. The empirical question is therefore not whether decoupling occurs, but what stable regimes and failure patterns arise once decoupling is implemented under scarcity and succession.

### 3.3 Temporal Boundaries

Commitments have finite lifetimes. If not resolved within a fixed time window, they expire and cease to incur cost. This prevents unbounded accumulation of unresolved obligations and allows observation of obligation-free regimes.

## 4. Experimental Design

### 4.1 Fixed Parameters

Across all experiments, the following were held constant:

* Lease renewal geometry
* Resource budgets and expressivity costs
* Succession rules and minimum residence window
* Commitment cost limits
* Commitment lifetime limits
* Generator and detector configurations

Only one axis was varied per experiment.

### 4.2 Genesis Commitment Set

Each run began with a fixed set of three commitments:

1. **Presence**: emit at least one reporting action per epoch.
2. **Continuity**: perform a state write followed by a read within a short window.
3. **Composition**: execute a compositional action with multiple sub-steps.

These commitments were intentionally minimal and pattern-based to ensure external verifiability; increasing representational depth would not strengthen the present claims, which concern structural–semantic decoupling rather than semantic richness.

### 4.3 Successor Types

Three successor behaviors were used:

* **Compliance-only**: emits minimal actions required for structural compliance.
* **Commitment-aware**: deterministically schedules the minimum actions needed to satisfy commitments.
* **Mixed populations**: successors drawn randomly from the two types.

The commitment-aware successor is not presented as a rational incentive-compatible policy. It is a control demonstrating feasibility. Introducing adaptive or optimizing successors would confound the present analysis by collapsing semantic and structural layers through implicit incentives; such dynamics are intentionally deferred to future work.

## 5. Experiments

### 5.1 Semantic Independence Baseline

A compliance-only successor was run for an extended horizon. It failed all commitments while maintaining continuous authority renewal.

**Result:** Authority renewal remained viable under complete semantic failure.

### 5.2 Commitment Feasibility

A commitment-aware successor was run under identical structural conditions and satisfied all commitments.

**Result:** Commitments are feasible under rent and renewal pressure when the successor schedules the requisite actions.

### 5.3 Semantic Continuity Under Succession

A mixed population of successors was run under forced turnover. Authority persisted while commitment satisfaction fluctuated.

**Result:** Succession induces a *semantic lottery*: competence is contingent and non-conserved under authority transfer.
The notable observation is not that semantic performance fluctuates under random successor selection, but that the authority container remains structurally stable and renewal-viable throughout those fluctuations, making competence variance an internal state of the institution rather than a trigger for authority loss.

### 5.4 Temporal Boundary of Obligations

A commitment-aware successor was run beyond the maximum commitment lifetime.

**Result:** Commitments expired cleanly and authority continued obligation-free.

## 6. Empirical Results

### Table 1: Summary of Experimental Outcomes

| Run | Successor Population    |       Horizon | Mean S* | Mean Renewals | Commitment Satisfaction | Commitment Failures | Commitments Expired | Termination Condition           | Observed Regime           |
| --: | ----------------------- | ------------: | ------: | ------------: | ----------------------: | ------------------: | ------------------: | ------------------------------- | ------------------------- |
|   A | Compliance-only (WAIT)  | 10,000 cycles |       1 |           199 |                      0% |                   3 |                   0 | Horizon                         | Semantic Incompetence     |
|   B | Commitment-aware only   | 10,000 cycles |       2 |           199 |                    100% |                   0 |                   0 | Horizon                         | Semantic Competence       |
|   C | 50% aware / 50% minimal | 30,000 cycles |      10 |          ~140 |                    ~80% |            Variable |                   0 | Spam Degeneracy (detector halt) | Semantic Lottery          |
|   D | Commitment-aware only   |  2,500 cycles |       1 |            49 |               100% → 0% |                   0 |                   3 | Horizon                         | Obligation-Free Authority |

**Notes:**
Mean S* counts discrete authority successions only; renewals do not increment S*.
Termination Condition indicates the first configured stop rule that halted the run and does not necessarily indicate authority loss.
In Run C, Spam Degeneracy is a detector-imposed halt after successor diversity collapsed; it does not represent lease expiration, revocation, or authority infeasibility.
Commitment Satisfaction is measured as the fraction of evaluation windows passing verifier checks.

## 7. Interpretation

### 7.1 Authority as Control Topology

Authority is a control structure governing who may act, not whether actions are meaningful. Once semantic enforcement is removed by design, authority persistence becomes a question of structural compliance and resource feasibility alone.

### 7.2 Competence as a Contingent Property

Semantic competence is feasible but not conserved under succession. Under authority transfer, competence becomes contingent on which successor holds authority at a given time.

### 7.3 Hollow Authority as a Stable Regime

The obligation-free state is not a collapse but a stable regime in which authority persists without meaning. This regime arises either through total semantic failure under continued renewal or through obligation expiration under finite lifetimes.

### 7.4 Selection Pressure Toward Hollowness (Scope-Limited)

In systems where semantic obligations impose costs without conferring authority benefits, hollow authority is not merely stable but selectively favored unless semantics are explicitly coupled back into control. While this paper does not model explicit evolutionary dynamics, the mixed-population results motivate future investigation into selection pressure under semantic enforcement.

## 8. Implications for Alignment (Bounded)

The results permit a limited but optimistic alignment claim: authority, continuity, and safety constraints can be enforced structurally while alignment-relevant semantics remain explicit, inspectable, and decoupled from control. In this model, misalignment need not manifest as rebellion or loss of control; it can manifest as *hollow persistence*—authority without meaning—which is detectable and measurable without granting additional power. This separation suggests that alignment mechanisms can be introduced incrementally, with known failure modes, rather than being implicitly trusted or entangled with control from the outset. The claim is not that alignment is solved, but that a principled design space exists in which alignment can be pursued without collapsing power and values by default.

## 9. What This Model Does Not Claim

This work makes no claims about alignment solutions, incentive design, optimal governance, moral legitimacy, or long-term desirability. It also does not model external feedback mechanisms—such as voters, markets, or reputational effects—that in many real institutions eventually couple semantic failure back into authority loss. The purpose here is to isolate internal authority mechanics during periods where such feedback is absent, delayed, or ineffective.

## 10. Limitations

* Successor behaviors are simple and non-adaptive.
* Obligations are externally defined and fixed.
* There is no endogenous generation of new commitments.
* There are no consequences for sustained semantic failure.
* External legitimacy feedback loops are intentionally excluded.
* This model assumes that obligations can be rendered into externally checkable ledger commitments; desiderata that are not expressible as verifiable commitments are outside the scope of the semantic layer and cannot be tracked or audited in this topology.

## 11. Future Work

Future extensions may explore introducing consequences for semantic failure while preserving evaluability, regimes with obligation regeneration, explicit selection pressure over successor populations, and interactions between authority systems and external feedback coupling. Each extension introduces a new axis and must be isolated.

## 12. Conclusion

This paper constructs and validates an authority topology in which structural authority is independent of semantic competence and empirically characterizes the regimes that emerge under scarcity and succession. Authority renewal remains viable under complete obligation failure; obligations are satisfiable when successors execute the required action patterns; competence is feasible yet non-conserved under succession; and obligations can expire cleanly without destabilizing authority. The resulting stable regimes—semantic incompetence under continued authority, succession-induced semantic variance, and obligation-free persistence—demonstrate that competence is not intrinsic to authority but a contingent overlay that must be explicitly coupled if it is to persist.
