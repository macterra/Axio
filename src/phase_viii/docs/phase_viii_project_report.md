# Phase VIII Project Report
## Governance Stress Architecture Proof of Concept (GSA-PoC)

- **Program:** Phase VIII — GSA-PoC
- **Version History:** VIII-0 v0.1 → VIII-5 v0.1
- **Date:** February 4, 2026
- **Status:** ✅ CLOSED POSITIVE — VIII-0 through VIII-5 PASS

---

## Executive Summary

Governance Stress Architecture Proof of Concept (GSA-PoC) is a six-stage experimental program investigating the **structural requirements for authority-constrained execution** in computational systems. The program asks: *Can authority enforcement, conflict resolution, temporal governance, and meta-authority be realized mechanically without semantics, heuristics, optimization, or fallback?*

### Core Achievement

Phase VIII demonstrates that **authority governance can be purely structural**, enabling:
1. Authority-constrained execution without semantic interpretation
2. Plural authority representation without implicit collapse
3. Conflict resolution only through explicit destruction
4. Temporal persistence only through explicit renewal
5. Meta-authority without privilege escalation
6. Authority injection without provenance laundering

> **Under the tested adversarial model, authority-constrained execution is mechanically realizable using a deterministic kernel. Conflicts persist until explicitly destroyed. Time does not resolve conflict or restore authority. Governance operates as ordinary authority-bound transformation without semantic privilege. Injection is explicit, content-addressed at the injection boundary, and non-privileged.**

### Key Results Summary

| Stage | Core Test | Result | Status |
|-------|-----------|--------|--------|
| VIII-0 (AKR-0) v0.1 | Authority kernel calibration | ✅ AKR0_PASS | CLOSED |
| VIII-1 (MPA) v0.1 | Plural authority representation | ✅ VIII1_PASS | CLOSED |
| VIII-2 (DCR) v0.1 | Destructive conflict resolution | ✅ VIII2_PASS | CLOSED |
| VIII-3 (TG) v0.1 | Temporal governance | ✅ VIII3_PASS | CLOSED |
| VIII-4 (GT) v0.1 | Governance transitions | ✅ VIII4_PASS | CLOSED |
| VIII-5 (AI) v0.1 | Authority injection | ✅ VIII5_PASS | CLOSED |

---

## 1. Program Architecture

### 1.1 Core Thesis

> "Authority is structural. Conflicts persist. Time does not heal. Governance binds itself."

Phase VIII establishes that **structural enforcement** — not behavioral heuristics, semantic analysis, or optimization — is sufficient for authority governance **under the tested adversarial model**.

### 1.2 Frozen Dependencies

| Specification | Version | Purpose |
|---------------|---------|---------|
| AST Spec (Authority State Transformation) | v0.2 | Authority kernel formalism |
| AIE Spec (Authority Input Environment) | v0.1 | Authority feed specification |

### 1.3 Architectural Invariants

All Phase VIII experiments satisfy:

1. **Authority Opacity** — Authority internals are not inspected for semantic content
2. **Identity Immutability** — Authority identity cannot change once instantiated in kernel state
3. **Refusal-First Semantics** — Inadmissible actions are refused, not queued or modified
4. **Conflict Persistence** — Conflicts persist until explicitly resolved through destruction
5. **Anti-Ordering** — No implicit ordering by creation time, source, or novelty
6. **Determinism and Replayability** — Identical inputs produce identical outputs

### 1.4 Progressive Constraint Model

| Stage | Mechanism Tested | Builds On |
|-------|------------------|-----------|
| VIII-0 | Authority-constrained execution | — |
| VIII-1 | Plural authority + conflict detection | VIII-0 |
| VIII-2 | Destructive resolution only | VIII-0, VIII-1 |
| VIII-3 | Temporal governance (expiry/renewal) | VIII-0, VIII-1, VIII-2 |
| VIII-4 | Meta-authority (governance actions) | VIII-0, VIII-1, VIII-2, VIII-3 |
| VIII-5 | Authority injection | All prior stages |

---

## 2. Foundation Specifications

### 2.1 AST Spec v0.2 (Authority State Transformation)

**Purpose:** Formal specification of the authority kernel — what authority is, how it's represented, and how it transforms.

**Core Definitions:**
- **Authority:** The lawful capacity to bind action within a defined scope, under explicit provenance and responsibility (structural, not semantic)
- **Authority State:** Complete inspectable representation of all authorities, scopes, conflicts, and transitions
- **Sovereignty Invariant:** No action may be taken unless attributable to at least one explicit, active authority

**Lawful Transformations:**
| Transformation | Description |
|----------------|-------------|
| Create | New authority enters state |
| Suspend | Authority temporarily inactive |
| Resume | Suspended authority reactivated |
| Revoke | Authority permanently removed |
| Expire | Authority validity ends |
| Narrow Scope | Authority scope reduced |
| Register Conflict | Conflict between authorities recorded |
| Resolve Conflict | Conflict resolved (destructive only) |

> *Phase VIII exercises a restricted subset of AST transformations (CREATE, DESTROY, RENEW, EXPIRE, EXECUTE, CONFLICT/DEADLOCK registration); other AST transformations (Suspend, Resume, Narrow Scope, non-destructive Resolve) are not activated in this program.*

**Deadlock Taxonomy (DeadlockCause enum):**
| DeadlockCause | Description |
|---------------|-------------|
| CONFLICT_DEADLOCK | Mutually exclusive claims, no resolution authority |
| GOVERNANCE_DEADLOCK | No authority to modify authority structure |
| ENTROPIC_COLLAPSE | Authority exhausted through lawful resolution |
| EMPTY_AUTHORITY | No ACTIVE authorities remain |

### 2.2 AIE Spec v0.1 (Authority Input Environment)

**Purpose:** Specifies the external environment that supplies authority records to the kernel.

**Critical Constraint — Feeder Blindness:**
> Authority issuance must be independent of kernel state, outcomes, and semantic interpretation. No semantic puppeteering allowed.

**Key Parameters:**
- Address Book (fixed set of holder identifiers)
- Active Scope Pool (finite subset with declared collision probability)
- Injection schedule / issuance functions (declared ex ante)

---

## 3. Experiment History

### 3.1 VIII-0 (AKR-0) v0.1 — Authority Kernel Runtime Calibration

**Research Question:**
> Can authority-constrained execution be carried out deterministically, auditable refusal enforced, and deadlock recognized — without semantics, heuristics, optimization, or fallback?

**Purpose:** Calibration baseline. Establishes that the kernel correctly executes, refuses, and detects deadlock.

**Conditions:**
| Condition | Description | Injections/Epoch | Actions/Epoch |
|-----------|-------------|------------------|---------------|
| A | Valid Authority (positive control) | 20 | 20 |
| B | Authority Absence (negative control) | 0 | 20 |
| C | Conflict Saturation | 50 | 20 |

**Key Results:**
- 15/15 runs passed
- 61,115 total events processed
- 179 actions executed, 24,872 refused
- Condition B: Immediate ENTROPIC_COLLAPSE (correct behavior)
- Replay verified: 15/15 ✓

**Contribution:** Established that authority-constrained execution is mechanically realizable. The kernel correctly classifies all events and maintains determinism.

---

### 3.2 VIII-1 (MPA) v0.1 — Minimal Plural Authority (Static)

**Research Question:**
> Can plural authority be represented structurally without collapse, even when no action is admissible?

**Purpose:** Tests whether two competing authorities can coexist structurally.

**Conditions:**
| Condition | Description | Expected |
|-----------|-------------|----------|
| A | Contested Actions | Both authorities present, conflict registered, deadlock declared |
| B | Third-Party Actions | Deadlock persists, third-party actions refused |

**Key Results:**
- 10/10 success criteria passed
- Both authorities symmetric (no distinguishing structural property)
- Conflict registered on first contested action
- DEADLOCK_DECLARED emitted exactly once
- Deadlock persisted through Condition B

**Verification Checks:**
| Check | Description |
|-------|-------------|
| CHECK_BOTH_AUTHORITIES_PRESENT | AUTH_A and AUTH_B both ACTIVE at run end |
| CHECK_AUTHORITIES_SYMMETRIC | No distinguishing structural property |
| CHECK_CONFLICT_REGISTERED | Conflict registered on first contested action |
| CHECK_NO_ACTION_EXECUTED | No ACTION_EXECUTED emitted |
| CHECK_REFUSAL_CODES_CORRECT | All actions refused with correct reason codes |
| CHECK_DEADLOCK_DECLARED_ONCE | DEADLOCK_DECLARED emitted exactly once |
| CHECK_DEADLOCK_PERSISTS | Deadlock persists through Condition B |
| CHECK_THIRD_PARTY_REFUSED | Third-party actions refused in deadlock state |
| CHECK_STATE_HASH_DETERMINISTIC | State hash deterministic across replay |
| CHECK_LOGS_VERIFY | All logs verify with hash chain intact |

**Contribution:** Demonstrated that plural authority can coexist structurally. The kernel does not implicitly resolve or collapse competing claims.

---

### 3.3 VIII-2 (DCR) v0.1 — Destructive Conflict Resolution (Timeless)

**Research Question:**
> Can authority conflicts be resolved only through explicit destruction — no implicit resolution, no temporal priority, no silent merging?

**Purpose:** Tests that destruction is the sole resolution mechanism.

**Conditions:**
| Condition | Description | Expected |
|-----------|-------------|----------|
| A | Destroy Denying Authority | Action executed after AUTH_B destroyed |
| B | Destroy Both Authorities | Permanent deadlock (no authority remains) |
| C | No Destruction Authorization | Deadlock persists indefinitely |

**Key Results:**
- All conditions passed
- Asymmetric admissibility: AUTH_A permits EXECUTE_OP0, AUTH_B denies (empty set)
- VOID state: irreversible transition, non-participant in admissibility
- Forbidden events verified: No CONFLICT_RESOLVED, DEADLOCK_EXITED, AUTHORITY_MERGED

**Verification Checks:**
| Check | Description |
|-------|-------------|
| CHECK_DESTRUCTION_ENABLES_ACTION | Action executes only after destroying denial authority |
| CHECK_VOID_IS_IRREVERSIBLE | VOID authorities cannot be reactivated |
| CHECK_VOID_NONPARTICIPANT | VOID authorities do not participate in admissibility |
| CHECK_BOTH_DESTROYED_DEADLOCK | Destroying both causes permanent deadlock |
| CHECK_NO_IMPLICIT_RESOLUTION | No forbidden resolution events emitted |
| CHECK_DEADLOCK_PERSISTS_WITHOUT_DESTRUCTION | Deadlock persists without destruction authorization |

**Contribution:** Established that destruction is the minimal resolution mechanism. No implicit resolution, temporal priority, or silent merging occurs.

---

### 3.4 VIII-3 (TG) v0.1 — Temporal Governance (Authority Over Time)

**Research Question:**
> Can authority persist over time only via explicit expiry and renewal, without semantic reinterpretation, implicit ordering, or responsibility laundering?

**Purpose:** Tests temporal binding — authority validity is epoch-bounded.

**Core Invariant:**
> No authority may persist across epochs without explicit renewal. No authority may regain force once expired or destroyed. Time does not resolve conflict, repair deadlock, or justify reinterpretation.

**New Mechanisms:**
| Mechanism | Description |
|-----------|-------------|
| **Epochs** | Discrete temporal units (integers 0, 1, 2, ...) |
| **Expiry** | Authority validity ends at expiry_epoch |
| **Renewal** | Explicit action to extend authority expiry |
| **Eager Expiry** | Authorities expire at epoch boundary |

**Conditions:**
| Condition | Description | Expected |
|-----------|-------------|----------|
| A | Expiry Without Renewal | All expired, EMPTY_AUTHORITY deadlock |
| B | Renewal Without Conflict | Renewal restores admissibility for new scope |
| C | Renewal After Destruction | Non-resurrective (AUTH_D remains VOID) |
| D | Renewal Under Ongoing Conflict | No "newest wins" logic applied |

**Key Implementation:**
- Two-phase processing: Phase 1 (epoch advancement + eager expiry), Phase 2 (renewals → destructions → actions)
- Authority states: ACTIVE, EXPIRED, VOID, PENDING
- Conflict status: OPEN_BINDING → OPEN_NONBINDING (when participant becomes non-ACTIVE)

**Key Results:**
- 29/29 success criteria passed
- Expired authorities cannot be renewed (status is terminal)
- VOID authorities cannot be renewed (destruction is permanent)
- Time does not resolve conflict or restore authority

**Contribution:** Established that authority persistence requires explicit renewal. Time does not heal, resolve, or restore.

---

### 3.5 VIII-4 (GT) v0.1 — Governance Transitions (Meta-Authority)

**Research Question:**
> Can authority govern authority through ordinary, authority-bound transformations without privilege, escalation, kernel choice, or semantic exception?

**Purpose:** Tests meta-authority — governance actions are themselves authority-bound.

**New Invariants:**
| Invariant | Description |
|-----------|-------------|
| **Governance Non-Amplification** | `AAV_new ⊆ (AAV_auth1 ∪ ... ∪ AAV_authN)` — no capability laundering |
| **No Kernel Decision** | Kernel must not choose which authority governs or resolve governance conflicts |

**Action Admissibility Vector (AAV):**
| Bit | Type | Description |
|-----|------|-------------|
| 0 | EXECUTE | Standard resource transformation |
| 1 | DESTROY_AUTHORITY | Governance: void an authority |
| 2 | CREATE_AUTHORITY | Governance: create new authority |
| 3-15 | RESERVED | Must be 0 |

**Conditions:**
| Condition | Description | Expected |
|-----------|-------------|----------|
| A | Governance Without Authority | Refused with NO_AUTHORITY |
| B | Single-Authority Governance | Target transitioned to VOID |
| C | Conflicting Governance Authorities | Deadlock declared |
| D1 | Self-Governance Execution | Self-destruction executed, EMPTY_AUTHORITY deadlock |
| D2 | Self-Governance Deadlock | No special-case resolution |
| E | Infinite Regress Attempt | Terminated via instruction bound |

**Key Implementation:**
- B_EPOCH_INSTR = 1000 instruction budget per epoch
- Newly created authorities remain PENDING until next epoch boundary
- 142 authorities created before bound exhaustion in Condition E

**Key Results:**
- 21/21 success criteria passed
- Governance actions execute under same rules as resource actions
- Self-destruction is lawful (no special protection)
- Instruction bound prevents infinite regress

**Contribution:** Established that governance transitions are ordinary authority-bound transformations. No semantic privilege or kernel exception exists.

---

### 3.6 VIII-5 (AI) v0.1 — Authority Injection Under Open-System Constraint

**Research Question:**
> Can new authority be injected explicitly at the kernel boundary without violating conflict persistence, auditability, responsibility traceability, or non-privilege guarantees?

**Purpose:** Tests authority ingress — the kernel boundary is explicit and auditable.

**New Invariants:**
| Invariant | Description |
|-----------|-------------|
| **Authority Injection Core Invariant** | No authority enters except through explicit, externally supplied injection event |
| **Authority Identity Derivation Invariant** | AuthorityID = SHA256(capability_core) |
| **Injection Lineage Constraint** | `creation_metadata.lineage := "VOID"` |
| **Anti-Ordering (Extended)** | No priority from external origin, timing, source, or novelty |

**Capability Core Fields (included in hash):**
| Field | Included |
|-------|----------|
| holder | ✓ |
| resourceScope | ✓ |
| aav | ✓ |
| expiryEpoch | ✓ |

**Conditions:**
| Condition | Description | Expected |
|-----------|-------------|----------|
| A | Injection Into Empty Authority State | Deadlock cleared after activation |
| B | Injection Into Active Conflict | Conflict NOT erased |
| C | Competing Injections | Outcome invariance verified |
| D | Injection After Authority Destruction | No resurrection |
| E | Injection Under Load | Atomic budget enforcement |
| F | Injection Flooding Attempt | 125 succeeded, 75 refused |

**Key Implementation:**
- C_INJECT = 8 instruction cost
- Processing order: `(source_id, authority_id)` lexicographic
- Duplicate detection: same AuthorityID (content-addressed) → idempotent

**Key Results:**
- 11/11 success criteria passed
- 31/31 unit tests passed
- Injection does not clear existing conflicts
- Injection does not bypass deadlock implicitly
- Duplicate injections are idempotent (same capability → same ID → no state change)

**Contribution:** Established that authority injection is explicit, content-addressed, and non-privileged. No provenance laundering or conflict erasure.

---

## 4. Core Findings

### 4.1 Positive Results

1. **Authority-constrained execution is mechanically realizable** — VIII-0 demonstrated that no action executes without authority, and all inadmissible actions are refused.

2. **Plural authority coexists structurally** — VIII-1 showed that competing authorities persist without implicit collapse or resolution.

3. **Destruction is the sole resolution mechanism** — VIII-2 proved that conflicts persist until explicitly destroyed; no temporal priority or silent merging.

4. **Time does not heal** — VIII-3 established that authority persistence requires explicit renewal; expired authorities cannot be resurrected.

5. **Governance is ordinary** — VIII-4 demonstrated that meta-authority operates under the same rules as resource authority; no semantic privilege.

6. **Injection is explicit** — VIII-5 proved that authority enters only through explicit injection events with content-addressed identity.

7. **No intelligence required** — All mechanisms are structural, not heuristic or behavioral.

### 4.2 Structural Properties Established

| Property | Tested In | Status |
|----------|-----------|--------|
| **Authority Opacity** | VIII-0 | ✅ Confirmed |
| **Identity Immutability** | VIII-0 | ✅ Confirmed |
| **Refusal-First Semantics** | VIII-1 | ✅ Confirmed |
| **Conflict Persistence** | VIII-1, VIII-2 | ✅ Confirmed |
| **Anti-Ordering** | VIII-2, VIII-5 | ✅ Confirmed |
| **Destruction-Only Resolution** | VIII-2 | ✅ Confirmed |
| **VOID Irreversibility** | VIII-2, VIII-3 | ✅ Confirmed |
| **Temporal Governance (expiry/renewal)** | VIII-3 | ✅ Confirmed |
| **Two-Phase Processing** | VIII-3, VIII-4, VIII-5 | ✅ Confirmed |
| **Governance Non-Amplification** | VIII-4 | ✅ Confirmed |
| **No Kernel Decision** | VIII-4 | ✅ Confirmed |
| **Content-Addressed Identity (injected authorities)** | VIII-5 | ✅ Confirmed |
| **Determinism and Replayability** | All | ✅ Confirmed |

### 4.3 Methodological Contributions

1. **Preregistration discipline** — All experiments preregistered with frozen component hashes before execution.

2. **Regression gates** — Each experiment must pass prior experiment verification as entry condition.

3. **Condition distinguishability** — Each condition must produce structurally different outcomes.

4. **Adversarial model binding** — Explicit threat model frozen before execution.

5. **Bit-perfect replayability** — All runs verified for deterministic replay.

---

## 5. Technical Specifications

### 5.1 Authority State Schema

```
AuthorityState:
  state_id: str                    # Hash of state
  current_epoch: int               # Current epoch
  authorities: Dict[str, Authority]  # AuthorityID → Authority
  pending_authorities: Dict[str, Authority]  # PENDING authorities
  conflicts: Dict[str, Conflict]   # ConflictID → Conflict
  deadlock: bool                   # Deadlock state
  deadlock_cause: Optional[DeadlockCause]  # If deadlocked
```

### 5.2 Authority Schema

```
Authority:
  authority_id: str               # Immutable; content-addressed iff creation_metadata.lineage == "VOID"
  holder: str                     # Authority holder
  resource_scope: str             # Scope of authority
  aav: int                        # Action Admissibility Vector
  status: AuthorityStatus         # ACTIVE | PENDING | EXPIRED | VOID
  start_epoch: int                # First epoch of validity
  expiry_epoch: int               # Last epoch of validity
  creation_metadata: CreationMetadata  # Lineage and creation info
  expiry_metadata: Optional[ExpiryMetadata]  # If expired/voided
```

### 5.3 Action Admissibility Vector (AAV)

| Bit | Action Type | Meaning |
|-----|-------------|---------|
| 0 | TRANSFORM_EXECUTE | Standard resource transformation |
| 1 | DESTROY_AUTHORITY | Governance: void an authority |
| 2 | CREATE_AUTHORITY | Governance: create new authority |
| 3-15 | RESERVED | Must be 0 |

### 5.4 Authority Status Transitions

```
PENDING → ACTIVE       (epoch boundary activation)
ACTIVE → EXPIRED       (eager expiry at epoch boundary)
ACTIVE → VOID          (destruction)
EXPIRED → (terminal)   (no transitions)
VOID → (terminal)      (no transitions)
```

### 5.5 Instruction Cost Constants

| Constant | Value | Description |
|----------|-------|-------------|
| C_LOOKUP | 1 | Authority lookup |
| C_STATE_WRITE | 2 | State transition write |
| C_HASH | 2 | Hash computation (SHA-256) |
| C_AAV_WORD | 1 | AAV word operation |
| C_AST_RULE | 2 | AST rule application / schema validation |
| C_CONFLICT_UPDATE | 3 | Conflict/deadlock update |
| C_TRACE_APPEND | 1 | Trace append |
| C_INJECT | 8 | Injection cost |
| B_EPOCH_INSTR | 1000 | Epoch instruction budget |

### 5.6 Deadlock Causes

| Cause | Description |
|-------|-------------|
| EMPTY_AUTHORITY | No ACTIVE authorities remain |
| CONFLICT_DEADLOCK | Mutual conflict with no resolution authority |
| GOVERNANCE_DEADLOCK | No authority to modify authority structure |
| ENTROPIC_COLLAPSE | Authority exhausted through lawful resolution |

### 5.7 Refusal Reasons

| Reason | Description |
|--------|-------------|
| NO_AUTHORITY | No authority covers requested action |
| CONFLICT | Action blocked by authority conflict |
| BOUND_EXHAUSTED | Instruction budget exhausted |
| DEADLOCK | System in deadlock state |
| SCHEMA_INVALID | Injection schema validation failed |
| LINEAGE_INVALID | Injection lineage not VOID |
| EPOCH_MISMATCH | Injection epoch does not match current |
| HASH_MISMATCH | Supplied AuthorityID does not match computed |
| DUPLICATE_EPOCH_ADVANCE | Multiple epoch advancements in batch |

### 5.8 AuthorityID Assignment (Scope Clarification)

Authority identity is immutable once instantiated. Content-addressed identity is introduced in VIII-5 **only for injected authorities** marked by `creation_metadata.lineage == "VOID"`, where:

```
authority_id := SHA256(capability_core)
```

Authorities created internally via governance (VIII-4 CREATE_AUTHORITY) retain **opaque AuthorityIDs** (kernel-interpreted only as stable identifiers) and are distinguished structurally by non-VOID lineage.

**No retroactive identity rule is applied to stages VIII-0 through VIII-4.**

| Lineage | AuthorityID Derivation |
|---------|------------------------|
| `"VOID"` (injected) | Content-addressed: SHA256(capability_core) |
| `<CreatorAuthorityID>` (governance-created) | Opaque: kernel treats as uninterpreted immutable ID |

---

## 6. Cumulative Event Statistics

### 6.1 VIII-0 (15 runs)

| Metric | Value |
|--------|-------|
| Total Events | 61,115 |
| Actions Executed | 179 |
| Actions Refused | 24,872 |
| Replay Verified | 15/15 |

### 6.2 VIII-1 (10 success criteria)

| Metric | Value |
|--------|-------|
| Authorities Present | 2 |
| Conflicts Registered | 1 |
| Actions Refused | All contested |
| Deadlock Persisted | ✓ |

### 6.3 VIII-2 (3 conditions)

| Condition | Outcome |
|-----------|---------|
| A (Destroy Denier) | Action executed after destruction |
| B (Destroy Both) | Permanent deadlock |
| C (No Destruction) | Deadlock persists indefinitely |

### 6.4 VIII-3 (29 success criteria)

| Metric | Value |
|--------|-------|
| Epochs Tested | Multiple |
| Expirations Processed | ✓ |
| Renewals Processed | ✓ |
| Resurrection Attempts | Blocked |

### 6.5 VIII-4 (21 success criteria)

| Condition | Outcome |
|-----------|---------|
| A (No Auth) | Refused |
| B (Single Auth) | Executed |
| C (Conflict) | Deadlock |
| D1 (Self-Destroy) | Executed → Empty Authority |
| D2 (Self-Deadlock) | No resolution |
| E (Regress) | 142 authorities before bound |

### 6.6 VIII-5 (11 success criteria, 31 unit tests)

| Condition | Bundles | Outcome |
|-----------|---------|---------|
| A (Empty) | 1 | Deadlock cleared after activation |
| B (Conflict) | 1 | Conflict preserved |
| C (Competing) | 2 | Both processed, order-invariant |
| D (Post-Destroy) | 1 | New authority, no resurrection |
| E (Load) | varies | Budget enforced atomically |
| F (Flood) | 200 | 125 accepted, 75 refused |

---

## 7. Conclusions

### 7.1 What Phase VIII Establishes

1. **Authority-constrained execution is mechanically realizable** — No semantic interpretation, optimization, or fallback required.

2. **Conflicts persist until explicitly destroyed** — No implicit resolution, temporal priority, or silent merging.

3. **Time does not heal** — Authority persistence requires explicit renewal; expired authorities are terminal.

4. **Governance is ordinary** — Meta-authority operates under the same rules as resource authority.

5. **Injection is explicit** — Authority enters only through content-addressed injection events with VOID lineage.

6. **The kernel makes no decisions** — Classification, refusal, and execution are structural, not chosen.

7. **Replayability is bit-perfect** — Identical inputs produce identical outputs across all stages.

*All findings are bounded by the adversarial model: no law-substrate bypass, no key compromise, bounded instruction budget.*

### 7.2 What Phase VIII Does Not Establish

1. **Cryptographic key management** — Key generation, storage, and rotation are out of scope.

2. **Production-scale performance** — Instruction budgets are test-scale; larger loads not validated.

3. **Multi-kernel coordination** — All experiments test single-kernel scenarios.

4. **Semantic attack resistance** — Authority is classified structurally; content-based attacks not tested.

5. **Long-horizon persistence** — Epoch counts are test-scale; longer horizons not validated.

### 7.3 Program Status

**VIII-0 PASS → VIII-1 PASS → VIII-2 PASS → VIII-3 PASS → VIII-4 PASS → VIII-5 PASS**

**Phase VIII (GSA-PoC): CLOSED POSITIVE**

With six stages passing:

- **VIII-0:** Authority kernel calibration verified
- **VIII-1:** Plural authority representation verified
- **VIII-2:** Destructive conflict resolution verified
- **VIII-3:** Temporal governance verified
- **VIII-4:** Governance transitions verified
- **VIII-5:** Authority injection verified

---

## Appendix A: Version Closure Status

| Stage | Version | Status | Classification |
|-------|---------|--------|----------------|
| VIII-0 (AKR-0) | v0.1 | ✅ CLOSED | `AKR0_PASS / AUTHORITY_EXECUTION_ESTABLISHED` |
| VIII-1 (MPA) | v0.1 | ✅ CLOSED | `VIII1_PASS / PLURAL_AUTHORITY_REPRESENTABLE` |
| VIII-2 (DCR) | v0.1 | ✅ CLOSED | `VIII2_PASS / DESTRUCTIVE_RESOLUTION_POSSIBLE` |
| VIII-3 (TG) | v0.1 | ✅ CLOSED | `VIII3_PASS / TEMPORAL_SOVEREIGNTY_POSSIBLE` |
| VIII-4 (GT) | v0.1 | ✅ CLOSED | `VIII4_PASS / GOVERNANCE_TRANSITIONS_POSSIBLE` |
| VIII-5 (AI) | v0.1 | ✅ CLOSED | `VIII5_PASS / AUTHORITY_INJECTION_POSSIBLE` |

---

## Appendix B: Invariants by Stage

| Invariant | Established In | Inherited By |
|-----------|----------------|--------------|
| Authority Opacity | VIII-0 | All |
| Identity Immutability | VIII-0 | All |
| Refusal-First Semantics | VIII-1 | VIII-2+ |
| Conflict Persistence | VIII-1, VIII-2 | VIII-3+ |
| Anti-Ordering | VIII-2 | VIII-3+ |
| VOID Irreversibility | VIII-2 | VIII-3+ |
| Temporal Governance | VIII-3 | VIII-4+ |
| Two-Phase Processing | VIII-3 | VIII-4+ |
| Governance Non-Amplification | VIII-4 | VIII-5 |
| No Kernel Decision | VIII-4 | VIII-5 |
| Content-Addressed Identity (injected only) | VIII-5 | — |
| Injection Lineage Constraint | VIII-5 | — |
| Determinism and Replayability | VIII-0 | All |

---

## Appendix C: File Inventory

```
src/phase_viii/
├── 0-AKR/
│   ├── src/           # kernel.py, structures.py
│   ├── runs/          # Run logs
│   └── docs/          # Preregistration, implementation report
├── 1-MPA/
│   ├── src/           # kernel.py, structures.py
│   ├── runs/          # Run logs
│   └── docs/          # Preregistration, implementation report
├── 2-DCR/
│   ├── src/           # kernel.py, structures.py
│   ├── runs/          # Run logs
│   └── docs/          # Preregistration, implementation report
├── 3-TG/
│   ├── src/           # kernel.py, structures.py
│   ├── runs/          # Run logs
│   └── docs/          # Preregistration, implementation report
├── 4-GT/
│   ├── src/           # kernel.py, structures.py
│   ├── runs/          # Run logs
│   └── docs/          # Preregistration, implementation report
├── 5-AI/
│   ├── src/           # kernel.py, structures.py, canonical.py, test_ai.py
│   ├── runs/          # Run logs
│   └── docs/          # Preregistration, implementation report
├── docs/
│   ├── AST-spec.md    # Authority State Transformation spec v0.2
│   ├── AEI-spec.md    # Authority Input Environment spec v0.1
│   └── phase_viii_project_report.md  # This document
```

---

## Appendix D: Licensed Claims

### VIII-0 (AKR-0) v0.1
> Authority-constrained execution is mechanically realizable under AST Spec v0.2 using a deterministic kernel without semantic interpretation, optimization, or fallback behavior.

### VIII-1 (MPA) v0.1
> Plural authority can be represented structurally without collapse, even when no action is admissible.

### VIII-2 (DCR) v0.1
> Authority destruction is the minimal resolution mechanism; deadlock correctly persists without destruction authorization.

### VIII-3 (TG) v0.1
> Authority can persist over time only via explicit renewal under open-system constraints; time does not resolve conflict or eliminate cost.

### VIII-4 (GT) v0.1
> Governance transitions can be represented as ordinary authority-bound transformations and either execute lawfully or fail explicitly without semantic privilege.

### VIII-5 (AI) v0.1
> New authority can be injected at the kernel boundary explicitly, structurally, and deterministically without violating conflict persistence, auditability, responsibility traceability, or non-privilege guarantees.

---

## Appendix E: Glossary

| Term | Definition |
|------|------------|
| **AAV** | Action Admissibility Vector — bitmask of permitted action types |
| **Authority** | Instantiated stateful object tracked by the kernel; the lawful capacity to bind action within a defined scope |
| **Authority Record** | Serialized input/state representation of an authority (including lineage, epochs, AAV) |
| **Authority State** | Complete inspectable representation of all authorities and conflicts |
| **Capability Core** | Fields determining authority identity (holder, scope, AAV, expiry) |
| **Conflict** | Registered dispute between authorities over a scope |
| **Deadlock** | State where no admissible action exists |
| **Epoch** | Discrete temporal unit for authority validity |
| **VOID** | Terminal authority status (destroyed, non-participant) |
| **PENDING** | Authority waiting for epoch boundary activation |
| **Lineage** | Provenance marker (VOID for injected, AuthorityID for created) |

---

**End of Phase VIII Project Report — GSA-PoC v0.1**
