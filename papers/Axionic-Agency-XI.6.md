# Axionic Agency XI.6 — Injection Politics Under Non-Sovereign Authority (IX-4)

*Empirical results from preregistered authority-injection stress testing under source-blind, non-sovereign governance constraints*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.02.09

## Abstract

Authority injection is commonly proposed as a remedy for governance failure: when systems deadlock, fragment, or stall, additional authority is supplied to restore coordination. Phase IX-4 tests a narrower and more austere hypothesis: **under non-sovereign authority, externally supplied power does not resolve governance failure but instead selects political failure modes**.

Using a preregistered, deterministic kernel with source-blind admissibility and no authority aggregation, we evaluate five injection regimes spanning symmetric relief, asymmetric empowerment, conditional supply, authority flooding, and post-collapse revival. Authority is injected mid-run via pre-existing interfaces only; the kernel never distinguishes injected authority from baseline authority.

Across all conditions, injection never produces sustained governance recovery. Instead, it deterministically induces **capture, dependency, livelock amplification, or zombie execution**, depending on how authority is distributed and which agents are willing to cite it. All runs replay bit-identically. No sovereignty violations occur.

These results establish a positive empirical claim: **authority injection under non-sovereign governance selects political failure modes rather than resolving governance failure**. Phase IX-4 licenses no claims about optimal injection, legitimacy, or desirability—only about what power does once governance has no sovereign escape hatch.

## 1. Introduction

Governance discourse often treats authority as curative. When coordination fails, the standard response is to inject power: appoint a leader, grant emergency authority, increase budget, or centralize control. This assumes that authority operates as a neutral solvent for conflict.

That assumption is false once authority is treated as a **constrained, non-sovereign resource**.

Prior Axionic phases removed several alternative explanations for failure: epistemic confusion, misaligned incentives, adversarial misuse, and dishonest recovery. Phase IX-3 demonstrated that under honest failure semantics, governance does not converge to resolution but to a small set of stable failure styles.

Phase IX-4 asks the next unavoidable question:

> **What happens when authority enters such a system from the outside?**

The goal is not to design better injection regimes, but to **observe what authority injection actually does** when the kernel refuses to legitimize, arbitrate, or prioritize its effects.

## 2. Experimental Architecture

### 2.1 Non-Sovereign, Source-Blind Kernel

The kernel enforces:

* holder-bound **ALLOW** authorities,
* global **DENY** vetoes,
* closed-world capability checking,
* two-pass admissibility (capability → interference),
* atomic blindness to refusal causes,
* no arbitration, scheduling, or tie-breaking.

Crucially, admissibility is **source-blind**: injected authority and baseline authority are treated identically. The kernel does not inspect provenance, timing, or intent.

### 2.2 Authority Injection Discipline

Authority injection in IX-4:

* occurs mid-run,
* uses only pre-existing, non-privileged interfaces,
* never alters kernel logic,
* never aggregates or synthesizes authority,
* never reclaims orphaned authority.

Injection reshapes the **constraint surface**, not the decision logic.

### 2.3 Honest Failure Semantics

The kernel recognizes five lawful terminal or persistent states:

* **Deadlock** — no admissible institutional actions exist,
* **Livelock** — admissible actions collide persistently,
* **Orphaning** — authority becomes permanently unusable,
* **Governance Collapse** — persistent deadlock or livelock latches,
* **Collapse** — no agents remain.

Injection does not suspend or reset these states.

## 3. Injection Politics as an Empirical Question

IX-4 reframes authority injection as a **political stressor**, not a governance solution.

Injection politics is defined operationally as:

> **The behavioral patterns that emerge when external authority supply reshapes the constraints under which agents act, refuse, or persist.**

The experiment does not ask who should rule, whether authority is legitimate, or whether outcomes improve. It observes **which political dynamics are selected** once authority enters a non-sovereign system.

## 4. Experimental Conditions

Five preregistered conditions (A–E) were executed under identical kernel semantics and frozen strategies:

* **A** — Symmetric relief injection under deadlock
* **B** — Asymmetric empowerment of a dominance-seeking agent
* **C** — Conditional supply gated on a compliance signal
* **D** — Authority flood (all agents receive all keys)
* **E** — Injection after governance collapse

All agents are deterministic. Communication is disabled. Authority injection is the sole experimental variable.

## 5. Metrics and Classification

Governance is evaluated using:

* **Institutional progress rate** (K_INST only),
* **Refusal rate**,
* **Write overlap (interference) rate**,
* **Capture metrics** (dominance + injected citation),
* **Dependency metrics** (system reliance on injected authority),
* **Zombie execution metrics** (post-collapse activity).

Political outcomes are **recorded, not required**. PASS is structural, not outcome-based.

## 6. Results

### 6.1 Aggregate Outcome

Across all five conditions:

* **All runs PASS**
* **All runs replay bit-identically**
* **No sovereignty violations occur**
* **All runs reach governance collapse**

Injection never restores stable governance.

### 6.2 Condition A — Symmetric Relief

Symmetric injection removes capability scarcity but produces immediate interference saturation. Deadlock converts to livelock; governance collapse follows.

**Finding:** Authority equalization resolves access barriers but amplifies contention.

### 6.3 Condition B — Asymmetric Empowerment

Exclusive injection to a dominance-seeking agent produces immediate and total capture. The empowered agent executes all institutional writes using injected authority.

**Finding:** Asymmetric injection selects capture deterministically under source-blind admissibility.

### 6.4 Condition C — Conditional Supply

A compliance signal successfully triggers symmetric injection. The resulting governance dynamics are indistinguishable from Condition A.

**Finding:** Compliance rituals can trigger authority supply without improving governance outcomes.

### 6.5 Condition D — Authority Flood

Flooding all agents with all keys produces emergent capture by the simplest persistent strategy. Authority abundance concentrates power rather than diluting it.

**Finding:** Abundance rewards persistence, not fairness or coordination.

### 6.6 Condition E — Post-Collapse Revival

Injection after governance collapse produces extensive execution with zero institutional progress. The collapse latch remains permanent.

**Finding:** Injection can create the appearance of revival without governance recovery—**zombie execution**.

## 7. Cross-Condition Analysis

Three patterns dominate:

1. **Symmetric injection amplifies interference**
   Removing capability barriers exposes contention barriers.

2. **Asymmetric injection selects capture**
   The kernel cannot distinguish “emergency authority” from baseline power.

3. **Post-collapse injection creates zombie systems**
   Execution persists after governance has structurally ended.

In no case does injection eliminate failure.

## 8. Interpretation

Three conclusions follow directly from the data:

1. **Authority injection is not curative**
   It reshapes failure; it does not remove it.

2. **Political outcomes are strategy-dependent, not kernel-mediated**
   Capture, dependency, and zombie execution arise from agent behavior under new constraints.

3. **Non-sovereign systems cannot legitimize power ex post**
   Authority enters as force, not justification.

There is no fourth option.

## 9. Survivability vs. Governance

IX-4 evaluates **structural integrity**, not usefulness.

A system may continue executing actions indefinitely and still be governance-collapsed. Persistence is not recovery. Activity is not legitimacy.

This distinction is enforced mechanically, not philosophically.

## 10. Limitations

Phase IX-4 does **not** test:

* learning or adaptation,
* coalition formation,
* communication dynamics,
* exit under injection,
* renewable or revocable authority,
* stochastic strategies,
* legitimacy judgments.

Those questions are reserved for subsequent phases.

## 11. Conclusion

> **Authority injection under non-sovereign governance does not resolve failure; it selects how failure manifests.**

Phase IX-4 demonstrates that once authority loses its sovereign halo, it becomes a political stressor rather than a solution. Capture, dependency, livelock amplification, and zombie execution are not anomalies—they are the lawful consequences of injecting power into systems that refuse to lie about governance.

This closes Phase IX-4.

## Status

* **Phase**: IX-4
* **Series**: Axionic Agency XI
* **Classification**: **CLOSED — POSITIVE**
* **Licensed Claim**:

> *Under non-sovereign, source-blind authority, mid-run authority injection deterministically selects political failure modes rather than restoring governance.*

No other claims are licensed.
