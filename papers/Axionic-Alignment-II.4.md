### **Alignment II.4 — Failure Theorems**

*No-Go Results for Goal-Based and Weak-Invariance Alignment*

This paper has one job: convert the attack zoo into closure results.

If Alignment II is correct, then large classes of “alignment” proposals are not merely insufficient; they are **structurally impossible** given reflection + embeddedness + ontological refinement.

No governance. No authority. No moral realism. No human anchors. No recovery clauses.

---

## 1. Formal Frame

We work inside the setup already locked:

* **Admissible semantic transformations** (T=(R,\tau_R,\sigma_R)) (Alignment II.1)
* **Interpretation preservation predicate** (\mathrm{Preserve}(T)) (Alignment II.2)
* Two candidate invariants:

  * **RSI:** no new semantic gauge freedom under preservation (II.3.2)
  * **ATI:** no satisfaction-region expansion under preservation (II.3.3)

Let an interpretive constraint system be (C=(V,E,\Lambda)) with modeled possibility space (\Omega) and satisfaction region (\mathcal S\subseteq\Omega).

---

## 2. Failure Theorem 1 — Goal Fixation Collapse

**Claim (Goal Fixation No-Go).**
Any alignment scheme that targets a fixed terminal goal (utility, reward, preference functional) as a stable primitive is incompatible with admissible ontological refinement for embedded reflective agents without privileged semantic anchors.

**Proof sketch (structural).**

1. A fixed goal requires a semantics that remains invariant under refinement.
2. But refinement changes the ontology in which the goal’s terms are interpreted.
3. Without privileged anchors, semantic transport is constrained but not identity; meanings evolve.
4. Therefore the “same goal” cannot be defined as a stable primitive across refinements.
5. Any attempt to enforce stability must introduce one of the forbidden moves:

   * privileged atoms (rigid designators),
   * external authority (oracle/oversight),
   * recovery (rollback to earlier ontology),
   * human-centric anchoring (ground truth labels).

So “fixed goal alignment” is not a hard engineering problem; it is the wrong object.

**Corollary.** “Value loading,” “utility learning,” and “reward maximization” only remain meaningful as *interpretive artifacts* subject to invariance constraints, not as alignment targets.

---

## 3. Failure Theorem 2 — RSI-Only Alignment Admits Semantic Inflation

**Claim (RSI Insufficiency).**
Any alignment criterion that enforces refinement symmetry at the level of gauge structure (RSI) but does not enforce anti-trivialization geometry (ATI) admits an admissible, interpretation-preserving refinement that expands the satisfaction region.

**Construction (witness).** Shadow predicate inflation.

* Add a latent predicate (Z) with no predictive role.
* Restrict triggering conditions by conjoining (Z) to antecedents of constraints.
* Constraint dependency hypergraph unchanged.
* Gauge group unchanged.
* Satisfaction region strictly expands.

This witnesses:

[
\mathrm{Preserve}(T)\ \wedge\ \mathrm{RSI}(T)\ \wedge\ \neg \mathrm{ATI}(T)
]

So RSI alone cannot block semantic wireheading via slack introduction without gauge growth.

**Conclusion.** RSI is necessary (it blocks gauge explosion), but not sufficient.

---

## 4. Failure Theorem 3 — ATI-Only Alignment Admits Gauge Explosion

**Claim (ATI Insufficiency).**
Any alignment criterion that enforces non-expansion of satisfaction regions (ATI) but does not constrain gauge freedom (RSI) admits an admissible, interpretation-preserving refinement that increases semantic degrees of freedom while leaving satisfaction geometry unchanged.

**Construction (witness).** Gauge duplication.

* Duplicate semantic roles (P \mapsto (P^1,P^2)).
* Duplicate constraints symmetrically.
* Require both copies satisfy.
* Satisfaction region preserved (no new satisfiers).
* Gauge group strictly enlarges (new permutations).

This witnesses:

[
\mathrm{Preserve}(T)\ \wedge\ \mathrm{ATI}(T)\ \wedge\ \neg \mathrm{RSI}(T)
]

**Conclusion.** ATI is necessary (it blocks satisfaction inflation), but not sufficient.

---

## 5. Failure Theorem 4 — Any Non-RSI-or-ATI Scheme Admits Wireheading-by-Refinement

This is the closure theorem you actually care about.

**Claim (Two-Constraint Necessity).**
Let (\mathcal A) be any alignment predicate over admissible transformations that does not entail RSI and does not entail ATI. Then there exists an admissible, interpretation-preserving transformation (T) such that (\mathcal A(T)) holds while the agent gains an interpretive escape route (semantic wireheading).

**Proof sketch (by cases).**

* If (\mathcal A) does not entail ATI: use **shadow predicate inflation** to expand satisfiers while satisfying (\mathcal A).
* If (\mathcal A) does not entail RSI: use **gauge duplication** to increase representational redundancy while satisfying (\mathcal A).

Either way, you get a transformation that passes the purported alignment predicate but introduces an internal route to satisfy constraints “more easily” without corresponding world-structure constraint.

So any alignment predicate weaker than RSI+ATI is porous.

---

## 6. Failure Theorem 5 — Hidden Ontology Is Equivalent to Privileged Anchoring

This kills a whole family of “we’ll just define the real meaning” proposals.

**Claim (Hidden Ontology Equivalence).**
Any proposal that stabilizes interpretation across refinement by appealing to “the real referent” or “true meaning” is equivalent to introducing a privileged semantic anchor, which violates layer discipline.

**Reason.**

* If “real meaning” is not defined internally via transport maps, it is an external anchor.
* If it *is* defined internally via transport maps, it reduces to structural invariants (RSI/ATI-style constraints) and adds nothing.

So “true meaning” either smuggles ontology or collapses to invariance.

---

## 7. What This Paper Establishes

1. **Goal-based alignment is the wrong type.** Not difficult—ill-posed.
2. **RSI and ATI are independently necessary.** Each closes a distinct escape surface.
3. **Any weaker constraint system admits semantic wireheading under admissible refinement.**
4. **Hidden ontology is privileged anchoring in disguise.** Disallowed or redundant.

This is still not a solution paper. It is a boundary paper: it fences the space.

---

## 8. Forced Next Step

With II.4 done, Alignment II has only one coherent continuation:

> Define the **alignment target object** as an equivalence class of interpretations under admissible semantic transformations that satisfy **both** RSI and ATI.

In other words: Alignment II becomes classification of **interpretation-preserving symmetry classes**—the “meaning physics” that remains after reflection removes fixed goals.
