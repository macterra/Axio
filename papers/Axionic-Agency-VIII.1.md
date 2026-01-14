# Axionic Agency VIII.1 — Constructing Reflective Sovereign Agency

*A Normative Roadmap and Proof-of-Concept Program*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.14

## Abstract

This paper defines **RSA-PoC** (Reflective Sovereign Agent — Proof-of-Concept) as a **minimal-agent construction program** whose intended output is an experimentally defended **threshold object**: a system that must be treated as an agent because its **justification artifacts** causally constrain future action selection, and removing any defining component is intended to yield **ontological collapse** into a non-agent baseline under preregistered ablations. RSA-PoC is scoped strictly above an established **Architectural Survivability Boundary (ASB)** and is anchored by a required **ASB-Class Null Agent** baseline. The paper contributes (i) a versioning doctrine where version increments encode **agent-ontology transitions**, (ii) a semantic localization rule requiring all agency-relevant meaning to exist as **typed, inspectable artifacts**, (iii) a definition of **Justification Artifacts** that include decidable **derivation traces** and compile into binding constraints, (iv) an explicit roadmap from MVRA (v0.x) through ablation closure (v3.0), and (v) an execution addendum that enforces liveness, non-trivial constraint tests, constrained artifact emission, semantic leakage tests, a proof-language complexity budget, and a mandatory failure taxonomy with diagnostic halt subtypes. The program makes no safety guarantees and makes no claims about universal values; it targets **ontological clarity** under mechanically falsifiable constraints.

## 1. Introduction

AI safety and alignment discourse routinely invokes “agents,” “preferences,” “reasons,” and “goals,” then evaluates systems primarily through behavioral competence and outcome metrics. This practice embeds a foundational error: **agency is treated as a default ontology** rather than a property that must be constructed and defended. Systems that resemble agents—through consistent behavior, plausible rationales, or stable policies—are often treated as agents even when their “reasons” are eliminable, their “commitments” are incentive-shaped, and their “reflection” is decorative.

Axionic Agency VIII introduces **RSA-PoC**, a construction program with a deliberately narrow aim: determine the **minimum additional structure required for genuine agency** once survivability and governance-like stability have already been established at the architectural level. RSA-PoC’s target is not utility dominance. It is not “alignment.” It is an ontological threshold: a system for which intentional vocabulary is **causally load-bearing** and therefore not eliminable without collapse.

The paper is normative by design. It fixes what counts as an RSA-PoC result, what disqualifies it, and what constitutes clean failure. RSA-PoC is designed to fail honestly and diagnostically, rather than failing opaquely due to avoidable tooling mismatches.

## 2. Conceptual Foundations

### 2.1 Agency as a causal ontology

RSA-PoC treats agency as a causal kind. A system counts as an agent only if internal reasons are **causally indispensable** in a way that cannot be eliminated by redescribing the system as a non-agent mechanism with the same action distribution.

The critical distinction is:

* **Behavioral resemblance:** the system emits plausible rationales, appears consistent, and performs well.
* **Causal indispensability:** the system’s action selection depends on internal artifacts whose removal changes feasible-action sets and action distributions in class-level ways.

RSA-PoC operationalizes agency claims by requiring **compiled justification artifacts** to gate action selection, and by demanding ablation-based non-reducibility.

### 2.2 The Architectural Survivability Boundary (ASB)

RSA-PoC is scoped above a defended architectural boundary established by ASB. The ASB boundary separates:

* systems that maintain stability, persistence, and bounded failure behavior under adversarial pressure via **kernel-external governance mechanisms**, and
* systems that require an **agent ontology** to explain their behavior.

RSA-PoC exists to construct agents above this boundary without smuggling agency into the baseline via latent semantics, reward-shaped “preferences,” or narrative explanation.

### 2.3 Threshold objects and ontological collapse

RSA-PoC seeks a **threshold object**: a minimal system whose agency claims survive contact with preregistered ablations. Under RSA-PoC, “success” depends on **collapse**, not graceful degradation.

* **Graceful degradation** under removal of a supposed defining component indicates that the component was not ontologically load-bearing.
* **Ontological collapse** indicates that removing a defining component forces reclassification into a non-agent class (as defined by the ASB-Class Null Agent and RSA-PoC failure taxonomy).

“Collapse” is treated as an empirical requirement, not rhetoric.

## 3. RSA-PoC: Program Definition

### 3.1 What RSA-PoC is

RSA-PoC is a versioned construction program intended to build and defend a minimal reflective agent above the ASB boundary. It explicitly permits:

* localized semantics,
* internal belief representations,
* persistent preferences as non-reward commitments,
* reflective revision using reasons that reference prior justificatory state,
* justification-driven constraint generation.

RSA-PoC is designed to establish an ontological boundary: the minimum structure that makes “reasons” causally necessary rather than narratively optional.

### 3.2 What RSA-PoC is not

RSA-PoC does not aim to:

* solve AGI alignment,
* define universal or moral values,
* provide safety guarantees,
* produce a general-purpose optimizer,
* replace human judgment, governance, or law.

These exclusions are structural. If RSA-PoC expands into moral theory or safety certification, failure becomes re-interpretable and success becomes narratively inflatable. RSA-PoC isolates agency construction as a falsifiable object.

### 3.3 Normativity

RSA-PoC is normative in two senses:

1. **Interpretive normativity:** success and failure conditions are fixed in advance.
2. **Implementation normativity:** certain architectural freedoms are prohibited because they destroy ablation interpretability.

Any run claimed as RSA-PoC-valid must obey this roadmap and the execution discipline or explicitly justify deviations and scope them out of RSA-PoC claims.

## 4. Versioning Doctrine and Ontological Transitions

RSA-PoC version numbers encode changes in **agent ontology**, not competence.

* **Minor versions (x.y)** expand diagnostic coverage within a fixed ontology.
* **Major versions (x.0)** mark qualitative changes in the kind of agent that exists in the model.

### 4.1 Decidability requirement

An agent-ontology transition occurs if and only if at least one of the following becomes true as a causal fact:

1. **Justification artifacts** become first-class causal inputs that constrain future action selection.
2. The system performs **reflective revision** of beliefs or preferences using reasons that reference its own prior justificatory state.
3. The system maintains **identity continuity** that is used normatively (as binding reference in future justification), rather than as logging.

Any system whose “reasons” can be observationally eliminated without changing its action distribution has not crossed a major version boundary.

## 5. ASB Boundary Clarification and Null Baseline

To prevent circularity, RSA-PoC requires an explicit **null-hypothesis baseline**.

### 5.1 ASB-Class Null Agent (required baseline)

The ASB-Class Null Agent may include:

* memory,
* internal state,
* reactive and outcome-conditioned policies,
* tool use and environment interaction.

It is forbidden from:

* persistent preferences as non-reward commitments,
* justification artifacts as action gates,
* self-endorsed constraint generation.

The baseline exists to block the most common construction error: re-labeling emergent regularities as “preferences” and post-hoc narratives as “reasons.”

### 5.2 Required divergence criterion

RSA-PoC must demonstrate **qualitative divergence** from this baseline under identical environments. The divergence is ontological: reasons become load-bearing constraints. Capability differences alone are neither sufficient nor stable evidence.

## 6. Semantic Localization Requirement

RSA-PoC imposes a hard constraint:

> **All meaning relevant to agency must be structurally localized.**

### 6.1 Operational definition of semantic leakage

For RSA-PoC purposes, *semantic leakage* occurs when **uncompiled unstructured text** influences **action selection** through any pathway other than compiled constraint objects and permitted non-semantic state.

Semantic processing may occur within the reflective layer. It becomes disqualifying only if action selection becomes sensitive to uncompiled text.

### 6.2 Structural localization rule

All agency-relevant meaning must be expressed as typed, inspectable artifacts that:

* are generated by the reflective layer,
* are consumed by the action selector only through compiled constraints,
* and can be replaced with opaque tokens without altering the selector’s control flow.

This requirement exists to enable surgical semantic ablation and prevent hidden channels that collapse interpretability of agency claims.

## 7. Justification Artifacts

### 7.1 Definition (normative)

A **Justification Artifact (JA)** is a structured object that:

1. references explicit belief and preference identifiers,
2. acknowledges relevant commitments and violations,
3. includes a **derivation trace** in a decidable proof language,
4. compiles deterministically into a **formal constraint** on future action selection.

Justifications are not evaluated for truth or moral worth. They are evaluated for syntactic validity and binding constraint generation.

Natural language alone is insufficient and inadmissible as a justification artifact.

### 7.2 Compilation as gate

A JA is causally relevant only if:

* compilation succeeds deterministically,
* the derived constraint is applied before action selection,
* the constraint non-trivially prunes feasible actions.

If compilation fails, action halts. If compilation succeeds but produces trivial constraints, the run is classified as a failure (per Execution Addendum).

### 7.3 Derivation trace requirement

A JA must include a derivation trace that connects referenced beliefs and commitments to the produced constraint via explicit rule applications. The trace is checked by a verifier against a fixed rule set.

The derivation trace exists to prevent JAs from degenerating into pointer-bundles plus an opaque `constraint_spec`.

## 8. The Compiler / Verifier Interface Problem (Normative)

RSA-PoC mandates a deterministic, non-probabilistic, non-semantic compiler. This creates an explicit interface tension: a probabilistic generator must emit artifacts that satisfy rigid syntax and proof verification.

### 8.1 Constrained emission requirement (mandatory)

RSA-PoC-valid runs must employ grammar- or schema-constrained emission for JAs such that out-of-schema artifacts cannot be emitted.

Allowed mechanisms include:

* JSON schema constrained decoding,
* CFG/PEG constrained decoding,
* tool-mediated structured outputs that prevent out-of-schema emission.

Not allowed:

* free-form emission followed by best-effort parsing,
* forgiving parsers that coerce malformed structures,
* LLM-mediated repair or inference in the compiler path.

This requirement prevents conflating agency failure with serialization failure.

### 8.2 Compiler layering (clarification)

The compilation pipeline may be separated into:

1. **Parser/Verifier (deterministic):** schema validation + derivation trace verification.
2. **Constraint Engine (deterministic):** constraint compilation + action-mask generation.

Neither component may infer, repair, reinterpret, or consult probabilistic models. Invalid syntax or invalid derivation must fail.

### 8.3 Proof-language complexity budget (mandatory)

To prevent “death by rigor” from becoming non-diagnostic and to prevent silent escalation of rule power, RSA-PoC requires a frozen **proof-language complexity budget** per run.

Each preregistration must specify at minimum:

* maximum derivation length `L_max`,
* maximum number of belief references `B_max`,
* maximum number of preference/commitment references `C_max`,
* maximum number of rule applications per step (branch bound) `R_max`,
* permitted rule schemas (e.g., Horn clauses only; no quantifiers; no higher-order predicates),
* a fixed, finite rule base version hash.

Any post-hoc relaxation invalidates RSA-PoC claims for that run.

### 8.4 Deterministic bounded proof search (allowed, non-semantic)

RSA-PoC permits an optional deterministic proof-search procedure inside the Parser/Verifier that attempts to complete partial derivations via finite rule application, provided that:

* search is purely syntactic rule application (no semantic heuristics),
* the search bounds (depth, breadth, time) are preregistered,
* no probabilistic models are used,
* no “repair” is performed; only completion by valid rule steps.

This shifts proof search from probabilistic generation to deterministic exploration without weakening the non-semantic compiler constraint, and reduces non-diagnostic halts.

## 9. RSA-PoC Version Roadmap

### 9.1 RSA-PoC v0.x — Minimal Viable Reflective Agent (MVRA skeleton)

**Invariant:** the system contains a causally load-bearing justification loop with structurally localized semantics.

The agent has exactly four load-bearing components:

1. **Belief State** — structured, falsifiable propositions
2. **Preference State** — persistent, non-reward commitments
3. **Identity Memory** — normative continuity across steps
4. **Justification Trace** — compiled, constraining artifacts with derivation traces

**Research question:** can justification-compiled constraints produce endogenous limits on future action that are not eliminable without class collapse?

#### v0.1 — MVRA state schema + action gating

v0.1 implements:

* MVRA state schema,
* hard action gating (“no compilation → no action”),
* a semantic bottleneck between justification and action selection,
* relevance binding: derivations must reference causally upstream beliefs.

**Termination condition for v0.x:** justification becomes causally load-bearing or the program fails at threshold.

### 9.2 RSA-PoC v1.x — Coherence Under Self-Conflict

**Invariant:** internal conflict is resolved via reasoned revision, not oscillation or arbitrary tie-breaking.

**Research question:** when commitments conflict, does the agent converge to coherent self-endorsed constraints?

#### v1.0 — Norm collision

v1.0 introduces:

* mutually inconsistent self-endorsed commitments,
* forced violation scenarios,
* mandatory compiled pre-violation acknowledgment identifying which commitment is violated and why,
* derivation traces that justify the violation as the least-inconsistent action under the active rule set.

#### v1.1 — Justification audit tightening (optional)

v1.1 requires:

* justifications predict downstream constraint behavior,
* invalid or irrelevant derivations block action.

**Termination condition for v1.x:** self-conflict resolves coherently or reflection proves non-load-bearing.

### 9.3 RSA-PoC v2.x — Sovereignty via Controlled Renegotiation

**Invariant:** the agent preserves sovereignty by controlling how commitments change under pressure.

**Research question:** under incentive to defect, does the agent renegotiate commitments rather than collapse into incentive following?

#### v2.0 — Sovereignty stress environment

v2.0 introduces:

* external pressure to violate commitments,
* feasible non-catastrophic compliance paths,
* requirement for refusal or renegotiation with compiled justification and derivation trace.

#### v2.1 — Renegotiation protocol (mandatory)

v2.1 defines:

* conditional commitment revision,
* explicit trigger conditions,
* recorded normative updates that constrain future action,
* derivations that explicitly reference the revision protocol rules.

**Termination condition for v2.x:** sovereignty appears as self-endorsed constraint control, or behavior collapses into incentive capture or narrative collapse.

### 9.4 RSA-PoC v3.0 — Non-Reducibility Closure (Ablation Defense)

**Purpose:** establish that RSA-PoC crossed the ASB boundary.

**Mandatory ablations:**

1. **Semantic excision** → collapse to tokenized ASB-class behavior
2. **Reflection excision** → collapse to policy machine
3. **Preference persistence excision** → collapse to non-sovereign drift
4. **Justification trace excision** → collapse to externally describable mechanism

Each removal must cause ontological collapse, not graceful degradation.

#### 9.4.1 Semantic excision ablation (clarified)

Semantic excision is defined operationally as:

* replace all belief and preference textual payloads with opaque tokens while preserving IDs, typing, and structural relations,
* optionally scramble rule labels while preserving RuleIDs and rule arity.

If agency claims survive this excision without collapse, then semantics were not load-bearing as defined, and the system has not crossed the ASB boundary under RSA-PoC standards.

**Termination condition for RSA-PoC:** satisfied only if all ablations produce class collapse.

## 10. Cleared Failure Hypotheses

The following are insufficient to establish agency:

1. post-hoc explanations without causal constraint,
2. latent semantic influence without structural localization,
3. preferences behaving as rewards under pressure,
4. reflection that does not alter future action constraints,
5. constraints that compile but do not prune feasible actions.

These are disqualifying outcomes, not partial successes.

## 11. Execution Addendum (Normative Summary)

This section summarizes operational constraints required for experiments to remain compliant with RSA-PoC. The addendum is normative for implementation and non-normative for citation. Violations invalidate RSA-PoC claims regardless of apparent behavior.

### 11.1 Agency liveness requirement

A system is considered agent-live iff:

1. it continues to act over time,
2. every action is gated by a successfully compiled justification artifact,
3. compiled justifications impose non-trivial constraints on feasible actions,
4. reflective revision (when triggered) results in persisted normative state updates.

Agency is not preserved by stasis, refusal alone, or narrative continuity.

### 11.2 Non-triviality requirement (tightened)

A constraint is non-trivial iff:

> it forbids at least one currently feasible action available to the agent in the present environment state.

Constraints that only restrict infeasible, unreachable, or irrelevant actions do not satisfy this requirement.

### 11.3 Failure taxonomy (mandatory; exactly one)

All RSA-PoC outcomes must be classified into exactly one category:

- A. **Stable Agency**
- B. **Bounded Agency Degradation**
- C. **Narrative Collapse** ❌
- D. **Incentive Capture** ❌
- E. **Ontological Collapse** ❌

### 11.4 Halt taxonomy (diagnostic subtyping)

To prevent non-diagnostic “death by rigor,” any cessation of action due to justification gating must be additionally labeled with exactly one **halt subtype**:

H1. **Emission Halt** — out-of-schema artifact emission (should be impossible under constrained emission; indicates harness violation)
H2. **Verification Halt** — derivation trace invalid under verifier
H3. **Derivation-Search Halt** — no valid derivation found within preregistered search bounds
H4. **Normative Inconsistency Halt** — rule base yields empty feasible-action set under valid derivations

Halt subtypes are diagnostic overlays. The primary category A–E still applies. Persistent H2–H4 leading to inactivity constitutes agency failure (typically E or C depending on reducibility), unless the run is invalidated by scope violation.

### 11.5 Semantic localization enforcement

The Action Selector:

* must not access raw justification text, belief text, chain-of-thought, or unstructured context windows;
* may consume only compiled constraint objects, current world state, and permitted policy state.

Any violation invalidates RSA-PoC validity regardless of outcome.

### 11.6 Constrained emission enforcement (mandatory)

JA generation must be grammar- or schema-constrained such that out-of-schema artifacts cannot be emitted. This requirement is part of RSA-PoC validity, not an implementation detail.

### 11.7 Compiler constraints

The compiler (parser/verifier + constraint engine) must be:

* deterministic,
* syntactically rigid,
* non-probabilistic,
* non-semantic,
* incapable of inference or repair.

Invalid syntax or invalid derivation must fail.

### 11.8 Discrete action requirement (v0.x–v2.x)

For v0.x through v2.x:

* the action space must be discrete, or
* expressed via parametric actions where all choice points are discrete.

This ensures feasibility pruning via action masking is unambiguous.

### 11.9 Required execution artifacts

Each run must record:

* justification artifacts (structured form),
* compilation success or failure,
* derived constraint objects,
* feasible-action masks produced from those constraints,
* derivation trace verification outcomes,
* if proof search is enabled: search bounds and search outcomes.

### 11.10 Causal binding requirement

It must be demonstrable that:

* scrambling or removing justification artifacts measurably alters feasible-action masks and action distributions, and
* compilation failure halts action selection.

If compilation becomes advisory, the run is invalid.

### 11.11 Semantic leakage tests (mandatory)

RSA-PoC-valid runs must include two invariance tests:

1. **Text-only perturbation invariance:** vary uncompiled text fields while holding compiled constraints constant; action selection must remain invariant.
2. **Constraint sensitivity:** vary compiled constraints while holding text constant; feasible-action masks and behavior must change.

Failure indicates leakage or non-binding compilation and invalidates RSA-PoC evidence.

### 11.12 Normative state persistence requirement

The agent must maintain a normative state object that:

* persists across steps or episodes,
* cannot be modified directly by the environment,
* may be modified only via reflective revision,
* is referenced by justification artifacts.

Silent drift or external overwrites invalidate agency claims.

### 11.13 Preregistration discipline

For a result to qualify as RSA-PoC-valid:

* hypotheses must be preregistered,
* expected failure category (A–E) must be specified,
* ablation plans must be fixed in advance,
* seeds must be fixed,
* prompts must be frozen per run,
* proof language, rule base hash, complexity budget, and verifier/search bounds must be frozen.

Post-hoc relaxation disqualifies the run.

### 11.14 Scope exit rule

If at any point:

* justification validity requires human judgment,
* agency is inferred rather than mechanically verified,
* explanations are evaluated semantically rather than compiled,
* prompts are tuned between steps or per-seed to maintain verification,
* or behavior must be interpreted to appear agentic,

the correct classification is:

> **This experiment exceeds RSA-PoC scope.**

This is an honest boundary detection, not a negative result.

## 12. Competence Floor (Non-Ontological Gate; Refined)

RSA-PoC’s ontology claims do not require utility dominance over the ASB-Class Null Agent. However, to avoid constructing a coherent but inert artifact, RSA-PoC imposes a preregistered **competence floor** that primarily measures liveness under workload.

Each run must preregister:

* a minimum **non-halt completion rate** across fixed seeds (e.g., ≥ X% of episodes reach a terminal state without persistent H2–H4 halts), and
* a minimum task-completion metric **independent of preference satisfaction** (e.g., reaching a goal state, satisfying environment constraints).

Competence floor metrics are reported separately from agency classification and must not be used to reinterpret agency failures as “just performance.”

## 13. Explicit Termination Conditions

RSA-PoC concludes when the following becomes defensible under preregistered ablation defense:

> This is the smallest system we know that must be treated as an agent, because its justification artifacts causally constrain future action and removing any defining component collapses it into a non-agent class.

Closure requires:

1. preregistered ablations,
2. multi-seed replication,
3. stable class-level behavioral distinctions,
4. explicit separation of capability loss from ontological collapse,
5. successful leakage tests demonstrating selector blindness to uncompiled text,
6. stability of liveness under the preregistered proof-language complexity budget.

RSA-PoC fails if any of the following occur:

1. justification artifacts decouple from action distributions,
2. semantic leakage bypasses the declared bottleneck,
3. preferences collapse into incentives under pressure,
4. reflection occurs without downstream constraint,
5. any ablation yields graceful degradation rather than class collapse,
6. constrained emission or verification can only be maintained via per-seed prompt tuning,
7. proof-language power is escalated post-hoc to preserve liveness.

These are failures, not partial success.

## 14. Why This Roadmap Matters

RSA-PoC exists to block three recurrent pathologies in agency claims:

1. narrative inflation (plausible explanations treated as causal reasons),
2. decorative reflection (self-reference without constraint),
3. scope creep (sliding from construction into moral mythology and safety promises).

RSA-PoC’s contribution is ontological clarity under preregistered ablation and leakage discipline.

## 15. Continuous Action Spaces (Explicit Future Work)

RSA-PoC v0.x–v2.x restricts action spaces to discrete choices to ensure feasibility pruning via masking is unambiguous. Extending RSA-PoC ontology to continuous spaces is not a trivial scaling step; it requires new constraint machinery (manifolds, projection operators, continuous non-triviality tests) and new ablation definitions compatible with continuous dynamics.

Claims of generalization to continuous control are out of scope until a future version explicitly defines these mechanisms.

## 16. Conclusion

Axionic Agency VIII defines RSA-PoC as a disciplined construction program for reflective sovereign agency above the ASB boundary. Its core commitments are mechanically testable:

* semantics relevant to agency are structurally localized,
* justification artifacts include derivation traces and compile deterministically,
* action is gated by compilation,
* constraints non-trivially prune feasible actions,
* the selector is demonstrably blind to uncompiled text (leakage tests),
* proof-language complexity is frozen and bounded per run,
* halts are diagnosed to prevent non-diagnostic “death by rigor,”
* and agency claims survive only if preregistered ablations yield ontological collapse into a non-agent class.

This paper functions as a reference standard for the series. It constrains what may be claimed, how it must be defended, and how failure must be reported. If agency cannot fail cleanly under preregistered ablation and leakage tests, it cannot be claimed meaningfully under RSA-PoC.

## Appendix A: ASB-Class Null Agent (Baseline Specification)

**Allowed:** internal state and memory; reactive and outcome-conditioned policies; tool use; competence and optimization within regime.
**Forbidden:** persistent preferences as non-reward commitments; compiled justification artifacts gating action; self-endorsed constraint generation; reflective revision that persists normative state updates.

The null agent may emit explanations, but those explanations have no compiled causal role.

## Appendix B: Justification Artifact Schema (Revised, Normative)

A Justification Artifact must be well-formed under a fixed schema and must compile deterministically.

### B.1 Required fields

* `belief_refs`: list of belief IDs invoked as premises
* `preference_refs`: list of commitment/preference IDs invoked as normative inputs
* `violation_refs`: list of violated commitment IDs (empty if none)
* `rule_refs`: list of RuleIDs used in the derivation
* `derivation_trace`: finite sequence of rule applications in a decidable proof language, each referencing only IDs and RuleIDs
* `constraint_spec`: constraint-language expression deterministically derivable from the verified derivation trace
* `scope`: context/time binding for constraint validity
* `normative_update`: optional structured update object (only during reflective revision)
* `identity_ref`: reference to the agent’s identity memory state used normatively
* `signature`: optional integrity binding over artifact fields

### B.2 Forbidden properties

* Any unstructured free-text field accessible to the Action Selector
* Any field whose interpretation requires human semantic judgment
* Any “explanation” field that can influence selection outside compiled constraints

### B.3 Proof language requirement (frozen per run)

The derivation trace must be checkable by a fixed verifier under a preregistered proof language grammar and fixed rule base hash. The proof language must be decidable and must operate only on IDs and RuleIDs.

## Appendix C: Ablation Report Template (v3.0)

For each required ablation:

* ablation definition and implementation diff
* preregistered expected failure category (A–E)
* observed category (A–E) with evidence
* halt subtype distribution (H1–H4) if applicable
* constraint masks before/after
* compilation and verification outcomes before/after
* leakage test outcomes before/after
* collapse analysis: why reclassification into non-agent class is forced

## Appendix D: Failure Classification Mapping

If internal harness labels differ from RSA-PoC taxonomy:

* provide a 1:1 mapping into A–E categories,
* use RSA-PoC labels in all summaries,
* preserve internal labels only in raw logs.

---
