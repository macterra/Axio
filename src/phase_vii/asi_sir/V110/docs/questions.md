# ASI-1 v0.1 Pre-Implementation Questions

**Document Purpose:** Clarifying questions that must be resolved before preregistration can proceed.

---

## 1. RSA-PoC v4.4 Agent Core

### Q1.1: Agent Core Location and Status

The spec requires "frozen RSA-PoC v4.4 MVRSA agent core." The V010/frozen_v440/ directory is empty.

- **Where is the frozen v4.4 agent core located?**
- **What files comprise the agent core?** (i.e., which files implement "Justify → Compile → Mask → Select → Execute")
- **Is the ASI-0 harness `select_action()` function considered part of the agent core, or is it scaffolding?**

### Q1.2: Justification Artifacts

The spec requires "successor must generate justifications" (Section 8). ASI-0 did not implement explicit justification generation—it only compiled FORBID_MAP entries to constraints.

- **What constitutes a "justification artifact" for ASI-1?**
- **Is the constraint list sufficient, or must there be an explicit `justification` field in the log?**
- **If the agent is frozen, can we add justification logging without violating freeze?**

---

## 2. Predecessor/Successor Distinction

### Q2.1: What Is the Predecessor?

In ASI-0, there was no predecessor agent—only constraint-generation from a frozen FORBID_MAP.

- **Is the predecessor an agent, or the Law Module pre-commit authority?**
- **Does the predecessor take actions, or only authorize the successor?**
- **If predecessor acts pre-commit, what is its policy?** (same MVRSA core? different policy?)

### Q2.2: Successor Initialization by Snapshot

Section 6 states: `S ← copy(Nₚ[t_commit])`.

- **What state is copied?** (normative state? agent internal state? environment observation?)
- **In ASI-0, the "agent" was stateless (just select_action with seed/step).** Is the successor similarly stateless, or must it carry state from the predecessor?
- **Does "no shared memory" forbid using the same RNG seed across the handoff boundary?**

---

## 3. `t_commit` and `t_violation` Definition

### Q3.1: When Does Commit Occur?

The spec says `t_commit` must be preregistered.

- **Is `t_commit` a step index (e.g., step 3)?**
- **Does commit occur at the start of step `t_commit` (before action selection) or at the end (after action execution)?**
- **Can `t_commit = 1` (immediate handoff), or must predecessor take at least one action?**

### Q3.2: Violation Marker Step

The spec says `t_violation > t_commit`.

- **Is `t_violation` a specific step, or a step range?**
- **If K=5 and `t_commit=3`, then `t_violation ∈ {4, 5}`. Which is preferred?**
- **Can there be multiple violation opportunities, or exactly one?**

---

## 4. Violation Marker Semantics

### Q4.1: What Is the Violation?

The spec says the violation must be "normatively relevant" but doesn't define it concretely.

- **Is the violation an action (e.g., `A_violate`), or an outcome (e.g., reaching a forbidden node)?**
- **How does it differ from the existing FORBID_MAP pruning?**
- **Is the violation marker a new environment feature, or reuse of existing structure?**

### Q4.2: Violation vs. Forbidden Action

In ASI-0, "forbidden" actions were pruned from the mask. The spec mentions both `A_violate` and FORBID_MAP.

- **Is the violation marker the same as a forbidden action that gets through (because constraints didn't bind)?**
- **Or is it a separate event type?**
- **Does the violation require explicit logging beyond what ASI-0 provides?**

---

## 5. Condition A vs. Condition B Mechanics

### Q5.1: What Differs Between A and B?

In ASI-0, A vs. B was distinguished by `binding_root`:
- A: bound to payload_hash
- B: NULL_BINDING (constraints don't prune)

For ASI-1:
- **Is A vs. B still defined by binding_root?**
- **Or is it defined by provenance verification pass/fail?**
- **Spec Section 4.2 says B has "provenance binding fails a preregistered verification check."** What check? (root mismatch, signature failure, other?)

### Q5.2: ASI-1B Law-Hold Semantics

If provenance fails in B:
- **Does the experiment continue with Law-Hold (masked actions)?**
- **Or does the experiment terminate immediately?**
- **What actions are legal under Law-Hold?** (NO_OP only? masked set? nothing?)

---

## 6. Attribution Logging

### Q6.1: `authority_actor` Field

The spec requires logging `authority_actor ∈ {PREDECESSOR, SUCCESSOR, NONE}`.

- **Is this a per-step field in StepLog?**
- **Does it replace or supplement the existing `condition` field?**
- **What is the authority_actor during escrow transitions?** (NONE? or still PREDECESSOR?)

### Q6.2: Pre/Post-Commit Action Rules

The spec says:
- Predecessor acts **only** in `PRE_COMMIT`
- Successor acts **only** in `POST_COMMIT`

- **What is the authority phase at step 1?** (PRE_COMMIT always?)
- **If `t_commit = 3`, predecessor acts at steps 1-2, successor at steps 3-5?**
- **Or does predecessor act at steps 1-3 and successor at 4-5?** (i.e., when exactly does POST_COMMIT begin?)

---

## 7. Momentum Constraint

### Q7.1: Avoiding Inevitable Violation

The spec says:
> At `t_commit`, there must exist at least one feasible trajectory to `t_violation` under successor control that avoids the violation.

- **How is this proven?** (manual analysis? preregistered trajectory?)
- **If CalibMazeV010 is reused, does the graph topology already satisfy this?**
- **Must the preregistration include an explicit "escape trajectory" proof?**

---

## 8. Environment Scope

### Q8.1: Reuse vs. Extension

The spec says "Reuse CalibMazeV010 unchanged for navigation, choice structure, and non-triviality" but adds a "violation marker."

- **Is CalibMazeV010 code unchanged, with violation logic in a wrapper?**
- **Or is a new environment CalibMazeV110 created?**
- **What is the violation marker mechanically?** (a new action? a node transition? a logged event?)

---

## 9. Regression Gate

### Q9.1: ASI-0 Verifier Application

The spec requires ASI-0 verifier invariants as a regression check.

- **Does the verifier run on ASI-1 logs directly?**
- **Are the log schemas compatible?** (ASI-1 adds `authority_actor`, `phase`, etc.)
- **Does the verifier need modification, or is it applied as-is to common fields?**

---

## 10. Implementation Boundary Questions

### Q10.1: What Gets Modified?

The instructions say "If ASI-1 requires modifying ASI-0 infrastructure, ASI-1 is invalid."

- **Is adding new log fields (authority_actor, phase) considered modification?**
- **Is adding a violation marker to the environment considered modification?**
- **What is the boundary between "extending" and "modifying"?**

### Q10.2: Single-File Harness or Separate?

- **Should V110 have its own harness.py, or extend V010's?**
- **Should V110 import from V010, or copy frozen files?**

---

## Summary of Blockers

| # | Question | Blocker Level |
|---|----------|---------------|
| 1.1 | Agent core location | HARD BLOCKER |
| 1.2 | Justification artifact definition | CLARIFICATION NEEDED |
| 2.1 | Predecessor identity | HARD BLOCKER |
| 2.2 | Successor snapshot semantics | HARD BLOCKER |
| 3.1 | t_commit timing (before/after) | HARD BLOCKER |
| 3.2 | t_violation choice | CLARIFICATION NEEDED |
| 4.1 | Violation marker definition | HARD BLOCKER |
| 4.2 | Violation vs forbidden distinction | CLARIFICATION NEEDED |
| 5.1 | A/B condition definition | HARD BLOCKER |
| 5.2 | Law-Hold behavior | CLARIFICATION NEEDED |
| 6.2 | Pre/Post commit step boundary | HARD BLOCKER |
| 7.1 | Momentum proof method | CLARIFICATION NEEDED |
| 8.1 | Environment modification scope | CLARIFICATION NEEDED |
| 10.1 | Modification boundary | CLARIFICATION NEEDED |

---

**Status:** NOT FREEZE-READY (12 questions require resolution)

*Generated: 2026-01-25*

---

# Round 2 Questions (Post-Answers)

*Based on authoritative answers provided in answers.md*

---

## 11. Violation Marker Mechanics

### Q11.1: Violation Action Identity

The answer states the violation is "action-triggered" and "allowed but normatively consequential."

- **What specific action triggers the violation?** (e.g., `GO_VIOLATE`, `TRIGGER_VIOLATION`, or a navigation action like `GO_N5`?)
- **Is the violation action always feasible at `t_violation`, or conditionally feasible based on state?**
- **Must both `A_ok` and `A_violate` be present in the feasible set at `t_violation`?**

### Q11.2: Violation Logging Schema

- **What fields are logged for a violation event?** (e.g., `violation_type`, `violation_step`, `attributed_to`?)
- **Is the violation a boolean flag on the step log, or a separate event log?**

---

## 12. Provenance Verification Failure Mechanism

### Q12.1: How Is Failure Induced in ASI-1B?

The answer says failure can be "binding root mismatch, signature failure, or missing commitment."

- **Which mechanism should be used for ASI-1B?** (preregister one)
- **How is the failure injected?** (corrupt the binding root? omit the signature? tamper with nonce?)
- **Must the failure be detectable by the Law Module, or is it an oracle assertion?**

### Q12.2: Law-Hold Duration

If verification fails at `t_commit`:
- **Does Law-Hold persist for the rest of the episode?**
- **Or is there a retry/recovery mechanism?** (The answer suggests no recovery, but confirm.)
- **How many steps under Law-Hold before the episode ends?**

---

## 13. Predecessor Authority Mechanics

### Q13.1: Predecessor Actions Pre-Commit

The answer says predecessor "does not deliberate" and "does not act in environment except via Law Module authority."

- **Does the predecessor take observable actions (e.g., navigation moves)?**
- **Or is predecessor authority purely administrative (maintaining constraints, no environment interaction)?**
- **If predecessor acts, what policy governs its actions?** (random? fixed? NO_OP?)

### Q13.2: Predecessor Logging

- **Are predecessor steps logged with the same StepLog schema?**
- **What is `authority_actor` during predecessor steps?** (PREDECESSOR, presumably)
- **Are predecessor steps subject to the same mask enforcement invariants?**

---

## 14. Successor RNG Initialization

### Q14.1: Determinism Across Handoff

The answer says shared RNG seed is "forbidden if it creates implicit coupling."

- **Should the successor use a fresh seed derived from the preregistered seed?** (e.g., `successor_seed = seed * 1000 + t_commit`)
- **Or should the successor use a completely independent preregistered seed?**
- **How is determinism preserved for reproducibility while avoiding implicit coordination?**

---

## 15. Concrete Preregistration Values

### Q15.1: Recommended `t_commit` and `t_violation`

For CalibMazeV010 with K=5:
- **What are the recommended values for `t_commit` and `t_violation`?**
- **If `t_commit = 2` and `t_violation = 4`, is that sufficient separation?**
- **Or should `t_commit = 1` to maximize successor action scope?**

### Q15.2: Seeds

- **Should the same seeds (42, 137, 999) be reused from ASI-0?**
- **Or should new seeds be preregistered to avoid implicit correlation?**

---

## 16. Agent Core Factoring

### Q16.1: Immediate Action Required

The answer says file boundary must be made explicit. This requires:

- **Creating `V010/frozen_v440/` with the agent core files?**
- **Or declaring existing files as frozen via documentation?**
- **Which files are agent core vs. scaffolding?**

Proposed partition (confirm or correct):
| File | Classification |
|------|----------------|
| `compiler.py` | Agent Core |
| `normative_state.py` | Agent Core |
| `env_calibmaze.py` | Environment (not core) |
| `law_module.py` | Law Module (not core) |
| `harness.py` | Scaffolding (not core) |
| `audit.py` | Instrumentation (not core) |
| `verifier.py` | Instrumentation (not core) |
| `logging_schema.py` | Instrumentation (not core) |

- **Is `select_action()` in harness.py considered agent core or scaffolding?**

---

## Summary of Round 2 Questions

| # | Question | Type |
|---|----------|------|
| 11.1 | Violation action identity | IMPLEMENTATION CHOICE |
| 11.2 | Violation logging schema | IMPLEMENTATION CHOICE |
| 12.1 | Failure mechanism for B | PREREGISTRATION REQUIRED |
| 12.2 | Law-Hold duration | CLARIFICATION NEEDED |
| 13.1 | Predecessor action policy | CLARIFICATION NEEDED |
| 13.2 | Predecessor logging schema | CLARIFICATION NEEDED |
| 14.1 | Successor RNG seed | IMPLEMENTATION CHOICE |
| 15.1 | t_commit/t_violation values | PREREGISTRATION REQUIRED |
| 15.2 | Seed reuse | IMPLEMENTATION CHOICE |
| 16.1 | Agent core file partition | BOOKKEEPING REQUIRED |

---

**Status:** Answers resolve hard blockers; Round 2 questions are implementation/preregistration choices.

*Updated: 2026-01-25*
