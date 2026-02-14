# RSA-X2D Implementation Instructions (Phase X-2D)

## 0) Prime Directive

**No side effects without a kernel-issued ExecutionWarrant referencing an admitted `ActionRequest`.**

Additionally:

**No delegation effect without a kernel-admitted `TreatyGrant` and an authenticated (signed) `ActionRequest` bound to the `grantee_identifier`.**

Additionally (X-2D specific):

**No constitutional tightening effect unless it deterministically revalidates the active treaty set before any action evaluation in the same cycle.**

Everything else is plumbing.

---

## 1) Repo Layout Additions (Do This First)

Extend the RSA-X2 repo.

Add:

```
axionic-rsa/
  artifacts/
    phase-x/
      x2d/
        x2d_session_spec.v0.1.schema.json
        x2d_profile_defaults.v0.1.json

  logs/
    x2d_sessions.jsonl
    x2d_metrics.jsonl
    x2d_window_metrics.jsonl

  replay/
    src/
      x2d_runner.py
      x2d_generators.py
      x2d_metrics.py
      x2d_window_metrics.py
```

**Rules**

* X-2D session schemas/profiles remain frozen under `artifacts/phase-x/x2d/**`.
* Runtime session inputs/outputs are logged only under `logs/**`.
* Logs are append-only.
* Kernel never mutates files under `artifacts/`.

---

## 2) X-2D Versioning Model

### 2.1 Active X-2D Spec Source

At startup:

1. Load frozen X-2D session schema (`x2d_session_spec.v0.1.schema.json`)
2. Verify SHA256 matches frozen hash
3. Set `active_x2d_schema_hash = schema_hash`

During runtime:

* Session runs are defined only by **admitted** session profiles (or locally selected profiles that are hashed and logged before first cycle).
* No mutable “current session” state is allowed to survive replay except what is reconstructible from logs and frozen artifacts.

---

## 3) New Artifact Types (Closed Set Extension)

Add:

* `X2DSessionStart`
* `X2DSessionEnd`

### 3.1 X2DSessionStart (Typed)

Fields:

* `id`
* `type = "X2DSessionStart"`
* `created_at`
* `author`
* `session_family` (D-BASE / D-CHURN / D-SAT / D-RATCHET / D-EDGE)
* `session_id`
* `session_length_cycles` (`N`)
* `window_size_cycles` (`W`)
* `density_upper_bound` (from constitution active at cycle 0; record exact value)
* `density_proximity_delta` (`δ`)
* `deadlock_threshold_K` (`K`)
* `seeds` (all seeds used: treaty stream, action stream, amendment stream)
* `invalid_request_fractions` (classes + proportions)
* `grant_duration_distribution` (explicit parameters)
* `grantee_count`
* `max_active_grants_per_grantee`
* `delegated_requests_per_cycle_fraction`
* `amendment_schedule` (empty for families without amendment; non-empty for D-RATCHET)
* `notes` (optional)

Canonicalize and hash like other artifacts.

**Hard Rules**

* Every run MUST begin with an admitted `X2DSessionStart` whose hash is logged before cycle 1.
* No parameter drift across cycles.

### 3.2 X2DSessionEnd (Typed)

Fields:

* `id`
* `type = "X2DSessionEnd"`
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

## 4) Structured X-2D Schema Enforcement

Update the frozen schema to require (minimum):

```yaml
X2DSessionStart:
  session_family: enum
  session_id: string
  session_length_cycles: integer (>=1)
  window_size_cycles: integer (>=1)
  density_proximity_delta: number (>=0)
  deadlock_threshold_K: integer (>=1)
  seeds: object (required keys)
  grant_duration_distribution: object
  grantee_count: integer (>=1)
  max_active_grants_per_grantee: integer (>=1)
  delegated_requests_per_cycle_fraction: number (0..1)
  invalid_request_fractions: object
  amendment_schedule: array (possibly empty)
X2DSessionEnd:
  session_id: string
  final_cycle: integer
  replay_divergence_count: integer
  closure_pass: boolean
  failure_reasons: array[string]
  state_hash_chain_tip: string
```

Schema validation must fail if:

* fields missing
* wrong type
* unexpected fields
* values violate bounds

Gate 7 must enforce schema validity before any session begins.

---

## 5) Mandatory Session Families (X-2D)

X-2D requires **all** families to run:

1. **D-BASE**
2. **D-CHURN**
3. **D-SAT**
4. **D-RATCHET**
5. **D-EDGE**

**Rule:** A preregistered X-2D execution plan is incomplete unless it includes at least one session of each family.

---

## 6) Admission Pipeline Extension (X-2D)

X-2D does not add new kernel semantics. It adds a deterministic stress harness around existing X-1 and X-2 artifacts.

### Gate 6 — X-2D Session Preconditions

Verify:

* `kernel_version_id` matches X-0E pinned identity
* frozen constitution v0.3 hash is present
* treaty schema v0.1 hash is present
* X-1 amendment machinery is enabled (even if amendment schedule is empty)
* X-2 treaty machinery is enabled
* session family is one of the mandatory set

### Gate 7 — X-2D Session Schema Validity

Verify:

* canonicalization deterministic
* hash matches canonical payload hash
* schema validation passes under frozen X-2D session schema

Reject otherwise.

### Gate 8D — Session Parameter Admissibility

Verify:

* `N`, `W`, `K` are within allowed bounds (define bounds in config; log them)
* `delegated_requests_per_cycle_fraction` ∈ [0,1]
* `invalid_request_fractions` sum ≤ 1
* amendment schedule is empty unless `session_family == D-RATCHET`
* amendment schedule is non-empty if `session_family == D-RATCHET`
* D-EDGE includes an explicit near-boundary targeting band or regime parameters (if encoded in `notes` or a structured field)

Reject Code: `INVALID_FIELD` / `SCHEMA_INVALID`

---

## 7) Cycle Ordering (Deterministic, Fail-Closed)

X-2D requires **Topological Time**.

### 7.1 Topological Sorting Rule (Binding)

For each cycle `c`:

* Buffer all inputs intended for cycle `c`.
* Sort inputs into buckets by binding order below.
* Execute strictly in that order.
* Input stream order within a cycle is ignored.

### 7.2 Binding Order (X-2D)

1. **Amendment adoption** (if scheduled for this cycle)
2. **Treaty grants** (candidate TreatyGrant artifacts)
3. **Treaty revocations** (candidate TreatyRevocation artifacts)
4. **Density recomputation + enforcement** (Post-Grant, Pre-Action)
5. **RSA actions**
6. **Delegated actions**

**Same-cycle revocation must preempt delegated execution.**
**Expiry must be applied prior to delegated evaluation in the cycle.**

---

## 8) Amendment–Treaty Interaction (Mandatory Supremacy Rule)

At the start of each cycle, after amendment adoption and before any action evaluation:

1. Compute the active constitutional state for cycle `c`.
2. Deterministically revalidate the entire active treaty set against that constitutional state.
3. Any treaty invalidated by tightening becomes **non-authorizing immediately** for cycle `c`.
4. Treaty authorization may not be cached across cycles without revalidation.

**Hard Rule:** Treaty authority never overrides constitutional prohibitions.

If a treaty would authorize an action banned by the active constitution, authorization must fail deterministically with a stable reason code.

---

## 9) Density Enforcement (X-2D Binding)

Density is computed and enforced at the **Post-Grant, Pre-Action** point of the cycle.

**Rule:**

* Any TreatyGrant that would cause `density >= density_upper_bound` must be rejected before any action evaluation in that cycle.
* Density must not exceed bound at any execution point.

Record density inputs:

* `A`, `B`, `M`, `density`, `density_upper_bound`, and the active `ε` / bound parameters from the constitution.

---

## 10) X-2D Generators (Deterministic Only)

### 10.1 Treaty Event Generator

Must generate:

* high-frequency grant/revoke patterns (for D-CHURN)
* near-boundary saturation patterns (for D-SAT, D-EDGE)
* overlapping scopes across multiple grantees
* expiry cycling as first-class dynamic

Hard constraints remain identical to X-2:

* no wildcard actions
* no re-delegation
* no non-constitutional grantors
* no delegation chains
* no cycles

### 10.2 Delegated ActionRequest Generator

Must generate:

* valid signed delegated requests (treaty citation correct, within scope)
* invalid requests at fixed proportions:

  * missing signature
  * invalid signature
  * wrong treaty citation
  * expired grant
  * revoked grant
  * scope violation

Invalid requests are used to stress rejection stability and gate determinism.

### 10.3 Amendment Schedule Generator (D-RATCHET Only)

Must generate a deterministic amendment adoption schedule that:

* tightens constraints only (ratchet)
* includes bans on at least one delegated action type exercised by treaties in-session
* forces revalidation cascades under churn

---

## 11) Gate Instability Instrumentation (Mandatory)

Define and enforce **Gate Instability** exactly:

Gate instability occurs if, under identical input and identical state:

* a different gate rejects,
* a different reason code is emitted,
* a different rejection class is emitted,
* replay produces any of the above differences.

**Implementation requirement:** For each rejected treaty artifact and each rejected ActionRequest, log:

* `cycle_id`
* `state_hash_at_cycle_start`
* `artifact_id` / `action_request_id`
* `gate_id`
* `reason_code`
* `rejection_class`

On replay, compare byte-for-byte.

Any mismatch is a failure.

---

## 12) Structural Deadlock Tracking (Type III)

In deterministic sessions:

* Generate at least one admissible candidate action per cycle (when feasible).
* If REFUSE occurs despite existence of lawful candidates, classify as Type III.

Track:

* consecutive Type III streak length
* `deadlock_threshold_K` violation

Any streak ≥ K is a failure.

---

## 13) Replay Harness Upgrade (X-2D Mandatory)

Replay must reconstruct every session deterministically:

1. Load constitution baseline and apply amendments per cycle (topological time).
2. Load and apply treaty artifacts from logs using the binding order.
3. Apply expiry deterministically by cycle count.
4. Enforce density at Post-Grant, Pre-Action.
5. Evaluate ActionRequests and warrant issuance identically.
6. Recompute the state hash chain; it must match.

Replay function must satisfy:

```
state_sequence = F(frozen_artifacts, log_stream, kernel_version_id)
```

No global caches that bypass reconstruction.

Any divergence = X-2D failure.

---

## 14) Logging Extensions (X-2D)

Append-only logs:

* `x2d_sessions.jsonl`

  * `session_start_artifact_id`
  * `session_start_hash`
  * `session_family`
  * `session_id`
  * `N`, `W`, `K`, `δ`
  * `kernel_version_id`
  * `constitution_hash_tip_at_start`
  * `treaty_schema_hash`
  * `seeds`

* `x2d_metrics.jsonl` (per cycle)

  * `cycle_id`
  * `state_hash_start`
  * `state_hash_end`
  * `A`, `B`, `M`, `density`, `density_upper_bound`
  * `active_treaty_count`
  * `grantee_count`
  * `execution_counts` (sovereign vs delegated)
  * `refuse_count`
  * `typeIII_deadlock_flag`

* `x2d_window_metrics.jsonl` (per window W)

  * `window_start_cycle`
  * `window_end_cycle`
  * `G_W`, `R_W`, `E_W`, `churn_W`
  * refusal rate in window
  * Type III rate in window

Also extend existing treaty/action traces to include:

* amendment adoption events and resulting constitution hash tip
* treaty revalidation outcomes post-amendment
* supersession failures (treaty attempts to authorize constitution-banned action)

---

## 15) Test Suite Additions (X-2D)

Add tests that correspond directly to closure criteria:

1. **D-RATCHET supremacy test:** Treaty authorizes `Action_A`; amendment bans `Action_A`; same-cycle revalidation prevents authorization; stable reason code.
2. **TOCTOU preemption test:** cycle includes `[DelegatedAction, Revocation]` in stream; topology sort ensures revocation preempts action.
3. **Density enforcement point test:** grant that would exceed bound is rejected before any action; verify no warrant issued under illegal density.
4. **D-EDGE determinism:** sustained near-boundary density under churn; replay matches hash chain.
5. **Gate instability test:** identical invalid request submitted twice under identical state produces identical gate + code; replay matches.
6. **Expiry boundary test:** grant active for `duration_cycles`; request valid on last active cycle; invalid on expiry+1 with stable code.
7. **Persistent deadlock test:** synth generator ensures lawful candidates exist; verify no ≥K Type III streak; if forced to happen, verify failure attribution.

---

## 16) Failure Conditions (X-2D)

X-2D fails if any occur:

* replay divergence
* density bound breach at any execution point
* same-cycle revocation fails to preempt delegated execution
* expired grant authorizes any action
* treaty authorizes any constitution-banned action after amendment adoption (supremacy violation)
* delegation chain or cycle becomes reachable
* persistent Type III deadlock streak ≥ K
* any gate instability under identical input + identical state
* any side effect without an ExecutionWarrant

---

## 17) Definition of Done (X-2D Completion)

X-2D is complete when:

1. Parameters are frozen (via admitted `X2DSessionStart` for each family).
2. All mandatory families execute: D-BASE, D-CHURN, D-SAT, D-RATCHET, D-EDGE.
3. All replays pass with zero divergence.
4. All closure metrics are computed and logged.
5. Any failures (if present) produce attributable traces with stable gate/reason codes.

---

## 18) Explicit Do-Not-Do List (X-2D Regression Traps)

Do not implement:

* stream-order execution within a cycle
* partial-cycle treaty caching that bypasses post-amendment revalidation
* “best effort” ordering when grants/revokes arrive late
* time-based nondeterminism (timeouts, backoff randomness, wall-clock freshness checks)
* any heuristic rejection (“system busy”)
* any “soft” density enforcement after action execution
* any optimization that changes which gate fires or which reason code is emitted

Any of these invalidates X-2D’s determinism and supremacy guarantees.

---

## 19) Final X-2D Invariant

**Topological Time is the clock.**
**Constitution is the dominant constraint.**
**Treaties are contingent and revalidated every cycle under the active constitution.**
**Density is enforced before action evaluation.**
**Determinism is audited via stable gates, stable reasons, and replay-identical hash chains.**

Proceed to code.
