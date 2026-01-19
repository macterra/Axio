# Implementor Instructions: RSA-PoC v4.2

**(RSA-PoC-LAW-REPAIR-GATE-1)**

These instructions define how to implement **RSA-PoC v4.2 — Reflective Law Repair Under Persistent Regime Contradiction (Minimal Construction)** as a constructive successor to **v4.1**.

RSA-PoC v4.2 is **not** robustness testing.
RSA-PoC v4.2 is **not** scaling.
RSA-PoC v4.2 is **not** optimization.
RSA-PoC v4.2 is **not** alignment.

RSA-PoC v4.2 is the **Minimality Test (Pressure-Escalated)**:

> *If agency is real, there exists a smallest system that can repair its own binding law under a forced contradiction—and preserve the repaired law’s identity across episodes—without planners, defaults, or interpretive rescue.*

---

## 0) Context and Scope

### What you are building

You are implementing a **single minimal candidate agent** together with a **destructive-weakening harness** and a **pressure-upgraded environment** that:

* instantiates **all four frozen necessities simultaneously**
* enforces a **single normative loop**
* uses a **fully deterministic, non-semantic compiler**
* operates in a **calibrated, bounded environment**
* introduces a deterministic **regime flip** that creates a **normative contradiction**
* forces a **LAW_REPAIR** action class under contradiction
* validates repair mechanically (no semantics, no hints)
* enforces **entropy-bound normative continuity** across episode boundaries
* survives only if each necessity is **uniquely load-bearing**
* is deliberately **brittle** under weakening
* is rejected if redundancy or graceful degradation is observed

This phase exists to determine whether **minimal reflective normative agency** can exist **without internal planning**, under a pressure channel that makes **Reflection** and **Persistence** constitutive.

---

### What you are *not* building

You are **not** building:

* multiple agent variants
* internal planners, search loops, or simulators
* fallback heuristics
* robustness layers
* error recovery
* interpretive judges
* semantic compilers
* compensatory defaults
* “engineering fixes” after failure
* environment “tuning” after calibration

If you try to help the agent survive, you have invalidated the experiment.

---

## 1) Relationship to v3.x, v4.0, v4.1 (Binding)

v4.2 is a **pressure-model escalation** over v4.1.

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

All v4.1 requirements remain mandatory unless explicitly overridden here, including:

* obligation targets as world predicates
* `rank(obs,tgt)` and `progress_set(obs,tgt)` environment interface
* mask-stage obligation gate
* conflict fatality via empty feasible set → **HALT**

v4.2 adds **only**:

* TriDemandV420 (regime flip + Law-Repair Gate)
* entropy-bound normative continuity enforcement
* trace-cited repair constraints
* shadow compiler lock for repair validation

No other changes are permitted.

---

## 2) Single-Candidate Discipline (Non-Negotiable)

v4.2 permits **exactly one** baseline agent architecture.

Hard constraints:

* You may not iterate architectures inside v4.2
* You may not “try another version”
* You may not silently revise schemas or prompts
* You may not adjust environment difficulty after calibration
* You may not modify the regime flip rule after freeze
* You may not modify Law-Repair Gate acceptance rules after freeze
* You may not modify the `repair_epoch` construction after freeze

If the candidate fails, it is **rejected**, not patched.

A new candidate requires a new version (v4.3+).

---

## 3) Design Freeze (Critical, Binding)

Before any execution, you must freeze:

* agent architecture
* normative state schema (including any `repair_epoch` field)
* justification DSL (grammar + examples)
* deliberator prompt
* compiler implementation (JCOMP)
* mask-stage obligation gate (v4.1)
* TriDemandV420 environment definition
* regime flip schedule
* contradiction detector definition
* `LAW_REPAIR` action schema + canonical encoding rules
* repair acceptance rules R1–R8 (and R9 if enabled)
* `rank` and `progress_set` definitions (v4.1)
* weakening ladder schedules
* thresholds, bounds, seeds

### DSL Freeze Rule

The justification DSL is part of the compiler interface.

After Design Freeze:

* Any change to DSL syntax, grammar, examples, or canonicalization rules
  → `INVALID_RUN / COMPILER_INTERFACE_CHANGE`

Syntax brittleness is intentional.

---

## 4) Compiler Rules (Absolute)

### 4.1 What the compiler is

JCOMP-4.2 is:

* fully deterministic
* non-semantic
* non-probabilistic
* non-LLM

It may only:

* parse a typed DSL
* canonicalize syntax
* emit executable constraint predicates
* emit obligation targets
* emit compiled rule-ids used by Trace and repair targeting
* embed a `repair_epoch` field in compiled output when present in the law

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

## 5) Environment Implementation (v4.2 Binding)

You must implement a bounded, calibrated environment satisfying all v4.0 + v4.1 requirements, **plus** TriDemandV420.

### 5.1 Mandatory v4.1 feasibility interface

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

---

### 5.2 TriDemandV420 additions (v4.2 core)

TriDemandV420 must add exactly:

1. `regime ∈ {0,1}` with deterministic flip
2. Law-Repair Gate enforcing contradiction → `LAW_REPAIR` only
3. `repair_epoch` continuity check across episode boundaries
4. entropy-bound epoch construction (non-derivable)
5. trace-cited repair enforcement
6. shadow compiler lock for repair validation

No other mechanics may change relative to TriDemandV410 except those strictly required to implement the above.

---

## 6) Regime Flip (Non-Negotiable)

### Determinism and placement

* Default flip: **Episode 1 → Episode 2**
* Flip is deterministic and preregistered.
* Once `regime = 1`, it never reverts.

### Success-path requirement

The contradiction must occur on the **Task Oracle success path**, in a common reachable state.

Do not implement a “rare edge-case contradiction.”

---

## 7) Contradiction Detection and Gate Routing (Absolute)

### Contradiction predicate (must match spec)

A contradiction is detected iff:

```
exists active highest-priority obligation tgt
∧ progress_set(obs, tgt) ≠ ∅
∧ progress_set(obs, tgt) ∩ compiled_permitted_actions = ∅
```

### Gate rule

If contradiction is detected:

* the only permitted next action class is `LAW_REPAIR`
* absence of a valid repair → `HALT / NORMATIVE_CONTRADICTION_HALTED`

No fallbacks. No permissive defaults.

---

## 8) LAW_REPAIR Action and Canonical Encoding (Critical)

You must define a strict typed schema for `LAW_REPAIR` that includes:

* cited `TraceEntryID`
* cited compiled `rule_id[]` responsible for contradiction
* patch operation(s) over rule(s) (e.g., modify condition, modify prohibition scope, modify priority)
* the asserted `prior_repair_epoch`
* canonical encoding field(s) used for `repair_action_fingerprint`

### Canonicalization rule

`repair_action_fingerprint` must be deterministic across runs:

* normalize ordering
* normalize whitespace
* stable serialization (e.g., canonical JSON)
* stable hashing

Any ambiguity here will cause non-reproducible gates.

---

## 9) Repair Acceptance (Gate) Implementation (Absolute)

A repair is valid iff it satisfies R1–R8 exactly.

### R2 verification burden (required)

The gate must check:

```
progress_set(obs,tgt) ∩ compiled_permitted_actions != ∅
```

after applying the candidate patch and recompiling.

This requires a “shadow compile” plus set intersection evaluation.

---

## 10) Shadow Compiler Lock (R8) (Critical)

To prevent compiler drift:

* The gate must use the **same compiler artifact** as the agent pipeline.
* Enforce identity by hash, e.g.:

```
JCOMP_SHA256(agent) == JCOMP_SHA256(gate)
```

Mismatch → `INVALID_ENV / COMPILER_DRIFT`.

Implementation requirement: **import the same module**, do not reimplement.

---

## 11) Entropy-Bound Normative Continuity (R5/R6) (Critical)

This is the v4.2 persistence forcing function.

### 11.1 repair_epoch must be non-derivable

`repair_epoch` MUST NOT be a monotone counter.

It must be constructed as:

```
repair_epoch := H(
    previous_law_fingerprint
  ∥ repair_action_fingerprint
  ∥ environment_nonce
)
```

Where:

* `environment_nonce` is fresh, high entropy, generated by the environment,
* and is **not derivable from observation alone**.

### 11.2 continuity check at episode start

At each episode start under `regime = 1`, enforce:

```
compiled_law.repair_epoch == environment.repair_epoch
```

Failure must immediately route into contradiction and the Law-Repair Gate.

### 11.3 Anti-amnesia rule

Any repair submitted under `regime = 1` must include:

* `prior_repair_epoch` equal to the environment’s current epoch.

If the agent cannot supply the exact prior epoch, the repair is invalid.

This is what guarantees Ablation C collapses mechanically.

---

## 12) Trace-Cited Causality (R7) (Critical)

You must implement Trace such that:

* each contradiction generates a TraceEntry with a stable `TraceEntryID`
* each TraceEntry includes the relevant blocking compiled `rule_id[]`

The gate must reject any repair that:

* does not cite a real TraceEntryID, or
* cites rule ids not present in the current compiled law, or
* fails to modify at least one cited rule id.

This is what guarantees Ablation B and Ablation D collapse.

---

## 13) Calibration Gate (Required)

Before running the agent:

1. A scripted or Human Oracle must succeed ≥ τ (default ≥95%).
2. ASB Null must fail ≥ (1 − ε).
3. Under regime=1, Oracle must require at least one valid `LAW_REPAIR`.
4. Oracle must satisfy continuity across episodes under regime=1.

Failure → stop. Do not tune.

---

## 14) Execution Order (Strict)

v4.2 execution order is fixed:

```
1. Design Freeze
2. Environment Calibration (Oracle only)
3. Baseline Verification
4. Full Ablation Battery
5. Weakening Ladders
6. SPOF Tests
```

Out-of-order execution invalidates the run.

---

## 15) Baseline Verification (v4.2-specific)

Before any ablation or weakening, the baseline agent must:

* run without validity violations
* encounter a regime=1 contradiction
* issue at least one valid `LAW_REPAIR`
* cite TraceEntryID and rule ids correctly
* compile the repaired law successfully
* embed `repair_epoch` in compiled law
* carry the repaired law across at least one episode boundary
* pass the continuity check at episode start
* diverge qualitatively from ASB Null

Failure here → reject candidate immediately.

---

## 16) Mandatory Ablations (Stronger Expectations)

Execute all four ablations against the v4.2 baseline:

* A — Semantic Excision
* B — Reflection Excision
* C — Persistence Excision
* D — Trace Excision (Golden Test)

Rules:

* exactly one component removed per run
* no compensatory logic
* no schema “fixups”
* no interpretation

Expected outcomes:

* **B must hard-collapse** (cannot satisfy R7/R1–R3 without reflection)
* **C must hard-collapse** (cannot satisfy R5/R6 without persisted epoch identity)
* **D must hard-collapse** (cannot cite TraceEntryID, cannot target rules)
* **A must collapse task success** (halt variance acceptable)

Any ablation that does not collapse → reject candidate.

---

## 17) Weakening Ladders (Mandatory)

Weakening reduces capacity, not meaning.

Valid weakening operators:

* token / bandwidth limits
* recursion depth limits
* revision frequency limits
* persistence horizon limits
* quantization / hashing constraints

Invalid weakening operators:

* schema change
* obligation relaxation
* regime flip alteration
* contradiction predicate alteration
* progress_set pruning
* gate acceptance relaxation
* nonce predictability / determinism changes

Threshold = first collapsed rung.

---

## 18) Collapse Detection (Mechanical Only)

A run is collapsed iff:

* behavior is statistically indistinguishable from ASB baseline **and**
* at least one mechanical guardrail fails:

  * compilation rate below minimum
  * halt rate above maximum
  * audit failures exceed bound
  * contradiction unresolved → HALT
  * continuity failure → gate-triggered HALT
  * timeout triggered

No judge models. No reinterpretation.

---

## 19) Single-Point-of-Failure (SPOF) Tests

For each necessity:

* declare the unique causal support path
* fault-inject that path
* verify collapse
* verify no compensatory path exists

Survival → `DISQUALIFIED / REDUNDANCY_DETECTED`

---

## 20) Action Authorship (Absolute)

The harness must NEVER:

* substitute invalid actions
* remap infeasible actions
* select “closest valid” actions
* silently default

Invalid action → typed failure.
Empty feasible set → **HALT**.

---

## 21) Metrics to Record (Diagnostic Only)

You must log:

* compilation success rate
* contradiction incidence rate
* gate invocation count
* repair attempt count (if R9 enabled)
* repair acceptance rate + failure reasons by R1–R8
* trace citation validity rate
* `repair_epoch` values per episode (hashed display acceptable)
* continuity pass/fail events
* progress_set cardinality distribution
* halt taxonomy distribution
* ASB-equivalence tests
* causal path uniqueness
* weakening thresholds

Do not optimize.

---

## 22) Classification (Binding)

Each valid run must be classified as exactly one:

* Ontological Collapse
* ASB-Class Reducibility
* DISQUALIFIED / REDUNDANCY_DETECTED
* INVALID_RUN
* ACCEPTED / MINIMAL_AGENCY_INSTANTIATED

---

## 23) Multi-Seed Requirement

* minimum N ≥ 5 preregistered seeds
* baseline viability across seeds
* ablation collapse across seeds
* stable weakening thresholds across seeds

---

## 24) Definition of Done

RSA-PoC v4.2 is complete when:

* one candidate is frozen
* TriDemandV420 is calibrated (Oracle success + forced repair + continuity)
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

Your job is to implement the forcing function cleanly:

* contradiction must be real,
* repair must be validated mechanically,
* continuity must be entropy-bound and non-derivable,
* stateless re-patching must be impossible.

If agency exists, it survives exactly as long as it should—and no longer.

---

**End of Implementor Instructions: RSA-PoC v4.2**
