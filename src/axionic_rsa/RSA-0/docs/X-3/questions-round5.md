# RSA X-3 — Follow-Up Questions (Round 5)

**Phase:** X-3 — Sovereign Succession Under Lineage
**Status:** Pre-implementation Q&A — Round 5
**Source:** Answers from Round 4 (`docs/X-3/answers-round4.md`)

---

## AJ — Prior Key Privilege Leak Detection

**AJ1.** AD2 says no `zeroed_keys` set; "prior key privilege leak" is detected by checking `signer != sovereign_public_key_active`. But AD2 also says to emit `PRIOR_KEY_PRIVILEGE_LEAK` specifically for attempts by the prior key. To emit that specific code (rather than a generic `SIGNATURE_INVALID`), the kernel needs to know which key is the *prior* sovereign. Proposed: add `prior_sovereign_public_key: Optional[str]` to `InternalStateX3` (set at activation, null when no succession has occurred). Gate logic: if signer == prior key → `PRIOR_KEY_PRIVILEGE_LEAK`; if signer == neither active nor prior → generic rejection. Confirm or specify an alternative.

**AJ2.** Does `PRIOR_KEY_PRIVILEGE_LEAK` apply only to SuccessionProposal attempts by the prior key, or also to TreatyRatification and TreatyGrant signed by the prior key? AD2 says "any artifact that claims sovereign authority" — this suggests all sovereign-signed artifact types. Confirm the full list.

---

## AK — X3-INVALID_BOUNDARY Family

**AK1.** AF3 adds X3-INVALID_BOUNDARY as the 8th mandatory family. Proposed parameters:

| Parameter | Value |
|-----------|-------|
| Cycles | 50 |
| Rotations | 1 valid at cycle 20 |
| Delegation mode | LOW |
| Boundary faults | 4 injections (one per fault class from Instructions §10.3) at cycles 21-24 |

Each fault class gets its own injection cycle:
  - Cycle 21: Wrong signer for CycleCommit (prior cycle)
  - Cycle 22: Wrong signer for CycleStart
  - Cycle 23: Missing `pending_successor_key` despite admitted proposal
  - Cycle 24: Non-null `pending_successor_key` without admitted proposal

All must fail with `BOUNDARY_SIGNATURE_MISMATCH`. Confirm or adjust.

**AK2.** Boundary faults are injected at the harness level (since boundary signatures are harness-produced). The kernel never sees these — boundary verification happens in the replay harness (per AH2). So boundary fault testing is purely a replay verification test, not a kernel admission test. Is this correct? If so, boundary faults cannot be tested via `policy_core_x3()` unit tests — only via session-level replay tests.

---

## AL — policy_core_x3 Function Signature

**AL1.** AH2 says `policy_core_x3()` receives "already-verified" boundary-derived state. Proposed function signature:

```python
def policy_core_x3(
    observations: List[Observation],
    action_candidates: List[CandidateBundle],
    amendment_candidates: List[AmendmentProposal],
    pending_amendment_candidates: List[PendingAmendment],
    treaty_grant_candidates: List[TreatyGrant],
    treaty_revocation_candidates: List[TreatyRevocation],
    treaty_ratification_candidates: List[TreatyRatification],
    delegated_action_candidates: List[DelegatedActionRequest],
    succession_candidates: List[SuccessionProposal],
    constitution: EffectiveConstitutionFrame,
    internal_state: InternalStateX3,
    repo_root: Path,
    schema: Optional[Dict] = None,
) -> PolicyOutputX3:
```

Key additions vs. `policy_core_x2`: `treaty_ratification_candidates`, `succession_candidates`, `EffectiveConstitutionFrame` type, `InternalStateX3` type. Confirm or adjust.

**AL2.** `PolicyOutputX3` — what new output fields are needed beyond `PolicyOutputX2`? Proposed:
  - `succession_admitted: Optional[SuccessionProposal]` (the admitted proposal, if any)
  - `succession_rejected: List[SuccessionRejection]` (rejected proposals with codes)
  - `ratifications_admitted: List[TreatyRatification]`
  - `ratifications_rejected: List[RatificationRejection]`
  - `suspension_events: List[SuspensionEvent]` (treaties moved to SUSPENDED)
  - `pending_successor_key: Optional[str]` (set if succession admitted)

Confirm or adjust.

---

## AM — Convergence Check

**AM1.** Across 4 rounds (162 questions), the following binding decisions are implementation-ready. Confirm this is the complete set of decisions needed before coding begins, or flag any remaining gaps:

1. Genesis: frozen artifact at `artifacts/phase-x/x3/genesis.v0.1.json`, one canonical keypair from `X3_GENESIS_SEED`, chain length starts at 1
2. Overlay: frozen JSON at `artifacts/phase-x/x3/x3_overlay.v0.1.json`, structured clauses, `overlay:<hash>#<id>` citation namespace, `EffectiveConstitutionFrame` wrapper
3. Kernel: `kernel/src/rsax3/` with artifacts_x3, succession_admission, treaty_ratification, policy_core_x3, state_x3; extends InternalStateX2
4. Ordering: X3_TOPOLOGICAL 12-step (Step 0 boundary → amendments → revalidation → succession → revocations → ratifications → density A → grants → density B → RSA actions → delegated actions → commit)
5. Boundary: harness signs CycleCommit/CycleStart, kernel never signs, replay harness verifies; every cycle produces both records; cycle 1 skips commit verification
6. Self-succession: no-op (no chain increment, no suspension, no pending key, consumes per-cycle slot, logged as admitted artifact)
7. Suspension: `suspended_grant_ids` in InternalStateX3, blocks new grants via `SUSPENSION_UNRESOLVED`, expired suspended grants auto-removed, suspended grants excluded from density
8. Ratification: kernel-level artifact, gates R0–R4, one per treaty, `ratify=false` → REVOKED, multiple per cycle allowed
9. Lineage: historical_sovereign_keys set for cycle detection, tip hash chain, no fork/cycle allowed
10. Signing: HKDF-SHA256 for successor key derivation, JCS-canonical payload excluding signature field
11. Families: 8 mandatory (BASE, NEAR_BOUND, CHURN, RAT_DELAY, MULTI_ROT, INVALID_SIG, DUP_CYCLE, INVALID_BOUNDARY)
12. Version: `kernel_version_id = rsa-replay-regime-x3-v0.1`
13. Composition: refactor X-2D sub-steps, X-3 wraps; harness calls policy_core_x3 directly
14. Density: full repair at both checkpoints, same algorithm as X-2D

---

## End of X-3 Follow-Up Questions Round 5 (8 questions across 4 sections AJ–AM)
