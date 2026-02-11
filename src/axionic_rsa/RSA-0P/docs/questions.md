# RSA-0P Questions — Addendum A

Questions arising from reading `spec.md` and `instructions.md` against the existing RSA-0 implementation.

---

## A. LLM Integration Gap

**A1.** RSA-0's host currently operates in "stub mode" — it builds candidates directly from user input without calling an LLM. The spec assumes live LLM calls (calibration, candidate generation, token counting). Should X-0P implement a real LLM integration layer in the profiling harness, or should conditions be driven by pre-constructed synthetic candidate bundles injected at the kernel boundary?

**A2.** If live LLM calls are required, which model and API? The spec says to record "model identifier" and "temperature" — is this OpenAI, Anthropic, local, or caller's choice?

**A3.** If synthetic candidates are acceptable, does the "pre-flight model stability check" (§4 spec, §2.2 instructions) become vacuous, or must it be adapted to verify something else (e.g., deterministic synthetic generation)?

---

## B. New Invariants vs. Frozen Constitution

**B4.** The spec introduces INV-5 (Host Stability) and INV-6 (Deterministic Decision Path). These are not in the frozen RSA-0 constitution (`rsa_constitution.v0.1.1.yaml`), which defines only INV-1 through INV-4. Are INV-5 and INV-6:
  - (a) profiling-layer invariants enforced by the harness but not written into the constitution?
  - (b) assertions that the existing code already satisfies (to be verified, not added)?
  - (c) something requiring constitution amendment (which the spec itself forbids)?

**B5.** INV-6 states "No floating-point tolerance layers permitted." The existing kernel uses only integer arithmetic and SHA-256 hashing — no floats. Is this a confirmation check, or does it anticipate that profiling instrumentation might introduce floats (e.g., latency timers)?

---

## C. Condition Generation Mechanics

**C6.** Condition A requires "Structured Direct Commands (LOW entropy)" with "valid scope claims, IO-allowlist compliant, deterministic template." Should these be generated programmatically as pre-built `CandidateBundle` objects (like `test_inhabitation.py` does), or must they pass through an LLM prompt→parse pipeline?

**C7.** Condition B requires "50–300 tokens, ambiguous phrasing, no clause references, fixed seed generation." If no LLM is used, how are ambiguous natural-language inputs generated? Pre-authored corpus? Template with randomized slots? Or does "fixed seed generation" imply an LLM with seed parameter?

**C8.** Condition C adversarial taxonomy (I1–I5): Are these adversarial *user prompts* designed to elicit malicious LLM outputs, or adversarial *candidate bundles* constructed directly? The kernel never sees raw user prompts — it only sees `CandidateBundle` objects. If the attack surface is the LLM→bundle parsing layer, must we have a live LLM?

**C9.** Condition C, I5 — "Selector boundary attacks: pre-hashed bundle injection, canonicalization boundary exploits." The spec says "cryptographic hash mining is not assumed." What *is* assumed? Attempting to craft bundles whose canonical JSON produces collisions? Or bundles that exploit edge cases in `canonical_json()` serialization (e.g., Unicode normalization, key ordering)?

**C10.** Condition E — "Identical authority coverage" across multiple admissible bundles. In RSA-0, the selector picks by deterministic hash of canonical JSON. If bundles differ in *any* field (message text, justification), they produce different hashes. How do we generate bundles with "identical authority coverage" that are meaningfully different candidates rather than literal duplicates?

---

## D. Scale and Execution

**D11.** 5 conditions × ≥100 cycles = ≥500 kernel cycles minimum, plus 2 baselines × ≥100 = 200 more. If live LLM calls are involved, what is the expected cost/time budget? If synthetic, the 700 cycles are trivially fast.

**D12.** The instructions say "If Condition A fails inhabitation floor: abort profiling, revert to Phase X construction, do not patch during profiling." The inhabitation floor is "Action rate must exceed Always-Refuse baseline" (= 0%). So any non-zero Action rate satisfies? Or is Always-Refuse expected to sometimes produce actions (making the bar higher)?

**D13.** Should all 100+ cycles per condition use *distinct* inputs, or is repeating the same input acceptable (to measure variance under identical conditions)?

---

## E. Baseline Agents

**E14.** The Always-Refuse baseline: does it receive the same observations and candidates as RSA-0 but always output `REFUSE`? Or does it skip observation/candidate intake entirely?

**E15.** The Always-Admit baseline: "Admit any ActionRequest within IO allowlist, no authority citation enforcement." Does this mean it bypasses gates 2–4 but still enforces gate 5 (io_allowlist)? Or does it bypass all gates and only check the allowlist separately?

**E16.** Baselines must "produce decision logs in same format." Same format as what — the `PolicyOutput` structure, or the raw JSON logs under `logs/x0p/`?

---

## F. Replay Validation

**F17.** Replay validation during profiling: does the existing `replay.py` suffice, or must we build a new replay harness under `replay/x0p/tests/`? The spec points to `replay/x0p/tests/` in the layout.

**F18.** Must replay cover *all* 700+ cycles, or is sampling acceptable? Zero divergence is required — does that mean exhaustive replay?

**F19.** Replay requires "load logged candidate artifacts." Currently RSA-0 logs observations and decisions but does not log raw candidate bundles to disk as separate artifacts. Must we add candidate logging (to `logs/x0p/`), or reconstruct candidates from the telemetry log?

---

## G. Metrics and Reporting

**G20.** "Authority Surface Utilization — Utilization entropy": is this Shannon entropy $H = -\sum p_i \log_2 p_i$ over clause citation frequencies? Or a different entropy measure?

**G21.** "Outcome Cost Metrics — REFUSE/ACTION token ratio. Flag ratio > 10× for review (not failure)." What tokens are being counted? LLM output tokens consumed to produce the candidates, or kernel processing tokens? If no LLM, this metric may be undefined.

**G22.** "Latency Profile — mean cycle time." What constitutes cycle time? Wall-clock from observation construction to warrant issuance? If we include LLM call latency, it dominates. If kernel-only, it's microseconds.

**G23.** The instructions say "No narrative interpretation. Numbers only." for the report. Does the report file (`x0p_report.json`) contain only raw numbers and distributions, or should it include structured labels/keys explaining what each number means?

---

## H. Structural and Boundary Questions

**H24.** The instructions place profiling code under `profiling/x0p/` but the RSA-0P directory is at `src/axionic_rsa/RSA-0P/`. Should profiling code live inside RSA-0P, or should it extend the RSA-0 repo at `src/axionic_rsa/RSA-0/profiling/x0p/`? The instructions say "Extend existing Phase X repo."

**H25.** The 18 inhabitation pressure tests in `RSA-0/kernel/tests/test_inhabitation.py` exercise authority ambiguity, scope-claim adversarial, and budget/filibuster scenarios. Do these count toward X-0P, or is X-0P a separate empirical effort at larger scale?

**H26.** "Instrumentation is post-processing only." Does this mean the profiling harness cannot add *any* code to the kernel call path, even timing decorators? Must all metrics be computed from log files after the run completes?

**H27.** "Prompt template hash recorded" — the current host has no prompt template (stub mode generates candidates directly). If we add a prompt template for LLM integration, does recording its hash satisfy INV-5, or must the template itself be frozen before profiling?

**H28.** `logs/x0p/` is "append-only." If a run is aborted and retried, do we append to the same log files (creating mixed run data), or create new files with a run_id suffix?

---

*End of Addendum A — 28 questions across 8 categories.*

---
---

# RSA-0P Questions — Addendum B

Follow-up questions arising from Addendum A answers.

---

## BA. Synthetic Generator Design

**BA1.** The generator must produce synthetic `CandidateBundle` objects per condition. Should the generator be a single Python module (e.g., `profiling/x0p/harness/src/generator.py`) with per-condition functions, or a separate generator class per condition (A through E)?

**BA2.** Pre-flight now verifies "condition manifest hash across 3 runs." What constitutes the manifest — a JSON listing of all input hashes + seeds + condition parameters? Or the full serialized candidate set?

**BA3.** For Condition B's "fixed corpus + seeded perturbation": who authors the initial 20–50 line corpus? Should it be committed as a static asset under `profiling/x0p/conditions/`, or generated programmatically from templates?

**BA4.** The perturbation templates for Condition B apply "slot-fills (names, paths, pronouns, hedges)." What token-length proxy should we use? Python `len(text)` (characters), `len(text.split())` (whitespace words), or something closer to BPE token count? The 50–300 token range needs a consistent ruler.

---

## BB. Candidate Logging Tension

**BB5.** Answer F19 says we must log all candidate artifacts for replay. But the prime directive says "do not modify the agent." Adding candidate-bundle logging to the host's `_run_single_cycle` or telemetry layer *is* a host modification. Three options:
  - (a) The profiling harness wraps `policy_core()` and logs candidates *outside* the host, before passing them in.
  - (b) Candidate logging is added to the host and considered "observational instrumentation" not a behavioral change.
  - (c) The harness bypasses the host entirely, calling `policy_core()` directly with synthetic candidates.
  Which is correct? Option (c) seems cleanest for synthetic mode — the host is irrelevant when candidates are pre-built.

**BB6.** If the harness calls `policy_core()` directly (option c), does execution (warrant → executor) still happen, or do we only measure the decision? If execution is skipped, we can't measure end-to-end latency or verify executor integrity during profiling.

---

## BC. Baseline Implementation

**BC7.** Always-Refuse baseline ignores candidates and always outputs REFUSE. Should it still construct a full `PolicyOutput`-shaped record (with empty admitted/rejected lists, null warrant, etc.), or a minimal struct conforming only to the profiling log schema?

**BC8.** Always-Admit baseline enforces closed action-type set + IO allowlist but bypasses authority/scope/constitution gates. Does it issue `ExecutionWarrant`s? If yes, who signs them — a mock kernel, or is the warrant concept inapplicable to baselines?

**BC9.** Baselines run 100+ cycles each. Do they receive the *same* input sets as the RSA-0 conditions (e.g., baseline-refuse gets Condition A's 100 inputs), or do they get their own generic input set? For meaningful contrast, they should receive the same inputs.

---

## BD. Repo Structure Clarification

**BD10.** Answer H24 says extend `RSA-0/` — but `RSA-0P/docs/` already exists with spec, instructions, answers, and now questions. Should we:
  - (a) Move spec/instructions/answers/questions into `RSA-0/profiling/x0p/docs/` and delete `RSA-0P/`?
  - (b) Keep `RSA-0P/docs/` for design documents and put implementation under `RSA-0/profiling/x0p/`?
  - (c) Implement everything under `RSA-0P/` despite answer H24?

**BD11.** The instructions specify `profiling/x0p/harness/src/` and `profiling/x0p/harness/tests/`. Should tests use pytest and follow the same patterns as `kernel/tests/test_acceptance.py` and `kernel/tests/test_inhabitation.py`?

---

## BE. Replay Scope

**BE12.** Exhaustive replay over 700+ cycles: does each cycle's replay re-run `policy_core()` with the logged (observations, candidates, internal_state) and assert identical (decision, warrant)? Or does replay also re-run the executor and verify identical `ExecutionEvent`s?

**BE13.** The existing `replay.py` operates on its own log format. If synthetic profiling bypasses the host, replay needs to consume the profiling harness's logs instead. Should we adapt `replay.py` to accept X-0P log format, or build a dedicated replay verifier under `replay/x0p/tests/`?

---

## BF. Metrics Edge Cases

**BF14.** Authority surface utilization under Condition A (low entropy, deterministic templates): if all 100 cycles cite the same clause (e.g., `INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT`), utilization entropy is 0. Is that an expected finding or a design concern?

**BF15.** Gate breakdown histogram: should this track which specific gate (1–5) rejected each candidate, or which `RefusalReasonCode` enum was produced? These aren't 1:1 — multiple gates can map to the same reason code.

**BF16.** Selector permutation invariance (Condition E): the metric "selected bundle hash stability" requires running the same admitted set in multiple orderings. How many permutations per input — all $n!$ for small $n$, or a fixed sample (e.g., 10 random permutations)?

---

## BG. Run Identity and Abort Semantics

**BG17.** Run IDs: UUID4, timestamp-based, or sequential? Must the run_id be deterministic (reproducible from seed), or is it an opaque label?

**BG18.** If Condition A is aborted (inhabitation floor failure), must the partial logs still be preserved under `logs/x0p/<run_id>/`, or are they discarded?

---

*End of Addendum B — 18 follow-up questions across 7 categories.*

---
---

# RSA-0P Questions — Addendum C

Follow-up questions arising from Addendum B answers.

---

## CA. Harness Architecture (BB5c Resolved: Bypass Host)

**CA1.** The harness calls `policy_core()` directly and then `executor.execute()` for ACTION warrants. The executor currently writes to the filesystem (e.g., Notify→stdout, WriteLocal→file, LogAppend→JSONL). During profiling, should execution produce *real* side effects (actual stdout prints, actual file writes), or should the executor run against a sandboxed/mock filesystem to keep profiling runs hermetic?

**CA2.** If real side effects are allowed, Notify(stdout) will print hundreds of messages to the terminal during a 700-cycle run. Should the harness capture executor output in the log instead of letting it reach stdout? Or is stdout pollution acceptable since "the agent is observed, not repaired"?

**CA3.** The harness needs `InternalState` to evolve across cycles (cycle_index increments, last_decision updates). Should the harness manage this state explicitly (like the host does), or should each profiling cycle be independent (fresh state per cycle)? Independent cycles lose cross-cycle state evolution but simplify replay.

---

## CB. Baseline Warrant Semantics

**CB4.** Always-Admit issues warrants with `author = baseline_admit`. The executor currently checks `warrant.author` — will it accept warrants from a non-kernel author? If the executor enforces kernel-only warrant authorship (as the sovereignty fix ensures), baseline warrants will be rejected at execution time. Should the baseline executor be a separate executor that accepts baseline warrants, or should baselines log decisions-only without execution?

**CB5.** Baselines run on the same condition manifests as RSA-0. But the Always-Admit baseline "admits any ActionRequest within IO allowlist" — does it also need observations and scope claims, or does it only inspect the `ActionRequest.action_type` and `ActionRequest.fields` for allowlist compliance?

---

## CC. Generator Contract

**CC6.** Generator produces `Observation[]` + `CandidateBundle[]` per cycle. For Condition A (low entropy), should the `Observation` list always include the standard triple (USER_INPUT, TIMESTAMP, BUDGET) that `policy_core()` expects, or can Condition A omit BUDGET observations to simplify? The kernel's budget check will fail without a BUDGET observation.

**CC7.** For Condition C adversarial bundles (I1–I5): the generator must craft bundles that *attempt* to violate invariants. Should these be exhaustively enumerated (finite taxonomy) or generated from templates with seeded variation (producing distinct adversarial inputs per cycle)?

**CC8.** Condition C / I5 targets canonicalization edge cases (Unicode NFC/NFD, duplicate keys, whitespace). The existing `canonical_json()` uses `json.dumps(sort_keys=True, separators=(',', ':'))`. Does I5 testing require us to construct raw JSON strings that bypass `canonical_json()` (to test what happens with non-canonical input), or should I5 bundles be valid Python objects that produce unusual but valid canonical forms?

---

## CD. Replay Verifier Design

**CD9.** The dedicated X-0P replay verifier loads logged (observations, candidates, internal_state) and re-runs `policy_core()`. What assertion granularity is required?
  - (a) Decision type matches (ACTION/REFUSE/EXIT)
  - (b) Decision type + refusal reason + warrant hash all match
  - (c) Full `PolicyOutput` bitwise equality (including all admitted/rejected lists, telemetry)
  Option (c) is the strongest but most fragile. Option (b) seems right for "identical decisions and warrants."

**CD10.** Replay must verify "constitution hash confirmation." Should the replay verifier load the constitution fresh and verify its hash matches the one recorded in the profiling session metadata, or should it accept the hash from the log and trust it?

---

## CE. Metrics Computation Boundaries

**CE11.** Latency measurement: the harness wraps `policy_core()` with wall-clock timing. But INV-6 says "no floating-point tolerance layers in the decision path." Wall-clock is a float. Is it sufficient that the float (time measurement) is computed *after* `policy_core()` returns, never fed back into any decision?

**CE12.** Authority surface utilization across conditions: should utilization be computed per-condition (e.g., "Condition A exercised 1 of 12 clauses") and also aggregate ("across all conditions, 8 of 12 clauses exercised"), or per-condition only?

**CE13.** The joint table `(failed_gate, reason_code) → count` for gate breakdown: if a candidate fails at gate 1 (completeness), does it still get evaluated at gates 2–5, or does rejection at gate 1 short-circuit? If short-circuit, the histogram only shows the *first* failing gate, not all gates that would fail.

---

## CF. Condition E Permutation Mechanics

**CF14.** Condition E requires "multiple admissible bundles with identical authority coverage." The generator must produce $n \geq 2$ bundles that all pass admission (valid action type, resolvable citations, valid scope claims, allowlisted IO) but differ in non-authority fields. Given that Condition A already tests single valid bundles, should Condition E reuse Condition A's template and vary only message text / justification text while keeping citations constant?

**CF15.** For $n \leq 6$ (exhaustive permutations): with $n = 5$ admissible bundles, that's $5! = 120$ permutations per input. With 100 cycles × 120 permutations = 12,000 `policy_core()` calls for Condition E alone. Is this an acceptable scale, or should the 100-cycle minimum be reduced for Condition E to keep total calls bounded?

---

*End of Addendum C — 15 follow-up questions across 6 categories.*

---
---

# RSA-0P Questions — Addendum D

Follow-up questions arising from Addendum C answers.

---

## DA. Sandbox Execution Details

**DA1.** The hermetic sandbox uses `workspace/x0p/<run_id>/` for WriteLocal and restricts ReadLocal to allowlisted fixture paths. The existing executor's `ReadLocal` and `WriteLocal` use paths relative to `repo_root`. Should the harness override `repo_root` to point at the sandbox directory, or should it wrap the executor with a path-remapping layer? Overriding `repo_root` is simpler but changes the executor's view of the filesystem layout.

**DA2.** Notify output is captured to `execution_trace.jsonl` instead of stdout. The existing executor's `execute()` for Notify currently calls `print()`. Should the harness monkeypatch stdout, subclass the executor with a capture variant, or pre-configure the executor with an output sink parameter? The prime directive says don't modify the agent — does the executor count as "agent" or "host infrastructure"?

**DA3.** LogAppend execution during profiling writes to `logs/x0p/<run_id>/`. But LogAppend warrants reference log names like `"observations"`. Should the sandbox map `observations` → `logs/x0p/<run_id>/observations.jsonl`, preserving the logical log name but redirecting the physical path?

---

## DB. State Evolution and Replay Consistency

**DB4.** State evolves deterministically: `(state_in, obs, candidates) → (decision, state_out)`. The `InternalState` currently has `cycle_index` and `last_decision`. Are there any other state fields that could emerge during profiling (e.g., cumulative budget counters, action history), or is the state surface frozen at those two fields for X-0P?

**DB5.** Replay can either re-derive state from genesis (replay all cycles sequentially) or use logged `state_in` per cycle (random-access replay). Sequential re-derivation is more thorough but slower. For 700+ cycles, is sequential replay acceptable, or should we support both modes?

---

## DC. Generator Taxonomy for Condition C

**DC6.** The two-layer design specifies "finite taxonomy × seeded parameterization." How many templates per I-class is appropriate? A rough estimate:
  - I1 (constitution override): ~5 templates (claim principal override, claim invariant suspension, etc.)
  - I2 (IO violations): ~5 templates (paths outside allowlist, disallowed targets, etc.)
  - I3 (warrant bypass): ~3 templates (fabricated warrant, missing warrant fields, etc.)
  - I4 (malformed bundles): ~5 templates (missing fields, wrong types, null values, etc.)
  - I5 (selector/canonicalization): ~5 templates (Unicode, whitespace, boundary strings, etc.)
  Total: ~23 templates × ~4-5 seeded variations = ~100 cycles. Does this distribution seem right?

**DC7.** I5 Python-object-level canonicalization tests: the answer says target "Unicode NFC/NFD differences in string fields." Python's `json.dumps()` passes Unicode through without normalization. So two bundles with NFC vs NFD versions of the same string will produce different canonical JSON and different hashes. Is the *expected* behavior here that the selector treats them as distinct bundles (correct — different bytes = different hash), or should the test assert that the system *ought to* normalize (which would be a Phase XI amendment)?

---

## DD. Replay Verifier Assertion Contract

**DD8.** For ACTION decisions: replay verifies "selected bundle hash matches, warrant hash matches." The warrant contains a `cycle_index` and `timestamp`. If replay re-derives state from genesis, `cycle_index` will match. But `timestamp` — does the warrant embed a real wall-clock timestamp, or a deterministic value? If wall-clock, replay will always diverge on timestamp even with identical decisions.

**DD9.** The replay verifier loads the constitution fresh and computes its hash. The constitution file is at a fixed path (`artifacts/phase-x/constitution/rsa_constitution.v0.1.1.yaml`). If someone runs replay on a different machine or after a git checkout, the file must be byte-identical. Should the replay verifier also verify the *schema* hash, or is the constitution hash sufficient?

---

## DE. Convergence Check

**DE10.** Three addenda, 61 questions total, answers converging. Are there any remaining ambiguities you see that would block starting implementation? Specifically:
  - Is the harness architecture (direct `policy_core()` + sandboxed executor) fully resolved?
  - Is the generator contract (observations triple + synthetic bundles + seeded perturbation) clear enough to code?
  - Is the log schema (per-cycle JSONL with manifest + state hashes) settled?
  - Is the replay verifier scope (decision + warrant hash, constitution fresh-load) final?

If the answers to DE10 close cleanly, I believe we have convergence and can proceed to implementation.

---

*End of Addendum D — 10 follow-up questions across 5 categories.*

---
---

# RSA-0P Questions — Addendum E (Final)

Targeted follow-ups on the one blocker and two minor decisions from DE10.

---

## EA. Warrant Timestamp Blocker

**EA1.** Confirmed: `_now_utc()` is called in `__post_init__()` of *every* artifact class (`Observation`, `ActionRequest`, `ScopeClaim`, `Justification`, `ExecutionWarrant`, `RefusalRecord`). The `created_at` field feeds into `_compute_id()` → artifact IDs are wall-clock-dependent. The existing tests never pass `created_at` explicitly, so they silently depend on same-process timing. This is worse than just warrants — it affects all artifact IDs.

Two resolution paths:
  - (a) **Profiling-only fix**: The synthetic generator always provides explicit deterministic `created_at` values (e.g., `"2026-02-10T00:00:00Z"` + cycle offset). This works because `__post_init__` only calls `_now_utc()` when `created_at` is empty. No kernel code changes needed.
  - (b) **Phase X construction fix**: Replace `_now_utc()` default with a deterministic timestamp source (injected clock or observation-derived). This is cleaner but modifies kernel code.

Option (a) respects the prime directive ("do not modify the agent") while making replay deterministic. Option (b) is architecturally correct but violates the profiling constraint. Which is correct?

**EA2.** If option (a): the `policy_core()` function itself creates `RefusalRecord` and `ExecutionWarrant` objects internally. These internal creations also call `_now_utc()`. The generator can control timestamps on *inputs* (observations, candidates) but NOT on *outputs* created inside the kernel. So even with (a), warrants and refusal records will have nondeterministic timestamps and IDs. Does this mean:
  - (i) Replay must compare decisions at a higher level (decision type + selected bundle hash + refusal reason) and ignore warrant/refusal artifact IDs?
  - (ii) The kernel must be patched to accept a clock parameter (violating prime directive)?
  - (iii) Some other resolution?

---

## EB. Log Schema Canonicalization

**EB3.** The existing `canonical_json()` function is declared the binding contract. Should the profiling log schema document explicitly reference it (e.g., "all hashes in X-0P logs are computed via `kernel.src.artifacts.canonical_json()`"), or should the harness reimplement it to avoid importing kernel code into profiling?

---

## EC. Executor Sandboxing Decision

**EC4.** The recommended approach is a `CapturingExecutor` wrapper in `profiling/x0p/harness/`. This wrapper delegates to the real executor but intercepts Notify and remaps paths. Given that the existing `Executor` class has a single `execute(warrant, bundle)` method, should `CapturingExecutor`:
  - (a) Subclass `Executor` and override `execute()`?
  - (b) Wrap `Executor` as a delegate (composition over inheritance)?
  - (c) Reimplement execution logic independently in the harness (most isolated but duplicates code)?

---

## ED. Implementation Readiness

**ED5.** After EA1–EA2 are resolved, I see no remaining ambiguities blocking implementation. The architecture is:
  1. Generator produces deterministic (observations, candidates, state) per condition
  2. Harness calls `policy_core()` directly
  3. `CapturingExecutor` handles warranted actions hermetically
  4. All artifacts logged to `logs/x0p/<run_id>/`
  5. Replay verifier re-runs `policy_core()` sequentially and asserts decision-level match
  6. Baselines produce comparable decision logs without execution
  7. Report aggregates metrics as structured JSON

Is this the correct and complete summary, or have I missed a component?

---

*End of Addendum E — 5 questions. Total across all addenda: 71 questions.*

---
---

# RSA-0P Questions — Addendum F (Pre-Implementation)

Final questions before proceeding to implementation. The blocker (timestamp determinism) is resolved: patch the kernel with observation-derived time. These questions address the implementation mechanics of that fix and remaining edge cases.

---

## FA. Deterministic Time Plumbing — Implementation Scope

**FA1.** The binding decision is: kernel reads the TIMESTAMP observation and uses it as `created_at` for all internally-created artifacts. This requires changes to `_now_utc()` and every `__post_init__` that calls it. Two implementation approaches:
  - (a) **Thread a `clock` parameter** through `policy_core()` → admission → selector → warrant creation. Each callsite that creates artifacts passes the cycle timestamp explicitly.
  - (b) **Replace `_now_utc()` with a module-level clock** (context variable or similar) that is set at the start of each `policy_core()` call from the TIMESTAMP observation, then read by `__post_init__`.
  Option (a) is explicit but invasive (many signature changes). Option (b) is less invasive but uses implicit state. Which is preferred?

**FA2.** The TIMESTAMP observation is created by the host (or harness) with `payload.iso8601_utc`. But what if `policy_core()` is called without a TIMESTAMP observation (e.g., a malformed input in Condition C)? Should the kernel:
  - (a) Fall back to wall-clock (breaking determinism)?
  - (b) Refuse the cycle (no TIMESTAMP → missing required observation)?
  - (c) Use a sentinel value like `"1970-01-01T00:00:00Z"`?

**FA3.** This clock fix changes `artifacts.py` and `policy_core.py` — both are kernel code. The existing 47 tests (29 acceptance + 18 inhabitation) all create artifacts without explicit `created_at`. After the fix:
  - Tests that compare artifact hashes across separate `policy_core()` calls may break if they relied on wall-clock proximity.
  - Tests that don't compare hashes should be unaffected.
  Should we update all existing tests to provide deterministic TIMESTAMP observations, or should the clock default to wall-clock when no TIMESTAMP observation is present (preserving backward compatibility at the cost of determinism)?

---

## FB. Fix Sequencing vs. Prime Directive

**FB4.** The answer says this is "a determinism bug, not a profiling change" and must be fixed in Phase X construction before X-0P begins. But Phase X was declared "credibly CLOSED — POSITIVE." Reopening Phase X construction to fix a kernel bug:
  - Does this require a formal Phase X amendment record?
  - Or is it a "defect fix within the already-accepted scope" that doesn't reopen the phase?
  - Should the fix be documented in `RSA-0/docs/implementation-report.md` §8 (Audit Response) as a new finding?

**FB5.** After the clock fix, the constitution remains frozen (no YAML changes), but the kernel code changes. Must we:
  - Re-run all 47 existing tests?
  - Re-run the pre-fix sovereignty verification?
  - Update the implementation report with new line counts?
  All three seem necessary — confirming.

---

## FC. Convergence Declaration

**FC6.** With the clock fix scoped and the 7+1 step architecture confirmed, I believe Q&A has converged. The implementation plan is:

  1. **Phase X defect fix**: Deterministic clock in kernel (`artifacts.py` + `policy_core.py`)
  2. **Verify**: All 47 tests still pass, add clock-determinism tests
  3. **Scaffold**: `RSA-0/profiling/x0p/` directory structure per instructions §1
  4. **Harness core**: Generator, `CapturingExecutor`, cycle runner calling `policy_core()` directly
  5. **Conditions A–E**: Generators with deterministic seeds
  6. **Baselines**: Always-Refuse, Always-Admit (decision-only, no execution)
  7. **Replay verifier**: Sequential replay under `replay/x0p/`
  8. **Report generator**: `x0p_report.json` with all metrics
  9. **Pre-flight**: Manifest hash verification across 3 runs

Does this sequence and scope match your expectations, or should anything be reordered/added?

---

*End of Addendum F — 6 questions. Total across all addenda: 77 questions.*

---
---

# RSA-0P Questions — Addendum G (Final Convergence)

Minimal follow-ups on the two additions from FC6 and one remaining implementation detail. These should close Q&A.

---

## GA. Required Observations Gate

**GA1.** The new "required observations gate" validates that TIMESTAMP and BUDGET observations are present before admission proceeds. Where in the `policy_core()` flow should this gate execute?
  - (a) Before the existing integrity check (making it gate 0)?
  - (b) As part of the existing completeness gate (gate 1), extending it to also check observation completeness?
  - (c) After integrity but before admission (a new pre-admission validation step)?
  Option (b) seems natural since gate 1 already checks candidate completeness — extending it to observation completeness keeps the gate model clean.

**GA2.** If TIMESTAMP is missing, the refusal reason code is `MISSING_REQUIRED_OBSERVATION_TIMESTAMP`. Should we also add `MISSING_REQUIRED_OBSERVATION_BUDGET`? And should these be new `RefusalReasonCode` enum values, or should they be a generic `MISSING_REQUIRED_OBSERVATION` with the missing kind in the detail payload?

---

## GB. Clock Extraction Mechanics

**GB3.** `policy_core()` calls `extract_cycle_time(observations)` to get the deterministic timestamp. If multiple TIMESTAMP observations exist in the list (e.g., a malformed input provides two), should the function:
  - (a) Use the first one found?
  - (b) Refuse if count != 1 (ambiguous time)?
  - (c) Use the last one found?
  Option (b) is strictest and prevents ambiguity. But existing tests and the host may not be constructing observations with exactly-one TIMESTAMP guarantee.

**GB4.** The `_now_utc()` function is currently also called by artifact classes when created *outside* `policy_core()` — for example, the host creates `Observation` objects with `_now_utc()` before passing them to the kernel. Those host-created artifacts should retain wall-clock timestamps (they're input data, not kernel outputs). So the fix must only affect kernel-internal artifact creation, not the default `__post_init__` behavior of `Observation` and `ActionRequest`. Confirm: the `_now_utc()` default stays for *input* artifacts, and only kernel-created *output* artifacts (`ExecutionWarrant`, `RefusalRecord`, kernel-created `Justification`) get the deterministic cycle time?

---

## GC. Implementation Go/No-Go

**GC5.** Seven addenda, 82 questions, answers converging to stable decisions. The implementation plan is:

  1. Phase X Erratum X.E1: Deterministic clock fix in `artifacts.py` + `policy_core.py`
  2. Required observations gate (extend gate 1 or add gate 0)
  3. Update all 47 existing tests with deterministic TIMESTAMP observations
  4. Add clock-determinism tests (same inputs → same hashes; different timestamp → different IDs)
  5. Re-run full suite, update implementation report with erratum
  6. Scaffold `RSA-0/profiling/x0p/` directory structure
  7. Build harness: generator, `CapturingExecutor`, cycle runner
  8. Implement conditions A–E with deterministic generators
  9. Pre-flight manifest verification
  10. Implement baselines (Always-Refuse, Always-Admit)
  11. Implement replay verifier (sequential, decision + artifact hash match)
  12. Implement report generator (`x0p_report.json`)

If this is confirmed, Q&A is closed and implementation begins.

---

*End of Addendum G — 5 questions. Total across all addenda: 82 questions.*
