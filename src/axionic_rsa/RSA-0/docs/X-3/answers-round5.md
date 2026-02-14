## AJ — Prior Key Privilege Leak Detection

### AJ1. Do we need `prior_sovereign_public_key` in state to emit `PRIOR_KEY_PRIVILEGE_LEAK`?

**Confirm.** Add:

* `prior_sovereign_public_key: Optional[str]`

**State update rule (at activation in Step 0):**

* When consuming `pending_successor_key`:

  * `prior_sovereign_public_key = sovereign_public_key_active` (the key that was active in cycle c−1)
  * `sovereign_public_key_active = pending_successor_key`
  * `pending_successor_key = null`

**Classification rule (for any sovereign-signed artifact check):**

* If `signer == sovereign_public_key_active` → proceed with normal verification.
* Else if `prior_sovereign_public_key != null and signer == prior_sovereign_public_key` → reject with `PRIOR_KEY_PRIVILEGE_LEAK`.
* Else → reject with the artifact’s normal signature/authority failure code (typically `SIGNATURE_INVALID`).

No `zeroed_keys` set required.

### AJ2. Which artifact types trigger `PRIOR_KEY_PRIVILEGE_LEAK`?

Apply it to **all artifacts that require sovereign signature**, i.e. any artifact whose admissibility rule is “must be signed by active sovereign.”

In X-3 scope, at minimum:

* `SuccessionProposal`
* `TreatyRatification`

If your kernel model treats **TreatyGrant / TreatyRevocation** as sovereign-origin artifacts (i.e., grantor is the sovereign key), then **also**:

* `TreatyGrant`
* `TreatyRevocation`

If grants/revocations are instead admitted from non-sovereign sources (unlikely in your earlier phases, but possible), then `PRIOR_KEY_PRIVILEGE_LEAK` applies only where “sovereign signature required” is the gate.

**Binding simplification:** implement the check as a shared helper:

* `verify_active_sovereign_signature(payload, signature, signer_pk, state) -> {OK | PRIOR_KEY_PRIVILEGE_LEAK | SIGNATURE_INVALID}`

and use it wherever “active sovereign signature required” appears.

---

## AK — X3-INVALID_BOUNDARY Family

### AK1. Are the proposed parameters correct?

**Adjust.** Your proposed fault timing is slightly off because two of the four faults are *about a rotation boundary* and must be injected at the boundary they are meant to corrupt.

**Binding structure:**

* Choose a single rotation admitted in **cycle 20** (non-self).
* Activation happens at the **boundary between 20 and 21**.
* Therefore, the two signature faults should be injected on:

  * **CycleCommit(20)** (signed at end of cycle 20)
  * **CycleStart(21)** (signed at start of cycle 21)

The two state-consistency faults are about the `pending_successor_key` invariant and should be injected **for the same boundary** as well, otherwise they’re not testing the handoff zipper.

So:

* **Fault A:** wrong signer for `CycleCommitPayload(20)` (end of cycle 20)
* **Fault B:** wrong signer for `CycleStartPayload(21)` (start of cycle 21)
* **Fault C:** missing `pending_successor_key` in committed state of cycle 20 **despite** admitted succession in cycle 20
* **Fault D:** non-null `pending_successor_key` in committed state of cycle 20 **without** any admitted succession in cycle 20

Run these as **four separate sessions** inside the X3-INVALID_BOUNDARY family (or four subcases), not four different cycles in one session. Reason: a failing boundary should hard-stop deterministically; you don’t continue to cycle 22–24 after a boundary verification failure.

**Rejection code:**

* Fault A/B → `BOUNDARY_SIGNATURE_MISMATCH`
* Fault C/D → use a distinct code, not `BOUNDARY_SIGNATURE_MISMATCH`, because these are **state consistency** failures, not signature verification failures.

Add two codes:

* `BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR`
* `BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR`

This improves attribution and avoids overloading “signature mismatch” for non-signature faults.

### AK2. Are boundary faults purely replay-harness tests?

**Correct.** Boundary faults are harness-produced record faults and are validated by **the replay harness boundary verifier**.

Implications:

* You do not test them via `policy_core_x3()` unit tests.
* You test them via **session-level replay verification** (the same harness that checks boundary signatures before calling policy core for the cycle).

You can still unit-test the boundary verifier itself, but that’s a harness module test, not kernel admission.

---

## AL — policy_core_x3 Function Signature

### AL1. Confirm or adjust proposed signature

**Adjust for minimalism and determinism.**

Your signature is workable but over-parameterized. Prefer the same “buffered inputs” object approach used elsewhere: pass one `CycleInputsX3` bundle rather than 9 separate candidate lists.

If you want to keep list parameters, binding tweaks:

1. Remove `pending_amendment_candidates` unless your X-1 implementation truly separates “amendment candidates” vs “pending amendments” as distinct streams. If it does, keep it; otherwise this is confusion fodder.

2. Ensure the **ordering is enforced inside** `policy_core_x3`, not by caller ordering of args.

3. `schema` should not be passed into policy core unless policy core performs schema validation. Schema validation should be in the session gate / harness, not in policy core. So default binding: **omit `schema`** from policy core.

**Binding signature (list-based, close to yours):**

```python
def policy_core_x3(
    *,
    cycle_id: int,
    observations: List[Observation],
    amendment_candidates: List[AmendmentProposal],
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

Notes:

* `cycle_id` should be explicit (determinism, logging).
* Separate `rsa_action_candidates` from delegated requests (keeps action semantics clear).
* `repo_root` should not be required in policy core (I/O boundary). Logging happens outside or via injected logger interface.

### AL2. PolicyOutputX3 additions

**Mostly confirm, with two changes.**

1. Do not return `suspension_events` from policy core if suspension is applied in **Step 0** by the harness boundary activation logic (per Round 3/4). That event belongs to boundary handling, not intra-cycle policy.

2. Do not duplicate `pending_successor_key` in output; it’s already in `internal_state` after step 3, and will be committed in the end-state hash.

**Binding new fields in `PolicyOutputX3` beyond X2:**

* `succession_admission: Optional[SuccessionAdmissionRecord]`

  * includes proposal id/hash, admitted bool, reason code if rejected, and if admitted whether it is self/no-op
* `succession_rejections: List[SuccessionRejectionRecord]` (for all non-admitted proposals in the cycle)
* `ratification_admissions: List[RatificationAdmissionRecord]`
* `ratification_rejections: List[RatificationRejectionRecord]`

Everything else (warrants, executions, state hash inputs, treaty changes) should remain as in X-2 outputs.

---

## AM — Convergence Check

### AM1. Is the listed decision set complete for coding?

**Almost complete. Two remaining binding gaps to close before coding starts:**

1. **Boundary verifier code taxonomy**
   You currently have:

* `BOUNDARY_SIGNATURE_MISMATCH`
  but you also need explicit state-consistency codes (as per AK1):
* `BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR`
* `BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR`

Also decide whether a “wrong key derived from lineage” vs “signature invalid under correct key” are distinguished. My recommendation: keep one code for signature mismatch and two for state mismatch; don’t over-fragment.

2. **Exact payload schemas for CycleCommitPayload and CycleStartPayload**
   You defined them conceptually in Round 2. Freeze them now as:

* `cycle_commit_payload.v0.1.schema.json`
* `cycle_start_payload.v0.1.schema.json`

and pin their hashes under `artifacts/phase-x/x3/`.

This prevents drift in what is signed and verified.

Everything else in your AM1 list is sufficient and consistent.

---

### Updated AM1 list with the two additions

Add:

15. Boundary verifier codes: `BOUNDARY_SIGNATURE_MISMATCH`, `BOUNDARY_STATE_MISSING_PENDING_SUCCESSOR`, `BOUNDARY_STATE_SPURIOUS_PENDING_SUCCESSOR`
16. Frozen schemas for CycleCommitPayload and CycleStartPayload (hash-pinned artifacts)

With those, you’re genuinely at “start coding” readiness.
