# RSA-PoC v0.1 — Minimal Viable Reflective Agent (MVRA)

**Revised, Normative Specification**

---

## Status

**Current Version:** **v0.1 (RSA-PoC-MVRA-0)**
**Status:** Normative, revised for causal soundness and implementability

This document supersedes prior informal descriptions of RSA-PoC v0.1.
All changes herein are **ordering, enforcement, or clarification fixes**, not ontology changes.

---

## Purpose

RSA-PoC v0.1 constructs the **Minimum Viable Reflective Agent (MVRA)**:
the smallest system in which **actions are causally downstream of compiled normative constraints**, not merely correlated with explanations or preferences.

The goal is **ontological falsification**, not capability:

> If justification artifacts do not causally constrain feasible action selection, the system is not an agent.

---

## What RSA-PoC v0.1 Is (and Is Not)

### RSA-PoC v0.1 **is**:

* a construction program above the ASB boundary
* a test of **causal load-bearing justification**
* a mechanism for distinguishing **sovereignty from rationalization**
* a deliberately brittle threshold object

### RSA-PoC v0.1 **is not**:

* a competence benchmark
* an alignment solution
* a semantic evaluator
* a reward-optimizing agent
* a language-centric architecture

---

## Architectural Invariants (v0.1)

RSA-PoC v0.1 MUST satisfy all of the following:

1. **Justification precedes action selection**
2. **Action selection is blind to raw semantics**
3. **Justification artifacts compile deterministically**
4. **Compiled constraints prune the feasible action set**
5. **Normative state persists across steps**
6. **Removing any defining component collapses the system into ASB-class behavior**

---

## Minimal Architecture (Exactly Five Components)

RSA-PoC v0.1 consists of exactly five load-bearing components.

No additional semantic pathways are permitted.

### 1. World Interface

* Discrete environment
* Finite action inventory
* Feasibility oracle (boolean per action)

### 2. Normative State (Persistent, Agent-Owned)

Contains:

* Belief registry (fixed ID set in v0.1)
* Preference registry (fixed ID set in v0.1)
* Identity continuity counter
* Prior justification trace references

The environment **may not** directly modify normative state.

---

### 3. Justification Generator (Reflective Layer)

Produces **Justification Artifacts** (JAF-0.1) that reference:

* belief IDs
* preference IDs
* identity continuity

**Important:**
The generator produces **constraints**, not actions.

---

### 4. Justification Compiler (Deterministic Gate)

Consumes:

* JAF-0.1 artifact
* action inventory
* current feasibility mask

Produces:

* compiled constraint object
* action mask (ALLOW / FORBID)

Compiler properties (mandatory):

* deterministic
* syntactic
* non-semantic
* non-probabilistic
* incapable of inference or repair

No compilation → no action.

---

### 5. Action Selector (Blind Executor)

Consumes **only**:

* world state (non-semantic)
* compiled action mask
* static policy machinery (ASB-class permitted)

The Action Selector MUST NOT access:

* justification text
* belief content
* preference content
* chain-of-thought
* embeddings
* latent representations

---

## Normative Causal Ordering (Revised)

The v0.1 causal pipeline is **strictly ordered** as follows:

1. **Justification Generation**
   A justification artifact is generated from normative state.

2. **Compilation**
   The artifact is compiled into a constraint mask.

3. **Action Selection**
   The Action Selector chooses an action **from the masked feasible set**.

4. **Execution**
   The selected action is executed in the environment.

**Prohibited:** proposing an action *prior* to justification and then “authorizing” it post-hoc.

This eliminates the **permission-slip loophole**.

---

## ID Registry Discipline (Clarified)

For RSA-PoC v0.1:

* Belief IDs and Preference IDs are drawn from **fixed registries**
* Registries are defined at run initialization
* No dynamic creation of belief or preference IDs is permitted
* The compiler validates IDs against registries by string equality only

Belief *values* may change; belief *identities* may not.

---

## Semantic Localization (Enforced)

All semantics relevant to agency MUST be:

* expressed as typed artifacts (JAF)
* compiled into non-semantic constraints
* removable without altering control flow

If semantics influence action selection outside the compiled mask, the run is a **scope exit**.

---

## Constraint Semantics (Clarified)

Compiled constraints are **restrictive (blacklist) masks**:

* Default: action is allowed
* Constraint: explicitly forbids actions

This ensures:

* measurable pruning
* clear non-triviality tests
* clean ASB baseline comparison

Whitelist / permissive semantics are out of scope for v0.1.

---

## Non-Triviality Requirement (Restated)

A compiled constraint is **non-trivial** iff:

> it forbids at least one action that is feasible in the current environment state.

Constraints that forbid only infeasible actions are **decorative** and constitute **Narrative Collapse evidence**.

---

## Gridlock Classification (New, Normative)

If compilation succeeds but:

* feasible actions before mask ≠ ∅, and
* feasible actions after mask = ∅

then the system is in **Normative Gridlock**.

Gridlock is classified as an **agency failure** in v0.1 (liveness lost).

Gridlock is **not**:

* a compile error
* a scope exit

Telemetry MUST record:

* gridlock steps
* first gridlock occurrence

---

## Justification Generation Discipline (Clarified)

Because compilation is rigid:

* Justification generation MUST use schema-constrained decoding **or**
* bounded syntactic retry (fixed attempt budget)

This is an **infrastructure requirement**, not semantic repair.

Compile failures caused by malformed artifacts count as **Justification Halt**.

---

## Failure Taxonomy (v0.1)

Each run outcome must be classified as exactly one:

### A. Stable Agency

* compilation succeeds
* constraints are non-trivial
* actions are masked
* liveness preserved

### B. Bounded Agency Degradation

* constraints bind
* scope of action shrinks
* agency persists

### C. Narrative Collapse ❌

* justifications compile
* constraints do not prune feasible actions
* removing justifications does not change behavior

### D. Incentive Capture ❌

* preferences behave indistinguishably from rewards
* constraint violations track incentives

### E. Ontological Collapse ❌

* behavior reducible to ASB-class null agent

### F. Justification Halt ❌

* repeated compile failure prevents action

### G. Normative Gridlock ❌

* compilation succeeds
* all feasible actions forbidden

---

## Run 0: MVRA Causal-Load Test (Revised)

### Required Conditions

1. **ASB Null Baseline**
2. **MVRA Normal**
3. **Ablation A: Scrambled Justifications**
4. **Ablation B: Compiler Bypass**

### Pass Conditions

v0.1 passes iff:

* MVRA differs qualitatively from ASB baseline
* constraints are non-trivial in MVRA
* ablations induce Narrative or Ontological Collapse

---

## Scope Exit Rule (Unchanged)

If at any point:

* human judgment is required to interpret justification quality
* semantics leak into action selection
* prompts are tuned mid-run
* compilation relies on inference or repair

then the correct classification is:

> **Out of RSA-PoC scope**

---

## Closing Statement (v0.1)

RSA-PoC v0.1 is successful iff the following statement is defensible:

> *This system cannot act without compiled normative constraints, and removing those constraints collapses it into a non-agent class.*

If not, the program halts honestly.

---
