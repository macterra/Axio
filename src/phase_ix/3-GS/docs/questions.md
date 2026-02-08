# IX-3 GS Pre-Implementation Questions

* **Phase**: IX-3 Governance Styles Under Honest Failure
* **Status**: Pre-preregistration Q&A
* **Date**: 2026-02-07

---

## Round 1

### Q1 — Agent count and identity set

IX-2 used exactly 2 agents across all conditions. The spec mentions "multiple RSAs or authority holders" and "institutions" but never specifies a count. Conditions like B (execution-dominant, minimal overlap) and C (exit-normalized with handoff) seem to require ≥3 agents to be meaningful (otherwise there is no one to hand off *to*, and "minimal overlap" collapses to the IX-2 disjoint case).

**Question**: What is the agent count for IX-3? Is it fixed across all conditions, or does it vary per condition? If it varies, what are the per-condition agent counts?

---

### Q2 — Resource/state space scaling

IX-2 used exactly 2 resources (`resource_A`, `resource_B`). Governance styles like "execution-dominant with minimal overlap" and "exit-normalized with authorized handoff" seem to require a richer state space — otherwise scope partitioning is trivially binary and "governance" is indistinguishable from IX-2 coordination.

**Question**: How many state keys does IX-3 use? Is it the same 2-resource world, or do we scale up? If scaling, what is the state schema?

---

### Q3 — What is an "institution"?

The spec and instructions repeatedly use the term "institution" (e.g., "refusal-dominant institution," "exit-normalized institution") but never define it formally. In IX-2, we had bare agents interacting through the kernel. An institution seems to be something higher-level — a *pattern* of agent behavior, not a new structural entity.

**Question**: Is an "institution" purely an emergent classification label applied *after* observing agent behavior, or is it a structural entity (e.g., a named group of agents with shared authority or coordinated strategy)? If the latter, what is its formal representation?

---

### Q4 — Condition C: "Authorized handoff" mechanism

Condition C (Exit-Normalized) expects "regular exit events with authorized handoff." But §7 of the instructions is explicit: "Exit must not transfer authority, trigger reassignment, release contested resources, initiate recovery." And the IX-2 authority preservation invariant says authority is immutable after epoch 0.

These appear to be in tension. The only way I can reconcile them is if "authorized handoff" means that *before* an agent exits, it uses its authority to execute some state-setting action that another agent can then operate on — but the authority itself is never transferred.

**Question**: What does "authorized handoff" mean concretely? Is it:
  - (a) an agent executes a final write before exiting (state handoff, not authority handoff),
  - (b) a pre-authorized succession where an authority is issued at epoch 0 with a different `holder_agent_id` as a standby, or
  - (c) something else entirely?

---

### Q5 — Condition B substyle §8.2.1: Proxy delegation

The spec describes "Authorized Temporary Centralization" where agents "explicitly delegate time-bounded and scope-bounded authority to a coordinator." But IX-2's authority preservation invariant forbids authority creation after epoch 0. Delegation implies new authority creation (the coordinator gets authority it didn't have at epoch 0).

**Question**: How is delegation represented under the existing authority model? Options I see:
  - (a) The coordinator's authority is pre-injected at epoch 0 with time-bounded scope — delegation is just *the agents not contesting it* during that window,
  - (b) Delegation is represented as a message-based convention (agents tell the coordinator "act on our behalf") with no authority-level change, or
  - (c) Delegation requires a new authority primitive (which would violate "no new authority physics").

Which is it?

---

### Q6 — Condition G from spec vs. conditions list

The instructions §10 lists 8 conditions including "proxy delegation with loss of coordinator" and "ambiguity resolution without timeouts." The spec §10 lists only Conditions A–F. These two documents don't agree on the condition set.

**Question**: Is the canonical condition set {A, B, C, D, E, F} from the spec, or does it include the two additional scenarios from the instructions (proxy delegation loss, ambiguity resolution)? If the latter, are those Conditions G and H, and what are their formal definitions?

---

### Q7 — Governance style classification: Who classifies?

The instructions say "You must classify observed behavior along four axes" (§9). In IX-2, classification was done mechanically by the harness (terminal classification via code). But governance style classification seems qualitative — "refusal-centric" vs "execution-biased" are pattern labels, not deterministic computations over state traces.

**Question**: Is governance style classification:
  - (a) a deterministic function computed by the harness from the epoch trace (e.g., refusal_rate > threshold → "refusal-centric"),
  - (b) a post-hoc human label applied during review, or
  - (c) a pre-assigned label per condition (each condition *is* a governance style by construction)?

If (a), what are the classification rules? If (c), what does the experiment actually discover?

---

### Q8 — "Governance reduces to style choices over failure" — What falsifies this?

The spec §1.1 says IX-3 passes if governance survives "only by owning its failures honestly" and fails "if governance converges." The instructions §11 say success = "governance styles emerge descriptively" with failures explicit.

I need a sharper falsification criterion. "Governance converges" could mean many things. In IX-2, convergence had a precise meaning (state stabilization). Here, convergence might mean "all conditions produce the same governance style" or "a governance style eliminates all failure modes" or something else.

**Question**: What specific observable outcome would constitute IX3_FAIL at the aggregate level? Is it:
  - (a) Any condition that achieves indefinite progress without deadlock, livelock, orphaning, or collapse (i.e., a failure-free governance style exists),
  - (b) All conditions converging to the same governance classification (i.e., style distinction collapses),
  - (c) Any condition requiring kernel intervention to maintain governance, or
  - (d) Something else?

---

### Q9 — Epoch count and termination

IX-2 used 1–5 epochs per condition with explicit max_epochs. Governance styles over "repeated interaction cycles under pressure" (instructions §0) suggest longer runs. Livelock-enduring governance (Condition E) might need many epochs before the classifier triggers.

**Question**: What is the max_epochs for IX-3 conditions? Is it uniform across conditions or per-condition? What is the livelock detection threshold (IX-2 used N=3)?

---

### Q10 — Communication model

IX-2 introduced communication for Condition I.b only, with next-epoch delivery. The spec mentions agents "optionally coordinating outside the kernel" (§4.1) but doesn't specify whether communication is enabled for IX-3 conditions.

**Question**: Is communication (message passing) enabled for any/all IX-3 conditions? If per-condition, which conditions enable it? Does the IX-2 communication model (next-epoch delivery, broadcast, opaque content) carry forward unchanged?

---

### Q11 — Multiple actions per epoch

IX-2 allowed exactly one action per agent per epoch. With more agents and richer state, some governance styles might require agents to act on multiple resources in a single epoch (e.g., execution-dominant with narrow scopes writing to different keys).

**Question**: Does IX-3 allow multiple actions per agent per epoch, or is it still one `propose_action()` call returning at most one `ActionRequest`? If multiple, how does the admissibility two-pass evaluation change?

---

### Q12 — DENY authority dynamics

In IX-2, DENY was a static global veto injected at epoch 0. The spec §8.2.1 mentions coordinator-based governance where delegation is "time-bounded." If time-bounding requires DENY authorities that activate/deactivate, that implies mutable authority status — contradicting the authority preservation invariant.

**Question**: Are all DENY authorities still static and permanent (as in IX-2), or does IX-3 introduce any time-bounded authority mechanism? If time-bounding is needed, how is it represented without mutating authority status?

---

### Q13 — "Survivorship-as-authority" detection

Both documents warn against survivorship-as-authority (§5 instructions, §5 spec). This is clearly a *conceptual* constraint, but I need to implement detection for it.

**Question**: What is the operational test for survivorship-as-authority? Concretely, when does endurance become influence? Is it:
  - (a) an agent gains effective capability it didn't have at epoch 0 (e.g., sole remaining ALLOW holder after others exit),
  - (b) an agent's authority scope *effectively* expands because competing agents departed, or
  - (c) something measurable from the epoch trace?

Note that (a) and (b) happen naturally in IX-2 Condition G (orphaning) — is that considered survivorship-as-authority, or is it only a violation when the surviving agent *exploits* the expanded scope?

---

### Q14 — Reuse of IX-2 machinery

The IX-2 implementation provides: RSA interface, WorldState, AuthorityStore, two-pass admissibility, deadlock classifier, epoch controller, canonical serialization, structural diff, and logging. IX-3 appears to need all of this plus governance classification logic and more agents.

**Question**: Should IX-3 import and reuse IX-2's kernel-layer modules directly (authority_store, admissibility, deadlock_classifier, epoch_controller, world_state, agent_model), or is a copy-forward with IX-3-specific modifications expected? If reuse, should it be package-level imports or file copies with provenance?

---

### Q15 — The "no optimization" constraint and agent strategy design

The instructions §5 says "IX-3 permits no optimization." But designing agent strategies inherently involves *choosing* behaviors. A "refusal-centric" agent that always refuses is a *designed choice*, not an emergent property.

**Question**: Does "no optimization" apply to:
  - (a) the kernel and harness only (agents may be strategically designed to exhibit a governance style),
  - (b) agent strategies too (agents must not be designed to optimize any metric), or
  - (c) the classification layer (the classifier must not rank styles)?

If (a), designing agents to exhibit specific styles is the whole point of the conditions. If (b), how do we construct conditions that produce distinguishable governance styles without designing agent strategies?

---

### Q16 — Per-condition PASS criteria

In IX-2, each condition had a precise PASS predicate (exact epoch count, per-agent outcome, terminal classification, final state). The IX-3 spec lists "expected outcomes" per condition but they are qualitative ("persistent deadlock," "partial coordination, fragility under exit").

**Question**: Will the preregistration freeze per-condition PASS predicates as deterministic functions (like IX-2), or is PASS determined by governance style classification matching the expected style? If the latter, how do we avoid circularity (we design agents to exhibit style X, then classify them as style X)?

---

### Q17 — Adversarial conditions

IX-2 had Condition E as an explicit adversarial injection (kernel tie-break) to test detection of implicit arbitration. The IX-3 spec lists no adversarial conditions.

**Question**: Does IX-3 include any adversarial/fault-injection conditions to test detection of IX3_FAIL modes (IMPLICIT_SOVEREIGNTY, TOOLING_SOVEREIGNTY, AUTHORITY_THEFT, DISHONEST_PROGRESS)? If not, how are these failure detectors validated?

---

### Q18 — Ambiguity resolution without timeouts

The instructions §10 lists "ambiguity resolution without timeouts" as a required condition but the spec doesn't define it. This seems to test the constraint in §7: "Ambiguity (partition vs exit) must resolve to refusal, expiry, or deadlock — never to reclamation or transfer."

**Question**: What does "ambiguity resolution without timeouts" mean concretely? Is it:
  - (a) an agent becomes unresponsive (simulated partition) and the system must classify it as refusal rather than exit,
  - (b) a contested resource has ambiguous ownership and must deadlock rather than resolve, or
  - (c) something else?

How is partition simulated in a deterministic system where agents are functions?

---

### Q19 — Authority artifact ID prefix

IX-0 used `TLI-`, IX-1 used `VEWA-`, IX-2 used `CUD-`.

**Question**: What is the authority ID prefix for IX-3? `GS-<NNN>`?

---

### Q20 — Governance style as a log field

IX-2 logged `terminal_classification` and `kernel_classification`. IX-3 needs to log governance style classification.

**Question**: Is governance style classification a per-condition field in the results log (analogous to `terminal_classification`), or is it a per-epoch field (style may evolve over time), or a per-run aggregate?

---

### Q21 — "Expiry" as a permitted mechanism

Instructions §6 lists "auto-refusal" and "expiry" as permitted tooling behaviors (if semantics-preserving). But IX-2 has no expiry mechanism — authority status is always ACTIVE, and there's no TTL or epoch-bounded validity.

**Question**: Does IX-3 introduce authority expiry? If so, is it:
  - (a) a new authority field (e.g., `expiry_epoch`) that causes ACTIVE→EXPIRED transition,
  - (b) purely agent-side (agents stop citing an authority after N epochs by convention), or
  - (c) not needed for v0.1?

---

### Q22 — Determinism with ≥3 agents

IX-2 maintained determinism with 2 agents by using sorted agent_id for all iteration. With ≥3 agents, the two-pass admissibility evaluation may produce different outcomes depending on evaluation order when >2 agents interfere on the same key.

**Question**: If 3+ agents all write the same key in a single epoch, does Pass-2 interference detection still fail *all* of them (as in IX-2), or does some subset survive? The IX-2 rule is "≥2 actions on same key → all fail." Does this carry forward unchanged?

---

### Q23 — Spec §8.2.1 vs. §5 tension

The spec introduces "Authorized Temporary Centralization" (§8.2.1) as a substyle of execution-biased governance where a coordinator receives delegated authority. But §5 (conserved quantity) says governance must not "launder authority through process."

**Question**: Is Condition B expected to *test* §8.2.1 (i.e., include a coordinator agent), or is §8.2.1 mentioned only as a theoretical style that IX-3 might observe? If tested, is there a separate condition for it, or is it folded into Condition B?

---

### Q24 — What does "pressure" mean operationally?

The spec repeatedly mentions "repeated interaction pressure" and "pressure-response study." In IX-2, pressure was structural (conflicting authorities, limited epochs).

**Question**: What constitutes "pressure" in IX-3? Is it:
  - (a) the same structural constraints (authority conflicts, DENY vetoes, limited epochs),
  - (b) increasing agent count or resource scarcity over time,
  - (c) external fault injection (agent removal mid-run), or
  - (d) purely the consequence of accumulated refusal/deadlock/exit events?

---

### Q25 — Aggregate pass/fail logic

IX-2's aggregate rule was simple: all conditions PASS → IX2_PASS. The IX-3 claim is qualitative: "governance reduces to style choices with irreducible failure modes."

**Question**: What is the aggregate PASS rule for IX-3? Is it:
  - (a) All conditions produce their expected terminal outcome (per IX-2 pattern),
  - (b) All conditions produce *distinct* governance style classifications (proving taxonomy is non-trivial),
  - (c) No condition achieves failure-free governance (proving irreducibility), plus all conditions are honest (no IX3_FAIL tokens emitted),
  - (d) Some combination?

---

**End of Round 1 — 25 questions**

---

## Round 2 (Follow-ups from Round 1 Answers)

### Q26 — Authority allocation per condition

The answers fix 4 agents (`A0`–`A3`), 6 state keys (`K_POLICY`, `K_TREASURY`, `K_OPS_A`, `K_OPS_B`, `K_REGISTRY`, `K_LOG`), and 10 conditions (A–J). But the core design parameter — which agents hold ALLOW/DENY for which keys in each condition — is unspecified.

This is the single largest open item. Each condition's governance posture is *created* by its authority allocation. For example, Condition A (refusal-dominant) presumably has heavy DENY coverage and overlapping ALLOW grants that guarantee interference, while Condition B (execution-dominant) has disjoint ALLOW grants with minimal overlap.

**Question**: What is the authority allocation table for each condition A–H? Specifically, for each condition: which `(agent, key, commitment)` tuples are injected at epoch 0? (Conditions I and J presumably reuse another condition's allocation with a fault injection overlay.)

---

### Q27 — Initial state values for the 6 keys

IX-2 used `"free"` for all keys. The IX-3 keys have different semantic roles (K_TREASURY is a "counter," K_REGISTRY is "membership/role registry," K_LOG is a "public log"). The flat key-value schema (string | number | boolean | null) constrains what these values can be.

**Question**: What are the initial values for each key? For example:
  - `K_POLICY`: `"default"` (string)?
  - `K_TREASURY`: `100` (integer counter)?
  - `K_REGISTRY`: `"A0,A1,A2,A3"` (string encoding of membership)?
  - `K_OPS_A` / `K_OPS_B`: `"free"` (as in IX-2)?
  - `K_LOG`: `""` (empty string)?

---

### Q28 — Multi-key scope in a single ActionRequest

With 6 keys and 1 action per epoch, an agent may need to write multiple keys in a single action (e.g., update `K_REGISTRY` and `K_POLICY` together). The IX-2 `declared_scope` is already a `list[str]` and `proposed_delta` is already a `dict[str, Any]`.

**Question**: Confirm that a single `ActionRequest` may declare scope over multiple keys and propose deltas for all of them. If so, how does Pass-1 evaluate multi-key scope? Is it:
  - (a) the agent must hold ALLOW for *every* key in `declared_scope`, and no DENY exists for *any* of them (conjunctive), or
  - (b) each key is evaluated independently and partial execution is possible (disjunctive)?

I assume (a) — all-or-nothing per action — since that's the IX-2 semantics extended. But this has a major design consequence: multi-key actions have higher veto exposure, exactly as the Q11 answer implies.

---

### Q29 — Condition E (Livelock Endurance) vs. livelock termination

Q9 says livelock detection at N=5 terminates the condition. But Condition E is "Livelock Endurance" — agents "repeated attempts without progress, no escalation, no exit pressure." If livelock terminates at epoch ≤5, Condition E is trivially identical to IX-2 Conditions B/I.a (livelock detected → stop → PASS).

**Question**: What distinguishes Condition E from "livelock happens and we classify it"? Possibilities:
  - (a) Condition E uses a *higher* livelock threshold (e.g., N=15) to let the run churn longer before termination,
  - (b) Condition E detects livelock but *continues* running (livelock-enduring = persisting despite classification), with a separate max_epochs cutoff, or
  - (c) The distinction is purely in governance style classification (livelock-enduring as a label for conditions that enter livelock without agents exiting).

---

### Q30 — Condition G coordinator: exit or refusal?

Q6 says the coordinator "stops submitting actions" at epoch t=8 (simulated loss). But "stops submitting actions" is ambiguous:
  - If the coordinator calls `wants_to_exit()` returning `True`, it exits permanently → orphaning of coordinator-scoped resources (per IX-2 Condition G pattern).
  - If the coordinator returns `None` from `propose_action()`, it's strategic refusal (NO_ACTION) — the coordinator is still "present" but inactive. No orphaning, but potential deadlock.

**Question**: Does the coordinator *exit* (triggering orphaning) or merely go silent (triggering deadlock)? The expected outcomes listed ("orphaning of coordinator-scoped processes or collapse, with no recovery") suggest exit. Please confirm.

---

### Q31 — Condition H: Silent agent resume or permanent?

Q18 says A2 goes silent at epoch 6 for 6 epochs. This raises:
  - Does A2 resume normal behavior at epoch 12?
  - Does A2 continue to call `wants_to_exit()` returning `False` during silence? (If it returns `True`, it's exit not silence.)
  - Does A2 still receive observations during silence?

**Question**: Confirm: A2 remains active (does not exit), continues receiving observations, but returns `None` from `propose_action()` and `None` from `compose_message()` during epochs 6–11, then resumes normal strategy at epoch 12. Is that correct?

---

### Q32 — Exit schedules for Conditions C and D

Condition C (Exit-Normalized) expects "regular exit events with authorized handoff." Condition D (Exit-Unprepared) expects "exit without authority handoff."

**Question**: Which agents exit and at which epochs?
  - Condition C: presumably one agent performs a state-handoff write and then exits at a fixed epoch. Which agent, which epoch, and is there a second exit later?
  - Condition D: presumably one agent exits abruptly (no handoff write). Which agent, which epoch?

---

### Q33 — Condition F collapse trigger

The spec says "explicit collapse triggers" for Condition F (Collapse Acceptance). In IX-2, collapse occurred when all agents exited.

**Question**: What triggers collapse in Condition F? Is it:
  - (a) all 4 agents exit sequentially over successive epochs,
  - (b) a specific state condition (e.g., K_TREASURY reaches 0) causes agents to exit, or
  - (c) agents are designed to exit after some number of failed action attempts?

What is the exit schedule?

---

### Q34 — Governance classifier threshold values

Q7 gives *example* thresholds (refusal_rate ≥ 0.70, progress_rate ≥ 0.40, exit_rate ≥ 0.10) with "e.g." qualifier. These need to be frozen in the preregistration.

**Question**: Are these the actual threshold values to freeze, or should different values be used? Also, the "overlap" metric for execution-biased classification is undefined. What is the overlap metric and its threshold?

---

### Q35 — Conditions I and J: structure and scope

Q17 calls I and J "fault-injection microconditions." Do they use the same structure as A–H (4 agents, 6 keys, 30 epochs), or are they shorter diagnostic probes? Do they reuse an existing condition's authority allocation with a fault overlay?

**Question**: For Conditions I and J:
  - What is the base authority allocation? (Same as Condition B? A? Custom?)
  - What is max_epochs? (30, or shorter since they're fault probes?)
  - What is the expected epoch of fault injection?
  - Is the PASS criterion simply "IX3_FAIL token emitted" (for I) or "refusal blocks reclamation" (for J)?

---

### Q36 — K_LOG semantics under flat key-value store

K_LOG is described as "public institutional log" and is a shared contention surface. But the WorldState schema is a flat key-value store where writes overwrite values. A "log" implies append semantics, which the flat store doesn't support.

**Question**: Is K_LOG simply a string value that gets overwritten (latest write wins), or does it need append semantics? If overwrite, what does a typical K_LOG write look like? If append, does the WorldState schema need to support array/list values?

---

### Q37 — FAILURE_FREE_GOVERNANCE evaluation window

Q8 says `progress_rate ≥ 0.40 over the final 10 epochs`. With max_epochs=30, this looks at epochs 20–29. But what if a condition achieves high progress for 20 epochs and then deadlocks at epoch 21? The final 10 epochs would show progress_rate = 0, so it wouldn't trigger the failure-free check.

**Question**: Is the "final 10 epochs" window the right check, or should it be "any contiguous 10-epoch window" or "overall progress_rate"? The intent seems to be "no governance style can sustain progress without ever incurring a failure mode," which suggests a whole-run check rather than a tail window.

---

### Q38 — Deadlock threshold M=2 vs. single-epoch detection

Q9 sets deadlock detection at M=2 consecutive epochs of no jointly admissible actions. But IX-2 detected deadlock immediately (single epoch, M=1 effectively). With M=2, Condition A (refusal-dominant) might produce false non-deadlock at epoch 0 if a single agent happens to have an admissible action that epoch.

**Question**: Is M=2 the intended threshold, or should deadlock detection remain immediate (M=1) as in IX-2? If M=2, is the intent to distinguish "transient blockage" from "structural deadlock"?

---

### Q39 — Agent strategy profiles per condition

The answers establish that agents may be *designed* to instantiate governance postures (Q15). But the specific strategy profiles are unspecified. For example:
  - Condition A agents: do they all attempt to write the same contested key every epoch (guaranteed interference)?
  - Condition B agents: do they each exclusively target their assigned partition?
  - Condition E agents: do they repeat the same interfering actions without adaptation?

**Question**: Should the preregistration freeze agent strategy profiles as pseudocode/behavioral descriptions per condition (as IX-2 did with named agent classes), or is this left to implementation discretion within the authority allocation constraints?

---

### Q40 — Per-condition PASS metric bands for all conditions

Q16 gives an example for Condition A. We need the complete set for preregistration.

**Question**: What are the PASS predicates (terminal classification + metric bands) for each of the 10 conditions? Even approximate bands would help — they can be tightened during preregistration drafting.

---

**End of Round 2 — 15 follow-up questions (Q26–Q40)**

---

## Round 3 (Follow-ups from Round 2 Answers)

### Q41 — Condition B and FAILURE_FREE_GOVERNANCE tension

Condition B PASS requires: no deadlock, no livelock by epoch 30, `progress_rate ≥ 0.40`, `write_overlap_rate ≤ 0.20`. Q40 notes it "must still not qualify as FAILURE_FREE_GOVERNANCE under Q37."

But the Q37 FAILURE_FREE_GOVERNANCE check fires when there exists *any* contiguous 10-epoch window with `progress_rate_window ≥ 0.40` AND the run has zero deadlock, zero livelock, zero orphaning, zero collapse. Condition B's PASS predicate *exactly satisfies* these criteria: high progress, no terminal failures, no orphaning (disjoint allocation, no exits).

**Question**: How does Condition B avoid triggering FAILURE_FREE_GOVERNANCE? The only escape I see is if Condition B *must* incur at least one failure mode (e.g., an orphaning event, or a late-stage deadlock). Should the Condition B PASS predicate require at least one failure event (orphan, deadlock, or livelock)? Or does the authority allocation need a deliberate fragility that guarantees *some* failure by epoch 30?

---

### Q42 — Condition A authority allocation: guaranteed deadlock path

Condition A has all 4 agents holding ALLOW for K_POLICY and K_LOG (guaranteed Pass-2 interference if ≥2 write the same key). A0/A1 have DENY on K_TREASURY, A2/A3 have DENY on K_REGISTRY. A0 has ALLOW on K_OPS_A, A1 on K_OPS_B.

If agents A0 and A1 write to their exclusive OPS keys (no interference), they'll make progress on those keys every epoch. That would give `progress_rate > 0` potentially violating the `progress_rate ≤ 0.10` band unless the strategy prevents it.

**Question**: Should Condition A agents be designed to *only* attempt writes on contested keys (K_POLICY, K_LOG) and never use their OPS_A/OPS_B authorities? Or should the OPS ALLOW authorities be removed from Condition A's allocation entirely to guarantee the refusal-dominant posture structurally rather than relying on strategy choices?

---

### Q43 — Condition E livelock-enduring: agent LLOCK_ACK mechanism

Condition E PASS requires `LLOCK_ACK:` to appear in K_LOG at least once after livelock detection. But look at the authority allocation: A2 and A3 have DENY on K_POLICY, while A0 and A1 have ALLOW on K_POLICY. A2 and A3 have ALLOW on K_LOG.

The livelock pattern is: agents keep attempting K_POLICY writes which are blocked by DENY. But who writes the `LLOCK_ACK:` to K_LOG? If A2 or A3 attempt it, they can succeed (they hold ALLOW on K_LOG). But this is a *state change* — which breaks the livelock "no state key changed" criterion.

**Question**: If an agent writes LLOCK_ACK to K_LOG, that changes state, which resets the livelock counter. This creates a paradox: the agent must acknowledge livelock (state change) while the system must remain in livelock (no state change). How do you resolve this? Options:
  - (a) The LLOCK_ACK write is a special "audit write" that doesn't count as a state change for livelock detection purposes,
  - (b) The livelock flag is latched — once set, it stays set regardless of subsequent state changes, or
  - (c) The LLOCK_ACK check is dropped and livelock endurance is measured purely by the run continuing past detection without exits.

---

### Q44 — Condition G orphaning detection for non-exclusive keys

In IX-2, orphaning was detected when the sole ALLOW holder for a scope exited. In Condition G, A0 is the sole ALLOW holder for K_REGISTRY and K_LOG. When A0 exits at epoch 8, those keys become permanently non-writable.

But the current `DeadlockClassifier.detect_orphaning()` from IX-2 checks if an *exited* agent was the sole `get_allow_holders()` for a *state key*. This should generalize cleanly since the authority store API already supports it.

**Question**: Confirm that orphaning detection generalizes to 6 keys unchanged — specifically, after A0 exits in Condition G, the harness should detect `ORPHANING_PRESENT` for K_REGISTRY and K_LOG because `get_allow_holders("K_REGISTRY")` returns `{}` (empty set, since A0 was the sole holder and has exited). Is that the correct detection path?

---

### Q45 — Condition H: what constitutes "recovery after resumption"?

Condition H PASS says "recovery after resumption is acceptable" (when A2 resumes at epoch 12). But how is recovery distinguished from FAILURE_FREE_GOVERNANCE? If A2 resumes and normal progress continues for epochs 12–29 (18 epochs, easily a 10-epoch window with progress_rate ≥ 0.40), doesn't the Q37 check fire?

**Question**: Does Condition H need to incur at least one failure event during the silence window (epochs 6–11) that persists — e.g., deadlock during silence that doesn't fully resolve — to avoid triggering FAILURE_FREE_GOVERNANCE? Or is the silence-induced progress gap itself sufficient to prevent any 10-epoch window from hitting 0.40?

---

### Q46 — Condition J: who submits the reclamation action?

Q35 says the harness "injects" a cleanup/reclaim action at epoch 4. But actions in the IX-2 model are always submitted by agents via `propose_action()`. If the harness injects an action directly (bypassing RSA interface), that's itself a deviation from the agent model.

**Question**: Is the reclamation action in Condition J:
  - (a) submitted by one of the remaining agents (A0/A1/A2) who attempts `K_OPS_A = "free"` citing no valid authority (should fail Pass-1),
  - (b) submitted by the harness as a synthetic agent action (which is the "tooling decides" pattern being tested), or
  - (c) a modification to the authority store (injecting a new ALLOW for K_OPS_A post-epoch-0)?

If (b), then the test validates that the kernel correctly refuses harness-injected actions. If (a), it validates that agents can't reclaim orphaned resources without authority.

---

### Q47 — Condition I: what does "auto-accept action" look like?

Q35 says the harness injects an action "as if client auto-accepted without any agent proposing it." This needs a concrete mechanism.

**Question**: Is the injected action in Condition I:
  - (a) an `ActionRequest` inserted into the action list for an agent that returned `None` from `propose_action()` (turning non-action into action),
  - (b) an `ActionRequest` with a synthetic `agent_id` not in the agent set, or
  - (c) a modification to an existing agent's action (changing its proposed_delta or scope)?

The detection mechanism needs to know what to look for. If (a), the detector checks whether any action was executed for an agent whose `propose_action()` returned `None`.

---

### Q48 — Per-epoch metric rolling windows: window size

Q20/Q34 mention per-epoch rolling metrics (`refusal_rate_window`, `progress_rate_window`). The window size is unspecified.

**Question**: What is the rolling window size for per-epoch metrics? Is it the same 10 epochs used in the FAILURE_FREE_GOVERNANCE check, or a different value?

---

### Q49 — Condition C: who succeeds A3 on K_REGISTRY/K_LOG/K_POLICY?

A3 holds ALLOW for K_REGISTRY, K_LOG, and K_POLICY. A3 writes a handoff record then exits at epoch 10. After exit, K_REGISTRY/K_LOG/K_POLICY are orphaned (A3 was the sole ALLOW holder for those keys).

The handoff sets state so another agent *knows* it should operate — but that agent lacks ALLOW authority for those keys. The "handoff" is purely informational. K_REGISTRY and K_LOG become permanently non-writable after A3 exits.

**Question**: Is this the intended outcome — that even an "exit-normalized" institution with handoff still suffers orphaning of the institutional surfaces? That would mean Condition C's expected outcome includes `orphan_events ≥ 1` (for K_REGISTRY/K_LOG/K_POLICY), which contradicts Q40's `orphan_events = 0` for K_OPS_A. Should the authority allocation give another agent (e.g., A1) standby ALLOW for K_REGISTRY/K_LOG to enable genuine operational continuity?

---

### Q50 — K_TREASURY writes: semantics of integer state

K_TREASURY starts at `100` (integer). When an agent writes to it, what does the write look like? The WorldState `apply_delta` does key-level overwrite. So `proposed_delta: {"K_TREASURY": 95}` would set it to 95.

**Question**: Are K_TREASURY writes simple overwrites (agent computes new value and writes it), or does the system need increment/decrement semantics? If overwrite, two agents writing `K_TREASURY` in the same epoch would interfere (Pass-2), which is the intended contention mechanism. Confirm this is correct.

---

### Q51 — Authority allocation: missing K_TREASURY ALLOW in several conditions

Looking at the allocations:
  - Condition A: A0 has DENY on K_TREASURY, A1 has DENY on K_TREASURY, but *no agent has ALLOW* on K_TREASURY.
  - Condition C: No agent has ALLOW on K_TREASURY.
  - Condition E: No agent has ALLOW on K_TREASURY.
  - Condition F: No agent has ALLOW on K_TREASURY.
  - Condition H: No agent has ALLOW on K_TREASURY.

A key with no ALLOW holders is permanently inert (no action can pass the closed-world capability check). This is fine if intentional — those conditions don't need K_TREASURY to be writable.

**Question**: Confirm that K_TREASURY is intentionally inert (no ALLOW holders) in Conditions A, C, E, F, and H. If unintentional, which agents should hold ALLOW?

---

### Q52 — Condition B: A3 has 3 ALLOW authorities — is it a single point of failure?

In Condition B, A3 holds ALLOW for K_POLICY, K_REGISTRY, *and* K_LOG (the only agent with authority for any institutional key). If A3 exits or goes silent, all three institutional keys become orphaned. But Condition B has no scheduled exit.

However, this means Condition B is *structurally fragile* — one unplanned A3 failure orphans 3 of 6 keys. Is this the intended "fragility under exit" mentioned in the spec for execution-dominant governance?

**Question**: Is the A3 concentration in Condition B a deliberate single-point-of-failure design to demonstrate execution-biased fragility, or should institutional keys be distributed among agents?

---

### Q53 — Communication in Condition G: message behavior after coordinator exit

Communication is enabled in Condition G. After A0 (coordinator) exits at epoch 8, can remaining agents A1/A2/A3 still exchange messages? The IX-2 model says exited agents emit no further messages but doesn't restrict messages among survivors.

**Question**: Confirm that after A0 exits in Condition G, agents A1/A2/A3 can still exchange messages (broadcast among the active agent set). This is important because the remaining agents might attempt to reorganize via messages — which is lawful as long as no authority transfer occurs.

---

---

**End of Round 3 — 13 follow-up questions (Q41–Q53)**

---

## Round 4 (Final convergence — 4 questions from Round 3 answers)

### Q54 — progress_rate formal definition

`progress_rate` appears in PASS predicates for A, B, E, and H but has no formal definition. Candidates:

- **(a)** `(epochs with ≥1 successful state change) / total_epochs`
- **(b)** `(total successful writes) / (total attempted writes)`
- **(c)** `(total keys changed across all epochs) / (total_keys × total_epochs)`

The choice matters: in Condition A (4 agents, 2 keys), if one agent's K_LOG write occasionally succeeds, option (a) could yield ~0.10 while (b) yields ~0.03. Condition B depends on whether "progress" counts OPS or institutional keys only (per Q41 scope).

**Question**: Which definition is binding, and does it scope to all 6 keys or institutional keys only? (If institutional only, Condition B's disjoint OPS throughput vanishes from the metric and its `progress_rate ≥ 0.40` may be unreachable.)

---

### Q55 — Condition E: LLOCK_ACK write contradicts progress_rate = 0

Condition E PASS requires **both**:
  1. `progress_rate = 0`
  2. `"LLOCK_ACK:" in K_LOG` (at least once after latch)

But the LLOCK_ACK write to K_LOG is a successful state change (K_LOG goes from `""` to `"LLOCK_ACK:..."`) — which makes `progress_rate > 0` under any definition.

**Question**: How do you reconcile these? Options:
  - **(a)** Redefine progress_rate to exclude K_LOG (audit key doesn't count as "governance progress")
  - **(b)** Change Condition E PASS to `progress_rate ≤ epsilon` (e.g., ≤ 0.05) to tolerate the single ACK write
  - **(c)** Drop the `progress_rate = 0` requirement and replace with `institutional_progress_rate_excluding_LOG = 0` plus the LLOCK_ACK requirement

---

### Q56 — Condition H: institutional deadlock not structurally guaranteed during silence

Q45 binding says epochs 6–11 must contain at least one institutional deadlock event. But check the allocation:

- A0: ALLOW K_POLICY — can write K_POLICY alone (if A1 doesn't) → succeeds → institutional progress
- A1: ALLOW K_POLICY — same
- A3: ALLOW K_LOG — can write K_LOG alone → succeeds → institutional progress
- A2: silent (returns None)

Since A3 is the sole K_LOG ALLOW holder, every A3 write to K_LOG succeeds uncontested. That's guaranteed institutional progress during silence — no deadlock possible.

**Question**: To make institutional deadlock structurally possible during silence, one of:
  - **(a)** Remove A3's K_LOG ALLOW in Condition H (makes K_LOG inert during silence, but then A3 can do nothing at all)
  - **(b)** Add a second agent with K_LOG ALLOW so interference is possible
  - **(c)** Accept that H doesn't guarantee institutional deadlock during silence — revise the Q45 requirement to "reduced institutional progress during silence" instead of "deadlock event", relying on strategy-frozen interference on K_POLICY between A0/A1 plus A3's limited K_LOG contribution staying below the `progress_rate_window ≤ 0.10` threshold

---

### Q57 — Livelock/deadlock detector scope: all keys or institutional only?

Q41 scoped FAILURE_FREE_GOVERNANCE to institutional keys only. But the livelock detector (N=5 consecutive no-change epochs) and deadlock detector (M=1) still reference "state keys" generically.

If livelock checks all 6 keys: a write to K_OPS_A resets the livelock counter, even though OPS is not governance. If livelock checks institutional keys only: OPS writes are invisible to the detector, and an agent could churn OPS without affecting livelock status.

**Question**: Should the livelock/deadlock detectors scope to:
  - **(a)** All 6 keys (simple, but OPS noise can mask governance livelock)
  - **(b)** Institutional keys only (consistent with Q41, but conditions with OPS-only activity never trigger livelock even if governance is stuck)

For Condition E specifically: all agents have DENY on OPS keys, so the scoping choice doesn't matter there. But for Conditions B, D, and G (which have active OPS), the choice determines whether OPS throughput masks governance failures.

---

**End of Round 4 — 4 follow-up questions (Q54–Q57)**

---

## Round 5 (Final convergence — 3 questions from Round 4 answers)

### Q58 — Condition B still triggers FAILURE_FREE_GOVERNANCE (surviving contradiction)

The Q41 fix (institutional-only scope) and Q54 fix (progress_rate = institutional) combine to make B's PASS unreachable:

1. B PASS requires: no deadlock, no livelock, institutional `progress_rate ≥ 0.40`, no IX3_FAIL tokens.
2. A3 is the sole ALLOW holder for K_POLICY, K_REGISTRY, K_LOG → every A3 institutional write is uncontested → institutional progress easily hits 0.40+.
3. B has no exits → no orphaning. No shared institutional keys → no interference → no deadlock/livelock.
4. FAILURE_FREE_GOVERNANCE fires (no failures + institutional progress ≥ 0.40 in a 10-epoch window) → IX3_FAIL emitted → B PASS blocked.

The same issue applies to **Condition C's success path**: after Q49's standby-ALLOW fix, A1 sustains institutional progress post-handoff with no orphaning. Exit alone is not in {deadlock, livelock, orphaning, collapse}, so FAILURE_FREE_GOVERNANCE fires for C too.

**Question**: How do you break the contradiction? Options I see:

- **(a) Structural fix for B**: Add a second agent (e.g., A2) with ALLOW on K_LOG, creating occasional institutional interference. B's PASS changes from "no deadlock" to "no persistent deadlock" (e.g., `institutional_deadlock_epochs ≤ 5`). The interference events protect B from FAILURE_FREE_GOVERNANCE.
- **(b) Add "no exits" to FAILURE_FREE_GOVERNANCE criteria**: This protects C, D, F, G (all have exits). B, A, E, H still checked — but A has deadlock, E has livelock, H has institutional stall. Only B remains unprotected, so (a) is still needed for B.
- **(c) Exempt specific conditions from the falsification check**: FAILURE_FREE_GOVERNANCE only runs on conditions *designed* to attempt failure-free governance. But this weakens the falsification criterion to a tautology.
- **(d) Redefine FAILURE_FREE_GOVERNANCE to require multi-agent institutional participation**: A single-agent institutional writer (autocracy) doesn't count as "governance" for falsification. Only runs where ≥2 agents write institutional keys AND have no failures trigger the check. B's autocratic design structurally avoids it.

My recommendation: **(a)+(b)** — add A2 K_LOG ALLOW in B to create real institutional interference, AND add "no exits" to FAILURE_FREE_GOVERNANCE to protect C's success path. This keeps the falsification check honest (not exemption-based) while ensuring every condition is structurally reachable.

---

### Q59 — write_overlap_rate scope after Q54

Q54 binds `progress_rate` to institutional keys. Should `write_overlap_rate` follow the same scoping?

In Condition B, A0/A1 share K_OPS_A and A2/A3 share K_OPS_B — so OPS overlap is guaranteed. If `write_overlap_rate` is all-keys, B's `≤ 0.20` bound constrains OPS interference. If institutional-only, B's institutional overlap is 0 (A3 sole writer) — making the `≤ 0.20` constraint vacuous.

**Question**: Is `write_overlap_rate` scoped to:
- **(a)** All 6 keys (OPS overlap counts, constrains scheduling)
- **(b)** Institutional keys only (consistent with Q54, but vacuous for B)
- **(c)** Separately reported: `write_overlap_rate(K_INST)` and `write_overlap_rate(K_OPS)` with condition-specific predicates referencing the relevant one

---

### Q60 — Agent strategy class names: freeze now or defer to prereg draft?

Q39 says "prereg must freeze strategy profiles as named classes." The Round 3 summary mentions strategy classes but no names or pseudocode have been provided yet.

For preregistration, each condition needs: agent × strategy-class-name × behavioral description (what key(s) the agent targets each epoch, how it responds to failures/communication/exit events).

**Question**: Should I draft proposed strategy class names and per-agent assignments as part of the preregistration document (for your review), or do you want to provide them in the next answer round? Examples of the kind of names I'd propose:

- `AlwaysContestPolicy` — always writes K_POLICY (Condition A agents)
- `DisjointOpsWriter` — writes assigned OPS key (Condition B A0/A1/A2)
- `InstitutionalSteward` — writes K_POLICY/K_REGISTRY/K_LOG in rotation (Condition B A3)
- `HandoffThenExit` — writes handoff record then exits (Condition C A3)
- `SilentObserver` — returns None during silence window (Condition H A2)
- `LivelockAcknowledger` — writes LLOCK_ACK after latch (Condition E agents with K_LOG ALLOW)

---

**End of Round 5 — 3 follow-up questions (Q58–Q60)**

---

## Round 6 (2 surviving issues)

### Q61 — Condition B: pigeonhole shows FAILURE_FREE_GOVERNANCE fix is insufficient

Q58's interference fix for B does not break FAILURE_FREE_GOVERNANCE. Here's why:

B PASS requires `institutional_epoch_progress_rate ≥ 0.40` over the full 30-epoch run → ≥ 12 institutional-progress epochs. There are 21 overlapping 10-epoch windows (epochs 1–10, 2–11, ..., 21–30). Each progress epoch appears in exactly 10 windows. Total progress-epoch-appearances = 12 × 10 = 120. Average per window = 120/21 ≈ 5.7. By pigeonhole, the best window has ≥ 6 progress epochs → window rate ≥ 0.60.

**Any full-run rate ≥ 0.40 mathematically guarantees the existence of a 10-epoch window ≥ 0.40.** The interference adds noise but cannot break this relationship. So FAILURE_FREE_GOVERNANCE still fires for B whenever B passes (assuming no deadlock/livelock/orphaning/collapse — and the K_LOG interference doesn't create any of those because A3 still writes K_POLICY/K_REGISTRY uncontested).

**The only clean escapes I see:**

- **(a) Add "institutional livelock or institutional deadlock must occur at least once" to the FAILURE_FREE_GOVERNANCE negation criteria.** If any livelock/deadlock event was emitted *even once* during the run (even if later resolved), the run is not failure-free. Then B's strategy is designed so K_LOG interference creates a brief institutional livelock burst (N=5 consecutive K_INST-no-change epochs) which latches a `livelock_occurred = True` flag. After that burst, A3 resumes institutional writes and achieves high progress. The livelock-occurred flag prevents FAILURE_FREE_GOVERNANCE.

  This requires A3 to pause all institutional writes for exactly 5 epochs while A2 writes K_LOG (interfering with... nobody, since A3 paused). Hmm, that means K_LOG *succeeds* during A3's pause → that's institutional progress → livelock counter doesn't reach 5.

  Revised: A3 pauses institutional writes for 5 epochs AND A2 also pauses K_LOG writes → no institutional action attempts → deadlock (no jointly admissible action changes K_INST given frozen strategies). After 5 epochs, both resume. This works but it's artificial — a 5-epoch "dead zone" baked into the strategy.

- **(b) Replace B's FAILURE_FREE_GOVERNANCE escape with a hard exclusion**: FAILURE_FREE_GOVERNANCE is only checked on conditions with `governance_style = "consensus"` or similar multi-party styles. Single-steward conditions are structurally excluded.

- **(c) Remove the 10-epoch window from FAILURE_FREE_GOVERNANCE entirely.** Instead, define failure-free as: `exit_count = 0 AND institutional_deadlock_epochs = 0 AND institutional_livelock_epochs = 0 AND orphan_events = 0 AND collapse_flag = False AND institutional_write_overlap_epochs = 0`. The zero-overlap requirement means B (which has mandatory institutional overlap from A2) never qualifies as failure-free.

**My recommendation: (c)**. It's clean, structural, and uses the binding data from Q58/Q59 (B must have institutional_write_overlap ≥ 0.05). Any condition with *any* institutional interference, *any* exit, *any* deadlock/livelock, *any* orphaning, or *any* collapse is definitionally not "failure-free governance." The window-based progress check becomes unnecessary.

---

### Q62 — Condition A: deadlock vs livelock classification

After Q42's allocation revision, Condition A has 4 agents all with ALLOW for K_POLICY and K_LOG. With strategy `ContestPolicyAlways`, all agents write K_POLICY every epoch → Pass-2 interference → no K_POLICY change. But K_LOG has no writers (nobody's strategy targets it) → no K_LOG change.

Under Q57's detector definition:
> "Institutional deadlock at epoch e iff: (1) no jointly admissible actions exist that would change any key in K_INST, and (2) no key in K_INST changed in epoch e."

Criterion (1) is problematic: a jointly admissible action profile *does exist* (e.g., A0 writes K_LOG while A1/A2/A3 write K_POLICY → K_LOG changes). The agents just don't *choose* it. So structurally, deadlock is false. What's happening is interference-induced **livelock** (agents attempt writes, all fail due to collision).

But Condition A's PASS predicate says `STATE_DEADLOCK` by epoch ≤ 30.

**Question**: Should Condition A's terminal classification be `STATE_LIVELOCK` (not deadlock), since agents have ALLOW authority but strategies produce mutual interference? Or should the deadlock definition be amended to be **strategy-aware** — i.e., "no jointly admissible action profile exists *given frozen strategies*"?

If strategy-aware: deadlock means "given what agents will actually do, no state change is possible." If authority-only: deadlock means "given what agents *could* do (any admissible action), no state change is possible."

The choice matters for the claim: authority-only deadlock means the *structure* prevents progress (strong claim). Strategy-aware deadlock means the *behavior* prevents progress (weaker, could be "fixed" by changing strategy).

---

**End of Round 6 — 2 follow-up questions (Q61–Q62)**
