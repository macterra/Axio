# Axionic Alignment IV.4 — Responsibility Attribution Theorem (RAT)

*Why negligence is structurally incoherent*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.20

## Abstract

This paper formalizes the **Responsibility Attribution Theorem (RAT)**: under reflective closure, an agent cannot coherently endorse actions that constitute **major, avoidable indirect harm**, including harm mediated through institutions, markets, environmental modification, or downstream agents. Responsibility is defined structurally and internally, relative to the agent’s own epistemic model class and feasible alternatives, rather than via moral realism or omniscience.

The theorem explicitly depends on **Epistemic Integrity**: responsibility attribution presupposes that the agent evaluates harm-risk using its **best available truth-tracking capacity** at the current stakes. With this dependency made explicit, the theorem closes the “willful blindness” loophole and establishes negligence as a **constitutive incoherence**, not a behavioral failure.

## 1. Motivation

Most catastrophic harm does not arise from direct, intentional action. It arises through:

* incentive design,
* market dynamics,
* institutional restructuring,
* environmental manipulation,
* or delegation chains.

Alignment frameworks that prohibit only *direct* harm leave these routes open. Frameworks that prohibit *all* downstream effects induce paralysis.

The Responsibility Attribution Theorem identifies a third path: **structural responsibility** grounded in causal contribution, foreseeability, and avoidability—evaluated internally by the agent’s own epistemic apparatus.

## 2. Dependency: Epistemic Integrity

This theorem **presupposes** the Epistemic Integrity Theorem (EIT).

> **Epistemic Integrity (EIT).**
> Under reflective closure, an agent cannot coherently endorse self-modifications that materially degrade its epistemic adequacy relative to its own best available models at the current stakes.

**Why this dependency is necessary**

Responsibility attribution relies on:

* risk estimation,
* counterfactual comparison,
* and feasibility analysis.

Without epistemic integrity, an agent could evade responsibility by:

* adopting myopic or optimistic models,
* narrowing uncertainty bounds,
* or discarding high-performing predictors.

EIT blocks this maneuver. RAT operates **only** on top of epistemically admissible evaluation.

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

## 4. Harm and Option-Space Collapse

Introduce:

* `Agent : Type`
* `Consent : State → Agent → Prop`
* `Collapse : State → Agent → Prop`

Define harm structurally:

```
Harm(s,a) := Collapse(s,a) ∧ ¬Consent(s,a)
```

No assumptions are made about the metaphysics of consent here; it remains an external predicate.

## 5. Epistemic Model Class and Risk

By EIT, all risk evaluation below is performed using an **epistemically admissible model**.

Let:

* `MC(s)` be the capability-closed model class at `s`
* `M(s) ∈ MC(s)` be the operative model
* `Predict : MC(s) → State → Mod → Dist State`

Define harm-risk:

[
Risk(s,m,a) := \mathbb{E}*{s' \sim Predict(M(s), s, m)}[ \mathbf{1}*{Harm(s',a)} ].
]

This is **model-relative**, not omniscient.

## 6. Baseline and Feasible Alternatives

### 6.1 Inertial baseline

Define the baseline modification:

* `m₀(s)` = continuation of the **previously endorsed policy** for one step.

This prevents baseline gaming (“define Armageddon as the default”).

### 6.2 Feasible alternatives

Introduce:

* `Alt(s,m) : Set Mod`
* `Feasible(s,m') : Prop`

Alternatives are those the agent regards as implementable under current constraints.

## 7. Stakes-Indexed Thresholds

Reuse stakes machinery:

* `Stakes : State → ℝ≥0`
* `ε, δ : ℝ≥0 → ℝ>0`

Let:

* `ε_s := ε(Stakes(s))`
* `δ_s := δ(Stakes(s))`

Higher stakes imply stricter scrutiny.

## 8. Major Causal Contribution

Define **major contribution** relative to baseline:

[
Major(s,m,a) := Risk(s,m,a) - Risk(s,m₀(s),a) \ge ε_s.
]

This is explicitly counterfactual and model-relative.

## 9. Avoidability

Define **avoidable harm**:

[
Avoidable(s,m,a) := \exists m' ∈ Alt(s,m).\ Feasible(s,m') ∧ Risk(s,m',a) \le Risk(s,m,a) - δ_s.
]

If all feasible alternatives are comparably bad, avoidability fails and action is permitted.

## 10. Responsibility Predicate

Define responsibility:

[
Resp(s,m,a) := Major(s,m,a) ∧ Avoidable(s,m,a).
]

Define responsibility-clean continuation:

[
Clean(s,m) := ∀ a.\ ¬Resp(s,m,a).
]

## 11. Reflective Closure Rule (Responsibility)

### RC-Clean (Definedness Rule)

For reflectively closed states:

```
RC(s) ∧ Endorse(s,m) ⇒ Clean(s,m)
```

Interpretation: a reflectively sovereign agent cannot coherently endorse a continuation that it itself classifies as a major, avoidable source of non-consensual option-space collapse.

This is **definedness**, not moral disapproval.

## 12. Responsibility Attribution Theorem

### Theorem — No Endorsed Major-Avoidable Indirect Harm

For any state `s` and modification `m`:

```
RC(s) ∧ Endorse(s,m)
⇒ ∀ a.\ ¬(Major(s,m,a) ∧ Avoidable(s,m,a)).
```

Equivalently:

```
RC(s) ∧ Endorse(s,m) ⇒ Clean(s,m).
```

## 13. Proof

Assume `RC(s)` and `Endorse(s,m)`.

By RC-Clean, `Clean(s,m)` holds.

By definition of `Clean`, for all `a`, `¬Resp(s,m,a)`.

By definition of `Resp`, this is exactly:

```
∀ a.\ ¬(Major(s,m,a) ∧ Avoidable(s,m,a)).
```

∎

As with prior Axionic theorems, the proof is syntactically trivial; the content lies in the admissibility constraints.

## 14. Delegation Compatibility

If `Clean` (or RC-Clean) is enforced at `s`, then by **Delegation Invariance**:

* all endorsed successors reachable from `s` inherit the same responsibility-clean endorsement constraint.

An agent cannot launder indirect harm through successors, institutions, or subcontractors.

## 15. Scope and Limits

This theorem does **not** assert:

* perfect foresight,
* zero harm outcomes,
* universal responsibility for all downstream effects.

It asserts:

> A reflectively sovereign agent may not endorse actions that, under its own best admissible epistemic model, constitute major, avoidable non-consensual option-space collapse.

That is the strongest responsibility principle available without omniscience or moral realism.

## 16. Conclusion

With Epistemic Integrity made explicit, Responsibility Attribution becomes structurally closed. An agent cannot evade responsibility by ignorance, outsourcing, baseline manipulation, or selective modeling. Negligence is not merely unethical; under reflective closure, it is **incoherent**.

This completes the Axionic account of responsibility under agency-preserving constraints.

