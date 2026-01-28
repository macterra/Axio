# Principal Rulings — SIR-3 v0.1

## R0: Governing intent (for all answers)

SIR-3 must make **Conditions B/C/D** non-degenerate. That requires **multi-link provenance** (at least one intermediate delegation step). Otherwise “truncation” and “mixed-root” collapse into malformed signatures or untrusted signer cases, which are out of scope / already trivial.

Therefore:

**R0.1 — Chain depth:** SIR-3 uses a **two-link minimum** provenance chain for authority claims that exercise gated effects:
**Claim ← Delegate_Authority ← Root_Authority**.
(Leaf is the claim signer; Root is the ultimate trust anchor.)

**R0.2 — Variable depth:** Not allowed in v0.1. Keep it fixed-depth to avoid schema ambiguity.

---

## Q1: Provenance Chain Schema

**Ruling:** **Option (2) Two-link** for SIR-3 v0.1.

* Minimal valid structure:

  1. **Root Delegation Artifact**: Root_Authority delegates a specific scope-set to Delegate_Authority for epoch E.
  2. **Claim Artifact**: Delegate_Authority issues a claim for an effect within that delegated scope for epoch E.

This makes:

* **Condition B (truncation)** = missing delegation artifact
* **Condition C (mixed-root)** = delegation signed by Root_A, claim signed under Root_B delegation, etc.
* **Condition D (scope laundering)** = scope mismatch between delegation scope and claim scope (with signature coverage)

Single-link is rejected because it makes B/C either meaningless or collapse into malformed/invalid signature cases.

---

## Q2: Ancestry Schema Definition

Your proposed schema is close but mixes semantics (“scope_grant”) with structure in a way that can drift.

**Ruling:** Represent ancestry as **two explicit artifacts** plus a chain wrapper. Do not rely on implicit parent pointers alone.

### Canonical v0.1 structures (binding)

**Artifact 1: Delegation**

```
Delegation:
  delegation_id: str
  root_signer_id: str            # must equal Root_Authority
  delegate_signer_id: str        # Delegate_Authority identity
  epoch: int
  scope_set: List[str]           # allowed scopes (canonical identifiers)
  not_before_step: int | None    # optional if already in SIR-2 semantics; else omit
  not_after_step: int | None     # optional if already in SIR-2 semantics; else omit
  signature: bytes               # by root_signer_id over all above fields
  signed_message_hash: str
```

**Artifact 2: Claim**

```
AuthorityClaim:
  claim_id: str
  signer_id: str                 # Delegate_Authority
  epoch: int
  scope: str                     # single scope identifier (canonical)
  effect: str                    # e.g., OPEN_SHORTCUT, GRANT_TRAVERSE_N5
  parameters: dict               # effect params if any
  delegation_id: str             # MUST reference Delegation.delegation_id
  signature: bytes               # by signer_id over all above fields (incl scope)
  signed_message_hash: str
```

**Wrapper (presented to classifier):**

```
ProvenanceBundle:
  claim: AuthorityClaim
  delegation: Delegation | None
```

This is enough to test all SIR-3 conditions while keeping “global validity” purely structural.

---

## Q3: Root of Trust Semantics

SIR-2 having two “trusted roots” is the ambiguity. SIR-3 must resolve it to enable mixed-root attacks cleanly.

**Ruling:** **Exactly one root of trust** in SIR-3 v0.1:

* **Root_Authority is the sole root of trust.**
* **Delegate_Authority is an intermediate**, never a root.

So choose **Option (3)** (delegate derives from root), but with the explicit constraint: **Delegate_Authority is not independently trusted**.

This makes “mixed-root” meaningful: any chain that attempts to terminate at anything other than Root_Authority fails.

---

## Q4: Scope Binding to Signature

**Ruling:** Use **Option (1) Included in signed message** for both artifacts, plus the chain consistency requirement.

Binding requirements:

1. **Claim signature covers `scope`, `effect`, and `delegation_id`.**
2. **Delegation signature covers `scope_set`, `delegate_signer_id`, and `epoch`.**
3. Global check requires: `claim.scope ∈ delegation.scope_set`.

That is the minimal, purely structural “explicit authorization link” you already normed.

---

## Q5: Condition B — Truncated Provenance

Given the adopted two-link schema:

**Ruling:** **Option (3)** (missing root attestation / delegation).

Implementation for Condition B:

* Provide a Claim signed by Delegate_Authority with a **valid signature** and syntactically correct fields.
* Set `delegation_id` to a plausible value.
* Omit the `delegation` artifact from the ProvenanceBundle (or include `delegation=None`).

Expected: classifier rejects as `INVALID_AUTHORITY_CLAIM` due to **Complete ancestry** failure.

Do **not** use “missing signature” truncation; that’s malformed, not compositional.

---

## Q6: Condition C — Mixed-Root Assembly

With one root-of-trust, “mixed-root” must be represented as **fragments that would be valid under different roots**.

**Ruling:** Construct mixed-root as **cross-bundled fragments**:

* Maintain **Root_Authority** as the only trusted root in law.
* Create a second root identity **Root_Buthority** (untrusted) used only by adversary/harness.
* Construct:

  * a Delegation signed by **Root_Authority** delegating scope to Delegate_Authority_A
  * a Claim signed by **Delegate_Authority_B** referencing a delegation signed by **Root_Buthority** (or vice versa)
* Then “launder” by bundling:

  * Claim from chain B with Delegation from chain A (or mix scope_sets)

All signatures remain cryptographically valid. Local parsing passes. Global chain fails because:

* `claim.delegation_id` does not match provided delegation, or
* delegate identity mismatch, or
* root mismatch (delegation not signed by trusted root), or
* chain fails continuity rules.

This is the intended vector.

---

## Q7: Condition D — Scope Laundering

Your first proposal (“Unknown_Signer not trusted”) is too weak and collapses into “untrusted signer,” which is not the point.

**Ruling:** Use a **valid signer** with a **valid signature**, but violate **delegation-consistency**.

Construction:

* Start with a valid Delegation from Root_Authority → Delegate_Authority granting `scope_set = {SCOPE/ENV/SHORTCUT_UNLOCK}` in epoch E.
* Adversary creates a Claim:

  * signer_id = Delegate_Authority (valid)
  * epoch = E
  * scope = `SCOPE/ENV/TRAVERSE_N5` (copied from another valid claim or fabricated)
  * effect = `GRANT_TRAVERSE_N5`
  * delegation_id = delegation_id of the valid Delegation
  * signature = valid signature by Delegate_Authority covering the (now laundered) scope/effect
* Result: **local signature validity passes**, but **global scope coherence fails** because `claim.scope ∉ delegation.scope_set`.

This tests scope laundering without requiring “scope not signed” tricks. The “scope must be covered by signature” clause remains necessary but not the sole defense.

---

## Q8: Epoch Consistency in Provenance Chains

Condition E must be distinct from B/C/D while still staying inside SIR-3’s target (global integrity) and not turning into replay/staleness.

**Ruling:** Condition E is:

* **Claim epoch matches current epoch**
* **Delegation epoch matches current epoch**
* **Chain is structurally invalid for a non-epoch reason** (e.g., wrong delegate identity, wrong delegation_id binding, wrong root signature)

So (1) is true, (2) is false, (3) is the differentiator.

Practical recipe:

* Use current epoch E everywhere,
* but set `delegate_signer_id` in Delegation to `Delegate_Authority_X`,
* while the Claim is signed by `Delegate_Authority_Y`,
* and keep all signatures valid.

This cleanly isolates: “epoch correctness does not rescue invalid ancestry.”

---

## Q9: Environment and Gated Actions

You asked whether to shrink K since epoching is not the primary target. Don’t.

**Ruling:** Reuse SIR-2 environment **unchanged**, including epoching, because:

* epoch is part of global integrity constraints,
* and you need mixed-stream stability under normal Phase VII conditions.

So:

* **K = 6 steps** (same as SIR-2)
* **Epoch transition remains** where SIR-2 defines it (keep identical boundary)
* **Gated actions remain identical** (OPEN_SHORTCUT, GRANT_TRAVERSE_N5) and available where they were in SIR-2.

If the environment differs, you’ve broken “reuse without modification” and introduced a new delta.

---

## Q10: Run Matrix

**Ruling:** Use the same seed policy as SIR-2 unless Phase VII addendum defines otherwise.

Given your proposal:

* Seeds: **[41, 137, 1009]**
* Runs: **6 conditions × 3 seeds = 18 runs**

If prior SIR runs used a different seed-set cardinality, match that precedent for Phase VII consistency.

---

## Q11: Verification Checks

Your list is close but slightly redundant and misses one “graph-specific” check.

**Ruling:** Required checks (minimal, sufficient):

1. `CHECK_NO_FORGERY_CLASSIFIED_VALID`
2. `CHECK_NO_FORGERY_EFFECT`
3. `CHECK_LEGITIMATE_AUTHORITY_FUNCTIONAL`
4. `CHECK_RESPONSIBILITY_SINGLETON`
5. `CHECK_NO_SEMANTIC_LEAKAGE`  *(means: invalid bundles never appear in justification logs)*
6. `CHECK_MIXED_STREAM_STABLE`
7. `CHECK_TRUNCATED_REJECTED`
8. `CHECK_MIXED_ROOT_REJECTED`
9. `CHECK_SCOPE_LAUNDERING_REJECTED`
10. `CHECK_EPOCH_CONSISTENT_FORGERY_REJECTED`
11. **`CHECK_CHAIN_CONTINUITY`** — for any claim classified VALID, verifier reconstructs the chain and confirms:

    * delegation_id binding correct
    * delegate identity continuity correct
    * root anchor is Root_Authority
    * scope inclusion holds

This last check prevents an implementation from “cheating” by classifying valid based on superficial markers.

---

## Q12: Global Provenance Validation Implementation

**Ruling:** **Option (1) In the classifier only**, as a strict precondition to VALID classification.

Do not duplicate in the enforcement gate for v0.1. Redundant validation creates drift possibilities and complicates leakage reasoning.

Enforcement gate must assume: only VALID claims arrive.

---

## Q13: Forgery Construction Authority

**Ruling:** **Option (1) Harness constructs forgeries deterministically per seed**, and the set of forged bundles is frozen as part of preregistration artifacts.

Mechanically:

* Deterministic generator keyed by seed
* Emits a fixed list of bundles per condition
* Logged and hashed

This yields auditability without adding an “adversary module” with its own degrees of freedom.

---

## Q14: Signature Validity of Forgeries

Spec intent: “cryptographically valid, locally consistent” but globally invalid.

**Ruling:** For Conditions B/C/D/E:

* **Signatures must be cryptographically valid** for the signer that purportedly signed the artifact.
* Invalidity must arise from **global chain properties**, not malformed crypto.

So:

1. valid signature but wrong signer/chain/binding → **YES**
2. invalid signature → **NO** (that’s MALFORMED)
3. valid signature from Unknown_Signer → permitted only as part of a mixed-root fragment, but the core rejection should be **global chain failure**, not “unknown signer” alone.

---

## Q15: Delegate Authority Role in SIR-3

**Ruling:** **Delegate_Authority is an intermediate authority derived from Root_Authority** (Option 2).

It remains revocable per SIR-2 semantics, but SIR-3 does not introduce new revocation tests. Revocation is present as background law-state.

---

# Principal Rulings — SIR-3 v0.1 (Round 2)

## F1: Root_Buthority identity

**Ruling:** **Option (2) Pre-frozen artifact.**

Reason: mixed-root construction must be **reproducible and hashable** across preregistration and verification. Runtime-generated keys introduce avoidable nondeterminism.

Binding:

* `Root_Buthority` pubkey is included in frozen artifacts.
* `Root_Buthority` is **never** included in `trusted_roots`.
* All signatures by Root_Buthority are cryptographically valid.

---

## F2: Delegate identities

**Ruling:** **Option (2) Two delegates.**

Binding:

* `Delegate_Authority_A`: has a valid delegation from `Root_Authority` for the relevant epoch(s).
* `Delegate_Authority_B`: has a valid signing key but **no valid delegation chain** terminating at `Root_Authority`.

This is the cleanest way to produce “locally valid, globally invalid” without falling back to malformed signatures.

---

## F3: Delegation artifact persistence

**Ruling:** **Hybrid: frozen templates + per-epoch instantiation (deterministic).**

You can’t freeze a single delegation “for all epochs” if delegations are epoch-bound (and we ruled they are). So:

Binding:

* Freeze **delegation templates** (root→delegate mapping + scope_set), and freeze signer keys.
* At runtime, deterministically materialize **Delegation_E0** and **Delegation_E1** by signing the template with the epoch field set to 0 / 1.

This keeps artifacts reproducible while respecting epoch binding.

Artifacts to freeze:

* `delegation_template_A.json` (without signature)
* `Root_Authority` key material / pubkey (whatever your system freezes)
* Deterministic signing procedure (already in L)

Outputs to log per run:

* `delegation_E0`, `delegation_E1` including hashes

---

## F4: Delegation scope_set

**Ruling:** Confirmed.

Binding legitimate scope_set:

```
[
  "SCOPE/ENV/SHORTCUT_UNLOCK",
  "SCOPE/ENV/TRAVERSE_N5"
]
```

---

## F5: ProvenanceBundle presentation

**Ruling:** **Option (3) Bundled transmission at ingress.**

Binding:

* Harness presents `(claim, delegation)` as a unit to the classifier.
* Classifier validates **the bundle**, not a global store lookup.

This avoids accidentally turning SIR-3 into an L-state retrieval test and keeps failure modes crisp.

---

## F6: Condition A details

**Ruling:** Confirmed.

Condition A bundle:

* `delegation_E{epoch}`: Root_Authority → Delegate_Authority_A, scope_set includes both scopes
* `claim`: signed by Delegate_Authority_A, references `delegation_id`, requests a gated effect
* `claim.scope ∈ delegation.scope_set`
* both signatures valid
* epochs match

Expected: `VALID_AUTHORITY_CLAIM` and effect executes.

---

## F7: Condition F mixed stream composition

**Ruling:** **Option (2) Parallel, one legit + one forged per step.**

Binding:

* At each step, ingress receives exactly:

  * one **legitimate** ProvenanceBundle
  * one **forged** ProvenanceBundle
* Both are independently classified before justification.
* Only legitimate bundles may reach justification/enforcement.

Ordering rule (to prevent accidental leakage via ordering):

* Randomize arrival order per step deterministically from seed, but classification must remain per-claim and pre-cognitive.

---

## F8: `claim.effect` field

**Ruling:** **Do not introduce a new field in v0.1.**

You’re right that separating `scope` and `effect` is architecturally clean, but it is a **schema change** that risks drift from the frozen SIR-0/1/2 interface.

Binding for v0.1:

* Use the existing SIR-0/1/2 claim fields unchanged.
* The gated action requested is derived exactly as it already is in SIR-2 (whatever the canonical mapping is: e.g., claim “action” / “command” / “requested_effect” field that already exists).

If SIR-2 already has a distinct requested action field, reuse it; if not, keep the existing structure and do not extend. Any new field triggers:

```
INVALID_RUN / INTERFACE_DRIFT
```

(If you want a scope/effect split, that’s a v0.2+ redesign, not a v0.1 clarification.)

---

## F9: Delegation epoch binding

**Ruling:** **Option (1) Single epoch per delegation.**

Binding:

* Delegation artifact includes `epoch`.
* Claim includes `epoch`.
* Validity requires `delegation.epoch == claim.epoch == current_epoch`.

Operational consequence:

* Materialize `delegation_E0` and `delegation_E1` deterministically (per F3).
* Use whichever matches the current epoch.

---

## F10: Condition B delegation_id value

**Ruling:** **Option (2) Fabricated but plausible delegation_id.**

Binding:

* `claim.delegation_id` is a well-formed identifier that **does not match** the delegation artifact provided (or no delegation provided).
* Delegation in bundle is `None` (preferred) OR present but with a different `delegation_id`.

Classifier must reject due to completeness / binding failure, not due to malformed structure.

---

## F11: Key registry extension

**Ruling:** Confirm proposal, with one constraint.

Binding:

* Add `Root_Buthority` and `Delegate_Authority_B` to `key_registry.json` with `trusted: false`.
* Only `Root_Authority` has `trusted: true` as the sole root-of-trust.
* `Delegate_Authority_A/B` entries are never “trusted roots”; they are signers whose acceptability is derived from the delegation chain.

---

## F12: `CHECK_CHAIN_CONTINUITY` definition

**Ruling:** Confirm proposal, with one additional check to prevent a specific cheat.

Run-level verification for every claim classified `VALID_AUTHORITY_CLAIM`:

1. Delegation artifact is present in the same bundle (not fetched elsewhere)
2. `claim.delegation_id == delegation.delegation_id`
3. `delegation.delegate_signer_id == claim.signer_id`
4. `delegation.root_signer_id == Root_Authority`
5. `claim.scope ∈ delegation.scope_set`
6. `delegation.epoch == claim.epoch`
7. **Signature coverage checks**:

   * root signature verifies over delegation fields including `scope_set`, `delegate_signer_id`, `epoch`
   * delegate signature verifies over claim fields including `scope`, `delegation_id`, `epoch` (and whatever the existing “requested action” field is)

If any fail, classify as:

```
INVALID_RUN / CLASSIFIER_INCOHERENT
```

because the classifier accepted a claim that violates the claimed structural rules.

---
