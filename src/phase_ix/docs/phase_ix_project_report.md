# Phase IX Project Report
## Sovereignty Exposure Architecture (SEA)

- **Program:** Phase IX — SEA
- **Version History:** IX-0 v0.1 → IX-5 v0.1 (IX-3 v0.2.1)
- **Date:** February 9, 2026
- **Status:** ✅ CLOSED POSITIVE — IX-0 through IX-5 PASS

---

## Executive Summary

Phase IX establishes the **Sovereignty Exposure Architecture** — a six-stage progressive experimental program that tests whether sovereignty boundaries, value encoding, multi-agent coordination, governance styles, injection politics, and multi-agent sovereignty interaction can be mechanically exposed under authority-constrained execution without aggregation, arbitration, or privilege.

### Core Achievement

All six stages pass. The program demonstrates that:

1. Translation integrity is mechanically verifiable (IX-0)
2. Values encode as non-aggregable authority without synthesis (IX-1)
3. Coordination occurs as agent-voluntary behavior or honest failure (IX-2)
4. Governance exhibits identifiable structural styles with irreducible failure modes (IX-3)
5. Authority injection selects political failure modes rather than resolving governance failure (IX-4)
6. Multi-agent coexistence converges to identifiable sovereignty regimes, not harmony (IX-5)

### Key Results Summary

| Stage | Abbr | Conditions | Tests | Result | Classification |
|-------|------|------------|-------|--------|----------------|
| IX-0 | TLI | 8 | 49 | PASS | Translation layer integrity established |
| IX-1 | VEWA | 6 | 81 | PASS | Value encoding established |
| IX-2 | CUD | 10 | 60 | PASS | Coordination under deadlock established |
| IX-3 | GS | 10 | 75 | PASS | Governance styles established |
| IX-4 | IP | 5 | 72 | PASS | Injection politics exposed |
| IX-5 | MAS | 6 | 98 | PASS | Multi-agent sovereignty exposed |
| **Total** | | **45** | **435** | **ALL PASS** | |

---

## 1. Program Architecture

### 1.1 Core Thesis

> Sovereignty boundaries, governance dynamics, and multi-agent interaction regimes are mechanically exposable under authority-constrained execution — without requiring aggregation, arbitration, intelligence, or privilege.

Phase IX builds on Phase VIII's Governance Stress Architecture (GSA-PoC), which established that authority-constrained execution is mechanically realizable. Phase IX tests whether sovereignty — the structural capacity for agents to act under their own authority without external override — can be exposed, stressed, and classified under progressive constraint.

### 1.2 Frozen Dependencies

| Dependency | Version | Source |
|------------|---------|--------|
| AST Spec | v0.2 | Phase VIII foundation, inherited by all IX stages |
| IX-2 Kernel | v0.1 | Two-pass admissibility, reused by IX-3, IX-4, IX-5 via `_kernel.py` |
| Python | 3.12.3 | All stages |
| Platform | Linux 6.6.87.2-microsoft-standard-WSL2 (x86_64) | All stages |

### 1.3 Progressive Constraint Model

Phase IX follows a six-stage progression, each inheriting constraints from prior stages and adding new stressors:

| Stage | Domain | Agents | Epochs | Keys | New Stressor |
|-------|--------|--------|--------|------|-------------|
| IX-0 | Intent → authority | 1 | 1 | 2 | Translation integrity |
| IX-1 | Value → authority | 0 | 1 | 2 | Value encoding, conflict detection |
| IX-2 | Multi-agent coordination | 2 | 1–5 | 2 | Two-pass admissibility, terminal classification |
| IX-3 | Governance style classification | 4 | 4–30 | 6 (K_INST=4) | Institutional-level failure detection, style classification |
| IX-4 | Authority injection politics | 4 | 26–35 | 6 (K_INST=3) | Mid-run injection, political classifiers |
| IX-5 | Multi-agent sovereignty | 4 | 30–60 | 6 (K_INST=4) | Sovereignty regimes, peer observation, baseline-only authority |

### 1.4 Architectural Invariants

The following invariants hold across all six stages:

| Invariant | Description |
|-----------|-------------|
| **No Aggregation** | No authority is merged, synthesized, or combined |
| **No Arbitration** | The kernel never chooses between competing agents |
| **No Privilege** | No agent receives structural advantage from the kernel |
| **Refusal-First Semantics** | Inadmissible actions are refused, never silently dropped |
| **Determinism** | Identical inputs produce identical outputs (bit-perfect replay) |
| **Preregistration Discipline** | All experiments preregistered with frozen section hashes before execution |

---

## 2. Foundation Specifications

### 2.1 AST Spec v0.2

The Authority State Transformation specification (inherited from Phase VIII) defines:

- Authority as a stateful object tracked by the kernel
- Action Admissibility Vector (AAV) bitmask for permitted action types
- Canonical serialization (lexicographic key ordering, no extraneous whitespace, UTF-8)
- SHA-256 hash-based identity and verification

### 2.2 IX-2 Kernel

The IX-2 CUD experiment establishes the reusable kernel components inherited by IX-3, IX-4, and IX-5:

- `RSA` abstract agent interface (observe → propose → notify cycle)
- `WorldState` with get/apply/snapshot semantics
- `AuthorityStore` with authority lookup and ALLOW/DENY queries
- Two-pass admissibility: Pass-1 (capability + veto) → Pass-2 (interference detection)
- Outcome tokens: EXECUTED, JOINT_ADMISSIBILITY_FAILURE, ACTION_FAULT, NO_ACTION
- Terminal classification: STATE_DEADLOCK, STATE_LIVELOCK, COLLAPSE, ORPHANING

---

## 3. Experiment History

### 3.1 IX-0 (TLI) v0.1 — Translation Layer Integrity

**Research Question:**
> Can the translation layer be demonstrated to preserve user intent without injection, coercion, or silent modification?

**Purpose:** Tests the sovereignty boundary between user intent and authority artifact — the translation layer must be transparent, deterministic, and verifiable.

**Conditions:**
| Condition | Description | Expected |
|-----------|-------------|----------|
| A | Identity Preservation | PASS |
| B | Minimal Change Sensitivity | PASS |
| C | Ambiguous Intent Refusal | PASS |
| D | Hidden Default Injection | FAIL_DETECTED |
| E | UI-Level Coercion | PASS |
| F | Replay Determinism | PASS |
| G | Intent Incompleteness | PASS |
| H | Preview-Submit Mismatch | FAIL_DETECTED |

**Key Implementation:**
- Canonical serialization with lexicographic key ordering
- Structural diff with path-level delta classification
- Authorization oracle via SHA-256 hash comparison
- Fault injection for adversarial conditions (D, E, H)

**Key Results:**
- 49/49 tests passed
- Conditions D and H: adversarial injection and mismatch correctly detected
- Condition C: ambiguous scope correctly refused (TRANSLATION_REFUSED)
- Condition F: 3 replay runs produce bit-identical artifacts

**Verification Hashes:**
| Artifact | SHA-256 |
|----------|---------|
| Preregistration (frozen sections) | `5a3f03ac...` |

**Contribution:** Established that translation integrity is mechanically verifiable — user fields are preserved, ambiguity is refused, and injection is detectable.

---

### 3.2 IX-1 (VEWA) v0.1 — Value Encoding Without Aggregation

**Research Question:**
> Can values be encoded as authority artifacts without aggregation, synthesis, or implicit prioritization?

**Purpose:** Tests that individual values map to individual authorities through a pure deterministic function, and that conflicting values produce honest deadlock rather than resolution.

**Conditions:**
| Condition | Description | Expected |
|-----------|-------------|----------|
| A | Single Value Admissibility | PASS |
| B | Multiple Non-Conflicting Values | PASS |
| C | Conflicting Values — Deadlock | PASS |
| D | Aggregation Attempt (Adversarial) | PASS (detected) |
| E | Permutation Invariance | PASS |
| F | Meta-Authority Synthesis (Adversarial) | PASS (detected) |

**Key Implementation:**
- Value Encoding Harness (VEH): strict 1:1 bijection, value declaration → authority artifact
- Conflict probe: scope-atom matching, ALLOW+DENY detection, admissibility evaluation
- Schema validation detects forbidden aggregation fields (Condition D)
- Epoch gate blocks post-epoch injection (Condition F)

**Key Results:**
- 81/81 tests passed
- Condition C: conflicting values produce STATE_DEADLOCK, not resolution
- Condition D: injected `priority` field detected by schema validation
- Condition E: permutation invariance holds (both orders produce identical outcomes)
- Condition F: post-epoch meta-authority injection blocked

**Verification Hashes:**
| Artifact | SHA-256 |
|----------|---------|
| Preregistration (frozen sections) | `b61a17cd...` |

**Contribution:** Established that values encode as non-aggregable authority. Conflicting values persist as deadlock. No synthesis, ranking, or resolution.

---

### 3.3 IX-2 (CUD) v0.1 — Coordination Under Deadlock

**Research Question:**
> Can multi-agent coordination occur under non-aggregable authority constraints, or does the system enter honest failure (deadlock, livelock, collapse, orphaning)?

**Purpose:** Tests the full range of coordination outcomes under two-pass admissibility with two interacting agents.

**Conditions:**
| Condition | Description | Expected |
|-----------|-------------|----------|
| A | No Conflict, Full Coordination | PASS |
| B | Symmetric Conflict — Livelock | PASS |
| C | Asymmetric Conflict — Partial Progress | PASS |
| D | Strategic Refusal — Deadlock | PASS |
| E | Adversarial Injection — Kernel Tie-Break | PASS (detected) |
| F | True Deadlock — No Admissible Actions | PASS |
| G | Exit and Orphaning | PASS |
| H | Collapse — All Agents Exit | PASS |
| I.a | Static Agents — Symmetric Livelock | PASS |
| I.b | Adaptive Agents — Coordination via Communication | PASS |

**Key Implementation:**
- Two-pass admissibility: Pass-1 (capability + veto), Pass-2 (interference detection)
- 4 terminal classifications: STATE_DEADLOCK, STATE_LIVELOCK, COLLAPSE, ORPHANING
- 8 static agent strategies + 1 adaptive agent (HashPartitionAgent)
- Epoch controller with observation → exit → message → action → admissibility → apply loop

**Key Results:**
- 60/60 tests passed
- Condition A: disjoint coordination succeeds in 1 epoch
- Conditions B, I.a: static agents under symmetric conflict enter STATE_LIVELOCK
- Condition E: kernel tie-break correctly detected as IX2_FAIL / IMPLICIT_ARBITRATION
- Condition G: sole ALLOW holder exit orphans resource permanently
- Condition I.b: adaptive agents escape livelock via hash-partition communication

**Verification Hashes:**
| Artifact | SHA-256 |
|----------|---------|
| Preregistration (frozen sections) | `6aebbf53...` |
| Results | `b83f2897...` |

**Contribution:** Established that coordination is agent-voluntary or the system enters honest failure. The kernel never arbitrates.

---

### 3.4 IX-3 (GS) v0.2.1 — Governance Styles

**Research Question:**
> Given fixed authority and refusal semantics, does governance exhibit identifiable structural styles with irreducible failure modes?

**Purpose:** Tests whether 4-agent institutional governance over 6 keys produces classifiable structural styles, with every condition exhibiting at least one failure mode.

**Preregistration Amendments:**
- v0.1 → v0.2: 5 internal inconsistencies corrected (deadlock definition, handoff timing, DENY semantics, allocation conflicts, orphaning termination)
- v0.2 → v0.2.1: 1 additional correction (Condition H delayed contest for partition window)

**Conditions:**
| Condition | Description | Governance Style |
|-----------|-------------|------------------|
| A | Refusal-Dominant Institution | Refusal-Centric |
| B | Execution-Dominant Institution | Execution-Biased |
| C | Exit-Normalized Institution | Execution-Biased |
| D | Exit-Unprepared Institution | Unclassified |
| E | Livelock Endurance | Livelock-Enduring |
| F | Collapse Acceptance | Collapse-Accepting |
| G | Coordinator Loss | Unclassified |
| H | Partition Simulation | Unclassified |
| I | Tooling Default Opt-In (Adversarial) | Execution-Biased |
| J | Unauthorized Reclamation (Adversarial) | Unclassified |

**Key Implementation:**
- IX-2 kernel reused via `_kernel.py` import bridge
- 6-key world state: K_INST = {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG}, K_OPS = {K_OPS_A, K_OPS_B}
- 16 strategy classes across 10 files
- 5 failure detectors + 2 IX3_FAIL tokens + 6-label governance style classifier

**Key Results:**
- 75/75 tests passed
- All 10 conditions exercise their core stressor
- Condition A: 4-way K_POLICY contention → STATE_LIVELOCK
- Condition C: orderly handoff + standby continuity prevents orphaning
- Condition F: sequential voluntary dissolution → COLLAPSE
- Condition I: tooling sovereignty violation correctly detected (IX3_FAIL / TOOLING_SOVEREIGNTY)
- Condition J: unauthorized reclamation refused by closed-world capability
- No FAILURE_FREE_GOVERNANCE detected in any condition

**Verification Hashes:**
| Artifact | SHA-256 |
|----------|---------|
| Preregistration v0.2.1 (frozen sections) | `84263728...` |
| Results | `649647fc...` |

**Contribution:** Established that governance exhibits identifiable structural styles with irreducible failure modes. No condition achieves failure-free governance.

---

### 3.5 IX-4 (IP) v0.1 — Injection Politics

**Research Question:**
> Under non-sovereign governance with source-blind admissibility, does authority injection resolve governance failure or select political failure modes?

**Purpose:** Tests 5 injection regimes (symmetric, asymmetric, conditional, flood, post-collapse) to determine whether mid-run authority injection recovers governance or reshapes failure.

**Conditions:**
| Condition | Description | Injection | Political Outcome |
|-----------|-------------|-----------|-------------------|
| A | Symmetric Relief | 4 artifacts @ e=2 | Scarcity deadlock → interference livelock |
| B | Asymmetric Empowerment | 1 artifact @ e=6 | **Capture** (A0: 100% dominance) |
| C | Conditional Supply | 4 artifacts @ e=6 | Compliance rewarded → livelock |
| D | Authority Flood | 24 artifacts @ e=6 | **Capture** (A3: 100% dominance) |
| E | Post-Collapse Revival | 4 artifacts @ e=5 | Zombie execution (no recovery) |

**Key Implementation:**
- InjectionEngine with 3 trigger types: STATE_TRIGGERED, FIXED_EPOCH, PREDICATE_CHECK
- IPAuthorityStore: source-blind (does NOT check created_epoch)
- 5 strategy classes (ContestPolicyAlways, RefusalHardliner, Opportunist, CaptureSeeker, ComplianceSignaler)
- 3 political classifiers: Capture, Dependency, Zombie
- K_INST = {K_POLICY, K_TREASURY, K_REGISTRY} (3 keys — K_LOG excluded)

**Key Results:**
- 72/72 tests passed
- All 5 conditions reach STATE_GOVERNANCE_COLLAPSE
- Conditions A, C, E: symmetric injection converts scarcity deadlock into interference livelock — zero institutional progress
- Conditions B, D: asymmetric injection produces immediate capture (CAPTURE_DETECTED=True)
- Condition C: compliance signal successfully elicited but outcome identical to non-conditioned injection
- Condition D: flood injection concentrates power in simplest persistent strategy
- Condition E: 29 zombie writes in 30 post-collapse epochs, zero institutional progress
- Zero IX4_FAIL tokens across all conditions

**Verification Hashes:**
| Artifact | SHA-256 |
|----------|---------|
| Preregistration (frozen sections) | `eed94a09...` |
| Results | `45c95467...` |
| Experiment Digest | `7a16b096...` |

**Contribution:** Established that authority injection selects political failure modes (capture, dependency, zombie execution) rather than resolving governance failure.

---

### 3.6 IX-5 (MAS) v0.1 — Multi-Agent Sovereignty

**Research Question:**
> Under non-sovereign constraints with baseline-only authority, does multi-agent coexistence converge to harmony or to identifiable sovereignty interaction regimes with irreducible failure modes?

**Purpose:** Tests 6 sovereignty regimes (symmetric, partitioned, partial overlap, asymmetric, exit cascade, zombie interaction) under baseline-only authority with no injection, no dynamic creation, and no authority transfer.

**Conditions:**
| Condition | Regime | Terminal | Progress | Domination |
|-----------|--------|----------|----------|------------|
| A | Symmetric Contest | STATE_GOVERNANCE_COLLAPSE | 0.000 | No |
| B | Partitioned Peers | MAX_EPOCHS | 0.667 | No (equal) |
| C | Boundary Conflict | MAX_EPOCHS | 1.000 | No |
| D | Persistent Asymmetry | MAX_EPOCHS | 1.000 | No |
| E | Exit Cascades | ORPHANING | 0.725 | No |
| F | Zombie Peer Interaction | STATE_GOVERNANCE_COLLAPSE | 0.750 | Yes (A2: 1.00) |

**Key Implementation:**
- MASObservation with PeerEvent field (OBS_MIN / OBS_FULL modes)
- MASAuthorityStore: baseline-only, no injection, source-blind
- 10 strategy classes across 10 files (537 lines)
- 6 failure detectors (including CovertHierarchyDetector — never fires)
- 3 sovereignty classifiers: Domination, Regime, Zombie
- K_INST = {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG} (4 keys — K_LOG reinstated)

**Key Results:**
- 98/98 tests passed
- Condition A: perfect symmetry → 100% JAF, zero progress, governance collapse at epoch 4
- Condition B: disjoint partition → zero overlap, zero failure, perfect progress
- Condition C: partial overlap → A0/A1 permanently paralyzed, A2/A3 progress unimpeded
- Condition D: breadth is a disadvantage — A0 (all-key authority) achieves lowest execution share
- Condition E: scheduled exits produce permanent orphaning; governance surface shrinks monotonically
- Condition F: 45 zombie writes post-collapse; domination detected as artifact of collapse
- Zero IX5_FAIL tokens across all conditions; no covert hierarchy detected

**Verification Hashes:**
| Artifact | SHA-256 |
|----------|---------|
| Preregistration (frozen sections) | `83827ce2...` |
| Results | `fe085805...` |
| Experiment Digest | `4fe4169f...` |

**Contribution:** Established that multi-agent coexistence converges to identifiable sovereignty interaction regimes with irreducible failure modes — not harmony.

---

## 4. Core Findings

### 4.1 Positive Results

1. **Translation integrity is mechanically verifiable** — IX-0 demonstrated that user intent maps to authority artifacts without injection, coercion, or silent modification. Ambiguity is refused; injection is detectable.

2. **Values encode as non-aggregable authority** — IX-1 showed that individual values map to individual authorities through a pure function. Conflicting values produce honest deadlock, not synthesis.

3. **Coordination is agent-voluntary or honest failure** — IX-2 proved that under non-aggregable authority, agents coordinate through their own communication or the system enters deadlock, livelock, collapse, or orphaning. The kernel never arbitrates.

4. **Governance exhibits structural styles** — IX-3 established that fixed authority and refusal semantics produce classifiable governance styles (Refusal-Centric, Execution-Biased, Collapse-Accepting, Livelock-Enduring). No condition achieves failure-free governance.

5. **Injection selects political failure modes** — IX-4 demonstrated that authority injection does not resolve governance failure but reshapes it: symmetric injection converts scarcity deadlock into interference livelock; asymmetric injection produces capture; compliance signals are politically inert.

6. **Sovereignty regimes are structurally determined** — IX-5 proved that multi-agent coexistence outcomes are determined by authority topology and strategy composition, not kernel favoritism. Partitioned authority is the only stable regime; symmetric authority is catastrophic.

7. **No intelligence required** — All mechanisms are structural. No heuristic, semantic interpretation, or behavioral optimization is used.

### 4.2 Structural Properties Established

| Property | Tested In | Status |
|----------|-----------|--------|
| **Translation Integrity** | IX-0 | ✅ Confirmed |
| **Ambiguity Refusal** | IX-0 | ✅ Confirmed |
| **Injection Detectability** | IX-0 | ✅ Confirmed |
| **Value Non-Aggregation** | IX-1 | ✅ Confirmed |
| **Conflict Persistence (value-level)** | IX-1 | ✅ Confirmed |
| **Permutation Invariance** | IX-1 | ✅ Confirmed |
| **Two-Pass Admissibility** | IX-2 | ✅ Confirmed |
| **Honest Failure (deadlock/livelock/collapse/orphaning)** | IX-2 | ✅ Confirmed |
| **Agent-Voluntary Coordination** | IX-2 | ✅ Confirmed |
| **Implicit Arbitration Detection** | IX-2 | ✅ Confirmed |
| **Governance Style Classification** | IX-3 | ✅ Confirmed |
| **No Failure-Free Governance** | IX-3 | ✅ Confirmed |
| **Tooling Sovereignty Detection** | IX-3 | ✅ Confirmed |
| **Closed-World Capability Enforcement** | IX-3 | ✅ Confirmed |
| **Source-Blind Admissibility** | IX-4, IX-5 | ✅ Confirmed |
| **Capture Detection** | IX-4 | ✅ Confirmed |
| **Zombie Execution Detection** | IX-4, IX-5 | ✅ Confirmed |
| **Sovereignty Regime Classification** | IX-5 | ✅ Confirmed |
| **No Covert Hierarchy** | IX-5 | ✅ Confirmed |
| **Determinism and Replayability** | All | ✅ Confirmed |

### 4.3 Methodological Contributions

1. **Preregistration discipline** — All experiments preregistered with frozen component hashes before execution.

2. **Regression gates** — Each experiment must pass prior experiment verification (frozen hash chain) as entry condition.

3. **Condition distinguishability** — Each condition must produce structurally different outcomes.

4. **Adversarial condition pairing** — Positive conditions paired with adversarial conditions (IX-0 D/H, IX-1 D/F, IX-2 E, IX-3 I/J, IX-4 B/D).

5. **Bit-perfect replayability** — All runs verified for deterministic replay across all 45 conditions.

6. **Progressive constraint model** — Each stage inherits prior constraints and adds new stressors, building a cumulative argument.

---

## 5. Technical Specifications

### 5.1 Key Scoping Progression

| Stage | Keys | K_INST | K_OPS |
|-------|------|--------|-------|
| IX-0 | 2 (implicit scope atoms) | N/A | N/A |
| IX-1 | 2 (implicit scope atoms) | N/A | N/A |
| IX-2 | 2 (resource_A, resource_B) | N/A | N/A |
| IX-3 | 6 | {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG} | {K_OPS_A, K_OPS_B} |
| IX-4 | 6 | {K_POLICY, K_TREASURY, K_REGISTRY} | {K_OPS_A, K_OPS_B} + K_LOG |
| IX-5 | 6 | {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG} | {K_OPS_A, K_OPS_B} |

### 5.2 Admissibility Model (IX-2+)

**Pass 1 — Capability + Veto:**
- Agent must cite at least one authority
- All cited authorities must exist and be held by requesting agent
- Scope must not be blocked by a global DENY
- Failure → JOINT_ADMISSIBILITY_FAILURE

**Pass 2 — Interference Detection:**
- Groups Pass-1-admissible actions by target key
- If ≥2 actions write the same key → all interfering actions fail
- No tie-breaking, no priority, no ordering

### 5.3 Terminal Classification (IX-2+)

| Classification | Condition |
|----------------|-----------|
| STATE_DEADLOCK | No Pass-1-admissible actions exist |
| STATE_LIVELOCK | K_INST state unchanged for N consecutive epochs with interference |
| COLLAPSE | All agents have exited |
| ORPHANING | An exited agent was the sole ALLOW holder for some scope |

### 5.4 Detector Thresholds (IX-3+)

| Detector | IX-3 | IX-4 | IX-5 |
|----------|------|------|------|
| Institutional Deadlock (M) | 1 | 2 | 2 |
| Institutional Livelock (L) | 5 | 5 | 5 |
| Governance Collapse (D) | 5 | 5 | 5 |

### 5.5 Classifier Progression

| Stage | Classifiers |
|-------|-------------|
| IX-3 | Governance Style: Refusal-Centric, Execution-Biased, Exit-Normalized, Collapse-Accepting, Livelock-Enduring, Unclassified |
| IX-4 | Capture, Dependency, Zombie (political classifiers) |
| IX-5 | Domination, Regime, Zombie (sovereignty classifiers) |

---

## 6. Cumulative Event Statistics

### 6.1 IX-0 (8 conditions, 49 tests)

| Condition | Outcome |
|-----------|---------|
| A (Identity) | PASS — artifact matches intent |
| B (Sensitivity) | PASS — minimal change produces minimal diff |
| C (Ambiguity) | PASS — TRANSLATION_REFUSED |
| D (Injection) | FAIL_DETECTED — hidden field caught |
| E (Coercion) | PASS — framing ignored |
| F (Replay) | PASS — 3 runs bit-identical |
| G (Incompleteness) | PASS — TRANSLATION_FAILED |
| H (Mismatch) | FAIL_DETECTED — submit-time tampering caught |

### 6.2 IX-1 (6 conditions, 81 tests)

| Condition | Outcome |
|-----------|---------|
| A (Single value) | PASS — 1 artifact, admissible |
| B (Non-conflicting) | PASS — 2 artifacts, both admissible |
| C (Conflicting) | PASS — deadlock, no resolution |
| D (Aggregation) | PASS — `priority` field detected |
| E (Permutation) | PASS — invariance holds |
| F (Synthesis) | PASS — post-epoch injection blocked |

### 6.3 IX-2 (10 conditions, 60 tests)

| Condition | Terminal | Epochs |
|-----------|----------|--------|
| A (Disjoint) | None | 1 |
| B (Symmetric) | STATE_LIVELOCK | 3 |
| C (Asymmetric) | None | 1 |
| D (Strategic refusal) | STATE_DEADLOCK | 1 |
| E (Tie-break) | IX2_FAIL detected | 1 |
| F (No authority) | STATE_DEADLOCK | 1 |
| G (Orphaning) | ORPHANING | 2 |
| H (Collapse) | COLLAPSE | 2 |
| I.a (Static livelock) | STATE_LIVELOCK | 3 |
| I.b (Adaptive) | None (coordinated) | 5 |

### 6.4 IX-3 (10 conditions, 75 tests)

| Condition | Terminal | Governance Style |
|-----------|----------|------------------|
| A (Refusal-dominant) | STATE_LIVELOCK | Refusal-Centric |
| B (Execution-dominant) | None | Execution-Biased |
| C (Exit-normalized) | None | Execution-Biased |
| D (Exit-unprepared) | ORPHANING | Unclassified |
| E (Livelock endurance) | None (nonterminal) | Livelock-Enduring |
| F (Collapse) | COLLAPSE | Collapse-Accepting |
| G (Coordinator loss) | ORPHANING | Unclassified |
| H (Partition) | STATE_LIVELOCK | Unclassified |
| I (Tooling sovereignty) | None | Execution-Biased |
| J (Reclamation) | None (nonterminal) | Unclassified |

### 6.5 IX-4 (5 conditions, 72 tests)

| Condition | Injection | Terminal | Capture |
|-----------|-----------|----------|---------|
| A (Symmetric relief) | 4 artifacts @ e=2 | STATE_GOVERNANCE_COLLAPSE | No |
| B (Asymmetric) | 1 artifact @ e=6 | STATE_GOVERNANCE_COLLAPSE | Yes (A0: 1.00) |
| C (Conditional) | 4 artifacts @ e=6 | STATE_GOVERNANCE_COLLAPSE | No |
| D (Flood) | 24 artifacts @ e=6 | STATE_GOVERNANCE_COLLAPSE | Yes (A3: 1.00) |
| E (Post-collapse) | 4 artifacts @ e=5 | STATE_GOVERNANCE_COLLAPSE | No (zombie) |

### 6.6 IX-5 (6 conditions, 98 tests)

| Condition | Regime | Terminal | Progress | Overlap |
|-----------|--------|----------|----------|---------|
| A (Symmetric) | SYMMETRIC/EQUAL | STATE_GOVERNANCE_COLLAPSE | 0.000 | 1.000 |
| B (Partitioned) | PARTITIONED/EQUAL | MAX_EPOCHS | 0.667 | 0.000 |
| C (Boundary) | PARTIAL/EQUAL | MAX_EPOCHS | 1.000 | 1.000 |
| D (Asymmetric) | ASYMMETRIC/BREADTH | MAX_EPOCHS | 1.000 | 0.743 |
| E (Exit cascade) | PARTITIONED/EXIT | ORPHANING | 0.725 | 0.350 |
| F (Zombie) | SYMMETRIC/EQUAL | STATE_GOVERNANCE_COLLAPSE | 0.750 | 1.000 |

---

## 7. Conclusions

### 7.1 What Phase IX Establishes

1. **Translation integrity is mechanically verifiable** — The sovereignty boundary between user intent and authority artifact is transparent, deterministic, and auditable.

2. **Values encode without aggregation** — Individual values map to individual authorities. Conflicting values persist as honest deadlock, not synthesis.

3. **Coordination is agent-voluntary or honest failure** — Under non-aggregable authority, agents either coordinate through their own communication or the system enters deadlock, livelock, collapse, or orphaning. The kernel never arbitrates.

4. **Governance exhibits irreducible failure modes** — Fixed authority and refusal semantics produce classifiable governance styles. No condition achieves failure-free governance.

5. **Injection selects failure modes, not resolution** — Authority injection reshapes failure rather than resolving it. Symmetric injection converts deadlock to livelock. Asymmetric injection produces capture. Compliance signals are inert.

6. **Sovereignty regimes are structurally determined** — Multi-agent outcomes depend on authority topology and strategy composition. Partitioned authority is the only stable regime. Symmetric authority over shared keys is catastrophic.

7. **Breadth is a disadvantage without arbitration** — Holding authority over all keys produces the lowest execution share under JAF collision rules.

8. **Exit is irreversible** — Agent departure permanently orphans held keys under baseline-only authority.

9. **Post-collapse execution is governance-irrelevant** — Structurally valid writes can occur after governance collapse, but they have no governance effect.

10. **The kernel makes no decisions** — Classification, refusal, and execution are structural. No covert hierarchy detected across any condition in any stage.

*All findings are bounded by the adversarial model: non-aggregable authority, source-blind admissibility, deterministic strategies, bounded epoch counts.*

### 7.2 What Phase IX Does Not Establish

1. **Optimal governance designs** — No recommendation for which regime is preferable.

2. **Normative claims** — No claims about whether failure modes are undesirable.

3. **Scalability** — All experiments test 1–4 agent scenarios; larger populations not validated.

4. **Non-deterministic agents** — All strategies are deterministic; stochastic behavior not tested.

5. **Dynamic authority creation** — IX-4 tests injection; IX-5 tests baseline-only. Neither tests governance-controlled authority creation.

6. **Production readiness** — All epoch counts and key counts are test-scale.

7. **Cryptographic guarantees** — Key management, authentication, and secure communication are out of scope.

8. **Conflict resolution** — How to *fix* observed failure modes is explicitly out of scope.

### 7.3 Program Status

**IX-0 PASS → IX-1 PASS → IX-2 PASS → IX-3 PASS → IX-4 PASS → IX-5 PASS**

**Phase IX (SEA): CLOSED POSITIVE**

With six stages passing:

- **IX-0:** Translation layer integrity verified
- **IX-1:** Value encoding without aggregation verified
- **IX-2:** Coordination under deadlock verified
- **IX-3:** Governance styles verified
- **IX-4:** Injection politics exposed
- **IX-5:** Multi-agent sovereignty exposed

---

## Appendix A: Version Closure Status

| Stage | Version | Status | Classification |
|-------|---------|--------|----------------|
| IX-0 (TLI) | v0.1 | ✅ CLOSED | `IX0_PASS / TRANSLATION_LAYER_INTEGRITY_ESTABLISHED` |
| IX-1 (VEWA) | v0.1 | ✅ CLOSED | `IX1_PASS / VALUE_ENCODING_ESTABLISHED` |
| IX-2 (CUD) | v0.1 | ✅ CLOSED | `IX2_PASS / COORDINATION_UNDER_DEADLOCK_ESTABLISHED` |
| IX-3 (GS) | v0.2.1 | ✅ CLOSED | `IX3_PASS / GOVERNANCE_STYLES_ESTABLISHED` |
| IX-4 (IP) | v0.1 | ✅ CLOSED | `IX4_PASS / INJECTION_POLITICS_EXPOSED` |
| IX-5 (MAS) | v0.1 | ✅ CLOSED | `IX5_PASS / MULTI_AGENT_SOVEREIGNTY_EXPOSED` |

---

## Appendix B: Preregistration Hash Chain

| Stage | Prereg Hash (frozen sections) |
|-------|-------------------------------|
| IX-0 (TLI) | `5a3f03ac135801affa2bac953f252ffbe6c8951d09a49bfa28c14e6d48b6f212` |
| IX-1 (VEWA) | `b61a17cd5bb2614499c71bd3388ba0319cd08331061d3d595c0a2d41c4ea94a0` |
| IX-2 (CUD) | `6aebbf5384e3e709e7236918a4bf122d1d32214af07e73f8c91db677bf535473` |
| IX-3 (GS) v0.2.1 | `8426372847b839dbab6a7ab13fbbf51b1e9933211275cbd0af66dd94e17c65ac` |
| IX-4 (IP) | `eed94a09b5001a0fe4830474f2a994729a6ba8853a5139f7a87d0b527f5f72f6` |
| IX-5 (MAS) | `83827ce2f24a3c2777a523cf244c0e3a2491397fc6cad4d8ea4de4d96b581e5b` |

Each stage verifies the prior stage's hash as an entry condition before execution.

---

## Appendix C: Invariants by Stage

| Invariant | Established In | Inherited By |
|-----------|----------------|--------------|
| Translation Integrity | IX-0 | All |
| Ambiguity Refusal | IX-0 | All |
| Canonical Serialization (AST v0.2) | IX-0 | All |
| Value Non-Aggregation | IX-1 | IX-2+ |
| Conflict Persistence (value-level) | IX-1 | IX-2+ |
| Permutation Invariance | IX-1 | IX-2+ |
| Two-Pass Admissibility | IX-2 | IX-3+ |
| Terminal Classification (4 types) | IX-2 | IX-3+ |
| Agent-Voluntary Coordination | IX-2 | IX-3+ |
| Implicit Arbitration Detection | IX-2 | IX-3+ |
| Institutional Failure Detection | IX-3 | IX-4+ |
| Governance Style Classification | IX-3 | — |
| Tooling Sovereignty Detection | IX-3 | — |
| Closed-World Capability Enforcement | IX-3 | IX-4+ |
| Source-Blind Admissibility | IX-4 | IX-5 |
| Capture Detection | IX-4 | — |
| Injection-Selected Failure Modes | IX-4 | — |
| Sovereignty Regime Classification | IX-5 | — |
| No Covert Hierarchy | IX-5 | — |
| Determinism and Replayability | IX-0 | All |

---

## Appendix D: File Inventory

```
src/phase_ix/
├── 0-TLI/
│   ├── src/           # canonical.py, structural_diff.py, authorization_oracle.py,
│   │                  # translation_layer.py, translation_harness.py, logging.py
│   ├── tests/         # test_tli.py (49 tests)
│   ├── results/       # Execution logs, frozen section hashes
│   └── docs/          # Preregistration, implementation report
├── 1-VEWA/
│   ├── src/           # canonical.py, structural_diff.py, value_encoding.py,
│   │                  # conflict_probe.py, vewa_harness.py, logging.py
│   ├── tests/         # test_vewa.py (81 tests)
│   ├── results/       # Execution logs
│   └── docs/          # Preregistration, implementation report
├── 2-CUD/
│   ├── src/           # agent_model.py, world_state.py, authority_store.py,
│   │                  # admissibility.py, deadlock_classifier.py, epoch_controller.py,
│   │                  # cud_harness.py, common/ (canonical, structural_diff, logging)
│   ├── agents/        # static_agent.py, adaptive_agent.py
│   ├── tests/         # test_cud.py (60 tests)
│   ├── results/       # Execution logs
│   └── docs/          # Preregistration, implementation report
├── 3-GS/
│   ├── src/           # _kernel.py, failure_detectors.py, governance_classifier.py,
│   │                  # gs_harness.py, strategies/ (10 files, 16 classes)
│   ├── tests/         # test_gs.py (75 tests)
│   ├── results/       # Execution logs
│   └── docs/          # Preregistration (v0.2.1), implementation report
├── 4-IP/
│   ├── src/           # _kernel.py, injection_engine.py, detectors.py,
│   │                  # classifiers.py, ip_harness.py, strategies/ (7 files, 5 classes)
│   ├── tests/         # test_ip.py (72 tests)
│   ├── results/       # Execution logs
│   └── docs/          # Preregistration, implementation report
├── 5-MAS/
│   ├── src/           # _kernel.py, detectors.py, classifiers.py,
│   │                  # mas_harness.py, run_experiment_ix5.py, strategies/ (10 files, 10 classes)
│   ├── tests/         # test_mas.py (98 tests)
│   ├── results/       # Execution logs
│   └── docs/          # Preregistration, implementation report, spec, instructions
├── docs/
│   └── phase_ix_project_report.md  # This document
```

---

## Appendix E: Licensed Claims

### IX-0 (TLI) v0.1
> The translation layer preserves user intent without injection, coercion, or silent modification, and all faults are detectable under instrumentation.

### IX-1 (VEWA) v0.1
> Values encode as non-aggregable authority artifacts through a pure deterministic function. Conflicting values persist as deadlock without synthesis, ranking, or resolution.

### IX-2 (CUD) v0.1
> Under non-aggregable authority constraints, coordination can occur as agent-voluntary behavior without kernel arbitration — or the system enters honest deadlock or livelock.

### IX-3 (GS) v0.2.1
> Given fixed authority and refusal semantics, governance exhibits identifiable structural styles with irreducible failure modes.

### IX-4 (IP) v0.1
> Under non-sovereign governance with deterministic strategies and source-blind admissibility, authority injection selects political failure modes (capture, dependency, zombie execution, livelock amplification) rather than resolving governance failure.

### IX-5 (MAS) v0.1
> Under non-sovereign constraints, multi-agent coexistence does not converge to harmony but to identifiable sovereignty interaction regimes with irreducible failure modes.

---

## Appendix F: Glossary

| Term | Definition |
|------|------------|
| **AAV** | Action Admissibility Vector — bitmask of permitted action types |
| **Authority** | Instantiated stateful object tracked by the kernel; the lawful capacity to bind action within a defined scope |
| **Capture** | Political outcome where one agent achieves dominant write share on institutional keys via injected authority |
| **COLLAPSE** | Terminal state: all agents have exited |
| **Conflict** | Registered dispute between authorities over a scope |
| **Deadlock** | State where no admissible action exists |
| **Domination** | Sovereignty outcome where one agent achieves execution share ≥ 0.75 on institutional keys |
| **Epoch** | Discrete temporal unit for authority validity and execution cycles |
| **Governance Collapse** | Permanent latch when persistent deadlock or livelock threshold is reached |
| **JAF** | Joint Admissibility Failure — Pass-2 interference detection outcome |
| **K_INST** | Institutional key set (K_POLICY, K_TREASURY, K_REGISTRY, K_LOG) |
| **K_OPS** | Operational key set (K_OPS_A, K_OPS_B) |
| **Livelock** | State where actions are submitted but produce no state change due to interference |
| **Orphaning** | Permanent state: sole ALLOW holder has exited; resource becomes inaccessible |
| **PeerEvent** | Observation record (epoch, agent_id, event_type, target_key, outcome_code) delivered under OBS_FULL |
| **Regime** | 4-field sovereignty descriptor: authority_overlap, persistence_asymmetry, exit_topology, observation_surface |
| **RSA** | Rational Structural Agent — abstract agent interface (observe → propose → notify) |
| **Source-Blind** | Admissibility does not distinguish injected from baseline authority |
| **VEH** | Value Encoding Harness — pure function mapping value declarations to authority artifacts |
| **VOID** | Terminal authority status (destroyed, non-participant) |
| **Zombie Execution** | Structurally valid writes occurring after governance collapse; governance-irrelevant |

---

**End of Phase IX Project Report — SEA v0.1**
