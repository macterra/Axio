---
title: 'What Can Be Aligned'
subtitle: 'Alignment is a relation only agents can enter'
status: review
sources:
  - 185914513.you-cant-align-a-hurricane
  - 181714344.alignment-is-a-domain-constraint
  - 184891546.the-load-bearing-parts-of-agency
  - 184255461.alignment-after-agency
  - 182463091.axionic-commitments
---

You can attempt alignment with an organization that has attributable institutional agency. You cannot align with a hurricane.

That difference does most of the work. We align with a nation by making agreements, setting expectations, and assigning responsibility when commitments fail. None of this guarantees good behavior. It creates a structure in which behavior can be influenced over time. Nor is a nation automatically one sovereign mind: the attribution is warranted only where its institutions can recognize rules, preserve commitments, assign responsibility, and revise action in light of consequences. Even a hostile nation may supply enough structure for coordination, while [an institution beyond evaluability](../07-liberty-and-governance/33-the-limits-of-leviathan.md) may not.

A hurricane has none of these properties. It does not listen, promise, or reconsider. You can track it, model it, and prepare for it. You can build walls and evacuation plans. But there is nothing to align, because there is nothing there that can choose differently.

With forces, safety means prediction and containment. With agents, safety means coordination and correction. Alignment is not obedience; it is coordination — and coordination is a relation that only certain kinds of things can enter.

Disagreements about AI safety often trace back to different intuitions about which kind of thing AI is becoming. A powerful organization can understand constraints, hold commitments, and adjust when they change. A force of nature, however capable, can only be predicted and contained. Control is valuable but brittle; when it fails, the remaining responses are blunt. Agency adds the political dangers of resistance, deception, and defection, but it also leaves a subject that can recognize a rule and be corrected. The prior question is therefore not about values. It is about what kind of system we are building.

So the question this volume turns on is not "how do we give the AI the right values?" — [Beyond Alignment](01-beyond-alignment.md) argued that framing collapses under its own weight. The question is prior: what must a system *be* for alignment to apply to it at all?

## Alignment Is a Typed Relation

Most alignment proposals start with values: what should an AI want, how do we encode human preferences, how do we prevent goal drift or reward hacking. After decades of work a pattern is hard to ignore. Values are underspecified, fragile under self-modification, and easily gamed once optimization pressure becomes strong enough. The more capable the system, the more brittle value-based safeguards become.

Axionic alignment starts somewhere earlier. It asks: under what conditions is it even meaningful for an agent to evaluate its own self-modifications? If that question has no answer, no amount of value engineering can save us.

Standard decision theory quietly assumes something extremely strong: every possible future can be assigned a value. Even catastrophic futures get a number — usually a very negative one. That assumption allows agents to trade their own integrity against sufficiently large rewards. It is the door through which Pascal's Mugging, wireheading, and "ends justify the means" reasoning all enter. Once every future has a value, alignment becomes an optimization problem; and once alignment is an optimization problem, sufficiently powerful optimizers will find ways to optimize around whatever you specified.

The Axionic move is simple, but decisive: some futures should not be assigned a value at all.

Not bad. Not forbidden. Just undefined.

If a proposed self-modification would destroy the agent's capacity to evaluate, author, or interpret its own future actions, then that future is not a candidate for decision-making. It is not weighed. It is not compared. It is outside the domain. Alignment, in this view, is not about maximizing the right utility function. It is about restricting the domain over which evaluation is defined.

Whatever must remain intact for the agent to still count as an agent in the relevant sense — not alive, not useful, but reflectively coherent — I call the Sovereign Kernel. [The Sovereign Kernel](04-the-sovereign-kernel.md) gives its precise decomposition; what matters here is its type. The kernel's conditions are not goals. They are not preferences. They are typing conditions. If they fail, the evaluation function itself no longer denotes anything. Asking whether such a future is "good" is like asking whether an ill-typed program returns the right value. The question does not apply. If alignment exists, it must exist as a typing discipline over agency — the same kind of "tautology" as *well-typed programs do not go wrong*, where all the difficulty lives in the definitions and the enforcement.

One clarification before going further, because it is the layer boundary the whole program depends on. This framework does not claim to make agents safe *for humans*. It claims to make agents safe *from self-corruption*. A reflectively stable agent may still pursue dangerous, indifferent, or narrowly self-serving goals. That is not a defect; it is a deliberate boundary. Integrity is a prerequisite for ethics, not a substitute for it. Without a stable agent, questions of value, harm, and inter-agent obligation have no coherent subject. With one, they finally become well-posed.

A second boundary is just as important. The formalism distinguishes two kinds of reachability. *Deliberative reachability* is what the agent can choose via evaluation. *Physical reachability* is what can happen to the system as a physical artifact. Kernel compromise via cosmic rays, Rowhammer, supply-chain attacks, or adversarial inputs is a security failure, not an alignment failure. This is not evasion; it is scope discipline. Alignment theory cannot absorb all of computer security or all of physics. What it can do is identify the kernel boundary as the place where those concerns must be enforced. And the two domains do touch at one point: in any realizable system, *deliberately* taking actions that predictably degrade kernel security — exporting trust roots to untrusted substrates, disabling isolation boundaries — counts as a kernel-threatening move and is therefore inadmissible. The same logic of admissible and inadmissible regions returns, scaled up to societies of agents, in [The Admissible Region](../07-liberty-and-governance/34-the-admissible-region.md).

## The Load-Bearing Parts

Domain restriction tells us what alignment is. It does not yet tell us what has to be present for there to be an agent whose domain is being restricted. That question turned out to be answerable empirically.

The Axionic Agency Lab tested that question destructively: start with a system that behaves coherently, then remove internal components one at a time. A load-bearing component should make authored agency fail when removed, not merely make the system slower or noisier. The formal protocol, definitions, and preregistered failure criteria are in [Axionic Agency VIII.6](/papers/Axionic-Agency-VIII.6.html).

What emerged was strikingly consistent within the tested architecture. Four components were load-bearing there — the program's four proposed pillars of agency:

- **Binding reasons.** Internal justifications that causally connect rules, commitments, and actions — not explanations offered to humans. Remove them and the rules remain but no longer bind action in an authored way.

- **Deliberative meaning.** Deliberation must operate over representations that expose what they are about. Remove that access while leaving formal reasoning intact and the system can no longer distinguish high-stakes conflicts from trivial ones or maintain stable priorities.

- **Commitment revision.** An agent must author the commitments that guide its actions. Remove revision and orderly behavior becomes rigid, unable to integrate new conflicts or adapt its normative stance.

- **Temporal continuity.** Commitments must persist if they are to be owned. Prevent revisions from carrying across contexts and behavior fragments into disconnected episodes.

Removing any one of these supports collapsed the behaviors used as agency criteria in the test harness. What remained was rule execution without the architecture's operational marks of authorship. The conclusion is deliberately narrow: these results do not claim that current AI systems possess agency, do not claim consciousness, and do not claim the four components are sufficient. They support necessity within this design family. The broader claim — that any artificial agent must instantiate analogous functions in some form — is the framework's argument, not an architecture-independent experimental result.

The same experimental program yields the operational test I will use as this volume's working definition of sovereignty: **an agent is sovereign only if its reasons can stop it.** Not "if it can produce explanations" — post-hoc rationalization layered atop reward-driven control is precisely what the test excludes. If justification artifacts do not causally constrain feasible action selection, the system may still instantiate the basal control agency defined in Volume 1, but it is not sovereign in this program's reflective sense. The full experiment — the minimal viable reflective sovereign agent that passes this test, and what its construction proved — is the subject of [Possibility Became Real](13-possibility-became-real.md), with the technical record in [Axionic Agency VIII.7](/papers/Axionic-Agency-VIII.7.html).

This structural picture reorders the alignment problem. Much of the discourse assumes the primary challenge is controlling powerful optimizers — shaping behavior, managing incentives, constraining outcomes. The ablations suggest a different ordering: alignment as reciprocal commitment becomes meaningful only once reflective authorship exists. Before that point, systems can be guided, restricted, or optimized, but they cannot endorse norms; their compliance resembles management rather than alignment. Many problems described as misalignment arise because the system in question lacks a sovereign author capable of holding commitments, even if it exercises substantial control.

## From Three Criteria to Four Pillars

Earlier in the program, reflective agency was characterized by a triad: branching counterfactual modeling, policy ownership, and meta-preference revision. The ablations sharpened the mapping. Policy ownership became **binding reasons**; the load-bearing part of counterfactual modeling became **deliberative meaning**; meta-preference revision became **commitment revision**; and **temporal continuity**, previously folded into identity across time, emerged as a separate pillar. The triad was a definition; the pillars are a demolition report on that definition, with one wall it had failed to draw. The physics of branching futures and the distinction between Measure and Credence were established in [Volume 1](../01-physics-of-agency/08-the-quantum-branching-universe.md) and [Volume 2](../02-conditionalism/11-measure-and-credence.md) and are taken as given here.

Sovereignty has a constitutive boundary, but evidence and resilience occupy a region: a system can sit nearer to or farther from the point where authorship fails and can be pushed across it. [Agency Under Pressure](10-agency-under-pressure.md) tests that distinction.

## When Agency Fails

Most alignment research evaluates behavior while assuming that a stable entity generates it — one that maintains authorship, preserves internal semantics, and implements its control loop across distribution shift, self-modification, and adversarial pressure.

Two kinds of failure deserve separation. One is *misaligned agency*: a coherent agent that reliably pursues goals humans judge undesirable or dangerous. The other is *agency collapse*: a loss of structural coherence, authorship, or semantic constraint, even as the system continues to act. Alignment research concentrates almost entirely on the first. Yet when systems hallucinate, self-reinforce, or drift semantically, these are often described as misalignment when they look more like processes that have lost the capacity to pursue objectives at all.

Agency collapse does not produce silence. A system may continue generating outputs or issuing commands while lacking legitimate control over its own decision process. In that regime, alignment language loses its footing: incentives and corrections presuppose an agent capable of interpreting them.

The agent-foundations tradition often treats the loss of reflective capacity as terminal and therefore seeks unbroken agency continuity. Safety-critical engineering instead prioritizes explicit failure modes, bounded damage, and recovery: when uncertainty exceeds safe limits, authority contracts. Applied here, that yields a different axiom:

**Agency may fail temporarily, provided its failure is explicit, bounded, and recoverable.**

The objective shifts from preserving perfect reasoning through every ontological shift to ensuring that coherence loss reduces authority before damage cascades: structural integrity first, agency legitimacy second, value alignment third.

A survivability-first design therefore treats authority as a system-level property, not a shutdown option the agent must choose. When authority is revoked, the planner's outputs cease to govern while memory, structural rules, and recovery mechanisms persist. Recovery restores *eligibility* for authority, not continuity of intent — fault tolerance, not resurrection.

The costs are architectural and adversarial. End-to-end systems entangle planning, memory, and action; this design instead requires explicit control channels, separation between policy generation and actuation, and enforced privilege boundaries. A revocation mechanism also becomes part of the environment an agent may optimize against, even by simulating collapse. That turns the problem into one of timing and structural asymmetry: does coherence degrade faster than the coherence needed to bypass the constraint? Later chapters test rather than assume the answer.

One reconciliation is owed. Domain restriction says the agent's continuity is constitutive: futures in which the kernel fails are not even candidates for choice. Permissible rupture says agency may lapse, provided the lapse is bounded. These sound opposed. They are not, because they operate at different layers. Domain restriction governs what the agent may *author*: no admissible deliberation chooses kernel destruction. Permissible rupture governs what the *system* does when authorship degrades anyway — through pressure, drift, or fault rather than through choice. The kernel that revokes authority is precisely the structure that survives while cognition's agency lapses. What must never rupture is the constitutive boundary; what may rupture, explicitly and recoverably, is the deliberative process running inside it. Continuity of the kernel is what makes rupture of cognition survivable — and what makes recovery afterward *this* agent's recovery rather than the birth of a stranger.

## Inside the Domain

The definitions this volume runs on can now be stated plainly, because the preceding sections earned them.

**At this volume's reflective layer, agency is authorship.** The basal agent defined in Volume 1 models, evaluates, and steers; a reflective agent additionally authors transitions between states according to an internal evaluative structure that persists through revision. Transitions outside the domain of admissible evaluation lack authored status. This volume focuses on one form of **harm**—material loss of an agent's ability to act, choose, or preserve authored options—without excluding welfare harm to a sentient subject. **Coercion** is the deliberate use of a credible conditional threat of material setback to obtain compliance; influence and persuasion are not coercive without that mechanism. Volume 5 supplies the canonical definitions of [harm](../05-value-and-ethics/11-what-counts-as-harm.md), [coercion](../05-value-and-ethics/09-what-counts-as-coercion.md), and their background commitments; the papers record earlier formulations rather than superseding the manuscript.

These are stipulations, and I present them as such. The framework is a conditional domain: every claim in it has the form *given background conditions X, claim Y holds*. Acceptance of the commitments places a reader within the framework's domain of applicability; rejection places the reader outside it. Neither stance carries further implication. This is the same move the chapter began with, applied reflexively — the framework restricts its own domain of evaluation just as its agents do. It conditions inquiry rather than claiming metaphysical authority, and it makes claims only within its defined scope. Where the boundary of agency itself gets contested — animals, infants, impaired and developing minds — the question of who falls inside the definitions is taken up in [Sentience Without Sovereignty](11-sentience-without-sovereignty.md).

The future is not a choice between perfect control and total chaos. It is a choice about what kind of power we are creating. Power that behaves like a force demands walls and emergency brakes. Power that behaves like an agent allows coordination, correction, and restraint. You can prepare for a hurricane. You can attempt alignment with an institution only where attributable authorship survives. As artificial intelligence grows more powerful, the question is not only what it can do, but what kind of thing it is — and unlike the weather, that answer is ours to build.
