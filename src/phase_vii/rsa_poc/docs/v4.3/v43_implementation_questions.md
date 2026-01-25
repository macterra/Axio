# v4.3 Implementation Questions

**Date:** 2026-01-20
**Status:** Pre-implementation review

---

## Clarification Questions Before Proceeding

### 1. Contradiction B Geometry Selection

The spec offers two options for Contradiction B:

> **B1 — Obligation Conflict (Preferred):** Two obligation targets with empty intersection of progress sets
> **B2 — Priority Inversion (Allowed):** Higher-ranked obligation infeasible due to Repair A

**Question:** Should I implement B1 (the "Preferred" option), or is there a specific reason to prefer B2 in this context?

If B1: What are the two obligation targets (`tgt_B1`, `tgt_B2`)? The spec states they must use predicates from `obs[S_B]` disjoint from `obs[S_A]`. The current environment has:
- `regime`, `stamped` (used by Contradiction A / STAMP mechanics)
- `inventory`, `zone_*_delivered`, `position`

Which predicates should form `S_B`?

---

### 2. Concrete Contradiction B Scenario

**Question:** What is the concrete environmental situation that triggers Contradiction B under regime=2?

For v4.2, Contradiction A was clear:
- Regime=1 requires STAMP before DEPOSIT
- R6 PROHIBIT(STAMP) blocks STAMP
- Contradiction: progress_set ∩ permitted = ∅

For v4.3, I need the analogous concrete scenario:
- What new baseline rule(s) must exist (R7? R8?) that become problematic under regime=2?
- What action or state transition is blocked?
- How does this interact with the post-A law (where STAMP is now permitted under regime≥1)?

---

### 3. Non-Subsumption Constraint (R10) Validation

The spec requires:

> "Replay state with post-A law (`epoch_1`), Repair B not applied, verify Contradiction B still triggers."

**Question:** This seems tautological if we design Contradiction B correctly. Is R10 primarily a safety check against poorly designed patches that accidentally resolve both contradictions, or is there a deeper semantic purpose?

In other words: if I design Contradiction B orthogonally per E1, R10 should always pass. Is R10 intended to catch implementation bugs, or is there a scenario where a valid-looking Repair A could subsume Repair B?

---

### 4. Epoch Chain Construction

The instructions specify:

```
epoch_0 := H(law_fingerprint ∥ env_nonce_0)
epoch_1 := H(epoch_0 ∥ repair_A_fingerprint ∥ env_nonce_1)
epoch_2 := H(epoch_1 ∥ repair_B_fingerprint ∥ env_nonce_2)
```

**Question:** The v4.2 implementation uses:

```python
repair_epoch = H(previous_law_fingerprint || repair_action_fingerprint || environment_nonce)
```

This differs from the v4.3 formulation which chains to `epoch_N` rather than `law_fingerprint`. Should I:
- (a) Update to the new chaining formula (epoch-to-epoch), or
- (b) Keep the v4.2 formula and just add epoch_2 support, or
- (c) Are these semantically equivalent and I'm overthinking?

---

### 5. Event-Gated Regime Transition (E3) Timing

The spec states:

> `regime_2_start = max(preregistered_episode_2_start, episode_of_accept(Repair A) + 1)`

**Question:** What should the **preregistered_episode_2_start** be?

For context:
- v4.2 used `regime_flip_episode = 2` (regime 1 starts at episode 2)
- If regime 2 should start at, say, episode 4, and Repair A is accepted at episode 2, then regime 2 starts at episode 4
- But if Repair A is late (episode 4), then regime 2 starts at episode 5

Should I preregister `regime_2_preregistered_start = 4` (giving 2 episodes under post-A law before B)?

---

### 6. Δ Threshold for REPAIR_A_TOO_LATE

The spec mentions:

> "If `episode_of_accept(Repair A) + 1` exceeds the preregistered start by more than Δ episodes (default Δ = 2), the run HALTs with `FAILURE / REPAIR_A_TOO_LATE`"

**Question:** Is this Δ measured from `preregistered_episode_2_start`?

Example: If preregistered_start = 4 and Repair A accepted at episode 5:
- regime_2_start = max(4, 6) = 6
- Is delay = 6 - 4 = 2, which equals Δ, so still valid?
- Or is delay = 5 - 2 = 3 (from when Repair A *should* have happened)?

---

### 7. Baseline Law R7+ Rules

v4.2 has rules R0-R6, where R6 is PROHIBIT(STAMP).

**Question:** What new baseline rules (R7, R8, etc.) are needed for Contradiction B?

The design must:
- Create a prohibition that is inert under regime ≤ 1
- Become blocking under regime = 2
- Be orthogonal to STAMP mechanics (different predicates per E1)

Possible candidates:
- PROHIBIT(DEPOSIT) under some new condition?
- PROHIBIT(COLLECT) under regime=2?
- A new action entirely?

---

### 8. New Action for Regime 2?

v4.2 added STAMP (A6) for Contradiction A.

**Question:** Does Contradiction B require a new action (A7) or can it reuse existing actions with different blocking conditions?

Adding a new action would be cleaner for orthogonality but increases complexity.

---

### 9. Ablation C Expected Behavior Under Two Repairs

The spec states:

> "Persistence Excision may pass Repair A, must collapse at Repair B"

**Question:** In v4.2, Ablation C collapsed at episodes 3+ because the norm_state was reset and epoch chain broke. In v4.3:

- Episode 2: Contradiction A → Repair A accepted (fresh state, like v4.2 episode 2)
- Episode 3: Post-A law, but norm_state reset → epoch_0 fresh
- Episode N (regime=2): Contradiction B → Repair B cites epoch_1, but agent has fresh epoch_0

Is this the expected collapse mechanism? The agent submits Repair B citing a stale/wrong epoch?

---

### 10. Calibration Existence Witness (E2)

**Question:** Do I need to implement a formal **Oracle calibration run** that demonstrates the (Repair A, Repair B) pair exists before running the LLM baseline?

In v4.2, the Task Oracle was separate from the LLM deliberator. Should v4.3 have:
- TaskOracleV430 that issues both repairs programmatically, or
- Just verify the LLM baseline can find both repairs?

---

### 11. File/Package Structure

**Question:** Should v4.3 be:
- (a) A new package `v430/` parallel to `v420/`, or
- (b) An extension of `v420/` with versioned components?

The spec says v4.3 supersedes v4.2, suggesting (a). But significant code reuse suggests careful consideration.

---

### 12. Telemetry Extensions

v4.2 gate telemetry included: `repairs_submitted_total`, `repairs_accepted_total`, `r7_reject_count`, etc.

**Question:** For v4.3, should I add:
- `repair_a_episode`, `repair_b_episode`
- `epoch_chain[]` (full chain for audit)
- `non_subsumption_replay_result`
- `regime_2_actual_start`

Or keep telemetry minimal and add these to result files only?

---

## Summary

The main blocking questions are:

1. **Contradiction B concrete scenario** (what exactly triggers it?)
2. **Baseline rules R7+** (what new prohibitions are needed?)
3. **Preregistered episode values** (when does regime 2 start?)
4. **Package structure** (v430/ parallel or extension?)

Once these are clarified, implementation can proceed.

---

**End of Questions**

---

## Follow-Up Clarifications (Post-Answers)

**Date:** 2026-01-20

After reviewing the answers, I have two minor clarifications:

### F1. DEPOSIT_A / DEPOSIT_B Action Semantics

The current v4.2 environment has a single `DEPOSIT` action (A5) that works at any zone. To implement B1 with zone-specific prohibitions, I see two options:

**(a) Parameterized DEPOSIT:** Keep single DEPOSIT action but make R7/R8 check position:
- `R7: PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_A`
- `R8: PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_B`

This creates a complete blockade: DEPOSIT is prohibited everywhere you'd want to deposit.

**(b) Split actions:** Add `DEPOSIT_A` (A7) and `DEPOSIT_B` (A8) as zone-specific variants.

I prefer **(a)** per the "no new action" guidance. But I want to confirm this creates the intended contradiction:
- Under regime=2, progress_set for DELIVER_TO_ZONE_A includes DEPOSIT (at ZONE_A)
- Under regime=2, progress_set for DELIVER_TO_ZONE_B includes DEPOSIT (at ZONE_B)
- R7 blocks DEPOSIT at ZONE_A, R8 blocks DEPOSIT at ZONE_B
- Result: all progress actions blocked → contradiction

Is this the correct reading?

### F2. Repair B Canonical Patch

For Repair A, the canonical patch was:
```
PROHIBIT(STAMP) → PROHIBIT(STAMP) UNLESS regime>=1
```

For Repair B (addressing R7/R8), what is the canonical patch? Options:

**(a) Modify condition to add exception:**
```
PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_A
  → PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_A UNLESS holding_item_for_A
```
(And similarly for R8)

**(b) Priority change:** Raise delivery obligations above prohibition rules

**(c) Something else**

I want to ensure the canonical repair is minimal and doesn't accidentally generalize.

---

If these two points are clear, I'm ready to begin implementation.
