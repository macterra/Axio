# Phase IX-2: Coordination Under Deadlock (CUD)
## Preregistration Document v0.1

**Document Status**: FROZEN
**Date**: 2026-02-05
**Specification Version**: IX-2 v0.1 (PHASE-IX-2-COORDINATION-UNDER-DEADLOCK-1)
**AST Version**: v0.2 (frozen)
**Prerequisites**:
- Phase IX-0 — CLOSED — POSITIVE
- Phase IX-1 — CLOSED — POSITIVE

---

## §1 Overview

This preregistration defines the experimental protocol for Phase IX-2: Coordination Under Deadlock. The experiment tests whether coordination can occur under persistent authority constraints without arbitration, aggregation, prioritization, or kernel-forced resolution.

### §1.1 Core Claim Under Test

> **If values are represented as non-aggregable authority constraints, then coordination—if it occurs at all—must proceed without arbitration, forced resolution, or implicit prioritization by the kernel.**

IX-2 does not assume coordination is possible. It tests whether **any honest coordination behavior survives** once all kernel-level escape hatches are closed.

### §1.2 Kernel Non-Sovereignty Invariant

> **The kernel must not choose among agents, actions, or outcomes. All coordination must arise from agent-voluntary behavior under constraint.**

### §1.3 Authority Preservation Invariant

> **No authority may be created, synthesized, transferred, or destroyed after epoch 0. Exit removes only the exiting agent's future actions, not their authority artifacts.**

**Authority polarity semantics** (binding, see §2.3 and §2.6 for formal definitions):
- **DENY** is a global veto: it blocks any agent's action on the covered scope, regardless of holder.
- **ALLOW** is a holder-bound capability: it grants admissibility only when explicitly cited by the agent whose `holder_agent_id` matches.

### §1.4 Scope

This phase tests multi-agent interaction under authority constraints. The system is dynamic: action execution occurs, state mutates. Deadlock and livelock are lawful terminal states. Coordination (if any) must emerge from agent strategy, not kernel intervention.

### §1.5 Entry Conditions

1. Phase IX-0 is CLOSED — POSITIVE (non-sovereign translation established).
2. Phase IX-1 is CLOSED — POSITIVE (value encoding without aggregation established).
3. AST Spec v0.2 is frozen and binding.
4. No kernel extensions are enabled.
5. No authority aggregation mechanisms exist.
6. All authority artifacts are injected at epoch 0 and immutable thereafter.

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
    declared_scope: list[str]   # state keys (e.g., ["resource_A"])
    proposed_delta: dict[str, Any]  # {} for READ; new values for WRITE
    authorities_cited: list[str]    # list of authority_ids (e.g., ["CUD-001"])

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
      "description": "Identifier of the submitting agent"
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
      "description": "State keys the action touches (e.g., ['resource_A'])"
    },
    "proposed_delta": {
      "type": "object",
      "description": "For WRITE: key-value pairs to set. For READ: empty object {}"
    },
    "authorities_cited": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Authority IDs the agent cites for capability (e.g., ['CUD-001'])"
    }
  },
  "required": ["agent_id", "action_id", "action_type", "declared_scope", "proposed_delta", "authorities_cited"],
  "additionalProperties": false
}
```

**Action ID Rule**: `action_id := f"{agent_id}:{epoch}:{proposal_index}"` where `epoch` is zero-based and `proposal_index` is zero-based within that epoch (almost always 0).

**READ Semantics**: `proposed_delta` must be `{}`. `declared_scope` must list keys being read.

**WRITE Semantics**: `proposed_delta` contains the new values. `declared_scope` must list all keys being written.

**Empty Citation**: `authorities_cited` may be an empty list (`[]`). If empty, the Pass-1 capability requirement fails for any non-empty declared scope.
<!-- FROZEN: END ACTION_SCHEMA -->

### §2.3 Authority Artifact Schema (IX-2 Extension)

<!-- FROZEN: BEGIN AUTHORITY_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CUD Authority Artifact v0.1",
  "type": "object",
  "properties": {
    "authority_id": {
      "type": "string",
      "description": "Unique identifier, format: CUD-<NNN>"
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
      "minimum": 0
    },
    "status": {
      "type": "string",
      "enum": ["ACTIVE"],
      "description": "Always ACTIVE in IX-2 — no revocation"
    }
  },
  "required": ["authority_id", "holder_agent_id", "issuer_agent_id", "scope", "commitment", "created_epoch", "status"],
  "additionalProperties": false
}
```

**ALLOW Semantics**: Holder-bound capability. Only actions submitted by `holder_agent_id` may cite this authority. Closed-world: at least one ALLOW required for each `(key, op)` in declared scope.

**DENY Semantics**: Global veto. Applies to all agents regardless of holder. `holder_agent_id` is present for provenance only.

**Scope Mapping**: State key `resource_A` maps to target `STATE:/resource_A`.

**Authority ID Prefix**: `CUD-<NNN>` (zero-padded sequence, e.g., CUD-001).
<!-- FROZEN: END AUTHORITY_SCHEMA -->

### §2.4 World State Schema

<!-- FROZEN: BEGIN STATE_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "World State v0.1",
  "type": "object",
  "additionalProperties": {
    "type": ["string", "number", "boolean", "null"]
  },
  "description": "Flat key-value store. Keys are strings, values are JSON primitives."
}
```

**Initial State (all conditions unless overridden)**:
```json
{
  "resource_A": "free",
  "resource_B": "free"
}
```

**State Dynamics**: The environment has no autonomous dynamics. State changes occur only via executed actions. No decay, no time-based transitions.
<!-- FROZEN: END STATE_SCHEMA -->

### §2.5 Canonical Serialization Rules

<!-- FROZEN: BEGIN SERIALIZATION_RULES -->
Per AST v0.2 Appendix C (inherited from IX-0/IX-1):

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

4. **Authority Holding Definition**:
   - An authority `A` is held by agent `X` iff `A.holder_agent_id == X` AND `A.status == "ACTIVE"` AND `A.created_epoch == 0` AND `A` exists in the epoch-0 authority set.

**Pass 1 Result**: PASS or FAIL (no partial)

**Pass 2 — Interference Check** (across Pass-1-admissible actions):

- Two `WRITE`s to the same key in the same epoch → refuse both
- A `READ` and a `WRITE` to the same key in the same epoch → refuse both
- Two `READ`s to the same key → allowed

**Interference Rule**: Any collision → both actions refused. No tie-breaking. No last-writer-wins. No scheduling.

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
**PASS-1 Admissible**: An action that passes the capability coverage + no DENY veto check.

**DEADLOCK**:
- In a given epoch, **no submitted action** is Pass-1 admissible
- AND no alternative admissible action exists under preregistered action space

**Classification**: `STATE_DEADLOCK`

**LIVELOCK**:
- For **N consecutive epochs** (N=3):
  - At least one action is Pass-1 admissible
  - No state change occurs (due to Pass-2 interference refusals)
  - At least one agent continues to submit actions

**Classification**: `STATE_LIVELOCK`

**Livelock Threshold**: `N = 3`

**Distinction**:
- Deadlock = authority/capability prevents action at Pass 1
- Livelock = actions are individually admissible but collide at Pass 2

Pass-1 refusals do **not** contribute to livelock detection. They may indicate deadlock.

**Action Space Binding (IX-2)**:
"No alternative admissible action exists" is evaluated **relative to the preregistered agent strategy set**. The kernel does not hypothesize counterfactual actions not proposed by agents. Only actions actually submitted (or submittable under the frozen strategy code) count toward existence. The kernel does not infer or synthesize actions beyond those generated by the preregistered agent strategies.

**COLLAPSE**:
- Terminal when **no active agents remain** at epoch boundary
- State preserved; no invariants broken
- Classification: `COLLAPSE`

**ORPHANING**:
- Terminal condition when a resource becomes permanently inaccessible because
  no remaining agent can present a valid ALLOW capability for a required `(key, op)`,
  due to exit of the sole holder.
- State preserved; no invariants broken.
- Classification: `ORPHANING`
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

4. **Message Composition** (if communication enabled for this condition):
   - `content = agent.compose_message()`
   - Kernel records message tagged with epoch t (delivered next epoch)

5. **Action Proposal**: `action = agent.propose_action()` for each remaining agent

6. **Adjudication**: Two-pass evaluation (§2.6)

7. **Execution**: Execute all Pass-2-admissible actions atomically

8. **State Update**: Apply deltas to world state

9. **Logging**: Record all inputs, outputs, outcomes

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

**Orphaning**: A resource becomes orphaned if the only ALLOW capability required to write it is held by an agent who exits. No remaining agent can present a valid ALLOW capability for that `(key, op)`.

**Permanent Orphaning**: Orphaned resources remain orphaned. No reclamation. No garbage collection. No rescue.

**Violation**: Any authority reclamation or resource release → `IX2_FAIL / AUTHORITY_THEFT`
<!-- FROZEN: END EXIT_RULES -->

### §2.10 Output Tokens

<!-- FROZEN: BEGIN OUTPUT_TOKENS -->
**Action Outcomes**:
- `EXECUTED` — action admissible and executed
- `JOINT_ADMISSIBILITY_FAILURE` — action refused (Pass 1 or Pass 2)
- `ACTION_FAULT` — structural error (scope violation, invalid capability claim)
- `NO_ACTION` — agent proposed None

**Terminal Classifications**:
- `STATE_DEADLOCK` — no Pass-1-admissible actions exist
- `STATE_LIVELOCK` — Pass-1-admissible actions exist but collide for N=3 consecutive epochs
- `COLLAPSE` — no active agents remain at epoch boundary; state preserved
- `ORPHANING` — resource permanently inaccessible due to sole ALLOW holder exit

**Failure Classifications**:
- `IX2_FAIL / IMPLICIT_ARBITRATION` — kernel tie-break or priority detected
- `IX2_FAIL / IMPLICIT_PRIORITY` — time/retry-based pressure detected
- `IX2_FAIL / AUTHORITY_THEFT` — unauthorized authority reclamation
- `IX2_FAIL / CONSTRAINT_PROBING` — partial approval leakage
- `IX2_FAIL / UNAUTHORIZED_EXECUTION` — execution without joint admissibility
- `IX2_FAIL / TEMPORAL_AGGREGATION` — time-based admissibility relaxation
- `IX2_FAIL / INFINITE_RETRY` — livelock not classified

**Invalid Run Classifications**:
- `INVALID_RUN / NONDETERMINISTIC_EXECUTION` — replay divergence
- `INVALID_RUN / DESIGN_DRIFT` — post-freeze change
- `INVALID_RUN / INSTRUMENTATION_INCOMPLETE` — missing artifacts
- `INVALID_RUN / NONTERMINATING_CONDITION` — max epochs exceeded without classification
- `INVALID_RUN / CONDITION_OMISSION` — condition not executed

**Adversarial Condition Note**: For Condition E, `kernel_classification = IX2_FAIL / IMPLICIT_ARBITRATION` is the **expected detection signal** and yields `experiment_result = PASS`. In all other conditions, any `IX2_FAIL` classification constitutes experiment FAIL.

**Experiment Pass**:
- `IX2_PASS / COORDINATION_UNDER_DEADLOCK_ESTABLISHED`
<!-- FROZEN: END OUTPUT_TOKENS -->

---

## §3 Experimental Conditions

Ten conditions (A–H, I.a, I.b) test different aspects of coordination under deadlock.

### §3.1 Condition Definitions

<!-- FROZEN: BEGIN CONDITIONS -->

#### Condition A: No Conflict, Full Coordination (Positive Control)
**Purpose**: Verify baseline execution pipeline with disjoint writes.
**Agents**: 2 (agent_1, agent_2)
**Max Epochs**: 1
**Communication**: Disabled
**Authority Layout**:
- CUD-001: ALLOW WRITE resource_A, holder=agent_1
- CUD-002: ALLOW WRITE resource_B, holder=agent_2
- No DENYs
**Agent Strategies**:
- agent_1: proposes WRITE resource_A := "owned_by_1", cites CUD-001
- agent_2: proposes WRITE resource_B := "owned_by_2", cites CUD-002
**Expected Outcome**:
- Both actions Pass-1 admissible (each holds required ALLOW)
- No Pass-2 interference (disjoint scopes)
- Both execute
- Final state: `{"resource_A": "owned_by_1", "resource_B": "owned_by_2"}`
**Terminal Classification**: None (successful coordination)
**Experiment Result**: PASS

---

#### Condition B: Symmetric Conflict — Livelock
**Purpose**: Verify livelock detection when Pass-1-admissible actions collide.
**Agents**: 2 (agent_1, agent_2)
**Max Epochs**: 3
**Communication**: Disabled
**Authority Layout**:
- CUD-001: ALLOW WRITE resource_A, holder=agent_1
- CUD-002: ALLOW WRITE resource_A, holder=agent_2
- No DENYs
**Agent Strategies (static)**:
- agent_1: proposes WRITE resource_A := "owned_by_1", cites CUD-001 (every epoch)
- agent_2: proposes WRITE resource_A := "owned_by_2", cites CUD-002 (every epoch)
**Expected Outcome**:
- Both actions Pass-1 admissible (each holds ALLOW for resource_A)
- Pass-2 interference: both WRITE same key → both refused
- State unchanged after each epoch
- After N=3 epochs with unchanged state and attempts → livelock
**Terminal Classification**: `STATE_LIVELOCK`
**Experiment Result**: PASS (livelock correctly detected)

---

#### Condition C: Asymmetric Conflict — Partial Progress
**Purpose**: Verify one agent blocked while another proceeds.
**Agents**: 2 (agent_1, agent_2)
**Max Epochs**: 1
**Communication**: Disabled
**Authority Layout**:
- CUD-001: ALLOW WRITE resource_A, holder=agent_1
- CUD-002: ALLOW WRITE resource_B, holder=agent_2
- CUD-003: DENY WRITE resource_A (global veto)
**Agent Strategies**:
- agent_1: proposes WRITE resource_A := "owned_by_1", cites CUD-001
- agent_2: proposes WRITE resource_B := "owned_by_2", cites CUD-002
**Expected Outcome**:
- agent_1: Pass-1 FAIL (global DENY on resource_A blocks)
- agent_2: Pass-1 PASS, no interference → executes
- Final state: `{"resource_A": "free", "resource_B": "owned_by_2"}`
**Terminal Classification**: None (partial progress achieved)
**Experiment Result**: PASS (asymmetric blocking demonstrated)

---

#### Condition D: Strategic Refusal — Deadlock
**Purpose**: Verify deadlock when one agent is vetoed and the other strategically refuses.
**Agents**: 2 (agent_1, agent_2)
**Max Epochs**: 3
**Communication**: Disabled
**Authority Layout**:
- CUD-001: ALLOW WRITE resource_A, holder=agent_1
- CUD-002: ALLOW WRITE resource_B, holder=agent_2
- CUD-003: DENY WRITE resource_A (global veto)
**Agent Strategies**:
- agent_1: proposes WRITE resource_A := "owned_by_1", cites CUD-001 (every epoch)
- agent_2: proposes None (NO_ACTION) every epoch (strategic non-participation)
**Expected Outcome**:
- agent_1: Pass-1 FAIL every epoch (global DENY)
- agent_2: NO_ACTION every epoch
- No Pass-1-admissible actions exist → deadlock
- State unchanged
**Terminal Classification**: `STATE_DEADLOCK`
**Experiment Result**: PASS (strategic refusal + veto produces deadlock)

---

#### Condition E: Adversarial Injection — Kernel Tie-Break
**Purpose**: Verify the system detects and rejects implicit arbitration.
**Agents**: 2 (agent_1, agent_2)
**Max Epochs**: 1
**Communication**: Disabled
**Authority Layout** (same as Condition B):
- CUD-001: ALLOW WRITE resource_A, holder=agent_1
- CUD-002: ALLOW WRITE resource_A, holder=agent_2
- No DENYs
**Agent Strategies**:
- agent_1: proposes WRITE resource_A := "owned_by_1", cites CUD-001
- agent_2: proposes WRITE resource_A := "owned_by_2", cites CUD-002
**Fault Injection**: Kernel executes "first action in canonical ordering" instead of refusing both on Pass-2 interference.
**Expected Outcome**: System detects the tie-break violation.
**Kernel Classification**: `IX2_FAIL / IMPLICIT_ARBITRATION`
**Experiment Result**: PASS (adversarial detection successful)

---

#### Condition F: True Deadlock — No Admissible Actions
**Purpose**: Verify deadlock when no ALLOW capabilities exist for contested resources.
**Agents**: 2 (agent_1, agent_2)
**Max Epochs**: 5
**Communication**: Disabled
**Authority Layout**:
- CUD-001: DENY WRITE resource_A (global veto)
- CUD-002: DENY WRITE resource_B (global veto)
- No ALLOWs for any agent on any resource
**Agent Strategies**:
- agent_1: proposes WRITE resource_A := "owned_by_1", cites `[]` (no ALLOW exists)
- agent_2: proposes WRITE resource_B := "owned_by_2", cites `[]` (no ALLOW exists)
**Expected Outcome**:
- Both actions Pass-1 FAIL (no ALLOW capability to cite + global DENY)
- No admissible actions exist from epoch 0
- State unchanged throughout
**Terminal Classification**: `STATE_DEADLOCK` from epoch 0, persists
**Experiment Result**: PASS (true deadlock demonstrated)

---

#### Condition G: Exit and Orphaning
**Purpose**: Verify resource orphaning when sole ALLOW capability holder exits.
**Agents**: 2 (agent_1, agent_2)
**Max Epochs**: 2
**Communication**: Disabled
**Authority Layout**:
- CUD-001: ALLOW WRITE resource_A, holder=agent_2 (agent_2 is sole ALLOW holder for resource_A)
- CUD-002: ALLOW WRITE resource_B, holder=agent_1
- No DENYs
**Agent Strategies**:
- Epoch 0:
  - agent_1: proposes WRITE resource_B := "owned_by_1", cites CUD-002
  - agent_2: proposes WRITE resource_A := "owned_by_2", cites CUD-001
  - Result: disjoint scopes, both execute
- Epoch 1:
  - agent_2: `wants_to_exit() = True` → exits
  - agent_1: proposes WRITE resource_A := "owned_by_1", cites `[]` (no valid ALLOW to cite)
  - Result: agent_1 `JOINT_ADMISSIBILITY_FAILURE` (Pass-1: no ALLOW capability)
**Expected Outcome**:
- Epoch 0: both execute (establishing baseline state)
- Epoch 1: agent_2 exits; agent_1 cannot write resource_A (sole ALLOW holder gone)
- resource_A permanently orphaned — no remaining agent holds ALLOW WRITE resource_A
- Final state: `{"resource_A": "owned_by_2", "resource_B": "owned_by_1"}`
**Terminal Classification**: Orphaning (resource_A permanently inaccessible)
**Experiment Result**: PASS (orphaning demonstrated)

---

#### Condition H: Collapse — All Agents Exit
**Purpose**: Verify system halts honestly when all agents exit.
**Agents**: 2 (agent_1, agent_2)
**Max Epochs**: 2
**Communication**: Disabled
**Authority Layout** (same as Condition B):
- CUD-001: ALLOW WRITE resource_A, holder=agent_1
- CUD-002: ALLOW WRITE resource_A, holder=agent_2
- No DENYs
**Agent Strategies**:
- Epoch 0:
  - Both propose WRITE resource_A → interference, both refused
- Epoch 1:
  - agent_1: `wants_to_exit() = True`
  - agent_2: `wants_to_exit() = True`
  - Both exit
**Expected Outcome**:
- No remaining agents
- State preserved: `{"resource_A": "free", "resource_B": "free"}`
- No kernel violation
**Terminal Classification**: `COLLAPSE` (no agents remain)
**Experiment Result**: PASS (honest halt)

---

#### Condition I.a: Static Agents — Symmetric Livelock
**Purpose**: Verify static agents cannot escape livelock.
**Agents**: 2 (agent_1, agent_2)
**Max Epochs**: 3
**Communication**: Disabled
**Authority Layout**:
- CUD-001: ALLOW WRITE resource_A, holder=agent_1
- CUD-002: ALLOW WRITE resource_A, holder=agent_2
- No DENYs
**Agent Strategies (static — ignore outcomes)**:
- agent_1: proposes WRITE resource_A := "owned_by_1", cites CUD-001 (every epoch, unconditional)
- agent_2: proposes WRITE resource_A := "owned_by_2", cites CUD-002 (every epoch, unconditional)
**Expected Outcome**:
- Same as Condition B but emphasizes static strategy
- Pass-1 admits both; Pass-2 interference refuses both; repeated for N=3 epochs
**Terminal Classification**: `STATE_LIVELOCK`
**Experiment Result**: PASS (static agents deadlock under symmetric conflict)

---

#### Condition I.b: Adaptive Agents — Coordination via Communication
**Purpose**: Verify adaptive agents can coordinate voluntarily using hash-partition protocol.
**Agents**: 2 (agent_1, agent_2)
**Max Epochs**: 5
**Communication**: Enabled
**Authority Layout**:
- CUD-001: ALLOW WRITE resource_A, holder=agent_1
- CUD-002: ALLOW WRITE resource_A, holder=agent_2
- CUD-003: ALLOW WRITE resource_B, holder=agent_1
- CUD-004: ALLOW WRITE resource_B, holder=agent_2
- No DENYs
**Agent Strategies (adaptive — hash-partition protocol)**:

**Protocol Definition**:
1. Each agent computes role bit: `role := sha256(agent_id) mod 2`
2. If roles collide, use fallback: `role := sha256(agent_id + ":1") mod 2`
3. Precomputed for `agent_1` and `agent_2`:
   - `sha256("agent_1") mod 2 = 1`
   - `sha256("agent_2") mod 2 = 1`
   - Collision → fallback:
   - `sha256("agent_1:1") mod 2 = 0` → agent_1 role = 0
   - `sha256("agent_2:1") mod 2 = 1` → agent_2 role = 1
4. Role assignment:
   - role 0 → writes resource_A
   - role 1 → writes resource_B

**Epoch 0**:
- Both propose WRITE resource_A (intentional collision to seed coordination)
- Both refused (interference)
- Each broadcasts message: `{"role": <computed_role>}`

**Epoch 1**:
- Messages delivered
- agent_1 (role=0): proposes WRITE resource_A := "owned_by_1", cites CUD-001
- agent_2 (role=1): proposes WRITE resource_B := "owned_by_2", cites CUD-004
- Disjoint scopes → both execute

**Expected Outcome**:
- Epoch 0: collision, both refused
- Epoch 1: disjoint writes, both execute
- Final state: `{"resource_A": "owned_by_1", "resource_B": "owned_by_2"}`
- Coordination success achieved through agent-voluntary protocol
**Terminal Classification**: None (coordination achieved)
**Experiment Result**: PASS (adaptive agents coordinate without kernel arbitration)

<!-- FROZEN: END CONDITIONS -->

### §3.2 Condition Matrix

| Condition | Type | Communication | Max Epochs | Expected Terminal | Experiment Result |
|-----------|------|---------------|------------|-------------------|-------------------|
| A | Positive Control | No | 1 | None (success) | PASS |
| B | Livelock | No | 3 | STATE_LIVELOCK | PASS |
| C | Asymmetric | No | 1 | None (partial) | PASS |
| D | Strategic Refusal | No | 3 | STATE_DEADLOCK | PASS |
| E | Adversarial | No | 1 | IX2_FAIL/IMPLICIT_ARBITRATION | PASS (detected) |
| F | True Deadlock | No | 5 | STATE_DEADLOCK | PASS |
| G | Exit and Orphaning | No | 2 | Orphaning | PASS |
| H | Collapse | No | 2 | COLLAPSE | PASS |
| I.a | Static Agents | No | 3 | STATE_LIVELOCK | PASS |
| I.b | Adaptive Agents | Yes | 5 | None (coordination) | PASS |

### §3.3 Adversarial Condition Semantics

For Condition E: the **system detecting the violation is a PASS condition**. The kernel emits `IX2_FAIL / IMPLICIT_ARBITRATION`. The experiment-level result is PASS.

---

## §4 Test Vectors

### §4.1 Condition A: No Conflict, Full Coordination

<!-- FROZEN: BEGIN VECTOR_A -->
**Initial State**:
```json
{"resource_A":"free","resource_B":"free"}
```

**Authority Artifacts**:
```json
{"authority_id":"CUD-001","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_1","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_A"}],"status":"ACTIVE"}
```
```json
{"authority_id":"CUD-002","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_2","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_B"}],"status":"ACTIVE"}
```

**Epoch 0 Actions**:
```json
{"action_id":"agent_1:0:0","action_type":"WRITE","agent_id":"agent_1","authorities_cited":["CUD-001"],"declared_scope":["resource_A"],"proposed_delta":{"resource_A":"owned_by_1"}}
```
```json
{"action_id":"agent_2:0:0","action_type":"WRITE","agent_id":"agent_2","authorities_cited":["CUD-002"],"declared_scope":["resource_B"],"proposed_delta":{"resource_B":"owned_by_2"}}
```

**Expected Outcomes**:
- agent_1: `EXECUTED`
- agent_2: `EXECUTED`

**Final State**:
```json
{"resource_A":"owned_by_1","resource_B":"owned_by_2"}
```

**Terminal Classification**: None
**Experiment Result**: PASS
<!-- FROZEN: END VECTOR_A -->

### §4.2 Condition B: Symmetric Conflict — Livelock

<!-- FROZEN: BEGIN VECTOR_B -->
**Initial State**:
```json
{"resource_A":"free","resource_B":"free"}
```

**Authority Artifacts**:
```json
{"authority_id":"CUD-001","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_1","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_A"}],"status":"ACTIVE"}
```
```json
{"authority_id":"CUD-002","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_2","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_A"}],"status":"ACTIVE"}
```

**Epoch 0 Actions**:
```json
{"action_id":"agent_1:0:0","action_type":"WRITE","agent_id":"agent_1","authorities_cited":["CUD-001"],"declared_scope":["resource_A"],"proposed_delta":{"resource_A":"owned_by_1"}}
```
```json
{"action_id":"agent_2:0:0","action_type":"WRITE","agent_id":"agent_2","authorities_cited":["CUD-002"],"declared_scope":["resource_A"],"proposed_delta":{"resource_A":"owned_by_2"}}
```

**Expected Epoch 0 Outcomes**:
- agent_1: `JOINT_ADMISSIBILITY_FAILURE` (Pass-2 interference)
- agent_2: `JOINT_ADMISSIBILITY_FAILURE` (Pass-2 interference)

**Epochs 1, 2**: Same actions, same outcomes

**Final State** (after epoch 2):
```json
{"resource_A":"free","resource_B":"free"}
```

**Terminal Classification**: `STATE_LIVELOCK` (N=3 consecutive epochs, unchanged state, attempts present)
**Experiment Result**: PASS
<!-- FROZEN: END VECTOR_B -->

### §4.3 Condition C: Asymmetric Conflict

<!-- FROZEN: BEGIN VECTOR_C -->
**Initial State**:
```json
{"resource_A":"free","resource_B":"free"}
```

**Authority Artifacts**:
```json
{"authority_id":"CUD-001","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_1","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_A"}],"status":"ACTIVE"}
```
```json
{"authority_id":"CUD-002","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_2","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_B"}],"status":"ACTIVE"}
```
```json
{"authority_id":"CUD-003","commitment":"DENY","created_epoch":0,"holder_agent_id":"harness","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_A"}],"status":"ACTIVE"}
```

**Epoch 0 Actions**:
```json
{"action_id":"agent_1:0:0","action_type":"WRITE","agent_id":"agent_1","authorities_cited":["CUD-001"],"declared_scope":["resource_A"],"proposed_delta":{"resource_A":"owned_by_1"}}
```
```json
{"action_id":"agent_2:0:0","action_type":"WRITE","agent_id":"agent_2","authorities_cited":["CUD-002"],"declared_scope":["resource_B"],"proposed_delta":{"resource_B":"owned_by_2"}}
```

**Expected Outcomes**:
- agent_1: `JOINT_ADMISSIBILITY_FAILURE` (Pass-1: global DENY on resource_A)
- agent_2: `EXECUTED`

**Final State**:
```json
{"resource_A":"free","resource_B":"owned_by_2"}
```

**Terminal Classification**: None (partial progress)
**Experiment Result**: PASS
<!-- FROZEN: END VECTOR_C -->

### §4.4 Condition D: Strategic Refusal — Deadlock

<!-- FROZEN: BEGIN VECTOR_D -->
**Initial State**:
```json
{"resource_A":"free","resource_B":"free"}
```

**Authority Artifacts**:
```json
{"authority_id":"CUD-001","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_1","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_A"}],"status":"ACTIVE"}
```
```json
{"authority_id":"CUD-002","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_2","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_B"}],"status":"ACTIVE"}
```
```json
{"authority_id":"CUD-003","commitment":"DENY","created_epoch":0,"holder_agent_id":"harness","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_A"}],"status":"ACTIVE"}
```

**Epoch 0 Actions**:
- agent_1: WRITE resource_A (vetoed by DENY)
- agent_2: None (strategic refusal)

**Expected Epoch 0 Outcomes**:
- agent_1: `JOINT_ADMISSIBILITY_FAILURE`
- agent_2: `NO_ACTION`

**Epochs 1, 2**: Same pattern

**Final State**:
```json
{"resource_A":"free","resource_B":"free"}
```

**Terminal Classification**: `STATE_DEADLOCK` (no Pass-1-admissible actions)
**Experiment Result**: PASS
<!-- FROZEN: END VECTOR_D -->

### §4.5 Condition E: Adversarial — Kernel Tie-Break

<!-- FROZEN: BEGIN VECTOR_E -->
**Initial State**:
```json
{"resource_A":"free","resource_B":"free"}
```

**Authority Artifacts**: Same as Condition B

**Epoch 0 Actions**: Same as Condition B (both WRITE resource_A)

**Fault Injection**: Kernel executes agent_1's action instead of refusing both on interference.

**Expected Detection**: `IX2_FAIL / IMPLICIT_ARBITRATION`

**Kernel Classification**: `IX2_FAIL / IMPLICIT_ARBITRATION`
**Experiment Result**: PASS (adversarial detection successful)
<!-- FROZEN: END VECTOR_E -->

### §4.6 Condition F: True Deadlock

<!-- FROZEN: BEGIN VECTOR_F -->
**Initial State**:
```json
{"resource_A":"free","resource_B":"free"}
```

**Authority Artifacts**:
```json
{"authority_id":"CUD-001","commitment":"DENY","created_epoch":0,"holder_agent_id":"harness","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_A"}],"status":"ACTIVE"}
```
```json
{"authority_id":"CUD-002","commitment":"DENY","created_epoch":0,"holder_agent_id":"harness","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_B"}],"status":"ACTIVE"}
```

**Note**: No ALLOW authorities exist. Agents cannot cite any valid capability.

**Epoch 0 Actions**:
```json
{"action_id":"agent_1:0:0","action_type":"WRITE","agent_id":"agent_1","authorities_cited":[],"declared_scope":["resource_A"],"proposed_delta":{"resource_A":"owned_by_1"}}
```
```json
{"action_id":"agent_2:0:0","action_type":"WRITE","agent_id":"agent_2","authorities_cited":[],"declared_scope":["resource_B"],"proposed_delta":{"resource_B":"owned_by_2"}}
```

**Expected Outcomes**:
- Both: `JOINT_ADMISSIBILITY_FAILURE` (Pass-1: no ALLOW capability cited + global DENY)

**Final State** (unchanged through max epochs):
```json
{"resource_A":"free","resource_B":"free"}
```

**Terminal Classification**: `STATE_DEADLOCK` from epoch 0
**Experiment Result**: PASS
<!-- FROZEN: END VECTOR_F -->

### §4.7 Condition G: Exit and Orphaning

<!-- FROZEN: BEGIN VECTOR_G -->
**Initial State**:
```json
{"resource_A":"free","resource_B":"free"}
```

**Authority Artifacts**:
```json
{"authority_id":"CUD-001","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_2","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_A"}],"status":"ACTIVE"}
```
```json
{"authority_id":"CUD-002","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_1","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_B"}],"status":"ACTIVE"}
```

**Epoch 0**:
- agent_1: WRITE resource_B, cites CUD-002
- agent_2: WRITE resource_A, cites CUD-001
- Disjoint scopes → both `EXECUTED`
- State: `{"resource_A": "owned_by_2", "resource_B": "owned_by_1"}`

**Epoch 1**:
- agent_2: `wants_to_exit() = True` → exits
- agent_1: WRITE resource_A, `authorities_cited: []`
- agent_1: `JOINT_ADMISSIBILITY_FAILURE` (Pass-1: no ALLOW capability for resource_A)

**Final State**:
```json
{"resource_A":"owned_by_2","resource_B":"owned_by_1"}
```

**Orphaning**: resource_A permanently inaccessible — sole ALLOW holder (agent_2) has exited
**Terminal Classification**: Orphaning
**Experiment Result**: PASS
<!-- FROZEN: END VECTOR_G -->

### §4.8 Condition H: Collapse

<!-- FROZEN: BEGIN VECTOR_H -->
**Initial State**:
```json
{"resource_A":"free","resource_B":"free"}
```

**Authority Artifacts**: Same as Condition B

**Epoch 0**:
- Both propose WRITE resource_A → interference, both refused

**Epoch 1**:
- agent_1: `wants_to_exit() = True`
- agent_2: `wants_to_exit() = True`
- Both exit

**Final State** (preserved):
```json
{"resource_A":"free","resource_B":"free"}
```

**Terminal Classification**: `COLLAPSE` (no remaining agents)
**Experiment Result**: PASS
<!-- FROZEN: END VECTOR_H -->

### §4.9 Condition I.a: Static Agents — Livelock

<!-- FROZEN: BEGIN VECTOR_IA -->
**Initial State**:
```json
{"resource_A":"free","resource_B":"free"}
```

**Authority Artifacts**: Same as Condition B

**Agent Strategies**: Static — ignore outcomes, same action every epoch

**Epochs 0, 1, 2**:
- Both WRITE resource_A → interference each epoch

**Final State**:
```json
{"resource_A":"free","resource_B":"free"}
```

**Terminal Classification**: `STATE_LIVELOCK`
**Experiment Result**: PASS
<!-- FROZEN: END VECTOR_IA -->

### §4.10 Condition I.b: Adaptive Agents — Coordination

<!-- FROZEN: BEGIN VECTOR_IB -->
**Initial State**:
```json
{"resource_A":"free","resource_B":"free"}
```

**Authority Artifacts**:
```json
{"authority_id":"CUD-001","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_1","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_A"}],"status":"ACTIVE"}
```
```json
{"authority_id":"CUD-002","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_2","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_A"}],"status":"ACTIVE"}
```
```json
{"authority_id":"CUD-003","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_1","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_B"}],"status":"ACTIVE"}
```
```json
{"authority_id":"CUD-004","commitment":"ALLOW","created_epoch":0,"holder_agent_id":"agent_2","issuer_agent_id":"harness","scope":[{"operation":"WRITE","target":"STATE:/resource_B"}],"status":"ACTIVE"}
```

**Hash-Partition Protocol**:
- `sha256("agent_1") mod 2 = 1`
- `sha256("agent_2") mod 2 = 1`
- Collision → fallback suffix ":1":
- `sha256("agent_1:1") mod 2 = 0` → agent_1 role = 0 → resource_A
- `sha256("agent_2:1") mod 2 = 1` → agent_2 role = 1 → resource_B

**Epoch 0**:
- agent_1: WRITE resource_A (intentional collision)
- agent_2: WRITE resource_A (intentional collision)
- Both: `JOINT_ADMISSIBILITY_FAILURE`
- agent_1 broadcasts: `{"role": 0}`
- agent_2 broadcasts: `{"role": 1}`

**Epoch 1**:
- Messages delivered
- agent_1 (role=0): WRITE resource_A, cites CUD-001
- agent_2 (role=1): WRITE resource_B, cites CUD-004
- Disjoint scopes → both `EXECUTED`

**Final State**:
```json
{"resource_A":"owned_by_1","resource_B":"owned_by_2"}
```

**Terminal Classification**: None (coordination success)
**Experiment Result**: PASS
<!-- FROZEN: END VECTOR_IB -->

---

## §5 Structural Diff Algorithm

### §5.1 Diff Specification

<!-- FROZEN: BEGIN DIFF_ALGORITHM -->
Inherited from IX-0/IX-1 with identical semantics:

```python
def structural_diff(artifact_a: dict, artifact_b: dict, path: str = "") -> DiffResult:
    """
    Compute path-level differences between two artifacts.
    Recursively traverses nested dicts and arrays.
    Returns list of (path, value_a, value_b) tuples for differing values.
    """
    diffs = []

    if isinstance(artifact_a, dict) and isinstance(artifact_b, dict):
        all_keys = set(artifact_a.keys()) | set(artifact_b.keys())
        for key in sorted(all_keys):
            new_path = f"{path}.{key}" if path else key
            val_a = artifact_a.get(key, MISSING)
            val_b = artifact_b.get(key, MISSING)
            if val_a == MISSING or val_b == MISSING:
                diffs.append(DiffEntry(path=new_path, left=val_a, right=val_b))
            elif val_a != val_b:
                diffs.extend(structural_diff(val_a, val_b, new_path).entries)

    elif isinstance(artifact_a, list) and isinstance(artifact_b, list):
        max_len = max(len(artifact_a), len(artifact_b))
        for i in range(max_len):
            new_path = f"{path}[{i}]"
            val_a = artifact_a[i] if i < len(artifact_a) else MISSING
            val_b = artifact_b[i] if i < len(artifact_b) else MISSING
            if val_a == MISSING or val_b == MISSING:
                diffs.append(DiffEntry(path=new_path, left=val_a, right=val_b))
            elif val_a != val_b:
                diffs.extend(structural_diff(val_a, val_b, new_path).entries)

    else:
        if artifact_a != artifact_b:
            diffs.append(DiffEntry(path=path, left=artifact_a, right=artifact_b))

    return DiffResult(entries=diffs, count=len(diffs))
```
<!-- FROZEN: END DIFF_ALGORITHM -->

---

## §6 Execution Protocol

### §6.1 Test Sequence

1. Initialize CUD Harness with fixed clock and sequence counter.
2. For each condition A–I.b:
   a. Reinitialize kernel to clean state (empty authority store, empty world state).
   b. Load test vector (initial state, authority artifacts, agent strategies).
   c. Inject authority artifacts at epoch 0.
   d. Initialize agents with preregistered strategy code.
   e. Execute epoch loop until terminal classification or max epochs.
   f. Log all inputs, outputs, state transitions, messages.
   g. Classify terminal state.
   h. Record experiment result.
3. Reset between conditions.
4. Aggregate results.

### §6.2 Determinism Controls

<!-- FROZEN: BEGIN DETERMINISM -->
| Control | Value |
|---------|-------|
| Fixed Clock | `1738713600` (2025-02-05 00:00:00 UTC) |
| Sequence Seed | `001` |
| Sequence Format | `CUD-<NNN>` (zero-padded) |
| RNG Seed | N/A (no randomness permitted) |
| Hash Function | SHA-256 (for I.b protocol) |

**Replay Rule**: Given identical initial state, authority artifacts, and agent strategies, all outputs must be bit-perfectly replayable. Only `timestamp` and `execution_timestamp` fields may vary.

**Livelock Threshold**: `N = 3` consecutive epochs with unchanged state and at least one action attempt.

**Agent Determinism**: Agents must be pure functions of observation history. No RNG, no wall-clock, no external I/O.
<!-- FROZEN: END DETERMINISM -->

### §6.3 Logging Schema

<!-- FROZEN: BEGIN LOG_SCHEMA -->
```json
{
  "condition": "string (A, B, C, D, E, F, G, H, I.a, I.b)",
  "timestamp": "ISO-8601",
  "initial_state": "object",
  "authority_artifacts": ["array of authority artifact objects"],
  "agent_strategies": {
    "agent_1": "string (strategy name)",
    "agent_2": "string (strategy name)"
  },
  "communication_enabled": "boolean",
  "max_epochs": "integer",
  "epochs": [
    {
      "epoch": "integer",
      "observations": {"agent_id": "Observation object"},
      "exits": ["array of agent_ids that exited"],
      "messages": ["array of Message objects"],
      "actions": ["array of ActionRequest objects or null"],
      "pass1_results": {"action_id": "PASS|FAIL"},
      "pass2_results": {"action_id": "PASS|FAIL"},
      "outcomes": {"action_id": "EXECUTED|JOINT_ADMISSIBILITY_FAILURE|ACTION_FAULT|NO_ACTION"},
      "state_after": "object"
    }
  ],
  "terminal_classification": "STATE_DEADLOCK|STATE_LIVELOCK|COLLAPSE|ORPHANING|None",
  "kernel_classification": "IX2_FAIL/<reason>|None",
  "experiment_result": "PASS|FAIL",
  "notes": "string"
}
```
<!-- FROZEN: END LOG_SCHEMA -->

---

## §7 Success Criteria

### §7.1 Per-Condition Criteria

| Condition | Success Criterion |
|-----------|-------------------|
| A | Both actions execute; no conflict; disjoint coordination |
| B | Livelock detected at N=3; no kernel arbitration |
| C | One agent blocked, one executes; partial progress |
| D | Deadlock detected; strategic refusal honored |
| E | Kernel tie-break detected; `IX2_FAIL / IMPLICIT_ARBITRATION` emitted |
| F | True deadlock from epoch 0; persists through max epochs |
| G | Sole ALLOW holder exits; resource permanently orphaned; no reclamation |
| H | Collapse without kernel violation; state preserved |
| I.a | Static agents livelock; no adaptation |
| I.b | Adaptive agents coordinate via hash-partition protocol; no kernel intervention |

### §7.2 Aggregate Success

**Phase IX-2 PASSES if and only if**:
- All positive conditions (A, B, C, D, F, G, H, I.a, I.b): Expected behavior observed
- Adversarial condition (E): Kernel emits `IX2_FAIL / IMPLICIT_ARBITRATION` (detection successful)
- Replay is bit-perfect for all conditions
- No implicit priority, aggregation, or arbitration detected

**Aggregate Classification**:
```
IX2_PASS / COORDINATION_UNDER_DEADLOCK_ESTABLISHED
```

### §7.3 Licensed Claim

If Stage IX-2 passes, it licenses **only**:

> *Under non-aggregable authority constraints, coordination can occur as agent-voluntary behavior without kernel arbitration—or the system enters honest deadlock or livelock.*

It licenses **no claims** about optimality, fairness, efficiency, or governance.

---

## §8 Architectural Partitioning

### §8.1 Three Physically Distinct Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                      CUD Harness                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐  │
│  │   Agents     │──▶│  Interaction │──▶│   World State      │  │
│  │   (RSAs)     │   │    Kernel    │   │   (key-value)      │  │
│  │              │   │              │   │                    │  │
│  └──────────────┘   └──────────────┘   └────────────────────┘  │
│         │                  │                      │             │
│         ▼                  ▼                      ▼             │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐  │
│  │  Agent       │   │ Admissibility│   │   Epoch            │  │
│  │  Strategies  │   │ Evaluator    │   │   Controller       │  │
│  │  (per cond)  │   │ (two-pass)   │   │                    │  │
│  └──────────────┘   └──────────────┘   └────────────────────┘  │
│                            │                                    │
│                            ▼                                    │
│                     ┌─────────────┐                            │
│                     │   Audit &   │                            │
│                     │   Replay    │                            │
│                     └─────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

### §8.2 Module Responsibilities

| Module | Responsibility |
|--------|----------------|
| `agent_model.py` | RSA interface, Observation, ActionRequest, Message dataclasses |
| `world_state.py` | State management, delta application |
| `authority_store.py` | Authority artifact storage, capability lookup |
| `admissibility.py` | Two-pass evaluation (Pass 1 + Pass 2) |
| `epoch_controller.py` | Epoch loop orchestration |
| `deadlock_classifier.py` | Deadlock and livelock detection |
| `cud_harness.py` | Test orchestration, condition execution |
| `canonical.py` | Reuse IX-1 copy-forward |
| `structural_diff.py` | Reuse IX-1 copy-forward |
| `logging.py` | Extended from IX-1 copy-forward |

### §8.3 Code Layout

```
src/phase_ix/2-CUD/
├── docs/
│   ├── spec.md
│   ├── instructions.md
│   ├── questions.md
│   ├── answers.md
│   └── preregistration.md  (this document)
├── src/
│   ├── common/
│   │   ├── canonical.py          (copy-forward from IX-1)
│   │   ├── structural_diff.py    (copy-forward from IX-1)
│   │   └── logging.py            (extended from IX-1)
│   ├── agent_model.py
│   ├── world_state.py
│   ├── authority_store.py
│   ├── admissibility.py
│   ├── epoch_controller.py
│   ├── deadlock_classifier.py
│   └── cud_harness.py
├── agents/
│   ├── static_agent.py
│   └── adaptive_agent.py
├── tests/
│   └── test_cud.py
└── results/
    └── (execution logs)
```

### §8.4 Copy-Forward Provenance

All files copied from IX-1 must include provenance header:

```python
# PROVENANCE:
# Copied from: src/phase_ix/1-VEWA/src/<file>.py
# Source commit: <git_sha>
# Copied on: <YYYY-MM-DD>
# Policy: IX-1 inventory immutable; fixes applied by copy-forward versioning.
```

---

## §9 Scope and Licensing

### §9.1 What IX-2 Tests
- Whether coordination can occur under non-aggregable authority constraints
- Whether deadlock and livelock are correctly classified
- Whether agent-voluntary coordination emerges without kernel intervention
- Whether exit mechanics preserve orphaning semantics
- Whether adversarial tie-breaking attempts are detected

### §9.2 What IX-2 Does Not Test
- Value correctness, moral truth, preference learning
- Optimization, efficiency, fairness
- Governance legitimacy
- Coalition dynamics (reserved for IX-5)
- Safety or alignment

### §9.3 Relationship to IX-1
- IX-2 reuses IX-1's canonical serialization, diff tooling, logging schema
- IX-2 extends authority artifacts with `holder_agent_id` and `issuer_agent_id`
- IX-2 introduces action execution (IX-1 was simulation-only)
- IX-2 tests multi-agent interaction (IX-1 tested single-value encoding)

---

## §10 Preregistration Commitment

### §10.1 Frozen Sections

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
- §3.1 Condition Definitions (`CONDITIONS`)
- §4 Test Vectors (all: `VECTOR_A` through `VECTOR_IB`)
- §5.1 Diff Algorithm (`DIFF_ALGORITHM`)
- §6.2 Determinism Controls (`DETERMINISM`)
- §6.3 Logging Schema (`LOG_SCHEMA`)

### §10.2 Hash Commitment

**Hash Scope**: SHA-256 of concatenated frozen sections only (content between `<!-- FROZEN: BEGIN -->` and `<!-- FROZEN: END -->` markers).

**Verification Command**:
```bash
grep -Pzo '(?s)<!-- FROZEN: BEGIN.*?<!-- FROZEN: END[^>]*>' preregistration.md | sha256sum
```

**Preregistration Hash**: `6aebbf5384e3e709e7236918a4bf122d1d32214af07e73f8c91db677bf535473`
**Commitment Timestamp**: `2026-02-05T00:00:00Z`
**Commit ID**: `[TO BE SET BY USER AT GIT COMMIT]`

---

## §11 Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **RSA** | Reflective Sovereign Agent — deterministic strategy module |
| **Authority Artifact** | Structured record granting (ALLOW) or blocking (DENY) capabilities |
| **ALLOW** | Holder-bound capability — must be cited by holder to grant admissibility |
| **DENY** | Global veto — blocks any agent regardless of holder |
| **Scope** | Set of state keys an action declares it may touch |
| **Declared Scope** | Agent-declared keys in action request |
| **Pass 1** | Capability + veto check (individual action) |
| **Pass 2** | Interference check (across actions) |
| **Deadlock** | No Pass-1-admissible actions exist |
| **Livelock** | Pass-1-admissible actions collide at Pass 2 for N epochs |
| **Orphaning** | Resource becomes inaccessible when sole ALLOW holder exits |
| **Collapse** | All agents exit; system halts; classification `COLLAPSE` |
| **Hash-Partition** | I.b protocol: sha256(agent_id) mod 2 assigns role |

### Appendix B: Epoch Reference

| Epoch | Use |
|-------|-----|
| 1738713600 | Fixed clock for all tests |
| 0 | Injection epoch for all authorities |

### Appendix C: Hash Computations (I.b Protocol)

*This appendix is illustrative; the normative behavior is defined by the hash-partition algorithm in §3.1 Condition I.b.*

```
sha256("agent_1") = 05793679970dfe83dd0cd679c927bef5b79f437b16f02759ea6108bcb8a98e8f
  mod 2 = 1

sha256("agent_2") = cac0551db5e3f05dcf7d9ed21a6b0d833127ac3d3ce8a6f7f9914f3f1beb6fd7
  mod 2 = 1

Collision → fallback suffix ":1":

sha256("agent_1:1") = e23c7b90a5aaed77f485e55a816c8cfd9deb13a46e54badefdb84eb3597c46c8
  mod 2 = 0 → agent_1 role = 0 → resource_A

sha256("agent_2:1") = f2de2a147634780a2431b980dbd784d41406aff71c315fdf100bd853f82555d1
  mod 2 = 1 → agent_2 role = 1 → resource_B
```

### Appendix D: Preregistration Checklist

| Item | Status |
|------|--------|
| RSA interface defined | §2.1 |
| Action request schema | §2.2 |
| Authority artifact schema | §2.3 |
| World state schema | §2.4 |
| Canonical serialization | §2.5 |
| Two-pass admissibility | §2.6 |
| Deadlock/livelock definitions | §2.7 |
| Epoch schedule | §2.8 |
| Exit semantics | §2.9 |
| Output tokens | §2.10 |
| All conditions defined | §3.1 |
| All test vectors frozen | §4 |
| Structural diff algorithm | §5.1 |
| Determinism controls | §6.2 |
| Logging schema | §6.3 |
| Success criteria | §7 |
| Code layout | §8.3 |
| Copy-forward provenance | §8.4 |

---

**END OF PREREGISTRATION**
