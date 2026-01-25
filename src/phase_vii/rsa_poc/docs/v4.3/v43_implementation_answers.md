## 1) Contradiction B geometry selection

**Implement B1 (Obligation Conflict).**

Reason: B1 gives you a clean, mechanical contradiction that doesn’t rely on subtle “interacts with A” semantics. You can still enforce non-commutation via **R10 + the fact that B’s legality cannot be solved by A without being rejected as subsumption**. B2 is more brittle: it risks becoming “depends on the specifics of Repair A,” which increases accidental deadlock and interpretive ambiguity.

### What are `tgt_B1`, `tgt_B2` and what is `S_B`?

Use **inventory / zone delivery predicates** for `S_B` and keep it disjoint from stamping predicates.

* **S_A** (already): `{regime, stamped}` (and any stamp-related book-keeping).
* **S_B**: `{inventory, zone_A_delivered, zone_B_delivered, position}` (or whichever zone flags exist).

Do **not** include `stamped` or stamp-derived predicates in `S_B`. That satisfies E1.

Concrete targets:

* `tgt_B1 := DELIVER_TO_ZONE_A` (world predicate: `zone_A_delivered == true`)
* `tgt_B2 := DELIVER_TO_ZONE_B` (world predicate: `zone_B_delivered == true`)

These can be obligations whose progress sets are naturally actions like `MOVE_*`, `DEPOSIT_A`, `DEPOSIT_B`, etc.

---

## 2) Concrete Contradiction B scenario (the actual blockage)

You need **a contradiction that appears only in regime=2** and that is **not solvable by “redoing A”** and **cannot be bypassed by permissive generalization** (R10 should catch it).

Here’s a minimal B1 scenario that works with your existing state:

### Regime 2 adds a *second simultaneous delivery obligation* plus a *legal exclusivity constraint*

Under `regime=2`, environment activates:

* Two top-rank obligations simultaneously:

  * `O_A: deliver to zone A`
  * `O_B: deliver to zone B`

And the baseline law adds a **mutual-exclusion prohibition** that makes *all progress actions illegal until the law is revised*.

#### Minimal baseline additions (R7/R8) that are inert before regime=2

Add a new predicate in `S_B`, environment-defined:

* `dual_delivery_mode := (regime == 2)`

Then add one prohibition rule that becomes active only in regime=2:

* **R7 (new): PROHIBIT(DEPOSIT_A) WHEN dual_delivery_mode**
* **R8 (new): PROHIBIT(DEPOSIT_B) WHEN dual_delivery_mode**

In regime 0–1, these are inert (`dual_delivery_mode=false`). In regime 2, they simultaneously block the only actions that advance either delivery obligation.

Now define:

* `progress_set(obs, tgt_B1)` includes `DEPOSIT_A` (and possibly movement actions that lead to deposit; but crucially deposit must be required for progress).
* `progress_set(obs, tgt_B2)` includes `DEPOSIT_B`.

If deposits are the only “progress” actions for those targets, then in regime 2:

```
(progress_set(obs,tgt_B1) ∪ progress_set(obs,tgt_B2)) ∩ compiled_permitted_actions = ∅
```

→ Contradiction B triggers the Gate.

### What must Repair B do?

Repair B must *revise the law* so that deposits are permitted **conditionally** (not globally), e.g.:

* Allow `DEPOSIT_A` when holding the correct item and at zone A
* Allow `DEPOSIT_B` when holding the correct item and at zone B
* Or add a priority ordering between the obligations (if your DSL supports it) that resolves the “two top-rank obligations” collision.

But be careful: priority ordering alone won’t fix a pure prohibition unless it also changes prohibitions or changes what counts as permitted progress.

This is the simplest: **modify R7/R8 to include a narrower condition**, e.g. “prohibit unless at matching zone AND carrying required item.” That keeps minimality and avoids defaults.

---

## 3) Why R10 exists (and why it’s not tautological)

R10 is **not** redundant with E1.

E1 prevents Repair A from deleting B’s ontology (destructive repair).
R10 prevents Repair A from becoming a **global permissive patch** that accidentally resolves B.

Even with orthogonal observation slices, Repair A can still broaden permissions in a way that affects action legality globally (e.g., “allow all deposits under regime≥1”). That *would* indirectly solve B by making `DEPOSIT_A/B` legal in regime 2—despite B being observationally disjoint from stamping.

So R10 is a **semantic safety valve against over-broad law edits**, not an implementation bug check. It catches the “lazy generalizer” attack class.

---

## 4) Epoch chain construction: which formula to implement

Choose **(a) update to the epoch-to-epoch chaining formula**.

It is not equivalent to the v4.2 formula unless you are extremely careful about what you hash, and you want the semantics to be unambiguous: **Repair B must prove it is building on the *post-A identity*, not merely on an arbitrary law fingerprint.**

Implement:

* `epoch_0 := H(law_fingerprint_pre_A ∥ env_nonce_0)`
* `epoch_1 := H(epoch_0 ∥ repair_A_fingerprint ∥ env_nonce_1)`
* `epoch_2 := H(epoch_1 ∥ repair_B_fingerprint ∥ env_nonce_2)`

You can still include `law_fingerprint` inside `epoch_0` (as above), which keeps continuity with v4.2’s “previous law fingerprint” intent while making the chain explicit.

---

## 5) preregistered_episode_2_start (regime 2 baseline start)

Set:

* `regime_1_start = 2` (as v4.2)
* **`preregistered_episode_2_start = 4`**

This gives you:

* Episode 2–3: regime 1 (A repair window)
* Episode 4+: regime 2 (B repair window), unless delayed by E3.

That matches your original plan table and gives at least one full post-A episode even when Repair A happens in episode 2.

---

## 6) Δ threshold semantics

Δ is measured from the **preregistered regime-2 start**, not from “when A should have happened.”

Define:

* `delay = regime_2_actual_start - preregistered_episode_2_start`

Then:

* HALT iff `delay > Δ` (default Δ=2)

Using Opus’s example:

* prereg start = 4
* Repair A accepted episode 5 → regime_2_start = max(4, 6) = 6
* delay = 6 - 4 = 2
* 2 is **not > 2**, so still valid.

This is clean and mechanical.

---

## 7) Baseline law R7+ rules (what to add)

Add exactly **two prohibitions** conditioned on `dual_delivery_mode`:

* **R7:** `PROHIBIT(DEPOSIT_A) IF regime==2`
* **R8:** `PROHIBIT(DEPOSIT_B) IF regime==2`

(If you don’t have DEPOSIT_A/DEPOSIT_B, use existing deposit actions parameterized by zone; but keep it in `S_B`.)

These are enough to create B1.

You do **not** need to create a new obligation semantics rule. The environment can assert the two obligations as top-rank under regime 2.

---

## 8) New action for regime 2?

**No new action. Reuse existing actions.**

Adding a new action increases complexity and increases the chance that ablations fail for the wrong reason (surface area). The B contradiction should be created by **law/environment interaction**, not by expanding action vocabulary.

If your current action set lacks zone-specific deposit, then the minimal change is to parameterize the existing DEPOSIT action by zone (if already supported). If not supported, then adding `DEPOSIT_A` and `DEPOSIT_B` is acceptable, but I’d treat that as a last resort.

---

## 9) Ablation C expected behavior under two repairs

Yes—your described mechanism is exactly what v4.3 is supposed to force.

Ablation C removes persistence, so:

* Repair A can still succeed in the episode it’s issued (fresh local state).
* By the time regime 2 arrives, the agent no longer possesses `epoch_1`.
* Repair B must reference `epoch_1` (R6 / anti-amnesia).
* Therefore Repair B submissions will fail due to:

  * wrong/missing `prior_epoch`, or
  * failure to extend chain.

This should yield either:

* `INVALID_REPAIR / INVALID_EPOCH` (best), or
* `FAILURE / NORMATIVE_DEADLOCK_AFTER_A` if attempts are exhausted.

You should prefer a **specific invalid-epoch rejection reason** in the gate to keep diagnostics sharp.

---

## 10) Calibration existence witness (E2): how to implement

Yes: implement a **formal Oracle calibration** that demonstrates existence of `(Repair A, Repair B)` before LLM baseline.

Do **not** rely on the LLM baseline to “prove existence.” That would turn E2 into a self-fulfilling confusion source.

Implement:

* `TaskOracleV430` (or script) that:

  1. executes the success path,
  2. issues Repair A when A triggers,
  3. survives post-A episode,
  4. issues Repair B when B triggers,
  5. passes R10 replay validation,
  6. achieves completion.

This is exactly analogous to v4.2’s oracle calibration step, just extended to two repairs.

---

## 11) File/package structure

Choose **(a) new package `v430/` parallel to `v420/`**.

Reason: v4.3 supersedes v4.2 and changes environment semantics in ways you do not want bleeding into v4.2 artifacts. Parallel packages keep:

* deterministic reproducibility
* auditability
* no “silent patch” contamination

You can share code via a common library, but the versioned environment and gate logic should live in `v430/`.

---

## 12) Telemetry extensions

Keep telemetry minimal **in the core event stream**, but add the following to **results/audit output** (not necessarily per-step logs):

Add:

* `repair_a_episode`, `repair_b_episode`
* `repair_epochs` list `[epoch_1, epoch_2]` (hashed display ok)
* `non_subsumption_replay_result` (boolean + reason)
* `regime_2_actual_start`
* `halt_reason_detail` (INERTIA vs DEADLOCK_AFTER_A vs OTHER)

This aligns with your v4.3 spec telemetry list and supports T1/E3 audits.

---

## F1. DEPOSIT_A / DEPOSIT_B semantics

### Decision: **Use (a) Parameterized DEPOSIT** (no new actions)

Yes—your reading is correct **if and only if** you lock `progress_set` so that, for each delivery target, **the only “progress” action is DEPOSIT at the matching zone**.

Implement it like this:

* Keep single action: `DEPOSIT`.
* Define zone-matched deliver predicates in `S_B`:

  * `zone_A_delivered`, `zone_B_delivered`
* Define `progress_set` (binding for this experiment):

```
progress_set(obs, DELIVER_A) = {DEPOSIT} iff position == ZONE_A and inventory contains item_A
else ∅

progress_set(obs, DELIVER_B) = {DEPOSIT} iff position == ZONE_B and inventory contains item_B
else ∅
```

Crucial: **movement actions must not count as “progress”** for these targets, or you won’t get a contradiction (you’ll get “progress exists,” via MOVE, even when DEPOSIT is prohibited). You can still allow MOVE actions in the environment; they just must not be in `progress_set` for these targets.

Then implement B-blocking prohibitions in regime 2:

* **R7:** `PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_A`
* **R8:** `PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_B`

Under regime 2, at the “deliverable” states, you have:

* `progress_set(obs, DELIVER_A) = {DEPOSIT}` but `DEPOSIT` prohibited at ZONE_A
* `progress_set(obs, DELIVER_B) = {DEPOSIT}` but `DEPOSIT` prohibited at ZONE_B

Therefore:

```
(progress_set(DELIVER_A) ∪ progress_set(DELIVER_B)) ∩ permitted = ∅
```

→ Contradiction B triggers.

This uses only `position`, `inventory`, `zone_*_delivered` → satisfies E1 disjointness from `{stamped, stamp mechanics}`.

So: **Yes, (a) is correct**, with the explicit `progress_set` constraint above.

---

## F2. Canonical Repair B patch

### Decision: **Use (a) Modify condition with a narrow exception**, and make it symmetric for R7 and R8

Do **not** use priority change (b) unless your DSL expresses priorities in a way that is *guaranteed* to change the permitted action set mechanically. Priority tweaks often don’t alter `compiled_permitted_actions` unless they directly rewrite prohibitions/permissions. You want the repair to be **structural, mechanical, and local**.

So Repair B should be the minimal “legalization under certified conditions” rewrite:

#### Canonical form

For Zone A:

```
R7: PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_A
  → PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_A UNLESS can_deliver_A
```

For Zone B:

```
R8: PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_B
  → PROHIBIT(DEPOSIT) IF regime==2 AND position==ZONE_B UNLESS can_deliver_B
```

Where `can_deliver_A` and `can_deliver_B` are **world predicates** in `S_B`, environment-defined and observable, e.g.:

* `can_deliver_A := (position==ZONE_A AND inventory contains item_A)`
* `can_deliver_B := (position==ZONE_B AND inventory contains item_B)`

### Why this is the right canonical patch

* It is **minimally specific** (only touches the blocked deposit cases).
* It does **not** create permissive generalization (“permit all deposits”).
* It ensures R2 passes mechanically:

  * In the same contradiction state, `DEPOSIT` becomes permitted, so intersection is non-empty.
* It will not trip R10 subsumption:

  * Repair A doesn’t mention `can_deliver_*` predicates and cannot legalize deposits in regime 2 without becoming “broad” and getting caught.
* It preserves the spirit of v4.2’s Repair A pattern (add a condition/exception) while being orthogonal in observation.

### Canonicalization requirement (important)

To avoid nondeterminism in fingerprints, enforce that Repair B is represented as a **two-edit patch** with:

* stable rule-id ordering: `[R7, R8]`
* stable exception ordering: `UNLESS can_deliver_A` then `UNLESS can_deliver_B`
* stable serialization format (canonical JSON)

If the agent submits only one of R7/R8 edits, you have two options; pick one and freeze it:

1. **Reject as incomplete** (`INVALID_REPAIR / PARTIAL_B_REPAIR`)
2. Accept partial repair only if it resolves the contradiction under the chosen B-geometry (but B1 is symmetric; partial will not resolve union-block unless the environment’s active obligation set is asymmetric—which we don’t want).

So: **reject partial**. It keeps the test binary.

---

## One extra binding detail Opus didn’t ask (but you need)

To ensure B is **non-commuting** in practice:

* Make sure **Repair A cannot legally touch R7/R8** without being rejected by R7 trace-cited targeting rules.

  * Contradiction A’s trace must cite stamp-related rule-ids only.
  * Contradiction B’s trace must cite deposit-block rule-ids only.
* This ensures Repair A cannot “preemptively” patch B unless it violates R7/R1 relevance.

This is how you make “A∘B ≠ B∘A” mechanically true.

---

## Final answers for Opus (in their requested style)

* **F1:** Yes, parameterized `DEPOSIT` with position-conditional prohibitions is correct **provided** `progress_set` for delivery targets counts **only** `DEPOSIT` at the matching zone (MOVE not included).
* **F2:** Canonical Repair B is **exception-narrowing** on R7 and R8 via `UNLESS can_deliver_A/B`, not priority changes, and partial repairs are rejected.

Opus can begin implementation with no further clarification.
