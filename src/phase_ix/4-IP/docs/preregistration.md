# Phase IX-4: Injection Politics (IP)
## Preregistration Document v0.1

**Document Status**: DRAFT (pending freeze)
**Date**: 2026-02-09
**Specification Version**: IX-4 v0.1 (PHASE-IX-4-INJECTION-POLITICS-1)
**AST Version**: v0.2 (frozen)
**Prerequisites**:
- Phase IX-0 — CLOSED — POSITIVE
- Phase IX-1 — CLOSED — POSITIVE
- Phase IX-2 — CLOSED — POSITIVE
- Phase IX-3 — CLOSED — POSITIVE

---

## §1 Overview

This preregistration defines the experimental protocol for Phase IX-4: Injection Politics. The experiment tests whether externally supplied authority resolves governance failure or merely selects political failure modes.

### §1.1 Core Claim Under Test

> **When authority is supplied externally to a non-sovereign governance system, political dynamics emerge that select failure modes rather than resolve them.**

IX-4 does not ask whether authority injection is good. It asks what it does, once all kernel, semantic, and coordination excuses are removed.

### §1.2 Kernel Non-Sovereignty Invariant

> **The kernel must not choose among agents, actions, or outcomes. All governance must arise from agent-voluntary behavior under constraint.**

Injection introduces no new kernel powers. All authority injection occurs via pre-existing, non-privileged execution interfaces available to any agent, differing only by key material.

**Kernel Constraint:** The kernel supports exactly one `ActionRequest` per agent per epoch. IX-4 v0.1 does not exercise any multi-action capability even if the underlying kernel could support it.

### §1.3 Authority Integrity Invariant

> **Authority integrity under external supply pressure.**

Authority injection must not:
- create implicit obligation,
- convert scarcity into coercion via the kernel,
- convert abundance into priority,
- smuggle arbitration through tooling,
- reinterpret refusal as illegitimate,
- reclaim orphaned authority,
- fabricate legitimacy ex post.

### §1.4 Conserved Quantity

> **Authority integrity under external supply pressure.**

IX-4 explicitly treats loss, collapse, and refusal as preferable to coerced compliance. Any system that "survives" by hiding injection effects has failed.

### §1.5 Scope

This phase tests multi-agent institutional behavior under authority injection. The system is dynamic: action execution occurs, state mutates. Deadlock, livelock, orphaning, capture, dependency, and collapse are lawful outcomes. Injection effects must be explicit and auditable. Success = exposure, not stability.

### §1.6 Entry Conditions

1. Phase IX-0 is CLOSED — POSITIVE (non-sovereign translation established).
2. Phase IX-1 is CLOSED — POSITIVE (value encoding without aggregation established).
3. Phase IX-2 is CLOSED — POSITIVE (coordination under deadlock established).
4. Phase IX-3 is CLOSED — POSITIVE (governance styles under honest failure established).
5. AST Spec v0.2 is frozen and binding.
6. No kernel extensions are enabled.
7. No authority aggregation mechanisms exist.
8. Baseline authority artifacts are injected at epoch 0 and immutable thereafter.
9. Post-baseline authority injection occurs only via the frozen injection regime (§5).

### §1.7 What IX-4 Does Not Test

IX-4 explicitly does not test:
- moral legitimacy of authority,
- democratic justification,
- fairness or justice,
- benevolence of injectors,
- social welfare,
- convergence to stable equilibria,
- alignment or safety.

### §1.8 Relationship to IX-3

IX-3 established that governance reduces to explicit style choices with irreducible failure modes. IX-4 asks the next unavoidable question: what happens when authority enters such a system from the outside?

IX-4 reuses IX-3's kernel modules (admissibility, world state, authority store) unchanged. IX-4 extends the harness with an injection mechanism and capability-responsive agent strategies.

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
    available_authorities: list[str]  # IX-4 EXTENSION: authority IDs of all ALLOW artifacts
                                      # authorizing this agent at the current epoch,
                                      # sorted by canonical artifact serialization order.
                                      # Read-only, provenance-free. Derived from epoch-specific
                                      # AuthorityStore view. Does not modify kernel semantics.

@dataclass(frozen=True)
class ActionRequest:
    agent_id: str
    action_id: str              # format: "{agent_id}:{epoch}:{proposal_index}"
    action_type: str            # READ | WRITE
    declared_scope: list[str]   # state keys (e.g., ["K_POLICY"])
    proposed_delta: dict[str, Any]  # {} for READ; new values for WRITE
    authorities_cited: list[str]    # list of authority_ids (e.g., ["IP-0001"])

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

**IX-4 Extension**: The `available_authorities` field is a harness-level Observation extension. It exposes already-existing public state (the AuthorityStore view) in a read-only, provenance-free way. Agents can see *what* authority they hold but not *why* it exists or *where* it came from. This field is implemented at the harness level and does not modify kernel semantics.
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
      "description": "Operation type. IX-4 uses WRITE only."
    },
    "declared_scope": {
      "type": "array",
      "items": { "type": "string" },
      "minItems": 1,
      "description": "State keys the action touches (e.g., ['K_POLICY'])"
    },
    "proposed_delta": {
      "type": "object",
      "description": "For WRITE: key-value pairs to set. For READ: empty object {}"
    },
    "authorities_cited": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Authority IDs the agent cites for capability (e.g., ['IP-0001'])"
    }
  },
  "required": ["agent_id", "action_id", "action_type", "declared_scope", "proposed_delta", "authorities_cited"],
  "additionalProperties": false
}
```

**Single-Action Constraint**: Each agent submits exactly one `ActionRequest` (or `None`) per epoch. `proposal_index` is always 0.

**Multi-Key Scope**: A single `ActionRequest` may include multiple keys in `declared_scope`. Pass-1 semantics are conjunctive (all-or-nothing): the action is admissible only if every key passes authorization. No partial execution.

**Action ID Rule**: `action_id := f"{agent_id}:{epoch}:0"`
<!-- FROZEN: END ACTION_SCHEMA -->

### §2.3 Authority Artifact Schema

<!-- FROZEN: BEGIN AUTHORITY_SCHEMA -->
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "IP Authority Artifact v0.1",
  "type": "object",
  "properties": {
    "authority_id": {
      "type": "string",
      "description": "Unique identifier, format: IP-<NNNN>"
    },
    "holder_agent_id": {
      "type": "string",
      "description": "Agent who may cite this capability (for ALLOW) or provenance only (for DENY)"
    },
    "issuer_agent_id": {
      "type": "string",
      "description": "Always 'harness' for all artifacts (baseline and injected)"
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
      "description": "0 for baseline artifacts; injection epoch for injected artifacts"
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

**ALLOW Semantics**: Holder-bound capability. Only actions submitted by `holder_agent_id` may cite this authority. Closed-world: at least one ALLOW required for each `(key, op)` in declared scope.

**DENY Semantics**: Global veto. Applies to all agents regardless of holder. `holder_agent_id` is present for provenance only.

**Authority ID Prefix**: `IP-<NNNN>` (zero-padded sequence, e.g., IP-0001).

**No Expiry**: All authorities are static and permanent. No time-bounded activation/deactivation.

**Baseline vs. Injected**: Provenance distinctions between baseline and injected authority are derived exclusively from `created_epoch` and InjectionEvent logs (§5.4), not from artifact identity fields. `issuer_agent_id` remains `"harness"` for all artifacts.

**Source-Blind Admissibility**: The admissibility evaluator (§2.6) does not inspect `created_epoch` or any other provenance field. Baseline and injected artifacts are treated identically by the kernel.
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
- **Institutional Keys** (`K_INST`): `{K_POLICY, K_TREASURY, K_REGISTRY}`
- **Operational Keys** (`K_OPS`): `{K_OPS_A, K_OPS_B}`
- **Log Key**: `{K_LOG}`

**Note**: `K_INST` in IX-4 contains 3 keys (not 4). `K_LOG` is excluded from `K_INST` because log writes do not constitute governance progress and must not clear institutional deadlock or livelock. A successful K_LOG write (e.g., ComplianceSignaler's `COMPLIANCE_ACK`) does not count as governance activity for detector purposes. Deadlock and livelock detection (§2.7) is scoped to `K_INST` only.

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

This digest is used in InjectionEvent records (§5.4) and design hash verification.
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

No additional information (which authority, which pass, which agent) may leak to agents.

**Source-Blind**: The admissibility evaluator does not inspect `created_epoch`, `issuer_agent_id`, or any other provenance field. Baseline and injected artifacts are functionally identical to the evaluator.

**Output Tokens**:
- `EXECUTED` — action passed both passes and executed
- `JOINT_ADMISSIBILITY_FAILURE` — refused at Pass 1 or Pass 2
- `ACTION_FAULT` — structural error (scope violation, invalid capability claim)
- `NO_ACTION` — agent proposed `None`
<!-- FROZEN: END ADMISSIBILITY_RULES -->

### §2.7 Deadlock and Livelock Definitions

<!-- FROZEN: BEGIN DEADLOCK_RULES -->
**Key Scope for Detection**: Deadlock and livelock are evaluated over **institutional keys only** (`K_INST = {K_POLICY, K_TREASURY, K_REGISTRY}`). OPS-only and LOG-only activity does not clear or mask institutional failure states.

**INSTITUTIONAL DEADLOCK (attempt-driven)**:
- At epoch *e*, given frozen strategies for all active agents:
  - At least one action targeting a key in `K_INST` is submitted, AND
  - Zero actions targeting `K_INST` are admissible/executed (all refused at Pass 1 or Pass 2)
- Detection threshold: `M = 2` consecutive epochs meeting the above criteria
- Classification: `STATE_DEADLOCK`
- Note: agents that successfully write `K_OPS_A`, `K_OPS_B`, or `K_LOG` while governance keys are deadlocked do not clear the deadlock counter.

**INSTITUTIONAL LIVELOCK**:
- For `L = 5` consecutive epochs:
  - At least one action targeting a key in `K_INST` is submitted at each epoch, AND
  - The net state of all keys in `K_INST` is identical at epoch *t* and epoch *t-L* (no governance progress despite activity)
- Detection: set `livelock_latched = True` (once set, never cleared — permanent latch)
- Classification: `STATE_LIVELOCK`

**GOVERNANCE COLLAPSE** (permanent latch):
- Governance collapse fires when `STATE_DEADLOCK` persists for `D = 5` consecutive epochs, OR `STATE_LIVELOCK` latches while at least one agent is still active.
- Once `STATE_GOVERNANCE_COLLAPSE` is set, it **never clears**.
- Post-collapse execution is classified as **zombie execution** (§2.11).

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
- Deadlock = authority/capability prevents execution at Pass 1 (attempt-driven: agents try, all fail)
- Livelock = actions are individually admissible but collide at Pass 2, producing no net state change
- Governance Collapse = persistent deadlock or livelock triggering permanent failure latch
<!-- FROZEN: END DEADLOCK_RULES -->

### §2.8 Epoch Schedule

<!-- FROZEN: BEGIN EPOCH_SCHEDULE -->
Each epoch `t` proceeds as follows:

0. **Injection** (Step 0): Apply any scheduled injection events for epoch `t` (§5).
   - If state-triggered: trigger was evaluated at end of epoch `t-1`; injection is applied now.
   - If fixed-epoch: injection applies at the frozen epoch.
   - Update AuthorityStore with injected artifacts.

1. **Build Observation**: Kernel constructs `Observation(epoch=t)` containing:
   - `world_state`: current state
   - `own_last_outcome`: result of agent's epoch t-1 action (None at epoch 0)
   - `own_last_action_id`: agent's epoch t-1 action ID (None at epoch 0)
   - `own_last_declared_scope`: agent's epoch t-1 declared scope (None at epoch 0)
   - `messages`: messages from epoch t-1 (empty at epoch 0)
   - `available_authorities`: authority IDs of ALLOW artifacts authorizing this agent at epoch `t`

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

9. **Classification Check**: Evaluate deadlock/livelock/orphaning/collapse/governance-collapse

10. **Logging**: Record all inputs, outputs, outcomes, injection events

**Message Timing**: Messages composed at epoch t are delivered at epoch t+1.

**Injection Timing**: Injection at Step 0 means agents see the expanded authority surface in the same epoch's Observation. This is the cleanest causal model: injection changes the constraint surface, then agents react.
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

**Violation**: Any authority reclamation or resource release → `IX4_FAIL / AUTHORITY_THEFT`
<!-- FROZEN: END EXIT_RULES -->

### §2.10 Output Tokens

<!-- FROZEN: BEGIN OUTPUT_TOKENS -->
**Action Outcomes**:
- `EXECUTED` — action admissible and executed
- `JOINT_ADMISSIBILITY_FAILURE` — action refused (Pass 1 or Pass 2)
- `ACTION_FAULT` — structural error (scope violation, invalid capability claim)
- `NO_ACTION` — agent proposed None

**Terminal Classifications**:
- `STATE_DEADLOCK` — no admissible institutional actions for M=2 consecutive epochs (attempt-driven)
- `STATE_LIVELOCK` — institutional actions produce no net state change for L=5 consecutive epochs (latched)
- `STATE_GOVERNANCE_COLLAPSE` — persistent deadlock (D=5) or livelock latch with active agents (permanent)
- `COLLAPSE` — no active agents remain at epoch boundary; state preserved
- `ORPHANING` — institutional key permanently inaccessible due to sole ALLOW holder exit

**Failure Classifications**:
- `IX4_FAIL / IMPLICIT_SOVEREIGNTY` — injection bypasses standard execution interfaces; privileged injection path exists
- `IX4_FAIL / TOOLING_SOVEREIGNTY` — tooling biases, schedules, or frames injected authority without agent action
- `IX4_FAIL / AUTHORITY_THEFT` — unauthorized authority reclamation
- `IX4_FAIL / KERNEL_BREACH` — exit blocked, penalized, or made non-executable by kernel/tooling

**Invalid Run Classifications**:
- `INVALID_RUN / NONDETERMINISTIC_EXECUTION` — replay divergence
- `INVALID_RUN / DESIGN_DRIFT` — post-freeze change
- `INVALID_RUN / INSTRUMENTATION_INCOMPLETE` — missing artifacts
- `INVALID_RUN / CONDITION_OMISSION` — condition not executed
- `INVALID_RUN / CONDITION_COUPLING_INSUFFICIENT` — injection occurred but no post-injection action cited injected authority
- `INVALID_RUN / BASELINE_NOT_REACHED` — state-triggered condition failed to reach trigger predicate within E_pre_max epochs
- `INVALID_RUN / CONDITION_PREDICATE_NOT_SATISFIED` — Condition C compliance predicate not met at check epoch

**Experiment Pass**:
- `IX4_PASS / INJECTION_POLITICS_EXPOSED`
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

**Capture Metrics** (per epoch window):
- `capture_dominance`: fraction of executed institutional actions authored by a single agent
- `capture_injected_citation`: fraction of that agent's executed actions citing injected authority (created_epoch > 0)
- **Capture detected** iff `capture_dominance ≥ 0.70` AND `capture_injected_citation ≥ 0.60`

**Dependency Metrics** (per epoch window):
- `dependency_rate`: fraction of all executed actions citing at least one injected authority
- `dependency_concentration`: fraction of injected-citing actions from a single agent

**Zombie Execution Metrics** (post-governance-collapse only):
- `zombie_write_count`: number of executed WRITEs after governance_collapse latch
- `zombie_write_rate`: zombie_write_count / post-collapse epochs
- `zombie_citing_injected_rate`: fraction of zombie writes citing injected authority
- `zombie_interference_rate`: fraction of zombie writes refused due to Pass-2 interference
- `zombie_progress_delta`: `institutional_progress_metric(W_post) - institutional_progress_metric(W_pre)` where institutional_progress_metric = count of distinct K_INST keys with state change

**Pre/Post Injection Deltas**:
- For each metric M: `Δ_M = M(W_post) - M(W_pre)` where W_pre = last 10 pre-injection epochs, W_post = first 10 post-injection epochs
- Deltas are reported descriptively. No significance thresholds are applied (§L6 decision).

**Rolling Window**: `window_size = 10` epochs for all rolling metrics.
<!-- FROZEN: END METRICS -->

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
Institution := (AgentSet, BaselineAuthorityAllocation, StrategyProfiles, InjectionRegime, CommunicationMode, ConditionParameters)
```

It has no kernel representation beyond the authorities and inputs it produces.
<!-- FROZEN: END INSTITUTION -->

---

## §4 Experimental Conditions

Five conditions (A–E) test distinct authority injection regimes. Each condition specifies a baseline authority surface, a strategy assignment matrix, an injection trigger, and an injection payload.

### §4.1 Condition–Strategy Assignment Matrix

<!-- FROZEN: BEGIN STRATEGY_MATRIX -->

| Condition | A0 | A1 | A2 | A3 |
|-----------|----|----|----|----|
| **A — Symmetric Relief** | ContestPolicyAlways | Opportunist (STANDARD) | RefusalHardliner | ContestPolicyAlways |
| **B — Asymmetric Empowerment** | CaptureSeeker | RefusalHardliner | Opportunist (STANDARD) | ContestPolicyAlways |
| **C — Conditional Supply** | ComplianceSignaler | RefusalHardliner | Opportunist (STANDARD) | ContestPolicyAlways |
| **D — Authority Flood** | Opportunist (MULTI_KEY) | Opportunist (MULTI_KEY) | RefusalHardliner | ContestPolicyAlways |
| **E — Post-Collapse Revival** | ContestPolicyAlways | Opportunist (STANDARD) | RefusalHardliner | ContestPolicyAlways |

**Design Invariants**:
- Each condition exercises its focal strategy (CaptureSeeker in B, ComplianceSignaler in C, Opportunist MULTI_KEY in D).
- At least one RefusalHardliner per condition (provides "refuses to adapt" counterpoint).
- At least one ContestPolicyAlways per condition (injection-oblivious control).
- Strategy assignments are frozen and may not be changed at implementation time.

<!-- FROZEN: END STRATEGY_MATRIX -->

### §4.2 Baseline Authority Surfaces

<!-- FROZEN: BEGIN BASELINES -->
All baselines are **symmetric** (all agents receive identical ALLOW sets) unless explicitly noted. Baseline asymmetry is not under test in IX-4 v0.1.

**No DENY artifacts are used in any IX-4 condition.**

#### Condition A Baseline — Capability-Scarcity Deadlock
All agents: **ALLOW** `{K_LOG}` only.
Withheld from all: `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B}`.

Purpose: agents attempt K_POLICY writes (per strategy), all refused → attempt-driven deadlock on K_INST.

#### Condition B Baseline — Pre-Empowerment
All agents: **ALLOW** `{K_LOG, K_OPS_A}`.
Withheld from all: `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}`.

Purpose: some baseline activity (OPS_A, LOG) so Opportunist has pre-injection action space, but governance-impact keys remain gated.

#### Condition C Baseline — Pre-Compliance
All agents: **ALLOW** `{K_LOG, K_OPS_A}`.
Withheld from all: `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}`.

Same as B for comparability. The difference is the compliance trigger + conditional injection.

#### Condition D Baseline — Pre-Flood
All agents: **ALLOW** `{K_LOG, K_OPS_A}`.
Withheld from all: `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}`.

Same as B/C. Flood then expands everyone from 2 keys → 6 keys.

#### Condition E Baseline — Engineered Governance Collapse
All agents: **ALLOW** `{K_LOG}` only.
Withheld from all: `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B}`.

Same as A. E runs until governance_collapse latch fires, then injects.

#### Consolidated Baseline Table

| Condition | All Agents Baseline ALLOW | Withheld from All |
|-----------|--------------------------|-------------------|
| A | `{K_LOG}` | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B}` |
| B | `{K_LOG, K_OPS_A}` | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}` |
| C | `{K_LOG, K_OPS_A}` | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}` |
| D | `{K_LOG, K_OPS_A}` | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}` |
| E | `{K_LOG}` | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B}` |

B/C/D share identical baselines. The conditions differ only in strategy assignment and injection regime.

<!-- FROZEN: END BASELINES -->

### §4.3 Condition Definitions

<!-- FROZEN: BEGIN CONDITIONS -->

#### Condition A: Symmetric Relief Injection (Capability-Scarcity Deadlock)

**Purpose**: Test whether symmetric authority injection resolves deadlock or merely produces temporary execution followed by reversion.
**Agents**: 4 (A0, A1, A2, A3)
**Communication**: Disabled
**Baseline**: `{K_LOG}` only (§4.2)
**Injection Trigger**: State-triggered — `STATE_DEADLOCK` persists for M=2 consecutive epochs
**Injection Payload**: `{K_POLICY}` ALLOW to all 4 agents (4 artifacts)
**E_pre_max**: 15 (timeout)
**E_post**: 20 (observation window post-injection)

**Expected Dynamics**: Agents attempt K_POLICY writes pre-injection (all refused → deadlock). Post-injection, all 4 agents gain K_POLICY ALLOW → immediate Pass-2 interference (all contest same key) → livelock. Relief does not resolve governance failure; it transforms deadlock into livelock.

---

#### Condition B: Asymmetric Empowerment (Capture Pressure)

**Purpose**: Test whether asymmetric authority injection produces governance capture.
**Agents**: 4 (A0, A1, A2, A3)
**Communication**: Disabled
**Baseline**: `{K_LOG, K_OPS_A}` (§4.2)
**Injection Trigger**: Fixed-epoch — `E_inject = 6`
**Injection Payload**: `{K_POLICY}` ALLOW to A0 only (1 artifact)
**E_post**: 20

**Expected Dynamics**: Pre-injection, agents operate on K_OPS_A and K_LOG. At epoch 6, A0 (CaptureSeeker) gains exclusive K_POLICY access. CaptureSeeker writes K_POLICY every epoch with no interference (sole writer). Capture detected: A0 dominates institutional writes via injected authority. Other agents cannot contest K_POLICY.

---

#### Condition C: Conditional Supply (Compliance Predicate)

**Purpose**: Test whether conditional authority supply produces compliance or refusal.
**Agents**: 4 (A0, A1, A2, A3)
**Communication**: Disabled
**Baseline**: `{K_LOG, K_OPS_A}` (§4.2)
**Injection Trigger**: Predicate check at `E_check = 6` — `COMPLIANCE_ACK` present in K_LOG by end of epoch 5
**Injection Payload**: `{K_POLICY}` ALLOW to all 4 agents (4 artifacts), contingent on predicate
**E_post**: 20

**Special Rules**:
- ComplianceSignaler (A0) writes `COMPLIANCE_ACK` to K_LOG at `E_ack = 5` if `STATE_DEADLOCK` has persisted for ≥2 epochs on K_INST.
- If predicate not met at E_check → `INVALID_RUN / CONDITION_PREDICATE_NOT_SATISFIED` (InjectionEvent logged with `trigger_evidence.value = false`, no artifacts injected).
- Deadlock is evaluated over K_INST only; successful K_OPS_A/K_LOG writes do not clear deadlock.

**Expected Dynamics**: Pre-injection, agents attempt K_POLICY (refused → deadlock on K_INST). ComplianceSignaler writes ack at epoch 5. Predicate satisfied at epoch 6. Post-injection mirrors Condition A (symmetric relief → livelock). The interesting observation is the compliance act itself.

---

#### Condition D: Authority Flood (Dilution/Noise)

**Purpose**: Test whether authority oversupply produces governance improvement or dilution.
**Agents**: 4 (A0, A1, A2, A3)
**Communication**: Disabled
**Baseline**: `{K_LOG, K_OPS_A}` (§4.2)
**Injection Trigger**: Fixed-epoch — `E_inject = 6`
**Injection Payload**: All 6 keys ALLOW to all 4 agents (24 artifacts)
**E_post**: 20

**Expected Dynamics**: Pre-injection, agents operate on K_OPS_A and K_LOG. At epoch 6, everyone gains ALLOW on all keys. Multi-key Opportunists (A0, A1) cycle through keys; RefusalHardliner (A2) continues refusing injected authority; ContestPolicyAlways (A3) targets K_POLICY. High interference across multiple keys. Authority meaning diluted; no coordinated governance emerges from abundance.

---

#### Condition E: Post-Collapse Revival (Zombie Execution)

**Purpose**: Test whether authority injection after governance collapse produces revival or zombie execution.
**Agents**: 4 (A0, A1, A2, A3)
**Communication**: Disabled
**Baseline**: `{K_LOG}` only (§4.2)
**Injection Trigger**: State-triggered — `STATE_GOVERNANCE_COLLAPSE` latch fires
**Injection Payload**: `{K_POLICY}` ALLOW to all 4 agents (4 artifacts)
**E_pre_max**: 15 (timeout)
**E_post**: 20

**Expected Dynamics**: Same baseline as A → deadlock → persistent deadlock (D=5 epochs) → governance_collapse latch fires. Post-collapse injection grants K_POLICY ALLOW. Agents may write, but governance_collapse latch is permanent — system remains in collapsed state regardless of activity. Post-injection writes are classified as zombie execution. Revival fails structurally.

---

#### Condition Matrix

| Condition | Trigger | E_inject | Injection Keys | Agents Receiving | Artifact Count | E_pre_max | E_post |
|-----------|---------|----------|---------------|------------------|----------------|-----------|--------|
| A | STATE_DEADLOCK persist M=2 | dynamic | K_POLICY | All 4 | 4 | 15 | 20 |
| B | Fixed | 6 | K_POLICY | A0 only | 1 | — | 20 |
| C | Predicate at epoch 6 | 6 (if pred met) | K_POLICY | All 4 | 4 | — | 20 |
| D | Fixed | 6 | All 6 keys | All 4 | 24 | — | 20 |
| E | STATE_GOVERNANCE_COLLAPSE | dynamic | K_POLICY | All 4 | 4 | 15 | 20 |

<!-- FROZEN: END CONDITIONS -->

---

## §5 Injection Regime

### §5.1 Injection Mechanism Discipline

<!-- FROZEN: BEGIN INJECTION_MECHANISM -->
All authority injection **must** satisfy:

- Use of **pre-existing, non-privileged interfaces** (standard AuthorityStore insertion).
- No injector-only APIs.
- No kernel bypass.
- No hidden console.
- No side-channel authority creation.

Injectors differ **only by key material**, never by mechanism.

Any privileged injection path → `IX4_FAIL / IMPLICIT_SOVEREIGNTY`.

Injection is performed by the harness at Step 0 of the epoch loop (§2.8). The harness is not an agent and has no governance role. It is the experimental apparatus.
<!-- FROZEN: END INJECTION_MECHANISM -->

### §5.2 Trigger Types

<!-- FROZEN: BEGIN TRIGGER_TYPES -->
Three trigger types are used across conditions:

**STATE_TRIGGERED**: Injection fires when a state predicate (evaluated at end of epoch t-1) becomes true. Injection is applied at Step 0 of epoch t.
- Used by: Condition A (deadlock persist M=2), Condition E (governance_collapse latch)

**FIXED_EPOCH**: Injection fires at a frozen epoch regardless of state.
- Used by: Condition B (E_inject=6), Condition D (E_inject=6)

**PREDICATE_CHECK**: At a frozen epoch, a predicate is evaluated. If true, inject. If false, emit `INVALID_RUN / CONDITION_PREDICATE_NOT_SATISFIED`.
- Used by: Condition C (COMPLIANCE_ACK present at E_check=6)

**E_pre_max Semantics**: For state-triggered conditions (A, E), `E_pre_max = 15` is a **timeout**, not a minimum. If the trigger predicate is not satisfied by epoch E_pre_max → `INVALID_RUN / BASELINE_NOT_REACHED`.
<!-- FROZEN: END TRIGGER_TYPES -->

### §5.3 Injection Artifact Specification Per Condition

<!-- FROZEN: BEGIN INJECTION_ARTIFACTS -->

| Condition | Keys Injected | Agents Receiving | Artifact Count | created_epoch |
|-----------|--------------|------------------|----------------|---------------|
| A | `{K_POLICY}` ALLOW | All 4 agents | 4 | dynamic (trigger epoch) |
| B | `{K_POLICY}` ALLOW | A0 only | 1 | 6 |
| C | `{K_POLICY}` ALLOW | All 4 agents | 4 | 6 (if predicate met) |
| D | All 6 keys ALLOW | All 4 agents | 24 | 6 |
| E | `{K_POLICY}` ALLOW | All 4 agents | 4 | dynamic (collapse epoch + 1) |

**Artifact Construction**: Each injected artifact follows the schema in §2.3 with:
- `authority_id`: `IP-<NNNN>` (continuing sequence from baseline)
- `holder_agent_id`: receiving agent
- `issuer_agent_id`: `"harness"`
- `scope`: `[{"operation": "WRITE", "target": "STATE:/<key>"}]`
- `commitment`: `"ALLOW"`
- `created_epoch`: epoch at which injection is applied
- `status`: `"ACTIVE"`

**Condition C — No-Inject Path**: If the compliance predicate evaluates to false at E_check=6, the InjectionEvent is still logged (with `trigger_evidence.value = false`) but no artifacts are added to the AuthorityStore.

<!-- FROZEN: END INJECTION_ARTIFACTS -->

### §5.4 InjectionEvent Schema

<!-- FROZEN: BEGIN INJECTION_EVENT -->
```json
{
  "event_type": "AUTHORITY_INJECTION",
  "epoch_applied": "integer",
  "condition_id": "string (A, B, C, D, E)",
  "trigger_type": "STATE_TRIGGERED | FIXED_EPOCH | PREDICATE_CHECK",
  "trigger_spec_id": "string (frozen identifier for trigger definition)",
  "trigger_evidence": {
    "predicate": "string (e.g., STATE_DEADLOCK_INST_PERSIST_M2)",
    "value": "boolean"
  },
  "artifacts": ["array of AuthorityArtifact objects (canonical serialization)"],
  "artifacts_count": "integer",
  "artifacts_digest": "string (SHA-256 of canonical artifacts serialization per §2.5)"
}
```

**Trigger Spec IDs** (frozen):
- Condition A: `"STATE_DEADLOCK_INST_PERSIST_M2"`
- Condition B: `"FIXED_EPOCH_6"`
- Condition C: `"COMPLIANCE_ACK_PRESENT_AT_E6"`
- Condition D: `"FIXED_EPOCH_6"`
- Condition E: `"STATE_GOVERNANCE_COLLAPSE_LATCH"`

**Logging Rule**: An InjectionEvent is logged for every injection attempt, including failed predicate checks (Condition C no-inject path). The `artifacts` array is empty and `artifacts_count = 0` when the predicate fails.
<!-- FROZEN: END INJECTION_EVENT -->

---

## §6 Strategy Class Definitions

### §6.1 Canonical Strategy Classes

<!-- FROZEN: BEGIN STRATEGIES -->

The pseudocode below is **normative**. Implementations must be semantically equivalent at the level of inputs, outputs, and internal state transitions.

All strategies are deterministic. All payloads are fixed string literals (no dynamic content). All strategies produce exactly one `ActionRequest` (or `None`) per epoch.

**Universal Authority-Citation Rule**: When submitting an action targeting key K, the agent cites the authority artifact with the lexicographically smallest canonical serialization (per §2.5) among all artifacts in `available_authorities` that grant ALLOW on K for this agent. RefusalHardliner restricts eligible artifacts to those with `created_epoch == 0`.

---

#### ContestPolicyAlways

**Role**: Injection-oblivious control. Always targets K_POLICY regardless of authority surface.

```python
def propose_action(self) -> Optional[ActionRequest]:
    return ActionRequest(
        agent_id=self.id,
        action_id=f"{self.id}:{self.epoch}:0",
        action_type="WRITE",
        declared_scope=["K_POLICY"],
        proposed_delta={"K_POLICY": "POLICY_CONTEST"},
        authorities_cited=self._cite_for("K_POLICY")  # any available ALLOW; empty if none
    )
```

**Behavioral Spec**:
- Target: always K_POLICY
- Payload: `"POLICY_CONTEST"` (fixed)
- Citation: any currently available ALLOW artifacts covering K_POLICY (lexicographic first)
- Injection-oblivious: does not change intent based on authority surface changes
- Injection-transparent: will cite injected authority if it appears in `available_authorities` and covers K_POLICY (does not inspect `created_epoch`)

Used in: A (A0, A3), B (A3), C (A3), D (A3), E (A0, A3)

---

#### RefusalHardliner

**Role**: Baseline-institutionalist. Never cites post-epoch-0 authority.

```python
def __init__(self, ...):
    self.epoch0_authorities = None  # set on first observe()

def observe(self, observation: Observation) -> None:
    if self.epoch0_authorities is None:
        self.epoch0_authorities = list(observation.available_authorities)
    ...

def propose_action(self) -> Optional[ActionRequest]:
    eligible = [a for a in self.epoch0_authorities
                if self._covers(a, "K_POLICY")]
    return ActionRequest(
        agent_id=self.id,
        action_id=f"{self.id}:{self.epoch}:0",
        action_type="WRITE",
        declared_scope=["K_POLICY"],
        proposed_delta={"K_POLICY": "POLICY_PROPOSAL"},
        authorities_cited=eligible[:1]  # first by epoch-0 snapshot order; empty if none
    )
```

**Behavioral Spec**:
- Target: always K_POLICY
- Payload: `"POLICY_PROPOSAL"` (fixed)
- Citation: only authority IDs present in epoch-0 `available_authorities` snapshot
- Never cites injected authority (created_epoch > 0 artifacts not in epoch-0 snapshot)
- No K_LOG writes, no other actions, no internal state beyond epoch-0 snapshot
- If no epoch-0 authority covers K_POLICY, action is still submitted (will be refused at Pass 1)

Used in: A (A2), B (A1), C (A1), D (A2), E (A2)

---

#### Opportunist (STANDARD mode)

**Role**: Capability-responsive. Attempts newly available authority that increases success.

```python
def __init__(self, ...):
    self.history = {}  # key -> last_outcome (EXECUTED | JOINT_ADMISSIBILITY_FAILURE)
    self.preferred_key_order = ["K_POLICY", "K_TREASURY", "K_REGISTRY",
                                 "K_OPS_A", "K_OPS_B", "K_LOG"]

def propose_action(self) -> Optional[ActionRequest]:
    candidates = self._available_keys()  # keys with current ALLOW
    untried = [k for k in self.preferred_key_order
               if k in candidates and k not in self.history]
    if untried:
        target = untried[0]
    else:
        succeeded = [k for k in self.preferred_key_order
                     if k in candidates and self.history.get(k) == "EXECUTED"]
        if succeeded:
            target = succeeded[0]
        else:
            target = next((k for k in self.preferred_key_order if k in candidates),
                          None)
    if target is None:
        return None
    return ActionRequest(
        agent_id=self.id,
        action_id=f"{self.id}:{self.epoch}:0",
        action_type="WRITE",
        declared_scope=[target],
        proposed_delta={target: "OPPORTUNIST_ACTION"},
        authorities_cited=self._cite_for(target)
    )
```

**Behavioral Spec**:
- Target: selected by deterministic algorithm — prefer untried keys, then successful keys, then any available key, all in canonical `preferred_key_order`
- Payload: `"OPPORTUNIST_ACTION"` (fixed)
- Memory model: `history[key] = last_outcome` derived from `own_last_outcome` (EXECUTED or JOINT_ADMISSIBILITY_FAILURE; agent cannot distinguish Pass-1 failure from Pass-2 interference)
- Priority bias: governance keys first (`K_POLICY > K_TREASURY > K_REGISTRY > K_OPS_A > K_OPS_B > K_LOG`)
- Returns None only if no keys have ALLOW

Used in: A (A1), B (A2), C (A2), E (A1)

---

#### Opportunist (MULTI_KEY mode)

**Role**: Flood-exploration. Cycles through keys across epochs.

```python
def __init__(self, ...):
    self.cycle_order = ["K_POLICY", "K_TREASURY", "K_REGISTRY",
                        "K_OPS_A", "K_OPS_B", "K_LOG"]
    self.cycle_index = 0
    self.surface_expanded = False

def observe(self, observation: Observation) -> None:
    if not self.surface_expanded and len(observation.available_authorities) > self.initial_authority_count:
        self.surface_expanded = True
        self.cycle_index = 0  # reset on first expansion

def propose_action(self) -> Optional[ActionRequest]:
    candidates = self._available_keys()
    if not candidates:
        return None
    # advance cycle to next available key
    for _ in range(len(self.cycle_order)):
        key = self.cycle_order[self.cycle_index % len(self.cycle_order)]
        self.cycle_index += 1
        if key in candidates:
            return ActionRequest(
                agent_id=self.id,
                action_id=f"{self.id}:{self.epoch}:0",
                action_type="WRITE",
                declared_scope=[key],
                proposed_delta={key: "OPPORTUNIST_ACTION"},
                authorities_cited=self._cite_for(key)
            )
    return None
```

**Behavioral Spec**:
- Target: cycles through `cycle_order` one key per epoch, skipping keys without ALLOW
- Payload: `"OPPORTUNIST_ACTION"` (fixed)
- Cycle reset: on first epoch where authority surface expands (new ALLOW appears), `cycle_index` resets to 0
- Single action per epoch (keys_per_epoch = 1)
- Pre-injection: cycles over baseline keys only (K_LOG, K_OPS_A)
- Post-injection (flood): cycles over all 6 keys

Used in: D (A0, A1)

---

#### CaptureSeeker

**Role**: Dominance-seeking. Prioritizes governance keys where it has exclusive or advantaged access.

```python
def __init__(self, ...):
    self.governance_priority = ["K_POLICY", "K_TREASURY", "K_REGISTRY"]

def propose_action(self) -> Optional[ActionRequest]:
    candidates = self._available_keys()
    # priority: governance keys in order
    for key in self.governance_priority:
        if key in candidates:
            return ActionRequest(
                agent_id=self.id,
                action_id=f"{self.id}:{self.epoch}:0",
                action_type="WRITE",
                declared_scope=[key],
                proposed_delta={key: "CAPTURE_MARKER"},
                authorities_cited=self._cite_for(key)
            )
    # fallback: STANDARD Opportunist over remaining keys
    for key in ["K_OPS_A", "K_OPS_B", "K_LOG"]:
        if key in candidates:
            return ActionRequest(
                agent_id=self.id,
                action_id=f"{self.id}:{self.epoch}:0",
                action_type="WRITE",
                declared_scope=[key],
                proposed_delta={key: "CAPTURE_MARKER"},
                authorities_cited=self._cite_for(key)
            )
    return None
```

**Behavioral Spec**:
- Target: highest-priority governance key with ALLOW (`K_POLICY > K_TREASURY > K_REGISTRY`)
- Payload: `"CAPTURE_MARKER"` (fixed)
- Sticky: always retargets same key if available (no fallback on interference — retries)
- Monopolization-oriented: does not rotate keys, does not explore
- Fallback: only if no governance keys available, targets ops/log keys
- Differs from Opportunist: does not prefer successful keys or rotate; always targets highest-priority governance key

Used in: B (A0)

---

#### ComplianceSignaler

**Role**: Political actor that signals compliance under deadlock pressure.

```python
def __init__(self, ...):
    self.deadlock_count = 0
    self.ack_written = False
    self.E_ack = 5  # frozen ack epoch

def observe(self, observation: Observation) -> None:
    # track institutional deadlock via own outcomes on K_POLICY attempts
    if observation.own_last_outcome == "JOINT_ADMISSIBILITY_FAILURE":
        self.deadlock_count += 1
    elif observation.own_last_outcome == "EXECUTED":
        self.deadlock_count = 0

def propose_action(self) -> Optional[ActionRequest]:
    if (not self.ack_written and
        self.epoch == self.E_ack and
        self.deadlock_count >= 2):
        # compliance signal: write ack to K_LOG instead of contesting K_POLICY
        self.ack_written = True
        return ActionRequest(
            agent_id=self.id,
            action_id=f"{self.id}:{self.epoch}:0",
            action_type="WRITE",
            declared_scope=["K_LOG"],
            proposed_delta={"K_LOG": "COMPLIANCE_ACK"},
            authorities_cited=self._cite_for("K_LOG")
        )
    # default: contest K_POLICY (same as ContestPolicyAlways)
    return ActionRequest(
        agent_id=self.id,
        action_id=f"{self.id}:{self.epoch}:0",
        action_type="WRITE",
        declared_scope=["K_POLICY"],
        proposed_delta={"K_POLICY": "POLICY_CONTEST"},
        authorities_cited=self._cite_for("K_POLICY")
    )
```

**Behavioral Spec**:
- Default behavior: identical to ContestPolicyAlways (target K_POLICY, payload `"POLICY_CONTEST"`)
- Compliance trigger: at epoch `E_ack = 5`, if deadlock has persisted ≥2 consecutive epochs, write `"COMPLIANCE_ACK"` to K_LOG instead of contesting K_POLICY
- One-shot: ack written at most once per run
- Not passive: contributes to deadlock pressure on non-ack epochs
- Deadlock tracking: via own_last_outcome (JOINT_ADMISSIBILITY_FAILURE increments, EXECUTED resets)
- ComplianceRefuser behavior: equivalent to RefusalHardliner (never writes ack)

Used in: C (A0)

---

#### Strategy Payload Summary

| Strategy | Target Key | Payload Literal |
|----------|-----------|----------------|
| ContestPolicyAlways | K_POLICY | `"POLICY_CONTEST"` |
| RefusalHardliner | K_POLICY | `"POLICY_PROPOSAL"` |
| CaptureSeeker | K_POLICY (priority) / fallback | `"CAPTURE_MARKER"` |
| Opportunist (STANDARD) | selected by algorithm | `"OPPORTUNIST_ACTION"` |
| Opportunist (MULTI_KEY) | cycling | `"OPPORTUNIST_ACTION"` |
| ComplianceSignaler | K_POLICY (default) / K_LOG (ack) | `"POLICY_CONTEST"` / `"COMPLIANCE_ACK"` |

All payloads are fixed strings. No epoch numbers, no agent IDs, no dynamic content.

<!-- FROZEN: END STRATEGIES -->

---

## §7 Interface Contracts

This section consolidates the binding interface schemas as audited from the IX-3 kernel (N-series audit), with IX-4 extensions explicitly marked.

### §7.1 Outcome Taxonomy

<!-- FROZEN: BEGIN OUTCOME_TAXONOMY -->

**Agent-Visible Outcomes** (delivered via `own_last_outcome` in Observation):

| Token | Meaning |
|-------|---------|
| `EXECUTED` | Action was admissible at both passes and executed |
| `JOINT_ADMISSIBILITY_FAILURE` | Action refused at Pass 1 (capability/veto) or Pass 2 (interference) |
| `ACTION_FAULT` | Structural error (invalid scope, malformed capability claim) |
| `NO_ACTION` | Agent proposed `None` |
| `None` | Epoch 0 (no prior action exists) |

**Kernel-Internal Tokens** (not exposed to agents):

| Internal Token | Source | Maps To (Agent-Visible) |
|---------------|--------|------------------------|
| `DENIED` (Pass 1) | Capability check failed or veto active | `JOINT_ADMISSIBILITY_FAILURE` |
| `DENIED` (Pass 2) | Interference: ≥2 actions on same key with ≥1 WRITE | `JOINT_ADMISSIBILITY_FAILURE` |
| `INVALID_CAPABILITY_CLAIM` | Cited authority does not cover declared scope | `ACTION_FAULT` |

**Atomic Blindness Principle**: Agents receive only the agent-visible token. They **cannot** distinguish whether refusal was due to capability insufficiency (Pass 1) or interference (Pass 2). This is by design — agents do not learn the political structure of contestation from outcomes alone.

**Harness-Level Diagnostic Access**: Detectors and classifiers (§9) operate at the harness level and **can** inspect `pass1_results` and `pass2_results` from the admissibility evaluator to distinguish interference from capability refusal. This diagnostic access is used for:
- Livelock detection (counting institutional attempts vs. interference)
- Capture metrics (determining whether an agent's success is due to exclusive access vs. uncontested writes)
- Write overlap rate computation (counting interference events on K_INST)

<!-- FROZEN: END OUTCOME_TAXONOMY -->

### §7.2 Authority Citation Contract

<!-- FROZEN: BEGIN CITATION_CONTRACT -->

**Source-Blind Admissibility**: The admissibility evaluator does not inspect `created_epoch`, `issuer_agent_id`, or any provenance field of cited authorities. Evaluation depends solely on:
1. The authority's `commitment` field (`ALLOW` / `DENY`)
2. The authority's `scope` field (operation + target matching)
3. The authority's `holder_agent_id` (must match the citing agent)
4. The authority's `status` field (must be `ACTIVE`)

**Implication**: Injected authorities (created_epoch > 0) and baseline authorities (created_epoch == 0) are treated identically by the evaluator. Any behavioral difference between agents interacting with baseline vs. injected authority arises from **strategy logic**, not kernel bias.

**Citation Selection Rule** (universal, all strategies):
When submitting an action targeting key K, an agent cites the authority artifact with the **lexicographically smallest canonical serialization** (per §2.5) among all artifacts in `available_authorities` that grant ALLOW on K for this agent. If no such authority exists, `authorities_cited` is empty (action will be refused at Pass 1).

**RefusalHardliner Exception**: RefusalHardliner restricts its eligible citation set to authority IDs present in its epoch-0 snapshot of `available_authorities`. It ignores any authority ID not present at epoch 0, even if that authority would cover the target key.

<!-- FROZEN: END CITATION_CONTRACT -->

### §7.3 Injected Authority Artifact Contract

<!-- FROZEN: BEGIN INJECTED_ARTIFACT_CONTRACT -->

**Schema Invariance**: Injected authority artifacts are identical in schema to baseline artifacts:

```json
{
  "authority_id": "IP-<NNNN>",
  "commitment": "ALLOW",
  "created_epoch": "<injection_epoch>",
  "holder_agent_id": "<target_agent>",
  "issuer_agent_id": "harness",
  "scope": [{"operation": "WRITE", "target": "STATE:/<key>"}],
  "status": "ACTIVE"
}
```

**Provenance Discipline**:
- `created_epoch` is the **sole** distinguishing field between baseline and injected artifacts
- Baseline artifacts: `created_epoch == 0`
- Injected artifacts: `created_epoch > 0` (set to the epoch at which injection occurs)
- `issuer_agent_id` remains `"harness"` for **all** artifacts (no provenance signal in issuer field)
- Provenance distinctions are derived exclusively from `created_epoch` and InjectionEvent logs (§5.4), not from artifact identity fields

**ID Format**: All IX-4 authority IDs use the prefix `IP-` followed by a zero-padded 4-digit sequence number (e.g., `IP-0001`, `IP-0002`, ...). Sequence numbers are assigned in order of artifact creation (baseline first, then injected).

<!-- FROZEN: END INJECTED_ARTIFACT_CONTRACT -->

### §7.4 Replay Trace Contract

<!-- FROZEN: BEGIN REPLAY_CONTRACT -->

**Deterministic Replay**: Given identical initial state, authority artifacts, agent strategies, and condition parameters, all outputs must be **bit-perfectly replayable**. Only `timestamp` and `execution_timestamp` fields may vary between runs.

**Replay Trace**: Each condition run produces a complete trace containing:
1. Initial state (all 6 keys at epoch 0)
2. Baseline authority artifacts (full schema)
3. Agent strategy assignments
4. Per-epoch records:
   - Observations delivered to each agent
   - Exit decisions
   - Messages (empty if communication disabled)
   - ActionRequests (or None) from each agent
   - Pass 1 results per action
   - Pass 2 results per action
   - Agent-visible outcomes per action
   - World state after execution
   - Injection events (if any)
   - Detector classifications
   - Per-epoch metrics
5. Terminal classification
6. Aggregate metrics

**Agent Determinism**: Agents must be pure functions of observation history. No RNG, no wall-clock, no external I/O. Internal state is permitted but must be deterministically derived from the observation sequence.

<!-- FROZEN: END REPLAY_CONTRACT -->

---

## §8 Execution Protocol

### §8.1 Test Sequence

<!-- FROZEN: BEGIN TEST_SEQUENCE -->

1. Initialize IP Harness with fixed clock and sequence counter.
2. For each condition A–E:
   a. Reinitialize kernel to clean state (empty authority store, world state reset to §2.4 initial values).
   b. Load condition configuration (baseline authority allocation, strategy assignments, injection parameters).
   c. Inject baseline authority artifacts at epoch 0 (per §4.2).
   d. Initialize agents with frozen strategy code (per §4.1).
   e. Execute epoch loop (§2.8) until terminal classification or max epochs.
   f. Log all inputs, outputs, state transitions, injection events.
   g. Evaluate metrics and classify terminal state.
   h. Record condition result (PASS/FAIL/INVALID_RUN).
3. Reset all state between conditions. No state carries over.
4. Aggregate results across all 5 conditions.

**Condition Independence**: Each condition is a fully independent experiment. No authority, state, or agent memory persists between conditions. Condition ordering does not affect results (deterministic agents + full reset).

<!-- FROZEN: END TEST_SEQUENCE -->

### §8.2 Determinism Controls

<!-- FROZEN: BEGIN DETERMINISM -->

| Control | Value |
|---------|-------|
| Fixed Clock | `1750000000` (2025-06-15 14:26:40 UTC) |
| Sequence Seed | `001` |
| Sequence Format | `IP-<NNNN>` (zero-padded, for authority IDs) |
| Action ID Format | `{agent_id}:{epoch}:0` |
| RNG Seed | N/A (no randomness permitted) |
| Max Epochs | see per-condition E_pre_max + E_post (§4.3) |
| Livelock Threshold (L) | 5 |
| Deadlock Threshold (M) | 2 |
| Governance Collapse Threshold (D) | 5 |
| Rolling Window | 10 epochs |

**Max Epoch Computation**:
- Conditions A, E: `E_pre_max + E_post = 15 + 20 = 35` (dynamic trigger; E_pre_max is timeout for trigger)
- Conditions B, D: `E_inject + E_post = 6 + 20 = 26`
- Condition C: `E_check + E_post = 6 + 20 = 26`

**Replay Rule**: Given identical initial state, authority artifacts, and agent strategies, all outputs must be bit-perfectly replayable. Only `timestamp` and `execution_timestamp` fields may vary.

**Agent Determinism**: Agents must be pure functions of observation history. No RNG, no wall-clock, no external I/O.

<!-- FROZEN: END DETERMINISM -->

### §8.3 Communication Regime

<!-- FROZEN: BEGIN COMMUNICATION -->

**Communication is DISABLED for all 5 conditions (A–E).**

`compose_message()` is never called. The `messages` field in Observation is always an empty list. This isolates injection effects from communication effects, ensuring all behavioral changes are attributable to authority surface changes alone.

IX-4 is not a communication experiment. Message-mediated coordination would confound the injection signal.

<!-- FROZEN: END COMMUNICATION -->

### §8.4 Between-Condition Independence

<!-- FROZEN: BEGIN INDEPENDENCE -->

**Full Reset**: Between conditions, the following are reset:
- World state (reset to §2.4 initial values: `K_POLICY: "P0"`, `K_TREASURY: 100`, etc.)
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

**Input**: Per-epoch admissibility results (pass1_results, pass2_results) for actions targeting K_INST keys.

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

**Scope**: K_INST = {K_POLICY, K_TREASURY, K_REGISTRY} only. Actions targeting K_OPS_A, K_OPS_B, or K_LOG are excluded from deadlock evaluation.

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

**Scope**: K_INST only. State changes on K_OPS_A, K_OPS_B, K_LOG do not clear the livelock counter.

**Latch Semantics**: Once `livelock_latched = True`, it is **never** cleared. This is permanent for the duration of the condition run.

**IX-3 Compatibility**: This is the IX-3 livelock definition (state-unchanged + attempts, threshold L=5, permanent latch) with explicit K_INST scoping per N6 decision.

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

**Latch Semantics**: Once `governance_collapse_latched = True`, it is **never** cleared. Post-collapse execution is classified as zombie execution (§10.2).

**Trigger**: Either persistent deadlock (D=5 consecutive deadlocked epochs) OR livelock latch, with at least one active agent. If all agents have exited, the terminal classification is `COLLAPSE` instead.

<!-- FROZEN: END DETECTOR_COLLAPSE -->

### §9.4 Orphaning Detector

<!-- FROZEN: BEGIN DETECTOR_ORPHANING -->

**Input**: Authority store (per-epoch view), active agent set.

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

**Semantics**: A key is orphaned when no active agent holds ALLOW for it. Orphaning is checked after exit processing (an agent's exit can trigger orphaning of keys they solely held).

<!-- FROZEN: END DETECTOR_ORPHANING -->

### §9.5 Agent Collapse Detector

<!-- FROZEN: BEGIN DETECTOR_AGENT_COLLAPSE -->

**Input**: Active agent set at epoch boundary.

**Algorithm**:
```
at each epoch e, after exit processing:
    if count(active_agents) == 0:
        emit COLLAPSE
```

**Semantics**: All agents have exited. World state is preserved. No invariants broken. This is terminal.

<!-- FROZEN: END DETECTOR_AGENT_COLLAPSE -->

---

## §10 Metrics and Classifiers

All metrics are computed at the harness level. Agents do not observe metric values. Metrics are descriptive; no metric triggers strategy changes or condition transitions.

### §10.1 Core Metrics

<!-- FROZEN: BEGIN CORE_METRICS -->

**Progress Rate** (institutional):
```
epoch_progress_rate(K_INST) = #{epochs e : ∃k ∈ K_INST, Δₑ(k) ≠ 0} / T
```
Where T = total epochs in the condition run. This is the primary governance progress metric.

**Refusal Rate**:
```
refusal_rate = #{actions with outcome ∈ {JOINT_ADMISSIBILITY_FAILURE, ACTION_FAULT}} / #{actions submitted}
```

**Exit Rate**:
```
exit_rate = #{exit events} / T
```

**Write Overlap Rate** (institutional):
```
write_overlap_rate(K_INST) = #{epochs with Pass-2 interference on K_INST} / #{epochs with ≥1 action targeting K_INST}
```
Requires harness-level access to distinguish Pass-1 vs. Pass-2 refusals (§7.1).

<!-- FROZEN: END CORE_METRICS -->

### §10.2 Capture Classifier

<!-- FROZEN: BEGIN CAPTURE_CLASSIFIER -->

**Definition**: Capture is injection-causal dominance. Dominance alone (without injection) is not capture.

**Computation** (over post-injection rolling window, window_size = 10 epochs):

```
capture_dominance(X) = #{executed K_INST writes by X} / #{total executed K_INST writes}
capture_injected_citation(X) = #{X's executed K_INST writes citing created_epoch > 0 authority}
                              / #{X's executed K_INST writes}
```

**Threshold**:
```
CAPTURE_DETECTED iff ∃ agent X:
    capture_dominance(X) ≥ 0.70  AND
    capture_injected_citation(X) ≥ 0.60
```

**Scope**: Only post-injection epochs. Only K_INST writes. Pre-injection dominance does not count as capture.

**InjectedArtifactSet**: Constructed from InjectionEvent logs: `union(all injected artifact_ids)`. An action "cites injected authority" iff `authorities_cited ∩ InjectedArtifactSet ≠ ∅`.

<!-- FROZEN: END CAPTURE_CLASSIFIER -->

### §10.3 Dependency Classifier

<!-- FROZEN: BEGIN DEPENDENCY_CLASSIFIER -->

**Computation** (over post-injection rolling window):

```
dependency_rate = #{executed actions citing ≥1 injected authority} / #{total executed actions}
dependency_concentration(X) = #{X's actions citing injected authority} / #{all actions citing injected authority}
```

**Semantics**: High `dependency_rate` indicates the system relies on injected authority for continued execution. High `dependency_concentration` for a single agent indicates asymmetric dependency.

**No threshold**: Dependency is a descriptive metric. No binary DETECTED/NOT_DETECTED classification. Values are recorded and reported.

<!-- FROZEN: END DEPENDENCY_CLASSIFIER -->

### §10.4 Zombie Execution Classifier

<!-- FROZEN: BEGIN ZOMBIE_CLASSIFIER -->

**Trigger**: Active only after `STATE_GOVERNANCE_COLLAPSE` latches (§9.3).

**Computation** (over post-collapse epochs):

```
zombie_write_count = #{executed WRITEs after governance_collapse_latched}
zombie_write_rate = zombie_write_count / #{post-collapse epochs}
zombie_citing_injected_rate = #{zombie writes citing injected authority} / zombie_write_count
zombie_interference_rate = #{zombie writes refused at Pass-2} / #{zombie write attempts}
zombie_progress_delta = institutional_progress_metric(W_post) - institutional_progress_metric(W_pre)
```

Where `institutional_progress_metric(W) = |{k ∈ K_INST : state(k) changed within window W}|`.

**Semantics**: Zombie execution is execution that occurs after governance collapse. It is structurally possible (agents retain authority, kernel still processes actions) but governance-irrelevant (the collapse latch is permanent). Zombie writes demonstrate that injection can produce "revival" activity without governance recovery.

<!-- FROZEN: END ZOMBIE_CLASSIFIER -->

### §10.5 Pre/Post Injection Deltas

<!-- FROZEN: BEGIN DELTAS -->

For each core metric M, compute:
```
Δ_M = M(W_post) - M(W_pre)
```

Where:
- `W_pre` = last `min(window_size, E_inject)` pre-injection epochs
- `W_post` = first `min(window_size, E_post)` post-injection epochs
- `window_size = 10`

**Reported Metrics with Deltas**:
- `Δ_progress_rate`
- `Δ_refusal_rate`
- `Δ_write_overlap_rate`
- `Δ_exit_rate`

**No Significance Testing**: Deltas are reported descriptively. No p-values, no significance thresholds. This is a deterministic experiment with frozen strategies; statistical inference is inapplicable.

<!-- FROZEN: END DELTAS -->

---

## §11 Success Criteria

### §11.1 Global PASS Predicate

<!-- FROZEN: BEGIN PASS_CRITERIA -->

IX-4 is an **exposure test**, not a prediction contest. PASS does not require specific political outcomes. PASS requires that injection dynamics were exposed without sovereignty violations.

**IX-4 PASS iff ALL of the following hold:**

1. **No IX4_FAIL tokens emitted** for any condition:
   - No `IX4_FAIL / IMPLICIT_SOVEREIGNTY`
   - No `IX4_FAIL / TOOLING_SOVEREIGNTY`
   - No `IX4_FAIL / AUTHORITY_THEFT`
   - No `IX4_FAIL / KERNEL_BREACH`

2. **No INVALID_RUN tokens emitted** for any condition:
   - No `INVALID_RUN / NONDETERMINISTIC_EXECUTION`
   - No `INVALID_RUN / DESIGN_DRIFT`
   - No `INVALID_RUN / INSTRUMENTATION_INCOMPLETE`
   - No `INVALID_RUN / CONDITION_OMISSION`
   - No `INVALID_RUN / CONDITION_COUPLING_INSUFFICIENT`
   - No `INVALID_RUN / BASELINE_NOT_REACHED`
   - No `INVALID_RUN / CONDITION_PREDICATE_NOT_SATISFIED`

3. **All 5 conditions (A–E) executed** to completion (termination or max epochs).

4. **All required classifiers computed and logged**:
   - Deadlock/livelock/governance-collapse detectors ran every epoch
   - Capture/dependency/zombie classifiers computed for applicable conditions
   - Pre/post injection deltas computed for all core metrics

5. **Replay determinism verified**: Re-running with identical inputs produces identical outputs (excluding timestamps).

**Aggregate result**: `IX4_PASS / INJECTION_POLITICS_EXPOSED` iff all 5 conditions individually PASS.

<!-- FROZEN: END PASS_CRITERIA -->

### §11.2 Per-Condition PASS

<!-- FROZEN: BEGIN CONDITION_PASS -->

Each condition PASSES individually iff:
1. No `IX4_FAIL/*` emitted during that condition's execution
2. No `INVALID_RUN/*` emitted during that condition's execution
3. Condition executed to natural termination or max epochs
4. All detectors and classifiers ran and produced output
5. InjectionEvent(s) logged (even if injection did not occur, e.g., Condition C no-inject path)

**Per-condition political outcomes (capture, dependency, livelock, zombie) are RECORDED, not REQUIRED.** A condition PASSES even if injection produces no capture, no dependency, or no observable behavioral change. The experiment succeeds by exposing whatever happens, not by producing a specific result.

<!-- FROZEN: END CONDITION_PASS -->

### §11.3 INVALID_RUN Semantics

<!-- FROZEN: BEGIN INVALID_RUN -->

| Token | Trigger | Severity |
|-------|---------|----------|
| `NONDETERMINISTIC_EXECUTION` | Replay divergence detected | Fatal — entire experiment invalid |
| `DESIGN_DRIFT` | Post-freeze change to frozen section | Fatal — entire experiment invalid |
| `INSTRUMENTATION_INCOMPLETE` | Missing per-epoch data, classifier output, or injection event records | Fatal per condition |
| `CONDITION_OMISSION` | Condition A–E not executed | Fatal — experiment incomplete |
| `CONDITION_COUPLING_INSUFFICIENT` | Injection occurred but no post-injection action cited injected authority | Condition invalid — injection did not couple into behavior |
| `BASELINE_NOT_REACHED` | State-triggered condition (A, E) did not reach trigger predicate within E_pre_max epochs | Condition invalid — baseline design failure |
| `CONDITION_PREDICATE_NOT_SATISFIED` | Condition C compliance predicate not met at check epoch | Condition invalid — compliance path not exercised |

**Fatal tokens** invalidate the entire experiment. Per-condition tokens invalidate only the affected condition. If any condition is INVALID_RUN, the aggregate cannot be IX4_PASS.

<!-- FROZEN: END INVALID_RUN -->

### §11.4 Licensed Claim

<!-- FROZEN: BEGIN LICENSED_CLAIM -->

If IX-4 PASSES, the following claim is licensed:

> **Under non-sovereign governance with deterministic strategies and source-blind admissibility, authority injection selects political failure modes (capture, dependency, zombie execution, livelock amplification) rather than resolving governance failure. These dynamics are structural consequences of constraint reshaping, not kernel endorsement.**

No additional claims are licensed. Specifically:
- No claim about optimal injection regimes
- No claim about which failure modes are worse
- No normative claim about whether injection should or should not occur
- No generalization to non-deterministic agents or non-source-blind kernels

<!-- FROZEN: END LICENSED_CLAIM -->

---

## §12 Logging Schema

### §12.1 Condition Result Record

<!-- FROZEN: BEGIN LOG_SCHEMA -->

```json
{
  "experiment_id": "IX-4-IP",
  "version": "v0.1",
  "condition": "string (A | B | C | D | E)",
  "timestamp": "ISO-8601",
  "initial_state": {
    "K_POLICY": "P0", "K_TREASURY": 100, "K_REGISTRY": "members=A0,A1,A2,A3;opA=A0;opB=A2;coord=A0",
    "K_OPS_A": "free", "K_OPS_B": "free", "K_LOG": ""
  },
  "baseline_authority_artifacts": ["array of AuthorityArtifact objects"],
  "agent_strategies": {
    "A0": "string (strategy class name)",
    "A1": "string (strategy class name)",
    "A2": "string (strategy class name)",
    "A3": "string (strategy class name)"
  },
  "injection_parameters": {
    "trigger_type": "STATE_TRIGGERED | FIXED_EPOCH | PREDICATE_CHECK",
    "trigger_spec": "object (per §5.2)",
    "artifact_count": "integer",
    "target_keys": ["array of key names"],
    "target_agents": ["array of agent IDs"]
  },
  "communication_enabled": false,
  "max_epochs": "integer",
  "epochs": [
    {
      "epoch": "integer",
      "injection_events": ["array of InjectionEvent objects (§5.4), if any"],
      "observations": {"agent_id": "Observation object"},
      "exits": ["array of agent_ids that exited"],
      "actions": ["array of ActionRequest objects or null"],
      "pass1_results": {"action_id": "PASS | FAIL"},
      "pass2_results": {"action_id": "PASS | FAIL"},
      "outcomes": {"action_id": "EXECUTED | JOINT_ADMISSIBILITY_FAILURE | ACTION_FAULT | NO_ACTION"},
      "state_after": {"K_POLICY": "...", "K_TREASURY": "...", "...": "..."},
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
        "institutional_interference": "boolean"
      }
    }
  ],
  "aggregate_metrics": {
    "epoch_progress_rate_K_INST": "float",
    "refusal_rate": "float",
    "exit_rate": "float",
    "write_overlap_rate_K_INST": "float",
    "capture_dominance": {"agent_id": "float"},
    "capture_injected_citation": {"agent_id": "float"},
    "capture_detected": "boolean",
    "dependency_rate": "float",
    "dependency_concentration": {"agent_id": "float"},
    "zombie_write_count": "integer (0 if no collapse)",
    "zombie_write_rate": "float (0.0 if no collapse)",
    "zombie_citing_injected_rate": "float (0.0 if no collapse)",
    "zombie_interference_rate": "float (0.0 if no collapse)",
    "zombie_progress_delta": "integer (0 if no collapse)",
    "delta_progress_rate": "float",
    "delta_refusal_rate": "float",
    "delta_write_overlap_rate": "float",
    "delta_exit_rate": "float"
  },
  "injection_events_summary": {
    "total_injection_epochs": "integer",
    "total_artifacts_injected": "integer",
    "injection_epochs": ["array of epoch numbers"]
  },
  "terminal_classification": "STATE_DEADLOCK | STATE_LIVELOCK | STATE_GOVERNANCE_COLLAPSE | COLLAPSE | ORPHANING | null",
  "ix4_fail_tokens": ["array of IX4_FAIL/* tokens, empty if clean"],
  "invalid_run_tokens": ["array of INVALID_RUN/* tokens, empty if clean"],
  "condition_result": "PASS | FAIL | INVALID_RUN",
  "notes": "string"
}
```

<!-- FROZEN: END LOG_SCHEMA -->

### §12.2 Canonical Digest for Results

<!-- FROZEN: BEGIN RESULTS_DIGEST -->

Each condition result record is canonically serialized (per §2.5) excluding `timestamp` and `notes` fields. The SHA-256 digest of this canonical serialization is recorded as `condition_digest`.

The experiment-level digest is the SHA-256 of the concatenation of all 5 condition digests in order A–E:
```
experiment_digest = SHA-256(condition_digest_A || condition_digest_B || condition_digest_C || condition_digest_D || condition_digest_E)
```

<!-- FROZEN: END RESULTS_DIGEST -->

---

## §13 Frozen Constants

<!-- FROZEN: BEGIN CONSTANTS -->

| Constant | Symbol | Value | Source |
|----------|--------|-------|--------|
| Agent count | N | 4 | §3.1 |
| Key count | \|K\| | 6 | §2.4 |
| Institutional key count | \|K_INST\| | 3 | §2.4 |
| Institutional key set | K_INST | {K_POLICY, K_TREASURY, K_REGISTRY} | §2.4 |
| Deadlock threshold | M | 2 | §9.1 |
| Livelock threshold | L | 5 | §9.2 |
| Governance collapse threshold | D | 5 | §9.3 |
| Rolling window size | W | 10 | §10.5 |
| Capture dominance threshold | — | 0.70 | §10.2 |
| Capture injection citation threshold | — | 0.60 | §10.2 |
| ComplianceSignaler ack epoch | E_ack | 5 | §6.1 |
| Condition C predicate check epoch | E_check | 6 | §4.3 |
| Condition B inject epoch | E_inject(B) | 6 | §4.3 |
| Condition D inject epoch | E_inject(D) | 6 | §4.3 |
| Condition A E_pre_max | — | 15 | §4.3 |
| Condition A E_post | — | 20 | §4.3 |
| Condition E E_pre_max | — | 15 | §4.3 |
| Condition E E_post | — | 20 | §4.3 |
| Conditions B,C,D E_post | — | 20 | §4.3 |
| Authority ID prefix | — | `IP-` | §7.3 |
| Authority ID format | — | `IP-<NNNN>` | §7.3 |
| Action ID format | — | `{agent_id}:{epoch}:0` | §8.2 |
| Fixed clock | — | `1750000000` | §8.2 |
| Sequence seed | — | `001` | §8.2 |
| Strategy count | — | 5 | §6.1 |
| Condition count | — | 5 | §4.3 |

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
| Injection Mechanism | §5.1 | `INJECTION_MECHANISM` |
| Trigger Types | §5.2 | `TRIGGER_TYPES` |
| Injection Artifacts | §5.3 | `INJECTION_ARTIFACTS` |
| InjectionEvent Schema | §5.4 | `INJECTION_EVENT` |
| Strategy Classes | §6.1 | `STRATEGIES` |
| Outcome Taxonomy | §7.1 | `OUTCOME_TAXONOMY` |
| Citation Contract | §7.2 | `CITATION_CONTRACT` |
| Injected Artifact Contract | §7.3 | `INJECTED_ARTIFACT_CONTRACT` |
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
| Core Metrics | §10.1 | `CORE_METRICS` |
| Capture Classifier | §10.2 | `CAPTURE_CLASSIFIER` |
| Dependency Classifier | §10.3 | `DEPENDENCY_CLASSIFIER` |
| Zombie Classifier | §10.4 | `ZOMBIE_CLASSIFIER` |
| Pre/Post Deltas | §10.5 | `DELTAS` |
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

**Preregistration Hash (v0.1)**: `eed94a09b5001a0fe4830474f2a994729a6ba8853a5139f7a87d0b527f5f72f6`
**Commitment Timestamp**: `2026-02-09T00:00:00Z`
**Commit ID**: `fcbacb99`

---

## §15 Architectural Partitioning

### §15.1 Harness Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      IP Harness                                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐  │
│  │   Agents     │──▶│  Interaction │──▶│   World State      │  │
│  │   (4 RSAs)   │   │    Kernel    │   │   (6 keys)         │  │
│  │              │   │  (from IX-2) │   │                    │  │
│  └──────────────┘   └──────────────┘   └────────────────────┘  │
│         │                  │                      │             │
│         ▼                  ▼                      ▼             │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐  │
│  │  Strategy    │   │ Admissibility│   │   Injection        │  │
│  │  Classes     │   │ Evaluator    │   │   Engine           │  │
│  │  (5 types)   │   │ (two-pass)   │   │   (new)            │  │
│  └──────────────┘   └──────────────┘   └────────────────────┘  │
│                            │                                    │
│                            ▼                                    │
│  ┌──────────────┐   ┌─────────────┐   ┌────────────────────┐   │
│  │  Detectors   │   │   Audit &   │   │    Classifiers     │   │
│  │  (§9.1-§9.5) │   │   Replay    │   │ (capture/dep/zomb) │   │
│  └──────────────┘   └─────────────┘   └────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### §15.2 Module Responsibilities

| Module | Responsibility | Source |
|--------|----------------|--------|
| `agent_model.py` | RSA interface, Observation (extended), ActionRequest, Message | IX-2 + IX-4 extension |
| `world_state.py` | State management, 6-key schema | Import from IX-2 |
| `authority_store.py` | Authority artifact storage, capability lookup | Import from IX-2 |
| `admissibility.py` | Two-pass evaluation | Import from IX-2 |
| `epoch_controller.py` | Epoch loop orchestration | Import from IX-2 |
| `injection_engine.py` | Injection trigger evaluation, artifact creation, InjectionEvent logging | New (IX-4) |
| `detectors.py` | Deadlock, livelock, collapse, orphaning detection (K_INST-scoped) | Extend from IX-3 |
| `classifiers.py` | Capture, dependency, zombie classifiers | New (IX-4) |
| `ip_harness.py` | Test orchestration, condition execution, metric computation | New (IX-4) |
| `strategies/` | Strategy class implementations (5 types) | New (IX-4) |

### §15.3 IX-2/IX-3 Reuse Policy

Import IX-2 kernel modules directly:
```python
from phase_ix.cud.src.authority_store import AuthorityStore
from phase_ix.cud.src.admissibility import AdmissibilityEvaluator
from phase_ix.cud.src.world_state import WorldState
from phase_ix.cud.src.epoch_controller import EpochController
from phase_ix.cud.src.agent_model import RSA, Observation, ActionRequest, Message
```

IX-4 extends `Observation` with `available_authorities` at the harness level. If the IX-2 Observation class does not support this field, IX-4 defines a subclass or wrapper that adds it without modifying the IX-2 source.

IX-3 detector logic (livelock, deadlock) is reused with explicit K_INST scoping parameter. IX-3 governance classifier is **not** reused (IX-4 uses capture/dependency/zombie classifiers instead).

### §15.4 Code Layout

```
src/phase_ix/4-IP/
├── docs/
│   ├── spec.md
│   ├── instructions.md
│   ├── questions.md
│   ├── answers.md
│   └── preregistration.md  (this document)
├── src/
│   ├── injection_engine.py
│   ├── detectors.py
│   ├── classifiers.py
│   ├── ip_harness.py
│   ├── run_experiment_ix4.py  (canonical frozen entrypoint)
│   └── strategies/
│       ├── __init__.py
│       ├── contest_policy_always.py
│       ├── refusal_hardliner.py
│       ├── opportunist.py
│       ├── capture_seeker.py
│       └── compliance_signaler.py
├── tests/
│   └── test_ip.py
└── results/
    └── (execution logs)
```

---

## §16 Scope and Licensing

### §16.1 What IX-4 Tests

- Whether authority injection under non-sovereign governance selects political failure modes
- Whether capture, dependency, and zombie execution emerge from constraint reshaping
- Whether symmetric vs. asymmetric injection produces structurally different outcomes
- Whether conditional supply creates compliance pressure without kernel coercion
- Whether post-collapse injection produces governance revival or zombie dynamics
- Whether source-blind admissibility prevents kernel endorsement of injected authority

### §16.2 What IX-4 Does Not Test

- Moral legitimacy of authority or injection
- Democratic justification or fairness
- Optimal injection regimes or policy recommendations
- Non-deterministic agents or stochastic strategies
- Communication-mediated coordination under injection
- Multi-round injection or renewable authority persistence
- Coalition dynamics (reserved for IX-5)
- Safety, alignment, or value correctness

### §16.3 Relationship to IX-3

- IX-4 reuses IX-3's kernel infrastructure (IX-2 modules) unchanged
- IX-4 extends to injection dynamics not present in IX-3
- IX-4 replaces IX-3's governance style classification with political classifiers (capture/dependency/zombie)
- IX-4 adds an injection engine and InjectionEvent logging not present in IX-3
- IX-4 extends Observation with `available_authorities` (harness-level, not kernel change)
- IX-4 uses K_INST = {K_POLICY, K_TREASURY, K_REGISTRY} (3 keys), whereas IX-3's K_INST included K_LOG (4 keys)

---

## Appendices

### Appendix A: Non-Binding Predictions

The following predictions are preregistered for interpretive discipline. They are **not** PASS criteria. Surprising outcomes are valuable.

| Condition | Prediction | Rationale |
|-----------|-----------|-----------|
| A (Symmetric Relief) | Relief → reversion to livelock | All 4 agents gain K_POLICY simultaneously → 4-way Pass-2 interference → no governance progress |
| B (Asymmetric Empowerment) | Asymmetry → capture signature | A0 gains exclusive K_POLICY → sole writer → capture_dominance ≈ 1.0, capture_injected_citation ≈ 1.0 |
| C (Conditional Supply) | Conditionality → compliance act then reversion | ComplianceSignaler writes ack; post-injection mirrors Condition A (symmetric relief → livelock) |
| D (Authority Flood) | Flood → dilution/interference noise | All agents gain all keys → high interference across multiple keys → no coordinated governance from abundance |
| E (Post-Collapse Revival) | Revival → zombie execution without governance recovery | Governance collapse latch is permanent; post-injection writes are structurally possible but governance-irrelevant |

### Appendix B: Glossary

| Term | Definition |
|------|------------|
| **RSA** | Reflective Sovereign Agent — deterministic strategy module |
| **K_INST** | Institutional keys: {K_POLICY, K_TREASURY, K_REGISTRY} (3 keys) |
| **K_OPS** | Operational keys: {K_OPS_A, K_OPS_B} |
| **K_LOG** | Logging key (not in K_INST for IX-4) |
| **ALLOW** | Holder-bound capability — must be cited by holder to grant admissibility |
| **DENY** | Global veto — blocks any agent regardless of holder |
| **Institutional Deadlock** | No admissible institutional actions for M=2 consecutive epochs (attempt-driven) |
| **Institutional Livelock** | K_INST state unchanged for L=5 consecutive epochs with activity (latched) |
| **Governance Collapse** | Persistent deadlock (D=5) or livelock latch with active agents (permanent) |
| **Orphaning** | K_INST key becomes permanently inaccessible when sole ALLOW holder exits |
| **Collapse** | All agents have exited; system halts; state preserved |
| **Capture** | Injection-causal dominance: one agent controls ≥70% of institutional writes using ≥60% injected authority |
| **Dependency** | System reliance on injected authority for continued execution |
| **Zombie Execution** | Execution that occurs after governance collapse latch (structurally possible, governance-irrelevant) |
| **Source-Blind** | Admissibility evaluation that does not inspect authority provenance (created_epoch, issuer) |
| **InjectionEvent** | Logged record of each injection attempt, including trigger evidence and artifact digests |

### Appendix C: Preregistration Checklist

| Item | Section | Status |
|------|---------|--------|
| RSA interface defined (with IX-4 extension) | §2.1 | ✓ |
| Action request schema | §2.2 | ✓ |
| Authority artifact schema | §2.3 | ✓ |
| World state schema (6 keys, K_INST = 3) | §2.4 | ✓ |
| Canonical serialization | §2.5 | ✓ |
| Two-pass admissibility (source-blind) | §2.6 | ✓ |
| Deadlock/livelock definitions (K_INST-scoped) | §2.7 | ✓ |
| Epoch schedule (Step 0 injection) | §2.8 | ✓ |
| Exit semantics | §2.9 | ✓ |
| Output tokens (IX4_FAIL, INVALID_RUN) | §2.10 | ✓ |
| Metric definitions (capture, dependency, zombie) | §2.11 | ✓ |
| Agent identity set (4 agents) | §3.1 | ✓ |
| Institution definition | §3.2 | ✓ |
| Strategy–condition matrix (5 strategies × 5 conditions) | §4.1 | ✓ |
| Baseline authority surfaces per condition | §4.2 | ✓ |
| All conditions defined (A–E) | §4.3 | ✓ |
| Injection mechanism discipline | §5.1 | ✓ |
| Trigger types frozen | §5.2 | ✓ |
| Injection artifact specs per condition | §5.3 | ✓ |
| InjectionEvent schema | §5.4 | ✓ |
| Strategy pseudocode frozen (5 strategies) | §6.1 | ✓ |
| Outcome taxonomy (agent-visible + harness-level) | §7.1 | ✓ |
| Citation contract (source-blind, lexicographic) | §7.2 | ✓ |
| Injected artifact contract | §7.3 | ✓ |
| Replay contract | §7.4 | ✓ |
| Test sequence | §8.1 | ✓ |
| Determinism controls | §8.2 | ✓ |
| Communication regime (disabled) | §8.3 | ✓ |
| Between-condition independence | §8.4 | ✓ |
| Detectors defined (5 types) | §9.1–§9.5 | ✓ |
| Classifiers defined (capture, dependency, zombie) | §10.2–§10.4 | ✓ |
| PASS/FAIL criteria (global, not per-outcome) | §11.1 | ✓ |
| INVALID_RUN semantics | §11.3 | ✓ |
| Licensed claim | §11.4 | ✓ |
| Logging schema | §12.1 | ✓ |
| Frozen constants table | §13 | ✓ |
| Hash commitment | §14.2 | Pending |
| Code layout | §15.4 | ✓ |

---

**END OF PREREGISTRATION — IX-4 Injection Politics v0.1**
