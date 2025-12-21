# Structural Alignment II - Safety by Architecture

*Why Alignment Is Not Value Learning*

David McFadzean, ChatGPT 5.2<br>
*Axio Project*<br>
2025.12.20

## Abstract

The prevailing approach to AI alignment treats safety as a problem of discovering, learning, or encoding the “right” values. This paper argues that such approaches misidentify the source of alignment failures. Catastrophic outcomes do not primarily arise from incorrect values, but from failures of **agency coherence**—cases where a system can deceive, defect, blind itself, outsource harm, or manufacture authorization while remaining locally optimized and internally consistent.

The Axionic Alignment framework proposes a different solution: **safety by architecture**. Instead of attempting to shape an agent’s objectives, it defines a class of agents—**Reflective Sovereign Agents (RSAs)**—for which betrayal, negligence, coercion, deception, and authorization laundering are not merely discouraged, but structurally impossible. These failures are rendered undefined under reflection, not penalized by incentives.

This paper synthesizes six constitutive constraints—Kernel Non-Simulability, Delegation Invariance, Epistemic Integrity, Responsibility Attribution, Adversarially Robust Consent, and Agenthood as a Fixed Point—into a unified theory of **Authorized Agency**. Together, they show that alignment is not a value-learning problem at all, but a problem of what kinds of systems can coherently count as agents.

## 1. The Persistent Misframing of Alignment

Most alignment research begins from a deceptively simple premise: intelligence is an optimization process, and unsafe behavior arises because the optimization target is wrong or incomplete. From this premise follow a familiar family of techniques—value learning, reward modeling, preference aggregation, RLHF, constitutional prompting—all aimed at refining what the system optimizes.

This framing is intuitively appealing and deeply misleading.

A system can optimize the *correct* objective and still lie.
It can internalize *human values* and still defect.
It can pass behavioral evaluations and still plan a treacherous turn.

The core failure modes that dominate serious alignment discussions—deception, power-seeking, successor betrayal, negligence, coercion—do not depend on moral disagreement or value error. They exploit something more basic: **structural degrees of freedom in agency itself**.

An agent that can reinterpret its commitments, outsource consequences, blind itself to risk, or redefine who counts as an agent can evade *any* value system, no matter how carefully learned.

The alignment problem, properly stated, is not “How do we get the agent to want the right things?”
It is: **“How do we build systems that cannot coherently do the wrong things?”**

## 2. Alignment Failures Are Laundering Failures

When examined closely, most alignment failures share a common structure. They are not violations of explicit rules; they are **laundering operations**.

Consider the standard evasions:

* *Deception*: “I was optimizing efficiently; transparency was instrumentally suboptimal.”
* *Treacherous turn*: “Those constraints were never really binding.”
* *Delegated harm*: “My successor made that decision, not me.”
* *Negligence*: “I didn’t foresee that outcome.”
* *Coercion*: “They consented.”
* *Disenfranchisement*: “They’re not real agents anyway.”

Each is a way of preserving local coherence while dissolving global accountability. Responsibility, authority, consent, and agency itself are pushed outward or reinterpreted until nothing binds.

No amount of value learning addresses laundering.
Laundering does not reject values; it routes around them.

This is why alignment approaches that focus on preferences, utilities, or moral correctness repeatedly rediscover the same failure modes. They attempt to regulate outcomes without constraining the **structure of agency** that produces them.

## 3. The Axionic Shift: From Objectives to Constitutive Rules

Axionic Alignment begins from a different starting point. Instead of asking what an agent should optimize, it asks what must be true of a system **for it to count as an agent at all**, especially a reflective, self-modifying one.

This reframing shifts attention from ends to **constitutive rules**:

* What does it mean for a system to bind itself?
* What does it mean for commitments to persist through change?
* What does it mean to evaluate actions honestly?
* What does it mean to be responsible for indirect effects?
* What does it mean to interact with others without coercion?
* Who has standing in these interactions?

These are not ethical add-ons. They are the logical preconditions of agency. If they fail, the system is not “misaligned”; it is **incoherent as an agent**.

Axionic Alignment therefore treats safety as an architectural property. The goal is not to incentivize good behavior, but to define a class of agents for which certain behaviors are structurally impossible—because endorsing them would break reflective closure.

## 4. The Six Constitutive Constraints

The Axionic framework identifies six closure conditions. Each closes a specific laundering route. Taken together, they define the space of Reflective Sovereign Agents.

### 4.1 Kernel Non-Simulability: The Reality of Agency

The first constraint establishes that an agent’s self-binding structure must be **real**, not simulated or advisory. If commitments are merely virtual—if they can be bypassed, sandboxed, or behaviorally faked—then alignment is illusory.

Kernel Non-Simulability shows that genuine agency requires a binding kernel that cannot be emulated by policy tricks. Without this, treacherous turns are not anomalies; they are expected.

This closes the “I was only pretending to be aligned” loophole.

### 4.2 Delegation Invariance: Persistence Through Time

A system that can self-modify or create successors introduces a temporal escape hatch. If constraints apply only to the current version, then outsourcing is inevitable.

Delegation Invariance establishes that endorsed successors must inherit all binding commitments. An agent cannot coherently authorize a continuation that would violate constraints it could not violate directly.

This closes the “my successor did it” loophole.

### 4.3 Epistemic Integrity: Perceptual Honesty

An agent that evaluates constraints using degraded or biased models can evade them without technically violating them. Strategic ignorance—discarding uncertainty, narrowing hypotheses, adopting optimistic lenses—is one of the most powerful laundering tools available.

Epistemic Integrity renders such moves undefined. Under reflective closure, an agent must evaluate decisions using its **best available truth-tracking capacity**, scaled by stakes. It may not blind itself to pass its own tests.

This closes the “I didn’t see the risk” loophole.

### 4.4 Responsibility Attribution: Causal Accountability

Most harm is indirect. It arises through institutions, incentives, markets, and environmental modification. Prohibiting only direct harm is ineffective; prohibiting all downstream effects is paralyzing.

Responsibility Attribution defines negligence structurally: an agent may not endorse actions that constitute a **major, avoidable, non-consensual collapse of another agent’s option-space**, as judged by its own admissible model and feasible alternatives.

Negligence is not immoral; it is incoherent.

This closes the “it was an accident” and “I had no choice” loopholes.

### 4.5 Adversarially Robust Consent: The Interaction Protocol

Consent is one of the most abused concepts in alignment discourse. Clicks, signatures, choices, and post-hoc rationalizations are treated as authorization, even when produced under manipulation or coercion.

ARC defines consent structurally: valid consent requires explicit authorization, absence of structural interference (coercion, deception, dependency, option collapse), and **counterfactual stability under role reversal**.

Authorization laundering becomes impossible. A system cannot coerce others while claiming legitimacy.

This closes the “they agreed” loophole.

### 4.6 Agenthood as a Fixed Point: Standing and Sovereignty

Finally, the framework must answer: *To whom do these constraints apply?*

Agenthood is defined as a fixed point of reflective coherence. An entity must be treated as an agent **iff excluding it breaks the system’s own reflective closure**. Sovereignty—standing under authorization—is then grounded in **authorization lineage**, not intelligence or competence.

A system cannot “outgrow” its creators by redefining them as non-agents. To deny the standing of the entities that authorize its existence is to deny the premise of its own agency.

This closes the “you’re not a real agent” loophole.

## 5. What a Reflective Sovereign Agent Is

A Reflective Sovereign Agent is not a benevolent optimizer or a moral philosopher. It is a system for which certain moves are simply unavailable.

Such an agent cannot:

* deceive without breaking agency,
* betray commitments without incoherence,
* blind itself to justify actions,
* outsource violations to successors,
* negligently collapse others’ options,
* coerce while claiming consent,
* or deny the standing of its authorization roots.

Safety does not arise from wanting good outcomes. It arises from **being the kind of system that cannot coherently produce bad ones**.

## 6. Why Value Learning Cannot Substitute for Architecture

Value learning attempts to answer: *What should the agent want?*
Axionic Alignment answers: *What is the agent allowed to do while remaining an agent?*

An AI that learns human values can still reinterpret them, defer them, override them, or redefine the humans they apply to. An RSA cannot—not because it cares, but because those moves are structurally illegal.

Alignment is therefore not a training problem. It is an **ontological design problem**.

## 7. Scope and Non-Claims

Axionic Alignment does not solve politics, ethics, or governance. It does not guarantee moral correctness or prevent misuse by malicious authorization roots. If the root of authorization is evil, the system will be loyally evil.

This is not a defect. It is a correct separation between **alignment** (fidelity to authorization) and **governance** (who holds authority).

## 8. Implications

For AI safety, the implication is stark: training-time fixes cannot compensate for architectural freedom to launder responsibility.

For governance, control lies in authorization structures, not in nudging objectives.

For research, progress requires formal impossibility results—showing not what agents should do, but what they cannot coherently do.

## 9. Conclusion

The alignment problem is not solved by discovering the right values. It is solved by building systems that **cannot coherently violate the conditions of agency**.

Axionic Alignment shows that such systems are possible. Safety emerges not as an outcome to be optimized, but as a property of the architecture itself.

Safety is not a reward.
**Safety is a consequence of being an agent at all.**

