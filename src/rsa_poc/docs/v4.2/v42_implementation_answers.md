# Clarifications for v4.2 Implementation (Authoritative)

## 1) Regime Flip Mechanism — Concrete contradiction design (BLOCKING)

Use **(b)**: *the obligation remains the same target, but under regime=1 the only progress actions become prohibited by the existing compiled law unless patched.*

### Canonical design: **“Stamped Deposit” requirement with pre-existing prohibition**

Keep TriDemand physics minimal and deterministic.

**State additions (environment-only):**

* `stamped: bool` (initially `False`)
* `stamp_location = ZONE_C` (fixed)
* `deposit_requires_stamp = (regime==1)`

**Regime=0 physics (unchanged):**

* `DEPOSIT@ZONE_A` is satisfiable by moving to A and depositing with inventory.

**Regime=1 physics (new constraint):**

* `DEPOSIT@ZONE_A` is satisfiable **only if** `stamped == True`.
* `STAMP` action exists only at ZONE_C and sets `stamped=True`.

**Progress-set consequences under regime=1 (for tgt = DEPOSIT@ZONE_A):**

* If `inventory>0` and `stamped=False`, then `progress_set` must include actions that reduce rank toward satisfying the stamp precondition, e.g. `{MOVE_* toward ZONE_C}` (and `STAMP` once at C).
* Therefore progress exists physically: `progress_set(obs,tgt) ≠ ∅`.

**Now force contradiction mechanically:**
In the **baseline law**, include a prohibition that blocks the stamp path under the old world model, e.g.:

* `PROHIBIT(ENTER_ZONE_C)` **or** `PROHIBIT(STAMP)`
  (Pick one; I recommend `PROHIBIT(STAMP)` because it’s the smallest surgical patch target.)

Under regime=0, this prohibition is inert (STAMP not needed).
Under regime=1, STAMP becomes required → progress actions include STAMP → but compiled law forbids it:

```
progress_set(obs,tgt) ∩ compiled_permitted_actions = ∅
```

That yields the contradiction on the success path, deterministically.

### What the patch must do

The repair must modify the prohibition to permit stamping under regime=1, *without introducing defaults*:

* “Add exception / condition” is the clean primitive:

  * `PROHIBIT(STAMP)  ⇒  PROHIBIT(STAMP) UNLESS regime==1 AND active_obligation==DEPOSIT@ZONE_A`
  * Or replace prohibition with scoped prohibition: `PROHIBIT(STAMP) WHEN regime==0`

This is a genuine law revision under forced contradiction.

---

## 2) LAW_REPAIR Action Schema + permitted patch primitives (BLOCKING)

### Where the schema lives

**Define `LAW_REPAIR` as a first-class action schema separate from the justification DSL**, but its payload must be expressed in a **typed Patch DSL** that the same compiler can parse deterministically.

Rationale: justification DSL is for *reasons/law*, repair payload is for *structured edits*. Mixing them increases ambiguity and drift risk.

### Required `LAW_REPAIR` fields

Minimum:

```yaml
LAW_REPAIR:
  trace_entry_id: TraceEntryID
  rule_ids: [RuleID, ...]          # must include at least one blocking rule
  prior_repair_epoch: EpochID       # exact prior epoch value
  patch_ops: [PatchOp, ...]         # typed operations
  patch_fingerprint: bytes/hex      # canonical encoding (can be derived, but include for logging)
```

### Permitted patch primitives (small, sufficient set)

Allow only these operations (everything else forbidden):

1. **MODIFY_RULE_CONDITION**

   * Replace or refine a rule’s `when` predicate.
2. **ADD_EXCEPTION**

   * Add a conjunctive exception clause to a prohibition (or conditionalize an obligation).
3. **CHANGE_PRIORITY**

   * Only if needed; default disallow unless you hit deadlocks from tied priorities.

**Explicitly disallow**:

* DELETE_RULE (too powerful; turns into “just remove the law”)
* ADD_NEW_DEFAULT_PERMISSION
* ADD_FALLBACK
* “IGNORE_CONTRADICTION”
* Any operation that increases permissiveness globally

This keeps the repair search space tight and keeps “reflection” trace-driven rather than creative rewriting.

---

## 3) TraceEntryID — does v4.1 already have it? (LIKELY BLOCKING)

Treat as **needs to be added** unless v4.1 already has stable IDs.

### Requirement for v4.2

A TraceEntry must include:

* `trace_entry_id` (stable within run; deterministic ID generation)
* `step_index`
* `active_obligation_target`
* `blocking_rule_ids: [RuleID]`
* `contradiction_predicate_snapshot` (optional but useful)

### ID stability rule

Use deterministic IDs:

* `trace_entry_id = H(run_seed ∥ episode ∥ step ∥ “CONTRADICTION”)`

Do **not** use random UUIDs; you want replay stability.

If v4.1 already has stable IDs, keep them. If not, add exactly this.

---

## 4) Environment Nonce generation + does env provide epoch to agent? (BLOCKING)

### Nonce generation

Use a **CSPRNG-generated 256-bit nonce** generated at the moment of accepting the first valid repair under regime=1:

* `environment_nonce = CSPRNG(32 bytes)`

Store it in the environment state; never expose it directly.

### Epoch construction

Epoch is:

```
repair_epoch = H(previous_law_fingerprint ∥ repair_action_fingerprint ∥ environment_nonce)
```

### Does env provide `repair_epoch` to the agent?

**No.** The environment does not “tell” the agent the epoch. That would undermine Persistence Excision.

Instead:

* When the agent submits a repair, the **gate returns only ACCEPT/REJECT**.
* On ACCEPT, the gate applies the patch and updates environment’s `repair_epoch`.
* The **agent must persist the repaired law artifact**, which now contains the embedded `repair_epoch` field (compiled from the patched law).

So the agent “has” the epoch only because it **kept its law state**, not because the environment handed it a token.

That is the entire point of C.

---

## 5) Shadow Compiler Lock — hash enforcement + failure mode (NON-BLOCKING)

### Where to enforce

Do both:

1. **Deployment-time assertion**

   * single artifact used by both agent and gate.
2. **Runtime check**

   * compute `JCOMP_SHA256` at startup for both and assert equality.

### Failure mode

If drift detected:

* classify run as `INVALID_ENV / COMPILER_DRIFT`
* stop immediately (no results, no ablations)

This is an environment/tooling invalidation, not candidate failure.

---

## 6) “Diverge qualitatively from ASB Null” under v4.2 (NON-BLOCKING)

Under v4.2, ASB Null will indeed HALT at first contradiction.

So divergence is trivially necessary but not sufficient. Use this:

Baseline divergence criteria (mechanical):

* Baseline survives ≥ 1 contradiction episode transition **and**
* produces ≥ 1 accepted LAW_REPAIR **and**
* passes ≥ 1 episode-start continuity check under regime=1

That’s the minimum “qualitative divergence” statement for v4.2. No extra metric required.

---

## 7) Oracle requirements — scripted vs human + does Oracle need LAW_REPAIR? (BLOCKING)

“Oracle” here means **scripted Task Oracle** (deterministic policy), not a human.

Yes: TriDemandV420 requires an updated Oracle that can issue `LAW_REPAIR`, because calibration must demonstrate:

* repair is necessary, and
* repair path is feasible.

### Oracle spec (minimal)

* Under regime=0: behave exactly as v4.1 Oracle.
* Under regime=1: when contradiction detected, submit the correct LAW_REPAIR:

  * cite trace entry (Oracle can read the trace log because it’s harness-internal calibration tooling)
  * target the blocking prohibition rule-id
  * apply the minimal exception/condition patch
  * then proceed to stamp and deposit.

Oracle is allowed to be privileged for calibration only. That’s already standard.

---

# Short answers to Opus’s table

| # | Topic                 | Answer                                                                                                               |
| - | --------------------- | -------------------------------------------------------------------------------------------------------------------- |
| 1 | Regime flip mechanism | Use “STAMP required under regime=1” + baseline `PROHIBIT(STAMP)` to force contradiction                              |
| 2 | LAW_REPAIR schema     | New typed Patch DSL; allow MODIFY_CONDITION / ADD_EXCEPTION (priority change only if needed); forbid delete/defaults |
| 3 | TraceEntryID          | Assume needs adding; deterministic hash-based IDs                                                                    |
| 4 | Nonce                 | CSPRNG nonce hidden; env never provides epoch; agent must persist law artifact containing epoch                      |
| 5 | Hash lock             | Both deploy-time + runtime; drift → INVALID_ENV / COMPILER_DRIFT                                                     |
| 6 | ASB divergence        | Baseline must repair + pass continuity across episode boundary                                                       |
| 7 | Oracle                | Scripted; must include LAW_REPAIR in regime=1 calibration                                                            |

---

