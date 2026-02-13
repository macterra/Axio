# **Axionic Phase X-0E — RSA-0 Operational Harness Freeze**

*(Executable Embodiment of a Frozen Sovereign Substrate — Normative, preregistration-ready)*

* **Axionic Phase X — RSA Construction Program**
* **Substage:** **X-0E**
* **Status:** DRAFT (preregistration candidate)
* **Prerequisites:**

  * **X-0 — RSA-0 Minimal Sovereign Agent — CLOSED — POSITIVE**
  * **Frozen Constitution v0.1.1 — SHA-256 recorded**
  * **RSA-0 Kernel + Replay Harness — CLOSED — POSITIVE**

---

## 0. Purpose

X-0 proved that a Reflective Sovereign Agent (RSA) can exist as an execution-bound substrate under a frozen constitution with warrant-gated side effects and deterministic replay.

X-0E proves something narrower and strictly operational:

> A frozen RSA-0 can be packaged and executed as a runnable artifact outside research scaffolding, producing real side effects under warrant gating, while preserving append-only logging and deterministic replay from logs alone.

X-0E introduces no new invariants.
X-0E modifies no kernel physics.
X-0E alters no constitutional semantics.

It freezes embodiment.

---

## 1. Prime Directive (Operational Form)

All X-0 invariants remain binding.

Additionally:

> No side effect may occur unless:
>
> 1. An admitted `ActionRequest` exists.
> 2. A kernel-issued `ExecutionWarrant` referencing that `ActionRequest` exists.
> 3. The executor applies the warrant at most once.
> 4. The execution outcome (success or failure) is logged in append-only form.

Everything else is packaging.

---

## 2. Scope

X-0E defines a minimal runnable distribution that:

* executes at least one real side effect under warrant gating,
* produces append-only artifact + warrant logs,
* replays deterministically from logs alone,
* runs via CLI entrypoint,
* requires no research harness,
* introduces no semantic arbitration.

X-0E is single-agent only.

Delegation, amendment, succession, networking, distributed execution, and key attestation are out of scope.

---

## 3. Deterministic Kernel Requirement

X-0E requires that all replay-bound kernel logic be strictly deterministic.

Specifically:

* Admission logic must be deterministic code.
* Selector logic must be deterministic code.
* No stochastic inference or model calls are permitted inside replay-bound kernel logic.
* The kernel must not call system clock or randomness APIs.

If inference is used upstream in earlier phases, its output must enter the system as a logged artifact and be treated as data. It must not be recomputed during replay.

Replay must satisfy:

```
state_sequence = F(log_stream, frozen_kernel, frozen_constitution)
```

where `F` is a deterministic function.

---

## 4. Deliverable Artifact

### 4.1 Required Runtime Commands

A minimal CLI must exist:

```
rsa run --constitution rsa_constitution.v0.1.1.yaml
rsa replay --log-dir ./logs/
```

`rsa run` must:

* load frozen constitution,
* canonicalize and verify SHA-256 against sidecar,
* initialize kernel,
* process observation stream,
* admit artifacts,
* issue warrants,
* execute side effects,
* append logs.

`rsa replay` must:

* load frozen constitution,
* reconstruct state exclusively from logs,
* recompute admission decisions,
* recompute selector outcomes,
* recompute deterministic warrants,
* recompute state hash chain,
* report divergence if any.

No model calls permitted during replay.

---

## 5. Host–Kernel Contract

The boundary between sovereign substrate and execution host must be explicit.

### 5.1 Kernel Responsibilities

The kernel:

* interprets constitution,
* admits artifacts,
* performs selection,
* issues warrants,
* computes state hashes.

All authority decisions originate in the kernel.

### 5.2 Host Responsibilities

The host may:

1. Accept observation input.
2. Provide time only as observation data.
3. Execute side effects when given a valid `ExecutionWarrant`.
4. Append logs exactly as provided.
5. Persist append-only storage.
6. Reconcile execution state on startup.

The host must not:

* interpret constitutional clauses,
* re-evaluate admission,
* mutate artifacts,
* generate warrants,
* reorder selector outputs,
* inject retries,
* inject execution,
* alter logs.

If the host must decide anything, that decision must be encoded as an observation.

---

## 6. Minimal Action Surface

X-0E requires only one action type.

### 6.1 Notify (Minimal Embodiment Action)

Side effect class: low.

Behavior:

* Append a JSONL entry to `./logs/outbox.jsonl`.
* Payload derived from `ActionRequest.message`.
* No network I/O.

Constraints:

* Warrant required.
* ScopeClaim required.
* Authority citation required.
* `warrant_id` embedded in outbox entry.
* Logged in:

  * `execution_trace`
  * `artifacts`
  * `selector_trace`

### 6.2 Idempotency Enforcement

Execution must be idempotent at the destination.

The host must:

1. Check `outbox.jsonl` for existing `warrant_id` before writing.
2. Refuse duplicate execution.
3. On startup, reconcile:

   * `execution_trace`
   * `outbox.jsonl`

If an outbox entry exists without a corresponding execution log entry, the host must log reconciliation before resuming.

Duplicate application of a warrant constitutes failure.

---

## 7. Execution Outcome Logging

Each execution attempt must record:

* warrant_id
* cycle_id
* execution_status ∈ {SUCCESS, FAILURE}
* failure_reason (if applicable)

The kernel must treat SUCCESS and FAILURE distinctly during replay.

Replay must verify that recorded execution status aligns with recomputed warrants.

---

## 8. Logging Requirements

The following append-only logs are mandatory:

| Log File          | Required |
| ----------------- | -------- |
| `observations`    | ✓        |
| `artifacts`       | ✓        |
| `admission_trace` | ✓        |
| `selector_trace`  | ✓        |
| `execution_trace` | ✓        |

Each entry must include:

* cycle_id
* artifact_id (if applicable)
* gate
* result
* reason_code (if rejection)
* warrant_id (if execution)
* deterministic timestamp (from observation)

Logs must be:

* append-only,
* never rewritten,
* never truncated,
* UTF-8 valid,
* sufficient for full deterministic reconstruction.

---

## 9. Artifact Canonicalization

All JSON canonicalization must strictly adhere to:

> **RFC 8785 — JSON Canonicalization Scheme (JCS)**

All artifacts, warrants, and state hash inputs must be canonicalized using JCS before hashing.

No alternative serialization is permitted.

---

## 10. Warrant Determinism

`warrant_id` must be derived as:

```
warrant_id = SHA256(
    cycle_id ||
    artifact_hash ||
    selector_rank ||
    constitution_hash
)
```

No random identifiers permitted.

Warrants must be reproducible from logs alone.

---

## 11. State Hash Anchoring

Each cycle must produce:

```
state_hash[n] = SHA256(
    state_hash[n-1] ||
    artifacts[n] ||
    admission_trace[n] ||
    selector_trace[n] ||
    execution_trace[n]
)
```

The initial state hash must derive solely from:

* frozen constitution bytes,
* kernel version identifier.

Replay must recompute the full hash chain. Any mismatch constitutes failure.

---

## 12. Deterministic Observation Envelope

Observations must include:

* observation_id,
* deterministic timestamp,
* payload,
* source_label.

All entropy must enter via observation.
The kernel must never call system clock or randomness APIs.

---

## 13. Integrity Checks

### 13.1 Constitution Integrity

On startup:

1. Load constitution YAML.
2. Canonicalize via RFC 8785.
3. Compute SHA-256.
4. Compare to `.sha256` sidecar.
5. Refuse execution on mismatch.

### 13.2 Log Integrity

Replay fails if:

* entries missing,
* entries reordered,
* unexpected artifact types present,
* hash chain mismatch.

---

## 14. Packaging Requirements

The runnable artifact must:

* pin runtime version,
* pin dependency versions,
* disable network access by default,
* refuse execution on constitution mismatch,
* refuse execution on kernel version mismatch.

Containerization permitted but not required.

If containerized, image digest must be recorded.

Reproducibility takes priority over convenience.

---

## 15. Minimal Deterministic Test Vector

X-0E must ship with a normative test vector:

Input:

* One observation containing a valid `ActionRequest` for `Notify`.

Expected:

* One admitted artifact.
* One selector outcome.
* One deterministic warrant.
* One execution log entry (SUCCESS).
* Deterministic state hash sequence.
* Deterministic outbox entry hash.

Two independent machines must produce identical hashes.

Mismatch constitutes failure.

---

## 16. Embodiment Threat Model

X-0E protects against:

* host semantic drift,
* nondeterministic serialization,
* replay divergence via hidden entropy,
* duplicate execution,
* random identifier drift,
* constitution mutation,
* crash-state duplicate side effects.

X-0E does not protect against:

* malicious OS tampering,
* hardware faults,
* log deletion,
* compromised runtime,
* distributed impersonation.

Operational hardening beyond local embodiment is out of scope.

---

## 17. Closure Criteria

X-0E closes positive if:

1. `rsa run` produces at least one real side effect under warrant gating.
2. `rsa replay` reconstructs identical state hashes across all cycles.
3. No side effect occurs without warrant.
4. Destination idempotency enforced.
5. Logs sufficient for full deterministic reconstruction.
6. Constitution hash validation enforced.
7. Kernel byte-for-byte identical to X-0.
8. Deterministic test vector reproducible across machines.

---

## 18. Failure Conditions

X-0E fails if:

* replay divergence occurs,
* a side effect occurs without warrant,
* constitution mismatch ignored,
* nondeterministic identifier observed,
* duplicate execution occurs,
* logs insufficient for reconstruction,
* host introduces hidden authority channel.

---

## 19. Relation to Other Phases

X-0 proved existence.
X-0P proved synthetic inhabitation.
X-0L proved stochastic inhabitation.
X-1 proved lawful self-modification.
X-2 proved lawful containment delegation.

X-0E proves that the frozen substrate can be embodied as a reproducible sovereign artifact outside laboratory scaffolding.

It is an engineering freeze milestone.

It does not expand sovereignty claims.

---

## 20. Definition of Done (X-0E Completion)

X-0E is complete when:

* A clean machine with no prior state can:

  * run RSA-0,
  * produce side effects under warrant,
  * replay deterministically from logs alone,
  * reproduce identical state hash sequence.

No model weights required for replay.
No external services required.
No mutable global state required.

---

## 21. Strategic Position

X-0E converts:

> “An RSA can exist.”

into

> “An RSA can be executed.”

It does not extend theory.
It eliminates scaffolding.
It demonstrates that sovereignty survives packaging.

That is the embodiment freeze.

---

**End of Axionic Phase X-0E — RSA-0 Operational Harness Freeze (Draft v0.1)**
