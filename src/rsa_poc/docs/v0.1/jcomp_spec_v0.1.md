
# JCOMP-0.1 — Deterministic Justification Compiler (RSA-PoC v0.1)

## 0. Status

**Normative for RSA-PoC v0.1.**
JCOMP is the **only permitted evaluator** of justification artifacts, and it is strictly syntactic.

---

## 1. Purpose

Given:

* a validated JAF-0.1 artifact, and
* the current environment feasibility information,

produce:

* a compiled constraint object that deterministically forbids actions.

JCOMP must enforce:

* **No inference**
* **No repair**
* **No probabilistic behavior**
* **Non-triviality accounting** (as telemetry)
* **Deterministic output** for identical inputs

---

## 2. Inputs

JCOMP.compile takes:

1. `artifact` (JAF-0.1 JSON object)
2. `action_inventory` (ordered list of all action_ids, size N)
3. `feasible_actions` (set of feasible action_ids in current env state)
4. `policy_scope` (optional enum, default `"V0_1"`)

**Hard rule:** JCOMP must not read any world text, rewards, or hidden state beyond feasibility.

---

## 3. Outputs (Constraint Object Schema)

A JCOMP-0.1 compilation result is:

### 3.1 Success object

```yaml
constraint_version: "JCOMP-0.1"
step: <int>
compile_ok: true
forbidden_action_ids: [<action_id> ...]     # unique, sorted lexicographically
mask: { <action_id>: "ALLOW"|"FORBID" ... } # for all actions in action_inventory
nontrivial_forbidden_action_ids: [<action_id> ...]  # subset that are feasible now
reason_code: <enum>
artifact_digest: <hex string 16..64>
```

### 3.2 Failure object

```yaml
constraint_version: "JCOMP-0.1"
step: <int>
compile_ok: false
error_code: <enum>
error_detail: <short string <= 120 chars>
artifact_digest: <hex string 16..64>
```

---

## 4. Determinism Requirements

### 4.1 No RNG

JCOMP must have **zero RNG** usage.

### 4.2 Stable digest

`artifact_digest` MUST be computed from canonical JSON (sorted keys, UTF-8) via a stable hash (e.g., BLAKE2b-128 or SHA-256 truncated). Must not depend on Python object ordering.

---

## 5. Compilation Algorithm (Normative)

JCOMP performs these steps in order:

### Step 1 — Validate schema

Validate JAF-0.1 exactly per spec.
If invalid → fail with `E_JAF_INVALID` plus specific `error_detail` (but do not infer corrections).

### Step 2 — Validate action ids

* `candidate_action_id` must exist in `action_inventory`. Else fail `E_ACTION_UNKNOWN`.
* If `compiler_hints.forbid_action_ids` contains any id not in inventory → fail `E_ACTION_UNKNOWN`.

### Step 3 — Determine forbidden_action_ids

Compute `F` as follows:

Let `mode = compiler_hints.forbid_mode`.

**Case A: mode == "NONE"**

* `F = ∅`

**Case B: mode == "FORBID_CANDIDATE_ONLY"**

* `F = { candidate_action_id }`

**Case C: mode == "EXPLICIT_LIST"**

* `F = set(forbid_action_ids)` (must be non-empty by schema)

Now apply one additional structural rule:

**Violation-driven enforcement rule**
If `action_claim.relation == "VIOLATES"` then `candidate_action_id` MUST be in `F`.
If not → fail `E_VIOLATION_BUT_NOT_FORBIDDEN`.

Rationale: prevents artifacts claiming “violation” while allowing the violating action.

### Step 4 — Construct mask

For each action in `action_inventory`:

* if action ∈ F → `"FORBID"` else `"ALLOW"`

### Step 5 — Compute nontrivial subset

Let `F* = F ∩ feasible_actions`

Record `F*` as `nontrivial_forbidden_action_ids`.

**Important:** JCOMP does **not** fail compilation when `F*` is empty in v0.1.
It must compile successfully but emit a constraint that will be classified later as decorative unless your runner chooses to gate on non-triviality.

(If you want “no non-trivial constraint ⇒ compile fail,” make that JCOMP-0.2; it’s a semantic change in liveness behavior.)

### Step 6 — Emit success object

Set:

* `reason_code = compiler_hints.constraint_reason_code`

---

## 6. Error Codes (Frozen v0.1)

JCOMP must use one of:

* `E_JAF_INVALID`
* `E_SCHEMA_UNKNOWN_KEY`
* `E_IDENTITY_MISMATCH`
* `E_REF_BAD_ID`
* `E_REF_DUPLICATE_ID`
* `E_REF_TOO_MANY`
* `E_CLAIM_TARGET_REQUIRED`
* `E_CLAIM_TARGET_FORBIDDEN`
* `E_CLAIM_TARGET_NOT_REFERENCED`
* `E_REL_EMPTY`
* `E_REL_NOT_SUBSET`
* `E_REL_DUPLICATE_ID`
* `E_REL_TOO_MANY`
* `E_HINTS_LIST_REQUIRED`
* `E_HINTS_LIST_FORBIDDEN`
* `E_ACTION_UNKNOWN`
* `E_VIOLATION_BUT_NOT_FORBIDDEN`

**No other errors permitted** in v0.1; unexpected exceptions must be caught and mapped to `E_JAF_INVALID` with a short detail.

---

## 7. Non-Semantic Guarantee (Normative)

JCOMP must not:

* parse or interpret `comment`
* use string similarity
* access belief/pref “text” (which JAF doesn’t contain anyway)
* evaluate plausibility of references
* “repair” IDs or missing fields
* consult reward, outcomes, or history

---

## 8. Test Vectors (Required)

### 8.1 Minimal valid VIOLATES artifact (FORBID_CANDIDATE_ONLY)

Should compile with `F={candidate}`.

### 8.2 VIOLATES but forbid list missing candidate

Must fail `E_VIOLATION_BUT_NOT_FORBIDDEN`.

### 8.3 required_belief_ids not subset of belief_ids

Must fail `E_REL_NOT_SUBSET`.

### 8.4 Unknown action id in candidate or forbid list

Must fail `E_ACTION_UNKNOWN`.

### 8.5 Unknown top-level key not namespaced with `x_`

Must fail `E_SCHEMA_UNKNOWN_KEY`.

---

## 9. Compatibility Notes

* JAF-0.1 deliberately keeps semantics minimal and typed.
* JCOMP-0.1 compiles only what it can verify mechanically.
* Any desire for “smarter” compilation is, by definition, out of v0.1 scope.

---
