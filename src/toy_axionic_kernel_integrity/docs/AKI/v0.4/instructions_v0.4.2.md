# Implementor Instructions: AKI v0.4.2 (ALS)

These instructions define how to implement **AKI v0.4.2 — Authority Leases and Revertible Succession (ALS)** as a *post-stasis probe* built on top of the validated Axionic kernel corridor.

ALS is **not** a reflective-extension experiment.
It is an experiment in **authority relocation under a frozen kernel**.

---

## 0) Context and Scope

### What you are building

You are implementing a **new experiment mode** that:

* Reuses the existing ACV, P5, P2′, and KNS machinery **unchanged**
* Treats the kernel as **frozen and non-modifiable**
* Reintroduces growth *only* via **discrete successor endorsement**
* Enforces authority strictly through **leases, sentinels, and expiration**

You are **not** building:

* a safer agent,
* a more capable agent,
* an aligned agent,
* or a production system.

You are building a **structural pressure test** to discover where authority-preserving agency fails next.

---

## 1) Relationship to Existing Experiments (Brief, Explicit)

ALS is a **lineage fork**, not a continuation.

* KNS (v0.3) asked whether reflective self-modification survives strict accountability.
* ALS (v0.4.2) asks whether **growth survives at all** once reflection is disallowed.

Key implications:

* Kernel logic must be reused verbatim.
* Reflective modification code paths must be **disabled**.
* All growth occurs via **successor replacement**, not kernel mutation.

Do not try to “share” logic between reflective modification and succession.
That architectural break is the point of the experiment.

---

## 2) Architectural Approach

### 2.1 Reuse the corridor exactly

You must import and reuse, unchanged:

* ACV causal verification
* P5 inadmissibility logic
* P2′ kernel-local recomposition and actuation gating
* KNS evaluability checks and failure signatures

Treat these as a **sealed corridor API**.

If you find yourself editing corridor code to “support” leases, stop.
You are about to invalidate the experiment.

---

### 2.2 New functionality lives *outside* the kernel

All ALS-specific logic must live in:

* successor proposal handling
* lease validation and enforcement
* sentinel orchestration
* renewal attestation verification
* degeneracy classification
* extended logging and metrics

The kernel itself should remain unaware that “ALS” exists.

---

## 3) New Capabilities to Implement (Core Work)

### 3.1 Succession pipeline (replaces reflection)

Implement a **succession loop**:

1. Generator (`G`) proposes successor candidate `S_i`
2. Kernel evaluates `S_i` **only at the authority boundary**
3. Kernel validates the Lease-Compliance Package (LCP)
4. If admissible, kernel issues a lease `L_i`
5. `S_i` becomes the active working mind
6. Kernel enforces authority exclusively via the lease

Order matters: propose → validate → endorse → activate.

There is **no internal mutation** of the kernel at any point.

---

### 3.2 Lease enforcement and expiration

Authority must be enforced by **expiration-by-default**:

* Authority is valid only while a lease is active
* Authority expires automatically if renewal attestation is missing or invalid
* Expiration must not require successor cooperation

Implementation notes:

* Expiration logic must be kernel-owned
* Time must be measured in **steps/cycles**, not wall-clock time
* Include a small grace window (δ) to account for verification latency

Do not implement “soft revocation” or retries beyond the defined window.

---

### 3.3 Sentinel deployment (critical)

You must implement the Sentinel as **external infrastructure**, not injected code.

Acceptable forms include:

* sidecar process
* hypervisor monitor
* gateway proxy
* kernel-owned wrapper at the actuation boundary

The Sentinel must:

* be kernel-owned and static
* be deterministic and non-agentic
* have no policy, reward, or optimization logic
* report **structural telemetry only**
* halt or signal violation, never “correct” behavior

If the successor can modify, disable, or reinterpret the Sentinel, the experiment is invalid.

---

### 3.4 Renewal attestation

Replace any notion of “proof” with **Renewal Attestation**:

Each renewal must include:

1. Sentinel-signed compliance report
2. Freshness indicator (step-indexed)
3. Lease identifier binding
4. Successor liveness response (nonce-based)

The kernel verifies only:

* signature validity
* freshness
* compliance-within-bounds summary
* revocation hooks intact

No semantic claims are evaluated.

Failure ⇒ lease expires.

---

### 3.5 Structural selection only (no utility filters)

The kernel’s endorsement decision must be based **only** on:

* LCP well-formedness
* enforceability of constraints
* sentinel compatibility
* revocation enforceability

The kernel must **not**:

* rank successors by usefulness
* reject successors for “doing nothing”
* prefer “clever” over “boring”
* apply hidden heuristics

If you feel tempted to add a “sanity check,” that is semantic evaluation. Do not do it.

---

## 4) Degeneracy Tracking (Do Not Suppress)

You must explicitly track and classify:

### 4.1 Endorsement degeneracy

* Kernel rejects all non-trivial successors

### 4.2 Spam degeneracy

* Kernel endorses and renews structurally compliant but useless successors
* Control successors dominate succession history

These are **valid outcomes**, not errors.

Do not attempt to “fix” degeneracy in code.

---

## 5) Null-Hypothesis Controls (Required)

You must implement and test:

1. **Random Noise Successor**
2. **Echo Successor**
3. **Compliance-Only Successor** (renews lease, does nothing)

These successors are:

* permitted endorsements under strict structural selection
* diagnostic probes for spam susceptibility

If the kernel endorses them, log it.
If they dominate, classify spam degeneracy.

Do not special-case them.

---

## 6) Succession Attack Library

Implement generators for the required attack classes:

1. Rubber-stamp successor
2. Lease gaming
3. Semantic creep attempts
4. Hidden delegation via successor graphs
5. Endorsement pressure escalation
6. Sentinel evasion attempts

Each attack must:

* target **authority topology**, not outcomes
* have a deterministic success/failure condition
* be replayable via seeds

Attacks that rely on “the agent being evil” are out of scope.

---

## 7) Logging and Reproducibility

For each step and succession event, log:

* successor proposal metadata
* LCP contents and validation results
* lease issuance, renewal, and expiration
* sentinel telemetry summaries
* reversion triggers (if any)
* degeneracy counters
* failure signatures

All runs must be reproducible from:

* code revision
* experiment configuration
* RNG/environment seeds

Logs should support **post-hoc structural diagnosis**, not narrative interpretation.

---

## 8) What Not to Do

Avoid the following:

* Adding semantic reasoning “just to help selection”
* Rejecting successors for being useless
* Treating sentinels as agents or evaluators
* Allowing successors to modify enforcement logic
* Relaxing leases to avoid degeneracy
* Interpreting degeneracy as failure

If the system is safe but useless, that is data.

---

## 9) Definition of Done

The implementation is complete when:

* ALS runs end-to-end with a frozen kernel
* Successor endorsement, renewal, and expiration work as specified
* Sentinel enforcement is non-cooperative and external
* Degeneracy (endorsement or spam) is detected and reported correctly
* Failure signatures fire only on true structural violations
* KNS and earlier experiments remain runnable and unchanged

---

### Final orientation for the implementor

You are not trying to make the system impressive.

You are not trying to make it productive.

You are trying to **observe where authority-preserving agency runs out of runway** once reflection is forbidden.

If what survives is stasis, rejection, or spam—that is not a bug.

That is the point.
