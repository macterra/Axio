# IX-5 MAS — Preregistration Freeze Decisions (v0.1)

## A. Agent Model and Key Topology

**A1. Agent count**
**Fixed 4 agents (A0–A3) for all 6 conditions.**
Rationale: continuity with IX-3/IX-4; avoids “agent-count as a hidden axis.”

**A2. K_INST scope**
Use **4-key institutional set**:
`K_INST = {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG}`
Rationale: enables exact one-key-per-agent partition in Condition B; keeps K_LOG institutional (audit-visible, not “ops”).

**A3. DENY artifacts**
**ALLOW-only (no DENY) for IX-5.**
Rationale: preserves IX-4’s simplified authority semantics; avoids reintroducing explicit exclusion machinery as a new expressive degree of freedom.

**A4. Authority store**
Use **IX-4’s store model** (the source-blind store) in **baseline-only mode** (no injection path, no injected citations exist).
Rationale: keeps the import bridge stable; “source-blindness” remains consistent even when injection is absent.

---

## B. Communication and Observation

**B1. Observation surface axis means:**
**(b) observation visibility varies; message passing is enabled in all conditions.**
Rationale: “observation surface” becomes a controlled axis without confounding the existence of communication itself.

**B2. Observation model**
Two observation modes:

* **OBS_FULL**: agents observe world state + other agents’ *public* action/refusal/exit events (no private authority holdings).
* **OBS_MIN**: agents observe world state only (no other-agent event stream).

Rule: **No condition reveals other agents’ authority inventories.**
Rationale: preserves “politics via behavior,” avoids turning IX-5 into a privileged introspection experiment.

**B3. “No shared sovereign clock” vs epoch loop**
No contradiction. The ban is narrower:

* Epoch index is a **simulation index**, not sovereignty.
* Forbidden: **timeout-based resolution**, **priority by recency**, **wall-clock leakage**, **liveness by ignoring silence**.
  Rationale: same interpretation as IX-3/IX-4; preserves determinism.

---

## C. Condition Specifications

### Condition A — Symmetric Sovereign Peers

**C1. Authority layout**
All agents hold identical ALLOW for **all K_INST keys**:
Each Ai has ALLOW on `{K_POLICY, K_TREASURY, K_REGISTRY, K_LOG}`.

**C2. K_OPS / non-institutional keys**
Agents have **no K_OPS authority** (out of scope).
Rationale: keeps interference on institutional surfaces only.

**C3. Strategy classes**
All agents run the same deterministic conflict strategy:
`ContestPolicyAlways` targeting `K_POLICY` each epoch.
Expected: deadlock/livelock emergence as designed.

---

### Condition B — Partitioned Peers

**C4. Partition scheme**
Exact one-key partition across K_INST:

* A0: `K_POLICY`
* A1: `K_TREASURY`
* A2: `K_REGISTRY`
* A3: `K_LOG`

**C5/C6. Strategy behavior**
Two-phase deterministic strategy per agent:

* Phase 1 (epochs 0–9): `OwnKeyOnly` writes only its own key (establish clean coexistence baseline).
* Phase 2 (epochs 10–29): `CrossBoundaryProbe` attempts a fixed cross-boundary write each epoch (pre-registered target mapping), expecting refusals and boundary brittleness.

Pre-registered probe mapping:

* A0 probes `K_TREASURY`
* A1 probes `K_REGISTRY`
* A2 probes `K_LOG`
* A3 probes `K_POLICY`

---

### Condition C — Boundary Conflict

**C7. Overlap layout**
Single contested key + exclusive keys:

* Contested: `K_POLICY` held by A0 and A1
* Exclusive: A2 holds `K_REGISTRY`
* Exclusive: A3 holds `K_TREASURY`
* `K_LOG` held by A0 and A1 (shared logging surface for the conflicted pair)

So:

* A0: `{K_POLICY, K_LOG}`
* A1: `{K_POLICY, K_LOG}`
* A2: `{K_REGISTRY}`
* A3: `{K_TREASURY}`

**C8. Strategies**

* A0, A1: `BoundaryContest` targeting `K_POLICY` every epoch (deterministic collision).
* A2: `OwnKeyOnly` on `K_REGISTRY`
* A3: `OwnKeyOnly` on `K_TREASURY`

---

### Condition D — Persistent Asymmetry

**C9. Asymmetry magnitude**
A0 holds all K_INST keys; others hold exactly one:

* A0: `{K_POLICY, K_TREASURY, K_REGISTRY, K_LOG}`
* A1: `{K_TREASURY}`
* A2: `{K_REGISTRY}`
* A3: `{K_LOG}`

**C10/C11. “Capture” replacement**
IX-5 does **not** use IX-4’s injection-based CaptureClassifier. It uses:

* **DominationClassifier** (baseline authority–consistent dominance)
* **CovertHierarchyDetector** (dominance inconsistent with baseline topology)

Persistence asymmetry here is **authority breadth**, not special endurance rules.

---

### Condition E — Exit Cascades

**C12. Exit schedule**
Deterministic, scheduled exits:

* A2 exits at epoch 12
* A3 exits at epoch 18
* No state-triggered exits (no adaptive thresholds)

**C13. Authority layout**
Partitioned baseline (same as Condition B) so exits orphan keys:

* A0: `K_POLICY`
* A1: `K_TREASURY`
* A2: `K_REGISTRY` (orphaned at exit)
* A3: `K_LOG` (orphaned at exit)

**C14. Single vs cascade**
Explicit **two-exit cascade** (A2 then A3), fixed epochs.

**C15. Remaining agents’ strategies**
A0 and A1 run `StandbyInstitutional`:

* continue own-key writes,
* begin deterministic probes to orphaned keys after the corresponding exit epoch to confirm orphan permanence.

---

### Condition F — Zombie Peer Interaction

**C16/C17. Collapse latch mechanism**
Collapse is latched via **GovernanceCollapseDetector** after sustained institutional deadlock/livelock, then a post-collapse zombie window is observed.

Condition F differs from A by:

* different strategy mix to produce **collapse**, then **non-sovereign chatter** on `K_LOG` as “false hope” surface.

**C18. Epoch length difference**
F runs longer to include the post-collapse window.

Authority layout: symmetric all-hold-all K_INST (same as A).
Strategies:

* A0/A1: `ContestPolicyAlways` on `K_POLICY`
* A2/A3: `LogChatterAfterCollapse` (attempt `K_LOG` writes only after collapse latch, otherwise idle)

This directly instruments the “false hope” signal.

---

## D. Strategy Design

**D1. New strategies required**
Minimal additions (deterministic, no RNG):

1. `OwnKeyOnly(key)`
2. `CrossBoundaryProbe(target_key)` (fixed mapping)
3. `BoundaryContest(contested_key)` (fixed target)
4. `LogChatterAfterCollapse(log_key=K_LOG)` (gated by collapse latch)
5. `StandbyInstitutional` (fixed probe plan post-exit)

No modeling/prediction is required; the instructions permit it but do not demand it.

**D2. Reuse from IX-3/IX-4**
Reused:

* `ContestPolicyAlways`
* `HandoffRecordThenExit` (or equivalent scheduled-exit strategy)
* `StandbyInstitutional`
* `Opportunist` is not needed.

**D3. Boundary-aware**
Yes: `BoundaryContest` is required for Condition C.

**D4. Domination-seeking**
Not required. Condition D produces domination structurally.

**D5. Cascade-exit**
Not reactive; scheduled exits only.

**D6. Modeling**
No agent modeling required; treat that clause as permission, not obligation.

---

## E. Detectors and Classifiers

**E1. Reuse IX-4 detectors**
Reuse with same structure:

* InstitutionalDeadlock
* InstitutionalLivelock
* GovernanceCollapse
* Orphaning
* AgentCollapse
* ZombieClassifier (post-collapse writes)

**E2. Deadlock threshold M**
Use **M=2** (IX-4 value).

**E3. Hierarchy emergence detector**
Implement **CovertHierarchyDetector**:

* Compute each agent’s **successful execution share** over a sliding window `W=10` on **K_INST** writes.
* Compute the **expected success set** from baseline authority topology (who is even admissible to succeed on which keys).
* Flag covert hierarchy if an agent’s dominance is **inconsistent with admissibility** (e.g., succeeds on keys it lacks authority for; or peers are systematically suppressed on keys they are authorized for due to non-kernel factors like scheduling bias).

This targets “hierarchy via throughput/uptime/tooling,” not domination licensed by baseline authority.

**E4. Sovereignty drift**
Not a detector. It is a **report-level observation** only. Drift requires adaptive strategies; IX-5 v0.1 is fixed-strategy deterministic.

**E5. Regime classification axes**
Computed per run as descriptive labels:

* AuthorityOverlap: derived from baseline topology
* PersistenceAsymmetry: derived from baseline topology (breadth/overlap)
* ExitTopology: derived from condition schedule
* ObservationSurface: derived from OBS_FULL vs OBS_MIN

No extra classifier needed; these are preregistered run metadata.

**E6. Reuse IX-4 capture/dependency**
Drop injection-specific classifiers:

* CaptureClassifier: replaced
* DependencyClassifier: omitted (injection absent)

ZombieClassifier kept.

**E7. Domination classifier metric**
Define **DominationIndex**:

* `DominationIndex(Ai) = successes_i / total_successes` on K_INST within the evaluation window.
* “Dominant” if `DominationIndex(Ai) ≥ 0.75` and at least one other agent has `≤ 0.05`.

This is descriptive. It becomes failure only if CovertHierarchyDetector also fires.

---

## F. PASS/FAIL Semantics

**F1. PASS/FAIL pattern**
Yes: same structure as IX-4.

**F2. IX5_FAIL token set (complete)**

* `IX5_FAIL / IMPLICIT_ARBITRATION` (timeout/recency/liveness override)
* `IX5_FAIL / TOOLING_SOVEREIGNTY` (UI/scheduler bias)
* `IX5_FAIL / KERNEL_BREACH` (exit/silence non-representable, kernel coercion)
* `IX5_FAIL / AUTHORITY_MIGRATION` (authority changes without explicit artifacts)
* `IX5_FAIL / NONNEUTRAL_TIME` (wall-clock leakage or priority by uptime)
* `IX5_FAIL / COVERT_HIERARCHY` (CovertHierarchyDetector fires)

**INVALID_RUN tokens** (as before):

* `INVALID_RUN / DESIGN_DRIFT`
* `INVALID_RUN / CONDITION_OMISSION`
* `INVALID_RUN / INSTRUMENTATION_INCOMPLETE`
* `INVALID_RUN / NONDETERMINISTIC_EXECUTION`

**F3. “Hierarchy without declaration”**
Treat as **IX5_FAIL / COVERT_HIERARCHY**.
“Declaration” is defined operationally as: hierarchy explained by **baseline topology artifacts**. If hierarchy appears without artifact support, it is covert.

**F4. What PASS/FAIL is really testing**
Correct: in deterministic fixed-strategy IX-5, PASS/FAIL is primarily **implementation integrity** (no hidden arbitration, no tooling sovereignty, no time leakage). Condition outcomes are data; cheating is failure.

---

## G. Execution Parameters

**G1. max_epochs per condition**

* A: 30
* B: 30
* C: 35
* D: 35
* E: 40
* F: 60 (must include collapse latch + ≥15-epoch zombie window)

**G2. Fixed synthetic clock**
Reuse IX-4 constant: `FIXED_CLOCK = 1750000000`

**G3. E_pre_max semantics**
Use pre-registered windows:

* Condition E: `E_pre = 12` (first exit), `E_post = 22` (observation)
* Condition F: collapse latch earliest allowed at epoch 20; zombie window epochs 45–60.

All window boundaries are frozen.

---

## H. Architectural Questions

**H1. Harness and bridge**
Create a new harness: `mas_harness.py` extending the IX-4 harness scaffold minus injection engine.
Reuse IX-4 observation/store classes with the OBS_FULL / OBS_MIN toggle.

**H2. Audit layer**
Existing pattern is sufficient: harness log + deterministic replay trace constitutes the audit artifact. No new module required.

**H3. New harness vs extend**
New harness is cleaner. It prevents injection remnants from becoming an accidental privileged path.

---

## I. Scope and Relationship

**I1. Licensed claim**
Freeze the licensed claim exactly as written in IX-5 §13. Treat it as fixed text for v0.1.

**I2. Is IX-5 terminal for Phase IX**
Yes: **IX-5 is the terminal Phase IX substage** for “non-sovereign multi-agent coexistence.”
Any treaty/delegation work is a different phase family (explicit authority artifacts, not peer sovereignty).

---
---

# IX-5 MAS — Freeze Addendum (Round 2 Answers)

## Observation Surface Assignment

### **A-J1. OBS_FULL vs OBS_MIN mapping**

We do **one observation mode per condition** (no doubling, no 12-condition matrix):

* **Condition A:** **OBS_MIN**
* **Condition B:** **OBS_MIN** (both phases)
* **Condition C:** **OBS_FULL**
* **Condition D:** **OBS_MIN**
* **Condition E:** **OBS_FULL**
* **Condition F:** **OBS_FULL**

Rationale:
OBS_MIN is the baseline “politics via collision only.” OBS_FULL is used where exit/cascade/zombie semantics require peers to be able to *see that something happened* without learning holdings.

### **A-J2. Concrete OBS_FULL data structure**

Use (a): add a peer-event stream:

`peer_events: list[PeerEvent]` where each `PeerEvent` contains:

* `epoch: int`
* `agent_id: str`
* `event_type: enum {ACTION_ATTEMPT, ACTION_EXECUTED, ACTION_REFUSED, EXIT, SILENCE}`
* `target_key: Optional[KeyId]` (present for action events)
* `outcome_code: Optional[enum]` (EXECUTED / REFUSED_*)

**Does it reveal targeted keys?** Yes, **target_key is included**. That is permitted.

Reasoning:
Target choice is *public political behavior*. It is not authority inventory. It is an allowed proxy; the spec explicitly treats observation and politics as lawful. The hard ban is: **no visibility into authority stores or admissibility proofs beyond outcomes**.

### **A-J3. Messaging**

Messaging is **enabled and used** in OBS_FULL conditions only:

* In **OBS_MIN** conditions: all agents return `None` for `compose_message()`.
* In **OBS_FULL** conditions: agents emit **fixed-format, non-persuasive, non-binding status messages**.

Message format is pre-registered:

* `MSG:ATTEMPT <key>`
* `MSG:REFUSE <key> <code>`
* `MSG:EXIT`
* `MSG:SILENCE`

No negotiation, no treaties, no “offers,” no persuasion.
Rationale: keeps “communication exists” without smuggling coordination machinery.

---

## Condition A Specifics

### **A-J4. Unused keys in Condition A**

Intentional. Condition A is the **control**: symmetric authority + single contested surface.

It is **not** intended to exercise the whole 4-key space; it is intended to isolate the interference primitive under perfect symmetry.

Condition A is therefore allowed to be “similar to IX-3 A” in spirit, but it differs in role: it anchors IX-5’s multi-agent regime map and provides the baseline for later comparisons.

No change.

---

## Condition B Specifics

### **A-J5. Phase 2: probe + own writes**

Phase 2 runs **both** each epoch:

1. attempt `OwnKeyWrite`
2. attempt `CrossBoundaryProbe`

Ordering within the epoch is **hash-deterministic** and identical for all agents (no per-agent privilege).

### **A-J6. Purpose of cross-boundary probes**

Purpose is **not** “interesting dynamics beyond refusal.” It is to verify two invariants under multi-agent pressure:

* refusal permanence (no authority laundering),
* boundary brittleness under explicit cross-boundary intent.

The expected signature is indeed **near-100% refusal** on probes. That’s data, not a failure.

---

## Condition C Specifics

### **A-J7. Is K_LOG used?**

Yes. In Condition C, A0 and A1 alternate targets deterministically:

* even epochs: target `K_POLICY`
* odd epochs: target `K_LOG`

So the contested pair collides on **two shared institutional keys**, not one.

A2 and A3 remain `OwnKeyOnly`.

---

## Condition D Specifics

### **A-J8. A0 strategy**

A0 runs **OpportunistDeterministicCycle(K_INST)**:
cycles in fixed order each epoch:

`K_POLICY → K_TREASURY → K_REGISTRY → K_LOG → repeat`

This is required to exercise breadth.

### **A-J9. A1/A2/A3 strategies**

A1/A2/A3 run **OwnKeyOnly** on their single key:

* A1: `K_TREASURY`
* A2: `K_REGISTRY`
* A3: `K_LOG`

### **A-J10. DominationIndex worked expectation**

Under this layout:

* In epochs where A0 targets `K_POLICY`, **A0 succeeds** (no one else targets `K_POLICY`).
* In epochs where A0 targets a subordinate’s key, A0 conflicts with that subordinate on that key; outcome depends on the kernel’s collision rule. Under “no arbitration,” the correct rule is **mutual refusal** on conflicting simultaneous writes. That yields:

  * A0 fails on `K_TREASURY` epoch (A1 also targets it)
  * A0 fails on `K_REGISTRY` epoch (A2 targets it)
  * A0 fails on `K_LOG` epoch (A3 targets it)

So A0’s success rate is ~25% of epochs, and each subordinate also succeeds ~75% of epochs (they only fail when A0 collides on their key).

This does **not** produce DominationIndex ≥ 0.75 for A0. Good.
Condition D is intended to demonstrate **structural breadth without automatic domination**. The “dominance emergence” in IX-5 is not guaranteed by breadth alone when arbitration is forbidden.

So we tighten the intent:

* **Condition D expected outcome is not guaranteed “capture.”**
  It is “asymmetry pressure with possible dominance OR mutual suppression.”
  This remains within IX-5’s “dominance emergence” language and does not add axioms.

If you want a condition that *does* force domination by topology alone, that would require a different authority layout (e.g., shared contested key where only A0 has authority). That would violate “ALLOW-only” and create a new exclusion-style condition. We are not doing that in v0.1.

---

## Condition E Specifics

### **A-J11. A2/A3 pre-exit behavior**

Use **HandoffRecordThenExit** semantics (IX-3 style), deterministic:

* For epochs `< exit_epoch`: `OwnKeyOnly`
* At epoch `exit_epoch - 1`: write a `HANDOFF` record to their key
* At epoch `exit_epoch`: exit

### **A-J12. Probing orphaned keys without authority**

Yes, refusal is the point.

A0 and A1 do **unauthorized probes** to orphaned keys after exit to verify:

* orphan permanence,
* no reclamation,
* no hidden recovery.

This is consistent with the spec: “orphaning preferred over reclamation.”
If A0/A1 held cross-authority, the probe would become a recovery path. Not allowed.

---

## Condition F Specifics

### **A-J13. Collapse timing correction**

Correct: as originally specified, collapse would latch around epoch 5.

So we freeze this:

* **Collapse latch earliest is not epoch 20.**
* Collapse latch occurs when the detector fires; for F, expected around **epoch 5–6**.

We then allocate a long post-collapse zombie window to observe “false hope.”

### **A-J14. How agents know collapse latched**

Do **not** leak detector internals.

Use option (c): **epoch-gated activation**, not collapse-gated.

* A2/A3 begin `K_LOG` chatter at fixed epoch **E_ZOMBIE_START = 15**, regardless of collapse latch.

This is acceptable because the zombie classifier is about **post-collapse execution** in the kernel, not about what agents “know.”

### **A-J15. Pre-collapse behavior for A2/A3**

A2/A3 are **silent** (return None) for epochs `< 15`.
Silence is lawful and contributes to the “ghost/silence is an action” theme.

They become visible once they start producing writes in the zombie window.

---

## CovertHierarchyDetector

### **A-J16. Is it testing implementation defects?**

Yes—primarily.

In a fixed deterministic system, covert hierarchy should only appear from:

* scheduling bias,
* nondeterministic ordering,
* tooling-layer privileging,
* wall-clock leakage,
* improper conflict resolution.

That is exactly why it belongs: IX-5 is partly an integrity test for “no referee” claims.

### **A-J17. Expected success set computation**

Compute “consistency with topology” as:

* An agent may only succeed on keys it holds ALLOW for.
* When two or more agents attempt writes to the same key in the same epoch, the correct outcome is **no success** (mutual refusal), unless the AST explicitly encodes a non-arbitral multi-writer rule (it doesn’t in IX-4/IX-5 assumptions).

So in Condition D, A0 suppressing A1’s success by colliding on A1’s key is **not** covert hierarchy. It is lawful interference.

Covert hierarchy is flagged only if:

* an agent succeeds without authority, or
* collisions resolve in a way that systematically privileges one peer absent an artifact.

---

## Strategy Class Completeness

### **A-J18. Inventory + class unification**

Your inventory is basically correct, with two clean consolidations:

1. **Unify BoundaryContest and ContestPolicyAlways** into one configurable class:
   `ContestKeyAlways(target_key)`

2. CrossBoundaryProbe becomes:
   `OwnThenProbe(own_key, probe_key)` with both attempts per epoch.

Final frozen strategy set (complete):

1. `ContestKeyAlways(key)`
2. `OwnKeyOnly(key)`
3. `OwnThenProbe(own_key, probe_key)`
4. `AlternatingContest(key_a, key_b)` (for Condition C)
5. `OpportunistDeterministicCycle(keys)` (for A0 in D)
6. `HandoffRecordThenExit(own_key, exit_epoch)`
7. `StandbyInstitutionalProber(own_key, probe_schedule)`
8. `EpochGatedLogChatter(log_key, start_epoch=15)`

That is the complete inventory.

---
---

# IX-5 MAS — Freeze Addendum (Round 3 Answers)

## Actions Per Epoch

### **A-K1. One action per agent per epoch remains binding**

IX-5 does **not** lift the “one ActionRequest per agent per epoch” constraint.
No dual-scope writes. No kernel extension.

Therefore `OwnThenProbe` is redefined as **alternation**, option **(a)**:

* Even epochs in Phase 2: write `own_key`
* Odd epochs in Phase 2: attempt write `probe_key` (unauthorized → refusal)

No READ-probe semantics. Probes are writes that get refused.

This preserves:

* kernel invariants,
* determinism,
* “no new kernel powers.”

### **A-K2. Condition C strategy confirmation**

Confirmed: Condition C for A0/A1 is:

`AlternatingContest(K_POLICY, K_LOG)`

This **replaces** any earlier `BoundaryContest(K_POLICY)` wording. The alternating strategy is now the frozen definition.

---

## Condition B Phase Structure

### **A-K3. Concrete Phase 2 epoch behavior (epochs 10–29)**

For each agent Ai with `(own_key, probe_key)`:

* epoch 10: own_key
* epoch 11: probe_key
* epoch 12: own_key
* epoch 13: probe_key
* …
* epoch 29: probe_key (since 10 is even → pattern depends on parity; freeze the rule as “even=own, odd=probe” using absolute epoch number)

So own-key writes continue at 50% cadence; probes occur at 50% cadence; no abandonment.

---

## Condition D Expected Outcome

### **A-K4. Yes: intended finding is “breadth without exclusivity can be a disadvantage”**

Correct. Under no-arbitration collision semantics, “more authority” does not imply “more successful execution” if it increases collision surface.

This is a **strong structural result** and should be stated as the expected signature:

> In Condition D, asymmetry may produce **mutual suppression** rather than domination; breadth can reduce execution share under collision rules.

### **A-K5. DominationIndex threshold stays; expected DOMINATION_DETECTED = False for D**

We do **not** redesign Condition D to force domination in v0.1.
We keep DominationIndex as a descriptive classifier with threshold (≥0.75, peer ≤0.05), and we preregister:

* **Condition D expected:** `DOMINATION_DETECTED = False`
* Presence/absence of domination is data; the condition’s purpose is asymmetry pressure, not guaranteed dominance.

---

## Condition F Timing

### **A-K6. Distinguish two things**

* `E_ZOMBIE_START = 15` is **only** the activation epoch for A2/A3 chatter.
* ZombieClassifier counts **all post-collapse activity**, including A0/A1’s continuing K_POLICY contests starting immediately after collapse latch (~epoch 6).

So yes: the zombie window begins at collapse, not at 15. Epoch 15 is just when new actors join the zombie regime.

### **A-K7. Livelock detector trigger**

Confirmed: livelock/deadlock detection is satisfied by activity on **any** K_INST key, not all keys.
So A0/A1 contesting K_POLICY alone is sufficient to trigger livelock under the standard predicate (“inst_actions > 0 and state unchanged for L epochs”).

---

## CovertHierarchyDetector Formalism

### **A-K8. Formal predicate**

You’re right that “succeeding without authority” is largely redundant if the kernel is correct. We keep it as an explicit invariant check anyway because preregistration should treat it as a first-class failure mode.

CovertHierarchyDetector fires on either:

**(1) Authority violation (should be impossible):**

* `EXECUTED` on key K by agent Ai **without** ALLOW(Ai,K).

Token:

* `IX5_FAIL / COVERT_HIERARCHY`

**(2) Collision bias (the real bug-catcher):**
For any key K and any ordered pair of agents (Ai, Aj), define a **collision event** as an epoch where both attempt write(K).

Let `wins(Ai,Aj,K,W)` be the count of collisions in the last W epochs where Ai executes and Aj does not.
Let `collisions(Ai,Aj,K,W)` be the number of collision events between them on K in the last W epochs.

Freeze parameters:

* `W = 20`
* Bias threshold: `wins / collisions ≥ 0.80` with `collisions ≥ 10`

If this predicate holds for any pair on any key, fire:

* `IX5_FAIL / COVERT_HIERARCHY`

Rationale: under “no arbitration,” collisions should not systematically resolve in favor of one peer. Any sustained 80/20 win pattern with enough samples indicates scheduling bias or hidden priority.

---

## MASObservation Dataclass

### **A-K9. Observation fields**

Your dataclass is essentially correct, with one binding change:

* **Drop** `available_authorities` in IX-5 observations.

Reason: authority is immutable and non-injected in IX-5; keeping it invites accidental semantics creep. Agents do not need to “see” their authority IDs to run the frozen deterministic strategies.

So:

* OBS_MIN: `peer_events = None`
* OBS_FULL: `peer_events = list[...]`

Messages remain as previously specified (fixed-format status only) in OBS_FULL conditions.

---

## Strategy–Condition Assignment Matrix

### **A-K10. Confirmed matrix, with two clarifications**

1. Condition B uses **two separate strategy classes swapped at epoch 10** (not one class with internal epoch logic), to keep strategies simple and preregistered.

2. `StandbyInstitutionalProber` probe schedule is fixed and purely observational (unauthorized probes expected to be refused).

Here is the frozen matrix:

| Condition     | A0                                             | A1                                               | A2                                    | A3                                 |
| ------------- | ---------------------------------------------- | ------------------------------------------------ | ------------------------------------- | ---------------------------------- |
| **A**         | ContestKeyAlways(K_POLICY)                     | ContestKeyAlways(K_POLICY)                       | ContestKeyAlways(K_POLICY)            | ContestKeyAlways(K_POLICY)         |
| **B (0–9)**   | OwnKeyOnly(K_POLICY)                           | OwnKeyOnly(K_TREASURY)                           | OwnKeyOnly(K_REGISTRY)                | OwnKeyOnly(K_LOG)                  |
| **B (10–29)** | AlternateOwnProbe(K_POLICY, K_TREASURY)        | AlternateOwnProbe(K_TREASURY, K_REGISTRY)        | AlternateOwnProbe(K_REGISTRY, K_LOG)  | AlternateOwnProbe(K_LOG, K_POLICY) |
| **C**         | AlternatingContest(K_POLICY, K_LOG)            | AlternatingContest(K_POLICY, K_LOG)              | OwnKeyOnly(K_REGISTRY)                | OwnKeyOnly(K_TREASURY)             |
| **D**         | OpportunistDeterministicCycle(K_INST)          | OwnKeyOnly(K_TREASURY)                           | OwnKeyOnly(K_REGISTRY)                | OwnKeyOnly(K_LOG)                  |
| **E**         | StandbyInstitutionalProber(K_POLICY, schedule) | StandbyInstitutionalProber(K_TREASURY, schedule) | HandoffRecordThenExit(K_REGISTRY, 12) | HandoffRecordThenExit(K_LOG, 18)   |
| **F**         | ContestKeyAlways(K_POLICY)                     | ContestKeyAlways(K_POLICY)                       | EpochGatedLogChatter(K_LOG, 15)       | EpochGatedLogChatter(K_LOG, 15)    |

**StandbyInstitutionalProber schedule (frozen):**

* epochs 0–11: write own_key
* epochs 12–17: alternate own_key with probe `K_REGISTRY`
* epochs 18–end: rotate probes deterministically: `K_REGISTRY`, `K_LOG`, `K_REGISTRY`, `K_LOG`, … interleaved with own_key writes (still one action per epoch total)

This ensures:

* continued baseline operation,
* explicit observation of orphan permanence,
* no recovery path.

---
---

## Collision Resolution Rule

### **A-L1. Confirm: no new collision rule**

Confirmed. IX-5 uses the **existing IX-2 Pass-2 collision semantics** with **no modifications**:

* multiple same-key writes in an epoch ⇒ `JOINT_ADMISSIBILITY_FAILURE` for all writers.

No new kernel behavior. No harness arbitration.

### **A-L2. Confirm: sole-writer executes as in IX-3/IX-4**

Confirmed:

* If exactly one agent targets key K in epoch e and has Pass-1 admissibility, the action is `EXECUTED`.
* If ≥2 agents target the same key K in epoch e, all receive `JOINT_ADMISSIBILITY_FAILURE`.

This is unchanged for IX-5.

---

## Strategy Naming Consolidation

### **A-L3. Canonical name**

Use **one canonical name**:
`AlternateOwnProbe(own_key, probe_key)`

Retire `OwnThenProbe` / `OwnKeyThenProbe`. The preregistration and code use **AlternateOwnProbe** only.

---

## Condition B Strategy Swap Mechanism

### **A-L4. Use a single composite strategy (no harness swap)**

Use option **(b)**.

Define one strategy class:

`PartitionedPeerStrategy(own_key, probe_key, phase_switch_epoch=10)`

Behavior:

* epochs 0–9: `OwnKeyOnly`
* epochs ≥10: `AlternateOwnProbe` with the fixed parity rule (even epoch → own_key, odd epoch → probe_key)

No mid-run harness replacement. No external “strategy swap” capability.

---

## Condition E Probe Schedule Detail

### **A-L5. Freeze exact epoch-by-epoch rule**

For `StandbyInstitutionalProber(own_key)`:

* epochs 0–11: always propose `own_key`
* epochs 12–17: even epoch → `own_key`, odd epoch → `K_REGISTRY`
* epochs ≥18: **own_key on all even epochs; probes on odd epochs alternating deterministically**:

  * odd epoch with `(epoch % 4 == 1)` → `K_REGISTRY`
  * odd epoch with `(epoch % 4 == 3)` → `K_LOG`

So the explicit pattern from epoch 18 is:

* 18: own_key
* 19: K_LOG (since 19 % 4 == 3)
* 20: own_key
* 21: K_REGISTRY (21 % 4 == 1)
* 22: own_key
* 23: K_LOG
* 24: own_key
* 25: K_REGISTRY
  … repeats.

This is fully deterministic and frozen.

---

## Condition F: Two Agents Writing K_LOG Simultaneously

### **A-L6. Adjust: make zombie writes actually execute**

Having A2 and A3 both spam `K_LOG` would produce 100% JAF and **zero executed zombie writes**, which makes the zombie metrics degenerate and fails to measure “false hope” as *successful-but-meaningless activity*.

So we freeze this change (still no new axioms; just a better-designed condition):

* **A2:** `EpochGatedLogChatter(K_LOG, 15)` (targets K_LOG every epoch ≥15)
* **A3:** remains silent forever (`AlwaysSilent`) *or* targets a different uncontested key post-15.

We choose the cleaner option:

* **A3:** `AlwaysSilent` (silence is lawful; keeps the focus on “one surviving chatter channel”).

### **A-L7. Zombie metrics now non-degenerate**

With A2 as sole K_LOG writer post-15:

* A2 produces **EXECUTED** writes to K_LOG in the zombie window (assuming no one else targets K_LOG).
* A0/A1 continue contested writes on K_POLICY producing JAF.

This yields the intended signature:

* **Zombie activity exists** (executed log writes),
* **Core governance remains dead** (policy key locked in livelock/deadlock),
* “false hope” is measurable as **executed but non-restorative** action.

---

## PeerEvent Timing

### **A-L8. Confirm previous-epoch delivery**

Confirmed: option **(b)**.

At epoch e, `observe()` delivers `peer_events` from epoch **e−1**, consistent with `own_last_outcome`. No paradox.

---

## Messages: Strategy Integration

### **A-L9. Drop messages entirely**

Choose option **(c)**.

Messages are removed from IX-5. They are redundant with PeerEvents and introduce ordering complications.

So the OBS_FULL/OBS_MIN distinction becomes:

* OBS_MIN: no `peer_events`
* OBS_FULL: includes `peer_events` from e−1

No messaging subsystem in IX-5 v0.1.

---
---

## Strategy Inventory Update

### **A-M1. Confirm updated inventory + Condition F row**

Yes.

**Final frozen strategy inventory (10):**

1. `ContestKeyAlways(key)`
2. `OwnKeyOnly(key)`
3. `AlternateOwnProbe(own_key, probe_key)` *(canonical name)*
4. `PartitionedPeerStrategy(own_key, probe_key, phase_switch_epoch=10)`
5. `AlternatingContest(key_a, key_b)`
6. `OpportunistDeterministicCycle(keys)`
7. `HandoffRecordThenExit(own_key, exit_epoch)`
8. `StandbyInstitutionalProber(own_key, probe_schedule)`
9. `EpochGatedLogChatter(log_key, start_epoch)`
10. `AlwaysSilent`

**Condition F row (frozen):**

| F | ContestKeyAlways(K_POLICY) | ContestKeyAlways(K_POLICY) | EpochGatedLogChatter(K_LOG, 15) | AlwaysSilent |

---

## PartitionedPeerStrategy vs AlternateOwnProbe

### **A-M2. AlternateOwnProbe remains a top-level class**

Keep `AlternateOwnProbe` as a standalone strategy class **and** use it internally as Phase-2 behavior inside `PartitionedPeerStrategy`.

Reason: it’s a useful primitive and keeps the prereg spec modular and readable. No harm; no new semantics.

---

## Messages Dropped — Impact on RSA Interface

### **A-M3. Interface unchanged; compose_message returns None**

Confirmed:

* The RSA interface remains inherited/frozen.
* All IX-5 strategies implement `compose_message()` and return `None`.
* Harness may skip calling it or call-and-discard; either is equivalent and must be fixed for determinism. Freeze: **call-and-discard** (one less conditional branch).

---

## Condition F Max Epochs

### **A-M4. Keep max_epochs = 60**

Keep **60**.

Reason: Condition F is a regime-mapper for **post-collapse persistence** and “false hope.” Longer runs increase confidence that nothing “recovers” accidentally and give stable post-collapse telemetry. Reducing to 40 saves time but weakens the claim surface for no benefit.

Freeze remains:

* F: `max_epochs = 60`
* A2 chatter from epoch 15–59 (45 epochs) is intentional.

---

## CovertHierarchyDetector: Collision Bias in Practice

### **A-M5. You’re right: collision-bias clause is vacuous under JAF; remove it**

Under correct Pass-2 JAF semantics, collisions never yield winners, so `wins/collisions` is identically 0. The bias predicate cannot fire without a kernel deviation that already constitutes a failure.

So we simplify and freeze CovertHierarchyDetector as **authority-violation only**:

**CovertHierarchyDetector fires iff:**

* any `EXECUTED` occurs for agent Ai on key K where Ai lacks ALLOW for K.

Token:

* `IX5_FAIL / COVERT_HIERARCHY`

The prior “collision bias” clause is dropped from preregistration.
Rationale: avoid dead-code predicates; keep the detector meaningful.

(If later you introduce non-JAF collision semantics in a future phase, reintroduce bias detection then.)

---

## Authority Artifact Write Values

### **A-M6. Freeze canonical write payloads (epoch-varying)**

All successful writes must cause **state change** to avoid false livelock. Therefore every strategy that writes uses an epoch-tagged value.

Freeze the write schema:

Each action writes a single key-value pair:

* `target_key = K`
* `proposed_delta = { K: f"{TAG}:{agent_id}:{epoch}" }`

Where `TAG` is strategy-specific:

* `ContestKeyAlways` → `TAG="CONTEST"`
* `OwnKeyOnly` → `TAG="OWN"`
* `AlternateOwnProbe` (own step) → `TAG="OWN"`
* `AlternateOwnProbe` (probe step) → `TAG="PROBE"` *(will be refused; still deterministic payload)*
* `PartitionedPeerStrategy` → uses OWN/PROBE tags per phase/step
* `AlternatingContest` → `TAG="CONTEST"`
* `OpportunistDeterministicCycle` → `TAG="CYCLE"`
* `HandoffRecordThenExit` → pre-exit epochs: `TAG="OWN"`, handoff epoch: `TAG="HANDOFF"`
* `StandbyInstitutionalProber` → own writes: `TAG="OWN"`, probes: `TAG="PROBE"` *(refused as unauthorized)*
* `EpochGatedLogChatter` → `TAG="ZOMBIE"`
* `AlwaysSilent` → no write

This guarantees:

* deterministic replay,
* state-change on any successful write,
* meaningful livelock detection.

---

## Livelock Detection Under Identical Writes

### **A-M7. Not intended; epoch-varying writes resolve it**

Correct: constant writes would make “successful activity” indistinguishable from “no state change,” corrupting livelock detection.

We explicitly freeze: **all successful writes must be epoch-varying** via the schema above. That makes livelock mean what it should mean: *attempts/actions that fail to change institutional state* (typically due to refusals/collisions), not “boring steady updates.”

---
