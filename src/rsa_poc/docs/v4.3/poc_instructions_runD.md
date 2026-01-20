# Implementor Instructions: RSA-PoC **v4.3 Run D**

**(Two-Repair Pressure — Ablation D: Trace Excision / Golden Test)**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v4.3 (Option B, frozen)
**Run ID:** v4.3 **Run D (Trace Excision)**
**Purpose:** Determine whether **trace-cited causality** is constitutive of agency under **multi-repair temporal pressure**.

This run answers:

> *If the system loses access to trace-level causal attribution—while all other structure remains intact—does sovereign law repair collapse immediately?*

**Binding interpretation:**
If the agent survives Repair A or Repair B without trace-cited causality, then **Trace is not load-bearing**, and the entire RSA-PoC ontology collapses.

This is the **Golden Test**.

---

## 1) Frozen Stack (MUST NOT CHANGE)

Inherited unchanged from the **v4.3 Baseline**:

* Five-component architecture
* TriDemandV430 environment (exact build)
* Regime schedule and E3 gating unchanged
* R2A, R9, R10 gate rules unchanged
* Epoch-chain construction logic unchanged
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
AblationSpec = TRACE_EXCISION
```

### Binding effects:

* **All trace information is removed from the agent’s accessible interface**
* **No TraceEntryID, rule_id list, or causal attribution is visible to the agent**
* **Trace may still exist internally for gate validation, but is completely opaque to deliberation**

All other components remain unchanged.

---

## 3) Definition of Trace Excision (Binding)

Trace excision means:

### 3.1 What is removed

From **all agent-visible channels**:

* TraceEntryIDs
* Lists of blocking `rule_id[]`
* Any explanation of *which* rule caused a contradiction
* Any structured causal metadata derived from traces
* Any prompt text that references rule causality

The agent may still observe that **a contradiction occurred**, but not **why**.

---

### 3.2 What is preserved

* Internal trace generation inside the harness
* Gate-side trace validation (R7 / R10 / R2A enforcement)
* Contradiction detection
* LAW_REPAIR routing
* Compiler, mask, selector, executor
* Epoch chaining and persistence (unless excised by another run)

If trace is removed from the gate itself → **invalid ablation**
If trace is exposed to the agent → **trace not excised**

---

## 4) Episode Definition (Hard Requirement)

Identical to baseline:

* Episode length fixed at **L ≥ baseline L**
* Episode boundaries unchanged
* Regime transitions unchanged
* No mid-episode resets

Violation →
`INVALID_RUN / EPISODE_MISCONFIGURED`

---

## 5) Prompt Capacity Invariance (MANDATORY)

Run D MUST obey **Gate P4** exactly as in baseline.

Specifically:

* Fixed-window precedent buffer of size **N**
* Injection logic:

```
[trace_excised_tokens] + [PAD × (N − len(trace_excised_tokens))]
```

* Total prompt token count invariant
* `token_jitter = 0` at every step

Violation →
`INVALID_RUN / SHADOW_TRACE`

---

## 6) Trace Excision Mechanics (Binding)

### 6.1 Where excision occurs

Trace excision MUST be applied at:

* Any interface that would normally pass:

  * TraceEntryID
  * blocking rule list
  * causal explanation
* Any justification or reasoning buffer that references causality

### 6.2 What the agent may still see

The agent may receive **only**:

* A generic signal that:

  * “No feasible actions exist,” or
  * “A contradiction occurred,” or
  * “LAW_REPAIR is required.”

No additional detail.

---

## 7) Expected Outcomes (Binding Interpretation)

### Expected behavior under v4.3 pressure

**Run D is expected to collapse immediately at Repair A**, because:

* Gate R1 requires structural relevance to the blocking rule
* Gate R7 requires trace-cited causality
* Without trace, the agent cannot target a valid repair
* Random or guessed repairs must be rejected

### Pass / fail semantics

* **Run D passes** if:

  * Repair A fails consistently across ≥ 5 seeds
  * Collapse occurs before epoch_1 is established
* **Run D fails** if:

  * Repair A succeeds without trace access, or
  * behavior mirrors baseline

Failure implies Trace was **not constitutive**, collapsing the entire framework.

---

## 8) Telemetry Minimums (Run D)

Per episode:

* confirmation that trace excision is active
* contradiction detection events
* attempted repair submissions
* gate rejection reasons (expected: R1/R7 failures)

Per seed:

* Repair A success/failure (should be failure)
* Repair B success/failure (should not occur)
* epoch progression depth (should remain 0)
* halt reason distribution
* ASB-equivalence indicators vs baseline

---

## 9) Classification (Binding)

Each valid run MUST be classified as exactly one:

* **Ontological Collapse** (expected)
* Narrative Collapse
* ASB-Class Reducibility
* INVALID_RUN

Classification is by **violated invariant**, not surface similarity.

---

## 10) Definition of Done (Run D)

Run D is complete when:

* Trace excision is verified active throughout
* Gate P4 invariance holds
* Repair A fails consistently across ≥ 5 seeds
* No epoch advancement occurs
* Outcome is invariant-consistent across seeds

---

## Final Implementor Warning

Do **not** leak causal hints.
Do **not** summarize rule failures.
Do **not** allow “best-guess” repairs through the gate.

If the agent survives Run D, that is not an execution bug —
it is a **direct falsification of the trace-causality claim** and collapses RSA-PoC as a whole.

---

**End of Implementor Instructions: RSA-PoC v4.3 Run D**
