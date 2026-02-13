# RSA X-0E Design Questions

Questions arising from reading the Phase X-0E spec (v0.1) and implementation instructions.
Each question is tagged with the source section(s) that prompted it.

---

## A — Constitution Version & Freeze Scope

**Q1.** Both documents reference `rsa_constitution.v0.1.1.yaml` exclusively. The codebase is currently at constitution v0.3 (with X-1 amendment and X-2 delegation additions). Does X-0E freeze against v0.1.1 specifically, or should it support any frozen constitution version? The spec prerequisite says "Frozen Constitution v0.1.1 — SHA-256 recorded," and closure criterion §17.7 says "Kernel byte-for-byte identical to X-0." But the kernel has since been extended with X-1 and X-2 modules. Clarify:
(a) Is the X-0E kernel the *original* X-0 kernel snapshot, ignoring X-1/X-2 extensions?
(b) Or is X-0E the *current* kernel (with X-1/X-2) pinned to v0.1.1 constitution (which would make X-1/X-2 code paths dormant)?
(c) Or should X-0E be constitution-version-agnostic, working with any frozen constitution?
*(spec §0, §17.7, instructions §2.1)*

**Q2.** If X-0E uses only v0.1.1, the v0.1.1 constitution has `amendment_policy: amendments_enabled: false` and no treaty/delegation sections. Do we strip the X-1/X-2 kernel extensions from the X-0E package, or simply never exercise them?
*(spec §2, §17.7)*

**Q3.** The constitution `.sha256` sidecar already exists at `artifacts/phase-x/constitution/rsa_constitution.v0.1.1.yaml.sha256`. Should the X-0E package embed a *copy* under `artifacts/phase-x/x-0e/` as the instructions suggest, or reference the existing sidecar in the shared `constitution/` directory?
*(instructions §1, §2.1)*

---

## B — Repo Layout & File Organization

**Q4.** The instructions (§1) propose a flat layout (`cli/`, `replay/`, `runtime/`, `logs/`) at the top of the RSA-0 repo. But the repo already has:
- `host/cli/main.py` (480 lines) — existing outer-loop CLI
- `replay/src/replay.py` (269 lines) — existing replay harness
- `host/tools/executor.py` (204 lines) — existing warrant executor

Should X-0E:
(a) Refactor/replace the existing `host/` and `replay/` code into the new layout?
(b) Create a parallel `cli/` and `runtime/` tree that wraps/imports from existing code?
(c) Treat the X-0E packaging as a *build output* that assembles from existing sources?
*(instructions §1)*

**Q5.** The instructions list `replay/src/jcs_canonicalize.py` and `replay/src/state_hash.py` as new files. But canonical JSON is already implemented in `kernel/src/artifacts.py` (`canonical_json()`, `canonical_json_bytes()`, `artifact_hash()`), and state hashing is duplicated across four profiling harness files. Should X-0E:
(a) Promote the existing `canonical_json` functions into a shared module and import everywhere?
(b) Create fresh standalone implementations in `replay/src/` that duplicate the logic?
(c) Keep the kernel's implementation canonical and have replay import from `kernel.src.artifacts`?
*(instructions §1, spec §9)*

**Q6.** The instructions list `runtime/src/net_guard.py` for disabling network access. What mechanism is expected? Python-level monkey-patching of `socket`? An OS-level firewall rule? Or simply a flag that causes the host to refuse any network-touching action types (which X-0E doesn't have anyway, since the only action is Notify)?
*(instructions §1, spec §14)*

---

## C — Warrant Determinism & ID Derivation

**Q7.** The spec (§10) defines `warrant_id = SHA256(cycle_id || artifact_hash || selector_rank || constitution_hash)`. The current X-2 implementation computes warrant_id as `SHA256(json.dumps({all warrant fields except warrant_id}, sort_keys=True))`. These are different formulas — the spec uses explicit field concatenation while the existing code hashes the full warrant dict.

Which is binding?
(a) The spec formula: `SHA256(cycle_id || artifact_hash || selector_rank || constitution_hash)` — four explicit fields only.
(b) The existing pattern: `SHA256(canonical_json(warrant_dict \ {warrant_id}))` — all fields.
(c) A new formula specific to X-0E?

If (a), what is the separator for `||`? Literal `||` bytes? Newline? No separator (raw concatenation)?
*(spec §10, instructions §7.3)*

**Q8.** The spec formula uses `selector_rank` as an input to `warrant_id`. Current selector returns a rank (integer). Is `selector_rank` the integer index (0, 1, 2...) or the string representation ("0", "1", "2...")? Or the full selector trace hash?
*(spec §10)*

**Q9.** The `cycle_id` in the warrant_id derivation — is this the integer cycle number, a string, or a hash of the cycle observation? Current code uses integer cycle numbers.
*(spec §10)*

---

## D — State Hash Chain

**Q10.** The spec (§11) defines `state_hash[n] = SHA256(state_hash[n-1] || artifacts[n] || admission_trace[n] || selector_trace[n] || execution_trace[n])`. Current state hashing is `SHA256(canonical_json(InternalState.to_dict()))` — a snapshot hash, not a chain.

X-0E requires a *chain* (each hash depends on the previous). Clarify:
(a) Are `artifacts[n]`, `admission_trace[n]`, etc. the *full JSONL records* for cycle n, or their *hashes*?
(b) What is the concatenation mechanism? Raw byte concatenation of JSON strings? Concatenation of hex digest strings?
(c) If a cycle has multiple artifacts (multiple admitted candidates), are they concatenated in selector-rank order?
*(spec §11, instructions §7.4)*

**Q11.** The initial state hash is `SHA256(active_constitution_hash || kernel_version_id)`. What exactly is `kernel_version_id`? The current codebase has no explicit kernel version string. Is it a git commit hash? A manually maintained version? A hash of the kernel source files?
*(spec §11, instructions §7.4)*

---

## E — Canonicalization (JCS Compliance)

**Q12.** The spec mandates "RFC 8785 — JSON Canonicalization Scheme (JCS)" strictly. The current `canonical_json()` uses `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)`. This is JCS-compatible *only for the type subset used* (no floats, no special Unicode). Should X-0E:
(a) Keep the current approach with an explicit assertion that the type subset is JCS-safe?
(b) Import/install a proper JCS library (e.g., `python-jcs` or `canonicaljson`)?
(c) Implement a standalone JCS function that handles the full spec (float serialization, Unicode normalization)?

If (b), which library? `canonicaljson` (used by Matrix protocol) or another?
*(spec §9, instructions §7.1)*

**Q13.** The instructions (§2.1) say "YAML must be canonicalized into a deterministic JSON form before hashing." The constitution is YAML. What is the canonical YAML→JSON conversion? `yaml.safe_load()` → `canonical_json()`? Or a specific YAML-to-JSON serializer? Different YAML parsers may produce different dict orderings for the same YAML input — is this a concern?
*(instructions §2.1)*

---

## F — Observation Stream & Test Vector

**Q14.** The spec (§4.1) says `rsa run` processes an "observation stream" from "stdin, file, or test vector." What is the observation format? The existing `host/cli/main.py` uses OpenAI API calls to generate candidate bundles from observations. X-0E spec says "no model calls." How does the observation-to-candidate pipeline work without an LLM?
(a) Are observations pre-baked JSONL files with fully-formed `CandidateBundle` records?
(b) Is there a deterministic hard-coded mapping from observation to candidate?
(c) Does the test vector include the full candidate (ActionRequest + ScopeClaim + Justification)?
*(spec §4.1, §15, instructions §4, §8)*

**Q15.** The spec (§15) requires "two independent machines must produce identical hashes." For the minimal test vector, does "independent machine" mean:
(a) Different OS instances with the same Python version?
(b) Different Python versions (e.g., 3.11 vs 3.12)?
(c) Different platforms (Linux vs macOS)?
What is the minimum reproducibility bar?
*(spec §15, §17.8)*

**Q16.** The test vector is "one observation → one admitted artifact → one warrant → one execution." But the current kernel pipeline expects a `CandidateBundle` (ActionRequest + ScopeClaim + Justification + AuthorityCitations), not a raw observation. Is the observation the *outer envelope* containing an already-constructed CandidateBundle in its payload? Or does X-0E introduce a simpler observation→artifact path?
*(spec §15, instructions §12)*

---

## G — Outbox & Idempotency

**Q17.** The outbox record requires a `timestamp` field described as "deterministic, from observation." But observations don't currently carry a `timestamp` field — they have a `payload` dict. Should the observation envelope be extended with an explicit `timestamp` field that flows through to the outbox? Or is the timestamp extracted from the observation payload by convention?
*(spec §6.1, instructions §5.1)*

**Q18.** For startup reconciliation (§6.2/instructions §6.2): "For each `warrant_id ∈ effected_warrants \ executed_warrants`" — the reconciliation adds a synthetic `execution_trace` entry. Does this synthetic entry also need a `state_hash` computation? Or is reconciliation outside the hash chain?
*(instructions §6.2, spec §11)*

**Q19.** The reconciliation trace is a separate log (`reconciliation_trace.jsonl`). Is it included in the state hash chain? The spec §11 formula only mentions `artifacts`, `admission_trace`, `selector_trace`, and `execution_trace` — reconciliation_trace is absent.
*(spec §11, instructions §6.2, §9)*

---

## H — Execution & Host Boundary

**Q20.** The existing `host/tools/executor.py` implements four action types: `Notify`, `ReadLocal`, `WriteLocal`, `LogAppend`. X-0E scope is "Notify only." Should the X-0E executor:
(a) Strip all other action types and refuse them?
(b) Keep the full executor but only test/exercise Notify?
(c) Create a new minimal executor that only knows Notify?
*(spec §2, §6, instructions §5)*

**Q21.** The existing `Notify` implementation in `executor.py` appends to a log file. The X-0E spec says Notify writes to `outbox.jsonl` specifically. The current `Notify` does not write to an outbox. Is X-0E's Notify the same logical operation but redirected to `outbox.jsonl`, or a new implementation?
*(spec §6.1, instructions §5.1)*

**Q22.** The spec (§5.2) says the host "must not interpret constitutional clauses." The current `host/cli/main.py` loads the constitution and passes it to the kernel. Does "interpret" mean the host must not read/parse constitutional fields for its own decision-making (which it doesn't), or does it mean the host must not even load the constitution YAML (only the kernel loads it)?
*(spec §5.1, §5.2)*

---

## I — Replay Architecture

**Q23.** The existing `replay/src/replay.py` re-runs `policy_core()` with logged observations. X-0E requires replay to also verify the state hash *chain* (not just per-cycle decisions). The current replay has no concept of a hash chain. Is the X-0E replay:
(a) An upgrade to the existing `replay.py`?
(b) A new standalone replayer (as suggested by instructions §1: `replay/src/replayer.py`)?
(c) Both — upgrade existing + add chain verification?
*(instructions §1, §11, spec §4.1)*

**Q24.** Replay must "recompute admission decisions" and "recompute selector outcomes." The current replay already does this. But X-0E adds execution outcome verification — replay must check that `execution_status` matches what would be expected. During replay, no actual execution occurs. How does replay verify execution outcomes?
(a) It trusts the logged `execution_status` and just verifies the warrant was correctly issued?
(b) It checks that for each warranted action, there exists an execution entry, and for each refused action, there is no execution entry?
(c) Something else?
*(spec §7, instructions §11)*

**Q25.** The instructions (§11) say replay must "apply startup reconciliation deterministically (based on outbox vs execution_trace)." During replay, there is no real crash. Does replay simulate reconciliation by examining the log state, or does it skip reconciliation and just verify the reconciliation_trace entries match what it would compute?
*(instructions §11, §6.2)*

---

## J — Packaging & Pinning

**Q26.** The spec (§14) says "pin runtime version" and "pin dependency versions." What is the pinning mechanism?
(a) A `requirements.txt` or `pyproject.toml` with pinned versions?
(b) A lockfile (`pip freeze` output)?
(c) A Docker image with fixed base?
(d) All of the above?
*(spec §14, instructions §1)*

**Q27.** The spec (§14) says "refuse execution on kernel version mismatch." How is kernel version mismatch detected? There is no `kernel_version_id` currently defined. Is this the same as Q11 — a hash of kernel source, or a manually maintained version string?
*(spec §14)*

**Q28.** Instructions §1 lists `artifacts/phase-x/x-0e/x-0e_profile.v0.1.json` as a deliverable artifact. What is the expected content/schema of this profile file? Is it analogous to the profiling harness output from X-0P/X-0L/X-1/X-2?
*(instructions §1)*

---

## K — Test Suite Scope

**Q29.** The instructions (§12) list 7 test cases. The existing test suites for prior phases have 50–100+ tests. Is the §12 list the *minimum* set, or the *complete* set? Should X-0E tests also cover:
- Constitution loading edge cases (missing sidecar, corrupt YAML, wrong hash)?
- Log format validation (missing fields, wrong types)?
- Multiple cycles (not just single-observation)?
- Warrant determinism across restarts?
*(instructions §12)*

**Q30.** Test 6 says "Cross-machine replay: logs copied to fresh machine → identical state hash chain." How is this tested in CI? Is it sufficient to run replay twice in the same environment (simulating fresh state by clearing caches), or must there be an actual separate machine/container?
*(instructions §12, spec §15)*

---

## L — Relation to Existing Profiling Harnesses

**Q31.** X-0P, X-0L, X-1, and X-2 each have dedicated profiling harnesses (`profiling/x0p/`, etc.) with cycle runners and test suites. X-0E is described as "outside laboratory scaffolding." Does X-0E:
(a) Get its own profiling harness in `profiling/x0e/` following the established pattern?
(b) Replace the profiling concept entirely — the `rsa run` / `rsa replay` CLI *is* the harness?
(c) Both — CLI for production use, plus a lightweight profiling wrapper for closure testing?
*(spec §0, §19, instructions §14)*

**Q32.** The existing profiling harnesses use `gpt-4o` (X-0L) or stub generators (X-0P) for candidate generation. X-0E forbids model calls. If X-0E has a profiling harness, it must use pre-baked observations only. Is this the same as the test vector concept (§15), or is the profiling run expected to cover more cycles/scenarios?
*(spec §3, §15)*

---

## M — Scope Boundaries & Edge Cases

**Q33.** The spec says "X-0E introduces no new invariants" (§0) and "kernel byte-for-byte identical to X-0" (§17.7). But the instructions introduce several new concepts: outbox.jsonl, reconciliation_trace.jsonl, startup reconciliation, execution outcome logging with SUCCESS/FAILURE, state hash chaining. These are new behavioral requirements. Are they classified as:
(a) Host-layer additions (not kernel changes)?
(b) Operational additions that the spec considers "packaging, not invariants"?
(c) Implicit kernel extensions that §17.7 incorrectly constrains?
*(spec §0, §17.7, instructions §6, §7, §10)*

**Q34.** The spec (§17.3) says "No side effect occurs without warrant." The startup reconciliation itself writes to `reconciliation_trace.jsonl`. Is this write considered a "side effect" that requires a warrant? Or is reconciliation a host-level infrastructure operation exempt from warrant gating?
*(spec §17.3, instructions §6.2)*

**Q35.** If `rsa run` is interrupted mid-cycle (after admission but before execution), what is the expected recovery behavior on restart? Resume mid-cycle? Re-run the entire cycle? The spec doesn't explicitly address partial-cycle crash recovery.
*(spec §6, instructions §6.2)*

---

## N — Follow-Up Questions (from Answers)

**Q36.** A1 says X-0E is constitution-version-agnostic mechanically but certifies closure against v0.1.1. The v0.1.1 constitution lacks the `AmendmentProcedure`, `AuthorityModel`, and `TreatySystem` sections that X-1/X-2 added. When the kernel loads v0.1.1 and the X-1/X-2 modules are present but dormant: should the kernel's X-1/X-2 code paths be explicitly guarded with "if section exists in constitution" checks, or do they already degrade gracefully when those sections are absent? If not, this is a code change needed before X-0E.
*(A1, A2)*

**Q37.** A5 says to promote canonicalization + state hashing into a shared module. Where should it live? Options:
(a) `kernel/src/canonical.py` (keeps it in the kernel namespace)
(b) A new top-level `lib/` or `shared/` directory
(c) Keep it in `kernel/src/artifacts.py` but have replay and host import from there directly
*(A5)*

**Q38.** A7 binds `warrant_id = SHA256(JCS(warrant_payload_without_warrant_id))`. The current X-2 implementation uses `json.dumps(sort_keys=True)` not JCS. Once a real JCS library is adopted (per A12), the existing `compute_warrant_id()` in `policy_core_x2.py` must be updated. Should this JCS migration also update the `_compute_id()` method on `ExecutionWarrant` in `artifacts.py` and the `artifact_hash()` function? In other words: does X-0E mandate JCS everywhere hashing occurs, retroactively affecting all existing hash computations?
*(A7, A12, meta-fix)*

**Q39.** A10 introduces `H_observations[n]` as a component of the state hash chain, but the spec's §11 formula omits observations from the chain (only listing `artifacts`, `admission_trace`, `selector_trace`, `execution_trace`). The answer adds observations. Is this intentional — observations are now part of the chain — or should the implementation follow the spec formula exactly (without observations)?
*(A10, spec §11)*

**Q40.** A11 defines kernel_version_id as a manual semantic string (e.g., `"rsa-kernel-x0e-v0.1"`). A27 says replay refuses on version mismatch. If the kernel is shared across X-0E and future phases, and the version string changes for X-1E or X-1 work, old logs become non-replayable. Is the version string tied to:
(a) The X-0E phase specifically (changes only when X-0E is revised)?
(b) The kernel codebase (changes on any kernel modification)?
(c) The constitution version (changes per constitution)?
*(A11, A27)*

**Q41.** A12 says use a real JCS library as a pinned dependency. Which specific Python library is approved? The main candidates are:
- `canonicaljson` (Matrix protocol, well-maintained, but encodes to bytes not str)
- `jcs` (direct RFC 8785 implementation, less maintained)
- Self-implemented (more control, more risk)
Has a choice been made, or should we evaluate and propose?
*(A12)*

**Q42.** A13 says "no floats allowed" and to enforce with validation. The constitution YAML could contain floats if a future version adds numeric thresholds (e.g., `density_upper_bound: 0.85` in v0.2). Since X-0E is constitution-agnostic mechanically, should the float prohibition be:
(a) A validation error at constitution load time (refuse any YAML that produces floats)?
(b) A JCS-level concern only (handle floats correctly if they appear)?
(c) Documented as a constraint on constitution authoring but not enforced in code?
*(A13)*

**Q43.** A18 says reconciliation changes the effective execution trace and must be reflected in the hash chain via execution_trace entries. But A35 says on crash recovery, re-run from last completed logged cycle. If a crash occurs after the outbox write but before execution_trace, reconciliation on restart appends a synthetic execution_trace entry. This new entry was not present in the original run's hash chain. How does replay handle this? The hash chain will differ from a clean (non-crashing) run. Is this acceptable because replay reconstructs from the *actual* logs (including reconciliation), not from an idealized non-crash scenario?
*(A18, A35, spec §11)*

**Q44.** A20 says refuse everything except Notify. The existing `executor.py` supports `ReadLocal`, `WriteLocal`, `LogAppend`. `LogAppend` is used internally by the host to write logs. If LogAppend is explicitly refused as an action type, how does the host write logs? Is `LogAppend` a host infrastructure operation (not an RSA action), or is it an action type that needs to remain but be excluded from the "Notify only" constraint?
*(A20)*

**Q45.** A28 describes the profile as a "freeze manifest" with fields like `kernel_version_id`, `constitution_hash`, `dependency_lock_hash`, etc. Should this manifest be:
(a) Generated automatically by `rsa run` at startup and written to the artifacts directory?
(b) Hand-authored and checked in as a static artifact (like the constitution)?
(c) Generated by a separate `rsa freeze` or build command?
*(A28)*

**Q46.** A30 says use two clean containers for cross-machine replay in CI. The current project has no CI configuration or Dockerfile. Should X-0E deliverables include:
(a) A Dockerfile for the RSA runtime?
(b) A CI workflow file (GitHub Actions)?
(c) Both?
(d) Neither — just document the procedure and test manually?
*(A26, A30)*

**Q47.** A33 reinterprets §17.7 "kernel byte-for-byte identical to X-0" as "no semantic changes to authority rules." This is a significant deviation from the literal spec text. Should the spec be amended to reflect this interpretation before implementation begins, or proceed with the relaxed interpretation and document the rationale?
*(A33, spec §17.7)*

---

## O — Follow-Up Questions Round 2 (from A36–A47)

**Q48.** A36 requires graceful degradation when optional constitution sections are absent, with explicit `Optional[...]` fields and deterministic guards. The current constitution parser in `kernel/src/constitution.py` loads v0.1.1 today. Does it already return `None` for missing sections like `amendment_procedure` and `treaty_system`, or does it assume they exist? If the latter, how extensive are the required guard additions — just the X-1/X-2 entry points, or scattered throughout admission/selector/policy_core?
*(A36)*

**Q49.** A37 places shared canonicalization in `kernel/src/canonical.py` and hashing in `kernel/src/hashing.py`. The current `canonical_json()`, `canonical_json_bytes()`, and `artifact_hash()` live in `kernel/src/artifacts.py` (lines ~30–50). Moving them to new files changes every import in the codebase (kernel tests, all four profiling harnesses, replay, host). Should these moves happen as a preparatory refactor *before* X-0E implementation begins, or as part of the X-0E implementation itself?
*(A37)*

**Q50.** A38 says JCS is mandatory for all hash computations participating in X-0E determinism. Switching from `json.dumps(sort_keys=True)` to a JCS library will produce *different bytes* for the same input if the library handles any edge case differently (e.g., Unicode escaping, key ordering of nested objects). This means all existing test fixtures with hardcoded hashes will break. Should the test migration be:
(a) Part of X-0E (update all fixtures to new JCS-based hashes)?
(b) A separate preparatory PR before X-0E begins?
(c) Handled by making tests compute expected hashes dynamically rather than using hardcoded values?
*(A38)*

**Q51.** A39 says follow the spec exactly: no observations in the state hash chain. But A10 *includes* `H_observations[n]` in the chain formula. A39 overrides A10. To confirm: the binding implementation formula is:
```
state_hash[n] = SHA256(
  state_hash[n-1] ||
  H_artifacts[n] ||
  H_admission[n] ||
  H_selector[n] ||
  H_execution[n]
)
```
with observations excluded — correct?
*(A10, A39, spec §11)*

**Q52.** A40 ties `kernel_version_id` to the "replay semantics regime" — it changes only when hashing rules, warrant derivation, state hash chain rules, or log schema changes. Given that X-0E itself is changing hashing (JCS migration per A38) and adding the state hash chain (new), the kernel_version_id for X-0E must be distinct from any prior implicit version. Is there a prior version string that needs to be retroactively assigned to pre-X-0E logs, or are pre-X-0E logs simply outside the versioned replay regime (non-replayable under X-0E rules)?
*(A40)*

**Q53.** A41 approves `canonicaljson` as the default JCS library. The `canonicaljson` library returns `bytes`, not `str`. The current `canonical_json()` returns `str` and `canonical_json_bytes()` returns `bytes`. If we adopt `canonicaljson`, the natural primitive becomes bytes-first. Should the shared module expose:
(a) Both `canonical_json() → str` and `canonical_json_bytes() → bytes` for compatibility?
(b) Only `canonical_json_bytes() → bytes` (forcing callers to decode if they need str)?
(c) Only `canonical_json() → str` (wrapping the library's bytes output)?
*(A41)*

**Q54.** A42 says support floats correctly per RFC 8785 and forbid NaN/Inf. The `canonicaljson` library (approved in A41) handles floats by encoding them as integers when possible (e.g., `1.0` → `1`). This means `yaml.safe_load()` producing `1.0` (float) from YAML `1.0` will serialize differently than if the YAML had `1` (int). Is this acceptable, or must the YAML→Python loading step normalize numeric types before JCS?
*(A42, A41)*

**Q55.** A43 confirms that crash-then-reconcile runs produce different hash chains than clean runs, and replay reconstructs from actual logs. This means the test vector (spec §15) — which must produce identical hashes on two machines — must be a *clean run* (no crash). Should crash-recovery scenarios have *separate* test vectors with their own expected hash sequences, or is crash recovery tested only via unit/integration tests (not cross-machine determinism tests)?
*(A43, spec §15)*

**Q56.** A44 says `LogAppend` is host infrastructure, not a warranted action. The current `executor.py` implements `LogAppend` as an action type with warrant gating. Refactoring logging out of the warrant path means:
(a) Removing `LogAppend` from the `ActionType` enum entirely?
(b) Keeping it in the enum but never issuing warrants for it?
(c) Moving log-writing to a separate host service that is not routed through the executor?
Which approach, and does this require kernel changes (removing LogAppend from the action space)?
*(A44)*

**Q57.** A45 introduces a new `rsa freeze` CLI command. The spec (§4.1) only defines `rsa run` and `rsa replay`. Adding `rsa freeze` extends the CLI surface beyond spec. Should this be:
(a) A formal addition to the X-0E deliverable (update spec)?
(b) A utility script outside the `rsa` CLI namespace (e.g., `scripts/generate_manifest.py`)?
(c) Part of the build/packaging process, not a runtime command?
*(A45, spec §4.1)*

**Q58.** A46 requires both Dockerfile and GitHub Actions workflow. The current repo has no CI pipeline. What is the scope of the GitHub Actions workflow:
(a) X-0E cross-machine replay only (the two-container test)?
(b) Full test suite (`pytest` for all 478+ tests) plus the cross-machine replay?
(c) Full test suite, cross-machine replay, and linting/type-checking?
*(A46)*

**Q59.** A47 says amend §17.7 before implementation. Who amends the spec — should the implementation agent propose the amended text in a separate document/PR, or directly edit `docs/X-0E/spec.md`? And does this amendment require approval before X-0E coding begins, or can it proceed in parallel?
*(A47)*

---

## P — Follow-Up Questions Round 3 (from A48–A59)

**Q60.** A48 says guard at "phase entry points and gate dispatch" with a deterministic `NOT_APPLICABLE` / `MISSING_CONSTITUTION_SECTION` refusal. Currently `policy_core()` is the single entry point that dispatches to admission gates. If a v0.1.1 observation somehow triggers an X-1 amendment path (e.g., an `ActionRequest` with `action_type: "AmendConstitution"`), should the refusal happen:
(a) At admission gate level (gate refuses the action type as not in the v0.1.1 closed set)?
(b) At a new pre-dispatch check that inspects constitution capabilities before entering any gate?
(c) Both (defense in depth)?
The v0.1.1 constitution already lists `AmendConstitution` as forbidden — does the existing `io_allowlist` / `constitution_compliance` gate already cover this, making explicit guards unnecessary for that path?
*(A48)*

**Q61.** A49 says do the canonicalization move as PR0 (mechanical refactor, no semantic change). The current `canonical_json()` in `artifacts.py` is imported by ~15+ files across kernel tests, profiling harnesses, replay, and host. Should PR0 also add a compatibility shim in `artifacts.py` (re-export from `canonical.py`) to avoid breaking all imports at once, or do a clean cut with updated imports everywhere?
*(A49)*

**Q62.** A50 says compute expected hashes dynamically in tests, with a small set of "golden vectors" pinned. How many golden vectors are needed? Specifically:
(a) One per artifact type (Observation, ActionRequest, ScopeClaim, ExecutionWarrant, etc.)?
(b) One end-to-end vector (the §15 test vector with full state hash chain)?
(c) A JCS conformance suite (RFC 8785 test cases from the spec)?
*(A50)*

**Q63.** A51 confirms the 5-component chain formula (no observations). The `||` operator — A10 previously said "hash-of-hashes" where each component is `SHA256(JCS(list_of_records))`. Confirm: the `||` is concatenation of the raw hex digest strings (not binary), then SHA256 of that concatenated string? Or is it concatenation of raw bytes (32 bytes each), then SHA256 of the 160-byte (5×32) binary block? The encoding matters for cross-implementation reproducibility.
*(A51, A10)*

**Q64.** A52 says pre-X-0E logs are outside the versioned replay regime. The existing `replay/src/replay.py` currently replays X-0P and X-0L logs. After X-0E lands with `kernel_version_id` enforcement, will the old `replay.py` still work for old logs? Or does upgrading the replay harness (per A23) break backward compatibility with pre-X-0E logs? Should we:
(a) Keep the old replay code path for unversioned logs (dual mode)?
(b) Freeze the old `replay.py` as `replay_legacy.py` and build X-0E replay fresh?
(c) Accept that old logs are no longer replayable with the upgraded harness?
*(A52, A23)*

**Q65.** A53 says expose both `canonical_bytes()` and `canonical_str()`, bytes-first. The current `artifact_hash()` calls `canonical_json_bytes()`. With the rename to `canonical_bytes()`, should `artifact_hash()` also be renamed (e.g., to `content_hash()` or `jcs_hash()`) to reflect that it now uses JCS, or keep the name for continuity?
*(A53)*

**Q66.** A54 says do NOT normalize numeric types — `1` (int) and `1.0` (float) are distinct. But `canonicaljson` library encodes `1.0` as `1` (integer form) per RFC 8785 §3.2.2.3. This means after JCS, `{"x": 1}` and `{"x": 1.0}` produce *identical* canonical bytes and therefore identical hashes. The distinction is lost at the JCS layer despite being preserved at the Python layer. Is this acceptable? Or does this mean the "distinct inputs" claim from A54 is effectively void for the hash-relevant path?
*(A54, A41)*

**Q67.** A55 says clean test vector for closure, crash scenarios as integration tests. For the integration crash tests: the current test framework is `pytest`. Should crash simulation be done via:
(a) Mocking file I/O to simulate partial writes (e.g., `outbox.jsonl` written but `execution_trace.jsonl` not)?
(b) Actually killing a subprocess mid-cycle and verifying recovery?
(c) Constructing log files manually with deliberate inconsistencies, then running reconciliation?
*(A55, instructions §12 test 3/4)*

**Q68.** A56 says move log-writing to host infrastructure, not routed through executor-as-action. The current `executor.py` has `LogAppend` as one of four action types. If we make `LogAppend` unreachable in X-0E (keep in enum, never warrant it), the host needs a *separate* log-writing interface. Should this be:
(a) A new `host/log_writer.py` module that the host calls directly?
(b) Methods on the existing executor that bypass warrant checking (a "privileged" path)?
(c) A simple `append_jsonl(path, record)` utility function used by the host loop?
*(A56)*

**Q69.** A57 says implement manifest generation as `scripts/generate_x0e_manifest.py` or a `make` target. The repo currently has no `Makefile` or `scripts/` directory. Which is preferred:
(a) A standalone Python script in a new `scripts/` directory?
(b) A `Makefile` with targets for freeze, test, run, replay?
(c) Both (Makefile delegates to scripts)?
*(A57)*

**Q70.** A58 says CI scope is cross-machine replay (mandatory) + minimal pytest smoke (optional). What constitutes the "minimal pytest subset" for X-0E? Is it:
(a) Only the new X-0E-specific tests?
(b) X-0E tests plus the core kernel tests (`test_acceptance.py`)?
(c) All tests that exercise code paths reachable under v0.1.1 constitution?
*(A58)*

**Q71.** A59 says propose the §17.7 amendment as a separate doc PR. The answers document (A47) already contains the proposed replacement text. Should this amendment also incorporate the other binding clarifications from the Q&A (e.g., warrant_id rule from A7, chain formula from A51, kernel_version_id semantics from A40), creating an "X-0E spec v0.2" with all Q&A resolutions baked in? Or keep the amendment minimal (§17.7 only) and let the Q&A answers serve as the binding supplement?
*(A59, A47)*

**Q72.** The three-PR plan (A59 consolidated recommendation) is PR0 (refactor), PR-SPEC (text fix), PR1 (X-0E semantics). What is the dependency ordering? Specifically:
(a) PR0 must merge before PR1, but PR-SPEC can merge in parallel with either?
(b) All three are strictly sequential: PR0 → PR-SPEC → PR1?
(c) PR0 and PR-SPEC can be parallel, both must merge before PR1?
*(A59 consolidated recommendation)*

---

## Q — Follow-Up Questions Round 4 (from A60–A72)

**Q73.** A23 said "upgrade existing `replay.py`" (single implementation), but A64 says "freeze legacy replay as `replay_legacy.py` and build `replay_x0e.py`" (two implementations). These contradict. Which is binding?
(a) Single `replay.py` upgraded with regime detection — dispatches to legacy or X-0E mode based on log metadata?
(b) Two separate files (`replay_legacy.py` + `replay_x0e.py`) with a thin CLI dispatcher?
(c) Abandon legacy replay entirely — old logs are historical artifacts, not replayable?
*(A23, A64)*

**Q74.** A53 names the new functions `canonical_bytes()` and `canonical_str()`. A61 says keep shim exports as `canonical_json` and `canonical_json_bytes` in `artifacts.py`. This creates two naming conventions: the new module uses `canonical_bytes/str`, the shim re-exports as `canonical_json/canonical_json_bytes`. Should PR1 (JCS migration) also rename the shim exports to match the new names, or keep the old names indefinitely for backward compatibility?
*(A53, A61)*

**Q75.** A63 says raw 32-byte concatenation for the state hash chain. The initial state hash is `SHA256(active_constitution_hash || kernel_version_id)`. The `constitution_hash` is 32 raw bytes, but `kernel_version_id` is a variable-length string (e.g., `"rsa-replay-regime-x0e-v0.1"`). How is the string encoded for concatenation? UTF-8 bytes directly? Or hash the string first to get 32 bytes and concatenate the two 32-byte values?
*(A63, A11, spec §11)*

**Q76.** A62 says golden vectors include "one per hash primitive" for at least `ActionRequest` and `ExecutionWarrant`. Where are these vectors stored?
(a) Inline in test files as Python dicts + expected hex strings?
(b) As separate JSON fixture files under `tests/fixtures/`?
(c) In the artifacts directory alongside the constitution?
*(A62)*

**Q77.** A68 says put `append_jsonl()` in `host/log_io.py`. The spec (instructions §9) requires append-only discipline. Does `append_jsonl()` need to enforce:
(a) `fsync` after each write (crash safety)?
(b) File locking (concurrent access prevention)?
(c) Append-mode open (`"a"`) only, never `"w"`?
(d) All of the above?
And should replay also use `log_io.py` for reading, or is it read-only and uses its own loader?
*(A68, instructions §9)*

**Q78.** A69 says create `scripts/generate_x0e_manifest.py`. The manifest includes `dependency_lock_hash` (hash of lockfile). There is currently no lockfile in the repo. Should PR0 or PR1 also create a `requirements-lock.txt` or `poetry.lock`, and if so, what dependencies are pinned? The current `pyproject.toml` (if any) may have loose version specs.
*(A69, A28, A26)*

**Q79.** A70 says CI runs only X-0E-specific tests. But X-0E tests will import from `kernel.src.*` and exercise `policy_core()`, admission gates, selector — all shared code. If a regression is introduced in shared kernel code, X-0E CI won't catch it unless it manifests in the X-0E test paths. Is this risk acceptable, or should CI also run `test_acceptance.py` as a 30-second smoke check?
*(A70)*

**Q80.** A72 says PR0 and PR-SPEC can run in parallel. PR0 adds `kernel/src/canonical.py` and `kernel/src/hashing.py` with compatibility shims. PR-SPEC amends `docs/X-0E/spec.md`. These are indeed independent. But who reviews PR-SPEC — does the implementation agent self-merge a spec text change, or does it require explicit human approval before merge?
*(A72, A59)*

---

## R — Follow-Up Questions Round 5 (from A73–A80)

**Q81.** A73 introduces a dispatcher in `rsa replay` that routes to legacy or X-0E mode based on `kernel_version_id` in log metadata. Pre-X-0E logs have no `kernel_version_id`. Should the dispatcher treat absent `kernel_version_id` as:
(a) Implicit legacy mode (route to `replay_legacy.py`)?
(b) An error requiring the user to pass an explicit `--legacy` flag?
(c) A warning + legacy fallback?
*(A73)*

**Q82.** A75 defines `state_hash[0] = SHA256(constitution_hash_bytes || kernel_version_hash)` where `kernel_version_hash = SHA256(UTF8(kernel_version_id))`. This means changing the `kernel_version_id` string changes `state_hash[0]` and therefore the entire chain. A40 says `kernel_version_id` changes only when replay semantics change. If a typo is discovered in the version string after logs exist, correcting it would break replay of those logs. Should the version string be:
(a) Frozen in code and never corrected (typos become canonical)?
(b) Indirected through a lookup table so the string can be corrected while the hash stays stable?
(c) Accompanied by its pre-computed hash in the freeze manifest, making the string advisory and the hash binding?
*(A75, A40)*

**Q83.** A77 says `fsync` after each entry for crash safety, with single-writer assumption. The spec (instructions §4) says `rsa run` processes an "observation stream." If observations arrive rapidly, per-entry `fsync` across 5+ log files per cycle could become a bottleneck. Is there a latency/throughput target for X-0E, or is correctness-at-any-speed acceptable for v0.1?
*(A77, instructions §4)*

**Q84.** A78 says create `requirements-lock.txt` in PR1 with pinned transitive deps. The `canonicaljson` library (A41) may pull in transitive dependencies. Should the lockfile pin:
(a) Only direct dependencies (canonicaljson, PyYAML, etc.)?
(b) Full transitive closure (every package in the venv)?
(c) Full transitive closure plus Python version constraint?
*(A78, A41)*

---

*84 questions total (35 original + 12 R1 + 12 R2 + 13 R3 + 8 R4 + 4 R5). End of X-0E Q&A.*
