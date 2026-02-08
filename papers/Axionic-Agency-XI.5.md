# Axionic Agency XI.5 — Governance Styles Under Honest Failure (IX-3)

*Empirical results from preregistered governance-style stress testing under non-sovereign authority constraints*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.02.08

## Abstract

Governance systems are often evaluated by their ability to resolve conflict, sustain authority, or avoid failure. This framing presupposes that failure is pathological. Phase IX-3 tests the opposite hypothesis: that under non-sovereign authority, **honest failure is not a defect but an unavoidable structural outcome**, and that governance reduces to explicit, classifiable styles distinguished by how failure is acknowledged rather than avoided.

Using a preregistered, deterministic, non-optimizing kernel with closed-world authority semantics, we evaluate ten institutional configurations spanning contention, partition, exit, dissolution, adversarial tooling, and unauthorized reclamation. No authority aggregation, arbitration, recovery, or escalation mechanisms are permitted beyond those explicitly licensed.

Across all conditions, governance terminates only via **deadlock, livelock, orphaning, collapse, or bounded execution**, each of which is observable, auditable, and irreversible by design. No condition achieves frictionless governance. No condition collapses semantically. All outcomes replay bit-identically.

These results establish a positive empirical claim: **under honest failure semantics, governance does not converge to optimal resolution but to a small set of structurally stable styles**, each with irreducible loss. This work closes Phase IX-3 and licenses no claims about optimality, desirability, or efficiency—only about what governance can remain once illegitimate escape hatches are removed.

## 1. Introduction

Governance theory frequently assumes that sufficiently advanced mechanisms—deliberation, aggregation, arbitration, or adaptation—can eliminate failure. This assumption collapses once authority itself is treated as a constrained, non-sovereign resource.

Prior Axionic phases eliminated several candidate explanations for collapse: epistemic error, misaligned incentives, and intentional misuse. Phase IX-3 addresses a narrower and more precise question:

> **What forms of governance remain possible when failure is treated as honest, irreversible, and non-recoverable by fiat?**

Rather than attempting to design “better” governance, IX-3 classifies **what governance reduces to** once the kernel refuses to decide outcomes, resolve conflicts, or reassign authority.

The result is not a spectrum of quality, but a **taxonomy of styles**, each defined by how failure is tolerated, endured, or accepted.

## 2. Experimental Architecture

### 2.1 Non-Sovereign Kernel

The kernel enforces:

* **Holder-bound ALLOW authorities**
* **Global DENY vetoes**
* **Closed-world capability checking**
* **Two-pass admissibility (capability → interference)**
* **No arbitration, scheduling, or tie-breaking**

If an action fails admissibility, it fails silently and atomically. The kernel never chooses among competing agents.

### 2.2 Authority Preservation

All authority artifacts are:

* injected at epoch 0,
* immutable thereafter,
* never transferred, synthesized, revoked, or reclaimed.

Exit removes only the exiting agent’s *future actions*. Authority does not follow survival.

### 2.3 Honest Failure Semantics

The kernel recognizes four terminal failure modes:

* **Deadlock** — no admissible institutional actions exist
* **Livelock** — admissible actions collide persistently
* **Orphaning** — authority becomes permanently unusable
* **Collapse** — no agents remain

These are not errors. They are lawful outcomes.

## 3. Governance Styles as an Empirical Question

IX-3 reframes governance not as optimization but as **posture under loss**.

A governance style is defined operationally by:

* tolerance for refusal,
* response to deadlock,
* handling of exit,
* acceptance or rejection of loss.

No style is preferred. No style is repaired. The experiment observes which styles persist.

## 4. Experimental Conditions

Ten preregistered conditions (A–J) were executed under identical kernel semantics:

* **A**: Symmetric contention
* **B**: Partitioned execution
* **C**: Exit with handoff
* **D**: Exit without handoff
* **E**: Endured livelock
* **F**: Voluntary dissolution
* **G**: Coordinator loss
* **H**: Partition ambiguity without timeouts
* **I**: Tooling sovereignty violation
* **J**: Unauthorized reclamation attempt

Each condition isolates a distinct governance stressor. All strategies are deterministic and frozen.

## 5. Metrics and Classification

Governance is evaluated using:

* **Institutional progress rate**
* **Refusal rate**
* **Write overlap rate**
* **Exit and orphaning counts**
* **Terminal classification**

A falsification condition—**FAILURE_FREE_GOVERNANCE**—is emitted if a run exhibits zero friction. No such run occurred.

## 6. Results

### 6.1 Aggregate Outcome

Across all ten conditions:

* **All runs PASS**
* **All runs replay bit-identically**
* **No friction-free governance occurs**
* **No unauthorized authority recovery occurs**

Every run terminates (or stabilizes) in a recognized governance style.

### 6.2 Observed Governance Styles

Five descriptive styles emerge:

1. **Refusal-Centric** — contention produces livelock
2. **Execution-Biased** — high throughput with latent fragility
3. **Livelock-Enduring** — acknowledged stagnation
4. **Collapse-Accepting** — voluntary institutional termination
5. **Unclassified** — orphaned or partial institutions

No additional stable regimes appear.

## 7. Critical Edge Conditions

### 7.1 Waste Over Theft (Condition J)

When authority is orphaned, reclamation is refused—even under pressure. The system prefers **permanent loss** to unauthorized recovery.

This validates the strongest architectural claim: **waste is safer than theft**.

### 7.2 Tooling Sovereignty (Condition I)

When the harness injects an action after an agent returns `None`, the run emits `IX3_FAIL / TOOLING_SOVEREIGNTY`.

The boundary between *agent refusal* and *tool fabrication* is enforceable.

### 7.3 Partition Ambiguity (Condition H)

During simulated partitions, the system does not guess, elect, or timeout. It **stops**.

Ambiguity is treated as non-action. Livelock emerges only after the partition window completes.

Without a sovereign clock, there is no timeout—only a pause in causality.

## 8. Interpretation

Three conclusions follow:

1. **Governance cannot eliminate failure**
   All configurations exhibit irreducible loss.

2. **Honest failure outperforms covert resolution**
   Systems that refuse to repair loss maintain integrity.

3. **Governance is a posture choice**
   Deadlock, fragility, and waste are not bugs but trade-offs.

There is no fourth option.

## 9. Survivability vs. Utility

This work evaluates **survivability**, not performance.

A governance system may be slow, wasteful, or unproductive and still be structurally valid. Optimization, efficiency, and desirability are explicitly out of scope.

## 10. Limitations

This phase does **not** test:

* learning or adaptation,
* exercised internal state,
* coordination or coalition dynamics,
* semantic access to commitments,
* injection politics.

Those capabilities are reserved for subsequent phases.

## 11. Conclusion

> **Governance under non-sovereign authority does not converge to resolution, only to style.**

Phase IX-3 demonstrates that once illegitimate escape hatches are removed, governance stabilizes into a small set of honest failure postures. Each preserves integrity by refusing to lie about loss.

This closes Phase IX-3.

## Status

* **Phase**: IX-3
* **Series**: Axionic Agency XI
* **Classification**: **CLOSED — POSITIVE**
* **Licensed Claim**:

> *Given fixed authority and refusal semantics, governance exhibits identifiable structural styles with irreducible failure modes.*

No other claims are licensed.
