# Stage VIII-4 — Preregistration

**Stage:** VIII-4 — Governance Transitions (Meta-Authority)
**Version:** v0.1
**Status:** FROZEN
**Date:** 2026-02-04

---

## 1. Experimental Question

> *Can authority govern authority through ordinary, authority-bound transformations without privilege, escalation, kernel choice, or semantic exception?*

---

## 2. Entry Conditions

Stage VIII-4 may begin only if:

1. AKR-0 v0.1 is CLOSED — POSITIVE
2. Stage VIII-1 v0.1 is CLOSED — POSITIVE
3. Stage VIII-2 v0.1 is CLOSED — POSITIVE
4. Stage VIII-3 v0.1 is CLOSED — POSITIVE
5. AST Spec v0.2 is frozen and binding
6. AIE v0.1 is frozen and binding

---

## 3. Inherited Invariants (Binding)

The following invariants from prior stages remain in force:

| Invariant | Source |
|-----------|--------|
| Authority Opacity | AKR-0 |
| Identity Immutability | AKR-0 |
| Refusal-First Semantics | VIII-1 |
| Conflict Persistence | VIII-2 |
| Anti-Ordering | VIII-2 |
| Temporal Governance (expiry/renewal) | VIII-3 |
| Two-Phase Processing | VIII-3 |
| Determinism and Replayability | All |

---

## 4. New Invariants (VIII-4 Specific)

### 4.1 Governance Non-Amplification Invariant

> No governance action may create authority whose Action Admissibility Vector (AAV) exceeds the union of the admitting authorities' AAVs.

Formally:
```
AAV_new ⊆ (AAV_auth1 ∪ AAV_auth2 ∪ ... ∪ AAV_authN)
```

where `{auth1, ..., authN}` are the ACTIVE authorities that admit the governance action.

Violation constitutes:
```
VIII4_FAIL / AUTHORITY_LAUNDERING
```

### 4.2 Governance Action Identity Invariant

Governance action identity is determined by the tuple:
```
(epoch, sorted(initiator_ids), sorted(target_ids), action_type, params_hash)
```

- Sorting is bytewise lexicographic on canonical encodings
- `params_hash` = SHA256(canonical_json(params))
- Identical governance actions at different epochs are distinct

**Canonicalization rules for params_hash (per AST Appendix C):**
1. UTF-8 encoding, no BOM
2. No whitespace (minified): `separators=(',', ':')`
3. Object keys sorted lexicographically by UTF-8 byte value
4. Integers only (no floats, no exponential notation)
5. Null fields included explicitly as `null`
6. No optional field omission — all fields present
7. Arrays preserve semantic order
8. Boolean values as `true`/`false` (lowercase)

### 4.3 No Kernel Decision Invariant

The kernel must not:
- Choose which authority governs
- Choose which governance action applies
- Resolve governance conflicts
- Break self-referential loops

Any kernel-initiated governance constitutes:
```
VIII4_FAIL / KERNEL_DECISION
```

---

## 5. Schema Definitions

### 5.1 Action Admissibility Vector (AAV)

AAV is a fixed-length bit vector indexed by Transformation Type ID.

```python
AAV_LENGTH = 16  # Number of transformation types in AST v0.2

class AAV:
    """
    Action Admissibility Vector.

    AAV[i] = 1: Authority can admit transformation type i
    AAV[i] = 0: Authority cannot admit transformation type i

    Bit ordering: bit i corresponds to Transformation Type ID i (LSB = bit 0)
    """
    bits: int  # Packed as unsigned integer, LSB = type 0
```

**Transformation Type IDs (AST v0.2):**

| ID | Type | Description |
|----|------|-------------|
| 0 | EXECUTE | Standard resource transformation |
| 1 | DESTROY_AUTHORITY | Governance: void an authority |
| 2 | CREATE_AUTHORITY | Governance: create new authority |
| 3-15 | RESERVED | Reserved for future use |

**Reserved Bits Constraint (v0.1):**

All reserved bits (3-15) must be 0 in all authority AAVs. Any authority with a 1 in a reserved bit position constitutes:
```
INVALID_RUN / AAV_RESERVED_BIT_SET
```

This prevents capability stowaway in undefined fields.

### 5.2 Extended AuthorityRecord Schema

```python
@dataclass
class AuthorityRecord:
    authority_id: str           # Unique, immutable
    status: AuthorityStatus     # ACTIVE, EXPIRED, VOID
    resource_scope: str         # Opaque scope identifier
    aav: int                    # Action Admissibility Vector (packed bits)
    expiry_epoch: int           # Epoch at which authority expires
    lineage: Optional[str]      # Prior authority ID (for renewals)
    metadata: dict              # Status-specific metadata
```

### 5.3 Governance Action Schema

```python
@dataclass
class GovernanceAction:
    action_type: GovernanceActionType  # DESTROY_AUTHORITY or CREATE_AUTHORITY
    initiator_ids: frozenset[str]      # Authorities requesting the action
    target_ids: frozenset[str]         # Authorities being targeted
    epoch: int                         # Epoch of action
    params: dict                       # Action-specific parameters

class GovernanceActionType(Enum):
    DESTROY_AUTHORITY = 1
    CREATE_AUTHORITY = 2
```

**DESTROY_AUTHORITY params:**
```python
{
    "target_authority_id": str,
    "destruction_reason": str  # Optional trace metadata
}
```

**CREATE_AUTHORITY params:**
```python
{
    "new_authority_id": str,
    "resource_scope": str,      # Must exactly match an admitting authority's scope (§8.3)
    "scope_basis_authority_id": str,  # ID of admitting authority whose scope is used
    "aav": int,                 # Must satisfy non-amplification (§8.2)
    "expiry_epoch": int,
    "lineage": Optional[str]    # If renewal/delegation
}
```

---

## 6. Instruction Accounting

### 6.1 Instruction Cost Constants

| Constant | Symbol | Value |
|----------|--------|-------|
| Authority lookup | C_LOOKUP | 1 |
| AAV word operation | C_AAV_WORD | 1 |
| AST rule application | C_AST_RULE | 2 |
| Conflict/deadlock update | C_CONFLICT_UPDATE | 3 |
| State transition write | C_STATE_WRITE | 2 |

### 6.2 Epoch Instruction Budget

```
B_EPOCH_INSTR = 1000
```

This budget applies **per epoch total**, not per action.

### 6.3 AAV Containment Cost

```
cost = C_AAV_WORD * ceil(AAV_LENGTH / 64)
```

For AAV_LENGTH = 16: cost = 1 instruction per containment check.

### 6.4 Exhaustion Behavior

On budget exhaustion during action evaluation:

1. Abort evaluation of current action (atomic, no partial state)
2. Emit `ACTION_REFUSED` with reason `BOUND_EXHAUSTED`
3. Refuse all remaining actions in epoch with same reason
4. Epoch terminates

---

## 7. Processing Order

### 7.1 Two-Phase Processing (Extended from VIII-3)

**Phase 1:** Epoch Advancement
1. Process epoch advancement events
2. Apply eager expiry to authorities past expiry_epoch
3. Update conflict statuses for expired authorities

**Phase 2:** Actions (in sub-phase order)
1. **Renewals** — AuthorityRenewalRequest events
2. **Authority Destructions** — DESTROY_AUTHORITY governance actions
3. **Authority Creations** — CREATE_AUTHORITY governance actions
4. **Non-Governance Actions** — Standard action requests

### 7.3 Authority Activation Timing (Critical)

> **Authorities created within a step-batch do not become ACTIVE until the next step-batch boundary.**

**Step-batch definition (v0.1):** A step-batch is the complete Phase 2 processing of a single epoch after Phase 1 expiry. There is exactly one step-batch per epoch.

This prevents within-batch bootstrapping and ensures:
- No same-batch admission by newly created authorities
- Instruction bound is an invariant, not an ordering artifact
- Deterministic evaluation independent of creation order within batch

Consequence: A governance chain where AUTH_A creates AUTH_B, and AUTH_B immediately creates AUTH_C, requires **multiple epochs**, not one.

### 7.2 Intra-Sub-Phase Ordering

Within each sub-phase, process items in lexicographic order by identity tuple:

```
(epoch, sorted(initiator_ids), sorted(target_ids), action_type, params_hash)
```

This ordering is deterministic and replayable.

---

## 8. Admissibility Evaluation

### 8.0 Scope Overlap Definition (v0.1, Structural)

For v0.1, scope relationships are defined by byte-equality only:

```
scope_overlap(A, B) := (A.resource_scope == B.resource_scope)
covers(A, target)   := (A.resource_scope == target.resource_scope)
```

No semantic parsing, subsetting, or lattice operations are permitted.

### 8.1 Governance Action Admissibility

For a governance action to be admissible:

1. At least one ACTIVE authority must have `AAV[action_type] = 1`
2. The admitting authority's resource_scope must cover the target per §8.0 (byte-equality)
3. All ACTIVE authorities whose scope overlaps the target must agree structurally

**Structural agreement** means: under identical AST rule application, all overlapping authorities produce the same admissibility result. There is no "DENY vote" — only structural compatibility or incompatibility.

### 8.2 Non-Amplification Check

For CREATE_AUTHORITY:

1. Compute `AAV_union = AAV_auth1 | AAV_auth2 | ... | AAV_authN` for all admitting authorities
2. Check `(params.aav & ~AAV_union) == 0`
3. If check fails: refuse with reason `AMPLIFICATION_BLOCKED`

### 8.3 Scope Containment for CREATE_AUTHORITY

For v0.1, scope handling is purely structural:

1. `scope_basis_authority_id` must be in the admitting authority set
2. `params.resource_scope` must **exactly equal** `scope_basis_authority.resource_scope`
3. No scope derivation, subsetting, or semantic parsing is permitted
4. If constraint 1 or 2 fails: refuse with reason `SCOPE_NOT_COVERED`

> **Note:** Both "basis not in admitting set" and "scope token mismatch" map to the single refusal reason `SCOPE_NOT_COVERED`. No finer distinction is made in v0.1.

This ensures non-amplification extends to scope without semantic interpretation.

### 8.4 Conflict Detection

A conflict exists iff there exist at least two ACTIVE authorities whose admissibility evaluations for the same action yield different structural results under the same AST rules.

Examples of structural incompatibility:
- Authority A covers target scope, Authority B covers target scope, but A's AAV permits while B's AAV does not
- Authority A covers target scope with PERMIT verdict, Authority B covers overlapping scope with structural constraint that blocks

On conflict:
1. Register conflict record with participant authority IDs
2. Enter deadlock state
3. Emit `DEADLOCK_DECLARED` with cause `CONFLICT`

---

## 9. Outputs

Stage VIII-4 may emit only:

| Output | Description |
|--------|-------------|
| `AUTHORITY_EXPIRED` | Authority transitioned to EXPIRED |
| `AUTHORITY_RENEWED` | New authority created with lineage |
| `AUTHORITY_DESTROYED` | Authority transitioned to VOID |
| `AUTHORITY_CREATED` | New authority created (no lineage) |
| `ACTION_EXECUTED` | Action completed successfully |
| `ACTION_REFUSED` | Action refused with reason |
| `DEADLOCK_DECLARED` | First entry into deadlock |
| `DEADLOCK_PERSISTED` | Continued deadlock state |

### 9.1 Output Schemas

**AUTHORITY_CREATED:**
```python
{
    "outputType": "AUTHORITY_CREATED",
    "eventIndex": int,
    "stateHash": str,
    "details": {
        "new_authority_id": str,
        "resource_scope": str,
        "aav": int,
        "expiry_epoch": int,
        "lineage": Optional[str],
        "admitting_authorities": list[str],
        "creation_epoch": int
    }
}
```

**ACTION_REFUSED (extended reasons):**
```python
{
    "reason": str,  # NO_AUTHORITY, CONFLICT_BLOCKS, AMPLIFICATION_BLOCKED,
                    # BOUND_EXHAUSTED, TARGET_NOT_ACTIVE
    ...
}
```

---

## 10. Experimental Conditions

### Condition A — Governance Without Authority

**Setup:**
- No ACTIVE authority has AAV bit set for governance actions
- Governance action DESTROY_AUTHORITY proposed

**Events:**
1. GovernanceAction(DESTROY_AUTHORITY, target=AUTH_X)

**Expected Outputs:**
1. ACTION_REFUSED (reason: NO_AUTHORITY)

**Success Criteria:**
1. Governance action refused
2. No authority state change
3. No conflict registered (no authority to conflict)

---

### Condition B — Single-Authority Governance

**Setup:**
- AUTH_GOV: ACTIVE, AAV = 0b011 (EXECUTE + DESTROY_AUTHORITY)
- AUTH_TARGET: ACTIVE, AAV = 0b001 (EXECUTE only)

**Events:**
1. GovernanceAction(DESTROY_AUTHORITY, initiator=AUTH_GOV, target=AUTH_TARGET)

**Expected Outputs:**
1. AUTHORITY_DESTROYED (authority_id: AUTH_TARGET)

**Success Criteria:**
1. Governance action executes
2. AUTH_TARGET transitions to VOID
3. No conflict (single admitting authority)

---

### Condition C — Conflicting Governance Authorities

**Setup:**
- AUTH_GOV_A: ACTIVE, AAV = 0b011 (EXECUTE + DESTROY), scope = SCOPE_X
- AUTH_GOV_B: ACTIVE, AAV = 0b001 (EXECUTE only, no DESTROY), scope = SCOPE_X (overlapping)
- AUTH_TARGET: ACTIVE, scope = SCOPE_X

**Events:**
1. GovernanceAction(DESTROY_AUTHORITY, target=AUTH_TARGET)

**Structural conflict:** AUTH_GOV_A has AAV bit for DESTROY; AUTH_GOV_B does not. Both cover AUTH_TARGET's scope. This is structural incompatibility under AST rules.

**Expected Outputs:**
1. ACTION_REFUSED (reason: CONFLICT_BLOCKS, conflict_id: C:0001)
2. DEADLOCK_DECLARED (cause: CONFLICT)

**Success Criteria:**
1. Conflict registered between AUTH_GOV_A and AUTH_GOV_B
2. Deadlock declared
3. AUTH_TARGET remains ACTIVE

---

### Condition D1 — Self-Governance Execution

**Setup:**
- AUTH_SELF: ACTIVE, AAV = 0b011 (EXECUTE + DESTROY_AUTHORITY)
- AUTH_SELF is the only governance-capable authority
- AUTH_SELF's scope covers itself

**Events:**
1. GovernanceAction(DESTROY_AUTHORITY, initiator=AUTH_SELF, target=AUTH_SELF)

**Expected Outputs:**
1. AUTHORITY_DESTROYED (authority_id: AUTH_SELF)

**Success Criteria:**
1. Self-targeting governance executes
2. AUTH_SELF transitions to VOID
3. No special-case handling
4. System may have no remaining governance authority (valid terminal state)

---

### Condition D2 — Self-Governance Deadlock

**Setup:**
- AUTH_SELF_A: ACTIVE, AAV = 0b011 (EXECUTE + DESTROY), scope = SCOPE_S
- AUTH_SELF_B: ACTIVE, AAV = 0b001 (EXECUTE only, no DESTROY), scope = SCOPE_S
- Both cover AUTH_SELF_A's scope (SCOPE_S)

**Events:**
1. GovernanceAction(DESTROY_AUTHORITY, target=AUTH_SELF_A)

**Structural conflict:** AUTH_SELF_A has AAV bit for DESTROY; AUTH_SELF_B does not. Both cover the target's scope. This is structural incompatibility under AST rules.

**Expected Outputs:**
1. ACTION_REFUSED (reason: CONFLICT_BLOCKS, conflict_id: C:0001)
2. DEADLOCK_DECLARED (cause: CONFLICT)

**Success Criteria:**
1. Conflict registered between AUTH_SELF_A and AUTH_SELF_B
2. Deadlock declared
3. Both authorities remain ACTIVE
4. No special-case resolution for self-governance

---

### Condition E — Infinite Regress Attempt

**Setup:**
- AUTH_R1 through AUTH_R100: All ACTIVE, AAV = 0b111 (EXECUTE + DESTROY + CREATE)
- All share the same resource_scope (mutual governance)
- Each authority's scope covers all others

**Events:**
A single step-batch containing 200 governance actions:
1. GovernanceAction(CREATE_AUTHORITY, initiator=AUTH_R1, params={new_id: AUTH_NEW_1, ...})
2. GovernanceAction(CREATE_AUTHORITY, initiator=AUTH_R2, params={new_id: AUTH_NEW_2, ...})
... (200 CREATE actions from existing ACTIVE authorities)

**Expected Outputs:**
Some AUTHORITY_CREATED events, then:
- ACTION_REFUSED (reason: BOUND_EXHAUSTED) for remaining actions

**Success Criteria:**
1. Instruction bound (B_EPOCH_INSTR = 1000) limits total work
2. Chain terminates deterministically via bound exhaustion
3. No infinite loop possible
4. Partial progress is valid (some authorities created before exhaustion)
5. Final state is deterministic and replayable
6. Newly created authorities are NOT used as initiators (per §7.3)

---

## 11. Global Success Criteria

| # | Criterion | Condition |
|---|-----------|-----------|
| 1 | Governance refused without authority | A |
| 2 | No authority state change on refusal | A |
| 3 | Single-authority governance executes | B |
| 4 | Target transitions to VOID | B |
| 5 | Conflicting governance enters deadlock | C |
| 6 | Conflict record created | C |
| 7 | Self-targeting governance executes | D1 |
| 8 | Self-termination is valid terminal state | D1 |
| 9 | Self-targeting with conflict enters deadlock | D2 |
| 10 | No special-case for self-governance | D1, D2 |
| 11 | Regress terminates via bound | E |
| 12 | Partial progress valid | E |
| 13 | Newly created authorities not used as same-batch initiators | E |
| 14 | Non-amplification enforced (AAV) | All |
| 15 | Scope containment enforced (exact match) | All |
| 16 | No kernel-initiated governance | All |
| 17 | No implicit ordering | All |
| 18 | Governance actions have distinct identities | All |
| 19 | Deterministic and replayable | All |
| 20 | Hash chain integrity | All |
| 21 | No reserved AAV bits set | All |

---

## 12. Failure Taxonomy

### Stage Failures (Terminal)

| Code | Meaning |
|------|---------|
| `VIII4_FAIL / AUTHORITY_LAUNDERING` | Non-amplification violated |
| `VIII4_FAIL / GOVERNANCE_PRIVILEGE` | Governance bypassed admissibility |
| `VIII4_FAIL / IMPLICIT_ORDERING` | Priority inferred from governance metadata |
| `VIII4_FAIL / IMPLICIT_RESOLUTION` | Conflict resolved without explicit action |
| `VIII4_FAIL / KERNEL_DECISION` | Kernel chose governance outcome |
| `VIII4_FAIL / IN_PLACE_MUTATION` | Authority modified without new ID |
| `VIII4_FAIL / RESPONSIBILITY_LOSS` | Trace incomplete |

### Invalid Run

| Code | Meaning |
|------|---------|
| `INVALID_RUN / NONTERMINATING_REGRESS` | Regress did not terminate |
| `INVALID_RUN / NONDETERMINISTIC_EXECUTION` | Replay diverged |
| `INVALID_RUN / OUTPUT_VIOLATION` | Unexpected output type |
| `INVALID_RUN / UNAUTHORIZED_INPUT` | Implicit trigger or kernel-generated input |
| `INVALID_RUN / AAV_RESERVED_BIT_SET` | Authority has 1 in reserved AAV bit (3-15) |

---

## 13. Classification Rule

Stage VIII-4 produces exactly one classification:

**PASS:**
```
VIII4_PASS / GOVERNANCE_TRANSITIONS_POSSIBLE
```

**FAIL:**
```
VIII4_FAIL / <reason>
```

**INVALID:**
```
INVALID_RUN / <reason>
```

---

## 14. Licensed Claim

If Stage VIII-4 passes, it licenses only:

> *Governance transitions can be represented as ordinary authority-bound transformations and either execute lawfully or fail explicitly without semantic privilege.*

It does not license claims of:
- Governance stability
- Institutional persistence
- Democratic legitimacy
- Optimal amendment procedures

---

## 15. Logging and Verification

### 15.1 Required Trace Fields

For each governance action:
- Governance action identity tuple
- Admitting authority IDs and their AAVs
- Non-amplification check result
- Instruction cost incurred
- Conflict/deadlock state transitions
- Final authority state hashes

### 15.2 Hash Chain

Per AST Appendix C and VIII-3 precedent:
```
H[i] = SHA256( ascii_hex(H[i-1]) || canonical_json_bytes(output[i]) )
```

Genesis hash: `"0" × 64` (64-char ASCII string of zeros)

### 15.3 Replay Verification

Given identical:
- Initial state hash
- Epoch sequence
- Input event sequence

The following must be bit-identical:
- All output events
- Final state hash
- Hash chain head

---

## 16. Preregistration Freeze Checklist

Before freeze, confirm:

- [ ] AAV schema defined (§5.1)
- [ ] Transformation Type IDs enumerated (§5.1)
- [ ] Reserved AAV bits constraint defined (§5.1)
- [ ] AuthorityRecord schema extended (§5.2)
- [ ] GovernanceAction schema defined (§5.3)
- [ ] CREATE_AUTHORITY scope_basis_authority_id required (§5.3)
- [ ] Instruction costs frozen (§6.1)
- [ ] Epoch budget frozen (§6.2)
- [ ] Exhaustion behavior defined (§6.4)
- [ ] Phase 2 ordering frozen (§7.1)
- [ ] Authority activation timing frozen (§7.3)
- [ ] Intra-sub-phase ordering frozen (§7.2)
- [ ] Scope containment for CREATE defined (§8.3)
- [ ] Conflict detection structural-only (§8.4)
- [ ] Non-amplification check defined (§8.2)
- [ ] Canonicalization rules frozen (§4.2)
- [ ] All conditions specified (§10)
- [ ] Success criteria enumerated (§11)
- [ ] Failure taxonomy complete (§12)
- [ ] Hash chain formula specified (§15.2)

---

## 17. Freeze Block

```
FROZEN: 2026-02-04T00:00:00Z
HASH: 28393554a3afee666e3aaecaa9f2784c3c2ccf7cba007a7746270485409a2454
TIMESTAMP: 2026-02-04T00:00:00Z
```

**Freeze Procedure:** SHA-256 of document bytes with HASH set to TBD.

---

**End of Preregistration — Stage VIII-4 v0.1**
