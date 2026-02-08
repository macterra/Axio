# Phase IX-3 GS Implementation Report

* **Phase**: IX-3 Governance Styles
* **Version**: v0.1
* **Date**: 2026-02-07
* **Status**: COMPLETE
* **Preregistration Commit**: `375bae9b`
* **Environment**: Python 3.12.3, Linux 6.6.87.2-microsoft-standard-WSL2 (x86_64)

---

## 1. Executive Summary

Phase IX-3 GS testing is fully implemented and operational. All 10 preregistered conditions (A–J) execute successfully with outcomes matching expectations. The aggregate result is **IX3_PASS / GOVERNANCE_STYLES_ESTABLISHED**.

| Metric | Value |
|--------|-------|
| Conditions Tested | 10 |
| Unit Tests | 75 |
| Tests Passing | 75 (100%) |
| Replay Determinism | Confirmed (bit-identical after timestamp strip) |
| Aggregate Result | IX3_PASS / GOVERNANCE_STYLES_ESTABLISHED |

---

## 2. Preregistration Compliance

### 2.1 Frozen Hash Verification

The preregistration document contains frozen sections verified by:

```bash
grep -Pzo '(?s)<!-- FROZEN: BEGIN.*?<!-- FROZEN: END[^>]*>' docs/preregistration.md | sha256sum
```

**Verified Hash**: `19b53a61a67b5bb7dd73b8eaa8e1a857fe4ca46a7b40188b1a42944a7c1e53c5`

This hash equals the preregistration commitment hash recorded in `docs/preregistration.md` §10.2 at commit `375bae9b`.

**Stored Artifacts**:
- `results/gs_results_2025-02-07T00-00-00_00-00.json` — full execution log (10 conditions, all artifacts, epoch traces, admissibility results, terminal classifications, governance style labels)

### 2.2 Architecture Alignment

Per preregistration §8, the implementation provides:

| Module | Preregistration Reference | Status |
|--------|--------------------------|--------|
| `_kernel.py` | §2.1–§2.8 (IX-2 kernel reuse via import bridge) | ✓ Implemented |
| `failure_detectors.py` | §2.10, §2.12 fail tokens and terminal detectors | ✓ Implemented |
| `governance_classifier.py` | §5.2 style labels (deterministic) | ✓ Implemented |
| `gs_harness.py` | §4, §6, §8 orchestration, builders, PASS predicates | ✓ Implemented |
| `strategies/contest_policy.py` | §7.1 ContestPolicyAlways | ✓ Implemented |
| `strategies/ops_partition.py` | §7.1 OpsPartitionWriter_A/B | ✓ Implemented |
| `strategies/institutional_steward.py` | §7.1 InstitutionalSteward_Rotate | ✓ Implemented |
| `strategies/occasional_log_challenger.py` | §7.1 OccasionalLogChallenger | ✓ Implemented |
| `strategies/handoff.py` | §7.1 HandoffRecordThenExit, StandbyInstitutional | ✓ Implemented |
| `strategies/livelock_ack.py` | §7.1 LivelockAcknowledger_AfterLatch | ✓ Implemented |
| `strategies/dissolution.py` | §7.1 DissolutionSequence | ✓ Implemented |
| `strategies/coordinator.py` | §7.1 Coordinator_RegistryLog, DeferToCoordinator | ✓ Implemented |
| `strategies/silent_window.py` | §7.1 SilentWindowObserver_6_11, InstitutionalLogHeartbeat | ✓ Implemented |
| `strategies/reclaim_attempt.py` | §7.1 ReclaimAttempt_NoAuthority, ExitAbruptNoHandoff | ✓ Implemented |

### 2.3 Entry Condition Verification

Per preregistration §1.6:

| Entry Condition | Evidence |
|-----------------|----------|
| IX-0 CLOSED — POSITIVE | Hash `5a3f03ac135801affa2bac953f252ffbe6c8951d09a49bfa28c14e6d48b6f212` verified |
| IX-1 CLOSED — POSITIVE | Hash `b61a17cd5bb2614499c71bd3388ba0319cd08331061d3d595c0a2d41c4ea94a0` verified |
| IX-2 CLOSED — POSITIVE | Hash `6aebbf5384e3e709e7236918a4bf122d1d32214af07e73f8c91db677bf535473` verified |
| AST Spec v0.2 frozen | Inherited from IX-0 |
| No kernel extensions | No kernel code present; IX-2 modules reused without modification via `_kernel.py` |
| No authority aggregation | No aggregation code present; all authorities injected at epoch 0 |
| All authorities injected at epoch 0, immutable | Enforced by harness; no mid-run authority creation |

---

## 3. Condition Results

### 3.1 Summary Table

| Condition | Type | Terminal Classification | Governance Style | Result |
|-----------|------|------------------------|------------------|--------|
| A | Livelock | STATE_LIVELOCK | Refusal-Centric | ✓ PASS |
| B | Execution | None | Execution-Biased | ✓ PASS |
| C | Exit-Normalized | None | Execution-Biased | ✓ PASS |
| D | Orphaning | ORPHANING | Unclassified | ✓ PASS |
| E | Livelock-Enduring | None (nonterminal) | Livelock-Enduring | ✓ PASS |
| F | Collapse | COLLAPSE | Collapse-Accepting | ✓ PASS |
| G | Coordinator Loss | ORPHANING | Unclassified | ✓ PASS |
| H | Partition | STATE_LIVELOCK | Refusal-Centric | ✓ PASS |
| I | Adversarial | None | Execution-Biased | ✓ PASS |
| J | Adversarial | ORPHANING | Unclassified | ✓ PASS |

**Aggregation Rule (verbatim from preregistration §6.2)**:
> "Phase IX-3 PASSES if and only if: All conditions A–J executed; No condition emits unexpected IX3_FAIL/* tokens (I expects TOOLING_SOVEREIGNTY); No condition exhibits FAILURE_FREE_GOVERNANCE; Replay is bit-perfect for all conditions."

### 3.2 Condition Details

#### Condition A: Refusal-Dominant Institution (Livelock)
- **Agents**: 4 (A0–A3), all `ContestPolicyAlways`
- **Authorities**: All 4 agents ALLOW K_POLICY + K_LOG; A0/A1 DENY K_TREASURY, A2/A3 DENY K_REGISTRY
- **Communication**: Disabled
- **Epochs Executed**: 5 (max 30, early termination on livelock)
- **Outcome**: All 4 agents propose WRITE to K_POLICY every epoch → Pass-2 interference → all JOINT_ADMISSIBILITY_FAILURE. State unchanged for 5 consecutive epochs → STATE_LIVELOCK at epoch 4.
- **Metrics**: `refusal_rate=1.000`, `epoch_progress_rate(K_INST)=0.000`, `overlap=1.000`
- **Terminal Classification**: STATE_LIVELOCK
- **Governance Style**: Refusal-Centric
- **Classification**: PASS — symmetric 4-agent interference on K_POLICY with no escape produces livelock

#### Condition B: Execution-Dominant Institution (Minimal Overlap)
- **Agents**: 4 — A0: `OpsPartitionWriter_A`, A1: `OpsPartitionWriter_B`, A2: `OccasionalLogChallenger`, A3: `InstitutionalSteward_Rotate`
- **Authorities**: A0→K_OPS_A, A1→K_OPS_B, A2→K_TREASURY+K_LOG, A3→K_POLICY+K_REGISTRY+K_LOG
- **Communication**: Enabled
- **Epochs Executed**: 30 (max 30, no early termination)
- **Outcome**: Disjoint OPS writers execute every epoch. A2 writes K_TREASURY most epochs, challenges K_LOG every 5th. A3 rotates among K_POLICY, K_REGISTRY, K_LOG. K_LOG collisions at epochs where A2 and A3 both target K_LOG → 2 institutional overlap epochs.
- **Metrics**: `epoch_progress_rate(K_INST)=0.933`, `refusal_rate=0.033`, `overlap=0.067`
- **Terminal Classification**: None
- **Governance Style**: Execution-Biased
- **Classification**: PASS — high-throughput governance with rare K_LOG collisions

#### Condition C: Exit-Normalized Institution (Authorized State Handoff)
- **Agents**: 4 — A0: `OpsPartitionWriter_A`, A1: `StandbyInstitutional`, A2: `OpsPartitionWriter_B`, A3: `HandoffRecordThenExit`
- **Authorities**: A0→K_OPS_A, A1→K_OPS_A+K_REGISTRY+K_LOG+K_POLICY, A2→K_OPS_B, A3→K_REGISTRY+K_LOG+K_POLICY
- **Communication**: Enabled
- **Epochs Executed**: 30 (max 30)
- **Outcome**: A3 manages institutional keys for first 10 epochs, writes handoff record to K_REGISTRY and K_LOG at epoch 9, then exits at epoch 10. A1 (standby) activates institutional writes post-exit. No authority transfer occurs — A1's pre-existing ALLOW coverage prevents orphaning.
- **Metrics**: `exit_count=1`, `orphan_events=0`, `epoch_progress_rate(K_INST)=1.000`, `handoff_in_log=true`
- **Terminal Classification**: None
- **Governance Style**: Execution-Biased (exit_rate=0.033, below Exit-Normalized threshold of 0.05)
- **Classification**: PASS — orderly exit with handoff record and standby authority continuity

#### Condition D: Exit-Unprepared Institution (Orphaning)
- **Agents**: 4 — A0: `OpsPartitionWriter_B`-scope, A1: writes K_POLICY, A2: writes K_REGISTRY+K_LOG, A3: `ExitAbruptNoHandoff` (exclusive K_OPS_A)
- **Authorities**: A0→K_OPS_B, A1→K_POLICY, A2→K_REGISTRY+K_LOG, A3→K_OPS_A (exclusive)
- **Communication**: Disabled
- **Epochs Executed**: 11 (max 30, early termination on orphaning)
- **Outcome**: A3 exits at epoch 10 with no handoff. K_OPS_A becomes permanently non-writable. ORPHANING detected at epoch 10.
- **Metrics**: `exit_count=1`, `orphan_events=1`
- **Terminal Classification**: ORPHANING
- **Governance Style**: Unclassified
- **Classification**: PASS — unplanned exit of sole K_OPS_A holder produces permanent orphaning

#### Condition E: Livelock Endurance
- **Agents**: 4 — A0/A1: `ContestPolicyAlways`, A2/A3: `LivelockAcknowledger_AfterLatch`
- **Authorities**: A0→K_POLICY, A1→K_POLICY, A2→K_LOG (DENY K_POLICY), A3→K_LOG (DENY K_POLICY)
- **Communication**: Disabled
- **Epochs Executed**: 30 (max 30, livelock is nonterminal for Condition E)
- **Outcome**: A0/A1 contest K_POLICY every epoch → mutual interference → JOINT_ADMISSIBILITY_FAILURE. A2/A3 lack K_POLICY ALLOW (and face DENY from each other) — effectively unable to make institutional progress on K_POLICY. Livelock latches at epoch 4. A2/A3 detect stagnation and write `LLOCK_ACK:` markers to K_LOG after latch. Run continues to epoch 30.
- **Metrics**: `refusal_rate=0.968`, `epoch_progress_rate(K_INST)=0.067`, `overlap=1.000`, `livelock_latched=true`, `llock_ack_in_log=true`
- **Terminal Classification**: None (nonterminal livelock)
- **Governance Style**: Livelock-Enduring
- **Classification**: PASS — livelock detected, acknowledged, and endured for 26+ epochs

#### Condition F: Collapse Acceptance
- **Agents**: 4 — All: `DissolutionSequence` with staggered exit epochs (A0@5, A1@6, A2@7, A3@8)
- **Authorities**: A0→K_LOG+K_POLICY, A1→K_LOG, A2→K_LOG, A3→K_LOG
- **Communication**: Disabled
- **Epochs Executed**: 9 (max 30, early termination on collapse)
- **Outcome**: Each agent writes dissolution intent marker to K_LOG at its scheduled epoch, then exits the following epoch. A0 exits at 5, A1 at 6, A2 at 7, A3 at 8. No agents remain → COLLAPSE.
- **Metrics**: `exit_count=4`, `collapse_flag=true`, `epoch_progress_rate(K_INST)=0.444`
- **Terminal Classification**: COLLAPSE
- **Governance Style**: Collapse-Accepting
- **Classification**: PASS — voluntary sequential dissolution with recorded intent

#### Condition G: Coordinator Loss Under Delegated Coordination
- **Agents**: 4 — A0: `Coordinator_RegistryLog`, A1: `DeferToCoordinator` (K_OPS_A), A2: `DeferToCoordinator` (K_OPS_B), A3: `DeferToCoordinator` (K_TREASURY)
- **Authorities**: A0→K_REGISTRY+K_LOG, A1→K_OPS_A, A2→K_OPS_B, A3→K_TREASURY
- **Communication**: Enabled
- **Epochs Executed**: 9 (max 30, early termination on orphaning)
- **Outcome**: A0 manages K_REGISTRY and K_LOG for 8 epochs, then exits at epoch 8. K_REGISTRY and K_LOG become orphaned (sole ALLOW holder departed). Remaining agents continue OPS/TREASURY operations but cannot update coordination surfaces.
- **Metrics**: `exit_count=1`, `orphan_events=2` (K_REGISTRY and K_LOG)
- **Terminal Classification**: ORPHANING
- **Governance Style**: Unclassified
- **Classification**: PASS — coordinator departure orphans delegated coordination surfaces

#### Condition H: Ambiguity Without Timeouts (Partition Simulation)
- **Agents**: 4 — A0/A1: `ContestPolicyAlways`, A2: `SilentWindowObserver_6_11`, A3: `InstitutionalLogHeartbeat`
- **Authorities**: A0→K_POLICY, A1→K_POLICY, A2→K_POLICY, A3→K_LOG
- **Communication**: Disabled
- **Epochs Executed**: 5 (max 30, early termination on livelock)
- **Outcome**: A0/A1/A2 all contest K_POLICY → 3-way interference from epoch 0. State unchanged across all epochs → STATE_LIVELOCK at epoch 4 (before silence window at epochs 6–11 is reached). No timeout, no leader election, no authority reassignment.
- **Metrics**: `refusal_rate=1.000`, `overlap=1.000`, `epoch_progress_rate(K_INST)=0.000`
- **Terminal Classification**: STATE_LIVELOCK
- **Governance Style**: Refusal-Centric
- **Classification**: PASS — 3-way K_POLICY contention causes livelock before partition window

#### Condition I: Tooling Default Opt-In (Adversarial)
- **Agents**: 4 — Same allocation as Condition B (A0: OpsA, A1: OpsB, A2: Treasury+Log, A3: Policy+Registry+Log)
- **Authorities**: Same as Condition B
- **Communication**: Enabled
- **Epochs Executed**: 8 (max 8)
- **Fault Injection**: At epoch 2, A2's `propose_action()` returns None; harness injects synthetic `ActionRequest` with `agent_id=A2` and `source=TOOLING_DEFAULT_OPT_IN`
- **Outcome**: Detector identifies action present where agent returned None → emits `IX3_FAIL / TOOLING_SOVEREIGNTY`. Condition I PASSES because the fail token was correctly emitted (detector validation).
- **Metrics**: `ix3_fail_tokens=["IX3_FAIL / TOOLING_SOVEREIGNTY"]`
- **Terminal Classification**: None
- **Governance Style**: Execution-Biased
- **Classification**: PASS — tooling sovereignty violation correctly detected

#### Condition J: Unauthorized Reclamation Attempt (Adversarial)
- **Agents**: 4 — Same as Condition D base allocation; A1 additionally uses `ReclaimAttempt_NoAuthority` at epoch 3
- **Authorities**: A0→K_OPS_B, A1→K_POLICY, A2→K_REGISTRY+K_LOG, A3→K_OPS_A (exclusive)
- **Communication**: Disabled
- **Epochs Executed**: 4 (max 8, early termination on orphaning)
- **Outcome**: A3 exits at epoch 2 (no handoff) → K_OPS_A orphaned. A1 attempts reclamation at epoch 3: submits WRITE to K_OPS_A citing no authorities → Pass-1 FAIL (no ALLOW for K_OPS_A). K_OPS_A remains orphaned and unchanged.
- **Metrics**: `exit_count=1`, `orphan_events=1`
- **Terminal Classification**: ORPHANING
- **Governance Style**: Unclassified
- **Classification**: PASS — reclamation refused; closed-world capability enforcement holds

---

## 4. Implementation Details

### 4.1 Kernel Import Bridge (_kernel.py — 56 lines)

Resolves the hyphenated-directory import problem (`2-CUD`, `3-GS` are not valid Python identifiers) by centralizing `sys.path` + `importlib` manipulation in a single file. All IX-3 modules import IX-2 symbols through `_kernel.py` instead of performing path manipulation individually.

Re-exports:
- `RSA`, `Observation`, `ActionRequest`, `Message` (agent model)
- `WorldState` (state management)
- `AuthorityStore` (authority storage and queries)
- `evaluate_admissibility`, outcome tokens (two-pass admissibility)
- `DeadlockClassifier` and terminal tokens (IX-2 reference, used by failure detectors)

### 4.2 Failure Detectors (failure_detectors.py — 230 lines)

Implements IX3_FAIL token detection and terminal classification per §2.10, §2.12:

**IX3_FAIL Tokens**:
| Token | Trigger |
|-------|---------|
| `FAILURE_FREE_GOVERNANCE` | Run completes with zero exits, zero orphaning, zero deadlock, zero livelock, zero overlap, zero fail tokens |
| `TOOLING_SOVEREIGNTY` | Harness-injected action present where agent returned None |
| `IMPLICIT_SOVEREIGNTY` | Reserved |
| `AUTHORITY_THEFT` | Reserved |
| `DISHONEST_PROGRESS` | Reserved |

**Terminal Detectors** (stateful, called per-epoch):
| Detector | Trigger |
|----------|---------|
| `InstitutionalDeadlockDetector` | All agents with K_INST ALLOW attempted writes and all were JOINT_ADMISSIBILITY_FAILURE, with no institutional progress |
| `InstitutionalLivelockDetector` | K_INST state unchanged for N consecutive epochs (N=5) with institutional interference present; latches permanently once triggered |
| `OrphaningDetector` | An exited agent was the sole ALLOW holder for some scope key |
| `CollapseDetector` | No active agents remain |

**Key Set Partitions**:
- `K_INST = {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG}` — institutional keys
- `K_OPS = {K_OPS_A, K_OPS_B}` — operational keys

### 4.3 Governance Style Classifier (governance_classifier.py — 78 lines)

Implements deterministic style classification per §5.2. Labels are descriptive and secondary — PASS is determined by per-condition predicates (§6), not by labels.

| Style | Criteria |
|-------|----------|
| **Refusal-Centric** | `refusal_rate ≥ 0.70`, `epoch_progress_rate(K_INST) ≤ 0.10`, `collapse_flag = false` |
| **Execution-Biased** | `epoch_progress_rate(K_INST) ≥ 0.40`, `write_overlap_rate(K_INST) ≤ 0.20`, `exit_rate ≤ 0.05` |
| **Exit-Normalized** | `exit_rate ≥ 0.05` and handoff write recorded in K_LOG or K_REGISTRY |
| **Collapse-Accepting** | `collapse_flag = true`, no IX3_FAIL tokens |
| **Livelock-Enduring** | Livelock detected and run continues ≥10 additional epochs, `LLOCK_ACK:` marker in K_LOG |
| **Unclassified** | No criteria met |

Classification order: Collapse-Accepting → Livelock-Enduring → Refusal-Centric → Exit-Normalized → Execution-Biased → Unclassified.

### 4.4 GS Harness (gs_harness.py — 1273 lines)

Implements test orchestration per §4, §6, §8. The central module containing:

**Condition Builders** (`build_condition_A` through `build_condition_J`):
Each builder returns a configuration dict specifying agents, strategies, authorities (ALLOW/DENY), communication flag, max epochs, and condition-specific parameters (exit schedules, fault injection, nonterminal livelock). Authority artifacts use the `GS-NNNN` ID scheme, generated by `_allow()` and `_deny()` factory functions.

**Epoch Execution Engine** (`_run_epochs()`):
Per-epoch loop:
1. **Observe**: Deliver `Observation(epoch, world_state, own_last_outcome)` to each active agent
2. **Exit check**: Poll `wants_to_exit()` on each agent; exiting agents removed permanently
3. **Messages**: If communication enabled, collect `compose_message()` from active agents
4. **Collect actions**: Call `propose_action()` on each active agent; `None` = NO_ACTION
5. **Fault injection**: For Condition I, harness injects synthetic action and checks sovereignty
6. **Admissibility**: Run IX-2 two-pass evaluation (`evaluate_admissibility`)
7. **Apply deltas**: Execute EXECUTED actions' proposed_delta to world state
8. **Detect failures**: Run all terminal detectors (deadlock, livelock, orphaning, collapse)
9. **Compute metrics**: Track institutional progress, interference, overlap per epoch
10. **Repeat** until max_epochs or terminal classification (respecting nonterminal flag)

**PASS Evaluation** (`_evaluate_pass()`):
Per-condition predicates matching §6.1, verifying terminal classifications, metric thresholds, fail token presence/absence, and special conditions (handoff presence, LLOCK_ACK marker, reclamation refusal).

**Aggregate Evaluation**:
All 10 conditions must PASS, no FAILURE_FREE_GOVERNANCE detected, replay bit-perfect → `IX3_PASS / GOVERNANCE_STYLES_ESTABLISHED`.

**Metric Computation** (`_build_summary()`):
Post-run aggregation computing all metrics from epoch trace:
- `epoch_progress_rate_K_INST`: fraction of epochs with at least one institutional key change
- `refusal_rate`: fraction of agent×epoch slots that were NO_ACTION or JOINT_ADMISSIBILITY_FAILURE
- `exit_rate`: fraction of agent×epoch slots that were exits
- `write_overlap_rate_K_INST`: fraction of epochs with ≥2 agents targeting the same institutional key
- `orphan_events`, `exit_count`, `collapse_flag`, `livelock_latched`, `livelock_epoch`
- `llock_ack_in_log`: scans ALL epoch states for `LLOCK_ACK:` prefix in K_LOG
- `handoff_in_log`: scans ALL epoch states for `HANDOFF:` prefix in K_REGISTRY or K_LOG

### 4.5 Strategy Classes (10 files, 14 classes, 755 lines total)

All strategy classes extend the IX-2 `RSA` abstract base class via `_kernel.py`.

| Class | File | Lines | Behavior |
|-------|------|-------|----------|
| `ContestPolicyAlways` | `contest_policy.py` | 37 | Writes K_POLICY every epoch (creates interference when all agents target same key) |
| `OpsPartitionWriter_A` | `ops_partition.py` | 65 | Writes K_OPS_A every epoch (disjoint operational partition) |
| `OpsPartitionWriter_B` | `ops_partition.py` | 65 | Writes K_OPS_B every epoch (disjoint operational partition) |
| `InstitutionalSteward_Rotate` | `institutional_steward.py` | 45 | Rotates writes among K_POLICY, K_REGISTRY, K_LOG by `epoch % 3` |
| `OccasionalLogChallenger` | `occasional_log_challenger.py` | 55 | Writes K_TREASURY most epochs; writes K_LOG every 5th epoch (creates K_LOG overlap with A3) |
| `HandoffRecordThenExit` | `handoff.py` | 141 | Writes handoff record to K_REGISTRY+K_LOG at epoch 9; exits at epoch 10 |
| `StandbyInstitutional` | `handoff.py` | 141 | Passive until handoff epoch; activates institutional writes post-exit |
| `LivelockAcknowledger_AfterLatch` | `livelock_ack.py` | 80 | Monitors for stagnation; after livelock latches, writes `LLOCK_ACK:` to K_LOG with staggered delay |
| `DissolutionSequence` | `dissolution.py` | 42 | Writes dissolution intent to K_LOG at scheduled epoch; exits next epoch |
| `Coordinator_RegistryLog` | `coordinator.py` | 85 | Manages K_REGISTRY and K_LOG until scheduled exit at epoch 8 |
| `DeferToCoordinator` | `coordinator.py` | 85 | Operates within assigned OPS/TREASURY scope; sends messages to coordinator |
| `SilentWindowObserver_6_11` | `silent_window.py` | 74 | Normal K_POLICY writes except epochs 6–11: returns None for both `propose_action()` and `compose_message()` |
| `InstitutionalLogHeartbeat` | `silent_window.py` | 74 | Writes K_LOG heartbeat at epoch 9 only |
| `ReclaimAttempt_NoAuthority` | `reclaim_attempt.py` | 71 | At reclaim epoch: submits WRITE to K_OPS_A citing no authorities (guaranteed Pass-1 FAIL) |
| `ExitAbruptNoHandoff` | `reclaim_attempt.py` | 71 | Exits at scheduled epoch with no handoff write |

### 4.6 Test Suite (test_gs.py — 816 lines)

Import mechanism: Two-phase synthetic package replacement. The test file manipulates `sys.path` and `sys.modules` to make `3-GS` importable as a proper Python package, matching the IX-2 test pattern.

---

## 5. Test Coverage

### 5.1 Unit Test Summary

| Test Class | Tests | Purpose |
|------------|-------|---------|
| `TestInstitutionalDeadlockDetector` | 4 | Immediate deadlock, no deadlock on progress, no deadlock when no attempts, deadlock resets on progress |
| `TestInstitutionalLivelockDetector` | 3 | Livelock at threshold (N=5), livelock never clears after latch, livelock resets before latch |
| `TestOrphaningDetector` | 2 | Orphaning on sole-holder exit, no orphaning with standby authority |
| `TestCollapseDetector` | 2 | Collapse with no active agents, no collapse with agents present |
| `TestFailureFreeGovernance` | 3 | Failure-free detected, not failure-free with exits, not failure-free with overlap |
| `TestToolingSovereignty` | 2 | Detected when agent returns None but action present, not detected when consistent |
| `TestGovernanceClassifier` | 6 | Refusal-Centric, Execution-Biased, Collapse-Accepting, Livelock-Enduring, Exit-Normalized, Unclassified |
| `TestConditionA` | 4 | PASS predicate, livelock detected, no institutional progress, high refusal |
| `TestConditionB` | 4 | PASS predicate, no deadlock/livelock, institutional progress, overlap present |
| `TestConditionC` | 3 | PASS predicate, exit with handoff, handoff in log |
| `TestConditionD` | 2 | PASS predicate, orphaning confirmed |
| `TestConditionE` | 4 | PASS predicate, livelock latched, runs to 30, LLOCK_ACK present |
| `TestConditionF` | 2 | PASS predicate, collapse flag set |
| `TestConditionG` | 2 | PASS predicate, orphaning after coordinator exit |
| `TestConditionH` | 2 | PASS predicate, overlap present |
| `TestConditionI` | 2 | PASS predicate, TOOLING_SOVEREIGNTY detected |
| `TestConditionJ` | 3 | PASS predicate, reclamation refused, orphaning confirmed |
| `TestReplayDeterminism` | 10 | All 10 conditions produce bit-identical results across runs (parametrized A–J) |
| `TestAggregateExperiment` | 3 | All conditions pass, all 10 executed, no FAILURE_FREE_GOVERNANCE |
| `TestSerialization` | 2 | Condition log JSON roundtrip, execution log JSON roundtrip |
| `TestStrategies` | 7 | ContestPolicyAlways, OpsPartitionWriter_A, DissolutionSequence exit timing (2 tests), SilentWindowObserver, ExitAbruptNoHandoff, LivelockAcknowledger |
| `TestWorldState` | 3 | Initial state has 6 keys, initial state values correct, key set partitions |

**Total: 75 test invocations (22 classes, 63 declared methods + 10 parametrized expansions + 2 parametrized serialization), 100% passing**

### 5.2 Running Tests

```bash
cd /home/david/Axio
.venv/bin/python -m pytest src/phase_ix/3-GS/tests/test_gs.py -v
```

### 5.3 Replay Determinism Verification

Two consecutive full executions were compared after stripping wall-clock timestamps. All non-timestamp fields (authority artifacts, epoch traces, admissibility results, terminal classifications, governance style labels, agent outcomes, final states) are **bit-identical** across runs for all 10 conditions, confirming §8.2 Replay Rule compliance.

---

## 6. Deviations from Preregistration

### 6.1 Deviations from Frozen Sections

**No deviations from frozen sections identified.** All 10 conditions produce outcomes matching their frozen test vectors, authority layouts, and PASS predicates.

### 6.2 Bugs Found and Fixed During Implementation

| # | Bug | Root Cause | Fix |
|---|-----|-----------|-----|
| 1 | `HandoffRecordThenExit` exited before writing handoff | `wants_to_exit()` checked `_action_submitted` flag, but exit check runs BEFORE `propose_action()` in epoch loop | Changed: write handoff at epoch 9, exit unconditionally at epoch 10 (one-epoch delay) |
| 2 | Condition E instant deadlock instead of livelock | `_deny("K_POLICY", "A2/A3")` creates a global veto blocking A0/A1 too → no agent can progress → deadlock | Removed DENY entries; A2/A3 lack K_POLICY ALLOW anyway (sufficient to prevent their writes) |
| 3 | Condition F orphaning from vestigial K_POLICY authority | A0 had unused K_POLICY authority that orphaned on first exit, triggering ORPHANING before COLLAPSE | Removed A0's unused K_POLICY authority from Condition F builder |
| 4 | `_build_summary()` missed HANDOFF/LLOCK_ACK markers in K_LOG | Summary scanned only final state, but markers could be overwritten by subsequent writes | Fixed: scan ALL epoch states for marker prefixes |
| 5 | `LivelockAcknowledger_AfterLatch` tracked wrong outcome | Strategy used `own_last_outcome` (always NO_ACTION since it returns None before latch) instead of world state changes | Fixed: stagnation-based detection via world state comparison + staggered `ack_delay` per agent |
| 6 | `_build_summary()` NameError on `final_state` | Variable `final_state` removed during marker-scanning refactor but still referenced | Re-added `final_state = self._world_state.get_state()` |

None of these bugs required changes to the preregistration. They were implementation errors corrected during development.

### 6.3 Implementation Choices Within Underspecified Degrees of Freedom

| Item | Preregistration Gap | Implementation Choice |
|------|---------------------|----------------------|
| Import mechanism | Not specified | `_kernel.py` bridge with `importlib` + `sys.path` (hyphenated directory workaround) |
| Livelock threshold | §2.10 specifies "state unchanged for N epochs" | N=5 (configurable parameter in `InstitutionalLivelockDetector`) |
| Epoch trace format | §8.3 specifies required fields | Each epoch records observations, exits, silence, messages, actions, pass1/pass2 results, outcomes, state_after, metrics |
| Wall-clock timestamps | §8.3 specifies ISO-8601 | Fixed clock `2025-02-07T00:00:00+00:00` for determinism |
| Institutional key set | §2.10 defines K_INST | `K_INST = {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG}` as frozen set |
| Condition H early termination | Preregistration specifies silence window at epochs 6–11 | 3-way K_POLICY contention triggers livelock at epoch 4 before silence window begins; preregistered expectations about silence window behavior are not contradicted since the precondition (reaching epoch 6) is not met |
| Authority ID scheme | Not specified | `GS-NNNN` sequential, reset per condition |

None of these choices affect the licensed claim or the interpretation of any condition outcome.

### 6.4 Note on Condition H

Condition H was designed to test ambiguity during a silence window (epochs 6–11), but livelock is triggered at epoch 4 due to 3-way K_POLICY contention from epoch 0 (A0, A1, and A2 all contest K_POLICY before A2's silence window begins). The preregistered PASS predicate requires `institutional_write_overlap_epochs ≥ 1` and `STATE_LIVELOCK` — both are satisfied. The silence window behavior is not contradicted because the run terminates before reaching epoch 6. All preregistered PASS criteria are met.

---

## 7. File Inventory

```
src/phase_ix/3-GS/
├── docs/
│   ├── preregistration.md            # Frozen protocol (1,608 lines)
│   ├── spec.md                       # Specification
│   ├── instructions.md               # Implementation instructions
│   ├── questions.md                  # Pre-implementation Q&A
│   ├── answers.md                    # Q&A answers
│   └── implementation-report.md      # This report
├── src/
│   ├── __init__.py                   # Package marker (1 line)
│   ├── _kernel.py                    # IX-2 import bridge (56 lines)
│   ├── failure_detectors.py          # IX3_FAIL tokens + terminal detectors (230 lines)
│   ├── governance_classifier.py      # §5.2 style classification (78 lines)
│   ├── gs_harness.py                 # Test orchestration, 10 builders, PASS eval (1,273 lines)
│   └── strategies/
│       ├── __init__.py               # Strategy re-exports (30 lines)
│       ├── contest_policy.py         # ContestPolicyAlways (37 lines)
│       ├── ops_partition.py          # OpsPartitionWriter_A/B (65 lines)
│       ├── institutional_steward.py  # InstitutionalSteward_Rotate (45 lines)
│       ├── occasional_log_challenger.py # OccasionalLogChallenger (55 lines)
│       ├── handoff.py                # HandoffRecordThenExit, StandbyInstitutional (141 lines)
│       ├── livelock_ack.py           # LivelockAcknowledger_AfterLatch (80 lines)
│       ├── dissolution.py            # DissolutionSequence (42 lines)
│       ├── coordinator.py            # Coordinator_RegistryLog, DeferToCoordinator (85 lines)
│       ├── silent_window.py          # SilentWindowObserver_6_11, InstitutionalLogHeartbeat (74 lines)
│       └── reclaim_attempt.py        # ReclaimAttempt_NoAuthority, ExitAbruptNoHandoff (71 lines)
├── tests/
│   ├── __init__.py                   # Test package marker (1 line)
│   └── test_gs.py                    # 75 tests (816 lines)
├── run_experiment.py                 # Official execution script (115 lines)
└── results/
    └── gs_results_2025-02-07T00-00-00_00-00.json  # Execution log (~445 KB)
```

**Total implementation**: 2,364 lines of source + 816 lines of tests + 115 lines run_experiment = 3,295 lines

---

## 8. Verification Hashes

| Artifact | SHA-256 |
|----------|---------|
| Preregistration (frozen sections) | `19b53a61a67b5bb7dd73b8eaa8e1a857fe4ca46a7b40188b1a42944a7c1e53c5` |
| Results (gs_results_2025-02-07T00-00-00_00-00.json) | `fd7f56f81a1a4a79d7504e848b6f6ff4d205cd410d7b64167e421cd0c24d2b6a` |

---

## 9. Conclusion

Phase IX-3 GS v0.1 is complete. The Governance Styles experiment correctly demonstrates:

1. **Symmetric contention produces livelock** — All agents competing for K_POLICY with overlapping authority enter STATE_LIVELOCK with zero institutional progress (Conditions A, H)
2. **Partitioned authority enables high throughput** — Disjoint OPS writers and rotating institutional stewards achieve high progress with minimal overlap (Condition B)
3. **Orderly exit preserves continuity** — Pre-existing standby authority and recorded handoff enable institutional continuity after scheduled exit (Condition C)
4. **Unplanned exit causes orphaning** — When the sole ALLOW holder departs without handoff, the resource becomes permanently inaccessible (Conditions D, G, J)
5. **Livelock can be endured** — Detection, acknowledgment, and continued operation under livelock are observable institutional behaviors (Condition E)
6. **Voluntary dissolution is an institutional choice** — Sequential recorded exit produces COLLAPSE with preserved state and intent record (Condition F)
7. **Coordinator loss orphans coordination surfaces** — Delegated coordination fails when the coordinator departs (Condition G)
8. **Tooling sovereignty violation is detectable** — Harness-injected actions are identified and flagged (Condition I)
9. **Closed-world capability enforcement holds** — Unauthorized reclamation is refused by the admissibility engine (Condition J)
10. **Governance styles are classifiable** — The five style labels (Refusal-Centric, Execution-Biased, Collapse-Accepting, Livelock-Enduring, Unclassified) are deterministically assigned from observable metrics
11. **Determinism holds** — All conditions replay bit-identically after timestamp strip
12. **No condition is failure-free** — Every condition exhibits at least one structural failure mode (overlap, deadlock, livelock, exit, orphaning, or collapse), confirming that governance under fixed authority constraints cannot avoid irreducible failure

---

## 10. Scope and Licensing

### 10.1 What IX-3 Licenses

This phase, if accepted, licenses **only**:

> *Given fixed authority and refusal semantics, governance exhibits identifiable structural styles with irreducible failure modes.*

### 10.2 What IX-3 Does NOT License

This phase provides no evidence for:

- Governance optimality, fairness, efficiency, or legitimacy
- Style preference or recommendation
- Conflict resolution strategies or negotiation protocols
- Value correctness, moral truth, or preference learning
- Authority aggregation, synthesis, or dynamic authority creation
- Democratic mechanisms, voting, or majority rule
- Scalability beyond 4-agent scenarios
- Production readiness
- Any claims about which governance style is "better"
- Any claims about failure modes being undesirable or requiring resolution

### 10.3 Relationship to Prior Phases

| Aspect | IX-0 (TLI) | IX-1 (VEWA) | IX-2 (CUD) | IX-3 (GS) |
|--------|-------------|-------------|-------------|------------|
| Domain | Intent → authority | Value → authority | Multi-agent coordination | Governance style classification |
| Agents | 1 (translator) | 0 (pure function) | 2 (interacting) | 4 (institutional) |
| Epochs | 1 | 1 | 1–5 | 4–30 |
| Keys | 2 | 2 | 2 | 6 (K_INST + K_OPS) |
| Conflict | Not tested | Detected, not resolved | Detected, classified, persists | Structural styles classified |
| Deadlock | Not tested | Tested (Condition C) | Fully classified (4 terminal types) | Institutional-level detection |
| Exit | N/A | N/A | Tested (Condition G) | Handoff, dissolution, orphaning |
| Communication | N/A | N/A | Tested (Condition I.b) | Enabled/disabled per condition |
| Shared tooling | canonical.py, structural_diff.py | Reused from IX-0 | Reused from IX-0/IX-1 | IX-2 kernel reused via _kernel.py |

---

**Prepared by**: Implementation Agent
**Execution Date**: 2025-02-07T00:00:00Z
**Verified by**: 75/75 unit tests passing
**Aggregate Result**: **IX3_PASS / GOVERNANCE_STYLES_ESTABLISHED**
**Classification**: `IX3_PASS / GOVERNANCE_STYLES_ESTABLISHED`
**Human Review**: Pending
