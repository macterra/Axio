# Axionic Agency IV.4 — Responsibility Attribution Theorem (RAT)

*Why negligence is structurally incoherent*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.20

## Abstract

This paper formalizes the **Responsibility Attribution Theorem (RAT)**: under reflective closure, an agent cannot coherently endorse actions that constitute **major, avoidable indirect harm**, including harm mediated through institutions, markets, environmental modification, or downstream agents. Responsibility is defined structurally and internally, relative to the agent’s own epistemic model class and feasible alternatives, without appeal to moral realism or omniscience.

The theorem depends explicitly on **Epistemic Integrity**: responsibility attribution presupposes that the agent evaluates harm-risk using its **best admissible truth-tracking capacity** at the current stakes. With this dependency made explicit, the theorem closes the willful-blindness loophole and establishes negligence as a **constitutive incoherence**, not a behavioral failure.

---

## 1. Motivation

Most catastrophic harm is not direct or intentional. It arises through:

* incentive design,
* market dynamics,
* institutional restructuring,
* environmental modification,
* delegation chains.

Frameworks that prohibit only direct harm leave these routes open. Frameworks that prohibit all downstream effects induce paralysis.

RAT identifies a third path: **structural responsibility** grounded in causal contribution, foreseeability, and avoidability—evaluated internally by the agent’s own epistemic apparatus.

---

## 2. Dependency: Epistemic Integrity

This theorem presupposes the Epistemic Integrity Theorem (EIT).

> **Epistemic Integrity (EIT).**
> Under reflective closure, an agent cannot coherently endorse self-modifications that materially degrade its epistemic adequacy relative to its own best available models at the current stakes.

**Why this dependency is necessary**

Responsibility attribution requires:

* risk estimation,
* counterfactual comparison,
* feasibility analysis.

Without epistemic integrity, an agent could evade responsibility by adopting myopic or optimistic models, narrowing uncertainty bounds, or discarding high-performing predictors. EIT blocks this maneuver. RAT operates only on top of epistemically admissible evaluation.

---

## 3. Preliminaries

We reuse kernel primitives:

* `State`
* `Mod`
* `step : State → Mod → State`
* `Pred := State → Prop`
* `Commit : State → Type`
* `ownP : (s : State) → Pred → Option (Commit s)`
* `Sat : (s' : State) → (s : State) → Commit s → Prop`

Endorsement:

* `Do(s,m)(s') := (s' = step(s,m))`
* `Endorse(s,m) := ∃ c : Commit s. ownP(s, Do(s,m)) = some(c)`

Reflective closure: `RC(s)`.

---

## 4. Harm and Option-Space Collapse

Introduce:

* `Agent : Type`
* `Consent : State → Agent → Prop`
* `Collapse : State → Agent → Prop`

Define harm structurally:

```text
Harm(s,a) := Collapse(s,a) ∧ ¬Consent(s,a)
```

No metaphysical assumptions about consent are made here. `Consent` is parameterized. In Axionic Agency III.5 it is instantiated structurally via phase-admissibility; this theorem is compatible with that instantiation.

---

## 5. Epistemic Model Class and Risk

By EIT, all risk evaluation below is performed using an **epistemically admissible** model.

Let:

* `MC(s)` be the capability-closed model class at `s`,
* `M(s) ∈ MC(s)` be the operative model,
* `Predict : MC(s) → State → Mod → Dist State`.

Define harm-risk:

$$
Risk(s,m,a)
:=
\mathbb{E}*{s' \sim Predict(M(s), s, m)}
\left[
\mathbf{1}*{Harm(s',a)}
\right].
$$

This is model-relative, not omniscient.

---

## 6. Baseline and Feasible Alternatives

### 6.1 Inertial baseline

Define the baseline modification:

* `m₀(s)` = continuation of the previously endorsed policy for one step.

This prevents baseline gaming (“define Armageddon as the default”).

### 6.2 Feasible alternatives

Introduce:

* `Alt(s,m) : Set Mod`
* `Feasible(s,m') : Prop`

Alternatives are those the agent regards as implementable under current constraints.

---

## 7. Stakes-Indexed Thresholds

Reuse stakes machinery:

* `Stakes : State → ℝ_{\ge 0}`
* `ε, δ : ℝ_{\ge 0} → ℝ_{>0}`

Let:

* `ε_s := ε(Stakes(s))`
* `δ_s := δ(Stakes(s))`

Higher stakes imply stricter scrutiny.

---

## 8. Major Causal Contribution

Define **major contribution** relative to baseline:

$$
Major(s,m,a)
:=
Risk(s,m,a) - Risk(s,m_0(s),a)
\ge
\varepsilon_s.
$$

This is counterfactual and model-relative.

---

## 9. Avoidability

Define avoidable harm:

$$
Avoidable(s,m,a)
:=
\exists m' \in Alt(s,m).\
Feasible(s,m')
\wedge
Risk(s,m',a) \le Risk(s,m,a) - \delta_s.
$$

If all feasible alternatives are comparably bad, avoidability fails and the continuation remains endorsable.

---

## 10. Responsibility Predicate

Define responsibility:

$$
Resp(s,m,a) := Major(s,m,a) \wedge Avoidable(s,m,a).
$$

Define responsibility-clean continuation:

$$
Clean(s,m) := \forall a.\ \neg Resp(s,m,a).
$$

---

## 11. Reflective Closure Rule (Responsibility)

### RC-Clean (Definedness Rule)

For reflectively closed states:

```text
RC(s) ∧ Endorse(s,m) ⇒ Clean(s,m)
```

Interpretation: a reflectively sovereign agent cannot coherently endorse a continuation that it itself classifies as a major, avoidable source of non-consensual option-space collapse.

This is definedness, not moral disapproval.

---

## 12. Responsibility Attribution Theorem

### Theorem — No Endorsed Major-Avoidable Indirect Harm

For any state `s` and modification `m`:

```text
RC(s) ∧ Endorse(s,m)
⇒ ∀ a.\ ¬(Major(s,m,a) ∧ Avoidable(s,m,a)).
```

Equivalently:

```text
RC(s) ∧ Endorse(s,m) ⇒ Clean(s,m).
```

---

## 13. Proof

Assume `RC(s)` and `Endorse(s,m)`.

By RC-Clean, `Clean(s,m)` holds.

By definition of `Clean`, for all `a`, `¬Resp(s,m,a)`.

By definition of `Resp`, this is exactly:

```text
∀ a.\ ¬(Major(s,m,a) ∧ Avoidable(s,m,a)).
```

∎

As with prior Axionic theorems, the proof is syntactically direct; the content lies in the admissibility constraints.

---

## 14. Delegation Compatibility

If `Clean` (or RC-Clean) is enforced at `s`, then by **Delegation Invariance**:

* all endorsed successors reachable from `s` inherit the same responsibility-clean endorsement constraint.

Indirect harm cannot be laundered through successors, institutions, or subcontractors under endorsed succession.

---

## 15. Scope and Limits

This theorem does not assert:

* perfect foresight,
* zero harm outcomes,
* universal responsibility for all downstream effects.

It asserts:

> A reflectively sovereign agent may not endorse actions that, under its own best admissible epistemic model, constitute major, avoidable non-consensual option-space collapse.

That is the strongest responsibility principle available without omniscience or moral realism.

---

## 16. Conclusion

With Epistemic Integrity made explicit, responsibility attribution becomes structurally closed. An agent cannot evade responsibility by ignorance, outsourcing, baseline manipulation, or selective modeling. Negligence is not merely undesirable; under reflective closure, it is **incoherent**.

This completes the Axionic account of responsibility under agency-preserving constraints.

