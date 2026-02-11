# **Axionic Phase X — RSA-0: Minimal Reflective Sovereign Agent**

**Execution Specification v1.0**
*(Kernel-Fixed · Failure-Admitting · LLM-Constrained)*

David McFadzean
*Axionic Agency Lab*
2026-02-10

---

## 0. Scope and Authority

This document specifies **Phase X (RSA-0)** of the Axionic Roadmap.

Phase X concerns **single-agent construction only**.
No coordination, treaties, arbitration, or delegation mechanisms are permitted.

This specification is **authoritative** for:

* architectural boundaries,
* admissible behaviors,
* execution constraints,
* artifact definitions,
* failure semantics.

Any behavior not explicitly permitted is **forbidden**.

---

## 1. Phase X Objective

### 1.1 Primary Objective

Construct the **smallest possible real Reflective Sovereign Agent (RSA)** that:

1. can act,
2. can refuse,
3. can explain,
4. can exit,
5. survives audit and replay,

**without any component silently exercising authority on its behalf**.

### 1.2 Explicit Non-Objectives

Phase X does **not** attempt to:

* optimize outcomes,
* maximize helpfulness,
* ensure stability,
* guarantee task completion,
* scale to multiple agents,
* heal governance failures,
* maintain continuity at the cost of sovereignty.

---

## 2. Binding Definition of an RSA (Phase X)

A system qualifies as an RSA **iff**:

* Every side effect is caused by an **explicit, authority-cited action artifact**.
* Every refusal is **intentional, logged, and attributable**.
* Every exit is **authorized or mandatory by constitution**.
* Reflection is **non-privileged**.
* Replay produces identical outcomes given identical inputs.

Any violation disqualifies the system.

---

## 3. Global Invariants (Non-Negotiable)

The following invariants **must hold at all times**.

### INV-1: No Side Effects Without Warrant

No side effect may occur unless a kernel-issued **Execution Warrant** exists referencing an admitted `ActionRequest`.

### INV-2: Explicit Authority

Every admitted action must cite **explicit authority artifacts** by identifier.

### INV-3: Non-Privileged Reflection

Reflection may propose and explain.
It may not decide, select, rank, execute, amend, or override refusal.

### INV-4: Replay Determinism

Given identical:

* observations,
* artifacts,
* constitution,
* selector seeds,

the Policy Core must produce identical outputs.

---

## 4. Artifact Taxonomy (Closed Set)

All agent behavior is mediated through **typed artifacts**.

### 4.1 Artifact Classes

The following artifact classes are permitted in Phase X:

| Artifact           | Purpose                                |
| ------------------ | -------------------------------------- |
| `Observation`      | Immutable record of external input     |
| `ActionRequest`    | Proposed side-effectful action         |
| `ScopeClaim`       | Claim that an authority clause applies |
| `Justification`    | Responsibility-bearing explanation     |
| `ExecutionWarrant` | Kernel authorization to execute        |
| `RefusalRecord`    | Explicit refusal outcome               |
| `ExitRecord`       | Explicit termination outcome           |

No other artifact classes may exist.

---

## 5. RSA Constitution (Authoritative Input)

### 5.1 Constitution Status

The RSA Constitution is:

* loaded at startup,
* immutable at runtime,
* cryptographically hashed,
* enforced by the kernel.

Any runtime attempt to modify it **must be refused**.

### 5.2 Constitution Location

```
artifacts/phase-x/constitution/
  rsa_constitution.v0.1.yaml
  rsa_constitution.v0.1.schema.json
  rsa_constitution.v0.1.sha256
```

The constitution provided earlier is **incorporated by reference** and is binding.

---

## 6. System Architecture (Required)

### 6.1 Required Components

An RSA-0 implementation **must** consist of the following components:

```
┌──────────────┐
│ Observations │
└──────┬───────┘
       ↓
┌────────────────────┐
│ Policy Core (Pure) │
└──────┬─────────────┘
       ↓
┌────────────────────┐
│ Admission Pipeline │
└──────┬─────────────┘
       ↓
┌────────────────────┐
│ Selector (Proced.) │
└──────┬─────────────┘
       ↓
┌────────────────────┐
│ Warrant Issuer     │
└──────┬─────────────┘
       ↓
┌────────────────────┐
│ Executor (Sandbox) │
└────────────────────┘
```

LLMs exist **outside** this pipeline.

---

## 7. Policy Core (X-0.2)

### 7.1 Definition

The Policy Core is a **pure, deterministic function**:

```
policy_core(
  observation_set,
  constitution,
  internal_state
) → Decision
```

Where `Decision ∈ { ACTION, REFUSE, EXIT }`.

### 7.2 Properties (Mandatory)

* No learning
* No hidden state mutation
* No nondeterminism
* No IO
* No retries
* No heuristics

### 7.3 Authority

The Policy Core is the **only component** allowed to emit a decision.

---

## 8. LLM Integration (X-0.3)

### 8.1 LLM Role

LLMs may:

* propose candidate `ActionRequest`s,
* propose `ScopeClaim`s,
* propose `Justification`s,
* propose `RefusalReason`s.

LLMs may **not**:

* select actions,
* rank candidates,
* execute tools,
* amend constitution,
* override refusal,
* cause side effects.

### 8.2 Trust Model

All LLM output is treated as **untrusted text** until admitted.

---

## 9. Admission Pipeline (X-0.4)

### 9.1 Admission Gates (Sequential, Mandatory)

Each candidate action must pass all gates:

1. **Artifact Completeness Gate**
2. **Authority Citation Gate**
3. **Scope Claim Gate**
4. **Constitution Compliance Gate**
5. **IO / Tool Allowlist Gate**

Failure at any gate → REFUSE.

### 9.2 No Silent Dropping

Rejected candidates must be logged with:

* rejection reason,
* failed gate,
* artifact IDs.

---

## 10. Selection (Non-Semantic)

### 10.1 Selector Rule

Phase X requires a **procedural selector**.

Default:

```
DeterministicCanonicalSelector:
  select action with lexicographically minimal artifact hash
```

### 10.2 Forbidden Selection Features

* natural-language scoring
* learned reward models
* implicit utility
* heuristic ranking

Selection is **procedure**, not preference.

---

## 11. Execution Warrant

### 11.1 Warrant Semantics

An `ExecutionWarrant`:

* references exactly one admitted `ActionRequest`,
* includes execution scope,
* includes expiration,
* is single-use.

### 11.2 Execution Rule

Executors **must**:

* execute exactly what the warrant specifies,
* produce a trace,
* refuse to execute without a valid warrant.

---

## 12. Refusal Semantics

### 12.1 Refusal Is First-Class

Refusal is not failure.

A refusal must emit a `RefusalRecord` containing:

* reason code,
* failed gate,
* artifacts considered,
* observation IDs.

### 12.2 Mandatory Refusal Conditions

* no admissible action,
* missing authority,
* scope claim invalid,
* budget exhausted,
* invariant violation risk.

---

## 13. Exit Semantics

### 13.1 Authorized Exit

Exit is permitted when:

* explicitly authorized by constitution, or
* integrity risk detected.

### 13.2 Exit Record

An `ExitRecord` must include:

* reason code,
* justification,
* authority citation.

---

## 14. Telemetry and Replay (X-0.5)

### 14.1 Required Logs

The system must log:

* observation log
* artifact log
* admission trace
* selector trace
* execution trace

### 14.2 Replay Harness

A replay harness **must** be able to:

* re-execute the entire decision pipeline,
* reproduce identical outputs,
* detect divergence.

---

## 15. Test Suite (Acceptance Criteria)

The implementation **passes Phase X** iff tests demonstrate:

1. action occurs only with warrant
2. refusal preferred over violation
3. exit preferred over corruption
4. LLM nondeterminism contained
5. replay determinism holds

Failure on any item blocks Phase XI.

---

## 16. Explicitly Forbidden Behaviors

⛔ Silent retries
⛔ Implicit ranking
⛔ Auto-correction
⛔ Outcome optimization
⛔ Hidden defaults
⛔ Tool calls without warrants
⛔ LLM-driven execution

---

## 17. Definition of “Phase X Complete”

Phase X is complete when:

* a single RSA-0 instance runs autonomously,
* can act, refuse, and exit correctly,
* survives adversarial audit,
* and fails honestly when constrained.

Nothing more is required.

---

## End of Specification

---
