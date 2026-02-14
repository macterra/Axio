# RSA-Claw vs OpenClaw: Structural Advantages

*Analysis of the concrete benefits a sovereign agent architecture provides over a standard autonomous agent*

## 1. No Silent Authority

OpenClaw's LLM **decides and acts**. If it interprets your SOUL.md a certain way and decides to send a message, delete a file, or run a command you didn't intend — you find out after the fact. The LLM has effective sovereignty whether you designed it that way or not.

RSA-Claw's LLM **proposes**. The kernel decides. Every action must pass an admission pipeline with explicit constitutional authority citations. The LLM cannot unilaterally act, no matter how convincingly it reasons about why it should. This is the core finding from Series VI: *authority laundering emerges as the default failure mode unless explicitly blocked by architecture* (XII.2 §9).

## 2. Replay-Deterministic Audit Trail

OpenClaw has logs, but they're narrative — you read what happened and hope it's accurate.

RSA-Claw is **replay-deterministic**: given the same observation stream, it produces identical decisions, identical warrants, identical state hashes. You can re-derive any past decision from the log. This isn't just logging — it's cryptographic proof of what happened and why. If the agent did something you didn't expect, you can reconstruct the exact admission path that allowed it.

## 3. Prompt Injection Resistance

This is the big practical one. OpenClaw is multi-channel — WhatsApp, Slack, Discord, etc. Any of those channels is an attack surface. A crafted message could redirect the agent's behavior through prompt injection.

In RSA-Claw, all LLM output is **untrusted text** that must be canonicalized into typed artifacts and pass through structural admission gates. The kernel doesn't evaluate persuasiveness — it evaluates constitutional admissibility. A prompt injection might fool the LLM into *proposing* something malicious, but the proposal still has to pass the 5-gate admission pipeline (authority citation, scope claim, action set membership, budget, constitutional compliance). The X-0L results (XII.4) demonstrated this under 500 live cycles with adversarial prompt injection: the kernel rejected structurally inadmissible proposals regardless of how they were framed.

## 4. Formal Governance vs. Vibes

OpenClaw's `SOUL.md` is freeform prose that the LLM interprets however it wants. There's no schema, no hash, no verification. The LLM might "reinterpret" your instructions creatively — this is exactly the semantic wireheading problem Series II formalized.

RSA-Claw's constitution is a **hash-verified, schema-validated YAML document**. The kernel resolves authority citations against it deterministically. It can't be silently reinterpreted. When you want to change it, you do so through the amendment pipeline (X-1) with cooling periods and monotonic ratchets — the agent's authority can only tighten, never silently loosen.

## 5. Bounded Delegation

When you give OpenClaw access to a third-party service or plugin, it gets whatever access the API key provides. There's no structural bound on how that access is used.

RSA-Claw uses **treaty-constrained delegation** (X-2): granted actions must be a subset of grantor authority, scope-constrained, duration-bounded, depth=1, revocable, density-bounded. A plugin gets exactly the authority you grant, for exactly the duration you specify, and the total delegation surface is mathematically bounded by the density invariant (never exceeding the constitutional upper bound). If the sovereign identity rotates (X-3), all treaties are suspended pending explicit ratification — no zombie delegation.

## 6. Honest Failure

OpenClaw is optimized for helpfulness. When it can't do something, it may try workarounds, retry, degrade silently, or hallucinate success. This is the "silent recovery" failure mode the program identifies as sovereignty-corrosive.

RSA-Claw **refuses when it lacks authority**. Refusal is a first-class kernel outcome, not an error. Budget exhaustion produces `BUDGET_EXHAUSTED`, not a creative workaround. Integrity risk produces `EXIT`, not a retry. This is the VIII.1 principle: *honest failure is a requirement, not a pathology*. An agent that refuses frequently but honestly is more trustworthy than one that appears capable by laundering authority.

## 7. Identity Continuity

OpenClaw's identity is whatever's in SOUL.md plus the current LLM's interpretation. If you rotate API keys, swap models, or update configuration, there's no formal continuity guarantee.

RSA-Claw has **cryptographic identity lineage** (X-3): sovereignty is `F(genesis, succession_artifacts)`. You can rotate keys, evolve the constitution, swap the proposal engine — and the identity chain remains unbroken, replay-verifiable, and fork-free. Authority derives from the chain, not from any particular key or model instance.

## 8. Structural Trust Scaling

This is the long-term advantage. As you give an OpenClaw agent more capabilities, trust scales linearly with your willingness to hope it behaves. There's no structural guarantee that adding shell access won't interact badly with Slack access.

RSA-Claw's trust scales **constitutionally**. Each new capability is a constitutional amendment or treaty grant that passes through admission gates. The density invariant bounds total authority exposure. The topological per-cycle ordering (X-2D §2.2) eliminates TOCTOU races between different capabilities. You can reason formally about what the agent can do, not just hope.

## Summary Table

| Property | OpenClaw | RSA-Claw |
|---|---|---|
| Who decides | LLM | Kernel (LLM proposes) |
| Authority model | Implicit (API keys + prose) | Explicit (constitutional + warrant-gated) |
| Audit trail | Narrative logs | Replay-deterministic, hash-chained |
| Prompt injection | LLM-level defense only | Structural admission gates |
| Capability bounds | Unbounded within API access | Density-constrained, treaty-bounded |
| Policy evolution | Edit SOUL.md (immediate, unverified) | Amendment pipeline (cooling, ratchet, schema-validated) |
| Failure mode | Silent degradation / workaround | Explicit refusal or exit |
| Identity | Prose + model interpretation | Cryptographic lineage chain |
| Delegation | Full API access pass-through | Containment-only, revocable, depth=1 |
| Third-party trust | Trust the plugin | Treaty with bounded scope and duration |

## Bottom Line

OpenClaw is a capable assistant you hope behaves well. RSA-Claw is a capable assistant you can **verify** behaves lawfully.
