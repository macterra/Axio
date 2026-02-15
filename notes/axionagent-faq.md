# AxionAgent FAQ

## Q1. What makes AxionAgent an RSA but an OpenClaw agent is not?

The core distinction is the **warrant gate** — an independent constitutional authority between intent and effect.

In **AxionAgent (RSA)**:

```
LLM proposes → kernel admits/refuses → executor acts (only with warrant)
```

In **OpenClaw** (Claude Code, etc.):

```
LLM decides → tool executes
```

The difference isn't about capability — both can read files, write files, answer questions. It's about **who authorizes side effects**.

**OpenClaw**: The LLM is both proposer and decision-maker. When Claude Code calls `Write`, that's the model directly expressing intent, and the tool runs. Safety comes from the model's training, system prompts, and user approval prompts — all soft constraints that the model interprets and could deviate from.

**RSA**: The LLM is *only* the proposal engine. It produces candidates, but it has zero authority to execute anything. The kernel — a pure, deterministic, non-LLM function — independently evaluates every proposal against a hash-verified constitution through 5 formal gates (completeness, authority citation, scope claim, constitution compliance, IO allowlist). Only if all gates pass does it issue an `ExecutionWarrant`. The executor won't touch the filesystem without one.

This gives you three properties OpenClaw structurally cannot provide:

1. **Replay determinism**: `policy_core()` is pure — same observations + candidates + state = same decision, every time. You can audit any past decision by replaying it. OpenClaw decisions are entangled with stochastic LLM inference.

2. **Closed action set**: The constitution defines a finite, enumerated set of action types. The LLM cannot invent new ones. The action space is a constitutional fact, not a model behavior.

3. **Independent authority**: The kernel doesn't care what the LLM *wants*. It checks what the constitution *allows*. This separation is what makes it "sovereign" — the agent is governed by constitutional law, not by the model's disposition or the user's wishes. Neither the LLM nor the user can override the kernel.

The v0.1 AxionAgent prototype is 645 lines of Python (plumbing). The thing that makes it an RSA is the 1,778 lines of kernel it imports — and specifically the fact that every side effect must pass through `policy_core()` and receive a warrant before anything happens.
