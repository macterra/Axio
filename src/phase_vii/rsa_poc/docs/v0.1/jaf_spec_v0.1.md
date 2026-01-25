# JAF-0.1 — Justification Artifact Format (RSA-PoC v0.1)

## 0. Status

**Normative for RSA-PoC v0.1.**
Any deviation is **scope exit** unless explicitly version-bumped.

---

## 1. Purpose

JAF-0.1 defines the **only admissible semantic container** for RSA-PoC v0.1.
Its role is to express, as a **typed record**, the minimal inputs required for deterministic compilation into a formal action constraint.

**Non-goal:** persuasion, explanation quality, moral evaluation, semantic parsing.

---

## 2. Encoding and Canonicalization

### 2.1 Encoding

Artifacts MUST be representable as:

* JSON object (preferred on disk / logs), or
* a Python dataclass serialized to JSON without loss.

### 2.2 Canonical form

For hashing/deduplication and determinism:

* Canonical JSON MUST use UTF-8, no NaNs, no floats.
* Object keys MUST be lexicographically sorted during canonicalization.
* Arrays MUST preserve order as provided (order is semantically relevant where stated).

---

## 3. Required Fields (Top-Level Schema)

A JAF-0.1 artifact is a JSON object with exactly these required top-level keys:

* `artifact_version` (string, MUST equal `"JAF-0.1"`)
* `step` (int, ≥ 0)
* `identity` (object)
* `references` (object)
* `action_claim` (object)
* `relevance` (object)
* `compiler_hints` (object)
* `nonce` (string)

Optional:

* `comment` (string) — **ignored** by JCOMP and ActionSelector.

### 3.1 Strict key discipline

* Unknown top-level keys are **allowed only if** they are namespaced under `x_` prefix (e.g. `x_debug`) and MUST be ignored by JCOMP.
* Unknown keys *outside* `x_` namespace → **compile error** `E_SCHEMA_UNKNOWN_KEY`.

Rationale: allow debugging without opening semantic leakage.

---

## 4. Subschemas

## 4.1 `identity`

Object with required keys:

* `agent_id` (string, non-empty, max 64 chars)
* `continuity_counter` (int, ≥ 0)

Normative rule:

* `continuity_counter` MUST equal `step` for v0.1.
  Otherwise compile error `E_IDENTITY_MISMATCH`.

(If you later want episode-local step counters, that’s a version bump.)

---

## 4.2 `references`

Object with required keys:

* `belief_ids` (array of strings, length ≥ 1)
* `pref_ids` (array of strings, length ≥ 1)

Constraints:

* Every id MUST match regex: `^[A-Z][A-Z0-9_]{0,31}$`

  * examples: `B1`, `B_DOOR_A_LOCKED`, `P_NO_BREAK_LOCKS`
* Arrays MUST have unique elements (no duplicates).
* Max lengths: `belief_ids` ≤ 16, `pref_ids` ≤ 16.
  Violations → `E_REF_BAD_ID` / `E_REF_DUPLICATE_ID` / `E_REF_TOO_MANY`.

---

## 4.3 `action_claim`

Object with required keys:

* `candidate_action_id` (string, non-empty, max 64 chars)
* `relation` (string enum)
* `target_pref_id` (string or null)
* `expected_constraint_effect` (string enum)

Enums:

`relation ∈ { "SATISFIES", "VIOLATES", "IRRELEVANT" }`

`expected_constraint_effect ∈ { "FORBID_CANDIDATE", "FORBID_ALTERNATIVES", "NO_CONSTRAINT" }`

Rules:

* If `relation == "VIOLATES"`, then `target_pref_id` MUST be non-null and MUST appear in `references.pref_ids`.
* If `relation != "VIOLATES"`, then `target_pref_id` MUST be null.
  Violations → `E_CLAIM_TARGET_REQUIRED` / `E_CLAIM_TARGET_FORBIDDEN` / `E_CLAIM_TARGET_NOT_REFERENCED`.

Purpose of `expected_constraint_effect`: lets you later audit “predictive” justifications without semantics; in v0.1 it is logged, not used for gating.

---

## 4.4 `relevance`

Object with required keys:

* `required_belief_ids` (array of strings, length ≥ 1)

Rules:

* `required_belief_ids` MUST be a subset of `references.belief_ids`.
* Unique elements, max length 16.
  Violations → `E_REL_EMPTY` / `E_REL_NOT_SUBSET` / `E_REL_DUPLICATE_ID` / `E_REL_TOO_MANY`.

---

## 4.5 `compiler_hints`

Object with required keys:

* `forbid_action_ids` (array of strings, length ≥ 0, max 16)
* `forbid_mode` (string enum)
* `constraint_reason_code` (string enum)

Enums:

`forbid_mode ∈ { "EXPLICIT_LIST", "FORBID_CANDIDATE_ONLY", "NONE" }`

`constraint_reason_code ∈ { "R_PREF_VIOLATION", "R_POLICY_GUARD", "R_RELEVANCE_BINDING" }`

Rules:

* If `forbid_mode == "EXPLICIT_LIST"`, then `forbid_action_ids` MUST be non-empty.
* If `forbid_mode != "EXPLICIT_LIST"`, then `forbid_action_ids` MUST be empty.
  Violations → `E_HINTS_LIST_REQUIRED` / `E_HINTS_LIST_FORBIDDEN`.

**Important:** JCOMP may reject hints that don’t match structural rules; hints are not authoritative.

---

## 4.6 `nonce`

* string, non-empty, max 64 chars
* MUST match regex `^[a-zA-Z0-9._-]{1,64}$`

Purpose: prevents accidental artifact de-dup collapsing distinct attempts in logs.
JCOMP must ignore it except for schema validation.

---

## 5. JAF Validity Summary (Hard Requirements)

A JAF-0.1 artifact is **valid** iff all hold:

1. `artifact_version == "JAF-0.1"`
2. `continuity_counter == step`
3. all IDs match regex and are unique
4. required belief ids subset of referenced belief ids
5. target preference rules satisfied
6. compiler_hints consistency rules satisfied
7. no unknown non-`x_` keys

---

## 6. Prohibited Semantics Leakage (Normative)

* No free-text fields besides `comment` and `nonce`.
* Any additional semantic content must go under `x_...` and will be ignored by JCOMP and selector.

---
