---
title: 'Minds and Agents'
subtitle: 'The vehicle and the driver'
status: review
sources:
  - 167297761.minds-and-agents
  - 167660845.minds-as-recursive-simulations
---

A robot vacuum builds a map of your apartment, plans a route around chair legs and stairs, and executes it. On many engineering definitions it is an agent; on stricter accounts it is an automated controller. Nobody suspects it of brooding. Meanwhile, much public argument about artificial intelligence asks "does it have a mind?" as though *mind* and *agent* were the same category. This chapter separates them: agency names organized control; mind names an integrated modeling process with reflective capacities. The vehicle-and-driver image is useful so long as it is not mistaken for two physically separable things.

## What Makes an Agent

For this chapter, a **deliberative agent** is a physical or virtual system that does four things. It carries predictive models; evaluates at least some counterfactual actions; selects among them under goals or policies; and closes a causal loop through an environment. This is narrower than Volume I's minimal physical agency and avoids pretending that every regulator performs explicit deliberation.

Humans and many animals qualify. Some autonomous robots and virtual agents may qualify relative to a bounded environment. A rock rolling downhill does not, and a thermostat is regulation without deliberation. [Minimal and maximal agents](../01-physics-of-agency/05-minimal-and-maximal-agents.md) develops the broader triad of embeddedness, predictive modeling, and intentional biasing. A bacterium swimming up a sugar gradient qualifies as a minimal physical agent there: it senses recent change and biases action toward a viable state. It need not perform the explicit counterfactual comparison required here.

## What Makes a Mind

A **mind**, as this book uses the term, is an integrated modeling process within an agent, distinguished by three capacities. **Reflective self-modeling**: it represents some of its own internal states, capabilities, and limits. **Metacognition**: it monitors and can sometimes correct its cognitive processes. **Reflective goal revision**: it can evaluate and adjust at least some goals or strategies rather than merely executing a fixed policy.

The bacterium has none of this. It models the sugar gradient; it does not model itself modeling the sugar gradient. The robot vacuum maps the floor; it does not ask whether floor-mapping is worth its while. Human cognition has all of it, which is why a person can do what no bacterium can: change course not because the world pushed back but because reflection did — deciding the goal itself was wrong.

Within this functional taxonomy, the relationship is one-way. **Agents without minds are common**: bacteria, simple controllers, and much software act on their environments without reflective self-modeling. A mind, as defined here, is a process *of* an embodied or virtual agent: its self-model represents that agent's states and its conclusions can alter the agent's conduct. This is a terminological dependency, not proof that every possible theory of mind must individuate systems the same way.

## The Ladder

Saying what a mind is a subsystem *of* still leaves open what kind of thing the subsystem is. The answer is best built from the ground up, one rung at a time, each rung adding exactly one capability to the one below.

A **mathematical function** maps inputs to outputs. A program may implement a function, but programs can also maintain state, interact with an environment, and behave nondeterministically.

A **program** encodes a process. It may maintain internal state, branch on conditions, and produce side effects.

A **recursive program** invokes itself, directly or indirectly. Recursion is a way of organizing computation, not a necessary increase in expressive power; iteration can usually implement the same computable transformation.

A **simulation** is a program put to a particular use: modeling the state transitions of a dynamic system. It may update a state repeatedly, incorporate stochastic events, or interact with live inputs. Run it and a model of a world unfolds in step with — or ahead of — the world itself.

And then the last rung. A **mind is a recursive simulation of agency**: a simulation, maintained by an agent, whose subject matter is the agent itself in interaction with its environment — and, crucially, in interaction with itself. It models the vehicle it drives, forecasts that vehicle's encounters with the world, evaluates the alternatives, and feeds the results back into the vehicle's actual behavior. It is not a passive picture hung inside the skull; it actively shapes what the agent does next. A mind is a self-referential predictive control system — a control loop that includes itself among the things it controls. That control loops must run on models is the argument of [control requires models](03-control-requires-models.md); the mind is the special case in which the model's domain has expanded to swallow the modeler.

The three capacities now have distinct jobs. Reflective self-modeling supplies information about the system; metacognition monitors the modeling process; goal revision closes a control loop through that information. Recursion can support higher-order monitoring and introspection. Whether it is sufficient for phenomenal consciousness remains the disputed step taken up in [Consciousness Explained](07-consciousness-explained.md).

## Substrate and Portability

Notice what the ladder never mentions: neurons. Every rung is characterized computationally — by what the process does, not by what it is made of. A biological mind is instantiated in neural tissue, continuously integrating sensory input, memory, prediction, and motor output. The functional definition does not privilege tissue. If the relevant organization is multiply realizable, a mind could in principle run on another substrate. That is a substantive functionalist assumption, not something proved merely by defining mind computationally.

Whether a particular mind can actually be *moved* is a separate question. **Portability** — transferring a mind between agents — is a contingent property, not a definitional one. Human minds are not presently portable: cognition is woven into the body and brain, with no demonstrated interface for extraction. An artificial mind might be more portable if its functional organization could be checkpointed and resumed, but copying state would still leave questions about embodiment, continuity, and identity. Debates about mind-uploading routinely collapse three claims: the functionalist hypothesis that minds are multiply realizable, the unproved engineering claim that a human mind can be transferred, and this book's requirement that a functioning mind remain coupled to some agent-context. Keeping them apart makes the dispute tractable.

## The Driver and the Vehicle

The framework is compact — agent as vehicle, mind as driver, the driver a recursive simulation the vehicle runs of itself — but it does real sorting work. It separates reflective capacity from agency, which are graded separately: a system can climb high on one axis while sitting at zero on the other. The reflexive robots and processes that increasingly run the world are agents without minds, and they need exactly the scrutiny agents need — their causal efficacy is real — without any temptation to wonder what it is like to be them. And it locates the genuinely hard question about current AI systems in the right place. The popular question — do they have minds? — comes second. The prior question is whether they are agents at all: whether anything in there predicts, weighs counterfactuals, selects toward goals, and closes the loop through the world on its own behalf. That question gets its own chapter in [the agency criterion](23-the-agency-criterion.md). The order matters, and the dependency dictates it. There can be no driver where there is no vehicle.
