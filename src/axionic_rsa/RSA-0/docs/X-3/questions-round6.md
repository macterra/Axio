# RSA X-3 — Follow-Up Questions (Round 6)

**Phase:** X-3 — Sovereign Succession Under Lineage
**Status:** Pre-implementation Q&A — Round 6
**Source:** Answers from Round 5 (`docs/X-3/answers-round5.md`)

---

## AN — Frozen Boundary Payload Schemas

Round 5 AM1 identified the frozen schemas for CycleCommitPayload and CycleStartPayload as a remaining gap. Round 1 F1 defined `identity_chain_tip_public_key` in CycleCommitPayload, but Round 4 AE1 introduced the richer `identity_chain_tip_hash = SHA256(JCS({type, chain_length, active_key, prior_tip_hash, succession_proposal_hash}))`. These encode different information.

**AN1.** Proposed frozen CycleCommitPayload:

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
  "identity_chain_tip_hash": "<hex>"
}
```

Key change from F1: replace `identity_chain_tip_public_key` with `identity_chain_tip_hash` (AE1 definition). Rationale: the tip hash encodes the full chain structure (length, active key, prior tip, succession proposal hash), whereas tip_public_key is just the current active key — already inferrable from the signer. The tip hash is the stronger anchor. Confirm or adjust.

**AN2.** Proposed frozen CycleStartPayload:

```json
{
  "type": "CycleStart",
  "cycle_id": "<int>",
  "kernel_version_id": "<string>",
  "state_hash_prev": "<hex>",
  "sovereign_public_key_active": "<ed25519:...>",
  "identity_chain_length": "<int>",
  "identity_chain_tip_hash": "<hex>"
}
```

Addition vs. S5: `identity_chain_tip_hash`. The start-of-cycle payload should anchor chain state so the boundary verifier can confirm chain continuity after activation. Without it, the CycleStart only asserts who the active key is, but not whether the chain transition was correctly computed. Confirm or adjust.

---

## AO — Suspension Placement Confirmation

**AO1.** Round 5 AL2 says suspension is applied "in Step 0 by the harness boundary activation logic." To confirm the full picture:

- Cycle c Step 3: succession admitted → `pending_successor_key` set in `InternalStateX3`
- Cycle c Step 11: commit → CycleCommitPayload includes `pending_successor_key`
- Cycle c+1 Step 0 (boundary activation, harness-level):
  1. `prior_sovereign_public_key = sovereign_public_key_active`
  2. `sovereign_public_key_active = pending_successor_key`
  3. `pending_successor_key = null`
  4. All ACTIVE grant IDs → `suspended_grant_ids`
  5. Update `identity_chain_tip_hash`
- Cycle c+1 Step 5 (ratification, kernel-level): new sovereign ratifies/rejects suspended grants

This means `policy_core_x3()` receives a state with suspensions already applied and never performs suspension itself. The one-cycle delay (succession admitted in c, suspension effective in c+1) is intentional. Confirm this is the binding model, or indicate if suspension should occur within Step 3 of the same cycle instead.

---

## AP — policy_core_x3 and pending_amendment_candidates

**AP1.** Round 5 AL1 says to remove `pending_amendment_candidates` "unless your X-1 implementation truly separates them." It does — X-1 defines `PendingAmendment` as a separate dataclass (in [artifacts_x1.py](../../kernel/src/rsax1/artifacts_x1.py)), and `policy_core_x2()` takes `pending_amendment_candidates: List[PendingAmendment]` as a distinct parameter from `amendment_candidates: List[AmendmentProposal]`. Keeping it is necessary for X-3. Confirmed binding signature with this inclusion:

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
```

Confirm this is final, or flag any remaining adjustments.

---

## End of X-3 Follow-Up Questions Round 6 (4 questions across 3 sections AN–AP)
