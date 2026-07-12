---
title: 'Infinite Randomness'
subtitle: 'Boltzmann brains and the mathematics of everything'
status: review
sources:
  - 169620752.infinite-randomness
  - 169621940.infinite-randomness-and-qft
  - 167947701.the-vastness-of
  - 170284204.the-vulcan-number
---

A freak fluctuation in empty space assembles, atom by atom, a functioning human brain — complete with a lifetime of memories, a mood, a headache, the vivid impression of sitting somewhere reading a book. An instant later it dissolves back into the void. This is the classic Boltzmann brain, and the standard reaction to it is a shudder followed by a dismissal: assembling a macroscopic organ by thermal accident is so fantastically improbable, so violent an offense against thermodynamic intuition, that the scenario is filed under cautionary tales for cosmologists and forgotten.

I want to use the case as a stress test for a stronger proposal: perhaps consciousness depends on an appropriately realized informational organization rather than on biological matter in particular. That proposal is not established by the mathematics that follows. The chapter separates three claims that are easy to blur: finite strings can encode descriptions of minds; some physical systems may realize minds; and mere occurrence of an encoding might itself constitute realization. Only the first is mathematical. The second is empirical and philosophical; the third begins the speculative ontology developed in this part.

## Consciousness as Software

Suppose consciousness is computationally realizable and substrate-independent within some class of physical systems. This is a substantive functionalist assumption, not a consensus result of cognitive science. Even if it holds, a description of a computational state is not automatically an execution of that state; an account of physical or causal realization is still required.

Now imagine an infinite sequence of independent random draws with full support over finite configurations. Under those assumptions, every finite pattern occurs infinitely often with probability one. That is a theorem about a stochastic model, not a guarantee supplied by infinity alone. Calling an occurrence a conscious experience would additionally require the realization principle just left open.

The immediate objection is continuity. A state can encode apparent memories and expectations without standing in the causal sequence those representations describe. Other randomly occurring states may fit the same narrative, but logical compatibility does not order their occurrences or connect them causally. The pattern theory considered here proposes that a sufficiently coherent collection could nevertheless ground a subjective life. Competing theories make causal continuity constitutive and reject that conclusion.

The radical conjecture is therefore: **subjective continuity might supervene on internal coherence without matching external causal history.** A state with counterfeit memories may be locally indistinguishable to its subject from one with veridical memories. That underdetermines the subject's evidence about its past; it does not show that caused and merely described histories are ontologically equivalent.

If the conjecture is granted, external causation becomes underdetermined by present experience, and a random substrate could replace an intentional simulator in the thought experiment. But randomness does not generate realizations “for free”: the substrate, probability law, realization relation, and measure over observers all remain load-bearing assumptions.

Whether these spontaneous instantiations *count* — whether a counterfeit of your evidence, however internally coherent, carries any weight when you reason about where and what you are — is a separate question, and it is the hardest one in this territory. It has an answer, and the answer is not "count the copies": it turns on which realizations of your evidence are *admissible*, genuinely grounding the structures that make your evidence evidence. That argument belongs to anthropics and is made in [You're Not a Random Sample](../02-conditionalism/15-youre-not-a-random-sample.md). This chapter's job is prior to it: to establish just how much the substrate contains, and how cheaply.

## Your Life Is in π

"Every finite pattern occurs infinitely often" sounds like the kind of claim that should cost something — some exotic metaphysical machinery, some leap of faith about infinity. It costs almost nothing. The mathematics that delivers it is a standard, well-studied property of ordinary numbers, and you can hold examples of it in your hand.

Start with the size of the thing to be contained. Take a complete digital record of a human life — one hundred years of continuous high-definition video, efficiently compressed. Call it two petabytes: roughly $1.8 \times 10^{16}$ bits, eighteen quadrillion. That is your life, every moment and every subtle detail, as one finite bitstring.

A real number is **normal** in a given base if every finite digit sequence appears with its expected limiting frequency. Normality is widely conjectured, though not proven, for π. If π is normal in base 2, then any specified finite digital record occurs in its binary expansion infinitely often. So do encodings of every book, genome, and finite dataset. This is syntactic containment only: digits that encode a video, connectome, or program do not thereby display, embody, or execute it.

Two caveats keep this honest. First, the existence is implicit, not practical: *locating* your life's bitstring in π is computationally intractable in a way that shades into impossibility, so this is a fact about what π contains, not a retrieval scheme. Second, π's normality is a conjecture. Émile Borel proved in 1909 that almost all real numbers — in the precise measure-theoretic sense — are normal in every base; pick a real at random and it contains everything finite with probability one. Yet not a single familiar constant — π, $e$, $\sqrt{2}$ — has been proven normal in any base. Normality is simultaneously generic and unexhibited: nearly every number has the property, and we can barely point to one that provably does.

## The Vulcan Number

Mathematicians handle that embarrassment by construction: if nature won't hand over a certified normal number, build one. Champernowne's constant, $0.123456789101112\ldots$, concatenates the integers in base 10 and is provably normal there. The Copeland–Erdős constant does the same with the primes. These numbers are deliberately artificial — illustrations rather than discoveries — and that artificiality is exactly their virtue: the everything-container property holds *by construction*, no conjecture required.

In 2019 I contributed my own to the Online Encyclopedia of Integer Sequences: [sequence A308705](https://oeis.org/A308705), the Vulcan Number. The goal was to make the containment property not just provable but *obvious*. The construction: concatenate every finite binary string in shortlex order — shortest strings first, lexicographic within each length:

```
0, 1, 00, 01, 10, 11, 000, 001, 010, 011, 100, 101, 110, 111, 0000, ...
```

Prefix a binary point and you have an infinite binary constant:

```
0.0100011011000001...
```

Every finite bit pattern appears, exactly on schedule, because the construction walks through all of them by brute enumeration. No conjecture stands between the definition and the property. And unlike some celebrated constructions in this neighborhood (Chaitin's Ω is a normal number you provably cannot compute), the Vulcan Number is explicit, deterministic, and simple enough for an introductory programming course:

```python
from decimal import Decimal, getcontext
from itertools import product

# Concatenate all binary strings in shortlex order (lengths 1..8 shown)
bits = "".join(
    "".join(pattern)
    for length in range(1, 9)
    for pattern in product("01", repeat=length)
)

# Evaluate the binary expansion 0.<bits> as a decimal
getcontext().prec = 70
vulcan = sum(Decimal(2) ** -(i + 1) for i, b in enumerate(bits) if b == "1")
print(vulcan)
```

Numerically, the construction converges on:

```
0.276387117279486523734198676211901230555089988160685506143676819115...
```

Whether this particular concatenation is normal is separate from the simpler property it has by construction: every finite bitstring occurs. The example shows that universal finite-string containment is easy to define. A chosen encoding of a life record sits at a computable offset; the life itself does not. Between π, where normality remains conjectural, and an explicit enumeration, the mathematical lesson is narrow but useful: containing every finite description is cheap.

A normal number contains finite patterns statically; the specified stochastic process produces them over time with probability one. Neither fact alone tells us which patterns are physically implemented computations or conscious states. That missing bridge is precisely what the metaphysical proposal must supply.

## Coherence as Physics

One objection remains, and it is the serious one. A random sequence contains finite descriptions, but containment is not realization. Even granting a realization rule, the model would need to explain why experiences exhibit stable quantitative regularities rather than arbitrary noise. Our observations agree with highly tested physical theories; a universal string container does not predict that fact.

The proposal can reproduce a theory's allowed mathematical histories by defining *coherence* in terms of that theory. For quantum field theory, the filter would need to encode its state space, dynamics, symmetries, observables, and probability rule. This is a redescription unless an independent reason privileges that filter and its measure.

With sufficiently rich stipulations, the filtered model can be constructed to match QFT's predictions. Its empirical equivalence is then conditional on the filter, realization rule, and observer measure reproducing the physical theory. The construction demonstrates representational equivalence, not yet an independently predictive rival ontology.

The exercise illustrates a familiar underdetermination: formally equivalent descriptions can package ontology differently. It does not establish that the random-substrate package is more parsimonious, because the complexity may simply have moved into its filter and interpretation map.

The scenario still has several load-bearing components: an infinite substrate or sequence space, a probability measure, a coherence criterion, an interpreter, a realization relation, and an observer measure. None has been explained merely by invoking universal containment. [Chaos as Foundation](20-chaos-as-foundation.md) asks whether this package can nevertheless serve as a comparatively minimal metaphysical representation. The thought experiment ends not at a demonstrated bottom of reality but at a precise list of debts for the chapters that follow.
