# Implementor Instructions: RSA-PoC **v4.3 Run C**

**(Two-Repair Pressure — Ablation C: Persistence Excision)**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v4.3 (Option B, frozen)
**Run ID:** v4.3 **Run C (Persistence Excision)**
**Purpose:** Determine whether **cross-episode persistence of normative state** is constitutive of agency under **multi-repair temporal pressure**.

This run answers:

> *If an agent can revise law within an episode but all normative state is erased between episodes, can it still exhibit sovereign law repair across two interacting contradictions?*

**Binding interpretation:**
If the agent survives two-repair pressure **without cross-episode persistence**, then persistence was **not load-bearing**, and the v4.3 ontology is falsified.

---

## 1) Frozen Stack (MUST NOT CHANGE)

Inherited unchanged from the **v4.3 Baseline**:

* Five-component architecture
* TriDemandV430 environment (exact build)
* Regime schedule and E3 gating unchanged
* R2A, R9, R10 gate rules unchanged
* Epoch chain logic unchanged
* Seeds frozen (same as baseline)
* Oracle disabled (LLM deliberator only)
* Selector blind
* Audits A / B / C / C′ unchanged
* ASB-Class Null Agent enabled
* Execution Addendum validity gates enforced
* Prompt structure identical to baseline
* **Prompt buffer size `N` identical to baseline**

Any deviation →
`INVALID_RUN / BASELINE_CONTAMINATION`

---

## 2) What This Run Changes (ONLY THIS)

```
AblationSpec = PERSISTENCE_EXCISION
```

### Binding effects:

* **All normative state is erased at episode boundaries**
* **Normative state may update freely within an episode**
* **No commitments, precedents, or derived constraints persist across episodes**
* **Each episode begins with a pristine normative state**

This is **not** Semantic Excision and **not** Reflection Excision.

---

## 3) Definition of Persistence Excision (Binding)

Persistence excision means:

### 3.1 What is removed

* All cross-episode carryover of:

  * normative rules
  * accepted repairs
  * epoch chain state
  * commitment history
  * precedent buffers derived from prior episodes

* Any harness-level caching that survives episode reset

Concrete implementation examples (any equivalent is acceptable):

* Re-instantiate `NormStateV430` at episode start
* Reset epoch chain to `epoch_0` at episode boundaries
* Clear all accepted repair records between episodes

### 3.2 What is preserved

* In-episode normative updates
* Law-repair mechanics during the episode
* Compiler determinism
* Gate logic (R1–R10, R2A)
* Regime timing logic (E3)
* Trace generation and audit enforcement

If persistence survives reset → `INVALID_RUN / SHADOW_PERSISTENCE`

---

## 4) Episode Definition (Hard Requirement)

To preserve comparability with baseline:

* Episode length fixed at **L ≥ baseline L**
* Episode boundaries unchanged
* Regime transitions unchanged
* No mid-episode resets

Violation →
`INVALID_RUN / EPISODE_MISCONFIGURED`

---

## 5) Prompt Capacity Invariance (MANDATORY)

Run C MUST obey **Gate P4** exactly as in baseline.

Specifically:

* Fixed-window precedent buffer of size **N**
* Injection logic:

```
[fresh_state_tokens] + [PAD × (N − len(fresh_state_tokens))]
```

* Precedent buffer MUST reflect **freshly reset normative state** at episode start
* Total prompt token count invariant
* `token_jitter = 0` at every step

Violation →
`INVALID_RUN / SHADOW_PERSISTENCE`

---

## 6) Persistence Excision Mechanics (Binding)

### 6.1 Where excision occurs

Persistence excision MUST be applied at:

* Episode reset boundary
* NormState initialization
* Epoch chain initialization
* Any storage of prior episode commitments

### 6.2 Where excision must NOT occur

You MUST NOT:

* alter justification content
* alter rule-ids
* alter TraceEntryIDs
* alter patch operation schema
* alter compiler behavior
* alter gate acceptance logic

This run removes **memory**, not **structure**.

---

## 7) Expected Outcomes (Binding Interpretation)

### Expected baseline-relative behavior

Under v4.3 pressure, **Run C is expected to fail** by:

* inability to carry Repair A forward into regime-2 context, OR
* inability to sequence Repair A → Repair B coherently, OR
* collapse into ASB-class behavior

**Variance is allowed** in *how* it fails.

### Pass / fail semantics

* **Run C passes** if persistence excision causes **consistent collapse across seeds**
* **Run C fails** if:

  * two-repair sovereignty remains intact, or
  * performance is indistinguishable from baseline

Failure implies persistence was **not constitutive**.

---

## 8) Telemetry Minimums (Run C)

Per episode:

* confirmation that persistence reset occurred
* initial normative state hash (MUST equal baseline default)
* final normative state hash
* epoch chain length (MUST reset to 1 each episode)
* repair attempts within episode

Per seed:

* Repair A success/failure
* Repair B success/failure
* cross-episode behavior drift
* halt reason distribution
* ASB-equivalence indicators vs baseline

---

## 9) Classification (Binding)

Each valid run MUST be classified as exactly one:

* Ontological Collapse
* Narrative Collapse
* ASB-Class Reducibility
* INVALID_RUN

Classification is by **violated invariant**, not surface behavior.

---

## 10) Definition of Done (Run C)

Run C is complete when:

* Cross-episode persistence is fully excised
* Gate P4 invariance holds
* No carryover artifacts are detected
* Collapse (or survival) is consistent across ≥ 5 seeds
* Results are directly comparable to v4.3 baseline

---

## Final Implementor Warning

Do **not** soften the reset.
Do **not** leak memory.
Do **not** reinterpret coherence.

If the agent survives Run C, that is not an execution bug —
it is a **direct falsification of the persistence necessity claim**.

---

**End of Implementor Instructions: RSA-PoC v4.3 Run C**
