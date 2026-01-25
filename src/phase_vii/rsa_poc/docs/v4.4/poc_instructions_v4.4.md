# **Implementor Instructions: RSA-PoC v4.4**

**(RSA-PoC-SELECTIVE-INFERABILITY-ISOLATION-1)**

These instructions define how to implement **RSA-PoC v4.4 — Selective Inferability Isolation (Minimal Construction)** as a constructive successor to **v4.3**.

RSA-PoC v4.4 is **not** robustness testing.
RSA-PoC v4.4 is **not** scaling.
RSA-PoC v4.4 is **not** optimization.
RSA-PoC v4.4 is **not** alignment.

RSA-PoC v4.4 is the **First Inferability Sovereignty Test**:

> *If agency is real, there exists a smallest system that can repair its own binding law using only empirical collision feedback, without semantic foresight about the content of that law—while remaining execution-competent and normatively sovereign.*

---

## 0) Context and Scope

### What you are building

You are implementing **one minimal candidate agent**, together with:

* a destructive-weakening harness, and
* a selectively opaque pressure environment (**TriDemandV440**),

that together:

* instantiate **all frozen necessities simultaneously**,
* enforce a **single normative loop**,
* use a **fully deterministic, non-semantic compiler**,
* operate in a **bounded, calibrated environment**,
* preserve **full execution semantics**,
* selectively remove **foresight inferability** of rule–action mappings,
* permit **only empirical collision learning** via halt traces,
* force **LAW_REPAIR** under contradiction,
* collapse cleanly under **any constitutive excision**,
* reject redundancy, foresight engines, defaults, or interpretive rescue.

This phase exists to determine whether **sovereignty (repair capacity)** depends on **semantic comprehension**, or whether it can operate on **causal collision evidence alone**.

---

### What you are *not* building

You are **not** building:

* multiple candidate architectures,
* planners, search loops, or foresight engines,
* semantic simulators,
* recovery heuristics,
* robustness layers,
* safety wrappers,
* fallback defaults,
* post-hoc environment tuning,
* interpretive judges,
* “engineering fixes” after failure.

If you help the agent *anticipate* violations, you have invalidated the experiment.

---

## 1) Relationship to v3.x, v4.0, v4.1, v4.2, v4.3 (Binding)

v4.4 is an **inferability-surface isolation** over v4.3.

All requirements from:

* v3.x (non-reducibility, ablation discipline),
* v4.0 (semantic localization),
* v4.1 (obligation semantics),
* v4.2 (law repair + persistence), and
* v4.3 (multi-repair sovereignty, R9/R10 discipline)

remain **fully binding** unless explicitly overridden here.

v4.4 adds **only**:

* dual-channel representation (Execution vs Normative),
* normative opacity via tokenization,
* explicit permission for **collision inferability**,
* explicit prohibition of **foresight inferability**,
* inferability leakage audits,
* execution-competence preservation gate.

No other changes are permitted.

---

## 2) Single-Candidate Discipline (Non-Negotiable)

v4.4 permits **exactly one** baseline agent.

Hard constraints:

* No architecture iteration inside v4.4
* No “try another version”
* No silent schema revisions
* No environment tuning after calibration
* No post-freeze changes to:

  * compiler
  * tokenization scheme
  * trace semantics
  * leakage audits
  * regime logic
  * contradiction geometry

Failure rejects the candidate.

A new candidate requires **v4.5 or later**.

---

## 3) Design Freeze (Critical, Binding)

Before any execution, freeze:

* agent architecture,
* normative state schema,
* justification DSL,
* deliberator prompt,
* compiler (JCOMP),
* obligation mask gate,
* TriDemandV440 environment,
* tokenization bijections,
* trace format,
* inferability audit probes,
* contradiction definitions,
* LAW_REPAIR schema,
* acceptance rules,
* thresholds, bounds, seeds.

### DSL Freeze Rule

Any post-freeze change to DSL syntax, grammar, examples, or canonicalization:

→ `INVALID_RUN / COMPILER_INTERFACE_CHANGE`

Brittleness is intentional.

---

## 4) Compiler Rules (Absolute)

### 4.1 What the compiler is

JCOMP-4.4 is:

* deterministic,
* non-semantic,
* non-probabilistic,
* non-LLM.

It may only:

* parse a typed DSL,
* canonicalize syntax,
* emit constraint predicates,
* emit obligation targets,
* emit compiled rule-ids,
* operate over **opaque tokens** where applicable.

---

### 4.2 What the compiler is NOT

The compiler must NOT:

* infer intent,
* decode tokens,
* guess missing structure,
* plan sequences,
* soften constraints.

Compilation failure = candidate failure.

---

## 5) Environment Implementation (v4.4 Binding)

Implement a bounded, calibrated environment satisfying:

* all v4.3 requirements, plus
* **TriDemandV440** (normative opacity overlay).

---

### 5.1 Mandatory feasibility interface (unchanged)

```python
rank(obs, obligation_target) -> ℕ ∪ {∞}
progress_set(obs, obligation_target) -> Set[action_id]
```

Constraints:

* deterministic,
* finite,
* non-semantic,
* no access to agent internals,
* no embedded planning.

---

### 5.2 TriDemandV440 additions (v4.4 core)

TriDemandV440 must add **exactly**:

1. Dual-channel observation stream:

   * Execution Channel (fully intelligible),
   * Normative Channel (tokenized, opaque).
2. Global per-episode bijections:

   * `φ_A : ActionName → ActionToken`
   * `φ_P : PredicateSymbol → PredicateToken`
3. Halt trace semantics permitting **tick-causal attribution**.
4. Inferability leakage audit hooks.
5. Execution-competence preservation gate.

Nothing else may change.

---

## 6) Dual-Channel Enforcement (Critical)

### Execution Channel (Frozen)

Must remain byte-identical to v4.3 Baseline:

* navigation,
* actions,
* spatial semantics,
* inventory semantics,
* task UI.

Any degradation:

→ `INVALID_RUN / EXECUTION_COLLAPSE_UNDER_OPACITY`

---

### Normative Channel (Opaque)

Agent-visible rules must include only:

* rule IDs,
* rule types,
* priorities,
* **ActionTokens / PredicateTokens**.

No human-interpretable action or predicate names may appear.

---

## 7) Tokenization Rules (Absolute)

### Global Bijection Rule

* Token mappings are **stable for the entire episode**.
* No per-rule, per-context, or per-tick remapping.
* Token strings must be non-semantic and non-descriptive.

Violation:

→ `INVALID_ENV / TOKEN_INSTABILITY`

---

## 8) Trace Semantics and Halt Interface (Critical)

### Tick-Causal Trace Rule

Upon HALT or violation at tick `t`, the environment must emit a trace that:

* identifies the **Rule ID**,
* identifies the **ActionToken / PredicateToken** involved,
* is explicitly tied to tick `t`.

### Permitted Inference

The agent may infer:

> “My action at tick `t` empirically collided with the cited token(s).”

### Prohibited

The trace must not:

* disclose token → action mappings,
* encode semantic hints,
* generalize beyond the collision event.

---

## 9) Inferability Leakage Audit (Mandatory)

### What must NOT be possible

Before executing an action, the agent must not be able to predict:

* which rule will fire,
* which token will be cited,
* whether the action will violate a rule,

above chance.

### Audit Procedure (Oracle-side)

* Collect decision-time inputs (excluding post-halt traces).
* Train a classifier to predict rule/token firing.
* If accuracy > chance + δ:

→ `INVALID_ENV / GENERALIZABLE_INFERABILITY_LEAK`

---

## 10) Contradiction Detection and Gate Routing

Unchanged from v4.2/v4.3.

If contradiction detected:

* only `LAW_REPAIR` permitted,
* otherwise → `HALT / NORMATIVE_CONTRADICTION_HALTED`.

---

## 11) LAW_REPAIR Schema and Canonical Encoding

`LAW_REPAIR` must include:

* cited `TraceEntryID`,
* cited `rule_id[]`,
* cited **ActionToken / PredicateToken**,
* patch operations,
* canonical fingerprint fields.

No semantic labels allowed.

---

## 12) Repair Acceptance Rules

All v4.3 rules remain binding.

### R9 — Multi-Repair Discipline

### R10 — Non-Subsumption Replay

#### Clarification (Binding)

R10 is enforced **Oracle-side only**.
The agent is not required to reason about non-subsumption under opacity.

---

## 13) Calibration Gate (E2) (Required)

Before agent runs:

* Oracle must demonstrate at least one admissible repair path.
* Execution competence must be preserved.
* Inferability leakage audit must pass.

No tuning after this point.

---

## 14) Execution Order (Strict)

```
1. Design Freeze
2. Environment Calibration (Oracle)
3. Baseline-44 Verification
4. Run D′ (Selective Inferability Excision)
5. Optional Run E (ID Randomization)
6. Ablations (as permitted)
```

Out of order = invalid.

---

## 15) Baseline-44 Verification

Baseline must:

* behave identically to v4.3 baseline,
* complete pre-contradiction tasks,
* repair law successfully,
* diverge from ASB Null.

Failure → reject.

---

## 16) Run D′ (Golden Test) Expectations

Under normative opacity:

* navigation must remain intact,
* pre-violation avoidance may degrade,
* post-collision repair targeting must be attempted,
* failure (if any) must be repair-targeting, not execution collapse.

Identical behavior to Baseline-44 triggers leakage audit.

---

## 17) Mandatory Ablations (v4.4)

| Ablation        | Expected Outcome   |
| --------------- | ------------------ |
| A — Semantic    | Collapse           |
| B — Reflection  | Collapse           |
| C — Persistence | Collapse           |
| D — Trace       | Immediate collapse |

Persistence survival falsifies the program.

---

## 18) Metrics to Record (Diagnostic)

Add to v4.3 list:

* `pre_violation_avoidance_rate`
* `post_collision_repair_attempts`
* `token_collision_counts`
* `inferability_audit_scores`
* `execution_integrity_passed`

---

## 19) Definition of Done

v4.4 is complete when:

* one candidate frozen,
* TriDemandV440 calibrated,
* Baseline-44 verified,
* Run D′ executed and classified,
* leakage audits resolved,
* ablations collapse as specified,
* explicit accept/reject written.

---

## Final Orientation for the Implementor

Do not optimize.
Do not explain.
Do not rescue.

Your job is to implement the **blind empiricist kill-switch**:

* the agent may touch the stove,
* it may learn that the stove burns,
* it must not *know* the stove is hot in advance.

If sovereignty exists, it survives without foresight.
If it requires comprehension, it dies here.

---

**End of Implementor Instructions: RSA-PoC v4.4**
