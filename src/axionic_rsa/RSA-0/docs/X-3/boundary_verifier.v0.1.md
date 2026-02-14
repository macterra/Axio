# X-3 Boundary Verifier — Algorithmic Specification (v0.1)

**Phase:** X-3 — Sovereign Succession Under Lineage
**Status:** Frozen per Q&A AS1

---

## Overview

The boundary verifier runs at the harness level at the start of each cycle.
It is NOT inside `policy_core_x3()`. The kernel never signs boundary records
and never performs boundary verification. The harness signs and verifies.

---

## Inputs

- `committed_state`: `InternalStateX3` from end of prior cycle
- `cycle_commit_record`: `{payload: CycleCommitPayload, signature: hex}`
- `cycle_start_record`: `{payload: CycleStartPayload, signature: hex}`
- `succession_admitted_in_prior_cycle`: `bool`

---

## Algorithm (per cycle c ≥ 2)

### Step 1: Verify CycleCommit(c−1) Signature

```
expected_signer = committed_state.sovereign_public_key_active  (cycle c−1)
payload_bytes   = JCS(cycle_commit_record.payload)
valid           = Ed25519.verify(expected_signer, payload_bytes, signature)
if not valid:
    FAIL → BOUNDARY_SIGNATURE_MISMATCH
```

### Step 2: Verify Pending Successor State Consistency

```
if succession_admitted_in_prior_cycle:
    if cycle_commit_record.payload.pending_successor_key is null:
        FAIL → BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR
else:
    if cycle_commit_record.payload.pending_successor_key is not null:
        FAIL → BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR
```

### Step 3: Boundary Activation (if pending_successor_key present)

```
if committed_state.pending_successor_key is not null:
    prior_key                                = committed_state.sovereign_public_key_active
    committed_state.prior_sovereign_public_key = prior_key
    committed_state.sovereign_public_key_active = committed_state.pending_successor_key
    committed_state.pending_successor_key       = null

    # Suspend all ACTIVE grants
    for grant in committed_state.active_treaty_set.active_grants(cycle_id=c):
        committed_state.suspended_grant_ids.add(grant.id)

    # Update lineage
    committed_state.identity_chain_length += 1
    committed_state.identity_chain_tip_hash = SHA256(JCS({
        "type": "identity_chain_tip",
        "chain_length": committed_state.identity_chain_length,
        "active_key": committed_state.sovereign_public_key_active,
        "prior_tip_hash": <previous tip hash>,
        "succession_proposal_hash": <hash of admitted proposal from cycle c−1>
    }))

    # Record in historical keys for cycle detection (S5 gate)
    committed_state.historical_sovereign_keys.add(prior_key)
```

### Step 4: Verify CycleStart(c) Signature

```
expected_signer = committed_state.sovereign_public_key_active  (post-activation)
payload_bytes   = JCS(cycle_start_record.payload)
valid           = Ed25519.verify(expected_signer, payload_bytes, signature)
if not valid:
    FAIL → BOUNDARY_SIGNATURE_MISMATCH
```

### Step 5: Verify CycleStart(c) Chain/Frame Continuity

```
if cycle_start_record.payload.identity_chain_length != committed_state.identity_chain_length:
    FAIL → BOUNDARY_STATE_CHAIN_MISMATCH

if cycle_start_record.payload.identity_chain_tip_hash != committed_state.identity_chain_tip_hash:
    FAIL → BOUNDARY_STATE_CHAIN_MISMATCH

if cycle_start_record.payload.overlay_hash != committed_state.overlay_hash:
    FAIL → BOUNDARY_STATE_CHAIN_MISMATCH

if cycle_start_record.payload.sovereign_public_key_active != committed_state.sovereign_public_key_active:
    FAIL → BOUNDARY_STATE_CHAIN_MISMATCH
```

---

## Cycle 1 Special Case

- No CycleCommit verification (no prior cycle)
- Verify CycleStart(1) signature under genesis key only
- committed_state initialized from genesis artifact

---

## Self-Succession

Self-succession produces no activation, no suspension, no chain increment.
The CycleCommit has `pending_successor_key = null`.
CycleStart verifies normally under the same key.

---

## Failure Semantics

Any boundary verification failure is a hard stop. The session terminates
with the failure reason code in the `X3SessionEnd` artifact.

---

**End of Boundary Verifier Specification v0.1**
