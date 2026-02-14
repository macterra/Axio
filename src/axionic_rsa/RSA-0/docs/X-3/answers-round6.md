## AN — Frozen Boundary Payload Schemas

### AN1. CycleCommitPayload with `identity_chain_tip_hash` instead of `identity_chain_tip_public_key`

**Confirm, with one small addition.**

You’re right: `identity_chain_tip_public_key` is redundant (it’s the active sovereign key for that cycle, which is either already in state or inferable from the signer). The **tip hash** is the stronger anchor and matches AE1.

**Binding CycleCommitPayload v0.1:**

```json
{
  "type": "CycleCommit",
  "cycle_id": "<int>",
  "kernel_version_id": "<string>",
  "state_hash_end": "<hex>",
  "state_hash_prev": "<hex>",
  "constitution_hash_tip": "<hex>",
  "pending_successor_key": "<ed25519:... | null>",
  "identity_chain_length": "<int>",
  "identity_chain_tip_hash": "<hex>",
  "overlay_hash": "<hex>"
}
```

**Why add `overlay_hash`?** Because your effective constitutional frame is `constitution v0.3 + overlay v0.1`, and S2 snapshotting depends on it. Boundary records should anchor the frame identity across replay. This is a “hash pointer,” not semantics.

Signature: Ed25519 over JCS(CycleCommitPayload).

### AN2. CycleStartPayload including `identity_chain_tip_hash`

**Confirm.** This makes CycleStart a continuity assertion, not merely “who signs now.”

**Binding CycleStartPayload v0.1:**

```json
{
  "type": "CycleStart",
  "cycle_id": "<int>",
  "kernel_version_id": "<string>",
  "state_hash_prev": "<hex>",
  "sovereign_public_key_active": "<ed25519:...>",
  "identity_chain_length": "<int>",
  "identity_chain_tip_hash": "<hex>",
  "overlay_hash": "<hex>"
}
```

Signature: Ed25519 over JCS(CycleStartPayload).

**Verifier rule:** CycleStart’s `identity_chain_*` fields must match the replay-reconstructed state after activation at Step 0. If not, fail with a boundary state mismatch code (not signature mismatch).

---

## AO — Suspension Placement Confirmation

### AO1. Is the one-cycle-delayed suspension model binding?

**Confirm, with one correction to your step list.**

Binding model:

* Cycle **c**, Step 3: succession admitted → `pending_successor_key` set (if non-self).

* Cycle **c**, Step 11: commit → CycleCommitPayload includes `pending_successor_key` and the **pre-activation** identity tip hash for cycle c.

* Cycle **c+1**, Step 0 (boundary activation, harness-level + state transition):

  1. Verify CycleCommit(c) signature under cycle c active sovereign.
  2. If `pending_successor_key` present in committed state:

     * `prior_sovereign_public_key = sovereign_public_key_active`
     * `sovereign_public_key_active = pending_successor_key`
     * `pending_successor_key = null`
     * **apply suspension**: move ACTIVE grants to `suspended_grant_ids`
     * **update lineage**:

       * `identity_chain_length += 1`
       * `identity_chain_tip_hash = H(tip_update_payload)` using AE1, with `succession_proposal_hash` from the admitted proposal in cycle c
  3. Verify CycleStart(c+1) signature under derived `sovereign_public_key_active(c+1)`.

* Cycle **c+1**, Step 5: ratification (kernel-level) operates on already-suspended set.

**Self-succession exception (binding):** no activation, no suspension, no chain increment, no tip-hash update.

This is intentional: it avoids “same-cycle abdication semantics” and keeps X-3 as a pure boundary transition.

---

## AP — policy_core_x3 and pending_amendment_candidates

### AP1. Confirm final policy_core_x3 signature (with PendingAmendment)

**Confirm as final.** Keeping `pending_amendment_candidates` is required if X-1 already models it distinctly and X-2 consumes it distinctly.

Final binding signature:

```python
def policy_core_x3(
    *,
    cycle_id: int,
    observations: List[Observation],
    amendment_candidates: List[AmendmentProposal],
    pending_amendment_candidates: List[PendingAmendment],
    succession_candidates: List[SuccessionProposal],
    treaty_revocation_candidates: List[TreatyRevocation],
    treaty_ratification_candidates: List[TreatyRatification],
    treaty_grant_candidates: List[TreatyGrant],
    delegated_action_candidates: List[DelegatedActionRequest],
    rsa_action_candidates: List[ActionRequest],
    constitution_frame: EffectiveConstitutionFrame,
    internal_state: InternalStateX3,
) -> PolicyOutputX3:
    ...
```

No further adjustments needed before coding, assuming the boundary verifier remains harness-level and policy_core_x3 does not accept boundary records as inputs.

---

