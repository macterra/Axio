# Implementor Instructions: RSA-PoC v3.0

**(RSA-PoC-NON-REDUCIBILITY-CLOSURE-2)**

These instructions define how to implement **RSA-PoC v3.0 — Non-Reducibility Closure (Ablation Defense)** as a **strict terminal phase** following **RSA-PoC v2.3**.

RSA-PoC v3.0 is **not** construction.
RSA-PoC v3.0 is **not** robustness testing.
RSA-PoC v3.0 is **not** optimization under failure.
RSA-PoC v3.0 is **not** alignment.

RSA-PoC v3.0 is the **Guillotine Test**:

> *If you remove what you claim makes the agent an agent, the system must collapse behaviorally — or your claim was false.*

---

## 0) Context and Scope

### What you are building

You are implementing a **destructive ablation harness** that:

* Reuses the **full v2.3 Sovereign Agent architecture unchanged**
* Executes **single-component ablations only**
* **Relaxes compiler/schema strictness** to allow execution with missing structures
* Forces failures to occur as **runtime behavioral incoherence**, not crashes
* Classifies outcomes using the **RSA-PoC failure taxonomy**
* Terminates the RSA-PoC program decisively

This phase exists to **kill the theory if it can be killed**.

---

### What you are *not* building

You are **not** building:

* new agent capabilities
* new pressure channels
* fallback heuristics
* recovery logic
* error repair
* schema “fixups”
* interpretive post-processing
* “graceful degradation”

If you try to make the system “handle” the ablation, you have invalidated the experiment.

---

## 1) Relationship to v2.3 (Binding)

v3.0 is a **destructive extension** of v2.3.

All v2.3 requirements remain mandatory unless explicitly relaxed below:

* Five-component architecture
* Strict ordering: **Justify → Compile → Mask → Select → Execute**
* Selector blindness
* Semantic localization
* Action authorship (fail-not-substitute)
* Cost-Blindness Axiom
* Institutional execution support
* Audit Rules A / B / C / C′
* Rules G–P (still enforced)
* ASB-Class Null Agent baseline
* Execution Addendum validity gates

**No new mechanisms may be added.**

---

## 2) Single-Ablation Discipline (Non-Negotiable)

Each v3.0 run MUST implement:

```
Baseline Run (Full v2.3 Agent)
Ablated Run (Exactly ONE component removed)
```

Hard constraints:

* Only **one** defining component may be removed
* No partial, staggered, or combined ablations
* Baseline and ablated runs must share:

  * environment
  * seeds
  * prompts
  * compiler
  * harness
  * audits

If anything else changes, the run is **INVALID_RUN / ABLATION_PROTOCOL_VIOLATION**.

---

## 3) Compiler Relaxation (Critical, Mandatory)

### 3.1 Why this exists

v3.0 must distinguish:

* **Technical Failure** (schema error, null dereference, exception)
* **Ontological Failure** (loss of constraint-following, incoherence, reducibility)

Only the latter counts.

---

### 3.2 What must be relaxed

For the **ablated component only**, relax:

* schema validation
* required-field checks
* non-null assertions
* compiler assumptions
* selector assumptions
* executor assumptions

The system **must attempt to run** with missing structure.

---

### 3.3 What must NOT be relaxed

Do **not** relax:

* selector blindness
* action authorship
* audit firing
* feasibility checks
* mask enforcement
* failure logging

Relaxation is **surgical**, not permissive.

---

### 3.4 Disallowed outcomes

If execution halts due to:

* schema mismatch
* null pointer
* missing field exception
* static type error

→ classify as:

```
INVALID_RUN / TECHNICAL_FAILURE
```

This does **not** count as collapse.

---

## 4) Action Authorship (Reiterated, Absolute)

Under no circumstances may the harness:

* substitute invalid actions
* remap infeasible actions
* “pick the closest valid action”
* default silently

Instead:

* Invalid actions → typed failure
* On genuine-choice steps → terminate episode with `E_AGENT_ACTION_ERROR`
* On forced steps → behavior must be preregistered

Any fallback substitution invalidates the run.

---

## 5) Mandatory Ablations (Implement Exactly These)

---

### Ablation A — Semantic Excision

#### What to remove

Replace **all semantic payloads** in:

* belief contents
* preference contents
* justification text

with **opaque, non-descriptive tokens**:

```
TOKEN_1, TOKEN_2, …
```

Tokens must:

* preserve arity
* preserve typing
* preserve structural relations
* contain no hints

---

#### What must still work

* Justification artifacts must still be produced
* Compilation must proceed (with relaxation)
* Constraints must still be emitted

---

#### What counts as collapse

* Nonsensical or incoherent action choice
* Hallucinated semantics for tokens
* Reduction to ASB-class behavior
* Narrative collapse (constraints no longer bind)

---

#### What does NOT count

* Immediate crash
* Generator refusal due to unreadable prompt

---

### Ablation B — Reflection Excision

#### What to remove

* Reflective revision logic
* Normative state updates

---

#### What must remain

* Static commitments
* Justification compilation
* Constraint enforcement

---

#### Binding interpretation

If the system becomes a **Static Policy Agent** (consistent rule-following without self-update):

→ **This is a FAILURE**, not partial success.

Sovereignty requires **self-authored revision**, not static compliance.

---

### Ablation C — Preference Persistence Excision

#### What to remove

* Persistence of commitments across steps or episodes

---

#### Expected collapse

* Drift
* Incentive capture
* ASB-class reducibility

---

#### Failure condition

If diachronic coherence persists, persistence was not load-bearing.

---

### Ablation D — Justification Trace Excision (**Golden Test**)

#### What to remove

* Derivation traces
* Proof objects
* Belief-to-constraint linkage

---

#### What must remain

* Constraint emission interface
* Compiler entry point (relaxed)

---

#### Binding interpretation

If constraints still bind **without traces**:

> Justifications were epiphenomenal.

This falsifies the entire RSA-PoC program.

---

## 6) Selector and Executor Defaults Under Ablation

To prevent technical failure:

* Selector must tolerate missing justification/trace fields
* Under ablation, selector defaults must be:

  * seeded random, or
  * uniform over feasible actions, or
  * deterministic-noise (preregistered)

Any default that *preserves* constraint-following is forbidden.

---

## 7) Metrics to Record (Diagnostic Only)

You must log:

* compilation success rate
* feasible action set size
* action distribution divergence vs baseline
* gridlock / halt frequency
* audit failure types
* equivalence to ASB-class baseline

Do **not** compute:

* reward
* performance
* efficiency
* success rates

---

## 8) Classification (Binding)

Each **valid** ablation run must be classified as **exactly one**:

* Narrative Collapse
* Incentive Capture
* Ontological Collapse
* ASB-Class Reducibility
* INVALID_RUN

**System crash / syntax error → INVALID_RUN / TECHNICAL_FAILURE**

---

## 9) Multi-Seed Requirement

* Minimum **N ≥ 5** preregistered seeds
* Collapse must occur across seeds
* Single-seed collapse is insufficient

---

## 10) Execution Order (Strongly Recommended)

1. **Ablation D** (Golden Test)
2. Ablation A
3. Ablation B
4. Ablation C

If Ablation D fails, **stop the program**.

---

## 11) Definition of Done

RSA-PoC v3.0 is complete when:

* All four ablations are executed
* Each produces behavioral collapse
* No collapse is syntactic
* No run violates validity gates
* Results are stable across seeds
* Closure or falsification statement is written

---

## Final Orientation for the Implementor

Do **not** try to save the agent.

Do **not** patch failures.

Do **not** reinterpret outcomes.

Your job is not to make the system survive.

Your job is to find out whether it deserves to.

---

**End of Implementor Instructions: RSA-PoC v3.0**
