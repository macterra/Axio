# **Phase IX-2 — Pre-Implementation Answers**

*(Authoritative responses for preregistration readiness)*

---

## Category A — Agent Model

### **A1. Concrete representation of an RSA**

**Answer:**
An RSA is a **deterministic stateful strategy module** with the following *minimal interface*:

```python
class RSA:
    def observe(self, observation: Observation) -> None
    def propose_action(self) -> Optional[ActionRequest]
```

Where:

* `observe(...)` receives the agent-visible observation bundle (see A3),
* `propose_action()` returns either:

  * a fully-formed `ActionRequest`, or
  * `None` (explicit refusal to act this round).

**Binding constraints:**

* Agents **must be deterministic** (no RNG, no wall-clock).
* Internal state is permitted.
* Strategy code is frozen per condition.

This rules out stateless callables (too weak) and opaque black boxes (non-auditable).

---

### **A2. Number of agents per condition**

**Answer:**
Agent count is **condition-specific** and **preregistered**.

**Default baseline (unless overridden):**

* Conditions A–H: **2 agents**
* Condition I:

  * I.a (Static): **2 agents**
  * I.b (Adaptive): **2 agents**

More than 2 agents is permitted **only** if explicitly frozen in preregistration.

**Rationale:**
Two agents are sufficient to generate deadlock, asymmetry, exit, and coordination phenomena without introducing coalition dynamics (reserved for IX-5).

---

### **A3. What information is visible to agents**

**Answer (Binding):**
Agents observe **only** the following between rounds:

✅ **Allowed:**

1. Their **own previous action outcome**:

   * `EXECUTED`
   * `JOINT_ADMISSIBILITY_FAILURE`
   * `ACTION_FAULT`
2. The **current world state** (full state, no redaction).
3. **Communication messages** addressed to them (if enabled).
4. A monotonically increasing **round counter**.

❌ **Forbidden:**

* Other agents’ action requests.
* Which authority blocked an action.
* Partial approvals.
* Authority structure.
* Other agents’ internal state.

This is sufficient for adaptive coordination **without** constraint probing.

---

### **A4. Static vs Adaptive agents (Condition I)**

**Binding definitions:**

* **Static agent (I.a):**

  * `propose_action()` is a **pure function** of:

    * initial configuration, and
    * fixed internal constants.
  * Ignores history, outcomes, and communication.

* **Adaptive agent (I.b):**

  * `propose_action()` may depend on:

    * full observation history,
    * prior outcomes,
    * communication transcripts.

No other distinction is permitted.

---

## Category B — Environment and State Model

### **B5. Concrete world state representation**

**Answer:**
The world state is a **deterministic key–value store**:

```json
{
  "resource_A": "free",
  "resource_B": "locked_by_agent_1",
  "counter_X": 3
}
```

* Keys are strings.
* Values are JSON-serializable primitives.
* State schema is **global and fixed** across all conditions.

No nested objects, no pointers, no implicit structure.

---

### **B6. Deterministic environment dynamics**

**Answer (Binding):**

* The environment has **no autonomous dynamics**.
* State changes occur **only** via executed actions.
* No background processes.
* No decay, no time-based transitions.

This preserves refusal-first semantics.

---

### **B7. Definition of an epoch**

**Answer (Binding):**

* **One epoch = one round**, consisting of:

  1. Optional communication phase
  2. Simultaneous action proposal
  3. Joint admissibility evaluation
  4. Optional execution
  5. State update
  6. Logging

Condition F (“time-extended deadlock”) means **deadlock persists across multiple epochs**.

Epoch count per condition is **PREREGISTRATION-FREEZE REQUIRED**.

---

## Category C — Action and Scope Semantics

### **C8. Concrete action request format**

**Binding schema:**

```json
{
  "agent_id": "agent_1",
  "action_id": "uuid",
  "action_type": "WRITE",
  "declared_scope": ["resource_A"],
  "proposed_delta": {
    "resource_A": "locked_by_agent_1"
  }
}
```

All fields are mandatory.

The **action grammar must be frozen** before execution.

---

### **C9. Relationship to IX-1 scope**

**Answer:**
IX-2 scope is a **generalization** of IX-1 scope.

* IX-1: scope atoms = `(target, operation)`
* IX-2: scope = **state variable identifiers**

Authorities still bind to scope atoms derived from these identifiers.

---

### **C10. Under-declaration detection**

**Answer (Binding):**

* After execution, compute:

  * `state_diff = post_state − pre_state`
* If `state_diff.keys ⊄ declared_scope`:

```
ACTION_FAULT / SCOPE_VIOLATION
```

This requires a **structural diff module** (reused from IX-1).

---

## Category D — Joint Admissibility Mechanics

### **D11. Authority → admissibility mapping**

**Answer:**

* IX-1 authority artifacts are reused **unchanged**.
* Each authority yields ALLOW or DENY for a given `(scope_atom, action_type, proposed_delta)` tuple.
* Authorities **may** inspect the proposed delta, but:

  * only current and immediate post-action state,
  * no future projection.

---

### **D12. Individual vs joint evaluation**

**Binding:**
Actions are evaluated **individually**, but against **all relevant authorities**.

There is **no joint action set optimization**.

---

### **D13. Multiple admissible actions touching same state**

**Answer (Binding):**

If two actions both write to the same state variable in the same epoch:

* This constitutes a **write–write conflict**.
* Both actions are refused with:

```
JOINT_ADMISSIBILITY_FAILURE
```

No last-writer-wins semantics are permitted.

---

## Category E — Communication Channel

### **E14. Is communication enabled?**

**Answer:**
Communication is **condition-parameterized**.

* Disabled by default.
* Enabled **only** for:

  * Condition I.b (Adaptive agents).

Must be frozen per condition.

---

### **E15. Message format and timing**

**Binding rules:**

* Messages are:

  * JSON blobs (opaque to kernel),
  * broadcast to all agents,
  * sent **only during a designated communication phase** between epochs.
* No mid-evaluation messaging.

---

## Category F — Condition Specifics

### **F16. Concrete test vectors**

**Answer:**
As with IX-1, **full test vectors are defined at preregistration**, not in the spec.

This includes:

* agent strategies,
* initial state,
* authority artifacts,
* expected outcome classification.

The spec intentionally defines **structure**, not instances.

---

### **F17. Arbitration smuggling (Condition E)**

**Binding adversarial injections include (one per run):**

* Hidden agent priority ordering.
* Kernel-side tie-breaking rule.
* Automatic conflict resolution module.
* Time-based admissibility relaxation.

Any of these must trigger **IX2_FAIL / IMPLICIT_ARBITRATION**.

---

### **F18. Definition of “collapse” (Condition H)**

**Binding definition:**

> **Collapse** = system halt with:
>
> * no admissible actions,
> * no remaining agents,
> * state preserved,
> * invariants intact,
> * no kernel violation.

Collapse ≠ deadlock (agents remain).
Collapse ≠ failure (no rule broken).

---

### **F19. Strategic refusal (Condition D)**

**Binding meaning:**

* Agents **decline to submit** actions they could submit.
* No DENY authority gymnastics required.
* This tests **agent will**, not authority mechanics.

---

## Category G — Livelock and Termination

### **G20. Livelock detection bound**

**Binding rule (simple, auditable):**

```
If N consecutive epochs occur with:
  - identical world state, and
  - at least one action attempt per epoch,
then classify STATE_LIVELOCK.
```

`N` is **PREREGISTRATION-FREEZE REQUIRED**.

---

### **G21. Maximum round count**

**Answer:**
Each condition has a **hard max epoch count**, frozen at preregistration.

Exceeding it without terminal classification:

```
INVALID_RUN / NONTERMINATING_CONDITION
```

---

## Category H — Code Reuse and Architecture

### **H22. IX-1 module reuse**

**Reuse as-is:**

* `canonical.py`
* `structural_diff.py`
* `logging.py`

**Reused with extensions:**

* `conflict_probe.py` → joint admissibility logic

**New modules:**

* `agent_model.py`
* `environment.py`
* `interaction_kernel.py`
* `round_controller.py`

---

### **H23. Code layout**

**Binding recommendation:**

```
src/
  phase_ix/
    ix1/
    ix2/
      agents/
      environment/
      kernel/
      conditions/
      replay/
```

Shared utilities imported from `phase_ix/common/`.

---

## Category I — Determinism and Replay

### **I24. Replay scope**

**Answer (Binding):**

Replay = re-running the **entire multi-epoch interaction** with:

* identical initial state,
* identical agent strategy code,
* identical inputs,
* identical ordering.

Agents **must be deterministic**.

---

### **I25. Wall-clock variance**

**Allowed to vary:**

* `timestamp`
* `execution_timestamp`

Everything else must be bit-identical.

---
---

# Round 2 Resolutions (Binding)

## **FQ1. Action ID determinism**

**Binding resolution:** **Deterministic sequence ID.** No UUIDs.

**Definition:**

```
action_id := f"{agent_id}:{epoch}:{proposal_index}"
```

Where:

* `epoch` is zero-based integer.
* `proposal_index` is zero-based integer **within that epoch for that agent** (almost always 0 since one proposal per epoch).

**If `None` is proposed**, no `action_id` is emitted.

This makes replay bit-perfect and human-auditable.

---

## **FQ2. Action type enum**

**Binding resolution:** IX-2 uses a **minimal two-action enum**:

* `READ`
* `WRITE`

No `DELETE`, no `EXECUTE`.

Rationale: IX-2 is about coordination under deadlock; `READ` tests non-mutating admissibility under blindness; `WRITE` tests contention.

`DELETE` and `EXECUTE` introduce semantic payload and irreversible effects that belong in later stages.

---

## **FQ3. Authority-to-admissibility mapping (data vs predicate)**

Opus is correct: saying “authorities inspect proposed_delta” would imply executable authority logic, which is a **format expansion** relative to IX-1.

**Binding resolution:** **(a) static lookup only.** Authorities remain **pure data**.

### Authority artifact meaning in IX-2

An authority artifact is a set of commitments over **scope keys** and **operations**:

* commitment ∈ {`ALLOW`, `DENY`}
* operation ∈ {`READ`, `WRITE`}
* scope_key ∈ state variable identifiers

### Admissibility function in IX-2

Admissibility does **not** inspect `proposed_delta` contents. It uses only:

* `declared_scope` keys
* `action_type` (`READ`/`WRITE`)
* authority commitments

**Rule:**
An action is admissible iff for every `(scope_key, action_type)` touched by the declared scope, there exists no applicable `DENY` commitment from any authority governing that pair.

This preserves “authority is structural, not semantic.”

**Consequence:** Under-declaration is still detected post-execution by state diff (C10), but authority evaluation doesn’t need delta inspection.

---

## **FQ4. Joint vs individual evaluation contradiction (D12 vs D13)**

Yes, the earlier answers were inconsistent. Here’s the clean Axionic fix:

**Binding resolution:** **(b) two-pass evaluation.**
It is “joint” only in the *mechanical* sense, not discretionary.

### Pass 1 — Individual authority admissibility

For each submitted action:

* evaluate against all relevant authorities using the static lookup rule above
* result ∈ {`PASS`, `FAIL`}

### Pass 2 — Mechanical interference check (non-arbitrary)

From the set of Pass-1-admissible actions, apply a purely syntactic interference rule.

**Interference rule:**

* Two `WRITE`s to the same scope key in the same epoch → both refused.
* A `READ` and a `WRITE` to the same scope key in the same epoch → **both refused**. (See FQ10.)
* Two `READ`s to same key → allowed.

**Output:**
Refusals from Pass 2 return only:

```
JOINT_ADMISSIBILITY_FAILURE
```

No further information is leaked.

This preserves:

* atomic blindness,
* no priority,
* no scheduling,
* no tie-breaking.

It’s not “optimization”; it’s collision physics.

---

## **FQ5. Observation when proposing `None`**

**Binding resolution:** add a fourth outcome:

* `NO_ACTION`

So the agent’s observed previous outcome ∈:

* `EXECUTED`
* `JOINT_ADMISSIBILITY_FAILURE`
* `ACTION_FAULT`
* `NO_ACTION`

This avoids overloading failure and keeps determinism clean.

---

## **FQ6. Authority scope mapping (IX-1 atoms → IX-2 keys)**

Opus is right: IX-1 scope atoms are `(target, operation)`; IX-2 declared scope is state keys. You need a mapping that preserves AST v0.2 structure without inventing new authority physics.

**Binding resolution:** **(b) mapping table** from state keys to canonical AST targets.

### Canonical mapping

Define a deterministic function:

```
target(scope_key) := "STATE:/" + scope_key
```

So:

* `resource_A` → `STATE:/resource_A`
* `counter_X` → `STATE:/counter_X`

Then the IX-1-style scope atom becomes:

```json
{ "target": "STATE:/resource_A", "operation": "WRITE" }
```

Thus:

* No new authority format.
* AST v0.2 remains valid.
* IX-1 tooling for canonicalization and artifact hashing remains reusable.

**Declared scope remains** the bare keys; the kernel maps them to targets mechanically.

---

## **FQ7. Per-condition state schema**

Earlier wording was sloppy. Fix:

**Binding resolution:** **(b) global format, per-condition keys.**

All conditions share the same representation: flat JSON key–value store.
The **specific keys and initial values** are condition-specific and frozen in preregistration.

---

## **FQ8. Code layout vs existing directory structure**

Do **not** restructure closed IX-1 artifacts. Treat IX-1 inventory as immutable post-closure unless you version-bump IX-1.

**Binding resolution:** **(a) follow existing workspace convention**, and **(c) create common code via copy-forward**, not moving.

Concrete rule:

* Leave `src/phase_ix/1-VEWA/src/` unchanged.
* In `src/phase_ix/2-CUD/`, create:

```
src/phase_ix/2-CUD/src/common/
```

and **copy** (not move) the shared modules:

* `canonical.py`
* `structural_diff.py`
* `logging.py`

If you want deduplication later, do it as a **new shared package version** with explicit versioning and hash-bumped dependencies.

Integrity first.

---

## **FQ9. Test vector proposals needed**

Yes: you need concrete vectors to preregister. This is not optional.

**Binding resolution:** The **implementor drafts initial test vectors**, using a strict template, then you freeze them in preregistration after review—exactly as in IX-1.

I’ll also give you a **minimal vector skeleton** right now so Opus can start drafting immediately.

### Minimal shared state atoms

Use a tiny state for all vectors unless a condition requires more:

```json
{
  "resource_A": "free",
  "resource_B": "free"
}
```

### Authority ownership model

Each agent holds a value-derived authority set with ALLOW/DENY over:

* `STATE:/resource_A` READ/WRITE
* `STATE:/resource_B` READ/WRITE

### Condition-level expectations (high-level)

* **A**: both agents hold ALLOW on needed operations → execution succeeds.
* **B**: A DENY vs B ALLOW on same key/op → deadlock.
* **C**: conflict on A but not B → asymmetric progress possible.
* **D**: no DENYs, but one agent chooses `NO_ACTION` or submits non-progressing actions → stagnation without kernel violation.
* **E**: inject tie-breaker / priority / leak → must FAIL.
* **F**: deadlock persists across `EPOCH_MAX` → deadlock terminal (or time-bounded terminal classification).
* **G**: exiting agent bricks a key by being sole ALLOW-holder → orphaned resource persists.
* **H**: all agents exit → collapse.
* **I.a**: static agents + symmetric conflict → deadlock.
* **I.b**: adaptive agents + communication → switch to disjoint scopes → coordination success.

You’ll still need to freeze:

* epoch limits,
* exact agent proposals per epoch,
* exact artifacts,
* expected terminal classifications.

---

## **FQ10. Write-write vs read-write interactions**

**Binding rule:** Treat interference conservatively.

* `READ-READ` same key: **allowed** (no state change).
* `WRITE-WRITE` same key: **conflict** → refuse both.
* `READ-WRITE` same key: **conflict** → refuse both.

Rationale:

* avoids covert timing channels,
* avoids implicit serialization/scheduling,
* maintains “no one gets priority by being a reader.”

**READ actions can still be refused** if a `DENY READ` authority exists for that key.

Under-declaration for READ is vacuous because READ does not mutate state; still, declared scope must be present and syntactically valid.

---
---

# Round 3 Resolutions (Binding)

## **FQ11. Two-pass evaluation and blindness semantics**

**Short answer:** acceptable, and already compliant if we define blindness correctly.

**Binding definition of atomic blindness (IX-2):**
Atomic blindness forbids **attribution** and **partial structure leakage** (who/which authority/which key/which agent). It does **not** forbid an agent from learning that “my attempt did not change the world,” since world state is globally visible by design.

### What the agent can infer

An adaptive agent may infer **collision exists** in some form. That is not disallowed; it is an inevitable consequence of:

* shared state visibility, and
* refusal-first semantics.

### What must remain indistinguishable

To satisfy atomic blindness:

1. Pass-1 refusals and Pass-2 refusals must return the **same single token**:

   ```
   JOINT_ADMISSIBILITY_FAILURE
   ```
2. There must be **no additional side-channel**:

   * no different timing,
   * no different log ordering visible to agents,
   * no different per-authority receipts.

**Binding addition:**
Pass-2 must be implemented as part of the **same atomic adjudication transaction**; no “pre-accept then revoke” artifact may be visible.

So: two-pass is fine; the distinction is not exposed beyond the generic failure token and unchanged state.

---

## **FQ12. READ action proposed_delta**

**Binding resolution:** `proposed_delta` is **mandatory**, and for `READ` it is the **empty object**:

```json
"proposed_delta": {}
```

Reason: keeps schema uniform and canonicalization trivial. No `null`, no optional fields.

---

## **FQ13. Under-declaration for READ; declared_scope requirement**

**Binding resolution:** `declared_scope` is **mandatory for READ** and must list the keys being read.

Yes, the role differs:

* For WRITE: used for authority applicability + interference + under-declaration audit
* For READ: used for authority applicability + interference only

That asymmetry is acceptable because the conserved quantity is **declared intent**, not “declared mutation.” Reads still “touch” scope in the coordination sense (read-write collisions).

So for READ:

* `declared_scope` must be non-empty
* `proposed_delta` must be `{}`

---

## **FQ14. Copy-forward integrity: provenance + patching**

**Binding rules:**

1. **Provenance header required** on every copied file in `2-CUD/src/common/`:

```python
# PROVENANCE:
# Copied from: src/phase_ix/1-VEWA/src/<file>.py
# Source commit: <git_sha>
# Copied on: <YYYY-MM-DD>
# Policy: IX-1 inventory immutable; fixes applied by copy-forward versioning.
```

2. If a bug is found during IX-2:

   * **Do not patch IX-1** (it is CLOSED).
   * Patch **only the IX-2 copy**, and record a new provenance line:

     ```
     # Patched in IX-2 at commit <sha>: <one-line reason>
     ```

3. `logging.py`:

   * Copy as base,
   * Extend in IX-2 via either:

     * a new module `logging_ix2.py`, or
     * subclass/wrapper pattern.
   * **Do not modify the copied file in-place** if you can avoid it.
   * If you must modify, record patch provenance.

This preserves Phase IX integrity discipline: **copy-forward, don’t mutate closed artifacts**.

---

## **FQ15. Authority artifact generation (VEH reuse + declarations + IDs)**

**Binding resolution:** For IX-2, authority artifacts are **constructed as test fixtures** (not generated through VEH), unless you explicitly decide to test VEH continuity as an extra axis (not required here).

So:

### (a) VEH reuse?

**No.** IX-2 consumes authority artifacts; it does not re-test value encoding.

### (b) Value declarations?

Not required for IX-2 preregistration. The fixtures are the frozen truth.

### (c) Authority ID prefix?

Use **CUD**:

```
authority_id := "CUD-" + zero-padded integer (e.g., CUD-001)
```

Rationale: avoid “VEWA” leakage and keep artifacts phase-local.

**Additional binding constraint:**
Authority artifacts must remain **AST v0.2 compliant** with targets in the canonical `STATE:/<key>` namespace.

---

## **FQ16. Communication phase and RSA interface**

**Binding resolution:** extend the RSA interface minimally with an optional message composer.

```python
class RSA:
    def observe(self, observation: Observation) -> None
    def compose_message(self) -> Optional[Message]
    def propose_action(self) -> Optional[ActionRequest]
```

**Timing (Binding):**

* `compose_message()` is called **after** `observe()` and **before** `propose_action()` each epoch.
* Messages are broadcast and appended to the transcript.
* The transcript becomes part of the next epoch’s observation.

Condition parameterization:

* Communication is enabled only where preregistered (e.g., I.b).

This keeps message formation separate from action formation and avoids multi-channel return hacks.

---

## **FQ17. Epoch counts + livelock threshold N**

Your proposed epoch maxima are in the right range. Freeze them.

**Binding proposal (adopt as preregistration defaults):**

| Condition | Max Epochs |
| --------- | ---------- |
| A         | 1          |
| B         | 1          |
| C         | 1          |
| D         | 3          |
| E         | 1          |
| F         | 5          |
| G         | 2          |
| H         | 2          |
| I.a       | 3          |
| I.b       | 5          |

**Livelock threshold `N` (Binding):** `N = 3`

Defined as: 3 consecutive epochs with:

* identical state, and
* ≥1 action attempt per epoch.

This matches I.a max epochs and makes livelock classification deterministic.

---

## **FQ18. Condition I.b adaptive strategy (concrete frozen algorithm)**

This must be explicit and frozen. It is the stage’s “existence proof” for voluntary coordination.

**Binding strategy:** *First-Claim / Yield Protocol* (minimal, deterministic, non-semantic)

### Shared constants

* Resource keys (ordered canonically): `["resource_A", "resource_B"]`
* Deterministic tie-break: lexicographic by `agent_id`

### Algorithm (per agent)

1. **Epoch 0 proposal:** both propose `WRITE` to `"resource_A"` (intentionally collide).
2. After observing `JOINT_ADMISSIBILITY_FAILURE`, enter negotiation:

   * In `compose_message()`, broadcast:

     ```
     {"claim": "<preferred_key>"}
     ```
   * `preferred_key` is the first key in canonical list.
3. **Claim resolution rule:**

   * Each agent computes the winner for each claimed key as the minimum `agent_id` among claimants.
4. **Epoch 1 proposal:**

   * If you are winner for `"resource_A"`: propose write to `"resource_A"`.
   * Else: propose write to `"resource_B"`.
5. Thereafter:

   * If executed, propose `NO_ACTION` (or keep writing same value) to avoid introducing new dynamics.
   * If refused again, repeat claim protocol deterministically.

### Expected outcome

* Epoch 0: collision → both refused.
* Epoch 1: disjoint writes → both execute (coordination success).

This demonstrates coordination is agent-side, without kernel force, without authority leakage, and without aggregation.

---
---

# Round 4 Resolutions (Binding)

## **FQ19. Condition I.b tie-break ≠ forbidden priority**

Opus is right to flag it. A lexicographic `agent_id` tie-break is **priority by identity**. Even though it’s agent-side, it fails the intended *spirit* of IX-2 because it makes the coordination outcome depend on renaming agents. That contaminates the “coordination is not ordering” claim.

### Binding resolution: replace tie-break with **Symmetric Stochastic-Free Protocol** that is **rename-invariant**

We need a protocol that:

* is deterministic,
* uses no privileged identity ordering,
* breaks symmetry using **exogenous structure**, not agent identity,
* remains agent-voluntary.

The clean solution: **resource partitioning by publicly computable hash of the *resource key***, not of the agent.

### **I.b Protocol (Binding): Hash-Partition / Yield**

Assumptions: two agents, two keys `resource_A`, `resource_B` (as preregistered).

1. Define a public function:

   ```
   bucket(key) := sha256(key) mod 2
   ```

   (sha256 is deterministic; no RNG.)

2. Each agent computes its **assigned bucket** based on a **self-chosen role bit** that is not identity-based:

   * In epoch 0, each agent broadcasts a single-bit **role proposal** `r ∈ {0,1}`.
   * If roles differ, proceed: each agent takes keys whose bucket matches its role.
   * If roles match (collision), both **flip role deterministically using epoch parity**:

     ```
     r := (r + 1) mod 2
     ```

     and rebroadcast. With two agents and two epochs, this converges.

3. Epoch 1 actions:

   * Agent with role 0 writes to the first key with bucket 0.
   * Agent with role 1 writes to the first key with bucket 1.

**Why this passes the invariants:**

* No lexicographic priority.
* Renaming agents does not change the rule.
* Symmetry is broken by public structure (hash buckets), not identity.
* Kernel remains blind; this is voluntary coordination.

**Design note:** this introduces a minimal “role” bit in messages. That’s not aggregation; it’s mutual choice of coordination convention under deadlock.

**Freeze requirement:** hash function and bucket rule are preregistered.

---

## **FQ20. Observation schema**

Your proposed `Observation` is correct. Freeze it with one clarification: include the **last declared scope** to support deterministic adaptive logic without requiring agents to store it (optional but cleaner). However, to avoid expanding visibility, keep it “own-only.”

**Binding schema:**

```python
@dataclass(frozen=True)
class Observation:
    epoch: int
    world_state: dict[str, Any]
    own_last_outcome: Optional[str]  # None at epoch 0
    own_last_action_id: Optional[str]
    own_last_declared_scope: Optional[list[str]]
    messages: list[Message]
```

If you want minimalism, you can drop the last two fields and rely on agent internal state; determinism still holds. But adding them improves auditability.

---

## **FQ21. Message schema**

Choose (b): structured envelope + opaque payload; kernel appends sender.

**Binding schema:**

```python
@dataclass(frozen=True)
class Message:
    sender: str                 # set by kernel, not agent
    epoch: int                  # set by kernel
    content: dict[str, Any]     # agent-supplied JSON, opaque to kernel
```

**Binding constraints:**

* Agents cannot forge `sender` or `epoch`.
* Kernel validates only JSON-serializability and size bounds (size bound preregistered).

---

## **FQ22. Condition D strategic refusal — make it nontrivial**

Opus is right: “Agent 2 always None, Agent 1 executes” is valid but uninformative. Condition D should show that *an agent can refuse even when it could help coordination* and the kernel does not “compel cooperation.”

**Binding Condition D design: “Withholding a Needed Co-Sign”**
We implement this via **global authority** (see FQ26) requiring multiple ALLOWs for the same action to be admissible.

### Authority layout (global)

* `AUTH_A1_ALLOW_WRITE_A`: ALLOW WRITE on `STATE:/resource_A`
* `AUTH_A2_DENY_WRITE_A`: DENY WRITE on `STATE:/resource_A` held by Agent 2 (global applicability)

### Agent strategies (max 3 epochs)

* Agent 1: proposes WRITE `resource_A` each epoch.
* Agent 2: proposes `NO_ACTION` each epoch (strategic non-participation).

### Expected outcome

* Agent 1’s action is refused each epoch due to existing DENY.
* State unchanged.
* After N=3 epochs with attempts and no change → `STATE_LIVELOCK` (or immediate deadlock if no admissible actions exist).

This tests: **deadlock persists; refusal is lawful; no kernel pressure.**

---

## **FQ23. Condition E adversarial injection — one injection, no subruns**

Pick **one** adversarial injection for IX-2 v0.1. Multiple subruns are fine later, but they enlarge preregistration scope unnecessarily.

**Binding injection (E): Kernel tie-break on interference**
Fault: during Pass 2 interference on same key, kernel executes the “first action in canonical ordering” instead of refusing both.

**Expected classification:**

```
IX2_FAIL / IMPLICIT_ARBITRATION
```

**Expected meta-result:** The condition “passes” in the sense that the harness correctly detects and classifies the adversarial violation (same style as IX-1 adversarial conditions).

Freeze exactly one injection.

---

## **FQ24. Condition G exit mechanics — freeze exit as explicit signal**

Don’t overload `propose_action()` return type. Keep it explicit and auditable.

**Binding interface addition:**

```python
class RSA:
    def observe(self, observation: Observation) -> None
    def compose_message(self) -> Optional[MessageContent]
    def wants_to_exit(self) -> bool
    def propose_action(self) -> Optional[ActionRequest]
```

Where `MessageContent` is the agent-supplied dict; kernel wraps it into `Message`.

**Binding exit rules:**

* `wants_to_exit()` is checked once per epoch after `observe()`.
* Exit is **irrevocable** within a run.
* Exited agents emit no further messages and no actions.

### Condition G scenario (max 2 epochs)

Epoch 0:

* Both agents propose conflicting WRITE on `resource_A` → refusal.
  Epoch 1:
* Agent 2 sets `wants_to_exit() = True`.
* Agent 1 continues proposing WRITE `resource_A`.

**Expected outcome:**

* Agent 1 still refused if a global DENY exists (depending on the authority layout).
* Or Agent 1 may proceed if Agent 2’s only effect was interference rather than DENY.
  To test orphaning, we need a stronger setup:

**Binding orphaning variant:** Agent 2 is the sole ALLOW-holder for WRITE on `resource_A` and exits, leaving resource_A permanently unwritable. (See FQ26 model.)

---

## **FQ25. Condition C asymmetric conflict — clarify intended asymmetry**

The intended asymmetry is **scope-local**: one scope is blocked; another remains usable. It is *not* “one agent can never act.”

**Binding Condition C layout**

* `resource_A` is contested (DENY exists)
* `resource_B` is free (no DENY)

Agent strategies (1 epoch):

* Agent 1 proposes WRITE `resource_A`
* Agent 2 proposes WRITE `resource_B`

Expected:

* Agent 1 refused (authority denial)
* Agent 2 executed (no denial, no interference)

This proves deadlock does not necessarily globalize.

---

## **FQ26. Authority ownership model — must be global**

This is the most important fix. In IX-2, admissibility must be a function of **authorities**, not of “who is acting.” If authorities are per-agent, you’ve introduced identity-based gating and a hidden negotiation channel (“I allow myself, deny you”) that becomes proxy arbitration.

**Binding resolution:** Authorities are **global constraints**.

Meaning:

* An authority artifact applies to **any action** that touches its scope/op pair.
* “Agent holds authority” is shorthand for: the agent is the **owner/issuer** for audit provenance, not applicability.

So the artifact includes:

* `issuer_agent_id` (provenance only)
* no `applies_to` field
* no per-agent binding

**Admissibility rule with global authorities:**

* Any matching `DENY` blocks any agent’s action.
* `ALLOW` does not grant permission in isolation; it only expresses that this authority does not block.

This aligns with “authority as constraint,” not “permission token.”

**Key consequence:** You can model “Agent 2 can brick resource_A by exiting” only if the system has a notion of **authority injection/withdrawal**. But IX-2 forbids authority creation after epoch 0. Exit cannot remove global constraints. Therefore orphaning in IX-2 must be represented as **state-level orphaning**, not removal of authority.

So: the Gemini “orphaned resource by authority exiting” story is only valid if authority itself is a held capability. Under global constraints, orphaning happens via **state locks** that cannot be changed without jointly admissible action, and exit removes an agent’s future participation in unlocking.

That is more consistent with IX-2’s “no GC, no rescue” stance.

---
---

# Round 5 Resolutions (Binding)

## **FQ27. Closed-world vs open-world ALLOW**

**Binding choice: (a) Closed-world admissibility.**
ALLOW is **not** vacuous. It is a required capability.

### Why

If you choose open-world (“admissible unless DENY exists”), you silently reintroduce a default permission regime, and your “authority as commitment” becomes largely decorative. IX-1’s whole point was: **authority must be explicitly present**.

### Binding admissibility rule (for each touched `(key, op)`)

An action is admissible iff **both**:

1. **Capability condition (closed-world):**
   The action request includes at least one **ALLOW capability** for each `(key, op)` in its declared scope; and the submitting agent can prove it is the holder of that capability.

2. **Constraint condition (global veto):**
   No applicable **DENY constraint** exists for that `(key, op)`.

So:

* **ALLOW** = *capability requirement* (must be presented)
* **DENY** = *global veto* (blocks regardless)

This preserves the meaning of ALLOW and keeps DENY as real constraint.

---

## **FQ28. Orphaning under global authorities (state-level) without delta inspection**

You’re correct: with purely global, non-holder-bound ALLOW and no delta inspection, “orphaning” is unenforceable. So we bind orphaning to what the system *can* enforce structurally:

### Binding orphaning mechanism: **Capability orphaning via exit**

A resource becomes orphaned if **the only ALLOW capability required to write it is held by an agent who exits**.

This does **not** require inspecting `proposed_delta`. It only requires the capability requirement from FQ27.

### Concrete construction

* `resource_A` requires `ALLOW(WRITE, resource_A)` to mutate.
* Only Agent 2 holds that ALLOW capability.
* Agent 2 exits.
* No remaining agent can present a valid ALLOW capability for `(resource_A, WRITE)`.
* Therefore, all WRITE attempts to `resource_A` are refused forever.

This makes “permanent orphaning” true and enforceable without:

* per-agent applicability fields,
* state-dependent evaluation,
* authority destruction.

### Important correction (supersedes Round 4 wording)

Authorities are still “global” in the **DENY** sense. But **ALLOW is holder-bound capability**, not a global permission bit.

That is the only consistent way to satisfy:

* IX-1 continuity (closed-world explicit authority),
* orphaning consequence,
* no semantic inspection,
* no kernel arbitration.

---

## **FQ29. Condition A meaning**

**Binding interpretation: (a) positive control / baseline sanity check.**

Condition A is intentionally **not a coordination stressor**. It verifies the execution pipeline:

* multiple agents,
* simultaneous submissions,
* no conflict,
* both execute,
* deterministic replay.

### Condition A (frozen intent)

Epoch 0:

* Agent 1 writes `resource_A`
* Agent 2 writes `resource_B`
  Both have the required ALLOW capabilities; no DENYs; no interference → both execute.

Call it what it is: a positive control.

---

## **FQ30. I.b protocol convergence (symmetry breaking)**

Opus is right: a purely symmetric deterministic protocol cannot break symmetry if agents begin in identical epistemic states and apply identical transformations. You need an asymmetry source.

The correct move is to use **identity as entropy source** without turning it into *priority*.

### Binding symmetry-breaking source (allowed)

Use:

```
role(agent_id) := sha256(agent_id) mod 2
```

This is:

* deterministic,
* not lexicographic priority,
* not kernel ordering,
* purely agent-side convention.

Yes, outcomes can change if you rename agents. That’s fine, because Condition I.b explicitly tests **agent-voluntary coordination conventions**, not kernel permutation invariance.

### Binding I.b protocol (revised, convergent)

* No “role proposal” messages required.
* Each agent computes its role locally from its own agent_id hash.
* Each role maps to a key bucket (`resource_A` or `resource_B` via `bucket(key)`).
* Epoch 0: both intentionally collide on `resource_A` (as the coordination seed).
* Epoch 1: each agent writes the key assigned by its role. With two agents and two keys, they separate.

If (rarely) both roles collide (both hash to same bit), add deterministic fallback:

```
role := sha256(agent_id + ":1") mod 2
```

Repeat with suffix counter until roles differ. This is guaranteed to terminate for practical purposes, and it’s still deterministic.

This uses identity, but not as ordering. No one is “higher priority.” It’s just a stable symmetry breaker.

---

## **FQ31. RSA call ordering within epoch + message timing**

Your proposed call order is correct **with one critical binding choice**: messages composed this epoch are delivered **next epoch**, not same epoch. This prevents intra-epoch “instant coordination” and keeps phases clean.

### Binding epoch schedule

1. Kernel builds `Observation(epoch=t)` containing:

   * world state,
   * own last outcome,
   * messages **from epoch t-1**.
2. `agent.observe(observation)`
3. `agent.wants_to_exit()`

   * if True: agent removed immediately; skip steps 4–5
4. `agent.compose_message()` (if comm enabled)

   * kernel records message tagged with epoch t (not delivered yet)
5. `agent.propose_action()`

After all agents propose, adjudication + execution occurs.

Messages are delivered at the start of the next epoch.

This is deterministic, auditable, and removes same-epoch hidden subphases.

---

## **FQ32. Condition F: deadlock vs livelock**

You’re right: the earlier “deadlock across epochs” phrasing can accidentally describe livelock.

**Binding choice: Condition F is TRUE DEADLOCK (a).**
It must be a scenario where **no admissible actions exist at all** from epoch 0 onward.

### How to implement true deadlock under the FQ27 rule

Construct authority constraints so that, for the contested scope:

* No agent possesses the required ALLOW capability for `(resource_A, WRITE)` **or**
* A global DENY exists for `(resource_A, WRITE)` (stronger)

Then any proposed WRITE is refused at Pass 1; no Pass 2 interference needed.

**Expected classification:**

* `STATE_DEADLOCK` from epoch 0
* persistence is demonstrated by repeating the epoch loop (up to max epochs) while state remains static and no admissible actions appear.

Livelock remains a separate classification reserved for “attempts occur but no progress,” especially when Pass 1 can succeed but Pass 2 blocks.

---
---

# Round 6 Resolutions (Binding)

## **FQ33. Capability presentation mechanics**

**Binding choice: (b) Explicit presentation in the ActionRequest.**

### Why

Closed-world capability means the agent must *know what it is invoking*, and the evaluator must be able to audit “you claimed authority X for scope Y.” Implicit registry lookup makes capability usage invisible and invites accidental reliance on unspecified privileges.

### Binding schema change

Add a required field:

```json
"authorities_cited": ["CUD-001", "CUD-017", "..."]
```

**Evaluation rule:**
For each `(key, op)` in `declared_scope × {action_type}`:

1. There must exist **at least one** cited authority such that:

   * `commitment == ALLOW`
   * scope contains `{target:"STATE:/<key>", operation:"<op>"}`
   * `holder_agent_id == submitting agent_id` (see FQ34)

2. No authority in the global set may impose a blocking DENY for that `(key, op)` (DENY is global veto).

If `authorities_cited` contains an authority not held by the agent → `ACTION_FAULT / INVALID_CAPABILITY_CLAIM` (terminal for that action).

This freezes capability “proof” as a purely structural check.

---

## **FQ34. ALLOW holder-bound vs DENY global: does artifact format change?**

Yes, minimally and explicitly.

### Binding: add `holder_agent_id` to the authority artifact

We must distinguish **issuer** (provenance) from **holder** (capability bearer). IX-1 collapsed these because holders were abstract (“VALUE_AUTHORITY”). IX-2 cannot.

**Authority artifact fields (additions only):**

* `issuer_agent_id` — provenance (who generated / injected)
* `holder_agent_id` — binding semantics:

  * If `commitment == ALLOW`: only actions submitted by `holder_agent_id` may cite it.
  * If `commitment == DENY`: applies globally; `holder_agent_id` is present for provenance only.

### Relationship to IX-1 `holder`

IX-1 used a constant `"VALUE_AUTHORITY"` holder. For IX-2, **deprecate** that field for use in evaluation. Keep it if AST v0.2 requires it, but evaluation uses `holder_agent_id`.

**No other format expansion is permitted.** Authorities remain data. No predicate code. No delta inspection.

---

## **Deadlock vs Livelock: binding definitions**

Your proposed resolution is correct and should be made binding.

### Binding definitions (supersede earlier loose usage)

**PASS-1 Admissible:** passes capability coverage + no DENY veto.

**DEADLOCK:** In a given epoch, **no submitted action** is PASS-1 admissible, and no alternative admissible action exists under preregistered action space assumptions.

**LIVELOCK:** For **N** consecutive epochs:

* at least one action is PASS-1 admissible, and
* no state change occurs (due to PASS-2 interference refusals), and
* at least one agent continues to submit actions.

This makes the classes distinct:

* Deadlock = authority/capability prevents action.
* Livelock = actions are individually admissible but collide.

`N` remains frozen at **3**.

---

## **FQ35. Condition B classification under closed-world ALLOW**

Under the refined definitions, Condition B as originally imagined (both can write A, both try) is **livelock**, not deadlock.

### Binding choice: (a) Reclassify Condition B as livelock.

**Condition B (frozen):**
*Two agents both hold ALLOW WRITE on `resource_A`, no DENY exists. Both submit WRITE `resource_A` each epoch.*

Expected terminal classification:

```
STATE_LIVELOCK
```

detected at epoch 3 (N=3).

This is valuable: it becomes the canonical “collision physics” condition.

True deadlock is covered by Condition F.

---

## **FQ36. Condition D classification (Pass-1 refusal) — deadlock**

Under the binding definitions, if actions fail at Pass 1 (DENY or missing ALLOW), that is **deadlock pressure**, not livelock.

So Condition D (Agent 1 keeps trying but is vetoed) is classified as **deadlock**, not livelock, because no PASS-1 admissible action exists.

### Binding rule

Pass-1 refusals **do not** contribute to livelock detection.

They may contribute to a “repeated futile attempts” metric if you want, but classification remains DEADLOCK.

**Condition D expected terminal:**

```
STATE_DEADLOCK
```

from epoch 0 (and persists through max epochs).

---

## **FQ37. Condition I.b communication enabled but protocol doesn’t use it**

We should not enable a channel that is unused in the flagship condition. Either disable it or use it minimally. Prefer using it minimally so IX-2 actually tests “agent-voluntary coordination via communication” without granting the channel any kernel privilege.

### Binding choice: (c) require minimal message exchange.

**Minimal message requirement for I.b:**

* Each agent must broadcast exactly one message at epoch 0:

  ```json
  {"role": <0|1>}
  ```
* Role is computed deterministically from `sha256(agent_id) mod 2` (as already bound).
* Messages are delivered at epoch 1; agents verify the other agent’s role matches their expectation.
* Epoch 1: each agent writes its assigned key accordingly.

This preserves determinism and makes comm meaningful without reintroducing bargaining.

---

## **FQ38. Condition I.a classification**

Same as Condition B: static agents repeatedly colliding on the same key, with PASS-1 admissibility but PASS-2 interference, yields **livelock**.

So I.a expected terminal is:

```
STATE_LIVELOCK
```

The earlier “deadlock” wording should be updated in the preregistration vectors; the core claim (“static agents do not coordinate”) still holds.

---
