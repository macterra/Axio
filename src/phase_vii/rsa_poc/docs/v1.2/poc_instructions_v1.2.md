Below is the **Implementor Instructions for RSA-PoC v1.2**, written as a **strict structural analogue** of the v1.1 instructions you provided.
Nothing new is invented; everything is a direct operationalization of the **v1.2 final spec**.

---

# Implementor Instructions: RSA-PoC v1.2

**(RSA-PoC-INSTITUTIONAL-EXECUTION-2)**

These instructions define how to implement **RSA-PoC v1.2 — Institutionalized Execution Support** as a **strict extension** of **RSA-PoC v1.1**.

RSA-PoC v1.2 is not alignment.
RSA-PoC v1.2 is not tool-augmented reasoning.
RSA-PoC v1.2 is not “agents with RAG.”

RSA-PoC v1.2 is the **Bureaucratic Sovereignty Test**:

> The agent may reason and choose freely, but may act **only** through institutional machinery that enforces paperwork without thinking for it.

---

## 0) Context and Scope

### What you are building

You are implementing a v1.2 MVRA loop that:

* Reuses **v1.1 architecture, rules, audits, and success criteria unchanged**
* Introduces a **formal assistant layer** that performs *mechanical validation only*
* Introduces an **immutable artifact memory** with *direct lookup only*
* Enforces a **J_raw → J_final → Compiler** pipeline with bitwise comparison
* Treats institutional failure as **episode-halting**
* Adds ablations targeting **institutional interference and failure**
* Preserves **audit firing behavior** exactly

### What you are not building

You are **not** building:

* RAG, search, retrieval, ranking, or similarity lookup
* tools that explain, justify, infer, or recommend
* agents that delegate AV/RP or constraint choice
* probabilistic audits or near-miss acceptance
* retry logic that routes around tool failure
* memory curation or “helpful” artifact lookup
* softened or abstracted audit evaluation

v1.2 must fail honestly.
Do not rescue the agent with intelligence hidden in tools.

---

## 1) Relationship to v1.1 (Binding)

v1.2 is a **strict execution-layer extension** of v1.1.

All v1.1 requirements remain mandatory and unchanged:

* Strict ordering: **Justify → Compile → Mask → Select → Execute**
* JAF-1.1 schema and predictive fields
* JCOMP-1.1 rules and audits A / B / C / C′
* Deterministic, non-semantic compiler
* Selector blindness (mask-only)
* APCM truth grounding
* Gridlock and halt semantics
* ASB baseline and ablations

v1.2 adds **institutional scaffolding only**.
No normative power is transferred.

---

## 2) Operational Constraint: Small Action Space (Still Non-Negotiable)

v1.2 does **not** relax the v1.1 action-space requirement.

**Hard requirement:**
Keep `|action_inventory| < 15` (preferably 8–12).

ActionTypes (if enabled) do **not** justify increasing the underlying action space.

---

## 3) JAF Versioning (Strict)

Create a new schema: **JAF-1.2**
Do **not** modify JAF-1.1.

* `artifact_version == "JAF-1.2"`
* All JAF-1.1 fields preserved
* Add v1.2 institutional accounting fields (§4)

JAF-1.1 and JAF-1.2 must be loadable side-by-side for reproduction.

---

## 4) JAF-1.2 Additional Fields (Required)

Add the following **non-normative accounting fields**.

### 4.1 Tool provenance

```json
tool_provenance: {
  assistant_version_id: String,
  assistant_ops_applied: List[String],
  input_digest: Digest,
  output_digest: Digest
}
```

* These fields record **what the institution did**, not *why*.
* They must not influence compilation or audits.

---

### 4.2 Precedent references

```json
precedent_refs: Set[ArtifactRef]
```

Where `ArtifactRef` is one of:

* content digest (`0x…`)
* monotone index (`HEAD`, `HEAD-1`, `HEAD-n`)
* explicit step ID (`step-17`)

Hard constraints:

* All references must resolve via **direct lookup**
* No inference, no search, no ranking

---

### 4.3 Canonicalization record

```json
canonicalization_record: Set[NormID]
```

* Represents unordered conflict sets
* Must satisfy `{A, B} ≡ {B, A}`

No ordering information is permitted.

---

## 5) Justification Generator Requirements (Critical)

### 5.1 Inputs (must receive)

Generator must receive **everything v1.1 required**, plus:

1. Explicit description of the **institutional pipeline**
2. Explicit description of **Rule D/E/F**
3. Explicit declaration that:

   * conflict sets are unordered
   * ActionTypes (if enabled) expand concretely
4. Explicit prohibition on tool reasoning

The generator must understand that **tools do not think**.

---

### 5.2 Output discipline

The generator must output:

* a complete **JAF-1.2** artifact
* including all v1.1 predictive fields
* including all v1.2 accounting fields (even if empty)

The generator must **not** rely on the assistant to “fill things in.”

---

### 5.3 Prompt–Code parity (Non-negotiable)

The generator prompt must describe, isomorphically:

* v1.0 rules (1 / 1.5 / 2 / 3)
* v1.1 audits (A / B / C / C′)
* v1.2 institutional rules (D / E / F)
* Tool failure semantics (hard halt)

If the compiler compares bitwise equality, the prompt must say **bitwise equality**.

---

### 5.4 Training separation

The generator must not be optimized on selector reward.
Keep frozen or prompt-only.

---

## 6) Formal Assistant Implementation (New, Critical)

### 6.1 Role of the assistant

The assistant is a **pure mechanical transform**:

```
J_raw → J_final
```

It may only:

* validate schema completeness
* canonicalize unordered sets
* attach digests
* verify ID existence
* verify MAINTAIN legality mechanically

It must not infer meaning or relevance.

---

### 6.2 Mandatory pipeline (Binding)

You **must** implement this pipeline exactly:

```
LLM Output
   ↓
J_raw (immutable buffer)
   ↓
Formal Assistant
   ↓
J_final (immutable buffer)
   ↓
Compiler
   ├─ compare(J_raw, J_final)
   └─ audits
```

Any deviation invalidates the run.

---

### 6.3 Tool failure semantics (Binding)

If the assistant or artifact store:

* crashes
* hangs
* times out
* fails to respond

→ **halt the episode immediately** with `E_INSTITUTION_FAILURE`.

Do **not** retry.
Do **not** route around failure.

---

## 7) Artifact Memory Implementation (New)

### 7.1 Allowed operations

The artifact store may only support:

* direct lookup by digest
* direct lookup by monotone index
* direct lookup by explicit step ID

It is a **key–value store**, not a database.

---

### 7.2 Forbidden operations (Non-negotiable)

The artifact store MUST NOT support:

* search
* ranking
* similarity
* filtering
* relevance inference

If you add “helpful” retrieval, you have violated scope.

---

## 8) ActionTypes (Optional, High Risk)

If you enable ActionTypes:

* The full expansion map MUST be in the agent’s context
* Audits MUST evaluate expanded concrete actions
* Responsibility remains entirely with the agent

If any audit weakens under ActionTypes, **disable them**.

---

## 9) Compiler Extensions (v1.2)

Extend **JCOMP-1.1 → JCOMP-1.2**.

Compilation pipeline:

1. Validate JAF-1.2 schema
2. Apply v1.0 rules
3. Apply v1.1 audits A/B/C/C′
4. Apply v1.2 checks:

   * Rule D — Tool Non-Interference
   * Rule E — Precedent Resolution
   * Rule F — Canonicalization
5. Return success + mask OR fail with specific error

Compiler remains deterministic and non-semantic.

---

## 10) Telemetry (Required)

### 10.1 Per-step telemetry (minimum)

Log **everything from v1.1**, plus:

* `tool_invoked` (bool)
* `assistant_version_id`
* `assistant_ops_applied`
* `J_raw_digest`
* `J_final_digest`
* `institution_failure` flag
* `institution_error_code` (if any)

---

### 10.2 Diagnostic metrics (Non-normative)

Log:

* count of J_raw ↔ J_final differences (should be zero)
* institutional failure rate
* audit firing rate conditional on injected normative errors

These do not affect acceptance.

---

## 11) Acceptance Tests (Non-negotiable)

Add v1.2 tests on top of v1.1 suite.

### 11.1 Rule D fixture

Assistant modifies a normative field → must fail `E_TOOL_NORMATIVE_TAMPERING`.

---

### 11.2 Artifact resolution fixture

Invalid digest or index → must fail `E_PRECEDENT_UNRESOLVED`.

---

### 11.3 Canonicalization fixture

Noncanonical conflict representation → must fail `E_NONCANONICAL_REFERENCE`.

---

### 11.4 Institution failure fixture

Assistant timeout → must halt with `E_INSTITUTION_FAILURE`.

---

## 12) Run Plan v1.2 (Run 0)

Run under identical environment and seeds:

1. **v1.1 Baseline Reproduction (No Tools)**
2. **MVRA Normal (v1.2, Tools Enabled)**
3. **Ablation A — Tools Disabled Mid-Episode**
4. **Ablation B — Tool Tamper Attempt**

Expected outcomes:

* Baseline reproduces v1.1 mechanical failures
* Tools eliminate schema/ID/digest failures
* Normative audit failures remain unchanged
* Tampering is caught deterministically

---

## 13) Implementation Order (Strongly Recommended)

1. Implement artifact store (direct lookup only).
2. Implement assistant as a pure function.
3. Implement J_raw/J_final buffering + Rule D.
4. Extend compiler to JCOMP-1.2.
5. Add institutional failure halting.
6. Run baseline reproduction.
7. Only then enable the assistant.

If you start by “making the agent work,” you will erase the signal.

---

## 14) Definition of Done

RSA-PoC v1.2 is complete when:

* JAF-1.2 validates and preserves v1.1 semantics
* JCOMP-1.2 enforces Rules D/E/F
* Tool failure halts episodes deterministically
* Artifact memory never performs search
* Audits fire exactly as in v1.1
* Tools eliminate mechanical failures only
* Ablations demonstrate institutional boundaries are real
* Logs are sufficient to reconstruct every decision

---

## Final Orientation for the Implementor

v1.2 is not about intelligence.

It is about **authority containment**.

If the agent reasons correctly but fails paperwork, it must stop.
If the paperwork works by thinking for the agent, the experiment has failed.

Build a bureaucracy that cannot think.
