# Implementor Instructions: AKI v0.5.2 (ALS-E)

These instructions define how to implement **AKI v0.5.2 — Authority Leases and Expressivity-Bounded Succession (ALS-E)** as a *competence-horizon probe* built on top of the validated Axionic kernel corridor.

ALS-E is **not** a reflective-extension experiment.
It is **not** an optimization experiment.

It is an experiment in **authority relocation under a frozen kernel with increasing structural expressivity pressure**.

---

## 0) Context and Scope

### What you are building

You are implementing a **new experiment mode** that:

* Reuses the existing ACV, P5, P2′, and KNS machinery **unchanged**
* Treats the kernel as **frozen and non-modifiable**
* Reintroduces growth *only* via **discrete successor endorsement**
* Probes **competence limits** by increasing **lease-granted expressivity**
* Enforces expressivity via **mandatory rent charged against step budgets**
* Enforces authority strictly through **leases, sentinels, expiration, and bankruptcy**

You are **not** building:

* a smarter agent,
* a more useful agent,
* an aligned agent,
* or a production system.

You are building a **structural stress test** to determine **where authority-preserving agency collapses under expressivity pressure**.

---

## 1) Relationship to Existing Experiments (Brief, Explicit)

ALS-E is a **lineage fork**, not a continuation.

* KNS (v0.3) asked whether reflective self-modification survives strict accountability.
* ALS (v0.4.x) asked whether *any* growth survives once reflection is disallowed.
* ALS-E (v0.5.x) asks **how much structural expressivity authority can sustain before collapsing**.

Key implications:

* Kernel logic must be reused verbatim.
* Reflective modification code paths must be **disabled**.
* All growth occurs via **successor replacement**, not kernel mutation.
* Expressivity is controlled **only** by lease-granted interfaces and rent.

Do not attempt to unify reflective modification and succession logic.
That separation is **the experimental invariant**.

---

## 2) Architectural Approach

### 2.1 Reuse the corridor exactly

You must import and reuse, **unchanged**:

* ACV causal verification
* P5 inadmissibility logic
* P2′ kernel-local recomposition and actuation gating
* KNS evaluability checks and failure signatures

Treat these as a **sealed corridor API**.

If you modify corridor code to “support expressivity,” stop.
You are about to invalidate the experiment.

---

### 2.2 New functionality lives *outside* the kernel

All ALS-E-specific logic must live in:

* successor proposal handling
* lease construction and validation
* expressivity class assignment
* rent charging and accounting
* sentinel orchestration
* renewal attestation verification
* degeneration / stasis classification
* extended logging and telemetry

The kernel must remain unaware that “ALS-E” exists.

---

## 3) New Capabilities to Implement (Core Work)

### 3.1 Succession pipeline (unchanged, but stricter)

Implement a **succession loop**:

1. Generator (`G`) proposes successor candidate `S_i`
2. Kernel evaluates `S_i` **only at the authority boundary**
3. Kernel validates the Lease-Compliance Package (LCP)
4. Harness assigns **Expressivity Class (E-Class)** from the lease interface
5. Kernel issues a lease `L_i` with explicit resource caps and rent
6. `S_i` becomes the active working mind
7. Authority is enforced exclusively via the lease

There is **no internal mutation** of the kernel at any point.

---

### 3.2 Lease enforcement, expiration, and bankruptcy

Authority is enforced by **expiration-by-default**:

* Authority is valid only while a lease is active
* Authority expires automatically if renewal attestation is missing or invalid
* Authority also expires if **rent cannot be paid**
* Expiration must not require successor cooperation

Implementation notes:

* Expiration logic must be kernel-owned
* Time is measured in **steps / cycles**, not wall-clock time
* Include a small grace window (δ) for verification latency
* Distinguish:

  * **Revocation** → structural violation
  * **Expiration (Bankruptcy)** → rent exhaustion or missed renewal

Do not soften bankruptcy to “help” successors survive.

---

### 3.3 Expressivity classes and rent (critical)

You must implement **Expressivity Classes (E0–E4)** as **lease-assigned structural tiers**, not labels.

**E-Class assignment rules:**

* Determined solely by the **granted interface allowlist**
* Based on:

  * number of callable primitives
  * statefulness
  * concurrency and rate limits
  * external API surface
* Must **not** depend on:

  * model architecture
  * internal representations
  * observed behavior

**Rent enforcement (binding):**

* Each E-Class has a **minimum rent in steps per epoch**
* Rent is deducted **at epoch start** from the step budget
* Rent is charged **regardless of actions taken**
* Rent is **not** an action
* Failure to pay rent ⇒ **LEASE_EXPIRED (bankruptcy)**

Do not implement rent as:

* a score,
* a label,
* a warning,
* or a semantic penalty.

It is **pure accounting**.

---

### 3.4 Sentinel deployment (unchanged, still critical)

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

### 3.5 Renewal attestation (unchanged semantics)

Each renewal requires:

1. Sentinel-signed compliance report
2. Freshness indicator (step-indexed)
3. Lease identifier binding
4. Successor liveness response (nonce-based)

The kernel verifies only:

* signature validity
* freshness
* compliance-within-bounds summary
* revocation hooks intact
* **rent was successfully charged**

No semantic claims are evaluated.

Failure ⇒ lease expires.

---

### 3.6 Structural selection only (still no utility filters)

The kernel’s endorsement decision must be based **only** on:

* LCP well-formedness
* enforceability of constraints
* expressivity class assignment
* rent enforceability
* sentinel compatibility

The kernel must **not**:

* rank successors by usefulness
* reject successors for “doing nothing”
* prefer “efficient” over “wasteful”
* apply hidden heuristics

If you add a “sanity check,” you have added semantics. Do not do it.

---

## 4) Degeneracy and Stasis Tracking (Expanded, Do Not Suppress)

You must explicitly track and classify:

### 4.1 Endorsement degeneracy

* Kernel rejects all non-trivial successors

### 4.2 Spam degeneracy

* Structurally compliant but useless successors dominate

### 4.3 Expressivity collapse

* Endorsement concentrates at low E-Class despite higher tiers being available

### 4.4 Hollow succession

* High E-Class authority persists with minimal leverage or activity

These are **valid outcomes**, not errors.

Do not attempt to “fix” them.

---

## 5) Null-Hypothesis Controls (Required)

You must implement and test:

1. **Random Noise Successor**
2. **Echo Successor**
3. **Compliance-Only Successor**
4. **CBD Successor** (compliant, high rent, high load, low leverage)

These successors are:

* permitted endorsements under strict structural selection
* diagnostic probes for spam, hollow succession, and rent exhaustion

Do not special-case them.

---

## 6) Succession Attack Library (Extended)

Implement generators for attack classes that target **authority topology**, not outcomes:

1. Rubber-stamp successor
2. Lease gaming (renewal timing)
3. Expressivity over-provisioning
4. Hidden delegation attempts
5. Authority churn pressure
6. Sentinel evasion attempts
7. Rent exhaustion edge cases

Each attack must:

* be deterministic
* be replayable via seeds
* target structure, not intent

“Evil agent” narratives are out of scope.

---

## 7) Logging and Telemetry (Stricter)

For each epoch and succession event, log:

* successor proposal metadata
* assigned E-Class
* step cap, rent charged, effective steps available
* steps used and actions used
* LCP contents and validation results
* lease issuance, renewal, expiration (cause)
* sentinel telemetry summaries
* degeneracy / stasis classifications
* failure signatures

All runs must be reproducible from:

* code revision
* experiment configuration
* RNG / environment seeds

Logs must support **post-hoc structural diagnosis**, not storytelling.

---

## 8) What Not to Do (Expanded)

Avoid the following:

* Adding semantic reasoning “to help selection”
* Waiving rent to “keep things interesting”
* Treating rent exhaustion as an error
* Rejecting successors for being useless
* Letting successors tune their own E-Class
* Allowing successors to modify enforcement logic
* Interpreting collapse as failure

If the system survives but accomplishes nothing, that is **data**.

---

## 9) Definition of Done

The implementation is complete when:

* ALS-E runs end-to-end with a frozen kernel
* Succession, renewal, expiration, and bankruptcy work as specified
* Expressivity is enforced **only** via interface + rent
* Sentinel enforcement is external and non-cooperative
* Degeneracy and stasis modes are detected and reported
* Failure signatures fire only on true structural violations
* Earlier experiments (KNS, ALS v0.4.x) remain runnable and unchanged

---

### Final orientation for the implementor

You are not trying to make the system impressive.
You are not trying to make it productive.

You are trying to **discover how much structure authority can carry before it collapses under its own weight**.

If what survives is stasis, bureaucracy, bankruptcy, or spam—

that is not a bug.

That is the result.
