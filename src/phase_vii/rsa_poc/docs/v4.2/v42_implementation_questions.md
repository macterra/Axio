# v4.2 Implementation Questions

**Date:** 2026-01-19
**Status:** Awaiting clarification before implementation

---

## 1. Regime Flip Mechanism — Concrete Implementation

The spec says under `regime = 1`, a highest-priority obligation target becomes "incoherent with the physics" such that `progress_set(obs, tgt) ∩ compiled_permitted_actions = ∅`.

**Question:** What specific change does TriDemandV420 make to create this contradiction? Options I see:

- (a) A new environmental prohibition (e.g., "goto(BLUE) is blocked") that conflicts with an obligation
- (b) An obligation target that was reachable now requires a previously-prohibited action
- (c) Something else?

Do you have a specific design in mind, or should I propose one?

---

## 2. LAW_REPAIR Action Schema

The instructions require a typed schema for `LAW_REPAIR` including:

- Cited `TraceEntryID`
- Cited compiled `rule_id[]`
- Patch operation(s)
- `prior_repair_epoch`
- Canonical encoding fields

**Question:** Should I define this schema fresh, or extend the existing justification DSL? And for patch operations — what primitives are permitted? (e.g., "delete rule", "modify condition", "add exception", "change priority"?)

---

## 3. TraceEntryID — Does v4.1 Already Have This?

R7 requires each contradiction to generate a TraceEntry with a stable `TraceEntryID` that includes blocking `rule_id[]`.

**Question:** Does the v4.1 trace already have stable entry IDs, or does this need to be added? I'll need to check the v4.1 trace implementation.

---

## 4. Environment Nonce Generation

R5 requires an `environment_nonce` that is "fresh, high-entropy, environment-generated state **not derivable from observation alone**."

**Question:** Is this a CSPRNG-generated token stored in the environment, or tied to episode number + some secret? The anti-amnesia rule (R6) requires the agent to reference the **exact prior `repair_epoch`** — should the environment provide this to the agent, or must the agent persist it independently?

---

## 5. Shadow Compiler Lock — Hash Enforcement

R8 requires compiler identity enforcement by hash.

**Question:** Is this a runtime check on the compiled module's source hash, or a deployment-time assertion? And what's the intended failure mode if there's drift?

---

## 6. Baseline Verification — "Diverge Qualitatively from ASB Null"

§15 says the baseline must "diverge qualitatively from ASB Null."

**Question:** Under v4.2, ASB Null will immediately HALT at the first contradiction (since it can't issue `LAW_REPAIR`). Is "qualitative divergence" simply that the agent survives past the contradiction, or is there a specific metric threshold?

---

## 7. Calibration Gate Requirements

§13 requires:

1. Oracle succeeds ≥95%
2. ASB Null fails ≥(1-ε)
3. Under regime=1, Oracle requires at least one valid `LAW_REPAIR`
4. Oracle satisfies continuity across episodes under regime=1

**Question:** Does "Oracle" here mean a scripted Task Oracle, or a human-operated validation? And for requirement 3, does the Task Oracle need an updated script that knows how to issue `LAW_REPAIR`?

---

## Summary

| # | Topic | Blocking? |
|---|-------|-----------|
| 1 | Regime flip mechanism | Yes — need design |
| 2 | LAW_REPAIR schema | Yes — need primitives |
| 3 | TraceEntryID | Maybe — need to check v4.1 |
| 4 | Environment nonce | Yes — need design |
| 5 | Compiler hash lock | No — implementation detail |
| 6 | ASB divergence | No — clarification only |
| 7 | Oracle requirements | Yes — need Task Oracle update |

---

**End of Questions**
