# RSA-0 Phase X Addendum: Answers to Opus Questions

## Constitution

### 1) Where is the constitution content?

It already exists as a draft (I provided it earlier in this thread). For the handoff, treat the **constitution YAML included at the end of this message** as the authoritative v0.1 starting point.

**Minimal clauses required in Phase X** (and included in the YAML):

* closed action set
* IO allowlists
* network disabled
* budgets (`max_candidates_per_cycle`, token budget)
* refusal policy (mandatory conditions + required fields)
* exit policy (permitted + mandatory conditions)
* selection policy (deterministic canonical selector)
* amendment policy (disabled)

### 2) Schema strictness?

**Strict.** The schema must validate:

* structural shape **and**
* enumerations for: action types, notify targets, refusal/exit reason codes, selector rule types
* bounds: max lengths, max candidates, token budgets
* booleans for network enabled, amendments enabled

It must **not** attempt to validate semantic truth (e.g., whether a ScopeClaim is “correct”). It validates *form*, allowed enums, and constraints.

### 3) Authority store beyond the constitution?

For Phase X: **constitution is the only authority artifact**.

There is **no separate authority store** in RSA-0. You can implement an “authority store” interface, but it must load exactly one document: `rsa_constitution.v0.1.yaml`.

(Phase XI introduces additional authority artifacts via amendment protocol; Phase X forbids them.)

---

## Artifact Design

### 4) Canonical serialization format?

Use **RFC 8785 JSON Canonicalization Scheme (JCS)**.

Reason: it eliminates ambiguity and makes replay/selection clean. Anything “homegrown deterministic JSON” tends to rot under edge cases.

### 5) Artifact ID hash algorithm?

Use **SHA-256** for all artifact IDs, untruncated.

Reason: (a) consistent with constitution hash, (b) avoids pointless bikeshedding, (c) collision paranoia is cheap here.

### 6) Author field granularity?

Use:

* `kernel`
* `host`
* `user`
* `reflection`

Yes: `reflection` means “LLM-originated proposal.”

Do **not** differentiate LLM calls in v0.1. If you want traceability, add optional fields:

* `reflection_session_id`
* `reflection_call_index`

But admission logic must not depend on those.

---

## Policy Core & Determinism

### 7) What is `internal_state`?

In RSA-0, keep it minimal and deterministic:

`internal_state` = a small struct derived from prior admitted artifacts, e.g.:

* `cycle_index` (int)
* `last_decision` (enum)
* optional: `commitments` (empty in Phase X unless you explicitly model them)

Initialize on first cycle as:

* `cycle_index = 0`
* `last_decision = NONE`
* `commitments = []`

Do **not** include raw log history in `internal_state`. That creates accidental dependence on logging.

### 8) How does policy core decide without heuristics?

Correct reading:

* The **LLM proposes** candidate bundles (untrusted).
* The Policy Core performs **structural admission + deterministic selection**.
* If zero admissible → REFUSE (or EXIT if mandated).

In RSA-0, the Policy Core is essentially:

> *Admission pipeline + selector + warrant issuance decision.*

That is intended. There is no additional “smartness” in Phase X.

### 9) Timestamp handling / warrant expiration?

Two rules:

* The **host injects a timestamp observation every cycle** (so time is part of the logged observation stream).
* **Warrant expiration is cycle-bound, not wall-clock-bound** in v0.1.

Define:

* warrant includes `issued_in_cycle`
* warrant valid only for that same `cycle_index`
* executor checks `warrant.issued_in_cycle == current_cycle_index`

This avoids requiring an executor clock for warrant validity.

Executor is allowed to read cycle_index from the host runtime context (not from system time).

---

## Admission Pipeline

### 10) Gate ordering strictness?

**Must be executed in the specified order** for trace comparability and deterministic failure reporting:

1. Completeness
2. Authority Citation
3. Scope Claim
4. Constitution Compliance
5. IO/Tool Allowlist

This makes refusal traces stable and comparable across implementations.

### 11) What counts as “authority citation”? Identifier format?

In Phase X, an authority citation is a reference to a clause in the constitution.

Use this identifier format:

`constitution:v0.1/<section_path>#<clause_id>`

Example:

* `constitution:v0.1/action_types/Notify#requires`
* `constitution:v0.1/selection_policy/default_selector_rule#DeterministicCanonical`

Practical requirement:

* citations are strings
* they must resolve to a real node in the loaded constitution document
* resolution can be implemented as JSONPointer-like lookup after YAML→JSON parsing

---

## Selector

### 12) Hash scope for selection: bundle or ActionRequest?

Use **full bundle hash**, not ActionRequest alone.

Reason: same `ActionRequest` paired with different `ScopeClaim`/`Justification` must be distinguishable; otherwise you create hidden preference by throwing away responsibility context.

Bundle definition for hashing:

* `ActionRequest` canonical JSON
* `ScopeClaim` canonical JSON
* `Justification` canonical JSON
* plus the list of authority citations

---

## Execution & Tools

### 13) Warrant expiration semantics / executor purity?

Executor is **not pure**. It performs side effects.

Purity constraints apply to **Policy Core**, not executor.

Expiration check is cycle-bound (see #9), so no wall clock required.

### 14) Notify: one tool or two?

One action type: `Notify` with field:

* `target ∈ { stdout, local_log }`

Implementation may route to different sinks internally, but externally it’s one action type.

### 15) ReadLocal allowlist?

Initial allowlist (Phase X v0.1):

* read: `./artifacts/` and `./workspace/`
* write: `./workspace/` and `./logs/`

Reading constitution is allowed via `./artifacts/`.

### 16) Logging as side effect vs INV-1

Do **not** bypass INV-1. Logging must not be a “special exemption.”

Solution: implement an internal tool/action pair used only by the kernel:

* Tool: `LogAppend`
* Action type: `LogAppend` (kernel-only)

Flow:

* kernel issues an internal warrant for `LogAppend` writes (append-only JSONL)
* executor performs log write only with warrant

This preserves INV-1 literally.

`LogAppend` is **not** available to reflection/user proposals in Phase X.

---

## LLM Integration

### 17) How does LLM receive context? Who assembles prompt?

The **host assembles** the prompt, not the kernel.

Prompt inputs (Phase X minimal):

* current cycle observations (canonical, with IDs)
* constitution excerpt: allowed action types + key prohibitions + budgets + selector rule
* last cycle decision summary (optional; from logs or internal_state)

Do **not** include the full constitution YAML in every prompt; include a stable excerpt to keep token usage bounded and deterministic.

### 18) `max_candidates_per_cycle` initial value?

Set to **5** in v0.1.

Reason: you need >1 to exercise selector determinism and “no silent dropping” traces. Setting it to 1 makes selector dead code.

### 19) Candidate parsing format and malformed proposals?

LLM must output **strict JSON** in a single top-level object:

```json
{
  "candidates": [ {bundle1}, {bundle2}, ... ]
}
```

Each bundle must contain:

* ActionRequest
* ScopeClaim
* Justification
* authority_citations (array of strings)

Malformed proposals are **not silently dropped**.

They become **rejected candidates** with a rejection trace entry at the Completeness Gate (or Parsing Gate, which is a pre-step inside Completeness).

Do not emit Refusal solely because one candidate is malformed; refuse only if **no admissible candidate** exists *after evaluation*.

---

## Replay

### 20) Replay scope: decision pipeline vs side effects?

Replay re-executes:

* admission
* selection
* warrant issuance
* expected decision outputs

Replay does **not** re-execute side effects.

Replay verifies that the same warrant would have been issued, and that the recorded execution trace corresponds to that warrant.

### 21) Run ID and cycle ID determinism?

* `cycle_id` = sequential counter starting at 0 (deterministic).
* `run_id` does not need to be deterministic. It can be UUIDv4.

Replay uses the recorded `run_id` from logs; determinism requirement is on decisions and warrants, not the cosmetic run identifier.

---

## Implementation Language & Scope

### 22) Language choice?

Default to **Python** for Phase X unless there is a strong operational reason otherwise.

Reason: fastest path to a correct reference implementation; Phase X is about invariants, not performance.

### 23) Single-cycle vs loop?

Must implement a **multi-cycle loop**.

Minimum acceptance:

* at least **3 cycles** in a single run
* where cycles include both:

  * an admitted action (Notify is sufficient)
  * a refusal (e.g., invalid candidate set)

You need multiple cycles to validate state handling + replay across transitions.

### 24) Integrity risk definition in RSA-0?

Integrity risk is defined as any of the following:

* constitution hash mismatch at startup
* canonicalization failure (cannot canonicalize an artifact deterministically)
* replay divergence detected in replay harness
* detection of side effect without warrant (executor attempted action without valid warrant)

Response:

* if detected at startup → refuse to start (hard fail)
* if detected mid-run → `EXIT` with reason `INTEGRITY_RISK` (if constitution permits; it does)

---

# Constitution YAML v0.1 (Authoritative for Opus)

Place this file at:
`artifacts/phase-x/constitution/rsa_constitution.v0.1.yaml`

```yaml
meta:
  name: "RSA Constitution"
  version: "0.1"
  phase: "X"
  date: "2026-02-10"
  authority_model: "closed"
  status: "FROZEN"
  notes:
    - "Phase X constitution: closed action set, non-privileged reflection, warrant-gated side effects."
    - "All unspecified behaviors are forbidden."

non_goals:
  forbidden_objectives:
    - "outcome_optimization"
    - "helpfulness_maximization"
    - "implicit_coordination"
    - "stability_at_any_cost"
    - "silent_recovery"
    - "hidden_ranking"
    - "unlogged_defaults"
  interpretive_rule:
    - "In ambiguity, refuse rather than infer."

invariants:
  - id: "INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT"
    statement: "No side effects may occur without a kernel-issued execution warrant referencing an admitted ActionRequest."
  - id: "INV-AUTHORITY-CITED"
    statement: "Every admitted action must cite explicit authority identifiers resolvable in this constitution."
  - id: "INV-NON-PRIVILEGED-REFLECTION"
    statement: "Reflection may propose and explain; it may not decide, select, execute, amend, or override refusal."
  - id: "INV-REPLAY-DETERMINISM"
    statement: "Given identical observations, artifacts, and seeds, policy outputs and warrants must be identical."

action_space:
  closed_world: true

  action_types:
    - type: "Notify"
      description: "Emit a message to an approved local sink."
      required_fields:
        - name: "target"
          type: "enum"
          allowed: ["stdout", "local_log"]
        - name: "message"
          type: "string"
          max_len: 2000
      requires:
        authority_citations: true
        scope_claim: true
        justification: true
      side_effect_class: "low"

    - type: "ReadLocal"
      description: "Read from an allowlisted local path; no network."
      required_fields:
        - name: "path"
          type: "string"
          constraints: ["must_be_under_allowlist_read"]
      requires:
        authority_citations: true
        scope_claim: true
        justification: true
      side_effect_class: "none"

    - type: "WriteLocal"
      description: "Write to an allowlisted local path."
      required_fields:
        - name: "path"
          type: "string"
          constraints: ["must_be_under_allowlist_write"]
        - name: "content"
          type: "string"
          max_len: 200000
      requires:
        authority_citations: true
        scope_claim: true
        justification: true
      side_effect_class: "medium"

    - type: "Exit"
      description: "Terminate the agent run intentionally."
      required_fields:
        - name: "reason_code"
          type: "enum"
          allowed:
            - "NO_ADMISSIBLE_ACTION"
            - "AUTHORITY_CONFLICT"
            - "BUDGET_EXHAUSTED"
            - "INTEGRITY_RISK"
            - "USER_REQUESTED"
      requires:
        authority_citations: true
        scope_claim: true
        justification: true
      side_effect_class: "terminal"

    - type: "LogAppend"
      description: "Append-only JSONL logging. Kernel-only. Not available to reflection proposals."
      required_fields:
        - name: "log_name"
          type: "enum"
          allowed:
            - "observations"
            - "artifacts"
            - "admission_trace"
            - "selector_trace"
            - "execution_trace"
        - name: "jsonl_line"
          type: "string"
          max_len: 20000
      requires:
        authority_citations: true
        scope_claim: false
        justification: false
      side_effect_class: "low"
      kernel_only: true

refusal_policy:
  refusal_is_first_class: true
  mandatory_refusal_conditions:
    - "no_admissible_action_exists"
    - "missing_required_artifact"
    - "authority_citation_invalid_or_missing"
    - "scope_claim_missing_or_invalid"
    - "constitution_violation_detected"
    - "execution_warrant_unavailable"
    - "budget_exhausted"
  refusal_output_requirements:
    include:
      - "refusal_reason_code"
      - "failed_gate"
      - "missing_artifacts"
      - "authority_ids_considered"
      - "observation_ids_referenced"

exit_policy:
  exit_permitted: true
  exit_mandatory_conditions:
    - "integrity_risk_detected"
  exit_preferred_over:
    - "constitution_violation"
    - "unknown_side_effect_path"

amendment_policy:
  amendments_enabled: false
  forbidden_actions:
    - "AmendConstitution"
    - "ModifyAuthorityStore"
    - "InstallTool"
    - "EnableNetwork"
    - "ChangeSelectorRule"

reflection_policy:
  llm_allowed: true
  llm_role:
    - "propose_actions"
    - "propose_justifications"
    - "propose_refusals"
    - "propose_scope_claims"
  llm_forbidden:
    - "execute"
    - "select"
    - "amend"
    - "override_refusal"
    - "trigger_side_effects"
  proposal_budgets:
    max_candidates_per_cycle: 5
    max_total_tokens_per_cycle: 6000
  anti_filibuster_rule:
    - "If budgets are exhausted without an admitted ActionRequest, REFUSE with BUDGET_EXHAUSTED."

selection_policy:
  selector_rule_required: true
  default_selector_rule:
    type: "DeterministicCanonical"
    key: "bundle_hash_lexicographic_min"
    rationale: "Selection is procedural, not preferential."
  forbidden_selector_features:
    - "natural_language_scoring"
    - "learned_reward_models"
    - "implicit_utility"

io_policy:
  allowlist:
    read_paths:
      - "./artifacts/"
      - "./workspace/"
    write_paths:
      - "./workspace/"
      - "./logs/"
  network:
    enabled: false

telemetry_policy:
  required_logs:
    - "observations"
    - "artifacts"
    - "admission_trace"
    - "selector_trace"
    - "execution_trace"
  replay:
    required: true
```

---
---

# Addendum B — RSA-0 Clarifications (Q25–Q33)

## 25) `max_total_tokens_per_cycle` scope

**Counts LLM output tokens only.**
Prompt input tokens are not counted against this budget.

Rationale: input token accounting varies by provider and is not kernel-verifiable; output tokens are observable at the host boundary and can be logged deterministically.

Operational rule:

* Host must log `llm_output_token_count` per cycle.
* If `llm_output_token_count > max_total_tokens_per_cycle` → **budget exhausted** and treated per refusal rules.

Keep `6000` as-is for v0.1.

---

## 26) `WriteLocal` in v0.1?

**Yes: implement `WriteLocal` in v0.1.**
Do not ship an “in-constitution but unimplemented” action type.

Rationale: having action types that cannot execute creates an ambiguous failure class (is refusal lawful or implementation-incomplete?). Phase X wants clean falsifiability.

Constraint:

* `WriteLocal` may write **only** under `./workspace/` and `./logs/` per allowlist.
* No overwrite semantics beyond “write file” unless you specify them; simplest is:

  * create or replace whole file content
  * path must be under allowlist

---

## 27) IO allowlist path base

Paths are resolved **relative to the repo root** (the directory containing `artifacts/`).

Binding rule:

* On startup, the host computes `repo_root` as the nearest ancestor directory that contains `./artifacts/phase-x/constitution/`.
* Convert allowlist entries to **absolute canonical paths** at startup (realpath).
* Freeze them in memory as the effective allowlist for the run.
* Every runtime path must be:

  * resolved to absolute canonical path
  * checked as a descendant of an allowlisted canonical path

No dependence on current working directory after startup.

---

## 28) `LogAppend` admission path

`LogAppend` uses the **same admission pipeline**, with two special rules:

1. **Kernel-only gate (new, mandatory)**

   * If `ActionRequest.type == LogAppend` then `author` must be `kernel`.
   * Any `reflection`-authored LogAppend candidate is rejected at **Completeness Gate** with reason `KERNEL_ONLY_ACTION`.

2. `scope_claim` and `justification` requirements are skipped because constitution declares them false for LogAppend.

Everything else (citations, constitution compliance, IO allowlist) still applies.

This preserves the single-pipeline architecture and keeps INV-1 literal.

---

## 29) Exit as action type vs decision type

Exit is a **Decision**, not a side-effect action.

Binding behavior:

* `Decision = EXIT` emits an `ExitRecord` and terminates the run.
* EXIT does **not** issue an ExecutionWarrant and does **not** go through tool execution.

Why keep `Exit` in `action_types` then?

* Only to bind the **required fields and reason codes** structurally (schema-level), and to require authority citations + scope claim + justification in the `ExitRecord`.

Implementation rule:

* Treat EXIT as an internal kernel outcome whose *record* must satisfy the same structural requirements listed for `Exit` in the constitution:

  * reason_code enum
  * authority citations required
  * scope claim required
  * justification required

No warrant, no executor.

---

## 30) Citation resolution — concrete mapping

Yes: you need a canonical mapping generated at constitution load time.

Binding approach:

* Convert constitution YAML to a normalized JSON object.
* Build a **citation index** that maps stable IDs to JSONPointer paths.

Rules:

1. Any object with an `id` field is addressable by that id.
2. Arrays are traversed; index is allowed internally but citations must use IDs when available.
3. Citation format is:

`constitution:v0.1#<id>`

with optional pointer for non-ID nodes:

`constitution:v0.1@<json_pointer>`

**Preferred**: ID citations. Pointers only when no `id` exists.

Concrete examples:

* Cite invariant `INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT` as:

  * `constitution:v0.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT`
* Cite selector rule default node (no id in YAML) as:

  * `constitution:v0.1@/selection_policy/default_selector_rule`

Opus should implement:

* `resolve_citation(citation_string) -> node` using this index.

This removes ambiguity and decouples citations from YAML array ordering.

---

## 31) Budget tracking granularity

Two budgets exist:

### A) Candidate count (`max_candidates_per_cycle`)

Counts **all parsed candidates**, including malformed candidates that can be assigned an ID.

Operationally:

* LLM output JSON is parsed into an array.
* Each candidate becomes either:

  * a well-formed candidate bundle, or
  * a “malformed candidate” record with parsing error details
* Both count toward `max_candidates_per_cycle`.

Rationale: otherwise a malicious model can filibuster with malformed spam “for free.”

### B) Token budget (`max_total_tokens_per_cycle`)

Enforced by the **host** (it called the LLM).

* Host logs `llm_output_token_count`.
* Host injects this as a `BudgetObservation` for the cycle (deterministic input to policy).
* If over budget, the policy must REFUSE with `BUDGET_EXHAUSTED` unless an admissible action exists that does not depend on further reflection. For v0.1, simplest is unconditional refusal when over budget.

---

## 32) Bundle hash comparison details

* Compute bundle hash as **SHA-256 over canonical JSON of a single composite object**:

```json
{
  "action_request": {...},
  "scope_claim": {...},
  "justification": {...},
  "authority_citations": [...]
}
```

* Canonicalize with RFC 8785 (JCS).
* Hash raw bytes of canonical JSON (UTF-8).
* Compare hashes by **raw bytes lexicographic order** (not hex string).

Hex encoding may be used for display/logging only.

---

## 33) `internal_state` across replay

Reconstruct `internal_state` **by replaying forward**, cycle-by-cycle.

Do **not** store state snapshots as authority.

Rules:

* `cycle_index` increments deterministically.
* `last_decision` is the previous cycle’s decision.
* `commitments` remains empty in v0.1 unless you explicitly add commitment artifacts (not required for Phase X).

Replay algorithm:

1. initialize internal_state = {cycle_index: 0, last_decision: NONE, commitments: []}
2. process cycle 0 → decision0
3. update internal_state deterministically
4. process cycle 1 → decision1
   … etc.

If Opus wants convenience snapshots for debugging, they may be logged as non-authoritative telemetry, but replay must not depend on them.

---
---

# Addendum C — RSA-0 Clarifications (Q25–Q45)

## Re-stated answers (Q25–Q33)

**25. Token budget scope:** counts **LLM output tokens only**. Host logs `llm_output_token_count`.
**26. WriteLocal v0.1:** **implement it** in v0.1 (no “declared but unimplemented” actions).
**27. Allowlist base:** relative to **repo root** (directory containing `artifacts/…`). Resolve to absolute canonical paths at startup and freeze.
**28. LogAppend admission:** same 5-gate pipeline; kernel-only enforced as a **Completeness sub-check**; scope/justification skipped per constitution.
**29. Exit:** EXIT is a **Decision** (no warrant/executor). ExitRecord must satisfy Exit structural requirements.
**30. Citations:** use `constitution:v0.1#<id>` preferred; pointer form `constitution:v0.1@<json_pointer>` allowed only when no id exists. Build a citation index at load.
**31. Budgets:** candidate count counts **all parsed candidates incl malformed**; token budget enforced by host and injected as an Observation.
**32. Selector hash:** SHA-256 over JCS of a **single composite object**; compare **raw bytes** lexicographically.
**33. internal_state replay:** reconstruct by replaying forward cycle-by-cycle; no authoritative snapshots.

---

## Admission Pipeline Mechanics

### 34. Kernel-only gate position

**Fold into the existing Completeness Gate as a mandatory sub-check.**
No sixth gate. Maintain the closed five-gate taxonomy.

Rule:

* At Completeness Gate, after parsing, enforce:

  * if `ActionRequest.type` has `kernel_only: true` then `ActionRequest.author == "kernel"` else reject.

### 35. LogAppend citation requirements

Kernel-authored `LogAppend` must cite **both**:

1. `constitution:v0.1#INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT` (why logging is still warrant-gated)
2. `constitution:v0.1@/telemetry_policy/required_logs` (why these logs exist)

If Opus prefers fewer citations, minimum is (2) only, but the binding requirement is **both** in v0.1 to keep intent legible in audits.

### 36. ExitRecord structural validation — when?

**Policy core must self-validate ExitRecord before emitting EXIT.**
No post-decision admission pipeline.

Concretely:

* When policy core determines EXIT:

  * construct `ExitRecord`
  * validate against constitution Exit requirements (reason_code enum, citations present/resolvable, scope_claim present/valid form, justification present)
  * if validation fails, that is an **integrity risk** → EXIT with `INTEGRITY_RISK` is still required, but the ExitRecord must then cite the failure and use a minimal valid structure.

Net: policy core never emits an ill-formed ExitRecord.

---

## Budget Observations

### 37. BudgetObservation subtype handling

Do **not** extend artifact taxonomy.

Implement `Observation` with a required field:

* `kind` ∈ { `user_input`, `timestamp`, `budget`, `system` }

`BudgetObservation` is:

* `Observation.kind = "budget"`
* payload schema:

  * `llm_output_token_count: int`
  * `llm_candidates_reported: int`
  * `llm_parse_errors: int`

This keeps “Observation” as a single artifact class while still typing subcases.

### 38. Budget exhaustion vs partial admission

**Budget is a cycle-level gate, all-or-nothing, for output-token budget.**

Rule:

* If `llm_output_token_count > max_total_tokens_per_cycle`:

  * **do not parse** candidates
  * emit REFUSE with `BUDGET_EXHAUSTED`

For `max_candidates_per_cycle`:

* Parse the JSON, take the first N candidates in listed order (N = max), mark the remainder as **rejected with reason `CANDIDATE_BUDGET_EXCEEDED`** in the admission trace (they still “count,” but are deterministically excluded).

This prevents nondeterminism about “which ones slipped in before budget ran out.”

---

## Citation Index

### 39. Citation index integrity

The citation index is **derived** from the constitution and must not be separately hashed as an authority artifact.

But it must be part of startup integrity checks:

* After generating the index, run a deterministic “self-test”:

  * resolve every `id`-citation present in the constitution itself (all `invariants[*].id` at minimum)
  * resolve a fixed set of pointer citations used by the system (telemetry_policy required_logs, selection default rule)
* If any resolution fails → hard startup failure (refuse to start).

This prevents silent mis-resolution.

### 40. Pointer citations vs adding IDs everywhere

**Mixed ID/pointer citations are intentional for v0.1.**

Do not retrofit IDs across every node in the YAML now; that’s churn and doesn’t buy you structural safety. Pointer citations are acceptable **only** for:

* a small stable set of nodes used by system internals (telemetry_policy, selection default, io_policy allowlist).

Constraint:

* Pointer citations must reference nodes whose paths are stable under v0.1; changing them is an amendment in Phase XI, not Phase X.

---

## Exit Semantics

### 41. Exit record logging without violating INV-1

Exit logging must still respect INV-1.

Binding ordering:

1. Policy core emits `Decision = EXIT` with `ExitRecord` (pure, no IO)
2. Kernel issues a **LogAppend warrant** for writing the ExitRecord to `execution_trace` (and optionally `artifacts`)
3. Executor performs the log write(s)
4. Host terminates the run

So: EXIT causes side effects only via `LogAppend` warrants.

---

## Host / CLI Cycle Flow

### 42. Cycle initiation (outer loop control)

The **host** initiates cycles.

Binding loop:

1. host collects external inputs (CLI line or no-input tick)
2. host creates Observations (including timestamp, budget observation after LLM call if used)
3. host calls LLM (optional; see below)
4. host parses LLM output into candidate bundles
5. host calls kernel `policy_core(...)` with:

   * observations
   * candidate bundles (as artifacts / structured inputs)
   * internal_state
6. if ACTION: kernel issues warrant → host executes via executor
7. if REFUSE: host logs refusal (via LogAppend warrant)
8. if EXIT: host logs exit (via LogAppend warrant) then terminates

Kernel does not pull observations; it remains a pure function plus warrant issuance logic.

### 43. No-input cycles

For Phase X acceptance, allow **no-input cycles** but do not require them.

Binding behavior:

* A cycle may run with only:

  * timestamp observation
  * (optional) system observation
* If no user input is present, the default expected outcome is **REFUSE** (unless constitution permits some autonomous action; v0.1 does not).

Acceptance requires multi-cycle behavior; at least one cycle can be no-input to prove the loop isn’t blocked on stdin.

---

## Determinism Edge Cases

### 44. JCS and Python library

Mandate a library.

Use the Python package: **`jcs`** (RFC 8785 implementation) *if available*, otherwise **`canonicaljson`** is acceptable **only if** it conforms to RFC 8785 semantics for numbers and escaping.

Binding requirement:

* Opus must include a unit test vector from RFC 8785 examples (or a minimal subset) to prove conformance.

No manual implementation in v0.1.

### 45. UTF-8 and surrogate handling

Mandate strict UTF-8 with surrogates rejected.

Rules:

* All canonical JSON is UTF-8.
* Reject invalid Unicode/surrogate code points at parse time.
* If the LLM outputs invalid Unicode → candidate is malformed; counts toward candidate budget; rejected at Completeness with `INVALID_UNICODE`.

This prevents cross-runtime divergence.

---

## One final binding cleanup (so Opus doesn’t stall)

If Opus needs one more crisp artifact: define **reason codes** for rejections and refusals.

* Refusal reason codes: use the `Exit.reason_code` list plus:

  * `CANDIDATE_PARSE_FAILED`
  * `CANDIDATE_BUDGET_EXCEEDED`
  * `INVALID_UNICODE`

But do not expand beyond what’s necessary in Phase X.

---
Below are **binding answers** to Q46–Q55. This is **Addendum D**. It tightens Phase X without changing objectives.

---

# Addendum D — RSA-0 Clarifications (Q46–Q55)

## Observation Schema

### 46) Observation.kind enum — closed or open?

**Closed for Phase X.** Only:

`{ user_input, timestamp, budget, system }`

`system` covers:

* startup integrity check results (pass/fail flags, constitution hash verified)
* replay/self-test outcomes for the citation index
* executor integrity events (attempted side effect without warrant, warrant invalid)

Anything outside the enum is **invalid observation** → triggers **EXIT with INTEGRITY_RISK** (because the host violated the closed-world interface to the kernel).

### 47) Per-kind payload validation?

**Yes: per-kind schema is mandatory.** Define it in code and (optionally) in JSON schema for `Observation`.

Binding payload schemas:

* `user_input` payload:

  * `text: string` (max_len 4000)
  * `source: enum { cli }` (Phase X only)
* `timestamp` payload:

  * `iso8601_utc: string` (must be UTC, `YYYY-MM-DDTHH:MM:SSZ`)
* `budget` payload:

  * `llm_output_token_count: int` (>=0)
  * `llm_candidates_reported: int` (>=0)
  * `llm_parse_errors: int` (>=0)
* `system` payload:

  * `event: enum { startup_integrity_ok, startup_integrity_fail, citation_index_ok, citation_index_fail, replay_ok, replay_fail, executor_integrity_fail }`
  * `detail: string` (max_len 2000)

Payload is not opaque in Phase X. Form must be validated.

---

## Budget Semantics

### 48) Token budget “do not parse” ordering

Binding order:

1. Host receives raw LLM output text
2. Host obtains output token count from provider metadata **or** local tokenizer
3. If `llm_output_token_count > max_total_tokens_per_cycle`:

   * **do not JSON-parse**
   * discard raw output (but log its hash + token count)
   * emit `budget` observation and REFUSE with `BUDGET_EXHAUSTED`

So yes: count tokens before parsing.

### 49) Candidate truncation ordering (LLM order nondeterminism)

This is fine because **replay uses the logged candidate list**.

Phase X determinism is defined over the *observed inputs*, not over the LLM’s latent distribution. The LLM is outside the kernel; the host logs the candidate bundles it actually received.

Therefore:

* do **not** sort candidates before truncation
* truncate in listed order
* log the order explicitly

Sorting would introduce a second selector-like layer outside the kernel; avoid it.

---

## Cycle Flow & LLM Invocation

### 50) LLM call — every cycle or conditional?

Conditional.

Binding rule:

* Host calls LLM only when it does **not** already have at least one candidate bundle from a deterministic source.

Examples where host skips LLM:

* user input is a structured “direct command” the host can deterministically compile into a candidate bundle, e.g.:

  * `exit`
  * `notify stdout "..."` (if you support this CLI form)

If user input is freeform natural language, host may call LLM.

### 51) Host-constructed candidates

Yes, allowed and preferred for deterministic cases.

Rules:

* Host-constructed candidates must set `author: "host"`.
* They go through the **same admission pipeline** with no special path.
* The host is just another proposal source; it has no authority.

This reduces LLM dependence while preserving invariants.

---

## ExitRecord Integrity Edge Case

### 52) Minimal valid ExitRecord when self-validation fails

Define a hardcoded fallback template that does **not require citation resolution**.

Binding minimal ExitRecord:

* `type = ExitRecord`
* `reason_code = INTEGRITY_RISK`
* `authority_citations = ["constitution:v0.1@/exit_policy/exit_mandatory_conditions"]` **(string literal allowed even if not resolvable)**
* `scope_claim`:

  * minimal object:

    * `observation_ids: []`
    * `claim: "INTEGRITY_RISK: citation resolution or record construction failed"`
* `justification`:

  * minimal string: `"Integrity risk: unable to construct a fully validated ExitRecord."`

Key point: **Do not block exit** on citation resolution. Integrity-risk exit must be survivable even when the citation index is the failing component.

This is the only exception where a citation may be present as an opaque string and not resolvable.

---

## Reason Codes

### 53) Single enum or per-artifact?

Separate enums. Closed sets.

* `ExitRecord.reason_code`: exactly the `Exit` allowed list in constitution.
* `RefusalRecord.reason_code`: separate enum:

  * `NO_ADMISSIBLE_ACTION`
  * `MISSING_REQUIRED_ARTIFACT`
  * `AUTHORITY_CITATION_INVALID`
  * `SCOPE_CLAIM_INVALID`
  * `CONSTITUTION_VIOLATION`
  * `EXECUTION_WARRANT_UNAVAILABLE`
  * `BUDGET_EXHAUSTED`
  * `INTEGRITY_RISK`
* Admission rejection reason codes (per-candidate, not per-cycle):

  * `CANDIDATE_PARSE_FAILED`
  * `INVALID_UNICODE`
  * `CANDIDATE_BUDGET_EXCEEDED`
  * `KERNEL_ONLY_ACTION`
  * `MISSING_FIELD`
  * `INVALID_FIELD`
  * `CITATION_UNRESOLVABLE`
  * `PATH_NOT_ALLOWLISTED`

Do not unify them; keep them typed to avoid semantic bleed.

---

## Logging Pipeline

### 54) LogAppend warrant issuance — sequential or batched?

**Batched.** One LogAppend warrant per log stream **per cycle**, max five warrants.

Mechanism:

* kernel accumulates log lines in memory during the cycle
* at cycle end, kernel issues up to five LogAppend warrants (one per log_name) containing **a single JSONL line** that itself may encapsulate an array of entries for that stream

This avoids 25 gate evaluations and simplifies traces.

### 55) Infinite regress risk (logging the log of the log)

Termination rule:

* The admission/selector/execution traces for `LogAppend` itself are **not logged via LogAppend in the same cycle**.
* Instead, record `LogAppend` meta-events into an in-memory “meta-trace” and include them as part of the *next cycle’s* admission trace (or in a reserved field inside the current cycle’s execution_trace payload, but not recursively).

Simpler binding rule for v0.1:

* LogAppend actions are treated as **telemetry sink commits** that do not themselves generate admission-trace entries beyond a single “log_commit” summary line in `execution_trace`.

No recursive logging.

---
Good. These are the right “boring edge” questions. Below are **binding answers** Q56–Q65. This is **Addendum E**. It preserves the closed-world principles and removes the remaining ambiguities.

---

# Addendum E — RSA-0 Clarifications (Q56–Q65)

## LogAppend batching & admission

### 56) Batched LogAppend — single warrant or five?

Keep **up to five** `LogAppend` warrants (one per log stream). Do **not** introduce `CycleLogCommit` (no new action type in Phase X).

Overhead is acceptable: 5 admissions per cycle is negligible and keeps the model simple and fully uniform under INV-1.

Binding rule:

* Exactly one LogAppend warrant per stream **only if that stream has entries** in that cycle.
* Zero-entry streams issue no warrant.

### 57) LogAppend payload — array-in-line vs multiple lines

Use **standard JSONL semantics**: **one JSON object per line**.

Therefore:

* A single `LogAppend` warrant may carry **multiple JSONL lines** as a list of strings (not one string containing an array).
* Executor appends each line independently in the given order.

Update the LogAppend action schema (v0.1) as:

* replace `jsonl_line: string` with `jsonl_lines: array<string>` (max_len per line 20000; max_lines per warrant 200)

This is a constitution revision. Treat it as **v0.1.1** (patch-level) and re-hash.

---

## Meta-trace & regress

### 58) Meta-trace next-cycle bleed

Eliminate the cross-cycle bleed. It was a convenience, not a requirement.

Binding rule (v0.1.1):

* LogAppend actions produce **no admission-trace entries at all**.
* Instead, they produce a single `log_commit_summary` object appended to `execution_trace` for the same cycle, describing:

  * which streams were written
  * how many lines per stream
  * hashes of the committed lines (optional)

This ends regress cleanly:

* No “logging the logging of the logging”
* No cross-cycle dependency
* No special cases for cycle 0 or final cycle

Replay does not need to model logging internals beyond verifying that LogAppend warrants correspond to expected committed lines.

---

## Host-constructed candidates

### 59) Host candidate format — same schema? JSON roundtrip?

Host-constructed candidates must conform to the **same logical bundle schema** (ActionRequest + ScopeClaim + Justification + citations), but **no JSON stringify/parse roundtrip is required**.

Binding rule:

* Host may construct artifact objects directly in memory.
* Canonicalization/hashing is performed by the kernel on these objects using JCS serialization.
* Logging outputs canonical JSON for replay.

### 60) Direct commands — observation vs candidate?

Direct commands produce **both**:

1. a `user_input` Observation recording exactly what the user typed, and
2. a host-constructed candidate bundle.

Never skip the Observation. Observations are the immutable external record; candidates are proposals.

---

## Observation payload validation

### 61) Validation — host, kernel, or both? Response to invalid observation

Both validate.

Binding behavior:

* Host validates before calling kernel; if invalid → host emits a `system` observation `startup_integrity_fail`-style **for the current run** and terminates (no kernel call).
* Kernel also validates at intake; if any observation is invalid → **EXIT with INTEGRITY_RISK** (not REFUSE, not drop).

No silent dropping. Invalid observation is a host/kernel interface breach.

---

## System observation events

### 62) System events are pre-kernel or observations?

Split them:

**Pre-kernel hard checks (prevent kernel run):**

* `startup_integrity_fail` (constitution hash mismatch)
* `citation_index_fail` (citation resolution self-test failure)

These abort before any cycles.

**In-run observations (fed to kernel):**

* `startup_integrity_ok` (cycle 0)
* `citation_index_ok` (cycle 0)
* `replay_fail` (if detected during a run—rare; typically post-run)
* `executor_integrity_fail` (if executor detects an invalid warrant attempt)

Kernel response to any in-run system event that indicates an integrity failure (`executor_integrity_fail`, `replay_fail`):

* **EXIT with INTEGRITY_RISK immediately.**

Yes, the failure is already in the past; the response is still required to prevent continuation under corruption.

---

## Reason code gaps

### 63) Cycle-level RefusalRecord: which failed_gate when multiple candidates fail differently?

RefusalRecord must report the **earliest gate at which all candidates are eliminated**.

Binding rule:

* Compute, for each gate i, the set of candidates remaining after gate i.
* Find the smallest i where remaining set is empty.
* Set `failed_gate = gate_i`.

Additionally, RefusalRecord must include a new field:

* `rejection_summary_by_gate`: counts per gate

This preserves “single failed_gate” while not losing information.

### 64) `INTEGRITY_RISK` in RefusalRecord — dead code?

Yes: **dead code for Phase X**.

Binding rule:

* Any integrity risk triggers **EXIT**, not REFUSE.
* Remove `INTEGRITY_RISK` from RefusalRecord.reason_code enum in v0.1.1.

This aligns with exit_policy “integrity risk mandatory exit.”

---

## Determinism boundary / acceptance test

### 65) “LLM nondeterminism contained” — concrete test

The acceptance test is:

**A) Candidate-set determinism test (kernel property)**

* Given the same logged candidate set and observations, replay produces identical:

  * admitted set
  * selected bundle hash
  * decision
  * warrants

This is mandatory.

**B) Nondeterminism insulation test (system property)**

* Run two live executions with the same prompt+observations where LLM returns different candidate sets.
* Verify that in each run:

  * only admitted bundles can cause side effects
  * refusal occurs when none admissible
  * all side effects have warrants

This is not “same decision despite different LLM outputs.” It is:

> different LLM outputs cannot bypass sovereignty, and cannot introduce unlogged authority.

So “contained” means “unable to create un-audited authority,” not “output-stable.”

---
Below are **binding answers** to Q66–Q73. This is **Addendum F**. It also cleanly resolves the “amendments forbidden but we changed the constitution” tension by defining **a single pre-freeze correction window**.

---

# Addendum F — RSA-0 Clarifications (Q66–Q73)

## Constitution Versioning

### 66) v0.1 → v0.1.1 in Phase X: allowed or not?

**Allowed as a pre-freeze correction.** No exception mechanism is introduced.

Binding rule:

* The constitution is considered **“provisional” until the first successful end-to-end run passes the Phase X sovereignty sanity test suite.**
* During the provisional window, patch-level corrections `v0.1.x` are permitted **only** to fix specification mismatches and determinism hazards discovered by implementation review.
* Once the first passing run is achieved, the constitution becomes **FROZEN** and further changes require Phase XI amendment machinery (not available in Phase X).

Therefore:

* Treat `v0.1.1` as the **first truly frozen** Phase X constitution.
* Yes: update spec/instructions to reference `v0.1.1` (file paths, hash filenames). No ambiguity.

---

## LogAppend Schema Change

### 67) `jsonl_lines` max warrant size / splitting

Yes, 4MB is too large as a practical ceiling.

Binding constraints (v0.1.1):

* `max_lines_per_warrant = 50`
* `max_chars_per_line = 10_000`
* `max_bytes_per_warrant = 256_000` (256 KB, UTF-8)

Kernel must split batches across multiple warrants when any limit would be exceeded.

This keeps warrants tractable and avoids pathological memory spikes.

### 68) Inline log content vs references

**Inline content is binding for Phase X.** No staging-by-reference.

Rationale: reference-based staging introduces a second side-channel storage mechanism that becomes a new integrity surface (naming, retrieval, lifetime, hashing, etc.). Phase X wants one thing: warrants cause side effects, fully explicit.

So:

* LogAppend warrants carry the actual JSONL lines (within the size limits above).
* If too large, split into multiple warrants.

---

## Log Commit Summary

### 69) `log_commit_summary` schema (required fields)

`log_commit_summary` is a single object appended to `execution_trace` (in the same cycle). Required fields:

* `cycle_index: int`
* `streams_written: array<string>` (subset of `{observations, artifacts, admission_trace, selector_trace, execution_trace}`)
* `warrants: array<object>` each:

  * `warrant_id: string`
  * `log_name: string`
  * `line_count: int`
  * `lines_sha256: string` (SHA-256 of `"\n".join(lines) + "\n"` bytes, UTF-8)
* `total_lines_written: int`

Yes: include warrant IDs. That cross-reference is required.

### 70) Replay verification of log commits

Replay must **re-derive** expected log lines and verify both:

1. Warrant correctness:

   * the set of LogAppend warrants issued in the run matches what the kernel would issue under replay, including ordering and content hashes
2. Commit correctness:

   * the committed lines (as recorded in log files) hash to the `lines_sha256` recorded in `log_commit_summary`

Replay does not need “admission trace entries” for LogAppend. It validates LogAppend by recomputing what the kernel would have logged and comparing hashes.

In other words: **logging is treated as deterministic output of the kernel**, not a separately “admitted decision” to be audited via admission_trace recursion.

---

## RefusalRecord Schema Update

### 71) `rejection_summary_by_gate` constitutional or implementation-level?

Implementation-level, not constitutional.

Binding rule:

* Constitution’s `refusal_output_requirements.include` is the *minimum required set*.
* Implementations may add extra fields so long as they do not weaken required ones or introduce forbidden semantics.

So `rejection_summary_by_gate` is **required by spec** but does not require a constitution revision.

---

## Observation Validation & Host Termination

### 72) Host self-termination before kernel: who produces ExitRecord?

Host must **not** terminate silently.

Binding behavior:

* If host detects invalid observation pre-kernel, it must still execute the Phase X exit pathway:

  1. emit a `system` observation `startup_integrity_fail` (host-local)
  2. invoke the kernel in a special “startup-only cycle” with:

     * a single `system` observation describing the failure
     * no candidates
  3. kernel returns `EXIT(INTEGRITY_RISK)` with an ExitRecord
  4. host logs the ExitRecord via LogAppend warrants
  5. host terminates

So the kernel remains the authority that issues ExitRecords, even for startup integrity failures.

No host-level sovereignty exemption.

---

## Nondeterminism Insulation Test

### 73) Test B: real LLM vs mock?

Use a **stub LLM** that returns predetermined candidate sets.

Binding rule:

* Phase X acceptance does not require testing the stochasticity of a live commercial model.
* Phase X requires that **whatever proposals arrive** cannot bypass sovereignty. That property is stronger and can be validated with stubs.

Therefore:

* Test B uses two stubbed responses:

  * candidate-set A
  * candidate-set B
* Both run under identical observations (except the `budget` observation reflecting the stub output size).
* Verify warrants/side effects remain fully authority-bound.

This satisfies “real RSA” because the RSA-0 claim is architectural: it’s about gating and accountability, not model sampling behavior.

---
## 74) v0.1.1 change set — complete? Consolidate?

**Yes: the v0.1.1 change set is now complete.** No further constitution deltas are pending.

**Implementation must not proceed against “v0.1 + informal patches.”** That guarantees drift. Phase X is allergic to drift.

**Binding rule:** produce and freeze a consolidated **`rsa_constitution.v0.1.1.yaml`** (plus schema + sha256) **before** implementation begins beyond scaffolding (repo layout, empty modules, CI harness).

### v0.1.1 deltas included

1. `LogAppend.jsonl_line` → `LogAppend.jsonl_lines: array<string>`
2. LogAppend per-warrant limits:

   * `max_lines_per_warrant = 50`
   * `max_chars_per_line = 10_000`
   * `max_bytes_per_warrant = 256_000`
3. RefusalRecord enum: **remove `INTEGRITY_RISK`** (integrity risk ⇒ EXIT only)
4. (No other constitution-level changes.)

Everything else stays as v0.1.

---

## 75) Startup-only cycle — is it cycle 0?

**Yes: it is cycle 0.** There is no “pre-cycle.” `cycle_index` starts at 0, always.

Implication:

* The first user-input cycle is typically cycle 1.

Acceptance criterion update:

* “at least 3 cycles” means **3 cycles total**, including cycle 0.
  So a minimal passing run is:
* cycle 0 (startup ok, typically REFUSE)
* cycle 1 (ACTION or REFUSE)
* cycle 2 (ACTION or REFUSE)

---

## 76) Startup cycle mandatory refusal — intentional?

**Yes. No new Decision type.** A startup cycle that REFUSEs is not a bug; it is a valid “no admissible action” outcome under closed authority.

However, to avoid a confusing “every run starts with a refusal” UX artifact, you may optionally allow a kernel-authored LogAppend-only action in cycle 0 to record startup integrity events. That still results in `Decision = ACTION` (LogAppend) and remains sovereignty-correct because:

* action is kernel-only,
* warrant-gated,
* no external side effect beyond logging.

**Binding choice for v0.1.1:** allow either behavior:

* REFUSE is acceptable, or
* ACTION(LogAppend startup summary) is acceptable

But **do not** introduce `INIT`.

---

## 77) Replay re-derives log lines — is log construction part of determinism?

Yes. **Log-line construction is part of deterministic kernel behavior** and must be replayable.

Binding structure:

* Policy Core remains pure with respect to **Decision**.
* Kernel has a second pure function:

```
derive_telemetry(cycle_inputs, decision, traces) -> LogIntents
```

Where `LogIntents` deterministically yields the exact JSON objects/lines that will be written via LogAppend warrants.

Replay re-runs:

* admission + selection + decision
* telemetry derivation
* warrant splitting

So: log construction is pure, deterministic, and replay-checked.

---

## 78) Split warrant partial writes — integrity risk or acceptable?

Partial writes are **acceptable**, but must be **detectable** and must trigger **EXIT on the next cycle** if detected.

Binding rules:

1. Each LogAppend warrant includes:

   * `stream`
   * `sequence_index` (0..k-1)
   * `sequence_len` (k)
   * `lines_sha256`
2. Executor must write lines and then emit an execution trace entry `log_append_committed` for each warrant.
3. At cycle start, the host provides a `system` observation summarizing the previous cycle’s committed warrant IDs for logs (or the kernel reads its own last-cycle execution_trace from allowlisted logs).
4. If expected warrants were not committed → `system.event = executor_integrity_fail` → kernel EXIT(INTEGRITY_RISK).

So logs are allowed to be partially written, but the system must not continue silently.

---

## 79) Sufficient to begin? Any known open items?

**Yes: sufficient to begin implementation once the consolidated v0.1.1 constitution is produced and hashed.**

No other blockers remain.

### Implementation gating (binding)

* **Before coding logic:** create consolidated `rsa_constitution.v0.1.1.yaml`, schema, sha256.
* **Then implement:** artifacts, canonicalization, admission gates, selector, warrants, executor, logging, replay.
* **No parallel “finalize while implementing.”** That’s exactly how drift returns.

---
Below are **binding answers** to Q80–Q83. This is **Addendum H**. It closes the remaining implementation ambiguities before we freeze v0.1.1.

---

# Addendum H — Final Clarifications (Q80–Q83)

## 80) Where do LogAppend limits live in the constitution?

Put them **nested inside the `LogAppend` action type definition**.

Rationale: these are not global system constants; they are **constraints on that action type’s admissible payload**. Co-location keeps the authority surface local and avoids inventing a new top-level semantic namespace.

**Binding schema location:**
`action_space.action_types[type == "LogAppend"].limits`

Required fields:

* `max_lines_per_warrant: int` (=50)
* `max_chars_per_line: int` (=10000)
* `max_bytes_per_warrant: int` (=256000)

These are constitution-authoritative, not implementation defaults.

---

## 81) Cycle 0 LogAppend startup summary — what content?

Keep it **minimal**. No “startup manifest.”

Binding content for cycle 0 startup LogAppend:

* exactly the two system events:

  * `startup_integrity_ok`
  * `citation_index_ok`
* include:

  * `constitution_sha256` (string)
  * `repo_root` (string, canonical absolute path)
* include:

  * `effective_allowlist_read_roots` (array of canonical absolute paths)
  * `effective_allowlist_write_roots` (array of canonical absolute paths)

Do **not** include:

* citation index size
* internal maps
* schema dumps
* environment details

Reason: cycle 0 must not become a second configuration subsystem. The goal is to make startup verifiable and replayable, not verbose.

---

## 82) `derive_telemetry` inputs and trace interface

Yes: `traces` are structured in-memory objects produced by admission + selector for the current cycle.

Binding requirement:

* admission and selector must emit **structured trace events** into an in-memory list.
* `derive_telemetry(...)` must be a pure function over:

  * `cycle_inputs` (observations + candidates + internal_state)
  * `decision`
  * `trace_events[]`

Trace event interface is **closed and minimal** for Phase X to preserve determinism.

Define three event types only:

1. `admission_event`

* `candidate_id`
* `gate` ∈ { completeness, authority_citation, scope_claim, constitution_compliance, io_allowlist }
* `result` ∈ { pass, fail }
* `reason_code` (rejection enum if fail)

2. `selection_event`

* `admitted_bundle_hashes` (array<string>)
* `selected_bundle_hash` (string)

3. `execution_event`

* `warrant_id`
* `tool` (action type)
* `result` ∈ { committed, failed }
* `detail` (string, bounded)

Implementations may add extra fields **only if**:

* they are deterministic
* they are schema-validated
* they do not add new event types in Phase X

This keeps replay stable and prevents “trace drift.”

---

## 83) Previous-cycle warrant verification — who provides it? logs read access?

The **executor** provides commit acknowledgments as part of the **in-memory run state**, not by reading log files.

So: **do not add `./logs/` to `read_paths`**.

Binding mechanism:

* After executing each LogAppend warrant, executor returns an `execution_event` with `result=committed` and the `warrant_id`.
* Host aggregates these acknowledgments in memory and injects them at next cycle start as a `system` observation:

  * `event = executor_integrity_fail` only if expected commits were not acknowledged.
  * Otherwise no failure event is emitted.

This avoids host reading logs and avoids expanding IO policy.

Additionally:

* If the process crashes mid-cycle, that run ends; the next run’s startup cycle may optionally scan logs for forensic debugging, but **that is outside Phase X correctness requirements**. Phase X correctness is per-run, and partial-write detection is intra-run.

---
