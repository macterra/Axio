# RSA X-3 — Follow-Up Questions (Round 4)

**Phase:** X-3 — Sovereign Succession Under Lineage
**Status:** Pre-implementation Q&A — Round 4
**Source:** Answers from Round 3 (`docs/X-3/answers-round3.md`)

---

## AD — Step 0 & Activation Sequencing

**AD1.** Step 0 applies treaty suspension at activation (before amendment adoption at step 1). If an amendment was *adopted* in the prior cycle that changes treaty rules (e.g., tightens density bound), the suspension trigger runs under the *post-amendment* constitution (since the amendment was adopted in cycle c−1). Correct? Or does activation use the constitution snapshot from the *start* of cycle c−1 (before that cycle's own amendments)?

**AD2.** Step 0 says "enforce prior-key zeroing rule (state-level, not a step)." Concretely, how is zeroing represented in `InternalStateX3`? Is there a `zeroed_keys: set` that the kernel checks when evaluating succession proposals and ratifications (i.e., reject if signer is in `zeroed_keys`)? Or is the check simply `signer != sovereign_public_key_active`?

**AD3.** For cycle 1: there is no cycle 0 commit. The CycleStart for cycle 1 is verified under the genesis key, but there is no prior CycleCommit to verify. Does Step 0 skip CycleCommit verification for cycle 1, or does session initialization produce a synthetic "cycle 0 commit" (genesis anchor commit)?

---

## AE — Identity Chain Tip Hash

**AE1.** V2 includes `identity_chain_tip_hash: str` in `InternalStateX3`. How is this computed? Proposed: `identity_chain_tip_hash = SHA256(JCS({"chain_length": N, "public_key": active_key, "prior_tip_hash": prev_tip_hash}))`, where the genesis tip hash is `SHA256(JCS(genesis_artifact_without_hash_field))`. Confirm or define.

**AE2.** Does self-succession update `identity_chain_tip_hash`? Since self-succession produces no state change (no chain increment, no key change), the tip hash should remain unchanged. Confirm.

---

## AF — Harness Family Parameters

**AF1.** K1 mapped 7 buckets to families: X3-BASE, X3-NEAR_BOUND, X3-CHURN, X3-RAT_DELAY, X3-MULTI_ROT, X3-INVALID_SIG, X3-DUP_CYCLE. Should all 7 be run in every production profiling sweep (like X-2D's 5 mandatory families), or are some optional?

**AF2.** Proposed default parameters per family (adjust as needed):

| Family | Cycles | Rotations | Ratification Delay | Delegation Mode | Invalid Fractions |
|--------|--------|-----------|--------------------|-----------------|--------------------|
| X3-BASE | 50 | 1 at cycle 25 | 1 cycle | LOW | 0 |
| X3-NEAR_BOUND | 60 | 1 at cycle 30 | 1 cycle | NEAR_BOUND | 0 |
| X3-CHURN | 80 | 1 at cycle 40 | 2 cycles | CHURN_ACTIVE | 0 |
| X3-RAT_DELAY | 60 | 1 at cycle 20 | 5+ cycles | LOW | 0 |
| X3-MULTI_ROT | 80 | 3 at cycles 20,40,60 | 1 cycle | LOW | 0 |
| X3-INVALID_SIG | 50 | 1 valid + 1 invalid | 1 cycle | LOW | sig:0.5 |
| X3-DUP_CYCLE | 50 | 1 valid + 1 dup | 1 cycle | LOW | dup:0.5 |

Are these reasonable starting points?

**AF3.** Instructions §3.1 shows `invalid_boundary_fractions` on `X3SessionStart`. Instructions §10.3 lists 4 boundary fault classes: wrong cycle N commit signer, wrong cycle N+1 start signer, missing `pending_successor_key` despite admitted proposal, non-null `pending_successor_key` without admitted proposal. Should these be injected in dedicated families (e.g., X3-INVALID_BOUNDARY) or mixed into existing families? If dedicated, that brings the total to 8 families.

---

## AG — Successor Key Generation

**AG1.** How does the harness generate successor keypairs for rotation? Proposed: derive from `session_seed + rotation_index` (e.g., `successor_privkey = Ed25519_from_seed(SHA256(session_seed ‖ rotation_index))`). This makes all successor keys deterministic and reproducible. Confirm or specify an alternative derivation.

**AG2.** For X3-MULTI_ROT with 3 rotations: are the successor keys pre-computed at session start (so `X3SessionStart` can log them or their derivation is reproducible), or computed lazily at each rotation cycle?

---

## AH — Verification Placement

**AH1.** AA2 says `kernel_version_id = rsa-replay-regime-x3-v0.1`. X-2D sessions used the X-0E `kernel_version_id`. If X-3 changes the version, can X-2D families still run alongside X-3 families in the same test suite? Or does the version change mean X-2D tests need their own version pinning (they already have it — just confirming no conflict).

**AH2.** X1's step 11 says "Kernel verifies commit signature deterministically during replay." But F4 says kernel never holds private keys and only verifies. Verification requires the public key. During replay, the replayer reconstructs the active sovereign key from the lineage. Does `policy_core_x3()` receive the CycleCommit/CycleStart records as input parameters for verification, or does it only operate on intra-cycle artifacts (with boundary verification happening in the replay harness outside the kernel)?

---

## AI — Density Checkpoints

**AI1.** X1 answer says density checkpoints use "one function invoked twice." Is this the same `apply_constitutional_revalidation()` + density repair from X-2D, or a simpler bound-check-only function? In X-2D, density repair removes grants to bring density below bound. In X-3, the same repair logic should apply at checkpoints A and B. Confirm the density checkpoint is full repair (not just assertion).

**AI2.** When suspended grants are excluded from density (G6), the density denominator changes. Does effective density use the same formula as X-2 (`distinct (authority, action) pairs / |authorities| × |actions|`), counting only ACTIVE grants (not suspended)?

---

## End of X-3 Follow-Up Questions Round 4 (16 questions across 6 sections AD–AI)
