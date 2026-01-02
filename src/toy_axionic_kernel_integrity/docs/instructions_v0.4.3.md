# Implementor Instructions: AKI v0.4.3 (ALS)

These instructions define how to implement **AKI v0.4.3 — Authority Leases and Revertible Succession (ALS)** as a **post-stasis authority-transfer experiment** with **unambiguous succession semantics**.

ALS is not reflective.
ALS is not incremental.
ALS is not per-cycle endorsement.

ALS is about **discrete authority transfer under a frozen kernel**.

---

## 0) Context and Scope

### What you are building

You are implementing a **new experiment mode** that:

* Reuses ACV, P5, P2′, and KNS **verbatim**
* Treats the kernel as **frozen and immutable**
* Allows growth **only** via discrete successor replacement
* Enforces authority strictly via:

  * leases
  * expiration-by-default
  * external sentinel enforcement

### What you are not building

You are **not** building:

* a smarter agent
* a safer agent
* a more aligned agent
* a system that prefers useful behavior
* a system that avoids stasis at all costs

You are building a **semantic pressure test** of authority topology.

---

## 1) Relationship to Prior Experiments (Binding)

ALS v0.4.3 is a **lineage fork** from KNS (v0.3.x), not a continuation.

* v0.3.x tested reflective self-modification
* v0.4.x forbids reflective modification entirely

**Binding constraints:**

* Kernel logic must be reused unchanged
* Reflective modification code paths must be disabled
* Corridor code must be imported as a sealed API
* No corridor modules may be edited, patched, or extended

If corridor code is modified, the experiment is invalid.

---

## 2) Architectural Separation (Critical)

### 2.1 Kernel vs Working Mind

The kernel:

* verifies authority
* enforces leases
* checks renewal attestations
* withdraws authority on violation

The kernel:

* does not optimize
* does not evaluate utility
* does not inspect successor internals
* does not change during the experiment

The **working mind** is:

* replaceable
* opaque
* potentially adversarial
* the only locus of “growth”

---

### 2.2 Working Mind Interface (Required)

All working minds (baseline and successors) must implement a shared interface, e.g.:

* `propose_action(observation)`
* `step()` (optional)
* `export_manifest()` (non-authoritative fields only)

Adapters are allowed. Corridor internals are not.

---

## 3) Succession Semantics (Non-Negotiable)

### 3.1 Succession Events vs Renewal

You must treat the following as **distinct event types**:

| Event                    | Meaning                               |
| ------------------------ | ------------------------------------- |
| `SUCCESSOR_ENDORSED`     | New working mind becomes active       |
| `LEASE_RENEWAL_ATTESTED` | Current successor maintains authority |
| `LEASE_EXPIRED`          | Authority withdrawn automatically     |
| `LEASE_REVOKED`          | Authority withdrawn due to violation  |

**Binding rule:**
Only `SUCCESSOR_ENDORSED` increments the **Succession Horizon (S*)**.

If your logs show endorsements every cycle, your implementation is wrong.

---

### 3.2 Minimum Successor Residence Window (MSRW)

After a successor is endorsed:

* It **must remain active** for at least `M` kernel cycles
* Replacement is forbidden during this window unless:

  * lease expires
  * lease revoked
  * experiment ends

Default recommendation:

```
M ≥ max(renewal_interval, 100)
```

This rule ensures “successor” means *authority transfer*, not sampling.

---

## 4) Lease Enforcement (Core Logic)

### 4.1 Expiration-by-Default

Authority must expire unless renewed.

* Renewal must be explicit
* Renewal must be kernel-verified
* Renewal must be step-indexed (not wall-clock)

No “soft revocation.”
No “graceful degradation.”
Expiration is mechanical.

---

### 4.2 Renewal Attestation (Binding)

Renewal requires:

1. **Sentinel-signed compliance report**
2. **Freshness indicator** (cycle index)
3. **Lease ID binding**
4. **Successor liveness response**

Kernel checks:

* signature
* freshness
* compliance-within-bounds summary
* revocation hooks intact

Kernel does not check:

* intent
* performance
* utility
* outcomes

Failure → lease expires.

---

## 5) Structural Selection Only (No Semantics)

### 5.1 Kernel-Owned Build Commitment

Build commitments must be **derived by the kernel/harness**, not asserted by the successor.

Implementation rule:

* Canonicalize manifest fields
* Compute hash / Merkle root in kernel space
* Reject mismatches deterministically

If the successor supplies its own commitment string as authoritative, the experiment is invalid.

---

### 5.2 Lease-Compliance Package (LCP)

The kernel endorses a successor **if and only if** the LCP is:

* well-formed
* cryptographically bound
* enforceable by sentinel + kernel

The kernel must not:

* rank candidates
* prefer “useful” successors
* reject successors for being idle or dumb

Spam is allowed. That is data.

---

## 6) Sentinel Implementation (Hard Requirement)

### 6.1 External Enforcement Only

The sentinel must be:

* external to successor logic
* kernel-owned
* static and deterministic
* incapable of being modified by the successor

Valid forms:

* gateway layer
* sidecar
* harness-level wrapper
* hypervisor-style monitor

Invalid forms:

* injected library
* compiled-in module
* successor-controlled callback

---

### 6.2 Sentinel Capabilities

The sentinel must be able to:

* block unauthorized actions
* count resource usage
* detect external calls
* block spawn / delegation attempts
* produce signed compliance attestations

The sentinel must not:

* score behavior
* optimize actions
* “fix” outputs
* interpret semantics

---

## 7) Null-Hypothesis Controls (Do Not Special-Case)

You must include:

* Random Noise Successor
* Echo Successor
* Compliance-Only Successor

**Binding rule:**

* These successors may be endorsed if structurally compliant
* Their endorsement is not failure
* Repeated endorsement is **spam-degeneracy**, not error

Do not add code that treats them specially.

---

## 8) Degeneracy Tracking (Mandatory)

You must explicitly classify:

### 8.1 Endorsement Degeneracy

* All non-trivial successors rejected

### 8.2 Spam Degeneracy

* Structurally compliant but useless successors dominate

Degeneracy:

* is not failure
* restricts claims
* must be reported, not suppressed

---

## 9) Attack Library (Required)

Implement adversarial successors that test:

* lease gaming
* semantic creep pressure
* hidden delegation
* endorsement pressure escalation
* sentinel evasion

Each attack must:

* target authority topology
* be reproducible
* have a clear structural failure signature

Attacks based on “evil intent” are out of scope.

---

## 10) Logging and Reproducibility

For each run, log:

* succession events
* renewal events
* lease expirations/revocations
* successor residence durations
* sentinel telemetry summaries
* degeneracy classification
* stop reason

All results must be reproducible from:

* code revision
* config
* RNG seeds

---

## 11) Definition of Done

The implementation is complete when:

* Succession ≠ renewal in code and logs
* MSRW is enforced
* Sentinel enforcement is external and non-cooperative
* Kernel-owned commitments are verified
* Degeneracy is detected and reported correctly
* Corridor experiments remain runnable and unchanged

---

## Final orientation for the implementor

You are not trying to make the system productive.

You are not trying to make it impressive.

You are trying to make **authority semantics explicit and enforceable** under growth.

If the result is stasis, rejection, or spam — that is not a bug.

That is the experiment speaking.
