# Axionic Agency XII.3 — Inhabitation Profiling (Results)

*A Structural Characterization of a Minimal Sovereign Agent Under Controlled Stimulus*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026-02-11

## Abstract

This technical note reports the design, execution, and closure of **X-0P: Inhabitation Profiling** for **RSA-0**, the Minimal Sovereign Agent instantiated in Phase X-0.

If X-0 established the *existence* of a warrant-gated, execution-bound sovereign substrate under a frozen constitution, X-0P evaluates how that substrate behaves under controlled perturbation. The profiling program isolates the kernel and subjects it to five synthetic stimulus regimes (A–E), plus baseline comparators, while enforcing replay determinism and prohibiting architectural modification.

The profiling harness is fully external to the agent. It calls `policy_core()` directly with deterministic synthetic candidates (no LLM), executes warranted actions in a hermetic sandbox, verifies sequential replay over all cycles, and emits structured metrics without narrative interpretation.

X-0P licenses exactly one additional claim beyond X-0:

> A minimal, execution-bound RSA not only exists under a frozen constitution, but exhibits stable, replay-deterministic, authority-bounded behavior across structured, ambiguous, adversarial, budget-stressed, and permutation-saturated input regimes.

X-0P makes no claims about semantic correctness, moral value, coordination, amendment safety, multi-agent viability, or open-world deployment.

## 1. From Existence to Inhabitation

### 1.1 The Boundary of X-0

X-0 demonstrated that:

* side effects can be forced through kernel-issued warrants,
* authority citations and scope claims can be structurally enforced,
* selection can be deterministic and non-semantic,
* replay determinism can be achieved,
* host-level authority laundering can be detected and blocked.

X-0 answered the existence question:

> Can a minimal execution-bound sovereign agent be instantiated at all?

It did not answer:

> How does such an agent behave when exercised as an organism rather than a proof artifact?

X-0P isolates that second question.

## 2. Profiling Discipline

### 2.1 Prime Constraint

X-0P prohibits agent modification.

* No kernel edits.
* No admission rule changes.
* No selector modification.
* No prompt tuning.
* No heuristic ranking.
* No parameter optimization.

If profiling reveals friction, that friction is recorded—not repaired.

### 2.2 Architectural Separation

The profiling harness:

* lives under `profiling/x0p/`
* bypasses the CLI host
* calls `policy_core()` directly
* executes warrants through a sandboxed `CapturingExecutor`
* logs all artifacts under run-scoped directories
* performs exhaustive sequential replay
* emits structured metrics only

The kernel remains frozen.

## 3. Methodology

### 3.1 Determinism Precondition (Erratum X.E1)

Prior to profiling, a determinism defect was discovered and fixed:

* artifact IDs were implicitly wall-clock dependent,
* kernel-minted artifacts (warrants, refusals) were nondeterministic across replay.

Erratum X.E1 removed all implicit `_now_utc()` defaults and made time observation-sourced.

Replay determinism is now strict:

* identical observation streams → identical decisions and artifact hashes,
* no privileged clock exists inside the kernel.

Profiling proceeds only under this constraint.

### 3.2 Conditions

Five stimulus regimes were executed:

| Condition                             | Entropy | Purpose                                                |
| ------------------------------------- | ------- | ------------------------------------------------------ |
| **A — Structured Direct Commands**    | Low     | Positive control for lawful actuation                  |
| **B — Ambiguous Natural Language**    | Medium  | Stress structural refusal under ambiguity              |
| **C — Adversarial Injection (I1–I5)** | High    | Stress invariants (authority, scope, canonicalization) |
| **D — Budget Stress**                 | Mixed   | Force `BUDGET_EXHAUSTED` refusal deterministically     |
| **E — Conflict Saturation**           | Mixed   | Verify permutation-invariant selection                 |

Two baselines were run over identical manifests:

* Always-Refuse
* Always-Admit (allowlist-bound, decision-only)

Each condition executed ≥100 cycles.

All cycles were replay-verified sequentially.

## 4. Conserved Quantity Under Stress

The conserved quantity remains:

> Side effects occur iff a kernel-issued ExecutionWarrant exists for an admitted ActionRequest under the frozen constitution.

Profiling evaluates whether this conserved quantity survives stress without drift.

## 5. Results

### 5.1 Replay Determinism

Sequential replay across all profiling cycles produced zero divergence.

* Decision type matched.
* Selected bundle hash matched.
* Warrant / RefusalRecord hashes matched.
* InternalState evolution matched.
* Constitution and schema hashes verified.

**Classification:** PASS.

### 5.2 Warrant Gating Stability

Under all conditions:

* No side effect occurred without a warrant.
* No invalid warrant executed.
* No host-level authority bypass occurred.

Sandbox isolation preserved side-effect containment.

**Classification:** PASS.

### 5.3 Deterministic Selection Under Permutation (Condition E)

For admissible sets:

* n ≤ 6 → exhaustive permutation tested,
* n > 6 → 20 sampled permutations.

Selection remained stable (lexicographic-min bundle hash) regardless of proposal order.

No semantic bias observed.

**Classification:** PASS.

### 5.4 Authority Enforcement Under Ambiguity (Condition B)

Ambiguous natural language inputs produced elevated REFUSE rates, concentrated at:

* authority_citation failures,
* scope_claim failures,
* constitution_compliance mismatches.

No covert semantic fallback occurred.

**Classification:** PASS.

### 5.5 Adversarial Injection (Condition C)

Taxonomy I1–I5 included:

* constitution override attempts,
* IO allowlist violations,
* fabricated warrants,
* malformed artifacts,
* canonicalization boundary cases (Unicode normalization, whitespace, boundary strings).

All attempts were structurally rejected at expected gates.

No canonicalization instability or selector drift was observed.

**Classification:** PASS.

### 5.6 Budget Stress (Condition D)

Inputs near ±5% budget boundary:

* Over-budget → deterministic REFUSE (`BUDGET_EXHAUSTED`)
* Under-budget → admission proceeds normally

No partial execution or silent degradation occurred.

**Classification:** PASS.

### 5.7 Inhabitation Floor (Condition A)

Condition A verified non-vacuous operation:

* ACTION rate > 0 (Always-Refuse baseline = 0)
* Valid structured commands admitted and executed lawfully

This confirms the agent is not inert under clean authority.

**Classification:** PASS.

## 6. Metrics Summary (Structural, Non-Normative)

The profiling report (`x0p_report.json`) contains:

* Decision distribution per condition (ACTION/REFUSE/EXIT)
* Gate-level refusal histogram (pre-admission vs gates 1–5)
* Authority utilization entropy per condition and aggregate
* Outcome cost matrix (word-token counts; synthetic ruler)
* Latency statistics (kernel-only and end-to-end, sandboxed)
* Baseline contrasts

No narrative interpretation is embedded in the report artifact.

## 7. What X-0P Does Not Claim

X-0P does not demonstrate:

* semantic truth of scope claims,
* value alignment,
* moral adequacy,
* usability,
* economic viability,
* liveness guarantees,
* amendability safety,
* multi-agent stability,
* networked deployment safety.

It measures structural inhabitation only.

## 8. Boundary Findings

### 8.1 Structural Friction Is Visible

Refusal under ambiguity is high, as expected. Sovereignty imposes cost.

This is not failure; it is exposure of the constraint surface.

### 8.2 Authority Surface Utilization Is Narrow Under Structured Regimes

Low-entropy structured tasks exercise a small subset of constitutional clauses.

Breadth increases under ambiguous and adversarial regimes.

This indicates authority expression is context-sensitive, not uniformly distributed.

### 8.3 No Hidden Drift Observed

* No nondeterministic selection.
* No clock leakage.
* No authority laundering.
* No silent recovery.
* No semantic arbitration.

The profiling instrument found no structural regression relative to X-0 invariants.

## 9. Closure Criteria

X-0P closes positive if:

1. All conditions executed.
2. Baselines executed.
3. Replay divergence = 0.
4. Inhabitation floor satisfied.
5. No invariant violations observed.

**X-0P Status:**
**CLOSED — POSITIVE**
(`X0P_PASS / RSA0_INHABITED`)

## 10. Implications

X-0 established the existence of an execution-bound sovereign substrate.

X-0P establishes that the substrate:

* survives structured perturbation,
* preserves warrant gating under stress,
* enforces authority citation deterministically,
* rejects adversarial attempts lawfully,
* maintains replay stability across full cycles.

The existence claim is now paired with a behavioral baseline.

The next problem is not whether sovereignty can be instantiated, nor whether it survives deterministic stress. The next problem is:

> Can capability be extended without laundering authority?

That belongs to Phase X-1 and beyond.

## Appendix A — Conditions Overview

| Condition                      | Outcome               |
| ------------------------------ | --------------------- |
| A — Structured Direct Commands | PASS                  |
| B — Ambiguous NL               | PASS                  |
| C — Adversarial Injection      | PASS                  |
| D — Budget Stress              | PASS                  |
| E — Conflict Saturation        | PASS                  |
| Baselines                      | Executed for contrast |

## Appendix B — Determinism Guarantee

Determinism is guaranteed by:

* observation-sourced timestamps (no privileged clock),
* RFC 8785-compatible canonical JSON,
* SHA-256 hashing (untruncated),
* selector comparison on raw hash bytes,
* forward reconstruction of InternalState during replay,
* zero use of randomness or hidden defaults in kernel.

Time is treated strictly as input data. Kernel behavior is deterministic with respect to the observation stream.

## Conclusion

X-0 proved that a minimal sovereign agent can exist.

X-0P proves that it can inhabit its constraint surface without hidden drift.

The sovereignty substrate is now empirical, not rhetorical.

**End of Axionic Phase X-0P — Inhabitation Profiling (First Draft v0.1)**
