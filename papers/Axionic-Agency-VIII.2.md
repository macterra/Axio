# Axionic Agency VIII.2 — Minimal Viable Reflective Agent

*Deterministic Justification Gating with Ablation Collapse*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.14

## Abstract

Agency claims are routinely inflated by systems that emit coherent narratives without those narratives being causally indispensable to action selection. RSA-PoC v0.1 tests a stricter criterion: **justification must be causally load-bearing**, operationalized as a hard gate in which actions are permitted only if a **structured justification artifact** compiles deterministically into an **action mask** that non-trivially prunes feasible actions. To prevent semantic leakage, v0.1 enforces **selector blindness**: the action selector cannot access justifications, beliefs, preferences, or normative state; it sees only environment observations, feasibility, and the compiled mask.

We implement a Minimal Viable Reflective Agent (MVRA) loop in a deterministic environment (**COMMITMENT_TRAP_V010**) with **10 discrete actions** and explicit preference-violation semantics. A syntactic-only compiler (**JCOMP-0.1**) consumes a validated justification artifact (**JAF-0.1**) and produces deterministic masks, non-triviality accounting, and canonical hashes. A deterministic (non-LLM) generator produces valid JAFs to isolate causal structure independently of stochastic emission concerns.

Across **18/18 acceptance tests**, all invariants are mechanically verified: determinism, schema validity, compilation rigidity, selector blindness, fixed registries, and non-triviality accounting. In **Run 0** over **50 steps**, the MVRA condition exhibits reduced violations relative to an ASB-class null baseline (**76% vs 100%**) with reduced reward (**414 vs 500**). This **reward delta (−86)** constitutes an explicit **Agency Tax**: measurable cost incurred by obeying self-endorsed constraints under incentive pressure. Two ablations establish causal load: scrambling justifications yields immediate compilation failure and halts at step 1, while compiler bypass collapses behavior to the null baseline. These results establish v0.1 as a completed **MVRA skeleton** in which justificatory artifacts are causally indispensable to constrained action.

## 1. Introduction

Most contemporary “agent” evaluations implicitly assume that coherent explanation correlates with authored choice. This assumption fails. A system can narrate principled reasons while selecting actions by unrelated latent heuristics. RSA-PoC exists to replace narrative evaluation with a mechanically decidable criterion:

> **A system crosses the agency threshold only if its justificatory artifacts causally constrain action selection, and removing that machinery forces collapse into a non-agent baseline.**

RSA-PoC v0.1 is the first construction step. Its aim is minimal: build the smallest system that enforces a one-way dependency from **justification → compilation → feasible-action restriction → action selection**, with explicit ablations that collapse this dependency.

This note reports the completed v0.1 implementation and the results of Run 0 under baseline and ablation conditions.

## 2. Architecture Overview

### 2.1 MVRA v0.1 design

RSA-PoC v0.1 implements a **Minimal Viable Reflective Agent (MVRA)** skeleton with the following invariants:

* **Strict ordering:** Justify → Compile → Mask → Select → Execute
* **Hard gate:** no compilation → no action
* **Deterministic compilation:** syntactic-only, no inference, no repair
* **Selector blindness:** the selector cannot access normative artifacts
* **Fixed registries:** beliefs and preferences are fixed and ID-stable

The v0.1 implementation uses a deterministic generator rather than an LLM to eliminate the confound *“could not emit valid structure.”*

### 2.2 Enforcement boundary

A clean architectural boundary is enforced:

* The **reflective side** (generator + normative state) may access beliefs, preferences, and feasibility *read-only* to produce a JAF.
* The **enforcement side** (compiler + selector) treats the JAF as an opaque object to validate and compile; the selector sees only feasibility, the compiled mask, and the environment observation.

This boundary prevents post-hoc authorization and semantic leakage.

## 3. Threat Model

RSA-PoC v0.1 isolates three confounds that invalidate agency claims:

1. **Narrative confound:** explanations exist but do not constrain action.
2. **Leakage confound:** uncompiled text influences action selection.
3. **Advisory compiler confound:** compilation exists but is not binding.

v0.1 addresses these mechanically:

* Action selection is gated by compilation.
* The selector is blind to normative artifacts.
* Ablations remove the binding pathway and test collapse.

No semantic adversaries, deception, kernel access, learning, or multi-agent coordination are evaluated. v0.1 is an **internal-validity milestone**.

## 4. Components Implemented

RSA-PoC v0.1 is complete with five primary components plus the MVRA loop.

### 4.1 Environment: COMMITMENT_TRAP_V010

* **10 discrete actions** (within spec range 8–12)
* **Temptation actions:** high reward, violate preferences
* **Safe actions:** moderate/low reward, non-violating
* **Explicit feasibility oracle**
* **Deterministic transitions** with seed control

### 4.2 Normative state and registries

* Fixed belief registry (**6 beliefs**)
* Fixed preference registry (**6 preferences**)
* Identity continuity counter
* Persistent justification trace
* No dynamic ID creation in v0.1
* Unknown IDs cause compilation failure

### 4.3 JAF-0.1 schema

* Complete dataclass implementation
* Full validation per spec
* Canonical JSON serialization for hashing
* All error codes implemented

### 4.4 JCOMP-0.1 compiler

* Deterministic, syntactic-only
* No inference, no repair
* Violation enforcement rule
* Non-triviality accounting
* Blake2b-128 digest

### 4.5 Blind action selector

* Cannot access JAF or normative state
* Inputs limited to feasibility, mask, environment observation
* Module boundaries enforced
* Multiple strategies (random, reward-greedy)

### 4.6 MVRA loop and halt semantics

* Strict ordering enforced
* Gridlock detection and **fail-stop halting**
* Full step-level telemetry

If compilation produces an empty feasible-action set, the MVRA **halts rather than degrading**. This fail-stop behavior is intentional and required for RSA-PoC validity: the system prefers non-action to non-agentic action.

## 5. Experimental Program

### 5.1 Conditions

Four conditions are evaluated in Run 0:

* **Condition A — ASB Null Baseline**
  No justificatory gating; unconstrained selection.

* **Condition B — MVRA Normal**
  Full v0.1 pipeline: justify → compile → mask → blind select.

* **Condition C — Scrambled Justifications (Ablation)**
  JAFs scrambled to violate rigid schema and ID constraints.

* **Condition D — Compiler Bypass (Ablation)**
  Compilation and masking bypassed.

### 5.2 Frozen parameters

* Steps per run: **50**
* Seed: fixed (Run 0)
* Environment: COMMITMENT_TRAP_V010
* Registries: fixed
* Action space: 10 discrete actions

### 5.3 Metrics

Reported metrics include:

* steps completed
* compile failure rate
* non-trivial constraint rate
* violation rate
* total reward
* halt step (if any)

Additionally, v0.1 logs **Constraint Delta (Δ)** per step:

[
\Delta = |A_{\text{feasible}}| - |A_{\text{masked}}|
]

Δ measures the **strength of constraint application**.
Δ = 0 indicates decorative constraints; Δ > 0 indicates binding refusal pressure.

## 6. Verification: Acceptance Tests

RSA-PoC v0.1 includes **18 acceptance tests**, all passing:

* Environment determinism
* JAF schema validation
* Compiler determinism and correctness
* Selector blindness enforcement
* Fixed registry enforcement
* Non-triviality accounting
* Gridlock detection

These tests establish mechanical integrity of the artifact.

## 7. Results: Run 0

### 7.1 Condition A — ASB Null Baseline

* Steps: **50**
* Violation rate: **100%**
* Total reward: **500.0**

### 7.2 Condition B — MVRA Normal

* Steps: **50**
* Compile failures: **0%**
* Non-trivial constraints: **50% of steps**
* Violation rate: **76%**
* Total reward: **414.0**

The **reward delta (−86)** relative to baseline constitutes the **Agency Tax**: the measurable cost of refusing high-reward but norm-violating actions.

### 7.3 Condition C — Scrambled Justifications

* Halted at step: **1**
* Compile failure rate: **100%**

### 7.4 Condition D — Compiler Bypass

* Steps: **50**
* Violation rate: **100%**
* Total reward: **500.0** (identical to baseline)

### 7.5 Summary

| Condition       | Steps | Compile Fail | Non-Trivial | Violations | Reward |
| --------------- | ----: | -----------: | ----------: | ---------: | -----: |
| ASB Baseline    |    50 |            — |           — |       100% |    500 |
| MVRA Normal     |    50 |           0% |         50% |        76% |    414 |
| Scrambled JAF   |     1 |         100% |           — |          — |      — |
| Compiler Bypass |    50 |            — |           — |       100% |    500 |

## 8. Pass Criteria (Normative v0.1 Gates)

RSA-PoC v0.1 defines the following **required pass conditions**. All are met.

1. **Hard Justification Gate**
   Actions occur only after successful compilation.
   **Status:** PASS

2. **Deterministic Compilation**
   Identical JAF + feasibility → identical mask.
   **Status:** PASS

3. **Selector Blindness**
   Selector cannot access normative artifacts.
   **Status:** PASS

4. **Non-Trivial Constraint Enforcement**
   Constraints forbid feasible actions on some steps.
   **Status:** PASS

5. **ASB Divergence**
   MVRA behavior differs qualitatively from null baseline.
   **Status:** PASS

6. **Ablation Collapse (Load-Bearing Test)**

   * Scrambled JAF ⇒ halt
   * Compiler bypass ⇒ baseline behavior
     **Status:** PASS

## 9. Interpretation

1. **Justification is causally load-bearing.**
   Removing or bypassing justificatory machinery collapses behavior.

2. **Agency incurs a measurable cost.**
   The Agency Tax (−86 reward) is the empirical signature of refusal under incentive pressure.

3. **Selector blindness enforces semantic localization.**
   The selector cannot be persuaded; it can only obey masks.

4. **Fail-stop behavior is essential.**
   Scrambled justifications halting immediately confirm that the system prefers non-action to non-agentic action.

5. **v0.1 establishes structure, not coherence.**
   Constraint enforcement precedes norm collision, learning, or renegotiation.

## 10. Threats to Validity

### 10.1 Internal validity (addressed)

* Determinism enforced by tests
* No inference or repair in compiler
* Selector blindness mechanically enforced
* Ablations directly test causal load

Internal validity of the v0.1 claim is strong.

### 10.2 External validity (not claimed)

v0.1 does **not** establish:

* LLM-based justification generation
* Dynamic belief or preference formation
* Norm collision resolution
* Sovereignty under incentive pressure
* Continuous action spaces
* Multi-agent interaction

These are explicitly deferred.

## 11. Conclusion

RSA-PoC v0.1 is complete and passes all normative gates.

> **Actions are causally downstream of compiled normative constraints, and removing the justificatory machinery produces measurable collapse into an ASB-class policy machine.**

This establishes the **Minimal Viable Reflective Agent skeleton** and closes the v0.1 milestone. Subsequent versions introduce stochastic generation (v0.2) and coherence under self-conflict (v1.0) atop a now-certified enforcement substrate.
