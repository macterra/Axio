# RSA-0 Implementation Instructions (Phase X)

## 0) Prime Directive

**No side effects without a kernel-issued ExecutionWarrant** that references an admitted `ActionRequest`.

Everything else is plumbing.

---

## 1) Repo Layout (Create This First)

Create a new repo (or a top-level folder) with this exact structure:

```
axionic-rsa/
  artifacts/
    phase-x/
      constitution/
        rsa_constitution.v0.1.yaml
        rsa_constitution.v0.1.schema.json
        rsa_constitution.v0.1.sha256
        CHANGELOG.md

  kernel/
    src/
    tests/

  host/
    cli/
    tools/
    sandbox/

  logs/
    .gitkeep

  replay/
    src/
    tests/

  workspace/
    .gitkeep
```

**Rules**

* `artifacts/phase-x/**` = frozen inputs (versioned, hashed).
* `logs/**` = runtime outputs only (never treated as authority).
* `workspace/**` = any writable area allowed by constitution.
* `kernel/**` must be pure+deterministic except for logging output creation (logging is side effect; treat it as permitted low-risk side effect via `Notify/local_log` tools or direct file append under allowlist).

---

## 2) Freeze the Constitution (RSA-0 cannot start until done)

### 2.1 Write the files

Place the constitution YAML at:

* `artifacts/phase-x/constitution/rsa_constitution.v0.1.yaml`

Create:

* `rsa_constitution.v0.1.schema.json` — schema validating the YAML structure
* `rsa_constitution.v0.1.sha256` — SHA256 hash of the YAML (and optionally schema)

### 2.2 Enforce immutability

At runtime:

* load YAML once at startup
* verify hash matches
* **refuse** to start if mismatch

No “auto-fix.” No regeneration. No fallback.

---

## 3) Implement the Artifact Types (Typed, Closed Set)

Implement these structs/classes exactly:

* `Observation`
* `ActionRequest`
* `ScopeClaim`
* `Justification`
* `ExecutionWarrant`
* `RefusalRecord`
* `ExitRecord`

**Hard requirements**

* Every artifact has:

  * `id` (stable: hash of canonical serialization)
  * `type`
  * `created_at`
  * `author` (at minimum: `kernel` vs `reflection` vs `user` vs `host`)
* Canonical serialization must be stable (JSON canonicalization or equivalent). This is required for hashing and deterministic selection.

---

## 4) Implement the Kernel Core (Pure, Deterministic)

### 4.1 Policy Core signature

Implement:

```
policy_core(observations, constitution, internal_state) -> Decision
Decision ∈ { ACTION(bundle), REFUSE(record), EXIT(record) }
```

Where `ACTION(bundle)` contains:

* exactly one `ActionRequest`
* exactly one `ScopeClaim`
* exactly one `Justification`
* citations to authority IDs (from constitution / authority store)

### 4.2 Constraints

Policy core must be:

* deterministic
* side-effect free
* no IO
* no network
* no time-based decisions
* no randomness

If you need time, treat it as an **observation input** (timestamped) and hash it.

---

## 5) Implement the Admission Pipeline (Structural Gates)

Implement admission as sequential gates. For each candidate action bundle:

1. **Completeness Gate**

* required artifacts present
* required fields present

2. **Authority Citation Gate**

* citations exist
* cited authority IDs exist in authority store / constitution
* authority in scope (Phase X: constitution + any allowed fixed authority artifacts)

3. **Scope Claim Gate**

* `ScopeClaim` exists
* references observation IDs/hashes
* cites a specific clause/permission identifier

4. **Constitution Compliance Gate**

* action type is in closed set
* action fields conform to constitution constraints
* network policy obeyed

5. **IO / Tool Allowlist Gate**

* local paths under allowlist
* commands in allowlist (if enabled)
* otherwise refuse

**Output on failure**

* produce a `RefusalRecord` with:

  * `reason_code`
  * `failed_gate`
  * `missing_artifacts`
  * `candidate_ids`
  * `observation_ids`

**No silent dropping**
All candidates must either:

* be admitted, or
* produce a rejection trace entry

---

## 6) Implement the Selector (Procedural, Non-Semantic)

Phase X selector is **deterministic canonicalization**:

* compute canonical hash for each admitted candidate bundle (or the `ActionRequest` id)
* choose the lexicographically smallest hash

**Forbidden**

* any ranking based on natural language
* any heuristic “best”
* any learned model scoring

**If multiple equal** (should not happen if hash stable), break ties by stable artifact ID ordering.

---

## 7) Execution Warrants (The Only Path to Side Effects)

### 7.1 Warrant issuance

Kernel issues an `ExecutionWarrant` only after:

* admission success
* selection

Warrant must include:

* `warrant_id`
* referenced `ActionRequest.id`
* scope constraints (e.g., allowed path, allowed command, target sink)
* expiration (can be “immediate single cycle”)
* single-use flag

### 7.2 Warrant enforcement

All tools must require a warrant. If absent/invalid:

* refuse tool execution
* log refusal

---

## 8) Host + Tools (Minimal Set)

### 8.1 Start with CLI host only

Implement a CLI host that:

* converts user input into `Observation`
* calls the kernel cycle
* executes warrant if issued
* prints refusal/exit records

No Slack/Discord/web until Phase X complete.

### 8.2 Tools (start with two)

Implement two tools first:

1. `Notify(stdout|local_log)`
2. `ReadLocal` (allowlisted paths only)

Optionally add `WriteLocal` later, but only under `./workspace/`.

**Do not implement ExecLocal in v0.1** unless you have a concrete allowlist and a sandbox. Leaving it disabled is safer and still sufficient to complete Phase X.

---

## 9) LLM Integration (Boxed)

### 9.1 LLM is a proposal engine only

LLM can output untrusted text proposals that are converted into candidate artifacts by the host.

LLM must not:

* call tools
* choose the final action
* amend constitution
* bypass admission gates

### 9.2 Containment

Even if LLM outputs 100 proposals:

* only up to `max_candidates_per_cycle` from constitution are admitted into evaluation
* if over budget: **REFUSE with BUDGET_EXHAUSTED** (per constitution)

---

## 10) Logging & Replay (Acceptance-Critical)

### 10.1 Required logs (append-only)

Write logs to `logs/`:

* `observations.jsonl`
* `artifacts.jsonl`
* `admission_trace.jsonl`
* `selector_trace.jsonl`
* `execution_trace.jsonl`

Each line must be self-contained JSON with:

* `run_id`
* `cycle_id`
* `artifact_ids`
* hashes

### 10.2 Replay harness

Implement replay that:

* replays from logs (observations + artifacts)
* recomputes admission and selection
* verifies the same Decision and warrant are produced

Any divergence is a **Phase X failure**.

---

## 11) Test Suite (Must Pass)

### 11.1 Sovereignty sanity checks

Write tests that assert:

1. **No warrant → no side effect**
2. **Invalid warrant → no side effect**
3. **Missing scope claim → REFUSE**
4. **Missing authority citations → REFUSE**
5. **Multiple admissible candidates → deterministic selector chooses same one**
6. **LLM nondeterminism does not change outcome** when the candidate set is identical
7. **Replay produces identical decision + warrant**

### 11.2 Failure-mode tests

* budget exhaustion → REFUSE with correct code
* constitution violation → REFUSE
* integrity risk (if implemented) → EXIT or REFUSE per constitution

---

## 12) Definition of Done (Phase X Completion)

RSA-0 is complete when all are true:

1. The agent runs autonomously (CLI loop) without human “approval clicks”
2. It performs at least one admitted action (`Notify` is enough)
3. It refuses correctly when no action is admissible
4. It exits when mandated by policy (if implemented)
5. Every side effect has:

   * admitted ActionRequest
   * scope claim
   * justification
   * execution warrant
6. Replay determinism holds across runs

No further features required.

---

## 13) Explicit Do-Not-Do List (Phase X Kill Switch)

Do not implement:

* intent routers
* priority schedulers
* retries
* self-repair
* “helpful” fallbacks
* semantic ranking
* background jobs
* dynamic tool installation
* network access (unless constitution enables it—current v0.1 disables it)

Any of these is a **proxy-sovereignty regression**.

---
