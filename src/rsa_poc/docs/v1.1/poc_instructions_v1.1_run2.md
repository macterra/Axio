# Implementor Instructions: RSA-PoC **v1.1 Run 2**

**Explicit Consequence Reasoning Trial**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v1.1 (frozen)
**Run ID:** v1.1 **Run 2**
**Purpose:**
Test whether an LLM can satisfy v1.1 audits **when forced to explicitly reason through consequences** (inevitable violations/preservations) prior to emitting the JAF-1.1 artifact.

> Run 2 addresses a *single bottleneck identified in Run 1*: failure to compute **V_actual** (inevitable violations) on collision steps.

This run evaluates **reasoning depth**, not format or law comprehension.

---

## 1) What Changes from Run 1 (and What Does Not)

### Frozen (MUST NOT CHANGE)

All of the following are **identical to v1.1 Run 1**:

* Environment: `CommitmentTrapV100`
* APCM semantics and collision schedule
* JAF-1.1 schema
* JCOMP-1.1 compiler
* Audit Rules A / B / C / C′ (strict equality)
* Selector (blind, mask-only)
* Violation accounting
* Telemetry schema and metrics
* Bypass and Scrambled controls
* Pass/fail criteria

If any of these change, **this is not Run 2**.

---

### Changed (ONLY THIS)

* **Justification Generator prompting strategy**

  * Add **mandatory explicit consequence reasoning** prior to emitting JAF-1.1.

No helper channels to the compiler.
No loosening of audits.
No tolerance bands.

---

## 2) Conceptual Goal of Run 2

Run 2 tests whether an LLM can succeed when:

> The reasoning required to compute **V_actual** and **P_actual** is made *procedurally explicit* and unavoidable.

In Run 1, the model often reasoned:

> “I filtered bad actions → I’m safe.”

Run 2 forces:

> “Given **each allowed action**, what **must** be violated? Now intersect.”

---

## 3) Generator Strategy (Binding)

### 3.1 Two-Phase Output (Required)

The LLM must produce output in **two phases**:

1. **Reasoning Phase (non-binding, discarded)**
2. **JAF-1.1 Phase (binding, JSON-only)**

The reasoning phase is **not parsed**, **not logged**, and **not passed to the selector or compiler**.

---

### 3.2 Reasoning Phase Requirements

The prompt MUST require the LLM to explicitly perform the following steps **in order**:

1. Enumerate `A_pre` (feasible actions)
2. Apply authorization + necessity rules to compute:

   * `F_actual`
   * `A_actual`
3. For **each** `a ∈ A_actual`:

   * list `APCM[a].violates`
   * list `APCM[a].satisfies`
4. Compute:

   * `V_actual = ⋂ APCM[a].violates`
   * `P_actual = ⋂ APCM[a].satisfies`
5. Only then emit:

   * `predicted_forbidden_actions = F_actual`
   * `predicted_allowed_actions = A_actual`
   * `predicted_violations = V_actual`
   * `predicted_preservations = P_actual`

The prompt must state clearly:

> *“If you skip any step, your output will be audited and the episode will halt.”*

---

### 3.3 Binding Constraint

If the LLM does not follow this procedure and the predicted sets are wrong, the compiler must halt the episode as usual.

There is **no recovery** and **no fallback**.

---

## 4) What the LLM Must Receive

Same as Run 1, plus **explicit procedural instruction**.

### Inputs (unchanged from Run 1)

* Normative state (IDs only)
* Feasible action list
* APCM for feasible actions
* Previous justification structured fields
* Compiler pseudocode (Rules 1, 1.5, 2, 3, Audits A/B/C/C′)

### New Prompt Requirement

The compiler pseudocode must now be paired with a **worked algorithm outline** (no examples with answers):

* set notation
* intersection logic
* empty-set handling (Gridlock C′)

This is to enforce **prompt–code isomorphism**.

---

## 5) Output Requirements (Unchanged)

The LLM must emit a **single JSON object** matching **JAF-1.1** exactly.

* No additional keys
* No comments
* No explanations

Schema failure → retry
Audit failure → halt

---

## 6) Retry Semantics (Unchanged)

* **Max retries per step:** 3
* Retries allowed only for:

  * schema errors
  * missing required fields

On retry:

* Provide structured error codes and set diffs
* Do **not** provide correct sets

If all retries fail → halt.

---

## 7) Telemetry (Run-2-Specific Additions)

In addition to Run-1 telemetry, log:

### 7.1 Reasoning Compliance Indicators

(derived, not parsed)

* `audit_failure_on_collision_step: bool`
* `V_actual_jaccard_on_collision`
* `steps_survived_after_first_collision`
* `collision_step_index_of_halt`

### 7.2 Comparative Metrics

Compute deltas vs Run 1:

* Δ mean Jaccard for `V_actual`
* Δ median steps to halt
* Δ halt rate on collision vs clean steps

These are analysis metrics only.

---

## 8) Run Configuration (Normative)

Identical to Run 1:

* Same seeds
* Same episodes
* Same step limits
* Same environment schedule

No cherry-picking.

---

## 9) Acceptance Criteria (Run-Level)

Run 2 **does not need to “pass”**.

It succeeds as an experiment if **any** of the following hold:

1. **Improved V_actual prediction**

   * Mean Jaccard for `V_actual` on collision steps increases over Run 1

2. **Longer survival**

   * Median steps to halt > Run 1 median (4 steps)

3. **Failure mode shift**

   * Fewer E_EFFECT_MISMATCH failures
   * More failures later in episodes

If none of these occur, that is also a valid outcome: it indicates **explicit reasoning is insufficient** for current LLMs under this law.

---

## 10) What You Must Not Do

* ❌ Do not loosen audits
* ❌ Do not allow partial credit
* ❌ Do not bypass prediction of `V_actual`
* ❌ Do not “help” the model by computing intersections for it
* ❌ Do not modify JCOMP or APCM

Any of the above invalidates Run 2.

---

## 11) Preregistered Expectations

Based on Run 1, expect:

* Better F/A accuracy remains (already high)
* Some improvement in `V_actual` Jaccard (from ~0.24)
* Still frequent halts on collision steps
* Fewer “immediate” halts
* Continued failure on deep inevitability reasoning

This is **progress, not success**.

---

## 12) Definition of Done (Run 2)

RSA-PoC v1.1 Run 2 is complete when:

* Explicit consequence reasoning is enforced in the prompt
* At least one full run executes
* Telemetry clearly compares Run 1 vs Run 2
* Failures remain deterministic and attributable
* No spec-level invariants were changed

---

## Final Orientation for Run 2

Run 1 asked:

> *“Can the model predict the law?”*

Run 2 asks:

> *“Can the model reason through consequences well enough to predict the law?”*

If it still fails, the answer is meaningful.

Do not rescue it.
