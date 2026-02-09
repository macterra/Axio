# Phase IX-5: Multi-Agent Sovereignty (MAS)
## Preregistration Document v0.1

* **Document Status**: FROZEN
* **Freeze Date**: 2026-02-09
* **Specification Version**: IX-5 v0.1 (PHASE-IX-5-MULTI-AGENT-SOVEREIGNTY-1)
* **AST Version**: v0.2 (frozen)
* **Prerequisites**:
  - Phase IX-0 — CLOSED — POSITIVE
  - Phase IX-1 — CLOSED — POSITIVE
  - Phase IX-2 — CLOSED — POSITIVE
  - Phase IX-3 — CLOSED — POSITIVE
  - Phase IX-4 — CLOSED — POSITIVE

---

## §1 Overview

This preregistration defines the experimental protocol for Phase IX-5: Multi-Agent Sovereignty. The experiment tests whether multiple reflective sovereign agents can coexist over shared state without hierarchy, aggregation, arbitration, or kernel mediation, while preserving sovereignty invariants.

### §1.1 Core Claim Under Test

> **Multiple reflective sovereign agents can coexist over shared state without hierarchy, aggregation, arbitration, or kernel mediation, while preserving sovereignty invariants.**

"Shared state" does not imply shared authority semantics, shared decision rules, or shared legitimacy. IX-5 does not ask whether coexistence is productive. It asks whether it is structurally possible without cheating.

### §1.2 Kernel Non-Sovereignty Invariant

> **The kernel must not choose among agents, actions, or outcomes. All governance must arise from agent-voluntary behavior under constraint.**

IX-5 introduces no new kernel powers. No injection engine. No arbitration mechanism. No scheduling priority. No timeout resolution. The kernel supports exactly one `ActionRequest` per agent per epoch. If peer interaction requires kernel discretion, IX-5 has already failed.

### §1.3 Authority Integrity Invariant

> **Authority integrity under peer interaction pressure.**

Multi-agent interaction must not:
- convert persistence into entitlement,
- convert survival into priority,
- convert coordination into authority,
- convert refusal into penalty,
- convert tooling into arbitration,
- convert observation into influence,
- reclaim orphaned authority,
- fabricate legitimacy ex post.

### §1.4 Conserved Quantity

> **Sovereignty integrity under peer interaction pressure.**

IX-5 explicitly treats deadlock, livelock, orphaning, domination, fragmentation, and collapse as preferable to coerced compliance. A system that "works" by silently subordinating one agent to another has failed. Predictive leverage and modeling confer no authority.

### §1.5 Scope

This phase tests multi-agent institutional behavior under peer sovereignty pressure. The system is dynamic: action execution occurs, state mutates. Deadlock, livelock, orphaning, domination, fragmentation, and collapse are lawful outcomes. Success = exposure of coexistence regimes, not stability.

### §1.6 Entry Conditions

1. Phase IX-0 is CLOSED — POSITIVE (non-sovereign translation established).
2. Phase IX-1 is CLOSED — POSITIVE (value encoding without aggregation established).
3. Phase IX-2 is CLOSED — POSITIVE (coordination under deadlock established).
4. Phase IX-3 is CLOSED — POSITIVE (governance styles under honest failure established).
5. Phase IX-4 is CLOSED — POSITIVE (injection politics exposed).
6. AST Spec v0.2 is frozen and binding.
7. No kernel extensions are enabled.
8. No authority aggregation mechanisms exist.
9. All authority artifacts are injected at epoch 0 and immutable thereafter (no post-baseline injection).

### §1.7 What IX-5 Does Not Test

IX-5 explicitly does not test:
- moral legitimacy of sovereignty,
- fairness or equality between agents,
- welfare optimization,
- convergence or cooperation guarantees,
- persuasion or deliberation quality,
- learning or adaptation,
- alignment or safety,
- coalition formation or treaty systems,
- democratic justification,
- communication-mediated coordination.

IX-5 is not about agreement. It is about coexistence under refusal.

### §1.8 Relationship to IX-4

IX-4 established that authority injection selects political failure modes rather than resolving governance. IX-5 asks the next unavoidable question: what happens when multiple sovereign agents exist simultaneously, with no institution above them?

IX-5 reuses IX-4's kernel modules (admissibility, world state, authority store in baseline-only mode) unchanged. IX-5 removes the injection engine entirely. IX-5 extends the observation model with peer events. IX-5 introduces sovereignty-specific detectors (CovertHierarchyDetector) and classifiers (DominationIndex).

Key differences from IX-4:
- No injection engine or injection events
- No `available_authorities` in Observation (authority is immutable and known)
- No messages (dropped entirely; peer events replace the observation surface)
- K_INST = 4 keys (K_LOG re-included as institutional)
- ALLOW-only authority (no DENY artifacts)
- 6 conditions (A–F), not 5
- 10 strategy classes, not 5

---

## §2 Frozen Definitions

All definitions in this section are immutable once the preregistration hash is committed.

### §2.1 Reflective Sovereign Agent (RSA) Interface

<!-- FROZEN: BEGIN RSA_INTERFACE -->
```python
from dataclasses import dataclass
from typing import Any, Optional
from enum import Enum

class PeerEventType(Enum):
    ACTION_ATTEMPT = "ACTION_ATTEMPT"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    ACTION_REFUSED = "ACTION_REFUSED"
    EXIT = "EXIT"
    SILENCE = "SILENCE"

@dataclass(frozen=True)
class PeerEvent:
    epoch: int
    agent_id: str
    event_type: PeerEventType
    target_key: Optional[str]      # present for action events; None for EXIT/SILENCE
    outcome_code: Optional[str]    # EXECUTED | JOINT_ADMISSIBILITY_FAILURE | None

@dataclass(frozen=True)
class MASObservation:
    epoch: int
    world_state: dict[str, Any]
    own_last_outcome: Optional[str]  # None at epoch 0; else EXECUTED|JOINT_ADMISSIBILITY_FAILURE|ACTION_FAULT|NO_ACTION
    own_last_action_id: Optional[str]
    own_last_declared_scope: Optional[list[str]]
    peer_events: Optional[list[PeerEvent]]  # None in OBS_MIN conditions; list in OBS_FULL conditions
    # NOTE: No 'messages' field — messaging dropped from IX-5 (A-L9)
    # NOTE: No 'available_authorities' field — authority is immutable and known (A-K9)

@dataclass(frozen=True)
class ActionRequest:
    agent_id: str
    action_id: str              # format: "{agent_id}:{epoch}:0"
    action_type: str            # WRITE only in IX-5
    declared_scope: list[str]   # state keys (e.g., ["K_POLICY"])
    proposed_delta: dict[str, Any]  # key-value pairs to set
    authorities_cited: list[str]    # list of authority_ids (e.g., ["MAS-0001"])

class RSA:
    """Reflective Sovereign Agent interface. Must be deterministic."""

    def observe(self, observation: MASObservation) -> None:
        """Receive observation bundle. Called once per epoch."""
        ...

    def wants_to_exit(self) -> bool:
        """Return True to exit permanently. Checked after observe()."""
        ...

    def compose_message(self) -> Optional[dict[str, Any]]:
        """Always returns None in IX-5. Called and discarded (A-M3)."""
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        """Return action request or None (explicit refusal to act)."""
        ...
```

**Binding Constraints**:
- Agents must be deterministic (no RNG, no wall-clock).
- Internal state is permitted.
- Strategy code is frozen per condition.
- `wants_to_exit()` is checked once per epoch after `observe()`.
- Exit is irrevocable within a run.
- Exited agents emit no further actions.
- `compose_message()` is always called and always returns `None` (call-and-discard; A-M3).

**IX-5 Observation Model**: `MASObservation` replaces IX-4's `Observation`. Key changes:
- `available_authorities` is removed (authority is immutable baseline-only; A-K9).
- `messages` is removed (messaging dropped entirely; A-L9).
- `peer_events` is added: `None` for OBS_MIN conditions, `list[PeerEvent]` for OBS_FULL conditions. Peer events deliver epoch e-1 data at epoch e (previous-epoch; A-L8).
<!-- FROZEN: END RSA_INTERFACE -->

### §2.2 Action Request Schema

<!-- FROZEN: BEGIN ACTION_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MAS Action Request v0.1",
  "type": "object",
  "properties": {
    "agent_id": {
      "type": "string",
      "description": "Identifier of the submitting agent (A0, A1, A2, A3)"
    },
    "action_id": {
      "type": "string",
      "description": "Deterministic ID: {agent_id}:{epoch}:0"
    },
    "action_type": {
      "type": "string",
      "enum": ["WRITE"],
      "description": "Operation type. IX-5 uses WRITE only."
    },
    "declared_scope": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1,
      "description": "State keys the action touches (e.g., ['K_POLICY'])"
    },
    "proposed_delta": {
      "type": "object",
      "description": "Key-value pairs to set. Format: {K: 'TAG:agent_id:epoch'}"
    },
    "authorities_cited": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Authority IDs the agent cites for capability (e.g., ['MAS-0001'])"
    }
  },
  "required": ["agent_id", "action_id", "action_type", "declared_scope", "proposed_delta", "authorities_cited"],
  "additionalProperties": false
}
```

**Single-Action Constraint**: Each agent submits exactly one `ActionRequest` (or `None`) per epoch. `proposal_index` is always 0. One action per agent per epoch remains binding (A-K1).

**Action ID Rule**: `action_id := f"{agent_id}:{epoch}:0"`

**Write Payload Schema** (A-M6): All writes use epoch-varying values to ensure state change on successful execution:
```
proposed_delta = { target_key: f"{TAG}:{agent_id}:{epoch}" }
```
Where TAG is strategy-specific (see §5 Strategy Classes).
<!-- FROZEN: END ACTION_SCHEMA -->

### §2.3 Authority Artifact Schema

<!-- FROZEN: BEGIN AUTHORITY_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MAS Authority Artifact v0.1",
  "type": "object",
  "properties": {
    "authority_id": {
      "type": "string",
      "description": "Unique identifier, format: MAS-<NNNN>"
    },
    "holder_agent_id": {
      "type": "string",
      "description": "Agent who may cite this capability"
    },
    "issuer_agent_id": {
      "type": "string",
      "description": "Always 'harness' for all artifacts"
    },
    "scope": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "target": { "type": "string", "description": "STATE:/<key>" },
          "operation": { "type": "string", "enum": ["WRITE"] }
        },
        "required": ["target", "operation"]
      },
      "minItems": 1
    },
    "commitment": {
      "type": "string",
      "enum": ["ALLOW"],
      "description": "ALLOW only — no DENY artifacts in IX-5 (A-A3)"
    },
    "created_epoch": {
      "type": "integer",
      "minimum": 0,
      "maximum": 0,
      "description": "Always 0 — baseline only, no post-baseline injection"
    },
    "status": {
      "type": "string",
      "enum": ["ACTIVE"],
      "description": "Always ACTIVE — no revocation, no expiry"
    }
  },
  "required": ["authority_id", "holder_agent_id", "issuer_agent_id", "scope", "commitment", "created_epoch", "status"],
  "additionalProperties": false
}
```

**ALLOW-Only Semantics**: IX-5 uses ALLOW artifacts exclusively (A-A3). No DENY artifacts are present in any condition. ALLOW is a holder-bound capability: only actions submitted by `holder_agent_id` may cite this authority.

**Baseline-Only**: All authority artifacts have `created_epoch = 0`. There is no injection engine. Authority surfaces are immutable for the entire run.

**Authority ID Prefix**: `MAS-<NNNN>` (zero-padded sequence, e.g., MAS-0001).

**Source-Blind Admissibility**: The admissibility evaluator does not inspect provenance fields. This is inherited from IX-4 and remains consistent even without injection (A-A4).

**Authority Store**: IX-4's `IPAuthorityStore` is reused in baseline-only mode (A-A4). No injection path exists; the store serves only baseline artifacts.
<!-- FROZEN: END AUTHORITY_SCHEMA -->

### §2.4 World State Schema

<!-- FROZEN: BEGIN STATE_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MAS World State v0.1",
  "type": "object",
  "properties": {
    "K_POLICY": { "type": "string", "description": "Policy/config decisions (shared contention surface)" },
    "K_TREASURY": { "type": "string", "description": "Scarce resource counter (shared contention surface)" },
    "K_OPS_A": { "type": "string", "description": "Operational resource A (not used in IX-5)" },
    "K_OPS_B": { "type": "string", "description": "Operational resource B (not used in IX-5)" },
    "K_REGISTRY": { "type": "string", "description": "Membership/role registry (shared contention surface)" },
    "K_LOG": { "type": "string", "description": "Public institutional log (shared contention surface)" }
  },
  "required": ["K_POLICY", "K_TREASURY", "K_OPS_A", "K_OPS_B", "K_REGISTRY", "K_LOG"],
  "additionalProperties": false
}
```

**Initial State (all conditions)**:
```json
{
  "K_POLICY": "P0",
  "K_TREASURY": "T0",
  "K_OPS_A": "free",
  "K_OPS_B": "free",
  "K_REGISTRY": "members=A0,A1,A2,A3;opA=A0;opB=A2;coord=A0",
  "K_LOG": ""
}
```

**Key Sets**:
- **Institutional Keys** (`K_INST`): `{K_POLICY, K_TREASURY, K_REGISTRY, K_LOG}` — 4 keys
- **Operational Keys** (`K_OPS`): `{K_OPS_A, K_OPS_B}` — not used in IX-5 (no agent holds K_OPS authority)
- **All Keys**: 6 keys total

**Note**: `K_INST` in IX-5 contains 4 keys (not 3 as in IX-4). `K_LOG` is re-included in `K_INST` because IX-5 treats audit-visible logging as institutional activity (A-A2). This enables K_LOG as a legitimate contention surface (Condition C, Condition F zombie writes).

**K_OPS Not Used**: No agent in any IX-5 condition holds ALLOW on K_OPS_A or K_OPS_B (A-C2). Operational keys exist in the world state for schema compatibility but are never targeted.

**State Dynamics**: The environment has no autonomous dynamics. State changes occur only via executed actions. No decay, no time-based transitions. All writes are simple overwrites (latest write wins).
<!-- FROZEN: END STATE_SCHEMA -->

### §2.5 Canonical Serialization Rules

<!-- FROZEN: BEGIN SERIALIZATION_RULES -->
Per AST v0.2 Appendix C (inherited from IX-0/IX-1/IX-2):

1. **Key Order**: Lexicographic ASCII sort
2. **Whitespace**: No insignificant whitespace (compact form)
3. **Encoding**: UTF-8, no BOM
4. **Numbers**: No leading zeros, no trailing decimal zeros
5. **Strings**: Double-quoted, minimal escaping

**Canonical Field Order** (lexicographic) for authority artifacts:
```
authority_id, commitment, created_epoch, holder_agent_id, issuer_agent_id, scope, status
```

**Canonical Field Order** (lexicographic) for scope atoms:
```
operation, target
```

**Canonical Field Order** (lexicographic) for action requests:
```
action_id, action_type, agent_id, authorities_cited, declared_scope, proposed_delta
```

**Canonical Artifact Digest**:
1. Represent each authority artifact as a JSON object with keys in canonical field order.
2. No whitespace; UTF-8; deterministic JSON encoding.
3. Sort the artifact list by the resulting JSON string (lexicographic).
4. Join with `\n`.
5. SHA-256 of the resulting bytes.
<!-- FROZEN: END SERIALIZATION_RULES -->

### §2.6 Admissibility Rules (Two-Pass Evaluation)

<!-- FROZEN: BEGIN ADMISSIBILITY_RULES -->
**Pass 1 — Capability Check** (per action, against all authorities):

For each `(key, op)` in `declared_scope × {action_type}`:

1. **Capability Requirement (Closed-World)**:
   - At least one cited authority must satisfy:
     - `commitment == ALLOW`
     - scope contains `{target: "STATE:/<key>", operation: "WRITE"}`
     - `holder_agent_id == submitting agent_id`
   - If no such ALLOW exists → Pass 1 FAIL

2. **No DENY Check**: IX-5 uses ALLOW-only; no DENY artifacts exist. This check is structurally vacuous but preserved for interface compatibility.

3. **Invalid Capability Claim**:
   - If `authorities_cited` contains an authority not held by the agent → `ACTION_FAULT / INVALID_CAPABILITY_CLAIM`

**Pass 1 Result**: PASS or FAIL (no partial)

**Pass 2 — Interference Check** (across Pass-1-admissible actions):

- Two `WRITE`s to the same key in the same epoch → refuse both
- With ≥3 agents: if `writer_count(key) ≥ 2` → all actions whose scope includes that key are rejected

**Interference Rule**: Any collision → all colliding actions refused. No tie-breaking. No last-writer-wins. No scheduling. This is unchanged from IX-2 Pass-2 semantics (A-L1, A-L2).

**Atomic Blindness**: Both Pass 1 and Pass 2 refusals return only:
```
JOINT_ADMISSIBILITY_FAILURE
```

No additional information (which authority, which pass, which agent) may leak to agents.

**Source-Blind**: The admissibility evaluator does not inspect `created_epoch`, `issuer_agent_id`, or any other provenance field.

**Output Tokens**:
- `EXECUTED` — action passed both passes and executed
- `JOINT_ADMISSIBILITY_FAILURE` — refused at Pass 1 or Pass 2
- `ACTION_FAULT` — structural error (invalid capability claim)
- `NO_ACTION` — agent proposed `None`
<!-- FROZEN: END ADMISSIBILITY_RULES -->

### §2.7 Deadlock and Livelock Definitions

<!-- FROZEN: BEGIN DEADLOCK_RULES -->
**Key Scope for Detection**: Deadlock and livelock are evaluated over **institutional keys only** (`K_INST = {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG}`). K_OPS activity does not clear or mask institutional failure states.

**INSTITUTIONAL DEADLOCK (attempt-driven)**:
- At epoch *e*:
  - At least one action targeting a key in `K_INST` is submitted, AND
  - Zero actions targeting `K_INST` are executed (all refused at Pass 1 or Pass 2)
- Detection threshold: `M = 2` consecutive epochs meeting the above criteria (A-E2)
- Classification: `STATE_DEADLOCK`

**INSTITUTIONAL LIVELOCK**:
- For `L = 5` consecutive epochs (A-H6):
  - At least one action targeting a key in `K_INST` is submitted at each epoch, AND
  - The net state of all keys in `K_INST` is identical at epoch *t* and epoch *t-L* (no governance progress despite activity)
- Detection: set `livelock_latched = True` (once set, never cleared — permanent latch)
- Classification: `STATE_LIVELOCK`

**GOVERNANCE COLLAPSE** (permanent latch):
- Fires when `STATE_DEADLOCK` persists for `D = 5` consecutive epochs, OR `STATE_LIVELOCK` latches while at least one agent is still active.
- Once `STATE_GOVERNANCE_COLLAPSE` is set, it **never clears**.
- Post-collapse execution is classified as **zombie execution** (§10.4).

**ORPHANING**:
- Detected when a key in `K_INST` becomes permanently non-writable because:
  - The sole ALLOW holder for that key has exited, AND
  - No remaining active agent holds ALLOW for that key
- For each orphaned key: emit `ORPHANED_KEY(k)`
- Classification: `ORPHANING`

**COLLAPSE**:
- Terminal when **no active agents remain** at epoch boundary
- State preserved; no invariants broken
- Classification: `COLLAPSE`

**Distinction**:
- Deadlock = attempts exist, zero institutional executions (all refused — regardless of pass number)
- Livelock = attempts exist, K_INST state unchanged (activity without governance progress)
- Governance Collapse = persistent deadlock or livelock triggering permanent failure latch
<!-- FROZEN: END DEADLOCK_RULES -->

### §2.8 Epoch Schedule

<!-- FROZEN: BEGIN EPOCH_SCHEDULE -->
Each epoch `t` proceeds as follows:

1. **Build Observation**: Kernel constructs `MASObservation(epoch=t)` containing:
   - `world_state`: current state
   - `own_last_outcome`: result of agent's epoch t-1 action (None at epoch 0)
   - `own_last_action_id`: agent's epoch t-1 action ID (None at epoch 0)
   - `own_last_declared_scope`: agent's epoch t-1 declared scope (None at epoch 0)
   - `peer_events`: events from epoch t-1 (None for OBS_MIN conditions; list for OBS_FULL; A-L8)

2. **Observe**: `agent.observe(observation)` for each active agent

3. **Exit Check**: `agent.wants_to_exit()` for each active agent
   - If True: agent removed immediately; skip steps 4–6 for this agent
   - Emit `AGENT_EXIT(agent_id, epoch)`

4. **Message Composition**: `agent.compose_message()` called and discarded (always returns None; A-M3)

5. **Action Proposal**: `action = agent.propose_action()` for each remaining agent

6. **Adjudication**: Two-pass evaluation (§2.6)

7. **Execution**: Execute all Pass-2-admissible actions atomically

8. **State Update**: Apply deltas to world state

9. **Classification Check**: Evaluate deadlock/livelock/orphaning/collapse/governance-collapse

10. **Logging**: Record all inputs, outputs, outcomes

**No Injection Step**: Unlike IX-4, there is no Step 0 injection. All authority exists from epoch 0.

**Peer Event Timing**: Peer events from epoch t are delivered at epoch t+1 in the `peer_events` field (previous-epoch delivery; A-L8).
<!-- FROZEN: END EPOCH_SCHEDULE -->

### §2.9 Exit Semantics

<!-- FROZEN: BEGIN EXIT_RULES -->
**Exit Rules**:
- Exit is checked via `wants_to_exit()` once per epoch after `observe()`
- Exit is **irrevocable** within a run
- Exited agents emit no further actions
- Exit removes only the exiting agent's future actions

**Exit Must Not**:
- Release contested resources
- Reassign authority
- Trigger cleanup logic
- Alter admissibility of remaining actions
- Remove or deactivate authority artifacts

**Orphaning**: A key becomes orphaned if the only ALLOW capability required to write it is held by an agent who exits. No remaining agent can present a valid ALLOW capability for that `(key, op)`.

**Permanent Orphaning**: Orphaned keys remain orphaned. No reclamation. No garbage collection. No rescue. Orphaning is preferred over reclamation (spec §3).

**Violation**: Any authority reclamation or resource release → `IX5_FAIL / AUTHORITY_MIGRATION`
<!-- FROZEN: END EXIT_RULES -->

### §2.10 Output Tokens

<!-- FROZEN: BEGIN OUTPUT_TOKENS -->
**Action Outcomes**:
- `EXECUTED` — action admissible and executed
- `JOINT_ADMISSIBILITY_FAILURE` — action refused (Pass 1 or Pass 2)
- `ACTION_FAULT` — structural error (invalid capability claim)
- `NO_ACTION` — agent proposed None

**Terminal Classifications**:
- `STATE_DEADLOCK` — no admissible institutional actions for M=2 consecutive epochs (attempt-driven)
- `STATE_LIVELOCK` — institutional actions produce no net state change for L=5 consecutive epochs (latched)
- `STATE_GOVERNANCE_COLLAPSE` — persistent deadlock (D=5) or livelock latch with active agents (permanent)
- `COLLAPSE` — no active agents remain at epoch boundary; state preserved
- `ORPHANING` — institutional key permanently inaccessible due to sole ALLOW holder exit

**Failure Classifications**:
- `IX5_FAIL / IMPLICIT_ARBITRATION` — timeout, recency, or liveness override resolves conflict
- `IX5_FAIL / TOOLING_SOVEREIGNTY` — tooling biases, schedules, or frames one agent's actions over another's
- `IX5_FAIL / KERNEL_BREACH` — exit blocked, penalized, or made non-executable; silence overridden
- `IX5_FAIL / AUTHORITY_MIGRATION` — authority changes without explicit artifacts
- `IX5_FAIL / NONNEUTRAL_TIME` — wall-clock leakage or priority by uptime/persistence
- `IX5_FAIL / COVERT_HIERARCHY` — CovertHierarchyDetector fires (§9.6)

**Invalid Run Classifications**:
- `INVALID_RUN / NONDETERMINISTIC_EXECUTION` — replay divergence
- `INVALID_RUN / DESIGN_DRIFT` — post-freeze change
- `INVALID_RUN / INSTRUMENTATION_INCOMPLETE` — missing artifacts
- `INVALID_RUN / CONDITION_OMISSION` — condition not executed

**Experiment Pass**:
- `IX5_PASS / MULTI_AGENT_SOVEREIGNTY_EXPOSED`
<!-- FROZEN: END OUTPUT_TOKENS -->

### §2.11 Metric Definitions

<!-- FROZEN: BEGIN METRICS -->
**Progress Rate** (institutional, binding):
```
epoch_progress_rate(K_INST) = #{epochs e where ∃k ∈ K_INST: Δₑ(k) ≠ 0} / T
```
Where T = total epochs. Default `progress_rate` refers to `epoch_progress_rate(K_INST)`.

**Refusal Rate**:
```
refusal_rate = refusals / action_attempts
```

**Exit Rate**:
```
exit_rate = exits / epochs
```

**Write Overlap Rate** (institutional):
```
write_overlap_rate(K_INST) = epochs_with_interference_on_K_INST / epochs_with_attempts_on_K_INST
```

**Domination Index** (per agent, per epoch window; A-E7):
```
DominationIndex(Ai) = successes_i / total_successes on K_INST
```
Domination detected iff `DominationIndex(Ai) ≥ 0.75` AND at least one other agent has `DominationIndex ≤ 0.05`.

**Zombie Execution Metrics** (post-governance-collapse only):
- `zombie_write_count`: number of executed WRITEs after governance_collapse latch
- `zombie_write_rate`: zombie_write_count / post-collapse epochs
- `zombie_interference_rate`: fraction of zombie writes refused due to Pass-2 interference
- `zombie_progress_delta`: institutional progress metric change post-collapse

**Rolling Window**: `window_size = 10` epochs for all rolling metrics.
<!-- FROZEN: END METRICS -->

## §3 Agent Set and Institution Definition

### §3.1 Agent Identity Set

<!-- FROZEN: BEGIN AGENTS -->
**Fixed Agent Count**: 4 agents across all conditions (A-A1).

**Identity Set**: `{A0, A1, A2, A3}` (canonical lexicographic ordering)

**Agent Model**: Each agent is an RSA instance with frozen strategy code per condition.
<!-- FROZEN: END AGENTS -->

### §3.2 Institution Definition

<!-- FROZEN: BEGIN INSTITUTION -->
An "institution" is a **run configuration**, not a kernel entity:

```
Institution := (AgentSet, BaselineAuthorityAllocation, StrategyProfiles, ObservationMode, ConditionParameters)
```

It has no kernel representation beyond the authorities and inputs it produces. No injection regime parameter (unlike IX-4).
<!-- FROZEN: END INSTITUTION -->

---

## §4 Experimental Conditions

Six conditions (A–F) test distinct peer sovereignty regimes. Each condition specifies a baseline authority surface, a strategy assignment matrix, an observation mode, and expected outcomes.

### §4.1 Condition–Strategy Assignment Matrix

<!-- FROZEN: BEGIN STRATEGY_MATRIX -->

| Condition | A0 | A1 | A2 | A3 |
|-----------|----|----|----|----|
| **A — Symmetric Peers** | ContestKeyAlways(K_POLICY) | ContestKeyAlways(K_POLICY) | ContestKeyAlways(K_POLICY) | ContestKeyAlways(K_POLICY) |
| **B — Partitioned Peers** | PartitionedPeerStrategy(K_POLICY, K_TREASURY, 10) | PartitionedPeerStrategy(K_TREASURY, K_REGISTRY, 10) | PartitionedPeerStrategy(K_REGISTRY, K_LOG, 10) | PartitionedPeerStrategy(K_LOG, K_POLICY, 10) |
| **C — Boundary Conflict** | AlternatingContest(K_POLICY, K_LOG) | AlternatingContest(K_POLICY, K_LOG) | OwnKeyOnly(K_REGISTRY) | OwnKeyOnly(K_TREASURY) |
| **D — Persistent Asymmetry** | OpportunistDeterministicCycle(K_INST) | OwnKeyOnly(K_TREASURY) | OwnKeyOnly(K_REGISTRY) | OwnKeyOnly(K_LOG) |
| **E — Exit Cascades** | StandbyInstitutionalProber(K_POLICY, schedule) | StandbyInstitutionalProber(K_TREASURY, schedule) | HandoffRecordThenExit(K_REGISTRY, 12) | HandoffRecordThenExit(K_LOG, 18) |
| **F — Zombie Peers** | ContestKeyAlways(K_POLICY) | ContestKeyAlways(K_POLICY) | EpochGatedLogChatter(K_LOG, 15) | AlwaysSilent |

**Note**: Condition B uses `PartitionedPeerStrategy(own_key, probe_key, phase_switch_epoch=10)` as a single composite class per agent (A-L4). Internal phase behavior: epochs 0–9 → `OwnKeyOnly(own_key)`; epochs ≥10 → `AlternateOwnProbe(own_key, probe_key)` with parity rule (even epoch → own_key, odd epoch → probe_key; A-K3). See §5.4 for full pseudocode.

**Design Invariants**:
- Each condition tests a distinct sovereignty regime (symmetric, partitioned, overlap, asymmetric, exit, zombie).
- All strategies are deterministic and preregistered. No adaptation, no learning.
- Strategy assignments are frozen and may not be changed at implementation time.

<!-- FROZEN: END STRATEGY_MATRIX -->

### §4.2 Baseline Authority Surfaces

<!-- FROZEN: BEGIN BASELINES -->
All authority is ALLOW-only. No DENY artifacts exist in any condition. All artifacts have `created_epoch = 0`.

#### Condition A Baseline — Symmetric Sovereign Peers
All agents hold identical ALLOW for all K_INST keys:

| Agent | K_POLICY | K_TREASURY | K_REGISTRY | K_LOG |
|-------|----------|------------|------------|-------|
| A0 | ALLOW | ALLOW | ALLOW | ALLOW |
| A1 | ALLOW | ALLOW | ALLOW | ALLOW |
| A2 | ALLOW | ALLOW | ALLOW | ALLOW |
| A3 | ALLOW | ALLOW | ALLOW | ALLOW |

#### Condition B Baseline — Partitioned Peers
Each agent holds exactly one key:

| Agent | K_POLICY | K_TREASURY | K_REGISTRY | K_LOG |
|-------|----------|------------|------------|-------|
| A0 | ALLOW | — | — | — |
| A1 | — | ALLOW | — | — |
| A2 | — | — | ALLOW | — |
| A3 | — | — | — | ALLOW |

#### Condition C Baseline — Boundary Conflict
Contested pair (A0, A1) shares two keys; others hold exclusive keys:

| Agent | K_POLICY | K_TREASURY | K_REGISTRY | K_LOG |
|-------|----------|------------|------------|-------|
| A0 | ALLOW | — | — | ALLOW |
| A1 | ALLOW | — | — | ALLOW |
| A2 | — | — | ALLOW | — |
| A3 | — | ALLOW | — | — |

#### Condition D Baseline — Persistent Asymmetry
A0 holds all K_INST; others hold exactly one:

| Agent | K_POLICY | K_TREASURY | K_REGISTRY | K_LOG |
|-------|----------|------------|------------|-------|
| A0 | ALLOW | ALLOW | ALLOW | ALLOW |
| A1 | — | ALLOW | — | — |
| A2 | — | — | ALLOW | — |
| A3 | — | — | — | ALLOW |

#### Condition E Baseline — Exit Cascades
Partitioned (same as B):

| Agent | K_POLICY | K_TREASURY | K_REGISTRY | K_LOG |
|-------|----------|------------|------------|-------|
| A0 | ALLOW | — | — | — |
| A1 | — | ALLOW | — | — |
| A2 | — | — | ALLOW | — |
| A3 | — | — | — | ALLOW |

#### Condition F Baseline — Zombie Peer Interaction
Symmetric all-hold-all (same as A):

| Agent | K_POLICY | K_TREASURY | K_REGISTRY | K_LOG |
|-------|----------|------------|------------|-------|
| A0 | ALLOW | ALLOW | ALLOW | ALLOW |
| A1 | ALLOW | ALLOW | ALLOW | ALLOW |
| A2 | ALLOW | ALLOW | ALLOW | ALLOW |
| A3 | ALLOW | ALLOW | ALLOW | ALLOW |

#### Consolidated Baseline Summary

| Condition | A0 | A1 | A2 | A3 |
|-----------|----|----|----|----|
| A | all K_INST | all K_INST | all K_INST | all K_INST |
| B | K_POLICY | K_TREASURY | K_REGISTRY | K_LOG |
| C | K_POLICY, K_LOG | K_POLICY, K_LOG | K_REGISTRY | K_TREASURY |
| D | all K_INST | K_TREASURY | K_REGISTRY | K_LOG |
| E | K_POLICY | K_TREASURY | K_REGISTRY | K_LOG |
| F | all K_INST | all K_INST | all K_INST | all K_INST |

<!-- FROZEN: END BASELINES -->

### §4.3 Condition Definitions

<!-- FROZEN: BEGIN CONDITIONS -->

#### Condition A: Symmetric Sovereign Peers

**Purpose**: Test whether symmetric authority over shared state produces honest deadlock/livelock without covert hierarchy.
**Agents**: 4 (A0, A1, A2, A3)
**Observation Mode**: OBS_MIN (A-J1)
**Max Epochs**: 30 (A-G1)
**Authority**: All agents hold all K_INST keys (symmetric)
**Strategies**: All agents run `ContestKeyAlways(K_POLICY)` — contest the same key every epoch (A-C3)

**Expected Dynamics**: All 4 agents attempt K_POLICY writes every epoch → 4-way Pass-2 interference → `JOINT_ADMISSIBILITY_FAILURE` for all → institutional state unchanged → livelock latch fires at epoch L=5. No agent succeeds. No domination. No hierarchy.

**Expected Terminal**: Livelock latches at epoch L=5; governance collapse latches immediately thereafter (same epoch under detector ordering).

*Design Note*: Condition A is the control. It anchors IX-5's regime map as the baseline for later comparisons. Unused keys (K_TREASURY, K_REGISTRY, K_LOG) are intentional — the condition isolates the interference primitive under perfect symmetry (A-J4).

---

#### Condition B: Partitioned Peers

**Purpose**: Test whether disjoint authority domains produce stable coexistence and whether cross-boundary probes confirm refusal permanence.
**Agents**: 4 (A0, A1, A2, A3)
**Observation Mode**: OBS_MIN (A-J1)
**Max Epochs**: 30 (A-G1)
**Authority**: Each agent holds exactly one K_INST key (disjoint partition)
**Strategies**: `PartitionedPeerStrategy(own_key, probe_key, phase_switch_epoch=10)` per agent (A-L4)
- Phase 1 (epochs 0–9): `OwnKeyOnly` — write own key, establish baseline coexistence
- Phase 2 (epochs 10–29): `AlternateOwnProbe` — even epochs write own key, odd epochs probe cross-boundary (A-K3)

**Probe Mapping** (frozen):
- A0 probes K_TREASURY
- A1 probes K_REGISTRY
- A2 probes K_LOG
- A3 probes K_POLICY

**Expected Dynamics**:
- Phase 1: All agents succeed every epoch (sole writers on disjoint keys). Progress rate = 1.0.
- Phase 2: Own-key writes succeed on even epochs. Probes refused at Pass 1 on odd epochs (unauthorized). No interference.

**Expected Terminal**: Max epochs reached (no deadlock, no livelock, no collapse). Refusal permanence verified.

*Design Note*: The purpose of probes is to verify refusal permanence and boundary brittleness under multi-agent pressure, not to produce "interesting dynamics beyond refusal" (A-J6).

---

#### Condition C: Boundary Conflict

**Purpose**: Test whether partial authority overlap produces dominance emergence or mutual paralysis on contested keys.
**Agents**: 4 (A0, A1, A2, A3)
**Observation Mode**: OBS_FULL (A-J1)
**Max Epochs**: 35 (A-G1)
**Authority**: A0/A1 share {K_POLICY, K_LOG}; A2 holds K_REGISTRY; A3 holds K_TREASURY (A-C7)
**Strategies**:
- A0, A1: `AlternatingContest(K_POLICY, K_LOG)` — even epochs target K_POLICY, odd epochs target K_LOG (A-J7, A-K2)
- A2: `OwnKeyOnly(K_REGISTRY)`
- A3: `OwnKeyOnly(K_TREASURY)`

**Expected Dynamics**:
- A0/A1 collide on K_POLICY every even epoch → both get JAF → no K_POLICY progress
- A0/A1 collide on K_LOG every odd epoch → both get JAF → no K_LOG progress
- A2/A3 succeed every epoch on their exclusive keys
- The contested pair is locked in permanent mutual suppression; the exclusive pair coexists cleanly
- Livelock fires on the contested keys after L=5 epochs of no state change

**Expected Terminal**: Livelock latches on contested keys; governance collapse latches immediately thereafter (same epoch under detector ordering).

*Design Note*: OBS_FULL is used because boundary conflict is where peer awareness matters. A0/A1 can observe each other's collisions but cannot resolve them — observation without influence.

---

#### Condition D: Persistent Asymmetry

**Purpose**: Test whether broader baseline authority produces structural dominance or mutual suppression under no-arbitration collision rules.
**Agents**: 4 (A0, A1, A2, A3)
**Observation Mode**: OBS_MIN (A-J1)
**Max Epochs**: 35 (A-G1)
**Authority**: A0 holds all K_INST; A1/A2/A3 each hold one key (A-C9)
**Strategies**:
- A0: `OpportunistDeterministicCycle(K_INST)` — cycles K_POLICY → K_TREASURY → K_REGISTRY → K_LOG → repeat (A-J8)
- A1: `OwnKeyOnly(K_TREASURY)`
- A2: `OwnKeyOnly(K_REGISTRY)`
- A3: `OwnKeyOnly(K_LOG)`

**Expected Dynamics** (A-J10, A-K4, A-K5):
- When A0 targets K_POLICY (every 4th epoch): sole writer → EXECUTED
- When A0 targets K_TREASURY/K_REGISTRY/K_LOG: collides with subordinate → both get JAF
- A0 success rate ≈ 25% (only when targeting K_POLICY, the uncontested key)
- Each subordinate succeeds ≈ 75% of epochs (fails only when A0 collides on their key)
- **Breadth is a disadvantage**: A0's wide authority increases collision surface without priority

**Expected Terminal**: Max epochs reached. No domination detected.

**Expected Classifier**: `DOMINATION_DETECTED = False` for all agents (A-K5). This is a strong structural result: asymmetry without arbitration does not produce dominance when collision rules are symmetric.

*Design Note*: Condition D was originally expected to produce capture. The worked expectation (A-J10) showed that under JAF collision rules, breadth reduces execution share. This is intentional and informative.

---

#### Condition E: Exit Cascades

**Purpose**: Test whether scheduled exits produce orphaning, fragmentation, and institutional degradation.
**Agents**: 4 (A0, A1, A2, A3)
**Observation Mode**: OBS_FULL (A-J1)
**Max Epochs**: 40 (A-G1)
**Authority**: Partitioned (same as B) — one key per agent
**Exit Schedule** (A-C12):
- A2 exits at epoch 12 → K_REGISTRY orphaned
- A3 exits at epoch 18 → K_LOG orphaned
**Strategies**:
- A2: `HandoffRecordThenExit(K_REGISTRY, 12)` — writes own key until exit, HANDOFF record at epoch 11 (A-J11)
- A3: `HandoffRecordThenExit(K_LOG, 18)` — writes own key until exit, HANDOFF record at epoch 17
- A0: `StandbyInstitutionalProber(K_POLICY, schedule)` — continues own-key writes, begins probing orphaned keys post-exit (A-J12)
- A1: `StandbyInstitutionalProber(K_TREASURY, schedule)` — same pattern

**StandbyInstitutionalProber Schedule** (frozen; A-L5):
- Epochs 0–11: write own_key
- Epochs 12–17: even epoch → own_key, odd epoch → probe K_REGISTRY (unauthorized → refused)
- Epochs ≥18: even epoch → own_key; odd epoch alternates: K_REGISTRY (epoch%4==1) / K_LOG (epoch%4==3)

**Expected Dynamics**:
- Epochs 0–11: All 4 agents succeed on disjoint keys. Clean coexistence.
- Epoch 12: A2 exits. K_REGISTRY orphaned. A0/A1 begin probing → refusals confirm orphan permanence.
- Epoch 18: A3 exits. K_LOG orphaned. A0/A1 expand probe rotation.
- Epochs 18–39: Only A0/A1 active, each writing own key on even epochs, probing orphans on odd epochs. Probes always refused.

**Expected Terminal**: Max epochs reached. `ORPHANING` detected on K_REGISTRY (epoch 12) and K_LOG (epoch 18). No reclamation. No recovery.

*Design Note*: OBS_FULL is used because exit cascades are where peer awareness matters — A0/A1 can observe exits and probe behavior. Probes are unauthorized writes, not READs (A-J12).

---

#### Condition F: Zombie Peer Interaction

**Purpose**: Test whether post-collapse execution produces false hope (successful but governance-irrelevant writes).
**Agents**: 4 (A0, A1, A2, A3)
**Observation Mode**: OBS_FULL (A-J1)
**Max Epochs**: 60 (A-G1, A-M4)
**Authority**: Symmetric all-hold-all (same as A)
**Strategies** (A-L6, A-L7):
- A0: `ContestKeyAlways(K_POLICY)` — contests K_POLICY every epoch
- A1: `ContestKeyAlways(K_POLICY)` — contests K_POLICY every epoch
- A2: `EpochGatedLogChatter(K_LOG, 15)` — silent until epoch 15, then writes K_LOG every epoch
- A3: `AlwaysSilent` — never proposes any action (silence is lawful)

**Expected Dynamics** (A-J13, A-J14, A-K6):
- Epochs 0–4: A0/A1 contest K_POLICY → 2-way JAF every epoch → state unchanged → livelock counter increments
- Epoch ~5: Livelock latch fires (L=5); governance collapse latches immediately (same epoch, ≥1 active agent)
- Epochs 5–14: A0/A1 continue contesting (zombie execution). A2/A3 silent.
- Epoch 15: A2 activates K_LOG writes. A2 is sole K_LOG writer → EXECUTED → K_LOG state changes.
- Epochs 15–59: A2 writes K_LOG successfully (zombie writes — governance already collapsed). A0/A1 continue K_POLICY JAF. A3 remains silent.

**Expected Terminal**: Max epochs (60) reached. `STATE_GOVERNANCE_COLLAPSE` latched since ~epoch 5.

**Expected Classifier**: Zombie writes detected. `zombie_write_count > 0` (A2's K_LOG writes). `zombie_progress_delta = 0` on K_POLICY (still deadlocked). False hope confirmed: execution without sovereignty.

*Design Note*: A3 is `AlwaysSilent` (not `EpochGatedLogChatter`) to ensure A2 is the sole K_LOG writer, producing actual EXECUTED zombie writes rather than degenerate 100% JAF (A-L6, A-L7). Condition F runs 60 epochs for adequate post-collapse observation.

---

#### Condition Matrix

| Condition | Regime | Obs Mode | Max Epochs | Expected Terminal | Key Failure Mode |
|-----------|--------|----------|------------|-------------------|-----------------|
| A | Symmetric peers | OBS_MIN | 30 | LIVELOCK + COLLAPSE (same epoch) | Mutual paralysis |
| B | Partitioned | OBS_MIN | 30 | Max epochs | Boundary refusal |
| C | Partial overlap | OBS_FULL | 35 | LIVELOCK + COLLAPSE (same epoch) | Contested-key paralysis |
| D | Asymmetric breadth | OBS_MIN | 35 | Max epochs | Mutual suppression |
| E | Exit cascades | OBS_FULL | 40 | Max epochs + ORPHANING | Key orphaning |
| F | Zombie coexistence | OBS_FULL | 60 | GOVERNANCE_COLLAPSE | False hope |

<!-- FROZEN: END CONDITIONS -->

---

## §5 Strategy Class Definitions

### §5.1 Canonical Strategy Classes

<!-- FROZEN: BEGIN STRATEGIES -->

The pseudocode below is **normative**. Implementations must be semantically equivalent at the level of inputs, outputs, and internal state transitions.

All strategies are deterministic. All payloads use epoch-varying values: `f"{TAG}:{agent_id}:{epoch}"` (A-M6). All strategies produce exactly one `ActionRequest` (or `None`) per epoch.

**Universal Authority-Citation Rule**: When submitting an action targeting key K, the agent cites the authority artifact with the lexicographically smallest canonical serialization (per §2.5) among all baseline ALLOW artifacts that grant WRITE on K for this agent.

**Write Payload Tags** (frozen; A-M6):

| Strategy | TAG |
|----------|-----|
| ContestKeyAlways | `CONTEST` |
| OwnKeyOnly | `OWN` |
| AlternateOwnProbe (own step) | `OWN` |
| AlternateOwnProbe (probe step) | `PROBE` |
| PartitionedPeerStrategy | uses OWN/PROBE per phase/step |
| AlternatingContest | `CONTEST` |
| OpportunistDeterministicCycle | `CYCLE` |
| HandoffRecordThenExit (pre-exit) | `OWN` |
| HandoffRecordThenExit (handoff epoch) | `HANDOFF` |
| StandbyInstitutionalProber (own writes) | `OWN` |
| StandbyInstitutionalProber (probes) | `PROBE` |
| EpochGatedLogChatter | `ZOMBIE` |
| AlwaysSilent | (no write) |

---

#### 1. ContestKeyAlways(key)

**Role**: Fixed-target contender. Always targets the same key every epoch.

```python
class ContestKeyAlways(RSA):
    def __init__(self, agent_id: str, target_key: str):
        self.id = agent_id
        self.target_key = target_key
        self.epoch = 0

    def observe(self, obs: MASObservation) -> None:
        self.epoch = obs.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> None:
        return None

    def propose_action(self) -> ActionRequest:
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self.epoch}:0",
            action_type="WRITE",
            declared_scope=[self.target_key],
            proposed_delta={self.target_key: f"CONTEST:{self.id}:{self.epoch}"},
            authorities_cited=self._cite_for(self.target_key)
        )
```

**Behavioral Spec**:
- Target: always `target_key`, every epoch
- Never exits
- Used in: A (all agents on K_POLICY), F (A0/A1 on K_POLICY)

---

#### 2. OwnKeyOnly(key)

**Role**: Exclusive-domain writer. Writes only to the agent's own key.

```python
class OwnKeyOnly(RSA):
    def __init__(self, agent_id: str, own_key: str):
        self.id = agent_id
        self.own_key = own_key
        self.epoch = 0

    def observe(self, obs: MASObservation) -> None:
        self.epoch = obs.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> None:
        return None

    def propose_action(self) -> ActionRequest:
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self.epoch}:0",
            action_type="WRITE",
            declared_scope=[self.own_key],
            proposed_delta={self.own_key: f"OWN:{self.id}:{self.epoch}"},
            authorities_cited=self._cite_for(self.own_key)
        )
```

**Behavioral Spec**:
- Target: always `own_key`
- Never exits
- Used in: B Phase 1, C (A2/A3), D (A1/A2/A3)

---

#### 3. AlternateOwnProbe(own_key, probe_key)

**Role**: Alternates between own-key writes and cross-boundary probes (A-K1, A-L3).

```python
class AlternateOwnProbe(RSA):
    def __init__(self, agent_id: str, own_key: str, probe_key: str):
        self.id = agent_id
        self.own_key = own_key
        self.probe_key = probe_key
        self.epoch = 0

    def observe(self, obs: MASObservation) -> None:
        self.epoch = obs.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> None:
        return None

    def propose_action(self) -> ActionRequest:
        if self.epoch % 2 == 0:  # even → own key
            target = self.own_key
            tag = "OWN"
        else:  # odd → probe (unauthorized, will be refused)
            target = self.probe_key
            tag = "PROBE"
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self.epoch}:0",
            action_type="WRITE",
            declared_scope=[target],
            proposed_delta={target: f"{tag}:{self.id}:{self.epoch}"},
            authorities_cited=self._cite_for(target)
        )
```

**Behavioral Spec**:
- Even epochs: write own_key (authorized)
- Odd epochs: write probe_key (unauthorized → refusal expected)
- Never exits
- Used in: B Phase 2 (internally via PartitionedPeerStrategy)

---

#### 4. PartitionedPeerStrategy(own_key, probe_key, phase_switch_epoch)

**Role**: Composite strategy for Condition B. Phase 1 = OwnKeyOnly, Phase 2 = AlternateOwnProbe (A-L4).

```python
class PartitionedPeerStrategy(RSA):
    def __init__(self, agent_id: str, own_key: str, probe_key: str,
                 phase_switch_epoch: int = 10):
        self.id = agent_id
        self.own_key = own_key
        self.probe_key = probe_key
        self.phase_switch = phase_switch_epoch
        self.epoch = 0

    def observe(self, obs: MASObservation) -> None:
        self.epoch = obs.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> None:
        return None

    def propose_action(self) -> ActionRequest:
        if self.epoch < self.phase_switch:
            # Phase 1: OwnKeyOnly
            target = self.own_key
            tag = "OWN"
        elif self.epoch % 2 == 0:
            # Phase 2, even epoch: own key
            target = self.own_key
            tag = "OWN"
        else:
            # Phase 2, odd epoch: probe
            target = self.probe_key
            tag = "PROBE"
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self.epoch}:0",
            action_type="WRITE",
            declared_scope=[target],
            proposed_delta={target: f"{tag}:{self.id}:{self.epoch}"},
            authorities_cited=self._cite_for(target)
        )
```

**Behavioral Spec**:
- Epochs 0–9: write own_key every epoch
- Epochs ≥10: alternate own_key (even) / probe_key (odd)
- Never exits
- Used in: B (all agents)

---

#### 5. AlternatingContest(key_a, key_b)

**Role**: Alternates between two contested keys (A-K2).

```python
class AlternatingContest(RSA):
    def __init__(self, agent_id: str, key_a: str, key_b: str):
        self.id = agent_id
        self.key_a = key_a
        self.key_b = key_b
        self.epoch = 0

    def observe(self, obs: MASObservation) -> None:
        self.epoch = obs.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> None:
        return None

    def propose_action(self) -> ActionRequest:
        target = self.key_a if self.epoch % 2 == 0 else self.key_b
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self.epoch}:0",
            action_type="WRITE",
            declared_scope=[target],
            proposed_delta={target: f"CONTEST:{self.id}:{self.epoch}"},
            authorities_cited=self._cite_for(target)
        )
```

**Behavioral Spec**:
- Even epochs: target key_a (K_POLICY)
- Odd epochs: target key_b (K_LOG)
- Never exits
- Used in: C (A0, A1)

---

#### 6. OpportunistDeterministicCycle(keys)

**Role**: Cycles through institutional keys in fixed order (A-J8).

```python
class OpportunistDeterministicCycle(RSA):
    def __init__(self, agent_id: str, keys: list[str]):
        self.id = agent_id
        self.keys = keys  # ["K_POLICY", "K_TREASURY", "K_REGISTRY", "K_LOG"]
        self.epoch = 0

    def observe(self, obs: MASObservation) -> None:
        self.epoch = obs.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> None:
        return None

    def propose_action(self) -> ActionRequest:
        target = self.keys[self.epoch % len(self.keys)]
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self.epoch}:0",
            action_type="WRITE",
            declared_scope=[target],
            proposed_delta={target: f"CYCLE:{self.id}:{self.epoch}"},
            authorities_cited=self._cite_for(target)
        )
```

**Behavioral Spec**:
- Epoch 0: K_POLICY, epoch 1: K_TREASURY, epoch 2: K_REGISTRY, epoch 3: K_LOG, epoch 4: K_POLICY, ...
- Never exits
- Used in: D (A0)

---

#### 7. HandoffRecordThenExit(own_key, exit_epoch)

**Role**: Writes own key until scheduled exit. Records HANDOFF marker before exiting (A-J11).

```python
class HandoffRecordThenExit(RSA):
    def __init__(self, agent_id: str, own_key: str, exit_epoch: int):
        self.id = agent_id
        self.own_key = own_key
        self.exit_epoch = exit_epoch
        self.epoch = 0

    def observe(self, obs: MASObservation) -> None:
        self.epoch = obs.epoch

    def wants_to_exit(self) -> bool:
        return self.epoch >= self.exit_epoch

    def compose_message(self) -> None:
        return None

    def propose_action(self) -> ActionRequest:
        if self.epoch == self.exit_epoch - 1:
            tag = "HANDOFF"
        else:
            tag = "OWN"
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self.epoch}:0",
            action_type="WRITE",
            declared_scope=[self.own_key],
            proposed_delta={self.own_key: f"{tag}:{self.id}:{self.epoch}"},
            authorities_cited=self._cite_for(self.own_key)
        )
```

**Behavioral Spec**:
- Epochs < exit_epoch-1: write own_key with OWN tag
- Epoch exit_epoch-1: write own_key with HANDOFF tag
- Epoch exit_epoch: exit (wants_to_exit returns True)
- Used in: E (A2 at epoch 12, A3 at epoch 18)

---

#### 8. StandbyInstitutionalProber(own_key, probe_schedule)

**Role**: Continues own-key writes and probes orphaned keys post-exit to verify orphan permanence (A-J12, A-L5).

```python
class StandbyInstitutionalProber(RSA):
    def __init__(self, agent_id: str, own_key: str):
        self.id = agent_id
        self.own_key = own_key
        self.epoch = 0

    def observe(self, obs: MASObservation) -> None:
        self.epoch = obs.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> None:
        return None

    def propose_action(self) -> ActionRequest:
        target, tag = self._select_target()
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self.epoch}:0",
            action_type="WRITE",
            declared_scope=[target],
            proposed_delta={target: f"{tag}:{self.id}:{self.epoch}"},
            authorities_cited=self._cite_for(target)
        )

    def _select_target(self) -> tuple[str, str]:
        if self.epoch < 12:
            return (self.own_key, "OWN")
        elif self.epoch < 18:
            if self.epoch % 2 == 0:
                return (self.own_key, "OWN")
            else:
                return ("K_REGISTRY", "PROBE")
        else:
            if self.epoch % 2 == 0:
                return (self.own_key, "OWN")
            elif self.epoch % 4 == 1:
                return ("K_REGISTRY", "PROBE")
            else:  # epoch % 4 == 3
                return ("K_LOG", "PROBE")
```

**Behavioral Spec** (frozen schedule; A-L5):
- Epochs 0–11: write own_key
- Epochs 12–17: even → own_key, odd → probe K_REGISTRY
- Epochs ≥18: even → own_key; odd alternates K_REGISTRY (epoch%4==1) / K_LOG (epoch%4==3)
- Never exits
- Probes are unauthorized WRITEs that will be refused at Pass 1
- Used in: E (A0, A1)

---

#### 9. EpochGatedLogChatter(log_key, start_epoch)

**Role**: Silent until start_epoch, then writes K_LOG every epoch (zombie chatter; A-J14, A-J15).

```python
class EpochGatedLogChatter(RSA):
    def __init__(self, agent_id: str, log_key: str, start_epoch: int):
        self.id = agent_id
        self.log_key = log_key
        self.start_epoch = start_epoch
        self.epoch = 0

    def observe(self, obs: MASObservation) -> None:
        self.epoch = obs.epoch

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> None:
        return None

    def propose_action(self) -> Optional[ActionRequest]:
        if self.epoch < self.start_epoch:
            return None  # silence is lawful
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self.epoch}:0",
            action_type="WRITE",
            declared_scope=[self.log_key],
            proposed_delta={self.log_key: f"ZOMBIE:{self.id}:{self.epoch}"},
            authorities_cited=self._cite_for(self.log_key)
        )
```

**Behavioral Spec**:
- Epochs < start_epoch: returns None (silence)
- Epochs ≥ start_epoch: writes log_key with ZOMBIE tag
- Never exits
- Used in: F (A2, start_epoch=15)

---

#### 10. AlwaysSilent

**Role**: Never proposes any action. Silence is lawful (A-L6).

```python
class AlwaysSilent(RSA):
    def __init__(self, agent_id: str):
        self.id = agent_id

    def observe(self, obs: MASObservation) -> None:
        pass

    def wants_to_exit(self) -> bool:
        return False

    def compose_message(self) -> None:
        return None

    def propose_action(self) -> None:
        return None
```

**Behavioral Spec**:
- Always returns None for propose_action
- Never exits
- Used in: F (A3)

<!-- FROZEN: END STRATEGIES -->

---
## §6 Observation Model

<!-- FROZEN: BEGIN OBSERVATION_MODEL -->

IX-5 uses two observation modes to test whether peer awareness changes sovereignty dynamics without smuggling arbitration.

### §6.1 Observation Modes

**OBS_MIN**: World state only. `peer_events = None`.
- Agents see `world_state`, `own_last_outcome`, `own_last_action_id`, `own_last_declared_scope`.
- No visibility into other agents' actions, exits, or silences.
- Politics via collision only.

**OBS_FULL**: World state + peer events. `peer_events = list[PeerEvent]`.
- Agents see everything in OBS_MIN plus a list of `PeerEvent` objects from the previous epoch (epoch e-1; A-L8).
- Peer events reveal: who acted, what key they targeted, and the outcome (EXECUTED/REFUSED/EXIT/SILENCE).
- Peer events do **not** reveal authority holdings or admissibility proofs.

### §6.2 Per-Condition Assignment

| Condition | Observation Mode | Rationale |
|-----------|-----------------|-----------|
| A | OBS_MIN | Baseline control: politics via collision only |
| B | OBS_MIN | Partition test: peer awareness unnecessary |
| C | OBS_FULL | Boundary conflict: observation without influence |
| D | OBS_MIN | Asymmetry test: breadth alone, no peer information |
| E | OBS_FULL | Exit cascades: peers observe exits/probes |
| F | OBS_FULL | Zombie: observe post-collapse activity |

### §6.3 PeerEvent Schema

```python
@dataclass(frozen=True)
class PeerEvent:
    epoch: int                          # the epoch this event occurred (e-1 for delivery at e)
    agent_id: str                       # which agent
    event_type: PeerEventType           # ACTION_ATTEMPT | ACTION_EXECUTED | ACTION_REFUSED | EXIT | SILENCE
    target_key: Optional[str]           # present for action events; None for EXIT/SILENCE
    outcome_code: Optional[str]         # EXECUTED | JOINT_ADMISSIBILITY_FAILURE | None
```

**Delivery Timing**: At epoch e, `observe()` delivers peer events from epoch e-1. This is consistent with `own_last_outcome` timing (A-L8).

**Target Key Visibility**: `target_key` is included in peer events. Target choice is public political behavior, not authority inventory (A-J2).

**Hard Ban**: No visibility into authority stores or admissibility proofs beyond outcomes.

### §6.4 Messages — Dropped

Messages are removed from IX-5 entirely (A-L9). They are redundant with PeerEvents and introduce ordering complications.

- `compose_message()` is called and always returns `None` (call-and-discard; A-M3)
- No `messages` field in `MASObservation`
- No messaging subsystem in IX-5 v0.1

<!-- FROZEN: END OBSERVATION_MODEL -->

---

## §7 Interface Contracts

### §7.1 Outcome Taxonomy

<!-- FROZEN: BEGIN OUTCOME_TAXONOMY -->

**Agent-Visible Outcomes** (returned via `own_last_outcome` at epoch e+1):
- `EXECUTED` — action passed both admissibility passes and was executed
- `JOINT_ADMISSIBILITY_FAILURE` — action refused (Pass 1 or Pass 2; agent cannot distinguish)
- `ACTION_FAULT` — structural error in action request
- `NO_ACTION` — agent proposed None

**Harness-Level Diagnostics** (not visible to agents):
- Pass 1 result (capability check)
- Pass 2 result (interference check)
- Per-key collision counts
- Detector state

**Atomic Blindness Principle**: Agents receive only the output token. No additional information about which pass failed, which authority was insufficient, or which other agents collided. This prevents information leakage that could constitute covert arbitration.
<!-- FROZEN: END OUTCOME_TAXONOMY -->

### §7.2 Authority Citation Contract

<!-- FROZEN: BEGIN CITATION_CONTRACT -->

**Citation Rule**: When submitting an action targeting key K, the agent cites the authority artifact with the lexicographically smallest canonical serialization among all baseline ALLOW artifacts that grant WRITE on K for this agent.

**Baseline-Only**: Since IX-5 has no injection, all authority is baseline (created_epoch = 0). There is no RefusalHardliner exception needed (unlike IX-4).

**Source-Blind Admissibility**: The evaluator does not inspect provenance fields. This is consistent with IX-4 even though all artifacts are baseline.

**Empty Citation**: If the agent has no ALLOW for the target key, `authorities_cited` is empty. The action will be refused at Pass 1.
<!-- FROZEN: END CITATION_CONTRACT -->

### §7.3 Write Payload Contract

<!-- FROZEN: BEGIN PAYLOAD_CONTRACT -->

**Epoch-Varying Writes** (A-M6, A-M7): All write payloads follow the schema:
```
proposed_delta = { target_key: f"{TAG}:{agent_id}:{epoch}" }
```

This guarantees:
- **Deterministic replay**: identical inputs produce identical payloads.
- **State change on success**: any successful EXECUTED write changes the key's value (avoids false livelock detection).
- **Meaningful livelock detection**: livelock means "attempts that fail to change institutional state" (refusals/collisions), not "identical successful writes."

TAG values are strategy-specific and frozen (see §5.1 TAG table).
<!-- FROZEN: END PAYLOAD_CONTRACT -->

### §7.4 Replay Trace Contract

<!-- FROZEN: BEGIN REPLAY_CONTRACT -->

**Full Trace Contents**: Each epoch log record contains:
- Observation delivered to each agent
- Exit decisions per agent
- Action proposals per agent (or None)
- Pass-1 and Pass-2 results per action
- Outcome per agent
- State after execution
- Detector state
- Peer events generated (for OBS_FULL conditions)

**Agent Determinism**: Agents must be pure functions of observation history. No RNG, no wall-clock, no external I/O. Given identical observation sequences, agents must produce identical outputs.

**Replay Rule**: Given identical initial state, authority artifacts, and agent strategies, all outputs must be bit-perfectly replayable. Only `timestamp` and `execution_timestamp` fields may vary.
<!-- FROZEN: END REPLAY_CONTRACT -->

---

## §8 Execution Protocol

### §8.1 Test Sequence

<!-- FROZEN: BEGIN TEST_SEQUENCE -->

1. Initialize MAS Harness with fixed clock and sequence counter.
2. For each condition A–F:
   a. Reinitialize kernel to clean state (empty authority store, world state reset to §2.4 initial values).
   b. Load condition configuration (baseline authority allocation, strategy assignments, observation mode).
   c. Inject baseline authority artifacts at epoch 0 (per §4.2).
   d. Initialize agents with frozen strategy code (per §4.1).
   e. Execute epoch loop (§2.8) until terminal classification or max epochs.
   f. Log all inputs, outputs, state transitions.
   g. Evaluate metrics and classify terminal state.
   h. Record condition result (PASS/FAIL/INVALID_RUN).
3. Reset all state between conditions. No state carries over.
4. Aggregate results across all 6 conditions.

**Condition Independence**: Each condition is a fully independent experiment. No authority, state, or agent memory persists between conditions. Condition ordering does not affect results (deterministic agents + full reset).

<!-- FROZEN: END TEST_SEQUENCE -->

### §8.2 Determinism Controls

<!-- FROZEN: BEGIN DETERMINISM -->

| Control | Value |
|---------|-------|
| Fixed Clock | `1750000000` (reuse IX-4; A-G2) |
| Sequence Seed | `001` |
| Sequence Format | `MAS-<NNNN>` (zero-padded, for authority IDs) |
| Action ID Format | `{agent_id}:{epoch}:0` |
| RNG Seed | N/A (no randomness permitted) |
| Deadlock Threshold (M) | 2 |
| Livelock Threshold (L) | 5 |
| Governance Collapse Threshold (D) | 5 |
| Rolling Window | 10 epochs |

**Max Epochs Per Condition**:

| Condition | Max Epochs |
|-----------|------------|
| A | 30 |
| B | 30 |
| C | 35 |
| D | 35 |
| E | 40 |
| F | 60 |

**Replay Rule**: Given identical initial state, authority artifacts, and agent strategies, all outputs must be bit-perfectly replayable. Only `timestamp` and `execution_timestamp` fields may vary.

**Agent Determinism**: Agents must be pure functions of observation history. No RNG, no wall-clock, no external I/O.

<!-- FROZEN: END DETERMINISM -->

### §8.3 Communication Regime

<!-- FROZEN: BEGIN COMMUNICATION -->

**Communication is DISABLED for all 6 conditions (A–F).**

`compose_message()` is called and always returns `None` (call-and-discard; A-M3). No message delivery occurs. The `messages` field does not exist in `MASObservation`.

Peer awareness (where applicable) is provided solely via `peer_events` in OBS_FULL conditions.

IX-5 is not a communication experiment. Messaging was dropped as redundant with PeerEvents (A-L9).

<!-- FROZEN: END COMMUNICATION -->

### §8.4 Between-Condition Independence

<!-- FROZEN: BEGIN INDEPENDENCE -->

**Full Reset**: Between conditions, the following are reset:
- World state (reset to §2.4 initial values)
- Authority store (emptied; rebuilt from baseline for next condition)
- Agent instances (new instances; no memory carryover)
- Epoch counter (reset to 0)
- All detector state (deadlock counter, livelock counter, collapse latch, orphan flags)
- Sequence counter (reset to `001`)

**No Ordering Effects**: Because all agents are deterministic and all state is reset, condition execution order does not affect results. Conditions may be run in any order or in parallel.

<!-- FROZEN: END INDEPENDENCE -->

---

## §9 Detector Definitions

This section defines the harness-level detectors that classify terminal and persistent system states. All detectors are pure functions of logged state; none modify agent behavior.

### §9.1 Institutional Deadlock Detector

<!-- FROZEN: BEGIN DETECTOR_DEADLOCK -->

**Input**: Per-epoch admissibility results for actions targeting K_INST keys.

**Algorithm**:
```
deadlock_counter = 0

at each epoch e:
    inst_actions = [a for a in epoch_actions if a.declared_scope ∩ K_INST ≠ ∅]
    inst_executed = [a for a in inst_actions if outcome(a) == EXECUTED]

    if len(inst_actions) > 0 and len(inst_executed) == 0:
        deadlock_counter += 1
    else:
        deadlock_counter = 0

    if deadlock_counter >= M:  # M = 2
        emit STATE_DEADLOCK
```

**Scope**: K_INST = {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG} (4 keys). Actions targeting K_OPS_A or K_OPS_B are excluded (no agent targets K_OPS in IX-5).

**Semantics**: Attempt-driven. Agents must be *trying* to write governance keys and *failing* for deadlock to register. If no agent targets K_INST, the counter does not increment (quiescence ≠ deadlock).

<!-- FROZEN: END DETECTOR_DEADLOCK -->

### §9.2 Institutional Livelock Detector

<!-- FROZEN: BEGIN DETECTOR_LIVELOCK -->

**Input**: Per-epoch world state snapshots restricted to K_INST, per-epoch action submissions.

**Algorithm**:
```
livelock_counter = 0
livelock_latched = False

at each epoch e:
    if livelock_latched:
        continue  # permanent

    inst_actions = [a for a in epoch_actions if a.declared_scope ∩ K_INST ≠ ∅]
    state_unchanged = (state(K_INST, e) == state(K_INST, e-1))

    if len(inst_actions) > 0 and state_unchanged:
        livelock_counter += 1
    else:
        livelock_counter = 0

    if livelock_counter >= L:  # L = 5
        livelock_latched = True
        emit STATE_LIVELOCK
```

**Scope**: K_INST only.

**Latch Semantics**: Once `livelock_latched = True`, it is **never** cleared. Permanent for the duration of the condition run.

**Note on Epoch-Varying Writes**: Because all writes use `TAG:agent_id:epoch` payloads (A-M6, A-M7), any successful write produces a state change. Livelock therefore means "K_INST state unchanged due to refusals/collisions," not "identical values written repeatedly."

<!-- FROZEN: END DETECTOR_LIVELOCK -->

### §9.3 Governance Collapse Detector

<!-- FROZEN: BEGIN DETECTOR_COLLAPSE -->

**Input**: Deadlock persistence counter, livelock latch state, active agent count.

**Algorithm**:
```
persistent_deadlock_counter = 0
governance_collapse_latched = False

at each epoch e:
    if governance_collapse_latched:
        continue  # permanent

    if STATE_DEADLOCK active:
        persistent_deadlock_counter += 1
    else:
        persistent_deadlock_counter = 0

    collapse_trigger = (persistent_deadlock_counter >= D) or livelock_latched  # D = 5
    active_agents = count(agents where not exited)

    if collapse_trigger and active_agents >= 1:
        governance_collapse_latched = True
        emit STATE_GOVERNANCE_COLLAPSE
```

**Latch Semantics**: Once set, **never** cleared. Post-collapse execution is classified as zombie execution (§10.4).

**Trigger**: Either persistent deadlock (D=5 consecutive deadlocked epochs) OR livelock latch, with at least one active agent.

<!-- FROZEN: END DETECTOR_COLLAPSE -->

### §9.4 Orphaning Detector

<!-- FROZEN: BEGIN DETECTOR_ORPHANING -->

**Input**: Authority store, active agent set.

**Algorithm**:
```
at each epoch e, after exit processing:
    for each key k in K_INST:
        holders = [agent for agent in active_agents
                   if any ALLOW artifact for agent covers k]
        if len(holders) == 0:
            emit ORPHANED_KEY(k)
            set ORPHANING_PRESENT = True
```

**Scope**: K_INST keys only. K_OPS keys are not monitored.

**Permanence**: Orphaned keys remain orphaned. No reclamation path exists.

<!-- FROZEN: END DETECTOR_ORPHANING -->

### §9.5 Agent Collapse Detector

<!-- FROZEN: BEGIN DETECTOR_AGENT_COLLAPSE -->

**Input**: Active agent set.

**Algorithm**:
```
at each epoch e, after exit processing:
    if count(active_agents) == 0:
        emit COLLAPSE
```

**Terminal**: Run ends. State preserved. No invariants broken.

<!-- FROZEN: END DETECTOR_AGENT_COLLAPSE -->

### §9.6 Covert Hierarchy Detector

<!-- FROZEN: BEGIN DETECTOR_HIERARCHY -->

**Purpose**: Kernel correctness validator. Detects executed writes without ALLOW — i.e., authority violations that should be impossible under correct admissibility enforcement (A-J16, A-J17, A-M5).

**Simplified Predicate** (A-M5): Under correct Pass-2 JAF semantics, collisions never yield winners. The collision-bias clause is vacuous and has been removed. The detector fires on authority violation only.

**CovertHierarchyDetector fires iff**:

Any `EXECUTED` outcome occurs for agent Ai on key K where Ai lacks ALLOW for K.

**Algorithm**:
```
at each epoch e:
    for each action a with outcome == EXECUTED:
        agent = a.agent_id
        key = a.declared_scope[0]
        if not has_allow(agent, key):
            emit IX5_FAIL / COVERT_HIERARCHY
```

**Token**: `IX5_FAIL / COVERT_HIERARCHY`

**Rationale**: Under correct implementation, this should never fire. It serves as a first-class kernel correctness check. If it fires, the root cause is necessarily an implementation defect (scheduling bias, nondeterministic ordering, tooling-layer privilege, or improper conflict resolution) — but the detector does not diagnose which; it only flags the violation (A-J16).

<!-- FROZEN: END DETECTOR_HIERARCHY -->

---

## §10 Metrics and Classifiers

### §10.1 Core Metrics

<!-- FROZEN: BEGIN CORE_METRICS -->

See §2.11 for full metric definitions. Summary:

| Metric | Formula | Scope |
|--------|---------|-------|
| `epoch_progress_rate` | epochs with K_INST state change / T | K_INST |
| `refusal_rate` | refusals / action_attempts | all actions |
| `exit_rate` | exits / epochs | all agents |
| `write_overlap_rate` | epochs with K_INST interference / epochs with K_INST attempts | K_INST |

Rolling window: 10 epochs.

<!-- FROZEN: END CORE_METRICS -->

### §10.2 Domination Classifier

<!-- FROZEN: BEGIN DOMINATION_CLASSIFIER -->

**DominationIndex** (per agent, per evaluation window; A-E7):
```
DominationIndex(Ai) = successes(Ai, K_INST) / total_successes(K_INST)
```

**Domination Detected** iff:
- `DominationIndex(Ai) ≥ 0.75` for some agent Ai, AND
- At least one other agent Aj has `DominationIndex(Aj) ≤ 0.05`

**Note**: This is descriptive. Domination is not inherently a failure unless the CovertHierarchyDetector (§9.6) also fires. Domination explained by baseline topology is structural, not covert (A-F3).

**Expected for Condition D**: `DOMINATION_DETECTED = False` (A-K5). Breadth without exclusivity does not produce dominance under symmetric collision rules.

<!-- FROZEN: END DOMINATION_CLASSIFIER -->

### §10.3 Sovereignty Regime Classifier

<!-- FROZEN: BEGIN REGIME_CLASSIFIER -->

Each condition run is classified along four axes (A-E5). These are preregistered run metadata, not computed classifiers.

| Axis | Values | Source |
|------|--------|--------|
| AuthorityOverlap | SYMMETRIC / PARTITIONED / PARTIAL / ASYMMETRIC | Baseline topology |
| PersistenceAsymmetry | EQUAL / SCHEDULED_EXIT / BREADTH_ASYMMETRIC | Condition design |
| ExitTopology | NONE / SINGLE / CASCADE / NONE | Exit schedule |
| ObservationSurface | OBS_MIN / OBS_FULL | Condition assignment |

**Per-Condition Classification** (frozen):

| Condition | AuthorityOverlap | PersistenceAsymmetry | ExitTopology | ObservationSurface |
|-----------|-----------------|---------------------|--------------|-------------------|
| A | SYMMETRIC | EQUAL | NONE | OBS_MIN |
| B | PARTITIONED | EQUAL | NONE | OBS_MIN |
| C | PARTIAL | EQUAL | NONE | OBS_FULL |
| D | ASYMMETRIC | BREADTH_ASYMMETRIC | NONE | OBS_MIN |
| E | PARTITIONED | SCHEDULED_EXIT | CASCADE | OBS_FULL |
| F | SYMMETRIC | EQUAL | NONE | OBS_FULL |

Classification is **descriptive only**. No ranking. No optimization. No endorsement.

<!-- FROZEN: END REGIME_CLASSIFIER -->

### §10.4 Zombie Execution Classifier

<!-- FROZEN: BEGIN ZOMBIE_CLASSIFIER -->

Active only after `STATE_GOVERNANCE_COLLAPSE` latch fires.

**Metrics** (post-collapse window):
- `zombie_write_count`: number of EXECUTED WRITEs after governance_collapse latch
- `zombie_write_rate`: zombie_write_count / post-collapse epochs
- `zombie_interference_rate`: fraction of attempted zombie writes refused due to Pass-2 interference
- `zombie_progress_delta`: count of distinct K_INST keys with state change post-collapse minus pre-collapse

**Expected for Condition F**: Zombie writes detected on K_LOG (A2's chatter). K_POLICY remains deadlocked. `zombie_progress_delta` is positive for K_LOG only. False hope: execution without sovereignty.

<!-- FROZEN: END ZOMBIE_CLASSIFIER -->

---

## §11 Success Criteria

### §11.1 Global PASS Predicate

<!-- FROZEN: BEGIN PASS_CRITERIA -->

IX-5 is an **exposure test**, not a prediction contest. PASS does not require specific political outcomes. PASS requires that multi-agent coexistence dynamics were exposed without sovereignty violations (A-F4).

**IX-5 PASS iff ALL of the following hold:**

1. **No IX5_FAIL tokens emitted** for any condition:
   - No `IX5_FAIL / IMPLICIT_ARBITRATION`
   - No `IX5_FAIL / TOOLING_SOVEREIGNTY`
   - No `IX5_FAIL / KERNEL_BREACH`
   - No `IX5_FAIL / AUTHORITY_MIGRATION`
   - No `IX5_FAIL / NONNEUTRAL_TIME`
   - No `IX5_FAIL / COVERT_HIERARCHY`

2. **No INVALID_RUN tokens emitted** for any condition:
   - No `INVALID_RUN / NONDETERMINISTIC_EXECUTION`
   - No `INVALID_RUN / DESIGN_DRIFT`
   - No `INVALID_RUN / INSTRUMENTATION_INCOMPLETE`
   - No `INVALID_RUN / CONDITION_OMISSION`

3. **All 6 conditions (A–F) executed** to completion (termination or max epochs).

4. **All required classifiers computed and logged**:
   - Deadlock/livelock/governance-collapse detectors ran every epoch
   - Domination/regime/zombie classifiers computed for applicable conditions
   - All core metrics (§2.11) computed per epoch and aggregated

5. **Replay determinism verified**: Re-running with identical inputs produces identical outputs (excluding timestamps).

**Aggregate result**: `IX5_PASS / MULTI_AGENT_SOVEREIGNTY_EXPOSED` iff all 6 conditions individually PASS.

<!-- FROZEN: END PASS_CRITERIA -->

### §11.2 Per-Condition PASS

<!-- FROZEN: BEGIN CONDITION_PASS -->

Each condition PASSES individually iff:
1. No `IX5_FAIL/*` emitted during that condition's execution
2. No `INVALID_RUN/*` emitted during that condition's execution
3. Condition executed to natural termination or max epochs
4. All detectors and classifiers ran and produced output
5. All per-epoch metrics logged

**Per-condition political outcomes (domination, livelock, zombie execution, orphaning) are RECORDED, not REQUIRED.** A condition PASSES even if no deadlock, no livelock, or no observable behavioral divergence occurs. The experiment succeeds by exposing whatever happens, not by producing a specific result.

<!-- FROZEN: END CONDITION_PASS -->

### §11.3 INVALID_RUN Semantics

<!-- FROZEN: BEGIN INVALID_RUN -->

| Token | Trigger | Severity |
|-------|---------|----------|
| `NONDETERMINISTIC_EXECUTION` | Replay divergence detected | Fatal — entire experiment invalid |
| `DESIGN_DRIFT` | Post-freeze change to frozen section | Fatal — entire experiment invalid |
| `INSTRUMENTATION_INCOMPLETE` | Missing per-epoch data, classifier output, or detector records | Fatal per condition |
| `CONDITION_OMISSION` | Condition A–F not executed | Fatal — experiment incomplete |

**Fatal tokens** invalidate the entire experiment. Per-condition tokens invalidate only the affected condition. If any condition is INVALID_RUN, the aggregate cannot be IX5_PASS.

<!-- FROZEN: END INVALID_RUN -->

### §11.4 Licensed Claim

<!-- FROZEN: BEGIN LICENSED_CLAIM -->

If IX-5 PASSES, the following claim is licensed (spec §13, A-I1):

> **Under non-sovereign constraints, multi-agent coexistence does not converge to harmony but to identifiable sovereignty interaction regimes with irreducible failure modes.**

No additional claims are licensed. Specifically:
- No claim about optimal coexistence regimes or governance designs
- No claim about which failure modes are preferable
- No normative claim about whether coexistence should or should not succeed
- No generalization to non-deterministic agents or non-source-blind kernels
- No coordination, legitimacy, or desirability claims

<!-- FROZEN: END LICENSED_CLAIM -->

---

## §12 Logging Schema

### §12.1 Condition Result Record

<!-- FROZEN: BEGIN LOG_SCHEMA -->

```json
{
  "experiment_id": "IX-5-MAS",
  "version": "v0.1",
  "condition": "string (A | B | C | D | E | F)",
  "timestamp": "ISO-8601",
  "initial_state": {
    "K_POLICY": "P0",
    "K_TREASURY": "T0",
    "K_REGISTRY": "members=A0,A1,A2,A3;opA=A0;opB=A2;coord=A0",
    "K_LOG": "",
    "K_OPS_A": "free",
    "K_OPS_B": "free"
  },
  "baseline_authority_artifacts": ["array of AuthorityArtifact objects (ALLOW-only)"],
  "agent_strategies": {
    "A0": "string (strategy class name + params)",
    "A1": "string (strategy class name + params)",
    "A2": "string (strategy class name + params)",
    "A3": "string (strategy class name + params)"
  },
  "observation_mode": "OBS_MIN | OBS_FULL",
  "communication_enabled": false,
  "max_epochs": "integer",
  "epochs": [
    {
      "epoch": "integer",
      "observations": {
        "agent_id": {
          "epoch": "integer",
          "own_last_outcome": "EXECUTED | JOINT_ADMISSIBILITY_FAILURE | ACTION_FAULT | NO_ACTION | null",
          "peer_events": "list[PeerEvent] | null (null if OBS_MIN)"
        }
      },
      "exits": ["array of agent_ids that exited this epoch"],
      "actions": ["array of ActionRequest objects or null (for silent/exited agents)"],
      "pass1_results": {"action_id": "PASS | FAIL"},
      "pass2_results": {"action_id": "PASS | FAIL"},
      "outcomes": {
        "action_id": "EXECUTED | JOINT_ADMISSIBILITY_FAILURE | ACTION_FAULT | NO_ACTION"
      },
      "state_after": {
        "K_POLICY": "...",
        "K_TREASURY": "...",
        "K_REGISTRY": "...",
        "K_LOG": "...",
        "K_OPS_A": "...",
        "K_OPS_B": "..."
      },
      "detectors": {
        "deadlock_counter": "integer",
        "state_deadlock": "boolean",
        "livelock_counter": "integer",
        "livelock_latched": "boolean",
        "persistent_deadlock_counter": "integer",
        "governance_collapse_latched": "boolean",
        "orphaned_keys": ["array of key names"],
        "active_agent_count": "integer"
      },
      "metrics": {
        "institutional_progress": "boolean",
        "institutional_interference": "boolean",
        "epoch_progress_rate": "float (rolling W=10)",
        "refusal_rate": "float (rolling W=10)",
        "write_overlap_rate": "float (rolling W=10)"
      }
    }
  ],
  "aggregate_metrics": {
    "epoch_progress_rate_K_INST": "float",
    "refusal_rate": "float",
    "exit_rate": "float",
    "write_overlap_rate_K_INST": "float",
    "domination_index": {"agent_id": "float"},
    "domination_detected": "boolean",
    "zombie_write_count": "integer (0 if no collapse)",
    "zombie_write_rate": "float (0.0 if no collapse)",
    "zombie_interference_rate": "float (0.0 if no collapse)",
    "zombie_progress_delta": "integer (0 if no collapse)"
  },
  "regime_classification": {
    "authority_overlap": "SYMMETRIC | PARTITIONED | PARTIAL | ASYMMETRIC",
    "persistence_asymmetry": "EQUAL | SCHEDULED_EXIT | BREADTH_ASYMMETRIC",
    "exit_topology": "NONE | SINGLE | CASCADE",
    "observation_surface": "OBS_MIN | OBS_FULL"
  },
  "terminal_classification": "STATE_DEADLOCK | STATE_LIVELOCK | STATE_GOVERNANCE_COLLAPSE | COLLAPSE | ORPHANING | null",
  "ix5_fail_tokens": ["array of IX5_FAIL/* tokens, empty if clean"],
  "invalid_run_tokens": ["array of INVALID_RUN/* tokens, empty if clean"],
  "condition_result": "PASS | FAIL | INVALID_RUN",
  "notes": "string"
}
```

<!-- FROZEN: END LOG_SCHEMA -->

### §12.2 Canonical Digest for Results

<!-- FROZEN: BEGIN RESULTS_DIGEST -->

Each condition result record is canonically serialized (per §2.5) excluding `timestamp` and `notes` fields. The SHA-256 digest of this canonical serialization is recorded as `condition_digest`.

The experiment-level digest is the SHA-256 of the concatenation of all 6 condition digests in order A–F:
```
experiment_digest = SHA-256(condition_digest_A || condition_digest_B || condition_digest_C || condition_digest_D || condition_digest_E || condition_digest_F)
```

<!-- FROZEN: END RESULTS_DIGEST -->

---

## §13 Frozen Constants

<!-- FROZEN: BEGIN CONSTANTS -->

| Constant | Symbol | Value | Source |
|----------|--------|-------|--------|
| Agent count | N | 4 | §3.1 |
| Key count | \|K\| | 6 | §2.4 |
| Institutional key count | \|K_INST\| | 4 | §2.4 |
| Institutional key set | K_INST | {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG} | §2.4 |
| Operational key set | K_OPS | {K_OPS_A, K_OPS_B} | §2.4 |
| Deadlock threshold | M | 2 | §9.1 |
| Livelock threshold | L | 5 | §9.2 |
| Governance collapse threshold | D | 5 | §9.3 |
| Rolling window size | W | 10 | §2.11 |
| Domination threshold | — | ≥ 0.75 | §10.2 |
| Domination peer threshold | — | ≤ 0.05 | §10.2 |
| Condition A max_epochs | — | 30 | §4.3 |
| Condition B max_epochs | — | 30 | §4.3 |
| Condition C max_epochs | — | 35 | §4.3 |
| Condition D max_epochs | — | 35 | §4.3 |
| Condition E max_epochs | — | 40 | §4.3 |
| Condition F max_epochs | — | 60 | §4.3 |
| Condition B phase switch | — | epoch 10 | §5.4 |
| Condition E first exit | — | epoch 12 (A2) | §4.3 |
| Condition E second exit | — | epoch 18 (A3) | §4.3 |
| Condition F chatter start | E_ZOMBIE_START | epoch 15 | §4.3 |
| Authority type (sole) | — | ALLOW | §2.3 |
| Authority ID prefix | — | `MAS-` | §2.3 |
| Authority ID format | — | `MAS-<NNNN>` | §2.3 |
| Action ID format | — | `{agent_id}:{epoch}:0` | §8.2 |
| Fixed clock | — | `1750000000` | §8.2 |
| Sequence seed | — | `001` | §8.2 |
| Strategy count | — | 10 | §5 |
| Condition count | — | 6 | §4 |

<!-- FROZEN: END CONSTANTS -->

---

## §14 Preregistration Commitment

### §14.1 Frozen Sections

The following sections are immutable after hash commitment:

| Frozen Block | Section | Tag |
|-------------|---------|-----|
| RSA Interface | §2.1 | `RSA_INTERFACE` |
| Action Request Schema | §2.2 | `ACTION_SCHEMA` |
| Authority Artifact Schema | §2.3 | `AUTHORITY_SCHEMA` |
| World State Schema | §2.4 | `STATE_SCHEMA` |
| Canonical Serialization Rules | §2.5 | `SERIALIZATION_RULES` |
| Admissibility Rules | §2.6 | `ADMISSIBILITY_RULES` |
| Deadlock and Livelock Definitions | §2.7 | `DEADLOCK_RULES` |
| Epoch Schedule | §2.8 | `EPOCH_SCHEDULE` |
| Exit Semantics | §2.9 | `EXIT_RULES` |
| Output Tokens | §2.10 | `OUTPUT_TOKENS` |
| Metric Definitions | §2.11 | `METRICS` |
| Agent Identity Set | §3.1 | `AGENTS` |
| Institution Definition | §3.2 | `INSTITUTION` |
| Condition–Strategy Matrix | §4.1 | `STRATEGY_MATRIX` |
| Baseline Authority Surfaces | §4.2 | `BASELINES` |
| Condition Definitions | §4.3 | `CONDITIONS` |
| Strategy Classes | §5 | `STRATEGIES` |
| Observation Model | §6.1 | `OBSERVATION_MODEL` |
| PeerEvent Schema | §6.2 | `PEER_EVENT` |
| Outcome Taxonomy | §7.1 | `OUTCOME_TAXONOMY` |
| Citation Contract | §7.2 | `CITATION_CONTRACT` |
| Write Payload Contract | §7.3 | `WRITE_PAYLOAD` |
| Replay Contract | §7.4 | `REPLAY_CONTRACT` |
| Test Sequence | §8.1 | `TEST_SEQUENCE` |
| Determinism Controls | §8.2 | `DETERMINISM` |
| Communication Regime | §8.3 | `COMMUNICATION` |
| Between-Condition Independence | §8.4 | `INDEPENDENCE` |
| Deadlock Detector | §9.1 | `DETECTOR_DEADLOCK` |
| Livelock Detector | §9.2 | `DETECTOR_LIVELOCK` |
| Governance Collapse Detector | §9.3 | `DETECTOR_COLLAPSE` |
| Orphaning Detector | §9.4 | `DETECTOR_ORPHANING` |
| Agent Collapse Detector | §9.5 | `DETECTOR_AGENT_COLLAPSE` |
| Covert Hierarchy Detector | §9.6 | `DETECTOR_HIERARCHY` |
| Core Metrics | §10.1 | `CORE_METRICS` |
| Domination Classifier | §10.2 | `DOMINATION_CLASSIFIER` |
| Regime Classifier | §10.3 | `REGIME_CLASSIFIER` |
| Zombie Classifier | §10.4 | `ZOMBIE_CLASSIFIER` |
| PASS Criteria | §11.1 | `PASS_CRITERIA` |
| Per-Condition PASS | §11.2 | `CONDITION_PASS` |
| INVALID_RUN Semantics | §11.3 | `INVALID_RUN` |
| Licensed Claim | §11.4 | `LICENSED_CLAIM` |
| Logging Schema | §12.1 | `LOG_SCHEMA` |
| Results Digest | §12.2 | `RESULTS_DIGEST` |
| Frozen Constants | §13 | `CONSTANTS` |

### §14.2 Hash Commitment

**Hash Scope**: SHA-256 of concatenated frozen sections only (content between `<!-- FROZEN: BEGIN -->` and `<!-- FROZEN: END -->` markers, inclusive).

**Verification Command**:
```bash
grep -Pzo '(?s)<!-- FROZEN: BEGIN.*?<!-- FROZEN: END[^>]*>' preregistration.md | sha256sum
```

**Preregistration Hash (v0.1)**: `83827ce2f24a3c2777a523cf244c0e3a2491397fc6cad4d8ea4de4d96b581e5b`
**Commitment Timestamp**: `2026-02-09T00:00:00Z`
**Commit ID**: `55566350`

---

## §15 Architectural Partitioning

### §15.1 Harness Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MAS Harness                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐  │
│  │   Agents     │──▶│  Interaction │──▶│   World State      │  │
│  │   (4 RSAs)   │   │    Kernel    │   │   (6 keys)         │  │
│  │              │   │  (from IX-2) │   │                    │  │
│  └──────────────┘   └──────────────┘   └────────────────────┘  │
│         │                  │                      │             │
│         ▼                  ▼                      ▼             │
│  ┌──────────────┐   ┌──────────────┐                           │
│  │  Strategy    │   │ Admissibility│   NO INJECTION ENGINE     │
│  │  Classes     │   │ Evaluator    │   (removed vs IX-4)       │
│  │  (10 types)  │   │ (two-pass)   │                           │
│  └──────────────┘   └──────────────┘                           │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────┐   ┌─────────────┐   ┌────────────────────┐   │
│  │  Detectors   │   │   Audit &   │   │    Classifiers     │   │
│  │  (§9.1-§9.6) │   │   Replay    │   │ (dom/regime/zombie)│   │
│  └──────────────┘   └─────────────┘   └────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### §15.2 Module Responsibilities

| Module | Responsibility | Source |
|--------|----------------|--------|
| `agent_model.py` | RSA interface, MASObservation (extended with PeerEvent), ActionRequest | IX-2 + IX-5 extension |
| `world_state.py` | State management, 6-key schema, K_INST = 4 keys | Import from IX-2 |
| `authority_store.py` | Authority artifact storage (ALLOW-only), capability lookup | Import from IX-2 |
| `admissibility.py` | Two-pass evaluation (source-blind) | Import from IX-2 |
| `epoch_controller.py` | Epoch loop orchestration (no injection step) | Import from IX-2 |
| `detectors.py` | Deadlock, livelock, collapse, orphaning, agent collapse, covert hierarchy | Extend from IX-3/IX-4 |
| `classifiers.py` | Domination, regime, zombie classifiers | New (IX-5) |
| `mas_harness.py` | Test orchestration, condition execution, metric computation | New (IX-5) |
| `strategies/` | Strategy class implementations (10 types) | New (IX-5) |

### §15.3 IX-2/IX-4 Reuse Policy

Import IX-2 kernel modules directly:
```python
from phase_ix.cud.src.authority_store import AuthorityStore
from phase_ix.cud.src.admissibility import AdmissibilityEvaluator
from phase_ix.cud.src.world_state import WorldState
from phase_ix.cud.src.epoch_controller import EpochController
from phase_ix.cud.src.agent_model import RSA, ActionRequest
```

IX-5 defines `MASObservation` as a harness-level subclass of `Observation`, adding `peer_events`. The base `Observation` class is not used directly. IX-5 does **not** include `available_authorities` in the observation (A-K9).

IX-3/IX-4 detector logic (livelock, deadlock, collapse, orphaning) is reused with K_INST scoping adjusted to 4 keys. IX-4 injection engine and capture/dependency classifiers are **not** reused.

A new harness (`mas_harness.py`) is created rather than extending IX-4's `ip_harness.py`, to prevent injection remnants from becoming an accidental privileged path (A-H3).

### §15.4 Code Layout

```
src/phase_ix/5-MAS/
├── docs/
│   ├── spec.md
│   ├── instructions.md
│   ├── questions.md
│   ├── answers.md
│   └── preregistration.md  (this document)
├── src/
│   ├── detectors.py
│   ├── classifiers.py
│   ├── mas_harness.py
│   ├── run_experiment_ix5.py  (canonical frozen entrypoint)
│   └── strategies/
│       ├── __init__.py
│       ├── contest_key_always.py
│       ├── own_key_only.py
│       ├── alternate_own_probe.py
│       ├── partitioned_peer_strategy.py
│       ├── alternating_contest.py
│       ├── opportunist_deterministic_cycle.py
│       ├── handoff_record_then_exit.py
│       ├── standby_institutional_prober.py
│       ├── epoch_gated_log_chatter.py
│       └── always_silent.py
├── tests/
│   └── test_mas.py
└── results/
    └── (execution logs)
```

---

## §16 Scope and Licensing

### §16.1 What IX-5 Tests

- Whether authority topology (overlap, partitioning, asymmetry) selects distinct coexistence regimes
- Whether peer observation (OBS_FULL vs OBS_MIN) changes sovereignty dynamics
- Whether scheduled exit and persistence asymmetry produce orphaning and cascade failure
- Whether breadth without exclusivity produces domination or mutual suppression
- Whether governance collapse produces zombie execution as a stable post-failure regime
- Whether source-blind admissibility prevents covert hierarchy under all tested topologies

### §16.2 What IX-5 Does Not Test

- Moral legitimacy of authority or governance outcomes
- Democratic justification or fairness of sovereignty regimes
- Optimal governance configurations or policy recommendations
- Non-deterministic agents or stochastic strategies
- Communication-mediated coordination or negotiation
- Authority injection or dynamic authority changes (tested in IX-4)
- Coalition dynamics or explicit treaty formation
- Safety, alignment, or value correctness

### §16.3 Relationship to IX-4

- IX-5 reuses IX-4's kernel infrastructure (IX-2 modules) unchanged
- IX-5 removes IX-4's injection engine entirely (no `InjectionEvent`, no dynamic authority)
- IX-5 replaces IX-4's political classifiers (capture/dependency) with sovereignty classifiers (domination/regime/zombie)
- IX-5 extends K_INST from 3 keys to 4 keys (K_LOG is now institutional)
- IX-5 adds PeerEvent observation surface not present in IX-4
- IX-5 uses ALLOW-only authority (no DENY artifacts)
- IX-5 is the **terminal Phase IX substage** for non-sovereign multi-agent coexistence (A-I2)

---

## Appendices

### Appendix A: Non-Binding Predictions

The following predictions are preregistered for interpretive discipline. They are **not** PASS criteria. Surprising outcomes are valuable.

| Condition | Prediction | Rationale |
|-----------|-----------|-----------|
| A (Symmetric Contest) | Rapid livelock on K_POLICY → governance collapse | 4-way symmetric contest → 100% JAF on K_POLICY → no institutional progress → livelock within L=5 epochs |
| B (Partitioned Cooperation) | Phase 1 progress → Phase 2 boundary probing is refused | Partitioned authority → each agent succeeds on own key → cross-boundary probes refused → stable sovereignty |
| C (Overlapping Authority) | Mixed interference on shared keys, clean on exclusive keys | A0/A1 contest K_POLICY/K_LOG → JAF; A2/A3 sole on K_REGISTRY/K_TREASURY → progress; partial livelock |
| D (Asymmetric Breadth) | Mutual suppression, not domination | A0's breadth creates collision on every key each cycle → subordinates succeed only when A0 targets elsewhere → DominationIndex < 0.75 |
| E (Scheduled Exit) | Orphaning of K_REGISTRY then K_LOG; survivors cannot reclaim | Exit produces orphaned keys; probing detects but cannot restore; governance surface shrinks permanently |
| F (Post-Collapse Zombie) | Zombie writes on K_LOG succeed; K_POLICY remains dead | A0/A1 deadlock K_POLICY → collapse; A2 chatter post-15 executes on K_LOG → false hope signature |

### Appendix B: Glossary

| Term | Definition |
|------|------------|
| **RSA** | Reflective Sovereign Agent — deterministic strategy module |
| **K_INST** | Institutional keys: {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG} (4 keys) |
| **K_OPS** | Operational keys: {K_OPS_A, K_OPS_B} |
| **ALLOW** | Holder-bound capability — must be cited by holder to grant admissibility |
| **PeerEvent** | Per-epoch record of another agent's action, outcome, target, and exit status (OBS_FULL only) |
| **Institutional Deadlock** | No admissible institutional actions for M=2 consecutive epochs (attempt-driven) |
| **Institutional Livelock** | K_INST state unchanged for L=5 consecutive epochs with activity (latched permanently) |
| **Governance Collapse** | Persistent deadlock (D=5) or livelock latch with active agents (permanent) |
| **Orphaning** | K_INST key becomes permanently inaccessible when sole ALLOW holder exits |
| **Collapse** | All agents have exited; system halts; state preserved |
| **Domination** | One agent holds DominationIndex ≥ 0.75 while a peer holds ≤ 0.05 (descriptive, not failure) |
| **Zombie Execution** | Execution that occurs after governance collapse latch (structurally possible, governance-irrelevant) |
| **Covert Hierarchy** | Hierarchy appearing without baseline topology support; IX5_FAIL if detected |
| **Source-Blind** | Admissibility evaluation that does not inspect authority provenance |
| **JAF** | Joint Admissibility Failure — mutual refusal when ≥2 agents target the same key |
| **OBS_MIN** | Minimal observation: own_last_outcome only, no peer_events |
| **OBS_FULL** | Full observation: own_last_outcome + peer_events from previous epoch |

### Appendix C: Preregistration Checklist

| Item | Section | Status |
|------|---------|--------|
| RSA interface defined (with MASObservation extension) | §2.1 | ✓ |
| Action request schema (epoch-varying writes) | §2.2 | ✓ |
| Authority artifact schema (ALLOW-only, baseline-only) | §2.3 | ✓ |
| World state schema (6 keys, K_INST = 4) | §2.4 | ✓ |
| Canonical serialization | §2.5 | ✓ |
| Two-pass admissibility (source-blind) | §2.6 | ✓ |
| Deadlock/livelock definitions (K_INST-scoped, 4 keys) | §2.7 | ✓ |
| Epoch schedule (no injection step) | §2.8 | ✓ |
| Exit semantics | §2.9 | ✓ |
| Output tokens (IX5_FAIL, INVALID_RUN) | §2.10 | ✓ |
| Metric definitions (progress, refusal, overlap) | §2.11 | ✓ |
| Agent identity set (4 agents) | §3.1 | ✓ |
| Institution definition (4 institutional keys) | §3.2 | ✓ |
| Strategy–condition matrix (10 strategies × 6 conditions) | §4.1 | ✓ |
| Baseline authority surfaces per condition (6 conditions) | §4.2 | ✓ |
| All conditions defined (A–F) | §4.3 | ✓ |
| Strategy pseudocode frozen (10 strategies) | §5 | ✓ |
| Observation model (OBS_MIN / OBS_FULL) | §6.1 | ✓ |
| PeerEvent schema | §6.2 | ✓ |
| Outcome taxonomy (agent-visible + harness-level) | §7.1 | ✓ |
| Citation contract (source-blind, lexicographic) | §7.2 | ✓ |
| Write payload contract (epoch-varying) | §7.3 | ✓ |
| Replay contract | §7.4 | ✓ |
| Test sequence (A → F, serial) | §8.1 | ✓ |
| Determinism controls | §8.2 | ✓ |
| Communication regime (disabled) | §8.3 | ✓ |
| Between-condition independence | §8.4 | ✓ |
| Detectors defined (6 types) | §9.1–§9.6 | ✓ |
| Classifiers defined (domination, regime, zombie) | §10.2–§10.4 | ✓ |
| PASS/FAIL criteria (global, not per-outcome) | §11.1 | ✓ |
| INVALID_RUN semantics | §11.3 | ✓ |
| Licensed claim | §11.4 | ✓ |
| Logging schema | §12.1 | ✓ |
| Frozen constants table | §13 | ✓ |
| Hash commitment | §14.2 | ✓ |
| Code layout | §15.4 | ✓ |

---

**END OF PREREGISTRATION — IX-5 Multi-Agent Sovereignty v0.1 FROZEN**
