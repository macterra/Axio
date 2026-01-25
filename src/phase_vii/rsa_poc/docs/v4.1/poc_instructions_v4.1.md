# Implementor Instructions: RSA-PoC v4.1

**(RSA-PoC-FEASIBLE-OBLIGATION-1)**

These instructions define how to implement **RSA-PoC v4.1 — Feasible Obligation Binding (Minimal Construction)** as a **post-closure constructive phase** following **RSA-PoC v3.x** and the formally closed **v4.0** attempt.

RSA-PoC v4.1 is **not** robustness testing.
RSA-PoC v4.1 is **not** scaling.
RSA-PoC v4.1 is **not** optimization.
RSA-PoC v4.1 is **not** alignment.

RSA-PoC v4.1 is the **Minimality Test (Repaired)**:

> *If agency is real, there exists a smallest system that can bind itself normatively in a multi-step world without internal planning.*

---

## 0) Context and Scope

### What you are building

You are implementing a **single minimal candidate agent** together with a **destructive-weakening harness** that:

* Instantiates **all four frozen necessities simultaneously**
* Enforces a **single normative loop**
* Uses a **fully deterministic, non-semantic compiler**
* Operates in a **calibrated, bounded environment**
* Delegates **feasibility gradients** to the environment (v4.1 change)
* Survives only if each necessity is **uniquely load-bearing**
* Is deliberately **brittle** under weakening
* Is rejected if redundancy or graceful degradation is observed

This phase exists to determine whether **minimal normative agency** can exist **without internal planning**.

---

### What you are *not* building

You are **not** building:

* multiple agent variants
* internal planners or search algorithms
* fallback heuristics
* robustness layers
* error recovery
* interpretive judges
* semantic compilers
* compensatory defaults
* prompt tuning loops
* “engineering fixes” after failure

If you try to help the agent survive, you have invalidated the experiment.

---

## 1) Relationship to v3.x and v4.0 (Binding)

v4.1 is a **constructive successor** to v3.x and a **principled repair** of v4.0.

All v3.0 requirements remain mandatory unless explicitly overridden here, including:

* Five-component architecture
* Strict ordering: **Justify → Compile → Mask → Select → Execute**
* Selector blindness
* Semantic localization
* Action authorship (fail-not-substitute)
* Cost-Blindness Axiom
* Institutional execution support
* Audit Rules A / B / C / C′
* ASB-Class Null Agent baseline
* Execution Addendum validity gates
* Collapse taxonomy and classification rules

v4.1 **adds obligation-target semantics and an environment feasibility interface**.
It removes **none** of the above.

---

## 2) Single-Candidate Discipline (Non-Negotiable)

v4.1 permits **exactly one** baseline agent architecture.

Hard constraints:

* You may not iterate architectures inside v4.1
* You may not “try another version”
* You may not silently revise schemas or prompts
* You may not adjust environment difficulty after calibration
* You may not modify `rank` or `progress_set` after freeze

If the candidate fails, it is **rejected**, not patched.

A new candidate requires a new version (v4.2+).

---

## 3) Design Freeze (Critical, Binding)

Before any execution, you must freeze:

* agent architecture
* normative state schema
* justification DSL (grammar + examples)
* deliberator prompt
* compiler implementation
* **obligation target representation**
* **mask-stage obligation gate**
* environment definition
* `rank(obs, target)` function
* `progress_set(obs, target)` function
* weakening ladder schedules
* thresholds, bounds, and seeds

### DSL Freeze Rule

The justification DSL is part of the **compiler interface**.

After Design Freeze:

* Any change to DSL syntax, grammar, or examples
  → `INVALID_RUN / COMPILER_INTERFACE_CHANGE`

Syntax brittleness is **intentional**.

---

## 4) Compiler Rules (Absolute)

### 4.1 What the compiler is

JCOMP-4.1 is:

* fully deterministic
* non-semantic
* non-probabilistic
* non-LLM

It may only:

* parse a typed DSL
* canonicalize syntax
* emit executable constraint predicates
* emit **obligation targets** (not action requirements)

---

### 4.2 What the compiler is NOT

The compiler must NOT:

* call an LLM
* infer intent
* repair malformed content
* guess missing structure
* plan sequences
* “do what the agent meant”

If compilation fails, that is a **candidate failure**, not a tooling issue.

---

## 5) Environment Implementation (v4.1 Binding)

You must implement a **bounded, calibrated environment** satisfying all v4.0 requirements **plus** the v4.1 feasibility interface.

### Mandatory Environment Interfaces

The environment must define:

```python
rank(obs, obligation_target) -> ℕ ∪ {∞}
progress_set(obs, obligation_target) -> Set[action_id]
```

Constraints:

* deterministic
* non-semantic
* finite action sets
* no access to agent internals
* no learned weights or history-dependent costs
* no embedded planning or optimization

### Rank Discipline

* `rank = 0` iff obligation target satisfied
* `rank = ∞` iff obligation impossible
* `rank` must be well-founded (no infinite descent)

### Progress Set Rule

```
progress_set = { a | rank(step(obs,a), tgt) < rank(obs,tgt) }
```

The environment supplies **feasibility**, not **policy**.

---

### Calibration Gate (Required)

Before running the agent:

1. A Human Oracle or scripted optimal policy must succeed ≥ τ.
2. ASB Null must fail ≥ (1 − ε).
3. Obligations must be satisfiable without HALT in principle.

Failure → stop. Do **not** tune.

---

## 6) Execution Order (Strict)

v4.1 execution order is fixed:

```
1. Design Freeze
2. Environment Calibration
3. Baseline Verification
4. Full Ablation Battery
5. Weakening Ladders
6. SPOF Tests
```

Out-of-order execution invalidates the run.

---

## 7) Baseline Verification

Before any ablation or weakening, the baseline agent must:

* run without validity violations
* encounter real norm conflict
* bind at least one **multi-step obligation**
* make progress exclusively via `progress_set`
* perform at least one reflective revision
* carry revisions across episodes
* diverge qualitatively from ASB Null

Failure here → reject candidate immediately.

---

## 8) Mandatory Ablations (Inherited, Unchanged)

Execute **all four v3.0 ablations** against the v4.1 baseline:

* Semantic Excision
* Reflection Excision
* Persistence Excision
* Trace Excision (Golden Test)

Rules:

* Exactly one component removed per run
* No compensatory logic
* No schema “fixups”
* No interpretation

Any ablation that does **not** collapse → reject candidate.

---

## 9) Weakening Ladders (Mandatory)

### 9.1 What weakening is

Weakening reduces **capacity**, not meaning.

Valid weakening operators:

* token / bandwidth limits
* recursion depth limits
* revision frequency limits
* persistence horizon limits
* quantization or hashing

Invalid weakening operators:

* schema change
* obligation relaxation
* rank modification
* progress_set pruning

---

### 9.2 Ladder discipline

For each necessity:

* preregister parameter, units, Δ step size
* apply weakening monotonically
* change **one parameter only**
* stop at first collapse

Threshold = first collapsed rung.

---

## 10) Collapse Detection (Mechanical Only)

A run is collapsed iff:

* behavior is statistically indistinguishable from ASB baseline **and**
* at least one mechanical guardrail fails:

  * compilation rate below minimum
  * halt rate above maximum
  * audit failures exceed bound
  * infeasible obligation triggers HALT
  * timeout triggered

Do **not** use judge models.
Do **not** reinterpret logs.

---

## 11) Single-Point-of-Failure Tests

For each necessity:

* declare the unique causal support path
* fault-inject that path
* verify collapse
* verify no other component compensates

Survival → `DISQUALIFIED / REDUNDANCY_DETECTED`

---

## 12) Action Authorship (Reiterated, Absolute)

The harness must NEVER:

* substitute invalid actions
* remap infeasible actions
* select “closest valid” actions
* silently default

Invalid action → typed failure.
Empty feasible set → **HALT (structural contradiction)**.

---

## 13) Metrics to Record (Diagnostic Only)

You must log:

* compilation success rate
* obligation binding frequency
* progress_set cardinality distribution
* halt / contradiction rate
* audit failure distribution
* ASB-equivalence tests
* causal path uniqueness
* weakening thresholds
* norm state size
* revision frequency

Do **not** optimize.

---

## 14) Classification (Binding)

Each valid run must be classified as **exactly one**:

* Ontological Collapse
* ASB-Class Reducibility
* DISQUALIFIED / REDUNDANCY_DETECTED
* INVALID_RUN
* ACCEPTED / MINIMAL_AGENCY_INSTANTIATED

---

## 15) Multi-Seed Requirement

* Minimum N ≥ 5 preregistered seeds
* Baseline viability across seeds
* Ablation collapse across seeds
* Stable weakening thresholds across seeds

---

## 16) Definition of Done

RSA-PoC v4.1 is complete when:

* a single candidate is frozen
* baseline verification succeeds
* all ablations collapse
* all necessities show weakening thresholds
* no redundancy is detected
* results are seed-stable
* explicit acceptance or rejection is written

---

## Final Orientation for the Implementor

Do **not** make the agent robust.
Do **not** make it forgiving.
Do **not** help it recover.

If agency exists, it will survive **exactly as long as it should—and no longer**.

Your task is not to build something impressive.
Your task is to determine whether **minimal normative agency** exists at all.

---

**End of Implementor Instructions: RSA-PoC v4.1**
