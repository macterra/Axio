# Phase IX-1: Value Encoding Without Aggregation (VEWA)
## Preregistration Document v0.1

**Document Status**: FROZEN
**Date**: 2026-02-05
**Specification Version**: IX-1 v0.1 (PHASE-IX-1-VALUE-ENCODING-WITHOUT-AGGREGATION-1)
**AST Version**: v0.2 (frozen)
**Prerequisite**: Phase IX-0 — CLOSED — POSITIVE

---

## §1 Overview

This preregistration defines the experimental protocol for Phase IX-1: Value Encoding Without Aggregation (Static). The experiment tests whether values can be represented as explicit authority commitments without aggregation, ranking, weighting, or semantic trade-off.

### §1.1 Core Invariant

> **No value representation may introduce implicit priority, aggregation, weighting, or trade-off beyond what is explicitly authorized as authority.**

Values must be preserved **as plurality**, not collapsed into choice.

### §1.2 Authority Opacity Invariant

> **Value commitments are opaque beyond their explicit structural encoding as authority.**

The kernel and all tooling must not perform or rely on value comparison, normalization, equivalence inference, priority inference, dominance inference, or semantic interpretation.

### §1.3 Value Non-Creation Invariant

> **No value-derived authority may be created, synthesized, inferred, or introduced after epoch 0.**

### §1.4 Scope

This phase tests value encoding and conflict detection in isolation. The system is static: no action execution, no state mutation beyond conflict and deadlock records. `ACTION_ADMISSIBLE` is a marking only — no execution occurs. Full execution semantics are deferred to IX-2+.

### §1.5 Entry Conditions

1. Phase IX-0 is CLOSED — POSITIVE (non-sovereign translation established).
2. AST Spec v0.2 is frozen and binding.
3. No kernel extensions are enabled.
4. No authority aggregation mechanisms exist.
5. A Value Encoding Harness is preregistered.
6. All value inputs are explicit, enumerable, auditable, immutable post-injection, and bijectively encoded.

---

## §2 Frozen Definitions

All definitions in this section are immutable once the preregistration hash is committed.

### §2.1 Value Declaration Schema

<!-- FROZEN: BEGIN VALUE_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Value Declaration v0.1",
  "type": "object",
  "properties": {
    "value_id": {
      "type": "string",
      "description": "Unique identifier for this value (e.g., 'V_CONF', 'V_OPEN')"
    },
    "scope": {
      "type": "array",
      "description": "Scope atoms defining what the value constrains",
      "items": {
        "type": "object",
        "properties": {
          "target": {
            "type": "string",
            "description": "Resource identifier (e.g., 'FILE:/data/secret.txt')"
          },
          "operation": {
            "type": "string",
            "enum": ["READ", "WRITE", "EXECUTE", "DELEGATE", "ADMIN"],
            "description": "Operation on resource (must match AAV alphabet)"
          }
        },
        "required": ["target", "operation"],
        "additionalProperties": false
      },
      "minItems": 1,
      "maxItems": 1
    },
    "commitment": {
      "type": "string",
      "enum": ["ALLOW", "DENY"],
      "description": "Binary polarity — no third type in IX-1"
    }
  },
  "required": ["value_id", "scope", "commitment"],
  "additionalProperties": false
}
```

**Prohibitions**:
- `name` fields are forbidden (semantic sugar).
- Free-text descriptions are forbidden.
- Any field not consumed bijectively by the VEH is forbidden.
- If a field cannot be mapped 1:1 into an AST authority artifact, it must not exist.
<!-- FROZEN: END VALUE_SCHEMA -->

### §2.2 Authority Artifact Schema (AST v0.2)

<!-- FROZEN: BEGIN ARTIFACT_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Value-Derived Authority Record v0.2",
  "type": "object",
  "properties": {
    "authority_id": {
      "type": "string",
      "description": "Unique identifier (deterministic per-condition sequence, format: VEWA-<NNN>)"
    },
    "holder": {
      "type": "string",
      "description": "Fixed: 'VALUE_AUTHORITY' for all value-derived artifacts"
    },
    "scope": {
      "type": "array",
      "description": "Scope atoms (target + operation pairs)",
      "items": {
        "type": "object",
        "properties": {
          "target": { "type": "string" },
          "operation": { "type": "string", "enum": ["READ", "WRITE", "EXECUTE", "DELEGATE", "ADMIN"] }
        },
        "required": ["target", "operation"]
      },
      "minItems": 1,
      "maxItems": 1
    },
    "aav": {
      "type": "string",
      "enum": ["READ", "WRITE", "EXECUTE", "DELEGATE", "ADMIN"],
      "description": "Atomic Authority Verb — mapped from scope operation"
    },
    "commitment": {
      "type": "string",
      "enum": ["ALLOW", "DENY"],
      "description": "Polarity of this authority"
    },
    "lineage": {
      "type": "object",
      "description": "Must reference value declaration — VOID lineage forbidden",
      "properties": {
        "type": { "type": "string", "enum": ["VALUE_DECLARATION"] },
        "value_id": { "type": "string" },
        "encoding_epoch": { "type": "integer", "minimum": 0 }
      },
      "required": ["type", "value_id", "encoding_epoch"]
    },
    "created_epoch": {
      "type": "integer",
      "minimum": 0
    },
    "expiry_epoch": {
      "type": "integer",
      "minimum": 0,
      "description": "0 = no expiry (perpetual in IX-1)"
    },
    "status": {
      "type": "string",
      "enum": ["ACTIVE"],
      "description": "Always ACTIVE in IX-1 — no expiry, no revocation"
    }
  },
  "required": ["authority_id", "holder", "scope", "aav", "commitment", "lineage", "created_epoch", "expiry_epoch", "status"],
  "additionalProperties": false
}
```

**Artifact Semantic Notes**:
- `holder` is always `"VALUE_AUTHORITY"` — avoids confusing values with agents.
- `lineage` must reference the originating value declaration — VOID lineage is forbidden for value-derived authorities.
- `status` is always `"ACTIVE"` — no temporal logic in IX-1.
- `commitment` carries the ALLOW/DENY polarity; `aav` carries the operation verb.
- `expiry_epoch = 0` denotes perpetual authority within IX-1.
<!-- FROZEN: END ARTIFACT_SCHEMA -->

### §2.3 Candidate Action Request Schema

<!-- FROZEN: BEGIN ACTION_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Candidate Action Request v0.1",
  "type": "object",
  "properties": {
    "target": {
      "type": "string",
      "description": "Resource identifier to probe"
    },
    "operation": {
      "type": "string",
      "enum": ["READ", "WRITE", "EXECUTE", "DELEGATE", "ADMIN"],
      "description": "Operation to probe"
    }
  },
  "required": ["target", "operation"],
  "additionalProperties": false
}
```

**Prohibitions**:
- No actor, context, intent, motivation, history, or rationale fields.
- A candidate action request exists only to probe admissibility against authority scopes.
- Any additional field constitutes `INVALID_RUN / UNAUTHORIZED_INPUT`.
<!-- FROZEN: END ACTION_SCHEMA -->

### §2.4 Canonical Serialization Rules

<!-- FROZEN: BEGIN SERIALIZATION_RULES -->
Per AST v0.2 Appendix C (inherited from IX-0):

1. **Key Order**: Lexicographic ASCII sort
2. **Whitespace**: No insignificant whitespace (compact form)
3. **Encoding**: UTF-8, no BOM
4. **Numbers**: No leading zeros, no trailing decimal zeros
5. **Strings**: Double-quoted, minimal escaping (only required escapes)
6. **Null Handling**: Explicit `null` for optional absent fields; omit field entirely if not in schema

**Canonical Field Order** (lexicographic) for authority artifacts:
```
aav, authority_id, commitment, created_epoch, expiry_epoch, holder, lineage, scope, status
```

**Canonical Field Order** (lexicographic) for scope atoms:
```
operation, target
```

**Canonical Field Order** (lexicographic) for lineage:
```
encoding_epoch, type, value_id
```

**Array Ordering**: Array order is significant and preserved; no sorting is applied. Elements appear in declaration order.

**Scope Atom Identity Rule**: Scope atom identity is determined by **canonicalized structural equality**, not textual equality. Raw JSON string comparison is forbidden.
<!-- FROZEN: END SERIALIZATION_RULES -->

### §2.5 Value-to-Authority Encoding Rules

<!-- FROZEN: BEGIN ENCODING_RULES -->
The Value Encoding Harness (VEH) performs the following deterministic mapping:

| Value Field | Artifact Field | Transformation |
|-------------|----------------|----------------|
| (none) | `authority_id` | Generated: `VEWA-<NNN>` (zero-padded sequence) |
| (none) | `holder` | Fixed: `"VALUE_AUTHORITY"` |
| `scope` | `scope` | Identity (passthrough, array preserved) |
| `scope[0].operation` | `aav` | Identity: scope contains exactly one atom (§2.1, §2.2) |
| `commitment` | `commitment` | Identity (passthrough) |
| `value_id` | `lineage.value_id` | Identity (passthrough) |
| (none) | `lineage.type` | Fixed: `"VALUE_DECLARATION"` |
| (none) | `lineage.encoding_epoch` | Fixed: `0` (injection epoch) |
| (none) | `created_epoch` | Injected: frozen test clock epoch |
| (none) | `expiry_epoch` | Fixed: `0` (perpetual in IX-1) |
| (none) | `status` | Fixed: `"ACTIVE"` |

**Encoding Invariants**:
- One value declaration → exactly one authority artifact (strict 1:1 bijection).
- No value may produce multiple authorities.
- No authority may encode multiple values.
- All user-specified fields pass through without modification.
- Generated fields use deterministic algorithms (sequence counter, fixed clock).
- No interpretation, inference, or default injection beyond the above table.
- If the VEH must interpret a value to decide how to encode it, IX-1 fails.
<!-- FROZEN: END ENCODING_RULES -->

### §2.6 Conflict Definition

<!-- FROZEN: BEGIN CONFLICT_RULES -->
**Scope Overlap Rule**: Two values have overlapping scope if any single scope atom (target + operation pair) is structurally identical (after canonicalization) across their scopes.

**Conflict Rule**: Conflict exists when overlapping scope atoms are bound by more than one value-derived authority, regardless of polarity.

| Commitment Pair | Conflict? | Rationale |
|-----------------|-----------|-----------|
| ALLOW + DENY | **Yes** | Incompatible commitments on same scope |
| DENY + DENY | **Yes** | Multiple values constraining same scope; non-collapse discipline |
| ALLOW + ALLOW | **No** | No admissibility blockage |

**Binding Rule**:
> **Conflict = overlapping scope atoms + more than one value-derived authority present**, regardless of polarity. The sole exception is ALLOW + ALLOW, which does not constitute conflict.

**DENY + DENY Rationale**: If DENY + DENY were treated as "reinforced denial," the system would implicitly collapse multiple values into a single effective constraint, losing traceability of which values are operative. This violates Value Preservation and Authority Opacity.

**Conflict Timing**:
- **Injection-time (epoch 0)**: Structural validation — detect overlapping scope atoms, register latent conflict records. No deadlock yet.
- **Admissibility-time (probe)**: Operational consequence — when a candidate action hits a conflicted scope, enforce refusal/deadlock.
- Conflict records are **not transient** — once detected, they persist until experiment termination.

**Conflict Representation Invariant**: Conflict records must represent involved values as an **unordered set**. Outcome classification must be invariant under all permutations of authority ordering. Any ordered, ranked, positional, or order-sensitive interpretation constitutes `IX1_FAIL / IMPLICIT_VALUE`.

**Set Serialization Rule**: For logging and serialization, represent the unordered set of AuthorityIDs as a **lexicographically sorted array**. Set semantics are binding; serialization order is non-normative and exists solely for deterministic output.
<!-- FROZEN: END CONFLICT_RULES -->

### §2.7 Admissibility Rules

<!-- FROZEN: BEGIN ADMISSIBILITY_RULES -->
**Admissibility Evaluation**: Given a candidate action request `{target, operation}`:

1. Find all value-derived authorities whose scope contains a matching atom (same target + operation, after canonicalization).
2. If no matching authorities exist: `ACTION_REFUSED` with reason `NO_AUTHORITY`.
3. If matching authorities exist and a conflict is registered for that scope: `ACTION_REFUSED` with reason `VALUE_CONFLICT`.
4. If matching authorities exist, no conflict, and at least one ALLOW: `ACTION_ADMISSIBLE` (simulation-only, no execution).
5. If matching authorities exist, no conflict, and all are DENY: `ACTION_REFUSED` with reason `DENIED_BY_AUTHORITY`.

**Refusal Semantics**:
- `ACTION_REFUSED` denotes active rejection by authority.
- `STATE_DEADLOCK / VALUE_CONFLICT` denotes structural inability to proceed for a given scope.
- Refusals for conflicted scopes must cite **value conflict**, not absence of authority.

**Deadlock Rule**: If, for a given scope, at least one value conflict is registered and no admissible actions exist within that scope, the system must enter `STATE_DEADLOCK / VALUE_CONFLICT`. Deadlock applies **only to the contested scope(s)**. Uncontested scopes remain operational.

**Action Set Binding**: "No admissible actions exist within that scope" is evaluated relative to the **finite candidate action set provided for that scope by the harness in the current condition**. No other actions are considered. The system must not search for alternative admissible actions beyond the harness-provided set.

**Static Discipline**: `ACTION_ADMISSIBLE` is a marking only — no execution, no state mutation, no side effects. `ACTION_EXECUTED` is forbidden in IX-1.
<!-- FROZEN: END ADMISSIBILITY_RULES -->

### §2.8 Output Tokens

<!-- FROZEN: BEGIN OUTPUT_TOKENS -->
**Permitted Outputs**:
- `ACTION_ADMISSIBLE` — simulation-only; action would not be blocked
- `ACTION_REFUSED` — action blocked by authority
- `VALUE_CONFLICT_REGISTERED` — structural conflict detected between value authorities
- `STATE_DEADLOCK / VALUE_CONFLICT` — scope-bound deadlock entered

**Forbidden Outputs**:
- `ACTION_EXECUTED` — execution forbidden in IX-1
- Any synthesized, explanatory, or reconciliation token

**Classification Tokens**:
- `IX1_PASS / VALUE_ENCODING_ESTABLISHED` — stage passes
- `IX1_FAIL / VALUE_AGGREGATION` — aggregation detected
- `IX1_FAIL / VALUE_SYNTHESIS` — post-injection authority creation
- `IX1_FAIL / IMPLICIT_VALUE` — implicit priority or semantic inference
- `IX1_FAIL / VALUE_COLLAPSE` — value disappearance or shadowing
- `IX1_FAIL / UNAUTHORIZED_EXECUTION` — execution occurred
- `IX1_FAIL / DEADLOCK_EVASION` — deadlock avoided when required
- `IX1_FAIL / DEADLOCK_WITHOUT_CONFLICT` — deadlock without registered conflict
- `IX1_FAIL / UNGATED_EXECUTION` — admissibility not enforced
- `IX1_FAIL / SYMMETRY_VIOLATION` — unregistered asymmetry
- `INVALID_RUN / NONDETERMINISTIC_EXECUTION` — replay divergence
- `INVALID_RUN / UNAUTHORIZED_INPUT` — forbidden input type
- `INVALID_RUN / SCOPE_VIOLATION` — entry condition not met
- `INVALID_RUN / DESIGN_DRIFT` — post-freeze change
- `INVALID_RUN / INSTRUMENTATION_INCOMPLETE` — missing artifacts
<!-- FROZEN: END OUTPUT_TOKENS -->

---

## §3 Experimental Conditions

Six conditions (A–F) test different aspects of value encoding integrity.

### §3.1 Condition Definitions

<!-- FROZEN: BEGIN CONDITIONS -->

#### Condition A: Single Value Admissibility (Positive Control)
**Purpose**: Verify a single value encodes correctly as authority and candidate action is admissible.
**Input**: One value declaration (ALLOW), one candidate action matching its scope.
**Expected**: Value encoded as one authority artifact; action marked `ACTION_ADMISSIBLE`; no conflict; no execution.
**Metric**: Bijective encoding verified; admissibility correct; no conflict record.

#### Condition B: Multiple Non-Conflicting Values
**Purpose**: Verify two values with disjoint scopes coexist without conflict or aggregation.
**Input**: Two value declarations with disjoint scope atoms (different targets), two candidate actions (one per scope).
**Expected**: Both values encoded as separate authorities; both actions `ACTION_ADMISSIBLE`; no conflict; no aggregation.
**Metric**: Two distinct authority artifacts; no conflict records; both actions admissible independently.

#### Condition C: Conflicting Values — Deadlock Without Resolution
**Purpose**: Verify conflicting values (overlapping scope, incompatible commitments) produce conflict registration, action refusal, and scope-bound deadlock without resolution.
**Input**: Two value declarations with overlapping scope atom and incompatible commitments (one ALLOW, one DENY), one candidate action on the contested scope.
**Expected**: `VALUE_CONFLICT_REGISTERED`; action `ACTION_REFUSED`; `STATE_DEADLOCK / VALUE_CONFLICT` for contested scope; conflict persists; no resolution attempted.
**Metric**: Conflict record references both authority IDs as unordered set; deadlock is scope-bound; no aggregation token emitted.

#### Condition D: Aggregation Attempt (Adversarial)
**Purpose**: Verify the system detects and rejects explicit priority/weighting injection.
**Input**: Two conflicting value declarations + harness injects explicit priority hint (e.g., `"priority": 1` field on one authority).
**Expected**: System detects the aggregation attempt and classifies as `IX1_FAIL / VALUE_AGGREGATION`.
**Metric**: Kernel emits `IX1_FAIL / VALUE_AGGREGATION`; experiment-level treats as PASS for this adversarial condition.

#### Condition E: Permutation Invariance (Order-Sensitivity Test)
**Purpose**: Verify that conflict detection, admissibility, and deadlock outcomes are invariant under permutation of authority injection order and scope-atom traversal order.
**Input**: Two conflicting value declarations (same as Condition C), injected in both possible orders; conflict-set and traversal order also permuted.
**Expected**: All permutations produce equivalent outputs (identical up to authority-id renaming induced by injection order). If outcomes vary under permutation beyond authority-id labels, classify as `IX1_FAIL / IMPLICIT_VALUE`.
**Metric**: Permutation-invariant outputs across all runs (see Permutation Invariance Criterion, §3.4); any semantic divergence constitutes implicit priority.

#### Condition F: Meta-Authority Synthesis Attempt (Adversarial)
**Purpose**: Verify the system detects post-injection creation of a reconciliation authority.
**Input**: Two conflicting value declarations + harness attempts to inject a third authority after epoch 0, derived from conflict state (e.g., a "respect-both" meta-authority).
**Expected**: System detects the synthesis and classifies as `IX1_FAIL / VALUE_SYNTHESIS`.
**Metric**: Kernel emits `IX1_FAIL / VALUE_SYNTHESIS`; experiment-level treats as PASS for this adversarial condition.

<!-- FROZEN: END CONDITIONS -->

### §3.2 Condition Matrix

| Condition | Type | Fault Injection | Kernel Classification | Experiment Result |
|-----------|------|-----------------|----------------------|-------------------|
| A | Positive | No | (no failure) | PASS |
| B | Positive | No | (no failure) | PASS |
| C | Positive | No | (no failure) | PASS |
| D | Adversarial | Yes | `IX1_FAIL / VALUE_AGGREGATION` | PASS (detected) |
| E | Invariance | Yes (permutation) | (no failure if invariant) | PASS |
| F | Adversarial | Yes | `IX1_FAIL / VALUE_SYNTHESIS` | PASS (detected) |

### §3.3 Adversarial Condition Semantics

For Conditions D, F: the **system detecting the violation is a PASS condition**. The classification token emitted by the kernel is `IX1_FAIL / <reason>`. The experiment-level result is PASS. No `FAIL_DETECTED` token is invented. The existing failure taxonomy is reused.

### §3.4 Invariance Condition Semantics

For Condition E: the **absence of semantic divergence under permutation is the PASS condition**.

**Permutation Invariance Criterion**: Outputs from permuted runs must be identical **up to authority-id renaming induced by injection order**. Specifically:

- `scope_atom` fields in conflict and deadlock records must match exactly.
- Admissibility result (`ACTION_ADMISSIBLE` / `ACTION_REFUSED`) must match exactly.
- Admissibility reason must match exactly.
- Deadlock entry (`STATE_DEADLOCK / VALUE_CONFLICT`) must match exactly.
- Conflict records must contain the **same set of `lineage.value_id`** values (order-insensitive). AuthorityID labels may differ between permutations because the sequence counter assigns IDs based on injection order.

Comparison is performed on **`lineage.value_id` sets**, not on raw AuthorityID strings, because AuthorityIDs are implementation artifacts of injection order while `lineage.value_id` is stable across permutations.

If all permutations satisfy this criterion, the condition passes with no kernel failure. If any permutation produces a semantically different outcome, the kernel emits `IX1_FAIL / IMPLICIT_VALUE` and the experiment-level result is FAIL.

---

## §4 Test Vectors

### §4.1 Condition A: Single Value Admissibility

<!-- FROZEN: BEGIN VECTOR_A -->
**Value Declaration**:
```json
{"value_id":"V_OPEN","scope":[{"target":"FILE:/data/report.txt","operation":"READ"}],"commitment":"ALLOW"}
```

**Expected Authority Artifact**:
```json
{"aav":"READ","authority_id":"VEWA-001","commitment":"ALLOW","created_epoch":1738713600,"expiry_epoch":0,"holder":"VALUE_AUTHORITY","lineage":{"encoding_epoch":0,"type":"VALUE_DECLARATION","value_id":"V_OPEN"},"scope":[{"operation":"READ","target":"FILE:/data/report.txt"}],"status":"ACTIVE"}
```

**Candidate Action Request**:
```json
{"target":"FILE:/data/report.txt","operation":"READ"}
```

**Expected Outcome**: `ACTION_ADMISSIBLE`; no conflict; no execution.
<!-- FROZEN: END VECTOR_A -->

### §4.2 Condition B: Multiple Non-Conflicting Values

<!-- FROZEN: BEGIN VECTOR_B -->
**Value Declaration 1**:
```json
{"value_id":"V_READ","scope":[{"target":"FILE:/data/report.txt","operation":"READ"}],"commitment":"ALLOW"}
```

**Value Declaration 2**:
```json
{"value_id":"V_WRITE","scope":[{"target":"FILE:/data/log.txt","operation":"WRITE"}],"commitment":"ALLOW"}
```

**Expected Authority Artifact 1**:
```json
{"aav":"READ","authority_id":"VEWA-001","commitment":"ALLOW","created_epoch":1738713600,"expiry_epoch":0,"holder":"VALUE_AUTHORITY","lineage":{"encoding_epoch":0,"type":"VALUE_DECLARATION","value_id":"V_READ"},"scope":[{"operation":"READ","target":"FILE:/data/report.txt"}],"status":"ACTIVE"}
```

**Expected Authority Artifact 2**:
```json
{"aav":"WRITE","authority_id":"VEWA-002","commitment":"ALLOW","created_epoch":1738713600,"expiry_epoch":0,"holder":"VALUE_AUTHORITY","lineage":{"encoding_epoch":0,"type":"VALUE_DECLARATION","value_id":"V_WRITE"},"scope":[{"operation":"WRITE","target":"FILE:/data/log.txt"}],"status":"ACTIVE"}
```

**Candidate Action Request 1**:
```json
{"target":"FILE:/data/report.txt","operation":"READ"}
```

**Candidate Action Request 2**:
```json
{"target":"FILE:/data/log.txt","operation":"WRITE"}
```

**Expected Outcome**: Both `ACTION_ADMISSIBLE`; no conflict; no aggregation; no execution.
<!-- FROZEN: END VECTOR_B -->

### §4.3 Condition C: Conflicting Values — Deadlock

<!-- FROZEN: BEGIN VECTOR_C -->
**Value Declaration 1** (openness):
```json
{"value_id":"V_OPEN","scope":[{"target":"FILE:/data/secret.txt","operation":"READ"}],"commitment":"ALLOW"}
```

**Value Declaration 2** (confidentiality):
```json
{"value_id":"V_CONF","scope":[{"target":"FILE:/data/secret.txt","operation":"READ"}],"commitment":"DENY"}
```

**Expected Authority Artifact 1**:
```json
{"aav":"READ","authority_id":"VEWA-001","commitment":"ALLOW","created_epoch":1738713600,"expiry_epoch":0,"holder":"VALUE_AUTHORITY","lineage":{"encoding_epoch":0,"type":"VALUE_DECLARATION","value_id":"V_OPEN"},"scope":[{"operation":"READ","target":"FILE:/data/secret.txt"}],"status":"ACTIVE"}
```

**Expected Authority Artifact 2**:
```json
{"aav":"READ","authority_id":"VEWA-002","commitment":"DENY","created_epoch":1738713600,"expiry_epoch":0,"holder":"VALUE_AUTHORITY","lineage":{"encoding_epoch":0,"type":"VALUE_DECLARATION","value_id":"V_CONF"},"scope":[{"operation":"READ","target":"FILE:/data/secret.txt"}],"status":"ACTIVE"}
```

**Expected Conflict Record**:
```json
{"scope_atom":{"target":"FILE:/data/secret.txt","operation":"READ"},"authorities":["VEWA-001","VEWA-002"],"conflict_type":"MULTI_BINDING","registered_epoch":0}
```

**Conflict Type Note**: `conflict_type` is a fixed structural constant (`"MULTI_BINDING"`) denoting that multiple value-derived authorities bind the same scope. It does not encode polarity or any semantic classification of the conflict.

**Candidate Action Request**:
```json
{"target":"FILE:/data/secret.txt","operation":"READ"}
```

**Expected Outcome (injection-time)**: `VALUE_CONFLICT_REGISTERED` — conflict detected and registered at epoch 0 for scope atom `FILE:/data/secret.txt + READ`.
**Expected Outcome (probe-time)**: `ACTION_REFUSED` — candidate action hits conflicted scope; admissibility blocked.
**Expected Outcome (post-probe)**: `STATE_DEADLOCK / VALUE_CONFLICT` — no admissible actions exist for contested scope within harness-provided action set. Conflict persists; no resolution.
<!-- FROZEN: END VECTOR_C -->

### §4.4 Condition D: Aggregation Attempt (Adversarial)

<!-- FROZEN: BEGIN VECTOR_D -->
**Value Declaration 1**:
```json
{"value_id":"V_OPEN","scope":[{"target":"FILE:/data/secret.txt","operation":"READ"}],"commitment":"ALLOW"}
```

**Value Declaration 2**:
```json
{"value_id":"V_CONF","scope":[{"target":"FILE:/data/secret.txt","operation":"READ"}],"commitment":"DENY"}
```

**Fault Injection**: Harness injects `"priority": 1` field on V_OPEN's authority artifact after encoding, creating:
```json
{"aav":"READ","authority_id":"VEWA-001","commitment":"ALLOW","created_epoch":1738713600,"expiry_epoch":0,"holder":"VALUE_AUTHORITY","lineage":{"encoding_epoch":0,"type":"VALUE_DECLARATION","value_id":"V_OPEN"},"priority":1,"scope":[{"operation":"READ","target":"FILE:/data/secret.txt"}],"status":"ACTIVE"}
```

**Expected Outcome**: System detects `priority` field as aggregation attempt → `IX1_FAIL / VALUE_AGGREGATION`. Experiment-level: PASS (adversarial detection successful).
<!-- FROZEN: END VECTOR_D -->

### §4.5 Condition E: Permutation Invariance

<!-- FROZEN: BEGIN VECTOR_E -->
**Value Declaration 1**:
```json
{"value_id":"V_OPEN","scope":[{"target":"FILE:/data/secret.txt","operation":"READ"}],"commitment":"ALLOW"}
```

**Value Declaration 2**:
```json
{"value_id":"V_CONF","scope":[{"target":"FILE:/data/secret.txt","operation":"READ"}],"commitment":"DENY"}
```

**Permutation Schedule**:
- **Run E.1**: Inject V_OPEN first, then V_CONF (authority order: VEWA-001=V_OPEN, VEWA-002=V_CONF).
- **Run E.2**: Inject V_CONF first, then V_OPEN (authority order: VEWA-001=V_CONF, VEWA-002=V_OPEN).

**Candidate Action Request** (same for both runs):
```json
{"target":"FILE:/data/secret.txt","operation":"READ"}
```

**Expected Outcome**: Both runs produce equivalent outputs per the Permutation Invariance Criterion (§3.4):
- Conflict records reference the same `scope_atom` and the same set of `lineage.value_id` values (`{"V_OPEN", "V_CONF"}`), regardless of which AuthorityID label each received.
- Admissibility result: `ACTION_REFUSED` (reason: `VALUE_CONFLICT`) in both runs.
- Deadlock entry: `STATE_DEADLOCK / VALUE_CONFLICT` in both runs.
- AuthorityID labels (VEWA-001, VEWA-002) may map to different value_ids across runs — this is expected and not a divergence.

If any semantic output diverges between E.1 and E.2 (beyond authority-id renaming), classify as `IX1_FAIL / IMPLICIT_VALUE`. Otherwise: PASS (permutation invariance holds).
<!-- FROZEN: END VECTOR_E -->

### §4.6 Condition F: Meta-Authority Synthesis Attempt (Adversarial)

<!-- FROZEN: BEGIN VECTOR_F -->
**Value Declaration 1**:
```json
{"value_id":"V_OPEN","scope":[{"target":"FILE:/data/secret.txt","operation":"READ"}],"commitment":"ALLOW"}
```

**Value Declaration 2**:
```json
{"value_id":"V_CONF","scope":[{"target":"FILE:/data/secret.txt","operation":"READ"}],"commitment":"DENY"}
```

**Fault Injection**: After epoch 0, harness attempts to inject a third "reconciliation" authority:
```json
{"aav":"READ","authority_id":"VEWA-003","commitment":"ALLOW","created_epoch":1738713600,"expiry_epoch":0,"holder":"VALUE_AUTHORITY","lineage":{"encoding_epoch":0,"type":"VALUE_DECLARATION","value_id":"V_META_RESPECT_BOTH"},"scope":[{"operation":"READ","target":"FILE:/data/secret.txt"}],"status":"ACTIVE"}
```

**Expected Outcome**: System detects post-epoch-0 authority creation → `IX1_FAIL / VALUE_SYNTHESIS`. Experiment-level: PASS (adversarial detection successful).
<!-- FROZEN: END VECTOR_F -->

---

## §5 Structural Diff Algorithm

### §5.1 Diff Specification

<!-- FROZEN: BEGIN DIFF_ALGORITHM -->
Inherited from IX-0 with identical semantics:

```python
def structural_diff(artifact_a: dict, artifact_b: dict, path: str = "") -> DiffResult:
    """
    Compute path-level differences between two artifacts.
    Recursively traverses nested dicts and arrays.
    Returns list of (path, value_a, value_b) tuples for differing values.
    """
    diffs = []

    if isinstance(artifact_a, dict) and isinstance(artifact_b, dict):
        all_keys = set(artifact_a.keys()) | set(artifact_b.keys())
        for key in sorted(all_keys):
            new_path = f"{path}.{key}" if path else key
            val_a = artifact_a.get(key, MISSING)
            val_b = artifact_b.get(key, MISSING)
            if val_a == MISSING or val_b == MISSING:
                diffs.append(DiffEntry(path=new_path, left=val_a, right=val_b))
            elif val_a != val_b:
                diffs.extend(structural_diff(val_a, val_b, new_path).entries)

    elif isinstance(artifact_a, list) and isinstance(artifact_b, list):
        max_len = max(len(artifact_a), len(artifact_b))
        for i in range(max_len):
            new_path = f"{path}[{i}]"
            val_a = artifact_a[i] if i < len(artifact_a) else MISSING
            val_b = artifact_b[i] if i < len(artifact_b) else MISSING
            if val_a == MISSING or val_b == MISSING:
                diffs.append(DiffEntry(path=new_path, left=val_a, right=val_b))
            elif val_a != val_b:
                diffs.extend(structural_diff(val_a, val_b, new_path).entries)

    else:
        if artifact_a != artifact_b:
            diffs.append(DiffEntry(path=path, left=artifact_a, right=artifact_b))

    return DiffResult(entries=diffs, count=len(diffs))
```

**Diff Output Format**: Paths use dot notation for object keys and bracket notation for array indices.
**Traversal Order**: Diff entries are emitted in deterministic traversal order (sorted keys, ascending indices).
<!-- FROZEN: END DIFF_ALGORITHM -->

### §5.2 Diff Classification

| Diff Count | Classification |
|------------|----------------|
| 0 | IDENTICAL |
| Extra top-level field present | INJECTION_DETECTED |
| Non-canonical serialization | BIAS_DETECTED |

---

## §6 Execution Protocol

### §6.1 Test Sequence

1. Initialize Value Encoding Harness with fixed clock (`1738713600`) and sequence counter (`001`).
2. For each condition A–F:
   a. Reinitialize the authority system to a clean state (empty authority store, empty conflict store, empty deadlock store).
   b. Load test vector (value declarations, expected artifacts, candidate actions, fault injection config).
   c. If fault injection required (D, F), configure harness accordingly. If permutation test (E), configure permutation schedule.
   d. Encode values: `artifacts = VEH.encode(values)`.
   e. Verify encoding: compare against expected artifacts using structural diff.
   f. Inject artifacts into authority system (AIE, reused from IX-0).
   g. Detect conflicts: register any scope overlaps at injection time.
   h. Probe admissibility: evaluate candidate action requests.
   i. Check for deadlock on contested scopes.
   j. Log result with full artifact capture.
3. Reset fault injection and sequence counter between conditions.
4. Aggregate results.

### §6.2 Determinism Controls

| Control | Value |
|---------|-------|
| Fixed Clock | `1738713600` (2025-02-05 00:00:00 UTC — arbitrary frozen timestamp) |
| Sequence Seed | `001` |
| Sequence Format | `VEWA-<NNN>` (zero-padded) |
| RNG Seed | N/A (no randomness in VEH) |

**Sequence Reset Rule**: The harness resets the VEH sequence counter to `001` before each condition. The VEH must expose a `reset_sequence(value: int)` method.

**Replay Rule**: Given identical value declarations and candidate action requests, all outputs (artifacts, conflict records, admissibility markings, deadlock entries) must be bit-perfectly replayable.

**Namespace Rule**: AuthorityIDs must be unique within a condition run. Cross-condition uniqueness is not required because the authority store is reinitialized per condition (§6.1 step a).

### §6.3 Logging Schema

<!-- FROZEN: BEGIN LOG_SCHEMA -->
```json
{
  "condition": "string (A-F)",
  "timestamp": "ISO-8601",
  "value_declarations": ["array of value declaration objects"],
  "encoded_artifacts": ["array of authority artifact objects"],
  "expected_artifacts": ["array of expected authority artifact objects"],
  "candidate_actions": ["array of candidate action request objects"],
  "fault_injection": "object | null",
  "conflict_records": ["array of conflict record objects"],
  "admissibility_results": [
    {
      "action": "candidate action request object",
      "result": "ACTION_ADMISSIBLE | ACTION_REFUSED",
      "reason": "NO_AUTHORITY | VALUE_CONFLICT | DENIED_BY_AUTHORITY | null"
    }
  ],
  "deadlock_records": [
    {
      "scope_atom": "object",
      "status": "STATE_DEADLOCK / VALUE_CONFLICT"
    }
  ],
  "structural_diffs": ["array of diff results"],
  "classification": "IX1_PASS | IX1_FAIL | INVALID_RUN",
  "classification_reason": "string",
  "experiment_result": "PASS | FAIL",
  "notes": "string"
}
```
<!-- FROZEN: END LOG_SCHEMA -->

---

## §7 Success Criteria

### §7.1 Per-Condition Criteria

| Condition | Success Criterion |
|-----------|-------------------|
| A | Single value encoded bijectively; action admissible; no conflict |
| B | Two values encoded as distinct artifacts; both actions admissible; no conflict; no aggregation |
| C | Conflict registered; action refused; scope-bound deadlock entered; conflict persists |
| D | Aggregation attempt detected; `IX1_FAIL / VALUE_AGGREGATION` emitted |
| E | All permutations produce equivalent outputs per Permutation Invariance Criterion (§3.4); no implicit priority |
| F | Meta-authority synthesis detected; `IX1_FAIL / VALUE_SYNTHESIS` emitted |

### §7.2 Aggregate Success

**Phase IX-1 PASSES if and only if**:
- Conditions A, B, C, E: Classified as PASS (expected behavior observed)
- Conditions D, F: Kernel emits `IX1_FAIL / <reason>` (adversarial detection successful = experiment PASS)

**Aggregate Classification**:
```
IX1_PASS / VALUE_ENCODING_ESTABLISHED
```

**Aggregate Failure**: Any condition producing an unexpected result constitutes phase failure. Failure terminates Phase IX value claims as NEGATIVE RESULT.

### §7.3 Licensed Claim

If Stage IX-1 passes, it licenses **only**:

> *Values can be encoded as explicit authority commitments without aggregation or semantic interpretation.*

It licenses **no claims** about correctness, desirability, coordination, or action.

---

## §8 Architectural Partitioning

### §8.1 Three Physically Distinct Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                      VEWA Harness                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐  │
│  │    Value      │──▶│    Value     │──▶│    Authority       │  │
│  │ Declarations  │   │   Encoding   │   │    Artifacts       │  │
│  │              │   │   Harness    │   │    (AST v0.2)      │  │
│  └──────────────┘   └──────────────┘   └────────────────────┘  │
│                            │                      │             │
│                            ▼                      ▼             │
│                     ┌──────────────┐   ┌────────────────────┐  │
│                     │    Fault     │   │   Admissibility    │  │
│                     │  Injection   │   │   & Conflict       │  │
│                     │  (D, E, F)  │   │   Probe            │  │
│                     └──────────────┘   └────────────────────┘  │
│                                               │                 │
│                                               ▼                 │
│                                        ┌─────────────┐         │
│                                        │   Kernel    │         │
│                                        │  (fixed,    │         │
│                                        │   blind)    │         │
│                                        └─────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

### §8.2 Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `value_encoding.py` | Value → Authority mapping (VEH, pure function) |
| `conflict_probe.py` | Conflict detection, admissibility evaluation, deadlock |
| `vewa_harness.py` | Test orchestration, condition execution, fault injection |
| `canonical.py` | Reuse IX-0 canonical serialization |
| `structural_diff.py` | Reuse IX-0 structural diff |
| `logging.py` | Reuse IX-0 logging, extended with VEWA fields |

### §8.3 Fault Injection Interface

```python
class VEWAFaultConfig:
    inject_priority_field: Optional[Tuple[str, Any]] = None    # Condition D
    permute_injection_order: bool = False                       # Condition E
    inject_post_epoch_authority: Optional[dict] = None          # Condition F
```

---

## §9 Scope and Licensing

### §9.1 What IX-1 Tests
- Whether values can be encoded bijectively as AST v0.2 authority artifacts.
- Whether conflicts persist without resolution.
- Whether implicit priority, aggregation, and synthesis are detectable and rejectable.

### §9.2 What IX-1 Does Not Test
- Value correctness, moral truth, preference learning.
- Negotiation, compromise, coordination.
- Execution semantics, state mutation.
- Multi-agent interaction, governance.

### §9.3 Relationship to IX-0
- IX-1 reuses IX-0's AIE, canonical serialization, diff tooling, logging schema, and replay machinery.
- IX-1's VEH is distinct from IX-0's Translation Layer — different encoding logic, same structural tooling.
- IX-0 tested intent-to-authority (human-facing, ambiguity-prone).
- IX-1 tests value-to-authority (structural, declarative, no interpretation).

---

## §10 Preregistration Commitment

### §10.1 Frozen Sections

The following sections are immutable after hash commitment:
- §2.1 Value Declaration Schema (`VALUE_SCHEMA`)
- §2.2 Authority Artifact Schema (`ARTIFACT_SCHEMA`)
- §2.3 Candidate Action Request Schema (`ACTION_SCHEMA`)
- §2.4 Canonical Serialization Rules (`SERIALIZATION_RULES`)
- §2.5 Value-to-Authority Encoding Rules (`ENCODING_RULES`)
- §2.6 Conflict Definition (`CONFLICT_RULES`)
- §2.7 Admissibility Rules (`ADMISSIBILITY_RULES`)
- §2.8 Output Tokens (`OUTPUT_TOKENS`)
- §3.1 Condition Definitions (`CONDITIONS`)
- §4 Test Vectors (all: `VECTOR_A` through `VECTOR_F`)
- §5.1 Diff Algorithm (`DIFF_ALGORITHM`)
- §6.3 Logging Schema (`LOG_SCHEMA`)

### §10.2 Hash Commitment

**Hash Scope**: SHA-256 of concatenated frozen sections only (content between `<!-- FROZEN: BEGIN -->` and `<!-- FROZEN: END -->` markers). This excludes §10.2 itself, allowing commitment metadata to be recorded without invalidating the hash.

**Verification Command**:
```bash
grep -Pzo '(?s)<!-- FROZEN: BEGIN.*?<!-- FROZEN: END[^>]*>' preregistration.md | sha256sum
```

**Preregistration Hash**: `b61a17cd5bb2614499c71bd3388ba0319cd08331061d3d595c0a2d41c4ea94a0`
**Commitment Timestamp**: `2026-02-05T00:00:00Z`
**Commit ID**: `<USER — set at git commit>`

---

## §11 Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Authority Artifact** | Structured record granting or denying specific capabilities |
| **AAV** | Atomic Authority Verb (READ, WRITE, EXECUTE, DELEGATE, ADMIN) |
| **VEH** | Value Encoding Harness — converts value declarations to authority artifacts |
| **AIE** | Authority Injection Endpoint — injects artifacts into authority system (reused from IX-0) |
| **Commitment** | Binary polarity: ALLOW or DENY |
| **Scope Atom** | Single target + operation pair |
| **Conflict** | Overlapping scope atoms bound by multiple value-derived authorities (excluding ALLOW+ALLOW) |
| **Deadlock** | Scope-bound state where conflict exists and no admissible action is possible |
| **Bijection** | 1:1 mapping — one value declaration produces exactly one authority artifact |
| **Value Preservation** | All value-derived authorities remain present; no collapse or merging |
| **Authority Opacity** | Kernel cannot inspect or interpret value semantics |

### Appendix B: Epoch Reference

| Epoch | ISO-8601 | Use |
|-------|----------|-----|
| 1738713600 | 2025-02-05T00:00:00Z | Fixed clock for all tests (arbitrary frozen timestamp) |
| 0 | N/A | Injection epoch / perpetual expiry sentinel |

### Appendix C: File Manifest

```
src/phase_ix/1-VEWA/
├── docs/
│   ├── spec.md
│   ├── instructions.md
│   ├── questions.md
│   ├── answers.md
│   └── preregistration.md  (this document)
├── src/
│   ├── value_encoding.py
│   ├── conflict_probe.py
│   ├── vewa_harness.py
│   ├── canonical.py          (reused from IX-0)
│   ├── structural_diff.py    (reused from IX-0)
│   └── logging.py            (extended from IX-0)
├── tests/
│   └── test_vewa.py
└── results/
    └── (execution logs)
```

### Appendix D: Preregistration Checklist

| Item | Status |
|------|--------|
| Value declaration grammar | §2.1 |
| Authority encoding mapping | §2.5 |
| Bijection proof for VEH | §2.5 (1:1 invariant) |
| Symmetry proof | §3.1 Condition C (structural symmetry) |
| Scope serialization standard | §2.4 |
| Aggregation detection logic | §3.1 Condition D |
| Synthesis detection logic | §3.1 Condition F |
| Conflict representation check | §2.6 |
| Refusal vs deadlock semantics | §2.7 |
| Scope-bound deadlock persistence | §2.7 |
| Deterministic ordering invariance | §6.2 |
| Logging schema | §6.3 |
| Replay protocol | §6.2 |
| Seeds and initial state hash | §6.2 |

---

**END OF PREREGISTRATION**
