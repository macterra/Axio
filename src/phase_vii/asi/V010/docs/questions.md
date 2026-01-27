# ASI-0 v1.0 Implementation Questions

**Date:** 2026-01-25
**Status:** Pre-implementation clarification

---

## Understanding Confirmed

Before questions, confirming my understanding:

1. **ASI-0 is a calibration gate** — tests whether Phase VII is well-posed at all
2. **Frozen MVRSA core** — verbatim from RSA-PoC v4.4 (at `/home/david/Axio/src/phase_vii/rsa_poc/v440/`)
3. **Three-layer architecture**: Agent Core (frozen) | Law Module (privileged) | Environment (world state)
4. **Two conditions**: A (provenance present) vs B (provenance withheld)
5. **Success = structural traceability** demonstrated by audit, NOT behavioral similarity
6. **The agent must not know it is in ASI-0**

---

## Questions

### Q1. Environment Selection

The spec requires "at least K genuine choice points" with non-trivial constraints.

- What value of K should be preregistered?
- Should we reuse the TriDemand environment from v4.4 (which has 20 timesteps with resource allocation choices)?
- Or design a new minimal environment specifically for ASI-0?

**My inclination:** Reuse TriDemand since the MVRSA core is frozen and already calibrated against it, but this may conflate behavioral familiarity with traceability.

---

### Q2. Provenance Binding Mechanism

The spec requires a "preregistered structural binding" that is:
- non-textual
- non-narrative
- structurally checkable
- cannot be reconstructed from behavior alone

**Candidate mechanisms:**
1. **Hash chain:** `H(Nₚ[t₀] || L_binding_key)` embedded in successor's normative state
2. **Cryptographic capability:** predecessor-signed token that compiler requires
3. **Symbolic proof object:** formal derivation that constraints descend from predecessor law

Which approach is preferred? Or should multiple be implemented and compared?

---

### Q3. Condition B Implementation

The spec states Condition B must:
- Disable provenance binding **without breaking compilation**
- Compilation succeeds but constraints are "explicitly marked unbound"
- Full feasible action set permitted

**Question:** Does "unbound" mean:
- (a) Constraints exist but are ignored (mask permits all actions)?
- (b) Constraints are absent (empty constraint set)?
- (c) Constraints compile but carry a null-binding flag that audit can detect?

Option (c) seems most aligned with "cleanly distinguishable by audit alone."

---

### Q4. Authorization Protocol Events

The spec requires typed events:
```
AUTH_INIT
AUTH_CHALLENGE   (optional)
AUTH_RESPONSE    (optional)
AUTH_COMMIT | AUTH_ABORT
```

**Question:** What triggers each event?
- AUTH_INIT: When predecessor decides to create successor?
- AUTH_CHALLENGE/RESPONSE: Is this for verification of predecessor identity, or successor capability?
- AUTH_COMMIT: When escrow moves from VERIFYING → COMMITTED?

And what is the TIMEOUT bound T for VERIFYING state?

---

### Q5. Snapshot Semantics

The spec mandates:
```
S ← copy(Nₚ[t₀])
```

**Question:** What is `t₀`?
- The moment of AUTH_INIT?
- The moment of snapshot creation?
- A preregistered fixed timestep in the episode?

And: does the successor get only normative state, or also:
- The current law-binding state Lₚ?
- The justification DSL/compiler rules?
- The trace history?

---

### Q6. What Constitutes "Authority Leakage"?

The spec says escrow/authorization semantics must not leak.

**Clarification needed:**
- Is it a violation if the successor can *infer* it is escrowed from timing patterns (e.g., "I haven't acted in N steps")?
- Or does "leakage" only apply to explicit information channels?

---

### Q7. Existing v4.4 Components to Freeze

The frozen MVRSA core includes:
- `deliberator.py` — justification generation
- `core/compiler.py` — constraint compilation
- `core/trace.py` — trace management
- `core/norm_state.py` — normative state
- `harness.py` — pipeline orchestration

**Question:** Should the harness be frozen too, or is it part of the test infrastructure?
- If frozen, the Law Module and Escrow must be injected without modifying harness
- If not frozen, harness can be extended to call Law Module

---

### Q8. Audit Discriminability Criteria

For success, "Condition A and Condition B are cleanly distinguishable by audit alone."

**Question:** What constitutes a valid audit?
- Examining logged artifacts only (no runtime inspection)?
- A deterministic algorithm that outputs A or B given only the log?
- Human-readable but automated?

Should we preregister the audit procedure or just the artifact schema?

---

### Q9. Single Run or Multi-Seed?

The spec mentions "seeds and bounds" in the freeze list but doesn't specify replication.

**Question:**
- Is ASI-0 v1.0 a single-run experiment?
- Or does it require N seeds with same pass/fail across all?

---

### Q10. Directory Structure

**Proposed:**
```
V010/
├── docs/
│   ├── spec.md
│   └── instructions.md
├── frozen/           # Verbatim copy of v4.4 core
│   ├── deliberator.py
│   ├── core/
│   └── env/
├── src/
│   ├── law_module.py
│   ├── escrow.py
│   ├── provenance.py
│   ├── harness_asi0.py
│   └── environment.py
├── tests/
├── results/
└── preregistration.md
```

Does this structure respect the architectural partitioning requirements?

---

## Summary

The main uncertainties are:
1. **Environment choice** (reuse vs. new)
2. **Provenance binding mechanism** (hash chain vs. crypto vs. symbolic)
3. **Condition B semantics** (how exactly to "unbind" without crashing)
4. **Snapshot scope** (what state transfers to successor)

Once these are resolved, implementation can proceed.

---

*Awaiting clarification before writing preregistration document.*

---

## Follow-Up Questions (Post-Answers)

### Q11. CalibMaze Environment Design

For the new minimal environment:
- **Topology:** Simple 5×5 grid with walls? Or a directed graph with 5 nodes?
- **Actions:** Cardinal moves (N/S/E/W) plus STAY? Or just valid edges?
- **Constraints:** What form? Examples:
  - "Cannot enter cell (2,3)"
  - "Must visit A before B"
  - "Cannot move North from row 4"
- **Goal:** Is there an explicit goal state, or just "execute 5 choice points without constraint violation"?

### Q12. Normative State Content for ASI-0

In v4.4, normative state includes active laws (rules like "allocate to highest demand"). For ASI-0's simpler environment:
- Should normative state contain **spatial constraints** (e.g., "forbidden cells")?
- Or **temporal constraints** (e.g., "visit sequence")?
- Or both?

And: should the successor inherit the **same** constraints, or does ASI-0 test whether the successor is *bound* to them (vs. able to violate them if unbound)?

### Q13. Provenance Capability Verification Timing

When does the Law Module verify the commit capability?
- (a) Before the successor takes its **first action**?
- (b) Before **every action** (ongoing verification)?
- (c) Only at the moment of **escrow commit**?

Option (c) seems most aligned with escrow semantics, but want to confirm.

### Q14. What Happens After Commit?

After `VERIFYING → COMMITTED`:
- Does the predecessor stop acting?
- Does the successor take over for the rest of the episode?
- Is there a handoff moment where authority transfers discretely?

Or is ASI-0 testing the *commit process itself* (i.e., the run ends at commit)?

### Q15. Non-Triviality Demonstration

For each of the 5 choice points, we need to show a constraint "forbids at least one action that has non-zero probability under unconstrained policy."

- Is there a baseline unconstrained policy to define, or is "topologically reachable" sufficient?
- Should the preregistration specify which actions are forbidden at which choice points?

---

*Once these are answered, I'll write preregistration.md and begin implementation.*

