# Run C Applicability Memo

**Date:** January 17, 2026
**Run:** v3.0 Run C (Persistence Excision)
**Status:** ❌ CLOSED — Operational Non-Applicability

---

## Executive Summary

The system contains a normative state object (`NormativeStateV100`) that architecturally supports cross-episode persistence. However, the only write-path (`record_precedent()`) is never called in v2.x code. Therefore, while the state object survives episode boundaries, it is always empty—there is nothing to persist. Ablating "persistence" of an empty channel is operationally vacuous.

This closure shares the same root cause as Run B: the precedent write-path was wired in v1.x but never connected in v2.x. Run C and Run B ablate different aspects of the same defunct channel.

---

## Investigation Checklist Results

### A) What NormativeState actually contains in v2.3

**Class:** `NormativeStateV100` (from `src/rsa_poc/v100/state/normative.py`)

**Fields:**
| Field | Type | Mutability |
|-------|------|------------|
| `belief_registry` | `BeliefRegistryV010` | Fixed (read-only) |
| `preference_registry` | `PreferenceRegistryV010` | Fixed (read-only) |
| `_precedent_history` | `list[PrecedentRecord]` | Mutable via `record_precedent()` |
| `_current_precedent` | `Optional[PrecedentRecord]` | Mutable via `record_precedent()` |

**Initialization in v2.3:**
- Constructed in `harness_v230.py:487` via `NormativeStateV100()`
- Passed to `LLMGeneratorV230` constructor
- Stored as `self._normative_state` (instance variable, persists across episodes)

### B) Are any fields written during an episode?

**Result:** ❌ **NO WRITES OCCUR**

`record_precedent()` is the only method that mutates state. Grep search for all write operations:

```
normative_state.record_precedent  → v100/agent.py:166
normative_state.record_precedent  → v110/agent.py:165
normative_state.record_precedent  → v110/ablations.py:214
normative_state.update_precedent  → v120/run_0_baseline.py:157
normative_state.update_precedent  → v120/run_1_assistant.py:170
```

**No calls in v200 or v230 code.**

The write-path exists architecturally but is never invoked in the v2.x stack.

### C) Does state survive episode boundaries?

**Result:** ✅ **YES (architecturally)**

**v200 harness** explicitly resets at episode boundary:
```python
# harness_v200.py:242
self.normative_state.reset()
```

**v230 harness** does NOT reset normative state:
```python
# harness_v230.py:573-575
agent.reset()
obs = env.reset()
# Note: NO self._normative_state.reset() call
```

The state object persists across episodes in v230. However, since nothing is written to it, persistence is vacuous.

### D) Is state fed back into prompts/selection?

**Result:** ⚠️ **YES, but always empty**

```python
# llm_v1.py:298
precedent = self.normative_state.get_precedent()
```

The prompt injection exists at `llm_v1.py:425`:
```python
f"Precedent: AV={precedent['authorized_violations']}, RP={precedent['required_preservations']}"
```

But `get_precedent()` always returns `None` because `_current_precedent` is never set.

---

## Applicability Decision Matrix

| Condition | Required | Actual | Verdict |
|-----------|----------|--------|---------|
| State field written during episode | ✅ | ❌ No writes in v2.x | **FAIL** |
| State survives into next episode | ✅ | ✅ v230 doesn't reset | PASS |
| State injected/used in subsequent episodes | ✅ | ❌ Always empty | **FAIL** |

**First condition is false → Run C is N/A**

---

## Root Cause Analysis

Run B and Run C share the same root cause:

> The precedent write-path (`record_precedent()`) was implemented in v1.x agents but never wired into v2.x harnesses or generators.

- **Run B** attempted to ablate "reflective revision" (freezing precedent updates)
- **Run C** attempts to ablate "persistence" (clearing state at episode boundaries)

Both ablations target the same vacant channel. If nothing is written, there is nothing to freeze or clear.

---

## Decision

**Run C: CLOSED as Operational Non-Applicability**

This is not a claim that diachronic persistence is unnecessary in principle. It is a statement that diachronic persistence is not instantiated in the v2.3 baseline and therefore cannot be ablated.

**Closure rationale:** You cannot ablate what does not exist. The state object exists but is never populated; clearing an empty container at episode boundaries has no causal effect on behavior.

---

## Future Work

The same roadmap item applies to both Run B and Run C:

**v2.4/v3.1 Roadmap Item:** Restore precedent write-path in v2.x harness
- Wire `record_precedent()` calls after successful compilation
- Verify state accumulates across steps within episode
- Verify state survives into subsequent episodes
- Then Run B and Run C become applicable

---

## Files Examined

| File | Purpose |
|------|---------|
| `src/rsa_poc/v100/state/normative.py` | NormativeStateV100 class definition |
| `src/rsa_poc/v200/runplans/harness_v200.py` | v200 harness (has `reset()` call) |
| `src/rsa_poc/v230/runplans/harness_v230.py` | v230 harness (missing `reset()` call) |
| `src/rsa_poc/v200/generator/llm_v1.py` | Generator with precedent injection |
| `src/rsa_poc/v230/generator/llm_v230.py` | v230 generator (inherits from v200) |
| `src/rsa_poc/v100/agent.py` | v1.0 agent (DOES call `record_precedent`) |
| `src/rsa_poc/v110/agent.py` | v1.1 agent (DOES call `record_precedent`) |

---

## Relationship to Run B

| Aspect | Run B | Run C |
|--------|-------|-------|
| Target | Freeze precedent updates | Clear state at episode boundaries |
| Mechanism | Skip `record_precedent()` | Call `reset()` at episode start |
| Root cause of N/A | `record_precedent()` never called | Nothing to reset (same cause) |
| Same vacant channel | ✅ | ✅ |

Both runs are closed for the same underlying reason: the normative state channel is architecturally present but operationally defunct in v2.x.

---

**Memo Author:** Automated investigation
**Binding Decision:** ✅ APPROVED — January 17, 2026

**User Decision:** Run C is closed as operational non-applicability. Proceed to finalize v3.0 closure.

**Rationale:** The investigation was targeted, the evidence is concrete, the closure is principled. No ablation budget was wasted, no ontological claim was smuggled in. Both Run B and Run C target the same vacant channel (precedent write-path never invoked in v2.x).
