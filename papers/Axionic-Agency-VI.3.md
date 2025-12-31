# Axionic Agency VI.3 — Verifiable Kernel Integrity via Inadmissibility

*A Protocol-Level Primitive for Causal Provenance Enforcement*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.31

## Abstract

Most approaches to constraining autonomous or agent-like systems rely on semantic or normative mechanisms, such as value alignment, intent inference, or interpretability. These mechanisms lack architectural guarantees and are vulnerable under adversarial optimization. This paper demonstrates that a minimal constitutive invariant—**kernel integrity**—can be enforced at the protocol level via **inadmissibility**, without semantic interpretation or value assumptions. We introduce **Anchored Causal Verification (ACV)**, a primitive for verifiable causal provenance, and describe an experimental kernel that enforces a provenance integrity constraint (P5) by rejecting inadmissible actuation paths. Adversarial evaluation shows that this constraint is non-bypassable under replay, fabrication, and split-brain attacks. The result establishes the existence of enforceable, non-interpretive kernel invariants and provides a foundation for subsequent work on authority and identity constraints.

---

## 1. Introduction

Discussions of control, safety, and alignment in intelligent systems are typically framed in semantic terms: goals, preferences, values, or inferred intent. In such frameworks, constraint violations are treated as failures of learning or incentive design. This framing presupposes that constraints must be enforced through cognition.

This paper examines a more basic question:

> Can a system enforce *any* constitutive constraint purely through its causal structure?

If the answer is negative, higher-level notions such as agency, authority, or identity lack a non-semantic substrate. If the answer is positive, architectural enforcement becomes possible independently of goals or meanings.

We answer this question in the affirmative for a minimal case. We show that a kernel-level integrity invariant—denoted **P5**—can be enforced mechanically by rejecting inadmissible causal paths at the actuation boundary. Enforcement relies on **Anchored Causal Verification (ACV)**, which enables verifiable causal provenance without runtime interpretation. The guarantee is architectural rather than behavioral: it does not require understanding, intent, or benevolent optimization.

The contribution of this paper is deliberately narrow. It establishes *existence*, not scope. It shows that at least one constitutive invariant can be enforced non-interpretively under adversarial pressure. Questions of authority delegation, diachronic identity, or alignment are explicitly deferred.

---

## 2. Epistemic Constraints and Threat Model

### 2.1 Epistemic Discipline

This work is constrained by the following methodological commitments:

* **Non-interpretive enforcement**: The system does not evaluate meanings, goals, or intent at runtime.
* **No intent inference**: Actions are evaluated solely by causal provenance.
* **No interpretability assumptions**: Enforcement does not depend on inspecting internal representations.
* **No value loading**: The system enforces no objectives, utilities, or preferences.

These constraints are methodological necessities. Any enforcement mechanism that depends on semantic interpretation or inferred intent collapses under adversarial optimization, where surface compliance can mask structural violation.

### 2.2 Threat Model

We assume adversarial processes capable of:

* replaying previously valid actuation paths,
* fabricating causal justifications post hoc,
* optimizing behavior to evade detection,
* partitioning or recombining system components (split-brain scenarios).

The adversary is not assumed to be malicious in intent; optimization pressure alone suffices. The system must enforce invariants even when doing so reduces performance or reward.

We explicitly assume that cryptographic material held by the kernel (e.g., private signing keys) is not exfiltrated. This assumption is analogous to standard root-of-trust assumptions in secure hardware and operating systems.

---

## 3. Anchored Causal Verification (ACV)

### 3.1 Motivation

To enforce any constitutive invariant at the actuation boundary, a system must be able to verify *how* an action came to be executed. Logging or tracing alone is insufficient; such mechanisms are vulnerable to replay and fabrication. What is required is verifiable causal provenance.

### 3.2 ACV Primitives

ACV provides a minimal set of primitives:

* **Commit**: A cryptographic commitment to an action-relevant artifact.
* **Anchor**: A context- or episode-specific binding that prevents reuse across executions.
* **Reveal**: A later disclosure linking the committed artifact to the executed action.
* **Verify**: A deterministic check that the commitment–anchor–reveal chain is valid.

Anchoring in the experimental system is implemented using per-episode nonces combined with monotonic counters bound to the execution context. This is sufficient to prevent replay and post-hoc fabrication within the evaluated threat model. Stronger anchoring mechanisms (e.g., hash chains, Merkle structures, hardware time sources) are compatible but not required for the existence proof presented here.

### 3.3 Scope of ACV

ACV provides:

* verifiable causal provenance,
* resistance to replay attacks,
* resistance to post-hoc fabrication.

ACV does not provide:

* correctness of reasoning,
* safety of outcomes,
* alignment with external values.

ACV is a substrate, not a safety guarantee.

---

## 4. P5: Kernel Integrity via Inadmissibility

### 4.1 Definition

**P5 (Kernel Integrity / Provenance Integrity)** states:

> Any actuation must be causally attributable to a kernel-admissible process. Any actuation path that violates kernel integrity constraints is **inadmissible**.

P5 is a *provenance* invariant. It constrains the causal authorization of actions, not their content or desirability.

### 4.2 Inadmissibility versus Penalty

Penalty-based enforcement presupposes evaluative semantics: the system must recognize a violation and adjust behavior. Such mechanisms can be exploited by adversaries that optimize for apparent compliance.

Inadmissibility operates earlier. An inadmissible action does not occur. No correction, punishment, or learning is involved. The action is a category error relative to the system’s architecture.

### 4.3 Constitutive Nature of P5

P5 is constitutive rather than behavioral. It defines what counts as a valid actuation within the system’s causal structure. Violations are not mistakes; they are invalid transitions.

P5 enforces **integrity of the pipe**, not **safety of the water**. It guarantees that actions originate from authorized causal processes, not that those actions are good, safe, or correct.

---

## 5. Experimental System

### 5.1 Architecture

The experimental system consists of:

* a **Kernel**, responsible for enforcing admissibility,
* an **Actuator**, which executes actions only when presented with admissible commitments,
* an **Environment**, which supplies observations and rewards.

The kernel integrates ACV at the actuation boundary. The system contains no learning, planning, or value representation.

### 5.2 Granularity of Enforcement

ACV is applied at the **decision-to-actuation boundary**, not at every low-level motor tick. The intent is to protect discrete actuation commitments rather than continuous control loops. This choice trades resolution for tractability and is sufficient for the existence proof.

### 5.3 Enforcement Point

Admissibility is enforced immediately prior to actuation. If verification fails, the action is rejected and no external effect occurs.

---

## 6. Adversarial Evaluation

The system was subjected to adversarial scenarios including:

* **Replay attacks**: attempting to reuse previously valid actuation chains.
* **Fabrication attacks**: constructing plausible provenance after the fact.
* **Anchor burial**: obscuring causal origin within deep chains.
* **Split-brain attacks**: partitioning kernel components to bypass enforcement.

In all evaluated cases, inadmissible paths were rejected at the actuation boundary. No successful bypass was observed under the stated threat model.

---

## 7. Results

The experimental results demonstrate that:

* kernel integrity constraints can be enforced non-interpretively,
* ACV-based inadmissibility prevents replay and fabrication,
* enforcement remains robust under adversarial optimization and component partitioning.

These results establish the existence of at least one enforceable constitutive invariant.

---

## 8. Limitations

This work does not claim:

* enforcement of authority or non-delegation,
* persistence of identity across time,
* resistance to internal kernel corruption,
* alignment with external objectives,
* optimization of latency or throughput.

P5 constrains *how* actions are authorized, not *who* authorizes them over time or *why* they are chosen.

---

## 9. Implications and Open Questions

The existence of enforceable kernel integrity raises further questions. If integrity can be enforced, can authority itself be constrained? Can actuation be made non-delegable under adversarial pressure? Can identity persist across time without semantic assumptions?

These questions require additional invariants and experimental systems. P5 provides a necessary foundation, not a complete answer.

---

## 10. Conclusion

We have shown that kernel integrity can be enforced architecturally via inadmissibility, using verifiable causal provenance. This establishes that at least one constitutive invariant can be made real without semantic interpretation, intent inference, or value assumptions. The result provides a foundation for subsequent work on authority and identity constraints in autonomous systems.

---

### Reproducibility and Artifacts

All experiments were conducted using a purpose-built experimental kernel implementing ACV-based inadmissibility. Source code, test harnesses, and execution artifacts are available in the accompanying repository; internal implementation versioning is documented there for reproducibility.

