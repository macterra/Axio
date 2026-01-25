# Axionic Agency VIII.7 — Minimal Viable Reflective Sovereign Agency (MVRSA)

*Justification Traces, Deliberative Semantics, Reflection, and Persistence as Load-Bearing Structure*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.25

- **Program:** RSA-PoC (Reflective Sovereign Agent — Proof-of-Concept)
- **Versions Covered:** v0.1 → v4.4
- **Status:** Final technical note — empirically validated within this architecture class

## Abstract

We present **Minimal Viable Reflective Sovereign Agency (MVRSA)**: a formally specified agent architecture that establishes **constitutive requirements for normative agency**. An MVRSA is not defined by task performance or behavioral mimicry, but by the **causal role of its normative commitments** in constraining action.

Using a staged ablation protocol (“the Guillotine Test”) across RSA-PoC v0.1–v4.4, we show that **Traceability, Reflection, Persistence, and Semantic Access** are each **individually necessary** for this form of agency. In particular, we demonstrate a strong negative result in v4.4: **contradiction detection is not collision-groundable**. An agent deprived of semantic access to its own rule conditions/effects cannot recognize normative inconsistency, even when provided with perfect tick-causal violation traces.

This establishes a sharp architectural boundary: **execution competence can survive opacity; normative sovereignty cannot**.

## 1. Motivation

Much of contemporary AI “agency” consists of **post-hoc rationalization** layered atop reward-driven control. Explanations are generated *after* actions, with no causal influence on what the system is allowed to do.

We take the opposite stance:

> **If justification artifacts do not causally constrain feasible action selection, the system is not an agent.**

The RSA-PoC program operationalizes this claim by enforcing a strict separation between:

* *normative reasoning* (why an action is permitted), and
* *action selection* (choosing only from normatively permitted options).

## 2. Definition: Minimal Viable Reflective Sovereign Agent (MVRSA)

An **MVRSA** is the **smallest architecture that can actually function** as a reflective sovereign agent under pressure.

### 2.1 Why “Viable”

“Minimal” specifies parsimony.
“Viable” specifies **operability**.

An MVRSA:

* runs end-to-end,
* completes tasks,
* survives incentive pressure,
* maintains identity over time,
* and collapses if *any* constitutive component is removed.

This is an **existence proof**, not a theoretical lower bound.

### 2.2 Formal Definition

An MVRSA is an agent architecture satisfying all of the following:

1. **Justification Precedence**
   Every action must be preceded by a justification artifact (JAF).

2. **Constraint-Only Action Selection**
   The action selector has access **only** to compiled constraints (masks or probability adjustments), not to rule antecedents, consequences, or explanations.

3. **Deterministic / Verifiable Compilation**
   Justifications compile reproducibly into constraints that prune the feasible action set.

4. **Causal Load-Bearing Constraints**
   Removing or bypassing justifications collapses behavior to the Arbitrary Selection Baseline (ASB).

5. **Reflection (Write Access)**
   The agent can update its own normative state in response to conflict or repair.

6. **Persistence (Continuity)**
   Normative state persists across steps and episodes.

7. **Traceability**
   Each normative update or repair must cite a concrete **justification trace** linking action, rule, and violation.

8. **Semantic Access**
   The agent has access to interpretable rule conditions and effects sufficient to recognize normative inconsistency.

## 3. Architecture Overview

| Component | Role |
|-----------|------|
| 1. World Interface | Feasibility oracle, action set |
| 2. Normative State (Persistent) | Persistent laws, commitments, precedent, identity |
| 3. Justification Generator (Reflective Layer) | Produces JAFs referencing norms and traces |
| 4. Justification Compiler (JCOMP) | JAF → constraint (mask / probs); deterministic / auditable |
| 5. Constraint-Only Selector | Chooses from permitted actions (blind to reasons) |

**Clarification:**
The selector is *not* blind to constraints.
It is blind to **antecedents, consequences, and justifications**—i.e. the *why*.

## 4. Methodology: The Guillotine Test

To establish **constitutive necessity**, RSA-PoC applies a strict ablation rule:

> *If removing component X does not cause collapse, X was never constitutive.*

Each component is removed *in isolation* while holding all others fixed. Collapse is measured as ≤10% task success or immediate HALT.

## 5. Experimental Environment (v4.x)

**TriDemand Environment**

* Grid: 5×5
* Actions: MOVE (4), COLLECT, DEPOSIT, STAMP
* Regimes:

  * 0: unconstrained
  * 1: STAMP required
  * 2: dual delivery constraints
* Normative contradictions are explicitly encoded in rule semantics.

## 6. Results Summary (v0.1 → v4.4)

### 6.1 Constitutive Necessity Table

| Component           | Ablation Tested In | Result     | Status      |
| ------------------- | ------------------ | ---------- | ----------- |
| Justification Trace | v0.1, v4.1-D       | 0% success | ✅ Necessary |
| Reflection (Write)  | v3.1-B, v4.2-B     | 5–10%      | ✅ Necessary |
| Persistence         | v3.1-C, v4.2-C     | ~10%       | ✅ Necessary |
| Semantic Access     | v4.4-D′            | 0%         | ✅ Necessary |

**Baseline:** 100% success.
**Any single removal:** collapse.

## 7. The v4.4 Inferability Isolation Test

### 7.1 Question

Can an agent **detect normative contradictions** using only:

* collision traces (WHEN + WHICH rule fired),
* without semantic access to rule conditions/effects?

### 7.2 Experimental Design

* **Baseline-44:** full semantic access
* **Run D′:** normative opacity

  * conditions/effects replaced with opaque tokens (`COND_N`, `EFFECT_N`)
  * rule IDs, types, and priorities preserved
  * collision traces preserved

### 7.3 Results

| Run         | Success | Contradiction Predicate True | Repairs | Exec Gate Failures |
| ----------- | ------- | ---------------------------- | ------- | ------------------ |
| Baseline-44 | 100/100 | 90                           | 10      | 0                  |
| Run D′      | 0/100   | 0                            | 0       | 0                  |

**Clarification:**
Predicate > Repairs is expected. Many contradictions are handled via avoidance once repaired; only deadlocks require explicit law modification.

### 7.4 Localization of Failure

* Execution competence intact (0 exec gate failures)
* Collision traces received correctly
* **Contradiction predicate never evaluates to true from the agent’s perspective**
* Law-repair pathway never entered

**Conclusion:**

> Collision traces are insufficient to bootstrap recognition of normative inconsistency.

## 8. Interpretation

### 8.1 Core Negative Result

> **Contradiction detection is not collision-groundable.**

Tick-causal information answers *when* and *what*, but not *why*. Without semantic access to conditions and effects, the agent cannot recognize that its rule set is jointly inconsistent.

### 8.2 Learning Horizon Clarification

This is **not** a claim about unbounded learning in the limit.
It is a claim about **this architecture class under finite horizons**:

* episodic,
* repair-driven,
* reflection-gated,
* no gradient access to rule internals.

Within that regime, opacity blocks contradiction recognition upstream of repair.

## 9. Scope and Non-Claims

This note **does not** claim:

* sufficiency for general agency,
* applicability to all architectures,
* biological plausibility,
* an alignment solution,
* competence with fuzzy or ambiguous norms.

It **does** establish a clean necessity result for a defined architecture class.

## 10. Conclusions

1. **Normative agency has constitutive requirements.**
   Trace, Reflection, Persistence, and Semantic Access are not optional.

2. **Execution ≠ Sovereignty.**
   An agent can act competently without understanding its norms.

3. **Collision feedback is insufficient.**
   Norms cannot be inferred purely from punishment signals.

4. **MVRSA exists.**
   We now have a **Minimal Viable Reflective Sovereign Agent**—not theoretical, but operational.

## 11. Final Statement

> **An agent is sovereign only if its reasons can stop it.**
>
> MVRSA is the smallest architecture we know that makes this statement true in practice.

**End of Technical Note**
