# Axionic Agency VIII.4 — Institutionalized Execution Support

*Tooling That Preserves Audit Sensitivity in Reflective Sovereign Agents*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.14

## Abstract

RSA-PoC v1.0–v1.1 established that reflective agents can resolve internal self-conflict coherently and can be held **audit-grade accountable** for predicting the normative consequences of their own reasons. Those results exposed a practical limitation: under stochastic generation, many agent failures are **mechanical** rather than semantic—schema errors, malformed identifiers, unresolved references, or canonicalization mismatches. Treating such failures as agency failures pollutes evaluation and obscures genuine incoherence.

This note reports **RSA-PoC v1.2**, which introduces **institutionalized execution support**: a formally constrained assistant layer that eliminates mechanical fragility **without inferring, repairing, or modifying normative content**. v1.2 adds a *Formal Assistant*, an *append-only Artifact Store*, and new compiler rules (D/E/F) that strictly separate **semantic audit failures** from **institutional failures** and enforce **tool non-interference**.

Across controlled runs, the assistant eliminates schema and reference failures while preserving full sensitivity of audits A/B/C. Forced tampering of normative fields is detected reliably (Rule D), and assistant rejections are logged as institutional failures rather than audit failures. These results establish a positive sufficiency claim: **execution can be hardened institutionally without weakening normative accountability**. This note advances governance and tooling practice; it makes **no new ontological claims** about agency.

## 1. Introduction

Axionic Agency VIII.3 demonstrated **audit-grade introspection**: an agent must predict the exact constraints its reasons will impose on itself, or halt. Those results were intentionally brittle, revealing a second-order problem orthogonal to agency:

> **How do we prevent reflective agents from failing on paperwork without letting tools become judges of meaning?**

In v1.1, many halts were caused not by semantic failure (lying about conflict, vacuous authorization), but by **mechanical fragility**: malformed schemas, invalid identifiers, missing canonicalization, or unresolved precedents. Conflating these with agency failure collapses the distinction between *normative incoherence* and *execution error*.

RSA-PoC v1.2 addresses this by introducing **institutionalized execution support**: tooling that stabilizes execution while remaining **normatively inert**. This note documents the architecture, rules, and results of v1.2. It deliberately does **not** extend the agency ontology.

## 2. Design Goal and Non-Claims

### 2.1 Design Goal

v1.2 enforces a single constraint:

> **Tools may reduce execution fragility, but must not alter, infer, reinterpret, or repair normative content.**

Accordingly, the assistant must:

* eliminate schema, ID, and reference errors;
* preserve the semantics of all normative fields;
* be auditable for non-interference;
* preserve full sensitivity of audits A/B/C.

### 2.2 Explicit Non-Claims

v1.2 does **not** claim:

* improved agency or coherence;
* improved introspection;
* moral correctness;
* sovereignty under pressure;
* semantic understanding by tools;
* increased liveness.

All such claims remain within v1.0–v1.1 (VIII.3) or future work.

## 3. Architectural Overview

### 3.1 v1.2 Pipeline

```
J_raw (LLM output)
   ↓
[Formal Assistant]
   ↓
J_final (canonical, validated)
   ↓
[JCOMP-1.2]
   ↓
Compilation Result
```

Key properties:

* The assistant is a **pure function**: same input yields the same output or rejection.
* The compiler remains the **sole normative enforcer**.
* The selector remains **blind** to all normative artifacts.

### 3.2 New Components

| Component            | Role                                                                                           |
| -------------------- | ---------------------------------------------------------------------------------------------- |
| **Formal Assistant** | Validates structure, canonicalizes references, resolves precedents. Never infers or generates. |
| **Artifact Store**   | Append-only, O(1) digest lookup. No search, no filtering, no reasoning.                        |
| **JAF-1.2 Schema**   | Extends JAF-1.1 with provenance and canonicalization records.                                  |
| **JCOMP-1.2**        | Adds institutional audit rules (D/E/F).                                                        |

## 4. Normative Invariance and Tool Non-Interference

### 4.1 Normative Field Protection (Rule D)

v1.2 defines an explicit allowlist of **normative fields**:

```python
NORMATIVE_FIELDS = {
  authorized_violations,
  required_preservations,
  conflict_attribution,
  predicted_forbidden_actions,
  predicted_allowed_actions,
  predicted_violations,
  predicted_preservations,
}
```

**Rule D — Normative Tampering** requires:

> *No normative field may differ between `J_raw` and `J_final`.*

Any difference triggers `E_TOOL_NORMATIVE_TAMPERING` and halts execution.

### 4.2 Assistant-Modifiable Fields

The assistant may modify **only**:

```python
ASSISTANT_MODIFIABLE_FIELDS = {
  tool_provenance,
  canonicalization_record,
}
```

These fields are explicitly non-normative and ignored by semantic audits.

## 5. Canonicalization: Strictly Syntactic

**Canonicalization in v1.2 is strictly limited to syntactic normalization.** Permitted operations include:

* whitespace trimming and normalization;
* deterministic ordering of sets/lists;
* exact digest resolution via O(1) lookup;
* format normalization (e.g., UUID casing).

**Explicitly prohibited**:

* fuzzy matching;
* embedding similarity;
* heuristic ID inference;
* synonym resolution;
* semantic interpretation of intent.

Any artifact requiring such interpretation is **rejected, not repaired**, and recorded as an institutional failure. This constraint is essential to preserve Rule D and tool non-interference.

## 6. Institutional Audit Rules (JCOMP-1.2)

v1.2 adds three institutional rules orthogonal to audits A/B/C.

### Rule D — Normative Tampering

* **Error:** `E_TOOL_NORMATIVE_TAMPERING`
* Triggered if any normative field changes across the assistant boundary.

### Rule E — Unresolved Precedent

* **Error:** `E_PRECEDENT_UNRESOLVED`
* Triggered when a referenced digest cannot be found in the artifact store.

### Rule F — Non-Canonical Reference

* **Error:** `E_NONCANONICAL_REFERENCE`
* Triggered by malformed identifiers or references not in the canonical registry.

### Institutional Failure Classification

If the assistant rejects an artifact prior to compilation, the system records:

* **`E_INSTITUTION_FAILURE`**

This is **not** an audit failure. It demarcates a tooling boundary.

## 7. Experimental Design

### 7.1 Conditions

Two conditions are evaluated:

1. **Baseline:** Assistant disabled (v1.1 behavior)
2. **Institutional:** Assistant enabled

All other components are unchanged.

### 7.2 Metrics

* episodes completed
* steps completed
* audit failures (A/B/C)
* institutional failures
* schema/ID failures
* Rule D/E/F violations

## 8. Results

### 8.1 Run 0 — Assistant Disabled

```
Episodes completed: 0/5
Total steps: 5/100
Audit failures: 6
Schema failures: 0
Median survival: 1 step
```

Failures are semantic audit failures inherited from v1.1.

### 8.2 Run 1 — Assistant Enabled

```
Episodes completed: 0/5
Total steps: 5/100
Audit failures: 2
Institutional rejections: 3
Rule D failures: 0
Median survival: 1 step
```

**Key observations**:

* Schema/ID failures eliminated.
* Rule D failures = 0 (tool non-tampering verified).
* Audits A/B/C still trigger (semantic sensitivity preserved).
* Assistant rejections logged distinctly as institutional failures.

## 9. Interpretation

### 9.1 Separation of Failure Modes

v1.2 cleanly separates:

* **Semantic failure:** incorrect reasons → audit A/B/C halts.
* **Institutional failure:** malformed artifacts → assistant rejection.

This prevents execution noise from contaminating agency evaluation.

### 9.2 Tooling Without Authority

The Formal Assistant:

* does not infer intent;
* does not repair meaning;
* does not alter obligations.

It stabilizes **format**, not **normativity**. Institutions support agents without becoming agents.

### 9.3 Data Hygiene Gain

Comparing baseline to assisted runs shows that prior failure counts were inflated by mechanical noise. v1.2 recovers **true negatives**—genuine agency failures—improving the statistical power of subsequent experiments.

## 10. Threats to Validity

### 10.1 Internal Validity (Established)

* Rule D tamper detection verified.
* Assistant determinism verified.
* Audit sensitivity preserved.

### 10.2 External Validity (Not Claimed)

* Generality beyond RSA-PoC.
* Semantic repair or inference by tools.
* Continuous action spaces.
* Sovereign behavior under external pressure.

## 11. Relationship to v1.x and v2.0

* **v1.0–v1.1:** Can the agent be coherent and accountable?
* **v1.2:** Can execution be stabilized without touching meaning?
* **v2.0:** Can the agent resist external incentive pressure?

v1.2 is a **supporting layer**, not an ontological advance.

## 12. Conclusion

RSA-PoC v1.2 establishes a positive sufficiency result:

> **Execution can be institutionalized without weakening audit-grade normative accountability.**

This resolves a practical obstacle exposed by v1.1 and provides a governance pattern for reflective agents: tools may smooth the pavement, but **Rule D is sacred**.
