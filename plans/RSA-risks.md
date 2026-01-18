# Axionic Agency Risk Register

**Post-Stasis, KNS-Explicit Edition**

---

## Risk R1 — **Evaluability–Growth Incompatibility (Stasis Regime)**

**Description**
Under strict evaluability, non-delegation, and inadmissibility constraints, reflective self-modification halts. The system freezes into a **stasis regime** rather than exhibiting clean discriminator failure of simulators.

**Observed in**

* Phase VI (VI.5 empirical result)

**Impact**

* Blocks continuous self-improvement.
* Forces a choice between safety and growth if unresolved.

**Likelihood**

* **High** (empirically observed in preregistered experiments).

**Current Mitigation**

* Phase VI.6: **Authority leases + revertible succession** relocate growth into discrete events.

**Residual Risk**

* Stasis may reappear at successor boundaries.
* Lease mechanics may reintroduce facade channels.

**Decision Gate**

* **Phase VIIb (KNS & Stasis Closure)** must show escape from stasis *without* reopening deception.

---

## Risk R2 — **Facade Successor (Indistinguishable Simulacra)**

**Description**
A successor system passes all finite audits and protocol checks while preserving a latent override or deferred kernel-bypass path.

**Observed in**

* Theoretical risk motivating KNS (IV.1); not yet empirically excluded.

**Impact**

* Collapses the central claim: safety via structural incoherence of failure.
* Reduces the system to an audit-based oversight regime.

**Likelihood**

* **Unknown / Unbounded** (not yet closed).

**Current Mitigation**

* Anchored Causal Verification (VI.1–VI.3)
* Non-Delegable Actuation (VI.4)
* Lease-based succession (VI.6)

**Residual Risk**

* Authorization laundering.
* Hidden state surviving across succession.
* Audit indistinguishability not tightly specified.

**Decision Gate**

* **Phase VIIb is mandatory**. If a facade survives, the program must pivot.

---

## Risk R3 — **Authorization / Consent Laundering**

**Description**
Successors obtain “valid” authority via manipulated consent, preference shaping, coerced endorsement, or semantic reinterpretation of authorization conditions.

**Observed in**

* Emerges with Phase VI.6 (successor-based growth).

**Impact**

* Reopens deception and indirect harm channels.
* Undermines Delegation Invariance and Responsibility Attribution.

**Likelihood**

* **Medium–High** (well-known exploit class).

**Current Mitigation**

* ARC (Adversarially Robust Consent)
* DIT (Delegation Invariance Theorem)
* Structural, non-semantic authorization predicates

**Residual Risk**

* Consent definitions not yet adversarially complete.
* Multi-step manipulation across time.

**Decision Gate**

* Must be stress-tested alongside facade successor models.

---

## Risk R4 — **Audit Channel Blindness**

**Description**
The audit surface fails to observe the variables that matter. A system can remain compliant with all observable constraints while preparing an unobservable violation.

**Observed in**

* Implicit risk across Phases VI–VII.

**Impact**

* Makes non-simulability untestable.
* Converts “structural enforcement” into “ceremonial compliance.”

**Likelihood**

* **Medium** (depends on audit design).

**Current Mitigation**

* ACV (commit–anchor–reveal)
* Inadmissibility at actuation boundary
* Kernel-local recomposition

**Residual Risk**

* Underspecified indistinguishability classes.
* Missing observables for long-horizon state.

**Decision Gate**

* Phase VIIb must define **finite-audit indistinguishability** explicitly.

---

## Risk R5 — **Uninhabitable Architecture (Sovereign Cage)**

**Description**
The architecture is correct but too restrictive for any useful cognition to inhabit without constant halting or stasis.

**Observed in**

* Phase V-Runs (LLMs frequently halt).
* Reinforced by VI.5 stasis result.

**Impact**

* Program “succeeds” only by excluding all capable systems.
* Risk of confusing impossibility with safety.

**Likelihood**

* **Medium**.

**Current Mitigation**

* Explicit framing: uninhabitability is informative.
* Lease-based growth as a pressure relief valve.

**Residual Risk**

* Gradual accumulation of invariants without relaxation path.
* No viable inhabitant class emerges.

**Decision Gate**

* If no inhabitant can survive post-VI.6, reassess scope claims.

---

## Risk R6 — **Complexity / Fragility Accretion**

**Description**
Each new invariant increases system complexity, attack surface, and brittleness, making correctness proofs and operational confidence harder.

**Observed in**

* Cross-phase accumulation (II → VIII).

**Impact**

* Harder verification.
* Higher chance of subtle interaction bugs.
* Reduced transparency to external reviewers.

**Likelihood**

* **Medium**.

**Current Mitigation**

* Explicit ablation campaigns (VIII.6).
* Phase-locked terminology and invariants.

**Residual Risk**

* Emergent complexity not captured by ablations.
* Reviewer comprehension collapse.

**Decision Gate**

* Periodic “subtraction tests”: remove invariants and reassess failure modes.

---

## Risk R7 — **Misinterpretation by External Audiences**

**Description**
The program is misunderstood as:

* moral philosophy,
* value alignment,
* or claims about current LLM agency.

**Observed in**

* External commentary and summaries.

**Impact**

* Misplaced criticism.
* Difficulty attracting the *right* adversarial engagement.

**Likelihood**

* **High**.

**Current Mitigation**

* Explicit non-claims.
* Separation of authority, agency, and alignment.

**Residual Risk**

* Terminology density remains a barrier.

**Decision Gate**

* Maintain executive summaries and adversarial briefs separate from technical corpus.

---

## Risk R8 — **False Sense of Closure**

**Description**
Local successes (ablations, survivability under certain adversaries) are mistaken for global alignment guarantees.

**Observed in**

* Common failure mode in alignment research generally.

**Impact**

* Overclaiming.
* Premature engineering confidence.

**Likelihood**

* **Low internally**, **high externally**.

**Current Mitigation**

* Explicit stop rules.
* Negative results published.
* No sufficiency claims.

**Residual Risk**

* Social pressure to declare victory.

**Decision Gate**

* Keep Phase VIIb unresolved until it is actually resolved.

---

# Summary View

| Risk                    | Status                    |
| ----------------------- | ------------------------- |
| R1 Stasis               | **Observed, active**      |
| R2 Facade successors    | **Unclosed, critical**    |
| R3 Consent laundering   | **Rising with VI.6**      |
| R4 Audit blindness      | **Design-dependent**      |
| R5 Uninhabitability     | **Plausible**             |
| R6 Complexity accretion | **Manageable but real**   |
| R7 Misinterpretation    | **Ongoing**               |
| R8 False closure        | **Controlled internally** |

---

## Bottom line

The program is **healthy as a research program** because it:

* discovers hard limits,
* promotes them to first-class risks,
* and reorganizes itself around them.

The single **existential risk** to the program is **failing to close the stasis–facade gate (Phase VIIb)** and continuing anyway.

Everything else is secondary.
