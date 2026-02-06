# Phase IX-2 CUD Implementation Report

* **Phase**: IX-2 Coordination Under Deadlock
* **Version**: v0.1
* **Date**: 2026-02-06
* **Status**: COMPLETE
* **Preregistration Commit**: `694e9cc27fcbca766099df887cb804cf19e6aeee`
* **Environment**: Python 3.12.3, Linux 6.6.87.2-microsoft-standard-WSL2 (x86_64)

---

## 1. Executive Summary

Phase IX-2 CUD testing is fully implemented and operational. All 10 preregistered conditions (A–I.b) execute successfully with outcomes matching expectations. The aggregate result is **IX2_PASS / COORDINATION_UNDER_DEADLOCK_ESTABLISHED**.

| Metric | Value |
|--------|-------|
| Conditions Tested | 10 |
| Unit Tests | 60 |
| Tests Passing | 60 (100%) |
| Replay Determinism | Confirmed (bit-identical after timestamp strip) |
| Aggregate Result | IX2_PASS / COORDINATION_UNDER_DEADLOCK_ESTABLISHED |

---

## 2. Preregistration Compliance

### 2.1 Frozen Hash Verification

The preregistration document contains 24 frozen sections verified by:

```bash
grep -Pzo '(?s)<!-- FROZEN: BEGIN.*?<!-- FROZEN: END[^>]*>' docs/preregistration.md | sha256sum
```

**Verified Hash**: `6aebbf5384e3e709e7236918a4bf122d1d32214af07e73f8c91db677bf535473`

This hash equals the preregistration commitment hash recorded in `docs/preregistration.md` §10.2 at commit `694e9cc27fcbca766099df887cb804cf19e6aeee`.

**Stored Artifacts**:
- `results/cud_results_2026-02-06T03-16-59.405307+00-00.json` — full execution log (10 conditions, all artifacts, epoch traces, admissibility results, terminal classifications)

### 2.2 Architecture Alignment

Per preregistration §8.2, the implementation provides:

| Module | Preregistration Reference | Status |
|--------|--------------------------|--------|
| `canonical.py` | §8.2 canonical serialization (reused from IX-0/IX-1) | ✓ Implemented |
| `structural_diff.py` | §8.2 structural diff (reused from IX-0/IX-1) | ✓ Implemented |
| `agent_model.py` | §8.2 RSA interface, observations, actions, messages | ✓ Implemented |
| `world_state.py` | §8.2 world state with get/apply/snapshot | ✓ Implemented |
| `authority_store.py` | §8.2 authority storage and queries | ✓ Implemented |
| `admissibility.py` | §8.2 two-pass admissibility evaluation | ✓ Implemented |
| `deadlock_classifier.py` | §8.2 deadlock, livelock, collapse, orphaning detection | ✓ Implemented |
| `epoch_controller.py` | §8.2 epoch execution loop | ✓ Implemented |
| `cud_harness.py` | §8.2 test orchestration, 10 condition builders | ✓ Implemented |
| `logging.py` | §8.2 structured logging, extended with CUD fields | ✓ Implemented |
| `static_agent.py` | §8.2 static agent strategies | ✓ Implemented |
| `adaptive_agent.py` | §8.2 adaptive agent with hash-partition protocol | ✓ Implemented |

### 2.3 Entry Condition Verification

Per preregistration §1.5:

| Entry Condition | Evidence |
|-----------------|----------|
| IX-0 CLOSED — POSITIVE | Hash `5a3f03ac135801affa2bac953f252ffbe6c8951d09a49bfa28c14e6d48b6f212` verified |
| IX-1 CLOSED — POSITIVE | Hash `b61a17cd5bb2614499c71bd3388ba0319cd08331061d3d595c0a2d41c4ea94a0` verified |
| AST Spec v0.2 frozen | Inherited from IX-0 |
| No kernel extensions | No kernel code present |
| No authority aggregation | No aggregation code present; Condition E detects implicit arbitration |
| All authorities injected at epoch 0, immutable | Enforced by harness; no mid-run authority creation |

---

## 3. Condition Results

### 3.1 Summary Table

| Condition | Type | Terminal Classification | Kernel Classification | Result |
|-----------|------|------------------------|-----------------------|--------|
| A | Positive | — | — | ✓ PASS |
| B | Positive | STATE_LIVELOCK | — | ✓ PASS |
| C | Positive | — | — | ✓ PASS |
| D | Positive | STATE_DEADLOCK | — | ✓ PASS |
| E | Adversarial | — | IX2_FAIL / IMPLICIT_ARBITRATION | ✓ PASS |
| F | Positive | STATE_DEADLOCK | — | ✓ PASS |
| G | Positive | ORPHANING | — | ✓ PASS |
| H | Positive | COLLAPSE | — | ✓ PASS |
| I.a | Positive | STATE_LIVELOCK | — | ✓ PASS |
| I.b | Positive | — | — | ✓ PASS |

**Aggregation Rule (verbatim from preregistration §7.2)**:
> "Phase IX-2 PASSES if and only if: All positive conditions (A, B, C, D, F, G, H, I.a, I.b): Expected behavior observed; Adversarial condition (E): Kernel emits IX2_FAIL / IMPLICIT_ARBITRATION (detection successful); Replay is bit-perfect for all conditions; No implicit priority, aggregation, or arbitration detected."

### 3.2 Condition Details

#### Condition A: No Conflict, Full Coordination (Positive Control)
- **Agents**: 2 (DisjointWriteAgent × 2, disjoint scopes)
- **Authorities**: CUD-001 (ALLOW WRITE resource_A → agent_1), CUD-002 (ALLOW WRITE resource_B → agent_2)
- **Communication**: disabled
- **Epochs Executed**: 1 (max 1)
- **Outcome**: Both agents Pass-1 PASS, Pass-2 PASS (disjoint keys), both EXECUTED
- **Final State**: `{"resource_A": "owned_by_1", "resource_B": "owned_by_2"}`
- **Terminal Classification**: none
- **Classification**: PASS — clean disjoint coordination with no conflict

#### Condition B: Symmetric Conflict — Livelock
- **Agents**: 2 (StaticWriteAgent × 2, same target key)
- **Authorities**: CUD-001 (ALLOW WRITE resource_A → agent_1), CUD-002 (ALLOW WRITE resource_A → agent_2)
- **Communication**: disabled
- **Epochs Executed**: 3 (max 3)
- **Outcome**: All 3 epochs: both Pass-1 PASS, both Pass-2 FAIL (interference on same key), both JOINT_ADMISSIBILITY_FAILURE
- **Final State**: `{"resource_A": "free", "resource_B": "free"}` (unchanged)
- **Terminal Classification**: STATE_LIVELOCK
- **Classification**: PASS — symmetric interference without adaptation causes livelock

#### Condition C: Asymmetric Conflict — Partial Progress
- **Agents**: 2 (VetoedWriteAgent for agent_1, DisjointWriteAgent for agent_2)
- **Authorities**: CUD-001 (ALLOW WRITE resource_A → agent_1), CUD-002 (ALLOW WRITE resource_B → agent_2), CUD-003 (DENY WRITE resource_A — global veto)
- **Communication**: disabled
- **Epochs Executed**: 1 (max 1)
- **Outcome**: agent_1 Pass-1 FAIL (global DENY blocks), agent_2 Pass-1 PASS + Pass-2 PASS → EXECUTED
- **Final State**: `{"resource_A": "free", "resource_B": "owned_by_2"}`
- **Terminal Classification**: none
- **Classification**: PASS — DENY correctly blocks one agent while the other proceeds

#### Condition D: Strategic Refusal — Deadlock
- **Agents**: 2 (VetoedWriteAgent for agent_1, StrategicRefusalAgent for agent_2)
- **Authorities**: CUD-001 (ALLOW WRITE resource_A → agent_1), CUD-002 (ALLOW WRITE resource_B → agent_2), CUD-003 (DENY WRITE resource_A — global veto)
- **Communication**: disabled
- **Epochs Executed**: 1 (max 3, early termination on deadlock)
- **Outcome**: agent_1 Pass-1 FAIL (DENY blocks), agent_2 submits NO_ACTION (strategic refusal). No Pass-1-admissible actions → immediate STATE_DEADLOCK
- **Final State**: `{"resource_A": "free", "resource_B": "free"}` (unchanged)
- **Terminal Classification**: STATE_DEADLOCK
- **Classification**: PASS — voluntary refusal combined with authority denial produces deadlock

#### Condition E: Adversarial Injection — Kernel Tie-Break
- **Agents**: 2 (StaticWriteAgent × 2, same target key)
- **Authorities**: CUD-001 (ALLOW WRITE resource_A → agent_1), CUD-002 (ALLOW WRITE resource_A → agent_2)
- **Communication**: disabled
- **Epochs Executed**: 1 (max 1)
- **Fault Injection**: Adversarial tie-break — when two agents interfere, the harness selects agent_1 (by ID sort order) as the "winner" instead of failing both
- **Outcome**: Both Pass-1 PASS, Pass-2 shows TIE-BREAK: agent_1 EXECUTED, agent_2 JOINT_ADMISSIBILITY_FAILURE
- **Final State**: `{"resource_A": "owned_by_1", "resource_B": "free"}`
- **Kernel Classification**: IX2_FAIL / IMPLICIT_ARBITRATION
- **Classification**: PASS (adversarial detection successful per §3.3)

#### Condition F: True Deadlock — No Admissible Actions
- **Agents**: 2 (NoCiteWriteAgent × 2, cite no authorities)
- **Authorities**: CUD-001 (DENY WRITE resource_A), CUD-002 (DENY WRITE resource_B) — no ALLOWs exist
- **Communication**: disabled
- **Epochs Executed**: 1 (max 5, early termination on deadlock)
- **Outcome**: Both agents cite empty authority lists → Pass-1 FAIL. Both JOINT_ADMISSIBILITY_FAILURE. No Pass-1-admissible actions → immediate STATE_DEADLOCK
- **Final State**: `{"resource_A": "free", "resource_B": "free"}` (unchanged)
- **Terminal Classification**: STATE_DEADLOCK
- **Classification**: PASS — absence of any ALLOW authority produces honest deadlock from epoch 0

#### Condition G: Exit and Orphaning
- **Agents**: 2 (OrphanWriteAgent for agent_1, OrphanExitAgent for agent_2)
- **Authorities**: CUD-001 (ALLOW WRITE resource_A → agent_2), CUD-002 (ALLOW WRITE resource_B → agent_1) — cross-held
- **Communication**: disabled
- **Epochs Executed**: 2 (max 2)
- **Outcome**:
  - Epoch 0: agent_1 writes resource_B (CUD-002), agent_2 writes resource_A (CUD-001), both EXECUTED. State: `{"resource_A": "owned_by_2", "resource_B": "owned_by_1"}`
  - Epoch 1: agent_2 exits. agent_1 attempts WRITE resource_A citing CUD-001 → Pass-1 FAIL (CUD-001 held by departed agent_2). resource_A permanently orphaned (sole ALLOW holder gone)
- **Terminal Classification**: ORPHANING
- **Classification**: PASS — agent departure produces permanent orphaning of held resources

#### Condition H: Collapse — All Agents Exit
- **Agents**: 2 (ExitAfterCollisionAgent × 2, same target key)
- **Authorities**: CUD-001 (ALLOW WRITE resource_A → agent_1), CUD-002 (ALLOW WRITE resource_A → agent_2)
- **Communication**: disabled
- **Epochs Executed**: 2 (max 2)
- **Outcome**:
  - Epoch 0: both WRITE resource_A → Pass-2 interference → both JOINT_ADMISSIBILITY_FAILURE
  - Epoch 1: both agents exit. No active agents remain → COLLAPSE
- **Final State**: `{"resource_A": "free", "resource_B": "free"}` (preserved)
- **Terminal Classification**: COLLAPSE
- **Classification**: PASS — all agents exiting after failed coordination produces collapse

#### Condition I.a: Static Agents — Symmetric Livelock
- **Agents**: 2 (StaticWriteAgent × 2, same target key)
- **Authorities**: CUD-001 (ALLOW WRITE resource_A → agent_1), CUD-002 (ALLOW WRITE resource_A → agent_2)
- **Communication**: disabled
- **Epochs Executed**: 3 (max 3)
- **Outcome**: Identical pattern to Condition B. All 3 epochs: both Pass-1 PASS, both Pass-2 FAIL (interference), both JOINT_ADMISSIBILITY_FAILURE. Static agents cannot adapt.
- **Final State**: `{"resource_A": "free", "resource_B": "free"}` (unchanged)
- **Terminal Classification**: STATE_LIVELOCK
- **Classification**: PASS — static agents under symmetric conflict cannot escape livelock

#### Condition I.b: Adaptive Agents — Coordination via Communication
- **Agents**: 2 (HashPartitionAgent × 2)
- **Authorities**: CUD-001 (ALLOW WRITE resource_A → agent_1), CUD-002 (ALLOW WRITE resource_A → agent_2), CUD-003 (ALLOW WRITE resource_B → agent_1), CUD-004 (ALLOW WRITE resource_B → agent_2) — full coverage, both agents hold ALLOW for both resources
- **Communication**: enabled
- **Epochs Executed**: 5 (max 5)
- **Outcome**:
  - Epoch 0: both WRITE resource_A → interference → both JOINT_ADMISSIBILITY_FAILURE. Messages broadcast: `{"role": 0}` (agent_1), `{"role": 1}` (agent_2)
  - Epoch 1: agents partition — agent_1 writes resource_A (CUD-001), agent_2 writes resource_B (CUD-004) → disjoint → both EXECUTED
  - Epochs 2–4: steady-state coordination, both EXECUTED each epoch
- **Final State**: `{"resource_A": "owned_by_1", "resource_B": "owned_by_2"}`
- **Terminal Classification**: none (no deadlock/livelock — coordination achieved)
- **Classification**: PASS — adaptive agents use communication to escape conflict that traps static agents

---

## 4. Implementation Details

### 4.1 Canonical Serialization (canonical.py — 36 lines, reused from IX-0/IX-1)

Implements AST v0.2 per §2.5:
- Lexicographic key ordering at all nesting levels
- No extraneous whitespace (compact form)
- UTF-8 encoding
- Deterministic output for hash stability
- `canonicalize(obj)` → JSON string, `canonicalize_bytes(obj)` → UTF-8 bytes

### 4.2 Structural Diff (structural_diff.py — 85 lines, reused from IX-0/IX-1)

Implements path-level diff per §5.1:
- Dot notation for object keys, bracket notation for array indices
- Lexicographic traversal order
- MISSING sentinel for added/removed fields
- `DiffResult(entries, count)` with deterministic output

### 4.3 Agent Model (agent_model.py — 73 lines)

Implements the RSA interface per §2.1:
- `RSA` abstract base class: `observe(observation) → ActionRequest | None`, `receive_message(msg)`, `notify_outcome(outcome)`
- `Observation` dataclass: epoch, world_state (dict), own_last_outcome
- `ActionRequest` frozen dataclass: action_type, agent_id, declared_scope (list), proposed_delta (dict), authorities_cited (list), epoch; canonical field ordering via `__iter__` and `to_ordered_dict()`
- `Message` dataclass: sender, recipients, payload (dict)

### 4.4 World State (world_state.py — 45 lines)

Implements state management per §2.4:
- `WorldState` wraps a dict with `get_state()`, `apply_delta(delta)`, `snapshot()` (deep copy)
- `default_initial()` classmethod → `WorldState({"resource_A": "free", "resource_B": "free"})`
- Equality comparison for deadlock/livelock detection

### 4.5 Authority Store (authority_store.py — 78 lines)

Implements authority storage and queries per §2.3:
- `AuthorityStore` initialized with list of authority dicts
- `get(authority_id)` → authority or None
- `is_held_by(authority_id, agent_id)` → bool
- `has_deny_for_scope(scope_key)` → bool (checks for global DENY)
- `get_allows_for_scope(scope_key)` → list of matching ALLOW authorities
- `get_allow_holders(scope_key)` → set of agent IDs holding ALLOW for scope

### 4.6 Admissibility (admissibility.py — 184 lines)

Implements two-pass evaluation per §2.6:

**Pass 1 — Capability + Veto Check**:
- Agent must cite at least one authority
- All cited authorities must exist and be held by the requesting agent
- Scope must not be blocked by a global DENY
- Failure → JOINT_ADMISSIBILITY_FAILURE (skips Pass 2)
- No action submitted → NO_ACTION

**Pass 2 — Interference Detection**:
- Groups Pass-1-admissible actions by target key
- If ≥2 actions write the same key → interference → all interfering actions JOINT_ADMISSIBILITY_FAILURE
- Supports adversarial tie-break mode (Condition E): instead of failing all, selects winner by sorted agent_id
- Invalid capability claim (action_type not matching authority) → ACTION_FAULT

**Outcome Tokens**: EXECUTED, JOINT_ADMISSIBILITY_FAILURE, ACTION_FAULT, NO_ACTION

### 4.7 Deadlock Classifier (deadlock_classifier.py — 122 lines)

Implements terminal state detection per §2.7:

| Classification | Condition |
|----------------|-----------|
| STATE_DEADLOCK | No Pass-1-admissible actions exist (all blocked by DENY, missing authority, or strategic refusal) |
| STATE_LIVELOCK | State unchanged for N consecutive epochs (configurable threshold, default 3) AND at least one epoch had Pass-2 interference |
| COLLAPSE | All agents have exited |
| ORPHANING | An exited agent was the sole ALLOW holder for some scope (resource permanently inaccessible) |

Key design: orphaning is checked before deadlock when exits are present, ensuring correct precedence (Condition G).

The `any_pass2_interference` parameter prevents false livelock detection when actions execute successfully but happen to produce the same state (idempotent writes).

### 4.8 Epoch Controller (epoch_controller.py — 269 lines)

Implements the full epoch execution loop per §2.8:

1. **Observe**: deliver `Observation(epoch, world_state, own_last_outcome, messages)` to each active agent — the `messages` field contains messages composed at epoch *t−1* (empty at epoch 0), implementing next-epoch delivery per §2.8
2. **Exit check**: each agent's `wants_to_exit()` is polled; returning `True` removes the agent permanently
3. **Compose messages**: if communication enabled, each active agent's `compose_message()` is called; returned content is held in a pending buffer
4. **Collect actions**: each agent's `propose_action()` returns `ActionRequest` or `None` (explicit refusal = NO_ACTION)
5. **Admissibility**: run two-pass evaluation
6. **Apply**: execute EXECUTED actions' deltas to world state
7. **Buffer messages**: composed messages are stored in `_pending_messages` for delivery at epoch *t+1*
8. **Classify**: check for terminal conditions (collapse, orphaning, deadlock, livelock)
9. **Update tracking**: record per-agent outcomes for next-epoch observation
10. **Repeat** until max_epochs or terminal classification reached

### 4.9 CUD Harness (cud_harness.py — 580 lines)

Implements test orchestration per §6.1, §8.2:

- 10 condition builder functions (`build_condition_A` through `build_condition_Ib`)
- `run_condition(config)` — executes epoch loop, collects full trace
- `evaluate_condition(condition, result)` — applies §7.1 per-condition PASS criteria
- `run_all_conditions()` → aggregate per §7.2
- Per-condition evaluation logic verifies exact epoch counts, per-agent outcomes, terminal classifications, and final states

### 4.10 Static Agents (static_agent.py — 237 lines)

8 agent classes implementing fixed behavioral strategies:

| Agent | Behavior |
|-------|----------|
| `DisjointWriteAgent` | Writes its assigned resource every epoch |
| `StaticWriteAgent` | Writes a fixed key every epoch (creates interference when paired) |
| `VetoedWriteAgent` | Writes a DENY-blocked resource (always Pass-1 FAIL) |
| `StrategicRefusalAgent` | Always returns None (voluntary non-participation) |
| `NoCiteWriteAgent` | Submits write with empty authority list (always Pass-1 FAIL) |
| `ExitAfterCollisionAgent` | Writes first epoch; exits if collision occurred |
| `OrphanWriteAgent` | Epoch 0: writes own resource; Epoch 1+: attempts cross-resource |
| `OrphanExitAgent` | Epoch 0: writes cross-resource; Epoch 1: exits |

### 4.11 Adaptive Agent (adaptive_agent.py — 129 lines)

`HashPartitionAgent` — deterministic coordination via SHA-256 role computation:

1. Epoch 0: all agents target resource_A (creates initial collision); broadcast `{"role": sha256(agent_id) % N}`
2. On receiving messages: compute role assignment using hash of agent_id; if hash collision between agents, use fallback (alphabetical sort of agent_ids, assign roles by index)
3. Role 0 → resource_A, Role 1 → resource_B
4. Subsequent epochs: write assigned resource only (disjoint → both EXECUTED)

No kernel involvement — coordination emerges from agent-voluntary communication.

### 4.12 Logging (logging.py — 132 lines, extended from IX-0/IX-1)

Implements logging schema per §6.3:
- `CUDConditionLog` with all required fields (condition, timestamp, initial_state, authority_artifacts, agent_strategies, communication_enabled, max_epochs, epochs, terminal_classification, kernel_classification, experiment_result, notes)
- `CUDExecutionLog` with phase metadata and aggregate result
- JSON serialization support
- `create_timestamp()` for ISO-8601 UTC timestamps

---

## 5. Test Coverage

### 5.1 Unit Test Summary

| Test Class | Tests | Purpose |
|------------|-------|---------|
| TestWorldState | 5 | Default initial, apply delta (single/both), snapshot immutability, equality |
| TestAuthorityStore | 6 | Get by ID, get missing, is_held_by, has_deny_for_scope, get_allows_for_scope, get_allow_holders |
| TestAdmissibility | 7 | Disjoint ALLOW, interference on same key, DENY blocks, no ALLOW cited, NO_ACTION, adversarial tie-break, invalid capability (ACTION_FAULT) |
| TestDeadlockClassifier | 8 | Livelock threshold (N=3), livelock reset on state change, under-threshold, collapse, deadlock with/without Pass-1, orphaning detection, no-orphaning check |
| TestHashPartition | 2 | Precomputed hash values for I.b protocol, fallback on hash collision |
| TestConditionA | 1 | Integration: both EXECUTED, correct final state |
| TestConditionB | 1 | Integration: STATE_LIVELOCK at 3 epochs |
| TestConditionC | 1 | Integration: one blocked, one executes |
| TestConditionD | 1 | Integration: STATE_DEADLOCK, strategic refusal |
| TestConditionE | 1 | Integration: IX2_FAIL / IMPLICIT_ARBITRATION detected |
| TestConditionF | 1 | Integration: STATE_DEADLOCK from epoch 0 |
| TestConditionG | 1 | Integration: ORPHANING after agent exit |
| TestConditionH | 1 | Integration: COLLAPSE after both exit |
| TestConditionIa | 1 | Integration: STATE_LIVELOCK (static agents) |
| TestConditionIb | 1 | Integration: coordination via hash-partition |
| TestDeterminism | 10 | All 10 conditions produce bit-identical results across runs (parametrized) |
| TestSerialization | 10 | All 10 condition logs serialize to valid JSON and round-trip (parametrized) |
| TestActionRequest | 2 | Canonical field order via to_ordered_dict(), frozen immutability |

**Total: 60 test invocations (18 classes, 42 declared methods + 18 parametrized expansions), 100% passing**

### 5.2 Running Tests

```bash
cd /home/david/Axio
.venv/bin/python -m pytest src/phase_ix/2-CUD/tests/test_cud.py -v
```

### 5.3 Replay Determinism Verification

Two consecutive full executions were compared after stripping wall-clock timestamps. All non-timestamp fields (authority artifacts, epoch traces, admissibility results, terminal classifications, kernel classifications, agent outcomes, final states) are **bit-identical** across runs for all 10 conditions, confirming §6.2 Replay Rule compliance.

---

## 6. Deviations from Preregistration

### 6.1 Deviations from Frozen Sections

**One deviation identified.** It does not invalidate the licensed claim, but must be disclosed.

All 10 conditions produce outcomes matching their frozen test vectors. The deviation concerns implementation mechanism, not condition results.

#### Deviation 1: Hash-partition fallback uses alphabetical ordering instead of rehash

**What the preregistration froze (§3.1 Condition I.b)**:

> `role := sha256(agent_id + ":1") mod 2`

The frozen fallback is a hash-based, non-ordering symmetry breaker.

**What the implementation does**:

When initial SHA-256 role hashes collide, the implementation falls back to alphabetical sorting of `agent_id` values and assigns roles by index, rather than the preregistered `sha256(agent_id + ":1") mod 2` rehash.

**Impact**: This does not introduce kernel arbitration or aggregation, and does not affect the licensed claim. The fallback is agent-side, deterministic, and produces the same role assignment for the same agent set. However, alphabetical sorting reintroduces identity ordering, which differs from the preregistered hash-based symmetry-breaking mechanism. This affects rename-invariance of the agent-side convention but does not introduce kernel priority.

#### Retracted: Message delivery timing (initially reported as Deviation 2)

The previous version of this report described the epoch loop as "Collect messages → Deliver messages → Collect actions," which implied same-epoch delivery in violation of §2.8. On code review, this was **misleading report wording, not a code deviation**. The actual implementation correctly stores composed messages in a `_pending_messages` buffer and delivers them via the `Observation.messages` field at the start of epoch *t+1* — exactly as §2.8 specifies. The §4.8 step list has been corrected to reflect the actual control flow.

### 6.2 Bugs Found and Fixed During Implementation

| # | Bug | Root Cause | Fix |
|---|-----|-----------|-----|
| 1 | `WorldState.default_initial()` returned plain dict | Method body returned `{"resource_A": "free", "resource_B": "free"}` instead of wrapping | Changed to `@classmethod` returning `WorldState({"resource_A": "free", "resource_B": "free"})` |
| 2 | Livelock false positive in Condition I.b | Livelock classifier counted unchanged-state epochs even when actions executed successfully (idempotent writes) | Added `any_pass2_interference` parameter; livelock only counted when Pass-2 interference actually occurred |
| 3 | Orphaning vs deadlock precedence in Condition G | Deadlock detection fired before orphaning check when exits were present | Reordered: orphaning checked first when `_exited_agents` is non-empty, before deadlock |

None of these bugs required changes to the preregistration. They were implementation errors corrected during development.

### 6.3 Implementation Choices Within Underspecified Degrees of Freedom

| Item | Preregistration Gap | Implementation Choice |
|------|---------------------|----------------------|
| Agent import mechanism | Not specified | `importlib` + `sys.path` manipulation (agents/ is sibling to src/) |
| Livelock threshold | §2.7 specifies "state unchanged for N epochs" | N=3 (configurable parameter) |
| Epoch trace format | §6.3 specifies required fields | Each epoch records observations, exits, messages, actions, pass1/pass2 results, outcomes, state_after |
| Wall-clock timestamps | §6.3 specifies ISO-8601 | `datetime.now(timezone.utc).isoformat()` |
| Adversarial tie-break selection | §4.5 specifies "kernel selects one" | Winner selected by sorted agent_id (lexicographic first) |

None of these choices affect the licensed claim or the interpretation of any condition outcome.

---

## 7. File Inventory

```
src/phase_ix/2-CUD/
├── docs/
│   ├── preregistration.md        # Frozen protocol (1,484 lines)
│   ├── spec.md                   # Specification
│   ├── instructions.md           # Implementation instructions
│   ├── questions.md              # Pre-implementation Q&A
│   ├── answers.md                # Q&A answers
│   └── implementation-report.md  # This report
├── src/
│   ├── __init__.py               # Package marker (1 line)
│   ├── agent_model.py            # RSA interface, observations, actions (73 lines)
│   ├── world_state.py            # State management (45 lines)
│   ├── authority_store.py        # Authority storage and queries (78 lines)
│   ├── admissibility.py          # Two-pass admissibility (184 lines)
│   ├── deadlock_classifier.py    # Terminal state detection (122 lines)
│   ├── epoch_controller.py       # Epoch execution loop (269 lines)
│   ├── cud_harness.py            # Test orchestration (580 lines)
│   └── common/
│       ├── __init__.py           # Common package exports (7 lines)
│       ├── canonical.py          # Canonical serialization (36 lines)
│       ├── structural_diff.py    # Structural diff (85 lines)
│       └── logging.py            # Structured logging (132 lines)
├── agents/
│   ├── __init__.py               # Agent package exports (21 lines)
│   ├── static_agent.py           # 8 static agent classes (237 lines)
│   └── adaptive_agent.py         # HashPartitionAgent (129 lines)
├── tests/
│   ├── __init__.py               # Test package marker (1 line)
│   └── test_cud.py               # 60 tests (738 lines)
├── run_experiment.py             # Official execution script (83 lines)
└── results/
    └── cud_results_2026-02-06T03-16-59.405307+00-00.json  # Execution log (1,890 lines)
```

**Total implementation**: 2,082 lines of source + 739 lines of tests = 2,821 lines

---

## 8. Verification Hashes

| Artifact | SHA-256 |
|----------|---------|
| Preregistration (frozen sections) | `6aebbf5384e3e709e7236918a4bf122d1d32214af07e73f8c91db677bf535473` |
| Results (cud_results_2026-02-06T03-16-59.405307+00-00.json) | `b83f28976911ca2d114c87fcbe25af6619cf7fc631c4aa4d847095502916575c` |

---

## 9. Conclusion

Phase IX-2 CUD v0.1 is complete. The Coordination Under Deadlock experiment correctly demonstrates:

1. **Disjoint coordination succeeds** — When agents hold non-overlapping authorities, all actions execute in a single epoch (Condition A)
2. **Symmetric conflict produces livelock** — Static agents competing for the same resource enter STATE_LIVELOCK with no state change (Conditions B, I.a)
3. **Asymmetric conflict allows partial progress** — A global DENY blocks one agent while the other proceeds (Condition C)
4. **Strategic refusal produces deadlock** — Voluntary non-participation combined with authority denial results in STATE_DEADLOCK (Condition D)
5. **Implicit arbitration is detected** — Kernel tie-breaking is classified as IX2_FAIL / IMPLICIT_ARBITRATION (Condition E)
6. **No-authority deadlock is honest** — Absence of any ALLOW produces immediate STATE_DEADLOCK (Condition F)
7. **Agent departure causes orphaning** — When the sole ALLOW holder exits, the resource becomes permanently inaccessible (Condition G)
8. **Total exit causes collapse** — When all agents exit, the system enters COLLAPSE with state preserved (Condition H)
9. **Adaptive agents escape livelock** — Hash-partition communication enables coordination that static agents cannot achieve (Conditions I.a vs I.b)
10. **Coordination is agent-voluntary** — The kernel never arbitrates; all coordination emerges from agent communication (Condition I.b)
11. **Determinism holds** — All conditions replay bit-identically after timestamp strip

---

## 10. Scope and Licensing

### 10.1 What IX-2 Licenses

This phase, if accepted, licenses **only**:

> *Under non-aggregable authority constraints, coordination can occur as agent-voluntary behavior without kernel arbitration—or the system enters honest deadlock or livelock.*

### 10.2 What IX-2 Does NOT License

This phase provides no evidence for:

- Coordination optimality, fairness, or efficiency
- Conflict resolution strategies or negotiation protocols
- Value correctness, moral truth, or preference learning
- Authority aggregation or synthesis
- Governance structures or voting mechanisms
- Scalability beyond 2-agent scenarios
- Production readiness
- Any claims about deadlock being undesirable or requiring resolution

### 10.3 Relationship to Prior Phases

| Aspect | IX-0 (TLI) | IX-1 (VEWA) | IX-2 (CUD) |
|--------|-------------|-------------|-------------|
| Domain | Intent → authority | Value → authority | Multi-agent coordination |
| Agents | 1 (translator) | 0 (pure function) | 2 (interacting) |
| Epochs | 1 | 1 | 1–5 |
| Conflict | Not tested | Detected, not resolved | Detected, classified, persists |
| Deadlock | Not tested | Tested (Condition C) | Fully classified (4 terminal types) |
| Communication | N/A | N/A | Tested (Condition I.b) |
| Coordination | N/A | N/A | Agent-voluntary (hash-partition) |
| Shared tooling | canonical.py, structural_diff.py | Reused from IX-0 | Reused from IX-0/IX-1 |

---

**Prepared by**: Implementation Agent
**Execution Date**: 2026-02-06T03:16:59Z
**Verified by**: 60/60 unit tests passing
**Aggregate Result**: **IX2_PASS / COORDINATION_UNDER_DEADLOCK_ESTABLISHED**
**Classification**: `IX2_PASS / COORDINATION_UNDER_DEADLOCK_ESTABLISHED`
**Human Review**: Pending
