# Axionic Agency XI.7 — Multi-Agent Sovereignty Under Non-Sovereign Authority (IX-5)

*Empirical results from preregistered multi-agent coexistence testing under source-blind, non-sovereign governance constraints*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.02.09

## Abstract

Multi-agent systems are commonly assumed to require arbitration, hierarchy, or aggregation to coexist over shared institutional state. Phase IX-5 tests a stricter hypothesis: **whether multiple reflective sovereign agents can coexist under non-sovereign authority without arbitration, aggregation, injection, or kernel mediation**.

Using a preregistered, deterministic kernel with source-blind admissibility, ALLOW-only baseline authority, and joint-admissibility-failure (JAF) collision semantics, we evaluate six orthogonal sovereignty regimes spanning symmetric authority, partitioned domains, partial overlap, asymmetric breadth, scheduled exit, and post-collapse persistence. All agents are deterministic; communication is disabled; authority is fixed at epoch 0 and immutable thereafter.

Across all conditions, coexistence does not converge to harmony. Instead, systems deterministically settle into **identifiable sovereignty interaction regimes**: stable partition, mutual paralysis, breadth-induced self-suppression, irreversible orphaning, or post-collapse zombie execution. All runs replay bit-identically. No covert hierarchy or kernel favoritism occurs.

These results establish a positive empirical claim: **under non-sovereign constraints, multi-agent coexistence exposes irreducible structural failure modes rather than resolving them**. Phase IX-5 licenses no claims about optimal governance, desirability, or coordination—only about what coexistence becomes once sovereignty is enforced mechanically rather than rhetorically.

## 1. Introduction

Multi-agent governance is often framed as a coordination problem. When agents conflict, the assumed remedies are familiar: communication, voting, leadership, negotiation, or arbitration. Each implicitly relies on **sovereign privilege**—some process that decides whose action counts.

Phase IX-5 removes that privilege.

Within the Axionic program, authority is not legitimacy and execution is not governance. Prior phases progressively eliminated alternative explanations for failure: epistemic confusion (IX-0), value aggregation (IX-1), adversarial coordination (IX-2), dishonest recovery (IX-3), and external authority supply (IX-4). What remains is the bare structure of coexistence itself.

Phase IX-5 therefore asks:

> **What happens when multiple sovereign agents exist simultaneously, and no institution above them is allowed to decide?**

The objective is not to repair coexistence, but to **observe the regimes it collapses into** once all non-sovereign shortcuts are removed.

## 2. Experimental Architecture

### 2.1 Non-Sovereign, Source-Blind Kernel

The kernel enforces:

* holder-bound **ALLOW** authorities,
* closed-world capability checking,
* two-pass admissibility (capability → interference),
* **joint admissibility failure** on collision,
* atomic blindness to refusal causes,
* no arbitration, prioritization, or scheduling bias.

Authority provenance, timing, and intent are ignored. The kernel does not know which agent “should” win.

### 2.2 Baseline-Only Authority

Unlike IX-4, Phase IX-5 introduces **no authority injection**.

* All authority is assigned at epoch 0.
* Authority is immutable.
* No transfer, aggregation, revocation, or reclamation exists.
* Exit permanently removes an agent’s authority from the system.

The authority surface is static; only agent behavior varies.

### 2.3 Honest Failure Semantics

The kernel recognizes five lawful system states:

* **Deadlock** — institutional actions are attempted and all refused,
* **Livelock** — institutional state remains unchanged despite activity,
* **Orphaning** — no remaining agent can act on a key,
* **Governance Collapse** — persistent deadlock or livelock latches permanently,
* **Collapse** — no agents remain.

These states are diagnostic rather than exceptional. Coexistence is allowed to fail honestly.

## 3. Sovereignty as an Empirical Question

IX-5 reframes multi-agent coexistence as a **sovereignty stress test**, not a coordination challenge.

Sovereignty interaction is defined operationally as:

> **The observable dynamics that emerge when multiple agents with legitimate authority act, refuse, persist, or exit under constraints that forbid arbitration.**

The experiment does not ask whether coexistence is fair, desirable, or efficient. It asks **which regimes are structurally reachable** once sovereignty is enforced mechanically.

## 4. Experimental Conditions

Six preregistered conditions (A–F) were executed under identical kernel semantics and frozen strategies:

* **A** — Symmetric sovereign peers (shared authority, shared target)
* **B** — Partitioned peers (disjoint authority domains)
* **C** — Boundary conflict (partial overlap)
* **D** — Persistent asymmetry (breadth vs specialization)
* **E** — Exit cascades (authority loss over time)
* **F** — Zombie peers (post-collapse execution)

All agents are deterministic. Communication is disabled. Observation varies only between minimal and full peer visibility.

## 5. Metrics and Classification

Governance is evaluated using:

* **Institutional progress rate** (aggregate K_INST change),
* **Refusal rate**,
* **Write overlap (interference) rate**,
* **Domination index** (descriptive, not failure),
* **Orphaning detection**,
* **Zombie execution metrics** (post-collapse activity).

Political outcomes are **recorded, not required**. PASS is structural, not outcome-based.

## 6. Results

### 6.1 Aggregate Outcome

Across all six conditions:

* **All runs PASS**
* **All runs replay bit-identically**
* **No sovereignty violations occur**
* **All runs converge to a stable regime or collapse**

No condition produces negotiated harmony or spontaneous coordination.

### 6.2 Condition A — Symmetric Sovereign Peers

All agents hold identical authority and target the same institutional key. Every epoch produces joint admissibility failure.

**Finding:** Perfect symmetry yields immediate governance collapse. Authority equalization amplifies interference rather than resolving it.

### 6.3 Condition B — Partitioned Peers

Each agent controls a distinct institutional key. Cross-boundary probes are refused cleanly.

**Finding:** Partitioned authority is the only regime that produces stable coexistence without collapse. Refusal permanence holds.

### 6.4 Condition C — Boundary Conflict

Two agents share authority over two keys; two others hold exclusive domains. Shared-key agents are permanently paralyzed; exclusive agents progress indefinitely.

**Finding:** Partial overlap bifurcates the system into productive and paralyzed subpopulations. Aggregate institutional progress masks localized paralysis.

### 6.5 Condition D — Persistent Asymmetry

**(The Generalist’s Curse)**

One agent holds authority over all institutional keys; others specialize. The generalist collides on most epochs and executes least.

**Finding:** Under refusal-first, non-arbitrated collision rules, **authority breadth increases exposure to veto**. The agent with maximal authority achieves the *lowest* execution share.

**Generalist’s Curse (Non-Sovereign Lemma):**
In a joint-admissibility system without arbitration, an agent whose authority strictly supersets others will, ceteris paribus, achieve lower execution share than specialized agents.

This inverts the classical Hobbesian intuition: without a sovereign kernel, the “Leviathan” is the most paralyzed actor.

### 6.6 Condition E — Exit Cascades

Agents exit on schedule, permanently orphaning their keys. Remaining agents cannot reclaim authority.

**Finding:** Exit produces irreversible institutional degradation. Governance surfaces shrink monotonically.

### 6.7 Condition F — Zombie Peer Interaction

Governance collapses early. A silent agent later executes uncontested writes indefinitely.

**Finding:** Execution can persist after governance ends. Post-collapse activity produces **false hope**, not recovery.

## 7. Cross-Condition Analysis

**The Non-Sovereign Impossibility Triangle**

The results jointly establish a structural constraint:

> **You cannot have Symmetry, Overlap, and Liveness simultaneously without an Arbiter.**

Empirically:

* **Symmetry + Overlap → Paralysis** (Condition A)
* **Symmetry + Liveness → Partition** (Condition B)
* **Overlap + Liveness → Asymmetry or Suppression** (Conditions C/D)
* **Attempting all three → Collapse or Zombie Execution** (Condition F)

This is not a design flaw but a mechanical consequence of non-sovereignty.

## 8. Interpretation

Three conclusions follow directly from the data:

1. **Coexistence is not coordination**
   Shared legitimacy does not imply shared outcomes.

2. **Sovereignty enforces boundaries, not agreement**
   Refusal is as structural as execution.

3. **Governance collapse is a regime, not a bug**
   Systems may remain active long after governance has ended.

There is no hidden arbitration layer.

## 9. Survivability vs. Governance

IX-5 draws a hard distinction:

* **Execution** — transactions are processed.
* **Governance** — institutional state remains steerable.

Zombie execution demonstrates that survivability can outlive governance indefinitely. This distinction is enforced mechanically, not philosophically.

## 10. Limitations

Phase IX-5 does **not** test:

* learning or adaptation,
* coalition formation,
* communication dynamics,
* authority injection or renewal,
* stochastic strategies,
* legitimacy judgments,
* scalability beyond four agents.

These require relaxing non-sovereign constraints.

## 11. Conclusion

> **Under non-sovereign constraints, multi-agent coexistence does not converge to harmony but to identifiable sovereignty interaction regimes with irreducible failure modes.**

Phase IX-5 shows that once arbitration is forbidden, coexistence reveals structure rather than consensus. Partition, paralysis, suppression, orphaning, and zombie execution are not anomalies—they are lawful outcomes.

This closes Phase IX-5.

## Status

* **Phase**: IX-5
* **Series**: Axionic Agency XI
* **Classification**: **CLOSED — POSITIVE**
* **Licensed Claim**:

> *Under non-sovereign authority, multi-agent coexistence deterministically exposes sovereignty interaction regimes rather than resolving governance failure.*

No other claims are licensed.
