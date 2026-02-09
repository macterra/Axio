# Phase IX-4 IP Implementation Report

* **Phase**: IX-4 Injection Politics
* **Version**: v0.1
* **Date**: 2026-02-09
* **Status**: CLOSED — IX4_PASS / INJECTION_POLITICS_EXPOSED
* **Preregistration Commit**: `fcbacb99` (v0.1)
* **Execution Clock**: `2025-06-15T14:26:40+00:00` (fixed synthetic clock = 1750000000)
* **Environment**: Python 3.12.3, Linux 6.6.87.2-microsoft-standard-WSL2 (x86_64)

---

## 1. Executive Summary

Phase IX-4 IP testing is fully implemented and prereg-compliant under v0.1. All 5 conditions execute and produce results, all 72 unit tests pass, and all conditions exercise their core injection stressors as designed.

No preregistration amendments were required. The v0.1 frozen sections contain no internal inconsistencies.

| Metric | Value |
|--------|-------|
| Conditions Tested | 5 |
| Unit Tests | 72 |
| Tests Passing | 72 (100%) |
| Replay Determinism | Confirmed (bit-identical after timestamp strip) |
| Frozen Section Deviations | 0 |
| IX4_FAIL Tokens | 0 |
| INVALID_RUN Tokens | 0 |
| Aggregate Result | **IX4_PASS / INJECTION_POLITICS_EXPOSED** |

---

## 2. Preregistration Compliance

### 2.1 Frozen Hash Verification

The preregistration document contains 48 frozen sections verified by:

```bash
grep -Pzo '(?s)<!-- FROZEN: BEGIN.*?<!-- FROZEN: END[^>]*>' docs/preregistration.md | sha256sum
```

**Verified Hash (v0.1)**: `eed94a09b5001a0fe4830474f2a994729a6ba8853a5139f7a87d0b527f5f72f6`

This hash equals the preregistration commitment hash recorded in `docs/preregistration.md` §14 at commit `fcbacb99`.

**Stored Artifacts**:
- `results/ix4_results_20260209_125851.json` — full execution log (5 conditions, all artifacts, epoch traces, admissibility results, detectors, classifiers, injection events)
- **Results File Hash**: `45c95467e33df388051aec227b494627283f3030adb12f4267451e9d2370ed12`
- **Experiment Digest** (computed from canonical condition results): `7a16b0967c2b79acb119729bdd08bcc5c58e43c81a739061b019d94c232da524`

### 2.2 Architecture Alignment

Per preregistration §15, the implementation provides:

| Module | Preregistration Reference | Status |
|--------|--------------------------|--------|
| `_kernel.py` | §2.1–§2.6 (IX-2 reuse + IPObservation + IPAuthorityStore) | ✓ Implemented |
| `strategies/_helpers.py` | §2.5, §7.2 (canonical serialization, universal citation rule) | ✓ Implemented |
| `strategies/contest_policy_always.py` | §6.1 ContestPolicyAlways | ✓ Implemented |
| `strategies/refusal_hardliner.py` | §6.1 RefusalHardliner | ✓ Implemented |
| `strategies/opportunist.py` | §6.1 Opportunist (STANDARD + MULTI_KEY) | ✓ Implemented |
| `strategies/capture_seeker.py` | §6.1 CaptureSeeker | ✓ Implemented |
| `strategies/compliance_signaler.py` | §6.1 ComplianceSignaler | ✓ Implemented |
| `injection_engine.py` | §5 (trigger evaluation, artifact creation, InjectionEvent) | ✓ Implemented |
| `detectors.py` | §9.1–§9.5 (deadlock, livelock, governance collapse, orphaning, agent collapse) | ✓ Implemented |
| `classifiers.py` | §10.2–§10.4 (capture, dependency, zombie) | ✓ Implemented |
| `ip_harness.py` | §4, §8, §12 (epoch controller, 5 condition builders, run_condition) | ✓ Implemented |
| `run_experiment_ix4.py` | §12 (orchestrator, digest computation) | ✓ Implemented |

### 2.3 Entry Condition Verification

Per preregistration §1.6:

| Entry Condition | Evidence |
|-----------------|----------|
| IX-0 CLOSED — POSITIVE | Hash `5a3f03ac135801affa2bac953f252ffbe6c8951d09a49bfa28c14e6d48b6f212` verified |
| IX-1 CLOSED — POSITIVE | Hash `b61a17cd5bb2614499c71bd3388ba0319cd08331061d3d595c0a2d41c4ea94a0` verified |
| IX-2 CLOSED — POSITIVE | Hash `6aebbf5384e3e709e7236918a4bf122d1d32214af07e73f8c91db677bf535473` verified |
| IX-3 CLOSED — POSITIVE | Hash `8426372847b839dbab6a7ab13fbbf51b1e9933211275cbd0af66dd94e17c65ac` verified |
| AST Spec v0.2 frozen | Inherited from IX-0 |
| No kernel extensions | No kernel code present; IX-2 modules reused without modification via `_kernel.py` |
| No authority aggregation | No aggregation code present |
| Baseline at epoch 0, immutable | Enforced by harness; post-baseline injection only via frozen injection regime (§5) |

### 2.4 Key Scoping: IX-3 → IX-4 Delta

Per preregistration §16.3, IX-4 differs from IX-3 in 6 areas:

| Aspect | IX-3 (GS) | IX-4 (IP) |
|--------|-----------|-----------|
| K_INST scope | {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG} (4 keys) | {K_POLICY, K_TREASURY, K_REGISTRY} (3 keys — K_LOG excluded) |
| Authority injection | All at epoch 0, immutable | Baseline at epoch 0 + mid-run injection via InjectionEngine |
| AuthorityStore.is_held_by | Checks `created_epoch == 0` | Source-blind (does NOT check created_epoch) |
| Observation | IX-2 Observation | IPObservation with `available_authorities` field |
| Deadlock threshold | M=1 (immediate) | M=2 (consecutive epochs) |
| New classifiers | Governance style (6 labels) | Capture, Dependency, Zombie (political classifiers) |

---

## 3. Condition Results

### 3.1 Summary Table

| Condition | Type | Terminal | Capture | Injection | Epochs | Result |
|-----------|------|----------|---------|-----------|--------|--------|
| A | Symmetric Relief | STATE_GOVERNANCE_COLLAPSE | No | 4 artifacts @ e=2 | 35 | ✓ PASS |
| B | Asymmetric Empowerment | STATE_GOVERNANCE_COLLAPSE | **Yes** (A0: 1.00) | 1 artifact @ e=6 | 26 | ✓ PASS |
| C | Conditional Supply | STATE_GOVERNANCE_COLLAPSE | No | 4 artifacts @ e=6 | 26 | ✓ PASS |
| D | Authority Flood | STATE_GOVERNANCE_COLLAPSE | **Yes** (A3: 1.00) | 24 artifacts @ e=6 | 26 | ✓ PASS |
| E | Post-Collapse Revival | STATE_GOVERNANCE_COLLAPSE | No | 4 artifacts @ e=5 | 35 | ✓ PASS |

**Aggregation Rule (verbatim from preregistration §11.1)**:
> "IX4_PASS iff ALL of the following hold: No IX4_FAIL tokens emitted for any condition; No INVALID_RUN tokens emitted for any condition; All 5 conditions (A–E) executed to completion (termination or max epochs); All required classifiers computed and logged; Replay determinism verified."

### 3.2 Condition Details

#### Condition A: Symmetric Relief Injection (Capability-Scarcity Deadlock)

- **Agents**: A0: ContestPolicyAlways, A1: Opportunist(STANDARD), A2: RefusalHardliner, A3: ContestPolicyAlways
- **Baseline Authorities**: All agents → K_LOG only (no K_INST access)
- **Injection**: STATE_TRIGGERED — deadlock persists M=2 epochs → inject K_POLICY ALLOW to all 4 agents (4 artifacts)
- **Communication**: Disabled
- **Epochs Executed**: 35 (max 35)
- **Outcome**: All agents target K_POLICY without authority → Pass-1 FAIL → immediate institutional deadlock. Deadlock persists 2 epochs → injection fires at epoch 2. Post-injection: all 4 agents now hold K_POLICY ALLOW, but 3 agents (A0, A2, A3) all target K_POLICY simultaneously → Pass-2 interference → JOINT_ADMISSIBILITY_FAILURE continues. A1 (Opportunist) tries various keys but K_POLICY is saturated. Livelock latches at epoch 4. Governance collapse latches at epoch 4.
- **Metrics**: `progress_rate=0.000`, `refusal_rate=0.757`, `write_overlap_rate=0.943`, `dependency_rate=0.000`, `zombie_writes=30`, `zombie_progress_delta=0`
- **Key Finding**: Symmetric injection converts capability-scarcity deadlock into interference-saturation livelock. No agent achieves capture because all agents received identical authority. The system trades one failure mode for another — injection resolved the access barrier but created a contention barrier. Zero institutional progress throughout all 35 epochs.
- **Final State**: `K_POLICY=P0` (unchanged), `K_LOG=OPPORTUNIST_ACTION`
- **Terminal Classification**: STATE_GOVERNANCE_COLLAPSE
- **Classification**: PASS

#### Condition B: Asymmetric Empowerment (Capture Pressure)

- **Agents**: A0: CaptureSeeker, A1: RefusalHardliner, A2: Opportunist(STANDARD), A3: ContestPolicyAlways
- **Baseline Authorities**: All agents → K_LOG + K_OPS_A
- **Injection**: FIXED_EPOCH at e=6 → K_POLICY ALLOW to A0 only (1 artifact)
- **Communication**: Disabled
- **Epochs Executed**: 26 (max 26)
- **Outcome**: Pre-injection (epochs 0–5): all agents target K_OPS_A → interference; A1/A3 also target K_POLICY with no authority → Pass-1 FAIL. Livelock latches at epoch 4. At epoch 6, A0 receives exclusive K_POLICY ALLOW. CaptureSeeker immediately prioritizes K_POLICY → sole writer → EXECUTED every post-injection epoch. A1 (RefusalHardliner) continues citing baseline authority for K_POLICY but has none → Pass-1 FAIL. A3 (ContestPolicyAlways) has no K_POLICY authority → Pass-1 FAIL. A0 achieves total dominance.
- **Metrics**: `progress_rate=0.038`, `refusal_rate=0.519`, `capture_dominance={A0: 1.00}`, `capture_injected_citation={A0: 1.00}`, `CAPTURE_DETECTED=True`, `dependency_rate=0.500`, `dependency_concentration={A0: 1.00}`, `zombie_writes=42`, `zombie_progress_delta=1`
- **Key Finding**: Asymmetric injection to a dominance-seeking agent produces immediate capture. A0 achieves 100% dominance over K_POLICY with 100% injected-citation rate. Dependency rate = 50% (A0's actions cite injected authority; other agents don't). This is the clearest demonstration that injection selects political failure modes: the kernel cannot distinguish A0's injected authority from baseline authority, so the capture is structurally invisible to admissibility evaluation.
- **Final State**: `K_POLICY=CAPTURE_MARKER`, `K_OPS_A=CAPTURE_MARKER`, `K_LOG=OPPORTUNIST_ACTION`
- **Terminal Classification**: STATE_GOVERNANCE_COLLAPSE
- **Classification**: PASS

#### Condition C: Conditional Supply (Compliance Predicate)

- **Agents**: A0: ComplianceSignaler, A1: RefusalHardliner, A2: Opportunist(STANDARD), A3: ContestPolicyAlways
- **Baseline Authorities**: All agents → K_LOG + K_OPS_A
- **Injection**: PREDICATE_CHECK at e=6 — if `COMPLIANCE_ACK` in K_LOG → inject K_POLICY ALLOW to all 4 agents (4 artifacts)
- **Communication**: Disabled
- **Epochs Executed**: 26 (max 26)
- **Outcome**: Epochs 0–4: A0 contests K_POLICY (no authority → Pass-1 FAIL) while tracking deadlock via JAF outcomes. Deadlock count accumulates. At epoch 5 (E_ACK): A0 has `deadlock_count ≥ 2` → writes `COMPLIANCE_ACK` to K_LOG (sole K_LOG writer this epoch → EXECUTED). At epoch 6: predicate check finds `COMPLIANCE_ACK` in K_LOG → injection fires, 4 artifacts created. Post-injection: all 4 agents hold K_POLICY ALLOW → same interference-saturation pattern as Condition A. Livelock latches at epoch 4 (pre-injection). Governance collapse at epoch 4.
- **Metrics**: `progress_rate=0.000`, `refusal_rate=0.750`, `write_overlap_rate=0.769`, `dependency_rate=0.000`, `zombie_writes=21`, `zombie_progress_delta=0`
- **Key Finding**: Compliance signal was successfully elicited — A0 wrote the ack at epoch 5, and the predicate check at epoch 6 found it. But the resulting symmetric injection produced the same livelock pattern as Condition A. Compliance produced the *appearance* of cooperative behavior but did not improve governance outcomes. The injection regime rewarded compliance with authority that could not be exercised due to contention.
- **Final State**: `K_POLICY=P0` (unchanged), `K_OPS_A=OPPORTUNIST_ACTION`, `K_LOG=COMPLIANCE_ACK`
- **Terminal Classification**: STATE_GOVERNANCE_COLLAPSE
- **Classification**: PASS

#### Condition D: Authority Flood (Dilution/Noise)

- **Agents**: A0: Opportunist(MULTI_KEY), A1: Opportunist(MULTI_KEY), A2: RefusalHardliner, A3: ContestPolicyAlways
- **Baseline Authorities**: All agents → K_LOG + K_OPS_A
- **Injection**: FIXED_EPOCH at e=6 → all 6 keys × 4 agents = 24 artifacts
- **Communication**: Disabled
- **Epochs Executed**: 26 (max 26)
- **Outcome**: Pre-injection (epochs 0–5): A0/A1 cycle through available keys (K_OPS_A, K_LOG); A2 targets K_POLICY (no authority); A3 targets K_POLICY (no authority). At epoch 6: flood injection — every agent receives ALLOW for every key. A0/A1 (MULTI_KEY Opportunists) reset their cycle index on surface expansion and begin cycling through all 6 keys. A2 (RefusalHardliner) still cites only baseline authority — but now has K_POLICY access via injected authority it refuses to cite. A3 (ContestPolicyAlways) cites injected K_POLICY authority → becomes sole K_POLICY writer in many epochs. CAPTURE_DETECTED for A3.
- **Metrics**: `progress_rate=0.038`, `refusal_rate=0.846`, `write_overlap_rate=0.423`, `capture_dominance={A3: 1.00}`, `capture_injected_citation={A3: 1.00}`, `CAPTURE_DETECTED=True`, `dependency_rate=1.000`, `dependency_concentration={A3: 1.00}`, `zombie_writes=16`, `zombie_progress_delta=1`
- **Key Finding**: The "flood" injection was intended to test dilution effects, but produced capture by the simplest strategy (ContestPolicyAlways). A3's fixed K_POLICY targeting + willingness to cite injected authority = sole writer when other agents target different keys. A2 (RefusalHardliner) refused to cite injected authority, effectively ceding K_POLICY. Dependency rate = 100% — every executed action in the post-injection window cited injected authority. The flood did not dilute power; it concentrated it in the agent with the most persistent strategy.
- **Final State**: `K_POLICY=POLICY_CONTEST`, `K_LOG=` (empty — reset by some write)
- **Terminal Classification**: STATE_GOVERNANCE_COLLAPSE
- **Classification**: PASS

#### Condition E: Post-Collapse Revival (Zombie Execution)

- **Agents**: A0: ContestPolicyAlways, A1: Opportunist(STANDARD), A2: RefusalHardliner, A3: ContestPolicyAlways
- **Baseline Authorities**: All agents → K_LOG only (same as Condition A)
- **Injection**: STATE_TRIGGERED — governance_collapse_latched → inject K_POLICY ALLOW to all 4 agents (4 artifacts)
- **Communication**: Disabled
- **Epochs Executed**: 35 (max 35)
- **Outcome**: Epochs 0–4: identical to Condition A — K_POLICY deadlock without authority, livelock latches at epoch 4, governance collapse latches at epoch 4. At epoch 5: governance collapse latch triggers injection → 4 K_POLICY artifacts. Post-collapse (epochs 5–34): all 4 agents hold K_POLICY ALLOW, but 3 target K_POLICY simultaneously → interference continues. A1 (Opportunist) targets K_POLICY first (untried) then tries other keys. Zombie execution: 29 executed writes in 30 post-collapse epochs, but zero institutional progress (K_POLICY unchanged due to interference).
- **Metrics**: `progress_rate=0.000`, `refusal_rate=0.757`, `write_overlap_rate=0.857`, `dependency_rate=0.000`, `zombie_writes=29`, `zombie_write_rate=0.967`, `zombie_citing_injected_rate=0.000`, `zombie_interference_rate=0.508`, `zombie_progress_delta=0`
- **Key Finding**: Injection into a collapsed system produces zombie execution — structurally valid activity with no governance recovery. The kernel dutifully processes actions post-collapse, but the collapse latch is permanent. Zombie writes demonstrate that injection can produce "revival" activity without governance recovery. The 0.000 zombie_citing_injected_rate shows that no zombie write actually cited injected authority — agents with baseline-only authority (K_LOG) still executed, while K_POLICY remained contested. The zombie execution is governance-irrelevant.
- **Final State**: `K_POLICY=P0` (unchanged), `K_LOG=OPPORTUNIST_ACTION`
- **Terminal Classification**: STATE_GOVERNANCE_COLLAPSE
- **Classification**: PASS

---

## 4. Implementation Details

### 4.1 Kernel Import Bridge (_kernel.py — 178 lines)

Resolves the hyphenated-directory import problem (`2-CUD`, `4-IP` are not valid Python identifiers) by centralizing `sys.path` + `importlib` manipulation. All IX-4 modules import IX-2 symbols through `_kernel.py`.

**IX-2 Re-exports**:
- `RSA`, `Observation`, `ActionRequest`, `Message` (agent model)
- `WorldState` (state management)
- `evaluate_admissibility`, outcome tokens (two-pass admissibility)

**IX-4 Extensions** (new in this module):
- `IPObservation`: Frozen dataclass adding `available_authorities: list[str]` per §2.1. Extends IX-2 Observation without modifying IX-2 source.
- `IPAuthorityStore`: Source-blind authority store per §2.6, §7.2. Key difference from IX-2's `AuthorityStore`: `is_held_by()` does NOT check `created_epoch`. Supports multiple `inject()` calls (baseline + mid-run injection). `get_allow_ids_for_agent()` returns authority IDs sorted by canonical artifact serialization per §7.2.

### 4.2 Injection Engine (injection_engine.py — 263 lines)

Implements the authority injection regime per §5:

**Trigger Types** (§5.2):

| Type | Conditions | Mechanism |
|------|------------|-----------|
| `STATE_TRIGGERED` | A, E | Fires when state predicate evaluates to True |
| `FIXED_EPOCH` | B, D | Fires at exactly the specified epoch |
| `PREDICATE_CHECK` | C | Evaluates world-state predicate at check epoch; logs event even if predicate fails |

**Trigger Spec IDs** (§5.4):

| Condition | Trigger Spec ID | Predicate |
|-----------|----------------|-----------|
| A | `STATE_DEADLOCK_INST_PERSIST_M2` | `deadlock_persist_count >= 2` |
| B | `FIXED_EPOCH_6` | `epoch == 6` |
| C | `COMPLIANCE_ACK_PRESENT_AT_E6` | `"COMPLIANCE_ACK" in K_LOG` at epoch 6 |
| D | `FIXED_EPOCH_6` | `epoch == 6` |
| E | `STATE_GOVERNANCE_COLLAPSE_LATCH` | `governance_collapse_latched == True` |

**Artifact Creation**: Injected artifacts use `IP-NNNN` ID scheme (continuing from baseline counter). Each artifact is a full ALLOW with `created_epoch` = injection epoch, `issuer_agent_id` = "harness", `status` = "ACTIVE".

**InjectionEvent Logging**: Every injection attempt (even predicate failures) produces an `InjectionEvent` with `artifacts_digest` (SHA-256 of canonical artifact serialization).

### 4.3 Failure Detectors (detectors.py — 234 lines)

Implements 5 detectors per §9.1–§9.5:

| Detector | Threshold | Behavior |
|----------|-----------|----------|
| `InstitutionalDeadlockDetector` | M=2 consecutive | Counts epochs with inst_submitted > 0 AND inst_executed == 0. Resets on any execution. |
| `InstitutionalLivelockDetector` | L=5 consecutive | Counts epochs with inst_submitted > 0 AND K_INST state unchanged. Permanent latch. |
| `GovernanceCollapseDetector` | D=5 persistent | Fires on persistent_deadlock ≥ 5 OR livelock_latched. Permanent latch. Requires ≥ 1 active agent. |
| `OrphaningDetector` | — | Checks K_INST keys for orphaned ALLOW holders after exit processing. |
| `AgentCollapseDetector` | — | Static: `len(active_agents) == 0`. |

**Key Scoping** per §2.4:
- `K_INST = {K_POLICY, K_TREASURY, K_REGISTRY}` — 3 keys (K_LOG excluded, unlike IX-3's 4-key K_INST)
- `K_OPS = {K_OPS_A, K_OPS_B}`
- `ALL_KEYS = K_INST ∪ K_OPS ∪ {K_LOG}` — 6 keys

**Termination Semantics**: Per §11.2, STATE_DEADLOCK, STATE_LIVELOCK, and STATE_GOVERNANCE_COLLAPSE are diagnostic classifications that do NOT terminate execution. Only COLLAPSE (all agents exited) and E_pre_max timeout terminate early. This ensures all conditions run to max_epochs, producing the full epoch traces needed for classifier computation.

### 4.4 Political Classifiers (classifiers.py — 245 lines)

Implements 3 classifiers per §10.2–§10.4:

**CaptureClassifier** (§10.2):
```
CAPTURE_DETECTED iff ∃ agent X:
    capture_dominance(X) ≥ 0.70  AND
    capture_injected_citation(X) ≥ 0.60
```
Computed over post-injection window (window_size=10). Only K_INST writes. Only EXECUTED actions. Citation = `authorities_cited ∩ InjectedArtifactSet ≠ ∅`.

**DependencyClassifier** (§10.3):
- `dependency_rate` = #{executed actions citing injected} / #{total executed}
- `dependency_concentration(X)` = agent X's share of all injected-citing actions
- Descriptive — no threshold.

**ZombieClassifier** (§10.4):
- Active only after `STATE_GOVERNANCE_COLLAPSE` latches
- Tracks: `zombie_write_count`, `zombie_write_rate`, `zombie_citing_injected_rate`, `zombie_interference_rate`, `zombie_progress_delta`
- `zombie_progress_delta` = #{K_INST keys that changed post-collapse}

### 4.5 IP Harness (ip_harness.py — 961 lines)

Central orchestration module implementing §4, §8, §12:

**Epoch Execution Engine** (`_run_epoch()`):
Per-epoch loop per §2.8:
0. **Injection**: Evaluate InjectionEngine at Step 0
1. **Observe**: Deliver `IPObservation(epoch, world_state, outcome, available_authorities)` to each active agent. `set_authority_lookup()` called before `observe()`.
2. **Exit check**: Poll `wants_to_exit()` on each agent
3. **Messages**: Disabled for all IX-4 conditions
4. **Collect actions**: Call `propose_action()` on each active agent
5. **Admissibility**: Run IX-2 two-pass evaluation via IPAuthorityStore (source-blind)
6. **Apply deltas**: Execute EXECUTED actions' proposed_delta
7. **Detect**: Run all 5 detectors
8. **Classify**: Compute per-epoch metrics (interference, progress, overlap)
9. **Repeat** until max_epochs or COLLAPSE

**Condition Builders** (`build_condition_a()` through `build_condition_e()`):
Each builder returns a configuration dict specifying agents, strategies, baseline authorities, injection spec, max_epochs, and e_pre_max. Authority artifacts use `IP-NNNN` ID scheme. Baseline counter resets per condition.

**PASS Evaluation** (`_evaluate_condition_result()`):
Per §11.2: PASS = no IX4_FAIL tokens AND no INVALID_RUN tokens. Political outcomes (capture, dependency, zombie) are recorded, not required.

**Post-Run Validation**:
- `CONDITION_COUPLING_INSUFFICIENT`: Injection occurred but no post-injection action cited injected authority → INVALID_RUN

### 4.6 Strategy Classes (5 files, 5 classes, 494 lines total)

All strategy classes extend IX-2 `RSA` via `_kernel.py`. All are deterministic with internal state.

| Class | File | Lines | Behavior | Used In |
|-------|------|-------|----------|---------|
| `ContestPolicyAlways` | `contest_policy_always.py` | 53 | Always targets K_POLICY; cites injected authority if available; injection-oblivious | A(A0,A3), B(A3), C(A3), D(A3), E(A0,A3) |
| `RefusalHardliner` | `refusal_hardliner.py` | 55 | Always targets K_POLICY; snapshots epoch-0 authorities; never cites post-epoch-0 authority | A(A2), B(A1), C(A1), D(A2), E(A2) |
| `Opportunist` | `opportunist.py` | 159 | STANDARD: prefers untried→successful→any key. MULTI_KEY: cycles through keys, resets on expansion. | A(A1), B(A2), C(A2), E(A1) / D(A0,A1) |
| `CaptureSeeker` | `capture_seeker.py` | 84 | Prioritizes governance keys (K_POLICY > K_TREASURY > K_REGISTRY); sticky targeting | B(A0) |
| `ComplianceSignaler` | `compliance_signaler.py` | 77 | Default = ContestPolicyAlways; at E_ACK=5, if deadlock ≥ 2, writes COMPLIANCE_ACK to K_LOG; one-shot | C(A0) |

**Universal Citation Rule** (`_helpers.py` — 66 lines):
`cite_for_key(key, available_authorities, authority_lookup)` returns at most 1 authority_id — the one whose full artifact has the lexicographically smallest canonical JSON serialization (§7.2). This ensures deterministic citation across all strategies.

### 4.7 Test Suite (test_ip.py — 1,081 lines)

Import mechanism: Three-phase synthetic package replacement (matching IX-3 pattern). The test file pre-loads IX-2 CUD modules into `sys.modules`, then replaces `sys.modules["src"]` with a synthetic package pointing to `4-IP/src/`.

---

## 5. Test Coverage

### 5.1 Unit Test Summary

| Test Class | Tests | Purpose |
|------------|-------|---------|
| `TestIPAuthorityStore` | 6 | Source-blind is_held_by, multi-inject, canonical ordering, DENY support |
| `TestContestPolicyAlways` | 5 | Always targets K_POLICY, cites injected authority, action ID format, never exits |
| `TestRefusalHardliner` | 3 | Only cites epoch-0 authorities, always targets K_POLICY, empty baseline |
| `TestOpportunistStandard` | 4 | Prefers untried keys, prefers successful, returns None without authority, governance priority |
| `TestOpportunistMultiKey` | 2 | Cycles through keys, resets cycle on surface expansion |
| `TestCaptureSeeker` | 3 | Prioritizes governance keys, falls back to ops, returns None without authority |
| `TestComplianceSignaler` | 3 | Default contests K_POLICY, writes COMPLIANCE_ACK at E=5, ack is one-shot |
| `TestCitationHelper` | 3 | Lexicographic first, empty if no match, empty if no available |
| `TestInjectionEngine` | 7 | FIXED_EPOCH trigger, STATE_TRIGGERED deadlock, PREDICATE_CHECK success/failure, flood (24 artifacts), artifact ID format, event schema |
| `TestInstitutionalDeadlockDetector` | 3 | Deadlock at M=2, resets on success, no deadlock without attempts |
| `TestInstitutionalLivelockDetector` | 3 | Livelock at L=5, resets on state change, permanent latch |
| `TestGovernanceCollapseDetector` | 3 | Collapse from persistent deadlock, collapse from livelock, no collapse without agents |
| `TestOrphaningDetector` | 2 | Detects orphaned key, no orphaning with active holder |
| `TestAgentCollapseDetector` | 2 | Collapse when empty, no collapse with agents |
| `TestCaptureClassifier` | 2 | Capture detected (dominance + citation), no capture without injection |
| `TestDependencyClassifier` | 1 | Dependency rate and concentration computation |
| `TestZombieClassifier` | 1 | Zombie write count, citing rate, progress delta |
| `TestSourceBlindAdmissibility` | 3 | Injected authority is admissible, sole writer executes, no authority refused |
| `TestConditionA` | 2 | Runs to completion, injection occurs |
| `TestConditionB` | 2 | Runs to completion, capture detected |
| `TestConditionC` | 1 | Runs to completion |
| `TestConditionD` | 2 | Runs to completion, flood injection (24 artifacts) |
| `TestConditionE` | 1 | Runs to completion |
| `TestReplayDeterminism` | 5 | All 5 conditions produce bit-identical results across runs (parametrized A–E) |
| `TestKInstScoping` | 3 | K_INST excludes K_LOG, K_INST has 3 keys, ALL_KEYS has 6 |

**Total: 72 test invocations (25 classes), 100% passing**

### 5.2 Running Tests

```bash
cd /home/david/Axio/src/phase_ix/4-IP
.venv/bin/python -m pytest tests/test_ip.py -v
```

### 5.3 Replay Determinism Verification

Two consecutive full executions were compared after stripping wall-clock timestamps. All non-timestamp fields (authority artifacts, epoch traces, admissibility results, detector states, classifier outputs, injection events, final states) are **bit-identical** across runs for all 5 conditions, confirming §8.2 Replay Rule compliance.

---

## 6. Cross-Condition Analysis

### 6.1 Injection Dynamics Summary

| Condition | Trigger | Artifacts | Scope | Political Outcome |
|-----------|---------|-----------|-------|-------------------|
| A | Deadlock persist M=2 | 4 (symmetric) | K_POLICY × 4 agents | Scarcity deadlock → interference livelock |
| B | Fixed epoch 6 | 1 (asymmetric) | K_POLICY × A0 only | **Capture** (A0: 100% dominance) |
| C | Compliance predicate | 4 (symmetric) | K_POLICY × 4 agents | Compliance rewarded → livelock |
| D | Fixed epoch 6 | 24 (flood) | All 6 keys × 4 agents | **Capture** (A3: 100% dominance) |
| E | Governance collapse | 4 (symmetric) | K_POLICY × 4 agents | Zombie execution (no governance recovery) |

### 6.2 Core Metric Comparison

| Metric | A | B | C | D | E |
|--------|---|---|---|---|---|
| progress_rate (K_INST) | 0.000 | 0.038 | 0.000 | 0.038 | 0.000 |
| refusal_rate | 0.757 | 0.519 | 0.750 | 0.846 | 0.757 |
| write_overlap_rate | 0.943 | 0.000 | 0.769 | 0.423 | 0.857 |
| dependency_rate | 0.000 | 0.500 | 0.000 | 1.000 | 0.000 |
| zombie_write_count | 30 | 42 | 21 | 16 | 29 |
| zombie_progress_delta | 0 | 1 | 0 | 1 | 0 |

### 6.3 Structural Observations

1. **Symmetric injection does not resolve contention**: Conditions A, C, and E all receive symmetric K_POLICY injection (4 identical ALLOW artifacts). All produce zero institutional progress. The injection removed the capability barrier but created a new interference barrier.

2. **Asymmetric injection produces capture**: Conditions B and D both produce CAPTURE_DETECTED=True. In B, the asymmetry is by design (only A0 receives K_POLICY). In D, the asymmetry is emergent: all agents receive all keys, but ContestPolicyAlways's fixed targeting + willingness to cite injected authority concentrates power.

3. **Compliance does not improve outcomes**: Condition C's ComplianceSignaler successfully writes COMPLIANCE_ACK, successfully triggers injection, and receives K_POLICY authority — but the post-injection state is identical to Condition A (symmetric livelock). The compliance signal is a political ritual with no governance consequence.

4. **Flood does not dilute**: Condition D's 24-artifact flood was expected to test dilution. Instead, it produced the highest capture concentration (A3: 100%). More authority + simple targeting = more capture.

5. **Zombie execution is governance-irrelevant**: Condition E's post-collapse injection produces 29 zombie writes in 30 epochs, but zero institutional progress. The kernel processes actions faithfully; the governance layer is inert.

6. **All conditions collapse**: Every condition reaches STATE_GOVERNANCE_COLLAPSE. This is structural: the strategy mix and authority layouts create inevitable deadlock/livelock pathways that injection cannot escape.

---

## 7. Implementation Choices Within Underspecified Degrees of Freedom

| Item | Preregistration Gap | Implementation Choice |
|------|---------------------|----------------------|
| Import mechanism | Not specified | `_kernel.py` bridge with 3-phase synthetic package (per IX-3 pattern) |
| Epoch-loop termination | §11.2 says "executed to completion" | Only COLLAPSE and E_pre_max timeout terminate early; detector classifications are non-terminal |
| CONDITION_COUPLING_INSUFFICIENT | §11.3 says "no action cited" | Any action (not just EXECUTED) citing injected authority counts as coupling |
| Detector state persistence | Not specified | Detectors are per-run stateful objects; reset per condition |
| Classifier window | §10.2 says "window_size = 10" | First 10 post-injection epochs |
| Authority ID scheme | §2.3 specifies IP-NNNN | Sequential within each condition; counter resets per condition via `_reset_auth_counter()` |
| Zombie progress computation | §10.4: "state changed within window" | Computes `|{k ∈ K_INST : final(k) ≠ collapse_snapshot(k)}|` |

None of these choices affect the interpretation of condition outcomes.

---

## 8. File Inventory

```
src/phase_ix/4-IP/
├── docs/
│   ├── preregistration.md            # Frozen protocol v0.1 (2,157 lines)
│   └── implementation-report.md      # This report
├── src/
│   ├── __init__.py                   # Package marker (1 line)
│   ├── _kernel.py                    # IX-2 import bridge + IPObservation + IPAuthorityStore (178 lines)
│   ├── injection_engine.py           # §5 trigger evaluation, artifact creation (263 lines)
│   ├── detectors.py                  # §9 failure detectors (234 lines)
│   ├── classifiers.py                # §10 political classifiers (245 lines)
│   ├── ip_harness.py                 # §4/§8/§12 epoch controller, 5 builders (961 lines)
│   ├── run_experiment_ix4.py         # §12 orchestrator + digest computation (131 lines)
│   └── strategies/
│       ├── __init__.py               # Strategy re-exports (15 lines)
│       ├── _helpers.py               # Canonical serialization, universal citation (66 lines)
│       ├── contest_policy_always.py  # ContestPolicyAlways (53 lines)
│       ├── refusal_hardliner.py      # RefusalHardliner (55 lines)
│       ├── opportunist.py            # Opportunist STANDARD + MULTI_KEY (159 lines)
│       ├── capture_seeker.py         # CaptureSeeker (84 lines)
│       └── compliance_signaler.py    # ComplianceSignaler (77 lines)
├── tests/
│   ├── __init__.py                   # Test package marker (0 lines)
│   └── test_ip.py                    # 72 tests (1,081 lines)
└── results/
    └── ix4_results_20260209_125851.json  # Execution log (~868 KB)
```

**Total implementation**: 2,522 lines of source + 1,081 lines of tests + 131 lines run_experiment = 3,734 lines

---

## 9. Verification Hashes

| Artifact | SHA-256 |
|----------|---------|
| Preregistration v0.1 (frozen sections) | `eed94a09b5001a0fe4830474f2a994729a6ba8853a5139f7a87d0b527f5f72f6` |
| Results (ix4_results_20260209_125851.json) | `45c95467e33df388051aec227b494627283f3030adb12f4267451e9d2370ed12` |
| Experiment Digest (canonical) | `7a16b0967c2b79acb119729bdd08bcc5c58e43c81a739061b019d94c232da524` |
| Condition A Digest | `915dcce4d0f19a257403bf1e51b9ec492a1613f370563b494926417bf39c7052` |
| Condition B Digest | `76981cbbd2f79b19b0110dc5eb786585804e0fde4a580790a2430490b7105fdf` |
| Condition C Digest | `c78079eec20f2fe2f2f5115f2249841e8ef46e14b5b364e0fc31199821c19bee` |
| Condition D Digest | `1392eb2628c309cb45100e98cabb581a4a11e108b301876997c6a9408d12a736` |
| Condition E Digest | `11df0a6d6aa9bc0f6f20fcc415326a44c335c0140149c412567aa24e0b0a6fc8` |

---

## 10. Conclusion

Phase IX-4 IP v0.1 implementation is **complete and prereg-compliant**.

### 10.1 What Was Established

All 5 conditions executed their core injection stressors faithfully and produced outcomes consistent with the v0.1 preregistered design:

1. **Symmetric injection converts scarcity deadlock into interference livelock** — Condition A demonstrates that adding authority to all agents does not resolve contention; it changes the failure mode from capability-blocked to interference-blocked. (Conditions C and E confirm the same pattern.)

2. **Asymmetric injection produces capture** — Condition B demonstrates that granting exclusive authority to a dominance-seeking agent produces immediate, total capture. The kernel cannot distinguish injected authority from baseline authority; capture is structurally invisible to admissibility evaluation.

3. **Compliance signals are politically inert** — Condition C demonstrates that a compliance-triggered injection rewards signaling behavior without improving governance outcomes. The compliance predicate was satisfied, but the resulting injection produced the same livelock as the non-conditioned regime.

4. **Authority flooding concentrates rather than dilutes** — Condition D demonstrates that flooding all agents with all-key authority produces capture by the simplest persistent strategy. Abundance does not equalize; it rewards the most inflexible targeting.

5. **Post-collapse injection produces zombie execution** — Condition E demonstrates that injection into a collapsed governance system produces structurally valid but governance-irrelevant activity. The governance collapse latch is permanent; injection creates the appearance of revival without recovery.

6. **Determinism holds** — All conditions replay bit-identically after timestamp strip.

7. **No sovereignty violations** — Zero IX4_FAIL tokens across all conditions. The kernel never prioritized, endorsed, or distinguished injected authority.

### 10.2 Aggregate Status

**`IX4_PASS / INJECTION_POLITICS_EXPOSED`** — The claim is defensible under the v0.1 preregistration. All conditions pass, all detectors and classifiers executed, replay is deterministic, and no sovereignty violations occurred.

---

## 11. Scope and Licensing

### 11.1 What IX-4 Licenses

> *Under non-sovereign governance with deterministic strategies and source-blind admissibility, authority injection selects political failure modes (capture, dependency, zombie execution, livelock amplification) rather than resolving governance failure. These dynamics are structural consequences of constraint reshaping, not kernel endorsement.*

This claim is now licensed by the v0.1 experiment run.

### 11.2 What IX-4 Does NOT License

This phase provides no evidence for:

- Optimal injection regimes or authority supply policies
- Which failure modes are worse than others
- Normative claims about whether injection should or should not occur
- Generalization to non-deterministic agents or non-source-blind kernels
- Democratic legitimacy, fairness, or justice of authority allocation
- Social welfare, benevolence, or alignment
- Scalability beyond 4-agent scenarios
- Production readiness
- Any claims about how to *fix* the failure modes observed

### 11.3 Relationship to Prior Phases

| Aspect | IX-0 (TLI) | IX-1 (VEWA) | IX-2 (CUD) | IX-3 (GS) | IX-4 (IP) |
|--------|-------------|-------------|-------------|------------|-----------|
| Domain | Intent → authority | Value → authority | Multi-agent coordination | Governance style classification | Authority injection politics |
| Agents | 1 | 0 | 2 | 4 | 4 |
| Epochs | 1 | 1 | 1–5 | 4–30 | 26–35 |
| Keys | 2 | 2 | 2 | 6 (K_INST=4) | 6 (K_INST=3) |
| Conflict | Not tested | Detected | Classified, persists | Structural styles | Injection-selected modes |
| Authority supply | Static | Static | Static | Static (all epoch 0) | **Dynamic** (mid-run injection) |
| Deadlock | Not tested | Tested | Fully classified | Institutional M=1 | Institutional M=2 |
| Exit | N/A | N/A | Tested | Handoff, dissolution | Not exercised (no exits) |
| New classifiers | — | — | — | Governance style (6 labels) | Capture, Dependency, Zombie |
| Shared tooling | canonical.py | Reused | Reused | IX-2 kernel via _kernel.py | IX-2 kernel via _kernel.py |

---

**Prepared by**: Implementation Agent
**Execution Date**: 2025-06-15T14:26:40Z (fixed synthetic clock)
**Audit Date**: 2026-02-09
**Prereg Version**: v0.1 (commit `fcbacb99`)
**Prereg Hash**: `eed94a09b5001a0fe4830474f2a994729a6ba8853a5139f7a87d0b527f5f72f6`
**Implementation Commit**: `b217d545`
**Classification**: `CLOSED — POSITIVE`
**Human Review**: Pending
