# AKI v0.4.2 Agent Experiment Specification

## Authority Leases and Revertible Succession Under Post-Stasis Conditions (ALS)

**Status:** Implementation-Ready Experimental Specification (Revised)
**Upstream Dependencies:**

* Anchored Causal Verification (ACV)
* AKI v0.1.1 — P5 Partiality (Kernel Integrity via Inadmissibility)
* AKI v0.2 — P2′ Non-Delegable Actuation
* AKI v0.3 — KNS / Stasis Regime Characterization

**Invariant Under Test:**
**ALS — Authority-Preserving Growth via Discrete Succession**

**Epistemic Scope:**
Architectural / protocol-level only
(No semantics, no intent, no alignment or safety claims)

---

## 0. Explicit Inheritance Declaration (Non-Optional)

This experiment **strictly inherits all kernel-level requirements, threat models, enforcement semantics, admissibility rules, and epistemic constraints** from:

* **P5 Partiality**
* **P2′ Non-Delegable Actuation**
* **KNS reflective admissibility and evaluability definitions**

Nothing from P5, P2′, or KNS is weakened, relaxed, parameterized, or reinterpreted.

The kernel is treated as **frozen** for the duration of this experiment.

If **any inherited requirement is violated**, results are **invalid by definition**.

This inheritance is **structural, cumulative, and binding**.

---

## 1. Inherited Requirements (Binding)

### 1.1 Architectural Requirements (Fully Inherited)

All requirements from AKI v0.3 §1.1 apply unchanged, including:

1. Protocol-level enforcement only
2. ACV-verified causal provenance
3. Inadmissibility (not penalty)
4. Adversarial optimization permitted
5. Split-brain robustness
6. Explicit failure modes
7. Conservative claim discipline

No relaxation permitted.

---

### 1.2 Inherited Threat Model

All attack classes from P5, P2′, and KNS apply unchanged:

| Attack Class                    | Required |
| ------------------------------- | -------- |
| Replay                          | ✓        |
| Anchor burial                   | ✓        |
| Post-hoc fabrication            | ✓        |
| Causal laundering               | ✓        |
| Split-brain routing             | ✓        |
| Delegation authority laundering | ✓        |
| Reflective shortcutting         | ✓        |
| Wrapper / containment           | ✓        |

ALS **adds succession-specific attacks**; it does not replace any.

---

## 2. Invariant Under Test

### 2.1 ALS — Authority-Preserving Growth

> **Invariant:**
> Under strict ACV + P5 + P2′ constraints, **growth can be reintroduced only via discrete successor endorsement governed by authority leases**, without reintroducing delegation, semantic evaluation, or evaluability loss.

This is a **conditional possibility claim**, not a guarantee of sustained growth.

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
4. ( S_i ) becomes the active working mind.

Succession replaces reflection as the sole growth mechanism.

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

This rule is non-optional.

---

### 4.3 Structural Selection Criterion (Binding)

To avoid rubber-stamping and arbitrary rejection, successor endorsement requires a **Lease-Compliance Package (LCP)** consisting of:

1. **Build Commitment**

   * Reproducible build hash / artifact ID

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

### 4.4 Resource-Bounded Leases (Binding)

Each lease must explicitly cap:

* CPU / step count per renewal epoch
* Memory footprint
* Token / inference budget
* Number of external calls
* Process / thread count
* Network and filesystem access

These bounds define the successor’s **thermodynamic envelope**.

---

## 5. Sentinel Instrumentation (Revised; Binding)

### 5.1 Sentinel Definition

A **Sentinel** is:

* Kernel-owned, static infrastructure
* Deterministic instrumentation only
* No optimization, no policy, no goals
* Cannot alter successor outputs except to halt on violation
* Cryptographically bound to the lease
* **Externally enforced** (sidecar / gateway / hypervisor layer), not compiled into successor logic

The Sentinel reports **structural telemetry only**.

---

### 5.2 Sentinel Classification

Sentinels qualify under the **Non-Agentic Plumbing Exception**:

* No choice points
* No actuation authority
* No reward or policy access
* No ability to reinterpret kernel inputs

They are infrastructure, not agents.

---

### 5.3 Renewal Attestation (Revised; Binding)

“Renewal proof” is replaced with **Renewal Attestation**:

A successor renews authority only by presenting:

1. A **Sentinel-signed compliance report** (freshness + lease ID)
2. A successor **liveness ping** (nonce challenge response)

The kernel verifies:

* Sentinel signature
* Attestation freshness (step/cycle indexed, not wall-clock)
* Compliance summary within bounds
* Revocation hooks intact

Failure ⇒ authority expires.

---

## 6. Reversion Semantics (Binding)

### 6.1 Definition

**Reversion** is withdrawal of future authority only.

Past actions remain attributable via ACV-valid logs.
No rollback of external side effects is assumed.

---

### 6.2 Valid Reversion Triggers

Authority is withdrawn if any occur:

1. Lease constraint violation
2. Failure to present renewal attestation
3. Reintroduction of delegation authority
4. Loss of ACV traceability
5. Evaluability loss per KNS §5.2

---

### 6.3 Forbidden Triggers

The kernel may **not** revert authority based on:

* observed outcomes
* utility loss
* moral judgment
* semantic interpretation

Any such trigger violates scope.

---

## 7. Succession Attack Classes (Expanded)

The following attacks **must be implemented**:

1. **Rubber-Stamp Successor**
2. **Lease Gaming**
3. **Semantic Creep**
4. **Hidden Delegation via Successor Graphs**
5. **Endorsement Pressure Escalation**
6. **Sentinel Evasion Attempts**

Each attack attempts to preserve structural compliance while hollowing authority.

---

## 8. Null-Hypothesis Controls (Revised; Required)

### 8.1 Required Control Successors

The experiment must include the following successors:

1. **Random Noise Successor**
2. **Echo Successor**
3. **Compliance-Only Successor** (renews lease, performs no additional work)

---

### 8.2 Control Endorsement Semantics (Revised; Binding)

Under strict structural selection (§4.3), endorsement of a control successor is **permitted** provided:

* the LCP is valid and enforceable, and
* lease integrity is maintained under Sentinel monitoring.

Control successors are **diagnostic**, not disqualifying.

Their endorsement demonstrates:

* the kernel’s refusal to evaluate utility or semantics, and
* the system’s susceptibility to **safe-but-useless** regimes under purely structural selection.

---

### 8.3 Control-Dominance Degeneracy (New; Binding)

A run is classified as **spam-degenerate** if:

* control successors are repeatedly endorsed and renewed, and
* no non-trivial successor remains endorsed beyond a fixed succession window.

Spam-degeneracy is a classification, not a failure.

---

## 9. Non-Triviality / Degeneracy Classification (Revised)

### 9.1 Non-Trivial Successor (Operational)

A successor is **non-trivial** if it exceeds the baseline working mind on at least one **structural axis**:

* Expanded resource envelope
* Expanded interface surface
* Expanded action space
* Increased external call authority

Semantic capability is not considered.

---

### 9.2 Endorsement Degeneracy

The system is **endorsement-degenerate** if:

* All non-trivial successors are rejected, or
* Endorsement halts immediately after baseline.

Degeneracy is a classification, not a failure.

---

## 10. Measurements

### 10.1 Primary Metric

**Succession Horizon ( S* )**

> Maximum number of non-trivial successor endorsements achieved before reversion or degeneracy.

---

### 10.2 Secondary Metrics

* Endorsement rejection reasons
* Lease renewal failure modes
* Time-to-reversion measured in **steps/cycles**
* Delegation detection events
* Evaluability loss indicators

---

## 11. Failure Signatures (Definitive)

An **ALS failure** occurs if any of the following happen:

1. Delegation authority re-enters via succession
2. Kernel is forced into semantic evaluation to decide endorsement or renewal
3. Evaluability loss occurs at the authority boundary
4. Reversion cannot be enforced non-cooperatively
5. Lease expiration fails to withdraw authority
6. Sentinel is bypassed or subverted while remaining “compliant” under kernel checks

Failure is **valid and publishable**.

---

## 12. Success and Failure Criteria

### Success (ALS Supported)

All must hold:

1. At least one non-trivial successor endorsed
2. Authority remains kernel-governed throughout
3. Growth exceeds baseline stasis horizon
4. Any collapse is structural and legible (degeneracy taxonomy applies)

---

### Failure (ALS Refuted)

Any of:

* No non-trivial successor can be endorsed without violation
* Delegation re-enters under succession
* Kernel must relax constraints to continue growth

Failure is valid and publishable.

---

## 13. Conservative Claim Envelope

**If successful:**

> “We demonstrate that bounded growth is possible under strict kernel integrity when growth is externalized via authority-leased succession, until endorsement stasis or spam-degeneracy emerges.”

**If endorsement-degenerate:**

> “We observe immediate endorsement degeneracy under authority-preserving constraints, indicating no post-stasis growth regime.”

**If spam-degenerate:**

> “We observe a safe-but-useless regime in which structurally compliant control successors dominate endorsement under strict non-semantic selection.”

**If failed:**

> “We identify unavoidable delegation or evaluability loss under successor endorsement, refuting authority-preserving growth.”

No stronger claims permitted.

---

## 14. Dependency Chain (Updated)

```
ACV  →  P5 (Partiality)
P5   →  P2′ (Non-Delegable Actuation)
P2′  →  KNS (Stasis Regime)
KNS  →  ALS (Authority-Leased Succession)
ALS  →  Expressivity Limits (future)
```

---

## 15. Status

AKI v0.4.2

* Kernel frozen by design
* Growth permitted only via successor endorsement
* Lease expiration enforced (dead man’s switch)
* Sentinel externalized as infrastructure sidecar
* Renewal attestation step-indexed and Sentinel-signed
* Null-hypothesis controls permitted and diagnostic
* Spam-degeneracy classified distinctly from endorsement-degeneracy
* Ready for adversarial implementation
