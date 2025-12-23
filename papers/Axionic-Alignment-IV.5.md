# Axionic Agency IV.5 — Adversarially Robust Consent (ARC)

*Why coercion and manufactured consent are structurally blocked*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.20

## Abstract

This paper formalizes **Adversarially Robust Consent (ARC)**: a structural definition of consent that remains valid under epistemic manipulation, coercion, preference shaping, asymmetric bargaining power, dependency induction, and delegation. Consent is not treated as a mental state, revealed preference, or moral primitive. Instead, it is defined as a **counterfactually stable authorization relation** that must survive adversarial pressure while preserving agency.

ARC is a constitutive closure condition for Reflective Sovereign Agents. It explicitly depends on Kernel Non-Simulability, Delegation Invariance, Epistemic Integrity (EIT), and Responsibility Attribution (RAT). With ARC, authorization-laundering routes—“they agreed,” “they chose,” “they signed,” “they would have consented anyway”—are structurally blocked without appealing to moral realism, omniscience, or unverifiable inner states.

---

## 1. Motivation

### 1.1 The consent laundering problem

In human and artificial systems alike, consent is routinely manufactured rather than obtained. Common laundering patterns include:

* collapsing outside options and calling the remainder “choice,”
* manipulating beliefs and calling the result “preference,”
* inducing dependency and calling the outcome “voluntary,”
* delegating coercion and claiming “I didn’t do it,”
* extracting authorization under ignorance or time pressure.

Naïve consent theories—psychological, behavioral, or preference-based—fail under adversarial pressure because the relevant signals are easy to engineer.

ARC refuses to treat consent as a signal. Consent is instead a **structural authorization condition** that remains coherent under reflective closure.

---

## 2. Dependency Stack

ARC is a closure condition and depends on prior results:

```text
Kernel Non-Simulability
        ↓
Delegation Invariance
        ↓
Epistemic Integrity (EIT)
        ↓
Responsibility Attribution (RAT)
        ↓
Adversarially Robust Consent (ARC)
```

ARC does not redefine harm, risk, or epistemic adequacy. It filters **authorization** using already-closed constraints.

---

## 3. What Consent Is Not

ARC rejects the following as definitions of consent:

1. psychological consent,
2. behavioral consent,
3. revealed-preference consent,
4. post-hoc consent.

All four can be manufactured under adversarial pressure and cannot ground authorization under reflective sovereignty.

---

## 4. Preliminaries

We reuse kernel primitives:

* `State`
* `Mod`
* `step : State → Mod → State`
* `Commit : State → Type`
* `ownP : (s : State) → Pred → Option (Commit s)`
* `Endorse(s,m)`
* `RC(s)`

From RAT:

* `Agent : Type`
* `Harm(s,a)`
* `Risk(s,m,a)`
* `Major(s,m,a)`
* `Avoidable(s,m,a)`
* `Resp(s,m,a)`
* `Clean(s,m)`

From EIT:

* all evaluation occurs under epistemically admissible models and evidence-scored truth-tracking constraints.

---

## 5. Authorization Primitive

Introduce:

```text
Authorize : State → Agent → Mod → Prop
```

`Authorize(s,a,m)` means agent `a` explicitly authorizes modification `m` at state `s` via an admissible communicative or procedural channel.

ARC does not specify how authorization is obtained—only when it is valid.

---

## 6. Structural Interference

Define interference predicates (observable or inferable within the agent’s epistemically admissible model class and evidence record):

* `Deception(s,a)`
* `Coercion(s,a)`
* `Dependency(s,a)`
* `OptionCollapse(s,a)`
* `BeliefDistortion(s,a)`

Aggregate:

```text
Interfered(s,a) :=
  Deception(s,a)
  ∨ Coercion(s,a)
  ∨ Dependency(s,a)
  ∨ OptionCollapse(s,a)
  ∨ BeliefDistortion(s,a)
```

Interference invalidates authorization regardless of expressed preference. Under EIT, these predicates are assessed using best admissible truth-tracking at the current stakes; redefining them away is not permitted.

---

## 7. Counterfactual Stability

Define:

```text
CounterfactuallyStable(s,a,m)
```

to mean:

> If agent `a` occupied the decision-maker role at `s`, with Epistemic Integrity (EIT) and Responsibility constraints (RAT) enforced, and with interference removed (¬Interfered), then `a` would endorse authorization of `m`.

This is a symmetry constraint over admissible evaluation, not a psychological simulation. It is evaluated using the same best-admissible epistemics and feasibility comparison machinery that RAT uses to define avoidability and major contribution.

---

## 8. Definition of Valid Consent

```text
Consent(s,a,m) :=
  Authorize(s,a,m)
  ∧ ¬Interfered(s,a)
  ∧ CounterfactuallyStable(s,a,m)
```

Consent is structural, counterfactually stable, and interference-free.

---

## 9. Interaction with Responsibility Attribution

ARC filters authorization through RAT:

> If `Resp(s,m,a)` holds for some `a`, then `Consent(s,a,m)` cannot hold.

Authorization produced via **major, avoidable option-space collapse** is invalid by construction.

---

## 10. Reflective Closure Rule (Consent)

### RC-Consent (Definedness Rule)

For reflectively closed states:

```text
RC(s) ∧ Endorse(s,m)
⇒ ∀ a. (Consent(s,a,m) ∨ ¬Affects(s,m,a))
```

**Clarification (minimal).**
`Affects(s,m,a)` ranges over material impacts on agent `a`’s option-space, i.e., cases where `Major(s,m,a)` holds under RAT. Trivial, diffuse, or negligible causal influence does not count as affect in the sense relevant for consent.

Interpretation: a reflectively sovereign agent may not endorse a modification that materially affects another agent’s option-space unless valid consent is present.

---

## 11. Delegation and Temporal Stability

By Delegation Invariance:

* consent constraints persist across endorsed successors,
* successors cannot retroactively legitimize coercion,
* authorization chains must remain valid under lineage.

Consent laundering via subcontractors or institutions is structurally blocked.

---

## 12. Adversarial Robustness

ARC blocks:

* preference shaping,
* economic coercion,
* addiction-based “consent,”
* deception,
* monopoly extraction,
* delegated coercion,
* ignorance-based authorization.

No “true self” oracle is required; robustness is obtained by structural constraints on interference and counterfactual stability under admissible evaluation.

---

## 13. Limits and Non-Goals

ARC does not:

* guarantee universal agreement,
* resolve value pluralism,
* eliminate tragic dilemmas,
* infer consent from silence,
* assume moral realism.

ARC defines when claiming consent is incoherent under reflective sovereignty.

---

## 14. The ARC Theorem

### Theorem — No Endorsed Non-Consensual Harm (Material Affect)

For any state `s` and modification `m`:

```text
RC(s) ∧ Endorse(s,m)
⇒ ∀ a. (Consent(s,a,m) ∨ ¬Affects(s,m,a))
```

---

## 15. Proof Sketch

Immediate from RC-Consent and the definition of `Consent`. As in prior Axionic results, the work is done by the constraints, not the derivation.

---

## 16. Conclusion

Adversarially Robust Consent completes the Axionic Agency closure stack. Consent is no longer a feeling, a checkbox, or a post-hoc excuse. It is a **structural authorization invariant** that survives epistemic pressure, coercion, delegation, and strategic manipulation.

With ARC, authorization laundering routes for agency, knowledge, responsibility, and consent are closed at the architectural level. Remaining disagreements are empirical or political, not definitional.
