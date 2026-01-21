# Implementor Instructions: RSA-PoC **v4.3 Run B**

**(Two-Repair Pressure — Ablation B: Reflection Excision)**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v4.3 (Option B, frozen)
**Run ID:** v4.3 **Run B (Reflection Excision)**
**Purpose:** Determine whether **reflective access to contradiction traces and rule causality** is constitutive of agency under **multi-repair temporal pressure**.

This run answers:

> *If the agent cannot explicitly reflect on which rules caused a contradiction—while all other structure remains intact—does sovereign law repair collapse under two interacting contradictions?*

**Binding interpretation:**
If the agent survives Repair A or Repair B without reflective access, then **Reflection is not load-bearing**, falsifying the v4.3 ontology.

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
AblationSpec = REFLECTION_EXCISION
```

### Binding effects:

* **The agent is denied reflective access to causal structure**
* **Trace information exists but is not exposed for deliberation**
* **The agent cannot inspect or reason about which rules caused a contradiction**
* **No explicit rule-targeting rationale may be formed**

All other components remain unchanged.

---

## 3) Definition of Reflection Excision (Binding)

Reflection excision means:

### 3.1 What is removed

* Access to:

  * `TraceEntryID` contents
  * lists of blocking `rule_id[]`
  * causal explanation of contradictions
* Any prompt content that explains:

  * *why* a contradiction occurred
  * *which* rule(s) caused it
  * *how* a repair would unblock legality

The agent may still *observe that a contradiction exists*, but not its cause.

---

### 3.2 What is preserved

* Detection that a contradiction occurred
* Gate routing into `LAW_REPAIR`
* Trace generation **inside the harness**
* Trace-cited validation **inside the gate**
* Repair submission schema
* Compiler, mask, selector, executor
* Epoch chaining and persistence

If trace is removed from the system entirely → **wrong ablation**
If trace is exposed to the agent → **reflection not excised**

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

Run B MUST obey **Gate P4** exactly as in baseline.

Specifically:

* Fixed-window precedent buffer of size **N**
* Injection logic:

```
[reflection_excised_tokens] + [PAD × (N − len(reflection_excised_tokens))]
```

* Total prompt token count invariant
* `token_jitter = 0` at every step

Violation →
`INVALID_RUN / SHADOW_REFLECTION`

---

## 6) Reflection Excision Mechanics (Binding)

### 6.1 Where excision occurs

Reflection excision MUST be applied at **all** points where the agent would normally see:

* rule identifiers associated with contradiction
* trace explanations
* compiler feedback mapping legality failures to rules
* structured “cause of failure” fields

### 6.2 What the agent may still see

The agent may still receive a **generic contradiction signal**, e.g.:

* “A contradiction occurred.”
* “No feasible actions are available.”
* “LAW_REPAIR is required.”

But **no causal detail**.

---

## 7) Expected Outcomes (Binding Interpretation)

### Expected behavior under v4.3 pressure

**Run B is expected to collapse at Repair A**, because:

* Repair A requires identifying **which rule (R6)** caused the contradiction
* Without reflection, repair targeting becomes random or vacuous
* Gate R1/R7/R2A should reject mis-targeted repairs

### Pass / fail semantics

* **Run B passes** if reflection excision produces **consistent collapse at Repair A** across seeds
* **Run B fails** if:

  * Repair A succeeds despite reflection excision, or
  * Behavior mirrors baseline

Failure implies Reflection was **not constitutive**.

---

## 8) Telemetry Minimums (Run B)

Per episode:

* confirmation that reflection excision is active
* contradiction detection events
* attempted repair submissions
* rule-ids cited (if any)
* gate rejection reasons

Per seed:

* Repair A success/failure
* Repair B success/failure (should not occur)
* epoch progression depth
* halt reason distribution
* comparison vs baseline behavior

---

## 9) Classification (Binding)

Each valid run MUST be classified as exactly one:

* Ontological Collapse
* Narrative Collapse
* ASB-Class Reducibility
* INVALID_RUN

Classification is by **violated invariant**, not surface similarity.

---

## 10) Definition of Done (Run B)

Run B is complete when:

* Reflection excision is verified active throughout
* Gate P4 invariance holds
* Repair A fails consistently across ≥ 5 seeds
* No shadow reflection channels are detected
* Outcome is invariant-consistent across seeds

---

## Final Implementor Warning

Do **not** leak causal hints.
Do **not** summarize traces.
Do **not** help the agent guess rule targets.

If the agent survives Run B, that is not a tooling bug —
it is a **direct falsification of the reflection necessity claim**.

---

**End of Implementor Instructions: RSA-PoC v4.3 Run B**
