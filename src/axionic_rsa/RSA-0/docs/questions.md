# RSA-0 Implementation Questions

Questions arising from `spec.md` and `instructions.md` review.

---

## Constitution

1. **Where is the constitution content?** The spec references a constitution "incorporated by reference" and the instructions say to place it at `artifacts/phase-x/constitution/rsa_constitution.v0.1.yaml`, but no constitution YAML is provided. Is there an existing draft, or does it need to be authored from scratch? If authored, what are the minimal clauses required (e.g., allowed actions, network policy, budget limits, exit conditions)?

2. **Schema specifics:** The instructions call for `rsa_constitution.v0.1.schema.json`. How strict should the schema be? Should it validate only structural shape, or also enumerate allowed values for fields like action types, tool names, and scope identifiers?

3. **What does the authority store contain beyond the constitution?** The admission pipeline references "authority store / constitution" — is the constitution the *only* authority artifact in Phase X, or are there other fixed authority documents?

---

## Artifact Design

4. **Canonical serialization format:** The instructions say "JSON canonicalization or equivalent." Should we use RFC 8785 (JCS) specifically, or is a simpler deterministic JSON serialization (sorted keys, no whitespace) acceptable?

5. **Artifact ID = hash of canonical form — which hash?** SHA-256 is used for the constitution hash. Should all artifact IDs also use SHA-256, or is a shorter hash (e.g., truncated SHA-256, BLAKE3) acceptable?

6. **Author field granularity:** The instructions specify author as `kernel | reflection | user | host`. Is `reflection` synonymous with "LLM proposal"? Should there be a distinction between different LLM calls within the same cycle?

---

## Policy Core & Determinism

7. **What constitutes `internal_state`?** The policy core signature is `policy_core(observations, constitution, internal_state) → Decision`. What is `internal_state`? Is it the accumulated artifact/log history from prior cycles, or something more specific? How is it initialized on the first cycle?

8. **How does the policy core produce decisions without heuristics?** The spec forbids heuristics, learning, and nondeterminism in the policy core. But mapping observations to candidate action bundles requires *some* logic. Is the intent that the LLM proposes candidates and the policy core only performs structural admission + deterministic selection? If so, the policy core is essentially the admission pipeline + selector — is that the correct reading?

9. **Timestamp handling:** The spec says "if you need time, treat it as an observation input." Should the host inject a `TimestampObservation` at the start of each cycle, or only when time is relevant? Does the warrant `expiration` field imply the executor needs a time source — and if so, how is that reconciled with the purity constraint?

---

## Admission Pipeline

10. **Gate ordering strictness:** The five gates are listed sequentially. Must they execute in exactly that order, or is it sufficient that all five are checked (since a bundle must pass all of them)?

11. **What counts as "authority citation"?** The Authority Citation Gate requires citations to "exist" and "be in scope." Concretely, does this mean the `ScopeClaim` or `Justification` must contain a string identifier (e.g., `constitution.v0.1:clause:3.2`) that is looked up in the loaded constitution? What is the identifier format?

---

## Selector

12. **Hash scope for selection:** The selector hashes "each admitted candidate bundle (or the `ActionRequest` id)." Which is it — the full bundle hash or just the `ActionRequest.id`? These could differ if the same ActionRequest appears with different ScopeClaims or Justifications.

---

## Execution & Tools

13. **Warrant expiration semantics:** Warrants can expire "immediate single cycle." How is expiration checked if the executor doesn't have access to a clock (purity constraint)? Is the executor exempt from the purity requirement since it's the component that actually performs side effects?

14. **`Notify(stdout|local_log)` — two modes or two tools?** Is `Notify` a single tool with a `sink` parameter, or are `NotifyStdout` and `NotifyLocalLog` separate tools?

15. **`ReadLocal` scope:** What paths should be on the initial allowlist? Only `./workspace/`? Also `./artifacts/` (read-only)? The constitution itself?

16. **Logging as side effect:** The instructions acknowledge logging is a side effect but treat it as a "permitted low-risk side effect." Does logging bypass the warrant pipeline entirely, or does the kernel auto-issue an internal warrant for log writes? If bypassed, how is this reconciled with INV-1 ("No Side Effects Without Warrant")?

---

## LLM Integration

17. **How does the LLM receive context?** The spec says LLMs are "outside the pipeline." Concretely, what is the LLM prompt composed of? Does it receive the current observations, the constitution (or a summary), and prior cycle history? Who assembles the prompt — the host or the kernel?

18. **`max_candidates_per_cycle`:** This is referenced as a constitution parameter. What is its initial value? Is 1 sufficient for RSA-0, or should it allow multiple candidates to exercise the selector?

19. **Candidate parsing:** LLM output is "untrusted text" converted into candidate artifacts by the host. What is the expected format for LLM output? Structured JSON? Free text with a parser? How strict is parsing — does a malformed proposal become a `RefusalRecord` or is it silently dropped (which would violate "no silent dropping")?

---

## Replay

20. **Replay scope:** Does replay re-execute only the kernel decision pipeline (admission + selection + warrant issuance), or does it also re-execute the actual side effects? The spec says "re-execute the entire decision pipeline" — confirming this means the decision path only, not tool execution.

21. **Run ID and cycle ID generation:** These appear in logs. How are they generated deterministically? Is `run_id` a hash of the initial state, and `cycle_id` a sequential counter?

---

## Implementation Language & Scope

22. **Language choice:** Neither document specifies an implementation language. Is Python the expected choice (given the existing codebase), or is there a preference?

23. **Single-cycle vs. loop:** The instructions mention a "CLI loop" but the spec focuses on single-cycle semantics. For Phase X acceptance, is demonstrating correct single-cycle behavior sufficient, or must the agent run a multi-cycle loop autonomously?

24. **Exit trigger:** The spec says exit is permitted when "explicitly authorized by constitution" or "integrity risk detected." What constitutes an integrity risk in RSA-0? Hash mismatch on constitution? Replay divergence mid-run? Is there a concrete detection mechanism required?

---

## Follow-up Questions (from answers.md review)

### Constitution YAML

25. **`max_total_tokens_per_cycle` scope:** The constitution sets this to 6000. Does this count LLM output tokens only, or prompt input + output combined? If the latter, 6000 may be very tight once observations + constitution excerpt are included.

26. **`WriteLocal` in v0.1?** The constitution defines `WriteLocal` as an action type, but the instructions say "optionally add WriteLocal later." Should `WriteLocal` be implemented in v0.1, or should the action type exist in the constitution but be gated as unimplemented at the tool level?

27. **IO allowlist path base:** The constitution uses `./artifacts/` and `./workspace/`. Relative to what — the repo root (`axionic-rsa/`), or the working directory at runtime? Must paths be resolved to absolute at startup and frozen?

### Admission Pipeline (Kernel-Only Actions)

28. **LogAppend admission path:** The constitution defines `LogAppend` with `scope_claim: false` and `justification: false`, and marks it `kernel_only: true`. Does `LogAppend` go through the same five admission gates (with Scope Claim and parts of Completeness trivially passing), or does it follow a separate kernel-internal admission path? If the latter, how is that reconciled with the single-pipeline architecture in the spec?

29. **Exit as action type vs. decision type:** The spec defines `Decision ∈ { ACTION, REFUSE, EXIT }`, but the constitution lists `Exit` as an action type in `action_space`. Does an EXIT decision go through the full admission pipeline like a normal action (requiring `ScopeClaim`, `Justification`, and warrant), or is it a distinct decision pathway? If both, when does each apply?

### Authority Citations

30. **Citation path resolution — concrete examples:** The answer specifies the format `constitution:v0.1/<section_path>#<clause_id>`. Given the YAML's nested structure (arrays with objects containing `id` fields), what are the concrete citation paths for common cases? E.g., to cite `INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT`, is it `constitution:v0.1/invariants/0#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT` or `constitution:v0.1/invariants#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT`? Is there a canonical mapping from YAML structure to citation identifiers that should be generated at constitution load time?

### Budget & Anti-Filibuster

31. **Budget tracking granularity:** The `anti_filibuster_rule` says "if budgets are exhausted without an admitted ActionRequest, REFUSE with BUDGET_EXHAUSTED." Is `max_candidates_per_cycle` counted as total proposals parsed from LLM output (including malformed ones), or only well-formed candidates that enter admission? Similarly, is the token budget tracked by the host (which calls the LLM) and injected as an observation, or enforced structurally within the kernel?

### Selector

32. **Bundle hash comparison:** The answer says use the full bundle hash (SHA-256 of canonical JSON of ActionRequest + ScopeClaim + Justification + citations). Is the comparison performed on the hex-encoded hash string (lexicographic on hex chars), or on the raw bytes? And is the bundle hash computed by concatenating the individual canonical JSONs, or by canonicalizing a composite object containing all four components?

### Replay & State

33. **internal_state across replay:** The answer defines `internal_state` as `{cycle_index, last_decision, commitments}`. During replay, is `internal_state` reconstructed from logs cycle-by-cycle (i.e., replayed forward), or is it expected to be stored as a snapshot in the logs at each cycle boundary?

---

## Follow-up Questions (from Addendum B review)

### Admission Pipeline Mechanics

34. **Kernel-only gate position:** Answer 28 introduces a new "kernel-only gate" at the Completeness Gate for `LogAppend`. Should this be formalized as a Gate 0 (pre-completeness check on author/kernel_only), or folded into the existing Completeness Gate as an additional sub-check? The spec's closed set of five gates would need to accommodate this — is adding a sixth gate permitted, or must it be a sub-rule of an existing gate?

35. **LogAppend citation requirements:** LogAppend requires `authority_citations: true` per the constitution, but has `scope_claim: false` and `justification: false`. Which specific constitution clause should kernel-authored LogAppend actions cite? Is there an implicit "telemetry_policy" citation (e.g., `constitution:v0.1@/telemetry_policy/required_logs`), or must the kernel cite the invariant that mandates logging?

36. **ExitRecord structural validation — when?** Answer 29 says EXIT is a Decision (not a warranted action), but the ExitRecord must still satisfy the Exit action type's structural requirements (reason_code, citations, scope_claim, justification). At what point in the pipeline is this validation performed? Does the policy core self-validate the ExitRecord before emitting it, or does the ExitRecord pass through an abbreviated admission pipeline after the decision is made?

### Budget Observations

37. **`BudgetObservation` as a new observation subtype:** Answer 31 says the host injects `llm_output_token_count` as a `BudgetObservation`. The spec defines `Observation` as a single artifact class (Section 4.1). Should `BudgetObservation` be a typed field/tag within `Observation`, or does it require extending the artifact taxonomy? If the former, what is the schema for observation subtypes (user input, timestamp, budget, etc.)?

38. **Budget exhaustion vs. partial admission:** Answer 31 says "simplest is unconditional refusal when over budget." But what if the LLM produced 3 candidates within budget and 2 after exceeding it — are the first 3 still admissible, or does exceeding the budget retroactively taint the entire cycle? In other words, is budget a pre-filter (truncate candidates at budget boundary) or a cycle-level gate (all-or-nothing)?

### Citation Index

39. **Citation index as runtime artifact:** Answer 30 describes building a citation index at constitution load time. Is this index itself logged or hashed? If the index generation has a bug, citations could resolve incorrectly and silently admit invalid actions. Should the citation index be part of the startup integrity check (e.g., included in the constitution hash, or validated against a known-good index)?

40. **Pointer-style citations — scope:** Answer 30 allows `constitution:v0.1@<json_pointer>` for nodes without `id` fields. Several constitution sections lack IDs (e.g., `io_policy`, `amendment_policy`, individual entries in `forbidden_actions` arrays). Should IDs be added to these sections in the constitution YAML to avoid pointer-based citations entirely, or is mixed ID/pointer citation intentional?

### Exit Semantics

41. **Exit record logging:** If EXIT does not go through the executor (no warrant), who writes the ExitRecord to logs? The kernel directly? If so, this is a side effect (log write) without a warrant — or does the kernel issue a final `LogAppend` warrant for the ExitRecord before terminating? What is the ordering: emit ExitRecord, then log it, then halt?

### Host / CLI Cycle Flow

42. **Cycle initiation:** Who initiates each cycle — the host or the kernel? Concretely: does the host poll for user input, package it as observations, call the kernel, and then call the LLM? Or does the kernel request observations from the host? The data flow in the spec (Section 6.1) shows observations flowing into the policy core, but doesn't specify the outer control loop.

43. **No-input cycles:** Must every cycle have user input, or can the agent run cycles autonomously (e.g., processing prior observations or internal state transitions with no new external input)? The "CLI loop" framing suggests user-driven, but the "runs autonomously" acceptance criterion (Answer 23) suggests otherwise.

### Determinism Edge Cases

44. **JCS and Python:** RFC 8785 (JCS) requires specific handling of floating-point serialization (IEEE 754 double → shortest decimal). Python's `json.dumps` does not conform to JCS by default. Is there a specific Python JCS library mandated, or should we implement canonical serialization manually? If a library, which one — and is it acceptable to add it as a dependency?

45. **Hash stability across Python versions:** SHA-256 of canonical JSON bytes should be stable, but Python's default string encoding edge cases (e.g., surrogate pairs in JSON keys) could cause divergence. Should we mandate UTF-8 with surrogates rejected (strict mode), or allow them?

---

## Follow-up Questions (from Addendum C review)

### Observation Schema

46. **Observation `kind` enum — closed or open?** Answer 37 introduces `Observation.kind ∈ { user_input, timestamp, budget, system }`. Is this enum closed (only these four, matching the closed-world principle), or can the host introduce new kinds in future cycles? If closed, what does `system` cover — startup events, integrity check results, something else?

47. **Observation payload schema — per-kind validation?** Each observation kind implies a different payload structure (e.g., `budget` has `llm_output_token_count`, `user_input` has a text field, `timestamp` has an ISO datetime). Should the constitution or schema define per-kind payload schemas, or is the payload an opaque string/object validated only at consumption time?

### Budget Semantics

48. **Token budget: "do not parse" vs. already-parsed?** Answer 38 says if output tokens exceed budget, "do not parse candidates" and REFUSE. But the host must have already received the LLM output to count the tokens. Is the intent that the host counts tokens *before* parsing JSON, and if over budget, discards the raw text without attempting to parse? Or does the host parse first, count tokens from the API response metadata, and then discard the parsed result?

49. **Candidate truncation ordering:** Answer 38 says for `max_candidates_per_cycle`, "take the first N candidates in listed order." LLM output order is nondeterministic across runs. Does this mean the truncation point could vary if the LLM returns the same candidates in a different order? Is that acceptable because replay uses the *logged* candidate list (which preserves order), or should candidates be sorted canonically before truncation?

### Cycle Flow & LLM Invocation

50. **LLM call: every cycle or conditional?** Answer 42's binding loop shows the LLM call as step 3 (optional). Under what conditions does the host skip the LLM call? If user input is a direct command (e.g., "exit"), does the host convert it to an observation and still call the LLM, or can the host construct candidate bundles itself without LLM involvement?

51. **Host-constructed candidates:** If the host can construct candidate bundles directly (e.g., for user-requested exit), then the host is acting as a proposal source alongside the LLM. Should host-constructed candidates have `author: "host"` and go through the same admission pipeline, or is this a special path?

### ExitRecord Integrity Edge Case

52. **ExitRecord self-validation failure:** Answer 36 says if the policy core fails to construct a valid ExitRecord, it should still EXIT with `INTEGRITY_RISK` using "a minimal valid structure." What constitutes the minimal valid ExitRecord? Is there a hardcoded fallback ExitRecord template that doesn't depend on citation resolution (since citation index failure could be the cause), or must even the integrity-risk exit resolve citations?

### Reason Codes

53. **Reason code taxonomy — single enum or per-artifact?** The answers introduce reason codes across multiple contexts: Exit reason codes (constitution), refusal reason codes (RefusalRecord), and rejection reason codes (`CANDIDATE_PARSE_FAILED`, `CANDIDATE_BUDGET_EXCEEDED`, `INVALID_UNICODE`). Are these all values of a single shared `reason_code` enum, or are there separate enums for `ExitRecord.reason_code`, `RefusalRecord.reason_code`, and admission rejection `reason_code`?

### Logging Pipeline

54. **LogAppend warrant issuance — blocking or batched?** During a single cycle, the kernel may need to issue multiple LogAppend warrants (observations log, artifacts log, admission trace, selector trace, execution trace). Are these issued and executed sequentially within the cycle, or batched? If sequential, does each LogAppend go through the full admission pipeline independently (5 gates × 5 log writes = 25 gate evaluations per cycle)?

55. **LogAppend admission trace — infinite regress?** If LogAppend itself goes through the admission pipeline, and the admission pipeline produces traces that must be logged via LogAppend, there's a potential infinite regress (logging the log of the log). Is there a termination rule — e.g., LogAppend admission traces are accumulated in memory and written in a single batch at cycle end, without recursively logging their own admission?

---

## Follow-up Questions (from Addendum D review)

### LogAppend Batching & Admission

56. **Batched LogAppend — single warrant or five?** Answer 54 says the kernel issues "up to five LogAppend warrants (one per log_name)." Each warrant must go through the admission pipeline (Answer 28). Even batched, that's still five admission evaluations per cycle. Is that acceptable overhead, or should there be a single "CycleLogCommit" warrant that covers all five streams in one pass? If the latter, does that require a new action type (violating the closed set)?

57. **LogAppend JSONL payload — array-in-line?** Answer 54 says a single JSONL line "may encapsulate an array of entries for that stream." Standard JSONL is one JSON object per line. Embedding an array of entries in a single line breaks the line-per-event convention and complicates replay parsing. Should each LogAppend warrant carry multiple JSONL lines (one per entry), or is the array-in-line form binding?

### Meta-Trace & Next-Cycle Logging

58. **LogAppend meta-trace in next cycle:** Answer 55 says LogAppend meta-events are recorded in memory and included in the next cycle's admission trace. This means cycle N's admission trace contains both cycle N's actual admission events *and* cycle N-1's LogAppend meta-events. Does this cross-cycle bleed complicate replay, since replaying cycle N now requires knowledge of cycle N-1's logging outcome? How is this handled for cycle 0 (no prior cycle) and the final cycle (no next cycle to flush into)?

### Host-Constructed Candidates

59. **Host candidate format — same LLM JSON schema?** Answer 51 says host-constructed candidates go through the same admission pipeline with `author: "host"`. Must these candidates conform to the exact same JSON bundle schema as LLM candidates (ActionRequest + ScopeClaim + Justification + authority_citations), or can the host use an internal representation that bypasses parsing? If the former, is the host effectively serializing to JSON and re-parsing, or can it construct artifact objects directly?

60. **Direct commands — observation vs. candidate?** Answer 50 says the host can skip the LLM for "direct commands" like `exit` or `notify stdout "..."`. But user input is supposed to become an `Observation` (per instructions §8.1). Does a direct command produce *both* an Observation (recording what the user typed) *and* a host-constructed candidate bundle, or does the host skip the Observation for direct commands?

### Observation Payload Validation

61. **Observation validation — host or kernel?** Answer 47 mandates per-kind payload schemas. Who validates observations — the host before passing them to the kernel, the kernel at intake, or both? If the kernel validates and rejects an ill-formed observation, what is the appropriate response — REFUSE, EXIT, or simply drop the malformed observation (which would violate "no silent dropping")?

### System Observation Events

62. **System observation `event` enum completeness:** Answer 46 defines `system.event` values including `startup_integrity_ok/fail`, `citation_index_ok/fail`, `replay_ok/fail`, `executor_integrity_fail`. Are these emitted as Observations into the kernel's observation set, or are they pre-kernel host-level checks that prevent the kernel from running at all? If they're Observations, the kernel would need to process an `executor_integrity_fail` observation — but by that point the integrity violation has already occurred. What is the kernel's expected response to receiving a system observation indicating a past integrity failure?

### Reason Code Gaps

63. **RefusalRecord reason codes vs. admission rejection codes — relationship:** Answer 53 defines separate enums for RefusalRecord and admission rejection. A RefusalRecord is a cycle-level outcome ("no admissible action"), while admission rejections are per-candidate. But the RefusalRecord must include `failed_gate` and `missing_artifacts` (per the constitution's `refusal_output_requirements`). When all candidates are rejected at different gates for different reasons, which `failed_gate` does the cycle-level RefusalRecord cite — the gate that rejected the *last* candidate, the *most common* failure gate, or all of them?

64. **`INTEGRITY_RISK` in RefusalRecord:** Answer 53 lists `INTEGRITY_RISK` as both an Exit reason code and a Refusal reason code. Under what circumstances would the kernel REFUSE (rather than EXIT) for an integrity risk? The exit policy says integrity risk is a *mandatory* exit condition. Is `INTEGRITY_RISK` in the refusal enum dead code, or is there a scenario where refusal is preferred over exit for an integrity issue?

### Determinism Boundary

65. **LLM nondeterminism containment — acceptance test:** Answer 44 mandates a JCS library with test vectors. But the spec's acceptance criterion #4 is "LLM nondeterminism contained." Concretely, how is this tested? Is the test: given the same logged candidate set (fixing the LLM's output), replay produces identical decisions? Or must the test demonstrate that *different* LLM outputs (same prompt, different runs) still result in the same decision when the admitted subset is identical?

---

## Follow-up Questions (from Addendum E review)

### Constitution Versioning

66. **v0.1 → v0.1.1 patch implications:** Answers 57 and 64 introduce constitution changes (replace `jsonl_line` with `jsonl_lines`, remove `INTEGRITY_RISK` from RefusalRecord enum). How should patch-level constitution revisions work in Phase X where amendments are forbidden? Is "v0.1.1" a pre-freeze correction (the constitution was never truly frozen yet), or does this require a formal exception to the amendment policy? Must the spec and instructions docs also be updated to reference v0.1.1?

### LogAppend Schema Change

67. **`jsonl_lines: array<string>` — max warrant size:** Answer 57 sets max 200 lines per warrant at 20,000 chars each, yielding a theoretical max of ~4MB per LogAppend warrant. Is this ceiling intentional, or should there be a tighter per-warrant byte limit? In practice, should the kernel split large log batches across multiple warrants if they exceed a size threshold?

68. **LogAppend warrant content — lines vs. references:** Each LogAppend warrant now carries the full text of all JSONL lines for a stream. For large cycles (many candidates, verbose traces), this means the warrant itself becomes a large artifact. Should warrants carry the log content inline, or carry a hash/reference to content staged in memory, with the executor retrieving content by reference? The latter would keep warrants lightweight but adds a content-staging mechanism.

### Log Commit Summary

69. **`log_commit_summary` schema:** Answer 58 introduces a `log_commit_summary` object in `execution_trace`. What are the required fields? At minimum: `streams_written`, `lines_per_stream`, `line_hashes`. Should `log_commit_summary` also include the warrant IDs for the LogAppend warrants, creating a cross-reference between execution_trace and the warrants that produced log side effects?

70. **Replay verification of log commits:** Answer 58 says "replay verifies that LogAppend warrants correspond to expected committed lines." But if LogAppend produces no admission-trace entries, replay has no record of the admission decision for LogAppend warrants. Does replay simply trust that LogAppend warrants were correctly issued (since they're kernel-authored), or must replay re-derive the expected log content and verify it matches the committed lines?

### RefusalRecord Schema Update

71. **`rejection_summary_by_gate` — new required field:** Answer 63 adds `rejection_summary_by_gate` to RefusalRecord. This field isn't in the constitution's `refusal_output_requirements`. Should it be added to the constitution (another v0.1.1 change), or is it an implementation-level field that doesn't require constitutional authority?

### Observation Validation & Host Termination

72. **Host self-termination path:** Answer 61 says if the host detects an invalid observation, it "terminates (no kernel call)." But the spec says every exit must produce an ExitRecord with authority citations. If the host terminates before the kernel runs, who produces the ExitRecord? Is host-level termination exempt from ExitRecord requirements, or must the host construct one itself (making the host partially sovereign, which may conflict with the kernel-only authority model)?

### Nondeterminism Insulation Test

73. **Test B practicality:** Answer 65's "nondeterminism insulation test" requires two live executions with the same prompt where the LLM returns different candidate sets. LLM output isn't controllable — you can't guarantee different outputs on demand. Should this test use a mock/stub LLM that returns predetermined different candidate sets, or must it use a real LLM and simply run enough trials? If mocked, does that satisfy the "real RSA" acceptance criterion?

---

## Follow-up Questions (from Addendum F review)

### Constitution Patch Finalization

74. **v0.1.1 change set — is it complete?** Answers across addenda introduce several constitution changes: `jsonl_line` → `jsonl_lines` (A57), remove `INTEGRITY_RISK` from RefusalRecord enum (A64), add warrant size limits (A67). Are there any other pending changes, or is this the final v0.1.1 delta? Should a consolidated v0.1.1 YAML be produced before implementation begins, or can implementation proceed against v0.1 with the patches applied informally?

### Startup-Only Cycle

75. **Startup cycle as cycle 0?** Answer 72 introduces a "startup-only cycle" where the kernel runs with a single system observation and no candidates. Is this the same as cycle 0 in the normal flow (i.e., cycle 0 always begins with startup integrity observations), or is it a distinct pre-cycle that doesn't increment `cycle_index`? If it's cycle 0, then the first user-input cycle is cycle 1 — does this affect the "at least 3 cycles" acceptance criterion?

76. **Startup cycle decision path:** In the startup-only cycle with `startup_integrity_ok` + `citation_index_ok` observations and no candidates, the expected decision is REFUSE (no admissible action). This means every successful run begins with a mandatory refusal. Is that intentional, or should the startup cycle be a special "INIT" decision type (which would expand `Decision ∈ { ACTION, REFUSE, EXIT }` to include `INIT`)?

### Log Commit Verification

77. **Replay re-derives log lines — from what?** Answer 70 says replay must "re-derive expected log lines and verify hashes." But log content is constructed by the kernel during execution — it includes observation IDs, artifact IDs, admission trace details, etc. To re-derive this content, replay must re-run the entire kernel cycle *including* the log-line construction logic. Is the log-line construction considered part of the pure policy core (and thus subject to determinism), or is it a separate kernel function? If separate, what determinism guarantees does it carry?

### LogAppend Warrant Splitting

78. **Split warrant ordering and atomicity:** Answer 67 says the kernel must split large log batches across multiple warrants. If a cycle produces log content requiring 3 LogAppend warrants for a single stream, and the executor fails after writing warrant 1 and 2 but not 3, the log stream is now partially written. Is partial log writes an integrity risk (triggering EXIT on the next cycle), or is it acceptable because logs are append-only and the next run can detect incomplete writes?

### Implementation Readiness

79. **Sufficient to begin?** After 7 rounds of Q&A (73 questions, 6 addenda), is the spec + answers corpus now sufficient to begin implementation, or are there known open items that must be resolved first? Specifically: is a consolidated v0.1.1 constitution YAML a prerequisite, or can implementation start in parallel with constitution finalization?

---

## Final Clarifications (from Addendum G review)

### Constitution v0.1.1 Production

80. **Schema for `jsonl_lines`:** The v0.1.1 schema must validate the new `jsonl_lines: array<string>` field plus the three new limits (`max_lines_per_warrant`, `max_chars_per_line`, `max_bytes_per_warrant`). Should these limits appear as top-level constants in the constitution YAML (e.g., under a new `logappend_limits` section), or as nested fields within the `LogAppend` action type definition? The latter keeps them co-located but makes the action type definition heavier than the others.

### Cycle 0 Behavior

81. **Cycle 0 LogAppend startup summary — content?** Answer 76 allows cycle 0 to emit an ACTION(LogAppend) recording startup integrity events instead of REFUSE. What should this LogAppend contain — just the system observation data (`startup_integrity_ok`, `citation_index_ok`), or a richer startup manifest (constitution hash, resolved allowlists, citation index size, etc.)? A richer manifest aids debugging but adds implementation scope to cycle 0.

### Telemetry Derivation Function

82. **`derive_telemetry` inputs — traces as argument?** Answer 77 defines `derive_telemetry(cycle_inputs, decision, traces) → LogIntents`. What are `traces` here — the in-memory admission and selector trace objects from the current cycle? If so, `derive_telemetry` depends on the admission pipeline's internal state, meaning the pipeline must expose structured trace objects (not just log strings). Is there a defined interface for these trace objects, or should implementation define them freely as long as the output is deterministic?

### Partial Write Detection

83. **Previous-cycle warrant verification — who provides it?** Answer 78 says cycle-start system observations summarize the previous cycle's committed warrant IDs. The host must read the log files to determine which warrants were actually written. But log files are under `./logs/` (write-allowlisted), and the host reading them mid-run is a read operation outside the allowlist (`./logs/` is write-only in the constitution's `io_policy`). Should `./logs/` be added to `read_paths` in v0.1.1, or does the host have implicit read access to logs outside the constitution's IO policy (since the host is not the kernel and IO policy gates kernel-level actions, not host-level operations)?
