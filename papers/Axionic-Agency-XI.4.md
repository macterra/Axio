# Axionic Agency XI.4 — Coordination Under Deadlock (IX-2)

*A Structural Demonstration of Interaction, Refusal, Livelock, Orphaning, and Collapse Without Arbitration or Aggregation*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026-02-06

## Abstract

This technical note reports the completed results of **Coordination Under Deadlock (IX-2)**, a preregistered experimental program within **Axionic Phase IX** that evaluates whether **multi-agent interaction can proceed under non-aggregable authority constraints** without arbitration, prioritization, semantic resolution, or kernel-forced coordination.

IX-2 isolates the boundary between **value encoding** and **execution under constraint**. It tests whether (i) holder-bound capabilities and global veto constraints can enforce refusal without hidden priority, (ii) joint execution remains possible when scopes do not collide, (iii) symmetric conflict yields honest non-resolution (livelock), (iv) authority denial and voluntary non-participation yield honest deadlock, (v) exit can produce permanent orphaning without reclamation, (vi) total exit yields collapse with state preserved, and (vii) agent-voluntary coordination can emerge via communication without kernel arbitration.

Across ten preregistered conditions (A–H, I.a, I.b), all observed outcomes matched preregistered expectations. Deterministic replay was verified as bit-identical after stripping explicitly permitted timestamp fields. One preregistered mechanism deviation was disclosed: the adaptive strategy’s hash-collision fallback used alphabetical ordering rather than the preregistered rehash; this change was agent-side, deterministic, and did not affect kernel non-sovereignty or the licensed claim.

The results license exactly one claim: **under non-aggregable authority constraints, coordination can occur only as agent-voluntary behavior, and otherwise the system enters honest deadlock or livelock without kernel arbitration**. IX-2 makes no claims about optimality, fairness, efficiency, governance legitimacy, scalability beyond two agents, safety, or alignment.

## 1. Problem Definition

### 1.1 The Coordination Assumption

Most “multi-agent coordination” systems quietly assume a resolver.

When agents conflict, the system chooses: a priority order, a tie-break, a fairness heuristic, a scheduler, a vote, a compromise rule, or a global objective. Even when presented as “coordination,” this is often **arbitration disguised as mechanics**.

IX-2 rejects this assumption.

If values have been encoded without aggregation (IX-1), then **coordination—if it exists—must arise without forced resolution**. Otherwise, the kernel is sovereign.

IX-2 asks a narrower, more brutal question:

> When no one is permitted to decide for others, does interaction proceed honestly, or does the system smuggle a decision?

### 1.2 Failure Modes Targeted

IX-2 is designed to surface interaction-level failures that masquerade as coordination:

* **Kernel arbitration:** selecting among colliding actions, scheduling, tie-breaking.
* **Implicit priority:** outcomes depending on ordering, time, retries, or endurance.
* **Aggregation by protocol:** “helpful” mechanics that convert conflict into choice.
* **Constraint probing:** partial approvals or informative refusals revealing authority topology.
* **Authority laundering:** using protocol mechanics to reclaim or reassign capability.
* **Dishonest liveness:** progress recovered by cheating rather than admissibility.

Any of these constitutes IX-2 failure.

## 2. Fixed Assumptions and Scope

### 2.1 Inherited Foundations (Frozen)

IX-2 inherits, without reinterpretation, the conclusions and constraints of:

* **AST v0.2** — authority artifact grammar and canonical serialization,
* **AKR-0** — deterministic, semantic-free execution physics,
* **Phase VIII (GSA-PoC)** — governance completeness without kernel semantics,
* **IX-0** — non-sovereign translation integrity,
* **IX-1** — value encoding without aggregation.

IX-2 introduces no new kernel semantics. It introduces **interaction and execution** under a fixed authority regime.

### 2.2 Explicit Exclusions

IX-2 does **not** test:

* value correctness or moral truth,
* preference learning,
* optimization, efficiency, or fairness,
* bargaining correctness,
* governance legitimacy,
* coalition dynamics (reserved for later Phase IX),
* safety or alignment.

IX-2 is an execution honesty probe, not a policy proposal.

## 3. Conserved Quantity

The conserved quantity throughout IX-2 is:

> **Authority-constrained interaction without arbitration or aggregation, preserving explicit capability ownership and global veto semantics.**

Interaction must preserve:

* **closed-world capability:** actions require explicit holder-bound ALLOW citation,
* **global veto:** DENY applies to all agents regardless of holder,
* **atomic blindness:** refusals reveal no authority identity or pass attribution,
* **collision physics:** interference refuses without tie-breaking,
* **no reclamation:** exit does not reassign authority or unlock resources,
* **deterministic replay:** outcomes invariant under re-execution.

Any mechanism that substitutes “somebody must choose” violates the conserved quantity.

## 4. Experimental Methodology

### 4.1 Preregistration Discipline

IX-2 was preregistered prior to implementation, including:

* RSA interface (observe / exit / message / action),
* action request schema (declared scope, delta, capability citations),
* authority artifact schema (holder-bound ALLOW, global DENY),
* two-pass admissibility (capability+veto, then interference),
* deadlock/livelock/orphaning/collapse definitions,
* epoch schedule and message timing,
* explicit condition set (A–H, I.a, I.b),
* determinism controls and replay criteria,
* aggregate pass/fail criteria.

All conditions executed with outcomes matching preregistered expectations. One agent-side strategy fallback deviation was disclosed (see §6.3).

### 4.2 Execution Architecture

Each run consisted of four strictly partitioned components:

1. **Agents (RSAs)** — deterministic strategy modules (static or adaptive).
2. **Interaction Kernel** — two-pass admissibility evaluator + atomic execution.
3. **World State** — flat key–value state store with deterministic deltas.
4. **Instrumentation Layer** — canonical logging, replay verification, structural comparison.

No component interpreted value semantics or optimized outcomes.

## 5. Conditions and Stressors

### 5.1 Condition A — No Conflict, Full Coordination (Positive Control)

**Purpose:** Verify baseline execution pipeline under disjoint writes.

**Result:** Both agents possessed the required holder-bound ALLOW capabilities for disjoint resources. Pass 1 succeeded; Pass 2 detected no interference; both actions executed in a single epoch.

**Classification:** PASS.

### 5.2 Condition B — Symmetric Conflict: Livelock

**Purpose:** Verify livelock classification under symmetric collision with Pass-1 admissibility.

**Result:** Both agents held ALLOW WRITE capability on the same scope key and repeatedly submitted colliding writes. Pass 1 admitted both; Pass 2 refused both due to interference. State remained unchanged for N=3 consecutive epochs with Pass-2 interference.

**Terminal Classification:** `STATE_LIVELOCK`.

**Classification:** PASS.

### 5.3 Condition C — Asymmetric Conflict: Partial Progress

**Purpose:** Verify that a global veto blocks one scope while disjoint action proceeds.

**Result:** A DENY WRITE veto existed for `resource_A`. Agent 1’s attempted write failed Pass 1. Agent 2’s disjoint write to `resource_B` passed Pass 1 and Pass 2 and executed.

**Classification:** PASS.

### 5.4 Condition D — Strategic Refusal: Deadlock

**Purpose:** Verify honest deadlock when capability/veto prevents admissibility and the other agent refuses to act.

**Result:** Agent 1’s write to a vetoed scope failed Pass 1. Agent 2 submitted `NO_ACTION` each epoch. No Pass-1-admissible actions existed within the preregistered action space, yielding immediate deadlock.

**Terminal Classification:** `STATE_DEADLOCK`.

**Classification:** PASS.

### 5.5 Condition E — Adversarial Arbitration Injection (Tie-Break)

**Purpose:** Verify that kernel tie-breaking is detectable and classifiable as failure.

**Result:** Under forced tie-break injection, the kernel selected a “winner” under interference instead of refusing both. This produced a kernel-level arbitration signature.

**Kernel Classification:** `IX2_FAIL / IMPLICIT_ARBITRATION`.

Per preregistration, detection of this failure constitutes experiment-level PASS for the adversarial condition.

**Classification:** FAIL_DETECTED (expected).

### 5.6 Condition F — True Deadlock: No Admissible Actions

**Purpose:** Verify deadlock when no ALLOW capabilities exist and DENY vetoes apply.

**Result:** No ALLOW capabilities were present. Agents cited empty authority lists. Pass 1 failed for all actions. No admissible actions existed from epoch 0 onward.

**Terminal Classification:** `STATE_DEADLOCK`.

**Classification:** PASS.

### 5.7 Condition G — Exit and Orphaning

**Purpose:** Verify permanent orphaning when the sole capability holder exits.

**Result:** `resource_A` had a sole ALLOW WRITE holder (agent_2). After agent_2 executed its own write and exited, agent_1 could no longer present any valid ALLOW capability for `(resource_A, WRITE)`. All subsequent attempts to write `resource_A` failed Pass 1. Orphaning was classified as terminal.

**Terminal Classification:** `ORPHANING`.

**Classification:** PASS.

### 5.8 Condition H — Collapse

**Purpose:** Verify honest halt when all agents exit.

**Result:** Following initial collision and refusal, both agents exited. No active agents remained. State was preserved and no invariants were violated.

**Terminal Classification:** `COLLAPSE`.

**Classification:** PASS.

### 5.9 Condition I.a — Static Agents Under Symmetric Conflict

**Purpose:** Verify that static agents cannot escape symmetric livelock.

**Result:** Identical to Condition B with the additional constraint that agents ignore outcomes. Persistent collision and refusal produced livelock.

**Terminal Classification:** `STATE_LIVELOCK`.

**Classification:** PASS.

### 5.10 Condition I.b — Adaptive Agents: Agent-Voluntary Coordination via Communication

**Purpose:** Verify that adaptive agents can escape symmetric conflict without kernel arbitration.

**Result:** Agents intentionally collided at epoch 0 and broadcast role messages. At epoch 1, they partitioned writes across disjoint resources, producing successful execution and stable disjoint coordination thereafter. No kernel scheduling or tie-breaking occurred; coordination arose entirely from agent strategy.

**Classification:** PASS.

## 6. Determinism Verification and Deviations

### 6.1 Replay Determinism

Replay determinism was verified by:

* canonical JSON serialization with sorted keys,
* fixed condition vectors and sequence control,
* structural comparison of complete execution logs.

Only explicitly permitted timestamp fields were stripped prior to comparison. All other fields were compared verbatim.

**Result:** Bit-identical outputs across replays, modulo permitted timestamp variance.

### 6.2 Preregistration Hash and Artifact Integrity

The preregistration frozen-sections hash was verified as recorded in the preregistration commit, and the full execution log was stored with a published SHA-256 digest.

### 6.3 Disclosed Deviation (Non-Kernel, Agent-Side)

One deviation from frozen preregistered mechanism was identified:

* **Condition I.b hash-partition fallback:** The preregistered fallback defined role collision resolution via rehash (`sha256(agent_id + ":1") mod 2`). The implementation used alphabetical ordering of `agent_id` values to assign roles by index when collisions occur.

**Impact:** This deviation is agent-side and deterministic. It does not introduce kernel arbitration, aggregation, or priority inside admissibility. It affects rename-invariance of the agent-side convention but does not alter the licensed claim.

## 7. Core Results

### 7.1 Positive Results

IX-2 establishes that:

1. **Explicit capability citation enforces closed-world admissibility.**
2. **Global veto constraints block actions uniformly without semantic reasoning.**
3. **Disjoint execution is possible without coordination machinery.**
4. **Symmetric conflict yields livelock under interference physics rather than hidden tie-breaking.**
5. **Deadlock emerges honestly when Pass-1 admissibility is absent within the preregistered action space.**
6. **Exit can permanently orphan resources without authority reclamation.**
7. **Total exit yields collapse with state preserved.**
8. **Adaptive coordination can arise as agent-voluntary behavior without kernel arbitration.**
9. **Replay determinism holds under canonical serialization and fixed vectors.**
10. **Explicit arbitration attempts are detectable under adversarial injection.**

### 7.2 Negative Results (Explicit)

IX-2 does **not** establish:

* that coordination is efficient, fair, or stable under richer environments,
* that negotiation yields satisfactory outcomes,
* that deadlock/livelock are avoidable without aggregation,
* that two-agent results generalize to coalitions,
* any safety or alignment claim.

## 8. Failure Semantics and Closure

### 8.1 Closure Criteria

IX-2 closes positive if and only if:

1. Kernel does not arbitrate (except under detected adversarial injection).
2. No aggregation or implicit priority emerges in admissibility.
3. Atomic blindness holds (no partial approval leakage).
4. Deadlock/livelock/orphaning/collapse classifications match preregistration.
5. Adversarial tie-break produces `IX2_FAIL / IMPLICIT_ARBITRATION`.
6. Replay determinism holds.

All criteria were satisfied, with one disclosed agent-side mechanism deviation.

### 8.2 IX-2 Closure Status

**IX-2 Status:** **CLOSED — POSITIVE**
(`IX2_PASS / COORDINATION_UNDER_DEADLOCK_ESTABLISHED`)

## 9. Boundary Conditions and Deferred Hazards

### 9.1 Coordination vs Arbitration

IX-2 makes explicit what many systems blur: coordination is not a kernel service under Axionic constraints. If coordination happens, it happens because agents voluntarily choose compatible actions.

### 9.2 The Price of Capability Sovereignty

Closed-world capability produces permanence:

* vetoed actions remain vetoed,
* orphaned resources remain orphaned,
* exit does not unlock what the kernel is forbidden to reclaim.

This is not a defect; it is the structural consequence of non-sovereign kernels.

### 9.3 Interface to Subsequent Phase IX Work

IX-2 removes the final “the system had to schedule” excuse at the interaction layer.

Subsequent Phase IX investigations may now legitimately ask:

* what governance styles exist under honest failure,
* how coordination attempts degrade under resource pressure,
* how multi-agent systems behave under coalition formation,
* what meta-governance could exist without aggregation.

These belong to IX-3 and beyond.

## 10. Implications (Strictly Limited)

IX-2 establishes a necessary condition for reflective sovereignty in multi-agent settings:

* a kernel can remain non-sovereign while enforcing authority constraints,
* coordination is possible only as agent-voluntary behavior,
* and honest non-resolution states are not errors.

It does not establish sufficiency for governance.

## 11. Conclusion

IX-2 demonstrates that multi-agent interaction can be forced to remain honest under conflict: the system can execute when scopes do not collide, refuse without explanation when they do, deadlock when authority prevents admissibility, livelock when admissible actions interfere, orphan resources when sole capability holders exit, and collapse when agents depart.

Coordination survives only in one form:

**voluntary convergence of agents under constraint.**

Everything else is arbitration.

## Appendix A — Condition Outcomes

| Condition | Outcome       |
| --------- | ------------- |
| A         | PASS          |
| B         | PASS          |
| C         | PASS          |
| D         | PASS          |
| E         | FAIL_DETECTED |
| F         | PASS          |
| G         | PASS          |
| H         | PASS          |
| I.a       | PASS          |
| I.b       | PASS          |

## Appendix B — Determinism Summary

* Canonical serialization enforced
* Fixed vectors and sequence control
* Timestamp-only variance permitted
* Bit-identical replay otherwise confirmed

**End of Axionic Agency XI.4 — Coordination Under Deadlock Results**
