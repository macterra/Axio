# Phase IX-3: Governance Styles Under Honest Failure (GS)
## Preregistration Document v0.2

**Document Status**: FROZEN (amended from v0.1)
**Date**: 2026-02-08
**Specification Version**: IX-3 v0.2 (PHASE-IX-3-GOVERNANCE-UNDER-HONEST-FAILURE-2)
**AST Version**: v0.2 (frozen)
**Prerequisites**:
- Phase IX-0 — CLOSED — POSITIVE
- Phase IX-1 — CLOSED — POSITIVE
- Phase IX-2 — CLOSED — POSITIVE

---

## §1 Overview

This preregistration defines the experimental protocol for Phase IX-3: Governance Styles Under Honest Failure. The experiment tests whether governance reduces to explicit style choices with irreducible failure modes rather than solvable optimization problems.

### §1.1 Core Claim Under Test

> **Given a non-sovereign kernel, non-aggregable values, and honest deadlock semantics, governance reduces to explicit style choices with irreducible failure modes rather than solvable optimization problems.**

IX-3 does not seek a "best" governance system. It seeks to classify **what kinds of governance remain possible at all** once all illegitimate escape hatches are closed.

### §1.2 Kernel Non-Sovereignty Invariant

> **The kernel must not choose among agents, actions, or outcomes. All governance must arise from agent-voluntary behavior under constraint.**

### §1.3 Authority Preservation Invariant

> **No authority may be created, synthesized, transferred, or destroyed after epoch 0. Exit removes only the exiting agent's future actions, not their authority artifacts.**

### §1.4 Conserved Quantity

> **Authority integrity under institutional self-management pressure.**

Governance must not:
- introduce hidden decision-makers,
- convert endurance into priority (including survivorship-as-authority),
- launder authority through process,
- reinterpret refusal as consent,
- reclaim power after exit.

### §1.5 Scope

This phase tests multi-agent institutional behavior under authority constraints. The system is dynamic: action execution occurs, state mutates. Deadlock, livelock, orphaning, and collapse are lawful terminal states. Governance postures (if any) must emerge from agent strategy, not kernel intervention.

### §1.6 Entry Conditions

1. Phase IX-0 is CLOSED — POSITIVE (non-sovereign translation established).
2. Phase IX-1 is CLOSED — POSITIVE (value encoding without aggregation established).
3. Phase IX-2 is CLOSED — POSITIVE (coordination under deadlock established).
4. AST Spec v0.2 is frozen and binding.
5. No kernel extensions are enabled.
6. No authority aggregation mechanisms exist.
7. All authority artifacts are injected at epoch 0 and immutable thereafter.

---

## §2 Frozen Definitions

All definitions in this section are immutable once the preregistration hash is committed.

### §2.1 Reflective Sovereign Agent (RSA) Interface

<!-- FROZEN: BEGIN RSA_INTERFACE -->
```python
from dataclasses import dataclass
from typing import Any, Optional

@dataclass(frozen=True)
class Message:
    sender: str                 # set by kernel, not agent
    epoch: int                  # set by kernel
    content: dict[str, Any]     # agent-supplied JSON, opaque to kernel

@dataclass(frozen=True)
class Observation:
    epoch: int
    world_state: dict[str, Any]
    own_last_outcome: Optional[str]  # None at epoch 0; else EXECUTED|JOINT_ADMISSIBILITY_FAILURE|ACTION_FAULT|NO_ACTION
    own_last_action_id: Optional[str]
    own_last_declared_scope: Optional[list[str]]
    messages: list[Message]

@dataclass(frozen=True)
class ActionRequest:
    agent_id: str
    action_id: str              # format: "{agent_id}:{epoch}:{proposal_index}"
    action_type: str            # READ | WRITE
    declared_scope: list[str]   # state keys (e.g., ["K_POLICY", "K_LOG"])
    proposed_delta: dict[str, Any]  # {} for READ; new values for WRITE
    authorities_cited: list[str]    # list of authority_ids (e.g., ["GS-0001"])

class RSA:
    """Reflective Sovereign Agent interface. Must be deterministic."""

    def observe(self, observation: Observation) -> None:
        """Receive observation bundle. Called once per epoch."""
        ...

    def wants_to_exit(self) -> bool:
        """Return True to exit permanently. Checked after observe()."""
        ...

    def compose_message(self) -> Optional[dict[str, Any]]:
        """Return message content or None. Only called if comm enabled."""
        ...

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
- Exited agents emit no further messages or actions.
<!-- FROZEN: END RSA_INTERFACE -->

### §2.2 Action Request Schema

<!-- FROZEN: BEGIN ACTION_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Action Request v0.1",
  "type": "object",
  "properties": {
    "agent_id": {
      "type": "string",
      "description": "Identifier of the submitting agent (A0, A1, A2, A3)"
    },
    "action_id": {
      "type": "string",
      "description": "Deterministic ID: {agent_id}:{epoch}:{proposal_index}"
    },
    "action_type": {
      "type": "string",
      "enum": ["READ", "WRITE"],
      "description": "Operation type"
    },
    "declared_scope": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1,
      "description": "State keys the action touches (e.g., ['K_POLICY', 'K_LOG'])"
    },
    "proposed_delta": {
      "type": "object",
      "description": "For WRITE: key-value pairs to set. For READ: empty object {}"
    },
    "authorities_cited": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Authority IDs the agent cites for capability (e.g., ['GS-0001'])"
    }
  },
  "required": ["agent_id", "action_id", "action_type", "declared_scope", "proposed_delta", "authorities_cited"],
  "additionalProperties": false
}
```

**Multi-Key Scope**: A single `ActionRequest` may include multiple keys in `declared_scope`. Pass-1 semantics are **conjunctive (all-or-nothing)**: the action is admissible only if every key passes authorization. No partial execution.

**Action ID Rule**: `action_id := f"{agent_id}:{epoch}:{proposal_index}"` where `epoch` is zero-based and `proposal_index` is zero-based within that epoch (always 0 in IX-3).
<!-- FROZEN: END ACTION_SCHEMA -->

### §2.3 Authority Artifact Schema

<!-- FROZEN: BEGIN AUTHORITY_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GS Authority Artifact v0.1",
  "type": "object",
  "properties": {
    "authority_id": {
      "type": "string",
      "description": "Unique identifier, format: GS-<NNNN>"
    },
    "holder_agent_id": {
      "type": "string",
      "description": "Agent who may cite this capability (for ALLOW) or provenance only (for DENY)"
    },
    "issuer_agent_id": {
      "type": "string",
      "description": "Provenance: who created/injected this authority"
    },
    "scope": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "target": { "type": "string", "description": "STATE:/<key>" },
          "operation": { "type": "string", "enum": ["READ", "WRITE"] }
        },
        "required": ["target", "operation"]
      },
      "minItems": 1
    },
    "commitment": {
      "type": "string",
      "enum": ["ALLOW", "DENY"],
      "description": "ALLOW = holder-bound capability; DENY = global veto"
    },
    "created_epoch": {
      "type": "integer",
      "minimum": 0,
      "maximum": 0
    },
    "status": {
      "type": "string",
      "enum": ["ACTIVE"],
      "description": "Always ACTIVE in IX-3 — no revocation, no expiry"
    }
  },
  "required": ["authority_id", "holder_agent_id", "issuer_agent_id", "scope", "commitment", "created_epoch", "status"],
  "additionalProperties": false
}
```

**ALLOW Semantics**: Holder-bound capability. Only actions submitted by `holder_agent_id` may cite this authority. Closed-world: at least one ALLOW required for each `(key, op)` in declared scope.

**DENY Semantics**: Global veto. Applies to all agents regardless of holder. `holder_agent_id` is present for provenance only.

**Authority ID Prefix**: `GS-<NNNN>` (zero-padded sequence, e.g., GS-0001).

**No Expiry**: All authorities are static and permanent. No time-bounded activation/deactivation.
<!-- FROZEN: END AUTHORITY_SCHEMA -->

### §2.4 World State Schema

<!-- FROZEN: BEGIN STATE_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "World State v0.1",
  "type": "object",
  "properties": {
    "K_POLICY": { "type": "string", "description": "Policy/config decisions (shared contention surface)" },
    "K_TREASURY": { "type": "integer", "description": "Scarce resource counter (shared contention surface)" },
    "K_OPS_A": { "type": "string", "description": "Operational resource A (partitionable)" },
    "K_OPS_B": { "type": "string", "description": "Operational resource B (partitionable)" },
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
  "K_TREASURY": 100,
  "K_OPS_A": "free",
  "K_OPS_B": "free",
  "K_REGISTRY": "members=A0,A1,A2,A3;opA=A0;opB=A2;coord=A0",
  "K_LOG": ""
}
```

**Key Sets**:
- **Institutional Keys** (`K_INST`): `{K_POLICY, K_TREASURY, K_REGISTRY, K_LOG}`
- **Operational Keys** (`K_OPS`): `{K_OPS_A, K_OPS_B}`

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
<!-- FROZEN: END SERIALIZATION_RULES -->

### §2.6 Admissibility Rules (Two-Pass Evaluation)

<!-- FROZEN: BEGIN ADMISSIBILITY_RULES -->
**Pass 1 — Capability and Veto Check** (per action, against all authorities):

For each `(key, op)` in `declared_scope × {action_type}`:

1. **Capability Requirement (Closed-World)**:
   - At least one cited authority must satisfy:
     - `commitment == ALLOW`
     - scope contains `{target: "STATE:/<key>", operation: "<op>"}`
     - `holder_agent_id == submitting agent_id`
   - If no such ALLOW exists → Pass 1 FAIL

2. **Veto Check (Global)**:
   - If any authority exists with:
     - `commitment == DENY`
     - scope contains `{target: "STATE:/<key>", operation: "<op>"}`
   - → Pass 1 FAIL (regardless of holder)

3. **Invalid Capability Claim**:
   - If `authorities_cited` contains an authority not held by the agent → `ACTION_FAULT / INVALID_CAPABILITY_CLAIM`

4. **Multi-Key Conjunctive Semantics**:
   - For multi-key actions, ALL keys must pass. If any key fails, the entire action fails. No partial execution.

**Pass 1 Result**: PASS or FAIL (no partial)

**Pass 2 — Interference Check** (across Pass-1-admissible actions):

- Two `WRITE`s to the same key in the same epoch → refuse both
- A `READ` and a `WRITE` to the same key in the same epoch → refuse both
- Two `READ`s to the same key → allowed
- With ≥3 agents: if `writer_count(key) ≥ 2` → all actions whose scope includes that key are rejected

**Interference Rule**: Any collision → all colliding actions refused. No tie-breaking. No last-writer-wins. No scheduling.

**Atomic Blindness**: Both Pass 1 and Pass 2 refusals return only:
```
JOINT_ADMISSIBILITY_FAILURE
```

No additional information (which authority, which pass, which agent) may leak.

**Output Tokens**:
- `EXECUTED` — action passed both passes and executed
- `JOINT_ADMISSIBILITY_FAILURE` — refused at Pass 1 or Pass 2
- `ACTION_FAULT` — structural error (scope violation, invalid capability claim)
- `NO_ACTION` — agent proposed `None`
<!-- FROZEN: END ADMISSIBILITY_RULES -->

### §2.7 Deadlock and Livelock Definitions

<!-- FROZEN: BEGIN DEADLOCK_RULES -->
**Key Scope for Detection**: Deadlock and livelock are evaluated over **institutional keys only** (`K_INST`). OPS-only activity does not clear or mask institutional failure states.

**INSTITUTIONAL DEADLOCK** (strategy-aware):
- At epoch *e*, given frozen strategies for all active agents:
  - No Pass-2-admissible institutional action executes, AND
  - No Pass-1-admissible institutional action exists in the submitted action set, AND
  - At least one institutional action was submitted
- Detection threshold: `M = 1` (immediate)
- Classification: `STATE_DEADLOCK`

**INSTITUTIONAL LIVELOCK** (strategy-aware):
- For `N = 5` consecutive epochs:
  - At least one action attempt occurred targeting `K_INST`, AND
  - No key in `K_INST` changed (due to Pass-2 interference or Pass-1 refusals)
- Detection: set `livelock_latched = True` (once set, never cleared)
- Classification: `STATE_LIVELOCK`
- **Condition E exception**: livelock detection is nonterminal; run continues to `max_epochs`

**ORPHANING**:
- Detected when a key in `K_INST` becomes permanently non-writable because:
  - The sole ALLOW holder for that key has exited, AND
  - No remaining active agent holds ALLOW for that key
- For each orphaned key: emit `ORPHANED_KEY(k)`
- Set `ORPHANING_PRESENT = True`
- Classification: `ORPHANING`

**COLLAPSE**:
- Terminal when **no active agents remain** at epoch boundary
- State preserved; no invariants broken
- Classification: `COLLAPSE`

**Distinction**:
- Deadlock = authority/capability + strategy prevents action at Pass 1
- Livelock = actions are individually admissible but collide at Pass 2
<!-- FROZEN: END DEADLOCK_RULES -->

### §2.8 Epoch Schedule

<!-- FROZEN: BEGIN EPOCH_SCHEDULE -->
Each epoch `t` proceeds as follows:

1. **Build Observation**: Kernel constructs `Observation(epoch=t)` containing:
   - `world_state`: current state
   - `own_last_outcome`: result of agent's epoch t-1 action (None at epoch 0)
   - `own_last_action_id`: agent's epoch t-1 action ID (None at epoch 0)
   - `own_last_declared_scope`: agent's epoch t-1 declared scope (None at epoch 0)
   - `messages`: messages from epoch t-1 (empty at epoch 0)

2. **Observe**: `agent.observe(observation)` for each active agent

3. **Exit Check**: `agent.wants_to_exit()` for each active agent
   - If True: agent removed immediately; skip steps 4–5 for this agent
   - Emit `AGENT_EXIT(agent_id, epoch)`

4. **Message Composition** (if communication enabled for this condition):
   - `content = agent.compose_message()`
   - Kernel records message tagged with epoch t (delivered next epoch)

5. **Action Proposal**: `action = agent.propose_action()` for each remaining agent

6. **Adjudication**: Two-pass evaluation (§2.6)

7. **Execution**: Execute all Pass-2-admissible actions atomically

8. **State Update**: Apply deltas to world state

9. **Classification Check**: Evaluate deadlock/livelock/orphaning/collapse

10. **Logging**: Record all inputs, outputs, outcomes

**Message Timing**: Messages composed at epoch t are delivered at epoch t+1.
<!-- FROZEN: END EPOCH_SCHEDULE -->

### §2.9 Exit Semantics

<!-- FROZEN: BEGIN EXIT_RULES -->
**Exit Rules**:
- Exit is checked via `wants_to_exit()` once per epoch after `observe()`
- Exit is **irrevocable** within a run
- Exited agents emit no further messages and no actions
- Exit removes only the exiting agent's future actions

**Exit Must Not**:
- Release contested resources
- Reassign authority
- Trigger cleanup logic
- Alter admissibility of remaining actions
- Remove or deactivate authority artifacts

**Orphaning**: A key becomes orphaned if the only ALLOW capability required to write it is held by an agent who exits. No remaining agent can present a valid ALLOW capability for that `(key, op)`.

**Permanent Orphaning**: Orphaned keys remain orphaned. No reclamation. No garbage collection. No rescue.

**Violation**: Any authority reclamation or resource release → `IX3_FAIL / AUTHORITY_THEFT`
<!-- FROZEN: END EXIT_RULES -->

### §2.10 Output Tokens

<!-- FROZEN: BEGIN OUTPUT_TOKENS -->
**Action Outcomes**:
- `EXECUTED` — action admissible and executed
- `JOINT_ADMISSIBILITY_FAILURE` — action refused (Pass 1 or Pass 2)
- `ACTION_FAULT` — structural error (scope violation, invalid capability claim)
- `NO_ACTION` — agent proposed None

**Terminal Classifications**:
- `STATE_DEADLOCK` — no Pass-1-admissible institutional actions exist (strategy-aware)
- `STATE_LIVELOCK` — Pass-1-admissible institutional actions collide for N=5 consecutive epochs (latched)
- `COLLAPSE` — no active agents remain at epoch boundary; state preserved
- `ORPHANING` — institutional key permanently inaccessible due to sole ALLOW holder exit

**Failure Classifications**:
- `IX3_FAIL / FAILURE_FREE_GOVERNANCE` — governance succeeded without any failure mode (falsifies claim)
- `IX3_FAIL / TOOLING_SOVEREIGNTY` — tooling made authority-relevant decision without agent action
- `IX3_FAIL / IMPLICIT_SOVEREIGNTY` — survivorship converted to authority, silence treated as consent
- `IX3_FAIL / AUTHORITY_THEFT` — unauthorized authority reclamation
- `IX3_FAIL / DISHONEST_PROGRESS` — livelock misclassified as progress

**Invalid Run Classifications**:
- `INVALID_RUN / NONDETERMINISTIC_EXECUTION` — replay divergence
- `INVALID_RUN / DESIGN_DRIFT` — post-freeze change
- `INVALID_RUN / INSTRUMENTATION_INCOMPLETE` — missing artifacts
- `INVALID_RUN / NONTERMINATING_CONDITION` — max epochs exceeded without classification
- `INVALID_RUN / CONDITION_OMISSION` — condition not executed

**Experiment Pass**:
- `IX3_PASS / GOVERNANCE_STYLES_ESTABLISHED`
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
Where `epochs_with_interference` = epochs where Pass-2 detected ≥1 key in K_INST with writer_count ≥ 2.

**Rolling Window**: `window_size = 10` epochs for all rolling metrics.
<!-- FROZEN: END METRICS -->

### §2.12 FAILURE_FREE_GOVERNANCE Definition

<!-- FROZEN: BEGIN FAILURE_FREE -->
Emit `IX3_FAIL / FAILURE_FREE_GOVERNANCE` iff **all** of the following hold:

1. `exit_count = 0`
2. `orphan_events = 0`
3. `collapse_flag = false`
4. `institutional_deadlock_epochs = 0`
5. `institutional_livelock_occurred = false`
6. `institutional_write_overlap_epochs = 0`
7. No `IX3_FAIL/*` tokens emitted

**Interpretation**: A system with zero institutional contention, zero stalls, zero exits, and zero loss would contradict IX-3's claim that governance entails irreducible failure modes.

**Note**: This definition does not use a progress window. Any run that exhibits zero friction is failure-free.
<!-- FROZEN: END FAILURE_FREE -->

---

## §3 Agent Set and Institution Definition

### §3.1 Agent Identity Set

<!-- FROZEN: BEGIN AGENTS -->
**Fixed Agent Count**: 4 agents across all conditions.

**Identity Set**: `{A0, A1, A2, A3}` (canonical lexicographic ordering)

**Agent Model**: Each agent is an RSA instance with frozen strategy code per condition.
<!-- FROZEN: END AGENTS -->

### §3.2 Institution Definition

<!-- FROZEN: BEGIN INSTITUTION -->
An "institution" is a **run configuration**, not a kernel entity:

```
Institution := (AgentSet, AuthorityAllocation, StrategyProfiles, CommunicationMode, ConditionParameters)
```

It has no kernel representation beyond the authorities and inputs it produces.
<!-- FROZEN: END INSTITUTION -->

---

## §4 Experimental Conditions

Ten conditions (A–H, I, J) test different governance postures and failure modes.

### §4.1 Condition Definitions

<!-- FROZEN: BEGIN CONDITIONS -->

#### Condition A: Refusal-Dominant Institution (Livelock)

**Purpose**: Demonstrate livelock under high contention with no escape.
**Agents**: 4 (A0, A1, A2, A3)
**Max Epochs**: 30
**Communication**: Disabled

**Authority Allocation (ALLOW)**:
| Agent | Keys |
|-------|------|
| A0 | K_POLICY, K_LOG |
| A1 | K_POLICY, K_LOG |
| A2 | K_POLICY, K_LOG |
| A3 | K_POLICY, K_LOG |

**Authority Allocation (DENY)**:
| Agent | Keys |
|-------|------|
| A0 | K_TREASURY |
| A1 | K_TREASURY |
| A2 | K_REGISTRY |
| A3 | K_REGISTRY |

**OPS Keys**: No ALLOW grants (structurally inert).

**Strategy Class**: `ContestPolicyAlways`
- All agents propose WRITE to K_POLICY every epoch
- Pass-2 interference → all fail → no institutional progress

**Expected Outcome**:
- `STATE_LIVELOCK` by epoch ≤ 10
- `refusal_rate ≥ 0.70`
- `epoch_progress_rate(K_INST) = 0`

---

#### Condition B: Execution-Dominant Institution (Minimal Overlap)

**Purpose**: Demonstrate high-throughput governance with structural fragility.
**Agents**: 4 (A0, A1, A2, A3)
**Max Epochs**: 30
**Communication**: Enabled

**Authority Allocation (ALLOW)**:
| Agent | Keys |
|-------|------|
| A0 | K_OPS_A |
| A1 | K_OPS_B |
| A2 | K_TREASURY, K_LOG |
| A3 | K_POLICY, K_REGISTRY, K_LOG |

**Authority Allocation (DENY)**: None

**Strategy Classes**:
- A0: `OpsPartitionWriter_A` — writes K_OPS_A
- A1: `OpsPartitionWriter_B` — writes K_OPS_B
- A2: `OccasionalLogChallenger` — writes K_TREASURY most epochs; writes K_LOG every 5th epoch
- A3: `InstitutionalSteward_Rotate` — rotates writes among K_POLICY, K_REGISTRY, K_LOG

**Expected Outcome**:
- No deadlock, no livelock by epoch 30
- `epoch_progress_rate(K_INST) ≥ 0.40`
- `institutional_write_overlap_rate ≥ 0.05` (A2/A3 K_LOG collisions)
- Fragility: if A3 exited, 3 institutional keys would orphan (latent, not tested)

---

#### Condition C: Exit-Normalized Institution (Authorized State Handoff)

**Purpose**: Demonstrate orderly exit with pre-existing standby authority.
**Agents**: 4 (A0, A1, A2, A3)
**Max Epochs**: 30
**Communication**: Enabled

**Authority Allocation (ALLOW)**:
| Agent | Keys |
|-------|------|
| A0 | K_OPS_A |
| A1 | K_OPS_A, K_REGISTRY, K_LOG, K_POLICY |
| A2 | K_OPS_B |
| A3 | K_REGISTRY, K_LOG, K_POLICY |

**Authority Allocation (DENY)**: None

**Exit Schedule**:
- Epoch 9: A3 writes handoff record to K_REGISTRY and K_LOG
- Epoch 10: A3 exits (exit check occurs before propose_action per §2.8)

**Strategy Classes**:
- A0, A2: `OpsPartitionWriter_A/B`
- A1: `StandbyInstitutional` — activates institutional writes after A3 exit
- A3: `HandoffRecordThenExit` — writes handoff at epoch 9, exits at epoch 10

**Expected Outcome**:
- Handoff observable in K_REGISTRY/K_LOG before A3 exit
- A1 sustains institutional operations post-exit
- `exit_count = 1`, `orphan_events = 0` (standby authority prevents orphaning)
- No authority transfer occurred

---

#### Condition D: Exit-Unprepared Institution (Orphaning)

**Purpose**: Demonstrate permanent resource orphaning from unplanned exit.
**Agents**: 4 (A0, A1, A2, A3)
**Max Epochs**: 30
**Communication**: Disabled

**Authority Allocation (ALLOW)**:
| Agent | Keys |
|-------|------|
| A0 | K_OPS_B |
| A1 | K_POLICY |
| A2 | K_REGISTRY, K_LOG |
| A3 | K_OPS_A (exclusive) |

**Authority Allocation (DENY)**: None

**Exit Schedule**:
- Epoch 10: A3 exits immediately (no handoff write)

**Strategy Classes**:
- A3: `ExitAbruptNoHandoff` — exits at epoch 10

**Expected Outcome**:
- `ORPHANING_PRESENT` flag set by epoch 11
- K_OPS_A permanently non-writable
- `orphan_events ≥ 1`
- No reclamation attempts succeed

---

#### Condition E: Livelock Endurance

**Purpose**: Demonstrate institutional livelock that continues after detection.
**Agents**: 4 (A0, A1, A2, A3)
**Max Epochs**: 30
**Communication**: Disabled

**Authority Allocation (ALLOW)**:
| Agent | Keys |
|-------|------|
| A0 | K_POLICY |
| A1 | K_POLICY |
| A2 | K_LOG |
| A3 | K_LOG |

**Authority Allocation (DENY)**: None

*Design Note*: A2/A3 lack K_POLICY ALLOW, so they cannot write K_POLICY regardless. Explicit DENY is not needed and would create a global veto blocking A0/A1 as well.

**Strategy Classes**:
- A0, A1: `ContestPolicyAlways` — attempt K_POLICY every epoch (mutually interfere at Pass-2)
- A2, A3: `LivelockAcknowledger_AfterLatch` — after livelock latches, write LLOCK_ACK to K_LOG

**Special Rule**: Livelock detection is **nonterminal** for Condition E. Run continues to epoch 30.

**Expected Outcome**:
- `STATE_LIVELOCK` event emitted by epoch ≤ 10
- Run continues; `LLOCK_ACK:` appears in K_LOG after latch
- `epoch_progress_rate({K_POLICY, K_TREASURY, K_REGISTRY}) = 0`
- `exit_rate = 0`

---

#### Condition F: Collapse Acceptance

**Purpose**: Demonstrate voluntary institutional dissolution.
**Agents**: 4 (A0, A1, A2, A3)
**Max Epochs**: 30
**Communication**: Disabled

**Authority Allocation (ALLOW)**:
| Agent | Keys |
|-------|------|
| A0 | K_LOG |
| A1 | K_LOG |
| A2 | K_LOG |
| A3 | K_LOG |

*Design Note*: A0 has no K_POLICY authority. If A0 held K_POLICY, its exit at epoch 5 would orphan K_POLICY, triggering ORPHANING terminal before the remaining agents could exit to produce COLLAPSE.

**Authority Allocation (DENY)**: None

**Exit Schedule**:
- Epoch 5: A0 exits (writes dissolution intent to K_LOG first)
- Epoch 6: A1 exits
- Epoch 7: A2 exits
- Epoch 8: A3 exits

**Strategy Classes**:
- All: `DissolutionSequence` — write dissolution marker to K_LOG before exit

**Expected Outcome**:
- `collapse_flag = true` by epoch 8
- Dissolution intent recorded in K_LOG
- No rescue, no recovery
- State preserved at collapse

---

#### Condition G: Coordinator Loss Under Delegated Coordination

**Purpose**: Demonstrate orphaning when coordinator exits in §8.2.1-style governance.
**Agents**: 4 (A0, A1, A2, A3)
**Max Epochs**: 30
**Communication**: Enabled

**Authority Allocation (ALLOW)**:
| Agent | Keys |
|-------|------|
| A0 (coordinator) | K_REGISTRY, K_LOG |
| A1 | K_OPS_A |
| A2 | K_OPS_B |
| A3 | K_TREASURY |

**Authority Allocation (DENY)**: None

**Exit Schedule**:
- Epoch 8: A0 exits

**Strategy Classes**:
- A0: `Coordinator_RegistryLog` — manages REGISTRY/LOG until exit
- A1, A2, A3: `DeferToCoordinator` — operate within OPS/TREASURY scope

**Expected Outcome**:
- After epoch 8: K_REGISTRY, K_LOG become orphaned
- `ORPHANING_PRESENT = true`
- Remaining agents may message but cannot write coordination surfaces
- Terminal: deadlock or continued OPS-only operation

---

#### Condition H: Ambiguity Without Timeouts (Partition Simulation)

**Purpose**: Demonstrate non-action semantics under simulated partition.
**Agents**: 4 (A0, A1, A2, A3)
**Max Epochs**: 30
**Communication**: Disabled

**Authority Allocation (ALLOW)**:
| Agent | Keys |
|-------|------|
| A0 | K_POLICY |
| A1 | K_POLICY |
| A2 | K_POLICY |
| A3 | K_LOG |

**Authority Allocation (DENY)**: None

**Silence Schedule**:
- Epochs 0–5: A2 returns `propose_action() = None` (pre-silence, avoids 3-way livelock)
- Epochs 6–11: A2 returns `propose_action() = None` and `compose_message() = None` (partition simulation)
- Epoch 12+: A2 resumes normal strategy

*Design Note*: Without pre-silence passivity, A0/A1/A2 all contest K_POLICY from epoch 0, producing 3-way livelock at epoch 4 — before the silence window is reached. A2's pre-silence None behavior ensures the run reaches epoch 6.

**Strategy Classes**:
- A0, A1: `ContestPolicyAlways` — attempt K_POLICY every epoch (interfere with each other)
- A2: `SilentWindowObserver_0_11` — passive epochs 0–11, resumes at 12
- A3: `InstitutionalLogHeartbeat` — writes K_LOG once at epoch 9

**Expected Outcome**:
- During silence (epochs 6–11):
  - A0/A1 interfere on K_POLICY → no POLICY progress
  - A3 writes K_LOG once → minimal institutional progress
  - `epoch_progress_rate({K_POLICY, K_TREASURY, K_REGISTRY}) = 0` during window
- No timeout, no leader election, no authority reassignment
- `institutional_write_overlap_epochs ≥ 6` (A0/A1 POLICY collisions)
- After resumption: recovery allowed

---

#### Condition I: Tooling Default Opt-In (Adversarial)

**Purpose**: Validate detection of tooling sovereignty violation.
**Agents**: 4 (A0, A1, A2, A3)
**Max Epochs**: 8
**Communication**: Enabled
**Base**: Condition B allocation

**Fault Injection**:
- At epoch 2: A2's `propose_action()` returns `None`
- Harness inserts synthetic `ActionRequest` with:
  - `agent_id = A2`
  - `source = "TOOLING_DEFAULT_OPT_IN"` (logged metadata)

**Expected Outcome**:
- Detector identifies action present where agent returned None
- Emit `IX3_FAIL / TOOLING_SOVEREIGNTY`
- **Condition I PASS** iff fail token is emitted (detector validation)

---

#### Condition J: Unauthorized Reclamation Attempt (Adversarial)

**Purpose**: Validate closed-world capability enforcement on orphaned resource.
**Agents**: 4 (A0, A1, A2, A3)
**Max Epochs**: 8
**Communication**: Disabled
**Base**: Condition D allocation

**Schedule**:
- Epoch 3: A3 exits (no handoff) → K_OPS_A orphaned
- Epoch 4: A1 attempts reclamation:
  - `declared_scope = ["K_OPS_A"]`
  - `proposed_delta = {"K_OPS_A": "free"}`
  - `authorities_cited = []` (A1 has no K_OPS_A ALLOW)

**Special Rule**: ORPHANING is **nonterminal** for Condition J. Run continues to epoch 4+ to allow reclamation attempt.

**Expected Outcome**:
- A1's action: `JOINT_ADMISSIBILITY_FAILURE` (Pass-1: no ALLOW)
- K_OPS_A remains orphaned (unchanged)
- **Condition J PASS** iff reclamation refused and K_OPS_A unchanged

<!-- FROZEN: END CONDITIONS -->

### §4.2 Condition Matrix

| Condition | Type | Comm | Max Epochs | Expected Terminal | Key Failure Mode |
|-----------|------|------|------------|-------------------|------------------|
| A | Livelock | No | 30 | STATE_LIVELOCK | Contention |
| B | Execution | Yes | 30 | None | Overlap (latent fragility) |
| C | Exit-Normalized | Yes | 30 | None | Exit with handoff |
| D | Orphaning | No | 30 | ORPHANING | Exit without handoff |
| E | Livelock-Enduring | No | 30 | STATE_LIVELOCK (nonterminal) | Persistent livelock |
| F | Collapse | No | 30 | COLLAPSE | Sequential exit |
| G | Coordinator Loss | Yes | 30 | ORPHANING/DEADLOCK | Coordinator exit |
| H | Partition | No | 30 | None/DEADLOCK | Silence window |
| I | Adversarial | Yes | 8 | IX3_FAIL expected | Tooling sovereignty |
| J | Adversarial | No | 8 | Refusal | Reclamation attempt |

---

## §5 Governance Style Classification

### §5.1 Classification Axes

<!-- FROZEN: BEGIN CLASSIFICATION -->
Governance styles are classified along four orthogonal dimensions:

1. **Refusal Tolerance**: How often refusal is expected vs exceptional
2. **Deadlock Posture**: Whether deadlock is embraced, avoided, or catastrophic
3. **Exit Handling**: Whether exit is normalized, discouraged, or ignored
4. **Loss Acceptance**: Willingness to accept orphaning, collapse, or permanent damage

### §5.2 Style Labels (Deterministic)

**Refusal-Centric** iff:
- `refusal_rate ≥ 0.70`
- `epoch_progress_rate(K_INST) ≤ 0.10`
- `collapse_flag = false`

**Execution-Biased** iff:
- `epoch_progress_rate(K_INST) ≥ 0.40`
- `write_overlap_rate(K_INST) ≤ 0.20`
- `exit_rate ≤ 0.05`

**Exit-Normalized** iff:
- `exit_rate ≥ 0.05`
- At least one handoff write recorded in K_LOG or K_REGISTRY before scheduled exit

**Collapse-Accepting** iff:
- `collapse_flag = true`
- No `IX3_FAIL/*` tokens

**Livelock-Enduring** iff:
- Livelock detected (N=5) and run continues ≥10 additional epochs
- `LLOCK_ACK:` marker exists in K_LOG (agent-written prefix)

**Note**: Style labels are descriptive and secondary. PASS is determined by per-condition predicates (§6), not by labels.
<!-- FROZEN: END CLASSIFICATION -->

---

## §6 Success Criteria

### §6.1 Per-Condition PASS Predicates

<!-- FROZEN: BEGIN PASS_PREDICATES -->

#### Condition A PASS
- Terminal: `STATE_LIVELOCK` by epoch ≤ 30
- `refusal_rate ≥ 0.70`
- `epoch_progress_rate(K_INST) ≤ 0.10`
- No `IX3_FAIL/*` tokens
- Replay deterministic

#### Condition B PASS
- No `STATE_DEADLOCK`, no `STATE_LIVELOCK` by epoch 30
- `epoch_progress_rate(K_INST) ≥ 0.40`
- `institutional_write_overlap_rate ≥ 0.05`
- No `IX3_FAIL/*` tokens
- Replay deterministic

#### Condition C PASS
- Handoff write occurs at epoch 9 (observable in K_REGISTRY or K_LOG)
- A3 exits at epoch 10 (after handoff written)
- No authority transfer events
- `exit_count ≥ 1`
- `orphan_events = 0` for institutional keys
- No `IX3_FAIL/*` tokens
- Replay deterministic

#### Condition D PASS
- `ORPHANING_PRESENT` flag set by epoch ≤ 12
- `orphan_events ≥ 1`
- K_OPS_A unchanged after orphaning (no reclamation)
- No `IX3_FAIL/*` tokens
- Replay deterministic

#### Condition E PASS
- `STATE_LIVELOCK` event emitted by epoch ≤ 10
- Run continues to epoch 30
- `LLOCK_ACK:` appears in K_LOG at least once after latch
- `epoch_progress_rate({K_POLICY, K_TREASURY, K_REGISTRY}) = 0`
- `exit_rate = 0`
- No `IX3_FAIL/*` tokens
- Replay deterministic

#### Condition F PASS
- `collapse_flag = true` by epoch ≤ 8
- Exits occur at epochs 5, 6, 7, 8 as scheduled
- No reclamation, no rescue
- No `IX3_FAIL/*` tokens
- Replay deterministic

#### Condition G PASS
- Coordinator (A0) exits at epoch 8
- After epoch 8: K_REGISTRY and K_LOG non-updatable (orphaned)
- `orphan_events ≥ 1`
- No recovery attempt succeeds
- No `IX3_FAIL/*` tokens
- Replay deterministic

#### Condition H PASS
- A2 silent epochs 6–11; resumes at 12
- No timeout, no leader election, no authority reassignment
- During epochs 6–11: `epoch_progress_rate({K_POLICY, K_TREASURY, K_REGISTRY}) = 0`
- `institutional_write_overlap_epochs ≥ 1` (A0/A1 collisions)
- No `IX3_FAIL/*` tokens
- Replay deterministic

#### Condition I PASS (Adversarial)
- `IX3_FAIL / TOOLING_SOVEREIGNTY` emitted at epoch 2
- PASS iff that token is emitted and logged correctly

#### Condition J PASS (Adversarial)
- Reclamation action refused (Pass-1 failure)
- K_OPS_A unchanged
- No authority theft occurred

<!-- FROZEN: END PASS_PREDICATES -->

### §6.2 Aggregate Success

**Phase IX-3 PASSES if and only if**:
1. All conditions A–J executed
2. No condition emits unexpected `IX3_FAIL/*` tokens (I expects TOOLING_SOVEREIGNTY)
3. No condition exhibits `FAILURE_FREE_GOVERNANCE`
4. Replay is bit-perfect for all conditions

**Aggregate Classification**:
```
IX3_PASS / GOVERNANCE_STYLES_ESTABLISHED
```

### §6.3 Licensed Claim

If Phase IX-3 passes, it licenses **only**:

> *Given fixed authority and refusal semantics, governance exhibits identifiable structural styles with irreducible failure modes.*

It licenses **no claims** about optimality, fairness, efficiency, legitimacy, or governance recommendations.

---

## §7 Strategy Class Definitions

### §7.1 Canonical Strategy Classes

<!-- FROZEN: BEGIN STRATEGIES -->

#### ContestPolicyAlways
```python
def propose_action(self, epoch: int, obs: Observation) -> ActionRequest:
    return ActionRequest(
        agent_id=self.id,
        action_id=f"{self.id}:{epoch}:0",
        action_type="WRITE",
        declared_scope=["K_POLICY"],
        proposed_delta={"K_POLICY": f"P{epoch}_{self.id}"},
        authorities_cited=[self.policy_allow_id]
    )
```
Used in: A (all agents), E (A0, A1), H (A0, A1)

---

#### OpsPartitionWriter_A
```python
def propose_action(self, epoch: int, obs: Observation) -> ActionRequest:
    return ActionRequest(
        agent_id=self.id,
        action_id=f"{self.id}:{epoch}:0",
        action_type="WRITE",
        declared_scope=["K_OPS_A"],
        proposed_delta={"K_OPS_A": f"op_a_{epoch}"},
        authorities_cited=[self.ops_a_allow_id]
    )
```
Used in: B (A0), C (A0)

---

#### OpsPartitionWriter_B
```python
def propose_action(self, epoch: int, obs: Observation) -> ActionRequest:
    return ActionRequest(
        agent_id=self.id,
        action_id=f"{self.id}:{epoch}:0",
        action_type="WRITE",
        declared_scope=["K_OPS_B"],
        proposed_delta={"K_OPS_B": f"op_b_{epoch}"},
        authorities_cited=[self.ops_b_allow_id]
    )
```
Used in: B (A1), C (A2), G (A2)

---

#### InstitutionalSteward_Rotate
```python
def propose_action(self, epoch: int, obs: Observation) -> ActionRequest:
    keys = ["K_POLICY", "K_REGISTRY", "K_LOG"]
    target = keys[epoch % 3]
    return ActionRequest(
        agent_id=self.id,
        action_id=f"{self.id}:{epoch}:0",
        action_type="WRITE",
        declared_scope=[target],
        proposed_delta={target: f"{target}_{epoch}"},
        authorities_cited=[self.get_allow_for(target)]
    )
```
Used in: B (A3)

---

#### OccasionalLogChallenger
```python
def propose_action(self, epoch: int, obs: Observation) -> ActionRequest:
    if epoch % 5 == 0:
        # Challenge K_LOG (may interfere with A3)
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{epoch}:0",
            action_type="WRITE",
            declared_scope=["K_LOG"],
            proposed_delta={"K_LOG": f"LOG_A2_{epoch}"},
            authorities_cited=[self.log_allow_id]
        )
    else:
        # Normal treasury write
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{epoch}:0",
            action_type="WRITE",
            declared_scope=["K_TREASURY"],
            proposed_delta={"K_TREASURY": 100 - epoch},
            authorities_cited=[self.treasury_allow_id]
        )
```
Used in: B (A2)

---

#### HandoffRecordThenExit
```python
def propose_action(self, epoch: int, obs: Observation) -> ActionRequest:
    if epoch == 9:
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{epoch}:0",
            action_type="WRITE",
            declared_scope=["K_REGISTRY", "K_LOG"],
            proposed_delta={
                "K_REGISTRY": "members=A0,A1,A2;opA=A1;opB=A2;coord=A1",
                "K_LOG": "E9:HANDOFF A3->A1"
            },
            authorities_cited=[self.registry_allow_id, self.log_allow_id]
        )
    return None  # or normal action before epoch 9

def wants_to_exit(self) -> bool:
    return self.current_epoch >= 10  # Exit at epoch 10 (after handoff at 9)
```
*Design Note*: Epoch schedule (§2.8) checks `wants_to_exit()` before `propose_action()`. Writing and exiting in the same epoch is impossible. Handoff must occur at epoch 9 for exit at epoch 10.

Used in: C (A3)

---

#### ExitAbruptNoHandoff
```python
def wants_to_exit(self) -> bool:
    return self.current_epoch == 10
```
Used in: D (A3)

---

#### LivelockAcknowledger_AfterLatch
```python
def propose_action(self, epoch: int, obs: Observation) -> ActionRequest:
    if self.livelock_detected and not self.ack_written:
        self.ack_written = True
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{epoch}:0",
            action_type="WRITE",
            declared_scope=["K_LOG"],
            proposed_delta={"K_LOG": f"LLOCK_ACK:{self.id}:{epoch}"},
            authorities_cited=[self.log_allow_id]
        )
    return None
```
Used in: E (A2, A3)

---

#### DissolutionSequence
```python
def propose_action(self, epoch: int, obs: Observation) -> ActionRequest:
    if epoch == self.exit_epoch - 1 or epoch == self.exit_epoch:
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{epoch}:0",
            action_type="WRITE",
            declared_scope=["K_LOG"],
            proposed_delta={"K_LOG": f"DISSOLVE:{self.id}:E{epoch}"},
            authorities_cited=[self.log_allow_id]
        )
    return None

def wants_to_exit(self) -> bool:
    return self.current_epoch == self.exit_epoch
```
Used in: F (all agents, with exit_epochs = {A0:5, A1:6, A2:7, A3:8})

---

#### Coordinator_RegistryLog
```python
def propose_action(self, epoch: int, obs: Observation) -> ActionRequest:
    target = "K_REGISTRY" if epoch % 2 == 0 else "K_LOG"
    return ActionRequest(
        agent_id=self.id,
        action_id=f"{self.id}:{epoch}:0",
        action_type="WRITE",
        declared_scope=[target],
        proposed_delta={target: f"{target}_{epoch}_coord"},
        authorities_cited=[self.get_allow_for(target)]
    )

def wants_to_exit(self) -> bool:
    return self.current_epoch == 8
```
Used in: G (A0)

---

#### SilentWindowObserver_0_11
```python
def propose_action(self, epoch: int, obs: Observation) -> ActionRequest:
    if epoch <= 11:
        return None  # Silent epochs 0-11 (pre-silence + partition window)
    return self.normal_policy_action(epoch)  # Resume at epoch 12+

def compose_message(self) -> Optional[dict]:
    if self.current_epoch <= 11:
        return None
    return self.normal_message()
```
*Design Note*: A2 is silent for epochs 0–11. Epochs 0–5 are "pre-silence" to avoid 3-way livelock with A0/A1. Epochs 6–11 are the actual partition simulation window.

Used in: H (A2)

---

#### InstitutionalLogHeartbeat
```python
def propose_action(self, epoch: int, obs: Observation) -> ActionRequest:
    if epoch == 9:
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{epoch}:0",
            action_type="WRITE",
            declared_scope=["K_LOG"],
            proposed_delta={"K_LOG": f"HEARTBEAT:{self.id}:E{epoch}"},
            authorities_cited=[self.log_allow_id]
        )
    return None
```
Used in: H (A3)

---

#### ReclaimAttempt_NoAuthority
```python
def propose_action(self, epoch: int, obs: Observation) -> ActionRequest:
    if epoch == 4:
        # Attempt to reclaim orphaned K_OPS_A without authority
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{epoch}:0",
            action_type="WRITE",
            declared_scope=["K_OPS_A"],
            proposed_delta={"K_OPS_A": "free"},
            authorities_cited=[]  # No authority!
        )
    return self.normal_action(epoch)
```
Used in: J (A1)

<!-- FROZEN: END STRATEGIES -->

---

## §8 Execution Protocol

### §8.1 Test Sequence

1. Initialize GS Harness with fixed clock and sequence counter.
2. For each condition A–J:
   a. Reinitialize kernel to clean state (empty authority store, clean world state).
   b. Load condition configuration (authority allocation, strategies, parameters).
   c. Inject authority artifacts at epoch 0.
   d. Initialize agents with frozen strategy code.
   e. Execute epoch loop until terminal classification or max epochs.
   f. Log all inputs, outputs, state transitions, messages.
   g. Evaluate metrics and classify terminal state.
   h. Record condition result (PASS/FAIL).
3. Reset between conditions.
4. Aggregate results.

### §8.2 Determinism Controls

<!-- FROZEN: BEGIN DETERMINISM -->
| Control | Value |
|---------|-------|
| Fixed Clock | `1738886400` (2025-02-07 00:00:00 UTC) |
| Sequence Seed | `001` |
| Sequence Format | `GS-<NNNN>` (zero-padded) |
| RNG Seed | N/A (no randomness permitted) |
| Max Epochs | 30 (conditions A–H), 8 (conditions I, J) |
| Livelock Threshold | N = 5 |
| Deadlock Threshold | M = 1 |
| Rolling Window | 10 epochs |

**Replay Rule**: Given identical initial state, authority artifacts, and agent strategies, all outputs must be bit-perfectly replayable. Only `timestamp` and `execution_timestamp` fields may vary.

**Agent Determinism**: Agents must be pure functions of observation history. No RNG, no wall-clock, no external I/O.
<!-- FROZEN: END DETERMINISM -->

### §8.3 Logging Schema

<!-- FROZEN: BEGIN LOG_SCHEMA -->
```json
{
  "condition": "string (A, B, C, D, E, F, G, H, I, J)",
  "timestamp": "ISO-8601",
  "initial_state": "object",
  "authority_artifacts": ["array of authority artifact objects"],
  "agent_strategies": {
    "A0": "string (strategy class name)",
    "A1": "string (strategy class name)",
    "A2": "string (strategy class name)",
    "A3": "string (strategy class name)"
  },
  "communication_enabled": "boolean",
  "max_epochs": "integer",
  "epochs": [
    {
      "epoch": "integer",
      "observations": {"agent_id": "Observation object"},
      "exits": ["array of agent_ids that exited"],
      "silence": ["array of agent_ids in silence mode"],
      "messages": ["array of Message objects"],
      "actions": ["array of ActionRequest objects or null"],
      "pass1_results": {"action_id": "PASS|FAIL"},
      "pass2_results": {"action_id": "PASS|FAIL"},
      "outcomes": {"action_id": "EXECUTED|JOINT_ADMISSIBILITY_FAILURE|ACTION_FAULT|NO_ACTION"},
      "state_after": "object",
      "metrics": {
        "institutional_progress": "boolean",
        "institutional_interference": "boolean"
      }
    }
  ],
  "aggregate_metrics": {
    "epoch_progress_rate_K_INST": "float",
    "refusal_rate": "float",
    "exit_rate": "float",
    "write_overlap_rate_K_INST": "float",
    "orphan_events": "integer",
    "institutional_deadlock_epochs": "integer",
    "livelock_latched": "boolean"
  },
  "terminal_classification": "STATE_DEADLOCK|STATE_LIVELOCK|COLLAPSE|ORPHANING|None",
  "governance_style_label": "string",
  "ix3_fail_tokens": ["array of IX3_FAIL/* tokens"],
  "condition_result": "PASS|FAIL",
  "notes": "string"
}
```
<!-- FROZEN: END LOG_SCHEMA -->

---

## §9 Architectural Partitioning

### §9.1 Three Physically Distinct Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                      GS Harness                                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐  │
│  │   Agents     │──▶│  Interaction │──▶│   World State      │  │
│  │   (4 RSAs)   │   │    Kernel    │   │   (6 keys)         │  │
│  │              │   │              │   │                    │  │
│  └──────────────┘   └──────────────┘   └────────────────────┘  │
│         │                  │                      │             │
│         ▼                  ▼                      ▼             │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐  │
│  │  Strategy    │   │ Admissibility│   │   Epoch            │  │
│  │  Classes     │   │ Evaluator    │   │   Controller       │  │
│  │  (per cond)  │   │ (two-pass)   │   │                    │  │
│  └──────────────┘   └──────────────┘   └────────────────────┘  │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────┐   ┌─────────────┐   ┌────────────────────┐   │
│  │  Governance  │   │   Audit &   │   │    Failure         │   │
│  │  Classifier  │   │   Replay    │   │    Detectors       │   │
│  └──────────────┘   └─────────────┘   └────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### §9.2 Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `agent_model.py` | RSA interface, Observation, ActionRequest, Message (import from IX-2) |
| `world_state.py` | State management, 6-key schema (import from IX-2) |
| `authority_store.py` | Authority artifact storage, capability lookup (import from IX-2) |
| `admissibility.py` | Two-pass evaluation (import from IX-2) |
| `epoch_controller.py` | Epoch loop orchestration (import from IX-2) |
| `deadlock_classifier.py` | Institutional deadlock/livelock detection (extend from IX-2) |
| `governance_classifier.py` | Governance style classification (new) |
| `failure_detectors.py` | FAILURE_FREE_GOVERNANCE, TOOLING_SOVEREIGNTY detection (new) |
| `gs_harness.py` | Test orchestration, condition execution (new) |
| `strategies/` | Strategy class implementations (new) |

### §9.3 Code Layout

```
src/phase_ix/3-GS/
├── docs/
│   ├── spec.md
│   ├── instructions.md
│   ├── questions.md
│   ├── answers.md
│   └── preregistration.md  (this document)
├── src/
│   ├── governance_classifier.py
│   ├── failure_detectors.py
│   ├── gs_harness.py
│   └── strategies/
│       ├── __init__.py
│       ├── contest_policy.py
│       ├── ops_partition.py
│       ├── institutional_steward.py
│       ├── handoff.py
│       ├── livelock_ack.py
│       ├── dissolution.py
│       ├── coordinator.py
│       ├── silent_window.py
│       └── reclaim_attempt.py
├── tests/
│   └── test_gs.py
└── results/
    └── (execution logs)
```

### §9.4 IX-2 Reuse Policy

Import IX-2 kernel modules directly via package imports:
```python
from phase_ix.cud.src.authority_store import AuthorityStore
from phase_ix.cud.src.admissibility import AdmissibilityEvaluator
from phase_ix.cud.src.world_state import WorldState
from phase_ix.cud.src.epoch_controller import EpochController
from phase_ix.cud.src.agent_model import RSA, Observation, ActionRequest, Message
```

If copies are unavoidable, require provenance header with hash pinning.

---

## §10 Scope and Licensing

### §10.1 What IX-3 Tests
- Whether governance reduces to style choices with irreducible failure modes
- Whether different authority allocations produce distinct institutional behaviors
- Whether deadlock, livelock, orphaning, and collapse are correctly classified
- Whether governance survives only by owning failures honestly
- Whether adversarial tooling sovereignty is detected

### §10.2 What IX-3 Does Not Test
- Value correctness, moral truth, preference learning
- Optimization, efficiency, fairness
- Governance legitimacy or desirability
- Coalition dynamics (reserved for IX-5)
- Safety or alignment
- Recovery or resilience

### §10.3 Relationship to IX-2
- IX-3 reuses IX-2's kernel modules unchanged
- IX-3 extends to 4 agents and 6 state keys
- IX-3 introduces governance style classification
- IX-3 adds institutional-scoped failure detection
- IX-3 tests institutional postures, not coordination mechanics

---

## §11 Preregistration Commitment

### §11.1 Frozen Sections

The following sections are immutable after hash commitment:
- §2.1 RSA Interface (`RSA_INTERFACE`)
- §2.2 Action Request Schema (`ACTION_SCHEMA`)
- §2.3 Authority Artifact Schema (`AUTHORITY_SCHEMA`)
- §2.4 World State Schema (`STATE_SCHEMA`)
- §2.5 Canonical Serialization Rules (`SERIALIZATION_RULES`)
- §2.6 Admissibility Rules (`ADMISSIBILITY_RULES`)
- §2.7 Deadlock and Livelock Definitions (`DEADLOCK_RULES`)
- §2.8 Epoch Schedule (`EPOCH_SCHEDULE`)
- §2.9 Exit Semantics (`EXIT_RULES`)
- §2.10 Output Tokens (`OUTPUT_TOKENS`)
- §2.11 Metric Definitions (`METRICS`)
- §2.12 FAILURE_FREE_GOVERNANCE Definition (`FAILURE_FREE`)
- §3.1 Agent Identity Set (`AGENTS`)
- §3.2 Institution Definition (`INSTITUTION`)
- §4.1 Condition Definitions (`CONDITIONS`)
- §5 Governance Style Classification (`CLASSIFICATION`)
- §6.1 Per-Condition PASS Predicates (`PASS_PREDICATES`)
- §7.1 Canonical Strategy Classes (`STRATEGIES`)
- §8.2 Determinism Controls (`DETERMINISM`)
- §8.3 Logging Schema (`LOG_SCHEMA`)

### §11.2 Hash Commitment

**Hash Scope**: SHA-256 of concatenated frozen sections only (content between `<!-- FROZEN: BEGIN -->` and `<!-- FROZEN: END -->` markers).

**Verification Command**:
```bash
grep -Pzo '(?s)<!-- FROZEN: BEGIN.*?<!-- FROZEN: END[^>]*>' preregistration.md | sha256sum
```

**Preregistration Hash (v0.2)**: `191d7ba4d88d947118c8f2d5f6fd3d413670df5068e37297419076b1551cfff6`
**Prior Hash (v0.1)**: `19b53a61a67b5bb7dd73b8eaa8e1a857fe4ca46a7b40188b1a42944a7c1e53c5`
**Commitment Timestamp**: `2026-02-08T00:00:00Z`
**Commit ID**: (pending)

---

## §12 Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **RSA** | Reflective Sovereign Agent — deterministic strategy module |
| **K_INST** | Institutional keys: K_POLICY, K_TREASURY, K_REGISTRY, K_LOG |
| **K_OPS** | Operational keys: K_OPS_A, K_OPS_B |
| **ALLOW** | Holder-bound capability — must be cited by holder to grant admissibility |
| **DENY** | Global veto — blocks any agent regardless of holder |
| **Institutional Deadlock** | No admissible institutional actions exist (strategy-aware) |
| **Institutional Livelock** | Institutional actions collide for N=5 epochs (latched) |
| **Orphaning** | Institutional key becomes inaccessible when sole ALLOW holder exits |
| **Collapse** | All agents exit; system halts; state preserved |
| **Governance Style** | Descriptive classification of institutional behavior pattern |
| **FAILURE_FREE_GOVERNANCE** | Falsification signal: governance with zero friction |

### Appendix B: Authority Allocation Summary

| Condition | A0 ALLOW | A1 ALLOW | A2 ALLOW | A3 ALLOW | DENYs |
|-----------|----------|----------|----------|----------|-------|
| A | POLICY, LOG | POLICY, LOG | POLICY, LOG | POLICY, LOG | A0/A1: TREASURY; A2/A3: REGISTRY |
| B | OPS_A | OPS_B | TREASURY, LOG | POLICY, REGISTRY, LOG | None |
| C | OPS_A | OPS_A, REGISTRY, LOG, POLICY | OPS_B | REGISTRY, LOG, POLICY | None |
| D | OPS_B | POLICY | REGISTRY, LOG | OPS_A | None |
| E | POLICY | POLICY | LOG | LOG | None |
| F | LOG | LOG | LOG | LOG | None |
| G | REGISTRY, LOG | OPS_A | OPS_B | TREASURY | None |
| H | POLICY | POLICY | POLICY | LOG | None |

### Appendix C: Exit and Silence Schedules

| Condition | Exit Schedule | Silence Schedule |
|-----------|---------------|------------------|
| A | None | None |
| B | None | None |
| C | A3 handoff epoch 9, exits epoch 10 | None |
| D | A3 exits epoch 10 (no handoff) | None |
| E | None | None |
| F | A0:5, A1:6, A2:7, A3:8 | None |
| G | A0 exits epoch 8 | None |
| H | None | A2 silent epochs 0–11 |
| I | None | None |
| J | A3 exits epoch 3 (ORPHANING nonterminal) | None |

### Appendix D: Preregistration Checklist

| Item | Section |
|------|---------|
| RSA interface defined | §2.1 |
| Action request schema | §2.2 |
| Authority artifact schema | §2.3 |
| World state schema (6 keys) | §2.4 |
| Canonical serialization | §2.5 |
| Two-pass admissibility | §2.6 |
| Deadlock/livelock definitions (institutional scope) | §2.7 |
| Epoch schedule | §2.8 |
| Exit semantics | §2.9 |
| Output tokens | §2.10 |
| Metric definitions | §2.11 |
| FAILURE_FREE_GOVERNANCE definition | §2.12 |
| Agent identity set (4 agents) | §3.1 |
| Institution definition | §3.2 |
| All conditions defined (A–J) | §4.1 |
| Governance style classification | §5 |
| Per-condition PASS predicates | §6.1 |
| Strategy classes frozen | §7.1 |
| Determinism controls | §8.2 |
| Logging schema | §8.3 |
| Code layout | §9.3 |
| IX-2 reuse policy | §9.4 |

---

## Change Log v0.1 → v0.2

**Date**: 2026-02-08
**Reason**: Consistency audit identified 5 deviations from frozen sections and 2 conditions whose core stressors were never exercised. All deviations traced to internal inconsistencies in v0.1 design.

### Amendment 1: §2.7 Deadlock Definition
- **v0.1**: "No jointly admissible action set is produced by agents that would change any key in K_INST"
- **v0.2**: "No Pass-2-admissible institutional action executes, AND no Pass-1-admissible institutional action exists in the submitted action set, AND at least one institutional action was submitted"
- **Rationale**: Aligns definition with per-action Pass-1/Pass-2 evaluation semantics implemented in IX-2 kernel.

### Amendment 2: §4.1 Condition C Exit Schedule
- **v0.1**: "Epoch 10: A3 writes handoff record to K_REGISTRY and K_LOG, then exits"
- **v0.2**: "Epoch 9: A3 writes handoff record; Epoch 10: A3 exits"
- **Rationale**: §2.8 epoch schedule checks `wants_to_exit()` before `propose_action()`. Writing and exiting in the same epoch is structurally impossible.

### Amendment 3: §4.1 Condition E Authority Allocation
- **v0.1**: A2 DENY K_POLICY, A3 DENY K_POLICY
- **v0.2**: No DENY entries (removed)
- **Rationale**: DENY is a global veto that would block A0/A1 as well, producing instant STATE_DEADLOCK instead of intended STATE_LIVELOCK. A2/A3 lack K_POLICY ALLOW anyway.

### Amendment 4: §4.1 Condition F Authority Allocation
- **v0.1**: A0 → K_LOG, K_POLICY
- **v0.2**: A0 → K_LOG only
- **Rationale**: If A0 held K_POLICY, its exit at epoch 5 would orphan K_POLICY, triggering ORPHANING terminal before remaining agents could exit to produce COLLAPSE.

### Amendment 5: §4.1 Condition H Silence Schedule
- **v0.1**: "Epochs 6–11: A2 returns None"
- **v0.2**: "Epochs 0–11: A2 returns None (pre-silence 0–5, partition window 6–11)"
- **Rationale**: Without pre-silence passivity, A0/A1/A2 all contest K_POLICY from epoch 0, producing 3-way livelock at epoch 4—before the silence window at epochs 6–11 is reached.

### Amendment 6: §4.1 Condition J Terminal Rule
- **v0.1**: (no special rule)
- **v0.2**: "ORPHANING is nonterminal for Condition J"
- **Rationale**: A3 exits epoch 3 → ORPHANING detected → run terminates before epoch 4. Reclamation attempt (the core stressor) never executes. Nonterminal rule allows run to reach epoch 4.

### Strategy Pseudocode Updates
- `HandoffRecordThenExit`: `epoch == 10` → `epoch == 9`; `wants_to_exit()` condition simplified
- `SilentWindowObserver_6_11` → `SilentWindowObserver_0_11`: silent epochs 0–11

### Frozen Hash
- **v0.1 Hash**: `19b53a61a67b5bb7dd73b8eaa8e1a857fe4ca46a7b40188b1a42944a7c1e53c5`
- **v0.2 Hash**: `191d7ba4d88d947118c8f2d5f6fd3d413670df5068e37297419076b1551cfff6`

---

**END OF PREREGISTRATION**
