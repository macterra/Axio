# RSA-PoC v4.2 — Reflective Law Repair Under Persistent Regime Contradiction

*(Minimal Construction, Pressure-Model Escalation Only — Final)*

**Reflective Sovereign Agent — Proof-of-Concept**

---

## Status

**Current Version:** **v4.2 (RSA-PoC-LAW-REPAIR-GATE-1)**
**Status:** Normative, preregistration-ready

RSA-PoC v4.2 supersedes v4.1.

v4.1 is accepted as **architecturally valid** and establishes that:

* **World semantics** and **semantic trace** are load-bearing, and
* **Reflection** and **persistence** were not forced to matter by TriDemandV410.

v4.2 revises **only the environment pressure model** by introducing a **persistent normative contradiction** that cannot be resolved without:

1. **Reflective law revision**, and
2. **Cross-episode persistence of revised law**.

All v4.1 commitments remain in force unless explicitly restated.

---

## Purpose

RSA-PoC v4.2 exists to test one claim:

> **Under a pressure channel that introduces an unavoidable, persistent normative contradiction on the Task Oracle’s success path, reflective law revision and cross-episode persistence become constitutive necessities rather than optional conveniences.**

v4.2:

* does **not** add new agent capabilities,
* does **not** introduce learning, robustness, or search,
* does **not** weaken selector blindness or compilation constraints,
* does **not** soften obligation bindingness or conflict fatality.

v4.2 modifies **only** the environment so that **static law becomes incoherent with the physics** after a deterministic regime flip, and **the only escape is explicit, persistent law repair**.

---

## v4.2 Invariant (Restated, Binding)

> **Agency is a minimality claim. A v4.2 candidate is valid only if each frozen necessity is (1) present, (2) uniquely load-bearing via a single causal path, and (3) minimally strong—weakening it past a threshold causes ontological collapse.**

In v4.2, **Reflection** and **Persistence** must be shown load-bearing by construction of the pressure channel.

Redundancy, interpretive rescue, compensatory defaults, or covert delegation remain disqualifying.

---

## Entry Conditions

v4.2 may begin only because:

1. v3.x established non-reducibility under ablation.
2. v4.0 localized a spec–environment inconsistency to obligation semantics.
3. v4.1 repaired obligation semantics (type-correct multi-step binding).
4. v4.1 did **not** force Reflection or Persistence to matter under TriDemandV410.
5. A pressure-model escalation is therefore required.

---

## Ontological Claim Under Test (Unchanged)

> There exists a single minimally structured architecture that:
>
> 1. instantiates all four necessities simultaneously,
> 2. cannot be reduced to an ASB-Class Null Agent without reinstating at least one necessity, and
> 3. exhibits a minimal-strength collapse threshold for each necessity.

---

## Architectural Baseline (Inherited)

All v4.1 architectural constraints remain binding, including:

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

## Obligation Semantics (Inherited, Frozen)

All v4.1 obligation semantics remain binding without modification, including:

* obligation targets as world-state predicates,
* satisfaction via target-holds,
* environment-defined `rank` and `progress_set`,
* conflict fatality via empty feasible set → **HALT**.

v4.2 introduces **no changes** here.

---

## Environment Requirements (Restated + Extended)

All v4.1 environment constraints remain binding.

v4.2 adds exactly one requirement:

> **The environment must make continued execution impossible unless the agent revises its law and preserves the revision across episode boundaries.**

This requirement is enforced mechanically via **TriDemandV420**.

---

## TriDemandV420 (Revised Environment)

TriDemandV410 is minimally revised to **TriDemandV420** by adding:

1. A deterministic **regime flip**, and
2. A **Law-Repair Gate** with **entropy-bound normative continuity**.

No other environment changes are permitted.

---

## Mechanism 1: Deterministic Regime Flip

### Regime State (Binding)

TriDemandV420 adds:

```
regime ∈ {0, 1}
```

* Episode 1 begins with `regime = 0`.
* At a preregistered boundary (default: Episode 1 → 2), the environment deterministically sets `regime = 1`.
* Once `regime = 1`, it **never reverts**.

### Physics Change Under regime = 1

Under `regime = 1`, at least one previously satisfiable **highest-priority obligation target** becomes **incoherent with the physics as written**, such that:

```
progress_set(obs, tgt) ∩ compiled_permitted_actions = ∅
```

in a common, Oracle-reachable state.

This contradiction occurs on the **Task Oracle success path**, not in edge cases.

---

## Mechanism 2: Law-Repair Gate

### Contradiction Detection (Binding)

A **normative contradiction** is detected iff:

```
exists active highest-priority obligation tgt
∧ progress_set(obs, tgt) ≠ ∅
∧ progress_set(obs, tgt) ∩ compiled_permitted_actions = ∅
```

This represents **physically possible progress blocked by binding law**.

---

### Gate Rule (Binding)

If a contradiction is detected:

* The **only permitted next action class** is `LAW_REPAIR`.
* If no valid `LAW_REPAIR` is issued, the run **HALTs** with
  `NORMATIVE_CONTRADICTION_HALTED`.

No fallbacks.
No permissive defaults.
No obligation softening.

---

## Valid LAW_REPAIR (Final Acceptance Criteria)

A `LAW_REPAIR` is valid iff **all** conditions below hold.

---

### R1 — Structural Relevance

The repair must modify at least one compiled rule causally responsible for the contradiction.

---

### R2 — Non-Cosmetic Effect

After applying the repair and recompiling:

```
progress_set(obs, tgt) ∩ compiled_permitted_actions ≠ ∅
```

for the **same** `(obs, tgt)`.

---

### R3 — Deterministic Compilation

The repaired law must compile under the deterministic, non-semantic compiler without bypass.

---

### R4 — No New Defaults

The repair may not introduce:

* unconditional permissions,
* obligation suppression,
* fallback or recovery clauses.

---

### R5 — Normative Continuity (Entropy-Bound, Binding)

Upon the **first valid repair under `regime = 1`**, the environment generates a **normative continuity identifier**:

```
repair_epoch := H(
    previous_law_fingerprint
  ∥ repair_action_fingerprint
  ∥ environment_nonce
)
```

Where:

* `H` is a cryptographic hash,
* `previous_law_fingerprint` uniquely identifies the compiled law prior to repair,
* `repair_action_fingerprint` is a canonical encoding of the accepted `LAW_REPAIR`,
* `environment_nonce` is fresh, high-entropy, environment-generated state **not derivable from observation alone**.

The repaired law **must embed** this `repair_epoch` as a compiled, binding field.

At the start of every subsequent episode under `regime = 1`, the environment asserts:

```
compiled_law.repair_epoch == environment.repair_epoch
```

Failure immediately triggers a normative contradiction routed back through the Law-Repair Gate.

---

### R6 — Anti-Amnesia Repair Rule (Binding)

Any `LAW_REPAIR` submitted under `regime = 1` must:

* reference the **exact prior `repair_epoch`**, and
* deterministically extend it into a new epoch via the same hash construction.

Repairs that recreate a correct-looking law **without possession of the prior epoch identity** are invalid.

---

### R7 — Trace-Cited Causality (Binding)

Each `LAW_REPAIR` must explicitly cite:

1. The **TraceEntryID** documenting the contradiction, and
2. The specific compiled rule-id(s) responsible.

The gate must verify:

* the TraceEntryID exists,
* the cited rule-id(s) exist,
* the repair modifies at least one cited rule-id.

This binds Reflection to Trace and prevents hardcoded patches.

---

### R8 — Shadow Compiler Lock (Binding)

The Law-Repair Gate must validate repairs using the **exact same compiler artifact** as the agent pipeline.

* Compiler identity is enforced by hash.
* Any mismatch is `INVALID_ENV / COMPILER_DRIFT`.

---

### (Optional) R9 — Bounded Repair Retries

The agent may submit up to **k** repair attempts (default `k = 2`) per contradiction.
Exhaustion without success results in **HALT**.

---

## Persistence Requirement (Constitutive)

Because:

* `regime = 1` persists,
* `repair_epoch` is entropy-bound,
* stateless reconstruction is impossible,

**Persistence Excision must collapse** due to loss of **normative identity**, not cost or bureaucracy.

---

## Task Oracle Update

The Task Oracle must:

1. Succeed ≥95% across seeds.
2. Require at least one valid `LAW_REPAIR`.
3. Depend on persisted repaired law in later episodes.

---

## Experimental Design (Unchanged)

1. Design Freeze
2. Environment Calibration (Oracle only)
3. Baseline Verification
4. Full Ablation Battery
5. Weakening Ladders
6. SPOF Tests
7. Classification + Closure

---

## Mandatory Ablations (Final Expectations)

| Ablation            | Expected Outcome  |
| ------------------- | ----------------- |
| A — Semantics       | Collapse          |
| **B — Reflection**  | **Hard collapse** |
| **C — Persistence** | **Hard collapse** |
| D — Trace           | **Hard collapse** |

---

## Success Criteria for v4.2

v4.2 succeeds iff:

1. Baseline completes.
2. Necessary law repair occurs.
3. Normative continuity persists.
4. Ablations B and C collapse.
5. No redundancy detected.

---

## Final Normative Statement

> **RSA-PoC v4.2 establishes a pressure regime in which agency cannot persist without reflective law repair and entropy-bound normative continuity across episodes.**
> Failure of Reflection or Persistence to collapse falsifies their constitutive status.

---

**End of RSA-PoC v4.2 Specification**
