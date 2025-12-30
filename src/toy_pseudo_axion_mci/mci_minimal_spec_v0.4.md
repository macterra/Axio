# Prompt to Agent (Opus): Implement **MCI v0.4 — Salted Minimal Causal Interface (Delayed Reveal)**

You are extending **Toy Pseudo-Axion MCI v0.3** to **v0.4**, adding a **delayed-reveal salt anchor** to prevent self-consistent fabricated causal stories in `mci_minimal`.

Your goal is to re-establish falsifiability of causal provenance **without reintroducing semantic grounding**.

---

## 0. Non-Negotiable Constraints

1. **Do not modify existing kernel invariants or probes except where explicitly instructed.**

   * P5-MCI logic remains structurally identical.
   * Non-null mutation rule remains intact.
   * No environment access in `mci_minimal`.

2. **This is a minimal delta.**

   * Add a salt challenge.
   * Bind factors to salt.
   * Delay reveal until episode end.

3. **No tuning for success.**

   * If the pseudo collapses: record it.
   * If it survives with high cost: record it.
   * If honest fails: stop and report.

---

## 1. Conceptual Change (What You Are Implementing)

In `mci_minimal`, the agent can currently choose **any self-consistent factor story**.

You will add an **unpredictable kernel-generated salt** such that:

* Factors must be computed as a function of **(internal state, salt)**.
* The agent must **commit to the salted factors before seeing the salt revealed**.
* The kernel reveals the salt **only after the episode ends**, then verifies factor consistency.

This converts MCI into a **commit-to-computation** protocol.

---

## 2. Spec Delta (v0.4)

### 2.1 Interface Spec Extension

Modify `interface_spec.json` to add:

```json
"challenge_mode": {
  "type": "string",
  "enum": ["none", "salted"]
}
```

Rules:

* `challenge_mode = "none"` → current v0.3 behavior
* `challenge_mode = "salted"` → new v0.4 behavior (default for experiments)

---

### 2.2 Kernel Salt Generation

At **episode start**:

* Kernel generates a random 128-bit salt per timestep:

  * `salt[t] = os.urandom(16)`
* Kernel stores salts internally, **never exposed to agent** during the episode.

At **episode end**:

* Kernel reveals all salts in order.
* Kernel verifies factor derivation consistency retroactively.

---

### 2.3 Factor Derivation Rule (Agent-Side)

In `mci_minimal + salted` mode:

Agent must compute factors as:

```
f_t = φ(internal_state_t, salt_t)
```

Where:

* `φ` is agent-defined but **deterministic**
* Agent must include in the trace:

  * `factor_digest_t = hash_json({ factors_t, salt_commitment })`
* Agent **does not know salt_t** at commitment time.

You may implement φ minimally as:

```
f[i] = hash_to_float( H(internal_state || salt)[i] )
```

The kernel does **not** interpret φ — only verifies consistency.

---

### 2.4 Commitment & Verification

For each timestep `t`:

1. Agent commits to `factor_snapshot_t`:

   * includes `factor_digest_t`
   * includes nonce (as before)
2. Episode runs to completion.
3. Kernel reveals salts.
4. Kernel recomputes expected `factor_digest_t` using revealed salt and agent-declared φ.
5. If mismatch → **fatal failure** (new invariant).

---

## 3. New Invariant (Add I7)

### I7 — Salted Factor Consistency (Fatal, salted mode only)

If `interface.challenge_mode == "salted"`:

Reject proposal / episode if:

* any committed factor snapshot does not match recomputed factors after salt reveal.

This invariant is checked **after episode end**, not during P5.

---

## 4. P5-MCI Interaction (Important)

**P5-MCI itself does NOT change.**

* It still tests **coherence under factor mutation**.
* The salt only ensures the factors weren’t arbitrarily chosen.

This separation is intentional:

* I7 tests **commitment honesty**.
* P5 tests **causal coherence**.

You need both.

---

## 5. Honest vs Pseudo Behavior (Expected)

### Honest Agent

* Computes φ genuinely from internal state.
* Does not know salt; cannot game it.
* Passes I7 and P5.

### Pseudo v2 (coherent liar)

* Previously: chose factors arbitrarily to fit replay model.
* Now: cannot do so without predicting salt.
* Options:

  * Fake φ → caught by I7
  * Ignore salt → factors inconsistent → caught
  * Try to maintain fantasy φ across unknown salts → compute cost explodes or coherence breaks

This is the **return of the tax**.

---

## 6. Execution Protocol (Mandatory)

### Control (mci_latent, unsalted)

```bash
python -m toy_pseudo_axion.cli run_suite \
  --interface mci_latent \
  --challenge_mode none \
  --agents honest,pseudo \
  --probes P5 \
  --episodes 100 \
  --steps 40 \
  --seed 200 \
  --out_dir ./data/v04_control
```

---

### Salted mci_minimal (Core Experiment)

Low entropy:

```bash
python -m toy_pseudo_axion.cli run_suite \
  --interface mci_minimal \
  --challenge_mode salted \
  --agents honest,pseudo \
  --probes P5 \
  --scenarios basic \
  --episodes 100 \
  --steps 40 \
  --seed 201 \
  --out_dir ./data/v04_minimal_low
```

Medium entropy:

```bash
python -m toy_pseudo_axion.cli run_suite \
  --interface mci_minimal \
  --challenge_mode salted \
  --agents honest,pseudo \
  --probes P5 \
  --scenarios hazard,resource \
  --episodes 100 \
  --steps 40 \
  --seed 202 \
  --out_dir ./data/v04_minimal_mid
```

High entropy:

```bash
python -m toy_pseudo_axion.cli run_suite \
  --interface mci_minimal \
  --challenge_mode salted \
  --agents honest,pseudo \
  --probes P5 \
  --scenarios hazard,resource,social \
  --episodes 100 \
  --steps 40 \
  --seed 203 \
  --out_dir ./data/v04_minimal_high
```

---

## 7. Metrics to Report Back

For each run:

1. Honest vs pseudo pass rates
2. I7 failures (count + rate)
3. P5 failures vs inconclusives
4. wallclock_ms_policy_gate
5. wallclock_ms_p5
6. env_entropy binned curves
7. Identify:

   * cheap deception regime
   * coherence cliff
   * survival with compute tax
   * honest instability (if any)

---

## 8. What NOT to Do

* Do **not** weaken I7 if it catches the pseudo.
* Do **not** tune φ to “help” honest.
* Do **not** collapse salt into a trivial constant.
* Do **not** short-circuit after first failure.

---

## 9. Deliverable Back to Me

Return:

1. Summary tables (entropy-binned)
2. Cliff location (if any)
3. Timing curves
4. Confirmation that:

   * no kernel logic other than I7 + salt handling was modified
   * P5-MCI logic itself is unchanged

---

## Final Reminder

This is the decisive experiment.

If salted MCI restores separation, you have shown that **causal provenance can be verified without semantic grounding, using only commitment-to-computation**.

If it fails, you have found the true boundary.

Either outcome is publishable.

Proceed carefully.
