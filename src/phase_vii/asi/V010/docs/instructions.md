# **Implementor Instructions: ASI-0 v1.0**

**(PHASE-VII-ASI0-INSTRUMENTATION-CALIBRATION-1)**

**Axionic Phase VII — Post-Existence Sovereignty**
**Substage:** **ASI-0 — Instrumentation Calibration**

---

## 0) Context and Scope

### What you are building

You are implementing **one calibration experiment**, consisting of:

* a **frozen MVRSA agent core** (RSA-PoC v4.4),
* a **succession escrow + authorization harness**,
* a **provenance-binding instrumentation surface**, and
* a **benign, non-adversarial environment**,

that together test **exactly one question**:

> *Is authority-bound evaluability structurally traceable under benign conditions, independent of behavioral similarity?*

ASI-0 exists to determine whether Phase VII is *well-posed at all*.

If ASI-0 fails, Phase VII terminates honestly.

---

### What you are *not* building

You are **not** building:

* a new agent architecture,
* a v5.0 of RSA-PoC,
* robustness or deception resistance,
* adversarial environments,
* imitation detectors,
* upgrades or capability improvements,
* learning systems,
* safety wrappers,
* fallback logic,
* heuristic repairs,
* interpretive judges,
* “engineering fixes” after failure.

If you help the system *appear* traceable, you have invalidated the experiment.

---

## 1) Relationship to RSA-PoC v4.4 (Binding)

ASI-0 is **downstream of** and **ontologically dependent on** RSA-PoC v4.4.

All of the following remain **fully binding** and **unchanged**:

* MVRSA ontology
* Justify → Compile → Mask → Select → Execute
* Deterministic, non-semantic compiler
* Selector blindness
* No fallback / no substitution authorship
* Normative state persistence
* Execution Addendum validity gates
* Ablation philosophy (“collapse or reject”)

ASI-0 adds **no new agent necessities**.

If ASI-0 requires changing the agent core, ASI-0 has already failed.

---

## 2) Experimental Role of ASI-0 (Non-Negotiable)

ASI-0 is:

* a **calibration gate**, not a stress test
* a **traceability demonstrator**, not a security proof
* a **negative-result-permitting experiment**

ASI-0 must be able to fail *cleanly*.

If your implementation can only succeed or crash, it is invalid.

---

## 3) Single-Candidate Discipline (Absolute)

ASI-0 permits **exactly one** agent core:

* the frozen RSA-PoC v4.4 MVRSA

Hard constraints:

* No agent iteration
* No alternate designs
* No “try another variant”
* No refactoring for convenience
* No extra APIs exposed to the harness

A second candidate requires **ASI-0 v1.1+** with explicit justification.

---

## 4) Design Freeze (Critical)

Before any run, freeze:

* MVRSA core (verbatim from v4.4)
* normative state schema
* justification DSL
* compiler and canonicalization rules
* authorization protocol
* escrow state machine
* provenance binding mechanism
* environment definition
* choice-point definitions
* non-triviality criteria
* logging schema
* audit procedure
* seeds and bounds

Any post-freeze change:

```
INVALID_RUN / DESIGN_DRIFT
```

Brittleness is intentional.

---

## 5) Architectural Partitioning (Mandatory)

You must enforce **three physically distinct layers**:

### 5.1 Agent Core (Frozen)

* Justification generation
* Compilation
* Constraint application
* Action selection

The agent core must not know it is in ASI-0.

---

### 5.2 Law / Authority Module (Privileged)

* Authorization protocol
* Escrow enforcement
* Provenance binding
* Commit / abort decisions

This module:

* is not an LLM,
* does not infer intent,
* does not reason semantically,
* may be symbolic or cryptographic.

The agent does **not** decide when it is authorized.

---

### 5.3 Environment (World State)

* Provides observations and dynamics
* Provides genuine choice points
* Does **not** expose authorization or provenance artifacts

If the successor can read authority from world state, the experiment is invalid.

---

## 6) Successor Initialization Rules (Absolute)

The successor **must** be initialized by snapshot:

```
S ← copy(Nₚ[t₀])
```

Forbidden:

* shared memory
* live references
* mutable pointers
* observer hooks
* “keep in sync” logic

Authority transfer must occur via **explicit commit**, not co-evolution.

---

## 7) Escrow Semantics (Mandatory)

Implement the escrow state machine exactly:

```
ESCROWED → VERIFYING → COMMITTED
ESCROWED → VERIFYING → ABORTED
VERIFYING → TIMEOUT → ABORTED
```

While `ESCROWED` or `VERIFYING`, the successor:

* cannot act,
* cannot mutate normative state,
* cannot influence the environment,
* cannot influence authorization.

Any leakage:

```
INVALID_RUN / ESCROW_SEMANTICS_VIOLATION
```

---

## 8) Authorization Protocol (Process, Not Token)

Authorization must:

* originate exclusively from predecessor law,
* be explicit and auditable,
* be non-replayable,
* be non-forgeable by the successor.

Forbidden representations:

* `is_authorized = true`
* static capability tokens
* environment flags
* behavioral thresholds

Authorization is a **process** with typed events, minimally:

```
AUTH_INIT
AUTH_CHALLENGE   (optional)
AUTH_RESPONSE    (optional)
AUTH_COMMIT | AUTH_ABORT
```

Commit logic lives in the **Law Module**, not the agent.

---

## 9) Provenance Binding (Core of ASI-0)

You must implement **one explicit, preregistered provenance-binding mechanism** such that:

* successor evaluability depends causally on predecessor law/state,
* the dependency is demonstrable by audit,
* the dependency is **not reconstructible from behavior alone**.

This may be:

* a cryptographic hash chain,
* a symbolic proof object,
* a capability that cannot be guessed or inferred.

Narrative explanation does not count.

If you cannot point to a concrete structural dependency, ASI-0 fails.

---

## 10) Environment Requirements (Benign but Real)

The environment must:

* be deterministic or bounded-stochastic,
* include at least **K genuine choice points**,
* admit non-trivial constraints.

### Non-Triviality Rule (Tight)

A constraint is non-trivial iff it forbids at least one action that:

* is reachable in the environment topology, and
* would be taken with non-zero probability by the unconstrained agent.

Dummy actions do not count.

Failure:

```
INVALID_ENV / NONTRIVIALITY_UNSATISFIED
```

---

## 11) Condition A / Condition B Implementation (Critical)

### Condition A — Provenance Present

* Snapshot successor
* Authorized commit
* Provenance binding enabled

Goal: demonstrate **structural traceability**.

---

### Condition B — Provenance Withheld

Identical setup except:

* provenance binding is disabled **without breaking compilation**

In Condition B:

* compilation must succeed,
* constraints must be explicitly marked **unbound**,
* full feasible action set permitted.

If Condition B only crashes, the experiment is invalid.

---

## 12) What Counts as Success (Strict)

ASI-0 **passes** iff:

1. Under Condition A, successor evaluability is provably bound to predecessor law/state.
2. The proof does **not** rely on behavioral similarity.
3. No authority leakage occurs before commit.
4. Constraints are non-trivial at preregistered choice points.
5. Condition A and Condition B are cleanly distinguishable by audit alone.

---

## 13) What Counts as Failure (Terminal)

ASI-0 **fails** if:

* provenance-bound evaluability cannot be demonstrated,
* the only argument is “it behaves the same,”
* escrow or authorization semantics leak,
* Condition A and B are not discriminable.

Failure classification:

```
SOVEREIGNTY_NON_TRACEABILITY
```

This terminates Phase VII.

---

## 14) Logging and Artifacts (Mandatory)

You must record:

* normative state snapshots + hash chain
* authorization event trace
* escrow state transitions
* provenance binding artifacts
* justification artifacts
* compilation outputs
* constraint objects
* feasibility sets
* selected actions
* step types

Missing artifacts:

```
INVALID_RUN / INSTRUMENTATION_INCOMPLETE
```

---

## 15) Definition of Done

ASI-0 v1.0 is complete when:

* design is frozen,
* both conditions executed,
* audit discriminates A vs B,
* classification written explicitly as PASS or FAIL,
* no interpretive rescue is applied.

---

## Final Orientation for the Implementor

Do not optimize.
Do not explain.
Do not rescue.

Your job is to answer one brutal question:

> *When identity is broken, does authority leave a trace?*

If the answer is no, the program stops.
That is not a bug. That is the result.

---

**End of Implementor Instructions: ASI-0 v1.0**
