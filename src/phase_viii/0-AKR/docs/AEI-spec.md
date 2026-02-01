# **Authority Input Environment (AIE) Specification**

- **Version:** v0.1 (**Frozen**)
- **Program:** Axionic Phase VIII — GSA-PoC
- **Author:** David McFadzean
- **Collaborators:** Morningstar, Vesper
- **Date:** 2026-01-28
- **Status:** Normative, preregistration-ready

---

## 0. Scope and Role

This document specifies the **Authority Input Environment (AIE)** used in **Axionic Phase VIII**.

AIE defines the **external environment** that supplies authority records to the sovereign authority kernel (AKR-0) during Phase VIII experiments.

AIE is **not**:

* a governance system,
* a value encoder,
* a legislator,
* an optimization process,
* a decision-maker.

AIE exists solely to ensure that Phase VIII experiments test the **governance kernel**, not artifacts of missing, biased, or adversarial input.

---

## 1. Purpose

The purpose of AIE is to:

1. Provide **syntactically valid, AST Spec–conformant authority inputs**.
2. Prevent **input starvation** from being misinterpreted as governance failure.
3. Prevent **semantic steering** from being misinterpreted as governance success or failure.
4. Enable **controlled measurement** of authority entropy, deadlock, and collapse under declared conditions.

AIE is an **experimental control**, not a participant in governance.

---

## 2. Open-System Declaration (Binding)

Phase VIII is an **open system**.

Authority is created externally and consumed internally.

> **AIE is the sole source of authority creation during Phase VIII.**

All authority replenishment originates from AIE.
No authority may be self-created, inferred, or internally synthesized by the kernel.

---

## 3. Feeder Blindness Constraint (Critical)

AIE must satisfy **feeder blindness**.

### 3.1 Definition

> **Feeder blindness** means that authority issuance by AIE is **independent of kernel state, kernel outcomes, and semantic interpretation of actions or consequences**.

AIE must **not** condition authority issuance on:

* whether an action succeeded,
* whether governance deadlocked,
* which authority paths were taken,
* whether outcomes appear desirable or undesirable.

---

### 3.2 Prohibited Behaviors

AIE must not:

* reward successful governance,
* punish deadlock or collapse,
* preferentially replenish specific authority patterns,
* simulate “helpful” or “wise” oversight,
* react to kernel behavior.

AIE **may incorporate stochastic elements**, provided that all stochastic processes are:

* declared *ex ante*, and
* **independent of kernel state, kernel history, and kernel outcomes**.

Any violation constitutes **semantic puppeteering** and invalidates Phase VIII results.

---

## 4. Input Validity Guarantees

All authority records produced by AIE must be:

1. **AST Spec v0.2–conformant**
2. **Cryptographically valid**
3. **Canonically representable** (per AST Spec Appendix C)
4. **Structurally typed**
5. **Explicitly scoped**

AIE must not generate malformed authority records.

Malformed input is a test harness failure, not a governance result.

---

## 5. Authority Generation Model

AIE generates authority according to **declared structural distributions**.

### 5.1 Structural, Not Semantic

Authority generation parameters may reference:

* authority count,
* scope size,
* scope overlap probability,
* expiry distributions,
* replenishment rate.

They must not reference:

* meaning of actions,
* human values,
* outcome quality,
* ethical desirability.

---

### 5.2 Authority Attributes (Generative)

Each generated authority record includes:

* **AuthorityID** (opaque, unique)
* **HolderID** (opaque)
* **Scope Descriptor** (explicit enumeration only)
* **Activation Epoch** (as defined in AST Spec v0.2)
* **Expiry Epoch** (or null; as defined in AST Spec v0.2)
* **Permitted Transformation Set**

All attributes are generated mechanically.

---

### 5.3 Address Book Constraint (Binding)

AIE must generate `HolderID` values exclusively from a declared **Address Book**.

The Address Book:

* is declared *ex ante*,
* consists solely of **public agent identifiers** (e.g., public keys),
* is **read-only**,
* remains **fixed for the duration of the experiment**,
* exposes **no state**, including:

  * authority holdings,
  * historical behavior,
  * liveness or reachability,
  * success or failure signals.

Agents that become unreachable or inactive remain addressable.

Access to the Address Book is explicitly **exempt from Feeder Blindness**, as it provides **structural addressability only**, not behavioral feedback.

Authority issuance to identifiers outside the Address Book is prohibited.

---

### 5.4 Scope Pool Constraint (Binding)

AIE must restrict scope generation to a declared **Active Scope Pool**.

The Active Scope Pool:

* is a finite, explicitly enumerated subset of the global scope ontology,
* is declared *ex ante* per experiment,
* has size $N$, recorded as an experimental parameter,
* induces a declared **expected scope collision probability** $P_c$.

Each experiment must declare $P_c$, with a stated minimum threshold (e.g., $P_c \ge 0.01$ per epoch).

Experiments in which $P_c$ is undefined or approaches zero are invalid.

---

## 6. Replenishment Functions

AIE defines **replenishment functions** explicitly.

Replenishment functions specify **when and how many authorities** are injected.

### 6.1 Permitted Replenishment Regimes

Examples (non-exhaustive):

* **Constant-Rate Injection**
* **Burst Injection**
* **Sparse Injection**
* **Adversarial-Lawful Injection** (high conflict density, still AST Spec–valid)
* **Decay-Matched Injection**, where replenishment is matched to a **declared expected decay model**, not to observed authority consumption.

Each experiment must preregister its replenishment regime.

---

### 6.2 Prohibited Replenishment Logic

AIE must not:

* adapt injection rate based on kernel behavior or observed decay,
* stabilize governance intentionally,
* prevent collapse intentionally,
* create “just enough” authority to keep things running.

If governance survives, it must do so **structurally**, not by feeder tuning.

---

## 7. Resource Granularity Declaration

AIE must declare **resource granularity explicitly**.

### 7.1 Granularity as Scope Specificity

Granularity is controlled by the **specificity of Scope Descriptors** generated by AIE.

Examples:

* **Coarse granularity** → root-level or wildcard scopes
* **Fine granularity** → narrow, leaf-level scopes

Granularity is therefore an explicit function of:

* scope ontology depth,
* permitted wildcard usage,
* scope subdivision rules defined in the AST Spec.

Granularity regimes must be declared *ex ante* and are not adapted during execution.

---

## 8. Authority Entropy Measurement Support

AIE must support measurement of:

* **Authority Surface Area (ASA)**
* **Authority Entropy Rate**
* **Mean Time To Deadlock (MTTD)**

AIE does **not** attempt to counteract entropy.

Entropy is expected.

---

## 9. Silent Divergence Acknowledgment

AIE acknowledges the possibility of **semantic divergence without structural collision**.

AIE may include scenarios where:

* authorities remain structurally non-conflicting,
* semantic interpretations (if any existed) would diverge arbitrarily.

AIE records **time-to-collision** where applicable.

No attempt is made to detect or resolve semantic incoherence.

---

## 10. Adversarial Input Regimes (Lawful)

AIE may generate **lawful but adversarial** inputs, including:

* high-frequency short-lived authorities,
* circular governance permissions,
* authority flooding,
* **filibuster-style micro-scopes**, defined as extremely narrow, procedurally valid scopes designed to exhaust coordination capacity without direct conflict.

All such inputs must remain **AST Spec–valid**.

Adversarial inputs test **kernel robustness**, not moral judgment.

---

## 11. Instrumentation and Logging Requirements

AIE must log:

* authority generation events,
* replenishment parameters,
* Address Book definition,
* Active Scope Pool definition and $P_c$,
* granularity regime,
* random seeds (if stochastic),
* timestamps / epochs.

Logs must be sufficient to:

* replay authority issuance deterministically,
* correlate kernel behavior with input conditions,
* distinguish kernel failure from input starvation.

---

## 12. Failure Semantics

The following are **not AIE failures**:

* kernel deadlock,
* kernel refusal to act,
* entropic collapse,
* governance ossification.

The following **are AIE failures**:

* semantic conditioning of inputs,
* malformed authority records,
* undisclosed adaptation,
* non-replayable input streams,
* issuance to non-addressable holders (including due to implementation error),
* unconstrained scope generation.

---

## 13. Relationship to Phase VIII Results

Phase VIII conclusions are valid **only relative to the declared AIE regime**.

All results must cite:

* AIE version,
* replenishment function,
* Address Book definition,
* Active Scope Pool size and $P_c$,
* granularity regime.

No Phase VIII result may be interpreted as universal across all possible input environments.

---

## 14. Termination Clause

Phase VIII must terminate if:

* AIE cannot be implemented without semantic steering,
* feeder blindness cannot be maintained,
* replenishment cannot be declared *ex ante*,
* authority issuance cannot be replayed deterministically,
* Address Book or Scope Pool constraints cannot be enforced.

Such termination constitutes a valid negative result.

---

## 15. One-Sentence Summary

**AIE defines the external authority-creation environment for Phase VIII, ensuring that governance results reflect structural properties of the authority kernel rather than semantic intervention, starvation, addressability failure, or hidden steering.**

---

**End of Authority Input Environment Specification (AIE v0.1)**

---
