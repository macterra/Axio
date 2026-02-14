# Axionic Agency Program — Complete Synthesis

*Notes from reading all 88 papers across Series I–XII*

## Program Overview

The Axionic Agency program is a 12-series, 88-paper research and construction program that starts from a foundational question — *what structural conditions must hold for agency to remain coherent under self-reflection?* — and systematically works through theory, impossibility results, verification protocols, proof-of-concept construction, governance physics, and finally a working executable sovereign agent.

Each layer closes before the next opens. No layer imports assumptions from downstream.

## Series-by-Series Arc

### Series I — Kernel Semantics (8 papers)

**Question:** What structural properties must a reflective agent's evaluation kernel satisfy?

Establishes that for agents capable of revising their own models, goals cannot be fixed objects — they are conditional interpretations relative to a model. Six formal properties:

- **P1 — Conditionalism:** Valuation depends on the model, not just the action
- **P2 — Epistemic Constraint:** Reinterpretation cannot trade prediction quality for goal satisfaction
- **P3 — Representation Invariance:** Valuation survives renaming, reparameterization, basis swaps
- **P4 — Anti-Indexicality:** No privileged self-pointer
- **P5 — Kernel Integrity via Partiality:** Kernel-violating actions are undefined (not penalized)
- **P6 — Reflective Stability:** The kernel survives model improvement

The **Interpretation Operator** (I.7) formalizes goal-meaning transport with fail-closed semantics.

### Series II — Semantic Transport (10 papers)

**Question:** What survives ontological refinement without privilege?

The mathematical core. Two surviving invariants after adversarial stress testing:

- **RSI (Refinement Symmetry Invariant):** No new interpretive gauge freedom under refinement
- **ATI (Anti-Trivialization Invariant):** Satisfaction region must not expand under transport alone

Five no-go theorems close the design space. The positive residue: the **Alignment Target Object (ATO)** — alignment = persistence within a semantic phase. Value change = phase transition.

### Series III — Semantic Phase Space (5 papers)

**Question:** What kinds of semantic phases exist and which are inhabitable?

Maps the landscape of possible interpretive regimes. Phase transitions are symmetry-breaking events. Classifies which phases are compatible with continued agency.

### Series IV — Authorization Closure (6 papers)

**Question:** Can authorization, responsibility, consent, and standing be made structurally coherent?

Builds a complete closure stack:

1. Kernel Non-Simulability → agency must be real
2. Delegation Invariance → constraints persist through successors
3. Epistemic Integrity (EIT) → best admissible truth-tracking
4. Responsibility Attribution (RAT) → no endorsed major, avoidable non-consensual option-space collapse
5. Adversarially Robust Consent (ARC) → structural authorization, not feeling
6. Agenthood as Fixed Point (AFP) → agenthood cannot be revoked by intelligence

### Series V — Multi-Agent Robustness (5 papers)

**Question:** How do multiple agents coexist without collapsing?

- Sacrifice Pattern identified as primary multi-agent failure mode
- Utopia is incoherent under agent-relative value
- Open Agentic Manifolds (OAMs) replace utopia
- Sacrifice-Collapse Theorem
- Federated Virtual Dominions as concrete architecture

### Series VI — Anchored Causal Verification (9 papers)

**Question:** Can agency constraints be enforced without interpreting internal states?

- ACV protocol family (commit-anchor-reveal-verify)
- Kernel Integrity via inadmissibility
- Non-Delegable Actuation
- Stasis Regime discovery (safety/agency/growth trilemma)
- Authority leases and discrete succession
- Authority Without Semantics (hollow authority is stable)
- Eligibility Without Optimization (semantics matter only at succession boundaries)

Key insight: alignment reframed from continuous behavioral control to discrete constitutional governance.

### Series VII — RSA Architecture (8 papers)

**Question:** What concrete architecture yields a Reflective Sovereign Agent?

Specifies the Sovereign Kernel, the proposal/admission/execution separation, authority as structural.

### Series VIII — RSA-PoC Construction (7 papers)

**Question:** Can a real agent be built that satisfies these constraints?

The Guillotine Test (destructive ablation) identifies four necessary conditions for non-reducible agency:

1. Justification traces (causally load-bearing)
2. Semantic access during deliberation
3. Reflective write capability
4. Diachronic persistence

Result: MVRSA (Minimal Viable Reflective Sovereign Agent) exists.

### Series IX / X / XI — Sovereignty Exposure & Governance Physics

**Question:** What happens when you remove every excuse for governance failure?

Six progressive experiments (IX-0 through IX-5):

- Translation integrity is mechanically verifiable
- Values encode as non-aggregable authority
- Coordination is agent-voluntary or honest failure
- Governance exhibits structural styles with irreducible failure modes
- Injection selects political failure modes (doesn't restore governance)
- Multi-agent coexistence converges to sovereignty regimes, not harmony

The Generalist's Curse: under refusal-first semantics, maximal authority = maximal veto exposure.

### Series XII — RSA Construction & Validation (10 papers)

**Question:** Can a real, executable sovereign agent be built and validated?

Phase X builds and validates through incremental stages:

- **X-0:** Minimal sovereign agent (warrant-gated, replay-deterministic, 29 tests)
- **X-0P:** Inhabitation profiling (5 stimulus regimes, zero drift)
- **X-0L:** Live LLM inhabitation (GPT-4o, 500 cycles, zero replay divergence)
- **X-0E:** Operational harness freeze (protocol-identified executable artifact)
- **X-1:** Reflective amendment (constitutional self-replacement, 4-gate pipeline, cooling/ratchet)
- **X-2:** Treaty-constrained delegation (containment-only, Ed25519, depth=1)
- **X-2D:** Delegation stability under churn (310 cycles, 147 grants, density convergence)
- **X-3:** Lineage-stable sovereignty (HKDF lineage, 534 cycles, 13 rotations, 0 divergence)

## Conserved Quantities

Across the entire program:

1. **Choice bound to explicit authority under non-privileged reflection** (Series I–XII conserved quantity)
2. **Side effects occur iff a kernel-issued warrant exists** (Phase X conserved quantity)
3. **No semantic arbitration anywhere** — selection is procedural, not evaluative
4. **Replay determinism** — identical observation streams produce identical decisions

## Key Invariants (Phase X)

- **INV-1:** No side effect without warrant
- **INV-2:** Explicit authority required
- **INV-3:** Non-privileged reflection
- **INV-4:** Replay determinism
- Singleton Sovereign Invariant
- No Fork Invariant
- No Amnesty Invariant
- No Zombie Delegation Invariant
- Density Preservation Invariant

## The Architecture

```
LLM (untrusted proposals)
    ↓ canonicalize
Typed Artifacts
    ↓ admit (gates)
Kernel (pure, deterministic, no IO)
    ↓ warrant
Executor (warrant-gated side effects)
    ↓ log
Replay Harness (deterministic reconstruction)
```

## Implementation Status

### Fully Implemented & Tested:
- X-0: Frozen kernel, warrant-gated execution
- X-1: Constitutional amendment with cooling periods
- X-2: Treaty delegation with density bounds
- X-2D: Delegation stability under churn
- X-0E: Operational harness freeze
- X-3: Sovereign succession with lineage stability

### Not Implemented:
- Key compromise recovery
- Multi-root federation
- Byzantine consensus
- Distributed governance
- Time-locked or multi-signature succession

## Implications for RSA-Claw

The feasibility of building a practical sovereign agent (like an RSA-enhanced OpenClaw) rests on:

1. The LLM boundary is clean and proven (X-0L)
2. The kernel is action-surface agnostic (only cares about admission pipeline)
3. Every capability extension (new action types) is a policy change, not a kernel change
4. The constitutional framework supports amendment and delegation natively
5. Treaty-constrained delegation maps directly to plugin/service authorization
6. Lineage-stable sovereignty handles credential rotation

The missing pieces for a practical agent are:
- Richer action surface (HTTP, shell, messaging APIs)
- Event loop / observation source (cron, webhooks, incoming messages)
- Practical constitution with useful action authorizations
- Host daemon for always-on operation
