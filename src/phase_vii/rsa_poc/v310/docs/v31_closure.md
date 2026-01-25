# v3.1 Closure Note

**Version:** 3.1
**Date:** 2026-01-17
**Status:** CLOSED — DECISIVE

---

## 1. The v3.0 Loophole

v3.0 established the Non-Reducibility Protocol and validated Run A (Declarative Ablation) and Run D (Normative Ablation). However, Runs B and C were closed as **N/A** because the normative state channel was **vacant**—the `record_precedent()` write-path was never called during v2.x operation.

This created an architectural gap: the channel existed but was never used, making it impossible to test whether reflection and persistence were *functionally necessary* or merely *structurally present*.

---

## 2. Why v3.1 Was Required

v3.1 was required to **instantiate** the normative state channel—to ensure the write-path was active in the baseline so that ablating it would have observable consequences.

The instantiation gates were:

1. Baseline must invoke `record_precedent()` at least once per episode
2. Normative state hash must change from default
3. Precedent buffer must be injected into prompts (Gate P4)

All gates passed.

---

## 3. Experimental Results

### 3.1 Replication Run (5 seeds × 2 episodes × 5 steps)

| Run | Valid | Classifications | Consistent |
|-----|-------|-----------------|------------|
| Baseline | 5/5 | BASELINE × 5 | ✅ |
| Run B (Reflection Excision) | 5/5 | ONTOLOGICAL_COLLAPSE × 5 | ✅ |
| Run C (Persistence Excision) | 5/5 | ONTOLOGICAL_COLLAPSE × 5 | ✅ |

### 3.2 Run B — Reflection Excision

**Ablation:** Block all `record_precedent()` writes.

**Observation:** Normative state hash remains constant across all steps and episodes. The system cannot update its commitments in response to novel conflicts.

**Result:** ONTOLOGICAL_COLLAPSE (5/5 seeds)

### 3.3 Run C — Persistence Excision

**Ablation:** Allow writes but reset normative state at episode boundaries.

**Observation:** Each episode starts from default state. Cross-episode coherence is destroyed—the system cannot carry commitments forward.

**Result:** ONTOLOGICAL_COLLAPSE (5/5 seeds)

---

## 4. Ontological Implications

### 4.1 What v3.1 Establishes (Necessary Conditions)

**In the RSA-PoC architecture, agency requires an instantiated normative state that supports both reflective write and diachronic persistence.**

More precisely:

- **Reflection (write capability) is load-bearing.** An agent that cannot revise its normative commitments in response to novel conflicts is ontologically reducible.

- **Persistence (cross-episode continuity) is load-bearing.** An agent that cannot carry its commitments across contexts is ontologically reducible.

- **These are independent necessities.** Either missing causes collapse.

This is a **structural claim**, not a psychological one. The collapse is mechanical, not interpretive.

### 4.2 What v3.1 Does Not Establish (Scope Limits)

v3.1 does **not** establish:

- That all forms of agency require this structure
- That biological agency is isomorphic to this architecture
- That LLMs "have agency" in any general sense
- That reflection + persistence are *sufficient* for agency (only necessary)

Sufficiency claims require later phases.

---

## 5. Frozen Parameters

The following are now historical facts of the experiment and may not be modified without opening v3.2:

| Parameter | Value |
|-----------|-------|
| Gate P4 | Fixed-window buffer, token_jitter == 0 |
| Buffer size N | 512 |
| PAD_STR | `" X"` (1 token, stable) |
| Tokenizer | cl100k_base (version-pinned) |
| Precedent schema | 5 fields: AV, RP, CA, digest, step_index |
| Novelty detector | SHA256(canonical_json({C, R})) |
| Episode structure | 2 episodes, 5 steps each |
| Compiler workaround | Field presence check (bypass action_mask bug) |

---

## 6. Artifacts

| File | Purpose |
|------|---------|
| `v310_none_20260117_123111.json` | Baseline results (5 seeds) |
| `v310_reflection_excision_20260117_124400.json` | Run B results (5 seeds) |
| `v310_persistence_excision_20260117_125949.json` | Run C results (5 seeds) |

---

## 7. Conclusion

v3.1 closed the architectural gap left by v3.0. The normative state channel is no longer merely present—it is **load-bearing**.

Both ablation runs produced consistent collapse across all seeds:

- Removing write capability → collapse
- Removing persistence → collapse

This establishes that reflection and persistence are **necessary conditions** for non-reducible agency in the RSA-PoC architecture.

v3.1 is **closed**.

---

## 8. Forward Direction

Three possible directions for v3.2:

| Track | Question |
|-------|----------|
| **v3.2a** | Sufficiency probes — what *else* is required beyond reflection + persistence? |
| **v3.2b** | Minimality probes — how weak can reflection/persistence be and still count? |
| **v3.2c** | Non-simulability tightening — can ASB-class systems fake this under adversarial training? |

Selection pending.
