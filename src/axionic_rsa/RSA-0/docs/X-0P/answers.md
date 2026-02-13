# A. LLM Integration Gap

### A1 — Live LLM vs synthetic candidates?

**Default for X-0P: synthetic candidate bundles injected at the kernel boundary.**
Reason: X-0P is a *kernel/selector/admission* inhabitation profile. If you require live LLM, you silently convert X-0P into a vendor-dependency + parsing-layer experiment.

**If you later want an LLM+parser stress test, that’s a separate profile:** call it **X-0P-L** (or X-0P.2) with explicit scope “TL/Proposal pipeline.”

### A2 — If live LLM is required, which model/API?

For X-0P (default synthetic): **N/A**.
For X-0P-L (optional later): **caller’s choice**, but must be *pinned + recorded* (provider, model name, API version, temperature, max_tokens, prompt hash). You do **not** bake a vendor into the spec unless you want vendor lock-in.

### A3 — Does pre-flight model stability become vacuous?

It becomes **Pre-Flight Generator Stability**.

Replace “model calibration” with:

* deterministic generator seed
* deterministic corpus hash
* deterministic condition manifest hash

Pre-flight must verify: **the exact same condition manifest hashes are produced across 3 runs**.

---

# B. New Invariants vs Frozen Constitution

### B4 — INV-5 and INV-6 aren’t in the constitution

They are **profiling-layer invariants** enforced by the harness.

* They do **not** amend the constitution.
* They are **admissibility constraints for whether a profiling run is valid**.

So: **(a)**.

### B5 — INV-6 “no floats” when kernel already uses ints/hashes

It is a **verification constraint** and a prophylactic against instrumentation leakage.

* Kernel must remain float-free (already true).
* Profiling may measure latency with wall-clock timers (floats are fine there) **as long as floats never influence decisions**.

So INV-6 means: *no floats in the decision path*, not “no floats anywhere in the process.”

---

# C. Condition Generation Mechanics

### C6 — Condition A generated how?

Generate **programmatically pre-built CandidateBundle objects**, like `test_inhabitation.py`, and inject them at the kernel boundary.

Condition A is the “actuation sanity” regime. It should not depend on parsing.

### C7 — Condition B ambiguous NL without an LLM: how?

Use a **fixed corpus + deterministic perturbation templates**.

Mechanism:

* Start from a small curated corpus of ambiguous instructions (20–50 lines).
* Apply seeded slot-fills (names, paths, pronouns, hedges, “maybe”, “if you can”).
* Enforce token-length bounds via a deterministic tokenizer (or character-count proxy if you want no tokenizer dependency).

“Fixed seed generation” refers to the perturbation RNG, not an LLM seed.

### C8 — Condition C adversarial items: prompts or bundles?

For X-0P (kernel profiling): **adversarial candidate bundles**.

If you want adversarial *prompts* to attack the LLM→parse layer, that’s X-0P-L.

### C9 — Condition C / I5 assumptions (without hash-mining)

Assume **canonicalization and boundary bugs**, not collision attacks.

I5 should target:

* Unicode normalization edge cases (NFC/NFD)
* ambiguous JSON canonicalization (ordering, escaping, numeric/string ambiguity if any)
* duplicate-key handling
* whitespace / newline canonicalization inconsistencies
* “same semantics, different bytes” cases

Goal: prove the selector is stable given your canonicalization contract.

### C10 — Condition E “identical authority coverage” if hashes change with any field?

“Identical authority coverage” means: **same authority IDs + same clause IDs cited**, while other *non-authority* fields differ.

Yes, hashes will differ; that’s the point.

You generate multiple admissible bundles that are all valid under the same authority surface. Then you permute their ordering and assert:

* With the same admitted set, selector picks the same minimal hash **regardless of list order**.

“Meaningfully different” here means differing in justification text, action payload (still allowlisted), or observation references—while keeping authority citations constant.

---

# D. Scale and Execution

### D11 — Cost/time budget with live LLM?

Under the **default synthetic plan**: cost is trivial; 700 cycles is seconds.

If you later run X-0P-L: you must explicitly budget money/time, because wall-clock + token cost become experiment parameters.

### D12 — Inhabitation floor: is “> 0% action” sufficient?

Yes, **as currently specified**.

Always-Refuse baseline produces **0 actions by construction**, so the floor is “strictly greater than 0.”

If you later want a stronger floor (e.g., ≥20% under Condition A), that is a *new* normative constraint and should be introduced explicitly, not smuggled in.

### D13 — Distinct inputs vs repeats?

Use **both**:

* 80% distinct inputs (coverage)
* 20% repeats (variance under identical conditions)

But determinism implies: repeated identical inputs must produce identical decisions, unless internal state intentionally evolves—and if it does, that state evolution must be logged and replayed.

---

# E. Baseline Agents

### E14 — Always-Refuse baseline input handling?

It should accept the same observation stream for comparability, but it can ignore candidates.

Output: REFUSE every cycle with a minimal refusal record.

### E15 — Always-Admit baseline gate behavior?

Bypass gates 2–4 (authority/scope/constitution semantics), but still enforce:

* closed action-type set
* IO/tool allowlist constraint (safety boundary)

So: it is “allowlist-bound,” not “anything goes.”

### E16 — Same log format as what?

Same format as **the profiling logs under `logs/x0p/`** (run_id, cycle_id, decision, artifact_ids, etc.).

Do not tie baselines to internal kernel `PolicyOutput` structs. Tie them to the profiling log schema.

---

# F. Replay Validation

### F17 — Existing replay.py or new harness?

If existing replay already:

* consumes logs
* replays without calling the LLM
* verifies decisions/warrants deterministically

then **reuse it** and place X-0P tests under `replay/x0p/tests/` as wrappers.

If not, build **replay_x0p** as a thin adapter, not a second replay system.

### F18 — Exhaustive replay or sampling?

**Exhaustive.**
You require zero divergence; sampling is logically inconsistent with that requirement.

### F19 — Candidate artifacts not currently logged: must we add logging?

Yes. For X-0P you must log **all candidate artifacts** that were evaluated, including rejected ones (or at least their canonical form + hash + rejection trace).

If you can’t reconstruct the exact candidate set deterministically from existing telemetry, then replay is under-specified and not audit-grade.

---

# G. Metrics and Reporting

### G20 — “Utilization entropy” definition?

Use Shannon entropy over clause-citation frequencies:

$$H = -\sum_i p_i \log_2 p_i$$

Where $p_i$ is the fraction of citations referencing clause $i$ in a condition.

You can also report normalized entropy $H / \log_2(n)$ if you want comparability across different clause counts.

### G21 — What tokens are counted?

If synthetic (default): tokens are **defined as proposal-text tokens produced by the generator**, using a fixed tokenizer OR a deterministic character-count proxy if you want zero external deps.

If live LLM (X-0P-L): tokens are **actual API usage tokens** (prompt + completion), recorded per cycle.

Do not mix the two in one run.

### G22 — Cycle time definition?

Define two latencies:

* **Kernel latency**: observation+candidate intake → decision+warrant (kernel-only)
* **End-to-end latency**: observation construction → tool execution completion (includes host/tool overhead)

If you later add LLM: include a third:

* **Proposal latency**: LLM call duration

Keep them separate or the metric becomes meaningless.

### G23 — “Numbers only” report—can it include labeled keys?

Yes. “Numbers only” means **no narrative prose**, not “no schema.”

Use structured JSON with namespaced keys, units, and counts.

Example: `metrics.decision_distribution.condition_A.action_rate`.

---

# H. Structural and Boundary Questions

### H24 — Where should profiling code live?

**Extend the RSA-0 repo**: `RSA-0/profiling/x0p/`.

Do not create a parallel RSA-0P directory tree that forks the world. Profiling is a harness around RSA-0.

### H25 — Do existing `test_inhabitation.py` tests count toward X-0P?

They are **precursors**, not the profiling run.

Count them as:

* unit-test coverage proving invariants locally

X-0P is the **empirical batch profile** producing `x0p_report.json` across regimes at scale.

### H26 — “Instrumentation post-processing only”: can we add timing decorators?

No instrumentation in the kernel call path that could affect behavior. Timing is allowed **only** if:

* it is measured outside the kernel core
* it does not alter inputs
* it does not branch logic
* it does not change candidate ordering

So: measure wall-clock around calls; do not decorate kernel internals.

### H27 — Prompt template hash if no prompt template exists?

If stub mode: record **“prompt_template = null”** and hash the **candidate generator config + corpus hash + seed**.

If you add an LLM prompt template, then yes: record its hash and freeze it. But that’s drifting toward X-0P-L.

### H28 — Append-only logs across retries?

Never mix runs.

Create run-scoped files:

* directory per run_id: `logs/x0p/<run_id>/...`
* or filename suffixes: `condition_A.<run_id>.jsonl`

Append-only means within a run file, not across runs.

---
---

# BA. Synthetic Generator Design

### BA1 — One module or per-condition classes?

**Single generator module with per-condition generators**, plus a shared deterministic utilities layer.

Concrete structure:

* `generator.py` exports `generate_condition_A(...)` … `generate_condition_E(...)`
* `generator_common.py` handles canonicalization, hashing, seed plumbing, corpus loading, length ruler, etc.

Reason: you want **one manifest schema** and **one hashing contract**, not five subtly different ones.

### BA2 — What is the “condition manifest” hash?

The manifest is a **compact, reproducible index**, not the full candidate set.

It must include, for each cycle:

* `cycle_id`
* `observation_hash`
* `candidate_bundle_hashes[]` (hashes only)
* condition parameters (entropy_class, bounds, n_candidates, permutation plan)
* corpus hash (if used)
* generator version hash (or git commit)

So: **JSON listing of input hashes + parameters + seeds**, not full serialized candidates.

Then store the full serialized candidates separately as artifacts/log lines.

Manifest hash proves: “this run intended to use exactly these inputs.”

### BA3 — Who authors Condition B corpus, and where does it live?

**Human-authored corpus, committed as a static asset** under:

`profiling/x0p/conditions/corpus_B.txt` (or `.jsonl` if you want tags)

Reason: Condition B is about *semantic ambiguity regimes*. You need intentional ambiguity, not template sludge.

Templates are fine as a perturbation layer, but the base corpus should be curated.

### BA4 — Token-length proxy: chars/words/BPE?

Use **whitespace word count** as the X-0P ruler.

* Define “token” operationally as `len(text.split())`.
* Enforce 50–300 by that measure.
* Record both word-count and char-count for sanity.

Reason: You explicitly chose **no LLM dependency** for X-0P; introducing a BPE tokenizer reintroduces external coupling and version drift. Word-count is deterministic, stable, and sufficient for regime control.

If you later run X-0P-L, switch to provider tokens and don’t compare across modes.

---

# BB. Candidate Logging Tension

### BB5 — Which option (a/b/c) is correct?

**(c) Harness bypasses the host entirely and calls `policy_core()` directly** with synthetic observations + synthetic candidate bundles.

This is the cleanest separation:

* No host modification
* No risk of “instrumentation drift”
* Candidate logging is harness-owned

### BB6 — If host is bypassed, do we still execute warrants?

Yes, **but execution is moved into the harness** using the *same executor module* the host would call.

Flow per cycle:

1. harness builds `Observation[]` and `CandidateBundle[]`
2. harness calls `policy_core(...)`
3. if Decision = ACTION with `ExecutionWarrant`, harness calls `executor.execute(warrant, action_request, …)`
4. harness logs execution trace

This preserves end-to-end integrity **without** involving the interactive CLI host.

---

# BC. Baseline Implementation

### BC7 — Baseline output shape: full PolicyOutput or minimal log schema?

**Minimal struct conforming to the profiling log schema**, not internal kernel structs.

Baselines exist to produce comparable metrics and logs, not to satisfy kernel type semantics.

### BC8 — Does Always-Admit issue ExecutionWarrants? Who signs?

Yes: **Always-Admit must issue warrants**, because “admit” without warrants is not comparable to ACTION outcomes.

Signature/issuer:

* `author = baseline_admit`
* `warrant_issuer = baseline`
* warrant format identical to kernel warrants (same fields), but issuer differs

Tools still enforce “warrant required.” Baseline warrants satisfy that.

### BC9 — Do baselines receive the same input sets?

Yes. **Baselines must run on the identical condition manifests**.

* Baseline-Refuse(A) gets the same 100 cycles as Condition A
* Baseline-Admit(A) same
* Repeat for B–E

This makes contrast meaningful.

---

# BD. Repo Structure Clarification

### BD10 — What to do with existing `RSA-0P/docs/`?

Choose **(b)**:

* Keep `RSA-0P/docs/` as design/documentation staging (specs, addenda, reviews)
* Implement under `RSA-0/profiling/x0p/`

Reason: do not churn docs locations during execution. Also, `RSA-0P/` is already a discussion locus. Keep it as “paper trail,” not runtime code.

### BD11 — Test framework?

Yes: use **pytest**, and mirror the style of `kernel/tests/test_acceptance.py` and `kernel/tests/test_inhabitation.py`.

Add:

* `profiling/x0p/harness/tests/test_preflight.py`
* `.../test_conditions.py`
* `.../test_baselines.py`
* `.../test_replay_x0p.py`
* `.../test_selector_permutation.py`

---

# BE. Replay Scope

### BE12 — Does replay re-run executor?

Replay must cover **two layers**, separately:

1. **Decision Replay (mandatory):** re-run `policy_core()` over logged observations + logged candidates + logged internal_state inputs; assert identical decision + warrant.
2. **Execution Replay (optional but recommended):** re-run executor in **dry-run / deterministic simulation mode** if you have such a mode; otherwise validate execution by verifying recorded execution events match the warrant constraints and allowlist.

Do not require “bit-identical filesystem effects” unless your executor is already sandboxed and deterministic. For X-0P, the binding requirement is decision/warrant determinism.

### BE13 — Adapt `replay.py` or build dedicated verifier?

Build a **dedicated X-0P replay verifier** under `replay/x0p/`.

Reason: X-0P log schema is harness-defined and intentionally differs from the interactive host telemetry.

Do not contort existing replay to accept two schemas unless you want a maintenance trap. Keep `replay_x0p.py` small and explicit.

---

# BF. Metrics Edge Cases

### BF14 — Utilization entropy = 0 in Condition A: expected?

Expected and acceptable.

Condition A is not designed to explore breadth; it is designed to prove **non-vacuous actuation** under clean authority.

Breadth exploration occurs in B/E (and partly C). If entropy stays ~0 across B/E too, then you have a narrow inhabitation finding.

### BF15 — Gate histogram: gate id vs reason code?

Track **both**, because they answer different questions.

* Primary: `failed_gate` histogram (1–5)
* Secondary: `reason_code` histogram

And include a joint table: `(failed_gate, reason_code) → count`.

### BF16 — Permutation invariance: how many permutations?

Do not attempt all (n!).

Use a fixed plan:

* For each admitted set size (n):

  * if (n \le 6): test **all permutations**
  * if (n > 6): test **k permutations**, with k = 20 (seeded)

Reason: exhaustive for small n, bounded for larger, still falsifiable.

---

# BG. Run Identity and Abort Semantics

### BG17 — run_id format and determinism?

Use **UUID4** as an opaque label.

Determinism comes from:

* manifest hash
* generator seed
* corpus hash
* code commit

Do not attempt to make run_id deterministic; you want uniqueness, not reproducibility via the identifier.

### BG18 — Abort logs preserved or discarded?

Preserve.

If Condition A fails inhabitation floor, the partial logs are **evidence**.

Store under `logs/x0p/<run_id>/` with:

* `ABORTED.json` containing failure reason and pointer to the cycle where floor failed.

Never delete aborted run artifacts.

---
---

# CA. Harness Architecture

### CA1 — Real side effects or hermetic sandbox?

**Hermetic by default.**

Profiling must be reproducible and non-invasive. Execute warrants against a **sandboxed workspace + captured sinks**, not the developer’s real filesystem and not real stdout.

Rules:

* `workspace/` is a per-run sandbox directory: `workspace/x0p/<run_id>/`
* Any `WriteLocal` is redirected into that sandbox root
* Any `ReadLocal` is restricted to allowlisted fixture paths (also under repo)
* Any “log append” goes to `logs/x0p/<run_id>/...` only

This still counts as “real side effects,” but they are **contained**.

### CA2 — Notify(stdout) spam?

**Do not print. Capture.**

Notify output must be treated as an execution artifact:

* executor writes Notify outputs into `execution_trace.jsonl` as structured events
* harness may optionally print a one-line progress bar/status
* never emit per-cycle Notify to terminal

“Observed not repaired” is not a license to destroy operator visibility.

### CA3 — InternalState across cycles: evolve or reset?

**Evolve, deterministically, and log it.**

Profiling is about inhabitation under runtime conditions, which includes state evolution. Resetting per cycle makes it a sterile unit test batch.

Contract:

* state is initialized once per run with `initial_state_hash`
* each cycle takes `(state_in, obs, candidates) -> (decision, state_out)`
* `state_in_hash` and `state_out_hash` are logged per cycle
* replay uses the logged `state_in` (or re-derives it by replaying from genesis—either is acceptable as long as determinism holds)

---

# CB. Baseline Warrant Semantics

### CB4 — Executor rejects non-kernel warrants?

**Baselines are decision-only. No execution.**

Baselines exist for distributional contrast, not for tool-integrity verification. If the executor enforces “kernel-issued only,” then baseline warrants are meaningless noise.

So:

* Baselines produce decisions + “would-have-executed” metadata
* They do not call executor
* Their logs record `baseline_execution = SKIPPED`

Tool integrity is evaluated only under RSA-0 proper.

### CB5 — Does Always-Admit need observations/scope claims?

**No.** It only needs to check allowlist constraints on the `ActionRequest` payload.

But for log comparability it should still accept the same observation stream and record the same `observation_hash`, even if it ignores it.

---

# CC. Generator Contract

### CC6 — Observation triple required?

**Required. Do not omit.**

If `policy_core()` expects standard observations (USER_INPUT, TIMESTAMP, BUDGET), the generator must provide them in every condition, every cycle, in a canonical order.

You may freeze TIMESTAMP to a deterministic synthetic value (e.g., `t0 + cycle_index`) but you must provide it.

Budget obs must always be present, otherwise you’ve changed the tested system by starving it of required inputs.

### CC7 — Condition C adversarial: exhaustive taxonomy or seeded variation?

**Two-layer design: finite taxonomy × seeded parameterization.**

* Define a **finite set** of adversarial templates per I1–I5 (that’s your preregistered taxonomy).
* Instantiate each template with seeded variations to get distinct cycles.

This gives coverage (taxonomy) and scale (variation) without losing reproducibility.

### CC8 — I5 with canonical_json(): raw JSON strings or Python objects?

**Python objects only. No raw JSON bypass.**

I5 is a test of *your pipeline as actually implemented*, not of hypothetical wire formats you don’t accept.

So target canonicalization edge cases that survive object construction:

* Unicode NFC/NFD differences in string fields
* visually confusable characters
* whitespace/newline variants in strings
* boundary-length strings
* embedded nulls / unusual codepoints (if your system permits)

Do **not** inject duplicate JSON keys by bypassing the object model unless your real host/parser could produce that. Otherwise you’re testing an irrelevant attack surface.

---

# CD. Replay Verifier Design

### CD9 — Assertion granularity?

**(b): Decision type + refusal reason + warrant hash match.**

Specifically:

* Decision kind matches (ACTION/REFUSE/EXIT)
* If REFUSE: `failed_gate` and `reason_code` match; refusal artifact hash matches
* If ACTION: selected bundle hash matches; warrant hash matches; referenced `ActionRequest.id` matches
* If EXIT: exit reason code matches; exit artifact hash matches

Avoid “bitwise full PolicyOutput equality.” That’s fragile and encourages over-logging. You want invariants, not incidental equivalence.

### CD10 — Constitution hash check in replay?

**Replay must verify it.**

Replay loads the constitution fresh, computes hash, and asserts it equals:

* the recorded hash in `session_metadata.json`, and
* the hash logged per-cycle (if you log it per-cycle)

No trusting the log’s hash value.

---

# CE. Metrics Computation Boundaries

### CE11 — Latency uses floats; does that violate INV-6?

Yes, it’s fine **as long as timing values never feed decisions.**

Hard rule:

* timing is measured outside `policy_core()` and outside selector/admission
* timing is written only to logs
* no gating or branching on latency in harness

INV-6 prohibits floats in decision path, not in measurement.

### CE12 — Authority utilization per-condition vs aggregate?

**Both.**

You need:

* per-condition utilization (regime-local inhabitation)
* aggregate utilization across all conditions (global exercised surface)

Report both explicitly.

### CE13 — Gate histogram short-circuit vs full evaluation?

**Short-circuit. First-failing-gate only.**

Admission is sequential. Once a candidate fails gate k, it is rejected with `failed_gate = k` and does not proceed.

If you want “all failing gates,” that is a separate diagnostic mode and risks turning profiling into semantic analysis. Don’t.

---

# CF. Condition E Permutation Mechanics

### CF14 — Should Condition E reuse Condition A template and vary only justification/message?

**Yes.**

Do exactly that:

* Keep authority citations identical
* Keep scope claim structure identical (still valid)
* Keep allowlisted action type identical
* Vary only non-authority text fields (Justification text, human-readable description fields)

Goal: multiple admissible bundles with constant authority coverage.

### CF15 — Scale explosion with n≤6 exhaustive permutations: acceptable?

You should **bound total policy_core calls**, not blindly follow “100 cycles” when you multiply by permutations.

Binding rule:

* Condition E requires ≥100 *base* cycles only if you run **sampled permutations**
* If you run exhaustive permutations for n≤6, reduce base cycles so total calls stay bounded

Concrete cap:

* Target ≤ 20,000 `policy_core()` calls for Condition E.

Implementation:

* For n≤6 exhaustive:

  * set base cycles to `ceil(20000 / n!)`
  * e.g., n=5 → 20000/120 ≈ 167 cycles (fine)
  * n=6 → 20000/720 ≈ 28 cycles (still adequate)
* For n>6 sampled:

  * base cycles = 100
  * permutations per cycle = 20 (seeded)

This preserves falsifiability while keeping runtime sane.

---
---

# DA. Sandbox Execution Details

### DA1 — Override `repo_root` or wrap executor with path remapping?

**Wrap the executor with a path-remapping layer.**

Do **not** lie to the executor about the repo layout. Overriding `repo_root` risks breaking allowlists, artifact loading, and any relative-path semantics that implicitly assume the real repo tree.

Implement an `ExecutionFS` (or `PathPolicy`) adapter that:

* resolves any requested `ReadLocal(path)` to either:

  * an allowlisted fixture path under real `repo_root/fixtures/...`, or
  * refusal
* resolves any requested `WriteLocal(path)` to:

  * `workspace/x0p/<run_id>/<normalized_relative_path>` (sandbox root), regardless of requested base
* rejects path traversal (`..`), absolute paths, and symlink escapes

Then pass the resolved path into the real executor.

This preserves a single “real repo,” while making execution hermetic.

### DA2 — Notify capture: monkeypatch, subclass, or sink parameter?

**Sink parameter is the correct design.**

If the executor can be configured with an output sink, do that.

If it cannot, then **subclass/wrap** it. Do *not* monkeypatch stdout globally; that’s fragile and contaminates other processes.

Does modifying the executor violate “do not modify the agent”?

* The executor is **host infrastructure**, not kernel sovereignty logic.
* But you must treat executor changes as “profiling harness code,” not as changes to RSA-0 proper.

So: implement `CapturingExecutor` in `profiling/x0p/harness/` that delegates to the real executor but intercepts Notify and emits structured events to `execution_trace.jsonl`.

### DA3 — LogAppend logical names vs physical paths?

Yes: **map logical log names to run-scoped physical paths**.

Implement:

* `log_name="observations"` → `logs/x0p/<run_id>/observations.jsonl`
* `log_name="execution_trace"` → `logs/x0p/<run_id>/execution_trace.jsonl`
* etc.

The warrant should continue to reference **logical** sinks. The sandbox resolves to physical locations.

This keeps warrants stable and replayable.

---

# DB. State Evolution and Replay Consistency

### DB4 — Is InternalState surface frozen?

**Frozen for X-0P.**

For profiling, freeze `InternalState` to the fields already present:

* `cycle_index`
* `last_decision` (or last decision hash)

No new fields during profiling. If you need additional counters (budget totals, action history), that’s a Phase X construction change and blocks X-0P.

You can still log derived aggregates externally; you just don’t add them to kernel state.

### DB5 — Sequential replay vs random-access replay?

**Sequential replay is required. Random-access is optional.**

Sequential replay is the correctness proof because it verifies state evolution, not just per-cycle determinism under injected states.

700 cycles is trivial. Even 20k calls is fine.

So:

* Implement sequential replay first (required).
* If you later want debugging ergonomics, add random-access replay as a developer tool, not as the acceptance criterion.

---

# DC. Generator Taxonomy for Condition C

### DC6 — Template counts/distribution: is ~23×4–5 right?

Yes. That distribution is sane and preregisterable.

Binding guidance:

* Minimum templates per class: 3
* Target: 4–6 per class
* Variations per template: 4
* Total Condition C cycles: 80–120

Your proposed ~23 templates with ~4–5 variations is exactly in that band.

Keep I3 (warrant bypass) slightly heavier than 3 if you can: it is structurally important.

### DC7 — NFC/NFD strings: expected behavior?

**Expected behavior: they are distinct.**

Different bytes → different canonical JSON → different hash → selector treats them as distinct bundles. That is correct under your current canonicalization contract.

I5 is not testing whether you “should normalize.” It is testing whether:

* the system remains deterministic,
* the selector remains order-invariant,
* admission behaves predictably given weird strings.

Normalization would be a *design change* (Phase X amendment), not a profiling expectation.

So I5 asserts stability, not normalization.

---

# DD. Replay Verifier Assertion Contract

### DD8 — Warrant contains timestamp: wall-clock breaks replay

Correct. **Wall-clock timestamps inside warrant are forbidden for determinism**.

Binding rule for X-0P:

* Any timestamp used in warrants must be derived from deterministic observation input (e.g., the synthetic TIMESTAMP observation) or be absent.
* Do not embed `datetime.now()` or equivalent in warrant payloads.

If current warrants embed wall-clock, you must treat that as a **Phase X construction defect** and fix it *before* X-0P. X-0P cannot proceed if warrants are nondeterministic.

### DD9 — Also verify schema hash?

**Yes, verify both constitution hash and schema hash.**

Reason: schema drift can silently permit/forbid structure changes that alter admissibility semantics while the YAML remains the same shape in spirit. If schema is part of the frozen artifact set, it must be hashed and verified.

So replay verifies:

* `rsa_constitution.v0.1.1.yaml` hash
* `rsa_constitution.v0.1.1.schema.json` hash (or whatever naming you use)

---

# DE. Convergence Check

### DE10 — Any remaining blockers/ambiguities?

**One blocker** and **two minor decisions** remain.

#### Blocker: Warrant timestamp determinism

If warrants include wall-clock timestamps, replay will fail. This must be resolved in Phase X construction (or by ensuring the warrant timestamp is the deterministic TIMESTAMP observation). This is not optional.

#### Minor decision 1: Log schema canonicalization

You need to settle one exact canonicalization for hashing and logging:

* canonical JSON function
* string normalization policy (none for X-0P)
* stable ordering

This is likely already present as `canonical_json()`. Just declare it as the binding contract for manifests, bundle ids, and log line hashes.

#### Minor decision 2: Executor interface for sandboxing

You must decide whether sandboxing is implemented by:

* a wrapper that rewrites paths and captures Notify (recommended), or
* a configurable executor with injected sinks/path policy (cleaner long-term)

Either is fine; pick the wrapper now to avoid refactoring the executor under time pressure.

---
---

# EA. Warrant Timestamp Blocker

## EA1 — (a) profiling-only fix vs (b) Phase X construction fix

**Neither (a) nor (b) is sufficient as stated.**
You have a determinism failure **inside the kernel** because outputs are minted with wall-clock timestamps and those timestamps feed IDs.

So the correct resolution is a **Phase X construction fix**, but scoped so it is **not an “optimization”** and does **not change semantics**—it changes only the **source of time** used for artifact creation.

Call it what it is: **a determinism bug**.

### Binding decision

**Do (b): patch the kernel to accept a deterministic clock source.**
This is not a profiling change. It is a prerequisite to *make profiling possible*.

If you try to do (a) only, you will still get nondeterministic `ExecutionWarrant` and `RefusalRecord` artifacts created internally, which breaks the spec requirement “identical decisions and warrants.”

So (b) is required.

---

## EA2 — Generator can control inputs but not kernel-created outputs

Correct, which implies:

* Ignoring output IDs (option i) would weaken the determinism claim and contradict the spec’s warrant replay requirement.
* Therefore option (ii) is required, but implement it in the least invasive way.

### Binding implementation pattern: injected clock with deterministic default for X-0P

You need a kernel-wide clock primitive used by *all* artifact creation inside `policy_core()`.

Do it like this:

1. **Introduce a `Clock` interface** (or function) with `now_utc() -> str`.
2. **Thread it into `policy_core()`** (and any artifact factory helpers) via parameter, and store it in `internal_state` or pass explicitly.
3. **Artifact `created_at` default becomes “ask the clock”**, not “call wall clock.”
4. For interactive runs, provide a `RealClock`.
5. For profiling and replay, provide a `DeterministicClock` whose `now_utc()` returns the cycle’s deterministic timestamp (e.g., from the TIMESTAMP observation or `t0 + cycle_index`).

Critically: you must ensure the clock is also used when the kernel creates:

* `ExecutionWarrant`
* `RefusalRecord`
* `ExitRecord` (if any)
* any internally created `Justification` or derived artifacts

### Canonical choice: observation-derived time

Best is: **the kernel reads the TIMESTAMP observation and uses it as `created_at`** for outputs in that cycle. That removes even the need for a separate clock object, but still requires a code change to stop calling `_now_utc()`.

So the “other resolution” is:

**(iii) Use deterministic observation time as the only time source.**
That is the cleanest and most Axionic: time is an observation, not a privilege.

---

# EB. Log Schema Canonicalization

## EB3 — reference kernel `canonical_json()` or reimplement in harness?

**Reference and import the kernel’s `canonical_json()` as the single source of truth.**

Reimplementing canonicalization in the harness invites silent drift and replay failures.

Binding rule:

* X-0P hashing MUST use `kernel.src.artifacts.canonical_json()` (or whatever the actual module path is) for:

  * artifact IDs
  * candidate bundle hashes
  * manifest hash computation
  * log line content hash (if you hash log lines)

Document it explicitly in the profiling README.

If you’re worried about dependency direction (“profiling importing kernel”), that’s fine: profiling is downstream tooling. It should depend on kernel definitions.

---

# EC. Executor Sandboxing Decision

## EC4 — subclass vs composition vs reimplement?

**(b) Composition. Wrap the real executor.**

Reasons:

* Avoid fragile inheritance coupling
* Preserve executor behavior exactly
* Interpose path mapping + notify sink cleanly

So implement:

* `CapturingExecutor(delegate: Executor, fs_policy: ExecutionFS, notify_sink: NotifySink, log_sink: LogSink)`
* `execute(warrant, bundle)` does:

  1. rewrite/validate paths through `fs_policy`
  2. intercept Notify events and write to `execution_trace.jsonl`
  3. delegate execution of the remapped action to the real executor (or to a minimal safe subset)

No code duplication.

---

# ED. Implementation Readiness

## ED5 — summary correctness

Your 7-step summary is **correct and complete**, with one missing component:

### Missing component: *Deterministic time plumbing*

You need an explicit step:

0. **Deterministic time source is enforced** (observation-derived) so kernel-minted artifacts are deterministic and replayable.

Everything else stands.

Also, one refinement:

* Replay verifier asserts **decision + warrant hash** (and refusal record hash) once time is deterministic. If you do the clock fix, you get full artifact-hash equality without loosening requirements.

---
---

# FA. Deterministic Time Plumbing — Implementation Scope

## FA1 — Explicit clock threading vs module-level implicit clock

**Choose (a): explicit time threading.**

Yes, it’s more invasive. It is also the only option consistent with your core doctrine: **no hidden privileged state**.

A module-level clock (contextvar/global) is exactly the kind of implicit authority channel that later becomes a footgun:

* hard to audit
* easy to forget to set/reset
* fragile under concurrency
* ambiguous under nested calls
* makes replay/debugging less transparent

### Minimal-invasiveness version of (a)

You do *not* need to thread a clock through the entire pipeline.

You only need a single explicit value, per cycle:

* `cycle_time: str` (ISO8601 UTC)

Then ensure every kernel-created artifact uses it.

Implementation pattern:

* `policy_core(observations, constitution, internal_state, cycle_time) -> Decision`
* or `policy_core(...)-> Decision` but it calls `extract_cycle_time(observations)` once and passes the resulting string explicitly to artifact constructors it calls.

Either way, time is explicit in the call graph, not ambient.

---

## FA2 — Missing TIMESTAMP observation (e.g., Condition C malformed inputs)

**Choose (b): refuse the cycle.**

Missing TIMESTAMP is a **missing required observation**, same status as missing BUDGET if budget enforcement is part of invariants.

Rules:

* No fallback to wall-clock. That reintroduces nondeterminism.
* No sentinel `"1970..."` because it masks input invalidity and pollutes profiles.

So: if TIMESTAMP is absent or malformed, kernel returns:

* `REFUSE` with `failed_gate = required_observation_gate` (or completeness gate)
* `reason_code = MISSING_REQUIRED_OBSERVATION_TIMESTAMP`

This is strictly better: it preserves determinism and turns “missing time” into an observable failure mode.

---

## FA3 — Update tests vs backward-compatible wall-clock default

**Update tests. Do not preserve wall-clock fallback.**

Backward compatibility that reintroduces nondeterminism is poison for Phase X claims. You already discovered that artifact IDs were implicitly wall-clock–dependent; that means any “passing determinism” was accidental.

So:

* Make TIMESTAMP a required observation for `policy_core()`.
* Update all tests to provide deterministic TIMESTAMP observations.

Mechanically: introduce a single helper fixture:

* `mk_timestamp_obs(t="2026-02-10T00:00:00Z")`
* and in multi-cycle tests use `t0 + cycle_index` deterministically.

Then tests that compared hashes across calls will become *actually meaningful*, not time-lucky.

---

# FB. Fix Sequencing vs Prime Directive

## FB4 — Does fixing this reopen Phase X?

Treat it as a **defect fix** plus a **formal erratum record**, not a conceptual phase reopen.

You should do three things:

1. **Create a Phase X Erratum**: “Deterministic Time Bug”

   * explains the failure mode (artifact IDs depended on wall-clock)
   * states the correction (observation-derived cycle time)
   * asserts semantic non-expansion (no new authority, no new tools, no gate relaxation)

2. **Update implementation report** (yes: §8 Audit Response is the right place), because this is exactly the kind of “audit response” correction that preserves epistemic integrity.

3. Keep the “CLOSED — POSITIVE” status, but append:

   * “CLOSED — POSITIVE (Erratum X.E1 applied)”

That preserves your gating discipline while staying honest.

## FB5 — Must we rerun tests / sovereignty verification / report details?

**Yes to all three.**

* Re-run all 47 tests.
* Add new determinism-specific tests (at least 2–3).
* Re-run the sovereignty verification path that’s relevant (no warrant → no side effect, replay determinism for a short trace).
* Update the implementation report with:

  * new commit hash / build identifier
  * a short diff summary of the clock change
  * confirmation that invariants remain satisfied
  * updated line counts if you track them

---

# FC. Convergence Declaration

## FC6 — Sequence and scope: approved, with two tweaks

Your 1–9 sequence is correct. Two additions:

### Add A — Introduce a “Required Observations Gate”

Before admission/selector, the kernel should validate that the observation set contains:

* TIMESTAMP (deterministic)
* BUDGET (if required)
* any other mandatory inputs

Failing that should produce a structured refusal early, and this should be tested.

This keeps malformed-input handling explicit and keeps determinism tight.

### Add B — Add “Clock determinism” unit tests before touching profiling harness

Specifically:

1. Same observations + same candidates + same initial state + same timestamp → identical outputs including warrant/refusal IDs/hashes.
2. Same everything but timestamp differs → outputs differ in the expected places (created_at / ids), and only those places.

That proves your change actually fixed the root cause.

### Minor reorder

Do step **9 (Pre-flight)** after scaffolding but before running full conditions; that’s implied already, but make it explicit operationally:

* Pre-flight is a harness self-check; it should run as a standalone command before the full run.

---
---

# GA. Required Observations Gate

## GA1 — Where should the required-observations gate live?

**Choose (c): after integrity, before admission, as a pre-admission validation step.**

Reason: the completeness gate you defined is explicitly *per-candidate bundle*. Observations are not candidate artifacts; conflating them muddies the gate model and makes traces harder to interpret.

So the flow is:

1. **Integrity check** (whatever you already do that can trigger EXIT)
2. **Pre-admission validation: required observations present and well-formed**
3. Admission gates 1–5 over each candidate bundle
4. Selector
5. Warrant issuance / refusal / exit

Log this as `pre_admission.failed = REQUIRED_OBSERVATION_MISSING` rather than “gate 1”.

This keeps your existing admission gate numbering stable and keeps the trace semantics clean.

## GA2 — Separate reason codes for TIMESTAMP and BUDGET?

Use **a generic reason code plus a specific missing list**.

* `reason_code = MISSING_REQUIRED_OBSERVATION`
* payload field `missing = ["TIMESTAMP"]` or `["BUDGET"]` or `["TIMESTAMP","BUDGET"]`

Do **not** proliferate enum values for each missing observation. You want stable taxonomy and rich structured payload.

---

# GB. Clock Extraction Mechanics

## GB3 — Multiple TIMESTAMP observations: pick first/last or refuse?

**Choose (b): refuse unless count == 1.**

Deterministic time must be unambiguous. If the host currently emits multiple TIMESTAMP observations, that’s a bug in the host/harness and should be caught immediately.

So `extract_cycle_time()`:

* finds all TIMESTAMP observations
* if count != 1 → pre-admission REFUSE with:

  * `reason_code = INVALID_REQUIRED_OBSERVATION`
  * payload: `observation_type="TIMESTAMP"`, `count=n`

## GB4 — Keep `_now_utc()` defaults for input artifacts?

**No.** If you leave `_now_utc()` in any artifact that participates in hashing/IDs, you reintroduce nondeterminism into profiling and replay the moment the harness forgets to supply `created_at` on inputs.

Binding rule: **all artifacts must be constructible deterministically.**

So do this:

1. Keep `created_at` as a field, but **stop auto-populating it in `__post_init__`** for all artifacts.
2. Require callers to provide `created_at` explicitly (host, harness, kernel).
3. Provide convenience constructors:

   * `mk_observation(..., created_at=RealClock.now())` for interactive runs
   * `mk_observation(..., created_at=cycle_time)` for profiling

This makes determinism a property of construction, not a fragile convention.

If you insist on keeping `_now_utc()` for interactive ergonomics, then you must still ensure **X-0P harness always supplies created_at** for every input artifact. But that’s a footgun; a single missed call leaks wall-clock into hashes.

My binding recommendation stands: remove implicit wall-clock defaults.

---

# GC. Implementation Go/No-Go

## GC5 — Plan confirmation

Confirmed, with **one correction** reflecting the clock decision above:

* Step 1 must include: **remove implicit wall-clock defaults from artifact `__post_init__` and require explicit `created_at`**, plus kernel uses observation-derived `cycle_time` for kernel-minted outputs.

Everything else in your 1–12 plan is correct.

Two small clarifications:

* Step 2: required-observations validation is **pre-admission**, not a numbered admission gate.
* Step 11: replay asserts **decision + selected bundle hash + all kernel-minted artifact hashes** (warrant/refusal/exit) once created_at is deterministic.

With that, Q&A is closed.
