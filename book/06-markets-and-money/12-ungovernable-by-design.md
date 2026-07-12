---
title: 'Ungovernable by Design'
subtitle: 'What protocol rules can—and cannot—govern'
status: review
sources:
  - 178199698.ungovernable-by-design
  - 169071397.powering-freedom
---

Every few years the same demand resurfaces: make Bitcoin filter its content. Restrict data fields, cap scripts, or ban convenient encodings. Protocol changes can raise the cost, reduce throughput, discourage standard forms, and change what default software relays. What they cannot guarantee in a sufficiently expressive public system is that agents will never encode prohibited information through some remaining representation. The distinction is between control, deterrence, and perfect prevention.

Adam Back — the cypherpunk whose Hashcash proof-of-work is the mechanism Satoshi built on — has stated the position as cleanly as anyone. Bitcoin is bearer, censorship-resistant money. Nobody likes spam, and nobody wants to see illegal content on the chain. But there are inherent fundamentals that govern all internet protocols and programming languages, and no amount of wishing exempts Bitcoin from them. Bitcoin is decentralized — ungovernable by design: each person can run whatever software and policy they want, and the only thing they must share is the Nakamoto consensus rules, because people who want to mutually transact have to enforce the same rules. Beyond that, nothing binds anyone. You cannot realistically prevent arbitrary data hidden in fields, keys, hashes, script constructs, client-side data invisible to the network, encrypted payloads, steganography. And you cannot materially restrict encoding by shrinking field sizes or part-hobbling the scripting language. Limit a 520-byte output field to 34-byte public keys and you have prevented nothing: people can, will, and already have used multiple outputs and multiple transactions to carry the same data.

That position rests on three technical truths, and each one deserves to be pulled out and examined, because together they form an argument that reaches far beyond cryptocurrency.

## Three Truths About Substrates

**Encoding is difficult to eliminate completely.** Bitcoin exposes several channels—keys, hashes, scripts, transaction structure, and timing—that can carry information. Rules can make a channel expensive or nonstandard without proving that every covert channel is closed. This is a security claim about residual capacity, not the stronger claim that all restrictions are futile.

**Consensus validates structure, not private intent.** Nodes can enforce predicates over observable transaction data, and software can classify content probabilistically. Neither proves the sender's meaning or guarantees agreement about context. Consensus is well suited to deterministic validity rules; semantic and legal judgments usually require institutions outside that narrow mechanism.

**Limits alter cost and convenience.** Restricting fields or opcodes may push an encoding across more transactions, into a covert channel, or off the default relay path. That can materially reduce use even when it cannot reduce theoretical capacity to zero. A serious proposal should specify its target—perfect exclusion, lower prevalence, lower node burden, or clearer liability—and be judged against that target.

## Semantics Routes Around Syntax

The generalization is narrower: in an open, expressive system, syntax-level regulation often displaces behavior and creates evasion pressure. It can still change cost, scale, visibility, and default behavior. The system and its users adapt, so governance must assess substitution rather than count only compliance in the targeted channel.

You have seen this before, in substrates that have nothing to do with money. Language is the oldest case. Every censorship regime in history has discovered that banning words does not ban meanings. Prohibit a term and the euphemism arrives before the ink dries; prohibit the euphemism and you get irony, allusion, code, the pointed silence that says more than the banned sentence did. The censor is always regulating yesterday's encoding while today's meaning walks past in a new coat. What the censor wants to prohibit is an intent; what the censor can actually see is a syntax; and any medium expressive enough to be worth censoring is expressive enough to re-encode the intent in an unbanned form.

Biology is the same case in a different alphabet. DNA is an open generative code, and life is very good at routing around structural constraints — that is roughly what evolution *is*. Suppress one pathway and selection finds another; the space of encodings is too large to fence. And markets, the subject of this volume, are the case in between: prohibit a trade and you do not eliminate the trade, you re-encode it — into a black market, a barter arrangement, an offshore structure, a favor economy. The price mechanism, like the blockchain, transmits whatever people are determined to transmit. In each case the regulator confines a *form*, and the behavior reappears in another form, because the thing being regulated was never the form. It was the capability, and the capability is a mathematical property of the substrate.

The slogan “you can regulate behavior, but not math” captures one boundary and obscures another. A legislature cannot repeal an identity of arithmetic. Institutions can regulate people, hardware, interfaces, custodians, energy use, and which protocol implementations receive legal or commercial support. Protocol rules also govern what conforming nodes accept. Censorship resistance is therefore graded across layers: strong against unilateral semantic control inside consensus, weaker at exchanges, network access, mining concentration, software distribution, and users exposed to law.

Bitcoin's contribution is to expose this boundary sharply. Its consensus provides rule-bound validation with minimized discretion inside the protocol. Development, mining, node policy, exchanges, law, and user coordination remain social governance layers. Nakamoto consensus relocates and constrains interpretation; it does not remove every interpreter or eliminate capture at the edges.

## The Cost Objection

If perfect semantic filtering is unavailable, a separate question concerns what the network costs. A monetary network can consume substantial electricity while providing a service its users value; both facts belong in the assessment.

But "waste" is not a physical quantity. There is no instrument that measures joules and reports back which of them were wasted. Waste is a *valuation*: energy spent on something the speaker considers not worth it. Energy usage alone never equals energy waste — every economic activity, from manufacturing to banking to running the internet, consumes energy, and the only meaningful questions are whether the energy consumed generates commensurate value and whether that value could be had more cheaply another way. The critic who calls Bitcoin's energy wasteful has smuggled a judgment about Bitcoin's value inside what sounds like an engineering measurement. [Value is agent-relative](../05-value-and-ethics/01-the-myth-of-objective-value.md); the tens of millions of people holding and transacting in bitcoin have registered their valuation in the most credible way possible, by paying for it.

Annual mining estimates vary with hashrate, hardware efficiency, utilization, and methodology. Comparisons with “banking,” gold, data centers, or air conditioning often use incompatible system boundaries and do not establish substitution. The stable facts are that proof-of-work deliberately consumes substantial electricity, location and timing affect grid and emissions consequences, and the relevant counterfactual is not zero energy but the services and security alternative being compared. Any edition that prints a current total should date it and cite one methodology rather than mix estimates in a rhetorical table.

And the comparison to banking understates the case, because the fiat alternative is not free. The incumbent monetary system runs on central banks and regulatory agencies, branch networks and ATMs and bank data centers, payment rails — SWIFT, ACH, the card networks — plus the security and physical infrastructure of minting, vaulting, and moving cash. All of it consumes energy; almost none of it appears in the ledger when Bitcoin's consumption is being indicted. To the extent Bitcoin replaces or supplements those legacy systems, the *net* energy picture is a comparison between two infrastructures, not a comparison between Bitcoin and zero.

## What the Energy Buys

Mining is unusually location-flexible and can be interruption-tolerant, though network access, cooling, hardware logistics, financing, regulation, and revenue stability still constrain sites. That flexibility can monetize curtailed generation or stranded gas and can also compete with other loads or prolong fossil generation. Mining surveys and models disagree about the global energy mix and often rely on incomplete samples. The environmental verdict depends on marginal generation, time, location, methane leakage, grid congestion, and the counterfactual use of the energy—not on one global percentage.

The deeper answer asks what the energy purchases. Proof-of-work makes rewriting history and block production costly without assigning a central issuer. Users may value resistance to inflationary policy, confiscation, or payment censorship. Access still depends on connectivity, keys, fees, counterparties, law, and usable interfaces, so it is not an account no institution can deny in every practical sense. Whether the security and access benefits justify the energy and external costs is both a valuation and an engineering comparison; emissions and grid effects remain physical facts even when “waste” is evaluative.

The two halves meet in a design tradeoff. Proof-of-work uses recurring physical cost to minimize discretionary validation inside consensus. That does not make the wider network ungoverned or governor-free; it changes which actors can exercise which powers and what acquiring those powers costs.

Ungovernability, though, is a property of this particular design, not of blockchains as a category. Replace burned energy with staked capital and discretion comes creeping back in — who holds the stake, who coordinates the validators, who decides what a fork means. What happens when a network makes that trade is [the next chapter](13-the-fork-and-the-merge.md).
