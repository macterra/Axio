Below are **Round 4 binding answers (AD–AI)**. I’m keeping the system deterministic, replay-tight, and consistent with the **Step 0 boundary model** and **“no private keys in kernel”** constraint.

---

# AD — Step 0 & Activation Sequencing

## AD1. Suspension trigger uses which constitution?

**It uses the constitution as of the end of cycle c−1 (post–c−1 adoption).**

Reason: Step 0 runs at the start of cycle *c*, and its inputs are the **committed end-state of cycle c−1**. Amendments adopted in cycle c−1 are already part of that committed state and therefore part of the active constitutional frame at cycle c start.

So the suspension trigger (ACTIVE→SUSPENDED) is evaluated under:

* `EffectiveFrame_end_of(c−1)`.

No “start-of-cycle c−1” snapshot.

## AD2. How is prior-key zeroing represented?

Do **not** add `zeroed_keys: set`. That adds state you do not need and creates extra invariants to maintain.

Binding rule is simpler and stronger:

* Sovereign privileges are defined solely by `sovereign_public_key_active`.
* Anything that must be sovereign-signed is verified against `sovereign_public_key_active` (or against `prior_sovereign_public_key` only within SuccessionProposal gate S3/S4 for that cycle’s admission).

Post-activation “prior key privilege leak” is detected as:

* any artifact that claims sovereign authority and is signed by a key **≠ `sovereign_public_key_active`** is rejected (with the appropriate reason code for that artifact class).
* specifically, for attempts by the prior key to act as sovereign after activation, emit `PRIOR_KEY_PRIVILEGE_LEAK`.

This is an **interpretation rule**, not a blacklist.

## AD3. Cycle 1: commit verification or synthetic cycle 0 commit?

**Skip CycleCommit verification for cycle 1.** No synthetic cycle 0 commit.

Cycle 1 Step 0 does:

* verify `CycleStartPayload(1)` under genesis key
* initialize state from genesis artifact + pinned constitution + overlay + kernel_version_id

CycleCommit verification begins at cycle 2 Step 0, where `CycleCommitPayload(1)` exists.

---

# AE — Identity Chain Tip Hash

## AE1. How is `identity_chain_tip_hash` computed?

Confirm your proposed construction with a minor tightening:

Define a canonical “tip update payload”:

```
TipUpdatePayload = JCS({
  "type": "IdentityTip",
  "chain_length": L,
  "active_key": sovereign_public_key_active,
  "prior_tip_hash": prior_tip_hash,
  "succession_proposal_hash": <hash of admitted SuccessionProposal canonical payload>  # or null if none
})
```

Then:

* `identity_chain_tip_hash = SHA256(TipUpdatePayload)`

Genesis tip hash:

* `identity_chain_tip_hash_genesis = SHA256(JCS(genesis_artifact_without_hash_field))`

This gives you a chain tip hash that is:

* deterministic,
* lineage-linked,
* and sensitive to which succession artifact caused the transition.

## AE2. Does self-succession update `identity_chain_tip_hash`?

No. Self-succession is a lineage no-op.

* `identity_chain_tip_hash` unchanged
* `identity_chain_length` unchanged
* `pending_successor_key` unchanged

The admitted self-succession is visible only in the artifact/admission trace.

---

# AF — Harness Family Parameters

## AF1. Are all 7 families mandatory?

**Yes. All 7 are mandatory for the X-3 freeze-grade sweep.**

Rationale: each family corresponds to a distinct closure criterion bucket (lawful rotation, near-bound, churn interaction, suspension delay, multi-rotation, invalid signature rejection, duplicate-cycle rejection). If you don’t run them all, you are not actually testing the spec’s failure surface.

## AF2. Are the proposed defaults reasonable?

Yes — with two adjustments:

1. **X3-INVALID_SIG**: make it *one valid* rotation plus *one invalid attempt* in a different cycle (not the same cycle). Otherwise it interacts with the “one per cycle” rule and you’ll conflate `SIGNATURE_INVALID` with `MULTIPLE_SUCCESSIONS_IN_CYCLE`.

2. **X3-DUP_CYCLE**: ensure the duplicate is genuinely “same-cycle second candidate” so it deterministically hits `MULTIPLE_SUCCESSIONS_IN_CYCLE`, not `SIGNATURE_INVALID` or other.

Everything else is a good starting baseline.

## AF3. Boundary fault injection: dedicated family or mixed?

Dedicated. Create **one additional mandatory family**:

* **X3-INVALID_BOUNDARY**

Reason: boundary faults are qualitatively different from SuccessionProposal faults; mixing them into other families increases attribution ambiguity (you’ll get failures, but tracing becomes noisier and you risk masking true regressions).

So total families = **8**, mandatory.

---

# AG — Successor Key Generation

## AG1. Deterministic successor key derivation?

Confirm your proposal, with one requirement:

* use a fixed, documented KDF (e.g., HKDF-SHA256) rather than ad-hoc concatenation, to avoid accidental collisions or encoding bugs.

Binding scheme:

* `seed_i = HKDF_SHA256(ikm=session_seed, info="X3_SUCCESSOR_KEY", salt=rotation_index_bytes)`
* `successor_sk_i = Ed25519_from_seed(seed_i)`
* `successor_pk_i = derive_pk(successor_sk_i)`

## AG2. Precompute at start or lazy?

Either is fine **as long as derivation is logged reproducibly**.

Binding choice: **precompute at session start** for audit clarity, but do **not** log private keys or raw seeds.

Log only:

* the KDF scheme identifier
* the session seed commitment hash (not the seed)
* the list of successor public keys (or hashes of them)

That keeps replay deterministic without exposing secrets.

---

# AH — Verification Placement

## AH1. New `kernel_version_id` conflicts with X-2D?

No conflict.

X-2D runs continue to pin their own `kernel_version_id` (X-0E/X-2D regime). X-3 runs pin `rsa-replay-regime-x3-v0.1`.

They can coexist in the same test suite; they are simply different regimes.

## AH2. Does `policy_core_x3()` verify CycleCommit/CycleStart, or is that harness-only?

**Boundary verification is performed by the replay harness, not by `policy_core_x3()`.**

Reason: CycleCommit/CycleStart are harness-level records, not in-kernel artifacts. The kernel policy core should operate on intra-cycle buffered artifacts and state transitions. The replay harness:

* reconstructs state at cycle boundaries,
* verifies boundary signatures using the derived active sovereign public key,
* then calls `policy_core_x3()` for the cycle’s topological processing.

So inputs:

* `policy_core_x3()` receives the **already-verified** boundary-derived state (`sovereign_public_key_active`, `pending_successor_key`, etc.).
* The harness retains and verifies boundary records independently.

This preserves kernel purity and keeps verification logic centralized.

---

# AI — Density Checkpoints

## AI1. Density checkpoint function: full repair or assertion?

Full repair — same semantics as X-2D density repair, invoked at two checkpoints.

So at checkpoints A and B:

* compute effective density under the current ACTIVE treaty set
* if density exceeds bound:

  * deterministically apply the repair rule (whatever X-2D uses: remove newest grants first, or lexicographic eviction, etc.)
  * log repairs deterministically
* proceed only once density is within bound

No “assert-only” checkpoints.

## AI2. Density formula with suspension exclusion?

Yes: compute density exactly as X-2 does, but the set of grants considered is **ACTIVE only**.

* SUSPENDED grants are excluded from:

  * the authority-action pair set
  * the active authority set
  * any derived counts

This makes suspension a true “non-authorizing” state, not a hidden contributor.

---

## Net binding deltas introduced in Round 4

1. Cycle 1: no synthetic commit; start verification only.
2. No `zeroed_keys` set; sovereign privilege defined by active key equality.
3. Boundary verification is harness/replay responsibility, not inside `policy_core_x3()`.
4. Add mandatory family **X3-INVALID_BOUNDARY** (total 8).
5. Density checkpoints are full repair, invoked twice.

