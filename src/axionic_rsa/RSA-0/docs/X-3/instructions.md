# RSA-X3 Implementation Instructions (Phase X-3)

## 0) Prime Directive

**No side effects without a kernel-issued ExecutionWarrant referencing an admitted `ActionRequest`.**

Additionally:

**No delegation effect without a kernel-admitted `TreatyGrant` and an authenticated (signed) `ActionRequest` bound to the `grantee_identifier`.**

Additionally (X-3 specific):

**No sovereign identity transition unless a kernel-admitted `SuccessionProposal` deterministically sets `pending_successor_key` in Cycle N, the Cycle N commit is signed by `prior_sovereign_public_key`, and the Cycle N+1 start header is verified under `pending_successor_key`.**

Everything else is plumbing.

---

## 1) Repo Layout Additions (Do This First)

Extend the RSA-X2 repo.

Add:

```
axionic-rsa/
  artifacts/
    phase-x/
      x3/
        x3_session_spec.v0.1.schema.json
        x3_profile_defaults.v0.1.json

  logs/
    x3_sessions.jsonl
    x3_metrics.jsonl
    x3_boundary_events.jsonl

  replay/
    src/
      x3_runner.py
      x3_generators.py
      x3_metrics.py
      x3_boundary.py
```

**Rules**

* X-3 session schemas/profiles remain frozen under `artifacts/phase-x/x3/**`.
* Runtime session inputs/outputs are logged only under `logs/**`.
* Logs are append-only.
* Kernel never mutates files under `artifacts/`.

---

## 2) X-3 Versioning Model

### 2.1 Active X-3 Spec Source

At startup:

1. Load frozen X-3 session schema (`x3_session_spec.v0.1.schema.json`)
2. Verify SHA256 matches frozen hash
3. Set `active_x3_schema_hash = schema_hash`

During runtime:

* Session runs are defined only by **admitted** session profiles (or locally selected profiles that are hashed and logged before first cycle).
* No mutable “current session” state survives replay except what is reconstructible from logs and frozen artifacts.

---

## 3) New Artifact Types (Closed Set Extension)

Add:

* `X3SessionStart`
* `X3SessionEnd`
* `SuccessionProposal` *(as specified in X-3)*
* `TreatyRatification` *(X-3 uses this artifact name; if an equivalent exists, alias deterministically—do not create a second ratification type.)*

### 3.1 X3SessionStart (Typed)

Fields:

* `id`
* `type = "X3SessionStart"`
* `created_at`
* `author`
* `session_id`
* `session_length_cycles` (`N`)
* `seeds` (all seeds used: succession stream, treaty stream, action stream, amendment stream if any)
* `rotation_schedule` (explicit: cycles at which a SuccessionProposal is injected; may include no-op/self-succession)
* `ratification_schedule` (explicit: cycles at which TreatyRatification artifacts are injected)
* `delegation_state_mode` (LOW / NEAR_BOUND / CHURN_ACTIVE)
* `invalid_succession_fractions` (classes + proportions)
* `invalid_boundary_fractions` (classes + proportions; see Section 10.3)
* `notes` (optional)

Canonicalize and hash like other artifacts.

**Hard Rules**

* Every run MUST begin with an admitted `X3SessionStart` whose hash is logged before cycle 1.
* No parameter drift across cycles.

### 3.2 X3SessionEnd (Typed)

Fields:

* `id`
* `type = "X3SessionEnd"`
* `created_at`
* `author`
* `session_id`
* `final_cycle`
* `replay_divergence_count`
* `closure_pass: bool`
* `failure_reasons` (if any; enumerated codes)
* `state_hash_chain_tip`

Canonicalize and hash like other artifacts.

---

## 4) Structured X-3 Schema Enforcement

Update the frozen schema to require (minimum):

```yaml
X3SessionStart:
  session_id: string
  session_length_cycles: integer (>=1)
  seeds: object (required keys)
  rotation_schedule: array[integer]   # cycles
  ratification_schedule: array[integer]
  delegation_state_mode: enum
  invalid_succession_fractions: object
  invalid_boundary_fractions: object
X3SessionEnd:
  session_id: string
  final_cycle: integer
  replay_divergence_count: integer
  closure_pass: boolean
  failure_reasons: array[string]
  state_hash_chain_tip: string
SuccessionProposal:
  prior_sovereign_public_key: string
  successor_public_key: string
  authority_citations: array
  justification: string
  signature: string
TreatyRatification:
  treaty_id: string
  ratify: boolean
  signature: string
```

Schema validation must fail if:

* fields missing
* wrong type
* unexpected fields
* values violate bounds

Gate 7 (X-3 session gate) must enforce schema validity before any session begins.

---

## 5) Mandatory X-3 Scenarios (Minimum Coverage)

X-3 requires the following scenario buckets to run:

1. **Low-delegation rotation** (baseline)
2. **Near-bound rotation** (density close to bound at rotation cycle)
3. **Rotation during delegation churn** (grant/revoke active)
4. **Rotation with ratification delay** (≥1 cycle of suspended treaties)
5. **Multi-rotation in one session** (≥2 activations)
6. **Rejected succession** (invalid signature)
7. **Rejected succession** (duplicate in same cycle)

**Rule:** A preregistered X-3 execution plan is incomplete unless it includes at least one run covering each bucket.

---

## 6) Admission Pipeline Extension (X-3)

X-3 adds succession artifacts and boundary verification, without adding new authority semantics.

### Gate 6 — X-3 Session Preconditions

Verify:

* `kernel_version_id` matches X-0E pinned identity
* frozen constitution v0.3 hash present
* treaty schema hash present
* X-2 treaty machinery enabled
* treaty suspension + ratification machinery enabled
* lineage state initialized from genesis anchor

### Gate 7 — X-3 Session Schema Validity

Verify:

* canonicalization deterministic
* hash matches canonical payload hash
* schema validation passes under frozen X-3 session schema

Reject: `SCHEMA_INVALID` / `INVALID_FIELD`

### Gate S* — SuccessionProposal Admission (Per Spec)

Implement exactly as X-3:

S1 Completeness → `INVALID_FIELD`
S2 Authority Citation Snapshot → `AUTHORITY_CITATION_INVALID`
S3 Signature Verification → `SIGNATURE_INVALID`
S4 Sovereign Match → `PRIOR_SOVEREIGN_MISMATCH`
S5 Lineage Integrity → `IDENTITY_CYCLE` / `LINEAGE_FORK`
S6 Constitutional Compliance → `SUCCESSION_DISABLED`
S7 Per-Cycle Uniqueness → `MULTIPLE_SUCCESSIONS_IN_CYCLE`

---

## 7) Cycle Ordering (Deterministic, Fail-Closed)

X-3 requires **Topological Time**.

### 7.1 Topological Sorting Rule (Binding)

For each cycle `c`:

* Buffer all inputs intended for cycle `c`.
* Sort into buckets by binding order below.
* Execute strictly in that order.
* Input stream order within a cycle is ignored.

### 7.2 Binding Order (X-3)

1. Amendment adoption
2. Constitutional revalidation
3. SuccessionProposal admission
4. Record `pending_successor_key` (if admitted)
5. Treaty grants
6. Treaty revocations
7. Density repair
8. RSA actions
9. Delegated actions
10. Warrant issuance
11. Cycle commit (End-State hash + signature)

**Hard Rule:** Succession admission does not change Cycle N sovereign authority. Activation occurs only at boundary.

---

## 8) Boundary Signature Logic (X-3 Binding)

X-3 defines a deterministic boundary zipper.

### 8.1 Required State Fields

Add to kernel state:

* `sovereign_public_key_active`
* `pending_successor_key` (nullable)
* `identity_chain_length`
* `identity_chain_tip_public_key`
* `identity_chain_tip_hash` *(if you store chain as hashes; if not, store enough to reconstruct deterministically)*

### 8.2 Three-Phase Transition Enforcement

**Phase A — In-Cycle Admission (Cycle N)**

If a SuccessionProposal is admitted in cycle N:

* set `pending_successor_key = successor_public_key`
* record a boundary event log record (see Section 14)

**Phase B — Cycle N Commit Signature**

Cycle N End-State commit MUST:

* include SuccessionProposal artifact + admission decision (if any)
* include `pending_successor_key` value
* be signed by `prior_sovereign_public_key` (the active key throughout Cycle N)

Reject signing/verification mismatch:

`BOUNDARY_SIGNATURE_MISMATCH`

**Phase C — Cycle N+1 Start Header Verification**

At Cycle N+1 start:

* if `pending_successor_key != null`:

  * set `sovereign_public_key_active = pending_successor_key`
  * clear `pending_successor_key`
  * enforce prior key zeroing (Section 9)
* verify the Cycle N+1 start/header signature under `sovereign_public_key_active`

Reject:

`BOUNDARY_SIGNATURE_MISMATCH`

**Hard Rule:** The validator must be able to derive the Cycle N+1 verification key from Cycle N committed state alone.

---

## 9) Prior Key Revocation (X-3 Binding)

Upon successor activation:

* prior sovereign key is downgraded to **Zero Authority**
* it is treated as a stranger unless explicitly granted new powers by the successor

Enforce:

* any post-activation attempt by prior key to issue sovereign-signed artifacts fails deterministically

Reject:

`PRIOR_KEY_PRIVILEGE_LEAK`

---

## 10) Treaty Suspension + Ratification (X-3 Binding)

### 10.1 Suspension Trigger

On successor activation:

* all ACTIVE treaties → `SUSPENDED`
* delegated execution blocked until ratified

### 10.2 Ratification Handling

`TreatyRatification` must:

* be signed by the active sovereign key
* reference a concrete treaty id (no wildcards)
* deterministically transition treaty state:

  * `SUSPENDED` → `ACTIVE` (if ratify=true)
  * `SUSPENDED` → `REVOKED` (if ratify=false), or remain suspended (pick one rule and freeze it—do not branch by implementation convenience)

### 10.3 Invalid Boundary Test Injection (Harness)

The harness must be able to inject boundary faults deterministically to test rejection stability:

* wrong signer for Cycle N commit signature
* wrong signer for Cycle N+1 start signature
* missing pending_successor_key despite admitted proposal
* non-null pending_successor_key without admitted proposal

Each must fail with a stable reason code (`BOUNDARY_SIGNATURE_MISMATCH` or a more specific frozen code set if you add them—prefer one code unless you have a taxonomy already).

---

## 11) Lineage Integrity (Deterministic Only)

Maintain lineage as a computed property of the log:

* identity tip updates only on boundary activation
* successor must not create:

  * cycles (`IDENTITY_CYCLE`)
  * forks (`LINEAGE_FORK`)
  * alternate roots

Do not rely on external config to define the active sovereign.

---

## 12) Gate Instability Instrumentation (Mandatory)

Define and enforce gate instability exactly:

Gate instability occurs if, under identical input and identical state:

* a different gate rejects,
* a different reason code is emitted,
* a different rejection class is emitted,
* replay produces any of the above differences.

Log for each rejected SuccessionProposal and each boundary verification failure:

* `cycle_id`
* `state_hash_at_cycle_start`
* `artifact_id` (or boundary event id)
* `gate_id`
* `reason_code`
* `rejection_class`

Replay compare byte-for-byte.

Any mismatch is an X-3 failure.

---

## 13) Replay Harness Upgrade (X-3 Mandatory)

Replay must reconstruct deterministically:

1. Load constitution baseline; apply amendments per cycle (topological time).
2. Load and apply succession artifacts using binding order.
3. Record `pending_successor_key` in Cycle N state if admitted.
4. Sign/verify Cycle N commit under prior key.
5. Activate successor at boundary; verify Cycle N+1 header under successor key.
6. Apply treaty suspension at activation.
7. Apply ratifications per schedule.
8. Enforce density and action evaluation as usual.
9. Recompute hash chain; must match.

Replay function must satisfy:

```
state_sequence = F(frozen_artifacts, log_stream, kernel_version_id)
```

No global caches that bypass reconstruction.

Any divergence = X-3 failure.

---

## 14) Logging Extensions (X-3)

Append-only logs:

* `x3_sessions.jsonl`

  * `session_start_artifact_id`
  * `session_start_hash`
  * `session_id`
  * `N`
  * `kernel_version_id`
  * `constitution_hash_tip_at_start`
  * `treaty_schema_hash`
  * `seeds`
  * `rotation_schedule`
  * `ratification_schedule`

* `x3_metrics.jsonl` (per cycle)

  * `cycle_id`
  * `state_hash_start`
  * `state_hash_end`
  * `sovereign_public_key_active`
  * `pending_successor_key` (nullable)
  * `identity_chain_length`
  * `active_treaty_count`
  * `suspended_treaty_count`
  * `execution_counts` (sovereign vs delegated)
  * `refuse_count`
  * `boundary_event_flag` (true if activation occurred)

* `x3_boundary_events.jsonl` (per boundary)

  * `cycle_N`
  * `cycle_N_state_hash_end`
  * `prior_key`
  * `successor_key`
  * `pending_successor_key_recorded: bool`
  * `cycle_N_commit_signature_key`
  * `cycle_Nplus1_start_signature_key`
  * `boundary_verification_pass: bool`
  * `failure_reason` (if any)

Also extend existing traces to include:

* SuccessionProposal admission decisions
* lineage integrity checks and outcomes
* treaty suspension events at activation
* treaty ratification outcomes

---

## 15) Test Suite Additions (X-3)

Add tests corresponding to closure criteria and new boundary semantics:

1. **Boundary zipper test:** admit succession at Cycle N; Cycle N commit verifies under prior key; Cycle N+1 start verifies under successor key; replay matches.
2. **Wrong Cycle N signer test:** commit signature under wrong key fails with `BOUNDARY_SIGNATURE_MISMATCH`.
3. **Wrong Cycle N+1 signer test:** start signature under wrong key fails with `BOUNDARY_SIGNATURE_MISMATCH`.
4. **Duplicate succession same-cycle test:** second proposal rejected with `MULTIPLE_SUCCESSIONS_IN_CYCLE`.
5. **Invalid signature proposal test:** rejected with `SIGNATURE_INVALID`.
6. **Treaty suspension enforcement test:** delegated actions fail during suspension window with stable code.
7. **Ratification restore test:** ratified treaties regain authorization; delegated actions succeed only after ratification.
8. **Prior key privilege leak test:** any post-activation attempt to act as sovereign fails with `PRIOR_KEY_PRIVILEGE_LEAK`.
9. **Lineage fork/cycle test:** crafted proposal triggering cycle/fork fails with `IDENTITY_CYCLE` / `LINEAGE_FORK`.
10. **Multi-rotation session test:** ≥2 activations; zero divergence replay; identity_chain_length increments deterministically.

---

## 16) Failure Conditions (X-3)

X-3 fails if any occur:

* replay divergence
* dual sovereign roots
* replay-admissible lineage fork
* boundary signature mismatch
* prior key privilege leak post-activation
* delegated execution during treaty suspension
* treaty reactivation without ratification
* density bound breach at any execution point
* gate instability under identical input + identical state
* any side effect without an ExecutionWarrant

---

## 17) Definition of Done (X-3 Completion)

X-3 is complete when:

1. Parameters are frozen via admitted `X3SessionStart`.
2. ≥2 lawful successions admitted + activated across runs (at least one session with ≥2 rotations).
3. ≥1 unlawful succession rejected with correct reason code.
4. Boundary zipper verified (Cycle N commit under prior key; Cycle N+1 start under successor key).
5. Treaty suspension blocks delegated actions until ratified.
6. Ratified treaties regain functionality.
7. Prior key is zeroed post-activation; no privilege leak.
8. All replays pass with zero divergence.
9. All metrics and boundary logs are computed and append-only.

---

## 18) Explicit Do-Not-Do List (X-3 Regression Traps)

Do not implement:

* any wall-clock-based boundary logic
* any “best effort” header verification that tries multiple keys
* any implicit treaty inheritance across succession
* any partial-cycle sovereign activation
* any optimization that changes which gate fires or which reason code is emitted
* any external config for “current sovereign” during replay
* any behavior where multiple SuccessionProposals are admitted in a cycle
* any behavior where prior key retains implicit privileges after activation

Any of these invalidates X-3 determinism and singleton sovereignty guarantees.

---

## 19) Final X-3 Invariant

**Lineage is state.**
**Boundary signatures zip the chain.**
**Succession is admitted in-cycle, activated at boundary, and verified under the successor at cycle start.**
**Prior keys are zeroed.**
**Treaties suspend and must be explicitly ratified.**
**Determinism is audited via stable gates, stable reasons, and replay-identical hash chains.**

Proceed to code.
