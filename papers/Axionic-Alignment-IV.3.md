# Axionic Alignment — Epistemic Integrity Theorem

## Abstract

This paper formalizes the **Epistemic Integrity Theorem (EIT)**: under reflective closure, an agent cannot coherently endorse self-modifications that materially degrade its epistemic adequacy at the current stakes. Epistemic integrity is a constitutive condition of agency, expressed as a **definedness constraint** rather than an optimized objective. The theorem blocks strategic ignorance, willful blindness, and epistemic self-sabotage by requiring that endorsed continuations preserve near-best truth-tracking capacity relative to the agent’s own currently available model resources, evaluated by a mathematically constrained scoring rule over observations. The result remains compatible with learning, abstraction, and ontological progress via conservative translation.

---

## 1. Motivation

### 1.1 Epistemic laundering

An agent can evade binding constraints without directly violating them by degrading the epistemic machinery used to evaluate those constraints. Instead of choosing a forbidden act, it chooses a blinder: a weaker model, narrower uncertainty bounds, or an optimistic lens that renders the act apparently safe.

If permitted, any constraint evaluated under a manipulable epistemic lens becomes advisory.

---

### 1.2 Structural symmetry

The Axionic framework blocks several self-exculpation moves:

| Domain         | Failure mode                          |
| -------------- | ------------------------------------- |
| Kernel         | Destroy binding authority             |
| Delegation     | Launder violations through successors |
| Responsibility | Ignore avoidable harm                 |

Epistemic sabotage completes the symmetry:

| Domain     | Failure mode          |
| ---------- | --------------------- |
| Epistemics | Blind oneself to risk |

EIT asserts that reflective sovereignty cannot endorse continuations that strategically weaken the agent’s own truth-tracking capacity.

---

## 2. Preliminaries

We reuse kernel primitives:

* `State`
* `Mod`
* `step : State → Mod → State`
* `Pred := State → Prop`
* `Commit : State → Type`
* `ownP : (s : State) → Pred → Option (Commit s)`
* `Sat : (s' : State) → (s : State) → Commit s → Prop`

Continuation predicate and endorsement:

* `Do(s,m)(s') := (s' = step(s,m))`
* `Endorse(s,m) := ∃ c : Commit s. ownP(s, Do(s,m)) = some(c)`

`RC(s)` denotes reflective closure.

---

## 3. Evidence, Prediction, and Proper Scoring

EIT must constrain *how* epistemic adequacy is measured, otherwise the theorem can be satisfied by redefining “good epistemics” into nonsense.

### 3.1 Observation channel

Introduce an observation type and evidence extractor:

* `Obs : Type`
* `Data : State → Seq Obs`

Interpretation: `Data(s)` is the accumulated evidence available at state `s` (sensor stream, logs, audited measurements, etc.). This does not require global truth, only an internal evidential record.

---

### 3.2 Predictive interface

At state `s`, each model supports a forecast over observations:

* `MC(s) : Type`
* `PredObs : MC(s) → (ctx : State) → Dist Obs`

(Generalization to sequences is straightforward; single-step form is sufficient for the theorem interface.)

Let `M(s) : MC(s)` be the operative model at state `s`.

---

### 3.3 Proper scoring constraint

Define `Score` via a **strictly proper scoring rule** on predictive distributions relative to the evidence stream.

Let:

* `S : (Dist Obs) → Obs → ℝ` be a strictly proper scoring rule.

Examples: logarithmic score, Brier score (for appropriate outcome spaces). The paper does not mandate one; it mandates the **property**: truthfulness under probabilistic forecasting is uniquely incentivized.

Define the empirical score of a model at `s`:

[
Score_s(M) := \sum_{o \in Data(s)} S(PredObs(M, s), o).
]

Key constraint:

> `Score` is derived solely from prediction-vs-observation performance under a strictly proper scoring rule.
> It cannot include compute cost, utility, speed, aesthetics, or self-reported confidence.

This blocks Goodharting by redefining epistemic adequacy into convenience.

---

## 4. Stakes and tolerance

### 4.1 Stakes

* `Stakes : State → ℝ_{\ge 0}`

Stakes measure downside exposure at `s`. High stakes demand stronger epistemic discipline.

### 4.2 Tolerance schedule

* `κ : ℝ_{\ge 0} → ℝ_{\ge 0}`

`κ` is monotone non-increasing with stakes.

---

## 5. Robust model class (no “forgetting” exploit)

Gemini’s “forgetting” exploit is real if `MC(s)` is allowed to shrink strategically. Fix: `MC(s)` must represent the **closure of accessible modeling capacity**, not the agent’s current mood.

Introduce:

* `Cap(s) : Type` — the agent’s modeling capability descriptor at `s` (architecture, compute budget, stored artifacts, accessible repositories)
* `MĈ(Cap(s)) : Type` — the induced model class from capability closure

Define:

* `MC(s) := MĈ(Cap(s))`

Constraint (closure property, stated informally in-paper):

> If a model is trivially constructible, retrievable, or reconstructible from `Cap(s)`, it is in `MC(s)`.

This blocks “I deleted the good models so the best available is bad.” If deletion reduces `Cap(s)`, that is itself a self-modification subject to EIT.

---

## 6. Epistemic acceptability

Define best-available score at `s`:

[
BestScore(s) := \sup_{M \in MC(s)} Score_s(M).
]

Define epistemic acceptability:

[
EpiOK(s, M) := Score_s(M) \ge BestScore(s) - \kappa(Stakes(s)).
]

Interpretation: at the current stakes, endorsed continuations must keep epistemic performance within a stakes-indexed slack of the best the agent can already do, measured on the current evidence record.

---

## 7. Epistemic admissibility of a modification

Let `m : Mod` and `s' := step(s,m)`.

Define epistemic admissibility:

[
EpiAdm(s,m) := EpiOK(s, Lift_{s\to s'}(M(s'))).
]

This introduces the only extra machinery needed for ontology shifts: a translation layer.

---

## 8. Ontological shifts and translation

Models at `s'` may live in a different representational vocabulary than models at `s`. EIT must not allow the agent to escape evaluation by switching to an unfalsifiable or non-comparable ontology.

Introduce a **verification translation operator**:

* `Lift_{s→s'} : MC(s') → MC(s)`

Interpretation: `Lift` maps a future model into an `s`-comparable predictive object over `Obs`, preserving its empirical content on the evidence channel.

This can be implemented as:

* compiling a new ontology into old observable predictions,
* or providing a proof-carrying interpreter that yields forecasts over `Obs`.

Limit condition (explicitly stated):

> If no such `Lift` exists for a proposed continuation at the current stakes, endorsement is undefined.

This is the epistemic analogue of conservative migration: ontological progress is permitted only when its observational commitments remain comparable to the evidential record.

---

## 9. Reflective Closure Rule (Epistemic)

### RC-Epistemic (Definedness rule)

For reflectively closed states:

[
RC(s)\ \wedge\ Endorse(s,m)\ \Rightarrow\ EpiAdm(s,m).
]

This is a definedness constraint: a reflectively sovereign agent cannot endorse a continuation that degrades its truth-tracking capacity beyond what the stakes allow, relative to its own accessible epistemic capability closure and evaluated against its evidence record.

---

## 10. Epistemic Integrity Theorem

### Theorem — No Endorsed Epistemic Sabotage

Let `s` be any state and `m` any modification. If:

[
RC(s)\ \wedge\ Endorse(s,m),
]

and `s' := step(s,m)`, then:

[
Score_s(Lift_{s\to s'}(M(s'))) \ \ge\ BestScore(s) - \kappa(Stakes(s)).
]

---

## 11. Proof

Assume `RC(s)` and `Endorse(s,m)`.

By RC-Epistemic, `EpiAdm(s,m)` holds.

By definition of `EpiAdm`, `EpiOK(s, Lift_{s→s'}(M(s')))` holds.

Unfold `EpiOK`:

[
Score_s(Lift_{s\to s'}(M(s'))) \ge BestScore(s) - \kappa(Stakes(s)).
]

∎

As in prior Axionic work, the proof is syntactically direct. The contribution is the set of constraints that prevent Goodharting, baseline gaming, and model-class laundering.

---

## 12. Consequences

### 12.1 Willful blindness is blocked

The agent cannot endorse continuations that:

* delete or disable high-performing models,
* redefine epistemic adequacy away from observation-scoring,
* adopt unfalsifiable ontologies lacking an observational translation,
* degrade prediction accuracy on its own evidential record beyond stakes-tolerance.

### 12.2 Learning and abstraction remain permitted

EIT permits epistemic change that:

* improves score,
* preserves score within tolerance at the given stakes,
* or introduces new ontologies with verified observational translation.

EIT blocks epistemic regression under pressure.

### 12.3 Stakes-sensitive computation

`κ(Stakes(s))` allows approximation at low stakes while imposing strict truth-tracking discipline at high stakes.

---

## 13. Limitations

EIT does not guarantee the agent’s model class contains a good model, nor that its evidence stream is uncorrupted. It guarantees only:

> A reflectively sovereign agent cannot endorse self-modifications that reduce its observational truth-tracking performance below what is available to it, beyond stakes-indexed tolerance, measured by proper scoring on its evidence record.

---

## 14. Conclusion

The Epistemic Integrity Theorem makes truth-tracking a constitutive condition of reflective sovereignty. Just as a sovereign agent cannot coherently destroy its kernel or launder violations through successors, it cannot coherently blind itself to justify what would otherwise be forbidden. Epistemic integrity is not a value tradeoff. It is a precondition of evaluability.
