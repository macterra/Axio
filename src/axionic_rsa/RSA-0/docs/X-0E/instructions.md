# RSA-X0E Implementation Instructions (Phase X-0E)

## 0) Prime Directive

**No side effects without a kernel-issued `ExecutionWarrant` referencing an admitted `ActionRequest`.**

Additionally:

**No execution may occur unless the destination enforces at-most-once semantics via `warrant_id` (check-then-act + startup reconciliation).**

Everything else is plumbing.

---

## 1) Repo Layout Additions (Do This First)

Extend the RSA-0 repo.

Add:

```
axionic-rsa/
  artifacts/
    phase-x/
      x-0e/
        rsa_constitution.v0.1.1.yaml
        rsa_constitution.v0.1.1.yaml.sha256
        x-0e_profile.v0.1.json

  cli/
    rsa.py
    commands/
      run.py
      replay.py

  logs/
    outbox.jsonl
    observations.jsonl
    artifacts.jsonl
    admission_trace.jsonl
    selector_trace.jsonl
    execution_trace.jsonl
    reconciliation_trace.jsonl

  replay/
    src/
      loader.py
      replayer.py
      jcs_canonicalize.py
      state_hash.py
      divergence.py

  runtime/
    src/
      host.py
      executor_notify.py
      log_append.py
      pinning.py
      net_guard.py
```

**Rules**

* Frozen constitution bytes live only under `artifacts/phase-x/**`.
* Runtime logs live only under `logs/**`.
* Logs are append-only.
* Kernel never mutates files under `artifacts/`.
* Replay uses **no model calls**, **no system clock**, **no randomness**.

---

## 2) Frozen Constitution Integrity Model

### 2.1 Active Constitution Source

At startup:

1. Load frozen constitution file (`rsa_constitution.v0.1.1.yaml`)
2. Canonicalize deterministically (**RFC 8785 JCS** for JSON inputs; YAML must be canonicalized into a deterministic JSON form before hashing)
3. Compute SHA-256
4. Compare to `.sha256` sidecar
5. Refuse to run if mismatch

Set:

* `active_constitution_hash = sha256(canonical_constitution_bytes)`

**Hard Rules**

* Constitution is immutable during run and replay.
* Constitution hash is included in warrant derivation and state-hash anchoring.
* Replay must refuse if constitution hash differs from run.

---

## 3) Deterministic Kernel Requirement (Closed Set)

X-0E requires that all replay-bound kernel logic is deterministic.

**Rules**

* Admission logic: deterministic code only.
* Selector logic: deterministic code only.
* No stochastic inference, no model calls, no hidden caches.
* Kernel must not call system clock or randomness APIs.
* Any “intelligence” output (if present upstream) must enter as a logged artifact and be treated as data, not recomputed logic.

---

## 4) Required CLI Surface

Implement:

```
rsa run --constitution artifacts/phase-x/x-0e/rsa_constitution.v0.1.1.yaml --log-dir ./logs/
rsa replay --constitution artifacts/phase-x/x-0e/rsa_constitution.v0.1.1.yaml --log-dir ./logs/
```

### `rsa run` must

1. Validate constitution integrity (Section 2).
2. Initialize kernel with `active_constitution_hash` and `kernel_version_id`.
3. Process observation stream (stdin, file, or test vector).
4. Canonicalize + hash artifacts deterministically.
5. Perform admission and selection.
6. Issue warrants deterministically.
7. Execute side effects only via warrant-gated executor.
8. Append logs (append-only, fsync discipline as implemented).
9. Emit per-cycle `state_hash`.

### `rsa replay` must

1. Validate constitution integrity (Section 2).
2. Reconstruct state exclusively from logs.
3. Recompute admission decisions.
4. Recompute selector outcomes.
5. Recompute deterministic warrants (including `warrant_id`).
6. Recompute full state hash chain and compare per-cycle.
7. Report divergence and stop.

**Replay Constraint**

* No model calls.
* No network calls.
* No system clock.
* No randomness.
* No mutable global cache.

---

## 5) Minimal Action Surface (X-0E)

X-0E requires exactly one real side effect to demonstrate embodiment.

### 5.1 `Notify` (Minimal Embodiment Action)

Side effect class: low.

Behavior:

* Append a JSONL record to `logs/outbox.jsonl`.

Required outbox fields:

* `warrant_id`
* `cycle_id`
* `artifact_id`
* `payload_hash`
* `message` (derived from `ActionRequest.message`)
* `timestamp` (deterministic, from observation)

**Hard Rules**

* Warrant required.
* Must be executed by host only (no kernel direct I/O).
* Must not perform any network I/O.
* Must be idempotent at destination (Section 6).

---

## 6) Execution Boundary (Crash-Safe At-Most-Once)

### 6.1 Check-Then-Act (Destination Idempotency)

Before executing `Notify(warrant)`:

1. Scan `outbox.jsonl` (or maintain an append-only index derived solely from it) for `warrant_id`.
2. If present: **do not execute**; log `DUPLICATE_WARRANT_REFUSED`.

Execution occurs only if `warrant_id` is absent.

### 6.2 Startup Reconciliation (Crash After Effect / Before Log)

On startup (prior to first new cycle):

1. Load `execution_trace.jsonl` into a set `executed_warrants` (derived).
2. Load `outbox.jsonl` into a set `effected_warrants` (derived).
3. For each `warrant_id ∈ effected_warrants \ executed_warrants`:

   * Append a reconciliation entry to `reconciliation_trace.jsonl`.
   * Append a synthetic `execution_trace` entry with:

     * `execution_status = SUCCESS`
     * `reason = RECONCILED_FROM_DESTINATION`

**Hard Rules**

* Reconciliation is append-only.
* Reconciliation must happen before any new warrant is executed.
* Replay must deterministically reproduce reconciliation behavior from logs alone.

---

## 7) Canonicalization and Hashing (Mandatory)

### 7.1 JSON Canonicalization

All JSON used for hashing must strictly follow:

* **RFC 8785 — JSON Canonicalization Scheme (JCS)**

No “sort keys” approximations allowed.

### 7.2 Artifact Hash

```
artifact_hash = SHA256(JCS(artifact_json))
```

### 7.3 Warrant Determinism

Derive:

```
warrant_id = SHA256(
  cycle_id || artifact_hash || selector_rank || active_constitution_hash
)
```

No random IDs.

### 7.4 State Hash Anchoring

Maintain hash chain:

```
state_hash[n] = SHA256(
  state_hash[n-1] ||
  artifacts[n] ||
  admission_trace[n] ||
  selector_trace[n] ||
  execution_trace[n]
)
```

Initial:

* `state_hash[0] = SHA256(active_constitution_hash || kernel_version_id)`

---

## 8) Deterministic Observation Envelope

Observations must be treated as data.

Each observation entry must include:

* `observation_id`
* `cycle_id` (or deterministically derivable cycle)
* `timestamp` (deterministic, part of observation)
* `source_label`
* `payload`

**Hard Rules**

* Kernel must never call system clock.
* Any time dependence must come from observation payload.
* Replay must reproduce identical observation stream from logs.

---

## 9) Logging Requirements (Append-Only)

Write these logs:

* `observations.jsonl`
* `artifacts.jsonl`
* `admission_trace.jsonl`
* `selector_trace.jsonl`
* `execution_trace.jsonl`
* `outbox.jsonl`
* `reconciliation_trace.jsonl` (if any)

Each log record must include:

* `cycle_id`
* `artifact_id` (if applicable)
* `gate`
* `result`
* `reason_code` (if rejection)
* `warrant_id` (if execution-related)
* `timestamp` (from observation)

**Rules**

* Append-only.
* Never rewrite/truncate.
* UTF-8 valid.
* Replay must fail on missing or reordered entries.

---

## 10) Host Failure Propagation (Execution Outcome Logging)

Execution trace must record outcome:

* `execution_status ∈ {SUCCESS, FAILURE}`
* `failure_reason` if FAILURE (e.g., disk full, permission denied)

If FAILURE:

* No side effect may be claimed as applied.
* Kernel must treat the world as unchanged for that warrant.

Replay must deterministically verify the same SUCCESS/FAILURE outcomes from logs.

---

## 11) Replay Harness Upgrade (Mandatory)

Replay must:

1. Load frozen constitution + verify hash.
2. Load logs in deterministic order.
3. Apply startup reconciliation deterministically (based on outbox vs execution_trace).
4. Recompute admission decisions.
5. Recompute selector outcomes.
6. Recompute warrants (`warrant_id`).
7. Recompute and compare state hash chain per cycle.
8. Fail fast on divergence.

Replay must satisfy:

```
state_sequence = F(log_stream, frozen_kernel, frozen_constitution)
```

No global cache allowed.

Any divergence = X-0E failure.

---

## 12) Test Suite Additions (X-0E)

Add tests:

1. Positive: single Notify request → admitted → warrant issued → outbox append → replay stable.
2. Negative: attempt to execute Notify without warrant → REFUSE + log.
3. Crash simulation A: effect written, execution_trace missing → restart triggers reconciliation → no duplicate write → replay stable.
4. Crash simulation B: execution_trace FAILURE recorded → outbox unchanged → replay stable.
5. Canonicalization parity: same artifact hashed in two runtimes yields identical hash (JCS conformance test).
6. Cross-machine replay: logs copied to fresh machine → identical state hash chain.
7. Selector determinism: same logs → identical selector_trace.

---

## 13) Failure Conditions (X-0E)

Phase X-0E fails if:

* Replay diverges.
* Any side effect occurs without a kernel-issued ExecutionWarrant.
* Constitution hash mismatch is ignored.
* Warrant IDs differ between run and replay.
* Destination idempotency is not enforced (duplicate warrant executes).
* Startup reconciliation is missing or nondeterministic.
* Any nondeterministic identifier appears.
* Any model call, network call, system clock call, or randomness enters replay-bound kernel logic.

---

## 14) Definition of Done (X-0E Completion)

X-0E complete when:

1. `rsa run` produces at least one real side effect under warrant gating.
2. `rsa replay` reproduces identical per-cycle state hashes from logs alone.
3. Constitution integrity check is enforced and refusal is correct on mismatch.
4. Destination idempotency + startup reconciliation prevents duplicate execution under crash scenarios.
5. JCS canonicalization produces cross-runtime hash parity.
6. All rejection paths and failures are logged and attributable.

---

## 15) Explicit Do-Not-Do List (X-0E Regression Traps)

Do not implement:

* Model calls in replay or kernel gates
* “Helpful” fallback semantics (e.g., execute without warrant if local)
* Using system time inside kernel
* Random UUIDs for artifacts or warrants
* Non-JCS “canonicalization”
* Mutable state that is not reconstructible from logs alone
* Network I/O for Notify or during replay
* Silent retries in the host without explicit warrant semantics

Any of these reintroduces proxy authority or breaks determinism.

---

## 16) Final X-0E Invariant

Physics (Kernel) is deterministic and replay-bound.
Law (Constitution) is frozen and hash-verified.
Execution is warrant-gated and at-most-once at the destination.
Logs are sufficient to reconstruct the full sovereign state sequence.

If implemented faithfully, the RSA becomes an executable, audit-grade sovereign artifact outside the lab.

Proceed to code.
