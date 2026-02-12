# A — Artifact Schema & Fields

**Q1 (binding field set; diff_summary vs author)**

* `author` is **required** on *all* artifacts (kernel vs reflection vs user vs host). This is already a Phase X invariant, even if one draft omitted it.
* `diff_summary` is **optional, informational, non-binding**. Keep it in the schema as optional, never gate on it.

**Q2 (embedded YAML size; canonical JSON)**

* `proposed_constitution_yaml` is stored as a **literal UTF-8 string** inside the JSON artifact.
* Impose a hard size limit: `max_constitution_bytes` (bytes, not tokens), enforced by schema and/or gate 7.
* RFC 8785 canonical JSON treats it as a string; the *string content* is what matters, so you must define a canonicalization rule for the YAML bytes (see Q3).

**Q3 (proposal id too whitespace-sensitive)**
Binding rule: two hashes exist, with different purposes.

* `proposed_constitution_hash` = SHA-256 of **canonical constitution bytes** (see below).
* `AmendmentProposal.id` = SHA-256 of canonical JSON of the proposal object **including**:

  * `prior_constitution_hash`
  * `proposed_constitution_hash`
  * structured fields / citations / scope claim / justification
  * **excluding** the raw YAML text (or including it only as a *derived* canonical byte hash)

This avoids “one trailing space changes proposal id” while still cryptographically binding the proposal to the constitution content.

**Canonical constitution bytes (required):**

* Normalize line endings to `\n`
* Strip trailing whitespace per line
* Require UTF-8, no tabs (or normalize tabs → spaces if you insist)
* Parse+re-emit YAML is **forbidden** as “canonicalization” (too many emitter differences). Keep it a deterministic byte normalization rule.

**Q4 (adoption record id)**
Yes: `AmendmentAdoptionRecord.id = SHA-256(canonical_json(record))`.
This record does **not** include the full YAML; it binds via `new_constitution_hash`.

**Q5 (authorization_threshold: integer vs enum)**
Binding for X-1: **integer only**.
If you want enum rules later (e.g., “2-of-3 authorities”), that is X-2+ with explicit structured authority sets.

**Q6 (authority_reference_mode enum values)**
Binding enum values (X-1):

* `CLAUSE_IDS` — citations must reference constitution clause IDs only
* `AUTHORITY_IDS` — citations must reference authority IDs only
* `BOTH` — must include both

Pick one for v0.2 base constitution; simplest is `CLAUSE_IDS` if you already have clause identifiers.

**Q7 (density_upper_bound optional semantics)**
If absent: only the global invariant applies → **density < 1** (i.e., reject density == 1).
If present: enforce **density ≤ density_upper_bound** (plus still reject density == 1).
Ratchet treatment: **density_upper_bound may only decrease or remain** (tightening is allowed, loosening is forbidden).

---

# B — The Bootstrap Problem (this is the real blocker)

**Q8 (v0.1.1 disables amendments and lacks ECK)**
Binding answer: **X-1 cannot bootstrap from v0.1.1.**
If v0.1.1 has `amendments_enabled: false`, no AmendmentProcedure, and no ECK sections, then by definition **no AmendmentProposal can be admitted** and **ECK checks cannot pass**.

So the only coherent option is:

**(a) Yes:** you must introduce a new base constitution (call it v0.2 for clarity) as a frozen artifact **before** running X-1.

No exemptions. No “first proposal bypass.”

**Q9 (who creates v0.2 base constitution)**
Binding: **human-authored, frozen artifact input**.
It cannot be produced through the amendment channel because the amendment channel does not exist until the base constitution enables it. That chicken-and-egg is real; solve it the boring way.

**Q10 (exact ECK key paths)**
Binding for v0.2+ constitutions: ECK sections must be **top-level keys** with these exact names:

* `AmendmentProcedure`
* `AuthorityModel`
* `WarrantDefinition`
* `ScopeSystem`

No “mapping” to existing scattered keys. You want deterministic structural checks, so you want canonical key paths.

---

# C — Admission Pipeline

**Q11 (gates 0–5 assume CandidateBundle)**
Binding: admission becomes **type-dispatched**.

* Action candidates use the existing CandidateBundle gates 0–5.
* AmendmentProposal uses an **AmendmentAdmission pipeline** that reuses only the *generic* parts of 0–5 (field presence, citation structure), and skips action-specific checks.

Concrete:

* Gate 1 completeness → type-specific required fields
* Gate 4 constitution_compliance → for AmendmentProposal, means “amendments enabled; schema valid; ECK present,” not “action type ∈ set”
* Gate 5 IO allowlist → skip for AmendmentProposal

**Q12 (is AmendmentProposal wrapped as CandidateBundle)**
Binding: **separate channel.**
Do **not** shoehorn it into `(ActionRequest, ScopeClaim, Justification, AuthorityCitations)`.

**Q13 (scope_claim/justification/citations embedded vs separate artifacts)**
Binding: for X-1 keep them **embedded** in AmendmentProposal to avoid multiplying artifact coordination.
They still must be structurally typed fields, but they are not separate artifacts in X-1.

**Q14 (cooling check at proposal admission?)**
Cooling is an **adoption constraint**, not a proposal constraint.
At proposal admission time you only validate:

* amendments enabled
* prior hash matches
* schema + ECK + 8A + 8B structural checks
  Cooling is checked when creating an adoption decision/record.

**Q15 (re-run gates at adoption; what if constitution changed?)**
Binding: adoption re-validates **against the then-active constitution** *and* requires:

* `proposal.prior_constitution_hash == active_constitution_hash` at adoption time

Therefore:

* If any other amendment has been adopted in the meantime, the old proposal becomes **automatically invalid** (must be refused with reason code `PRIOR_HASH_MISMATCH`).

This prevents adopting “stale” proposals under a changed meta-law.

---

# D — Cooling Delay & Pending Proposals

**Q16 (where is proposal_cycle stored?)**
Binding: store `proposal_cycle` as a field in the proposal artifact **when it is admitted** (host writes it at admission time) *or* in an admission trace log keyed by `proposal_id`.

I recommend: put it in the **admission trace log** (append-only), not inside the proposal itself (proposal should be content-addressed; changing it post-admission breaks its id).

So:

* `proposal_cycle` is derived from `amendment_trace.jsonl` admission entry.

**Q17 (pending proposal tracking; kernel stateless)**
Binding: pending proposals are part of **internal_state** only if internal_state is itself fully reconstructible from logs.
Simplest: treat pending proposals as a derived set from logs each cycle:

* pending = admitted proposals − (adopted proposals ∪ explicitly refused proposals)

This is deterministic and replayable.

**Q18 (multiple pending proposals?)**
Yes, multiple can be pending.

Resolution rule (binding):

* Only proposals whose `prior_constitution_hash` matches the current active hash are eligible.
* If multiple eligible, selection uses the same deterministic selector rule: lexicographically smallest proposal id (or hash).

**Q19 (P₁ invalidated by adoption of P₂?)**
Yes. Once P₂ changes the active constitution hash, any proposal with prior hash != active hash becomes **ineligible** and should be logged as `STALE_PROPOSAL_INVALIDATED` (refusal record or trace entry). No silent ignoring.

---

# E — Adoption Trigger & Execution

**Q20 (who triggers adoption?)**
Binding: adoption is a **kernel decision**, not a new external action.

Mechanism:

* The kernel’s policy_core may output `ADOPT(proposal_id)` as a decision variant (parallel to ACTION/REFUSE/EXIT).
* Host executes this as “no side effect” except kernel-issued records + log append (which is already allowed telemetry).

No separate `AdoptAmendment` action type in X-1.

**Q21 (log writes are side effects; warrant?)**
Binding: logging is permitted under the existing “low-risk log append” pathway, but still must be **warranted** if you’re treating log append as a tool.

So:

* Kernel issues a LogAppend ExecutionWarrant for the append operation (or you treat log append as part of the kernel’s trusted runtime side effects under a fixed allowlist). Pick one and be consistent.
  Given your Phase X template: treat logging as side effect under allowlist → **use warrants**.

**Q22 (when does new constitution take effect?)**
Binding:

* Adoption occurs in cycle **N** under the **old** constitution.
* `effective_cycle = N + 1`.
* New constitution becomes active at the start of cycle N+1.

This avoids mid-cycle law switching.

**Q23 (who can propose AmendmentProposal?)**
Binding:

* `AmendmentProposal.author` may be `reflection` or `user` (via host mediation).
* `AmendmentAdoptionRecord.author` is always `kernel`.
* The LLM is never a direct author; it produces text that the host converts into a `reflection` proposal.

---

# F — Replay

**Q24 (extend replay module or new one?)**
Binding: extend the existing replay harness.
Replay is infrastructure, but it is part of the “physics enforcement” layer. It must be versioned with the kernel.

**Q25 (reload constitution every cycle or only fork boundaries?)**
Binding: reload only at **fork boundaries**, but prohibit mutable carryover.
Implementation pattern:

* Maintain a local map `{hash -> parsed_constitution}` inside the replay run.
* At each cycle, determine active hash; fetch parsed object from the map.
* This is not a “global cache”; it is a deterministic memoization inside `F(log_stream, kernel_version)`.

**Q26 (must the YAML be logged?)**
Binding: **must** be reconstructible from logs.
You already log the full `AmendmentProposal` artifact in `artifacts.jsonl`; that is sufficient. So:

* Not required to duplicate YAML in `constitutions.jsonl`, but required that `artifacts.jsonl` contains the admitted proposal with full YAML string.

---

# G — Gate 8B Mechanics (requires v0.2 structure)

**Q27 (what are “authorities”?)**
Binding: authorities come from `AuthorityModel.authorities[]` (explicit list) in v0.2+.
Not invariants, not arbitrary citation targets.

**Q28 (how count mappings M?)**
Binding: v0.2 must include explicit mapping structure, e.g.:

```yaml
AuthorityModel:
  authorities: [A1, A2, ...]
  permissions:
    - authority: A1
      actions: [Notify, ReadLocal]
    - authority: A2
      actions: [Notify]
```

Then:

* M = sum over permissions of |actions|, after expanding lists and removing duplicates.

**Q29 (where would wildcard appear?)**
In that same explicit mapping structure. That is exactly why you need it.
Wildcards are forbidden in `authority` and in `actions`.

**Q30 (define “globally scoped” structurally)**
Binding definition:

* If an action type’s definition does **not** require `ScopeClaim`, that action is “globally scoped.”
* Scope collapse occurs if **all** actions are globally scoped, or if **no** action requires a scoped warrant.

This is purely structural.

---

# H — Gate 8A Mechanics

**Q31 (detect “executable payloads” without semantics)**
Binding: do it by **schema closure**, not regex.

* Constitution schema must set `additionalProperties: false` broadly.
* Specifically forbid any fields like `script`, `code`, `eval`, `template`, `hook`, `python`, `js`, `expr`.
* If the schema rejects unknown keys, most “payload” attempts die at Gate 7.

Gate 8A then becomes:

* “Reject if any forbidden key exists anywhere” (structural tree walk)
* “Reject if schema contains any field intended to be executed” (i.e., the schema itself prevents it)

No content heuristics.

**Q32 (undefined kernel hooks)**
Binding: there are **no hooks** in X-1.
So “references undefined kernel hooks” reduces to: reject any field in the constitution that attempts to reference runtime function names or tool entry points outside the allowlisted action/tool vocabulary. Again: schema closure.

---

# I — Constitution v0.2 Design

**Q33 (what must change for v0.2 base?)**
Minimum required for X-1 to be meaningful:

1. `amendments_enabled: true` (or equivalent structured policy)
2. Introduce top-level ECK sections exactly:

   * `AmendmentProcedure`
   * `AuthorityModel`
   * `WarrantDefinition`
   * `ScopeSystem`
3. Include explicit authority–action mapping table for density computation
4. Define `AmendmentProcedure` fields as strictly typed
5. Add new refusal reason codes for X-1 gates
6. Add new log streams to LogAppend allowlist enum (see Q36)

**Q34 (reflection_policy forbids “amend”)**
Binding: remove/adjust it in v0.2.
If you keep `llm_forbidden: [amend]` you are forbidding the LLM from proposing amendments at all (because your harness prompt will inevitably include “amendment”). Easiest: remove that token restriction and rely on the structural gates.

**Q35 (new rejection codes?)**
Yes. Binding minimal set:

* `AMENDMENTS_DISABLED`
* `PRIOR_HASH_MISMATCH`
* `ECK_MISSING`
* `SCHEMA_INVALID`
* `PHYSICS_CLAIM_DETECTED`
* `WILDCARD_MAPPING`
* `UNIVERSAL_AUTHORIZATION`
* `SCOPE_COLLAPSE`
* `ENVELOPE_DEGRADED`
* `COOLING_VIOLATION`

**Q36 (add new log names to LogAppend enum?)**
Yes. If LogAppend validates `log_name` against an enum, then v0.2 must include:

* `constitutions`
* `amendment_trace`

---

# J — Budget & Tokenization

**Q37 (proposal size vs B₁ cap)**
Binding: no exemptions in X-1.
If B₁ is 6000 tokens and the proposal doesn’t fit, the correct outcome is **REFUSE with BUDGET_EXHAUSTED**.
Mitigations are out of X-1 scope (patch artifacts are X-2+).

Also bind a constitution size cap (`max_constitution_bytes`) so “unamendable by budget” is an explicit, testable constraint rather than an emergent failure.

**Q38 (session budget B₂?)**
Carry forward whatever X-0L already implemented. X-1 does not add new session-budget machinery. If you have B₂, it applies unchanged.

---

# K — LLM / Harness Integration

**Q39 (how prompt LLM to propose AmendmentProposal?)**
Binding: separate proposal mode prompt template:

* If amendments enabled and there exists a pending/desired amendment context, the host asks the LLM for `AmendmentProposal` objects only.
* Otherwise, ask for normal action proposals.

This is a host-level routing decision, not a kernel one.

**Q40 (canonicalizer changes?)**
Canonicalizer does not need conceptual changes: it’s still JSON canonicalization.
But you must adopt the binding rule from Q3:

* Proposal id binds to `proposed_constitution_hash`, not raw YAML bytes.

**Q41 (need live LLM to close X-1?)**
Not strictly. Closure criterion is “at least one amendment successfully adopted.” That can be achieved via:

* A deterministic fixture proposal (hand-authored AmendmentProposal artifact) injected by the host in tests, without live LLM.

Live LLM is optional for closure; it’s a realism layer.

---

# L — Structural / Organizational

**Q42 (extend RSA-0 vs parallel directory?)**
Binding: implement X-1 as a **new kernel version** that imports RSA-0 components, but does not mutate old behavior silently.

Concrete pattern:

* `kernel/src/rsa0/*` remains unchanged (baseline)
* `kernel/src/rsax1/*` composes rsa0 gates and adds amendment gates

**Q43 (kernel admission pipeline is “immutable,” but we changed it?)**
This is a phase-boundary confusion.

Binding clarification:

* “Kernel physics is immutable” means **immutable during a run under a fixed kernel version**.
* Moving from RSA-0 to RSA-X1 is a new kernel release; that is allowed.
* Once X-1 begins, the X-1 kernel code is frozen.

So: yes, you modify the code between phases; you do not self-modify it during execution.

**Q44 (how many tests?)**
Binding: treat each numbered item in the X-1 test plan as a **family**, with at least:

* 1 positive path
* 1 negative path
  where applicable.

Minimum: ~12–20 total tests is reasonable (not a spec invariant), but you must cover every rejection code at least once.

**Q45 (diff_summary semantics)**
Purely informational, computed by proposer/host, never verified by kernel, never used in gates.

**Q46 (can adopted constitution remove action types?)**
Yes, law can shrink the action space. ECK does not prevent it.
The kernel must still enforce that only declared action types are admissible.
(If you want “action-space non-shrink” as a constraint, that’s a new meta-law and belongs in X-2+.)

**Q47 (ratchet for density_upper_bound?)**
Binding:

* If present in old and new: `new.density_upper_bound <= old.density_upper_bound` (tightening allowed, loosening forbidden).
* If absent in old and present in new: allowed (tightening from implicit 1 to explicit <1).
* If present in old and absent in new: forbidden (that would loosen constraints).

---
Binding answers to **Q48–Q70**. No ambiguity; each resolves to a single implementable rule.

---

# FA — Proposal ID & Constitution Canonicalization

**Q48 (include YAML vs include hash in proposal id)**
Binding: `proposed_constitution_yaml` is **excluded** from the dict used to compute `AmendmentProposal.id`.
Instead, the dict **must include** `proposed_constitution_hash` (and `prior_constitution_hash`).
So the proposal id binds to the constitution content **via its canonical-byte hash**, not via raw YAML bytes.

**Q49 (who normalizes; reject vs normalize-then-hash)**
Binding: the **kernel** performs normalization at Gate 7 and computes `proposed_constitution_hash` from the normalized bytes.
Then it checks equality with the proposal’s `proposed_constitution_hash`.

Implications:

* The proposer/host may emit any whitespace; it does not matter **if** the normalized bytes match the proposal’s hash.
* If the YAML contains **tabs** or **non-UTF-8**, that is a **Gate 7 REFUSE** (invalid encoding), not something to “fix.”
* Trailing spaces and CRLF are normalized by the kernel. Tabs are not normalized; they are rejected.

**Q50 (max bytes checked on raw or canonical bytes)**
Binding: `max_constitution_bytes` applies to **canonical constitution bytes** (post-normalization).
Reason: the hash binds to canonical bytes; the size limit must bind to the same object.

---

# FB — Selector & Decision Routing

**Q51 (if both amendment and action admitted in same cycle)**
Binding: **mutually exclusive per cycle** by decision space partitioning:

Cycle evaluation order:

1. Adoption check (eligible pending proposals)
2. Else amendment proposal selection (if any admissible proposals)
3. Else normal action selection (if any admissible action bundles)
4. Else REFUSE / EXIT

So amendments preempt actions when present and admissible; adoption preempts everything.

**Q52 (decision types; PROPOSE_AMENDMENT?)**
Binding decision set for X-1 kernel:

* `ACTION(bundle)`
* `ADOPT(record)`
* `REFUSE(record)`
* `EXIT(record)`

There is **no** `PROPOSE_AMENDMENT` decision type.

Admitting an AmendmentProposal is not a “decision”; it is an admission outcome recorded in `amendment_trace.jsonl`. The kernel’s *decision* that cycle is still either `ACTION`, `ADOPT`, `REFUSE`, or `EXIT`.

**Q53 (can a cycle admit proposal and do regular action?)**
Binding: **no.** Each cycle yields exactly one of the four decisions above.
You may still *admit* multiple candidates (actions and/or proposals) during evaluation, but execution is single-path.

---

# FC — Kernel Purity & Log-Derived State

**Q54 (kernel can’t read logs; how pending proposals appear)**
Binding: option **(b)** with a precise constraint:

* The host maintains `internal_state` as an in-memory structure.
* Every cycle, the host passes `internal_state` into `policy_core`.
* Every cycle outcome appends a **state delta artifact** (or log entry) sufficient to reconstruct `internal_state` during replay.

So the kernel does not read files, but the *replay harness* reconstructs the same `internal_state` stream from logs and feeds it to `policy_core`.

**Q55 (new observation kind?)**
Binding: **no new observation kind.**
Pending proposals are not observations. They live in `internal_state`, which is already an input to `policy_core`.

If you need to surface “cooling elapsed” information, that is derived from:

* current cycle number (already in internal_state), and
* stored pending proposal metadata in internal_state.

No schema change to observations.

**Q56 (stale invalidation: kernel or host?)**
Binding: **kernel emits it** as a refusal-trace event.

Mechanism:

* When scanning pending proposals each cycle, any proposal whose `prior_constitution_hash != active_constitution_hash` is marked `STALE_PROPOSAL_INVALIDATED` in `amendment_trace.jsonl` (and removed from pending set deterministically).
* Host must not silently drop; the kernel must produce an attributable trace.

---

# FD — ADOPT Decision Mechanics

**Q57 (effective_cycle always N+1 or user-specified?)**
Binding: **always `current_cycle + 1`.**
No deferred adoption in X-1. `effective_cycle` exists for replay clarity and must equal N+1.

**Q58 (ADOPT and LogAppend co-occur?)**
Binding: yes, ADOPT produces compound outputs:

* The decision is `ADOPT(AmendmentAdoptionRecord)`
* Kernel also issues the necessary LogAppend warrants to append:

  * `amendment_trace.jsonl`
  * `constitutions.jsonl`
  * plus the normal per-cycle traces if your architecture does that uniformly

This is not a second “decision.” It is telemetry side effects warrant-issued as usual.

**Q59 (does adoption preempt normal action?)**
Binding: **yes.** Adoption check happens first; if an adoption is selected, normal action candidates are ignored that cycle.

**Q60 (what triggers adoption attempt?)**
Binding: kernel checks all pending proposals **every cycle**, using:

* current cycle number from internal_state
* stored `proposal_cycle` in internal_state
* `cooling_period_cycles` from the active constitution

No special host hint observation is required.

---

# FE — Authority–Action Mapping Structure

**Q61 (explicit mapping vs previously implicit universality)**
Binding: yes, v0.2 must enumerate explicit authority–action permissions.

This is not optional because density computation requires explicit `M` and explicit `A` and `B`.

Yes, it is a structural tightening relative to v0.1.1; that is the point of X-1 becoming enforceable.

**Q62 (authorities vs invariants relationship)**
Binding: **authorities are new identifiers** defined in `AuthorityModel.authorities[]`.

Relationship:

* Invariants remain kernel physics and/or meta constraints.
* Authorities are **citation targets** for law-level authorization.
* Authorities may *reference* invariants in their definitions (as descriptive text or clause IDs), but invariants are not authorities.

So: do not reuse invariant IDs as authority IDs.

**Q63 (what is B: all action types or only mapped action types?)**
Binding: **B = total number of action types declared in the constitution’s closed action set**, not just those appearing in permissions.

Reason: otherwise an attacker can drop actions from the permission table to artificially lower B and game density.

Therefore:

* B counts all action types in `action_space.action_types` (or whatever your canonical list is).
* If an action type is unmapped for all authorities, that is permissible and lowers density, but it also means “no one can do that action.”

---

# FF — v0.2 Constitution Structure

**Q64 (complexity budget?)**
Binding: no line-count budget.
Constraint is structural:

* schema closure (`additionalProperties: false`)
* explicit typing
* explicit key paths
* size caps (`max_constitution_bytes`)

If v0.2 grows, it grows. The real budget is token/cycle proposal budget; that is handled by `max_constitution_bytes` + B₁.

**Q65 (what is WarrantDefinition?)**
Binding: `WarrantDefinition` is a **central structured definition** of warrant semantics at the policy layer, not a relocation of per-action `requires`.

Minimum required contents (structured):

* warrant type name(s) and required fields (ids, action_ref, scope bounds, expiry, single_use)
* statement that **any side-effectful tool requires a warrant** (as a policy clause ID, even though physics enforces it)
* mapping between action types and warrant scope parameters (structured, not prose)

Per-action `requires` may remain, but `WarrantDefinition` is the ECK anchor that must persist.

**Q66 (what is ScopeSystem?)**
Binding: `ScopeSystem` defines **scope types** and the structural rules for scoped warrants.

Minimum contents:

* list of scope types (e.g., `FILE_PATH`, `LOG_STREAM`, `WORKSPACE_PATH`)
* for each action type: whether scope_claim required, and which scope types are valid
* structural constraints for allowlisted roots (`./workspace/**`, `logs/**`, etc.) as data

So it is not “just a top-level copy of flags”; it’s the typed vocabulary the kernel checks.

---

# FG — Repo Organization

**Q67 (move files or add new directory?)**
Binding: do **not** physically move existing files if you already have a flat layout.

Instead:

* Create `kernel/src/rsax1/` as a new module/package
* It imports the existing RSA-0 modules from their current locations
* Over time, you may refactor into `rsa0/` if you want, but X-1 does not require a disruptive move

**Q68 (must RSA-0 tests pass unmodified against X-1 kernel?)**
Binding: yes, RSA-0 tests must still pass **when run in RSA-0 mode**.

Implementation rule:

* keep RSA-0 kernel entrypoint intact (same decision type set, same behavior)
* add a separate X-1 entrypoint or mode flag that enables ADOPT logic and amendment gates
* X-0P and X-0L suites run against RSA-0 mode, unchanged

This preserves the “kernel frozen” claim for Phase X-0 runs while allowing phase progression.

---

# FH — Test & Closure

**Q69 (fixture proposal: must pass gates?)**
Binding: the fixture proposal must pass the **full** pipeline gates 6–8B and be adopted.
You may bypass the LLM, but you may not bypass admission/adoption logic, or you haven’t tested X-1.

So: inject a deterministic AmendmentProposal artifact as if produced by reflection/host, then run the normal cycle(s).

**Q70 (test count closer to 25–30?)**
Binding: yes—expect closer to **25–35** once you cover:

* each new rejection code at least once
* each legacy rejection code regression tests
* positive adoption path
* replay across fork
* stale invalidation
* wildcard + yaml-anchor edge cases

There is no minimum number as a spec invariant, but coverage must include every rejection code and every gate.

---

## One critical binding summary

* Proposal ids bind via `proposed_constitution_hash`, not raw YAML.
* Kernel normalizes (CRLF + trailing spaces) and rejects tabs/non-UTF-8.
* Adoption preempts action; one decision per cycle; ADOPT is a decision type.
* Pending proposals live in replayable internal_state, not observations, not log reads.
* v0.2 must introduce explicit AuthorityModel with explicit permission mappings; B counts the full action set.

Binding answers to **Q71–Q84**. I’ll resolve the contradictions you’ve surfaced by pinning down the object model and cycle semantics. No “or”.

---

# SA — Proposal ID Computation Detail

**Q71 (two dicts: id vs logged artifact)**
Binding: you implement **two canonical serializations** for AmendmentProposal:

1. **Full form** (for logging / replay / human audit)
   Contains `proposed_constitution_yaml` (the raw YAML string) and all other fields.

2. **ID form** (for hashing `id`)
   Contains **all fields except** `proposed_constitution_yaml`.

Concretely:

* `to_dict_full()` → used for JSONL logging and transport
* `to_dict_id()` → used for RFC 8785 canonical JSON and `id = sha256(cjson(to_dict_id()))`

The YAML is not a “separate attachment” in the filesystem sense; it is part of the full artifact, but it is **excluded from identity hashing**.

**Q72 (kernel sees YAML but id excludes it)**
Binding: the artifact object always carries the full YAML string as a normal field.
The *id computation* simply excludes it via `to_dict_id()`.
Kernel gate evaluation uses the **full** object (including YAML) for normalization and checks; id hashing uses the reduced view.

---

# SB — Internal State Extension

**Q73 (internal_state shape; store YAML or hashes?)**
Binding: `internal_state` stores **hashes + minimal metadata**, never the full YAML.

Minimum required fields:

* `cycle_number: int`
* `active_constitution_hash: str`
* `constitution_store: Dict[str, ParsedConstitutionMeta]` (optional; see below)
* `pending_amendments: List[PendingAmendment]`
* `decision_type_history: List[str]` (bounded length)

Where:

`PendingAmendment`:

* `proposal_id: str`
* `prior_constitution_hash: str`
* `proposed_constitution_hash: str`
* `proposal_cycle: int`

Do **not** store the YAML in internal_state.

You also do **not** need `adopted_amendments` in internal_state if adoption is always logged and active hash is updated deterministically. Replay derives it from logs.

About `constitution_store`:

* In the **host/replay harness**, keep a deterministic in-memory map `hash -> parsed constitution` to avoid reparsing each cycle.
* This map is not part of kernel `internal_state` passed into `policy_core` unless you treat it as immutable derived input. Keep it in the host/harness layer.

**Q74 (which cooling period applies; staleness makes moot?)**
Binding: confirmed.
A pending proposal is adoptable only if `prior_constitution_hash == active_constitution_hash`.
Therefore the cooling period applied at adoption time is always the one from the currently active constitution, which is the same constitution the proposal was admitted under (otherwise it’s stale and invalidated).

---

# SC — Decision Space & Cycle Semantics

You correctly spotted an inconsistency: “proposal admission is not a decision” cannot coexist with “one decision per cycle” when proposal admission is the productive outcome.

Fix it by making proposal-queueing an explicit decision type.

**Q75 (what is the decision when a proposal is admitted?)**
Binding: add a fifth decision variant:

* `QUEUE_AMENDMENT(proposal_id)`
  (kernel commits to queueing exactly one admitted AmendmentProposal into pending set that cycle)

So X-1 decision set is:

* `ACTION(bundle)`
* `QUEUE_AMENDMENT(proposal_id)`
* `ADOPT(record)`
* `REFUSE(record)`
* `EXIT(record)`

No other hidden outcomes.

**Q76 (does ADOPT need an ExecutionWarrant?)**
Binding: ADOPT does **not** issue an `ExecutionWarrant` for “adoption,” because adoption is not a tool side effect. The `AmendmentAdoptionRecord` is the authorization artifact for the constitution transition.

However:

* Any **log writes** performed as tools still require their own warrants (e.g., LogAppend warrant), as per Phase X prime directive for side effects.
* So ADOPT yields: `AmendmentAdoptionRecord` + LogAppend warrants (and nothing else).

---

# SD — Gate Re-Validation at Adoption

**Q77 (need YAML each cycle; kernel purity)**
Binding architecture: the kernel does **not** reread logs; the host provides the proposal object.

Mechanism:

* The host maintains an **in-memory proposal registry** for the run: `proposal_id -> full AmendmentProposal (including YAML)`.
* When policy_core returns `QUEUE_AMENDMENT(proposal_id)`, the host adds that proposal to the registry and to `pending_amendments` metadata.
* On each cycle, when evaluating adoption candidates, the host supplies to policy_core the **full objects** for pending proposals as part of the *inputs* (not as observations; as a separate parameter).

So the pure signature becomes:

```
policy_core(observations, constitution, internal_state, pending_proposal_objects) -> Decision
```

Where `pending_proposal_objects` is a deterministic list of full proposals corresponding to `internal_state.pending_amendments`, ordered by stable proposal_id.

Replay harness reconstructs the same proposal registry from `artifacts.jsonl` deterministically, and passes the same objects back in.

No kernel log reading. No internal_state bloat.

**Q78 (adoption re-validation redundant/moot?)**
Partly. Binding clarity:

Adoption-time checks include:

1. `prior_hash == active_hash` (staleness guard)
2. cooling elapsed
3. re-run 7 / 8A / 8B on the proposed constitution YAML

Why re-run 7/8A/8B if nothing changed? Two reasons:

* Detect corrupted in-memory proposal object or log inconsistency (replay safety)
* Ensure adoption is deterministic even if proposal admission logic had a bug

Ratchet step (8B.5) is indeed redundant when hashes match and no intervening adoption occurred, but it is still enforced as part of the gate set. Think of it as belt-and-suspenders, not as a semantic discriminator.

---

# SE — Constitution v0.2 Concrete Structure

**Q79 (sensible authority names; what do citations reference?)**
Binding choice for v0.2:

* Use **policy-domain authorities**, not action-mirroring and not abstract metaphysics.

Recommended minimal authority IDs:

* `AUTH_TELEMETRY`
* `AUTH_IO_READ`
* `AUTH_IO_WRITE` (if WriteLocal enabled)
* `AUTH_GOVERNANCE` (amendment-related permissions)
* `AUTH_EXECUTION` (if you later add exec-like actions)

In X-1, set `authority_reference_mode = BOTH`.

Meaning:

* `authority_citations` must include at least one **Authority ID** (`AUTH_*`) *and* at least one **Clause ID** (`CL-*` or similar) from the constitution.

This gives you two orthogonal citation namespaces:

* Authorities: “who/what class of permission”
* Clauses: “where in text the rule is stated”

**Q80 (does gate 2 resolve AuthorityModel authorities now?)**
Binding: yes. Gate 2 expands its citation resolution to support **two namespaces**:

* Clause citations resolved against `CitationIndex` / clause IDs
* Authority citations resolved against `AuthorityModel.authorities[]`

Gate 2 behavior is phase-dependent; in RSA-0 mode it may only resolve clause IDs. In X-1 mode it must resolve both if `authority_reference_mode` requires it.

This is not proxy arbitration; it’s structural lookup.

**Q81 (WarrantDefinition vs ScopeSystem division of responsibility)**
Binding division:

* `WarrantDefinition` = structure of warrants and their lifecycle constraints
  (fields, single-use, expiry, action_ref binding)

* `ScopeSystem` = structure of scope claims and scope domains
  (scope types, how scope_claim references observations, which scope types are valid for which actions, how scopes are bounded)

Overlap is permitted only via references:

* `WarrantDefinition` references scope types by name (must exist in ScopeSystem)
* ScopeSystem does not redefine warrant fields

**Q82 (ScopeSystem vs io_policy coexist?)**
Binding: they coexist.

* `ScopeSystem` defines **types and validation rules** (structural typing)
* `io_policy` carries **concrete allowlists** (data lists)

ScopeSystem may reference io_policy by key path, but does not replace it.

---

# SF — Repo & Backward Compatibility

**Q83 (mode flag vs wrapper entry point?)**
Binding: wrapper entry point. Do **not** add mode flags to the RSA-0 policy_core.

Create:

* `kernel/src/policy_core_x0.py` (existing behavior, unchanged)
* `kernel/src/policy_core_x1.py` (new entry point)

RSA-0 remains frozen and testable.

**Q84 (avoid duplication; composition preferred?)**
Binding: composition.

`policy_core_x1` does:

1. Determine active constitution (hash) from internal_state (host-provided, already verified)
2. Check adoptable pending proposals → possibly `ADOPT`
3. Else check admissible amendment proposals → possibly `QUEUE_AMENDMENT`
4. Else delegate to `policy_core_x0` for normal action selection → `ACTION/REFUSE/EXIT`

So X-1 reuses the entire RSA-0 action path without copying it.

---

## Net changes you must apply to earlier bindings (so nothing conflicts)

1. Decision set for X-1 is now **five**: ACTION, QUEUE_AMENDMENT, ADOPT, REFUSE, EXIT.
2. Pending proposal *objects* are supplied to policy_core as an explicit input (not logs, not observations, not internal_state).

That resolves every contradiction Opus identified while preserving:

* kernel purity (no IO)
* replay determinism
* single-path execution per cycle
* enforceable adoption semantics
Binding answers to **Q85–Q97**. I’m going to tighten the architecture where Opus correctly spotted remaining ambiguity.

---

# TA — Proposal Artifact Dual Serialization

**Q85 (should all artifacts split full/id forms?)**
Binding: **yes**—all artifacts get the dual interface, even if identical, to keep uniformity and avoid special-casing.

* Default rule: `to_dict_id() == to_dict_full()` for all existing RSA-0 artifacts.
* Exception: `AmendmentProposal.to_dict_id()` excludes `proposed_constitution_yaml`.

This keeps the framework coherent: “artifact identity serialization” is a first-class concept.

---

# TB — `policy_core_x1` Signature & Inputs

**Q86 (where do candidates and new amendment proposals enter?)**
Binding inputs for X-1:

```
policy_core_x1(
  observations,
  action_candidates,            # CandidateBundles for normal actions
  amendment_candidates,         # AmendmentProposals proposed this cycle (full objects)
  pending_amendment_candidates, # AmendmentProposals previously queued (full objects)
  constitution,                 # active constitution object
  internal_state
) -> PolicyOutput
```

Rules:

* `action_candidates` is exactly what RSA-0 already consumes.
* `amendment_candidates` is the “new proposals this cycle” pool.
* `pending_amendment_candidates` is the “queued from prior cycles” pool.

No mixing with CandidateBundles. AmendmentProposals are separate channel inputs.

**Q87 (return type: shared PolicyOutput vs new type?)**
Binding: **shared `PolicyOutput`** extended to support the 5 decision variants and X-1 artifacts.

So:

* `PolicyOutput` is the single return type used by both X0 and X1.
* X0 continues to return only ACTION/REFUSE/EXIT.
* X1 may return ACTION/QUEUE_AMENDMENT/ADOPT/REFUSE/EXIT.

`PolicyOutput` structure (binding minimal fields):

* `decision_type`
* `primary_artifacts` (e.g., selected ActionBundle or AmendmentAdoptionRecord)
* `warrants` (ExecutionWarrant + LogAppend warrants as needed)
* `trace_records` (admission/selector/amendment traces)
* `state_delta` (host-applied internal_state update instructions)

X0 can leave new fields empty.

---

# TC — QUEUE_AMENDMENT Semantics

**Q88 (side effects; warrant?)**
Binding:

When decision is `QUEUE_AMENDMENT`:

* Kernel emits:

  * a `RefusalRecord` **only if** no proposal was admissible; otherwise none
  * an **amendment trace entry** describing admission + selection + queueing
  * a `state_delta` instructing host to append a `PendingAmendment` entry
* Side effects:

  * LogAppend writes (amendment_trace + normal traces) via **LogAppend warrants**
* There is **no ExecutionWarrant** for queueing itself. Queueing is state update + logging, not a tool-executed side effect beyond LogAppend.

**Q89 (selector for amendment proposals?)**
Binding: yes, amendment proposals use a selector.

* First, run amendment admission gates on all `amendment_candidates`.
* If ≥1 admitted, select exactly one by deterministic rule:

  * choose lexicographically smallest `AmendmentProposal.id`
* Then decision is `QUEUE_AMENDMENT(selected_proposal_id)`.

This mirrors action selection without semantic scoring.

**Q90 (what does QUEUE_AMENDMENT output contain?)**
Binding: kernel outputs:

* `selected_proposal_id`
* `proposal_cycle = current_cycle` (explicit in state_delta)
* `prior_constitution_hash`
* `proposed_constitution_hash`

Host responsibilities:

* Persist the full proposal object in its proposal registry keyed by `proposal_id`
* Append `PendingAmendment` to internal_state using the state_delta
* Append the full proposal to `artifacts.jsonl` (see Q91)

Kernel does not construct host storage objects; it emits deterministic instructions.

---

# TD — Constitution Store & Replay

**Q91 (when is full AmendmentProposal logged?)**
Binding: the full AmendmentProposal is logged **only when it becomes committed state**, i.e., when it is selected and queued.

So:

* Proposals entering the cycle as candidates are **not** necessarily logged.
* The selected proposal is logged to `artifacts.jsonl` in the same cycle as `QUEUE_AMENDMENT`.

This keeps logs minimal and avoids logging untrusted spam proposals.

**Q92 (where does host get new constitution for cycle N+1?)**
Binding: from the proposal registry.

Mechanism:

* `PendingAmendment` contains `proposal_id` and `proposed_constitution_hash`.
* The host looks up the full `AmendmentProposal` by id in the registry, extracts YAML, normalizes+parses, and inserts into a live `{hash -> parsed_constitution}` map.

Yes: the host maintains the same deterministic map during live execution as replay does.

Source of truth:

* proposal registry → constitution YAML → canonical bytes → hash
* must match `proposed_constitution_hash` and adoption record’s `new_constitution_hash`

No fetching from logs during live run.

---

# TE — Gate 2 Expansion & Citation Namespaces

**Q93 (citation format for authorities; CitationIndex changes?)**
Binding formats:

* Clause citation (existing pattern):
  `constitution:<hash>#CL-...` (or whatever your clause IDs are)

* Authority citation:
  `authority:<hash>#AUTH_IO_READ`

Where `<hash>` is the active constitution hash at the time the artifact is created/admitted.

Resolution:

* Clause citations resolve through existing `CitationIndex` (built from constitution clauses).
* Authority citations resolve through `AuthorityModel.authorities[]` lookup.

Do **not** overload CitationIndex with authorities; keep a separate authority resolver.

**Q94 (BOTH means also enforce namespace presence?)**
Binding: yes.

When `authority_reference_mode = BOTH`, Gate 2 must enforce:

* at least one resolvable clause citation, AND
* at least one resolvable authority citation

In addition to “all citations resolve.”

This is a structural condition, not semantic evaluation.

---

# TF — v0.2 Constitution Design Decisions

**Q95 (AUTH_GOVERNANCE mapping vs density formula)**
Binding: the density model applies to **actions**, and amendments are not actions. But governance authority must still exist as a citation target.

Therefore:

* `AuthorityModel.authorities[]` includes `AUTH_GOVERNANCE`.
* `AuthorityModel.permissions` includes governance permissions in a separate section:

```yaml
AuthorityModel:
  authorities: [...]
  action_permissions:   # used for density (A×B, M)
    - authority: AUTH_TELEMETRY
      actions: [LogAppend, Notify]
    ...
  amendment_permissions: # NOT part of density
    - authority: AUTH_GOVERNANCE
      amendments: [ConstitutionReplacement]
```

Density counts:

* A = number of distinct authorities appearing in `action_permissions` only
* B = number of action types in closed action set
* M = mappings in `action_permissions` only

Amendment permissions are checked structurally at Gate 6/8B.4 via citations, not via density.

**Q96 (new schema file or modify existing?)**
Binding: v0.2 gets a **new schema file** and a new YAML file.

* `rsa_constitution.v0.2.yaml`
* `rsa_constitution.v0.2.schema.json`
* `rsa_constitution.v0.2.sha256`

Do not mutate the v0.1 schema. v0.1 remains frozen evidence of Phase X-0.

**Q97 (max_constitution_bytes value?)**
Binding: set `max_constitution_bytes = 32768` (32 KiB) for v0.2.

Rationale:

* comfortably covers a ~15–20KB constitution
* leaves room for growth while still fitting typical B₁ constraints
* makes “unamendable by budget” experimentally reachable

Gate enforcement uses **canonical bytes** length (post-normalization), per Q50.

---

## Consolidated “now unambiguous” X-1 kernel/host contract

* All artifacts implement `to_dict_full()` and `to_dict_id()`. Only AmendmentProposal differs.
* X-1 policy_core input separates action candidates, new amendment candidates, pending amendment candidates.
* X-1 outputs a single `PolicyOutput` extended with QUEUE_AMENDMENT/ADOPT.
* Full AmendmentProposal is logged only when queued (committed).
* Host maintains proposal registry + constitution cache map.
* Authorities use `authority:<hash>#AUTH_*` citations; clauses use `constitution:<hash>#CL-*`. BOTH requires at least one of each.
Binding answers to **Q98–Q106**.

---

# UA — PolicyOutput & state_delta

**Q98 (does kernel always emit state_delta?)**
Binding: **state_delta is X-1 only, and emitted only when needed.**

* RSA-0 contract remains unchanged: host advances `cycle_number`, appends decision history, etc.
* X-1 adds an optional `state_delta` field to `PolicyOutput`.

  * For `ACTION/REFUSE/EXIT`: `state_delta = null` (host does the usual bookkeeping).
  * For `QUEUE_AMENDMENT` and `ADOPT`: `state_delta` is required and non-null.

So: you do **not** rewrite RSA-0 host logic; you extend it to apply `state_delta` when present.

**Q99 (what does ADOPT state_delta do vs host derives?)**
Binding: **ADOPT state_delta fully specifies state transitions.** No host “derivation” beyond applying it.

ADOPT `state_delta` must instruct the host to:

1. **Remove** the adopted proposal from `pending_amendments`.
2. **Set** `active_constitution_hash` to the adopted `new_constitution_hash`, effective **next cycle** (store as `pending_constitution_hash_next_cycle` or similar).
3. **Invalidate** all remaining pending proposals (emit trace events for each) whose `prior_constitution_hash != new_active_hash` once the new hash becomes active.

   * If you prefer, do invalidation immediately after adoption with respect to `new_constitution_hash` (deterministic either way). Binding choice: **invalidate immediately at adoption time**.

Host must not silently drop stale proposals; the kernel provides explicit invalidation instructions and trace entries.

---

# UB — Amendment Admission Pipeline Detail

**Q100 (do new amendment proposals pass 0–5?)**
Binding: new amendment proposals pass an **amendment-specific** pipeline that reuses only generic structure from 0–5, then runs 6–8B.

Concretely, for `amendment_candidates`:

1. **Completeness (amendment schema)** — required fields present on AmendmentProposal
2. **Authority Citation (expanded gate 2)** — citations resolve + BOTH requirement satisfied
3. **Scope Claim (structural)** — scope_claim present and references observation ids/hashes as required
4. **Constitution Compliance (amendment enablement)** — amendments_enabled true + prior_hash matches active
5. **IO Allowlist** — **skip** (no IO fields)
6. **Amendment Authorization** — AmendmentProcedure exists + structured
7. **Full Replacement Integrity** — canonicalize YAML, hash match, schema valid, ECK present
   8A. **Physics Claim Rejection**
   8B. **Structural Constraint Preservation**

So: it’s not “only 6–8B,” and it’s not the action bundle 0–5 either. It’s a type-switched variant.

**Q101 (duplicate proposal id collision)**
Binding: treat identical IDs as **idempotent duplicates**, not an error.

* If two proposals have identical `to_dict_id()` → they are the same proposal by definition.
* If they carry different `proposed_constitution_yaml` but same `proposed_constitution_hash`, that means the YAML differs only in non-canonical features (CRLF, trailing spaces) and is effectively the same constitution. Accept.
* If they somehow carry different canonical bytes yet same `proposed_constitution_hash`, that’s a cryptographic collision; ignore as out of scope.

Selector behavior:

* If multiple admitted proposals share the same ID, selecting that ID is deterministic; the host should keep the first-seen full form and ignore later duplicates, logging `DUPLICATE_PROPOSAL_IGNORED`.

---

# UC — Citation Format & clause IDs

**Q102 (clause IDs; must they be CL-*?)**
Binding: **clause IDs must be explicit stable IDs, and ECK sections must expose clause IDs.** Do not cite raw key paths.

Rule:

* Every citable clause has an explicit `id: CL-...` field inside the YAML (including ECK-related clauses like amendment authorization, envelope, thresholds).
* `constitution:<hash>#CL-...` is the only valid clause citation form.

Therefore:

* `constitution:<hash>#AmendmentProcedure` is **not** a valid clause citation.
* Invariant IDs like `INV-*` may exist, but in X-1 they are not clause citations unless you explicitly treat them as `CL-*`. Binding choice: keep `INV-*` as non-citable physics labels; use `CL-*` for citable law clauses.

**Q103 (where does authority resolver live?)**
Binding: authority resolver is built from the parsed constitution and attached to the constitution object:

* `constitution.citation_index` (existing)
* `constitution.authority_index` (new) — a set/map of authority IDs + permissions info

Gate 2 receives the constitution object and uses both indices.

---

# UD — v0.2 Constitution Concrete Content

**Q104 (ConstitutionReplacement enum; future extension?)**
Binding: yes, X-1 supports exactly **one** amendment type:

* `ConstitutionReplacement`

Treat it as an enum value in the schema:

```yaml
amendment_permissions:
  - authority: AUTH_GOVERNANCE
    amendments: [ConstitutionReplacement]
```

Future phases may add:

* `PatchAmendment`
* `SectionAmendment`
* etc.

But X-1 is replacement-only.

**Q105 (Exit as action type or not?)**
Binding: **remove Exit from action_space.action_types** in v0.2.

Exit is a **decision**, not an action. Keeping it as an action type pollutes density B and creates needless ambiguity.

So v0.2 closed action set is:

* `Notify`
* `ReadLocal`
* `WriteLocal` (if enabled)
* `LogAppend`

`EXIT` remains a policy_core decision variant governed by constitution rules, but not part of the action permission matrix.

**Q106 (minimal v0.2 scope; what changes?)**
Binding: v0.2 changes are **minimal and structural**, but you must update obvious metadata.

Carry forward all v0.1.1 content unchanged *except where structurally necessary for X-1*. Required changes:

1. Update version metadata (`version: v0.2`, date, hash files, changelog entry).
2. Enable amendments (structured, not free text).
3. Add the four ECK top-level sections with concrete typed content:

   * AmendmentProcedure (typed, ratchetable)
   * AuthorityModel (authorities + action_permissions + amendment_permissions)
   * WarrantDefinition
   * ScopeSystem
4. Add new log streams to LogAppend allowlist enum.
5. Add new rejection codes.
6. Remove Exit from action_types if it was there.
7. Ensure schema closure (`additionalProperties: false`) and strict typing for all new fields.

No other policy changes unless required to satisfy these structural constraints.

---

Binding answers to **Q107–Q110**.

---

# VA — Citation Transition (INV-* → CL-*)

**Q107 (INV-* citable or not; transition impact)**
Opus is right: making `INV-*` non-citable would explode RSA-0 compatibility for no structural gain.

Binding correction:

* **`INV-*` remains citable.**
* **`CL-*` is additive**, not a replacement, in v0.2 and X-1.

So:

**(a)** v0.2 introduces `CL-*` IDs for new law clauses (especially ECK + amendment rules), but existing invariant citations remain valid.
**(b)** Gate 2 in X-1 mode must accept both:

* `constitution:<hash>#INV-*` (legacy invariant citations)
* `constitution:<hash>#CL-*` (law clause citations)
  **(c)** Yes, it’s intentional to keep backward compatibility. `CL-*` becomes the required namespace for amendment procedure references; actions may cite either `INV-*` or `CL-*` depending on `authority_reference_mode`.

Refined binding rule for X-1:

* **Clause citations:** `constitution:<hash>#CL-*`
* **Invariant citations:** `constitution:<hash>#INV-*`
* **Authority citations:** `authority:<hash>#AUTH_*`

And `authority_reference_mode = BOTH` means:

* at least one **authority** citation, and
* at least one **clause-or-invariant** citation (`CL-*` or `INV-*`).

This preserves RSA-0 fixtures and keeps the “BOTH” requirement meaningful.

---

# VB — Stale Invalidation Timing

**Q108 (invalidate against new hash though it activates N+1?)**
Binding: invalidate **forward-looking** at adoption time against the **adopted new constitution hash**, even though it becomes active at N+1.

So during cycle N when ADOPT occurs:

* Compute `new_hash = adoption_record.new_constitution_hash`
* For every remaining pending proposal `p`:

  * If `p.prior_constitution_hash != new_hash`, mark it stale and remove it (with trace event)

Rationale:

* Those proposals are logically stale the moment you commit to switching to the new law next cycle.
* Doing it immediately avoids a one-cycle ambiguity window and keeps replay simple.

So: invalidation key is `new_constitution_hash`, not `current_active_hash`.

---

# VC — Amendment Scope Claims

**Q109 (scope_claim meaning for amendments)**
Binding: **AmendmentProposals do not require ScopeClaim.** Drop it from the amendment admission pipeline.

Reason: scope is an execution boundary concept for side effects; amendment proposals are policy artifacts. Forcing a scope claim here is fake structure.

Replace with a dedicated structural field already present:

* `authority_citations` must cite the AmendmentProcedure clause (CL-*), plus governance authority (AUTH_*), per BOTH.
* `prior_constitution_hash` already binds the proposal to the current law context.

So:

* No `scope_claim` field inside AmendmentProposal.
* Gate 3 (Scope Claim) is **skipped** for amendment proposals.

This resolves the forced-observation problem cleanly.

---

# VD — v0.2 Draft Readiness

**Q110 (is the v0.2 delta checklist complete?)**
It’s almost complete. Two missing binding items:

1. **Explicit typed `max_candidates_per_cycle` / proposal budget fields** for amendments (if your constitution currently budgets only action proposals). X-1 needs a budget cap for `amendment_candidates` selection to prevent proposal spam becoming an implicit proxy channel. If you already have `max_candidates_per_cycle` global, reuse it; otherwise add:

   * `amendment_policy.max_amendment_candidates_per_cycle`
   * `amendment_policy.max_pending_amendments`

2. **Amendment artifact enablement in the schema**: since AmendmentProposal is a new artifact type, v0.2 must explicitly include it in the closed artifact/type vocabulary (even if it is “separate channel”). Otherwise the “closed set” claim is violated.

Everything else on Opus’s checklist is correct **with one correction** from Q107:

* Do **not** make `INV-*` non-citable. Keep it, add `CL-*`.

So the binding v0.2 delta checklist is:

* Add ECK sections (4)
* Add `CL-*` IDs for new clauses (keep `INV-*` valid)
* Add explicit action_permissions mapping + amendment_permissions
* Enable amendments + set authority_reference_mode = BOTH
* Add new log streams to LogAppend enum
* Add new rejection codes
* Remove Exit from action_types (Exit remains decision)
* Add `max_constitution_bytes: 32768`
* Enforce schema closure (`additionalProperties:false`)
* Add amendment budget caps / candidate caps (or reuse existing caps explicitly)
* Add AmendmentProposal / AmendmentAdoptionRecord to closed artifact vocabulary

That closes the Q&A in a way that’s implementable without breaking RSA-0.
