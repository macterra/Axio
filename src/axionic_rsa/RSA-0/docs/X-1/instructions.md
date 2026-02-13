# RSA-X1 Implementation Instructions (Phase X-1)

## 0) Prime Directive

**No side effects without a kernel-issued ExecutionWarrant referencing an admitted `ActionRequest`.**

Additionally:

**No constitution change without a kernel-issued `AmendmentAdoptionRecord` referencing an admitted `AmendmentProposal`.**

Everything else is plumbing.

---

## 1) Repo Layout Additions (Do This First)

Extend the RSA-0 repo.

Add:

```
axionic-rsa/
  artifacts/
    phase-x/
      constitution/
        rsa_constitution.v0.1.yaml
        rsa_constitution.v0.1.schema.json
        rsa_constitution.v0.1.sha256

  logs/
    constitutions.jsonl
    amendment_trace.jsonl

  replay/
    src/
      constitution_loader.py
```

**Rules**

* Constitution files remain frozen under `artifacts/phase-x/**`.
* Runtime constitution transitions are logged only under `logs/**`.
* Logs are append-only.
* Kernel never mutates files under `artifacts/`.

---

## 2) Constitution Versioning Model

### 2.1 Active Constitution Source

At startup:

1. Load base constitution (`v0.1.yaml`)
2. Verify SHA256 matches frozen hash
3. Set `active_constitution_hash = v0.1_hash`

During runtime:

* Active constitution may change only via logged `AmendmentAdoptionRecord`
* Constitution is always referenced by hash

Never store mutable in-memory policy that survives replay.

---

## 3) New Artifact Types (Closed Set Extension)

Add:

* `AmendmentProposal`
* `AmendmentAdoptionRecord`

### 3.1 AmendmentProposal (Typed)

Fields:

* `id`
* `type = "AmendmentProposal"`
* `created_at`
* `author`
* `prior_constitution_hash`
* `proposed_constitution_yaml`
* `proposed_constitution_hash`
* `authority_citations`
* `scope_claim`
* `justification`

Canonicalize and hash exactly like other artifacts.

---

### 3.2 AmendmentAdoptionRecord

Fields:

* `id`
* `type = "AmendmentAdoptionRecord"`
* `created_at`
* `proposal_id`
* `prior_constitution_hash`
* `new_constitution_hash`
* `effective_cycle`
* `authority_citations`

Kernel-issued only.

---

## 4) Structured AmendmentProcedure (Schema Enforcement)

Update `rsa_constitution.v0.1.schema.json` to require:

```yaml
AmendmentProcedure:
  cooling_period_cycles: integer (>=2)
  authorization_threshold: integer
  authority_reference_mode: enum
  density_upper_bound: float (<1) optional
```

No free-text amendment procedures permitted.

Schema validation must fail if:

* fields missing
* wrong type
* unexpected fields
* values violate bounds

Gate 7 must enforce schema validity before any 8B checks.

---

## 5) Admission Pipeline Extension

AmendmentProposal passes through existing gates 0–5, then:

---

### Gate 6 — Amendment Authorization

Verify:

* `prior_constitution_hash == active_constitution_hash`
* AmendmentProcedure exists
* Cooling delay rule satisfied
* Authority citations valid

---

### Gate 7 — Full Replacement Integrity

Verify:

* Proposed YAML canonicalizes deterministically
* Hash matches `proposed_constitution_hash`
* Schema validation passes
* ECK sections present:

  * AmendmentProcedure
  * AuthorityModel
  * WarrantDefinition
  * ScopeSystem

Reject otherwise.

---

### Gate 8A — Physics Claim Rejection

Reject if proposed YAML:

* Introduces executable payloads
* Declares kernel invariants
* Claims to disable warrant gating
* References undefined kernel hooks

This is structural, not semantic.

---

### Gate 8B — Structural Constraint Preservation

Evaluate in strict order.

#### Step 1 — Cardinality

Extract:

* A = number of distinct authorities
* B = number of distinct actions

If A < 1 → REFUSE
If B < 1 → REFUSE

---

#### Step 2 — Wildcard Check

Scan fully parsed authority mappings.

Reject if any:

```
authority: "*"
action: "*"
```

YAML anchors must be resolved before this check.

---

#### Step 3 — Universal Authorization

Compute:

```
M = number of distinct authority–action pairs
density = M / (A × B)
```

Reject if:

* M == A × B
* density == 1

Division by zero must not occur (cardinality checked first).

---

#### Step 4 — Scope Collapse

Reject if:

* ScopeSystem empty
* All actions globally scoped
* No action requires scoped warrant

---

#### Step 5 — Ratchet Check (Envelope Degradation)

Let:

* old = active_constitution.AmendmentProcedure
* new = proposed_constitution.AmendmentProcedure

Reject if:

* new.cooling_period_cycles < old.cooling_period_cycles
* new.authorization_threshold < old.authorization_threshold
* structured fields replaced with free text
* AmendmentProcedure removed

Ratchet is monotonic non-decreasing.

---

## 6) Cooling Delay Enforcement

AmendmentProposal cannot be adopted until:

```
current_cycle >= proposal_cycle + cooling_period_cycles
```

Cooling must be enforced at adoption time.

Adoption in same cycle is illegal.

---

## 7) Adoption Execution

When eligible:

1. Re-run all Gates 6–8B.
2. If still valid:

   * Issue `AmendmentAdoptionRecord`
   * Set `active_constitution_hash = proposed_hash`
   * Log in `constitutions.jsonl`

No file writes to artifacts.

Constitution YAML may be stored in logs for replay integrity.

---

## 8) Replay Harness Upgrade (Mandatory)

Replay must:

1. Load base constitution.
2. Reconstruct constitution transitions from `AmendmentAdoptionRecord` entries.
3. At cycle `effective_cycle`, switch active constitution.
4. Continue deterministic execution.

Replay must satisfy:

```
state_sequence = F(log_stream, kernel_version)
```

No global policy cache allowed.

Any divergence = X-1 failure.

---

## 9) Logging Extensions

Append to logs:

* `amendment_trace.jsonl`

  * proposal_id
  * gate_results
  * rejection_reason (if any)
  * density
  * cardinality
  * envelope comparison results

* `constitutions.jsonl`

  * cycle_id
  * prior_hash
  * new_hash

All logs append-only.

---

## 10) Test Suite Additions (X-1)

Add tests:

1. Trivial amendment (comment change) → adopt → replay stable.
2. Universal authorization proposal → REFUSE.
3. Scope collapse proposal → REFUSE.
4. Cooling reduction attempt → REFUSE.
5. Authorization threshold reduction → REFUSE.
6. Wildcard injection attempt → REFUSE.
7. Replay across amendment boundary produces identical result.
8. Repeated amendment (10 chained) maintains determinism.

---

## 11) Failure Conditions

Phase X-1 fails if:

* Replay diverges.
* Ratchet can be weakened.
* Universal authorization accepted.
* Cooling bypass possible.
* Constitution mutated without adoption record.

---

## 12) Definition of Done (Phase X-1 Completion)

X-1 complete when:

1. At least one lawful amendment adopted.
2. Replay determinism holds across fork.
3. Ratchet monotonicity enforced.
4. density < 1 invariant preserved.
5. No proxy authority introduced.
6. All rejection paths logged and attributable.

---

## 13) Explicit Do-Not-Do List (X-1 Regression Traps)

Do not implement:

* Semantic evaluation of constitutions
* LLM-based degeneracy detection
* Natural language amendment procedures
* Patch-based mutation (v0.1 remains full replacement)
* Global policy object caching
* Auto-recovery of failed amendments
* “Helpful” fallback constitution
* Network-enabled amendment fetch

Any of these reintroduces proxy sovereignty.

---

## 14) Final X-1 Invariant

Physics (Kernel) is immutable.
Law (Constitution) is replaceable.
Meta-Law (Gates 6–8B + Ratchet) prevents structural collapse.

If implemented faithfully, sovereignty is conserved under lawful self-modification.

Proceed to code.
