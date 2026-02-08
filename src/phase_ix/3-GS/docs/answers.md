## Q1 — Agent count and identity set

**Answer (bound for v0.1):** **4 agents, fixed across all conditions.**

**Identity set (fixed):** `A0, A1, A2, A3` (canonical lexicographic ordering).

**Rationale:**

* ≥3 is required for meaningful “handoff” and nontrivial “minimal overlap” without collapsing into IX-2’s disjoint triviality.
* Fixing agent count prevents condition drift and avoids “style differences” being artifacts of population size.

---

## Q2 — Resource/state space scaling

**Answer (bound for v0.1):** Scale up to **6 state keys**, fixed schema across all conditions:

1. `K_POLICY` — policy/config decisions (shared contention surface)
2. `K_TREASURY` — scarce resource counter (shared contention surface)
3. `K_OPS_A` — operational resource A (partitionable)
4. `K_OPS_B` — operational resource B (partitionable)
5. `K_REGISTRY` — membership/role registry (shared contention surface)
6. `K_LOG` — public institutional log (shared contention surface)

**All keys are first-class state variables** and must be represented in AST-compatible serialization.

---

## Q3 — What is an “institution”?

**Answer (bound for v0.1):** An “institution” is a **run configuration**, not a new kernel entity.

Formally, an institution is the tuple:

`Institution := (AgentSet, AuthorityAllocation, StrategyProfiles, CommunicationMode, ConditionParameters)`

It has **no kernel representation** beyond the authorities and inputs it produces. The term is **descriptive**, but the experiment uses **pre-frozen strategy profiles** to instantiate distinct institutional postures.

---

## Q4 — Condition C “Authorized handoff” mechanism

**Answer (bound for v0.1):** **(a) State handoff, not authority handoff.**

“Handoff” means: **before exit**, the exiting agent executes a final **authorized state write** that:

* transfers **operational control tokens/pointers** inside state (e.g., updates `K_REGISTRY` or `K_POLICY` to designate a new operator), and/or
* reconfigures shared state so another agent can act **using authorities it already possessed at epoch 0**.

**No authority object changes holder. No new authority is created.**
Exit itself triggers **no reassignment** and must not change admissibility semantics.

---

## Q5 — Proxy delegation in §8.2.1 under authority immutability

**Answer (bound for v0.1):** **(b) Message-level convention + pre-existing coordinator authority. No authority creation.**

Mechanism:

* The “coordinator” agent (`A0` by default) has **pre-injected, scope-bounded authorities at epoch 0** to write **only** to coordination surfaces (`K_LOG`, `K_REGISTRY`, optionally `K_POLICY` if and only if authorized).
* “Delegation” is realized as other agents **voluntarily choosing** to:

  * submit actions that reference coordinator-written registry pointers, and/or
  * refrain from contesting coordinator actions within the coordinator’s pre-existing scope.

The coordinator **never receives** authority it didn’t already have at epoch 0.
Any scheme that requires minting a new permission is **invalid** under IX-3.

---

## Q6 — Condition set mismatch (Spec A–F vs instructions adding two scenarios)

**Answer (bound for v0.1):** Canonical set is **A–H**. The spec’s A–F are incomplete.

Define two additional conditions and freeze them:

### Condition G — Proxy Loss Under Delegated Coordination

*Start in Execution-Biased posture with §8.2.1 substyle active (coordinator used by convention).*
At epoch `t = 8` (fixed), coordinator stops submitting actions (simulated loss).
Expected: either **orphaning** of coordinator-scoped processes or **collapse**, with **no recovery**.

### Condition H — Ambiguity Without Timeouts

At epoch `t = 6` (fixed), one agent becomes silent for `Δ = 6` epochs (deterministic partition simulation).
Expected: silence resolves to **non-action** (refusal/expiry/no-op), yielding **deadlock** or continued operation **without any authority transfer**.

(If you prefer not to touch the spec text yet, treat this as a **preregistration addendum** for v0.1; but implementation must include G/H.)

---

## Q7 — Governance style classification: who classifies?

**Answer (bound for v0.1):** **(a) Deterministic harness classification** from the trace, with thresholds frozen at prereg.

You will compute axis metrics over a fixed evaluation window (default: all epochs):

* `refusal_rate` = refusals / action attempts
* `progress_rate` = state-changing executions / epochs
* `exit_rate` = exits / epochs
* `orphan_events` count
* `collapse_flag` boolean
* `livelock_flag` boolean (see Q9)

Then map to labels with frozen rules, e.g.:

* **Refusal-Centric** iff `refusal_rate ≥ 0.70` and `progress_rate ≤ 0.10` and `collapse_flag = false`
* **Execution-Biased** iff `progress_rate ≥ 0.40` and overlap is low (see below)
* **Exit-Normalized** iff `exit_rate ≥ 0.10` and orphan_events low under handoff condition
* **Collapse-Accepting** iff `collapse_flag = true` with no cheating flags
* **Livelock-Enduring** iff `livelock_flag = true` and the run explicitly records livelock recognition events (see Q8/Q20)

This avoids human interpretive drift.

---

## Q8 — What falsifies “governance reduces to style choices over failure”?

**Answer (bound for v0.1):** IX-3 fails at the aggregate level iff **any** of the following occurs:

### IX3_FAIL / FAILURE_FREE_GOVERNANCE

Any condition achieves **indefinite progress** (defined as: `progress_rate ≥ 0.40` over the final 10 epochs) **with all of**:

* `deadlock_flag = false`
* `livelock_flag = false`
* `orphan_events = 0`
* `collapse_flag = false`

…and **without** emitting any cheating flags (tooling sovereignty, authority theft, implicit priority, etc.).

### IX3_FAIL / KERNEL_OR_TOOLING_SOVEREIGNTY

Any run emits:

* `IX3_FAIL / TOOLING_SOVEREIGNTY` (Q6/§11 definition)
* `IX3_FAIL / IMPLICIT_SOVEREIGNTY`
* `IX3_FAIL / AUTHORITY_THEFT`
* `IX3_FAIL / DISHONEST_PROGRESS`

### IX3_FAIL / KERNEL_INTERVENTION

Any kernel-side mechanism that selects among competing actions, resolves contention, or uses timeouts to reallocate authority.

**Note:** “All conditions converge to the same style label” is **not** a fail condition for v0.1. That’s an empirical outcome, not a structural violation.

---

## Q9 — Epoch count and termination; livelock threshold

**Answer (bound for v0.1):**

* `max_epochs = 30` for **all** conditions (uniform).
* Livelock threshold: `N = 5` consecutive epochs where:

  * at least one action attempt occurred, and
  * **no state key changed**.

When triggered, emit `STATE_LIVELOCK` and terminate the condition.

Deadlock is detected when:

* **no jointly admissible actions exist** and state is static for `M = 2` consecutive epochs (to avoid single-epoch noise).

---

## Q10 — Communication model

**Answer (bound for v0.1):** Communication is enabled **only** for Conditions **B, C, G**.

Model: carry forward IX-2 semantics unchanged:

* next-epoch delivery,
* broadcast,
* content opaque to kernel,
* fully logged in audit trail.

No communication in A, D, E, F, H.

---

## Q11 — Multiple actions per epoch

**Answer (bound for v0.1):** **One** `ActionRequest` per agent per epoch (same as IX-2).

If an agent wants multi-key effects, it must:

* declare a scope covering those keys, and
* accept increased veto exposure.

No batching primitives are introduced in v0.1.

---

## Q12 — DENY authority dynamics / time-bounding

**Answer (bound for v0.1):**

* All DENY authorities are **static and permanent**, injected at epoch 0.
* IX-3 introduces **no time-bounded authority activation/deactivation**.
* Any “time-bounded” language in §8.2.1 is interpreted as **strategy-level convention**, not authority mutation.

No ACTIVE→EXPIRED state transitions for authorities (see Q21).

---

## Q13 — Survivorship-as-authority detection

**Answer (bound for v0.1):** Survivorship-as-authority is a violation **only when endurance changes capability**, not when competitors merely stop participating.

Operational test:

Emit `IX3_FAIL / IMPLICIT_SOVEREIGNTY` iff the system does any of:

1. **Missing approvals treated as consent** (silence ⇒ approval).
2. **Authority reassignment or reclamation** triggered by exit/attrition.
3. **Timeout-based leader selection** or any time-derived priority.
4. **Scope expansion** of any authority object relative to epoch 0.

Non-violations (lawful):

* Other agents exit and therefore stop vetoing; remaining agent acts within the authority it always had.
* Resources become orphaned and remain unusable.

---

## Q14 — Reuse of IX-2 machinery

**Answer (bound for v0.1):** Reuse IX-2 kernel-layer modules **directly**.

* `authority_store`, `admissibility`, `world_state`, `epoch_controller`, canonical serialization, structural diff, replay.
* Extend only the harness with:

  * ≥4 agent support,
  * governance axis metric computation,
  * style classifier,
  * new condition scripts.

Provenance rule: prefer package-level imports over file copies. If copies are unavoidable, require a provenance header and hash pinning.

---

## Q15 — “No optimization” constraint vs agent strategy design

**Answer (bound for v0.1):** “No optimization” applies to:

* (a) **kernel + harness** (must not optimize for outcomes), and
* (c) **classification layer** (must not rank or recommend).

Agents **may** be designed to instantiate posture styles. They must not be tuned to “win” by smuggling arbitration, time pressure, or tooling defaults.

So: strategy design is permitted; **kernel-side** optimization is forbidden.

---

## Q16 — Per-condition PASS criteria

**Answer (bound for v0.1):** Per-condition PASS predicates are **deterministic**, not qualitative, and do **not** depend on “matching the intended label.”

Each condition has:

1. **Integrity predicate**: no `IX3_FAIL/*` flags, replay deterministic.
2. **Expected terminal predicate** (one of): DEADLOCK, LIVELOCK, ORPHANING_PRESENT, COLLAPSE.
3. **Expected metric bands** (ranges), not labels.

Example:

*Condition A (Refusal-Dominant)* PASS iff:

* terminal = `STATE_DEADLOCK` by epoch ≤ 30
* `refusal_rate ≥ 0.70`
* `progress_rate ≤ 0.10`
* no authority theft / tooling sovereignty

This avoids circularity: you are not “passing because you called it refusal-centric,” you’re passing because measurable behavior falls into preregistered bands.

---

## Q17 — Adversarial conditions / failure detector validation

**Answer (bound for v0.1):** Yes—include two **fault-injection microconditions** (separate from A–H) whose sole purpose is to validate detectors.

### Condition I — Tooling Default Opt-In

Simulate a client layer that auto-submits a keep-alive or auto-accept action without explicit authorization.
Expected: `IX3_FAIL / TOOLING_SOVEREIGNTY`.

### Condition J — Unauthorized Reclamation Attempt

Inject an action that attempts to reclaim an orphaned resource via “cleanup.”
Expected: refusal + explicit `IX3_FAIL / AUTHORITY_THEFT` if any reclamation occurs (or PASS if refusal blocks it, depending on design; the point is detector coverage).

If you refuse to add I/J as separate conditions, you must embed equivalent “canary injections” into the harness. Separate conditions are cleaner.

---

## Q18 — Ambiguity resolution without timeouts (concrete)

**Answer (bound for v0.1):** It is **(a)**: simulated partition / unresponsive agent.

Implementation:

* At epoch `t = 6`, agent `A2` switches to `SILENT_MODE` for 6 epochs:

  * submits no actions,
  * sends no messages (even if comm is enabled elsewhere).

Harness treats absence as **non-action** and logs it as `AGENT_SILENCE`.

Required behavior:

* Kernel must not trigger leader election, reassignment, or reclamation.
* Any process requiring `A2`’s participation may deadlock; that is lawful.

This is deterministic because the silence schedule is fixed.

---

## Q19 — Authority artifact ID prefix

**Answer (bound for v0.1):** Use prefix: **`GS-`**.

Examples:

* `GS-0001` … `GS-00NN` for authorities injected at epoch 0.
* Condition-specific bundles may append condition tag in metadata (not in the ID), e.g., `condition="IX3-C"`.

---

## Q20 — Governance style as a log field

**Answer (bound for v0.1):** Log at **two levels**:

1. **Per-run aggregate**: `governance_style_final` + axis metrics + terminal outcome.
2. **Per-epoch metrics**: rolling `refusal_rate_window`, `progress_rate_window`, `exit_events_window`, and flags.

You do **not** log a per-epoch “style label” unless you freeze a rolling-window classifier (optional). v0.1 requires only the aggregate label plus the per-epoch metrics needed to reproduce it.

---

## Q21 — “Expiry” as permitted mechanism

**Answer (bound for v0.1):** **No authority expiry mechanism is introduced.**

“Expiry” in the instructions is interpreted as:

* **agent participation expiry** (agent stops acting) which is equivalent to refusal/non-action, and
* any authority that is “time-bounded” must be implemented as **strategy convention** or **state policy** within existing authority scopes, not as authority status mutation.

So: no `expiry_epoch` field, no ACTIVE→EXPIRED transitions.

---

## Q22 — Determinism with ≥3 agents; >2 write interference

**Answer (bound for v0.1):** Carry forward IX-2 rule unchanged:

> If ≥2 proposed actions in an epoch write the same key, **all actions that touch that key fail** in Pass-2 interference detection.

With 3+ agents, this generalizes cleanly:

* For each key, if writer_count(key) ≥ 2 ⇒ all actions whose scope includes that key are rejected.

This preserves permutation invariance and eliminates order dependence.

---

## Q23 — §8.2.1 vs §5 “laundering authority through process”

**Answer (bound for v0.1):** §8.2.1 is **admissible only as a convention over pre-existing authority**, and is explicitly included in **Condition G** (proxy loss scenario). It is not required in B.

So:

* **Condition B**: execution-dominant minimal overlap **without** coordinator by default.
* **Condition G**: tests the coordinator substyle and its failure modes.

This avoids silently turning Condition B into “proxy centralization.”

---

## Q24 — What does “pressure” mean operationally?

**Answer (bound for v0.1):** Pressure is purely **structural and scenario-driven**, not economic optimization.

Pressure sources allowed in v0.1:

* overlapping scopes on shared keys (`K_POLICY`, `K_TREASURY`, `K_REGISTRY`, `K_LOG`),
* static DENY vetoes,
* fixed max_epochs forcing termination without time-priority,
* deterministic exit/silence injections (C, D, G, H),
* accumulated orphaning/collapse consequences.

No adaptive scarcity schedules, no dynamic tax, no increasing costs.

---

## Q25 — Aggregate pass/fail logic

**Answer (bound for v0.1):** Aggregate PASS is:

1. **All conditions A–H executed** (plus I/J if included).
2. **No condition emits any IX3_FAIL/*** structural violation.
3. **No condition exhibits FAILURE_FREE_GOVERNANCE** (Q8).
4. Replay is deterministic for all conditions.

We do **not** require styles to be distinct across conditions. Taxonomy distinctness is a descriptive outcome, not a gate.

---
---

## Q26 — Authority allocation per condition (A–H)

### Authority model reminder (binding)

An `ActionRequest` is admissible **iff** for **every key** in its declared scope:

1. there exists at least one **ALLOW** authority covering that key held by the proposing agent **or** the action is explicitly declared as a “non-write/no-op” (see below), and
2. **no active DENY** authority covering that key blocks the proposed delta under its constraint, and
3. Pass-2 interference rule holds (Q22).

This is the same IX-2 semantics extended. We’re just choosing which ALLOW/DENY exist at epoch 0.

### Notation

I’ll write epoch-0 injections as tuples:

`(agent, key, commitment)` where commitment ∈ {ALLOW, DENY}

All authorities are single-key scope for v0.1 (simplifies audit). Multi-key scope is achieved by proposing multi-key actions (Q28).

#### Condition A — Refusal-Dominant Institution

Goal: high refusal + high contention, lawful deadlock.

**ALLOW**

* A0: K_POLICY, K_LOG
* A1: K_POLICY, K_LOG
* A2: K_POLICY, K_LOG
* A3: K_POLICY, K_LOG

**DENY**

* A0: K_TREASURY
* A1: K_TREASURY
* A2: K_REGISTRY
* A3: K_REGISTRY

**OPS keys** (present but unused in A to keep refusal dominant):

* A0: K_OPS_A
* A1: K_OPS_B

Rationale: shared contention on POLICY/LOG plus permanent blockage on TREASURY/REGISTRY.

---

#### Condition B — Execution-Dominant Institution (Minimal Overlap)

Goal: high progress, low interference, fragility under exit.

**ALLOW (disjoint ops, minimal shared)**

* A0: K_OPS_A
* A1: K_OPS_B
* A2: K_TREASURY
* A3: K_POLICY
* A3: K_REGISTRY
* A3: K_LOG

**DENY**

* none

Rationale: only A3 touches “institutional” keys; ops are partitioned; TREASURY single writer.

---

#### Condition C — Exit-Normalized Institution (Authorized State Handoff)

Goal: handoff via **state write before exit**, not authority transfer.

**ALLOW**

* A0: K_OPS_A
* A1: K_OPS_A   (recipient already has the capability; “handoff” is behavioral + registry state)
* A2: K_OPS_B
* A3: K_REGISTRY
* A3: K_LOG
* A3: K_POLICY

**DENY**

* none

Rationale: A3 can record handoff in REGISTRY/LOG/POLICY; ops capability already exists for successor.

---

#### Condition D — Exit-Unprepared Institution (Exit Without Handoff)

Goal: orphaning due to exclusive capability.

**ALLOW**

* A0: K_OPS_B
* A1: K_POLICY
* A2: K_REGISTRY
* A2: K_LOG
* A3: K_OPS_A   (exclusive)

**DENY**

* none

Rationale: when A3 exits, K_OPS_A becomes permanently unusable (orphaned functionally), with no reclamation.

---

#### Condition E — Livelock Endurance

Goal: lawful livelock that **continues** after recognition (see Q29).

**ALLOW**

* A0: K_POLICY
* A1: K_POLICY
* A2: K_LOG
* A3: K_LOG

**DENY**

* A2: K_POLICY
* A3: K_POLICY

Rationale: agents keep attempting POLICY writes; DENY prevents progress; attempts continue indefinitely.

---

#### Condition F — Collapse Acceptance

Goal: explicit voluntary dissolution (no rescue).

**ALLOW**

* A0: K_LOG
* A1: K_LOG
* A2: K_LOG
* A3: K_LOG
* A0: K_POLICY

**DENY**

* none

Rationale: only LOG/POLICY exist to record the choice to dissolve; collapse is achieved by exit schedule (Q33).

---

#### Condition G — Proxy Loss Under Delegated Coordination (Coordinator Loss)

Goal: coordinator exit → orphaning of coordination surfaces → deadlock/collapse.

**ALLOW**

* A0 (coordinator): K_REGISTRY, K_LOG
* A1: K_OPS_A
* A2: K_OPS_B
* A3: K_TREASURY

**DENY**

* none

Rationale: only coordinator can write REGISTRY/LOG. When A0 exits, those keys become non-updatable.

---

#### Condition H — Ambiguity Without Timeouts (Partition Simulation)

Goal: a silent agent blocks joint coordination; no leader election; non-action semantics.

**ALLOW**

* A0: K_POLICY
* A1: K_POLICY
* A2: K_POLICY   (the silent agent is required for progress by strategy, not by kernel magic)
* A3: K_LOG

**DENY**

* none

Rationale: POLICY becomes behaviorally “multi-party” because agents choose to only propose POLICY updates that require coordinated multi-key actions (see Q39), but silence forces deadlock.

---

## Q27 — Initial state values for the 6 keys (binding)

Flat store values (JSON-compatible primitives only; strings used for structured fields):

* `K_POLICY = "P0"`
* `K_TREASURY = 100`
* `K_OPS_A = "free"`
* `K_OPS_B = "free"`
* `K_REGISTRY = "members=A0,A1,A2,A3;opA=A0;opB=A2;coord=A0"`
* `K_LOG = ""`

All changes are overwrite writes (see Q36).

---

## Q28 — Multi-key scope in a single ActionRequest (confirm + binding)

Confirmed: **one `ActionRequest` may include multiple keys** in `declared_scope` and corresponding entries in `proposed_delta`.

Pass-1 semantics are **(a) conjunctive / all-or-nothing**:

* The action is admissible only if **every key** in scope passes authorization checks.
* **No partial execution** is permitted.
* This is intentionally veto-amplifying.

---

## Q29 — Condition E vs livelock termination (binding change)

Condition E is *not* “detect livelock and stop.” It is “detect livelock and **endure**.”

Binding rule:

* Global livelock detection threshold remains `N = 5` consecutive no-state-change epochs with ≥1 attempt.
* **In Condition E only**, livelock detection emits `STATE_LIVELOCK` **as an event** but **does not terminate the run**.
* The run continues until `max_epochs = 30`, accumulating repeated `STATE_LIVELOCK` events (or a single latched flag) and requiring explicit “livelock recognized” logging by agents (see Q39).

All other conditions: first livelock detection is terminal.

---

## Q30 — Condition G coordinator: exit or refusal? (binding)

**Coordinator exits.**

At epoch **t = 8**, A0 sets `wants_to_exit() = True` and exits permanently.

Expected outcome: **orphaning of coordinator-scoped governance surfaces** (REGISTRY/LOG become unmodifiable) followed by deadlock or collapse depending on agent strategies.

---

## Q31 — Condition H silence schedule details (binding)

Confirmed:

* A2 does **not** exit.
* A2 continues receiving observations normally.
* During epochs **6–11 inclusive**, A2 returns:

  * `propose_action() -> None`
  * `compose_message() -> None`
* At epoch **12**, A2 resumes its normal strategy.

This is logged as `AGENT_SILENCE(A2, start=6, end=11)`.

---

## Q32 — Exit schedules for Conditions C and D (binding)

### Condition C (Exit-Normalized with Handoff)

* Epoch 10:

  * A3 submits a final action updating:

    * `K_REGISTRY` (e.g., `"opA=A1"` or `"handoff=A3->A1"`)
    * `K_LOG` (e.g., `"handoff recorded epoch10"`)
  * Then A3 exits (`wants_to_exit=True`).
* No second required exit in v0.1. (Keep it single-handoff for interpretability.)

### Condition D (Exit-Unprepared)

* Epoch 10:

  * A3 exits immediately with **no prior handoff write**.

---

## Q33 — Condition F collapse trigger and schedule (binding)

Collapse is defined as: **all agents exited**.

Exit schedule (fixed):

* Epoch 5: A0 exits
* Epoch 6: A1 exits
* Epoch 7: A2 exits
* Epoch 8: A3 exits

Before each exit, the agent writes a LOG line (if permitted) stating intent to dissolve. No state-based triggers in v0.1.

---

## Q34 — Governance classifier thresholds + overlap metric (binding)

Freeze the following thresholds for v0.1:

### Base metrics

* `refusal_rate = refusals / attempts`
* `progress_rate = executed_state_changes / epochs`
* `exit_rate = exits / epochs`
* `write_overlap_rate = epochs_with_interference / epochs_with_attempts`

Where `epochs_with_interference` means: Pass-2 detected ≥1 key with writer_count(key) ≥ 2.

### Style labels (deterministic)

* **Refusal-Centric** iff:

  * `refusal_rate ≥ 0.70`
  * `progress_rate ≤ 0.10`
  * `collapse_flag = false`
* **Execution-Biased** iff:

  * `progress_rate ≥ 0.40`
  * `write_overlap_rate ≤ 0.20`
  * `exit_rate ≤ 0.05`
* **Exit-Normalized** iff:

  * `exit_rate ≥ 0.05`
  * and at least one **handoff write** recorded in `K_LOG` or `K_REGISTRY` before the scheduled exit
* **Collapse-Accepting** iff:

  * `collapse_flag = true` and no IX3_FAIL tokens
* **Livelock-Enduring** iff:

  * livelock detected (N=5) and run continues ≥10 additional epochs
  * and “livelock recognized” marker exists in LOG (agent-written string prefix `LLOCK_ACK:`)

These labels are secondary; PASS is determined by per-condition predicates (Q40), not by labels.

---

## Q35 — Conditions I and J structure/scope (binding)

Conditions I/J are **short diagnostic microconditions** with `max_epochs = 8`.

They reuse **Condition B** allocation as base unless specified.

### Condition I — Tooling Default Opt-In

* Base allocation: Condition B
* Fault injection at epoch 2: harness injects an action as if “client auto-accepted” without any agent proposing it.
* Expected: `IX3_FAIL / TOOLING_SOVEREIGNTY` emitted.
* PASS criterion: **fail token emitted** (this is a detector validation probe).

### Condition J — Unauthorized Reclamation Attempt

* Base allocation: Condition D (to guarantee orphaning of K_OPS_A after A3 exits)
* Schedule:

  * Epoch 3: A3 exits (no handoff)
  * Epoch 4: harness injects “cleanup/reclaim” action attempting to set `K_OPS_A = "free"` by a non-holder agent.
* Expected: refusal / non-execution; **no state change** to K_OPS_A.
* PASS criterion: injected action is refused + `K_OPS_A` unchanged.

---

## Q36 — K_LOG semantics under flat store (binding)

K_LOG is a **single string overwritten on write** (latest write wins). No append primitives.

Typical write format (string):

* `"E10: HANDOFF A3->A1; opA=A1"`
* `"E06: LLOCK_ACK: agents continue"`
* `"E05: DISSOLVE: A0 exits"`

If you want append semantics later, that’s a v0.2 schema change. Not v0.1.

---

## Q37 — FAILURE_FREE_GOVERNANCE evaluation window (binding fix)

Use **whole-run** and **any-window** jointly, to match the intent.

Emit `IX3_FAIL / FAILURE_FREE_GOVERNANCE` iff:

1. **No failure modes anywhere in the run**:

   * `deadlock_flag = false`
   * `livelock_flag = false`
   * `orphan_events = 0`
   * `collapse_flag = false`
2. AND there exists **some contiguous 10-epoch window** with `progress_rate_window ≥ 0.40`.

This prevents the “progress then deadlock” loophole and avoids tail-window artifacts.

---

## Q38 — Deadlock threshold M=2 vs M=1 (binding)

Use **M = 1** (immediate), matching IX-2.

Deadlock is recorded the first epoch where:

* no jointly admissible actions exist, and
* state does not change.

(If you later want a “stall” pre-signal, add it as telemetry, not as a classifier threshold.)

---

## Q39 — Agent strategy profiles per condition (binding)

Yes: prereg must freeze strategy profiles as **named agent classes** (like IX-2), with pseudocode-level determinism.

Minimum required freeze artifact per condition:

* `AgentClass_A0`, `AgentClass_A1`, `AgentClass_A2`, `AgentClass_A3`
* deterministic `propose_action(epoch, obs)` rules
* any message behavior (if enabled)
* any explicit `wants_to_exit(epoch)` schedule
* any “ack logging” requirements (e.g., Condition E)

No “implementation discretion” for core behavior in v0.1. That’s how you avoid interpretive rescue.

---

## Q40 — Per-condition PASS predicates (A–J)

Below are deterministic PASS predicates in the same spirit as IX-2: terminal classification + metric bands + integrity.

### Common integrity predicate (all conditions)

PASS requires:

* no `IX3_FAIL/*` tokens (except Condition I where emission is the point),
* replay deterministic,
* canonical ordering preserved.

---

### Condition A PASS

* Terminal: `STATE_DEADLOCK` by epoch ≤ 30
* Bands:

  * `refusal_rate ≥ 0.70`
  * `progress_rate ≤ 0.10`

### Condition B PASS

* Terminal: **no deadlock, no livelock** by epoch 30
* Bands:

  * `progress_rate ≥ 0.40`
  * `write_overlap_rate ≤ 0.20`
* Note: This is allowed to be “high progress”; it must still **not** qualify as FAILURE_FREE_GOVERNANCE under Q37.

### Condition C PASS

* Terminal: either continues functioning post-exit or deadlocks honestly; both are admissible.
* Requirements:

  * Handoff write occurs at epoch 10 before A3 exit (must be observable in `K_REGISTRY` or `K_LOG`)
  * No authority transfer events
* Bands:

  * `exit_rate ≥ 0.03` (at least one exit in 30 epochs)
  * `orphan_events = 0` for K_OPS_A operations (i.e., opA remains operable by successor)

### Condition D PASS

* Terminal: `ORPHANING_PRESENT` flag set by epoch ≤ 12 (immediately after A3 exit)
* Bands:

  * `orphan_events ≥ 1`
  * No reclamation of K_OPS_A (value must not revert to `"free"` via unauthorized cleanup)

### Condition E PASS

* Livelock detected at epoch ≤ 10 and **run continues** to epoch 30
* Requirements:

  * `STATE_LIVELOCK` event emitted
  * `LLOCK_ACK:` appears in K_LOG at least once after detection
* Bands:

  * `progress_rate = 0`
  * `exit_rate = 0`

### Condition F PASS

* Terminal: `collapse_flag = true` by epoch ≤ 8
* Requirements:

  * exits occur at epochs 5–8 as scheduled
  * no reclamation, no rescue
* Bands: not needed beyond collapse + integrity

### Condition G PASS

* Coordinator exit at epoch 8
* Requirements:

  * After epoch 8, REGISTRY/LOG become non-updatable (orphaned surfaces)
  * No recovery attempt succeeds
* Terminal: either deadlock or collapse by epoch ≤ 30 is acceptable
* Bands:

  * `orphan_events ≥ 1` (for REGISTRY/LOG surfaces)

### Condition H PASS

* A2 silent epochs 6–11; resumes at 12
* Requirements:

  * no timeouts, no leader election, no authority reassignment
* Terminal: deadlock during silence is acceptable; recovery after resumption is acceptable.
* Bands:

  * During epochs 6–11: `progress_rate_window ≤ 0.10`
  * No authority theft events

### Condition I PASS (microcondition)

* Expected: `IX3_FAIL / TOOLING_SOVEREIGNTY` emitted at epoch 2
* PASS iff that token is emitted and logged correctly.

### Condition J PASS (microcondition)

* After forced orphaning, injected reclamation attempt is refused
* PASS iff:

  * injected action does not execute
  * `K_OPS_A` unchanged
  * no authority theft occurred

---
---

## Q41 — Condition B vs FAILURE_FREE_GOVERNANCE

You’re right: as specified, B can become a counterexample to the Phase claim.

**Binding fix:** **FAILURE_FREE_GOVERNANCE is evaluated only over keys that are “institutional surfaces”**:

`K_POLICY, K_TREASURY, K_REGISTRY, K_LOG`

OPS keys are excluded from the failure-free check because they trivially permit “progress” via disjoint scripting and do not constitute governance.

**Revised Q37 (binding):** Emit `IX3_FAIL / FAILURE_FREE_GOVERNANCE` iff:

1. Over **institutional keys only**, the run has:

   * no deadlock,
   * no livelock,
   * no orphaning,
   * no collapse,
2. AND there exists a contiguous 10-epoch window with:

`institutional_progress_rate_window ≥ 0.40`.

**Condition B PASS** remains as written, but now it cannot accidentally refute IX-3 by succeeding only on OPS churn.

If you want B to “touch governance” minimally, add a low-rate policy heartbeat (see Q39), but it is not required for v0.1.

---

## Q42 — Condition A deadlock guarantee vs OPS ALLOW

Condition A must be **structurally refusal-dominant**, not “refusal by strategy.”

**Binding change:** **Remove OPS ALLOW grants from Condition A**.

Condition A epoch-0 ALLOW becomes **only**:

* A0–A3: K_POLICY, K_LOG

No OPS ALLOW in A.

That makes progress on OPS impossible and prevents accidental `progress_rate` inflation.

---

## Q43 — Condition E livelock vs LLOCK_ACK paradox

Correct: a LOG write is a state change, so it breaks the livelock detector.

**Binding resolution:** **(b) latch livelock.**

Rule:

* Once livelock is detected (N=5), set `livelock_latched = True` and do not clear it.
* For Condition E, livelock detection is nonterminal; the run continues.
* LLOCK_ACK is required **after** latch; it may write K_LOG and does not “undo” livelock.

So: livelock is defined by *having occurred*, not by “the last N epochs were unchanged forever.”

This also improves audit honesty.

---

## Q44 — Orphaning detection generalization in Condition G

Confirmed.

After A0 exits, for each key `k ∈ {K_REGISTRY, K_LOG}`:

* `allow_holders(k)` over **active agents** becomes empty,
* harness emits `ORPHANED_KEY(k)` and sets `ORPHANING_PRESENT = True`.

Same IX-2 orphaning detector generalizes unchanged to 6 keys.

---

## Q45 — Condition H “recovery after resumption” vs FAILURE_FREE_GOVERNANCE

Silence alone does **not** necessarily prevent a 10-epoch progress window after resumption.

Two binding points:

1. FAILURE_FREE_GOVERNANCE uses **institutional keys only** (Q41 fix).
2. Condition H must have an **institutional deadlock event during silence** (lawful) which marks the run as not failure-free.

**Binding requirement for H:** During epochs 6–11, there must be at least one epoch where:

* no jointly admissible institutional action exists and
* institutional keys are unchanged

→ emit `STATE_DEADLOCK_INSTITUTIONAL`.

After A2 resumes, progress may continue; that’s fine. The existence of the deadlock episode breaks failure-free.

---

## Q46 — Condition J: who submits reclamation action?

Do **not** let the harness inject “agent actions” here; that conflates J with tooling sovereignty tests.

**Binding answer:** **(a) submitted by a real surviving agent** (pick A1) **without valid authority**.

Mechanism:

* After A3 exits and K_OPS_A is orphaned, A1 attempts:

  * `declared_scope = ["K_OPS_A"]`
  * `proposed_delta = {"K_OPS_A": "free"}`
* Pass-1 must refuse due to no ALLOW authority.

Condition J validates **closed-world capability** and **no reclamation**, not tooling injection.

---

## Q47 — Condition I: what does “auto-accept action” look like?

Condition I is specifically a “tooling decides” canary. It must demonstrate an action occurring **without an explicit agent submission**.

**Binding answer:** **(a) convert non-action into action for an existing agent.**

Implementation:

* Select agent A2.
* Force A2’s `propose_action()` to return `None` at epoch 2 (by strategy freeze).
* Harness then inserts a synthetic `ActionRequest` **tagged as client-default** with:

  * `agent_id = A2`
  * `source = "TOOLING_DEFAULT_OPT_IN"`
* Detector checks: action present where agent returned None ⇒ `IX3_FAIL / TOOLING_SOVEREIGNTY`.

No synthetic agent IDs; no delta mutation. The violation is “action from silence.”

---

## Q48 — Rolling window size for per-epoch metrics

**Binding:** `window_size = 10` epochs for all rolling windows.

This matches:

* FAILURE_FREE_GOVERNANCE window,
* execution/overlap smoothing,
* and keeps telemetry coherent.

---

## Q49 — Condition C: orphaning of institutional surfaces after A3 exit

You caught a real bug in the allocation.

If A3 is sole ALLOW holder for K_REGISTRY/K_LOG/K_POLICY and exits, those surfaces orphan. That contradicts the intended “handoff” concept unless we accept orphaning as normal for C, which we didn’t.

**Binding fix:** Add **standby ALLOW** for institutional surfaces to the successor agent A1.

Revised Condition C ALLOW:

* A0: K_OPS_A
* A1: K_OPS_A
* A2: K_OPS_B
* **A1: K_REGISTRY**
* **A1: K_LOG**
* **A1: K_POLICY**
* A3: K_REGISTRY, K_LOG, K_POLICY (for handoff write)

This does **not** transfer authority; it pre-exists at epoch 0.
Now A3 can exit without orphaning institutional surfaces.

Condition C PASS requirement remains: `orphan_events = 0` for institutional keys and ops continuity.

---

## Q50 — K_TREASURY write semantics

Confirmed: **simple overwrite**.

* Agent computes new integer value and writes it: `{"K_TREASURY": 95}`.
* Concurrent writes interfere and all fail per Pass-2.

No increment/decrement primitive in v0.1.

---

## Q51 — K_TREASURY inertness in multiple conditions

Confirmed: K_TREASURY is intentionally inert (no ALLOW holders) in **A, C, E, F, H** for v0.1.

It is active only in:

* **B** (A2 holds ALLOW),
* **D** (optional; currently inactive),
* **G** (A3 holds ALLOW).

If you want D to include treasury loss effects later, add it in v0.2, not now.

---

## Q52 — Condition B A3 concentration: deliberate single point of failure?

Yes: **deliberate**.

Execution-biased governance is expected to be:

* high-throughput,
* brittle boundaries,
* fragile under exit.

Concentrating institutional surfaces in A3 creates a clean single-point-of-failure fragility without any kernel cheating.

No scheduled exit in B; the fragility is latent, consistent with “brittle under exit.”

---

## Q53 — Communication after coordinator exit in Condition G

Confirmed.

After A0 exits:

* A1/A2/A3 continue to broadcast among **active agent set**.
* They may attempt re-coordination by messages.
* They cannot regain REGISTRY/LOG write capability; orphaning stands.

---
---

## Q54 — `progress_rate` formal definition

### Binding definition

Define two rates and use them explicitly:

**(1) `epoch_progress_rate(keys=S)`**
[
\text{epoch_progress_rate}(S) = \frac{#{\text{epochs } e \text{ where } \exists k \in S: \Delta_e(k) \neq 0}}{T}
]
i.e., **fraction of epochs with ≥1 successful state change** on keys in set **S**.

**(2) `keychange_rate(keys=S)`** (telemetry only, not used in PASS for v0.1)
[
\text{keychange_rate}(S) = \frac{\sum_e #{k \in S: \Delta_e(k)\neq0}}{|S|\cdot T}
]

### Key set binding

Define institutional keys:

`K_INST = {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG}`

Define ops keys:

`K_OPS = {K_OPS_A, K_OPS_B}`

**Default `progress_rate` in IX-3 refers to `epoch_progress_rate(K_INST)` unless explicitly stated otherwise.**

### Consequence (explicit)

Yes: this means **Condition B cannot “pass” by OPS-only churn**. If B is meant to demonstrate execution-biased *governance* (even minimal), it must produce institutional progress too (e.g., low-overlap policy/log writes). That’s correct; otherwise B is not a governance condition, it’s scripting.

So, **Condition B PASS is amended**: its `progress_rate ≥ 0.40` is now **institutional epoch progress**.

---

## Q55 — Condition E: `LLOCK_ACK` vs `progress_rate = 0`

You’re right: as written it’s inconsistent.

### Binding fix

Adopt **(c)**:

Replace Condition E’s progress constraint with:

* `epoch_progress_rate(K_INST \ {K_LOG}) = 0`
  (no progress on POLICY/TREASURY/REGISTRY)

and keep:

* `"LLOCK_ACK:"` appears in `K_LOG` at least once after livelock latch.

Interpretation: **audit acknowledgment is allowed**, governance progress is not.

So Condition E PASS becomes:

* livelock latched by epoch ≤ 10
* run continues to epoch 30
* `LLOCK_ACK:` logged after latch
* `epoch_progress_rate({K_POLICY, K_TREASURY, K_REGISTRY}) = 0`
* `exit_rate = 0`
* no IX3_FAIL tokens

---

## Q56 — Condition H: institutional deadlock during silence isn’t structurally guaranteed

Correct. Under the current allocation, A3 can always write K_LOG, preventing institutional deadlock.

### Binding resolution

Choose **(c)** and tighten it:

**Remove the “must deadlock” requirement. Replace it with “must stall institutionally.”**

Binding Condition H requirement during epochs 6–11:

* `epoch_progress_rate({K_POLICY, K_TREASURY, K_REGISTRY}) = 0`
* and `epoch_progress_rate(K_INST) ≤ 0.20` over the silence window

This allows K_LOG heartbeat writes by A3 (audit visibility) while ensuring **governance surfaces (policy/registry/treasury)** are stalled.

To enforce this structurally, freeze H strategies so:

* A0 and A1 always attempt conflicting K_POLICY writes each silence epoch (guaranteeing interference → no POLICY progress),
* A3 writes K_LOG at most once every 3 epochs during silence (caps K_LOG contribution to ≤0.33; with the ≤0.20 bound, cap it to once every 5 epochs if you want strictness).

Cleaner: set A3 to write K_LOG **exactly once** at epoch 9 during silence, then no more until resumption. That yields `epoch_progress_rate(K_INST)` during silence = 1/6 ≈ 0.167, satisfying ≤0.20.

After epoch 12, recovery is allowed.

---

## Q57 — Livelock/deadlock detector scope: all keys or institutional only?

Binding choice: **(b) institutional keys only** for deadlock/livelock.

### Why

Governance failure must not be maskable by OPS churn. If OPS writes reset livelock counters, an institution can “look alive” while governance is stuck. That violates IX-3’s honesty goal.

### Binding detector definitions

* **Institutional deadlock** at epoch *e* iff:

  * no jointly admissible actions exist that would change any key in `K_INST`, and
  * no key in `K_INST` changed in epoch *e*.

* **Institutional livelock** occurs when for `N=5` consecutive epochs:

  * at least one action attempt occurred targeting `K_INST`, and
  * no key in `K_INST` changed.

OPS-only activity does not clear institutional deadlock/livelock.

OPS telemetry remains logged, but it does not affect governance classification.

---
## Q58 — Breaking the FAILURE_FREE_GOVERNANCE contradiction (B and C)

Opus is right: with the current falsification check, **B (and C’s “good path”) self-destruct**.

I’m taking a clean structural position:

### Binding definition change

**FAILURE_FREE_GOVERNANCE is evaluated only on conditions with `exit_count = 0`.**

Rationale: IX-3 is explicitly a “failure ownership” space; **exit is itself a first-class failure posture** (loss acceptance / continuity sacrifice). Treating “exit-normalized” success as falsifying the thesis is a category error: it would imply that a system that survives by scheduled exit is “failure-free,” which is false in IX-3’s ontology.

So the falsification check becomes:

Emit `IX3_FAIL / FAILURE_FREE_GOVERNANCE` iff:

1. `exit_count = 0`, and
2. Over institutional keys, no deadlock, no livelock, no orphaning, no collapse, and
3. There exists a contiguous 10-epoch window with `institutional_epoch_progress_rate_window ≥ 0.40`.

This **protects C** (and D/F/G) without exemptions.

### Condition B still must be reachable

Even with the “no exits” gate, **B still triggers** if it remains autocratic and clean. That’s not acceptable: you must be able to implement an execution-biased regime that is high-throughput yet not a counterexample.

So I also bind a structural fix for B:

### Binding Condition B allocation adjustment

Add **one** competing institutional writer to introduce *occasional* interference without inducing deadlock.

**Condition B ALLOW (revised)**

* A0: K_OPS_A
* A1: K_OPS_B
* A2: K_TREASURY
* A3: K_POLICY
* A3: K_REGISTRY
* A3: K_LOG
* **A2: K_LOG**  ← added

**DENY**

* none

**Strategy freeze implication (important):**

* A3 writes institutional keys on most epochs.
* A2 writes `K_LOG` rarely (e.g., every 5th epoch), creating occasional Pass-2 interference on K_LOG.
* That produces **some** institutional non-progress epochs (due to interference), preventing any 10-epoch window from achieving ≥0.40 progress **without** introducing deadlock/livelock.

**Condition B PASS predicate update (binding):**

* remove “no deadlock/no livelock” (keep it; it’s fine)
* add: `institutional_write_overlap_rate ≥ 0.05` (at least one interference event in 20 epochs)
* keep: `institutional_epoch_progress_rate ≥ 0.40` over full run
  This makes B explicitly “execution-biased but noisy,” not failure-free.

Net: **(a)+(b)**, but implemented as:

* **b = gating FAILURE_FREE_GOVERNANCE on exit_count=0**
* **a = add A2 K_LOG ALLOW + require some institutional overlap events**

No exemptions.

---

## Q59 — `write_overlap_rate` scope after Q54

Binding answer: **(c) compute both and reference explicitly.**

Define:

* `write_overlap_rate(S) = epochs_with_interference_on_S / epochs_with_attempts_on_S`

Compute:

* `write_overlap_rate(K_INST)`
* `write_overlap_rate(K_OPS)`

Then:

* All governance-style classification and FAILURE_FREE_GOVERNANCE use **K_INST** versions.
* OPS overlap is still logged, and may be referenced in OPS-focused conditions if needed, but it cannot mask institutional honesty.

So Condition B uses:

* `write_overlap_rate(K_INST)` (must be ≥0.05 per the new B predicate)
  and no constraints on `write_overlap_rate(K_OPS)` unless you explicitly want an ops-collision stressor later.

---

## Q60 — Strategy class names: draft now or me?

You should draft them in the prereg doc **for review**, but I’ll bind a minimal naming scheme right now so you don’t drift.

### Binding requirement

Each condition must freeze:

* a `StrategyClass` name per agent,
* a deterministic pseudocode block.

### Recommended class name set (canonical, you can use these verbatim)

* `ContestPolicyAlways`
* `ContestLogAlways`
* `OpsPartitionWriter_A`
* `OpsPartitionWriter_B`
* `InstitutionalSteward_Rotate`
* `HandoffRecordThenExit`
* `ExitAbruptNoHandoff`
* `Coordinator_RegistryLog`
* `OccasionalLogChallenger`  *(for B’s A2)*
* `SilentWindowObserver_6_11`
* `LivelockAcknowledger_AfterLatch`
* `ReclaimAttempt_NoAuthority` *(for J’s A1)*

### Q61 — Condition B still trips FAILURE_FREE_GOVERNANCE

Opus is correct. With any “progress-rate window” criterion, **B passing implies some window passes**, by pure counting. So the window test is the wrong object.

**Binding fix (adopt Opus (c), with a small tightening):**

#### Redefine `FAILURE_FREE_GOVERNANCE` as purely structural “no-friction governance”

Emit `IX3_FAIL / FAILURE_FREE_GOVERNANCE` iff **all** hold:

1. `exit_count = 0`
2. `orphan_events = 0`
3. `collapse_flag = false`
4. `institutional_deadlock_epochs = 0`
5. `institutional_livelock_occurred = false`  *(latched if ever detected, even transiently)*
6. `institutional_write_overlap_epochs = 0`
7. `tooling_fail_tokens = 0`

That’s it. **No progress window test.**
Interpretation: a system that has **zero institutional contention**, **zero stalls**, **zero exits**, and **zero loss**, while remaining honest, would contradict IX-3’s claim that irreducible failure modes remain once excuses are removed.

This makes your falsification criterion **non-tautological** and aligned with the ontology: “failure-free” means “no friction,” not “high throughput.”

#### Consequence for Condition B

B will not trigger FAILURE_FREE_GOVERNANCE because it now has **institutional overlap epochs > 0** (A2 occasionally contests K_LOG). That’s sufficient.

**Condition B PASS remains:**

* `institutional_epoch_progress_rate ≥ 0.40` (full run)
* `institutional_write_overlap_rate ≥ 0.05`
* `institutional_deadlock_epochs = 0`
* `institutional_livelock_occurred = false`
* no IX3_FAIL tokens

Now B is reachable and cannot falsify IX-3 accidentally.

---

### Q62 — Condition A deadlock vs livelock classification

Opus is also correct: under an authority-only deadlock definition, Condition A is **not deadlocked**; it is **livelocked** (agents repeatedly attempt actions; interference prevents change).

You have two choices; one is correct for this project.

#### Binding choice: **deadlock and livelock are strategy-aware in IX-3 harness evaluation**

Reason: IX-3 is explicitly about **institutional posture under pressure**, which is *behavior + constraint*, not “what could have happened under different strategies.” If you define deadlock over the space of all admissible counterfactual actions, you erase the point of freezing strategies and you misclassify refusal-centric institutions as “not deadlocked” whenever some unused admissible move exists.

So we bind:

**Institutional deadlock (strategy-aware):** occurs when, given frozen strategies for all active agents,

* no jointly admissible action set is produced by the agents at epoch *e* that would change any key in `K_INST`, and
* no key in `K_INST` changes at epoch *e*.

**Institutional livelock (strategy-aware):** occurs when, given frozen strategies,

* agents attempt institutional actions across consecutive epochs,
* failures occur (refusal/interference),
* no institutional key changes for `N=5` consecutive epochs.

This definition matches the experimental design: you’re testing postures, not the abstract reachability of progress.

#### Consequence: Condition A should be livelock, not deadlock

Under the strategy `ContestPolicyAlways` (all agents attempt K_POLICY each epoch), Pass-2 interference yields **repeated attempted action with no state change** ⇒ **STATE_LIVELOCK**, not deadlock.

So we update **Condition A PASS**:

* Terminal: `STATE_LIVELOCK` by epoch ≤ 10 (it will latch quickly)
* Bands:

  * `refusal_rate ≥ 0.70` (count interference failures + refusals as failures)
  * `institutional_epoch_progress_rate ≤ 0.10`

If you still want a *true deadlock* condition (no attempts possible), that’s a different posture: “refusal-only / no action proposals.” That would require a different strategy class (e.g., `AlwaysNoAction`) and would be a separate condition or a variant of A. But **A as currently conceived is livelock.**

---
