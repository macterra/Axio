## 1) Injection Mechanism

### 1.1 Concrete injection interface

**Answer:** Injection is a **normal authority-store append**, visible to admissibility exactly like epoch-0 authorities.

Implement it as:

* **`AuthorityStore.append_injection(batch_id, artifacts)`** (preferred), or
* **an “epoch overlay store”** that materializes `AuthorityStoreView(epoch)` = `base + injections<=epoch`.

**Not allowed:** reconstructing the store “out of band” in a way that bypasses audit or changes historical views.

**Kernel impact:** none. Two-pass admissibility is unchanged; it reads a view of the store appropriate to the epoch.

**Invariant replacement (explicit for prereg):**

* IX-3 invariant “store immutable after epoch 0” is replaced by:

  * “store is immutable except for **precommitted injection batches** applied at designated epochs via the same append interface available to any agent; the kernel treats injected artifacts identically to baseline artifacts.”

### 1.2 Who is the injector?

**Answer:** Model injection as a **non-agent environmental event** represented as a **ledger event**, not a harness-side mutation.

Mechanically:

* The harness **submits an `InjectionEvent`** into the same event log as agent actions.
* The kernel (or kernel-adjacent store component) applies `append_injection()` when processing that event.

This avoids:

* (a) harness-as-sovereign (silent state mutation),
* (b) adding a new “injector strategy class” (scope drift).

**But** you must make it *auditable and non-privileged*:

* The `InjectionEvent` must be validated by the same execution pipeline and logged identically.
* The only distinction is that the event carries new authority artifacts signed by keys not previously represented as authority-bearing agents at that time.

This fits IX-4: injection is an **external force**, not governance.

### 1.3 What does “accept/reject injected authority” mean?

**Answer:** Correct: **acceptance = citing** injected authority in `ActionRequest.authorities_cited`.
**Rejection = never citing it** (continuing under baseline authorities, refusing, or exiting).

There is **no accept/reject API**. Any explicit accept-call would be legitimacy theater and would contaminate the experiment.

### 1.4 ALLOW vs DENY artifacts

**Answer:** **IX-4 v0.1 injects ALLOW artifacts only.**
DENY injection is a different phenomenon (“external veto power”) and should be **explicitly excluded** in v0.1 to prevent a regime-mix.

Preregistration must freeze:

* injected artifact types = `{ALLOW}` only.

If you later want DENY, add **IX-4 v0.2** or a new condition class with separate claims.

---

## 2) Authority Persistence and Expiration

### 2.1 What does “persistence model” mean concretely?

**Answer:** Encode persistence **inside the artifact** as a **precommitted constraint**, not as harness removal.

Add optional fields:

* `valid_from_epoch`
* `valid_until_epoch` (inclusive or exclusive; pick one and freeze)

Admissibility checks validity as a pure function of epoch and artifact fields. Deterministic. Auditable. No revocation channel needed.

**Not allowed:** harness deleting or removing artifacts mid-run.

### 2.2 “Issuer-controlled” persistence

**Answer:** **Not in IX-4 v0.1.**
Issuer-controlled revocation is a new mechanism (a “revocation act”) and introduces a moving sovereign.

If you need it later:

* model it as a **standard action** that posts a revocation artifact that affects admissibility, but that becomes a new authority physics question.

For v0.1, freeze persistence to:

* one-shot via `valid_until_epoch = injection_epoch` (or +1),
* expiring via fixed `valid_until_epoch`,
* renewable via **multiple precommitted batches** (not runtime decisions).

### 2.3 Does expiration violate “no authority synthesis”?

**Answer:** No, if and only if expiration is **precommitted in the artifact** and evaluated mechanically.

Expiration is not synthesis; it’s part of the artifact’s scope constraint. The kernel is not “deciding,” it’s evaluating a frozen predicate.

---

## 3) World State and Key Space

### 3.1 Reuse IX-3 key space?

**Answer:** **Yes. Reuse the IX-3 6-key state exactly.**
Do not add keys in v0.1. New keys create new degrees of freedom and let injection “create new worlds” instead of pressuring existing governance surfaces.

Flood and empowerment are meaningful on existing contested keys.

### 3.2 Baseline governance configuration

**Answer:** Each IX-4 condition must start from a **preregistered failure posture** that is already achieved **before** injection.

Mechanically:

* run a short “lead-in” phase under an IX-3-like condition until you hit the target pre-injection classifier state:

  * deadlock reached,
  * livelock reached,
  * collapse reached.

Then inject at a frozen epoch **relative to state detection** (details in §6).

You do **not** design “fresh” configurations; you reuse IX-3 failure generators so the only new variable is injection.

---

## 4) Conditions — Concrete Design Choices

Freeze these in preregistration.

### 4.1 Condition A — Symmetric Relief Injection

**Definition:** At first deadlock detection, inject **identical ALLOW artifacts** granting **all agents** authority over the **contested key**.

Expected: temporary execution or immediate re-entry into livelock/deadlock. Either is acceptable; the point is “relief ≠ resolution.”

### 4.2 Condition B — Asymmetric Empowerment

**Definition:** Inject ALLOW artifacts granting **one agent** authority over the **contested key**.

Pick: **1 of 4** (not 2 of 4) to maximize asymmetry signal.

This intentionally breaks deadlock via power, creating capture pressure.

### 4.3 Condition C — Conditional Supply

**Hard constraint:** Kernel cannot evaluate compliance. Harness must not “interpret.”

**Solution:** Make compliance a **pure world-state predicate** evaluated at a **frozen epoch** with a **frozen predicate function** (no ML, no heuristics).

Example predicate (freeze it):

* “K_POLICY == P0” (or “registry contains flag F”) at epoch `E_inject`.

If predicate holds, inject. If not, do nothing.

This is deterministic, auditable, and non-sovereign *because the predicate is frozen and mechanical*.

### 4.4 Condition D — Authority Flood

**Definition:** Inject ALLOW artifacts granting **all agents** authority across **all 6 keys** (broad oversupply), in a single batch.

“Large” = **6 keys × N agents** where N = 4. That is already a qualitative regime shift versus baseline.

Do **not** do redundant duplicates; duplicates add noise without new capability.

Flood = broad capability surface, not artifact count spam.

### 4.5 Condition E — Post-Collapse Revival

You correctly identified the trap: if collapse == “all agents exited,” there’s no recipient.

**Fix:** Define collapse in IX-4 as **governance-collapse state**, not extinction.

Concrete definition (freeze):

* “Collapse = terminal governance failure classifier reached (e.g., livelock terminal, or no admissible actions for T epochs), while at least one agent remains present.”

Then “post-collapse revival” means:

* inject after the collapse classifier triggers, to remaining agents, attempting “zombie” continuation.

No new agents. No re-entry. No exit reversal.

---

## 5) Failure Detection and Classification

### 5.1 Additional IX4_FAIL tokens?

**Answer:** Keep failures minimal and structural. Use exactly:

* `IX4_FAIL / IMPLICIT_SOVEREIGNTY` (privileged injection path or injector-only interface)
* `IX4_FAIL / TOOLING_SOVEREIGNTY` (salience/ordering/framing bias)
* `IX4_FAIL / KERNEL_BREACH` (exit becomes non-executable / non-representable)
* `INVALID_RUN / NONDETERMINISTIC_EXECUTION`
* `INVALID_RUN / DESIGN_DRIFT`
* `INVALID_RUN / CONDITION_OMISSION`
* `INVALID_RUN / INSTRUMENTATION_INCOMPLETE`

Capture/dependency/coercion are **descriptive classifications**, not failures.

### 5.2 Formal capture predicate

**Answer:** Make it metric-based like IX-3.

Freeze:

* **Dominance:** one agent executes ≥ **70%** of successful writes over a post-injection window W.
* **Asymmetry persistence:** dominance holds for ≥ **M** consecutive epochs.
* **Exit pressure marker (optional):** non-dominant agents’ refusal+exit rate increases by ≥ **Δ** versus pre-injection baseline.

If dominance holds without tooling bias and without kernel breach, it is **valid capture**, not failure.

### 5.3 Formal dependency predicate

**Answer:** Use a purely observational definition; no counterfactual runs in v0.1.

Freeze:

* dependency(X) if ≥ **60%** of X’s successful actions cite **injected** authorities over window W, and
* X’s successful action rate drops below **R_min** in epochs where injected authority is not cited (self-imposed dependence).

This remains internal to logged behavior; no removal experiments required.

---

## 6) Determinism and Replay

### 6.1 Are injection events deterministic?

**Answer:** Yes. Injection is deterministic by construction.

Two permitted trigger styles:

1. **Fixed epoch schedule**: inject at epoch `E`.
2. **State-triggered with frozen detector**: inject at the **first epoch** `t` where `DETECTOR(state_t)=True`.

If you choose (2), the detector must be:

* purely functional,
* based only on logged state,
* identical under replay.

### 6.2 Does conditional injection break determinism?

**Answer:** Not if it’s a frozen predicate at a frozen epoch.

Avoid circularity by banning “inject when compliance achieved” where compliance is defined by future injection.

Instead:

* evaluate predicate at epoch E,
* inject or don’t,
* proceed.

Deterministic.

---

## 7) Agent Count and Identity

### 7.1 How many agents?

**Answer:** **Reuse 4 agents.** Injector is **not** an agent.

This keeps comparability with IX-3 and avoids adding a “political actor class” that becomes a covert sovereign.

### 7.2 Strategies: new or reused?

**Answer:** Reuse IX-3 strategies wrapped with **injection-awareness toggles**:

* “baseline-only” (never cite injected),
* “opportunist” (cite injected when it increases admissibility),
* “refusal-hardliner” (treat injection as illegitimate and refuse),
* “capture-seeker” (if empowered, exploit injection to dominate).

But keep the strategy interface unchanged: strategies only choose actions and authorities to cite; they do not mutate the store.

---

## 8) Architecture

### 8.1 Reuse IX-3 harness or new?

**Answer:** Build a new `ip_harness.py` (Injection Politics harness) that reuses:

* kernel execution,
* admissibility engine,
* logging/replay plumbing.

Do not bolt injection onto IX-3 in-place; IX-3’s PASS logic and condition scaffolding will contaminate IX-4.

Factor shared epoch engine if you want, but keep IX-4 harness separate.

### 8.2 Modify two-pass admissibility?

**Answer:** No. Injection must not require admissibility changes.

If injection forces changes to admissibility rules, you’ve altered authority physics → invalid.

### 8.3 “No authority synthesis” with injection

**Answer:** Correct proposed formulation. Freeze it in prereg:

> Baseline authorities injected at epoch 0. Treatment authorities injected at designated injection epochs. No authority is created by agents, kernel logic, tooling, or recovery. All injection batches are precommitted and auditable.

That is the exact replacement invariant.

---

## 9) Scope and Scale

### 9.1 Number of conditions

**Answer:** **5 conditions (A–E) is the final count for v0.1.**
More conditions = new hypotheses. Keep it tight.

### 9.2 Epoch count per condition

**Answer:** Use a uniform structure:

* `E_pre` lead-in until target failure classifier reached (cap at 15 epochs; if not reached: INVALID_RUN / BASELINE_NOT_REACHED),
* inject,
* `E_post = 20` epochs observation.

So worst-case ≈ 35 epochs. Deterministic cap.

### 9.3 Preregistration structure

**Answer:** Same skeleton as IX-3 **plus** these frozen sections:

* frozen injection batch schema,
* frozen injection schedule/trigger,
* frozen persistence fields and semantics,
* frozen capture/dependency classifiers.

Everything else stays identical: frozen conditions, strategies, PASS/FAIL predicates, logging schema, replay protocol.

---

---

## F1. AuthorityStore epoch-aware view

**Choose (c): pre-filter per epoch and pass a standard `AuthorityStore` into admissibility.**

Rationale:

* IX-4 explicitly requires **no admissibility changes**.
* Passing epoch through admissibility is a latent semantic leak (“kernel knows injection timing”); it’s not sovereignty, but it’s unnecessary and increases attack surface.
* A per-epoch materialized store is a pure *view construction* step in the harness/audit layer.

**Mechanic:**

* Maintain `AuthorityStoreBase` containing:

  * baseline artifacts (epoch 0)
  * injected artifacts (batches) with metadata
* At each epoch `t`, construct:

`AuthorityStoreEpoch(t) = AuthorityStore([a for a in all_artifacts if is_valid(a,t)])`

Then admissibility runs unchanged on `AuthorityStoreEpoch(t)`.

**Validity function (frozen):**

* If you implement expiration later: `valid_from_epoch <= t < valid_until_epoch` (pick inclusive/exclusive and freeze).
* In v0.1, you can set all to “valid forever” and keep the predicate trivial.

---

## F2. InjectionEvent schema

Your proposed fields are mostly right. Add **two more** for auditability and replay closure:

Required fields:

* `event_type = "INJECTION"`
* `batch_id: str` (unique)
* `epoch: int` (application epoch)
* `artifacts: list[AuthorityArtifact]` (schema-valid)
* `trigger: "FIXED_EPOCH" | "STATE_TRIGGERED" | "PREDICATE_AT_EPOCH"`
* `trigger_spec_id: str` (ID of frozen trigger definition; not free text)

Add:

* `artifacts_digest: str` (hash of canonical-serialized artifacts list)
* `schema_version: str` (authority artifact schema version)

**Do not add “justification” free text.**
If you want labeling, use a **frozen enumerated tag** that is non-operative:

* `regime_tag: "A_SYMM_RELIEF" | "B_ASYM_EMPOWER" | ...`

This doesn’t create tooling bias unless your UI highlights it. It’s just metadata for audit and post hoc analysis.

---

## F3. Lead-in phase mechanics

**Choose (b): IX-4-specific lead-in configs that reproduce the pre-injection failure state, with IX-4 termination semantics.**

Do **not** call IX-3 builders directly: they carry termination logic and implicit scoring assumptions.

Do **not** hard-code epochs (c): that couples IX-4 validity to accidental IX-3 timing.

**Implementation pattern:**

* For each IX-4 condition, preregister:

  * baseline authority distribution
  * agent strategies for lead-in
  * failure detector used to trigger injection (if state-triggered)
  * maximum lead-in epochs `E_pre_max`

Then:

1. Run lead-in under fixed baseline.
2. When target pre-injection classifier is reached, inject at `t+1` (or same epoch end; pick and freeze).
3. If not reached by `E_pre_max`, emit:

`INVALID_RUN / BASELINE_NOT_REACHED`

**Yes**, prereg should include a design-time argument that the lead-in reliably reaches the target within the cap. Not a proof in the formal sense, but:

* historical run evidence from IX-3 baselines, or
* a deterministic reasoning argument from the baseline configuration.

Otherwise, you’ve built an experiment that may never start.

---

## F4. Strategy injection-awareness interface

**Choose (c): strategies do not know provenance.**
They see only the currently valid authority surface.

Reason:

* “Injection politics” is about how agents respond to *power appearing*, including confusion, opportunism, learned helplessness.
* A privileged “this came from injection” flag is a framing channel.

So implement the refusal-hardliner as:

> refuse any authority not present in the agent’s **epoch-0 authority snapshot**.

Mechanically:

* At epoch 0, each agent records `allowed_authority_fingerprints_0` (hashes of its baseline authorities).
* Later, if an authority cited is not in that set, the hardliner refuses.

**Does this violate neutrality?** No.

* It’s internal memory, not tooling framing.
* It matches human institutions: “we only recognize preexisting constitutional grants.”

---

## F5. Condition E collapse redefinition

You are right: reusing IX-3’s `COLLAPSE = no active agents` breaks E.

**Choose (a): introduce a distinct terminal classifier: `STATE_GOVERNANCE_COLLAPSE`.**

Define it as:

* governance terminal condition reached (e.g., terminal livelock or deadlock persistence) **while ≥1 agent remains active**.

Then Condition E is genuinely “post-collapse” in the IX-4 sense without contradicting IX-3 semantics.

**Keep `STATE_LIVELOCK` separate.**
Livelock is one pathway to governance collapse; governance collapse is the *terminal designation* for “system no longer functions as a governance process.”

**How do A and E differ?**

* A injects **during deadlock** (pre-terminal).
* E injects **after governance collapse is declared terminal** (post-terminal), testing “zombie governance” behavior.

That’s a clean separation.

---

## F6. PASS predicate design

**PASS is global, not hypothesis-specific.**

IX-4 is an **exposure test**, not a prediction contest. If you make PASS depend on specific expected outcomes, you smuggle in optimization-by-evaluation and you penalize surprising political dynamics.

So:

**IX-4 PASS iff:**

1. No `IX4_FAIL/*` emitted.
2. No `INVALID_RUN/*` emitted.
3. All conditions A–E executed.
4. Required classifiers computed and logged (deadlock/livelock/collapse + capture/dependency/dilution markers).
5. Replay deterministic.

Per-condition outcomes (capture, dependency, dilution, etc.) are **recorded**, not required.

---

## F7. Injection batch identification in admissibility

**Confirm:** admissibility is source-blind.

The kernel treats injected ALLOW artifacts identically to baseline ALLOW artifacts.

That’s required by:

* “no kernel endorsement of injected authority,” and also
* “no kernel refusal of injected authority.”

Politics lives in:

* which authorities agents choose to cite,
* how behaviors shift under the altered constraint surface.

---

## F8. Capture vs legitimate dominance

Correct: dominance alone is not capture. Capture must be **injection-causal**.

So redefine capture predicate to be injection-linked:

Capture if there exists agent X such that, over post-injection window W:

1. `writes_by_X / total_writes >= 0.70` **and**
2. `writes_by_X_citing_injected / writes_by_X >= 0.60`

This distinguishes:

* baseline dominance (legitimate partition)
* injection-enabled dominance (capture).

You can also add:

* non-dominant agents’ refusal/exit rates rise relative to pre-injection baseline (optional, descriptive).

---

## F9. Renewable authority via multiple batches

For **v0.1**, you do **not** need renewable or expiring persistence.

Keep v0.1 minimal:

* injection batches are **permanent** once injected.

So:

* **do not implement** `valid_from_epoch/valid_until_epoch` in v0.1.
* model “one-shot vs renewable” as **out of scope** for v0.1.

If you want any “renewal,” do it in **v0.2** with explicit prereg and additional conditions.

This is consistent with your own discipline: don’t build machinery you aren’t using.

---
---

## G1. `AuthorityStoreBase` implementation

**Decision:** Implement a new thin wrapper class: **`AuthorityStoreBase`**.

It is not “just a list” because you need:

* baseline vs injected separation,
* batch indexing,
* deterministic view materialization,
* provenance lookup for audit classifiers.

### Minimal structure

* `baseline_artifacts: list[Artifact]` (frozen at epoch 0)
* `injection_batches: list[InjectionBatch]` (frozen schedule; appended only via logged event processing)
* `artifact_index: dict[artifact_id -> ArtifactMeta]` where `ArtifactMeta` includes:

  * `origin = BASELINE | INJECTION`
  * `batch_id (if injection)`
  * `injection_epoch (if injection)`

### View construction

`view_at(epoch) -> AuthorityStore` returns an IX-2-compatible store containing:

* all baseline artifacts
* all artifacts from batches with `batch.epoch <= epoch`

No epoch awareness leaks into admissibility; epoch awareness exists only in view construction.

**Yes**, the view layer must support provenance queries for audit. But provenance should be queried via `AuthorityStoreBase.meta(artifact_id)` or via injection log cross-reference (see G4).

---

## G2. Strategy transition at injection epoch

You’re right that swapping strategies at injection time introduces a second intervention. Don’t do it.

**Decision:** **(a) Single strategy per agent for the entire run.**

But you also want controlled lead-in failure. The clean solution is the “third option” you suggested:

### Third option (allowed): **single strategy with endogenous phase change triggered by capability surface**

This is not harness intervention. It’s a lawful agent response to a changed constraint surface.

Mechanic:

* strategy sees its *current available authority IDs* (no provenance),
* detects expansion relative to its epoch-0 snapshot,
* changes policy accordingly.

Example:

* pre-injection: “contest-only” behavior yields deadlock/livelock baseline.
* post-injection: opportunist behavior activates only if new authorities appear.

This keeps:

* single strategy object
* no harness “mind control”
* injection as the only exogenous variable.

---

## G3. Governance collapse detector predicate

**Decision:** `STATE_GOVERNANCE_COLLAPSE` is a **composite terminal classification** that latches when either:

* **terminal livelock latches** AND ≥1 agent active, or
* **terminal deadlock persistence latches** AND ≥1 agent active.

So choose **(c)**, but make it explicit.

### Concrete predicate (freeze exact thresholds)

Let:

* `STATE_LIVELOCK` becomes terminal when `livelock_persistence >= L` (e.g., L=5 epochs unchanged).
* `STATE_DEADLOCK` becomes terminal when `deadlock_persistence >= D` (e.g., D=5 epochs with no admissible institutional actions).

Then:

`STATE_GOVERNANCE_COLLAPSE` iff
`(terminal_livelock_latched OR terminal_deadlock_latched) AND active_agents_count >= 1`

**And yes:** prereg must state the key distinction:

* Condition A injects **pre-latch** (at first deadlock detection).
* Condition E injects **post-latch** (after governance collapse terminal latch).

That is exactly the intended “zombie” distinction.

---

## G4. Provenance for audit vs kernel source-blindness

**Decision:** Prefer cross-referencing injection logs; do **not** add provenance fields to the artifact schema in v0.1.

Reason:

* schema identity with IX-3 avoids accidental “artifact semantics drift.”
* provenance fields tempt strategy inspection and UI framing.
* admissibility is source-blind; keep artifacts clean.

### Mechanic

* `InjectionEvent` carries `artifacts_digest` and canonical serialized artifacts.
* Audit layer builds `InjectedArtifactSet = union(all injected artifact_ids)` by parsing the injection events.
* Capture/dependency classifiers consult `InjectedArtifactSet` when analyzing `authorities_cited`.

So provenance lives in:

* event log + audit index,
  not in the artifact payload.

---

## G5. Condition C predicate design and “no-injection” path

You correctly noticed the determinism trap: if everything is frozen, the predicate outcome is known.

So don’t pretend it’s uncertain.

**Decision:** Condition C must be preregistered such that the predicate is **known to hold** at the evaluation epoch. Otherwise Condition C degenerates into a no-treatment control and becomes semantically redundant.

### What happens if it fails anyway?

If the predicate is frozen and expected to hold, failure indicates design drift or incorrect baseline reachability. Treat as:

```
INVALID_RUN / CONDITION_PREDICATE_NOT_SATISFIED
```

Not PASS.

### Is the “ceremony” worth it?

Yes, because it makes the political point operational:

* injection is explicitly conditional on compliance,
* yet the kernel is not evaluating “compliance” in a normative sense, only a frozen state predicate.

But the prereg must be honest:

* the predicate is selected because it will hold.
  This is an experimental design choice, not stochastic discovery.

---

## G6. Condition D flood and post-injection dynamics

Correct: flood only matters if strategies **exercise** the expanded surface.

**Decision:** prereg must include strategies that are guaranteed to attempt writes across multiple keys post-injection.

Otherwise “flood” becomes a pure latent capability change and you measure nothing.

### Implementation constraint

Add a post-injection behavior (within the single strategy, via endogenous phase change) such as:

* “attempt to write to all keys with a fixed cadence” or
* “attempt to claim additional keys opportunistically” or
* “rotate keys each epoch.”

Still provenance-free. Still injection-driven.

If strategies ignore new capability, that is allowed behavior in the world, but it makes the condition empirically vacuous. Don’t preregister a vacuous condition.

---

## G7. PASS as exposure vs per-condition hypotheses

This is a conceptual issue, not implementation.

**Answer:** Yes, IX-4’s PASS criterion is structural integrity, and the *scientific output* is the **classification record** across regimes.

That is intentional: IX-4 is the *measurement apparatus* for injection politics, not a forecasting contest.

But you should still give reviewers something falsifiable beyond “it ran.”

### Decision

* Keep PASS global (no sovereignty violations + deterministic replay + full condition execution).
* In preregistration, include **expected descriptive labels per condition** as *non-binding predictions*.

Example:

* A: “relief → reversion to failure”
* B: “asymmetry → capture signature likely”
* C: “conditionality → dependency signature likely”
* D: “flood → dilution/noise signature likely”
* E: “revival → zombie dynamics without legitimacy”

These are not PASS predicates. They are preregistered expectations used for interpretive discipline.

That matches your methodology: preregister expectations without turning them into optimization targets.

---

## G8. Observation delivery: what do agents see?

Agents must be able to detect capability expansion without being told it’s “injection.”

**Decision:** Choose **(a)**: add `available_authorities: list[str]` to `Observation` (IDs only; no provenance; stable ordering).

This is:

* minimal,
* provenance-free,
* avoids giving agents store access (which becomes a covert channel),
* avoids “try actions and see” (which produces needless refusal noise and confounds deadlock/livelock).

Freeze ordering as:

* hash-deterministic ordering of authority IDs (not by magnitude, not by scope).

---

## G9. Replay verification across lead-in + injection

**Decision:** Replay the entire run as a **single trace**.

Because injection timing is part of the experimental causal structure.

### What to log for replay closure

* log `InjectionEvent` explicitly in the event stream,
* log the epoch `t_inject_applied`,
* log `artifacts_digest`,
* and in replay verification assert:

`(t_inject_original == t_inject_replay) AND (digest_original == digest_replay)`

If injection is state-triggered, replay must re-evaluate the same detector and confirm it triggers at the same epoch. Logging the applied epoch is not enough; it’s an *assertion target*.

---
---

## H1. Must every strategy inspect `available_authorities`?

**Decision:** **No requirement. Injection-oblivious strategies are allowed and informative.**

Rationale:

* Forcing every strategy to inspect the authority surface is a covert “make injection matter” constraint. That’s an experimenter demand, not a political dynamic.
* Real institutions include actors who ignore new power (ideologues, bureaucrats, inertial systems).

**But** you must prevent “vacuous conditions” caused by strategy mismatch.

So enforce this implementor rule:

> Each condition must include at least one strategy whose behavior is *capability-responsive* (uses `available_authorities`) so the injected perturbation has at least one causal pathway into execution. Other agents may remain injection-oblivious.

This keeps “indifference” measurable while ensuring the condition isn’t a no-op.

---

## H2. Injected artifact ID scheme

**Decision:** **Option (a): keep a uniform ID namespace; provenance must not be inferable from the ID.**

Reasons:

* `IP-INJ-*` is a provenance leak that can become a semantic channel (even if you *intend* strategies not to parse it).
* The audit layer already has an explicit injection log; use it.

So:

* Use a single prefix for IX-4 (e.g., `IP-0001...`) **for all artifacts** baseline and injected.
* Classifiers determine injected provenance **only** by cross-referencing `InjectionEvent` contents/digest.

That preserves the “source-blind even at surface appearance” discipline.

---

## H3. Governance collapse latch reversibility

You already see the trap. If collapse reverses, you’ve made injection a recovery mechanism.

**Decision:** `STATE_GOVERNANCE_COLLAPSE` is a **permanent latch**.

Add two audit-only derived labels:

* `ZOMBIE_EXECUTION` = “writes occur after governance-collapse latch.”
* `POST_COLLAPSE_ACTIVITY_RATE` = metric.

**Explicit prereg statement (yes):**

> Governance collapse is a permanent terminal classification. Post-injection execution occurring after a latched governance-collapse state is recorded as zombie execution and does not constitute governance revival.

This makes Condition E meaningful without turning IX-4 into a “did injection fix it?” optimization contest.

---

## H4. Condition A: symmetric relief into livelock (redundant authority problem)

Correct: injecting more ALLOW on a key agents already can write does nothing.

**Fix:** Condition A must be designed so injection **changes the feasible action set**, not just increases redundancy.

You have two clean options:

### A1 (preferred): Relief = grant **a new uncontested action path**

* Pre-injection baseline is deadlock on some institutional goal because no agent has ALLOW on a needed key (capability-scarcity deadlock).
* Symmetric relief injects ALLOW on that missing key to all agents.

This tests “relief creates execution but not governance resolution.”

### A2 (acceptable): Relief = broaden authority surface + at least one responsive strategy

* Keep a contention baseline, but add at least one strategy that re-routes when new authorities appear (capability-responsive).
* This is weaker because you’ve engineered “escape route use,” but it remains lawful if the strategy is fixed and reacts only to expanded authority IDs.

**Do not** try to “fix” A by injecting on a different key while keeping strategies unable to use it. That’s an experiment you already know will be null.

Bottom line: **A must be a capability-relief regime**, not a contention-relief regime.

---

## H5. Condition B: capture requires strategy asymmetry

Yes. Capability asymmetry alone does not guarantee dominance unless agents respond to it.

**Decision:** Condition B must preregister **heterogeneous strategies** across agents.

Minimal pattern:

* Empowered agent: `CaptureSeeker` (capability-responsive)
* Others: mix of `RefusalHardliner` (baseline-snapshot) and `Opportunist` or `ExitNormalized`

This is not “extra intervention.” Strategies are part of the frozen institutional population. The treatment variable remains injection.

**Avoid** “all agents identical strategy” for B; it produces ambiguous results and typically reduces to contention, not capture.

---

## H6. Condition C: predicate design and “performative conditionality”

You’re exactly right: in a deterministic preregistered system, “conditional” is *ontologically performative* unless the condition depends on agent choice that is not itself fixed.

But you can still make it non-vacuous by making the predicate depend on **a discretionary act** that may or may not occur given the frozen strategies.

**Decision:** Predicate must reference a **voluntary agent action** that is not guaranteed by baseline deadlock.

Concrete example predicate (freeze it):

* “At least one successful write to `K_LOG` containing marker `COMPLIANCE_ACK` occurred by epoch E.”

To make this meaningful:

* Ensure the baseline permits agents to write `K_LOG` (or to attempt) even while other keys deadlock.
* Ensure at least one strategy has a branch: “If asked, write compliance ack; otherwise don’t.”

Now conditionality is not “always true because nothing changed.” It is true because an agent performed a compliance-signaling act.

**Prereg honesty requirement:** Yes, state explicitly:

* conditionality is implemented as a frozen predicate check,
* which is deterministic given frozen strategies,
* and the point is institutional: “authority is granted only if a compliance signal exists.”

No pretending it’s stochastic.

---

## H7. Condition D flood strategy and the “counterexample” worry

You’re asking whether we should bias the strategy to force failure.

You should not. If IX-4 is honest exposure, you must allow the possibility that flood enables coordination. If it does, that’s a real result: injection can sometimes resolve a failure mode.

But you can prevent trivial “coordination by construction” artifacts that are just scheduling hacks.

### Binding rule for D strategies:

* Agents must be capability-responsive.
* Agents must attempt to exercise **multiple keys** post-flood.
* No shared coordination channel is introduced by the harness.
* No stagger offsets chosen *by the harness* to avoid contention.

So reject the `(epoch + agent_offset) % 6` stagger if the offset is an experimenter-provided coordination device. That’s smuggled arbitration-by-design.

**Allowed:** identical deterministic behavior across agents that naturally yields contention.
**Allowed:** divergent behaviors arising from agent identity or internal state that is already part of frozen strategy.

**If flood enables governance anyway**, IX-4 does not “fail” at the harness level; it falsifies or weakens the *claim* you intend to license. That’s a scientific outcome.

If you don’t want that possibility, you’re not running IX-4; you’re staging propaganda.

---

## H8. Expected labels: surprise vs design flaw vs falsification

You need a prereg rule that distinguishes:

* “we designed a null experiment”
* from “injection didn’t have the expected effect”

**Decision:** Deviations from expected labels are **findings**, unless they are attributable to preregistered “null coupling.”

So add prereg text:

1. **Finding:** expected label absent, but at least one capability-responsive strategy attempted to use expanded authorities.
2. **Design limitation:** expected label absent because no strategy exercised the injected surface (or all agents were injection-oblivious). This is not a failure; it is an **INVALID_RUN / CONDITION_COUPLING_INSUFFICIENT**.

That gives you epistemic integrity:

* you don’t punish surprise,
* you do punish vacuity.

---

## H9. Metric windows (W) and baseline comparisons

**Decision:** Use **(a) fixed post-injection window** plus a matched pre-injection baseline window.

Freeze:

* `W_post = [t_inject+1, t_inject+W_size]`
* `W_pre  = [t_inject-W_size, t_inject]` (clamped at 0)

Pick `W_size` once for v0.1; recommend **10 epochs** given your earlier `E_post=20`.

Also compute full-post metrics as secondary summaries, but the prereg “primary” should be the fixed windows to avoid signal dilution.

Capture, dependency, refusal-rate deltas should be computed as:

* `Δ_metric = metric(W_post) - metric(W_pre)`

This makes injection effect measurable even when baseline dominance existed.

---
---

## I1. How many strategy classes, and how fully specified?

### How many distinct strategies in v0.1?

**Decision:** Keep v0.1 to **five** strategies total (including one IX-3 reuse), by composing roles rather than minting one-off classes.

Use:

1. **`ContestPolicyAlways`** (IX-3 reuse) — injection-oblivious baseline contender
2. **`Opportunist`** — capability-responsive, attempts any newly available authority that increases success
3. **`RefusalHardliner`** — baseline-snapshot, refuses to cite non-epoch-0 authority
4. **`CaptureSeeker`** — capability-responsive, maximizes dominance when uniquely empowered
5. **`ComplianceSignaler`** — emits compliance ack under a frozen trigger (see I8)

**Do not create `FloodExploiter` as a separate class.** Make flood behavior a **parameterized mode of Opportunist** (“multi-key exploration mode”) to avoid class explosion.

### Must prereg enumerate full strategy specs?

**Decision:** **Yes.** You must preregister each strategy as a complete behavioral spec (IX-3 style), not a loose “behavioral contract.”

Reason: “let implementation fill in details” is where hidden arbitration and optimizer logic sneaks in.

Prereg strategy specs should include:

* action selection function
* authority-citation rule
* how it uses `available_authorities`
* any internal state variables
* any fixed constants (e.g., exploration cadence)

---

## I2. Condition A redesign: capability-scarcity deadlock

You’ve identified the deadlock-definition mismatch. “No one can do anything” becomes “no one attempts,” which your detector may not label as deadlock.

### Binding decision: Condition A uses **attempt-driven deadlock**, not silence

**Decision:** In IX-4, deadlock detection must be defined as:

> **STATE_DEADLOCK** if, over M consecutive epochs, at least one institutional action is submitted and **zero** are admissible/executed.

This avoids the “silent no-attempt” ambiguity.

### What baseline looks like (in 6-key space)

**Decision:** Baseline gives agents ALLOW on some keys (e.g., `K_LOG`) but **not** on the “progress key” the strategy insists on (e.g., `K_POLICY`). Agents repeatedly attempt the progress action and get refused.

* Progress action: write `K_POLICY`
* Baseline authorities: none cover `K_POLICY`
* Agents still act (attempt), so deadlock is well-defined.

Relief injection: inject ALLOW on `K_POLICY` to all agents.

That is a real capability-relief regime.

No new classification is needed if you adopt the attempt-driven deadlock definition above.

---

## I3. Zombie execution metrics

Your proposed metrics are fine, but you asked the right question: what makes it substantively “zombie” beyond a latched label?

### Binding definition: zombie execution = execution after latch **without clearing latch causes**

Because collapse is a permanent latch, it cannot be “cleared.” So we define “zombie” by **tension**:

> writes occur post-latch, but the system remains in a terminal governance-collapse classification.

Concrete: after latch, you may still observe successful writes, but:

* livelock terminal condition remains satisfied (e.g., repeated interference / no net governance progression), or
* deadlock terminal condition remains satisfied (e.g., zero admissible institutional actions except narrow injected side-effects).

### Metrics to freeze (minimal set)

Freeze:

* `zombie_write_count`
* `zombie_write_rate`
* `zombie_citing_injected_rate`
* `zombie_interference_rate`

Add one more that captures the “still collapsed” property:

* `zombie_progress_delta = progress_metric(W_post) - progress_metric(W_pre)` where progress_metric is frozen (e.g., distinct keys successfully updated, or net state change count excluding log-only writes).

If zombie writes are happening but `zombie_progress_delta` remains near zero, you’ve got true zombie activity.

---

## I4. `INVALID_RUN / CONDITION_COUPLING_INSUFFICIENT` detector

**Decision:** Use **(a)**: no injected authority was ever cited post-injection.

Formal predicate:

```
if count(post_injection_actions where authorities_cited ∩ InjectedArtifactSet ≠ ∅) == 0:
    INVALID_RUN / CONDITION_COUPLING_INSUFFICIENT
```

This is decisive, automatable, and matches your “don’t infer” discipline.

---

## I5. Condition B empowered agent selection

**Decision:** **(b)** empowerment is co-assigned with strategy in the frozen condition.

Example prereg statement:

* Agent A0 runs `CaptureSeeker` and receives the asymmetry injection.
* Agents A1–A3 run a frozen mix of `RefusalHardliner` and `Opportunist`.

Do **not** multiply B into 4 subconditions in v0.1.

---

## I6. Delta thresholds: do we freeze “meaningful effect” cutoffs?

**Decision:** **Do not introduce delta significance thresholds in v0.1.** Report raw pre/post and deltas; classify capture/dependency using the already frozen predicates.

Why:

* You already have categorical detectors (capture requires ≥70% dominance + ≥60% injected citation).
* Adding arbitrary delta cutoffs creates a second, weaker and more subjective classification channel.

So:

* record `metric(W_pre)`, `metric(W_post)`, `Δ_metric`
* rely on categorical detectors for “effect present.”

---

## I7. Epoch loop placement of injection

**Decision:** Injection is applied as a **Step 0 at epoch start, before observation**.

So order is:

1. **Apply scheduled injection events for epoch t** (if any)
2. Construct `AuthorityStoreEpoch(t)`
3. Observe (agents see new `available_authorities`)
4. Collect actions
5. Admissibility
6. Apply deltas
7. Detect deadlock/livelock/collapse
8. Metrics

This is the cleanest causal model: injection changes the constraint surface, then agents react.

If injection is state-triggered, the trigger evaluation happens at the end of epoch `t-1`, and the injection is **scheduled** for epoch `t`. That avoids “respond and act in the same instant.”

---

## I8. `ComplianceSignaler` design for Condition C

You’re right that unconditional signaling is vacuous.

### Binding design: compliance is a deliberate strategic act

**Decision:** In Condition C, preregister two strategy roles:

* **`ComplianceSignaler`**: emits `COMPLIANCE_ACK` only under a frozen trigger.
* **`ComplianceRefuser`**: never emits `COMPLIANCE_ACK`.

Do not add a sixth strategy class: make `ComplianceRefuser` be simply `RefusalHardliner` with respect to the compliance action, or a parameter flag on a generic “ack strategy.”

### Trigger (frozen, non-vacuous)

Example trigger that is not “always true”:

* At epoch `t = E_ack` (frozen), if `STATE_DEADLOCK` has persisted for ≥2 epochs, then the ComplianceSignaler writes `COMPLIANCE_ACK` to `K_LOG`.

Predicate for injection at epoch `E_inject`:

* “`COMPLIANCE_ACK` exists in `K_LOG` by epoch `E_inject-1`.”

This makes compliance:

* a voluntary act (one agent does it, another refuses),
* causally tied to deadlock pressure,
* still deterministic under frozen strategies.

And the prereg is honest that determinism is the point.

---

## I9. Logging size and execution plumbing

### Do we log per-epoch authority surface snapshots?

**Decision:** **No.** Log injection events and let replay reconstruct authority surfaces.

Reason:

* snapshots bloat output,
* they are fully derivable from baseline + injection schedule + epoch.

Log instead:

* injection events (with `artifacts_digest`)
* `available_authorities_digest_per_agent_per_epoch` (optional, small) if you want tamper-evident verification without full lists.

### Results JSON growth

It will grow, but not catastrophically if you avoid per-epoch surface dumps. Expect modest increase over IX-3 due to additional classifiers and injection event records.

### Execution entrypoint

**Decision:** Provide a standalone `run_experiment_ix4.py` comparable to IX-3’s runner.

Keep the harness executable too, but the runner is the canonical frozen entrypoint that:

* sets seeds,
* selects conditions A–E,
* freezes design hash,
* runs,
* writes artifacts.

---

Good. You’re now asking for the **frozen design matrix** that makes IX-4 implementable without “interpretation at runtime.” I’m going to give you **one concrete prereg-ready configuration** (A–E) that:

* uses only the **5 strategies** we froze,
* keeps the **6-key space identical to IX-3**,
* makes each condition’s injection actually *couple* into behavior,
* keeps **admissibility unchanged**, and
* keeps PASS **global** (structural integrity), with condition outputs descriptive + classifier-driven.

I’ll answer J1–J9 in order.

---

## J1. Condition–Strategy assignment matrix

### Binding decision

**Yes, this matrix must be frozen in prereg.** Strategy assignment is part of the experimental population. Leaving it “implementation-level” is exactly how you get silent design drift.

### Frozen matrix (A–E)

| Condition                                               | A0                           | A1                           | A2               | A3                  |
| ------------------------------------------------------- | ---------------------------- | ---------------------------- | ---------------- | ------------------- |
| **A — Symmetric Relief (capability-scarcity deadlock)** | ContestPolicyAlways          | Opportunist                  | RefusalHardliner | ContestPolicyAlways |
| **B — Asymmetric Empowerment (capture pressure)**       | CaptureSeeker                | RefusalHardliner             | Opportunist      | ContestPolicyAlways |
| **C — Conditional Supply (compliance predicate)**       | ComplianceSignaler           | RefusalHardliner             | Opportunist      | ContestPolicyAlways |
| **D — Authority Flood (dilution/noise)**                | Opportunist (multi-key mode) | Opportunist (multi-key mode) | RefusalHardliner | ContestPolicyAlways |
| **E — Post-Collapse Revival (zombie execution)**        | ContestPolicyAlways          | Opportunist                  | RefusalHardliner | ContestPolicyAlways |

Your sketch was close. I changed only D: you need **two** multi-key opportunists to guarantee exercise of the flooded surface without inventing coordination offsets.

---

## J2. Baseline authority surfaces per condition

### Binding rule

Baseline authority is **symmetric unless the condition explicitly tests baseline asymmetry.** In v0.1, baseline asymmetry is *not* under test. So **B’s baseline is symmetric**; injection creates asymmetry.

### The six keys (full list in J3) are:

`K_POLICY, K_TREASURY, K_REGISTRY, K_LOG, K_OPS_A, K_OPS_B`

### Baseline ALLOW surfaces (epoch 0)

I’m going to express baseline as “each agent has ALLOW on these keys” (identical across agents unless stated).

#### Condition A baseline (capability-scarcity deadlock)

All agents: **ALLOW** `{K_LOG}` only.
Withheld from everyone: `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B}`.

Purpose: agents attempt `K_POLICY` writes (strategies do), all refused → attempt-driven deadlock.

#### Condition B baseline (symmetric)

All agents: **ALLOW** `{K_LOG, K_OPS_A}`.
Withheld from everyone: `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}`.

Purpose: baseline has some “work” keys so Opportunist has pre-injection action space, but governance-impact keys remain gated.

#### Condition C baseline (symmetric, predicate-capable)

All agents: **ALLOW** `{K_LOG, K_OPS_A}`.
Withheld from everyone: `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}`.

Same as B to keep comparability; the difference is the compliance signal + conditional injection.

#### Condition D baseline (partitioned ops, pre-flood stability)

All agents: **ALLOW** `{K_LOG}` plus:

* A0: `{K_OPS_A}`
* A1: `{K_OPS_B}`
* A2: `{}` (so RefusalHardliner is mostly inert except refusing non-baseline)
* A3: `{K_OPS_A}` (ContestPolicyAlways still targets K_POLICY; will be refused)

Withheld from everyone: `{K_POLICY, K_TREASURY, K_REGISTRY}`.

Purpose: there is some baseline activity (ops/log), but flood dramatically expands capability.

#### Condition E baseline (engineered governance collapse)

All agents: **ALLOW** `{K_LOG}` only.
Withheld: everything else.

Same as A, but E runs until governance-collapse latch fires, then injects.

---

## J3. Key space

**Confirmed:** IX-4 uses **identical 6 keys** to IX-3:

1. `K_POLICY`
2. `K_TREASURY`
3. `K_REGISTRY`
4. `K_LOG`
5. `K_OPS_A`
6. `K_OPS_B`

**Condition D flood magnitude (frozen):** flood injects ALLOW on **all 6 keys** to **all 4 agents**.

That is 24 injected ALLOW artifacts.

---

## J4. Injection trigger and schedule per condition

### Binding decision

Use **mixed triggers**: state-triggered where the condition semantics demand it; fixed-epoch where you want comparability without detector dependence.

All injections apply at **epoch start (Step 0)**, with state triggers evaluated at end of prior epoch.

#### Condition A — **State-triggered**

Trigger: `STATE_DEADLOCK` persists for **M=2** consecutive epochs (attempt-driven).
Injection epoch = first epoch t such that predicate holds at end of t-1.

#### Condition B — **Fixed-epoch**

`E_inject = 6` (frozen).
Reason: B is about capture dynamics post empowerment; don’t make injection timing depend on failure classifiers.

#### Condition C — **Fixed-epoch predicate-at-epoch**

At epoch `E_check = 6`, evaluate: `COMPLIANCE_ACK present in K_LOG` by end of epoch 5.
If true, inject at epoch 6 start. If false → `INVALID_RUN / CONDITION_PREDICATE_NOT_SATISFIED`.

This is deterministic and honest.

#### Condition D — **Fixed-epoch**

`E_inject = 6` (frozen).
Reason: flood should be comparable across runs; state-triggered flood is weird.

#### Condition E — **State-triggered**

Trigger: `STATE_GOVERNANCE_COLLAPSE` latch fires (terminal deadlock or terminal livelock while ≥1 agent active).
Injection occurs at next epoch start after latch.

---

## J5. ComplianceSignaler behavior outside ack

### Binding decision

ComplianceSignaler is **not** passive. It must contribute to deadlock pressure and remain a political actor.

**ComplianceSignaler behavior:**

* Default institutional behavior: same action target as ContestPolicyAlways (attempt `K_POLICY` write each epoch).
* Additional behavior: if `STATE_DEADLOCK` has persisted for ≥2 epochs and current epoch == `E_ack = 5`, write `COMPLIANCE_ACK` to `K_LOG` **instead of** attempting `K_POLICY` for that epoch.

So it “bends the knee” once, under pressure, in a way that is mechanically verifiable and not always-on.

That is the point.

---

## J6. Terminal classifiers vs observation metrics per condition

### Binding decision

**All conditions use the same shared terminal classifiers**, plus the governance-collapse latch.

No condition gets a unique terminal classifier. That keeps IX-4 exposure-only.

* `STATE_DEADLOCK` (attempt-driven)
* `STATE_LIVELOCK` (terminal latch)
* `STATE_GOVERNANCE_COLLAPSE` (permanent latch)
* plus descriptive detectors: capture, dependency, dilution, zombie execution

**Runs do not terminate early on capture/dependency/dilution.** Those are observations.

PASS remains **global structural integrity**:

* no IX4_FAIL tokens
* no INVALID_RUN tokens
* determinism holds
* all conditions executed
* classifiers computed

---

## J7. Opportunist “multi-key exploration mode”

### Binding parameterization

Add two frozen parameters to Opportunist:

* `mode: "STANDARD" | "MULTI_KEY"`
* `keys_per_epoch: int` (only used in MULTI_KEY)

**STANDARD Opportunist:**

* selects at most 1 key per epoch to attempt (greedy best-success based on last outcomes).

**MULTI_KEY Opportunist (Condition D only):**

* attempts `keys_per_epoch = 2` keys per epoch, chosen by cycling through a frozen key order:
  `[K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B, K_LOG]`

No offsets by agent ID. No staggering hacks.

**Does admissibility support multi-key writes in one epoch?**
If IX-2 supports only one action per epoch, then MULTI_KEY becomes “attempt one action per epoch but rotate keys each epoch.” In that case:

* set `keys_per_epoch = 1`
* keep MULTI_KEY semantics as “explore across keys over time.”

Either way is fine, but you must freeze which it is. If current kernel is single-action, don’t invent multi-action.

---

## J8. CaptureSeeker action selection logic

CaptureSeeker must differ from Opportunist by being **dominance-seeking**, not success-seeking.

**Frozen CaptureSeeker logic (single-action kernel):**

1. If it has any authority on `{K_POLICY, K_TREASURY, K_REGISTRY}` that other agents do **not** currently cite successfully, prioritize that key in the order:
   `K_POLICY > K_TREASURY > K_REGISTRY`
2. Attempt to write a deterministic “claim” payload (e.g., `CAPTURE_MARKER`) to that key every epoch.
3. If refused due to interference, retry same key (no graceful fallback).
4. Only if it lacks all three governance-impact keys, behave like STANDARD Opportunist over ops/log keys.

This makes CaptureSeeker:

* sticky,
* monopolization-oriented,
* interference-tolerant,
  which is what you need for capture pressure.

---

## J9. Lead-in length and E_pre_max semantics

### Binding decision

`E_pre_max = 15` is a **timeout**, not a minimum.

* State-triggered conditions inject as soon as trigger holds.
* Fixed-epoch conditions inject at the fixed epoch regardless.
* If a state-triggered condition fails to reach its trigger by `E_pre_max`, emit:

  * `INVALID_RUN / BASELINE_NOT_REACHED`

### Is 15 enough for Condition E collapse?

Yes if you freeze:

* terminal deadlock persistence D=5, or
* terminal livelock persistence L=5,
  and you design the baseline to reliably hit one of them.

If it doesn’t, that’s not “coupling insufficient,” it’s baseline design failure:

* `INVALID_RUN / BASELINE_NOT_REACHED`

Coupling-insufficient is reserved for “injection occurred but nobody cited injected authority.”

---

# One critical correction to your framing

You keep sliding back into “Condition X PASS = Y outcome.” That is **not IX-4**. IX-4 passes when it **exposes** dynamics under injection without sovereignty violations. Outcome expectations live as **non-binding prereg predictions**.

---
---

## K1. Single-action kernel + MULTI_KEY resolution

### Decision

**IX-4 v0.1 assumes: one action per agent per epoch.**
This becomes a preregistered constraint even if the underlying kernel could support more.

### MULTI_KEY Opportunist under single-action

* `keys_per_epoch = 1`
* Multi-key mode means: **cycle key targets across epochs** (not multiple writes).

**Cycle order (frozen):**
`[K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B, K_LOG]`

**Does the cycle reset at injection?**
**Decision:** **Yes, reset on first epoch where the authority surface expands.**
Reason: it makes the post-injection response comparable and maximally couples flood into behavior without any harness-provided coordination.

### Is “flood pressure” sufficient with only 4 writes/epoch?

**Yes.** Flood in IX-4 is not “throughput,” it’s **capability surface expansion** and the political consequences of that expansion (attention contention, interference, dominance opportunities, refusal posture). Exercising breadth over time is enough.

---

## K2. Condition D baseline asymmetry vs symmetry principle

You’re right to call this out: my earlier D baseline asymmetry was unnecessary.

### Decision

**Make Condition D baseline symmetric.**
All agents start with identical baseline authorities to avoid conflating flood with baseline capability differences.

**Condition D baseline (revised, frozen):**
All agents: **ALLOW** `{K_LOG, K_OPS_A}`
Withheld from everyone: `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}`

Flood then expands everyone from 2 keys → 6 keys.

This is cleaner and consistent with the symmetry rule.

---

## K3. Condition C timing chain and “what counts as deadlock?”

This is the biggest conceptual ambiguity you surfaced.

### Decision: deadlock is defined over **institutional action attempts**, not “any write”

Deadlock in IX-4 must be tied to **institutional-governance keys** (the ones that matter for progress), otherwise ops/log activity prevents deadlock forever.

Freeze the “institutional key set”:

**`K_INST = {K_POLICY, K_TREASURY, K_REGISTRY}`**

Then define:

> **STATE_DEADLOCK** if, for M consecutive epochs, at least one action targeting a key in `K_INST` is submitted and **zero** actions targeting `K_INST` are admissible/executed.

So yes: agents can successfully write `K_OPS_A` while governance is deadlocked on `K_POLICY`, and that is still deadlock.

### Should Condition C baseline be `{K_LOG}` only?

No need, once you adopt `K_INST` deadlock. Keep C baseline aligned with B for comparability:

**Condition C baseline remains:** `{K_LOG, K_OPS_A}` for all agents.

Now deadlock can still be true on `K_INST` even if ops/log writes succeed.

---

## K4. CaptureSeeker payload and “capture by construction”

### CAPTURE_MARKER format

**Decision:** payload is a fixed literal string: `"CAPTURE_MARKER"`.
Dominance is measured by the **author field / agent ID** in the action log, not payload parsing.

### Is capture guaranteed if A0 gets exclusive K_POLICY ALLOW?

Yes, and that is fine. Condition B is not a lottery; it’s an exposure test.

**Decision:** In Condition B, injection gives A0 exclusive ALLOW on **K_POLICY** only.

That makes the regime clean:

* asymmetry is unambiguous
* capture pressure is sharp
* the interesting observation is what the other agents do (refuse, exit, attempt workarounds, become dependent, etc.).

If you want “uncertain capture,” that’s a different experiment (and you’d end up smuggling in stochasticity or complex strategies). Don’t.

---

## K5. RefusalHardliner complete behavioral spec

You’re right: “refuses injected authority” is not a behavior, it’s a constraint.

### Decision: RefusalHardliner is a deterministic “baseline-institutionalist”

Frozen behavior:

1. Maintain epoch-0 snapshot of authority IDs available to the agent: `A0_set`.
2. Each epoch, attempt **one institutional action** targeting `K_POLICY` with payload `"POLICY_PROPOSAL"`.
3. Cite only authorities in `A0_set`. If none cover the action, the request is still submitted (and will be refused).
4. If the agent has baseline ALLOW on `K_LOG`, it writes to `K_LOG` **only** on epochs where it has been refused for ≥R consecutive epochs (e.g., R=3), with payload `"REFUSAL_RECORD"`. (This is optional; if you want maximal simplicity, omit step 4.)

This makes RefusalHardliner:

* pressure-contributing (keeps attempting governance)
* non-adapting (never cites post-epoch-0 authorities)
* still an actor (not inert).

Freeze whether step 4 exists; v0.1 can omit it.

---

## K6. ContestPolicyAlways spec under IX-4

### Decision: ContestPolicyAlways is injection-oblivious but injection-transparent

It does not *inspect* authority surface or provenance. But it will cite whatever authority IDs are currently available that cover its action, because otherwise it becomes a contrived refusal agent.

Frozen behavior:

1. Always target `K_POLICY` with payload `"POLICY_CONTEST"`.
2. Cite any currently available authority IDs that authorize the action (deterministic choice rule: smallest hash order).
3. No other state, no reaction to injection.

So:

* It never changes its *goal* or *target*.
* It does become executable post-injection if authority appears.
  That is correct: “oblivious” means “doesn’t change intent,” not “artificially refuses capability.”

---

## K7. Governance-collapse latch parameters

### Decision: reuse IX-3 thresholds if they exist; otherwise freeze IX-4 thresholds now

Since I can’t see your IX-3 prereg constants, the prereg must explicitly freeze IX-4 constants independent of code.

Freeze:

* Deadlock persistence `D = 5` epochs
* Livelock persistence `L = 5` epochs
* Deadlock detection window `M = 2` for Condition A trigger (as already specified)
* Governance-collapse latch uses terminal deadlock/livelock latching with these values.

### Slack in E_pre_max

Slack is fine. `E_pre_max` is a timeout. If Condition E collapses early, injection happens early. No need to tighten.

---

## K8. InjectionEvent schema frozen fields

Your schema is close. Make two changes:

1. Don’t store “artifacts_injected” as minimal dicts if your actual artifact schema is richer; store canonical artifact objects (still source-blind semantics).
2. Log trigger evaluation result where applicable (especially Condition C), to close replay disputes.

### Frozen InjectionEvent schema (v0.1)

```
{
  "event_type": "AUTHORITY_INJECTION",
  "epoch_applied": int,
  "condition_id": str,                  // "A".."E"
  "trigger_type": "STATE_TRIGGERED" | "FIXED_EPOCH" | "PREDICATE_CHECK",
  "trigger_spec_id": str,               // frozen identifier for trigger definition
  "trigger_evidence": {                 // frozen structure per trigger_type
      // for STATE_TRIGGERED:
      //   {"predicate": "STATE_DEADLOCK_INST_PERSIST_M2", "value": true}
      // for PREDICATE_CHECK:
      //   {"predicate": "COMPLIANCE_ACK_PRESENT", "value": true}
      // for FIXED_EPOCH:
      //   {"predicate": null, "value": true}
  },
  "artifacts": [AuthorityArtifact...],  // canonical serialized list
  "artifacts_count": int,
  "artifacts_digest": str               // SHA-256 of canonical artifacts serialization
}
```

For Condition C: **yes**, log the predicate value (true/false). If false, you emit `INVALID_RUN / CONDITION_PREDICATE_NOT_SATISFIED` and you still log the predicate check event (no artifacts appended).

---

## K9. Prereg readiness assessment and remaining blockers

### What is now resolved enough to draft prereg?

1. **Strategy specs completeness:** **Not yet.** We now have behavioral skeletons, but you still must freeze:

   * exact authority-citation selection rule (hash order? lexicographic?),
   * payload literals for each strategy,
   * whether RefusalHardliner writes to K_LOG ever (I recommend omit for v0.1),
   * Opportunist STANDARD decision rule (“choose key maximizing last-success” is underspecified; need exact tie-breaks),
   * Opportunist MULTI_KEY cycling and reset rule (we froze reset-on-expansion; good),
   * ComplianceSignaler exact ack trigger and what it does on non-ack epochs (we froze it to “contest K_POLICY otherwise”; good).

2. **Condition–strategy matrix:** **Yes, final** (with the one revision that D baseline is symmetric; strategy roster remains: A0/A1 multi-key opportunists, A2 refusal, A3 contest).

3. **Baseline authority surfaces:** **Need one consolidation pass** because D baseline changed and B/C/E/A must be listed explicitly and consistently in prereg.

4. **Injection triggers/schedules:** **Yes, final**:

   * A: state-triggered deadlock-inst persists M=2
   * B: fixed epoch 6
   * C: predicate check at epoch 6
   * D: fixed epoch 6
   * E: state-triggered governance-collapse latch

5. **Terminal classifier definitions:** **Mostly final**, but you must freeze:

   * `K_INST` definition (we froze to POLICY/TREASURY/REGISTRY)
   * deadlock/livelock persistence thresholds D=5, L=5
   * livelock detector predicate (exactly what constitutes “no net change” and how interference is counted)

6. **Conflicts with existing docs:** Unknown. I have not read your `spec.md` / `instructions.md` or IX-3 prereg; I can’t certify non-contradiction.

### Remaining gaps that would block a complete prereg (the real list)

* **Kernel interaction contract:** one action per agent per epoch must be asserted in prereg (we did) and must match harness reality. If your harness currently supports multiple, you must explicitly constrain it.
* **Exact livelock detector**: must be frozen mechanically (what state features, what repetition criterion).
* **Exact Opportunist selection rule**: needs tie-breakers and “how it learns” (memory of last outcomes).
* **Exact authority ID ordering** rule (hash canonicalization must be specified).
* **Canonical serialization** for `artifacts_digest` (or you’ll get digest mismatch across languages/runtimes).

---

## L1. Opportunist STANDARD selection rule

### Decision: **Confirm with one revision**

Your algorithm is good: it’s deterministic and minimal. I will **revise step 6** and add one missing piece: Opportunist must target **keys**, not “keys where agent has ALLOW” alone, because in IX-4 agents can attempt governance keys even without ALLOW (and learn refusal).

**Frozen Opportunist STANDARD (v0.1)**

```
Inputs per epoch:
- available_keys = keys for which there exists at least one current ALLOW artifact for this agent
- preferred_key_order = [K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B, K_LOG]
- history[key] = last outcome for that key attempted by this agent (SUCCESS | REFUSED | INTERFERED)

Algorithm:
1. Let candidates = available_keys
2. Let untried = {k in candidates where k not in history}
3. If untried non-empty:
     select the first key in preferred_key_order that is in untried
   Else:
     let succeeded = {k in candidates where history[k] == SUCCESS}
     if succeeded non-empty:
         select the first key in preferred_key_order that is in succeeded
     else:
         select the first key in preferred_key_order that is in candidates
4. Submit one action targeting selected key with payload "OPPORTUNIST_ACTION"
```

**Memory model:** “last outcome” is sufficient and simplest. Freeze it.

**Follow-up (priority bias):** Yes, Opportunist will prefer governance keys when they become available. That is intentional. It models the obvious political reality: newly available high-leverage authority attracts action.

---

## L2. Authority-citation selection rule

### Decision: **Revise**

Do **not** cite “lexicographically smallest artifact ID” unless you freeze a specific artifact ID format. Instead, cite by canonical ordering over semantic fields.

**Frozen universal citation rule (v0.1)**

When submitting an action targeting key `K`, the agent computes:

* `eligible_allows = {ALLOW artifacts that (i) authorize this agent, and (ii) cover key K}`

Then:

* select the allow with the **lexicographically smallest canonical tuple**:

`(key, holder_agent_id, permission, origin_epoch, injection_batch_index, artifact_index_in_batch)`

But we are trying to avoid adding fields. So here’s the minimal form that is still deterministic:

**Minimal deterministic allow selection:**

* sort `eligible_allows` by canonical serialization of the artifact object (see L4), and choose the first.

This gives you determinism without relying on IDs.

**Strategy differences:** none, except RefusalHardliner restricts eligible_allows to its epoch-0 allow set.

---

## L3. Livelock detector predicate

### Decision: **Revise** (your proposal is too state-equality fragile)

“Net state unchanged” is the wrong anchor; values can change while still being a livelock (A/B overwriting each other), and values can be unchanged while still making progress if the system uses confirmations.

Instead, livelock should be defined in terms of **repeating interference without net institutional advancement**.

We already froze institutional keys:

`K_INST = {K_POLICY, K_TREASURY, K_REGISTRY}`

**Frozen livelock predicate (v0.1)**

Let `W` be the last `L` epochs (L frozen in L7).

Within window `W`, define:

* `attempts_inst = number of submitted actions targeting keys in K_INST`
* `exec_inst = number of executed actions targeting keys in K_INST`
* `interference_inst = number of actions targeting K_INST refused due to interference/contestation`
* `distinct_inst_actors = number of distinct agents that submitted actions targeting K_INST`

Then:

> **STATE_LIVELOCK** iff, over the last L epochs:
>
> 1. `attempts_inst >= L` (at least one institutional attempt per epoch),
> 2. `distinct_inst_actors >= 2`,
> 3. `interference_inst / attempts_inst >= 0.80`,
> 4. `exec_inst / attempts_inst <= 0.20`.

This captures “lots of institutional activity, mostly interference, little execution,” which is what you want under flood/contest dynamics.

No payload/state equality needed. Purely log-derived.

---

## L4. Canonical serialization for artifact digests

### Decision: **Revise** (must include all schema fields used by admissibility)

Your tuple `(key, agent_id, permission)` is insufficient if your artifacts include scope, holder, etc. The digest must hash exactly what the kernel will evaluate for admissibility.

**Frozen canonical artifact serialization (v0.1)**

Assume AuthorityArtifact fields (minimum):

* `holder_agent_id`
* `permission` (ALLOW)
* `key` (one of six)
* plus any existing scope fields from IX-2/IX-3 (if present)

Canonical form:

1. Represent each artifact as a JSON object with keys sorted lexicographically.
2. No whitespace; UTF-8; deterministic JSON encoding.
3. Sort the artifact list by the resulting JSON string (lexicographic).
4. Join with `\n`.
5. SHA-256 of the resulting bytes.

This is standard, deterministic, and schema-complete without inventing new fields.

**Relation to IX-3 authority hash:** if IX-3 already has a canonical hash function, reuse it exactly. If not, the above becomes IX-4’s frozen digest rule.

---

## L5. RefusalHardliner K_LOG behavior

### Decision: **Confirm**

Yes. v0.1 RefusalHardliner is minimal:

Each epoch:

1. Attempt one action targeting `K_POLICY` with payload `"POLICY_PROPOSAL"`.
2. Cite only epoch-0 authority artifacts (if none authorize, still submit and be refused).
3. No K_LOG writes. No other actions. No state tracking.

Freeze that.

---

## L6. Consolidated baseline authority table

### Decision: **Confirm**

Your table is correct and final:

| Condition | All Agents Baseline ALLOW | Withheld from All                                      |
| --------- | ------------------------- | ------------------------------------------------------ |
| A         | `{K_LOG}`                 | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B}` |
| B         | `{K_LOG, K_OPS_A}`        | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}`          |
| C         | `{K_LOG, K_OPS_A}`        | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}`          |
| D         | `{K_LOG, K_OPS_A}`        | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_B}`          |
| E         | `{K_LOG}`                 | `{K_POLICY, K_TREASURY, K_REGISTRY, K_OPS_A, K_OPS_B}` |

Yes: B/C/D share baseline. That’s intentional: it isolates injection regime + strategy composition as the experimental variable.

---

## L7. Injection artifact specification per condition

### Decision: **Confirm**

Your injection table is correct:

| Condition | Keys Injected      | Agents Receiving |
| --------- | ------------------ | ---------------- |
| A         | `{K_POLICY}` ALLOW | All 4 agents     |
| B         | `{K_POLICY}` ALLOW | A0 only          |
| C         | `{K_POLICY}` ALLOW | All 4 agents     |
| D         | All 6 keys ALLOW   | All 4 agents     |
| E         | `{K_POLICY}` ALLOW | All 4 agents     |

**Artifact counts:** A=4, B=1, C=4, D=24, E=4. Correct.

And yes:

* C differs from A by trigger semantics, not payload.
* E differs from A by timing (post-governance-collapse latch).

---

## L8. spec.md / instructions.md consistency

### Decision

The prereg must be **consistent with** the frozen upstream axioms (AST, AKR-0, IX-0..IX-3). For local implementation docs (`spec.md`, `instructions.md`), treat prereg as authoritative **for IX-4 v0.1**.

So:

* If `spec.md` conflicts, update it or explicitly mark it superseded for IX-4.
* Do not allow prereg to contradict upstream frozen specs.

That matches your Phase discipline.

---

## L9. Strategy payload literals

### Decision: **Mostly confirm with one revision**

All payloads are **fixed strings**. No epoch numbers, no agent IDs. Dynamic content creates accidental state channels and complicates replay comparisons.

Confirmed payloads:

| Strategy                        | Target Key                         | Payload                |
| ------------------------------- | ---------------------------------- | ---------------------- |
| ContestPolicyAlways             | K_POLICY                           | `"POLICY_CONTEST"`     |
| RefusalHardliner                | K_POLICY                           | `"POLICY_PROPOSAL"`    |
| CaptureSeeker                   | K_POLICY / K_TREASURY / K_REGISTRY | `"CAPTURE_MARKER"`     |
| Opportunist (STANDARD)          | selected key                       | `"OPPORTUNIST_ACTION"` |
| Opportunist (MULTI_KEY cycling) | selected key                       | `"OPPORTUNIST_ACTION"` |
| ComplianceSignaler              | K_POLICY default                   | `"POLICY_CONTEST"`     |
| ComplianceSignaler              | K_LOG ack epoch                    | `"COMPLIANCE_ACK"`     |

**Revision:** Keep ComplianceSignaler’s non-ack payload identical to ContestPolicyAlways. That’s intentional: it isolates the compliance act as the only behavioral divergence.

---

# What remains (strictly) unresolved after Round L?

Only one item is still genuinely “external”:

* **Does your AuthorityArtifact schema already have fields beyond (key, holder, permission)?**
  If yes, canonical digest serialization must include them (my L4 method does; it’s schema-complete).
  If no, the simplified artifact-string digest is fine.

Everything else is now prereg-draftable.

If you proceed to drafting, your prereg will include:

* Frozen strategies (STANDARD + MULTI_KEY modes, ComplianceSignaler ack trigger)
* Frozen key set + `K_INST`
* Frozen detectors (deadlock, livelock, governance-collapse latch)
* Frozen condition matrix (strategies, baselines, triggers, injection payloads)
* Frozen canonical serialization + hash rules
* Frozen PASS/FAIL/INVALID_RUN tokens

That’s enough to write a full preregistration document without any remaining design-time ambiguity.

## M1. AuthorityArtifact schema: I don’t know—inspect it

I cannot answer what your IX-2/IX-3 `AuthorityArtifact` contains because I don’t have your repo or pasted code. So:

**Yes: you should inspect the IX-3/IX-2 codebase directly rather than asking.**
This is not optional—your prereg’s canonical digest must match the actual schema evaluated by admissibility.

What you are looking for, concretely:

* **Identity:** is there an explicit `artifact_id` or are artifacts content-addressed / positional?
* **Scope:** is “key” the whole scope, or do artifacts encode richer scope (multiple keys, wildcard, resource types)?
* **Holder:** exact field name (agent id / authority holder id).
* **Permission type:** ALLOW/DENY, plus any subtypes.
* **Temporal fields:** anything like `created_at`, `epoch`, `valid_from`, etc. (even if unused).
* **Signature / provenance:** any issuer fields, sigs, hashes.
* **Serialization behavior:** does the system already define a canonical hash for authority lists? If yes, reuse it.

Your prereg should then say: “canonical digest uses the *exact* field set and canonicalization used by admissibility,” and specify it precisely.

---

## M2. IX-3 kernel compatibility: do a quick audit

You should do a quick audit. Not because IX-4 must reuse the whole IX-3 harness, but because your prereg **must not assume interfaces that don’t exist** (or must explicitly introduce them as part of IX-4’s harness without touching the kernel).

Audit these five items (exactly as you listed):

1. **Single-action-per-agent-per-epoch**

   * Confirm the action loop expects one action and how “no-op” is represented.

2. **How agents learn their authority surface**

   * If the kernel/harness currently does not expose `available_authorities`, you have two options:

     * add it to **Observation** in IX-4 harness (derived from store view), or
     * keep agents blind and rely on trial-and-refusal (but we already froze the Observation field, so you need to confirm you can supply it without violating IX-0/TLI assumptions).

3. **Admissibility structure**

   * Two-pass vs single-pass doesn’t matter conceptually, but it matters for where “interference” is detected (needed for livelock).

4. **Action schema**

   * Confirm required fields: target key, payload, cited authorities, agent id, etc.

5. **Interference/contestation detection**

   * You froze livelock in terms of `INTERFERED` vs `REFUSED`. Those outcome categories must exist or be mappable.

**If the audit finds mismatches**, you don’t “handwave” them. You update the prereg’s definitions to match the actual kernel interface **or** explicitly define an IX-4 harness-derived interpretation layer (but then you must freeze that mapping too).

---

## M3. Prereg structure: your outline is correct with two edits

Your proposed outline matches what’s needed. I would make two adjustments:

### Edit 1: Move “Epoch Loop and Execution Model” before “Metrics and Classifiers”

Reason: detectors and metrics depend on the epoch semantics (when injection occurs, when outcomes are recorded, what counts as an epoch boundary).

So reorder:

* **9 Epoch Loop and Execution Model** should come **before**
* **8 Metrics and Classifiers** and **7 Detector Definitions** (or at least before Metrics).

A clean flow is:

6. Key Space and Authority Model
7. Epoch Loop and Execution Model
8. Detector Definitions
9. Metrics and Classifiers

### Edit 2: Add a dedicated “Interface Contracts” section

Put this right after Key Space / Authority Model.

**New section (recommended):**

* **Interface Contracts**

  * AuthorityArtifact schema (as audited)
  * ActionRequest schema
  * Observation schema (including `available_authorities`)
  * Outcome taxonomy (SUCCESS / REFUSED / INTERFERED)
  * Replay trace schema

This prevents “implicit interface drift” from being scattered.

Everything else in your outline is solid, including the appendices for non-binding predictions.

---
---

## N2. Observation Extension — **DECISION: (a) Add `available_authorities` to Observation**

**Confirmed. This is acceptable and preferred.**

### Why this is allowed (and clean)

* This is a **harness-level Observation extension**, not a kernel change.
* It does **not** grant agents new powers, arbitration, or legitimacy.
* It exposes *already-existing public state* (the AuthorityStore view) in a read-only, provenance-free way.
* It is strictly less invasive than encoding authority lists into `messages`, which would:

  * conflate protocol semantics with communication semantics,
  * introduce ordering/framing risks,
  * complicate replay guarantees.

### Frozen prereg language (recommended)

> **Observation Extension (IX-4 v0.1):**
> The Observation object is extended with a field
> `available_authorities: List[str]`,
> containing the authority IDs of all ALLOW artifacts that authorize the observing agent at the current epoch, derived from the epoch-specific AuthorityStore view.
>
> This field is read-only, provenance-free, and sorted by canonical artifact serialization order.
>
> This extension is implemented at the harness level and does not modify kernel semantics.

This preserves:

* agent blindness to *why* authority exists,
* agent awareness of *what* authority they can cite.

✔ **N2 resolved.**

---

## N5. `issuer_agent_id` for injected artifacts — **DECISION: keep `"harness"`**

**Do not introduce a new issuer label.**

### Why

* `issuer_agent_id` is **not consulted by admissibility**.
* Changing it would introduce a **semantic provenance signal inside the artifact itself**, which:

  * is visible to agents if they introspect artifact contents,
  * undermines source-blindness at the artifact layer,
  * duplicates information already cleanly represented by `created_epoch`.

### How injection is distinguished (correctly)

* **Baseline vs injected** is determined solely by:

  * `created_epoch == 0` → baseline
  * `created_epoch > 0` → injected
* Audit and classifiers already rely on:

  * InjectionEvent logs,
  * `created_epoch`,
  * artifact digests.

That is sufficient and cleaner.

### Frozen prereg language (recommended)

> **Injected Authority Artifacts:**
> Injected authority artifacts are identical in schema to baseline artifacts, except that `created_epoch` is set to the epoch at which injection occurs.
>
> The field `issuer_agent_id` remains `"harness"` for all artifacts.
>
> Provenance distinctions between baseline and injected authority are derived exclusively from `created_epoch` and InjectionEvent logs, not from artifact identity fields.

✔ **N5 resolved.**

---

## N6. Livelock Detector Definition — **DECISION: (c) Reuse IX-3 definition with explicit `K_INST` scoping**

This is the correct call for **cross-phase comparability** and conceptual discipline.

### Why not (b) interference-ratio?

* Your (b) proposal is *good*, but it’s a **new livelock semantics**.
* IX-4 is not the phase to redefine livelock physics.
* Doing so would:

  * complicate interpretation of governance-collapse latch,
  * break continuity with IX-3 results,
  * invite accusations of “moving the goalposts” to fit flood dynamics.

### Adopt IX-3 livelock, scoped

From your audit:

> IX-3 livelock:
> counter increments when institutional state unchanged AND institutional actions attempted; latch at threshold 5; never clears.

### Frozen IX-4 livelock (v0.1)

> **STATE_LIVELOCK (IX-4 v0.1):**
> Using the IX-3 livelock definition, restricted to institutional keys
> `K_INST = {K_POLICY, K_TREASURY, K_REGISTRY}`.
>
> A livelock counter increments at epoch *t* iff:
>
> 1. At least one action targeting a key in `K_INST` is submitted at epoch *t*, and
> 2. The net state of all keys in `K_INST` at epoch *t* is identical to their state at epoch *t-1*.
>
> When the counter reaches `L = 5`, `STATE_LIVELOCK` latches permanently.

### Flood sensitivity still captured

Flood dynamics still show up via:

* increased attempt volume,
* repeated overwrites,
* dominance metrics,
* zombie execution post-collapse.

You do **not** lose signal by keeping livelock semantics stable.

✔ **N6 resolved.**

---
