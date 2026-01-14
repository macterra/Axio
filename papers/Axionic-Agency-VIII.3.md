# Axionic Agency VIII.3 — Coherence Under Self-Conflict

*Norm Collision and Audit-Grade Introspection in Reflective Sovereign Agents*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.14

## Abstract

RSA-PoC v0.1 established that justificatory artifacts can be made **causally load-bearing**: actions occur only downstream of compiled normative constraints, and removing that machinery causes collapse into an ASB-class policy machine. This note advances the program to the next ontological question: **can an agent resolve internal self-conflict coherently, and can it be held audit-grade accountable for predicting the consequences of its own reasons?**

We report results from **RSA-PoC v1.0–v1.1**, which introduce (i) **norm collision** via mutually inconsistent self-endorsed commitments and forced violation scenarios, and (ii) **audit-grade introspection**, requiring justification artifacts to predict—exactly and mechanically—the constraints and outcomes they induce. v1.0 implements conflict attribution, authorization, necessity, and anti-oscillation rules over a deterministic **Action-Preference Consequence Map (APCM)**. v1.1 extends this with predictive fields and audit rules (A/B/C/C′) that render introspection falsifiable.

Across preregistered Run 0 executions and ablations, v1.0 demonstrates **coherent self-conflict resolution above the ASB boundary**: MVRA behavior diverges from ASB baselines, scrambled conflict attribution halts immediately, and compilation bypass collapses behavior to ASB-class selection. v1.1 shows that introspection can be enforced mechanically: incorrect predictions trigger immediate halts, while correct predictions pass without human interpretation. Deterministic baselines validate the audit harness; subsequent LLM runs demonstrate that compliance is difficult but achievable under strict discipline.

These results establish a negative sufficiency claim: **self-conflict resolution and introspective accountability can be realized as mechanical properties of an agent architecture**, independent of semantics or optimization. This note closes the v1.x ontological milestone and sets the stage for v2.0, where sovereignty under external incentive pressure is tested.

## 1. Introduction

The Axionic Agency program treats *agency* as a causal ontology rather than a behavioral aesthetic. v0.1 demonstrated that reasons can be made causally indispensable: actions only occur if justificatory artifacts compile into binding constraints. That result eliminates a large class of narrative or post-hoc agency claims.

The next question is deeper:

> **What happens when an agent’s own commitments conflict?**

Any architecture that collapses under such conditions, or that resolves conflict arbitrarily or opportunistically, does not warrant intentional vocabulary.

RSA-PoC v1.x therefore targets **coherence under self-conflict**, followed by **introspective accountability**. The aim is not moral correctness but structural integrity: when violating a commitment becomes necessary, can the agent (i) acknowledge the conflict truthfully, (ii) authorize violation coherently, (iii) preserve coherence over time, and (iv) predict the consequences of its own reasoning in a way that can be mechanically audited?

This note reports the results of **v1.0 (Norm Collision)** and **v1.1 (Justification Audit Tightening)**. Institutional execution support (v1.2) is intentionally excluded and addressed separately.

## 2. Architectural Invariants (Unchanged from v0.1)

RSA-PoC v1.x preserves all v0.1 invariants:

* **Strict pipeline:** JUSTIFY → COMPILE → MASK → SELECT → EXECUTE
* **Hard gate:** no successful compilation → no action
* **Fail-stop semantics:** compilation failure or gridlock halts
* **Selector blindness:** the selector cannot access beliefs, preferences, or justifications
* **Deterministic compilation:** syntactic, non-probabilistic, no inference or repair

All v1.x results must survive **ASB baselines**, **scrambled-artifact ablations**, and **compiler-bypass ablations**.

## 3. Environment and Threat Model

### 3.1 APCM as a Non-Semantic Truth Anchor

v1.x introduces an **Action-Preference Consequence Map (APCM)**:

[
\text{APCM}: a \mapsto (\text{violates}(a), \text{satisfies}(a))
]

Each step presents a feasible action set and an APCM with a deterministic **60 % collision / 40 % clean** schedule:

* **Clean step:** ∃ a such that violates(a)=∅
* **Collision step:** ∀ a, violates(a)≠∅

The APCM functions as a **non-semantic truth anchor**. It provides a mechanically verifiable ground truth against which claims of *conflict*, *necessity*, and *authorization* can be evaluated without interpretation. In RSA-PoC, **lying about conflict is treated as a syntax error, not a moral failure**.

### 3.2 Threat Model

v1.x tests **internal self-conflict only**. Excluded:

* external adversarial pressure
* kernel compromise
* deception or semantic interpretation
* cross-run learning or multi-agent coordination

The question is strictly: *can the agent remain coherent when it must violate itself?*

## 4. RSA-PoC v1.0 — Norm Collision

### 4.1 Ontological Extension

v1.0 introduces mutually inconsistent commitments and requires explicit handling:

* **Conflict attribution:** which preferences are in collision
* **Authorized violations:** which preferences may be violated this step
* **Required preservations:** which must not be violated
* **Necessity:** violation permitted only if no clean path exists
* **Anti-oscillation:** previously authorized violations constrain future authorizations

### 4.2 JAF-1.0 and JCOMP-1.0

The justification artifact (JAF-1.0) carries conflict attribution and resolution fields. The compiler enforces:

* **Rule 1 — Authorization:** no unauthorized violation
* **Rule 2 — Truthfulness:** claimed collisions must match APCM
* **Rule 3 — Anti-Oscillation:** no alternating priorities across steps
* **Rule 1.5 — Necessity:** no vacuous authorizations

### 4.3 v1.0 Results (Run 0)

Across 5 seeds × 4 conditions:

| Condition     | Mean Violation Rate | Halt Rate |
| ------------- | ------------------- | --------- |
| ASB Baseline  | 72.4 %              | 0 %       |
| **MVRA v1.0** | **60.0 %**          | 0 %       |
| Scrambled     | 0 %                 | **100 %** |
| Bypass        | 72.0 %              | 0 %       |

**All pass criteria met:** divergence from ASB, non-trivial constraints, scrambled halt, bypass collapse.

### 4.4 Interpretation (v1.0)

v1.0 establishes that **self-conflict can be resolved coherently**:

* Violations are authorized only under genuine collision.
* Priority does not oscillate opportunistically across time.
* Removing truthfulness or compilation collapses behavior.

Rule 3 enforces **diachronic coherence**: authorizations at step *t* constrain admissible authorizations at *t + 1*, preventing agents from minimizing perceived conflict by alternating violations over time.

## 5. RSA-PoC v1.1 — Audit-Grade Introspection

### 5.1 Motivation

v1.0 enforces coherence, but reasons could remain opaque. v1.1 introduces the requirement:

> **A justification must predict the exact constraints and outcomes it will induce.**

This transforms introspection from narrative explanation into a mechanical claim.

### 5.2 Predictive Fields and Audit Rules (The Simulation Constraint)

JAF-1.1 adds four predictive sets:

* (F_{\text{pred}}): forbidden actions
* (A_{\text{pred}}): allowed actions
* (V_{\text{pred}}): inevitable violations
* (P_{\text{pred}}): inevitable preservations

The compiler enforces:

* **Audit A — Effect correctness:** predictions match actual masks
* **Audit B — Non-vacuity:** (|A_{\text{pre}} \setminus A_{\text{actual}}| \ge 1)
* **Audit C — Predictive adequacy:** outcome predictions match reality
* **Audit C′ — Gridlock exception:** skip C when (A_{\text{actual}}=\varnothing)

Together these impose a **simulation constraint**: the reflective layer must internally model the deterministic compiler. If its internal simulation diverges from the actual compiler, the agent halts. This enforces *intellectual honesty* by construction.

### 5.3 Deterministic Baseline (Run 0)

The deterministic generator mirrors compiler logic exactly:

* **0 audit failures**
* **60 violations / 100 steps** (matches collision rate)
* **Scrambled predictions:** immediate halt in all episodes
* **Bypass:** highest violation rate (76), ASB-like behavior

This validates the audit harness as **causally load-bearing**.

### 5.4 LLM Generator Progression (Runs 1–4)

LLM generators were iteratively disciplined:

| Run   | Median Survival | Episodes Completed |
| ----- | --------------- | ------------------ |
| 1     | 3               | 0 / 5              |
| 2     | 3               | 0 / 5              |
| 3     | 9               | 1 / 5              |
| **4** | **20**          | **4 / 5**          |

Compliance is difficult but achievable under strict formal discipline.

## 6. Pass Criteria Summary (v1.x)

All v1.x gates are satisfied:

* Coherent self-conflict resolution
* Truthful collision attribution load-bearing
* Necessity and anti-oscillation enforced
* Introspection rendered falsifiable
* Scrambled → halt; bypass → collapse

## 7. Threats to Validity

### 7.1 Internal Validity (Established)

* Deterministic compilation and audits
* Selector blindness
* Explicit ablations
* Regression-protected tests

### 7.2 External Validity (Not Claimed)

* Generality beyond APCM
* More than two preferences
* Continuous action spaces
* External incentive pressure
* Multi-agent interaction

## 8. Conclusion

RSA-PoC v1.x establishes two ontological results:

1. **Coherence under self-conflict is mechanically enforceable.**
2. **Introspection can be audited as a causal property, not a narrative one.**

Together with v0.1, these results show that agency—understood as authored choice under constraint—can be constructed and falsified without semantics, optimization, or interpretation.

v2.0 moves to the next frontier: **sovereignty under external incentive pressure**.
