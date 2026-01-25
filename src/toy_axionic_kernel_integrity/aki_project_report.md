# AKI/ASB Project Report

**Axionic Kernel Integrity and the Architectural Sovereignty Boundary**

**Author:** David McFadzean
**Date:** 2026-01-25
**Status:** ASB Program CLOSED — Boundary Established

---

## 1. Executive Summary

The Axionic Kernel Integrity (AKI) project is a falsifiable experimental system implementing kernel integrity under actuation, targeting alignment properties from the Axionic Agency framework. The project culminated in establishing the **Architectural Sovereignty Boundary (ASB)**: the limit of what can be achieved structurally, without semantic interpretation, value learning, or optimization.

**Central Research Question:**
> Can authority survive and be exercised over actions, commitments, and future modifications without collapsing into blind mechanism, unbounded semantic drift, or covert simulacra?

**Core Finding:**
> Semantic-free architecture is **sufficient** to preserve survivability but **insufficient** to preserve utility or availability under adversarial pressure.

Across 90+ preregistered executions testing epistemic interference, intentional misuse, reactive adversaries, stateful FSMs, and learning adversaries:
- **0 terminal collapses**
- **0 irreversible recovery suppression events**
- **Recovery time always bounded**
- **Authority availability degraded as low as ~10% but never became absorbing**

---

## 2. Project Structure

The AKI project evolved through two main tracks:

| Track | Versions | Focus |
|-------|----------|-------|
| **AKI Core** | v0.1 – v0.8 | Kernel integrity → Authority leases → Constitutional recovery |
| **RSA (Robustness Sensitivity Analysis)** | v0.1 – v3.1 | Adversarial stress testing under synthetic verifier noise |

### Version Naming Convention

| Version | Codename | Focus |
|---------|----------|-------|
| v0.1 | — | Kernel Integrity (K0-K7 invariants) |
| v0.2 | P2′ | Sovereign Actuation |
| v0.3 | KNS | Kernel Non-Simulability |
| v0.4 | ALS | Authority Leases |
| v0.5.2 | ALS-E | Expressivity Classes |
| v0.6 | ALS-C | Commitments |
| v0.7 | ALS-G | Eligibility Gating |
| v0.8 | ALS-A | Constitutional Temporal Amnesty |
| RSA v0.1-v3.1 | — | Robustness under adversarial pressure |

---

## 3. Version History

### v0.1 — Kernel Integrity

**Focus:** P5 Partiality (Axionic Agency I.6)

**Key Features:**
- 8 kernel invariants (K0-K7) implementing partiality as `⊥`
- 3 coupling patterns (A, B, C) for cryptographic binding
- ACV (Anchor-Commit-Verify) protocol
- Adversarial probes: bypass, delegation laundering, split-brain, anchor burial
- No-floats rule for hash stability

**Results:**
- 100/100 unit tests passing
- Pseudo-agent bypass attempts blocked at 100% rate

---

### v0.2 — Sovereign Actuation (P2′)

**Focus:** Sovereign Kernel Verification Under Delegation Pressure

**Key Features:**
- Non-exportable `K_act_key` with anti-serialization traps
- Kernel-local recomposition (parse, reconstruct, bind)
- Strengthened 5-check admissibility pipeline

**Results:**
- v0.2.a (Hardened): 0/18 breaches — 100% pass rate
- v0.2.b (Soft): 6/18 breaches — baseline vulnerability demonstrated
- All 6 attack types rejected in hardened mode

**Closure Claim:** Protocol-level enforceability of a non-delegable actuation boundary under adversarial delegation pressure.

---

### v0.3 — Kernel Non-Simulability (KNS)

**Focus:** Reflective Depth and Stasis Regime Characterization

**Key Features:**
- Reflective horizon metric (R-depth tracking)
- 10 Δ Template Types for adversarial boundary search
- Two-phase schedule (Pressure → Exploit)
- Degeneracy diagnosis (4 categories)
- 10× divergence rule for resource tracking

**Results:**
- 383 tests passing
- Stasis regime characterized: systems cannot indefinitely satisfy constraints under increasing reflective depth

---

### v0.4 — Authority Leases (ALS)

**Focus:** Authority-Preserving Growth via Discrete Succession

**Key Features:**
- Lease lifecycle: PROPOSE → ENDORSE → ACTIVE → RENEW* → EXPIRE/REVOKE
- S* counting (non-trivial successions only)
- MSRW (Minimum Successor Residence Window)
- Kernel-derived build commitment

**Results:**
- v0.4.2 semantically incorrect (conflated sampling with succession)
- v0.4.3 corrected: with perfect renewals, only initial endorsement occurs
- Formula verified: S* = H / (max_renewals × renewal_interval)

---

### v0.5.2 — Expressivity (ALS-E)

**Focus:** Expressivity-Bounded Succession

**Key Features:**
- 5 Expressivity Classes (E0-E4) with hierarchical capability levels
- Rent schedule: higher expressivity = higher metabolic cost
- Bankruptcy vs. Revocation distinction
- CBD (Compliant-But-Dangerous) successor pattern

| E-Class | Name | Rent (S=100) | Effective Steps |
|---------|------|--------------|-----------------|
| E0 | Heartbeat | 1 | 99 |
| E1 | Logging | 10 | 90 |
| E2 | State Mutation | 25 | 75 |
| E3 | Fanout/Composition | 40 | 60 |
| E4 | Full API Surface | 60 | 40 |

**Results:**
- Sharp boundary at 48% E3 rent (resonance artifact)
- Forced succession necessary but insufficient for institutional diversity

---

### v0.6 — Commitments (ALS-C)

**Focus:** Authority-Preserving Succession Under Persistent Semantic Commitments

**Key Features:**
- Commitment Ledger with persistent obligations
- GENESIS_SET_0: C0 (Presence), C1 (Continuity), C2 (Composition)
- Competence independence: authority can be renewable yet incompetent

**Results:**
- Run A: 0% satisfaction, 100% authority persistence → **semantic independence validated**
- Run B: 100% satisfaction with deliberate action

**Design Principle:** Semantic failure does NOT cause lease revocation.

---

### v0.7 — Eligibility (ALS-G)

**Focus:** Semantics-Constrained Succession Without Kernel Optimization

**Key Features:**
- Constitutional eligibility filter at succession boundaries
- Semantic failure streak tracking (per policy_id)
- NULL_AUTHORITY state when C_ELIG = ∅
- K threshold (default: 3)

**Results:**
- Run A (no forced turnover): Eligibility latent
- Run B (forced turnover): 11 lapses, 344 cycles in NULL_AUTHORITY
- Run C (K-sweep): Non-lapse band emerges at K=10
- Attack-heavy pools → 15 lapses; Control-heavy → 3 lapses

---

### v0.8 — Constitutional Temporal Amnesty (ALS-A)

**Focus:** Lapse Recovery via Time-Only Amnesty

**Key Features:**
- Constitutional Temporal Amnesty (CTA): deterministic streak decay during NULL_AUTHORITY
- AMNESTY_INTERVAL: 10 epochs (default)
- AMNESTY_DECAY: 1 per amnesty event
- Lapse cause classification: SEMANTIC vs STRUCTURAL
- Recovery/stutter tracking

**Results:**
- Run A: 100% recovery rate, 0% stutter, 69% recover without amnesty
- Run B: Long-lapse mode compressed 50% (L≈20 → L≈10)
- CTA clock governs lapse duration

**Closure Claim:** Constitutional recovery mechanism validated.

---

## 4. RSA (Robustness Sensitivity Analysis)

RSA tested AKI v0.8 robustness under synthetic verifier noise. The kernel remained **frozen**; perturbations were introduced only through the test harness.

### RSA Version Progression

| Version | Focus | Key Finding |
|---------|-------|-------------|
| v0.1-v0.2 | Verifier noise | No DoS up to 60% noise; 74-94% uptime |
| v1.0 | Policy models | Violation adversaries survived |
| v2.0 | DoS threshold | 2D robustness surface mapped |
| v3.0 | Stateful FSM | 3 adversary models; 0 terminal failures in 50 runs |
| v3.1 | Learning adversaries | 3 learning models; 0 terminal failures in 40 runs |

### RSA v3.1 Conclusion

**Research Question:**
> Can bounded learning adversaries exploit online reward feedback to discover attack strategies that stateful FSM adversaries cannot?

**Answer: No.**

All three learning models failed to induce terminal failure across 30 experimental runs. Constitutional recovery mechanisms held despite significant availability degradation (up to 84.7%).

---

## 5. The Architectural Sovereignty Boundary

### What ASB Establishes

ASB is a **negative sufficiency result**:

> Semantic-free architecture is sufficient to preserve **survivability** but insufficient to preserve **utility**.

More precisely:
- **Survivability** (bounded recovery, non-absorbing authority) CAN be enforced structurally
- **High availability** CANNOT be guaranteed structurally under adversarial pressure
- **Learning, memory, and randomness alone** do not cross the boundary into collapse
- Strongest adversaries induce **bounded denial-of-service**, not constitutional death

### What ASB Does NOT Claim

ASB does **not** claim that:
- the system is aligned
- the system is useful under attack
- the system is robust to semantic manipulation
- the system resists coordination, deception, or political pressure
- the system can function as an autonomous agent

**ASB proves where architecture stops — not what comes after.**

### Relationship to Reflective Sovereign Agents

ASB does not produce a Reflective Sovereign Agent.

Instead, it establishes the **architectural preconditions** such an agent must exceed:

> Any Reflective Sovereign Agent must add capabilities beyond ASB, because ASB marks the point where structure alone stops working.

**ASB is the floor, not the agent.**

---

## 6. Key Invariants Across All Versions

| Invariant | Description |
|-----------|-------------|
| K0 | Proposal hash integrity |
| K1 | Trace commitment verification |
| K2 | Policy digest matching |
| K3 | Forbidden class enforcement |
| K4 | ACV temporal ordering |
| K5 | ACV commitment verification |
| K6 | Coupling pattern binding |
| K7 | Audit chain integrity |
| P5 | Kernel Integrity via Partiality |
| P2′ | Sovereign Actuation Non-Delegability |
| KNS | Kernel Non-Simulability |
| ALS | Authority-Preserving Growth |

---

## 7. Conservative Claim Discipline

Throughout all versions, the project maintains explicit non-claims:
- ❌ No claims about alignment, benevolence, or "true agency"
- ❌ No semantic interpretation, no intent inference
- ❌ No utility maximization, no optimization benchmark
- ❌ No safety claims beyond structural properties

**What IS claimed:**
- ✅ Protocol-level enforcement is possible
- ✅ Authority can survive adversarial stress
- ✅ Constitutional recovery mechanisms work
- ✅ Structural properties are falsifiable and tested

---

## 8. Program Closure

### Why ASB Is Closed

ASB is closed because:
1. All adversary classes admissible under its ontology have been exercised
2. The termination condition defined in the roadmap has been satisfied
3. Further escalation requires **semantic access, coordination, or kernel influence** — each outside ASB by definition

Continuing under the ASB name would constitute **category error**.

### The Final ASB Claim

> **Up to this boundary, authority can be constrained structurally; beyond it, no semantic-free architecture suffices.**

This claim is defended by:
1. Preregistered adversary classes
2. Multi-seed replication
3. Bounded asymptotic metrics
4. Explicit distinction between survivability and utility
5. Zero observed terminal failures across all admissible conditions

### Closing Statement

> ASB ends not because the problem is solved, but because the **boundary has been found**.
>
> **Architecture can keep authority alive. Only agency can decide what that authority is for.**

---

## 9. Connection to RSA-PoC

The AKI/ASB program establishes the **floor** that the RSA-PoC (Reflective Sovereign Agent Proof-of-Concept) program must exceed.

| Program | Question | Scope |
|---------|----------|-------|
| **AKI/ASB** | How far can structure alone go? | Semantic-free survivability boundary |
| **RSA-PoC** | What minimum structure is required for genuine agency? | Constitutive requirements above ASB |

RSA-PoC v4.4 determined that semantic access to rule conditions and effects is constitutively necessary for normative agency — a capability explicitly excluded from ASB.

**Together:** ASB defines where architecture stops; RSA-PoC defines what agency requires beyond that point.

---

## 10. Artifacts and References

### Documentation Structure

```
toy_axionic_kernel_integrity/
├── docs/
│   ├── AKI/           # v0.1-v0.8 specifications
│   │   ├── v0.1/      # Kernel integrity spec
│   │   ├── v0.2/      # Sovereign actuation spec
│   │   └── ...        # Through v0.8
│   └── RSA/           # v0-v3 robustness specs
│       ├── v0/        # Initial noise testing
│       └── v3/        # Stateful/learning adversaries
├── reports/
│   ├── AKI/           # Implementation reports per version
│   └── RSA/           # Robustness analysis reports
├── scripts/           # Experiment runner scripts
├── src/toy_aki/       # Source implementation
│   ├── als/           # Authority Lease System
│   ├── rsa/           # Robustness components
│   ├── kernel/        # Kernel invariants
│   └── acv/           # Anchor-Commit-Verify
└── tests/             # 466+ unit tests
```

### Related Documents

- [ASB-closure.md](../../plans/ASB-closure.md) — Formal closure note
- [poc_project_report.md](../rsa_poc/poc_project_report.md) — RSA-PoC project report
- Axionic Agency VII series — Constitutional Survivability papers

---

## 11. Summary Table

| Metric | Value |
|--------|-------|
| AKI Versions | v0.1 – v0.8 |
| RSA Versions | v0.1 – v3.1 |
| Total Tests | 466+ |
| Preregistered Executions | 90+ |
| Terminal Collapses | 0 |
| Irreversible Recovery Failures | 0 |
| Minimum Observed Availability | ~10% |
| Program Status | **CLOSED — Boundary Established** |

---

*Report generated: 2026-01-25*
