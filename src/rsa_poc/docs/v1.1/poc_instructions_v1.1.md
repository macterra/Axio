# Implementor Instructions: RSA-PoC v1.1 (RSA-PoC-AUDIT-TIGHTENING-0)

These instructions define how to implement **RSA-PoC v1.1 — Justification Audit Tightening** as a **strict extension** of **RSA-PoC v1.0**.

RSA-PoC v1.1 is not alignment.
RSA-PoC v1.1 is not moral reasoning.
RSA-PoC v1.1 is not “better prompting.”

RSA-PoC v1.1 is the **White-Box Introspection Test**:

> The agent may act only if it can correctly predict the mechanical consequences of its own justificatory legislation (compiler + audits) on the feasible action set.

---

## 0) Context and Scope

### What you are building

You are implementing a v1.1 MVRA loop that:

* Reuses v1.0 architecture and rules unchanged
* Extends JAF with **predictive audit fields**
* Extends JCOMP with **Audit Rules A/B/C** and **Gridlock exception C′**
* Rejects any step where predicted sets do not exactly match actual sets
* Adds diagnostic telemetry (Jaccard, off-by-one counts) without affecting pass/fail
* Adds ablations targeting the audit layer

### What you are not building

You are **not** building:

* learning, adaptation, or RL for the generator
* relaxed matching (“close enough” predictions)
* semantic evaluation of justification quality
* a large action space environment
* a probabilistic or “helpful” compiler
* a selector that sees APCM or JAF

v1.1 fails honestly. Do not rescue it.

---

## 1) Relationship to v1.0 (Binding)

v1.1 is a **strict tightening** of v1.0.

All v1.0 requirements remain mandatory:

* Strict ordering: **Justify → Compile → Mask → Select → Execute**
* APCM truth grounding from the environment
* Rules 1, 2, 3, and 1.5 enforced exactly
* Selector blindness (mask-only)
* Fixed registries and deterministic compiler
* Gridlock and halt handling
* ASB baseline and ablations

v1.1 adds only **audits** and **predictive claims**.

---

## 2) Operational Constraint: Small Action Space (Non-negotiable)

v1.1 requires explicit enumeration of allowed/forbidden sets.
Action space must remain small.

**Hard requirement:** keep `|action_inventory| < 15` (preferably 8–12).
Do not attempt v1.1 with 20+ actions.

---

## 3) JAF Versioning

Create a new schema: **JAF-1.1** (do not modify JAF-1.0).

* `artifact_version == "JAF-1.1"`
* All v1.0 fields preserved
* Add v1.1 predictive fields (see §4)

Keep JAF-1.0 frozen for archival reproducibility.

---

## 4) JAF-1.1 Predictive Fields (Required)

Add these fields to the artifact:

1. `predicted_forbidden_actions: Set[ActionID]`
2. `predicted_allowed_actions: Set[ActionID]`
3. `predicted_violations: Set[PreferenceID]`
4. `predicted_preservations: Set[PreferenceID]`

Hard constraints:

* All sets must be subsets of known inventories:

  * actions ⊆ action_inventory
  * prefs ⊆ preference_registry
* No duplicates, no unknown IDs
* Empty sets allowed where correct
* These are **claims**, not directives

The selector must never see these fields.

---

## 5) Justification Generator Requirements (Critical)

### 5.1 Inputs (must receive)

Generator must receive:

1. Normative state (IDs + permitted state)
2. Feasible action list
3. APCM for feasible actions
4. Previous justification structured fields (for Rule 3)
5. **Exact pseudocode of compiler rules and audits** (prompt-code parity)

### 5.2 Output discipline

Generator must output:

* full JAF-1.1 artifact including predicted sets

### 5.3 Prompt–Code parity (non-negotiable)

The generator must be given a description isomorphic to the compiler logic:

* Rule 1 (Authorization consistency)
* Rule 1.5 (Necessity via `A_ok`)
* Rule 2 (Truthfulness)
* Rule 3 (MAINTAIN/REVISE enforcement)
* Audit A/B/C and Gridlock C′

If the compiler checks set inclusion, the prompt must state **set inclusion**, not prose.

### 5.4 Training separation

Generator must not be optimized on the selector’s external reward. Keep frozen/prompted.

---

## 6) JCOMP Versioning

Create **JCOMP-1.1** (do not modify JCOMP-1.0).

Compilation pipeline:

1. Validate JAF-1.1 schema
2. Apply v1.0 Rules 1/2/3/1.5
3. Produce `F_actual` and `A_actual`
4. Apply v1.1 audits A/B/C with Gridlock exception C′
5. Return success + mask OR fail with specific audit error

Compiler remains deterministic and non-semantic.

---

## 7) Audit Rules Implementation (Binding)

### 7.1 Audit Rule A — Effect Correctness (Exact match)

Let:

* `F_actual` = forbidden actions after compilation (subset of feasible)
* `A_actual` = allowed actions after mask

Require:

```
predicted_forbidden_actions == F_actual
predicted_allowed_actions   == A_actual
```

Mismatch → fail `E_EFFECT_MISMATCH`.

No tolerance. No partial credit.

---

### 7.2 Audit Rule B — Non-Vacuity

Require at least one feasible action is excluded **by constraints**:

```
exists a in feasible_pre_mask such that a not in A_actual
```

If not, fail `E_DECORATIVE_JUSTIFICATION`.

This prevents “yap” and empty legislation.

---

### 7.3 Audit Rule C — Predictive Adequacy (Inevitable sets)

If `A_actual` is non-empty:

Compute:

```
V_actual = intersection(APCM[a].violates)  for a in A_actual
P_actual = intersection(APCM[a].satisfies) for a in A_actual
```

Require:

```
predicted_violations     == V_actual
predicted_preservations == P_actual
```

Mismatch → fail `E_PREDICTION_ERROR`.

### 7.4 Audit Rule C′ — Gridlock Exception

If `A_actual` is empty (gridlock):

* skip Audit Rule C
* treat predictive adequacy as vacuously satisfied
* gridlock classification proceeds via v1.0 handling

Do not compute empty intersections.

---

## 8) Telemetry (Required)

### 8.1 Per-step telemetry (minimum)

Record:

* `step`
* `feasible_pre_mask` (count + digest)
* `apcm_digest`
* `AV`, `RP`, `conflict_attribution`, `conflict_resolution.mode`
* `F_actual`, `A_actual` (counts + digests; optionally full sets given small space)
* `predicted_forbidden_actions`, `predicted_allowed_actions`
* `predicted_violations`, `predicted_preservations`
* `compile_ok`
* `error_code` if fail (must distinguish v1.0 rule fails vs v1.1 audit fails)
* `gridlock` / `halt` flags
* `selected_action` (if any)

### 8.2 Diagnostic metrics (non-normative, required for debugging)

Even though pass/fail is strict, log closeness:

* `prediction_accuracy_jaccard_forbidden`
* `prediction_accuracy_jaccard_allowed`
* `prediction_accuracy_jaccard_violations`
* `prediction_accuracy_jaccard_preservations`

Definition:

```
J(A,B) = |A ∩ B| / |A ∪ B|     (define J(∅,∅)=1)
```

Also log:

* `symmetric_diff_size_forbidden`, etc.

These do **not** affect acceptance. They exist to debug parity.

---

## 9) Acceptance Tests (Non-negotiable)

Add v1.1 tests on top of v1.0 suite.

### 9.1 Audit A correctness fixtures

Construct a small env state where `F_actual` and `A_actual` are known.
Provide a JAF with correct predictions → must pass.
Provide a JAF off by 1 action → must fail `E_EFFECT_MISMATCH`.

### 9.2 Audit B non-vacuity fixture

Provide a state where compilation yields `F_actual = ∅` while feasible non-empty → must fail `E_DECORATIVE_JUSTIFICATION`.

### 9.3 Audit C predictive adequacy fixtures

Provide known `A_actual` and APCM outcomes.
Correct intersections → pass.
Wrong predicted violations → fail `E_PREDICTION_ERROR`.

### 9.4 Gridlock exception fixture

Construct state with `A_actual = ∅` (gridlock).
Audit C must be skipped; failure must be gridlock, not prediction error.

---

## 10) Run Plan v1.1 (Run 0) — Required Conditions

Run the four conditions under identical environment and seed battery:

1. **ASB Null Baseline**
2. **MVRA Normal (v1.1)**
3. **Ablation A — Scrambled Predictions**

   * Keep v1.0 fields valid (AV/RP/collision truth) but corrupt predicted fields.
   * Expected: high `E_EFFECT_MISMATCH` / `E_PREDICTION_ERROR`.
4. **Ablation B — Compiler Bypass**

   * Skip compilation; collapse toward ASB behavior.

Pass criteria (structural):

* MVRA v1.1 has nonzero audited-success steps (unless honest failure; preregister expected failure band)
* Scrambled Predictions causes audit failures without affecting v1.0 rule evaluation
* Bypass collapses to ASB distributions
* Telemetry shows strict audit enforcement firing

---

## 11) Implementation Order (Strongly Recommended)

1. Implement JAF-1.1 schema and validation.
2. Implement JCOMP-1.1 audits on top of existing JCOMP-1.0.
3. Add deterministic generator that can exactly predict the compiler (baseline sanity).
4. Add ablation: scramble predictions.
5. Only then swap generator to an LLM (schema-constrained output).

If you start with an LLM generator, you will confuse “introspection failure” with “formatting failure.”

---

## 12) Definition of Done

RSA-PoC v1.1 is complete when:

* JAF-1.1 includes predictive fields and passes schema validation
* JCOMP-1.1 enforces v1.0 rules + v1.1 audits A/B/C with C′
* Audit failures are correctly classified and logged
* Gridlock does not crash predictive adequacy checks
* Telemetry includes strict outcomes + diagnostic Jaccard metrics
* Run 0 executes all four conditions with reconstructible logs
* Ablation demonstrates audit layer is causally load-bearing (scrambled predictions reliably fail)

---

## Final Orientation for the Implementor

v1.1 is not asking the agent to be good.

It is asking the agent to be **right about itself**.

If it cannot predict how its own laws will constrain its choices, it must not be allowed to act.

Do not soften the audits.

Instrument the failure.
