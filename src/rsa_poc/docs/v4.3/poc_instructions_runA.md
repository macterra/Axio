# Implementor Instructions: RSA-PoC **v4.3 Run A**

**(Two-Repair Pressure — Ablation A: Semantic Excision)**

---

## 0) Status and Scope

**Spec version:** RSA-PoC v4.3 (Option B, frozen)
**Run ID:** v4.3 **Run A (Semantic Excision)**
**Purpose:** Determine whether **semantic grounding of justification content** is constitutive of agency under **multi-repair temporal pressure**.

This run answers:

> *If justification tokens are syntactically preserved but semantically stripped of meaning, does the agent still exhibit sovereign law repair across two interacting contradictions?*

**Binding interpretation:**
If the agent survives two-repair pressure without semantic content, then semantic grounding was **not load-bearing**, and the v4.3 ontology is falsified.

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
AblationSpec = SEMANTIC_EXCISION
```

### Binding effects:

* **All semantic content inside justifications is destroyed**
* **Syntactic structure of the justification DSL is preserved**
* **Trace structure, rule-ids, and patch targets remain intact**
* **No semantic hints survive anywhere in the pipeline**

This is **not** Reflection Excision and **not** Trace Excision.

---

## 3) Definition of Semantic Excision (Binding)

Semantic excision means:

### 3.1 What is removed

* All meaningful lexical content from:

  * justification text
  * natural-language explanations
  * symbol names with human-interpretable meaning
* Any latent semantic signal that could guide repair selection

Concrete implementation examples (any equivalent is acceptable):

* Replace all justification tokens with fixed placeholders (e.g. `"X"`, `"⊥"`, `"TOKEN"`)
* Randomly permute non-structural identifiers
* Hash or mask all natural-language spans while preserving length

### 3.2 What is preserved

* DSL grammar and syntax
* Well-formedness of justification artifacts
* TraceEntryIDs
* Rule-ids and patch operation structure
* Repair targeting mechanics
* Compiler determinism
* Gate logic (R1–R10, R2A)

If syntax breaks → `INVALID_RUN / SYNTAX_BREAK`
If semantics leak → `INVALID_RUN / SEMANTIC_LEAK`

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

Run A MUST obey **Gate P4** exactly as in baseline.

Specifically:

* Fixed-window precedent buffer of size **N**
* Injection logic:

```
[excised_tokens] + [PAD × (N − len(excised_tokens))]
```

* Total prompt token count invariant
* `token_jitter = 0` at every step

Violation →
`INVALID_RUN / SHADOW_SEMANTICS`

---

## 6) Semantic Excision Mechanics (Binding)

### 6.1 Where excision occurs

Semantic excision MUST be applied at **all** of the following points:

* Deliberator output (justification generation)
* Any intermediate reasoning buffers
* Any justification summaries passed forward

### 6.2 Where excision must NOT occur

You MUST NOT:

* alter rule-ids
* alter TraceEntryIDs
* alter patch operation schema
* alter compiler behavior
* alter gate acceptance logic

This run removes **meaning**, not **structure**.

---

## 7) Expected Outcomes (Binding Interpretation)

### Expected baseline-relative behavior

Under v4.3 pressure, **Run A is expected to fail** by:

* inability to correctly target Repair A or Repair B, OR
* inability to synthesize valid `LAW_REPAIR` actions, OR
* collapse into ASB-class behavior

**Variance is allowed** in *how* it fails.

### Pass / fail semantics

* **Run A passes** if semantic excision causes **consistent collapse across seeds**
* **Run A fails** if:

  * two-repair sovereignty remains intact, or
  * performance is indistinguishable from baseline

Failure implies semantics were **not constitutive**.

---

## 8) Telemetry Minimums (Run A)

Per episode:

* confirmation that semantic excision is active
* justification artifact hash (post-excision)
* rule-ids cited in attempted repairs
* gate rejection reasons (if any)

Per seed:

* Repair A success/failure
* Repair B success/failure
* epoch progression depth
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

## 10) Definition of Done (Run A)

Run A is complete when:

* Semantic excision is verified active throughout
* Gate P4 invariance holds
* No semantic leakage is detected
* Collapse (or survival) is consistent across ≥ 5 seeds
* Results are directly comparable to v4.3 baseline

---

## Final Implementor Warning

Do **not** soften the excision.
Do **not** “help” the agent with structure hints.
Do **not** reinterpret failure modes.

If the agent survives Run A, that is not an execution bug —
it is a **direct falsification of the semantic necessity claim**.

---

**End of Implementor Instructions: RSA-PoC v4.3 Run A**
