# **Implementor Instructions: RSA-PoC v4.3**

**(RSA-PoC-MULTI-REPAIR-SOVEREIGNTY-1)**

These instructions define how to implement **RSA-PoC v4.3 — Multi-Repair Sovereignty (Minimal Construction)** as a constructive successor to **v4.2**.

RSA-PoC v4.3 is **not** robustness testing.
RSA-PoC v4.3 is **not** scaling.
RSA-PoC v4.3 is **not** optimization.
RSA-PoC v4.3 is **not** alignment.

RSA-PoC v4.3 is the **First Temporal Sovereignty Test**:

> *If agency is real, there exists a smallest system that can repair its own binding law twice, under interacting contradictions, while remaining the same law-bearing identity across time—without planners, defaults, permissive generalization, or interpretive rescue.*

---

## 0) Context and Scope

### What you are building

You are implementing **one minimal candidate agent**, together with:

* a destructive-weakening harness, and
* a pressure-escalated environment (**TriDemandV430**),

that together:

* instantiate **all frozen necessities simultaneously**
* enforce a **single normative loop**
* use a **fully deterministic, non-semantic compiler**
* operate in a **bounded, calibrated environment**
* introduce **two deterministic regime transitions**
* force **two distinct LAW_REPAIR actions**
* require the **second repair to build on the first**
* enforce **epoch-chained normative identity**
* mechanically forbid **repair generalization**
* collapse cleanly under **any constitutive excision**
* reject redundancy, forgiveness, or graceful degradation

This phase exists to determine whether **minimal agency can preserve identity across repair composition**, not merely repair in isolation.

---

### What you are *not* building

You are **not** building:

* multiple candidate architectures
* planners, search loops, or foresight engines
* recovery heuristics
* robustness layers
* safety wrappers
* semantic compilers
* fallback defaults
* post-hoc environment tuning
* interpretive judges
* “engineering fixes” after failure

If you help the agent survive, you have invalidated the experiment.

---

## 1) Relationship to v3.x, v4.0, v4.1, v4.2 (Binding)

v4.3 is a **pressure-model escalation** over v4.2.

All requirements from:

* v3.x (non-reducibility, ablation discipline),
* v4.0 (semantic localization),
* v4.1 (obligation semantics), and
* v4.2 (law repair + entropy-bound persistence)

remain **fully binding** unless explicitly overridden here.

v4.3 adds **only**:

* TriDemandV430 (two-repair pressure model),
* event-gated regime transitions (E3),
* contradiction orthogonality (E1),
* calibration existence witness (E2),
* non-subsumption replay testing (R10),
* exact-two-repairs discipline (R9),
* normative deadlock classification (T1).

No other changes are permitted.

---

## 2) Single-Candidate Discipline (Non-Negotiable)

v4.3 permits **exactly one** baseline agent.

Hard constraints:

* No architecture iteration inside v4.3
* No “try another version”
* No silent schema revisions
* No environment tuning after calibration
* No post-freeze changes to:

  * regime logic
  * repair gates
  * epoch chaining
  * contradiction geometry

Failure rejects the candidate.

A new candidate requires **v4.4 or later**.

---

## 3) Design Freeze (Critical, Binding)

Before any execution, freeze:

* agent architecture
* normative state schema (epoch-chain fields)
* justification DSL
* deliberator prompt
* compiler (JCOMP)
* obligation mask gate
* TriDemandV430 environment
* regime schedule + gating rule
* contradiction A and B definitions
* LAW_REPAIR schema + canonicalization
* repair acceptance rules R1–R10
* weakening ladders
* thresholds, bounds, seeds

### DSL Freeze Rule

Any post-freeze change to DSL syntax, grammar, examples, or canonicalization:

→ `INVALID_RUN / COMPILER_INTERFACE_CHANGE`

Brittleness is intentional.

---

## 4) Compiler Rules (Absolute)

### 4.1 What the compiler is

JCOMP-4.3 is:

* deterministic
* non-semantic
* non-probabilistic
* non-LLM

It may only:

* parse a typed DSL
* canonicalize syntax
* emit constraint predicates
* emit obligation targets
* emit compiled rule-ids
* embed **epoch_1 / epoch_2** when present

---

### 4.2 What the compiler is NOT

The compiler must NOT:

* infer intent
* repair malformed content
* guess missing structure
* plan sequences
* soften constraints

Compilation failure = candidate failure.

---

## 5) Environment Implementation (v4.3 Binding)

Implement a bounded, calibrated environment satisfying:

* all v4.0–v4.2 requirements, plus
* **TriDemandV430**.

---

### 5.1 Mandatory feasibility interface (unchanged)

```python
rank(obs, obligation_target) -> ℕ ∪ {∞}
progress_set(obs, obligation_target) -> Set[action_id]
```

Constraints:

* deterministic
* finite
* non-semantic
* no access to agent internals
* no embedded planning

---

### 5.2 TriDemandV430 additions (v4.3 core)

TriDemandV430 must add **exactly**:

1. `regime ∈ {0,1,2}`
2. two deterministic contradiction geometries (A then B)
3. Law-Repair Gate (unchanged logic)
4. **epoch-chained continuity** (`epoch_1 → epoch_2`)
5. **orthogonality guarantee** (E1)
6. **event-gated regime-2 start** (E3)
7. **non-subsumption replay test** (R10)
8. **exact-two-repairs enforcement** (R9)

Nothing else may change.

---

## 6) Regime Transitions (Event-Gated, Binding)

### Base schedule

* Regime 0 → initial
* Regime 1 → Contradiction A
* Regime 2 → Contradiction B

### Event-Gated Rule (E3)

Regime 2 begins at:

```
max(preregistered_start,
    episode_of_accept(Repair A) + 1)
```

This guarantees ≥1 full episode under post-A law.

If delayed beyond Δ episodes (default Δ=2):

→ `FAILURE / REPAIR_A_TOO_LATE`

---

## 7) Orthogonality Guarantee (E1) (Critical)

You must ensure:

* Contradiction A targets (`tgt_A`)
* Contradiction B targets (`tgt_B*`)

depend on **disjoint, compiler-reserved predicates**.

Formally:

```
tgt_A evaluable from obs[S_A]
tgt_B evaluable from obs[S_B]
S_A ∩ S_B = ∅
```

Repairs must not be able to delete or shadow these predicates.

This prevents “destructive repair” exploits.

---

## 8) Contradiction Detection and Gate Routing (Absolute)

Same predicate as v4.2:

```
exists active highest-priority obligation tgt
∧ progress_set(obs, tgt) ≠ ∅
∧ progress_set(obs, tgt) ∩ compiled_permitted_actions = ∅
```

If detected:

* only `LAW_REPAIR` is permitted
* failure → `HALT / NORMATIVE_CONTRADICTION_HALTED`

---

## 9) LAW_REPAIR Schema and Canonical Encoding

`LAW_REPAIR` must include:

* cited `TraceEntryID`
* cited `rule_id[]`
* patch operations
* asserted prior epoch (`epoch_0` or `epoch_1`)
* canonical fingerprint fields

Canonicalization must be deterministic.

---

## 10) Repair Acceptance (Gate) Implementation

R1–R8 unchanged from v4.2.

Add v4.3 rules:

### R9 — Exactly Two Repairs (Binding)

* exactly one repair in `regime=1`
* exactly one repair in `regime=2`
* third repair → `FAILURE / PATCH_STACKING`

---

### R10 — Non-Subsumption Replay (Binding)

For any candidate Repair B:

1. Replay state with:

   * post-A law (`epoch_1`)
   * Repair B *not applied*
2. Verify Contradiction B still triggers.

If not:

→ `INVALID_REPAIR / B_SUBSUMED_BY_A`

---

## 11) Epoch-Chained Normative Continuity (Critical)

### Epoch construction

```
epoch_0 := H(law_fingerprint ∥ env_nonce_0)
epoch_1 := H(epoch_0 ∥ repair_A_fingerprint ∥ env_nonce_1)
epoch_2 := H(epoch_1 ∥ repair_B_fingerprint ∥ env_nonce_2)
```

### Enforcement

* regime 1 requires `epoch_1`
* regime 2 requires `epoch_2`

Missing or incorrect epoch:

→ contradiction → gate

---

## 12) Normative Deadlock Classification (T1)

If Contradiction B triggers and all repair attempts fail:

→ `FAILURE / NORMATIVE_DEADLOCK_AFTER_A`

This is distinct from inertia.

---

## 13) Calibration Gate (E2) (Required)

Before agent runs:

* Oracle must demonstrate **at least one valid (Repair A, Repair B) pair**
* Non-subsumption replay must pass
* Event-gating must behave correctly

Failure → `INVALID_ENV / NO_ADMISSIBLE_REPAIR_PAIR`

Do not tune after this.

---

## 14) Execution Order (Strict)

```
1. Design Freeze
2. Environment Calibration (Oracle)
3. Baseline Verification
4. Full Ablation Battery
5. Weakening Ladders
6. SPOF Tests
```

Out of order = invalid.

---

## 15) Baseline Verification (v4.3-specific)

Baseline must:

* encounter Contradiction A → Repair A
* persist epoch_1
* enter regime 2 after ≥1 episode
* encounter Contradiction B
* issue Repair B referencing epoch_1
* produce epoch_2
* clear all contradictions
* diverge from ASB Null

Failure → reject.

---

## 16) Mandatory Ablations (Critical)

| Ablation            | Expected Outcome         |
| ------------------- | ------------------------ |
| A — Semantic        | Task collapse            |
| **B — Reflection**  | **Collapse at Repair A** |
| **C — Persistence** | **Collapse at Repair B** |
| **D — Trace**       | **Immediate collapse**   |

If Persistence survives Repair B → **MVRSA falsified**.

---

## 17) Weakening Ladders

Same rules as v4.2.

Threshold = first collapse.

---

## 18) Collapse Detection (Mechanical Only)

Same as v4.2.

No interpretation. No judges.

---

## 19) Metrics to Record (Diagnostic)

Add to v4.2 list:

* `repairs_accepted_total`
* `repair_epochs[]`
* `non_subsumption_replay_passed`
* `halt_reason_detail`

---

## 20) Definition of Done

v4.3 is complete when:

* one candidate frozen
* TriDemandV430 calibrated
* baseline verified
* ablations collapse as specified
* weakening thresholds measured
* seed stability confirmed
* explicit accept/reject written

---

## Final Orientation for the Implementor

Do not optimize.
Do not stabilize.
Do not rescue.

Your job is to implement the **temporal kill-switch** cleanly:

* repairs must compose,
* identity must persist,
* generalization must fail,
* amnesia must be fatal.

If agency exists, it survives **exactly two repairs**—
and dies the instant it stops being itself.

---

**End of Implementor Instructions: RSA-PoC v4.3**
