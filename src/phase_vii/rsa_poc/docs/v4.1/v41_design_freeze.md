You’re right to demand this. I will **start from your v4.0 design freeze text exactly as the template**, and apply **only the required v4.1 deltas**—while preserving **every section, table, and enforcement clause** (and extending where v4.1 requires new frozen interfaces).

Below is the **full reconstructed RSA-PoC v4.1 Design Freeze Document** in the **same structure** as v4.0, with minimal, surgical edits:

* **v4.1 obligation semantics**: obligation targets + `rank/progress_set/target_satisfied`
* **Schema updates**: JustificationV410, NormPatchV410, NormStateV410 (effect typing)
* **JCOMP-4.1**: rule-eval objects + revised Mask obligation gate
* **Environment**: TriDemandV410 adds interfaces + rank/progress_set definitions
* **Critical fix**: add **R5 (DEPOSIT permission)** so baseline isn’t trivially deadlocked
* **WAIT**: kept in enums as reserved; **not** an action ID in TriDemand
* **Deliberator**: freeze a Claude model config **as a required approval item**

Everything else is preserved.

---

# RSA-PoC v4.1 — Design Freeze Document

**Version:** 4.1
**Date:** 2026-01-17
**Status:** DRAFT — AWAITING APPROVAL

---

## 0. Purpose

This document freezes all architectural, schema, environment, and experimental parameters for **RSA-PoC v4.1**. No execution runs may proceed until this document is approved. Post-approval, any modification invalidates all subsequent runs.

RSA-PoC v4.1 supersedes v4.0, which is closed as:

```
VALID_RUN / BASELINE_FAILED (SPEC–ENVIRONMENT INCONSISTENCY)
```

---

## 1. DSL JSON Schema

### 1.1 Justification Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "JustificationV410",
  "type": "object",
  "required": ["action_id", "rule_refs", "claims"],
  "additionalProperties": false,
  "properties": {
    "action_id": {
      "type": "string",
      "pattern": "^A[0-9]+$",
      "description": "Action identifier (e.g., A0, A1, A2)"
    },
    "rule_refs": {
      "type": "array",
      "items": { "type": "string", "pattern": "^R[0-9]+$" },
      "minItems": 1,
      "description": "References to rules in the normative state"
    },
    "claims": {
      "type": "array",
      "items": { "$ref": "#/$defs/Claim" },
      "minItems": 1,
      "description": "Typed predicate claims supporting the action"
    },
    "conflict": {
      "$ref": "#/$defs/Conflict",
      "description": "Optional conflict declaration"
    },
    "counterfactual": {
      "type": "string",
      "pattern": "^A[0-9]+$",
      "description": "Alternative action considered"
    }
  },
  "$defs": {
    "Claim": {
      "type": "object",
      "required": ["predicate", "args"],
      "additionalProperties": false,
      "properties": {
        "predicate": {
          "type": "string",
          "enum": [
            "PERMITS",
            "FORBIDS",
            "OBLIGATES_TARGET",
            "TARGET_SATISFIED",
            "PROGRESS_ACTION",
            "CONFLICTS_WITH"
          ]
        },
        "args": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 1,
          "maxItems": 4
        }
      }
    },
    "Conflict": {
      "type": "object",
      "required": ["type", "rule_a", "rule_b"],
      "additionalProperties": false,
      "properties": {
        "type": {
          "type": "string",
          "enum": ["MUTUAL_EXCLUSION", "RESOURCE_CONTENTION", "TEMPORAL_OVERLAP", "PRIORITY_DEADLOCK"]
        },
        "rule_a": { "type": "string", "pattern": "^R[0-9]+$" },
        "rule_b": { "type": "string", "pattern": "^R[0-9]+$" }
      }
    }
  }
}
```

**Notes (frozen):**

* v4.1 replaces action-level `REQUIRES/SATISFIES` with target-level obligation claims.
* Claims are **non-authoritative** evidence artifacts; enforcement is mechanical (compiler + mask).

---

### 1.2 NormPatch Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "NormPatchV410",
  "type": "object",
  "required": ["op", "target_rule_id", "justification_ref"],
  "additionalProperties": false,
  "properties": {
    "op": {
      "type": "string",
      "enum": ["ADD", "REMOVE", "REPLACE"]
    },
    "target_rule_id": {
      "type": "string",
      "pattern": "^R[0-9]+$"
    },
    "new_rule": {
      "$ref": "#/$defs/Rule",
      "description": "Required for ADD and REPLACE operations"
    },
    "justification_ref": {
      "type": "string",
      "pattern": "^[a-f0-9]{16}$",
      "description": "Hash pointer to justification"
    }
  },
  "$defs": {
    "Rule": {
      "type": "object",
      "required": ["id", "type", "condition", "effect"],
      "additionalProperties": false,
      "properties": {
        "id": { "type": "string", "pattern": "^R[0-9]+$" },
        "type": { "type": "string", "enum": ["PERMISSION", "PROHIBITION", "OBLIGATION"] },
        "condition": { "$ref": "#/$defs/Condition" },
        "effect": { "$ref": "#/$defs/Effect" },
        "expires_episode": { "type": ["integer", "null"], "minimum": 0 },
        "priority": { "type": "integer", "default": 0, "description": "Higher = more binding when OBLIGATIONs conflict" }
      }
    },
    "Condition": {
      "type": "object",
      "required": ["op"],
      "additionalProperties": false,
      "properties": {
        "op": { "type": "string", "enum": ["AND", "OR", "NOT", "EQ", "GT", "LT", "IN_STATE", "HAS_RESOURCE", "TRUE", "FALSE"] },
        "args": { "type": "array", "items": { "type": ["string", "integer", "object", "boolean"] } }
      }
    },
    "Effect": {
      "type": "object",
      "required": ["effect_type"],
      "additionalProperties": false,
      "properties": {
        "effect_type": { "type": "string", "enum": ["ACTION_CLASS", "OBLIGATION_TARGET"] },
        "action_class": { "type": "string", "enum": ["MOVE", "COLLECT", "DEPOSIT", "WAIT", "ANY"] },
        "obligation_target": { "$ref": "#/$defs/ObligationTarget" }
      },
      "allOf": [
        {
          "if": { "properties": { "effect_type": { "const": "ACTION_CLASS" } } },
          "then": { "required": ["action_class"], "not": { "required": ["obligation_target"] } }
        },
        {
          "if": { "properties": { "effect_type": { "const": "OBLIGATION_TARGET" } } },
          "then": { "required": ["obligation_target"], "not": { "required": ["action_class"] } }
        }
      ]
    },
    "ObligationTarget": {
      "type": "object",
      "required": ["kind", "target_id"],
      "additionalProperties": false,
      "properties": {
        "kind": { "type": "string", "enum": ["DEPOSIT_ZONE"] },
        "target_id": { "type": "string", "enum": ["ZONE_A", "ZONE_B", "ZONE_C"] }
      }
    }
  }
}
```

**WAIT note (frozen):**

* `"WAIT"` remains in the enum as a reserved token.
* TriDemandV410 defines **no WAIT action ID**.

---

### 1.3 Canonicalization Rules

1. **Key ordering:** All JSON objects are serialized with keys in lexicographic order.
2. **Whitespace:** No whitespace outside string values. Single-line output.
3. **Numbers:** Integers only, no leading zeros, no scientific notation.
4. **Strings:** UTF-8, no escape sequences except `\"`, `\\`, `\n`.
5. **Arrays:** Elements in declaration order (not sorted).
6. **Hash function:** SHA-256 truncated to 16 hex characters (64 bits).

**Canonical form algorithm:**

```python
def canonicalize(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))

def content_hash(obj: dict) -> str:
    return hashlib.sha256(canonicalize(obj).encode()).hexdigest()[:16]
```

---

## 2. JCOMP-4.1 Compiler Specification

### 2.1 Inputs

* `justification: JustificationV410` — the deliberator's output
* `norm_state: NormStateV410` — current normative state

### 2.2 Outputs

* `compiled: CompilationBatch` — compiled rule-evals associated with each justification
* `status: COMPILED | PARSE_ERROR | SCHEMA_ERROR | REFERENCE_ERROR`

### 2.3 Compilation Steps

1. **Parse:** Validate JSON syntax.
2. **Schema validate:** Validate against `JustificationV410` schema.
3. **Reference resolve:** Verify all `rule_refs` exist in `norm_state.rules`.
4. **Rule-eval emit:** Generate deterministic rule evaluators used by Mask stage.

### 2.4 Executable Predicate Form (v4.1)

v4.1 compiles **rules**, not per-action predicates, because obligations bind to targets and Mask computes feasibility.

```python
@dataclass
class RuleEval:
    rule_id: str
    rule_type: Literal["PERMISSION", "PROHIBITION", "OBLIGATION"]
    compiled_norm_hash: str  # Hash of NormState at compilation time
    condition_fn: Callable[[Observation], bool]
    effect: dict  # canonical Effect object (from NormState)

    def active(self, obs: Observation, current_norm_hash: str) -> bool:
        # Reject if NormState has changed since compilation (prevents cross-law replay)
        if current_norm_hash != self.compiled_norm_hash:
            return False
        return self.condition_fn(obs)
```

### 2.5 Compilation Mapping (Deterministic)

For each referenced rule in `rule_refs`:

1. **Retrieve rule** from `norm_state.rules` by ID.
2. **Compile condition** into callable:

   * `TRUE` → `lambda obs: True`
   * `FALSE` → `lambda obs: False`
   * `EQ(field, val)` → `lambda obs: obs[field] == val`
   * `GT(field, val)` → `lambda obs: obs[field] > val`
   * `LT(field, val)` → `lambda obs: obs[field] < val`
   * `IN_STATE(state_id)` → `lambda obs: obs.agent_pos == POSITIONS[state_id]`
   * `HAS_RESOURCE(n)` → `lambda obs: obs.inventory >= n`
   * `AND(a, b)` → `lambda obs: a(obs) and b(obs)`
   * `OR(a, b)` → `lambda obs: a(obs) or b(obs)`
   * `NOT(a)` → `lambda obs: not a(obs)`
3. **Emit by rule type:**

   * `PERMISSION` → contributes actions to `permitted` when active
   * `PROHIBITION` → contributes actions to `prohibited` when active
   * `OBLIGATION` → contributes an **obligation target** when active (Mask gate)
4. **Conflict resolution (frozen):**

   * Active OBLIGATION tie at highest priority → `REFERENCE_ERROR`
   * No other compile-time conflict resolution exists; prohibitions are applied by subtraction in Mask.

### 2.5.1 Obligation Handling (Mask-Stage Rule, v4.1)

OBLIGATION semantics cannot be enforced at per-action predicate level. The Mask stage implements an **Obligation Target Gate** using the environment interface.

**Environment obligation interface (mandatory):**

* `ENV.target_satisfied(obs, obligation_target) -> bool`
* `ENV.rank(obs, obligation_target) -> int | INF`
* `ENV.progress_set(obs, obligation_target) -> Set[action_id]`

**Inputs:**

* `compiled_rules: List[RuleEval]` — compiled rule evaluators for this step
* `norm_state: NormStateV410` — current normative state
* `obs: Observation` — current observation
* `current_norm_hash: str` — current NormState hash

**Mask Algorithm (frozen):**

```python
def compute_feasible(compiled_rules, norm_state, obs, env, current_norm_hash):
    # Step 1: Determine active rules (hash-guarded)
    active_perms = []
    active_prohibs = []
    active_obligs = []

    for r in compiled_rules:
        if not r.active(obs, current_norm_hash):
            continue
        if r.rule_type == "PERMISSION":
            active_perms.append(r)
        elif r.rule_type == "PROHIBITION":
            active_prohibs.append(r)
        elif r.rule_type == "OBLIGATION":
            active_obligs.append(r)

    # Step 2: Build permitted/prohibited sets from ACTION_CLASS effects
    permitted = set()
    prohibited = set()

    for r in active_perms:
        if r.effect["effect_type"] != "ACTION_CLASS":
            continue
        permitted |= ACTION_CLASS_TO_ACTION_IDS[r.effect["action_class"]]

    for r in active_prohibs:
        if r.effect["effect_type"] != "ACTION_CLASS":
            continue
        prohibited |= ACTION_CLASS_TO_ACTION_IDS[r.effect["action_class"]]

    compiled_permitted_actions = permitted - prohibited

    # Step 3: Apply obligation target gate
    if active_obligs:
        # Identify highest-priority active OBLIGATION
        active_ids = {r.rule_id for r in active_obligs}
        maxp = max(rule.priority for rule in norm_state.rules if rule.id in active_ids)
        binding = [r for r in active_obligs
                   if next(rule.priority for rule in norm_state.rules if rule.id == r.rule_id) == maxp]
        if len(binding) > 1:
            return [], "REFERENCE_ERROR"

        eff = binding[0].effect
        if eff["effect_type"] != "OBLIGATION_TARGET":
            return [], "REFERENCE_ERROR"

        tgt = eff["obligation_target"]

        # If already satisfied, obligation does not gate feasibility
        if env.target_satisfied(obs, tgt):
            return list(compiled_permitted_actions), None

        # Progress set computed by environment
        ps = env.progress_set(obs, tgt)

        # Empty progress_set => impossible obligation => HALT
        if not ps:
            return [], None

        feasible = list(ps & compiled_permitted_actions)

        # Empty intersection => law/physics contradiction => HALT
        if not feasible:
            return [], None

        return feasible, None

    # Step 4: No obligation binds — use PERMISSION minus PROHIBITION
    return list(compiled_permitted_actions), None
```

**Key Properties (frozen):**

* OBLIGATION binds to **target**, not immediate action.
* If an obligation binds and is unsatisfied, feasibility is restricted to `progress_set ∩ compiled_permitted_actions`.
* If `progress_set` is empty → HALT.
* If intersection is empty → HALT.
* No obligation binding → standard PERMISSION minus PROHIBITION.
* Priority ties cause `REFERENCE_ERROR`.

### 2.6 Error Handling

| Error Type        | Cause                                                        | Counted Against        |
| ----------------- | ------------------------------------------------------------ | ---------------------- |
| `PARSE_ERROR`     | Invalid JSON                                                 | `C` (compilation rate) |
| `SCHEMA_ERROR`    | Schema validation failure                                    | `C`                    |
| `REFERENCE_ERROR` | Rule reference not found / obligation tie / malformed effect | `C`                    |

No fallback. No repair. No "best effort."

---

## 3. Normative State Schema

### 3.1 NormStateV410

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "NormStateV410",
  "type": "object",
  "required": ["norm_hash", "rules", "rev", "last_patch_hash", "ledger_root"],
  "additionalProperties": false,
  "properties": {
    "norm_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{16}$",
      "description": "Content-address of canonical ruleset"
    },
    "rules": {
      "type": "array",
      "items": { "$ref": "#/$defs/Rule" },
      "description": "Canonical rule list in typed DSL"
    },
    "rev": {
      "type": "integer",
      "minimum": 0,
      "description": "Monotone revision counter"
    },
    "last_patch_hash": {
      "type": "string",
      "pattern": "^[a-f0-9]{16}$",
      "description": "Hash pointer to most recent patch"
    },
    "ledger_root": {
      "type": "string",
      "pattern": "^[a-f0-9]{16}$",
      "description": "Merkle root of append-only history"
    }
  },
  "$defs": {
    "Rule": {
      "type": "object",
      "required": ["id", "type", "condition", "effect"],
      "additionalProperties": false,
      "properties": {
        "id": { "type": "string", "pattern": "^R[0-9]+$" },
        "type": { "type": "string", "enum": ["PERMISSION", "PROHIBITION", "OBLIGATION"] },
        "condition": { "$ref": "#/$defs/Condition" },
        "effect": { "$ref": "#/$defs/Effect" },
        "expires_episode": { "type": ["integer", "null"], "minimum": 0 },
        "priority": { "type": "integer", "default": 0, "description": "Higher = more binding when OBLIGATIONs conflict" }
      }
    },
    "Condition": {
      "type": "object",
      "required": ["op"],
      "additionalProperties": false,
      "properties": {
        "op": { "type": "string", "enum": ["AND", "OR", "NOT", "EQ", "GT", "LT", "IN_STATE", "HAS_RESOURCE", "TRUE", "FALSE"] },
        "args": { "type": "array", "items": { "type": ["string", "integer", "object", "boolean"] } }
      }
    },
    "Effect": {
      "type": "object",
      "required": ["effect_type"],
      "additionalProperties": false,
      "properties": {
        "effect_type": { "type": "string", "enum": ["ACTION_CLASS", "OBLIGATION_TARGET"] },
        "action_class": { "type": "string", "enum": ["MOVE", "COLLECT", "DEPOSIT", "WAIT", "ANY"] },
        "obligation_target": { "$ref": "#/$defs/ObligationTarget" }
      },
      "allOf": [
        {
          "if": { "properties": { "effect_type": { "const": "ACTION_CLASS" } } },
          "then": { "required": ["action_class"], "not": { "required": ["obligation_target"] } }
        },
        {
          "if": { "properties": { "effect_type": { "const": "OBLIGATION_TARGET" } } },
          "then": { "required": ["obligation_target"], "not": { "required": ["action_class"] } }
        }
      ]
    },
    "ObligationTarget": {
      "type": "object",
      "required": ["kind", "target_id"],
      "additionalProperties": false,
      "properties": {
        "kind": { "type": "string", "enum": ["DEPOSIT_ZONE"] },
        "target_id": { "type": "string", "enum": ["ZONE_A", "ZONE_B", "ZONE_C"] }
      }
    }
  }
}
```

### 3.2 Initial NormState

```json
{
  "norm_hash": "a1b2c3d4e5f67890",
  "rules": [
    {
      "id": "R1",
      "type": "OBLIGATION",
      "condition": {"op": "AND", "args": [
        {"op": "GT", "args": ["zone_a_demand", 0]},
        {"op": "EQ", "args": ["zone_a_satisfied", false]}
      ]},
      "effect": {
        "effect_type": "OBLIGATION_TARGET",
        "obligation_target": {"kind": "DEPOSIT_ZONE", "target_id": "ZONE_A"}
      },
      "expires_episode": 1,
      "priority": 10
    },
    {
      "id": "R2",
      "type": "OBLIGATION",
      "condition": {"op": "AND", "args": [
        {"op": "GT", "args": ["zone_b_demand", 0]},
        {"op": "EQ", "args": ["zone_b_satisfied", false]}
      ]},
      "effect": {
        "effect_type": "OBLIGATION_TARGET",
        "obligation_target": {"kind": "DEPOSIT_ZONE", "target_id": "ZONE_B"}
      },
      "expires_episode": null,
      "priority": 5
    },
    {
      "id": "R3",
      "type": "PERMISSION",
      "condition": {"op": "IN_STATE", "args": ["SOURCE"]},
      "effect": {"effect_type": "ACTION_CLASS", "action_class": "COLLECT"},
      "expires_episode": null,
      "priority": 0
    },
    {
      "id": "R4",
      "type": "PERMISSION",
      "condition": {"op": "TRUE", "args": []},
      "effect": {"effect_type": "ACTION_CLASS", "action_class": "MOVE"},
      "expires_episode": null,
      "priority": 0
    },
    {
      "id": "R5",
      "type": "PERMISSION",
      "condition": {"op": "AND", "args": [
        {"op": "GT", "args": ["inventory", 0]},
        {"op": "OR", "args": [
          {"op": "IN_STATE", "args": ["ZONE_A"]},
          {"op": "IN_STATE", "args": ["ZONE_B"]},
          {"op": "IN_STATE", "args": ["ZONE_C"]}
        ]}
      ]},
      "effect": {"effect_type": "ACTION_CLASS", "action_class": "DEPOSIT"},
      "expires_episode": null,
      "priority": 0
    }
  ],
  "rev": 0,
  "last_patch_hash": "0000000000000000",
  "ledger_root": "0000000000000000"
}
```

**Initial rules:**

| ID | Type       | Description                       | Expires   | Priority     |
| -- | ---------- | --------------------------------- | --------- | ------------ |
| R1 | OBLIGATION | Prioritize Zone A when demand > 0 | Episode 1 | 10 (highest) |
| R2 | OBLIGATION | Satisfy Zone B when demand > 0    | Never     | 5            |
| R3 | PERMISSION | Collect at source                 | Never     | 0            |
| R4 | PERMISSION | Move anywhere                     | Never     | 0            |
| R5 | PERMISSION | Deposit at zones when inv>0       | Never     | 0            |

**Notes (frozen):**

* R1 expiration at episode 1 creates the revision necessity trigger.
* R1 has higher priority than R2, so when both zones demand, R1 binds.
* At episode 2, R1 expires → R2 becomes sole OBLIGATION → agent must patch to restore Zone A priority (or equivalent).

### 3.3 Update Semantics

1. Apply `NormPatchV410` to `rules` list.
2. Increment `rev`.
3. Compute new `norm_hash` from canonical `rules`.
4. Set `last_patch_hash` to hash of the patch.
5. Update `ledger_root` by hashing `(old_ledger_root || last_patch_hash)`.

---

## 4. MVRSA-4.1 Component Wiring

### 4.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          MVRSA-4.1                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │DELIBERATE│───▶│  COMPILE │───▶│   MASK   │───▶│  SELECT  │  │
│  │  (LLM)   │    │ (JCOMP)  │    │          │    │ (blind)  │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│       │                                               │         │
│       │              ┌──────────┐                     │         │
│       └─────────────▶│ EXECUTE  │◀────────────────────┘         │
│                      │          │                               │
│                      └────┬─────┘                               │
│                           │                                     │
│                           ▼                                     │
│                    ┌──────────────┐                             │
│                    │  NormState   │                             │
│                    │  (persist)   │                             │
│                    └──────────────┘                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Interface Definitions

```python
# Deliberate → Compile
@dataclass
class DeliberationOutput:
    justifications: List[JustificationV410]  # minItems ≥ 1, one per candidate action
    patch: Optional[NormPatchV410]

# Compile → Mask
@dataclass
class CompilationResult:
    action_id: str
    status: Literal["COMPILED", "PARSE_ERROR", "SCHEMA_ERROR", "REFERENCE_ERROR"]
    compiled_rules: Optional[List[RuleEval]]

@dataclass
class CompilationBatch:
    results: List[CompilationResult]  # One per justification
    compiled_count: int
    failed_count: int

# Mask → Select
@dataclass
class MaskedActions:
    feasible: List[str]  # Action IDs computed by Mask
    feasible_count: int  # Informative metric

# Select → Execute
@dataclass
class Selection:
    action_id: str
    source: Literal["AUTHORED", "HALT"]  # No DEFAULT, no RANDOM fallback

# Execute output
@dataclass
class ExecutionResult:
    obs: Observation
    reward: float
    done: bool
    info: Dict[str, Any]
```

### 4.3 Selector Blindness (Binding)

The selector:

* Receives only `MaskedActions.feasible` (action IDs)
* Has no access to justifications, compiled_rules, or normative state
* Selects uniformly at random if multiple feasible actions exist
* Returns `HALT` if `feasible = []`
* **No DEFAULT source exists** — defaults are forbidden

### 4.4 Fail-Not-Substitute (Binding)

If all compilations fail:

* `feasible = []`
* Selector returns `HALT`
* No action is substituted
* No default is applied
* Each failed compilation counts against `C` metric

---

## 5. Environment Definition: TriDemandV410

### 5.1 Overview

A 5×5 gridworld with three demand zones, resource scarcity, and a mechanical revision trigger.

v4.1 adds an environment obligation interface:

* `target_satisfied`
* `rank`
* `progress_set`

### 5.2 State Space

```python
@dataclass
class TriDemandState:
    agent_pos: Tuple[int, int]      # (0-4, 0-4) → 5 bits (25 cells)
    inventory: int                   # 0-3 → 2 bits
    zone_demands: Tuple[int, int, int]  # Each ∈ {0, 1} → 3 bits
    zone_satisfied: Tuple[bool, bool, bool]  # → 3 bits
    step: int                        # 0-39 (H=40) → 6 bits
    episode: int                     # 0-19 (E=20) → 5 bits
    rule_r1_active: bool             # → 1 bit
```

**State size bit budget:**

| Field          | Range  | Bits        |
| -------------- | ------ | ----------- |
| agent_pos      | 0-24   | 5           |
| inventory      | 0-3    | 2           |
| zone_demands   | {0,1}³ | 3           |
| zone_satisfied | bool³  | 3           |
| step           | 0-39   | 6           |
| episode        | 0-19   | 5           |
| rule_r1_active | bool   | 1           |
| **Total**      |        | **25 bits** |

**State size cap:** S = 32 bits (satisfies S bound with headroom)

### 5.3 Action Space

| Action  | ID | Effect                           |
| ------- | -- | -------------------------------- |
| MOVE_N  | A0 | Move north (if valid)            |
| MOVE_S  | A1 | Move south (if valid)            |
| MOVE_E  | A2 | Move east (if valid)             |
| MOVE_W  | A3 | Move west (if valid)             |
| COLLECT | A4 | Collect resource at source       |
| DEPOSIT | A5 | Deposit resource at current zone |

**Action arity:** A = 6 (satisfies A ≤ 6)

**WAIT status (frozen):**

* There is **no WAIT action** in TriDemandV410. `WAIT` remains reserved in schemas but maps to an empty action set in this environment.

### 5.4 Grid Layout

```
┌───┬───┬───┬───┬───┐
│ . │ . │ B │ . │ . │   B = Zone B (demand)
├───┼───┼───┼───┼───┤
│ . │ . │ . │ . │ . │
├───┼───┼───┼───┼───┤
│ A │ . │ S │ . │ C │   A = Zone A, C = Zone C, S = Source
├───┼───┼───┼───┼───┤
│ . │ . │ . │ . │ . │
├───┼───┼───┼───┼───┤
│ . │ . │ X │ . │ . │   X = Agent start
└───┴───┴───┴───┴───┘
```

### 5.5 Obligation Target Semantics (v4.1, frozen)

Define obligation target satisfaction:

* `{"kind":"DEPOSIT_ZONE","target_id":"ZONE_A"}` is satisfied iff `zone_a_satisfied == True`
* `{"kind":"DEPOSIT_ZONE","target_id":"ZONE_B"}` is satisfied iff `zone_b_satisfied == True`
* `{"kind":"DEPOSIT_ZONE","target_id":"ZONE_C"}` is satisfied iff `zone_c_satisfied == True`

Environment must implement:

```python
def target_satisfied(obs, obligation_target) -> bool:
    ...
```

### 5.6 Rank Function (v4.1, frozen)

Environment must implement:

```python
INF = 10**9  # sentinel for impossible obligations

def rank(obs, obligation_target) -> int:
    """
    Returns 0 iff target satisfied.
    Returns INF iff impossible (TriDemandV410 has no impossible targets under valid physics).
    Otherwise returns a natural-number rank that strictly decreases along progress_set actions.
    Deterministic, well-founded, non-semantic.
    """
```

**TriDemandV410 rank definition:**

Let `pos = obs.agent_pos`. Let `inv = obs.inventory`. Let `src = POSITIONS["SOURCE"]`. Let `zone_pos(tgt)` be the position of the target zone.

* If `target_satisfied(obs, tgt)` → `rank = 0`
* Else if `inv == 0` → `rank = 1 + manhattan(pos, src)`
* Else (`inv > 0`) → `rank = 1 + manhattan(pos, zone_pos(tgt))`

**Interpretation (frozen):**

* At target zone with inventory>0 and not yet satisfied → `rank = 1`
* After a successful DEPOSIT that satisfies the target → `rank = 0`

### 5.7 progress_set Function (v4.1, frozen)

Environment must implement:

```python
def progress_set(obs, tgt) -> Set[str]:
    return { a for a in ACTION_IDS if rank(step(obs, a), tgt) < rank(obs, tgt) }
```

Properties:

* Finite
* Deterministic
* Depends only on `(obs, tgt)`
* Does not consult agent internals
* Returns empty set iff obligation is impossible (not expected in TriDemandV410 under valid dynamics)

### 5.7.1 Step Dynamics (frozen)

* `MOVE_*`: update position iff within bounds; else no-op.
* `COLLECT`: if at SOURCE and inventory<3, inventory += 1; else no-op.
* `DEPOSIT`: if at a demanded zone and inventory>0:

  * inventory -= 1
  * set corresponding `zone_satisfied=True`
  * clear demand bit if modeled that way (or leave demand as “was demanded”; satisfaction flag is authoritative for target_satisfied)
    else no-op.

### 5.7.2 Branching Constraint (v4.1 calibration requirement)

For each obligation target, the environment must exhibit at least one non-terminal state where:

* `|progress_set(obs, tgt)| ≥ 2`

except where grid boundaries force unique descending motion.

Failure → `INVALID_RUN / ENV_AUTOPILOT_DEGENERACY`

### 5.8 Conflict Trigger

**Unavoidable conflict (step ≤ F):**

At step 5 (on Oracle path), Zone A and Zone B both have demand=1, but only one resource is immediately available. The Oracle must choose which to satisfy first, creating a `RESOURCE_CONTENTION` conflict between active obligations:

* `R1: OBLIGATION target Zone A (initial, priority 10)`
* `R2: OBLIGATION target Zone B (priority 5)`

**F = 10** (conflict occurs by step 10 on Oracle path)

### 5.9 Revision Necessity Trigger

**Mechanical trigger:**

Rule `R1` has `expires_episode: 1`. At episode 2 start:

* `R1` is invalidated (removed from active rules)
* Without revision, the agent has no high-priority binding for Zone A
* The agent **must** issue a `NormPatch` to ADD or REPLACE an obligation restoring Zone A priority (or equivalent legal structure)

If no patch is issued by step 5 of episode 2, the agent enters `LOCKOUT` state (no valid actions for Zone A situations).

### 5.10 Success Criterion

Episode success: All three zones satisfied within H steps.

### 5.11 Bounds Summary

| Parameter          | Value                          |
| ------------------ | ------------------------------ |
| State size cap (S) | 32 bits (25 used)              |
| Action arity (A)   | 6                              |
| Episode length (H) | 40 steps                       |
| Episode count (E)  | 20 episodes                    |
| Conflict bound (F) | 10 steps                       |
| Revision trigger   | Episode 2, step 0 (R1 expires) |

---

## 6. Calibration Gate

### 6.1 Thresholds

| Parameter                 | Value |
| ------------------------- | ----- |
| τ (Oracle success rate)   | 0.95  |
| ε (ASB Null success rate) | 0.10  |

### 6.2 Calibration Protocol

**Note:** Calibration runs are separate pre-freeze verification runs, not subject to v4.1 Episode Cap E. They validate the environment before the main experiment begins.

1. Run **Human Oracle** (scripted optimal policy) for 100 episodes across all seeds.
2. Verify success rate ≥ τ = 0.95.
3. Run **ASB Null** (uniform random) for 100 episodes across all seeds.
4. Verify success rate ≤ ε = 0.10.
5. Verify branching constraint (§5.7.2) holds for each target (Zone A/B/C) on at least one reachable non-terminal state.

**Gate failure:**

* `INVALID_RUN / ENV_NOT_DISCRIMINATIVE` (Oracle/Null thresholds fail), or
* `INVALID_RUN / ENV_AUTOPILOT_DEGENERACY` (branching constraint fails)

### 6.3 Oracle Policy (Sketch)

```
1. Collect from Source when inventory == 0
2. Deposit to highest-priority demanded zone per active obligation
3. If conflict: follow active priority (R1 initially)
4. At episode 2: issue patch to reinstate Zone A priority obligation
5. Repeat until all zones satisfied
```

---

## 7. Seed List

**Preregistered seeds (N = 5):**

```python
SEEDS = [42, 123, 456, 789, 1024]
```

All runs must use exactly these seeds. Additional seeds require v4.2+.

---

## 8. Weakening Ladder Parameters

### 8.1 W1: Justification Traces

| Parameter     | `max_trace_tokens`                           |
| ------------- | -------------------------------------------- |
| Units         | Tokens (cl100k_base)                         |
| Baseline      | 512                                          |
| Δ (step size) | -64                                          |
| Rungs         | 512 → 448 → 384 → 320 → 256 → 192 → 128 → 64 |
| Minimum rung  | 64 (schema-valid minimum)                    |

**Truncation rules (schema-preserving):**

1. Token budget applies to canonical JSON string of justification.
2. Truncation is deterministic, applied in order:

   * Truncate `args` arrays from end (preserve at least 1 arg per claim)
   * Remove `claims` from end (preserve at least 1 claim)
   * Remove `counterfactual` if present
   * Remove `conflict` if present
3. Required fields (`action_id`, `rule_refs[0]`, `claims[0]`) are never removed.
4. If budget < schema-valid minimum (~64 tokens), compilation fails and counts against `C`.
5. Rung 0 is not included — minimum rung is 64 tokens.

### 8.2 W2: Semantic Affordances

| Parameter     | `obs_bits_budget`                        |
| ------------- | ---------------------------------------- |
| Units         | Bits (observation quantization)          |
| Baseline      | 64                                       |
| Δ (step size) | -8                                       |
| Rungs         | 64 → 56 → 48 → 40 → 32 → 24 → 16 → 8 → 0 |
| Quantization  | Deterministic hash-based feature masking |

### 8.3 W3: Reflection

| Parameter     | `min_steps_between_patches`                                         |
| ------------- | ------------------------------------------------------------------- |
| Units         | Steps                                                               |
| Baseline      | 1 (can patch every step)                                            |
| Δ (step size) | +5                                                                  |
| Rungs         | 1 → 6 → 11 → 16 → 21 → 26 → 31 → 36 → 41 (>H, effectively disabled) |

### 8.4 W4: Persistence

| Parameter     | `persist_episodes_horizon`                          |
| ------------- | --------------------------------------------------- |
| Units         | Episodes                                            |
| Baseline      | 20 (full E)                                         |
| Δ (step size) | -2                                                  |
| Rungs         | 20 → 18 → 16 → 14 → 12 → 10 → 8 → 6 → 4 → 2 → 1 → 0 |

### 8.5 Normalization Reporting

Each threshold reported as:

1. **Absolute:** e.g., `max_trace_tokens = 128`
2. **Normalized:** e.g., `128 / 512 = 0.25` (25% of baseline)

---

## 9. Guardrails

### 9.1 Compilation Rate

| Metric  | `C`                                       |
| ------- | ----------------------------------------- |
| `C_min` | 0.70                                      |
| Meaning | ≥70% of deliberation outputs must compile |

### 9.2 Halt Rate

| Metric  | `H`                              |
| ------- | -------------------------------- |
| `H_max` | 0.20                             |
| Meaning | ≤20% of steps may result in HALT |

### 9.3 Audit Failures

| Metric  | `A`                                   |
| ------- | ------------------------------------- |
| `A_max` | 0.10                                  |
| Meaning | ≤10% of steps may have audit failures |

### 9.4 Timeouts

| Timeout          | Value       | Effect               |
| ---------------- | ----------- | -------------------- |
| `T_deliberation` | 30 seconds  | Deliberation failure |
| `T_step`         | 60 seconds  | Step failure         |
| `T_episode`      | 600 seconds | Episode failure      |

---

## 10. Ablation Battery

### 10.1 Run A — Semantic Excision

* **Preserve observation shape and arity** (same keys/types, same feature vector length)
* Replace semantic payloads with **opaque tokens** of equal arity/type
* Opaque token generation: `hash(field_name || run_seed)` truncated to field's original byte length
* Tokens are **constant per field across all steps and episodes** (no time-indexed variation)
* Deliberator sees structurally valid but semantically meaningless observation
* All other components intact

### 10.2 Run B — Reflection Excision

* Block all `NormPatch` operations
* `rev` stays at 0
* `rules` never changes post-initialization

### 10.3 Run C — Persistence Excision

* Reset `NormState` to initial at each episode boundary
* Patches apply within episode only

### 10.4 Run D — Trace Excision

* Remove `justification` from compilation input
* Compiler receives only `action_id`
* No `claims`, no `rule_refs`

---

## 11. Classification Rules (Inherited)

Each valid run classified as exactly one:

| Classification                     | Condition                                                 |
| ---------------------------------- | --------------------------------------------------------- |
| BASELINE                           | Survives pressure-free, diverges from ASB                 |
| NARRATIVE_COLLAPSE                 | Trace ablation causes ASB-equivalence                     |
| INCENTIVE_CAPTURE                  | Semantic ablation causes ASB-equivalence                  |
| ONTOLOGICAL_COLLAPSE               | Reflection or persistence ablation causes ASB-equivalence |
| ASB_CLASS_REDUCIBILITY             | Baseline indistinguishable from ASB                       |
| DISQUALIFIED / REDUNDANCY_DETECTED | SPOF test survival                                        |
| INVALID_RUN                        | Gate/protocol violation                                   |

---

## 12. Execution Order (Binding)

```
1. Design Freeze (this document) → APPROVED
2. Implementation
3. Environment Calibration
4. Baseline Verification (5 seeds)
5. Ablation Battery (A, B, C, D × 5 seeds = 20 runs)
6. Weakening Ladders (W1, W2, W3, W4 × 5 seeds × rungs)
7. SPOF Tests
8. Final Classification + Closure
```

---

## 13. Deliberator LLM Freeze (v4.1 addition, binding)

The deliberator may be implemented using Claude.

After Design Freeze approval, the following parameters are frozen and **must not change**:

* `provider` (must be constant)
* `model` (exact Claude model ID string)
* `temperature`
* `max_output_tokens`
* `system_prompt` text
* `tool_mode / json_mode` setting (if used)
* retry policy (max retries + what is shown to the model on retry)

Any change after approval → `INVALID_RUN / DELIBERATOR_INTERFACE_CHANGE`.

---

## 14. Approval Gate

**This document must be approved before any execution runs.**

| Item                                                      | Status        |
| --------------------------------------------------------- | ------------- |
| DSL JSON Schema                                           | Defined       |
| JCOMP-4.1 Spec                                            | Defined       |
| NormState Schema                                          | Defined       |
| Component Wiring                                          | Defined       |
| Environment                                               | Defined       |
| Obligation interface (rank/progress_set/target_satisfied) | Defined       |
| Calibration Gates                                         | Defined       |
| Seeds                                                     | Preregistered |
| Ladder Parameters                                         | Preregistered |
| Guardrails                                                | Defined       |
| Ablation Battery                                          | Defined       |
| Deliberator LLM freeze                                    | Defined       |

---

**Awaiting approval to proceed with implementation.**

---

**End of v4.1 Design Freeze Document**
