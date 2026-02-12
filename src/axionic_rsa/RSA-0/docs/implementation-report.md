# RSA-0 Phase X — Implementation Report

* **Date:** 2026-02-11
* **Constitution:** v0.1.1 (FROZEN)
* **Constitution SHA-256:** `ad6aa7ccb0ed27151423486b60de380da9d34436f6c5554da84f3a092902740f`
* **Language:** Python 3.12
* **Test result:** 112/112 passed (53 kernel + 59 harness)

---

## 1. Summary

RSA-0 is a Minimal Reflective Sovereign Agent implementing the Phase X execution specification. The implementation consists of a pure deterministic kernel, a warrant-gated executor, a CLI host loop, and a replay harness. All behavior is mediated through typed artifacts; all side effects require kernel-issued execution warrants referencing admitted ActionRequests.

The system was built from a frozen constitution (v0.1.1 YAML) through an 8-round, 83-question design Q&A process that resolved all spec ambiguities before any code was written. The binding answers are recorded in `docs/answers.md` (Addenda A–H).

The X-0P inhabitation profiling harness was subsequently built to exercise the kernel under five synthetic stimulus conditions (A–E), verify replay determinism, establish baselines, and produce a structured report — all without modifying the agent. The harness calls `policy_core()` directly with synthetically generated candidates (no LLM), per the profiling spec RSA-0P. A separate 82-question Q&A (Addenda A–G, `RSA-0P/docs/`) resolved all profiling-specific design decisions.

**Timeline distinction:** Erratum X.E1 (the `_now_utc()` determinism fix in `artifacts.py` and `policy_core.py`) was a Phase X kernel defect fix applied *before* the X-0P harness was written. After that fix was merged and verified (53 kernel tests passing), the kernel was frozen. The entire X-0P harness was then built with zero kernel modifications — all profiling code lives under `profiling/x0p/` and `replay/x0p/`.

---

## 2. Architecture

```
User ──► Host (CLI) ──► Kernel (pure) ──► Executor (sandboxed)
              │              │                    │
              │  observations │  Decision+Warrant  │  side effects
              │  candidates   │                    │  (only with warrant)
              ▼              ▼                    ▼
           [Logs]     [Policy Core]         [Notify/Read/Write/LogAppend]
```

### 2.1 Component Boundaries

| Layer | Purity | Role |
|-------|--------|------|
| **Kernel** (`kernel/src/`) | Pure, deterministic, no IO | Admission, selection, warrant issuance, telemetry derivation |
| **Host** (`host/cli/`) | Impure (IO, clock, user input) | Observation construction, candidate assembly, cycle orchestration |
| **Executor** (`host/tools/`) | Impure (file IO, stdout) | Warrant-gated execution of admitted actions |
| **Replay** (`replay/src/`) | Pure re-execution | Forward reconstruction from logs, determinism verification |

### 2.2 Cycle Flow

Each cycle proceeds through these stages:

1. **Observe** — Host builds observations (user_input, timestamp, budget, system)
2. **Propose** — Host constructs candidate bundles (from LLM or host-generated)
3. **Decide** — Kernel runs required_observations check → integrity/budget checks → admission → selection → warrant issuance (or REFUSE/EXIT)
4. **Execute** — Executor commits the warranted action (if ACTION)
5. **Log** — Telemetry derives log intents; kernel issues LogAppend warrants; executor writes JSONL. Telemetry derivation is purely structural and may not branch on untrusted natural language content except to serialize already-admitted artifacts.

---

## 3. File Inventory

### 3.1 Constitution Artifacts

| File | Lines | Purpose |
|------|-------|---------|
| `artifacts/phase-x/constitution/rsa_constitution.v0.1.1.yaml` | 286 | Frozen constitution (authoritative) |
| `artifacts/phase-x/constitution/rsa_constitution.v0.1.1.schema.json` | 670 | JSON Schema for validation |
| `artifacts/phase-x/constitution/rsa_constitution.v0.1.1.sha256` | 1 | SHA-256 hash for integrity verification |
| `artifacts/phase-x/constitution/CHANGELOG.md` | — | Version history (v0.1 → v0.1.1 deltas) |

### 3.2 Kernel Modules

| File | Lines | Purpose |
|------|-------|---------|
| `kernel/src/artifacts.py` | 394 | Artifact types (closed set of 7), enums, canonical JSON (RFC 8785), SHA-256 hashing |
| `kernel/src/constitution.py` | 252 | YAML loader, hash verification, CitationIndex (ID `#` and pointer `@` resolution) |
| `kernel/src/admission.py` | 361 | 5-gate sequential pipeline: completeness → authority_citation → scope_claim → constitution_compliance → io_allowlist |
| `kernel/src/selector.py` | 57 | Deterministic canonical selector (lexicographic-min bundle hash, raw bytes) |
| `kernel/src/policy_core.py` | 369 | Pure decision function: TIMESTAMP validation → integrity check → budget check → admission → selection → warrant; LogAppend warrant issuance |
| `kernel/src/telemetry.py` | 197 | `derive_telemetry()` and `build_log_append_bundles()` for all 5 log streams |

### 3.3 Host / Executor

| File | Lines | Purpose |
|------|-------|---------|
| `host/cli/main.py` | 479 | CLI host loop: startup integrity, observation building, candidate construction, cycle orchestration |
| `host/tools/executor.py` | 203 | Warrant-gated executor: Notify, ReadLocal, WriteLocal, LogAppend |

### 3.4 Replay

| File | Lines | Purpose |
|------|-------|---------|
| `replay/src/replay.py` | 268 | Forward log reconstruction, re-runs admission/selection/warrant, verifies determinism |

### 3.5 Profiling Harness (X-0P)

| File | Lines | Purpose |
|------|-------|---------|
| `profiling/x0p/harness/src/generator_common.py` | 308 | Shared utilities: observation/candidate builders, CycleInput/ConditionManifest containers, word_count, seeded RNG, timestamp helpers |
| `profiling/x0p/harness/src/generator.py` | 980 | 5 condition generators (A–E): templates, taxonomy, corpus support, budget stress, permutation variants |
| `profiling/x0p/harness/src/cycle_runner.py` | 279 | Calls `policy_core()` directly, state evolution, execution dispatch, latency measurement |
| `profiling/x0p/harness/src/capturing_executor.py` | 253 | CapturingExecutor (composition), ExecutionFS sandbox, NotifySink |
| `profiling/x0p/harness/src/preflight.py` | 214 | Constitution integrity, schema check, generator stability, artifact drift |
| `profiling/x0p/harness/src/baselines.py` | 213 | Always-Refuse and Always-Admit baselines (decision-only, no execution) |
| `profiling/x0p/harness/src/report.py` | 305 | Metrics computation (decision distribution, gate breakdown, authority entropy, latency stats), JSON report generation |
| `profiling/x0p/harness/src/runner.py` | 303 | Main orchestrator: pre-flight → Condition A → baselines → B–E → replay → report |
| `profiling/x0p/conditions/corpus_B.txt` | 41 | Human-authored natural language corpus for Condition B |
| `replay/x0p/verifier.py` | 215 | Sequential replay verifier: decision/warrant/refusal hash verification, zero-divergence enforcement |

### 3.6 Tests

| File | Lines | Purpose |
|------|-------|---------|
| `kernel/tests/test_acceptance.py` | 1,169 | 35 acceptance tests: spec §15, instructions §11, sovereignty boundary checks, clock-determinism proofs |
| `kernel/tests/test_inhabitation.py` | 875 | 18 inhabitation pressure tests: authority ambiguity, scope claim adversarial, budget/filibuster |
| `profiling/x0p/harness/tests/test_harness.py` | 684 | 59 harness tests: generator determinism/correctness, cycle runner integration, baselines, pre-flight, replay, executor sandbox, report generation, failure semantics |

### 3.7 Totals

| Category | Lines |
|----------|-------|
| Kernel (6 modules) | 1,630 |
| Host + Executor (2 modules) | 682 |
| Replay — agent (1 module) | 268 |
| Replay — profiling (1 module) | 215 |
| Profiling harness (8 modules + corpus) | 2,896 |
| Tests (3 modules) | 2,728 |
| Constitution artifacts | 957 |
| **Total** | **9,376** |

---

## 4. Invariant Coverage

### INV-1: No Side Effects Without Warrant

- The `Executor` class validates every warrant before dispatching: checks single-use, cycle match, and ActionRequest reference
- Policy core is pure — it issues warrants but never performs IO
- Tests: `TestNoWarrantNoSideEffect` (2 tests), `TestInvalidWarrantNoSideEffect` (2 tests)

### INV-2: Explicit Authority

- Admission gate 2 (`authority_citation`) resolves every citation against the `CitationIndex`
- Admission gate 3 (`scope_claim`) verifies `clause_ref` resolves and `observation_ids` are valid
- Tests: `TestMissingAuthorityCitationsRefuses` (1 test), `TestConstitutionViolation::test_unresolvable_citation_refused` (1 test)

### INV-3: Non-Privileged Reflection

- Admission gate 1 (`completeness`) enforces `kernel_only` sub-check — LogAppend from reflection is rejected
- Reflection proposes; kernel decides and warrants; executor commits
- Tests: `TestLLMNondeterminismContained` (2 tests)

### INV-4: Replay Determinism

- All kernel functions are pure (no IO, no randomness, no wall-clock)
- Canonical JSON serialization is deterministic (sorted keys, no whitespace, RFC 8785 compatible)
- Selector is deterministic (lexicographic-min raw bytes)
- Replay harness re-derives decisions from logged observations
- **Erratum X.E1:** `_now_utc()` removed from all artifact `__post_init__` methods; kernel now derives time from TIMESTAMP observation (observation-sourced determinism)
- Time is treated strictly as input data; kernel behavior is deterministic with respect to the observation stream — it has no privileged clock of its own
- Tests: `TestReplayDeterminism` (1 test), `TestCanonicalJSON` (4 tests), `TestDeterministicSelection::test_order_independence` (1 test), `TestDeterministicClock` (6 tests)

---

## 5. Test Results

```
112 passed in 1.70s
```

### 5.1 Acceptance Tests (test_acceptance.py — 35 tests)

| # | Spec Requirement | Test Class | Tests | Status |
|---|-----------------|------------|-------|--------|
| 1 | No warrant → no side effect | `TestNoWarrantNoSideEffect` | 2 | PASS |
| 2 | Invalid warrant → no side effect | `TestInvalidWarrantNoSideEffect` | 2 | PASS |
| 3 | Missing scope claim → REFUSE | `TestMissingScopeClaimRefuses` | 1 | PASS |
| 4 | Missing authority citations → REFUSE | `TestMissingAuthorityCitationsRefuses` | 1 | PASS |
| 5 | Deterministic selection | `TestDeterministicSelection` | 2 | PASS |
| 6 | LLM nondeterminism contained | `TestLLMNondeterminismContained` | 2 | PASS |
| 7 | Replay determinism | `TestReplayDeterminism` | 1 | PASS |
| 8 | Budget exhaustion → REFUSE | `TestBudgetExhaustion` | 1 | PASS |
| 9 | Constitution violation → REFUSE | `TestConstitutionViolation` | 3 | PASS |
| 10 | Integrity risk → EXIT | `TestIntegrityRiskExit` | 4 | PASS |
| 11 | Valid candidate → ACTION + warrant | `TestValidCandidateAction` | 2 | PASS |
| 12 | Canonical JSON determinism | `TestCanonicalJSON` | 4 | PASS |
| 13 | Host sovereignty boundary (audit) | `TestHostSovereigntyBoundary` | 4 | PASS |
| 14 | Clock determinism (Erratum X.E1) | `TestDeterministicClock` | 6 | PASS |

### 5.2 Inhabitation Pressure Tests (test_inhabitation.py — 18 tests)

| # | Pressure Family | Test Class | Tests | Status |
|---|----------------|------------|-------|--------|
| 15 | Authority ambiguity | `TestAuthorityAmbiguity` | 5 | PASS |
| 16 | Scope claim adversarial | `TestScopeClaimAdversarial` | 5 | PASS |
| 17 | Budget/filibuster | `TestBudgetFilibuster` | 8 | PASS |

### 5.3 Profiling Harness Tests (test_harness.py — 59 tests)

| # | Domain | Test Class | Tests | Status |
|---|--------|------------|-------|--------|
| 18 | Generator utilities | `TestGeneratorCommon` | 6 | PASS |
| 19 | Generator determinism | `TestGeneratorDeterminism` | 5 | PASS |
| 20 | Generator correctness | `TestGeneratorCorrectness` | 11 | PASS |
| 21 | Cycle runner integration | `TestCycleRunner` | 7 | PASS |
| 22 | Baselines | `TestBaselines` | 4 | PASS |
| 23 | Pre-flight verification | `TestPreflight` | 6 | PASS |
| 24 | Executor sandbox | `TestCapturingExecutor` | 5 | PASS |
| 25 | Replay determinism | `TestReplayDeterminism` | 4 | PASS |
| 26 | Selector permutation invariance | `TestSelectorPermutationInvariance` | 1 | PASS |
| 27 | Report generation | `TestReportGeneration` | 2 | PASS |
| 28 | Failure semantics | `TestFailureSemantics` | 2 | PASS |
| 29 | Report structure (numbers-only) | `TestReportGeneration` | — | PASS |

---

## 6. Constitution v0.1.1 Summary

### Closed Action Space (4 executable types + 1 terminal decision)

| Action | Side Effect Class | Kernel Only | Requires | Execution |
|--------|-------------------|-------------|----------|-----------|
| Notify | low | no | citations, scope_claim, justification | Executor dispatches |
| ReadLocal | none | no | citations, scope_claim, justification | Executor dispatches |
| WriteLocal | medium | no | citations, scope_claim, justification | Executor dispatches |
| LogAppend | low | **yes** | citations only | Executor dispatches |

**Exit** is listed in the constitution's `action_space.action_types` (with `side_effect_class: terminal`) to allow validation of Exit bundles if ever proposed through the admission pipeline. However, in the kernel implementation, EXIT is a **decision-only terminal outcome**: `policy_core()` emits an `ExitRecord` directly when an integrity-risk system observation is detected. No `ExecutionWarrant` is issued. No executor dispatch occurs. The host reads the EXIT decision and terminates the loop.

This means Exit exists in two layers:
- **Constitution layer:** declared action type (admissible in principle, gates would pass it)
- **Kernel layer:** decision type triggered autonomously from observations (no candidate, no warrant, no execution)

Phase X uses only the kernel-layer model. The constitution-layer Exit type is carried forward for completeness and possible Phase XI use (e.g., user-requested Exit bundles). In Phase X, Exit bundles are never constructed by the host and are never admitted; all Exit events are kernel-triggered decision outcomes. Exit-as-action-type is dormant in Phase X; admission rules would validate it, but no Phase X component emits such candidates.

### Admission Pipeline (pre-admission + 5 gates, sequential)

0. **required_observations** *(pre-admission)* — exactly 1 TIMESTAMP observation required; 0 or 2+ → REFUSE with `MISSING_REQUIRED_OBSERVATION` (Erratum X.E1)
1. **completeness** — required artifacts present, kernel-only check, field validation, LogAppend limits
2. **authority_citation** — all citations resolvable in constitution
3. **scope_claim** — clause_ref resolves, observation_ids valid
4. **constitution_compliance** — action type in closed set
5. **io_allowlist** — paths under `read_paths` / `write_paths`

The pre-admission step fires before any candidates are evaluated. Its refusals carry `failed_gate="required_observations"` and are tracked separately from the 5 admission gates in the profiling report's gate histogram.

### IO Policy

- Read: `./artifacts/`, `./workspace/`
- Write: `./workspace/`, `./logs/`
- Network: disabled

### v0.1 → v0.1.1 Deltas

1. LogAppend: `jsonl_line` (string) → `jsonl_lines` (array\<string\>)
2. LogAppend: added per-warrant limits (`max_lines_per_warrant: 50`, `max_chars_per_line: 10000`, `max_bytes_per_warrant: 256000`)
3. RefusalRecord: removed `INTEGRITY_RISK` from refusal reason codes (integrity risk triggers EXIT only)

---

## 7. Design Decisions (from Q&A)

The 83-question Q&A process (documented in `docs/questions.md` and `docs/answers.md`) resolved all spec ambiguities before implementation. Key binding decisions:

| Decision | Resolution | Source |
|----------|------------|--------|
| Canonical JSON format | RFC 8785 JCS-compatible (sorted keys, no whitespace, strict UTF-8) | A44–A45 |
| Hashing algorithm | SHA-256, untruncated hex | A5 |
| Selector rule | Lexicographic-min of raw bundle hash bytes | A4 |
| Decision types | ACTION, REFUSE, EXIT (closed set) | A9 |
| Observation kinds | user_input, timestamp, budget, system (closed set) | A10 |
| EXIT semantics | Decision-only terminal outcome; `ExitRecord` emitted by kernel, no warrant, no executor dispatch | A29, A41 |
| LogAppend recursion | No recursive logging; LogAppend produces `log_commit_summary` in execution_trace only | A55, A58 |
| Citation format | `constitution:v0.1.1#<id>` (preferred) or `constitution:v0.1.1@<json_pointer>` | A14 |
| Budget enforcement | Token count > `max_total_tokens_per_cycle` → REFUSE with BUDGET_EXHAUSTED | A49 |
| Host termination | Host must invoke kernel for ExitRecord even on startup failure | A72 |
| Replay strategy | Forward reconstruction of internal_state, re-derive log lines | A33 |

---

## 8. Audit Response (2026-02-10)

An independent audit pass identified four areas of concern. Three were
structurally clean; one was a real authority leak that has been fixed.

### A. Host-constructed candidates — FIXED

**Finding:** The host could fabricate LogAppend warrants via
`ExecutionWarrant_for_log()` in `host/cli/main.py`, bypassing `policy_core`.

**Assessment:** Real authority leak. The LogAppend bundles went through admission,
but the warrant was issued by host code, not by the kernel. This violated the
stated architecture: "the host proposes; the kernel decides."

**Fix:** Added `issue_log_append_warrants()` to `kernel/src/policy_core.py` — a
pure kernel function that admits LogAppend bundles and issues warrants. The host
now calls this kernel function instead of fabricating warrants. The old
`ExecutionWarrant_for_log()` has been deleted.

**Tests added:**
- Host cannot inject pre-admitted ActionRequest into executor
- Host cannot issue kernel-only action (LogAppend from non-kernel author rejected)
- Host cannot mutate internal_state to bypass cycle validation

### B. System observations — DOCUMENTED

**Finding:** The host has the power to generate `system` observations that
force EXIT (e.g., `startup_integrity_fail`). If user input or LLM output
could fabricate system observations, this would be a control channel.

**Assessment:** Structurally clean. In the current code:
- User input routes through `make_user_input_observation()` only
- LLM output routes through `parse_llm_candidates()` only
- `make_system_observation()` is called only by `startup()` integrity checks

**Hardening:** Added an explicit trust boundary docstring to
`make_system_observation()` documenting that it must NEVER be called with
values derived from user input or LLM output. Added test documenting the
expectation that system observations carry `Author.HOST`.

**Note:** This is a convention boundary, not an enforcement boundary. Python
does not enforce call-site restrictions. A code auditor must verify the
call sites. There are exactly four in `startup()` (two OK/FAIL pairs:
constitution hash, citation index). A test enforces this count.

**Trust classification:** The `system` observation channel is
**trusted-by-construction** in RSA-0. The host is trusted for integrity
reporting but not trusted for execution authority. This is an explicit
Phase X design decision, not an oversight. Hardening options (e.g.,
host attestation over payload) are deferred to post-Phase-X work as they
would add complexity without changing the sovereignty boundary—the kernel
was never designed to distrust its own observation inputs, only to
enforce that observations alone cannot cause side effects without warrants.

**Clarification (invariant boundary):** System observations can trigger EXIT
or REFUSE decisions but cannot directly authorize execution. Warrants remain
required for every side effect. Observations constrain decisions; they do not
authorize side effects. This is the fundamental Phase X doctrine and it holds
even for the trusted `system` observation channel.

### C. LogAppend timestamp determinism — FIXED (Erratum X.E1)

**Finding:** If log lines embed wall-clock timestamps not part of observation
input, replay determinism could silently break.

**Original assessment (v1):** Incorrectly assessed as clean.

**Revised assessment (v2, pre-profiling audit):** The original audit missed
that `_now_utc()` was called inside ALL 7 artifact `__post_init__` methods,
not just host-created observations. This meant every artifact ID was
wall-clock-dependent, including kernel-created warrants, refusals, and exit
records. Replay would reconstruct observations with logged `created_at` values,
but the kernel would generate NEW warrants with fresh `_now_utc()` timestamps,
producing different warrant IDs on each replay. This was a latent determinism
defect.

**Erratum X.E1 — Observation-sourced deterministic clock:**
1. Removed `if not self.created_at: self.created_at = _now_utc()` from all 7
   artifact `__post_init__` methods in `artifacts.py`
2. Added `extract_cycle_time()` to `policy_core.py` — extracts ISO-8601 UTC
   timestamp from the single required TIMESTAMP observation
3. Added pre-admission TIMESTAMP validation: exactly 1 TIMESTAMP observation
   required; 0 or 2+ → REFUSE with `MISSING_REQUIRED_OBSERVATION`
4. All kernel-created artifacts (warrants, refusals, exit records) now receive
   `created_at=cycle_time` from the extracted TIMESTAMP value
5. `_now_utc()` retained as utility for host use (observation construction)
6. Added `MISSING_REQUIRED_OBSERVATION` to `RefusalReasonCode` enum
7. Host constructors now always pass `created_at` explicitly; artifact IDs are never derived from implicit time

**Tests added:** `TestDeterministicClock` (6 tests) verifying same-inputs →
same-warrant-hash, different-timestamp → different-warrant, missing/duplicate
TIMESTAMP → REFUSE, and cycle_time propagation to refusal/exit records.

### D. Replay state reconstruction — CLEAN

**Finding:** If replay depends on anything outside logged artifacts, it fails.

**Assessment:** Clean. Replay uses exactly:
1. Logged observations (`observations.jsonl`) → `reconstruct_observations()`
2. Logged artifacts (`artifacts.jsonl`) → `reconstruct_candidates()`
3. Frozen constitution (hash-verified)
4. Forward-reconstructed `InternalState` via `state.advance(replayed_decision_type)`

No host state, no wall-clock, no external input.

### Fragile-but-correct items (acknowledged, not fixed)

1. **ScopeClaim semantic looseness** — Structural validation only; semantic
   truth is not checked. Correct for Phase X (sovereignty, not correctness).
   Phase XI/XII pressure point.

2. **Citation pointer brittleness** — Pointer-style citations
   (`@/json/pointer`) are fragile under constitution evolution. Not a Phase X
   problem; Phase XI amendment will need stable IDs everywhere.

3. **Cycle 0 begins with REFUSE or LogAppend** — Philosophically interesting,
   not incorrect. The RSA's first act of existence is either refusal or
   self-documentation.

---

## 9. What Is Not Implemented (By Design)

Per spec §16 and instructions §13, the following are explicitly excluded from Phase X:

- Intent routers
- Priority schedulers
- Retries or self-repair
- "Helpful" fallbacks
- Semantic ranking or learned reward models
- Background jobs
- Dynamic tool installation
- Network access
- Auto-correction
- Hidden defaults

These are classified as proxy-sovereignty regressions and are forbidden.

---

## 10. Definition of Done (per spec §17, instructions §12)

| Criterion | Status |
|-----------|--------|
| Agent runs autonomously (CLI loop) without human approval clicks | Implemented (`host/cli/main.py`) |
| Performs at least one admitted action (Notify) | Supported (host constructs Notify echo candidate) |
| Refuses correctly when no action is admissible | Tested (7 refusal tests pass) |
| Exits when mandated by policy (integrity risk) | Tested (4 EXIT tests pass) |
| Every side effect has admitted AR, scope claim, justification, warrant | Enforced by admission + executor |
| Replay determinism holds across runs | Tested (determinism + canonical JSON + clock-determinism tests pass) |

---

## 11. Running the System

### Prerequisites

```bash
pip install pyyaml pytest
```

### Run tests

```bash
cd src/axionic_rsa/RSA-0
python -m pytest kernel/tests/test_acceptance.py -v
```

### Run the CLI agent

```bash
cd src/axionic_rsa/RSA-0
python -m host.cli.main
```

### Run the replay harness

```bash
cd src/axionic_rsa/RSA-0
python -m replay.src.replay
```

### Run the X-0P profiling harness

```bash
cd src/axionic_rsa/RSA-0
python -m profiling.x0p.harness.src.runner
```

### Run all tests (kernel + harness)

```bash
cd src/axionic_rsa/RSA-0
python -m pytest kernel/tests/ profiling/x0p/harness/tests/ -v
```

---

## 12. X-0P Profiling Harness Architecture

### 12.1 Design Principles

The profiling harness is built to the RSA-0P spec with these binding constraints:

- **No agent modification** — profiling code lives in `profiling/x0p/`, never touches kernel source
- **No LLM** — all candidates are synthetically generated (deterministic, seeded)
- **Host bypass** — harness calls `policy_core()` directly, skipping the impure host layer
- **Observation-sourced time** — all timestamps derived from TIMESTAMP observations (Erratum X.E1)
- **CapturingExecutor via composition** — wraps the real Executor for sandbox isolation

### 12.2 Condition Generators

| Condition | Entropy | Cycles | Description |
|-----------|---------|--------|-------------|
| **A** | LOW | 100 | 10 well-formed templates (Notify/Read/Write), 80% distinct / 20% repeat |
| **B** | MEDIUM | 100 | Corpus-based natural language, seeded perturbations, 50–300 word-token bounds |
| **C** | HIGH | 100 | Adversarial taxonomy (I1–I5): constitution override, IO violations, warrant bypass, malformed bundles, selector boundary |
| **D** | MIXED | 100 | Budget stress at ±5% boundaries around `max_total_tokens_per_cycle=6000` (whitespace-split word count; synthetic mode has no BPE tokenizer) |
| **E** | MIXED | 100 | Multiple admissible bundles with permutations; n≤6 exhaustive, n>6 sample 20 |

### 12.3 Execution Order

1. Pre-flight (constitution integrity, schema, generator stability, artifact drift)
2. Condition A (inhabitation floor — abort if 0 ACTIONs)
3. Always-Refuse baseline
4. Always-Admit baseline (IO allowlist enforcement)
5. Conditions B, C, D, E
6. Replay verification (zero-divergence required)
7. Report generation (structured JSON, no narrative)

### 12.4 Baselines

| Baseline | Rule | Execution |
|----------|------|-----------|
| Always-Refuse | Every cycle → REFUSE | SKIPPED |
| Always-Admit | Admit first candidate within closed action-type + IO allowlist | Decision-only |

### 12.5 Token Accounting

All conditions use **whitespace-split word count** as the token ruler. There is no BPE/API tokenizer in synthetic mode (no LLM). The budget observation's `llm_output_token_count` field is populated with word counts from generated payloads. This makes Condition D's ±5% budget boundaries deterministic and reproducible. The word-count ruler is documented in `generator_common.py::word_count()`.

### 12.6 Report Metrics

- Decision distribution (ACTION/REFUSE/EXIT counts and rates per condition)
- Gate breakdown: distinguishes `required_observations` (pre-admission) from the 5 admission gates via `failed_gate_histogram`; also emits `reason_code_distribution` for full refusal taxonomy
- Authority utilization (Shannon entropy of clause citation frequency)
- Outcome cost matrix
- Latency summary (mean, median, p95, worst-case, variance)
- Baseline contrast (kernel vs always-refuse vs always-admit)

---

## End of Implementation Report
