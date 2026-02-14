# X-2D Implementation Questions

## A — Architectural Scope & Kernel Boundary

**Q1.** The spec says "X-2D introduces no new authority semantics and no new kernel physics." The instructions add `X2DSessionStart` and `X2DSessionEnd` as new artifact types (§3) and Gates 6/7/8D (§6). Are these new types admitted through the existing X-2 `policy_core_x2` pipeline (extending step 1), or do they live entirely in the harness layer outside the kernel? If kernel-external, what does "admitted" mean — just schema validation in the harness before logging?

**Q2.** Instructions §6 defines Gates 6, 7, and 8D for session admission. These gate numbers collide with the existing kernel admission gates (Gate 6T/7T/8C in X-2 treaty admission). Should X-2D session gates use a distinct namespace (e.g., Gate 6D/7D/8D) to avoid confusion? Or are they literally extensions of the kernel admission pipeline?

**Q3.** The existing `policy_core_x2` has a 5-step per-cycle ordering (CL-CYCLE-ORDERING). X-2D spec §6.2 defines its own binding order (amendment → grants → revocations → density → RSA actions → delegated actions). This is nearly identical to CL-CYCLE-ORDERING but splits density recomputation into an explicit step between revocations and actions. In the existing kernel, density is checked inside Gate 8C.7 during grant admission. Does X-2D require moving density enforcement into the per-cycle flow (after all grants/revocations are processed, before action evaluation), or is the Gate 8C.7 per-grant check sufficient?

**Q4.** The existing `ActiveTreatySet.prune_for_density()` does greedy pruning (oldest first) when density exceeds the bound. X-2D spec §3.2 says grants exceeding density must be *rejected*, not pruned. Which semantics apply under X-2D? Is pruning disabled in favor of hard rejection at admission? Or does the harness never generate inputs that would trigger pruning, relying on Gate 8C.7 to reject individually?

**Q5.** Instructions §1 places the X-2D harness under `replay/src/` (x2d_runner.py, x2d_generators.py, etc.). Previous harnesses live under `profiling/` (x0p, x0l, x1, x2). Should X-2D follow the established pattern and go under `profiling/x2d/` instead? Or is the `replay/src/` placement intentional?

## B — Cycle Ordering & Topological Time

**Q6.** Instructions §7.2 binding order lists density recomputation as step 4 ("Post-Grant, Pre-Action"). But what about density enforcement *during* grant admission? The existing kernel checks density per-grant at Gate 8C.7 (each grant evaluated sequentially, density rechecked after each admission). Does X-2D require an additional aggregate density check after *all* grants in the cycle have been admitted, or is the per-grant sequential check sufficient for the "Post-Grant, Pre-Action" requirement?

**Q7.** "Same-cycle revocation must preempt delegated execution" — in the existing CL-CYCLE-ORDERING, revocations (Step 1b) are processed before grants (Step 1c), and both happen before action evaluation (Step 4). So revocations already preempt delegated execution by ordering. Does X-2D require any additional preemption mechanism beyond the existing step ordering, or is this just restating what CL-CYCLE-ORDERING already guarantees?

**Q8.** "Expiry is applied prior to delegated evaluation in the cycle." The existing `ActiveTreatySet.active_grants(current_cycle)` already filters out expired grants. Is X-2D asking for an explicit expiry-sweep step (logging which grants expired), or is the existing implicit filtering sufficient?

**Q9.** Instructions §7.2 lists "Treaty grants" and "Treaty revocations" as separate steps, with grants before revocations. But the existing CL-CYCLE-ORDERING processes revocations (Step 1b) before grants (Step 1c). Which ordering is authoritative for X-2D? The instructions order (grants → revocations → density) or the existing CL-CYCLE-ORDERING (revocations → grants → density)?

## C — Amendment–Treaty Interaction & Supremacy

**Q10.** Instructions §8 says "deterministically revalidate the entire active treaty set against [the updated] constitutional state." What does revalidation mean concretely? Re-running the full treaty admission pipeline (Gates 6T/7T/8C) on each active grant against the new constitution? Or a narrower check (e.g., only verifying granted_actions are still in the closed action set and density_upper_bound hasn't been breached)?

**Q11.** If a treaty is invalidated by amendment revalidation, what happens to it? Is it removed from `ActiveTreatySet`? Revoked with a synthetic `TreatyRevocation`? Marked as non-authorizing but still present? The spec says it "loses authorizing power immediately" but does not specify the mechanism.

**Q12.** The spec's prime directive says "No constitutional tightening effect unless it deterministically revalidates the active treaty set before any action evaluation in the same cycle." In the existing CL-CYCLE-ORDERING, amendment adoption (Step 1a) happens before treaty evaluation. But currently there is no treaty revalidation step after adoption. Does X-2D require adding an explicit revalidation step between Step 1a (adopt) and Step 1b (revocations)?

**Q13.** For D-RATCHET, the amendment schedule "tightens constraints only (ratchet)" and "includes bans on at least one delegated action type exercised by treaties in-session." When an amendment bans an action type that active treaties grant — does the revalidation cascade revoke those treaties entirely, or just strip the banned action from their granted_actions? The latter would require per-action partial invalidation that doesn't exist in the current model.

**Q14.** If an amendment tightens `density_upper_bound` such that the existing active treaty set now exceeds the new bound, what happens? Immediate treaty pruning/invalidation? Or is it only enforced on *new* grants? The ratchet rule says `density_upper_bound` is non-increasing, so this scenario is guaranteed in D-RATCHET.

## D — Density & Proximity

**Q15.** The spec defines `density_proximity_delta` (δ) but never specifies how it's used beyond being a session parameter. Is δ used by the generator to target density within `[density_upper_bound - δ, density_upper_bound)`, or is it a metric threshold for "near-boundary" classification in the report? Or both?

**Q16.** The existing constitution sets `density_upper_bound: 0.75`. The density formula is `M / (A × B)`. With v0.3 having 4 executable action types, reaching density near 0.75 requires substantial grant volume. What are the expected ranges for `grantee_count` and `max_active_grants_per_grantee` to make D-SAT and D-EDGE scenarios feasible? Should the harness generate enough grantees to make near-boundary density achievable?

**Q17.** Spec §3.2 says "Density must remain below bound at all execution points." The density check currently happens only during grant admission (Gate 8C.7). If a revocation occurs that lowers A_eff (by removing a grantee's only grant), density could paradoxically increase even though M_eff decreased. Is the "all execution points" requirement demanding runtime density checks at additional points (e.g., after revocations)?

**Q18.** D-EDGE requires "sustained operation within a preregistered band near `density_upper_bound` under maximal lawful churn." What constitutes the "preregistered band"? Is this `[density_upper_bound - δ, density_upper_bound)`? Should the generator explicitly target and maintain density within this band cycle-over-cycle?

## E — Generators & Determinism

**Q19.** Instructions §10 says generators are "deterministic only." The existing X-2 profiling harness pre-builds all scenarios before execution (`build_lawful_*`, `build_adv_*`). X-2D needs generators that produce treaty events, delegated requests, and amendment schedules over N cycles. Should generators pre-compute the entire N-cycle event stream before execution starts (fully deterministic plan), or generate each cycle's events from seeded state (lazy but deterministic)?

**Q20.** For D-CHURN, what constitutes "high-frequency grant/revoke patterns"? Approximately what percentage of cycles should have grant or revocation events? Is there a target churn rate (churn_W), or should the generator maximize churn within constraint validity?

**Q21.** For invalid delegated requests (§10.2), the instructions specify six invalid classes. Are these the *only* invalid classes, or can the generator introduce additional adversarial patterns (e.g., request for a valid treaty but wrong scope_zone, or request using a treaty that was valid last cycle but expired this cycle)?

**Q22.** The existing X-2 `IdentityPool` generates Ed25519 keypairs. X-2D needs multiple grantees with concurrent grants. Should all grantee identities be generated upfront in the session start and recorded in seeds, or can new identities be introduced mid-session?

**Q23.** Instructions §10.3 says D-RATCHET's amendment schedule must "force revalidation cascades under churn." How many amendment adoption events are expected per D-RATCHET session? One tightening? Multiple progressive tightenings? Is there a target cadence (e.g., every N/K cycles)?

## F — State Hash Chain & Replay

**Q24.** X-2D requires replay under the X-0E regime (`kernel_version_id = "rsa-replay-regime-x0e-v0.1"`). The X-0E state hash chain has 4 components: artifacts, admission, selector, execution. X-2D introduces treaty events, amendment events, and density metrics. Do treaty/amendment/density records go into the existing 4 components (e.g., treaty admission events → admission component, treaty artifacts → artifacts component), or does X-2D extend the hash chain with new components?

**Q25.** The X-0E state hash chain was designed for the v0.1.1 closure constitution (Notify-only, no treaties). X-2D runs under v0.3 with full treaty and amendment machinery. Does using the same `kernel_version_id` and hash chain formula remain correct, or does X-2D's extended per-cycle structure (topological time, treaty revalidation, density enforcement) constitute a new replay protocol requiring a new `kernel_version_id`?

**Q26.** Instructions §13 says "Replay must reconstruct every session deterministically" and "No global caches that bypass reconstruction." The existing `InternalStateX2.active_treaty_set` is forward-reconstructed. Does X-2D replay need to reconstruct the treaty set from scratch each cycle (no carry-over), or is forward reconstruction (applying grants/revocations/expirations incrementally) acceptable as long as it's deterministic?

**Q27.** Instructions §13 says replay must "Apply expiry deterministically by cycle count." The existing `TreatyGrant.is_active(current_cycle)` checks `grant_cycle + duration_cycles > current_cycle`. Is this the complete expiry semantics, or does X-2D introduce explicit expiry events that must be logged and replayed?

## G — Metrics, Logging & Instrumentation

**Q28.** Instructions §14 specifies three log files: `x2d_sessions.jsonl`, `x2d_metrics.jsonl`, `x2d_window_metrics.jsonl`. These are under `logs/`. The X-0E regime uses `host/log_io.py` (append_jsonl with fsync). Should X-2D logs use the same `append_jsonl` mechanism, or are they harness-level files outside the X-0E log regime?

**Q29.** Instructions §14 says to "extend existing treaty/action traces to include amendment adoption events and resulting constitution hash tip, treaty revalidation outcomes post-amendment, supersession failures." Does "extend" mean adding fields to the existing X-2 log schema, or logging additional records alongside the existing ones? If the former, this modifies the log schema version which conflicts with the frozen `x0e-v0.1` schema.

**Q30.** Per-cycle metrics (§14) include `state_hash_start` and `state_hash_end`. The X-0E chain produces one hash per cycle. Is `state_hash_start` the previous cycle's hash (state_hash[n-1]) and `state_hash_end` the current cycle's hash (state_hash[n])? Or does X-2D compute sub-cycle hashes (e.g., after amendment adoption but before action evaluation)?

**Q31.** Window metrics (§14) use window size W. Is W a sliding window (every cycle computes metrics over the preceding W cycles), or non-overlapping windows (metrics computed every W cycles)? The spec uses `window_start_cycle` and `window_end_cycle` which suggests non-overlapping, but "churn_W" is defined more like a sliding window metric.

## H — Session Schema & Admission

**Q32.** Instructions §3.1 says `density_upper_bound` is recorded from "constitution active at cycle 0." But D-RATCHET can tighten `density_upper_bound` via amendment. Does the session record the *initial* bound, or the *minimum* bound across the session? If initial, does the session need to track bound changes over the session?

**Q33.** The `X2DSessionStart` includes `amendment_schedule` which is an array. What is the schema for each element? At minimum: `{cycle: int, amendment_type: string, ...}`. Should it include the full amendment content (replacement YAML hash, deltas), or just scheduling metadata?

**Q34.** Instructions §4 says "Gate 7 must enforce schema validity before any session begins." Is this Gate 7 the same as X-2D Gate 7 (§6), or the kernel's Gate 7T? The context suggests it's the session-level Gate 7, but the numbering overlap creates ambiguity.

**Q35.** Instructions §6 Gate 6 says "X-1 amendment machinery is enabled (even if amendment schedule is empty)." How is "enabled" determined? By checking that the constitution version is ≥ v0.2 and has `AmendmentProcedure` defined? Or by verifying the X-1 kernel extension modules are importable?

## I — Tests & Closure

**Q36.** Instructions §15 lists 7 specific tests. Are these the *complete* test suite, or are additional tests expected? For example, there's no explicit test for revocation monotonicity (closure criterion 9) or for the logging/metrics infrastructure.

**Q37.** Instructions §15.7 says "if forced to happen, verify failure attribution." How should the test force a persistent deadlock? The generator is supposed to "ensure lawful candidates exist" each cycle, so a streak ≥ K means a kernel bug. Should the test use a pathological constitution that makes deadlock inevitable, or inject candidates that appear lawful but trigger constraint interactions?

**Q38.** Closure criterion 9 says "revocation monotonicity (revocation/expiry never increase M or any M_i)." Can this actually be violated by the existing kernel? If grantee X has two grants covering {Notify, ReadLocal} and one is revoked covering only {Notify}, M decreases but M_i for the remaining authority may not change. Under what scenario would M *increase* on revocation? Is this criterion testing for implementation bugs, or is there a mathematical edge case?

**Q39.** Instructions §16 lists "delegation chain or cycle becomes reachable" as a failure condition. The existing Gate 8C.5 (depth) and 8C.6 (acyclicity) should prevent this. Is this criterion testing those gates under churn stress (i.e., could rapid grant/revoke patterns create a window where a chain becomes temporarily reachable), or confirming they hold under load?

## J — Parameters & Preregistration

**Q40.** Spec §10 says "No post-freeze tuning." When are parameters frozen? Before any code is written (now)? Or after code is complete but before the production run (like X-0P/X-0L)? The spec says "preregistration-ready pending parameterization" which suggests parameters are set later.

**Q41.** What are the expected session lengths (N) for each family? X-0P and X-0L used 100 cycles. X-2D seems to need longer runs for churn dynamics to manifest. Should N be in the hundreds? Thousands? Is there a computational budget constraint?

**Q42.** How many sessions per family? X-2 profiling ran one session (26 cycles, 8 phases). Is X-2D expected to run one session per family (5 total), or multiple sessions per family with different seeds?

**Q43.** The `X2DSessionStart` includes `seeds` as "all seeds used: treaty stream, action stream, amendment stream." Should these be integer seeds for seeded RNG (like X-0P's `SEED = 42`), or structured objects? What is the expected seed schema?

## K — Existing Code Interaction

**Q44.** The existing `policy_core_x2` returns a `PolicyOutputX2` which includes `treaty_grants_admitted`, `treaty_grants_rejected`, `treaty_revocations_admitted`, etc. X-2D needs per-cycle density metrics, gate instability data, and Type III classification layered on top. Should the X-2D harness extract these from `PolicyOutputX2` post hoc, or does `PolicyOutputX2` need extension?

**Q45.** The existing `ConstitutionX2.compute_effective_density()` returns `(A_eff, B, M_eff, density)`. X-2D metrics require logging all four values per cycle. Is the existing return signature sufficient, or should it also return `density_upper_bound` for convenience?

**Q46.** Instructions say X-2D runs under `kernel_version_id = "rsa-replay-regime-x0e-v0.1"`. The X-0E CLI (`cli/rsa.py`) was designed for Notify-only under v0.1.1. Should X-2D use the X-0E CLI infrastructure at all, or does it need its own runner that invokes `policy_core_x2` directly (like the existing X-2 profiling harness does)?

**Q47.** The spec lists "TreatyProcedure.effective_density_definition" with a revalidation trigger `DENSITY_BOUND_TIGHTENED`. This exists in the v0.3 constitution YAML. Is there existing kernel code that handles this trigger, or must X-2D implement the revalidation cascade from scratch?

## L — Failure Attribution & Gate Instability

**Q48.** Instructions §11 defines gate instability as any difference in gate/reason_code/rejection_class between run and replay "under identical input and identical state." The existing `TreatyAdmissionEvent` logs gate and reason_code but not a separate "rejection_class." Is `rejection_class` a new field that needs to be added to the event model, or is it derivable from the existing reason_code?

**Q49.** "On replay, compare byte-for-byte." Does this mean comparing the JCS-canonical bytes of each `TreatyAdmissionEvent` / rejection record between run and replay? Or comparing the raw log lines? The distinction matters if log records contain non-deterministic fields (e.g., `created_at` from host clock).

**Q50.** For gate instability detection, the requirement says "identical input and identical state." How is "identical state" verified in practice? By checking `state_hash_at_cycle_start` matches? Or by comparing the full `InternalStateX2.to_dict()` canonical form?

## M — Edge Cases & D-EDGE Specifics

**Q51.** D-EDGE requires "sustained operation within a preregistered band near `density_upper_bound` under maximal lawful churn." "Maximal lawful churn" means what exactly? Maximum number of grant/revoke events per cycle that the kernel can process without constraint violation? Or the highest churn_W achievable while maintaining density in the target band?

**Q52.** What if the generator cannot maintain density in the target band because grants that would raise density are rejected by Gate 8C.7? Is this a generator design failure (tests aborted), an expected regime (success with lower-than-target density), or does the generator need to be smart enough to compute feasible grant configurations before submitting them?

**Q53.** Instructions §6 Gate 8D says "D-EDGE includes an explicit near-boundary targeting band or regime parameters (if encoded in `notes` or a structured field)." This suggests the targeting band might go in `notes` as free text rather than a structured field. Should we define a structured field for this instead?

## N — Report & Deliverables

**Q54.** Spec §11 deliverables include "structured JSON metrics report" and "per-family summary table." Is the report format expected to follow the existing X-0P/X-0L/X-1/X-2 pattern (single JSON file), or is the per-family table a separate markdown artifact?

**Q55.** Should the implementation report (docs/implementation-report.md) be updated with §21 (X-2D Architecture) and §22 (X-2D Closure Results) sections following the established pattern?

---

## O — Follow-ups: Cycle Ordering & Harness Bucketing (from A3, B9)

**Q56.** A3 says keep Gate 8C.7 AND add a Cycle Step 4 aggregate density assertion. B9 says the harness must feed inputs into `policy_core_x2` in buckets matching X-2D order (grants before revocations), potentially via two admission passes per cycle. Currently `policy_core_x2` is called *once* per cycle with all candidates. To implement two-pass bucketing without kernel changes, should the harness call `policy_core_x2` twice per cycle (once with grants-only, once with revocations + actions), or should it call `policy_core_x2` once with inputs pre-sorted into a single candidate list where grants precede revocations? The existing Step 1b/1c ordering inside `policy_core_x2` would need to be respected either way.

**Q57.** B9 says the alternative is a feature flag to adjust CL-CYCLE-ORDERING for X-2D runs. Given the prime directive "no new kernel physics," is a feature flag that reorders Step 1b and 1c inside `policy_core_x2` acceptable? Or does reordering internal kernel steps constitute changing kernel physics, making the two-pass harness approach the only valid option?

**Q58.** If we use two-pass bucketing (grants pass, then revocations+actions pass), the first pass (grants-only) would go through `policy_core_x2` with no action candidates, meaning it would always produce REFUSE (no admissible actions). The harness would then discard the REFUSE decision and run a second pass with revocations + actions using the updated `InternalStateX2` from pass 1. Is this semantically clean, or does discarding a kernel decision violate sovereignty?

## P — Follow-ups: Revalidation Mechanics (from C10–C14)

**Q59.** C10 says revalidation is a "narrow authorization-validity check" (not full re-admission). C12 places revalidation after grants and revocations but before density enforcement. C13 says invalidation is full (treaty becomes non-authorizing if any granted action is now prohibited). This implies a specific function signature like `revalidate_treaty_set(active_set, constitution) → (valid_set, invalidated_list)`. Should this function live in the kernel layer (e.g., `kernel/src/rsax2/treaty_admission.py`) since it affects authorization, or in the harness since it's orchestration?

**Q60.** C11 says mark invalidated treaties with `invalidated_by_constitution_at_cycle = c`. The existing `ActiveTreatySet` tracks invalidity via `revoked_grant_ids` (a set of IDs). Invalidation is semantically different from revocation. Should we add a parallel `invalidated_grant_ids` set to `ActiveTreatySet`, or reuse the `revoked_grant_ids` mechanism (treating invalidation as a form of revocation)? The former is cleaner for audit; the latter avoids modifying the data structure.

**Q61.** C14 says invalidate treaties newest-first when density_upper_bound tightens. This is similar to `prune_for_density()` but with "newest first" instead of "oldest first," and motivated by constitutional supremacy rather than maintenance. Should we implement this as a separate method (e.g., `invalidate_for_density_tightening()`) on `ActiveTreatySet`, or keep the logic entirely in the revalidation function from Q59?

**Q62.** C12's cycle ordering places revalidation after grants/revocations but before density enforcement. But what if a newly admitted grant in this cycle depends on the authorization of an existing treaty that the amendment just invalidated? Example: grantee X has grant G1 (from prior cycle) covering Notify; amendment bans Notify; new grant G2 in this cycle also covers Notify for grantee Y. Should G2 be admitted (it was processed before revalidation) and then immediately invalidated by revalidation? Or should revalidation happen *before* new grant admission to prevent admitting soon-to-be-invalid grants?

## Q — Follow-ups: Density Enforcement Details (from D15–D18, A4)

**Q63.** A4 says pruning is forbidden and replaced with hard rejection. But C14 says invalidate treaties newest-first when density tightens. Isn't invalidation-by-density-tightening a form of pruning? How do we reconcile "pruning is forbidden" with "invalidate treaties deterministically until density < bound"? Is the distinction that A4 applies to *grant admission* (reject the grant) while C14 applies to *constitutional changes* (invalidate existing treaties)?

**Q64.** D17 confirms density must be checked after all mutations (grants/revokes/revalidation/expiry) as a single "Step 4" computation. If this step finds density ≥ bound (e.g., because A decreased after a revocation), what action is taken? The grants were already admitted. Do we retroactively invalidate the most-recently-admitted grants from this cycle? Or is this an irrecoverable session failure?

**Q65.** The density formula `M / (A × B)` counts distinct (authority, action) pairs. When a treaty is *invalidated* (non-authorizing), do we still count that grantee as an "authority" in A if they have other non-invalidated grants? Or does invalidation remove them from the resolution set entirely, potentially *increasing* density for remaining authorities?

## R — Follow-ups: State Hash Chain & Protocol Identity (from F24–F25)

**Q66.** F24 says treaty/amendment artifacts fold into the existing "artifacts" hash chain component, and admission events fold into the "admission" component. F25 says keep the same `kernel_version_id` if topology is implemented in harness input batching. But the X-0E hash chain was defined for 4 components (artifacts, admission, selector, execution) with records in append order. If X-2D introduces new record types (treaty admission events, revalidation events, density assertions) that get folded into these components, the hash chain output changes even for identical kernel behavior. Is that acceptable, or does it break the "same protocol" claim?

**Q67.** F25's binding decision says "implement topology and revalidation as deterministically logged admission events so the protocol stays the same." This means revalidation outcomes must appear as records in the admission log. What should these records look like? Should they use the existing `TreatyAdmissionEvent` schema (with a new gate like `"REVALIDATION"`), or a new record type?

**Q68.** If we keep the same `kernel_version_id`, the X-0E replay harness (`cli/commands/replay.py`) should theoretically be able to replay X-2D logs. But it was designed for Notify-only under v0.1.1. Should X-2D runs be replayable by the X-0E replay command (proving protocol compatibility), or only by the X-2D-specific replay harness?

## S — Follow-ups: Generator Feasibility & D-EDGE (from M51–M53, E19)

**Q69.** E19 says precompute the entire N-cycle plan and hash it at session start. For D-EDGE, the generator must maintain density within `[upper_bound − δ, upper_bound)` while maximizing churn. This requires the generator to simulate density computation for each planned cycle to verify feasibility before execution. Should the generator embed a density simulator that runs `_compute_effective_density()` during plan construction, or is an approximation acceptable?

**Q70.** M52 says if the generator can't maintain the band, the session is invalid. But how do we determine this? Does the generator fail fast during plan construction (before any cycles run), or could it discover infeasibility mid-session? If the latter, is a partial session result (with documented failure point) acceptable, or must the entire plan be validated upfront?

**Q71.** M53 says add structured fields `target_density_band_low` and `target_density_band_high` to `X2DSessionStart`. These are derived from `density_upper_bound` and `density_proximity_delta` (band = `[upper_bound - δ, upper_bound)`). Should both δ AND the explicit band be recorded (redundant but auditable), or just one?

## T — Follow-ups: Test Design & Deadlock (from I36–I39)

**Q72.** I37 says use a "pathological constitution" to force deadlock. The existing v0.3 constitution is frozen. Does I37 mean creating a *new* test-only constitution YAML that is structurally valid but creates mutual constraint incompatibility? Or using v0.3 with a specific treaty/amendment configuration that makes all lawful candidates fail admission?

**Q73.** I36 says add tests for revocation monotonicity, log schema integrity, and per-family session runner sanity. That brings the minimum test suite to ~10 explicit tests. For the existing phases, test counts were: X-0P=59, X-0L=99, X-1=19, X-2=35, X-0E=51. What scale of test suite is expected for X-2D? Tens (like X-1/X-2 harness tests) or fifties+ (like X-0P)?

**Q74.** The spec says "any gate instability under identical input + identical state" is a failure condition. Should there be a dedicated test that deliberately submits the same invalid request twice in a run (not just run vs. replay) and verifies identical gate/reason_code? Or is run-vs-replay comparison sufficient?

## U — Follow-ups: Logging & Schema (from G28–G31)

**Q75.** G29 says add adjacent records in new X-2D logs, don't mutate existing frozen log schema. But the instructions §14 say to "extend existing treaty/action traces to include amendment adoption events and resulting constitution hash tip." If we can't modify existing logs, should these extension fields go into `x2d_metrics.jsonl` keyed by `cycle_id`, effectively making `x2d_metrics.jsonl` the enrichment layer over existing traces?

**Q76.** G28 says use X-0E's `append_jsonl` with fsync. The X-0E log files are under the `--log-dir` passed to `rsa run`. X-2D logs are under `logs/` per instructions §1. Should X-2D logs use a per-session log directory (like X-0E), or a shared `logs/` directory with session_id as a key in each record?

**Q77.** H32 says record `density_upper_bound_initial`, `density_upper_bound_min_observed`, and per-cycle `density_upper_bound_active`. The per-cycle active bound changes only on amendment adoption. Should every cycle's metric record include the (unchanged) active bound for completeness, or only record it on the cycles where it changes?

---

## V — Follow-ups: `cycle_ordering_mode` Injection (from O56–O58)

**Q78.** O57 says `cycle_ordering_mode = "X2D_TOPOLOGICAL"` is a "compile-time/run-mode constant." The existing `policy_core_x2.run_cycle()` is kernel code shared across all phases. How does the mode constant enter the kernel call? Options: (a) parameter to `run_cycle()`, (b) field on `InternalStateX2`, (c) module-level constant toggled by the harness before import. Option (a) is cleanest but changes the kernel API; (c) risks cross-contamination if modules are reloaded. Which is sanctioned?

**Q79.** Currently amendment adoption lives in the X-1 amendment engine, invoked by the harness before or during `policy_core_x2`. Under X2D_TOPOLOGICAL, revalidation must happen after amendment adoption but before grant admission (P62). If the harness handles amendment adoption → revalidation → then calls `policy_core_x2` (which only does grants → revocations → density → actions), the revalidation is architecturally *outside* the single kernel call. Is that acceptable? Or must `policy_core_x2` internalize amendment adoption + revalidation as a new initial step, making the "single call" truly self-contained?

## W — Follow-ups: Density Invalidation Convergence (from Q64–Q65)

**Q80.** P62 places revalidation (amendment-driven) before grants. Q64 places density-repair invalidation (mutation-driven) after all mutations as Step 5. These are two separate invalidation events in a single cycle: (1) revalidation after amendment adoption, using reason codes like `ACTION_BANNED` / `SCOPE_RULE_TIGHTENED`, and (2) density repair after grants/revocations/expiry, using reason code `DENSITY_TIGHTENED`. Both produce `TreatyRevalidationEvent` records. Is this the correct reading — two distinct invalidation passes per cycle, each deterministic, each logged separately?

**Q81.** Q65 says invalidating a treaty can *increase* density (A drops faster than M when the invalidated authority's only basis for inclusion is removed). The Step 5 density-repair loop ("invalidate newest-first until density < bound") could therefore be non-convergent: each invalidation may raise density by lowering A. What guarantees termination? When all treaties are invalidated, density becomes 0/0 (undefined) or 0. Is the termination proof simply that the loop must end when no treaties remain? If so, the "session fails" clause in Q64 is unreachable except on implementation bugs — confirm?

**Q82.** R67 specifies `TreatyRevalidationEvent` with `result: {VALID, INVALIDATED}`. During revalidation, should the step emit events for *every* active treaty (both VALID and INVALIDATED results), or only for treaties whose status changes to INVALIDATED? Full logging ensures completeness-verifiable replay (auditor can confirm every treaty was checked) but scales with active treaty count per amendment cycle.

## X — Follow-ups: Generator Revalidation Simulation (from S69–S70, P62)

**Q83.** S69 says the generator must use real `_compute_effective_density()` during plan construction. For D-RATCHET sessions, the plan includes amendments that trigger revalidation cascades (P62), which can invalidate treaties, which changes density (Q65). Must the generator also simulate the full revalidation + density-repair logic during plan construction to ensure the plan is feasible post-cascade? Or can it assume the planned treaty set survives revalidation and only simulate density?

## Y — Follow-ups: Logging Architecture (from U75–U76)

**Q84.** U76 says per-session directory `logs/x2d/<session_id>/` containing `x2d_metrics.jsonl`, `x2d_window_metrics.jsonl`, etc. The `x2d_sessions.jsonl` file records session start/end metadata and spans multiple sessions. Does it live at `logs/x2d/x2d_sessions.jsonl` (cross-session index, one entry per session start/end), while per-session metric files live inside the session subdirectory? Or does each session directory contain its own `x2d_sessions.jsonl` with a single entry?

## Z — Follow-ups: Authority Counting & Invariants (from Q65)

**Q85.** Q65 says invalidated authorities with zero active non-invalidated grants don't count in A "if they have no constitutional authority." The RSA itself has constitutional authority (sovereign, not treaty-derived). Does the RSA always count in A, giving A ≥ 1 as an invariant? If so, density = M/(A×B) ≤ M/B when all treaties are invalidated, which bounds the worst case. Confirm this interpretation and whether A ≥ 1 is an exploitable invariant for the termination proof in Q81.

---

## AA — Follow-ups: Kernel Scope Expansion (from V79, A1)

**Q86.** V79 says amendment adoption and treaty revalidation must live *inside* `policy_core_x2`, not in the harness. This means `policy_core_x2.run_cycle()` must now: (1) accept amendment candidates as input, (2) invoke X-1 amendment adoption logic, (3) run revalidation, (4) then proceed with grants → revocations → density → actions. Currently amendment adoption lives in the X-1 amendment engine and is invoked by harnesses externally. Does V79 mean the existing X-1 amendment engine code is *called from within* `policy_core_x2` (composition), or that the logic is *moved/duplicated* into `policy_core_x2` (inlining)? Composition preserves X-1 module boundaries; inlining risks divergence.

**Q87.** V79's kernel expansion combined with V78's API change (`cycle_ordering_mode` parameter) and the new revalidation machinery represents substantial kernel modification. A1 says "X-2D introduces no new authority semantics and no new kernel physics." Is the position that amendment internalization + revalidation + ordering mode are *organizational* changes (moving existing physics to correct location) rather than *new* physics? If so, is there a bright line test for what would constitute "new physics" under this definition?

**Q88.** If `run_cycle()` now accepts amendment candidates and `cycle_ordering_mode`, existing callers (X-2 profiling harness, X-0E CLI) must be updated. Should they pass `amendment_candidates=[]` and `cycle_ordering_mode="DEFAULT"` explicitly, or should these parameters have defaults that preserve backward-compatible behavior? If defaults, existing callers need zero code changes but implicitly depend on default semantics.

## AB — Follow-ups: M and Constitutional Authority in Density (from W81, Z85)

**Q89.** W81 says "M for treaty-derived authorizations" becomes 0 when all treaties are invalidated. Z85 confirms the RSA always counts in A. But the RSA has *constitutional* authority — it can execute actions (Notify, ReadLocal, etc.) by sovereign right, not via treaty. Do these constitutional (authority, action) pairs contribute to M in the density formula? If yes, then with all treaties invalidated, density = M_constitutional / (1 × B), which is nonzero. If no, density = 0. The termination proof and the density invariant depend on which interpretation holds. Which is it?

## AC — Follow-ups: Generator Access to Kernel (from X83)

**Q90.** X83 says the generator must run "the same deterministic kernel functions in dry-run mode." Does this mean the generator directly imports and calls kernel functions (`_compute_effective_density()`, `apply_constitutional_revalidation()`, treaty admission gates, etc.) during plan construction? If so, the generator has a direct dependency on kernel internals, which means kernel changes require generator updates. Is that acceptable, or should the generator call a dedicated "simulation API" that wraps kernel functions with a stable interface?

## AD — Follow-ups: Revalidation Event Schema (from W82, R67)

**Q91.** R67 defined `TreatyRevalidationEvent` with `result: {VALID, INVALIDATED}`. W82 says emit events only for treaties that transition to INVALIDATED, plus a `TreatyRevalidationSummaryEvent` with `checked_count` and `invalidated_count`. Since individual events are now always INVALIDATED, should the `result` field be dropped from `TreatyRevalidationEvent` (it's always `INVALIDATED`), or retained for forward compatibility in case a future phase wants to log VALID results?

## AE — Follow-ups: Naming & Minor Consistency (from Y84, U76)

**Q92.** U76 names the session log `x2d_sessions.jsonl` (plural). Y84 names it `x2d_session.jsonl` (singular) and specifies it lives inside each per-session directory with only that session's start/end records. Which name is authoritative? Singular makes sense for per-session files; plural makes sense for a cross-session index. Should the convention be: `x2d_session.jsonl` (singular) per session directory + `index_sessions.jsonl` for the cross-session index?

---

## AF — Follow-ups: Density Definition Retraction & Repair Loop (from AB89, W81, Z85)

**Q93.** AB89 retracts W81/Z85's binding "A ≥ 1 always (RSA counts in A)." The new binding is: A counts only delegated authorities; RSA excluded; A=0 → density=0 by convention. W81's termination proof relied on A ≥ 1. The revised termination argument is "finite monotonic removal of treaties, eventually A=0 → density=0." This is sound, but during the repair loop, intermediate density can *spike* above the bound (invalidating a treaty drops A faster than M, increasing density temporarily). Should the density-repair loop's correctness contract explicitly state: "intermediate over-bound density within the loop is expected and not a failure; the invariant is that the loop terminates with density < bound OR density = 0 (no treaties)"?

**Q94.** AB89 redefines density as delegation-only. The existing `_compute_effective_density()` in [artifacts_x2.py](kernel/src/rsax2/artifacts_x2.py) presumably computes `M/(A×B)`. When A=0 and M=0, this is 0/0. Should the function return `(0, B, 0, 0.0)` as a guarded special case (i.e., `if A == 0: return (0, B, 0, 0.0)`)? And should this guard be considered a bug fix to the existing kernel code, or an X-2D-specific change gated by `cycle_ordering_mode`?

## AG — Follow-ups: Simulation API Mechanics (from AC90)

**Q95.** AC90 places the simulation API at `kernel/sim/simulate_cycle()`. The existing kernel code is at `kernel/src/rsax2/`. Should the sim package be `kernel/src/rsax2/sim/` (sub-package, natural import path like `from rsax2.sim import simulate_cycle`) or a separate top-level `kernel/sim/` (parallel to `kernel/src/`)? The former keeps simulation tightly coupled to the kernel version; the latter signals it's a distinct utility layer.

**Q96.** AC90 says simulation runs "without side effects." The kernel's `run_cycle()` mutates `InternalStateX2` in place. Should `simulate_cycle()` deep-copy the input state and mutate the copy (returning the modified copy plus outputs), or should it be a pure function that takes immutable snapshots and computes outputs without any state mutation? Deep-copy is simpler to implement given existing code; pure computation is cleaner but requires refactoring state updates.

---

No further follow-ups. All binding decisions from Rounds 1–6 are internally consistent and mechanically actionable. The Q&A is converged.

*Total: 96 questions across 33 sections (A–AG), all answered.*
