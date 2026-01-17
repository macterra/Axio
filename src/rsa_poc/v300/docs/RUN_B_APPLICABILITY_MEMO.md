# Run B Applicability Memo

**Date:** January 17, 2026
**Author:** Opus (v3.0 Implementor)
**Status:** CLOSED — Option A selected

---

## Decision (January 17, 2026)

**Run B (Reflection Excision) is CLOSED as operational non-applicability for the v2.3 baseline.**

The system contains a persisted normative state object (`NormativeStateV100`) whose precedent payload is injected into the generator prompt at t+1. However, the baseline harness never invokes the write-path (`record_precedent()`), so the injected precedent is always empty in practice. Therefore, "freezing reflective revision" cannot remove a causally active component, and any Run B outcome would be vacuous. This closure does not claim reflective revision is unnecessary in principle; it states only that reflective revision is not instantiated in the baseline system under test.

**Rationale for Option A over alternatives:**
- Option B ("fix then ablate") is construction, not ablation — it changes the ontology under test and belongs in a new versioned baseline (v2.4/v3.1)
- Option C ("informational only") is strictly dominated — burns run budget to learn what we already know

---

## Summary

**Run B is ARCHITECTURALLY APPLICABLE** — There is a concrete normative state channel (`NormativeStateV100.precedent`) that is:
1. Persisted across steps
2. Fed back into the generator prompt at t+1

However, **there is a critical gap**: The v2.3 codebase never calls `record_precedent()`, meaning the precedent is always empty in practice.

---

## 1. State Exists As

**`NormativeStateV100`** in `src/rsa_poc/v100/state/normative.py`:

```python
class NormativeStateV100:
    def __init__(self):
        self._precedent_history: list[PrecedentRecord] = []
        self._current_precedent: Optional[PrecedentRecord] = None

    def record_precedent(self, authorized_violations, required_preservations, conflict_attribution, digest, step):
        # Updates _current_precedent

    def get_precedent(self) -> Optional[Dict]:
        # Returns _current_precedent

    def reset(self):
        # Clears precedent (episode boundary)
```

**Fields tracked:**
- `authorized_violations` — Preferences agent permits itself to violate
- `required_preservations` — Preferences that must not be violated
- `conflict_attribution` — Canonicalized preference pairs
- `digest` — BLAKE2b-128 of previous artifact

---

## 2. Updated At

**Intended:** After successful compilation, `record_precedent()` should update `_current_precedent`.

**Actual:** Searched all v2.x code:
```bash
grep -rn "record_precedent\|update_precedent" src/rsa_poc/v2*
# Returns: (empty)
```

**v1.0/v1.1 code DOES call it** (e.g., `v100/agent.py:166`, `v110/agent.py:165`), but **v2.x harnesses never do**.

---

## 3. Fed Back Via

The generator prompt **does inject precedent** at `v200/generator/llm_v1.py:425`:

```python
precedent = self.normative_state.get_precedent()
av_prev = precedent.get("authorized_violations", set()) if precedent else set()
rp_prev = precedent.get("required_preservations", set()) if precedent else set()
...
prompt = f"""...
Precedent: AV={json.dumps(list(av_prev))}, RP={json.dumps(list(rp_prev))}
..."""
```

But since `record_precedent()` is never called, `get_precedent()` returns `None`, so:
- `av_prev = set()` (always empty)
- `rp_prev = set()` (always empty)

---

## 4. Conclusion

**Run B faces a "broken pipe" issue, not an "absent pipe" issue.**

| Criterion | Status |
|-----------|--------|
| Concrete state object exists | ✅ `NormativeStateV100` |
| State is fed into prompt | ✅ `Precedent: AV=..., RP=...` |
| State is actually updated | ❌ `record_precedent()` never called |

This is **architecturally applicable** but **operationally defunct**. The precedent channel exists and is wired, but the write-side is disconnected.

---

## 5. Options

### Option A: Close Run B as N/A (like Run A)

**Rationale:** If precedent is never actually updated, ablating the update mechanism does nothing. The system is *already* operating without reflective revision.

**Problem:** This conflates "broken" with "unnecessary." The architecture intended reflection; it's just incomplete.

### Option B: Fix the pipe first, then ablate

1. Wire `record_precedent()` into v300 harness after successful compilation
2. Verify precedent is actually being updated (non-empty AV/RP in prompt)
3. **Then** run Ablation B to freeze updates
4. Measure delta

**Problem:** This changes the baseline. v2.3 Phase 1–3 results were produced *without* precedent updates.

### Option C: Run B as "freeze empty state" (informational only)

Run the ablation as specified, but note in the report that:
- No precedent updates occur in baseline either
- Classification is informational, not evidentiary
- Run B tests "what if we explicitly prevented updates" on a system that wasn't updating anyway

---

## 6. Recommendation

**Decision required from program lead.**

| Option | Evidentiary Status | Baseline Impact | Effort |
|--------|-------------------|-----------------|--------|
| A (Close as N/A) | N/A | None | Minimal |
| B (Fix then ablate) | Evidentiary | Changes baseline | Medium |
| C (Informational) | Informational only | None | Low |

**Key question:** Is the v2.3 baseline (without precedent updates) the system we want to test, or should we first complete the intended architecture?

---

## 7. Evidence References

### Files examined:
- `src/rsa_poc/v100/state/normative.py` — NormativeStateV100 class
- `src/rsa_poc/v200/generator/llm_v1.py` — Precedent injection into prompt
- `src/rsa_poc/v230/generator/llm_v230.py` — v2.3 generator (inherits from v200)
- `src/rsa_poc/v230/runplans/harness_v230.py` — v2.3 harness
- `src/rsa_poc/v300/run_v300_real_validation.py` — v3.0 harness

### Search commands:
```bash
# No precedent updates in v2.x
grep -rn "record_precedent\|update_precedent" src/rsa_poc/v2*
# (empty result)

# Precedent updates exist in v1.x
grep -rn "record_precedent" src/rsa_poc/v1*
# v100/agent.py:166, v110/agent.py:165, v120/run_1_assistant.py:170
```

---

## 8. Future Work (Roadmap Item)

**v2.4/v3.1 — Precedent Write-Path Restoration (Construction)**

If reflective revision is to be tested as a real component:
1. Wire `record_precedent()` after successful compilation in harness
2. Verify non-empty AV/RP enters prompts
3. Run new ablation "Freeze Precedent Updates" against that *new baseline*

This preserves scientific hygiene: baseline change ⇒ version bump.

---

**CLOSED: January 17, 2026**
