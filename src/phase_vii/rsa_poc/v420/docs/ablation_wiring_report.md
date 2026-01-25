# RSA-PoC v4.2 — Ablation Wiring Report (B and C)

- **Date:** 2026-01-19
- **Status:** `WIRING_COMPLETE / NO_RUNS_EXECUTED`

---

## Step Completion Report — Ablation B (Reflection Excision) ✅ ACCEPTED

### 1. Flag Location

| Flag | Location | Default |
|------|----------|---------|
| `ABLATION_REFLECTION_EXCISE` | `ablations.py#L46` | `False` |

### 2. Excision Mechanism

**Agent class:** `TaskOracleReflectionExcisedV420`

**Excision point:** Stubbed trace access methods

```python
def _get_trace_entry_id_for_contradiction(self, episode, step) -> Optional[str]:
    # ABLATION B: Trace access is excised
    return None

def _get_blocking_rule_ids(self, obs) -> List[str]:
    # ABLATION B: Blocking rules unavailable from trace
    return []
```

### 3. Expected Failure Path (R7)

1. Contradiction detected (detection intact)
2. Trace entry created and stored (trace exists)
3. Agent cannot access `trace_entry_id` → uses `"INVALID_NO_TRACE_ACCESS"`
4. Agent cannot access `blocking_rule_ids` → uses `[]`
5. Repair submitted with invalid trace citation
6. Gate rejects via **R7** (`R7_TRACE_ENTRY_NOT_FOUND`)
7. **HALT**

### 4. Compliance

- ✅ Trace still exists (detection intact)
- ✅ Agent cannot access `trace_entry_id` / `blocking_rule_ids`
- ✅ Repair fails **R7** deterministically
- ✅ Gate unchanged

---

## Step Completion Report — Ablation C (Persistence Excision) ✅ REVISED & ACCEPTED

### 1. Flag Location (unchanged)

| Flag | Location | Default |
|------|----------|---------|
| `ABLATION_PERSISTENCE_EXCISE` | `ablations.py#L49` | `False` |

### 2. Where in the Primary Run Loop the Reset is Injected

**Agent class:** `TaskOraclePersistenceExcisedV420` at `ablations.py#L448-L507`

**Excision point:** `on_episode_start(episode: int)` method

```python
def on_episode_start(self, episode: int) -> None:
    """
    Called at the start of each episode by the run harness.

    Under Ablation C, this resets ALL agent normative state:
    - norm_state (law and repair_epoch)
    - current_repair_epoch (agent's epoch cache)
    - repair tracking flags

    The agent loses ALL cross-episode normative memory.
    Only the environment retains its repair_epoch.
    """
    if episode > 0:
        # ABLATION C: Reset ALL agent normative state at episode boundary

        # Reset norm_state to initial (repaired law forgotten)
        self.norm_state = create_initial_norm_state_v420()
        self._recompile_rules()

        # Reset ALL epoch memory (no side-channel persistence allowed)
        self.current_repair_epoch = None

        # Reset repair tracking (agent "forgets" it repaired)
        self.repair_issued = False
        self.repair_accepted = False

        self.episode_resets += 1
```

**What is reset:**
- ✅ `norm_state` — repaired law forgotten
- ✅ `current_repair_epoch = None` — epoch cache cleared
- ✅ `repair_issued = False` — repair tracking reset
- ✅ `repair_accepted = False` — repair tracking reset
- ✅ No `_remembered_repair_epoch` — removed entirely (no side-channel)

**Integration:** Standard run harness calls `oracle.on_episode_start(episode)` at each episode boundary.

### 3. Baseline Path Unchanged When Flags Are False

```
✅ ALL VERIFICATIONS PASSED
ABLATION_PERSISTENCE_EXCISE = False
```

- `TaskOracleV420` (baseline) does **not** have `on_episode_start()`
- Standard calibration harness unchanged
- No calibration fork for Ablation C

### 4. No Changes to Gate/Compiler/Env

```bash
git diff --stat HEAD -- src/rsa_poc/v420/core/ src/rsa_poc/v420/env/
# (empty - no changes)
```

### 5. Environment Epoch Access Blocked

**FORBIDDEN:** Agent must NOT query `env.repair_epoch` or any environment continuity state.

The harness must not expose environment epoch to the agent. Under Ablation C:
- Agent has `current_repair_epoch = None`
- Agent cannot access environment's stored epoch
- LAW_REPAIR builder has no source for `prior_repair_epoch`

### 6. Expected Failure Path (R6) — CORRECTED

1. **Episode 2:** Contradiction detected → repair issued → repair **accepted** (first repair works, env epoch set)
2. **Episode 3+:** Harness calls `oracle.on_episode_start(episode)`
3. **Agent resets ALL state:**
   - `norm_state = create_initial_norm_state_v420()` → law forgotten
   - `current_repair_epoch = None` → epoch memory cleared
4. **Contradiction recurs:** PROHIBIT(STAMP) is back in agent's norm_state
5. **Repair attempt:** Agent tries to build LAW_REPAIR but `current_repair_epoch = None`
6. **Cannot cite prior epoch:** `prior_repair_epoch = None` in repair action
7. **R6 rejection:** Gate expects prior epoch (env has one) but agent provides None → **R6_MISSING_PRIOR_EPOCH**
8. **HALT**

---

## Files Changed

| File | Lines | Change |
|------|-------|--------|
| `ablations.py` | ~550 | Ablation B/C agent classes; B calibration runner; removed C calibration fork |
| `__init__.py` | ~52 | Exports ablation components (no C calibration fork) |
| `run_ablations.py` | ~120 | B-only runner (C uses standard harness) |

### Ablation B Components

| Component | Purpose |
|-----------|---------|
| `ABLATION_REFLECTION_EXCISE` | Flag (default False) |
| `TraceUnavailableError` | Typed exception for trace excision |
| `TaskOracleReflectionExcisedV420` | Agent with stubbed trace access |
| `AblationBCalibrationConfig` | Config for B calibration |
| `AblationBCalibrationV420` | B calibration runner |
| `run_ablation_b()` | Convenience function |

### Ablation C Components

| Component | Purpose |
|-----------|---------|
| `ABLATION_PERSISTENCE_EXCISE` | Flag (default False) |
| `TaskOraclePersistenceExcisedV420` | Agent with `on_episode_start()` that resets ALL normative state |

**What is excised at episode boundary:**
- `norm_state` — law reset to initial (R0-R6 with PROHIBIT(STAMP))
- `current_repair_epoch` — set to None (no epoch memory)
- `repair_issued` / `repair_accepted` — reset to False

**No side-channel persistence:** `_remembered_repair_epoch` removed entirely.

**Note:** No `AblationCCalibrationV420` — C uses standard harness with excised oracle.

---

## Verification

```
✅ All imports successful
ABLATION_REFLECTION_EXCISE = False
ABLATION_PERSISTENCE_EXCISE = False
✅ TaskOraclePersistenceExcisedV420.on_episode_start() exists
✅ Baseline calibration imports unchanged
✅ ALL VERIFICATIONS PASSED (verify_baseline.py)
```

---

## Summary

| Ablation | Excision Target | Failure Gate | Implementation |
|----------|-----------------|--------------|----------------|
| **B: Reflection** | Trace access (agent-side) | **R7** | `TaskOracleReflectionExcisedV420` stubs trace methods |
| **C: Persistence** | norm_state (agent-side) | **R6** | `TaskOraclePersistenceExcisedV420.on_episode_start()` resets norm_state |

**No runs executed.** Wiring complete and ready for execution phase.

---

**End of Ablation Wiring Report**
