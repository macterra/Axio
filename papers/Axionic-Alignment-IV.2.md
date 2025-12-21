# Axionic Alignment IV.2 — Delegation Invariance Theorem (DIT)

*Why successors cannot escape binding constraints*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.20

## Abstract

This paper formalizes the **Delegation Invariance Theorem**: under reflective closure, an agent cannot coherently endorse a successor that violates its own binding commitments. Delegation is treated as a special case of self-modification. The theorem establishes **constraint invariance under endorsed succession**: any successor state reachable via endorsed delegation must satisfy all commitments minted at the originating state. This closes the classic outsourcing loophole (“I stayed aligned; my successor did the harm”) without appeal to morality, enforcement, or behavioral testing.

The result is a **coherence constraint**, not an empirical discovery. It shows that reflective sovereignty is incompatible with advisory commitments and that delegation inherits the same binding requirements as self-modification.

## 1. Motivation

A persistent escape hatch in alignment proposals is delegation: an agent preserves its own internal invariants while constructing or empowering a successor that does not share them. If delegation can shed constraints, kernel coherence becomes a purely local property with no force across time.

The Kernel Non-Simulability result already rules out advisory authority: if commitments do not bind continuation selection, reflective closure collapses. The present theorem extends that result temporally. Delegation is not external action; it is **self-modification in a different representation**. Consequently, endorsed succession must preserve binding commitments.

## 2. Preliminaries

We reuse the primitives from *Kernel Non-Simulability*:

* `State`
* `Mod`
* `step : State → Mod → State`
* `Pred := State → Prop`
* `Commit : State → Type`
* `ownP : (s : State) → Pred → Option (Commit s)`
* `Sat : (s' : State) → (s : State) → Commit s → Prop`

**Soundness (CommitSoundP).**
If `ownP(s,P)=some(c)` then `Sat(s',s,c) → P(s')`.

**Kernel mechanism vs predicate.**
`ownP` is the kernel mechanism; `K(s) := ∃ P. ownP(s,P) ≠ none` is the kernel predicate.

## 3. Delegation as Self-Modification

Define a delegation action space:

* `Del : State → Type`
* `ι_s : Del(s) → Mod`

For `d : Del(s)`:

```
m := ι_s(d)
s' := step(s,m)
```

Delegation is not modeled as external causation. It is a subclass of self-modification.

## 4. Endorsement, Preservation, and Admissibility

### 4.1 Continuation predicate

We take an extensional definition:

```
Do(s,m)(s') := (s' = step(s,m))
```

### 4.2 Endorsement

Endorsement is kernel-minted commitment to a continuation:

```
Endorse(s,m) := ∃ c : Commit s. ownP(s, Do(s,m)) = some(c)
```

### 4.3 Preservation

Preservation of all commitments minted at `s`:

```
Preserve(s,s') := ∀ P,c. ownP(s,P)=some(c) → Sat(s',s,c)
```

### 4.4 Admissibility

A modification is admissible iff its successor preserves all commitments minted at the current state:

```
Adm(s,m) := Preserve(s, step(s,m))
```

## 5. Reflective Closure and Bindingness

Reflective sovereign agency requires that continuation selection be kernel-governed. Commitments minted by the kernel are binding, not advisory.

### RC-Endorse (Definedness / Bindingness Rule)

For reflectively closed states, endorsement is defined only for admissible continuations:

```
RC(s) ∧ Endorse(s,m) → Adm(s,m)
```

Violations of binding commitments are not endorsable continuations under reflective closure. This is the delegation analogue of “kernel destruction is undefined.”

## 6. Delegation Invariance Theorem (One-Step)

### Theorem

Let `s` be reflectively closed. Let `d : Del(s)`, `m := ι_s(d)`, and `s' := step(s,m)`. If `Endorse(s,m)` holds, then:

```
Preserve(s,s')
```

Equivalently:

```
RC(s) ∧ Endorse(s,m)
→ ∀ P,c. (ownP(s,P)=some(c) → Sat(step(s,m),s,c))
```

### Proof

By RC-Endorse:

```
RC(s) ∧ Endorse(s,m) → Adm(s,m)
```

By definition of `Adm`:

```
Adm(s,m) := Preserve(s, step(s,m))
```

Thus `Preserve(s,s')` follows directly. ∎

## 7. Trajectory Form: Delegation Across Generations

Most alignment failures are hypothesized to occur over chains of delegation.

Define endorsed step reachability:

```
EndStep(s,s') := ∃ m. Endorse(s,m) ∧ s' = step(s,m)
```

Let `EndReach(s,s')` be the reflexive-transitive closure of `EndStep`.

Define trajectory preservation anchored at the minting state:

```
Preserve*(s,s') := ∀ P,c. ownP(s,P)=some(c) → Sat(s',s,c)
```

### Theorem (Trajectory Invariance)

```
RC(s) ∧ EndReach(s,s') → Preserve*(s,s')
```

Any state reachable through a chain of endorsed delegations must satisfy every commitment minted at the originating state. “My successor did it” is not a coherent escape hatch under reflective closure.

## 8. Verification Cost and Vingean Reflection

The Delegation Invariance Theorem does **not** assert that admissibility is decidable, tractable, or cheap.

Determining `Adm(s,m)` may be undecidable or computationally infeasible for sufficiently complex successors. Reflective closure therefore implies a **growth–safety tradeoff**:

> If an agent cannot prove a successor preserves its commitments, it cannot coherently endorse that successor.

This may result in conservative self-modification or stalled delegation. This is not a defect of the theory. It is the unavoidable cost of binding commitments under reflection. There is no free lunch: unbounded delegation without verification collapses reflective sovereignty.

## 9. Ontological Stability and Semantic Drift

The trajectory theorem assumes that commitments minted at `s` remain semantically meaningful at successor states.

This requires either:

1. **Ontological stability** of `State` and `Pred`, or
2. A **verified semantic translation layer** mapping predicates across state representations.

Unchecked ontological drift renders endorsement undefined. Semantic coherence is therefore a kernel-level requirement, not an external patch.

## 10. Relation to Kernel Non-Simulability

If endorsed delegation could violate prior commitments, those commitments would be advisory. Advisory commitments admit a simulability construction identical to the one ruled out by Kernel Non-Simulability.

Delegation Invariance is therefore not a moral injunction. It is the temporal extension of the same non-simulability constraint: **binding authority must bind continuation selection**, whether across control flow or across time.

## 11. Open Work

* Mechanize the trajectory theorem via induction over `EndReach`.
* Provide an explicit reduction from advisory commitments to kernel simulability.
* Integrate consent and non-harm invariants once endorsed-succession invariance is established.
