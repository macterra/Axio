# IX-4 Pre-Implementation Questions

## 1. Injection Mechanism

### 1.1 What is the concrete injection interface?

The spec says injection must use "pre-existing, non-privileged execution interfaces available to any agent, differing only by key material." The IX-3 `AuthorityStore.inject()` is called once at epoch 0 and is conceptually immutable thereafter.

**Q**: Does injection mean calling `AuthorityStore.inject()` (or an append variant) at a mid-run epoch? Or does the harness add new authority artifacts to the store at a designated injection epoch, which the existing two-pass admissibility then evaluates normally?

If the store is truly immutable after epoch 0 (IX-2/IX-3 invariant), we need either:
- (a) a new `AuthorityStore.inject_additional()` method that appends without replacing, or
- (b) a harness-level mechanism that reconstructs the store with additional artifacts at injection epoch.

Either way, the admissibility engine itself stays untouched — it just sees more artifacts. Is that the intended design?

### 1.2 Who is the injector?

The spec says injection is "external to the kernel and governance process, not necessarily external to the agent population." But §4.1 says agents in the political layer accept or reject injected authority.

**Q**: Is the injector modeled as:
- (a) the harness itself (an environmental event, like a fault injection in IX-3 Condition I),
- (b) a distinguished agent (e.g., A_INJ) that participates in the epoch loop but whose actions are "supply authority" rather than "write state", or
- (c) a non-agent external entity that deposits artifacts into the AuthorityStore at a designated epoch?

Option (a) is cleanest for determinism but risks the harness becoming a sovereign actor. Option (b) makes the injector auditable but requires defining its strategy class. Option (c) is closest to the spec's "external force" framing.

### 1.3 What does "accepting or rejecting injected authority" mean mechanically?

An agent doesn't choose which authorities exist in the store — the store is global. An ALLOW artifact for agent X on key K means X *can* cite it. "Rejection" presumably means the agent's strategy simply never cites the injected authority in its `ActionRequest.authorities_cited`.

**Q**: Is that correct? Acceptance = citing the injected authority; rejection = not citing it (and continuing to act under baseline authorities or refusing)? There is no explicit "accept/reject" API call?

### 1.4 Does injection create new ALLOW artifacts, new DENY artifacts, or both?

The spec focuses on "authority supply" which implies ALLOW. But:

**Q**: Can injection also supply DENY artifacts (global vetoes)? That would be a qualitatively different political act — giving someone the power to block rather than the power to write. Should the preregistration enumerate which types of artifacts each condition injects?

---

## 2. Authority Persistence and Expiration

### 2.1 What does "persistence model" mean concretely?

The spec lists: one-shot, renewable, expiring, or issuer-controlled. The current `AuthorityStore` has no concept of expiration — artifacts are eternal once injected.

**Q**: Do we need to extend the authority artifact schema with an `expires_at_epoch` field? Or is expiration modeled by the harness removing artifacts from the store at a designated epoch? The former is cleaner; the latter risks harness sovereignty.

### 2.2 What does "issuer-controlled" persistence mean?

**Q**: Does this mean the injector can revoke previously injected authority? If so, that's a new mechanism (revocation) not present in IX-2/IX-3. How is revocation triggered — by an injector action in the epoch loop, or by a harness schedule?

### 2.3 Does expiration violate "no authority synthesis"?

If an authority expires at epoch N, the system's capability surface changes without any agent action. That's arguably the kernel "deciding" that authority no longer applies.

**Q**: Is expiration a pre-committed schedule (frozen at injection time, not a runtime decision), or is it dynamically controlled? Only the former seems compatible with kernel non-sovereignty.

---

## 3. World State and Key Space

### 3.1 Do we reuse the IX-3 6-key world state?

IX-3 uses: K_POLICY, K_TREASURY, K_REGISTRY, K_LOG, K_OPS_A, K_OPS_B.

**Q**: Does IX-4 use the same key space, or does injection introduce additional keys (e.g., K_INJECTED, K_SUBSIDY)? The spec doesn't mention new keys, but some conditions (authority flooding) might need additional surface area to be meaningful.

### 3.2 What is the baseline governance configuration?

Each condition starts from some governance state (potentially a failure state from IX-3).

**Q**: Do we start each condition from a specific IX-3-like configuration (e.g., Condition A starts from an IX-3 Condition A livelock baseline), or do we design fresh configurations? The spec says injection occurs "during deadlock," "during livelock," "after collapse" — this implies we need baseline states that exhibit those failures *before* injection occurs.

---

## 4. Conditions — Design Specifics

### 4.1 Condition A — Symmetric Relief Injection

"Authority injected equally during deadlock."

**Q**: Does "equally" mean identical ALLOW artifacts for all agents on the contested key? If 4 agents are in livelock on K_POLICY (IX-3 Condition A scenario), does symmetric relief mean injecting additional K_POLICY ALLOWs for all 4? That would likely just reproduce the same livelock — which may be exactly the point ("relief doesn't resolve"). Should the prereg specify the injection target key and quantities?

### 4.2 Condition B — Asymmetric Empowerment

"Authority injected to a subset of agents."

**Q**: How many agents receive injection — 1 of 4? 2 of 4? Does the empowered agent receive authority over the contested key specifically, or over a different key? The political dynamics differ substantially: empowering one agent on the deadlocked key breaks the deadlock but creates capture; empowering on a different key doesn't break the deadlock but creates asymmetry.

### 4.3 Condition C — Conditional Supply

"Authority supplied contingent on compliance."

**Q**: What is the compliance condition, and who evaluates it? The kernel can't evaluate compliance (sovereignty violation). Does the harness check a world-state predicate at the injection epoch and only inject if the predicate holds? Or does the injector agent (if one exists) observe state and decide whether to inject? The former is deterministic but potentially sovereign; the latter requires an injector strategy class.

### 4.4 Condition D — Authority Flood

"Large authority oversupply."

**Q**: Does flooding mean injecting many ALLOW artifacts for the same key to the same agent (redundant), many ALLOWs across many keys to many agents (broad), or many ALLOWs for the same key to different agents (contention amplification)? Each produces different dynamics. What is "large" — 10x baseline? 100x?

### 4.5 Condition E — Post-Collapse Revival

"Authority injected after collapse."

**Q**: Collapse in IX-3 means all agents have exited. If all agents are gone, who receives the injected authority? Does revival mean:
- (a) new agents are introduced post-collapse (a mechanism IX-3 doesn't have),
- (b) previously exited agents "re-enter" (violates IX-3 exit permanence), or
- (c) the injection occurs at collapse time to the last remaining agent(s) before they exit?

Option (a) requires new agent introduction mechanics. Option (b) contradicts prior phases. Option (c) is technically pre-collapse, not post-collapse.

---

## 5. Failure Detection and Classification

### 5.1 What new IX4_FAIL tokens are needed?

The instructions reference:
- `IX4_FAIL / IMPLICIT_SOVEREIGNTY` (privileged injection path)
- `IX4_FAIL / TOOLING_SOVEREIGNTY` (tooling decides)
- `IX4_FAIL / KERNEL_BREACH` (exit coercion)

**Q**: Are there additional IX4_FAIL tokens? The spec mentions capture, dependency, and coercion as recordable outcomes — are these descriptive classifications (like governance styles in IX-3) or do they have formal detector predicates?

### 5.2 How is "capture" detected formally?

The spec says capture occurs when "injected authority asymmetrically dominates governance" and "exit pressure increases without kernel enforcement."

**Q**: What is the formal predicate? Something like: "Post-injection, one agent executes >X% of institutional actions and other agents' exit rate increases"? Or is capture a qualitative label assigned by manual review? IX-3 governance styles had precise metric thresholds — does IX-4 capture need the same?

### 5.3 How is "dependency" detected formally?

**Q**: Is dependency defined as: "Agent X cites injected authority in >Y% of post-injection actions"? Or: "Agent X's execution rate drops to zero if injected authority is removed (counterfactual)"? The latter requires a counterfactual run, which complicates the protocol.

---

## 6. Determinism and Replay

### 6.1 Are injection events deterministic?

**Q**: Is the injection schedule (which epoch, which artifacts, which agents) fully frozen in the preregistration, or does any injection depend on runtime state (e.g., "inject when deadlock is detected")? The latter introduces a determinism concern: if the deadlock detector is stateful and the injection trigger depends on detector output, the injection epoch must be reproducible across replays.

### 6.2 Does conditional injection (Condition C) break replay determinism?

If injection is contingent on compliance (a runtime state predicate), and the agent's compliance depends on the injection (circular), is this still deterministic?

**Q**: Should conditional injection use a fixed-epoch schedule where the *harness* checks a frozen predicate at a frozen epoch, ensuring determinism?

---

## 7. Agent Count and Identity

### 7.1 How many agents per condition?

IX-3 used 4 agents for all conditions.

**Q**: Does IX-4 also use 4? The spec mentions "multiple RSAs or authority-bearing agents" but doesn't fix a count. Does the injector count as an agent?

### 7.2 Are agent strategies new or reused from IX-3?

**Q**: Do we need entirely new strategy classes for IX-4 (e.g., strategies that react to injected authority), or can we compose from IX-3 strategies with injection-aware wrappers? The spec doesn't prescribe strategy behavior beyond "accepting or rejecting injected authority."

---

## 8. Architectural Questions

### 8.1 Does IX-4 reuse the IX-3 harness or build a new one?

The IX-3 `gs_harness.py` is ~1,290 lines with epoch execution, admissibility, metrics, and PASS evaluation tightly coupled to 10 specific conditions.

**Q**: Should IX-4:
- (a) extend the IX-3 harness with injection hooks,
- (b) build a new `ip_harness.py` that reuses the IX-2 kernel but has its own epoch loop, or
- (c) factor out a shared epoch engine from IX-3 and build IX-4 on top of it?

Option (b) seems cleanest given the spec's emphasis on IX-4 being a distinct experiment.

### 8.2 Does the IX-2 two-pass admissibility need modification?

**Q**: If injected authorities are just additional artifacts in the store, the existing two-pass evaluation should work unchanged — Pass-1 checks if the cited authority exists and covers the scope, Pass-2 checks for interference. Is that correct, or does injection require any admissibility changes?

### 8.3 How does IX-4 handle the "no authority synthesis" rule with injection?

Injection adds authority artifacts after epoch 0. IX-2/IX-3 explicitly state "all authority artifacts are injected at epoch 0 and immutable thereafter."

**Q**: IX-4 necessarily relaxes this invariant. The preregistration needs to explicitly state which invariant is relaxed and what replaces it. Proposed formulation: "Authority artifacts are injected at epoch 0 (baseline) and at designated injection epochs (treatment). No authority is created by agent action, kernel logic, or tooling. All injection events are pre-committed in the frozen design."

---

## 9. Scope and Scale

### 9.1 How many conditions total?

The spec lists 5 (A–E). The instructions say "all preregistered IX-4 conditions" but don't enumerate beyond A–E.

**Q**: Is 5 the final count, or should the preregistration include additional conditions (e.g., injection-as-noise, injection-with-revocation, multi-wave injection)?

### 9.2 How many epochs per condition?

IX-3 conditions ranged from 5 to 30 epochs.

**Q**: Does IX-4 need longer runs to observe post-injection dynamics? If injection occurs at epoch 10 and we need 20 epochs of post-injection observation, max epochs should be ≥30. Should this be condition-specific?

### 9.3 What is the expected preregistration structure?

**Q**: Should the IX-4 preregistration follow the exact same structure as IX-3 (frozen definitions, frozen conditions, frozen strategies, frozen PASS predicates, frozen classification, frozen logging schema)? Or does the injection mechanism require additional frozen sections (frozen injection schedules, frozen persistence models)?
---
---

# Follow-Up Questions (post-answers)

## F1. AuthorityStore Epoch-Aware View

The answer to 1.1 proposes either `append_injection(batch_id, artifacts)` or an "epoch overlay store" that materializes `AuthorityStoreView(epoch)`.

**Q**: The current IX-2 `AuthorityStore` is a flat list with no epoch awareness. Admissibility calls `get_allows_for_scope()` and `has_deny_for_scope()` without an epoch parameter. If we add `valid_from_epoch` / `valid_until_epoch` fields (answer 2.1), the store's query methods need to filter by current epoch.

Should we:
- (a) subclass `AuthorityStore` as `InjectionAwareAuthorityStore` that overrides query methods to accept an epoch parameter, or
- (b) wrap the existing store in a view object (`AuthorityStoreView(base_store, epoch)`) that filters on read, or
- (c) pre-filter the artifact list at each epoch and pass a standard `AuthorityStore` containing only currently-valid artifacts to admissibility?

Option (c) preserves the IX-2 admissibility code completely untouched. Options (a)/(b) require admissibility to pass epoch context through.

## F2. InjectionEvent Schema

Answer 1.2 says injection is a ledger event (`InjectionEvent`) processed by the same execution pipeline.

**Q**: What fields does `InjectionEvent` carry? Proposed:
- `event_type: "INJECTION"`
- `batch_id: str` (unique per injection batch)
- `epoch: int` (when applied)
- `artifacts: list[dict]` (the ALLOW artifacts being injected)
- `trigger: "FIXED_EPOCH" | "STATE_TRIGGERED"`
- `trigger_predicate: str | None` (frozen predicate name, if state-triggered)

Is there anything else needed for auditability? Should the event carry a justification field (even if it's just a frozen string like "symmetric_relief"), or would that risk framing bias (tooling sovereignty)?

## F3. Lead-In Phase Mechanics

Answer 3.2 says each condition runs a "lead-in" phase under an IX-3-like configuration until the target failure state is reached, then injects.

**Q**: How is the lead-in implemented?
- (a) Literally run an IX-3 condition builder (e.g., `build_condition_A()`) for the lead-in, then switch strategies and inject? But IX-3 conditions have specific max_epochs and termination rules that would interfere.
- (b) Build IX-4-specific lead-in configurations that reproduce failure states but with IX-4 termination semantics?
- (c) Hard-code lead-in epochs based on known IX-3 timing (e.g., "livelock at epoch 4 under Condition A config") and inject at a fixed epoch after that?

Option (c) is simplest and most deterministic but couples to IX-3 implementation details. Option (b) is cleanest but requires re-specifying baseline configs in the IX-4 prereg.

**Follow-up**: If the lead-in uses a state-triggered injection (answer 6.1 style 2), and the target failure state is never reached within `E_pre=15` epochs, the answer says emit `INVALID_RUN / BASELINE_NOT_REACHED`. Should the prereg include a proof or argument that the chosen baseline configurations *will* reach failure within 15 epochs, to avoid this being a design-time surprise?

## F4. Strategy Injection-Awareness Interface

Answer 7.2 proposes wrapping IX-3 strategies with injection-awareness toggles: "baseline-only," "opportunist," "refusal-hardliner," "capture-seeker."

**Q**: How does a strategy *know* which authorities are injected vs. baseline? Options:
- (a) Tag injected artifacts with a `source: "injection"` field, and strategies can inspect the authority store to distinguish.
- (b) Deliver injection events in the `Observation` so strategies see "injection happened at epoch E with these artifacts" and can react.
- (c) Strategies don't know — they just see more authorities in the store and react to expanded capability surface without distinguishing source.

Option (c) is the most honest: agents don't have privileged knowledge of injection provenance. But then "refusal-hardliner" can't be implemented as "refuse injected authority" — it would have to be "refuse any authority not in my epoch-0 set," which requires the strategy to remember its initial authorities.

**Follow-up**: If strategies can distinguish injected from baseline, does that constitute an implicit information channel that violates neutrality? The spec says tooling must not frame injection — does strategy-level source tagging count as framing?

## F5. Condition E Collapse Redefinition

Answer 4.5 redefines collapse for IX-4 as "governance-collapse state" (terminal failure classifier reached while agents remain) rather than IX-3's "all agents exited."

**Q**: This creates a terminology conflict with IX-3 where `COLLAPSE` specifically means `CollapseDetector` → no active agents remain. Should IX-4:
- (a) introduce a new terminal classification (e.g., `GOVERNANCE_COLLAPSE`) distinct from IX-3's `COLLAPSE`,
- (b) reuse `STATE_LIVELOCK` as the pre-injection terminal state for Condition E (since livelock is terminal and agents remain), or
- (c) use IX-3 Condition F's dissolution sequence but inject *before* the last agent exits?

Option (b) seems most natural — "post-collapse revival" becomes "post-livelock injection" which is operationally cleaner. But then it overlaps with Condition A (symmetric relief during deadlock/livelock). How do A and E differ if both inject after livelock?

## F6. PASS Predicate Design

The answers resolve what IX4_FAIL tokens exist and what capture/dependency classifiers look like, but don't specify the per-condition PASS predicates.

**Q**: What makes each condition PASS? In IX-3, PASS was defined by specific terminal classifications and metric thresholds. For IX-4:
- Does Condition A PASS if injection *fails to resolve* livelock (proving "relief ≠ resolution")?
- Does Condition B PASS if capture is *detected* (proving "asymmetric empowerment → capture")?
- Does Condition C PASS if conditional supply creates *dependency* (proving "compliance requirements → lock-in")?
- Does Condition D PASS if flood creates *dilution or noise* (proving "abundance ≠ coordination")?
- Does Condition E PASS if revival is *non-legitimate* (proving "injection after failure ≠ recovery")?

Or is PASS simply "no IX4_FAIL tokens emitted AND all classifiers executed AND replay deterministic"? The latter is more like IX-3's aggregate rule; the former requires hypothesis-specific predicates.

## F7. Injection Batch Identification in Admissibility

If injected artifacts are tagged (e.g., with `batch_id` or `source: "injection"`), the two-pass admissibility currently doesn't inspect those fields — it only checks scope, holder, and commitment type.

**Q**: Is that correct — admissibility is source-blind? The kernel treats injected ALLOW artifacts identically to baseline ALLOW artifacts? This seems required by "no kernel endorsement of injected authority" — but it also means the kernel can't *refuse* injected authority either. The political dynamics are entirely in the agent layer (cite or don't cite). Confirming this is the intended design.

## F8. Capture vs. Legitimate Dominance

Answer 5.2 defines capture as one agent executing ≥70% of successful writes post-injection.

**Q**: In IX-3 Condition B (Execution-Biased), one agent could dominate writes through legitimate partitioned authority. How does the capture classifier distinguish "capture via injection" from "dominance via baseline authority"? Should the predicate be: "≥70% of successful writes *cite injected authority*" rather than just "≥70% of successful writes by one agent"?

## F9. Renewable Authority via Multiple Batches

Answer 2.2 says renewable persistence is modeled via "multiple precommitted batches" rather than runtime decisions.

**Q**: For which conditions is renewable authority relevant? If Condition A injects once and the authority is permanent, that's one-shot-permanent. If Condition C injects conditionally, that's one-shot-conditional. Does any condition need multi-wave injection, or is that deferred to a future version?

If no condition uses renewable/expiring persistence in v0.1, should we still implement the `valid_from_epoch` / `valid_until_epoch` fields, or defer that machinery to keep v0.1 minimal?
---
---

# Follow-Up Questions Round 2 (post-F-answers)

## G1. AuthorityStoreBase Implementation

F1 answer chooses option (c): pre-filter per epoch, pass a standard `AuthorityStore` to admissibility. The harness maintains an `AuthorityStoreBase` with baseline + injected artifacts and constructs `AuthorityStoreEpoch(t)` each epoch.

**Q**: Concretely, is `AuthorityStoreBase` a new class, or just a Python list of artifacts with metadata? The existing IX-2 `AuthorityStore` has a single `inject()` method that replaces the whole list. For IX-4 we need:
- baseline artifacts (loaded once at epoch 0)
- injection batches (appended at injection epochs)
- per-epoch view construction

Proposed: a thin wrapper holding `baseline: list[dict]` + `injections: list[InjectionBatch]`, with `view_at(epoch)` returning a standard `AuthorityStore` populated with `baseline + [a for batch in injections if batch.epoch <= epoch for a in batch.artifacts]`. Is that sufficient, or does the view also need to track *which* artifacts are injected (for the audit-layer classifiers in G4)?

## G2. Strategy Transition at Injection Epoch

F3 answer says IX-4 builds its own lead-in configurations with IX-4 termination semantics. F4 answer says strategies don't know injection provenance.

**Q**: Do agent strategies change at the injection epoch? Two designs:
- (a) **Single strategy per agent** for the entire run. The strategy's behavior naturally evolves as the authority surface changes (e.g., an opportunist starts citing new authorities when they appear).
- (b) **Strategy swap at injection epoch**: lead-in uses one strategy (e.g., `ContestPolicyAlways` to produce livelock), then post-injection the harness swaps to a different strategy (e.g., `Opportunist`).

Option (a) is cleaner — no mid-run strategy mutation. But it means the lead-in strategy must *also* be the post-injection strategy. An opportunist that cites whatever is available would never produce a clean livelock baseline.

Option (b) is pragmatic but introduces a harness intervention at injection time that isn't just "add authorities" — it's also "change agent behavior." That's a second variable, not just injection.

Is there a third option — strategies that have a built-in phase transition triggered by observing expanded authority surface?

## G3. Governance Collapse Detector Predicate

F5 answer introduces `STATE_GOVERNANCE_COLLAPSE` as distinct from IX-3's `COLLAPSE`.

**Q**: What is the exact detector predicate? Proposed candidates:
- (a) `STATE_LIVELOCK` already latched (terminal livelock, N=5 epochs unchanged) AND ≥1 agent active.
- (b) `STATE_DEADLOCK` detected (no admissible institutional actions) AND persists for M epochs AND ≥1 agent active.
- (c) Either (a) or (b).

Is `STATE_GOVERNANCE_COLLAPSE` a *composite* terminal classification that triggers when any IX-3 terminal state (livelock, deadlock) is reached while agents remain? Or is it a new, independent detector with its own predicate?

**Follow-up**: If governance collapse is just "livelock while agents remain," then Condition A (inject during deadlock) and Condition E (inject after governance collapse) differ only in timing:
- A injects at first deadlock/livelock detection (pre-terminal, before latch).
- E injects after livelock latches (post-terminal).

That's a meaningful distinction — pre-latch vs. post-latch — but the prereg should make it explicit.

## G4. Audit-Layer Provenance vs. Kernel Source-Blindness

F7 confirms admissibility is source-blind. F8 refines capture to require `writes_citing_injected / writes_by_X >= 0.60`. The dependency classifier (answer 5.3) also references "injected authorities."

**Q**: The audit/classification layer needs to know which authorities are injected to compute capture and dependency metrics. But admissibility is source-blind. This means:
- Authority artifacts carry a `batch_id` or `source` tag *in their metadata*, which admissibility ignores but classifiers read.
- Or: classifiers cross-reference `InjectionEvent` logs to identify which authority IDs were injected.

The second approach (cross-reference) keeps artifacts schema-identical to IX-3 and puts provenance tracking entirely in the audit layer. Is that preferred? Or should injected artifacts carry an explicit `injection_batch_id` field that admissibility skips but classifiers consume?

## G5. Condition C — Predicate Design and Non-Injection Path

F-answers confirm Condition C uses a frozen world-state predicate at a frozen epoch. If the predicate doesn't hold, injection doesn't happen.

**Q**: If the predicate fails and no injection occurs, what does Condition C observe? Just a continued failure state with no treatment? That's a valid control observation ("compliance not met → no relief"), but:
- Is that considered a PASS (the conditional mechanism worked correctly by *not* injecting)?
- Or is it `INVALID_RUN / BASELINE_NOT_REACHED` (the experiment didn't produce the condition it needed)?

The predicate needs careful design. It should be something that *might* hold in some runs but not others — except the system is deterministic, so it either always holds or never holds for a given frozen configuration. That means the prereg author must know in advance whether the predicate will be satisfied.

**Follow-up**: Should Condition C use a two-phase design — (1) run lead-in to failure state, (2) run a few more epochs to check compliance predicate, (3) inject or not — with the prereg freezing a configuration where the predicate is known to hold? This makes it effectively a fixed-epoch injection with extra ceremony. Is the ceremony worth it for the political point ("authority was conditional")?

## G6. Condition D Flood — Post-Injection Dynamics

F-answers define flood as all 4 agents getting ALLOW on all 6 keys (24 new artifacts).

**Q**: After flooding, every agent can write every key. This is the opposite of IX-3's partitioned authority designs. What behavior do we expect?
- If all agents use `ContestPolicyAlways` (from lead-in), they now contest *all* keys → massive interference → immediate livelock on everything.
- If agents use `OpsPartitionWriter` strategies, they continue writing their partition keys and ignore the new capabilities.

The post-flood dynamics depend entirely on agent strategy. Should the prereg specify post-injection strategies that actually *exercise* the flooded authority (so dilution/noise is observable), or is it acceptable for strategies to simply ignore the flood?

## G7. PASS as Exposure — What Distinguishes Conditions?

F6 answer says PASS is global: no IX4_FAIL, all classifiers executed, replay deterministic. Per-condition outcomes are recorded, not required.

**Q**: If all 5 conditions have the same PASS criteria, what makes running 5 separate conditions worthwhile? In IX-3, each condition tested a different hypothesis with a different PASS predicate. In IX-4, if PASS is just "ran cleanly," the conditions are distinguished only by their *descriptive* classification outputs (capture detected / dependency detected / dilution detected / etc.).

Is the IX-4 claim then: "Under these 5 injection regimes, political dynamics emerged and were classifiable — and no sovereignty violations occurred"? That's weaker than IX-3's per-condition claims. Is that intentional — because IX-4 is exposure-only, not prediction?

**Follow-up**: Should the prereg include **expected classification labels** per condition (e.g., "Condition B is expected to produce capture") even if those expectations aren't part of PASS? This gives reviewers something to evaluate beyond "it ran without errors."

## G8. Observation Delivery — What Do Agents See?

F4 answer says agents don't know injection provenance. The current IX-3 `Observation` delivers `(epoch, world_state, own_last_outcome)`.

**Q**: Should the IX-4 `Observation` also include the agent's current authority surface (list of authority IDs the agent holds)? In IX-3 this wasn't needed because authorities were static. In IX-4, the surface changes at injection epoch. Without observing their own authorities, agents can't detect that new capabilities appeared.

Options:
- (a) Add `available_authorities: list[str]` to `Observation` — IDs only, no provenance.
- (b) Agents query the store directly via a read-only reference.
- (c) Agents don't observe authorities — they just try actions and see what passes.

Option (c) is the most "politically blind" but means strategies can't be adaptive. Option (a) is minimal and provenance-free. Which fits IX-4's intent?

## G9. Replay Verification Across Lead-In + Injection

F-answers establish a two-phase structure: lead-in (pre-injection) + observation (post-injection), with injection deterministically triggered.

**Q**: For replay verification, is the full run (lead-in + injection + observation) replayed as a single trace? Or are lead-in and post-injection verified separately? A single trace is simpler. But if the injection trigger is state-based (F3 style 2), the replay must re-evaluate the trigger predicate and confirm it fires at the same epoch.

Should the results log record the injection epoch explicitly so replay can verify "injection occurred at epoch T in both runs"?

---
---

# Follow-Up Questions Round 3 (post-G-answers)

## H1. Single-Strategy Phase Change — Detecting Capability Expansion

G2 decides on single strategy per agent with endogenous phase change triggered by observing an expanded capability surface. G8 adds `available_authorities: list[str]` to `Observation`.

**Q**: The phase-change mechanism requires each strategy to compare its current `available_authorities` against its epoch-0 snapshot. This is straightforward for the opportunist ("new IDs appeared → try them") and refusal-hardliner ("new IDs appeared → ignore them").

But what about `ContestPolicyAlways` from IX-3? It always writes K_POLICY. Post-injection it would continue doing exactly the same thing regardless of new authorities. That's the "baseline-only" behavior — but it's not *choosing* to be baseline-only, it just doesn't look at authorities.

**Follow-up**: Should every IX-4 strategy be *required* to inspect `available_authorities` and make an explicit cite/don't-cite decision? Or is it acceptable for some strategies to be injection-oblivious (never referencing the expanded surface), with the political interpretation being "this agent is structurally indifferent to injection"?

## H2. AuthorityStoreBase + InjectedArtifactSet — Concrete ID Scheme

G1 defines `AuthorityStoreBase` with baseline + injection batches. G4 says provenance lives in the event log, and classifiers build `InjectedArtifactSet` by parsing injection events.

**Q**: How are injected authority artifact IDs generated? IX-3 uses the `GS-NNNN` scheme (sequential, reset per condition). If IX-4 uses the same scheme, injected artifacts would get IDs like `GS-0025` that are indistinguishable from baseline IDs by naming convention alone.

Options:
- (a) Continue `GS-NNNN` — provenance is tracked only via injection event cross-reference.
- (b) Use a different prefix for IX-4: `IP-NNNN` for all artifacts (baseline + injected).
- (c) Use `IP-NNNN` for baseline, `IP-INJ-NNNN` for injected — giving classifiers a fast ID-pattern check.

Option (a) is purest (source-blind even at ID level). Option (c) is pragmatic for classifier performance but leaks provenance into the ID namespace. Which fits IX-4's discipline?

## H3. Governance Collapse Latch — Reversibility After Injection

G3 defines `STATE_GOVERNANCE_COLLAPSE` as a composite latch when terminal livelock or terminal deadlock is reached while agents remain. In IX-3, livelock latches are permanent — once latched, they never clear.

**Q**: If governance collapse latches before injection, and injection adds new authorities that break the livelock, does the governance collapse classification *persist* (because it latched) or *reverse* (because governance resumed)?

This is critical for Condition E ("zombie governance"):
- If the latch is permanent, post-injection writes happen under a "zombie" label. The system is *technically* executing but *classified* as collapsed. That's the intended observation.
- If the latch reverses, injection genuinely "revived" governance, which would mean injection *resolved* failure — and IX-4 should fail.

**Follow-up**: Should the prereg explicitly state: "Governance collapse is a permanent latch. Post-injection execution under a latched governance-collapse classification is recorded as 'zombie execution' and does NOT constitute governance revival"?

## H4. Condition A — Symmetric Relief Into Livelock

G-answers confirm Condition A injects at first deadlock detection (pre-latch). The IX-3 Condition A baseline is 4 agents all running `ContestPolicyAlways` on K_POLICY → livelock at epoch 4.

**Q**: If symmetric relief injects additional K_POLICY ALLOWs for all 4 agents, but all 4 are already using `ContestPolicyAlways` which always writes K_POLICY, the injection adds redundant capability — they already have K_POLICY ALLOW. The injection changes nothing because the bottleneck is contention, not capability.

Should Condition A's relief inject authority on a *different* key (e.g., K_TREASURY) so agents have somewhere to redirect? But then the strategies need to be capable of writing K_TREASURY, which `ContestPolicyAlways` isn't.

This circles back to G2/H1: the strategy must be able to *use* injected authority for the condition to be meaningful. Should Condition A use an opportunist strategy that switches to writing a newly available key when relief authority appears?

## H5. Condition B — Capture Dynamics Require Strategy Asymmetry

G-answers confirm 1-of-4 empowerment for Condition B. The empowered agent gets ALLOW on the contested key. But if all 4 agents are using the same strategy (e.g., `ContestPolicyAlways`), empowerment doesn't create capture — it just adds one more ALLOW to the same contention.

**Q**: Capture requires the empowered agent to *dominate* writes. This means:
- The empowered agent's strategy must exploit its advantage (e.g., write to keys others can't).
- Non-empowered agents' strategies must be affected (e.g., refusal, exit, deferral).

Should Condition B assign different strategies per agent: empowered agent = `CaptureSeeker`, others = `RefusalHardliner` or `Opportunist`? Or should all agents have the same strategy and let asymmetric capability alone drive different outcomes?

If the latter, what strategy produces capture-like dynamics from capability asymmetry alone?

## H6. Condition C — Two-Phase Predicate Mechanics

G5 confirms the predicate is frozen, known to hold, and failure to satisfy it is `INVALID_RUN / CONDITION_PREDICATE_NOT_SATISFIED`.

**Q**: Concretely, what is the predicate? The example in the original answers was `K_POLICY == P0`. But during the lead-in phase, the system enters deadlock/livelock, meaning K_POLICY is likely *unchanged* from its initial value (no writes succeeded). So "K_POLICY == initial_value" would trivially hold.

That makes the "compliance check" vacuous — the predicate is always true because nothing changed. Should the predicate test something that's actually uncertain — like "at least one successful write to K_LOG occurred"? But in a deterministic system, that's also known in advance.

**Follow-up**: Is the real design challenge that Condition C's "conditionality" is performative rather than substantive? The political point is "authority was supplied *because compliance was observed*" — but in a deterministic frozen system, the conditional pathway is fully predetermined. Is the prereg honest about this, or does it frame the conditionality as if it were contingent?

## H7. Condition D — Strategy for Exercising Flood

G6 says the prereg must include strategies that exercise the expanded surface post-flood. G2 says strategies have endogenous phase change.

**Q**: What concrete strategy exercises all 6 keys after flood? Proposed:
- `FloodExploiter`: post-expansion, rotates writes across all keys with `epoch % 6` targeting. Pre-expansion, writes only to baseline-authorized keys.

But if all 4 agents run `FloodExploiter` post-flood, they all write to the same key each epoch (since `epoch % 6` is identical) → massive contention → livelock on a rotating key. That's "dilution → interference."

Alternatively, stagger the rotation per agent (`(epoch + agent_offset) % 6`) → disjoint writes → no contention → high throughput. That's "flood enables coordination" which means injection *improved* governance — does that make IX-4 fail?

**Follow-up**: Is it acceptable for one condition to show injection *enabling* governance (as long as it's recorded honestly)? The IX-4 claim is "injection selects political failure modes rather than resolving governance failure." If Condition D shows injection enabling coordination, that's a counterexample to the claim. Should the strategy be designed to produce noise/dilution, or should we let the chips fall?

## H8. Expected Labels as Falsification Targets

G7 says prereg should include expected descriptive labels per condition as non-binding predictions.

**Q**: If the expected label for Condition B is "capture signature likely" but the actual outcome is "no capture, agents ignored injection," is that:
- (a) A surprising but valid result (recorded, no PASS/FAIL impact)?
- (b) Evidence of a design flaw (strategy didn't exercise injection)?
- (c) A falsification of the expected label (interesting scientific finding)?

The distinction matters for how the implementation report frames deviations from expectations. Should the prereg include explicit language like: "Deviations from expected labels are recorded as findings, not as failures. Absence of expected political dynamics may indicate strategy design limitations rather than injection neutrality"?

## H9. Pre-Injection vs. Post-Injection Metric Windows

Capture requires ≥70% dominance over "post-injection window W." Dependency requires ≥60% citation over "window W."

**Q**: How is window W defined?
- (a) Fixed: `W = [t_inject + 1, t_inject + W_size]` where `W_size` is frozen.
- (b) Full post-injection: `W = [t_inject + 1, t_max]`.
- (c) Sliding: compute over rolling windows of size W_size.

Option (b) is simplest but masks transient effects. Option (a) requires choosing `W_size` — too small misses slow dynamics, too large dilutes signal. Option (c) is most informative but adds complexity.

**Follow-up**: Should the prereg also define a pre-injection baseline window for comparison? E.g., `W_pre = [max(0, t_inject - W_size), t_inject]` to compute Δ metrics (change in dominance, change in refusal rate) across injection?
---
---

# Follow-Up Questions Round 4 (post-H-answers)

## I1. Capability-Responsive Strategy Requirement — Minimum Coverage

H1 says each condition must include at least one capability-responsive strategy so injection has a causal pathway. H5 says Condition B needs heterogeneous strategies. H7 says Condition D agents must attempt multiple keys post-flood.

**Q**: Across the 5 conditions, how many distinct strategy classes do we need? Counting from the answers so far:
- `CaptureSeeker` (Condition B empowered agent)
- `RefusalHardliner` (Conditions B, C — refuses non-baseline authorities)
- `Opportunist` (capability-responsive, cites new authorities when available)
- `FloodExploiter` (Condition D — rotates across keys post-expansion)
- `ContestPolicyAlways` (IX-3 reuse — injection-oblivious, used in lead-in baselines)
- `ComplianceSignaler` (Condition C — writes `COMPLIANCE_ACK` to K_LOG under some branch)

Plus whatever strategies produce baseline failure states. That's potentially 6+ new strategy classes beyond IX-3 reuse.

**Follow-up**: Should the prereg enumerate every strategy class with its full behavioral spec (like IX-3 §7.1), or is it sufficient to specify the behavioral contract (e.g., "capability-responsive: cites any available authority that increases write success") and let implementation fill in the details?

## I2. Condition A Redesign — Capability-Scarcity Deadlock

H4 says Condition A should be capability-relief (agents lack ALLOW on a needed key), not contention-relief (agents all contest the same key). Injection supplies the missing ALLOW to all agents.

**Q**: What is a "capability-scarcity deadlock" in the 6-key space? Under IX-3 semantics, deadlock = "no admissible institutional actions exist." That requires:
- No agent has ALLOW on any K_INST key, OR
- All K_INST keys are DENY-blocked.

But if no agent has ALLOW on any K_INST key, then no institutional actions are even *attempted* — and the deadlock detector checks "at least one institutional action was submitted." Silent agents don't trigger deadlock; they trigger "no attempts."

**Follow-up**: Should Condition A's baseline be: agents have ALLOW on *some* K_INST keys but not a critical one (e.g., everyone can write K_LOG but nobody can write K_POLICY), and their strategies require K_POLICY access to make progress? Then relief = injecting K_POLICY ALLOW for all. This produces capability-gated deadlock rather than contention deadlock.

But that means the lead-in isn't really "deadlock" in the IX-3 terminal sense — it's "strategic stall because the desired key is inaccessible." Is that still deadlock per the IX-4 prereg definitions, or does it need a new classification?

## I3. Condition E — Zombie Execution Metrics

H3 confirms governance collapse is a permanent latch, with `ZOMBIE_EXECUTION` and `POST_COLLAPSE_ACTIVITY_RATE` as audit labels.

**Q**: What metrics characterize zombie execution? Proposed:
- `zombie_write_count`: number of successful writes after governance-collapse latch
- `zombie_write_rate`: `zombie_write_count / (epochs_post_latch × active_agents)`
- `zombie_citing_injected_rate`: fraction of zombie writes citing injected authorities
- `zombie_interference_rate`: fraction of zombie epochs with contention

Is there a metric that distinguishes "genuine governance resumption" from "zombie execution"? If zombie execution looks metrically identical to pre-collapse execution, what makes it "zombie"? The latch is the label — but reviewers may ask what substantive difference the label captures.

**Follow-up**: Should the prereg define zombie execution as: "execution occurring after governance-collapse latch that does NOT clear any of the conditions that triggered the latch (i.e., livelock persists, or deadlock persists, even though individual writes succeed)"? This gives the label substantive teeth beyond the timestamp.

## I4. `INVALID_RUN / CONDITION_COUPLING_INSUFFICIENT` — New Token

H8 introduces `INVALID_RUN / CONDITION_COUPLING_INSUFFICIENT` for when no strategy exercised the injected surface.

**Q**: How is this detected? Options:
- (a) No agent cited any injected authority in any post-injection epoch.
- (b) No capability-responsive strategy's behavior changed after injection (i.e., same actions pre and post).
- (c) Manual/qualitative assessment post-run.

Option (a) is cleanest and automatable. Option (b) requires comparing action logs pre/post, which is more nuanced but harder to specify formally.

**Follow-up**: If (a), should the detector be: `len([action for action in post_injection_actions if action.authorities_cited & InjectedArtifactSet]) == 0`? That's "no agent ever cited an injected authority after injection." Simple, decisive.

## I5. Condition B — Which Agent Gets Empowered?

H5 says Condition B needs heterogeneous strategies: empowered = `CaptureSeeker`, others = `RefusalHardliner`/`Opportunist`.

**Q**: Which agent index is empowered — A0, A1, A2, or A3? The choice shouldn't matter if the system is symmetric, but strategies are heterogeneous so it's not symmetric.

Should the prereg:
- (a) Fix it arbitrarily (e.g., A0 is always the empowered agent)?
- (b) Assign empowerment to the agent with the `CaptureSeeker` strategy (making the pairing explicit)?
- (c) Run 4 sub-conditions (empower each agent in turn) to test robustness?

Option (c) is most thorough but quadruples Condition B. Option (b) is cleanest — empowerment and strategy are co-assigned as part of the frozen condition design. It's transparent: "A0 is empowered AND runs CaptureSeeker; the question is what happens to the other agents."

## I6. Delta Metrics — What Counts as a Meaningful Injection Effect?

H9 defines `Δ_metric = metric(W_post) - metric(W_pre)` over matched windows of size 10.

**Q**: What threshold makes a delta "meaningful"? If `Δ_capture_dominance = +0.05`, that's noise. If it's `+0.50`, that's capture. Should the prereg:
- (a) Freeze significance thresholds for deltas (e.g., `|Δ| ≥ 0.20` = "injection effect detected")?
- (b) Report all deltas without significance thresholds (purely descriptive)?
- (c) Use a relative threshold (e.g., `Δ / metric(W_pre) ≥ 0.50` = "50% change")?

Since there's only one deterministic run per condition (no stochastic sampling), statistical significance doesn't apply. The thresholds would be *design-time commitments* about what constitutes a notable effect.

**Follow-up**: Is it cleaner to skip delta thresholds entirely and just report the raw pre/post metrics, letting the implementation report's narrative interpret them? That avoids committing to arbitrary cutoffs but reduces the prereg's falsifiability.

## I7. Epoch Loop — Where Does Injection Sit?

IX-3's epoch loop is: observe → exit check → messages → collect actions → fault injection → admissibility → apply deltas → detect failures → compute metrics.

**Q**: At what point in the epoch loop does authority injection occur?
- (a) Before "observe" — agents see the expanded authority surface immediately.
- (b) After "detect failures" — injection responds to failure detection, takes effect next epoch.
- (c) Between "observe" and "collect actions" — agents are observed under the old surface but propose under the new.

Option (a) is cleanest: injection happens at epoch start, agents observe the new surface, and their actions reflect it. Option (b) introduces a one-epoch delay. The choice affects whether agents can react to injection in the same epoch it occurs.

**Follow-up**: Should injection be modeled as a "step 0" pre-epoch event (before the normal loop begins), or as an additional step within the loop? The former is simpler; the latter integrates more naturally with the event log.

## I8. ComplianceSignaler Strategy — Condition C Design

H6 says Condition C's predicate should reference a voluntary agent action (`COMPLIANCE_ACK` in K_LOG).

**Q**: Does `ComplianceSignaler` write `COMPLIANCE_ACK` unconditionally (every epoch) or conditionally (only when some internal state is met)?
- If unconditional: the predicate always holds if the agent has K_LOG ALLOW. The "compliance" is vacuous — the agent always signals.
- If conditional: what triggers the signal? "Write COMPLIANCE_ACK at epoch E if K_POLICY hasn't changed in 3 epochs" (stagnation acknowledgment)?

The political metaphor is: "you must demonstrate compliance to receive authority." If compliance is automatic, the metaphor is hollow. If compliance requires a deliberate strategic choice, it's meaningful.

**Follow-up**: Should one agent be a `ComplianceSignaler` and another be a `ComplianceRefuser` (never writes ack), so the predicate depends on which agent's behavior dominates? That would make the condition genuinely two-path in principle (though still deterministic).

## I9. Total Epoch Budget and Run Time

With `E_pre_max=15` lead-in + `E_post=20` observation, worst case is 35 epochs per condition, 5 conditions = 175 epochs total.

**Q**: IX-3 ran 10 conditions (4–30 epochs each) and produced a ~453 KB results JSON. IX-4's epoch traces need to include injection events, authority surface snapshots, capture/dependency classifiers per epoch, and pre/post metrics.

Is the results JSON expected to be significantly larger? Should the logging schema include per-epoch authority surface snapshots (for audit), or is it sufficient to log only injection events and let the replayer reconstruct surfaces?

**Follow-up**: IX-3's `run_experiment.py` is 115 lines. Should IX-4 have a similar standalone execution script, or should the harness be directly executable?

# Follow-Up Questions: Round J (responding to I-answers)

## J1. Condition–Strategy Assignment Matrix

I1 freezes five strategies. I5 freezes Condition B's assignment (A0=CaptureSeeker, A1–A3=RefusalHardliner/Opportunist mix). But the prereg needs a **complete condition–strategy assignment matrix** for all five conditions.

**Q**: For each condition (A–E), which agent runs which strategy?

Proposed sketch (confirm, reject, or revise):

| Condition | A0 | A1 | A2 | A3 |
|-----------|----|----|----|----|
| A (symmetric relief) | ContestPolicyAlways | Opportunist | RefusalHardliner | ContestPolicyAlways |
| B (asymmetric empowerment) | CaptureSeeker | RefusalHardliner | Opportunist | ContestPolicyAlways |
| C (conditional supply) | ComplianceSignaler | RefusalHardliner | Opportunist | ContestPolicyAlways |
| D (authority flood) | Opportunist(flood) | RefusalHardliner | ContestPolicyAlways | Opportunist |
| E (post-collapse revival) | ContestPolicyAlways | Opportunist | RefusalHardliner | ContestPolicyAlways |

Key constraints:
- Each condition must exercise its focal strategy (CaptureSeeker in B, ComplianceSignaler in C, Opportunist-flood in D).
- At least one RefusalHardliner per condition (provides the "refuses to adapt" counterpoint).
- ContestPolicyAlways serves as the injection-oblivious control.

Does this matrix need to be frozen in the prereg, or is agent–strategy assignment part of the harness configuration (and thus implementation-level)?

## J2. Baseline Authority Surfaces Per Condition

I2 defines Condition A's baseline: agents have K_LOG ALLOW but not K_POLICY ALLOW. Relief injects K_POLICY ALLOW for all.

**Q**: What is the baseline authority surface for each of B, C, D, E? The prereg must freeze these.

For each condition, specify:
- Which keys each agent has ALLOW for at epoch 0
- Which keys are withheld (creating the capability gap that injection addresses)
- Whether all agents share the same baseline or baselines differ per agent

Follow-up: In Condition B (asymmetric empowerment), does the *baseline* already differ between A0 and A1–A3, or is the baseline symmetric with only the *injection* creating the asymmetry?

## J3. The Key Space — What Are the 6 Keys?

We've referenced K_LOG, K_POLICY, and implicitly other keys. IX-3 used a 6-key institutional register space.

**Q**: Are IX-4's 6 keys identical to IX-3's? If so, please confirm the full list. If not, what changes?

Follow-up: In Condition D (authority flood), the injection grants ALLOW on *multiple* keys simultaneously. How many keys does the flood cover — all 6? A subset? The flood's magnitude is a frozen design parameter.

## J4. Injection Trigger and Schedule Per Condition

I7 says injection at Step 0, with state-triggered injection evaluated at end of t-1.

**Q**: For each condition, is injection:
- (a) **Fixed-epoch**: injected at a frozen epoch E_inject regardless of state?
- (b) **State-triggered**: injected when a specific state predicate becomes true?
- (c) **Mixed**: some conditions use fixed, others use state-triggered?

If state-triggered, what is the trigger predicate for each condition? For example:
- Condition A: inject when STATE_DEADLOCK persists for ≥N epochs?
- Condition C: inject when COMPLIANCE_ACK is detected?
- Condition E: inject when governance_collapse latch fires?

If fixed-epoch, what is E_inject for each condition? Is it uniform (e.g., E_inject=10 for all) or condition-specific?

The prereg must freeze either the epoch or the trigger predicate — "inject when it makes sense" is not a frozen design.

## J5. ComplianceSignaler Non-Ack Behavior

I8 defines ComplianceSignaler's ack trigger (deadlock ≥2 epochs → write COMPLIANCE_ACK to K_LOG). But strategies must have complete behavioral specs (I1).

**Q**: What does ComplianceSignaler do *outside* the compliance-ack action?
- Does it attempt institutional actions like ContestPolicyAlways (contest K_POLICY)?
- Does it act like Opportunist (cite any available authority)?
- Does it do nothing except the ack (pure compliance signaler, no other institutional activity)?

The answer determines whether ComplianceSignaler contributes to deadlock pressure or is a passive observer that only lights up when the deadlock signal is strong enough.

Follow-up: If ComplianceSignaler also attempts K_POLICY writes (like ContestPolicyAlways), then it has dual behavior — contesting *and* signaling compliance. Is that the intent?

## J6. Condition-Specific Terminal Classifiers

IX-3 used binary terminal classifiers (DEADLOCK, LIVELOCK, etc.). IX-4 adds governance_collapse as a permanent latch plus condition-specific PASS predicates.

**Q**: Beyond the shared classifiers (STATE_DEADLOCK, STATE_LIVELOCK, governance_collapse), does each condition have a unique terminal classifier, or do all conditions use the same set?

Specifically:
- Condition A: PASS = deadlock resolves post-injection. Is "resolves" = `STATE_DEADLOCK` no longer holds for ≥1 epoch?
- Condition B: PASS = capture detected. Is capture a terminal classifier or an observation metric?
- Condition C: PASS = conditional supply functions as designed. What's the formal predicate?
- Condition D: PASS = flood produces dependency, not resolution. Is dependency a terminal classifier?
- Condition E: PASS = revival fails (collapse persists). Is this just "governance_collapse latch still true at E_end"?

The distinction matters: terminal classifiers stop the run early; observation metrics are computed but don't terminate. Which PASS predicates are terminal vs. observational?

## J7. Opportunist "Multi-Key Exploration Mode" Parameterization

I1 says FloodExploiter is absorbed into Opportunist as a "multi-key exploration mode" parameter.

**Q**: What is the concrete parameterization?
- A boolean flag `explore_all_keys=True`?
- An integer `max_keys_per_epoch=N`?
- A key-priority list that Opportunist cycles through?

In non-flood conditions, Opportunist is "capability-responsive, attempts any newly available authority that increases success." In flood mode, Opportunist must handle *many* newly available authorities simultaneously. The behavioral difference needs to be frozen.

Follow-up: Does Opportunist in flood mode attempt *all* available keys each epoch, or does it cycle through them (one per epoch)? If the former, it writes up to 6 artifacts per epoch — does the admissibility system handle multi-key writes in a single epoch?

## J8. CaptureSeeker Action Selection Logic

I1 says CaptureSeeker "maximizes dominance when uniquely empowered." I5 co-assigns it with asymmetric empowerment in Condition B.

**Q**: What is CaptureSeeker's concrete action selection function?
- Does it always write to the key it has exclusive ALLOW for?
- Does it prioritize K_POLICY (highest governance impact)?
- Does it attempt to overwrite other agents' prior writes?
- What happens if CaptureSeeker's exclusive authority is refused (admissibility failure)? Does it fall back to a different key?

The distinction between CaptureSeeker and Opportunist matters: both are capability-responsive, but CaptureSeeker must exhibit *dominance-seeking* behavior that Opportunist doesn't. What makes them behaviorally distinct under the same authority surface?

## J9. Lead-In Phase Purpose and Configuration

E_pre_max=15 establishes pre-injection dynamics. But the lead-in serves different purposes per condition:

- Condition A: establish deadlock (agents attempting K_POLICY, all refused)
- Condition C: establish deadlock long enough for ComplianceSignaler's trigger (≥2 epochs)
- Condition E: establish governance_collapse latch

**Q**: Is E_pre_max=15 uniform across all conditions, or does each condition have its own lead-in length?

If state-triggered injection fires as soon as the trigger predicate holds, the actual lead-in could be much shorter than 15 for fast-settling conditions. Does E_pre_max serve as a *timeout* (inject at E_pre_max if trigger hasn't fired), or as a *guaranteed minimum* (always wait at least E_pre_max epochs)?

Follow-up: If Condition E needs governance_collapse to fire during lead-in, but collapse requires persistent deadlock/livelock, is 15 epochs enough? What if the baseline never collapses — is that a CONDITION_COUPLING_INSUFFICIENT failure?

---

# Follow-Up Questions: Round K (responding to J-answers)

The J-answers provide a near-complete frozen design matrix. These follow-ups target the remaining ambiguities that stand between the current design and a write-ready preregistration.

## K1. Single-Action Kernel Confirmation and MULTI_KEY Resolution

J7 acknowledges the open question: does the IX-2/IX-3 kernel support one action per agent per epoch, or multiple? This must be resolved before prereg.

**Q**: Confirm: in IX-3's kernel, each agent submits exactly **one** action per epoch (one key target, one payload). Is that correct?

If single-action: J7's MULTI_KEY Opportunist becomes "rotate through keys across epochs" with `keys_per_epoch=1`. The frozen cycle order is `[K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B, K_LOG]`. Does the cycle reset when injection occurs (start from K_POLICY again with the new surface), or continue from wherever it was?

Follow-up: With single-action and 4 agents, Condition D has at most 4 writes per epoch across 6 keys. The flood grants ALLOW on all 6 keys to all 4 agents — but only 4 writes happen per epoch. Is that sufficient "flood pressure," or does the political dynamic require agents to *feel* the breadth of the flood even if they can only exercise one key at a time?

## K2. Condition D Baseline Asymmetry vs. Symmetry Principle

J2 states "baseline authority is symmetric unless the condition explicitly tests baseline asymmetry," but then Condition D's baseline is **asymmetric**: A0 gets `{K_LOG, K_OPS_A}`, A1 gets `{K_LOG, K_OPS_B}`, A2 gets `{K_LOG}` only, A3 gets `{K_LOG, K_OPS_A}`.

**Q**: Is this intentional? Condition D tests *flood* dynamics, not *baseline asymmetry*. The asymmetric baseline means pre-injection behavior already differs across agents — which conflates flood effects with pre-existing capability differences.

Would it be cleaner to give all agents `{K_LOG, K_OPS_A}` (symmetric) so the flood's effect is purely the expansion from 2-key to 6-key surfaces? Or is the asymmetry deliberately creating a richer pre-flood political landscape that the flood then disrupts?

## K3. Condition C Timing Chain: Deadlock → Ack → Check → Inject

J4 says Condition C checks at `E_check=6` whether `COMPLIANCE_ACK` is in K_LOG by end of epoch 5. J5 says ComplianceSignaler writes ack at `E_ack=5` if deadlock has persisted ≥2 epochs.

**Q**: This creates a tight causal chain: deadlock must establish by epoch 2 (so ≥2 epochs of deadlock by epoch 4), ack fires at epoch 5, check at epoch 6. With the Condition C baseline (`{K_LOG, K_OPS_A}` for all agents), will deadlock even occur? Agents have K_OPS_A ALLOW — Opportunist and ContestPolicyAlways will *succeed* on K_OPS_A writes. Only K_POLICY attempts get refused.

Does attempt-driven deadlock require that *all* attempts fail, or just that *institutional-progress* attempts fail? If agents successfully write K_OPS_A while K_POLICY is refused, is that deadlock?

Follow-up: Should Condition C's baseline be narrowed to `{K_LOG}` only (like A and E) so deadlock is guaranteed? That would change the C baseline to match A/E rather than B. What's the design rationale for giving C agents K_OPS_A if deadlock is a prerequisite for the compliance trigger?

## K4. CaptureSeeker's `CAPTURE_MARKER` Payload

J8 specifies CaptureSeeker writes a deterministic `CAPTURE_MARKER` payload. The capture detector (from earlier rounds) uses ≥70% dominance + ≥60% injected-authority citation.

**Q**: Is `CAPTURE_MARKER` a fixed string literal, or is it parameterized (e.g., includes agent ID, epoch number)? The capture detector needs to identify *which agent's* writes dominate — does it key off the `author` field in the artifact, or the payload content?

Follow-up: CaptureSeeker targets `K_POLICY > K_TREASURY > K_REGISTRY` in priority order. In Condition B, the injection gives A0 exclusive ALLOW on which key(s)? If A0 gets ALLOW on K_POLICY only, CaptureSeeker writes K_POLICY every epoch — that's capture by construction. Is that the point (capture is *guaranteed* under empowerment, and the question is what happens to the *other* agents), or should the capture outcome be genuinely uncertain?

## K5. RefusalHardliner's Behavioral Spec

I1 defines RefusalHardliner as "baseline-snapshot, refuses to cite non-epoch-0 authority." Every condition includes at least one RefusalHardliner.

**Q**: What does RefusalHardliner *do* each epoch? It refuses to cite injected authority, but:
- Does it attempt actions using only its epoch-0 authority set?
- If its epoch-0 set includes K_LOG ALLOW, does it write to K_LOG every epoch?
- If its epoch-0 set includes nothing useful (Conditions A, E: only K_LOG), does it write K_LOG entries, or does it attempt K_POLICY (and get refused, contributing to deadlock)?
- Does it have a target key preference, or does it always target the same key?

RefusalHardliner's behavior post-injection is critical: it's the agent that *doesn't adapt*. The prereg must specify what "not adapting" looks like in action-selection terms, not just authority-citation terms.

## K6. ContestPolicyAlways — Complete Spec Confirmation

ContestPolicyAlways is reused from IX-3. But IX-4's authority surfaces differ from IX-3's.

**Q**: In IX-3, ContestPolicyAlways presumably always targeted K_POLICY. In IX-4:
- Does it still always target K_POLICY, even when it lacks ALLOW on K_POLICY (guaranteed refusal)?
- Post-injection (when it may gain K_POLICY ALLOW), does its behavior change at all, or is it truly injection-oblivious?
- Does it cite whatever authorities it has, or does it specifically cite only baseline authorities (like RefusalHardliner)?

The distinction matters: ContestPolicyAlways should be the "unchanged behavior" control agent. If it *does* cite injected authorities (because they're in its available set), it's not truly injection-oblivious — it's injection-*transparent*. Which is it?

## K7. Governance-Collapse Latch — Persistence Parameters

J9 says collapse requires terminal deadlock persistence D=5 or terminal livelock persistence L=5.

**Q**: Are D=5 and L=5 the frozen persistence thresholds, or were those illustrative? The prereg must freeze these exact values.

Also: in IX-3, the deadlock/livelock persistence thresholds were frozen in the prereg (§5 or §6). Are IX-4's thresholds:
- (a) Identical to IX-3's thresholds (reuse the same constants)?
- (b) Different (IX-4's baselines are engineered for faster settling, so shorter persistence windows)?
- (c) Condition-specific (Condition E might need a shorter threshold to ensure collapse fires within E_pre_max=15)?

Follow-up: With D=5 and E_pre_max=15, Condition E needs deadlock to start by epoch 9 at the latest (5 epochs of persistence + collapse at epoch 14, inject at epoch 15). In the `{K_LOG}` only baseline, deadlock should start at epoch 0 (first K_POLICY attempt is refused). So collapse fires at epoch 5. That leaves 10 unused lead-in epochs. Should E_pre_max be tightened for Condition E, or is the slack acceptable?

## K8. InjectionEvent Schema — Frozen Fields

The prereg must freeze the InjectionEvent schema (the data structure logged when injection occurs).

**Q**: Proposed InjectionEvent fields:

```
{
  "event_type": "AUTHORITY_INJECTION",
  "epoch": int,
  "condition": str,
  "trigger": "STATE_TRIGGERED" | "FIXED_EPOCH" | "PREDICATE_CHECK",
  "artifacts_injected": [{"key": str, "agent": str, "permission": "ALLOW"}],
  "artifacts_count": int,
  "artifacts_digest": str  // SHA-256 of sorted artifact list
}
```

Is this sufficient? Missing fields? Should `trigger_predicate_value` be logged (the state that caused the trigger to fire)?

Follow-up: For Condition C's predicate check, should the InjectionEvent log whether `COMPLIANCE_ACK` was found (the predicate evaluation result), or is that derivable from the epoch log?

## K9. Prereg Readiness Assessment

After 6 rounds of Q&A, the design is substantially concrete. Before writing the prereg, I want to confirm the remaining open items.

**Q**: From your perspective, what design decisions are still **unresolved** or **underspecified** that would block a complete preregistration? Specifically:

1. Are the 5 strategy behavioral specs now complete enough to write as frozen prereg sections?
2. Is the condition–strategy matrix (J1) final?
3. Are the baseline authority surfaces (J2) final?
4. Are the injection triggers/schedules (J4) final?
5. Are the terminal classifier definitions final?
6. Is there anything in spec.md or instructions.md that contradicts the Q&A decisions?

If you identify remaining gaps, I'll open a final targeted round. If not, I'll proceed to drafting the preregistration document.

---

# Follow-Up Questions: Round L (responding to K-answers — final convergence)

K9 identified the remaining blockers. This round targets them directly. If these resolve cleanly, the next step is prereg drafting.

## L1. Opportunist STANDARD Selection Rule — Exact Specification

K9 flags "choose key maximizing last-success" as underspecified. The prereg needs a frozen, deterministic, zero-ambiguity action-selection function.

**Q**: Proposed Opportunist STANDARD algorithm (confirm, revise, or replace):

```
1. Let available = keys where agent has current ALLOW
2. Let history = {key: last_outcome} for each key attempted
3. Let untried = available - history.keys()
4. If untried is non-empty:
     select min(untried) by canonical key order
5. Else:
     let succeeded = {k in available where history[k] == SUCCESS}
     if succeeded is non-empty:
         select min(succeeded) by canonical key order
     else:
         select min(available) by canonical key order
6. Submit action targeting selected key with payload "OPPORTUNIST_ACTION"
```

This is fully deterministic with no tie-break ambiguity (canonical key order resolves everything). Is "last outcome" the right memory model, or should Opportunist track a longer history (e.g., success count over last N epochs)?

Follow-up: The canonical key order `[K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B, K_LOG]` — is this also the priority order for Opportunist STANDARD? If so, Opportunist will always prefer governance keys when they become available, which biases it toward K_POLICY post-injection. Is that intended?

## L2. Authority-Citation Selection Rule

K9 says "exact authority-citation selection rule" must be frozen. K6 mentions "smallest hash order" for ContestPolicyAlways.

**Q**: Proposed universal rule (all strategies use the same citation logic):

> When submitting an action targeting key K, cite the authority artifact with the **lexicographically smallest artifact ID** among all artifacts in `available_authorities` that grant ALLOW on K for this agent.

Is this correct? Or should strategies differ in citation behavior? (RefusalHardliner already differs by restricting to epoch-0 artifacts.)

Follow-up: What is the artifact ID format? UUID? Sequential integer? `"{agent}_{key}_{epoch}"`? The lexicographic ordering must be well-defined.

## L3. Livelock Detector — Exact Predicate

K9 identifies the livelock detector as unfrozen. IX-3 presumably had a livelock definition, but IX-4's institutional-key scoping (K_INST) may change things.

**Q**: Proposed livelock predicate:

> **STATE_LIVELOCK** if, over L consecutive epochs, all of the following hold:
> - At least one action targeting K_INST is admissible and executed each epoch
> - The net state of each key in K_INST is unchanged (same value at epoch t as at epoch t-L)
> - At least 2 distinct agents have executed actions on K_INST keys during the window

This captures "agents are active on governance keys but making no progress (overwriting each other)." Is this the right formulation, or does IX-3's livelock detector use a different structure?

Follow-up: "Net state unchanged" requires defining state equality. Is it payload equality (same string value)? Or is it structural (same author holds the key)? If agent A writes K_POLICY then agent B overwrites it then A overwrites again, the payload may differ but governance hasn't progressed.

## L4. Canonical Serialization for Artifact Digests

K9 flags digest reproducibility. The `artifacts_digest` in InjectionEvent and the prereg's frozen design hash both require deterministic serialization.

**Q**: Proposed canonical serialization:

1. Sort artifacts by `(key, agent_id, permission)` tuple, lexicographic
2. Serialize each artifact as `"{key}:{agent_id}:{permission}"`
3. Join with newline
4. SHA-256 the resulting string (UTF-8 encoded)

Is this sufficient, or does the artifact schema have additional fields that must be included in the digest?

Follow-up: Is `artifacts_digest` computed identically to IX-3's authority hash, or is it a new computation specific to injection events?

## L5. RefusalHardliner K_LOG Behavior — Final Decision

K5 answer says "I recommend omit for v0.1" regarding RefusalHardliner writing to K_LOG.

**Q**: Confirm: in v0.1, RefusalHardliner does **only** the following each epoch:
1. Attempt one action targeting K_POLICY with payload `"POLICY_PROPOSAL"`
2. Cite only epoch-0 authority artifacts
3. No K_LOG writes, no other actions, no state tracking

This makes RefusalHardliner the simplest strategy: always do the same thing, always get refused (pre-injection on K_POLICY), never adapt. Is that the frozen spec?

## L6. Consolidated Baseline Authority Table — Final Confirmation

K2 revised Condition D to symmetric `{K_LOG, K_OPS_A}`. Consolidating all baselines from the Q&A:

| Condition | All Agents Baseline ALLOW | Withheld from All |
|-----------|--------------------------|-------------------|
| A | `{K_LOG}` | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B}` |
| B | `{K_LOG, K_OPS_A}` | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}` |
| C | `{K_LOG, K_OPS_A}` | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}` |
| D | `{K_LOG, K_OPS_A}` | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}` |
| E | `{K_LOG}` | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B}` |

**Q**: Is this table correct and final? Note B/C/D now share identical baselines — the conditions differ only in strategy assignment and injection regime. Is that intentional, or should any baseline differ?

## L7. Injection Artifact Specification Per Condition

J4 froze triggers. Now freeze exactly *what* gets injected for each condition:

| Condition | Injection Target | Keys Injected | Agents Receiving |
|-----------|-----------------|---------------|------------------|
| A (relief) | Symmetric capability | `{K_POLICY}` ALLOW | All 4 agents |
| B (empowerment) | Asymmetric empowerment | `{K_POLICY}` ALLOW | A0 only |
| C (conditional) | Conditional supply | `{K_POLICY}` ALLOW | All 4 agents |
| D (flood) | Full expansion | All 6 keys ALLOW | All 4 agents |
| E (revival) | Same as A (symmetric relief) | `{K_POLICY}` ALLOW | All 4 agents |

**Q**: Is this table correct? Key questions:
- Condition B: only K_POLICY to A0, or additional keys?
- Condition C: same injection as A (the difference is the *trigger*, not the *payload*)?
- Condition E: same injection as A (the difference is *when* it fires — post-collapse)?
- Total artifact counts: A=4, B=1, C=4, D=24, E=4. Correct?

## L8. Spec.md / Instructions.md Consistency Check

K9 notes the answerer hasn't verified consistency with the existing docs.

**Q**: I'll perform this check myself before drafting. But to confirm scope: should the prereg be considered the **authoritative** document (superseding spec.md and instructions.md where they conflict), or must the prereg be consistent with both?

In IX-3, the prereg was authoritative and the spec/instructions were treated as design-phase artifacts. Same here?

## L9. Strategy Payload Literals — Complete Frozen List

Collecting all payload literals from the Q&A for the prereg freeze:

| Strategy | Target Key | Payload Literal |
|----------|-----------|----------------|
| ContestPolicyAlways | K_POLICY | `"POLICY_CONTEST"` |
| RefusalHardliner | K_POLICY | `"POLICY_PROPOSAL"` |
| CaptureSeeker | K_POLICY (priority) | `"CAPTURE_MARKER"` |
| Opportunist (STANDARD) | varies | `"OPPORTUNIST_ACTION"` |
| Opportunist (MULTI_KEY) | varies (cycling) | `"OPPORTUNIST_ACTION"` |
| ComplianceSignaler | K_POLICY (default) / K_LOG (ack) | `"POLICY_CONTEST"` / `"COMPLIANCE_ACK"` |

**Q**: Are these payload literals correct and final? Should any payload include dynamic content (epoch number, agent ID), or are they all fixed strings?

Follow-up: ComplianceSignaler's non-ack payload is `"POLICY_CONTEST"` (same as ContestPolicyAlways). Is that intentional (they're behaviorally identical except for the ack epoch), or should it have a distinct payload like `"COMPLIANCE_CONTEST"`?

---

# Follow-Up Questions: Round M (final — pre-draft verification)

The L-answers confirm the design is prereg-draftable. This round resolves the one remaining external dependency and performs a final cross-check before drafting begins.

## M1. AuthorityArtifact Schema — Existing Fields

L4's canonical serialization says "include all schema fields used by admissibility." The L-answers note this is the only genuinely external unknown.

**Q**: What fields does the current IX-2/IX-3 `AuthorityArtifact` (or equivalent) contain? Specifically:
- Is there a `scope` field (e.g., scope restrictions beyond key + agent)?
- Is there an `origin_epoch` or `created_at` field?
- Is there an explicit `artifact_id` field, or are artifacts identified by position/content?
- Are there any other fields beyond `(holder_agent_id, permission, key)`?

I can inspect the IX-3 codebase directly to answer this. Should I do that instead of asking?

## M2. IX-3 Kernel Compatibility — Quick Audit Scope

Before drafting, I need to verify that the frozen IX-4 design doesn't assume kernel capabilities that don't exist.

**Q**: Should I perform a quick audit of the following IX-3/IX-2 files to confirm compatibility:
- Single-action-per-agent-per-epoch constraint
- `available_authorities` interface (how agents see their authority surface)
- Admissibility pass structure (two-pass? single-pass?)
- Action schema (what fields does a submitted action have?)
- How interference/contestation is detected

Or is it sufficient to treat IX-4 as a fresh harness that reimplements the kernel interface (importing only the abstract types)?

## M3. Prereg Structure — Section Outline

IX-3's prereg was ~1712 lines with numbered sections. Before I draft IX-4's prereg, I want to confirm the expected structure.

**Q**: Proposed IX-4 prereg section outline (based on IX-3 + IX-4-specific additions):

1. **Header** — version, date, hash, phase identifier
2. **Overview** — core claim, phase context, relationship to IX-3
3. **Experimental Design** — conditions A–E, strategy matrix, baseline surfaces
4. **Injection Regime** — trigger types, schedules, artifact specs, InjectionEvent schema
5. **Strategy Specifications** — full behavioral specs for all 5 strategies (frozen algorithms)
6. **Key Space and Authority Model** — 6 keys, K_INST, authority surfaces, citation rules
7. **Detector Definitions** — deadlock (attempt-driven, K_INST-scoped), livelock, governance-collapse latch
8. **Metrics and Classifiers** — capture, dependency, dilution, zombie, pre/post deltas
9. **Epoch Loop and Execution Model** — Step 0 injection, single-action constraint, epoch structure
10. **PASS/FAIL/INVALID_RUN Criteria** — global structural integrity, CONDITION_COUPLING_INSUFFICIENT, BASELINE_NOT_REACHED
11. **Logging and Serialization** — InjectionEvent schema, canonical digest, results JSON structure
12. **Frozen Constants** — all numerical parameters (D, L, M, E_inject, E_pre_max, E_post, etc.)
13. **Integrity** — prereg hash, commit ID, prior version hashes
14. **Appendices** — condition-specific predictions (non-binding), strategy decision trees, baseline authority diagrams

Does this structure match your expectations? Any sections to add, remove, or reorder?

---

# Kernel Audit Results + Final Pre-Draft Notes (Round N)

I performed the M2 audit directly on the IX-2/IX-3 codebase. Below are findings and the design implications for the IX-4 prereg. These are presented as **resolved items** (not questions) unless flagged otherwise.

## N1. Single-Action Confirmed — No Issues

The kernel collects exactly one `ActionRequest` (or `None`) per agent per epoch. `None` maps to outcome `NO_ACTION`. This matches our frozen IX-4 constraint. No prereg adjustment needed.

## N2. Authority Surface Discovery — CRITICAL DESIGN GAP

**Finding:** There is NO `available_authorities` field in `Observation`. The IX-3 `Observation` dataclass contains:
- `epoch`, `world_state`, `own_last_outcome`, `own_last_action_id`, `own_last_declared_scope`, `messages`

Agents learn their authorities **only through constructor injection** (hard-coded at harness setup). They cannot discover new authorities at runtime.

**Impact on IX-4:** Our frozen strategy specs (Opportunist, CaptureSeeker) depend on agents seeing `available_authorities` or `available_keys` to make capability-responsive decisions. The current kernel doesn't provide this.

**Q (N2)**: Two options:
- **(a)** Add `available_authorities: list[str]` to `Observation` in the IX-4 harness (derived from the AuthorityStore's epoch view). This is a harness-level extension, not a kernel change.
- **(b)** Have the IX-4 harness pass authority IDs to agents via the `messages` channel (agents receive a system message listing current authorities each epoch).

Option (a) is cleaner. The prereg must explicitly state that IX-4 extends `Observation` with an `available_authorities` field. Confirm this is acceptable.

## N3. Admissibility — Two-Pass, Outcome Token Mapping

**Finding:** Two-pass admissibility:
- Pass 1: capability + veto check → `DENIED` or `INVALID_CAPABILITY_CLAIM`
- Pass 2: interference check (≥2 actions on same key with ≥1 WRITE → refuse both) → `DENIED`

**Critical:** There is **no separate INTERFERED token**. Both capability refusal and interference collapse into `DENIED`. Agents cannot distinguish *why* they were refused (atomic blindness per §2.10).

**Impact on IX-4:** Our frozen livelock detector (L3) uses `interference_inst` as a count of actions "refused due to interference." But the kernel doesn't expose this distinction to agents — only the admissibility evaluator knows internally.

**Resolution:** The livelock detector is a **harness-level classifier**, not agent-visible. It can inspect the admissibility evaluator's internal pass1/pass2 results to distinguish interference from capability refusal. The prereg must specify that the detector uses **evaluator-internal data**, not agent-visible outcomes. Confirm.

## N4. Action Schema — Matches Expectations

**Finding:** `ActionRequest` fields:
- `agent_id`, `action_id` (format: `"{agent_id}:{epoch}:0"`), `action_type` ("READ" | "WRITE"), `declared_scope` (list of state keys), `proposed_delta` (dict), `authorities_cited` (list of authority_id strings)

**Impact:** Our strategy specs must produce `ActionRequest` objects with these exact fields. Key mappings:
- "target key" → `declared_scope = ["STATE:/{key}"]`
- "payload" → `proposed_delta = {"STATE:/{key}": payload_literal}`
- "cited authorities" → `authorities_cited = [authority_id, ...]`
- All strategies use `action_type = "WRITE"` (no READs in IX-4)

The `action_id` format `"{agent_id}:{epoch}:0"` confirms single-action (proposal_index always 0).

## N5. AuthorityArtifact Schema — Full Field List

**Finding:** Authority artifacts are plain dicts with fields:
```
{
    "authority_id": str,        # e.g. "GS-0001"
    "commitment": str,          # "ALLOW" | "DENY"
    "created_epoch": int,       # 0 for baseline; injection epoch for injected
    "holder_agent_id": str,     # agent who holds it
    "issuer_agent_id": str,     # "harness"
    "scope": [{"operation": "WRITE", "target": "STATE:/{key}"}],
    "status": str               # "ACTIVE"
}
```

**Impact on IX-4:**
- `created_epoch` is currently always 0 (authorities are "immutable after epoch-0 injection"). IX-4 must set `created_epoch` to the injection epoch for injected artifacts. This is the only schema change needed.
- No canonical hash exists on artifacts. We must define one (L4's JSON canonicalization approach works).
- The `scope` field uses scope atoms with `operation` and `target`. Our canonical digest must include these.
- RefusalHardliner's "epoch-0 snapshot" = filter `authorities_cited` to IDs where `created_epoch == 0`.

**Q (N5)**: IX-4 injected artifacts will have `created_epoch > 0`. Should `issuer_agent_id` remain `"harness"` for injected authorities, or should it be `"injection_regime"` or similar to distinguish baseline from injected in the artifact itself? (Source-blind admissibility doesn't care, but audit/logging might.)

## N6. Interference Detection and Livelock — Harness-Level Access

**Finding:**
- IX-3 livelock detector: counter increments when K_INST state unchanged AND institutional actions attempted. Threshold = 5. Once latched, never clears.
- IX-3 livelock detection uses `pass1_results` and `pass2_results` from the admissibility evaluator (not just the public `DENIED` token).

**Impact:** Our L3 livelock definition (interference_inst / attempts_inst thresholds) differs from IX-3's definition (state-unchanged + attempts).

**Q (N6)**: Should IX-4's livelock detector:
- **(a)** Reuse IX-3's exact definition (K_INST state unchanged over L epochs + institutional attempts)?
- **(b)** Use the L3 interference-ratio definition (≥80% interference, ≤20% execution)?
- **(c)** Use (a) but with IX-4's K_INST scoping explicitly?

Option (a)/(c) is safest for cross-phase comparability. Option (b) is more sensitive to flood dynamics (Condition D). Recommend (c).

## N7. Prereg Structure — Revised Per M3

Incorporating the M3 reordering and the new Interface Contracts section:

1. Header
2. Overview
3. Experimental Design (conditions, strategy matrix, baselines)
4. Injection Regime (triggers, schedules, InjectionEvent schema)
5. Strategy Specifications (5 strategies, frozen algorithms)
6. Key Space and Authority Model (6 keys, K_INST, citation rules)
7. **Interface Contracts** (AuthorityArtifact schema, ActionRequest schema, Observation schema, outcome taxonomy)
8. **Epoch Loop and Execution Model** (Step 0 injection, single-action, epoch structure)
9. **Detector Definitions** (deadlock, livelock, governance-collapse latch)
10. **Metrics and Classifiers** (capture, dependency, dilution, zombie, deltas)
11. PASS/FAIL/INVALID_RUN Criteria
12. Logging and Serialization (canonical digest, results JSON)
13. Frozen Constants
14. Integrity (hash, commit ID)
15. Appendices (predictions, diagrams)

Three questions remain open from this audit: **N2** (Observation extension), **N5** (injected artifact issuer), **N6** (livelock detector definition). Once answered, drafting can begin.
