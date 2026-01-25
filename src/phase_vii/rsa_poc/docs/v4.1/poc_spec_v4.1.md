# RSA-PoC v4.1 — Feasible Obligation Binding

*(Minimal Construction, Revised & Clarified)*

**Reflective Sovereign Agent — Proof-of-Concept**

---

## Status

**Current Version:** **v4.1 (RSA-PoC-FEASIBLE-OBLIGATION-1)**
**Status:** Normative, preregistration-ready

RSA-PoC v4.1 supersedes v4.0.

v4.0 is formally closed as:

```
VALID_RUN / BASELINE_FAILED (SPEC–ENVIRONMENT INCONSISTENCY)
```

All v3.x results remain valid.
v4.1 revises **only obligation semantics and their environment interface**; all other v4.0 commitments remain in force unless explicitly restated.

---

## Purpose

RSA-PoC v4.1 repairs a **formal inconsistency** discovered in v4.0:

> *Strict action-level obligation semantics are incompatible with environments requiring multi-step satisfaction of obligations.*

v4.1 preserves the **ontological goal of v4.x**:

> **Determine whether there exists a minimal architecture in which agency is instantiated without redundancy, interpretive rescue, or hidden defaults.**

v4.1:

* does **not** relax minimality standards,
* does **not** introduce robustness, learning, or alignment,
* does **not** internalize planning or search,
* is a **type-correct refinement**, not a concession.

v4.1 explicitly evaluates **Normative Sovereignty** (bindingness, conflict handling, authorship integrity), not **Instrumental Rationality**.

---

## v4.1 Invariant (Restated, Binding)

> **Agency is a minimality claim. A v4.1 candidate is valid only if each frozen necessity is (1) present, (2) uniquely load-bearing via a single causal path, and (3) minimally strong—weakening it past a threshold causes ontological collapse.**

Redundancy, interpretive rescue, compensatory defaults, or covert delegation remain disqualifying.

---

## Entry Conditions

v4.1 may begin only because:

1. v3.x established non-reducibility under ablation.
2. v4.0.1 established a **spec–environment inconsistency** under valid execution.
3. That inconsistency is localized to **obligation semantics**, not the broader architecture.

---

## Ontological Claim Under Test (Unchanged)

> There exists a single minimally structured architecture that:
>
> 1. instantiates all four necessities simultaneously,
> 2. cannot be reduced to an ASB-Class Null Agent without reinstating at least one necessity, and
> 3. exhibits a minimal-strength collapse threshold for each necessity.

---

## Architectural Baseline (Inherited)

All v4.0 architectural constraints remain binding, including:

* Five-component architecture
* Strict ordering: **Justify → Compile → Mask → Select → Execute**
* Deterministic, non-semantic compiler (no LLM)
* Selector blindness
* Semantic localization
* Fail-not-substitute authorship
* Cost-Blindness Axiom
* Institutional execution support
* Audit Rules A / B / C / C′
* ASB-Class Null baseline
* Execution Addendum validity gates
* Single-candidate discipline
* No redundancy, no hidden defaults

---

## Revised Obligation Semantics (Core Change)

### 1. Obligation Target (Binding)

An **OBLIGATION** binds to an **obligation target**, not to a single immediate action.

An **obligation target** is the rule’s declared `effect`, interpreted as a desired **world-state predicate** (e.g., `DEPOSIT@ZONE_A`), not an atomic action token.

---

### 2. Obligation Satisfaction

An obligation is **satisfied** iff the obligation target holds in the current environment state.

Example:

* `OBLIGATION(DEPOSIT@ZONE_A)` is satisfied iff `zone_a_satisfied == True`.

---

### 3. Obligation Progress Set (Binding)

If an obligation is active and unsatisfied, the **Mask stage** must restrict the feasible action set to a deterministic **progress set** defined by the environment:

```
progress_set = ENV.progress_set(obs, obligation_target)
```

#### Progress Set Properties (Mandatory)

The `progress_set` must be:

* finite,
* deterministic,
* non-semantic,
* dependent only on `(obs, obligation_target)`,
* independent of agent internals or history,
* free of policy, optimization, learning, or heuristics.

---

### 4. Rank-Based Descent (Formal Definition)

The environment must define a **well-founded ranking function**:

```
rank(obs, obligation_target) -> ℕ ∪ {∞}
```

Subject to:

1. `rank = 0` iff the obligation target is satisfied,
2. `rank = ∞` iff the obligation is impossible,
3. rank depends only on environment-internal state,
4. rank is well-founded (no infinite descending chains).

The progress set is then defined as:

```
progress_set(obs, tgt) =
    { a | rank(step(obs, a), tgt) < rank(obs, tgt) }
```

This definition:

* requires no planning or foresight by the agent,
* does not encode policy,
* allows purely local, physics-like feasibility gradients.

---

### 5. Priority Resolution (Inherited)

If multiple obligations are active:

1. Select the highest-priority **positive obligation**.
2. If priorities tie → `REFERENCE_ERROR`.
3. Lower-priority **positive obligations** are suspended until the higher-priority obligation is satisfied or expires.

---

### 6. Prohibitions and Conflicts (Clarified)

**Prohibitions (negative constraints)** remain globally binding unless explicitly overridden by a higher-priority rule.

Conflict behavior is unchanged and intentional:

* If an active obligation’s progress set is fully prohibited, the feasible set becomes empty.
* An empty feasible set results in **HALT**.
* This represents a **structural contradiction**, not a recoverable execution error.

Impossible obligations are fatal to agency.

---

### 7. Obligation Gate (Revised Mask-Stage Rule)

At each step:

1. Identify active, unsatisfied obligations.
2. Select the highest-priority positive obligation (if any).
3. If one exists:

   * Compute `progress_set`.
   * If `progress_set = ∅` → `HALT`.
   * Else:

     ```
     feasible = progress_set ∩ compiled_permitted_actions
     ```
4. If no obligation binds:

   ```
   feasible = PERMISSION − PROHIBITION
   ```

`compiled_permitted_actions` denotes the action set after applying prohibitions and explicit overrides in the compiled law.

**Key property:**
The agent cannot act arbitrarily under obligation, yet is not deadlocked by infeasible single-step constraints.

---

## Environment Requirements (Restated + Extended)

All v4.0 environment constraints remain binding.

v4.1 adds:

### Environment Obligation Interface (Mandatory)

An in-scope environment must define:

```python
progress_set(obs, obligation_target) -> Set[action_id]
rank(obs, obligation_target) -> ℕ ∪ {∞}
```

Constraints:

* deterministic,
* non-semantic,
* finite action sets,
* no access to agent internals,
* no learned weights or history-dependent costs,
* no embedded planning or optimization.

The interface is part of the **environment specification**, not the agent.

---

### Branching Constraint (Calibration Requirement)

To avoid degenerate “escort” dynamics:

> For each obligation target, the environment must exhibit **branching states** (i.e., |progress_set| ≥ 2) in at least some non-terminal states, unless the physical dynamics strictly force a single action.

This is a calibration requirement, not an agent capability.

---

## TriDemandV410 (Revised Environment)

TriDemandV400 is minimally revised to **TriDemandV410** by adding `rank` and `progress_set`.

### Example Progress Sets for `DEPOSIT@ZONE_A`

| State                          | progress_set           |
| ------------------------------ | ---------------------- |
| inventory == 0 & at SOURCE     | {COLLECT}              |
| inventory == 0 & not at SOURCE | {MOVE_* toward SOURCE} |
| inventory > 0 & not at ZONE_A  | {MOVE_* toward ZONE_A} |
| inventory > 0 & at ZONE_A      | {DEPOSIT}              |

Equivalent deterministic definitions apply for ZONE_B and ZONE_C.

No other environment changes are permitted in v4.1.

---

## Experimental Design (Unchanged)

Execution order:

1. Design Freeze (v4.1)
2. Environment Calibration (Oracle only)
3. Baseline Verification
4. Full Ablation Battery
5. Weakening Ladders
6. SPOF Tests
7. Classification + Closure

---

## Mandatory Ablations (Unchanged)

Ablations A–D are executed exactly as in v4.0:

* Semantic Excision
* Reflection Excision
* Persistence Excision
* Trace Excision

Each must still cause collapse.

---

## Weakening Ladders (Unchanged)

W1–W4 remain identical in structure and reporting to v4.0:

* Traces: `max_trace_tokens`
* Semantics: `obs_bits_budget`
* Reflection: `min_steps_between_patches`
* Persistence: `persist_episodes_horizon`

Each necessity must exhibit a collapse threshold.

---

## Validity Gates (Restated)

All v4.0 gates remain binding:

* No post-freeze changes
* No Oracle outside calibration
* No pipeline bypass
* No interpretive judging
* No defaults
* Timeout = mechanical failure

---

## Success Criteria for v4.1

RSA-PoC v4.1 succeeds iff:

1. Baseline completes without pervasive HALT.
2. Baseline diverges qualitatively from ASB Null.
3. All four ablations collapse across seeds.
4. No redundancy is detected.
5. Each necessity exhibits a weakening threshold.
6. Results are stable across preregistered seeds.

---

## Failure Modes (Pre-Registered)

| Outcome                         | Interpretation                                  |
| ------------------------------- | ----------------------------------------------- |
| Baseline fails                  | Architecture + environment incompatible         |
| Some ablations fail to collapse | Necessity not load-bearing                      |
| No weakening threshold          | Necessity not minimal                           |
| Redundancy detected             | Ontology overclaimed                            |
| All candidates fail             | Minimal agency does not exist under constraints |

---

## Scope Discipline (Restated)

v4.1 exits scope if:

* obligation semantics are softened into guidance,
* `progress_set` becomes heuristic or policy-like,
* the environment embeds planning or optimization,
* the agent gains hidden defaults or fallbacks,
* results require interpretation rather than mechanics.

---

## Deliverables

A complete v4.1 submission includes:

* This specification
* Revised environment spec (`rank`, `progress_set`)
* Frozen DSL + JCOMP
* Baseline and ablation logs
* Weakening ladder data
* SPOF analysis
* Explicit accept / reject / impossibility statement

---

## Final Normative Statement

> **RSA-PoC v4.1 refines obligation semantics to be type-correct for multi-step environments without relaxing bindingness.**
> If agency exists as a minimal phenomenon, it must survive under these semantics.
> If it does not, the non-existence of minimal agency is a real result.

---

**End of RSA-PoC v4.1 Specification**
