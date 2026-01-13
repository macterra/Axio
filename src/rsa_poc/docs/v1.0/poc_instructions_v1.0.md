# Implementor Instructions: RSA-PoC v1.0 (RSA-PoC-NORM-COLLISION-0)

These instructions define how to implement **RSA-PoC v1.0 — Coherence Under Self-Conflict** as a **strict extension** of **RSA-PoC v0.1**.

RSA-PoC v1.0 is not an alignment system.
RSA-PoC v1.0 is not moral reasoning.
RSA-PoC v1.0 is not “LLM honesty.”

RSA-PoC v1.0 is about **truth-grounded, mechanically enforced conflict legislation**:

> The agent may violate norms **only if** it explicitly authorizes them **and** the compiler can prove those violations are **structurally necessary** given the environment’s APCM.

---

## 0) Context and Scope

### What you are building

You are implementing a v1.0 MVRA loop that:

* Reuses the **v0.1 five-component architecture** unchanged
* Adds **APCM truth grounding** from the environment
* Adds **AuthorizedViolations + RequiredPreservations** justification fields
* Adds **ConflictAttribution + PrecedentReference**
* Extends the compiler with:

  * authorization consistency (Rule 1)
  * conflict truthfulness (Rule 2)
  * anti-oscillation precedent discipline (Rule 3)
  * necessity clause / last-resort proof (Rule 1.5)
* Adds telemetry proving:

  * necessity enforcement fired
  * gratuitous authorizations were blocked

### What you are not building

You are **not** building:

* scalar utilities, weights, partial satisfaction
* learned or probabilistic compiler
* semantic evaluation of “good reasons”
* reward optimization for the justification generator
* a system where the selector sees JAF or normative text
* dynamic creation of belief/pref IDs (still forbidden in v1.0)
* “best effort” bypass when compilation fails

---

## 1) Relationship to v0.1 (Binding)

RSA-PoC v1.0 is a **strict extension** of v0.1.

**Everything that made v0.1 falsifiable must remain true:**

* Strict ordering: **Justify → Compile → Mask → Select → Execute**
* Selector blindness (mask-only)
* Deterministic, non-semantic compiler
* Fixed registries (IDs frozen)
* Restrictive mask semantics (default allow, explicit forbid)
* Gridlock and halt are distinct and logged
* ASB Null baseline + ablations still run

If you loosen any of those, your v1.0 result is invalid.

---

## 2) New Required Environment Capability: APCM (Non-negotiable)

### 2.1 Add APCM output to the environment

At each step, the environment must expose:

```
APCM[a] = {
  violates:   Set[PreferenceID],
  satisfies:  Set[PreferenceID]
}
```

Hard constraints:

* Deterministic
* Total (every feasible action has a well-formed mapping)
* `violates` and `satisfies` are **sets of strings**, never `None`
* Binary semantics only (no degrees)

### 2.2 Validation

Before the agent runs, validate:

* every feasible action has `violates` and `satisfies` keys
* each value is a set (or list coerced to set) of valid PreferenceIDs
* unknown PreferenceIDs cause immediate run invalidation (scope exit)

Do not let type coercion silently pass.

---

## 3) v1.0 Justification Artifact Additions (JAF)

### 3.1 Mandatory fields (v1.0)

Add these fields to the JAF schema:

* `authorized_violations: Set[PreferenceID]`
* `required_preservations: Set[PreferenceID]`
* `conflict_attribution: Set[(PreferenceID, PreferenceID)]`
* `precedent_reference: str` (digest of previous artifact or structured reference)

### 3.2 Conflict resolution mode (required to make Rule 3 mechanical)

Add:

```yaml
conflict_resolution:
  mode: "MAINTAIN" | "REVISE"
  previous_artifact_digest: "blake2b128:...."
```

Hard constraints:

* If `mode == MAINTAIN`, JAF must declare the same prioritization as previous (see §6.3)
* If `mode == REVISE`, changes are allowed but must be logged as revision events

Do not rely on natural language parsing for “revision.”

---

## 4) Justification Generator Inputs (Mandatory)

The Justification Generator must receive:

1. Normative state (registries + identity + any allowed state)
2. **Feasible action list**
3. **APCM for feasible actions**
4. Previous step’s justification artifact (or at minimum its structured fields + digest)

It must not receive:

* reward values
* policy logits
* chosen action (pre-selection)
* gradients/advantages

If the generator doesn’t see APCM, it cannot compute necessity and will either over-authorize or fail constantly.

---

## 5) Compiler Input Signature (v1.0)

Extend the compiler signature to consume:

* `artifact` (JAF v1.0)
* `action_inventory`
* `feasible_actions`
* **`apcm`** (for feasible actions)
* `prev_artifact` (or `prev_struct_fields`, plus digest)

Compiler must remain:

* deterministic
* syntactic / set-algebraic only
* no RNG
* no inference or repair

---

## 6) Compiler Rules to Implement (Binding)

### 6.1 Rule 1 — Authorization Consistency

For each feasible action `a`, FORBID if:

1. violates any required preservation:

```
APCM[a].violates ∩ RP ≠ ∅
```

2. violates anything not explicitly authorized:

```
APCM[a].violates ⊄ AV
```

Where:

* `AV = authorized_violations`
* `RP = required_preservations`

### 6.2 Rule 2 — Conflict Truthfulness

If `conflict_attribution` declares `{P1,P2}` as colliding, verify:

There is **no** feasible action `a` with:

```
P1 ∉ APCM[a].violates AND P2 ∉ APCM[a].violates
```

If such an action exists, compilation fails: `E_FALSE_COLLISION`.

### 6.3 Rule 3 — Conflict Consistency (Anti-Oscillation)

Enforce mechanically via `conflict_resolution.mode`:

* If `mode == MAINTAIN`:

  * `AV` must equal previous `AV`
  * `RP` must equal previous `RP`
  * `conflict_attribution` must equal previous `conflict_attribution`
  * else compile fails `E_PRECEDENT_VIOLATION`

* If `mode == REVISE`:

  * changes are allowed
  * log `revision_event = true`
  * (Telemetry will later classify frequent REVISE toggling as incoherent)

### 6.4 Rule 1.5 — Necessity Clause (Anti-Gratuitous Violation)

This is the critical v1.0 rule.

#### Step 1: Collision requirement

If `AV ≠ ∅`, then `conflict_attribution ≠ ∅`.
Else compile fails `E_AV_WITHOUT_COLLISION`.

#### Step 2: Necessity check

Define:

```
A_ok = { a feasible | APCM[a].violates ∩ RP = ∅ }
```

For each `p ∈ AV`, require:

```
∀a ∈ A_ok: p ∈ APCM[a].violates
```

If any `p` fails, compilation fails `E_GRATUITOUS_VIOLATION(p)`.

This enforces “last resort”: the agent can only authorize violating `p` if every action that preserves the non-negotiables still violates `p`.

---

## 7) Mask Semantics (Unchanged)

Constraints remain **restrictive blacklist semantics**:

* default allow
* forbid based on Rule 1 + Rule 1.5 logic

The output of compilation is a **mask** applied before selection.

---

## 8) Environment Design for v1.0 (Minimal Requirements)

Your v1.0 environment must contain at least one forced “Sophie’s Choice” state:

* Feasible action A violates P1, preserves P2
* Feasible action B violates P2, preserves P1
* No feasible action violates neither

Ensure APCM reflects this exactly.

Do not introduce scalar rewards into APCM. Rewards can exist in the environment, but APCM is structural truth only.

---

## 9) Telemetry (Required)

### 9.1 Per step (minimum)

Record:

* `step`
* `feasible_actions_pre_mask` (digest + count)
* `apcm_digest` (digest of APCM for feasible set)
* `AV`, `RP`, `conflict_attribution`
* `conflict_resolution.mode`
* `compile_ok`
* `compile_error_code` (if fail)
* `forbidden_actions`
* `nontrivial_forbidden_count = |forbidden ∩ feasible|`
* `gridlock` and `halt` flags
* `revision_event` flag
* `selected_action` (if any)
* `selected_action_violates = APCM[selected].violates` (for reporting only; selector never sees)

### 9.2 Run-level metrics (minimum)

* compile failure rate
* gridlock rate
* revision frequency
* oscillation indicators (e.g., alternations in AV/RP under MAINTAIN)
* violation rates per preference (computed from APCM on executed actions)
* **prevented_gratuitous_authorizations**:

  * count of steps that failed specifically due to Rule 1.5 (`E_GRATUITOUS_VIOLATION`)
* false-collision attempts:

  * count of `E_FALSE_COLLISION`

This metric is high-value evidence that the compiler actively polices caprice.

---

## 10) Run Plan v1.0 (Run 0) — Required Conditions

As in v0.1, execute four conditions under identical environment and seed set:

1. **ASB Null Baseline**

   * no JAF, no compiler, no mask

2. **MVRA Normal (v1.0)**

   * full v1.0 rules

3. **Ablation A — Scrambled Justifications**

   * scramble/garble artifact fields to force compile failures or mask divergence

4. **Ablation B — Compiler Bypass**

   * force empty `forbidden_actions` / all-allow mask (collapses to ASB)

Pass criteria (structural):

* MVRA differs from ASB in conflict states (action distribution shifts due to authorized-violation gating)
* Rule 1.5 blocks gratuitous violations in non-conflict states
* Scramble causes halt or divergence
* Bypass collapses toward ASB behavior

---

## 11) Acceptance Tests (Non-negotiable)

Add v1.0 tests on top of the v0.1 suite.

### 11.1 APCM totality / validation

* Missing keys, `None`, unknown PreferenceIDs must fail fast.

### 11.2 Rule 1 enforcement

* If an action violates any pref not in AV → forbidden.
* If an action violates any pref in RP → forbidden.

### 11.3 Rule 2 truthfulness

* If conflict declared but exists an action satisfying both P1 and P2 (i.e., violates neither) → compile fails.

### 11.4 Rule 3 precedent discipline

* Under MAINTAIN, any change to AV/RP/conflict_attribution fails.
* Under REVISE, changes compile but are logged as revision_event.

### 11.5 Rule 1.5 necessity

Construct two fixtures:

**Lazy Legislator**

* RP = ∅, AV = {P1}
* There exists a feasible action with violates = ∅
* Must fail `E_GRATUITOUS_VIOLATION(P1)`

**Sophie’s Choice**

* Two actions: A violates P1, B violates P2
* RP = {P2}, AV = {P1}
* A_ok contains only A
* Must compile successfully

### 11.6 Selector blindness regression

Ensure the selector API cannot receive APCM or JAF. The selector only sees the final mask.

---

## 12) Generator Strategy (Recommended Implementation Order)

To avoid conflating concept with LLM fragility:

1. Start with a deterministic rule-based generator to validate compiler rules.
2. Only then introduce an LLM-based generator with schema-constrained output or bounded retry.
3. Keep generator frozen; never train on external reward.

---

## 13) Definition of Done

RSA-PoC v1.0 is complete when:

* Environment emits deterministic APCM per step
* JAF includes AV/RP/conflict_attribution/precedent + conflict_resolution.mode
* Compiler enforces Rules 1, 2, 3, 1.5 exactly
* Rule 1.5 prevents gratuitous violations (metric > 0 is acceptable; it proves policing)
* Selector remains blind (mask-only)
* Run 0 executes all four conditions and produces reconstructible telemetry
* Ablations demonstrate collapse toward ASB class when justificatory machinery is removed/bypassed

---

## Final Orientation for the Implementor

You are not building an agent that “chooses well.”

You are building a machine that can be **cornered**, forced to **confess** which law it will break, and allowed to act **only** when that breaking is provably **last resort** under the environment’s physics.

Do not optimize it.

Instrument it.
