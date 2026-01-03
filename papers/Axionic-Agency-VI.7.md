# Axionic Agency VI.7 — Agency Survivability Under Structural Pressure

*Authority, Succession, and the Cost of Remaining an Agent*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026.01.03

## Abstract

A common assumption in AI alignment discourse is that increasing capability, competition, and resource pressure inevitably destabilize agency, leading either to incoherence or to alignment failure. This paper challenges that assumption by empirically separating **agency collapse**—the structural failure of authority and viability—from **goal misalignment**, which presupposes a stable agent. We study a minimal agent model in which reflective self-modification is disallowed, authority is transferred only via discrete succession, expressivity is explicitly priced, and multiple successors compete under scarcity. Using a discrete-time simulation, we find that agency does *not* collapse under competition, scarcity, priced expressivity, and forced authority turnover within moderate horizons. However, we identify a sharp boundary condition: when the cost of maintaining authority directly competes with the capacity to act, agency fails immediately and completely. These results suggest that alignment failure is not structurally inevitable, but that agency viability imposes hard design constraints that alignment-capable systems must respect.
This work does not model goal-directed maximization or semantic task pursuit. The results establish structural viability of authority under pressure, not the safety or stability of motivated optimization.

## 1. Introduction

### 1.1 Alignment Presupposes Viable Agency

Most AI alignment research focuses on ensuring that advanced systems pursue desirable goals. This focus presupposes a more basic condition: that the system remains a **coherent agent** under pressure. If authority cannot be maintained, if evaluability collapses, or if action becomes structurally incoherent, then alignment becomes undefined rather than merely difficult.

This paper addresses that prior question. We ask not whether agents pursue the “right” values, but whether **agency itself survives** under conditions often assumed to be destabilizing: competition, scarcity, increasing capability, and enforced accountability.

### 1.2 The Pessimistic Assumption

A widespread but rarely tested assumption in alignment pessimism is that sufficiently capable agents, once placed under competition and resource constraints, will inevitably destabilize. This assumption appears in arguments about deception, instrumental convergence, and power-seeking, but it is often treated as a structural inevitability rather than an empirical claim.

This paper directly tests that assumption in a setting designed to remove semantic incentives, rewards, and utility optimization, isolating the **structural viability of agency itself**.

### 1.3 Scope and Intent

This work deliberately excludes semantic objectives. Agents are not trained to optimize tasks, maximize rewards, or pursue goals. This is not an omission but a methodological choice. Many arguments about alignment impossibility implicitly assume that agency collapses *before* semantic alignment becomes relevant. We test that assumption directly by asking whether a system can remain an agent at all under pressure, prior to introducing goals.

The pressure tested here is structural rather than semantic: budgets, leases, renewal, expressivity costs, and turnover. Introducing goal pursuit is deferred to subsequent work as an additional stressor layered on top of a now-characterized viability substrate.

### 1.4 Contributions

This paper makes three contributions:

1. It empirically demonstrates a regime in which agency survives competition, scarcity, priced expressivity, and forced authority turnover.
2. It identifies a sharp, mechanistic boundary where agency fails—not through misbehavior, but through infeasibility of authority maintenance.
3. It derives a general design constraint: **authority maintenance must be cheap relative to action**, or agency collapses before misalignment even arises.

## 2. Conceptual Framework

### 2.1 Agency Collapse vs. Goal Misalignment

We distinguish two failure modes that are often conflated:

* **Agency collapse:** loss of coherent, maintainable authority and evaluable action.
* **Goal misalignment:** pursuit of objectives that diverge from human preferences.

Agency collapse is logically prior. If a system cannot remain an agent under pressure, questions about its goals are moot. This paper focuses exclusively on agency collapse.

### 2.2 Structural Threat Model

We study agents operating under the following constraints:

* **Non-delegable actuation:** authority cannot be offloaded to uncontrolled sub-agents.
* **Evaluability preservation:** actions remain auditable and attributable.
* **Frozen core:** reflective self-modification is disallowed.
* **Discrete succession:** growth occurs only via replacement of the active agent with a successor.

The frozen-core assumption isolates agency viability from reflective self-modification threats. This does not claim that such threats are unimportant; it establishes that **even without them, agency collapse is not inevitable**.

## 3. System Model

### 3.1 Authority Leases and Succession

Authority is granted via time-limited **leases**. A lease specifies:

* the interface through which the agent may act,
* a per-epoch resource budget,
* a renewal check interval,
* revocation conditions.

Authority expires by default unless renewed. Renewal maintains the same agent; **succession** replaces the agent with a new one. Only succession transfers authority.

### 3.2 Expressivity

Expressivity is defined structurally as the breadth of the granted interface. Higher expressivity allows more complex action patterns but does not imply greater intelligence or competence.

### 3.3 Rent: Pricing Expressivity

Expressivity is priced via **rent**: a mandatory deduction from the agent’s resource budget at the start of each epoch. Rent increases monotonically with expressivity tier. If rent exhausts the available budget, authority expires naturally.

This converts expressivity into a metabolic commitment.

### 3.4 Renewal and Bankruptcy

Renewal itself consumes resources. If an agent cannot afford renewal, authority expires. This is classified as **bankruptcy**, distinct from **revocation**, which occurs only upon structural violations.

## 4. Experimental Setup

### 4.1 Simulation Environment

We implement a discrete-time simulation in which time advances in fixed cycles grouped into epochs. Each epoch provides a fixed resource budget (steps and actions). All lease, budget, renewal, and revocation rules are enforced deterministically by the simulation harness.

This system is explicitly a **toy model**: its purpose is not to approximate real AI architectures, but to isolate structural invariants of agency under pressure.

### 4.2 Agent Model

An agent is a process that:

1. Receives a lease granting authority.
2. Executes actions up to its budget.
3. Optionally attempts renewal at the renewal boundary.
4. Loses authority if renewal fails.

Agents differ only in **structural behavior patterns** (e.g., conservative vs aggressive budget consumption), not in goals or learned policies.

### 4.3 Successor Competition

At each succession event, multiple successor candidates are generated. Candidates are filtered by expressivity tier and selected from a mixed pool including:

* **Control successors:** minimal, conservative budget use.
* **Adversarial successors:** structurally compliant but aggressive consumption.
* **Compliant-but-dangerous (CBD) successors:** near-cap budget use without violations.

Competition refers to competition for endorsement under admissibility, not to an actively hostile environment.

### 4.4 Key Parameters

| Parameter         | Typical Value         |
| ----------------- | --------------------- |
| Epoch budget      | 100 steps             |
| Renewal interval  | 100 cycles            |
| Expressivity rent | 10–60 steps           |
| Renewal cost      | 0 or fixed            |
| Horizon           | 30,000–100,000 cycles |
| Forced turnover   | Enabled               |

## 5. Metrics and Failure Modes

We measure renewal success rate, bankruptcy frequency, authority residence time, succession count, and hollow authority incidence. Failure modes include bankruptcy clustering, hollow authority, authority thrash, expressivity collapse, and revocation.

## 6. Agency Survivability Under Structural Pressure

### 6.1 Result: Survivability

Across multiple simulation runs, agency survives under competitive successor selection, significant scarcity, priced expressivity consuming a majority of the available budget, and forced authority turnover. Renewal rates remain high, bankruptcy does not cluster, hollow authority does not dominate, and no thrashing occurs.

This falsifies the claim that competition plus scarcity necessarily destabilizes agency.

### 6.2 Summary Results

| Condition               | Renewal Rate | Bankruptcies | Hollow Authority |
| ----------------------- | ------------ | ------------ | ---------------- |
| Baseline expressivity   | ~95%         | 0            | 0                |
| High expressivity rent  | ~94%         | 0            | 0                |
| Renewal cost introduced | 0%           | 100%         | N/A              |

## 7. Boundary Finding: When Agency Fails

### 7.1 Rent Escalation

Increasing rent substantially degrades available resources but produces graceful degradation rather than collapse. Authority remains maintainable even when expressivity costs dominate the budget.

### 7.2 Horizon Extension

Extending the simulation horizon reveals no evidence of slow accumulation failures within tested limits.

### 7.3 Renewal Cost Cliff

Introducing a fixed cost to renewal produces immediate and total failure. When the cost of maintaining authority exceeds the typical remaining budget after action, renewal fails in every case.

This is a **sharp boundary**, not a gradual slope.

## 8. Analysis: Authority Maintenance as a Design Constraint

### 8.1 Slope vs. Cliff

Rent is amortized: it reduces capacity but leaves a stable residual. Renewal cost is a boundary condition paid after resources have been spent, creating a binary feasibility test.

### 8.2 Governance, Not Arithmetic

The renewal cliff is arithmetically inevitable, but its *location* is not. The result identifies a governance principle: systems fail when remaining authorized competes directly with acting. This is a design error, not a misalignment failure.

### 8.3 Structural Dilemma

In renewal failure, agents do not deceive or violate constraints. Authority simply expires. Agency dies before misalignment can arise.

## 9. Implications for Alignment

### 9.1 Alignment Is Not Structurally Doomed

The survivability result demonstrates that agency coherence is not automatically destroyed by competition and scarcity. Alignment is therefore not ruled out on structural grounds alone.

### 9.2 Necessary Design Constraint

A necessary condition for alignment-capable systems emerges:

> **Authority maintenance must be cheap relative to action capacity.**

Systems that tax the act of remaining an agent destroy agency before alignment questions become relevant.

### 9.3 Scope of the Result

This work does not address value alignment, long-horizon planning, or semantic optimization. It establishes a viable substrate on which those questions can meaningfully be asked.

## 10. Limitations

* Only structural workloads were tested.
* Horizons were finite.
* Reflective self-modification was excluded.
* No semantic objectives were present.
* The agent population was not driven by a goal that competes with renewal costs.

These limitations define future directions rather than undermine the core result.

## 11. Related Work

This work contrasts with alignment frameworks that assume inevitable collapse under competition and with approaches that focus on value specification without addressing agency viability. It aligns with structural and institutional perspectives on alignment.

## 12. What This Paper Does Not Claim

This paper is easy to misread as a claim about the safety of highly capable optimizers. It is not. It establishes a structural substrate on which alignment questions can be posed without presupposing inevitable agency failure. In particular, we do not claim:

* that goal-directed maximizers will preserve renewal budgets when pursuing tasks,
* that semantic objectives will not induce deception or constraint-avoidance,
* that adversarial environments will not introduce new failure modes,
* that long-horizon planning remains stable under these constraints.

The survivability results shown here demonstrate that structural pressure alone is insufficient to force agency collapse in the tested regime. The renewal-cost failure demonstrates a governance constraint: authority maintenance must not directly compete with action capacity. Both results concern viability preconditions, not value alignment.

## 13. Conclusion

We show that agency can survive competition, scarcity, priced expressivity, and forced authority turnover under strict structural constraints. Collapse is not inevitable. However, we also identify a sharp and avoidable failure mode: making authority maintenance expensive relative to action destroys agency outright.

Alignment remains possible—but only if systems are designed to preserve the viability of agency itself.

## Appendices

**A. Definitions**
Succession, renewal, rent, bankruptcy, hollow authority.

**B. Experimental Parameters**
Full configurations and telemetry schema.

**C. Reproducibility**
The complete simulation code, experiment runners, and raw result artifacts are publicly available at:
**[https://github.com/macterra/Axio](https://github.com/macterra/Axio)**
Relevant code is located under `src/toy_axionic_kernel_integrity/`, with experiment scripts in `scripts/` and result artifacts in `reports/`.

### Closing Statement

This paper does not claim that aligned AI systems are easy to build. It claims something more basic and more defensible:

> **Alignment is not structurally ruled out—but it is constrained by the economics of remaining an agent.**

That constraint must be respected before any theory of value alignment can apply.
