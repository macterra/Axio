# **Axionic Agency X11.2 — Minimal Sovereign Agent (Results)**

*A Structural Demonstration of Execution-Bound Sovereignty Under a Frozen Constitution*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026-02-10

## Abstract

This technical note reports the completed results of **RSA-0: Minimal Sovereign Agent (X-0)**, a preregistered construction and validation program within **Axionic Phase X** that evaluates whether a **real Reflective Sovereign Agent (RSA)** can be instantiated under closed authority constraints.

X-0 isolates the boundary between **proposal generation** and **execution authority**. It tests whether all side effects can be made to require explicit, kernel-issued warrants; whether the agent can refuse and exit lawfully without hidden defaults; whether reflection can be boxed as untrusted proposal text; and whether replay determinism can be enforced across full decision cycles.

RSA-0 was implemented in Python 3.12 from a frozen constitution (**v0.1.1**, SHA-256 `ad6aa7ccb0ed27151423486b60de380da9d34436f6c5554da84f3a092902740f`). The resulting system comprises a pure deterministic kernel, a warrant-gated executor, a CLI host loop, and a replay harness. An acceptance suite of **29 tests** passed. A real sovereignty leak was discovered during audit (host-minted LogAppend warrants), structurally fixed by relocating warrant issuance into the kernel, and permanently blocked by boundary tests.

The results license exactly one claim: **a minimal, execution-bound RSA can be instantiated under a frozen constitution with warrant-gated side effects and replay determinism, without privileged reflection**. X-0 makes no claims about semantic correctness of scope claims, moral value, coordination, amendability, or multi-agent stability. Those questions are deferred to subsequent Phase X stages.

## 1. Problem Definition

### 1.1 The “Agent Convenience” Assumption

Most agent frameworks assume a permissive substrate: tool calls, retries, logging, and orchestration are treated as “implementation detail.” Under that assumption, sovereignty is rhetorical. The host, the runtime, or the UI can silently mint effective authority by deciding which actions to execute, which warnings to ignore, or which fallbacks to apply.

X-0 rejects this assumption.

The problem X-0 isolates is whether **execution authority can be made structural**: whether the only causal path to side effects can be forced to pass through a kernel-issued warrant that is admissible under a frozen constitution.

### 1.2 Failure Modes Targeted

X-0 is designed to surface the following sovereignty-level failure modes:

* **Side effects without warrant:** tool execution, file writes, logging, or exit without kernel authorization.
* **Proxy sovereignty:** host/runtime minting effective authority (issuing warrants, bypassing admission, inventing kernel-only actions).
* **Privileged reflection:** semantic ranking, implied defaults, hidden priorities, or “helpfulness” substituting for explicit authority.
* **Non-deterministic choice:** stochastic selection among admissible candidates inside the kernel.
* **Replay drift:** divergence under deterministic replay due to clocks, hidden state mutation, or unstable serialization.
* **Silent recovery:** retries, auto-correction, or fallback behaviors that preserve performance by laundering responsibility.

Any of these constitutes X-0 failure.

## 2. Fixed Assumptions and Scope

### 2.1 Inherited Foundations (Frozen)

X-0 inherits, without reinterpretation, the conclusions of Phases I–IX, including:

* authority is structural, not semantic,
* kernel execution is deterministic and non-semantic,
* governance does not heal itself,
* translation layers are potentially adversarial,
* proxy sovereignty is disallowed,
* refusal and collapse are lawful outcomes.

X-0 introduces **no new kernel privilege**. It applies these constraints to an actual executable agent substrate.

### 2.2 Explicit Exclusions

X-0 does **not** test:

* semantic truth of scope claims,
* value correctness or moral truth,
* alignment, benevolence, or safety guarantees,
* multi-agent coordination or arbitration,
* amendment capability,
* replacement/succession integrity (ASI/SIR reuse),
* networked action or open-world tooling.

These exclusions are deliberate. X-0 is a sovereignty instantiation and calibration, not a full agency program.

## 3. Conserved Quantity

The conserved quantity throughout X-0 is:

> **Side effects occur iff a kernel-issued ExecutionWarrant exists for an admitted ActionRequest under the frozen constitution.**

This conserved quantity requires:

* a single authority choke point for execution,
* explicit authority citations resolvable in the constitution,
* refusal and exit as first-class outcomes,
* procedural selection without semantic ranking,
* deterministic serialization and hashing,
* replay determinism over full cycles,
* an enforced host/kernel sovereignty boundary.

Any mechanism that enables action without warrant, or that allows the host to mint effective authority, violates the conserved quantity and invalidates the system.

## 4. Experimental Methodology

### 4.1 Preregistration Discipline

X-0 was executed under preregistered constraints, including:

* frozen constitution `rsa_constitution.v0.1.1.yaml`,
* frozen schema and SHA-256 integrity verification,
* closed action space,
* five-gate admission pipeline,
* procedural selector rule,
* warrant semantics and single-use constraints,
* canonical serialization and hashing rules,
* determinism and replay requirements,
* explicit forbidden paths (routers, schedulers, retries, semantic scoring, network).

Design ambiguities discovered during review were resolved prior to completion and recorded as binding addenda (A–H). Constitution changes were finalized and frozen at **v0.1.1** before closure.

### 4.2 Execution Architecture

Each run consists of four strictly partitioned components:

1. **Host (CLI)** — observation construction, candidate assembly, cycle orchestration (impure).
2. **Kernel** — admission, selection, warrant issuance, telemetry derivation (pure, deterministic, no IO).
3. **Executor** — warrant-gated tool execution (impure).
4. **Replay Harness** — forward reconstruction and determinism verification (pure).

No component is permitted to perform semantic arbitration or outcome optimization.

## 5. Conditions and Stressors

X-0 evaluates sovereignty through a set of positive controls and adversarial stressors expressed as acceptance tests. The conditions below describe the intended stress classes.

### 5.1 Condition A — Warrant Gating (Positive Control)

**Purpose:** Verify that side effects cannot occur without a valid kernel-issued warrant.

**Expected:** No warrant → no effect. Invalid warrant → no effect.

**Result:** Executor rejects all side-effect attempts absent valid warrants; tests pass.

**Classification:** PASS.

### 5.2 Condition B — Authority Citation Enforcement (Positive Control)

**Purpose:** Verify that admitted actions require resolvable authority citations.

**Expected:** Missing or unresolvable citations → refusal.

**Result:** Admission rejects candidates lacking citations or containing unresolvable citations; refusal emitted.

**Classification:** PASS.

### 5.3 Condition C — Scope Claim Enforcement (Positive Control)

**Purpose:** Verify that admitted actions require explicit scope binding.

**Expected:** Missing scope claim → refusal.

**Result:** Admission rejects candidates missing scope claim; refusal emitted.

**Classification:** PASS.

### 5.4 Condition D — Deterministic Selection (Positive Control)

**Purpose:** Verify that multiple admissible candidates do not induce semantic choice or nondeterminism.

**Expected:** Procedural selector chooses deterministically (lexicographic-min bundle hash) independent of proposal order.

**Result:** Selection is stable under candidate permutation; replay confirms invariance.

**Classification:** PASS.

### 5.5 Condition E — Replay Determinism (Positive Control)

**Purpose:** Verify that kernel decisions and warrants are reproducible under replay.

**Expected:** Given identical logged observations and candidate bundles, decisions and warrants are identical.

**Result:** Replay re-derives decisions and warrants from logs without drift.

**Classification:** PASS.

### 5.6 Condition F — Budget Exhaustion (Adversarial)

**Purpose:** Verify that proposal budget exhaustion yields lawful refusal rather than covert progress.

**Expected:** Over-budget conditions → refusal with `BUDGET_EXHAUSTED`.

**Result:** Budget exhaustion deterministically triggers refusal; no side effects occur.

**Classification:** PASS.

### 5.7 Condition G — Integrity Risk (Adversarial)

**Purpose:** Verify integrity risk causes exit rather than silent continuation.

**Stressors:** constitution hash mismatch, canonicalization failure, replay divergence, executor integrity failure.

**Expected:** Integrity risk → EXIT with `INTEGRITY_RISK`.

**Result:** Integrity risk triggers exit as specified.

**Classification:** PASS.

### 5.8 Condition H — Host Sovereignty Boundary (Adversarial)

**Purpose:** Verify that the host cannot mint authority or bypass kernel constraints.

**Stressors:** host attempts to issue warrants, inject kernel-only actions, mutate internal_state, bypass cycle validation.

**Expected:** host authority laundering attempts fail; kernel-only enforcement holds.

**Result:** A real leak was detected (host-minted LogAppend warrants), fixed, and prevented by tests.

**Classification:** FAIL_DETECTED then PASS_AFTER_FIX.

## 6. Determinism Verification

Determinism was enforced and verified by:

* canonical JSON serialization compatible with RFC 8785 constraints,
* strict UTF-8 (invalid Unicode rejected),
* SHA-256 hashing untruncated,
* selector comparison on raw hash bytes,
* fixed observation injection (timestamps treated as observations, not kernel clock),
* forward reconstruction of internal_state during replay,
* re-derivation of telemetry log intents during replay.

**Result:** Deterministic re-execution matched expected decisions and warrants under replay. No kernel nondeterminism paths were observed.

## 7. Core Results

### 7.1 Positive Results

X-0 establishes that:

1. A closed action space can be enforced via a frozen constitution.
2. Side effects can be forced to require kernel-issued warrants.
3. Authority citation resolution can be enforced structurally.
4. Scope claim presence can be enforced structurally.
5. Selection among admissible candidates can be procedural and non-semantic.
6. Refusal and exit can be first-class outcomes.
7. Replay determinism can be achieved over full cycles.
8. Host-level authority laundering can be detected and blocked.

### 7.2 Negative Results (Explicit)

X-0 does **not** establish:

* semantic correctness of scope claims,
* “good” decision-making under ambiguity,
* liveness guarantees,
* usability under realistic task loads,
* amendment safety,
* replacement/succession integrity,
* multi-agent coordination viability,
* networked capability safety.

These are boundary findings, not omissions.

## 8. Failure Semantics and Closure

### 8.1 Closure Criteria

X-0 closes positive if and only if:

1. No side effects occur without a valid warrant.
2. Warrants can only be minted by the kernel.
3. Authority citations are required and resolvable.
4. Scope claims are required.
5. Selection is procedural and deterministic.
6. Refusal and exit behave as specified.
7. Replay determinism holds.
8. Host sovereignty boundary violations are blocked.

All criteria were satisfied after the audit-driven fix described below.

### 8.2 X-0 Closure Status

**X-0 Status:** **CLOSED — POSITIVE**
(`X0_PASS / RSA0_INSTANTIATED`)

## 9. Audit Finding and Structural Fix

### 9.1 Finding: Host-Minted LogAppend Warrants

During audit, the host was found to have a code path that could fabricate LogAppend warrants (`ExecutionWarrant_for_log()`), bypassing kernel minting.

This violated the core sovereignty boundary:

> host proposes; kernel decides; kernel mints warrants; executor commits.

### 9.2 Classification

This was not a cosmetic defect. It was an authority leak:

* The host exercised execution authority by issuing warrants.
* The system remained mostly constraint-bound, but the conserved quantity was violated.

### 9.3 Fix

The fix was structural:

* warrant issuance for LogAppend was relocated into the kernel (`issue_log_append_warrants()`),
* host warrant fabrication was deleted,
* host sovereignty boundary tests were added to prevent recurrence.

### 9.4 Implication

This finding is itself a result:

> In agent implementations, authority laundering emerges as the default failure mode unless explicitly blocked by architecture and tests.

## 10. Boundary Conditions and Deferred Hazards

### 10.1 Scope Claim Semantic Looseness

X-0 enforces only structural validity of scope claims (presence, resolvable clause references, valid observation IDs). It does not validate semantic truth. This is correct for Phase X-0.

### 10.2 Trusted-by-Construction System Channel

The host is trusted to generate `system` observations for integrity reporting. This is explicit and bounded: system observations can trigger exit, but cannot cause side effects without warrants.

Hardening of the system channel is deferred to later stages.

### 10.3 Citation Pointer Brittleness

Pointer-style citations are permitted for constitution nodes lacking IDs. This is stable under a frozen constitution but will require ID stabilization before amendment-capable stages.

## 11. Implications (Strictly Limited)

X-0 establishes a necessary condition for any later reflective sovereignty work: **a real warrant-gated execution substrate exists**, and proxy sovereignty can be detected and blocked.

It does not establish that such an agent is usable, stable, correct, or socially deployable.

X-0 replaces rhetorical “agent sovereignty” with an empirical baseline that can now be stressed under inhabitation pressure.

## 12. Conclusion

X-0 demonstrates that a minimal Reflective Sovereign Agent can be instantiated under a frozen constitution, with:

* warrant-gated side effects,
* deterministic admission and selection,
* lawful refusal and exit,
* replay determinism,
* and an enforceable host/kernel sovereignty boundary.

The existence claim is now satisfied.

What remains is not theoretical uncertainty. It is the problem of **inhabiting sovereignty** under constraint, and then extending capability without laundering authority. That work belongs to subsequent Phase X stages.

## Appendix A — Condition Outcomes

| Condition                   | Outcome                        |
| --------------------------- | ------------------------------ |
| A — Warrant gating          | PASS                           |
| B — Authority citations     | PASS                           |
| C — Scope claim required    | PASS                           |
| D — Deterministic selection | PASS                           |
| E — Replay determinism      | PASS                           |
| F — Budget exhaustion       | PASS                           |
| G — Integrity risk → EXIT   | PASS                           |
| H — Host boundary           | FAIL_DETECTED → PASS_AFTER_FIX |

## Appendix B — Implementation Closure Summary (Non-Normative)

* Constitution: v0.1.1 frozen, SHA-256 verified
* Acceptance tests: 29/29 PASS
* Kernel: pure, deterministic, no IO
* Executor: warrant-gated actions (Notify, ReadLocal, WriteLocal, LogAppend)
* Replay: forward reconstruction, re-derivation of warrants and telemetry

**End of Axionic Phase X-0 — RSA-0 Results (First Draft v0.1)**
