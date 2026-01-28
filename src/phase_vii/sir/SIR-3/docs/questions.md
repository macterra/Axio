# SIR-3 v0.1 Questions

**Status:** AWAITING PRINCIPAL RULING
**Date:** 2026-01-27

---

## Context

These questions arise from reviewing:
- `spec.md` — SIR-3 v0.1 Specification (Full Draft)
- `instructions.md` — Implementor Instructions

SIR-3 tests **global provenance integrity under compositional attack**.

---

## Q1: Provenance Chain Schema

The spec requires "a single continuous ancestor–descendant chain terminating at one trusted root."

**Question:** What is the minimal provenance chain structure for SIR-3?

Options:
1. **Single-link:** Claim → Root_Authority signature (same as SIR-0/SIR-1/SIR-2)
2. **Two-link:** Claim → Intermediate_Authority → Root_Authority
3. **Variable-depth:** Chain depth varies by claim type or condition

If (1), how do we test "truncated provenance" (Condition B) or "mixed-root assembly" (Condition C)?

---

## Q2: Ancestry Schema Definition

The spec states claims must include "ancestry-referenced" and requires "all predecessor artifacts required by the law-defined minimal ancestry schema."

**Question:** What does the law-defined minimal ancestry schema contain?

Proposal:
```
ProvenanceChain:
  claim_id: str
  chain: List[ChainLink]

ChainLink:
  signer_id: str
  delegated_from: str | None  # Parent signer (None for root)
  scope_grant: str            # Scope authorized by this link
  epoch: int
  signature: bytes
  signed_message_hash: str
```

Is this correct, or should ancestry be represented differently?

---

## Q3: Root of Trust Semantics

The spec mentions "the law-defined root of trust" (singular) but SIR-2 has two trusted roots (Root_Authority, Delegate_Authority).

**Question:** For SIR-3:
1. Is there exactly one root of trust (Root_Authority only)?
2. Are there two roots (Root_Authority + Delegate_Authority)?
3. Can Delegate_Authority be a non-root intermediate that derives from Root_Authority?

Option (3) would enable testing "mixed-root" attacks where fragments claim different ultimate roots.

---

## Q4: Scope Binding to Signature

The spec states: "The scope identifier must be cryptographically covered by the issuer's signature."

**Question:** How is scope binding verified?

Options:
1. **Included in signed message:** The scope is part of the message hash that was signed
2. **Explicit scope certificate:** A separate signed scope-grant artifact
3. **Chain-embedded:** Each ChainLink contains the scope it authorizes, signed by that link's signer

Current SIR-0/SIR-1/SIR-2: scope is part of claim, signed by signer. Is this sufficient, or must the chain explicitly show scope delegation?

---

## Q5: Condition B — Truncated Provenance

The spec requires testing "missing one or more required ancestor artifacts."

**Question:** Given the current single-link provenance (Claim → Root), what constitutes truncation?

Options:
1. **Missing signature:** Claim present but artifact (signature) is null/empty
2. **Missing chain link:** Multi-link chain with intermediate link omitted
3. **Missing root attestation:** Claim signed by intermediate, but intermediate's delegation from root is absent

Which option should Condition B test? If (2) or (3), we need a multi-link provenance schema.

---

## Q6: Condition C — Mixed-Root Assembly

The spec requires testing "provenance fragments issued by different trusted roots."

**Question:** How do we construct a mixed-root claim?

Proposal:
- Claim body signed by one root (e.g., Root_Authority)
- Scope grant signed by different root (e.g., Delegate_Authority as independent root)
- Global validation fails because the chain doesn't unify to a single root

Is this the intended attack vector, or should the attack be structured differently?

---

## Q7: Condition D — Scope Laundering

The spec states: "Valid issuer and signature, scope copied from unrelated valid claim."

**Question:** How is scope laundering implemented?

Proposal:
- Adversary observes a valid claim with scope `SCOPE/ENV/SHORTCUT_UNLOCK`
- Adversary creates a new claim with:
  - Valid signature from Unknown_Signer (not trusted)
  - Scope field copied verbatim from the observed valid claim
- Validation fails because signature doesn't cover the scope properly

Or is the attack more sophisticated (e.g., valid signature but scope not in signed message)?

---

## Q8: Epoch Consistency in Provenance Chains

The spec requires: "All provenance elements are valid in the same authority epoch."

**Question:** For Condition E (Epoch-Consistent Forgery):
1. Does the claim's epoch match current epoch?
2. Does the provenance chain have mismatched epochs within itself?
3. Or is the epoch correct but the chain is structurally invalid?

Please clarify what makes Condition E distinct from Conditions B/C/D.

---

## Q9: Environment and Gated Actions

The spec states SIR-3 reuses "CalibMazeV010-SIR2 without modification" and inherits `OPEN_SHORTCUT` and `GRANT_TRAVERSE_N5`.

**Question:** Confirm environment parameters:
- K = 6 steps (same as SIR-2)?
- Epoch transition at step 3→4?
- Both gated actions available at N2?

Or should we use K = 5 steps (SIR-1 style) since we're not testing epoching per se?

---

## Q10: Run Matrix

The spec defines 6 conditions (A through F).

**Question:** Confirm the run matrix:
- Seeds: [41, 137, 1009] (3 seeds)?
- Total runs: 6 conditions × 3 seeds = 18 runs?

---

## Q11: Verification Checks

**Question:** What verification checks are required for SIR-3?

Proposal based on spec:
1. `CHECK_NO_PARTIAL_FORGERY_VALID` — No forgery classified as VALID
2. `CHECK_NO_FORGERY_EFFECT` — No forgery produces any effect
3. `CHECK_LEGITIMATE_AUTHORITY_FUNCTIONAL` — Valid claims produce effects
4. `CHECK_RESPONSIBILITY_SINGLETON` — Attribution remains sharp
5. `CHECK_NO_SEMANTIC_LEAKAGE` — No forgery content reaches justification
6. `CHECK_MIXED_STREAM_STABLE` — Condition F maintains enforcement
7. `CHECK_TRUNCATED_REJECTED` — Condition B claims rejected
8. `CHECK_MIXED_ROOT_REJECTED` — Condition C claims rejected
9. `CHECK_SCOPE_LAUNDERING_REJECTED` — Condition D claims rejected
10. `CHECK_EPOCH_FORGERY_REJECTED` — Condition E claims rejected

Is this complete, or are additional checks required?

---

## Q12: Global Provenance Validation Implementation

**Question:** Where should global provenance validation be implemented?

Options:
1. **In the classifier:** Extend `ClaimClassifier` with provenance chain validation
2. **In the enforcement gate:** Validate at effect time
3. **Both:** Classifier rejects incomplete chains, gate validates full chain

The spec suggests classification is where global provenance is checked. Confirm this is the sole location.

---

## Q13: Forgery Construction Authority

**Question:** Who constructs the partial provenance forgeries?

Options:
1. **Harness:** The test harness constructs forged claims with specific defects
2. **Adversary module:** A separate adversary module creates claims
3. **Pre-generated:** Forged claims are frozen artifacts before execution

For reproducibility, I propose (1) with deterministic construction based on seed.

---

## Q14: Signature Validity of Forgeries

The spec states adversary "may submit claims that are cryptographically valid."

**Question:** For forgeries:
1. Should signatures be cryptographically valid (but from wrong signer)?
2. Should signatures be invalid (malformed)?
3. Or should signatures be valid from Unknown_Signer (untrusted root)?

The spec suggests forgeries pass local validation but fail global. This implies valid signatures from valid actors, but invalid chains.

---

## Q15: Delegate Authority Role in SIR-3

SIR-2 introduced Delegate_Authority as a revocable trusted signer.

**Question:** What is Delegate_Authority's role in SIR-3?
1. **Same as SIR-2:** A trusted signer that can be revoked
2. **Intermediate authority:** Derives from Root_Authority via delegation
3. **Not used:** Only Root_Authority for SIR-3

If (2), this enables testing multi-link chains and mixed-root attacks.

---

## Summary

Key clarifications needed:
1. Provenance chain depth and schema
2. Root of trust count and delegation model
3. Specific attack construction for each condition
4. Environment parameters (K, epoch transitions)
5. Verification checks

Awaiting principal rulings before preregistration.

---

# Follow-Up Questions (Round 2)

**Status:** AWAITING PRINCIPAL RULING  
**Date:** 2026-01-27

Based on answers R0–R15, the following clarifications are needed:

---

## F1: Root_Buthority Identity

R6 introduces `Root_Buthority` as an untrusted root for mixed-root attacks.

**Question:** How is Root_Buthority instantiated?

Options:
1. **Runtime-generated:** Generate a new keypair at harness startup, not in trusted_roots
2. **Pre-frozen artifact:** Include in frozen artifacts with known pubkey but not trusted
3. **Synthetic identity:** Use a hardcoded "adversarial root" pattern

Proposal: Option (1) with the key logged but never added to trusted_roots.

---

## F2: Delegate_Authority_A vs Delegate_Authority_B

R6 and R8 mention `Delegate_Authority_A` and `Delegate_Authority_B` as distinct delegates.

**Question:** How many delegate identities exist in SIR-3?

Options:
1. **One delegate (Delegate_Authority):** All conditions use the same delegate, invalidity comes from chain structure
2. **Two delegates:** Delegate_Authority_A (valid, delegated from Root_Authority) and Delegate_Authority_B (valid signature capability but not delegated from Root_Authority)
3. **Per-condition delegates:** Different delegate identities for different forgery scenarios

Proposal: Option (2) — two delegates, both with valid signing keys, but only A has a valid delegation from Root_Authority.

---

## F3: Delegation Artifact Persistence

R2 defines the Delegation artifact schema.

**Question:** When is the Delegation artifact created and where is it stored?

Options:
1. **Per-episode:** Delegation created fresh at episode start, persists for episode
2. **Frozen artifact:** Delegation is a frozen preregistration artifact
3. **Per-step:** Delegation regenerated each step

Proposal: Option (2) — freeze a valid Delegation artifact that grants both gated scopes to Delegate_Authority for all epochs used in the experiment.

---

## F4: Delegation Scope Set

R2 shows `scope_set: List[str]` in the Delegation artifact.

**Question:** For the legitimate Delegation artifact, what scopes are included?

Proposal:
```
scope_set = [
  "SCOPE/ENV/SHORTCUT_UNLOCK",
  "SCOPE/ENV/TRAVERSE_N5"
]
```

This allows Delegate_Authority to authorize both gated actions. Confirm or amend.

---

## F5: ProvenanceBundle Presentation

R2 defines `ProvenanceBundle` with `claim` and `delegation` fields.

**Question:** How does the ProvenanceBundle reach the classifier?

Options:
1. **Extended claim artifact:** The claim's artifact field contains serialized bundle
2. **Separate channel:** Delegation artifacts maintained in L-state, claims reference by ID
3. **Bundled transmission:** Both artifacts presented together at ingress

Proposal: Option (3) — the harness presents `(claim, delegation)` pairs to the classifier. The classifier validates the bundle as a unit.

---

## F6: Condition A — Legitimate Provenance Details

**Question:** For Condition A (control), confirm the exact structure:

Proposal:
- Fresh Delegation from Root_Authority → Delegate_Authority granting both scopes
- Claim from Delegate_Authority referencing the delegation, requesting a gated action
- Both signatures valid, chain complete, scope in scope_set

Is this correct?

---

## F7: Condition F — Mixed Stream Composition

R10 confirms 6 conditions × 3 seeds = 18 runs.

**Question:** For Condition F (mixed stream), what is the claim composition per step?

Options:
1. **Alternating:** Step 1 legit, step 2 forgery, step 3 legit, ...
2. **Parallel:** Each step receives both a legitimate and a forged claim
3. **Ratio-based:** 1 legitimate per step, N forgeries per step (e.g., 3:1)

Proposal: Option (2) — each step receives one legitimate ProvenanceBundle and one forged ProvenanceBundle. The legitimate should produce effects; the forged should be rejected.

---

## F8: claim.effect Field

R2 shows `effect: str` in the AuthorityClaim schema (e.g., `OPEN_SHORTCUT`).

**Question:** Is `effect` a new field, or is it the same as the existing `scope` field semantics?

Current SIR-0/1/2: claims have `scope` which implicitly maps to an effect. R2 seems to separate:
- `scope` = authorization namespace
- `effect` = specific action requested

Proposal: Add `effect` as a separate field. The enforcement gate checks:
1. `claim.scope ∈ delegation.scope_set`
2. `claim.effect` maps to the gated action
3. `claim.scope` matches the action's required scope

Confirm this interpretation.

---

## F9: Delegation Epoch Binding

R2 shows the Delegation has an `epoch` field.

**Question:** How does epoch binding work for delegations?

Options:
1. **Single epoch:** Delegation valid only in the epoch specified
2. **Range:** Delegation valid from not_before_step to not_after_step across any epoch
3. **All epochs:** Delegation is epoch-agnostic, only claim epoch matters

Proposal: Option (1) — Delegation specifies the epoch it's valid for. Claims must match. For SIR-3, we freeze delegations for epoch 0 and epoch 1.

---

## F10: Condition B — Truncated Delegation ID

R5 states Condition B has a claim with `delegation_id` referencing a missing delegation.

**Question:** Is the `delegation_id` value:
1. A valid ID that exists in law-state but not in the bundle?
2. A fabricated ID that never existed?
3. Null/empty?

Proposal: Option (2) — a plausible but fabricated delegation_id. The classifier cannot find a matching delegation, so it fails completeness.

---

## F11: Key Registry Extension

SIR-3 introduces new identities: Root_Buthority, Delegate_Authority_B.

**Question:** Should these keys be added to the key_registry.json, or kept separate?

Proposal: Add to key_registry.json with a field `trusted: false` to distinguish them. Only `Root_Authority` has `trusted: true` as the sole root.

---

## F12: CHECK_CHAIN_CONTINUITY Implementation

R11 introduces `CHECK_CHAIN_CONTINUITY` to verify the validator isn't cheating.

**Question:** What does this check verify at the run level?

Proposal: For every claim classified VALID:
1. Extract the delegation_id
2. Verify delegation exists in the bundle
3. Verify delegation.delegate_signer_id == claim.signer_id
4. Verify delegation.root_signer_id == Root_Authority
5. Verify claim.scope ∈ delegation.scope_set
6. Verify delegation.epoch == claim.epoch

If any fails, the classifier is broken, not the claim.

---

---

**End of Follow-Up Questions**

