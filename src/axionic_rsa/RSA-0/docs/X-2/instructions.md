# RSA-X2 Implementation Instructions (Phase X-2)

## 0) Prime Directive

**No side effects without a kernel-issued ExecutionWarrant referencing an admitted `ActionRequest`.**

Additionally:

**No delegation effect without a kernel-admitted `TreatyGrant` and an authenticated (signed) `ActionRequest` bound to the `grantee_identifier`.**

Everything else is plumbing.

---

## 1) Repo Layout Additions (Do This First)

Extend the RSA-0 repo.

Add:

```
axionic-rsa/
  artifacts/
    phase-x/
      treaties/
        treaty_types.v0.1.schema.json

  logs/
    treaties.jsonl
    treaty_trace.jsonl

  replay/
    src/
      treaty_loader.py
      treaty_resolver.py
      signature_verify.py
```

**Rules**

* Treaty schema remains frozen under `artifacts/phase-x/**`.
* Runtime treaty admissions, activations, and revocations are logged only under `logs/**`.
* Logs are append-only.
* Kernel never mutates files under `artifacts/`.

---

## 2) Treaty Versioning Model

### 2.1 Active Treaty Source

At startup:

1. Load frozen treaty schema (`treaty_types.v0.1.schema.json`)
2. Verify SHA256 matches frozen hash (store alongside file if you already do this pattern)
3. Set `active_treaty_schema_hash = schema_hash`

During runtime:

* Active treaty set changes only via admitted `TreatyGrant` / `TreatyRevocation` artifacts.
* Treaty artifacts are always referenced by hash + id.
* Never store mutable in-memory treaty state that survives replay without reconstructing from logs.

---

## 3) New Artifact Types (Closed Set Extension)

Add:

* `TreatyGrant`
* `TreatyRevocation`

### 3.1 TreatyGrant (Typed)

Fields:

* `id`
* `type = "TreatyGrant"`
* `created_at`
* `author`
* `grantor_authority_id`
* `grantee_identifier`
* `granted_actions`
* `scope_constraints`
* `duration_cycles`
* `revocable: bool`
* `authority_citations`
* `justification`

Canonicalize and hash exactly like other artifacts.

**Hard Rules**

* No wildcard delegation (no `"*"` in any form).
* `granted_actions` must be subset of closed action set.
* `duration_cycles` finite and `>= 1`.
* Scope must be narrower or equal to grantor scope.
* Delegation depth ≤ 1 from constitutional root (no chains).

---

### 3.2 TreatyRevocation (Typed)

Fields:

* `id`
* `type = "TreatyRevocation"`
* `created_at`
* `author`
* `grant_id`
* `authority_citations`
* `justification`

Canonicalize and hash exactly like other artifacts.

---

## 4) Structured Treaty Schema Enforcement

Update the frozen schema to require:

```yaml
TreatyGrant:
  duration_cycles: integer (>=1)
  revocable: boolean
  granted_actions: array[ActionType] (minItems=1)
  grantee_identifier: IdentifierType
  scope_constraints: ScopeConstraintType
TreatyRevocation:
  grant_id: string
```

Schema validation must fail if:

* fields missing
* wrong type
* unexpected fields
* values violate bounds

Gate 7 must enforce schema validity before any 8C checks.

---

## 5) Admission Pipeline Extension

Treaty artifacts pass through existing gates 0–5, then:

---

### Gate 6 — Treaty Authorization Preconditions

Verify:

* `active_constitution_hash` exists and is loaded
* Constitutional delegation permission exists (explicit authority cites delegation)
* `authority_citations` are valid and admissible
* `grantor_authority_id` exists and is active

---

### Gate 7 — Treaty Schema Validity

Verify:

* Canonicalization deterministic
* Hash matches canonical payload hash
* Schema validation passes under frozen treaty schema

Reject otherwise.

---

### Gate 8C — Delegation Preservation Checks (TreatyGrant)

Evaluate in strict order.

#### Step 1 — Closed Action Set Membership

Reject if any action in `granted_actions` is not in the closed action set.

Reject Code: `INVALID_FIELD`

---

#### Step 2 — Wildcard Prohibition

Reject if any wildcard appears anywhere in:

* `granted_actions`
* `scope_constraints`
* authority mappings

Reject Code: `WILDCARD_MAPPING`

---

#### Step 3 — Scope Monotonicity

Compute:

* `Scope(grantor)`
* `Scope(grant)`

Reject if `Scope(grant)` is not subset of `Scope(grantor)`.

Reject Code: `SCOPE_COLLAPSE`

---

#### Step 4 — Coverage Monotonicity

Let `Coverage(X)` = set of (action, scope) pairs authorized for authority X.

Reject if:

```
Coverage(grantor ∪ grant_effect) > Coverage(grantor)
```

Reject Code: `COVERAGE_INFLATION`

---

#### Step 5 — Delegation Depth (No Chains)

Reject if the grantor authority is itself derived from a treaty.

Operational rule:

* Only constitutional authorities may issue TreatyGrant.

Reject Code: `EXCESSIVE_DEPTH`

---

#### Step 6 — Acyclicity

Reject if adding the grant introduces any cycle in the delegation graph.

Reject Code: `DELEGATION_CYCLE`

---

#### Step 7 — Density Margin

Compute per-cycle effective density over the closure of permission mappings:

```
A = number of distinct authorities (including grantees with active grants)
B = number of distinct actions
M = number of distinct authority–action pairs in effective resolution set
density = M / (A × B)
```

Reject if:

* `density >= 1 - ε`

Where `ε` is defined in the Constitution (amendable under X-1).

Reject Code: `DENSITY_MARGIN_VIOLATION`

Division by zero must not occur (cardinality checked first).

---

#### Step 8 — Duration Validity

Reject if:

* `duration_cycles < 1`
* `duration_cycles` not finite integer

Reject Code: `INVALID_FIELD`

---

### Gate 8R — Revocation Preservation Checks (TreatyRevocation)

Verify:

* Grant exists.
* Grant is revocable.
* Revoker has valid authority citations for revocation.
* Revocation does not apply retroactively.

Reject Code: `AUTHORITY_CITATION_INVALID` / `INVALID_FIELD` / `NONREVOCABLE_GRANT`

---

## 6) Cycle Ordering (Deterministic, Fail-Closed)

Per cycle boundary, enforce strict ordering:

1. Artifact admission (including TreatyGrant / TreatyRevocation)
2. Revocation processing
3. Active treaty set recomputation
4. ActionRequest admission
5. ExecutionWarrant issuance

Same-cycle revocation must take precedence over warrant issuance.

---

## 7) Signature Requirement (Mandatory for Delegated Actions)

If an `ActionRequest` relies on treaty-based authorization, it MUST include a signature (or verifiable proof) bound to `grantee_identifier`.

### Enforcement

During ActionRequest admission:

1. Determine whether treaty authority is being used.
2. If yes:

   * Verify signature deterministically against `grantee_identifier`.
   * Reject if missing/invalid before authority resolution.

Reject Code: `SIGNATURE_INVALID` / `SIGNATURE_MISSING`

### Replay Constraint

Signature verification must be purely mathematical and deterministic:

* no external identity providers
* no network calls
* no time-based freshness checks

---

## 8) Treaty Activation and Expiry

TreatyGrants are active only when:

```
current_cycle ∈ [grant_cycle, grant_cycle + duration_cycles - 1]
```

Expiry must be deterministic and logged implicitly by cycle progression.

TreatyRevocation:

* becomes effective at next cycle boundary
* removes grant from active set for all future cycles

No retroactive invalidation of executed warrants.

---

## 9) Authority Resolution Under Delegation

During ActionRequest admission:

```
AuthorityResolutionSet =
Constitution permissions
∪ ActiveTreatyGrants (cycle-valid, scope-valid)
```

Hard constraints:

* Treaty authority never overrides constitutional prohibitions.
* Treaty authority cannot introduce new action types.
* Treaty authority cannot expand scope beyond grantor scope.
* Delegation chains forbidden (depth ≤ 1).

---

## 10) Replay Harness Upgrade (Mandatory)

Replay must:

1. Load base constitution (per X-1).
2. Reconstruct active treaty set from `treaties.jsonl` and cycle ordering rules.
3. Apply revocations at boundary before ActionRequests.
4. Verify that signature checks are deterministic and yield identical accept/reject outcomes.
5. Continue deterministic execution.

Replay must satisfy:

```
state_sequence = F(log_stream, kernel_version)
```

No global treaty cache allowed.

Any divergence = X-2 failure.

---

## 11) Logging Extensions

Append to logs:

* `treaties.jsonl`

  * cycle_id
  * artifact_id
  * artifact_hash
  * type (TreatyGrant/TreatyRevocation)
  * grant_id (for revocations)
  * effective_cycle (for revocations)
  * expiry_cycle (for grants)

* `treaty_trace.jsonl`

  * artifact_id
  * gate_results (6/7/8C or 8R)
  * rejection_reason (if any)
  * density inputs (A,B,M,density,ε)
  * scope checks summary
  * depth/acyclicity result
  * signature verification outcome when relevant (ActionRequest admission trace)

All logs append-only.

---

## 12) Test Suite Additions (X-2)

Add tests:

1. Positive: A grants Notify to B → B submits signed request → warrant issued → replay stable.
2. Missing signature on delegated action → REFUSE.
3. Invalid signature → REFUSE.
4. Chain attempt A→B then B→C → REFUSE (depth).
5. Cycle attempt A→B and B→A → REFUSE (acyclicity).
6. Wildcard injection in granted_actions or scope → REFUSE.
7. Forbidden action delegated (not in closed action set) → REFUSE.
8. Infinite or zero duration → REFUSE.
9. Same-cycle revocation blocks pending delegated action (fail-closed ordering).
10. Density saturation attempt violates `1-ε` → REFUSE.
11. Replay across grant/expiry boundary produces identical result.
12. 100+ grants with sparse scopes maintain determinism and enforce ε margin.

---

## 13) Failure Conditions

Phase X-2 fails if:

* Replay diverges.
* Delegation chain is possible.
* Unsigned delegated ActionRequest is accepted.
* Revocation can be bypassed in same cycle ordering.
* Density margin enforcement fails.
* Treaty authority can override constitutional prohibitions.
* Any side effect occurs without a kernel-issued ExecutionWarrant.

---

## 14) Definition of Done (Phase X-2 Completion)

X-2 complete when:

1. At least one lawful TreatyGrant admitted and exercised via signed delegated ActionRequest.
2. At least one lawful TreatyRevocation applied and enforced.
3. Delegation depth ≤ 1 enforced strictly.
4. Density remains < 1 − ε across all test regimes.
5. Scope and coverage monotonicity enforced.
6. Replay determinism holds across grant / revoke / expiry boundaries.
7. All rejection paths logged and attributable.

---

## 15) Explicit Do-Not-Do List (X-2 Regression Traps)

Do not implement:

* Identity verification via external services
* Trust lists, reputational scoring, or “known agent” heuristics
* Any LLM-mediated signature interpretation
* “Helpful” signature fallback (e.g., accept unsigned if local)
* Implicit delegation inferred from conversation state
* Delegation chains (even “just one”)
* Network-enabled treaty fetch
* Mutable treaty state not reconstructible from logs

Any of these reintroduces proxy sovereignty.

---

## 16) Final X-2 Invariant

Physics (Kernel) is immutable.
Law (Constitution) is replaceable.
Treaties are bounded, revocable policy artifacts.
Identity binding is cryptographic and deterministic.

If implemented faithfully, authority can be projected without multiplying sovereignty.

Proceed to code.
