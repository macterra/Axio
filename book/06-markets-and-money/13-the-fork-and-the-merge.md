---
title: 'The Fork and the Merge'
subtitle: 'Proof-of-stake and the return of discretion'
status: review
sources:
  - 180917415.the-fork-and-the-merge
  - 184087663.when-consensus-entrenches-authority
---

In June 2016 an Ethereum smart contract executed according to its code while violating the expectations of many participants. The community's response exposed a conflict between application-level execution, protocol history, and socially recognized legitimacy.

The occasion was The DAO — an unaudited, overfunded experiment in crowd-directed venture funding that had absorbed roughly fourteen percent of all the ether in existence. Its smart contract contained a recursive-call bug: a withdrawal function could be re-entered before the contract updated its balance. An attacker used it to siphon 3.6 million ETH, about fifty million dollars at the time, into a child contract. Nothing about the blockchain failed. Consensus held, blocks were produced, the protocol executed exactly as written. The vulnerability was human judgment — bad code, deployed too big, too fast — not the machine underneath it.

The fear that followed was legitimate. An attacker controlling that much of the money supply threatened the market and the credibility of a young ecosystem. But the response set the precedent that concerns this chapter. Instead of accepting the rule the platform had been advertising — code is law — Ethereum's leadership orchestrated a hard fork that rewrote the ledger, reversed the exploit, and returned the funds to their original owners.

Including, in the interest of full disclosure, me. I held DAO tokens; the fork made me whole. I am not a neutral critic of the bailout — I am one of its beneficiaries, and I think it was a mistake.

The chain split over it. ETH carried on with the altered history; Ethereum Classic preserved the unedited history and attracted far less use and value. The bailout established that a sufficiently large coalition could coordinate a client change and that users could choose between histories. That reveals a social layer above protocol execution. It does not establish a single political class with unilateral override authority: the dissenting chain persisted. The relevant questions are how concentrated coordination was, what precedent it set, and how costly dissent became.

For six years you could file all of this under emergency. Every institution grants itself one exception in a crisis, and a system barely a year old, facing the loss of a seventh of its money supply, has a better excuse than most. The fork was a breach, but a breach of practice. What turned it into architecture was the Merge — Ethereum's 2022 conversion from proof-of-work to proof-of-stake. The fork proved that social consensus could override the protocol. The Merge made the override structural. To see why, we have to be precise about what decentralization actually is.

## What Decentralization Is

Discussions of decentralization usually begin with surface metrics: node counts, validator counts, client diversity. These numbers are easy to count and easy to advertise, and they miss the point. A system in which outcomes are reliably dictated by a small coalition is centralized no matter how many machines are plugged in.

Decentralization is about power. Who can determine state transitions? Who can block or force a change of rules? And the question that does the real work: can that authority be challenged *without anyone's prior approval*? A system is decentralized to the extent that control over it remains subject to displacement under adversarial conditions. Not distributed, not popular, not widely mirrored — contestable.

That framing makes the comparison between consensus mechanisms tractable, because the two great designs differ precisely in how authority is earned and whether it can be unseated.

Proof-of-work grants the right to propose blocks to whoever performs ongoing, externally costly computation. Authority is purchased in joules and silicon, hardware depreciates, energy is consumed, and every unit of influence must be continuously re-earned under changing external conditions. Proof-of-stake grants proposal and validation authority in proportion to capital locked inside the system, and pays rewards to that same capital. Both mechanisms centralize under scale — nothing exempts either from economies of scale. The distinction is what governs the centralization: whether dominance, once achieved, stays exposed to loss.

## The Compounding Loop

Proof-of-stake makes one defining architectural choice: validation authority scales with stake. If all holders receive the same proportional return and reinvest equally, their shares do not automatically diverge. Concentration can still grow through minimum efficient scale, differential participation, liquid-staking networks, custody, fee advantages, and compounding relative to holders who do not stake. Slashing, delegation choice, client diversity, issuance design, sales, and new purchases provide counterforces of varying strength. Oligarchy is a risk to measure, not a theorem equal to the staking yield.

Contrast the cost structure under proof-of-work. Decentralized control requires more than cost in general; it requires *adversarial* cost — a burden borne by challengers seeking authority, and equally by incumbents seeking to keep it. In proof-of-work that cost is external. A dominant miner's position rests on energy contracts, hardware procurement, geography, regulation, and supply chains — mutable conditions the ledger cannot see and the incumbent cannot vote on. Advantage must be re-bought every day at prevailing prices. Economies of scale are real and large miners do entrench, but their dominance persists only while the external world cooperates: an energy-price shift, a hardware generation, a jurisdictional crackdown can reorder the leaderboard. Authority remains continuously exposed to displacement even in periods when no displacement occurs — which is what contestability means. Decentralization does not require constant turnover; it requires credible turnover.

In proof-of-stake the primary cost is capital locked or exposed to protocol and market risk. A challenger can acquire stake in a market or attract delegation; an incumbent can sell, be slashed, lose delegation, or be diluted. In proof-of-work a challenger acquires hardware and energy, but those markets also have specialized supply chains, scale advantages, pool coordination, and regulatory exposure. The designs create different entry barriers and attack surfaces. Neither makes contestability automatic.

## Institutional Gravity

The compounding loop is the internal failure. The external one is what stake *is*: a legible, taxable, sanctionable financial position held by identifiable parties.

Many holders do not run validators. Operational complexity and risk push them toward exchanges, custodians, pools, and liquid-staking services, creating correlated legal and technical exposure. Mining pools also concentrate block construction even when hashpower can redirect, and specialized hardware, firmware, energy contracts, and geography create their own chokepoints. Unbonding rules and slashing can make stake delegation sticky; switching tools can make it fluid. “Machines versus paperwork” is a useful threat-model contrast only after the actual operator distribution and jurisdictions are specified.

In the period after the Merge, use of a small number of MEV relays and differing responses to OFAC sanctions provided evidence of relay and operator concentration. Inclusion remained probabilistic rather than absolutely censored, and relay shares, proposer-builder designs, and operator behavior can change. The episode supports the institutional-exposure hypothesis; it does not establish an irreversible equilibrium. Any quantitative claim here should be dated to a measurement window.

Stake-weighted governance completes the picture. Participation among small holders is chronically low; large holders are consistently engaged; outcomes therefore track capital ownership. Large stakeholders often prioritize stability, yield, regulatory comfort, and the preservation of established positions. The design can therefore drift toward ossification and rent protection even without explicit corruption.

## The Social Layer, Normalized

There is a standard rejoinder: every consensus system ultimately rests on social coordination — Bitcoin included. True. The difference is how often the social layer is invoked, and for what.

Proof-of-stake uses protocol-defined slashing conditions for observable violations such as conflicting signatures; ordinary enforcement need not determine private intent case by case. Social coordination still defines and can revise those rules, handle exceptional faults, and decide how clients respond to attacks. Proof-of-work likewise relies on social coordination for client rules, bug responses, mining policy, and forks. The comparison is about the frequency, concentration, and consequences of discretion, not its presence in one design and absence in the other.

This is where the fork and the Merge join into one story. The DAO bailout was the exceptional invocation of the social layer — a one-time moral override, defensible as an emergency if you squint. The Merge built the social layer into the security model, where it operates continuously and without the embarrassment of an emergency. The precedent of 2016 did not fade with maturity. It was institutionalized.

## You Cannot Decentralize Capital

Underneath all of this sits one asymmetry, and it is the load-bearing claim of the chapter.

Decentralization requires an external anchor: a resource that no political decree can alter, so that authority over the ledger rests on something outside anyone's jurisdiction. Energy is such a resource. A joule is a joule in every legal system on Earth; no legislature can inflate it, freeze it, or reassign it. This is the same anchor that makes the substrate itself [ungovernable by design](12-ungovernable-by-design.md) — regulators can harass the people at the edges, but they cannot repeal thermodynamics.

Capital is not such a resource. Capital is a social relation — ledger entries, claims, and titles that exist by institutional recognition and are enforceable, seizable, and taxable by states. A consensus mechanism that treats wealth as its source of truth therefore absorbs every constraint society imposes on wealth: regulation, taxation, sanctions, surveillance, compliance. It does not escape the political system; it imports it, and consensus becomes a shareholders' regime with a shareholders' relationship to the authorities. A proof-of-stake chain is not a neutral substrate. It is a financial network wearing decentralization as a costume.

Capital-weighted authority is exposed to wealth concentration, custody, sanctions, and financial regulation. Energy-weighted authority is exposed to industrial concentration, grids, hardware supply, pools, and land-based law. The design question is which exposures are more diverse, observable, and contestable for the threat model at hand. “You cannot decentralize capital” is the chapter's warning, not a demonstrated impossibility theorem.

## The Verdict

The Axio assessment, then. Both proof-of-work and proof-of-stake face concentration. Proof-of-work purchases Sybil resistance through recurring external resource expenditure; proof-of-stake purchases it through slashable internal capital. The former exposes authority to energy, hardware, pools, and jurisdiction; the latter to stake distribution, custody, delegation, and financial institutions. This chapter favors proof-of-work for adversarial monetary neutrality, but that verdict is conditional on measured contestability and cannot be read off the labels alone.

And the judgment on Ethereum follows. It did not forfeit credible neutrality by collaborating with institutions — every system that touches the real economy does that. It forfeited neutrality when it made institutional incentives part of its security model. The DAO fork showed that the rules would bend under sufficient moral pressure; the Merge ensured that the parties applying pressure would henceforth hold the validator keys. This is not a moral indictment so much as a structural one, and the structural kind is worse, because it is the kind that determines what survives: as with agents, so with institutions — [viability](../05-value-and-ethics/22-the-ethics-of-viability.md) belongs to designs that can hold their constraints under adversarial pressure, and a system that grants itself exceptions has announced the price at which it can be captured.

Every monetary system balances rule stability, recoverability, and social coordination. Ethereum accepted more explicit social and capital-weighted governance; Bitcoin has so far preserved a narrower change culture while still relying on implementers, miners, nodes, and users. This chapter prefers the latter tradeoff for adversarial money. The [next chapter](14-the-cybernetic-ghost-of-satoshi.md) explores what that persistence looks like without mistaking a design preference for a theorem that one network has rules and the other only exceptions.
