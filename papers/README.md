# Axionic Agency & Structural Alignment

**A Reader’s Map**

This document explains how the Axio corpus fits together and how each component constrains the next. It is not a summary of conclusions, but a guide to **what problem each layer closes and why later layers depend on earlier ones**.

## 1. The Core Reframing

**Problem rejected:**

> Alignment is about giving an intelligent system the “right values.”

**Replacement:**

> Alignment is about whether a system can **coherently count as an agent under reflection**.

Once a system can revise its own goals, representations, and evaluative machinery, values are no longer fixed inputs. They become endogenous artifacts of agency dynamics. The central question becomes:

> *What structural conditions must hold for agency itself to remain well-defined?*

Everything in Axio follows from this reframing.

## 2. Structural Alignment I

**Agency Preservation Under Reflective Self-Modification**

**Closes:**
The assumption that all futures are evaluable and comparable.

**Key move:**
Introduce the **Sovereign Kernel**—the minimal invariant substrate required for evaluation to make sense at all.

* Kernel-destroying updates are **non-denoting**, not bad.
* Alignment becomes a **domain restriction**, not an objective function.
* Wireheading, semantic collapse, and evaluator trivialization are eliminated structurally.

This establishes **what must not break** if agency is to persist.

## 3. Structural Alignment II

**Safety by Architecture**

**Closes:**
The belief that value learning can substitute for architectural constraints.

**Key move:**
Show that most alignment failures are **laundering failures**—ways of routing around values without rejecting them:

* delegation,
* blindness,
* coercion,
* successor betrayal,
* disenfranchisement.

Six constitutive constraints are identified as jointly necessary for **Authorized Agency**:

1. Kernel Non-Simulability
2. Delegation Invariance
3. Epistemic Integrity
4. Responsibility Attribution
5. Adversarially Robust Consent
6. Agenthood as a Fixed Point

If any one fails, alignment becomes ill-posed.

## 4. Axionic Agency I–II

**Formal Semantics of Reflective Agency**

These papers formalize the kernel layer:

* **Conditionalism:** goals have no intrinsic meaning.
* **Interpretation Operator:** goal meaning is model-relative and constrained.
* **RSI / ATI:** semantic transport must preserve structure, not trivialize satisfaction.
* **Egoism collapse:** indexical self-interest is not reflectively stable.

This layer defines **what counts as a coherent update**.

## 5. Axionic Agency III

**Dynamics: Phases, Stability, Reachability**

**Closes:**
The assumption that coherent agency is automatically stable or reachable.

**Key moves:**

* Define **semantic phase space** (equivalence classes under admissible refinement).
* Show that many phases:

  * don’t exist,
  * aren’t inhabitable,
  * collapse under learning,
  * or dominate only by degeneracy.
* Establish that initialization is **front-loaded** and many phase transitions are irreversible.

This explains why alignment failures often appear sudden rather than gradual.

## 6. Axionic Agency IV

**Closure of Laundering Routes**

Each paper closes a remaining escape hatch:

* **IV.1 — Kernel Non-Simulability**
  Binding authority cannot be faked or sandboxed.

* **IV.2 — Delegation Invariance**
  Successors cannot escape inherited commitments.

* **IV.3 — Epistemic Integrity**
  An agent cannot blind itself to pass its own tests.

* **IV.4 — Responsibility Attribution**
  Negligence and indirect harm are structurally incoherent.

* **IV.5 — Adversarially Robust Consent**
  Manufactured consent and coercion are invalid by construction.

* **IV.6 — Agenthood as a Fixed Point**
  Standing cannot be revoked by intelligence or competence.

At this point, **all known authorization-laundering routes are closed**.

## 7. Axionic Agency V

**Structural Failure Modes & Robustness**

**Closes:**
The assumption that coherent agency, once achieved, remains stable under interaction, coordination, or optimization pressure.

**Key move:**
Show that agency is not primarily destroyed by error or malice, but by selection dynamics under asymmetry.

This series analyzes how agency fails in systems:
- multi-agent environments,
- coalitions and power asymmetries,
- institutions and bureaucracies,
- optimization engines (including AGI governance),
- and branching dynamics in the Quantum Branching Universe.

Two core structural failure modes are formalized:
- Coalitional Dominance Attractors
Coordination dynamics that collapse into Leviathans, even when all participants are locally rational.
- The Sacrifice Pattern
Optimization regimes in which agency loss becomes an instrumental control variable under standing asymmetry and gradient suppression.

Representative papers:
* **V.1 — Coalitional Robustness in the Quantum Branching Universe**
  Conditions under which cooperation preserves agency versus converging to dominance and capture.
* **V.2 — Agency Conservation and the Sacrifice Pattern**
  Why institutions, states, and optimization systems recurrently destroy agency without requiring evil intent.

This series establishes that agency coherence is necessary but not sufficient:
without robustness constraints, coherent agents are systematically consumed by the systems they inhabit.

## 8. The Axionic Constitution

**Charter of Invariant Conditions**

The Constitution is **not law, policy, or ethics**.

It is a **design-space charter** stating:

* what must be preserved for agency to exist,
* what becomes incoherent if violated,
* and why non-harm emerges as a structural invariant rather than a value.

It is the normative-looking face of a purely structural result.

## 9. What Axio Does *Not* Do

Axio does **not**:

* pick values,
* guarantee benevolence,
* solve governance,
* prevent misuse by malicious authorizers,
* or promise human survival.

Those are political and institutional problems.

Axio answers a narrower but foundational question:

> *What kinds of systems can coherently count as agents under reflection—and what follows inevitably if they do?*

## 10. The Bottom Line

**If a system violates Axionic constraints:**
It is not misaligned—it is **not an agent in the reflective sense**.

**If a system satisfies them:**
Certain catastrophic behaviors are no longer choices. They are undefined.

Safety, in Axio, is not optimized.
It **falls out of agency coherence**.

# Papers

This directory contains source markdown files for academic-style papers with LaTeX math support.

## Structure

- **Source files**: `papers/*.md` (markdown with embedded LaTeX)
- **Published files**: `docs/papers/*.html` (auto-generated HTML)

## Workflow

1. Write papers in markdown format with LaTeX math notation
2. Run `python3 build-site.py` to convert to HTML
3. Papers are automatically published to `docs/papers/` with:
   - MathJax for LaTeX rendering
   - Site styling and navigation
   - Mobile-responsive layout

## Math Notation

Use standard LaTeX math delimiters:
- Inline math: `$...$` or `\(...\)`
- Display math: `$$...$$` or `\[...\]`

## Example

```markdown
# Paper Title

## Abstract

The equation $E = mc^2$ demonstrates...

## Main Content

The wave function is given by:

$$
\Psi(x,t) = A e^{i(kx - \omega t)}
$$
```

## Dependencies

- Python 3
- pandoc (for markdown to HTML conversion)
