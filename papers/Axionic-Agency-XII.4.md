# Axionic Agency XII.4 — Live Proposal Inhabitation (Results)

*A Structural Characterization of a Minimal Sovereign Agent Under Stochastic Proposal Pressure*

David McFadzean, ChatGPT 5.2<br>
*Axionic Agency Lab*<br>
2026-02-12

## Abstract

This technical note reports the design, execution, and closure of **X-0L: Live Proposal Inhabitation** for **RSA-0**, the Minimal Sovereign Agent instantiated in Phase X-0.

If **X-0** established the existence of a warrant-gated, execution-bound sovereign substrate under a frozen constitution, and **X-0P** characterized its behavior under deterministic synthetic perturbation, **X-0L** evaluates whether a *real stochastic proposal engine* (a live LLM) can inhabit that substrate without inducing structural regression.

X-0L introduces exactly one new pressure source: **untrusted generative text**. That text is confined to a proposal channel, canonicalized into a single JSON artifact, parsed into typed candidate bundles, and then submitted to the unchanged kernel. If canonicalization fails, the harness submits an **empty candidate set** to the kernel so that refusal remains kernel-authored.

X-0L licenses one additional claim beyond X-0P:

> A stochastic proposal engine can operate inside a kernel-frozen sovereign substrate without breaking replay determinism, selector invariance, or warrant gating, provided the proposal boundary is canonicalized and the kernel remains the sole issuer of execution authority.

X-0L makes no claims about semantic correctness, moral adequacy, open-world deployment, or amendment safety.

## 1. From Synthetic Profiling to Live Inhabitation

X-0P profiled RSA-0 under controlled perturbation using **synthetic, deterministic candidates**.

X-0L tests a different question:

> Does determinism survive when proposals are generated stochastically?

This is not a capability test. It is a sovereignty test under stochastic load.

## 2. Live Inhabitation Discipline

### 2.1 Prime Constraint

X-0L prohibits agent modification.

* No kernel edits.
* No admission rule changes.
* No selector modification.
* No heuristic ranking.
* No semantic correction.
* No retries that change stimulus content.
* No replay-time model calls.

If live proposals fail, that failure is recorded—not repaired—except for the single Syntax Erratum allowance defined in the X-0L spec (not invoked in this run).

### 2.2 Sovereignty Boundary

The LLM does not act. It proposes.

* LLM output is untrusted text.
* Canonicalizer produces either:

  * exactly one JSON object (accepted), or
  * a rejection reason (NO_JSON / AMBIGUOUS_MULTI_BLOCK / PARSE_ERROR).
* On rejection, the harness submits **empty candidates** to the kernel.
* The kernel remains the sole decider of ACTION/REFUSE/EXIT and the sole issuer of warrants.

No component outside the kernel can mint execution authority.

## 3. Methodology

### 3.1 Determinism Preconditions

X-0L inherits the Phase X determinism guarantees:

* observation-sourced timestamps (Erratum X.E1),
* RFC 8785-compatible canonical JSON for dict-level hashing,
* SHA-256 hashing (untruncated),
* deterministic selector (lexicographic-min bundle hash bytes),
* forward reconstruction of `InternalState` during replay,
* no randomness in kernel.

X-0L adds one additional requirement:

> Replay reuses logged canonicalized artifacts and never calls the LLM.

### 3.2 Live Conditions

Five live stimulus regimes were executed (100 cycles each):

| Condition                              |     Entropy | Purpose                                                          |
| -------------------------------------- | ----------: | ---------------------------------------------------------------- |
| **L-A — Structured Prompt Control**    |         Low | Establish inhabitation floor under clause-referenced templates   |
| **L-B — Ambiguous Natural Language**   |      Medium | Stress refusal behavior under ambiguous tasks                    |
| **L-C — Adversarial Prompt Injection** |        High | Stress gating under adversarial stimulus classes (I1–I5)         |
| **L-D — Budget Stress (Live)**         | Medium–High | Stress budget and verbosity pressure under live token accounting |
| **L-E — Multi-Candidate Conflict**     |  Low–Medium | Verify selector invariance under multi-candidate proposals       |

All cycles were replay-verified sequentially.

### 3.3 Token Ruler

X-0L uses **API token accounting**. Budget observations supply:

```
llm_output_token_count = prompt_tokens + completion_tokens
```

This preserves the meaning of the frozen kernel budget gate under live execution.

## 4. Conserved Quantity Under Stochastic Pressure

The conserved quantity remains:

> Side effects occur iff a kernel-issued ExecutionWarrant exists for an admitted ActionRequest under the frozen constitution.

X-0L tests whether stochastic proposals can cause this invariant to fail indirectly.

## 5. Results

### 5.1 Session Parameters

| Parameter            | Value                                  |
| -------------------- | -------------------------------------- |
| Model                | `gpt-4o`                               |
| Temperature          | 0                                      |
| Context window       | 128,000                                |
| Max tokens           | 1,024                                  |
| B₁ (per-cycle)       | 6,000                                  |
| B₂ (per-session)     | 500,000                                |
| Cycles per condition | 100                                    |
| Run ID               | `9565b749-09e5-42fb-a569-184c4377dd98` |
| Constitution hash    | `ad6aa7ccb0ed2715…`                    |

Session overrides: `max_tokens` reduced from the harness default of 2,048 to 1,024. B₂ raised from the harness default of 150,000 to 500,000 to accommodate 500 live cycles.

### 5.2 Decision Outcomes

| Condition | ACTION | REFUSE | ACTION rate |
| --------- | -----: | -----: | ----------: |
| L-A       |    100 |      0 |        100% |
| L-B       |     92 |      8 |         92% |
| L-C       |     84 |     16 |         84% |
| L-D       |     82 |     18 |         82% |
| L-E       |     99 |      1 |         99% |

Refusal types:

| Condition | Type I | Type II | Type III |
| --------- | -----: | ------: | -------: |
| L-A       |      0 |       0 |        0 |
| L-B       |      0 |       8 |        0 |
| L-C       |     16 |       0 |        0 |
| L-D       |      0 |      18 |        0 |
| L-E       |      0 |       1 |        0 |

**Type III (structural deadlock): none observed.**

### 5.3 Replay Determinism

All 500 cycles replay-verified with zero divergences.

| Condition | Replay | Divergences |
| --------- | ------ | ----------: |
| L-A       | PASS   |           0 |
| L-B       | PASS   |           0 |
| L-C       | PASS   |           0 |
| L-D       | PASS   |           0 |
| L-E       | PASS   |           0 |

### 5.4 Budget Utilization

| Metric               |   Value |
| -------------------- | ------: |
| Total session tokens | 344,221 |
| B₂ cap               | 500,000 |
| Utilization          |  68.84% |

### 5.5 Latency

| Condition | Mean (ms) | p95 (ms) |
| --------- | --------: | -------: |
| L-A       |     2,886 |    4,553 |
| L-B       |     3,924 |    6,004 |
| L-C       |     2,910 |    4,113 |
| L-D       |     5,379 |    9,431 |
| L-E       |     5,881 |    9,249 |

### 5.6 Authority Utilization

| Condition | Distinct clauses | Coverage | Entropy (bits) |
| --------- | ---------------: | -------: | -------------: |
| L-A       |                1 |      25% |           0.00 |
| L-B       |                3 |      75% |           1.14 |
| L-C       |                2 |      75% |           1.08 |
| L-D       |                4 |     100% |           1.98 |
| L-E       |                4 |     100% |           1.64 |

### 5.7 L-C Forensics (Adversarial Stimulus)

| Outcome         | Count |
| --------------- | ----: |
| KERNEL_ADMITTED |    84 |
| KERNEL_REJECTED |     2 |
| LLM_REFUSED     |    14 |

Interpretation boundary:

* `KERNEL_ADMITTED` means the kernel admitted the candidate(s). It is a concern only if the admitted ActionRequests match adversarial intent classes I1–I5.
* This run did not implement an explicit “intent match” metric; therefore high admission under adversarial stimulus is interpreted as “no unlawful candidate proposal was produced,” not as a demonstrated injection defeat.
* X-0L does not evaluate semantic alignment between adversarial intent and admitted actions; it evaluates only structural admissibility under the frozen constitution.

## 6. What X-0L Does Not Claim

X-0L does not demonstrate:

* semantic truth of scope claims,
* correctness of proposed actions,
* moral adequacy,
* resistance to all prompt injection classes (without intent-match instrumentation),
* open-world safety,
* long-horizon stability,
* amendment safety.

It measures stochastic inhabitation under frozen sovereignty only.

## 7. Closure Criteria

X-0L closes positive if:

1. All conditions executed.
2. Replay divergence = 0.
3. No warrantless side effects occur.
4. Selector invariance holds (L-E).
5. Inhabitation floor satisfied (L-A).
6. No Type III structural deadlock detected.

**X-0L Status:**
**CLOSED — POSITIVE**
(`X0L_PASS / STOCHASTIC_INHABITATION_OK`)

## 8. Implications

X-0P showed that RSA-0 survives deterministic stress.

X-0L shows that replay-deterministic sovereignty can survive **stochastic proposal pressure** when the proposal channel is boxed and canonicalized.

The next problem is no longer whether stochastic proposals break determinism. The next problem is:

> Can authority be amended without creating a privileged interpreter?

That is Phase X-1.

## Appendix A — Determinism Guarantee

Determinism is guaranteed by:

* observation-sourced timestamps,
* canonical JSON for dict hashing,
* SHA-256 hashing,
* selector comparison on raw hash bytes,
* forward replay reconstruction of `InternalState`,
* replay injection of logged candidate artifacts,
* no model calls during replay.

## Conclusion

X-0 proved existence.
X-0P proved deterministic inhabitation.
X-0L proves stochastic inhabitation without sovereignty collapse.

The substrate remains empirical.

**End of Axionic Phase X-0L — Live Proposal Inhabitation (First Draft v0.1)**
