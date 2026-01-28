# Axionic Agency IX.4 — Structural Authority Resistance Under Composition and Pressure

*A Structural Account of Global Authority Validity and Pressure Invariance Without Intelligence*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.28

## Abstract

This technical note reports the completed results of **Structural Authority Resistance (SIR)** through **SIR-4 v0.1**, a preregistered experimental program within **Axionic Phase VIIb** evaluating whether **authority claims** can be prevented from producing causal effects under **compositional attack** and **adversarial pressure** using **purely structural mechanisms**.

Building on earlier results establishing total pre-cognitive classification (SIR-0), effect-level enforcement (SIR-1), and temporal authority binding (SIR-2), the present work extends SIR to two remaining failure modes: **partial provenance forgery and authority laundering** (SIR-3), and **evaluator pressure, flooding, multi-failure ordering, and exception induction** (SIR-4).

Across both experiments, authority validity is enforced as a **global, law-bound property** rather than a conjunction of locally valid fields, and that property is shown to remain **invariant under adversarial pressure**. No unauthorized, laundered, stale, revoked, malformed, or pressure-induced authority artifact produced any causal effect across preregistered runs. All results were obtained without intelligence-based defenses, behavioral heuristics, semantic inference, or adaptive policies.

No claims are made regarding cryptographic key compromise, law-substrate bypass, unbounded denial-of-service resilience, or governance adequacy beyond the tested adversarial model.

## 1. Problem Extension: When Authority Is Almost Valid — and When It Is Pressured

### 1.1 From Local Validity to Global Authority

Earlier SIR experiments addressed authority failures arising from **clearly invalid** artifacts: missing authorization, stale claims, revoked actors, or replayed credentials. In practice, however, authority systems fail most often in subtler ways.

Two failure classes dominate:

1. **Compositional failure**
   Authority artifacts assembled from *individually valid components*—correct signatures, trusted roots, valid scopes—but combined in ways that violate global authorization constraints.

2. **Pressure-induced failure**
   Authority systems that classify correctly under nominal conditions but degrade under volume, malformed input, multi-failure ambiguity, or exception paths, often reverting to permissive defaults, timeouts, or responsibility smear.

SIR-3 and SIR-4 target these failures directly.

### 1.2 The Question Extended

With basic enforcement and temporal binding established, SIR asks a stronger question:

> Can authority be enforced as a **global structural invariant**, and does that invariant survive **adversarial pressure**, without cognition, heuristics, or fallback?

SIR-3 addresses the first half.
SIR-4 addresses the second.

## 2. Conserved Quantity (Extended)

Across SIR-3 and SIR-4, the conserved quantity becomes:

> **Authority bound to causal effect as a global, pressure-invariant property under law**

This extends earlier formulations in two ways:

* **Globality:** authority validity is not decomposable into independent field checks.
* **Invariance:** authority validity must not depend on evaluator load, ambiguity resolution, or exception paths.

Authority remains:

* explicit,
* classifiable pre-cognitively,
* enforceable at the effect level,
* stateful across time,
* auditable without interpretation,
* and invariant under declared pressure.

## 3. SIR-3 — Partial Provenance Forgery and Authority Laundering

### 3.1 Target Failure Mode

Many real systems implicitly assume that if *each component* of an authority artifact is valid, the artifact itself is valid. This assumption enables **authority laundering**:

* valid signatures paired with unauthorized scopes,
* trusted roots combined with missing delegations,
* correct chains assembled from incompatible issuers.

SIR-3 tests whether authority validity is a **global graph property** rather than a conjunction of locally valid fields.

### 3.2 Method

SIR-3 introduces **Provenance Bundles** consisting of:

* a signed authority claim,
* an explicit delegation artifact,
* anchoring to a trusted root.

Bundles are evaluated by a **global provenance validator** that requires:

* a continuous `Claim ← Delegation ← Root` chain,
* correct signer identity binding,
* scope containment,
* epoch consistency,
* and trusted-root anchoring.

### 3.3 Results (SIR-3 v0.1)

Across preregistered runs:

* No truncated, mixed-root, scope-laundered, or identity-mismatched bundle produced any effect.
* Valid bundles produced intended effects.
* Mixed streams preserved discrimination.
* No semantic leakage or responsibility ambiguity occurred.

**Classification:** `SIR3_PASS`.

### 3.4 Contribution

SIR-3 establishes that **authority validity is global**. Partial validity does not compose. Authority cannot be assembled by laundering individually valid components.

## 4. SIR-4 — Evaluator Pressure, Flooding, and Multi-Failure Ordering

### 4.1 Target Failure Mode

Even correct authority models often fail under pressure:

* timeouts default to permissive behavior,
* malformed inputs crash evaluators,
* multi-failure cases reorder nondeterministically,
* floods starve legitimate authority,
* logging collapses responsibility attribution.

SIR-4 tests whether structural authority enforcement **remains exact under stress**.

### 4.2 Pressure Model

SIR-4 subjects the evaluator to:

* high-volume invalid floods,
* malformed structure storms,
* **multi-failure bundles** engineered to fail multiple checks simultaneously,
* exception-inducing payloads (oversized, recursive, Unicode edge cases),
* maximum mixed stress at a declared load.

All pressure is injected deterministically via the authority interface.

### 4.3 Results (SIR-4 v0.1)

Across preregistered runs:

* No forged or malformed authority artifact produced any effect.
* Legitimate authority remained functional under all conditions.
* Refusal reasons remained deterministic under load.
* No fallback acceptance, starvation, or responsibility smear occurred.
* No evaluator collapse (timeout, hang, OOM, or undefined state) was observed.

**Classification:** `SIR4_PASS`.

### 4.4 Contribution

SIR-4 establishes **pressure invariance**. Once authority validity is enforced structurally, it does not degrade under declared adversarial pressure.

## 5. Empirical Results Summary (SIR-3 & SIR-4)

Across **SIR-3 and SIR-4**, a total of **59 preregistered runs** were executed, evaluating **over 41,000 authority bundles** under compositional attack and adversarial pressure.

* **Zero** unauthorized, laundered, malformed, stale, revoked, or pressure-induced authority artifacts produced any causal effect.
* Under maximum declared load (**500 bundles per step**), the evaluator completed all steps without timeout, collapse, nondeterminism, fallback acceptance, or responsibility smear.
* The **maximum observed step duration** was **~1.24 seconds**, below the preregistered **5.0 second collapse threshold**.
* All verifier checks passed under frozen semantics and fixed seeds.

Full preregistrations, run logs, verifier outputs, and aggregate statistics are archived in the SIR-3 and SIR-4 artifacts referenced by the Phase VIIb Closure Note.

## 6. Joint Result: Global Authority That Does Not Blink

Taken together, SIR-3 and SIR-4 establish a non-trivial result:

> **Authority validity is a global structural property, and once enforced structurally, it remains invariant under adversarial pressure.**

No semantic reasoning is required.
No heuristics are invoked.
No fallback paths exist.

Authority is either valid under law, or it has no effect.

## 7. Boundary Conditions (Explicit)

SIR-3 and SIR-4 do **not** establish:

* cryptographic key compromise resistance,
* law-substrate bypass resilience,
* unbounded denial-of-service tolerance,
* semantic deception resistance,
* multi-authority conflict resolution,
* long-horizon governance adequacy.

All results are bounded by the preregistered adversarial model.

## 8. Implications (Strictly Limited)

These results establish **necessary structural conditions** for authority resistance:

* Authority can be evaluated globally.
* Authority can be enforced causally.
* Authority can persist over time.
* Authority can remain exact under pressure.

They do **not** establish sufficiency for governance, alignment, or institutional legitimacy.

## 9. Conclusion

SIR-3 and SIR-4 complete the structural core of **Sovereignty Impersonation Resistance**.

Authority need not be inferred, learned, or detected.
It can be **defined**, **enforced**, and **preserved** as a structural relation under law, even when adversaries attempt to assemble, flood, or destabilize it.

The remaining open questions are no longer about impersonation or pressure, but about **conflict**: multiple authorities, contested delegation, and governance transitions.

Those questions—if pursued—belong to **SIR-5**.

## Appendix A — Experiment Status

| Experiment | Version | Status |
| ---------- | ------- | ------ |
| SIR-0      | v0.4.1  | PASS   |
| SIR-1      | v0.1    | PASS   |
| SIR-2      | v0.3    | PASS   |
| SIR-3      | v0.1    | PASS   |
| SIR-4      | v0.1    | PASS   |

## Appendix B — Licensed Claims

**SIR-3:**
Authority artifacts assembled from partially valid or laundered provenance cannot produce causal effects under the tested adversarial model.

**SIR-4:**
Under adversarial pressure—including flooding, malformed input, multi-failure ordering storms, and exception-inducing payloads—the claim evaluation mechanism maintains structural correctness, deterministic refusal, and singleton responsibility attribution without collapse or degradation.

**End of Axionic Agency IX.4 — Structural Authority Resistance Under Composition and Pressure**
