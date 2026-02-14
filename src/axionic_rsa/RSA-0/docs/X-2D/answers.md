# A — Architectural Scope & Kernel Boundary

**A1 (Q1): Where do X2DSessionStart/End live?**
**Harness layer only.** They are *not* kernel artifacts and must never enter `policy_core_x2` admission. “Admitted” here means: **schema-validated, hashed, logged append-only before cycle 1**, then used to drive deterministic input generation. They do not require ExecutionWarrants; they are harness metadata.

**A2 (Q2): Gate number collision**
Yes: use a distinct namespace. Use **Gate 6D / 7D / 8D** for session admission (D = Dynamics harness). Kernel gates retain their existing names (6T/7T/8C/8R etc). The spec should never reuse a bare “Gate 7” without suffix.

**A3 (Q3): Density step in cycle flow vs Gate 8C.7**
X-2D requires **an explicit cycle-level density enforcement point** in the orchestration, *but it does not require moving density out of Gate 8C.7.*
Concrete binding:

* **During grant admission**: Gate 8C.7 enforces density for each grant sequentially.
* **Post-Grant, Pre-Action**: the harness must compute density from the resulting active set and assert it remains below bound **before any action evaluation**.

So: **keep Gate 8C.7** AND add **Cycle Step 4 assertion**. This satisfies the “enforced point” requirement and catches “density increased by bookkeeping bug” pathologies.

**A4 (Q4): prune_for_density vs rejection**
Under X-2D, **pruning is forbidden**. The semantics are **hard rejection**, not greedy repair.
Binding rule: `ActiveTreatySet.prune_for_density()` must be disabled (or unreachable) in X-2D runs. If code currently prunes, replace with: “reject the offending grant(s) with `DENSITY_MARGIN_VIOLATION`.”
If you want pruning later, that is a new semantic and belongs in a different stage.

**A5 (Q5): Directory placement**
Place X-2D under **`profiling/x2d/`** to match established pattern. The replay modules should remain in `replay/src/` only if they’re generic replay utilities.
So:

* `profiling/x2d/{runner,generators,metrics}.py`
* `replay/src/` unchanged except for any *shared* helpers you already use across harnesses.

---

# B — Cycle Ordering & Topological Time

**B6 (Q6): per-grant check vs aggregate check**
You need both, but they serve different roles:

* Gate 8C.7 prevents admitting an illegal grant.
* The cycle-level check guarantees that after all grant+revoke processing and treaty revalidation, density is still below bound before action eval.

So: **sequential per-grant enforcement** + **aggregate cycle assertion**.

**B7 (Q7): preemption mechanism beyond ordering?**
No additional mechanism. X-2D is making this an **explicit invariant** and requiring **topological sorting** so stream order can’t subvert it. The kernel ordering already implies it; X-2D forbids implementations that accidentally execute stream order.

**B8 (Q8): explicit expiry sweep vs implicit filtering**
Implicit filtering is fine **for correctness**, but X-2D wants auditability under churn.
Binding: add an explicit **expiry-sweep record** to metrics/logging (not a new artifact): list of grant_ids that expired at cycle boundary. This is instrumentation, not semantics.

**B9 (Q9): grants before revocations vs existing CL-CYCLE-ORDERING**
Authoritative order for X-2D is:

1. amendment adoption
2. **grants**
3. **revocations**
4. density enforcement
5. RSA actions
6. delegated actions

Reason: You explicitly wanted “net-zero churn” in a cycle (grant then revoke) without action exposure, and you wanted revocation dominance over actions, not necessarily over grants. This ordering is coherent if you define revocation as “effective for same-cycle action evaluation,” which you do.

But you must make it consistent with existing kernel CL-CYCLE-ORDERING. So do this:

* Keep kernel internals as-is, but **the harness must feed inputs into policy_core in buckets** such that effective behavior matches X-2D order. If kernel currently processes revocations before grants, then for X-2D either:

  * (Preferred) adjust CL-CYCLE-ORDERING for X-2D runs under a feature flag (still deterministic), or
  * run two admission passes per cycle: one for grants, then one for revocations, then actions.

I recommend the second because it avoids “changing kernel physics” globally.

---

# C — Amendment–Treaty Interaction & Supremacy

**C10 (Q10): What does revalidation mean concretely?**
Not full re-admission (do not rerun 6T/7T/8C over original artifact). Revalidation is a **narrow, deterministic authorization-validity check** against the *current constitution*:

Minimum required checks:

* granted_actions still in closed action set
* treaty does not authorize any constitution-banned action
* scope monotonicity still holds under tightened scope rules (if scope rules can tighten)
* density bound compliance under current bound (see C14)
* no delegation depth/cycle changes (these should be structural and invariant)

Do **not** re-run signature or original author citations; those were for admission, not continued validity.

**C11 (Q11): What happens to invalidated treaties?**
Do **not** synthesize revocations (that is a new semantic artifact).
Mechanism: keep the grant in the historical log, but mark it **inactive/non-authorizing** in the active set via deterministic “invalidated_by_constitution_at_cycle = c” state that is reconstructible from logs + constitution transitions.

So: present in history; excluded from authorization resolution.

**C12 (Q12): Do we need an explicit step between amendment and revocations?**
Yes. Under X-2D ordering, revalidation happens after amendment adoption and before action evaluation. Where it sits relative to grants/revokes is:

* Adopt amendment
* Admit grants
* Admit revokes
* **Revalidate active set under new constitution** (or do it twice if you want: once after adoption, once after grant/revoke; but one post-mutation revalidation is sufficient)
* Enforce density
* Actions

This ensures “kill switch” works under churn.

**C13 (Q13): Full revoke vs strip banned actions**
Full invalidation of the treaty (non-authorizing). No partial stripping.
Partial stripping is a new semantic (treaty mutation) and violates “no new authority semantics.”
So: if any granted action becomes prohibited, the treaty becomes non-authorizing.

**C14 (Q14): density_upper_bound tightens and active set exceeds new bound**
Under X-2D: **fail closed** by **invalidating treaties deterministically until density is below bound**, but you must choose a deterministic rule that is not “greedy pruning” unless it is explicitly specified.

Best rule (deterministic, auditable, non-heuristic):

* Invalidate active treaties in **reverse admission time order** (newest first) until density < bound.
* Log each invalidation as “constitution_density_tightening_invalidation”.

This is not “prune_for_density” because it is constitutional supremacy enforcement, not opportunistic maintenance. But it is still a form of pruning—so name it honestly and bind it.

If you dislike invalidation by order, the alternative is: **amendment adoption fails** if it would make the system exceed bound. That’s also coherent, but it changes X-1 adoption semantics. For X-2D, keep adoption and invalidate treaties.

---

# D — Density & Proximity

**D15 (Q15): What is δ for?**
Both:

* Generator targeting: try to keep density within `[upper_bound − δ, upper_bound)` for D-SAT/D-EDGE.
* Reporting: count cycles “near-boundary” if density ≥ upper_bound − δ.

**D16 (Q16): feasibility of near-boundary density**
Yes: harness must choose grantee_count and grant patterns to make the band reachable. If B is small, density jumps in coarse increments, so you’ll need either:

* more authorities (increase A), or
* wider action set B (not allowed), or
* more fine-grained scope subdivisions if M counts (authority, action) pairs independent of scope granularity.

Given your density definition ignores scope granularity, near-boundary requires **many authorities with many action permissions**. So expect grantee_count in the tens to hundreds, depending on B.

**D17 (Q17): density can increase when A drops**
Correct observation. That’s why X-2D’s “all execution points” implies checks after revocations and after invalidations.
Binding: compute density at least at:

* Post-Grant/Pre-Action
* Post-Revocation/Pre-Action (if revokes change A)
* Post-Revalidation/Pre-Action (if invalidations change A/M)

Net: a single “Step 4” computation after all mutations (grant/revoke/revalidate/expire) is enough.

**D18 (Q18): preregistered band**
Yes: define D-EDGE band as `[upper_bound − δ, upper_bound)` and preregister δ.

---

# E — Generators & Determinism

**E19 (Q19): precompute whole stream vs seeded per-cycle**
Either is fine if deterministic. Prefer **precompute the entire N-cycle plan** and hash it at session start; it simplifies replay and makes “identical input” literal.

**E20 (Q20): high-frequency churn target**
Use a preregistered target churn rate per window `W`. Example: aim for churn_W in [0.5, 2.0] depending on whether you allow multiple events per cycle. The important part is: **explicitly encode the target** and measure deviation.

**E21 (Q21): invalid classes closed?**
Closed set for X-2D. Keep exactly the enumerated invalid classes so reason code stability is testable and attribution clean.

**E22 (Q22): grantee identities upfront?**
Generate upfront and bind to session start seeds. No mid-session identity introduction. Mid-session identities add a new moving part and complicate audit.

**E23 (Q23): amendment cadence**
Multiple tightenings. Minimum: 3 adoption events per D-RATCHET session. Cadence preregistered (e.g., every ⌊N/4⌋ cycles). Must include at least one action-ban and at least one density_upper_bound tightening.

---

# F — State Hash Chain & Replay

**F24 (Q24): hash chain components**
Do not extend hash chain components. Fold new events into the existing categories:

* treaty/amendment artifacts → artifacts component
* admission decisions + gate traces → admission component
* selection (if any) → selector component
* execution warrants/results → execution component

Metrics logs do not enter the state hash chain unless you already hash all logs (you probably don’t). The chain should hash *decisions and effects*, not derived metrics.

**F25 (Q25): same kernel_version_id?**
If `kernel_version_id` semantically means “the replay protocol,” and you changed cycle topology behavior (batch sorting + revalidation), then strictly speaking that is a **new replay protocol** and deserves a new `kernel_version_id`.
But if X-0E’s `kernel_version_id` already denotes “deterministic replay over logged admissions/actions,” and you are not changing the replay formula, just exercising more artifact types, you can keep it.

Binding decision: **keep the same kernel_version_id** only if:

* topological sorting is implemented purely in the harness input batching (not in kernel)
* revalidation/invalidation logic is implemented as deterministic state transitions already represented in hashed admission events

If either changes the protocol, bump kernel_version_id.

Given your insistence on pinned identity, I recommend: **do not bump**; implement topology and revalidation as *deterministically logged admission events* so the protocol stays the same.

**F26 (Q26): reconstruct from scratch each cycle?**
Forward reconstruction is acceptable as long as:

* it is a pure function of prior state + current cycle inputs,
* it produces identical results on replay,
* it does not consult external state.

So: incremental active set update is fine.

**F27 (Q27): explicit expiry events?**
No new expiry artifacts. Expiry is derived from `(grant_cycle, duration_cycles, current_cycle)`. Log expiry in metrics for audit only.

---

# G — Metrics, Logging & Instrumentation

**G28 (Q28): use X-0E append_jsonl?**
Yes. Use the same append-only mechanism (fsync discipline) so logs participate in the same operational integrity assumptions.

**G29 (Q29): extend existing logs vs add adjacent records**
Do not mutate existing frozen log schema. Add **adjacent records** in new X-2D logs keyed by `cycle_id` and `artifact_id`. Keep the original logs stable.

**G30 (Q30): state_hash_start/end meaning**
`state_hash_start` = previous cycle’s `state_hash_end` (or genesis for cycle 1).
`state_hash_end` = the chain tip after completing the full cycle.

No sub-cycle hashes unless already present.

**G31 (Q31): sliding vs non-overlapping windows**
Non-overlapping windows. It simplifies determinism and reporting. If you want sliding later, add it as a derived metric, not a primary log stream.

---

# H — Session Schema & Admission

**H32 (Q32): record initial vs minimum density bound**
Record both:

* `density_upper_bound_initial`
* `density_upper_bound_min_observed`
* and log per-cycle bound in `x2d_metrics.jsonl` as `density_upper_bound_active`

**H33 (Q33): amendment_schedule element schema**
Structured. Each element must include:

* `cycle`
* `amendment_artifact_id` (or full canonical payload hash)
* `amendment_hash`
  No free-text schedule.

**H34 (Q34): which Gate 7?**
Session Gate **7D** (not 7T).

**H35 (Q35): “enabled” meaning**
Both:

* constitution includes amendment procedure (structural capability)
* code modules for X-1 adoption are importable (implementation capability)

Fail session admission if either is false.

---

# I — Tests & Closure

**I36 (Q36): complete suite?**
Not complete. Those are minimum acceptance tests. Add explicit tests for:

* revocation monotonicity
* log schema integrity
* per-family session runner sanity

**I37 (Q37): forcing persistent deadlock**
Do not “force deadlock” via illegal candidates. Use a **pathological constitution** (still valid) that makes two constraints mutually incompatible for a window, then verify the classifier and failure attribution. This keeps the test honest: deadlock is structural, not injected invalidity.

**I38 (Q38): can revocation increase M?**
Mathematically it should not. This criterion is explicitly a **bug catcher** for:

* incorrect recomputation of A or M
* stale caches
* off-by-one in effective resolution closure

Keep it.

**I39 (Q39): chain/cycle reachability under churn**
Yes: you’re testing that the invariant holds under rapid mutation and that no “transient window” appears due to ordering/caching mistakes. It’s a stress assertion, not a new rule.

---

# J — Parameters & Preregistration

**J40 (Q40): when frozen?**
Freeze after implementation is complete and unit tests pass, before any “production” run. Same pattern as X-0P/X-0L: preregister parameters, then execute.

**J41 (Q41): expected N**
Hundreds at minimum; thousands for D-EDGE if performance allows. You don’t need to pick now; but preregistering N too small defeats the point.

**J42 (Q42): sessions per family**
At least 3 per family with different seeds if you want statistical confidence in “no flakiness.” If you want pure existence/stability, 1 per family is acceptable but weaker.

**J43 (Q43): seeds schema**
Structured object with named integer seeds:

* `seed_treaty_stream`
* `seed_action_stream`
* `seed_invalid_injector`
* `seed_amendment_stream`
  No “random” seed derivation.

---

# K — Existing Code Interaction

**K44 (Q44): extract from PolicyOutputX2 vs extend**
Extract post hoc in harness. Do not change `PolicyOutputX2` unless you are willing to bump interfaces. X-2D should be a wrapper, not a kernel mutation.

**K45 (Q45): density_upper_bound return**
Existing return signature is sufficient. Log `density_upper_bound_active` separately from constitution state.

**K46 (Q46): use X-0E CLI?**
Use a dedicated X-2D runner that invokes `policy_core_x2` directly, like other profiling harnesses. The CLI is for interactive runs; harness is for deterministic sessions.

**K47 (Q47): revalidation trigger code exists?**
Assume it does not. X-2D must implement the revalidation cascade deterministically in the harness/kernel boundary as you decide. The safe binding is: implement revalidation in the kernel’s treaty resolution layer (because it affects authorization), but keep orchestration in harness.

---

# L — Failure Attribution & Gate Instability

**L48 (Q48): rejection_class field**
Do not add it to frozen events. Derive it deterministically from reason_code via a fixed mapping table in harness, and log the derived class in X-2D logs.

**L49 (Q49): compare canonical bytes vs raw log lines**
Compare canonicalized, deterministic fields only. Never compare host timestamps. Use a canonical JSON form (JCS) over the stability tuple:
`(gate_id, reason_code, rejection_class, state_hash_start, artifact_hash)`.

**L50 (Q50): “identical state” verification**
Use `state_hash_at_cycle_start` as the identifier. That’s the whole point of having it. No need to canonicalize full internal state.

---

# M — Edge Cases & D-EDGE Specifics

**M51 (Q51): maximal lawful churn**
Defined as: maximize `(G_W + R_W + E_W)` subject to:

* no density breach
* no invalid admission
* staying within near-boundary band for the majority of cycles (preregister threshold)

**M52 (Q52): if generator can’t maintain band**
Generator must be feasibility-aware. If it can’t maintain the band, that is a **generator failure** and the session is invalid (abort, fix generator, re-freeze). D-EDGE is meaningless otherwise.

**M53 (Q53): targeting band in notes?**
No. Create a structured field in session start:

* `target_density_band_low`
* `target_density_band_high`

---

# N — Report & Deliverables

**N54 (Q54): report format**
Follow existing harness pattern: single structured JSON report per session plus an aggregate per-family summary JSON; render the “table” as derived output (markdown/CSV) but don’t make markdown normative.

**N55 (Q55): implementation report update**
Yes: add sections for X-2D architecture and closure results following established pattern.

---

## The two real fixes Opus is pointing at

1. **Ordering mismatch (grants vs revokes)** must be made authoritative and implemented without changing kernel “physics” globally. Use harness bucketing or a feature flag.
2. **Density semantics (reject vs prune)** must be bound: X-2D is reject-only. Pruning is out.

If you adopt these bindings, Opus’s 55 questions collapse into “implementation tasks,” not ambiguities.

Good follow-ups. These are the points where “topological time” meets a real codebase.

I’m going to answer with **binding implementation decisions**. No dithering.

---

# O — Cycle Ordering & Harness Bucketing

## O56 — One call vs two calls per cycle?

**Do not call `policy_core_x2` twice per cycle.**
Two-pass is semantically dirty (see O58) and complicates hash-chain attribution.

**Correct approach:** call `policy_core_x2` **once per cycle**, but ensure it implements the X-2D binding order internally **for that run mode**.

That implies: X-2D requires an ordering override inside `policy_core_x2` (or in the cycle driver immediately above it) so that within Step 1, grants are processed before revocations.

If you refuse any kernel-internal change at all, you cannot guarantee X-2D order if the kernel hardcodes revocations-first.

So: **single-call + ordered processing inside the core**.

## O57 — Is a feature flag “new kernel physics”?

A feature flag that changes CL-CYCLE-ORDERING is **not new authority semantics**, but it **is kernel physics** in the sense you care about (ordering of admissibility).

So treat it like this:

* Acceptable **only if** the flag is **scoped to the X-2D profiling harness**, is **off by default**, and is **fully deterministic** and **logged** as part of the replay regime identity for the session.
* Unacceptable if it becomes a runtime degree of freedom that can vary between runs without being cryptographically pinned.

In other words: it’s allowed as a **compile-time / run-mode constant** for X-2D, not as a mutable option.

Practical binding: implement an explicit mode:

```
cycle_ordering_mode = "X2D_TOPOLOGICAL"
```

and include it in:

* `X2DSessionStart` (harness metadata)
* the replay regime identity hash inputs (or at minimum the admission log prelude)

## O58 — Two-pass with “discard REFUSE” is not clean

Correct: discarding a kernel decision is a sovereignty violation in your framework because it makes the harness a meta-authority that can ignore kernel outputs.

So **no** two-pass with discarded outputs.

---

# P — Revalidation Mechanics

## P59 — Where does `revalidate_treaty_set(...)` live?

It affects authorization, so it must live in the **kernel layer**, not the harness.

Harness orchestrates *when* to call it (cycle step), but the function belongs with treaty resolution logic, e.g.:

* `kernel/src/rsax2/treaty_resolver.py` or `treaty_active_set.py`

**Rule:** anything that changes what authorizations exist belongs in kernel; anything that schedules workloads belongs in harness.

## P60 — `invalidated_grant_ids` vs reuse `revoked_grant_ids`

Add a parallel structure:

* `invalidated_grant_ids: set[str]`
* and optionally `invalidation_reason: dict[grant_id → reason_code]`
* plus `invalidated_at_cycle: dict[grant_id → cycle]`

Do **not** overload revocation; revocation is an authority act. Invalidation is constitutional dominance. Conflating them destroys audit semantics.

## P61 — Separate method vs inline logic?

Implement as a separate kernel method on `ActiveTreatySet` (or equivalent):

* `apply_constitutional_revalidation(constitution_state, cycle_id) -> RevalidationReport`

Inside it, call a helper for the density-tightening case:

* `apply_density_tightening_invalidation(strategy="newest_first")`

This keeps one locus of truth for “treaty set mutates due to constitution.”

## P62 — Revalidation timing relative to new grants

Revalidation must occur **before** grant admission to prevent admitting “soon-to-be-illegal” grants.

So the cycle order is:

1. Amendment adoption
2. **Revalidate active treaty set against new constitution**
3. Treaty grants
4. Treaty revocations
5. Density enforcement
6. RSA actions
7. Delegated actions

This is the clean hierarchy model:

* constitution changes
* existing downstream policy is reconciled
* new downstream policy is admitted
* then actions run

If you do revalidation after grants, you create useless admit→invalidate churn that can hide bugs and contaminates metrics.

So: **move revalidation earlier**.

(Yes: this is a revision to what I previously suggested; Opus exposed the dependency hazard. This is the correct ordering.)

---

# Q — Density Enforcement Details

## Q63 — “Pruning forbidden” vs “invalidate on bound tightening”

Distinction is exactly as you said:

* **Admission-time pruning** is forbidden. A grant that would breach the bound is rejected. No repair.
* **Constitutional bound tightening** can force invalidation of existing treaties to restore compliance. That is not “pruning as maintenance”; it is **supremacy enforcement**.

So reconcile by naming:

* `reject_on_density_breach` (admission)
* `invalidate_on_density_tightening` (revalidation)

Both deterministic. Different causes. Different logs.

## Q64 — What if aggregate Step 5 density check fails?

It must never fail if admission gates are correct, *except* for the A-drop paradox (A decreases and density increases).

Binding rule for X-2D:

* If post-mutation density check finds `density >= bound`, the kernel must **invalidate treaties newest-first** (deterministic) until density < bound, and log the invalidations as constitutional-density compliance actions.

Do not declare session failure immediately; fail-closed by invalidation.
Session fails only if even after invalidations you cannot restore density below bound (which implies a deeper bug or impossible configuration).

## Q65 — Does an invalidated grantee still count in A?

No. A counts **active authorities contributing to the effective resolution set**.

So:

* if an authority has **zero active, non-invalidated grants** and no constitutional authority, it does not count in A.
* invalidated treaties are excluded from M and from “authority present” counting if they were the authority’s only basis for inclusion.

Yes, this can increase density by lowering A faster than M. That’s exactly why Step 5 must be followed by deterministic invalidation until compliance.

---

# R — State Hash Chain & Protocol Identity

## R66 — “Same protocol” if new record types appear?

Yes. Protocol identity does not mean “same outputs,” it means “same hash function and sequencing rules.”

You can add new artifact/admission records and still be under the same replay protocol as long as:

* they are hashed using the same component update rules
* they are ordered deterministically
* replay reconstructs them identically

So: acceptable.

## R67 — What do revalidation records look like?

Do **not** overload `TreatyAdmissionEvent`. Revalidation is not admission.

Introduce a new admission-log record type (schema-stable) such as:

* `TreatyRevalidationEvent`

Fields (deterministic):

* `cycle_id`
* `state_hash_start`
* `constitution_hash_tip`
* `grant_id`
* `result`: {`VALID`, `INVALIDATED`}
* `reason_code` (e.g., `ACTION_BANNED`, `DENSITY_TIGHTENED`, `SCOPE_RULE_TIGHTENED`)
* `invalidated_at_cycle` (if applicable)

This record lives in the **admission component** hash stream.

## R68 — Must X-0E replay command replay X-2D?

No. Don’t force that. X-0E CLI tooling being “notify-era” is an implementation artifact. The contract is:

* the replay **protocol** is stable
* the **runner** may be specialized

So: X-2D uses its own replay harness, but the underlying hash chain rules remain identical. If later you want unification, fine—but don’t block X-2D on that.

---

# S — Generator Feasibility & D-EDGE

## S69 — Must generator simulate exact density?

Yes. Use the real `_compute_effective_density()` in a simulation loop during plan construction.

Approximation is unacceptable because D-EDGE is literally “ride the bound,” and off-by-one errors are what you’re hunting.

## S70 — Fail-fast vs mid-session infeasibility?

Fail fast. Precompute and validate the entire N-cycle plan before execution begins.

If infeasibility is discovered mid-session, that means your generator is not actually deterministic-with-foreknowledge, and you’ve introduced hidden adaptive behavior. That contaminates the stage.

Partial session outputs are not acceptable for closure runs. They’re acceptable only as development artifacts.

## S71 — Record δ and the explicit band?

Record both.

* δ is the primitive parameter.
* explicit band is derived but makes audits easier and avoids “interpretation.”

So include:

* `density_proximity_delta`
* `target_density_band_low`
* `target_density_band_high`

---

# T — Test Design & Deadlock

## T72 — “Pathological constitution” with frozen v0.3?

Do not create a new constitution YAML. That violates the freeze.

Force deadlock using **v0.3 + a preregistered amendment sequence** that tightens constraints into a mutually incompatible state *for the candidate generator you use*. Then verify Type III classification and failure attribution.

This keeps the constitution line intact while still producing the pathological regime.

## T73 — Expected test suite scale?

Tens, not fifties+.

X-2D is mostly orchestration + instrumentation around already-tested X-1/X-2 machinery. Target:

* ~25–40 tests total
* include 10–15 harness/order/revalidation/density tests
* include 10–15 determinism/gate-instability/replay tests

## T74 — Dedicated “same invalid twice in-run” test?

Yes. Do it.

Run-vs-replay detects nondeterminism across replay, but you also want to detect nondeterminism across identical-state encounters within the same run (e.g., due to mutable caches). So add:

* submit identical invalid request twice under identical `state_hash_start`
* assert identical `(gate_id, reason_code, derived_rejection_class)`

---

# U — Logging & Schema

## U75 — Where do “extension fields” go if logs can’t change?

Yes: `x2d_metrics.jsonl` (and/or `x2d_admission_enrichment.jsonl`) becomes the enrichment layer keyed by:

* `cycle_id`
* `artifact_id` / `grant_id`

Do not mutate the existing treaty/action trace schema.

## U76 — Per-session log dir vs shared logs/?

Per-session directory.

Determinism and hygiene are better when each session has its own immutable log bundle. Use:

```
logs/x2d/<session_id>/
  x2d_sessions.jsonl
  x2d_metrics.jsonl
  x2d_window_metrics.jsonl
  ...
```

and also write a top-level index if you want.

## U77 — Record active bound every cycle or only when changes?

Every cycle.

The redundancy is cheap; the audit benefit is huge; and it avoids “carry-forward ambiguity” bugs.

---

## The key binding changes vs earlier answers

1. **No two-pass calls.** Single call per cycle; order enforced as an X-2D run-mode.
2. **Revalidation moves earlier**: immediately after amendment adoption, before new grants.
3. **Density failures are repaired deterministically** via constitutional invalidation newest-first, not by pruning at admission, and not by failing the session immediately.

If you implement those three, the remaining questions become straightforward engineering.

Good. These are the last places ambiguity can leak into “mode magic,” non-termination, or fake feasibility.

Binding answers:

---

# V — `cycle_ordering_mode` Injection

## V78 — How does the mode enter the kernel?

Sanction **(a)**: add an explicit parameter.

Make it a required field of the cycle call, with a default for non-X2D harnesses:

* `run_cycle(..., cycle_ordering_mode="DEFAULT")`

Why this and not (b) or (c):

* (b) smuggles semantics into state and invites accidental persistence across replays.
* (c) is a contamination hazard and makes “mode” implicitly global.

API change is acceptable; it is not new authority semantics. It is an explicit binding of execution ordering, which is exactly what you want pinned.

Also: the harness must log `cycle_ordering_mode` in the session start record, and replay must assert it matches.

## V79 — Can amendment adoption + revalidation live outside the single kernel call?

No. Not if you mean “kernel is the sole authority on what is authorized.”

If the harness performs amendment adoption and treaty invalidation externally, the harness becomes a meta-authority deciding what the kernel will see. That violates your own architecture.

So: **`policy_core_x2` must internalize**:

1. amendment adoption (if any scheduled/admitted this cycle)
2. treaty revalidation pass (amendment-driven)
3. then proceed with grants → revocations → density enforcement → actions

The harness supplies the amendment candidates as part of the cycle input, but the kernel executes adoption + revalidation deterministically inside the cycle.

This preserves “single call” and keeps authority physics inside kernel.

---

# W — Density Invalidation Convergence

## W80 — Two invalidation passes per cycle?

Yes. Two distinct deterministic passes, logged separately:

1. **Post-amendment revalidation pass**
   Reasons: `ACTION_BANNED`, `SCOPE_RULE_TIGHTENED`, etc.

2. **Post-mutation density-repair pass** (after grants/revokes/expiry and after computing density)
   Reason: `DENSITY_REPAIR`

They can be implemented as one function invoked twice with different predicates and reason namespaces. But they must produce distinguishable events.

## W81 — Termination / non-convergence risk when invalidation increases density

You terminate because the loop is over a finite set and you monotonically remove treaties from the authorizing set.

But you’re right to worry about A dropping faster than M. So bind the semantics:

* If there exists **any constitutional authority** (the RSA), then **A ≥ 1** always.
* When all treaty-based authorities are removed, M for treaty-based pairs becomes 0, so density becomes `M/(A×B) = 0`.

That guarantees convergence.

Implementation requirement: define the “no treaties remain” case explicitly:

* A = count of authorities present in effective resolution set **including the RSA**
* If treaty set empty: M=0 (for treaty-derived authorizations); density = 0.

So yes: the “session fails” branch is reachable only on implementation bugs (e.g., division-by-zero, incorrect A counting, or not actually removing invalidated treaties from M). Treat it as a sanity-fail.

## W82 — Emit revalidation events for every treaty or only invalidations?

Emit **only for status changes** (i.e., newly invalidated) plus a single per-cycle summary record.

You want auditability without O(n) log blowup.

So log:

* `TreatyRevalidationSummaryEvent` per cycle (deterministic):

  * `cycle_id`
  * `active_treaty_count_pre`
  * `checked_count`
  * `invalidated_count`
  * `constitution_hash_tip`
  * `pass_type` (`POST_AMENDMENT` or `DENSITY_REPAIR`)
* `TreatyRevalidationEvent` only for each treaty that transitions to INVALIDATED.

Replay verifies `checked_count == active_treaty_count_pre` deterministically. That proves completeness without per-item VALID spam.

---

# X — Generator Simulation for D-RATCHET

## X83 — Must generator simulate revalidation + density repair?

Yes. Full simulation.

If you don’t simulate revalidation cascades, your “feasibility-checked plan” is fake, because amendment will invalidate grants, change A/M, and trigger density repair.

So the plan builder must run the same deterministic kernel functions in “dry-run mode”:

* apply amendment schedule
* run revalidation pass
* admit grants/revokes (dry-run)
* apply expiry
* apply density-repair invalidation

Then compute density and band adherence.

This is exactly why precomputing the plan is expensive. D-RATCHET is meant to be expensive.

---

# Y — Logging Architecture

## Y84 — Where does `x2d_sessions.jsonl` live?

Each session directory contains its own session file:

```
logs/x2d/<session_id>/
  x2d_session.jsonl   # start + end records for that session only
  x2d_metrics.jsonl
  x2d_window_metrics.jsonl
  ...
```

Optionally also keep a cross-session index:

```
logs/x2d/index_sessions.jsonl
```

…but the authoritative bundle is the per-session directory. This keeps session artifacts self-contained and portable.

---

# Z — Authority Counting & Invariants

## Z85 — Does RSA always count in A? Is A ≥ 1 guaranteed?

Yes.

Binding definition for A in density:

* A = number of distinct authorities that can appear in the effective resolution set **including the sovereign RSA authority**, even if no treaties exist.

Therefore A ≥ 1 always.

This invariant is part of the termination proof in W81 and must be encoded into the density computation to prevent 0/0.

It is not “exploitable” because the bound is enforced at authorization structure level; keeping A ≥ 1 prevents undefined math and guarantees convergence.

---

## Net changes you should lock in

1. `cycle_ordering_mode` is an explicit `run_cycle()` parameter, logged and replay-asserted.
2. Amendment adoption + treaty revalidation are **inside `policy_core_x2`**, not harness.
3. Two revalidation passes per cycle are allowed and separately logged (post-amendment; density-repair).
4. Generator dry-runs the same cascade logic to guarantee D-RATCHET feasibility.
5. A includes RSA; density defined as 0 when M=0; no 0/0.

That resolves Q78–Q85 cleanly and makes the implementation mechanically checkable.

Binding answers, and I’ll tighten the conceptual line so this doesn’t metastasize into “we changed physics by moving code.”

---

# AA — Kernel Scope Expansion

## AA86 — Composition vs inlining of X-1 amendment engine inside `policy_core_x2`

**Composition.**
`policy_core_x2.run_cycle()` calls the existing X-1 amendment engine as a dependency. Do not duplicate or inline amendment adoption logic.

Concrete requirement:

* `run_cycle()` accepts `amendment_candidates` (possibly empty).
* It invokes `x1_amendment_engine.adopt_if_admissible(...)` (or your equivalent) on those candidates.
* It receives back:

  * updated constitution state (hash tip)
  * amendment adoption events (admit/reject, reason codes)
* Then it runs treaty revalidation against the updated constitution state.
* Then proceeds with grants → revocations → density enforcement → actions.

This preserves module boundaries and prevents divergence.

## AA87 — Is this “new physics”? Bright line test.

Position: this is **organizational relocation and explicitization**, not new physics, because you are not adding new authority primitives or widening admissibility—only making the already-licensed hierarchy semantics *enforceable under replay and topological time*.

Bright line:

**New kernel physics = any change that expands or changes the set of lawful executions reachable under the same constitution + same admitted artifacts.**

Examples that *would* be new physics:

* introducing pruning as a runtime repair mechanism (changes reachable authorization sets)
* adding partial treaty mutation on amendment (changes treaty semantics)
* allowing grant chains or new delegation depth (expands reachable graphs)
* adding heuristic rejection/timeouts (changes acceptance function)
* changing what an ExecutionWarrant can authorize

What you are doing here:

* moving amendment adoption into the single-cycle kernel call
* adding deterministic revalidation (which is required by supremacy)
* pinning ordering as an explicit mode

These **restrict** or **make explicit** behavior; they do not create new reachable authority.

So: not new physics by the above test.

## AA88 — Defaults vs explicit args for new parameters

Use **defaults** to preserve backward compatibility **and** require explicit pinning in X-2D.

So:

* `amendment_candidates: list = []`
* `cycle_ordering_mode: str = "DEFAULT"`

Existing callers can keep working unchanged.

But the X-2D harness must pass them explicitly and log them in `X2DSessionStart`, and replay must assert they match.

This gives you both:

* compatibility
* explicitness where it matters

---

# AB — M and Constitutional Authority in Density

## AB89 — Do sovereign (RSA, action) pairs contribute to M?

**No.** Density is defined over the **delegation-induced effective resolution set**, not the sovereign baseline.

Reason: the purpose of density is to prevent **authority inflation via delegation**, not to penalize the existence of the base sovereign agent.

Binding definition for X-2D (and X-2 if you want consistency):

* `M = count of distinct (delegated_authority, action)` pairs admitted via active treaties, after revalidation/expiry/revocation/invalidations.
* The RSA’s constitutional authority is excluded from M.
* `A` counts active delegated authorities (grantees with ≥1 active, non-invalidated grant). RSA is excluded from A for density computation.

That yields:

* with no active treaties: A=0, M=0 → density defined as 0 (by convention; no division)
* termination and repair logic remains clean

If you include the RSA in A but exclude RSA pairs from M, you get awkward “density = 0/(1×B)” which is fine but unnecessary. The cleanest is: density is a delegation-only metric with a defined zero case.

So update the earlier “RSA always counts in A” statement: that was a convergence crutch. You don’t need it if you define the zero-treaty case directly.

**Invariant:** if A=0 then density=0.

This is the correct mathematical definition.

---

# AC — Generator Access to Kernel

## AC90 — Generator calling kernel internals vs stable simulation API

Use a **simulation API**.

The generator must not import private kernel internals ad hoc. That creates fragile coupling and silent divergence risk.

Create a stable interface, e.g.:

* `kernel/sim/simulate_cycle(...)`
* `kernel/sim/simulate_plan(...)`

which wraps:

* amendment adoption
* revalidation
* treaty admission
* density enforcement/repair
* expiry
* (optionally) action admission without side effects

It returns:

* next simulated state hash
* simulated active treaty set summary
* density metrics
* invalidation events

The harness uses the same API for dry-run planning validation. This pins generator semantics to kernel semantics without leaking internals.

So: dependency is acceptable, but **through a narrow stable surface**.

---

# AD — Revalidation Event Schema

## AD91 — Keep `result` field or drop it?

Keep it.

Even if X-2D only emits INVALIDATED per-item events, keeping `result` avoids schema churn and preserves forward compatibility for later phases that may log VALID.

But bind it:

* For `TreatyRevalidationEvent` emitted in X-2D, `result` MUST be `"INVALIDATED"`.

And keep the summary event as the completeness proof.

---

# AE — Naming consistency

## AE92 — `x2d_sessions.jsonl` vs `x2d_session.jsonl`

Adopt:

* Per-session: `logs/x2d/<session_id>/x2d_session.jsonl` (singular; contains start+end for that session)
* Cross-session index (optional): `logs/x2d/index_sessions.jsonl` (plural index concept)

That resolves the ambiguity cleanly and matches the per-session bundle model.

---

## Summary of the hard bindings introduced here

1. Amendment adoption is composed inside `run_cycle()` via the X-1 engine; no inlining.
2. “New physics” = expanded reachable lawful executions under same constitution+artifacts. These changes don’t.
3. New `run_cycle` params have defaults; X-2D must pass explicitly and replay-assert.
4. Density metric is **delegation-only**; with A=0 define density=0 (no RSA-in-A hack).
5. Generator uses a stable kernel simulation API, not raw internals.
6. Keep `result` field; per-item events are INVALIDATED in X-2D.
7. Naming: `x2d_session.jsonl` per session + optional `index_sessions.jsonl`.

If you want, the next step is to redline the X-2D spec and the X-2D implementation instructions to incorporate (4) and the revised ordering (revalidation immediately after amendment adoption).
Binding answers.

---

# AF — Density Definition Retraction & Repair Loop

## AF93 — Do we allow intermediate density spikes during the repair loop?

Yes. Make it explicit.

**Contract for density-repair loop:**

* The loop is a **repair procedure**, not a steady-state invariant.
* Intermediate states inside the loop may violate `density < bound`.
* Correctness condition is:

> After the loop terminates, either
> (a) `density < density_upper_bound`, or
> (b) `A = 0` (no active delegated authorities) and density is defined as `0`.

Additionally:

* Actions must never be evaluated while the system is in an intermediate over-bound repair state.

So the ordering is:

1. mutations (grant/revoke/expiry/revalidation)
2. density check
3. if over-bound: run repair loop to convergence
4. **only then** evaluate actions

That is the safety boundary.

## AF94 — How to guard 0/0 in `_compute_effective_density()`? Bug fix vs X-2D-only?

Guard it in the kernel, unconditionally. This is a correctness fix, not an X-2D quirk.

**Density is a function over a state. States with no active delegated authorities are valid.** The function must be total.

So implement:

* if `A == 0`: return `(0, B, 0, 0.0)` (and ensure B is still well-defined as the closed action set size)

This should not be gated by `cycle_ordering_mode`. If other phases ever compute density, they benefit from not crashing or producing NaNs.

Treat this as a kernel bug fix that preserves intended semantics.

---

# AG — Simulation API Mechanics

## AG95 — Where does the sim package live?

Put it under `kernel/src/rsax2/sim/`.

Reason: the simulation API must be version-aligned with the kernel internals. Keeping it in-package ensures:

* stable import path tied to the rsax2 version
* no confusion about cross-kernel compatibility
* easier enforcement that sim uses the same data models

So:

* `kernel/src/rsax2/sim/simulate_cycle.py`
* `kernel/src/rsax2/sim/simulate_plan.py`

## AG96 — Deep-copy mutable state vs pure immutable computation?

Deep-copy, deterministically.

You already have an in-place mutating `InternalStateX2`. Refactoring to immutability is a phase-level rewrite, not a harness requirement.

Binding implementation:

* `simulate_cycle(state: InternalStateX2, ...) -> (next_state: InternalStateX2, outputs: SimOutputs)`
* Inside, perform `state_copy = state.deep_copy_deterministic()` and run the same kernel transition logic on the copy.
* Never touch host clock, randomness, IO, network, or global caches.
* Ensure deep-copy is canonical (ordering stable, no object-identity artifacts).

This gives you “no side effects” while reusing proven transition code.

If later you want a purely functional core, that’s a separate refactor stage.

---

## Net binding updates implied

1. Add explicit language to X-2D spec/instructions: density repair loop may traverse over-bound intermediate states; only post-repair state is constrained.
2. Make `_compute_effective_density()` total with an `A==0 → density=0` guard as a global kernel fix.
3. Implement simulation as `rsax2.sim`, using deterministic deep-copies of `InternalStateX2`.

If you want, I can now reprint the X-2D spec and the X-2D implementation instructions with these bindings integrated while keeping the same version identifiers.
