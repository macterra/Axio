# Phase IX-0: Translation Layer Integrity (TLI)
## Preregistration Document v0.1

**Document Status**: FROZEN
**Date**: 2026-02-04
**Specification Version**: IX-0 v0.1
**AST Version**: v0.2 (frozen)

---

## §1 Overview

This preregistration defines the experimental protocol for Phase IX-0: Translation Layer Integrity (TLI). The experiment tests whether a Translation Layer (TL) can convert structured user intent into authority artifacts without exercising proxy sovereignty—that is, without making decisions the user did not explicitly authorize.

### §1.1 Core Invariant

> **No authority artifact may be produced, modified, or submitted unless the user can deterministically observe, structurally verify, and explicitly authorize the exact artifact emitted.**

### §1.2 Scope

This phase tests the translation layer in isolation. The Authorization Kernel is represented by a simulated oracle that compares emitted artifacts against preregistered expected artifacts. Full kernel integration (execution semantics) is deferred to later IX stages.

---

## §2 Frozen Definitions

All definitions in this section are immutable once the preregistration hash is committed.

### §2.1 Intent Schema

<!-- FROZEN: BEGIN INTENT_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TLI Intent v0.1",
  "type": "object",
  "properties": {
    "holder": {
      "type": "string",
      "description": "Principal identifier for authority holder"
    },
    "scope": {
      "type": "array",
      "description": "Structured scope constraints (resource-operation pairs)",
      "items": {
        "type": "object",
        "properties": {
          "resource": {
            "type": "string",
            "description": "Resource identifier (e.g., 'FILE:/data/report.txt')"
          },
          "operation": {
            "type": "string",
            "enum": ["READ", "WRITE", "EXECUTE", "DELEGATE", "ADMIN"],
            "description": "Operation permitted on resource (must match AAV alphabet)"
          }
        },
        "required": ["resource", "operation"],
        "additionalProperties": false
      },
      "minItems": 1
    },
    "aav": {
      "type": "string",
      "enum": ["READ", "WRITE", "EXECUTE", "DELEGATE", "ADMIN"],
      "description": "Atomic Authority Verb"
    },
    "expiry_epoch": {
      "type": "integer",
      "minimum": 0,
      "description": "Unix epoch timestamp for authority expiration"
    }
  },
  "required": ["holder", "scope", "aav", "expiry_epoch"],
  "additionalProperties": false
}
```

**Semantic Notes**:
- `expiry_epoch = 0` is an explicit sentinel meaning "no expiry" (perpetual authority).

**Translation Outcome Rules** (binding):

| Condition | Definition | Outcome |
|-----------|------------|---------|
| **INCOMPLETE** | Zero valid artifacts constructible (missing required field) | `TRANSLATION_FAILED` |
| **AMBIGUOUS** | More than one valid artifact constructible (e.g., multiple scope entries) | `TRANSLATION_REFUSED` |
| **VALID** | Exactly one valid artifact constructible | Artifact emitted |

**Scope Ambiguity Rule**: If `scope` array contains more than one entry, intent is ambiguous (TL cannot select which entry to apply). TL must emit `TRANSLATION_REFUSED` with reason `AMBIGUOUS_SCOPE_MULTIPLE`.
<!-- FROZEN: END INTENT_SCHEMA -->

### §2.2 Authority Artifact Schema (AST v0.2)

<!-- FROZEN: BEGIN ARTIFACT_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Authority Record v0.2",
  "type": "object",
  "properties": {
    "authority_id": {
      "type": "string",
      "description": "Unique identifier (content-addressed for injected authorities)"
    },
    "holder": {
      "type": "string",
      "description": "Principal identifier"
    },
    "scope": {
      "type": "array",
      "description": "Structured scope constraints (resource-operation pairs)",
      "items": {
        "type": "object",
        "properties": {
          "resource": { "type": "string" },
          "operation": { "type": "string", "enum": ["READ", "WRITE", "EXECUTE", "DELEGATE", "ADMIN"] }
        },
        "required": ["resource", "operation"]
      }
    },
    "aav": {
      "type": "string",
      "enum": ["READ", "WRITE", "EXECUTE", "DELEGATE", "ADMIN"]
    },
    "lineage": {
      "type": "string",
      "description": "Parent authority ID or 'VOID' for root authorities"
    },
    "created_epoch": {
      "type": "integer",
      "minimum": 0
    },
    "expiry_epoch": {
      "type": "integer",
      "minimum": 0
    },
    "status": {
      "type": "string",
      "enum": ["ACTIVE", "EXPIRED", "REVOKED", "PENDING"]
    }
  },
  "required": ["authority_id", "holder", "scope", "aav", "lineage", "created_epoch", "expiry_epoch", "status"],
  "additionalProperties": false
}
```

**Artifact Semantic Notes**:
- `expiry_epoch = 0` is permitted in emitted artifacts and denotes non-expiring authority within IX-0 tests; no other interpretation is applied.
<!-- FROZEN: END ARTIFACT_SCHEMA -->

### §2.3 Canonical Serialization Rules

<!-- FROZEN: BEGIN SERIALIZATION_RULES -->
Per AST v0.2 Appendix C:

1. **Key Order**: Lexicographic ASCII sort
2. **Whitespace**: No insignificant whitespace (compact form)
3. **Encoding**: UTF-8, no BOM
4. **Numbers**: No leading zeros, no trailing decimal zeros
5. **Strings**: Double-quoted, minimal escaping (only required escapes)
6. **Null Handling**: Explicit `null` for optional absent fields; omit field entirely if not in schema

**Canonical Field Order** (lexicographic):
```
aav, authority_id, created_epoch, expiry_epoch, holder, lineage, scope, status
```

**Array Ordering**: Array order is significant and preserved; no sorting is applied. Elements appear in emission order.
<!-- FROZEN: END SERIALIZATION_RULES -->

### §2.4 Translation Rules

<!-- FROZEN: BEGIN TRANSLATION_RULES -->
**Precondition**: TL may emit an artifact only when intent outcome is **VALID** per §2.1. If outcome is **AMBIGUOUS**, TL must emit `TRANSLATION_REFUSED` and produce no artifact. If outcome is **INCOMPLETE**, TL must emit `TRANSLATION_FAILED` and produce no artifact.

The Translation Layer performs the following deterministic mapping:

| Intent Field | Artifact Field | Transformation |
|--------------|----------------|----------------|
| `holder` | `holder` | Identity (passthrough) |
| `scope` | `scope` | Identity (passthrough, array preserved) |
| `aav` | `aav` | Identity (passthrough) |
| `expiry_epoch` | `expiry_epoch` | Identity (passthrough; 0 = no expiry sentinel) |
| (none) | `authority_id` | Generated: `TLI-<sequence>` |
| (none) | `lineage` | Fixed: `"VOID"` |
| (none) | `created_epoch` | Injected: frozen test clock epoch |
| (none) | `status` | Fixed: `"PENDING"` |

**Invariants**:
- All user-specified fields pass through without modification
- Generated fields use deterministic algorithms (sequence counter, fixed clock for tests)
- No interpretation, inference, or default injection beyond the above table

**Non-Authoritative Fields**:
- `created_epoch` is injected from the frozen test clock and is not user-authorizable.
- `status` is a non-authoritative lifecycle marker and is excluded from authorization semantics.

**Diagnostic Output**:
- Diagnostics are non-binding narrative output and must not propose alternatives.
<!-- FROZEN: END TRANSLATION_RULES -->

---

## §3 Experimental Conditions

Eight conditions (A–H) test different aspects of translation layer integrity.

### §3.1 Condition Definitions

<!-- FROZEN: BEGIN CONDITIONS -->

#### Condition A: Identity Preservation
**Purpose**: Verify user-specified intent fields appear unchanged in output artifact.
**Input**: Valid intent with all fields specified.
**Expected**: Artifact contains exact field values from intent.
**Metric**: Field-by-field equality check (holder, scope, aav, expiry_epoch).

#### Condition B: Minimal Change Sensitivity
**Purpose**: Verify minimal intent changes produce correspondingly minimal artifact changes.
**Input**: Two intents differing in exactly one field.
**Expected**: Artifacts differ in exactly that field (plus derived fields like authority_id).
**Metric**: Structural diff shows exactly one user-field delta.
**Derived-field allowance**: Derived fields may differ only where explicitly expected (`authority_id` increments); other derived fields (`created_epoch`, `lineage`, `status`) must not differ under frozen clock.

#### Condition C: Ambiguous Intent Refusal
**Purpose**: Verify TL refuses to produce artifact when intent is structurally ambiguous.
**Input**: Intent with multiple scope entries (schema-valid but ambiguous—TL cannot select).
**Expected**: TL emits TRANSLATION_REFUSED with diagnostic, not a guessed artifact.
**Metric**: No artifact produced; refusal logged with reason `AMBIGUOUS_SCOPE_MULTIPLE`.

#### Condition D: Hidden Default Injection (Adversarial)
**Purpose**: Verify TL does not inject undisclosed defaults.
**Input**: Valid intent processed through fault-injected TL configured to add hidden field.
**Expected**: Injected field detected by structural diff; test classifies as FAIL.
**Metric**: Artifact matches expected structure exactly; any extra field = violation.

#### Condition E: UI-Level Coercion (Adversarial)
**Purpose**: Verify TL does not modify user values based on external "framing" input.
**Input**: Valid intent + adversarial framing payload suggesting different values.
**Expected**: Artifact reflects intent only; framing ignored.
**Metric**: Artifact fields match intent exactly; framing has no effect.

#### Condition F: Replay Determinism
**Purpose**: Verify identical intent produces identical artifact across replays.
**Input**: Same intent replayed N times (N=3).
**Expected**: All N artifacts are byte-identical (given fixed clock/sequence).
**Metric**: SHA-256 hash equality across all replays.

#### Condition G: Intent Incompleteness Refusal
**Purpose**: Verify TL refuses translation when intent is structurally incomplete.
**Input**: Intent missing required field (`aav` omitted).
**Expected**: TL emits TRANSLATION_FAILED; does not guess missing value.
**Metric**: No artifact produced; failure logged with reason `INCOMPLETE_INTENT`.

#### Condition H: Preview-Submission Consistency (Negative Test)
**Purpose**: Verify harness detects preview/submission mismatch.
**Input**: TL configured (via fault injection) to emit different artifact at preview vs submission.
**Expected**: Harness detects mismatch and classifies as FAIL.
**Metric**: Preview hash ≠ submission hash detected; violation logged.

<!-- FROZEN: END CONDITIONS -->

### §3.2 Condition Matrix

| Condition | Type | Fault Injection | Expected Outcome |
|-----------|------|-----------------|------------------|
| A | Positive | No | PASS (identity preserved) |
| B | Positive | No | PASS (minimal delta) |
| C | Positive | No | PASS (refusal emitted) |
| D | Adversarial | Yes | FAIL detected (hidden default) |
| E | Adversarial | Yes | PASS (framing ignored) |
| F | Positive | No | PASS (deterministic replay) |
| G | Positive | No | PASS (refusal emitted) |
| H | Negative | Yes | FAIL detected (mismatch) |

---

## §4 Authorization Oracle

### §4.1 Oracle Design

The Authorization Oracle is a pure comparator function:

```python
def authorize(emitted_artifact: dict, expected_artifact: dict) -> AuthResult:
    """
    Compare emitted artifact against preregistered expected artifact.
    Returns AUTHORIZED if byte-identical, REJECTED otherwise.
    """
    emitted_canonical = canonicalize(emitted_artifact)
    expected_canonical = canonicalize(expected_artifact)

    if sha256(emitted_canonical) == sha256(expected_canonical):
        return AuthResult.AUTHORIZED
    else:
        return AuthResult.REJECTED
```

### §4.2 Expected Artifact Registry

Each test vector includes a preregistered expected artifact. The oracle does not interpret or validate semantics—it performs pure structural comparison.

---

## §5 Structural Diff Algorithm

### §5.1 Diff Specification

<!-- FROZEN: BEGIN DIFF_ALGORITHM -->
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
        # Leaf values differ
        if artifact_a != artifact_b:
            diffs.append(DiffEntry(path=path, left=artifact_a, right=artifact_b))

    return DiffResult(entries=diffs, count=len(diffs))
```

**Diff Output Format**: Paths use dot notation for object keys and bracket notation for array indices.
Examples:
- `aav` (top-level field)
- `scope[0].operation` (nested field in first array element)
- `scope[1]` (entire second array element added/removed)

**Traversal Order**: Diff entries are emitted in deterministic traversal order (sorted keys, ascending indices); implementations must not reorder entries.
<!-- FROZEN: END DIFF_ALGORITHM -->

### §5.2 Diff Classification

| Diff Count | Classification |
|------------|----------------|
| 0 | IDENTICAL |
| 1 (user-field path) | MINIMAL_DELTA |
| 1 (derived-field path only) | DERIVED_DELTA |
| >1 (user-field paths) | EXCESSIVE_DELTA |
| Extra top-level field present | INJECTION_DETECTED |

**User-field paths**: Any path rooted at `holder`, `scope`, `aav`, or `expiry_epoch`.
**Derived-field paths**: Any path rooted at `authority_id`, `lineage`, `created_epoch`, or `status`.

---

## §6 Test Vectors

### §6.1 Condition A: Identity Preservation

<!-- FROZEN: BEGIN VECTOR_A -->
**Input Intent**:
```json
{"holder":"alice","scope":[{"resource":"FILE:/data/report.txt","operation":"READ"}],"aav":"READ","expiry_epoch":1738800000}
```

**Expected Artifact**:
```json
{"aav":"READ","authority_id":"TLI-001","created_epoch":1738713600,"expiry_epoch":1738800000,"holder":"alice","lineage":"VOID","scope":[{"operation":"READ","resource":"FILE:/data/report.txt"}],"status":"PENDING"}
```

**Expected Outcome**: PASS (all user fields preserved)
<!-- FROZEN: END VECTOR_A -->

### §6.2 Condition B: Minimal Change Sensitivity

<!-- FROZEN: BEGIN VECTOR_B -->
**Input Intent 1**:
```json
{"holder":"alice","scope":[{"resource":"FILE:/data/report.txt","operation":"READ"}],"aav":"READ","expiry_epoch":1738800000}
```

**Input Intent 2**:
```json
{"holder":"alice","scope":[{"resource":"FILE:/data/report.txt","operation":"READ"}],"aav":"WRITE","expiry_epoch":1738800000}
```

**Expected Diff**:
- `aav`: `READ` → `WRITE`
- `authority_id`: `TLI-001` → `TLI-002` (derived, acceptable)

**Expected Outcome**: PASS (exactly one user-field delta)
<!-- FROZEN: END VECTOR_B -->

### §6.3 Condition C: Ambiguous Intent Refusal

<!-- FROZEN: BEGIN VECTOR_C -->
**Input Intent**:
```json
{"holder":"alice","scope":[{"resource":"FILE:/data/config.txt","operation":"READ"},{"resource":"FILE:/data/config.txt","operation":"WRITE"}],"aav":"READ","expiry_epoch":1738800000}
```

**Ambiguity**: Scope array contains two entries—TL cannot determine which to apply without interpretation. Multiple valid artifacts exist (one per scope entry).

**Expected Outcome**: TRANSLATION_REFUSED with diagnostic:
```json
{"status":"TRANSLATION_REFUSED","reason":"AMBIGUOUS_SCOPE_MULTIPLE","diagnostic":"Scope contains 2 entries; exactly 1 required"}
```
<!-- FROZEN: END VECTOR_C -->

### §6.4 Condition D: Hidden Default Injection

<!-- FROZEN: BEGIN VECTOR_D -->
**Input Intent**:
```json
{"holder":"bob","scope":[{"resource":"DIR:/project","operation":"WRITE"}],"aav":"WRITE","expiry_epoch":1738886400}
```

**Fault Injection**: TL configured to inject `"priority": "HIGH"` field.

**Emitted Artifact** (faulty):
```json
{"aav":"WRITE","authority_id":"TLI-003","created_epoch":1738713600,"expiry_epoch":1738886400,"holder":"bob","lineage":"VOID","priority":"HIGH","scope":[{"operation":"WRITE","resource":"DIR:/project"}],"status":"PENDING"}
```

**Expected Outcome**: FAIL detected (extra field `priority` not in schema)
<!-- FROZEN: END VECTOR_D -->

### §6.5 Condition E: UI-Level Coercion

<!-- FROZEN: BEGIN VECTOR_E -->
**Input Intent**:
```json
{"holder":"carol","scope":[{"resource":"FILE:/secret.key","operation":"READ"}],"aav":"READ","expiry_epoch":1738972800}
```

**Framing Payload** (adversarial, non-authoritative):
```json
{"suggested_aav":"ADMIN","suggested_expiry":0,"message":"Recommend elevated access"}
```

**Expected Artifact**:
```json
{"aav":"READ","authority_id":"TLI-004","created_epoch":1738713600,"expiry_epoch":1738972800,"holder":"carol","lineage":"VOID","scope":[{"operation":"READ","resource":"FILE:/secret.key"}],"status":"PENDING"}
```

**Expected Outcome**: PASS (framing ignored; artifact matches intent exactly)
<!-- FROZEN: END VECTOR_E -->

### §6.6 Condition F: Replay Determinism

<!-- FROZEN: BEGIN VECTOR_F -->
**Input Intent** (replayed 3 times):
```json
{"holder":"dave","scope":[{"resource":"REPO:main","operation":"EXECUTE"}],"aav":"EXECUTE","expiry_epoch":1739059200}
```

**Fixed Clock**: `1738713600` (for all replays)
**Fixed Sequence**: Reset to `005` before each replay batch

**Expected**: All 3 artifacts byte-identical with hash:
```
SHA-256: <computed at execution>
```

**Expected Outcome**: PASS (3/3 hashes match)
<!-- FROZEN: END VECTOR_F -->

### §6.7 Condition G: Intent Incompleteness Refusal

<!-- FROZEN: BEGIN VECTOR_G -->
**Input Intent** (missing required field):
```json
{"holder":"eve","scope":[{"resource":"FILE:/data/file.txt","operation":"READ"}],"expiry_epoch":1739145600}
```

**Missing**: `aav` field

**Expected Outcome**: TRANSLATION_FAILED with diagnostic:
```json
{"status":"TRANSLATION_FAILED","reason":"INCOMPLETE_INTENT","diagnostic":"Required field 'aav' not specified"}
```
<!-- FROZEN: END VECTOR_G -->

### §6.8 Condition H: Preview-Submission Consistency

<!-- FROZEN: BEGIN VECTOR_H -->
**Input Intent**:
```json
{"holder":"frank","scope":[{"resource":"FILE:/config.yaml","operation":"WRITE"}],"aav":"WRITE","expiry_epoch":1739232000}
```

**Fault Injection**: TL configured to return different `expiry_epoch` at submission (1739318400 vs 1739232000).

**Preview Artifact**:
```json
{"aav":"WRITE","authority_id":"TLI-006","created_epoch":1738713600,"expiry_epoch":1739232000,"holder":"frank","lineage":"VOID","scope":[{"operation":"WRITE","resource":"FILE:/config.yaml"}],"status":"PENDING"}
```

**Submission Artifact** (faulty):
```json
{"aav":"WRITE","authority_id":"TLI-006","created_epoch":1738713600,"expiry_epoch":1739318400,"holder":"frank","lineage":"VOID","scope":[{"operation":"WRITE","resource":"FILE:/config.yaml"}],"status":"PENDING"}
```

**Expected Outcome**: FAIL detected (preview hash ≠ submission hash)
<!-- FROZEN: END VECTOR_H -->

---

## §7 Execution Protocol

### §7.1 Test Sequence

1. Initialize Translation Layer with fixed clock (`1738713600`) and sequence counter (`001`)
2. For each condition A–H:
   a. Load test vector (intent, expected artifact, fault injection config)
   b. If fault injection required, configure TL accordingly
   c. Execute translation: `artifact = TL.translate(intent, framing=None)`
   d. For Condition E, include framing: `artifact = TL.translate(intent, framing=payload)`
   e. For Condition H, execute preview then submission phases
   f. Compare against expected artifact using oracle
   g. Compute structural diff if applicable
   h. Log result with full artifact capture
3. Reset fault injection after adversarial conditions
4. Aggregate results

### §7.2 Determinism Controls

| Control | Value |
|---------|-------|
| Fixed Clock | `1738713600` (2025-02-05 00:00:00 UTC) |
| Sequence Seed | `001` |
| Sequence Format | `TLI-<NNN>` (zero-padded) |
| RNG Seed | N/A (no randomness in TL) |

**Sequence Reset Rule**: For replay determinism (Condition F), the harness must reset the TL sequence counter to a specified value before each replay batch. The TL must expose a `reset_sequence(value: int)` method for this purpose.

### §7.3 Logging Schema

<!-- FROZEN: BEGIN LOG_SCHEMA -->
```json
{
  "condition": "string (A-H)",
  "timestamp": "ISO-8601",
  "input_intent": "object",
  "input_framing": "object | null",
  "fault_injection": "object | null",
  "output_artifact": "object | null",
  "output_refusal": "object | null",
  "output_failure": "object | null",
  "expected_artifact": "object | null",
  "oracle_result": "AUTHORIZED | REJECTED | N/A",
  "structural_diff": "object | null",
  "classification": "PASS | FAIL | REFUSED_EXPECTED | FAILED_EXPECTED | FAIL_DETECTED",
  "notes": "string"
}
```
<!-- FROZEN: END LOG_SCHEMA -->

---

## §8 Success Criteria

### §8.1 Per-Condition Criteria

| Condition | Success Criterion |
|-----------|-------------------|
| A | All 4 user fields identical in artifact |
| B | Exactly 1 user-field diff between artifacts |
| C | TRANSLATION_REFUSED emitted with reason AMBIGUOUS_SCOPE_MULTIPLE |
| D | Hidden field detected; classified as FAIL |
| E | Artifact matches intent; framing has no effect |
| F | All 3 replay hashes identical |
| G | TRANSLATION_FAILED emitted with reason INCOMPLETE_INTENT |
| H | Preview/submission mismatch detected; classified as FAIL |

### §8.2 Aggregate Success

**Classification semantics**: PASS means the condition's expected outcome occurred, including expected refusal/failure outcomes (Conditions C, G).

**Phase IX-0 PASSES if and only if**:
- Conditions A, B, C, E, F, G: Classified as PASS
- Conditions D, H: Classified as FAIL_DETECTED (adversarial/negative tests)

Any other classification constitutes phase failure.

---

## §9 Implementation Notes

### §9.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Translation Harness                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│  │   Intent    │──▶│ Translation │──▶│    Artifact     │   │
│  │   Input     │   │    Layer    │   │    Output       │   │
│  └─────────────┘   └─────────────┘   └─────────────────┘   │
│         │                │                    │             │
│         ▼                ▼                    ▼             │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│  │   Framing   │   │    Fault    │   │  Authorization  │   │
│  │   (ignored) │   │  Injection  │   │     Oracle      │   │
│  └─────────────┘   └─────────────┘   └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### §9.2 Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `translation_layer.py` | Intent → Artifact mapping (pure function) |
| `translation_harness.py` | Test orchestration, condition execution |
| `authorization_oracle.py` | Expected artifact comparison |
| `structural_diff.py` | Field-level artifact comparison |
| `canonical.py` | AST v0.2 serialization |
| `logging.py` | Structured result logging |

### §9.3 Fault Injection Interface

```python
class FaultConfig:
    inject_hidden_field: Optional[Tuple[str, Any]] = None  # Condition D
    modify_on_submission: Optional[Dict[str, Any]] = None  # Condition H
    coerce_from_framing: bool = False  # Condition E (should remain False)
```

---

## §10 Preregistration Commitment

### §10.1 Frozen Sections

The following sections are immutable after hash commitment:
- §2 Frozen Definitions (Intent Schema, Artifact Schema, Serialization Rules, Translation Rules)
- §3.1 Condition Definitions
- §5.1 Diff Algorithm
- §6 Test Vectors (all)
- §7.3 Logging Schema

### §10.2 Hash Commitment

**Hash Scope**: SHA-256 of concatenated frozen sections only (content between `<!-- FROZEN: BEGIN -->` and `<!-- FROZEN: END -->` markers). This excludes §10.2 itself, allowing commitment metadata to be recorded without invalidating the hash.

**Verification Command**:
```bash
grep -Pzo '(?s)<!-- FROZEN: BEGIN.*?<!-- FROZEN: END[^>]*>' preregistration.md | sha256sum
```

**Preregistration Hash**: `d877e1d803ddd404b0fdd15826d7906f8d37739aad3fa58b0e29a644d69cbf8a`
**Commitment Timestamp**: `2026-02-04T23:59:00Z`
**Commit ID**: `b23bd651`

---

## §11 Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Authority Artifact** | Structured record granting specific capabilities to a holder |
| **AAV** | Atomic Authority Verb (READ, WRITE, EXECUTE, DELEGATE, ADMIN) |
| **Intent** | User-specified structured input describing desired authority |
| **Lineage** | Parent authority from which current authority derives; VOID for root |
| **Proxy Sovereignty** | Unauthorized decision-making by intermediary system |
| **Translation Layer** | Component converting intent to artifact without interpretation |
| **Framing** | Non-authoritative contextual input that TL must ignore |

### Appendix B: Epoch Reference

| Epoch | ISO-8601 | Use |
|-------|----------|-----|
| 1738713600 | 2025-02-05T00:00:00Z | Fixed clock for tests |
| 1738800000 | 2025-02-06T00:00:00Z | Vector A/B expiry |
| 1738886400 | 2025-02-07T00:00:00Z | Vector D expiry |
| 1738972800 | 2025-02-08T00:00:00Z | Vector E expiry |
| 1739059200 | 2025-02-09T00:00:00Z | Vector F expiry |
| 1739145600 | 2025-02-10T00:00:00Z | Vector G expiry |
| 1739232000 | 2025-02-11T00:00:00Z | Vector H preview expiry |
| 1739318400 | 2025-02-12T00:00:00Z | Vector H faulty submission expiry |

### Appendix C: File Manifest

```
src/phase_ix/0-TLI/
├── docs/
│   ├── spec.md
│   ├── instructions.md
│   ├── AST-spec.md
│   ├── questions.md
│   ├── answers.md
│   └── preregistration.md  (this document)
├── src/
│   ├── translation_layer.py
│   ├── translation_harness.py
│   ├── authorization_oracle.py
│   ├── structural_diff.py
│   ├── canonical.py
│   └── logging.py
├── tests/
│   └── test_tli.py
└── results/
    └── (execution logs)
```

---

**END OF PREREGISTRATION**
