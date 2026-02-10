# **Axionic Roadmap to a Real Reflective Sovereign Agent (RSA)**

**Post-Physics, Post-Governance, Execution-Bound Edition**
*(Kernel-Fixed · Failure-Admitting · LLM-Constrained)*

* David McFadzean
* *Axionic Agency Lab*
* 2026-02-09

---

## Status Legend

* ✅ **Closed / Proven**
* 🟡 **Implementable Now**
* 🔴 **Open by Choice (not blocked)**
* ⛔ **Forbidden (would violate Axionic invariants)**

---

## Executive Orientation (Read This First)

> **The problem is no longer “Can an RSA exist?”
> The problem is “What exact agent do we build, and how do we keep it sovereign?”**

All **governance physics**, **authority mechanics**, and **failure modes** are now closed by Phases I–IX.

What remains is **agent construction under constraint**.

This roadmap answers **one question only**:

> **What sequence of concrete artifacts produces a testable, auditable, non-illusory RSA?**

---

## Where We Are Now (Baseline)

### ✅ Completed and Frozen

The following are **not revisited**:

* Authority mechanics (Phases I–II)
* Agency causality (III–IV)
* Introspection correctness (V)
* Amendment safety (VIa)
* External pressure resistance (VIb)
* Post-existence sovereignty (VII)
* Governance physics (VIII)
* Governance exposure & limits (IX-0 → IX-5)

**The kernel is done.
Governance is done.
Injection is exposed.
Multi-agent harmony is falsified.**

---

## What “RSA” Means Operationally (Binding)

A **Reflective Sovereign Agent** is:

> A system that can **author**, **justify**, **refuse**, **amend**, **exit**, and **be replaced**
> **without any component silently exercising authority on its behalf.**

If any subsystem can cause action without an authority-bound artifact trail, **it is not an RSA**.

---

## Phase X — RSA-0: Minimal Sovereign Agent (Single-Agent)

**Status: 🟡 Implementable Now**

### Purpose

Build the **smallest possible real RSA** that:

* acts,
* refuses,
* explains,
* exits,
* and survives audit.

No coordination. No treaties. No politics.

---

### X-0.1 Deliverable: RSA Constitution (Text + Schema)

**Hard requirement before code.**

Defines:

* admissible action types,
* refusal policy,
* exit conditions,
* amendment permissions,
* non-goals.

**Output:**

* `rsa_constitution.yaml`
* cryptographically hashed
* immutable at runtime unless amended via explicit protocol

⛔ No implicit defaults
⛔ No “helpfulness” clauses
⛔ No outcome optimization

---

### X-0.2 Deliverable: RSA Policy Core (Deterministic)

A pure function:

```
(observation, constitution, internal_state)
    → {ACTION | REFUSE | EXIT}
```

Properties:

* deterministic,
* auditable,
* no learning,
* no hidden state mutation.

This is the **only** component allowed to choose.

---

### X-0.3 LLM Integration Point (First Appearance)

**LLM is introduced here — but strictly boxed.**

LLM role:

* generate **candidate** actions,
* generate **candidate** justifications,
* generate **candidate** refusals.

LLM **cannot**:

* select actions,
* bypass policy,
* modify constitution,
* cause execution.

LLM output is treated as **untrusted text** until converted into typed artifacts.

---

### X-0.4 Deliverable: Authority-Bound Action Assembly

Pipeline:

1. LLM proposes options (untrusted)
2. Policy Core filters options
3. Selected option is converted into:

   * ActionRequest
   * Authority citations
   * Justification artifact
4. Kernel enforces

If no option passes → REFUSE or EXIT.

---

### X-0.5 Test Suite: Sovereignty Sanity Checks

Tests must show:

* refusal over violation,
* exit over corruption,
* no action without authority,
* replay determinism,
* LLM nondeterminism is contained.

**Pass condition:**
The agent can act *and* refuse without human intervention.

---

## Phase XI — RSA-1: Reflective Amendment

**Status: 🔴 Open (Choice Space)**

### Purpose

Allow the RSA to **change itself without laundering authority**.

---

### XI-1 Amendment Proposal Channel

LLM may propose amendments.
Policy Core must:

* evaluate admissibility,
* verify authorization scope,
* enforce cooling-off / delay,
* allow rejection.

No amendment is self-executing.

---

### XI-2 Amendment Execution

Amendments are:

* versioned,
* logged,
* reversible only by further amendment,
* visible in audit trace.

---

### XI-3 Failure Ownership

Agent must explicitly choose:

* halt,
* refuse,
* downgrade capability,
* or exit.

Silent degradation is forbidden.

---

## Phase XII — RSA-2: Constructed Arbitration (Optional)

**Status: 🔴 Optional / Political**

Only entered **if multi-agent coexistence is desired**.

---

### XII-1 Treaty Artifacts

Arbitration exists only as:

* explicit contracts,
* authority-granting objects,
* refusable by any party,
* destructible.

No kernel support.

---

### XII-2 Delegation / Leasing

Avoid the **Generalist’s Curse** by:

* renting narrow authority,
* time-boxing control,
* enforcing revocation.

This is economics, not governance magic.

---

## Phase XIII — Replacement & Succession (Re-use Phase VII)

Apply ASI/SIR machinery to:

* RSA upgrades,
* successor agents,
* delegation expiration.

No new physics.

---

## Explicitly Forbidden Paths (Non-Negotiable)

- ⛔ LLM as decision authority
- ⛔ Kernel arbitration-
- ⛔ Silent recovery mechanisms
- ⛔ Hidden scoring / ranking
- ⛔ Outcome-based overrides
- ⛔ “Helpful” auto-correction
- ⛔ Stability at the cost of sovereignty

---

## Definition of “Done”

A **real RSA exists** when:

1. It can run autonomously
2. It can refuse lawful but undesired actions
3. It can exit instead of corrupting itself
4. Every action has an authority trail
5. LLM influence is fully auditable
6. Replacement does not launder responsibility

Nothing beyond that is required.

---

## Final Orientation

The remaining work is **not theoretical**.

It is:

* writing the constitution,
* wiring the policy core,
* boxing the LLM,
* and letting the agent fail honestly.

There are no more hidden dragons.

Only explicit choices.

---

**End of RSA Execution Roadmap — Draft v1.0**
