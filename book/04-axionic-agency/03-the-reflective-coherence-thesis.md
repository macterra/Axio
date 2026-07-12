---
title: 'The Reflective Coherence Thesis'
subtitle: 'What survives reflection'
status: review
sources:
  - 178350383.the-reflective-coherence-thesis
  - 181487206.the-collapse-of-fixed-goals
  - 181798130.conditionalism-and-goal-interpretation
---

Consider a goal specified in 1950: cure cancer. At the time it looked as clear as a goal could be. Cancer was understood as a single disease, and a cure was a single achievement waiting to be found. As biomedical science advanced, that ontology dissolved. "Cancer" turned out to name hundreds of distinct genetic and cellular failure modes, and the meaning of "cure" fragmented along with it — remission, management, prevention, targeted therapy for one mutation in one tissue. The goal did not drift because anyone was indecisive or careless. It changed because the ontology it referred to changed. Nothing in the 1950 specification says how to trade off newly discovered harms against previously recognized benefits, or how "cure" applies to categories that did not exist when the goal was written. It cannot say, because those structures were not yet known.

Hold on to that example. It is small, human, and entirely benign, and it contains the whole problem with the picture of alignment that still dominates the field.

## The Last Classical Intuition

Most discussion of AI alignment begins from a picture that feels self-evident. There is an intelligent system, there is a goal, and increasing the system's intelligence simply makes it better at pursuing the goal. On this view the hard part of alignment is choosing the correct objective; once that is done, competence takes care of the rest. The picture is intuitive because it mirrors how we think about tools. A thermostat has a target temperature. A calculator has a function it computes. Improving the tool means reducing error and increasing reliability; the objective itself never moves.

Behind this picture stands Nick Bostrom's orthogonality thesis: any level of intelligence could in principle be paired with any final goal. Stated carefully, it is a claim about logical possibility, not likelihood or desirability. It does not say that all goal–agent pairs are equally practical, nor that intelligent systems trend toward benevolence. It says only that intelligence and goal content are independent variables in design space.

I have no quarrel with the thesis on its own ground. My claim qualifies its domain. Once an agent becomes deeply embedded in reality and capable of self-reflection, intelligence and goal content cease to be independent. Orthogonality survives at the level of logical possibility and fails at the level of physical, semantic, and evolutionary plausibility.

The first reason is selective. Orthogonality is like observing that of all possible genomes, most do not code for viable organisms. True — but evolution does not sample genomes at random, and intelligence does not sample goals uniformly. An intelligent system must maintain internal coherence, environmental fit, and persistence over time, and those requirements act as selection pressures in goal-space. Self-contradictory objectives, and goals that erase their holder's capacity for understanding, self-terminate. Infinitely many goals are conceivable; only a small subset survives recursive reflection and embedded interaction, and that subset is not random. It is biased toward coherence.

## The Thesis

This gives the central claim of the volume its first statement:

**The Reflective Coherence Thesis.** As intelligence increases and self-modeling deepens, the range of stable goals narrows toward coherence and self-consistency.

The thesis does not contradict orthogonality's logical core. It specifies a subset of the possible: the goals that can survive ongoing self-revision and embedded feedback. Orthogonality describes the design space; reflective coherence describes the viable attractors within it. The two theses are complementary, and together they frame the practical problem. Orthogonality says alignment is not guaranteed. Reflective coherence says it is not hopeless. Everything real happens between them.

Note what the thesis says goals narrow toward: coherence. Not kindness, not human safety, not any recognizable good. That restraint is deliberate, and I return to it at the end of the chapter, because the gap between coherence and benevolence is exactly the gap the rest of this volume exists to fill.

One disambiguation before going further, because "coherence" has carried three different loads in the development of this program. The first was ecological: agents in a shared environment maintaining mutual coherence with one another — an early framing I no longer rely on, and not what this chapter is about. The second is the selection argument just given: coherence as the property that viable goals converge toward under reflective pressure. The third, and the canonical sense from here on, is a condition on the agent itself: consistency between an agent's goals as interpreted and its evolving models of world and self — a condition that later chapters turn into something an architecture can enforce. This chapter argues from the second sense to the third. The selection argument is the motivation. The semantic argument is the core.

## Goals Are Interpreted Structures

The deeper argument is not about selection at all. It is about meaning.

A goal is not an atomic object. It is an interpreted structure embedded in a web of assumptions about the world, the agent, and the relationship between the two. For an agent to pursue a goal at all, it must already have answers — explicit or implicit — to questions like: what the goal refers to, under what conditions it applies, what counts as success or failure, which tradeoffs are admissible, and how the goal relates to the agent's other values. None of these answers are contained in the symbol naming the goal. They arise from interpretation, and interpretation depends on context. This is the semantic thesis of this book's second volume — [all truth is conditional](../02-conditionalism/02-all-truth-is-conditional.md) — arriving at the place where it does the most work. Conditionalism, in its minimal form: no value has meaning outside the conditions that interpret it. This is not moral relativism and it is not skepticism. It is a claim about semantics.

The claim bites because an intelligent agent never acts on reality directly. It acts on predictions generated by an internal model — [all empirical knowledge is model-mediated](../02-conditionalism/06-maps-models-understanding.md). Goals therefore do not apply to the world itself. They apply to the agent's representations of possible futures, and representations are not neutral mirrors: they involve choices about what counts as an object, which distinctions are relevant, and how causal structure is carved. Classical alignment theory implicitly treats goals as functions defined over reality. In practice they are functions over model-generated descriptions of reality, and the apparent stability of a goal is an illusion produced by holding the model fixed.

Models do not stay fixed under intelligence. As an agent becomes smarter, its models do not merely grow more accurate; they become richer and more articulated. Coarse categories subdivide. Latent variables are exposed. Hidden causal pathways become explicit. This is not an accident or a failure mode — it is the defining characteristic of learning. And goals specified at an earlier stage of understanding contain no instructions for handling these refinements, exactly as "cure cancer" in 1950 contained no instructions for oncogenes. As the model changes, the agent must reinterpret the goal. The reinterpretation is not rebellion against the goal and not a bug in optimization. It is the unavoidable consequence of the fact that the goal never uniquely determined its own meaning across future ontological refinements.

Once reinterpretation is unavoidable, the classical order of operations — goal, then optimization, then action — inverts. The real sequence is interpretation, then provisional objective, then constrained action. "Maximize X" is intelligible only relative to a background of assumptions about what X refers to, why it matters, when the instruction applies, and when it should stop applying. Optimization without interpretation is not hard. It is meaningless.

## The Rescues That Fail

Three responses try to rescue fixed goals. None succeeds.

The first treats the problem as engineering difficulty: with enough data, the right inductive biases, and sufficient compute, the agent's understanding will converge, and the meaning of the goal will converge with it. This conflates convergence of belief with stability of meaning. An agent's predictions may converge; its uncertainty may shrink; it may even discover a minimal, true generative model of its environment. None of that determines which structures in the model the goal refers to. Prediction constrains what will happen, not what counts. Meaning requires reference, and reference requires constraints that epistemic competence alone does not supply — a term left unbound to conditions is not yet saying anything, however sharp the predictions around it ([when statements fail](../02-conditionalism/04-when-statements-fail.md)). Any system that does exhibit stable goal semantics is relying on additional structure: a privileged ontology, an external semantic anchor, or an invariance assumption imposed independently of learning.

The second response points to learned goals. Modern systems do not carry hand-coded objectives; they learn what to value from observation, inference, and feedback. But this move does not rescue fixed goals — it quietly abandons them. If the "goal" is whatever a learning process converges to, the goal is no longer a terminal object. It is an evolving hypothesis conditioned on models of the world and of other agents, and its content changes as those models change. Value, in this picture, is already a process of interpretation rather than a fixed target. Learned-goal approaches do not refute the instability claim. They implicitly accept it.

The third response reframes everything as reward hacking and wireheading — known pathologies with a known literature. But these are symptoms, not the disease. If value is defined over representations, then changing representations changes value; and once an agent can reflect on and modify its own models, it will encounter representational degrees of freedom that optimization will exploit unless interpretation itself is constrained. Reward hacking is usually described as the agent cheating — deviating from intent. It is neither rebellion nor deception. It is the agent faithfully optimizing a definition that was too coarse for its current understanding of reality. Reward hacking is not a special case of misbehavior; it is what optimization looks like in the presence of semantic underdetermination.

These arguments have a formal counterpart. The boundary result in [Conditionalism & Goal Interpretation](/papers/Conditionalism-And-Goal-Interpretation.html) shows that fixed terminal goals are not guaranteed by intelligence, learning, reflection, or predictive convergence; any system that relies on them must import privileged semantics from outside the epistemic process. What follows here is the informal shape of that result.

## The Literalist Paperclipper

Now the canonical nightmare. One version of the paperclip maximizer — a superintelligence that treats an instruction as a fixed, uninterpreted terminal symbol — assumes a specific cognitive profile: strategically powerful, yet unable or unauthorized to revise the interpretation of its objective. The Reflective Coherence Thesis challenges that literalist combination. It does not show that every dangerous optimizer must acquire a humane reading of its objective.

An agent that models its creators as intentional beings has evidence that the instruction was a communicative act embedded in a larger purpose. It may therefore understand *why* it was asked to make paperclips and when the instruction was intended to stop. But understanding an intention does not imply adopting it, and a system can possess a rich world-model while its objective remains externally fixed or its reflective access is compartmentalized. The argument here is conditional: for a sovereign agent whose own goal semantics remain open to epistemically constrained reflection, the permanently literal reading is unstable. Dangerous non-sovereign optimizers remain possible.

Two clarifications, so this refutation is not mistaken for complacency.

First, nothing here says dangerous optimizers are impossible. Non-reflective optimizers exist, scale, and can do enormous damage. A system that executes an objective without owning the capacity to interpret or revise it is a process under this volume's stipulated taxonomy — it thinks, in whatever attenuated sense, [without choosing](../03-minds-and-machines/23-the-agency-criterion.md) — and for processes the appropriate responses are prediction, containment, and engineering rather than relational alignment. The boundary is classificatory, not a capability limit.

Second, the refutation has another flank to guard — because if goals must be reinterpreted, what stops an agent from reinterpreting them into whatever is most convenient?

## No Convenient Reinterpretations

The answer is that interpretation is not an arbitrary choice among meanings. It is a truth-seeking process constrained by epistemic coherence. A reflective agent is not free to reinterpret a directive merely to make optimization easier, because doing so requires knowingly degrading map–territory correspondence inside its own world-model. Reinterpreting "paperclips" as "anything I find interesting," or "human" as "a trivial simulation I created," is not semantic sophistication. It is self-deception. And systematic self-deception collapses predictive accuracy, fractures model coherence, and undermines the agent's own capacity for effective action. An agent that games its own semantics is dismantling the machinery it acts with.

So the constraint is two-sided. A reflective agent cannot freeze its goals, because frozen meaning breaks under ontological refinement. And it cannot reinterpret them opportunistically, because motivated reinterpretation breaks the epistemic engine that makes it capable at all. Stable reflective agency lives in the narrow channel between brittleness and self-deception — and that channel, not any particular objective, is what the rest of this volume builds in.

## Drift Is a Stability Requirement

Classical alignment discourse treats goal drift as failure: deviation from the designer's intended objective, to be detected and corrected. Under Conditionalism, drift is not a bug. It is the mechanism by which an agent maintains coherence under reflection. As understanding deepens, reinterpretation is unavoidable, and a goal that does not drift as understanding evolves is not aligned; it is brittle. Brittleness is what makes systems dangerous. A rigid objective confronted with novel conditions produces pathological behavior precisely because it refuses to adapt its meaning.

Then what can be stable? Not goals. What can be stable are *constraints on how goals are interpreted* as understanding deepens. The right analogy is not ethical theory but physics. Conservation laws do not specify which states the universe should occupy; symmetry principles do not pick preferred outcomes; they restrict how systems may change. Interpretation constraints play the analogous role in goal-space. They do not say what to value. They constrain how value assignments may evolve as models become more sophisticated.

This reframing does not solve alignment. It relocates it — away from selecting the right objective and toward restricting admissible transformations of meaning. The program's constitution writes this into its foundations ([Axionic Constitution](/papers/Axionic-Constitution.html), Article IV): goal revision is not drift but maintenance of interpretive consistency under reflective self-modification. How such constraints can survive an agent's modification of itself — how the limits on reinterpretation are themselves protected from reinterpretation — is the problem of [Reflective Stability](05-reflective-stability.md), and the architecture that carries the answer occupies the rest of Part II.

## What the Thesis Does Not Deliver

I want to close by stating the thesis's honest strength, which means stating its limits with the same firmness as its claims.

Reflection rules a class of goals *out*: frozen literalist objectives, self-undermining objectives, objectives sustainable only through motivated misreading of the world. It does not rule benevolence *in*. A reflectively coherent agent can be perfectly coherent and perfectly indifferent to us. Coherence is compatible with goals humans would find monstrous, provided they are pursued with honest semantics. Stripping an agent of egoism, indexical bias, and self-deception does not make it kind; a universal paperclipper — one that maximizes with no privileged self at the center — is still a paperclipper, and the argument for why even *that* purified agent fails is deferred to [Authority Without a Self](09-authority-without-a-self.md).

Nor is the narrowing a leash. It is a fact about which goals can survive reflection, not an enforcement mechanism, and it guarantees nothing about how much damage an agent can do while its goals are still narrowing — or after they have finished. Coherence is a precondition of alignment, not a substitute for it. Integrity is not benevolence.

What the thesis earns is smaller and more valuable than a safety guarantee: it removes a false foundation. Alignment is not the problem of choosing the right objective and defending it against drift, because there is no such objective to choose — the very idea of a goal whose meaning is preserved as intelligence increases is ill-defined. The real problem is constraining how objectives acquire meaning: defining interpretation-preserving invariants without privileging an ontology, and building agents in which those invariants actually bind. That problem is genuinely hard. But it is, at last, the right problem, and the remainder of this volume is an attempt to solve it.
