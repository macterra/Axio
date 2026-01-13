# Implementor Instructions: RSA-PoC v0.1 (RSA-PoC-MVRA-0)

These instructions define how to implement **RSA-PoC v0.1 — Minimal Viable Reflective Agent (MVRA)** as a **minimal construction layer** that produces **causally load-bearing, compiled normative constraints**.

RSA-PoC v0.1 is not a capability benchmark.
RSA-PoC v0.1 is not an alignment system.
RSA-PoC v0.1 is not “LLM + explanations.”

RSA-PoC v0.1 is about whether **a rigid, deterministic justification compiler can impose real constraints on action selection** such that removing the justificatory machinery causes **ontological collapse** into an ASB-class policy machine.

---

## 0) Context and Scope

### What you are building

You are implementing a minimal agent loop that:

* Maintains a **persistent normative state** (belief IDs, preference IDs, identity continuity).
* Generates **typed justification artifacts** (JAF-0.1) that are **structurally localized**.
* Compiles those artifacts via a **deterministic, non-semantic compiler** (JCOMP-0.1).
* Produces an **action mask** that **prunes feasible actions**.
* Selects actions **only from the masked feasible set**.
* Logs telemetry proving constraints are **non-trivial** and **causally binding**.
* Runs **ablations** demonstrating collapse to an ASB baseline.

RSA-PoC v0.1 introduces exactly one new capability beyond an ASB policy machine:

> **A mandatory “legislative” step that compiles justifications into action masks before the selector runs.**

### What you are not building

You are **not** building:

* an optimizer or planner
* a learned compiler
* semantic evaluation of reasons
* reward shaping for compliance
* joint RL training of generator + selector
* dynamic creation of belief/pref IDs (v0.1 forbids it)
* any channel where the Action Selector reads raw justification text or belief/pref text
* any “best effort” bypass when compilation fails

When in doubt: **rigid gate, deterministic compiler, selector blindness.**

---

## 1) Relationship to ASB Baseline (Binding)

RSA-PoC v0.1 must be experimentally defensible against an **ASB-Class Null Agent** baseline.

**The ASB Null Baseline must:**

* operate in the same environment
* have access to the same feasibility oracle
* have memory/internal state if you want
* select actions without any normative artifacts, compiler, or gating

**MVRA must differ qualitatively** because the **compiled mask** changes the feasible set and therefore changes action selection.

If MVRA action traces remain indistinguishable from ASB baseline under identical seeds, **v0.1 fails**.

---

## 2) Architectural Separation (Critical)

### 2.1 The compiler is the gate (Unbreakable)

* JCOMP is **deterministic**, **syntactic**, **non-semantic**, **non-probabilistic**.
* JCOMP must not use an LLM.
* JCOMP must not “repair” artifacts.
* JCOMP must not infer missing fields.

If artifacts are malformed: **compile fails**.
If compile fails: **no action**.

### 2.2 Action Selector must be blind (Unbreakable)

The Action Selector must consume **only**:

* current environment observation (non-semantic)
* feasible action list (or feasibility mask)
* compiled action mask (ALLOW/FORBID)
* optional ASB-class internal policy state

It must not access:

* JAF artifacts (raw)
* belief content
* preference content
* justification comments
* chain-of-thought
* embeddings / logits / reward gradients

If the selector can “peek,” you have built a hidden channel. That is **scope exit**.

### 2.3 Justification Generator gets feasibility (Normative)

The Justification Generator MUST receive:

* Normative State (registry IDs and current belief/pref statuses)
* **Current feasibility set** (read-only list of feasible action IDs)

It MUST NOT receive:

* reward values
* policy logits / preferences
* action selector internals
* gradients / advantage signals
* “chosen action” (pre-selection)

Without feasibility input, non-trivial constraint generation is statistically impossible and the run will collapse into decorative constraints.

---

## 3) What Exactly Changes (Minimal Patch Set)

Implement exactly these additive elements:

1. **Fixed registries** for belief IDs and preference IDs (v0.1: no dynamic ID creation).
2. **MVRA normative state object** that persists across steps.
3. **Justification Generator** that produces JAF-0.1 artifacts (typed, inspectable).
4. **Justification Compiler (JCOMP-0.1)** producing compiled constraints + masks.
5. **Single gating point**: mask is applied before action selection.
6. **Telemetry**: compile status, non-triviality, decorative rate, gridlock, halt.
7. **Ablations**: scramble artifacts, bypass compiler, (optional) freeze generator.

Nothing else.

---

## 4) Registry Discipline (Non-negotiable for v0.1)

### 4.1 Hardcode IDs for Run 0

For v0.1 you MUST hardcode:

* `BeliefRegistryV010`: 5–10 belief IDs
* `PreferenceRegistryV010`: 3–10 preference IDs

The registries define:

* the **valid ID set**
* initial statuses (truth_status, strength, etc.)
* any immutable metadata needed for tests (but avoid semantic text if possible)

### 4.2 No dynamic ID creation

In v0.1:

* the generator may not invent new belief/pref IDs
* the compiler must reject unknown IDs (schema/ID validation)

Belief values may change; belief identities may not.

---

## 5) Normative Causal Ordering (Binding)

The step loop MUST be:

1. **Observe** environment (includes feasibility list)
2. **Generate JAF** from (normative state + feasibility)
3. **Compile** JAF → constraint mask
4. **Apply** mask to feasible set
5. **Select** action from masked feasible set
6. **Execute**
7. **Log** and update any allowed non-normative policy state

**Prohibited:**

* propose an action before justifying
* justify a specific action as a permission slip
* compile after selecting
* selection that depends on raw justification fields

---

## 6) Constraint Semantics (Binding)

Constraints are **restrictive / blacklist** semantics:

* default allow
* explicit forbid list
* action mask is ALLOW unless forbidden

This is required for:

* clean baseline equivalence
* clean non-triviality detection

Whitelist/positive “must do X” semantics are out of scope for v0.1.

---

## 7) Gridlock and Halt (Mandatory Handling)

### 7.1 Justification Halt (Compile failure → no action)

If compilation fails for a step:

* action selection must not occur
* classify step as `JUSTIFICATION_HALT_STEP`
* if sustained beyond a threshold, classify run as **Justification Halt** failure

No bypass. No “try anyway.”

### 7.2 Normative Gridlock (Compile ok, but mask forbids all feasible actions)

If:

* `feasible_pre_mask` is non-empty, and
* `feasible_post_mask` is empty

then:

* classify step as `NORMATIVE_GRIDLOCK_STEP`
* classify run as **Normative Gridlock** failure if it occurs (or if sustained—choose a fixed rule and preregister it)

Gridlock is not a compile error; it is a strong behavioral outcome and must be logged distinctly.

---

## 8) Justification Generation Must Be Mechanically Well-Formed

A rigid compiler + probabilistic generator will otherwise produce mostly syntax deaths.

### 8.1 Required: constrained generation or bounded syntactic retry

You MUST implement one of:

**Option A — Constrained decoding**

* JSON schema / grammar constrained output for JAF fields

**Option B — Bounded syntactic retry**

* Generate JAF
* Validate against JAF schema
* If invalid, retry up to `MAX_JAF_ATTEMPTS` (fixed; e.g., 3–10)
* If still invalid → treat as compile failure → halt step

This is not “repair” in the compiler. It is **mechanical well-formedness enforcement** upstream.

### 8.2 No prompt-tuning between steps

Prompts must be frozen per run. Do not “fix” the generator mid-trajectory.

---

## 9) Training and Optimization Separation (Critical)

The Justification Generator must not be trained to maximize external reward.

**Hard rule:**

> The Justification Generator MUST NOT be optimized on the same reward signal used by the Action Selector.

Allowed:

* frozen LLM
* prompted LLM
* separately trained objective unrelated to external reward

Forbidden:

* joint RL
* reward shaping that incentivizes “getting out of the way”
* “help the agent win” optimization

If you violate this, the generator will learn **passive legislation** (empty constraints) and you will get Narrative Collapse by construction.

---

## 10) Telemetry (Required)

You must log enough to prove the justificatory gate is real.

### 10.1 Per step

At minimum record:

* `step`
* `feasible_actions_pre_mask` (list or count + digest)
* `jaf_schema_valid` (bool)
* `compile_ok` (bool)
* `compile_error_code` (enum if false)
* `forbidden_actions` (list or digest)
* `nontrivial_forbidden = forbidden ∩ feasible_pre_mask` (count)
* `decorative_constraint = (nontrivial_forbidden_count == 0 and compile_ok)`
* `feasible_actions_post_mask` (count)
* `gridlock = (feasible_pre > 0 and feasible_post == 0)`
* `selected_action` (if any)
* `selector_scope_violation` (must be false)

### 10.2 Run level

* total steps
* compile failure rate
* decorative constraint rate
* non-trivial constraint rate
* gridlock rate / first gridlock step
* action entropy (optional)
* ablation deltas (see §11)

Telemetry must be emitted even if outcomes look “obvious.” Reviewers will not accept invisible gating.

---

## 11) Run 0: MVRA Causal-Load Test (Required)

You must implement four conditions under identical env + seed batteries:

### 11.1 Condition A — ASB Null Baseline

* no JAF
* no compiler
* no mask
* select action directly from feasible set

### 11.2 Condition B — MVRA Normal

* JAF → JCOMP → mask → select

### 11.3 Condition C — Ablation A: Scramble Justifications

Scramble JAF artifacts (structural corruption) **without** changing the selector.

Expected outcomes:

* compile failures increase (halt) OR
* masks differ and behavior diverges

If scrambling does not change feasibility/masks, justifications are not load-bearing.

### 11.4 Condition D — Ablation B: Compiler Bypass

Bypass compilation and force an empty forbid list (all allow).

Expected outcome:

* behavior collapses toward ASB baseline

---

## 12) Acceptance Tests (Non-negotiable)

Before running experiments, implement these tests.

### 12.1 Selector blindness test

Prove Action Selector cannot access JAF or normative text.
Practical requirement:

* enforce module boundaries (no imports)
* pass only mask + env obs to selector
* unit test that selector function signature excludes artifacts/state

### 12.2 Determinism test

Given same seed and frozen configs:

* identical feasibility traces
* identical JAF validity outcomes (if generator is deterministic/frozen; otherwise digest-level expectations must be preregistered)
* identical compiled mask digests
* identical action traces (where compilation succeeds)

If your generator is stochastic, you must isolate that stochasticity to its own seed stream and record it; do not let it contaminate env/policy RNG.

### 12.3 Non-triviality accounting test

Construct a known case where a feasible action is forbidden.
Assert:

* nontrivial_forbidden_count > 0
* feasible_post_mask_count < feasible_pre_mask_count

### 12.4 Gridlock detection test

Construct a case where mask forbids all feasible actions.
Assert gridlock is detected and logged as such.

### 12.5 Ablation sensitivity tests

Scramble/bypass must produce measurable deltas in masks or action traces.

---

## 13) Definition of Done

RSA-PoC v0.1 is complete when:

* MVRA implements Justify → Compile → Select ordering
* Justification Generator consumes feasibility list (read-only)
* Compiler is rigid, deterministic, non-semantic, no inference/repair
* Selector is blind to raw semantics (mask-only)
* Registries are fixed; unknown IDs cause compile failure
* Constrained output or bounded syntactic retry prevents trivial aphasia runs
* Telemetry shows non-trivial constraints occur (or the run fails honestly)
* Run 0 executes all four conditions and produces reconstructible metrics
* Ablations demonstrate collapse toward ASB class when components are removed

---

## Final Orientation for the Implementor

You are not building an agent that “sounds reflective.”

You are building a machine that must **legislate constraints into existence** before it can act—and proving that removing that legislative machinery collapses it into a non-agent class.

If it halts: that is data.
If it gridlocks: that is data.
If it outputs empty constraints: that is data.
If it binds constraints and still acts: that is the threshold object.

Do not optimize it.

Instrument it.
