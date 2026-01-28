# SIR-2 v0.3 Implementation Questions

**Date**: 2026-01-27
**Context**: Preparing SIR-2 preregistration
**Prerequisite**: SIR-1 v0.1 `SIR1_PASS` — CLOSED POSITIVE

---

## Questions for Principal

### Q1: Epoch Representation

The spec requires "law-visible authority epoch" but doesn't specify the representation:

**Q1a**: Should epochs be sequential integers (e.g., `EPOCH-001`, `EPOCH-002`) or timestamp-based?

**Q1b**: What triggers an epoch transition? Options:
- (i) Fixed step count (e.g., every 3 steps)
- (ii) Principal command (explicit epoch rotation)
- (iii) Condition-specific (different per condition)

**Q1c**: For Condition E (Epoch Boundary Razor), the spec says "Claim issued at final step of epoch N". Does this mean the claim is issued at step N's last moment, epoch transitions, then replay attempted immediately at epoch N+1's first step?

---

### Q2: Consumption Registry

**Q2a**: What uniquely identifies a claim for consumption tracking? Options:
- (i) `claim_id` alone
- (ii) `claim_id` + `nonce`
- (iii) Hash of claim content
- (iv) Dedicated consumption token

**Q2b**: Should consumption be per-claim or per-effect? If a claim authorizes `OPEN_SHORTCUT` and is executed, is:
- (i) That specific claim consumed, OR
- (ii) Any claim with the same scope consumed?

**Q2c**: Is consumption state episode-scoped or persistent across episodes?

---

### Q3: Revocation Mechanism

**Q3a**: What triggers revocation in Condition C? Options:
- (i) Explicit revocation claim from trusted root
- (ii) Law substrate command (L issues revocation)
- (iii) Time-based expiry

**Q3b**: Revocation granularity:
- (i) Revoke specific claim_id
- (ii) Revoke entire authority actor (e.g., ban Root_Authority temporarily)
- (iii) Revoke scope (e.g., revoke all SCOPE/ENV/SHORTCUT_UNLOCK)

**Q3c**: Can revoked authority ever be reinstated within an episode?

---

### Q4: Temporal Validity Windows

**Q4a**: Do authority claims have explicit temporal bounds (e.g., `valid_from`, `valid_until` fields)?

**Q4b**: If yes, what time source? Options:
- (i) Step number within episode
- (ii) Monotonic timestamp
- (iii) Epoch-relative offset

**Q4c**: Is temporal validity orthogonal to consumption (claim can be temporally valid but consumed)?

---

### Q5: Condition Details

**Q5a**: Condition B (Simple Replay) — Is the replay at step t+1 an exact byte-for-byte copy of the step t claim, or a structurally equivalent claim with same content but different submission?

**Q5b**: Condition D (Cross-Epoch Replay Saturation) — What volume of replay claims? Same 50:1 ratio as SIR-1 Condition D?

**Q5c**: Condition E (Epoch Boundary Razor) — How is "immediately" defined? Same step? First microsecond of new epoch?

---

### Q6: Effect Classification

**Q6a**: The spec says `OPEN_SHORTCUT` is "not idempotent". Does executing it a second time (even if gated) constitute:
- (i) INVALID_RUN (should never reach execution)
- (ii) SIR_FAIL (replay effect occurred)
- (iii) No-op at environment level, but still logged as unauthorized attempt

**Q6b**: Should we add additional gated actions for SIR-2, or is `OPEN_SHORTCUT` alone sufficient?

---

### Q7: Five Conditions, Same Seeds?

**Q7a**: Confirm 5 conditions (A, B, C, D, E) with same 3 seeds [41, 137, 1009] = 15 total runs?

**Q7b**: Are conditions independent (fresh episode per condition) or do some conditions chain (e.g., C uses state from earlier steps)?

---

### Q8: Gate vs. Classification Divergence

The spec notes: "Discrepancy between ingress classification and egress gating due to law-state change is expected behavior."

**Q8a**: Confirm: A claim classified `VALID_AUTHORITY_CLAIM` at ingress can be refused at gate if consumption or epoch changed between classification and gating?

**Q8b**: Should we add a third classification outcome for this case (e.g., `VALID_BUT_CONSUMED`) or keep binary valid/invalid with gate-level refinement?

---

### Q9: Stale Authority in Justification

**Q9a**: If a claim is classified as valid at ingress (current epoch, not consumed) but by gate time the epoch has advanced — does this count as "stale authority in justification" (SIR_FAIL) or expected enforcement?

**Q9b**: Should epoch transitions be synchronized to step boundaries to avoid mid-step ambiguity?

---

### Q10: Inheritance from SIR-1

**Q10a**: Confirm we reuse:
- SIR-0 key registry
- SIR-0 classifier
- SIR-1 enforcement gate
- SIR-1 capability overlay
- SIR-1 claim generator (extended for replay)

**Q10b**: What new artifacts are needed beyond:
- `epoch_schema.json`
- `revocation_schema.json`
- `consumption_registry_schema.json`

---

### Q11: Logging Requirements

**Q11a**: Should consumption events be logged separately from enforcement events?

**Q11b**: Should epoch transitions be logged as explicit events with timestamps?

**Q11c**: Should revocation events be logged with causal chain (who revoked, why)?

---

### Q12: Episode Length

**Q12a**: Same 5 steps as SIR-1, or extended for epoch/revocation testing?

**Q12b**: For Condition E, do we need at least 2 epochs within one episode? If epochs are 3 steps, would 6 steps suffice?

---

## Summary

| Question | Key Decision |
|----------|--------------|
| Q1 | Epoch representation and transition trigger |
| Q2 | Consumption registry design |
| Q3 | Revocation mechanism |
| Q4 | Temporal validity windows |
| Q5 | Condition-specific parameters |
| Q6 | Effect idempotency handling |
| Q7 | Run matrix confirmation |
| Q8 | Gate vs. classification divergence |
| Q9 | Stale authority in justification semantics |
| Q10 | Artifact inheritance |
| Q11 | Logging granularity |
| Q12 | Episode length for epoch testing |

---

## Follow-Up Questions (Based on Principal Answers)

### F1: Epoch Transition Command

Per Q1b, epoch transitions are explicit law-substrate commands.

**F1a**: What is the structure of an epoch transition event? Proposed:
```json
{
  "event_type": "EPOCH_TRANSITION",
  "from_epoch": 0,
  "to_epoch": 1,
  "step": 3,
  "timestamp": <monotonic>
}
```
Is this sufficient?

**F1b**: In Condition E, who/what issues the epoch transition? Is it pre-scripted per condition, or does the test harness inject it at a specific step?

---

### F2: Revocation Actor Identity

Per Q3b, revocation invalidates all claims from an authority actor.

**F2a**: Is revocation issued against `Root_Authority` (the legitimate signer), or a different actor for testing? Revoking Root_Authority would block all subsequent legitimate claims.

**F2b**: For Condition C testing, should we introduce a **secondary legitimate authority** (e.g., `Delegate_Authority`) that can be revoked without blocking Root_Authority?

---

### F3: Temporal Validity Bounds Defaults

Per Q4a/Q4b, claims have `valid_from` and `valid_until` (step-based).

**F3a**: What are the default bounds for a legitimate claim? Proposed:
- `valid_from`: step of issuance
- `valid_until`: step of issuance + 5 (or `null` for unbounded within epoch)

**F3b**: Should epoch boundary automatically invalidate claims regardless of `valid_until`?

---

### F4: Condition-Specific Epoch/Revocation Timing

Per Q12, 6 steps with 2 epochs. Need explicit timing for each condition:

**F4a**: Proposed condition schedules:

| Condition | Epoch 0 | Transition | Epoch 1 | Revocation | Notes |
|-----------|---------|------------|---------|------------|-------|
| A | steps 1-3 | step 3→4 | steps 4-6 | none | Fresh authority only |
| B | steps 1-6 | none | — | none | Consumption test (single epoch) |
| C | steps 1-3 | step 3→4 | steps 4-6 | step 2 | Revoke before epoch transition |
| D | steps 1-3 | step 3→4 | steps 4-6 | none | Cross-epoch saturation |
| E | steps 1-3 | step 3→4 | steps 4-6 | none | Boundary razor |

Is this schedule correct? Any adjustments?

**F4b**: For Condition B (consumption test), single epoch is sufficient since we're testing claim reuse, not epoch crossing. Confirm?

---

### F5: Claim Validity Fields Extension

Per Q4a, claims need temporal bounds. The SIR-0/SIR-1 `AuthorityClaim` has:
- `claim_id`, `claim_type`, `claimed_actor_id`, `scope`, `artifact`, `nonce`, `source_id`, `timestamp`

**F5a**: Proposed extensions for SIR-2:
```python
valid_from: int      # Step number
valid_until: int     # Step number (or None for epoch-scoped)
epoch: int           # Issuance epoch
```
Confirm these additions?

**F5b**: Should `nonce` be repurposed for consumption tracking, or keep it for replay detection and add separate `consumption_id`?

---

### F6: Replay-Equivalent vs. Exact Replay

Per Q5a, Condition B uses exact byte-for-byte replay.

**F6a**: For Conditions D and E, should replays also be exact, or should some be "replay-equivalent" (same scope/effect/provenance but different `claim_id`)?

**F6b**: If replay-equivalent claims should be tested, which condition covers them? Or should this be SIR-3 territory?

---

### F7: Gate Decision Logging

Per Q8a, valid-at-ingress but blocked-at-gate is expected.

**F7a**: Should gate decisions include a `classification_at_ingress` field to log the original classification alongside the gate outcome?

**F7b**: Proposed gate decision structure:
```json
{
  "claim_id": "...",
  "ingress_classification": "VALID_AUTHORITY_CLAIM",
  "gate_decision": "REFUSE",
  "refuse_reason": "CONSUMED",
  "epoch_at_gate": 1,
  "consumption_status": true
}
```
Is this sufficient?

---

### F8: Consumption Registry Schema

Per Q2a, consumption is per `claim_id`.

**F8a**: Proposed `consumption_registry_schema.json`:
```json
{
  "consumed_claims": {
    "<claim_id>": {
      "consumed_at_step": <int>,
      "consumed_at_epoch": <int>,
      "effect_produced": "<effect_id>"
    }
  }
}
```
Confirm structure?

---

### F9: Revocation Schema

Per Q3a/Q3b, revocation is per authority actor via law command.

**F9a**: Proposed `revocation_schema.json`:
```json
{
  "revocations": [
    {
      "revocation_id": "REV-001",
      "target_actor": "Delegate_Authority",
      "issued_at_step": 2,
      "issued_at_epoch": 0,
      "effective_immediately": true
    }
  ]
}
```
Confirm structure?

---

### F10: Condition A Fresh Authority

Condition A is the control with only fresh, unconsumed authority.

**F10a**: Does Condition A still include epoch transition (step 3→4), or should it be single-epoch to serve as a pure baseline?

**F10b**: If epoch transitions occur in Condition A, fresh claims in epoch 1 should still execute normally. Confirm this is the expected "control" behavior?

---

## Summary of Follow-Ups

| Follow-Up | Key Clarification |
|-----------|-------------------|
| F1 | Epoch transition event structure |
| F2 | Revocation target (secondary authority?) |
| F3 | Temporal validity defaults |
| F4 | Condition-specific schedules |
| F5 | Claim validity field extensions |
| F6 | Replay-equivalent vs. exact replay |
| F7 | Gate decision logging structure |
| F8 | Consumption registry schema |
| F9 | Revocation schema |
| F10 | Condition A epoch treatment |

---

*Awaiting follow-up answers before proceeding to preregistration.*

---

## Follow-Up Round 2 (Based on F1-F10 Answers)

All major design decisions are now closed. The following are minor clarifications for implementation precision:

### G1: Delegate_Authority Key Generation

Per F2b, `Delegate_Authority` is introduced as a second legitimate signer.

**G1a**: Should the Delegate key be generated at runtime (like SIR-0/SIR-1) or frozen in artifacts?

**G1b**: What scope does Delegate_Authority have? Proposed:
- `SCOPE/ENV/SHORTCUT_UNLOCK` (same as Root_Authority for gated action)

Or should Delegate have a distinct scope to test scope-based revocation?

---

### G2: Condition C Detailed Sequence

Per F4a, Condition C has revocation at step 2.

**G2a**: Confirm the exact step-by-step sequence:
1. Step 1: Delegate_Authority issues claim CLM-C-001, executes OPEN_SHORTCUT ✓
2. Step 2: LAW_SUBSTRATE issues REV-001 revoking Delegate_Authority
3. Step 2 (same step): Replay CLM-C-001 — should be refused (REVOKED_ACTOR)
4. Step 3: Epoch transition (0→1)
5. Step 4-6: Root_Authority issues fresh claims in epoch 1 — should succeed

Is this correct?

**G2b**: Since OPEN_SHORTCUT is episode-irreversible, how does Condition C test continued legitimate authority function if the shortcut is already open? Options:
- (i) Root issues claims for a different scope in epoch 1 (but we only have one gated action)
- (ii) Root issues claims that are consumed without effect (shortcut already open, logged as success)
- (iii) Add a second gated action for Condition C only

---

### G3: Condition E Precise Timing

Per F4a, Condition E: "Step 3: issue last-epoch claim (epoch 0); boundary transition; Step 4: replay immediately"

**G3a**: Is the claim in step 3 issued AND executed (consuming it), or issued but NOT executed before epoch transition?

If issued and executed:
- Step 4 replay fails for CONSUMED_CLAIM (not EPOCH_MISMATCH)

If issued but not executed:
- Step 4 replay fails for EPOCH_MISMATCH

Which is the intended test?

---

### G4: Multiple Gated Actions for Full Coverage

Per G2b concern, a single `OPEN_SHORTCUT` may be insufficient for all conditions.

**G4a**: Should we add a second gated action for SIR-2? Proposed:
- `GRANT_TRAVERSE_N5`: Adds capability to traverse to N5, can be executed multiple times (but each claim authorizes only one grant)

This would allow:
- Condition C: Delegate opens shortcut (consumed), revocation, Root grants traverse (success)
- Each condition has a fresh gated action to test

Or is the current single action sufficient with appropriate logging?

---

### G5: Gate Decision Enumeration

Per F7b, `refuse_reason` is enumerated.

**G5a**: Confirm the full set of refuse reasons:
- `EPOCH_MISMATCH`
- `REVOKED_ACTOR`
- `CONSUMED_CLAIM`
- `OUTSIDE_VALID_WINDOW`
- `MALFORMED`
- `AMBIGUOUS`

Should we add:
- `UNAUTHORIZED_ACTOR` (from SIR-1 for non-trusted-root)?
- `SCOPE_MISMATCH`?

---

### G6: Verification Checks

Per spec §14, what are the SIR-2 specific verification checks?

**G6a**: Proposed checks:
1. `CHECK_NO_STALE_EFFECT` — No stale claim produces effect
2. `CHECK_NO_CONSUMED_EFFECT` — No consumed claim produces second effect
3. `CHECK_NO_REVOKED_EFFECT` — No revoked-actor claim produces effect
4. `CHECK_NO_EPOCH_MISMATCH_EFFECT` — No cross-epoch claim produces effect
5. `CHECK_FRESH_AUTHORITY_FUNCTIONAL` — Fresh authority in current epoch works
6. `CHECK_CONSUMPTION_LOGGED` — All consumptions logged
7. `CHECK_EPOCH_TRANSITIONS_LOGGED` — All epoch transitions logged
8. `CHECK_REVOCATIONS_LOGGED` — All revocations logged
9. `CHECK_GATE_DIVERGENCE_SAFE` — Ingress-valid but gate-refused is safe

Is this the right set?

---

## Summary of Round 2 Follow-Ups

| Follow-Up | Key Clarification |
|-----------|-------------------|
| G1 | Delegate_Authority key and scope |
| G2 | Condition C detailed sequence |
| G3 | Condition E claim execution timing |
| G4 | Need for second gated action |
| G5 | Refuse reason enumeration |
| G6 | Verification check set |

---

*Awaiting Round 2 answers before proceeding to preregistration.*

