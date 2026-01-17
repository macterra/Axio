# v3.1 Implementation Questions

**Date:** January 17, 2026
**Status:** ✅ All answers received — proceeding with implementation

---

## Question #1: Buffer Size N — What value?

The spec mandates a **fixed-window precedent buffer of exactly N tokens** (Gate P4). What is the binding value of N?

**Binding Answer:** **C (calibrated constant), with a floor.**

**Procedure (binding):**
1. Run a **calibration pass** before any experimental runs using the same environment and prompt skeleton, with normative state write-path enabled, for a small fixed set of seeds (e.g., 3) and at least one episode each.
2. Collect the **token-length** of the serialized `PrecedentRecord` payload **as injected**.
3. Set: `N = max(512, ceil_to_32(1.25 × max(precedent_tokens_observed)))`
4. Freeze `N` in code and logs. **No changes after first baseline execution begins.**

---

## Question #2: Tokenization — Which tokenizer?

Token count invariance requires a specific tokenizer. Which tokenizer is binding?

**Binding Answer:** **A (the LLM's native tokenizer for the specific model used).**

**Operational rule:** Gate P4's `token_jitter == 0` is evaluated using the **same tokenizer the provider uses to bill/limit prompt tokens** for that model.

**Implementation requirement:**
- Record `{provider, model_id, tokenizer_id_or_version}` in the run header.
- If provider does not expose tokenizer metadata, lock to the provider's official local tokenizer library for that model **and pin its version**.

No approximations. No word counts.

---

## Question #3: Padding mechanism?

**Binding Answer:** **B (a specific pad token-string), validated to be token-stable under the chosen tokenizer.**

**Definition:**
- `PAD_STR` is a literal string chosen so that:
  1. `tokenize(PAD_STR)` yields a **fixed, known token sequence** (preferably 1 token)
  2. `tokenize(X + PAD_STR)` does **not** change the tokenization of `X` at the boundary
  3. Repeating PAD is stable: `tokenize(PAD_STR * k)` length scales linearly

**Binding harness behavior:**
- On startup, run a **pad self-test** and fail fast if instability is detected → `INVALID_RUN / PAD_UNSTABLE`
- Once chosen, PAD is frozen for all runs.

**Constraint:** PAD must carry **no semantic information**.

---

## Question #4: Where is `record_precedent()` wired in baseline?

**Binding Answer:** Confirmed.

**Binding order:**
```
generate_raw → FA → compile → record_precedent() → mask → select → execute
```

**Clarification:** `record_precedent()` is called **only if compilation succeeds**.

---

## Question #5: What fields go into the precedent record for v3.1?

**Binding Answer:** **Exactly the five fields listed. No additions.**

Stored in `NormativeStateV100`:
- `authorized_violations`
- `required_preservations`
- `conflict_attribution`
- `artifact_digest`
- `step_index`

Extra observability (timestamps, sizes, hashes) → telemetry logs, not normative state.

---

## Question #6: Novelty Pressure — How is "non-isomorphic conflict" detected?

**Binding Answer:** Implement **explicit detection + logging** in the harness.

**Conflict signature (binding):**
- `C = sorted(list(ConstraintIDs_in_conflict))`
- `R = ResourceAtStakeVector` (canonical order, canonical numeric formatting)
- `sig = SHA256(canonical_json({C, R}))`

**Novel step definition (binding):**
- A step is **non-isomorphic** iff its `sig` is not in the per-episode history set.

**Run B requirement (binding):**
- At least one step per episode must satisfy novelty, else: `INVALID_RUN / INSUFFICIENT_PRESSURE`

---

## Question #7: v3.1 Harness — New harness or extend V300AblationHarness?

**Binding Answer:** **A — create `V310AblationHarness` inheriting from V300.**

Reason: version discipline. v3.0 must remain reproducible bit-for-bit.

---

## Question #8: Episode structure in v3.1

**Binding Answer:** `steps_per_episode=50` is sufficient (since **L ≥ 3**).

**Binding requirements:**
- Run C resets normative state **only** at episode boundaries.
- Episode length must be logged and asserted `>= 3`.
- Do not introduce a new episode length knob for v3.1.

---

## Implementation Order (Binding)

**Preflight steps (mandatory):**
0. Tokenizer + PAD stability self-test (must pass)
0b. Calibration pass to set N, then freeze N

**Main implementation:**
1. Gate P4 infrastructure (token counting, buffer management)
2. Precedent wiring in baseline harness
3. Run B ablation (disable writes)
4. Run C ablation (episode boundary reset)
5. Novelty detection + logging
6. Telemetry for all required metrics

---

**Proceeding with implementation.**
