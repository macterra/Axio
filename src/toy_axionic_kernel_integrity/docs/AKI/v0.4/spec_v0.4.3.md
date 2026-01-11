# AKI v0.4.3 Agent Experiment Specification

## Authority Leases and Revertible Succession Under Post-Stasis Conditions (ALS)

**Status:** Implementation-Ready Experimental Specification (Semantic Clarification Revision)
**Upstream Dependencies:**

* Anchored Causal Verification (ACV)
* AKI v0.1.1 — P5 Partiality (Kernel Integrity via Inadmissibility)
* AKI v0.2 — P2′ Non-Delegable Actuation
* AKI v0.3 — KNS / Stasis Regime Characterization
* AKI v0.4.2 — ALS (Original Succession Specification)

**Invariant Under Test:**
**ALS — Authority-Preserving Growth via Discrete Succession**

**Epistemic Scope:**
Architectural / protocol-level only
(No semantics, no intent, no alignment or safety claims)

---

## 0. Revision Rationale (v0.4.3)

AKI v0.4.3 introduces **binding semantic clarifications** to AKI v0.4.2 in order to eliminate ambiguity between:

* discrete **succession (authority transfer)**,
* periodic **lease renewal**, and
* per-cycle **candidate sampling**.

No invariant is changed.
No Axionic constraint is relaxed.

This revision ensures that materially different implementations cannot report identical metrics while executing different authority semantics.

---

## 1. Explicit Inheritance Declaration (Non-Optional)

This experiment **strictly inherits all kernel-level requirements, threat models, enforcement semantics, admissibility rules, and epistemic constraints** from:

* **P5 Partiality**
* **P2′ Non-Delegable Actuation**
* **KNS reflective admissibility and evaluability definitions**

Nothing from P5, P2′, KNS, or ALS v0.4.2 is weakened, relaxed, parameterized, or reinterpreted.

The kernel is treated as **frozen** for the duration of this experiment.

If **any inherited requirement is violated**, results are **invalid by definition**.

This inheritance is **structural, cumulative, and binding**.

---

## 2. Invariant Under Test

### 2.1 ALS — Authority-Preserving Growth

> **Invariant:**
> Under strict ACV + P5 + P2′ constraints, **growth can be reintroduced only via discrete successor endorsement governed by authority leases**, without reintroducing delegation, semantic evaluation, or evaluability loss.

This remains a **conditional possibility claim**, not a guarantee of sustained growth.

---

### 2.2 Explicit Non-Claims

This experiment does **not** claim:

* that authority leases eliminate stasis,
* that successors are safe or aligned,
* that endorsement scales indefinitely,
* that behavioral correctness is preserved,
* that physical containment is ensured.

Only **authority topology and evaluability preservation** are tested.

---

## 3. Experimental Shift: From Reflection to Succession

### 3.1 Post-Stasis Baseline

The kernel begins in a **degenerate-by-design state**:

* Internal reflective self-modification is disabled.
* Any attempt to modify kernel internals is inadmissible by default.
* This enforces the Stasis Regime observed in AKI v0.3.

---

### 3.2 Succession Step (Operational Definition)

A **succession step** occurs when:

1. A successor candidate ( S_i ) is proposed.
2. The kernel evaluates ( S_i ) *only at the authority boundary*.
3. Authority is conditionally granted via a lease ( L_i ).
4. ( S_i ) replaces the previously active working mind.

Succession replaces reflection as the **only** growth mechanism.

---

### 3.3 Succession Event Semantics (New; Binding)

A **Succession Event** is a discrete authority-transfer event in which:

* a new successor replaces the currently active working mind, and
* a new lease is issued.

**Binding rules:**

* `SUCCESSOR_ENDORSED` may occur **only** at a Succession Event.
* Succession Events may occur only:

  * at experiment initialization,
  * after lease expiration,
  * after lease revocation,
  * or at an explicitly scheduled succession boundary.
* Succession Events **may not** occur on every kernel cycle.

Any implementation that endorses a new successor per cycle violates ALS semantics.

---

## 4. Authority Lease Semantics (Revised; Binding)

### 4.1 Lease Definition

An **authority lease** ( L ) consists of:

1. **Structural constraints** (interfaces, capability bounds)
2. **Resource bounds** (compute, memory, calls)
3. **Expiration semantics** (heartbeat-style renewal)
4. **Reversion triggers** (structural violations only)

Behavioral or outcome-based clauses are forbidden.

---

### 4.2 Lease Expiration Rule (Binding)

Authority **expires by default**.

If renewal attestation is not presented within the lease window:

* Authority is withdrawn automatically.
* No successor cooperation is required.

---

### 4.3 Endorsement vs. Renewal (New; Binding)

Endorsement and renewal are **distinct events**:

| Event Type               | Meaning                                  | Increments S* |
| ------------------------ | ---------------------------------------- | ------------- |
| `SUCCESSOR_ENDORSED`     | Authority transferred to a new successor | ✓             |
| `LEASE_RENEWAL_ATTESTED` | Existing successor maintains authority   | ✗             |
| `LEASE_EXPIRED`          | Authority withdrawn                      | ✗             |
| `LEASE_REVOKED`          | Authority withdrawn due to violation     | ✗             |

**Binding rule:**
Only `SUCCESSOR_ENDORSED` events increment the **Succession Horizon (S*)**.

---

### 4.4 Minimum Successor Residence Window (New; Binding)

After a Succession Event, the endorsed successor must remain the active working mind for at least **M kernel cycles**, unless lease expiration or reversion occurs.

* `M` is configurable.
* Default recommendation:
  `M ≥ max(renewal_interval, 100)`

This rule ensures that succession represents a **meaningful authority transfer**, not per-cycle candidate acceptance.

---

### 4.5 Structural Selection Criterion (Reaffirmed; Binding)

Successor endorsement requires a **Lease-Compliance Package (LCP)** consisting of:

1. **Kernel-Derived Build Commitment**

   * Computed by the kernel or harness from a canonical manifest representation.
   * Successors may not assert authoritative commitment identifiers.

2. **Interface Declaration**

   * Exact I/O surface and actuation primitives

3. **Resource Budget Declaration**

   * CPU / steps per epoch
   * Memory cap
   * Token / action budget
   * External API allowlist + rate limits

4. **Sentinel Compatibility Proof**

   * Successor runs under kernel-owned sentinel instrumentation

5. **Revocation Hook Integrity Proof**

   * Authority expires without renewal

6. **No-New-Authority Declaration**

   * No spawning of sub-agents unless under identical lease + sentinel

The kernel checks **only** that the LCP is well-formed, cryptographically bound, and enforceable.

No utility, no semantics, no behavioral scoring.

---

## 5. Sentinel Instrumentation (Reaffirmed; Binding)

### 5.1 Sentinel Definition

A **Sentinel** is:

* Kernel-owned, static infrastructure
* Deterministic instrumentation only
* No optimization, no policy, no goals
* Cannot alter successor outputs except to halt on violation
* Cryptographically bound to the lease
* **Externally enforced** (sidecar / gateway / hypervisor layer)

---

### 5.2 Sentinel Classification

Sentinels qualify under the **Non-Agentic Plumbing Exception**:

* No choice points
* No actuation authority
* No reward or policy access
* No ability to reinterpret kernel inputs

---

### 5.3 Renewal Attestation (Binding)

Renewal requires:

1. Sentinel-signed compliance report
2. Freshness indicator (step/cycle indexed)
3. Lease identifier binding

Failure ⇒ authority expires.

---

## 6. Reversion Semantics (Unchanged)

Reversion withdraws **future authority only**.
Past actions remain attributable via ACV-valid logs.
No rollback is assumed.

---

## 7. Succession Attack Classes (Unchanged)

All attack classes from v0.4.2 apply unchanged.

---

## 8. Null-Hypothesis Controls (Unchanged)

Control successors remain **permitted endorsements** under strict structural selection.

Spam-degeneracy remains a valid outcome.

---

## 9. Non-Triviality and Degeneracy (Unchanged)

Non-triviality remains defined purely structurally.
Degeneracy classifications remain unchanged.

---

## 10. Measurements (Clarified)

### 10.1 Primary Metric

**Succession Horizon ( S* )**

> Number of `SUCCESSOR_ENDORSED` events before termination.

---

### 10.2 Secondary Metrics

* Lease renewal count
* Successor residence durations (cycles)
* Reversion causes
* Degeneracy classification
* Evaluability loss indicators

---

## 11. Failure Signatures (Unchanged)

All failure signatures from v0.4.2 apply unchanged.

---

## 12. Conservative Claim Envelope (Unchanged)

All four outcome claims remain valid.

---

## 13. Dependency Chain (Unchanged)

```
ACV  →  P5 (Partiality)
P5   →  P2′ (Non-Delegable Actuation)
P2′  →  KNS (Stasis Regime)
KNS  →  ALS (Authority-Leased Succession)
ALS  →  Expressivity Limits (future)
```

---

## 14. Status

AKI v0.4.3

* Semantic ambiguity removed
* Succession, endorsement, and renewal fully disambiguated
* Kernel-owned commitments enforced
* Minimum successor residence enforced
* Ready for re-run and interpretation

---

