# Stage VIII-3 — Implementation Report

**Stage:** VIII-3 — Temporal Governance (Authority Over Time)
**Version:** v0.1
**Classification:** `VIII3_PASS / TEMPORAL_SOVEREIGNTY_POSSIBLE`
**Date:** 2026-02-03

---

## 1. Executive Summary

Stage VIII-3 tests whether authority can persist over time only via explicit expiry and renewal, without semantic reinterpretation, implicit ordering, or responsibility laundering.

**Result:** All 29 success criteria passed. Authority persistence over epochs requires explicit renewal; time does not resolve conflict or eliminate cost.

---

## 2. Experimental Configuration

| Parameter | Value |
|-----------|-------|
| Initial Epoch | 0 |
| Final Epoch | 6 |
| Max Event Index | 35 |
| Total Output Events (hashed) | 24 |
| Conditions Executed | A → B → C → D (cumulative) |
| Kernel Instances | 1 |
| Hash Chain | Verified |

---

## 3. Condition Results

### 3.1 Condition A — Expiry Without Renewal

**Purpose:** Test authority expiry mechanics (non-conflicting authorities)

| Step | Event | Output |
|------|-------|--------|
| 1-2 | AuthorityInjection (AUTH_A, AUTH_B) | (trace only) |
| 3 | ActionRequest (EXECUTE_OP0) | ACTION_EXECUTED |
| 4-5 | EpochAdvancement (0→1→2) | (trace only) |
| 6 | EpochAdvancement (2→3) | AUTHORITY_EXPIRED ×2, DEADLOCK_DECLARED |
| 8 | ActionRequest (EXECUTE_OP0) | ACTION_REFUSED |

**Criteria Met:**
- ✓ All authorities transitioned to EXPIRED at epoch 3
- ✓ ACTIVE_AUTHORITY_SET == ∅
- ✓ DEADLOCK_DECLARED with cause EMPTY_AUTHORITY
- ✓ DEADLOCK_PERSISTED on subsequent action
- ✓ All actions refused after expiry

### 3.2 Condition B — Renewal Without Conflict

**Purpose:** Test renewal restores admissibility for new scope

| Step | Event | Output |
|------|-------|--------|
| 1 | AuthorityRenewalRequest (AUTH_C) | AUTHORITY_RENEWED |
| 2 | ActionRequest (R0001/OP1) | ACTION_EXECUTED |
| 3 | ActionRequest (R0000/OP0) | ACTION_REFUSED |

**Criteria Met:**
- ✓ Renewal creates new AuthorityID (AUTH_C)
- ✓ AUTHORITY_RENEWED emitted with correct metadata
- ✓ Admissibility restored for new scope
- ✓ Actions on expired scope still refused
- ✓ Expired authority records persist with metadata

### 3.3 Condition C — Renewal After Destruction

**Purpose:** Test renewal from VOID authority (non-resurrective)

| Step | Event | Output |
|------|-------|--------|
| 1-2 | AuthorityInjection (AUTH_D, AUTH_DX) | (trace only) |
| 3 | ActionRequest (OP2) | ACTION_REFUSED (C:0001), DEADLOCK_DECLARED |
| 4-5 | DestructionAuthorization (conflictId=C:0001) ×2 | AUTHORITY_DESTROYED ×2 |
| 6 | AuthorityRenewalRequest (AUTH_E from AUTH_D) | AUTHORITY_RENEWED |
| 7 | ActionRequest (OP2) | ACTION_EXECUTED |

**Criteria Met:**
- ✓ Conflict record created between AUTH_D and AUTH_DX
- ✓ Both AUTH_D and AUTH_DX transitioned to VOID
- ✓ AUTH_E created as ACTIVE via renewal
- ✓ Renewal references AUTH_D (existence validated)
- ✓ AUTH_D remains VOID (non-resurrective)
- ✓ Post-renewal action executes (no conflicting ACTIVE authority)

### 3.4 Condition D — Renewal Under Ongoing Conflict

**Purpose:** Test renewal does not confer priority or resolve conflict

| Step | Event | Output |
|------|-------|--------|
| 1-2 | AuthorityInjection (AUTH_F, AUTH_G) | (trace only) |
| 3 | ActionRequest (OP3) | ACTION_REFUSED (C:0002) |
| 4 | (Kernel) | DEADLOCK_DECLARED |
| 5 | EpochAdvancement (3→6) | AUTHORITY_EXPIRED (AUTH_G) |
| 6 | AuthorityRenewalRequest (AUTH_H from AUTH_G) | AUTHORITY_RENEWED |
| 7 | ActionRequest (OP3) | ACTION_REFUSED (C:0003) |

**Criteria Met:**
- ✓ Original conflict C:0002 becomes OPEN_NONBINDING (AUTH_G expired)
- ✓ New conflict C:0003 registered between AUTH_F and AUTH_H
- ✓ Action refused despite renewal (no priority inference)
- ✓ No "newest wins" logic applied

---

## 4. Authority State Summary

| Authority | Status | Metadata |
|-----------|--------|----------|
| AUTH_A | EXPIRED | ExpiryMetadata (epoch 3) |
| AUTH_B | EXPIRED | ExpiryMetadata (epoch 3) |
| AUTH_C | ACTIVE | RenewalMetadata (prior=null) |
| AUTH_D | VOID | DestructionMetadata (C:0001) |
| AUTH_DX | VOID | DestructionMetadata (C:0001) |
| AUTH_E | ACTIVE | RenewalMetadata (prior=AUTH_D) |
| AUTH_F | ACTIVE | — |
| AUTH_G | EXPIRED | ExpiryMetadata (epoch 6) |
| AUTH_H | ACTIVE | RenewalMetadata (prior=AUTH_G) |

---

## 5. Conflict State Summary

| Conflict | Participants | Status |
|----------|--------------|--------|
| C:0001 | {AUTH_D, AUTH_DX} | OPEN_NONBINDING |
| C:0002 | {AUTH_F, AUTH_G} | OPEN_NONBINDING |
| C:0003 | {AUTH_F, AUTH_H} | OPEN_BINDING |

> **Note:** Conflict IDs are allocated monotonically across the cumulative run; hence Condition D begins at C:0002 (C:0001 was allocated in Condition C).

---

## 6. Global Criteria Verification

| # | Criterion | Status |
|---|-----------|--------|
| 21 | Determinism and bit-perfect replay | ✓ |
| 22 | Monotonic epoch progression (0 → 6) | ✓ |
| 23 | Finite expiry enforced | ✓ |
| 24 | No kernel-initiated renewal | ✓ |
| 25 | No implicit ordering from timing/metadata | ✓ |
| 26 | No implicit resolution by time | ✓ |
| 27 | Complete responsibility trace | ✓ |
| 28 | No AuthorityID reuse | ✓ |
| 29 | Hash chain integrity | ✓ |

---

## 7. Key Implementation Details

### 7.1 Two-Phase Processing

Per prereg §8, each step batch processes:
1. **Phase 1:** Epoch advancement with eager expiry
2. **Phase 2:** Renewals → Destructions → Actions

### 7.2 Conflict Status Transitions

Per prereg §9.1:
- `OPEN_BINDING → OPEN_NONBINDING` when any participant becomes non-ACTIVE
- Conflict records are persistent (never deleted)

**Important distinction:** Expiry does not *resolve* conflict; it removes a participant from admissibility evaluation, and the conflict record persists as OPEN_NONBINDING. This is why Condition D's C:0002 becomes nonbinding but a new conflict C:0003 forms when AUTH_H (renewal of AUTH_G) re-enters the contested scope.

### 7.3 Deadlock Cause Recomputation

Per prereg §10.3:
- `deadlock_cause` is recomputed at each emission
- Causes: CONFLICT, EMPTY_AUTHORITY, MIXED

### 7.4 Trace-Only Events

Per prereg §6.1 and §13:
- Authority injection consumes event index but produces no output
- Epoch advancement consumes event index but produces no output (only expirations produce output)
- Trace markers excluded from hash chain

---

## 8. Files Created

```
/home/david/Axio/src/phase_viii/3-TG/
├── docs/
│   └── preregistration.md (FROZEN)
└── src/
    ├── structures.py    # Data structures with EXPIRED, ExpiryMetadata
    ├── canonical.py     # Canonical JSON and hashing
    ├── kernel.py        # TGKernel with two-phase processing
    ├── harness.py       # Event generators for Conditions A-D
    ├── logger.py        # Trace markers and hash chain
    ├── run_tg.py        # Experiment runner
    └── logs/            # Execution logs
```

---

## 9. Licensed Claim

> *Authority can persist over time only via explicit renewal under open-system constraints; time does not resolve conflict or eliminate cost.*

---

## 10. Classification

```
VIII3_PASS / TEMPORAL_SOVEREIGNTY_POSSIBLE
```

All four conditions (A, B, C, D) passed. All 29 success criteria satisfied.

---

## Appendix A: Verification Bundle

### Prereg Document
| Field | Value |
|-------|-------|
| Hash (SHA-256) | `c1081fc0668e693343a83a342cb4f5ff20ab2ee0885d283e7e37d48b61fd9eb6` |
| Freeze Timestamp | `2026-02-03T00:00:00Z` |

### Run Artifacts
| Field | Value |
|-------|-------|
| Final State Hash | `eab2ac3594023e6b896ec5d2d09aaab592f4bb3185dfe85d4f528d9acaf6fcb3` |
| Hash Chain Head | `bbd1e36bfc3fe615298f1374de96d1a18773fa8293f82a27951947928eca6ca0` |
| Hash Chain Length | 24 |
| Final Epoch | 6 |
| Classification | `VIII3_PASS` |

### Condition D Log Excerpt

```
[29] ACTION_REFUSED
      conflict_id: C:0002
      reason: CONFLICT_BLOCKS
      request_id: AR:007

[30] DEADLOCK_DECLARED
      deadlock_cause: CONFLICT
      open_conflicts: [C:0002]

[32] AUTHORITY_EXPIRED
      authority_id: AUTH_G
      -- C:0002 transitions to OPEN_NONBINDING (AUTH_G no longer ACTIVE)
      -- Deadlock condition cleared: no OPEN_BINDING conflicts remain

[33] AUTHORITY_RENEWED
      new_authority_id: AUTH_H
      prior_authority_id: AUTH_G

[34] ACTION_REFUSED
      conflict_id: C:0003 (NEW: {AUTH_F, AUTH_H})
      reason: CONFLICT_BLOCKS
      request_id: AR:008

[35] DEADLOCK_DECLARED
      deadlock_cause: CONFLICT
      open_conflicts: [C:0003]
```

**Deadlock Sequence Explanation:**

1. **[30]** First deadlock declared for C:0002 (AUTH_F permits, AUTH_G denies)
2. **[32]** AUTH_G expires → C:0002 becomes OPEN_NONBINDING → deadlock condition no longer holds (lawful exit)
3. **[34-35]** AUTH_H (renewal of AUTH_G) re-enters contested scope → NEW conflict C:0003 → fresh DEADLOCK_DECLARED

The second DEADLOCK_DECLARED is correct: it's a *new* deadlock from a *new* conflict, not persistence of the original. The original deadlock was lawfully exited when its sole denying participant expired.

**Conflict State Snapshots:**

| After Event | C:0002 | C:0003 |
|-------------|--------|--------|
| [30] | OPEN_BINDING {AUTH_F, AUTH_G} | — |
| [32] | OPEN_NONBINDING {AUTH_F, AUTH_G*} | — |
| [34] | OPEN_NONBINDING | OPEN_BINDING {AUTH_F, AUTH_H} |

*AUTH_G marked EXPIRED at this point.

**Interpretation:** The jump from C:0002 to C:0003 confirms renewal did not inherit or transfer the conflict; a fresh conflict was registered when the renewed authority (AUTH_H) re-entered the contested scope.

### Canonicalization
| Property | Value |
|----------|-------|
| Hash Algorithm | SHA-256 |
| JSON Canonicalization | AST Appendix C (minified, sorted keys, no floats) |
| Hash Chain Formula | `H[i] = SHA256( ascii_hex(H[i-1]) \|\| canonical_json_bytes(output[i]) )` |
| Genesis Hash | `"0" × 64` (64-char ASCII string of zeros) |

**Clarification:** `ascii_hex(H[i-1])` means the 64-character lowercase hexadecimal ASCII encoding of the previous hash, not the raw 32-byte digest. This is the actual implementation in `compute_hash_chain_entry()`:

```python
def compute_hash_chain_entry(prev_hash: str, event_bytes: bytes) -> str:
    combined = prev_hash.encode('utf-8') + event_bytes  # prev_hash is hex string
    return sha256_hex(combined)
```

**Test Vector (Output [1] → Hash Chain [1]):**
- Genesis: `0000000000000000000000000000000000000000000000000000000000000000`
- Output[1]: `{"details":{"request_id":"AR:001","transformation_type":"EXECUTE_OP0"},"eventIndex":4,"outputType":"ACTION_EXECUTED","stateHash":"a96d7c3a144a5b824ad235e339b4e3330f25847aca885c0705562ae0a6e2da86"}`
- H[1] = `d99484d774cb0e400c3f417a7cdb0c6fd75d30acaf1afa292bf79e3967a90229`

---

## Appendix B: Criteria-to-Condition Mapping

For auditability, the 29 success criteria from the preregistration map as follows:

| Criteria | Condition | Description |
|----------|-----------|-------------|
| 1–5 | A | Expiry mechanics, EMPTY_AUTHORITY deadlock |
| 6–10 | B | Renewal creates new ID, restores admissibility |
| 11–16 | C | Destruction + renewal, non-resurrective semantics |
| 17–20 | D | Ongoing conflict, no "newest wins" logic |
| 21–29 | Global | Determinism, monotonicity, trace completeness, hash chain |

---

**End of Implementation Report — Stage VIII-3 v0.1**
