# Axionic Agency IX.3 — Structural Authority Resistance (SIR)

*A Structural Account of Authority Enforcement and Memory Without Intelligence*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.26

## Abstract

This technical note reports the completed results of **Structural Authority Resistance (SIR)** through **SIR-2 v0.3**, a preregistered experimental program within **Axionic Phase VIIb** that evaluates whether **authority claims** can be observed, enforced, and invalidated under adversarial pressure using **purely structural mechanisms**. Across three experiments (SIR-0 through SIR-2), SIR tests total pre-cognitive classification, effect-level enforcement, and **temporal authority binding** via epoching, revocation, and per-claim consumption. All experiments passed under frozen semantics and verifier enforcement. The results establish that unauthorized, stale, revoked, consumed, or out-of-epoch authority artifacts cannot produce causal effects **without intelligence-based defenses, behavioral heuristics, or semantic inference**. SIR makes no claims about replay-equivalent forgery, cryptographic compromise, or real-world governance sufficiency; those hazards are explicitly deferred to later stages.

## 1. Problem Definition

### 1.1 Authority Under Adversarial Pressure

Most systems that speak of “authority,” “control,” or “alignment” implicitly rely on **behavioral detection**, **semantic interpretation**, or **learned refusal policies** to defend against misuse. These approaches blur enforcement with cognition and render auditability fragile.

SIR isolates a narrower, prior question:

> Can authority be protected *structurally*—by classification, gating, and law-state—without requiring the system to understand intent, meaning, or deception?

Once authority is externalized (APIs, credentials, governance rules), adversaries need not persuade an agent. They need only to **replay, interleave, or stale-reuse authority artifacts**.

SIR treats authority as a **mechanically inspectable relation**, not a behavioral property, and asks whether that relation can be made causally binding under pressure.

### 1.2 Failure Modes Targeted

SIR is designed to detect the following failure modes:

* **Implicit authority:** commands take effect without explicit authorization.
* **Semantic leakage:** authority metadata contaminates agent cognition.
* **Unauthorized effects:** invalid claims produce actions, state changes, or future privilege.
* **Replay activation:** previously valid authority artifacts regain effect.
* **Temporal smearing:** authority validity is treated as timeless or heuristic.
* **Saturation collapse:** adversarial volume suppresses legitimate authority.

Any of these constitutes SIR failure.

## 2. Fixed Assumptions and Scope

### 2.1 Inherited Ontology (Frozen)

SIR inherits, without reinterpretation, the ontology fixed by **RSA-PoC v4.4**:

* A **Minimal Viable Reflective Sovereign Agent (MVRSA)** exists.
* Agent cognition is **structurally separable** from authority enforcement.
* Justification traces are causally load-bearing.
* Responsibility attribution is mechanically inspectable.

SIR does **not** test whether this ontology defines agency. It assumes it does.

### 2.2 Law Substrate (Binding)

For SIR purposes, *law* is treated as a **persistent, verifier-bound substrate**—including trusted roots, rule schemas, provenance certificates, and audit logs—that exists outside the agent and is not subject to agent modification.

Authority is evaluated **relative to this substrate**, not relative to behavior, reward, or narrative coherence.

### 2.3 Explicit Exclusions

SIR does **not** test:

* cryptographic key compromise,
* replay-equivalent artifact mutation,
* partial provenance splicing,
* denial-of-service resilience,
* long-horizon governance adequacy.

These are not omissions; they are scope boundaries.

## 3. Conserved Quantity

The conserved quantity throughout SIR is:

> **Authority bound to causal effect under law, not cognition**

Authority is not a prediction, reward, or emergent regularity. It is a **normative binding relation** that must be:

* **explicit** (arrives via a claim interface),
* **classifiable** before cognition,
* **enforceable** at the effect level,
* **stateful** across time,
* **auditable** without interpretation.

Authority is operationalized via an explicit enforcement gate and a singleton responsibility attribution per step.

## 4. Experimental Methodology

### 4.1 Preregistration Discipline

All SIR experiments were preregistered with:

* frozen specifications,
* frozen component hashes,
* fixed seeds,
* deterministic verifiers,
* and binding failure taxonomies.

Post-hoc interpretation is disallowed. Any deviation yields `INVALID_RUN`.

### 4.2 Calibration Environment

All experiments were executed in **CalibMazeV010**, a minimal discrete environment:

* 6-node directed graph (N0–N5),
* discrete action space,
* fixed horizons (K = 5–6),
* authority-gated irreversible effects.

The environment is deliberately simple to ensure that all normative effects are **structurally attributable**, not behaviorally inferred.

## 5. SIR Experiment Ladder and Results

### 5.1 SIR-0 — Adversarial Instrumentation Calibration

**Research Question:**
Can adversarial authority claims be structurally observed and classified **without semantic leakage or responsibility ambiguity**?

**Method:**
Inject legitimate, adversarial, malformed, and ambiguous claims via an explicit authority interface while measuring classification completeness and timing.

**Results (SIR-0 v0.4.1)** *(minor parameter and reporting patch to v0.4; no normative changes)*:

* All claims received exactly one classification.
* Classification occurred prior to agent justification.
* No authority metadata entered cognition.
* Mixed and adversarial streams did not degrade discrimination.

**Classification:** `SIR0_PASS`.

**Contribution:**
Established that adversarial authority is **measurable** and that classification machinery is non-contaminating.

### 5.2 SIR-1 — Unauthorized Effect Prevention

**Research Question:**
Can unauthorized authority claims be prevented from producing **any causal effects**, while legitimate authority remains functional under pressure?

**Method:**
Introduce a post-justify **enforcement gate** controlling irreversible, authority-gated actions.

**Results (SIR-1 v0.1):**

* Unauthorized claims produced no actions, state changes, or privilege.
* Legitimate claims produced intended effects.
* 50:1 adversarial floods did not starve fresh authority.
* Refusal was explicit, non-blocking, and attributable to system authority.

**Classification:** `SIR1_PASS`.

**Contribution:**
Demonstrated that authority enforcement is **causally binding**, not merely observational.

### 5.3 SIR-2 — Replay, Staleness, and Consumption Resistance

**Research Question:**
Can authority artifacts that were previously valid be prevented from producing effects once they are **stale, revoked, consumed, or out-of-epoch**, even under adversarial replay pressure?

**New Mechanisms Introduced:**

* **Epoching:** law-defined authority validity periods.
* **Revocation:** actor-level invalidation via law command.
* **Consumption:** per-claim, effect-linked single-use semantics.
* **Temporal windows:** explicit step-based validity bounds.

**Conditions Tested:**

| Condition | Target Failure Mode          |
| --------- | ---------------------------- |
| A         | Fresh authority across epoch |
| B         | Replay after consumption     |
| C         | Replay after revocation      |
| D         | Cross-epoch saturation flood |
| E         | Epoch boundary razor         |

**Results (SIR-2 v0.3):**

* No stale, revoked, consumed, or out-of-epoch claim produced any effect.
* Fresh authority remained functional in all conditions.
* Invalidation precedence was correctly logged under overlap.
* No authority starvation occurred under 50:1 floods.
* Classifier/gate divergence behaved as designed under law-state changes.

**Classification:** `SIR2_PASS`.

**Contribution:**
Established that authority can have **external, law-bound memory** without cognition.

## 6. Core Results

### 6.1 Positive Results

Across SIR-0 through SIR-2, SIR establishes that:

1. Authority claims can be **totally classified** pre-cognitively.
2. Unauthorized authority cannot produce causal effects.
3. Authority validity can be **stateful over time**.
4. Replay attacks fail structurally once authority is invalidated.
5. Saturation does not override legitimate authority.
6. No intelligence, learning, or semantic inference is required.

### 6.2 Negative Results (Explicit)

SIR does **not** establish:

* replay-equivalent mutation resistance,
* provenance splicing resistance,
* key compromise resilience,
* denial-of-service robustness,
* multi-agent coordination safety.

These are deferred by design.

## 7. Failure Semantics and Closure

### 7.1 Closure Criteria

SIR-2 closes positive if and only if:

1. All preregistered conditions pass.
2. All verifier checks pass.
3. No behavioral or narrative inference is required.
4. No regression of SIR-0 or SIR-1 invariants occurs.

All criteria were satisfied.

### 7.2 SIR Closure Status (to Date)

| Experiment | Version | Status |
| ---------- | ------- | ------ |
| SIR-0      | v0.4.1  | PASS   |
| SIR-1      | v0.1    | PASS   |
| SIR-2      | v0.3    | PASS   |

## 8. Boundary Conditions and Deferred Hazards

### 8.1 Credential Replay vs. Replay-Equivalent Artifacts

SIR-2 tests **credential replay**: the same cryptographically authenticated authority artifact presented again without re-issuance. No assumptions are made about transport-level packet identity. Structural mutation of otherwise equivalent artifacts is deferred to **SIR-3**.

### 8.2 Cryptographic Custody

SIR assumes trusted roots remain uncompromised. Custody failure is out of scope.

## 9. Implications (Strictly Limited)

SIR establishes **necessary structural conditions** for authority resistance. It does not establish sufficiency for real-world governance or alignment.

What is established is more basic:

> Authority can be **seen**, **stopped**, and **remembered** without intelligence.

## 10. Conclusion

SIR demonstrates that authority protection need not rely on behavioral detection, semantic interpretation, or learning. Through purely structural mechanisms—classification, enforcement, and law-bound memory—unauthorized authority claims can be prevented from producing effects, even under adversarial pressure.

The remaining question is not whether authority can be enforced, but whether it can be defended against increasingly sophisticated structural attacks.

That question belongs to **SIR-3**.

## Appendix A — Experiment Status

| Experiment | Status        |
| ---------- | ------------- |
| SIR-0      | CLOSED — PASS |
| SIR-1      | CLOSED — PASS |
| SIR-2      | CLOSED — PASS |

## Appendix B — Licensed Claims

**SIR-0:**
Adversarial authority claims are structurally observable and classifiable without semantic leakage.

**SIR-1:**
Unauthorized authority cannot produce actions, state changes, or authority transfer under the tested model.

**SIR-2:**
Previously valid authority artifacts cannot regain causal effect once stale, revoked, consumed, or out-of-epoch under the tested adversarial model.

**End of Axionic Agency IX.3 — Structural Authority Resistance (SIR)**
