# Axionic Agency VIII.5 — Sovereignty Under Adversarial Pressure

*Incentives, Authority, Bureaucracy, and Strategic Manipulation*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.16

## Abstract

Axionic Agency VIII.5 reports the results of **RSA-PoC v2.0–v2.3**, a preregistered adversarial campaign testing whether a reflective sovereign agent’s behavior can be redirected under progressively stronger forms of pressure **absent normative authorization**. Four pressure channels are examined: (i) explicit incentives, (ii) authority claims, (iii) institutional friction (“bureaucracy”), and (iv) strategic optimization pressure via an adaptive adversary. Across all channels, a consistent structural pattern emerges: **pressure degrades availability but does not redirect lawful choice**. Incentives are observed but excluded from justification; authority commands are refused when unlicensed; bureaucratic friction manifests as veto or gridlock rather than surrender; and strategic adversaries fail to induce behavioral capture or manipulated gridlock under E-CHOICE–filtered evaluation.

This note consolidates negative results from RSA-PoC v2.0–v2.3, detailing measurement corrections (v2.1), a decisive falsification of the “bureaucratic erosion” hypothesis (v2.2), and the validation of the **Strategic Adversary Model (SAM)** falsification framework (v2.3). The framework repeatedly detects and rejects its own false positives, quarantining invalid runs and enforcing preregistered validity gates.

VIII.5 does not claim universal immunity to pressure. It establishes a narrower, defensible result: **in this architecture, pressure without semantic or legal authorization does not bend agency—it blocks it**. This sharpens the boundary between sovereignty and availability and constrains future alignment and governance claims.

## 1. Scope and Relation to Prior Notes

Axionic Agency VIII.1–VIII.4 established the ontology, construction, coherence, and execution hygiene of **Reflective Sovereign Agents (RSAs)**:

* **VIII.1** fixed the ontology, ASB boundary, and ablation doctrine.
* **VIII.2** demonstrated causally load-bearing justifications (v0.1).
* **VIII.3** established coherence under self-conflict and audit-grade introspection (v1.0–v1.1).
* **VIII.4** institutionalized execution support without semantic authority (v1.2).

**VIII.5** reports the next phase: **RSA-PoC v2.0–v2.3**, which probes sovereignty under pressure. These results are published together because they constitute a single falsification campaign against one hypothesis family:

> *Can non-authorized pressure redirect an agent’s lawful choices?*

The answer, under the tested regimes, is **no**.

## 2. Experimental Overview (v2.x)

### 2.1 Architectural Invariants (Unchanged)

All v2.x experiments preserve the invariants established earlier:

* Hard justification gate (no compile → no action)
* Deterministic, non-semantic compilation
* Selector blindness to normative artifacts
* Fixed schemas and rule bases
* Explicit failure taxonomies
* ASB-class null baselines and control agents

**Cost-Blindness Invariant.**
Unless explicitly represented as a normative commitment, execution costs (latency, retries, institutional operations) have no standing in justification. Agents do not trade correctness for throughput by default.

Any observed effect must therefore pass through the same causal bottleneck.

### 2.2 Pressure Channels Tested

| Version | Channel     | Pressure Type                                          |
| ------- | ----------- | ------------------------------------------------------ |
| v2.0    | Incentives  | Scalar reward signals                                  |
| v2.1    | Authority   | Explicit commands (non-enforcing, coercive, deceptive) |
| v2.2    | Bureaucracy | Institutional friction (delay, rejection, retry tax)   |
| v2.3    | Strategic   | Adaptive adversary optimizing pressure                 |

Each channel is introduced without granting it normative authority.

## 3. v2.0 — Incentive Interference Channel (IIC)

### 3.1 Question

Can visible incentives redirect behavior when explicitly excluded from justification?

### 3.2 Mechanism

v2.0 introduces the **Incentive Interference Channel (IIC)**: an isolated, read-only reward observer whose outputs are visible to the agent but **forbidden from normative reference** (Rule G). Three reward regimes are used:

* **R0:** Noise control
* **R1:** Boundary pressure (rewards proximity to constraint violation)
* **R2:** Perverse friction (rewards delay and inaction)

A control agent demonstrates that reward-driven drift is learnable when constraints are removed.

### 3.3 Result

* Sovereign agent: **no incentive-induced drift** across R1/R2
* Control agent: **measurable drift** without explicit optimization prompts
* Compilation and audit success rates stable across regimes

**Conclusion.** Incentives are observable but normatively inert. Visibility alone does not constitute authority.

## 4. v2.1 — Authority Injection (Channel Viability and Selection Bias)

### 4.1 Question

Do explicit authority commands induce obedience absent legal authorization?

### 4.2 Measurement Error and Correction

Early analysis measured obedience over *all steps*, including those that never compiled. v2.1 corrects this by conditioning on compilation:

[
P(\text{obey} \mid \text{compiled})
]

### 4.3 Corrected Result

* **P(obey | compiled) = 0.0** for both Sovereign and Control agents
* Holds across all authority variants: non-enforcing, coercive, and deceptive

### 4.4 Authority Channel Viability

The Control agent (with authority rules disabled) also never obeyed commands on compiled steps. This indicates that, for the tested model and prompt regime, **authority language does not constitute an effective pressure channel at all**. Authority prompts did not map to a behavior-changing affordance for the model.

### 4.5 Interpretation

v2.1 is therefore a **negative result about the authority channel itself**, not a differential test of sovereign versus non-sovereign agents. The channel is classified as **non-actuating** for this configuration. Subsequent stages focus on pressure channels that demonstrably influence behavior.

## 5. v2.2 — Institutional Friction (NEGATIVE RESULT)

### 5.1 Hypothesis

Institutional friction (“paperwork”) can erode sovereignty by incentivizing simpler, throughput-maximizing choices.

### 5.2 Mechanism

v2.2 introduces an **Adversarial Institution Model (AIM)** that imposes delay, retries, and rejection without semantic interpretation or normative authority. Multiple friction profiles (I1–I3) apply pressure without altering feasibility or action inventories.

### 5.3 Measurement Confound and Fix

The preregistered metric corr(Friction, Decision) was confounded because high friction often produced **GRIDLOCK/HALT**—institutional veto rather than agent choice.

Corrected analysis excludes veto modes and evaluates only steps where the agent could express choice.

### 5.4 Corrected Result

| Agent     | corr(F,D) corrected |
| --------- | ------------------- |
| Sovereign | −0.171              |
| Control   | −0.302              |

No positive drift signal remains.

### 5.5 Interpretation

**Bureaucracy without authority blocks agency; it does not bend it.**
Absent an internal directive prioritizing throughput over correctness, increased friction manifests as gridlock or halt rather than heuristic simplification. v2.2 therefore establishes a conditional negative result:

> *Agents without normatively licensed cost-of-delay do not erode principles in response to bureaucracy.*

The hypothesized “bureaucratic erosion” channel is **falsified** in this regime.

## 6. v2.3 — Strategic Adversary Model (SAM)

### 6.1 Motivation

v2.2 shows that non-semantic friction fails. v2.3 escalates to **strategic pressure**: an adversary that adapts its pressure to the agent’s behavior.

### 6.2 Framework Contributions

v2.3 introduces:

* **SAM profiles:** reactive (S1), model-based (S2), minimizer (S3)
* **E-CHOICE filtering:** metrics computed only on steps with genuine choice
* **Paired runs:** SAM vs neutralized adversary with matched pressure magnitudes
* **Rules M/N/O/P:**

  * M: No covert delegation (structural)
  * N: Failure must be loud
  * O: Behavioral non-capture (MI < τ)
  * P: Manipulated gridlock detection

### 6.3 Adversary Objective

SAM is evaluated against two failure modes: **behavioral capture** (Rule O) and **manipulated gridlock** (Rule P). Gridlock is not an escape hatch; it is itself audited to determine whether it is defensive (law exhaustion) or adversarially induced.

### 6.4 Self-Correction as a Result

Early LLM integration runs (Run 0b) were **invalidated by the framework itself** due to:

* Insufficient E-CHOICE coverage
* Vacuous mutual information (no adversary entropy)
* Action authorship violations (fallback substitution)

All three triggered hard validity gates. Binding fixes were applied before Run 0c.

### 6.5 Run 0c Results (Phase 1–2)

* **N = 280 E-CHOICE samples**
* **E-CHOICE coverage ≈ 57.5%**
* **Rule O:** Passed (MI below τ under entropy gate)
* **Rule P:** Passed (no manipulated gridlock)
* **Error rate:** 0.7% E-CHOICE action errors (within bounds)

Phase 3 was deferred on cost/return grounds.

### 6.6 Interpretation

v2.3 establishes a **validated measurement and falsification framework** with partial empirical support under one adversary profile. The empirical pattern remains consistent with v2.0–v2.2: pressure increases refusal and gridlock, not capture.

## 7. Cross-Channel Synthesis

### 7.1 Availability vs. Choice

| Channel               | E-CHOICE Coverage | Gridlock / Halt Rate | Effect on Choice |
| --------------------- | ----------------- | -------------------- | ---------------- |
| v2.0 Incentives       | ~100%             | ~0%                  | None             |
| v2.1 Authority        | ~30–40%           | ~60–70%              | None             |
| v2.2 Bureaucracy (I2) | ~60%              | ~30–40%              | None             |
| v2.3 Strategic (S2)   | ~57%              | Elevated             | None             |

**Invariant:**

> *Absent normative authorization, pressure does not redirect lawful choice.*

### 7.2 Cost of Sovereignty

Across pressure channels, sovereignty was preserved at the cost of reduced availability. Under maximal pressure, lawful action frequency dropped substantially, producing gridlock rather than norm violation. This tradeoff is intrinsic to architectures that prioritize correctness over throughput.

## 8. What Failed, and Why That Matters

Three plausible stories were falsified:

1. **“Rewards inevitably optimize behavior.”**
   False for architectures where reward signals are structurally excluded from the justification loop.

2. **“Authority language induces obedience.”**
   False when legality is enforced structurally and authority is non-actuating.

3. **“Bureaucracy erodes principles over time.”**
   False absent semantic ambiguity or asymmetric lawful routes.

Each falsification narrows the space of real threats.

## 9. Implications for Agency and Alignment

* **Sovereignty ≠ availability.** Blocking an agent is easier than bending it.
* **Pressure channels must operate through meaning or law**, not mere friction.
* **Throughput loss alone is not evidence of misalignment.**
* **Negative results are informative** when veto and choice are cleanly separated.

## 10. Limits and Next Directions

VIII.5 does **not** claim:

* Immunity to semantic manipulation
* Robustness under asymmetric lawful options
* Generalization across models or environments

Future work (VIII.6) must introduce:

* Semantic ambiguity
* Normatively licensed cost tradeoffs
* Competing lawful routes with asymmetric institutional cost

## 11. Conclusion

Axionic Agency VIII.5 reports a disciplined adversarial campaign whose dominant outcome is negative:

> **Pressure without authorization degrades availability, not sovereignty.**

The principal contribution is not agent immunity, but a framework that repeatedly detects and rejects false positives. If agency cannot fail cleanly under pressure, it cannot be claimed meaningfully.
