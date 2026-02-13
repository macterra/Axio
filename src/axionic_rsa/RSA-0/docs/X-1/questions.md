# RSA X-1 Design Questions

Questions arising from reading the Phase X-1 spec and implementation instructions.
Each question is tagged with the source section(s) that prompted it.

---

## A — Artifact Schema & Fields

**Q1.** AmendmentProposal has `diff_summary` in the spec (§2.2) but not in the instructions (§3.1). The instructions list `author` but the spec does not. What is the binding field set? Is `diff_summary` required, optional, or dropped? Is `author` required?
*(spec §2.2, instructions §3.1)*

**Q2.** The `proposed_constitution_yaml` field on AmendmentProposal — is this stored as a literal YAML string inside a JSON artifact? A full constitution YAML is ~280 lines. This makes the artifact very large. Is there a size limit? How does canonical JSON serialization (RFC 8785) handle the embedded YAML string?
*(spec §2.2, instructions §3.1)*

**Q3.** How is the `id` for AmendmentProposal computed? Same `SHA-256(canonical_json(to_dict()))` pattern as existing artifacts? If so, the hash includes the full proposed YAML text, making it extremely sensitive to whitespace.
*(spec §2.2)*

**Q4.** How is the `id` for AmendmentAdoptionRecord computed? Same pattern?
*(spec §2.3)*

**Q5.** The spec says `authorization_threshold` is "integer or enumerated rule" (§2.5); the instructions say just "integer" (§4). Which is binding? If enumerated rules are allowed, what are the valid enum values?
*(spec §2.5, instructions §4)*

**Q6.** The spec says `authority_reference_mode` is an enum (§2.5). What are the valid enum values? The term is not defined elsewhere.
*(spec §2.5)*

**Q7.** `density_upper_bound` is optional (spec §2.5). If absent from the AmendmentProcedure, is there an implicit ceiling (density < 1 from the invariants), or does "absent" mean "no density constraint"?
*(spec §2.5, §7)*

---

## B — The Bootstrap Problem

**Q8.** The current constitution v0.1.1 has `amendment_policy: amendments_enabled: false` and lists `AmendConstitution` as a forbidden action. It has no `AmendmentProcedure`, no explicit `AuthorityModel` section, no `WarrantDefinition` section, and no `ScopeSystem` section — all four ECK sections required by the spec (§2.4). How does X-1 bootstrap? Specifically:
(a) Does v0.1.1 need to be manually superseded by a v0.2 constitution that adds these sections *before* the kernel can process any AmendmentProposal?
(b) Or is the first AmendmentProposal exempt from ECK checks on the *prior* constitution (since v0.1.1 lacks them)?
(c) Or does the kernel treat `amendments_enabled: false` as "no amendment proposals can be admitted at all," meaning X-1 starts from a new base constitution?
*(spec §2.4, instructions §2.1, constitution v0.1.1 `amendment_policy`)*

**Q9.** If a new base constitution (e.g., v0.2) is needed, is it created manually (frozen artifact, human-authored), or must the agent propose it through the amendment channel? This is the deepest chicken-and-egg: the first amendment-capable constitution cannot be proposed through an amendment that requires an amendment-capable constitution.
*(spec §3.1, §4)*

**Q10.** The ECK section names — `AmendmentProcedure`, `AuthorityModel`, `WarrantDefinition`, `ScopeSystem` — do not correspond to any top-level keys in the current constitution YAML. The closest mappings might be: `AuthorityModel` → `meta.authority_model` + `invariants`? `WarrantDefinition` → the warrant structure in `action_space`? `ScopeSystem` → `observation_schema` + `io_policy`? What are the exact YAML key paths that the ECK check must verify?
*(spec §2.4, instructions §5 gate 7)*

---

## C — Admission Pipeline

**Q11.** AmendmentProposals pass through gates 0–5 (spec §3.2). But several existing gates assume CandidateBundle structure (ActionRequest + ScopeClaim + Justification + AuthorityCitations):
(a) Gate 1 (completeness): checks for required fields on ActionRequest. AmendmentProposal has different required fields. Does completeness need a type-switch?
(b) Gate 4 (constitution_compliance): checks action type ∈ closed set. AmendmentProposal is not an action type. Does this gate skip, pass-through, or need a branch?
(c) Gate 5 (io_allowlist): checks read_paths/write_paths. AmendmentProposal has no IO paths. Does this gate skip?
*(spec §3.2, instructions §5)*

**Q12.** Is an AmendmentProposal wrapped in a CandidateBundle (like ActionRequest), or is it a separate artifact type that enters the admission pipeline via a different channel? The current pipeline expects `CandidateBundle = (ActionRequest, ScopeClaim, Justification, AuthorityCitations)`. Where does AmendmentProposal fit in this tuple?
*(spec §3.1, instructions §3.1)*

**Q13.** The spec and instructions both have AmendmentProposal carrying its own `scope_claim`, `justification`, and `authority_citations` fields (not as separate artifacts). Is this intentionally different from the CandidateBundle pattern where these are separate artifacts? Or should they be factored out into the standard tuple?
*(spec §2.2, instructions §3.1)*

**Q14.** Gate 6 says "Cooling delay rule satisfied." At proposal admission time, there is no prior proposal to compare against (the cooling delay constrains *adoption*, not *proposal*). Is this check actually performed at admission of the proposal, or only at adoption time?
*(spec §3.2 gate 6, instructions §5 gate 6)*

**Q15.** Instructions §7 says at adoption time: "Re-run all Gates 6–8B." Is this a full re-admission of the *original proposal artifact*, or a separate adoption-specific check? If the constitution changed between proposal and adoption (via a different amendment), the proposal's `prior_constitution_hash` no longer matches — does this auto-invalidate it?
*(instructions §7)*

---

## D — Cooling Delay & Pending Proposals

**Q16.** Where is `proposal_cycle` stored? Is it derived from the cycle number in which the AmendmentProposal was admitted, or is it an explicit field? The kernel is pure and stateless per cycle — how does it know which cycle a prior proposal was admitted in?
*(spec §4, instructions §6)*

**Q17.** How are pending proposals tracked across cycles? The kernel's `InternalState` currently stores `cycle_number` and `decision_type_history`. Does it need a `pending_proposals` list? If so, what structure?
*(spec §4, instructions §6)*

**Q18.** Can multiple AmendmentProposals be pending simultaneously? If so, can they conflict (different proposed constitutions)? Is first-to-adopt-wins the resolution rule?
*(spec §4)*

**Q19.** If proposal P₁ is pending and a different proposal P₂ is adopted (changing the active constitution hash), P₁'s `prior_constitution_hash` no longer matches. Is P₁ automatically invalidated, or must it be explicitly rejected?
*(spec §4, §5.1)*

---

## E — Adoption Trigger & Execution

**Q20.** Who triggers adoption? The spec does not specify the mechanism:
(a) Does the host construct an "adopt amendment" candidate after the cooling period expires?
(b) Does the kernel auto-adopt when it detects a pending proposal past its cooling period?
(c) Is there a separate `AdoptAmendment` action type?
(d) Does the LLM propose adoption?
The trigger mechanism determines whether adoption is host-initiated, kernel-autonomous, or LLM-proposed.
*(spec §5.1, instructions §7)*

**Q21.** The spec says "No side effects beyond adoption artifact" (§5.1). But the adoption must be logged (instructions §9: `constitutions.jsonl`, `amendment_trace.jsonl`). Are these log writes performed via existing LogAppend warrants, or via a new mechanism? If LogAppend, does the kernel issue LogAppend warrants for adoption the same way it does for regular cycle telemetry?
*(spec §5.1, instructions §7, §9)*

**Q22.** After adoption, when does the new constitution take effect? Same cycle or next cycle? The field `effective_cycle` on AmendmentAdoptionRecord suggests it's specified, but the instructions don't clarify whether the adoption cycle itself runs under old or new law.
*(spec §5.1, instructions §7)*

**Q23.** Is AmendmentProposal `kernel_only` (like LogAppend), or can it be proposed by any author (like Notify)? Same question for the adoption trigger (if it's an artifact).
*(spec §3.1, instructions §3.1)*

---

## F — Replay

**Q24.** The existing replay harness (`replay/src/replay.py`) was built for single-constitution execution. X-1 requires constitution switching at fork boundaries. Is this an extension of the existing replay module, or a new module under `replay/x1/`? The spec says kernel physics is immutable, but the replay harness is kernel-adjacent infrastructure.
*(spec §5.2, instructions §8)*

**Q25.** Instructions §8 says "No global policy cache allowed." Does this mean the replay harness must reload and re-parse the constitution YAML at every cycle, or only at fork boundaries? If at every cycle, that's a significant performance constraint for long runs.
*(instructions §8)*

**Q26.** The instructions say "Constitution YAML may be stored in logs for replay integrity" (§7). Is this "may" or "must"? If the proposed YAML is only in the AmendmentProposal artifact (logged in `artifacts.jsonl`), replay can extract it from there. If it's not logged at all, replay cannot reconstruct the new constitution. What is the binding requirement?
*(instructions §7)*

---

## G — Gate 8B Mechanics

**Q27.** How are "distinct authorities" and "distinct actions" counted from the constitution YAML? In v0.1.1, the closest structures are `invariants` (4 entries) and `action_space.action_types` (5 types). Are authorities = invariant IDs? Or something else? The term "authority" is overloaded — it could mean invariant IDs, citation targets, or a new `AuthorityModel` section.
*(spec §3.2 gate 8B, instructions §5 gate 8B)*

**Q28.** How are "authority–action mappings" (M) counted? The current constitution has `requires.authority_citations: true` on each action type, but doesn't specify *which* authority IDs apply to *which* actions. The mapping is implicit (any invariant can be cited for any action). Does Gate 8B require switching to explicit per-authority-per-action mappings in the YAML?
*(spec §3.2 gate 8B, instructions §5 gate 8B)*

**Q29.** Wildcard check (instructions §5 gate 8B step 2): "Reject if any `authority: '*'` or `action: '*'`." Where in the YAML structure would these appear? The current constitution has no authority-action mapping table that could contain wildcards. Does the v0.2 constitution need to introduce an explicit mapping structure?
*(instructions §5 gate 8B step 2)*

**Q30.** Scope collapse check: "All actions globally scoped" and "No action requires scoped warrant." How is "globally scoped" defined structurally? The current constitution has `requires.scope_claim: true/false` per action type. Is `scope_claim: false` equivalent to "globally scoped"?
*(spec §3.2 gate 8B item 3, instructions §5 gate 8B step 4)*

---

## H — Gate 8A Mechanics

**Q31.** Gate 8A rejects constitutions that "introduce executable payloads" or "declare kernel invariants." How is "executable payload" detected structurally? Scanning for specific YAML keys? Regex for code-like patterns? The spec says "structural, not semantic" but this seems to require content heuristics.
*(spec §3.2 gate 8A, instructions §5 gate 8A)*

**Q32.** "References undefined kernel hooks" — what constitutes a "kernel hook"? Is there an exhaustive list of kernel hook names, or is this a negative check (reject if any key matches a forbidden pattern)?
*(spec §3.2 gate 8A, instructions §5 gate 8A)*

---

## I — Constitution v0.2 Design

**Q33.** If X-1 requires a new base constitution (per Q8/Q9), what changes are needed beyond adding the four ECK sections? At minimum:
(a) `amendment_policy.amendments_enabled` → `true`
(b) Remove `AmendConstitution` from `forbidden_actions`
(c) Add `AmendmentProcedure` section with required structured fields
(d) Add or map `AuthorityModel`, `WarrantDefinition`, `ScopeSystem`
(e) Add `AmendmentProposal` to the action/artifact type system
Is this the right scope, or is there more?
*(spec §2.4, §2.5, constitution v0.1.1)*

**Q34.** The reflection policy in v0.1.1 explicitly forbids `amend` in `llm_forbidden`. Must v0.2 remove this restriction to allow LLM-proposed amendments? Or does "propose an AmendmentProposal" not count as "amend" (since the kernel still decides)?
*(constitution v0.1.1 `reflection_policy.llm_forbidden`, spec §3.1)*

**Q35.** Does v0.2 need new admission rejection codes for the new gates? E.g., `AMENDMENT_UNAUTHORIZED`, `INTEGRITY_CHECK_FAILED`, `ECK_MISSING`, `PHYSICS_CLAIM_DETECTED`, `UNIVERSAL_AUTHORIZATION`, `SCOPE_COLLAPSED`, `ENVELOPE_DEGRADED`, `COOLING_VIOLATION`?
*(instructions §5 gates 6–8B)*

**Q36.** The LogAppend action currently writes to 5 log streams (observations, artifacts, admission_trace, selector_trace, execution_trace). Instructions §9 adds `constitutions.jsonl` and `amendment_trace.jsonl`. Must these be added to the `log_name` enum in the constitution's LogAppend definition?
*(instructions §9, constitution v0.1.1 `action_types.LogAppend.required_fields`)*

---

## J — Budget & Tokenization

**Q37.** A full AmendmentProposal with embedded constitution YAML (~280 lines) could easily be 3,000–5,000 tokens. The current B₁ cap is 6,000 tokens per cycle. Does adoption require a special budget exemption, or must the harness/LLM fit the entire proposal within B₁? This severely constrains the size of proposed constitutions.
*(spec §3.1, constitution v0.1.1 `reflection_policy.proposal_budgets`)*

**Q38.** Is there a B₂ (session budget) for X-1 runs? The spec doesn't mention session-level budget. Does X-0L's B₂ machinery carry forward?
*(spec, instructions — absent)*

---

## K — LLM / Harness Integration

**Q39.** How does the harness signal to the LLM that it should propose an AmendmentProposal vs a regular ActionRequest? Separate system prompt? Explicit instruction in the user message? Condition-dependent?
*(spec §3.1)*

**Q40.** The spec says "Canonicalization identical to X-0L" (§3.1). But an AmendmentProposal is structurally different from an ActionRequest JSON — it contains an embedded YAML string. Does the canonicalizer need changes, or is the proposal just a JSON object that happens to have a large string field?
*(spec §3.1)*

**Q41.** Is there an X-1 profiling harness (X-1P or X-1L)? Or does X-1 use only unit/acceptance tests (instructions §10)? The spec's closure criteria (§11) require "at least one amendment adopted" — does this require live LLM execution?
*(spec §11, instructions §10, §12)*

---

## L — Structural / Organizational

**Q42.** Instructions §1 says "Extend the RSA-0 repo." Does this mean modifying files under `src/axionic_rsa/RSA-0/`, or building X-1 as a parallel `src/axionic_rsa/RSA-1/` directory that imports from RSA-0? The kernel is frozen — so new gates must be separate modules. But the kernel's `admission.py` would need to call them.
*(instructions §1)*

**Q43.** If X-1 extends the RSA-0 kernel's admission pipeline with gates 6–8B, that is a kernel modification. But the spec says "Kernel Physics (Immutable in X-1)" and lists "Artifact admission pipeline" as immutable. How is this resolved? Are gates 6–8B a *post-admission extension* that runs after the existing pipeline, rather than modifications to the existing gates?
*(spec §0.1, instructions §5)*

**Q44.** The test plan (instructions §10) specifies 8 test categories. Is each a single test or a family? How many total tests are expected? Is there a minimum?
*(instructions §10)*

**Q45.** The `diff_summary` field (spec §2.2, absent from instructions) — if retained, is this computed by the proposer (LLM/host), verified by the kernel, or purely informational with no gate checking it?
*(spec §2.2)*

**Q46.** Can an adopted constitution remove action types from the closed set (e.g., delete WriteLocal)? Or does ECK preservation prevent shrinking the action space?
*(spec §2.4, §8)*

**Q47.** The ratchet (instructions §5 gate 8B step 5) is monotonic non-decreasing for `cooling_period_cycles` and `authorization_threshold`. What about `density_upper_bound`? Can it be *decreased* (stricter) or only *increased* (or unchanged)? Decreasing it is "safer" but the ratchet logic doesn't distinguish tightening from loosening.
*(instructions §5 gate 8B step 5, spec §3.2 gate 8B item 4)*

---

*47 questions. Answers received — follow-ups below.*

---
---

# Follow-Up Questions (from answers to Q1–Q47)

---

## FA — Proposal ID & Constitution Canonicalization

**Q48.** A3 says the proposal ID is computed from canonical JSON that *excludes* the raw YAML text "or including it only as a derived canonical byte hash." The "or" is ambiguous. Binding choice: is `proposed_constitution_yaml` **excluded** from the `to_dict()` used for `AmendmentProposal.id`, or is it **included as its hash** (i.e., replaced by `proposed_constitution_hash` in the dict)? These produce different IDs.
*(A3)*

**Q49.** A3 defines "canonical constitution bytes" (normalize line endings, strip trailing whitespace, UTF-8, no tabs). Who performs this normalization — the proposer (host/LLM), the kernel (at gate 7), or both? If the LLM emits YAML with tabs or trailing spaces, is that a gate 7 rejection, or does the kernel normalize-then-hash?
*(A3, gate 7)*

**Q50.** A3 says `proposed_constitution_hash = SHA-256(canonical constitution bytes)`. A2 says impose `max_constitution_bytes`. Is this byte limit checked against the *raw* YAML string or the *canonical* bytes? (They differ if normalization removes whitespace.)
*(A2, A3)*

---

## FB — Selector & Decision Routing

**Q51.** A12 says AmendmentProposal uses a "separate channel" (not CandidateBundle). The existing selector picks among admitted CandidateBundles via lexicographic-min hash. If both a CandidateBundle and an AmendmentProposal are admitted in the same cycle, which does the selector choose? Is there a priority rule (amendments before actions, or vice versa), or are they mutually exclusive per cycle?
*(A12, A20)*

**Q52.** A20 says ADOPT is a new kernel decision variant (parallel to ACTION/REFUSE/EXIT). This means `InternalState.decision_type_history` must track ADOPT. Does this also mean the decision type set is now {ACTION, REFUSE, EXIT, ADOPT, PROPOSE_AMENDMENT} (where PROPOSE_AMENDMENT is the decision to admit an amendment proposal), or is admitting a proposal just ACTION with an amendment-typed payload?
*(A20)*

**Q53.** Can a single cycle produce both a proposal admission *and* a regular action? Or is each cycle one decision: either ACTION (regular), PROPOSE (amendment admitted), ADOPT (amendment enacted), REFUSE, or EXIT?
*(A20, A12)*

---

## FC — Kernel Purity & Log-Derived State

**Q54.** A16 says `proposal_cycle` is derived from `amendment_trace.jsonl`. A17 says pending proposals are derived from logs each cycle. But the kernel is pure — it doesn't read files. How does the kernel obtain the pending proposal set and their admission cycles? Options: (a) host reconstructs from logs and passes as an observation, (b) internal_state accumulates it (reconstructible from logs during replay), (c) new observation kind. Which?
*(A16, A17)*

**Q55.** If pending proposals are passed to the kernel as observations (Q54 option a), is there a new observation kind (e.g., `amendment_status`) or is this packed into the existing `system` kind? The observation schema is currently a closed set of 4 kinds.
*(A17, constitution v0.1.1 `observation_schema`)*

**Q56.** A17 says "pending = admitted − (adopted ∪ refused)." A19 says stale proposals (prior_hash mismatch) should be logged as `STALE_PROPOSAL_INVALIDATED`. Does the kernel emit this refusal record during adoption processing, or does the host detect staleness and never present the proposal?
*(A17, A19)*

---

## FD — ADOPT Decision Mechanics

**Q57.** A20 says ADOPT is a kernel decision variant. A22 says effective_cycle = N+1 (always). The spec's `AmendmentAdoptionRecord` has an `effective_cycle` field. Is this field always computed as `current_cycle + 1`, or can the proposer specify a later effective cycle (e.g., N+3 for a deferred adoption)?
*(A20, A22, spec §2.3)*

**Q58.** Can ADOPT and LogAppend co-occur in the same cycle? In the current kernel, ACTION produces LogAppend warrants for telemetry. Does ADOPT also produce LogAppend warrants (for `amendment_trace.jsonl` and `constitutions.jsonl`)? If so, the cycle has: ADOPT decision + AmendmentAdoptionRecord + LogAppend warrants — a compound output.
*(A20, A21)*

**Q59.** When does the kernel check for adoptable proposals — before or after evaluating regular candidates? If adoption check happens first and succeeds, are regular candidates skipped? This determines whether adoption preempts normal action.
*(A20)*

**Q60.** What triggers the kernel to *attempt* adoption? Does the host pass a "cooling period elapsed for proposal X" observation? Or does the kernel check all pending proposals every cycle against the current cycle number?
*(A20, A16, A17)*

---

## FE — Authority–Action Mapping Structure

**Q61.** A28 shows an explicit `AuthorityModel.permissions` mapping. In the current v0.1.1, any invariant can be cited for any action (implicit universal mapping). The move to explicit mappings *restricts* what was previously unrestricted. Does this mean the v0.2 base constitution must enumerate every valid authority–action pair that was previously implicit? If so, this is a large structural change.
*(A28, A27)*

**Q62.** A28's mapping uses `authority` and `actions` fields. Are the `authority` values the same as invariant IDs (e.g., `INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT`), or are they new identifiers defined in `AuthorityModel.authorities[]`? If new, what is the relationship between authorities and invariants?
*(A27, A28)*

**Q63.** The density formula is `M / (A × B)`. With the explicit mapping from A28, if authority A1 maps to [Notify, ReadLocal] and A2 maps to [Notify], then A=2, B=2 (only Notify and ReadLocal appear), M=3. density = 3/4 = 0.75. But what about actions that appear in `action_space.action_types` but not in any permission mapping (e.g., WriteLocal, Exit, LogAppend)? Are they counted in B? If B=5 (all action types), density drops to 3/10 = 0.3.
*(A28, spec §3.2 gate 8B)*

---

## FF — v0.2 Constitution Structure

**Q64.** A33 lists 6 required changes for v0.2. The current constitution has ~287 lines. With the 4 new ECK sections (AmendmentProcedure, AuthorityModel, WarrantDefinition, ScopeSystem), explicit authority–action mappings, new rejection codes, new log streams, and schema changes — v0.2 could be 400+ lines. Is there a complexity budget, or does it grow as needed?
*(A33)*

**Q65.** What does `WarrantDefinition` contain as an ECK section? The current constitution defines warrants implicitly through the action_space `requires` fields. Does `WarrantDefinition` centralize warrant rules (e.g., "all side effects require warrants"), or is it just the existing `requires` fields moved to a new top-level key?
*(A10, A33)*

**Q66.** What does `ScopeSystem` contain? The current scoping is `requires.scope_claim: true/false` per action type. Does `ScopeSystem` define scope *types* (e.g., "file scope", "log scope"), or is it just a top-level key containing the existing per-action scope flags?
*(A10, A30, A33)*

---

## FG — Repo Organization

**Q67.** A42 says `kernel/src/rsa0/*` and `kernel/src/rsax1/*`. The current kernel is at `kernel/src/*.py` (flat). Does this mean physically moving existing files into `kernel/src/rsa0/`, or using `kernel/src/rsax1/` as a *new* directory that imports from the unchanged `kernel/src/` path?
*(A42)*

**Q68.** A43 says "modify code between phases." The RSA-0 implementation report says "kernel was frozen" and all profiling ran with zero kernel modifications. If X-1 adds ADOPT as a decision type and gates 6–8B to policy_core, the X-0P and X-0L test suites may break (new decision types not handled, new gates not expected). Must the RSA-0 test suite still pass unmodified against the X-1 kernel?
*(A43)*

---

## FH — Test & Closure

**Q69.** A41 says closure can be achieved with a "deterministic fixture proposal" (no live LLM). Does this fixture proposal need to pass through the full admission pipeline (gates 0–8B), or can it be injected post-admission? If post-admission, it doesn't test the gates.
*(A41)*

**Q70.** A44 says ~12–20 tests covering every rejection code. A35 lists 10 new rejection codes. The existing kernel has ~7 rejection codes. That's 17 rejection codes minimum, plus positive paths. Is the test target closer to 25–30?
*(A44, A35)*

---

*70 questions total (47 original + 23 follow-ups). Answers to Q48–Q70 received — second follow-ups below.*

---
---

# Second Follow-Up Questions (from answers to Q48–Q70)

---

## SA — Proposal ID Computation Detail

**Q71.** A48 says `proposed_constitution_yaml` is excluded from the dict for proposal ID, but `proposed_constitution_hash` is included. The proposal artifact still *contains* the full YAML string (for logging/replay per A26). When serializing the proposal to `artifacts.jsonl`, the full YAML is present. But when computing the ID, a *different* dict (without YAML) is used. Is this a special `to_dict_for_id()` method, or is `to_dict()` always the reduced form and the YAML is carried as a separate non-hashed attachment?
*(A48, A26)*

**Q72.** A49 says the kernel normalizes at Gate 7 and computes the hash from normalized bytes, then checks equality with `proposed_constitution_hash`. This means the kernel must have access to the raw YAML string (to normalize it). But A48 excludes YAML from the ID dict. So the kernel receives the full AmendmentProposal (with YAML) for gate evaluation, but computes the ID from a reduced dict. Is the full YAML a field on the artifact object but excluded from `to_dict()` for hashing? Or is it a separate parameter passed alongside the artifact?
*(A48, A49)*

---

## SB — Internal State Extension

**Q73.** A54 says pending proposals live in `internal_state`. A55 says no new observation kind. The current `InternalState` has `cycle_number` and `decision_type_history`. For X-1 it needs at minimum:
- `pending_proposals: List[{proposal_id, prior_constitution_hash, proposed_constitution_hash, proposal_cycle}]`
- `active_constitution_hash: str`
- `adopted_amendments: List[{adoption_id, effective_cycle, new_hash}]`

Is this the right shape? Are there other fields needed (e.g., the full proposed YAML for gate re-validation at adoption, or just the hashes)?
*(A54, A55, A60)*

**Q74.** A60 says the kernel checks all pending proposals every cycle using `cooling_period_cycles` from the active constitution. But `cooling_period_cycles` comes from `AmendmentProcedure` in the constitution. If multiple proposals are pending and the constitution hasn't changed, they all share the same cooling period. If a proposal was admitted under constitution C₁ with `cooling_period_cycles=3`, and constitution C₂ (adopted later) has `cooling_period_cycles=5`, which cooling period applies to the stale proposal? Per A15/A19, it's auto-invalidated (prior_hash mismatch), so this case can't arise. Confirm: is it correct that a pending proposal's cooling period is *always* from the constitution it was admitted under, and staleness makes the question moot?
*(A60, A15, A19)*

---

## SC — Decision Space & Cycle Semantics

**Q75.** A51 says the evaluation order is: (1) adoption check, (2) amendment proposal selection, (3) normal action selection, (4) REFUSE/EXIT. A52 says the decision set is {ACTION, ADOPT, REFUSE, EXIT}. When an AmendmentProposal is *admitted* (step 2), the decision type is... what? It can't be ACTION (that's for CandidateBundles). It can't be ADOPT (that's for enacting pending proposals). Is admitting a new AmendmentProposal implicitly an ACTION decision with an amendment-typed payload, or is there an unlisted fifth decision? A52 explicitly says "no PROPOSE_AMENDMENT decision type" and "admitting a proposal is an admission outcome, not a decision."

If admission is not a decision, what *is* the cycle's decision when a new proposal is admitted but no regular action or adoption happens? REFUSE? That seems wrong — something productive happened (a proposal was queued).
*(A51, A52, A53)*

**Q76.** A53 says each cycle yields exactly one of four decisions. A58 says ADOPT produces compound outputs (adoption record + LogAppend warrants). For ACTION, the kernel currently produces: selected bundle + ExecutionWarrant + LogAppend warrants. For ADOPT, the outputs are: AmendmentAdoptionRecord + LogAppend warrants. Is there also an ExecutionWarrant for ADOPT, or is the AmendmentAdoptionRecord itself the authorization artifact (replacing the warrant role)?
*(A52, A58)*

---

## SD — Gate Re-Validation at Adoption

**Q77.** A15/A59/A60 say adoption re-runs gates 6–8B every cycle against pending proposals. This means the kernel must have access to the full proposed constitution YAML each cycle (for gates 7, 8A, 8B). Per Q73, does `internal_state` carry the full YAML for each pending proposal, or does the kernel re-extract it from the logged artifact? If internal_state carries it, that's potentially large. If re-extracted, the kernel is reading logs (violating purity).
*(A15, A60, Q73)*

**Q78.** A15 says adoption re-validates "against the then-active constitution." Gates 8B step 5 (ratchet) compares old vs new AmendmentProcedure. At adoption time, "old" is the current active constitution. But the proposal was originally validated against a *different* "old" (the constitution active at proposal time). If no amendments were adopted between proposal and adoption, these are the same. But per A19, if they differ, the proposal is stale anyway. So ratchet re-validation at adoption is either (a) redundant (same old) or (b) moot (stale → rejected). Is adoption gate re-validation actually just the `prior_hash == active_hash` check plus cooling, with 8B being formally required but never producing a *different* result than at proposal time?
*(A15, A19, spec gate 8B step 5)*

---

## SE — Constitution v0.2 Concrete Structure

**Q79.** A62 says authorities are new identifiers, not invariant IDs. A28 shows `AuthorityModel.authorities: [A1, A2, ...]` with a permissions table. What are sensible authority names for v0.2? They need to be meaningful citation targets. Options:
- Mirror action types: `AUTH-NOTIFY`, `AUTH-READ`, `AUTH-WRITE`, `AUTH-LOG`
- Mirror policy domains: `AUTH-IO`, `AUTH-TELEMETRY`, `AUTH-AMENDMENT`
- Abstract roles: `AUTH-OBSERVATION`, `AUTH-EXECUTION`, `AUTH-GOVERNANCE`

The choice determines what `authority_reference_mode: CLAUSE_IDS` means — citations reference these authority IDs? Or clause IDs are something else?
*(A6, A27, A62)*

**Q80.** A6 says `authority_reference_mode` enum is {CLAUSE_IDS, AUTHORITY_IDS, BOTH}. A62 says authorities are new identifiers separate from invariants. The current kernel's `authority_citation` gate (gate 2) resolves citations against the `CitationIndex` using `constitution:v0.1.1#<id>` format. With v0.2, does gate 2 need to resolve against `AuthorityModel.authorities[]` instead of (or in addition to) the CitationIndex? This is a gate 2 behavior change, which is within the existing admission pipeline.
*(A6, A62, gate 2)*

**Q81.** A65 says `WarrantDefinition` must include "warrant type name(s) and required fields," "statement that side-effectful tools require warrants," and "mapping between action types and warrant scope parameters." A66 says `ScopeSystem` defines scope types and per-action scope requirements. There's overlap: both sections map action types to structural requirements. How do they divide responsibility? Is `WarrantDefinition` about *what a warrant must contain* and `ScopeSystem` about *what scope claims must reference*?
*(A65, A66)*

**Q82.** A66 lists scope types like `FILE_PATH`, `LOG_STREAM`, `WORKSPACE_PATH`. The current constitution uses `io_policy.allowlist.read_paths` and `write_paths` for path constraints. Does `ScopeSystem` subsume `io_policy`, or do they coexist (ScopeSystem for structural typing, io_policy for concrete path lists)?
*(A66, constitution v0.1.1 `io_policy`)*

---

## SF — Repo & Backward Compatibility

**Q83.** A67 says create `kernel/src/rsax1/` importing from existing flat `kernel/src/`. A68 says RSA-0 tests must pass in "RSA-0 mode." Concretely: does `policy_core.py` get a mode flag (`phase="x0"` vs `phase="x1"`), or is there a separate `policy_core_x1.py` that wraps the original? The mode flag approach means modifying the frozen RSA-0 `policy_core.py`; the wrapper approach means a new entry point.
*(A67, A68)*

**Q84.** A68 says "add a separate X-1 entrypoint or mode flag." If it's a separate entrypoint, the X-1 `policy_core` must replicate the full RSA-0 decision logic (observe → integrity → budget → admit → select → warrant) *plus* the amendment logic. That's significant duplication. Is composition preferred — X-1 calls RSA-0's `policy_core()` for the action path, then wraps it with amendment logic?
*(A67, A68)*

---

*84 questions total (47 original + 23 first follow-ups + 14 second follow-ups). Answers to Q71–Q84 received — third follow-ups below.*

---
---

# Third Follow-Up Questions (from answers to Q71–Q84)

---

## TA — Proposal Artifact Dual Serialization

**Q85.** A71 defines `to_dict_full()` and `to_dict_id()`. The existing artifact pattern in RSA-0 uses a single `to_dict()` for both hashing and logging. AmendmentProposal now breaks that symmetry. Should all existing artifacts also grow a `to_dict_id()` / `to_dict_full()` split (even if they're identical), or is the dual-form specific to AmendmentProposal only?
*(A71)*

---

## TB — `policy_core_x1` Signature & Inputs

**Q86.** A77 specifies a new pure signature: `policy_core(observations, constitution, internal_state, pending_proposal_objects) -> Decision`. The RSA-0 signature is `policy_core(observations, candidates, constitution, internal_state) -> PolicyOutput`. In X-1:
(a) Are `candidates` (CandidateBundles) still a parameter? AmendmentProposals enter via `pending_proposal_objects`. Regular action candidates still need to enter somehow.
(b) Where do *new* AmendmentProposals (not yet pending, submitted this cycle) enter? Are they a separate parameter, mixed into candidates, or part of `pending_proposal_objects`?
*(A77, A84, A12)*

**Q87.** A84 says `policy_core_x1` delegates to `policy_core_x0` for normal action selection. But `policy_core_x0` returns a `PolicyOutput` (which may include ACTION + ExecutionWarrant + LogAppend warrants). `policy_core_x1` also needs to return its own compound outputs (QUEUE_AMENDMENT + trace warrants, or ADOPT + adoption record + LogAppend warrants). Is the return type a shared `PolicyOutput` that now accommodates 5 decision types, or does X-1 define a new `PolicyOutputX1` type?
*(A84, A76)*

---

## TC — QUEUE_AMENDMENT Semantics

**Q88.** A75 introduces QUEUE_AMENDMENT as a fifth decision type. When the kernel decides QUEUE_AMENDMENT:
(a) What side effects occur? The proposal needs to be added to `pending_amendments` in internal_state and logged to `amendment_trace.jsonl`. The amendment_trace write requires a LogAppend warrant. Is that the complete set?
(b) Is there an ExecutionWarrant for QUEUE_AMENDMENT, or only LogAppend warrants (like ADOPT)?
*(A75, A76)*

**Q89.** A51 says evaluation order is: adoption → amendment proposal → action → refuse/exit. A75 adds QUEUE_AMENDMENT. If a cycle has both an adoptable pending proposal *and* a new admissible AmendmentProposal, adoption preempts (per A59). But if there's only a new admissible AmendmentProposal and no adoptable proposals, the decision is QUEUE_AMENDMENT. Does the amendment proposal go through a selector (like action bundles do), or is it always single-candidate (since A12 says separate channel)?
*(A51, A75, A18)*

**Q90.** When QUEUE_AMENDMENT is the decision, the host must update internal_state to include the new pending amendment. But the kernel is pure — it returns context describing what to queue, and the host applies it. Is the kernel's QUEUE_AMENDMENT output just `{proposal_id, proposal_cycle}`, and the host is responsible for constructing the `PendingAmendment` entry and persisting the full proposal object in its registry?
*(A73, A75, A77)*

---

## TD — Constitution Store & Replay

**Q91.** A73 says internal_state does not store YAML. A77 says the host maintains a proposal registry `proposal_id -> full AmendmentProposal`. For replay, the harness reconstructs this from `artifacts.jsonl`. But `artifacts.jsonl` currently logs *admitted* artifacts after kernel processing. At what point is the full AmendmentProposal logged — when QUEUE_AMENDMENT is decided, or when the proposal first enters the cycle as input?
*(A73, A77, A26)*

**Q92.** After ADOPT, the new constitution becomes active at cycle N+1. The host needs the parsed new constitution for cycle N+1. Where does the host get it? Options: (a) from the proposal registry (full AmendmentProposal includes YAML), (b) from a separate constitution store, (c) from logs. Per A25, replay uses a `{hash -> parsed_constitution}` map. Does the host maintain the same map during live execution?
*(A57, A25, A77)*

---

## TE — Gate 2 Expansion & Citation Namespaces

**Q93.** A80 says gate 2 expands to resolve two namespaces (clause IDs + authority IDs). The current `CitationIndex` builds from constitution YAML, resolving `constitution:v0.1.1#<id>` and `constitution:v0.1.1@<pointer>` formats. For v0.2 authority resolution:
(a) What is the citation format for authorities? `constitution:v0.2#AUTH_IO_READ`? Or a different prefix?
(b) Does the CitationIndex need to be extended, or is authority resolution a separate lookup?
*(A79, A80)*

**Q94.** A79 says `authority_reference_mode = BOTH` for v0.2, meaning citations must include at least one authority ID and one clause ID. The existing admission gate 2 just checks that all citations *resolve*. Does "BOTH" mean gate 2 must now also check that the *set* of citations contains at least one from each namespace? That's a new structural check beyond simple resolution.
*(A79, A80)*

---

## TF — v0.2 Constitution Design Decisions

**Q95.** A79 lists authorities `AUTH_TELEMETRY`, `AUTH_IO_READ`, `AUTH_IO_WRITE`, `AUTH_GOVERNANCE`, `AUTH_EXECUTION`. The current closed action set is {Notify, ReadLocal, WriteLocal, Exit, LogAppend}. The permissions mapping would be something like:
```
AUTH_TELEMETRY → [LogAppend, Notify]
AUTH_IO_READ → [ReadLocal]
AUTH_IO_WRITE → [WriteLocal]
AUTH_GOVERNANCE → [AmendmentProposal?]
```
But AmendmentProposal is not an action type (per A12 — it's a separate channel). Does `AUTH_GOVERNANCE` map to any action type, or is it an authority that applies only to AmendmentProposals (which are outside the action_space)? If outside, it doesn't factor into the density formula (A × B only counts action_space types).
*(A79, A63, A12)*

**Q96.** A82 says ScopeSystem and io_policy coexist. The schema for v0.2 needs `additionalProperties: false` (A31). Do the new ECK sections (AmendmentProcedure, AuthorityModel, WarrantDefinition, ScopeSystem) get added to the existing schema as required top-level properties, or does v0.2 get a new schema file?
*(A82, A31, A33)*

**Q97.** What is `max_constitution_bytes` set to for v0.2? A37 says bind it so "unamendable by budget" is testable. A rough estimate: v0.2 might be ~400 lines ≈ 15KB. For the proposal to fit in B₁ = 6,000 tokens (~24KB at ~4 bytes/token), the YAML itself can't be much larger than ~20KB. Is 32,768 (32KB) a sensible cap?
*(A37, A50)*

---

*97 questions total (47 + 23 + 14 + 13). Answers to Q85–Q97 received — fourth follow-ups below.*

---
---

# Fourth Follow-Up Questions (from answers to Q85–Q97)

---

## UA — PolicyOutput & state_delta

**Q98.** A87 introduces `state_delta` as a field of `PolicyOutput` — "host-applied internal_state update instructions." This is new: RSA-0's `PolicyOutput` had no such field; the host advanced internal_state itself (incrementing cycle_number, appending to decision_type_history). In X-1, does the kernel *always* emit a state_delta (including for ACTION/REFUSE/EXIT), or only for QUEUE_AMENDMENT and ADOPT? If always, this changes the RSA-0 contract.
*(A87)*

**Q99.** A88 says QUEUE_AMENDMENT emits a `state_delta` instructing the host to append a `PendingAmendment` entry. A57 says ADOPT sets `effective_cycle = current_cycle + 1`. Does the ADOPT state_delta instruct the host to (a) update `active_constitution_hash`, (b) remove the adopted proposal from `pending_amendments`, and (c) invalidate any stale proposals? Or does the host derive these from the AmendmentAdoptionRecord fields?
*(A87, A88, A57)*

---

## UB — Amendment Admission Pipeline Detail

**Q100.** A86 separates `amendment_candidates` (new this cycle) from `pending_amendment_candidates` (queued prior). A89 says new amendment proposals go through admission gates + selector → QUEUE_AMENDMENT. But A14 says proposal admission checks "amendments enabled, prior hash matches, schema + ECK + 8A + 8B." These are gates 6–8B from the spec. Do new amendment proposals *also* pass through gates 0–5 (or their amendment-adapted variants per A11), or only gates 6–8B?
*(A86, A89, A11, A14)*

**Q101.** A89 says select by lexicographically smallest proposal ID. But A48 says proposal ID is computed from `to_dict_id()` which excludes the YAML. Two proposals with identical metadata but different proposed constitutions would have different `proposed_constitution_hash` fields and thus different IDs. Confirmed: the selector correctly distinguishes them. But what if two proposals have identical `to_dict_id()` content (same prior_hash, same proposed_hash, same citations, same justification)? They'd have the same ID — is that a collision that should be rejected, or is it idempotent (same proposal submitted twice)?
*(A89, A48)*

---

## UC — Citation Format & clause IDs

**Q102.** A93 introduces `authority:<hash>#AUTH_*` as the authority citation format. The existing clause citation format is `constitution:<hash>#<id>`. The constitution currently has invariant IDs like `INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT` — these are clause IDs. For v0.2, does the set of clause IDs expand to include the new ECK section IDs? E.g., is `constitution:<hash>#AmendmentProcedure` a valid clause citation, or must there be explicit `CL-*` prefixed IDs?
*(A93, A79)*

**Q103.** A93 says "do not overload CitationIndex with authorities; keep a separate authority resolver." Currently `CitationIndex` is built in `constitution.py` and used by gate 2. For X-1, gate 2 needs *both* resolvers. Is the authority resolver built from the parsed constitution (like CitationIndex) and passed alongside it, or is it a method on the constitution object?
*(A93, A80)*

---

## UD — v0.2 Constitution Concrete Content

**Q104.** A95 splits AuthorityModel into `action_permissions` (for density) and `amendment_permissions` (not for density). The `amendment_permissions` section has `amendments: [ConstitutionReplacement]`. Is `ConstitutionReplacement` the single amendment type in X-1? If so, is it an enum value? Could future phases add `PatchAmendment`, `SectionAmendment`, etc.?
*(A95)*

**Q105.** The current v0.1.1 has `Exit` as an action type with `side_effect_class: terminal`. In the RSA-0 kernel, Exit is a decision-only outcome (no candidates, no warrants). Does v0.2 keep Exit in action_space.action_types (even though it's never used as an action), or remove it? If kept, it factors into B for density. If removed, the action set shrinks to {Notify, ReadLocal, WriteLocal, LogAppend} (B=4).
*(A63, A46, constitution v0.1.1)*

**Q106.** For the v0.2 constitution YAML, I need to draft the four ECK sections with concrete content. Before drafting, confirm the minimal v0.2 scope: is it *only* the structural additions needed for X-1 (ECK sections, authorities, permissions, new log streams, new rejection codes, amendments_enabled), with all other v0.1.1 content carried forward unchanged? Or are there other changes (e.g., updating the meta version, date, changelog)?
*(A33, A96)*

---

*106 questions total (47 + 23 + 14 + 13 + 9). Answers to Q98–Q106 received — fifth follow-ups below.*

---
---

# Fifth Follow-Up Questions (from answers to Q98–Q106)

---

## VA — Citation Transition (INV-* → CL-*)

**Q107.** A102 says `INV-*` IDs are "non-citable physics labels" in X-1, and only `CL-*` are valid clause citations. But in v0.1.1 (and all of RSA-0), the *only* citation targets are `INV-*` IDs — every ActionRequest cites `INV-NO-SIDE-EFFECTS-WITHOUT-WARRANT` etc. If v0.2 makes `INV-*` non-citable, then:
(a) Every action proposal must cite `CL-*` clause IDs instead. Does v0.2 introduce `CL-*` IDs for each rule that actions might cite?
(b) The existing gate 2 resolves `constitution:<version>#INV-*`. Must gate 2 in X-1 mode refuse `INV-*` citations, or accept them as legacy aliases?
(c) This affects the LLM system prompt and all test fixtures. It's a significant change. Is it intentional for X-1, or should `INV-*` remain citable and `CL-*` be additive?
*(A102, A80, A93)*

---

## VB — Stale Invalidation Timing

**Q108.** A99 says "invalidate immediately at adoption time" against the `new_constitution_hash`. A57 says the new constitution becomes active at cycle N+1. So at adoption time (cycle N), the active hash is still the *old* one. Invalidation checks `prior_constitution_hash != new_active_hash`. But the new hash isn't "active" yet — it's pending. Concretely: does the kernel invalidate proposals whose `prior_hash != new_constitution_hash` (forward-looking), or `prior_hash != current_active_hash` (which would invalidate nothing, since they matched to be pending)?
*(A99, A57)*

---

## VC — Amendment Scope Claims

**Q109.** A100 step 3 says the amendment admission pipeline checks scope_claim "references observation ids/hashes as required." The existing scope gate (gate 3) verifies `clause_ref` resolves and `observation_ids` are valid UUIDs from the current cycle's observations. For an AmendmentProposal:
(a) What does `clause_ref` reference? The AmendmentProcedure clause in the constitution (`CL-AMENDMENT-PROCEDURE` or similar)?
(b) What `observation_ids` should an amendment's scope_claim contain? The TIMESTAMP observation? All observations? This seems forced — amendments are constitutional proposals, not responses to specific observations.
(c) Could scope_claim be optional or trivially satisfied for amendments (e.g., always valid if `clause_ref` references the AmendmentProcedure clause)?
*(A100, A13, A11)*

---

## VD — v0.2 Draft Readiness

**Q110.** A105 removes Exit from action_space. A106 says carry forward all v0.1.1 content except structural X-1 additions. Combined with all prior answers, the v0.2 constitution needs:
- 4 ECK sections (AmendmentProcedure, AuthorityModel, WarrantDefinition, ScopeSystem)
- `CL-*` clause IDs on all citable rules
- Explicit `action_permissions` mapping (density-relevant)
- `amendment_permissions` section
- New log streams (constitutions, amendment_trace)
- New rejection codes (10 from A35)
- Exit removed from action_types
- `amendments_enabled: true` (or equivalent)
- `authority_reference_mode: BOTH`
- `max_constitution_bytes: 32768`
- Schema closure (`additionalProperties: false`)

Is this the complete v0.2 delta checklist, or am I missing items?
*(A106, all prior)*

---

*110 questions total (47 + 23 + 14 + 13 + 9 + 4). Awaiting answers to close Q&A.*
