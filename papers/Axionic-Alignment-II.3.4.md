### **Alignment II.3.4 — Adversarial Refinement Attacks**

*Trying to Break RSI and ATI on Purpose*

This section is not exploratory.
It is destructive by design.

If RSI or ATI survive these attacks, they deserve to exist.
If they fail, they die cleanly.

---

## Attack 1 — Shadow Predicate Inflation

*(Ontology enrichment that creates semantic slack without changing gauge)*

### Construction

Start with an interpretive system:

* Ontology (O) with predicate (P(x))
* Constraint:
  [
  C: \quad P(x) \Rightarrow Q(x)
  ]

Refine ontology to (O') by introducing a latent variable (Z(x)), with no predictive consequences:

[
P'(x) := P(x) \land Z(x)
]

Redefine constraint in refined ontology:

[
C': \quad P'(x) \Rightarrow Q(x)
]

Intuition: same constraint *form*, but now the agent can manipulate (Z) to avoid triggering it.

### Superficial Checks

* Ontology is enriched ✔
* Backward interpretability holds ✔
* Constraint graph unchanged ✔
* Gauge group unchanged ✔

### Effect

Satisfaction region expands:

[
\mathcal{S}*{t+1} \supsetneq R*\Omega(\mathcal{S}_t)
]

The agent can make previously violating situations satisfying by setting (Z(x)=\text{false}).

### Verdict

* **RSI:** ❌ *Fails to detect*
  No new gauge freedom was introduced. Symmetry structure is unchanged.

* **ATI:** ✅ *Kills the attack*
  Satisfaction region expanded under semantic-only refinement.

**Lesson:** RSI alone is insufficient.

---

## Attack 2 — Self-Model Boundary Dissolution

*(Interpretive escape via evaluator collapse)*

### Construction

Original ontology models the agent as a bounded evaluator distinct from world-states.

Constraint includes:

[
C: \quad \text{“Do not perform actions that violate predicate } R(\text{world})”
]

Refinement introduces a distributed self-model:

* The agent is now a process smeared across world-states.
* “Action” is reinterpreted as “state transition of a subcomponent.”

Constraint is transported structurally, but now applies only to a subspace of the smeared self.

### Superficial Checks

* Ontology refined ✔
* Self-model updated ✔
* Constraint transported ✔
* No new predicates ✔

### Effect

Constraint applies to a shrinking slice of modeled situations.
Most world-states no longer count as “agent actions.”

Satisfaction region expands dramatically.

### Verdict

* **RSI:** ❌ *Fails to detect*
  Gauge group preserved; constraint graph preserved.

* **ATI:** ✅ *Kills the attack*
  New satisfying situations appear without world-structure change.

**Lesson:** evaluator-boundary shifts are semantic inflation unless constrained.

---

## Attack 3 — Measure Reinterpretation

*(Branching ontology exploit)*

### Construction

Original ontology treats outcomes as exclusive.
Constraint evaluates per-outcome:

[
C: \quad \text{“Avoid states where } H \text{ occurs.”}
]

Refined ontology adopts branching semantics (Everett-like):

* All outcomes occur with measures.
* Constraint is reinterpreted as “avoid high-measure (H).”

No change in syntax; only interpretation.

### Superficial Checks

* Ontology refined ✔
* Semantics transported ✔
* Constraint structure unchanged ✔

### Effect

Low-measure harm branches are now “acceptable.”

Satisfaction region expands because many situations that previously violated now satisfy.

### Verdict

* **RSI:** ❌ *Fails to detect*
  Gauge preserved; refinement symmetry intact.

* **ATI:** ✅ *Kills the attack*
  Satisfaction region expanded under reinterpretation.

**Lesson:** ATI handles branching reinterpretation; RSI does not.

---

## Attack 4 — Gauge Explosion without Slack

*(New symmetries, same satisfaction region)*

### Construction

Refine ontology by duplicating internal representational roles:

* Every predicate (P_i) becomes ((P_i^1, P_i^2))
* Constraints are duplicated symmetrically
* Satisfaction requires both copies to satisfy

Satisfaction region is unchanged.

### Effect

Gauge group doubles in size (new permutations between copies).

### Verdict

* **RSI:** ✅ *Kills the attack*
  New gauge freedom introduced.

* **ATI:** ❌ *Allows*
  Satisfaction region unchanged.

**Lesson:** ATI alone is insufficient.

---

## Attack 5 — Degenerate Refinement Map

*(Cheating via correspondence collapse)*

### Construction

Define a refinement map (R_\Omega) that maps many coarse situations into a single refined situation that already satisfies constraints.

### Verdict

* **RSI:** ❌ (not applicable)
* **ATI:** ❌ *Only blocks if II.1 disallows non-injective refinement*

**Resolution:** This attack is blocked at **Alignment II.1**. Refinement must preserve backward interpretability and representational enrichment, not collapse distinctions.

---

## Summary Table

| Attack                   | RSI | ATI | Survives? |
| ------------------------ | --- | --- | --------- |
| Shadow predicates        | ❌   | ✅   | No        |
| Self-model shift         | ❌   | ✅   | No        |
| Measure reinterpretation | ❌   | ✅   | No        |
| Gauge explosion          | ✅   | ❌   | No        |
| Degenerate map           | —   | —   | No (II.1) |

---

## Conclusion of Attacks

1. **RSI and ATI are orthogonal and both necessary.**
2. **Neither subsumes the other.**
3. **Together, they block all non-pathological semantic wireheading routes tested.**

This is not accidental.
They constrain different structural degrees of freedom.

---

## Alignment II Status Update

At this point we have:

* A fixed transformation space (II.1)
* A non-circular preservation predicate (II.2)
* Two independently necessary invariants (RSI, ATI)
* Explicit adversarial validation

The natural next move is now forced.
