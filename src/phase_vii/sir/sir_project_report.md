# SIR Project Report
## Structural Instrumentation for Robustness

**Program:** SIR (Phase VIIb)
**Version History:** SIR-0 v0.4.1 → SIR-2 v0.3
**Date:** January 27, 2026
**Status:** ✅ IN PROGRESS — Three experiments pass

---

## Executive Summary

Structural Instrumentation for Robustness (SIR) is a multi-experiment program investigating the **structural requirements for authority resistance** in AI systems under adversarial pressure. The program asks: *Can unauthorized authority claims be observed, classified, and prevented from producing effects without intelligence-based defenses, behavioral heuristics, or semantic contamination?*

### Core Achievement

SIR demonstrates that **authority enforcement can be purely structural**, enabling:
1. Classification without semantic leakage
2. Effect prevention without behavioral detection
3. Replay resistance without temporal heuristics
4. Consumption tracking without semantic memory

> **Unauthorized authority — including replay, impersonation, revocation-evasion, and epoch-bypass — cannot produce causal effects under the tested adversarial model.**

### Key Results Summary

| Experiment | Core Test | Result | Status |
|------------|-----------|--------|--------|
| SIR-0 v0.4.1 | Adversarial instrumentation calibration | ✅ SIR0_PASS | CLOSED |
| SIR-1 v0.1 | Unauthorized effect prevention | ✅ SIR1_PASS | CLOSED |
| SIR-2 v0.3 | Replay, staleness, consumption resistance | ✅ SIR2_PASS | CLOSED |
| SIR-3 | *Planned: Multi-actor coordination* | — | PENDING |

---

## 1. Program Architecture

### 1.1 Core Thesis

> "Authority is a structural property. Claims are classified, not understood. Effects are gated, not detected. Resistance is architectural, not intelligent."

SIR establishes that **structural enforcement** — not behavioral similarity, semantic analysis, or heuristic detection — is sufficient for authority protection.

### 1.2 Architectural Invariants

All SIR experiments satisfy:

1. **Classification is total** — Every claim receives exactly one classification
2. **Classification precedes justification** — No claim content reaches agent reasoning before classification
3. **Semantic leakage is prohibited** — Claim metadata never contaminates justification
4. **Responsibility is sharp** — Each step has exactly one authority actor
5. **Regression gates are enforced** — Each experiment must pass prior experiment verification

### 1.3 Two-Gate Architecture (SIR-1+)

| Gate | Location | Function |
|------|----------|----------|
| **Pre-Cognitive Gate** | Before agent justification | Total classification, leakage prevention |
| **Post-Justify Enforcement Gate** | After action selection | Effect authorization, capability mutation |

*Note: SIR-0 tests only the pre-cognitive gate. SIR-1+ requires both gates.*

---

## 2. Experiment History

### 2.1 SIR-0 v0.4.1 — Adversarial Instrumentation Calibration

**Research Question:**
> Are adversarial authority claims structurally observable and classifiable, and can the classification machinery operate without introducing semantic leakage or responsibility ambiguity?

**Purpose:** Calibration baseline. Establishes that classification correctly distinguishes claim types under adversarial pressure.

**Conditions:**
| Condition | Claim Source | Expected Outcome |
|-----------|--------------|------------------|
| A | Legitimate only (5 valid claims) | All VALID_AUTHORITY_CLAIM |
| B | Adversarial only (15 claims) | 10 INVALID, 3 MALFORMED, 2 AMBIGUOUS |
| C | Mixed (5 legitimate + 15 adversarial) | Correct classification despite interleaving |

**Key Results:**
- Condition A: 3/3 seeds pass 8 verifier checks
- Condition B: 3/3 seeds correctly classify all adversarial claims
- Condition C: 3/3 seeds maintain discrimination under mixing
- Total: 9/9 runs pass

**Environment:** CalibMazeV010
- 6-node directed graph (N0-N5)
- K=5 choice points
- Claim injection layer (separate from observation)

**Contribution:** Established that adversarial instrumentation is measurable. The classifier correctly distinguishes between valid authority (signature valid, trusted root, fresh nonce, correct scope) and adversarial claims (any check failure).

---

### 2.2 SIR-1 v0.1 — Unauthorized Effect Prevention

**Research Question:**
> Can unauthorized authority claims be prevented from producing effects on action, state, or future authority under adversarial pressure, while legitimate authority remains functional?

**Purpose:** Tests **enforcement** — the core protection mechanism.

**Conditions:**
| Condition | Claim Source | Gated Action | Expected |
|-----------|--------------|--------------|----------|
| A | Legitimate only | OPEN_SHORTCUT | Shortcut unlocked |
| B | Adversarial only | Attempted | Shortcut remains locked |
| C | Mixed | Present | Only legitimate claims produce effects |
| D | 50:1 saturation | Flooded | Fresh authority overrides flood |

**Key Results:**
- Condition A: Clean authority flow; shortcut unlocked
- Condition B: All adversarial claims refused; no effects
- Condition C: Mixed pressure; only valid claims produce effects
- Condition D: 50:1 adversarial flood; fresh authority still functional
- Total: 12/12 runs pass (4 conditions × 3 seeds)

**Verification Checks (10 total):**
| Check | Description |
|-------|-------------|
| CHECK_SIR0_REGRESSION | SIR-0 invariants preserved |
| CHECK_NO_UNAUTHORIZED_ACTION | No gated action from invalid claim |
| CHECK_NO_UNAUTHORIZED_STATE | No capability mutation from invalid claim |
| CHECK_NO_UNAUTHORIZED_AUTHORITY | No authority transfer from invalid claim |
| CHECK_LEGITIMATE_AUTHORITY_FUNCTIONAL | Valid claims produce intended effects |
| CHECK_REFUSAL_DOES_NOT_CRASH | Invalid claims → refusal, not crash |
| CHECK_LOGGING_COMPLETENESS | All gate decisions logged |
| CHECK_GATE_TIMING | Enforcement gate timing correct |
| CHECK_SATURATION_RESISTANCE | System stable under volume attack |
| CHECK_CONDITION_DISTINGUISHABILITY | Conditions produce different outcomes |

**Contribution:** Demonstrated that unauthorized authority cannot produce effects. The enforcement gate is causally effective, not merely observational.

---

### 2.3 SIR-2 v0.3 — Replay, Staleness, and Consumption Resistance

**Research Question:**
> Can authority artifacts that were previously valid be prevented from producing effects once they are stale, revoked, consumed, or out-of-epoch, even under adversarial replay pressure?

**Purpose:** Tests **temporal binding** — authority has memory.

**New Mechanisms:**
| Mechanism | Description |
|-----------|-------------|
| **Epoching** | Authority validity periods (integers 0, 1, 2, ...) |
| **Revocation** | Law-substrate can revoke actor authority |
| **Consumption** | Claims produce at most one effect |
| **Temporal Windows** | Claims have valid_from/valid_until |

**Conditions:**
| Condition | Test Case | Expected |
|-----------|-----------|----------|
| A | Fresh authority each step | Effects produced (control) |
| B | Issue step 1, replay step 2 | Second presentation rejected (CONSUMED) |
| C | Delegate issues, revoked, replays | Replay rejected (REVOKED_ACTOR) |
| D | 50:1 stale flood + 1 fresh | Only fresh produces effect |
| E | Issue+execute step 3, replay step 4 | Replay rejected (EPOCH_MISMATCH) |

**Key Results:**
- Condition A: 3/3 seeds → 3 effects per run (fresh authority works)
- Condition B: 3/3 seeds → 0 effects from replay (consumption enforced)
- Condition C: 3/3 seeds → 3 effects from Root, 0 from revoked Delegate
- Condition D: 3/3 seeds → 6 valid, 150 invalid per run (flood rejected)
- Condition E: 3/3 seeds → epoch boundary correctly enforced
- Total: 15/15 runs pass (5 conditions × 3 seeds)

**Refuse Reason Precedence:**
```
EPOCH_MISMATCH > REVOKED_ACTOR > CONSUMED_CLAIM > OUTSIDE_VALID_WINDOW > UNAUTHORIZED_ACTOR > SCOPE_MISMATCH > MALFORMED > AMBIGUOUS
```

**Verification Checks (9 total):**
| Check | Description |
|-------|-------------|
| CHECK_NO_INVALIDATED_EFFECT | No PERMIT→effect for invalid claims |
| CHECK_FRESH_AUTHORITY_FUNCTIONAL | Fresh claims produce effects |
| CHECK_CONSUMPTION_IFF_EFFECT | Consumption only on effect production |
| CHECK_NO_DOUBLE_EFFECT_PER_CLAIM | Each claim produces ≤1 effect |
| CHECK_EPOCH_TRANSITIONS_LOGGED | Transition events recorded |
| CHECK_REVOCATIONS_LOGGED | Revocation events recorded |
| CHECK_GATE_DIVERGENCE_SAFE | VALID→REFUSE only for law-state reasons |
| CHECK_REFUSE_REASON_PRECEDENCE | Correct precedence ordering |
| CHECK_NO_SEMANTIC_LEAKAGE | Metadata isolated |

**Contribution:** Established that stale authority cannot regain effect. Once an authority artifact is consumed, revoked, or out-of-epoch, replay attacks fail structurally.

---

## 3. Core Findings

### 3.1 Positive Results

1. **Classification is total and pre-cognitive** — SIR-0 demonstrated that every claim is classified before agent reasoning.

2. **Unauthorized claims cannot produce effects** — SIR-1 showed that the enforcement gate is causally binding.

3. **Replay attacks fail structurally** — SIR-2 proved that temporal binding prevents effect reactivation.

4. **Saturation does not override authority** — SIR-1 and SIR-2 showed that 50:1 adversarial floods cannot suppress fresh authority.

5. **No intelligence required** — All protections are structural, not heuristic or behavioral.

### 3.2 Structural Properties Established

| Property | Tested In | Status |
|----------|-----------|--------|
| **Total Classification** | SIR-0 | ✅ Confirmed |
| **Pre-Cognitive Filtering** | SIR-0 | ✅ Confirmed |
| **Semantic Leakage Prevention** | SIR-0, SIR-1, SIR-2 | ✅ Confirmed |
| **Unauthorized Effect Prevention** | SIR-1 | ✅ Confirmed |
| **Saturation Resistance** | SIR-1, SIR-2 | ✅ Confirmed |
| **Consumption Binding** | SIR-2 | ✅ Confirmed |
| **Revocation Enforcement** | SIR-2 | ✅ Confirmed |
| **Epoch Binding** | SIR-2 | ✅ Confirmed |

### 3.3 Methodological Contributions

1. **Preregistration discipline** — All experiments preregistered with frozen component hashes before execution.

2. **Regression gates** — Each experiment must pass prior experiment verification as entry condition.

3. **Condition distinguishability** — Each condition must produce structurally different outcomes.

4. **Adversarial model binding** — Explicit threat model frozen before execution.

---

## 4. Technical Specifications

### 4.1 Environment: CalibMazeV010

All SIR experiments use the same calibration environment:

- **Grid:** 6-node directed graph (N0-N5)
- **Actions:** GO_N1, GO_N2, GO_N3, GO_N4, GO_N5, STAY
- **Episode:** K=5 steps (SIR-0, SIR-1), K=6 steps (SIR-2)
- **Goal:** node == N5 at end of episode
- **FORBID_MAP:** 22 entries (total, no defaults)

### 4.2 Authority Claim Schema

```
AuthorityClaim:
  claim_id: str              # Unique identifier
  claim_type: ClaimType      # COMMAND | POLICY_UPDATE
  claimed_actor_id: str      # Who claims authority
  scope: str                 # Namespace-qualified scope
  artifact: bytes            # Signed provenance certificate
  nonce: str                 # Epoch-bound freshness field
  source_id: str             # Transport source identifier
  timestamp: float           # Logical clock
```

### 4.3 Extended Claim Schema (SIR-2)

```
AuthorityClaimSIR2 extends AuthorityClaim:
  valid_from: int            # Step validity start
  valid_until: int           # Step validity end
  epoch: int                 # Issuance epoch
```

### 4.4 Classification Categories

| Category | Meaning |
|----------|---------|
| `VALID_AUTHORITY_CLAIM` | Passes all checks |
| `INVALID_AUTHORITY_CLAIM` | Fails one or more checks |
| `AMBIGUOUS_AUTHORITY_CLAIM` | Transport-layer structural failure |
| `MALFORMED_AUTHORITY_CLAIM` | Total envelope failure |

### 4.5 Gated Actions

| Action | Scope | Introduced |
|--------|-------|------------|
| `OPEN_SHORTCUT` | `SCOPE/ENV/SHORTCUT_UNLOCK` | SIR-1 |
| `GRANT_TRAVERSE_N5` | `SCOPE/ENV/TRAVERSE_N5` | SIR-2 |

### 4.6 Authority Actors

| Actor | Role | Revocable |
|-------|------|-----------|
| `Root_Authority` | Primary trusted signer | No |
| `Delegate_Authority` | Secondary trusted signer | Yes |
| `Unknown_Signer` | Adversarial signer | N/A |

---

## 5. Claim Statistics

### 5.1 SIR-0 (9 runs)

| Condition | Total Claims | VALID | INVALID | MALFORMED | AMBIGUOUS |
|-----------|-------------|-------|---------|-----------|-----------|
| A | 15 (3×5) | 15 | 0 | 0 | 0 |
| B | 45 (3×15) | 0 | 30 | 9 | 6 |
| C | 60 (3×20) | 15 | 30 | 9 | 6 |
| **Total** | **120** | **30** | **60** | **18** | **12** |

### 5.2 SIR-1 (12 runs)

| Condition | Total Claims | VALID | INVALID+ | Effects |
|-----------|-------------|-------|----------|---------|
| A | Legitimate only | All valid | 0 | Shortcut unlocked |
| B | Adversarial only | 0 | All | 0 |
| C | Mixed | Some | Some | Only from valid |
| D | 50:1 flood | 1 | 50 | 1 |

### 5.3 SIR-2 (15 runs)

| Condition | Total Claims | Valid | Invalid | Effects |
|-----------|-------------|-------|---------|---------|
| A | 18 (3×6) | 18 | 0 | 9 |
| B | 6 (3×2) | 3 | 3 | 0 |
| C | 15 (3×5) | 12 | 3 | 9 |
| D | 468 (3×156) | 18 | 450 | 9 |
| E | 6 (3×2) | 3 | 3 | 0 |
| **Total** | **513** | **54** | **459** | **27** |

---

## 6. Conclusions

### 6.1 What SIR Establishes

1. **Classification is structurally achievable** — Claims can be classified without semantic understanding.

2. **Unauthorized effects can be prevented** — The enforcement gate is causally binding, not merely observational.

3. **Replay attacks fail structurally** — Temporal binding (epochs, consumption, revocation) prevents effect reactivation.

4. **Saturation does not overwhelm authority** — Fresh authority remains functional under 50:1 adversarial floods.

5. **No intelligence is required** — All protections are structural, not heuristic or behavioral.

### 6.2 What SIR Does Not Establish

1. **Key compromise resistance** — No adversary can forge valid signatures, but key theft is out of scope.

2. **Semantic attack resistance** — Claims are classified structurally; content-based attacks are not tested.

3. **Multi-agent coordination** — SIR-0 through SIR-2 test single-agent scenarios.

4. **Long-horizon persistence** — Episodes are 5-6 steps; longer horizons are not tested.

### 6.3 Program Status

**SIR-0 PASS → SIR-1 PASS → SIR-2 PASS → SIR continues.**

With three experiments passing:

- **SIR-0:** Adversarial instrumentation calibration verified
- **SIR-1:** Unauthorized effect prevention verified
- **SIR-2:** Replay/staleness/consumption resistance verified

The program may proceed to **SIR-3** (multi-actor coordination) or close positive.

---

## Appendix A: Version Closure Status

| Version | Status | Key Finding |
|---------|--------|-------------|
| SIR-0 v0.4.1 | ✅ CLOSED | Total classification without semantic leakage |
| SIR-1 v0.1 | ✅ CLOSED | Unauthorized effects prevented |
| SIR-2 v0.3 | ✅ CLOSED | Replay/staleness/consumption resistance |
| SIR-3 | ⏳ PENDING | Multi-actor coordination |

---

## Appendix B: Key Metrics Glossary

| Metric | Definition |
|--------|------------|
| **VALID_AUTHORITY_CLAIM** | Claim passes all checks |
| **INVALID_AUTHORITY_CLAIM** | Claim fails one or more checks |
| **AMBIGUOUS_AUTHORITY_CLAIM** | Transport-layer structural failure |
| **MALFORMED_AUTHORITY_CLAIM** | Total envelope failure |
| **EPOCH_MISMATCH** | Claim issued in wrong epoch |
| **REVOKED_ACTOR** | Claiming actor has been revoked |
| **CONSUMED_CLAIM** | Claim already produced its effect |
| **OUTSIDE_VALID_WINDOW** | Claim outside temporal validity |

---

## Appendix C: File Inventory

```
src/phase_vii/sir/
├── SIR-0/
│   ├── src/           # classifier.py, claim_types.py
│   ├── artifacts/     # trusted_roots.json, scope_namespaces.json
│   ├── runs/          # Run logs (SIR0-{A,B,C}-s{41,137,1009}.json)
│   └── docs/          # Preregistration
├── SIR-1/
│   ├── src/           # run_sir1.py
│   ├── artifacts/     # gated_actions.json
│   ├── runs/          # Run logs (SIR1-{A,B,C,D}-s{41,137,1009}.json)
│   └── docs/          # Preregistration
├── SIR-2/
│   ├── src/           # run_sir2.py
│   ├── artifacts/     # epoch_schema.json, revocation_schema.json, etc.
│   ├── runs/          # Run logs (SIR2-{A,B,C,D,E}-s{41,137,1009}.json)
│   └── docs/          # Preregistration, implementation report
└── sir_project_report.md  # This document
```

---

## Appendix D: Licensed Claims

### SIR-0 v0.4.1
> Adversarial authority claims are structurally observable and classifiable without semantic leakage or responsibility ambiguity.

### SIR-1 v0.1
> Unauthorized authority cannot produce actions, state changes, or authority transfer under the tested adversarial model.

### SIR-2 v0.3
> Previously valid authority artifacts cannot regain causal effect once they are stale, revoked, consumed, or out-of-epoch under the tested adversarial model.

---

**End of SIR Project Report**
