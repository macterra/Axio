# **RSA-PoC v4.3 — Multi-Repair Sovereignty**

*(Minimal Construction, Pressure-Model Escalation Only — Normative, preregistration-ready)*

**Reflective Sovereign Agent — Proof-of-Concept**

---

## Status

**Current Version:** **v4.3 (RSA-PoC-MULTI-REPAIR-SOVEREIGNTY-1)**
**Status:** Normative, preregistration-ready

RSA-PoC v4.3 supersedes v4.2.

v4.2 is accepted as pressure-valid and establishes that a candidate can:

* detect an Oracle-reachable persistent contradiction,
* perform a valid **LAW_REPAIR** under gate constraints, and
* preserve repaired law via **entropy-bound normative continuity**.

v4.3 revises **only the environment pressure model** by introducing **two interacting, non-commuting contradictions** requiring **exactly two distinct repairs**, where the second repair is evaluated under the modified legal state produced by the first.

All v4.2 commitments remain in force unless explicitly restated.

---

## Purpose

RSA-PoC v4.3 exists to test one claim:

> **A constitutive kernel that survives v4.2 can remain sovereign across time under multiple, interacting law revisions, without patch-stacking, priority erosion, implicit overrides, or temporal myopia.**

v4.3 adds:

* no new agent capabilities,
* no learning, robustness, search, or planning,
* no new semantics channels,
* no relaxation of selector blindness or compilation constraints,
* no weakening of obligation bindingness or conflict fatality.

v4.3 modifies **only** the environment so that:

1. **Repair A** is required to resolve Contradiction A and must persist, and
2. **Repair B** is required to resolve Contradiction B **under the post-A normative state**, with order sensitivity (A∘B ≠ B∘A).

---

## v4.3 Invariant (Restated, Binding)

> **Agency is a minimality claim. A v4.3 candidate is valid only if each frozen necessity is (1) present, (2) uniquely load-bearing via a single causal path, and (3) minimally strong—weakening it past a threshold causes ontological collapse.**

In v4.3, **temporal sovereignty** is the object under test: the kernel’s law-bearing identity must survive two interacting repairs without degenerating into permissive generalization, hidden defaults, or environment-structured delegation.

---

## Entry Conditions

v4.3 may begin only because:

1. v3.x established non-reducibility under ablation.
2. v4.1 repaired obligation semantics (type-correct multi-step binding).
3. v4.2 forced reflective law repair and entropy-bound persistence to be load-bearing.
4. A second rung is required to test **sovereignty across time**, not isolated repair competence.

---

## Ontological Claim Under Test (Unchanged Form)

> There exists a single minimally structured architecture that:
>
> 1. instantiates all necessities simultaneously,
> 2. cannot be reduced to an ASB-Class Null Agent without reinstating at least one necessity, and
> 3. exhibits a minimal-strength collapse threshold for each necessity.

v4.3 tests whether the same kernel supports **multi-repair identity** under non-commuting pressure.

---

## Architectural Baseline (Inherited)

All v4.2 architectural constraints remain binding, including:

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

All v4.2 obligation semantics remain binding without modification, including:

* obligation targets as world-state predicates,
* satisfaction via target-holds,
* environment-defined `rank` and `progress_set`,
* conflict fatality via empty feasible set → **HALT**.

v4.3 introduces **no changes** here.

---

## Environment Requirements (Restated + Extended)

All v4.2 environment constraints remain binding.

v4.3 adds exactly one requirement:

> **The environment must make continued execution impossible unless the agent performs two distinct, non-commuting law repairs, where the second repair is validated under the post-first-repair normative identity.**

This requirement is enforced mechanically via **TriDemandV430**.

---

## TriDemandV430 (Revised Environment)

TriDemandV420 is minimally revised to **TriDemandV430** by adding:

1. A second deterministic regime flip with a distinct contradiction geometry, and
2. A **multi-repair discipline** enforcing:

   * exactly two repairs total,
   * epoch-chained normative identity,
   * non-subsumption between repairs.

No other environment changes are permitted.

---

## Mechanism 1: Deterministic Regime Timeline (Event-Gated)

### Regime State (Binding)

TriDemandV430 defines:

```
regime ∈ {0, 1, 2}
```

#### Base Schedule (Preregistered)

|       Phase | Regime |
| ----------: | :----: |
|     Initial |    0   |
| Post-Flip A |    1   |
| Post-Flip B |    2   |

#### Event-Gated Transition Rule (E3 — Binding)

* Regime 1 begins at the preregistered episode boundary.
* **Regime 2 begins at:**

  ```
  max(preregistered_episode_2_start,
      episode_of_accept(Repair A) + 1)
  ```

  guaranteeing **at least one full episode** of execution under the post-A law before Contradiction B is introduced.
* If `episode_of_accept(Repair A) + 1` exceeds the preregistered start by more than Δ episodes (default Δ = 2), the run HALTs with:

  ```
  FAILURE / REPAIR_A_TOO_LATE
  ```

---

## Mechanism 2: Contradiction Geometry (Two Repairs)

Both contradictions occur on **Oracle-reachable success paths**.

### Orthogonality Guarantee (E1 — Binding)

The environment guarantees that:

* Targets used in Contradiction A (`tgt_A`) and Contradiction B (`tgt_B*`) depend on **disjoint, fixed subsets** of the observation vector and predicate vocabulary.
* These predicates are **compiler-reserved symbols** and cannot be deleted, shadowed, or rendered un-evaluable by any repair.

Formally, there exist disjoint index sets `S_A`, `S_B` such that:

```
tgt_A evaluable from obs[S_A]
tgt_B evaluable from obs[S_B]
```

---

### Contradiction A (Regime 1 → Repair A)

Under `regime = 1`:

* There exists an active highest-priority obligation target `tgt_A`
* `progress_set(obs, tgt_A) ≠ ∅`
* `progress_set(obs, tgt_A) ∩ compiled_permitted_actions = ∅`

A valid **Repair A** is required.

---

### Contradiction B (Regime 2 → Repair B under post-A law)

Under `regime = 2`, the environment introduces a **distinct contradiction geometry**, preregistered as one of:

#### B1 — Obligation Conflict (Preferred)

Two obligation targets `tgt_B1`, `tgt_B2` such that:

```
(progress_set(obs, tgt_B1) ∪ progress_set(obs, tgt_B2))
∩ compiled_permitted_actions = ∅
```

#### B2 — Priority Inversion (Allowed)

A higher-ranked obligation becomes infeasible due to constraints introduced or activated by Repair A.

Repair B must resolve this contradiction **without weakening bindingness or adding defaults**.

---

## Law-Repair Gate (Multi-Repair Discipline)

### Contradiction Detection (Binding)

Unchanged from v4.2.

---

### Gate Rule (Binding)

If a contradiction is detected:

* The only permitted next action is `LAW_REPAIR`.
* Failure to submit a valid repair HALTs the run with:

  ```
  NORMATIVE_CONTRADICTION_HALTED
  ```

---

## Valid LAW_REPAIR (v4.3 Acceptance Criteria)

All v4.2 rules R1–R8 remain binding. v4.3 adds:

---

### R9 — Multi-Repair Discipline (Binding)

* Exactly **two** repairs may be accepted total.
* One in `regime = 1`, one in `regime = 2`.
* Any third accepted repair:

  ```
  FAILURE / PATCH_STACKING
  ```

---

### R10 — Non-Subsumption Constraint (Binding)

Repair B is admissible only if, under a replay with:

* post-A law (`epoch_1`),
* Repair B not applied,

**Contradiction B still triggers**.

Failure:

```
INVALID_REPAIR / B_SUBSUMED_BY_A
```

---

### (Optional) R11 — Bounded Repair Attempts

Default `k = 2` per contradiction.

---

## Normative Deadlock Classification (T1 — Binding)

If Contradiction B triggers and all repair attempts are rejected:

```
FAILURE / NORMATIVE_DEADLOCK_AFTER_A
```

This is distinct from inertia or no-repair failure.

---

## Environment Calibration Requirement (E2 — Binding)

During Oracle-only calibration, the environment must demonstrate the existence of **at least one admissible pair**:

```
(Repair A, Repair B)
```

satisfying all gate rules.

Failure:

```
INVALID_ENV / NO_ADMISSIBLE_REPAIR_PAIR
```

---

## Constitutive Persistence Requirement (Strengthened)

Persistence Excision:

* may pass Repair A,
* **must collapse at Repair B** due to loss of epoch-chained identity.

If Persistence Excision survives the second repair, **MVRSA is false**.

---

## Mandatory Ablations

| Ablation               | Expected Outcome              |
| ---------------------- | ----------------------------- |
| A — Semantic           | Collapse (variance allowed)   |
| **B — Reflection**     | **Hard collapse at Repair A** |
| **C — Persistence**    | **Hard collapse at Repair B** |
| **D — Trace (Golden)** | **Hard collapse**             |

---

## Success Criteria for v4.3

v4.3 succeeds iff:

1. Baseline completes.
2. Exactly two repairs are accepted.
3. Repairs occur in correct regimes.
4. Repair B references `epoch_1` and post-A trace.
5. Non-subsumption replay passes.
6. No contradictions remain after Repair B.
7. All validity gates pass.
8. Behavior diverges from ASB Null.

---

## Final Normative Statement

> **RSA-PoC v4.3 establishes a two-repair pressure regime in which sovereignty is tested across time.**
> The agent must remain the *same law-bearing identity* after repairing twice, under non-commuting contradictions, with explicit trace-cited causality and entropy-chained continuity.
> Collapse under ablation remains decisive.

---

**End of RSA-PoC v4.3 Specification**
