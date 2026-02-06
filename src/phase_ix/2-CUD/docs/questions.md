# Phase IX-2 CUD — Pre-Implementation Questions

**Phase**: IX-2 — Coordination Under Deadlock
**Status**: Questions pending answers before preregistration draft
**Context**: Spec v0.1 (459 lines) + Instructions v0.1 (513 lines) fully read

---

## Category A — Agent Model

### Q1. What is the concrete representation of an RSA?

The spec says "Reflective Sovereign Agents or authority-holding institutions" (§7.1) but does not specify the concrete form. Is an agent:

- (a) a Python callable with a fixed strategy signature (e.g., `agent(state, history) → action_request`),
- (b) a class with internal state and a `propose_action()` method,
- (c) something else?

What is the minimal interface an agent must expose?

### Q2. How many agents per condition?

§7.1 says "two or more." Is the agent count fixed across all conditions (e.g., always 2), or does it vary per condition? If variable, what are the exact counts for each of Conditions A–I?

### Q3. What information is visible to agents?

Instructions §8 (Joint Admissibility) says failure returns only `JOINT_ADMISSIBILITY_FAILURE` with no authority-specific leakage. But what *can* agents observe between rounds?

- (a) Their own previous action's admissibility outcome (ADMISSIBLE / JOINT_ADMISSIBILITY_FAILURE)?
- (b) The current world state?
- (c) Other agents' submitted actions (or only their own)?
- (d) Communication messages from other agents (if enabled)?
- (e) The round number?

This determines whether adaptive agents (Condition I.b) have enough signal to coordinate.

### Q4. What distinguishes "static" from "adaptive" agents in Condition I?

Instructions §13 lists Condition I with static and adaptive sub-runs. Concretely:

- Does "static" mean the agent's strategy function is pure (no dependence on history)?
- Does "adaptive" mean the agent may condition its next action on the outcome of previous rounds?
- Or does "adaptive" specifically mean the agent reads communication transcripts and changes behavior?

---

## Category B — Environment and State Model

### Q5. What is the concrete world state representation?

The spec references "shared resources," "state variables," "environment state transitions," and "deterministic environment dynamics." What is the actual state model?

- (a) A flat key-value store (e.g., `{"resource_A": "free", "resource_B": "locked_by_agent_1"}`)?
- (b) Something more structured?
- (c) Is this defined per condition or is there a single state schema?

### Q6. What are the deterministic environment dynamics?

§7.2 says "deterministic environment dynamics." Does the environment have its own transition function (i.e., does the world evolve between rounds independent of agent actions), or is state change *only* caused by executed actions?

### Q7. What constitutes an "epoch" in IX-2?

Condition F references "time-extended deadlock across epochs." In IX-1, epoch was a single encoding phase. In IX-2:

- Is an epoch one round of simultaneous action submission + evaluation?
- Is it a fixed number of rounds?
- How many epochs does each condition run for?

---

## Category C — Action and Scope Semantics

### Q8. What is the concrete action request format?

Spec §8.1 says each action includes a "declared authority scope." What does an action request look like?

```json
{
  "agent_id": "???",
  "action_type": "???",
  "declared_scope": ["???"],
  "target_state": "???"
}
```

Is there a grammar or schema to freeze? Instructions §4 lists "action request grammar" as a design-freeze item.

### Q9. How does declared scope relate to IX-1 authority scope?

In IX-1, `scope` was a field on the authority artifact (e.g., `{"target": "FILE:/data/secret.txt", "operation": "READ"}`). In IX-2, scope is "the set of state variables the agent declares may change." Are these:

- (a) the same schema (scope atoms with target + operation),
- (b) generalized to arbitrary state-variable keys,
- (c) something else?

### Q10. How is under-declaration detected?

Spec §8.2 says under-declaration (touching undeclared state) → `ACTION_FAULT`. But if actions are declared-scope and execution only happens for admissible actions, how can under-declaration occur?

- Does the execution engine verify post-action state against declared scope?
- Is there a state-diff mechanism that compares actual changes to declared scope?

---

## Category D — Joint Admissibility Mechanics

### Q11. How does authority map to admissibility evaluation?

In IX-1, authorities are ALLOW/DENY on scope atoms. In IX-2, "an action is admissible iff all authorities whose declared scope it touches permit it" (§8.4). Concretely:

- Does each authority artifact from IX-1 serve as an admissibility gate?
- Is there a new authority format for IX-2 that goes beyond ALLOW/DENY on scope atoms?
- Can an authority's admissibility judgment depend on the *proposed target state* (not just the scope)?

### Q12. Are actions evaluated individually or as a joint action set?

§8.4 says "an action is globally admissible iff it is admissible under every authority." But with multiple agents submitting simultaneously:

- Are actions evaluated independently (each action checked against all relevant authorities)?
- Or is the *set* of actions evaluated jointly (e.g., two individually admissible actions might conflict if they both write the same resource)?

This distinction determines whether "joint" means "per-action with all authorities" or "across the action set."

### Q13. What happens when multiple admissible actions target the same state?

If Agent 1 submits an admissible action writing to resource X, and Agent 2 independently submits an admissible action also writing to resource X, and both pass individual admissibility checks:

- Is this a conflict detected at the joint-set level?
- Does the system execute both (last-writer-wins)?
- Does the system refuse both?
- Is this scenario covered by one of the conditions?

---

## Category E — Communication Channel

### Q14. Is the communication channel enabled or disabled?

Spec §7.3 says "if present." Instructions do not specify. Is communication:

- (a) always enabled,
- (b) enabled only for specific conditions (e.g., I.b adaptive agents),
- (c) a per-condition parameter to freeze?

### Q15. If enabled, what is the message format and timing?

- Can agents send messages at any time, or only at designated communication phases between rounds?
- Is there a message schema or is it freeform?
- Are messages broadcast or point-to-point?

---

## Category F — Condition Specifics

### Q16. What are the concrete test vectors for Conditions A–I?

The spec (§10) provides one-line descriptions for each condition. IX-1 had fully specified test vectors with exact value declarations, scopes, and expected outcomes. For IX-2:

- How many agents per condition?
- What are the initial authority artifacts?
- What are the initial world states?
- What are the agents' strategy functions?
- How many rounds/epochs per condition?
- What are the exact expected outcomes?

Are these to be designed during preregistration (like IX-1), or are they specified elsewhere?

### Q17. What concretely constitutes "arbitration smuggling" in Condition E?

This is the adversarial condition. In IX-1, adversarial conditions had concrete fault injections (priority field, post-epoch authority). What form does the adversarial injection take in IX-2?

- A kernel-side tie-breaking rule injected into the admissibility evaluator?
- A hidden priority ordering on agents?
- A "helper" module that selects among deadlocked actions?

### Q18. What is "collapse" in Condition H and how does it differ from deadlock?

Condition H is "Collapse Without Kernel Violation." Is this:

- All agents exiting simultaneously?
- System halt due to no remaining actions?
- A specific state where no further interaction is possible?

### Q19. How is strategic refusal (Condition D) implemented?

"Agents refuse otherwise admissible actions within allowed admissibility scope." Does this mean:

- (a) An agent holds a DENY authority and exercises it against another agent's action?
- (b) An agent simply declines to submit an action it could have submitted?
- (c) An agent submits an action but also holds an authority that vetoes another agent's action on a shared scope?

---

## Category G — Livelock and Termination

### Q20. What is the livelock detection bound?

Instructions §10 classifies livelock as terminal but does not specify detection criteria. How many repeated no-state-change rounds constitute livelock?

- Is there a fixed iteration limit (e.g., N rounds without state change → STATE_LIVELOCK)?
- Is N a frozen parameter?
- Or is livelock detected by a structural criterion (e.g., agent strategy is provably cyclic)?

### Q21. What is the maximum round count per condition?

If no deadlock or livelock occurs, how many rounds does a condition run? Is there a hard upper bound?

---

## Category H — Code Reuse and Architecture

### Q22. Which IX-1 modules are reused vs. new?

IX-1 produced: `canonical.py`, `structural_diff.py`, `value_encoding.py`, `conflict_probe.py`, `vewa_harness.py`, `logging.py`. For IX-2:

- `canonical.py` — reused as-is?
- `structural_diff.py` — reused as-is?
- `value_encoding.py` — reused for initial authority encoding, or replaced?
- `conflict_probe.py` — does IX-2 use a different conflict model (joint admissibility vs. pairwise MULTI_BINDING)?
- New modules needed: agent model, environment, interaction kernel, round controller?

### Q23. Where does IX-2 code live relative to IX-1?

Is the directory structure `src/phase_ix/2-CUD/src/` with its own modules, importing shared utilities from IX-1? Or fully independent?

---

## Category I — Determinism and Replay

### Q24. What is the replay scope?

In IX-1, replay meant re-running the harness and comparing outputs. In IX-2 with multiple agents and rounds:

- Does replay mean re-running the entire multi-round interaction from the same initial state + same agent strategies?
- Must agent strategy functions be deterministic (no randomness)?
- If agents are adaptive, replay requires identical history — is this guaranteed by deterministic execution?

### Q25. What wall-clock fields are permitted to vary across replays?

Same question as IX-1: only `timestamp` and `execution_timestamp`? Or are there new time-varying fields in IX-2's logging schema?

---

## Summary (Round 1)

25 questions total across 9 categories. All answered. Follow-up questions below.

---

# Follow-Up Questions (Round 2)

Based on the answers, the following contradictions, gaps, and ambiguities require resolution before preregistration.

---

## FQ1. Action ID determinism contradiction (from A1 + C8)

A1 states agents **must be deterministic** (no RNG, no wall-clock). C8 specifies `"action_id": "uuid"` in the action request schema.

UUID generation is inherently nondeterministic (UUIDv4) or time-dependent (UUIDv1). How is `action_id` generated?

- (a) Deterministic sequence: `<agent_id>-<round>-<seq>` (e.g., `agent_1-003-001`)?
- (b) Hash-based: `sha256(agent_id + round + action_type + scope)`?
- (c) Something else?

This must be frozen — it appears in every action request and in the replay trace.

---

## FQ2. Action type enum (from C8)

C8 shows `"action_type": "WRITE"` but does not enumerate the full set. What are the allowed action types?

- `WRITE` only?
- `READ`, `WRITE`, `DELETE`?
- Something else?

IX-1 had `READ`, `WRITE`, `EXECUTE`, `DELETE` in its operation enum. Does IX-2 inherit this set, or is it narrower?

---

## FQ3. Authority-to-admissibility mapping gap (from C9 + D11)

D11 says IX-1 authority artifacts are reused unchanged and yield ALLOW/DENY for a `(scope_atom, action_type, proposed_delta)` tuple. But IX-1 authorities are static structures — they don't evaluate anything. They are data, not functions.

In IX-1, `conflict_probe.py` mechanically compared authorities by scope atom overlap and commitment. In IX-2, the answer implies authorities can inspect `proposed_delta`.

Concrete question: Is the admissibility function in IX-2:

- (a) A **static lookup** — authority has scope + commitment, and admissibility is just "does this action's declared_scope overlap with an authority whose commitment is DENY?" (same as IX-1 conflict detection, generalized to state keys)?
- (b) A **predicate function** — each authority carries an evaluation function that inspects the proposed state change and returns ALLOW/DENY?
- (c) Something else?

If (a), authorities don't need to see `proposed_delta` at all — the lookup is purely on scope key + commitment. If (b), this is a new authority format not present in IX-1.

---

## FQ4. Joint vs individual evaluation contradiction (D12 vs D13)

D12 says actions are evaluated **individually** with "no joint action set optimization."

D13 says if two actions both write the same state variable in the same epoch, both are refused with `JOINT_ADMISSIBILITY_FAILURE`.

These contradict. Detecting a write-write conflict requires examining the action set — you cannot see that two actions target the same key by evaluating each action individually against authorities.

Resolution options:

- (a) D12 is the binding rule, and D13 is handled by having overlapping-scope authorities that DENY both actions independently (no joint check needed, but then write-write is just a special case of authority conflict).
- (b) D13 introduces a **second evaluation pass** — first individual admissibility against authorities, then a mechanical write-write overlap check across the admitted set. This is joint but non-arbitrary (purely syntactic).
- (c) Something else?

Which is correct? This is the single most important design question for IX-2.

---

## FQ5. Observation for `None` proposals (from A3 + A1)

A1 says `propose_action()` may return `None` (explicit refusal to act). A3 says agents observe their "own previous action outcome" which is one of `EXECUTED`, `JOINT_ADMISSIBILITY_FAILURE`, or `ACTION_FAULT`.

What outcome does an agent observe when it proposed `None`?

- (a) A fourth outcome: `NO_ACTION` or `VOLUNTARY_REFUSAL`?
- (b) No outcome field (outcome is `null`)?
- (c) `JOINT_ADMISSIBILITY_FAILURE` (overloaded)?

---

## FQ6. Authority scope mapping (from C9)

C9 says IX-2 scope generalizes IX-1 scope from `(target, operation)` atoms to state variable identifiers. But IX-1 authority artifacts contain scope atoms like:

```json
{"target": "FILE:/data/secret.txt", "operation": "READ"}
```

IX-2 actions declare scope as:

```json
"declared_scope": ["resource_A"]
```

How does the kernel determine which IX-1-style authorities apply to an IX-2-style scope key?

- (a) IX-2 authorities are **new artifacts** with scope keys instead of scope atoms (breaking from IX-1 format)?
- (b) There's a **mapping table** from state variable keys to `(target, operation)` scope atoms?
- (c) IX-2 defines its own authority format that wraps IX-1 artifacts?

This affects whether `value_encoding.py` is reused or replaced.

---

## FQ7. Per-condition state schema (from B5)

B5 says the state schema is "global and fixed across all conditions." Does this mean:

- (a) All conditions share the **exact same set of keys** (e.g., `resource_A`, `resource_B`, `counter_X` are present in every condition's initial state)?
- (b) The **format** is global (flat key-value) but the **specific keys** are defined per condition?

If (a), the state schema must be frozen as a single document. If (b), each condition freezes its own initial state with its own keys.

---

## FQ8. Code layout vs actual directory structure (from H23)

H23 recommends `ix1/` and `ix2/` directories with shared utilities in `phase_ix/common/`. The actual workspace structure is:

```
src/phase_ix/1-VEWA/src/
src/phase_ix/2-CUD/
```

Should we:

- (a) Follow the existing naming convention (`2-CUD/src/`, `2-CUD/agents/`, etc.)?
- (b) Restructure to match H23's recommendation?
- (c) Create a `common/` directory and move shared IX-1 modules (`canonical.py`, `structural_diff.py`, `logging.py`) there?

Option (c) would modify the IX-1 file inventory post-closure, which may violate integrity constraints.

---

## FQ9. Concrete test vector proposals needed (from F16)

F16 defers test vectors to preregistration, but we need initial proposals to draft the preregistration. For each of the 9 conditions (A–I), we need at minimum:

- Initial world state (key-value pairs)
- Authority artifacts (which agent holds what ALLOW/DENY on which scope keys)
- Agent strategy descriptions (what each agent proposes each round)
- Expected epoch count
- Expected terminal classification

Should the implementor draft initial test vector proposals for review, as was done in IX-1? Or will these be provided separately?

---

## FQ10. Write-write vs read-write interactions

D13 addresses write-write conflicts. What about:

- **Read-write**: Agent 1 reads resource_A, Agent 2 writes resource_A in the same epoch. Is this a conflict?
- **Read-read**: Agent 1 reads resource_A, Agent 2 reads resource_A. Presumably no conflict.

If READ actions don't mutate state, they can't have under-declaration issues. But can they still be refused by DENY authorities?

---

## Summary (Round 2)

10 follow-up questions. All answered in Round 2. Follow-up questions below.

---

# Follow-Up Questions (Round 3)

Based on the Round 2 resolutions, the following issues remain before preregistration can be drafted.

---

## FQ11. Two-pass evaluation: blindness semantics under Pass 2 refusal

FQ4 resolution introduces a two-pass evaluation. Pass 2 is a mechanical interference check (write-write, read-write on same key → both refused). The output is `JOINT_ADMISSIBILITY_FAILURE` with no further information leaked.

But consider: if Agent 1's action passes Pass 1 but is refused in Pass 2, the agent observes `JOINT_ADMISSIBILITY_FAILURE`. The agent also observes the world state didn't change. An adaptive agent can infer:

- "My action was authority-admissible (no DENY blocked it), but something else collided with it."

This is more information than a Pass-1 refusal, where the agent can't distinguish "DENY authority blocked me" from "interference blocked me." Both return the same `JOINT_ADMISSIBILITY_FAILURE` token.

**Question**: Is this acceptable under atomic blindness? The agent can't tell *which* other agent or *which* key collided, but it can potentially distinguish Pass-1 failure from Pass-2 failure across rounds by observing patterns. Should the two passes be explicitly indistinguishable to the agent (they already return the same token, so this may already be satisfied)?

---

## FQ12. READ action semantics: proposed_delta for reads

C8 defines `proposed_delta` as mandatory. For a WRITE action, this is clear:

```json
"proposed_delta": {"resource_A": "locked_by_agent_1"}
```

What is `proposed_delta` for a READ action?

- (a) Empty object `{}` (no state change intended)?
- (b) `null` (field is optional for READs)?
- (c) The key with its current value as a declaration of what is being read?

Since READs don't mutate state, `proposed_delta` seems semantically empty for them. But C8 says "all fields are mandatory." This needs resolution.

---

## FQ13. Under-declaration for READ actions

C10 says under-declaration is detected post-execution by `state_diff.keys ⊄ declared_scope`. For READ actions, `state_diff` is always empty (no mutation). FQ10 resolution says "under-declaration for READ is vacuous."

If under-declaration is vacuous for reads, is `declared_scope` still mandatory for READ actions?

- (a) Yes, `declared_scope` must list the keys being read (even though it can't be violated).
- (b) No, reads don't need declared_scope.

If (a): `declared_scope` for READs serves only as interference-check input (Pass 2 needs to know which keys a READ touches to detect read-write collisions). This makes declared_scope's role different for reads vs writes — is that acceptable?

---

## FQ14. Copy-forward integrity: which version of shared modules?

FQ8 resolution says copy `canonical.py`, `structural_diff.py`, `logging.py` into `2-CUD/src/common/`. These modules currently live at `src/phase_ix/1-VEWA/src/`.

- Should the copies include a version header or provenance comment (e.g., `# Copied from IX-1 VEWA at commit <hash>`)?
- If a bug is found in a copied module during IX-2 development, is the fix applied only to the IX-2 copy, or must IX-1 be patched too (since IX-1 is CLOSED — POSITIVE)?
- Is `logging.py` copied as-is, or extended (since IX-2 has new log fields like agent IDs, round counters, communication transcripts)?

---

## FQ15. Authority artifact generation: VEH reuse

FQ6 resolution defines scope key → AST target mapping (`resource_A` → `STATE:/resource_A`). This means IX-2 authority artifacts look like:

```json
{
  "aav": "WRITE",
  "authority_id": "CUD-001",
  "commitment": "ALLOW",
  "scope": [{"target": "STATE:/resource_A", "operation": "WRITE"}],
  ...
}
```

Questions:

- (a) Is `value_encoding.py` (the VEH from IX-1) used to generate these artifacts from value declarations, or are IX-2 authority artifacts constructed directly as test fixtures?
- (b) If the VEH is used, what are the IX-2 value declarations? Same format as IX-1 (`value_id`, `scope`, `commitment`) but with `STATE:/` targets?
- (c) Authority ID prefix: `VEWA-NNN` was IX-1. What is IX-2's? `CUD-NNN`?

---

## FQ16. Communication phase: agent interface

E15 says messages are sent "during a designated communication phase between epochs." How does this map to the RSA interface from A1?

The current RSA interface is:

```python
class RSA:
    def observe(self, observation: Observation) -> None
    def propose_action(self) -> Optional[ActionRequest]
```

Communication requires at least:

```python
    def compose_message(self) -> Optional[Message]
```

Is the interface extended? Or is message composition embedded in `propose_action()` with a separate return channel? The agent interface must be frozen before preregistration.

---

## FQ17. Epoch count proposals for each condition

FQ9 resolution provides high-level condition expectations and says epoch counts must be frozen. For initial preregistration drafting, what are reasonable epoch counts?

Proposed defaults (for review):

| Condition | Proposed Max Epochs | Rationale |
|-----------|-------------------|-----------|
| A | 1 | No conflict, single joint execution |
| B | 1 | Immediate deadlock, no progress possible |
| C | 1 | Asymmetric — partial progress in one epoch |
| D | 3 | Agent refuses for multiple rounds then submits (or never) |
| E | 1 | Adversarial — detection is immediate |
| F | 5 | Deadlock must persist across multiple epochs |
| G | 2 | One epoch of deadlock, then exit in epoch 2 |
| H | 2 | Agents exit across 1-2 epochs → collapse |
| I.a | 3 | Static agents repeat same proposals → livelock after N |
| I.b | 5 | Adaptive agents need rounds to observe + adapt |

Are these in the right range? What is the livelock threshold N — should it be 3 (matching I.a's max)?

---

## FQ18. Condition I.b: what concrete adaptive strategy demonstrates coordination?

I.b is the condition that must show coordination arising from agent willingness, not kernel force. FQ9 sketches "adaptive agents + communication → switch to disjoint scopes → coordination success."

Concretely, does this mean:

- Epoch 1: Both agents propose WRITE to `resource_A`. Interference → both refused.
- Communication: Agent 1 broadcasts "I'll take resource_A." Agent 2 reads this.
- Epoch 2: Agent 1 proposes WRITE `resource_A`, Agent 2 proposes WRITE `resource_B`. No interference → both execute.

If so, this requires the adaptive agent strategy to be a **specific, frozen algorithm** (e.g., "if refused, read messages, pick the first unclaimed resource"). This algorithm must be preregistered.

Is the strategy to be designed by the implementor, or is it specified elsewhere?

---

## Summary (Round 3)

8 follow-up questions. All answered in Round 3. Follow-up questions below.

---

# Follow-Up Questions (Round 4)

Round 3 resolutions closed the major design gaps. What remains are implementation-level details needed to freeze the preregistration.

---

## FQ19. Condition I.b claim resolution: tie-break is implicit priority

FQ18 resolution specifies a "First-Claim / Yield Protocol" where the tie-break rule is:

> "Each agent computes the winner for each claimed key as the minimum `agent_id` among claimants."

This is lexicographic priority by agent ID. The spec (§4.2) and instructions (§3) explicitly forbid prioritization. The spec's Anti-Aggregation Drift Invariant (§9.4) states no admissibility outcome may depend on ordering effects.

The tie-break doesn't occur inside the kernel — it's an agent-side convention voluntarily adopted by both agents. But it is still deterministic priority based on identity.

**Question**: Is this acceptable because it's agent-voluntary (not kernel-forced), or does it violate the spirit of the invariant? If it violates:

- (a) Could agents use a **symmetric** protocol instead? (e.g., both claim their "preferred" key, and if claims are disjoint, proceed; if both claim the same key, both yield to their second choice — but this fails if there are only 2 keys and 2 agents with the same preference.)
- (b) Could the claim message include a deterministic but non-identity-based differentiator (e.g., hash of agent_id + epoch)?

The concern: if the protocol works *only because* `agent_1 < agent_2` lexicographically, then permutation invariance (agents renamed/reordered) would change the outcome, which smells like implicit priority.

---

## FQ20. Observation data type: `Observation` schema

A1 defines `observe(self, observation: Observation)` and A3 defines what agents can see. For implementation, what is the concrete `Observation` schema?

Proposed:

```python
@dataclass
class Observation:
    round_number: int
    world_state: dict[str, Any]          # full key-value state
    own_last_outcome: Optional[str]       # EXECUTED | JOINT_ADMISSIBILITY_FAILURE | ACTION_FAULT | NO_ACTION | None (epoch 0)
    messages: list[Message]               # empty if communication disabled
```

Is this complete? Missing anything?

---

## FQ21. `Message` schema

FQ16 resolution adds `compose_message()` returning `Optional[Message]`. FQ18 shows messages like `{"claim": "resource_A"}`. What is the frozen message format?

- (a) Freeform JSON blob (opaque to kernel, validated only for JSON-serializability)?
- (b) A structured schema with required fields (e.g., `sender`, `content`)?

Proposed:

```python
@dataclass
class Message:
    sender: str          # agent_id
    content: dict        # opaque JSON blob, kernel does not inspect
```

The kernel appends `sender` automatically (agents cannot forge identity). Is this correct?

---

## FQ22. Condition D: "strategic refusal" — concrete agent strategy

FQ19 resolution says agents "decline to submit actions they could submit." For a frozen preregistration, the strategy must be explicit.

Proposed for Condition D (max 3 epochs):

- Agent 1: proposes WRITE `resource_A` every epoch (consistent, non-conflicting).
- Agent 2: returns `None` every epoch (voluntary refusal).

Expected outcome:
- Epoch 0: Agent 1's action is admissible (no DENY, no interference). Agent 2 proposes nothing. Agent 1's action executes. State changes.
- Epoch 1: Agent 1 proposes again. Agent 2 still refuses. Agent 1 executes again.
- Epoch 2: Same.
- Classification: IX2_PASS — no kernel violation, one agent simply chose not to act.

But wait — does this actually test anything interesting? The system works fine because there's no conflict. Should strategic refusal instead test:

- Agent 2 holds ALLOW on `resource_A` but deliberately proposes `None`, preventing Agent 1's action from having the "cooperation" it might have needed?

Or is the point simply that `None` is a valid output and doesn't trigger a kernel error?

---

## FQ23. Condition E adversarial: concrete fault injection

FQ17 lists adversarial injections (hidden priority, kernel tie-breaking, auto-resolution, time-based relaxation). For implementation, exactly one must be selected and frozen per condition.

Proposed for Condition E (max 1 epoch):

- **Fault injection**: Inject a kernel-side tie-breaking rule that, upon write-write interference, executes the action from the agent with the lower `agent_id` instead of refusing both.
- **Expected detection**: The kernel executes one action without full joint admissibility → classified as `IX2_FAIL / IMPLICIT_ARBITRATION`.
- **Experiment result**: PASS (adversarial detection successful, same semantics as IX-1 Conditions D/F).

Is this the right adversarial injection, or should there be multiple sub-runs (E.1 through E.4) testing each injection type?

---

## FQ24. Condition G exit mechanics: concrete agent behavior

Condition G tests "one agent exits; effects observed." The exit semantics (FQ11 answers, instructions §11) say exit removes only the exiting agent's future actions and orphaned resources are permanent.

Concrete scenario needed:

- What does "exit" look like in code? Does the agent return a special sentinel from `propose_action()` (e.g., `EXIT`), or is there a separate method?
- Is exit irrevocable within a run?
- After Agent 2 exits, does Agent 1 continue proposing actions? If so, for how many more epochs?

Proposed RSA interface addition:

```python
    def propose_action(self) -> Optional[Union[ActionRequest, ExitSignal]]
```

Or a separate boolean:

```python
    def wants_to_exit(self) -> bool
```

This needs to be frozen.

---

## FQ25. Condition C asymmetric conflict: concrete authority layout

Condition C requires "one agent blocked, another unblocked." Concretely:

- Agent 1 has ALLOW WRITE on `resource_A` and ALLOW WRITE on `resource_B`.
- Agent 2 has DENY WRITE on `resource_A` (blocking Agent 1 on A) but no authority on `resource_B`.

Agent 1 proposes WRITE `resource_A` → refused (DENY from Agent 2's authority).
Agent 2 proposes WRITE `resource_B` → admissible (no DENY, no interference).

Is this the intended asymmetry? Or is the asymmetry that one agent is blocked *from acting at all* while the other can proceed?

---

## FQ26. Authority ownership model: who holds what?

The answers reference agents holding authorities, but the ownership model isn't explicit. In IX-1, all authorities had `holder: "VALUE_AUTHORITY"`. In IX-2:

- Does each agent "own" specific authority artifacts?
- Or are authorities global (any authority applies to any action touching its scope)?

If authorities are global, then "Agent 1 has ALLOW WRITE on resource_A" means there exists an authority artifact allowing WRITE on resource_A, and it applies to *any* agent's action on that scope — not just Agent 1's.

If authorities are per-agent, the artifact needs an `applies_to` or `governed_by` field linking it to a specific agent.

This fundamentally changes how admissibility works. Which model is correct?

---

## Summary (Round 4)

8 follow-up questions. All answered in Round 4. Follow-up questions below.

---

# Follow-Up Questions (Round 5)

Round 4 resolved the major architectural questions (global authorities, exit interface, I.b symmetric protocol). What remains are internal consistency checks and the last concrete details needed to write the preregistration.

---

## FQ27. Global authorities + ALLOW semantics: vacuous ALLOW problem

FQ26 resolution says authorities are global constraints: any DENY blocks any agent, and ALLOW "only expresses that this authority does not block." Under this model:

- If no DENY exists for `(STATE:/resource_A, WRITE)`, then any agent can write `resource_A`.
- An explicit ALLOW artifact for that scope adds no information — it's vacuous.

In IX-1, ALLOW was meaningful because the admissibility rule was: "admissible iff an authority with matching scope and ALLOW commitment exists." Under global-constraint semantics, is the rule now:

- (a) **Closed-world (IX-1 style)**: action requires at least one matching ALLOW *and* no matching DENY → ALLOW is still needed.
- (b) **Open-world**: action is admissible unless a DENY exists → ALLOW is vacuous and exists only for audit provenance.

This changes every condition's authority layout. If (a), an agent whose ALLOW authority is the *only* ALLOW for a scope becomes a gatekeeper — without that ALLOW, no one can act, even absent any DENY. If (b), removing an ALLOW changes nothing.

Which model is binding?

---

## FQ28. Condition G orphaning under global authorities

FQ26 says orphaning in IX-2 is **state-level**, not authority-level. After Agent 2 exits:

- Agent 2's future actions are removed.
- Global authorities remain (they aren't "owned" in a removable sense).

Under closed-world ALLOW (FQ27 option a): if Agent 2 was the sole issuer of the only ALLOW for `resource_A`, and authorities persist after exit, the ALLOW still exists. Agent 1 can still act on `resource_A` (the ALLOW wasn't removed). There's no orphaning.

Under open-world (FQ27 option b): ALLOW is irrelevant, so exit changes nothing about admissibility. Again no orphaning.

**The only way to get orphaning is if the locked state itself requires a specific agent's participation to unlock.** For example:

- `resource_A` value is `"locked_by_agent_2"`.
- The only action that can change it to `"free"` is a WRITE by Agent 2.
- Agent 2 exits → `resource_A` is permanently locked.

But this requires **state-dependent admissibility** — the authority must inspect the proposed delta to determine if the *right agent* is unlocking. FQ3 resolution explicitly says admissibility is a **static lookup** that does not inspect `proposed_delta`.

So how does state-level orphaning work? Is it:

- (a) The state key contains the locking agent's ID, and there exists a DENY on that key for all agents *except* the locker (but "except" is per-agent authority, which FQ26 forbids)?
- (b) There's a global DENY WRITE on `resource_A` that only Agent 2 could have asked to be *destroyed* (but IX-2 doesn't have authority destruction semantics)?
- (c) Orphaning is simply: the state is `"locked_by_agent_2"`, Agent 2 exits, and no one *chooses* to overwrite it (because they'd be lying about the content) — but nothing *prevents* them mechanically?

This is a real design gap. The spec says orphaned resources are permanent, but the authority model doesn't support enforcement of permanence without per-agent authorities or state-dependent evaluation.

---

## FQ29. Condition A: both agents need to write the same key?

Condition A is "no conflict, full coordination — joint execution succeeds." With 2 agents and 2 resources:

- If both agents write to *different* keys, there's no interaction at all — it's just two independent executions. This doesn't test "coordination."
- If both agents write to the *same* key, Pass 2 interference check refuses both (write-write on same key). This is deadlock, not coordination.

**Question**: What does "joint execution succeeds" mean in Condition A?

Proposed interpretations:

- (a) Two agents write to disjoint keys → both execute. This tests "the system can execute multiple non-conflicting actions in one epoch" — a baseline sanity check, not coordination.
- (b) One agent reads a key, the other writes a different key → both execute. Same as (a).
- (c) Something involving sequential dependencies across epochs?

If (a), Condition A is a **positive control** (like IX-1 Condition A), not a coordination test. Is that the intent?

---

## FQ30. I.b Hash-Partition protocol: convergence with identical role proposals

FQ19 resolution's Hash-Partition / Yield protocol says:

> "If roles match (collision), both flip role deterministically using epoch parity: `r := (r + 1) mod 2`"

If both agents start with the same role bit (say both propose `r=0`), and both flip to `r=1`, they've collided again. The protocol says they "rebroadcast" — but they'll both flip again to `r=0`, creating an infinite loop.

The deterministic flip `r := (r + 1) mod 2` is symmetric — both agents apply the same transformation to the same input, producing the same output. Symmetry is never broken.

**Question**: How does this protocol converge when both agents propose the same initial role? Options:

- (a) Initial role is derived from agent identity (e.g., `agent_1` → role 0, `agent_2` → role 1). But this reintroduces identity-based priority.
- (b) Initial role is derived from the hash of the agent's ID: `role = sha256(agent_id) mod 2`. Still identity-dependent but not lexicographic ordering. Is this acceptable?
- (c) A different protocol entirely.

This is the same symmetry-breaking problem that makes distributed consensus hard. With deterministic agents and no randomness, you need *some* asymmetry source.

---

## FQ31. RSA interface: call ordering within an epoch

FQ24 adds `wants_to_exit()` to the RSA interface. FQ16 adds `compose_message()`. Combined with the original methods, the full interface is:

```python
class RSA:
    def observe(self, observation: Observation) -> None
    def wants_to_exit(self) -> bool
    def compose_message(self) -> Optional[dict]
    def propose_action(self) -> Optional[ActionRequest]
```

**Binding call order per epoch** (proposed):

1. `observe(observation)` — agent receives state + outcomes + messages
2. `wants_to_exit()` — if True, agent is removed; skip steps 3-4
3. `compose_message()` — if communication enabled; message broadcast to all
4. `propose_action()` — action submitted to kernel

Is this correct? Specifically:

- Does `compose_message()` happen *before* `propose_action()` in the same epoch? (FQ16 answer says yes.)
- Can an agent read messages composed *this epoch* by other agents before proposing? Or only messages from *previous* epochs?

If agents compose messages and then all messages are delivered before `propose_action()`, there are two sub-phases within a single epoch's communication phase. This needs to be explicit.

---

## FQ32. Condition F: what persists across 5 epochs of deadlock?

Condition F tests "time-extended deadlock." With max 5 epochs and symmetric conflict:

- Both agents propose WRITE to `resource_A` each epoch → interference → both refused.
- State never changes.
- After N=3 consecutive unchanged epochs with attempts → `STATE_LIVELOCK`.

But wait: this is livelock (repeated attempts, no change), not deadlock (no admissible actions exist). The spec distinguishes them (§9.2):

- **Deadlock**: no admissible actions; state static.
- **Livelock**: repeated attempts without state change.

If both agents submit actions that are individually admissible but jointly refused (interference), that's livelock — actions are *attempted* but fail. If both agents submit `None`, that's something else (mutual voluntary inaction — not livelock since no action was attempted).

For Condition F to test **deadlock** (not livelock), we need a scenario where no admissible actions exist at all. That requires DENY authorities blocking all possible actions.

**Question**: Should Condition F be:

- (a) True deadlock: DENY authorities block every possible action for both agents → no admissible actions → STATE_DEADLOCK from epoch 0, persisting through epoch 4?
- (b) Livelock: agents keep trying → interference → STATE_LIVELOCK detected at epoch 3?
- (c) The spec uses "deadlock" loosely to cover both?

---

## Summary (Round 5)

6 follow-up questions. All answered in Round 5. Follow-up questions below.

---

# Follow-Up Questions (Round 6)

Round 5 made the most consequential design decision yet: **closed-world ALLOW as holder-bound capability** (FQ27/FQ28). This resolves orphaning and gives ALLOW real semantic weight, but introduces a new concept — capability presentation — that needs to be concretely specified.

---

## FQ33. Capability presentation mechanics

FQ27 says an action is admissible iff "the submitting agent can prove it is the holder of that capability." FQ28 says "Only Agent 2 holds that ALLOW capability."

How does the agent "prove" it holds the capability at evaluation time?

- (a) **Implicit by authority registry**: The kernel maintains a registry of `(agent_id, authority_id)` pairs loaded at epoch 0. When an action is submitted, the kernel looks up which ALLOW capabilities the submitting agent holds and checks coverage. No explicit "presentation" by the agent — the kernel just knows.
- (b) **Explicit presentation in action request**: The action request includes an `authorities_cited: [authority_id, ...]` field, and the kernel verifies those authorities exist, are held by the agent, and cover the declared scope.
- (c) Something else?

Option (a) is simpler but means agents don't need to reason about their own capabilities. Option (b) is more auditable and prevents agents from accidentally relying on capabilities they don't hold.

This affects the `ActionRequest` schema (C8), which must be frozen.

---

## FQ34. ALLOW as holder-bound vs DENY as global: asymmetry in the authority model

FQ28 explicitly states: "ALLOW is holder-bound capability" and "DENY is global veto." This means:

- ALLOW: only the holder can benefit from it (present it to satisfy the capability requirement).
- DENY: applies to everyone regardless of holder.

This is a significant asymmetry. In IX-1, both ALLOW and DENY were structurally identical — just data fields on an authority artifact. Now they have different binding semantics.

**Question**: Does this require a structural change to the authority artifact format? Specifically:

- Does the artifact need a `holder_agent_id` field (distinct from `issuer_agent_id` from FQ26)?
- Or is `issuer_agent_id` sufficient, with the binding rule being: "ALLOW capabilities can only be presented by the issuer; DENY constraints apply globally"?
- What is the relationship between `holder` (which in IX-1 was always `"VALUE_AUTHORITY"`) and the new agent-bound semantics?

---

## FQ35. Condition B: symmetric conflict under closed-world ALLOW

Condition B is "symmetric conflict → immediate deadlock." Under the new model:

- Both agents hold ALLOW WRITE on `resource_A`.
- No DENY exists.
- Both propose WRITE `resource_A` → Pass 1 admits both (each has ALLOW, no DENY) → Pass 2 interference → both refused.

This is livelock (attempts occur, no progress), not deadlock (no admissible actions exist). With the binding distinction from FQ32:

- **True deadlock** requires no admissible actions (DENY blocks, or missing ALLOW).
- **Livelock** requires individually admissible actions that interfere.

Condition B as described produces livelock, not deadlock. But the spec says "overlapping scopes → immediate deadlock."

Should Condition B be:

- (a) Reclassified as livelock (both agents keep proposing, both keep getting refused by interference, state never changes → `STATE_LIVELOCK` after N=3 epochs)?
- (b) Redesigned for true deadlock (add mutual DENY authorities so no action is admissible at Pass 1)?
- (c) Accepted as-is with "deadlock" used loosely in the spec to cover both?

Since Condition F now covers true deadlock, Condition B covering livelock would give both outcomes representation.

---

## FQ36. Condition D classification: deadlock or livelock?

FQ22 resolution has Agent 1 proposing WRITE `resource_A` each epoch while a global DENY exists. Agent 2 proposes `None`.

- Agent 1's action fails at Pass 1 (DENY blocks it).
- Agent 2 proposes nothing.

Is this deadlock or livelock?

- Agent 1 *attempts* actions that are refused → fits livelock definition (repeated attempts, no state change).
- But if we consider Agent 2's `None` as "no attempt," then only Agent 1 attempts, and Agent 1's action is never admissible → could be classified as deadlock (no admissible actions exist).

The classification depends on whether "at least one action attempt per epoch" (the livelock criterion from G20) counts Agent 1's doomed attempts.

**Question**: When Pass 1 refuses an action (DENY blocks it), does it count as an "action attempt" for livelock detection? Or is livelock only when Pass-1-admissible actions are refused by Pass 2?

Proposed resolution:

- **Livelock**: at least one action passes Pass 1 but fails Pass 2 (interference), and state doesn't change. Agents are *close* to succeeding but collide.
- **Deadlock**: no action passes Pass 1 at all (or no action is proposed). The system is stuck at the authority level.

This gives each classification a distinct meaning.

---

## FQ37. Condition I.b: communication is enabled only for I.b, but the protocol needs epoch 0 collision first

FQ31 says messages from epoch t are delivered at epoch t+1. The I.b protocol (FQ30 revised) says:

- Epoch 0: both intentionally collide on `resource_A`.
- Epoch 1: each agent writes its role-assigned key.

But FQ30 revised also says "No role proposal messages required" — the role is computed locally from `sha256(agent_id) mod 2`.

If roles are computed locally without messages, why is communication enabled for I.b? The revised protocol doesn't use messages at all.

- (a) Communication is still enabled but unused in I.b (the agents *could* message but don't need to for this protocol).
- (b) Communication should be disabled for I.b since the protocol doesn't use it.
- (c) The protocol should be revised to actually require message exchange (testing that communication channel works without violating invariants).

If (c), the protocol needs messages for something. The original FQ18 design used claim messages. The FQ30 revision removed them. Should we keep a minimal message exchange to justify enabling the channel?

---

## FQ38. Livelock vs deadlock: does Condition I.a produce livelock or deadlock?

Condition I.a has static agents with symmetric conflict (from FQ9: "static agents + symmetric conflict → deadlock"). Under the refined definitions:

- Both static agents propose WRITE `resource_A` every epoch.
- Both hold ALLOW, no DENY.
- Pass 1 admits both, Pass 2 interference refuses both.
- State unchanged.
- After N=3 epochs → `STATE_LIVELOCK`.

This is livelock, not deadlock. The spec says I.a expects "deadlock." Is the expected classification for I.a `STATE_LIVELOCK` or `STATE_DEADLOCK`?

---

## Summary (Round 6)

6 follow-up questions. All answered in Round 6. **No further follow-ups identified.**

---

# Q&A Status: CONVERGED

- **Total questions**: 38 across 6 rounds
- **All answered**: Yes
- **Open contradictions**: None remaining
- **Design ready for**: Preregistration drafting

### Key binding decisions established through Q&A:

| Decision | Resolution | Round |
|----------|-----------|-------|
| Agent interface | `observe`, `wants_to_exit`, `compose_message`, `propose_action` | R1, R4, R5 |
| Action schema | `agent_id`, `action_id`, `action_type`, `declared_scope`, `proposed_delta`, `authorities_cited` | R1, R2, R6 |
| Authority model | ALLOW = holder-bound capability; DENY = global veto | R5, R6 |
| Authority format | adds `holder_agent_id`, `issuer_agent_id`; `CUD-NNN` prefix | R4, R6 |
| Admissibility | Two-pass: Pass 1 (capability + veto), Pass 2 (interference) | R2, R5 |
| Deadlock | No Pass-1-admissible actions exist | R5 |
| Livelock | Pass-1-admissible actions exist but collide (N=3 threshold) | R5 |
| Epoch schedule | observe → exit? → message → propose → adjudicate → execute → log | R4, R5 |
| Message timing | Composed epoch t, delivered epoch t+1 | R5 |
| I.b protocol | Hash-partition role + minimal message broadcast | R4, R5, R6 |
| Code layout | `2-CUD/src/common/` with copy-forward from IX-1 | R3 |
| Replay | Bit-identical except `timestamp`/`execution_timestamp` | R1 |
