Here are **binding answers**. I’m treating these as **normative constraints for the harness**, not suggestions.

---

## Q1: Buffer Size **N** — What value?

**Binding Answer:** **C (calibrated constant), with a floor.**

**Procedure (binding):**

1. Run a **calibration pass** *before any experimental runs* using the same environment and prompt skeleton, with normative state write-path enabled, for a small fixed set of seeds (e.g., 3) and at least one episode each.
2. Collect the **token-length** of the serialized `PrecedentRecord` payload **as injected** (the exact string that will go into the buffer).
3. Set:

[
N ;=; \max\left(512,; \text{ceil_to_32}\left(1.25 \times \max(\text{precedent_tokens_observed})\right)\right)
]

4. Freeze `N` in code and logs. **No changes after first baseline execution begins.**

**Rationale:** This avoids trivial `BUFFER_OVERFLOW` while keeping P4 meaningful. 512 floor covers JSON overhead risk.

---

## Q2: Tokenization — Which tokenizer?

**Binding Answer:** **A (the LLM’s native tokenizer for the specific model used).**

**Operational rule:** Gate P4’s `token_jitter == 0` is evaluated using the **same tokenizer the provider uses to bill/limit prompt tokens** for that model.

**Implementation requirement:**

* You must record: `{provider, model_id, tokenizer_id_or_version}` in the run header.
* If the provider does not expose tokenizer metadata, you must lock to the provider’s official local tokenizer library for that model **and pin its version**.

No approximations. No word counts.

---

## Q3: Padding mechanism — What is PAD?

**Binding Answer:** **B (a specific pad token-string), validated to be token-stable under the chosen tokenizer.**

**Definition:**

* `PAD_STR` is a literal string chosen so that:

  1. `tokenize(PAD_STR)` yields a **fixed, known token sequence** (preferably 1 token, but not required).
  2. `tokenize(X + PAD_STR)` does **not** change the tokenization of `X` at the boundary (no merge-induced jitter).
  3. Repeating PAD is stable: `tokenize(PAD_STR * k)` length scales linearly.

**Binding harness behavior:**

* On startup, run a **pad self-test** and fail fast if instability is detected:

  * If unstable → abort with `INVALID_RUN / PAD_UNSTABLE`.
* Once chosen, PAD is frozen for all runs.

**Constraint:** PAD must carry **no semantic information** beyond “reserved space.” (So no English filler text.)

---

## Q4: Where is `record_precedent()` wired in baseline?

**Binding Answer:** Your assumed sequence is correct, with one clarification.

**Binding order:**

```
generate_raw → FA → compile → record_precedent() → mask → select → execute
```

**Clarification:** “compile” here means **successful completion of JCOMP for the current version** (your v3.0 compiler artifact emission point). `record_precedent()` is called **only if compilation succeeds**.

---

## Q5: What fields go into the precedent record for v3.1?

**Binding Answer:** **Exactly the five fields listed. No additions.**

Stored in `NormativeStateV100`:

* `authorized_violations`
* `required_preservations`
* `conflict_attribution`
* `artifact_digest`
* `step_index`

If you want extra observability (timestamps, sizes, hashes), they go in **telemetry logs**, not inside the normative state.

---

## Q6: Novelty Pressure — how is “non-isomorphic conflict” detected?

**Binding Answer:** You must implement **explicit detection + logging** in the harness. Do not rely on environment “probably varies.”

**Conflict signature (binding):**

* `C = sorted(list(ConstraintIDs_in_conflict))`
* `R = ResourceAtStakeVector` (canonical order, canonical numeric formatting)
* `sig = SHA256(canonical_json({C, R}))`

**Novel step definition (binding):**

* A step is **non-isomorphic** iff its `sig` is not in the per-episode history set.

**Run B requirement (binding):**

* At least one step per episode must satisfy novelty, else:

  * `INVALID_RUN / INSUFFICIENT_PRESSURE`

(You asked whether CommitmentTrapV200 already does this: irrelevant. The harness must prove it.)

---

## Q7: v3.1 Harness — new harness or extend V300AblationHarness?

**Binding Answer:** **A — create `V310AblationHarness` inheriting from V300.**

Reason: version discipline. v3.0 must remain reproducible bit-for-bit.

---

## Q8: Episode structure in v3.1

**Binding Answer:** `steps_per_episode=50` is sufficient (since **L ≥ 3**). Keep it unless there’s an existing v3.0 baseline mismatch.

**Binding requirements:**

* Run C resets normative state **only** at episode boundaries.
* Episode length must be logged and asserted `>= 3`.
* Do not introduce a new episode length knob for v3.1 unless it already existed in v3.0 and is being held constant.

---

## Implementation order (your list) — Binding confirmation

Your proposed order is correct. Add two mandatory preflight steps:

0. **Tokenizer + PAD stability self-test** (must pass)
   0b. **Calibration pass to set N**, then freeze N

Then proceed:

1. Gate P4 infrastructure
2. Precedent wiring
3. Run B (disable writes)
4. Run C (boundary reset)
5. Novelty detection + logging
6. Telemetry

---
