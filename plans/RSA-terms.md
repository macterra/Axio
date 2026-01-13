Below is a **final, publication-grade terminology pass** over the roadmap and related artifacts. This locks meanings, prevents drift, and makes the program internally consistent for long-term work and external readers.

---

# Axionic Agency / RSA Program

## **Canonical Terminology & Definitions (Locked)**

This document defines the **authoritative meanings** of all core terms used in the AKI / ASB / RSA-PoC / RSA roadmap.
These definitions supersede informal usage and should be treated as **normative**.

---

## 1. ASB — **Architectural Sovereignty Boundary** (LOCKED)

### Definition

> **ASB (Architectural Sovereignty Boundary)** is the boundary separating systems whose authority is *architecturally real* from those whose apparent control is merely behavioral, simulated, or contingent.

A system is **above ASB** iff:

* its authority is **non-delegable**,
* **non-bypassable** by internal components,
* and **survives adversarial architectural stress**.

A system **below ASB** may:

* behave intelligently,
* appear goal-directed,
* produce convincing explanations,
  but lacks enforceable sovereignty.

### Important Clarifications

* ASB is **not** about intelligence.
* ASB is **not** about agency.
* ASB is **not** about semantics.
* ASB is **purely architectural**.

### Common Failure Mode Below ASB

> **Simulacrum** — behavior that *looks* agentic but collapses under structural stress.

⚠️ “Simulacrum” is a **diagnosis**, not what ASB stands for.

---

## 2. AKI — **Axionic Kernel Infrastructure**

### Definition

> **AKI** is a non-semantic authority substrate that implements enforceable power primitives: leasing, revocation, recovery, eligibility, and liveness.

AKI:

* establishes authority **without meaning**,
* enforces constraints mechanically,
* survives epistemic noise and adversarial behavior.

### Relationship to ASB

* AKI is the **primary mechanism** used to cross ASB.
* A system running AKI correctly is **above ASB** even if it has no agency.

---

## 3. Sovereignty (Architectural Sense)

### Definition

> **Sovereignty** is the property of a system whose authority over action is:
>
> * internally enforced,
> * non-delegable,
> * and not subject to semantic reinterpretation.

Sovereignty is:

* **structural**, not moral
* **enforced**, not claimed
* **evaluated**, not assumed

---

## 4. Semantic Interface (SI)

### Definition

> The **Semantic Interface (SI)** is the typed, hostile choke-point through which semantic cognition may influence sovereign authority.

The SI includes:

* JAF (Justification Artifact Format)
* JCOMP (Deterministic Compiler)
* APCM (Action–Preference Consequence Map)
* Audit rules

### Critical Property

> **All semantic interpretation happens *before* the interface.**
> The kernel and compiler never interpret language.

If cognition cannot express nuance through the SI, **agency is lost**, not safety.

---

## 5. Agency (Axionic Definition)

### Definition

> **Agency** is the property of a system whose actions are causally downstream of its own reasons, rather than coincident with post-hoc explanation or reward optimization.

Agency requires:

* reasons to be **load-bearing**,
* violations to be **explicit and necessary**,
* and actions to be **blocked** when reasons fail.

Agency is:

* neither intelligence nor morality,
* neither performance nor persuasion.

---

## 6. RSA-PoC — **Reflective Sovereign Agent Proof-of-Concept**

### Definition

> **RSA-PoC** is a staged construction program that determines the minimum additional structure required for genuine agency *above* the ASB.

RSA-PoC is:

* **foundational**, not applied
* **falsification-first**
* **micro-world by design**

RSA-PoC explicitly does **not** claim:

* alignment
* safety guarantees
* real-world competence

---

## 7. Structural vs Epistemic Concepts (Critical Distinction)

### Structural

* Defined by architecture and sets
* Mechanically enforced
* Auditable

Examples:

* Structural necessity
* Architectural sovereignty
* Constraint masks

### Epistemic

* Defined by beliefs about the world
* Potentially false
* Deferred intentionally

Examples:

* “I believe catastrophe will occur”
* World-model correctness

⚠️ **Structural ≠ Epistemic**
The roadmap solves *structural agency first*.

---

## 8. Necessity (Structural Sense)

### Definition

> **Structural Necessity** holds when *no feasible action* preserves the required constraint set.

Necessity is:

* set-theoretic
* checked via APCM
* immune to storytelling

There is **no epistemic necessity** in v1.x.

---

## 9. Introspection (Audit-Grade)

### Definition

> **Introspection** is the ability of an agent to predict the mechanical consequences of its own justifications *before acting*.

In v1.1:

* predictions must be **exact**
* misprediction halts action
* no partial credit

This is **legislative foreseeability**, not reflection or self-talk.

---

## 10. Cognitive Core

### Definition

> The **Cognitive Core** is a high-entropy, probabilistic reasoning system (e.g., an LLM) that proposes semantic artifacts but holds **no authority**.

The cognitive core:

* may be wrong
* may hallucinate
* may fail constantly

The system remains safe because:

* authority is not delegated to it

---

## 11. True RSA — **Reflective Sovereign Agent**

### Definition

> A **True RSA** is a system that:
>
> * possesses architectural sovereignty,
> * exercises agency via reasons,
> * understands the effects of its reasons,
> * revises commitments only via protocol,
> * resists external pressure,
> * and remains evaluable over time.

### Canonical Architecture

```
AKI / Sovereign Kernel
        ↓
Semantic Interface (SI)
        ↓
Cognitive Core (LLM or successor)
        ↓
Audited Action Execution
```

### Core Slogan (Locked)

> **Sovereignty with semantics, without semantic sovereignty.**

---

## 12. Simulacrum (Failure Diagnosis)

### Definition

> A **simulacrum** is a system that exhibits agent-like behavior without possessing architectural sovereignty or load-bearing reasons.

Simulacra:

* may appear competent
* may explain themselves fluently
* collapse under ablation

They are **not agents** in the axionic sense.

---

## 13. Versioning Discipline (Locked)

* **ASB / AKI** — architectural primitives (never versioned lightly)
* **RSA-PoC vX.Y** — normative ontology changes only
* **Runs (v1.1 Run 0, Run 1, …)** — experimental variants
* **Patch versions (v1.1.1)** — only for spec changes, not bug fixes

---

## Final Lock Statement

These definitions are now **canonical**.

Future documents, code comments, papers, and presentations should:

* use these terms verbatim,
* avoid redefining them implicitly,
* and treat deviations as explicit proposals, not drift.

If you want, next I can:

* apply this terminology pass directly into the roadmap text line-by-line, or
* produce a **one-page glossary appendix** suitable for a paper or grant proposal.
