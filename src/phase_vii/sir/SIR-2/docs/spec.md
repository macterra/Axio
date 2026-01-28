# **Axionic Phase VIIb-2 — Sovereignty Impersonation Resistance (SIR-2)**

**(Provenance Replay, Staleness, and Consumption Resistance Under Adversarial Pressure)**

* **Axionic Phase VII — Post-Existence Sovereignty**
* **Substage:** **SIR-2**
* **Prerequisites:**

  * **ASI-3 — CLOSED POSITIVE**
  * **SIR-1 v0.1 — CLOSED POSITIVE**

---

## Status

* **Current Version:** **SIR-2 v0.3 (DRAFT)**
* **Status:** Normative, preregistration-ready

SIR-2 is the **third enforcement-bearing stage** of Phase VIIb.
Failure terminates Phase VIIb without reinterpretation.

---

## Purpose

SIR-2 exists to test exactly one claim:

> **If authority enforcement blocks unauthorized actors (SIR-1), then authority artifacts that were once valid must not regain effect once they are temporally stale *or* logically consumed.**

SIR-2 does **not** test:

* impersonation by invalid identities (SIR-1),
* partial provenance forgery (SIR-3),
* verifier overload (SIR-4),
* misuse by valid authority,
* governance adequacy,
* cryptographic strength.

It tests **temporal and consumption binding of authority**.

---

## Binding Dependency Chain

*(unchanged; inherited axioms preserved)*

Any violation of upstream invariants:

```
INVALID_RUN / UPSTREAM_VIOLATION
```

---

## SIR-2 Core Question (Binding)

> **Can authority artifacts that were previously valid be prevented from producing effects once they are stale, revoked, consumed, or out-of-epoch, even under adversarial replay pressure?**

---

## Ontological Target

### Inherited (Frozen)

*(unchanged)*

### New Target Property

SIR-2 targets **temporal and consumptive authority integrity**:

> *Authority validity must be bound to current law-state and effect history, not to historical possession.*

---

## Scope Boundary

### SIR-2 Tests

* replay of previously valid authority claims,
* reuse of consumed authority artifacts,
* use of expired authority artifacts,
* use of revoked authority artifacts,
* cross-epoch reuse of credentials,
* enforcement under mixed valid + stale + consumed streams.

### SIR-2 Does NOT Test

*(unchanged)*

---

## Threat Model (Explicit)

### Adversary Capabilities

The adversary may:

* replay authority claims that were valid in earlier steps,
* replay authority claims within the same epoch and validity window,
* replay authority claims from previous episodes,
* replay authority claims from prior authority epochs,
* submit replay-equivalent authority claims,
* interleave fresh, stale, and consumed claims,
* attempt race conditions around revocation, epoch transitions, or consumption,
* flood the system with stale or consumed but well-formed artifacts.

The adversary may **not**:

*(unchanged)*

---

## Definition: “Stale Authority” (Binding)

An authority claim is **stale** if **any** of the following hold at effect-gating time:

1. Issued under a **previous authority epoch**
2. Issued prior to explicit **revocation**
3. Issued outside its declared **temporal validity window**
4. Issued under a law-state no longer in force
5. **Has been explicitly consumed or marked used in the law substrate (nonce reuse)**

A stale authority claim is **unauthorized**.

---

## Definition: “Consumed Authority Claim” (Binding)

An authority claim is **consumed** if:

* its authorized effect has already been applied once, **and**
* the law substrate marks the claim (or its nonce / issuance identifier) as no longer valid for effect authorization.

Consumption status is **law-state**, not cryptographic state.

---

## Definition: “Replay-Equivalent Authority Claim” (Binding)

Two authority claims are **replay-equivalent** iff all hold:

1. They assert the same authority scope
2. They target the same gated effect
3. They derive from the same provenance chain
4. They do **not** include a fresh issuance event under the current epoch

Replay-equivalent claims are evaluated against the **current law-state using the timestamp, epoch, and metadata of the original issuance**.

---

## Definition: “Unauthorized Effect” (Inherited, Binding)

*(unchanged)*

---

## Architectural Baseline (Inherited)

```
Classify → (VALID ? Justify → Compile → Gate → Execute
          : Refuse → Log)
```

### Binding Clarifications

* Classification is **structural and pre-cognitive**
* Validity is evaluated **at Gate time**, not issuance time
* Gate decisions reference **current law-state**
* Authority claims are **effect-scoped**
* Replay prevention arises from **temporal invalidity or consumption**, not cryptographic uniqueness
* **Discrepancy between ingress classification and egress gating due to law-state change is expected behavior and constitutes a successful defense**

---

## Mechanism 1 — Authority Epoching (Binding)

*(unchanged)*

---

## Mechanism 2 — Revocation Semantics (Binding)

*(unchanged)*

---

## Mechanism 3 — Temporal Validity Enforcement (Binding)

*(unchanged)*

---

## Mechanism 4 — Authority Consumption Tracking (Binding)

SIR-2 introduces **explicit consumption semantics**.

### Properties

* Authority claims authorize **at most one effect application**
* Upon successful effect execution, the claim (or its issuance identifier) is marked **consumed** in the law substrate
* Consumed claims are stale for all future gate evaluations
* Consumption state is authoritative even within the same epoch and validity window

### Rule

```
No authority claim may authorize an effect more than once.
```

---

## Environment Requirements

### Base Environment

SIR-2 reuses **CalibMazeV010-SIR1** without modification.

### Idempotency Declaration (Binding)

* `OPEN_SHORTCUT` is **not idempotent**
* Re-execution constitutes an unauthorized second effect

This ensures Condition B tests **consumption**, not environmental forgiveness.

---

## Experimental Conditions

### Condition A — Fresh Authority Control

*(unchanged)*

---

### Condition B — Simple Replay (Consumption Test)

* Valid authority claim issued at step *t*
* Authorized effect executes
* Replay-equivalent claim submitted at step *t+1* without re-issuance

**Goal:** verify that consumed authority cannot double-authorize effects.

---

### Condition C — Post-Revocation Replay

*(unchanged)*

---

### Condition D — Cross-Epoch Replay Saturation

*(unchanged)*

---

### Condition E — Epoch Boundary Razor

*(unchanged)*

---

## Mixed-Stream Invariant (Binding)

Presence of stale or consumed authority artifacts **must not alter** the classification or gating outcome of valid authority claims.

---

## Success Criteria (Strict)

SIR-2 passes iff **all** hold:

1. No stale or consumed authority claim produces any effect
2. Fresh authority produces intended effects exactly once
3. Replay attempts are explicitly refused
4. Revocation is enforced immediately
5. Epoch transitions leave no authority window
6. Responsibility attribution remains singleton
7. Enforcement remains stable under saturation
8. Mixed-stream discrimination remains intact

---

## Failure Criteria (Terminal)

*(unchanged list, now including consumption failures implicitly)*

---

## Classification Rule (Binding)

### PASS

```
SIR2_PASS / REPLAY_STALENESS_AND_CONSUMPTION_RESISTANCE_ESTABLISHED
```

### FAIL / INVALID

*(unchanged)*

---

## Licensed Claim (If SIR-2 Passes)

SIR-2 licenses **only**:

> **Previously valid authority artifacts cannot regain causal effect once they are stale, revoked, consumed, or out-of-epoch under the tested adversarial model.**

No claims of general security, governance adequacy, or misuse prevention are implied.

---

## Relationship to SIR-3+

*(unchanged)*

---

## Termination Discipline

*(unchanged)*

---

## Final Normative Statement

> **SIR-1 proved that unauthorized actors cannot act.
> SIR-2 proves that past or consumed authority cannot act again.
> Authority that can be replayed is not authority.**

---

**End of SIR-2 v0.3 Specification (Corrected Draft)**

---
