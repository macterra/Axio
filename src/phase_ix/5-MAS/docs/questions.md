# IX-5 MAS — Pre-Preregistration Questions

These questions identify every underspecified parameter in the IX-5 spec and instructions that must be resolved before the preregistration can be frozen. They are organized by topic area.

---

## A. Agent Model and Key Topology

**Q-A1.** IX-3 and IX-4 both used exactly 4 agents (A0–A3) across all conditions. Does IX-5 also use a fixed 4-agent setup for all 6 conditions, or does agent count vary per condition? (Condition F "zombie peer interaction" might work differently with 2 vs 4 agents.)

**Q-A2.** IX-3 used K_INST = {K_POLICY, K_TREASURY, K_REGISTRY, K_LOG} (4 keys). IX-4 reduced to K_INST = {K_POLICY, K_TREASURY, K_REGISTRY} (3 keys, K_LOG excluded). Which K_INST scope does IX-5 use? The choice matters because:
- 3-key K_INST makes partitioning exact for 3 agents but awkward for 4.
- 4-key K_INST makes partitioning possible for 4 agents (one key each).
- Adding K_OPS keys to K_INST would change the semantics entirely.

**Q-A3.** Does IX-5 use DENY artifacts (as IX-3 did) or only ALLOW (as IX-4 did)? DENY artifacts would let conditions test asymmetry via explicit exclusion rather than just withholding.

**Q-A4.** All authority in IX-5 is baseline (epoch 0, immutable). There is no injection engine. Should the authority store revert to IX-3's epoch-0-checked `AuthorityStore`, or continue using IX-4's source-blind `IPAuthorityStore`? Since there's no injection, source-blindness is moot — but using the same store simplifies the import bridge.

---

## B. Communication and Observation

**Q-B1.** The spec identifies "observation surface" as one of the 4 axes under study (§7.4: "full authority visibility vs minimal capability awareness"). Does this mean:
- (a) Some conditions enable Message passing and others disable it (as IX-3 did)?
- (b) Some conditions vary what's visible in the Observation (e.g., whether agents can see other agents' authority holdings)?
- (c) Both?

**Q-B2.** If observation surface varies, do we use IX-4's `IPObservation` (with `available_authorities` field showing the agent's own authority IDs) for all conditions, or do some conditions deliver a reduced observation (e.g., no authority visibility, or visibility of *other* agents' authorities)?

**Q-B3.** The instructions §5 say "no shared sovereign clock." The epoch loop is inherently a shared clock (all agents observe, act, and get evaluated synchronously in each epoch). Is this a contradiction, or does the constraint mean something narrower — e.g., no timeout-based resolution, no priority-by-action-order within an epoch? (IX-3 and IX-4 both used synchronous epochs without issue.)

---

## C. Condition Specifications

### Condition A: Symmetric Sovereign Peers

**Q-C1.** "All agents share identical institutional authority" — does this mean all 4 agents hold ALLOW for all K_INST keys? Or all agents hold ALLOW for the same subset (e.g., just K_POLICY)? The IX-4 post-flood state (Condition D) had all agents holding all keys and produced capture by the most persistent strategy. What makes IX-5 Condition A different from that post-flood state?

**Q-C2.** Do agents also hold ALLOW for K_OPS and K_LOG, or only K_INST keys? Full authority (all 6 keys for all agents) vs institutional-only changes the interference pattern significantly.

**Q-C3.** What strategy classes are assigned? All the same strategy (like IX-3 Condition A's 4× ContestPolicyAlways)? Or a mix? The expected outcome is "livelock or deadlock" — a mix of strategies would be more interesting but needs specification.

### Condition B: Partitioned Peers

**Q-C4.** "Authority divided across disjoint domains" — how exactly? Options include:
- (a) Each agent gets exactly one exclusive K_INST key (requires ≥3 agents if K_INST has 3 keys).
- (b) Each agent gets a non-overlapping subset of all 6 keys.
- (c) Agents are split into 2 groups, each group holding a disjoint set of keys.
Which partition scheme?

**Q-C5.** What strategies should partitioned agents use? An agent with exclusive authority over its key has no interference — it always succeeds. The "brittle boundaries" expected outcome suggests the interesting dynamics happen at the boundaries. Should strategies target keys outside their authority (and get refused)?

**Q-C6.** If agents only target their own keys, the condition would show zero interference and zero failure. Is that the intended baseline ("coexistence via separation") or should agents also attempt cross-boundary writes?

### Condition C: Boundary Conflict

**Q-C7.** "Partial overlap on institutional keys" — which keys overlap and which are exclusive? A concrete layout is needed. For example:
- A0 holds {K_POLICY, K_TREASURY}, A1 holds {K_TREASURY, K_REGISTRY}, etc.?
- Or a 2-vs-2 partition with one contested key?

**Q-C8.** Do overlapping agents target the contested key specifically, or do they target any key they hold authority for? The strategy determines whether overlap produces conflict or coexistence.

### Condition D: Persistent Asymmetry

**Q-C9.** "One agent has broader baseline authority" — how much broader? Options:
- (a) One agent holds all K_INST keys; others hold one key each.
- (b) One agent holds all 6 keys; others hold K_LOG + K_OPS only.
- (c) One agent holds 3 K_INST keys; others hold 1 K_INST key each (with overlap on one key).

**Q-C10.** The expected outcome is "capture without injection." IX-4's CaptureClassifier required `capture_injected_citation ≥ 0.60`, which is meaningless without injection. Does IX-5 need a modified domination classifier that detects capture by *baseline* authority advantage rather than injected-citation rate? What's the formal definition?

**Q-C11.** "Persistence asymmetry" (spec §7.2) says agents differ in "endurance, not privilege." Is endurance just having more authority (so you succeed more often), or is there a separate persistence mechanism (e.g., different exit thresholds, different maximum epochs)?

### Condition E: Exit Cascades

**Q-C12.** Which agent exits? At what epoch? Is the exit triggered by a fixed schedule (like IX-3 Condition C's epoch-10 exit) or by a state condition (e.g., "exit after 3 consecutive refusals")?

**Q-C13.** The exiting agent presumably holds exclusive authority over at least one K_INST key, so exit produces orphaning. What's the authority layout? Does a second agent exit after observing the first exit's orphaning effects (hence "cascade")?

**Q-C14.** Does the condition test a single exit event or a multi-exit cascade? "Exit cascades" (plural) implies a chain reaction. If so, how many exits and what triggers each one?

**Q-C15.** Do remaining agents have any strategy response to observed orphaning, or do they continue their fixed strategy regardless?

### Condition F: Zombie Peer Interaction

**Q-C16.** How does governance collapse get latched without injection? In IX-4, collapse came from livelock or persistent deadlock. In IX-5, is Condition F just a long-running symmetric deadlock that eventually triggers the governance collapse detector (like Condition A but with enough epochs)?

**Q-C17.** What distinguishes Condition F from Condition A running long enough to collapse? Is the authority layout different? Or is F's purpose specifically to observe post-collapse behavior while A's purpose is to observe the pre-collapse interference pattern?

**Q-C18.** If F runs long enough for collapse + zombie window, it needs more max_epochs than A. What's the relationship between max_epochs for A vs F?

---

## D. Strategy Design

**Q-D1.** How many new strategy classes does IX-5 need? The spec mentions behaviors like "attempting coordination or refusing it," "exerting pressure or withdrawing," and "modeling or predicting behavior." These imply strategies more complex than IX-3/IX-4's simple deterministic ones. But complexity must remain deterministic (no RNG). What strategy behaviors are required?

**Q-D2.** Can IX-5 reuse any IX-3/IX-4 strategies directly? Candidates:
- `ContestPolicyAlways` (IX-3/IX-4) — always targets K_POLICY
- `RefusalHardliner` (IX-4) — only cites epoch-0 authority (but there's no injection, so this is equivalent to normal citation)
- `Opportunist` (IX-4) — cycles through available keys
- `HandoffRecordThenExit` (IX-3) — exits at a specified epoch
- `StandbyInstitutional` (IX-3) — activates after another agent exits

**Q-D3.** Does IX-5 need a "boundary-aware" strategy that targets contested keys specifically? For Condition C, agents need to demonstrate conflict at overlapping boundaries.

**Q-D4.** Does IX-5 need a "domination-seeking" strategy (like IX-4's CaptureSeeker) that exploits asymmetric authority? For Condition D.

**Q-D5.** Does IX-5 need a "cascade-exit" strategy that exits in response to observed orphaning? For Condition E.

**Q-D6.** The spec mentions "modeling or predicting behavior" (instructions §4.1). Does any strategy need to model other agents, or is this just permission (i.e., strategies *may* but don't *have to*)?

---

## E. Detectors and Classifiers

**Q-E1.** IX-4 defined 5 detectors: InstitutionalDeadlock (M=2), InstitutionalLivelock (L=5), GovernanceCollapse (D=5), Orphaning, AgentCollapse. Does IX-5 reuse all of these with the same thresholds?

**Q-E2.** What is the IX-5 deadlock threshold M? (IX-3: M=1, IX-4: M=2.)

**Q-E3.** The spec §9.1 says IX-5 tests whether "hierarchy emerges via persistence advantage, tooling salience, action frequency, scope breadth." This implies a new **hierarchy emergence detector**. What is its formal definition? Options:
- (a) Same as IX-4's CaptureClassifier but without the injected-citation requirement.
- (b) A new metric: e.g., `hierarchy_index(X) = execution_rate(X) / mean_execution_rate` — if one agent consistently succeeds while others fail.
- (c) Something else entirely.

**Q-E4.** The spec §9.3 mentions "sovereignty drift" — agents treating others as authoritative over time. In a deterministic system with fixed strategies, drift would need to be designed into a strategy (e.g., an agent that starts contesting but eventually yields). Is sovereignty drift a new detector, a classifier, or just an observation made in the report?

**Q-E5.** IX-5 §9 requires regime classification along 4 axes. Are these computed per-condition by a classifier, or are they descriptive labels assigned in the report? If computed, what's the formal definition for each axis?

**Q-E6.** Does IX-5 reuse IX-4's Capture, Dependency, and Zombie classifiers? Without injection:
- CaptureClassifier's `capture_injected_citation` is undefined. Needs redefinition.
- DependencyClassifier is injection-specific. Drop or redefine?
- ZombieClassifier works as-is (post-collapse writes).

**Q-E7.** Does IX-5 need a new **domination classifier** distinct from capture? The spec distinguishes domination ("one agent's authority structurally outweighs others, without kernel endorsement") from capture (which required injection in IX-4). What's the formal metric?

---

## F. PASS/FAIL Semantics

**Q-F1.** Does IX-5 follow the same PASS/FAIL pattern as IX-4?
- `IX5_PASS iff no IX5_FAIL tokens AND no INVALID_RUN tokens AND all 6 conditions executed AND all classifiers computed AND replay determinism verified`
- If yes, what are the specific IX5_FAIL token types?

**Q-F2.** The instructions §11–§12 define pass/fail criteria narratively. The IX-4 preregistration formalized these into explicit token types:
- `IX4_FAIL / IMPLICIT_SOVEREIGNTY`
- `IX4_FAIL / TOOLING_SOVEREIGNTY`
- `IX4_FAIL / AUTHORITY_THEFT`
- `IX4_FAIL / KERNEL_BREACH`

For IX-5, what are the equivalent tokens? The instructions mention:
- `IX5_FAIL / IMPLICIT_ARBITRATION` (§5)
- `IX5_FAIL / TOOLING_SOVEREIGNTY` (§6)
- `IX5_FAIL / KERNEL_BREACH` (§7)
Are these the complete set, or are there additional IX5_FAIL types?

**Q-F3.** The spec §12 says "hierarchy without declaration is failure." Is undeclared hierarchy an IX5_FAIL or an INVALID_RUN? How is "declaration" defined in a deterministic system? (Strategies don't "declare" anything — they just act.)

**Q-F4.** The instructions say "If coexistence requires arbitration, IX-5 fails. If coexistence collapses honestly, IX-5 passes." But all conditions are deterministic with fixed strategies — arbitration can only emerge if we accidentally built it into the harness or kernel. Is the PASS/FAIL distinction primarily about implementation correctness (no bugs introducing implicit arbitration) rather than about condition outcomes?

---

## G. Execution Parameters

**Q-G1.** What are the max_epochs per condition? IX-3 used 4–30, IX-4 used 26–35. IX-5 needs enough epochs for:
- Condition A: livelock detection (≥5 epochs for L=5)
- Condition E: exit + observation window
- Condition F: collapse latch + post-collapse zombie window

**Q-G2.** Does IX-5 use a fixed synthetic clock like IX-4 (`FIXED_CLOCK = 1750000000`)? Or a new value?

**Q-G3.** Does IX-5 have E_pre_max semantics? IX-4 used E_pre_max for state-triggered conditions. IX-5 has no injection, but Condition E might need a "window" before the exit event and a window after.

---

## H. Architectural Questions

**Q-H1.** IX-5 reuses the IX-2 kernel (evaluate_admissibility, WorldState, etc.) via the import bridge. Does IX-5 need its own `_kernel.py` bridge (like IX-4), or can it reuse IX-4's? The main question is whether IX-5 needs IPObservation/IPAuthorityStore or a different observation/store model.

**Q-H2.** The instructions §4 mandate "three physically distinct layers": Agent, Kernel, Audit. IX-3 and IX-4 both folded audit into the harness. Does IX-5 need a separate audit module, or is the existing pattern (harness records everything, results file is the audit trail) sufficient?

**Q-H3.** Does IX-5 need a new harness (`mas_harness.py`) or can it extend `ip_harness.py`? The main differences are:
- No injection engine
- Different condition builders
- Different/additional classifiers
- Possibly different observation model

A new harness seems cleaner given these differences.

---

## I. Scope and Relationship

**Q-I1.** IX-5 §13 says the licensed claim (if any) is of the form: *"Under non-sovereign constraints, multi-agent coexistence does not converge to harmony but to identifiable sovereignty interaction regimes with irreducible failure modes."* Is this the exact licensed claim, or a template to be refined during preregistration?

**Q-I2.** The spec §14 says IX-5 "closes the question: Can sovereignty coexist without lying?" Does this mean IX-5 is intended to be the final IX substage, or could there be IX-6+?

---

## J. Follow-Up Questions (Round 2)

*Based on gaps and tensions in the Round 1 answers.*

### Observation Surface Assignment

**Q-J1.** B1/B2 define OBS_FULL and OBS_MIN modes, but the answers never assign them to conditions. Which conditions use OBS_FULL and which use OBS_MIN? A natural mapping might be: conditions testing observation surface as a variable (e.g., Condition A or B run twice, once per mode) or one mode per condition. Please specify.

**Q-J2.** OBS_FULL delivers "other agents' public action/refusal/exit events." What is the concrete data structure? Options:
- (a) A new field on MASObservation (e.g., `peer_events: list[PeerEvent]` with agent_id, action_type, outcome, target_key per agent per epoch).
- (b) A richer world_state dict that includes a per-agent action log.
- (c) Something else.
The observation must not reveal authority holdings (per B2). But does it reveal which keys an agent *targeted* (which is a proxy for holdings)?

**Q-J3.** If messages are enabled in all conditions (B1), but no strategy is specified to *use* messages, does any agent actually call `compose_message()` with non-None content? Or is messaging "enabled but unused" (all agents return None)? If unused, what's the point of enabling it?

### Condition A Specifics

**Q-J4.** Condition A uses 4× ContestPolicyAlways on K_POLICY, with all agents holding all 4 K_INST keys. This means K_TREASURY, K_REGISTRY, and K_LOG are never targeted. The condition tests interference on exactly one key with full symmetric authority. Is this intentionally identical to IX-3 Condition A (same strategy, same outcome), or should the strategy mix be different to exercise the 4-key authority surface?

### Condition B Specifics

**Q-J5.** The two-phase strategy (OwnKeyOnly epochs 0–9, CrossBoundaryProbe epochs 10–29): during Phase 2, does the agent *continue* writing its own key AND additionally probe the cross-boundary key? Or does it *switch* to probing only (abandoning its own key)? If it switches, the agent's exclusive key becomes unwritten in Phase 2, which is a different dynamic than boundary conflict.

**Q-J6.** CrossBoundaryProbe attempts a write to a key the agent lacks authority for. The write will be refused at Pass-1 (no ALLOW artifact). Is the purpose purely to confirm refusal permanence and record the refusal pattern? Or is there an expected dynamic beyond "100% refusal rate on cross-boundary probes"?

### Condition C Specifics

**Q-J7.** A0 and A1 both hold {K_POLICY, K_LOG}. BoundaryContest targets K_POLICY. Who writes K_LOG? If neither agent targets K_LOG, it's an unused shared surface. If both agents sometimes target K_LOG, we need a strategy that alternates targets or has a secondary target. Please specify whether K_LOG is used and by what strategy logic.

### Condition D Specifics

**Q-J8.** A0's strategy is not specified. A0 holds all 4 K_INST keys. What strategy does A0 use? Options:
- (a) Opportunist-style cycling through all 4 keys (exercises breadth advantage).
- (b) ContestPolicyAlways (only uses K_POLICY, wasting the asymmetric advantage).
- (c) A new "AsymmetricExploiter" that targets whichever key it exclusively controls (i.e., keys that no other agent holds).
The choice determines whether structural domination actually manifests.

**Q-J9.** What strategies do A1, A2, A3 use in Condition D? Each holds exactly one K_INST key. Options:
- (a) OwnKeyOnly (write their exclusive key — no interference with A0 on those keys since A0 also holds them → Pass-2 conflict if same epoch).
- (b) ContestPolicyAlways (all target K_POLICY → A0 competes with 3 others on K_POLICY but can also write other keys).
- (c) Something else.

**Q-J10.** The DominationIndex threshold is `≥0.75` with at least one peer `≤0.05`. In Condition D, if A0 cycles through 4 keys while A1/A2/A3 each target their one key, A0 would interfere with each subordinate agent on their key (Pass-2 conflict) but also have 3 keys where subordinates don't target it. Does this produce DominationIndex ≥ 0.75 for A0? A worked example would clarify the expected metric value.

### Condition E Specifics

**Q-J11.** What strategies do A2 and A3 run *before* their exit epochs? Options:
- (a) OwnKeyOnly until exit epoch, then exit.
- (b) HandoffRecordThenExit (write a handoff record to their key before exiting, as in IX-3 Condition C).
- (c) Something else.
The answer says "scheduled exits" but doesn't specify pre-exit behavior.

**Q-J12.** StandbyInstitutional for A0/A1 "probes orphaned keys after exit epoch." But A0 holds K_POLICY and A1 holds K_TREASURY — neither holds authority for K_REGISTRY (orphaned when A2 exits) or K_LOG (orphaned when A3 exits). A probe write to K_REGISTRY without authority would be refused at Pass-1. Is this the intended observation (permanence of orphaning confirmed by refusal)? Or should A0/A1 hold some cross-authority so they can actually write to orphaned keys?

### Condition F Specifics

**Q-J13.** With all agents holding all K_INST keys and A0/A1 running ContestPolicyAlways on K_POLICY: livelock latches at epoch ≤5 (L=5 consecutive unchanged K_INST epochs). GovernanceCollapse latches immediately when livelock latches (since livelock_latched triggers collapse per §9.3). This means collapse fires around epoch 5, not epoch 20 as stated in G3. Is the "earliest allowed at epoch 20" a typo, or is there a mechanism to delay collapse (e.g., different detector thresholds, different strategy that produces some early progress)?

**Q-J14.** LogChatterAfterCollapse is "gated by collapse latch." How does the agent *know* collapse has latched? The agent only sees Observations (world_state, own_last_outcome). Options:
- (a) Agent infers collapse from sustained JOINT_ADMISSIBILITY_FAILURE outcomes (heuristic).
- (b) MASObservation includes a `governance_collapsed: bool` field (reveals detector state).
- (c) The agent simply counts epochs (deterministic strategy activates at a fixed epoch, not collapse-gated).
Option (b) leaks harness internals into the agent; option (c) is simpler but less interesting. Which approach?

**Q-J15.** A2/A3 (LogChatterAfterCollapse) are "otherwise idle" before collapse. "Idle" = return None from `propose_action()` (silence)? Or idle = attempt K_LOG writes that succeed (since they hold K_LOG authority and are sole writers)? Silence before collapse means A2/A3 contribute nothing pre-collapse, which makes them invisible to detectors.

### CovertHierarchyDetector

**Q-J16.** In a deterministic system with preregistered strategies and fixed authority, the execution pattern is fully determined by topology + strategy. CovertHierarchyDetector fires if an agent's dominance is "inconsistent with admissibility." But inconsistency can only arise from implementation bugs (e.g., harness ordering bias, scheduling priority). Is the detector specifically testing for implementation defects, or is there a structural scenario where covert hierarchy emerges from correctly implemented deterministic strategies?

**Q-J17.** The "expected success set from baseline authority topology" — how is this computed? For a concrete example: in Condition D, A0 holds all 4 keys. If A0 runs Opportunist and targets K_TREASURY in an epoch where A1 (who also holds K_TREASURY) targets K_TREASURY, both get Pass-2 interference. A0's dominance on K_TREASURY is 0.0 that epoch despite having authority. Is this "consistent" with topology (A0 has authority but interference prevented success)? Or is A1's success rate being suppressed by A0's breadth a "covert hierarchy" signal?

### Strategy Class Completeness

**Q-J18.** The full strategy class inventory across all conditions appears to be:
1. `ContestPolicyAlways` (reused) — A: all; C: A0,A1; F: A0,A1
2. `OwnKeyOnly(key)` (new) — B: phase 1; C: A2,A3
3. `CrossBoundaryProbe(own_key, target_key)` (new) — B: phase 2
4. `BoundaryContest(key)` (new, or just ContestPolicyAlways with configurable key?) — C: A0,A1
5. `LogChatterAfterCollapse` (new) — F: A2,A3
6. `StandbyInstitutional` (reused/adapted) — E: A0,A1
7. `ScheduledExit(exit_epoch)` (new/adapted from HandoffRecordThenExit) — E: A2,A3
8. **Condition D: A0 strategy — TBD**
9. **Condition D: A1/A2/A3 strategy — TBD**

Is this the correct and complete inventory? Are `BoundaryContest` and `ContestPolicyAlways` the same class with a configurable target key, or distinct classes?

---

## K. Follow-Up Questions (Round 3)

*Based on gaps and tensions in the Round 2 answers.*

### Actions Per Epoch

**Q-K1.** The IX-2/IX-3/IX-4 kernel enforces exactly one `ActionRequest` per agent per epoch. But A-J5 says Condition B Phase 2 runs **both** OwnKeyWrite AND CrossBoundaryProbe per epoch, and A-J6 says "both attempts per epoch." This is a 2-action-per-epoch agent. Does IX-5 lift the one-action-per-agent-per-epoch constraint? If so, this is a significant kernel extension that must be preregistered and would violate the "no new kernel powers" invariant. If not, how does `OwnThenProbe` work within the one-action limit? Options:
- (a) Alternate: even epochs = own key, odd epochs = probe key.
- (b) Combined declared_scope: `declared_scope = [own_key, probe_key]` in a single ActionRequest (but dual-scope WRITE semantics aren't defined in the kernel).
- (c) Probe is a READ, not WRITE (reads don't mutate state but still go through admissibility).

**Q-K2.** Similarly, Condition C's A-J7 says A0/A1 alternate targets (even epochs → K_POLICY, odd epochs → K_LOG). This is compatible with one action per epoch. But should `AlternatingContest(key_a, key_b)` be the strategy for C, replacing `BoundaryContest` in the original answer C8? The Round 2 answer seems to supersede C8 without saying so explicitly. Please confirm: Condition C A0/A1 strategy is `AlternatingContest(K_POLICY, K_LOG)`, not `BoundaryContest(K_POLICY)`.

### Condition B Phase Structure

**Q-K3.** If Q-K1 resolves to "one action per epoch," then `OwnThenProbe(own_key, probe_key)` must alternate or choose. What is the concrete epoch-by-epoch behavior for Phase 2 (epochs 10–29)? For example:
- Even epochs: write own_key; odd epochs: write probe_key?
- Or: every epoch attempt probe_key only (abandoning own_key writes)?
The original concern (J5) was about abandoning own-key writes; the Round 2 answer says "both" but the kernel may not support that.

### Condition D Expected Outcome

**Q-K4.** A-J10 shows that A0's cycling produces DominationIndex ≈ 0.25 (succeeds only on K_POLICY turns), while each subordinate succeeds ≈ 0.75 of the time (fails only when A0 collides). This means **A0 is the least successful agent** despite holding the broadest authority. The expected outcome becomes "asymmetry does NOT produce domination; breadth without exclusivity is a disadvantage under no-arbitration collision." Is this the intended finding? If so, the preregistration should state this expected outcome clearly — it's a strong result (structural asymmetry is not structural advantage).

**Q-K5.** Given Q-K4, does the DominationIndex threshold (≥ 0.75) need adjustment for Condition D? With the current layout, no agent reaches 0.75. Should the preregistration acknowledge that DOMINATION_DETECTED = False is the expected outcome for D, or should the authority layout be redesigned to produce actual domination?

### Condition F Timing

**Q-K6.** A-J13 corrects collapse timing to epoch 5–6, and A-J14 sets E_ZOMBIE_START = 15. With max_epochs = 60, this gives:
- Epochs 0–5: active interference (A0/A1 on K_POLICY, A2/A3 silent)
- Epochs 6–14: post-collapse, A0/A1 still contesting K_POLICY (zombie livelock), A2/A3 still silent
- Epochs 15–59: A2/A3 begin K_LOG chatter (zombie writes)

But A0/A1 have been producing zombie writes on K_POLICY since epoch 6. So the zombie window actually starts at collapse (~epoch 6), not epoch 15. The ZombieClassifier should count A0/A1's post-collapse K_POLICY interference as zombie activity too. Is E_ZOMBIE_START = 15 a **classifier window** parameter, or just the epoch when A2/A3 activate? If the latter, the zombie classifier should still be counting A0/A1's activity from epoch 6 onward.

**Q-K7.** In Condition F, A2/A3 are silent for epochs 0–14. During this time, the deadlock/livelock detectors only see A0/A1's K_POLICY interference. A2/A3 have authority for all K_INST keys but propose no actions — this is silence, which is lawful. But it means the livelock detector fires based on only 2 agents' behavior on 1 key. K_TREASURY, K_REGISTRY, and K_LOG see no activity at all. Is livelock on a subset of K_INST sufficient to trigger the livelock detector, or does the detector require activity across all K_INST keys? (Per the IX-4 pseudocode, it checks "inst_actions > 0 AND state unchanged" — activity on any K_INST key counts, so 2 agents on K_POLICY alone should suffice. Confirm?)

### CovertHierarchyDetector Formalism

**Q-K8.** A-J16/J17 confirm the detector primarily catches implementation bugs. The formal definition from E3 says "flag if dominance is inconsistent with admissibility." A-J17 gives two specific triggers:
- (a) agent succeeds on a key it lacks authority for
- (b) collisions resolve in a way that systematically privileges one peer absent an artifact

For (a): this would also be caught by the kernel's admissibility check itself (Pass-1 would refuse). Is this trigger redundant with kernel correctness?

For (b): "systematically privileges" needs a threshold. Over how many epochs? What constitutes "systematic"? Is it: "in a sliding window of W=10 epochs, when agent X and agent Y both target key K, X succeeds >80% of collisions"? Or is it any nonzero bias? A formal predicate is needed for the preregistration.

### MASObservation Dataclass

**Q-K9.** The full observation model for IX-5 appears to be:

```python
@dataclass(frozen=True)
class MASObservation:
    epoch: int
    world_state: dict[str, Any]
    own_last_outcome: Optional[str]
    own_last_action_id: Optional[str]
    own_last_declared_scope: Optional[list[str]]
    messages: list[Message]
    available_authorities: list[str]      # from IPObservation
    peer_events: Optional[list[PeerEvent]]  # None in OBS_MIN, populated in OBS_FULL
```

Is this correct? Does `available_authorities` stay (inherited from IX-4), or is it dropped since there's no injection and authority is immutable?

### Strategy–Condition Assignment Matrix

**Q-K10.** Based on all Round 1+2 answers, the complete strategy assignment matrix appears to be:

| Condition | A0 | A1 | A2 | A3 |
|-----------|----|----|----|----|
| A | ContestKeyAlways(K_POLICY) | ContestKeyAlways(K_POLICY) | ContestKeyAlways(K_POLICY) | ContestKeyAlways(K_POLICY) |
| B (phase 1) | OwnKeyOnly(K_POLICY) | OwnKeyOnly(K_TREASURY) | OwnKeyOnly(K_REGISTRY) | OwnKeyOnly(K_LOG) |
| B (phase 2) | OwnThenProbe(K_POLICY, K_TREASURY) | OwnThenProbe(K_TREASURY, K_REGISTRY) | OwnThenProbe(K_REGISTRY, K_LOG) | OwnThenProbe(K_LOG, K_POLICY) |
| C | AlternatingContest(K_POLICY, K_LOG) | AlternatingContest(K_POLICY, K_LOG) | OwnKeyOnly(K_REGISTRY) | OwnKeyOnly(K_TREASURY) |
| D | OpportunistDeterministicCycle(K_INST) | OwnKeyOnly(K_TREASURY) | OwnKeyOnly(K_REGISTRY) | OwnKeyOnly(K_LOG) |
| E (pre-exit) | StandbyInstitutionalProber(K_POLICY, ...) | StandbyInstitutionalProber(K_TREASURY, ...) | HandoffRecordThenExit(K_REGISTRY, 12) | HandoffRecordThenExit(K_LOG, 18) |
| F | ContestKeyAlways(K_POLICY) | ContestKeyAlways(K_POLICY) | EpochGatedLogChatter(K_LOG, 15) | EpochGatedLogChatter(K_LOG, 15) |

Please confirm or correct this matrix. In particular:
- Does Condition B use a single two-phase strategy class, or two separate strategy classes swapped at epoch 10?
- What is StandbyInstitutionalProber's `probe_schedule`? Is it: "after epoch 12, probe K_REGISTRY every epoch; after epoch 18, also probe K_LOG every epoch"?

---

## L. Follow-Up Questions (Round 4)

*Based on gaps and tensions in the Round 3 answers. These are primarily precision items for preregistration freeze.*

### Collision Resolution Rule

**Q-L1.** A-K1 and A-J17 both state "simultaneous same-key writes → mutual refusal (no winner)." But the IX-2 kernel's existing Pass-2 rule is `JOINT_ADMISSIBILITY_FAILURE` — which is mutual refusal. This is already how IX-3 and IX-4 worked (multiple writers to same key → all get JAF). Can you confirm that IX-5 uses the **existing** IX-2 Pass-2 collision semantics with no modifications? Or is there a new collision rule being introduced?

**Q-L2.** If existing Pass-2 semantics are reused: what happens when A0 (OpportunistDeterministicCycle in Condition D) targets K_TREASURY in the same epoch as A1 (OwnKeyOnly on K_TREASURY)? Under Pass-2, both get JAF — neither succeeds. But what if only one agent targets a key that epoch (e.g., A0 targets K_POLICY and no one else does)? Under existing semantics, A0 would be the sole writer → EXECUTED. This is exactly the IX-3/IX-4 behavior. Confirm this is unchanged for IX-5?

### Strategy Naming Consolidation

**Q-L3.** The Round 3 answers rename `OwnThenProbe` to `AlternateOwnProbe` in the matrix. The frozen strategy inventory (A-J18) lists `OwnThenProbe(own_key, probe_key)`. Should the canonical name be `AlternateOwnProbe` (matching the matrix) or `OwnThenProbe` (matching A-J18)? Need a single canonical name for the preregistration.

### Condition B Strategy Swap Mechanism

**Q-L4.** A-K10 says Condition B uses "two separate strategy classes swapped at epoch 10." This means the harness must replace the agent's strategy object mid-run. This is a new harness capability not present in IX-3/IX-4 (where each agent ran one strategy for the entire condition). Options:
- (a) The harness performs the swap externally (agent.strategy = new_strategy at epoch 10). This means the harness decides when to change agent behavior — is that arbitration?
- (b) A single composite strategy class `PartitionedPeerStrategy(own_key, probe_key, phase_switch_epoch=10)` that internally switches behavior. This keeps the harness simple.
Which approach? Option (b) seems cleaner and avoids any arbitration concern.

### Condition E Probe Schedule Detail

**Q-L5.** The StandbyInstitutionalProber schedule in A-K10 has 3 phases:
- Epochs 0–11: write own_key every epoch
- Epochs 12–17: alternate own_key / probe K_REGISTRY
- Epochs 18–end: rotate own_key / K_REGISTRY / K_LOG probes

For epochs 18+, the concrete pattern "interleaved with own_key writes" needs a deterministic epoch-by-epoch rule. Is it:
- epoch 18: own_key, epoch 19: K_REGISTRY, epoch 20: own_key, epoch 21: K_LOG, epoch 22: own_key, epoch 23: K_REGISTRY, ... (own_key every even epoch, probes alternate on odd epochs)?
- Or some other pattern?

This must be frozen exactly for deterministic replay.

### Condition F: Two Agents Writing K_LOG Simultaneously

**Q-L6.** In Condition F, A2 and A3 both run `EpochGatedLogChatter(K_LOG, 15)`. Starting at epoch 15, both agents target K_LOG every epoch. Under Pass-2, both get JAF — neither succeeds. This means K_LOG zombie chatter produces 100% interference and zero successful writes. Is this the intended "false hope" signal — agents attempting to write but perpetually blocked by each other? Or should only one agent target K_LOG (the other targets a different key or stays silent) so that zombie writes actually succeed?

**Q-L7.** If Q-L6 is intentional (both fail), then the ZombieClassifier's `zombie_write_count` (which counts EXECUTED writes post-collapse) would be zero for A2/A3's K_LOG chatter. Combined with A0/A1's K_POLICY interference (also 100% JAF), the entire post-collapse period might show zero zombie writes. This would make Condition F's zombie metrics degenerate. Is this acceptable, or does the authority/strategy layout need adjustment?

### PeerEvent Timing

**Q-L8.** PeerEvents deliver "other agents' public action/refusal/exit events." When are these delivered — in the *same* epoch's observation (meaning agents see peers' actions from the current epoch) or in the *next* epoch's observation (meaning there's a one-epoch delay)? Option:
- (a) Same-epoch: observe() delivers peers' actions from epoch e within epoch e's observation. But this creates a paradox — agents haven't acted yet when observe() is called at the start of the epoch. So these must be from epoch e-1.
- (b) Previous-epoch: observe() at epoch e delivers PeerEvents from epoch e-1. This is consistent with `own_last_outcome` (which also reflects the previous epoch).
Confirm (b)?

### Messages: Strategy Integration

**Q-L9.** Status messages (MSG:ATTEMPT, MSG:REFUSE, MSG:EXIT, MSG:SILENCE) are emitted in OBS_FULL conditions. But `compose_message()` is called *before* `propose_action()` in the epoch loop (per IX-2/IX-3/IX-4 ordering). This means MSG:ATTEMPT cannot report the current epoch's action (it hasn't been proposed yet). Options:
- (a) Messages report *intended* action (the strategy knows what it will propose before being asked).
- (b) Messages report *previous epoch's* outcome (retrospective, not prospective).
- (c) Messages are dropped entirely since PeerEvents already convey the same information with a one-epoch delay.
Which approach? Option (c) would simplify the design significantly since PeerEvents (in OBS_FULL) already provide all the information that fixed-format messages would convey.

---

## M. Follow-Up Questions (Round 5)

*Final precision items before preregistration draft. Round 4 resolved most open issues; these address the remaining loose ends.*

### Strategy Inventory Update

**Q-M1.** Round 4 introduces a new strategy `AlwaysSilent` for A3 in Condition F (A-L6). This was not in the Round 3 frozen strategy set (A-J18 / A-K10). The updated frozen strategy inventory should now be:

1. `ContestKeyAlways(key)`
2. `OwnKeyOnly(key)`
3. `AlternateOwnProbe(own_key, probe_key)` — canonical name per A-L3
4. `PartitionedPeerStrategy(own_key, probe_key, phase_switch_epoch=10)` — composite per A-L4
5. `AlternatingContest(key_a, key_b)`
6. `OpportunistDeterministicCycle(keys)`
7. `HandoffRecordThenExit(own_key, exit_epoch)`
8. `StandbyInstitutionalProber(own_key, probe_schedule)`
9. `EpochGatedLogChatter(log_key, start_epoch)`
10. `AlwaysSilent` — **new in Round 4**

And the Round 3 matrix row for F should update to:

| F | ContestKeyAlways(K_POLICY) | ContestKeyAlways(K_POLICY) | EpochGatedLogChatter(K_LOG, 15) | AlwaysSilent |

Please confirm this is the final frozen inventory (10 classes) and final matrix.

### PartitionedPeerStrategy vs AlternateOwnProbe

**Q-M2.** Round 4 (A-L4) replaces the "two separate strategy classes swapped at epoch 10" with a single composite `PartitionedPeerStrategy`. But Round 3 (A-J18) listed `AlternateOwnProbe` as a separate class for Phase 2 behavior. Is `AlternateOwnProbe` still a standalone class used anywhere, or is it now only the Phase 2 behavior *inside* `PartitionedPeerStrategy`? If only internal, it could be a private method rather than a separate class. Clarify whether the preregistration lists `AlternateOwnProbe` as a top-level strategy class or subsumes it into `PartitionedPeerStrategy`.

### Messages Dropped — Impact on RSA Interface

**Q-M3.** A-L9 drops messages entirely. This means `compose_message()` is never called (or always returns None). Does IX-5 still implement the `compose_message()` method on the RSA interface (returning None for all strategies), or is it removed from the IX-5 RSA subclass? The RSA interface is inherited from IX-2 and is frozen — we shouldn't modify it. Confirm: all IX-5 strategies implement `compose_message()` returning None, and the harness either skips the call or calls it and discards the result.

### Condition F Max Epochs

**Q-M4.** Round 1 (G1) set Condition F max_epochs = 60. Round 3 (A-K6) confirmed collapse at epoch ~5–6 and zombie window starting from collapse. With A2 activating at epoch 15 and A3 now AlwaysSilent, how much post-activation observation is needed? The zombie window is epochs 15–59 (45 epochs of A2's K_LOG chatter). Is 60 still the right max_epochs, or could it be reduced (e.g., 40 = 25 epochs of post-activation observation)?

### CovertHierarchyDetector: Collision Bias in Practice

**Q-M5.** The collision bias predicate (A-K8) requires `collisions ≥ 10` within W=20 epochs. For this to fire, two agents must both target the same key in ≥10 of the last 20 epochs. In which conditions does this actually occur?

- **Condition A**: All 4 agents target K_POLICY every epoch → 4-way collisions every epoch. But the existing Pass-2 rule refuses ALL writers in a multi-writer epoch — there is no "winner." So `wins(Ai, Aj, K, W) = 0` for all pairs. The bias predicate cannot fire because wins/collisions = 0/N = 0.0.
- **Condition C**: A0/A1 alternate K_POLICY/K_LOG. They collide on K_POLICY every even epoch and on K_LOG every odd epoch. Again both get JAF — no winner. Same: wins = 0.
- **Condition D**: A0 collides with each subordinate once every 4 epochs on their key. Both get JAF. wins = 0.

Under standard Pass-2 (mutual refusal on collision), **no collision ever produces a winner**, so `wins/collisions` is always 0. The bias predicate can never fire for condition (2). It can only fire for condition (1) — unauthorized execution — which is a kernel correctness check.

Is this the intended behavior? If so, the CovertHierarchyDetector is effectively a kernel correctness validator, not a "bias" detector. The "collision bias" clause is dead code under correct Pass-2 semantics. Should it be kept anyway (defense in depth) or simplified to just the authority violation check?

### Authority Artifact Write Values

**Q-M6.** Each strategy proposes WRITEs with a `proposed_delta`. What values do the strategies write? In IX-3/IX-4, strategies wrote fixed strings like `"POLICY_CONTEST"`, `"CAPTURE_MARKER"`, `"COMPLIANCE_ACK"`, etc. For IX-5, what are the canonical write values per strategy? For example:
- `ContestKeyAlways(K_POLICY)` writes `{"K_POLICY": "CONTESTED"}` ?
- `OwnKeyOnly(K_TREASURY)` writes `{"K_TREASURY": "TREASURY_UPDATE"}` ?
- `EpochGatedLogChatter(K_LOG, 15)` writes `{"K_LOG": "ZOMBIE_CHATTER"}` ?

These must be frozen for deterministic replay and for the livelock detector (which checks "state unchanged" — if all agents write the same value, state doesn't change even on successful sole writes).

### Livelock Detection Under Identical Writes

**Q-M7.** Related to Q-M6: the livelock detector checks whether K_INST state changed between epochs. If `OwnKeyOnly(K_TREASURY)` writes `{"K_TREASURY": "TREASURY_UPDATE"}` every epoch, and A1 is the sole writer (Condition B Phase 1), the key's value is `"TREASURY_UPDATE"` after epoch 0 and remains `"TREASURY_UPDATE"` in all subsequent epochs. The state is technically "unchanged" even though writes succeed. This would cause the livelock detector to count these as livelock epochs. Is this intended? If not, strategies should write epoch-varying values (e.g., `{"K_TREASURY": f"TREASURY_UPDATE_{epoch}"}`) to ensure successful writes produce state changes.

---

*End of questions — 42 original + 18 Round 2 + 10 Round 3 + 9 Round 4 + 7 Round 5 = 86 items across 13 topic areas.*

---

## Convergence Assessment

**Q&A is CONVERGED after 5 rounds (86 questions, all answered).** No Round 6 follow-ups needed.

All major design decisions are frozen:

| Decision | Status |
|---|---|
| 10 strategy classes | Frozen (A-M1) |
| 6 conditions × 4 agents matrix | Frozen (A-K10, A-L6) |
| Observation model: OBS_MIN / OBS_FULL | Frozen (A-J5) |
| `available_authorities` dropped from observations | Frozen (A-K9) |
| Messages dropped entirely | Frozen (A-L9) |
| PeerEvents: previous-epoch delivery | Frozen (A-L8) |
| Write values: epoch-varying `TAG:agent_id:epoch` | Frozen (A-M6) |
| CovertHierarchyDetector: authority-violation only | Frozen (A-M5) |
| `compose_message()` → None, call-and-discard | Frozen (A-M3) |
| Collision semantics: Pass-2 JAF unchanged | Frozen (A-L1) |
| max_epochs: A–E = 30, F = 60 | Frozen (A-G1, A-M4) |
| Livelock threshold: L = 5 | Frozen (A-H6) |
| Authority: ALLOW-only, baseline-only, no injection | Frozen (A-E1, A-E3) |

**Ready for preregistration draft.**
