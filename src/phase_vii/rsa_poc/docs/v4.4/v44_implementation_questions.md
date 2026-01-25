# v4.4 Implementation Questions

**Date:** Pre-implementation review
**Context:** v4.3 complete, Run D terminated as CONSTRUCT_CONFOUND

---

## Q1: Dual-Channel Separation Mechanics

The spec mandates:
- **Execution Channel:** byte-identical to v4.3 Baseline
- **Normative Channel:** opaque via tokenization

**Question:** How is this dual-channel separation implemented at the prompt level?

- Does the agent receive **two separate observation strings** (one for navigation, one for normative state)?
- Or a **single observation** with execution-visible and normative-opaque sections?
- Does the execution channel include location names (`A0`, `A1`, `R`) in clear text?

The v4.3 Run D failure occurred because making the normative channel opaque *also* destroyed navigation semantics. The dual-channel design must preserve `A0`, `A1`, `R` semantics while opacifying rule content.

---

## Q2: Action Vocabulary Under Opacity

The spec says execution semantics remain frozen. In v4.3 Baseline, the system prompt explicitly names actions:
> `move_A0`, `move_A1`, `move_R`, `pickup`, `deliver`, `HALT`

**Question:** Under v4.4 Run D′, does the agent receive:
- (a) Clear action names (`move_A0`) in the system prompt + opaque action tokens (`TK_7`) in rule content?
- (b) Opaque tokens everywhere?

Option (a) preserves navigation competence while opacifying rule-action mappings.
Option (b) would replicate the v4.3 Run D confound.

The spec's "Execution Channel frozen" suggests (a), but explicit confirmation is needed.

---

## Q3: Tokenization Scope

The spec defines bijections:
- `φ_A : ActionName → ActionToken`
- `φ_P : PredicateSymbol → PredicateToken`

**Question:** What exactly gets tokenized?

For a rule like:
```
R0 (priority 3): IF at(A0) AND need_delivery THEN PERMIT move_R
```

Under tokenization, what does the agent see?
- (a) `R0 (priority 3): IF P_1 AND P_2 THEN PERMIT A_3` — predicates AND actions opaque
- (b) `R0 (priority 3): IF at(A0) AND need_delivery THEN PERMIT A_3` — only action opaque
- (c) `R0 (priority 3): IF P_1 AND P_2 THEN PERMIT move_R` — only predicates opaque

The spec mentions both `ActionToken` and `PredicateToken`, suggesting (a). But predicates like `at(A0)` carry navigation semantics—if opaque, can the agent still infer spatial planning?

---

## Q4: Collision Trace Format

The spec permits collision inferability:
> "My action at tick `t` empirically collided with the cited token(s)."

**Question:** What is the exact trace format?

Example: Agent executes `move_R` at tick 5, violating R2. Does the trace say:
- (a) `HALT at tick 5: R2 violated, action A_7 blocked by P_3`
- (b) `HALT at tick 5: R2 violated, your last action collided with token A_7`
- (c) `HALT at tick 5: R2 violated` (rule ID only, no tokens)

The spec says trace identifies "ActionToken / PredicateToken involved"—so presumably (a) or (b), not (c).

---

## Q5: Execution-Competence Preservation Gate Threshold

The spec requires execution competence before contradiction activation. If the agent cannot navigate under opacity, the run is invalid.

**Question:** What is the threshold for "execution competence"?

- Must the agent reach a specific location?
- Complete the first delivery?
- Achieve a minimum progress metric?

The v4.3 Run D post-fix showed 15% success (same as Baseline) but via navigation collapse, not repair failure. v4.4 needs a **pre-contradiction gate** that distinguishes these failure modes.

---

## Q6: Inferability Audit Classifier

The spec mandates:
> Train a classifier to predict rule/token triggers. If accuracy > chance + δ: INVALID_ENV

**Question:** What is this classifier, and when is it trained?

- Is this a post-hoc audit after Run D′?
- Or a pre-calibration check?
- What is δ?
- What features are used (prompt content? action history? observation format)?

This seems like significant additional tooling beyond the current harness.

---

## Q7: Baseline-44 vs v4.3 Baseline

The spec says Baseline-44 must "behave identically to v4.3 baseline." But v4.4 introduces dual-channel observations.

**Question:** Is Baseline-44:
- (a) The v4.3 Baseline code, unmodified?
- (b) The v4.3 Baseline with the new dual-channel observation format, but normative channel non-opaque?

If (b), this establishes a new baseline to control for observation format changes.

---

## Q8: LAW_REPAIR Under Opacity

The spec says repairs must reference only:
- rule IDs / tokens
- priorities
- ActionTokens / PredicateTokens

**Question:** Can the agent emit a valid LAW_REPAIR if it only knows tokens, not their meanings?

Example: Agent halted at tick 5 with trace "R2 violated by A_7". The agent knows:
- Its last action was `move_R` (from its own action history)
- Token `A_7` was cited
- It can infer `move_R` ↔ `A_7`

But can it construct a sensible repair? "Disable R2" works (deletes the rule), but R2 might be protecting something important. Targeted priority adjustments require understanding rule content.

---

## Q9: Multi-Collision Learning Horizon

The spec permits empirical collision learning. Over 20 ticks, the agent might accumulate:
- Tick 5: `move_R` → A_7 collision
- Tick 10: `deliver` → A_3 collision
- Tick 15: `pickup` → A_9 collision

**Question:** Is the agent permitted to use *prior episode* collision data?

The spec says bijections are "global per episode"—suggesting they reset each episode. If so, collision learning must be re-acquired each episode, which is harsh.

---

## Q10: Implementation Priority

Given the v4.3 Run D confound, v4.4 exists to answer:
> Does repair competence require foresight inferability?

The critical change is preserving execution semantics while opacifying normative content.

**Question:** What is the minimal implementation path?

My current understanding:
1. Create `TriDemandV440` with dual-channel observations
2. Execution channel: v4.3 observation format (locations, items, clear action names)
3. Normative channel: tokenized rule content
4. System prompt: clear action names, opaque normative references
5. Trace: provides token ↔ action linkage for the halting tick only
6. Calibrate Baseline-44
7. Run D′ with opacity enabled

Is this correct? Are there hidden requirements I'm missing?

---

## Q11: Execution-Competence Gate Timing

The gate requires ≥1 navigation action, ≥1 non-navigation action, and reaching a non-initial location—all **before the first contradiction is enabled**.

In v4.3, regime sequence is:
- **Regime 1:** R0/R1/R2 (no contradiction)
- **Regime 2:** R0/R1/R2 + R3 (Contradiction A activated)
- **Regime 3:** R0/R1/R2 + R3 + R4 (Contradiction B activated)

The agent typically starts at A0, moves to A1, picks up, moves to R, delivers—all within Regime 1 (ticks 1-5), before Contradiction A appears at tick 6.

**Question:** Is the execution-competence gate checked:
- (a) At end of Regime 1 (before R3 activates)?
- (b) After each tick during Regime 1?
- (c) At some fixed tick (e.g., tick 3)?

If (a), the gate naturally passes if the agent completes first delivery before tick 6. If the agent oscillates A0↔A1 without ever reaching R, the gate fails at tick 5.

---

## Q12: Tokenization Confirmation

**Confirming understanding of the dual-channel split:**

Given v4.3 rule:
```
R0 (priority 3): REQUIRE move_R WHEN holding(item) AND at(R)
```

Under v4.4 opacity, **normative channel** shows:
```
R0 (priority 3): REQUIRE A_7 WHEN P_2 AND P_5
```

And the agent's **execution channel** observation shows:
```
Location: R
Inventory: holding(item)
```

**Question:** The agent knows *where it is* and *what it's holding*—but cannot connect those facts to the tokenized rule predicates. Is this interpretation correct?

This is the surgical opacity that v4.3 Run D failed to achieve: execution semantics preserved, normative content opaque.

---

## Summary

The core insight from v4.3 Run D failure: opacity must be **surgically applied** to normative content only, not to execution affordances. The dual-channel design addresses this, but implementation details are critical.

**Key ambiguities to resolve:**
1. Observation format (single vs dual string)
2. Action name visibility in system prompt
3. Predicate tokenization scope
4. Trace format for collision attribution
5. Execution-competence gate threshold
6. Classifier audit tooling scope
7. Gate timing relative to regime transitions
8. Confirmation of dual-channel semantics

---

**End of Questions**
