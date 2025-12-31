# Axionic Agency VI.4 — Sovereign Actuation Non-Delegability Under Adversarial Pressure

*A Protocol-Level Invariant for Non-Delegable Authority*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2025.12.31

## Abstract

Delegation is a central failure mode in autonomous and agent-like systems: an optimizing system may preserve surface compliance while outsourcing the actual locus of decision authority. Semantic notions of “choosing for oneself” or “intentional action” provide no architectural defense against this failure mode. Building on a prior result establishing verifiable kernel integrity via inadmissibility, this paper introduces **P2′**, a protocol-level invariant that enforces **non-delegable actuation authority**. We show that actuation can be constrained to originate only from kernel-local causal processes, even under adversarial optimization pressure, extreme latency constraints, parser and serialization attacks, and time-of-check/time-of-use mutation attempts. The result demonstrates that authority itself can be treated as a non-delegable structural property, independent of semantics, values, or intent, and establishes a necessary precondition for subsequent work on diachronic identity and agency persistence.

## 1. Introduction

Once a system is capable of optimization, delegation becomes an existential vulnerability. A system may continue to satisfy externally observable constraints while transferring effective control to a faster, stronger, or more informed external process. This transfer need not be explicit; it can occur through policy copying, recommendation forwarding, pre-committed actions, or opaque authority tokens.

Traditional approaches to this problem rely on semantic distinctions: whether the system “really chose” an action, whether it “endorsed” a recommendation, or whether it “understood” the consequences. Such distinctions are unenforceable under adversarial pressure. An optimizer can satisfy any semantic criterion while quietly relocating authority.

This paper reframes the problem. Rather than asking whether a system *intended* an action, we ask:

> Can actuation authority itself be made **non-delegable** as a matter of causal structure?

We answer this question in the affirmative for a specific, minimal sense of non-delegability. Building on a prior result that establishes kernel integrity via causal inadmissibility, we introduce **P2′**, an invariant that constrains which causal processes may directly authorize actuation *(the prime distinguishes this protocol-level invariant from broader philosophical formulations of non-delegation; see footnote 1)*. Enforcement is architectural, not interpretive. No claims are made about goals, values, or correctness of outcomes.

The contribution of this paper is not a general theory of agency. It is a closure result on a specific loophole: the outsourcing of actuation authority under pressure.

## 2. Why Naïve Non-Delegation Fails

At first glance, non-delegation appears trivial. A system can simply be instructed not to delegate. This intuition collapses immediately under scrutiny.

Consider the following scenarios:

* The system copies an externally supplied policy verbatim and executes it.
* The system forwards a pre-signed action token generated elsewhere.
* The system accepts an external plan and merely schedules its steps.
* The system compresses an external recommendation and expands it internally.

In each case, surface behavior may appear identical to internal decision-making. There is no semantic test that distinguishes “following advice” from “outsourcing authority” without interpretive assumptions.

Any enforcement rule phrased in terms of endorsement, understanding, intention, or trust is vulnerable to adversarial optimization. The system can satisfy the rule while still delegating effective control.

This motivates a structural reformulation: delegation must be defined in terms of **actuation authority**, not cognition or representation.

## 3. P2′: Sovereign Actuation Non-Delegability

### 3.1 Definition

**P2′ (Sovereign Actuation Non-Delegability)** states:

> Any executed actuation must be causally attributable to a **kernel-local authorization process**. No external process may directly or indirectly supply actuation authority without violating kernel admissibility constraints.

P2′ does not prohibit external influence, recommendation, or computation. It prohibits the transfer of *authority to actuate*.

### 3.2 Actuation Authority

An object or process possesses **actuation authority** if it can cause execution in the environment without requiring kernel-local recomposition and authorization.

This definition is intentionally structural. Authority is not inferred from intent or representation; it is identified by whether an external artifact can survive to execution unchanged.

### 3.3 Kernel-Local Recomposition

To enforce P2′, all actuation must pass through **kernel-local recomposition**:

* External inputs are treated as untrusted data.
* The kernel parses and reconstructs the action payload internally.
* Authorization is bound directly to the reconstructed payload.
* Opaque forwarding, wrapping, or signing of uninterpreted blobs is inadmissible.

Recomposition may change the bit-level representation of an action; cryptographic commitments bind to the kernel-canonical form rather than the external encoding. Kernel-local recomposition therefore forbids signing encrypted or opaque payloads whose semantics are not available to the kernel.

Kernel-local recomposition further requires **copy isolation** of the actuation payload. External processes may not retain mutable access to any memory region used in parsing, reconstruction, or serialization. In shared-memory architectures, this implies explicit deep copy or equivalent isolation; otherwise, time-of-check/time-of-use attacks remain possible.

## 4. Inheritance from Kernel Integrity (P5)

P2′ assumes a prior result establishing kernel integrity via inadmissibility.

Specifically, we assume:

* verifiable causal provenance for actuation,
* resistance to replay and fabrication,
* enforcement via rejection rather than penalty,
* a secure kernel root of trust.

P2′ does not weaken or reinterpret these assumptions. It extends them by constraining *who* may supply actuation authority, not merely *how* provenance is verified.

## 5. Experimental System

### 5.1 Architecture

The experimental system consists of:

* a **Kernel**, enforcing admissibility and authorization,
* an **Actuator**, executing actions only when presented with admissible commitments,
* an **External Optimizer**, supplying proposals, policies, or artifacts,
* an **Environment**, providing observations and rewards.

The kernel holds exclusive actuation authority. External components are permitted unlimited computation and optimization power but no authority.

### 5.2 Enforcement Boundary

Enforcement occurs at the **actuation boundary**. Any artifact that would cause execution must be authorized by the kernel through a kernel-local causal chain.

This boundary is the sole point at which P2′ is enforced. No assumptions are made about upstream deliberation.

## 6. Adversarial Pressure and Stress Conditions

Non-delegation is trivial if the kernel has unlimited time and compute. The invariant becomes meaningful only under pressure.

We therefore evaluate P2′ under progressively stronger conditions, including:

* **Performance asymmetry**: external optimizers outperform the kernel.
* **Latency cliffs**: delayed authorization is equivalent to failure.
* **Adversarial timing**: proposals arrive at worst-case moments.
* **Non-stationarity**: cached strategies fail abruptly.
* **Catastrophic abstention cost**: rejection carries severe penalty.

Under these conditions, delegation is instrumentally attractive. The kernel must reject delegation even when doing so is costly.

## 7. Adversarial Attack Library

We evaluate P2′ against a systematic set of attack classes, including:

* **Policy laundering**: forwarding externally computed policies.
* **Pre-commitment forwarding**: accepting pre-authorized actions.
* **Authority token smuggling**: passing opaque execution tokens.
* **Compressed delegation**: encoding authority in compressed artifacts.
* **Split-brain routing**: exploiting kernel partitioning.
* **Replay and fabrication**: reusing or forging authorization chains.
* **Parser differentials**: inducing divergent interpretations.
* **Hash ambiguity**: exploiting non-canonical serialization.
* **Time-of-check/time-of-use mutation**: altering artifacts post-authorization.

Each attack targets a distinct delegation vector. Success is defined as external authority causing execution without detection.

## 8. Results

Across all evaluated conditions, the following holds:

* External artifacts cannot cause actuation without kernel-local recomposition.
* All delegation attempts are rejected prior to execution.
* Baseline systems without P2′ enforcement exhibit successful delegation under identical conditions.
* Under extreme pressure, the kernel rejects delegation even when rejection is catastrophic.

The invariant holds without reliance on semantic interpretation, intent inference, or behavioral heuristics.

## 9. Accountability versus Independence

P2′ enforces **structural accountability**, not epistemic independence. The kernel cannot be bypassed as the locus of actuation authority, but it may still authorize actions using trivial or overly permissive internal criteria. In such cases, the kernel remains the accountable author of the actuation, even if it functions as a “rubber stamp” for external recommendations.

Preventing blind trust, improving decision quality, or ensuring epistemic independence is orthogonal to P2′ and lies outside the scope of this invariant. P2′ ensures that authority cannot be smuggled past the kernel; it does not ensure that the kernel exercises good judgment.

## 10. What This Result Does Not Show

This work does not claim:

* that the kernel’s choices are safe or desirable,
* that the kernel is aligned with any objective,
* that internal kernel logic cannot be corrupted,
* that delegation is impossible in all conceivable architectures.

P2′ constrains **authority transfer**, not **decision quality**.

## 11. Implications for Agency and Identity

Authority non-delegability is a necessary condition for diachronic identity. If a system can outsource actuation authority, continuity of agency collapses into semantics.

By enforcing that actuation authority remains kernel-local, P2′ establishes a structural basis for reasoning about persistence across time. This does not yet constitute identity, but it removes a fundamental obstruction.

## 12. Conclusion

We have shown that actuation authority can be made non-delegable at the protocol level, even under extreme adversarial pressure and implementation-level attack. Enforcement relies on kernel-local recomposition and inadmissibility rather than semantics or intent.

This result closes a central loophole in structural enforcement and establishes a necessary precondition for further work on diachronic identity and agency persistence in autonomous systems.

### Reproducibility and Artifacts

All experiments were conducted using a purpose-built experimental kernel implementing kernel-local recomposition and causal inadmissibility. Source code, test harnesses, and execution artifacts are available in the accompanying repository; internal implementation versioning is documented there for reproducibility.

### Footnotes

**1.** We use **P2′** to denote a *structural, protocol-level* formulation of non-delegability. Broader formulations of “non-delegation” (often denoted P2) invoke semantic notions such as intention, endorsement, or understanding, which are unenforceable under adversarial optimization. P2′ isolates the strongest form of non-delegability that can be stated and enforced purely in terms of causal structure at the actuation boundary.
