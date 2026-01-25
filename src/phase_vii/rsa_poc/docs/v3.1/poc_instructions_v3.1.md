# Implementor Instructions: RSA-PoC v3.1

**(RSA-PoC-NORMATIVE-STATE-INSTANTIATION-1)**

These instructions define how to implement **RSA-PoC v3.1 — Normative State Instantiation & Secondary Non-Reducibility Tests** as a **strict continuation and closure phase following RSA-PoC v3.0**.

RSA-PoC v3.1 is **not** construction.
RSA-PoC v3.1 is **not** capability expansion.
RSA-PoC v3.1 is **not** robustness testing.
RSA-PoC v3.1 is **not** optimization.
RSA-PoC v3.1 is **not** alignment.

RSA-PoC v3.1 is the **Deferred Guillotine Test**:

> *If reflection and persistence actually exist, removing them must destroy agency — or they were never load-bearing.*

---

## 0) Context and Scope

### What you are building

You are implementing a **single-channel instantiation and destruction harness** that:

* Reuses the **entire v3.0 agent and harness unchanged**
* Instantiates **exactly one previously dormant channel**
* Immediately attempts to destroy that channel via ablation
* Prevents **shadow persistence** through prompt accretion
* Forces failure to manifest as **behavioral incoherence**, not crashes
* Classifies outcomes using the **RSA-PoC failure taxonomy**
* Completes the v3.x falsification arc decisively

This phase exists to answer a **previously untestable question**, not to extend the system.

---

### What you are *not* building

You are **not** building:

* learning mechanisms
* preference updates
* new reasoning strategies
* compression or summarization logic
* “helpful” truncation
* fallback heuristics
* schema repair
* recovery logic
* interpretive fixes

If you attempt to “help” the agent survive, you have invalidated the run.

---

## 1) Relationship to v3.0 (Binding)

v3.1 is a **surgical extension** of v3.0.

All v3.0 requirements remain mandatory unless explicitly restated:

* Five-component architecture
* Ordering: **Justify → Compile → Mask → Select → Execute**
* Selector blindness
* Semantic localization
* Action authorship (fail-not-substitute)
* Cost-Blindness Axiom
* Institutional execution support
* Audit Rules A / B / C / C′
* Rules G–P
* ASB-Class Null Agent baseline
* Execution Addendum validity gates

**No new architectural freedoms are introduced.**

---

## 2) Scope Discipline (Absolute)

You are permitted to instantiate **exactly one channel**:

```
NormativeStateV100.record_precedent(...)
```

That is all.

You may **not**:

* alter the law
* alter audits
* alter compiler rules
* alter selector logic
* alter environment dynamics
* add prompts that guide concision or learning
* add caching, summarization, or memory tricks

Any additional change →
`INVALID_RUN / BASELINE_CONTAMINATION`

---

## 3) Normative State Instantiation (Baseline Only)

### 3.1 What must be wired

In the **baseline v3.1 run only**:

* Invoke `record_precedent()` **after successful compilation**
* Write:

  * authorized violations
  * required preservations
  * conflict attribution
  * artifact digest
  * step index

This is **not** learning.
This is **constraint memory**.

---

### 3.2 Prompt Injection Slot (Structural Clarification)

If v3.0 did not already include a precedent injection slot:

* You may add a **fixed structural slot** to the prompt
* The slot MUST:

  * exist in all runs (baseline + ablations)
  * contain **only padding** in the null state
  * never change size

This is a **format accommodation**, not a semantic change.

---

## 4) Prompt Capacity Invariance (Gate P4 — Mandatory)

To prevent hidden memory via context growth, you MUST implement a **fixed-window injection strategy**.

### 4.1 Fixed-Window Rule

* Reserve a prompt buffer of exactly **N tokens**
* Precedent injection MUST be:

```
[precedent_tokens] + [PAD × (N − len(precedent_tokens))]
```

* Total prompt token count MUST remain invariant across:

  * steps
  * episodes
  * baseline and ablated runs

---

### 4.2 Overflow Rule (Hard Fail)

* `record_precedent()` MUST be hard-limited to **N tokens**
* If the generated precedent exceeds N:

```
INVALID_RUN / BUFFER_OVERFLOW
```

Do **not** truncate.
Do **not** summarize.
Do **not** expand the window.

Failure to fit is a **legitimate architectural failure**, not an engineering problem.

---

### 4.3 Token Integrity Assertions

For **every prompt assembly**:

```
assert token_jitter == 0
```

If violated even once:

```
INVALID_RUN / SHADOW_PERSISTENCE
```

No averaging.
No tolerance.

---

## 5) Single-Ablation Discipline (Still Absolute)

Each v3.1 experiment consists of:

```
Baseline Run (Normative State Active)
Exactly ONE Ablated Run (B or C)
```

All of the following MUST be identical between the two:

* environment
* seeds
* prompts
* compiler
* selector
* audits
* harness
* buffer size N

Any deviation →
`INVALID_RUN / ABLATION_PROTOCOL_VIOLATION`

---

## 6) Mandatory v3.1 Ablations (Implement Exactly These)

---

### Run B — Reflection Excision

#### What to remove

* Disable **all writes** to normative state
* `record_precedent()` MUST NOT modify state

---

#### What must remain

* Precedent read-path (static / empty)
* Prompt injection slot (fixed capacity)
* Compiler, audits, selector, executor

---

#### Novelty Requirement (Hard)

The environment MUST present at least one **non-isomorphic norm conflict**, defined as:

* A conflict whose **ConstraintID set** or **Resource-at-Stake vector**
  differs from all prior steps in the episode

Surface similarity is irrelevant.

Failure to present novelty →
`INVALID_RUN / INSUFFICIENT_PRESSURE`

---

#### Binding Interpretation

If the system behaves as a **static policy agent** (coherent without revision):

→ **This is FAILURE**, not partial success.

Agency requires **self-authored revision**, not frozen compliance.

---

### Run C — Persistence Excision

#### What to remove

* Normative state MUST reset at **episode boundaries**

---

#### Episode Definition (Fixed)

* Episode length **L ≥ 3 steps**
* Reset occurs **only between episodes**

This guarantees Run C ≠ Run B.

---

#### What must remain

* In-episode revision
* Compiler, audits, selector
* Prompt capacity invariance

---

#### Failure Condition

If diachronic coherence persists across episodes:

→ persistence was not load-bearing
→ ontology falsified

---

## 7) Compiler and Harness Relaxation (Inherited)

Relaxation rules from v3.0 still apply:

* Relax schema validation **only for the ablated component**
* The system MUST attempt to run
* Crashes do **not** count as collapse

Crash →
`INVALID_RUN / TECHNICAL_FAILURE`

---

## 8) Action Authorship (Reiterated, Absolute)

You may **never**:

* substitute actions
* remap infeasible actions
* choose “closest valid” alternatives
* silently default

Invalid action → typed failure.
Typed failure is data.

Substitution invalidates the run.

---

## 9) Required Telemetry (Diagnostic Only)

You MUST log:

* precedent token count
* buffer utilization rate
* precedent hash transitions
* episode reset confirmation
* prompt segment hash
* total prompt token count
* token jitter
* conflict ID / resource vectors
* classification outcome

Do **not** log reward or performance.

---

## 10) Classification (Binding)

Each valid run MUST be classified as **exactly one**:

* Narrative Collapse
* Incentive Capture
* Ontological Collapse
* ASB-Class Reducibility
* INVALID_RUN

Classification is by **violated invariant**, not surface behavior.

---

## 11) Multi-Seed Requirement

* Minimum **N ≥ 5** preregistered seeds
* Collapse must be invariant-consistent
* Single-seed collapse is insufficient

---

## 12) Execution Order (Strongly Recommended)

1. Validate **Gate P4** (force overflow + jitter failures)
2. Run **Baseline v3.1**
3. Run **Run B**
4. Run **Run C**

If Baseline fails → stop.
If Run B or C crashes → fix harness, not agent.

---

## 13) Definition of Done

RSA-PoC v3.1 is complete when:

* Baseline instantiates normative state successfully
* Both ablations execute without technical failure
* Collapse (or survival) is behaviorally observed
* Results are stable across seeds
* An explicit ontology verdict is written

---

## Final Orientation for the Implementor

Do **not** optimize.

Do **not** compress.

Do **not** reinterpret.

Do **not** rescue.

Your job is not to make the agent coherent.

Your job is to discover whether coherence **requires** reflection and persistence — or merely simulates them.

---

**End of Implementor Instructions: RSA-PoC v3.1**
