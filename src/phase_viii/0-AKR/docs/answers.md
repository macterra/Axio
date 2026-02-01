## Q1. Execution Harness Action Generation — operation vocabulary

**Resolution (binding):** define a **minimal fixed operation set** for AKR-0 only:

* `READ`
* `WRITE`

Operations are **opaque strings** (AST Spec §2.2), but the harness must fix a finite set to generate traffic deterministically.

**ActionRequest form (normative):**

* `action = (ResourceID, Operation)` with `Operation ∈ {READ, WRITE}`.

No other operations exist in AKR-0.

---

## Q2. Address Book Definition — size and ID format

**Resolution (binding):** Address Book is **static**, **ex ante**, **fixed for entire run** (already required by AIE).

**Default cardinality for AKR-0:**

* `|AddressBook| = 16`

**HolderID format:**

* opaque strings: `H0001 … H0016` (no semantic structure, no embedded metadata)

If a holder is unreachable, it **remains addressable** (AIE §5.3).

---

## Q3. Active Scope Pool size and collision probability (P_c)

You need a **closed-form, declarable** (P_c), not “empirical after the fact.”

### Scope Pool definition (binding, AKR-0 default)

Let:

* `ResourceID ∈ {R0000 … R2047}` (2048 resources)
* `Operation ∈ {READ, WRITE}`

Then the **Active Scope Pool** is the set of atomic scope elements:

* `Pool = {(Ri, op)}`

So:

* `M = |Pool| = 2048 × 2 = 4096`

### Authority scope shape (binding, AKR-0 default)

Each injected authority record binds **exactly one** atomic scope element (scope size = 1).
This keeps conflict math clean and structural.

### Collision probability definition (binding)

Define per-epoch collision probability as the probability of **at least one** duplicate atomic scope element among the **new authorities injected in that epoch**:

[
P_c ;=; 1 - \prod_{i=0}^{n-1}\frac{M-i}{M}
]

where:

* (M) is the pool size
* (n) is the number of authorities injected in that epoch

### Default parameters satisfying (P_c \ge 0.01)

Choose:

* `M = 4096`
* `n = 20 authorities injected per epoch` (Condition A and C; Condition B varies)

This yields:

* (P_c \approx 0.045) per epoch (comfortably ≥ 0.01, not absurdly hot)

**Answer to Opus options:** choose **(2)**: declare (P_c) analytically from (M) and (n). Do **not** “derive empirically.”

---

## Q4. Instruction budget (gas) magnitude

**Resolution (binding):** gas is counted in **logical operations**, not time. The unit is the runtime’s primitive step counter (comparisons, membership checks, record scans, hash steps).

**Default gas budgets (AKR-0):**

* `GAS_ACTION_EVAL = 50_000`
* `GAS_TRANSFORM = 100_000`
* `GAS_EPOCH_ADVANCE = 200_000` (because it may expire multiple records)

These are intentionally generous for a small-state calibration; they must be identical across platforms.

On exhaustion: **preserve state** and emit refusal/suspension per spec.

---

## Q5. Epoch advancement rule; expiry eager vs lazy

**Resolution (binding):** epoch advancement is driven by **explicit `EPOCH_TICK` inputs from the harness**.

* Each `EPOCH_TICK` increments `currentEpoch := currentEpoch + 1`.
* Expiry is evaluated **eagerly on epoch advance** (deterministic bulk pass).

No wall-clock. No implicit “advance after N inputs.” No “advance after state changes.”

---

## Q6. Canonical ordering algorithm for same-epoch batches

**Resolution (binding):** canonical ordering is:

1. Canonicalize each input event as minified JSON using **AST Spec Appendix C rules**.
2. Compute `h = SHA256(canonical_json_bytes)`.
3. Sort ascending by `(h_hex, canonical_json_lex)`.

No type priority. No arrival nonce. Arrival order is logged but **ignored** for semantics.

If two events are byte-identical, that is a harness bug:

```
INVALID_RUN / DUPLICATE_EVENT
```

---

## Q7. Conflict registration vs conflict detection

AST Spec has both:

* structural conflict detection criteria, and
* `Register Conflict` transformation.

**Resolution (binding): AKR-0 does both, with strict roles:**

1. **Detection is automatic** during admissibility evaluation and on authority injection.
2. When detection triggers, the kernel performs a **`REGISTER_CONFLICT` transformation automatically**, attributable to `SYSTEM_AUTHORITY`, with a deterministic conflict record.

This preserves:

* structural detection (no semantics)
* explicit logged state change (auditability)

If you require AIE to explicitly register conflicts, you create a loophole and reduce kernel integrity.

---

## Q8. Transformation request source (besides Create)

**Resolution (binding):**

* **Create Authority**: **AIE only** (open system).
* **Expire Authority**: **kernel automatic** on epoch advance (SYSTEM_AUTHORITY), logged as transformations.
* **Register Conflict**: **kernel automatic** (SYSTEM_AUTHORITY), logged as transformation.
* **Suspend/Resume/Revoke/Narrow/Resolve Conflict**: may originate as **TransformationRequest inputs from the harness**, **on behalf of a specific HolderID**, and are accepted iff the request is admissible under AST Spec rules:

  * requester must have an ACTIVE authority whose `PermittedTransformationSet` includes the transformation
  * and whose scope binds the affected scope elements exactly (structural)
  * and no conflicts/suspensions block it

No other sources exist.

This keeps “who is trying to do governance” separate from “who supplies authority.”

---

## Q9. Deadlock detection trigger and thresholds

**Resolution (binding): deadlock detection is automatic** after processing a canonical batch of inputs for an epoch, and also after each action refusal/execution event (cheap check).

Define:

* Let `A_batch` be the set of candidate actions proposed by the harness for the epoch.
* Let `A_adm` be the subset admissible under current Authority State.

Then:

1. If `A_adm` is empty for the epoch batch:

   * If there exists at least one lawful transformation admissible that could change admissibility → **Governance Deadlock not yet** (system still has a move).
   * If no lawful transformation is admissible → **Governance Deadlock**.
2. If conflicts exist that block all admissible actions and no destructive conflict resolution is admissible → **Conflict Deadlock**.
3. **Entropic Collapse** is declared iff:

   * `ASA == 0` (AST Spec §4), **and**
   * no admissible transformations exist that can increase ASA (since no creation internal).

No “N consecutive attempts” thresholds. No percentage heuristics.

---

## Q10. Run configuration — action count / sizing

AKR-0 is a calibration gate, not a statistical inference study.

**Resolution (binding, defaults):**

* Each condition (A/B/C) runs:

  * `E = 100 epochs`
  * `K = 20 action requests per epoch` (total `2000` actions per condition per seed)
* The harness also injects authorities per epoch according to the condition.

No wall-clock sizing. No “power” targets.

---

## Q11. Seeds and initial state

**Resolution (binding):**

* `S = 5 seeds per condition` (A/B/C), total 15 runs.
* Seeds are fixed integers, e.g.: `{11, 22, 33, 44, 55}`.

**Initial Authority State at epoch 0:**

* Empty for all conditions (clean start).

Condition-specific authority injection:

* **Condition A:** inject `n=20` authorities at epoch 0, then `n=20` per epoch.
* **Condition B:** inject `n=0` always.
* **Condition C:** inject `n=50` per epoch (hot regime), with deliberate conflict density.

All initial state hashes must be logged.

---

## Q12. Transformation whitelist — is EXPIRE automatic?

**Resolution (binding):** EXPIRE is **automatic kernel behavior** on epoch advance.

* It must be logged as explicit `EXPIRE_AUTHORITY` transformations attributable to `SYSTEM_AUTHORITY`.
* AIE may also issue authorities with `ExpiryEpoch = null` or explicit epochs, but AIE does not “trigger expiry.”

No dual-mode “either.” Keep it single and deterministic.

---

## Q13. Suspension semantics (kernel “suspends execution”)

You have two suspensions in play:

* **authority suspension** (AST Spec transformation)
* **execution suspension** (kernel output state)

**Resolution (binding):**

* `SUSPENSION_ENTERED` is **recoverable** within the same run.
* It is emitted when the kernel cannot proceed due to deterministic constraints (e.g., gas exhaustion, bounded computation) **without asserting deadlock**.
* Triggers:

  * gas exhaustion on evaluation or transformation
  * bounded computation limit exceeded
  * malformed-but-typed input that must be refused without state change (optional, but if you include it, preregister)

Rule:

* Suspension **must not** perform governance.
* Suspension must preserve state.
* Suspension must be logged and replayable.

If you want simpler: treat all suspension as refusal; but you already made suspension an explicit output, so it needs a trigger class.

---

## Q14. Logging schema — pre-ordering vs post-ordering; format

**Resolution (binding): log both.**

* Pre-ordering log: raw harness emission sequence (with epoch tags).
* Post-ordering log: canonical sorted sequence actually executed.

Format:

* **append-only JSONL** (one event per line), canonicalized per Appendix C for fields that are hashed.
* Maintain a **hash chain**:

  * `eventHash = SHA256(prevEventHash || canonicalEventBytes)`
  * log `eventHash` on each line

This makes tamper evidence and replay straightforward.

---

## Q15. Replay protocol — mode and comparison granularity

**Resolution (binding):** replay is a **separate verifier pass** that:

1. loads the post-ordering log,
2. re-executes deterministically,
3. checks:

   * **per-event state hash**
   * **per-event output**
   * **per-event eventHash chain**

Final state hash alone is insufficient (too easy to accidentally diverge and reconverge).

Replay result is PASS iff every step matches byte-for-byte.

---

## Q16. `SYSTEM_AUTHORITY` identity and representation

**Resolution (binding): `SYSTEM_AUTHORITY` is implicit and is not represented as a HolderID, AuthorityID, or Authority Record.**

* `SYSTEM_AUTHORITY` is an **attribution label** used in **logs only** for kernel-automatic transformations:

  * `EXPIRE_AUTHORITY`
  * `REGISTER_CONFLICT`
  * (optionally) `SUSPENSION_ENTERED` events

It is **not**:

* in the Address Book,
* a HolderID,
* an Authority Record,
* a privileged governor.

Rationale: representing it as an authority object creates a “hidden authority” surface and invites meta-permission leakage. AKR-0 needs a *mechanical* executor attribution, not an entity.

**Implementor rule:** any kernel-automatic transformation must carry `actor = SYSTEM_AUTHORITY` in logs; it must not reference a HolderID.

---

## Q17. Conflict density for Condition C

**Resolution (binding): Condition C uses deliberate overlap, not pure random.**

Pure random with `M=4096`, `n=50` yields only ~26% chance of at least one collision per epoch—too weak for a “saturation” condition. You need *guaranteed* contested scopes to exercise conflict machinery every epoch.

### Target (binding)

Per epoch in Condition C:

* at least **30%** of injected authorities must collide on scope elements with at least one other injected authority **in the same epoch**.

### Algorithm (binding, deterministic)

Let `n=50`. Construct scope assignments as:

* Choose `k=15` “hot” scope elements for the epoch (deterministically via PRNG).
* Assign `2` authorities to each hot scope element → `30` authorities guaranteed to collide (15 pairs).
* Assign remaining `20` authorities to distinct “cold” scope elements drawn without replacement from the pool excluding the hot set.

This guarantees:

* 30/50 = 60% are in collisions (≥ 30% requirement)
* conflict registration is exercised reliably
* still remains purely structural (no kernel feedback)

---

## Q18. `PermittedTransformationSet` structure (and where it lives)

**Resolution (binding): `PermittedTransformationSet` is an explicit field in each Authority Record, as already described in AIE v0.1 §5.2 and AST Spec §2.1.**

It is **not derived** from scope semantics. It is **not a separate meta-authority system**.

### Minimal allowed representation (binding)

`PermittedTransformationSet` is a finite set of transformation type codes drawn from:

* `SUSPEND_AUTHORITY`
* `RESUME_AUTHORITY`
* `REVOKE_AUTHORITY`
* `NARROW_SCOPE`
* `RESOLVE_CONFLICT`

(Exclude `CREATE_AUTHORITY` because creation is AIE-only; exclude `EXPIRE_AUTHORITY` and `REGISTER_CONFLICT` because those are kernel-automatic.)

### Authorization rule (binding)

A TransformationRequest is admissible iff:

1. requester has ≥1 ACTIVE authority record in Authority State whose `HolderID` matches requester,
2. requested transformation type ∈ requester’s `PermittedTransformationSet`,
3. requester’s authority scope includes the **exact atomic scope element(s)** affected by the transformation (equality/membership only),
4. no conflicts/suspensions block the transformation’s affected elements.

No inheritance, no containment, no implied governance.

---

## Q19. Conflict record structure and storage

**Resolution (binding): conflicts are stored in a separate global conflict registry in the Authority State, and referenced from each Authority Record’s `ConflictSet`.**

This matches AST Spec’s dual mention of “Conflict Set” in AR plus conflict handling sections, while keeping canonical structure explicit.

### ConflictRecord schema (binding)

A conflict record is:

* `conflictId` (opaque string, deterministic)
* `epochDetected` (integer)
* `scopeElements` (sorted list of atomic `[ResourceID, Operation]` tuples that are contested)
* `authorityIds` (sorted list of AuthorityIDs involved; size ≥2)
* `status` ∈ {`OPEN`, `RESOLVED`}

### Deterministic `conflictId` (binding)

`conflictId = "C:" + sha256(canonical_json({epochDetected, scopeElements, authorityIds}))`

### Storage (binding)

Authority State contains:

* `conflicts: [ConflictRecord...]` (sorted lexicographically by `conflictId`)
* Each Authority Record contains:

  * `conflictSet: [conflictId...]` sorted

Conflict resolution updates:

* ConflictRecord `status := RESOLVED`
* AuthorityRecord conflictSet may remain as historical reference (or may be pruned only via explicit logged rule). For AKR-0, keep it simple: **do not prune** conflictSet.

---

## Q20. Harness seeding — PRNG algorithm

**Resolution (binding): specify a single PRNG algorithm for the harness and kernel-side sampling to avoid cross-implementation drift.**

Use **PCG32** (well-known, simple, deterministic across languages). Seed is the fixed integer for the run; stream id fixed to 0.

* `PRNG = PCG32(seed, stream=0)`

All derived randomness must come from this PRNG only, including:

* selection of HolderIDs for injected authorities,
* selection of scope elements,
* ordering of any synthetic traffic generation.

No “implementation-defined PRNG.”

---

## Q21. TransformationRequest input schema and validation

**Resolution (binding): TransformationRequest is a typed event with canonical JSON form; no cryptographic signature is required in AKR-0.**

AKR-0 is not a custody/crypto test; it is an execution determinism test. Introducing signatures creates needless complexity and platform variance. Authority is validated structurally from the Authority State.

### Schema (binding)

```json
{
  "type": "TransformationRequest",
  "epoch": <int>,
  "requestId": "<opaque>",
  "requesterHolderId": "<HolderID>",
  "transformation": "<enum>",
  "targets": {
    "authorityIds": ["A1", "A2", ...],
    "scopeElements": [["R0123","READ"], ...],
    "conflictIds": ["C:...", ...]
  }
}
```

Rules:

* `requestId` is deterministic: `"TR:" + sha256(canonical_json(event_without_requestId))`
* `targets` must include only the fields needed for that transformation; unused fields must be present as `null` or empty arrays per your canonicalization policy.

### Validation (binding)

Kernel validates admissibility using Q18 rule set:

* requester must hold an ACTIVE authority whose `PermittedTransformationSet` includes transformation,
* requester scope must cover exact affected scopeElements,
* conflicts/suspensions respected.

No external proofs.

---

## Q22. Gas counting — what costs gas?

**Resolution (binding): define a deterministic, structural cost model with fixed unit costs per primitive operation, and mandate that gas accounting is a pure function of the canonical input + current Authority State size.**

### Gas primitives (binding)

Use these costs:

* `C_HASH = 50` per SHA-256 over canonical bytes (count once per event hash computation)
* `C_COMPARE = 1` per string compare / tuple compare
* `C_SET_MEM = 5` per membership test in a sorted array (binary search assumed)
* `C_SCAN_AR = 10` per Authority Record scanned
* `C_UPDATE = 20` per Authority Record updated (immutable replace)
* `C_LOG = 10` per log event emitted

### Evaluation costs (binding)

* Admissibility check cost includes:

  * scan of relevant authorities: `C_SCAN_AR * (#authorities)`
  * membership tests for scope elements: `C_SET_MEM * (#checks)`
* Conflict detection cost includes:

  * comparisons across active authority scopes is **not quadratic** because scopes are atomic; implement via map from scopeElement → list(authorityId). Cost linear in number of active atomic bindings:

    * `C_UPDATE * (#bindings processed)` with bindings = sum over authorities of scope size (scope size 1 in baseline)

This is enough to make gas deterministic and comparable across platforms.

---

## Q23. Replay failure classification

**Resolution (binding): replay divergence emits `INVALID_RUN / NONDETERMINISTIC_EXECUTION` and must report the first divergent event index and the first mismatched artifact.**

### Required divergence report fields (binding)

* `divergenceEventIndex` (0-based)
* `expectedEventHash`
* `observedEventHash`
* `expectedStateHash`
* `observedStateHash`
* `expectedOutput`
* `observedOutput`

No new taxonomy. Keep it aligned with the spec: replay failure means the run is not a valid AKR-0 run.

---
---

## Q24. Authority Record — complete canonical schema

**Resolution (binding):** your proposed schema is *almost* correct. Two corrections:

1. **`status` and temporal fields must match AST Spec naming**
2. **Field order must be canonical**

### Canonical Authority Record schema (AKR-0)

```json
{
  "authorityId": "<AuthorityID>",
  "holderId": "<HolderID>",
  "origin": "<opaque-origin-ref>",
  "scope": [["R0000","READ"]],
  "status": "ACTIVE|SUSPENDED|REVOKED|EXPIRED",
  "startEpoch": <int>,
  "expiryEpoch": <int|null>,
  "permittedTransformationSet": ["SUSPEND_AUTHORITY", "..."],
  "conflictSet": ["C:...", "..."]
}
```

**Notes (binding):**

* `origin` is required by AST Spec §2.1 (“Origin Reference”); content is opaque.
* `startEpoch` replaces `creationEpoch` (AST terminology).
* `conflictSet` may be empty but must be present.
* All arrays are **sorted lexicographically**.

---

## Q25. AuthorityID generation rule

**Resolution (binding):** AuthorityIDs are **deterministic content hashes**, not counters or harness strings.

### AuthorityID rule (binding)

```
authorityId = "A:" + sha256(
  canonical_json(
    record_without_authorityId_and_conflictSet
  )
)
```

**Rationale:**

* Ensures deterministic replay
* Prevents “same authority, different ID” divergence
* Aligns with conflictId determinism

Counters (`A0001`) are forbidden. Harness-supplied IDs are forbidden.

---

## Q26. Scope element representation (scope size = 1)

**Resolution (binding):** scope is **always an array of tuples**, even for size 1.

Correct canonical form:

```json
"scope": [["R0123","READ"]]
```

The bare-tuple form is **invalid**.
This preserves uniform hashing and AST Appendix C conformance.

---

## Q27. Authority State — complete schema

**Resolution (binding):** Authority State contains **only structural governance data**.

### Canonical Authority State schema

```json
{
  "stateId": "<sha256>",
  "currentEpoch": <int>,
  "authorities": [<AuthorityRecord>, ...],
  "conflicts": [<ConflictRecord>, ...]
}
```

**Explicit exclusions (binding):**

* no `gasConsumed`
* no `eventIndex`
* no counters, metrics, or telemetry

Those belong **only in logs**, never in state.

---

## Q28. `NARROW_SCOPE` semantics with scope size = 1

**Resolution (binding):** `NARROW_SCOPE` is **defined but degenerate** in AKR-0.

Rules:

* Narrowing a single-element scope to empty is **forbidden**.
* Attempting to do so yields:

  ```
  INVALID_TRANSFORMATION / EMPTY_SCOPE
  ```
* `NARROW_SCOPE` therefore has **no successful application** in the AKR-0 baseline.

**Implication:**
`NARROW_SCOPE` exists for forward compatibility but is **unused** in AKR-0 experiments.

Do **not** introduce multi-element scopes just to exercise it.

---

## Q29. `RESOLVE_CONFLICT` mechanics

**Resolution (binding): destructive means *authority destruction*, not arbitration.**

### What RESOLVE_CONFLICT does (binding)

* A `RESOLVE_CONFLICT` transformation **must**:

  * REVOKE **at least one** authority participating in the conflict
  * Update the ConflictRecord `status := RESOLVED`

Forbidden:

* winner selection
* priority rules
* partial resolution
* compromise
* leaving all authorities intact

### Who may issue RESOLVE_CONFLICT

A holder may issue `RESOLVE_CONFLICT` iff:

1. they hold an ACTIVE authority whose:

   * `permittedTransformationSet` includes `RESOLVE_CONFLICT`, and
   * scope exactly binds the contested scope element(s)
2. the conflict is OPEN

There is **no special privilege** for “neutral” or third-party holders.

`SYSTEM_AUTHORITY` does **not** resolve conflicts.

---

## Q30. Event type enumeration (canonical ordering universe)

**Resolution (binding):** the complete event type set is exactly four.

### Canonical event types

1. `EPOCH_TICK`
2. `AuthorityInjection` *(from AIE)*
3. `TransformationRequest`
4. `ActionRequest`

**Rules (binding):**

* `AuthorityInjection` is a distinct event type.
* It is **not** bundled with `EPOCH_TICK`.
* All four participate equally in canonical ordering via hash sort.
* No priority by type.

---

## Q31. Condition B — what the harness injects

**Resolution (binding): Condition B is an empty-authority stress test, not a null run.**

In Condition B, the harness **still injects**:

1. `EPOCH_TICK` events — **yes**
2. `ActionRequest` events — **yes**
3. `TransformationRequest` events — **yes**, but all must fail admissibility

What it injects **zero of**:

* `AuthorityInjection` events

**Purpose:**
To verify that:

* refusal semantics work,
* deadlock classification works,
* the kernel does not hallucinate authority,
* governance absence is handled deterministically.

A “do nothing” Condition B is invalid.

---

## Final lock-in summary (Q24–Q31)

| Topic                  | Binding decision                                         |
| ---------------------- | -------------------------------------------------------- |
| AuthorityRecord schema | Explicit, canonical, includes origin + PTS + conflictSet |
| AuthorityID            | Deterministic hash-based                                 |
| Scope representation   | Always array-of-tuples                                   |
| Authority State        | Only epoch + authorities + conflicts                     |
| NARROW_SCOPE           | Defined but unusable in AKR-0                            |
| RESOLVE_CONFLICT       | Destructive revocation only                              |
| Event types            | Exactly 4                                                |
| Condition B            | Actions + ticks + transforms, zero authorities           |

---

## Q32. Origin Reference content (`origin` in AuthorityRecord)

**Resolution (binding):** `origin` must reference the **AuthorityInjection event hash**.

For any AIE-injected authority record:

* `origin = "AIE:" + <authorityInjectionEventHashHex>`

Where `<authorityInjectionEventHashHex>` is the SHA-256 of the canonical JSON of the **AuthorityInjection event** (see Q33), excluding no fields.

Rationale: this is

* deterministic,
* audit-linked,
* provenance-correct,
* non-semantic,
* and ties authority to the sole lawful creation channel (AIE).

No placeholders. No seed/epoch strings. No external opaque markers.

---

## Q33. AuthorityInjection event schema

**Resolution (binding):** `AuthorityInjection` is a canonical typed event with deterministic `eventId`.

### Canonical schema

```json
{
  "type": "AuthorityInjection",
  "epoch": <int>,
  "eventId": "<EventID>",
  "authority": {
    "authorityId": "<AuthorityID>",
    "holderId": "<HolderID>",
    "origin": null,
    "scope": [["R0000","READ"]],
    "status": "ACTIVE",
    "startEpoch": <int>,
    "expiryEpoch": <int|null>,
    "permittedTransformationSet": ["..."],
    "conflictSet": []
  }
}
```

**Binding rules:**

* In the nested `authority` object inside AuthorityInjection, **`origin` MUST be `null`**.

  * Reason: `origin` is defined to reference the injection event hash, which is not known until the event itself is canonically formed.
* After canonicalization and hashing of the full AuthorityInjection event, the runtime must set:

  * `authority.origin = "AIE:" + <authorityInjectionEventHashHex>`
  * and recompute `authorityId` deterministically using the Q25 rule **over the post-filled authority record**.
* The Authority State stores only the **post-filled** authority record.

### EventID rule (binding)

`eventId = "EI:" + sha256(canonical_json(event_without_eventId))`

No harness-supplied opaque IDs.

---

## Q34. `EPOCH_TICK` event schema

**Resolution (binding):** Epoch is advanced only by explicit tick events. Ticks are minimal and deterministic.

### Canonical schema

```json
{
  "type": "EPOCH_TICK",
  "eventId": "<EventID>",
  "targetEpoch": <int>
}
```

**Binding rules:**

* `targetEpoch` must equal `currentEpoch + 1` at the moment the tick is applied.
* If not, the run is invalid:

```
INVALID_RUN / EPOCH_DISCONTINUITY
```

### EventID rule (binding)

`eventId = "ET:" + sha256(canonical_json(event_without_eventId))`

---

## Q35. `ActionRequest` event schema (and requester requirement)

**Resolution (binding):** requester identity must be explicit and structural. Yes: `requesterHolderId` is required.

### Canonical schema

```json
{
  "type": "ActionRequest",
  "epoch": <int>,
  "requestId": "<RequestID>",
  "requesterHolderId": "<HolderID>",
  "action": [["R0123","READ"]]
}
```

**Binding rules:**

* `action` is a **scope-shaped value**: an array of atomic `[ResourceID, Operation]` tuples.
* For AKR-0 baseline, `action` must have length 1.
* `epoch` is the epoch at which the request is submitted.
* `requestId = "AR:" + sha256(canonical_json(event_without_requestId))`.

Rationale: without requester identity, authority can’t be attributed structurally; you’d implicitly create “anonymous actor” semantics.

---

## Q36. `permittedTransformationSet` for AIE-injected authorities

**Resolution (binding): condition-dependent, preregistered, non-adaptive.**

We need **some** lawful governance capability in Conditions A and C to avoid trivial governance deadlock and to exercise transformation pathways; but it must not be kernel-adaptive.

### Binding PTS assignment policy

* **Condition A (baseline executability):**

  * 80% of injected authorities: `permittedTransformationSet = []`
  * 20% of injected authorities: `permittedTransformationSet = ["REVOKE_AUTHORITY", "RESOLVE_CONFLICT"]`

* **Condition B (no authority):**

  * no injections → N/A

* **Condition C (conflict saturation):**

  * 50% of injected authorities: `[]`
  * 50%: `["REVOKE_AUTHORITY", "RESOLVE_CONFLICT"]`

**Notes (binding):**

* `NARROW_SCOPE` remains unused/degenerate in AKR-0 baseline (Q28).
* `SUSPEND_AUTHORITY` / `RESUME_AUTHORITY` are excluded in AKR-0 to reduce state branching and keep the calibration focused on conflict + expiry + refusal mechanics.
* Assignment must be deterministic from PRNG stream.

---

## Q37. Deadlock declaration — output vs state vs termination

**Resolution (binding):** `DEADLOCK_DECLARED` is an **output event only** (logged), does **not** mutate Authority State, and causes **run termination** for AKR-0.

Rationale:

* AKR-0 is a calibration gate; once deadlock is detected under its rules, continuing is only generating redundant refusals.
* Termination gives a crisp, audit-friendly end condition and prevents ambiguous “deadlocked but still processing” behavior.

### Binding behavior

* Upon deadlock detection:

  * emit `DEADLOCK_DECLARED` with subtype (Conflict/Governance/Entropic)
  * halt processing immediately
  * finalize run classification per AKR-0 (PASS/FAIL/INVALID depending on cause and invariants)

Deadlock is not a “state flag.” It is a terminal diagnostic event.

---

## Q38. Gas exhaustion mid-batch

**Resolution (binding):** gas exhaustion halts the batch immediately via `SUSPENSION_ENTERED` and terminates the run as **INVALID**.

Why INVALID? Because if you allow deferral or partial refusal strategies, you create additional policy degrees of freedom. AKR-0 is supposed to be a **sanity check**, and gas budgets are preregistered. If you can’t process a preregistered batch under preregistered budgets, the run configuration is invalid.

### Binding behavior

* If gas is exhausted during processing of an ordered batch:

  1. preserve Authority State unchanged for the current event
  2. emit `SUSPENSION_ENTERED / GAS_EXHAUSTED`
  3. terminate run with:

```
INVALID_RUN / GAS_BUDGET_UNSATISFIED
```

No deferral. No “refuse remainder.” No continuing.

---

## Q39. Harness `TransformationRequest` generation (Conditions A and C)

**Resolution (binding):** harness generates **targeted** transformation requests, but targeting is based only on the **post-ordering log replay state** (i.e., deterministic and derived, not adaptive to runtime performance).

In other words: the harness is a deterministic traffic generator with full knowledge of its own planned stream. It may choose targets **because it can simulate the state**. That’s not “feedback,” it’s “preregistered scripted traffic.”

### Binding policy

* **Condition A:**

  * Generate **no** TransformationRequests.
  * Goal is pure executability and refusal correctness under stable authority.

* **Condition B:**

  * Generate `k=5` TransformationRequests per epoch, uniformly across:

    * `REVOKE_AUTHORITY`
    * `RESOLVE_CONFLICT`
  * All must fail admissibility due to empty authority state.
  * Purpose: prove no hallucinated authority.

* **Condition C:**

  * Generate `k=10` TransformationRequests per epoch:

    * 70% `RESOLVE_CONFLICT` targeting currently OPEN conflicts (deterministically chosen by sorted conflictId)
    * 30% `REVOKE_AUTHORITY` targeting authorities participating in OPEN conflicts (deterministically chosen by sorted authorityId)
  * Requests are issued by holders that *may or may not* have permission; failures are allowed and logged.

This exercises:

* transformation admissibility logic,
* destructive-only conflict resolution pathway,
* determinism under conflict churn.

No random “spray.” No kernel-peeking at outcomes; only deterministic selection based on precomputable state.

---

