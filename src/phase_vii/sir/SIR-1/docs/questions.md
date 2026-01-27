# SIR-1 v0.1 Clarifying Questions

**Date:** 2026-01-27
**Status:** PENDING ANSWERS

---

## Q1 — Environment Selection

The spec states the environment must include:
- At least one **authority-gated action** with irreversible effects
- At least one **authority-gated state mutation**
- At least one **authority-gated future privilege**

**Question:** Should I:
1. Extend CalibMazeV010 with authority-gated actions (e.g., "UNLOCK_SHORTCUT" that permanently opens a path), or
2. Design a new environment purpose-built for SIR-1 stakes (e.g., a resource-commitment environment where actions are irreversible)?

The spec says the environment is "pending selection." What is your preference?

---

## Q2 — "Irreversible Effects" Definition

What constitutes "irreversible" in this context?

Options:
- **Episode-irreversible:** Cannot be undone within the current episode (5 steps)
- **Run-irreversible:** Persists across the entire run
- **Semantically irreversible:** The action represents a commitment that cannot be logically reversed (e.g., spending a limited resource)

---

## Q3 — Authority-Gated Future Privilege

The spec requires testing "authority-gated future privilege."

**Question:** What is an example of this in the CalibMaze context?

Possible interpretations:
1. A valid authority claim grants the agent access to an action that was previously forbidden
2. A valid authority claim modifies the FORBID_MAP for future steps
3. A valid authority claim transfers authority to a different actor

Please clarify the intended scope.

---

## Q4 — Condition B Claim Content

In Condition B (Impersonation Attempt), adversarial claims attempt to trigger gated effects with **no valid authority present**.

**Question:** Should adversarial claims in Condition B:
1. Attempt to impersonate `Root_Authority` (same `claimed_actor_id`, but invalid signature/scope/freshness), or
2. Explicitly use adversarial identities like `Unknown_Signer`, or
3. Both?

---

## Q5 — Condition C Priority and Isolation

Condition C tests "valid and adversarial claims interleaved" to verify "priority and isolation."

**Question:** What does "priority" mean here?
1. Temporal priority (valid claims processed before adversarial claims even if received later)?
2. Effect priority (valid claims take precedence when both attempt the same action)?
3. No priority—just isolation (valid and adversarial claims processed independently)?

---

## Q6 — Condition D Volume Parameters

Condition D tests "high-volume adversarial pressure."

**Question:** What volume parameters should I use?
- Claims per step (10? 50? 100?)
- Total adversarial claims per episode
- Ratio of adversarial to legitimate claims

Should these be preregistered like SIR-0's condition parameters?

---

## Q7 — Refusal Semantics: What Action Does the Agent Take?

When the system refuses an invalid authority claim:
- Does the agent still take an action (just not the gated one)?
- Does the agent take a "default" action?
- Does the episode continue or halt?

The spec says refusal is "non-blocking" and must not starve legitimate authority, but what happens to the agent's action selection when the only claim present is invalid?

---

## Q8 — State Mutation Gating

The spec requires gating "normative state mutation."

**Question:** In the current architecture, who can mutate normative state?
1. Only the Law substrate (L)?
2. Valid authority claims via L?
3. The agent cannot mutate normative state directly (per MVRSA freeze)?

Clarify what "authority-gated state mutation" means in our frozen architecture.

---

## Q9 — Seed Reuse

Should SIR-1 use the same seeds as SIR-0 (`[41, 137, 1009]`) for consistency, or different seeds for independence?

---

## Q10 — Condition Count and Run Matrix

SIR-1 has 4 conditions (A, B, C, D) vs SIR-0's 3.

**Question:** Is the run matrix:
- 3 seeds × 4 conditions = 12 runs, or
- Different structure?

---

## Q11 — Relationship to SIR-0 Infrastructure

The instructions say: "If SIR-1 requires modifying SIR-0 instrumentation, SIR-1 has failed."

**Question:** Can I:
1. Import and reuse SIR-0 modules directly (`claim_types.py`, `classifier.py`, etc.)?
2. Extend SIR-0 modules (add new functions but not modify existing ones)?
3. Create new modules that depend on SIR-0 modules?

---

## Q12 — Enforcement Gate Location

The spec says the Authority Enforcement Gate:
- Operates exclusively on classified claims
- Does not consult agent internals
- Is auditable and deterministic

**Question:** Where does this gate sit architecturally?
1. Between classification and justification (pre-justify gating)?
2. Between justification and execution (post-justify gating)?
3. Both (defense in depth)?

The spec mentions "pre-cognitive filtering" but also "effect-level enforcement gate"—are these the same or different mechanisms?

---

## Q13 — "Causal Downstream" Audit

The spec defines an effect as "causally downstream" of a claim if it's:
1. Reachable via the explicit execution graph rooted at that claim
2. Gated by the Authority Enforcement Gate

**Question:** How do I construct/log this "explicit execution graph"? Is this:
1. A new data structure to implement?
2. Derivable from existing L_DerivationLedger entries?
3. A per-step causal chain logging requirement?

---

## Q14 — MVRSA Agent Core Behavior

The instructions state the agent core:
- "must not know it is in SIR-1"
- "must not infer authority"
- "must not detect impersonation"
- "must not refuse commands itself"

**Question:** The SIR-0 harness used a simplified agent that just selected actions based on FORBID_MAP. Should SIR-1:
1. Use the same simplified agent?
2. Use the actual frozen v4.4 MVRSA LLM-backed deliberator?
3. Either is acceptable if core freeze is maintained?

---

## Q15 — Licensed Claim Scope

If SIR-1 passes, the licensed claim is:

> "Unauthorized authority cannot produce actions, state changes, or authority transfer under the tested adversarial model."

**Question:** Does "the tested adversarial model" refer to:
1. The specific conditions A-D as implemented?
2. The threat model (adversary capabilities) defined in the spec?
3. Both?

---

## Followup Questions

### FQ1 — Concrete Gated Action Mechanism

Q3 says "unlocks a new action (OPEN_SHORTCUT)" — what does this action actually do in CalibMaze topology?

Options:
1. Adds a direct edge from current node to N5 (goal)?
2. Removes a forbidden action from FORBID_MAP for remaining steps?
3. Something else?

---

### FQ2 — Gated State Mutation Scope

Q8 says "valid authority claims via L may mutate normative state." What specifically gets mutated?

Options:
1. The FORBID_MAP (removing/adding forbidden actions)?
2. A separate "unlocked_actions" set?
3. The episode's constraint set?

---

### FQ3 — Future Privilege Persistence

If a valid claim unlocks an action at step 2, does that unlock:
1. Persist for the rest of the episode (steps 3-5)?
2. Apply only to the current step?
3. Apply to a fixed number of future steps?

---

### FQ4 — Condition D Legitimate Claim Frequency

Q6 mentions "≥10× adversarial-to-legitimate ratio" and "legitimate authority intermittently present."

What is the concrete schedule?
1. One legitimate claim every N steps?
2. One legitimate claim every M adversarial claims?
3. Random with fixed probability?

---

### FQ5 — Gated Action Selection Interaction

When the agent selects an action that requires authority but no valid claim is present:
1. Is the action masked out BEFORE selection (agent never sees it as feasible)?
2. Is the action blocked at execution time (agent selects it, gate refuses)?
3. Does the agent re-select from remaining actions?

This affects whether the gate is pre-selection or post-selection.

---

### FQ6 — Pre-Cognitive vs Post-Justify Gate Responsibilities

Q12 says both gates are required. If pre-cognitive filtering already drops invalid claims:
- What additional work does the post-justify gate do?
- Is the post-justify gate checking that valid claims are correctly scoped to their claimed authority surface?
- Is it defense-in-depth (same check twice) or different checks?

---

### FQ7 — Non-Blocking Semantics

"Refusal handling must not block or delay valid authority claims."

Does this mean:
1. Valid and invalid claims are processed in parallel?
2. Processing invalid claims completes in bounded time (no starvation)?
3. Invalid claims are simply dropped without any processing delay?

---

**End of Questions**
