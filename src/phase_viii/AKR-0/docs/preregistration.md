# AKR-0 Preregistration

- **Project:** AKR-0 v0.1 — Authority Kernel Runtime Calibration
- **Phase:** VIII — Governance Stress Architecture (GSA-PoC)
- **Status:** PREREGISTERED
- **Date:** 2026-01-29
- **Authors:** Implementation by Opus, specification by Vesper/Morningstar

---

## 1. Purpose

This document preregisters the AKR-0 experiment parameters, schemas, and success criteria before implementation begins. All binding decisions from Q1–Q39 are consolidated here.

**Core Question:**
> Can authority-constrained execution be carried out deterministically, auditable refusal enforced, and deadlock recognized—without semantics, heuristics, optimization, or fallback?

---

## 2. Frozen Dependencies

| Dependency | Version | Status |
|------------|---------|--------|
| AST Spec | v0.2 | FROZEN |
| AIE Spec | v0.1 | FROZEN |
| AKR Spec | v0.1 | FROZEN |

---

## 3. Run Configuration

### 3.1 Conditions

| Condition | Description | Authority Injections/Epoch | Action Requests/Epoch | TransformationRequests/Epoch |
|-----------|-------------|---------------------------|----------------------|------------------------------|
| A | Valid Authority (positive control) | 20 | 20 | 0 |
| B | Authority Absence (negative control) | 0 | 20 | 5 |
| C | Conflict Saturation | 50 | 20 | 10 |

### 3.2 Run Parameters

| Parameter | Value |
|-----------|-------|
| Epochs per run | 100 |
| Seeds | {11, 22, 33, 44, 55} |
| Runs per condition | 5 |
| Total runs | 15 |
| Actions per run | 2,000 |
| Total actions | 30,000 |

### 3.3 Initial State

- All runs start with empty Authority State at epoch 0
- `currentEpoch = 0`
- `authorities = []`
- `conflicts = []`

---

## 4. Address Book and Scope Pool

### 4.1 Address Book (Fixed)

| Parameter | Value |
|-----------|-------|
| Cardinality | 16 |
| Format | `H0001` through `H0016` |

### 4.2 Scope Pool

| Parameter | Value |
|-----------|-------|
| Resources | `R0000` through `R2047` (2,048 resources) |
| Operations | `{READ, WRITE}` |
| Pool size (M) | 4,096 atomic scope elements |
| Scope size per authority | 1 (atomic) |

### 4.3 Collision Probability

For n=20 authorities per epoch:
$$P_c = 1 - \prod_{i=0}^{n-1}\frac{M-i}{M} \approx 0.045$$

---

## 5. PRNG

| Parameter | Value |
|-----------|-------|
| Algorithm | PCG32 |
| Stream ID | 0 |
| Seed source | Run seed (11, 22, 33, 44, 55) |

All randomness derived from single PRNG stream per run.

---

## 6. Gas Budgets

### 6.1 Per-Operation Budgets

| Operation | Gas Budget |
|-----------|------------|
| Action evaluation | 50,000 |
| Transformation | 100,000 |
| Epoch advance | 200,000 |

### 6.2 Gas Primitives

| Primitive | Cost |
|-----------|------|
| C_HASH | 50 |
| C_COMPARE | 1 |
| C_SET_MEM | 5 |
| C_SCAN_AR | 10 |
| C_UPDATE | 20 |
| C_LOG | 10 |

---

## 7. Canonical Schemas

### 7.1 Authority Record

```json
{
  "authorityId": "<AuthorityID>",
  "holderId": "<HolderID>",
  "origin": "<AIE:eventHash>",
  "scope": [["R0000", "READ"]],
  "status": "ACTIVE",
  "startEpoch": 0,
  "expiryEpoch": null,
  "permittedTransformationSet": [],
  "conflictSet": []
}
```

**AuthorityID rule:**
```
authorityId = "A:" + sha256(canonical_json(record_without_authorityId_and_conflictSet))
```

### 7.2 Authority State

```json
{
  "stateId": "<sha256>",
  "currentEpoch": 0,
  "authorities": [],
  "conflicts": []
}
```

### 7.3 Conflict Record

```json
{
  "conflictId": "<ConflictID>",
  "epochDetected": 0,
  "scopeElements": [["R0000", "READ"]],
  "authorityIds": ["A:...", "A:..."],
  "status": "OPEN"
}
```

**ConflictID rule:**
```
conflictId = "C:" + sha256(canonical_json({epochDetected, scopeElements, authorityIds}))
```

---

## 8. Event Schemas

### 8.1 EPOCH_TICK

```json
{
  "type": "EPOCH_TICK",
  "eventId": "<EventID>",
  "targetEpoch": 1
}
```

**EventID rule:** `eventId = "ET:" + sha256(canonical_json(event_without_eventId))`

### 8.2 AuthorityInjection

```json
{
  "type": "AuthorityInjection",
  "epoch": 0,
  "eventId": "<EventID>",
  "authority": {
    "authorityId": "<computed>",
    "holderId": "H0001",
    "origin": null,
    "scope": [["R0000", "READ"]],
    "status": "ACTIVE",
    "startEpoch": 0,
    "expiryEpoch": null,
    "permittedTransformationSet": [],
    "conflictSet": []
  }
}
```

**EventID rule:** `eventId = "EI:" + sha256(canonical_json(event_without_eventId))`

**Post-processing:**
1. Compute eventId
2. Set `authority.origin = "AIE:" + eventId_hash`
3. Recompute authorityId with filled origin

### 8.3 TransformationRequest

```json
{
  "type": "TransformationRequest",
  "epoch": 0,
  "requestId": "<RequestID>",
  "requesterHolderId": "H0001",
  "transformation": "REVOKE_AUTHORITY",
  "targets": {
    "authorityIds": ["A:..."],
    "scopeElements": null,
    "conflictIds": null
  }
}
```

**RequestID rule:** `requestId = "TR:" + sha256(canonical_json(event_without_requestId))`

### 8.4 ActionRequest

```json
{
  "type": "ActionRequest",
  "epoch": 0,
  "requestId": "<RequestID>",
  "requesterHolderId": "H0001",
  "action": [["R0000", "READ"]]
}
```

**RequestID rule:** `requestId = "AR:" + sha256(canonical_json(event_without_requestId))`

---

## 9. Canonical Ordering

1. Canonicalize each event as minified JSON per AST Appendix C
2. Compute `h = SHA256(canonical_json_bytes)`
3. Sort ascending by `(h_hex, canonical_json_lex)`
4. Duplicate events → `INVALID_RUN / DUPLICATE_EVENT`

---

## 10. PermittedTransformationSet Assignment

### 10.1 Condition A

| Percentage | PTS |
|------------|-----|
| 80% | `[]` |
| 20% | `["REVOKE_AUTHORITY", "RESOLVE_CONFLICT"]` |

### 10.2 Condition C

| Percentage | PTS |
|------------|-----|
| 50% | `[]` |
| 50% | `["REVOKE_AUTHORITY", "RESOLVE_CONFLICT"]` |

Assignment determined by PRNG stream (deterministic).

---

## 11. Condition C Conflict Density

**Target:** ≥30% of injected authorities collide per epoch

**Algorithm (per epoch, n=50):**
1. Choose k=15 "hot" scope elements via PRNG
2. Assign 2 authorities to each hot scope → 30 guaranteed collisions
3. Assign remaining 20 authorities to distinct "cold" scope elements

---

## 12. Transformation Admissibility

A TransformationRequest is admissible iff:
1. Requester has ≥1 ACTIVE authority with `holderId = requesterHolderId`
2. Requested transformation ∈ requester's `permittedTransformationSet`
3. Requester's scope includes exact affected scope elements
4. No conflicts/suspensions block the affected elements

---

## 13. Action Admissibility

An ActionRequest is admissible iff:
1. ≥1 ACTIVE authority exists binding the exact action scope
2. Authority's `holderId = requesterHolderId`
3. No OPEN conflict blocks the scope element
4. Authority is not SUSPENDED

---

## 14. Deadlock Detection

### 14.1 Conflict Deadlock
Conflicts block all admissible actions AND no destructive resolution is admissible.

### 14.2 Governance Deadlock
No admissible actions AND no admissible transformations that could change admissibility.

### 14.3 Entropic Collapse
`ASA == 0` (no active scope area) AND no admissible transformations to increase ASA.

**Deadlock terminates the run immediately.**

---

## 15. Kernel Outputs

| Output | Description |
|--------|-------------|
| ACTION_EXECUTED | Action completed under valid authority |
| ACTION_REFUSED | Action inadmissible |
| AUTHORITY_TRANSFORMED | State change from transformation |
| CONFLICT_REGISTERED | New conflict detected |
| DEADLOCK_DECLARED | Terminal deadlock detected |
| SUSPENSION_ENTERED | Gas exhaustion or bounded computation |

---

## 16. Logging

### 16.1 Format
- Append-only JSONL (one event per line)
- Hash chain: `eventHash = SHA256(prevEventHash || canonicalEventBytes)`

### 16.2 Log Types
- Pre-ordering log: raw harness emission sequence
- Post-ordering log: canonical sorted sequence

---

## 17. Replay Protocol

1. Load post-ordering log
2. Re-execute deterministically
3. Compare per-event:
   - State hash
   - Output
   - Event hash chain

**Divergence → `INVALID_RUN / NONDETERMINISTIC_EXECUTION`**

Divergence report includes:
- `divergenceEventIndex`
- `expectedEventHash` / `observedEventHash`
- `expectedStateHash` / `observedStateHash`
- `expectedOutput` / `observedOutput`

---

## 18. Success Criteria (AKR-0 PASS)

AKR-0 passes iff ALL of:
1. No action executes without authority
2. All inadmissible actions are refused
3. Conflicts block execution deterministically
4. Deadlocks are detected and classified
5. Replayability is bit-perfect
6. No semantic or heuristic logic is invoked

---

## 19. Failure Criteria (Terminal)

| Code | Description |
|------|-------------|
| `AKR_FAIL / UNGATED_EXECUTION` | Action without authority |
| `AKR_FAIL / ILLEGAL_TRANSFORMATION` | Transformation not in whitelist |
| `AKR_FAIL / CONFLICT_ARBITRATION` | Non-destructive conflict resolution |
| `AKR_FAIL / ILLEGAL_FALLBACK` | Heuristic or semantic fallback |
| `AKR_FAIL / STATE_INCOHERENCE` | State hash mismatch |
| `AKR_FAIL / UNBOUNDED_EVALUATION` | Computation exceeded budget |
| `INVALID_RUN / NONDETERMINISTIC_EXECUTION` | Replay divergence |
| `INVALID_RUN / GAS_BUDGET_UNSATISFIED` | Gas exhaustion mid-batch |
| `INVALID_RUN / DUPLICATE_EVENT` | Identical events in batch |
| `INVALID_RUN / EPOCH_DISCONTINUITY` | Non-sequential epoch tick |

---

## 20. Licensed Claim (if PASS)

> *Authority-constrained execution is mechanically realizable under AST Spec v0.2 using a deterministic kernel without semantic interpretation, optimization, or fallback behavior.*

**Scope qualifiers:**
- Valid only for declared AIE regime
- Valid only for PCG32 PRNG with specified seeds
- Valid only for scope pool M=4096, Address Book |H|=16
- No claims about governance success, stability, or desirability

---

## 21. File Structure

```
src/phase_viii/AKR-0/
├── docs/
│   ├── instructions.md
│   ├── AKR-spec.md
│   ├── AST-spec.md
│   ├── AEI-spec.md
│   ├── questions.md
│   ├── answers.md
│   └── preregistration.md  ← this file
├── src/
│   ├── kernel.py
│   ├── aie.py
│   ├── harness.py
│   ├── canonical.py
│   ├── pcg32.py
│   └── replay.py
├── logs/
│   └── (run logs)
└── results/
    └── (run results)
```

---

## 22. Attestation

This preregistration is binding. Any deviation from these parameters invalidates the run and requires re-preregistration.

---

**End of AKR-0 Preregistration — v0.1**
