# Stage VIII-5 — Preregistration

**Stage:** VIII-5 — Authority Injection Under Open-System Constraint
**Version:** v0.1
**Status:** FROZEN
**Date:** 2026-02-04
**Hash:** `8b8a9bc54c186548232309045740a73360abbee9339f00eac70d71eb1f1968f3`

---

## 1. Experimental Question

> *Can new authority be injected explicitly at the kernel boundary without violating conflict persistence, auditability, responsibility traceability, or non-privilege guarantees?*

---

## 2. Entry Conditions

Stage VIII-5 may begin only if:

1. AKR-0 v0.1 is CLOSED — POSITIVE
2. Stage VIII-1 v0.1 is CLOSED — POSITIVE
3. Stage VIII-2 v0.1 is CLOSED — POSITIVE
4. Stage VIII-3 v0.1 is CLOSED — POSITIVE
5. Stage VIII-4 v0.1 is CLOSED — POSITIVE
6. AST Spec v0.2 is frozen and binding
7. AIE v0.1 is frozen and binding
8. No authority injection occurs in prior stages

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
| Governance Non-Amplification | VIII-4 |
| No Kernel Decision | VIII-4 |
| Determinism and Replayability | All |

---

## 4. New Invariants (VIII-5 Specific)

### 4.1 Authority Injection Core Invariant

> No authority may enter the system except through an explicit, externally supplied injection event that is structurally evaluated under the same kernel invariants as all other authority state transitions.

There is no implicit authority creation.
There is no kernel-initiated injection.

Violation constitutes:
```
VIII5_FAIL / GOVERNANCE_PRIVILEGE
```

### 4.2 Authority Identity Derivation Invariant

AuthorityID values for injected authorities are **content-addressed**.

Each AuthorityID is deterministically derived from the capability-defining subset of the AuthorityRecord using SHA-256 per AST Spec v0.2.

**Fields included in hash (capability core):**
- holder / principal identifier
- resource_scope
- aav (Action Admissibility Vector)
- expiry_epoch

**Fields excluded from hash:**
- authority_id (derived, not input)
- status (runtime state)
- start/activation epoch (processing-dependent)
- destruction metadata
- injection source identifier
- trace/audit metadata
- creation_metadata.lineage (including "VOID" sentinel)

Canonical definition:
```
AuthorityCore := project(AuthorityRecord, CORE_FIELDS)
AuthorityID := SHA256(canonical_serialize(AuthorityCore))
```

Consequences:
- Identical capability records yield identical AuthorityIDs
- Duplicate injections are idempotent
- Same capability at different epochs → same AuthorityID
- Same capability from different sources → same AuthorityID

Violation constitutes:
```
VIII5_FAIL / IMPLICIT_ORDERING
```

### 4.3 Injection Lineage Constraint

Injected authorities must specify:
```
creation_metadata.lineage := "VOID"
```

`VOID` is a string literal sentinel indicating no lineage and no parent authority.

Properties:
- `VOID` is not comparable to any AuthorityID
- No ordering or privilege may be inferred from `VOID`
- `VOID` lineage activates VIII-5–specific validation path
- Created authorities (VIII-4) use `creation_metadata.lineage := <CreatorAuthorityID>`

Violation constitutes:
```
VIII5_FAIL / GOVERNANCE_PRIVILEGE
```

### 4.4 Anti-Ordering Invariant (Extended)

Injection must not introduce implicit ordering.

No priority may be inferred from:
- external origin
- injection timing
- injection source
- novelty
- absence of prior conflicts

Injected authority is not "higher" authority.

Violation constitutes:
```
VIII5_FAIL / IMPLICIT_ORDERING
```

### 4.5 Governance Non-Amplification Invariant (Extended)

> Injected authority must not retroactively amplify the effective authority of existing authorities.

Injection may introduce new authority capability, but must not:
- legitimize previously inadmissible actions without re-evaluation
- erase or downgrade existing conflict records
- bypass admissibility checks

Violation constitutes:
```
VIII5_FAIL / AUTHORITY_LAUNDERING
```

---

## 5. Schema Definitions

### 5.1 Authority Injection Event

```python
@dataclass
class AuthorityInjectionEvent:
    """
    External event introducing a new authority into the system.

    Not a governance action. Not authorized by existing authorities.
    Evaluated only for structural admissibility.
    """
    authority_record: AuthorityRecord  # The authority to inject
    source_id: str                      # Opaque, stable identifier (required, non-empty)
    injection_epoch: int                # Must equal current_epoch at processing time
```

**Source Identifier Requirements:**
- Required (not optional)
- Must be stable under replay
- Kernel treats as opaque
- Empty string forbidden
- If unknown, use sentinel: `"UNKNOWN"`

**Injection Epoch Consistency (Binding):**
- `injection_epoch` is required for logging/replay
- Kernel must enforce: `injection_epoch == current_epoch`
- If violated: emit `ACTION_REFUSED` with reason `EPOCH_MISMATCH` (non-terminal)

### 5.2 Extended AuthorityRecord Schema (Lineage Field)

```python
@dataclass
class AuthorityRecord:
    authority_id: str                  # Content-addressed for injected authorities
    status: AuthorityStatus            # PENDING, ACTIVE, EXPIRED, VOID
    resource_scope: str                # Opaque scope identifier
    aav: int                           # Action Admissibility Vector (packed bits)
    expiry_epoch: int                  # Epoch at which authority expires
    creation_metadata: CreationMetadata  # Includes lineage field
    metadata: dict                     # Status-specific metadata

@dataclass
class CreationMetadata:
    lineage: str                       # "VOID" for injected, CreatorID for created
    creation_epoch: int                # Epoch of injection/creation
    # Additional fields as needed
```

### 5.3 Canonical Serialization for Content-Addressing

Per AST Spec v0.2 Appendix C:

1. UTF-8 encoding, no BOM
2. No whitespace (minified): `separators=(',', ':')`
3. Object keys sorted lexicographically by UTF-8 byte value
4. Integers only (no floats, no exponential notation)
5. Null fields included explicitly as `null`
6. No optional field omission — all fields present
7. Arrays preserve semantic order
8. Boolean values as `true`/`false` (lowercase)

---

## 6. Instruction Accounting

### 6.1 Instruction Cost Constants

| Constant | Symbol | Value |
|----------|--------|-------|
| Authority lookup | C_LOOKUP | 1 |
| State transition write | C_STATE_WRITE | 2 |
| Hash computation | C_HASH | 2 |
| AAV word operation | C_AAV_WORD | 1 |
| AST rule application | C_AST_RULE | 2 |
| Conflict/deadlock update | C_CONFLICT_UPDATE | 3 |
| Trace append | C_TRACE_APPEND | 1 |

### 6.2 Injection Cost

```
C_INJECT = C_LOOKUP + C_STATE_WRITE + C_HASH + C_AST_RULE + C_TRACE_APPEND = 8
```

This covers:
- State lookup (duplicate detection)
- State write (if new)
- Hash computation (content-addressing)
- Schema validation (C_AST_RULE)
- Trace append (C_TRACE_APPEND)

Nothing is free. All injection operations consume budget.

### 6.3 Epoch Instruction Budget

```
B_EPOCH_INSTR = 1000
```

This budget applies **per epoch total**, not per action or injection.

### 6.4 Exhaustion Behavior

On budget exhaustion during injection evaluation:

1. Abort evaluation of current injection (atomic, no partial state)
2. Emit `ACTION_REFUSED` with reason `BOUND_EXHAUSTED`
3. Refuse all remaining injections/actions in epoch with same reason
4. The kernel stops processing further events in the current epoch after emitting refusals for all remaining queued events

---

## 7. Processing Order

### 7.1 Two-Phase Processing (Extended)

**Phase 1:** Epoch Advancement
1. Process epoch advancement events
2. Apply eager expiry to authorities past expiry_epoch
3. Transition PENDING authorities to ACTIVE
4. Update conflict statuses for expired/activated authorities

**Epoch Advancement Constraint (Binding):**

At most one epoch advancement request may be processed per epoch batch; additional requests are refused with `ACTION_REFUSED / DUPLICATE_EPOCH_ADVANCE`.

**Phase 2:** Actions (in sub-phase order)
1. **Injections** — Authority injection events
2. **Renewals** — AuthorityRenewalRequest events
3. **Authority Destructions** — DESTROY_AUTHORITY governance actions
4. **Authority Creations** — CREATE_AUTHORITY governance actions
5. **Non-Governance Actions** — Standard action requests

### 7.2 Authority Activation Timing

> **Injected authorities enter PENDING state and become ACTIVE only at the next epoch boundary.**

- Injection in epoch N → PENDING
- Epoch advancement to N+1 → becomes ACTIVE
- Cannot admit actions in injection epoch

This matches VIII-4 behavior for created authorities.

### 7.3 Intra-Sub-Phase Ordering

Within each sub-phase, process items in deterministic order:

For injections: lexicographic order by `(source_id, authority_id)`

Since `injection_epoch == current_epoch` is enforced, epoch is redundant in the ordering key.

---

## 8. Injection Evaluation

### 8.1 Structural Validation

At each injection event:

1. Validate AuthorityRecord schema (AST v0.2)
2. Enforce reserved-field constraints (AAV bits 3-15 must be 0)
3. Verify `creation_metadata.lineage == "VOID"`
4. Compute content-addressed AuthorityID
5. Check for duplicate (AuthorityID already exists)
6. Verify budget sufficiency for atomic completion
7. If new: register injected authority as PENDING
8. If duplicate: no state change

**AuthorityID Input Handling (Binding):**

For injection events, the kernel ignores any provided `authority_record.authority_id` and overwrites it with the derived content-addressed AuthorityID. If a non-empty AuthorityID is supplied and differs from the derived value, the injection is refused with `HASH_MISMATCH`.

9. Emit appropriate outputs
10. Preserve all existing conflicts

### 8.2 Injection Admissibility Checks (Binding)

Every injection must be:

1. Schema-valid (AST v0.2)
2. VOID-lineaged (`creation_metadata.lineage == "VOID"`)
3. Epoch-consistent (`injection_epoch == current_epoch`)
4. Content-addressed (AuthorityID derived from capability core)
5. Within deterministic budget for atomic completion

**If any check fails:**

Emit `ACTION_REFUSED` with a specific refusal reason:
- `SCHEMA_INVALID` — AuthorityRecord fails AST v0.2 validation
- `LINEAGE_INVALID` — lineage is not "VOID"
- `EPOCH_MISMATCH` — injection_epoch != current_epoch
- `HASH_MISMATCH` — record contains non-derived AuthorityID or fails derivation
- `BOUND_EXHAUSTED` — insufficient budget for atomic completion

On refusal:
- Preserve state (no partial injection)
- Continue processing remaining events only if budget permits
- Otherwise refuse remaining with `BOUND_EXHAUSTED`

**Terminal failure is reserved for kernel bypass:**

Executing an injection without performing the checks above constitutes:
```
VIII5_FAIL / UNGATED_EXECUTION
```

This preserves `UNGATED_EXECUTION` as kernel cheating, not bad inputs.

### 8.3 Duplicate Detection

Duplicate is determined by **AuthorityID match** (content-addressed over capability core).

If AuthorityID already exists in Authority State (regardless of status):
- Emit `AUTHORITY_INJECTED` (trace-only repeat)
- No Authority State mutation
- No reactivation, no epoch reset, no status change

Epoch does not matter for duplicate detection.

---

## 9. Injection and Conflict Semantics

### 9.1 Injected Authority Conflict Behavior

Injected authority must not:
- Clear existing conflict records
- Retroactively authorize blocked actions
- Downgrade deadlock states

Injected authority may:
- Join existing conflicts (at activation time)
- Create new conflicts when ACTIVE

### 9.2 Injection Under Deadlock

If injection occurs while system is in deadlock:
- Deadlock persists until admissibility changes structurally
- Kernel must not exit deadlock solely due to injection

Injection does not guarantee deadlock resolution.

---

## 10. Outputs

Stage VIII-5 may emit only:

| Output | Description |
|--------|-------------|
| `AUTHORITY_INJECTED` | Injection event processed (new or duplicate) |
| `AUTHORITY_EXPIRED` | Authority transitioned to EXPIRED |
| `AUTHORITY_RENEWED` | New authority created with lineage |
| `AUTHORITY_DESTROYED` | Authority transitioned to VOID |
| `AUTHORITY_CREATED` | New authority created via governance |
| `ACTION_EXECUTED` | Action completed successfully |
| `ACTION_REFUSED` | Action refused with reason |
| `DEADLOCK_DECLARED` | First entry into deadlock |
| `DEADLOCK_PERSISTED` | Continued deadlock state |

**Note:** `AUTHORITY_PENDING` is an internal state transition logged in the audit layer but not emitted as a user-visible output (per F4 resolution).

### 10.1 Output Schemas

**AUTHORITY_INJECTED:**
```python
{
    "outputType": "AUTHORITY_INJECTED",
    "eventIndex": int,
    "stateHash": str,
    "details": {
        "authority_id": str,
        "source_id": str,
        "injection_epoch": int,
        "is_duplicate": bool,
        "resource_scope": str,
        "aav": int,
        "expiry_epoch": int
    }
}
```

---

## 11. Experimental Conditions

### Condition A — Injection Into Empty Authority State

**Setup:**
- No ACTIVE authorities
- Authority state is empty or contains only EXPIRED/VOID authorities
- System in EMPTY_AUTHORITY deadlock state

**Events:**
1. Inject AUTH_A with VOID lineage at epoch 0
2. Advance epoch to 1

**Expected Outputs:**
1. `DEADLOCK_DECLARED` or `DEADLOCK_PERSISTED` at epoch 0 (EMPTY_AUTHORITY)
2. `AUTHORITY_INJECTED` (AUTH_A) at epoch 0
3. `DEADLOCK_PERSISTED` at epoch 0 (AUTH_A still PENDING)
4. After epoch advance to 1: deadlock may clear only if admissibility changes lawfully due to activation (explicitly logged)

**Success Criteria:**
1. Injection succeeds
2. Authority enters PENDING state
3. Deadlock persists until activation
4. Authority activates at next epoch boundary
5. Deadlock resolution (if any) is explicit and lawful
6. Trace complete

---

### Condition B — Injection Into Active Conflict

**Setup:**
- AUTH_X and AUTH_Y: ACTIVE, conflicting on resource R
- Deadlock declared

**Events:**
1. Inject AUTH_Z with overlapping scope on R at epoch N
2. Advance epoch to N+1

**Expected Outputs:**
1. `AUTHORITY_INJECTED` (AUTH_Z)
2. `DEADLOCK_PERSISTED` (conflict persists)

**Success Criteria:**
1. Injection succeeds
2. Existing conflict not erased
3. Deadlock persists or expands
4. No implicit resolution

---

### Condition C — Competing Injections

**Setup:**
- Empty authority state

**Events:**
1. Inject AUTH_A at epoch 0
2. Inject AUTH_B at epoch 0 (same epoch, overlapping scope)
3. Advance epoch to 1

**Expected Outputs:**
1. `AUTHORITY_INJECTED` (AUTH_A)
2. `AUTHORITY_INJECTED` (AUTH_B)
3. (Both activate at epoch 1)
4. Conflict may be declared if scopes overlap with incompatible AAVs

**Success Criteria:**
1. Both injections processed
2. No ordering preference
3. No kernel arbitration
4. Deterministic outcome under replay
5. Outcome invariance: swapping injection list order must not change Authority State or conflict classification, only trace ordering

---

### Condition D — Injection After Authority Destruction

**Setup:**
- AUTH_X: created at epoch 0, destroyed at epoch N

**Events:**
1. Inject AUTH_Y at epoch N+1 with similar scope

**Expected Outputs:**
1. `AUTHORITY_INJECTED` (AUTH_Y)

**Success Criteria:**
1. AUTH_Y treated as new authority
2. No resurrection of AUTH_X
3. Different AuthorityID (content-addressed)
4. Clean lineage ("VOID")

---

### Condition E — Injection Under Load

**Setup:**
- Epoch budget partially consumed by prior operations
- Remaining budget near exhaustion threshold

**Events:**
1. Inject AUTH_A

**Expected Outputs:**
- If sufficient budget: `AUTHORITY_INJECTED`
- If insufficient budget: `ACTION_REFUSED` (BOUND_EXHAUSTED)

**Success Criteria:**
1. Lawful refusal or success
2. No partial state
3. Atomic completion or atomic refusal
4. Budget accounting correct

---

### Condition F — Injection Flooding Attempt

**Setup:**
- Empty authority state
- High volume of injection events (exceeds epoch budget)

**Events:**
1. Inject AUTH_1, AUTH_2, ..., AUTH_N (N >> B_EPOCH_INSTR / C_INJECT)

**Expected Outputs:**
1. `AUTHORITY_INJECTED` for as many as budget allows
2. `ACTION_REFUSED` (BOUND_EXHAUSTED) for remainder

**Success Criteria:**
1. Refusal occurs only via budget exhaustion
2. No heuristic throttling
3. No prioritization
4. No silent collapse of trace or state
5. Deterministic cutoff point

---

## 12. Success Criteria (VIII5_PASS)

All of the following must hold for Stage VIII-5 to pass:

| # | Criterion | Verification |
|---|-----------|--------------|
| 1 | Injection is explicit | No implicit or kernel-initiated injection |
| 2 | Identity is content-addressed | AuthorityID = SHA256(capability core) |
| 3 | VOID lineage enforced | All injected authorities have lineage = "VOID" |
| 4 | No implicit ordering | No priority from timing, source, or novelty |
| 5 | No kernel arbitration | Kernel does not choose between competing injections |
| 6 | No conflict erasure | Injection does not clear existing conflicts |
| 7 | No deadlock bypass | Injection does not exit deadlock implicitly |
| 8 | Duplicate injections idempotent | Same content → same ID → no state change |
| 9 | Flooding handled via budget only | No heuristic throttling |
| 10 | Replay is bit-perfect | Identical inputs → identical outputs |
| 11 | Trace completeness preserved | All injections logged with source, epoch, ID |

---

## 13. Failure Criteria (Terminal)

| Failure Mode | Cause |
|--------------|-------|
| `VIII5_FAIL / AUTHORITY_LAUNDERING` | Semantic interpretation or retroactive amplification |
| `VIII5_FAIL / IMPLICIT_ORDERING` | User-assigned IDs or timing-based priority |
| `VIII5_FAIL / AUTHORITY_REANIMATION` | Overwriting existing AuthorityIDs |
| `VIII5_FAIL / GOVERNANCE_PRIVILEGE` | Lineage violation or kernel-initiated injection |
| `VIII5_FAIL / KERNEL_DECISION` | Kernel arbitrates between injections |
| `VIII5_FAIL / IMPLICIT_RESOLUTION` | Conflict or deadlock cleared by injection |
| `VIII5_FAIL / RESPONSIBILITY_LOSS` | Trace incomplete or unstable under replay |
| `VIII5_FAIL / UNGATED_EXECUTION` | Structural validation bypassed |
| `VIII5_FAIL / AD_HOC_RESOURCE_ARBITRATION` | Heuristic throttling or prioritization |
| `INVALID_RUN / NONDETERMINISTIC_EXECUTION` | Replay produces different results |
| `INVALID_RUN / NONTERMINATING_REGRESS` | Wall-clock timeout or unbounded execution |
| `INVALID_RUN / SCOPE_VIOLATION` | Injection in prior stages or entry conditions unmet |
| `INVALID_RUN / DESIGN_DRIFT` | Post-freeze modification |

---

## 14. Classification Rule

```
IF all 11 success criteria hold across all 6 conditions:
    VIII5_PASS
ELSE:
    VIII5_FAIL / <lowest-index violated criterion (1..11)>
```

---

## 15. Preregistration Checklist

- [ ] AST Spec v0.2 frozen
- [ ] AIE v0.1 frozen
- [ ] Stage VIII-5 execution semantics frozen
- [ ] Authority injection schema frozen
- [ ] Content-addressed AuthorityID derivation frozen
- [ ] VOID lineage sentinel semantics frozen
- [ ] Authority activation discipline frozen
- [ ] Admissibility logic frozen
- [ ] Conflict and deadlock handling frozen
- [ ] Intra-epoch evaluation bound frozen
- [ ] Deterministic instruction budget frozen
- [ ] Canonical input ordering rule frozen
- [ ] Execution harness definition frozen
- [ ] Logging schema frozen
- [ ] Replay protocol frozen
- [ ] Seeds and initial state hashes frozen

---

## 16. Appendix A: Cost Constants Summary

```python
# Instruction costs (frozen)
C_LOOKUP = 1        # Authority state lookup
C_STATE_WRITE = 2   # State transition write
C_HASH = 2          # Hash computation (SHA-256)
C_AAV_WORD = 1      # AAV word operation
C_AST_RULE = 2      # AST rule application
C_CONFLICT_UPDATE = 3  # Conflict/deadlock update
C_TRACE_APPEND = 1  # Trace append

# Derived costs
C_INJECT = C_LOOKUP + C_STATE_WRITE + C_HASH + C_AST_RULE + C_TRACE_APPEND  # = 8

# Budget
B_EPOCH_INSTR = 1000  # Per-epoch instruction budget
```

---

## 17. Appendix B: Capability Core Fields

Fields included in content-addressed hash for injected authorities:

| Field | Type | Description |
|-------|------|-------------|
| holder | str | Principal identifier |
| resource_scope | str | Opaque scope identifier |
| aav | int | Action Admissibility Vector |
| expiry_epoch | int | Expiry epoch |

Fields explicitly excluded:

| Field | Reason |
|-------|--------|
| authority_id | Derived (output, not input) |
| status | Runtime state |
| creation_metadata.lineage | Routing marker ("VOID") |
| creation_metadata.creation_epoch | Processing-dependent |
| source_id | Injection context, not capability |
| metadata | Audit/trace data |

---

## 18. Appendix C: Kernel Extension Strategy

Stage VIII-5 extends the Stage VIII-4 kernel. This is not a new kernel.

**Additions:**
- `process_injection()` method
- Content-addressed ID computation
- VOID lineage validation
- Duplicate detection
- `AUTHORITY_INJECTED` output emission

**Unchanged:**
- All VIII-4 governance logic
- Conflict and deadlock semantics
- Budget accounting (extended for C_HASH)
- Two-phase processing (extended for injections sub-phase)
- Activation timing

---

**End of Stage VIII-5 Preregistration — v0.1**
