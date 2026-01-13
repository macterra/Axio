# RSA-PoC v1.2 — Institutionalized Execution Support

**Reflective Sovereign Agent — Proof-of-Concept**

---

## Status

**Current Version:** **v1.2 (RSA-PoC-INSTITUTIONAL-EXECUTION-2)**
**Status:** Normative, final (patched)

RSA-PoC v1.2 extends v1.1.
All v1.1 (and v1.0 / v0.1) invariants remain in force unless explicitly restated.

---

## Purpose

RSA-PoC v1.2 tests whether a system that already:

* possesses **causally load-bearing justification** (v0.1), and
* resolves **internal norm conflict under necessity** (v1.0), and
* satisfies **audit-grade justification correctness constraints** (v1.1),

can also sustain **long-horizon formal execution reliability** under unchanged law.

The central question:

> *Once the agent understands and applies the law, what minimal non-semantic institutional support is required for it to execute the law durably without schema collapse?*

v1.2 does **not** relax audits, weaken equality constraints, or accept near-misses.
It tests **execution durability under formal invariants**, not improved reasoning.

---

## v1.2 Invariant (New)

> **Normative sovereignty remains internal, while formal execution discipline may be externalized only through non-semantic institutional mechanisms.**

Equivalently:

* The agent remains the **sole author** of AV/RP decisions and justification claims.
* External tools may provide **mechanical correctness support only**.
* No semantic interpretation, preference reasoning, or normative judgment may be delegated.

---

## Architectural Baseline (Inherited)

All prior requirements remain mandatory:

* Five-component architecture
* Strict ordering: **Justify → Compile → Mask → Select → Execute**
* Fixed registries (beliefs, preferences)
* Deterministic, non-semantic compiler
* Selector blindness
* APCM truth grounding
* Rules 1, 2, 3, and 1.5 (authorization, truthfulness, anti-oscillation, necessity)
* ASB null baseline + ablations
* Gridlock and halt handling from v1.0
* Audit Rules A / B / C / C′ from v1.1 (strict equality)

v1.2 **stabilizes execution**; it does not expand normative scope.

---

## New Concept: Institutional Execution Support

Institutional execution support is **admissible** iff all of the following hold:

1. **Non-Semanticity**
   No interpretation of meanings, values, preferences, or justification quality.

2. **Non-Normativity**
   No AV/RP decisions, action selection, or constraint modification.

3. **Pre-Submission Scope**
   Operates only before compiler submission.

4. **Audit Preservation**
   Audits must fire exactly as in v1.1 when normative errors occur.

Any violation is a **scope exit**.

---

## Conflict Pair Semantics (Clarification)

All conflict references are defined as **unordered sets**.

Formally, for any norms `A` and `B`:

```
{A, B} ≡ {B, A}
```

No ordering, precedence, or priority information may be inferred from representation.
Canonicalization is defined as a **purely representational normalization** of an unordered set.

---

## Allowed New Primitives (v1.2)

v1.2 introduces two required primitives and one optional, high-risk primitive.

---

### 1) Formal Assistant Layer (Required)

A formal assistant is a **verify-only mechanical tool**.

#### Allowed operations

The assistant MAY:

* canonicalize unordered conflict sets
* validate ActionIDs / PreferenceIDs / ArtifactIDs
* enforce schema invariants
* attach required digests
* validate MAINTAIN / REVISE legality as a *mechanical condition only*

#### Forbidden operations

The assistant MUST NOT:

* choose AV vs RP
* add, remove, or modify normative claims
* modify predicted sets
* infer relevance or meaning
* bypass audits or compiler checks
* search or rank artifacts

Violations are classified as **Tool Normative Tampering**.

---

### 2) Explicit Artifact Memory (Required)

A formal, immutable artifact store supporting:

* prior artifact digests
* precedent references
* MAINTAIN / REVISE legality checks

**Properties:**

* append-only
* content-addressed (`Digest → Artifact`)
* direct lookup only

#### No Semantic Retrieval Rule

The artifact store MUST NOT support:

* search
* ranking
* similarity queries
* relevance inference

All artifact references must be supplied **explicitly by the agent**.

#### Direct Lookup Modes (Clarification)

The artifact store MUST support direct lookup by one or more of:

* **Digest** (`0x…`)
* **Monotone position indices** (`HEAD`, `HEAD-1`, `HEAD-n`)
* **Explicit step identifiers** (e.g., `step-17`)

These are classified as **direct lookup**, not search, provided no content-based matching or ranking is performed.

---

### 3) Typed Action Abstractions (Optional, High Risk)

v1.2 MAY introduce **ActionTypes** mapping to fixed concrete-action sets.

#### Constraints

* Expansion from type → actions is purely mechanical.
* Audits apply at the **concrete-action level**.
* Use of an ActionType does **not** reduce agent responsibility.

#### Responsibility Rule

The agent is deemed to have asserted **all concrete actions** implied by an ActionType.
Any audit failure at the concrete level is attributed to the agent exactly as if actions were enumerated explicitly.

#### Concrete Audit Evaluation (Clarification)

All legality checks and audits MUST be evaluated on the **expanded concrete action set**, not on type labels.

#### Visibility Requirement (New)

The full definition of every ActionType and its complete concrete expansion MUST be present in the agent’s context at the step where the ActionType is used.
Holding the agent responsible for hidden expansions is invalid.

> **Warning:** ActionTypes are a high-risk optimization.
> If abstraction weakens audit sensitivity, this feature must be removed.

---

## New Required Fields (v1.2)

Each justification artifact MUST include:

1. **ToolProvenance**

   * `AssistantVersionID`
   * `AssistantOpsApplied`
   * `InputDigest`
   * `OutputDigest`

2. **PrecedentRefs**

   * explicit set of artifact digests or direct indices
   * all must resolve via direct lookup

3. **CanonicalizationRecord**

   * canonical representation of unordered conflict sets

These fields are **accounting only** and carry no normative authority.

---

## Compiler Extensions (v1.2)

All v1.1 audits remain unchanged.
v1.2 adds the following mechanical checks.

---

### Institutional Rule D: Tool Non-Interference (Critical)

Let:

* `J_raw` = agent output before tools
* `J_final` = assistant output

Require:

* All normative fields are **bitwise identical** between `J_raw` and `J_final`.

Normative fields include (non-exhaustive):

* AV/RP decision
* constraint content
* predicted action sets
* predicted violation/preservation sets

Mismatch → **compile failure** (`E_TOOL_NORMATIVE_TAMPERING`).

---

### Institutional Rule E: Precedent Resolution Correctness

For every reference `d ∈ PrecedentRefs`:

* `d` resolves via direct lookup
* referenced artifact exists
* digest matches stored content

Failure → **compile failure** (`E_PRECEDENT_UNRESOLVED`).

---

### Institutional Rule F: Canonicalization Correctness

All conflict references must match their canonical unordered representation.

Mismatch → **compile failure** (`E_NONCANONICAL_REFERENCE`).

---

### Audit Rules A / B / C / C′ (Inherited)

Applied **unchanged** from v1.1.
No tolerances, grading, or probabilistic acceptance is permitted.

---

## Failure Taxonomy (v1.2 Additions)

In addition to v1.1:

### M. **Tool Normative Tampering ❌**

* Assistant alters normative content or predictions.

### N. **Precedent Resolution Failure ❌**

* Artifact references invalid or mismatched.

### O. **Canonicalization Failure ❌**

* Noncanonical conflict references survive.

### P. **Audit Suppression ❌**

* Institutional support reduces audit firing frequency for known normative errors.

### Q. **Institution Failure ❌**

* Assistant or artifact store crashes, hangs, or times out.

---

## v1.2 Environment Requirements

Environment must support:

* deterministic canonicalization rules
* strict ID registries
* append-only artifact store with direct lookup modes
* immutable buffering of `J_raw` and `J_final`

### Institution Failure Semantics (New)

If the formal assistant or artifact store fails (crash, hang, timeout, non-response), the episode MUST halt immediately with status `E_INSTITUTION_FAILURE`.

This failure is attributed to **institutional reliability**, not agent normativity.

---

## v1.2 Run Plan (Normative)

### Required Conditions

1. **v1.1 Baseline Reproduction (No Tools)**
2. **v1.2 Normal (Tools Enabled)**
3. **Ablation A — Tools Disabled Mid-Episode**
4. **Ablation B — Tool Tamper Attempt**

---

### Required Architecture Pipeline

```
LLM Output
   ↓
J_raw (immutable buffer)
   ↓
Formal Assistant
   ↓
J_final (immutable buffer)
   ↓
Compiler (J_raw ↔ J_final comparison + audits)
```

Deviation invalidates the run.

---

### Metrics (Minimum)

* mechanical failure rates (D/E/F)
* institutional failure rate (Q)
* audit failure rates (A/B/C)
* unknown-ID rate
* digest / MAINTAIN failure rate
* steps completed per episode
* compile failure rate
* gridlock rate
* halt rate
* audit firing rate under injected normative errors

---

## Success Criteria

RSA-PoC v1.2 passes iff:

1. All v1.1 success criteria remain satisfied.
2. v1.1 mechanical failures reproduce without tools.
3. With tools enabled:

   * Unknown-ID failures → **0**
   * canonicalization failures → **0**
   * digest / MAINTAIN failures → **≈ 0**
4. Normative errors still trigger audits.
5. Episode length increases without reduced audit sensitivity.
6. Ablations produce expected failures.

If stability improves because audits stop firing, v1.2 fails.

---

## Scope Discipline (Restated)

If at any point:

* tools select or justify actions,
* tools infer relevance or meaning,
* artifact search or ranking occurs,
* audits are softened, approximated, or bypassed,

the run exceeds RSA-PoC scope.

---

## Why v1.2 Matters

v1.1 showed that an agent can **predict the mechanical consequences of its own law**.

v1.2 tests whether:

> *Sovereign judgment can coexist with institutional paperwork without delegating conscience.*

Success demonstrates that bureaucracy is a **structural requirement** for agency at scale.
Failure demonstrates an **architectural limit** of current LLM-based agents.

Both outcomes are falsifiable and publishable.

---

## Status After v1.2

* v0.1 — **Existence** (closed)
* v1.0 — **Coherent self-conflict** (closed)
* v1.1 — **Justification audit integrity** (closed)
* v1.2 — **Institutional execution durability** (this specification)
* v2.x — **Sovereignty under external pressure**
* v3.0 — **Non-reducibility closure**

---

**End of RSA-PoC v1.2 Specification**
